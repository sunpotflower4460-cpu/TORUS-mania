"""Read tissue-interruption and receiver chromatogram data from Vicia roots."""

import argparse
from pathlib import Path

import fitz
import numpy as np

from experiments import measured_return_sources as sources
from experiments.common import save_summary


# Pixel coordinates on the 3x crop of Fig. 8. A is tipward (filled), B shootward (open).
TIMES = [0, 1, 2, 3, 5]
MARKERS = {
    "control": {"x": [281, 355, 429, 501, 650], "tipward": [470, 455, 375, 303, 231],
                "shootward": [470, 430, 390, 391, 347]},
    "central_wire": {"x": [724, 797, 872, 945, 1092], "tipward": [470, 458, 434, 426, 389],
                     "shootward": [470, 426, 383, 347, 326]},
}


def grayscale(page, scale, clip=None):
    view = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, colorspace=fitz.csGRAY, alpha=False)
    return np.frombuffer(view.samples, dtype=np.uint8).reshape(view.height, view.width)


def wire_comparison(page):
    crop = (105, 93, 490, 290)
    image = grayscale(page, 3, fitz.Rect(*crop))
    scale = 200 / (470.5 - 221)
    delta = 3 * scale
    concentrations = {}
    for group, positions in MARKERS.items():
        curves = {}
        for direction in ("tipward", "shootward"):
            rows = positions[direction]
            for x, y in zip(positions["x"], rows):
                if np.count_nonzero(image[y-7:y+8, x-7:x+8] < 100) < 14:
                    raise ValueError(f"Missing marker in {group}, {direction} at ({x}, {y})")
            curves[direction] = [0.] + [(470.5 - y) * scale for y in rows[1:]]
        concentrations[group] = curves
    relative = {}
    for direction in ("tipward", "shootward"):
        control = np.array(concentrations["control"][direction][1:])
        wire = np.array(concentrations["central_wire"][direction][1:])
        relative[direction] = {
            "wire_over_control": (wire / control).tolist(),
            "last_ratio_reading_bounds": [(wire[-1]-delta)/(control[-1]+delta),
                                          (wire[-1]+delta)/(control[-1]-delta)],
        }
    return {
        "times_h": TIMES, "tissue": "3-mm excised section, 3–6 mm from the tip",
        "crop_pdf_points": crop, "render_scale": 3, "zero_and_200_dpm_rows": [470.5, 221],
        "read_markers_px": MARKERS, "point_reading_halfwidth_dpm": delta, "receiver_dpm": concentrations,
        "nonzero_time_ratios": relative,
    }


def chromatograms(page):
    pixels = grayscale(page, 1.7)
    results = {}
    for direction, left, right, start in (("tipward", 352., 492., 320), ("shootward", 534., 675., 245)):
        centers = np.rint(left + (np.arange(10) + 0.5) * (right-left) / 10).astype(int)
        rows = []
        for x in centers:
            stripe = pixels[start:412, x-3:x+4]
            ink = np.where(np.median(stripe, axis=1) < 153)[0]
            if not ink.size:
                raise ValueError(f"Missing TLC histogram line at x={x}")
            rows.append(int(start + ink[0]))
        values = np.maximum(0, (410 - np.array(rows)) * (20/57))
        results[direction] = {
            "centers_px": centers.tolist(), "top_rows": rows, "counts_dpm": values.tolist(),
            "sum_dpm": float(values.sum()),
            "fraction_at_Rf_0p5_to_0p7": float(values[5:7].sum()/values.sum()),
        }
    return {
        "source": "Fig. 3, pooled receivers, 4 h after a surface application, 10 equal Rf bins",
        "scale": 1.7, "zero_and_20_dpm_rows": [410, 353], "reading_halfwidth_per_bin_dpm": 2*20/57,
        "directions": results,
        "shootward_over_tipward_recovered": results["shootward"]["sum_dpm"]/results["tipward"]["sum_dpm"],
        "paper_recovery_fraction": .72, "paper_approximate_IAA_comigration_fraction": .8,
    }


def run(raw, out):
    with fitz.open(stream=sources.read(raw, "vicia76.pdf"), filetype="pdf") as pdf:
        if len(pdf) != 14:
            raise ValueError("Unexpected intact-root publication")
    with fitz.open(stream=sources.read(raw, "vicia78.pdf"), filetype="pdf") as pdf:
        wire = wire_comparison(pdf[7])
        tlc = chromatograms(pdf[4])
    # Reported distances from Fig. 4/text (1976), using the same surface donor region.
    times = np.array([10, 30, 60])
    tipward = np.array([1, 2, 4])
    shootward = np.array([2, 4, 8])
    report = {
        "experiment": "E44", "dois": ["10.1093/oxfordjournals.pcp.a075396", "10.1093/oxfordjournals.pcp.a075700"],
        "intact_root": {
            "donor_mm_from_tip": [4, 5], "time_min": times.tolist(), "tipward_front_mm": tipward.tolist(),
            "shootward_front_mm": shootward.tolist(), "distance_ratio": (shootward/tipward).tolist(),
            "fig7_localization": "20 min: basal outer tissue and weaker apical inner tissue; basal inner signal also seen at 30 min.",
            "chemical_scope": "Spatial signal is 14C. Intact-root study did not identify the metabolite in those sections.",
        },
        "wire_fig8": wire, "receiver_TLC_fig3": tlc,
        "checks": {
            "intact_fig4_three_times_and_two_fronts": len(tipward) == len(shootward) == len(times),
            "all_fig8_timepoints_and_groups": all(len(curve) == len(TIMES) for group in wire["receiver_dpm"].values() for curve in group.values()),
            "ten_TLC_bins_each_way": all(len(curve["top_rows"]) == 10 for curve in tlc["directions"].values()),
            "digitized_chromatogram_ratio_near_reported_2p7": abs(tlc["shootward_over_tipward_recovered"]-2.7) < .4,
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
