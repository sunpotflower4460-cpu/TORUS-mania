"""Verify the figures, paper and movies used in E55–E60."""

import argparse
import shutil
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

from experiments.return_energy_data import verified

RAW = Path(__file__).resolve().parents[1] / "data/raw/particle_return"
SOURCES = {
    "pencikfig5.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e73b/3877806/6c6e17c9dcc5/pc_114421_f5.jpg",
        "df72091dca01dd4a70a7959bd4ac9577decc27dcb4db1b4a82e0f769265a633a",
    ),
    "pencikfig6.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e73b/3877806/5e9e3a0ad073/pc_114421_f6.jpg",
        "404bd0c877f9e21a189b23944f620dbfe1a3722ab92e7ec37e4d87eb219019dc",
    ),
    "ljungfig4.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/eddd/1087988/c116f3fab1b6/tpc1701090f04.jpg",
        "e7af7e5cd36fc3342cd28eaa08fd2942b5e9c4b7f390d2f9d47b3ed45cc6742c",
    ),
    "petersfig5.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/790e/2714926/6f32ebe032f9/tpc2101659f05.jpg",
        "c5c0e1c857d14622308435b31c3f8c78288f7d646ab31fd6f837497745d2e5cb",
    ),
    "auxsen.pdf": (
        "https://www.nature.com/articles/s41586-021-03425-2.pdf",
        "540255a7e2b7f72d0f09e9dbd734830808fe8babee63d5e73e209bb38a213671",
    ),
    "granule-plane.mov": (
        "https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s006",
        "dbcbdbcc5cdecdf56b5ce43ca00ab8b7a26524f6737a7b5acdc8b685a76b3930",
    ),
    "granule-volume.avi": (
        "https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0159917.s008",
        "9579a53bb2730a8178e7af2ef363a86c4651fee4e546675db39b625911d98aac",
    ),
    "wufig-5.png": (
        "https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41567-023-02223-z/MediaObjects/41567_2023_2223_Fig5_HTML.png",
        "9e81e6c8e191ec1b411b3adde644f5f399597511a28becb916db856b7f982080",
    ),
    "hayashi-source.xlsx": (
        "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-021-27020-1/MediaObjects/41467_2021_27020_MOESM4_ESM.xlsx",
        "4fe8d692c09ece8409debc663cd964de2acb90ea54beaa3097ffe9a7a7508de6",
    ),
}


def read(raw, name):
    return verified(raw / name, SOURCES[name][1])


def fetch(raw):
    """Write verified files atomically so an interrupted transfer can be retried."""
    raw.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in SOURCES.items():
        destination = raw / name
        if not destination.exists():
            request = Request(url, headers={"User-Agent": "TORUS-mania research replay"})
            with (
                urlopen(request, timeout=45) as response,
                NamedTemporaryFile(dir=raw, delete=False) as output,
            ):
                candidate = Path(output.name)
                try:
                    shutil.copyfileobj(response, output)
                    output.flush()
                    if sha256(candidate.read_bytes()).hexdigest() != digest:
                        raise ValueError(f"Different source version for {name}")
                    candidate.replace(destination)
                finally:
                    candidate.unlink(missing_ok=True)
        read(raw, name)
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
