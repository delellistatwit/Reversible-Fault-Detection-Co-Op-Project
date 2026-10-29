import unittest
from src.benchmarks import build_half_adder, build_full_adder_peres
from src.experiment import simulate_circuit
from src.optimize import load_matrix, run_greedy, run_exact, resimulate


def matrix_for(circuit):
    """Build the input -> detected-faults matrix straight from the simulator."""
    inputs, _, rows = simulate_circuit(circuit)
    fault_ids = list(rows)
    matrix = {v: {f for f in fault_ids if rows[f][i]} for i, v in enumerate(inputs)}
    return inputs, fault_ids, matrix


class TestOptimize(unittest.TestCase):

    def test_load_week5_matrix(self):
        inputs, fault_ids, matrix = load_matrix("results/matrix/RUN_HALF_ADDER_2026-10-22.csv")
        self.assertEqual(len(inputs), 8)
        self.assertEqual(len(fault_ids), 9)
        self.assertIn("REMOVE_G0", matrix[(1, 1, 0)])          # 110 detects the missing Toffoli

    def test_half_adder_greedy_is_proven_minimum(self):
        inputs, fault_ids, matrix = matrix_for(build_half_adder())
        greedy = run_greedy(inputs, fault_ids, matrix)
        size, exact, status = run_exact(fault_ids, matrix, greedy, timeout_s=10)
        self.assertEqual((len(greedy), size, status), (3, 3, "PROVEN"))

    def test_peres_full_adder_exact_beats_greedy(self):
        inputs, fault_ids, matrix = matrix_for(build_full_adder_peres())
        greedy = run_greedy(inputs, fault_ids, matrix)
        size, exact, status = run_exact(fault_ids, matrix, greedy, timeout_s=10)
        self.assertEqual((len(greedy), size, status), (3, 2, "PROVEN"))

    def test_resimulation_confirms_selected_sets(self):
        circuit = build_full_adder_peres()
        inputs, fault_ids, matrix = matrix_for(circuit)
        greedy = run_greedy(inputs, fault_ids, matrix)
        _, exact, _ = run_exact(fault_ids, matrix, greedy, timeout_s=10)
        self.assertEqual(resimulate(circuit, greedy), [])
        self.assertEqual(resimulate(circuit, exact), [])

    def test_resimulation_catches_an_incomplete_set(self):
        # input 110 alone only catches some half adder faults
        missed = resimulate(build_half_adder(), [(1, 1, 0)])
        self.assertGreater(len(missed), 0)


if __name__ == "__main__":
    unittest.main()