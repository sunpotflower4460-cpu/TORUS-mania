"""Run the registered analyses E67–E71 from the repository root."""

import argparse
import json
from pathlib import Path
from time import monotonic

from experiments.iaa_embryo_sources import RAW, ROOT


def run(raw, previous, out, log):
    import matplotlib

    matplotlib.use("Agg")
    from experiments import iaa_embryo_figures as figures
    from experiments.E67_half_resolution.run import run as high_resolution
    from experiments.E68_root_label_loss.run import run as root_label_loss
    from experiments.E69_myosin_axis.run import run as myosin_axis
    from experiments.E70_material_torus_energy.run import run as energy_balance
    from experiments.E71_iaa_uptake.run import run as iaa_uptake

    jobs = (
        ("E67", high_resolution, (raw / "level1", out / "E67", previous)),
        ("E68", root_label_loss, (raw, out / "E68")),
        ("E69", myosin_axis, (raw, out / "E69")),
        ("E70", energy_balance, (out / "E70",)),
        ("E71", iaa_uptake, (raw, out / "E71")),
        ("figures", figures.plot, (out,)),
    )
    steps = []
    try:
        for name, job, arguments in jobs:
            start = monotonic()
            step = {"experiment": name, "completed": False}
            steps.append(step)
            try:
                job(*arguments)
                step["completed"] = True
            finally:
                step["wall_s"] = round(monotonic() - start, 3)
    finally:
        if log:
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(
                json.dumps({"runs": steps}, indent=2) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--previous", type=Path, default=ROOT / "research/results")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.previous, args.out, args.log)
