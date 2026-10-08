import copy

from src.circuit import Circuit
from src.gates import Gate, CNOTGate, ToffoliGate, FredkinGate


# Which attributes hold the control wires for each gate type
# NOT has no control, so it never gets CONTROL faults
CONTROL_ATTRS = {
    CNOTGate: ("control",),
    ToffoliGate: ("control1", "control2"),
    FredkinGate: ("control",),
}

# Fault statuses, assigned in this order
INVALID = "INVALID"
DUPLICATE = "DUPLICATE"
UNIQUE_VALID = "UNIQUE_VALID"


class WireSwap(Gate):
    """Internal helper used only for SWAP faults: always swaps two wires.

    This is not one of the four project gates.
    """

    def __init__(self, wire_a, wire_b):
        super().__init__("SWAP", [wire_a, wire_b])
        self.wire_a = wire_a
        self.wire_b = wire_b

    def apply(self, bits):
        """Swap the two wires unconditionally."""
        bits = list(bits)
        bits[self.wire_a], bits[self.wire_b] = bits[self.wire_b], bits[self.wire_a]
        return tuple(bits)


def circuit_signature(circuit):
    """Return a hashable description of a circuit's structure.

    Two circuits with the same signature have exactly the same gate list.
    Used to detect DUPLICATE faults.
    """
    return (circuit.num_wires, tuple((g.name, tuple(g.wires)) for g in circuit.gates))


class Fault:
    """One fault that can be injected into a circuit.

    Only three fault types are allowed:
        REMOVE- a gate is removed
        CONTROL- a gate's control wire is moved to a different wire
        SWAP- two wires are crossed right before a gate
    """

    TYPES = ("REMOVE", "CONTROL", "SWAP")
    LOCATION_LENGTHS = {"REMOVE": 1, "CONTROL": 3, "SWAP": 3}

    def __init__(self, fault_type, location):
        """
        fault_type: one of "REMOVE", "CONTROL", or "SWAP"
        location:   a tuple saying where the fault happens
                    (g,) REMOVE:  gate g is removed
                    (g, old, new) CONTROL: gate g's control moves from wire old to wire new
                    (g, a, b)     SWAP:    wires a and b are crossed right before gate g
        """
        if fault_type not in Fault.TYPES:
            raise ValueError(f"fault_type must be one of {Fault.TYPES}, got {fault_type}")

        if not isinstance(location, tuple):
            raise TypeError(f"location must be a tuple, got {type(location).__name__}")

        if len(location) != Fault.LOCATION_LENGTHS[fault_type]:
            raise ValueError(f"{fault_type} location must have {Fault.LOCATION_LENGTHS[fault_type]} values, got {location}")

        for n in location:
            if not isinstance(n, int) or n < 0:
                raise ValueError(f"location values must be non-negative integers, got {n}")

        
        self.fault_type = fault_type
        self.location = location

    def get_id(self):
        """Return this fault's string ID, e.g. "REMOVE_G2"."""

        if self.fault_type == "REMOVE":
            (g,) = self.location
            return f"REMOVE_G{g}"
        if self.fault_type == "CONTROL":
            g, old, new = self.location
            return f"CONTROL_G{g}_W{old}_TO_W{new}"
        g, a, b = self.location
        return f"SWAP_G{g}_W{a}_W{b}"

    def check(self, circuit):
        """Return None if this fault can be applied to the circuit, or a string saying why not."""


        num_gates = len(circuit.gates)
        g = self.location[0]

        if g >= num_gates:
            return f"gate {g} does not exist (circuit has {num_gates} gates)"

        if self.fault_type == "CONTROL":
            _, old, new = self.location
            gate = circuit.gates[g]
            attrs = CONTROL_ATTRS.get(type(gate))

            if attrs is None:
                return f"gate {g} ({gate.name}) has no control wire"
            
            if old not in [getattr(gate, a) for a in attrs]:
                return f"wire {old} is not a control of gate {g} ({gate.name})"
            
            if new >= circuit.num_wires:
                return f"wire {new} does not exist (circuit has wires 0 to {circuit.num_wires - 1})"
            
            if new in gate.wires:
                return f"wire {new} is already used by gate {g} ({gate.name})"

        if self.fault_type == "SWAP":
            _, a, b = self.location

            if a >= b:
                return f"swap wires must satisfy a < b, got a={a}, b={b}"
            
            if b >= circuit.num_wires:
                return f"wire {b} does not exist (circuit has wires 0 to {circuit.num_wires - 1})"

        return None

    def apply(self, circuit):
        """Return a new faulty copy of the circuit. The original is not changed.

        Raises ValueError if the fault cannot be applied
        """
        reason = self.check(circuit)

        if reason is not None:
            raise ValueError(f"{self.get_id()} is invalid: {reason}")

        faulty = copy.deepcopy(circuit)

        if self.fault_type == "REMOVE":
            (g,) = self.location
            del faulty.gates[g]

        elif self.fault_type == "CONTROL":
            g, old, new = self.location
            gate = faulty.gates[g]

            for attr in CONTROL_ATTRS[type(gate)]:
                if getattr(gate, attr) == old:
                    setattr(gate, attr, new)
                    break

            gate.wires = [new if w == old else w for w in gate.wires]

        elif self.fault_type == "SWAP":
            g, a, b = self.location
            faulty.gates.insert(g, WireSwap(a, b))

        faulty.validate()
        return faulty


class FaultGenerator:
    """Creates every possible fault of the three allowed types for a given circuit.

    The order is fixed (gate by gate, wire by wire), so repeated runs
    give the same list and the detection-matrix columns stay stable.
    """

    def __init__(self, circuit):
        """
        circuit: the correct circuit to generate faults for
        """
        if not isinstance(circuit, Circuit):
            raise TypeError(f"expected a Circuit, got {type(circuit).__name__}")

        self.circuit = circuit

    def generate_removal_faults(self):
        """Return a list of REMOVE faults, one per gate."""

        return [Fault("REMOVE", (g,)) for g in range(len(self.circuit.gates))]

    def generate_control_faults(self):
        """Return a list of CONTROL faults: each control wire moved to every wire the gate does not use."""

        faults = []
        for g, gate in enumerate(self.circuit.gates):
            for attr in CONTROL_ATTRS.get(type(gate), ()):
                old = getattr(gate, attr)
                for new in range(self.circuit.num_wires):
                    if new not in gate.wires:
                        faults.append(Fault("CONTROL", (g, old, new)))
        return faults

    def generate_swap_faults(self):
        """Return a list of SWAP faults: every wire pair (a < b) crossed before every gate."""

        faults = []
        n = self.circuit.num_wires
        for g in range(len(self.circuit.gates)):
            for a in range(n):
                for b in range(a + 1, n):
                    faults.append(Fault("SWAP", (g, a, b)))
        return faults

    def generate_all(self):
        """Return every fault from all three types in one list (REMOVE, then CONTROL, then SWAP)."""

        return self.generate_removal_faults() + self.generate_control_faults() + self.generate_swap_faults()


def classify_faults(circuit, faults):
    """Give every fault exactly one status, checked in this order:

        1. INVALID- the fault cannot be applied to this circuit
        2. DUPLICATE- the faulty circuit has exactly the same gate list as an earlier fault's
        3. UNIQUE_VALID- everything else

    Returns a list of (fault, status, note) in the same order as the input.
    note is the reason for INVALID, the earlier fault ID for DUPLICATE, or "" otherwise.
    """
    results = []
    seen = {}
    for fault in faults:
        reason = fault.check(circuit)

        if reason is not None:
            results.append((fault, INVALID, reason))
            continue

        signature = circuit_signature(fault.apply(circuit))
        
        if signature in seen:
            results.append((fault, DUPLICATE, seen[signature]))
        else:
            seen[signature] = fault.get_id()
            results.append((fault, UNIQUE_VALID, ""))
    return results