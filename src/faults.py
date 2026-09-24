from src.circuit import Circuit


class Fault:
    """One fault that can be injected into a circuit.

    Only three fault types are allowed:
        REMOVE  - a gate is removed
        CONTROL - a gate's control wire is changed
        SWAP    - two wires are swapped
    """

    TYPES = ("REMOVE", "CONTROL", "SWAP")

    def __init__(self, fault_type, location):
        """
        fault_type: one of "REMOVE", "CONTROL", or "SWAP"
        location:   a tuple of numbers saying where the fault happens, for example
                    (2,)      for REMOVE:  gate 2 is removed
                    (1, 0, 2) for CONTROL: gate 1's control moves from wire 0 to wire 2
                    (0, 1)    for SWAP:    wires 0 and 1 are swapped
        """
        if fault_type not in Fault.TYPES:
            raise ValueError(f"fault_type must be one of {Fault.TYPES}, got {fault_type}")

        if not isinstance(location, tuple):
            raise TypeError(f"location must be a tuple, got {type(location).__name__}")

        for n in location:
            if not isinstance(n, int) or n < 0:
                raise ValueError(f"location values must be non-negative integers, got {n}")

        self.fault_type = fault_type
        self.location = location

    def get_id(self):
        """Return this fault's string ID, e.g. "REMOVE_G2". (Implemented next week.)"""
        raise NotImplementedError

    def apply(self, circuit):
        """Return a new faulty copy of the circuit. The original is not changed. (Implemented next week.)"""
        raise NotImplementedError


class FaultGenerator:
    """Creates every possible fault of the three allowed types for a given circuit."""

    def __init__(self, circuit):
        """
        circuit: the correct circuit to generate faults for
        """
        if not isinstance(circuit, Circuit):
            raise TypeError(f"expected a Circuit, got {type(circuit).__name__}")

        self.circuit = circuit

    def generate_removal_faults(self):
        """Return a list of REMOVE faults, one per gate. (Implemented later.)"""
        raise NotImplementedError

    def generate_control_faults(self):
        """Return a list of CONTROL faults. (Implemented later.)"""
        raise NotImplementedError

    def generate_swap_faults(self):
        """Return a list of SWAP faults. (Implemented later.)"""
        raise NotImplementedError

    def generate_all(self):
        """Return every fault from all three types in one list. (Implemented later.)"""
        raise NotImplementedError