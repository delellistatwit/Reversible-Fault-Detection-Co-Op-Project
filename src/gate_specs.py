"""Locked schema and stable IDs for every gate type.

Each gate type has one entry in GATE_SPECS. The entry says which fields the
gate stores, which of them are controls and targets, how they map to
Jeramiah's VHDL ports, and the reference equation from his specification.
Nothing here may change without notifying the team.
"""

from itertools import product

from src.gates import NOTGate, CNOTGate, ToffoliGate, FredkinGate


GATE_SPECS = {
    "NOT": {
        "class": NOTGate,
        "fields": ("target",),
        "controls": (),
        "targets": ("target",),
        "vhdl_entity": "NOT_gate",
        "vhdl_inputs": ("A",),
        "vhdl_outputs": ("Y",),
        "equation": "Y = NOT A",
        "reference": lambda a: (1 - a,),
    },
    "CNOT": {
        "class": CNOTGate,
        "fields": ("control", "target"),
        "controls": ("control",),
        "targets": ("target",),
        "vhdl_entity": "Feynman_gate",
        "vhdl_inputs": ("A", "B"),
        "vhdl_outputs": ("P", "Q"),
        "equation": "P = A, Q = A XOR B",
        "reference": lambda a, b: (a, a ^ b),
    },
    "TOFFOLI": {
        "class": ToffoliGate,
        "fields": ("control1", "control2", "target"),
        "controls": ("control1", "control2"),
        "targets": ("target",),
        "vhdl_entity": "Toffoli_gate",
        "vhdl_inputs": ("A", "B", "C"),
        "vhdl_outputs": ("P", "Q", "R"),
        "equation": "P = A, Q = B, R = C XOR (A AND B)",
        "reference": lambda a, b, c: (a, b, c ^ (a & b)),
    },
    "FREDKIN": {
        "class": FredkinGate,
        "fields": ("control", "swap1", "swap2"),
        "controls": ("control",),
        "targets": ("swap1", "swap2"),
        "vhdl_entity": "Fredkin_gate",
        "vhdl_inputs": ("C", "A", "B"),
        "vhdl_outputs": ("P", "Q", "R"),
        "equation": "P = C, Q = B if C else A, R = A if C else B",
        "reference": lambda c, a, b: (c, b if c else a, a if c else b),
    },
}


def gate_type_id(gate):
    """Return the stable type ID of a gate, e.g. "TOFFOLI"."""
    for type_id, spec in GATE_SPECS.items():
        if type(gate) is spec["class"]:
            return type_id
    raise ValueError(f"{type(gate).__name__} is not a locked gate type")


def gate_instance_id(index, gate):
    """Return the stable ID of a gate inside a circuit, e.g. "G1_CNOT"."""
    return f"G{index}_{gate_type_id(gate)}"


def check_gate_schema(gate):
    """Check that a gate matches its locked schema. Returns True or raises ValueError."""
    type_id = gate_type_id(gate)
    spec = GATE_SPECS[type_id]

    if gate.name != type_id:
        raise ValueError(f"name is {gate.name}, schema requires {type_id}")

    for field in spec["fields"]:
        if not hasattr(gate, field):
            raise ValueError(f"{type_id} is missing field '{field}'")

    expected_wires = [getattr(gate, field) for field in spec["fields"]]
    if gate.wires != expected_wires:
        raise ValueError(f"{type_id} wires {gate.wires} do not match fields {expected_wires}")

    if len(set(gate.wires)) != len(gate.wires):
        raise ValueError(f"{type_id} uses the same wire twice")

    return True


def build_single_gate(type_id):
    """Build one gate of the given type on wires 0, 1, 2, ... in field order."""
    spec = GATE_SPECS[type_id]
    return spec["class"](*range(len(spec["fields"])))


def cross_check_with_vhdl():
    """Compare every gate's Python output with Jeramiah's reference equation for every input.

    Returns {type_id: {"rows": n, "mismatches": [input, ...]}}.
    Python wire i corresponds to VHDL input port i and output port i.
    """
    results = {}
    for type_id, spec in GATE_SPECS.items():
        gate = build_single_gate(type_id)
        n = len(spec["fields"])
        mismatches = []
        for inputs in product((0, 1), repeat=n):
            if gate.apply(inputs) != spec["reference"](*inputs):
                mismatches.append(inputs)
        results[type_id] = {"rows": 2 ** n, "mismatches": mismatches}
    return results


if __name__ == "__main__":
    print("Gate schema and VHDL cross-check")
    for type_id, result in cross_check_with_vhdl().items():
        spec = GATE_SPECS[type_id]
        status = "MATCH" if not result["mismatches"] else f"MISMATCH {result['mismatches']}"
        print(f"  {type_id:8} {spec['vhdl_entity']:13} {spec['equation']:45} {result['rows']} rows  {status}")