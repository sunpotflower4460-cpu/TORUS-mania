"""Render the root and energy comparisons from their saved values."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BLUE, GREEN, ORANGE, PURPLE = "#216390", "#187458", "#bd5718", "#72508f"
DARK, GRAY = "#1d2938", "#6d7783"


def load(root, experiment):
    return json.loads((root / experiment / "summary.json").read_text(encoding="utf-8"))


def axes(axis, title, x="", y=""):
    axis.set(title=title, xlabel=x, ylabel=y)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#dce2e8", lw=.7)


def transport(root, out):
    assay = load(root, "E33")["fig5c_relative_response"]
    trial = load(root, "E34")
    groups = ("epidermis_to_stele_differentiation_zone", "stele_to_outer_elongation_zone")
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.8, 4.5), layout="constrained")
    at = np.arange(len(groups))
    for off, treatment, color, label in ((-.15, "NPA+E2", ORANGE, "NPA"), (.15, "NOA+E2", BLUE, "1-NOA")):
        values = [100 * assay[k]["conditions"][treatment]["fraction_of_E2_mean"] for k in groups]
        bars = left.bar(at + off, values, .27, color=color, label=label)
        left.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    left.set_xticks(at, ["Outer layer → stele", "Stele → outer layer"])
    left.set_ylim(0, 109)
    left.axhline(100, color=GRAY, ls="--", lw=1)
    axes(left, "Local induction and transport inhibition", y="DR5 response (% of induction alone)")
    left.legend(loc="upper right", fontsize=9)

    observations = trial["genotype_observations"]
    wt = observations["WT"]
    v0, period0 = wt["growth_um_per_h"], wt["peak_period_h"]
    v = np.linspace(50, 235, 220)
    delay = trial["held_out_treatments"]["tau_h_from_E29"]
    right.plot(v, np.full(len(v), period0), color=GRAY, ls=":", label="Fixed period")
    right.plot(v, period0 * v0 / v, color=ORANGE, ls="--", label="Fixed distance")
    right.plot(v, delay + (period0-delay)*v0/v, color=BLUE, lw=2, label="Two waiting times")
    for name, group in observations.items():
        point = group["growth_um_per_h"], group["peak_period_h"]
        right.scatter(*point, color=DARK, marker="s" if name == "WT" else "o", zorder=4)
        right.annotate(name, point, xytext=(4, 6 if name != "line1" else -13),
                       textcoords="offset points", fontsize=8.5)
    right.set(xlim=(44, 242), ylim=(1.9, 12.5))
    axes(right, "Period forecasts for four test lines", "Primary root tip speed (μm/h)", "Period between DR5 peaks (h)")
    right.legend(loc="upper right", fontsize=8.8)
    fig.supxlabel("Public figure data · Hu et al. (2021) and De Gernier et al. (2025)", fontsize=9)
    fig.savefig(out / "root_transport_and_period.png", dpi=150)
    plt.close(fig)


def development(root, out):
    trial = load(root, "E35")
    survey = load(root, "E38")
    graft = trial["grafted_median_branch_number"]
    fig, (first, second, third) = plt.subplots(1, 3, figsize=(14.2, 4.6), layout="constrained")
    groups = ("shoot_WT_root_WT", "shoot_mutant_root_WT", "shoot_WT_root_mutant", "shoot_mutant_root_mutant")
    bars = first.bar(range(4), [graft[k] for k in groups], color=[GREEN, GRAY, GREEN, GRAY], width=.62)
    first.bar_label(bars, fmt="%.1f", fontsize=9, padding=3)
    first.set_xticks(range(4), ["WT/WT", "mut/WT", "WT/mut", "mut/mut"])
    first.set_ylim(0, 67)
    axes(first, "Shoot genotype and branching", "Graft (shoot/root)", "Total branch number (median)")

    endpoints = trial["fig6C_to_6F"]
    for field, color, label in (
        ("regular_light_primary_root_cm", BLUE, "Primary root length"),
        ("regular_light_lateral_root_density_per_cm", ORANGE, "Lateral-root density"),
    ):
        assay = endpoints[field]
        relative = 100*np.array(assay["cyp38_5"]) / assay["WT"]
        second.plot(assay["sucrose_percent"], relative, marker="o", lw=2, color=color, label=label)
    second.set_xticks([1, 2, 3])
    second.set_ylim(-5, 106)
    second.legend(loc="upper left", fontsize=8)
    axes(second, "Sucrose and two root outcomes", "Sucrose (%)", "Mutant median (% of WT at same dose)")

    for j, (name, color, label) in enumerate((
        ("transcriptional", BLUE, "Expression reporter"), ("integrase", PURPLE, "Integrase recorder"),
    )):
        rows = [
            survey["stages"][stage]["all_labelled_organs"]["reporters"][name]["bootstrap"]["mean"]
            for stage in ("1", "2")
        ]
        y = np.array([row["treated_minus_control"] for row in rows])
        limits = np.array([row["cluster_percentile_interval_95"] for row in rows]).T
        third.errorbar(np.arange(2) + (-.1 if j == 0 else .1), y, yerr=[y-limits[0], limits[1]-y],
                       fmt="o", color=color, capsize=4, label=label)
    third.axhline(0, color=GRAY, ls="--", lw=1)
    third.set(xticks=[0, 1], xticklabels=["Stage I", "Stage II"], xlim=(-.45, 1.45), ylim=(-.55, 2.25))
    third.legend(loc="upper left", fontsize=8)
    axes(third, "The reporter changes the estimate", "Primordium stage", "Auxinole effect (cells per primordium)")
    fig.supxlabel("Duan et al. (2021) and Maranas et al. (2026) · intervals resample seedlings within batches", fontsize=9)
    fig.savefig(out / "root_growth_and_branching.png", dpi=150)
    plt.close(fig)


def energy(root, out):
    vortex = load(root, "E36")
    release = load(root, "E37")["undriven_release"][-1]
    fig, (first, second, third) = plt.subplots(1, 3, figsize=(14.0, 4.5), layout="constrained")
    for axis in (first, second):
        axis.axhspan(.28, .38, color="#e4e9ef", label="0.33 ± 0.05")
        axis.axhline(.33, color=GRAY, ls="--", lw=1)
        axis.set_ylim(.17, .49)
    rows = vortex["orifice_piston"]["all_stroke_ratios"]
    x = [row["stroke_ratio"] for row in rows]
    first.plot(x, [row["alpha_read_fov2"] for row in rows], "o-", color=BLUE, label="Published ratio")
    first.plot(x, [row["alpha_from_three_separate_figures"] for row in rows], "D:", color=ORANGE,
               lw=1.6, ms=4, label="Ratio from three panels")
    first.legend(loc="upper right", fontsize=8.5)
    axes(first, "Orifice-generated vortex ring", "Maximum stroke ratio", "Dimensionless kinetic energy")

    curves = vortex["unsteady_biomimetic_generator"]
    for k, color, label in (
        ("advected_boundary", PURPLE, "Flow-tracked boundary"), ("core_rectangle", GREEN, "Core rectangle"),
    ):
        row = curves[k]
        second.plot(row["stroke_ratios"], row["estimated_alpha"], "o-", color=color, label=label)
    second.legend(loc="upper right", fontsize=8.5)
    axes(second, "Unsteady vortex generator", "Elapsed stroke ratio", "Dimensionless kinetic energy")

    trace = release["trace"]
    floor = release["remaining_energy"]
    decaying = 100 * (np.array(trace["stored_energy"])-floor) / (release["initial_energy"]-floor)
    third.plot(trace["time_s"], decaying, "o-", color=GREEN, lw=2, ms=4)
    third.set(xlim=(-.1, 5.), ylim=(-3, 105))
    axes(third, "Passive network after drive is removed", "Time in model (s)", "Stored energy above equilibrium (%)")
    fig.supxlabel("Limbourg & Nedić (2021), Baskaran & Mulleners (2022), and a linear transport-network model", fontsize=9)
    fig.savefig(out / "vortex_energy_and_driven_cycles.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    out = args.root / "return_energy_figures"
    out.mkdir(parents=True, exist_ok=True)
    for build in (transport, development, energy):
        build(args.root, out)
