"""Quantify whether imposed bends set the number and rate of root development."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as t_distribution

from experiments.common import save_summary
from experiments.E20_bending_controls import read_figure

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def mean_contrast(first, second, experiments):
    mean_a, se_a = first
    mean_b, se_b = second
    delta = mean_b - mean_a
    variance = se_a**2 + se_b**2
    standard_error = np.sqrt(variance)
    df = (experiments - 1) * variance**2 / (se_a**4 + se_b**4)
    # This is an independence reference. The treatment arms may share batches.
    independent_width = float(t_distribution.ppf(.975, df) * standard_error)
    largest_paired_width = float(t_distribution.ppf(.975, experiments-1) * (se_a + se_b))
    return {
        "difference_per_plant": delta,
        "independent_welch_df_reference": df,
        "independent_SE_reference": float(standard_error),
        "independent_95_reference": [delta-independent_width, delta+independent_width],
        "possible_SE_range_from_unknown_batch_correlation": [abs(se_a-se_b), se_a+se_b],
        "paired_95_envelope_for_unknown_batch_correlation": [delta-largest_paired_width, delta+largest_paired_width],
    }


def analyse_table(article):
    n = article["independent_experiments"]
    evaluations = {}
    for region, values in article["regions"].items():
        intact, bent, cut, cut_bent = values
        evaluations[region] = {
            "bending_intact": mean_contrast(intact, bent, n),
            "bending_cut": mean_contrast(cut, cut_bent, n),
            "tip_removed_without_bend": mean_contrast(intact, cut, n),
            "tip_removed_with_bend": mean_contrast(bent, cut_bent, n),
        }
        # Only point estimates. Cross-treatment covariance was not published.
        evaluations[region]["point_difference_in_bend_effect_between_cut_and_intact"] = (
            cut_bent[0] - cut[0] - (bent[0] - intact[0]))
    return {**article, "point_effects_and_intervals": evaluations, "preregistered_practical_increase": .50,
            "paired_batch_covariance_available": False}


def compute_scores(actual, predicted, error_bound):
    absolute = abs(actual - predicted)
    lower = np.maximum(absolute - error_bound, 0.)
    upper = absolute + error_bound
    return {
        "mae": float(np.mean(absolute)), "rmse": float(np.sqrt(np.mean(absolute**2))),
        "mae_fig_reading_envelope": [float(np.mean(lower)), float(np.mean(upper))],
        "rmse_fig_reading_envelope": [float(np.sqrt(np.mean(lower**2))), float(np.sqrt(np.mean(upper**2)))],
    }


def analyse_figure(figure):
    periods = figure["periods"]
    hours = np.array([entry["hours"] for entry in periods])
    measured = np.array([entry["root_and_primordia_per_day"] for entry in periods])
    training = hours == 6
    if training.sum() != 1 or (~training).sum() < 3:
        raise ValueError("The holdout comparison requires exactly one 6-hour reference and at least three holdouts")
    value_at_six = float(measured[training][0])
    uncertainty = figure["rate_uncertainty_from_3px"]
    relative_frequency = 6. / hours
    models = {
        "one_per_bend": (24. / hours, np.zeros_like(measured)),
        "fit_proportional_to_bends": (value_at_six*relative_frequency, uncertainty*relative_frequency),
        "constant_fit": (np.full_like(measured, value_at_six), np.full_like(measured, uncertainty)),
    }
    scores = {name: compute_scores(measured[~training], predicted[~training], uncertainty + bound[~training])
              for name, (predicted, bound) in models.items()}
    return {
        "reading_source": figure["source_url"], "reading_source_sha256": figure["source_sha256"],
        "calibration_period_h": 6, "calibration_observed_root_and_primordia_per_day": value_at_six,
        "test_periods_h": hours[~training].tolist(), "observation_uncertainty_per_day": uncertainty,
        "scores": scores,
        "all_plot_points": [
            {**row, "one_per_bend": float(models["one_per_bend"][0][i]),
             "fit_proportional_to_bends": float(models["fit_proportional_to_bends"][0][i]),
             "constant_fit": value_at_six,
             "implied_roots_and_primordia_per_bend": float(measured[i]*hours[i]/24.)}
            for i, row in enumerate(periods)
        ],
    }


def run(table_path, figure_path, out):
    table = json.loads(table_path.read_text(encoding="utf-8"))
    figure = json.loads(figure_path.read_text(encoding="utf-8"))
    table_result, figure_result = analyse_table(table), analyse_figure(figure)
    zeros = np.zeros(4)
    expected = [0., 0.]
    identity = compute_scores(zeros, zeros, zeros)
    checks = {
        "score_identical_predictions": identity["rmse_fig_reading_envelope"] == expected,
        "one_reference_excluded_from_holdout": 6 not in figure_result["test_periods_h"],
        "reported_treatments_all_present": all(len(values) == 4 for values in table["regions"].values()),
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, {"table": table_result, "frequency_holdout": figure_result,
                       "input_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (table_path, figure_path)},
                       "checks": checks}, __file__, read_figure.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, default=HERE / "published_table.json")
    parser.add_argument("--figure", type=Path, default=HERE / "figure_values.json")
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E20")
    args = parser.parse_args()
    run(args.table, args.figure, args.out)
