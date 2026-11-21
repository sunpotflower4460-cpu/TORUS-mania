"""Plot measurements and sampled trajectories derived from E55–E60."""

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

BLUE, ORANGE, GREEN, GRAY = "#286185", "#a85225", "#287267", "#687483"


def style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e2e8ed", linewidth=0.65)
    ax.spines[["top", "right"]].set_visible(False)


def root_figure(data, out):
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.3), layout="constrained")
    chromatography, local, washout, regeneration = axes.ravel()
    for ax in axes.ravel():
        style(ax)
    profile = data[55]["apical_5mm_of_shoot_excised_root_fig5b"]
    chromatography.bar(profile["fraction_retention_min"], profile["dpm"], color=BLUE, width=0.8)
    for name, color, label in (
        ("oxIAA_Glc", GREEN, "oxIAA conjugate"),
        ("oxIAA", "#6b91af", "oxIAA"),
        ("possible_free_IAA", ORANGE, "Free IAA window"),
    ):
        left, right = profile["peak_windows"][name]["inclusive_minutes"]
        chromatography.axvspan(left - 0.5, right + 0.5, color=color, alpha=0.29, label=label)
    chromatography.set(
        xlabel="HPLC retention (min)",
        ylabel="Disintegrations per minute",
        title="Label recovered at the root tip after 8 h",
    )
    chromatography.legend(frameon=False, loc="upper left", fontsize=8)
    synthesis = data[56]["relative_new_label_measure_fig4a"]["values_intact_then_excised"]
    for ys, style_label, col in zip(
        synthesis, ("Intact seedling", "Shoot excised"), (BLUE, ORANGE), strict=True
    ):
        local.plot([0.25, 0.75, 1.25, 1.75], ys, "o-", label=style_label, color=col)
    local.set(
        xlabel="Distance from root tip (mm)",
        ylabel="Newly labeled / unlabeled IAA",
        ylim=(0, 1.2),
        title="New IAA label after 24 h in heavy water",
    )
    local.legend(frameon=False, loc="lower left", fontsize=8)
    wash = data[57]["washout_fig3h"]
    for idx, label, col in ((0, "1 h exposure", ORANGE), (1, "10 min exposure", BLUE)):
        times = np.arange(7) * 5
        washout.plot(
            times, wash["normalized_above_own_baseline_from_after"][idx], "o-", color=col, label=label
        )
    washout.axhline(0, color=GRAY, linestyle=":", linewidth=1)
    washout.set(
        xlabel="Minutes since washout began",
        ylabel="Fraction of the starting FRET excess",
        title="Clearance depends on exposure duration",
    )
    washout.legend(frameon=False, loc="upper right", fontsize=8)
    conjugate = data[60]["conjugated_D2_IAA_Asp"]["wt_then_mutant_samples"]
    free = data[60]["released_free_D2_IAA"]["wt_then_mutant_samples"]
    for offset, name, grp, col in (
        (-0.15, "Wild type", 0, BLUE),
        (0.15, "Four hydrolases disrupted", 1, ORANGE),
    ):
        for x, values in enumerate((conjugate[grp], free[grp])):
            regeneration.scatter(
                x + offset + np.linspace(-0.035, 0.035, len(values)),
                values,
                color=col,
                s=27,
                label=name if not x else None,
            )
    regeneration.set(
        xticks=[0, 1],
        xticklabels=["Labeled IAA–Asp", "Labeled free IAA"],
        xlim=(-0.4, 1.4),
        ylabel="pmol per g fresh weight (log scale)",
        yscale="log",
        ylim=(0.025, 800),
        title="Free IAA regenerated from a labeled conjugate",
    )
    regeneration.legend(frameon=False, loc="upper left", fontsize=8)
    fig.savefig(out / "root_chemistry.png", dpi=155)
    plt.close(fig)


def embryo_figure(data, out):
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.3), layout="constrained")
    velocity, track, plane, arc = axes.ravel()
    for ax in axes.ravel():
        style(ax)
    movie = data[58]
    valid = [w for w in movie["minute_windows_and_tail"] if all(w["n_center_and_shell_segments"])]
    values = np.array([w["center_and_shell_median_axial_um_per_s"] for w in valid])
    for i, label, col in ((0, "Central region", BLUE), (1, "Outer region", ORANGE)):
        velocity.plot(np.arange(len(valid)) + 0.5, values[:, i], "o-", color=col, label=label)
    velocity.axhline(0, color=GRAY, linewidth=0.8, linestyle=":")
    velocity.set(
        xlabel="Minute of the same embryo recording",
        ylabel="Median screen-axis velocity (µm/s)",
        title="Opposite motion persists across seven one-minute windows",
    )
    velocity.legend(frameon=False, fontsize=8)
    scale = movie["pixels_per_um"]
    cx, cy = movie["tracking_primary"]["ellipse_center"]
    rx, ry = movie["tracking_primary"]["ellipse_radii_pixels"]
    track.add_patch(
        Ellipse((0, 0), 2 * rx / scale, 2 * ry / scale, facecolor="#f6f7f8", edgecolor="#9ba5ad", lw=1.1)
    )
    for i, t in enumerate(movie["longest_example_tracks"]):
        xy = (np.asarray(t["xy_pixels"]) - [cx, cy]) / scale
        col = [BLUE, ORANGE, GREEN, "#84538d"][i % 4]
        track.plot(xy[:, 0], -xy[:, 1], color=col, linewidth=1.2)
        track.scatter(xy[0, 0], -xy[0, 1], s=15, color=col)
    track.set(
        xlabel="Longitudinal image axis (µm)",
        ylabel="Cross-axis position (µm)",
        title="Seven longest continuous tracks (points mark starts)",
        xlim=(-25, 25),
        ylim=(-13, 13),
        aspect="equal",
    )
    for ax, key, title in (
        (plane, "fig5b_plane", "Plane cut near the centrosome"),
        (arc, "fig5h_arc", "Arc cut near the anterior cortex"),
    ):
        graph = data[59][key]
        for ys, name, col in zip(graph["uncut_and_cut_um"], ("Uncut", "Cut"), (BLUE, ORANGE), strict=True):
            ax.plot(graph["times_s"], ys, "o-", ms=2.4, linewidth=1.6, color=col, label=name)
        ax.axvline(0, color=GRAY, linewidth=0.8, linestyle=":")
        ax.set(xlabel="Seconds relative to cutting", ylabel="Mean displacement (µm)", title=title)
        ax.legend(frameon=False, loc="upper left", fontsize=8)
    fig.savefig(out / "embryo_flow.png", dpi=155)
    plt.close(fig)


def run(root):
    out = root / "particle_return_figures"
    out.mkdir(exist_ok=True, parents=True)
    data = {i: json.loads((root / f"E{i}" / "summary.json").read_text()) for i in range(55, 61)}
    root_figure(data, out)
    embryo_figure(data, out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root)
