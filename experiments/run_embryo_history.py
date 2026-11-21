"""Run the chick, zebrafish and IAA history analyses E61–E66."""

import argparse
import json
from pathlib import Path
from time import monotonic

from experiments.embryo_history_sources import RAW


def run(raw, out, log):
    import matplotlib

    matplotlib.use("Agg")
    from experiments import embryo_history_figures as figures
    from experiments.E61_vortices_and_axis.run import run as chick_vortices
    from experiments.E62_cell_returns.run import run as cell_returns
    from experiments.E63_tension_and_axis.run import run as chick_tension
    from experiments.E64_joint_iaa_history.run import run as iaa_history
    from experiments.E65_crosscheck_returns.run import run as crosscheck_returns
    from experiments.E66_image_only_track.run import run as image_track

    jobs = (
        ("E61", chick_vortices, (raw, out / "E61")),
        ("E62", cell_returns, (raw, out / "E62")),
        ("E63", chick_tension, (raw, out / "E63")),
        ("E64", iaa_history, (out / "E64",)),
        ("E65", crosscheck_returns, (raw, out / "E65", out / "E62")),
        ("E66", image_track, (raw, out / "E66", out / "E62", out / "E65")),
        ("figures", figures.plot, (out,)),
    )
    steps = []
    try:
        for name, job, arguments in jobs:
            start = monotonic()
            record = {"experiment": name, "completed": False}
            steps.append(record)
            try:
                job(*arguments)
                record["completed"] = True
            finally:
                record["wall_s"] = round(monotonic() - start, 3)
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
