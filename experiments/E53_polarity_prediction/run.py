"""Recover early pole-prediction errors from two independent panels of the same figure."""

import xml.etree.ElementTree as ET

import numpy as np
from scipy.stats import binomtest

from experiments import turning_path_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import pdf_figure

TIMES = [
    "fertilization",
    "anaphase_I",
    "five_min_after_AI",
    "anaphase_II",
    "one_min_before_SB",
    "symmetry_breaking",
    "before_pronuclear_migration",
]
# Left/right x coordinates, zero/top y coordinates, and the printed top count of Fig. 4B.
AXES = [
    (126.5, 603, 831.5, 572, 50),
    (695.5, 1171, 831.5, 572, 50),
    (1272.5, 1750, 831.5, 572, 30),
    (1836, 2312, 831.5, 572, 40),
    (126.5, 603, 1316.5, 1058, 40),
    (695.5, 1171, 1316.5, 1058, 40),
    (1272.5, 1750, 1316.5, 1058, 140),
]
DENOMINATORS = [(112, 9), (139, 10), (134, 11), (161, 11), (170, 10), (185, 12), (194, 16)]


def histogram(image, bounds):
    left, right, zero, top, maximum = bounds
    height_per_case = (zero - top) / maximum
    rows = []
    for col in np.linspace(left, right, 41)[1::2]:
        x = round(col)
        stripe = np.median(image[round(top) : round(zero) + 1, x - 4 : x + 5], axis=1)
        blue = stripe[:, 2] - stripe[:, 0] > 45
        orange = stripe[:, 0] - stripe[:, 2] > 65
        # Start at the x axis. The legend floats above the bars and is disconnected.
        color = blue | orange
        blank_run = np.convolve((~color).astype(int), np.ones(3, dtype=int), mode="valid") == 3
        gaps = np.flatnonzero(blank_run)
        first = int(gaps[-1] + 3) if gaps.size else 0
        rows.append(
            [float(blue[first:].sum() / height_per_case), float(orange[first:].sum() / height_per_case)]
        )
    return np.asarray(rows)


def panel_a(image):
    columns = [920, 1012, 1104, 1195, 1287, 1379, 1470]
    rows = {"PP": [358, 356, 352, 352, 352, 356, 358], "DP": [65, 152, 304, 331, 358, 358, 358]}
    result = {}
    for group, centers in rows.items():
        yy = []
        for x, y in zip(columns, centers, strict=True):
            patch = image[y - 11 : y + 12, x - 2 : x + 3]
            contrast = patch[:, :, 2] - patch[:, :, 0]
            ink = contrast > 48 if group == "PP" else contrast < -48
            if group == "PP":
                # The later red triangles overprint the centers of the blue circles.
                # Recover the center from surviving upper arcs. The isolated first
                # blue marker has a diameter of 17 pixels on its central column.
                candidates = []
                for dx in range(-7, 8):
                    line = image[y - 14 : y + 15, x + dx]
                    visible = np.flatnonzero(line[:, 2] - line[:, 0] > 48)
                    if visible.size:
                        candidates.append(y - 14 + visible[0] + np.sqrt(8.5**2 - dx**2))
                yy.append(float(np.median(sorted(candidates)[:3])) if candidates else None)
            else:
                marker = np.where(ink)[0]
                yy.append(float(y - 11 + np.median(marker)) if marker.size else None)
        result[group] = [None if y is None else float(np.clip((358 - y) / 293, 0.0, 1.0)) for y in yy]
    return result


def observed(k, n):
    ci = binomtest(k, n).proportion_ci(method="exact")
    return {"opposite": k, "total": n, "fraction": k / n, "exact_95": [float(ci.low), float(ci.high)]}


def run(raw, out):
    article = ET.fromstring(sources.read(raw, "kimura.xml"))
    content = " ".join(" ".join(article.itertext()).split())
    if "3/84" not in content or "7/69" not in content or "n = 20" not in content or "n = 23" not in content:
        raise ValueError("Published cohort counts not found")
    image = pdf_figure(sources.read(raw, "kimura.pdf"), 5, 22)
    curves = panel_a(image)
    stages, discrepancies = {}, []
    for i, (stage, axes, den) in enumerate(zip(TIMES, AXES, DENOMINATORS, strict=True)):
        heights = histogram(image, axes)
        counts = np.rint(heights).astype(int)
        pp, dp = den
        # B's left ten bins are the distal half; the right ten are the proximal half.
        errors = [int(counts[:10, 0].sum()), int(counts[10:, 1].sum())]
        fractions = (errors[0] / pp, errors[1] / dp)
        for g, rate in zip(("PP", "DP"), fractions):
            a = curves[g][i]
            if a is not None:
                discrepancies.append(abs(a - rate))
        stages[stage] = {
            "axis": axes,
            "printed_PP_DP": den,
            "recovered_histogram_totals": counts.sum(0).tolist(),
            "bins_100_to_0_PP_DP": counts.tolist(),
            "wrong_half_PP_DP": errors,
            "relative_to_printed_denominator": fractions,
            "always_entry_side_errors": dp,
            "cue_side_errors": sum(errors),
            "accuracy": 1 - sum(errors) / (pp + dp),
            "always_entry_side_accuracy": pp / (pp + dp),
            "balanced_accuracy": 1 - sum(fractions) / 2,
        }
    matches = [s["recovered_histogram_totals"] == list(s["printed_PP_DP"]) for s in stages.values()]
    summary = {
        "experiment": "E53",
        "doi": "10.1091/mbc.E20-01-0058",
        "source_pdf_page_one_based": 6,
        "stages": stages,
        "independent_panel_A_reread_error_fraction": curves,
        "max_abs_discrepancy_between_panels": max(discrepancies),
        "stages_matching_all_printed_totals": sum(matches),
        "last_histogram_limitation": "At 140 counts per axis, bars can be under two pixels per embryo. Report printed denominators; verify wrong halves against panel A.",
        "separate_source_cohorts": {
            "wildtype_self": observed(3, 84),
            "wildtype_mated": observed(7, 69),
            "unc_116": observed(0, 20),
            "yop_1_ret_1": observed(0, 23),
        },
        "motion_correlation": {"direction": 0.48, "speed": 0.48, "frames": 69, "zygotes": 5},
        "checks": {
            "embedded_image_dimensions": image.shape[:2] == (2902, 2333),
            "seven_stages_and_two_types": len(stages) == 7 and len(curves["DP"]) == 7,
            "first_six_histograms_recover_both_printed_denominators": all(matches[:6]),
            "independent_panel_agrees_to_two_percentage_points": max(discrepancies) < 0.02,
            "final_no_wrong_half_bars": stages[TIMES[-1]]["wrong_half_PP_DP"] == [0, 0],
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
