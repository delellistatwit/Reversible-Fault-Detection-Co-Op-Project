import unittest
from src.benchmarks import build_half_adder
from src.circuit import Circuit
from src.gates import CNOTGate
from src.faults import Fault, FaultGenerator, classify_faults, UNIQUE_VALID
from src.mutant_audit import expected_counts, audit_circuit, audit_results


class TestMutantAudit(unittest.TestCase):

    def test_half_adder_formula_counts(self):
        self.assertEqual(expected_counts(build_half_adder()), {"REMOVE": 2, "CONTROL": 1, "SWAP": 6})

    def test_half_adder_passes_every_check(self):
        for name, (ok, detail) in audit_circuit(build_half_adder()).items():
            with self.subTest(check=name):
                self.assertTrue(ok, detail)

    def test_catches_a_missing_fault(self):
        c = build_half_adder()
        faults = FaultGenerator(c).generate_all()[:-1]      # drop one fault
        checks = audit_results(c, faults, classify_faults(c, faults))
        self.assertFalse(checks["counts_match_formulas"][0])

    def test_catches_a_repeated_fault(self):
        c = build_half_adder()
        faults = FaultGenerator(c).generate_all()
        faults = faults + [faults[0]]                       # same fault twice
        checks = audit_results(c, faults, classify_faults(c, faults))
        self.assertFalse(checks["unique_fault_ids"][0])

    def test_catches_a_missing_status(self):
        c = build_half_adder()
        faults = FaultGenerator(c).generate_all()
        results = classify_faults(c, faults)[:-1]           # one fault never classified
        checks = audit_results(c, faults, results)
        self.assertFalse(checks["one_status_per_fault"][0])

    def test_catches_a_bad_duplicate_link(self):
        c = Circuit(2)
        c.add_gate(CNOTGate(0, 1))
        faults = FaultGenerator(c).generate_all()
        results = [(f, s, n) for f, s, n in classify_faults(c, faults)]
        f, _, _ = results[1]
        results[1] = (f, "DUPLICATE", "REMOVE_G0")          # claims a duplicate that is not the same circuit
        checks = audit_results(c, faults, results)
        self.assertFalse(checks["duplicates_valid"][0])


if __name__ == "__main__":
    unittest.main()