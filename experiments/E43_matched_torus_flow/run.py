"""Compare two three-dimensional flow directions at the same kinetic energy."""

import argparse
from pathlib import Path

import numpy as np

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
MAJOR_RADIUS = 1.2
DENSITY = 1000.
UPTAKE = .32
DURATION = 8.


def grid(counts):
    ns, nt, nf = counts
    ds = (.50 - .14) / ns
    dtheta, dphi = 2*np.pi/nt, 2*np.pi/nf
    s = (.14 + (np.arange(ns) + .5) * ds)[:, None, None]
    theta = ((np.arange(nt) + .5) * dtheta)[None, :, None]
    phi = ((np.arange(nf) + .5) * dphi)[None, None, :]
    r = MAJOR_RADIUS + s*np.cos(theta)
    volume = np.broadcast_to(s*r*ds*dtheta*dphi, counts)
    radial_profile = MAJOR_RADIUS * (.8 + .2*np.cos(np.pi*(s-.32)/.18))
    speed = radial_profile / r
    q_theta = np.broadcast_to(radial_profile*ds*dphi, counts)
    q_phi = np.broadcast_to(speed*s*ds*dtheta, counts)
    return s, theta, phi, volume, speed, radial_profile, q_theta, q_phi


def energy_budget(s, theta, phi, volume, speed, radial_profile, q_theta, q_phi):
    # Orthogonal unit directions in the embedded torus.
    cos2, sin2 = np.cos(phi)**2, np.sin(phi)**2
    theta_speed2 = speed**2 * (np.sin(theta)**2*(cos2+sin2) + np.cos(theta)**2)
    phi_speed2 = speed**2 * (cos2+sin2)
    ref_energy = .5 * DENSITY * speed**2
    # At each theta face, use its own metric and carried kinetic energy.
    theta_out = theta + np.pi / volume.shape[1]
    face_speed = radial_profile / (MAJOR_RADIUS + s*np.cos(theta_out))
    power_theta = .5 * DENSITY * face_speed**2 * q_theta
    power_phi = ref_energy * q_phi
    local_power = power_theta - np.roll(power_theta, 1, axis=1)
    return {
        "kinetic_energy_J": float(np.sum(ref_energy*volume)),
        "maximum_pointwise_energy_density_difference_over_peak": float(
            np.max(np.abs(theta_speed2-phi_speed2)) / np.max(speed**2)
        ),
        "theta_flux_through_theta_cut_W": float(power_theta[:, -1, :].sum()),
        "phi_flux_through_phi_cut_W": float(power_phi[:, :, -1].sum()),
        "theta_net_steady_work_W_in_closed_volume": float(local_power.sum()),
        "theta_positive_local_steady_work_W": float(np.maximum(local_power, 0).sum()),
        "theta_negative_local_steady_work_W": float(np.minimum(local_power, 0).sum()),
        "max_volume_face_flow_imbalance": float(max(
            np.max(np.abs(q_theta - np.roll(q_theta, 1, axis=1))),
            np.max(np.abs(q_phi - np.roll(q_phi, 1, axis=2))),
        )),
    }


def packet(theta, phi, volume):
    dtheta = np.angle(np.exp(1j*(theta-4.65)))
    dphi = np.angle(np.exp(1j*(phi-1.1)))
    distribution = volume*np.exp(-.5*((dtheta/.28)**2 + (dphi/.23)**2))
    return distribution / distribution.sum()


def describes(deposits, remaining, outflow, extra, theta, phi):
    mass = float(deposits.sum())
    theta_mass = deposits.sum(axis=(0, 2))
    phi_mass = deposits.sum(axis=(0, 1))
    return {
        "made_material_fraction_of_initial_resource": mass,
        "remaining_resource": float(remaining.sum()),
        "cumulative_outflow": outflow, "cumulative_supplement": extra,
        "mass_residual": float(abs(mass + remaining.sum() + outflow - extra - 1.)),
        "theta_concentration": float(abs(theta_mass @ np.exp(1j*theta.ravel()))/mass),
        "phi_concentration": float(abs(phi_mass @ np.exp(1j*phi.ravel()))/mass),
        "theta_material_marginal": theta_mass.tolist(),
        "phi_material_marginal": phi_mass.tolist(),
    }


def simulate(counts, cfl):
    s, theta, phi, volume, speed, profile, qt, qp = grid(counts)
    energy = energy_budget(s, theta, phi, volume, speed, profile, qt, qp)
    rates_t, rates_p = qt/volume, qp/volume
    steps = int(np.ceil(DURATION*max(rates_t.max(), rates_p.max())/cfl))
    dt = DURATION / steps
    reaction = -np.expm1(-UPTAKE * dt)
    rates_t, rates_p = dt*rates_t, dt*rates_p
    groups = ("closed_theta", "closed_phi", "cut_theta", "cut_theta_with_supplement")
    start = packet(theta, phi, volume)
    resource = {name: start.copy() for name in groups}
    material = {name: np.zeros_like(start) for name in groups}
    outflow = {name: 0. for name in groups}
    supply = {name: 0. for name in groups}
    for _ in range(steps):
        history = None
        for name in groups:
            azimuthal = name == "closed_phi"
            axis = 2 if azimuthal else 1
            outgoing = resource[name] * (rates_p if azimuthal else rates_t)
            incoming = np.roll(outgoing, 1, axis=axis)
            if name == "closed_theta":
                history = outgoing[:, -1, :]
            if name.startswith("cut"):
                outflow[name] += float(outgoing[:, -1, :].sum())
                incoming[:, 0, :] = 0.
                if name == "cut_theta_with_supplement":
                    incoming[:, 0, :] = history
                    supply[name] += float(history.sum())
            after_advection = resource[name] - outgoing + incoming
            gain = reaction * after_advection
            material[name] += gain
            resource[name] = after_advection - gain
    cases = {name: describes(material[name], resource[name], outflow[name], supply[name], theta, phi)
             for name in groups}
    return {
        "grid": list(counts), "steps": steps, "step_s": dt,
        "theta_centers": theta.ravel().tolist(), "phi_centers": phi.ravel().tolist(),
        "prescribed_energy": energy, "cases": cases,
        "material_L1_difference_theta_versus_phi": float(np.abs(material["closed_theta"]-material["closed_phi"]).sum()),
        "material_L1_difference_theta_versus_supplied_cut": float(
            np.abs(material["closed_theta"]-material["cut_theta_with_supplement"]).sum()
        ),
    }


def run(out):
    trials = {
        "coarse": simulate((8, 40, 64), .60),
        "fine": simulate((12, 64, 96), .60),
        "fine_small_step": simulate((12, 64, 96), .30),
    }
    analytic = 1-np.exp(-UPTAKE*DURATION)
    results = {
        "experiment": "E43", "radius_m": MAJOR_RADIUS, "cross_section_radii_m": [.14, .50],
        "density_kg_m3": DENSITY, "uptake_per_s": UPTAKE, "duration_s": DURATION,
        "analytic_closed_material_fraction": float(analytic), "trials": trials,
        "checks": {
            "incompressibility_and_equal_energy_density": all(
                r["prescribed_energy"]["max_volume_face_flow_imbalance"] < 1e-12
                and r["prescribed_energy"]["maximum_pointwise_energy_density_difference_over_peak"] < 1e-12
                and abs(r["prescribed_energy"]["theta_net_steady_work_W_in_closed_volume"]) < 1e-8
                for r in trials.values()
            ),
            "all_material_balances": all(x["mass_residual"] < 1e-9 for r in trials.values() for x in r["cases"].values()),
            "analytic_closed_uptake": all(
                abs(r["cases"][k]["made_material_fraction_of_initial_resource"] - analytic) < 1e-12
                for r in trials.values() for k in ("closed_theta", "closed_phi")
            ),
            "direction_effect_across_grid_and_step": all(
                r["cases"]["closed_theta"]["theta_concentration"] < r["cases"]["closed_phi"]["theta_concentration"]
                and r["cases"]["closed_phi"]["phi_concentration"] < r["cases"]["closed_theta"]["phi_concentration"]
                for r in trials.values()
            ),
            "replacement_matches_but_requires_supplement": all(
                r["material_L1_difference_theta_versus_supplied_cut"] < 1e-12
                and r["cases"]["cut_theta_with_supplement"]["cumulative_supplement"] > 0
                for r in trials.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, results, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E43")
    run(parser.parse_args().out)
