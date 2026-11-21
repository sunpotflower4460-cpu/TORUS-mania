"""Fetch the pinned chick, zebrafish, and maize primary sources for E72–E75."""

import argparse
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from experiments.iaa_embryo_sources import checked

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/calibrated_formation"
_NATURE = (
    "https://static-content.springer.com/esm/art%3A10.1038%2Fs41563-024-01942-9/"
    "MediaObjects/41563_2024_1942_MOESM"
)
_PMC = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/"
SOURCES = {
    "neural-main.xlsx": (
        _NATURE + "2_ESM.xlsx",
        "ded627caf90bf1c66273f705ae1d440c0ef73600276a1cb6c481d8ca35539219",
    ),
    "neural-extended.xlsx": (
        _NATURE + "3_ESM.xlsx",
        "c9b2b414a050e888ff8453eebeccb3cbc2cbe5d1df072da061d74af77592aad0",
    ),
    "epiboly-fig2.jpg": (
        _PMC + "eab0/5210093/eba7249a1b9e/EMBJ-36-25-g003.jpg",
        "da94a944875c51add787c02d3c01ac6d79b3b4910d6a655cd7c3cf5773c25d4f",
    ),
    "epiboly-fig4.jpg": (
        _PMC + "eab0/5210093/631c70bb4e97/EMBJ-36-25-g005.jpg",
        "3c17de42d5e0490cff002036ddb1efcd3385df3098b2bc7bfe2f6b66e15c2782",
    ),
    "lee-p824.png": (
        _PMC + "e00c/1064613/7e5513d7337e/plntphys00586-0040.png",
        "93463ce88ceb664dfcdceda17edefc65d0efca729bf6d9ce048115521d8f17c3",
    ),
    "lee-p825.png": (
        _PMC + "e00c/1064613/69f5c37e7f66/plntphys00586-0041.png",
        "d4993897bad2008618f10dccb0d03d754dbbda114d2107cfefcab20de642008e",
    ),
    "lee-p826.png": (
        _PMC + "e00c/1064613/978d944e6f57/plntphys00586-0042.png",
        "ac3812fa91464bbe3cced8fde55f49363353d15902f5b58e4e442c291cf19685",
    ),
    "hasenstein-p890.png": (
        _PMC + "1ef0/1054589/8bac0b9348a3/plntphys00624-0256.png",
        "aadd9c67dc91d3a885c21371245a097fea1e7608870bf9b94b678bddbc1f583c",
    ),
    "hasenstein-p891.png": (
        _PMC + "1ef0/1054589/398483250acb/plntphys00624-0257.png",
        "52d045654c49e27aa36a2ddb7424e908b6cb1395dfae4ae09c88f5733eaf916f",
    ),
    "hasenstein-p892.png": (
        _PMC + "1ef0/1054589/f73e4324b6bf/plntphys00624-0258.png",
        "ba2af383b55389758bee90fc6597d58bb492b702d0455adf0f7d6ecf4e0e31b2",
    ),
    "hasenstein-p893.png": (
        _PMC + "1ef0/1054589/2e106b34a5c3/plntphys00624-0259.png",
        "e8418c31041f0ff47899f783c073366ee9cea34152b4d96cac0b31971b2e157e",
    ),
}


def source(raw, name):
    return checked(raw / name, SOURCES[name][1])


def verified_inputs(raw, names):
    for name in names:
        source(raw, name)
    return {name: SOURCES[name][1] for name in names}


def fetch(raw):
    raw.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in SOURCES.items():
        target = raw / name
        if not target.exists():
            with NamedTemporaryFile(dir=raw, delete=False) as tmp:
                path = Path(tmp.name)
                try:
                    with urlopen(url, timeout=40) as response:
                        shutil.copyfileobj(response, tmp)
                    tmp.close()
                    checked(path, digest).replace(target)
                finally:
                    path.unlink(missing_ok=True)
        source(raw, name)
        print(f"{name} verified", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    fetch(parser.parse_args().raw)
