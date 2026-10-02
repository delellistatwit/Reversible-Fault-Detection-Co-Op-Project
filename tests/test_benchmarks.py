import unittest
from itertools import product
from src.benchmarks import build_xor, build_half_adder


class TestXOR(unittest.TestCase):

    def test_xor_output(self):
        c = build_xor()
        for a, b in product((0, 1), repeat=2):
            with self.subTest(a=a, b=b):
                out = c.simulate((a, b))
                self.assertEqual(out[1], a ^ b)


class TestHalfAdder(unittest.TestCase):

    def test_sum_and_carry(self):
        c = build_half_adder()
        for a, b in product((0, 1), repeat=2):
            with self.subTest(a=a, b=b):
                out = c.simulate((a, b, 0))
                self.assertEqual(out[1], a ^ b)   # sum
                self.assertEqual(out[2], a & b)   # carry

    def test_gate_order(self):
        c = build_half_adder()
        names = [g.name for g in c.gates]
        self.assertEqual(names, ["TOFFOLI", "CNOT"])


if __name__ == "__main__":
    unittest.main()