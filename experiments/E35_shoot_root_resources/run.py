"""Read grafting and sucrose responses from Duan et al.'s public figures."""

import argparse
from pathlib import Path

from experiments import return_energy_data as data
from experiments.common import save_summary

BASE = "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/0601/8133581/"
SOURCES = {
    "duan_f3.jpg": (BASE+"326c8e14f147/kiaa032f3.jpg",
                    "d21b6979c8ee9b8ab04cd1b95e8fc34953e24391b7738eafa9a9a5d8bbd20bd5"),
    "duan_f6.jpg": (BASE+"4faa493f59d5/kiaa032f6.jpg",
                    "92025d81d6873904bc538d5a7029ac44902b87f835797b4e0b65cb304b49e3ce"),
}
# Median strokes of the boxes from left to right. Coordinates of two axis ticks
# are also supplied, since the range and offset are different in each panel.
PANELS = {
    "3B": ((184, 20), (76, 60), (77.5, 200., 109., 191.)),
    "6B": ((245.5, 0), (44.5, 5), (143.5, 77., 237.5, 147.5)),
    "6C": ((596.5, 0), (428.5, 3), (420., 421., 427., 544.5, 510.5, 500.5)),
    "6D": ((596., 0), (429., 3), (480., 471.5, 462., 549., 531., 515.5)),
    "6E": ((917.5, 0), (722.5, 5), (774., 779., 786., 917.5, 917.5, 917.5)),
    "6F": ((920.5, 0), (721.5, 5), (911.5, 920.5, 920.5, 920.5, 920.5, 920.5)),
}


def convert(panel):
    (y0, val0), (y1, val1), rows = PANELS[panel]
    slope = (val1 - val0) / (y1 - y0)
    return [max(0., val0 + slope * (y - y0)) for y in rows], 2. * abs(slope)


def supplementation(panel, doses):
    estimates, halfwidth = convert(panel)
    n = len(doses)
    return {
        "sucrose_percent": doses, "WT": estimates[:n], "cyp38_5": estimates[n:],
        "WT_minus_cyp38_5": [a-b for a, b in zip(estimates[:n], estimates[n:])],
        "single_median_reading_half_width": halfwidth,
    }


def run(raw, out):
    fig3, fig6 = [data.rgb(data.verified(raw/name, digest)) for name, (_, digest) in SOURCES.items()]
    branches, halfwidth = convert("3B")
    ww, mm, wm, mw = branches
    germination = supplementation("6B", [0, 1])
    readings = {}
    for panel, endpoint in (
        ("6C", "regular_light_primary_root_cm"), ("6D", "low_light_primary_root_cm"),
        ("6E", "regular_light_lateral_root_density_per_cm"), ("6F", "low_light_lateral_root_density_per_cm"),
    ):
        group = supplementation(panel, [1, 2, 3])
        gap = group["WT_minus_cyp38_5"]
        group["WT_minus_mutant_gap_at_3_percent_minus_gap_at_1_percent"] = gap[-1] - gap[0]
        group["mutant_change_at_3_percent_minus_1_percent"] = group["cyp38_5"][-1] - group["cyp38_5"][0]
        readings[endpoint] = group
    report = {
        "experiment": "E35", "study_doi": "10.1093/plphys/kiaa032",
        "sources": {name: {"url": url, "sha256": digest} for name, (url, digest) in SOURCES.items()},
        "box_median_axis_and_rows": PANELS,
        "grafted_median_branch_number": {
            "shoot_WT_root_WT": ww, "shoot_mutant_root_mutant": mm,
            "shoot_WT_root_mutant": wm, "shoot_mutant_root_WT": mw,
            "WT_shoot_increment_on_WT_root": ww - mw,
            "WT_shoot_increment_on_mutant_root": wm - mm,
            "WT_root_increment_with_WT_shoot": ww - wm,
            "WT_root_increment_with_mutant_shoot": mw - mm,
            "readout_half_width_per_median": halfwidth,
        },
        "fig6B_primary_root_cm": germination,
        "fig6C_to_6F": readings,
        "checks": {
            "versioned_figure_sizes": fig3.shape[:2] == (835, 699) and fig6.shape[:2] == (1316, 632),
            "separate_supplementation_panels": all(len(x["WT"]) == len(x["cyp38_5"]) == 3 for x in readings.values()),
            "graft_and_sucrose_axes_positive": all(a[0] > b[0] and a[1] < b[1] for a, b, _ in PANELS.values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=data.RAW)
    parser.add_argument("--out", type=Path, default=data.RESULTS/"E35")
    args = parser.parse_args()
    run(args.raw, args.out)
