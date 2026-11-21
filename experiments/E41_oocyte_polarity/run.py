"""Quantify early, late, and later-development endpoints in Lu et al."""

import argparse
from pathlib import Path

import numpy as np

from experiments import return_energy_data as data
from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/path_and_formation"
FIGURES = {
    "lu_fig3.jpg": ("https://cdn.ncbi.nlm.nih.gov/pmc/blobs/d9f7/6168253/d93f499eddb6/JCB_201709174_Fig3.jpg",
                    "681f53c244211b84259f96ff62beb0dcd067268499b20ca0ee10cebe7df8497b"),
    "lu_fig4.jpg": ("https://cdn.ncbi.nlm.nih.gov/pmc/blobs/d9f7/6168253/042f427943e1/JCB_201709174_Fig4.jpg",
                    "3ce39bb1af2b07d51544a1b0cedc3b771f2bb0cb63ef4eff97e00f4e55044e74"),
}
ARTICLE = "https://pmc.ncbi.nlm.nih.gov/articles/PMC6168253/"
# Figure 3 shows the hatched posterior fraction, from the bottom of each bar.
# Input labels are (group, n at stage 9, n at stage 10B, approximate % at each).
LOCALIZATION = (
    ("control", 42, 67, 100, 100),
    ("sliding_reduced_Khc_mutA", 23, 24, 96, 100),
    ("Khc_RNAi", 31, 33, 0, 0),
    ("cargo_transport_reduced", 75, 18, 0, 100),
    ("cargo_and_sliding_reduced", 15, 10, 0, 0),
    ("streaming_rescue", 43, 51, 44, 55),
)
# The percentages and denominators are printed as text in Fig. 4C and Table 1.
# The rescue percentage in Fig. 4C has an explicit stage-selection caveat.
POLE = (
    ("control", 42, 100.),
    ("sliding_reduced_Khc_mutA", 18, 88.9),
    ("cargo_transport_reduced", 39, 82.0),
    ("cargo_and_sliding_reduced", 20, 0.),
    ("Khc_RNAi", 28, 3.6),
    ("streaming_rescue", 35, 52.8),
)
HATCHING = (
    ("control", 463, 92.4),
    ("sliding_reduced_Khc_mutA", 172, 48.8),
    ("cargo_transport_reduced", 591, 19.1),
    ("cargo_and_sliding_reduced", 388, 0.),
    ("Khc_RNAi", 458, 0.),
    ("streaming_rescue", 358, .8),
    ("staufen_mutant", 205, 0.),
    ("staufen_suntag_rescue", 118, 82.2),
)
PROFILE_AXIS_ZERO = {
    "control": 197, "sliding_reduced_Khc_mutA": 367, "Khc_RNAi": 534,
    "cargo_transport_reduced": 1036, "cargo_and_sliding_reduced": 1205, "streaming_rescue": 1373,
}
PROFILE_POSITIONS = np.linspace(.28, .72, 89)


def read_profile(image, zero, pixel_darkness):
    unity = zero-127
    means = []
    for position in PROFILE_POSITIONS:
        x = round(632 + 149*position)
        drawn = np.where(image[unity+1:zero-1, x-1:x+2] < pixel_darkness)[0] + unity + 1
        # The figure plots its mean with a symmetric error bar. Use the
        # midpoint of its visible ink, allowing a small horizontal window.
        y = (drawn.min()+drawn.max())/2 if len(drawn) else zero
        means.append((zero-y)/(zero-unity))
    values = np.asarray(means)
    flank = (values[0]+values[-1])/2
    above = PROFILE_POSITIONS[values >= .5*(values.max()+flank)]
    return {
        "relative_cortex_positions": PROFILE_POSITIONS.tolist(), "approximate_mean": values.tolist(),
        "peak": float(values.max()), "flank_mean": float(flank),
        "width_at_half_peak_above_flanks": float(above[-1]-above[0]),
    }


def possible_integers(n, percent, tolerance):
    plausible = [count for count in range(n+1) if abs(100*count/n - percent) <= tolerance + 1e-12]
    if not plausible:
        return None
    return [min(plausible), max(plausible)]


def run(raw, out):
    fig3, fig4 = [data.rgb(data.verified(raw/file, sha)) for file, (_, sha) in FIGURES.items()]
    profiles = {}
    for name, zero in PROFILE_AXIS_ZERO.items():
        reads = [read_profile(fig3.mean(axis=2), zero, cutoff) for cutoff in (130,160,190)]
        base = reads[1]
        widths = [row["width_at_half_peak_above_flanks"] for row in reads]
        base["width_range_from_reading_thresholds"] = [min(widths), max(widths)]
        base["selected_rescued_oocytes_only"] = (name == "streaming_rescue")
        profiles[name] = base
    localization = {}
    for name, early, late, p1, p2 in LOCALIZATION:
        localization[name] = {
            stage: {"n_oocytes": n, "image_percent": percent,
                    "posterior_count_range_at_two_percentage_point_reading_width": possible_integers(n, percent, 2.)}
            for stage, n, percent in (("9", early, p1), ("10B", late, p2))
        }
    pole = {name: {"published_sample_n": n, "pole_cell_percent": p,
                   "early_arrest_affects_interpretation": name == "streaming_rescue"} for name, n, p in POLE}
    hatching = {name: {"all_eggs": n, "percent_hatched": p, "count_range_from_rounding": possible_integers(n,p,.05)}
                for name, n, p in HATCHING}
    summary = {
        "experiment": "E41", "study_doi": "10.1083/jcb.201709174",
        "three_dimensional_flow_context_doi": "10.1038/s41567-023-02372-1", "table_1_article": ARTICLE,
        "figures": {name: {"url": url, "sha256": sha} for name, (url,sha) in FIGURES.items()},
        "fig3_stages_and_staufen": localization, "fig3_approximate_stage10B_profiles": profiles,
        "fig4C_pole_cell_specification": pole, "table1_hatching": hatching,
        "checks": {
            "registered_original_figure_sizes": fig3.shape[:2] == (1402,800) and fig4.shape[:2] == (333,800),
            "finite_profiles_at_registered_locations": all(
                len(p["approximate_mean"]) == len(PROFILE_POSITIONS)
                and all(0 <= value <= 1 for value in p["approximate_mean"]) for p in profiles.values()
            ),
            "screened_oocyte_counts_consistent_with_image_resolution": all(
                r["posterior_count_range_at_two_percentage_point_reading_width"] is not None
                for rows in localization.values() for r in rows.values()
            ),
            "hatching_counts_consistent_with_reported_precision": all(
                row["count_range_from_rounding"] is not None for row in hatching.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E41")
    args = parser.parse_args()
    run(args.raw, args.out)
