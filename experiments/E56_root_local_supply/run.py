"""Compare the spatial profiles of newly formed and total IAA with and without shoots."""

import numpy as np

from experiments import particle_return_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb


def recover_panel(image, x, rows, zero, tick, unit):
    # Read each group about the center of the printed square or triangle.
    for column, positions in zip(x, zip(*rows, strict=True), strict=True):
        for y in positions:
            if np.median(image[y - 2 : y + 3, column - 2 : column + 3]) > 105:
                raise ValueError(f"Mean marker not found near {column},{y}")
    scale = unit / (zero - tick)
    values = (zero - np.asarray(rows)) * scale
    return {
        "x_px": x,
        "marker_rows": rows,
        "zero_tick_unit": [zero, tick, unit],
        "values_intact_then_excised": values.tolist(),
        "reading_halfwidth": 2 * scale,
        "excised_as_fraction_of_intact": (values[1] / values[0]).tolist(),
        "tip_relative_to_remaining_three_average": (values[:, 0] / values[:, 1:].mean(axis=1)).tolist(),
    }


def run(raw, out):
    image = rgb(sources.read(raw, "ljungfig4.jpg")).mean(axis=2)
    synthesis = recover_panel(
        image, [68, 134, 199, 264], [[88, 91, 91, 98], [129, 145, 147, 145]], 170, 73, 1.2
    )
    amount = recover_panel(
        image, [403, 469, 537, 603], [[96, 127, 126, 133], [134, 150, 146, 148]], 171, 72, 2.0
    )
    corroboration = rgb(sources.read(raw, "petersfig5.jpg"))
    summary = {
        "experiment": "E56",
        "primary_doi": "10.1105/tpc.104.029272",
        "secondary_doi": "10.1105/tpc.109.066480",
        "labelled_interval_hours": 24,
        "measurement_day_after_germination": 8,
        "distance_edges_mm": [0, 0.5, 1.0, 1.5, 2.0],
        "relative_new_label_measure_fig4a": synthesis,
        "total_IAA_pg_per_mm_fig4b": amount,
        "scope": "New labeling ratio after germination day 7–8 with heavy water, not synthesis in mass per time. The excised root retains transport within the root and can change metabolism after excision.",
        "corroboration": "Petersson Fig. 5 reports cell-type staining and GC–SRM–MS in shoot-excised, NPA treated roots (16 h); contextual only.",
        "checks": {
            "original_dimensions": image.shape == (561, 640) and corroboration.shape[:2] == (231, 446),
            "four_halfmillimetre_intervals": all(
                len(v) == 4 for v in synthesis["values_intact_then_excised"]
            ),
            "group_labels_match_fig_4": synthesis["values_intact_then_excised"][0][0] > 0.9,
            "unit_axes_are_positive": amount["zero_tick_unit"][2] > 0
            and synthesis["zero_tick_unit"][2] > 0,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
