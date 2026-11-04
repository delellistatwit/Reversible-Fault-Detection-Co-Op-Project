"""
By: Matthew Santorsa
contains deliverable 1
"""

import itertools

def generate_vectors(n):
    """
    generates all 2^n unique binary test vectors for an n-wire circuit.
    """
    return list(itertools.product([0, 1], repeat=n))

# evidence sets
vectors_2_wire = generate_vectors(2)
vectors_3_wire = generate_vectors(3)
vectors_4_wire = generate_vectors(4)

if __name__ == '__main__':
    vectors_2 = generate_vectors(2)
    print(f"2-wire ({len(vectors_2_wire)}: {vectors_2_wire})")
    vectors_3 = generate_vectors(3)
    print(f"3-wire ({len(vectors_3_wire)}: {vectors_3_wire})")
    vectors_4 = generate_vectors(4)
    print(f"4-wire ({len(vectors_4_wire)}: {vectors_4_wire})")