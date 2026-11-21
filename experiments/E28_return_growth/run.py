"""Couple first-pass tracer return to cell production in a minimal event model."""

import argparse
from itertools import product
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from experiments.common import save_summary
from experiments.E22_reentry_test.run import BASE_FLOW, BASE_LOSS, matched_steady_state

ROOT = Path(__file__).resolve().parents[2]
RETURN_FRACTION = .20
GROWTH_CELLS = 2.
PRODUCTION = (.5, .75, 1., 1.25, 1.5)
RATES = np.array([BASE_FLOW[1], BASE_FLOW[2], BASE_LOSS[1], BASE_LOSS[2]])


def first_return(time, rates):
    outbound, inward, tip_loss, outer_loss = rates
    a = outbound+tip_loss
    b = inward+outer_loss
    tail = (1+a*time)*np.exp(-a*time) if abs(a-b) < 1.e-12 else (
        (b*np.exp(-a*time)-a*np.exp(-b*time))/(b-a)
    )
    return float(outbound*inward/(a*b) * (1-tail))


def wait_for_return(rates):
    if first_return(80., rates) < RETURN_FRACTION:
        return None
    return float(brentq(lambda time: first_return(time, rates)-RETURN_FRACTION, 0., 80.))


def integrated_return(rates, cut):
    outbound, inward, tip_loss, outer_loss = rates
    def dynamics(_, state):
        tip, outer, _, _ = state
        exit_flux = inward*outer
        return [-(outbound+tip_loss)*tip, outbound*tip-(inward+outer_loss)*outer,
                0. if cut else exit_flux, tip_loss*tip+outer_loss*outer+(exit_flux if cut else 0.)]
    times = np.linspace(0., 12., 241)
    sol = solve_ivp(dynamics, (0., 12.), [1., 0., 0., 0.], t_eval=times, rtol=1.e-11, atol=1.e-13)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.t, sol.y


def event_sequence(p, wait, cells):
    time = 0.
    events = []
    for _ in range(9):
        time += wait
        time += cells/p
        events.append([time, p*time])
    intervals = np.diff(np.asarray(events), axis=0).mean(axis=0)
    return {"period": float(intervals[0]), "frequency": float(1./intervals[0]),
            "spacing_cells": float(intervals[1]), "times_positions": events}


def run(out):
    delay = wait_for_return(RATES)
    if delay is None:
        raise RuntimeError("Registered route did not reach the threshold")
    t, pulse = integrated_return(RATES, False)
    _, cut = integrated_return(RATES, True)
    # The weak case diverts the rest of the former inward edge to loss.
    weak = RATES.copy()
    weak[1] = .03
    weak[3] += RATES[1]-weak[1]
    sensitivity = []
    for p_to_o, o_to_i, loss in product((.75, 1., 1.25), repeat=3):
        rates = RATES*np.array([p_to_o, o_to_i, loss, loss])
        sensitivity.append(wait_for_return(rates))
    baseline_period = GROWTH_CELLS+delay
    candidates = {
        str(p): {
            "return_gate": event_sequence(p, delay, GROWTH_CELLS),
            "independent_fixed_clock": event_sequence(p, baseline_period, 0.),
            "independent_fixed_distance": event_sequence(p, 0., baseline_period),
            "independent_growth_dependent_schedule": event_sequence(p, delay, GROWTH_CELLS),
        } for p in PRODUCTION
    }
    error = float(np.max(np.abs(pulse[2]-[first_return(x, RATES) for x in t])))
    budget_error = float(max(np.max(np.abs(x.sum(axis=0)-1.)) for x in (pulse, cut)))
    arrays = {"time": t.tolist(), "return_cumulative": pulse[2].tolist(), "cut_return_cumulative": cut[2].tolist()}
    result = {
        "experiment": "E28", "time_unit": "model time; no conversion to biological hours",
        "rates_tip_to_outer_outer_to_inner_tip_loss_outer_loss": RATES.tolist(),
        "first_return_threshold": RETURN_FRACTION, "return_wait": delay, "growth_distance_cells": GROWTH_CELLS,
        "unlabelled_steady_state_E22": matched_steady_state(),
        "sensitivity_waits": sensitivity, "events": candidates, "first_pass": arrays,
        "weak_return_no_threshold": wait_for_return(weak) is None,
        "cut_return_no_threshold": bool(np.max(cut[2]) < RETURN_FRACTION),
        "largest_integration_error": error, "largest_mass_error": budget_error,
        "checks": {
            "analytic_first_pass_matches_independent_solver": error < 1.e-8,
            "mass_balance": budget_error < 1.e-9,
            "calibrated_control_periods_match_at_p_one": max(
                abs(c["period"]-baseline_period) for c in candidates["1.0"].values()) < 1.e-10,
            "all_event_sequences_match_two_waiting_times": all(
                abs(candidates[str(p)]["return_gate"]["period"]-(delay+GROWTH_CELLS/p)) < 1.e-10 for p in PRODUCTION
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, result, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E28")
    args = parser.parse_args()
    run(args.out)
