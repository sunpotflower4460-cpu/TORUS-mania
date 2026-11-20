"""Reanalyse separate auxin movement, development, and hormone rescue assays."""

import argparse
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path

from scipy.stats import t

from experiments.common import save_summary
from experiments.E21_auxin_evidence import read_figure

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def contrast(before, after, n=None, dispersion="SE"):
    first, e0 = before
    second, e1 = after
    difference = second-first
    result = {"control_mean": first, "intervention_mean": second, "difference": difference,
              "change_percent": 100*difference/first if first else None}
    if n and e0 is not None and e1 is not None:
        v0, v1 = (e0**2, e1**2) if dispersion == "SE" else (e0**2/n, e1**2/n)
        if v0+v1:
            df = (n-1)*(v0+v1)**2/(v0**2+v1**2)
            margin = float(t.ppf(.975, df) * sqrt(v0+v1))
            result["approximate_independent_welch_95_difference"] = [difference-margin, difference+margin]
            result["n_per_group_used"] = n
    return result


def reed(source):
    data = source["table_I"]
    doses = {}
    for dose, *row in data:
        sample_size = source["table_I_n_plants_per_group"] if dose else None
        doses[str(dose)] = {
            name:contrast(before, after, sample_size)
            for name, before, after in zip(("lateral_roots","length_mm","density_per_mm"), data[0][1:], row, strict=True)
        }
    ci = source["table_II"]
    tracer = source["table_III"]
    locations = source["table_V"]
    return {
        "table_I_by_dose": doses,
        "table_II_endogenous_IAA_and_lateral_roots_separate_assays": {
            "free_IAA_ng_per_g_fresh_mass":contrast(*ci["concentration_free_IAA_ng_per_g_fresh_weight"]),
            "lateral_root_number":contrast(*ci["lateral_root_number"]),
            "printed_text_decrease_percent": ci["text_percent_lower_free_IAA"],
        },
        "table_III_24h_tracer": {
            "amount_fmol":contrast(*tracer["rootward_IAA_fmol"], tracer["n_independent_pools_per_group"]),
            "activity_cpm":contrast(*tracer["rootward_activity_cpm"], tracer["n_independent_pools_per_group"]),
            "n_plants_per_pool":tracer["plants_in_each_pool"],
            "published_P":tracer["published_P_transport"],
        },
        "table_V_two_placements": {
            "root_number":contrast(locations["upper_IAA__lower_NPA"][0],
                                   locations["upper_NPA__lower_IAA"][0], source["table_V_n_plants_per_group"]),
            "root_density_per_mm":contrast(locations["upper_IAA__lower_NPA"][1],
                                           locations["upper_NPA__lower_IAA"][1], source["table_V_n_plants_per_group"]),
            "reference_untreated":locations["upper_control__lower_control"],
            "note":"The upper/lower positions of IAA and NPA both change. This is a positional contrast.",
        },
    }


def rashotte(source):
    return {
        "unit":source["unit"], "original_unit_label":"pmol", "correction_doi":source["correction_doi"],
        "table_II_inhibitor": {
            key: {**contrast(a,b), "plants":plants, "experiments":replicates, "published_P":published_p}
            for key,(a,b,plants,replicates,published_p) in source["table_II"].items()
        },
        "table_IV_directional_assays": {
            key: {"Columbia_vs_eir1_without_inhibitor":contrast(a,c),
                  "Columbia_inhibitor":contrast(a,b),
                  "eir1_inhibitor":contrast(c,d), "published_P_Columbia_vs_eir1":published_p}
            for key,(a,b,c,d,published_p) in source["table_IV"].items()
        },
        "notes":"The two directions have distinct protocols. Table IV has SD and a sample-size range; "
                "no new confidence intervals from assumed n were calculated.",
    }


def casimiro(source, figure):
    table = source["table_1"]
    dose_results = {}
    for dose, density, length in table:
        n = source["table_1_n_plants_per_group"] if dose else None
        counts = source["table_2_total_counts_by_stage_I_to_VII"][str(dose)]
        pooled = sum(counts)
        dose_results[str(dose)] = {
            "density_per_mm":contrast(table[0][1], density, n, dispersion="SD"),
            "length_mm":contrast(table[0][2], length, n, dispersion="SD"),
            "different_sample_primordia_count_in_five_roots": pooled,
            "different_sample_stage_I_or_II_fraction": sum(counts[:2])/pooled if pooled else None,
        }

    rates = {key: row["lateral_roots_per_mm"] for key,row in figure["bars"].items()}
    rounding = figure["readout_uncertainty_per_mm_from_3px"]
    c, d = rates["C_NPA"], rates["D_NPA_plus_NAA"]
    minimum = max(0., d-rounding) - (c+rounding)
    maximum = d+rounding - max(0., c-rounding)
    return {"sustained_inhibitor_by_dose":dose_results,
            "figure_3_NAA_rescue_with_inhibitor_still_present": {
                "mean_densities_per_mm":rates, "original_source_url":figure["source_url"],
                "figure_readout_error_per_bar":rounding, "gain_per_mm":d-c,
                "difference_range_from_pixel_uncertainty_only":[minimum, maximum],
                "note":"The figure shows SD. The interval here describes digitization, not uncertainty across roots.",
            }}


def run(data_path, figure_path, out):
    values = json.loads(data_path.read_text(encoding="utf-8"))
    figure = json.loads(figure_path.read_text(encoding="utf-8"))
    checks = {
        "ratio_of_equal_means_has_no_change": contrast([2.,.1], [2.,.2])["change_percent"] == 0.,
        "tracer_conversion_consistency": abs(1501/61.4 - 1124/46.) < .05,
        "three_visible_rescue_bars_recovered": sum(b["detected_bar_above_axis"] for b in figure["bars"].values()) == 3,
        "corrected_radiotracer_units": values["rashotte"]["unit"] == "fmol",
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, {"reed_1998":reed(values["reed"]), "rashotte_2000":rashotte(values["rashotte"]),
                       "casimiro_2001":casimiro(values["casimiro"],figure),
                       "input_sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in (data_path, figure_path)},
                       "checks":checks}, __file__, read_figure.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--values", type=Path, default=HERE / "published_values.json")
    parser.add_argument("--figure", type=Path, default=HERE / "figure_values.json")
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E21")
    args = parser.parse_args()
    run(args.values, args.figure, args.out)
