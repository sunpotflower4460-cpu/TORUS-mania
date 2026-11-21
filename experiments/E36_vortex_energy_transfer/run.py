"""Score a fixed vortex-ring energy coefficient against public PIV figures."""

import argparse
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from experiments import return_energy_data as data
from experiments.common import save_summary

CAMBRIDGE = "https://static.cambridge.org/binary/version/id/urn:cambridge.org:id:"
JFM = CAMBRIDGE + "binary-alt:20211102033654-"
BASKARAN = CAMBRIDGE + "binary:20220630140740282-0747:S2633425922000095:S2633425922000095_fig7.png"
SOURCES = {
    "limbourg_f16.jpg": (JFM+"41747-optimisedImage-S0022112021000367_fig16.jpg",
                         "52d52c82b86514fceed86bb4d09365e7d5d4d3b60b7db9008714f49c3f485f1d"),
    "limbourg_f17.jpg": (JFM+"65203-optimisedImage-S0022112021000367_fig17.jpg",
                         "f9cc74e3df3e554c4a9bf67ef527cd390aafdb2ccd07156b3dcb2c3c53859f6f"),
    "limbourg_f18.jpg": (JFM+"81147-optimisedImage-S0022112021000367_fig18.jpg",
                         "41df849f7d6c4f5d2f4664d9ac83f07425347451647618972c20ba24ec532738"),
    "limbourg_f19.jpg": (JFM+"12139-optimisedImage-S0022112021000367_fig19.jpg",
                         "76623770ff18c0c432de944217f8844afef1596ce4d9da58f4ac7152e75598e4"),
    "baskaran_f7.png": (BASKARAN, "89bcfcf5a4ac0f63a1f53794aefa6cb2e6fc253a6ad4ec3d61dab19f4d891b83"),
}
CANONICAL = .33
ALPHA_ERROR_MARGIN = .05
PIXELS = 3.
RHO_KG_CM3 = .001
STROKES = np.arange(.5, 5.1, .5)
PROFILES = np.array([3.4, 3.9, 4.4, 4.9, 5.4, 5.9])

# Each figure has a different screen origin and its own labelled vertical scale.
# The short search windows distinguish black circle centers from open circles.
JFM_AXES = {
    "gamma": (16, 138., 116.8, 25.5, 457., 300., (406, 375, 349, 332, 313, 308, 303, 293, 294, 291)),
    "impulse": (17, 125.5, 116.7, 25.5, 457., 7., (428, 382, 338, 296, 253, 205, 179, 140, 144, 143)),
    "energy": (18, 132., 116.6, 25.5, 457.5, 50., (442, 403, 361, 315, 277, 246, 210, 192, 165, 144)),
    "alpha": (19, 134., 116.8, 65.5, 496., 1., (299, 334, 345, 357, 352, 345, 345, 362, 354, 363)),
}
ALPHA_FOV1_MARKER_ROWS = (293., 329., 356., 363., 383., 368., 367., 368., 369., 368.)


def circle_centres(pixels, x0, xunit, approximate):
    centres = []
    for index, y in enumerate(approximate):
        x = round(x0 + xunit * STROKES[index])
        dark = pixels[y-6:y+7, x-7:x+8].mean(axis=2) < 95
        interior = distance_transform_edt(dark)
        if interior.max() < 3:
            raise ValueError(f"No filled marker detected at ({x}, {y})")
        rows = np.where(interior == interior.max())[0]
        centres.append(y - 6 + float(rows.mean()))
    return np.array(centres)


def orifice(images):
    values = {}
    uncertainties = {}
    photo_rows = {}
    for name, (figure, x0, spacing, top, zero, top_value, expected) in JFM_AXES.items():
        image = images[f"limbourg_f{figure}.jpg"]
        right = image[:, image.shape[1]//2:]
        rows = circle_centres(right, x0, spacing, expected)
        factor = top_value / (zero - top)
        values[name] = (zero - rows) * factor
        uncertainties[name] = PIXELS * factor
        photo_rows[name] = rows.tolist()
    gamma, impulse, energy, direct = [values[k] for k in ("gamma", "impulse", "energy", "alpha")]
    normalization = np.sqrt(RHO_KG_CM3 * impulse * gamma**3)
    normalization_si = np.sqrt((100.**3 * RHO_KG_CM3) * (impulse / 100.) * (gamma / 100.**2)**3)
    assembled = energy / normalization
    predicted = CANONICAL * normalization
    cross_panel_delta = assembled - direct
    low = (energy - uncertainties["energy"]) / np.sqrt(
        RHO_KG_CM3 * (impulse + uncertainties["impulse"]) * (gamma + uncertainties["gamma"])**3
    )
    high = (energy + uncertainties["energy"]) / np.sqrt(
        RHO_KG_CM3 * (impulse - uncertainties["impulse"]) * (gamma - uncertainties["gamma"])**3
    )
    cross_panel_overlap = (low <= direct + uncertainties["alpha"]) & (high >= direct - uncertainties["alpha"])
    _, _, _, top, zero, _, _ = JFM_AXES["alpha"]
    fov1 = (zero - np.array(ALPHA_FOV1_MARKER_ROWS)) / (zero - top)
    rows = []
    for j, stroke in enumerate(STROKES):
        rows.append({
            "stroke_ratio": float(stroke), "circulation_cm2_per_s": float(gamma[j]),
            "impulse_kg_cm_per_s": float(impulse[j]), "global_kinetic_energy_J": float(energy[j] / 100.**2),
            "forecast_energy_J": float(predicted[j] / 100.**2), "relative_forecast_error": float(predicted[j] / energy[j] - 1),
            "alpha_from_three_separate_figures": float(assembled[j]), "alpha_read_fov2": float(direct[j]),
            "alpha_read_fov1": float(fov1[j]), "cross_panel_alpha_difference": float(cross_panel_delta[j]),
            "assembled_alpha_pixel_reading_range": [float(low[j]), float(high[j])],
            "alpha_overlap_between_panels_at_pixel_reading_range": bool(cross_panel_overlap[j]),
        })
    return {
        "all_stroke_ratios": rows, "filled_marker_rows": photo_rows,
        "digitization_half_width": uncertainties,
        "physical_units_conversion_max_rel_error": float(np.max(np.abs(normalization / 100.**2 / normalization_si - 1))),
        "reported_fov2_short_stroke": score(direct[STROKES < 3]),
        "reported_fov2_long_stroke": score(direct[STROKES >= 3]),
        "reported_fov1_long_stroke": score(fov1[STROKES >= 3]),
        "assembled_long_stroke": score(assembled[STROKES >= 3]),
        "assembled_energy_median_absolute_relative_error_long_stroke": float(
            np.median(np.abs(predicted[STROKES >= 3] / energy[STROKES >= 3] - 1))
        ),
        "max_cross_panel_alpha_difference": float(np.max(np.abs(cross_panel_delta))),
        "strokes_with_cross_panel_overlap_at_pixel_reading_range": int(np.sum(cross_panel_overlap)),
    }


def score(alpha):
    error = np.abs(alpha - CANONICAL)
    return {
        "points": len(alpha), "within_registered_band": int(np.sum(error <= ALPHA_ERROR_MARGIN)),
        "median_alpha": float(np.median(alpha)),
        "median_absolute_alpha_error": float(np.median(error)),
    }


def changing_jet(pixels):
    r, g, b = pixels[:, :pixels.shape[1]//2].transpose(2, 0, 1)
    masks = {
        "advected_boundary": (r < 130) & (b > r+15) & (b > g+35),
        "core_rectangle": (r < 80) & (g > 115) & (b > 105) & (np.abs(g-b) < 29),
    }
    results = {}
    for label, mask in masks.items():
        centre = []
        for stroke in PROFILES:
            x = round(231 + 120 * (stroke-2))
            rows = np.where(mask[130:400, x-2:x+3])[0]
            if len(rows) == 0:
                raise ValueError(f"No {label} curve at stroke {stroke}")
            centre.append(130 + float(np.median(rows)))
        # y=103 and y=342 are the 0.35 and 0.20 labelled ticks.
        alpha = .35 - (np.array(centre) - 103.) * .15 / (342. - 103.)
        results[label] = {
            "stroke_ratios": PROFILES.tolist(), "estimated_alpha": alpha.tolist(), "image_rows": centre,
            "late_compression": score(alpha[PROFILES >= 5]),
        }
    return results


def run(raw, out):
    images = {n: data.rgb(data.verified(raw/n, checksum)) for n, (_, checksum) in SOURCES.items()}
    circular = orifice(images)
    biomimetic = changing_jet(images["baskaran_f7.png"])
    report = {
        "experiment": "E36",
        "studies": ["10.1017/jfm.2022.275", "10.1017/jfm.2021.36", "10.1017/flo.2022.9"],
        "sources": {name: {"url": url, "sha256": digest} for name, (url, digest) in SOURCES.items()},
        "canonical_alpha": CANONICAL, "absolute_error_margin": ALPHA_ERROR_MARGIN,
        "orifice_water_density_assumption_kg_per_m3": 1000.,
        "orifice_piston": circular, "unsteady_biomimetic_generator": biomimetic,
        "baskaran_curve_alpha_readout_half_width": PIXELS * .15 / (342. - 103.),
        "cross_panel_note": "Assembly uses separate group summaries, not paired raw frames.",
        "checks": {
            "all_ten_orifice_strokes": len(circular["all_stroke_ratios"]) == 10,
            "dimensionally_consistent_energy": circular["physical_units_conversion_max_rel_error"] < 1e-12,
            "two_curves_at_each_scheduled_stroke": all(
                len(case["estimated_alpha"]) == len(PROFILES) for case in biomimetic.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=data.RAW)
    parser.add_argument("--out", type=Path, default=data.RESULTS/"E36")
    args = parser.parse_args()
    run(args.raw, args.out)
