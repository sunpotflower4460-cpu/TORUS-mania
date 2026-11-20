"""Recover Fig. 4B's mean root counts from the archived publication JPEG."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

URL = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/c89d/4762386/61856cae1d19/exbotj_erv541_f0004.jpg"
SHA256 = "828e8ad52730315b9d3751274f3d6ad1d2dbedd4de321ebc3bea0d6a1a7b20c8"
Y_ZERO = 523.
Y_TEN = 289.
CENTERS = {2: 124, 3: 138, 4: 151, 6: 178, 9: 217, 12: 257, 18: 337, 24: 417}


def read(image_path):
    if sha256(image_path.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Unexpected Fig. 4 JPEG checksum")
    with Image.open(image_path) as img:
        array = np.asarray(img.convert("RGB"), dtype=np.int16)
    measured = []
    for hours, x in CENTERS.items():
        # Blue upper markers are the combined count of emerged roots and primordia.
        start, stop = 315, 455
        red, green, blue = np.moveaxis(array[start:stop, x-4:x+5], -1, 0)
        selected = (blue - red > 40) & (green - red > 17) & (red < 120)
        y_pixels, _ = np.nonzero(selected)
        if y_pixels.size < 25:
            raise ValueError(f"Failed to identify the marker for {hours:g} h")
        y = float(np.median(y_pixels) + start)
        measured.append({"hours": hours, "x_px": x, "y_px": y,
                         "root_and_primordia_per_day": 10 * (Y_ZERO-y)/(Y_ZERO-Y_TEN)})
    return {"source_url": URL, "source_sha256": SHA256,
            "axis_calibration_y_0_and_10": [Y_ZERO, Y_TEN],
            "rate_uncertainty_from_3px": 30 / (Y_ZERO - Y_TEN),
            "one_hour_not_scored": "The paper defines the forced bending range as 2–24 h.",
            "periods": measured}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(read(args.figure), indent=2) + "\n", encoding="utf-8")
