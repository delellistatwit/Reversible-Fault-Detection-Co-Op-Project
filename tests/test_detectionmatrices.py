import unittest

from src.detectionmatrix_cnot import build_cnot_matrix
from src.detectionmatrix_fredkin import build_fredkin_matrix
from src.detectionmatrix_toffoli import build_toffoli_matrix


class TestGateDetectionMatrices(unittest.TestCase):

    def assert_valid_matrix(self, matrix, vector_count):
        self.assertEqual(len(matrix.matrix), vector_count)
        self.assertTrue(all(isinstance(vector, tuple) for vector in matrix.matrix))
        self.assertTrue(all(isinstance(faults, set) for faults in matrix.matrix.values()))
        self.assertTrue(set().union(*matrix.matrix.values()))

    def test_cnot_matrix(self):
        self.assert_valid_matrix(build_cnot_matrix(), 4)

    def test_toffoli_matrix(self):
        self.assert_valid_matrix(build_toffoli_matrix(), 8)

    def test_fredkin_matrix(self):
        self.assert_valid_matrix(build_fredkin_matrix(), 8)


if __name__ == "__main__":
    unittest.main()