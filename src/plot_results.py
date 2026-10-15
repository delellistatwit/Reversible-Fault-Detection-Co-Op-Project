"""Generate PNG charts from experiment JSON files in the results directory.

Run from the repository root with:
    python -m src.plot_results

Charts are written to results/plots by default. Integrated-run JSON files
include greedy-selector timings after running src.integrated_run again.
"""

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_matrix(path):
    """Load a matrix JSON object and return vector-to-fault sets and fault IDs."""
    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    raw_matrix = data.get("detection_matrix", data)
    matrix = {
        tuple(ast.literal_eval(vector)): set(faults)
        for vector, faults in raw_matrix.items()
    }
    fault_ids = set().union(*matrix.values()) if matrix else set()

    if isinstance(data, dict) and "faults" in data:
        fault_ids.update(
            fault["fault_id"]
            for fault in data["faults"]
            if fault.get("status") == "UNIQUE_VALID"
        )
    return matrix, sorted(fault_ids)


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def plot_heatmap(matrix, fault_ids, title, output_path):
    vectors = sorted(matrix)
    width = max(8, min(24, 3 + len(fault_ids) * 0.28))
    height = max(5, min(24, 2.5 + len(vectors) * 0.22))
    figure, axis = plt.subplots(figsize=(width, height), constrained_layout=True)

    if vectors and fault_ids:
        values = np.array([
            [int(fault in matrix.get(vector, set())) for fault in fault_ids]
            for vector in vectors
        ])
        image = axis.imshow(values, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
        axis.set_xticks(range(len(fault_ids)), fault_ids, rotation=65, ha="right")
        axis.set_yticks(range(len(vectors)), [str(vector) for vector in vectors])
        if values.size <= 400:
            for row in range(values.shape[0]):
                for column in range(values.shape[1]):
                    axis.text(column, row, str(values[row, column]), ha="center", va="center", fontsize=8)
        figure.colorbar(image, ax=axis, ticks=[0, 1], label="Detection")
    else:
        axis.text(0.5, 0.5, "No vectors or faults in this matrix", ha="center", va="center")
        axis.set_axis_off()

    axis.set_title(title)
    axis.set_xlabel("Fault")
    axis.set_ylabel("Input vector")
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def plot_multiplicity(matrix, fault_ids, title, output_path):
    multiplicity = Counter()
    for faults in matrix.values():
        multiplicity.update(faults)
    distribution = Counter(multiplicity.get(fault, 0) for fault in fault_ids)

    figure, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    if distribution:
        counts = sorted(distribution)
        axis.bar(counts, [distribution[count] for count in counts], color="#187f75")
        axis.set_xticks(counts)
    else:
        axis.text(0.5, 0.5, "No faults in this matrix", ha="center", va="center")
    axis.set_title(title)
    axis.set_xlabel("Vectors detecting a fault")
    axis.set_ylabel("Number of faults")
    axis.grid(axis="y", alpha=0.25)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def plot_signature_distribution(matrix, fault_ids, title, output_path):
    fault_vectors = {fault: set() for fault in fault_ids}
    for vector, faults in matrix.items():
        for fault in faults:
            fault_vectors.setdefault(fault, set()).add(vector)

    signatures = {}
    for fault, vectors in fault_vectors.items():
        signatures.setdefault(frozenset(vectors), []).append(fault)
    class_sizes = Counter(len(faults) for faults in signatures.values())

    figure, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    if class_sizes:
        sizes = sorted(class_sizes)
        axis.bar(sizes, [class_sizes[size] for size in sizes], color="#ce6848")
        axis.set_xticks(sizes)
    else:
        axis.text(0.5, 0.5, "No signature classes in this matrix", ha="center", va="center")
    axis.set_title(title)
    axis.set_xlabel("Faults in signature class")
    axis.set_ylabel("Number of signature classes")
    axis.grid(axis="y", alpha=0.25)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def plot_coverage_reduction(run_files, output_path):
    records = []
    for path in run_files:
        with path.open(encoding="utf-8") as file:
            result = json.load(file)
        summary = result.get("summary", {})
        total_faults = summary.get("unique_valid", 0)
        total_vectors = summary.get("total_vectors", 0)
        coverage = 100.0 if total_faults == 0 else 100 * summary.get("detectable", 0) / total_faults
        reduction = 0.0 if total_vectors == 0 else 100 * (1 - summary.get("selected_vectors", 0) / total_vectors)
        records.append((result.get("circuit_id", path.stem), coverage, reduction))

    if not records:
        return False

    labels = [record[0] for record in records]
    positions = np.arange(len(records))
    figure, axes = plt.subplots(2, 1, figsize=(max(9, len(records) * 0.9), 8), constrained_layout=True)
    for axis, values, title, color in (
        (axes[0], [record[1] for record in records], "Fault coverage", "#187f75"),
        (axes[1], [record[2] for record in records], "Test-vector reduction", "#ce6848"),
    ):
        axis.bar(positions, values, color=color)
        axis.set_xticks(positions, labels, rotation=35, ha="right")
        axis.set_ylabel("Percent")
        axis.set_ylim(0, 105)
        axis.set_title(title)
        axis.grid(axis="y", alpha=0.25)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return True


def plot_runtime(run_files, output_path):
    records = []
    for path in run_files:
        with path.open(encoding="utf-8") as file:
            result = json.load(file)
        runtime = result.get("summary", {}).get("greedy_runtime_ms")
        if runtime is not None:
            records.append((result.get("circuit_id", path.stem), runtime))

    if not records:
        return False

    labels = [record[0] for record in records]
    figure, axis = plt.subplots(figsize=(max(9, len(records) * 0.9), 5), constrained_layout=True)
    axis.bar(labels, [record[1] for record in records], color="#4b6d8a")
    axis.set_title("Greedy selector runtime")
    axis.set_ylabel("Runtime (ms)")
    axis.set_xlabel("Circuit")
    axis.tick_params(axis="x", labelrotation=35)
    axis.grid(axis="y", alpha=0.25)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return True


def generate_plots(results_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_files = sorted(results_dir.glob("detection_matrix_*.json"))
    run_files = sorted(results_dir.glob("integrated_run_*.json"))
    generated = []

    for path in matrix_files + run_files:
        try:
            matrix, fault_ids = read_matrix(path)
        except (OSError, ValueError, SyntaxError, TypeError) as error:
            print("Skipping {}: {}".format(path, error))
            continue

        stem = safe_name(path.stem)
        plots = (
            ("detection_matrix_{}.png".format(stem), lambda target: plot_heatmap(matrix, fault_ids, path.stem, target)),
            ("multiplicity_{}.png".format(stem), lambda target: plot_multiplicity(matrix, fault_ids, path.stem, target)),
            ("signature_distribution_{}.png".format(stem), lambda target: plot_signature_distribution(matrix, fault_ids, path.stem, target)),
        )
        for filename, draw in plots:
            target = output_dir / filename
            draw(target)
            generated.append(target)

    if plot_coverage_reduction(run_files, output_dir / "coverage_and_reduction.png"):
        generated.append(output_dir / "coverage_and_reduction.png")
    if plot_runtime(run_files, output_dir / "runtime_performance.png"):
        generated.append(output_dir / "runtime_performance.png")
    elif run_files:
        print("No runtime chart: rerun integrated experiments to record greedy_runtime_ms.")

    return generated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=None)
    arguments = parser.parse_args()
    output_dir = arguments.output_dir or arguments.results_dir / "plots"
    generated = generate_plots(arguments.results_dir, output_dir)

    if not generated:
        parser.error("no supported result JSON files found in {}".format(arguments.results_dir))
    print("Generated {} plots in {}".format(len(generated), output_dir))
    for path in generated:
        print("  {}".format(path))


if __name__ == "__main__":
    main()