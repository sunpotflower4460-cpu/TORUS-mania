"""Replay E19–E20 with the frozen table and figure readings."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def run(out, log):
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    commands = [(f"E19_grid{n}", "E19_return_paths.run", ["--n", str(n), "--out", str(out / "E19")])
                for n in (128, 256, 512)]
    commands.extend((("E20", "E20_bending_controls.run", ["--out", str(out / "E20")]),
                     ("figures", "return_path_figures", ["--root", str(out)])))
    rows = []
    start = time.monotonic()
    for name, module, args in commands:
        before = time.monotonic()
        result = subprocess.run([sys.executable, "-m", f"experiments.{module}", *args], env=env, check=False)
        rows.append({"case": name, "returncode": result.returncode, "wall_s": round(time.monotonic()-before, 3)})
        if result.returncode:
            break
    if log:
        result_log = {"wall_s": round(time.monotonic()-start, 3), "runs": rows}
        log.write_text(json.dumps(result_log, indent=2) + "\n", encoding="utf-8")
    if rows[-1]["returncode"]:
        raise SystemExit(rows[-1]["returncode"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    opts = parser.parse_args()
    run(opts.out, opts.log)
