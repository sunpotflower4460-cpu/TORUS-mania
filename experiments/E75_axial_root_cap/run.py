"""Compare axial tracer polarity with and without the maize root cap."""

from experiments import calibrated_formation_sources as inputs
from experiments.common import save_summary

# Pages 892–893, Tables I–III. Means and SE, each (apical, basal, printed B/A).
CAP = {
    "control_ph6": ((1615, 99), (10219, 724), 6.3),
    "control_ph4_5": ((1260, 53), (8180, 801), 6.5),
    "aluminum_chloride_5_mM": ((3758, 218), (8012, 744), 2.1),
    "calcium_chloride_5_mM": ((1871, 55), (14253, 1409), 7.6),
    "potassium_chloride_5_mM": ((1111, 39), (6051, 556), 5.4),
    "lanthanum_chloride_5_mM": ((5314, 560), (7757, 895), 1.5),
    "magnesium_chloride_5_mM": ((1101, 49), (8594, 938), 7.8),
    "egta_5_mM": ((1219, 31), (4487, 963), 3.7),
    "chlorpromazine_10_uM": ((1518, 45), (9067, 1219), 6.0),
}
NO_CAP = {
    "control_ph6": ((13982, 643), (8867, 475), 0.63),
    "control_ph4_5": ((10422, 625), (7377, 342), 0.71),
    "aluminum_chloride_5_mM": ((17489, 574), (15974, 1322), 0.91),
    "calcium_chloride_5_mM": ((17408, 1324), (13799, 836), 0.79),
}
IAA_PERCENT = {
    "control_ph6": ((1.17, 0.07), (6.82, 0.53), 5.83),
    "control_ph4_5": ((0.93, 0.04), (5.16, 0.46), 5.55),
    "aluminum_chloride_5_mM": ((2.26, 0.45), (4.33, 0.35), 1.92),
    "calcium_chloride_5_mM": ((1.25, 0.16), (8.78, 0.92), 7.02),
}
ABA_PERCENT = {
    "control_ph6": ((0.75, 0.03), (0.72, 0.05), 0.96),
    "control_ph4_5": ((0.72, 0.05), (0.76, 0.09), 1.06),
    "aluminum_chloride_5_mM": ((0.75, 0.04), (0.73, 0.06), 0.97),
    "calcium_chloride_5_mM": ((0.80, 0.04), (0.97, 0.03), 1.21),
}


def polarity(rows):
    return {
        cond: {
            "toward_tip_mean": tip[0],
            "toward_tip_se": tip[1],
            "toward_shoot_mean": shoot[0],
            "toward_shoot_se": shoot[1],
            "toward_shoot_to_toward_tip_ratio_of_reported_means": shoot[0] / tip[0],
            "printed_ratio": printed,
        }
        for cond, (tip, shoot, printed) in rows.items()
    }


def fold_changes(first, second):
    keys = (
        "toward_tip_mean",
        "toward_shoot_mean",
        "toward_shoot_to_toward_tip_ratio_of_reported_means",
    )
    return {k: first[k] / second[k] for k in keys}


def run(raw, out):
    files = tuple(f"hasenstein-p{p}.png" for p in range(890, 894))
    provenance = inputs.verified_inputs(raw, files)
    cap, no_cap = polarity(CAP), polarity(NO_CAP)
    iaa, aba = polarity(IAA_PERCENT), polarity(ABA_PERCENT)
    summary = {
        "experiment": "E75",
        "doi": "10.1104/pp.86.3.890",
        "inputs_sha256": provenance,
        "root": "Zea mays B73 x Missouri 17 apical root segments",
        "assay_duration_hours": 3,
        "reported_apical_segment_length_mm": 5,
        "applied_iaa_tracer": "tritiated IAA; chemical identity in recovered fractions assumed by the authors",
        "reported_replications": {"repetitions": 3, "replicates_per_repetition": 3},
        "table_1_cap_present_dpm": cap,
        "table_2_cap_removed_dpm": no_cap,
        "removed_to_present_fold_change": {
            cond: fold_changes(row, cap[cond]) for cond, row in no_cap.items()
        },
        "treatment_to_matching_control_fold_change": {
            prep: {
                "aluminum_chloride": fold_changes(
                    row["aluminum_chloride_5_mM"], row["control_ph4_5"]
                ),
                "calcium_chloride": fold_changes(
                    row["calcium_chloride_5_mM"], row["control_ph6"]
                ),
            }
            for prep, row in (("cap_present", cap), ("cap_removed", no_cap))
        },
        "table_3_cap_present_percent_of_uptake": {"IAA": iaa, "ABA": aba},
        "interpretation_limits": [
            "Acropetal (tipward) donor on the basal cut surface; basipetal (shootward) donor on the tip.",
            "Decapping changes the apical contact surface of both preparations.",
            "Opposite directions are measured in separate segments, and do not form a joint trajectory.",
            "pH is a control for Al precipitation; the design does not separate all cap physiology from contact geometry.",
            "Table 3 is expressed as percent of uptake. It uses a separate denominator from Tables 1 and 2.",
        ],
        "checks": {
            "table_1_and_2_recomputed_ratios_round_as_printed": all(
                abs(
                    row["toward_shoot_to_toward_tip_ratio_of_reported_means"]
                    - row["printed_ratio"]
                )
                <= tolerance
                for table, tolerance in ((cap, 0.05), (no_cap, 0.005))
                for row in table.values()
            ),
            "table_3_ratios_consistent_with_rounding_of_both_displayed_means": all(
                abs(
                    row["toward_shoot_to_toward_tip_ratio_of_reported_means"]
                    - row["printed_ratio"]
                )
                < 0.015
                for table in (iaa, aba)
                for row in table.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, inputs.__file__)
