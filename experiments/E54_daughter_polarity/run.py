"""Measure the persistent offset of daughter-cell polarity after alternate scanning patterns."""

from itertools import combinations

import numpy as np

from experiments import turning_path_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import pdf_figure

ZERO, SIXTY = 344.0, 51.0


def to_degrees(row):
    return (ZERO - row) * 60 / (ZERO - SIXTY)


def dots(gray, centers):
    values = []
    for x, y in centers:
        # Symmetric patch about each filled symbol, avoiding its adjoining neighbor or the mean bar.
        yy, xx = np.indices((9, 9))
        ink = (gray[y - 4 : y + 5, x - 4 : x + 5] < 88) & ((xx - 4) ** 2 + (yy - 4) ** 2 <= 16)
        if ink.sum() < 35:
            raise ValueError(f"Dot not present at {x},{y}")
        values.append(to_degrees(y - 4 + float(np.mean(yy[ink]))))
    return values


def mean_bar(gray, x):
    ink = np.flatnonzero(gray[12:448, x - 3 : x + 4].mean(axis=1) < 80)
    if not 3 <= len(ink) <= 12:
        raise ValueError("Unresolved printed mean")
    return to_degrees(12 + float(ink.mean()))


def run(raw, out):
    image = pdf_figure(sources.read(raw, "ng.pdf"), 9, 526)
    gray = np.mean(image, axis=2)
    centers = {
        "alternating_scan": [(228, 309), (215, 326), (228, 326), (228, 344), (228, 449)],
        "directional_scan": [(402, 28), (402, 63), (402, 186), (402, 221), (402, 344)],
    }
    angles = {name: dots(gray, points) for name, points in centers.items()}
    control, flow = [np.array(values) for values in angles.values()]
    means = [float(control.mean()), float(flow.mean())]
    bars = [mean_bar(gray, 190), mean_bar(gray, 366)]
    difference = means[1] - means[0]
    pool = np.r_[control, flow]
    diffs = []
    for allocation in combinations(range(len(pool)), len(flow)):
        pick = np.zeros(len(pool), dtype=bool)
        pick[list(allocation)] = True
        diffs.append(float(pool[pick].mean() - pool[~pick].mean()))
    omitted = [means[1] - np.delete(control, i).mean() for i in range(len(control))]
    omitted.extend(np.delete(flow, i).mean() - means[0] for i in range(len(flow)))
    summary = {
        "experiment": "E54",
        "doi": "10.1016/j.cub.2023.08.076",
        "source": "Fig. 5G, lower panel, P1, nmy-2(ts); approximately 8.5 min after flow",
        "pixel_zero_60deg": [ZERO, SIXTY],
        "dot_centers_px": centers,
        "angle_offset_degrees": angles,
        "reading_halfwidth_degrees": 2 * 60 / (ZERO - SIXTY),
        "means_control_flow_deg": means,
        "printed_bars_control_flow_deg": bars,
        "flow_minus_control_degrees": difference,
        "median_control_flow_deg": [float(np.median(control)), float(np.median(flow))],
        "delete_one_difference_range_deg": [float(min(omitted)), float(max(omitted))],
        "all_label_allocations": len(diffs),
        "two_sided_exchangeable_label_p": float(np.mean(np.abs(diffs) >= abs(difference) - 1e-9)),
        "scope": "Laser direction alternated between scans in controls to cancel induced flow. Tissue temperature, delivered mechanical work and the next division orientation were not paired outcomes in Fig. 5G.",
        "checks": {
            "figure_size": image.shape[:2] == (544, 512),
            "tenth_degree_ticks": abs(to_degrees(149) - 40) < 0.2 and abs(to_degrees(442) + 20) < 0.2,
            "printed_bars_agree_with_scored_points": max(abs(a - b) for a, b in zip(means, bars)) < 0.6,
            "complete_small_sample_permutation": len(diffs) == 252,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
