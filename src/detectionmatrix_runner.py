"""build and save the CNOT, Toffoli, and Fredkin detection matrices.

run from the repository root with:
    python -m src.detectionmatrix_runner
"""

import os

from src.detectionmatrix_cnot import build_cnot_matrix
from src.detectionmatrix_fredkin import build_fredkin_matrix
from src.detectionmatrix_toffoli import build_toffoli_matrix


MATRIX_BUILDERS = {
    "cnot": build_cnot_matrix,
    "toffoli": build_toffoli_matrix,
    "fredkin": build_fredkin_matrix,
}


def run_all(output_dir="results"):
    """build all matrices, save them as JSON, and return them by gate name."""
    os.makedirs(output_dir, exist_ok=True)
    matrices = {}

    for gate_name, builder in MATRIX_BUILDERS.items():
        matrix = builder()
        matrix.save(os.path.join(output_dir, f"detection_matrix_{gate_name}.json"))
        matrices[gate_name] = matrix
        detected_faults = set().union(*matrix.matrix.values()) if matrix.matrix else set()
        print(f"{gate_name.upper()}: {len(matrix.matrix)} vectors, {len(detected_faults)} detected faults")

    return matrices


if __name__ == "__main__":
    run_all()