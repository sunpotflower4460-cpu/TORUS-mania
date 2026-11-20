"""Reanalyse pH pulses and root elongation from Li et al.'s source workbooks."""

import argparse
from hashlib import sha256
import json
from math import log
from pathlib import Path
from statistics import mean, median, stdev

import numpy as np
from openpyxl import load_workbook
from PIL import Image

from experiments.common import save_summary


ROOT = Path(__file__).resolve().parents[2]
STATIC = "https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/"
SOURCES = {
    "li_f1.xlsx": ("41586_2021_4037_MOESM8_ESM.xlsx", "9f3dd97802ffca9b4e58a9255a1cd9da8fc89c99e1318fa676f4c299c298cee6"),
    "li_f2.xlsx": ("41586_2021_4037_MOESM9_ESM.xlsx", "8fda1a14473035b931ce1f826182001a412c0136bea1ce2066f709854a600de7"),
    "li_ext2.xlsx": ("41586_2021_4037_MOESM13_ESM.xlsx", "0ba797314b6bfe8e4766db5e9e3440e5961c06651178c5b182a11eb291e921a0"),
}
FIG1_URL = (
    "https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-021-04037-6/MediaObjects/"
    "41586_2021_4037_Fig1_HTML.png"
)
FIG1_SHA256 = "ff38151d9492579203313253905017b1ca5f7a35289aea82633d25d11f982512"
REFERENCE_PH = 5.80
TEMPERATURE_K = 298.15
GAS_CONSTANT = 8.31446261815324


def source_book(raw, filename):
    archive_name, expected = SOURCES[filename]
    path = raw / filename
    digest = sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError(f"Unexpected source workbook version: {path} ({digest})")
    return load_workbook(path, data_only=True), {"url": STATIC + archive_name, "sha256": digest}


def series(sheet, time_column, first_root_column, n_roots, measure_label):
    rows = list(sheet.values)
    header = rows[0]
    column_slice = slice(first_root_column, first_root_column+n_roots)
    ids = rows[1][column_slice]
    if (header[first_root_column] != measure_label or header[time_column] not in ("time (in min)", "time (min)")
            or ids != tuple(range(1, n_roots+1))):
        raise ValueError(f"Unexpected series headers in {sheet.title}")
    observations = [(row[time_column], row[column_slice])
                    for row in rows[2:] if row[time_column] is not None]
    times = np.array([row[0] for row in observations], dtype=float)
    values = np.array([row[1] for row in observations], dtype=float)
    if np.any(np.diff(times) <= 0.) or not np.any(np.isfinite(values)):
        raise ValueError(f"Invalid time coverage in {sheet.title}")
    return times, values, ids


def time_window(times, values, ids, start, stop, *, include_start=True, include_stop=False):
    lower = (times >= start) if include_start else (times > start)
    upper = (times <= stop) if include_stop else (times < stop)
    selection = lower & upper
    block = values[selection]
    if not len(block):
        raise ValueError(f"No observations in window {start}–{stop} min")
    complete = np.all(np.isfinite(block), axis=0)
    by_root = {str(root): float(block[:, i].mean()) for i, root in enumerate(ids) if complete[i]}
    if not by_root:
        raise ValueError(f"No complete roots in window {start}–{stop} min")
    return {
        "sample_times_min": times[selection].tolist(), "n_roots": len(by_root),
        "mean_of_root_means": mean(by_root.values()), "per_root_window_means": by_root,
    }


def paired_window_change(baseline, other):
    before, after = (window["per_root_window_means"] for window in (baseline, other))
    overlap = sorted(before.keys() & after.keys(), key=int)
    deltas = [after[root] - before[root] for root in overlap]
    first = mean(before[root] for root in overlap)
    second = mean(after[root] for root in overlap)
    return {
        "n_matched_roots": len(deltas), "baseline_mean_matched": first, "comparison_mean_matched": second,
        "mean_change": mean(deltas), "matched_mean_change_percent": 100. * mean(deltas)/first,
        "observed_individual_changes_min_max": [min(deltas), max(deltas)],
        "positive_changes": sum(value > 0 for value in deltas), "negative_changes": sum(value < 0 for value in deltas),
    }


def pulse_windows(data, onset, offset):
    times, values, ids = data
    last = float(times[-1])
    windows = {
        "baseline": time_window(times, values, ids, onset-5., onset),
        "early_pulse_descriptive": time_window(times, values, ids, onset, min(onset+5., offset), include_start=False),
        "late_pulse": time_window(times, values, ids, max(onset, offset-5.), offset),
        "late_washout": time_window(times, values, ids, max(offset, last-5.), last, include_stop=True),
    }
    return {
        "onset_min": onset, "washout_start_min": offset, "windows": windows,
        "paired_change_from_baseline": {name: paired_window_change(windows["baseline"], window)
                                        for name, window in windows.items() if name != "baseline"},
    }


def aggregate_trace(data):
    times, values, _ = data
    rows = [row[np.isfinite(row)] for row in values]
    return {
        "time_min": times.tolist(), "mean": [float(row.mean()) if len(row) else None for row in rows],
        "sample_sd": [float(row.std(ddof=1)) if len(row) > 1 else None for row in rows],
        "n_roots": [len(row) for row in rows],
    }


def chemical_shift(ph):
    shift = ph - REFERENCE_PH
    return {
        "reference_pH": REFERENCE_PH, "pulse_pH": ph, "delta_pH": shift,
        "reference_temperature_K": TEMPERATURE_K, "activity_ratio_pulse_over_reference": 10.**(-shift),
        "extracellular_chemical_potential_change_J_per_mol": -GAS_CONSTANT*TEMPERATURE_K*log(10.)*shift,
    }


def atpase_activity(sheet):
    header, *measurements = sheet.values
    if header != ("replicate", "normalized WT mock", "normalized WT 100nM IAA"):
        raise ValueError("The ATP hydrolysis worksheet layout has changed")
    ratios = [treated/mock for _, mock, treated in measurements]
    return {
        "n_reported_biological_replicates": len(ratios), "IAA_nM": 100, "exposure_minutes": 60,
        "relative_activity_means_from_normalized_extracts": mean(ratios),
        "sample_sd_relative_activity": stdev(ratios),
        "notes": "The relative hydrolytic activity of extracts does not provide in vivo ATP use or power.",
    }


def growth_axis_audit(path, trace):
    """Compare figure and workbook scale without applying a correction to either."""
    if sha256(path.read_bytes()).hexdigest() != FIG1_SHA256:
        raise ValueError(f"Unexpected figure version: {path}")
    with Image.open(path) as figure:
        pixels = np.asarray(figure.convert("RGB"))
    mappings = []
    for time in (-4., -2., 0., 5., 10., 20., 28., 30., 40.):
        x = round(106 + time * (317 - 106) / 32.)
        rows = [np.flatnonzero(pixels[540:817, c].max(axis=1) < 115)[-1] + 540 for c in range(x-1, x+2)]
        reads = [(822 - int(row)) * 6./287. for row in rows]
        original = trace["mean"][trace["time_min"].index(time)]
        mappings.append({"time_min": time, "mean_in_workbook": original, "figure_readout_median": median(reads),
                         "figure_to_workbook_ratio": median(reads)/original})
    return {
        "image_url": FIG1_URL, "sha256": FIG1_SHA256, "readout_points": mappings,
        "median_ratio": median(row["figure_to_workbook_ratio"] for row in mappings),
        "note": "Secondary comparison after noticing the discrepancy. Do not infer absolute growth units from this ratio.",
    }


def run(raw, out):
    f1, source1 = source_book(raw, "li_f1.xlsx")
    f2, source2 = source_book(raw, "li_f2.xlsx")
    ext2, source_ext2 = source_book(raw, "li_ext2.xlsx")
    alkaline = series(f1["Fig1e"], 1, 2, 8, "Growth (um/min)")
    acidic = series(f1["Fig1g"], 1, 2, 7, "Growth (um/min)")
    iaa_growth = series(f1["Fig1b"], 0, 1, 4, "Growth (um/min)")
    iaa_ph = series(f1["Fig1b"], 0, 6, 4, "rel pH")
    influx = series(ext2["ExtDataFig2c"], 0, 1, 9, "Net H+ influx (nmol/m2s)")
    before_iaa = time_window(*influx, -3., 0.)
    # The electrode sheet has a break during solution exchange. Use the first
    # three minutes after recording resumes at its full post-exchange coverage.
    after_iaa = time_window(*influx, 1., 4.)
    a = {"medium": chemical_shift(6.15), **pulse_windows(alkaline, 26., 44.)}
    b = {"medium": chemical_shift(5.10), **pulse_windows(acidic, 20., 42.)}
    activity = atpase_activity(f2["Fig2b"])
    f1.close()
    f2.close()
    ext2.close()
    traces = {"alkaline": aggregate_trace(alkaline), "acidic": aggregate_trace(acidic),
              "iaa_growth": aggregate_trace(iaa_growth), "iaa_HPTS": aggregate_trace(iaa_ph),
              "iaa_10nM_H_influx": aggregate_trace(influx)}
    audit = growth_axis_audit(raw / "li_fig1.png", traces["iaa_growth"])
    checks = {
        "alkaline_primary_contrast_has_eight_paired_roots": a["paired_change_from_baseline"]["late_pulse"]["n_matched_roots"] == 8,
        "late_alkaline_washout_has_seven_paired_roots": a["paired_change_from_baseline"]["late_washout"]["n_matched_roots"] == 7,
        "acid_primary_contrast_has_seven_paired_roots": b["paired_change_from_baseline"]["late_pulse"]["n_matched_roots"] == 7,
        "chemical_shift_from_activity_ratio": all(
            abs(GAS_CONSTANT*TEMPERATURE_K*log(x["medium"]["activity_ratio_pulse_over_reference"])
                - x["medium"]["extracellular_chemical_potential_change_J_per_mol"]) < 1.e-10 for x in (a, b)
        ),
        "three_atpase_biological_replicates": activity["n_reported_biological_replicates"] == 3,
        "electrode_comparison_has_eight_matched_roots": len(set(before_iaa["per_root_window_means"])
                                                            & set(after_iaa["per_root_window_means"])) == 8,
        "IAA_growth_preserves_the_source_gaps_at_32_5_and_33_min": [
            time for time, n in zip(traces["iaa_growth"]["time_min"], traces["iaa_growth"]["n_roots"], strict=True)
            if n == 0
        ] == [32.5, 33.],
    }
    summary = {
        "experiment": "E26", "study_doi": "10.1038/s41586-021-04037-6",
        "sources": {"figure_1": source1, "figure_2": source2, "extended_data_figure_2": source_ext2},
        "pH_pulse_growth_units": "micrometres per minute", "fig1e_alkaline_pulse": a, "fig1g_acidic_pulse": b,
        "Fig1b_5nM_IAA_pulse": {
            "growth_on_workbook_scale": pulse_windows(iaa_growth, 0., 32.),
            "apoplastic_HPTS_ratio": pulse_windows(iaa_ph, 0., 32.),
        },
        "Fig1b_growth_sheet_vs_figure_axis_audit": audit,
        "Fig2b_ATP_hydrolysis_secondary": activity,
        "ExtData2c_10nM_IAA_net_H_influx": {
            "units": "nmol per square metre per second; positive is inward",
            "baseline": before_iaa, "initial_IAA_exposure": after_iaa,
            "paired_change": paired_window_change(before_iaa, after_iaa),
            "note": "Separate root samples from the pH pulses, IAA imaging, and ATP hydrolysis assays.",
        },
        "window_policy": "Last five minutes of each phase. Switch times mark the start of the next phase. "
                         "Include the last recorded sample in late washout. Early pulse is descriptive. "
                         "Use only roots with complete data in both compared windows.",
        "checks": checks,
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__)
    (out / "traces.json").write_text(json.dumps(traces, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/raw/local_reflux")
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E26")
    args = parser.parse_args()
    run(args.raw, args.out)
