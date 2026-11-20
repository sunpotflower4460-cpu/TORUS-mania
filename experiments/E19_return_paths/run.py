"""Open a return path without changing local speed, dose, or uptake kinetics."""

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
LENGTH = 4.
END_TIME = 20.
RATES = np.array([1.2, .6])
CAPACITIES = np.array([.18, .75])
HISTORY_COLUMNS = ["time_s", "uptake_A", "uptake_B", "resource_in_channel", "internal_loss",
                   "export", "external_input", "cumulative_returns", "budget_residual"]


@dataclass(frozen=True)
class Case:
    return_fraction: float
    loss_rate: float = .15
    capacity_limited: bool = False
    replace_from_outside: bool = False
    diffusivity: float = 0.


CASES = {
    "open": Case(0.),
    "partial": Case(.5),
    "closed": Case(1.),
    "open_replenished": Case(0., replace_from_outside=True),
    "open_high_loss": Case(0., loss_rate=4.),
    "closed_high_loss": Case(1., loss_rate=4.),
    "open_capacity": Case(0., capacity_limited=True),
    "closed_capacity": Case(1., capacity_limited=True),
}
DIFFUSION_CASES = {"open_diffusion": Case(0., diffusivity=.005),
                   "closed_diffusion": Case(1., diffusivity=.005)}


def analytic_round(loss_rate):
    pass_survives = np.exp(-.50 * RATES)
    uptake = np.array([1. - pass_survives[0], pass_survives[0] * (1. - pass_survives[1])])
    survival = float(np.exp(-1.25 * loss_rate) * np.prod(pass_survives))
    return uptake, survival


def analytic_20s(case):
    uptake, survival = analytic_round(case.loss_rate)
    fraction = 1. if case.replace_from_outside else case.return_fraction
    return uptake * sum((survival*fraction)**j for j in range(5))


def diffuse(resource, diffusivity, dt, spacing, periodic):
    coefficient = diffusivity * dt / spacing**2
    split = int(np.ceil(coefficient / .45))
    share = coefficient / split
    for _ in range(split):
        exchange = share * np.diff(resource)
        between_ends = share * (resource[0] - resource[-1]) if periodic else 0.
        resource[:-1] += exchange
        resource[1:] -= exchange
        resource[0] -= between_ends
        resource[-1] += between_ends


def run_case(n, case):
    dt = LENGTH / n
    positions = dt * (np.arange(n) + .5)
    injection = (positions >= .25) & (positions < .50)
    sites = ((positions >= .75) & (positions < 1.25),
             (positions >= 1.75) & (positions < 2.25))
    loss_zone = (positions >= 2.50) & (positions < 3.75)
    resource = injection.astype(float) / injection.sum()
    absorbed = np.zeros(2)
    external = 1.
    internal_loss, exported, returned = 0., 0., 0.
    lost_fraction = -np.expm1(-case.loss_rate * dt/2)
    first_at_capacity = [None, None]
    # Predict fresh injections from one pass. No simulated concentrations are used.
    _, survival = analytic_round(case.loss_rate)
    steps_per_round = n
    added = ({j*steps_per_round: survival**j for j in range(1, 5)}
             if case.replace_from_outside else {})

    def exchange_with_matter(t):
        loss = resource[loss_zone] * lost_fraction
        resource[loss_zone] -= loss
        for i, mask in enumerate(sites):
            available = CAPACITIES[i] - absorbed[i] if case.capacity_limited else np.inf
            rate = RATES[i] * max(0., 1.-absorbed[i] / CAPACITIES[i]) if case.capacity_limited else RATES[i]
            transfer = resource[mask] * -np.expm1(-rate*dt/2)
            amount = float(transfer.sum())
            if amount > available:
                transfer *= available / amount
                amount = available
            resource[mask] -= transfer
            absorbed[i] += amount
            if case.capacity_limited and first_at_capacity[i] is None and absorbed[i] >= CAPACITIES[i]:
                first_at_capacity[i] = t
        return float(loss.sum())

    rows = []
    stride = round(.125/dt)
    min_cell = float(resource.min())
    for step in range(round(END_TIME/dt)+1):
        if step in added:
            amount = added[step]
            resource[injection] += amount / injection.sum()
            external += amount
        if step % stride == 0:
            stored = resource.sum()
            residual = stored + absorbed.sum() + internal_loss + exported - external
            rows.append([step*dt, *absorbed, stored, internal_loss, exported, external, returned, residual])
            min_cell = min(min_cell, float(resource.min()))
        if step == round(END_TIME/dt):
            break
        internal_loss += exchange_with_matter(step*dt + dt/2)
        if case.diffusivity:
            diffuse(resource, case.diffusivity, dt/2, dt, case.return_fraction == 1.)
        at_exit = resource[-1]
        at_inlet = case.return_fraction * at_exit
        returned += at_inlet
        exported += at_exit - at_inlet
        resource[1:] = resource[:-1]
        resource[0] = at_inlet
        if case.diffusivity:
            diffuse(resource, case.diffusivity, dt/2, dt, case.return_fraction == 1.)
        internal_loss += exchange_with_matter((step+1)*dt)

    history = np.asarray(rows)
    last = history[-1]
    result = {
        "return_fraction": case.return_fraction, "loss_rate_s_inverse": case.loss_rate,
        "diffusivity_m2_s": case.diffusivity, "capacity_limited": case.capacity_limited,
        "matched_fresh_injections": {str(step*dt): amount for step, amount in added.items()},
        "uptake_by_site": last[1:3].tolist(),
        "uptake_total": float(last[1:3].sum()), "B_share_of_uptake": float(last[2] / last[1:3].sum()),
        "final_stored_resource": float(last[3]), "internal_loss": float(last[4]),
        "export": float(last[5]), "external_supply": float(last[6]), "cumulative_returns": float(last[7]),
        "largest_absolute_budget_error": float(abs(history[:, -1]).max()),
        "minimum_sampled_cell_resource": min_cell, "first_time_exact_capacity_s": first_at_capacity,
    }
    if not case.capacity_limited and not case.diffusivity:
        expected = analytic_20s(case)
        result["analytic_final_uptake_by_site"] = expected.tolist()
        result["analytic_max_error"] = float(abs(expected-last[1:3]).max())
    return result, history


def run(n, out):
    cases = {**CASES, **DIFFUSION_CASES} if n == 512 else CASES
    results, histories = {}, {}
    for name, spec in cases.items():
        results[name], histories[name] = run_case(n, spec)
    early = histories["open"][:, 0] <= 3.
    max_early = max(float(abs(histories[name][early, 1:3] - histories["open"][early, 1:3]).max())
                    for name in ("closed", "partial"))
    replay_error = float(abs(histories["closed"][:, 1:3] - histories["open_replenished"][:, 1:3]).max())

    def difference(high, low, field):
        return results[high][field] - results[low][field]

    diff_controls = {
        "open_to_closed_uptake": difference("closed", "open", "uptake_total"),
        "high_loss_open_to_closed_uptake": difference("closed_high_loss", "open_high_loss", "uptake_total"),
        "capacity_open_to_closed_B_share": difference("closed_capacity", "open_capacity", "B_share_of_uptake"),
        "linear_open_to_closed_B_share": difference("closed", "open", "B_share_of_uptake"),
    }
    if "closed_diffusion" in results:
        diff_controls["diffusive_open_to_closed_uptake"] = difference("closed_diffusion", "open_diffusion", "uptake_total")
    data = {
        "grid": n, "dt_s": LENGTH/n, "path_length_m": LENGTH,
        "local_speed_m_s": 1., "carrier_kinetic_energy_density_j_per_m3": .5,
        "closing_return_only": True, "supply_unit": "initial resource mass, proportional to available resource energy",
        "checks": {
            "mass_budget_closed": max(row["largest_absolute_budget_error"] for row in results.values()) < 1.e-10,
            "sampled_field_nonnegative": min(row["minimum_sampled_cell_resource"] for row in results.values()) >= -1.e-12,
            "linear_geometric_series": max(row["analytic_max_error"] for row in results.values()
                                          if "analytic_max_error" in row) < 1.e-8,
            "no_pre_return_difference_without_diffusion": max_early < 1.e-8,
        },
        "early_maximum_difference": max_early, "replenishment_maximum_history_difference": replay_error,
        "preregistered_outcomes": {
            "uptake_increases_with_return_fraction": (results["open"]["uptake_total"]
                                                       < results["partial"]["uptake_total"]
                                                       < results["closed"]["uptake_total"]),
            "same_linear_uptake_share": abs(diff_controls["linear_open_to_closed_B_share"]) <= 1.e-8,
            "fresh_replenishment_matches_within_point_one_percent": replay_error <= .001,
            "high_loss_benefit_below_one_percent": abs(diff_controls["high_loss_open_to_closed_uptake"]) < .01,
            "capacity_case_increases_B_share_by_five_points": diff_controls["capacity_open_to_closed_B_share"] >= .05,
        },
        "comparisons": diff_controls, "history_columns": HISTORY_COLUMNS, "cases": results,
    }
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "histories.npz", **histories)
    save_summary(out, data, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, choices=(128, 256, 512), required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E19")
    args = parser.parse_args()
    run(args.n, args.out / f"grid{args.n}")
