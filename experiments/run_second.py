"""Run the registered E03–E08 series offline on Linux and record each process's resource use."""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy
import scipy

from experiments.E05_interaction.run import PAIRS
from experiments.E06_jet.run import CASES


def commands(out, workbook):
    yield "E03", "E03_vortex.run", ["--out", out/"E03"]
    yield "E03/cylinder", "E03_vortex.axisymmetric", ["--out", out/"E03/cylinder"]
    yield "E03/observers", "E03_vortex.observers", ["--out", out/"E03/observers"]
    yield "E04", "E04_transport.run", ["--out", out/"E04"]
    yield "E04/plant", "E04_transport.plant_data", [workbook,"--out",out/"E04/plant"]
    for name in ("phases", *PAIRS):
        yield "E05/"+name, "E05_interaction.run", ["--case",name,"--out",out/"E05"]
    for name in CASES:
        yield "E06/"+name, "E06_jet.run", ["--case",name,"--out",out/"E06"]
    yield "E06/circle_fine", "E06_jet.run", ["--refine-circle","--out",out/"E06"]
    yield "E07/predict", "E07_transfer.predict", ["--out",out/"E07"]
    yield "E07/score", "E07_transfer.run", ["--out",out/"E07"]
    yield "E08", "E08_survey.run", ["--out",out/"E08"]
    yield "figures", "second_figures", ["--root",out]


def run(out, workbook, log, code_id):
    env = dict(os.environ, MPLBACKEND="Agg", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    report = {"code_version": code_id, "python": platform.python_version(), "system": platform.system(),
              "versions": {"numpy": numpy.__version__, "scipy": scipy.__version__,
                           "matplotlib": matplotlib.__version__}, "thread_limit": 1, "processes": []}
    log.parent.mkdir(parents=True, exist_ok=True)
    for label, module, args in commands(out, workbook):
        start = datetime.now(timezone.utc).isoformat()
        before = time.perf_counter()
        proc = subprocess.Popen([sys.executable, "-m", "experiments."+module, *args], env=env)
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        report["processes"].append({"series": label, "start_utc": start, "exit": proc.returncode,
                                   "wall_s": time.perf_counter()-before,
                                   "cpu_s": usage.ru_utime+usage.ru_stime,
                                   "peak_rss_mib": usage.ru_maxrss/1024})
        log.write_text(json.dumps(report, indent=2) + "\n")
        if proc.returncode:
            raise SystemExit(f"{label} exited {proc.returncode}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--code-id", help="Commit used in this run; informational only")
    args = p.parse_args()
    run(args.out.resolve(), args.workbook.resolve(), args.log.resolve(), args.code_id)
