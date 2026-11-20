"""Reanalyse embryo-level speed and shape after tissue ablation."""

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from openpyxl import load_workbook

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/path_and_formation"
URL = "https://datadryad.org/api/v2/versions/373722/download"
SEED, BOOTSTRAPS = 424239, 8000
GROUPS = ("control", "Control ablation", "NC ablation", "PC ablation")
BOOKS = {
    "lumen-shape-data-experiments.xlsx": "d9dffce544e4a09dbfffd97a005eb6d263d71fe46b7207e42adc65e5d50fba14",
    "lumen-speed-data-experiments.xlsx": "c0b748dc13a916238a10bd4ad1febdf738b2be3235afcb9a89df19e245ad7e5e",
    "lumen-shape-data-simulation.xlsx": "4feaf0568bf8d358fb10cbfbe5beab0d7cedb9e086189152c6b7a3ad411e94e1",
    "lumen-speed-data-simulation.xlsx": "b790bbbbe1e73c5158218bda82fe8782af0274ce853610f54d6bb1a72b20fec6",
    "KV_cell_apical_width_data_Fig_4C-D.xlsx": "460d01badd552c757f02024de3ff9f76bef5a90163ba0c67312d2207c77cc162",
}


def read_books(archive):
    books = {}
    with ZipFile(archive) as entries:
        for name, checksum in BOOKS.items():
            binary = entries.read(name)
            if sha256(binary).hexdigest() != checksum:
                raise ValueError(f"Unexpected version of {name}")
            with BytesIO(binary) as stream:
                workbook = load_workbook(stream, read_only=True, data_only=True)
                try:
                    books[name] = {s.title: list(s.values) for s in workbook}
                finally:
                    workbook.close()
    return books


def embryo_data(rows, complete_stages):
    header, measurements = rows[0], rows[1:]
    if header[:2] != ("embryo #", "somite stage"):
        raise ValueError(f"Unknown measurement columns {header}")
    by_embryo = defaultdict(lambda: defaultdict(list))
    for embryo, stage, value in measurements:
        if isinstance(embryo, (float, int)) and isinstance(stage, (float, int)) and 5 <= stage <= 7:
            if not isinstance(value, (float, int)):
                raise ValueError(f"Missing numeric measure for embryo {embryo}, stage {stage}")
            by_embryo[int(embryo)][stage].append(value)
    means, complete = {}, {}
    for embryo, by_stage in by_embryo.items():
        means[str(embryo)] = float(np.mean([x for group in by_stage.values() for x in group]))
        if all(stage in by_stage for stage in complete_stages):
            complete[str(embryo)] = float(np.mean([np.mean(by_stage[stage]) for stage in complete_stages]))
    return means, complete, sum(len(x) for by_stage in by_embryo.values() for x in by_stage.values())


def contrast(treatment, baseline, rng):
    treatment, baseline = np.asarray(treatment), np.asarray(baseline)
    draws = []
    for group in (treatment, baseline):
        draws.append(group[rng.integers(0, len(group), (BOOTSTRAPS, len(group)))].mean(axis=1))
    return {
        "treatment_minus_baseline": float(treatment.mean() - baseline.mean()),
        "percentile_ci_95": np.quantile(draws[0]-draws[1], [.025,.975]).tolist(),
    }


def analyse_observations(sheets, complete_stages, rng):
    groups, observed = {}, {}
    for key in GROUPS:
        means, complete, count = embryo_data(sheets[key], complete_stages)
        observed[key] = list(means.values())
        groups[key] = {
            "n_embryos": len(means), "n_stage_observations": count, "embryo_means": means,
            "mean_of_embryos": float(np.mean(observed[key])),
            "complete_case_count": len(complete),
            "complete_case_mean": float(np.mean(list(complete.values()))) if complete else None,
        }
    differences = {}
    for condition in GROUPS[1:]:
        differences[condition] = {"versus_unablated": contrast(observed[condition], observed["control"], rng)}
        if condition != "Control ablation":
            differences[condition]["versus_sham"] = contrast(observed[condition], observed["Control ablation"], rng)
    return {"groups": groups, "contrasts": differences}


def model_directions(archive, observed):
    _, *entries = archive["control"]
    rows = np.array([row[1:4] for row in entries if isinstance(row[0], int)], dtype=float)
    directions = {}
    for index, name in enumerate(GROUPS[2:], 1):
        model_relative_change = float(rows[:, index].mean()/rows[:, 0].mean() - 1)
        data_delta = observed["contrasts"][name]["versus_unablated"]["treatment_minus_baseline"]
        directions[name] = {
            "relative_model_change": model_relative_change,
            "experiment_and_model_same_sign": bool(np.sign(data_delta) == np.sign(model_relative_change)),
        }
    return {"model_ensembles": len(rows), "comparison": directions}


def apical_width(sheets, rng):
    rows = sheets["Embyro averages"]
    groups = {}
    # The two condition columns end on different rows. The next numeric
    # row in each is a formula averaging the embryos, not another embryo.
    for name, a, p, stop in (("control", 0, 3, 17), ("NC ablation", 1, 4, 23)):
        pair = np.array([(row[a], row[p]) for row in rows[2:stop]])
        published_means = np.asarray([rows[stop][a], rows[stop][p]])
        difference = pair[:, 1]-pair[:, 0]
        groups[name] = {
            "n_embryos": len(pair), "anterior_um": float(pair[:,0].mean()),
            "posterior_um": float(pair[:,1].mean()),
            "within_embryo_posterior_minus_anterior_um": difference.tolist(),
            "mean_P_minus_A_um": float(difference.mean()),
            "author_mean_row_max_abs_difference": float(np.max(np.abs(pair.mean(axis=0)-published_means))),
        }
    key = "within_embryo_posterior_minus_anterior_um"
    return {"groups": groups, "change_in_anterior_posterior_difference": contrast(
        groups["NC ablation"][key], groups["control"][key], rng
    )}


def run(raw, out):
    books = read_books(raw / "kv_archive.zip")
    rng = np.random.default_rng(SEED)
    shape = analyse_observations(books["lumen-shape-data-experiments.xlsx"], (5.,6.,7.), rng)
    speed = analyse_observations(books["lumen-speed-data-experiments.xlsx"], (5.5,6.5), rng)
    shape["model_direction"] = model_directions(books["lumen-shape-data-simulation.xlsx"],shape)
    speed["model_direction"] = model_directions(books["lumen-speed-data-simulation.xlsx"],speed)
    widths = apical_width(books["KV_cell_apical_width_data_Fig_4C-D.xlsx"],rng)
    report = {
        "experiment": "E42", "study_doi": "10.1073/pnas.2418111122", "archive_doi": "10.5061/dryad.w9ghx3g2h",
        "source_url": URL, "workbook_sha256": BOOKS, "stage_window": [5,7],
        "replicates": BOOTSTRAPS, "rng_seed": SEED, "resample_unit": "embryo within each treatment",
        "shape_AP_to_LR_ratio": shape, "lumen_center_speed_um_per_min": speed,
        "apical_widths": widths,
        "checks": {
            "all_four_perturbation_groups": all(set(a["groups"]) == set(GROUPS) for a in (shape,speed)),
            "no_more_complete_embryos_than_included": all(
                b["complete_case_count"] <= b["n_embryos"] for a in (shape,speed) for b in a["groups"].values()
            ),
            "apical_width_pairs_and_summary_rows": (
                [x["n_embryos"] for x in widths["groups"].values()] == [15,21]
                and max(x["author_mean_row_max_abs_difference"] for x in widths["groups"].values()) < 1e-8
            ),
            "published_models_include_both_perturbations": all(
                set(a["model_direction"]["comparison"]) == {"NC ablation","PC ablation"} for a in (shape,speed)
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, default=ROOT / "research/results/E42")
    args = parser.parse_args()
    run(args.raw, args.out)
