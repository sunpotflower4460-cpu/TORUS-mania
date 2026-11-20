"""Replay E13–E15 using three checksum-verified, locally downloaded HDF5 files."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time


FLUX_CASES = ("ideal32", "ideal48", "diffusive32", "diffusive48", "time_refined48", "surface_coarse48", "shear")
ENERGY_CASES = ("light20", "light5", "flow48", "flow64")


def run(raw, out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}

    def launch(experiment, module, variant, args):
        before = time.monotonic()
        result = subprocess.run([sys.executable, "-m", f"experiments.{module}", *args], env=env, check=False)
        return {"experiment": experiment, "variant": variant, "returncode": result.returncode,
                "wall_s": round(time.monotonic() - before, 3)}

    commands = [
        ("E13", "E13_flux_transport.run", case, ["--case", case, "--out", str(out / "E13")]) for case in FLUX_CASES
    ] + [
        ("E14", "E14_moving_energy.run", case, ["--variant", case, "--out", str(out / "E14")]) for case in ENERGY_CASES
    ] + [
        ("E15", "E15_collision_data.run", "published_arrays", ["--raw", str(raw), "--out", str(out / "E15")])
    ]
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda command: launch(*command), commands))
    if all(row["returncode"] == 0 for row in results):
        results.append(launch("figures", "dynamics_figures", "all", ["--root", str(out)]))
    if log:
        log.write_text(json.dumps({"elapsed_wall_s": round(time.monotonic() - started, 3), "runs": results},
                                  indent=2) + "\n", encoding="utf-8")
    if any(row["returncode"] != 0 for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/dynamics"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.raw, args.out, args.log)
