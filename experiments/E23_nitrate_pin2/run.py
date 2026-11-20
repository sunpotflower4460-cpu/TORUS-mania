"""Reconstruct the nutrient contrasts from the public Fig. 6 and 7 workbooks."""

import argparse
from hashlib import sha256
from pathlib import Path
from statistics import mean, median, quantiles

from openpyxl import load_workbook

from experiments.common import save_summary


PMC = "https://pmc-oa-opendata.s3.amazonaws.com/PMC8447600.1/"
SOURCES = {
    "fig6": {
        "name": "EMBR-22-e51813-s007.xlsx",
        "sha256": "09de3fad8b5500c98a1937aeecba985764079c42520a339a8046df12e6fcd853",
        "sheets": ("Figure 6a", "Figure 6b"),
        "genotypes": ("Col-0", "eir1-1"),
        "reference": "Col-0",
    },
    "fig7": {
        "name": "EMBR-22-e51813-s002.xlsx",
        "sha256": "25dd877c41ecd286eee3877f54aca2442d0f674fa9535c69d6330135dc8ef12e",
        "sheets": ("Figure 7A", "Figure 7B"),
        "genotypes": ("Col-0", "PIN2wt", "PIN2S439D", "PIN2S439A"),
        "reference": "PIN2wt",
    },
}
REPLICATES = ("R1", "R2", "R3")
TREATMENTS = ("KCl", "KNO3")
UNITS = {"primary_length_mm": "mm", "density_per_cm": "roots and primordia/cm",
         "implied_count": "roots and primordia/plant"}
COUNT_TOLERANCE = 1e-8


def observations(sheet, genotypes):
    """Preserve positions within each replicate, including blank cells."""
    read_genotypes = tuple(sheet.cell(3, 2 + 3*i).value for i in range(len(genotypes)))
    if read_genotypes != genotypes:
        raise ValueError(f"Unexpected genotypes in {sheet.title}: {read_genotypes}")
    end = 1 + 3*len(genotypes)
    headers = next(sheet.iter_rows(min_row=4, max_row=4, max_col=end, values_only=True))[1:]
    if headers != ("Time 0", "3d KCl", "3d KNO3") * len(genotypes):
        raise ValueError(f"Unexpected treatment headers in {sheet.title}")
    groups = {name: {} for name in genotypes}
    seen = []
    for row in sheet.iter_rows(min_row=5, max_col=end, values_only=True):
        label = row[0]
        if label == "Average":
            break
        if label in REPLICATES:
            seen.append(label)
            for group in groups.values():
                group[label] = {condition: [] for condition in TREATMENTS}
        elif label is not None:
            raise ValueError(f"Unexpected row label in {sheet.title}: {label}")
        for i, genotype in enumerate(genotypes):
            for j, condition in enumerate(TREATMENTS):
                value = row[3*i + 2 + j]
                if value is not None and not isinstance(value, (int, float)):
                    raise ValueError(f"Unexpected measurement in {sheet.title}: {value}")
                groups[genotype][seen[-1]][condition].append(value)
    if tuple(seen) != REPLICATES:
        raise ValueError(f"Unexpected replicate labels in {sheet.title}: {seen}")
    return groups


def summary(values):
    observed = [value for value in values if value is not None]
    low, _, high = quantiles(observed, n=4, method="inclusive")
    return {"n": len(observed), "mean": mean(observed), "median": median(observed), "IQR": [low, high]}


def measure(groups, reference, unit):
    output = {"units": unit, "groups": {}}
    for genotype, group in groups.items():
        by_repeat = {label: {t: summary(values) for t, values in repeat.items()}
                     for label, repeat in group.items()}
        pooled = {t: summary([value for repeat in group.values() for value in repeat[t]])
                  for t in TREATMENTS}
        changes = {label: repeat["KNO3"]["mean"] - repeat["KCl"]["mean"]
                   for label, repeat in by_repeat.items()}
        output["groups"][genotype] = {"pooled": pooled, "by_replicate": by_repeat,
                                     "KNO3_minus_KCl_by_replicate": changes,
                                     "pooled_contrast": pooled["KNO3"]["mean"] - pooled["KCl"]["mean"],
                                     "equal_replicate_contrast": mean(changes.values())}
    contrasts = {}
    if reference in groups:
        base = output["groups"][reference]["KNO3_minus_KCl_by_replicate"]
        for genotype, result in output["groups"].items():
            if genotype == reference:
                continue
            interaction = {r: base[r] - result["KNO3_minus_KCl_by_replicate"][r] for r in REPLICATES}
            contrasts[genotype] = {
                "reference_minus_genotype_by_replicate": interaction,
                "equal_replicate_contrast": mean(interaction.values()),
                "leave_one_replicate_out": {leave: mean(v for r, v in interaction.items() if r != leave)
                                            for leave in REPLICATES},
            }
    output["reference"] = reference
    output["interaction_with_reference"] = contrasts
    return output


def count_audit(lengths, densities):
    """Screen within-replicate row alignment using density × primary length."""
    eligible = {}
    audit = {}
    for genotype, groups in lengths.items():
        inferred = {rep: {} for rep in REPLICATES}
        audit[genotype] = {"replicates": {}}
        for replicate, group in groups.items():
            rows = {}
            for condition in TREATMENTS:
                length = group[condition]
                density = densities[genotype][replicate][condition]
                products = [x*y/10 for x, y in zip(length, density) if x is not None and y is not None]
                errors = [abs(x-round(x)) for x in products]
                n_length = sum(v is not None for v in length)
                n_density = sum(v is not None for v in density)
                valid = sum(error <= COUNT_TOLERANCE for error in errors)
                consistent = len(products) == min(n_length, n_density) and valid == len(products)
                rows[condition] = {"n_length": n_length, "n_density": n_density, "n_aligned": len(products),
                                   "n_integer_consistent": valid, "maximum_integer_error": max(errors),
                                   "consistent": consistent}
                if consistent:
                    inferred[replicate][condition] = [round(value) for value in products]
            audit[genotype]["replicates"][replicate] = rows
        all_consistent = all(len(group) == len(TREATMENTS) for group in inferred.values())
        audit[genotype]["consistent_in_all_treatment_blocks"] = all_consistent
        if all_consistent:
            eligible[genotype] = inferred
    return eligible, audit


def reanalyse(raw):
    findings = {}
    for figure, source in SOURCES.items():
        path = raw / source["name"]
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != source["sha256"]:
            raise ValueError(f"Source data do not match the registered archive version: {path} ({digest})")
        book = load_workbook(path, data_only=True)
        a, b = source["sheets"]
        lengths, densities = (observations(book[name], source["genotypes"]) for name in (a, b))
        book.close()
        counts, audit = count_audit(lengths, densities)
        findings[figure] = {
            "source": {"url": PMC + source["name"], "sha256": digest, "sheets": source["sheets"]},
            "primary_length_mm": measure(lengths, source["reference"], UNITS["primary_length_mm"]),
            "density_per_cm": measure(densities, source["reference"], UNITS["density_per_cm"]),
            "implied_count": measure(counts, source["reference"], UNITS["implied_count"]),
            "length_density_row_alignment": audit,
        }
    return findings


def run(raw, out):
    findings = reanalyse(raw)
    fig6, fig7 = findings["fig6"], findings["fig7"]
    checks = {
        "source_Fig6_WT_density_group_sizes": all(v["n"] == 39 for v in fig6["density_per_cm"]["groups"]["Col-0"]["pooled"].values()),
        "source_Fig7_PIN2wt_density_group_sizes": all(v["n"] == 24 for v in fig7["density_per_cm"]["groups"]["PIN2wt"]["pooled"].values()),
        "Fig6_inferred_counts_have_30_observations_per_group": all(
            v["n"] == 30 for group in fig6["implied_count"]["groups"].values() for v in group["pooled"].values())
            and tuple(fig6["implied_count"]["groups"]) == SOURCES["fig6"]["genotypes"],
        "Fig7_inconsistent_row_matches_excluded_from_count_summary": tuple(fig7["implied_count"]["groups"]) == ("Col-0", "PIN2wt"),
    }
    record = {"experiment": "E23", "study_DOI": "10.15252/embr.202051813", "concentration_mM": 5,
              "days_after_treatment": 3, "replicate_labels": REPLICATES,
              "independent_biological_repeats_per_condition": 3,
              "count_rule": {"method": "Multiply position-matched length in cm and density per cm within each labelled repeat. Include a genotype if every treatment block aligns all rows of the smaller sample and every product is integer-consistent. The archive lacks specimen identifiers.",
                             "tolerance_count_units": COUNT_TOLERANCE},
              "figures": findings, "checks": checks}
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, record, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/auxin"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw, args.out)
