import ast
import csv
import json
import time
from itertools import combinations
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

CIRCUIT_ORDER = [
    "not_gate",
    "cnot_gate",
    "xor",
    "toffoli_gate",
    "fredkin_gate",
    "fredkin7",
    "half_adder",
    "all_gates",
    "graycode6",
    "ham7",
]


def parse_detection_matrix(raw_matrix: dict) -> dict:
    """Converts string keys '(0, 1)' to bit-tuples and fault lists to sets."""
    return {
        ast.literal_eval(vec_str): set(fault_list)
        for vec_str, fault_list in raw_matrix.items()
    }


def solve_exact_ots(matrix: dict, total_faults: set, gts_size: int, timeout_s: float = 10.0):
    """
    Proves the exact Optimal Test Set (OTS) size using signature-class compression
    and pruned branch-and-bound search.
    Returns: (ots_size, ots_vectors, is_proven_exact, runtime_ms)
    """
    t0 = time.perf_counter()
    if not total_faults:
        return 0, [], True, 0.0

    # Compress columns to unique fault signatures to speed up exact set cover
    fault_to_vecs = {f: set() for f in total_faults}
    for vec, f_set in matrix.items():
        for f in f_set:
            if f in fault_to_vecs:
                fault_to_vecs[f].add(vec)

    unique_signatures = list({frozenset(v_set): f for f, v_set in fault_to_vecs.items()}.values())
    num_sigs = len(unique_signatures)
    sig_index = {f: i for i, f in enumerate(unique_signatures)}

    # Convert each vector's coverage of unique signature classes into a bitmask
    vec_masks = {}
    for vec, f_set in sorted(matrix.items()):
        mask = 0
        for f in f_set:
            if f in sig_index:
                mask |= (1 << sig_index[f])
        if mask > 0:
            vec_masks[vec] = mask

    # Prune dominated vectors (if vec A is a subset of vec B, keep B)
    items = sorted(vec_masks.items(), key=lambda x: (- bin(x[1]).count("1"), x[0]))
    pruned = []
    for vec_a, mask_a in items:
        if not any((mask_a & mask_b) == mask_a and vec_a != vec_b for vec_b, mask_b in pruned):
            pruned.append((vec_a, mask_a))

    target_mask = (1 << num_sigs) - 1
    max_single = max((bin(m).count("1") for _, m in pruned), default=0)

    # Trivial 1-vector check
    for vec, mask in pruned:
        if mask == target_mask:
            dt = (time.perf_counter() - t0) * 1000.0
            return 1, [vec], True, dt

    if gts_size <= 2:
        dt = (time.perf_counter() - t0) * 1000.0
        return gts_size, [], True, dt

    # Test target sizes k = 2 .. gts_size - 1
    # If none exist, then OTS == gts_size is mathematically proven
    n_pruned = len(pruned)
    masks_only = [m for _, m in pruned]
    popcounts = [bin(m).count("1") for m in masks_only]

    # Suffix OR masks for instant pruning
    suffix_or = [0] * (n_pruned + 1)
    for i in range(n_pruned - 1, -1, -1):
        suffix_or[i] = suffix_or[i + 1] | masks_only[i]

    timed_out = False

    def search(k_remaining: int, start_idx: int, current_mask: int, chosen_indices: list):
        nonlocal timed_out
        if (time.perf_counter() - t0) > timeout_s:
            timed_out = True
            return None
        if current_mask == target_mask:
            return chosen_indices
        if k_remaining == 0 or start_idx >= n_pruned:
            return None
        if (current_mask | suffix_or[start_idx]) != target_mask:
            return None

        # Upper bound on remaining uncovered bits vs max possible bits in k_remaining steps
        uncovered_count = num_sigs - bin(current_mask).count("1")
        if start_idx + k_remaining > n_pruned:
            return None
        max_possible_add = sum(popcounts[start_idx : start_idx + k_remaining])
        if max_possible_add < uncovered_count:
            return None

        for idx in range(start_idx, n_pruned - k_remaining + 1):
            new_mask = current_mask | masks_only[idx]
            if new_mask == current_mask:
                continue
            res = search(k_remaining - 1, idx + 1, new_mask, chosen_indices + [idx])
            if res is not None:
                return res
            if timed_out:
                return None
        return None

    for k in range(2, gts_size):
        res = search(k, 0, 0, [])
        if timed_out:
            dt = (time.perf_counter() - t0) * 1000.0
            return None, [], False, dt
        if res is not None:
            dt = (time.perf_counter() - t0) * 1000.0
            ots_vecs = [pruned[i][0] for i in res]
            return k, ots_vecs, True, dt

    dt = (time.perf_counter() - t0) * 1000.0
    return gts_size, [], True, dt


def build_greedy_trace(matrix: dict, selected_vectors: list, total_faults: set) -> list:
    """Reconstructs the step-by-step greedy fault coverage trace."""
    covered_so_far = set()
    total_count = len(total_faults)
    trace = []

    for step_idx, vec_list in enumerate(selected_vectors, start=1):
        vec_tuple = tuple(vec_list)
        detected_by_vec = matrix.get(vec_tuple, set())
        newly_covered = sorted(list(detected_by_vec - covered_so_far))
        covered_so_far.update(detected_by_vec)
        cum_cov = (len(covered_so_far) / total_count) * 100.0 if total_count else 100.0

        trace.append({
            "step": step_idx,
            "vector_tuple": str(vec_tuple),
            "vector_bits": "".join(map(str, vec_tuple)),
            "total_detected_by_vector": len(detected_by_vec),
            "newly_covered_count": len(newly_covered),
            "cumulative_covered_count": len(covered_so_far),
            "total_unique_valid_faults": total_count,
            "cumulative_coverage_pct": round(cum_cov, 2),
            "newly_covered_faults": newly_covered,
        })

    return trace


def export_vhdl_vectors(traces_by_circuit: dict, out_txt: Path, out_csv: Path):
    """Exports selected test vectors in both VHDL constant array syntax and CSV format."""
    lines = [
        "-- ============================================================================",
        "-- WEEK 6 DELIVERABLE: VHDL HARDWARE TESTBENCH VECTOR LIST",
        "-- Generated automatically from locked integrated_run_<circuit>.json outputs",
        "-- ============================================================================\n",
    ]
    csv_rows = []

    for circuit_id, info in traces_by_circuit.items():
        wires = info["num_wires"]
        trace = info["trace"]
        lines.append(f"-- Circuit: {circuit_id} ({wires} wires, {len(trace)} selected vectors)")
        lines.append(f"type {circuit_id.lower()}_vec_array is array (0 to {len(trace) - 1}) of std_logic_vector({wires - 1} downto 0);")
        lines.append(f"constant {circuit_id}_TEST_VECTORS : {circuit_id.lower()}_vec_array := (")

        for i, step_info in enumerate(trace):
            bits = step_info["vector_bits"]
            comma = "," if i < len(trace) - 1 else ""
            lines.append(
                f'    {i} => "{bits}"{comma} -- Step {step_info["step"]}: '
                f'+{step_info["newly_covered_count"]} faults '
                f'({step_info["cumulative_coverage_pct"]:.2f}% cum. coverage)'
            )
            csv_rows.append({
                "circuit_id": circuit_id,
                "num_wires": wires,
                "selection_step": step_info["step"],
                "vector_tuple": step_info["vector_tuple"],
                "vhdl_bit_literal": bits,
                "newly_covered_faults": step_info["newly_covered_count"],
                "cumulative_coverage_pct": step_info["cumulative_coverage_pct"],
            })
        lines.append(");\n")

    out_txt.write_text("\n".join(lines), encoding="utf-8")

    if csv_rows:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)


def generate_figures(summary_rows: list, traces_by_circuit: dict, results_dir: Path):
    """Generates final-format IEEE-style optimization figures."""
    if not HAS_MATPLOTLIB or not summary_rows:
        return

    circuits = [r["circuit_id"] for r in summary_rows]
    exhaustive = [r["exhaustive_vectors_2n"] for r in summary_rows]
    gts = [r["gts_size"] for r in summary_rows]
    reduction = [r["reduction_pct"] for r in summary_rows]
    retention = [r["retention_pct"] for r in summary_rows]
    runtimes = [r["greedy_runtime_ms"] for r in summary_rows]

    x = np.arange(len(circuits))

    # Figure 1: Exhaustive (2^n) vs. GTS/OTS Vector Counts (Log Scale)
    fig, ax = plt.subplots(figsize=(10, 5))
    w = 0.36
    ax.bar(x - w / 2, exhaustive, width=w, label="Exhaustive Suite ($2^n$)", color="#4C72B0")
    ax.bar(x + w / 2, gts, width=w, label="Greedy Test Set (GTS)", color="#55A868")
    ax.set_yscale("log", base=2)
    ax.set_xticks(x)
    ax.set_xticklabels(circuits, rotation=30, ha="right")
    ax.set_ylabel("Number of Test Vectors ($\log_2$ scale)")
    ax.set_title("Exhaustive ($2^n$) vs. Optimized Test-Set Size (GTS)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(results_dir / "fig1_exhaustive_vs_gts.png", dpi=300)
    plt.close(fig)

    # Figure 2: Test-Set Reduction (%) vs. Retention (%)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x, reduction, label="Test-Set Reduction (%)", color="#2B5C8F")
    ax.bar(x, retention, bottom=reduction, label="Test-Set Retention (%)", color="#D95F02")
    ax.set_xticks(x)
    ax.set_xticklabels(circuits, rotation=30, ha="right")
    ax.set_ylabel("Percentage of Exhaustive Suite (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Test-Set Reduction vs. Retention Across Reversible Circuits")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(results_dir / "fig2_reduction_vs_retention.png", dpi=300)
    plt.close(fig)

    # Figure 3: Greedy Convergence Traces (Cumulative Coverage vs. Selection Step)
    fig, ax = plt.subplots(figsize=(8, 5))
    multi_step = ["HALF_ADDER", "ALL_GATES", "GRAYCODE6", "HAM7"]
    markers = ["o", "s", "^", "D"]
    for idx, cid in enumerate(multi_step):
        if cid in traces_by_circuit:
            tr = traces_by_circuit[cid]["trace"]
            steps = [0] + [s["step"] for s in tr]
            covs = [0.0] + [s["cumulative_coverage_pct"] for s in tr]
            ax.plot(steps, covs, marker=markers[idx % len(markers)], linewidth=2, label=cid)
    ax.set_xlabel("Greedy Selection Step ($k$)")
    ax.set_ylabel("Cumulative Fault Coverage (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Greedy Vector Selection Convergence Traces")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(results_dir / "fig3_greedy_convergence_traces.png", dpi=300)
    plt.close(fig)

    # Figure 4: Greedy Runtime Scaling (ms)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x, runtimes, color="#8172B2")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(circuits, rotation=30, ha="right")
    ax.set_ylabel("Greedy Selection Runtime (ms, log scale)")
    ax.set_title("Greedy Test-Set Selection Runtime Across Benchmarks")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(results_dir / "fig4_runtime_scaling.png", dpi=300)
    plt.close(fig)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    results_dir = repo_root / "results"

    summary_rows = []
    traces_by_circuit = {}

    print("\n" + "=" * 115)
    print("WEEK 6 OPTIMIZATION ANALYSIS: GTS, OTS, REDUCTION, RETENTION, PROVEN GAP & TRACES")
    print("=" * 115)

    for circuit_key in CIRCUIT_ORDER:
        json_path = results_dir / f"integrated_run_{circuit_key}.json"
        if not json_path.exists():
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        circuit_id = data["circuit_id"]
        run_id = data["run_id"]
        num_wires = data["num_wires"]
        num_gates = len(data["gates"])
        summary = data["summary"]

        matrix = parse_detection_matrix(data["detection_matrix"])
        uv_faults = {
            f["fault_id"]
            for f in data.get("faults", [])
            if f.get("status") == "UNIQUE_VALID"
        }

        selected_vecs = data.get("selected_vectors", [])
        total_vecs = summary["total_vectors"]
        gts_size = len(selected_vecs)

        # Reduction & Retention
        reduction_pct = (1.0 - (gts_size / total_vecs)) * 100.0 if total_vecs else 0.0
        retention_pct = (gts_size / total_vecs) * 100.0 if total_vecs else 0.0
        greedy_runtime_ms = summary.get("greedy_runtime_ms", 0.0)

        # Exact OTS & Proven GAP check
        ots_size, _, is_proven, ots_runtime_ms = solve_exact_ots(
            matrix, uv_faults, gts_size, timeout_s=10.0
        )

        # Rule: Use GAP only for proven exact outcomes
        if is_proven and ots_size is not None:
            ots_display = str(ots_size)
            gap_vectors = str(gts_size - ots_size)
            gap_pct = f"{((gts_size - ots_size) / ots_size) * 100.0:.2f}%"
            proof_status = "PROVEN_EXACT"
        else:
            ots_display = "UNPROVEN"
            gap_vectors = "N/A (Unproven)"
            gap_pct = "N/A (Unproven)"
            proof_status = "TIMEOUT_UNPROVEN"

        # Build step-by-step selection trace
        trace = build_greedy_trace(matrix, selected_vecs, uv_faults)
        traces_by_circuit[circuit_id] = {
            "run_id": run_id,
            "num_wires": num_wires,
            "num_gates": num_gates,
            "gts_size": gts_size,
            "ots_size": ots_display,
            "proof_status": proof_status,
            "trace": trace,
        }

        row_record = {
            "run_id": run_id,
            "circuit_id": circuit_id,
            "wires": num_wires,
            "gates": num_gates,
            "unique_valid_faults": len(uv_faults),
            "exhaustive_vectors_2n": total_vecs,
            "gts_size": gts_size,
            "ots_size": ots_display,
            "optimality_gap_vectors": gap_vectors,
            "optimality_gap_pct": gap_pct,
            "ots_proof_status": proof_status,
            "reduction_pct": round(reduction_pct, 2),
            "retention_pct": round(retention_pct, 2),
            "greedy_runtime_ms": round(greedy_runtime_ms, 6),
            "ots_solver_runtime_ms": round(ots_runtime_ms, 3),
        }
        summary_rows.append(row_record)

        print(
            f"{circuit_id:<13} | 2^n: {total_vecs:>3} | "
            f"GTS: {gts_size:>2} | OTS: {ots_display:>8} | "
            f"GAP: {gap_vectors:>14} | "
            f"Red: {reduction_pct:>6.2f}% | Ret: {retention_pct:>6.2f}% | "
            f"Greedy: {greedy_runtime_ms:>8.4f} ms"
        )

    # Save Optimization Summary Table CSV
    csv_path = results_dir / "optimization_summary_table.csv"
    if summary_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    # Save Greedy Selection Traces JSON
    traces_path = results_dir / "optimization_traces.json"
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces_by_circuit, f, indent=2)

    # Export VHDL Vector Lists
    vhdl_txt_path = results_dir / "vhdl_test_vectors.txt"
    vhdl_csv_path = results_dir / "vhdl_test_vectors.csv"
    export_vhdl_vectors(traces_by_circuit, vhdl_txt_path, vhdl_csv_path)

    # Generate Final-Format Figures
    generate_figures(summary_rows, traces_by_circuit, results_dir)

    print("=" * 115)
    print(f"Exported Optimization Table: {csv_path}")
    print(f"Exported Selection Traces:   {traces_path}")
    print(f"Exported VHDL Vector List:   {vhdl_txt_path}")
    print("=" * 115 + "\n")


if __name__ == "__main__":
    main()