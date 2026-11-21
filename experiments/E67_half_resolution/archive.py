"""Acquire the paper's 31 specified level-1 volume chunks with resumable downloads."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from experiments.E66_image_only_track.archive import BASE, FRAMES

LEVEL = "1"
EXPECTED_MANIFEST_SHA = (
    "31a5754f35645f7724c5395ab011b2685f9c6594cb31e94645daf5aa3fa6c3fb"
)
MEMBERS = (".zattrs", f"{LEVEL}/.zarray") + tuple(
    f"{LEVEL}/{t}/0/0/0/0" for t in FRAMES
)


def fetch_one(target, name):
    path = target / name
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        with NamedTemporaryFile(dir=path.parent, delete=False) as out:
            candidate = Path(out.name)
            try:
                with urlopen(BASE + name, timeout=70) as response:
                    expected_length = int(response.headers["Content-Length"])
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
                if out.tell() != expected_length:
                    raise OSError(f"Truncated image chunk {name}")
                out.close()
                candidate.replace(path)
                return
            except OSError:
                if attempt == 2:
                    raise
            finally:
                candidate.unlink(missing_ok=True)


def content_hash(target):
    """Hash a SHA-256 manifest in the pinned order, independently of archive metadata."""
    result = sha256()
    for member in MEMBERS:
        digest = sha256()
        with (target / member).open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        result.update(f"{digest.hexdigest()}  {member}\n".encode("ascii"))
    return result.hexdigest()


def fetch(target):
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda member: fetch_one(target, member), MEMBERS))
    digest = content_hash(target)
    if digest != EXPECTED_MANIFEST_SHA:
        raise ValueError("Unexpected level-1 archive version")
    return digest
