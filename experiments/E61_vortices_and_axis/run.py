"""Audit the published vortex measurements and their anatomical comparisons."""

import itertools
import re
import xml.etree.ElementTree as ET

from scipy.stats import t, ttest_ind_from_stats

from experiments import embryo_history_sources as sources
from experiments.common import save_summary


def compact(element):
    return " ".join("".join(element.itertext()).split())


def published_values(article):
    spacing = compact(article.find(".//fig[@id='fig1s1']/caption"))
    duration = next(
        compact(p)
        for p in article.findall(".//body//p")
        if "were maintained for a shorter period" in compact(p)
    )
    spacing_pattern = (
        r"control-GFP ([\d.]+)\s*±\s*([\d.]+)\s*μm vs ΔDEP-GFP ([\d.]+)"
        r"\s*±\s*([\d.]+)\s*μm, p=([\d.]+), n=(\d+)"
    )
    duration_pattern = (
        r"([\d.]+)\s*±\s*([\d.]+)\s*hr \(control ([\d.]+)"
        r"\s*±\s*([\d.]+)\s*hr, p=([\d.]+)"
    )
    control, control_sd, delta, delta_sd, reported_p, n = re.search(
        spacing_pattern, spacing
    ).groups()
    short, short_sd, long, long_sd, length_p = re.search(
        duration_pattern, duration
    ).groups()
    return (
        compare((control, control_sd, delta, delta_sd), int(n), reported_p),
        compare((long, long_sd, short, short_sd), 4, length_p),
    )


def compare(printed, n, stated_p):
    values = tuple(float(value) for value in printed)

    def recompute(v, equal_var):
        return float(
            ttest_ind_from_stats(
                v[0], v[1], n, v[2], v[3], n, equal_var=equal_var
            ).pvalue
        )

    steps = (0.5 * 10 ** -len(token.partition(".")[2]) for token in printed)
    rounded_range = [
        recompute(v, True)
        for v in itertools.product(
            *[
                [value - step, value + step]
                for value, step in zip(values, steps, strict=True)
            ]
        )
    ]
    difference = values[2] - values[0]
    smallest_paired_sd = abs(values[3] - values[1])
    paired_p_lower_bound = (
        float(2 * t.sf(abs(difference) * n**0.5 / smallest_paired_sd, df=n - 1))
        if smallest_paired_sd
        else None
    )
    return {
        "n_per_group": n,
        "control_mean_and_printed_spread": list(values[:2]),
        "intervention_mean_and_printed_spread": list(values[2:]),
        "intervention_minus_control": difference,
        "reported_p": float(stated_p),
        "student_p_if_spreads_are_sample_sd": recompute(values, True),
        "welch_p_if_spreads_are_sample_sd": recompute(values, False),
        "student_p_range_from_rounding_if_sd": [min(rounded_range), max(rounded_range)],
        "paired_p_lower_bound_if_sd_without_rounding": paired_p_lower_bound,
    }


def run(raw, out):
    article = ET.parse(sources.source(raw, "asai-article.xml"))
    sources.source(raw, "asai-fig1-supp1.jpg")
    spacing, duration = published_values(article)
    comparisons = [
        {
            "figure": "1 and supplement 1",
            "groups": ["GFP control", "dominant-negative ΔDEP-GFP"],
            "live_flow_n_each": 5,
            "stained_primitive_streak_n_at_least_each": 4,
            "comparison": "Bilateral rotational flows persisted in embryos with a shorter, wider streak.",
        },
        {
            "figure": "2",
            "groups": ["sham", "mitotic arrest"],
            "live_flow_n_each": 4,
            "stained_primitive_streak_n_at_least_each": 4,
            "comparison": "Bilateral flows began in both groups. Streak extension was diminished and the flow pattern ended earlier under arrest.",
        },
        {
            "figure": "3",
            "groups": ["control-GFP/COS implant", "ectopic Vg1/COS implant"],
            "live_flow_n_each": 4,
            "comparison": "Initial flows appeared at both axes in Vg1/COS embryos. Ectopic reverse rotations became dominant before original streak extension, which still proceeded along the authentic midline.",
            "pairing": "Original streak extension and disrupted authentic flow were observed together in the reported four treated embryos.",
        },
        {
            "figure": "4",
            "groups": [
                "control-GFP/COS under mitotic arrest",
                "Vg1/COS under mitotic arrest",
            ],
            "live_flow_n_each": 3,
            "stained_primitive_streak_n_each": 3,
            "comparison": "Predominant rotations at the ectopic site persisted despite diminished original and ectopic streaks. Controls initially rotated along the authentic axis and the pattern weakened.",
        },
    ]
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E61",
            "doi": "10.7554/eLife.89948.3",
            "evidence": "primary figures and reported group summaries from chick gastrulation interventions",
            "comparisons": comparisons,
            "spacing_micrometers_figure_1_supplement_1i": spacing,
            "flow_duration_hours_figure_2": duration,
            "scope": "Distance panel displays bars and error bars only. Both t tests assume the printed spreads are SD. Separate assay cohorts are not joined. These are epiblast surface flows; neither a closed 3D trajectory nor a mechanical energy flux is identified.",
            "checks": {
                "spacing_printed_n_and_means": spacing["n_per_group"] == 4
                and spacing["control_mean_and_printed_spread"][0] == 860.2
                and spacing["intervention_mean_and_printed_spread"][0] == 1008.4,
                "supplement_contains_reported_distance_criterion": article.find(
                    ".//fig[@id='fig1s1']"
                )
                is not None,
                "reported_flows_last_less_time_after_mitotic_arrest": duration[
                    "intervention_minus_control"
                ]
                < 0,
            },
        },
        __file__,
        sources.__file__,
    )
