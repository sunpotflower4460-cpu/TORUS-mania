"""Compare matched wild types, two transport directions, and lateral-root growth."""

import json

import numpy as np

from experiments import turning_path_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb


def bars(image, centers, starts, zero, upper, unit, offset=7):
    tops = []
    for center, start in zip(centers, starts, strict=True):
        # Read a short strip away from the central error bar and its cap.
        columns = image[start:zero, center - offset - 2 : center - offset + 2]
        ink = np.flatnonzero(np.median(columns, axis=(1, 2)) < 180)
        if not ink.size:
            raise ValueError(f"No bar at x={center}")
        tops.append(start + int(ink[0]))
    scale = unit / (zero - upper)
    return {
        "x": centers,
        "starts": starts,
        "x_offset": offset,
        "pixel_zero_tick_value": [zero, upper, unit],
        "top_rows": tops,
        "values": [(zero - t) * scale for t in tops],
        "reading_halfwidth": 2 * scale,
    }


def run(raw, out):
    lewis = rgb(sources.read(raw, "lewis_fig2.jpg"))
    w8 = rgb(sources.read(raw, "wu_fig8.jpg"))
    w9 = rgb(sources.read(raw, "wu_fig9.jpg"))
    genotypes = ["Col", "Ws", "mdr1-1", "mdr1-2", "mdr4-1", "mdr4-2", "benzoic_acid"]
    xs = [101, 158, 215, 272, 328, 385, 441]
    direction = {
        "rootward": bars(lewis, xs, [30] * 7, 347, 79, 1),
        "shootward": bars(lewis, xs, [1303] * 7, 1622, 1353, 1),
    }
    ratios = {}
    for name, measured in direction.items():
        values = measured["values"]
        ratios[name] = {genotypes[i]: values[i] / values[1 if i < 4 else 0] for i in range(2, 6)}
    w8data = bars(w8, [156, 262, 368, 474], [12] * 4, 359, 86, 100, 17)
    # Wu Fig. 9 contains hollow NPA bars; their top horizontal border is visible.
    w9data = bars(w9, [109, 150, 190, 260, 300, 340, 410, 450, 490], [10] * 6 + [96] * 3, 387, 47, 8, 12)
    rates = np.asarray(w9data["values"]).reshape(3, 3)
    rows = json.loads(sources.read(raw, "wu_table1.json"))
    stages = {}
    for row in rows[2:]:
        stages[row[0]] = [[float(v) for v in value.split(" ± ")] for value in row[1:]]
    stage_ratios = {
        name: values[-1][0] / stages["Col-0" if name.startswith("mdr4") else "Ws"][-1][0]
        for name, values in stages.items()
        if name.startswith("mdr")
    }
    summary = {
        "experiment": "E50",
        "dois": ["10.1105/tpc.107.051599", "10.1105/tpc.106.048777"],
        "primary_root_fig2": {
            "bar_order": genotypes,
            "measurements": direction,
            "ratios_to_matched_WT": ratios,
            "pooled_roots_per_trial": 8,
            "independent_trials_rootward_shootward": [5, 7],
        },
        "lateral_root_fig8": {
            "order": ["Ws", "mdr1-1", "mdr1-2", "GFP-MDR1 in mdr1-1"],
            **w8data,
            "independent_trials": 3,
            "roots_per_trial": 10,
        },
        "lateral_growth_fig9": {
            "genotypes": ["Ws", "mdr1-1", "mdr1-2"],
            "conditions": ["control", "IAA", "NPA"],
            **w9data,
            "mm_per_day": rates.tolist(),
            "IAA_gain_mm_per_day": (rates[:, 1] - rates[:, 0]).tolist(),
            "mutant_IAA_over_WT_control": (rates[1:, 1] / rates[0, 0]).tolist(),
            "independent_trials": 3,
            "plants_per_trial": 5,
        },
        "wu_table1": {
            "columns": rows[1][1:],
            "means_and_se": stages,
            "total_relative_to_matched_WT": stage_ratios,
        },
        "checks": {
            "figure_dimensions": lewis.shape[:2] == (1681, 494)
            and w8.shape[:2] == (412, 531)
            and w9.shape[:2] == (415, 531),
            "four_alleles_in_both_directions": all(len(v) == 4 for v in ratios.values()),
            "matched_controls_consistent_with_normalized_scales": abs(
                direction["rootward"]["values"][1] - 1
            )
            < 0.02
            and abs(w8data["values"][0] - 100) < 1,
            "complete_stage_table": len(stages) == 7 and all(len(v) == 4 for v in stages.values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
