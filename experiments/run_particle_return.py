"""Reproduce the root chemistry and embryo tracking measurements E55–E60."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from experiments.particle_return_sources import RAW

EXPERIMENTS = (
    "E55_root_iaa_fate",
    "E56_root_local_supply",
    "E57_auxsen_clearance",
    "E58_granule_paths",
    "E59_spindle_mechanisms",
    "E60_iaa_reactivation",
)


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    jobs = [(name + ".run", ["--raw", str(raw), "--out", str(out / name[:3])]) for name in EXPERIMENTS]
    jobs.append(("particle_return_figures", ["--root", str(out)]))
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
