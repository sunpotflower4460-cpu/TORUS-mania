"""Compare auxinole effects with seedlings as the resampling unit."""

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import io
from pathlib import Path
from zipfile import ZipFile

import numpy as np

from experiments import return_energy_data as data
from experiments.common import save_summary

URL = "https://datadryad.org/api/v2/versions/443502/download"
CSV_FILES = {
    "SourceData1a_LRdvp_LRlevel_dryad.csv": "d1ad3c16382cd944896587933d638e152b4b5a0c8369ae342a70330b06a8b3b9",
    "SourceData1b_LRdvp_seedlinglevel_dryad.csv": "5671a838ccad67aa236a68f189955b08255c2e2292057cfcef044961d59fc0ad",
}
LINES = {"transcriptional": "pGATA23mScarlet", "integrase": "444 GATA23"}
ITERATIONS = 4000
SEED = 382026
ENDPOINTS = ("mean", "sd")


def read_tables(archive):
    with ZipFile(archive) as files:
        for name, digest in CSV_FILES.items():
            content = files.read(name)
            if sha256(content).hexdigest() != digest:
                raise ValueError(f"Changed accession file: {name}")
            yield list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline="")))


def root_key(row):
    return (row["reporter construct"], float(row["auxinole concentration (uM)"]),
            int(float(row["sequential replicate"])), int(row["seedling number (sequential)"]))


def seedling_key(row):
    return (row["line"], float(row["auxinole conc"]),
            int(row["sequential replicate"]), int(row["seedling (sequential)"]))


def audit_organs(roots, plants):
    counts = defaultdict(Counter)
    stages = defaultdict(list)
    for row in roots:
        key = root_key(row)
        if key[0] not in LINES.values():
            continue
        if key not in plants:
            raise ValueError(f"Organs are missing their seedling entry: {key}")
        stage = row["LR stage"]
        counts[key][stage] += 1
        if stage in ("1", "2"):
            stages[stage, key].append(int(row["number of cells"]))
    differences = []
    for key, seedling in plants.items():
        archived = [int(float(seedling[f"stage {i} LRs"])) for i in (1, 2)]
        rebuilt = [counts[key][str(i)] for i in (1, 2)]
        if rebuilt != archived:
            differences.append({
                "seedling_key": key, "root_table_stage_1_and_2": rebuilt,
                "seedling_table_stage_1_and_2": archived,
            })
    return stages, differences


def summarize_sample(clusters):
    eligible = [cluster for cluster in clusters if len(cluster)]
    values = np.concatenate(eligible)
    return {
        "organs": len(values), "seedlings_with_stage": len(eligible), "seedlings_in_group": len(clusters),
        "mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1)),
        "median": float(np.median(values)), "equal_seedling_weight_mean": float(
            np.mean([np.mean(c) for c in eligible])
        ),
    }


def grouped_bootstrap(clusters, rng):
    sampled = np.zeros((ITERATIONS, 3))
    for replicate in clusters.values():
        sufficient_stats = np.array([(len(a), sum(a), sum(x*x for x in a)) for a in replicate])
        n = len(replicate)
        resampled = rng.integers(0, n, (ITERATIONS, n))
        sampled += sufficient_stats[resampled].sum(axis=1)
    n, total, squared = sampled.T
    if np.any(n < 2):
        raise ValueError("At least two organs are required to bootstrap the SD")
    return {"mean": total / n, "sd": np.sqrt(np.maximum(0., (squared - total**2/n)/(n-1)))}


def contrast(observed, draws):
    difference = observed[1] - observed[0]
    return {"treated_minus_control": difference, "cluster_percentile_interval_95": np.quantile(draws, [.025, .975]).tolist()}


def measure_stage(records, dose, stage, rng, bootstrap=True):
    results = {}
    treatment_draws = {}
    for reporter, line in LINES.items():
        groups = [defaultdict(list), defaultdict(list)]
        for key, organs in records.items():
            if key[0] == line and key[1] in (0., dose):
                groups[int(key[1] == dose)][key[2]].append(organs)
        stats = [summarize_sample([x for replicate in g.values() for x in replicate]) for g in groups]
        differences = {name: stats[1][name] - stats[0][name] for name in ENDPOINTS}
        result = {"control": stats[0], "auxinole": stats[1], "differences": differences}
        if bootstrap:
            control, treatment = [grouped_bootstrap(g, rng) for g in groups]
            treatment_draws[reporter] = {name: treatment[name] - control[name] for name in ENDPOINTS}
            result["bootstrap"] = {
                name: contrast([stats[0][name], stats[1][name]], treatment_draws[reporter][name])
                for name in ENDPOINTS
            }
        results[reporter] = result
    comparison = {}
    for name in ENDPOINTS:
        effects = [results[r]["differences"][name] for r in ("integrase", "transcriptional")]
        if bootstrap:
            draws = treatment_draws["transcriptional"][name] - treatment_draws["integrase"][name]
            comparison[name] = contrast(effects, draws)
        else:
            comparison[name] = effects[1] - effects[0]
    return {"stage": stage, "reporters": results, "transcriptional_minus_integrase_treatment_effect": comparison}


def seedling_outcomes(plants, dose):
    columns = ("main root length (cm)", "total LRs", "emerged LRs", "emerged LR density")
    rows = {}
    for reporter, line in LINES.items():
        endpoints = {}
        for treatment in (0., dose):
            group = [value for key, value in plants.items() if key[:2] == (line, treatment)]
            endpoints[str(treatment)] = {"seedlings": len(group), **{
                name: float(np.mean([float(row[name]) for row in group])) for name in columns
            }}
        rows[reporter] = endpoints
    return rows


def run(raw, out):
    roots, whole_plants = read_tables(raw/"dry_files_zip.zip")
    plants = {seedling_key(row): row for row in whole_plants if row["line"] in LINES.values()}
    if len(plants) != sum(row["line"] in LINES.values() for row in whole_plants):
        raise ValueError("Duplicated seedling key")
    stages, discrepancies = audit_organs(roots, plants)
    conflicting = {row["seedling_key"] for row in discrepancies}
    common_doses = set.intersection(*[{k[1] for k in plants if k[0] == line} for line in LINES.values()])
    dose = max(common_doses - {0.})
    rng = np.random.default_rng(SEED)
    output = {}
    for stage in ("1", "2"):
        eligible = {key: stages[stage, key] for key in plants}
        output[stage] = {
            "all_labelled_organs": measure_stage(eligible, dose, stage, rng),
            "excluding_seedlings_with_inconsistent_stage_counts": measure_stage(
                {k: v for k, v in eligible.items() if k not in conflicting}, dose, stage, rng, bootstrap=False
            ),
        }
    summary = {
        "experiment": "E38", "study_doi": "10.1093/genetics/iyag120", "data_doi": "10.5061/dryad.g4f4qrg51",
        "accession_download": URL, "accession_file_hashes": CSV_FILES,
        "all_csv_organ_rows": len(roots), "all_csv_seedling_rows": len(whole_plants),
        "included_seedlings": len(plants), "shared_auxinole_dose_uM": dose,
        "random_seed": SEED, "bootstrap_iterations": ITERATIONS,
        "stage_count_audit_differences": discrepancies, "stages": output,
        "seedling_outcomes": seedling_outcomes(plants, dose),
        "checks": {
            "all_early_stage_records_have_matching_seedling": sum(len(x) for x in stages.values()) == sum(
                row["reporter construct"] in LINES.values() and row["LR stage"] in ("1", "2") for row in roots
            ),
            "every_group_uses_two_cell_counting_batches": all(
                {k[2] for k in plants if k[:2] == (line, treatment)} == {1, 2}
                for line in LINES.values() for treatment in (0., dose)
            ),
            "same_reporters_at_each_stage": all(
                set(x["all_labelled_organs"]["reporters"]) == set(LINES) for x in output.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=data.RAW)
    parser.add_argument("--out", type=Path, default=data.RESULTS/"E38")
    args = parser.parse_args()
    run(args.raw, args.out)
