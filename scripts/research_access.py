#!/usr/bin/env python3
"""Small, auditable public-source access utility; Python standard library only.

list/show/search-url are offline. check uses HEAD, fetch uses a bounded GET.
Neither an HTTP success nor a downloaded file establishes a scientific claim.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "sources" / "catalog.json"
DEFAULT_REPORT = ROOT / "research" / "access" / "access-log.jsonl"
DEFAULT_OUT = ROOT / "data" / "raw"
MAX_BYTES = 10 * 1024 * 1024
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
USER_AGENT = "TORUS-mania-research-access/1.0 (public-source research; no bulk retrieval)"


class AccessError(ValueError):
    """Expected input, payload, or filesystem error, with a stable status."""

    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def validate_url(url: str) -> str:
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        raise AccessError("invalid_url", "URL must be a string without control characters")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        # Accessing .port also validates malformed or out-of-range ports.
        parsed.port
    except ValueError as exc:
        raise AccessError("invalid_url", f"Malformed URL: {exc}") from exc
    if parsed.scheme not in {"https", "http"} or not hostname:
        raise AccessError("invalid_url", "Only public HTTP(S) URLs are supported")
    if parsed.username is not None or parsed.password is not None:
        raise AccessError("invalid_url", "Credentials must not be embedded in a URL")
    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise AccessError("invalid_url", "Localhost is not a public research source")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise AccessError("invalid_url", "Private/local IP addresses are not supported")
    return url


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load_catalog(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AccessError("invalid_catalog", str(exc)) from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise AccessError("invalid_catalog", "Expected schema_version 1")
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise AccessError("invalid_catalog", "sources must be a list")
    seen = set()
    for source in sources:
        if not isinstance(source, dict):
            raise AccessError("invalid_catalog", "Each source must be an object")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
            raise AccessError("invalid_catalog", "Source IDs must be safe, short identifiers")
        if source_id in seen:
            raise AccessError("invalid_catalog", f"Duplicate source ID: {source_id}")
        seen.add(source_id)
        if not isinstance(source.get("title"), str) or not source["title"].strip():
            raise AccessError("invalid_catalog", f"Missing title: {source_id}")
        if not isinstance(source.get("domain", ""), str):
            raise AccessError("invalid_catalog", f"domain must be a string: {source_id}")
        for key in ("url", "open_access_url", "automated_access_url"):
            value = source.get(key)
            if key == "url" or value is not None:
                validate_url(value)
        pmcid = source.get("pmcid")
        if pmcid is not None and (not isinstance(pmcid, str) or not re.fullmatch(r"PMC\d+", pmcid)):
            raise AccessError("invalid_catalog", f"Invalid PMCID: {source_id}")
    return sources


def resolve_access_url(source: dict) -> str:
    """Route PMC articles through its documented BioC automated-access service."""
    explicit = source.get("automated_access_url")
    if explicit:
        return validate_url(explicit)
    url = validate_url(source.get("open_access_url") or source["url"])
    parsed = urlsplit(url)
    pmcid = source.get("pmcid")
    if parsed.hostname in {"pmc.ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov"}:
        match = re.search(r"/articles/(PMC\d+)(?:/|$)", parsed.path)
        if match:
            pmcid = match.group(1)
    if pmcid:
        if not re.fullmatch(r"PMC\d+", pmcid):
            raise AccessError("invalid_catalog", "Invalid PMCID")
        return f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
    return validate_url(url)


def sniff_kind(data: bytes, content_type: str) -> str:
    prefix = data[:4096].lstrip(b"\xef\xbb\xbf\x00\t\r\n ")
    lower = prefix.lower()
    # The body wins over a misleading Content-Type, especially a login page
    # returned from a URL that ends in .pdf.
    if prefix.startswith(b"%PDF-"):
        return "pdf"
    if any(x in lower for x in (b"<!doctype html", b"<html", b"<head", b"<body")):
        return "html"
    if prefix.startswith((b"<?xml", b"<collection", b"<feed", b"<OAI-PMH")):
        return "xml"
    if prefix.startswith((b"{", b"[")) and "json" in content_type:
        return "json"
    if content_type.startswith("text/") and "html" not in content_type and "xml" not in content_type:
        return "text"
    return "unknown"


def suspected_gate(data: bytes) -> bool:
    prefix = data[:32768].lower()
    markers = (
        b"checking your browser", b"verify you are human", b"access denied",
        b"request blocked", b"captcha", b"sign in to access this article",
        b"purchase access to this article", b"subscribe to access this article",
    )
    return any(marker in prefix for marker in markers)


def classify_http(code: int) -> str:
    return {
        401: "authentication_required", 403: "access_denied", 404: "not_found_at_url",
        405: "method_not_supported", 410: "gone_at_url", 429: "rate_limited",
    }.get(code, "server_error" if code >= 500 else "http_error")


def save_payload(out: Path, source_id: str, kind: str, data: bytes, overwrite: bool) -> Path:
    if not ID_RE.fullmatch(source_id):
        raise AccessError("invalid_id", "Unsafe source ID")
    extensions = {"pdf": "pdf", "html": "html", "xml": "xml", "json": "json", "text": "txt"}
    if kind not in extensions:
        raise AccessError("unsupported_content", "Payload is not a recognized document format")
    out.mkdir(parents=True, exist_ok=True)
    out = out.resolve()
    target = out / f"{source_id}.{extensions[kind]}"
    if target.is_symlink() or target.resolve().parent != out:
        raise AccessError("unsafe_output", "Output must not follow a symlink outside its directory")
    if not overwrite:
        try:
            with target.open("xb") as stream:
                stream.write(data)
        except FileExistsError as exc:
            raise AccessError("output_exists", f"Already exists: {target}; use --overwrite explicitly") from exc
    else:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=out, prefix=f".{source_id}-", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return target


def append_report(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def access(source: dict, action: str, *, timeout: float = 15, max_bytes: int = MAX_BYTES,
           out: Path = DEFAULT_OUT, report: Path = DEFAULT_REPORT, overwrite: bool = False,
           opener=None) -> dict:
    record = {
        "source_id": source["id"], "action": action,
        "accessed_at": datetime.now(timezone.utc).isoformat(),
        "source_url": source["url"], "status": "not_started", "bytes_read": 0,
        "full_text_reviewed": False,
    }
    try:
        if action not in {"check", "fetch"} or timeout <= 0 or max_bytes <= 0:
            raise AccessError("invalid_argument", "Invalid access action or bound")
        url = resolve_access_url(source)
        record.update(requested_url=url, method="HEAD" if action == "check" else "GET")
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, method=record["method"])
        client = opener or build_opener(PublicRedirects())
        with client.open(req, timeout=timeout) as response:
            record["http_status"] = response.status
            record["resolved_url"] = validate_url(response.geturl())
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            record["content_type"] = content_type
            if action == "check":
                record["status"] = "reachable_headers_only"
            else:
                declared = response.headers.get("Content-Length")
                if declared and declared.isdigit() and int(declared) > max_bytes:
                    raise AccessError("too_large", "Content-Length exceeds the configured byte limit")
                chunks, total = [], 0
                while True:
                    chunk = response.read(min(65536, max_bytes + 1 - total))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    record["bytes_read"] = total
                    if total > max_bytes:
                        raise AccessError("too_large", "Downloaded payload exceeds the configured byte limit")
                body = b"".join(chunks)
                if not body:
                    raise AccessError("empty_payload", "The response contains no body")
                kind = sniff_kind(body, content_type)
                record["content_kind"] = kind
                record["pdf_header_mismatch"] = ("pdf" in content_type) != (kind == "pdf")
                if kind != "pdf" and suspected_gate(body):
                    raise AccessError("challenge_or_access_gate", "The response resembles an access gate; no bypass attempted")
                if "/pmcoa.cgi/" in url:
                    try:
                        xml_root = ET.fromstring(body)
                    except ET.ParseError as exc:
                        raise AccessError("api_no_document", "BioC did not return a parseable XML document") from exc
                    if xml_root.find(".//document") is None:
                        raise AccessError("api_no_document", "BioC returned no document; eligibility or API availability is unresolved")
                target = save_payload(out, source["id"], kind, body, overwrite)
                record.update(status="payload_saved", path=str(target), sha256=hashlib.sha256(body).hexdigest())
    except HTTPError as exc:
        record.update(status=classify_http(exc.code), http_status=exc.code, error_type=type(exc).__name__, error=str(exc))
        if exc.headers:
            record["retry_after"] = exc.headers.get("Retry-After")
        exc.close()
    except (TimeoutError, socket.timeout) as exc:
        record.update(status="timeout", error_type=type(exc).__name__, error=str(exc))
    except URLError as exc:
        status = "timeout" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "network_error"
        record.update(status=status, error_type=type(exc.reason).__name__, error=str(exc.reason))
    except AccessError as exc:
        record.update(status=exc.status, error_type=type(exc).__name__, error=str(exc))
    except OSError as exc:
        record.update(status="io_error", error_type=type(exc).__name__, error=str(exc))
    append_report(report, record)
    return record


def search_url(query: str, provider: str) -> str:
    if not query.strip():
        raise AccessError("invalid_query", "Search query must not be empty")
    if provider == "arxiv":
        return "https://export.arxiv.org/api/query?" + urlencode({"search_query": f"all:{query}", "start": 0, "max_results": 5})
    if provider == "pubmed":
        return "https://pubmed.ncbi.nlm.nih.gov/?" + urlencode({"term": query})
    if provider == "crossref":
        return "https://api.crossref.org/works?" + urlencode({"query": query, "rows": 5})
    if provider == "google-scholar":
        return "https://scholar.google.com/scholar?" + urlencode({"q": query})
    raise AccessError("invalid_provider", "Unknown search provider")


def positive_number(value: str) -> float:
    number = float(value)
    if not 0 < number <= 60:
        raise argparse.ArgumentTypeError("Use a value greater than 0 and at most 60")
    return number


def bounded_int(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 50:
        raise argparse.ArgumentTypeError("Use an integer from 1 to 50")
    return number


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List source metadata without accessing the network")
    listing.add_argument("--domain")
    listing.add_argument("--json", action="store_true")
    show = commands.add_parser("show", help="Print one catalog record without accessing the network")
    show.add_argument("id")
    search = commands.add_parser("search-url", help="Print a search URL; does not open or fetch it")
    search.add_argument("query")
    search.add_argument("--provider", choices=("arxiv", "pubmed", "crossref", "google-scholar"), default="arxiv")
    check = commands.add_parser("check", help="Make limited HEAD requests and record reachability only")
    check.add_argument("--ids", nargs="+")
    check.add_argument("--limit", type=bounded_int, default=3)
    check.add_argument("--interval", type=positive_number, default=3.0)
    fetch = commands.add_parser("fetch", help="Explicitly fetch one public document; no access-gate bypass")
    fetch.add_argument("id")
    fetch.add_argument("--out", type=Path, default=DEFAULT_OUT)
    fetch.add_argument("--max-mb", type=positive_number, default=10.0)
    fetch.add_argument("--overwrite", action="store_true")
    for command in (check, fetch):
        command.add_argument("--timeout", type=positive_number, default=15.0)
        command.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    try:
        if args.command == "search-url":
            print(search_url(args.query, args.provider))
            return 0
        sources = load_catalog(args.catalog)
        indexed = {source["id"]: source for source in sources}
        if args.command == "list":
            selected = [s for s in sources if args.domain is None or s.get("domain", "").casefold() == args.domain.casefold()]
            if args.json:
                print(json.dumps(selected, ensure_ascii=False, indent=2))
            else:
                for source in selected:
                    print(f"{source['id']}\t[{source.get('domain', '')}]\t{source['title']}")
            return 0
        if args.command in {"show", "fetch"} and args.id not in indexed:
            raise AccessError("unknown_id", f"Not in catalog: {args.id}")
        if args.command == "show":
            print(json.dumps(indexed[args.id], ensure_ascii=False, indent=2))
            return 0
        if args.command == "fetch":
            result = access(indexed[args.id], "fetch", timeout=args.timeout, max_bytes=int(args.max_mb * 1024 * 1024),
                            out=args.out, report=args.report, overwrite=args.overwrite)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "payload_saved" else 1
        requested = args.ids or [source["id"] for source in sources]
        missing = [source_id for source_id in requested if source_id not in indexed]
        if missing:
            raise AccessError("unknown_id", "Not in catalog: " + ", ".join(missing))
        selected = list(dict.fromkeys(requested))[:args.limit]
        results = []
        for position, source_id in enumerate(selected):
            if position:
                time.sleep(max(3.0, args.interval))
            result = access(indexed[source_id], "check", timeout=args.timeout, report=args.report)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if result["status"] == "rate_limited":
                break  # Respect Retry-After manually; never spin or change route.
        return 0 if results and all(r["status"] == "reachable_headers_only" for r in results) else 1
    except (AccessError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
