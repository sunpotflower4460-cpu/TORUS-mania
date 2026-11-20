"""Read the four mean bars in Casimiro et al. Figure 3 from its public archive."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

URL = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/3d6c/135543/7b1793bbd171/00-0486f3.jpg"
SHA256 = "b28827ec60aff2913effd1b5bccdaa1f355cc003bbeb7b85aacae1107e5dd881"
Y_ZERO, Y_TOP, TOP_VALUE = 312., 8., .9
BAR_INTERIORS = {
    "A_no_treatment": (105, 154),
    "B_NAA": (184, 230),
    "C_NPA": (260, 293),
    "D_NPA_plus_NAA": (339, 388),
}


def read(source):
    if sha256(source.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Image checksum differs from the archived figure")
    with Image.open(source) as image:
        pixels = np.asarray(image.convert("L"))
    groups = {}
    for name, (lo, hi) in BAR_INTERIORS.items():
        # The top outline spans the interior. The hatch and the SD cap do not.
        dark = (pixels[:int(Y_ZERO)-3, lo:hi] < 115).mean(axis=1)
        lines = np.flatnonzero(dark > .83)
        top = float(lines[0]) if lines.size else Y_ZERO
        groups[name] = {"top_row": top, "detected_bar_above_axis": bool(lines.size),
                        "lateral_roots_per_mm": TOP_VALUE * (Y_ZERO-top) / (Y_ZERO-Y_TOP)}
    return {"source_url": URL, "source_sha256": SHA256, "units": "emerged lateral roots per mm primary root",
            "axis_calibration_y_0_and_0_9": [Y_ZERO, Y_TOP],
            "readout_uncertainty_per_mm_from_3px": 3*TOP_VALUE/(Y_ZERO-Y_TOP), "bars": groups}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(read(args.figure), indent=2) + "\n", encoding="utf-8")
