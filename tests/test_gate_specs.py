import unittest
from src.gates import Gate, NOTGate, CNOTGate, ToffoliGate, FredkinGate
from src.gate_specs import (GATE_SPECS, gate_type_id, gate_instance_id,
                            check_gate_schema, build_single_gate, cross_check_with_vhdl)


class TestGateSchemas(unittest.TestCase):

    def test_every_gate_type_has_a_spec(self):
        self.assertEqual(list(GATE_SPECS), ["NOT", "CNOT", "TOFFOLI", "FREDKIN"])

    def test_every_gate_matches_its_schema(self):
        for type_id in GATE_SPECS:
            with self.subTest(gate=type_id):
                self.assertTrue(check_gate_schema(build_single_gate(type_id)))

    def test_schema_rejects_tampered_wires(self):
        g = CNOTGate(0, 1)
        g.wires = [0, 2]          # wires no longer match the control/target fields
        with self.assertRaises(ValueError):
            check_gate_schema(g)

    def test_schema_rejects_unknown_gate(self):
        with self.assertRaises(ValueError):
            gate_type_id(Gate("MYSTERY", [0]))


class TestStableIDs(unittest.TestCase):

    def test_type_ids(self):
        self.assertEqual(gate_type_id(NOTGate(0)), "NOT")
        self.assertEqual(gate_type_id(CNOTGate(0, 1)), "CNOT")
        self.assertEqual(gate_type_id(ToffoliGate(0, 1, 2)), "TOFFOLI")
        self.assertEqual(gate_type_id(FredkinGate(0, 1, 2)), "FREDKIN")

    def test_instance_ids(self):
        self.assertEqual(gate_instance_id(0, NOTGate(3)), "G0_NOT")
        self.assertEqual(gate_instance_id(2, ToffoliGate(0, 1, 2)), "G2_TOFFOLI")

    def test_ids_do_not_depend_on_wires(self):
        self.assertEqual(gate_instance_id(1, CNOTGate(0, 1)), gate_instance_id(1, CNOTGate(3, 2)))


class TestVHDLCrossCheck(unittest.TestCase):

    def test_every_gate_matches_jeramiah_equations(self):
        for type_id, result in cross_check_with_vhdl().items():
            with self.subTest(gate=type_id):
                self.assertEqual(result["mismatches"], [])


if __name__ == "__main__":
    unittest.main()