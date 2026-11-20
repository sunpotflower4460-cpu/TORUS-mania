"""Plot the embryo and tracer-history measurements without copying source artwork."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BLUE = "#1e6490"
ORANGE = "#a34f1f"
GREEN = "#43705e"


def read(root, experiment):
    return json.loads((root / experiment / "summary.json").read_text())


def track_screen(axis, data, comparison):
    counts = data["track_analysis"]["screen_counts"]["primary"]
    totals = [
        sum(counts.values()),
        sum(value for key, value in counts.items() if key != "insufficient_travel"),
        sum(
            value
            for key, value in counts.items()
            if key not in ("insufficient_travel", "no_near_return")
        ),
        counts.get("curving_return", 0),
    ]
    labels = (
        "At least 10 positions",
        "Adequate travel",
        "Near start again",
        "Curving returns",
    )
    for row, (label, count) in enumerate(zip(labels, totals, strict=True)):
        axis.barh(
            row, np.log10(count + 1), color=BLUE if row < 3 else GREEN, height=0.64
        )
        axis.text(
            np.log10(count + 1) + 0.10, row, f"{count:,}", va="center", color="#243645"
        )
    axis.set_yticks(range(len(labels)), labels)
    axis.set_xlim(0, np.log10(totals[0] + 1) + 0.85)
    axis.set_xticks(
        np.log10(np.asarray([0, 10, 100, 1000, 10000, 100000]) + 1),
        ["0", "10", "100", "1k", "10k", "100k"],
    )
    axis.invert_yaxis()
    axis.set_xlabel("Tracking intervals (log scale)")
    axis.set_title("Zebrafish cell tracking")
    axis.grid(axis="x", alpha=0.18)


def track_example(axis, comparison, images):
    examples = comparison["same_id_for_all_frames_and_3d_rescore"]["relaxed"]
    example = next(
        row for row in examples if row["primary_track_id"] == images["E62_track_id"]
    )
    xyz = np.asarray(example["alternate_xyz_relative_to_start"])
    axis.plot(*xyz.T, color=BLUE, linewidth=2, label="Second tracking output")
    image_attempt = images["path_screen_by_prediction_radius"]["22"]
    raw = np.asarray(image_attempt["image_path_relative_to_first_position"])
    if raw.size:
        raw += (
            np.asarray(image_attempt["first_image_position_xyz"])
            - xyz[0]
            - np.asarray(example["alternate_start_xyz"])
        )
        axis.plot(
            *raw.T, color="#713475", marker=".", linewidth=2, label="Image-only attempt"
        )
    axis.scatter(*xyz[0], color=GREEN, s=42, label="Start", depthshade=False)
    axis.scatter(
        *xyz[-1], color=ORANGE, marker="x", s=50, label="Near return", depthshade=False
    )
    axis.set_box_aspect((1, 1, 0.9))
    width = max(np.ptp(xyz, axis=0)) / 2
    middle = (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    for center, setter in zip(
        middle, (axis.set_xlim, axis.set_ylim, axis.set_zlim), strict=True
    ):
        setter(center - width, center + width)
    axis.set(
        xlabel="Δx",
        ylabel="Δy",
        zlabel="Δz",
        title=f"Track {example['primary_track_id']:,} · archive units",
    )
    axis.legend(loc="upper left", frameon=False, fontsize=8)


def convergence(axis, tension):
    comparisons = (
        tension["figure_3_sandwich_growth_6_to_8_hours_survivors"][
            "convergence_um_per_hour"
        ],
        tension["figure_4e_stretcher_convergence_um_per_hour"],
    )
    for offset, comparison in zip((0, 3), comparisons, strict=True):
        for group, color, center in zip(
            ("control", "intervention"),
            (BLUE, ORANGE),
            (offset, offset + 1),
            strict=True,
        ):
            collect = comparison[group]
            values = collect["values"]
            x = center + np.linspace(-0.16, 0.16, len(values))
            axis.scatter(x, values, s=17, color=color, alpha=0.6)
            axis.hlines(
                collect["mean"], center - 0.28, center + 0.28, color=color, linewidth=2
            )
    axis.axhline(0, color="#68777d", linewidth=0.8)
    axis.set_xticks((0, 1, 3, 4), ("Control", "Sandwich", "Control", "Stretcher"))
    axis.set_ylabel("Axis convergence (µm/h)")
    axis.set_title("External tension and chick axis")
    axis.grid(axis="y", alpha=0.16)


def plot_embryo(root, out):
    fish = read(root, "E62")
    tension = read(root, "E63")
    comparison = read(root, "E65")
    images = read(root, "E66")
    fig = plt.figure(figsize=(10.6, 7.2), layout="constrained")
    track_screen(fig.add_subplot(2, 2, 1), fish, comparison)
    track_example(fig.add_subplot(2, 2, 2, projection="3d"), comparison, images)
    convergence(fig.add_subplot(2, 2, 3), tension)

    axis = fig.add_subplot(2, 2, 4)
    inflation = tension["figure_4b_inflation_timing_example"]
    t, width = np.asarray(inflation["time_s_and_width_um_single_embryo"][:-1]).T
    axis.plot(t, width, ".-", color=BLUE, label="One embryo")
    injections = inflation["published_injections_seconds"]
    for t_injection in injections:
        axis.axvline(t_injection, color=ORANGE, alpha=0.65, linestyle="--", linewidth=1)
    axis.plot([], [], "--", color=ORANGE, label="Inflation")
    axis.set(
        xlabel="Time (s)",
        ylabel="Posterior neural tube width (µm)",
        title="Width after inflation",
    )
    axis.legend(frameon=False, loc="upper left")
    fig.savefig(out / "embryo_paths_and_force.png", dpi=150)
    plt.close(fig)


def plot_root(root, out):
    data = read(root, "E64")
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.3), layout="constrained")
    palette = ("#b8ccd8", "#7196af", GREEN, "#ded294")
    labels = (
        "Other route, free",
        "Other route, conjugated",
        "Outer route, free",
        "Outer route, conjugated",
    )
    axis = axes[0]
    bottom = np.zeros(2)
    worlds = np.asarray(data["distinct_populations_for_the_same_marginals"])
    for heights, color, label in zip(worlds.T, palette, labels, strict=True):
        axis.bar(
            [0, 1],
            100 * heights,
            bottom=100 * bottom,
            color=color,
            label=label,
            width=0.65,
        )
        bottom += heights
    axis.set_xticks([0, 1], ["40% outer and free", "55% outer and free"])
    axis.set(
        ylabel="Share of recovered free label (%)",
        title="Same separate route and chemistry totals",
    )
    axis.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.11),
        ncol=2,
        fontsize=8,
    )

    axis = axes[1]
    select = [
        case
        for case in data["joint_readouts"]
        if case["route_and_chemistry_leakage_each"] <= 0.25
    ]
    for world, color, offset in ((0, GREEN, -0.22), (1, ORANGE, 0.22)):
        y = (
            np.array(
                [
                    case["simulation"]["500"][world]["central_95_percent"]
                    for case in select
                ]
            )
            * 100
        )
        x = (
            np.array([case["route_and_chemistry_leakage_each"] for case in select])
            * 100
            + offset
        )
        axis.vlines(x, y[:, 0], y[:, 1], color=color, linewidth=2)
        axis.scatter(x, (40, 55)[world] * np.ones(len(x)), color=color, s=24)
    axis.set(
        xticks=(0, 2, 10, 25),
        xlabel="Independent readout error of each tag (%)",
        ylabel="Recovered joint fraction (%)",
        title="Simulation with 500 joint readings",
    )
    axis.grid(axis="y", alpha=0.2)
    fig.savefig(out / "root_labels.png", dpi=150)
    plt.close(fig)


def plot(root):
    out = Path(root) / "embryo_history_figures"
    out.mkdir(parents=True, exist_ok=True)
    plot_embryo(root, out)
    plot_root(root, out)
