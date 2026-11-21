"""Reanalyse Hu et al. figure arrays for directional responses."""

import argparse
import io
from pathlib import Path
import re

import numpy as np
from openpyxl import load_workbook

from experiments import return_energy_data as data
from experiments.common import save_summary

URL = (
    "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-021-21802-3/"
    "MediaObjects/41467_2021_21802_MOESM12_ESM.xlsx"
)
SHA = "dc62b28a11ae34eb29084a8944f14714ebb6fe183146494432989fa34100410e"
TREATMENTS = ("E2", "NPA+E2", "NOA+E2")
ASSAYS = (
    ("pWOX5", "quiescent_centre_induction", 0),
    ("pSHR-EZ", "stele_to_outer_elongation_zone", 5),
    ("pSHR-stele", "stele_to_root_tip", 10),
    ("pAPL", "phloem_induction", 15),
    ("pSCR", "endodermis_induction", 20),
    ("pWER", "epidermis_to_stele_differentiation_zone", 25),
)


def single_reading_sensitivity(values, denominator):
    value = np.mean(values)
    baseline = np.mean(denominator)
    minus_value = (values.sum() - values) / (len(values) - 1)
    minus_baseline = (denominator.sum() - denominator) / (len(denominator) - 1)
    ratios = np.r_[minus_value / baseline, value / minus_baseline]
    return [float(ratios.min()), float(ratios.max())]


def responses(rows):
    groups = {}
    max_discrepancy = 0.
    for label, name, col in ASSAYS:
        start = rows[0][col:col+4]
        if start != (f"{label} (RFU)", *TREATMENTS):
            raise ValueError(f"Unexpected worksheet header for {label}: {start}")
        measurements = np.asarray([
            row[col+1:col+4] for row in rows[1:]
            if isinstance(row[col], str) and re.fullmatch(r"(cell |Root |ROI)\d+", row[col])
        ], dtype=float).T
        original_mean = next(row[col+1:col+4] for row in rows if row[col] == "Mean")
        means = measurements.mean(axis=1)
        max_discrepancy = max(max_discrepancy, float(np.max(np.abs(means - original_mean))))
        reference = measurements[0]
        groups[name] = {
            "workbook_label": label,
            "conditions": {
                treatment: {
                    "readings_RFU": vector.tolist(), "count_in_workbook": len(vector),
                    "mean_RFU": float(mean), "fraction_of_E2_mean": float(mean / means[0]),
                    "delete_one_measurement_ratio_range": (
                        [1., 1.] if treatment == "E2" else single_reading_sensitivity(vector, reference)
                    ),
                }
                for treatment, vector, mean in zip(TREATMENTS, measurements, means)
            },
        }
    return groups, max_discrepancy


def ablation(rows):
    output = {}
    delta = 0.
    for col, time in enumerate(("1 h", "12 h", "24 h"), 1):
        points = np.asarray([
            (row[col], row[col+3]) for row in rows[2:]
            if isinstance(row[0], str) and row[0].startswith("cell ")
            and isinstance(row[col], (float, int)) and isinstance(row[col+3], (float, int))
        ])
        means = points.mean(axis=0)
        reported = next((row[col], row[col+3]) for row in rows if row[0] == "Mean")
        delta = max(delta, float(np.max(np.abs(means - reported))))
        output[time] = {
            "paired_lower_upper_readings": points.tolist(), "paired_cells": len(points),
            "mean_lower": float(means[0]), "mean_upper": float(means[1]),
            "lower_minus_upper_mean": float(means[0] - means[1]),
            "median_of_paired_differences": float(np.median(points[:, 0] - points[:, 1])),
        }
    return output, delta


def run(raw, out):
    workbook = load_workbook(io.BytesIO(data.verified(raw/"yang_source.xlsx", SHA)), read_only=True, data_only=True)
    try:
        groups, discrepancy = responses(list(workbook["Fig.5c"].values))
        ablated, discrepancy_ablation = ablation(list(workbook["Fig.5e"].values))
    finally:
        workbook.close()
    inward = groups["epidermis_to_stele_differentiation_zone"]["conditions"]
    outward = groups["stele_to_outer_elongation_zone"]["conditions"]
    into_tip = groups["stele_to_root_tip"]["conditions"]
    ratio = "fraction_of_E2_mean"
    summary = {
        "experiment": "E33", "study_doi": "10.1038/s41467-021-21802-3",
        "source": {"url": URL, "sha256": SHA}, "analysis_units": "Workbook regions, cells, or individually labelled roots",
        "fig5c_relative_response": groups,
        "main_NOA_minus_NPA_retained_fraction_inward": inward["NOA+E2"][ratio] - inward["NPA+E2"][ratio],
        "NOA_retained_fraction_inward_minus_outward": inward["NOA+E2"][ratio] - outward["NOA+E2"][ratio],
        "fig5e_after_epidermis_ablation": ablated,
        "maximum_mean_difference_from_author_workbook": max(discrepancy, discrepancy_ablation),
        "registered_direction_pattern": {
            "NPA_decreases_all_three_targets": all(
                g["NPA+E2"][ratio] < 1 for g in (inward, outward, into_tip)
            ),
            "larger_NOA_retained_fraction_inward_and_to_tip_than_outward": (
                min(inward["NOA+E2"][ratio], into_tip["NOA+E2"][ratio]) > outward["NOA+E2"][ratio]
            ),
        },
        "checks": {
            "Fig5c_all_six_blocks_read": len(groups) == 6,
            "Fig5e_cell_counts": [row["paired_cells"] for row in ablated.values()] == [27, 25, 19],
            "author_means_reproduced": max(discrepancy, discrepancy_ablation) < 1e-8,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=data.RAW)
    parser.add_argument("--out", type=Path, default=data.RESULTS/"E33")
    args = parser.parse_args()
    run(args.raw, args.out)
