"""Reanalyse the PIN3 loss and tissue-specific rescue of lateral-root initiation."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from experiments.common import save_summary


ROOT = Path(__file__).resolve().parents[2]
READINGS = ROOT / "experiments/local_reflux_readings.json"
GENOTYPES = ("WT", "pin3", "transgene_negative", "transgene_positive")


def reading(panels, panel, units):
    source = panels[panel]
    values = dict(zip(GENOTYPES, source["values"], strict=True))
    delta = values["transgene_positive"] - values["transgene_negative"]
    error = source["digitization_halfwidth"]
    return {
        "units": units, "group_means_from_bars": values, "readout_halfwidth_per_bar": error,
        "positive_minus_negative": delta, "positive_minus_WT": values["transgene_positive"] - values["WT"],
        "positive_minus_negative_readout_interval": [delta - 2*error, delta + 2*error],
    }


def run(readings, out):
    panels = json.loads(readings.read_text(encoding="utf-8"))["panels"]
    founder = reading(panels, "fig3b_founder_density", "founder sites per cm primary root")
    lri = reading(panels, "fig3c_lri_density", "lateral-root initiation sites per cm primary root")
    total = reading(panels, "fig3d_combined_density", "founder plus initiation sites per cm primary root")
    sum_residuals = {
        genotype: total["group_means_from_bars"][genotype] - sum(
            panel["group_means_from_bars"][genotype] for panel in (founder, lri)
        ) for genotype in GENOTYPES
    }
    sum_tolerance = sum(panel["readout_halfwidth_per_bar"] for panel in (founder, lri, total))
    stage_endo = reading(panels, "fig3e_stage_I", "stage I abundance on the published axis")
    stage_stele = reading(panels, "fig4b_stage_I", "stage I abundance on the published axis")
    timing = panels["fig2d_founder_postbend"]
    # Use the paired elapsed interval reported in the text. The onset bars describe
    # mean times from bending and cannot recover each plant's delay.
    wt, mutant = 103, 206
    results = {
        "experiment": "E24", "study_doi": "10.1038/emboj.2012.303",
        "figure_readings_sha256": sha256(readings.read_bytes()).hexdigest(),
        "text_FC_detection_to_first_division": {
            "units": "min", "WT_mean": wt, "WT_printed_plus_minus": 10, "pin3_mean": mutant,
            "pin3_printed_plus_minus": 16, "reported_n_per_group": 10,
            "pin3_minus_WT": mutant - wt, "pin3_over_WT": mutant/wt,
        },
        "figure_2D_bending_to_founder_reporter": {
            "units": "min", "WT": timing["values"][0], "pin3": timing["values"][1],
            "readout_halfwidth_per_bar": timing["digitization_halfwidth"],
        },
        "figure_3_endodermal_PIN3_rescue": {
            "B_founder_density": founder, "C_initiation_density": lri, "D_combined_density": total,
            "reported_D_minus_B_plus_C_approximate": sum_residuals,
            "readout_halfwidth_of_subtraction": sum_tolerance,
            "note": "The observed sums are taken directly from 3D. Differences across panel summaries cannot be assigned to individuals.",
        },
        "stage_I_by_expression_site": {"figure_3E_endodermal": stage_endo, "figure_4B_stele": stage_stele},
        "checks": {
            "founder_timing_from_two_calibrated_bars": len(timing["values"]) == 2 and all(0 < v < 350 for v in timing["values"]),
            "density_panels_within_their_axes": all(
                all(0 <= v <= panels[key]["tick_value"] for v in panels[key]["values"])
                for key in ("fig3b_founder_density", "fig3c_lri_density", "fig3d_combined_density")
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, results, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", type=Path, default=READINGS)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E24")
    args = parser.parse_args()
    run(args.readings, args.out)
