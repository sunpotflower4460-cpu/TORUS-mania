"""Replay E27–E29 and verify the sealed forecasts before reading the holdout."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SEALED = ROOT/"research/results/E29/sealed_predictions.json"


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    pdf = raw/"berg_uu_alt.pdf"
    frozen = out/"E29/sealed_predictions.json"
    commands = (
        ("E27_plasmodesmata.run", ["--raw", str(raw), "--out", str(out/"E27")]),
        ("E28_return_growth.run", ["--out", str(out/"E28")]),
        ("E29_growth_holdout.run", ["seal", "--pdf", str(pdf), "--predictions", str(frozen)]),
        ("E29_growth_holdout.run", ["evaluate", "--pdf", str(pdf), "--predictions", str(frozen), "--out", str(out/"E29")]),
        ("reflux_growth_figures", ["--root", str(out)]),
    )
    steps = []
    started = time.monotonic()
    expected = SEALED.read_bytes()
    if frozen.resolve() == SEALED.resolve():
        raise ValueError("Use a separate output directory for a replay so that the published seal is preserved")
    for name, args in commands:
        launched = time.monotonic()
        result = subprocess.run([sys.executable, "-m", f"experiments.{name}", *args], env=env, check=False)
        steps.append({"module": name, "operation": args[0], "returncode": result.returncode,
                      "wall_s": round(time.monotonic()-launched, 3)})
        if result.returncode:
            break
        if args[0] == "seal" and frozen.read_bytes() != expected:
            raise ValueError("Reconstructed predictions differ from the committed seal")
    if log:
        log.write_text(json.dumps({"runs": steps, "wall_s": round(time.monotonic()-started, 3)}, indent=2)+"\n")
    if steps[-1]["returncode"]:
        raise SystemExit(steps[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT/"data/raw/reflux_growth")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
