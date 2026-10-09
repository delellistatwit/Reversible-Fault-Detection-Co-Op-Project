from src.circuit import Circuit
from src.detectionmatrix import build_detection_matrix
from src.toffoli_gate import ToffoliGate


def build_toffoli_matrix():
    """Return the detection matrix for a single Toffoli gate on three wires."""
    circuit = Circuit(3)
    circuit.add_gate(ToffoliGate(0, 1, 2))
    return build_detection_matrix(circuit)