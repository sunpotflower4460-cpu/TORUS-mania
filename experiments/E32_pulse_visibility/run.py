"""Compare pulse loss and true slowing when their persistent sites agree."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.stats import norm

from experiments.common import save_summary

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEAL = ROOT/"research/results/E29/sealed_predictions.json"
PRODUCTION = 2.5
N_CYCLES = 40000
SEED = 29032
WEAK_PEAK = .35
SIGMA_VALUES = (.05, .10, .20, .35)
FALSE_LIMIT, SENSITIVITY_LIMIT = .05, .80


def intervals(times, window):
    gaps = np.diff(times)
    return {
        "retained_sites": len(times), "rate_per_hour_for_full_window": len(times)/window,
        "mean_interval_h": float(gaps.mean()), "coefficient_of_variation": float(gaps.std(ddof=1)/gaps.mean()),
        "mean_spacing_in_mature_cell_lengths": float(PRODUCTION*gaps.mean()),
    }


def compare_periods(rng, base_period):
    period_cases = {}
    preview = {}
    window = base_period*N_CYCLES
    ticks = np.arange(1, N_CYCLES+1)*base_period
    for q in (.25, .50, .80):
        strong = rng.random(N_CYCLES) < q
        survived = ticks[strong]
        slow_fixed = np.arange(1, int(N_CYCLES*q)+1)*base_period/q
        # The fluctuating slow source can have the same geometric interval law.
        # Couple the two models to the same draws to demonstrate agreement even
        # along a single realization of the site process.
        slow_noisy = ticks[np.flatnonzero(strong)]
        period_cases[str(q)] = {
            "fixed_period_thinned": intervals(survived, window),
            "longer_fixed_period": intervals(slow_fixed, window),
            "longer_fluctuating_period_matched_sites": intervals(slow_noisy, window),
            "exact_mean_interval_h": base_period/q,
            "exact_site_rate_per_hour": q/base_period,
            "exact_thinned_interval_cv": float(np.sqrt(1-q)),
            "all_site_times_equal_under_coupling": bool(np.array_equal(survived, slow_noisy)),
        }
        if q == .5:
            preview = {
                "all_pulse_times_fixed_period_h": ticks[:24].tolist(),
                "weak_amplitude_and_strong_amplitude": np.where(strong[:24], 1., WEAK_PEAK).tolist(),
                "common_persistent_site_times_h": ticks[:24][strong[:24]].tolist(),
            }
    return period_cases, preview


def compare_detectors(rng):
    z_false = norm.ppf(1-FALSE_LIMIT)
    z_sens = norm.ppf(SENSITIVITY_LIMIT)
    noise = rng.standard_normal(N_CYCLES)
    evidence = {}
    for sigma in SIGMA_VALUES:
        lower_bound = sigma*z_false
        upper_bound = WEAK_PEAK-sigma*z_sens
        false_stimulus = sigma*noise
        weak_stimulus = WEAK_PEAK+sigma*noise
        evidence[str(sigma)] = {
            "threshold_at_5_percent_false_positives": float(lower_bound),
            "largest_threshold_at_80_percent_sensitivity": float(upper_bound),
            "both_requirements_possible": bool(lower_bound <= upper_bound),
            "theory_sensitivity_at_5_percent_false_positives": float(norm.sf((lower_bound-WEAK_PEAK)/sigma)),
            "simulated_false_positive_rate": float(np.mean(false_stimulus >= lower_bound)),
            "simulated_sensitivity": float(np.mean(weak_stimulus >= lower_bound)),
        }
    return evidence, float(WEAK_PEAK/(z_false+z_sens))


def run(seal, out):
    frozen = json.loads(seal.read_text(encoding="utf-8"))
    if frozen["experiment"] != "E29":
        raise ValueError("Expected a fixed E29 forecast")
    model = frozen["models"]["two_waiting_times"]
    base_period = model["tau_h"]+model["length_cells"]/PRODUCTION
    rng = np.random.default_rng(SEED)
    periods, preview = compare_periods(rng, base_period)
    detectors, noise_limit = compare_detectors(rng)
    summary = {
        "experiment": "E32", "model_base_period_h": base_period, "cell_production_per_h": PRODUCTION,
        "E29_training_estimates_sha256": sha256(seal.read_bytes()).hexdigest(),
        "period_units_note": "E29 supplies the base interval only. These are hypothetical pulse sequences.",
        "N_cycles": N_CYCLES, "rng_seed": SEED, "weak_peak_amplitude_arbitrary": WEAK_PEAK,
        "fixed_rate_and_fluctuating_comparisons": periods, "preview": preview,
        "threshold_detector_by_noise_sd": detectors, "largest_sd_with_both_requirements": noise_limit,
        "detector_note": "Measurements are at known windows with no stable site. No reporter kinetics or peak-timing uncertainty included.",
        "checks": {
            "geometric_expected_spacing_within_three_percent": all(
                abs(case["fixed_period_thinned"]["mean_interval_h"]/case["exact_mean_interval_h"]-1) < .03
                for case in periods.values()
            ),
            "geometric_interval_cv_within_three_percentage_points": all(
                abs(case["fixed_period_thinned"]["coefficient_of_variation"]-case["exact_thinned_interval_cv"]) < .03
                for case in periods.values()
            ),
            "paired_site_times_equal": all(x["all_site_times_equal_under_coupling"] for x in periods.values()),
            "gaussian_detection_simulation_matches_analytic_percentages": all(
                abs(x["simulated_sensitivity"]-x["theory_sensitivity_at_5_percent_false_positives"]) < .015
                and abs(x["simulated_false_positive_rate"]-FALSE_LIMIT) < .015 for x in detectors.values()
            ),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal", type=Path, default=DEFAULT_SEAL)
    parser.add_argument("--out", type=Path, default=ROOT/"research/results/E32")
    args = parser.parse_args()
    run(args.seal, args.out)
