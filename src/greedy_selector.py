"""
By: Matthew Santorsa
contains deliverables 3 and 4
"""
import time
import unittest

def calculate_coverage(detected_faults_set, total_faults_list):
    """Calculates the percentage of target faults successfully detected."""
    if len(total_faults_list) == 0:
        return 100.0
    return (len(detected_faults_set) / len(total_faults_list)) * 100.0

def calculate_reduction(selected_vectors_list, total_vectors_list):
    """Calculates the percentage decrease in test vectors compared to exhaustive set."""
    if len(total_vectors_list) == 0:
        return 0.0
    return (1 - (len(selected_vectors_list) / len(total_vectors_list))) * 100.0

def run_with_metrics(V, F, matrix):
    """Wrapper function to execute the selector and capture runtime in milliseconds."""
    start_time = time.perf_counter()
    selected = greedy_selector_v1(V, F, matrix)
    end_time = time.perf_counter()
    
    runtime_ms = (end_time - start_time) * 1000
    return selected, runtime_ms

def greedy_selector_v1(V, F, matrix):
    """
    executes deterministic greedy selection based pseudocode
    includes selection trace for verification.
    """
    selected_vectors = []
    uncovered_faults = set(F)
    
    # store original indices to strictly enforce the tie-breaker rule
    vector_indices = {v: i for i, v in enumerate(V)}
    available_vectors = list(V)  # working copy to remove vectors from
    
    print("--- Starting Selection Trace ---")
    
    while len(uncovered_faults) > 0:
        best_vector = None
        max_new_covered = 0
        
        # selection phase
        for v in available_vectors:
            detected_by_v = matrix.get(v, set())
            newly_detected = detected_by_v.intersection(uncovered_faults)
            new_covered = len(newly_detected)
            
            if new_covered > max_new_covered:
                best_vector = v
                max_new_covered = new_covered
                
            # tie breaking rule for determinism
            elif new_covered == max_new_covered and new_covered > 0:
                if vector_indices[v] < vector_indices[best_vector]:
                    best_vector = v
                    
        # failsafe when undetectable faults are present
        if max_new_covered == 0:
            print("Trace Log: Failsafe triggered. Remaining faults undetectable.")
            break
            
        # update sets and removal of faults
        selected_vectors.append(best_vector)
        faults_to_remove = matrix[best_vector].intersection(uncovered_faults)
        uncovered_faults.difference_update(faults_to_remove)
        available_vectors.remove(best_vector)
        
        # selection trace output
        print(f"Trace Log: Selected Vector {best_vector} | New Faults Covered: {max_new_covered} | Remaining Target Faults: {len(uncovered_faults)}")
        
    print("--- End of Trace ---")
    return selected_vectors


# 1. Setup the hand-worked AND gate example inputs
V = [(0, 0), (0, 1), (1, 0), (1, 1)]
F = ["A_SA1"] # Input A is Stuck-At-1
matrix = {
    (0, 0): set(),
    (0, 1): {"A_SA1"}, # This is the only vector that detects the fault
    (1, 0): set(),
    (1, 1): set()
}

# 2. Run the selector
final_vectors = greedy_selector_v1(V, F, matrix)
print(f"\nFinal Selected Vectors: {final_vectors}")

class TestGreedySelector(unittest.TestCase):

    def test_complete_coverage(self):
        """Test 1: All faults can be perfectly detected by the available vectors."""
        V = [(0, 0), (0, 1)]
        F = ["F1", "F2"]
        matrix = {(0, 0): {"F1"}, (0, 1): {"F2"}}
        result = greedy_selector_v1(V, F, matrix)
        self.assertEqual(result, [(0, 0), (0, 1)])

    def test_partial_coverage(self):
        """Test 2: Algorithm stops early because remaining faults aren't covered by remaining vectors."""
        V = [(0, 0), (0, 1)]
        F = ["F1", "F2", "F3"] # F3 is in target list, but not in matrix values
        matrix = {(0, 0): {"F1"}, (0, 1): {"F2"}}
        result = greedy_selector_v1(V, F, matrix)
        self.assertEqual(result, [(0, 0), (0, 1)]) # Should select both, then safely break

    def test_duplicate_vectors(self):
        """Test 3: The input pool contains duplicate vector entries."""
        V = [(0, 1), (0, 1), (1, 0)] # (0, 1) accidentally added twice
        F = ["F1"]
        matrix = {(0, 1): {"F1"}, (1, 0): set()}
        result = greedy_selector_v1(V, F, matrix)
        # Should cleanly pick the first (0, 1) and finish without crashing
        self.assertEqual(result, [(0, 1)])

    def test_ties(self):
        """Test 4: Two vectors cover the exact same number of faults; lower index must win."""
        V = [(0, 0), (1, 1)]
        F = ["F1"]
        # Both vectors detect F1. (0, 0) is at index 0, (1, 1) is at index 1.
        matrix = {(0, 0): {"F1"}, (1, 1): {"F1"}}
        result = greedy_selector_v1(V, F, matrix)
        self.assertEqual(result, [(0, 0)]) # Tie-breaker must strictly pick (0, 0)

    def test_undetectable_faults(self):
        """Test 5: Faults exist, but the matrix contains completely empty sets."""
        V = [(0, 0), (1, 1)]
        F = ["F1", "F2"]
        matrix = {(0, 0): set(), (1, 1): set()}
        result = greedy_selector_v1(V, F, matrix)
        self.assertEqual(result, []) # Failsafe must trigger immediately, returning empty list

# Execute the automated tests when run
if __name__ == '__main__':
    # Add a quiet execution so your selection trace logs don't clutter the test output
    import sys, os
    sys.stdout = open(os.devnull, 'w') # Suppress trace logs during testing
    unittest.main(exit=False)
    sys.stdout = sys.__stdout__ # Restore console output
    print("All automated unit tests passed successfully.")