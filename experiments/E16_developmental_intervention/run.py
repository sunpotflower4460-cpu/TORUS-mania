"""Estimate the effects of ciliary bending with uncertainty from reading a figure."""

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from scipy.stats import fisher_exact

from experiments.common import save_summary
from experiments.E08_survey.run import wilson
from experiments.E16_developmental_intervention import read_figure

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def allowed_counts(n, fractions, tolerance):
    possible = []
    for lower in range(n+1):
        if abs(lower/n - fractions[0]) > tolerance:
            continue
        for lower_and_middle in range(lower, n+1):
            if abs(lower_and_middle/n - fractions[1]) <= tolerance:
                possible.append((lower, lower_and_middle-lower, n-lower_and_middle))
    if not possible:
        raise ValueError(f"Bar does not match any integer counts: n={n}, fractions={fractions}")
    return possible


def endpoints(values):
    return [min(values), max(values)]


def summarize_group(row, tolerance):
    n = row["n"]
    possible = allowed_counts(n, row["cumulative_fractions"], tolerance)
    fractions = [endpoints([m/n for m in category]) for category in zip(*possible, strict=True)]
    intervals = []
    for category in zip(*possible, strict=True):
        subintervals = [wilson(m, n) for m in category]
        intervals.append([min(a for a, _ in subintervals), max(b for _, b in subintervals)])
    return {"n": n, "allowed_count_vectors": possible, "fraction_ranges": fractions,
            "wilson95_envelopes": intervals}


def compare(a, b, category):
    """b minus a. All other positions, including the middle, stay in the denominator."""
    na, nb = a["n"], b["n"]
    differences, p_values = [], []
    ca = {row[category] for row in a["allowed_count_vectors"]}
    cb = {row[category] for row in b["allowed_count_vectors"]}
    for k_a, k_b in product(ca, cb):
        differences.append(k_b / nb - k_a / na)
        p_values.append(float(fisher_exact([[k_a, na-k_a], [k_b, nb-k_b]]).pvalue))
    return {"difference_fraction_range": endpoints(differences),
            "pooled_individual_fisher_p_range": endpoints(p_values)}


def run(reading, out):
    raw = json.loads(reading.read_text(encoding="utf-8"))
    tol = raw["tolerance_fraction"]
    panels = {}
    for key, panel in raw["panels"].items():
        groups = {name: summarize_group(row, tol) for name, row in panel["groups"].items()}
        panels[key] = {"categories": panel["categories"], "groups": groups}

    heart = panels["G"]["groups"]
    gene = panels["F"]["groups"]
    effects = {
        "G_right_stim_vs_left_stim_for_right_heart": compare(heart["left_stimulated"], heart["right_stimulated"], 2),
        "G_left_stim_vs_right_stim_for_left_heart": compare(heart["right_stimulated"], heart["left_stimulated"], 0),
        "G_left_stim_vs_flow_deficient_for_left_heart": compare(heart["flow_deficient"], heart["left_stimulated"], 0),
        "G_right_stim_vs_flow_deficient_for_right_heart": compare(heart["flow_deficient"], heart["right_stimulated"], 2),
        "F_left_stim_vs_flow_deficient_for_right_dand5": compare(gene["flow_deficient"], gene["left_stimulated"], 0),
    }
    checks = {
        "recovered_counts_total_n": all(sum(row) == g["n"] for p in panels.values()
                                       for g in p["groups"].values() for row in g["allowed_count_vectors"]),
        "count_resolution_control": allowed_counts(20, [.5, .75], 1.e-12) == [(10, 5, 5)],
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, {"article_doi": "10.1126/science.abq7317", "source_sha256": raw["source_sha256"],
                       "reading_sha256": sha256(reading.read_bytes()).hexdigest(),
                       "tolerance_fraction_each_cumulative_boundary": tol, "panels": panels,
                       "contrasts": effects,
                       "scope_of_intervals": "Figure rounding and binomial uncertainty. Fish from pooled trials; "
                                             "trial clustering and raw count weights cannot be recovered.",
                       "checks": checks}, __file__, read_figure.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reading", type=Path, default=HERE / "figure_readings.json")
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E16")
    args = parser.parse_args()
    run(args.reading, args.out)
