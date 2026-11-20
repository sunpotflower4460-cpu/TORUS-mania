"""Compare published root and leaf development interventions."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from scipy.stats import fisher_exact

from experiments.common import save_summary
from experiments.E08_survey.run import wilson

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def counts_matching_rounded_percent(percent, n):
    if n is None:
        return None
    return [count for count in range(n+1) if abs(100*count - percent*n) <= .5*n]


def outcome(events, n):
    lo, hi = wilson(events, n)
    return {"events": events, "n": n, "fraction": events/n,
            "wilson95": [0. if events == 0 else lo, 1. if events == n else hi]}


def compare(treatment, control):
    kt, nt = treatment["events"], treatment["n"]
    kc, nc = control["events"], control["n"]
    test = fisher_exact([[kt, nt-kt], [kc, nc-kc]])
    return {"difference_fraction": kt/nt - kc/nc, "fisher_p_two_sided": float(test.pvalue)}


def run(inputs, out):
    source = json.loads(inputs.read_text(encoding="utf-8"))
    root_results = []
    for row in source["root_observations"]:
        root_results.append({**row, "difference_reported_percentage_points":
                            row["reported_percent"] - row["control_percent"],
                            "counts_at_nearest_whole_percent": counts_matching_rounded_percent(
                                row["reported_percent"], row["n"]),
                            "control_counts_at_nearest_whole_percent": counts_matching_rounded_percent(
                                row["control_percent"], row["control_n"])})
    timing = source["root_timing"]
    timing["nearest_whole_percent"] = counts_matching_rounded_percent(timing["reported_percent"], timing["n"])

    leaf = source["leaf"]
    leaf_result = {}
    for name, (n, initiation, reversal) in leaf["groups"].items():
        leaf_result[name] = {"leaf_initiation": outcome(initiation, n),
                             "reverse_phyllotaxy": outcome(reversal, n)}
    primary, sensitivity = {}, {}
    for line, other in (("E1.7", "E1.8"), ("E1.8", "E1.7")):
        treated, mock, alternate_mock, placebo = [leaf_result[name]["leaf_initiation"] for name in
            (f"{line}_induced", f"{line}_mock", f"{other}_mock", "G25_induced")]
        primary[line] = {"versus_same_line_mock": compare(treated, mock),
                         "versus_G25_induced": compare(treated, placebo)}
        sensitivity[line] = compare(treated, alternate_mock)

    other_endpoint = leaf["different_endpoint_fig_7"]
    result = {
        "inputs_sha256": sha256(inputs.read_bytes()).hexdigest(),
        "root_reported_rates": root_results, "root_reporter_timing": timing,
        "leaf_initiation": {"doi": leaf["doi"], "location": leaf["location"], "groups": leaf_result,
                            "primary_contrasts": primary,
                            "sensitivity_with_mock_denominators_as_in_body_text": sensitivity,
                            "source_note": leaf["text_table_discrepancy"]},
        "leaf_shape_in_existing_primordium": {**other_endpoint, **outcome(other_endpoint["observed"],
                                                                         other_endpoint["n"])},
        "checks": {
            "exact_percent_calibration": counts_matching_rounded_percent(80, 25) == [20],
            "inconsistent_rounding_calibration": counts_matching_rounded_percent(70, 45) == [],
            "wilson_includes_boundary_fractions": outcome(0, 28)["wilson95"][0] == 0.
                                                        and outcome(28, 28)["wilson95"][1] == 1.,
            "integer_data_within_denominators": all(
                0 <= initiation <= n and 0 <= reversal <= n for n, initiation, reversal in leaf["groups"].values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, result, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=HERE / "published_values.json")
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E18")
    args = parser.parse_args()
    run(args.inputs, args.out)
