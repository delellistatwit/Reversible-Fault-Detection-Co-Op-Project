"""Apply every fault model to every gate type and record which inputs detect each fault.

Each gate is placed alone on its own wires plus one spare wire, so that
control-line faults have somewhere to move.

Run from the repository root:
    python -m src.gate_fault_report

Writes results/gate_faults.json and prints a summary.
"""

import json
import os

from src.circuit import Circuit
from src.gate_specs import GATE_SPECS, build_single_gate, gate_instance_id
from src.faults import FaultGenerator, classify_faults, UNIQUE_VALID


def gate_report(type_id):
    gate = build_single_gate(type_id)
    circuit = Circuit(len(gate.wires) + 1)          # one spare wire
    circuit.add_gate(gate)

    correct = circuit.truth_table()
    faults = []
    for fault, status, note in classify_faults(circuit, FaultGenerator(circuit).generate_all()):
        entry = {"fault_id": fault.get_id(), "type": fault.fault_type, "status": status, "note": note}
        if status == UNIQUE_VALID:
            faulty = fault.apply(circuit).truth_table()
            entry["detected_by"] = [list(v) for (v, good), (_, bad) in zip(correct, faulty) if good != bad]
        faults.append(entry)

    return {
        "gate_type": type_id,
        "gate_id": gate_instance_id(0, gate),
        "wires": gate.wires,
        "spare_wire": circuit.num_wires - 1,
        "num_wires": circuit.num_wires,
        "equation": GATE_SPECS[type_id]["equation"],
        "faults": faults,
    }


def main():
    report = [gate_report(type_id) for type_id in GATE_SPECS]

    os.makedirs("results", exist_ok=True)
    with open("results/gate_faults.json", "w") as file:
        json.dump(report, file, indent=2)

    print("Faults per gate type (gate alone, plus one spare wire)")
    for r in report:
        counts = {}
        for f in r["faults"]:
            counts[f["type"]] = counts.get(f["type"], 0) + 1
        undetectable = [f["fault_id"] for f in r["faults"] if f["status"] == UNIQUE_VALID and not f["detected_by"]]
        print(f"\n{r['gate_id']}  wires {r['wires']}  spare wire {r['spare_wire']}")
        print(f"  faults: {len(r['faults'])}  {counts}  undetectable: {undetectable}")
        for f in r["faults"]:
            detected = f.get("detected_by", [])
            print(f"  {f['fault_id']:22} {f['status']:13} detected by {len(detected)} of {2 ** r['num_wires']} inputs")
    print("\nsaved to results/gate_faults.json")


if __name__ == "__main__":
    main()