"""Read matched washout times and the reversal of an auxin sensor asymmetry."""

import fitz
import numpy as np

from experiments import particle_return_sources as sources
from experiments.common import save_summary

WASH_RECT = (427, 296, 568, 408)
GRAVITY_RECT = (38, 168, 267, 428)


def render(book, page, bounds):
    pix = book[page].get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(*bounds), alpha=False)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).astype(np.int16)


def curves(image, x, purple_y, teal_y, axis):
    r, g, b = np.moveaxis(image, -1, 0)
    masks = ((r - g > 34) & (b - g > 30), (g - r > 54) & (b - r > 54))
    for mask, rows in zip(masks, (purple_y, teal_y), strict=True):
        for horizontal, vertical in zip(x, rows, strict=True):
            if not mask[vertical - 5 : vertical + 6, horizontal - 7 : horizontal + 8].any():
                raise ValueError(f"Mean trace missing at {horizontal},{vertical}")
    bottom, top, bottom_val, top_val = axis
    slope = (top_val - bottom_val) / (bottom - top)
    return {
        "x_px": x,
        "mean_marker_rows": [purple_y, teal_y],
        "axis": axis,
        "FRET_ratio": [[bottom_val + (bottom - y) * slope for y in rows] for rows in (purple_y, teal_y)],
        "reading_halfwidth_ratio": 2 * slope,
    }


def run(raw, out):
    with fitz.open(stream=sources.read(raw, "auxsen.pdf"), filetype="pdf") as source:
        wash = render(source, 2, WASH_RECT)
        tilt = render(source, 3, GRAVITY_RECT)
    washout = curves(
        wash,
        [113, 151, 190, 229, 267, 306, 344, 382],
        [206, 164, 185, 213, 222, 227, 231, 233],
        [206, 104, 149, 158, 158, 162, 170, 184],
        (235, 49, 0.9, 1.5),
    )
    groups = np.asarray(washout["FRET_ratio"])
    normalized = (groups[:, 1:] - groups[:, 0:1]) / (groups[:, 1:2] - groups[:, 0:1])
    direction = curves(
        tilt,
        [92, 180, 267, 354, 442, 528, 615],
        [593, 536, 521, 513, 535, 516, 512],
        [622, 520, 491, 491, 497, 553, 550],
        (679, 415, 0.2, 1.4),
    )
    upper, lower = direction["FRET_ratio"]
    summary = {
        "experiment": "E57",
        "doi": "10.1038/s41586-021-03425-2",
        "washout_fig3h": {
            "order": ["one_hour_exposure", "ten_minute_exposure"],
            "seedlings": [3, 5],
            "axis_labels": ["before", "after", "5", "10", "15", "20", "25", "30"],
            "normalized_above_own_baseline_from_after": normalized.tolist(),
            **washout,
        },
        "gravity_fig4d": {
            "order": ["top_or_left", "bottom_or_right"],
            "seedlings": 10,
            "orientation_and_elapsed_minutes": [
                "0° / 0",
                "135° / 1",
                "135° / 5",
                "135° / 10",
                "135° / 30",
                "0° / 1",
                "0° / 5",
            ],
            "bottom_right_minus_top_left": (np.asarray(lower) - upper).tolist(),
            **direction,
        },
        "scope": "FRET is an auxin-binding sensor readout; normalized deviations can fall below pre-treatment baseline and do not identify the pathway of an individual molecule.",
        "checks": {
            "panels_at_registered_dimensions": wash.shape[:2] == (336, 423)
            and tilt.shape[:2] == (780, 687),
            "both_washout_groups_eight_matching_stages": groups.shape == (2, 8),
            "before_similarity_matches_normalization": bool(np.ptp(groups[:, 0]) < 0.01),
            "common_time_axes_and_two_gravity_sides": len(upper) == len(lower) == 7,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
