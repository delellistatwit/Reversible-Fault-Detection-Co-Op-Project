import unittest
from src.circuit import Circuit
from src.gates import NOTGate, CNOTGate, ToffoliGate
from src.faults import (Fault, FaultGenerator, classify_faults,
                        INVALID, DUPLICATE, UNIQUE_VALID)
from src.benchmarks import build_half_adder


class TestFaultIDs(unittest.TestCase):

    def test_ids(self):
        self.assertEqual(Fault("REMOVE", (2,)).get_id(), "REMOVE_G2")
        self.assertEqual(Fault("CONTROL", (1, 0, 2)).get_id(), "CONTROL_G1_W0_TO_W2")
        self.assertEqual(Fault("SWAP", (0, 0, 1)).get_id(), "SWAP_G0_W0_W1")

    def test_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            Fault("STUCK_AT", (0,))

    def test_rejects_wrong_location_length(self):
        with self.assertRaises(ValueError):
            Fault("SWAP", (0, 1))


class TestRemoveRule(unittest.TestCase):

    def test_valid(self):
        c = build_half_adder()
        faulty = Fault("REMOVE", (0,)).apply(c)
        self.assertEqual([g.name for g in faulty.gates], ["CNOT"])
        self.assertEqual(len(c.gates), 2)   # original unchanged

    def test_rejected_gate_out_of_range(self):
        c = build_half_adder()
        self.assertIsNotNone(Fault("REMOVE", (5,)).check(c))
        with self.assertRaises(ValueError):
            Fault("REMOVE", (5,)).apply(c)


class TestControlRule(unittest.TestCase):

    def test_valid(self):
        c = build_half_adder()                       # gate 1 is CNOT(0, 1)
        faulty = Fault("CONTROL", (1, 0, 2)).apply(c)
        self.assertEqual(faulty.gates[1].control, 2)
        self.assertEqual(faulty.gates[1].wires, [2, 1])
        self.assertEqual(c.gates[1].control, 0)      # original unchanged

    def test_rejected_new_wire_already_used(self):
        c = build_half_adder()
        self.assertIsNotNone(Fault("CONTROL", (1, 0, 1)).check(c))

    def test_rejected_gate_has_no_control(self):
        c = Circuit(2)
        c.add_gate(NOTGate(0))
        self.assertIsNotNone(Fault("CONTROL", (0, 0, 1)).check(c))

    def test_rejected_old_wire_not_a_control(self):
        c = build_half_adder()
        self.assertIsNotNone(Fault("CONTROL", (1, 1, 2)).check(c))


class TestSwapRule(unittest.TestCase):

    def test_valid(self):
        c = build_half_adder()
        faulty = Fault("SWAP", (0, 0, 1)).apply(c)
        self.assertEqual([g.name for g in faulty.gates], ["SWAP", "TOFFOLI", "CNOT"])

    def test_rejected_same_wire_twice(self):
        c = build_half_adder()
        self.assertIsNotNone(Fault("SWAP", (0, 1, 1)).check(c))

    def test_rejected_wire_out_of_range(self):
        c = build_half_adder()
        self.assertIsNotNone(Fault("SWAP", (0, 0, 7)).check(c))


class TestGenerator(unittest.TestCase):

    def test_half_adder_counts(self):
        gen = FaultGenerator(build_half_adder())
        self.assertEqual(len(gen.generate_removal_faults()), 2)
        self.assertEqual(len(gen.generate_control_faults()), 1)
        self.assertEqual(len(gen.generate_swap_faults()), 6)
        self.assertEqual(len(gen.generate_all()), 9)

    def test_order_is_stable(self):
        ids1 = [f.get_id() for f in FaultGenerator(build_half_adder()).generate_all()]
        ids2 = [f.get_id() for f in FaultGenerator(build_half_adder()).generate_all()]
        self.assertEqual(ids1, ids2)

    def test_every_generated_fault_is_valid(self):
        c = build_half_adder()
        for f in FaultGenerator(c).generate_all():
            with self.subTest(fault=f.get_id()):
                self.assertIsNone(f.check(c))


class TestClassification(unittest.TestCase):

    def test_each_status(self):
        c = Circuit(2)
        c.add_gate(CNOTGate(0, 1))
        c.add_gate(CNOTGate(0, 1))
        faults = [Fault("REMOVE", (0,)), Fault("REMOVE", (1,)), Fault("REMOVE", (9,))]
        statuses = [s for _, s, _ in classify_faults(c, faults)]
        self.assertEqual(statuses, [UNIQUE_VALID, DUPLICATE, INVALID])

    def test_exactly_one_status_each(self):
        c = build_half_adder()
        faults = FaultGenerator(c).generate_all()
        results = classify_faults(c, faults)
        self.assertEqual(len(results), len(faults))

    def test_swap_crossing_carries_to_output(self):
        # a crossed pair stays crossed after the gate, so the outputs change
        c = Circuit(3)
        c.add_gate(ToffoliGate(0, 1, 2))
        f = Fault("SWAP", (0, 0, 1))
        self.assertEqual(classify_faults(c, [f])[0][1], UNIQUE_VALID)
        self.assertNotEqual(c.truth_table(), f.apply(c).truth_table())


if __name__ == "__main__":
    unittest.main()