import unittest
from qteasy.core import *
import numpy as np

class test_operator(unittest.TestCase):

    def test_operator_creation(self):
        op = Operator()
        self.assertIsInstance(op, Operator, 'Type should be Operator')

class test_functions(unittest.TestCase):

    def test_unify(self):
        l1 = np.array([[3,2,5],[5,3,2]])
        res = unify(l1)
        target = np.array([[0.3,0.2,0.5], [0.5,0.3,0.2]])
        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')
        l1 = np.array([[1,1,1,1,1],[2,2,2,2,2]])
        res = unify(l1)
        target = np.array([[0.2,0.2,0.2,0.2,0.2], [0.2,0.2,0.2,0.2,0.2]])
        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')

if __name__ == '__main__':
    unittest.main()