import os
import tempfile
import unittest
from src.real_import import load_real


def write_temp(text):
    """Write text to a temporary .real file and return its path."""
    handle, path = tempfile.mkstemp(suffix=".real")
    with os.fdopen(handle, "w") as file:
        file.write(text)
    return path


class TestLoadReal(unittest.TestCase):

    def test_graycode6(self):
        c, info = load_real("benchmarks/graycode6.real")
        self.assertEqual(c.num_wires, 6)
        self.assertEqual(len(c.gates), 5)
        self.assertEqual(info["variables"], ["a", "b", "c", "d", "e", "f"])
        # first line is "t2 b a": control b (wire 1), target a (wire 0)
        self.assertEqual(c.gates[0].control, 1)
        self.assertEqual(c.gates[0].target, 0)

    def test_ham7(self):
        c, _ = load_real("benchmarks/ham7.real")
        self.assertEqual(c.num_wires, 7)
        self.assertEqual(len(c.gates), 25)
        names = [g.name for g in c.gates]
        self.assertEqual(names.count("TOFFOLI"), 6)
        self.assertEqual(names.count("CNOT"), 19)

    def test_imported_circuits_are_reversible(self):
        for path in ("benchmarks/graycode6.real", "benchmarks/ham7.real"):
            with self.subTest(path=path):
                c, _ = load_real(path)
                outputs = [out for _, out in c.truth_table()]
                self.assertEqual(len(set(outputs)), len(outputs))

    def test_rejects_unsupported_gate(self):
        path = write_temp(".variables a b c d\n.begin\nt4 a b c d\n.end\n")
        with self.assertRaises(ValueError):
            load_real(path)
        os.remove(path)

    def test_rejects_unknown_variable(self):
        path = write_temp(".variables a b\n.begin\nt2 a z\n.end\n")
        with self.assertRaises(ValueError):
            load_real(path)
        os.remove(path)


if __name__ == "__main__":
    unittest.main()