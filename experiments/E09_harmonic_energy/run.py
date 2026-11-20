"""Harmonic circulation in a toroidal shell and its impermeable cuts."""
import argparse
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from experiments.common import save_summary

OUT = Path(__file__).resolve().parents[2] / "research/results/E09"
MAJOR, INNER, OUTER = 0.15, 0.025, 0.06
MU0 = 4 * np.pi * 1.e-7
SHELLS = {"thick": (INNER, OUTER), "thin": (0.039, 0.041)}
GRIDS = ((16, 64), (32, 128), (64, 256))
CUTS = ((True, True), (True, False), (False, True), (False, False))


def solid_coefficient(major, minor):
    """Exact norm squared of the unit-period azimuthal field, in metres."""
    return minor**2 / (major + np.sqrt(major**2 - minor**2))


def azimuthal_quadrature(major, inner, outer, ns, nt):
    ds = (outer-inner) / ns
    dtheta = 2*np.pi / nt
    s = inner + ds*(np.arange(ns) + .5)
    theta = dtheta*(np.arange(nt) + .5)
    radius = major + s[:, None]*np.cos(theta)
    return float(np.sum(s[:, None] / radius) * ds*dtheta/(2*np.pi))


def meridian(major, inner, outer, ns, nt, closed):
    """Minimise the integrated gradient norm subject to a unit winding."""
    ds, dtheta = (outer-inner)/ns, 2*np.pi/nt
    nodes = np.arange(ns*nt).reshape(ns, nt)
    s = inner + ds*(np.arange(ns)+.5)
    theta = dtheta*(np.arange(nt)+.5)
    s_faces = inner + ds*np.arange(1, ns)
    theta_faces = dtheta*np.arange(1, nt + int(closed))
    nt_edges = len(theta_faces)
    radial_weights = (2*np.pi*(major+s_faces[:, None]*np.cos(theta))
                      * s_faces[:, None]*dtheta/ds)
    angular_weights = (2*np.pi*(major+s[:, None]*np.cos(theta_faces))
                       * ds/(s[:, None]*dtheta))
    starts = np.concatenate((nodes[:-1].ravel(), nodes[:, :nt_edges].ravel()))
    ends = np.concatenate((nodes[1:].ravel(), np.roll(nodes, -1, axis=1)[:, :nt_edges].ravel()))
    weights = np.concatenate((radial_weights.ravel(), angular_weights.ravel()))
    index = np.arange(len(weights))
    derivative = coo_matrix((np.concatenate((-np.ones(len(index)), np.ones(len(index)))),
                             (np.tile(index, 2), np.concatenate((starts, ends)))),
                             shape=(len(index), nodes.size)).tocsr()
    seam = np.zeros(len(index))
    offset = radial_weights.size
    if closed:
        seam[offset+nt-1::nt] = 1.
    laplace = derivative.T @ derivative.multiply(weights[:, None])
    potential = np.zeros(nodes.size)
    potential[1:] = spsolve(laplace[1:, 1:].tocsc(), -(derivative.T @ (weights*seam))[1:])
    field = derivative @ potential + seam
    flux = weights*field
    periods = field[offset:].reshape(ns, nt_edges).sum(axis=1)
    return {"coefficient_m": float(field @ flux),
            "seam_flux_m": float(seam @ flux),
            "max_node_flux_m": float(abs(derivative.T @ flux).max()),
            "max_period_error": float(np.max(abs(periods-float(closed)))),
            "potentials": potential.reshape(ns, nt), "field": field, "flux": flux,
            "derivative": derivative, "weights": weights, "seam": seam,
            "s_m": s, "theta_rad": theta, "offset": offset}


def perturbations(result, ns, nt):
    """An independent, fluxless field assembled from elementary cell loops."""
    weights, field = result["weights"], result["field"]
    offset, norm = result["offset"], result["coefficient_m"]
    reports = []
    for seed in (11, 29, 47):
        rng = np.random.default_rng(seed)
        flux = np.zeros(len(field))
        for magnitude, i, j in zip(rng.normal(size=48), rng.integers(0, ns-1, 48),
                                   rng.integers(0, nt-1, 48)):
            flux[i*nt+j] += magnitude
            flux[offset+(i+1)*nt+j] += magnitude
            flux[i*nt+j+1] -= magnitude
            flux[offset+i*nt+j] -= magnitude
        perturb_norm = float(np.dot(flux, flux/weights))
        flux *= np.sqrt(.25*norm/perturb_norm)
        perturbed = field + flux/weights
        reports.append({
            "seed": seed, "flux_through_cut_m": float(result["seam"] @ flux),
            "max_node_flux_m": float(abs(result["derivative"].T @ flux).max()),
            "cross_term_m": float(field @ flux),
            "norm_ratio": float(np.dot(perturbed, weights*perturbed)/norm),
        })
    return reports


def physical_example():
    rho, circulation, turns, current = 1000., .08, 120, 1.4
    coefficient = solid_coefficient(MAJOR, OUTER)
    inductance = MU0*turns**2*coefficient
    return {"solid_coefficient_m": coefficient,
            "fluid": {"density_kg_m3": rho, "circulation_m2_s": circulation,
                      "volume_flux_m3_s": coefficient*circulation,
                      "hydraulic_inertance_kg_m4": rho/coefficient,
                      "kinetic_energy_j": rho*circulation**2*coefficient/2},
            "magnet": {"permeability_h_m": MU0, "turns": turns, "current_a": current,
                       "magnetic_flux_wb": coefficient*MU0*turns*current, "inductance_h": inductance,
                       "stored_energy_j": inductance*current**2/2}}


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    trials, solid, visual = [], [], {}
    for ns, nt in GRIDS:
        solid.append({"grid": [ns, nt], "azimuthal_m": azimuthal_quadrature(MAJOR, 0., OUTER, ns, nt)})
        for name, (inner, outer) in SHELLS.items():
            exact_azimuthal = solid_coefficient(MAJOR, outer)-solid_coefficient(MAJOR, inner)
            azimuthal = azimuthal_quadrature(MAJOR, inner, outer, ns, nt)
            for close_phi, close_theta in CUTS:
                result = meridian(MAJOR, inner, outer, ns, nt, close_theta)
                diagonal = [azimuthal*close_phi, result["coefficient_m"]]
                row = {"shell": name, "grid": [ns, nt], "closed_phi": close_phi,
                       "closed_theta": close_theta, "norm_matrix_diagonal_m": diagonal,
                       "rank": sum(value>1.e-10 for value in diagonal),
                       "expected_rank": int(close_phi)+int(close_theta),
                       "analytic_phi_m": exact_azimuthal*close_phi,
                       "theta_cut_flux_m": result["seam_flux_m"],
                       "theta_max_node_flux_m": result["max_node_flux_m"],
                       "theta_max_period_error": result["max_period_error"]}
                if close_phi and close_theta and ns == GRIDS[-1][0]:
                    row["zero_flux_perturbations"] = perturbations(result, ns, nt)
                    visual[f"{name}_s_m"] = result["s_m"]
                    visual[f"{name}_theta_rad"] = result["theta_rad"]
                    visual[f"{name}_potential"] = result["potentials"]
                trials.append(row)
    closed_thick = [r for r in trials if r["shell"] == "thick" and r["expected_rank"] == 2]
    theta_coarse, theta_fine = [r["norm_matrix_diagonal_m"][1] for r in closed_thick[-2:]]
    thin = next(r for r in reversed(trials) if r["shell"]=="thin" and r["expected_rank"]==2)
    center = sum(SHELLS["thin"])/2
    factor = center/np.sqrt(MAJOR**2-center**2)
    thin_analytic = np.array([factor, 1/factor]) * (SHELLS["thin"][1]-SHELLS["thin"][0])
    example = physical_example()
    perturb = [p for r in trials for p in r.get("zero_flux_perturbations", [])]
    checks = {
        "cut_ranks": all(r["rank"]==r["expected_rank"] for r in trials),
        "theta_continuity_and_period": all(r["theta_max_node_flux_m"]<1.e-9
                                           and r["theta_max_period_error"]<1.e-9 for r in trials),
        "theta_cut_flux_equals_norm": all(abs(r["theta_cut_flux_m"]-r["norm_matrix_diagonal_m"][1])<1.e-9
                                          for r in trials),
        "pinched_circle_cannot_store_harmonic_energy": all(r["norm_matrix_diagonal_m"][i]<1.e-10
                    for r in trials for i, closed in enumerate((r["closed_phi"], r["closed_theta"])) if not closed),
        "azimuthal_quadrature": all(abs(r["norm_matrix_diagonal_m"][0]/r["analytic_phi_m"]-1)<.001
                                  for r in trials if r["closed_phi"]) and all(
                    abs(s["azimuthal_m"]/example["solid_coefficient_m"]-1)<.001 for s in solid),
        "theta_converged_on_finest_two_grids": abs(theta_coarse/theta_fine-1)<.01,
        "thin_limit": bool(np.all(abs(np.array(thin["norm_matrix_diagonal_m"])/thin_analytic-1)<.02)),
        "fluxless_fields_increase_energy": all(abs(p["cross_term_m"])<1.e-9
                     and abs(p["flux_through_cut_m"])<1.e-9 and p["max_node_flux_m"]<1.e-9
                     and abs(p["norm_ratio"]-1.25)<1.e-8 for p in perturb),
    }
    np.savez_compressed(out/"meridian.npz", **visual)
    save_summary(out, {"geometry_m": {"major": MAJOR, "inner": INNER, "outer": OUTER},
                       "physical_example": example, "solid_quadrature": solid, "shells": trials,
                       "thin_analytic_m": thin_analytic.tolist(), "checks": checks}, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    run(parser.parse_args().out)
