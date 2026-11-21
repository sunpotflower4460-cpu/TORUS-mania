"""Reproduce the root tracer, flow-turn and embryo polarity measurements E49–E54."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from experiments.turning_path_sources import RAW

EXPERIMENTS = (
    "E49_root_pulse",
    "E50_directional_root_transport",
    "E51_turning_flow",
    "E52_division_rotation",
    "E53_polarity_prediction",
    "E54_daughter_polarity",
)


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    jobs = [(name + ".run", ["--raw", str(raw), "--out", str(out / name[:3])]) for name in EXPERIMENTS]
    jobs.append(("turning_path_figures", ["--root", str(out)]))
    steps = []
    started = time.monotonic()
    for module, arguments in jobs:
        tick = time.monotonic()
        process = subprocess.run(
            [sys.executable, "-m", "experiments." + module, *arguments], env=env, check=False
        )
        steps.append(
            {
                "module": module,
                "returncode": process.returncode,
                "wall_s": round(time.monotonic() - tick, 3),
            }
        )
        if process.returncode:
            break
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            json.dumps({"runs": steps, "wall_s": round(time.monotonic() - started, 3)}, indent=2) + "\n"
        )
    if steps[-1]["returncode"]:
        raise SystemExit(steps[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
