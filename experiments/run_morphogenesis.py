"""Replay E16–E18 from frozen figure readings and source-table counts."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from experiments.E17_flow_imprint.compare import VARIANTS


def run(out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}

    def invoke(name, module, args):
        started = time.monotonic()
        proc = subprocess.run([sys.executable, "-m", f"experiments.{module}", *args], env=env, check=False)
        return {"name": name, "returncode": proc.returncode, "wall_s": round(time.monotonic() - started, 3)}

    tasks = [(variant, "E17_flow_imprint.run", ["--variant", variant, "--out", str(out / "E17")])
             for variant in VARIANTS]
    tasks.extend((("E16", "E16_developmental_intervention.run", ["--out", str(out / "E16")]),
                  ("E18", "E18_organ_placement.run", ["--out", str(out / "E18")])))
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        runs = list(pool.map(lambda task: invoke(*task), tasks))
    if all(row["returncode"] == 0 for row in runs):
        runs.append(invoke("flow_comparison", "E17_flow_imprint.compare", ["--out", str(out / "E17")]))
        runs.append(invoke("figures", "morphogenesis_figures", ["--root", str(out)]))
    if log:
        log.write_text(json.dumps({"wall_s": round(time.monotonic()-started, 3), "runs": runs},
                                  indent=2) + "\n", encoding="utf-8")
    if any(row["returncode"] != 0 for row in runs):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    run(args.out, args.log)
