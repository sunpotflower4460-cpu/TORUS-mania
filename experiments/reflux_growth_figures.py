"""Plot the published profile contrasts and the frozen growth forecasts."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

GREEN = "#19775d"
BLUE = "#276996"
GRAY = "#737a83"
ORANGE = "#bd5928"


def read(root, relative):
    return json.loads((root/relative).read_text(encoding="utf-8"))


def style(axis, title, xlabel, ylabel):
    axis.set(title=title, xlabel=xlabel, ylabel=ylabel)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#e2e7ec", lw=.7)


def profiles(root, out):
    data = read(root, "E27/summary.json")
    rows = data["fig2J_mean_absolute_difference_in_normalized_DII_VENUS"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.9, 4.5), layout="constrained")
    fig.suptitle("Adding cell-to-cell diffusion improves the root-tip reporter profile", fontsize=14)
    x = np.arange(len(rows))
    for key, delta, label, color in (("reference", -.18, "Membrane transport", GRAY),
                                      ("changed", .18, "Plus plasmodesmata", GREEN)):
        left.bar(x+delta, [r[key] for r in rows.values()], width=.32, color=color, label=label,
                 yerr=[r["bar_readout_halfwidth"] for r in rows.values()], capsize=3)
    left.set_xticks(x, list(rows))
    left.set_ylim(0, 33)
    style(left, "Normalized DII-VENUS profile", "", "Mean absolute model–data difference")
    left.legend(loc="upper right", fontsize=8.5)

    rows = list(data["fig4_5_unnormalized_fluorescence_within_panel_only"].values())
    x = np.arange(2)
    for i, (color, label) in enumerate(((BLUE, "Observed"), (GREEN, "Model"))):
        vals = [r["change_percent"] for r in rows[i::2]]
        right.bar(x+(i-.5)*.36, vals, width=.32, color=color, label=label)
    right.axhline(0, lw=.8, color=GRAY)
    right.set_xticks(x, ["H₂O₂", "GSL8 perturbation"])
    right.set_ylim(-47, 4)
    style(right, "Permeability perturbations", "", "Mean fluorescence change (%)")
    right.legend(loc="lower right", fontsize=8.5)
    fig.supxlabel("Mellor et al. (2020), digitized summary bars · profile error bars denote reading range", fontsize=9)
    fig.savefig(out/"plasmodesmata_profiles.png", dpi=150)
    plt.close(fig)


def forecasts(root, out):
    prior = read(root, "E29/sealed_predictions.json")
    holdout = read(root, "E29/summary.json")["holdout"]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.75), layout="constrained")
    fig.suptitle("Forecasts fixed before reading the higher-production measurements", fontsize=14)
    p = np.linspace(1.10, 3.20, 160)
    models = prior["models"]
    for axis, key, unit in zip(axes, ("frequency", "spacing"), ("Priming events per hour", "Priming site spacing (cells)"), strict=True):
        axis.axvspan(1.97, 2.03, color="#d6dce1", alpha=.45)
        for selection, points, color, face in (
            ("Training markers", prior["training"], GRAY, GRAY),
            ("Held-out markers", holdout, BLUE, "none"),
        ):
            xy = np.asarray(points[key]["xy"])
            axis.scatter(xy[:,0], xy[:,1], s=19, facecolors=face, edgecolors=color, alpha=.68, label=selection)
        for name, color, dash, label in (
            ("two_waiting_times", GREEN, "-", "Two waiting times"),
            ("fixed_clock", GRAY, "--", "Fixed period"),
            ("fixed_distance", ORANGE, "--", "Fixed spacing"),
        ):
            model = models[name]
            period = model["tau_h"]+model["length_cells"]/p
            y = 1./period if key == "frequency" else p*period+model["spacing_offset_cells"]
            axis.plot(p, y, color=color, ls=dash, lw=1.8, label=label)
        axis.set_xlim(1.10, 3.20)
        style(axis, "Priming frequency" if key=="frequency" else "Distance between priming sites",
              "Cell production (cells/h)", unit)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=5, fontsize=8.6, frameon=False)
    fig.savefig(out/"sealed_growth_forecasts.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    folder = args.root/"reflux_growth_figures"
    folder.mkdir(parents=True, exist_ok=True)
    profiles(args.root, folder)
    forecasts(args.root, folder)
