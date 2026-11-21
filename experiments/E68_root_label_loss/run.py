"""Read the paired isotope envelopes and re-entry controls in maize roots."""

import json
from itertools import product

import numpy as np
from PIL import Image

from experiments import iaa_embryo_sources as sources
from experiments.common import save_summary

PANEL_AXES = {
    "no_tissue": (2, 135),
    "terminal_mm_with_cap": (169, 300),
    "terminal_mm_without_cap": (329, 461),
    "subtending_root": (496, 629),
}
X_START, X_END = 59, 391


def connected_height(mask, gap):
    """Find the uppermost polygon pixel connected to the axis within each column."""
    heights = np.zeros(mask.shape[1])
    for col, pixels in enumerate(mask.T):
        locations = np.flatnonzero(pixels[::-1])
        breaks = np.flatnonzero(np.diff(np.r_[-1, locations]) > gap + 1)
        stop = breaks[0] if breaks.size else len(locations)
        if stop:
            heights[col] = locations[stop - 1] + 1
    return heights


def measure_panel(image, top, baseline, dark, white, gap):
    outline = image[top + 5 : baseline, X_START:X_END]
    recovered = connected_height(outline < dark, gap)
    extrapolated = connected_height((outline < dark) | (outline >= white), gap)
    lost = float((extrapolated.sum() - recovered.sum()) / extrapolated.sum())
    return lost, recovered, extrapolated


def check_image(image):
    result = {}
    for name, (top, base) in PANEL_AXES.items():
        lost, actual, counterfactual = measure_panel(image, top, base, 120, 240, 2)
        estimates = [
            measure_panel(image, top, base + offset, dark, white, gap)[0]
            for dark, white, gap, offset in product(
                (110, 120, 130), (235, 240, 245), (1, 2), (-1, 0, 1)
            )
        ]
        result[name] = {
            "fractional_14C_loss_of_displayed_envelope": lost,
            "range_varying_mask_thresholds_and_baseline": [
                min(estimates),
                max(estimates),
            ],
            "mean_over_columns_14C_profile_height_pixels": float(actual.mean()),
            "mean_over_columns_no_loss_profile_height_pixels": float(
                counterfactual.mean()
            ),
            "x_start_source_pixel": X_START,
            "actual_profile_height_pixels": actual.tolist(),
            "no_loss_profile_height_pixels": counterfactual.tolist(),
        }
    return result


def verify_abstract(path, expected):
    record = json.loads(path.read_text())
    if record["doi"].lower() != expected.lower():
        raise ValueError("The article does not match the registered DOI")
    return record


def run(raw, out):
    with Image.open(sources.source(raw, "kerk-figure8.jpg")) as image:
        fig = np.array(image.convert("L"))
    panels = check_image(fig)
    paper = verify_abstract(
        sources.source(raw, "wilkins-abstract.json"), "10.1007/BF00384767"
    )
    article = paper["abstractText"]
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E68",
            "dois": ["10.1104/pp.122.3.925", "10.1007/BF00384767"],
            "maize_kerk_figure_8": {
                "interpretation": "Black is measured carboxyl-14C signal. The outer contour adds the expected signal computed from the 5-3H tag under no decarboxylation. Area is digitized from a plotted chromatogram of pooled cut-root samples, without replication-level uncertainties. The full dosed tracer and the chromatogram area have different denominators.",
                "hours_after_input": 12,
                "text_reports_at_least_30_percent_loss_in_terminal_mm": True,
                "panels": panels,
            },
            "maize_wilkins_abstract_only": {
                "publication_year": int(paper["pubYear"]),
                "receiver_decline_starts_at_25C_hours": [6, 8],
                "receiver_withdrawn_for_comparison_at_hours": 8,
                "receiver_removed_or_kept_in_contact": "receiver declined after a period of transport; the removed receiver showed little to no decline",
                "where_resorbed_label_found_apical_distance_mm": [2, 4],
                "net_export_continued_at_10C_at_least_hours": 50,
                "CO2_loss_started_for_IAA_1_14C_hours": [6, 8],
                "CO2_loss_started_for_IAA_2_14C_hours": [10, 12],
                "scope": "Root segments, donor on one cut end and receiver on the other. Re-entry of label from an external receiver, without observed endogenous outer layer route or recovery as free IAA.",
            },
            "scope": "Independent maize studies of isotope fate and resorption. Neither follows recovered free IAA through an internal sequence and back to its start.",
            "checks": {
                "image_matches_registered_axes": fig.shape == (672, 402)
                and all(
                    np.mean(fig[base, 57:392] < 125) > 0.97
                    for _, base in PANEL_AXES.values()
                ),
                "abstract_reports_receiver_removal_and_local_reabsorption": all(
                    value in article
                    for value in ("placed on planchettes", "2-4 mm", "resorption")
                ),
                "no_extrapolated_profile_smaller_than_observed": all(
                    np.all(
                        np.array(panel["no_loss_profile_height_pixels"])
                        >= np.array(panel["actual_profile_height_pixels"])
                    )
                    for panel in panels.values()
                ),
            },
        },
        __file__,
        sources.__file__,
    )
