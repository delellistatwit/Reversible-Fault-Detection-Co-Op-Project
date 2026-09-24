import unittest
from src.gates import NOTGate, CNOTGate, ToffoliGate, FredkinGate


class TestNOTGate(unittest.TestCase):

    def test_stores_wires(self):
        g = NOTGate(1)
        self.assertEqual(g.name, "NOT")
        self.assertEqual(g.wires, [1])

    def test_rejects_negative_wire(self):
        with self.assertRaises(ValueError):
            NOTGate(-1)

    @unittest.skip("Truth-table test added next week")
    def test_truth_table(self):
        pass


class TestCNOTGate(unittest.TestCase):

    def test_stores_wires(self):
        g = CNOTGate(0, 1)
        self.assertEqual(g.name, "CNOT")
        self.assertEqual(g.wires, [0, 1])

    def test_rejects_same_control_and_target(self):
        with self.assertRaises(ValueError):
            CNOTGate(1, 1)

    @unittest.skip("Truth-table test added next week")
    def test_truth_table(self):
        pass


class TestToffoliGate(unittest.TestCase):

    def test_stores_wires(self):
        g = ToffoliGate(0, 1, 2)
        self.assertEqual(g.name, "TOFFOLI")
        self.assertEqual(g.wires, [0, 1, 2])

    def test_rejects_repeated_wire(self):
        with self.assertRaises(ValueError):
            ToffoliGate(0, 0, 2)

    @unittest.skip("Truth-table test added next week")
    def test_truth_table(self):
        pass


class TestFredkinGate(unittest.TestCase):

    def test_stores_wires(self):
        g = FredkinGate(0, 1, 2)
        self.assertEqual(g.name, "FREDKIN")
        self.assertEqual(g.wires, [0, 1, 2])

    def test_rejects_repeated_wire(self):
        with self.assertRaises(ValueError):
            FredkinGate(0, 1, 1)

    @unittest.skip("Truth-table test added next week")
    def test_truth_table(self):
        pass


if __name__ == "__main__":
    unittest.main()