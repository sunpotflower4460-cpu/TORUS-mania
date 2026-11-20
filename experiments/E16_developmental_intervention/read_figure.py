"""Read the stacked fractions in Djenoune et al. Fig. 4F/G from its public JPEG."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

SOURCE = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/08ff/9939240/8b4eeafb05d5/nihms-1870894-f0004.jpg"
SHA256 = "5ab6850534d67aebb2cf7b1be8cf7b33f18036e3452685e22a0a46f56ee51865"
PANELS = {
    "F": {
        "top": 52, "bottom": 256,
        "palette_bottom_first": [(16, 77, 148), (228, 46, 150), (0, 164, 70)],
        "categories_bottom_first": ["dand5_right", "dand5_bilateral", "dand5_left"],
        "bars": [("uninjected", 481, 66), ("flow_deficient", 537, 62), ("left_stimulated", 593, 42)],
    },
    "G": {
        "top": 430, "bottom": 635,
        "palette_bottom_first": [(0, 161, 206), (229, 32, 147), (0, 164, 70)],
        "categories_bottom_first": ["heart_left", "heart_middle", "heart_right"],
        "bars": [("uninjected", 481, 85), ("injection_control", 537, 77), ("flow_deficient", 593, 53),
                 ("left_stimulated", 649, 51), ("right_stimulated", 704, 49)],
    },
}


def group_fraction(rgb, x, top, bottom, palette):
    observed = np.median(rgb[top:bottom+1, x-3:x+4], axis=1)
    distance = np.linalg.norm(observed[:, None, :] - palette[None, :, :], axis=-1)
    labels = np.where(distance.min(axis=1) < 70, distance.argmin(axis=1), -1)
    if np.any(np.diff(labels[labels != -1]) > 0):
        raise ValueError(f"Unexpected color order in bar at x={x}")
    cumulative = []
    y = np.arange(top, bottom+1)
    for category in (0, 1):
        below = y[(labels >= 0) & (labels <= category)]
        above = y[labels > category]
        if not len(below):
            boundary = bottom
        elif not len(above):
            boundary = top
        else:
            boundary = (below.min() + above.max()) / 2
        cumulative.append(float((bottom-boundary)/(bottom-top)))
    return {"x": x, "cumulative_fractions": cumulative}


def read(image_path):
    if sha256(image_path.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Figure hash differs from the preserved access record")
    with Image.open(image_path) as image:
        rgb = np.asarray(image.convert("RGB"))
    measurements = {}
    for panel, spec in PANELS.items():
        palette = np.array(spec["palette_bottom_first"])
        top, bottom = spec["top"], spec["bottom"]
        groups = {name: {"n": n, **group_fraction(rgb, x, top, bottom, palette)}
                  for name, x, n in spec["bars"]}
        measurements[panel] = {"categories": spec["categories_bottom_first"],
                               "y_bounds": [top, bottom], "groups": groups}
    return {"source_url": SOURCE, "source_sha256": SHA256, "source_size_px": [rgb.shape[1], rgb.shape[0]],
            "tolerance_fraction": .015, "panels": measurements}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(read(args.figure), indent=2) + "\n", encoding="utf-8")
