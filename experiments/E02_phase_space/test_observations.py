"""Boundary cases which can silently change finite-sample recurrence and density."""

import unittest

import numpy as np

from experiments.E02_phase_space.run import TAU, cell_counts, entries, return_distance


class PhaseObservationTests(unittest.TestCase):
    def test_return_uses_both_shortest_angles(self):
        observed = np.array([[TAU - 0.01, 0], [0.01, TAU - 0.03], [0.01, np.pi]])
        np.testing.assert_allclose(return_distance(observed), [0, 0.03, np.pi], atol=1e-14)

    def test_count_entries_after_exit_including_final_sample(self):
        distance = np.array([0.0, 0.01, 0.2, 0.02, 0.0, 0.1, 0.015])
        np.testing.assert_array_equal(np.flatnonzero(entries(distance, 0.02)), [3, 6])

    def test_opposite_edges_identify_the_same_cell(self):
        points = np.array([[0, TAU], [TAU, -TAU], [-0.01, 0.01]])
        counts = cell_counts(points)
        self.assertEqual(counts[0, 0], 2)
        self.assertEqual(counts[-1, 0], 1)
        self.assertEqual(counts.sum(), 3)


if __name__ == "__main__":
    unittest.main()
