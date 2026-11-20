"""Draw summaries from saved measurements without redistributing the source figures."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, GREEN, GREY = "#265e8d", "#b6541c", "#287364", "#69717b"


def style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#dee4e7", linewidth=0.65)
    ax.spines[["top", "right"]].set_visible(False)


def roots(data, figures):
    pulse, roots = data[49], data[50]
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.4), layout="constrained")
    for ax in axes:
        style(ax)
    ax = axes[0]
    for key, color in (("IAA", BLUE), ("IBA", GREEN)):
        rec = pulse["rootward_fig3b"][key]
        ax.plot(np.arange(1, 20, 2), rec["pmol_equivalent"], "o-", color=color, label=key)
    ax.axvspan(12, 20, color=GREY, alpha=0.10)
    ax.set(
        xlabel="Distance from pulse (mm)",
        ylabel="Recovered radiolabel (pmol equivalent)",
        title="Rootward transport after 1 h",
        xticks=[0, 4, 8, 12, 16, 20],
    )
    ax.legend(frameon=False)
    pos = np.arange(4)
    for offset, direction, color in ((-0.18, "rootward", GREEN), (0.18, "shootward", ORANGE)):
        vals = roots["primary_root_fig2"]["ratios_to_matched_WT"][direction]
        axes[1].bar(
            pos + offset,
            np.array(list(vals.values())) * 100,
            0.34,
            label=direction.capitalize(),
            color=color,
        )
    axes[1].axhline(100, ls=":", lw=1, color=GREY)
    axes[1].set(
        xticks=pos,
        xticklabels=list(vals),
        ylabel="Transport / matched wild type (%)",
        ylim=(0, 132),
        title="Two independently perturbed directions",
    )
    axes[1].legend(ncol=2, frameon=False, loc="upper center")
    rates = np.array(roots["lateral_growth_fig9"]["mm_per_day"])
    for i, (label, col) in enumerate((("Control", GREY), ("Added IAA", GREEN), ("NPA", ORANGE))):
        axes[2].bar(np.arange(3) + (i - 1) * 0.23, rates[:, i], 0.22, label=label, color=col)
    axes[2].set(
        xticks=np.arange(3),
        xticklabels=["Wild type", "mdr1-1", "mdr1-2"],
        ylabel="Lateral root elongation (mm/day)",
        ylim=(0, 10.8),
        title="Growth after lateral roots emerge",
    )
    axes[2].legend(ncol=3, frameon=False, loc="upper center", fontsize=8)
    fig.savefig(figures / "root_routes.png", dpi=150)
    plt.close(fig)


def embryos(data, figures):
    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.3), layout="constrained")
    turns, rotation, prediction, daughter = axes.ravel()
    for ax in axes.ravel():
        style(ax)
    group = data[51]["scores"]["primary"]["groups"]
    for i, (metric, label, color) in enumerate(
        (
            ("axial_opposition", "Axial counterflow", GREY),
            ("both_oppositions", "Axial and radial turns", BLUE),
            ("both_oppositions", "Energy advection*", ORANGE),
        )
    ):
        key = "energy_signs" if i == 2 else "velocity_signs"
        vals = [
            group[s][key][metric]["cells_both_halves"] / group[s]["n_cells_both_halves_eligible"] * 100
            for s in ("Ce", "Mm")
        ]
        turns.bar(np.arange(2) + (i - 1) * 0.24, vals, 0.23, label=label, color=color)
    turns.set(
        xticks=[0, 1],
        xticklabels=["Worm embryos (6)", "Mouse oocytes (7)"],
        ylim=(0, 128),
        ylabel="Both halves pass (% of cells)",
        title="Where the measured flow turns",
    )
    turns.legend(frameon=False, ncol=2, fontsize=8, loc="upper center")
    turns.set_xlabel("*Two measured velocity components")
    for emb in data[52]["embryos"]:
        rotation.scatter(
            emb["angle_deg"], emb["size_asymmetry_index"], s=40, color=ORANGE if emb["inverted"] else BLUE
        )
    rotation.axvline(90, ls=":", color=GREY, lw=1.2)
    rotation.axhline(0, color=GREY, lw=0.8)
    rotation.set(
        xlabel="Induced PAR rotation before division (degrees)",
        ylabel="Signed daughter-size asymmetry",
        title="First division following induced rotation",
        xlim=(0, 145),
    )
    stages = data[53]["stages"]
    for i, label, col in ((0, "Entry-side posterior", BLUE), (1, "Opposite-side posterior", ORANGE)):
        prediction.plot(
            np.arange(7),
            [100 * (1 - s["relative_to_printed_denominator"][i]) for s in stages.values()],
            "o-",
            color=col,
            label=label,
        )
    prediction.set(
        xticks=np.arange(7),
        xticklabels=["Fert.", "AI", "+5 min", "AII", "SB−1", "SB", "PNM"],
        ylabel="Correct posterior-side predictions (%)",
        ylim=(-5, 111),
        title="Which side becomes posterior?",
    )
    prediction.legend(frameon=False, loc="lower right", fontsize=8)
    groups = data[54]["angle_offset_degrees"]
    for i, (name, points) in enumerate(groups.items()):
        # Separate symbols with equal y values; the offset is only for displaying observations.
        offsets = np.linspace(-0.05, 0.05, len(points))
        daughter.scatter(i + offsets, points, color=(GREY, ORANGE)[i], s=33)
        daughter.plot([i - 0.15, i + 0.15], [np.mean(points)] * 2, color="#26323a", lw=2)
    daughter.axhline(0, color=GREY, ls=":", lw=0.9)
    daughter.set(
        xlim=(-0.45, 1.45),
        xticks=[0, 1],
        xticklabels=["Alternating scans", "Directional scans"],
        ylabel="PAR-2 axis offset from contact (degrees)",
        title="Polarity in the next cell, P1",
    )
    fig.savefig(figures / "flow_and_division.png", dpi=150)
    plt.close(fig)


def run(root):
    figures = root / "turning_path_figures"
    figures.mkdir(parents=True, exist_ok=True)
    data = {n: json.loads((root / f"E{n}" / "summary.json").read_text()) for n in range(49, 55)}
    roots(data, figures)
    embryos(data, figures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root)
