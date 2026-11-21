"""Read prebranch-site density under GNOM/AGD3 and BFA perturbations."""

import argparse
from hashlib import sha256
from pathlib import Path

import numpy as np
from PIL import Image

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
FIGURE_URL = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/84bd/7758939/40e6006dffcc/nihms-1649559-f0003.jpg"
FIGURE_SHA256 = "5648f6afab9948182d38dc82be3017e0982c425e8cb8409a6fd4b99c178f297c"
Y_ZERO, Y_FIFTEEN = 250.5, 60.5
SCALE = 15./(Y_ZERO-Y_FIFTEEN)
GROUPS = {
    "WT_mock": 482, "gnom184_mock": 512, "agd3_26_mock": 543, "agd3_SALK_mock": 573,
    "gnom184_agd3_26_mock": 603, "WT_BFA": 634, "agd3_26_BFA": 664, "agd3_SALK_BFA": 694,
}


def read_box(pixels, x):
    red, green, _ = pixels[125:254, x-7:x+8].transpose(2, 0, 1)
    line_color = (red-green > 19) if x < 620 else (green-red > 22)
    full_rows = np.flatnonzero(line_color.mean(axis=1) > .70)+125
    lines = [float(block.mean()) for block in np.split(full_rows, np.flatnonzero(np.diff(full_rows)>1)+1) if len(block)]
    if len(lines) == 1:
        lines *= 3  # A box collapsed to a single visible line.
    if len(lines) != 3:
        raise ValueError(f"Expected three box lines at x={x}, found {lines}")
    q3, median, q1 = [max(0., (Y_ZERO-y)*SCALE) for y in lines]
    return {"median": median, "quartiles_q1_q3": [q1, q3], "top_median_bottom_rows": lines}


def run(figure, out):
    if sha256(figure.read_bytes()).hexdigest() != FIGURE_SHA256:
        raise ValueError(f"Unexpected source figure: {figure}")
    with Image.open(figure) as im:
        pixels = np.asarray(im.convert("RGB"), dtype=np.int16)
    rows = {group: read_box(pixels, x) for group, x in GROUPS.items()}
    m = {group: box["median"] for group, box in rows.items()}
    drug = {group: m[f"{group}_BFA"]-m[f"{group}_mock"] for group in ("WT", "agd3_26", "agd3_SALK")}
    contrasts = {
        "gnom184_minus_WT_mock": m["gnom184_mock"]-m["WT_mock"],
        "suppressor_double_minus_gnom184_mock": m["gnom184_agd3_26_mock"]-m["gnom184_mock"],
        "suppressor_double_minus_WT_mock": m["gnom184_agd3_26_mock"]-m["WT_mock"],
        "BFA_minus_mock_by_genotype": drug,
        "genetic_recovery_fraction_of_WT_gnom_deficit": (
            (m["gnom184_agd3_26_mock"]-m["gnom184_mock"])/(m["WT_mock"]-m["gnom184_mock"])
        ),
    }
    report = {
        "experiment": "E30", "study_doi": "10.1126/science.abb7250", "figure_panel": "3C",
        "figure_url": FIGURE_URL, "figure_sha256": FIGURE_SHA256,
        "units": "prebranch sites per centimetre of primary root",
        "marker": "pCLE44::LUC", "axis_y_zero_fifteen": [Y_ZERO, Y_FIFTEEN],
        "box_values": rows, "contrasts_of_medians": contrasts,
        "reading_halfwidth_per_box_line": 3*SCALE, "reading_halfwidth_for_median_difference": 6*SCALE,
        "checks": {
            "eight_boxes_read": len(rows)==8,
            "median_between_read_quartiles": all(x["quartiles_q1_q3"][0] <= x["median"] <= x["quartiles_q1_q3"][1]
                                                 for x in rows.values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", type=Path, default=ROOT/"data/raw/root_clock/wachsman_f3.jpg")
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E30")
    args = parser.parse_args()
    run(args.figure, args.out)
