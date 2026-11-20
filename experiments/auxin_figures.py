"""Plot the measured auxin interventions and candidate tracer responses."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BLUE = "#2b6697"
GREEN = "#207961"
PURPLE = "#82559c"
ORANGE = "#bb5e29"
GRAY = "#676e77"


def load_summary(root, key):
    return json.loads((root / key / "summary.json").read_text(encoding="utf-8"))


def style(axis, title, x_label, y_label):
    axis.set(title=title, xlabel=x_label, ylabel=y_label)
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#dce1e8", linewidth=.7)
    axis.set_axisbelow(True)


def interventions(root, path):
    findings = load_summary(root, "E21")
    reed = findings["reed_1998"]
    mild = reed["table_I_by_dose"]["10.0"]
    items = [reed["table_III_24h_tracer"]["amount_fmol"], mild["density_per_mm"], mild["length_mm"]]
    ratios = [row["intervention_mean"]/row["control_mean"] for row in items]
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.8, 4.45), layout="constrained")
    fig.suptitle("Auxin transport and lateral-root formation", fontsize=15)
    bars = left.bar(np.arange(3), ratios, width=.59, color=[BLUE, GREEN, GRAY])
    left.bar_label(bars, labels=[f"{ratio:.1%}" for ratio in ratios], padding=-15, fontsize=9, color="white")
    left.axhline(1., ls="--", color=GRAY, label="Matched controls")
    left.set_xticks(np.arange(3), ["Tracer in root\nTable III", "Lateral-root density\nTable I", "Primary-root length\nTable I"])
    left.set_ylim(0, 1.16)
    style(left, "Transport inhibition · separate assays", "", "Intervention mean / control mean")
    left.legend(fontsize=8.5, loc="upper right")

    rescue = findings["casimiro_2001"]["figure_3_NAA_rescue_with_inhibitor_still_present"]
    rates = list(rescue["mean_densities_per_mm"].values())
    marks = np.arange(4)
    error = rescue["figure_readout_error_per_bar"]
    right.bar(marks, rates, width=.63, color=[GRAY, BLUE, ORANGE, GREEN])
    right.errorbar(marks, rates, yerr=[np.minimum(rates, error), np.full(4, error)],
                   fmt="none", ecolor="#242b35", capsize=3, linewidth=1.)
    for i, rate in enumerate(rates):
        right.text(i, rate + .025, f"{rate:.2f}", ha="center", fontsize=9)
    right.set_xticks(marks, ["Control", "NAA", "NPA", "NPA + NAA"])
    right.set_ylim(0, .83)
    style(right, "Auxin supplied while inhibition continued", "", "Emerged lateral roots per mm")
    fig.supxlabel("Reed et al. (1998), Tables I and III · Casimiro et al. (2001), Fig. 3 (digitization error shown)",
                 fontsize=9.2)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tracer(root, path):
    readings = load_summary(root, "E22")
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.8, 4.45), layout="constrained")
    fig.suptitle("Tracer in the inner tissue under matched steady-state profiles", fontsize=15)
    with np.load(root / "E22/responses.npz") as archive:
        curves = [("cycle", GREEN, "-", "Full cycle"),
                  ("shortcut", PURPLE, "-", "Shorter route, before and after cut"),
                  ("cycle_cut", ORANGE, "--", "Open route and cut full cycle")]
        for key, color, line, name in curves:
            vals = archive[key]
            left.plot(vals[:, 0], vals[:, 1], color=color, ls=line, lw=2, label=name)
    left.set_ylim(-.008, .2)
    style(left, "Response to a tracer pulse at the tip", "Normalized time", "Inner tracer / input pulse")
    left.legend(fontsize=8.5)

    study = readings["sensitivity"]
    times = list(readings["cut_effect_by_candidate"]["cycle"])
    numeric_times = np.array([float(t) for t in times])
    for i, t in enumerate(times):
        quantiles = study["cut_effect_by_time"][t]
        mid = quantiles["median"]
        errors = [[mid-quantiles["minimum"]], [quantiles["maximum"]-mid]]
        right.errorbar(numeric_times[i], mid, yerr=errors, fmt="o", color=BLUE,
                       lw=1.5, capsize=4, label="Range across 81 parameter sets" if i==0 else None)
    right.plot(numeric_times, [study["weak_return_effect"][t] for t in times],
               color=PURPLE, lw=1.5, marker="s", label="Weak return")
    right.axhline(.05, ls=":", lw=1., color=GRAY, label="5% comparison threshold")
    right.set_xticks(numeric_times)
    right.set_ylim(-.01, .27)
    style(right, "Effect of cutting only outer re-entry", "Normalized time", "Decrease / input pulse")
    right.legend(fontsize=8.5)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def nutrient(root, path):
    readings = load_summary(root, "E23")["figures"]
    fig, axes = plt.subplots(1, 3, figsize=(12.7, 4.6), layout="constrained")
    fig.suptitle("Root response to nitrate across three biological repeats", fontsize=15)
    panels = (
        ("fig6", "density_per_cm", "Fig. 6 · Lateral-root density", "Lateral roots and primordia / cm"),
        ("fig6", "implied_count", "Fig. 6 · Implied total count", "Lateral roots and primordia / plant"),
        ("fig7", "density_per_cm", "Fig. 7 · Lateral-root density", "Lateral roots and primordia / cm"),
    )
    for axis, (figure, measure, title, unit) in zip(axes, panels, strict=True):
        groups = readings[figure][measure]["groups"]
        axis.axhline(0, color=GRAY, lw=.9)
        for x, group in enumerate(groups.values()):
            repeats = list(group["KNO3_minus_KCl_by_replicate"].values())
            axis.scatter(x + np.array([-.16, 0., .16]), repeats, s=28, color=BLUE, zorder=3,
                         label="Biological repeat" if x == 0 else None)
            average = group["equal_replicate_contrast"]
            axis.hlines(average, x-.25, x+.25, color=ORANGE, lw=2, zorder=4,
                        label="Equal-weight mean" if x == 0 else None)
        labels = [name.replace("PIN2S", "PIN2\nS").replace("PIN2wt", "PIN2 WT") for name in groups]
        axis.set_xticks(range(len(groups)), labels)
        axis.set_xlim(-.52, len(groups)-.48)
        style(axis, title, "", unit)
    axes[-1].legend(loc="upper right", fontsize=8.4)
    fig.supxlabel("KNO₃ minus KCl at 3 days · Vega et al. (2021) supplement · Fig. 6 count inferred from aligned rows",
                 fontsize=9.2)
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    options = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    folder = options.root / "auxin_figures"
    folder.mkdir(parents=True, exist_ok=True)
    interventions(options.root, folder / "root_interventions.png")
    tracer(options.root, folder / "tracer_reentry.png")
    nutrient(options.root, folder / "nutrient_contrasts.png")
