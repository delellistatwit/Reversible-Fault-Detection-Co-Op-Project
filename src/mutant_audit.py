"""Mutant audit: checks that the generated faults (mutants) are correct and complete.

For each circuit it checks:
  1. every fault gets exactly one status (INVALID, DUPLICATE, or UNIQUE_VALID)
  2. fault counts match the formulas from the fault-module design
  3. no fault ID appears twice
  4. the generator gives the same list every time it runs
  5. every UNIQUE_VALID mutant actually changes the circuit
  6. every DUPLICATE points to an earlier UNIQUE_VALID fault with the same circuit
  7. every INVALID fault records the reason it was rejected

Run from the repository root:
    python -m src.mutant_audit                 (every circuit)
    python -m src.mutant_audit HALF_ADDER      (only the circuits named)

Writes results/mutant_audit.json and prints PASS or FAIL per circuit.
"""

import json
import os
import sys

from src.faults import (FaultGenerator, classify_faults, circuit_signature, CONTROL_ATTRS,
                        INVALID, DUPLICATE, UNIQUE_VALID)

STATUSES = (INVALID, DUPLICATE, UNIQUE_VALID)


def expected_counts(circuit):
    """Fault counts predicted by the formulas in the fault-module design.

    REMOVE:  one per gate
    CONTROL: for each control wire of each gate, one per wire the gate does not use
    SWAP:    for each gate, one per pair of wires, n * (n - 1) / 2
    """
    n = circuit.num_wires
    gates = circuit.gates
    control = sum(len(CONTROL_ATTRS.get(type(g), ())) * (n - len(g.wires)) for g in gates)
    return {"REMOVE": len(gates), "CONTROL": control, "SWAP": len(gates) * n * (n - 1) // 2}


def audit_results(circuit, faults, results):
    """Run every check on a list of faults and their classify_faults() results.

    Returns {check name: (passed, detail)}.
    """
    checks = {}

    # 1. exactly one status per fault
    bad = [f.get_id() for f, status, _ in results if status not in STATUSES]
    one_each = len(results) == len(faults) and not bad
    checks["one_status_per_fault"] = (one_each, f"{len(results)} results for {len(faults)} faults; bad statuses: {bad}")

    # 2. counts match the formulas
    actual = {"REMOVE": 0, "CONTROL": 0, "SWAP": 0}
    for f in faults:
        actual[f.fault_type] += 1
    expected = expected_counts(circuit)
    checks["counts_match_formulas"] = (actual == expected, f"expected {expected}, got {actual}")

    # 3. no repeated IDs
    ids = [f.get_id() for f in faults]
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    checks["unique_fault_ids"] = (not repeated, f"repeated: {repeated}")

    # 4. same list every run
    again = [f.get_id() for f in FaultGenerator(circuit).generate_all()]
    checks["stable_generation_order"] = (again == ids, "generator order is repeatable" if again == ids else "order changed between runs")

    # 5. unique-valid mutants change the circuit
    correct_sig = circuit_signature(circuit)
    unchanged = [f.get_id() for f, status, _ in results
                 if status == UNIQUE_VALID and circuit_signature(f.apply(circuit)) == correct_sig]
    checks["mutants_change_circuit"] = (not unchanged, f"unchanged mutants: {unchanged}")

    # 6. duplicates point to an earlier unique-valid fault with the same circuit
    earlier = {}
    broken = []
    for f, status, note in results:
        if status == UNIQUE_VALID:
            earlier[f.get_id()] = circuit_signature(f.apply(circuit))
        elif status == DUPLICATE:
            if note not in earlier or earlier[note] != circuit_signature(f.apply(circuit)):
                broken.append(f.get_id())
    checks["duplicates_valid"] = (not broken, f"bad duplicate links: {broken}")

    # 7. invalid faults say why
    no_reason = [f.get_id() for f, status, note in results if status == INVALID and not note]
    checks["invalid_have_reason"] = (not no_reason, f"invalid without a reason: {no_reason}")

    return checks


def audit_circuit(circuit):
    """Generate, classify, and audit every fault for one circuit."""
    faults = FaultGenerator(circuit).generate_all()
    results = classify_faults(circuit, faults)
    return audit_results(circuit, faults, results)


def main():
    from src.integrated_run import CIRCUITS

    report = {}
    print("\nMutant audit")
    for circuit_id in sys.argv[1:] or CIRCUITS:
        checks = audit_circuit(CIRCUITS[circuit_id]())
        passed = all(ok for ok, _ in checks.values())
        report[circuit_id] = {
            "passed": passed,
            "checks": {name: {"passed": ok, "detail": detail} for name, (ok, detail) in checks.items()},
        }
        print(f"  {circuit_id:13} {'PASS' if passed else 'FAIL'}  ({sum(ok for ok, _ in checks.values())}/{len(checks)} checks)")
        for name, (ok, detail) in checks.items():
            if not ok:
                print(f"      {name}: {detail}")

    os.makedirs("results", exist_ok=True)
    with open("results/mutant_audit.json", "w") as file:
        json.dump(report, file, indent=2)
    print("  saved to results/mutant_audit.json")


if __name__ == "__main__":
    main()