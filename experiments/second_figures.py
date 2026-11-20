"""Plot the saved fields, interventions, and survey counts without rerunning the solvers."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / "research/results"
BLUE, GOLD, GREY = "#13647a", "#b25c21", "#a9b4ba"


def read(root, directory):
    return json.loads((root / directory / "summary.json").read_text())


def flow(root, out):
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.4), layout="constrained",
                             gridspec_kw={"height_ratios": [1, .7]})
    cases = [("E03/slice_48_128.npz", 96, "Imposed ring · 0.75 s"),
             ("E05/base/pair_slice_48.npz", 96, "Two imposed rings · 0.75 s"),
             ("E06/circle/slice_48_128.npz", 224, "Jet from rest · 1.75 s")]
    for ax, (path, step, name) in zip(axes[0], cases):
        with np.load(root / path) as data:
            field = data[f"vorticity_{step}"].T
        im = ax.imshow(field, extent=(-3, 3, 0, 6), origin="lower", cmap="magma", vmin=0, vmax=3.5)
        ax.set(title=name, xlabel="x (m)", ylabel="z (m)")
    fig.colorbar(im, ax=axes[0], label="Vorticity magnitude (1/s)", shrink=.75, extend="max")
    ax = axes[1,0]
    for r in read(root, "E03")["runs"]:
        if r["dt"] == 1/128:
            rows = r["rows"]
            ax.plot([q["time"] for q in rows], [q["core_z_r_rms"][0]-3 for q in rows],
                    marker="o", ms=3, label=f'{r["n"]}³')
    ax.set(xlabel="Time (s)", ylabel="Core displacement (m)", title="Imposed ring")
    ax.legend(frameon=False)
    for ax, r in zip(axes[1,1:], read(root, "E06/circle")["runs"][1:]):
        for y, (threshold, times) in enumerate(r["detected_times"].items()):
            ax.scatter(times, np.full(len(times), y), s=20, color=BLUE)
        ax.axvline(1, ls=":", color=GREY)
        ax.set(yticks=range(3), yticklabels=["0.25","0.35","0.50"], ylim=(-.6,2.6), xlim=(0,1.8),
               xlabel="Time (s), pulse ends at 1", ylabel="Threshold / peak",
               title=f'Jet ring detections · {r["n"]}³')
    fig.savefig(out / "flow.png", dpi=170)
    plt.close(fig)


def necks(root, out):
    profiles = read(root,"E03/observers")["profiles"]
    fig, axes = plt.subplots(1, 3, figsize=(8.1, 4.1), layout="constrained", sharex=True, sharey=True)
    for ax, (key, label, color) in zip(axes, [("ring_48_96","Viscous ring · 0.75 s",BLUE),
                                               ("potential","Irrotational flow",GOLD),
                                               ("uniform","Uniform flow","#646c72")]):
        r = np.array(profiles[key]["radius_m"])
        z = profiles[key]["offset_m"]
        ax.fill_betweenx(z, -r, r, color=color, alpha=.16)
        ax.plot(r, z, color=color)
        ax.plot(-r, z, color=color)
        ax.axvline(0, lw=.6, ls=":", color=GREY)
        ax.set(title=label, xlabel="Transverse position (m)", xlim=(-.24,.24), ylim=(-.75,.75),
               xticks=[-.2,0,.2], yticks=[-.75,-.5,-.25,0,.25,.5,.75])
    axes[0].set_ylabel("Axial offset from centre (m)")
    fig.suptitle("Radius enclosing the same upward flux (0.10 m³/s)", weight="bold")
    fig.savefig(out/"flux_sections.png", dpi=170)
    plt.close(fig)


def comparisons(root, out):
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.2), layout="constrained")
    ax = axes[0,0]
    rows = read(root,"E04")["rows"]
    designs = ["tree","one_loop","uniform","adaptive_0.1","material_optimum"]
    x = np.arange(len(designs))
    for shift, changing, color, label in [(-.18,False,BLUE,"Fixed"), (.18,True,GOLD,"Alternating")]:
        vals = [[r["cut_max_unmet"] for r in rows if r["commodity"]=="water" and
                 r["design"]==name and r["varying_sinks"]==changing and r["threshold"]==.001]
                for name in designs]
        # Deterministic seeds are shown individually. They do not define a population error bar.
        for i, group in enumerate(vals):
            ax.scatter(np.full(len(group), i+shift), group, color=color, marker="o" if changing else "s",
                       label=label if i==0 else None, s=22, alpha=.8)
    ax.set(xticks=x, xticklabels=["Tree","+1 loop","Grid","Adaptive","Local opt."],
           ylabel="Largest unmet fraction after 1 cut", ylim=(-.04,1.04), title="A   Water network · three initial seeds")
    ax.legend(frameon=False, ncol=2)
    ax = axes[0,1]
    rows = [r for r in read(root,"E05/phases")["runs"] if r["seed"]==11 and r["hz"]==128]
    x = np.arange(len(rows))
    for offset, key, label, color in [(-.18,"B_from_A_at_21","A → B",BLUE),(.18,"A_from_B_at_21","B → A",GOLD)]:
        ax.bar(x+offset, [r[key][0] for r in rows], .34, label=label, color=color)
    ax.set(xticks=x, xticklabels=["Off","A → B","Both","Clock"], ylabel="Partner response after 1 s (rad)",
           title="B   Phase perturbation · first component")
    ax.legend(frameon=False)
    ax = axes[1,0]
    with np.load(root/"E07/predictions.npz") as pr, np.load(root/"E07/reference.npz") as ref:
        t = pr["time_s"]
        for data, style, label, color in [(ref["native_1000"],"-","Native · 1 kPa",BLUE),
                                           (ref["native_50000"],":","Native · 50 kPa",BLUE),
                                           (pr["M1"],"--","M1 · actual edges",GOLD),
                                           (pr["M2"],"-.","M2 · periodic edges","#563b78")]:
            ax.plot(t, data[:,0,3], style, lw=1.8, label=label, color=color)
    ax.set(xlim=(0,3), xlabel="Time after pulse (s)", ylabel="Source pressure / initial pressure",
           title="C   Hydraulic holdout · calculated pressures")
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1,1]
    d = read(root,"E08")["domains"]
    fields = ["fluid","plant","phase","space"]
    left = np.zeros(len(fields))
    for key, label, color in [("positive","Present",BLUE),("negative","Other form",GOLD),
                              ("unknown","Unresolved","#bdc7cb"),("excluded","Excluded","#e8ecee")]:
        vals = np.array([d[f][key] for f in fields])
        ax.barh(fields, vals, left=left, color=color, label=label)
        left += vals
    ax.invert_yaxis()
    ax.set(xticks=range(6), xlabel="Articles in frozen top five", title="D   Documented forms by target")
    ax.legend(frameon=False, ncol=2, fontsize=8, loc="upper center", bbox_to_anchor=(.5,-.24))
    fig.savefig(out/"comparisons.png", dpi=170)
    plt.close(fig)


def run(root, out):
    out.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                         "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold"})
    flow(root, out)
    comparisons(root, out)
    necks(root, out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    run(args.root, args.out or args.root / "figures")
