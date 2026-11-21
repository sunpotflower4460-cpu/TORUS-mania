"""Plot pathway discrimination, embryo outcomes, and matched-energy flow."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiments.return_energy_figures import BLUE, GRAY, GREEN, ORANGE, PURPLE, axes, load


def route_and_formation(root, out):
    route = load(root, "E40")["timeseries"]
    flow = load(root, "E43")["trials"]["fine"]
    fig, grid = plt.subplots(2, 2, figsize=(12.1, 7.8), layout="constrained")
    top, middle, left, right = grid.flat
    for key, color, fmt, label in (
        ("ordinary_outer_route_trajectories", GREEN, "-", "Through outer layer"),
        ("ordinary_bypass_route_trajectories", ORANGE, "--", "Through bypass"),
    ):
        upper = np.asarray(route[key])[:,4]
        top.plot(route["ordinary_times"], 100*upper, fmt, color=color, lw=2, label=label)
    axes(top, "Ordinary tracer signal is identical", "Model time", "Inner region (% of input)")
    top.legend(loc="lower right", fontsize=8.5)
    for key, color, style, label in (
        ("outer", GREEN, "-", "Outer return"),
        ("bypass", ORANGE, "--", "Bypass, 2% mislabelling"),
        ("cut", GRAY, ":", "Outer return cut"),
    ):
        middle.plot(route["first_return_times"], 100*np.array(route["first_return_traces_at_two_percent_mislabel"][key]),
                    color=color, ls=style, lw=2, label=label)
    axes(middle, "Marking outer passage separates the routes", "Model time", "First return (% of input)")
    middle.legend(loc="upper left", fontsize=8.5)

    for k, axis, title, legend in (
        ("theta", left, "Material across the tube cross-section", True),
        ("phi", right, "Material around the torus axis", False),
    ):
        locations = np.array(flow[k + "_centers"])
        for group, color, label in (
            ("closed_theta", BLUE, "Cross-sectional flow"),
            ("closed_phi", GREEN, "Around-axis flow"),
            ("cut_theta", ORANGE, "Cross-sectional return cut"),
        ):
            values = 100*np.array(flow["cases"][group][k+"_material_marginal"]) / (360/len(locations))
            axis.plot(np.degrees(locations), values, lw=2, color=color, label=label)
        axis.set_xlim(0, 360)
        axis.set_xticks([0,90,180,270,360])
        axes(axis, title, "Angle (degrees)", "Deposited material (% of input per degree)")
        if legend:
            axis.legend(loc="upper left", fontsize=8)
    fig.supxlabel("E40 and E43 are transport models. The E43 flows have identical kinetic energy density.", fontsize=9)
    fig.savefig(out/"tracer_and_flow_paths.png", dpi=150)
    plt.close(fig)


def embryology(root, out):
    fly, fish = load(root, "E41"), load(root, "E42")
    fig, (first, second, third) = plt.subplots(1, 3, figsize=(14.2, 4.7), layout="constrained")
    profiles = fly["fig3_approximate_stage10B_profiles"]
    for key, color, label in (
        ("control", GREEN, "Control"),
        ("sliding_reduced_Khc_mutA", BLUE, "Reduced streaming"),
    ):
        r=profiles[key]
        first.plot(r["relative_cortex_positions"], r["approximate_mean"], color=color, lw=2, label=label)
    axes(first, "Late oocyte posterior marker", "Relative position at cortex", "Normalized Staufen intensity")
    first.legend(loc="upper right", fontsize=8)

    fly_keys = ("control", "sliding_reduced_Khc_mutA", "Khc_RNAi", "streaming_rescue")
    loc = np.arange(len(fly_keys))
    for offset, block, k, color, label in (
        (-.16, "fig4C_pole_cell_specification", "pole_cell_percent", PURPLE, "Pole cells"),
        (.16, "table1_hatching", "percent_hatched", ORANGE, "Hatched"),
    ):
        second.bar(loc+offset, [fly[block][r][k] for r in fly_keys], .29, color=color, label=label)
    second.set(xticks=loc, xticklabels=["Control", "Reduced\nstreaming", "Khc\nRNAi", "Streaming\nrescue*"], ylim=(0,116))
    second.legend(loc="upper right", fontsize=8)
    axes(second, "Pole cells and hatching", "", "Reported percentage")

    for j, key in enumerate(("control","Control ablation","NC ablation","PC ablation")):
        r = fish["lumen_center_speed_um_per_min"]["groups"][key]
        points = list(r["embryo_means"].values())
        third.scatter(j+np.linspace(-.15,.15,len(points)),points,color=BLUE,alpha=.78,s=22)
        third.hlines(r["mean_of_embryos"],j-.23,j+.23,color=ORANGE,lw=2.4)
    third.set(xticks=range(4), xticklabels=["Control","Sham","Notochord\nremoved","Posterior cells\nremoved"])
    axes(third, "Embryonic organizer movement", "", "Lumen-center speed (μm/min)")
    fig.supxlabel("Lu et al. (2018) and Manna et al. (2025) · *Pole-cell scoring for the rescue was affected by early arrest.",
                  fontsize=9)
    fig.savefig(out/"embryonic_formation.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10})
    folder = root/"path_formation_figures"
    folder.mkdir(parents=True, exist_ok=True)
    route_and_formation(root,folder)
    embryology(root,folder)
