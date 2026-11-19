"""Shared ring coordinates and deterministic output for the two calibration experiments."""

import hashlib
import json
from pathlib import Path

import numpy as np


def ring_xyz(phi, theta, major_radius=2.0):
    """A ring of minor radius 1. Broadcasting also permits sampling the full surface."""
    radius = major_radius + np.cos(theta)
    x, y, z = np.broadcast_arrays(radius * np.cos(phi), radius * np.sin(phi), np.sin(theta))
    return np.stack((x, y, z), axis=-1)


def save_summary(directory, summary, *source_files):
    files = [Path(__file__), *map(Path, source_files)]
    summary["code_sha256"] = {p.parent.name + "/" + p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in files}
    path = directory / "summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")
    failed = [name for name, passed in summary["checks"].items() if not passed]
    print(f"{path}: {len(summary['checks'])} checks, {len(failed)} failed")
    if failed:
        raise SystemExit("Failed calibration: " + ", ".join(failed))
