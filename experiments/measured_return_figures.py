"""Plot the derived root-tracer and early-formation comparisons."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, GREEN, GREY = "#235a8b", "#ae5019", "#277664", "#647180"


def style(axis):
    axis.spines[["right", "top"]].set_visible(False)
    axis.grid(axis="y", color="#e1e7eb", linewidth=.7)
    axis.set_axisbelow(True)


def root_figure(e44, e45, directory):
    fig, (ax, chem, stable) = plt.subplots(1, 3, figsize=(13, 4.2), layout="constrained")
    for a in (ax, chem, stable):
        style(a)
    wire = e44["wire_fig8"]
    for key, label, color in (("tipward","Toward root tip",BLUE), ("shootward","Toward shoot",ORANGE)):
        values = wire["nonzero_time_ratios"][key]["wire_over_control"]
        ax.plot(wire["times_h"][1:], np.array(values)*100, "o-", color=color, label=label, lw=2)
    ax.axhline(100, color=GREY, ls=":", lw=1)
    ax.set(xlabel="Time after application (h)", ylabel="Receiver label with wire / control (%)",
           title="Broad bean root segments", xticks=[1,2,3,5], ylim=(0,170))
    ax.legend(frameon=False, loc="best")
    shares = np.array(e45["IBA_input_fig5C"]["IAA_percent_of_HPLC_IAA_plus_IBA"]["values"])
    chem.bar([0,1], shares, color=GREEN, width=.5, label="IAA")
    chem.bar([0,1], 100-shares, bottom=shares, color="#d8e2ea", width=.5, label="IBA")
    for x,v in enumerate(shares):
        chem.text(x,v/2,f"{v:.0f}%", color="white", ha="center", va="center", fontweight="bold")
    chem.set(xticks=[0,1], xticklabels=["0.4–2.4","2.4–4.4"], xlabel="Distance from root tip (mm)",
             ylabel="Share of two measured compounds (%)", ylim=(0,115), title="Label recovered after IBA input")
    chem.legend(frameon=False, loc="upper center", ncol=2)
    percent = e45["direct_stable_IAA_hypocotyl_fig3"]["percent_of_recovered_free_13C6_IAA"]
    stable.bar([0,1,2], percent["values"], color=[BLUE,GREY,GREY], width=.6)
    for i,value in enumerate(percent["values"]):
        stable.text(i,value+1,f"{value:.1f}%",ha="center")
    stable.set(xticks=[0,1,2], xticklabels=["Control","NPA","Reversed"], xlabel="Hypocotyl treatment",
               ylabel="Labelled free IAA in lower half + receiver (%)", ylim=(0,36), title="Direct ¹³C₆-IAA transport")
    fig.savefig(directory/"root_tracer.png", dpi=150)
    plt.close(fig)


def formation_figure(e46, e47, e48, directory):
    fig, axes = plt.subplots(2, 2, figsize=(12.5,8.3), layout="constrained")
    field, section, location, prediction = axes.ravel()
    for a in axes.ravel():
        style(a)
    cells = e46["scores"]["primary"]["cells"]
    for i,(cell,values) in enumerate(cells.items()):
        field.scatter(i,values["rmse_over_zero"], s=42, color=BLUE if cell.startswith("Ce") else ORANGE)
    field.axhline(1, color=GREY, ls=":", lw=1.4)
    field.set(xticks=[2.5,9], xticklabels=["C. elegans embryos (6)","Mouse oocytes (7)"],
              ylabel="Interior flow RMSE / zero-velocity RMSE", title="Interior velocity predicted from outer measurements")
    angles = 15 + 30*np.arange(12)
    medians = np.array(e48["cases"]["primary"]["sector_medians_core_shell_nm_per_s"])
    for col,label,color in ((0,"Center",ORANGE), (1,"Outer annulus",BLUE)):
        section.plot(angles, medians[:,col], "o-", ms=4, color=color, label=label)
    section.axhline(0,color=GREY,lw=.9)
    section.set(xticks=[0,90,180,270,360], xlabel="Angle in the transverse plane (degrees)",
                ylabel="Axial velocity (nm/s, + posterior)", ylim=(-110,115), title="One section from volumetric imaging")
    section.legend(frameon=False, ncol=2, loc="center", bbox_to_anchor=(.5,.68))
    for panel,label,color in (("Fig6C","Cdc42 intervention",BLUE), ("Fig6D","Arp2/3 inhibition",ORANGE)):
        g = e47["position_at_90_min"][panel]["groups"].values()
        location.plot([0,1,2],[v["mean_um"] for v in g],"o-",color=color,lw=2,label=label)
    location.set(xticks=[0,1,2],xticklabels=["Control","Single","With ROCK inhibition"],
                 ylabel="DNA midpoint distance from cell center (µm)", ylim=(0,35), title="Mean position at 90 min in two intervention series")
    location.legend(frameon=False,loc="lower left")
    window = e47["windows"]["availability_selected"]
    names = ["group_mean","early_flow","early_motion","both"]
    for offset,(label,group),color in zip([-.18,.18],window["groups"].items(),[BLUE,ORANGE]):
        prediction.bar(np.arange(4)+offset, [group["leave_one_oocyte_out"][m]["rmse_um_per_min"] for m in names],
                       width=.35, color=color, label=f"{label} (n={group['eligible_n']})")
    prediction.set(xticks=np.arange(4),xticklabels=["Group mean","Early flow","Early motion","Both"],
                   ylabel="Held-out error (µm/min)", ylim=(0,.225), title="Later spindle motion at 54–74 min")
    prediction.legend(frameon=False,loc="upper left",ncol=2)
    fig.savefig(directory/"flow_and_position.png", dpi=150)
    plt.close(fig)


def run(root):
    out = root / "measured_return_figures"
    out.mkdir(parents=True, exist_ok=True)
    results = [json.loads((root / f"E{n}" / "summary.json").read_text()) for n in range(44,49)]
    root_figure(*results[:2], out)
    formation_figure(*results[2:], out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root)
