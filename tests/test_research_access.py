"""Offline tests of the access boundary; no external servers are contacted."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "research_access.py"
SPEC = importlib.util.spec_from_file_location("research_access", MODULE_PATH)
access_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(access_tool)


class Response:
    def __init__(self, body=b"", content_type="text/html", status=200, extra_headers=None):
        self.body = io.BytesIO(body)
        self.headers = {"Content-Type": content_type, **(extra_headers or {})}
        self.status = status
        self.read_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.body.close()

    def geturl(self):
        return "https://example.org/paper"

    def read(self, size=-1):
        self.read_calls += 1
        return self.body.read(size)


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = {"id": "S001", "title": "A source", "url": "https://example.org/paper", "domain": "math"}

    def run_access(self, response=None, error=None, **kwargs):
        opener = mock.Mock()
        if error is not None:
            opener.open.side_effect = error
        else:
            opener.open.return_value = response
        record = access_tool.access(self.source, kwargs.pop("action", "fetch"),
                                    out=self.folder / "raw", report=self.folder / "log.jsonl",
                                    opener=opener, **kwargs)
        saved = json.loads((self.folder / "log.jsonl").read_text().splitlines()[-1])
        self.assertEqual(saved, record)
        return record, opener

    def write_catalog(self, content):
        path = self.folder / "catalog.json"
        path.write_text(json.dumps(content), encoding="utf-8")
        return path

    def test_catalog_rejects_traversal_duplicate_and_bad_schema(self):
        cases = [
            {"schema_version": 2, "sources": []},
            {"schema_version": 1, "sources": [{**self.source, "id": "../../outside"}]},
            {"schema_version": 1, "sources": [self.source, self.source]},
            {"schema_version": 1, "sources": [{**self.source, "url": "file:///etc/passwd"}]},
        ]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(access_tool.AccessError):
                access_tool.load_catalog(self.write_catalog(value))

    def test_malformed_json_is_a_catalog_error(self):
        path = self.folder / "bad.json"
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(access_tool.AccessError) as caught:
            access_tool.load_catalog(path)
        self.assertEqual(caught.exception.status, "invalid_catalog")

    def test_private_or_credential_urls_are_rejected(self):
        for url in ("http://127.0.0.1/", "http://[::1]/", "http://localhost/", "https://user:token@example.org/"):
            with self.subTest(url=url), self.assertRaises(access_tool.AccessError):
                access_tool.validate_url(url)

    def test_malformed_urls_report_invalid_url(self):
        for url in ("https://[broken/", "https://example.org:invalid/"):
            with self.subTest(url=url), self.assertRaises(access_tool.AccessError) as caught:
                access_tool.validate_url(url)
            self.assertEqual(caught.exception.status, "invalid_url")

    def test_pmc_articles_are_routed_to_bioc_not_scraped(self):
        source = {**self.source, "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7116426/"}
        self.assertEqual(access_tool.resolve_access_url(source),
                         "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC7116426/unicode")

    def test_head_checks_do_not_read_or_claim_full_text(self):
        response = Response(b"unreadable paywall text")
        record, opener = self.run_access(response, action="check")
        self.assertEqual(opener.open.call_args.args[0].method, "HEAD")
        self.assertEqual(response.read_calls, 0)
        self.assertEqual(record["status"], "reachable_headers_only")
        self.assertFalse(record["full_text_reviewed"])

    def test_head_405_does_not_fall_back_to_get(self):
        record, opener = self.run_access(error=HTTPError(self.source["url"], 405, "Method not allowed", {}, None), action="check")
        self.assertEqual(record["status"], "method_not_supported")
        self.assertEqual(opener.open.call_count, 1)

    def test_html_at_pdf_url_is_not_saved_as_pdf(self):
        self.source["url"] += ".pdf"
        record, _ = self.run_access(Response(b"<!doctype html><html><body>A landing page</body></html>", "application/pdf"))
        self.assertEqual(record["status"], "payload_saved")
        self.assertTrue(record["pdf_header_mismatch"])
        self.assertEqual(Path(record["path"]).suffix, ".html")

    def test_pdf_body_wins_over_generic_header(self):
        record, _ = self.run_access(Response(b"%PDF-1.7\nA test fixture", "application/octet-stream"))
        self.assertEqual(record["status"], "payload_saved")
        self.assertEqual(record["content_kind"], "pdf")
        self.assertEqual(len(record["sha256"]), 64)

    def test_challenge_is_recorded_without_saving_a_paper(self):
        record, opener = self.run_access(Response(b"<html><body>Checking your browser. CAPTCHA</body></html>"))
        self.assertEqual(record["status"], "challenge_or_access_gate")
        self.assertNotIn("path", record)
        self.assertEqual(opener.open.call_count, 1)

    def test_timeout_denial_and_absence_are_distinct(self):
        cases = [
            (URLError(socket.timeout("timed out")), "timeout"),
            (URLError("network policy blocked this host"), "network_error"),
            (HTTPError(self.source["url"], 403, "Forbidden", {}, None), "access_denied"),
            (HTTPError(self.source["url"], 404, "Not Found", {}, None), "not_found_at_url"),
        ]
        for error, expected in cases:
            with self.subTest(expected=expected):
                record, _ = self.run_access(error=error)
                self.assertEqual(record["status"], expected)
                self.assertFalse(record["full_text_reviewed"])

    def test_rate_limit_records_retry_after_without_retrying(self):
        record, opener = self.run_access(error=HTTPError(self.source["url"], 429, "Slow down", {"Retry-After": "120"}, None))
        self.assertEqual(record["status"], "rate_limited")
        self.assertEqual(record["retry_after"], "120")
        self.assertEqual(opener.open.call_count, 1)

    def test_declared_and_streaming_sizes_are_bounded(self):
        for response in (Response(b"small", "text/plain", extra_headers={"Content-Length": "1000"}),
                         Response(b"0123456789", "text/plain")):
            with self.subTest(response=response):
                record, _ = self.run_access(response, max_bytes=5)
                self.assertEqual(record["status"], "too_large")
                self.assertNotIn("path", record)

    def test_existing_payload_is_preserved(self):
        first, _ = self.run_access(Response(b"first", "text/plain"))
        second, _ = self.run_access(Response(b"second", "text/plain"))
        self.assertEqual(second["status"], "output_exists")
        self.assertEqual(Path(first["path"]).read_bytes(), b"first")
        third, _ = self.run_access(Response(b"third", "text/plain"), overwrite=True)
        self.assertEqual(third["status"], "payload_saved")
        self.assertEqual(Path(first["path"]).read_bytes(), b"third")

    def test_symlink_or_unsafe_filename_cannot_escape_output_directory(self):
        out = self.folder / "raw"
        out.mkdir()
        outside = self.folder / "keep.txt"
        outside.write_text("keep")
        (out / "S001.txt").symlink_to(outside)
        with self.assertRaises(access_tool.AccessError):
            access_tool.save_payload(out, "S001", "text", b"replace", overwrite=True)
        with self.assertRaises(access_tool.AccessError):
            access_tool.save_payload(out, "../keep", "text", b"replace", overwrite=True)
        self.assertEqual(outside.read_text(), "keep")

    def test_bioc_error_body_is_not_treated_as_a_paper(self):
        self.source["pmcid"] = "PMC7116426"
        record, _ = self.run_access(Response(b"<?xml version='1.0'?><error>Not available</error>", "application/xml"))
        self.assertEqual(record["status"], "api_no_document")
        self.assertNotIn("path", record)

    def test_bioc_document_can_be_saved_as_xml(self):
        self.source["pmcid"] = "PMC7116426"
        record, _ = self.run_access(Response(b"<?xml version='1.0'?><collection><document><id>1</id></document></collection>", "application/xml"))
        self.assertEqual(record["status"], "payload_saved")
        self.assertTrue(record["path"].endswith(".xml"))

    def test_search_url_is_offline_and_encodes_query(self):
        with mock.patch.object(access_tool, "build_opener") as network:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                result = access_tool.main(["search-url", "torus & branching", "--provider", "crossref"])
        self.assertEqual(result, 0)
        self.assertIn("%26", output.getvalue())
        network.assert_not_called()

    def test_check_defaults_to_three_and_validates_ids_before_network(self):
        sources = [{**self.source, "id": f"S{i:03d}"} for i in range(1, 6)]
        catalog = self.write_catalog({"schema_version": 1, "sources": sources})
        with mock.patch.object(access_tool, "access", return_value={"status": "reachable_headers_only"}) as request:
            with mock.patch.object(access_tool.time, "sleep") as sleep:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(access_tool.main(["--catalog", str(catalog), "check"]), 0)
            self.assertEqual(request.call_count, 3)
            self.assertEqual(sleep.call_count, 2)
            request.reset_mock()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(access_tool.main(["--catalog", str(catalog), "check", "--ids", "UNKNOWN"]), 2)
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
