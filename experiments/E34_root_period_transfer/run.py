"""Score fixed growth-to-period forecasts and re-count peak outcomes."""

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re

import fitz
import numpy as np

from experiments import return_energy_data as data
from experiments.common import save_summary

BASE = "https://biblio.ugent.be/publication/01K47A0QNA2VHHET9FD517S20G/file/"
SOURCES = {
    "degern_article.pdf": (
        BASE + "01K47CJF9R1X89CRS2EQVDNXRH.pdf",
        "4e713e031c5fdd820a0f1c5d5e6c5d95609661b2ae5b5078a0f9f66ca32e4ff9",
    ),
    "degern_supplement.pdf": (
        BASE + "01K47CPPCZDZ6GK9Q2DTNWX610.pdf",
        "edd903540832cd25c2c9910f0f120c765d65d578ac5bde081e265111885ddb27",
    ),
}
SEAL = data.RESULTS / "E29/sealed_predictions.json"
GROUPS = ("WT", "eto2", "line1", "line4", "line2")

# Versioned image coordinates of the median stroke and the labelled y ticks.
# Reference ticks are stored as (pixel row, value); rows increase downward.
PANELS = {
    "growth_um_per_h": ("S3A", (241, 0), (70, 300), (115, 172, 126.5, 159.5, 209.5)),
    "peak_distance_um": ("3H", (436, 0), (300, 1600), (381, 401, 392.5, 391, 400.5)),
    "peak_period_h": ("3I", (436, 0), (300, 20), (417.5, 411, 417.5, 414, 384.5)),
    "peaks_per_mm": ("3J", (436, 0), (300, 4), (406, 395.5, 396, 397, 380.5)),
    "emerged_lateral_roots_per_cm": ("3E", (190, 0), (54, 5), (115, 121, 112, 115.5, 112.5)),
}
MEDIAN_READ_HALF_WIDTH_PX = 2


def reads():
    records = {name: {} for name in GROUPS}
    uncertainty = {}
    for endpoint, (_, (y0, value0), (y1, value1), pixels) in PANELS.items():
        slope = (value1 - value0) / (y1 - y0)
        uncertainty[endpoint] = abs(slope) * MEDIAN_READ_HALF_WIDTH_PX
        for name, y in zip(GROUPS, pixels):
            records[name][endpoint] = value0 + (y - y0) * slope
    return records, uncertainty


def outcomes(supplement):
    with fitz.open(stream=supplement, filetype="pdf") as pdf:
        page = pdf[13].get_text(sort=True)
    if "Table S4." not in page:
        raise ValueError("No contingency table on the registered supplement page")
    matches = re.findall(r"^\s*(WT|eto2|pPIN2::gACS5eto2 line[124])\s+(\d+)\s+(\d+)\s+(\d+)", page, re.M)
    if len(matches) != len(GROUPS):
        raise ValueError("Could not parse all genotypes in Table S4")
    groups = {}
    for label, normal, aborted, total in matches:
        normal, aborted, total = map(int, (normal, aborted, total))
        if normal + aborted != total:
            raise ValueError(f"Table S4 counts do not sum for {label}")
        groups[label.split()[-1]] = {
            "normal": normal, "aborted": aborted, "total_peaks": total, "normal_fraction": normal / total,
        }
    return groups


def forecast(velocity, period, tau):
    ratio = velocity[0] / velocity[1:]
    return np.vstack((
        np.full(len(ratio), period[0]),
        period[0] * ratio,
        tau + (period[0] - tau) * ratio,
    ))


def log_errors(prediction, period):
    return np.sqrt(np.mean(np.log(prediction / period[1:])**2, axis=1))


def evaluate(records, width, tau, waiting_cells):
    velocity = np.array([records[k]["growth_um_per_h"] for k in GROUPS])
    period = np.array([records[k]["peak_period_h"] for k in GROUPS])
    if period[0] - width["peak_period_h"] <= tau:
        raise ValueError("Wild-type period cannot calibrate this positive growth waiting time")
    predictions = forecast(velocity, period, tau)
    scores = log_errors(predictions, period)
    # Figure reading variation only. These corners are not statistical samples.
    sign = np.array(list(product((-1, 1), repeat=2 * len(GROUPS))))
    v_limits = velocity + sign[:, :len(GROUPS)] * width["growth_um_per_h"]
    t_limits = period + sign[:, len(GROUPS):] * width["peak_period_h"]
    sensitivity = np.array([log_errors(forecast(v, t, tau), t) for v, t in zip(v_limits, t_limits)])
    models = {}
    for i, name in enumerate(("constant_period", "constant_distance", "two_waiting_times")):
        models[name] = {
            "predictions_h": dict(zip(GROUPS[1:], predictions[i])),
            "log_rmse": float(scores[i]),
            "log_rmse_at_reading_corners": [float(sensitivity[:, i].min()), float(sensitivity[:, i].max())],
        }
    return {
        "models": models, "tau_h_from_E29": tau, "E29_waiting_cells": waiting_cells,
        "number_of_pixel_reading_corners": len(sensitivity),
        "corners_with_two_waits_better_than_both_controls": int(np.sum(
            sensitivity[:, 2] < np.min(sensitivity[:, :2], axis=1)
        )),
        "implied_mature_length_um_if_exact_E29": dict(zip(GROUPS, velocity * (period - tau) / waiting_cells)),
    }


def run(raw, out):
    article, supplement = [data.verified(raw/name, digest) for name, (_, digest) in SOURCES.items()]
    main_image = data.pdf_figure(article, 24, 113)
    supplement_image = data.pdf_figure(supplement, 3, 43)
    records, width = reads()
    peak_outcomes = outcomes(supplement)
    seal = SEAL.read_bytes()
    model = json.loads(seal)["models"]["two_waiting_times"]
    scored = evaluate(records, width, model["tau_h"], model["length_cells"])
    for name, record in records.items():
        record.update(peak_outcomes[name])
        record["estimated_normal_peaks_per_mm"] = record["normal_fraction"] * record["peaks_per_mm"]
    baseline = records["WT"]
    for name, record in records.items():
        for key in ("peaks_per_mm", "estimated_normal_peaks_per_mm", "emerged_lateral_roots_per_cm"):
            record[key + "_relative_to_WT"] = record[key] / baseline[key]
    report = {
        "experiment": "E34", "study_doi": "10.1093/plphys/kiaf382",
        "sources": {name: {"url": url, "sha256": digest} for name, (url, digest) in SOURCES.items()},
        "E29_seal_sha256": sha256(seal).hexdigest(),
        "panel_pixel_reading": PANELS, "median_reading_half_width": width,
        "genotype_observations": records, "held_out_treatments": scored,
        "checks": {
            "all_plotted_inputs_versioned": main_image.shape[:2] == (578, 661)
            and supplement_image.shape[:2] == (310, 786),
            "five_identifiable_outcome_groups": set(peak_outcomes) == set(GROUPS),
            "all_models_score_four_interventions": all(
                len(x["predictions_h"]) == 4 for x in scored["models"].values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=data.RAW)
    parser.add_argument("--out", type=Path, default=data.RESULTS/"E34")
    args = parser.parse_args()
    run(args.raw, args.out)
