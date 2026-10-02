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

    def test_truth_table(self):
        g = NOTGate(0)
        expected = {
            (0,): (1,),
            (1,): (0,),
        }
        for inputs, output in expected.items():
            with self.subTest(inputs=inputs):
                self.assertEqual(g.apply(inputs), output)


class TestCNOTGate(unittest.TestCase):

    def test_stores_wires(self):
        g = CNOTGate(0, 1)
        self.assertEqual(g.name, "CNOT")
        self.assertEqual(g.wires, [0, 1])

    def test_rejects_same_control_and_target(self):
        with self.assertRaises(ValueError):
            CNOTGate(1, 1)

    def test_truth_table(self):
        g = CNOTGate(0, 1)
        expected = {
            (0, 0): (0, 0),
            (0, 1): (0, 1),
            (1, 0): (1, 1),
            (1, 1): (1, 0),
        }
        for inputs, output in expected.items():
            with self.subTest(inputs=inputs):
                self.assertEqual(g.apply(inputs), output)


class TestToffoliGate(unittest.TestCase):

    def test_stores_wires(self):
        g = ToffoliGate(0, 1, 2)
        self.assertEqual(g.name, "TOFFOLI")
        self.assertEqual(g.wires, [0, 1, 2])

    def test_rejects_repeated_wire(self):
        with self.assertRaises(ValueError):
            ToffoliGate(0, 0, 2)

    def test_truth_table(self):
        g = ToffoliGate(0, 1, 2)
        expected = {
            (0, 0, 0): (0, 0, 0),
            (0, 0, 1): (0, 0, 1),
            (0, 1, 0): (0, 1, 0),
            (0, 1, 1): (0, 1, 1),
            (1, 0, 0): (1, 0, 0),
            (1, 0, 1): (1, 0, 1),
            (1, 1, 0): (1, 1, 1),
            (1, 1, 1): (1, 1, 0),
        }
        for inputs, output in expected.items():
            with self.subTest(inputs=inputs):
                self.assertEqual(g.apply(inputs), output)


class TestFredkinGate(unittest.TestCase):

    def test_stores_wires(self):
        g = FredkinGate(0, 1, 2)
        self.assertEqual(g.name, "FREDKIN")
        self.assertEqual(g.wires, [0, 1, 2])

    def test_rejects_repeated_wire(self):
        with self.assertRaises(ValueError):
            FredkinGate(0, 1, 1)

    def test_truth_table(self):
        g = FredkinGate(0, 1, 2)
        expected = {
            (0, 0, 0): (0, 0, 0),
            (0, 0, 1): (0, 0, 1),
            (0, 1, 0): (0, 1, 0),
            (0, 1, 1): (0, 1, 1),
            (1, 0, 0): (1, 0, 0),
            (1, 0, 1): (1, 1, 0),
            (1, 1, 0): (1, 0, 1),
            (1, 1, 1): (1, 1, 1),
        }
        for inputs, output in expected.items():
            with self.subTest(inputs=inputs):
                self.assertEqual(g.apply(inputs), output)


if __name__ == "__main__":
    unittest.main()