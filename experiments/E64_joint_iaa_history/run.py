"""Find the identifiable fraction of first returns with both IAA histories."""

import numpy as np
from scipy.optimize import linprog

from experiments.common import save_summary

# Actual classes and readings use the same order: other route/outer route,
# then continuously free/conjugated at some point.
CONSTRAINTS = ((1, 1, 1, 1), (0, 0, 1, 1), (0, 1, 0, 1))
TARGET = (0, 0, 1, 0)
LEAKAGES = (0.0, 0.02, 0.10, 0.25, 0.45, 0.50)
SAMPLE_SIZES = (100, 500, 2000)


def sharp_bounds(outer, conjugated):
    b = (1, outer, conjugated)
    goal = np.array(TARGET)
    low = linprog(goal, A_eq=CONSTRAINTS, b_eq=b, method="highs")
    high = linprog(-goal, A_eq=CONSTRAINTS, b_eq=b, method="highs")
    analytic = [max(0.0, outer - conjugated), min(outer, 1 - conjugated)]
    return {
        "outer_route": outer,
        "past_conjugation": conjugated,
        "bounds": analytic,
        "linear_program_bounds": [float(low.fun), float(-high.fun)],
        "endpoint_populations": [low.x.tolist(), high.x.tolist()],
    }


def population(outer, conjugated, outer_and_free):
    outer_and_conjugated = outer - outer_and_free
    other_and_conjugated = conjugated - outer_and_conjugated
    return np.array(
        [
            1 - outer - other_and_conjugated,
            other_and_conjugated,
            outer_and_free,
            outer_and_conjugated,
        ]
    )


def readout_matrix(leakage):
    tag = np.array([[1 - leakage, leakage], [leakage, 1 - leakage]])
    return np.kron(tag, tag)


def joint_readout(leakage, worlds, rng):
    matrix = readout_matrix(leakage)
    singular = np.linalg.svd(matrix, compute_uv=False)
    rank = int(np.linalg.matrix_rank(matrix))
    measured = [matrix @ world for world in worlds]
    contrast = measured[1] - measured[0]
    simulation = {}
    if rank == 4:
        # Each row of observed counts is fitted as a measured frequency vector.
        # An unrestricted inverse makes noise amplification visible.
        inverse = np.linalg.inv(matrix)
        for sample_size in SAMPLE_SIZES:
            model_outcomes = []
            for observed in measured:
                trials = rng.multinomial(sample_size, observed, size=2000) / sample_size
                recovered = trials @ inverse.T
                model_outcomes.append(
                    {
                        "central_95_percent": np.quantile(
                            recovered[:, 2], (0.025, 0.975)
                        ).tolist(),
                        "mean": float(recovered[:, 2].mean()),
                        "invalid_population_fraction": float(
                            np.mean(np.any(recovered < -1e-10, axis=1))
                        ),
                    }
                )
            simulation[str(sample_size)] = model_outcomes
    return {
        "route_and_chemistry_leakage_each": leakage,
        "rank": rank,
        "condition_number": float(singular[0] / singular[-1]) if rank == 4 else None,
        "singular_values": singular.tolist(),
        "signal_attenuation": (1 - 2 * leakage) ** 2,
        "total_variation_between_observed_populations": float(
            np.abs(contrast).sum() / 2
        ),
        "observed_populations": [row.tolist() for row in measured],
        "simulation": simulation,
    }


def run(out):
    bounds = [sharp_bounds(0.50, 0.50), sharp_bounds(0.65, 0.30)]
    worlds = [population(0.65, 0.30, value) for value in (0.40, 0.55)]
    rng = np.random.default_rng(641120)
    experiments = [joint_readout(leakage, worlds, rng) for leakage in LEAKAGES]
    checks = {
        "linear_program_and_analytic_bounds_agree": all(
            np.allclose(item["bounds"], item["linear_program_bounds"])
            for item in bounds
        ),
        "opposed_histories_have_equal_marginals": bool(
            np.allclose(np.dot(CONSTRAINTS, worlds[0]), np.dot(CONSTRAINTS, worlds[1]))
        ),
        "no_leakage_preserves_worlds": bool(
            np.allclose(experiments[0]["observed_populations"], worlds)
        ),
        "rank_lost_at_chance_readout": [item["rank"] for item in experiments]
        == [4] * 5 + [1],
        "joint_difference_matches_both_tags_attenuation": all(
            np.isclose(
                item["total_variation_between_observed_populations"],
                0.30 * item["signal_attenuation"],
            )
            for item in experiments
        ),
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E64",
            "evidence": "mathematical model and simulated readouts",
            "denominator": "Verified first returns recovered as intact-label free IAA in the inner origin region",
            "class_order": [
                "other/free",
                "other/conjugated",
                "outer/free",
                "outer/conjugated",
            ],
            "outer_route_definition": "Verified passage through root tip and outer tissue, in order",
            "bounded_histories": bounds,
            "distinct_populations_for_the_same_marginals": [
                world.tolist() for world in worlds
            ],
            "joint_readouts": experiments,
            "simulation_trials_per_setting": 2000,
            "seed": 641120,
            "checks": checks,
        },
        __file__,
    )
