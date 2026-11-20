"""Score the preregistered change in uptake location across grids and time steps."""

import argparse
import json
from pathlib import Path

from experiments.common import save_summary

VARIANTS = ("grid48", "grid96", "time_refined96")


def final_uptake_center(summary, name):
    return summary["trials"][name]["snapshots"][-1]["uptake_geometry"]["z_centroid"]


def run(out):
    runs = {name: json.loads((out / name / "summary.json").read_text(encoding="utf-8")) for name in VARIANTS}
    coarse, fine, small_step = (runs[name] for name in VARIANTS)
    main_outcomes = {name: result["uptake_centroid_delta_reversing"] for name, result in runs.items()}
    directions = ("circulation", "reversed")
    grid_shift = max(abs(final_uptake_center(fine, name) - final_uptake_center(coarse, name))
                     for name in directions)
    time_shift = max(abs(final_uptake_center(fine, name) - final_uptake_center(small_step, name))
                     for name in directions)
    min_effect = min(abs(value) for value in main_outcomes.values())
    rings = {}
    for name in VARIANTS:
        result = runs[name]
        rings[name] = {
            "kinetic": {f: test["candidate"] for f, test in result["initial_kinetic_superlevels"].items()},
            "material": {case: [test["candidate"] for test in row["final_material_superlevels"].values()]
                         for case, row in result["trials"].items()},
        }
    timing = {}
    early = fine["trials"]["circulation"]["snapshots"]
    late = fine["trials"]["late_start"]["snapshots"]
    for frame in (0, 3):
        first, second = early[frame], late[frame]
        timing[str(first["time"])] = {
            "preflow_and_delayed_accumulated_uptake": [first["uptake"], second["uptake"]],
            "preflow_and_delayed_uptake_z": [first["uptake_geometry"]["z_centroid"],
                                           second["uptake_geometry"]["z_centroid"]],
        }
    save_summary(out, {
        "units": "Lengths relative to the cylinder radius",
        "signed_differences_reversing": main_outcomes, "maximum_single_center_grid_shift": grid_shift,
        "maximum_single_center_time_shift": time_shift,
        "preregistered_effect_threshold": .02,
        "meets_preregistered_effect_threshold": min_effect >= max(.02, grid_shift, time_shift),
        "timing": timing, "rings": rings,
        "checks": {"all_numeric_calibrations_passed": all(all(row["checks"].values()) for row in runs.values())},
    }, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    opts = parser.parse_args()
    run(opts.out)
