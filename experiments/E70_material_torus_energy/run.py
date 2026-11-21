"""Close the mechanical energy balance of three material tori in a sphere."""

import numpy as np
from numpy.polynomial.legendre import leggauss

from experiments.common import save_summary

RADIUS = 100e-6
AXIAL_SPEED = 10e-6
C = AXIAL_SPEED / (2 * RADIUS**2)
DENSITY = 1000.0
VISCOSITIES = (0.0, 0.001, 0.01)
FRACTIONS = (0.20, 0.55, 0.80)
RESOLUTIONS = (48, 96, 192)
PRESSURE_SHIFT = 1.0


def velocity(r, z):
    return 2 * C * r * z, 2 * C * (RADIUS**2 - 2 * r**2 - z**2)


def pressure(r, z, mu, shift=0.0):
    acceleration_potential = (
        2 * C**2 * (RADIUS**2 * r**2 - r**4 - 2 * RADIUS**2 * z**2 + z**4)
    )
    # Delta u_z is -20C. This gradient lets the spherical boundary supply
    # mechanical work with no force density in the bulk.
    return shift - DENSITY * acceleration_potential - 20 * mu * C * z


def torus_coordinates(q, theta):
    # (r²-a²/2)²+(rz)²=q² on every level of the streamfunction.
    r = np.sqrt(RADIUS**2 / 2 + q * np.cos(theta))
    z = q * np.sin(theta) / r
    return r, z


def surface_geometry(q, theta):
    r, z = torus_coordinates(q, theta)
    dr = -q * np.sin(theta) / (2 * r)
    dz = q * np.cos(theta) / r - z * dr / r
    # The normal is outward on the meridional contour oriented CCW.
    return r, z, 2 * np.pi * r * dz, -2 * np.pi * r * dr


def dissipation(q, theta, radial_order, mu):
    x, weight = leggauss(radial_order)
    radius = ((x + 1) * q / 2)[:, None]
    r, z = torus_coordinates(radius, theta)
    strain_squared = C**2 * (24 * z**2 + 18 * r**2)
    # 2πr dr dz = π/r * dx dy, with x=r²-a²/2 and y=rz.
    volume_density = np.pi * radius / r
    dtheta = 2 * np.pi / len(theta)
    return float(
        (weight * q / 2)
        @ np.sum(2 * mu * strain_squared * volume_density, axis=1)
        * dtheta
    )


def fluxes(q, theta, mu):
    r, z, normal_r, normal_z = surface_geometry(q, theta)
    ur, uz = velocity(r, z)
    dtheta = 2 * np.pi / len(theta)
    normal_velocity = normal_r * ur + normal_z * uz
    kinetic_density = DENSITY * (ur**2 + uz**2) / 2
    advective = kinetic_density * normal_velocity
    pressure_work = pressure(r, z, mu) * normal_velocity
    shifted_pressure_work = pressure(r, z, mu, PRESSURE_SHIFT) * normal_velocity
    stress_work_r = 2 * mu * C * (2 * z * ur - 3 * r * uz)
    stress_work_z = 2 * mu * C * (-3 * r * ur - 4 * z * uz)
    viscous = -stress_work_r * normal_r - stress_work_z * normal_z
    total = advective + pressure_work + viscous
    components = {
        "advection": advective,
        "pressure_work": pressure_work,
        "viscous_stress_work": viscous,
        "total": total,
    }
    return {
        "integrated_outward_W": {
            name: float(values.sum() * dtheta) for name, values in components.items()
        },
        "gross_total_outflow_W": float(np.maximum(total, 0).sum() * dtheta),
        "gross_total_inflow_W": float(np.maximum(-total, 0).sum() * dtheta),
        "max_abs_normal_volume_transport_m3_per_s_per_radian": float(
            np.abs(normal_velocity).max()
        ),
        "pressure_offset_max_effect_W_per_radian": float(
            np.abs(shifted_pressure_work - pressure_work).max()
        ),
        "normal_total_flux_W_per_radian": total.tolist()
        if len(theta) == RESOLUTIONS[0]
        else None,
    }


def momentum_residual(mu):
    r, z = np.meshgrid(
        RADIUS * np.array([0.25, 0.5, 0.75]), RADIUS * np.array([-0.33, 0, 0.33])
    )
    h = RADIUS * 1e-4
    ur, uz = velocity(r, z)
    dr_u = (np.array(velocity(r + h, z)) - velocity(r - h, z)) / (2 * h)
    dz_u = (np.array(velocity(r, z + h)) - velocity(r, z - h)) / (2 * h)
    convection = ur * dr_u + uz * dz_u
    grad = np.array(
        [
            (pressure(r + h, z, mu) - pressure(r - h, z, mu)) / (2 * h),
            (pressure(r, z + h, mu) - pressure(r, z - h, mu)) / (2 * h),
        ]
    )
    left = DENSITY * convection + grad
    left[1] += 20 * mu * C
    return float(np.abs(left).max())


def ring_geometry(fraction):
    q = RADIUS**2 / 2 * fraction
    reference = np.linspace(0, 2 * np.pi, 145)
    r, z = torus_coordinates(q, reference)
    return {
        "normalized_meridional_radius": fraction,
        "min_max_r_m": [float(r.min()), float(r.max())],
        "max_abs_z_m": float(np.abs(z).max()),
        "r_z_m": np.column_stack((r, z)).tolist(),
    }


def run(out):
    series = []
    for mu in VISCOSITIES:
        for fraction in FRACTIONS:
            q = RADIUS**2 / 2 * fraction
            integrations = []
            for n in RESOLUTIONS:
                theta = np.arange(n) * (2 * np.pi / n)
                result = fluxes(q, theta, mu)
                storage_loss = dissipation(q, theta, n // 2, mu)
                integrations.append(
                    {
                        "angle_count": n,
                        "radial_quadrature_order": n // 2,
                        "viscous_dissipation_W": storage_loss,
                        "steady_energy_residual_W": storage_loss
                        + result["integrated_outward_W"]["total"],
                        **result,
                    }
                )
            series.append(
                {
                    "viscosity_Pa_s": mu,
                    "motion_surface_level": fraction,
                    "resolutions": integrations,
                }
            )
    fine = [row["resolutions"][-1] for row in series]
    residuals = [momentum_residual(mu) for mu in VISCOSITIES]
    # Check with the actual simulated magnitudes as well as an absolute
    # floor for the analytic zero-viscosity reference.
    typical = max(row["viscous_dissipation_W"] for row in fine)
    checks = {
        "same_steady_velocity_satisfies_momentum_balance": max(residuals) < 1e-7,
        "material_tori_have_zero_normal_volume_flux": all(
            row["max_abs_normal_volume_transport_m3_per_s_per_radian"] < 1e-26
            for row in fine
        ),
        "pressure_gauge_has_no_material_surface_normal_flux": all(
            row["pressure_offset_max_effect_W_per_radian"] < 1e-26 for row in fine
        ),
        "zero_viscosity_has_zero_net_and_gross_energy_flux": all(
            all(
                row[key] < 1e-27
                for key in ("gross_total_inflow_W", "gross_total_outflow_W")
            )
            for row in fine[: len(FRACTIONS)]
        ),
        "viscous_tori_require_net_inward_mechanical_power": all(
            row["integrated_outward_W"]["total"] < 0 for row in fine[len(FRACTIONS) :]
        ),
        "energy_balance_for_all_tori_and_resolutions": all(
            abs(level["steady_energy_residual_W"]) < 1e-9 * typical
            for row in series
            for level in row["resolutions"]
        ),
        "power_scales_with_viscosity_without_changing_flow": all(
            np.isclose(
                high["integrated_outward_W"]["total"],
                10 * low["integrated_outward_W"]["total"],
                atol=1e-29,
                rtol=1e-8,
            )
            for high, low in zip(fine[6:], fine[3:6], strict=True)
        ),
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E70",
            "scope": "Manufactured steady Newtonian solution inside a sphere with prescribed tangential boundary motion, zero body force and identical velocity in every viscosity. No embryo calibration.",
            "outer_radius_m": RADIUS,
            "center_axial_speed_m_per_s": AXIAL_SPEED,
            "density_kg_per_m3": DENSITY,
            "pressure_offset_Pa": PRESSURE_SHIFT,
            "meridional_curves": [ring_geometry(fraction) for fraction in FRACTIONS],
            "momentum_residual_max_Pa_per_m_by_viscosity": dict(
                zip(map(str, VISCOSITIES), residuals, strict=True)
            ),
            "surfaces_and_energy_budgets": series,
            "checks": checks,
        },
        __file__,
    )
