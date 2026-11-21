"""Reanalyse division counts and plane orientation after local cell removal."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from experiments.common import save_summary


ROOT = Path(__file__).resolve().parents[2]
READINGS = ROOT / "experiments/local_reflux_readings.json"
GROUPS = ("control", "control_plus_NAA", "ktn1", "ktn1_plus_NAA")
COUNTS = ("total", "anticlinal", "periclinal")


def run(readings, out):
    panels = json.loads(readings.read_text(encoding="utf-8"))["panels"]
    averages = {}
    for i, name in enumerate(GROUPS):
        counts = {metric: panels[f"fig6e_{metric}"]["values"][i] for metric in COUNTS}
        averages[name] = {**counts, "fraction_anticlinal_from_mean_counts": counts["anticlinal"]/counts["total"],
                          "total_minus_sum_of_types": counts["total"] - counts["anticlinal"] - counts["periclinal"]}
    error = panels["fig6e_total"]["digitization_halfwidth"]
    contrasts = {
        name: {key: averages[f"{name}_plus_NAA"][key] - averages[name][key] for key in COUNTS}
        for name in ("control", "ktn1")
    }
    text_control = .90
    text_naa = 2.40
    result = {
        "experiment": "E25", "study_doi": "10.1101/gad.276964.115",
        "figure_readings_sha256": sha256(readings.read_bytes()).hexdigest(),
        "figure_6E_divisions_15h_after_ablation": {
            "units": "divisions per ablation event", "n_ablation_events_reported_per_group": 20,
            "readout_halfwidth_per_bar": error, "group_means_from_bars": averages,
            "NAA_minus_no_NAA": contrasts,
            "anticlinal_interaction_control_minus_ktn1": contrasts["control"]["anticlinal"] - contrasts["ktn1"]["anticlinal"],
            "note": "A ratio of mean counts is not a probability of a root forming a lateral root.",
        },
        "text_fig6_and_supplement_anticlinal_means_compared_with_Fig6E": {
            "without_NAA": {"text": text_control, "printed_SE": .14, "Figure_6E_readout": averages["control"]["anticlinal"]},
            "with_NAA": {"text": text_naa, "printed_SE": .15, "Figure_6E_readout": averages["control_plus_NAA"]["anticlinal"]},
            "note": "The paper refers to two figures in the same sentence. The bars and narrative are recorded separately.",
        },
        "text_fig2_ablation_15h": {
            "founder_cells": {"total_mean_SE": [3.4, .22], "periclinal_mean_SE": [2.5, .17]},
            "no_detectable_DR5_before_ablation": {"total_mean_SE": [2.9, .19], "periclinal_mean_SE": [2.6, .18]},
            "reported_n_events_per_group": 20,
        },
        "text_fig4_ablation_15h": {
            "slr_divisions_mean_SE": [2.45, .15], "tir1_afb2_afb3_divisions_mean_SE": [1.8, .2],
            "n_events_per_group": 20, "divisions_also_observed_with_NPA": True,
        },
        "checks": {
            "orientation_counts_add_to_total_within_figure_resolution": all(
                abs(row["total_minus_sum_of_types"]) <= 3*error for row in averages.values()
            ),
            "blank_anticlinal_bar_read_as_zero": averages["ktn1"]["anticlinal"] == 0.,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, result, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", type=Path, default=READINGS)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E25")
    args = parser.parse_args()
    run(args.readings, args.out)
