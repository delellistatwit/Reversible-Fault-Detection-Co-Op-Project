# Wire values. Wires start as 0 or 1; the V and V+ gates can also put a wire in a
# halfway state. The four values form a loop: 0 -> V0 -> 1 -> V1 -> 0.
#   V moves one step forward, V+ one step back, and NOT moves two steps.
V0 = "+"            # halfway state reached from 0 (V applied to 0)
V1 = "-"            # halfway state reached from 1 (V applied to 1)
UNKNOWN = "?"       # result when a control wire holds a halfway value
CYCLE = (0, V0, 1, V1)


def step(value, steps):
    """Move a wire value around the loop 0 -> V0 -> 1 -> V1 -> 0. UNKNOWN stays UNKNOWN."""
    if value not in CYCLE:
        return UNKNOWN
    return CYCLE[(CYCLE.index(value) + steps) % 4]


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
        """Return a new tuple of bits after this gate acts on them. Each gate type overrides this."""
        raise NotImplementedError


class NOTGate(Gate):
    #Flips target wire

    def __init__(self, target):
        super().__init__("NOT", [target])
        self.target = target

    def apply(self, bits):
        """Flip the target wire."""
        bits = list(bits)
        bits[self.target] = step(bits[self.target], 2)
        return tuple(bits)

class CNOTGate(Gate):
    #Flips the target wire if control wire = 1 (on)

    def __init__(self, control, target):
        super().__init__("CNOT", [control, target])
        self.control = control
        self.target = target

    def apply(self, bits):
        """Flip the target wire if the control wire is 1."""
        bits = list(bits)
        if bits[self.control] == 1:
            bits[self.target] = step(bits[self.target], 2)
        elif bits[self.control] != 0:
            bits[self.target] = UNKNOWN            # control is in a halfway state
        return tuple(bits)

class ToffoliGate(Gate):
    #Flips the target wire if both control wires are 1 (on)

    def __init__(self, control1, control2, target):
        super().__init__("TOFFOLI", [control1, control2, target])
        self.control1 = control1
        self.control2 = control2
        self.target = target

    def apply(self, bits):
        """Flip the target wire if both control wires are 1."""
        bits = list(bits)
        if bits[self.control1] == 1 and bits[self.control2] == 1:
            bits[self.target] ^= 1
        return tuple(bits)


class FredkinGate(Gate):
    #Swaps the two target wires if the control wire is 1 (on)

    def __init__(self, control, swap1, swap2):
        super().__init__("FREDKIN", [control, swap1, swap2])
        self.control = control
        self.swap1 = swap1
        self.swap2 = swap2

    def apply(self, bits):
        """Swap swap1 and swap2 if the control wire is 1."""
        bits = list(bits)
        if bits[self.control] == 1:
            bits[self.swap1], bits[self.swap2] = bits[self.swap2], bits[self.swap1]
        return tuple(bits)

class PeresGate(Gate):
    #A Toffoli followed by a CNOT, packed into one gate

    def __init__(self, a, b, c):
        super().__init__("PERES", [a, b, c])
        self.a = a
        self.b = b
        self.c = c

    def apply(self, bits):
        """P = A, Q = A XOR B, R = (A AND B) XOR C."""
        bits = list(bits)
        A, B, C = bits[self.a], bits[self.b], bits[self.c]
        bits[self.b] = A ^ B
        bits[self.c] = (A & B) ^ C
        return tuple(bits)


class HNGGate(Gate):
    #One gate that works as a full adder when D starts at 0

    def __init__(self, a, b, c, d):
        super().__init__("HNG", [a, b, c, d])
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def apply(self, bits):
        """P = A, Q = B, R = A XOR B XOR C, S = ((A XOR B) AND C) XOR (A AND B) XOR D."""
        bits = list(bits)
        A, B, C, D = bits[self.a], bits[self.b], bits[self.c], bits[self.d]
        bits[self.c] = A ^ B ^ C
        bits[self.d] = ((A ^ B) & C) ^ (A & B) ^ D
        return tuple(bits)


class VGate(Gate):
    #Controlled-V: moves the target one step forward if the control is 1 (two V gates = one NOT)

    def __init__(self, control, target):
        super().__init__("V", [control, target])
        self.control = control
        self.target = target

    def apply(self, bits):
        """Move the target one step (0 -> V0 -> 1 -> V1 -> 0) if the control is 1."""
        bits = list(bits)
        if bits[self.control] == 1:
            bits[self.target] = step(bits[self.target], 1)
        elif bits[self.control] != 0:
            bits[self.target] = UNKNOWN            # control is in a halfway state
        return tuple(bits)


class VDaggerGate(Gate):
    #Controlled-V+: moves the target one step back if the control is 1 (undoes V)

    def __init__(self, control, target):
        super().__init__("V_DAG", [control, target])
        self.control = control
        self.target = target

    def apply(self, bits):
        """Move the target one step back (0 -> V1 -> 1 -> V0 -> 0) if the control is 1."""
        bits = list(bits)
        if bits[self.control] == 1:
            bits[self.target] = step(bits[self.target], -1)
        elif bits[self.control] != 0:
            bits[self.target] = UNKNOWN            # control is in a halfway state
        return tuple(bits)
