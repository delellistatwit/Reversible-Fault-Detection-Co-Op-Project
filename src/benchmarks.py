from src.circuit import Circuit
from src.gates import CNOTGate, ToffoliGate


def build_xor():
    """Reversible XOR. Standard design, to be checked against Jeramiah's handoff.

    Wires:   0 = A, 1 = B
    Outputs: wire 0 = A (garbage), wire 1 = A XOR B
    """
    c = Circuit(2)
    c.add_gate(CNOTGate(0, 1))
    return c


def build_half_adder():
    """Reversible half adder. Standard design, to be checked against Jeramiah's handoff.

    Wires:   0 = A, 1 = B, 2 = constant input, always starts at 0
    Outputs: wire 0 = A (garbage), wire 1 = SUM (A XOR B), wire 2 = CARRY (A AND B)
    """
    c = Circuit(3)
    c.add_gate(ToffoliGate(0, 1, 2))
    c.add_gate(CNOTGate(0, 1))
    return c