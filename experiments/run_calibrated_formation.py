"""Run E72–E76 and plot the registered analyses."""

import argparse
import json
from pathlib import Path
from time import monotonic

from experiments.calibrated_formation_sources import RAW


def run(raw, out, log):
    import matplotlib

    matplotlib.use("Agg")
    from experiments.calibrated_formation_figures import plot
    from experiments.E72_neural_fold_work.run import run as neural_fold_work
    from experiments.E73_epiboly_power_location.run import run as epiboly_power_location
    from experiments.E74_transverse_root_iaa.run import run as transverse_root_iaa
    from experiments.E75_axial_root_cap.run import run as axial_root_cap
    from experiments.E76_energy_closure.run import run as energy_closure

    jobs = (
        ("E72", neural_fold_work, (raw, out / "E72")),
        ("E73", epiboly_power_location, (raw, out / "E73")),
        ("E74", transverse_root_iaa, (raw, out / "E74")),
        ("E75", axial_root_cap, (raw, out / "E75")),
        ("E76", energy_closure, (out / "E76",)),
        ("figures", plot, (out,)),
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
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
