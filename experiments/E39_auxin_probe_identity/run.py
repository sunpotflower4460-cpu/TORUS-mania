"""Read separate chemical species in the published FluorA root assay."""

import argparse
from pathlib import Path

import fitz
import numpy as np

from experiments import return_energy_data as data
from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/path_and_formation"
URL = "https://eprints.whiterose.ac.uk/id/eprint/172333/7/nph.17183%20%281%29.pdf"
SHA = "41deaad34df8776a6bfa40151b5089ec066ecfd5016c83290b5b21897df7a98a"
# Coordinates on the five-times render of Fig. 2a and 2b. The open square
# is free 2,4-D, while a filled diamond or triangle is the parent tracer.
CLIP = (125, 55, 487, 174)
TICK_ROWS = (458.5, 101.)
POSITIONS = {
    "FluorA_I": {"parent_tracer": (260.5, 246., 258., 244.5), "free_2_4_D": (456., 452.5, 452., 445.5)},
    "FluorA_II": {"parent_tracer": (304., 275., 226.5, 154.5), "free_2_4_D": (452.5, 454., 448.5, 441.)},
}
TIMES = np.array([.5, 1., 2., 3.])
READING_WIDTH_PX = 3.


def chemical_points(figure):
    scale = 600. / (TICK_ROWS[0] - TICK_ROWS[1])
    width = READING_WIDTH_PX * scale
    result = {}
    for name, positions in POSITIONS.items():
        for y in positions.values():
            if not all(0 < row < figure.height for row in y):
                raise ValueError(f"Marker is outside the original graph: {name}")
        parent, free = [
            np.maximum(0, (TICK_ROWS[0] - np.array(y)) * scale)
            for y in positions.values()
        ]
        slope = float((TIMES @ free) / (TIMES @ TIMES))
        slope_width = float(width * TIMES.sum() / (TIMES @ TIMES))
        shares = free/(parent+free)
        last_lo = max(free[-1]-width, 0) / (parent[-1]+free[-1])
        last_hi = (free[-1]+width) / (parent[-1]+free[-1])
        result[name] = {
            "parent_pmol_per_50_roots": parent.tolist(),
            "free_2_4_D_pmol_per_50_roots": free.tolist(),
            "free_fraction_of_two_measured_species": shares.tolist(),
            "free_fraction_at_3h_pixel_reading_range": [float(last_lo), float(last_hi)],
            "slope_pmol_per_50_roots_per_h_through_origin": slope,
            "slope_reading_half_width": slope_width,
            "estimated_free_pmol_per_50_roots_at_15_min": .25*slope,
            "estimate_reading_half_width_at_15_min": .25*slope_width,
        }
    return result, width


def run(raw, out):
    source = data.verified(raw/"fluora.pdf", SHA)
    with fitz.open(stream=source, filetype="pdf") as pdf:
        page = pdf[5]
        if "Biological activity of FluorAs is driven by metabolisation in vivo" not in page.get_text():
            raise ValueError("Unexpected page for original tracer figure")
        face = page.get_pixmap(matrix=fitz.Matrix(5,5), clip=fitz.Rect(*CLIP), alpha=False)
    series, width = chemical_points(face)
    report = {
        "experiment": "E39", "study_doi": "10.1111/nph.17183",
        "source": {"url": URL, "sha256": SHA},
        "figure": "Fig. 2a,b", "pixel_clipping_pdf_points": CLIP, "pixel_y_axis_zero_and_600": TICK_ROWS,
        "pixel_marker_rows": POSITIONS, "times_h_at_plotted_nonzero_times": TIMES.tolist(),
        "one_marker_reading_half_width_pmol_per_50_roots": width,
        "per_probe_results": series,
        "reported_15_min_free_2_4_D_estimate_pmol_per_50_roots": 2.7,
        "interpreting_probe": "Parents are fluorescent derivatives of 2,4-D, not native IAA. Root extracts have no tissue history.",
        "checks": {
            "registered_axes_and_original_scale": (face.width, face.height) == (1810, 595),
            "all_four_positive_plot_times_extracted": all(
                len(x["free_2_4_D_pmol_per_50_roots"]) == 4 for x in series.values()
            ),
            "chemical_share_gives_bounded_fraction": all(
                all(0 <= fraction <= 1 for fraction in x["free_fraction_of_two_measured_species"])
                for x in series.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, data.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E39")
    args = parser.parse_args()
    run(args.raw, args.out)
