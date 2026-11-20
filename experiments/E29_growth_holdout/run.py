"""Freeze low-production fits before reading the high-production figure panels."""

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy.ndimage import center_of_mass, distance_transform_edt, label, maximum_filter
from scipy.optimize import least_squares

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
PDF_URL = "https://dspace.library.uu.nl/bitstream/handle/1874/413557/1_s2.0_S153458072100561X_main.pdf?sequence=1"
PDF_SHA256 = "04905086dc09cd7bd03deda7a9123e31914e869ee398e8e1c665340f81708196"
PDF_PAGE = 12
SPLIT = 2.0
GUARD = .03
# Box in figure pixels, then the centres and values of two printed x and y ticks.
PANELS = {
    "frequency": ((111, 42, 684, 468), ((159.5, 1.25), (627.5, 3.0)), ((444.5, .2), (62.5, 1.0))),
    "spacing": ((803, 40, 1376, 466), ((852., 1.25), (1319.5, 3.0)), ((446., 1.), (41., 8.))),
}


def axis(points):
    (pix0, val0), (pix1, val1) = points
    slope = (val1-val0)/(pix1-pix0)
    return slope, val0-slope*pix0


def figure(path):
    if sha256(path.read_bytes()).hexdigest() != PDF_SHA256:
        raise ValueError(f"Unexpected PDF version: {path}")
    with fitz.open(path) as pdf:
        [entry] = pdf[PDF_PAGE].get_images()
        raster = pdf.extract_image(entry[0])["image"]
    with Image.open(io.BytesIO(raster)) as im:
        return im.convert("RGB")


def read_points(image, partition):
    out = {}
    for metric, (box, xticks, yticks) in PANELS.items():
        px, x0 = axis(xticks)
        py, y0 = axis(yticks)
        left, top, right, bottom = box
        split_x = round((SPLIT-x0)/px)
        if partition == "training":
            right = split_x
        else:
            left = split_x
        rgb = np.asarray(image.crop((left, top, right, bottom)), dtype=np.int16)
        r, g, b = rgb.transpose(2, 0, 1)
        blue = (b > 120) & (b-r > 100) & (b-g > 90)
        # A marker has a thicker interior than the blue regression curves.
        distance = distance_transform_edt(blue)
        peaks = (distance >= 4.) & (distance == maximum_filter(distance, size=7))
        labels, count = label(peaks, np.ones((3, 3), dtype=int))
        points = []
        kept = []
        if count:
            centres = center_of_mass(peaks, labels, list(range(1, count+1)))
            strongest_first = sorted(centres, key=lambda c: (-distance[round(c[0]), round(c[1])], *c))
            for y, x in strongest_first:
                if any((y-prev_y)**2+(x-prev_x)**2 < 36. for prev_y, prev_x in kept):
                    continue
                kept.append((y, x))
                p = x0+px*(left+x)
                if (partition == "training" and p < SPLIT-GUARD) or (partition == "holdout" and p > SPLIT+GUARD):
                    points.append([p, y0+py*(top+y)])
        out[metric] = {"xy": sorted(points), "readout_width": [3*abs(px), 3*abs(py)]}
    return out


def fit(training):
    p, frequency = np.asarray(training["frequency"]["xy"]).T
    def residuals(params):
        tau, distance = params
        predicted_log = -np.log(tau+distance/p)
        return predicted_log-np.log(frequency)
    opt = least_squares(residuals, [1., 2.], bounds=([0., 0.], [np.inf, np.inf]))
    if not opt.success:
        raise RuntimeError(opt.message)
    closed = opt.x.tolist()
    # The two simpler models are the limiting cases of the same operator.
    clock = [float(np.exp(-np.log(frequency).mean())), 0.]
    distance = [0., float(np.exp(np.log(p/frequency).mean()))]
    sp, observed = np.asarray(training["spacing"]["xy"]).T
    return {
        name: {"tau_h": tau, "length_cells": length, "spacing_offset_cells": float(np.mean(observed-(sp*tau+length)))}
        for name, (tau, length) in (("two_waiting_times", closed), ("fixed_clock", clock), ("fixed_distance", distance))
    }


def predict(model, p, metric):
    period = model["tau_h"] + model["length_cells"]/p
    return 1./period if metric == "frequency" else p*period + model["spacing_offset_cells"]


def seal(pdf, output):
    training = read_points(figure(pdf), "training")
    if min(len(panel["xy"]) for panel in training.values()) < 5:
        raise ValueError("Fewer than five readable training markers in a panel")
    models = fit(training)
    grid = [float(x/100) for x in range(203, 324)]
    frozen = {
        "experiment": "E29", "source_url": PDF_URL, "source_sha256": PDF_SHA256,
        "printed_cell_production_boundary": SPLIT, "guard_cells_per_hour": GUARD,
        "training": training, "models": models,
        "forecast_grid_cells_per_hour": grid,
        "forecasts": {
            name: {"frequency_h": [float(predict(model, p, "frequency")) for p in grid],
                   "spacing_cells": [float(predict(model, p, "spacing")) for p in grid]}
            for name, model in models.items()
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frozen, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def score_panel(model, metrics, data):
    p, actual = np.asarray(data["xy"]).T
    estimate = predict(model, p, metrics)
    if np.min(estimate) <= 0.:
        return {"n_markers": len(p), "nonpositive_predictions": int(np.sum(estimate <= 0.))}
    e = np.log(estimate/actual)
    xp, yp = data["readout_width"]
    lo_est = predict(model, p-xp, metrics)
    hi_est = predict(model, p+xp, metrics)
    lower = np.log(lo_est/(actual+yp))
    upper = np.log(hi_est/(actual-yp))
    min_abs = np.where((lower <= 0.) & (upper >= 0.), 0., np.minimum(abs(lower), abs(upper)))
    max_abs = np.maximum(abs(lower), abs(upper))
    return {
        "n_markers": len(p), "log_RMSE": float(np.sqrt(np.mean(e**2))), "mean_log_error": float(e.mean()),
        "log_RMSE_digitization_bounds": [float(np.sqrt(np.mean(min_abs**2))), float(np.sqrt(np.mean(max_abs**2)))],
        "median_observed": float(np.median(actual)), "median_predicted": float(np.median(estimate)),
    }


def evaluate(pdf, predictions, out):
    frozen = json.loads(predictions.read_text(encoding="utf-8"))
    if frozen["source_sha256"] != PDF_SHA256 or frozen["printed_cell_production_boundary"] != SPLIT:
        raise ValueError("Prediction file uses a different source or cutoff")
    holdout = read_points(figure(pdf), "holdout")
    qualified = min(len(panel["xy"]) for panel in holdout.values()) >= 5
    scores = {name: {metric: score_panel(model, metric, panel) for metric, panel in holdout.items()}
              for name, model in frozen["models"].items()} if qualified else {}
    result = {
        "experiment": "E29", "sealed_predictions_sha256": sha256(predictions.read_bytes()).hexdigest(),
        "figure": "van den Berg et al. (2021) Figure 7 A/B, blue marker centres; roots may overlap",
        "holdout": holdout, "minimum_coverage_reached": qualified, "scores": scores,
        "checks": {
            "training_points_below_guard": all(p < SPLIT-GUARD for x in frozen["training"].values() for p, _ in x["xy"]),
            "holdout_points_above_guard": all(p > SPLIT+GUARD for x in holdout.values() for p, _ in x["xy"]),
            "frozen_times_and_cell_distances_are_nonnegative": all(m["tau_h"] >= 0. and m["length_cells"] >= 0.
                                                                  for m in frozen["models"].values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, result, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["seal", "evaluate"])
    parser.add_argument("--pdf", type=Path, default=ROOT/"data/raw/reflux_growth/berg_uu_alt.pdf")
    parser.add_argument("--predictions", type=Path, default=ROOT/"research/results/E29/sealed_predictions.json")
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E29")
    args = parser.parse_args()
    if args.operation == "seal":
        seal(args.pdf, args.predictions)
    else:
        evaluate(args.pdf, args.predictions, args.out)
