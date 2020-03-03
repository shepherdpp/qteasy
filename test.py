import unittest
import qteasy as qt
import pandas as pd
import numpy as np
import itertools


class TestRates(unittest.TestCase):
    def test_rate_creation(self):
        r = qt.Rate(0.001, 0.001)
        self.assertIsInstance(r, qt.Rate, 'Type should be Rate')

    def test_rate_operations(self):
        r = qt.Rate(0.001, 0.001)
        self.assertEqual(r['fee'], 0.001, 'Item fee get is incorrect')
        self.assertEqual(r['slipege'], 0.001, 'Item get wrong')
        self.assertEqual(r['impact'], 0.001, 'item get wrong')
        self.assertEqual(r(1000), 1.002, 'fee calculation wrong')

    def test_rate_print(self):
        r = qt.Rate(0.1, 0.1)
        self.assertEqual(str(r), '<rate: fee:0.1, slipege:0.1, impact:0.1>', 'rate object printing wrong')


class TestUnify(unittest.TestCase):
    def test_unify(self):
        l1 = np.array([[3, 2, 5], [5, 3, 2]])
        res = qt.unify(l1)
        target = np.array([[0.3, 0.2, 0.5], [0.5, 0.3, 0.2]])

        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')
        l1 = np.array([[1, 1, 1, 1, 1], [2, 2, 2, 2, 2]])
        res = qt.unify(l1)
        target = np.array([[0.2, 0.2, 0.2, 0.2, 0.2], [0.2, 0.2, 0.2, 0.2, 0.2]])

        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')


class TestSpace(unittest.TestCase):
    def test_creation(self):
        """
            test if creation of space object is fine
        """
        # first group of inputs, output Space with two discr axis from [0,10]
        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['discr',
                      ['discr', 'discr']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'discr'], 'types incorrect')

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['foobar',
                      ['foo', 'bar']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['enum', 'enum'], 'types incorrect')

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = [['discr', 'foobar']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'enum'], 'types incorrect')

    def test_extract(self) -> object:
        """

        :return:
        """
        pass


class TestOperator(unittest.TestCase):

    def create_test_data(self):
        # build up test data: a 4-type, 3-share, 21-day matrix of prices that contains nan values in some days
        # for some shares

        # for share1:
        share1_close = [7.74, 7.83, 7.79, 7.93, 7.84, 7.83, 7.77, 7.84, 7.86, 7.92, 7.84,
                        7.83, 7.85, 8.14, 8.05, 8., 8.07, 8.1, 7.74, 7.71, 7.69]
        share1_open = [7.88, 7.93, 7.86, 7.95, 7.92, 7.95, 8.01, 7.87, 7.88, 7.94, 7.93,
                       7.88, 7.86, 8.43, 8.2, 8.19, 8.12, 8.15, 8.19, 7.79, 7.93]
        share1_high = [7.88, 7.93, 7.86, 7.95, 7.92, 7.95, 8.01, 7.87, 7.88, 7.94, 7.93,
                       7.88, 7.86, 8.43, 8.2, 8.19, 8.12, 8.15, 8.19, 7.79, 7.93]
        share1_low = [7.68, 7.66, 7.76, 7.76, 7.75, 7.79, 7.76, 7.65, 7.81, 7.79, 7.81,
                      7.7, 7.74, 7.82, 8., 7.97, 7.93, 8.01, 7.6, 7.58, 7.67]

        # for share2:
        share2_close = [6.98, 7.1, 7.14, 7.12, 7.1, 7.1, 7.11, 7.32, 7.36, np.nan, np.nan,
                        np.nan, np.nan, np.nan, np.nan, np.nan, 7.58, 7.97, 7.47, 7.75, 7.51]
        share2_open = [7.04, 6.94, 7.11, 7.14, 7.1, 7.11, 7.11, 7.11, 7.29, np.nan, np.nan,
                       np.nan, np.nan, np.nan, np.nan, np.nan, 7.8, 7.43, 7.9, 7.43, 7.7]
        share2_high = [7.06, 7.13, 7.15, 7.15, 7.14, 7.21, 7.27, 7.33, 7.39,  np.nan,  np.nan,
                       np.nan,  np.nan,  np.nan,  np.nan,  np.nan, 7.8 , 8.11, 7.93, 7.8 , 7.74]
        share2_low = [6.94, 6.94, 7.06, 7.05, 7.03, 7.06, 7.07, 7.1, 7.26,  np.nan,  np.nan,
                      np.nan,  np.nan,  np.nan,  np.nan,  np.nan, 7.37, 7.43, 7.33, 7.38, 7.44]

        # for share3:
        share3_close = [13.89, 14.13, 14.27, np.nan , np.nan, 14.53, 14.25, 14.56, 14.61,
                        14.61, 14.01, 13.85, 13.93, 14.00, 13.98, 13.85, 13.85, 13.99,
                        13.64, 13.82, 13.71]
        share3_open = [13.92, 13.85, 14.14, np.nan, np.nan, 14.38, 14.39, 14.26, 14.69,
                       14.68, 14.12, 13.99, 13.85, 14.02, 14.  , 13.95, 13.85, 13.86,
                       13.99, 13.63, 13.82]
        share3_high = [14.02, 14.16, 14.47, np.nan, np.nan, 14.8 , 14.51, 14.58, 14.73,
                       14.77, 14.22, 13.99, 13.96, 14.04, 14.06, 14.08, 13.95, 14.01,
                       14.13, 13.84, 13.83]
        share3_low = [13.8 , 13.8 , 14.11, np.nan, np.nan, 14.15, 14.24, 14.14, 14.48,
                      14.5 , 13.94, 13.79, 13.8 , 13.91, 13.95, 13.83, 13.76, 13.8 ,
                      13.46, 13.58, 13.68]

        date_indices = ['2016-07-01', '2016-07-04', '2016-07-05', '2016-07-06',
                        '2016-07-07', '2016-07-08', '2016-07-11', '2016-07-12',
                        '2016-07-13', '2016-07-14', '2016-07-15', '2016-07-18',
                        '2016-07-19', '2016-07-20', '2016-07-21', '2016-07-22',
                        '2016-07-25', '2016-07-26', '2016-07-27', '2016-07-28',
                        '2016-07-29']

        shares = ['000010', '000030', '000039']

        types = ['close', 'open', 'high', 'low']

        self.test_data_3D = np.zeros((3, 4, 21))
        self.test_data_2D = np.zeros((3, 21))

        # Build up 3D data
        self.test_data_3D[0, 0, :] = share1_close
        self.test_data_3D[0, 1, :] = share1_open
        self.test_data_3D[0, 2, :] = share1_high
        self.test_data_3D[0, 3, :] = share1_low

        self.test_data_3D[1, 0, :] = share2_close
        self.test_data_3D[1, 1, :] = share2_open
        self.test_data_3D[1, 2, :] = share2_high
        self.test_data_3D[1, 3, :] = share2_low

        self.test_data_3D[2, 0, :] = share3_close
        self.test_data_3D[2, 1, :] = share3_open
        self.test_data_3D[2, 2, :] = share3_high
        self.test_data_3D[2, 3, :] = share3_low

        # Build up 2D data
        self.test_data_2D[0, :] = share1_close
        self.test_data_2D[1, :] = share2_close
        self.test_data_2D[2, :] = share3_close

    def test_operator_generate(self) -> object:
        """

        :return:
        """
        self.op = qt.Operator(timing_types=['DMA'], selecting_types=['simple'], ricon_types=['urgent'])
        self.assertIsInstance(self.op, qt.Operator, 'Operator Creation Error')

    def test_operator_parameter_setting(self):
        """

        :return:
        """
        self.op.set_parameter('s-1', ('Y', 0.5))

if __name__ == '__main__':
    unittest.main()
