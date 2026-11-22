"""Draw scientific figures from the saved E77/E78 outputs; no refitting."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, GRAY, GREEN = "#2369A3", "#CF671C", "#737B83", "#37866B"
NAMES = ("fixed_clock", "fixed_distance", "two_waiting_times", "power_law")
LABELS = ("Fixed clock", "Fixed cell interval", "Two waits", "Power law")
COLORS = (GRAY, GREEN, BLUE, ORANGE)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(fig, directory, name):
    fig.savefig(directory / f"{name}.svg", metadata={"Date": None})
    fig.savefig(directory / f"{name}.png", dpi=160,
                metadata={"Software": "TORUS-mania E77-E78 scientific plots"})
    plt.close(fig)


def growth_figure(results, out):
    result = read(results / "E77/summary.json")
    training = read(ROOT / "research/results/E29/sealed_predictions.json")["training"]
    held = read(ROOT / "research/results/E29/summary.json")["holdout"]
    with (results / "E77/tau_profile.csv").open(encoding="utf-8") as stream:
        profile = list(csv.DictReader(stream))

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.3), layout="constrained")
    ax = axes[0, 0]
    for data, label, color, marker in (
        (training, "Fit: lower production", GRAY, "o"),
        (held, "Historical holdout", "#BBC8D1", "^"),
    ):
        p, f = np.asarray(data["frequency"]["xy"]).T
        ax.scatter(p, f, s=16, marker=marker, color=color, alpha=.8, label=label)
    p = np.linspace(.95, 3.25, 250)
    m = result["models"]["two_waiting_times"]
    ax.plot(p, 1 / (m["tau_h"] + m["length_cells"] / p), color=BLUE,
            linewidth=2.2, label="Two waits")
    m = result["models"]["power_law"]
    ax.plot(p, m["A"] * p**m["b"], color=ORANGE, linestyle="--", linewidth=2.2,
            label="Power law (same parameter count)")
    ax.axvspan(1.97, 2.03, color="black", alpha=.06)
    ax.set(title="A  Similar predictions from two different formulas",
           xlabel="Cell production (cells / h)", ylabel="DR5 peak frequency (1 / h)",
           xlim=(.95, 3.25), ylim=(.15, .95))
    ax.legend(fontsize=8, frameon=False, loc="upper left")

    ax = axes[0, 1]
    for i, (name, label, color) in enumerate(zip(NAMES, LABELS, COLORS)):
        values = [result["E29_historical_holdout"][name][metric]["log_RMSE"]
                  for metric in ("frequency", "spacing")]
        locations = np.arange(2) + (i - 1.5) * .18
        ax.bar(locations, values, width=.17, color=color, label=label)
        for x, value in zip(locations, values):
            ax.text(x, value + .009, f"{value:.3f}", ha="center", fontsize=8)
    ax.set(title="B  Error on the original held-out region",
           xticks=(0, 1), xticklabels=("Frequency (50 markers)", "Spacing (48 markers)"),
           ylabel="Log RMSE (lower is better)", ylim=(0, .60))
    ax.legend(ncol=2, fontsize=8, frameon=False, loc="upper left")

    ax = axes[1, 0]
    tau = np.array([float(r["tau_h"]) for r in profile])
    sse = np.array([float(r["training_frequency_log_SSE"]) for r in profile])
    relative = sse / sse.min() - 1
    ax.plot(tau, 100 * relative, color=BLUE, linewidth=2)
    for tolerance, color in ((10, "#D9E5ED"), (5, "#AFCADF"), (1, "#78A5C5")):
        allowed = relative <= tolerance / 100 + 1e-12
        ax.axvspan(tau[allowed].min(), tau[allowed].max(), color=color, alpha=.65)
        ax.axhline(tolerance, color=GRAY, linewidth=.7, linestyle=":")
    ax.plot(tau, 100 * relative, color=BLUE, linewidth=2)
    ax.text(2.45, 2.1, "1%: 0.65-1.48 h\n5%: 0.12-1.99 h\n10%: 0-2.32 h\nSensitivity sets, not CIs",
            fontsize=8, va="bottom")
    ax.set(title="C  The fitted delay is not tightly constrained",
           xlabel="Fixed delay tau (h); growth coefficient refitted",
           ylabel="Training log SSE above minimum (%)", xlim=(0, 4), ylim=(0, 30))

    ax = axes[1, 1]
    conditions = [r for r in result["E34_mature_cell_length_sensitivity"]["conditions"]
                  if r["family"] == "common_change"]
    q = [r["mature_cell_length_ratio_to_WT"]["eto2"] for r in conditions]
    for name, label, color in zip(NAMES, LABELS, COLORS):
        ax.plot(q, [r["scores"][name]["log_RMSE"] for r in conditions], "o-",
                color=color, markersize=4, label=label)
    ax.axvline(1, color=GRAY, linestyle=":", linewidth=1)
    ax.set(title="D  Transfer ranking depends on unmeasured cell length",
           xlabel="Mature cell length / WT (same q for four targets)",
           ylabel="E34 period log RMSE (4 genotype medians)",
           xticks=q, ylim=(0, .63))
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper center")
    for ax in axes.flat:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.14)
    fig.suptitle("E77 | Predictive agreement does not uniquely identify a reflux clock", fontsize=14)
    save(fig, out, "growth_law_specificity")


def circulation_figure(results, out):
    result = read(results / "E78/summary.json")
    with np.load(results / "E78/histories.npz", allow_pickle=False) as history:
        time = history["time_model_units"]
        steady = np.array(result["A_linear_circulation_and_stability"]["baseline_steady_amounts_I_T_O"])
        deviation = history["A/steady_plus_tip_pulse/amounts_expm"] - steady

    fig, axes = plt.subplots(1, 3, figsize=(12.1, 4.6), layout="constrained")
    ax = axes[0]
    for i, (label, color) in enumerate(zip(("Inner", "Tip", "Outer"), (BLUE, ORANGE, GREEN))):
        ax.plot(time, deviation[:, i], color=color, label=label, linewidth=1.8)
    ax.set(title="A  A circulating system can settle",
           xlabel="Model time", ylabel="Amount above steady state",
           xlim=(0, 24), ylim=(-.02, 1.06))
    ax.legend(frameon=False, fontsize=9)
    ax.text(.96, .73, "Constant supply + positive loss\n81 / 81 settings stable\nAnalytic stability bound verified",
            transform=ax.transAxes, ha="right", va="top", fontsize=8)

    ax = axes[1]
    rows = result["B_fixed_collective_flux_and_molecular_returns"]["conditions"]
    probs = [100 * r["first_complete_return_probability"] for r in rows]
    ax.bar(range(3), probs, color=(BLUE, GREEN, ORANGE), width=.6)
    for i, p in enumerate(probs):
        ax.text(i, p + 2.5, f"{p:.2f}%", ha="center", fontsize=10)
    ax.set(title="B  Same collective flux, different return",
           ylabel="Probability of a first complete molecular lap (%)",
           xticks=range(3),
           xticklabels=[f"d = {r['common_loss_rate']:g}\nSupply = {r['total_external_supply']:.3g}" for r in rows],
           xlabel="Loss rate and total external supply (model units)", ylim=(0, 110))
    ax.text(.98, .78, "Every edge flux = 1\nSame compartment amounts\nSupply is changed", transform=ax.transAxes,
            ha="right", va="top", fontsize=8)

    ax = axes[2]
    rows = result["C_transport_sensitivity_of_imposed_gate"]["conditions"]
    ax.plot([r["transport_multiplier"] for r in rows],
            [r["period_relative_to_multiplier_one"] for r in rows], "o-", color=BLUE, linewidth=1.8)
    ax.axhline(1, color=GRAY, linewidth=1, linestyle=":")
    ax.set(title="C  An imposed return gate changes the period",
           xlabel="Transfer-rate multiplier (both stages)",
           ylabel="Imposed period / baseline period", xticks=(.5, 1, 1.5, 2), ylim=(.7, 1.75))
    ax.text(.98, .96, "E28 gate: 20% arrival, then growth\nGrowth and loss rates fixed\nNot a growing-root model",
            transform=ax.transAxes, ha="right", va="top", fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.14)
    fig.suptitle("E78 | Collective circulation, molecular return, and a clock are separate observables", fontsize=13)
    save(fig, out, "circulation_vs_clock")


def plot(results):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.titlesize": 10, "svg.fonttype": "none",
                         "svg.hashsalt": "torus-mania-reflux-clock-20261122"})
    out = results / "reflux_clock_figures"
    out.mkdir(parents=True, exist_ok=True)
    growth_figure(results, out)
    circulation_figure(results, out)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results")
    plot(parser.parse_args().out)
