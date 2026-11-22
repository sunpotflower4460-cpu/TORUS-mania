"""Separate steady circulation, molecular first returns, and an imposed clock.

E78 is a dimensionless linear compartment calculation, not a simulation or
measurement of a growing root. See the committed E78 registration for scope.
"""

import argparse
from itertools import product
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from experiments.common import save_summary
from experiments.E22_reentry_test import run as e22
from experiments.E28_return_growth import run as e28

ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_COMMIT = "4d27d24822b51697c989ad6e3ddfa56a8601ef57"
MULTIPLIERS = (0.75, 1.0, 1.25)
COMMON_LOSSES = (0.02, 0.2, 2.0)
TRANSPORT_MULTIPLIERS = (0.5, 0.75, 1.0, 1.25, 2.0)
TIMES = np.linspace(0.0, 80.0, 801)
RTOL, ATOL = 1e-11, 1e-13
NUMERICAL_TOLERANCE = 1e-8


def integrate(rhs, initial, events=None):
    result = solve_ivp(
        rhs, (TIMES[0], TIMES[-1]), initial, method="DOP853",
        t_eval=TIMES, rtol=RTOL, atol=ATOL, events=events,
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result


def stable_transport(arrays):
    """Use E22's generator; verify its spectrum and affine responses separately."""
    source = np.array([1.0, 0.0, 0.0])
    rows = []
    column_error, eigen_error, steady_error, bound_excess = 0.0, 0.0, 0.0, 0.0
    for multipliers in product(MULTIPLIERS, repeat=4):
        rates = e22.BASE_FLOW * multipliers[:3]
        losses = e22.BASE_LOSS * multipliers[3]
        matrix, _, _ = e22.transport_rates(rates, losses, "cycle")
        values, vectors = np.linalg.eig(matrix)
        state = np.linalg.solve(-matrix, source)
        column_error = max(column_error, float(np.max(abs(matrix.sum(axis=0) + losses))))
        eigen_error = max(eigen_error, float(np.max(abs(matrix @ vectors - vectors * values))))
        residual = float(np.max(abs(matrix @ state + source)))
        steady_error = max(steady_error, residual)
        spectral_bound = -float(losses.min())
        spectral_abscissa = float(values.real.max())
        bound_excess = max(bound_excess, spectral_abscissa - spectral_bound)
        rows.append({
            "rate_multipliers_I_T_O_and_loss": list(multipliers),
            "transport_rates_I_T_O": rates.tolist(), "loss_rates_I_T_O": losses.tolist(),
            "eigenvalues_real_imag": [[float(v.real), float(v.imag)]
                                      for v in sorted(values, key=lambda v: (v.real, v.imag))],
            "spectral_abscissa": spectral_abscissa,
            "analytic_upper_bound_on_real_parts": spectral_bound,
            "steady_amounts_I_T_O": state.tolist(),
            "steady_edge_fluxes_I_to_T_T_to_O_O_to_I": (rates * state).tolist(),
            "steady_equation_max_residual": residual,
        })

    matrix, _, _ = e22.transport_rates(e22.BASE_FLOW, e22.BASE_LOSS, "cycle")
    equilibrium = np.linalg.solve(-matrix, source)
    response_rows = {}
    ode_error, mass_error, contraction_excess = 0.0, 0.0, 0.0
    for name, initial in (("zero_start", np.zeros(3)),
                          ("steady_plus_tip_pulse", equilibrium + [0.0, 1.0, 0.0])):
        def rhs(_, y):
            return np.r_[matrix @ y[:3] + source, e22.BASE_LOSS @ y[:3]]

        numerical = integrate(rhs, np.r_[initial, 0.0]).y.T
        exact = np.array([equilibrium + expm(matrix * t) @ (initial - equilibrium)
                          for t in TIMES])
        error = float(np.max(abs(numerical[:, :3] - exact)))
        budget = numerical[:, :3].sum(axis=1) + numerical[:, 3] - initial.sum() - source.sum() * TIMES
        deviation = np.sum(abs(exact - equilibrium), axis=1)
        bound = np.sum(abs(initial - equilibrium)) * np.exp(-e22.BASE_LOSS.min() * TIMES)
        excess = float(max(0.0, np.max(deviation - bound)))
        ode_error = max(ode_error, error)
        mass_error = max(mass_error, float(np.max(abs(budget))))
        contraction_excess = max(contraction_excess, excess)
        arrays[f"A/{name}/amounts_expm"] = exact
        arrays[f"A/{name}/amounts_and_accumulated_loss_ode"] = numerical
        arrays[f"A/{name}/deviation_l1_and_bound"] = np.column_stack((deviation, bound))
        response_rows[name] = {
            "initial_amounts_I_T_O": initial.tolist(), "final_amounts_I_T_O": exact[-1].tolist(),
            "max_ode_expm_difference": error, "maximum_mass_balance_residual": float(np.max(abs(budget))),
            "initial_deviation_l1": float(deviation[0]), "final_deviation_l1": float(deviation[-1]),
            "final_contraction_bound": float(bound[-1]), "maximum_contraction_bound_excess": excess,
            "final_accumulated_loss": float(numerical[-1, 3]),
        }
    return {
        "source_I_T_O": source.tolist(), "conditions": rows,
        "analytic_argument": "A is Metzler and column i sums to -d_i. Column Gershgorin disks give Re(lambda)<=-min(d_i)<0. Hence x*=(-A)^-1 s is asymptotically stable; no autonomous sustained periodic solution occurs under constant s in this model.",
        "contraction_bound": "||x(t)-x*||_1 <= exp(-min(d_i)*t) ||x(0)-x*||_1",
        "all_conditions_have_negative_spectral_abscissa": all(r["spectral_abscissa"] < 0 for r in rows),
        "conditions_with_complex_eigenvalues": sum(any(abs(v[1]) > 1e-10 for v in r["eigenvalues_real_imag"]) for r in rows),
        "baseline_steady_amounts_I_T_O": equilibrium.tolist(), "baseline_responses": response_rows,
        "E28_event_rule": {
            "source": "experiments/E28_return_growth/run.py:event_sequence",
            "construction": "Each of nine events adds wait and then cells/p; repetition is explicitly supplied to the model.",
            "interpretation": "A complex eigenvalue describes a decaying mode, not a persistent clock. This result does not apply to the growing, spatial, nonlinear cell model of van den Berg et al.",
        },
    }, {
        "A_column_loss_identity": column_error < 1e-12,
        "A_eigenpair_residuals": eigen_error < 1e-12,
        "A_numerical_spectrum_respects_analytic_bound": bound_excess < 1e-12,
        "A_equilibrium_equations": steady_error < 1e-12,
        "A_ode_matches_matrix_exponential": ode_error < NUMERICAL_TOLERANCE,
        "A_affine_material_budgets": mass_error < NUMERICAL_TOLERANCE,
        "A_semigroup_l1_contraction_bound": contraction_excess < NUMERICAL_TOLERANCE,
    }


def first_pass_generator(rates, losses):
    """n transient stages followed by separate first-arrival and loss absorbers."""
    n = len(rates)
    matrix = np.zeros((n + 2, n + 2))
    matrix[np.arange(n), np.arange(n)] = -(rates + losses)
    for i in range(n - 1):
        matrix[i + 1, i] = rates[i]
    matrix[n, n - 1] = rates[-1]
    matrix[n + 1, :n] = losses
    return matrix


def molecular_returns(arrays):
    rates = e22.BASE_FLOW.copy()
    prescribed_flux = 1.0
    equilibrium = prescribed_flux / rates
    rows = []
    errors = {name: 0.0 for name in ("steady", "probability", "time", "laps", "ode", "mass", "moment", "tail")}
    for common_loss in COMMON_LOSSES:
        losses = np.full(3, common_loss)
        source = losses * equilibrium
        recurrent, _, _ = e22.transport_rates(rates, losses, "cycle")
        generator = first_pass_generator(rates, losses)
        transient = generator[:3, :3]
        initial = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
        probability = float(np.prod(rates / (rates + losses)))
        conditional_time = float(np.sum(1.0 / (rates + losses)))
        expected_laps = probability / (1.0 - probability)
        occupation = np.linalg.solve(-transient, initial[:3])
        weighted_occupation = np.linalg.solve(-transient, occupation)
        probability_matrix = float(rates[-1] * occupation[-1])
        first_moment_matrix = float(rates[-1] * weighted_occupation[-1])
        time_matrix = first_moment_matrix / probability_matrix
        recurrent_occupation = np.linalg.solve(-recurrent, initial[:3])
        laps_matrix = float(rates[-1] * recurrent_occupation[-1])

        def rhs(t, y):
            # The extra component accumulates t times the first-return density.
            return np.r_[generator @ y[:5], t * rates[-1] * y[2]]

        numerical = integrate(rhs, np.r_[initial, 0.0]).y.T
        exact = np.array([expm(generator * t) @ initial for t in TIMES])
        final = numerical[-1]
        tail_probability = float(exact[-1, :3].sum())
        errors["steady"] = max(errors["steady"], float(np.max(abs(recurrent @ equilibrium + source))))
        errors["probability"] = max(errors["probability"], abs(probability_matrix - probability))
        errors["time"] = max(errors["time"], abs(time_matrix - conditional_time))
        errors["laps"] = max(errors["laps"], abs(laps_matrix - expected_laps))
        errors["ode"] = max(errors["ode"], float(np.max(abs(numerical[:, :5] - exact))))
        errors["mass"] = max(errors["mass"], float(np.max(abs(numerical[:, :5].sum(axis=1) - 1.0))))
        errors["moment"] = max(errors["moment"], float(abs(final[3] - probability)),
                               float(abs(final[5] / final[3] - conditional_time)))
        errors["tail"] = max(errors["tail"], tail_probability)
        arrays[f"B/loss_{common_loss}/first_pass_expm"] = exact
        arrays[f"B/loss_{common_loss}/first_pass_and_time_moment_ode"] = numerical
        rows.append({
            "common_loss_rate": common_loss,
            "steady_amounts_I_T_O": equilibrium.tolist(),
            "steady_edge_fluxes_I_to_T_T_to_O_O_to_I": (rates * equilibrium).tolist(),
            "external_supply_I_T_O": source.tolist(), "total_external_supply": float(source.sum()),
            "first_complete_return_probability": probability,
            "mean_return_time_conditional_on_return": conditional_time,
            "expected_complete_laps_before_loss": expected_laps,
            "independent_absorbing_matrix_probability": probability_matrix,
            "independent_absorbing_matrix_conditional_time": time_matrix,
            "independent_recurrent_reward_expected_laps": laps_matrix,
            "ode_first_return_probability_at_80": float(final[3]),
            "ode_conditional_return_time_from_events_before_80": float(final[5] / final[3]),
            "unabsorbed_probability_at_80_expm": tail_probability,
            "final_probability_lost_before_first_return_ode": float(final[4]),
        })
    return {
        "transport_rates_I_T_O": rates.tolist(), "fixed_edge_flux": prescribed_flux, "conditions": rows,
        "formulas": {
            "first_return_laplace_transform": "f_hat(s)=product_i k_i/(s+k_i+d_i)",
            "first_return_probability": "P=product_i k_i/(k_i+d_i)",
            "conditional_mean_time": "sum_i 1/(k_i+d_i)",
            "complete_lap_count": "Pr(N>=m)=P^m; E[N]=P/(1-P)",
        },
        "first_pass_state_order": ["inner_not_yet_returned", "tip", "outer", "first_return_absorber", "loss_absorber"],
        "first_pass_moment_extra_column": "integral_0^t time*first_return_density(time) dtime",
        "interpretation": "Each cohort starts in I and must pass T then O before returning. New supply contains none of that label. Total supply differs between conditions; no energy-work budget or chemical interconversion is modeled. Conditional return times exclude molecules that never return.",
        "numerical_error_maxima": errors,
    }, {
        "B_prescribed_steady_amounts_satisfy_balances": errors["steady"] < 1e-12,
        "B_probability_formula_matches_absorbing_matrix": errors["probability"] < 1e-12,
        "B_conditional_time_formula_matches_matrix_moment": errors["time"] < 1e-12,
        "B_lap_formula_matches_recurrent_reward": errors["laps"] < 1e-10,
        "B_ode_matches_absorbing_matrix_exponential": errors["ode"] < NUMERICAL_TOLERANCE,
        "B_five_state_mass_budget": errors["mass"] < NUMERICAL_TOLERANCE,
        "B_time_80_resolves_probability_and_first_moment": max(errors["moment"], errors["tail"]) < NUMERICAL_TOLERANCE,
    }


def imposed_wait_sensitivity(arrays):
    rows = []
    cdf_error, event_error, mass_error = 0.0, 0.0, 0.0
    for multiplier in TRANSPORT_MULTIPLIERS:
        rates = e28.RATES.copy()
        rates[:2] *= multiplier
        generator = first_pass_generator(rates[:2], rates[2:])
        ceiling = float(np.prod(rates[:2] / (rates[:2] + rates[2:])))

        def event(_, y):
            return y[2] - e28.RETURN_FRACTION

        event.direction = 1
        numerical = integrate(lambda _, y: generator @ y, [1.0, 0.0, 0.0, 0.0], event)
        analytic = np.array([e28.first_return(t, rates) for t in TIMES])
        wait = e28.wait_for_return(rates) if ceiling > e28.RETURN_FRACTION else None
        ode_wait = float(numerical.t_events[0][0]) if len(numerical.t_events[0]) else None
        if wait is not None and ode_wait is not None:
            event_error = max(event_error, abs(wait - ode_wait))
        elif (wait is None) != (ode_wait is None):
            event_error = float("inf")
        cdf_error = max(cdf_error, float(np.max(abs(analytic - numerical.y[2]))))
        mass_error = max(mass_error, float(np.max(abs(numerical.y.sum(axis=0) - 1.0))))
        period = None if wait is None else wait + e28.GROWTH_CELLS
        arrays[f"C/multiplier_{multiplier}/first_pass_ode"] = numerical.y.T
        arrays[f"C/multiplier_{multiplier}/return_cdf_E28_analytic"] = analytic
        rows.append({
            "transport_multiplier": multiplier,
            "rates_tip_to_outer_outer_to_inner_tip_loss_outer_loss": rates.tolist(),
            "eventual_return_probability": ceiling,
            "threshold_fraction_of_original_pulse": e28.RETURN_FRACTION,
            "finite_threshold_time_exists": ceiling > e28.RETURN_FRACTION,
            "threshold_status": ("reached" if wait is not None else
                                 "unreachable_at_finite_time" if ceiling <= e28.RETURN_FRACTION else
                                 "not_reached_within_E28_time_80_search"),
            "wait_time_tau": wait, "independent_ode_threshold_time": ode_wait,
            "imposed_period_T": period, "imposed_frequency": None if period is None else 1.0 / period,
        })
    reference = next(row for row in rows if row["transport_multiplier"] == 1.0)
    for row in rows:
        row["period_relative_to_multiplier_one"] = (None if row["imposed_period_T"] is None else
                                                    row["imposed_period_T"] / reference["imposed_period_T"])
        row["frequency_relative_to_multiplier_one"] = (None if row["imposed_frequency"] is None else
                                                       row["imposed_frequency"] / reference["imposed_frequency"])
    return {
        "production_rate_cells_per_model_time": 1.0, "growth_amount_cells": e28.GROWTH_CELLS,
        "conditions": rows, "first_pass_state_order": ["tip", "outer", "first_arrival_inner", "loss"],
        "maximum_cdf_ode_formula_error": cdf_error, "maximum_threshold_time_difference": event_error,
        "maximum_material_budget_residual": mass_error,
        "interpretation": "This is the sensitivity of E28's imposed first-arrival gate plus growth wait. It is not an autonomous oscillation, a full circuit starting at I, or a rerun of the original growing-cell reflux model. Compare to original-paper mechanisms separately, without identifying the parameters numerically.",
    }, {
        "C_ode_cdf_matches_E28_analytic_formula": cdf_error < NUMERICAL_TOLERANCE,
        "C_independent_threshold_event_times_agree": event_error < NUMERICAL_TOLERANCE,
        "C_first_pass_material_budgets": mass_error < NUMERICAL_TOLERANCE,
    }


def run(out):
    arrays = {"time_model_units": TIMES}
    part_a, checks_a = stable_transport(arrays)
    part_b, checks_b = molecular_returns(arrays)
    part_c, checks_c = imposed_wait_sensitivity(arrays)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "histories.npz", **arrays)
    summary = {
        "experiment": "E78", "registration_commit": REGISTRATION_COMMIT,
        "units": "Dimensionless compartment amounts, model time, and amounts per model time; no calibration to plant units.",
        "time_grid": {"start": 0.0, "end": 80.0, "points": len(TIMES)},
        "independent_integrator": {"method": "DOP853", "rtol": RTOL, "atol": ATOL},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "A_linear_circulation_and_stability": part_a,
        "B_fixed_collective_flux_and_molecular_returns": part_b,
        "C_transport_sensitivity_of_imposed_gate": part_c,
        "history_archive": "histories.npz; rows follow time_model_units; named arrays distinguish analytic and ODE paths.",
        "scope": "Steady collective circulation, labeled molecular return, autonomous temporal oscillation, spatial toroidal geometry, and a universal generation principle are separate claims. Only the first three are compared in this specified linear model. Biological support and original-paper mechanism comparisons require separate evidence.",
        "checks": {**checks_a, **checks_b, **checks_c},
    }
    save_summary(out, summary, __file__, e22.__file__, e28.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E78")
    run(parser.parse_args().out)
