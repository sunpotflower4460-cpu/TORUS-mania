"""Balance steady and transient work on linear transport networks."""

import argparse
from pathlib import Path

import numpy as np

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]


def incidence(node_count, edges):
    matrix = np.zeros((node_count, len(edges)))
    for column, (tail, head) in enumerate(edges):
        matrix[tail, column] = 1
        matrix[head, column] = -1
    return matrix


def steady(matrix, conductance, drive, supply):
    laplacian = (matrix * conductance) @ matrix.T
    rhs = supply - matrix @ (conductance * drive)
    # Every graph used here is connected. Set the last potential as reference.
    potential = np.r_[np.linalg.solve(laplacian[:-1, :-1], rhs[:-1]), 0.]
    flux = conductance * (matrix.T @ potential + drive)
    loss = float(np.sum(flux**2 / conductance))
    internal = float(drive @ flux)
    external = float(potential @ supply)
    return {
        "cycle_rank": matrix.shape[1] - matrix.shape[0] + 1,
        "potential": potential.tolist(),
        "edge_flux": flux.tolist(),
        "drive_power": internal,
        "reservoir_power": external,
        "dissipation": loss,
        "continuity_error": float(np.max(np.abs(matrix @ flux - supply))),
        "power_error": abs(loss - internal - external),
    }


def passive_release(matrix, conductance, capacitance, initial, steps):
    scaling = 1 / np.sqrt(capacitance)
    laplacian = (matrix * conductance) @ matrix.T
    eigenvalues, vectors = np.linalg.eigh(laplacian * scaling[:, None] * scaling)
    times = np.linspace(0, 12, steps)
    modes = vectors.T @ (initial / scaling)
    potentials = (np.exp(-times[:, None] * eigenvalues) * modes) @ vectors.T * scaling
    fluxes = (potentials @ matrix) * conductance
    energies = .5 * ((potentials**2) @ capacitance)
    dissipation = (fluxes**2) @ (1 / conductance)
    integrated = np.trapezoid(dissipation, times)
    return {
        "sample_count": steps, "initial_potential": initial.tolist(),
        "capacitance": capacitance.tolist(), "initial_energy": float(energies[0]),
        "remaining_energy": float(energies[-1]),
        "integrated_dissipation": float(integrated),
        "relative_energy_residual": float(abs(energies[0] - energies[-1] - integrated) / energies[0]),
        "conserved_storage_max_error": float(np.max(np.abs(potentials @ capacitance - initial @ capacitance))),
        "final_max_abs_flux": float(np.max(np.abs(fluxes[-1]))),
        "monotone_energy": bool(np.all(np.diff(energies) <= 1e-13)),
        "trace": {
            "time_s": times[::(steps-1)//16].tolist(),
            "stored_energy": energies[::(steps-1)//16].tolist(),
        },
    }


def calculation():
    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 0)]
    triangle = incidence(3, edges[:3])
    tree = incidence(3, edges[:2])
    theta = incidence(4, edges)
    g = np.array([1.4, .8, 1.0, 1.8, .6])
    drive = np.array([.9, 0., 0., 0., 0.])
    no_source = np.zeros(3)
    cases = {
        "driven_ring": steady(triangle, g[:3], drive[:3], no_source),
        "undriven_ring": steady(triangle, g[:3], np.zeros(3), no_source),
        "zero_affinity_ring": steady(triangle, g[:3], np.array([.9, -.9, 0.]), no_source),
        "cut_closed": steady(tree, g[:2], drive[:2], no_source),
        "cut_open_throughflow": steady(tree, g[:2], np.zeros(2), np.array([.27, 0., -.27])),
        "two_cycles": steady(theta, g, drive, np.zeros(4)),
        "one_return_cut": steady(theta[:, :4], g[:4], drive[:4], np.zeros(4)),
    }
    analytic = float(np.sum(drive[:3]) / np.sum(1 / g[:3]))
    physical = {}
    for regime, potential_unit, flux_unit, potential_scale, flux_scale in (
        ("electrical", "V", "A", .8, .002),
        ("hydraulic", "Pa", "m^3/s", 50., 2e-6),
        ("chemical_linear_response", "J/mol", "mol/s", 100., 5e-8),
    ):
        info = steady(triangle, g[:3] * flux_scale / potential_scale, drive[:3] * potential_scale, no_source)
        physical[regime] = {
            "potential_unit": potential_unit, "flux_unit": flux_unit,
            "potential_scale": potential_scale, "flux_scale": flux_scale,
            "cycle_flux": info["edge_flux"][0], "drive_affinity": .9 * potential_scale,
            "dissipation_W": info["dissipation"],
            "relative_flux_error": abs(info["edge_flux"][0] / flux_scale / analytic - 1),
            "relative_power_error": info["power_error"] / info["drive_power"],
        }
    args = (triangle, g[:3], np.array([1.1, .75, 1.3]), np.array([1.3, .2, -.8]))
    release = [passive_release(*args, steps) for steps in (513, 1025)]
    return {
        "experiment": "E37",
        "edge_order_for_two_cycle_graph": edges,
        "reference_edge_conductance": g.tolist(), "reference_edge_drive": drive.tolist(),
        "steady_cases": cases, "analytic_single_cycle_flux": analytic,
        "same_equations_in_physical_units": physical,
        "undriven_release": release,
        "checks": {
            "all_node_balances": all(x["continuity_error"] < 1e-12 for x in cases.values()),
            "all_work_balances": all(x["power_error"] < 1e-12 for x in cases.values()),
            "cycle_formula": max(abs(x - analytic) for x in cases["driven_ring"]["edge_flux"]) < 1e-12,
            "cycle_choices_removed_by_cut": [
                cases[key]["cycle_rank"] for key in ("two_cycles", "one_return_cut", "cut_closed")
            ] == [2, 1, 0],
            "cut_and_undriven_closed_no_steady_flux": all(
                max(abs(f) for f in cases[key]["edge_flux"]) < 1e-12
                for key in ("undriven_ring", "zero_affinity_ring", "cut_closed")
            ),
            "tree_with_external_source_transports": min(cases["cut_open_throughflow"]["edge_flux"]) > .26,
            "cross_domain_rescaling": all(
                max(x["relative_flux_error"], x["relative_power_error"]) < 1e-12 for x in physical.values()
            ),
            "passive_energy_balance_and_refinement": (
                release[-1]["relative_energy_residual"] < .001
                and release[-1]["relative_energy_residual"] < release[0]["relative_energy_residual"] / 3
                and release[-1]["monotone_energy"]
                and release[-1]["conserved_storage_max_error"] < 1e-12
                and release[-1]["final_max_abs_flux"] < 1e-6
            ),
        },
    }


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, calculation(), __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E37")
    run(parser.parse_args().out)
