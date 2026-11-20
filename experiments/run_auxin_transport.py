"""Replay E21–E23 using published measurements and a prespecified model."""

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
        ("E21", "E21_auxin_evidence.run", ["--out", str(out / "E21")]),
        ("E22", "E22_reentry_test.run", ["--out", str(out / "E22")]),
        ("E23", "E23_nitrate_pin2.run", ["--raw", str(raw), "--out", str(out / "E23")]),
        ("figures", "auxin_figures", ["--root", str(out)]),
    )
    rows = []
    start = time.monotonic()
    for key, module, args in commands:
        before = time.monotonic()
        result = subprocess.run([sys.executable, "-m", f"experiments.{module}", *args], env=env, check=False)
        rows.append({"case": key, "returncode": result.returncode, "wall_s": round(time.monotonic()-before, 3)})
        if result.returncode:
            break
    if log:
        info = {"wall_s": round(time.monotonic()-start, 3), "runs": rows}
        log.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    if rows[-1]["returncode"]:
        raise SystemExit(rows[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/auxin"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    options = parser.parse_args()
    run(options.raw, options.out, options.log)
