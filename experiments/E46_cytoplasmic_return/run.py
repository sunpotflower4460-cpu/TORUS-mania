"""Predict interior axial velocities from the outer observations in 13 cells."""

import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

from experiments import measured_return_sources as sources
from experiments.common import save_summary

SETTINGS = {
    "primary": (.30, .70, .98), "radius_q95": (.30, .70, .95),
    "radius_max": (.30, .70, 1.), "axial_25_75": (.25, .75, .98), "axial_35_65": (.35, .65, .98),
}


def flow_imbalance(radius, velocity):
    """Ring-area quadrature of measured axial flow, with axial symmetry assumed."""
    edges = np.linspace(0, 1, 9)
    means = []
    for low, high in zip(edges[:-1], edges[1:]):
        inside = (radius >= low) & ((radius < high) if high < 1 else (radius <= high))
        if not inside.any():
            return None
        means.append(np.mean(velocity[inside]))
    fluxes = np.diff(edges**2) * means
    return float(abs(fluxes.sum()) / np.abs(fluxes).sum()) if np.any(fluxes) else None


def score_cell(array, setting, keep_bands=False):
    z, signed_r, vz, _ = array.T
    z_fraction = (z - z.min()) / np.ptp(z)
    z_lo, z_hi, quantile = setting
    edges = np.linspace(z_lo, z_hi, 6)
    errors = {"zero_flux_profile": [], "uniform_from_outer": [], "zero_velocity": []}
    bands = []
    for low, high in zip(edges[:-1], edges[1:]):
        selected = (z_fraction >= low) & ((z_fraction < high) if high < edges[-1] else (z_fraction <= high))
        r = np.abs(signed_r[selected])
        v = vz[selected]
        if not len(r):
            continue
        scaled_r = r/np.quantile(r, quantile)
        outer = (scaled_r >= .80) & (scaled_r <= 1.)
        inner = scaled_r <= .35
        if min(outer.sum(), inner.sum()) < 3:
            continue
        shape = 2*scaled_r**2 - 1
        # Only outer velocities enter the wall coefficient. The inner data are untouched.
        wall = float(shape[outer] @ v[outer] / (shape[outer] @ shape[outer]))
        observed = v[inner]
        outer_mean = float(v[outer].mean())
        predictions = (wall*shape[inner], outer_mean, 0.)
        for name, predicted in zip(errors, predictions):
            errors[name].extend(np.square(observed-predicted))
        bands.append({
            "z_fraction": [float(low), float(high)], "n_outer": int(outer.sum()), "n_inner": int(inner.sum()),
            "outer_mean": outer_mean, "inner_mean": float(observed.mean()), "fitted_wall_speed": wall,
            "predicted_inner_mean": float(np.mean(predictions[0])),
            "opposite_signs": bool(outer_mean * observed.mean() < 0),
            "relative_absolute_net_flux": flow_imbalance(scaled_r, v),
        })
    if not bands:
        raise ValueError("No eligible axial bands")
    rms = {key: float(np.sqrt(np.mean(values))) for key, values in errors.items()}
    imbalance = [b["relative_absolute_net_flux"] for b in bands if b["relative_absolute_net_flux"] is not None]
    result = {
        "n_grid_points": len(array), "n_bands": len(bands), "n_inner_scored": len(errors["zero_velocity"]),
        "n_opposite_bands": sum(b["opposite_signs"] for b in bands),
        "mean_inner_and_outer_opposite": bool(np.mean([b["outer_mean"] for b in bands])
                                              * np.mean([b["inner_mean"] for b in bands]) < 0),
        "rmse_in_archived_velocity_units": rms,
        "rmse_over_zero": rms["zero_flux_profile"] / rms["zero_velocity"],
        "improves_on_both_controls": rms["zero_flux_profile"] < min(rms["uniform_from_outer"], rms["zero_velocity"]),
        "n_complete_flux_bands": len(imbalance),
        "median_relative_absolute_net_flux": float(np.median(imbalance)) if imbalance else None,
    }
    if keep_bands:
        result["bands"] = bands
    return result


def aggregate(cells):
    def summarize(group):
        residuals = [v["median_relative_absolute_net_flux"] for v in group
                     if v["median_relative_absolute_net_flux"] is not None]
        return {
            "n_cells": len(group),
            "cells_with_opposing_regional_means": sum(c["mean_inner_and_outer_opposite"] for c in group),
            "cells_better_than_both_controls": sum(c["improves_on_both_controls"] for c in group),
            "opposing_bands": sum(c["n_opposite_bands"] for c in group), "scored_bands": sum(c["n_bands"] for c in group),
            "median_rmse_over_zero": float(np.median([c["rmse_over_zero"] for c in group])),
            "median_of_cell_median_relative_net_flux": float(np.median(residuals)) if residuals else None,
        }
    return {prefix: summarize([v for k, v in cells.items() if k.startswith(prefix)]) for prefix in ("Ce", "Mm")}


def run(raw, out):
    with BytesIO(sources.read(raw, "piv_fields.xlsx")) as stream:
        book = load_workbook(stream, read_only=True, data_only=True)
        try:
            cells = {}
            for sheet in book:
                rows = iter(sheet.values)
                if next(rows) != ("D(Sc(x))", "Sc(y)", "vz", "vr"):
                    raise ValueError(f"Unknown fields in {sheet.title}")
                cells[sheet.title] = np.asarray(list(rows), dtype=float)
        finally:
            book.close()
    all_scores = {}
    for name, setting in SETTINGS.items():
        scores = {k: score_cell(a, setting, keep_bands=(name == "primary")) for k, a in cells.items()}
        all_scores[name] = {"settings_z_min_max_radius_q": setting, "cells": scores, "groups": aggregate(scores)}
    # Integrate in cylindrical volume. For unit viscosity, length, radius and wall speed,
    # the viscous power and the wall work must agree despite a vanishing net volume flux.
    x, weights = np.polynomial.legendre.leggauss(8)
    radius, weights = (x+1)/2, weights/2
    unit_net = float(np.sum(weights*2*np.pi*radius*(2*radius**2-1)))
    dissipation = float(np.sum(weights*2*np.pi*radius*(4*radius)**2))
    examples = {}
    for label, viscosity, speed in (("Ce", 1., 100e-9), ("Mm", .1, 1e-9)):
        examples[label] = {"viscosity_Pa_s": viscosity, "assumed_wall_speed_m_per_s": speed,
                           "watt_per_axial_micrometre": 8*np.pi*viscosity*speed**2 * 1e-6}
    report = {
        "experiment": "E46", "study_doi": "10.1371/journal.pone.0159917",
        "dataset_doi": "10.1371/journal.pone.0159917.s004", "scores": all_scores,
        "unit_cylinder": {"numerical_volume_flux": unit_net, "integrated_dissipation": dissipation, "wall_work": 8*np.pi},
        "conditional_power_examples": examples,
        "interpretation": "Single meridional PIV sections in the workbook. Coordinates were remapped by the authors. "
                          "Velocity units are not specified by the column labels. Power examples use the paper's "
                          "typical physical scales as hypothetical wall speeds, not measured work or a calibration of these arrays.",
        "checks": {
            "six_worms_and_seven_oocytes": set(cells) == {f"Ce{i}" for i in range(1,7)} | {f"Mm{i}" for i in range(1,8)},
            "finite_archived_vectors": all(np.isfinite(a).all().item() for a in cells.values()),
            "both_radial_regions_in_every_primary_cell": all(c["n_inner_scored"] >= 3 for c in all_scores["primary"]["cells"].values()),
            "zero_flux_in_ideal_reference": abs(unit_net) < 1e-13,
            "boundary_work_equals_integrated_dissipation_in_reference": abs(dissipation-8*np.pi) < 1e-12,
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
