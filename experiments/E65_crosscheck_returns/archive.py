"""Package the paper-linked InTRACKtive chunks for an exact replay."""

import json
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from zipfile import ZipFile, ZipInfo

BASE = "https://public.czbiohub.org/royerlab/ultrack/inTRACKtive/Sparse_Embryo_tracks_with_hex_bundle.zarr/"
ARCHIVE = "paper-zebrafish-chunks.zip"
ARRAYS = ("points", "points_to_tracks/indptr", "points_to_tracks/indices")


def fetch_member(member):
    for attempt in range(3):
        try:
            with urlopen(BASE + member, timeout=30) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise


def download(destination):
    metadata = {
        array + "/.zarray": fetch_member(array + "/.zarray") for array in ARRAYS
    }
    metadata["points/.zattrs"] = fetch_member("points/.zattrs")
    members = []
    for array in ARRAYS:
        spec = json.loads(metadata[array + "/.zarray"])
        shape, chunk = spec["shape"], spec["chunks"]
        if shape[1:] != chunk[1:]:
            raise ValueError(f"Unexpected layout at {array}")
        chunks = (shape[0] + chunk[0] - 1) // chunk[0]
        members.extend(
            f"{array}/{index}" + ".0" * (len(shape) - 1) for index in range(chunks)
        )
    with (
        ZipFile(destination, "w") as archive,
        ThreadPoolExecutor(max_workers=12) as pool,
    ):
        for name, content in sorted(metadata.items()):
            archive.writestr(ZipInfo(name), content)
        for name, content in zip(members, pool.map(fetch_member, members), strict=True):
            archive.writestr(ZipInfo(name), content)
