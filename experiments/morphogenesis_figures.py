"""Plot the material model and the independently published organ outcomes."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_summary(root, exp):
    return json.loads((root / exp / "summary.json").read_text(encoding="utf-8"))


def axial_section(values):
    return np.concatenate((values[::-1], values), axis=0).T


def growth(root, out):
    summary = read_summary(root, "E17/grid96")
    with np.load(root / "E17/grid96/fields.npz") as archive:
        values = {key: archive[key] for key in ("kinetic", "streamfunction", "resource_before_seed",
                                               "final_material", "seed", "r", "z")}
    figure, axes = plt.subplots(2, 3, figsize=(12, 7.6), layout="constrained")
    figure.suptitle("Same ring of kinetic energy, different growth", fontsize=16)
    extent = (-1, 1, -1, 1)
    x = np.r_[-values["r"][::-1], values["r"]]
    z = values["z"]
    stream = values["streamfunction"]
    index = {name: i for i, name in enumerate(summary["case_names"])}
    kinetic = axes[0, 0].imshow(axial_section(values["kinetic"]), origin="lower", extent=extent, cmap="magma")
    axes[0, 0].contour(x, z, axial_section(stream), levels=np.max(stream)*np.array([.30, .55, .80]),
                       colors="white", linewidths=.7)
    axes[0, 0].set_title("Kinetic energy and streamlines")
    figure.colorbar(kinetic, ax=axes[0, 0], shrink=.84, label="Kinetic energy density")
    c0 = values["resource_before_seed"]
    limits = max(c0[index["circulation"]].max(), c0[index["reversed"]].max())
    for ax, name, label in ((axes[0, 1], "circulation", "Resource before seed · circulation"),
                            (axes[0, 2], "reversed", "Resource before seed · reversed")):
        c_plot = ax.imshow(axial_section(c0[index[name]]), origin="lower", extent=extent, vmin=0, vmax=limits,
                           cmap="cividis")
        ax.set_title(label)
    figure.colorbar(c_plot, ax=axes[0, 1:], shrink=.84, label="Resource density")
    for ax, name, label in zip(axes[1], ("circulation", "reversed", "azimuthal"),
                              ("Final material · circulation", "Final material · reversed",
                               "Final material · azimuthal"), strict=True):
        material = ax.imshow(axial_section(values["final_material"][index[name]]),
                             origin="lower", extent=extent, vmin=0, vmax=1, cmap="viridis")
        ax.contour(x, z, axial_section(values["seed"]), levels=[.5*values["seed"].max()],
                   colors="white", linestyles="--", linewidths=1.)
        ax.set(title=label, xlabel="Horizontal position")
    figure.colorbar(material, ax=axes[1], shrink=.84, label="Material density")
    for ax in axes[:, 0]:
        ax.set_ylabel("Height")
    for ax in axes.ravel():
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
    figure.supxlabel("Dashed outline marks the initial seed · nondimensional coordinates", fontsize=10)
    figure.savefig(out, dpi=150)
    plt.close(figure)


def biological_outcomes(root, out):
    figure, (left, right) = plt.subplots(1, 2, figsize=(11.6, 4.6), layout="constrained")
    figure.suptitle("Local intervention before organ positioning", fontsize=15)
    heart = read_summary(root, "E16")["panels"]["G"]["groups"]
    positions = np.arange(3)
    selected = [heart[name] for name in ("flow_deficient", "left_stimulated", "right_stimulated")]
    fractions = np.array([np.mean(row["allowed_count_vectors"], axis=0) / row["n"] for row in selected])
    bottom = np.zeros(len(selected))
    for name, color, values in zip(("Left", "Middle", "Right"), ("#2769a0", "#927397", "#087e6e"),
                                   fractions.T, strict=True):
        left.bar(positions, values, bottom=bottom, width=.65, color=color, label=name)
        bottom += values
    left.set_xticks(positions, ["No stimulation\nn=53", "Left side\nn=51", "Right side\nn=49"])
    left.set(title="Zebrafish heart position", ylabel="Fraction of embryos", ylim=(0, 1.05))
    left.legend(loc="upper center", bbox_to_anchor=(.5, -.19), ncols=3, frameon=False, fontsize=9)

    leaves = read_summary(root, "E18")["leaf_initiation"]["groups"]
    for i, line in enumerate(("E1.7", "E1.8")):
        for suffix, color, shift in (("induced", "#6b5091", -.13), ("mock", "#6d737a", .13)):
            row = leaves[f"{line}_{suffix}"]["leaf_initiation"]
            center = row["fraction"]
            lo, hi = row["wilson95"]
            x = i+shift
            right.errorbar(x, center, yerr=[[center-lo], [hi-center]], fmt="o", color=color,
                           capsize=4, label=suffix.capitalize() if i==0 else None)
            right.annotate(f"{row['events']}/{row['n']}", (x, center), xytext=(0, 10),
                           textcoords="offset points", ha="center", fontsize=9)
    right.set_xticks([0,1], ["E1.7", "E1.8"])
    right.set(title="Tobacco leaf initiation", ylabel="Fraction of apices · Wilson 95% intervals",
              ylim=(-.02, .40), xlim=(-.5, 1.5))
    right.legend(loc="upper center", bbox_to_anchor=(.5, -.19), ncols=2, frameon=False, fontsize=9)
    for ax in (left, right):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", linewidth=.7, color="#e4e6e9")
        ax.set_axisbelow(True)
    figure.supxlabel("Djenoune et al. (2023), Fig. 4G · Pien et al. (2001), Table 1", fontsize=9)
    figure.savefig(out, dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    folder = args.root / "morphogenesis_figures"
    folder.mkdir(parents=True, exist_ok=True)
    growth(args.root, folder / "flow_and_growth.png")
    biological_outcomes(args.root, folder / "organ_position.png")
