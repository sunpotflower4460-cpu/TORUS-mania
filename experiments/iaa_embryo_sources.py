"""Public inputs for the next hypothesis tests, pinned by SHA-256."""

import argparse
import shutil
from hashlib import file_digest
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from experiments.E67_half_resolution import archive

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/iaa_embryo_work"
SOURCES = {
    "kerk-figure8.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/b50e/58929/a900412691c8/pp0305901008.jpg",
        "28e2d8e75f7941ecfb22a5ef09aea263e95a12064570216dd625e3348ddfcdff",
    ),
    "wilkins-abstract.json": (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:24477304&format=json&resultType=core",
        "bdc2423a239146a3ad017f4ac270f6bb40cf5810a3b1cabae628b80827e8d7db",
    ),
    "herrera-perez-figures.pdf": (
        "https://harvest.aps.org/v2/journals/articles/10.1103/PRXLife.1.013004/fulltext",
        "af4349605f415574e4e193c6b37b6a6346174dc7c7a438b1013216a31fce0b78",
    ),
    "martin-p892.png": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9365/1075445/6b5575234008/plntphys00603-0182.png",
        "8e76b9ea9e74f1d22aa882aaa9864809a8038b44490e6afcf287920b5c3b3aeb",
    ),
    "martin-p893.png": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9365/1075445/6f8bc8d6d53a/plntphys00603-0183.png",
        "26fd2cecbecda488c82b2066ba05ff7a844f75a77923b008d67e041db4a25c8a",
    ),
    "martin-p894.png": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9365/1075445/0b4ed5fe704b/plntphys00603-0184.png",
        "2060a541955b92012255b60b17a21fa949b1125aee08b9762d4f8bdd70cdd490",
    ),
}


def checked(path, expected):
    with path.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"Different source version for {path}")
    return path


def source(raw, name):
    return checked(raw / name, SOURCES[name][1])


def fetch(raw):
    raw.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in SOURCES.items():
        if not (raw / name).exists():
            with NamedTemporaryFile(dir=raw, delete=False) as tmp:
                path = Path(tmp.name)
                try:
                    with urlopen(url, timeout=40) as response:
                        shutil.copyfileobj(response, tmp)
                    tmp.close()
                    checked(path, digest).replace(raw / name)
                finally:
                    path.unlink(missing_ok=True)
        source(raw, name)
        print(f"{name} verified", flush=True)
    received = archive.fetch(raw / "level1")
    print(f"level 1 manifest SHA-256 {received}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    fetch(parser.parse_args().raw)
