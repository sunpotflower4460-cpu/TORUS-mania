"""Compare the tissue interventions and the pH-pulse trajectories."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BLUE = "#266a9a"
ORANGE = "#bf6129"
GREEN = "#247b62"
GRAY = "#6f747b"


def read(root, experiment, name="summary"):
    return json.loads((root / experiment / f"{name}.json").read_text(encoding="utf-8"))


def style(axis, title, unit):
    axis.set(title=title, ylabel=unit)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#dce2e9", lw=.8)


def tissue(root, out):
    rescue = read(root, "E24")["figure_3_endodermal_PIN3_rescue"]
    planes = read(root, "E25")["figure_6E_divisions_15h_after_ablation"]["group_means_from_bars"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.1, 4.5), layout="constrained")
    fig.suptitle("The adjacent endodermis changes the progression of lateral-root development", fontsize=14)
    x = np.arange(3)
    panels = [rescue[name] for name in ("B_founder_density", "C_initiation_density", "D_combined_density")]
    for offset, key, label, color in ((-.17, "transgene_negative", "No added PIN3", GRAY),
                                       (.17, "transgene_positive", "Endodermal PIN3", GREEN)):
        values = [p["group_means_from_bars"][key] for p in panels]
        left.bar(x + offset, values, width=.30, label=label, color=color,
                 yerr=[p["readout_halfwidth_per_bar"] for p in panels], capsize=3)
    left.set_xticks(x, ["Founder sites", "Initiation sites", "Combined"])
    left.set_ylim(0, 12.8)
    style(left, "PIN3 complementation in a pin3 background", "Sites per cm of primary root")
    left.legend(loc="upper left", fontsize=9)

    x = np.arange(len(planes))
    anti = [row["anticlinal"] for row in planes.values()]
    peri = [row["periclinal"] for row in planes.values()]
    right.bar(x, anti, color=BLUE, width=.62, label="Anticlinal")
    right.bar(x, peri, bottom=anti, color=ORANGE, width=.62, label="Periclinal")
    right.set_xticks(x, ["Control", "Control\n+ NAA", "ktn1", "ktn1\n+ NAA"])
    right.set_ylim(0, 4.5)
    style(right, "Division after removal of one endodermal cell", "Mean divisions per ablation in 15 h")
    right.legend(loc="upper right", fontsize=9)
    fig.supxlabel("Marhavý et al. (2013), Fig. 3 and (2016), Fig. 6E · error bars show digitization range", fontsize=9)
    fig.savefig(out / "root_tissue_interventions.png", dpi=150)
    plt.close(fig)


def proton_pulses(root, out):
    record = read(root, "E26")
    traces = read(root, "E26", "traces")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.45), sharey=True, layout="constrained")
    fig.suptitle("Root elongation responds to the pH of the surrounding medium", fontsize=14)
    for axis, panel, trace_key, color in (
        (axes[0], "fig1e_alkaline_pulse", "alkaline", BLUE),
        (axes[1], "fig1g_acidic_pulse", "acidic", ORANGE),
    ):
        case, series = record[panel], traces[trace_key]
        times, means, sd = (np.array(series[key], dtype=float) for key in ("time_min", "mean", "sample_sd"))
        ph = case["medium"]["pulse_pH"]
        axis.axvspan(case["onset_min"], case["washout_start_min"], color=color, alpha=.12, label=f"pH {ph:.2f} pulse")
        axis.fill_between(times, means-sd, means+sd, color=color, alpha=.2, lw=0)
        axis.plot(times, means, color=color, lw=2, label="Mean ± SD")
        axis.set(xlabel="Time (min)", ylim=(0, 12))
        style(axis, f"pH 5.80 → {ph:.2f} → 5.80", "Root elongation (µm/min)" if axis == axes[0] else "")
        axis.legend(loc="upper right", fontsize=9)
    fig.supxlabel("Li et al. (2021), public source arrays for Fig. 1e and 1g · 7–8 roots per time point", fontsize=9)
    fig.savefig(out / "proton_pulses.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    out = args.root / "local_reflux_figures"
    out.mkdir(parents=True, exist_ok=True)
    tissue(args.root, out)
    proton_pulses(args.root, out)
