"""Replay E30–E32 against the versioned public figures."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    commands = (
        ("E30_vesicle_transport.run", ["--figure", str(raw/"wachsman_f3.jpg"), "--out", str(out/"E30")]),
        ("E31_stage_progression.run", ["--raw", str(raw), "--out", str(out/"E31")]),
        ("E32_pulse_visibility.run", ["--out", str(out/"E32")]),
        ("root_clock_figures", ["--root", str(out)]),
    )
    steps = []
    start = time.monotonic()
    for module, args in commands:
        launched = time.monotonic()
        result = subprocess.run([sys.executable, "-m", f"experiments.{module}", *args], env=env, check=False)
        steps.append({"module": module, "returncode": result.returncode, "wall_s": round(time.monotonic()-launched, 3)})
        if result.returncode:
            break
    if log:
        log.write_text(json.dumps({"runs": steps, "wall_s": round(time.monotonic()-start, 3)}, indent=2)+"\n")
    if steps[-1]["returncode"]:
        raise SystemExit(steps[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT/"data/raw/root_clock")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
