"""Render fixed observations; rotate the camera or move the common time marker with the CLI."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

POS, NEG, ZERO = "#008882", "#bd5636", "#74797b"
COORD_COLORS = ("#3763a2", "#008882", "#a75e0e")
LABELS = {"circle": "Uniform circle", "helix": "Translating helix", "linear_spring": "Straight spring",
          "variable_circle": "Variable speed", "one_winding": "One winding", "two_windings": "Two windings"}


def plot_motions(data, path, marked_time=0.375, azimuth=-55):
    t = data["base_128/t_s"]
    if not t[0] <= marked_time <= t[-1]:
        raise ValueError("Time must lie in the saved interval [0, 2] s.")
    mark = int(np.argmin(np.abs(t - marked_time)))
    fig = plt.figure(figsize=(14, 13), layout="constrained")
    grid = fig.add_gridspec(len(LABELS), 5, width_ratios=(1.15, 1, 1, 1, 1.9))
    fig.suptitle(f"E01   Physical trajectory, projections and time record\n"
                 f"Same sample (black circle) at t = {t[mark]:g} s   |   "
                 "Teal: positive y velocity   /   Rust: negative", fontsize=15)
    for row, (name, label) in enumerate(LABELS.items()):
        prefix = "base_128/" + name
        xyz = data[prefix + "/xyz_m"]
        vy = data[prefix + "/vy_m_s"]
        colors = np.select([vy > 0, vy < 0], [POS, NEG], default=ZERO)
        # Keep the three spatial views at the same scale within each row.
        limit = max(1.15, 1.08 * np.abs(xyz).max())
        camera = fig.add_subplot(grid[row, 0], projection="3d", proj_type="ortho")
        camera.scatter(*xyz.T, c=colors, s=3, depthshade=False)
        camera.scatter(*xyz[mark], facecolors="none", edgecolors="black", s=55, depthshade=False)
        camera.view_init(22, azimuth)
        camera.set(xlim=(-limit, limit), ylim=(-limit, limit), zlim=(-limit, limit),
                   xticks=[], yticks=[], zticks=[], xlabel="x", ylabel="y", zlabel="z")
        camera.set_box_aspect((1, 1, 1))
        camera.set_title(label + "  (3D)", fontsize=10)
        for column, (a, b) in enumerate(((0, 2), (1, 2), (0, 1)), start=1):
            ax = fig.add_subplot(grid[row, column])
            ax.scatter(xyz[:, a], xyz[:, b], c=colors, s=4)
            ax.scatter(xyz[mark, a], xyz[mark, b], facecolors="none", edgecolors="black", s=50)
            ax.set(xlabel="xyz"[a] + " (m)", ylabel="xyz"[b] + " (m)", aspect="equal",
                   xlim=(-limit, limit), ylim=(-limit, limit))
            if row == 0:
                ax.set_title(("Front", "Side", "Top")[column - 1])
        ax = fig.add_subplot(grid[row, 4])
        for k, color in enumerate(COORD_COLORS):
            ax.plot(t, xyz[:, k], label="xyz"[k], color=color, lw=1.35)
            ax.scatter(t[mark], xyz[mark, k], facecolors="none", edgecolors="black", s=28, zorder=3)
        ax.axvline(t[mark], color="0.55", lw=0.8, ls=":")
        ax.set(xlabel="Time (s)", ylabel="Position (m)", xlim=(0, 2))
        if row == 0:
            ax.set_title("Coordinate history")
            ax.legend(ncols=3, loc="upper right", fontsize=8)
    fig.savefig(path, dpi=125)
    plt.close(fig)


def plot_surfaces(surfaces, path):
    fig = plt.figure(figsize=(12, 7), layout="constrained")
    fig.suptitle("E01   Five prescribed surfaces, identical cameras and scales\n"
                 "Top and front views include all samples, including the hidden side", fontsize=14)
    grid = fig.add_gridspec(3, 5)
    for col, (name, mesh) in enumerate(surfaces):
        x, y, z = mesh.transpose(2, 0, 1)
        ax = fig.add_subplot(grid[0, col], projection="3d", proj_type="ortho")
        ax.plot_wireframe(x, y, z, rstride=5, cstride=4, color="#356872", linewidth=0.55)
        ax.view_init(22, -55)
        ax.set(xlim=(-3.1, 3.1), ylim=(-3.1, 3.1), zlim=(-1.55, 1.55))
        ax.set_box_aspect((2, 2, 1))
        ax.set_axis_off()
        ax.set_title(name.replace("_", " ").title(), fontsize=11)
        for row, (vertical, label, h) in enumerate(((y, "y", 3.1), (z, "z", 1.55)), start=1):
            ax = fig.add_subplot(grid[row, col])
            ax.scatter(x, vertical, s=0.3, color="#356872", alpha=0.6)
            ax.set(xlabel="x (m)", ylabel=label + " (m)", aspect="equal", xlim=(-3.1, 3.1), ylim=(-h, h))
    fig.savefig(path, dpi=125)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("figure", type=Path)
    parser.add_argument("--time", type=float, default=0.375)
    parser.add_argument("--azimuth", type=float, default=-55)
    args = parser.parse_args()
    with np.load(args.observations) as data:
        plot_motions(data, args.figure, args.time, args.azimuth)
