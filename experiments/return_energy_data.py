"""Source checks and image loading for the root and vortex experiments."""

from hashlib import sha256
import io
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/root_and_vortex"
RESULTS = ROOT / "research/results"


def verified(path, expected):
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected source version for {path}")
    return data


def rgb(data):
    with Image.open(io.BytesIO(data)) as image:
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def pdf_figure(data, page_number, xref):
    with fitz.open(stream=data, filetype="pdf") as pdf:
        if xref not in [image[0] for image in pdf[page_number].get_images()]:
            raise ValueError(f"Figure {xref} is missing on PDF page {page_number+1}")
        return rgb(pdf.extract_image(xref)["image"])
