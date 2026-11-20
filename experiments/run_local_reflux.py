"""Replay E24–E26, including the proton-growth source workbook reanalysis."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    commands = (
        ("E24_endodermal_pin3.run", ["--out", str(out / "E24")]),
        ("E25_endodermal_constraint.run", ["--out", str(out / "E25")]),
        ("E26_proton_growth.run", ["--raw", str(raw), "--out", str(out / "E26")]),
        ("local_reflux_figures", ["--root", str(out)]),
    )
    runs = []
    start = time.monotonic()
    for module, args in commands:
        launched = time.monotonic()
        result = subprocess.run([sys.executable, "-m", f"experiments.{module}", *args], env=env, check=False)
        runs.append({"module": module, "returncode": result.returncode, "wall_s": round(time.monotonic()-launched, 3)})
        if result.returncode:
            break
    if log:
        log.write_text(json.dumps({"wall_s": round(time.monotonic()-start, 3), "runs": runs}, indent=2) + "\n")
    if runs[-1]["returncode"]:
        raise SystemExit(runs[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/local_reflux"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
