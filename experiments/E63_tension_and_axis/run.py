"""Recompute membrane stiffness, incremental probe work and axis responses."""

from collections import defaultdict
from io import BytesIO
from zipfile import ZipFile

import numpy as np
from openpyxl import load_workbook
from scipy.stats import fisher_exact, ttest_ind

from experiments import embryo_history_sources as sources
from experiments.common import save_summary

PROBE_SPEED_MM_S = 0.1
LINEAR_WINDOW_S = 20


def extract(raw):
    with ZipFile(sources.source(raw, "kunz-source.zip")) as archive:
        workbook = load_workbook(
            BytesIO(archive.read("Source_Data.xlsx")), read_only=True, data_only=True
        )
        try:
            return {
                name: list(workbook[name].values)
                for name in ("Fig.1h,5h,s3d", "Fig.3d,e", "Fig.4b", "Fig.4e", "Table1")
            }
        finally:
            workbook.close()


def descriptive(values):
    values = np.asarray(values, dtype=float)
    return {
        "values": values.tolist(),
        "n": len(values),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "sample_sd": float(values.std(ddof=1)),
    }


def differences(control, intervention, rng):
    def resample(group):
        group = np.asarray(group)
        return rng.choice(group, size=(10000, len(group)), replace=True).mean(axis=1)

    distribution = resample(intervention) - resample(control)
    return {
        "control": descriptive(control),
        "intervention": descriptive(intervention),
        "intervention_minus_control": float(np.mean(intervention) - np.mean(control)),
        "groupwise_bootstrap_95_percent_interval": np.quantile(
            distribution, [0.025, 0.975]
        ).tolist(),
        "student_p_two_sided": float(ttest_ind(control, intervention).pvalue),
    }


def probe(rows):
    by_group = defaultdict(list)
    for row in rows:
        if isinstance(row[7], (int, float)) and isinstance(row[6], str):
            by_group[row[6]].append(row[7])
    # The pooled D0 column agrees with the figure mean and caption n.
    by_group["Day 0 (plotted)"] = by_group["Day 0"] + by_group["Day 0 - sw"]
    groups = {}
    displacement_mm = PROBE_SPEED_MM_S * LINEAR_WINDOW_S
    for group in ("Baseline", "Day 0 (plotted)", "Day 1", "Day 2", "Day 2 - sw"):
        rate = np.asarray(by_group[group])
        effective_gradient = rate / PROBE_SPEED_MM_S  # mN/mm = N/m
        # One mN mm = one µJ. Remove force at start of linear fitting segment.
        separate_force_increment_work = 0.5 * effective_gradient * displacement_mm**2
        groups[group] = {
            "force_rise_millinewton_per_second": descriptive(rate),
            "effective_probe_gradient_newton_per_meter": descriptive(
                effective_gradient
            ),
            "linear_increment_work_microjoule": descriptive(
                separate_force_increment_work
            ),
        }
    return {
        "probe_speed_mm_per_s": PROBE_SPEED_MM_S,
        "linear_fit_duration_seconds": LINEAR_WINDOW_S,
        "idealized_linear_displacement_mm": displacement_mm,
        "day_0_worksheet_labels_and_counts": {
            key: len(by_group[key]) for key in ("Day 0", "Day 0 - sw")
        },
        "groups": groups,
        "work_reference": "Integral of the fitted increment of probe force relative to the start of a 2 mm linear ramp. The absolute probe work needs the force offset and full force-displacement trace. In vivo energy transfer was not measured.",
    }


def inflation(rows):
    injections = [int(rows[index][2]) for index in (1, 2, 3)]
    series = [[row[0], row[1]] for row in rows[6:16]]
    intact_series = series[:-1]  # The publication's plotted curve ends at 115 s.
    changes = []
    for time in injections[:2]:
        before = max(pair for pair in intact_series if pair[0] < time)
        after = min(pair for pair in intact_series if pair[0] > time)
        changes.append(
            {
                "injection_s": time,
                "before_time_and_width_um": before,
                "after_time_and_width_um": after,
                "width_difference_um": after[1] - before[1],
            }
        )
    return {
        "published_injections_seconds": injections,
        "time_s_and_width_um_single_embryo": series,
        "last_value_not_plotted": series[-1],
        "change_across_first_and_second_inflation": changes,
    }


def ruptures(rows, intervention, control):
    counts = {
        row[1]: (int(row[6]), int(row[7]))
        for row in rows
        if row[1] in (control, intervention)
    }
    cases, treated_total = counts[intervention]
    baseline, control_total = counts[control]
    pvalue = fisher_exact(
        [[cases, treated_total - cases], [baseline, control_total - baseline]]
    )
    return {
        "control_cases_and_total": [baseline, control_total],
        "intervention_cases_and_total": [cases, treated_total],
        "risk_difference": cases / treated_total - baseline / control_total,
        "fisher_exact_p_two_sided": float(pvalue.pvalue),
    }


def run(raw, out):
    sources.source(raw, "kunz-fig1.jpg")
    data = extract(raw)
    rng = np.random.default_rng(631120)
    sandwich = data["Fig.3d,e"]
    sandwich_outcomes = {
        name: differences(
            *[
                [row[column] for row in sandwich if row[0] == group]
                for group in ("c", "s")
            ],
            rng,
        )
        for name, column in (
            ("convergence_um_per_hour", 2),
            ("elongation_um_per_hour", 1),
        )
    }
    stretcher = data["Fig.4e"]
    if stretcher[1][0] != "On Stretcher" or stretcher[13][0] != "Control":
        raise ValueError("Unexpected stretcher group headings")
    control = np.array([row[1] for row in stretcher[13:23]])
    loaded = np.array([row[1] for row in stretcher[1:13]])
    stretch_outcomes = differences(control, loaded, rng)
    stretch_outcomes["caption_control_n"] = 9
    stretch_outcomes["mean_difference_with_any_one_control_omitted"] = [
        float(loaded.mean() - np.delete(control, index).mean())
        for index in range(len(control))
    ]

    mechanics = probe(data["Fig.1h,5h,s3d"])
    film = inflation(data["Fig.4b"])
    table = data["Table1"]
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E63",
            "doi": "10.1038/s41467-023-38988-3",
            "evidence": "primary chick experiment source workbook",
            "figure_1h_probe": mechanics,
            "figure_3_sandwich_growth_6_to_8_hours_survivors": sandwich_outcomes,
            "table_1_sandwich_ruptures": ruptures(
                table, "Sandwiched", "Control group (Single filter)"
            ),
            "figure_4e_stretcher_convergence_um_per_hour": stretch_outcomes,
            "table_1_stretcher_ruptures": ruptures(
                table, "Loaded on stretcher", "Control group (not loaded)"
            ),
            "figure_4b_inflation_timing_example": film,
            "table_1_inflation_cases_and_total": list(
                next((row[6], row[7]) for row in table if row[1] == "Inflated")
            ),
            "scope": "External manipulation preceded measured shape changes in this developmental window. The worksheet cannot give the pressure, force or displacement history needed for the intervention work or a spatial energy flux. The graded probe measures other samples.",
            "checks": {
                "figure_1h_counts": [
                    group["force_rise_millinewton_per_second"]["n"]
                    for group in mechanics["groups"].values()
                ]
                == [15, 17, 9, 16, 16],
                "figure_3d_e_counts": all(
                    (x["control"]["n"], x["intervention"]["n"]) == (11, 16)
                    for x in sandwich_outcomes.values()
                ),
                "figure_4e_source_counts_and_means": (
                    (len(control), len(loaded)) == (10, 12)
                    and bool(np.isclose(control.mean(), stretcher[22][2]))
                    and bool(np.isclose(loaded.mean(), stretcher[12][2]))
                ),
                "convergence_effect_direction_survives_every_one_control_exclusion": all(
                    difference < 0
                    for difference in stretch_outcomes[
                        "mean_difference_with_any_one_control_omitted"
                    ]
                ),
                "inflation_intact_curve_stops_before_third_injection": (
                    film["time_s_and_width_um_single_embryo"][-2][0]
                    < film["published_injections_seconds"][2]
                ),
            },
        },
        __file__,
        sources.__file__,
    )
