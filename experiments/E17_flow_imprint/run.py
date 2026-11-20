"""Test whether a pre-existing flow changes deposition from a spherical seed."""

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from experiments.common import save_summary
from experiments.E03_vortex import topology

ROOT = Path(__file__).resolve().parents[2]
DIFF_RESOURCE, DIFF_MATERIAL = .025, .0015
LOSS = .20
CASES = ("circulation", "reversed", "azimuthal", "through", "still", "late_start", "mirrored")
THRESHOLDS = (.35, .50, .65)


class Cylinder:
    def __init__(self, n):
        h = self.h = 1. / n
        self.rf = h * np.arange(n + 1)
        self.zf = -1. + h * np.arange(2 * n + 1)
        self.r = (self.rf[:-1] + self.rf[1:]) / 2
        self.z = (self.zf[:-1] + self.zf[1:]) / 2
        self.rface_area = 2 * np.pi * self.rf[:, None] * h
        self.zface_area = 2 * np.pi * self.r[:, None] * h
        self.volume = self.zface_area * h
        self.shape = (n, 2 * n)

    def integral(self, field):
        return float(np.sum(self.volume * field))

    def net_inflow_per_volume(self, radial, axial):
        return -(np.diff(radial, axis=0) + np.diff(axial, axis=1)) / self.volume

    def transport(self, field, diffusivity, flow=None):
        radial = np.zeros((self.shape[0] + 1, self.shape[1]))
        axial = np.zeros((self.shape[0], self.shape[1] + 1))
        radial[1:-1] = -diffusivity / self.h * self.rface_area[1:-1] * np.diff(field, axis=0)
        axial[:, 1:-1] = -diffusivity / self.h * self.zface_area * np.diff(field, axis=1)
        if flow is not None:
            radial[1:-1] += flow.positive_r * field[:-1] + flow.negative_r * field[1:]
            axial[:, 1:-1] += flow.positive_z * field[:, :-1] + flow.negative_z * field[:, 1:]
            # The entering reservoir carries zero resource. The outgoing side
            # carries the nearest interior value; diffusive flux is zero there.
            axial[:, 0] = flow.bottom_out * field[:, 0]
            axial[:, -1] = flow.top_out * field[:, -1]
        escape = np.sum(axial[:, -1]) - np.sum(axial[:, 0])
        return self.net_inflow_per_volume(radial, axial), float(escape)

    def geometry(self, field):
        center = self.z[None, :]
        amount = self.integral(field)
        zbar = self.integral(field * center) / amount
        widths = [np.sqrt(self.integral(field * x2) / amount)
                  for x2 in (self.r[:, None]**2, (center - zbar)**2)]
        return {"amount": amount, "z_centroid": zbar, "radial_rms": float(widths[0]),
                "axial_rms": float(widths[1])}


@dataclass
class Flow:
    positive_r: np.ndarray
    negative_r: np.ndarray
    positive_z: np.ndarray
    negative_z: np.ndarray
    bottom_out: np.ndarray
    top_out: np.ndarray
    kinetic: np.ndarray
    divergence_error: float


def streamfunction(r, z):
    return 6 * r**4 * (1 - r**2)**3 * (1 - z**2)**2


def flows(grid):
    r, z = grid.r[:, None], grid.z[None, :]
    ur = 24 * r**3 * (1 - r**2)**3 * z * (1 - z**2)
    uz = 12 * r**2 * (1 - r**2)**2 * (2 - 5*r**2) * (1 - z**2)**2
    kinetic = (ur**2 + uz**2) / 2
    stream = streamfunction(grid.rf[:, None], grid.zf[None, :])
    fr, fz = -2 * np.pi * np.diff(stream, axis=1), 2 * np.pi * np.diff(stream, axis=0)
    through_e = grid.integral(kinetic) / grid.integral(np.ones(grid.shape))

    def build(radial, axial, energy):
        radial_inner, axial_inner = radial[1:-1], axial[:, 1:-1]
        return Flow(np.maximum(radial_inner, 0.), np.minimum(radial_inner, 0.),
                    np.maximum(axial_inner, 0.), np.minimum(axial_inner, 0.),
                    np.minimum(axial[:, 0], 0.), np.maximum(axial[:, -1], 0.), energy,
                    float(abs(grid.net_inflow_per_volume(radial, axial)).max()))

    zero_r, zero_z = np.zeros_like(fr), np.zeros_like(fz)
    through_z = np.broadcast_to(np.sqrt(2 * through_e) * grid.zface_area, fz.shape)
    return {
        "circulation": build(fr, fz, kinetic),
        "reversed": build(-fr, -fz, kinetic),
        "azimuthal": build(zero_r, zero_z, np.sqrt(2 * kinetic)**2 / 2),
        "through": build(zero_r, through_z, np.full(grid.shape, through_e)),
        "still": build(zero_r, zero_z, np.zeros(grid.shape)),
    }


def derivatives(grid, case, source, c, m):
    uptake = 2 * c * m * (1 - m)
    c_transport, escape = grid.transport(c, DIFF_RESOURCE, case)
    m_transport, _ = grid.transport(m, DIFF_MATERIAL)
    return c_transport + source - LOSS*c - uptake, m_transport + uptake, uptake, escape


def integrate(grid, case, source, c, m, seconds, steps_per_second):
    dt = 1 / steps_per_second
    intake = grid.integral(source)
    initial_total = grid.integral(c + m)
    escaped, lost = 0., 0.
    uptake_integral = np.zeros_like(m)
    records = []
    cumulative_error = 0.
    lowest, largest_m = float(c.min()), float(m.max())
    for unit in range(seconds):
        for _ in range(steps_per_second):
            dc, dm, uptake, escape = derivatives(grid, case, source, c, m)
            stage_c, stage_m = c + dt*dc, m + dt*dm
            dc2, dm2, uptake2, escape2 = derivatives(grid, case, source, stage_c, stage_m)
            lost += dt/2 * LOSS * grid.integral(c + stage_c)
            escaped += dt/2 * (escape + escape2)
            uptake_integral += dt/2 * (uptake + uptake2)
            c = c + dt/2 * (dc + dc2)
            m = m + dt/2 * (dm + dm2)
        lowest = min(lowest, float(c.min()), float(m.min()))
        largest_m = max(largest_m, float(m.max()))
        balance = grid.integral(c + m) - initial_total + lost + escaped - (unit + 1)*intake
        cumulative_error = max(cumulative_error, abs(balance) / max(1.e-14, (unit + 1)*intake))
        uptake_amount = grid.integral(uptake_integral)
        records.append({
            "time": unit + 1, "resource": grid.integral(c), "material": grid.integral(m),
            "uptake": uptake_amount, "resource_loss": lost, "resource_outflow": escaped,
            "material_geometry": grid.geometry(m) if m.any() else None,
            "uptake_geometry": grid.geometry(uptake_integral) if uptake_amount else None,
        })
    return c, m, uptake_integral, {
        "snapshots": records, "maximum_relative_budget_error": cumulative_error,
        "minimum_sampled_density": lowest, "maximum_sampled_material_density": largest_m,
    }


def isotropic_volume(grid, field):
    n = grid.shape[0]
    coordinates = -1. + (np.arange(2*n) + .5) * grid.h
    radial = np.hypot(coordinates[:, None], coordinates[None, :])
    r_index = np.broadcast_to((radial[:, :, None] - grid.r[0]) / grid.h, (2*n, 2*n, 2*n))
    z_index = np.broadcast_to(np.arange(2*n)[None, None, :], r_index.shape)
    volume = map_coordinates(field, [r_index, z_index], order=1, mode="nearest")
    volume[radial > 1.] = 0.
    return volume


def superlevels(grid, field):
    volume = isotropic_volume(grid, field)
    return {str(level): topology.component_topology(volume, level) for level in THRESHOLDS}


def uniform_calibration(steps_per_second):
    grid = Cylinder(8)
    zero = np.zeros(grid.shape)
    c, _, _, _ = integrate(grid, None, np.ones(grid.shape), zero, zero, 1, steps_per_second)
    exact = -np.expm1(-LOSS) / LOSS
    return float(abs(c-exact).max()/exact)


def run(n, refine, out, classify=True):
    grid = Cylinder(n)
    f = flows(grid)
    r, z = grid.r[:, None], grid.z[None, :]
    psi = streamfunction(r, z)
    source = 7.5 * np.exp(-(r/.32)**2 - ((z+.55)/.18)**2)
    seed = .35 * (1 - np.tanh((np.hypot(r, z)-.27)/.045))
    empty = np.zeros(grid.shape)
    # Upper bound for the diagonal of the explicit transport loss operator.
    base_steps = int(np.ceil((4*DIFF_RESOURCE / grid.h**2 + 4/grid.h + LOSS + .5) / .88))
    steps = base_steps * refine

    primed, preparation = {}, {}
    for name, flow in f.items():
        primed[name], _, _, log = integrate(grid, flow, source, empty, empty, 5, steps)
        preparation[name] = log
    primed["late_start"] = primed["still"]
    preparation["late_start"] = preparation["still"]
    primed["mirrored"], _, _, preparation["mirrored"] = integrate(
        grid, f["reversed"], source[:, ::-1], empty, empty, 5, steps
    )

    result, final_c, final_material, all_uptake = {}, {}, {}, {}
    for name in CASES:
        driver = {"mirrored": "reversed", "late_start": "circulation"}.get(name, name)
        supply = source[:, ::-1] if name == "mirrored" else source
        c, m, consumed, log = integrate(grid, f[driver], supply, primed[name], seed, 4, steps)
        final_material[name], all_uptake[name], final_c[name] = m, consumed, c
        net_change = grid.integral(m - seed)
        log.update({
            "prep": {k: v for k, v in preparation[name].items() if k != "snapshots"},
            "preseed_resource": grid.geometry(primed[name]),
            "net_material_gain": net_change,
            "integrated_resource_to_material_error": abs(net_change - log["snapshots"][-1]["uptake"]),
        })
        if classify:
            log["final_material_superlevels"] = superlevels(grid, m)
            log["uptake_superlevels"] = superlevels(grid, consumed)
        result[name] = log

    reference = f["circulation"].kinetic
    same_energy = max(abs(f[name].kinetic - reference).max() / reference.max()
                      for name in ("reversed", "azimuthal"))
    matching_total = abs(grid.integral(f["through"].kinetic) / grid.integral(reference) - 1)
    mirror_error = abs(final_material["circulation"] - final_material["mirrored"][:, ::-1]).max()
    swirl_error = abs(final_material["still"] - final_material["azimuthal"]).max()
    ref_z = result["circulation"]["snapshots"][-1]["uptake_geometry"]["z_centroid"]
    reversed_z = result["reversed"]["snapshots"][-1]["uptake_geometry"]["z_centroid"]
    l1 = grid.integral(abs(final_material["circulation"] - final_material["reversed"]))
    analytic = uniform_calibration(steps)
    max_div = max(flow.divergence_error for flow in f.values())
    checks = {
        "solenoidal_face_volume_flux": max_div < 1.e-10,
        "same_kinetic_energy_in_direction_controls": same_energy < 1.e-10 and matching_total < 1.e-10,
        "axisymmetric_advection_vanishes_for_azimuthal": float(swirl_error) < 1.e-10,
        "reflection_of_source_and_velocity": float(mirror_error) < 1.e-10,
        "analytic_uniform_source_and_sink": analytic < 1.e-4,
        "closed_and_open_budgets": all(
            max(log["maximum_relative_budget_error"], log["prep"]["maximum_relative_budget_error"]) < .001
            for log in result.values()),
        "nonnegative_sampled_fields": all(
            min(log["minimum_sampled_density"], log["prep"]["minimum_sampled_density"]) >= -1.e-12
            and log["maximum_sampled_material_density"] <= 1.+1.e-12 for log in result.values()),
        "uptake_matches_material_gain": all(log["integrated_resource_to_material_error"] < 1.e-9
                                             for log in result.values()),
    }
    data = {
        "radial_cells": n, "axial_cells": 2*n, "dt": 1/steps, "time_refinement": refine,
        "domain": "simply connected cylinder, nondimensional length and time",
        "seed_geometry": grid.geometry(seed), "case_names": list(CASES),
        "kinetic_energy_per_volume_matched_through": grid.integral(reference) / grid.integral(np.ones(grid.shape)),
        "pointwise_energy_max_relative_difference": float(same_energy),
        "uniform_calibration_max_relative_error": analytic, "mirror_density_max_error": float(mirror_error),
        "finite_volume_max_divergence": max_div, "uptake_centroid_delta_reversing": ref_z - reversed_z,
        "final_material_density_l1_reversing_per_seed_mass": l1 / grid.integral(seed),
        "trials": result, "checks": checks,
    }
    if classify:
        data["flow_superlevels"] = superlevels(grid, psi)
        data["initial_kinetic_superlevels"] = superlevels(grid, reference)
        data["seed_superlevels"] = superlevels(grid, seed)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "fields.npz", r=grid.r, z=grid.z, source=source, seed=seed,
                        streamfunction=psi, kinetic=reference,
                        resource_before_seed=np.stack([primed[name] for name in CASES]),
                        final_resource=np.stack([final_c[name] for name in CASES]),
                        final_material=np.stack([final_material[name] for name in CASES]),
                        accumulated_uptake=np.stack([all_uptake[name] for name in CASES]))
    save_summary(out, data, __file__, topology.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", required=True, choices=("grid48", "grid96", "time_refined96"))
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E17")
    opts = parser.parse_args()
    grid_size, refinement = {"grid48": (48, 1), "grid96": (96, 1), "time_refined96": (96, 2)}[opts.variant]
    run(grid_size, refinement, opts.out / opts.variant)
