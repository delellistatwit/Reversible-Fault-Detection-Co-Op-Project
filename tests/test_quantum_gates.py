import unittest
from src.gates import VGate, VDaggerGate, NOTGate, CNOTGate, V0, V1, UNKNOWN
from src.circuit import Circuit, detects
from src.faults import FaultGenerator
from src.mutant_audit import audit_circuit

VALUES = (0, V0, 1, V1)


class TestVGates(unittest.TestCase):

    def test_v_moves_one_step_forward(self):
        g = VGate(0, 1)
        expected = {0: V0, V0: 1, 1: V1, V1: 0}
        for value, result in expected.items():
            with self.subTest(value=value):
                self.assertEqual(g.apply((1, value)), (1, result))

    def test_v_dagger_moves_one_step_back(self):
        g = VDaggerGate(0, 1)
        expected = {0: V1, V1: 1, 1: V0, V0: 0}
        for value, result in expected.items():
            with self.subTest(value=value):
                self.assertEqual(g.apply((1, value)), (1, result))

    def test_two_v_gates_equal_a_not(self):
        v = VGate(0, 1)
        for b in (0, 1):
            with self.subTest(b=b):
                self.assertEqual(v.apply(v.apply((1, b))), (1, 1 - b))

    def test_v_dagger_undoes_v(self):
        v, vd = VGate(0, 1), VDaggerGate(0, 1)
        for value in VALUES:
            with self.subTest(value=value):
                self.assertEqual(vd.apply(v.apply((1, value))), (1, value))

    def test_control_zero_does_nothing(self):
        for value in VALUES:
            with self.subTest(value=value):
                self.assertEqual(VGate(0, 1).apply((0, value)), (0, value))

    def test_halfway_control_gives_unknown(self):
        self.assertEqual(VGate(0, 1).apply((V0, 0)), (V0, UNKNOWN))
        self.assertEqual(CNOTGate(0, 1).apply((V1, 1)), (V1, UNKNOWN))

    def test_not_moves_two_steps(self):
        expected = {0: 1, 1: 0, V0: V1, V1: V0}
        for value, result in expected.items():
            with self.subTest(value=value):
                self.assertEqual(NOTGate(0).apply((value,)), (result,))


class TestVGateFaults(unittest.TestCase):

    def gate_circuit(self, gate_class):
        """One V or V+ gate on wires 0 and 1, plus a spare wire 2."""
        c = Circuit(3)
        c.add_gate(gate_class(0, 1))
        return c

    def test_fault_counts(self):
        # 1 REMOVE, control moves to the spare wire, 3 wire pairs to swap
        for gate_class in (VGate, VDaggerGate):
            counts = {"REMOVE": 0, "CONTROL": 0, "SWAP": 0}
            for f in FaultGenerator(self.gate_circuit(gate_class)).generate_all():
                counts[f.fault_type] += 1
            with self.subTest(gate=gate_class.__name__):
                self.assertEqual(counts, {"REMOVE": 1, "CONTROL": 1, "SWAP": 3})

    def test_mutant_audit_passes(self):
        for gate_class in (VGate, VDaggerGate):
            for name, (ok, detail) in audit_circuit(self.gate_circuit(gate_class)).items():
                with self.subTest(gate=gate_class.__name__, check=name):
                    self.assertTrue(ok, detail)


class TestDetectionRule(unittest.TestCase):

    def test_definite_difference_detects(self):
        self.assertTrue(detects((1, 0, 0), (1, 1, 0)))

    def test_same_output_does_not_detect(self):
        self.assertFalse(detects((1, 0, 0), (1, 0, 0)))

    def test_halfway_or_unknown_output_does_not_detect(self):
        self.assertFalse(detects((1, 0, 0), (1, V0, 0)))
        self.assertFalse(detects((1, 0, 0), (1, UNKNOWN, 0)))


if __name__ == "__main__":
    unittest.main()
