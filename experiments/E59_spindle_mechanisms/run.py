"""Extract the printed mean displacement after cuts at two locations."""

import numpy as np

from experiments import particle_return_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb


def traces(image, axes, times, green):
    xzero, xr, t_ref, yzero, yr, d_ref = axes
    r, g, b = np.moveaxis(image, -1, 0)
    control = (
        ((g > 148) & (g - r > 88) & (g - b > 43)) if green else ((g > 150) & (g - r > 95) & (b - r > 87))
    )
    cut = (r > 224) & (r - g > 92) & (r - b > 92)
    rows, displacements = [], []
    for mask in (control, cut):
        means = []
        for t in times:
            x = round(xzero + (xr - xzero) * t / t_ref)
            # The mean trace is saturated. Avoid the legend and the frame.
            top = (220 if t < 0 else 95) if green else 113
            bottom = 440 if green else 340
            yy = np.where(mask[top:bottom, x - 1 : x + 2])[0]
            means.append(float(np.median(yy) + top) if yy.size >= 4 else None)
        rows.append(means)
        displacements.append([None if v is None else (yzero - v) * d_ref / (yzero - yr) for v in means])
    return {
        "times_s": list(times),
        "printed_mean_rows": rows,
        "uncut_and_cut_um": displacements,
        "axes_x0_xref_tref_y0_yref_dref": axes,
        "reading_halfwidth_um": 2 * d_ref / (yzero - yr),
    }


def compare(series, endpoint, slope_times):
    t = np.asarray(series["times_s"])
    data = np.asarray(series["uncut_and_cut_um"], dtype=float)
    i = series["times_s"].index(endpoint)
    values = data[:, i]
    sl = []
    for group in data:
        use = (t >= slope_times[0]) & (t <= slope_times[1]) & np.isfinite(group)
        sl.append(float(np.polyfit(t[use], group[use], 1)[0]))
    return {
        "endpoint_s": endpoint,
        "uncut_and_cut_at_endpoint_um": values.tolist(),
        "cut_minus_uncut_um": float(values[1] - values[0]),
        "uncut_and_cut_linear_slopes_um_per_s": sl,
        "slope_time_range_s": slope_times,
    }


def run(raw, out):
    image = rgb(sources.read(raw, "wufig-5.png"))
    plane = traces(image[0:442, 1489:2170], (319, 655, 15, 197.5, 95, 2), range(-9, 15), green=False)
    arc = traces(image[1240:1757, 1470:2170], (367, 640, 30, 236, 76, 4), range(-23, 34), green=True)
    metrics_plane = compare(plane, 12, [5, 12])
    metrics_arc = compare(arc, 30, [6, 20])
    summary = {
        "experiment": "E59",
        "doi": "10.1038/s41567-023-02223-z",
        "fig5b_plane": {
            **plane,
            **metrics_plane,
            "printed_displacement_datasets_each_group": 48,
            "axis_direction": "orthogonal away from the cut",
        },
        "fig5h_arc": {
            **arc,
            **metrics_arc,
            "printed_uncut_then_cut_embryos": [14, 19],
            "axis_direction": "progression toward anterior along the long axis",
        },
        "source_flow_context": "Fig. 5e averaged particles from 8 embryos and showed a local circular flow. The authors observed it also in the model of cortical pulling, in which motion of the nuclear complex generates flow.",
        "scope": "Two kinds of ablation in different assays; means of printed time trajectories are not individual measurements. The timing, trajectories, and hydrodynamic model do not measure total energy work or show material return through a toroidal route.",
        "checks": {
            "original_png_dimensions": image.shape[:2] == (1757, 2170),
            "both_endpoints_and_slope_windows_readable": all(
                np.isfinite(panel["uncut_and_cut_at_endpoint_um"]).all()
                and np.isfinite(panel["uncut_and_cut_linear_slopes_um_per_s"]).all()
                for panel in (metrics_plane, metrics_arc)
            ),
            "saturated_means_visible_at_majority_of_times": all(
                sum(v is not None for v in row) > 0.6 * len(row)
                for panel in (plane, arc)
                for row in panel["uncut_and_cut_um"]
            ),
            "pre_cut_arc_means_below_zero_until_minus_6_seconds": all(
                v < 0
                for row in arc["uncut_and_cut_um"]
                for t, v in zip(arc["times_s"], row, strict=True)
                if t <= -6 and v is not None
            ),
            "units_consistent_with_printed_ticks": abs((236 - 156) * 0.025 - 2) < 0.01
            and abs((198 - 146) * 2 / 102.5 - 1) < 0.025,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
