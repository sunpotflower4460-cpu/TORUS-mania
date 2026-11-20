"""Replay E33–E38 and regenerate the report's figures."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from experiments import return_energy_data as data

EXPERIMENTS = (
    ("E33_directional_response", True),
    ("E34_root_period_transfer", True),
    ("E35_shoot_root_resources", True),
    ("E36_vortex_energy_transfer", True),
    ("E37_driven_circulation", False),
    ("E38_founder_reporters", True),
)


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    commands = [
        (name + ".run", ["--out", str(out / name[:3])] + (["--raw", str(raw)] if external else []))
        for name, external in EXPERIMENTS
    ]
    commands.append(("return_energy_figures", ["--root", str(out)]))
    start = time.monotonic()
    steps = []
    for module, args in commands:
        launched = time.monotonic()
        result = subprocess.run([sys.executable, "-m", "experiments." + module, *args], env=env, check=False)
        steps.append({"module": module, "returncode": result.returncode, "wall_s": round(time.monotonic()-launched, 3)})
        if result.returncode:
            break
    if log:
        log.write_text(json.dumps({"runs": steps, "wall_s": round(time.monotonic()-start, 3)}, indent=2)+"\n", encoding="utf-8")
    if steps[-1]["returncode"]:
        raise SystemExit(steps[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=data.RAW)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
