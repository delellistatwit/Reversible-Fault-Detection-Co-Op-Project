import unittest
from src.circuit import Circuit
from src.gates import NOTGate, CNOTGate


class TestCircuit(unittest.TestCase):

    def test_stores_num_wires(self):
        c = Circuit(3)
        self.assertEqual(c.num_wires, 3)
        self.assertEqual(c.gates, [])

    def test_rejects_zero_wires(self):
        with self.assertRaises(ValueError):
            Circuit(0)

    def test_add_gate(self):
        c = Circuit(2)
        c.add_gate(CNOTGate(0, 1))
        self.assertEqual(len(c.gates), 1)

    def test_rejects_wire_out_of_range(self):
        c = Circuit(2)
        with self.assertRaises(ValueError):
            c.add_gate(CNOTGate(0, 5))

    def test_rejects_non_gate(self):
        c = Circuit(2)
        with self.assertRaises(TypeError):
            c.add_gate("not a gate")

    def test_simulate(self):
        c = Circuit(2)
        c.add_gate(CNOTGate(0, 1))
        self.assertEqual(c.simulate((1, 0)), (1, 1))

    def test_simulate_runs_gates_in_order(self):
        # NOT on wire 0 first turns (0, 0) into (1, 0),
        # then CNOT sees wire 0 on and flips wire 1, giving (1, 1).
        c = Circuit(2)
        c.add_gate(NOTGate(0))
        c.add_gate(CNOTGate(0, 1))
        self.assertEqual(c.simulate((0, 0)), (1, 1))

    def test_simulate_rejects_bad_bits(self):
        c = Circuit(2)
        with self.assertRaises(ValueError):
            c.simulate((1, 2))
        with self.assertRaises(ValueError):
            c.simulate((1, 0, 1))

    def test_validate(self):
        c = Circuit(2)
        c.add_gate(CNOTGate(0, 1))
        self.assertTrue(c.validate())

    def test_validate_catches_non_gate(self):
        c = Circuit(2)
        c.gates.append("not a gate")
        with self.assertRaises(TypeError):
            c.validate()

    def test_truth_table_row_count_and_order(self):
        c = Circuit(3)
        table = c.truth_table()
        self.assertEqual(len(table), 8)
        self.assertEqual(table[0][0], (0, 0, 0))
        self.assertEqual(table[-1][0], (1, 1, 1))

    def test_truth_table_cnot(self):
        c = Circuit(2)
        c.add_gate(CNOTGate(0, 1))
        expected = [
            ((0, 0), (0, 0)),
            ((0, 1), (0, 1)),
            ((1, 0), (1, 1)),
            ((1, 1), (1, 0)),
        ]
        self.assertEqual(c.truth_table(), expected)


if __name__ == "__main__":
    unittest.main()