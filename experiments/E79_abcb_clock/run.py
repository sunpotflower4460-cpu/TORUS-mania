"""E79: descriptive clock/amplitude contrasts with unidentified biological units."""

from pathlib import Path

from experiments.abcb_source import (
    BASE_COMMIT, ROOT, Sources, compare, decimal_description, describe, extract,
    numeric_error, parser, registration, save_result, verify_headers,
)

CONTRACTS = (
    ("Figure 2", ("G78:G173", "H78:H166")),
    ("Figure 2", ("K78:K97", "L78:L97")),
    ("Figure 6", ("G63:G159", "H63:H127")),
    ("Figure 6", ("K63:K88", "L63:L85")),
)


def run(out, sources):
    registered = registration("E79")
    datasets, numerical_checks, errors = {}, {}, []
    for sheet, ranges in CONTRACTS:
        definition = sources.by_ranges(sheet, ranges)
        workbook = sources.workbook(definition)
        headers = verify_headers(workbook, definition)
        groups, independent = {}, {}
        for group in definition["groups"]:
            values, decimals, info = extract(workbook, sheet, group)
            stats, reference = describe(values), decimal_description(decimals)
            error = numeric_error(stats, reference)
            errors.append(error)
            groups[group["id"]] = {**info, "statistics": stats,
                                    "independent_statistic_max_scaled_difference": error}
            independent[group["id"]] = reference
        intervention = next(key for key in groups if key != "wt")
        contrast = compare(groups["wt"]["statistics"], groups[intervention]["statistics"])
        independent_contrast = compare(independent["wt"], independent[intervention])
        contrast_error = numeric_error(contrast, independent_contrast)
        errors.append(contrast_error)
        datasets[definition["id"]] = {
            "panel": definition["panel"], "measure": definition["measure"],
            "unit": definition["unit"], "age_days": definition["age_days"],
            "source": sources.provenance(definition), "headers": headers,
            "groups": groups, "comparison": contrast,
            "comparison_numerator": intervention, "comparison_denominator": "wt",
            "independent_contrast_max_scaled_difference": contrast_error,
            "excluded_summary_cells": definition.get("excluded_summary_cells", []),
            "unit_audit": {
                "descriptive_unit": "numeric entries in the published source table",
                "root_id_available": definition["root_id_available"],
                "batch_id_available": definition["batch_id_available"],
                "cross_measure_pairing_identified": definition["cross_measure_pairing_identified"],
                "root_level_effect_and_equivalence": "not_identifiable_without_unit_ids",
                "count_mismatch_is_not_proof_of_original_analysis_error": True,
            },
        }
        prefix = definition["id"]
        numerical_checks[prefix + "_headers_match_manifest"] = all(h["matches_manifest"] for h in headers)
        numerical_checks[prefix + "_registered_counts_and_cell_types"] = all(
            groups[g["id"]]["n_numeric_values"] == g["n_values"]
            and groups[g["id"]]["xml_cell_type_counts"] == g["xml_cell_type_counts"]
            for g in definition["groups"])
        numerical_checks[prefix + "_independent_statistics_and_ratios"] = contrast_error < 1e-12 and all(
            g["independent_statistic_max_scaled_difference"] < 1e-12 for g in groups.values())
    summary = {
        "experiment": "E79", "base_commit": BASE_COMMIT, "registration": registered,
        "analysis_type": "retrospective_descriptive_reanalysis_of_published_author_tables",
        "study_doi": "10.15252/embr.202256271", "datasets": datasets,
        "statistic_definitions": {
            "weighting": "Equal weight per published numeric entry; no reconstruction of root-level weights.",
            "standard_deviation": "Sample standard deviation, denominator n-1; descriptive dispersion, not standard error.",
            "quartiles": "Linear interpolation at (n-1)*q (inclusive/type 7), q=0.25 and 0.75.",
            "geometric_mean": "exp(mean(log(value))) only if every value in the group is positive.",
            "ratio": "Intervention group center divided by its own figure's WT center.",
        },
        "observation_method": {
            "age_days": 3, "frame_interval_minutes": 15, "exposure_minutes": 7,
            "reporter": "DR5:LUC auxin-response reporter",
            "amplitude": "Movie maximum minus minimum of the ROI mean signal (ADU per pixel), in a square ROI selected where a prebranch site forms.",
            "period": "Frames between reporter maxima in the oscillation zone.",
            "source": "Chen 2023 article Methods p.12; Fig.2 I/J and Fig.6 G/H captions.",
        },
        "root_level_inference": {
            "status": "not_identifiable_without_unit_ids",
            "confidence_intervals": None, "p_values": None, "equivalence_test": None,
            "ICC_sensitivity": None, "independent_row_intervals": None,
            "E78_period_ratio_exclusion": "not_assessed",
            "reason": "Root/event/batch links and non-detected or excluded events are unavailable. Row-weighted centers need not equal equally weighted root centers.",
        },
        "scope_limits": [
            "Fig.2 and Fig.6 are two comparisons in one published study, not two independent studies.",
            "No rows are paired across groups or between amplitude and period; no root or batch IDs are invented.",
            "A descriptive period ratio near one is not biological equivalence or proof of a constant period.",
            "No correction for weak-event selection, missing events, reporter delay or ROI selection is fitted.",
            "Reporter contrasts do not measure same-molecule return time or establish autonomous circulation or a physical torus.",
        ],
        "reproduction": {
            "primary": "ElementTree OOXML extraction; float/math.fsum/statistics aggregation.",
            "independent": "minidom re-read of the same registered cells; 50-digit Decimal mean, SD and geometric mean.",
            "maximum_scaled_statistic_or_ratio_difference": max(errors),
            "original_workbooks_modified": False, "individual_values_redistributed": False,
        },
        "checks": {"registration_bytes_match_public_commit": True,
                   "all_source_and_inner_workbook_hashes_match": True,
                   "four_registered_panels_recorded": len(datasets) == 4,
                   **numerical_checks},
    }
    save_result(out, summary, __file__)
    return summary


if __name__ == "__main__":
    args = parser(__doc__, ROOT / "research/results/E79").parse_args()
    run(args.out, Sources(args.cache, args.offline))

