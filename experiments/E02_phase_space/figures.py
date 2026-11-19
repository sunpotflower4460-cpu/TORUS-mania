"""Compare simultaneous phase observations in the square, in 3D and over time."""

import matplotlib.pyplot as plt
import numpy as np

from experiments.common import ring_xyz


def plot_states(data, path):
    fig = plt.figure(figsize=(12, 13), layout="constrained")
    grid = fig.add_gridspec(5, 4, width_ratios=(1.1, 1.3, 1.25, 1))
    fig.suptitle("E02   One trajectory in two phase coordinates\n"
                 "First 8 s: time runs purple to yellow in both views   |   "
                 "Right: fraction of 80 s per cell", fontsize=14)
    t = data["t_128_s"]
    early = t < 8
    cases = [("single", "One clock"), ("three_halves", "3/2, free"),
             ("sqrt2", "√2, free"), ("lock", "3/2, coupled (K = 2)"), ("noise_11", "3/2, noisy (seed 11)")]
    for row, (name, title) in enumerate(cases):
        key = f"{name}_128"
        samples = data[key + "/observed_rad"][early] / (2 * np.pi) % 1
        phi, theta = samples.T
        ax = fig.add_subplot(grid[row, 0])
        ax.scatter(phi, theta, c=t[early], vmin=0, vmax=8, s=2)
        ax.set(xlabel="Phase 1 (turns)", ylabel="Phase 2 (turns)", aspect="equal",
               xlim=(0, 1), ylim=(0, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1])
        ax.set_title(title, fontsize=11)
        ax = fig.add_subplot(grid[row, 1], projection="3d", proj_type="ortho")
        xyz = ring_xyz(phi * 2 * np.pi, theta * 2 * np.pi)
        # A faint mesh shows the assigned display surface, even for the one-clock control.
        v = np.linspace(0, 2 * np.pi, 25)
        mesh = ring_xyz(v[:, None], v[None, :])
        ax.plot_wireframe(*mesh.transpose(2, 0, 1), rstride=2, cstride=3, color="0.77", lw=0.45)
        ax.scatter(*xyz.T, c=t[early], vmin=0, vmax=8, s=3, depthshade=False)
        ax.set_box_aspect((3, 3, 1))
        ax.view_init(25, -50)
        ax.set_axis_off()
        if row == 0:
            ax.set_title("Same points on assigned T²", fontsize=10)
        ax = fig.add_subplot(grid[row, 2])
        ax.plot(t, data[key + "/delta_rad"], color="#365d7b", lw=1.0)
        ax.set(xlabel="Time (s)", ylabel="Phase 2 − phase 1 (rad)", xlim=(0, 80))
        if row == 0:
            ax.set_title("Unwrapped phase difference", fontsize=10)
        counts = data[key + "/density_80s"]
        ax = fig.add_subplot(grid[row, 3])
        # Same color scale in every row; high cells saturate at 5%.
        ax.imshow(counts.T / counts.sum(), origin="lower", extent=(0, 1, 0, 1), vmin=0, vmax=0.05,
                  cmap="magma", interpolation="nearest")
        ax.set(xlabel="Phase 1 (turns)", ylabel="Phase 2 (turns)", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1])
        ax.set_title(f"{np.count_nonzero(counts)} / 256 occupied", fontsize=10)
    fig.colorbar(ax.images[0], ax=fig.axes[-1], location="bottom", shrink=0.85,
                 ticks=[0, 0.025, 0.05], label="Sample fraction (≥0.05 at top)")
    fig.savefig(path, dpi=125)
    plt.close(fig)
