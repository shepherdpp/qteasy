import unittest
import qteasy as qt
import numpy as np
import itertools

class TestOperator(unittest.TestCase):

    def test_operator_creation(self):
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator, 'Type should be Operator')

class TestRates(unittest.TestCase):

    def test_rate_creation(self):
        r = qt.Rate(0.001, 0.001, 0.001)
        self.assertIsInstance(r, qt.Rate, 'Type should be Rate')

    def test_rate_operations(self):
        r = qt.Rate(0.001, 0.001, 0.001)
        self.assertEqual(r['fee'], 0.001, 'Item fee get is incorrect')
        self.assertEqual(r['slipery'], 0.001, 'Item get wrong')
        self.assertEqual(r['impact'], 0.001, 'item get wrong')
        self.assertEqual(r(1000), 1.002, 'fee calculation wrong')


class TestUnify(unittest.TestCase):

    def test_unify(self):
        l1 = np.array([[3,2,5],[5,3,2]])
        res = qt.unify(l1)
        target = np.array([[0.3,0.2,0.5], [0.5,0.3,0.2]])

        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')
        l1 = np.array([[1,1,1,1,1],[2,2,2,2,2]])
        res = qt.unify(l1)
        target = np.array([[0.2,0.2,0.2,0.2,0.2], [0.2,0.2,0.2,0.2,0.2]])

        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')

class TestSpace(unittest.TestCase):

    def test_creation(self):
        """
            test if creation of space object is fine
        """
        # first group of inputs, output Space with two discr axis from [0,10]
        pars_list = [[(0,10), (0,10)],
                     [[0,10], [0,10]]]
            #,
            #         [10, 10],
            #         (10, 10)]

        types_list = [None,
                      'discr',
                      'foobar',
                      ['discr', 'discr']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            self.assertEqual(b, [(0,10), (0,10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'discr'], 'types incorrect')

    def test_extract(self) -> object:
        """

        :return:
        """
        pass



if __name__ == '__main__':
    unittest.main()