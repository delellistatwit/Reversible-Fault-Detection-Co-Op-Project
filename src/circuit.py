from itertools import product
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
        """Run the input bits through every gate in order and return the output bits as a tuple."""
        if len(bits) != self.num_wires:
            raise ValueError(f"expected {self.num_wires} bits, got {len(bits)}")

        for b in bits:
            if b not in (0, 1):
                raise ValueError(f"bits must be 0 or 1, got {b}")

        bits = tuple(bits)
        for gate in self.gates:
            bits = gate.apply(bits)
        return bits

    def validate(self):
        """Check that every gate is a Gate and only uses wires the circuit has. Returns True or raises an error."""
        for i, gate in enumerate(self.gates):
            if not isinstance(gate, Gate):
                raise TypeError(f"item {i} in the gate list is not a Gate")

            for w in gate.wires:
                if w >= self.num_wires:
                    raise ValueError(f"gate {i} ({gate.name}) uses wire {w}, but the circuit only has wires 0 to {self.num_wires - 1}")

        return True

    def truth_table(self):
        """Run every possible input in counting order and return a list of (input, output) pairs."""
        self.validate()

        table = []
        for inputs in product((0, 1), repeat=self.num_wires):
            table.append((inputs, self.simulate(inputs)))
        return table