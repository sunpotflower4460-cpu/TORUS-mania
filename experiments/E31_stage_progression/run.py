"""Compare founder-cell induction and post-initiation organ counts."""

import argparse
from hashlib import sha256
import io
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

from experiments.common import save_summary
from experiments.local_reflux_reading import bar_top

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://pmc-oa-opendata.s3.amazonaws.com/PMC7775764.1/"
FILES = {
    "perianez_article.pdf": ("PMC7775764.1.pdf", "77b9b645725ee549d666cdab90431c42eff5cd77149810180547951b575e2d2c"),
    "perianez_sm.pdf": ("abd4722_SM.pdf", "c6681d011aa2a5550a72cb44c840ab7814ebcfd2608132a1e7b63b5f7d04745f"),
}


def founders(pdf):
    image_id = pdf[1].get_images()[0][0]
    with Image.open(io.BytesIO(pdf.extract_image(image_id)["image"])) as im:
        pixels = np.asarray(im.convert("RGB"), dtype=float)
    # Panel 1E has a break: three lower bars, then the top of the high bar.
    zero, low_tick_y, low_tick_value = 1517, 1170, 45.
    high_tick_y, high_tick_value = 1132, 750.
    high_scale = 15./(high_tick_y-1017.)
    low_scale = low_tick_value/(zero-low_tick_y)
    rows = [
        bar_top(pixels, zero, 729, 751),
        bar_top(pixels, zero, 799, 819),
        bar_top(pixels, zero, 868, 888),
        bar_top(pixels, high_tick_y, 934, 955),
    ]
    heights = [(zero-y)*low_scale for y in rows[:3]]
    heights.append(high_tick_value+(high_tick_y-rows[-1])*high_scale)
    return {
        "dose_muM_estradiol": [0, .1, .5, 10], "founder_marker_group_means": heights,
        "bar_top_rows": rows, "readout_halfwidth_by_group": [3*low_scale]*3+[3*high_scale],
        "note": "Inducible line scored in a separate experiment from the root and primordium counts.",
    }


def organs(pdf):
    page = pdf[2].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
    pixels = np.asarray(Image.frombytes("RGB", (page.width, page.height), page.samples), dtype=np.int16)
    r, g, b = pixels.transpose(2, 0, 1)
    colored = {
        "WT": (b-r > 25) & (b-g > 10) & (r < 105),
        "iaa18_potent": (r > 185) & (g > 75) & (r-b > 100),
        "potent_transgene": (g-r > 20) & (g-b > 12) & (g < 170),
    }
    groups = {}
    for name, mask in colored.items():
        thickness = distance_transform_edt(mask[265:450, 668:831])
        positions = []
        for center in (675, 749, 824):
            x = center-668
            region = thickness[:, x-6:x+7]
            if region.max() == 0.:
                raise ValueError(f"No marker at {center} for {name}")
            y, _ = np.where(region == region.max())
            positions.append(float(y.mean()+265))
        groups[name] = {
            "marker_rows": positions, "organs_per_plant": [max(0., (446-y)/5.) for y in positions]
        }
    return {
        "days_post_imbibition": [6, 9, 12], "reported_min_n_per_sample": 20,
        "primordia_plus_lateral_roots": groups, "readout_halfwidth": .6,
        "note": "A sum of primordia and lateral roots. Mutant and transgene markers nearly overlap at the zero line.",
    }


def run(raw, out):
    sources = {}
    for local, (remote, digest) in FILES.items():
        if sha256((raw/local).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Unexpected source PDF: {raw/local}")
        sources[local] = {"url": BASE+remote, "sha256": digest}
    with fitz.open(raw/"perianez_article.pdf") as pdf:
        cells = founders(pdf)
    with fitz.open(raw/"perianez_sm.pdf") as pdf:
        initiated = organs(pdf)
    a = cells["founder_marker_group_means"]
    b = initiated["primordia_plus_lateral_roots"]
    output = {
        "experiment": "E31", "study_doi": "10.1126/sciadv.abd4722", "sources": sources,
        "figure_1E_founder_marker_cell_counts": cells, "figure_S2C_post_initiation_counts": initiated,
        "within_figure_1E_change_from_mock": [x-a[0] for x in a[1:]],
        "figure_S2C_WT_minus_potent_at_12dpi": b["WT"]["organs_per_plant"][-1]-b["iaa18_potent"]["organs_per_plant"][-1],
        "checks": {
            "upper_marker_in_separate_axis_segment": 750. <= a[-1] <= 770.,
            "lower_bars_in_lower_axis_segment": all(0. <= x <= 45. for x in a[:3]),
            "three_readouts_for_each_group": all(len(x["organs_per_plant"])==3 for x in b.values()),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, output, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT/"data/raw/root_clock")
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E31")
    args = parser.parse_args()
    run(args.raw, args.out)
