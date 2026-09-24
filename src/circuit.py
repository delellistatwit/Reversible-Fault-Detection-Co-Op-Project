from src.gates import Gate

class Circuit:
    """A reversible circuit: a set number of wires and an ordered list of gates."""

    def __init__(self, num_wires):
        """
        num_wires: how many wires the circuit has (wires are numbered 0 to num_wires - 1)
        """
        if not isinstance(num_wires, int) or num_wires < 1:
            raise ValueError(f"num_wires must be a positive integer, got {num_wires}")

        self.num_wires = num_wires
        self.gates = []

    def add_gate(self, gate):
        """Add a gate to the end of the circuit."""


        if not isinstance(gate, Gate):
            raise TypeError(f"expected a Gate, got {type(gate).__name__}")

        for w in gate.wires:
            if w >= self.num_wires:
                raise ValueError(f"{gate.name} uses wire {w}, but the circuit only has wires 0 to {self.num_wires - 1}")

        self.gates.append(gate)

    def simulate(self, bits):
        """Run the input bits through every gate in order and return the output bits. (Implemented next week.)"""
        raise NotImplementedError

    def validate(self):
        """Check that the circuit is well-formed. (Implemented next week.)"""
        raise NotImplementedError

    def truth_table(self):
        """Run every possible input and return a list of (input, output) pairs. (Implemented next week.)"""
        raise NotImplementedError