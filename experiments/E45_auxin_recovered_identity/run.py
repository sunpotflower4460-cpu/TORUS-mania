"""Recover measured auxin chemical fractions after a localized input."""

import argparse
from pathlib import Path

import numpy as np

from experiments import measured_return_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb


def bar_values(image, columns, zero, tick_row, tick_value, shade):
    """Locate the filled edge connected to the axis, including short inhibitor bars."""
    tops = []
    for left, right in columns:
        column = np.median(image[:zero, left:right], axis=(1, 2))
        white = np.where(column >= shade)[0]
        if not white.size:
            raise ValueError(f"Unreadable bar in columns {left}:{right}")
        tops.append(int(white[-1] + 1))
    scale = tick_value / (zero - tick_row)
    return {
        "columns": columns, "zero_tick_value": [zero, tick_row, tick_value], "top_rows": tops,
        "values": [(zero - row)*scale for row in tops], "reading_halfwidth": 2*scale,
    }


def run(raw, out):
    root = rgb(sources.read(raw, "ruzicka5.jpg"))
    hypocotyl = rgb(sources.read(raw, "liu3.jpg"))
    # In Fig. 5C the lower (dark) part of each stack is IAA. Avoid the central error bars.
    chemical = bar_values(root, [(334, 346), (391, 403)], 482, 332, 100, 160)
    near, far = chemical["values"]
    # Fig. 5A includes open distant-section bars. Manually read the horizontal bar edge.
    root_axis = (222, 16, 80)
    iaa_rows = [(63, 142), (74, 143), (27, 131)]
    iaa_centers = [(75, 87), (113, 125), (151, 164)]
    for centers, rows in zip(iaa_centers, iaa_rows):
        for x, y in zip(centers, rows):
            if np.min(root[y-2:y+3, x-4:x+5]) > 180:
                raise ValueError("Missing marker on the direct IAA transport panel")
    scale = root_axis[2] / (root_axis[0]-root_axis[1])
    # Panels 3B/C use the same three treatments. Read the lower half plus receiver
    # and the percentage of recovered free isotope in those tissues, respectively.
    columns = [(50, 61), (78, 89), (105, 116)]
    pg = bar_values(hypocotyl, columns, 217, 140, 20, 225)
    percent = bar_values(hypocotyl, columns, 330, 277, 30, 225)
    report = {
        "experiment": "E45", "root_study_doi": "10.1073/pnas.1005878107",
        "hypocotyl_study_doi": "10.1104/pp.111.191288", "root_sections_mm": [[.4, 2.4], [2.4, 4.4]],
        "IBA_input_fig5C": {
            "minutes": 120, "input_fmol": 100, "IAA_percent_of_HPLC_IAA_plus_IBA": chemical,
            "distal_minus_near_percentage_points": far-near,
            "difference_reading_halfwidth_percentage_points": 2*chemical["reading_halfwidth"],
        },
        "IAA_input_fig5A": {
            "signal": "total 3H in each receiving section; chemical identity not separated in this panel",
            "groups": ["Col-0", "pdr9-2", "35S-ABCG37"], "pixel_zero_tick_value": root_axis,
            "marker_rows_near_far": iaa_rows, "reading_halfwidth_dpm": 2*scale,
            "dpm_per_root_segment_near_far": [[(root_axis[0]-y)*scale for y in pair] for pair in iaa_rows],
        },
        "direct_stable_IAA_hypocotyl_fig3": {
            "organ": "6-mm excised hypocotyl, 5 h", "input": "13C6-IAA; free intact labelled IAA by GC–MS/MS",
            "conditions": ["WT_basipetal", "WT_NPA", "WT_reversed_orientation"],
            "lower_plus_receiver_pg_per_plant": pg, "percent_of_recovered_free_13C6_IAA": percent,
            "NPA_over_WT_by_amount": pg["values"][1]/pg["values"][0],
        },
        "checks": {
            "source_image_dimensions": root.shape[:2] == (509, 457) and hypocotyl.shape[:2] == (352, 462),
            "two_HPLC_fractions_in_range": 0 <= near <= 100 and 0 <= far <= 100,
            "all_direct_IAA_groups_read": len(iaa_rows) == 3 and len(pg["values"]) == 3,
            "hypocotyl_reading_agrees_with_reported_29_percent": abs(percent["values"][0]-29) < 2,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, sources.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=sources.RAW)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw, args.out)
