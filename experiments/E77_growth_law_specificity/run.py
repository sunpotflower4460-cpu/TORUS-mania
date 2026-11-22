"""Exploratory specificity checks of the already observed E29/E34 growth laws."""

import argparse
import csv
import hashlib
from itertools import product
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from experiments.common import save_summary


ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "f014dbd642342b9e2682c9bb677c529a672a01be"
REGISTRATION_COMMIT = "4d27d24822b51697c989ad6e3ddfa56a8601ef57"
INPUTS = {
    "research/results/E29/sealed_predictions.json":
        "f57796a45c501ea06ba46f9c831fd977a483a92bf936b0d096bef17fae2244d7",
    "research/results/E29/summary.json":
        "9c6e9423332506b5f545d9140895c5110b6e842d757366ed52b724c1ee589650",
    "research/results/E34/summary.json":
        "58557d81e2459d32df4f45e7c34d9c3bb2e723f3c2172307e83e034b1b519854",
}
REGISTRATION_PATH = "research/registrations/E77-growth-law-specificity.md"
REGISTRATION_SHA256 = "09c7567c28e992676614157f60a554387a51b30a63e42a2c0c29c3a1b7c3d667"
MODELS = ("fixed_clock", "fixed_distance", "two_waiting_times", "power_law")
GROUPS = ("WT", "eto2", "line1", "line4", "line2")
TARGETS = GROUPS[1:]
FIT_STARTS = (0.1, 2.0, 10.0)
Q_COMMON = (0.75, 0.875, 1.0, 1.125, 1.25)
SSE_TOLERANCES = (0.01, 0.05, 0.10)


def pinned_json(relative, expected):
    contents = (ROOT / relative).read_bytes()
    if hashlib.sha256(contents).hexdigest() != expected:
        raise ValueError(f"Input differs from the registered base: {relative}")
    return json.loads(contents)


def observations(panel):
    points = np.asarray(panel["xy"], dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.all(points > 0):
        raise ValueError("Every registered marker must have positive finite coordinates")
    if not np.isfinite(points).all():
        raise ValueError("Nonfinite registered marker")
    return points.T


def frequency(model, production):
    p = np.asarray(production, dtype=float)
    if model["family"] == "power_law":
        return np.exp(model["log_A"] + model["b"] * np.log(p))
    return 1.0 / (model["tau_h"] + model["length_cells"] / p)


def spacing(model, production):
    p = np.asarray(production, dtype=float)
    return p / frequency(model, p) + model["spacing_offset_cells"]


def score(actual, predicted):
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    if actual.shape != predicted.shape or not np.all(actual > 0):
        raise ValueError("Scores require aligned positive observations")
    invalid = ~np.isfinite(predicted) | (predicted <= 0)
    result = {
        "n_observations": int(actual.size),
        "nonpositive_or_nonfinite_predictions": int(invalid.sum()),
        "log_RMSE": None,
        "mean_log_error": None,
    }
    if not invalid.any():
        residual = np.log(predicted / actual)
        result.update(log_RMSE=float(np.sqrt(np.mean(residual**2))),
                      mean_log_error=float(residual.mean()))
    return result


def marker_score(model, metric, panel):
    p, actual = observations(panel)
    predict = frequency if metric == "frequency" else spacing
    predicted = predict(model, p)
    result = score(actual, predicted)
    result["predictions_in_source_marker_order"] = predicted.tolist()
    dx, dy = panel["readout_width"]
    if np.any(p - dx <= 0) or np.any(actual - dy <= 0):
        raise ValueError("Registered reading interval reaches a nonpositive observation")
    endpoints = np.vstack((predict(model, p - dx), predict(model, p + dx)))
    # Both candidate families are monotone on p>0; the power spacing can decrease.
    low, high = endpoints.min(axis=0), endpoints.max(axis=0)
    result["reading_intervals_with_nonpositive_prediction"] = int((low <= 0).sum())
    result["log_RMSE_digitization_bounds"] = None
    if np.isfinite(endpoints).all() and np.all(low > 0):
        lower = np.log(low / (actual + dy))
        upper = np.log(high / (actual - dy))
        closest = np.where((lower <= 0) & (upper >= 0), 0.0,
                           np.minimum(np.abs(lower), np.abs(upper)))
        furthest = np.maximum(np.abs(lower), np.abs(upper))
        result["log_RMSE_digitization_bounds"] = [
            float(np.sqrt(np.mean(closest**2))), float(np.sqrt(np.mean(furthest**2)))
        ]
    return result


def fit_power(training):
    p, f = observations(training["frequency"])
    x, y = np.log(p), np.log(f)
    intercept, slope = np.linalg.lstsq(np.column_stack((np.ones(len(x)), x)), y,
                                     rcond=None)[0]
    constrained = bool(slope < 0)
    if constrained:
        slope, intercept = 0.0, float(y.mean())
    # Independent closed form; do not call the linear-algebra fitter again.
    mean_x = math.fsum(map(float, x)) / len(x)
    mean_y = math.fsum(map(float, y)) / len(y)
    covariance = math.fsum(float((a - mean_x) * (b - mean_y)) for a, b in zip(x, y))
    variance = math.fsum(float((a - mean_x)**2) for a in x)
    closed_b = max(0.0, covariance / variance)
    closed_a = mean_y - closed_b * mean_x
    model = {"family": "power_law", "log_A": float(intercept),
             "A": float(np.exp(intercept)), "b": float(slope)}
    sp, observed_spacing = observations(training["spacing"])
    model["spacing_offset_cells"] = float(
        np.mean(observed_spacing - sp / frequency(model, sp)))
    residual = np.log(frequency(model, p) / f)
    fit = {
        "training_frequency_markers": len(p),
        "training_spacing_markers": len(sp),
        "nonnegative_slope_boundary_used": constrained,
        "training_frequency_log_SSE": float(residual @ residual),
        "closed_form_log_A": closed_a,
        "closed_form_b": closed_b,
        "max_absolute_coefficient_difference": float(max(abs(intercept - closed_a),
                                                          abs(slope - closed_b))),
    }
    return model, fit


def target_predictions(name, model, velocities, periods, q=None):
    ratio = velocities[0] / velocities[1:]
    if q is not None:
        ratio = ratio * np.asarray(q)
    if name == "fixed_clock":
        return np.full(len(ratio), periods[0])
    if name == "fixed_distance":
        return periods[0] * ratio
    if name == "two_waiting_times":
        tau = model["tau_h"]
        return tau + (periods[0] - tau) * ratio
    return periods[0] * ratio**model["b"]


def evaluate_targets(models, velocities, periods, q=None):
    results = {}
    for name, model in models.items():
        predicted = target_predictions(name, model, velocities, periods, q)
        results[name] = {**score(periods[1:], predicted),
                         "predictions_h": dict(zip(TARGETS, map(float, predicted)))}
    return results


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def reading_sensitivity(models, velocities, periods, widths, out):
    rows, losses = [], []
    for index, signs in enumerate(product((-1, 1), repeat=2 * len(GROUPS))):
        v = velocities + np.array(signs[:5]) * widths["growth_um_per_h"]
        t = periods + np.array(signs[5:]) * widths["peak_period_h"]
        results = evaluate_targets(models, v, t)
        loss = [results[name]["log_RMSE"] for name in MODELS]
        losses.append(loss)
        predictions = [results[name]["predictions_h"][group]
                       for name in MODELS for group in TARGETS]
        rows.append([index, *signs, *loss, *predictions])
    filename = "E34_reading_corners.csv"
    header = (["corner_index"] + ["velocity_sign_" + g for g in GROUPS]
              + ["period_sign_" + g for g in GROUPS]
              + ["log_RMSE_" + m for m in MODELS]
              + [f"prediction_h_{m}_{g}" for m in MODELS for g in TARGETS])
    write_csv(out / filename, header, rows)
    array = np.asarray(losses, dtype=float)
    return {
        "file": filename,
        "number_of_corners": len(rows),
        "fixed_q": 1.0,
        "registered_scope": "Reproduction of the original three models' existing reading-corner ranges and comparison count.",
        "power_comparison_status": "supplementary_analysis_added_after_registration",
        "power_comparison_note_ja": "登録後の補助解析（既存の1,024端点設定をそのまま流用）。主判定には用いない。",
        "shared_WT_reading_is_the_same_for_all_four_targets": True,
        "log_RMSE_ranges": {m: [float(array[:, i].min()), float(array[:, i].max())]
                            for i, m in enumerate(MODELS)},
        "two_waits_better_than_both_original_controls": int(
            np.sum(array[:, 2] < np.minimum(array[:, 0], array[:, 1]))),
        "power_better_than_two_waits": int(np.sum(array[:, 3] < array[:, 2])),
        "interpretation": "Fixed image-reading corners, not random draws, biological replicates or coverage probabilities.",
    }


def length_sensitivity(models, velocities, periods):
    conditions = [(f"common_{q:g}", "common_change", (q,) * 4) for q in Q_COMMON]
    conditions.extend((f"endpoint_{i:02d}", "four_target_endpoints", q)
                      for i, q in enumerate(product((0.75, 1.25), repeat=4)))
    return [{"condition": name, "family": family,
             "mature_cell_length_ratio_to_WT": dict(zip(TARGETS, q)),
             "WT_ratio": 1.0,
             "scores": evaluate_targets(models, velocities, periods, q)}
            for name, family, q in conditions]


def tau_sensitivity(training, holdout, velocities, periods, out):
    p, f = observations(training["frequency"])
    sp, observed_spacing = observations(training["spacing"])
    hp, hf = observations(holdout["frequency"])
    hs, observed_holdout_spacing = observations(holdout["spacing"])
    records, csv_rows = [], []
    all_frequency, all_spacing, all_target = [], [], []
    max_length_spread, max_sse_spread, all_converged = 0.0, 0.0, True
    for index in range(401):
        tau = index / 100.0
        fits = []
        for start in FIT_STARTS:
            def residual(value):
                period = tau + value[0] / p
                if np.any(period <= 0):
                    raise ValueError("A zero period cannot enter the logarithmic objective")
                return np.log(period) + np.log(f)
            result = least_squares(residual, [start], bounds=(0.0, np.inf),
                                   ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=10000)
            fits.append({"start_cells": start, "length_cells": float(result.x[0]),
                         "training_log_SSE": float(result.fun @ result.fun),
                         "converged": bool(result.success), "nfev": int(result.nfev)})
        best = min(fits, key=lambda item: item["training_log_SSE"])
        length_spread = max(x["length_cells"] for x in fits) - min(x["length_cells"] for x in fits)
        sse_spread = max(x["training_log_SSE"] for x in fits) - min(x["training_log_SSE"] for x in fits)
        max_length_spread = max(max_length_spread, length_spread)
        max_sse_spread = max(max_sse_spread, sse_spread)
        all_converged = all_converged and all(x["converged"] for x in fits)
        model = {"family": "two_waiting_times", "tau_h": tau,
                 "length_cells": best["length_cells"]}
        model["spacing_offset_cells"] = float(
            np.mean(observed_spacing - sp / frequency(model, sp)))
        fp, ss = frequency(model, hp), spacing(model, hs)
        tp = target_predictions("two_waiting_times", model, velocities, periods)
        fs, spaces, ts = score(hf, fp), score(observed_holdout_spacing, ss), score(periods[1:], tp)
        all_frequency.append(fp)
        all_spacing.append(ss)
        all_target.append(tp)
        row = {"grid_index": index, "tau_h": tau, "length_cells": best["length_cells"],
               "spacing_offset_cells": model["spacing_offset_cells"],
               "training_frequency_log_SSE": best["training_log_SSE"],
               "multistart_length_spread": length_spread, "multistart_SSE_spread": sse_spread,
               "E34_positive_growth_wait_at_WT": bool(tau < periods[0])}
        records.append(row)
        csv_rows.append([index, tau, best["length_cells"], model["spacing_offset_cells"],
                         best["training_log_SSE"], int(row["E34_positive_growth_wait_at_WT"]),
                         *[value for fit in fits for value in
                           (fit["length_cells"], fit["training_log_SSE"], int(fit["converged"]), fit["nfev"])],
                         fs["log_RMSE"], spaces["log_RMSE"], ts["log_RMSE"],
                         fs["nonpositive_or_nonfinite_predictions"],
                         spaces["nonpositive_or_nonfinite_predictions"],
                         ts["nonpositive_or_nonfinite_predictions"],
                         *fp, *ss, *tp])
    filename = "tau_profile.csv"
    header = ["grid_index", "tau_h", "length_cells", "spacing_offset_cells",
              "training_frequency_log_SSE", "E34_positive_growth_wait_at_WT"]
    header += [f"start_{start:g}_{field}" for start in FIT_STARTS
               for field in ("length_cells", "training_log_SSE", "converged", "nfev")]
    header += ["E29_frequency_log_RMSE", "E29_spacing_log_RMSE", "E34_period_log_RMSE",
               "E29_frequency_invalid_predictions", "E29_spacing_invalid_predictions",
               "E34_period_invalid_predictions"]
    header += [f"E29_frequency_prediction_{i:03d}" for i in range(len(hp))]
    header += [f"E29_spacing_prediction_{i:03d}" for i in range(len(hs))]
    header += [f"E34_period_prediction_h_{group}" for group in TARGETS]
    write_csv(out / filename, header, csv_rows)
    best_record = min(records, key=lambda item: item["training_frequency_log_SSE"])
    minimum = best_record["training_frequency_log_SSE"]
    arrays = (np.asarray(all_frequency), np.asarray(all_spacing), np.asarray(all_target))
    sets = {}
    for tolerance in SSE_TOLERANCES:
        selected = [i for i, row in enumerate(records)
                    if row["training_frequency_log_SSE"] <= (1.0 + tolerance) * minimum]
        envelopes = {}
        for label, array in zip(("E29_frequency", "E29_spacing", "E34_period_h"), arrays):
            subset = array[selected]
            envelopes[label] = {"min_in_input_order": subset.min(axis=0).tolist(),
                                "max_in_input_order": subset.max(axis=0).tolist(),
                                "nonpositive_predictions_across_grid_points": int((subset <= 0).sum())}
        sets[f"within_{round(100 * tolerance)}_percent"] = {
            "relative_SSE_tolerance": tolerance,
            "maximum_training_log_SSE": float((1 + tolerance) * minimum),
            "grid_indices": selected,
            "tau_h_values": [records[i]["tau_h"] for i in selected],
            "prediction_envelopes": envelopes,
        }
    return {
        "file": filename, "grid_points": len(records), "tau_min_h": 0.0,
        "tau_max_h": 4.0, "tau_step_h": 0.01, "L_initial_values_cells": FIT_STARTS,
        "best_training_grid_point": best_record,
        "all_three_starts_converged": all_converged,
        "maximum_multistart_length_difference_cells": max_length_spread,
        "maximum_multistart_SSE_difference": max_sse_spread,
        "sensitivity_sets": sets,
        "scoring_order": {"E29_frequency": "E29/summary.json holdout.frequency.xy",
                          "E29_spacing": "E29/summary.json holdout.spacing.xy",
                          "E34": TARGETS},
        "interpretation": "Training-SSE tolerance sets; no biological confidence interval. All 401 rows, including invalid target predictions, are retained. A tau at or above WT period loses the positive growth-wait interpretation.",
    }


def run(out):
    seal, existing_e29, existing_e34 = [pinned_json(path, expected)
                                       for path, expected in INPUTS.items()]
    registration = (ROOT / REGISTRATION_PATH).read_bytes()
    if hashlib.sha256(registration).hexdigest() != REGISTRATION_SHA256:
        raise ValueError("Registration differs from the published design")
    out.mkdir(parents=True, exist_ok=True)
    models = {name: {"family": "two_waiting_times", **parameters}
              for name, parameters in seal["models"].items()}
    power, fit = fit_power(seal["training"])
    models["power_law"] = power
    models = {name: models[name] for name in MODELS}
    holdout = existing_e29["holdout"]
    e29 = {name: {metric: marker_score(model, metric, panel)
                  for metric, panel in holdout.items()} for name, model in models.items()}
    records = existing_e34["genotype_observations"]
    velocities = np.array([records[group]["growth_um_per_h"] for group in GROUPS])
    periods = np.array([records[group]["peak_period_h"] for group in GROUPS])
    e34 = evaluate_targets(models, velocities, periods)
    reading = reading_sensitivity(models, velocities, periods,
                                  existing_e34["median_reading_half_width"], out)
    q_cases = length_sensitivity(models, velocities, periods)
    profile = tau_sensitivity(seal["training"], holdout, velocities, periods, out)
    old_target_names = {"fixed_clock": "constant_period", "fixed_distance": "constant_distance",
                        "two_waiting_times": "two_waiting_times"}
    original_e29_errors, original_e34_errors, original_reading_errors = [], [], []
    for name, old_name in old_target_names.items():
        for metric in holdout:
            old, new = existing_e29["scores"][name][metric], e29[name][metric]
            original_e29_errors.append(abs(old["log_RMSE"] - new["log_RMSE"]))
            original_reading_errors.extend(abs(a - b) for a, b in zip(
                old["log_RMSE_digitization_bounds"], new["log_RMSE_digitization_bounds"]))
        old = existing_e34["held_out_treatments"]["models"][old_name]
        original_e34_errors.append(abs(old["log_rmse"] - e34[name]["log_RMSE"]))
        original_e34_errors.extend(abs(old["predictions_h"][g] - e34[name]["predictions_h"][g])
                                   for g in TARGETS)
        original_reading_errors.extend(abs(a - b) for a, b in zip(
            old["log_rmse_at_reading_corners"], reading["log_RMSE_ranges"][name]))
    delta_errors = []
    sp, sy = observations(seal["training"]["spacing"])
    for name in old_target_names:
        delta_errors.append(abs(models[name]["spacing_offset_cells"]
                                - float(np.mean(sy - sp / frequency(models[name], sp)))))
    baseline_q = next(case for case in q_cases if case["condition"] == "common_1")
    wt_predictions = {name: float(target_predictions(name, model, np.repeat(velocities[0], 5),
                                                    np.repeat(periods[0], 5))[0])
                      for name, model in models.items()}
    generated = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in (out / "tau_profile.csv", out / "E34_reading_corners.csv")}
    summary = {
        "experiment": "E77", "analysis_type": "exploratory_reanalysis_of_known_outcomes",
        "base_commit": BASE_COMMIT, "registration_commit": REGISTRATION_COMMIT,
        "registration": {"path": REGISTRATION_PATH, "sha256": REGISTRATION_SHA256},
        "input_sha256": INPUTS,
        "sources": {
            "E29": {"doi": "10.1016/j.devcel.2021.07.005", "figures": "7A and 7B",
                    "source_pdf_url": seal["source_url"], "source_pdf_sha256": seal["source_sha256"]},
            "E34": {"doi": "10.1093/plphys/kiaf382", "figures": "3I and S3A",
                    "source_files": existing_e34["sources"]},
        },
        "observable_and_independence_notes": [
            "E29 frequency, cell production and spacing come from the same root records; production and spacing share a mature cortical cell-length denominator. The figure does not restore root IDs or pair markers between panels.",
            "Overlapping figure markers are not reconstructed. The panels are not two independent biological samples; no composite likelihood, AIC, biological p value or biological confidence interval is used.",
            "De Gernier et al. (2025), accepted manuscript p.10 and Fig.1, place the DR5::LUC peak after initial priming, near the distal elongation zone. Both E29 and E34 transfer a reporter observable, not a directly measured first-return time. A constant reporter delay alone would not change the period; constancy across interventions is not assumed here.",
            "The source paper's finite-event-count correction of free spacing cannot be reconstructed without the root-specific peak counts. The registered E29 delta is an empirical offset, not an independent measurement of L or pathway length.",
            "All E29 holdout outcomes and all E34 genotypes were already known before E77. The historical partitions are reused for an exploratory comparison, not a fresh blind prediction.",
        ],
        "models": models, "power_law_fit": fit,
        "fit_parameter_accounting": {
            "fixed_clock": {"frequency_parameters": 1, "spacing_offsets": 1},
            "fixed_distance": {"frequency_parameters": 1, "spacing_offsets": 1},
            "two_waiting_times": {"frequency_parameters": 2, "spacing_offsets": 1},
            "power_law": {"frequency_parameters": 2, "spacing_offsets": 1},
            "E34": "Only tau or b is transferred; every law uses target WT v0,T0. No four-target coefficient fitting. L is absorbed into the WT growth scale.",
        },
        "E29_historical_holdout": e29,
        "E34_baseline_q_one": {"target_order": TARGETS, "WT_velocity_um_h": float(velocities[0]),
                               "WT_period_h": float(periods[0]), "scores": e34},
        "E34_reading_sensitivity": reading,
        "E34_mature_cell_length_sensitivity": {
            "common_q_values": Q_COMMON, "endpoint_q_values": [0.75, 1.25],
            "conditions": q_cases,
            "interpretation": "Hypothetical target/WT cell-length ratios, not a measured distribution. The identical q transformation is given to all growth-dependent models. WT remains q=1. Common endpoint conditions and all-equal endpoint corners are deliberately both retained.",
        },
        "tau_training_SSE_profile": profile,
        "generated_table_sha256": generated,
        "reproduction_errors": {
            "max_existing_E29_log_RMSE_difference": max(original_e29_errors),
            "max_existing_E34_prediction_or_log_RMSE_difference": max(original_e34_errors),
            "max_existing_reading_bound_difference": max(original_reading_errors),
            "max_existing_spacing_offset_difference": max(delta_errors),
            "WT_predictions_h": wt_predictions,
        },
        "interpretation_limits": [
            "The additive waiting-time law is also generated by an open supply or local recovery schedule. Its predictive ranking does not identify a molecular return path or toroidal geometry.",
            "A better empirical power law would not show that circulation is absent. A worse power law would not exclude all non-return mechanisms.",
            "Tau-profile minima use low-production frequency only. No target outcome selects a preferred tau; all registered grid rows and predictions are saved.",
            "Marker reading errors, SSE tolerance sets and hypothetical cell-length ranges are different kinds of sensitivity and are not biological sampling uncertainty.",
        ],
        "checks": {
            "all_input_hashes_equal_registered_base": True,
            "published_registration_hash_matches": True,
            "existing_three_E29_models_reproduced": max(original_e29_errors) < 1e-12,
            "existing_three_E34_models_reproduced": max(original_e34_errors) < 1e-12,
            "existing_digitization_ranges_reproduced": max(original_reading_errors) < 1e-12,
            "original_spacing_offset_rule_reproduced": max(delta_errors) < 1e-12,
            "power_fit_agrees_with_independent_closed_form": fit["max_absolute_coefficient_difference"] < 1e-12,
            "all_four_models_match_target_WT": all(abs(value - periods[0]) < 1e-12
                                                  for value in wt_predictions.values()),
            "q_one_reproduces_target_baseline": baseline_q["scores"] == e34,
            "all_401_tau_points_and_three_starts_recorded": profile["grid_points"] == 401
                and profile["all_three_starts_converged"],
            "tau_multistart_optima_agree_in_parameters_and_SSE":
                profile["maximum_multistart_length_difference_cells"] < 1e-5
                and profile["maximum_multistart_SSE_difference"] < 1e-8,
            "all_five_common_and_sixteen_endpoint_q_conditions_recorded":
                sum(c["family"] == "common_change" for c in q_cases) == 5
                and sum(c["family"] == "four_target_endpoints" for c in q_cases) == 16,
            "all_1024_reading_corners_recorded": reading["number_of_corners"] == 1024,
            "original_corner_comparison_reproduced": reading["two_waits_better_than_both_original_controls"]
                == existing_e34["held_out_treatments"]["corners_with_two_waits_better_than_both_controls"],
        },
    }
    save_summary(out, summary, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E77")
    run(parser.parse_args().out)
