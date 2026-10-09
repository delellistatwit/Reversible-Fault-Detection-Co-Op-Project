from src.circuit import Circuit
from src.detectionmatrix import build_detection_matrix
from src.fredkin_gate import FredkinGate


def build_fredkin_matrix():
    """return the detection matrix for a single Fredkin gate on three wires."""
    circuit = Circuit(3)
    circuit.add_gate(FredkinGate(0, 1, 2))
    return build_detection_matrix(circuit)