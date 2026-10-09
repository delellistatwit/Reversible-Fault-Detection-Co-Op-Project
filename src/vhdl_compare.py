"""Compare Jeramiah's VHDL (ModelSim) results with the Python simulator.

Each CSV in benchmarks/vhdl/ holds one row per simulation time step:
    gate,time_ns,<input ports...>,<output ports...>
Port names come from GATE_SPECS, so VHDL input port i is Python wire i.

Run from the repository root:
    python -m src.vhdl_compare
"""

import csv
import glob
import json
import os

from src.gate_specs import GATE_SPECS, build_single_gate


def load_vhdl_csv(path):
    """Read a VHDL result CSV, skipping comment lines that start with #."""
    with open(path, "r") as file:
        lines = [line for line in file if not line.startswith("#")]
    return list(csv.DictReader(lines))


def compare_rows(rows):
    """Compare each VHDL row with the Python gate. Returns a list of row results."""
    results = []
    for row in rows:
        type_id = row["gate"]
        spec = GATE_SPECS[type_id]
        inputs = tuple(int(row[port]) for port in spec["vhdl_inputs"])
        vhdl_out = tuple(int(row[port]) for port in spec["vhdl_outputs"])
        python_out = build_single_gate(type_id).apply(inputs)
        results.append({
            "gate": type_id,
            "time_ns": int(row["time_ns"]),
            "inputs": list(inputs),
            "vhdl": list(vhdl_out),
            "python": list(python_out),
            "match": vhdl_out == python_out,
        })
    return results


def main():
    all_results = []
    for path in sorted(glob.glob("benchmarks/vhdl/*.csv")):
        all_results.extend(compare_rows(load_vhdl_csv(path)))

    os.makedirs("results", exist_ok=True)
    with open("results/vhdl_compare.json", "w") as file:
        json.dump(all_results, file, indent=2)

    print("VHDL (ModelSim) vs Python")
    for r in all_results:
        print(f"  {r['gate']:8} t={r['time_ns']:>3} ns  in {r['inputs']}  VHDL {r['vhdl']}  Python {r['python']}  {'MATCH' if r['match'] else 'MISMATCH'}")
    matched = sum(r["match"] for r in all_results)
    print(f"  {matched} / {len(all_results)} rows match")
    print("saved to results/vhdl_compare.json")


if __name__ == "__main__":
    main()