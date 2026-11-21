"""Verified publications and source tables for E49–E54."""

import argparse
import json
import re
from hashlib import sha256
from html import unescape
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

from experiments.measured_return_sources import SOURCES as PREVIOUS
from experiments.return_energy_data import verified

RAW = Path(__file__).resolve().parents[1] / "data/raw/turning_paths"
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/"
BLOBS = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/"
KIM = "https://pmc-oa-opendata.s3.amazonaws.com/PMC7521852.1/"
SOURCES = {
    "rashotte_fig3.jpg": (
        BLOBS + "b135/219050/c90cfa6d2df7/pp1038176003.jpg",
        "b1b7e71ab2d0fd7d86517962c114b34fa39365904cb2aed12b1f95b7612bff41",
    ),
    "rashotte_table1.json": (
        PMC + "PMC219050/",
        "21a2760d10585d6349c5873531eaefe7110cd8a1c4fc275d4a2a8ca96a404df4",
    ),
    "lewis_fig2.jpg": (
        BLOBS + "cfe6/1955737/8055e6675458/tpc1901838f02.jpg",
        "d5dc325af197a1a8a1e91bb40bb55c0758f481a6e930b0a5fed208e94fa4471e",
    ),
    "wu_fig8.jpg": (
        BLOBS + "b53a/1955722/f3cc8b58ad7c/tpc1901826f08.jpg",
        "a54f674f93c58cd78f507f218378b4ef18c6ca67c78be853d06be94539d24950",
    ),
    "wu_fig9.jpg": (
        BLOBS + "b53a/1955722/b76eee89a94e/tpc1901826f09.jpg",
        "f243548c7f169c3c964c020e1594bcd8e2c7b9d3c92bceb238898dd1ed31f521",
    ),
    "wu_table1.json": (
        PMC + "PMC1955722/",
        "8f512fd965a45faeccf03a1ed7a8c843a77d42333c41c094c556679fc355abe6",
    ),
    "piv_fields.xlsx": PREVIOUS["piv_fields.xlsx"],
    "mittasch.pdf": (
        "https://tu-dresden.de/mn/math/wir/ressourcen/dateien/forschung/publikationen/pdf2018/Mittasch2018.pdf?lang=de",
        "8c9140c38144481f6defa9e8799ecb3f11efd0c253adca1c87ab001ef9ed9f3e",
    ),
    "kimura.pdf": (
        KIM + "PMC7521852.1.pdf",
        "68faabf7445442200537af00ed9dd7eec735b5dec370732d0bb026c8c5b7dea8",
    ),
    "ng.pdf": (
        "https://publikationen.bibliothek.kit.edu/1000168316/152241581",
        "b101f3bb7ea5a3e315e8ff529502eb1db2f8b0827fe4d2480f28f42079e92131",
    ),
    "kimura.xml": (
        KIM + "PMC7521852.1.xml",
        "80a8cdd07e16454023757f4d1e416a06bfb9290c09e997dc375e0176f894e345",
    ),
}


def table_one(data):
    """Pin the cells of the published first table, independent of the PMC page header."""
    page = data.decode("utf-8")
    table = re.search(r'<section\b[^>]*\bid="tbl1"[^>]*>.*?<table\b[^>]*>(.*?)</table>', page, re.DOTALL)
    if table is None:
        raise ValueError("Missing PMC Table 1")
    rows = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table[1], re.DOTALL):
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, re.DOTALL)
        rows.append([" ".join(unescape(re.sub(r"<[^>]+>", "", cell)).split()) for cell in cells])
    return (json.dumps(rows, ensure_ascii=False, indent=2) + "\n").encode()


def read(directory, name):
    return verified(directory / name, SOURCES[name][1])


def fetch(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in SOURCES.items():
        path = directory / name
        if not path.exists():
            request = Request(url, headers={"User-Agent": "TORUS-mania research replay"})
            with urlopen(request, timeout=55) as response:
                data = response.read()
            if name.endswith("_table1.json"):
                data = table_one(data)
            if sha256(data).hexdigest() != digest:
                raise ValueError(f"Unexpected source content for {name}")
            with NamedTemporaryFile(dir=directory, delete=False) as temp:
                temp.write(data)
            Path(temp.name).replace(path)
        read(directory, name)
        print(f"{name} verified")


def run_one(run):
    parser = argparse.ArgumentParser(description=run.__module__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw, args.out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    fetch(parser.parse_args().raw)
