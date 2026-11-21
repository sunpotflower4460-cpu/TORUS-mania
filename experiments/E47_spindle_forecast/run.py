"""Test early streaming as a predictor of later spindle movement in the same oocyte."""

import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from scipy.stats import spearmanr

from experiments import measured_return_sources as sources
from experiments.common import save_summary

GROUPS = {"control": (1, 33), "Cdc42T17N": (34, 63)}
MODELS = {"group_mean": [], "early_flow": [0], "early_motion": [1], "both": [0, 1]}
SEED = 470013


def numbers(values):
    return np.array([float(x) if isinstance(x, (int, float)) else np.nan for x in values])


def sheets(raw):
    with BytesIO(sources.read(raw, "oocyte.xlsx")) as stream:
        book = load_workbook(stream, read_only=True, data_only=True)
        try:
            return [list(book[k].values) for k in ("S5 Fig", "S5C Fig", "S5E Fig", "Fig 6")]
        finally:
            book.close()


def time_series(summary, flows, positions):
    nrows = len(flows) - 3
    if nrows != len(positions)-3:
        raise ValueError("Different archive lengths for flow and position")
    axes = [numbers(row[j] for row in summary[3:3+nrows]) for j in (17, 32)]
    if not np.array_equal(axes[0], axes[1], equal_nan=True):
        # Group averages can stop at different points. The clocks must coincide wherever both are reported.
        common = np.isfinite(axes[0]) & np.isfinite(axes[1])
        if not np.array_equal(axes[0][common], axes[1][common]):
            raise ValueError("Time axes disagree")
    times = np.where(np.isfinite(axes[0]), axes[0], axes[1])
    groups = {}
    for group, (first, last) in GROUPS.items():
        indices = [f"#{i}" for i in range(1, last-first+1)]
        if list(flows[2][first:last]) != indices or list(positions[2][first:last]) != indices:
            raise ValueError(f"Column IDs do not match for {group}")
        groups[group] = []
        for col in range(first, last):
            # Calibrate to the paper's centerward-positive sign using the paired
            # published peak velocities. Keep both sign comparisons in the result.
            velocity = -numbers(row[col] for row in flows[3:])
            distance = numbers(row[col] for row in positions[3:])
            groups[group].append((velocity, distance))
    return times, groups


def coverage(times, values, window):
    low, high = window
    scheduled = (times >= low) & (times <= high)
    observed = scheduled & np.isfinite(values)
    usable = (observed.sum() >= np.ceil(scheduled.sum()/2) and observed.any()
              and times[observed][0] <= low+3 and times[observed][-1] >= high-3)
    return observed, bool(usable)


def eligible(times, records, early, late):
    indices = []
    for index, (flow, distance) in enumerate(records):
        if (coverage(times, flow, early)[1] and coverage(times, distance, early)[1]
                and coverage(times, distance, late)[1]):
            indices.append(index)
    return indices


def least_squares_slope(times, values):
    return float(np.polyfit(times, values, 1)[0])


def leave_one_out(design, y):
    estimates = []
    for i in range(len(y)):
        train = np.arange(len(y)) != i
        if np.linalg.matrix_rank(design[train]) < design.shape[1]:
            return None
        coefficient = np.linalg.lstsq(design[train], y[train], rcond=None)[0]
        estimates.append(float(design[i] @ coefficient))
    return {"rmse_um_per_min": float(np.sqrt(np.mean((y-estimates)**2))), "predictions": estimates}


def forecast(times, records, early, late):
    subjects = []
    for index in eligible(times, records, early, late):
        flow, distance = records[index]
        fmask, _ = coverage(times, flow, early)
        pmask, _ = coverage(times, distance, early)
        lmask, _ = coverage(times, distance, late)
        subjects.append({
            "cell": index+1, "early_flow": float(np.mean(flow[fmask])),
            "early_motion": -least_squares_slope(times[pmask], distance[pmask]),
            "later_motion": -least_squares_slope(times[lmask], distance[lmask]),
        })
    n = len(subjects)
    scores = {}
    association = None
    deletion_gains = {}
    if n >= 2:
        features = np.array([[s["early_flow"], s["early_motion"]] for s in subjects])
        y = np.array([s["later_motion"] for s in subjects])
        if n > 2:
            association = {
                "slope_late_motion_per_early_flow": least_squares_slope(features[:,0], y),
                "spearman_early_flow_vs_late_motion": float(spearmanr(features[:,0], y).statistic),
            }
        for model, columns in MODELS.items():
            design = np.column_stack([np.ones(n), features[:, columns]])
            result = leave_one_out(design, y)
            if result is not None:
                scores[model] = result
        if n >= 8:
            mean_design = np.ones((n,1))
            flow_design = np.column_stack([np.ones(n), features[:,0]])
            for i, subject in enumerate(subjects):
                keep = np.arange(n) != i
                baseline = leave_one_out(mean_design[keep], y[keep])
                flow = leave_one_out(flow_design[keep], y[keep])
                if baseline is not None and flow is not None:
                    deletion_gains[str(subject["cell"])] = baseline["rmse_um_per_min"] - flow["rmse_um_per_min"]
    return {"eligible_n": n, "source_n": len(records), "interpretable_n_at_least_8": n >= 8,
            "subjects_um_per_min": subjects, "signed_association": association, "leave_one_oocyte_out": scores,
            "posthoc_flow_gain_after_deleting_cell_um_per_min": deletion_gains}


def select_window(times, groups):
    candidates = []
    for start in range(4, 21, 2):
        early, late = [start, start+20], [start+36, start+56]
        counts = {k: len(eligible(times, records, early, late)) for k, records in groups.items()}
        fraction = min(n/len(groups[k]) for k, n in counts.items())
        candidates.append({"early": early, "late": late, "counts": counts, "smaller_fraction": fraction})
    selected = next((item for item in candidates if item["smaller_fraction"] >= .5), None)
    if selected is None:
        selected = max(candidates, key=lambda item: item["smaller_fraction"])
    return selected, candidates


def check_published_series(times, groups, published):
    audit = {}
    for group, (max_col, speed_col, mean_col) in zip(GROUPS, [(27,42,33), (28,43,35)]):
        reported_peak = numbers(row[max_col] for row in published[3:3+len(groups[group])])
        reported_speed = numbers(row[speed_col] for row in published[3:3+len(groups[group])])
        peaks, opposite_peaks, speeds = [], [], []
        for flow, distance in groups[group]:
            inside = (times >= 10) & (times <= 50)
            v = flow[inside & np.isfinite(flow)]
            order = max(1, int(np.ceil(len(v) * .1)))
            peaks.append(float(np.sort(v)[-order:].mean()))
            opposite_peaks.append(float(np.sort(-v)[-order:].mean()))
            dmask = inside & np.isfinite(distance)
            speeds.append(-least_squares_slope(times[dmask], distance[dmask]))
        mean_errors = []
        for i in range(len(times)):
            plotted = published[3+i][mean_col]
            if isinstance(plotted, (int, float)):
                observed = [d[i] for _,d in groups[group] if np.isfinite(d[i])]
                mean_errors.append(abs(np.mean(observed)-plotted))
        audit[group] = {
            "pearson_raw_sign_vs_printed_peaks": float(np.corrcoef(opposite_peaks, reported_peak)[0,1]),
            "pearson_centerward_sign_vs_printed_peaks": float(np.corrcoef(peaks, reported_peak)[0,1]),
            "mae_recalculated_peaks_vs_printed_um_per_min": float(np.mean(abs(reported_peak-peaks))),
            "pearson_recalculated_motion_vs_printed": float(np.corrcoef(speeds, reported_speed)[0,1]),
            "max_error_replicate_mean_vs_plotted_distance_um": float(max(mean_errors)),
            "same_window_spearman_printed_peak_vs_speed": float(spearmanr(reported_peak, reported_speed).statistic),
        }
    return audit


def position_interventions(rows):
    rng = np.random.default_rng(SEED)
    comparisons = {}
    for series, first, treatment in [("Fig6C",1,"Cdc42T17N"), ("Fig6D",5,"CK-666")]:
        if rows[0][first].replace(" ","").upper() != series.upper():
            raise ValueError(f"Unexpected panel {series}")
        groups = {}
        samples = []
        for col, name in enumerate(("control", treatment, treatment+"_plus_ROCK_inhibition"), first):
            a = numbers(row[col] for row in rows[3:])
            a = a[np.isfinite(a)]
            samples.append(a)
            groups[name] = {"n": len(a), "mean_um": float(a.mean()), "median_um": float(np.median(a))}
        contrasts = {}
        for label, a, b in (("single_minus_control", samples[1], samples[0]),
                            ("double_minus_single", samples[2], samples[1])):
            da, db = [rng.choice(x, (8000,len(x)), replace=True).mean(axis=1) for x in (a,b)]
            contrasts[label] = {"difference_of_means_um": float(a.mean()-b.mean()),
                                "cell_resampled_95_percentile_um": np.quantile(da-db, [.025,.975]).tolist()}
        comparisons[series] = {"groups": groups, "contrasts": contrasts}
    return comparisons


def outcome_composition(flow_rows, distance_rows, selected_ids):
    # Subgroup columns duplicate full-series columns under new ordinal IDs.
    # Use exact equality on both observables to audit losses; labels never enter the predictor.
    maps = []
    for rows in (flow_rows, distance_rows):
        blocks = [(label, numbers(row[j] for row in rows[3:]))
                  for label, cols in (("small_PB2", range(64,81)), ("relocation", range(82,94))) for j in cols]
        labels = []
        for col in range(*GROUPS["Cdc42T17N"]):
            series = numbers(row[col] for row in rows[3:])
            matches = [label for label, other in blocks if np.array_equal(series, other, equal_nan=True)]
            if len(matches) != 1:
                raise ValueError("Ambiguous phenotype assignment in duplicate columns")
            labels.append(matches[0])
        maps.append(labels)
    if maps[0] != maps[1]:
        raise ValueError("Flow and position subgroup assignments disagree")
    return {label: {"original_n": maps[0].count(label),
                    "eligible_ids": [i for i in selected_ids if maps[0][i-1] == label]}
            for label in ("small_PB2","relocation")}


def run(raw, out):
    summary, flows, positions, final = sheets(raw)
    times, groups = time_series(summary, flows, positions)
    selection, candidates = select_window(times, groups)
    windows = {}
    for label, early, late in (("registered", [0,20], [30,60]),
                               ("availability_selected", selection["early"], selection["late"])):
        windows[label] = {"early_min": early, "late_min": late,
                          "groups": {g: forecast(times, rows, early, late) for g, rows in groups.items()}}
    calibration = check_published_series(times, groups, summary)
    phenotypes = position_interventions(final)
    selected_ids = [r["cell"] for r in windows["availability_selected"]["groups"]["Cdc42T17N"]["subjects_um_per_min"]]
    composition = outcome_composition(flows, positions, selected_ids)
    report = {
        "experiment": "E47", "study_doi": "10.1371/journal.pbio.3001376",
        "source_doi": "10.1371/journal.pbio.3001376.s007", "time_reference": "activation, min",
        "source_alignment": calibration, "windows": windows, "availability_candidates": candidates,
        "posthoc_phenotype_composition_of_availability_window": composition,
        "position_at_90_min": phenotypes, "bootstrap_seed": SEED, "bootstrap_unit": "oocyte within condition; batch IDs unavailable",
        "checks": {
            "published_replicate_counts": [len(v) for v in groups.values()] == [32,29],
            "published_mean_positions_recovered": all(v["max_error_replicate_mean_vs_plotted_distance_um"] < .00001 for v in calibration.values()),
            "published_velocity_orientation_checked": all(v["pearson_centerward_sign_vs_printed_peaks"] > .85 for v in calibration.values()),
            "subject_columns_agree_with_reported_motion": all(v["pearson_recalculated_motion_vs_printed"] > .95 for v in calibration.values()),
            "selected_windows_separated_by_16_min": selection["late"][0] - selection["early"][1] == 16,
            "future_phenotypes_matched_across_both_archived_sheets": sum(p["original_n"] for p in composition.values()) == 29,
            "all_six_90min_groups": [g["n"] for p in phenotypes.values() for g in p["groups"].values()] == [67,27,14,55,34,34],
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, sources.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=sources.RAW)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw, args.out)
