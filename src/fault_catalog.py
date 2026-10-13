"""Fault catalog: every fault for every circuit, one row per fault.

Each row records the fault's ID, type, location, status (INVALID, DUPLICATE,
or UNIQUE_VALID), and which inputs detect it. Bit strings list wire 0 first.

Run from the repository root:
    python -m src.fault_catalog                 (every circuit)
    python -m src.fault_catalog HALF_ADDER      (only the circuits named)

Writes results/fault_catalog_<circuit>.csv and prints a summary.
"""

import csv
import os
import sys
from datetime import date

from src.faults import FaultGenerator, classify_faults, UNIQUE_VALID, DUPLICATE
from src.gate_specs import gate_instance_id

COLUMNS = ["run_id", "circuit_id", "fault_id", "fault_type", "gate_id", "location",
           "status", "note", "detected_count", "total_vectors", "detected_by"]


def bits(vector):
    """Turn (1, 0, 1) into "101"."""
    return "".join(str(b) for b in vector)


def build_catalog(circuit_id, circuit, run_date=None):
    """Return one catalog row (a dict) per generated fault, in generator order."""
    run_id = f"RUN_{circuit_id}_{run_date or date.today().isoformat()}"
    correct = circuit.truth_table()
    detected = {}          # fault ID -> list of detecting inputs
    rows = []

    for fault, status, note in classify_faults(circuit, FaultGenerator(circuit).generate_all()):
        fault_id = fault.get_id()
        g = fault.location[0]
        gate_id = gate_instance_id(g, circuit.gates[g]) if g < len(circuit.gates) else ""

        if status == UNIQUE_VALID:
            faulty = fault.apply(circuit).truth_table()
            detected[fault_id] = [bits(v) for (v, good), (_, bad) in zip(correct, faulty) if good != bad]
            found = detected[fault_id]
        elif status == DUPLICATE:
            found = detected[note]          # same circuit as the earlier fault named in note
        else:
            found = []                      # invalid faults are never simulated

        rows.append({
            "run_id": run_id,
            "circuit_id": circuit_id,
            "fault_id": fault_id,
            "fault_type": fault.fault_type,
            "gate_id": gate_id,
            "location": " ".join(str(n) for n in fault.location),
            "status": status,
            "note": note,
            "detected_count": len(found),
            "total_vectors": len(correct),
            "detected_by": ";".join(found),
        })
    return rows


def write_catalog(rows, path):
    """Save catalog rows as a CSV file."""
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    from src.integrated_run import CIRCUITS

    os.makedirs("results", exist_ok=True)
    print("\nFault catalog")
    for circuit_id in sys.argv[1:] or CIRCUITS:
        rows = build_catalog(circuit_id, CIRCUITS[circuit_id]())
        path = f"results/fault_catalog_{circuit_id.lower()}.csv"
        write_catalog(rows, path)

        counts = {}
        for r in rows:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        undetectable = sum(1 for r in rows if r["status"] == UNIQUE_VALID and r["detected_count"] == 0)
        print(f"  {circuit_id:13} {len(rows):4} faults  {counts}  undetectable: {undetectable}  -> {path}")


if __name__ == "__main__":
    main()