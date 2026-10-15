"""Fault tests for every gate type.

Each gate is placed alone on its own wires plus one spare wire (the last wire),
so a control wire has somewhere to move. Every fault model is checked on every
gate: one valid case and the rejected cases.
"""

import unittest
from src.circuit import Circuit
from src.gate_specs import GATE_SPECS, build_single_gate, check_gate_schema
from src.faults import Fault, FaultGenerator, classify_faults, UNIQUE_VALID

GATE_TYPES = ("NOT", "CNOT", "TOFFOLI", "FREDKIN")

# expected fault counts for each gate alone plus one spare wire
EXPECTED_COUNTS = {
    "NOT":     {"REMOVE": 1, "CONTROL": 0, "SWAP": 1},
    "CNOT":    {"REMOVE": 1, "CONTROL": 1, "SWAP": 3},
    "TOFFOLI": {"REMOVE": 1, "CONTROL": 2, "SWAP": 6},
    "FREDKIN": {"REMOVE": 1, "CONTROL": 1, "SWAP": 6},
}


def gate_circuit(type_id):
    """One gate on wires 0..k-1, plus one spare wire."""
    gate = build_single_gate(type_id)
    c = Circuit(len(gate.wires) + 1)
    c.add_gate(gate)
    return c


def spare(c):
    return c.num_wires - 1


class TestRemoveOnEveryGate(unittest.TestCase):

    def test_valid_remove(self):
        for t in GATE_TYPES:
            with self.subTest(gate=t):
                c = gate_circuit(t)
                faulty = Fault("REMOVE", (0,)).apply(c)
                self.assertEqual(faulty.gates, [])
                self.assertEqual(len(c.gates), 1)                        # original unchanged
                for inputs, outputs in faulty.truth_table():
                    self.assertEqual(inputs, outputs)                    # wires pass straight through

    def test_rejects_missing_gate(self):
        for t in GATE_TYPES:
            with self.subTest(gate=t):
                self.assertIsNotNone(Fault("REMOVE", (1,)).check(gate_circuit(t)))


class TestControlOnEveryGate(unittest.TestCase):

    def test_not_has_no_control(self):
        c = gate_circuit("NOT")
        self.assertIsNotNone(Fault("CONTROL", (0, 0, spare(c))).check(c))

    def test_valid_control_move(self):
        for t in ("CNOT", "TOFFOLI", "FREDKIN"):
            with self.subTest(gate=t):
                c = gate_circuit(t)
                faulty = Fault("CONTROL", (0, 0, spare(c))).apply(c)
                gate = faulty.gates[0]
                first_control = GATE_SPECS[t]["controls"][0]
                self.assertEqual(getattr(gate, first_control), spare(c))
                self.assertTrue(check_gate_schema(gate))                 # still a well-formed gate
                self.assertEqual(getattr(c.gates[0], first_control), 0)  # original unchanged

    def test_rejects_wire_already_used(self):
        for t in ("CNOT", "TOFFOLI", "FREDKIN"):
            with self.subTest(gate=t):
                self.assertIsNotNone(Fault("CONTROL", (0, 0, 1)).check(gate_circuit(t)))

    def test_rejects_moving_a_target(self):
        for t in ("CNOT", "TOFFOLI", "FREDKIN"):
            with self.subTest(gate=t):
                c = gate_circuit(t)
                target = c.gates[0].wires[-1]                            # last wire is never a control
                self.assertIsNotNone(Fault("CONTROL", (0, target, spare(c))).check(c))

    def test_rejects_wire_out_of_range(self):
        for t in ("CNOT", "TOFFOLI", "FREDKIN"):
            with self.subTest(gate=t):
                c = gate_circuit(t)
                self.assertIsNotNone(Fault("CONTROL", (0, 0, c.num_wires + 3)).check(c))


class TestSwapOnEveryGate(unittest.TestCase):

    def test_valid_swap(self):
        for t in GATE_TYPES:
            with self.subTest(gate=t):
                c = gate_circuit(t)
                faulty = Fault("SWAP", (0, 0, spare(c))).apply(c)
                self.assertEqual([g.name for g in faulty.gates], ["SWAP", t])
                self.assertEqual(len(c.gates), 1)                        # original unchanged

    def test_rejects_same_wire(self):
        for t in GATE_TYPES:
            with self.subTest(gate=t):
                self.assertIsNotNone(Fault("SWAP", (0, 0, 0)).check(gate_circuit(t)))

    def test_rejects_wire_out_of_range(self):
        for t in GATE_TYPES:
            with self.subTest(gate=t):
                c = gate_circuit(t)
                self.assertIsNotNone(Fault("SWAP", (0, 0, c.num_wires + 3)).check(c))


class TestGeneratorOnEveryGate(unittest.TestCase):

    def test_fault_counts(self):
        for t in GATE_TYPES:
            with self.subTest(gate=t):
                counts = {"REMOVE": 0, "CONTROL": 0, "SWAP": 0}
                for f in FaultGenerator(gate_circuit(t)).generate_all():
                    counts[f.fault_type] += 1
                self.assertEqual(counts, EXPECTED_COUNTS[t])

    def test_every_fault_is_detected(self):
        for t in GATE_TYPES:
            c = gate_circuit(t)
            correct = c.truth_table()
            for f, status, _ in classify_faults(c, FaultGenerator(c).generate_all()):
                with self.subTest(gate=t, fault=f.get_id()):
                    self.assertEqual(status, UNIQUE_VALID)
                    self.assertNotEqual(f.apply(c).truth_table(), correct)


if __name__ == "__main__":
    unittest.main()