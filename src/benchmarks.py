from src.circuit import Circuit
from src.gates import NOTGate, CNOTGate, ToffoliGate, FredkinGate


def build_xor():
    """reversible XOR. standard design, to be checked against Jeramiah's handoff.

    Wires:   0 = A, 1 = B
    Outputs: wire 0 = A (garbage), wire 1 = A XOR B
    """
    c = Circuit(2)
    c.add_gate(CNOTGate(0, 1))
    return c


def build_half_adder():
    """reversible half adder. standard design, to be checked against Jeramiah's handoff.

    Wires:   0 = A, 1 = B, 2 = constant input, always starts at 0
    Outputs: wire 0 = A (garbage), wire 1 = SUM (A XOR B), wire 2 = CARRY (A AND B)
    """
    c = Circuit(3)
    c.add_gate(ToffoliGate(0, 1, 2))
    c.add_gate(CNOTGate(0, 1))
    return c


def build_all_gates():
    """Mixed circuit that uses all four gate types once.

    Wires:   0, 1, 2, 3 (no constant inputs)
    Gates:   NOT(3), CNOT(0, 1), TOFFOLI(0, 1, 2), FREDKIN(3, 1, 2)
    """
    c = Circuit(4)
    c.add_gate(NOTGate(3))
    c.add_gate(CNOTGate(0, 1))
    c.add_gate(ToffoliGate(0, 1, 2))
    c.add_gate(FredkinGate(3, 1, 2))
    return c


def build_full_adder():
    """reversible full adder from primitive gates. standard design, to be checked against Jeramiah's handoff.

    Wires:   0 = A, 1 = B, 2 = Cin, 3 = constant input, always starts at 0
    Outputs: wire 2 = SUM (A XOR B XOR Cin), wire 3 = CARRY (majority of A, B, Cin)
    """
    c = Circuit(4)
    c.add_gate(ToffoliGate(0, 1, 3))
    c.add_gate(CNOTGate(0, 1))
    c.add_gate(ToffoliGate(1, 2, 3))
    c.add_gate(CNOTGate(1, 2))
    return c