"""
By: Matthew Santorsa
contains deliverable 2
"""

import json
import ast

from src.faults import FaultGenerator, UNIQUE_VALID, classify_faults

class DetectionMatrix:
    def __init__(self):
        # init sparse dictionary map
        # format: { (0, 1): {"REMOVE_G2", "SWAP_W0_W1"} }
        self.matrix = {}

    def create_entry(self, vector, fault_id=None):
        """creates an entry for a vector. optionally adds a fault."""
        if vector not in self.matrix:
            self.matrix[vector] = set()
        if fault_id:
            self.matrix[vector].add(fault_id)

    def query(self, vector):
        """queries the matrix and returns the set of faults detected by a vector."""
        return self.matrix.get(vector, set())

    def save(self, filepath):
        """
        saves the matrix to a JSON file.
        converts tuple keys to strings and set values to lists for JSON compatibility.
        """
        export_data = {str(vector_key): list(fault_set) for vector_key, fault_set in self.matrix.items()}
        
        with open(filepath, 'w') as file:
            json.dump(export_data, file, indent=4)

    def load(self, filepath):
        """
        loads the matrix from a JSON file.
        safely evaluates string keys back into tuples and list values back into sets.
        """
        with open(filepath, 'r') as file:
            import_data = json.load(file)
            
        self.matrix = {}
        for key_str, fault_list in import_data.items():
            # ast.literal_eval safely converts the string "(0, 1)" back into the tuple (0, 1)
            original_tuple = ast.literal_eval(key_str)
            # converts the list back into a mathematical Set
            self.matrix[original_tuple] = set(fault_list)


def build_detection_matrix(circuit):
    """Build a detection matrix for a circuit using its unique valid faults."""
    correct_table = circuit.truth_table()
    vectors = [inputs for inputs, _ in correct_table]
    classified = classify_faults(circuit, FaultGenerator(circuit).generate_all())
    unique_faults = [fault for fault, status, _ in classified if status == UNIQUE_VALID]

    matrix = DetectionMatrix()
    for vector in vectors:
        matrix.create_entry(vector)

    for fault in unique_faults:
        faulty_table = fault.apply(circuit).truth_table()
        for (vector, correct_output), (_, faulty_output) in zip(correct_table, faulty_table):
            if correct_output != faulty_output:
                matrix.create_entry(vector, fault.get_id())

    return matrix

# --- required demonstration ---
if __name__ == "__main__":
    # 1. create
    dm = DetectionMatrix()
    dm.create_entry((0, 0)) # vector that detects nothing
    dm.create_entry((0, 1), "REMOVE_G2")
    dm.create_entry((0, 1), "SWAP_W0_W1")
    
    # 2. query
    print(f"Query (0, 1): {dm.query((0, 1))}")
    
    # 3. save
    dm.save("sample_matrix.json")
    print("Matrix saved to sample_matrix.json")
    
    # 4. load (creating a new instance to prove it works)
    dm_loaded = DetectionMatrix()
    dm_loaded.load("sample_matrix.json")
    print(f"Loaded from file, Query (0, 1): {dm_loaded.query((0, 1))}")