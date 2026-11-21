"""Recompute what chemically intact IAA uptake can show in maize root segments."""

from experiments import iaa_embryo_sources as sources
from experiments.common import save_summary

# Martin and Pilet (1986), page 893 Table I, page 894 results.
# Tissue fresh mass is averaged per pool of 20 pieces.
TISSUES = {
    "stele": (22.0, 22.8, 0.61),
    "cortex": (89.2, 12.4, 0.64),
    "whole_2_to_7_mm_region": (112.0, 10.6, 0.68),
}


def tissue_uptake(mg_per_20_segments, amount_per_fresh_gram, saturable):
    return {
        "tissue_fresh_mass_mg_per_20_pieces": mg_per_20_segments,
        "pmol_per_g_fresh_mass_per_4min": amount_per_fresh_gram,
        "pmol_per_piece_per_4min": amount_per_fresh_gram
        * (mg_per_20_segments / 20)
        / 1000,
        "reported_saturable_fraction": saturable,
        "saturable_pmol_per_g_fresh_mass_per_4min": amount_per_fresh_gram * saturable,
        "nonsaturable_pmol_per_g_fresh_mass_per_4min": amount_per_fresh_gram
        * (1 - saturable),
    }


def run(raw, out):
    for page in (892, 893, 894):
        sources.source(raw, f"martin-p{page}.png")
    uptake = {k: tissue_uptake(*v) for k, v in TISSUES.items()}
    stele, cortex = uptake["stele"], uptake["cortex"]
    input_minor, extract_minor = 0.03, 0.08
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E71",
            "doi": "10.1104/pp.81.3.889",
            "source_pages_read": [892, 893, 894],
            "figure_4_and_page_892_hplc": {
                "elapsed_minutes": 4,
                "solvent_input_minor_peak_fraction": input_minor,
                "root_extract_minor_peak_fraction": extract_minor,
                "root_extract_major_peak_fraction_by_difference": 1 - extract_minor,
                "minor_peak_percentage_point_difference": (extract_minor - input_minor)
                * 100,
                "radioactivity_extracted_from_tissue_for_fig4b": 0.995,
                "root_major_peak_retention_time_minutes": 18.5,
                "minor_peak_retention_times_minutes": [14, 15, 16],
                "evidence": "The dominant peak of 5-tritium-labeled material co-elutes with an IAA standard. The extraction yield is the share of tissue radioactivity recovered, whereas the minor fraction is a share within the chromatogram.",
            },
            "table_i_and_page_894": {
                "input_IAA_total_molar": 1e-8,
                "uptake_over_4_minutes": uptake,
                "relative_stele_to_cortex": {
                    "fresh_mass_per_piece": stele["tissue_fresh_mass_mg_per_20_pieces"]
                    / cortex["tissue_fresh_mass_mg_per_20_pieces"],
                    "uptake_per_piece": stele["pmol_per_piece_per_4min"]
                    / cortex["pmol_per_piece_per_4min"],
                    "uptake_per_unit_fresh_mass": stele[
                        "pmol_per_g_fresh_mass_per_4min"
                    ]
                    / cortex["pmol_per_g_fresh_mass_per_4min"],
                },
                "scope": "Both isolated tissues from 5–10 mm. Whole segment comes from 2–7 mm. Relative per-mass uptake is not radial inward flux in an intact root.",
            },
            "checks": {
                "fresh_mass_required_for_reported_direction_of_tissue_difference": (
                    stele["pmol_per_piece_per_4min"] < cortex["pmol_per_piece_per_4min"]
                    and stele["pmol_per_g_fresh_mass_per_4min"]
                    > cortex["pmol_per_g_fresh_mass_per_4min"]
                ),
                "calculated_major_peak_is_between_90_and_95_percent": 0.90
                < 1 - extract_minor
                < 0.95,
            },
        },
        __file__,
        sources.__file__,
    )
