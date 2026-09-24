class Gate:
    """Base class for all reversible gates

    A circuit is a list of bits, where each index is one wire
    Each gate reads and changes some of those wires
    """

    def __init__(self, name, wires):
        """
        name:  the gate type, ex "NOT"
        wires: every wire index this gate uses
        """
        for w in wires:
            if not isinstance(w, int) or w < 0:
                raise ValueError(f"{name}: wire index must be a non-negative integer, got {w}")

        if len(set(wires)) != len(wires):
            raise ValueError(f"{name}: the same wire cannot be used twice in one gate")

        self.name = name
        self.wires = wires

    def apply(self, bits):
        """Return a new list of bits after this gate acts on them."""
        raise NotImplementedError


class NOTGate(Gate):
    #Flips target wire

    def __init__(self, target):
        super().__init__("NOT", [target])
        self.target = target

    def apply(self, bits):
        """Flip the target wire (Added next week)"""
        raise NotImplementedError

class CNOTGate(Gate):
    #Flips the target wire if control wire = 1 (on)

    def __init__(self, control, target):
        super().__init__("CNOT", [control, target])
        self.control = control
        self.target = target

    def apply(self, bits):
        """Flip the target wire if the control wire is 1 (Added next week)"""
        raise NotImplementedError

class ToffoliGate(Gate):
    #Flips the target wire if both control wires are 1 (on)

    def __init__(self, control1, control2, target):
        super().__init__("TOFFOLI", [control1, control2, target])
        self.control1 = control1
        self.control2 = control2
        self.target = target

    def apply(self, bits):
        """Flip the target wire if both control wires are 1. (Implemented next week.)"""
        raise NotImplementedError


class FredkinGate(Gate):
    #Swaps the two target wires if the control wire is 1 (on)

    def __init__(self, control, swap1, swap2):
        super().__init__("FREDKIN", [control, swap1, swap2])
        self.control = control
        self.swap1 = swap1
        self.swap2 = swap2

    def apply(self, bits):
        """Swap swap1 and swap2 if the control wire is 1. (Implemented next week.)"""
        raise NotImplementedError