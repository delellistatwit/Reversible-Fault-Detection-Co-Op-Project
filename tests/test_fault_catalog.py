import unittest
from src.benchmarks import build_half_adder
from src.fault_catalog import build_catalog, COLUMNS
from src.faults import INVALID, DUPLICATE, UNIQUE_VALID


class TestFaultCatalog(unittest.TestCase):

    def setUp(self):
        self.rows = build_catalog("HALF_ADDER", build_half_adder(), run_date="2026-10-13")

    def test_one_row_per_fault(self):
        self.assertEqual(len(self.rows), 9)
        ids = [r["fault_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_row_has_all_columns(self):
        for r in self.rows:
            self.assertEqual(list(r), COLUMNS)

    def test_every_row_has_exactly_one_valid_status(self):
        for r in self.rows:
            self.assertIn(r["status"], (INVALID, DUPLICATE, UNIQUE_VALID))

    def test_detecting_inputs_are_recorded(self):
        row = next(r for r in self.rows if r["fault_id"] == "REMOVE_G0")
        # removing the Toffoli breaks the carry only when A = B = 1
        self.assertEqual(row["detected_by"], "110;111")
        self.assertEqual(row["detected_count"], 2)
        self.assertEqual(row["total_vectors"], 8)

    def test_stable_ids(self):
        row = self.rows[0]
        self.assertEqual(row["run_id"], "RUN_HALF_ADDER_2026-10-13")
        self.assertEqual(row["gate_id"], "G0_TOFFOLI")


if __name__ == "__main__":
    unittest.main()