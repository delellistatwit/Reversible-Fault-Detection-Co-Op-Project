import json
import os
import tempfile
import unittest
from src.benchmarks import build_half_adder
from src.experiment import load_config, simulate_circuit, check_results


class TestConfig(unittest.TestCase):

    def test_week5_config_lists_known_circuits(self):
        from src.integrated_run import CIRCUITS
        config = load_config("configs/week5.json", CIRCUITS)
        self.assertEqual(len(config["circuits"]), 13)

    def test_rejects_unknown_circuit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad.json")
            with open(path, "w") as file:
                json.dump({"experiment": "x", "circuits": ["HALF_ADDER", "NO_SUCH_CIRCUIT"]}, file)
            with self.assertRaises(ValueError):
                load_config(path, {"HALF_ADDER": build_half_adder})


class TestExhaustiveRun(unittest.TestCase):

    def setUp(self):
        self.circuit = build_half_adder()
        self.inputs, self.raw, self.matrix = simulate_circuit(self.circuit)

    def test_every_fault_on_every_input(self):
        self.assertEqual(len(self.inputs), 8)
        self.assertEqual(len(self.matrix), 9)
        self.assertEqual(len(self.raw), 9 * 8)

    def test_matrix_row_matches_detection(self):
        # removing the Toffoli breaks the carry only for inputs 110 and 111
        self.assertEqual(self.matrix["REMOVE_G0"], [0, 0, 0, 0, 0, 0, 1, 1])

    def test_raw_rows_record_outputs(self):
        row = next(r for r in self.raw if r["fault_id"] == "REMOVE_G0" and r["input"] == "110")
        self.assertEqual((row["correct_output"], row["faulty_output"], row["detected"]), ("101", "100", 1))

    def test_all_checks_pass(self):
        for name, ok in check_results("HALF_ADDER", self.circuit, self.inputs, self.raw, self.matrix).items():
            with self.subTest(check=name):
                self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()