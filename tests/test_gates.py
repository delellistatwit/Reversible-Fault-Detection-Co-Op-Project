import unittest
from itertools import product
from src.gates import NOTGate, CNOTGate, ToffoliGate, FredkinGate, PeresGate, HNGGate


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


class TestPeresGate(unittest.TestCase):

    def test_stores_wires(self):
        g = PeresGate(0, 1, 2)
        self.assertEqual(g.name, "PERES")
        self.assertEqual(g.wires, [0, 1, 2])

    def test_truth_table(self):
        g = PeresGate(0, 1, 2)
        for a, b, c in product((0, 1), repeat=3):
            with self.subTest(inputs=(a, b, c)):
                self.assertEqual(g.apply((a, b, c)), (a, a ^ b, (a & b) ^ c))

    def test_is_reversible(self):
        g = PeresGate(0, 1, 2)
        outputs = {g.apply(bits) for bits in product((0, 1), repeat=3)}
        self.assertEqual(len(outputs), 8)          # every input gives a different output


class TestHNGGate(unittest.TestCase):

    def test_stores_wires(self):
        g = HNGGate(0, 1, 2, 3)
        self.assertEqual(g.name, "HNG")
        self.assertEqual(g.wires, [0, 1, 2, 3])

    def test_truth_table(self):
        g = HNGGate(0, 1, 2, 3)
        for a, b, c, d in product((0, 1), repeat=4):
            with self.subTest(inputs=(a, b, c, d)):
                expected = (a, b, a ^ b ^ c, ((a ^ b) & c) ^ (a & b) ^ d)
                self.assertEqual(g.apply((a, b, c, d)), expected)

    def test_is_reversible(self):
        g = HNGGate(0, 1, 2, 3)
        outputs = {g.apply(bits) for bits in product((0, 1), repeat=4)}
        self.assertEqual(len(outputs), 16)         # every input gives a different output


if __name__ == "__main__":
    unittest.main()