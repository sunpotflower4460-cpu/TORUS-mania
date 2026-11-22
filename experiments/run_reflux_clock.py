"""Reproduce E77/E78 and their figures without network access or new fitting data."""

import argparse
import hashlib
import json
from pathlib import Path
import platform

import matplotlib
import numpy
import scipy

from experiments.E77_growth_law_specificity.run import run as growth_specificity
from experiments.E78_circulation_clock.run import run as circulation_clock
from experiments.reflux_clock_figures import plot

ROOT = Path(__file__).resolve().parents[1]


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    growth_specificity(out / "E77")
    circulation_clock(out / "E78")
    plot(out)
    outputs = sorted(p for folder in ("E77", "E78", "reflux_clock_figures")
                     for p in (out / folder).iterdir() if p.is_file())
    hashes = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in outputs}
    checks = {e: json.loads((out / e / "summary.json").read_text())["checks"]
              for e in ("E77", "E78")}
    log = {
        "analysis": "E77_E78_reflux_clock_identifiability",
        "registration_commit": "4d27d24822b51697c989ad6e3ddfa56a8601ef57",
        "base_commit": "f014dbd642342b9e2682c9bb677c529a672a01be",
        "date": "2026-11-22", "timezone": "Asia/Tokyo",
        "run_kind": "retrospective_reanalysis_and_analytic_model_checks",
        "environment": {"python": platform.python_version(), "numpy": numpy.__version__,
                        "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
        "new_independent_biological_datasets": 0,
        "inputs": "Pinned E29/E34 JSON and existing E22/E28 code; no network needed.",
        "checks": checks, "all_checks_passed": all(all(v.values()) for v in checks.values()),
        "output_sha256": hashes,
        "orchestration_code_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), ROOT / "experiments/reflux_clock_figures.py")
        },
    }
    logpath = out / "REFLUX_CLOCK_RUN.json"
    logpath.write_text(json.dumps(log, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    hashes[logpath.name] = hashlib.sha256(logpath.read_bytes()).hexdigest()
    (out / "REFLUX_CLOCK_SHA256SUMS").write_text(
        "".join(f"{digest}  {relative}\n" for relative, digest in sorted(hashes.items())), encoding="utf-8")
    print(f"E77/E78: {sum(len(v) for v in checks.values())} checks; {len(outputs)} reproducible artifacts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results")
    run(parser.parse_args().out)
