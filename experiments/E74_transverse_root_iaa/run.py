"""Reanalyse Lee and Evans's transverse label recovery in intact maize roots."""

from experiments import calibrated_formation_sources as inputs
from experiments.common import save_summary

# Values double-checked against the publisher's scanned tables (pp. 825–826).
# Triples of (receiver above mean, SD), (receiver below mean, SD), printed ratio.
RECEIVERS_90 = {
    "no_added_calcium": ((73, 15), (264, 41), 3.6),
    "receiver_10_mM_calcium_chloride": ((152, 24), (473, 28), 3.1),
}
SHORT = {
    "no_added_calcium": (
        30,
        ((4793, 582), (5189, 250), None),
        ((371, 17), (544, 58), 1.53),
        ((28, 2), (36, 5), None),
    ),
    "receiver_10_mM_calcium_chloride": (
        20,
        ((3782, 640), (4200, 722), None),
        ((87, 21), (267, 65), 3),
        ((10, 2), (17, 4), None),
    ),
}


def comparison(upper, lower, printed):
    return {
        "receiver_above_mean_cpm": upper[0],
        "receiver_above_sd_cpm": upper[1],
        "receiver_below_mean_cpm": lower[0],
        "receiver_below_sd_cpm": lower[1],
        "below_minus_above_cpm": lower[0] - upper[0],
        "below_to_above_ratio_of_reported_means": lower[0] / upper[0],
        "reported_polarity": printed,
    }


def run(raw, out):
    files = ("lee-p824.png", "lee-p825.png", "lee-p826.png")
    provenance = inputs.verified_inputs(raw, files)
    ninety = {condition: comparison(*data) for condition, data in RECEIVERS_90.items()}
    no_calcium, calcium = ninety.values()
    short = {
        condition: {
            "minutes": duration,
            "tissue_half_adjacent_to_donor": comparison(*donor_tissue),
            "tissue_half_adjacent_to_receiver": comparison(*receiver_tissue),
            "receiver_block": comparison(*receiver),
        }
        for condition, (
            duration,
            donor_tissue,
            receiver_tissue,
            receiver,
        ) in SHORT.items()
    }
    observed_time = {
        "no_added_calcium": {"tissue_half": 30, "receiver_block": 45},
        "receiver_10_mM_calcium_chloride": {"tissue_half": 20, "receiver_block": 30},
    }
    summary = {
        "experiment": "E74",
        "doi": "10.1104/pp.77.4.824",
        "inputs_sha256": provenance,
        "root": "Zea mays B73 x Missouri 17, intact primary root about 1.5 cm",
        "donor_receiver_geometry_mm_behind_tip": [3, 4.5],
        "applied_tracer": "[5-3H]IAA dosed externally on one side of the root",
        "table_i_at_90_min": ninety,
        "table_i_calcium_to_unsupplemented_fold_change": {
            direction: calcium[direction] / no_calcium[direction]
            for direction in (
                "receiver_above_mean_cpm",
                "receiver_below_mean_cpm",
                "below_to_above_ratio_of_reported_means",
            )
        },
        "table_ii_short_term_endpoints": short,
        "reported_detection_within_min": observed_time,
        "table_i_and_ii_reported_experiments_per_mean": 5,
        "decapped_horizontal": {
            "times_min": [45, 90],
            "reported_no_downward_preference_or_calcium_effect": True,
            "numerical_data_published": False,
        },
        "vertical_intact": {
            "time_min": 90,
            "approximately_cpm_above_background_either_calcium_condition": 95,
            "row_level_data_published": False,
        },
        "same_compound_assessment": {
            "duration_min": 180,
            "receiver_orientation": "below a horizontal root",
            "receiver_calcium_chloride_mM": 10,
            "approximate_extract_applied_to_chromatogram_dpm": 3000,
            "method": "TLC: the recovered zone co-migrated with donor and authentic IAA",
            "chromatogram_or_recovered_fraction_published": False,
        },
        "interpretation_limits": [
            "Opposite-side recovery had a chemical check in a separate, longer exposure.",
            "Individual cortical or central transits, intact chemical histories and return to the donor location were not measured.",
            "Shorter tissue observations differ in duration between calcium conditions.",
            "Scintillation cpm in the receiver is not the dpm of the supplied donor.",
        ],
        "checks": {
            "table_i_recomputed_ratios_match_rounding": all(
                round(row["below_to_above_ratio_of_reported_means"], 1)
                == row["reported_polarity"]
                for row in ninety.values()
            ),
            "earlier_tissue_readings_are_not_used_as_opposite_receiver_detections": (
                all(
                    row["minutes"]
                    == observed_time[cond]["tissue_half"]
                    < observed_time[cond]["receiver_block"]
                    for cond, row in short.items()
                )
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, inputs.__file__)
