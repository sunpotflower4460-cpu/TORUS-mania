"""Replay E09–E12 with frozen literature readings and no network."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import os
import sys
import time

COMMANDS = (
    ("E09", "E09_harmonic_energy.run", ()),
    ("E10", "E10_energy_observations.run", ()),
    ("E11", "E11_energy_transport.run", ("--domain","fluid")),
    ("E11", "E11_energy_transport.run", ("--domain","light")),
    ("E12", "E12_meridian_prediction.run", ("--group","light")),
    ("E12", "E12_meridian_prediction.run", ("--group","circle")),
    ("E12", "E12_meridian_prediction.run", ("--group","slit")),
)


def run(out, log):
    env = {**os.environ,"OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MPLBACKEND":"Agg"}

    def launch(module, args):
        before = time.monotonic()
        status = subprocess.run([sys.executable,"-m",f"experiments.{module}",*args],env=env,check=False)
        return {"module": module,"variant": args[-1] if module.endswith(".run") and args[-2]!="--out" else None,
                "exit": status.returncode,"wall_s": round(time.monotonic()-before,3)}

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(launch,module,["--out",str(out/directory),*args])
                   for directory,module,args in COMMANDS]
        results = [future.result() for future in futures]
    if all(row["exit"]==0 for row in results):
        results.append(launch("energy_figures",["--root",str(out)]))
    if log:
        log.write_text(json.dumps({"elapsed_wall_s":round(time.monotonic()-started,3),
                                     "runs":results},indent=2)+"\n")
    if any(row["exit"]!=0 for row in results):
        raise SystemExit(1)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--log",type=Path)
    args=parser.parse_args()
    run(args.out,args.log)
