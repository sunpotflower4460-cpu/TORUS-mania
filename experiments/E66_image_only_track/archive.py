"""Fetch the fixed source stack containing the registered fluorescence test."""

from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from zipfile import ZipFile, ZipInfo

BASE = "https://public.czbiohub.org/royerlab/ultrack/zebrafish_embryo.ome.zarr/"
ARCHIVE = "sparse-image-level2-frames308-338.zip"
FRAMES = range(308, 339)
LEVEL = "2"


def read_remote(name):
    for attempt in range(3):
        try:
            with urlopen(BASE + name, timeout=45) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise


def download(destination):
    names = [".zattrs", f"{LEVEL}/.zarray"] + [
        f"{LEVEL}/{frame}/0/0/0/0" for frame in FRAMES
    ]
    with (
        ZipFile(destination, "w") as archive,
        ThreadPoolExecutor(max_workers=8) as pool,
    ):
        for name, data in zip(names, pool.map(read_remote, names), strict=True):
            archive.writestr(ZipInfo(name), data)
