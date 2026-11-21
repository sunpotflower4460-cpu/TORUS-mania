"""Check whether labeled free IAA appears after a labeled conjugate input."""

import itertools
from io import BytesIO

import numpy as np
from openpyxl import load_workbook
from scipy.stats import ttest_ind

from experiments import particle_return_sources as sources
from experiments.common import save_summary


def data_from_sheet(data):
    with BytesIO(data) as stream:
        book = load_workbook(stream, read_only=True, data_only=True)
        try:
            sheet = book["Fig.3b"]
            return list(sheet.iter_rows(max_row=21, max_col=7, values_only=True))
        finally:
            book.close()


def analyze(rows, offset):
    header, genotypes = rows[offset + 2 : offset + 4]
    if genotypes[5:7] != ("WT", "ilr1ill2iar3ill3") or rows[offset + 4][1] != "pmol/g.Fresh weight":
        raise ValueError("Unexpected source data labels or units")
    values = np.asarray([row[5:7] for row in rows[offset + 4 : offset + 8]], dtype=float).T
    control, mutant = values
    reported = rows[offset + 8][5:7]
    reported_p = float(rows[offset + 10][5].split("=")[-1])
    means = values.mean(axis=1)
    exact, observed = [], abs(means[0] - means[1])
    joined = values.ravel()
    for selected in itertools.combinations(range(8), 4):
        group = np.zeros(8, dtype=bool)
        group[list(selected)] = True
        exact.append(abs(joined[group].mean() - joined[~group].mean()))
    return {
        "source_sheet_label": header[5],
        "fresh_weight_unit_pmol_per_g": True,
        "printed_first_row_one_based": offset + 5,
        "wt_then_mutant_samples": values.tolist(),
        "wt_then_mutant_means": means.tolist(),
        "wt_then_mutant_sd": values.std(axis=1, ddof=1).tolist(),
        "wt_then_mutant_reported_means": list(reported),
        "mutant_over_wt": float(means[1] / means[0]),
        "student_p_two_sided": float(ttest_ind(control, mutant).pvalue),
        "printed_student_p_two_sided": reported_p,
        "permutation_assignments": len(exact),
        "p_two_sided_exchangeable_labels": float(np.mean(np.asarray(exact) >= observed - 1e-8)),
        "nonoverlapping_measurements": bool(control.min() > mutant.max() or mutant.min() > control.max()),
    }


def run(raw, out):
    rows = data_from_sheet(sources.read(raw, "hayashi-source.xlsx"))
    conjugated = analyze(rows, 0)
    free = analyze(rows, 10)
    f = np.array(free["wt_then_mutant_means"])
    c = np.array(conjugated["wt_then_mutant_means"])
    summary = {
        "experiment": "E60",
        "doi": "10.1038/s41467-021-27020-1",
        "source_figure": "3b",
        "hours_after_input": 6,
        "conjugated_D2_IAA_Asp": conjugated,
        "released_free_D2_IAA": free,
        "free_share_of_two_group_means": (f / (f + c)).tolist(),
        "scope": "The supplied labeled IAA–Asp dimethyl ester is distinct from free IAA. The share uses two measured pools and their group means; rows have no sample identifiers that establish cross-metabolite pairing.",
        "checks": {
            "published_sheet_groups_and_sample_counts": len(conjugated["wt_then_mutant_samples"][0])
            == len(conjugated["wt_then_mutant_samples"][1])
            == len(free["wt_then_mutant_samples"][0])
            == len(free["wt_then_mutant_samples"][1])
            == 4,
            "published_header_matches_both_chemical_species": conjugated["source_sheet_label"]
            == "D2-IAA-Asp"
            and free["source_sheet_label"] == "D2-IAA",
            "printed_and_recomputed_means_agree": all(
                np.allclose(
                    panel["wt_then_mutant_means"],
                    panel["wt_then_mutant_reported_means"],
                    atol=1e-10,
                    rtol=0,
                )
                for panel in (free, conjugated)
            ),
            "all_four_by_four_allocations": free["permutation_assignments"] == 70,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
