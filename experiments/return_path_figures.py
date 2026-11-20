"""Plot return-path interventions and the held-out root-count comparison."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BLUE = "#235f92"
GREEN = "#1b7665"
PURPLE = "#79579b"
ORANGE = "#b45824"
GRAY = "#626b76"


def summary(path):
    return json.loads(path.read_text(encoding="utf-8"))


def style(ax, title, xlabel, ylabel):
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", color="#dfe4ea", linewidth=.7)
    ax.set_axisbelow(True)


def return_paths(root, path):
    data_path = root / "E19/grid512"
    cases = summary(data_path / "summary.json")["cases"]
    figure, (left, right) = plt.subplots(1, 2, figsize=(11.8, 4.5), layout="constrained")
    figure.suptitle("Effect of the return path at the same flow speed", fontsize=15)
    with np.load(data_path / "histories.npz") as histories:
        lines = (
            ("open", GRAY, "-", "Open"),
            ("partial", PURPLE, "-", "Half returned"),
            ("closed", GREEN, "-", "Closed return"),
            ("open_replenished", ORANGE, "--", "Open + fresh replenishment"),
        )
        for key, color, line_style, label in lines:
            a = histories[key]
            left.plot(a[:, 0], a[:, 1:3].sum(axis=1), color=color, ls=line_style, lw=2, label=label)
    style(left, "Fixed absorption rates", "Time (s)", "Resource absorbed / initial dose")
    left.set_ylim(0, 1.)
    left.legend(fontsize=8.5, loc="lower right")

    x = np.arange(2)
    positions = (("open", "open_capacity"), ("closed", "closed_capacity"))
    for offset, cols, color, label in zip((-.17, .17), positions, (GRAY, GREEN), ("Open", "Closed"), strict=True):
        shares = [cases[key]["B_share_of_uptake"] for key in cols]
        bars = right.bar(x+offset, shares, width=.32, color=color, label=label)
        right.bar_label(bars, labels=[f"{share:.1%}" for share in shares], padding=3, fontsize=9)
    right.set_xticks(x, ["Fixed absorption rates", "Finite capacity at each site"])
    right.set_ylim(0, .82)
    right.legend(fontsize=8.5, loc="upper left")
    style(right, "Resource allocated to the second site", "", "Site B / total absorbed")
    figure.savefig(path, dpi=150)
    plt.close(figure)


def root_counts(root, path):
    data = summary(root / "E20/summary.json")
    comparison = data["frequency_holdout"]
    estimates = comparison["all_plot_points"]
    hours = np.array([entry["hours"] for entry in estimates])
    rates = np.array([entry["root_and_primordia_per_day"] for entry in estimates])
    calibration = hours == 6
    uncertainty = comparison["observation_uncertainty_per_day"]
    ref_rate = comparison["calibration_observed_root_and_primordia_per_day"]
    figure, (left, right) = plt.subplots(1, 2, figsize=(11.8, 4.5), layout="constrained")
    figure.suptitle("Lateral-root counts under controlled bending", fontsize=15)
    x = np.linspace(2, 24, 180)
    left.plot(x, 24/x, color=ORANGE, ls="--", lw=1.8, label="One per bend")
    left.plot(x, ref_rate*6/x, color=PURPLE, ls=":", lw=1.8, label="Proportional fit")
    left.axhline(ref_rate, color=GREEN, lw=1.8, label="Constant fit")
    left.errorbar(hours[~calibration], rates[~calibration], yerr=uncertainty, fmt="o", ms=5, capsize=2,
                  color=BLUE, label="Held-out measurements")
    left.errorbar(hours[calibration], rates[calibration], yerr=uncertainty, fmt="o", mfc="white",
                  capsize=2, color=BLUE, label="6 h calibration")
    left.set_xticks([2, 4, 6, 9, 12, 18, 24])
    style(left, "Imposed bend intervals · Fig. 4B", "Hours between turns", "Roots and primordia per day")
    left.legend(fontsize=8.1)

    region = data["table"]["point_effects_and_intervals"]["five_mm_above_cutting_or_mark"]
    outcomes = [region[key] for key in ("bending_intact", "bending_cut", "tip_removed_without_bend")]
    effects = np.array([row["difference_per_plant"] for row in outcomes])
    bounds = np.array([row["independent_95_reference"] for row in outcomes])
    for i, color in enumerate((BLUE, BLUE, GREEN)):
        error = [[effects[i]-bounds[i, 0]], [bounds[i, 1]-effects[i]]]
        right.errorbar(i, effects[i], yerr=error, fmt="o", color=color, capsize=4, ms=6)
    right.axhline(0, color=GRAY, linewidth=.9)
    right.axhline(.5, color=GRAY, linewidth=.9, ls=":")
    right.text(2.46, .55, "0.5-root threshold", ha="right", color=GRAY, fontsize=8)
    right.set_xticks(np.arange(3), ["Bend\nintact tip", "Bend\nafter tip removal", "Remove tip\nno bend"])
    right.set_xlim(-.5, 2.5)
    style(right, "Change in lateral-root number · Table 1", "", "Extra roots per seedling in 5 mm")
    figure.supxlabel("Kircher & Schopfer (2016) · left: ±3 px digitization · right: 95% independence reference",
                       fontsize=9)
    figure.savefig(path, dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    options = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    folder = options.root / "return_path_figures"
    folder.mkdir(parents=True, exist_ok=True)
    return_paths(options.root, folder / "uptake.png")
    root_counts(options.root, folder / "root_controls.png")
