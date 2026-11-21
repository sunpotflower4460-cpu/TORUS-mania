"""Draw new figures from the numeric results of the two hypothesis tests."""

import json

import matplotlib.pyplot as plt
import numpy as np

BLUE = "#236986"
PURPLE = "#753967"
ORANGE = "#a85c29"
GREEN = "#477961"
GRAY = "#70818b"


def read(results, number):
    return json.loads((results / f"E{number}" / "summary.json").read_text())


def root_panels(results, out):
    root = read(results, 68)["maize_kerk_figure_8"]["panels"]
    uptake = read(results, 71)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2), layout="constrained")
    names = (
        "no_tissue",
        "terminal_mm_with_cap",
        "terminal_mm_without_cap",
        "subtending_root",
    )
    labels = ("No tissue", "Tip with cap", "Tip without cap", "Adjacent tissue")
    rates = np.array(
        [root[name]["fractional_14C_loss_of_displayed_envelope"] for name in names]
    )
    bounds = np.array(
        [root[name]["range_varying_mask_thresholds_and_baseline"] for name in names]
    )
    axis = axes[0]
    axis.bar(
        np.arange(len(names)), 100 * rates, color=(GRAY, GREEN, BLUE, BLUE), width=0.62
    )
    axis.errorbar(
        range(len(names)),
        100 * rates,
        100 * np.abs(bounds.T - rates),
        fmt="none",
        color="#333333",
        capsize=3,
    )
    axis.set_xticks(range(len(names)), labels, rotation=17, ha="right")
    axis.set_ylabel("Signal lost in plotted envelope (%)")
    axis.set_title("Loss of carboxyl carbon label")
    axis.grid(axis="y", alpha=0.20)

    axis = axes[1]
    root_tissues = uptake["table_i_and_page_894"]["uptake_over_4_minutes"]
    tissues = ("stele", "cortex", "whole_2_to_7_mm_region")
    sat = [
        root_tissues[tissue]["saturable_pmol_per_g_fresh_mass_per_4min"]
        for tissue in tissues
    ]
    non_sat = [
        root_tissues[tissue]["nonsaturable_pmol_per_g_fresh_mass_per_4min"]
        for tissue in tissues
    ]
    axis.bar(range(3), sat, width=0.6, color=BLUE, label="Saturable")
    axis.bar(
        range(3), non_sat, bottom=sat, width=0.6, color=ORANGE, label="Nonsaturable"
    )
    axis.set_xticks(range(3), ("Stele", "Cortex", "Whole segment"))
    axis.set_ylabel("IAA uptake over 4 min (pmol / g fresh mass)")
    axis.set_title("Uptake by isolated root tissues")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.20)
    fig.savefig(out / "root_tracer_and_uptake.png", dpi=150)
    plt.close(fig)


def image_paths(axis, result):
    reference = np.array(result["centered_reference_track_xyz"])
    initial_xyz = np.array(result["reference_start_xyz"])
    axis.plot(*reference.T, color=BLUE, label="Published tracking")
    for key, color in (("forward, 0.65", GREEN), ("forward, 0.50", ORANGE)):
        row = result["normalized_template_match"][key]
        relative = np.array(row["image_path_relative_to_first_position"])
        path = relative + np.array(row["first_image_position_xyz"]) - initial_xyz
        axis.plot(
            *path.T, color=color, linewidth=1.6, label=f"Image tracking · {key[-4:]}"
        )
        axis.scatter(*path[-1], color=color, marker="x", s=45)
    axis.set_box_aspect((1, 1, 0.8))
    axis.set(xlabel="Δx", ylabel="Δy", zlabel="Δz", title="Nucleus candidate in 3D")
    axis.legend(frameon=False, fontsize=7)


def extension(axis, result):
    colors = (BLUE, PURPLE, ORANGE)
    for color, (group, row) in zip(colors, result["figure_1c"].items(), strict=True):
        time = np.array([float(t) for t in row])
        length = [x["relative_mean_length"] for x in row.values()]
        axis.plot(time, length, "o-", color=color, label=group)
    axis.set(
        xlabel="Minutes after activation",
        ylabel="Length relative to onset",
        title="Drosophila germband elongation",
    )
    axis.grid(alpha=0.18)
    axis.legend(frameon=False)


def meridian(axis, result):
    angle = np.linspace(-np.pi / 2, np.pi / 2, 181)
    axis.plot(100 * np.cos(angle), 100 * np.sin(angle), color=GRAY, linewidth=1)
    for color, ring in zip(
        (BLUE, GREEN, ORANGE), result["meridional_curves"], strict=True
    ):
        coords = np.array(ring["r_z_m"]) * 1e6
        axis.plot(
            *coords.T, color=color, label=f"{ring['normalized_meridional_radius']:.2f}"
        )
    axis.set(
        xlabel="Radius (µm)",
        ylabel="Height (µm)",
        title="Section through material tori",
    )
    axis.set_aspect("equal")
    axis.legend(frameon=False, title="Surface level", loc="upper right", fontsize=8)


def energy(axis, result):
    data = result["surfaces_and_energy_budgets"]
    for color, viscosity in zip((GRAY, BLUE, ORANGE), (0, 0.001, 0.01), strict=True):
        rows = [row for row in data if row["viscosity_Pa_s"] == viscosity]
        q = [row["motion_surface_level"] for row in rows]
        power = [
            -row["resolutions"][-1]["integrated_outward_W"]["total"] * 1e16
            for row in rows
        ]
        d = [row["resolutions"][-1]["viscous_dissipation_W"] * 1e16 for row in rows]
        axis.plot(q, power, "o-", color=color, label=f"Viscosity {viscosity:g} Pa s")
        axis.scatter(q, d, marker="+", color="black", zorder=3, s=28)
    axis.scatter([], [], marker="+", color="black", label="Internal dissipation")
    axis.set(
        xlabel="Nested surface level",
        ylabel="Net inward power (10⁻¹⁶ W)",
        title="Energy crossing the material surface",
        xticks=(0.2, 0.55, 0.8),
    )
    axis.legend(frameon=False, fontsize=8)
    axis.grid(alpha=0.18)


def embryo_panels(results, out):
    fig = plt.figure(figsize=(9.8, 7.7), layout="constrained")
    image_paths(fig.add_subplot(2, 2, 1, projection="3d"), read(results, 67))
    extension(fig.add_subplot(2, 2, 2), read(results, 69))
    bound = read(results, 70)
    meridian(fig.add_subplot(2, 2, 3), bound)
    energy(fig.add_subplot(2, 2, 4), bound)
    fig.savefig(out / "embryo_paths_and_mechanical_power.png", dpi=150)
    plt.close(fig)


def plot(results):
    out = results / "iaa_embryo_figures"
    out.mkdir(parents=True, exist_ok=True)
    root_panels(results, out)
    embryo_panels(results, out)
