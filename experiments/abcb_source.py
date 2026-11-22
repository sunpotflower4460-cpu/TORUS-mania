"""Read the pinned Chen 2023 source workbooks without changing or redistributing them.

Only Python's standard library is required.  ElementTree/float extraction is checked
against a separate minidom/Decimal read of the registered cells.  Original workbooks
stay in an external cache; result files contain aggregates and cell provenance only.
"""

import argparse
from collections import Counter
from decimal import Decimal, localcontext
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import posixpath
import re
import statistics
import tempfile
from urllib.request import Request, urlopen
from xml.dom import minidom
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/sources/chen2023_manifest.json"
BASE_COMMIT = "39513901949d240066e066f5dfd41a1db9808c6f"
REGISTRATION_COMMIT = "6ccbe7dfcab0e96db4ee4fec4badfd19cd631e4e"
REGISTRATIONS = {
    "E79": ("research/registrations/E79-abcb-clock-source-data.md",
            "82cac4071cb71cf3c798aee09be5472155294bfe2f64de265d469ee523507c98"),
    "E80": ("research/registrations/E80-abcb-transport-growth-audit.md",
            "edc561ad946708d49ed842a145eddd9077ca05b10c928b965fb8a2fc8f4d8cc0"),
}
PINNED_FILES = {
    "8f12998383b368adeb33db2f0de497bb1f6f1f7c4804863f2286bd4ba789b059",
    "afe491baa0888b5e4f74971bf8cd672c8d29485ee88b892b5c0143d908e8592e",
    "e24bf364680d68a41551b9a480e3b0496c4147d3464ae078d3c0bad82d2d0108",
}
FIG4_WORKBOOK_SHA256 = "66b2fe0db6ac1557cfc3c3f41519758d8aad177477fd7f40bf9d854d751488c6"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def registration(experiment):
    path, expected = REGISTRATIONS[experiment]
    actual = sha256((ROOT / path).read_bytes())
    if actual != expected:
        raise ValueError(f"Published {experiment} registration changed: {path}")
    return {"path": path, "sha256": actual, "commit": REGISTRATION_COMMIT}


def parser(description, default_out):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--out", type=Path, default=default_out)
    result.add_argument("--cache", type=Path,
                        default=Path(tempfile.gettempdir()) / "torus-chen2023-cache",
                        help="Original-file cache outside this git checkout")
    result.add_argument("--offline", action="store_true", help="Require verified cached originals")
    return result


class Sources:
    def __init__(self, cache, offline=False):
        self.cache, self.offline = Path(cache).resolve(), offline
        if self.cache == ROOT or ROOT in self.cache.parents:
            raise ValueError("Keep original-file cache outside the git checkout")
        self.manifest_bytes = MANIFEST.read_bytes()
        self.manifest = json.loads(self.manifest_bytes)
        if self.manifest.get("schema_version") != 1:
            raise ValueError("Unsupported Chen source-manifest schema")
        self.files = {item["id"]: item for item in self.manifest["files"]}
        self.workbooks = {}

    def fetch(self, file_id):
        item = self.files[file_id]
        if item["sha256"] not in PINNED_FILES:
            raise ValueError(f"Not an E79/E80 registered data file: {file_id}")
        basename = item["local_basename"]
        if Path(basename).name != basename:
            raise ValueError("Unsafe cache basename")
        path = self.cache / basename
        if path.exists():
            data = path.read_bytes()
        elif self.offline:
            raise FileNotFoundError(f"Missing registered source in offline cache: {path}")
        else:
            self.cache.mkdir(parents=True, exist_ok=True)
            if not item["url"].startswith("https://"):
                raise ValueError("Use a public HTTPS original-source URL")
            request = Request(item["url"], headers={"User-Agent": "TORUS-mania-research/1.0"})
            with urlopen(request, timeout=30) as response:
                data = response.read(50_000_001)
            if len(data) > 50_000_000 or sha256(data) != item["sha256"]:
                raise ValueError(f"Downloaded source fails size/hash verification: {file_id}")
            path.write_bytes(data)
        if sha256(data) != item["sha256"]:
            raise ValueError(f"Cached source hash differs; use a fresh cache: {path}")
        return data

    def workbook(self, dataset):
        key = (dataset["file_id"], dataset.get("archive_member"))
        if key not in self.workbooks:
            data = self.fetch(key[0])
            if key[1]:
                with ZipFile(BytesIO(data)) as archive:
                    data = archive.read(key[1])
                if sha256(data) != FIG4_WORKBOOK_SHA256:
                    raise ValueError("Fig.4 inner workbook hash differs")
            self.workbooks[key] = Workbook(data)
        return self.workbooks[key]

    def provenance(self, dataset):
        item = self.files[dataset["file_id"]]
        return {"manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
                "manifest_sha256": sha256(self.manifest_bytes), "file_id": item["id"],
                "url": item["url"], "sha256": item["sha256"],
                "archive_member": dataset.get("archive_member"),
                "workbook_sha256": sha256(self.workbook(dataset).data),
                "sheet": dataset["sheet"]}

    def by_ranges(self, sheet, ranges):
        expected = set(ranges)
        matched = [d for d in self.manifest["datasets"] if d["sheet"] == sheet
                   and {g["range"] for g in d["groups"]} == expected]
        if len(matched) != 1:
            raise ValueError(f"Expected one manifest dataset for {sheet} {sorted(expected)}")
        return matched[0]


class Workbook:
    def __init__(self, data):
        self.data = data
        with ZipFile(BytesIO(data)) as archive:
            self.parts = {name: archive.read(name) for name in archive.namelist()
                          if name.endswith(".xml") or name.endswith(".rels")}
        strings = self.parts.get("xl/sharedStrings.xml")
        self.strings = [] if strings is None else [
            "".join(node.itertext()) for node in ET.fromstring(strings).findall("s:si", NS)]
        links = {r.attrib["Id"]: r.attrib["Target"] for r in
                 ET.fromstring(self.parts["xl/_rels/workbook.xml.rels"])}
        self.sheets = {}
        for sheet in ET.fromstring(self.parts["xl/workbook.xml"]).findall("s:sheets/s:sheet", NS):
            target = links[sheet.attrib[f"{{{REL_NS}}}id"]]
            part = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            self.sheets[sheet.attrib["name"]] = part
        self.cells = {}

    def sheet(self, name):
        if name not in self.cells:
            tree = ET.fromstring(self.parts[self.sheets[name]])
            result = {}
            for cell in tree.findall(".//s:sheetData/s:row/s:c", NS):
                typ = cell.attrib.get("t", "n")
                value = cell.findtext("s:v", default="", namespaces=NS)
                if typ == "s":
                    value = self.strings[int(value)]
                elif typ == "inlineStr":
                    value = "".join(cell.find("s:is", NS).itertext())
                result[cell.attrib["r"]] = {"type": typ, "text": value,
                    "formula": cell.findtext("s:f", default=None, namespaces=NS)}
            self.cells[name] = result
        return self.cells[name]

    def independent_decimals(self, sheet, refs):
        """Read the XML again with a different parser and exact decimal arithmetic."""
        def texts(element, tag):
            return ["".join(n.data for n in e.childNodes if n.nodeType in (n.TEXT_NODE, n.CDATA_SECTION_NODE))
                    for e in element.getElementsByTagNameNS(NS["s"], tag)]
        shared = []
        if "xl/sharedStrings.xml" in self.parts:
            doc = minidom.parseString(self.parts["xl/sharedStrings.xml"])
            shared = ["".join(texts(item, "t")) for item in doc.getElementsByTagNameNS(NS["s"], "si")]
            doc.unlink()
        doc = minidom.parseString(self.parts[self.sheets[sheet]])
        extracted = {}
        for item in doc.getElementsByTagNameNS(NS["s"], "c"):
            ref = item.getAttribute("r")
            if ref not in refs:
                continue
            typ = item.getAttribute("t") or "n"
            value = "".join(texts(item, "v"))
            if typ == "s":
                value = shared[int(value)]
            elif typ == "inlineStr":
                value = "".join(texts(item, "t"))
            if value.strip():
                extracted[ref] = Decimal(value.strip())
        doc.unlink()
        return [extracted[r] for r in refs if r in extracted]


def addresses(cell_range):
    start, end = cell_range.split(":")
    a, b = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", start), re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", end)
    if not a or not b or a[1] != b[1] or int(b[2]) < int(a[2]):
        raise ValueError("Registered extraction uses ordered single-column cell ranges")
    return [a[1] + str(row) for row in range(int(a[2]), int(b[2]) + 1)]


def extract(workbook, sheet, group):
    refs = addresses(group["range"])
    cells, values, counts = workbook.sheet(sheet), [], Counter()
    missing, nonnumeric, formulas = [], [], []
    numeric_strings = 0
    for ref in refs:
        cell = cells.get(ref)
        if cell is None or not cell["text"].strip():
            missing.append(ref)
            continue
        counts[cell["type"]] += 1
        if cell["formula"] is not None:
            formulas.append(ref)
        try:
            number = float(cell["text"].strip())
        except ValueError:
            nonnumeric.append(ref)
            continue
        if not math.isfinite(number) or cell["type"] in ("b", "e"):
            raise ValueError(f"Invalid observation at {sheet}!{ref}")
        values.append(number)
        numeric_strings += cell["type"] in ("s", "str", "inlineStr")
    if nonnumeric or formulas:
        raise ValueError(f"Unexpected text/formulas inside registered observations: {nonnumeric} {formulas}")
    independent = workbook.independent_decimals(sheet, refs)
    if len(values) != group["n_values"] or len(values) != len(independent):
        raise ValueError(f"Registered count differs at {sheet}!{group['range']}")
    cell_error = max((abs(x - float(y)) for x, y in zip(values, independent)), default=0.0)
    sum_error = abs(math.fsum(values) - float(sum(independent, Decimal(0))))
    if cell_error > 1e-12 or sum_error > 1e-10 * max(1.0, abs(math.fsum(values))):
        raise ValueError("Independent cell/sum extraction differs")
    info = {"label": group["label"], "range": group["range"], "n_numeric_values": len(values),
            "n_registered_cells": len(refs), "xml_cell_type_counts": dict(sorted(counts.items())),
            "numeric_string_count": int(numeric_strings), "missing_cells": missing,
            "n_nonpositive": sum(v <= 0 for v in values), "n_zero": values.count(0.0),
            "caption_n": group.get("caption_n"),
            "numeric_count_equals_caption_n": len(values) == group.get("caption_n"),
            "independent_read_max_cell_difference": cell_error,
            "independent_read_sum_difference": sum_error}
    expected_types = group.get("xml_cell_type_counts")
    if expected_types is not None and dict(counts) != expected_types:
        raise ValueError(f"Cell type counts differ from manifest at {group['range']}")
    return values, independent, info


def describe(values):
    n = len(values)
    q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
    positive = all(value > 0 for value in values)
    return {"n": n, "arithmetic_mean": math.fsum(values) / n,
            "sample_standard_deviation": statistics.stdev(values) if n > 1 else None,
            "median": statistics.median(values), "q1": q1, "q3": q3,
            "interquartile_range": q3 - q1, "minimum": min(values), "maximum": max(values),
            "geometric_mean": math.exp(math.fsum(math.log(x) for x in values) / n) if positive else None,
            "geometric_mean_status": "computed_all_values_positive" if positive else "not_computed_nonpositive_values"}


def decimal_description(values):
    with localcontext() as context:
        context.prec = 50
        n, total = Decimal(len(values)), sum(values, Decimal(0))
        mean = total / n
        sd = (sum(((v - mean)**2 for v in values), Decimal(0)) / (n - 1)).sqrt() if n > 1 else None
        geometric = (sum((v.ln() for v in values), Decimal(0)) / n).exp() if all(v > 0 for v in values) else None
        return {"arithmetic_mean": float(mean), "sample_standard_deviation": float(sd) if sd is not None else None,
                "geometric_mean": float(geometric) if geometric is not None else None}


def compare(control, intervention):
    ca, ia = control["arithmetic_mean"], intervention["arithmetic_mean"]
    cg, ig = control.get("geometric_mean"), intervention.get("geometric_mean")
    return {"arithmetic_mean_difference_intervention_minus_WT": ia - ca,
            "arithmetic_mean_ratio_intervention_over_WT": ia / ca if ca != 0 else None,
            "geometric_mean_ratio_intervention_over_WT": ig / cg if cg and ig is not None else None}


def numeric_error(first, second):
    return max((abs(first[k] - second[k]) / max(1.0, abs(second[k]))
                for k in second if first[k] is not None and second[k] is not None), default=0.0)


def verify_headers(workbook, dataset):
    headers = dataset.get("header_cells", [])
    if isinstance(headers, dict):
        headers = [{"cell": key, "text": value} for key, value in headers.items()]
    result = []
    cells = workbook.sheet(dataset["sheet"])
    for item in headers:
        actual = cells.get(item["cell"], {}).get("text", "")
        result.append({"cell": item["cell"], "text": actual, "matches_manifest": actual == item["text"]})
        if actual != item["text"]:
            raise ValueError(f"Registered header differs: {dataset['sheet']}!{item['cell']}")
    return result


def save_result(out, summary, *code_files):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    summary["code_sha256"] = {Path(p).relative_to(ROOT).as_posix(): sha256(Path(p).read_bytes())
                              for p in (Path(__file__), *map(Path, code_files))}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    failed = [key for key, value in summary["checks"].items() if not value]
    if failed:
        raise ValueError("Numerical/input checks failed: " + ", ".join(failed))
    print(f"{summary['experiment']}: {len(summary['checks'])} numerical/input checks passed")

