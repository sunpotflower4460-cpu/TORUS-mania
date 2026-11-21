"""Plot the independent experiments and the missed-pulse comparison."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

BLUE, GREEN, ORANGE, GRAY = "#276795", "#1d7a60", "#bf622d", "#737984"


def read(root, experiment):
    return json.loads((root/experiment/"summary.json").read_text(encoding="utf-8"))


def style(axis, title, xlabel, ylabel):
    axis.set(title=title, xlabel=xlabel, ylabel=ylabel)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#dce1e7", lw=.7)


def interventions(root, out):
    traffic = read(root, "E30")["box_values"]
    development = read(root, "E31")["figure_S2C_post_initiation_counts"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.8, 4.55), layout="constrained")
    fig.suptitle("Separate interventions affect successive stages of lateral-root formation", fontsize=14)
    groups = (
        ("WT_mock", "WT"), ("gnom184_mock", "gnom184"), ("gnom184_agd3_26_mock", "gnom184\n+ agd3"),
        ("WT_BFA", "WT"), ("agd3_26_BFA", "agd3-26"), ("agd3_SALK_BFA", "agd3-SALK"),
    )
    for i, (key, _) in enumerate(groups):
        box = traffic[key]
        middle = box["median"]
        low, high = box["quartiles_q1_q3"]
        left.errorbar(i, middle, yerr=[[middle-low], [high-middle]], fmt="o", capsize=4,
                      color=GREEN if i<3 else BLUE,
                      label="Mock" if i==0 else "BFA" if i==3 else None)
    left.set_xticks(range(len(groups)), [label for _, label in groups], fontsize=8.5)
    left.set_xlim(-.5, len(groups)-.5)
    left.set_ylim(-.4, 8)
    style(left, "Prebranch-site density", "", "Sites per cm of primary root")
    left.legend(loc="upper right", fontsize=8.8)

    ages = development["days_post_imbibition"]
    for key, label, color, marker in (
        ("WT", "WT", GREEN, "o"),
        ("iaa18_potent", "iaa18/potent", ORANGE, "s"),
        ("potent_transgene", "potent transgene", BLUE, "^"),
    ):
        row = development["primordia_plus_lateral_roots"][key]
        right.plot(ages, row["organs_per_plant"], lw=1.8, marker=marker, color=color, label=label)
    right.set_xticks(ages)
    right.set_ylim(-1, 33)
    style(right, "Organs after initiation", "Days after imbibition", "Primordia + lateral roots per plant")
    right.legend(loc="upper left", fontsize=8.8)
    fig.supxlabel("Wachsman et al. (2020), Fig. 3C, median and quartiles · Perianez-Rodriguez et al. (2021), Fig. S2C, means",
                 fontsize=8.8)
    fig.savefig(out/"root_clock_interventions.png", dpi=150)
    plt.close(fig)


def visibility(root, out):
    data = read(root, "E32")
    preview = data["preview"]
    times = np.asarray(preview["all_pulse_times_fixed_period_h"][:14])
    amplitudes = np.asarray(preview["weak_amplitude_and_strong_amplitude"][:14])
    strong = times[amplitudes > data["weak_peak_amplitude_arbitrary"]]
    weak = times[amplitudes == data["weak_peak_amplitude_arbitrary"]]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.2, 4.3), layout="constrained")
    fig.suptitle("A missed weak pulse can resemble a longer interval between pulses", fontsize=14)
    left.hlines([0, 1], 0, times[-1]+.5, color="#aeb8c1", lw=.8)
    left.scatter(weak, np.ones(len(weak)), marker="o", s=30, color=ORANGE, label="Weak pulse")
    for row in (1, 0):
        left.scatter(strong, np.full(len(strong), row), marker="o", s=42, color=GREEN,
                     label="Pulse with lasting site" if row==1 else None)
    left.set_xlim(0, times[-1]+1)
    left.set_ylim(-.5, 1.65)
    left.set_yticks([0, 1], ["Slower, variable pulses", "Fixed period, some weak"])
    style(left, "Same lasting sites in both models", "Model time (h)", "")
    left.legend(loc="upper right", fontsize=8.8)

    sigma = np.linspace(.025, .36, 180)
    sensitivity = norm.sf(norm.ppf(.95)-data["weak_peak_amplitude_arbitrary"]/sigma)
    right.plot(sigma, sensitivity, color=BLUE, lw=2, label="Sensitivity at 5% false positives")
    right.axhline(.80, color=GRAY, ls="--", lw=1, label="80% sensitivity")
    limit = data["largest_sd_with_both_requirements"]
    right.axvline(limit, color=ORANGE, lw=1.2, ls=":", label=f"Noise limit {limit:.3f}")
    right.set(ylim=(0, 1.05), xlim=(.025, .36))
    style(right, "Resolving pulses at missing-site times", "Noise SD (model units)", "Detection probability")
    right.legend(loc="lower left", fontsize=8.8)
    fig.savefig(out/"pulse_observability.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    folder = args.root/"root_clock_figures"
    folder.mkdir(parents=True, exist_ok=True)
    interventions(args.root, folder)
    visibility(args.root, folder)
