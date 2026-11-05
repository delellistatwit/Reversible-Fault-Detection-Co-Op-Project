import ast
import csv
import json
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from metrics import (
    calculate_coverage,
    calculate_density,
    calculate_multiplicity,
    find_essential_vectors,
    group_signature_classes,
)

# Ordered from smallest primary gates/circuits to largest external benchmarks
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


def extract_unique_valid_faults(data: dict) -> list:
    """Returns UNIQUE_VALID fault IDs in fixed generator order."""
    return [
        f["fault_id"]
        for f in data.get("faults", [])
        if f.get("status") == "UNIQUE_VALID"
    ]


def audit_circuit_run(data: dict, matrix: dict, unique_valid_faults: list) -> dict:
    """Audits row/column counts and fault consistency equations."""
    num_wires = data["num_wires"]
    summary = data["summary"]

    expected_rows = 2 ** num_wires
    actual_rows = len(matrix)
    summary_rows = summary["total_vectors"]

    # Eq 1: Row count consistency (|V| == 2^n)
    eq_rows_pass = (actual_rows == expected_rows == summary_rows)

    # Eq 2: Fault catalog partition (generated == unique_valid + duplicate + invalid)
    faults_gen = summary["faults_generated"]
    uv_count = summary["unique_valid"]
    dup_count = summary["duplicate"]
    inv_count = summary["invalid"]
    eq_catalog_pass = (
        faults_gen == (uv_count + dup_count + inv_count)
        and len(unique_valid_faults) == uv_count
    )

    # Eq 3: Detectability partition (unique_valid == detectable + len(undetectable))
    detectable_count = summary["detectable"]
    undetectable_list = summary["undetectable"]
    eq_detectable_pass = (uv_count == detectable_count + len(undetectable_list))

    # Eq 4: Matrix-to-Multiplicity sum identity
    mult = calculate_multiplicity(matrix)
    row_sum = sum(len(f_set) for f_set in matrix.values())
    col_sum = sum(mult.values())
    eq_density_pass = (row_sum == col_sum) and (len(mult) == detectable_count)

    all_passed = (
        eq_rows_pass
        and eq_catalog_pass
        and eq_detectable_pass
        and eq_density_pass
    )

    return {
        "expected_rows_2n": expected_rows,
        "actual_rows": actual_rows,
        "expected_cols_uv": uv_count,
        "actual_cols": len(unique_valid_faults),
        "total_ones": row_sum,
        "total_cells": actual_rows * uv_count,
        "eq1_row_count_pass": eq_rows_pass,
        "eq2_fault_catalog_pass": eq_catalog_pass,
        "eq3_detectability_pass": eq_detectable_pass,
        "eq4_matrix_sum_pass": eq_density_pass,
        "audit_status": "PASS" if all_passed else "FAIL",
    }


def save_heatmap(circuit_id: str, matrix: dict, fault_ids: list, out_path: Path):
    """Generates and saves a 2D binary heatmap of the fault-detection matrix."""
    if not HAS_MATPLOTLIB:
        return

    vectors = sorted(matrix.keys())
    num_v = len(vectors)
    num_f = len(fault_ids)

    grid = np.zeros((num_v, num_f), dtype=int)
    fault_idx = {f_id: j for j, f_id in enumerate(fault_ids)}

    for i, vec in enumerate(vectors):
        for f_id in matrix[vec]:
            if f_id in fault_idx:
                grid[i, fault_idx[f_id]] = 1

    fig_w = max(6, min(14, num_f * 0.22))
    fig_h = max(4, min(10, num_v * 0.15))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(
        grid, aspect="auto", cmap="Blues", vmin=0, vmax=1, interpolation="nearest"
    )
    ax.set_title(f"Fault-Detection Matrix Heatmap: {circuit_id} ({num_v}x{num_f})")
    ax.set_xlabel("Unique Valid Fault Index")
    ax.set_ylabel("Input Test Vector (Counting Order)")

    if num_f <= 35:
        ax.set_xticks(range(num_f))
        ax.set_xticklabels(fault_ids, rotation=90, fontsize=6)
    if num_v <= 32:
        ax.set_yticks(range(num_v))
        ax.set_yticklabels(["".join(map(str, v)) for v in vectors], fontsize=7)

    plt.colorbar(im, ax=ax, ticks=[0, 1], label="Detected (1=Yes, 0=No)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    results_dir = repo_root / "results"

    summary_rows = []
    detailed_report = {}

    print("\n" + "=" * 110)
    print("WEEK 5 BASELINE ANALYSIS & CONSISTENCY AUDIT")
    print("=" * 110)

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
        uv_faults = extract_unique_valid_faults(data)

        # 1. Audit row/column counts & consistency equations
        audit = audit_circuit_run(data, matrix, uv_faults)
        if audit["audit_status"] != "PASS":
            raise AssertionError(f"Audit failed for {circuit_id}: {audit}")

        # 2. Calculate Baseline Metrics
        coverage = calculate_coverage(matrix, uv_faults)
        density = calculate_density(matrix, uv_faults)
        multiplicity = calculate_multiplicity(matrix)
        essential_vecs = find_essential_vectors(matrix, multiplicity)
        sig_classes = group_signature_classes(matrix)

        selected_vecs = data.get("selected_vectors", [])
        num_selected = len(selected_vecs)
        total_vecs = summary["total_vectors"]
        reduction_pct = (
            (1.0 - (num_selected / total_vecs)) * 100.0 if total_vecs else 0.0
        )
        runtime_ms = summary.get("greedy_runtime_ms", 0.0)

        mult_values = list(multiplicity.values())
        min_mult = min(mult_values) if mult_values else 0
        avg_mult = sum(mult_values) / len(mult_values) if mult_values else 0.0
        max_mult = max(mult_values) if mult_values else 0

        # 3. Save Heatmap Figure
        heatmap_path = results_dir / f"heatmap_{circuit_key}.png"
        save_heatmap(circuit_id, matrix, uv_faults, heatmap_path)

        row_record = {
            "run_id": run_id,
            "circuit_id": circuit_id,
            "wires": num_wires,
            "gates": num_gates,
            "total_vectors_2n": total_vecs,
            "faults_generated": summary["faults_generated"],
            "unique_valid_faults": summary["unique_valid"],
            "duplicate_faults": summary["duplicate"],
            "invalid_faults": summary["invalid"],
            "detectable_faults": summary["detectable"],
            "undetectable_faults": len(summary["undetectable"]),
            "total_matrix_cells": audit["total_cells"],
            "total_positive_detections": audit["total_ones"],
            "coverage_pct": round(coverage, 2),
            "density_pct": round(density, 2),
            "min_multiplicity": min_mult,
            "avg_multiplicity": round(avg_mult, 2),
            "max_multiplicity": max_mult,
            "essential_vector_count": len(essential_vecs),
            "signature_class_count": len(sig_classes),
            "greedy_selected_vectors": num_selected,
            "test_set_reduction_pct": round(reduction_pct, 2),
            "greedy_runtime_ms": round(runtime_ms, 6),
            "audit_status": audit["audit_status"],
        }
        summary_rows.append(row_record)

        detailed_report[circuit_id] = {
            "metadata": row_record,
            "audit_checks": audit,
            "essential_vectors": [list(v) for v in essential_vecs],
            "signature_classes": sig_classes,
            "multiplicity": multiplicity,
        }

        print(
            f"[{audit['audit_status']}] {circuit_id:<13} | "
            f"Matrix: {total_vecs:>3}x{summary['unique_valid']:<3} | "
            f"1s: {audit['total_ones']:>5} | "
            f"Cov: {coverage:>6.2f}% | "
            f"Den: {density:>6.2f}% | "
            f"Mult(min/avg/max): {min_mult:>2}/{avg_mult:>5.2f}/{max_mult:<3} | "
            f"Ess: {len(essential_vecs):>1} | "
            f"Sig: {len(sig_classes):>3} | "
            f"Sel: {num_selected:>2} ({reduction_pct:>5.2f}%)"
        )

    csv_path = results_dir / "baseline_summary_table.csv"
    if summary_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    json_out_path = results_dir / "baseline_detailed_metrics.json"
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(detailed_report, f, indent=2)

    print("=" * 110)
    print(f"Saved CSV Baseline Table: {csv_path}")
    print(f"Saved JSON Dataset:       {json_out_path}")
    print("=" * 110 + "\n")


if __name__ == "__main__":
    main()