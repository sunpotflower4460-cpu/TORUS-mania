"""Replay the chemical, spatial and temporal comparisons in E44–E48."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from experiments.measured_return_sources import RAW

EXPERIMENTS = ("E44_vicia_routes", "E45_auxin_recovered_identity", "E46_cytoplasmic_return",
               "E47_spindle_forecast", "E48_transverse_streaming")


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    commands = [(name+".run", ["--raw", str(raw), "--out", str(out/name[:3])]) for name in EXPERIMENTS]
    commands.append(("measured_return_figures", ["--root", str(out)]))
    steps = []
    start = time.monotonic()
    for name, arguments in commands:
        tick = time.monotonic()
        sub = subprocess.run([sys.executable, "-m", "experiments."+name, *arguments], env=env)
        steps.append({"module": name, "returncode": sub.returncode, "wall_s": round(time.monotonic()-tick,3)})
        if sub.returncode:
            break
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(json.dumps({"runs": steps, "wall_s": round(time.monotonic()-start,3)}, indent=2)+"\n")
    if steps[-1]["returncode"]:
        raise SystemExit(steps[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
