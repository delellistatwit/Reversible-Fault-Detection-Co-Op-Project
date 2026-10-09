"""First integrated run: simulator -> fault generator -> detection matrix -> greedy selection.

Run from the repository root:
    python -m src.integrated_run

Writes results/integrated_run_<circuit>.json and prints a summary.
"""

import json
import os
from datetime import date

from src.benchmarks import build_xor, build_half_adder
from src.faults import FaultGenerator, classify_faults, UNIQUE_VALID, DUPLICATE, INVALID
from src.detectionmatrix import DetectionMatrix
from src.greedy_selector import greedy_selector_v1
from src.real_import import load_real

RUN_DATE = date.today().isoformat()
CIRCUITS = {
    "XOR": build_xor,
    "HALF_ADDER": build_half_adder,"GRAYCODE6": lambda: load_real("benchmarks/graycode6.real")[0],
    "HAM7": lambda: load_real("benchmarks/ham7.real")[0],
}


def run(circuit_id):
    circuit = CIRCUITS[circuit_id]()
    run_id = f"RUN_{circuit_id}_{RUN_DATE}"

    # 1. correct truth table
    correct = circuit.truth_table()
    vectors = [inputs for inputs, _ in correct]

    # 2. generate and classify faults
    classified = classify_faults(circuit, FaultGenerator(circuit).generate_all())
    unique = [f for f, status, _ in classified if status == UNIQUE_VALID]

    # 3. fill Matthew's detection matrix: a vector detects a fault if the outputs differ
    dm = DetectionMatrix()
    for v in vectors:
        dm.create_entry(v)
    for fault in unique:
        faulty_table = fault.apply(circuit).truth_table()
        for (v, good), (_, bad) in zip(correct, faulty_table):
            if good != bad:
                dm.create_entry(v, fault.get_id())

    # 4. greedy selection
    fault_ids = [f.get_id() for f in unique]
    selected = greedy_selector_v1(vectors, fault_ids, dm.matrix)

    detected = set().union(*dm.matrix.values())
    undetectable = [fid for fid in fault_ids if fid not in detected]

    result = {
        "run_id": run_id,
        "circuit_id": circuit_id,
        "num_wires": circuit.num_wires,
        "gates": [[g.name, g.wires] for g in circuit.gates],
        "faults": [
            {"fault_id": f.get_id(), "status": status, "note": note}
            for f, status, note in classified
        ],
        "detection_matrix": {str(v): sorted(dm.query(v)) for v in vectors},
        "selected_vectors": [list(v) for v in selected],
        "summary": {
            "total_vectors": len(vectors),
            "faults_generated": len(classified),
            "unique_valid": len(unique),
            "duplicate": sum(1 for _, s, _ in classified if s == DUPLICATE),
            "invalid": sum(1 for _, s, _ in classified if s == INVALID),
            "detectable": len(fault_ids) - len(undetectable),
            "undetectable": undetectable,
            "selected_vectors": len(selected),
        },
    }

    os.makedirs("results", exist_ok=True)
    path = f"results/integrated_run_{circuit_id.lower()}.json"
    with open(path, "w") as file:
        json.dump(result, file, indent=2)

    s = result["summary"]
    print(f"\n{run_id}")
    print(f"  vectors: {s['total_vectors']}  faults: {s['faults_generated']} "
          f"(unique-valid {s['unique_valid']}, duplicate {s['duplicate']}, invalid {s['invalid']})")
    print(f"  detectable: {s['detectable']}  undetectable: {s['undetectable']}")
    print(f"  selected vectors: {result['selected_vectors']}")
    print(f"  saved to {path}")


if __name__ == "__main__":
    for cid in CIRCUITS:
        run(cid)