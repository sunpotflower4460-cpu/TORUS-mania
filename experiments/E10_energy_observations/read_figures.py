"""Reproduce the original figure readings (optional PyMuPDF and Pillow)."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import fitz
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.signal import find_peaks
from scipy.spatial import cKDTree
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "kumar": ("bec-arxiv.pdf", "3f6fd04de4ecb5a204624147bde1d26252aaeaa7f1b51e658bd049d2bbc11da5"),
    "vinitskiy": ("mephi-figure.jpg", "f9cb6e92b1bd7a300d6c83792631df56364228aeddb0d29e4ffbd3e9297ba0d0"),
}


def pdf_rgb(pdf, xref):
    pix = fitz.Pixmap(pdf, xref)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]


def colorscale(rgb, colorbar, top, bottom, margin):
    middle = np.median(colorbar[:,colorbar.shape[1]//2-4:colorbar.shape[1]//2+4], axis=1)
    calibration = np.linspace(top,bottom,len(middle))
    # The vector chart adds end borders to the colour bar. Ignore black edge pixels.
    colors = middle[margin:len(middle)-margin]
    lookup = cKDTree(colors)
    _, index = lookup.query(rgb.reshape(-1,3))
    return calibration[margin:len(middle)-margin][index].reshape(rgb.shape[:2])


def ring_radius(pdf):
    # Page 3, Fig. 1a. The white scale bar is an 8-point vector rectangle.
    page = pdf[2]
    image = next(item for item in page.get_image_info(xrefs=True) if item["xref"]==106)
    x0,y0,x1,y1 = image["bbox"]
    data = colorscale(pdf_rgb(pdf,106),pdf_rgb(pdf,111),2.,0.,4)
    y, x = np.indices(data.shape)
    we = np.maximum(data-.35,0)
    center = np.array([np.sum(y*we),np.sum(x*we)])/we.sum()
    radial_points = np.linspace(6.,22.,321)
    theta = np.linspace(0.,2*np.pi,120,endpoint=False)
    coords = [center[0]+np.sin(theta[:,None])*radial_points*data.shape[0]/(y1-y0),
              center[1]+np.cos(theta[:,None])*radial_points*data.shape[1]/(x1-x0)]
    radial_profiles = map_coordinates(data, coords, order=1)
    scale_band = fitz.Rect(162.,107.,176.,112.)
    bars = [entry["rect"] for entry in page.get_drawings()
            if entry.get("fill")== (1.,1.,1.) and scale_band.contains(entry["rect"])]
    width = bars[0].width
    samples = radial_points[np.argmax(radial_profiles,axis=1)] * 7/width
    return {"radius_um": float(np.median(samples)), "azimuth_percentiles_um": np.quantile(samples,[.1,.9]).tolist(),
            "azimuth_samples": len(samples), "scale_bar_length_um": 7., "scale_bar_points": width}


def heatmap(pdf):
    # Page 8. The raster is the measured density only, with theoretical lines stored as vector overlays.
    data = []
    for winding, xref in ((-1,291),(0,292),(1,293)):
        rgb = pdf_rgb(pdf,xref)
        values = colorscale(rgb,pdf_rgb(pdf,295),1.5,.5,4)
        # Axis bounds correspond to 41 equally spaced measurements from 0 to 40 ms.
        indices = np.floor((np.arange(41)+.5)*rgb.shape[1]/41).astype(int)
        angular = -np.pi + (np.arange(rgb.shape[0])+.5)*2*np.pi/rgb.shape[0]
        coefficient = (np.exp(1j*angular) @ values[:,indices])/len(angular)
        amplitude = abs(coefficient)
        valid = amplitude>=.30*amplitude.max()
        valid_times = np.arange(len(indices))[valid].astype(float)
        phase_deg = np.rad2deg(np.unwrap(2*np.angle(coefficient[valid]))/2)
        # The intercept describes the measured phase origin only. The predicted slope is set by R.
        slope, intercept = np.polyfit(valid_times, phase_deg,1)
        # Fit the axis direction modulo pi without assuming an unwrap across noisy columns.
        # At 1 ms spacing the unique slope interval is [-90, 90) degrees/ms.
        slopes = np.arange(-90.,90.,.02)
        axes = coefficient[valid]**2 / amplitude[valid]**2
        alignment = np.exp(-2j*np.deg2rad(slopes[:,None]*valid_times)) @ axes / len(valid_times)
        best = np.argmax(abs(alignment))
        data.append({"winding": winding, "sampled_columns": 41,
                     "times_ms": valid_times.tolist(), "phase_deg": phase_deg.tolist(),
                     "unwrap_slope_deg_ms": float(slope), "unwrap_intercept_deg": float(intercept),
                     "circular_slope_deg_ms": float(np.round(slopes[best],2)),
                     "axial_phase_coherence": float(abs(alignment[best])),
                     "phase_residual_rms_deg": float(np.std(phase_deg-intercept-slope*valid_times))})
    return data


def histogram(pdf):
    # Page 9, Fig. 5. Read the centres of the published fitted line as a second summary.
    points = {}
    for drawing in pdf[8].get_drawings():
        color = drawing.get("color")
        if color and color[0]>.4 and color[1]<.05 and color[2]<.05:
            for _, start, finish in drawing["items"]:
                points[start.x] = start.y
                points[finish.x] = finish.y
    xs = np.array(sorted(points))
    line = np.array([points[x] for x in xs])
    local_peaks, _ = find_peaks(-line, prominence=15.)
    # x=212.366 is 150 degrees, width of grid is 194 points for 210 degrees (through 360).
    assert len(local_peaks) == 3
    return {"angles_deg": (150+(xs[local_peaks]-212.36599731445312)*210/194).tolist(),
            "hold_ms": 35.1, "stated_total_shots": 614}


def measured_field(source):
    photo = np.asarray(Image.open(source).convert("RGB"),dtype=int)
    # Columns of the 17 distinct red squares, read from the figure, avoiding its theory and legend.
    centers = [175,211,247,283,319,354,390,426,462,497,533,569,605,640,676,712,748]
    red = (photo[:,:,0]>110) & (photo[:,:,0]>photo[:,:,1]+60) & (photo[:,:,0]>photo[:,:,2]+60)
    rows = []
    for column in centers:
        candidates, _ = np.nonzero(red[144:545,column-2:column+3])
        # Legend red begins only above line y=144 for radius columns >400. Select marker locally.
        if column > 400:
            candidates = candidates[candidates>65]
        y = np.mean(candidates)+144
        rows.append([float(100+(column-111)*200/715),float(30+(553-y)*50/480)])
    return {"current_a": 400, "reading_uncertainty_gauss": .5, "reading_uncertainty_mm": .6,
            "radius_mm_field_gauss": rows}


def run(raw_path, output):
    checksums = {}
    for key, (name,digest) in FILES.items():
        checksums[key] = sha256((raw_path/name).read_bytes()).hexdigest()
        if checksums[key]!=digest:
            raise ValueError(f"Published figure does not match the recorded version: {name}")
    with fitz.open(raw_path/FILES["kumar"][0]) as pdf:
        bec = {"radius": ring_radius(pdf), "heatmap": heatmap(pdf), "histogram": histogram(pdf)}
    data = {"input_sha256": checksums, "bec": bec, "magnet": measured_field(raw_path/FILES["vinitskiy"][0])}
    output.write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT/"data/raw/energy")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw,args.out)
