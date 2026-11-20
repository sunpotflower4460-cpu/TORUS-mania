"""Read the registered bar heights from the versioned Marhavý figures."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image


FIGURES = {
    "m13_f2.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4191/3545298/39a8a79bd4a3/emboj2012303f2.jpg",
        "6c8ea7438a09f076d47df6cace06bea80f4156b02f2b3cd5c1910a44b00cd839",
    ),
    "m13_f3.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4191/3545298/67c87ff286a1/emboj2012303f3.jpg",
        "08d8b60940c494254537814f341baa643054fbdaa21f56fbad07d39d508f2b25",
    ),
    "m13_f4.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4191/3545298/779a927a2390/emboj2012303f4.jpg",
        "ac2c5204d18318ef6f513d5367475961ea4dcb83793c874355a47e03e26355aa",
    ),
    "m16_f6.jpg": (
        "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/1fff/4762431/567c1e2c187a/471f06.jpg",
        "fb648543b2da52024ace0a3e541da071b5822f08b0c2c4c08e177896372b9a98",
    ),
}

# Image-relative coordinates. Each horizontal slice sits inside one bar.
PANELS = {
    "fig2d_founder_postbend": ("m13_f2.jpg", 267, 169, 350, ((185, 194), (249, 258))),
    "fig3b_founder_density": ("m13_f3.jpg", 351, 208, 8, ((72, 86), (105, 120), (188, 200), (220, 234))),
    "fig3c_lri_density": ("m13_f3.jpg", 351, 210, 8, ((335, 349), (362, 376), (427, 442), (454, 469))),
    "fig3d_combined_density": ("m13_f3.jpg", 351, 209, 12, ((565, 577), (591, 604), (657, 670), (681, 694))),
    "fig3e_stage_I": ("m13_f3.jpg", 638, 416, 8, ((104, 109), (112, 116), (119, 123), (126, 130))),
    "fig4b_stage_I": ("m13_f4.jpg", 482, 213, 7, ((63, 68), (74, 79), (84, 89), (94, 99))),
    "fig6e_total": ("m16_f6.jpg", 1184, 934, 4.5, ((81, 88), (97, 104), (126, 133), (141, 148))),
    "fig6e_anticlinal": ("m16_f6.jpg", 1184, 934, 4.5, ((177, 184), (193, 200), (222, 229), (237, 244))),
    "fig6e_periclinal": ("m16_f6.jpg", 1184, 934, 4.5, ((274, 282), (289, 296), (319, 326), (334, 341))),
}


def bar_top(pixels, zero_row, left, right):
    interior = pixels[:zero_row - 3, left:right]
    # An empty bar position has a white strip immediately above the axis.
    near_axis = np.median(interior[-6:], axis=(0, 1))
    if near_axis.min() > 242:
        return zero_row
    filled = (np.linalg.norm(interior - 255., axis=2) > 68.).mean(axis=1) >= .68
    # Scan up from the bar's base, allowing at most two pale rows within a fill.
    gaps = np.flatnonzero(np.convolve(~filled, np.ones(3), mode="valid") == 3)
    if not gaps.size:
        raise ValueError(f"Bar interior at columns {left}–{right} has no readable background above it")
    return int(gaps[-1] + 3)


def read(raw):
    pixels = {}
    sources = {}
    for name, (url, digest) in FIGURES.items():
        path = raw / name
        if sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Unexpected figure version: {path}")
        with Image.open(path) as image:
            pixels[name] = np.asarray(image.convert("RGB"), dtype=float)
            sources[name] = {"url": url, "sha256": digest, "width_height_px": image.size}
    panels = {}
    for panel, (name, zero, tick, value_at_tick, columns) in PANELS.items():
        scale = value_at_tick / (zero - tick)
        top = [bar_top(pixels[name], zero, l, r) for l, r in columns]
        panels[panel] = {
            "file": name, "zero_row": zero, "tick_row": tick, "tick_value": value_at_tick,
            "interior_columns": columns, "bar_top_rows": top,
            "values": [(zero - t) * scale for t in top], "digitization_halfwidth": 3 * scale,
        }
    return {"sources": sources, "panels": panels}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/local_reflux"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(read(args.raw), indent=2) + "\n", encoding="utf-8")
