"""Score published individual embryo angles against the later signed size asymmetry."""

import fitz
import numpy as np
from scipy.stats import binomtest, fisher_exact

from experiments import turning_path_sources as sources
from experiments.common import save_summary

# Endpoints of the printed vector ticks in Fig. 5c, in PDF points.
X0, X150 = 75.834, 284.554
Y0, Y1 = 325.616, 299.553


def marker_centers(page):
    centers = []
    for path in page.get_drawings():
        rect = path["rect"]
        if path["type"] != "s" or rect.x0 < 73 or rect.x1 > 285 or rect.y0 < 286 or rect.y1 > 365:
            continue
        if path["color"] != (0.0, 0.0, 0.0):
            continue
        points = []
        for item in path["items"]:
            if item[0] != "l":
                points = []
                continue
            start, stop = item[1:]
            if not points or abs(start - points[-1]) > 0.01:
                points = [start]
            points.append(stop)
            if len(points) > 3 and abs(points[-1] - points[0]) < 0.01:
                xy = np.array([[p.x, p.y] for p in points[:-1]])
                width, height = np.ptp(xy, axis=0)
                if len(xy) >= 8 and 2.5 < width < 3.2 and 2.5 < height < 3.2:
                    center = (xy.min(0) + xy.max(0)) / 2
                    centers.append((float(center[0]), float(center[1]), float(width)))
                points = []
    return sorted(centers)


def interval(hits, n):
    ci = binomtest(hits, n).proportion_ci(method="exact")
    return [float(ci.low), float(ci.high)]


def run(raw, out):
    with fitz.open(stream=sources.read(raw, "mittasch.pdf"), filetype="pdf") as paper:
        page = paper[4]
        if not page.search_for("cell-size ratio"):
            raise ValueError("Did not find printed endpoint on requested page")
        markers = marker_centers(page)
    rows = []
    for x, y, width in markers:
        angle = (x - X0) * 150 / (X150 - X0)
        index = (Y0 - y) / (Y0 - Y1)
        rows.append(
            {
                "angle_deg": angle,
                "size_asymmetry_index": index,
                "center_xy_points": [x, y],
                "marker_half_width_deg": width * 75 / (X150 - X0),
                "inverted": index < 0,
            }
        )
    below = [r for r in rows if r["angle_deg"] < 90]
    above = [r for r in rows if r["angle_deg"] >= 90]
    normal, inverted = sum(not r["inverted"] for r in below), sum(r["inverted"] for r in above)
    contingency = [[normal, len(below) - normal], [len(above) - inverted, inverted]]
    sensitivity = {
        str(t): sum((r["angle_deg"] >= t) == r["inverted"] for r in rows)
        for t in (80, 85, 87.5, 90, 95, 100, 110)
    }
    gap = [
        max(r["angle_deg"] for r in rows if not r["inverted"]),
        min(r["angle_deg"] for r in rows if r["inverted"]),
    ]
    summary = {
        "experiment": "E52",
        "doi": "10.1038/s41556-017-0032-9",
        "printed_figure": "5c, hollow markers",
        "axis_ticks_pdf_points": {"x_0_150": [X0, X150], "y_0_1": [Y0, Y1]},
        "embryos": rows,
        "below90_normal_total": [normal, len(below)],
        "atleast90_inverted_total": [inverted, len(above)],
        "class_specific_exact_95": {
            "below_normal": interval(normal, len(below)),
            "above_inverted": interval(inverted, len(above)),
        },
        "always_initial_correct": sum(not r["inverted"] for r in rows),
        "always_majority_correct": max(
            sum(r["inverted"] for r in rows), sum(not r["inverted"] for r in rows)
        ),
        "angle_threshold_correct": sensitivity,
        "gap_max_normal_min_inverted_deg": gap,
        "within_marker_half_width_of_90": sum(
            abs(r["angle_deg"] - 90) <= r["marker_half_width_deg"] for r in rows
        ),
        "fisher_two_sided_descriptive": float(fisher_exact(contingency).pvalue),
        "scope": "Known threshold from this study. Existing PAR domains were moved during maintenance before cytokinesis.",
        "checks": {
            "published_number_of_independent_perturbed_embryos": len(rows) == 12,
            "published_angle_group_sizes": len(below) == 9 and len(above) == 3,
            "no_unperturbed_filled_marker_in_sample": min(r["angle_deg"] for r in rows) > 1,
            "signed_index_in_axis_range": all(-1.5 < r["size_asymmetry_index"] < 1.5 for r in rows),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
