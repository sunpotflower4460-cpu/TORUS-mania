"""Localize the warm and cool ends of a published epiboly power display."""

from itertools import pairwise

import numpy as np
from matplotlib.colors import rgb_to_hsv
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, binary_erosion

from experiments import calibrated_formation_sources as inputs
from experiments.common import save_summary

# Image coordinates on the source JPEG. The poles have the same orientation in Fig. 2A.
OUTLINE = (
    (404, 246),
    (446, 287),
    (403, 326),
    (393, 324),
    (382, 313),
    (375, 300),
    (373, 287),
    (377, 274),
    (382, 263),
    (391, 253),
)
PANELS = ((40, 0, 5.3), (60, 97, 4.2), (80, 193, 1.7))
MIN_BRIGHTNESS = 0.20


def color_masks(rgb, contrast):
    hue, _, value = np.moveaxis(rgb_to_hsv(rgb / 255.0), -1, 0)
    hue *= 360
    colored = (np.ptp(rgb, axis=-1) >= contrast) & (value >= MIN_BRIGHTNESS)
    warm = colored & (hue <= 65)
    cool = colored & (hue >= 180) & (hue <= 270)
    return warm, cool


def silhouette(size, shift, adjustment):
    mask = Image.new("1", size)
    ImageDraw.Draw(mask).polygon([(x + shift, y) for x, y in OUTLINE], fill=1)
    region = np.asarray(mask)
    if adjustment < 0:
        return binary_erosion(region, iterations=-adjustment)
    if adjustment > 0:
        return binary_dilation(region, iterations=adjustment)
    return region


def location(mask):
    rows = np.nonzero(mask)[0]
    vertical = np.clip((rows - 246) / 80, 0.0, 1.0)
    n = len(vertical)
    thirds = np.histogram(vertical, [0, 1 / 3, 2 / 3, 1])[0]
    return {
        "pixel_count": n,
        "mean_vertical_position": float(vertical.mean()) if n else None,
        "top_middle_bottom_counts": thirds.tolist(),
        "top_middle_bottom_fractions": (thirds / n).tolist() if n else None,
    }


def score(warm, cool, size, adjustment):
    results = []
    for stage, shift, rmse in PANELS:
        roi = silhouette(size, shift, adjustment)
        results.append(
            {
                "epiboly_percent": stage,
                "printed_power_rmse_percent": rmse,
                "mask_pixel_count": int(roi.sum()),
                "warm_end": location(warm & roi),
                "cool_end": location(cool & roi),
            }
        )
    return results


def difference(later, earlier):
    return later - earlier if later is not None and earlier is not None else None


def run(raw, out):
    names = ("epiboly-fig2.jpg", "epiboly-fig4.jpg")
    provenance = inputs.verified_inputs(raw, names)
    with Image.open(raw / names[1]) as figure:
        rgb = np.asarray(figure.convert("RGB"))
        size = figure.size
    variants = []
    for contrast in (25, 35, 55):
        warm, cool = color_masks(rgb, contrast)
        for adjustment in (-2, 0, 2):
            stages = score(warm, cool, size, adjustment)
            positions = [row["warm_end"]["mean_vertical_position"] for row in stages]
            variants.append(
                {
                    "min_channel_range_8bit": contrast,
                    "mask_adjustment_px": adjustment,
                    "stages": stages,
                    "warm_centroid_ordered_40_60_80": all(
                        a is not None and b is not None and a < b
                        for a, b in pairwise(positions)
                    ),
                    "warm_centroid_80_minus_40": difference(positions[2], positions[0]),
                    "warm_centroid_80_minus_60": difference(positions[2], positions[1]),
                }
            )
    primary = next(
        row
        for row in variants
        if row["min_channel_range_8bit"] == 35 and row["mask_adjustment_px"] == 0
    )
    sample_warm, sample_cool = color_masks(
        np.array([[[235, 25, 15], [0, 0, 200], [100, 100, 100]]]), contrast=35
    )
    summary = {
        "experiment": "E73",
        "doi": "10.15252/embj.201694264",
        "inputs_sha256": provenance,
        "embryos_represented_in_figure_4d": 1,
        "stages_from_one_embryo_and_not_independent": [40, 60, 80],
        "panel_size_px": list(size),
        "outline_first_panel_xy_px": OUTLINE,
        "panel_x_offsets_px": [row[1] for row in PANELS],
        "vertical_coordinate": "(image y - 246)/80, clipped to [0,1], display only",
        "min_hsv_value": MIN_BRIGHTNESS,
        "warm_hue_deg": [0, 65],
        "cool_hue_deg": [180, 270],
        "primary": primary,
        "all_mask_and_color_threshold_variants": variants,
        "interpretation_limits": [
            "The printed palette shows warm positive and cool negative ends, with no calibrated zero.",
            "Display area and location are not measured watts, flux vectors or biological replicates.",
            "Hydrodynamic regression uses PIV from a 2D section and a symmetric spherical cortex model.",
            "Figure 2 serves only to verify the display axis orientation.",
        ],
        "checks": {
            "source_fig4_has_pinned_original_resolution": size == (652, 515),
            "classifier_separates_saturated_red_blue_and_neutral": (
                sample_warm.tolist() == [[True, False, False]]
                and sample_cool.tolist() == [[False, True, False]]
            ),
            "each_stage_has_classified_and_unclassified_pixels": all(
                0
                < row["warm_end"]["pixel_count"] + row["cool_end"]["pixel_count"]
                < row["mask_pixel_count"]
                for row in primary["stages"]
            ),
            "three_nonoverlapping_primary_mask_positions": bool(
                sum(silhouette(size, shift, 0) for _, shift, _ in PANELS).max() == 1
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, inputs.__file__)
