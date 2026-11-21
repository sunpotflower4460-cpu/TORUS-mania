"""Fetch or verify the primary figures and workbooks used in E44–E48."""

import argparse
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

from experiments.return_energy_data import verified

RAW = Path(__file__).resolve().parents[1] / "data/raw/measured_return"
NDL = "https://dl.ndl.go.jp/view/prepareDownload?contentNo=1&itemId=info%3Andljp%2Fpid%2F"
PMC = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/"
PLOS = "https://journals.plos.org/"
SOURCES = {
    "vicia76.pdf": (NDL + "10767156", "bd3b7ae2f0737fe2fc85f40a3719af8155fee765f89f492733c37b6f8b8165ef"),
    "vicia78.pdf": (NDL + "10767564", "cef13427ec1faa271969dc1ec5462fa0527cb6e72ec7acb577c1263501c7f099"),
    "ruzicka5.jpg": (PMC + "5836/2890796/604eb15e5c4a/pnas.1005878107fig05.jpg",
                     "4d5685bf3a526bd195143b49f6af515b08611ecbfb45b8957de5e501e093743e"),
    "liu3.jpg": (PMC + "6b11/3320201/b502f507f0e0/PP_191288_gs_f3.jpg",
                 "9e477a0128f01c9ca0baab9000165847911ebce6deef302ebcc455de1f4091fe"),
    "piv_fields.xlsx": (PLOS + "plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s004",
                        "71dc8689d8f0ec4c17be5f7bdd1410ce173a69d7239c0728c7861f8ee6fc1a8f"),
    "niwayama3.png": (PLOS + "plosone/article/figure/image?size=large&id=info:doi/10.1371/journal.pone.0159917.g003",
                      "c739ec22d568c988b744327a125ed61d907cb82aab8f09539a6f9a448bbda0af"),
    "oocyte.xlsx": (PLOS + "plosbiology/article/file?type=supplementary&id=10.1371/journal.pbio.3001376.s007",
                    "b9b35776e7300b4ff4a4df783a4a74a6971b9aaf870ad69caa4c8259e3cc1a57"),
}


def read(raw, name):
    return verified(raw / name, SOURCES[name][1])


def fetch(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, (url, checksum) in SOURCES.items():
        destination = directory / name
        if destination.exists():
            read(directory, name)
        else:
            with urlopen(Request(url, headers={"User-Agent": "TORUS-mania research replay"}), timeout=60) as response:
                data = response.read()
            if sha256(data).hexdigest() != checksum:
                raise ValueError(f"Unexpected download for {name}")
            with NamedTemporaryFile(dir=directory, delete=False) as temporary:
                temporary.write(data)
            Path(temporary.name).replace(destination)
        print(f"{name} verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    fetch(parser.parse_args().raw)
