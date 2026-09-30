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