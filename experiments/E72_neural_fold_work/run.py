"""Recompute signed force, impulse and hydrogel work in a chick neural fold."""

import numpy as np
from openpyxl import load_workbook
from scipy.integrate import cumulative_trapezoid
from scipy.stats import ttest_ind

from experiments import calibrated_formation_sources as inputs
from experiments.common import save_summary

BOOTSTRAPS = 10_000
SEED = 721120


def worksheet(path, name):
    """Preserve the original 1-based worksheet row addresses."""
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        return [None, *workbook[name].values]
    finally:
        workbook.close()


def series(rows, first, last):
    time = np.asarray([row[0] for row in rows[first : last + 1]], dtype=float)
    sample = np.asarray([row[1:11] for row in rows[first : last + 1]], dtype=float)
    return time, sample


def compare(control, treated, rng):
    control_draws = rng.choice(control, (BOOTSTRAPS, len(control)))
    treated_draws = rng.choice(treated, (BOOTSTRAPS, len(treated)))
    difference = control_draws.mean(axis=1) - treated_draws.mean(axis=1)
    return {
        "vehicle_n": len(control),
        "rock_inhibition_n": len(treated),
        "vehicle_mean": float(control.mean()),
        "rock_inhibition_mean": float(treated.mean()),
        "vehicle_minus_rock_inhibition": float(control.mean() - treated.mean()),
        "bootstrap_percentile_95_ci_difference": np.percentile(
            difference, [2.5, 97.5]
        ).tolist(),
    }


def impulse(time, force):
    early = time <= 60
    time, force = time[early], force[early].T
    complete = force[np.isfinite(force).all(axis=1)]
    interpolated = np.array(
        [
            np.interp(time, time[np.isfinite(row)], row[np.isfinite(row)])
            for row in force
        ]
    )
    return np.trapezoid(complete, time, axis=1), np.trapezoid(
        interpolated, time, axis=1
    )


def work_curve(force_nn, displacement_um):
    return 0.001 * cumulative_trapezoid(force_nn, displacement_um, initial=0.0)


def vehicle_work(rows, time, strain, force):
    strain_ids = rows[7][1:11]
    force_ids = tuple(value.replace("_", " ") for value in rows[26][1:11])
    result = []
    for j, embryo in enumerate(strain_ids):
        f = force[:, force_ids.index(embryo)]
        displacement = strain[:, j] * rows[18][j + 1] / 100.0
        available = np.isfinite(f) & np.isfinite(displacement)
        times = time[available]
        work = work_curve(f[available], displacement[available])
        peak = int(work.argmax())
        result.append(
            {
                "embryo": embryo,
                "initial_width_um": rows[18][j + 1],
                "times_min": times.tolist(),
                "closure_displacement_um": displacement[available].tolist(),
                "force_nn": f[available].tolist(),
                "cumulative_sensor_work_pj": work.tolist(),
                "peak_work_pj": float(work[peak]),
                "peak_work_time_min": float(times[peak]),
                "endpoint_work_pj": float(work[-1]),
                "intervals_with_a_missing_intermediate_time": int(
                    np.count_nonzero(np.diff(times) > 30)
                ),
            }
        )
    return result


def example_work(rows):
    data = np.asarray([row[7:13] for row in rows[7:21]], dtype=float)
    time, diameter, displacement, _, force_time, force = data.T
    if not np.array_equal(time, force_time) or not np.allclose(
        displacement, diameter - diameter[0], atol=1e-5
    ):
        raise ValueError("Extended Data Fig. 8 rows do not match in time or diameter")
    work = work_curve(force, displacement)
    return {
        "times_min": time.tolist(),
        "worksheet_diameter_um": diameter.tolist(),
        "worksheet_displacement_um": displacement.tolist(),
        "worksheet_force_magnitude_nn": force.tolist(),
        "cumulative_pj": work.tolist(),
        "peak_work_pj": float(work.max()),
        "endpoint_work_pj": float(work[-1]),
        "diameter_change_um": float(diameter[-1] - diameter[0]),
    }


def values_with_missing(array):
    return [[float(x) if np.isfinite(x) else None for x in row] for row in array]


def run(raw, out):
    names = ("neural-main.xlsx", "neural-extended.xlsx")
    provenance = inputs.verified_inputs(raw, names)
    rows = worksheet(raw / names[0], "Fig 4")
    time, force = series(rows, 27, 35)
    treated_time, treated = series(rows, 40, 48)
    strain_time, strain = series(rows, 8, 16)
    if not np.array_equal(time, treated_time) or not np.array_equal(time, strain_time):
        raise ValueError("Figure 4 worksheets do not share a time grid")
    rng = np.random.default_rng(SEED)
    force_stats = {
        str(minute): compare(force[time == minute][0], treated[time == minute][0], rng)
        for minute in (60, 120)
    }
    control_impulse, control_imputed = impulse(time, force)
    treated_impulse, treated_imputed = impulse(time, treated)
    energy = np.asarray([row[1:3] for row in rows[52:62]], dtype=float)
    welch_p = float(ttest_ind(energy[:, 0], energy[:, 1], equal_var=False).pvalue)
    equal_variance_p = float(
        ttest_ind(energy[:, 0], energy[:, 1], equal_var=True).pvalue
    )
    energies = compare(energy[:, 0], energy[:, 1], rng)
    energies["published_pvalue"] = 0.375
    energies["two_sided_welch_ttest_pvalue"] = welch_p
    energies["two_sided_equal_variance_ttest_pvalue"] = equal_variance_p
    vehicle = vehicle_work(rows, time, strain, force)
    peak = np.sort([row["peak_work_pj"] for row in vehicle])
    example = example_work(worksheet(raw / names[1], "FigS8"))
    impulse_nn_min = compare(control_impulse, treated_impulse, rng)
    impulse_nn_s = {
        "vehicle_n": impulse_nn_min["vehicle_n"],
        "rock_inhibition_n": impulse_nn_min["rock_inhibition_n"],
        **{
            key: 60 * impulse_nn_min[key]
            for key in (
                "vehicle_mean",
                "rock_inhibition_mean",
                "vehicle_minus_rock_inhibition",
            )
        },
        "bootstrap_percentile_95_ci_difference": [
            60 * bound
            for bound in impulse_nn_min["bootstrap_percentile_95_ci_difference"]
        ],
    }
    summary = {
        "experiment": "E72",
        "doi": "10.1038/s41563-024-01942-9",
        "inputs_sha256": provenance,
        "bootstrap_seed": SEED,
        "bootstrap_draws": BOOTSTRAPS,
        "force_direction": "positive = medial compression; negative = outward",
        "figure_4e_forces_nn": {
            "times_min": time.tolist(),
            "vehicle_ids": list(rows[26][1:11]),
            "rock_inhibition_ids": list(rows[39][1:11]),
            "vehicle_at_each_time": values_with_missing(force),
            "rock_inhibition_at_each_time": values_with_missing(treated),
            "comparisons_at_minutes": force_stats,
        },
        "signed_impulse_0_to_60_min": {
            "complete_cases_nn_min": impulse_nn_min,
            "complete_cases_nn_s": impulse_nn_s,
            "interpolated_30_min_if_missing_nn_min": compare(
                control_imputed, treated_imputed, rng
            ),
        },
        "figure_4f_max_sensor_energy_pj_unpaired": energies,
        "figure_4be_matched_vehicle_sensor_work": vehicle,
        "figure_4be_vs_4f_vehicle_group_pj": {
            "mean_peak_from_paired_work": float(np.mean(peak)),
            "mean_reported_peak": float(energy[:, 0].mean()),
            "sorted_values_rmse_no_embryo_matching": float(
                np.sqrt(np.mean((peak - np.sort(energy[:, 0])) ** 2))
            ),
        },
        "extended_figure_8_example": example,
        "interpretation_limits": [
            "The printed cylinder deforms during ongoing closure. The zero is the initial reading.",
            "Reported force comes from the sensor deformation and its mechanical calibration.",
            "Figure 4f rows have no embryo IDs. Work entering a local sensor is not a whole-embryo flux.",
            "The FigS8 worksheet diameter grows, while the caption describes the narrowing model.",
        ],
        "checks": {
            "both_primary_times_have_ten_finite_embryos_per_group": all(
                np.isfinite(group[time == minute]).all() and group.shape[1] == 10
                for group in (force, treated)
                for minute in (60, 120)
            ),
            "complete_case_and_sensitivity_do_not_substitute_different_embryos": (
                len(control_impulse) == len(treated_impulse) == 9
                and len(control_imputed) == len(treated_imputed) == 10
            ),
            "figure_4f_welch_p_matches_caption_to_three_decimals": round(welch_p, 3)
            == energies["published_pvalue"],
            "work_conversion_one_nn_micrometre_is_one_thousandth_pj": bool(
                np.isclose(work_curve([1, 1], [0, 1])[-1], 0.001)
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, inputs.__file__)
