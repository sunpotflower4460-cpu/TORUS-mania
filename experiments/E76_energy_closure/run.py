"""Construct equal energy balances with different internal flux trajectories."""

from itertools import pairwise

import numpy as np

from experiments.common import save_summary

MAJOR_RADIUS = 0.45
RADIAL_RADIUS = 0.10
VERTICAL_RADIUS = 0.18
PERIOD = 2 * np.pi
SEEDS = np.array(
    [(0.45, 0, 0), (0.48, 0, 0.05), (0.40, 0, -0.06), (0.85, 0, 0), (0.10, 0, 0)]
)


def straight(points):
    field = np.zeros_like(points, dtype=float)
    field[..., 2] = 1.0
    return field


def with_torus(points):
    """Add curl of f*(y,-x,0)/2 and a divergence-free azimuthal field to e_z."""
    x, y, z = np.moveaxis(points, -1, 0)
    r = np.hypot(x, y)
    s = ((r - MAJOR_RADIUS) / RADIAL_RADIUS) ** 2 + (z / VERTICAL_RADIUS) ** 2
    t = np.clip((s - 1) / 3, 0.0, 1.0)
    profile = (1 - t) ** 3 * (1 + 3 * t + 6 * t**2)
    derivative = -10 * t**2 * (1 - t) ** 2
    profile_r = derivative * 2 * (r - MAJOR_RADIUS) / RADIAL_RADIUS**2
    profile_z = derivative * 2 * z / VERTICAL_RADIUS**2
    return np.stack(
        (
            x * profile_z / 2 - y * profile,
            y * profile_z / 2 + x * profile,
            1 - profile - r * profile_r / 2,
        ),
        axis=-1,
    )


def trace(field, seeds, steps):
    dt = PERIOD / steps
    path = [seeds.copy()]
    for _ in range(steps):
        start = path[-1]
        k1 = field(start)
        k2 = field(start + dt * k1 / 2)
        k3 = field(start + dt * k2 / 2)
        k4 = field(start + dt * k3)
        path.append(start + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6)
    return np.array(path)


def trajectory_metrics(paths):
    times = np.linspace(0, PERIOD, len(paths))
    phase = np.unwrap(np.arctan2(paths[..., 1], paths[..., 0]), axis=0)
    values = []
    for j, seed in enumerate(paths[0]):
        outside = times[np.any(np.abs(paths[:, j]) > 1, axis=-1)]
        values.append(
            {
                "seed_xyz": seed.tolist(),
                "end_xyz": paths[-1, j].tolist(),
                "endpoint_error_or_distance": float(
                    np.linalg.norm(paths[-1, j] - seed)
                ),
                "delta_z": float(paths[-1, j, 2] - seed[2]),
                "turns": float((phase[-1, j] - phase[0, j]) / PERIOD),
                "left_cube": bool(len(outside)),
                "first_sample_outside_cube": float(outside[0])
                if len(outside)
                else None,
            }
        )
    return values


def boundary_flux(field):
    axes = np.linspace(-1, 1, 33)
    u, v = np.meshgrid(axes, axes)
    result = {}
    for j, coord in enumerate("xyz"):
        for sign in (-1, 1):
            points = [u, v]
            points.insert(j, np.full_like(u, sign))
            normal = sign * field(np.stack(points, axis=-1))[..., j]
            result[f"{coord}_{sign:+d}"] = {
                "sampled_outward_min": float(normal.min()),
                "sampled_outward_max": float(normal.max()),
                "integrated_outward_flux": float(
                    np.trapezoid(np.trapezoid(normal, axes, axis=1), axes)
                ),
            }
    return result


def divergence_residual(field, grid, step):
    divergence = sum(
        (field(grid + offset)[..., axis] - field(grid - offset)[..., axis]) / (2 * step)
        for axis, offset in enumerate(np.eye(3) * step)
    )
    return {
        "rms": float(np.sqrt(np.mean(divergence**2))),
        "max_abs": float(np.abs(divergence).max()),
    }


def run(out):
    paths = {
        name: {
            str(steps): trajectory_metrics(trace(field, SEEDS, steps))
            for steps in (64, 128)
        }
        for name, field in (("straight", straight), ("local_torus", with_torus))
    }
    faces = {
        "straight": boundary_flux(straight),
        "local_torus": boundary_flux(with_torus),
    }
    coordinates = np.linspace(-1, 1, 33)
    grid = np.stack(np.meshgrid(*([coordinates] * 3), indexing="ij"), axis=-1)
    difference_steps = (0.01, 0.005, 0.0025, 0.0001, 0.00005, 0.000025)
    residuals = {
        name: {str(h): divergence_residual(field, grid, h) for h in difference_steps}
        for name, field in (("straight", straight), ("local_torus", with_torus))
    }
    closed = paths["local_torus"]["128"][:3]
    open_paths = paths["local_torus"]["128"][3:] + paths["straight"]["128"]
    fine_steps = [str(step) for step in difference_steps[-3:]]
    fine_errors = [residuals["local_torus"][h]["rms"] for h in fine_steps]
    summary = {
        "experiment": "E76",
        "field_units": "dimensionless kinematic example",
        "cube_interval_xyz": [-1, 1],
        "torus_r0_dr_dz": [MAJOR_RADIUS, RADIAL_RADIUS, VERTICAL_RADIUS],
        "closed_core_volume_fraction_of_cube": float(
            2 * np.pi**2 * MAJOR_RADIUS * RADIAL_RADIUS * VERTICAL_RADIUS / 8
        ),
        "profile_definition": "s=((r-r0)/dr)^2+(z/dz)^2; t=clip((s-1)/3,0,1); f=(1-t)^3(1+3t+6t^2)",
        "flux_definition": "F_z_base + curl(f*(y,-x,0)/2) + f*(-y,x,0)",
        "analytical_divergence_both_fields": 0,
        "analytical_period_in_core": float(PERIOD),
        "trajectory_samples_over_analytic_period": paths,
        "boundary": faces,
        "divergence_evaluation_grid_shape": grid.shape[:3],
        "numerical_divergence_residual": residuals,
        "interpretation_limits": [
            "The additional flux is constructed to vanish in a neighborhood of the boundary.",
            "A circular path follows a direction field in this steady model; it is not a tracked embryo or material trajectory.",
            "Identical divergence fixes net local source minus sink, without separately measuring either.",
            "No constitutive law or morphogenesis is fitted. This result concerns the information in balance data alone.",
        ],
        "checks": {
            "all_six_normal_flux_distributions_are_equal_on_sampled_faces": faces[
                "straight"
            ]
            == faces["local_torus"],
            "nonzero_equal_inflow_and_outflow": [
                faces["straight"][f"z_{sign:+d}"]["integrated_outward_flux"]
                for sign in (-1, 1)
            ]
            == [-4.0, 4.0],
            "numerical_divergence_converges_toward_analytic_zero": (
                fine_errors[-1] < 1e-5
                and all(coarse > 3 * fine for coarse, fine in pairwise(fine_errors))
                and residuals["straight"][fine_steps[-1]]["max_abs"] == 0
            ),
            "core_error_decreases_when_step_is_halved": all(
                coarse["endpoint_error_or_distance"]
                > 10 * fine["endpoint_error_or_distance"]
                for coarse, fine in zip(paths["local_torus"]["64"][:3], closed)
            ),
            "core_seeds_make_one_closed_turn": all(
                not row["left_cube"]
                and row["endpoint_error_or_distance"] < 1e-5
                and abs(row["turns"] - 1) < 1e-5
                for row in closed
            ),
            "all_open_controls_exit": all(
                row["left_cube"] and abs(row["delta_z"] - PERIOD) < 1e-10
                for row in open_paths
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__)
