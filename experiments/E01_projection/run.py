"""E01. Evaluate registered motions and surface controls. Lengths in m, time in s."""

import argparse
from pathlib import Path

import numpy as np

from experiments.common import ring_xyz, save_summary
from . import figures

TAU = 2 * np.pi
VIEWS = {"xyz": (0, 1, 2), "front_xz": (0, 2), "side_yz": (1, 2), "top_xy": (0, 1)}
SETTINGS = {"base": (0.20, 0.35, 2.0), "holdout": (0.71, 0.83, 3.0)}
RESULTS = Path(__file__).resolve().parents[2] / "research/results/E01"


def composed_rotation(angle):
    """Multiply consecutive planar rotations, starting from the specified initial phase."""
    increments = np.diff(angle, prepend=0.0)
    return np.cumprod(np.exp(1j * increments))


def motions(t, phi0, theta0, major):
    phi = TAU * t + phi0
    theta = 1.5 * TAU * t + theta0
    unit = composed_rotation(phi)
    zero = np.zeros_like(t)
    circle = np.column_stack((unit.real, unit.imag, zero))
    velocity_y = TAU * unit.real
    yield "circle", circle, velocity_y
    helix = circle.copy()
    helix[:, 2] = t  # Axial speed 1 m/s.
    yield "helix", helix, velocity_y
    # Solution of the straight spring y'' = -omega² y, in terms of its initial y and y'.
    y = np.sin(phi0) * np.cos(TAU * t) + np.cos(phi0) * np.sin(TAU * t)
    yield "linear_spring", np.column_stack((zero, y, zero)), TAU * np.cos(phi)
    variable = composed_rotation(phi + 0.55 * np.sin(TAU * t))
    rate = TAU * (1.0 + 0.55 * np.cos(TAU * t))
    yield "variable_circle", np.column_stack((variable.real, variable.imag, zero)), rate * variable.real
    for name, minor_angle, minor_rate in [
        ("one_winding", zero + theta0, 0.0), ("two_windings", theta, 1.5 * TAU)
    ]:
        xyz = ring_xyz(phi, minor_angle, major)
        vy = TAU * xyz[:, 0] - minor_rate * np.sin(minor_angle) * np.sin(phi)
        yield name, xyz, vy


def surface_points(n, major):
    azimuth = (TAU * np.arange(n) / n)[None, :]
    u = np.linspace(-1.0, 1.0, n + 1)[:, None]
    yield "ring_torus", ring_xyz(azimuth, np.pi * u, major)
    for name, radius, z in [
        ("sphere", np.cos(np.pi * u / 2), np.sin(np.pi * u / 2)),
        ("cylinder", np.ones_like(u), u),
        ("hyperboloid", np.sqrt(1.0 + u**2), u),
        ("double_cone", np.abs(u), u),
    ]:
        x = radius * np.cos(azimuth)
        yield name, np.stack((x, radius * np.sin(azimuth), np.broadcast_to(z, x.shape)), axis=-1)


def surface_metrics(points):
    x, y, z = points.reshape(-1, 3).T
    radius = np.hypot(x, y)
    hole_ratio = float(radius.min() / radius.max())
    # Only the front view (x,z) is used for these two widths. Tolerance in m.
    rim = float(np.abs(x[np.isclose(z, z.max(), rtol=0, atol=1e-12)]).max())
    waist = float(np.abs(x[np.isclose(z, 0.0, rtol=0, atol=1e-12)]).max())
    top_candidate = hole_ratio > 0.2
    return {"samples": len(x), "top_min_over_max_radius": hole_ratio, "top_candidate": top_candidate,
            "upper_halfwidth_m": rim, "middle_halfwidth_m": waist,
            "two_view_candidate": top_candidate and rim < 0.9 * waist}


def motion_metrics(t, xyz, vy, phi0, major, name, rate):
    x, y, z = xyz.T
    spectrum = 2 * np.abs(np.fft.rfft(y[:-1])) / (len(t) - 1)
    # The 2-second window puts 1 Hz and 2 Hz at Fourier bins 2 and 4.
    error = y - np.sin(TAU * t + phi0)
    distances = {}
    for view, axes in VIEWS.items():
        delta = xyz[:, axes] - xyz[0, axes]
        distances[view] = [float(np.linalg.norm(delta[second * rate])) for second in (1, 2)]
    result = {"y_vs_uniform_sine_max_m": float(np.abs(error).max()),
              "y_vs_uniform_sine_rmse_m": float(np.sqrt(np.mean(error**2))),
              "y_amplitude_1hz_m": float(spectrum[2]), "y_amplitude_2hz_m": float(spectrum[4]),
              "z_span_m": float(np.ptp(z)), "positive_vy_samples": int(np.count_nonzero(vy > 0)),
              "return_distance_m_at_1s_2s": distances}
    if name in ("one_winding", "two_windings"):
        result["surface_residual_max_m2"] = float(np.abs((np.hypot(x, y) - major)**2 + z**2 - 1).max())
    return result


def run(out, pilot):
    out.mkdir(exist_ok=True, parents=True)
    summary = {"experiment": "E01", "pilot": pilot, "duration_s": 2.0, "r_m": 1.0,
               "base_frequency_hz": 1.0, "seed": None, "runs": [], "checks": {}}
    arrays = {}
    for setting, (phi0, theta0, major) in SETTINGS.items():
        if pilot and setting != "base":
            continue
        for rate in ([64] if pilot else [64, 128]):
            t = np.arange(2 * rate + 1) / rate
            key = f"{setting}_{rate}"
            arrays[key + "/t_s"] = t
            values = {}
            for name, xyz, vy in motions(t, phi0, theta0, major):
                values[name] = motion_metrics(t, xyz, vy, phi0, major, name, rate)
                arrays[f"{key}/{name}/xyz_m"] = xyz
                arrays[f"{key}/{name}/vy_m_s"] = vy
            shapes = {name: surface_metrics(points) for name, points in surface_points(rate, major)}
            summary["runs"].append({"setting": setting, "rate_hz": rate, "phi0_rad": phi0,
                                    "theta0_rad": theta0, "R_m": major, "motions": values,
                                    "surfaces": shapes})
            circle = values["circle"]
            checks = {
                "sine_and_edge_view": circle["y_vs_uniform_sine_max_m"] <= 1e-10 and circle["z_span_m"] == 0,
                "same_y_on_line": bool(np.max(np.abs(arrays[key + "/circle/xyz_m"][:, 1]
                                                     - arrays[key + "/linear_spring/xyz_m"][:, 1])) <= 1e-10),
                "helix_advances": abs(values["helix"]["z_span_m"] - 2) <= 1e-10,
                "variable_speed_harmonic": values["variable_circle"]["y_amplitude_2hz_m"] > circle["y_amplitude_2hz_m"] + 0.01,
                "on_assigned_surface": all(values[n]["surface_residual_max_m2"] <= 1e-10
                                           for n in ("one_winding", "two_windings")),
                "windings_close": values["one_winding"]["return_distance_m_at_1s_2s"]["xyz"][0] <= 1e-10
                                  and values["two_windings"]["return_distance_m_at_1s_2s"]["xyz"][0] > 1e-10
                                  and values["two_windings"]["return_distance_m_at_1s_2s"]["xyz"][1] <= 1e-10,
                "single_view_confusions": {n for n, s in shapes.items() if s["top_candidate"]}
                                           == {"ring_torus", "cylinder", "hyperboloid"},
                "two_view_controls": all(s["two_view_candidate"] == (n == "ring_torus")
                                         for n, s in shapes.items()),
            }
            summary["checks"].update({f"{key}/{n}": passed for n, passed in checks.items()})
    if not pilot:
        np.savez_compressed(out / "observations.npz", **arrays)
        figures.plot_motions(arrays, out / "projections.png")
        figures.plot_surfaces(surface_points(64, SETTINGS["base"][2]), out / "surfaces.png")
    save_summary(out, summary, __file__, figures.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Output directory (default: research/results/E01[/pilot])")
    parser.add_argument("--pilot", action="store_true", help="Run only base conditions at 64 Hz")
    args = parser.parse_args()
    run(args.out or (RESULTS / "pilot" if args.pilot else RESULTS), args.pilot)
