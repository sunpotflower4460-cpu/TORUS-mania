"""Plot registered E79 descriptive ratios without implying root-level intervals."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot(out):
    out = Path(out)
    data = json.loads((out / "E79" / "summary.json").read_text())["datasets"]
    folder = out / "abcb_clock_figures"
    folder.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.hashsalt": "torus-abcb-clock-20261122"})
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0), sharey=True)
    labels = ["Whole-plant silencing\namiR-2572 (Fig. 2)",
              "Outer-tissue silencing\nsyn-tasi-1522A#1 (Fig. 6)"]
    panels = [
        ("A  Signal amplitude", ["fig2J_clock_amplitude", "fig6H_clock_amplitude"], "#236a89"),
        ("B  Peak-to-peak period", ["fig2I_clock_period", "fig6G_clock_period"], "#a45b22"),
    ]
    for ax, (title, keys, color) in zip(axes, panels):
        ax.axvline(1, color="#75808c", lw=1.1, ls="--")
        for y, key in zip([1, 0], keys):
            item = data[key]
            ratio = item["comparison"]["geometric_mean_ratio_intervention_over_WT"]
            if ratio is None:
                ax.text(.5, y, "Geometric mean unavailable", ha="center")
                continue
            wt = item["groups"]["wt"]
            treated = next(v for k, v in item["groups"].items() if k != "wt")
            ax.plot([1, ratio], [y, y], color=color, lw=2.8, alpha=.65)
            ax.scatter([ratio], [y], s=100, color=color, zorder=4)
            ax.scatter([1], [y], s=40, facecolor="white", edgecolor="#75808c", zorder=3)
            ax.text(ratio, y+.16, f"{ratio:.3f} x", ha="center", color=color, weight="bold", fontsize=13)
            count = f"Listed values: {wt['n_numeric_values']} / {treated['n_numeric_values']}"
            ax.text(.06, y-.22, count, fontsize=10, color="#45505b")
        ax.set_title(title, loc="left", fontsize=13, weight="bold", pad=18)
        ax.set_xlim(0, 1.26)
        ax.set_ylim(-.52, 1.48)
        ax.set_xticks([0, .25, .5, .75, 1, 1.25])
        ax.set_xlabel("Intervention / WT geometric mean", labelpad=10)
        ax.set_yticks([1, 0])
        ax.grid(axis="x", color="#e3e8eb", lw=.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0, pad=12)
        for side in ["top", "right", "left"]:
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#ccd3d9")
    axes[0].set_yticklabels(labels)
    fig.suptitle("ABCB silencing: amplitude and period", x=.02, ha="left", y=.98, fontsize=17, weight="bold")
    fig.text(.02, .905, "Descriptive centers of published values. Root-level uncertainty is not identified.", fontsize=11, color="#45505b")
    fig.text(.02, .035, "WT = 1. Points are group summaries, not individual roots. No confidence intervals or equivalence claims.\n"
                         "Source: Chen et al. (2023), DOI 10.15252/embr.202256271; registered E79 reanalysis.",
             fontsize=9.3, color="#45505b")
    fig.subplots_adjust(left=.235, right=.985, top=.79, bottom=.235, wspace=.16)
    fig.savefig(folder / "abcb_clock_ratios.png", dpi=170, metadata={"Software": "TORUS-mania E79"})
    fig.savefig(folder / "abcb_clock_ratios.svg", metadata={"Date": None, "Creator": "TORUS-mania E79"})
    plt.close(fig)
