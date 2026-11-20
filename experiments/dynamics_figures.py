"""Draw the material flux, moving energy budgets, and published PIV comparison."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BLUE = "#256092"
ORANGE = "#b35519"
GREEN = "#197764"
PURPLE = "#76519a"
GRAY = "#626974"


def output(path, size, title):
    fig, axes = plt.subplots(*size, figsize=(12, 4.4 if size[0] == 1 else 7.4), layout="constrained")
    fig.suptitle(title, fontsize=15)
    path.parent.mkdir(parents=True, exist_ok=True)
    return fig, axes


def axes_for_curves(ax, title, xlabel, ylabel):
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.grid(axis="y", color="#e1e4e9", linewidth=.7)
    ax.set_axisbelow(True)
    ax.spines[["right", "top"]].set_visible(False)


def flux(root, out):
    initial = root / "E13/diffusive48"
    config = json.loads((initial / "summary.json").read_text(encoding="utf-8"))
    with (np.load(initial / "histories.npz") as data,
          np.load(root / "E13/ideal48/histories.npz") as ideal):
        t = data["t_s"]
        ideal_flux = ideal["flux"][:, :, 0].mean(axis=1)
        fig, (left, right) = output(out, (1, 2), "A transported ring can lose flux while retaining its shape")
        left.plot(t, ideal_flux / ideal_flux[0], color=GREEN, lw=2.2, label="Ideal (vorticity and field)")
        options = [("matched", BLUE, "Matched diffusivity"), ("faster_diffusion", ORANGE, "Fast magnetic diffusion"),
                   ("shifted", PURPLE, "Offset initial field")]
        for name, color, label in options:
            index = config["names"].index(name)
            section_flux = data["flux"][:, :, index].mean(axis=1)
            left.plot(t, section_flux / section_flux[0], color=color, lw=2.1, label=label)
            energy = data["energy"][:, index]
            right.plot(t, energy / energy[0], color=color, lw=2.1, label=label)
        kinetic = data["energy"][:, 0]
        right.plot(t, kinetic / kinetic[0], color=GRAY, linestyle="--", lw=2.1, label="Fluid kinetic energy")
        magnetic_ideal = data["energy"][:, config["names"].index("magnetic_ideal")]
        right.plot(t, magnetic_ideal / magnetic_ideal[0], color=GREEN, linestyle=":", lw=2.3,
                   label="Ideal magnetic field")
        axes_for_curves(left, "Moving cross-section", "Time (s)", "Flux / initial flux")
        axes_for_curves(right, "Whole periodic volume", "Time (s)", "Energy / initial energy")
        left.legend(fontsize=8.5)
        right.legend(fontsize=8.5)
        fig.savefig(out, dpi=150)
        plt.close(fig)


def energy(root, out):
    fig, axes = output(out, (2, 2), "Energy exchange across a surface moving with the ring")
    for (left, right), variant, label, time_label in zip(
        axes, ("light20", "flow64"), ("Vacuum light pulse", "Viscous jet"),
        ("Time (light crossing units)", "Time (s)"), strict=True
    ):
        with np.load(root / f"E14/{variant}/histories.npz") as data:
            moving, fixed = data["fine_moving"], data["fine_fixed"]
            t = moving[:, 0]
            start = moving[0, 1]
            left.plot(t, moving[:, 1] / start, color=BLUE, lw=2.1, label="Following ring")
            left.plot(t, fixed[:, 1] / start, color=GRAY, lw=2.0, ls="--", label="Fixed")
            if "fine_tracers" in data.files:
                tracked = data["fine_tracers"]
                left.plot(tracked[:, 0], tracked[:, 2], color=PURPLE, lw=1.7,
                          label="Initial energy that stayed inside")
            right.plot(t, moving[:, 2] / start, color=ORANGE, lw=2.1, label="Outward")
            right.plot(t, moving[:, 3] / start, color=GREEN, lw=2.1, label="Inward")
            if variant == "flow64":
                right.plot(t, -moving[:, 5] / start, color=BLUE, lw=1.8, ls="--", label="Net viscous inflow")
                right.plot(t, moving[:, 6] / start, color=PURPLE, lw=1.8, ls=":", label="Dissipated inside")
        axes_for_curves(left, f"{label} · stored", time_label, "Energy / initial energy")
        axes_for_curves(right, f"{label} · moving boundary", time_label, "Accumulated / initial energy")
        left.legend(fontsize=8.2)
        right.legend(fontsize=8.2)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def observations(root, out):
    fig, (left, right) = output(out, (1, 2), "Measured turbulence after vortex-ring collisions")
    with np.load(root / "E15/observables.npz") as data:
        t, metric, _, fixed, linear = data["spreading_full"].T
        left.axvspan(3.05, t[-1], color="#edf1f7", label="Held-out interval")
        left.plot(t, metric / 1000, color=BLUE, lw=2.1, label="Measured")
        left.plot(t, fixed / 1000, color=GRAY, lw=1.8, ls=":", label="Fixed-width fit")
        left.plot(t, linear / 1000, color=ORANGE, lw=1.8, ls="--", label="Linear-width fit")
        for key, label, color, style in (("blob", "Ring collisions", BLUE, "-"),
                                         ("dog", "Double grid", ORANGE, "--"),
                                         ("sog", "Single grid", GREEN, ":")):
            time, _, turbulent, _ = data[f"partition_{key}"].T
            right.plot(time, turbulent, c=color, ls=style, lw=1.7, label=label)
        right.set_xscale("log")
        right.set_xlim(.05, 1000)
    axes_for_curves(left, "Small turbulence blob · Fig. 5A", "Time after forcing (s)",
                    r"Plane second moment ($10^3$ mm$^2$)")
    axes_for_curves(right, "Three forcing geometries · Fig. 4B and Fig. S21", "Time after forcing (s)",
                    "Fluctuating energy / total")
    left.legend(fontsize=8.5)
    right.legend(loc="lower right", fontsize=8.5)
    fig.supxlabel("Reanalysis of Matsuzawa et al. (2026) · Zenodo 18380405 · CC BY 4.0", fontsize=9)
    fig.savefig(out, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    folder = args.root / "dynamics_figures"
    flux(args.root, folder / "material_flux.png")
    energy(args.root, folder / "moving_energy.png")
    observations(args.root, folder / "vortex_collision.png")
