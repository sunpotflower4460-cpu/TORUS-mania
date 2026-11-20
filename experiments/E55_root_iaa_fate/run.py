"""Digitize chromatogram fractions and the independent oxIAA comparison."""

import numpy as np

from experiments import particle_return_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb

WINDOWS = {"oxIAA_Glc": (19, 22), "oxIAA": (27, 30), "possible_free_IAA": (39, 42)}


def fraction_bars(gray, columns, zero, upper, maximum):
    """Read the vertical marks through the center of each one-minute fraction."""
    left, right = columns
    rt = np.arange(1, 45)
    x = np.rint(left + (right - left) * rt / 45).astype(int)
    heights, tops = [], []
    for horizontal in x:
        stripe = np.median(gray[upper + 2 : zero, horizontal - 2 : horizontal + 3], axis=1)
        dark = np.flatnonzero(stripe < 160)
        if not dark.size or dark[-1] < len(stripe) - 2:
            row = zero
        else:
            cursor = int(dark[-1])
            while cursor > 0 and stripe[cursor - 1] < 185:
                cursor -= 1
            row = cursor + upper + 2
        tops.append(row)
        heights.append((zero - row) * maximum / (zero - upper))
    vals = np.asarray(heights)
    return {
        "fraction_retention_min": rt.tolist(),
        "columns": x.tolist(),
        "bar_rows": tops,
        "dpm": vals.tolist(),
        "dpm_reading_halfwidth": 2 * maximum / (zero - upper),
        "displayed_sum_dpm": float(vals.sum()),
        "peak_windows": ratios(rt, vals),
    }


def curve(gray):
    # Follow the ink across the continuous trace. The step penalty rejects
    # isolated peak labels while allowing a steep center of a narrow peak.
    left, right, top, bottom = 80, 732, 14, 282
    costs = gray[top:bottom, left:right] / 255
    rows = np.arange(len(costs))
    step = np.arange(-35, 36)
    choices = rows[:, None] + step
    clipped = np.clip(choices, 0, len(rows) - 1)
    penalty = np.where(choices == clipped, 0.027 * np.abs(step), 1e4)
    state = costs[:, 0].copy()
    memory = np.zeros(costs.shape, dtype=int)
    for i in range(1, costs.shape[1]):
        transition = state[clipped] + penalty
        best = np.argmin(transition, axis=1)
        memory[:, i] = clipped[rows, best]
        state = costs[:, i] + transition[rows, best]
    path = np.empty(costs.shape[1], dtype=int)
    path[-1] = int(np.argmin(state))
    for i in range(len(path) - 1, 0, -1):
        path[i - 1] = memory[path[i], i]
    expected_controls = [rt for rt in (2, 5.9, 19.9, 28.5, 32.3, 34.8, 36.1, 40.3, 44.0)]
    xx = np.arange(left, right)
    time = (xx - 77) * 45 / (734 - 77)
    amplitude = 150 + (286 - (path + top)) * 650 / (286 - 8)
    quiet = (time < 4.8) | ((time > 11) & (time < 17)) | (time > 42.4)
    background = float(np.median(amplitude[quiet]))
    return {
        "time_min": time.tolist(),
        "relative_units": amplitude.tolist(),
        "estimated_baseline": background,
        "trace_ink_fraction": float(np.mean(costs[path, np.arange(len(path))] < 0.63)),
        "signal_at_diagnostic_retention_minutes": np.interp(expected_controls, time, amplitude).tolist(),
        "diagnostic_retention_minutes": expected_controls,
        "peak_windows": ratios(time, amplitude, baseline=background, baseline_width=8),
    }


def ratios(time, signal, baseline=0, baseline_width=None):
    out = {}
    for compound, (lower, upper) in WINDOWS.items():
        measures = []
        backgrounds = (
            [baseline]
            if baseline_width is None
            else [baseline - baseline_width, baseline, baseline + baseline_width]
        )
        nominal = np.maximum(signal - baseline, 0)
        primary = (time >= lower) & (time <= upper)
        for offset in (-1, 0, 1):
            select = (time >= lower + offset) & (time <= upper + offset)
            for b in backgrounds:
                shifted = np.maximum(signal - b, 0)
                measures.append(float(shifted[select].sum() / shifted.sum()))
        out[compound] = {
            "inclusive_minutes": [lower, upper],
            "fraction": float(nominal[primary].sum() / nominal.sum()),
            "range_moving_window_and_baseline": [min(measures), max(measures)],
        }
    return out


def run(raw, out):
    chrom = rgb(sources.read(raw, "pencikfig5.jpg")).mean(axis=2)
    graph = rgb(sources.read(raw, "pencikfig6.jpg")).mean(axis=2)
    a = curve(chrom)
    b = fraction_bars(chrom, (77, 735), 628, 350, 4000.0)
    c = fraction_bars(chrom, (75, 734), 971, 693, 600.0)
    rows = []
    for x in (238, 560):
        marks = np.where(np.median(graph[20:518, x - 3 : x + 4], axis=1) < 100)[0]
        if not len(marks):
            raise ValueError(f"Missing oxIAA bar at {x}")
        rows.append(float(np.median(marks[:6])) + 20)
    levels = [(520 - row) * 700 / (520 - 9) for row in rows]
    b_peak = int(np.argmax(b["dpm"]))
    c_peak = int(np.argmax(c["dpm"]))
    summary = {
        "experiment": "E55",
        "doi": "10.1105/tpc.113.114421",
        "feeding_hours": 8,
        "whole_seedling_fig5a": a,
        "apical_5mm_of_shoot_excised_root_fig5b": b,
        "root_protoplasts_fig5c": c,
        "fig6_LC_MS": {
            "treatment_hours": 5.5,
            "root_length_mm": 5,
            "samples_per_group": 5,
            "bar_rows": rows,
            "control_and_IAA_treated_fmol_oxIAA_per_sample": levels,
            "treatment_to_control": levels[1] / levels[0],
        },
        "scope": "Free IAA window includes any unassigned label. Panel B is label recovered from the 5 mm apex of shoot-excised roots after dosing the cut. Neither area nor dpm share is a fraction of the whole applied dose.",
        "checks": {
            "two_figure_dimensions": chrom.shape == (1045, 746) and graph.shape == (578, 759),
            "continuous_chromatogram_trace": a["trace_ink_fraction"] > 0.75,
            "root_peak_in_assigned_oxidation_window": b["fraction_retention_min"][b_peak]
            in (19, 20, 21, 27, 28, 29),
            "protoplast_peak_in_oxIAA_window": 27 <= c["fraction_retention_min"][c_peak] <= 29,
            "all_printed_minute_fractions": len(b["dpm"]) == len(c["dpm"]) == 44,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
