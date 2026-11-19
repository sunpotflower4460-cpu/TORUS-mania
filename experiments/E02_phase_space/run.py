"""E02. Two phase coordinates with free drift or symmetric sine coupling."""

import argparse
import math
from pathlib import Path

import numpy as np

from experiments.common import save_summary
from . import figures

TAU = math.tau
INITIAL = np.array([0.17, 0.49])
BINS = 16
EPSILONS = (0.02, 0.05)
RESULTS = Path(__file__).resolve().parents[2] / "research/results/E02"
# Identifier, omega2/omega1, coupling (rad/s), measurement noise seed.
CASES = [
    ("single", 0.0, 0.0, None),
    ("equal", 1.0, 0.0, None),
    ("three_halves", 1.5, 0.0, None),
    ("sqrt2", math.sqrt(2), 0.0, None),
    ("rational_99_70", 99 / 70, 0.0, None),
    ("slip", 1.5, 1.0, None),
    ("lock", 1.5, 2.0, None),
    *((f"noise_{seed}", 1.5, 0.0, seed) for seed in (11, 29, 47)),
]


def integrate(t, ratio, coupling):
    """Classical RK4 on the unwrapped pair (no modulo operation in the ODE)."""
    omega = TAU * np.array([1.0, ratio])
    dt = t[1] - t[0]
    if coupling == 0:
        # RK4 reduces to addition of a constant increment at each step.
        increments = np.tile(dt * omega, (len(t), 1))
        increments[0] = INITIAL
        return np.cumsum(increments, axis=0)

    def rate(state):
        interaction = coupling * math.sin(state[1] - state[0])
        return np.array([omega[0] + interaction, omega[1] - interaction])

    phase = np.empty((len(t), 2))
    phase[0] = INITIAL
    for i in range(1, len(t)):
        p = phase[i - 1]
        a = rate(p)
        b = rate(p + 0.5 * dt * a)
        c = rate(p + 0.5 * dt * b)
        d = rate(p + dt * c)
        phase[i] = p + (dt / 6.0) * (a + 2*b + 2*c + d)
    return phase


def return_distance(observed):
    diff = observed - observed[0]
    shortest = (diff + np.pi) % TAU - np.pi
    return np.max(np.abs(shortest), axis=1)


def entries(distance, tolerance):
    inside = distance <= tolerance
    return np.r_[False, inside[1:] & ~inside[:-1]]


def cell_counts(phase):
    indices = np.floor((phase % TAU) * (BINS / TAU)).astype(int) % BINS
    counts = np.bincount(indices[:, 0] * BINS + indices[:, 1], minlength=BINS**2)
    return counts.reshape(BINS, BINS)


def measure_window(t, observed, rate, duration, events, distances):
    end = rate * duration
    delta = observed[:, 1] - observed[:, 0]
    advance = observed[end] - observed[0]
    midpoint = end // 2
    counts = cell_counts(observed[:end])
    strobe = cell_counts(observed[:end:rate])
    returns = []
    for epsilon, flags in zip(EPSILONS, events.T):
        times = t[:end + 1][flags[:end + 1]]
        returns.append({"epsilon_rad": epsilon, "count": len(times),
                        "first_s": float(times[0]) if len(times) else None})
    metrics = {"duration_s": duration, "density_samples": end,
               "occupied_cells_of_256": int(np.count_nonzero(counts)),
               "occupied_cells_1hz_strobe": int(np.count_nonzero(strobe)),
               "rotation_ratio": float(advance[1] / advance[0]),
               "delta_final_rad": float(delta[end]),
               "delta_tail_drift_rad_s": float((delta[end] - delta[midpoint]) / (duration / 2)),
               "delta_tail_span_rad": float(np.ptp(delta[midpoint:end+1])),
               "recurrences": returns}
    if duration >= 70:
        metrics["distance_at_70s_rad"] = float(distances[70 * rate])
    return metrics, counts


def run(out, pilot):
    out.mkdir(exist_ok=True, parents=True)
    duration = 8 if pilot else 80
    windows = [8] if pilot else [8, 80]
    summary = {"experiment": "E02", "pilot": pilot, "initial_phase_rad": INITIAL.tolist(),
               "omega1_rad_s": TAU, "tolerances_rad": EPSILONS, "density_grid": [BINS, BINS],
               "runs": [], "near_ratio_comparison": [], "checks": {}}
    arrays = {}
    coarse = {}
    for rate in ([64] if pilot else [64, 128]):
        t = np.arange(duration * rate + 1) / rate
        arrays[f"t_{rate}_s"] = t
        for case, ratio, coupling, seed in CASES:
            key = f"{case}_{rate}"
            numeric = integrate(t, ratio, coupling)
            stats = {"case": case, "rate_hz": rate, "frequency_ratio": ratio,
                     "K_rad_s": coupling, "noise_seed": seed, "measurement_sigma_rad": 0.0,
                     "windows": []}
            if coupling == 0:
                phase = INITIAL + t[:, None] * (TAU * np.array([1.0, ratio]))
                error = float(np.abs(numeric - phase).max())
                stats["rk4_vs_direct_max_rad"] = error
                summary["checks"][key + "/direct_solution"] = error <= 1e-8
            else:
                phase = numeric
                residual = phase.sum(axis=1) - INITIAL.sum() - TAU * (1 + ratio) * t
                error = float(np.abs(residual).max())
                stats["phase_sum_max_residual_rad"] = error
                summary["checks"][key + "/phase_sum"] = error <= 1e-8
                if rate == 64:
                    coarse[case] = phase
                else:
                    error = float(np.abs(phase[::2] - coarse[case]).max())
                    stats["coarse_fine_max_rad"] = error
                    summary["checks"][key + "/step_halving"] = error <= 1e-5
            observed = phase
            if seed is not None:
                stats["measurement_sigma_rad"] = 0.08
                rng = np.random.Generator(np.random.PCG64(seed))
                noise = rng.normal(0.0, 0.08, size=(duration * 128 + 1, 2))
                observed = phase + noise[::128 // rate]
            distance = return_distance(observed)
            flags = np.column_stack([entries(distance, e) for e in EPSILONS])
            arrays[key + "/phase_rad"] = phase
            arrays[key + "/observed_rad"] = observed
            arrays[key + "/wave"] = np.sin(observed)
            arrays[key + "/delta_rad"] = observed[:, 1] - observed[:, 0]
            arrays[key + "/return_distance_rad"] = distance
            arrays[key + "/entry"] = flags
            for window in windows:
                metrics, counts = measure_window(t, observed, rate, window, flags, distance)
                stats["windows"].append(metrics)
                arrays[f"{key}/density_{window}s"] = counts
                summary["checks"][f"{key}/density_{window}s"] = int(counts.sum()) == window * rate
            summary["runs"].append(stats)

            reference_period = {"single": 1, "equal": 1, "three_halves": 2, "rational_99_70": 70}.get(case)
            if reference_period is not None and reference_period <= duration:
                first = stats["windows"][-1]["recurrences"][0]["first_s"]
                summary["checks"][key + "/known_return"] = first == reference_period
            if case == "lock" and duration == 80:
                expected = math.asin(TAU * (ratio - 1) / (2 * coupling))
                stats["lock_prediction_rad"] = expected
                stats["lock_error_rad"] = abs(metrics["delta_final_rad"] - expected)
                summary["checks"][key + "/locked_phase"] = stats["lock_error_rad"] <= 1e-6
            if case == "slip":
                summary["checks"][key + "/slipping"] = metrics["delta_tail_drift_rad_s"] > 0

        difference = np.abs(arrays[f"sqrt2_{rate}/phase_rad"][:, 1] -
                            arrays[f"rational_99_70_{rate}/phase_rad"][:, 1])
        for second in ([8] if pilot else [8, 70, 80]):
            measured = float(difference[second * rate])
            summary["near_ratio_comparison"].append({"rate_hz": rate, "t_s": second,
                "pair_phase_gap_rad": measured, "predicted_rad": TAU * second * abs(99 / 70 - math.sqrt(2))})
            if second == 8:
                summary["checks"][f"pair_{rate}/short_window"] = measured < EPSILONS[0]
            if second == 70:
                summary["checks"][f"pair_{rate}/70s_thresholds"] = EPSILONS[0] < measured < EPSILONS[1]
    if not pilot:
        np.savez_compressed(out / "observations.npz", **arrays)
        figures.plot_states(arrays, out / "phase_space.png")
    save_summary(out, summary, __file__, figures.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Output directory (default: research/results/E02[/pilot])")
    parser.add_argument("--pilot", action="store_true", help="Run the 8-second window at 64 Hz")
    args = parser.parse_args()
    run(args.out or (RESULTS / "pilot" if args.pilot else RESULTS), args.pilot)
