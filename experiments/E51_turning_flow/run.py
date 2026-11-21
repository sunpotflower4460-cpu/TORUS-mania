"""Test both radial turns and central axial counterflow in each measured half-plane."""

from io import BytesIO

import numpy as np
from openpyxl import load_workbook

from experiments import turning_path_sources as sources
from experiments.common import save_summary

CASES = {
    "primary": (0.10, 0.30, "mean"),
    "near_poles": (0.05, 0.25, "mean"),
    "near_middle": (0.15, 0.35, "mean"),
    "median": (0.10, 0.30, "median"),
}


def geometry(array):
    z, r, vz, vr = array.T
    z = (z - z.min()) / np.ptp(z)
    # A disk narrows toward each pole. Measure the envelope in a sliding axial window.
    levels, inverse = np.unique(z, return_inverse=True)
    radii = np.array([np.max(np.abs(r[np.abs(z - level) <= 0.025])) for level in levels])
    radial_fraction = np.abs(r) / radii[inverse]
    speed2 = vz * vz + vr * vr
    weight = speed2 / np.mean(speed2)
    return z, r, radial_fraction, vz, np.sign(r) * vr, weight, float(np.sqrt(np.mean(speed2)))


def directions(values):
    core, shell, near, far = values
    axial = bool(core * shell < 0)
    radial = bool(near * far < 0)
    both = axial and radial
    return {
        "axial_opposition": axial,
        "radial_opposition": radial,
        "both_oppositions": both,
        "outward_at_source_inward_at_drain": bool(near > 0 and far < 0),
        "consistent_if_vz_toward_increasing_distance": both and bool(core * far > 0),
        "consistent_if_vz_toward_decreasing_distance": both and bool(core * far < 0),
    }


def score_half(geo, side, bounds):
    z, r, radius, vz, outward, weight, speed_rms = geo
    low, high, statistic = bounds
    middle = (z >= 0.35) & (z <= 0.65)
    middle_r = (radius >= 0.35) & (radius <= 0.80)
    masks = [
        middle & (radius <= 0.35),
        middle & (radius >= 0.75) & (radius <= 0.95),
        (z >= low) & (z <= high) & middle_r,
        (z >= 1 - high) & (z <= 1 - low) & middle_r,
    ]
    masks = [selection & (side * r > 0) for selection in masks]
    counts = [int(m.sum()) for m in masks]
    if min(counts) < 3:
        return {"n_points": counts, "eligible": False}
    reduce = np.mean if statistic == "mean" else np.median
    components = [vz, vz, outward, outward]
    velocity = [float(reduce(v[m])) for m, v in zip(masks, components)]
    # Dimensionless advective transport of the kinetic energy of the two tabulated components.
    advected = [float(reduce((weight * v / speed_rms)[m])) for m, v in zip(masks, components)]
    return {
        "eligible": True,
        "n_points": counts,
        "velocities": velocity,
        "velocity_signs": directions(velocity),
        "energy_advection_normalized": advected,
        "energy_signs": directions(advected),
    }


def groups(cells):
    out = {}
    for species in ("Ce", "Mm"):
        pairs = [
            list(v.values())
            for name, v in cells.items()
            if name.startswith(species) and all(h["eligible"] for h in v.values())
        ]
        group = {"n_cells_both_halves_eligible": len(pairs)}
        for observable in ("velocity_signs", "energy_signs"):
            group[observable] = {}
            for metric in directions([0.0, 0.0, 0.0, 0.0]):
                counts = [sum(h[observable][metric] for h in pair) for pair in pairs]
                group[observable][metric] = {"halves": sum(counts), "cells_both_halves": counts.count(2)}
        out[species] = group
    return out


def reference():
    z, r = np.meshgrid(np.linspace(0, 1, 61), np.linspace(-1, 1, 81))
    z, r = z.ravel(), r.ravel()
    vz = -z * (1 - z) * (2 - 4 * r * r)
    vr = (1 - 2 * z) * r * (1 - r * r)
    out = {}
    for name, radial in (("steady_recirculation", vr), ("axial_only", np.zeros_like(vr))):
        geo = geometry(np.column_stack([z, r, vz, radial]))
        out[name] = score_half(geo, 1, CASES["primary"])
    return out


def run(raw, out):
    with BytesIO(sources.read(raw, "piv_fields.xlsx")) as buf:
        workbook = load_workbook(buf, read_only=True, data_only=True)
        all_cases = {name: {} for name in CASES}
        try:
            for sheet in workbook:
                rows = iter(sheet.values)
                if next(rows) != ("D(Sc(x))", "Sc(y)", "vz", "vr"):
                    raise ValueError(f"Unexpected coordinate columns in {sheet.title}")
                array = np.asarray(list(rows), dtype=float)
                if not np.isfinite(array).all():
                    raise ValueError(f"Non-finite vectors in {sheet.title}")
                geo = geometry(array)
                for case, bounds in CASES.items():
                    all_cases[case][sheet.title] = {
                        name: score_half(geo, side, bounds) for name, side in (("upper", 1), ("lower", -1))
                    }
        finally:
            workbook.close()
    calibration = reference()
    scores = {
        case: {"end_window_and_statistic": CASES[case], "groups": groups(cells), "cells": cells}
        for case, cells in all_cases.items()
    }
    primary = scores["primary"]["groups"]
    summary = {
        "experiment": "E51",
        "dataset": "10.1371/journal.pone.0159917.s004",
        "region_order": ["axial_core", "axial_shell", "outward_near_source", "outward_near_drain"],
        "coordinate_scope": "D is distance from the source. Both axial velocity conventions are reported.",
        "energy_normalization": "(vz^2+vr^2) * component / rms_speed^3, common positive density factor cancelled",
        "calibration": calibration,
        "scores": scores,
        "checks": {
            "cell_counts": len(all_cases["primary"]) == 13,
            "both_halves_have_all_regions": primary["Ce"]["n_cells_both_halves_eligible"] == 6
            and primary["Mm"]["n_cells_both_halves_eligible"] == 7,
            "known_recirculation_turns": calibration["steady_recirculation"]["velocity_signs"][
                "consistent_if_vz_toward_increasing_distance"
            ],
            "open_axial_control_has_no_return_turns": not calibration["axial_only"]["velocity_signs"][
                "both_oppositions"
            ],
            "energy_control_has_no_radial_flux": calibration["axial_only"]["energy_advection_normalized"][
                2:
            ]
            == [0.0, 0.0],
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
