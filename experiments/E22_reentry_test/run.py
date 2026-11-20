"""Test tracer re-entry under matched steady profiles and different return routes."""

import argparse
from itertools import product
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ("cycle", "open", "shortcut")
I, T, O = 0, 1, 2
BASE_FLOW = np.array([.8, 1., .6])
BASE_LOSS = np.array([.2, .25, .35])
SAMPLES = (1., 2.5, 4.)
SCALES = (.75, 1., 1.25)
PULSE = np.array([0., 1., 0., 0., 0., 0.])
COLUMNS = ("time", "inner", "tip", "outer", "lost", "accumulated_outer_to_inner", "accumulated_tip_to_inner")


def transport_rates(flow, tissue_loss, route, cut=False):
    inner_to_tip, tip_to_outer, outer_exit = flow
    transport = np.zeros((3, 3))
    loss = tissue_loss.copy()
    transport[T, I] = inner_to_tip
    transport[O, T] = tip_to_outer
    if route == "cycle" and not cut:
        transport[I, O] = outer_exit
    else:
        loss[O] += outer_exit
    if route == "shortcut":
        # At the uncut steady state, O/T is tip_to_outer/(outer_exit+tissue_loss[O]).
        transport[I, T] = outer_exit * tip_to_outer / (outer_exit + tissue_loss[O])
    generators = transport - np.diag(transport.sum(axis=0) + loss)
    return generators, transport, loss


def tracer_generator(flow, tissue_loss, route, cut=False):
    generator, transfer, lost = transport_rates(flow, tissue_loss, route, cut)
    aug = np.zeros((len(PULSE), len(PULSE)))
    aug[:3, :3] = generator
    aug[3, :3] = lost
    aug[4, O] = transfer[I, O]
    aug[5, T] = transfer[I, T]
    return aug


def response(generator, time):
    return expm(generator * time) @ PULSE


def matched_steady_state():
    a, _, _ = transport_rates(BASE_FLOW, BASE_LOSS, "cycle")
    state = np.linalg.solve(-a, [1., 0., 0.])
    groups = {}
    for name in ROUTES:
        generator, rates, _ = transport_rates(BASE_FLOW, BASE_LOSS, name)
        # Prescribe nonnegative external input that sustains the matched state.
        supply = -generator @ state
        restored = np.linalg.solve(-generator, supply)
        groups[name] = {
            "states_I_T_O": restored.tolist(),
            "external_input_I_T_O": supply.tolist(),
            "shared_direction_fluxes_I_to_T_and_T_to_O": [
                float(rates[T, I] * restored[I]), float(rates[O, T] * restored[T])
            ],
        }
    return groups


def sensitivity():
    rows = []
    for a, b, c, loss in product(SCALES, repeat=4):
        flow = BASE_FLOW * [a, b, c]
        tissue_loss = BASE_LOSS * loss
        loop = tracer_generator(flow, tissue_loss, "cycle")
        interrupted = tracer_generator(flow, tissue_loss, "cycle", True)
        deltas = [response(loop, t)[I] - response(interrupted, t)[I] for t in SAMPLES]
        rows.append([a,b,c,loss,*deltas])
    raw = np.array(rows)
    stats = {}
    for t, deltas in zip(SAMPLES, raw[:, 4:].T, strict=True):
        stats[str(t)] = {"minimum": float(deltas.min()), "median": float(np.median(deltas)),
                         "maximum": float(deltas.max()), "fraction_above_5_percent": float(np.mean(deltas >= .05))}
    small_flow = BASE_FLOW.copy()
    small_flow[2] = .03
    weak = tracer_generator(small_flow, BASE_LOSS, "cycle")
    weak_cut = tracer_generator(small_flow, BASE_LOSS, "cycle", True)
    return {"cases": len(rows), "scaled_transport_and_loss": list(SCALES), "cut_effect_by_time": stats,
            "weak_return_rate": .03, "weak_return_effect": {
                str(t): float(response(weak, t)[I] - response(weak_cut, t)[I]) for t in SAMPLES
            }}, raw


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    baseline = matched_steady_state()
    times = np.linspace(0., 10., 201)
    histories, trials = {}, {}
    ivp_error, budget_error, derivative_error = 0., 0., 0.
    for kind in ROUTES:
        for cut in (False, True):
            name = f"{kind}_cut" if cut else kind
            generator = tracer_generator(BASE_FLOW, BASE_LOSS, kind, cut)
            exact = np.array([response(generator, t) for t in times])
            numerical = solve_ivp(lambda t, y: generator @ y, (0., 10.), PULSE, t_eval=times,
                                  rtol=1.e-10, atol=1.e-12)
            if not numerical.success:
                raise RuntimeError(numerical.message)
            ivp_error = max(ivp_error, float(abs(exact-numerical.y.T).max()))
            budget_error = max(budget_error, float(abs(exact[:, :4].sum(axis=1)-1.).max()))
            first = float((generator @ PULSE)[I])
            second = float((generator @ generator @ PULSE)[I])
            h = 1.e-4
            f0, f1, f2, f3 = (response(generator, j*h)[I] for j in range(4))
            numerical_first = (-3*f0+4*f1-f2)/(2*h)
            numerical_second = (2*f0-5*f1+4*f2-f3)/h**2
            derivative_error = max(derivative_error, float(abs(first-numerical_first)),
                                   float(abs(second-numerical_second)))
            i_peak = int(exact[:, I].argmax())
            histories[name] = np.column_stack((times, exact))
            trials[name] = {
                "initial_inner_rate": first, "initial_inner_second_derivative": second,
                "inner_at_selected_times": {str(t): float(response(generator, t)[I]) for t in SAMPLES},
                "peak_inner": float(exact[i_peak, I]),
                "time_of_peak_inner": float(times[i_peak]) if exact[i_peak, I] > 0. else None,
                "final_total_outer_to_inner": float(exact[-1, 4]), "final_total_shortcut": float(exact[-1, 5]),
            }

    scale_study, scale_data = sensitivity()
    concentrations = np.array([row["states_I_T_O"] for row in baseline.values()])
    fluxes = np.array([row["shared_direction_fluxes_I_to_T_and_T_to_O"] for row in baseline.values()])
    max_state_difference = max(float(np.ptp(concentrations, axis=0).max()), float(np.ptp(fluxes, axis=0).max()))
    analytic_second_derivative = float(BASE_FLOW[1] * BASE_FLOW[2])
    checks = {
        "matched_steady_concentrations_and_forward_fluxes": max_state_difference < 1.e-12,
        "nonnegative_external_sources": min(min(v["external_input_I_T_O"]) for v in baseline.values()) >= -1.e-12,
        "independent_integrator": ivp_error < 1.e-8,
        "mass_budget": budget_error < 1.e-10,
        "derivatives_check": derivative_error < 1.e-6,
        "analytic_two_hop_derivative": abs(trials["cycle"]["initial_inner_second_derivative"]
                                           - analytic_second_derivative) < 1.e-12,
    }
    measured_cut_effects = {
        name: {str(t): trials[name]["inner_at_selected_times"][str(t)]
               - trials[f"{name}_cut"]["inner_at_selected_times"][str(t)] for t in SAMPLES}
        for name in ROUTES
    }
    data = {
        "units": "nondimensional compartment concentrations and rates, not fit to plant data",
        "flow_rates": BASE_FLOW.tolist(), "tissue_loss_rates": BASE_LOSS.tolist(),
        "steady_state": baseline, "maximum_steady_difference": max_state_difference,
        "simulation": trials, "cut_effect_by_candidate": measured_cut_effects, "sensitivity": scale_study,
        "history_columns": list(COLUMNS), "sensitivity_columns": [
            "scale_inner_to_tip", "scale_tip_to_outer", "scale_outer_exit", "scale_tissue_loss",
            *[f"cut_effect_t{t}" for t in SAMPLES],
        ],
        "largest_mass_budget_error": budget_error, "max_independent_integrator_error": ivp_error,
        "checks": checks,
    }
    np.savez_compressed(out / "responses.npz", **histories, sensitivity=scale_data)
    save_summary(out, data, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E22")
    args = parser.parse_args()
    run(args.out)
