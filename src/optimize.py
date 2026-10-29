"""Week 6 optimization: greedy and exact test sets for every circuit in a configuration file.

For each circuit, the Week 5 matrix file (results/matrix/RUN_<circuit>_<matrix_date>.csv) is
used to find:
    greedy test set   Matthew's deterministic greedy selector (earliest input wins ties)
    exact test set    Matthew's exact solver; PROVEN only when the search finishes,
                      NOT_PROVEN if it hits the time limit
Each selected set is then re-simulated: every fault is applied to the circuit and run on only
the selected inputs, without using the matrix, to confirm every fault is still detected.
Greedy and exact are each timed several times.

Writes:
    results/optimization/week6_summary.csv   one row per circuit
    results/optimization/week6_log.txt       run details and pass/fail checks

Run from the repository root:
    python -m src.optimize                        (uses configs/week6.json)
    python -m src.optimize configs/week6.json
"""

import csv
import os
import sys
import time
from datetime import date
from statistics import mean

from src.experiment import load_config, git_commit, bits
from src.faults import FaultGenerator, classify_faults, INVALID
from src.greedy_selector import greedy_selector_v1
from src.optimization_analysis import solve_exact_ots

DEFAULT_CONFIG = "configs/week6.json"

COLUMNS = ["run_id", "circuit_id", "faults", "inputs",
           "greedy_size", "greedy_vectors", "exact_size", "exact_vectors", "exact_status",
           "greedy_resim", "exact_resim",
           "greedy_ms_min", "greedy_ms_mean", "greedy_ms_max",
           "exact_ms_min", "exact_ms_mean", "exact_ms_max"]


def load_matrix(path):
    """Read a Week 5 matrix CSV. Returns (inputs, fault_ids, matrix) where
    matrix maps each input tuple to the set of fault IDs it detects."""
    with open(path, "r", newline="") as file:
        rows = list(csv.reader(file))
    inputs = [tuple(int(b) for b in col) for col in rows[0][1:]]
    fault_ids = [row[0] for row in rows[1:]]
    matrix = {v: set() for v in inputs}
    for row in rows[1:]:
        for v, value in zip(inputs, row[1:]):
            if value == "1":
                matrix[v].add(row[0])
    return inputs, fault_ids, matrix


def run_greedy(inputs, fault_ids, matrix):
    return greedy_selector_v1(inputs, fault_ids, matrix, trace=False)


def run_exact(fault_ids, matrix, greedy_set, timeout_s):
    """Returns (size, vectors, status). When the solver proves the greedy size is already
    the minimum, it returns no vectors, so the greedy set is the exact set."""
    size, vectors, proven, _ = solve_exact_ots(matrix, set(fault_ids), len(greedy_set), timeout_s)
    if not proven:
        return None, [], "NOT_PROVEN"
    if not vectors:
        vectors = list(greedy_set)
    return size, sorted(vectors), "PROVEN"


def resimulate(circuit, selected):
    """Apply every valid fault and run only the selected inputs. Returns the IDs of faults
    that none of the selected inputs detect (an empty list means the set is complete)."""
    missed = []
    for fault, status, _ in classify_faults(circuit, FaultGenerator(circuit).generate_all()):
        if status == INVALID:
            continue
        faulty = fault.apply(circuit)
        if not any(circuit.simulate(v) != faulty.simulate(v) for v in selected):
            missed.append(fault.get_id())
    return missed


def time_runs(function, repeats):
    """Run a function several times. Returns (min, mean, max) runtime in milliseconds."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        function()
        times.append((time.perf_counter() - start) * 1000)
    return min(times), mean(times), max(times)


def optimize_circuit(circuit_id, circuit, matrix_path, run_date, repeats, timeout_s):
    """Greedy, exact, re-simulation, and timing for one circuit. Returns (row, missed)."""
    inputs, fault_ids, matrix = load_matrix(matrix_path)

    greedy = run_greedy(inputs, fault_ids, matrix)
    exact_size, exact, status = run_exact(fault_ids, matrix, greedy, timeout_s)
    missed = {"greedy": resimulate(circuit, greedy),
              "exact": resimulate(circuit, exact) if exact else None}

    g_times = time_runs(lambda: run_greedy(inputs, fault_ids, matrix), repeats)
    e_times = time_runs(lambda: run_exact(fault_ids, matrix, greedy, timeout_s), repeats)

    row = {
        "run_id": f"RUN_{circuit_id}_{run_date}",
        "circuit_id": circuit_id,
        "faults": len(fault_ids),
        "inputs": len(inputs),
        "greedy_size": len(greedy),
        "greedy_vectors": ";".join(bits(v) for v in greedy),
        "exact_size": exact_size if exact_size is not None else "",
        "exact_vectors": ";".join(bits(v) for v in exact),
        "exact_status": status,
        "greedy_resim": "PASS" if not missed["greedy"] else "FAIL",
        "exact_resim": "-" if missed["exact"] is None else ("PASS" if not missed["exact"] else "FAIL"),
    }
    for name, values in (("greedy", g_times), ("exact", e_times)):
        for label, value in zip(("min", "mean", "max"), values):
            row[f"{name}_ms_{label}"] = round(value, 4)
    return row, missed


def main():
    from src.integrated_run import CIRCUITS

    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG
    config = load_config(path, CIRCUITS)
    os.makedirs("results/optimization", exist_ok=True)

    run_date = date.today().isoformat()
    commit = git_commit()
    rows = []
    log = [f"experiment: {config['experiment']}", f"config: {path}", f"date: {run_date}",
           f"commit: {commit}", f"matrix source: results/matrix/RUN_<circuit>_{config['matrix_date']}.csv",
           f"timing repeats: {config['timing_repeats']}", f"exact time limit (s): {config['exact_timeout_s']}", ""]

    print(f"\nExperiment {config['experiment']} ({path}), commit {commit}")
    for circuit_id in config["circuits"]:
        matrix_path = f"results/matrix/RUN_{circuit_id}_{config['matrix_date']}.csv"
        row, missed = optimize_circuit(circuit_id, CIRCUITS[circuit_id](), matrix_path, run_date,
                                       config["timing_repeats"], config["exact_timeout_s"])
        rows.append(row)
        log.append(f"{row['run_id']}: greedy {row['greedy_size']} [{row['greedy_vectors']}], "
                   f"exact {row['exact_size']} [{row['exact_vectors']}] {row['exact_status']}, "
                   f"re-simulation greedy {row['greedy_resim']} (missed {missed['greedy']}), "
                   f"exact {row['exact_resim']}")
        print(f"  {circuit_id:17} greedy {row['greedy_size']}  exact {row['exact_size']} {row['exact_status']:10} "
              f"re-sim {row['greedy_resim']}/{row['exact_resim']}  greedy {row['greedy_ms_mean']:.3f} ms  "
              f"exact {row['exact_ms_mean']:.3f} ms")

    with open("results/optimization/week6_summary.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with open("results/optimization/week6_log.txt", "w") as file:
        file.write("\n".join(log) + "\n")
    print("  saved results/optimization/week6_summary.csv and week6_log.txt")


if __name__ == "__main__":
    main()