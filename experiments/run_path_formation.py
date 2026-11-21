"""Replay the molecular-history and early-formation experiments."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = (
    ("E39_auxin_probe_identity", True), ("E40_tracer_history", False), ("E41_oocyte_polarity", True),
    ("E42_embryo_mechanics", True), ("E43_matched_torus_flow", False),
)


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    commands = [
        (name+".run", ["--out", str(out/name[:3])] + (["--raw", str(raw)] if external else []))
        for name, external in EXPERIMENTS
    ]
    commands.append(("path_formation_figures", ["--root", str(out)]))
    steps, start = [], time.monotonic()
    for module, args in commands:
        launched = time.monotonic()
        result = subprocess.run([sys.executable, "-m", "experiments."+module, *args], env=env, check=False)
        steps.append({"module": module, "returncode": result.returncode, "wall_s": round(time.monotonic()-launched, 3)})
        if result.returncode:
            break
    if log:
        log.write_text(json.dumps({"runs": steps, "wall_s": round(time.monotonic()-start, 3)}, indent=2)+"\n",
                       encoding="utf-8")
    if steps[-1]["returncode"]:
        raise SystemExit(steps[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT/"data/raw/path_and_formation")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
