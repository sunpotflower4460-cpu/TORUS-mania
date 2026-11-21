"""Measure post-activation body axis elongation from the publisher's vector curves."""

import fitz
import numpy as np

from experiments import iaa_embryo_sources as sources
from experiments.common import save_summary

COLORS = {
    "control": (0, 0, 0),
    "optoGEF": (191 / 255, 0, 191 / 255),
    "optoGAP": (1, 165 / 255, 0),
}
KNOWN_TICKS = [442.980, 464.011, 485.042, 506.072]
TIMES = [0, 10, 15]
Y_ONE = 178.506
Y_TWO = 97.722


def flatten(item):
    kind, *pdf_points = item
    if kind == "l":
        return np.asarray([tuple(point) for point in pdf_points])
    if kind == "c":
        points = np.asarray([tuple(point) for point in pdf_points])
        t = np.linspace(0, 1, 21)[:, None]
        return (
            (1 - t) ** 3 * points[0]
            + 3 * t * (1 - t) ** 2 * points[1]
            + 3 * t**2 * (1 - t) * points[2]
            + t**3 * points[3]
        )
    raise ValueError(f"Unrecognized outline item {kind}")


def mean_paths(drawings):
    result = {}
    for group, expected in COLORS.items():
        selected = [
            drawing
            for drawing in drawings
            if drawing["fill"] is not None
            and np.allclose(drawing["fill"], expected, atol=0.001)
            and 425 < drawing["rect"].x0 < 440
            and 514 < drawing["rect"].x1 < 515
            and 100 < drawing["rect"].y0 < 153
            and drawing["rect"].y1 < 185
            and len(drawing["items"]) > 80
        ]
        (curve,) = selected
        result[group] = [flatten(item) for item in curve["items"]]
    return result


def height_at(outline, x):
    heights = []
    for poly in outline:
        left, right = poly[:-1], poly[1:]
        crossed = ((left[:, 0] < x) & (x <= right[:, 0])) | (
            (right[:, 0] < x) & (x <= left[:, 0])
        )
        a, b = left[crossed], right[crossed]
        heights.extend(
            a[:, 1] + (x - a[:, 0]) * (b[:, 1] - a[:, 1]) / (b[:, 0] - a[:, 0])
        )
    return np.array(heights)


def length_at(outline, time):
    x = np.interp(time, (0, 5, 10, 15), KNOWN_TICKS)
    offsets = np.linspace(-0.30, 0.30, 61)
    readings = []
    tick_spacing = (KNOWN_TICKS[-1] - KNOWN_TICKS[0]) / 15
    for offset in offsets:
        ordinates = height_at(outline, x + offset * tick_spacing)
        if len(ordinates):
            height = (Y_ONE - ordinates) / (Y_ONE - Y_TWO) + 1.0
            readings.append(
                (
                    offset,
                    (height.max() + height.min()) / 2,
                    (height.max() - height.min()) / 2,
                )
            )
    if len(readings) < 4:
        raise ValueError(f"No readable stroke around time {time}")
    times, centers, half_widths = np.array(readings).T
    slope, intercept = np.polyfit(times, centers, 1)
    residual = centers - (intercept + times * slope)
    return {
        "relative_mean_length": float(intercept),
        "local_line_readings": len(times),
        "local_window_minutes_either_side": 0.30,
        "max_stroke_half_width_plus_fit_residual": float(
            np.max(half_widths + np.abs(residual))
        ),
    }


def run(raw, out):
    with fitz.open(sources.source(raw, "herrera-perez-figures.pdf")) as pdf:
        page = pdf[2]
        drawings = page.get_drawings()
        if "FIG. 1." not in page.get_text():
            raise ValueError("Expected Figure 1 on PDF page 3")
        paths = mean_paths(drawings)
    means = {
        group: {str(t): length_at(curve, t) for t in TIMES}
        for group, curve in paths.items()
    }
    reference = {"control": 1.71, "optoGEF": 1.37, "optoGAP": 1.29}
    values = {group: row["15"]["relative_mean_length"] for group, row in means.items()}
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E69",
            "doi": "10.1103/PRXLife.1.013004",
            "stage": "blue light intervention starts at onset of Drosophila germband extension",
            "figure_1c": means,
            "available_times_note": "Common shown range ends around minute 17. Final values not extracted at 20 or 25 minutes.",
            "n_embryos_per_genotype_reported": [3, 5],
            "figure_1c_15_minute_text_means": reference,
            "figure_1c_15_minute_text_sem": {
                "control": 0.09,
                "optoGEF": 0.09,
                "optoGAP": 0.05,
            },
            "figure_1c_text_p_versus_control": {"optoGEF": 0.06, "optoGAP": 0.02},
            "relative_length_15_minute_minus_control": {
                key: values[key] - values["control"] for key in ("optoGEF", "optoGAP")
            },
            "figure_4a_reported_medial_myosin_percent_change_mean_sem": {
                "control": {"minute_1": [3, 2], "minute_5": [9, 2]},
                "optoGEF": {"minute_1": [22, 4], "minute_5": [66, 14]},
            },
            "figure_3d_text_initial_retraction_um_per_s_control_mean_sem": {
                "ap_junctions": [0.36, 0.04],
                "dv_junctions": [0.11, 0.03],
            },
            "scope": "Tissue length changes after the intervention at extension onset. Published group mean curves, not independent embryo values or calibrated stress-energy measurements. The optoGEF mean difference had reported p=0.06.",
            "checks": {
                "all_prespecified_times_in_common_figure_range_read": all(
                    all(row[str(t)] for t in TIMES) for row in means.values()
                ),
                "all_group_endpoints_match_printed_means_within_002": all(
                    abs(means[group]["15"]["relative_mean_length"] - normal) < 0.02
                    for group, normal in reference.items()
                ),
            },
        },
        __file__,
        sources.__file__,
    )
