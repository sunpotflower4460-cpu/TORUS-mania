"""E80: registered radiotracer summaries and transport/growth/clock linkage audit."""

import math

from experiments.abcb_source import (
    BASE_COMMIT, ROOT, Sources, compare, decimal_description, describe, extract,
    numeric_error, parser, registration, save_result, verify_headers,
)


def metadata_audit(sources):
    items = {d["id"]: d for d in sources.manifest["datasets"]}
    tracer, induced = items["fig4A_shootward_transport"], items["fig4C_induced_auxin_reporter"]
    return {
        "source_schema_note": "research/notes/chen_2023_source_schema.md",
        "source_access_record": "research/access/2026-11-22-abcb-clock.md",
        "measurements": [
            {"id": "radiotracer_transport", "panel": "4A", "genotypes": ["WT", "amiR-2572"],
             "observed_quantity": "Recovered radiolabel, dpm, after application to the root tip",
             "direction": tracer["direction"], "age_days": tracer["age_days"],
             "root_count_per_pool": tracer["root_count_per_pool"],
             "assay_duration_minutes": tracer["assay_duration_minutes"],
             "sampled_segment_geometry": tracer["sampled_segment_geometry"],
             "replicate_unit": tracer["observation_unit"],
             "chemical_identity_limit": tracer["chemical_identity_limit"],
             "evidence": ["chen2023_manifest.json:fig4A_shootward_transport", "article pp.8,13"],
             "protocol_doi": tracer["cited_protocol_doi"],
             "protocol_import_policy": tracer["protocol_import_policy"]},
            {"id": "induced_auxin_response", "panel": "4C", "age_days": induced["age_days"],
             "observed_quantity": "DR5:VENUS fluorescence in elongation-zone epidermal cells after QC-specific auxin synthesis induction",
             "treatment": induced["intervention"], "times_hours": [0, 7.5, 9],
             "source_cell_counts": {g["id"]: g["n_values"] for g in induced["groups"]},
             "seedlings_minimum_by_time": induced["seedlings_minimum_by_time"],
             "root_id_available": False, "same_seedlings_followed_over_time_not_established": True,
             "is_direct_flux_measurement": False, "new_value_aggregation": False,
             "headers": verify_headers(sources.workbook(induced), induced),
             "evidence": ["chen2023_manifest.json:fig4C_induced_auxin_reporter", "article Fig.4 caption p.8"]},
            {"id": "meristem_and_LRC_shape", "panels": ["2D", "2E", "2F"], "age_days": 5,
             "observed_quantities": ["QC-to-first-elongating-cortical-cell distance", "LRC cell number", "distal LRC cell length"],
             "clock_age_days": 3, "same_root_same_time_as_clock": "not_established",
             "is_mature_cortical_cell_length": False, "is_growth_velocity": False,
             "is_cell_production_rate": False, "new_value_aggregation": False,
             "evidence": ["chen2023_manifest.json:fig2D_meristem_length,fig2E_lrc_cell_number,fig2F_distal_lrc_length", "article Fig.2 caption p.6"]},
            {"id": "appendix_growth_context", "panels": ["S9B", "S9C", "S9E", "S9F"],
             "source_metadata": [{"dataset_id": d["id"], "age_days": d.get("age_days"),
                                  "measure": d["measure"], "unit": d["unit"]}
                                 for d in items.values() if d["id"].startswith("appendixS9")],
             "is_same_age_cell_production_measurement": False, "new_value_aggregation": False,
             "evidence": ["chen2023_manifest.json:appendixS9 datasets", "article appendix Fig.S9"]},
            {"id": "outer_tissue_specific_clock", "panels": ["6G", "6H"], "age_days": 3,
             "genotypes": ["WT", "syn-tasi-1522A#1"],
             "direct_transport_in_same_tissue_specific_line": tracer["tissue_specific_syntasi_assayed"],
             "transport_figure_genotype": "global amiR-2572, not the tissue-specific line",
             "root_id_available": False, "new_value_aggregation": "E79 only",
             "evidence": ["chen2023_manifest.json:fig6G_clock_period,fig6H_clock_amplitude", "article Fig.6 caption p.10"]},
        ],
        "identifiability": [
            {"target": "root_level_clock_equivalence", "status": "not_identified",
             "missing": ["root/event/batch mapping", "exclusion and non-detection records"]},
            {"target": "within_root_transport_amplitude_period_mediation", "status": "not_identified",
             "missing": ["matched transport and clock measurements in the same roots"]},
            {"target": "transport_effect_at_fixed_cell_production", "status": "not_identified",
             "missing": ["same-condition same-age growth velocity", "mature cortical cell length or direct production rate"]},
            {"target": "E78_two_first_order_rate_multipliers", "status": "not_identified",
             "missing": ["mapping from recovered dpm to both model transport rates", "supply, retention, loss, geometry and time calibration"]},
            {"target": "same_molecule_complete_return_or_torus", "status": "not_measured",
             "missing": ["all loop segments", "molecular identity and complete-return trajectories", "three-dimensional geometry"]},
        ],
        "observation_selection": {
            "clock_reporter": "DR5:LUC response, not a direct count of transported IAA",
            "amplitude_definition": "Movie max-minus-min of the ROI mean signal (ADU per pixel), in a square ROI selected where a PBS forms",
            "period_definition": "Frames between OZ reporter maxima", "frame_minutes": 15,
            "exposure_minutes": 7, "raw_movie_and_peak_identity_available": False,
            "correction_for_missing_events_performed": False,
            "E32_relation": "No new Bernoulli thinning or detection model is added.",
            "evidence": ["article Methods p.12", "chen2023_manifest.json:clock_methods"],
        },
        "scope": "This is a provenance/identifiability audit, not a new growth or oscillation model.",
    }


def run(out, sources):
    registered = registration("E80")
    definition = sources.by_ranges("Figure 4", ("B4:B6", "C4:C6", "D4:D7", "E4:E6"))
    workbook = sources.workbook(definition)
    headers = verify_headers(workbook, definition)
    cells = workbook.sheet(definition["sheet"])
    groups, references, summaries, errors = {}, {}, {}, []
    for group in definition["groups"]:
        values, decimals, info = extract(workbook, definition["sheet"], group)
        stats, reference = describe(values), decimal_description(decimals)
        # E80 registers arithmetic summaries only.  The helper's other summaries are not emitted.
        arithmetic = {key: stats[key] for key in ("n", "arithmetic_mean", "sample_standard_deviation")}
        arithmetic_reference = {key: reference[key] for key in ("arithmetic_mean", "sample_standard_deviation")}
        error = numeric_error(arithmetic, arithmetic_reference)
        errors.append(error)
        groups[group["id"]] = {**info, "statistics": arithmetic,
                                "independent_statistic_max_scaled_difference": error}
        references[group["id"]] = arithmetic_reference
        column = group["range"].split(":")[0][:-1]
        mean_cell, spread_cell = column + "8", column + "9"
        published_mean, published_spread = float(cells[mean_cell]["text"]), float(cells[spread_cell]["text"])
        sd = arithmetic["sample_standard_deviation"]
        sem = sd / math.sqrt(len(values))
        matches_sem = math.isclose(published_spread, sem, rel_tol=1e-9, abs_tol=1e-9)
        matches_sd = math.isclose(published_spread, sd, rel_tol=1e-9, abs_tol=1e-9)
        summaries[group["id"]] = {
            "mean_cell": mean_cell, "published_mean": published_mean,
            "recomputed_mean": arithmetic["arithmetic_mean"],
            "mean_absolute_difference": abs(published_mean - arithmetic["arithmetic_mean"]),
            "spread_cell": spread_cell, "row_label": cells["A9"]["text"],
            "published_spread": published_spread, "recomputed_sample_SD": sd,
            "recomputed_sample_SD_over_sqrt_n": sem,
            "absolute_difference_from_SD": abs(published_spread - sd),
            "absolute_difference_from_SD_over_sqrt_n": abs(published_spread - sem),
            "matches_sample_SD": matches_sd, "matches_sample_SD_over_sqrt_n": matches_sem,
            "diagnosis": "matches_both" if matches_sem and matches_sd else
                         "matches_SD_over_sqrt_n" if matches_sem else "matches_sample_SD" if matches_sd else "matches_neither",
            "original_summary_cells_modified": False,
        }
    contrasts = {}
    for chemical in ("iaa", "ba"):
        control, intervention = "wt_" + chemical, "amir_" + chemical
        result = compare(groups[control]["statistics"], groups[intervention]["statistics"])
        result.pop("geometric_mean_ratio_intervention_over_WT")
        independent = compare(references[control], references[intervention])
        independent.pop("geometric_mean_ratio_intervention_over_WT")
        error = numeric_error(result, independent)
        errors.append(error)
        contrasts[chemical.upper()] = {**result, "control": control, "intervention": intervention,
                                      "independent_contrast_max_scaled_difference": error}
    audit = metadata_audit(sources)
    summary = {
        "experiment": "E80", "base_commit": BASE_COMMIT, "registration": registered,
        "analysis_type": "published_radiotracer_descriptive_summary_and_identifiability_audit",
        "study_doi": "10.15252/embr.202256271",
        "transport": {"panel": "4A", "unit": "dpm", "source": sources.provenance(definition),
                      "headers": headers, "groups": groups, "comparisons": contrasts,
                      "excluded_summary_cells": definition["excluded_summary_cells"],
                      "replicate_unit": definition["observation_unit"]},
        "published_summary_cell_audit": {
            "groups": summaries,
            "interpretation": "Compare the original row labelled S.E. separately with sample SD and SD/sqrt(n). A label/value mismatch is recorded, not silently repaired. These summary cells are excluded from all observation aggregates and do not affect the arithmetic mean ratios.",
        },
        "measurement_linkage_audit": audit,
        "inference": {"paired_tests": None, "causal_transport_period_coefficient": None,
                      "fixed_cell_production_effect": None, "E78_model_rate_conversion": None,
                      "new_growth_or_oscillation_model": False},
        "structural_clarification": "Registration's workbook '4A' means the panel heading. The original ZIP member is Figure 4.xlsx and its sole worksheet is Figure 4. Registered cell ranges are unchanged.",
        "reproduction": {"independent": "minidom OOXML reread and 50-digit Decimal mean/SD/ratios",
                         "maximum_scaled_statistic_or_ratio_difference": max(errors),
                         "all_individual_values_redistributed": False,
                         "original_workbooks_modified": False},
        "checks": {
            "registration_bytes_match_public_commit": True,
            "original_archive_and_internal_workbook_hashes_match": True,
            "Fig4A_headers_match_manifest": all(h["matches_manifest"] for h in headers),
            "four_registered_source_groups_recorded": len(groups) == 4,
            "registered_cell_counts_and_types_match": all(
                groups[g["id"]]["n_numeric_values"] == g["n_values"] and
                groups[g["id"]]["xml_cell_type_counts"] == g["xml_cell_type_counts"] for g in definition["groups"]),
            "independent_descriptive_statistics_and_ratios_match": max(errors) < 1e-12,
            "author_mean_and_spread_cells_are_finite": all(
                math.isfinite(x["published_mean"]) and math.isfinite(x["published_spread"]) for x in summaries.values()),
            "Fig4C_header_definitions_match_manifest": all(
                h["matches_manifest"] for h in audit["measurements"][1]["headers"]),
        },
    }
    save_result(out, summary, __file__)
    return summary


if __name__ == "__main__":
    args = parser(__doc__, ROOT / "research/results/E80").parse_args()
    run(args.out, Sources(args.cache, args.offline))

