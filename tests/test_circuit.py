import unittest
from src.circuit import Circuit
from src.gates import CNOTGate


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

    @unittest.skip("simulate() added next week")
    def test_simulate(self):
        pass

    @unittest.skip("validate() added next week")
    def test_validate(self):
        pass

    @unittest.skip("truth_table() added next week")
    def test_truth_table_row_count(self):
        pass


if __name__ == "__main__":
    unittest.main()