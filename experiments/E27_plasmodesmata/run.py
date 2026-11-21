"""Digitize the published Mellor et al. comparisons."""

import argparse
from hashlib import sha256
from pathlib import Path

import numpy as np
from PIL import Image

from experiments.common import save_summary
from experiments.local_reflux_reading import bar_top

ROOT = Path(__file__).resolve().parents[2]
CDN = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/64f6/7132777/"
FIGURES = {
    "mellor_fig2.jpg": ("82245338738c/develop-147-181669-g2.jpg",
                        "671ebc7a23b167bbb36981bf5995f52008a1ff77ac834605ce95e1172a004f8b"),
    "mellor_fig4.jpg": ("087276e63c38/develop-147-181669-g4.jpg",
                        "f0b858b420915308ab5c5f74fa17ab0313c637a3d16c9ea4e37da7e0ffbc8305"),
    "mellor_fig5.jpg": ("abf436973a0c/develop-147-181669-g5.jpg",
                        "8509cb6f9975d36eba51b6496a456e4b4fc88efb1afb0046ea54171aa0d5c29a"),
}


def panel(pixels, y0, tick, tick_value, spans):
    scale = tick_value/(y0-tick)
    rows = [bar_top(pixels, y0, left, right) for left, right in spans]
    return [(y0-y)*scale for y in rows], 3*scale, rows


def contrast(first, second, halfwidth):
    return {
        "reference": first, "changed": second, "difference": second-first,
        "change_percent": 100*(second/first-1), "bar_readout_halfwidth": halfwidth,
        "difference_readout_range": [second-first-2*halfwidth, second-first+2*halfwidth],
    }


def run(raw, out):
    figures, sources = {}, {}
    for name, (url, digest) in FIGURES.items():
        path = raw / name
        if sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Unexpected archive image: {path}")
        with Image.open(path) as im:
            figures[name] = np.asarray(im.convert("RGB"), dtype=float)
        sources[name] = {"url": CDN+url, "sha256": digest}
    bars, error, rows = panel(figures["mellor_fig2.jpg"], 538, 409, 25.,
                              ((577, 587), (599, 609), (641, 651), (664, 674), (708, 718), (731, 741)))
    discrepancies = {genotype: contrast(bars[2*i], bars[2*i+1], error)
                     for i, genotype in enumerate(("WT", "pin2", "aux1"))}
    specs = {
        "fig4G_H2O2_observed": ("mellor_fig4.jpg", 595, 474, 70., ((210, 231), (310, 332))),
        "fig4H_H2O2_model": ("mellor_fig4.jpg", 595, 461, .7, ((444, 465), (545, 565))),
        "fig5K_GSL8_observed": ("mellor_fig5.jpg", 597, 474, 20., ((606, 630), (706, 730))),
        "fig5L_GSL8_model": ("mellor_fig5.jpg", 790, 661, .6, ((610, 633), (709, 734))),
    }
    interventions, coordinates = {}, {"fig2J_top_rows": rows}
    for key, (name, zero, tick, value, spans) in specs.items():
        pair, error, coordinates[key] = panel(figures[name], zero, tick, value, spans)
        interventions[key] = contrast(*pair, error)
    output = {
        "experiment": "E27", "study_doi": "10.1242/dev.181669", "sources": sources,
        "fig2J_mean_absolute_difference_in_normalized_DII_VENUS": discrepancies,
        "fig4_5_unnormalized_fluorescence_within_panel_only": interventions,
        "digitized_top_rows": coordinates,
        "checks": {
            "all_six_Fig2J_bars_detected_above_the_axis": len(rows) == 6 and max(rows) < 538,
            "both_bars_detected_in_each_perturbation": all(min(r["reference"], r["changed"]) > 0.
                                                          for r in interventions.values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, output, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/reflux_growth"))
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E27")
    args = parser.parse_args()
    run(args.raw, args.out)
