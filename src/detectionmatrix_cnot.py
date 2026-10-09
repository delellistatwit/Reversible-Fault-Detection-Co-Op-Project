from src.circuit import Circuit
from src.cnot_gate import CNOTGate
from src.detectionmatrix import build_detection_matrix


def build_cnot_matrix():
    """return the detection matrix for a single CNOT gate on two wires."""
    circuit = Circuit(2)
    circuit.add_gate(CNOTGate(0, 1))
    return build_detection_matrix(circuit)