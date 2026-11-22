"""Retrieve pinned author sources and reproduce E79/E80 descriptive results.

Examples:
  python -m experiments.run_abcb_clock --cache /tmp/chen2023-originals --out /tmp/chen2023-results
  python -m experiments.run_abcb_clock --cache /tmp/chen2023-originals --offline

Source workbooks remain outside the checkout.  No observation-level CSV is emitted.
"""

import json
from pathlib import Path
import platform

import matplotlib

from experiments.abcb_source import (
    BASE_COMMIT, MANIFEST, REGISTRATION_COMMIT, ROOT, Sources, parser, sha256,
)
from experiments.E79_abcb_clock.run import run as clock
from experiments.E80_abcb_transport.run import run as transport
from experiments.abcb_clock_figures import plot


def run(out, cache, offline=False):
    out = Path(out)
    sources = Sources(cache, offline)
    first = clock(out / "E79", sources)
    second = transport(out / "E80", sources)
    plot(out)
    files = [out / "E79/summary.json", out / "E80/summary.json"]
    files.extend(sorted((out / "abcb_clock_figures").glob("abcb_clock_ratios.*")))
    hashes = {p.relative_to(out).as_posix(): sha256(p.read_bytes()) for p in files}
    checks = {s["experiment"]: s["checks"] for s in (first, second)}
    code = [Path(__file__), ROOT / "experiments/abcb_source.py",
            ROOT / "experiments/E79_abcb_clock/run.py", ROOT / "experiments/E80_abcb_transport/run.py",
            ROOT / "experiments/abcb_clock_figures.py"]
    summary = {
        "analysis": "E79_E80_ABCB_clock_observation_units_and_transport",
        "registration_commit": REGISTRATION_COMMIT, "base_commit": BASE_COMMIT,
        "date": "2026-11-22", "timezone": "Asia/Tokyo",
        "run_kind": "retrospective_descriptive_reanalysis_and_measurement_audit",
        "environment": {"python": platform.python_version(), "matplotlib": matplotlib.__version__,
                        "data_reader": "standard-library OOXML ElementTree and independent minidom/Decimal"},
        "source_manifest": {"path": MANIFEST.relative_to(ROOT).as_posix(), "sha256": sha256(sources.manifest_bytes)},
        "study_doi": "10.15252/embr.202256271", "newly_analyzed_author_studies": 1,
        "new_biological_experiments": 0, "independent_replications_performed": 0,
        "root_level_confidence_intervals_or_equivalence_tests": "not_identifiable_without_unit_ids",
        "source_originals_redistributed": False, "individual_observation_tables_redistributed": False,
        "checks": checks, "all_checks_passed": all(all(x.values()) for x in checks.values()),
        "output_sha256": hashes,
        "code_sha256": {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()) for p in code},
    }
    log = out / "ABCB_CLOCK_RUN.json"
    log.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    hashes[log.name] = sha256(log.read_bytes())
    (out / "ABCB_CLOCK_SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())), encoding="utf-8")
    print(f"E79/E80: {sum(len(c) for c in checks.values())} numerical/input checks; {len(files)} result/figure files")


if __name__ == "__main__":
    args = parser(__doc__, ROOT / "research/results").parse_args()
    run(args.out, args.cache, args.offline)

