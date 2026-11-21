"""Read two spatial profiles of radiolabel and the independent NPA comparison."""

import json
import re

import numpy as np

from experiments import turning_path_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb


def series(image, x, rows, zero, tick, maximum):
    scale = maximum / (zero - tick)
    for col, row in zip(x, rows, strict=True):
        if image[row - 5 : row + 6, col - 5 : col + 6].min() > 145:
            raise ValueError(f"No marker at {col}, {row}")
    return {
        "marker_rows": rows,
        "pmol_equivalent": [(zero - row) * scale for row in rows],
        "reading_halfwidth_pmol": 2 * scale,
    }


def run(raw, out):
    image = rgb(sources.read(raw, "rashotte_fig3.jpg"))
    a_x = [117, 172, 226, 281, 335, 389]
    b_x = [109, 141, 173, 206, 237, 269, 301, 333, 365, 397]
    scan = {
        "shootward_fig3a": {
            "exposure_h": 5,
            "source": "root tip",
            "segment_edges_mm": [1, 3, 5, 7, 9, 14, 19],
            "pixel_zero_tick_value": [351, 38, 4],
            "x": a_x,
            "IAA": series(image, a_x, [200, 290, 338, 347, 347, 347], 351, 38, 4),
            "IBA": series(image, a_x, [91, 247, 322, 344, 350, 347], 351, 38, 4),
        },
        "rootward_fig3b": {
            "label_min": 10,
            "chase_min": 50,
            "donor_from_tip_mm": 20,
            "segment_edges_from_donor_mm": list(range(0, 21, 2)),
            "pixel_zero_tick_value": [754, 433, 12],
            "x": b_x,
            "IAA": series(image, b_x, [679, 683, 709, 710, 717, 735, 734, 729, 738, 734], 754, 433, 12),
            "IBA": series(image, b_x, [518, 592, 594, 659, 665, 725, 721, 710, 732, 715], 754, 433, 12),
        },
    }
    for compound in ("IAA", "IBA"):
        pulse = scan["rootward_fig3b"][compound]
        values = pulse["pmol_equivalent"]
        background = float(np.mean(values[6:]))  # The authors designate >=12 mm as background.
        pulse["mean_12_to_20_mm_pmol"] = background
        pulse["last_two_bins_before_10mm_minus_background_pmol"] = [v - background for v in values[3:5]]
    rows = json.loads(sources.read(raw, "rashotte_table1.json"))
    groups = {}
    for heading, start in (("rootward", 2), ("shootward", 5)):
        if not rows[start][0].startswith("Root"):
            raise ValueError("Incorrect Table I row group")
        groups[heading] = {}
        for compound, control, npa in rows[start + 1 : start + 3]:
            pair = [float(re.match(r"[0-9.]+", x)[0]) for x in (control, npa)]
            groups[heading][compound] = {
                "control_and_NPA_pmol": pair,
                "NPA_over_control": pair[1] / pair[0],
            }
    report = {
        "experiment": "E49",
        "doi": "10.1104/pp.103.022582",
        **scan,
        "table_1": groups,
        "reported_front_mm_after_one_hour": [8, 10],
        "individual_arrival_time_available": False,
        "chemical_scope": "The whole-seedling IBA TLC and the isotope measurements of individual segments used different samples.",
        "checks": {
            "figure_dimensions": image.shape[:2] == (845, 426),
            "both_profiles_complete": len(a_x) == 6 and len(b_x) == 10,
            "distance_sum_matches_pulse_donor": scan["rootward_fig3b"]["segment_edges_from_donor_mm"][-1]
            == 20,
            "matched_table_treatments": all(set(g) == {"IAA", "IBA"} for g in groups.values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
