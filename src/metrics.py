import unittest

def calculate_coverage(matrix, total_faults):
    """Returns the percentage of faults detected by the matrix."""
    if not total_faults:
        return 100.0
    detected = set().union(*matrix.values())
    return (len(detected) / len(total_faults)) * 100.0

def calculate_density(matrix, total_faults):
    """Returns the percentage of 1s in the matrix (total detections / possible detections)."""
    if not matrix or not total_faults:
        return 0.0
    total_detects = sum(len(faults) for faults in matrix.values())
    max_possible_detects = len(matrix) * len(total_faults)
    return (total_detects / max_possible_detects) * 100.0

def calculate_multiplicity(matrix):
    """Returns a dictionary mapping each fault to the number of vectors that detect it."""
    multiplicity = {}
    for faults in matrix.values():
        for f in faults:
            multiplicity[f] = multiplicity.get(f, 0) + 1
    return multiplicity

def find_essential_vectors(matrix, multiplicity):
    """Returns a list of vectors that are the ONLY detectors for at least one fault."""
    essential_vectors = set()
    for vector, faults in matrix.items():
        for f in faults:
            if multiplicity.get(f) == 1:
                essential_vectors.add(vector)
                break  # The vector is essential; move to the next vector
    return sorted(list(essential_vectors))

def group_signature_classes(matrix):
    """Groups faults that are detected by the exact same set of vectors."""
    fault_to_vectors = {}
    for vector, faults in matrix.items():
        for f in faults:
            if f not in fault_to_vectors:
                fault_to_vectors[f] = set()
            fault_to_vectors[f].add(vector)
    
    # Group by identical vector footprints
    signatures = {}
    for fault, vectors in fault_to_vectors.items():
        vec_tuple = frozenset(vectors)
        if vec_tuple not in signatures:
            signatures[vec_tuple] = []
        signatures[vec_tuple].append(fault)
    
    # Sort for consistent testing output
    return sorted([sorted(group) for group in signatures.values()])


# --- Validation: Comparing Automated Outputs with the Manual Example ---
class TestMetrics(unittest.TestCase):
    def setUp(self):
        # Manual Test Case setup
        self.total_faults = ["F1", "F2", "F3", "F4"]
        self.matrix = {
            (0, 0): set(),
            (0, 1): {"F1"},
            (1, 0): {"F2", "F4"},
            (1, 1): {"F1", "F3"}
        }
        self.multiplicity = calculate_multiplicity(self.matrix)

    def test_coverage(self):
        # Expectation: F1, F2, F3, F4 all detected (4/4) = 100%
        self.assertEqual(calculate_coverage(self.matrix, self.total_faults), 100.0)

    def test_density(self):
        # Expectation: 4 faults in matrix values out of 16 possible cells (4 vectors * 4 faults) = 25%
        self.assertEqual(calculate_density(self.matrix, self.total_faults), 25.0)

    def test_multiplicity(self):
        # Expectation: F1 shows up twice, others show up once
        expected = {"F1": 2, "F2": 1, "F3": 1, "F4": 1}
        self.assertEqual(self.multiplicity, expected)

    def test_essential_vectors(self):
        # Expectation: (1, 0) uniquely detects F2 and F4. (1, 1) uniquely detects F3.
        expected = [(1, 0), (1, 1)]
        self.assertEqual(find_essential_vectors(self.matrix, self.multiplicity), expected)

    def test_signature_classes(self):
        # Expectation: F2 and F4 share the exact same footprint (only detected by (1, 0)).
        expected = [['F1'], ['F2', 'F4'], ['F3']]
        self.assertEqual(group_signature_classes(self.matrix), expected)

if __name__ == '__main__':
    unittest.main(exit=False)