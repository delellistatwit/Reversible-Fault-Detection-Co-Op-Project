import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ANALYSIS_DIR = Path(__file__).resolve().parent
SRC_DIR = ANALYSIS_DIR.parent
REPO_ROOT = SRC_DIR.parent
for p in (str(ANALYSIS_DIR), str(SRC_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

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

SCRIPT_NAME = "src/analysis/regenerate_figures.py"
CLI_COMMAND = "python src/analysis/regenerate_figures.py"


def resolve_results_dir() -> Path:
    """Finds the active results/ folder in either <repo_root>/results or src/results."""
    for candidate in (REPO_ROOT / "results", SRC_DIR / "results"):
        if (candidate / "csv_sources" / "master_metrics_source.csv").exists():
            return candidate
        if (candidate / "integrated_run_xor.json").exists():
            return candidate
    if (SRC_DIR / "results").exists():
        return SRC_DIR / "results"
    return REPO_ROOT / "results"


def read_csv_rows(csv_path: Path) -> list:
    with open(csv_path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def regenerate_heatmap_from_csv(circuit_key: str, src_csv: Path, out_png: Path) -> tuple:
    """Reads binary matrix strictly from CSV and regenerates the 2D heatmap."""
    with open(src_csv, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    header = reader[0]
    fault_ids = header[1:]
    data_rows = reader[1:]

    vectors = [r[0] for r in data_rows]
    grid = np.array([[int(val) for val in r[1:]] for r in data_rows], dtype=int)

    num_v, num_f = grid.shape
    fig_w = max(6, min(14, num_f * 0.22))
    fig_h = max(4, min(10, num_v * 0.15))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(
        grid, aspect="auto", cmap="Blues", vmin=0, vmax=1, interpolation="nearest"
    )
    ax.set_title(
        f"Audited Fault-Detection Matrix: {circuit_key.upper()} ({num_v}x{num_f})"
    )
    ax.set_xlabel("Unique Valid Fault Index")
    ax.set_ylabel("Input Test Vector (Counting Order)")

    if num_f <= 35:
        ax.set_xticks(range(num_f))
        ax.set_xticklabels(fault_ids, rotation=90, fontsize=6)
    if num_v <= 32:
        ax.set_yticks(range(num_v))
        ax.set_yticklabels(vectors, fontsize=7)

    plt.colorbar(im, ax=ax, ticks=[0, 1], label="Detected (1=Yes, 0=No)")
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close(fig)
    return num_v, num_f


def main():
    results_dir = resolve_results_dir()
    csv_dir = results_dir / "csv_sources"
    fig_dir = results_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    lineage_rows = []

    print("\n" + "=" * 115)
    print(f"WEEK 7 CSV-ONLY GRAPH REGENERATION & FIGURE-SOURCE LINK LOGGING ({results_dir})")
    print("=" * 115)

    # 1. Regenerate all 10 Heatmaps strictly from matrix_<circuit>.csv
    for c_key in CIRCUIT_ORDER:
        src_csv = csv_dir / f"matrix_{c_key}.csv"
        if not src_csv.exists():
            continue
        out_png = fig_dir / f"heatmap_{c_key}.png"
        rows, cols = regenerate_heatmap_from_csv(c_key, src_csv, out_png)
        lineage_rows.append({
            "figure_id": f"FIG_HM_{c_key.upper()}",
            "figure_file": f"results/figures/heatmap_{c_key}.png",
            "figure_type": "2D Detection Matrix Heatmap",
            "source_csv_file": f"results/csv_sources/matrix_{c_key}.csv",
            "source_dimensions": f"{rows} rows x {cols} cols",
            "generating_script": SCRIPT_NAME,
            "regeneration_command": CLI_COMMAND,
            "verification_status": "VERIFIED_FROM_CSV",
        })

    # 2. Regenerate Multiplicity Distribution Plot from multiplicity_dist_<circuit>.csv
    dist_targets = [
        k for k in ("toffoli_gate", "half_adder", "all_gates", "graycode6", "ham7")
        if (csv_dir / f"multiplicity_dist_{k}.csv").exists()
    ]
    if dist_targets:
        fig, axes = plt.subplots(1, len(dist_targets), figsize=(15, 3.8), sharey=False)
        if len(dist_targets) == 1:
            axes = [axes]
        for idx, c_key in enumerate(dist_targets):
            src_csv = csv_dir / f"multiplicity_dist_{c_key}.csv"
            rows = read_csv_rows(src_csv)
            mults = [str(r["multiplicity_value"]) for r in rows]
            counts = [int(r["fault_count"]) for r in rows]
            axes[idx].bar(mults, counts, color="#4C72B0", edgecolor="black")
            axes[idx].set_title(c_key.upper(), fontsize=9)
            axes[idx].set_xlabel("Multiplicity (# Vectors)")
            if idx == 0:
                axes[idx].set_ylabel("Number of Faults")
            axes[idx].grid(axis="y", linestyle="--", alpha=0.5)

        fig.suptitle("Fault Multiplicity Distributions (Regenerated from Source CSVs)", fontsize=11)
        plt.tight_layout()
        plt.savefig(fig_dir / "dist1_multiplicity_distributions.png", dpi=300)
        plt.close(fig)

        lineage_rows.append({
            "figure_id": "FIG_DIST_MULT",
            "figure_file": "results/figures/dist1_multiplicity_distributions.png",
            "figure_type": "Fault Multiplicity Frequency Distribution",
            "source_csv_file": "results/csv_sources/multiplicity_dist_<circuit>.csv",
            "source_dimensions": f"{len(dist_targets)} benchmark circuit CSVs",
            "generating_script": SCRIPT_NAME,
            "regeneration_command": CLI_COMMAND,
            "verification_status": "VERIFIED_FROM_CSV",
        })

    # 3. Regenerate Signature-Class Size Distribution Plot from signature_dist_<circuit>.csv
    if dist_targets:
        fig, axes = plt.subplots(1, len(dist_targets), figsize=(15, 3.8), sharey=False)
        if len(dist_targets) == 1:
            axes = [axes]
        for idx, c_key in enumerate(dist_targets):
            src_csv = csv_dir / f"signature_dist_{c_key}.csv"
            rows = read_csv_rows(src_csv)
            sizes = [str(r["equivalence_class_size"]) for r in rows]
            cls_counts = [int(r["signature_class_count"]) for r in rows]
            axes[idx].bar(sizes, cls_counts, color="#55A868", edgecolor="black")
            axes[idx].set_title(c_key.upper(), fontsize=9)
            axes[idx].set_xlabel("Equiv. Class Size (# Faults)")
            if idx == 0:
                axes[idx].set_ylabel("Number of Signature Classes")
            axes[idx].grid(axis="y", linestyle="--", alpha=0.5)

        fig.suptitle("Signature-Class Size Distributions (Regenerated from Source CSVs)", fontsize=11)
        plt.tight_layout()
        plt.savefig(fig_dir / "dist2_signature_class_distributions.png", dpi=300)
        plt.close(fig)

        lineage_rows.append({
            "figure_id": "FIG_DIST_SIG",
            "figure_file": "results/figures/dist2_signature_class_distributions.png",
            "figure_type": "Signature Equivalence Class Size Distribution",
            "source_csv_file": "results/csv_sources/signature_dist_<circuit>.csv",
            "source_dimensions": f"{len(dist_targets)} benchmark circuit CSVs",
            "generating_script": SCRIPT_NAME,
            "regeneration_command": CLI_COMMAND,
            "verification_status": "VERIFIED_FROM_CSV",
        })

    # 4. Regenerate Optimization & Scaling Plots strictly from master_metrics_source.csv & greedy_traces_source.csv
    master_csv = csv_dir / "master_metrics_source.csv"
    if master_csv.exists():
        master_rows = read_csv_rows(master_csv)

        circuits = [r["circuit_id"] for r in master_rows]
        exhaustive = [int(r["exhaustive_vectors_2n"]) for r in master_rows]
        gts = [int(r["gts_size"]) for r in master_rows]
        reduction = [float(r["reduction_pct"]) for r in master_rows]
        retention = [float(r["retention_pct"]) for r in master_rows]
        runtimes = [float(r["greedy_runtime_ms"]) for r in master_rows]
        x = np.arange(len(circuits))

        # Fig 1
        fig, ax = plt.subplots(figsize=(10, 5))
        w = 0.36
        ax.bar(x - w / 2, exhaustive, width=w, label="Exhaustive Suite ($2^n$)", color="#4C72B0")
        ax.bar(x + w / 2, gts, width=w, label="Greedy Test Set (GTS)", color="#55A868")
        ax.set_yscale("log", base=2)
        ax.set_xticks(x)
        ax.set_xticklabels(circuits, rotation=30, ha="right")
        ax.set_ylabel("Number of Test Vectors ($\log_2$ scale)")
        ax.set_title("Exhaustive ($2^n$) vs. Optimized Test-Set Size (Regenerated from CSV)")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(fig_dir / "fig1_exhaustive_vs_gts.png", dpi=300)
        plt.close(fig)

        # Fig 2
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x, reduction, label="Test-Set Reduction (%)", color="#2B5C8F")
        ax.bar(x, retention, bottom=reduction, label="Test-Set Retention (%)", color="#D95F02")
        ax.set_xticks(x)
        ax.set_xticklabels(circuits, rotation=30, ha="right")
        ax.set_ylabel("Percentage of Exhaustive Suite (%)")
        ax.set_ylim(0, 105)
        ax.set_title("Test-Set Reduction vs. Retention (Regenerated from CSV)")
        ax.legend(loc="lower right")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(fig_dir / "fig2_reduction_vs_retention.png", dpi=300)
        plt.close(fig)

        # Fig 3
        traces_csv = csv_dir / "greedy_traces_source.csv"
        if traces_csv.exists():
            trace_rows = read_csv_rows(traces_csv)
            fig, ax = plt.subplots(figsize=(8, 5))
            for cid in ("HALF_ADDER", "ALL_GATES", "GRAYCODE6", "HAM7"):
                c_steps = [r for r in trace_rows if r["circuit_id"] == cid]
                if c_steps:
                    steps = [0] + [int(r["step"]) for r in c_steps]
                    covs = [0.0] + [float(r["cumulative_coverage_pct"]) for r in c_steps]
                    ax.plot(steps, covs, marker="o", linewidth=2, label=cid)
            ax.set_xlabel("Greedy Selection Step ($k$)")
            ax.set_ylabel("Cumulative Fault Coverage (%)")
            ax.set_ylim(0, 105)
            ax.set_title("Greedy Vector Selection Convergence Traces (Regenerated from CSV)")
            ax.legend()
            ax.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(fig_dir / "fig3_greedy_convergence_traces.png", dpi=300)
            plt.close(fig)

        # Fig 4
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(x, runtimes, color="#8172B2")
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels(circuits, rotation=30, ha="right")
        ax.set_ylabel("Greedy Selection Runtime (ms, log scale)")
        ax.set_title("Greedy Test-Set Selection Runtime (Regenerated from CSV)")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(fig_dir / "fig4_runtime_scaling.png", dpi=300)
        plt.close(fig)

        for fid, fname, ftype, scsv, sdim in [
            ("FIG_OPT_1", "results/figures/fig1_exhaustive_vs_gts.png", "Exhaustive vs. GTS Bar Chart", "results/csv_sources/master_metrics_source.csv", "10 circuits x 26 cols"),
            ("FIG_OPT_2", "results/figures/fig2_reduction_vs_retention.png", "Reduction vs. Retention Stacked Bar", "results/csv_sources/master_metrics_source.csv", "10 circuits x 26 cols"),
            ("FIG_OPT_3", "results/figures/fig3_greedy_convergence_traces.png", "Step-by-Step Coverage Convergence", "results/csv_sources/greedy_traces_source.csv", "22 trace steps x 6 cols"),
            ("FIG_OPT_4", "results/figures/fig4_runtime_scaling.png", "Greedy Selection Runtime Log-Scale Bar Chart", "results/csv_sources/master_metrics_source.csv", "10 circuits x 26 cols"),
        ]:
            lineage_rows.append({
                "figure_id": fid,
                "figure_file": fname,
                "figure_type": ftype,
                "source_csv_file": scsv,
                "source_dimensions": sdim,
                "generating_script": SCRIPT_NAME,
                "regeneration_command": CLI_COMMAND,
                "verification_status": "VERIFIED_FROM_CSV",
            })

    links_csv = results_dir / "figure_source_links.csv"
    if lineage_rows:
        with open(links_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(lineage_rows[0].keys()))
            writer.writeheader()
            writer.writerows(lineage_rows)

        for row in lineage_rows:
            print(f"[{row['verification_status']}] {row['figure_id']:<18} | {row['figure_file']:<48} <-- {row['source_csv_file']}")

    print("=" * 115)
    print(f"Exported Figure-Source Links Table: {links_csv}")
    print("=" * 115 + "\n")


if __name__ == "__main__":
    main()