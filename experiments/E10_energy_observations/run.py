"""Score publication-derived measurements against the registered circulation formulas."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.constants import hbar, atomic_mass

from experiments.common import save_summary
from experiments.E09_harmonic_energy import run as harmonic

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1]/"research/results/E10"


def relative_error(observed, predicted):
    return abs((predicted-observed)/observed)


def inductance(input_models):
    r_in, r_out = input_models["inner_mm"]*1.e-3, input_models["outer_mm"]*1.e-3
    rows = []
    for observation in input_models["rows"]:
        g = harmonic.MU0*observation["turns"]**2*observation["height_um"]*1.e-6/(2*np.pi)
        exact = float(g*np.log(r_out/r_in))*1.e9
        mid = 2*g*(r_out-r_in)/(r_out+r_in)*1.e9
        measured = observation["observed_nh"]
        rows.append({**observation, "ideal_nh": exact, "constant_field_nh": mid,
                     "ideal_error": relative_error(measured,exact),
                     "constant_field_error": relative_error(measured,mid),
                     "ideal_energy_nj_at_1_a": exact/2,
                     "inferred_energy_nj_at_1_a": measured/2})
    error = float(np.median([v["ideal_error"] for v in rows]))
    return {"doi": input_models["doi"], "rows": rows, "median_relative_error": error,
            "threshold": .20, "passes": error<=.20, "excluded": input_models["excluded"]}


def magnetic_profile(data, design):
    radius, observed = np.asarray(data["radius_mm_field_gauss"]).T
    setup = np.argmin(abs(radius-200.))
    inverse_r = observed[setup]*radius[setup]/radius
    constant = np.full(len(radius), observed[setup])
    held_out = np.arange(len(radius))!=setup
    errors = [float(np.median(relative_error(observed[held_out],p[held_out])))
              for p in (inverse_r,constant)]
    absolute = harmonic.MU0*design["turns"]*data["current_a"]/(2*np.pi*radius*1.e-3)*1.e4
    absolute_error = float(np.median(relative_error(observed,absolute)))
    energy_density = lambda gauss: (gauss*1.e-4)**2/(2*harmonic.MU0)
    return {"doi": "10.1088/1361-6587/ad0d87", "current_a": data["current_a"],
            "design": design,
            "reading_uncertainty_gauss": data["reading_uncertainty_gauss"],
            "reading_uncertainty_mm": data["reading_uncertainty_mm"],
            "normalization_index": int(setup), "shape_holdout_points": int(held_out.sum()),
            "absolute_prediction_points": len(radius),
            "radius_mm": radius.tolist(), "measured_gauss": observed.tolist(),
            "inverse_r_gauss": inverse_r.tolist(), "constant_gauss": constant.tolist(),
            "absolute_prediction_gauss": absolute.tolist(), "absolute_relative_error": absolute_error,
            "energy_density_from_measured_field_j_m3": energy_density(observed).tolist(),
            "energy_density_from_predicted_field_j_m3": energy_density(absolute).tolist(),
            "median_relative_error_inverse_r": errors[0], "median_relative_error_constant": errors[1],
            "passes": len(radius)>=4 and absolute_error<=min(.10,errors[1])}


def superflow(data):
    radius = data["radius"]["radius_um"]*1.e-6
    mass = 22.9897692820*atomic_mass
    # R is read independently from the unperturbed ring in Figure 1(a).
    rate_per_winding = float(np.degrees(hbar/(mass*radius**2))/1000)
    speed = hbar/(mass*radius)
    spectrum = 2*hbar/(mass*radius**2)/(2*np.pi)
    h = data["histogram"]
    groups = np.array(h["angles_deg"])
    histogram_slopes = (groups-groups[1])/h["hold_ms"]
    reports, errors = [], []
    for row, histogram in zip(data["heatmap"],histogram_slopes,strict=True):
        winding = row["winding"]
        predicted = winding * rate_per_winding
        measured = [row["circular_slope_deg_ms"],float(histogram)]
        error = [float(relative_error(value,predicted)) for value in measured] if winding else None
        reports.append({"winding": winding, "prediction_deg_ms": predicted,
                        "phase_slope_deg_ms": measured[0], "histogram_relative_slope_deg_ms": measured[1],
                        "registered_unwrapped_slope_deg_ms": row["unwrap_slope_deg_ms"],
                        "axial_phase_coherence": row["axial_phase_coherence"],
                        "sampled_heatmap_columns": row["sampled_columns"],
                        "used_heatmap_columns": len(row["times_ms"]), "relative_errors": error,
                        "sign_matches_both": all(np.sign(value)==winding for value in measured) if winding else None})
        if error:
            errors.extend(error)
    median_error = float(np.median(errors))
    return {"doi": "10.1088/1367-2630/18/2/025001", "radius": data["radius"],
            "unit_winding_speed_m_s": float(speed),
            "unit_winding_kinetic_energy_per_atom_j": float(mass*speed**2/2),
            "counterpropagating_mode_1_frequency_split_hz": float(spectrum),
            "observations": reports, "median_relative_error": median_error,
            "qualified_by_radius_figure": median_error<=.25,
            "histogram_angles_deg": h["angles_deg"],"histogram_shots_by_authors": h["stated_total_shots"]}


def intervention(source):
    x,p = np.asarray(source["barrier_over_chemical_potential_and_survival"]).T
    below, above = p[x<=1],p[x>1]
    # Sensitivity to 40% combined horizontal uncertainties quoted by the source.
    robust_low, robust_high = p[x*1.4<1], p[x*.6>1]
    return {**source, "measured_settings": len(x),
            "below_or_equal_1": {"n": len(below), "median_survival": float(np.median(below))},
            "above_1": {"n": len(above), "median_survival": float(np.median(above))},
            "sensitivity_outside_ambiguous_barriers": {
                "below_n": len(robust_low), "above_n": len(robust_high),
                "below_median": float(np.median(robust_low)), "above_median": float(np.median(robust_high))}}


def run(out):
    figures_path, tables_path = HERE/"figure_values.json", HERE/"table_values.json"
    figures = json.loads(figures_path.read_text())
    tables = json.loads(tables_path.read_text())
    coil = inductance(tables["coil"])
    magnet = magnetic_profile(figures["magnet"], tables["magnetic_design"])
    bec = superflow(figures["bec"])
    control = intervention(tables["topology_intervention"])
    checks = {"registered_coil_cases": len(coil["rows"])==3,
              "valid_magnetic_radius_data": len(magnet["radius_mm"])==17
                                           and np.all(np.diff(magnet["radius_mm"])>0),
              "valid_bec_winding_groups": [d["winding"] for d in bec["observations"]]==[-1,0,1],
              "all_barrier_settings": control["measured_settings"]==8}
    checks = {name:bool(value) for name,value in checks.items()}
    out.mkdir(parents=True,exist_ok=True)
    save_summary(out, {"coil":coil,"magnetic_profile":magnet,"bec":bec,
                       "barrier":control,"checks":checks}, __file__,harmonic.__file__,figures_path,tables_path)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=OUT)
    run(parser.parse_args().out)
