"""Reanalyse the measured figure arrays from Matsuzawa et al. (PNAS 2026)."""

import argparse
from hashlib import sha256
from pathlib import Path

import h5py
import numpy as np

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = "10.5281/zenodo.18380405"
SOURCES = {
    "Fig1B_Energy_spreading.h5": "b4fc9c06346060edd1c076984311be04caffe23130acb36e458270f0dfcf65c9",
    "Fig4B_energy_distribution.h5": "0960a761ca108f85bb48516baefecb103eeb80693888d6325dcac2f00e122791",
    "Fig5A_kymograph.h5": "3748b25a1e33e05024354b84b62443289c0717d993f0ceae48414ab3a8291e13",
}
WIDTH_COLUMNS = ("time_s", "second_moment_mm2", "median_energy_radius_mm", "fixed_fit_mm2", "linear_fit_mm2")
ENERGY_COLUMNS = ("time_s", "mean_fraction", "fluctuating_fraction", "signed_cross_fraction")


def snapshots(file):
    keys = ("e_t_560_20", "e_t_600_20", "e_t_700_20")
    x, y = file["x"][()], file["y"][()]
    fields = np.stack([file[k][()] for k in keys])
    valid = np.isfinite(fields).all(axis=0)
    values = fields[:, valid]
    if not (np.isfinite(x).all() and np.isfinite(y).all() and (values >= 0).all()
            and np.all(values.sum(axis=1) > 0)):
        raise ValueError("Unexpected coordinate or energy data in Fig. 1B")
    first = values[0] / values[0].sum()
    centroid = np.array([first @ x[valid], first @ y[valid]])
    distance2 = (x[valid] - centroid[0])**2 + (y[valid] - centroid[1])**2
    order = np.argsort(distance2)
    row_sum = values.sum(axis=1)
    moments = (values @ distance2) / row_sum
    indices = [np.searchsorted(np.cumsum(row[order]), total / 2) for row, total in zip(values, row_sum, strict=True)]
    figures = [{"array": k, "second_moment_mm2": float(s), "median_energy_radius_mm": float(m),
                "relative_integrated_plane_signal": float(e / row_sum[0])}
               for k, s, m, e in zip(keys, moments, np.sqrt(distance2[order[indices]]), row_sum, strict=True)]
    return {"shape_y_x": list(x.shape), "valid_common_cells": int(valid.sum()), "centroid_xy_mm": centroid.tolist(),
            "spacing_xy_mm": [float(x[0, 1] - x[0, 0]), float(y[1, 0] - y[0, 0])],
            "timing": "Archive key order only. HDF5 has no time or experimental-group attribute.",
            "snapshots": figures}


def plane_radial_moments(r, profile, cutoff):
    edges = np.r_[0, (r[1:] + r[:-1]) / 2, r[-1] + (r[-1] - r[-2]) / 2]
    edges = np.minimum(edges, cutoff)
    inner, outer = edges[:-1], edges[1:]
    weights = profile * (outer**2 - inner**2)[:, None] / 2
    cumulative = np.cumsum(weights, axis=0)
    mass = cumulative[-1]
    moments = ((outer**4 - inner**4) / 4) @ profile / mass
    index = np.argmax(cumulative >= mass / 2, axis=0)
    time = np.arange(len(index))
    before = cumulative[index, time] - weights[index, time]
    median = np.sqrt(inner[index]**2 + 2 * (mass / 2 - before) / profile[index, time])
    return moments, median, float(edges[-1])


def temporal_fit(t, moment):
    split = (t[0] + t[-1]) / 2
    train = t <= split
    # Both fits use only the first half of the same physical-time interval.
    slope, intercept = np.polyfit(t[train] - t[0], moment[train], 1)
    constant = np.full_like(t, np.mean(moment[train]))
    linear = intercept + slope * (t - t[0])
    rmse = [float(np.sqrt(np.mean((moment[~train] - fit[~train])**2))) for fit in (constant, linear)]
    return {"train_points": int(train.sum()), "holdout_points": int((~train).sum()),
            "split_s": float(split), "linear_slope_mm2_s": float(slope),
            "rmse_holdout_mm2": dict(zip(("fixed", "linear"), rmse, strict=True))}, constant, linear


def spreading(file):
    r_grid, t_grid, q = [file[key][()] for key in ("r", "t", "qr_scaled")]
    r, t = r_grid[:, 0], t_grid[0]
    if not (np.all(r_grid == r[:, None]) and np.all(t_grid == t)
            and np.all(np.diff(r) > 0) and np.all(np.diff(t) > 0)
            and np.isfinite(q).all() and (q > 0).all()):
        raise ValueError("Expected regular bins, increasing times and positive finite data in Fig. 5A")
    selected = (t >= .6 - 1.e-9) & (t <= 5.5 + 1.e-9)
    times = t[selected]
    result, arrays = {}, {}
    for tag, cutoff in (("full", np.inf), ("cut150", 150.)):
        metric, half_radius, edge = plane_radial_moments(r, q[:, selected], cutoff)
        calibration_moment, calibration_median, _ = plane_radial_moments(r, np.ones((len(r), 1)), cutoff)
        fit, constant, linear = temporal_fit(times, metric)
        result[tag] = {"outer_edge_mm": edge, "time_range_s": times[[0, -1]].tolist(),
                       "second_moment_mm2": metric[[0, -1]].tolist(),
                       "median_energy_radius_mm": half_radius[[0, -1]].tolist(), **fit}
        result[tag]["uniform_disk_calibration_error_mm"] = abs(float(calibration_median[0]) - edge / np.sqrt(2))
        result[tag]["uniform_disk_calibration_error_mm2"] = abs(float(calibration_moment[0]) - edge**2 / 2)
        arrays[f"spreading_{tag}"] = np.column_stack((times, metric, half_radius, constant, linear))
    return result, arrays


def average_in_log_time(t, fractions, low, high):
    interior = (t > low) & (t < high)
    nodes = np.r_[low, t[interior], high]
    logs = np.log(nodes)
    values = np.column_stack([np.interp(logs, np.log(t), y) for y in fractions.T])
    return np.trapezoid(values, x=logs, axis=0) / (logs[-1] - logs[0])


def partition(file):
    low, high = .05, 1000.
    split = np.sqrt(low * high)
    summary, arrays = {}, {}
    for key, trials in (("blob", 21), ("dog", 10), ("sog", 10)):
        group = file[key]
        t, total, mean, fluctuating, cross = [group[name][()] for name in
            ("time", "total_energy_density", "mean_flow__energy", "turbulent_energy", "cross_term")]
        if not (np.all(total > 0) and np.all(t > 0)):
            raise ValueError(f"Nonpositive time or total energy for Fig. 4B, {key}")
        measured = np.column_stack((mean, fluctuating, cross)) / total[:, None]
        named = np.column_stack([group[name][()] for name in
            ("mean_flow_fraction", "turbulent_energy_fraction", "cross_term_fraction")])
        t_unique, inverse, counts = np.unique(t, return_inverse=True, return_counts=True)
        unique_values = np.column_stack([np.bincount(inverse, weights=y) / counts for y in measured.T])
        if not (np.isfinite(unique_values).all() and t_unique[0] <= low and t_unique[-1] >= high):
            raise ValueError(f"Insufficient data for both registered intervals in {key}")
        arrays[f"partition_{key}"] = np.column_stack((t_unique, unique_values))
        summary[key] = {
            "ensemble_size": trials, "time_rows": len(t), "duplicate_time_rows": len(t) - len(t_unique),
            "time_span_s": t_unique[[0, -1]].tolist(),
            "largest_relative_energy_partition_residual": float(abs(measured.sum(axis=1) - 1.).max()),
            "largest_fraction_difference_vs_figure_columns": abs(measured - named).max(axis=0).tolist(),
            "archive_cross_fraction_duplicates_turbulent_fraction": bool(np.array_equal(named[:, 2], named[:, 1])),
            "signed_cross_fraction_limits": [float(measured[:, 2].min()), float(measured[:, 2].max())],
            "coherent_fluctuating_cross_logtime_first_half": average_in_log_time(t_unique, unique_values, low, split).tolist(),
            "coherent_fluctuating_cross_logtime_second_half": average_in_log_time(t_unique, unique_values, split, high).tolist(),
        }
    return {"columns": list(ENERGY_COLUMNS), "averaging_bounds_s": [low, float(split), high],
            "groups": summary}, arrays


def run(raw, out):
    observed = {}
    for name, digest in SOURCES.items():
        path = raw / name
        observed[name] = sha256(path.read_bytes()).hexdigest()
        if observed[name] != digest:
            raise ValueError(f"Input checksum differs for {path}")
    with h5py.File(raw / "Fig1B_Energy_spreading.h5") as source:
        images = snapshots(source)
    with h5py.File(raw / "Fig5A_kymograph.h5") as source:
        spread, spread_tables = spreading(source)
    with h5py.File(raw / "Fig4B_energy_distribution.h5") as source:
        energy, energy_tables = partition(source)
    checks = {
        "energy_partition_closes_with_signed_terms": all(
            row["largest_relative_energy_partition_residual"] < 1.e-10 for row in energy["groups"].values()),
        "uniform_disk_radial_quadrature": all(
            test["uniform_disk_calibration_error_mm"] < 1.e-9 and test["uniform_disk_calibration_error_mm2"] < 1.e-8
            for test in spread.values()),
    }
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "observables.npz", **spread_tables, **energy_tables)
    save_summary(out, {"dataset_doi": ARCHIVE, "article_doi": "10.1073/pnas.2526858123",
                       "input_sha256": observed, "h5py": h5py.__version__, "plane_snapshots": images,
                       "radial_spreading": {"ensemble_size": 10, "columns": list(WIDTH_COLUMNS), "domains": spread},
                       "energy_partition": energy, "checks": checks}, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/raw/dynamics")
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E15")
    args = parser.parse_args()
    run(args.raw, args.out)
