"""Plot the reanalysed root transport and embryo mechanics results."""

import matplotlib.pyplot as plt
import numpy as np

from experiments.E76_energy_closure.run import SEEDS, straight, trace, with_torus
from experiments.iaa_embryo_figures import BLUE, GRAY, GREEN, ORANGE, PURPLE, read


def root_panels(results, out):
    fig, (transverse, axial) = plt.subplots(
        1, 2, figsize=(10.6, 4.2), layout="constrained"
    )
    ninety = read(results, 74)["table_i_at_90_min"]
    for direction, label, offset, color in (
        ("above", "Upward", -0.18, BLUE),
        ("below", "Downward", 0.18, GREEN),
    ):
        centers = np.arange(len(ninety)) + offset
        transverse.bar(
            centers,
            [row[f"receiver_{direction}_mean_cpm"] for row in ninety.values()],
            yerr=[row[f"receiver_{direction}_sd_cpm"] for row in ninety.values()],
            width=0.32,
            color=color,
            capsize=4,
            label=label,
        )
    transverse.set(
        xticks=(0, 1),
        xticklabels=("No added calcium", "10 mM CaCl₂ in receiver"),
        ylabel="Opposite receiver (cpm, mean ± SD)",
        title="Label crossing an intact root · 90 min",
    )
    transverse.legend(frameon=False)
    transverse.grid(axis="y", alpha=0.2)

    data = read(results, 75)
    ratio = "toward_shoot_to_toward_tip_ratio_of_reported_means"
    conditions = (
        "control_ph6",
        "control_ph4_5",
        "calcium_chloride_5_mM",
        "aluminum_chloride_5_mM",
    )
    for key, label, marker, color in (
        ("table_1_cap_present_dpm", "Cap present", "o", BLUE),
        ("table_2_cap_removed_dpm", "Cap removed", "s", ORANGE),
    ):
        axial.scatter(
            range(len(conditions)),
            [data[key][c][ratio] for c in conditions],
            label=label,
            marker=marker,
            color=color,
        )
    axial.axhline(1, color=GRAY, linewidth=1, linestyle="--")
    axial.set(
        xticks=range(len(conditions)),
        xticklabels=("pH 6", "pH 4.5", "CaCl₂", "AlCl₃"),
        ylabel="Shootward / tipward receiver counts",
        title="Axial polarity in separate root segments · 3 h",
        yscale="log",
        ylim=(0.48, 12),
    )
    axial.legend(frameon=False)
    axial.grid(axis="y", alpha=0.2)
    fig.savefig(out / "root_transverse_and_axial_iaa.png", dpi=150)
    plt.close(fig)


def force_panel(axis, result):
    observations = result["figure_4e_forces_nn"]
    time = np.array(observations["times_min"])
    early = time <= 120
    for group, color, title in (
        ("vehicle", BLUE, "Vehicle"),
        ("rock_inhibition", PURPLE, "ROCK inhibition"),
    ):
        force = np.array(observations[f"{group}_at_each_time"], dtype=float)[early]
        axis.plot(time[early], force, color=color, alpha=0.17, linewidth=1)
        axis.plot(
            time[early], np.nanmean(force, axis=1), "o-", color=color, label=title
        )
    axis.axhline(0, color=GRAY, linewidth=1)
    axis.set(
        title="Forces on the chick neural-fold sensor",
        xlabel="Minutes",
        ylabel="Inward force (nN)",
    )
    axis.legend(frameon=False)


def work_panel(axis, result):
    for row in result["figure_4be_matched_vehicle_sensor_work"]:
        axis.plot(
            row["times_min"],
            row["cumulative_sensor_work_pj"],
            "o-",
            color=BLUE,
            alpha=0.26,
            markersize=2,
        )
    example = result["extended_figure_8_example"]
    axis.plot(
        example["times_min"],
        example["cumulative_pj"],
        color=ORANGE,
        label="Separate widening example",
    )
    axis.plot([], [], "o-", color=BLUE, label="Matched vehicle data")
    axis.set(
        title="Work estimated on the local sensor",
        xlabel="Minutes",
        ylabel="Cumulative work (pJ)",
    )
    axis.legend(frameon=False)


def power_display_panel(axis, result):
    stages = result["primary"]["stages"]
    data = np.array([row["warm_end"]["top_middle_bottom_counts"] for row in stages])
    stages_percent = [row["epiboly_percent"] for row in stages]
    for idx, color, label in zip(
        range(3),
        (BLUE, GRAY, ORANGE),
        ("Upper third", "Middle third", "Lower third"),
        strict=True,
    ):
        axis.bar(
            stages_percent,
            data[:, idx],
            width=11,
            bottom=data[:, :idx].sum(axis=1),
            color=color,
            label=label,
        )
    axis.text(40, 6, "No selected\nwarm pixels", ha="center", va="bottom", fontsize=8)
    axis.set(
        title="Warm pixels in published power display",
        xticks=stages_percent,
        xlabel="Epiboly stage (%) · one zebrafish embryo",
        ylabel="Warm pixel count",
    )
    axis.legend(frameon=False)


def energy_paths(axis):
    paths = trace(with_torus, SEEDS[:3], 128)
    axis.plot(*paths[:, 0].T, color=BLUE, label="Closed core path")
    axis.plot(*paths[:, 1].T, color=BLUE, alpha=0.45)
    axis.plot(*paths[:, 2].T, color=BLUE, alpha=0.45)
    line = trace(straight, SEEDS[:1], 128)[:, 0]
    axis.plot(*line[line[:, 2] < 1].T, color=ORANGE, label="Same seed, uniform flux")
    axis.scatter(*SEEDS[0], color="#232323", s=18)
    axis.set(
        xlim=(-1, 1),
        ylim=(-1, 1),
        zlim=(-1, 1),
        xticks=(-1, 0, 1),
        yticks=(-1, 0, 1),
        zticks=(-1, 0, 1),
        xlabel="x",
        ylabel="y",
        zlabel="z",
        title="Same boundary flux, different paths",
    )
    axis.set_box_aspect((1, 1, 1))
    axis.legend(frameon=False, loc="upper right", fontsize=8)


def embryo_panels(results, out):
    fig = plt.figure(figsize=(10.6, 8.6), layout="constrained")
    work = read(results, 72)
    force_panel(fig.add_subplot(2, 2, 1), work)
    work_panel(fig.add_subplot(2, 2, 2), work)
    power_display_panel(fig.add_subplot(2, 2, 3), read(results, 73))
    energy_paths(fig.add_subplot(2, 2, 4, projection="3d"))
    fig.savefig(out / "measured_work_and_flux_paths.png", dpi=150)
    plt.close(fig)


def plot(results):
    directory = results / "calibrated_formation_figures"
    directory.mkdir(parents=True, exist_ok=True)
    root_panels(results, directory)
    embryo_panels(results, directory)
