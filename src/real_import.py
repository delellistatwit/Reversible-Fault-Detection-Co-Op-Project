"""Import reversible circuits from RevLib .real files.

Supported gates (the NCT library):
    t1 x        NOT on x
    t2 c x      CNOT, control c, target x
    t3 c1 c2 x  Toffoli, controls c1 and c2, target x

Wires are numbered in the order of the .variables line (first variable = wire 0).
"""

from src.circuit import Circuit
from src.gates import NOTGate, CNOTGate, ToffoliGate

GATE_TYPES = {"t1": NOTGate, "t2": CNOTGate, "t3": ToffoliGate}


def load_real(path):
    """Read a .real file and return (circuit, info).

    info is a dict with the variable names and the .constants and .garbage
    strings (one character per wire; "-" means a normal wire).
    Raises ValueError for unsupported gates or a badly formed file.
    """
    variables = None
    constants = None
    garbage = None
    gate_lines = []
    in_body = False

    with open(path, "r") as file:
        for line_number, raw in enumerate(file, start=1):
            line = raw.strip()
            if line == "" or line.startswith("#"):
                continue

            if line == ".begin":
                in_body = True
            elif line == ".end":
                in_body = False
            elif in_body:
                gate_lines.append((line_number, line.split()))
            elif line.startswith(".variables"):
                variables = line.split()[1:]
            elif line.startswith(".constants"):
                constants = line.split()[1]
            elif line.startswith(".garbage"):
                garbage = line.split()[1]

    if variables is None:
        raise ValueError(f"{path}: missing .variables line")

    wire_of = {name: i for i, name in enumerate(variables)}
    circuit = Circuit(len(variables))

    for line_number, parts in gate_lines:
        gate_type, names = parts[0], parts[1:]

        if gate_type not in GATE_TYPES:
            raise ValueError(f"{path} line {line_number}: unsupported gate '{gate_type}' (only t1, t2, t3 are supported)")

        expected = int(gate_type[1:])
        if len(names) != expected:
            raise ValueError(f"{path} line {line_number}: {gate_type} needs {expected} wires, got {len(names)}")

        for name in names:
            if name not in wire_of:
                raise ValueError(f"{path} line {line_number}: unknown variable '{name}'")

        wires = [wire_of[name] for name in names]
        circuit.add_gate(GATE_TYPES[gate_type](*wires))

    info = {"variables": variables, "constants": constants, "garbage": garbage}
    return circuit, info