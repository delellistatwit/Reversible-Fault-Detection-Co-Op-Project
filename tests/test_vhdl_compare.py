import unittest
from src.vhdl_compare import load_vhdl_csv, compare_rows


class TestVHDLCompare(unittest.TestCase):

    def test_cnot_modelsim_matches_python(self):
        rows = load_vhdl_csv("benchmarks/vhdl/cnot_modelsim.csv")
        results = compare_rows(rows)
        self.assertEqual(len(results), 4)
        for r in results:
            with self.subTest(time_ns=r["time_ns"]):
                self.assertTrue(r["match"])

    def test_detects_a_mismatch(self):
        bad = [{"gate": "CNOT", "time_ns": "0", "A": "1", "B": "0", "P": "1", "Q": "0"}]
        self.assertFalse(compare_rows(bad)[0]["match"])


if __name__ == "__main__":
    unittest.main()