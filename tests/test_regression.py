"""Regression tests: today's code must reproduce the committed Week 5 and Week 6 results.

If a code change alters any detection result or selected test set, these tests fail and
name the circuit, so the change is caught before it reaches the results or the paper.
"""

import csv
import json
import unittest
from src.experiments.integrated_run import CIRCUITS
from src.experiments.experiment import simulate_circuit, bits
from src.experiments.optimize import load_matrix, run_greedy, run_exact

with open("configs/week5.json") as file:
    WEEK5_CIRCUITS = json.load(file)["circuits"]
REFERENCE_DATE = "2026-10-22"


class TestWeek5Regression(unittest.TestCase):

    def test_matrices_match_committed_results(self):
        for circuit_id in WEEK5_CIRCUITS:
            with self.subTest(circuit=circuit_id):
                inputs, _, matrix = simulate_circuit(CIRCUITS[circuit_id]())
                with open(f"results/matrix/RUN_{circuit_id}_{REFERENCE_DATE}.csv", newline="") as file:
                    committed = list(csv.reader(file))
                self.assertEqual(committed[0], ["fault_id"] + [bits(v) for v in inputs])
                self.assertEqual(committed[1:], [[f] + [str(x) for x in row] for f, row in matrix.items()])


class TestWeek6Regression(unittest.TestCase):

    def test_selected_sets_match_committed_results(self):
        with open("results/optimization/week6_summary.csv", newline="") as file:
            committed = {row["circuit_id"]: row for row in csv.DictReader(file)}
        for circuit_id in WEEK5_CIRCUITS:
            with self.subTest(circuit=circuit_id):
                inputs, fault_ids, matrix = load_matrix(f"results/matrix/RUN_{circuit_id}_{REFERENCE_DATE}.csv")
                greedy = run_greedy(inputs, fault_ids, matrix)
                size, exact, status = run_exact(fault_ids, matrix, greedy, timeout_s=10)
                row = committed[circuit_id]
                self.assertEqual(";".join(bits(v) for v in greedy), row["greedy_vectors"])
                self.assertEqual(";".join(bits(v) for v in exact), row["exact_vectors"])
                self.assertEqual((str(size), status), (row["exact_size"], row["exact_status"]))


if __name__ == "__main__":
    unittest.main()