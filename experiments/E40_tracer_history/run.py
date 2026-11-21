"""Compare root-route histories when ordinary tracer measurements agree."""

import argparse
from itertools import product
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from scipy.stats import norm

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
LOWER, TIP, OUTER, BYPASS, UPPER, LOSS, FIRST_RETURN = range(7)
BASE = (.95, .60, .85, .12)
DOWNWARD = .90
MARKED_FRACTION = .80
MARK_AT = 1.5
OBSERVE_AT = 6.
LEAKAGE = (0., .02, .10)


def generator(rates, route, first_return=False):
    forward, split, return_rate, decay = rates
    return_node = FIRST_RETURN if first_return else LOWER
    outer_end = UPPER if route == "outer" else LOSS
    bypass_end = UPPER if route == "bypass" else LOSS
    edges = [
        (LOWER, TIP, forward), (TIP, OUTER, split), (TIP, BYPASS, split),
        (OUTER, outer_end, return_rate), (BYPASS, bypass_end, return_rate),
        (UPPER, return_node, DOWNWARD),
    ]
    edges.extend((region, LOSS, decay) for region in range(5))
    matrix = np.zeros((7, 7))
    for source, target, rate in edges:
        matrix[source, source] -= rate
        matrix[target, source] += rate
    return matrix


def initial_marks(at_switch, leakage):
    initial = np.zeros(7)
    initial[OUTER] = at_switch[OUTER] * MARKED_FRACTION * (1 - leakage)
    initial[BYPASS] = at_switch[BYPASS] * MARKED_FRACTION * leakage
    return initial


def case(rates):
    outer, bypass = [generator(rates, route) for route in ("outer", "bypass")]
    outer_flow, bypass_flow = [expm(matrix * OBSERVE_AT)[:, LOWER] for matrix in (outer, bypass)]
    switch = expm(outer * MARK_AT)[:, LOWER]
    dt = OBSERVE_AT - MARK_AT
    returns = {route: expm(generator(rates, route, first_return=True) * dt) for route in ("outer", "bypass", "cut")}
    result = {}
    residual = max(abs(outer_flow.sum() - 1), abs(bypass_flow.sum() - 1))
    for epsilon in LEAKAGE:
        initial = initial_marks(switch, epsilon)
        outcomes = {key: matrix @ initial for key, matrix in returns.items()}
        result[str(epsilon)] = {route: float(values[FIRST_RETURN]) for route, values in outcomes.items()}
        residual = max(residual, max(abs(values.sum() - initial.sum()) for values in outcomes.values()))
    return {
        "rates": list(rates), "marked_initial_fraction_of_input": float(MARKED_FRACTION * switch[OUTER]),
        "ordinary_signal_max_abs_difference": float(np.max(np.abs(outer_flow - bypass_flow))),
        "max_absolute_mass_residual": float(residual), "first_return_by_leakage": result,
    }


def series():
    times = np.linspace(0, OBSERVE_AT, 49)
    initial = np.zeros(7)
    initial[LOWER] = 1.
    trajectories = {
        route: np.array([expm(generator(BASE, route) * t) @ initial for t in times])
        for route in ("outer", "bypass")
    }
    time_of_mark = int(np.searchsorted(times, MARK_AT))
    marked = initial_marks(trajectories["outer"][time_of_mark], .02)
    after = times[time_of_mark:]
    return_traces = {
        route: [float((expm(generator(BASE, route, first_return=True) * (t - MARK_AT)) @ marked)[FIRST_RETURN])
                for t in after]
        for route in ("outer", "bypass", "cut")
    }
    difference = np.abs(trajectories["outer"] - trajectories["bypass"])
    return {
        "ordinary_times": times.tolist(), "ordinary_outer_route_trajectories": trajectories["outer"].tolist(),
        "ordinary_bypass_route_trajectories": trajectories["bypass"].tolist(),
        "first_return_times": after.tolist(), "first_return_traces_at_two_percent_mislabel": return_traces,
        "maximum_difference_throughout_observation": float(difference.max()),
    }


def detector(cases):
    output = {}
    strength = norm.ppf(.95) + norm.ppf(.80)
    for epsilon in LEAKAGE:
        rows = [c["first_return_by_leakage"][str(epsilon)] for c in cases]
        true_min = min(r["outer"] for r in rows)
        true_max = max(r["outer"] for r in rows)
        false_max = max(max(r["cut"], r["bypass"]) for r in rows)
        sigma = max(0., float((true_min-false_max) / strength))
        output[str(epsilon)] = {
            "outer_return_fraction_range": [true_min, true_max], "largest_false_return": false_max,
            "largest_sd_for_80_percent_sensitivity_at_5_percent_fp": sigma,
            "detection_threshold_at_largest_sd": float(false_max + sigma * norm.ppf(.95)),
        }
    return output


def run(out):
    cases = [case(tuple(a*b for a, b in zip(BASE, scale))) for scale in product((.75, 1., 1.25), repeat=4)]
    baseline = case(BASE)
    traces = series()
    limits = detector(cases)
    report = {
        "experiment": "E40",
        "region_order": ["lower_inner", "tip", "outer", "hidden_bypass", "upper_inner", "loss", "counted_first_return"],
        "rate_order": ["forward", "split_per_route", "return_or_exit", "decay"],
        "downward_rate": DOWNWARD, "mark_time": MARK_AT, "read_time": OBSERVE_AT,
        "fraction_marked_if_no_leak": MARKED_FRACTION,
        "baseline": baseline, "timeseries": traces, "registered_rate_sweep": cases,
        "detection_assuming_gaussian_noise": limits,
        "checks": {
            "all_81_rate_cases": len(cases) == 81,
            "mass_balance_including_marked_tracer": max(c["max_absolute_mass_residual"] for c in cases) < 1e-12,
            "ordinary_tracer_never_identifies_these_pathways": max(
                traces["maximum_difference_throughout_observation"],
                max(c["ordinary_signal_max_abs_difference"] for c in cases),
            ) < 1e-12,
            "first_return_requires_marked_route": all(
                c["first_return_by_leakage"]["0.0"]["outer"] > 0
                and c["first_return_by_leakage"]["0.0"]["bypass"] == 0
                and all(v["cut"] == 0 for v in c["first_return_by_leakage"].values())
                for c in cases
            ),
            "increased_mislabel_reduces_discrimination": (
                limits["0.0"]["largest_sd_for_80_percent_sensitivity_at_5_percent_fp"]
                > limits["0.02"]["largest_sd_for_80_percent_sensitivity_at_5_percent_fp"]
                >= limits["0.1"]["largest_sd_for_80_percent_sensitivity_at_5_percent_fp"]
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E40")
    run(parser.parse_args().out)
