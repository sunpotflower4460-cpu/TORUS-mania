"""Versioned public data for E61–E63."""

import argparse
import shutil
from hashlib import file_digest
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from experiments.E65_crosscheck_returns import archive as reconstruction
from experiments.E66_image_only_track import archive as images

RAW = Path(__file__).resolve().parents[1] / "data/raw/embryo_history"
SOURCES = {
    "asai-article.xml": (
        "https://pmc-oa-opendata.s3.amazonaws.com/PMC11087055.1/PMC11087055.1.xml",
        "f75208516dfe062b2739fa13ec55d7f6f28434eef363978ffab6410289074f3d",
    ),
    "asai-fig1-supp1.jpg": (
        "https://pmc-oa-opendata.s3.amazonaws.com/PMC11087055.1/elife-89948-fig1-figsupp1.jpg",
        "25d0b94cf87c5db24a0a51477b2d3aa94114efad16380997a48863f442e6aae7",
    ),
    "shah-viewer-data.js": (
        "https://imb-dev.gitlab.io/cell-flow-navigator/prepareData/data.json?temp6",
        "f8afb07fb79eedda03825996b59ee2b45653f2a1f3fb1c6f31dde9aed7c09a3a",
    ),
    "zebrafish-tracks.zarr.zip": (
        "https://public.czbiohub.org/royerlab/zoo/Zebrafish/tracks_zebrafish_bundle.zarr.zip",
        "5660b35e36dc1fd123bd13bbff0d4bb8dd316bf7b8abfbfbc47bc31208647f06",
    ),
    reconstruction.ARCHIVE: (
        reconstruction.BASE,
        "f9bab4a47270512c6379492f07fb47c0edb077c9cc0cd402b4dca5625778b46b",
    ),
    images.ARCHIVE: (
        images.BASE,
        "8ec7f00ba8adcc7f59de3870d6c0e23c73d9da2a15226f11a451c9b044460ff7",
    ),
    "kunz-source.zip": (
        "https://pmc-oa-opendata.s3.amazonaws.com/PMC10241863.1/41467_2023_38988_MOESM9_ESM.zip",
        "737b3bb8ddc009e03e9e21fc50661ea4f8ba9b5b9b5de2ef0c9cb574a2c1216a",
    ),
    "kunz-fig1.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6142/10241863/52c29f7b16cf/41467_2023_38988_Fig1_HTML.jpg",
        "d9e83de488807f8818696f1920201595fa66be81538fc2ba591a11703dc70228",
    ),
}


ASSEMBLED_ARCHIVES = {
    reconstruction.ARCHIVE: reconstruction.download,
    images.ARCHIVE: images.download,
}


def verify(path, name):
    with path.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != SOURCES[name][1]:
            raise ValueError(f"Different source version for {path}")
    return path


def source(raw, name):
    return verify(raw / name, name)


def fetch(raw):
    raw.mkdir(parents=True, exist_ok=True)
    for name, (url, _) in SOURCES.items():
        destination = raw / name
        if not destination.exists():
            with NamedTemporaryFile(dir=raw, delete=False) as output:
                candidate = Path(output.name)
                try:
                    if name in ASSEMBLED_ARCHIVES:
                        output.close()
                        ASSEMBLED_ARCHIVES[name](candidate)
                    else:
                        with urlopen(url, timeout=45) as response:
                            shutil.copyfileobj(response, output)
                        output.flush()
                    verify(candidate, name)
                    candidate.replace(destination)
                finally:
                    candidate.unlink(missing_ok=True)
        source(raw, name)
        print(f"{name} verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    fetch(parser.parse_args().raw)
