import unittest
import qteasy as qt
import pandas as pd
import numpy as np
import itertools


class TestRates(unittest.TestCase):
    def test_rate_creation(self):
        print('testing rates objects\n')
        r = qt.Rate(0.001, 0.001)
        self.assertIsInstance(r, qt.Rate, 'Type should be Rate')

    def test_rate_operations(self):
        r = qt.Rate(fee=0.001, slipage=0.001)
        self.assertEqual(r['fee'], 0.001, 'Item fee get is incorrect')
        self.assertEqual(r['slipage'], 0.001, 'Item get wrong')
        self.assertEqual(r(1000), 1.001, 'fee calculation wrong')

    def test_rate_print(self):
        r = qt.Rate(0.1, 0.1)
        self.assertEqual(str(r), '<fixed fee: 0.1, rate fee:0.1, slipage:0>', 'rate object printing wrong')


class TestUnify(unittest.TestCase):
    def test_unify(self):
        print('Testing Unify functions\n')
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
        print('testing space objects\n')
        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['discr',
                      ['discr', 'discr']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            # print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            # print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'discr'], 'types incorrect')

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['foobar',
                      ['foo', 'bar']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            # print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            # print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['enum', 'enum'], 'types incorrect')

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = [['discr', 'foobar']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            # print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            # print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'enum'], 'types incorrect')

    def test_extract(self):
        """

        :return:
        """
        pass


class TestOperator(unittest.TestCase):
    def setUp(self):
        print('start testing HistoryPanel object\n')
        self.data = np.random.randint(10, size=(5, 10, 4))
        self.index = pd.date_range(start='20200101', freq='d', periods=10)
        self.shares = '000100,000101,000102,000103,000104'
        self.dtypes = 'close,open,high,low'
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.dtypes, rows=self.index)

    def create_history_panel(self):
        """ test the creation of a HistoryPanel object by passing all data explicitly

        """
        self.assertIsInstance(self.hp, qt.HistoryPanel)
        self.assertEqual(self.hp.shape[0], 5)
        self.assertEqual(self.hp.shape[1], 10)
        self.assertEqual(self.hp.shape[2], 4)
        self.assertEqual(self.hp.level_count, 5)
        self.assertEqual(self.hp.row_count, 11)
        self.assertEqual(self.hp.column_count, 4)
        self.assertEqual(list(self.hp.levels.keys), self.shares.split())
        self.assertEqual(list(self.hp.columns.keys), self.dtypes.split())

    def test_history_panel_slicing(self):

        self.assertTrue(np.allclose(self.hp['close'], self.data[:,:,0:1]))
        self.assertTrue(np.allclose(self.hp['close,open'], self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp[['close','open']], self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp['close:high'], self.data[:, :, 0:3]))
        self.assertTrue(np.allclose(self.hp['close,high'], self.data[:, :, [0,2]]))
        self.assertTrue(np.allclose(self.hp[:,'000100'], self.data[0:1,:,]))
        self.assertTrue(np.allclose(self.hp[:,'000100,000101'], self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:,['000100','000101']], self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:,'000100:000102'], self.data[0:3, :]))
        self.assertTrue(np.allclose(self.hp[:,'000100,000102'], self.data[[0,2], :]))
        self.assertTrue(np.allclose(self.hp['close,open','000100,000102'], self.data[[0,2], :, 0:2]))
        print('start testing HistoryPanel')
        data = np.random.randint(10, size=(10, 5))
        index = pd.date_range(start='20200101', freq='d', periods=10)
        shares = '000100,000101,000102,000103,000104'
        dtypes = 'close'
        df = pd.DataFrame(data)
        print('=========================\nTesting HistoryPanel creation from DataFrame')
        hp = qt.dataframe_to_hp(df=df, shares=shares, htypes=dtypes)
        hp.info()
        hp = qt.dataframe_to_hp(df=df, shares='000100', htypes='close, open, high, low, middle', column_type='dtypes')
        hp.info()

        print('=========================\nTesting HistoryPanel creation from initialization')
        data = np.random.randint(10, size=(5, 10, 4)).astype('float')
        index = pd.date_range(start='20200101', freq='d', periods=10)
        shares = '000100,000101,000102,000103,000104'
        dtypes = 'close, open, high,low'
        data[0, [5, 6, 9], [0, 1, 3]] = np.nan
        data[1:4, [4, 7, 6, 2], [1, 1, 3, 0]] = np.nan
        data[4:5, [2, 9, 1, 2], [0, 3, 2, 1]] = np.nan
        hp = qt.HistoryPanel(data, levels=shares, columns=dtypes, rows=index)
        hp.info()
        print('==========================\n输出close类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close', :, :], data[:, :, 0:1], equal_nan=True))
        print(f'==========================\n输出close和open类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0,1], :, :], data[:, :, 0:2], equal_nan=True))
        print(f'==========================\n输出第一只股票的所有类型历史数据\n')
        self.assertTrue(np.allclose(hp[:, [0], :], data[0:1, :, :], equal_nan=True))
        print('==========================\n输出第0、1、2个htype对应的所有股票全部历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1, 2]], data[:, :, 0:3], equal_nan=True))
        print('==========================\n输出close、high两个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[['close', 'high']], data[:, :, [0, 2]], equal_nan=True))
        print('==========================\n输出0、1两个htype的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1]], data[:, :, 0:2], equal_nan=True))
        print('==========================\n输出close、high两个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close,high'], data[:, :, [0, 2]], equal_nan=True))
        print('==========================\n输出close起到high止的三个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close:high'], data[:, :, 0:3], equal_nan=True))
        print('==========================\n输出0、1、3三个股票的全部历史数据\n')
        self.assertTrue(np.allclose(hp[:, [0, 1, 3]], data[[0, 1, 3], :, :], equal_nan=True))
        print('==========================\n输出000100、000102两只股票的所有历史数据\n')
        self.assertTrue(np.allclose(hp[:, ['000100', '000102']], data[[0, 2], :, :], equal_nan=True))
        print('==========================\n输出0、1、2三个股票的历史数据\n', hp[:, 0: 3])
        self.assertTrue(np.allclose(hp[:, 0: 3], data[0:3, :, :], equal_nan=True))
        print('==========================\n输出000100、000102两只股票的所有历史数据\n')
        self.assertTrue(np.allclose(hp[:, '000100, 000102'], data[[0, 2], :, :], equal_nan=True))
        print('==========================\n输出所有股票的0-7日历史数据\n')
        self.assertTrue(np.allclose(hp[:, :, 0:8], data[:, 0:8, :], equal_nan=True))
        print('==========================\n输出000100股票的0-7日历史数据\n')
        self.assertTrue(np.allclose(hp[:, '000100', 0:8], data[0, 0:8, :], equal_nan=True))
        print('==========================\nstart testing multy axis slicing of HistoryPanel object')
        print('==========================\n输出000100、000120两只股票的close、open两组历史数据\n',
              hp['close,open', ['000100', '000102']])
        print('==========================\n输出000100、000120两只股票的close到open三组历史数据\n',
              hp['close,open', '000100, 000102'])
        print(f'historyPanel: hp:\n{hp}')
        print(f'data is:\n{data}')
        hp.htypes = 'open,high,low,close'
        hp.info()
        hp.shares = ['000300', '600227', '600222', '000123', '000129']
        hp.info()

        cp = qt.CashPlan(['2012-01-01', '2010-01-01'], [10000, 20000], 0.1)
        cp.info()
        cp = qt.CashPlan(['20100501'], 10000)
        cp.info()
        cp = qt.CashPlan(pd.date_range(start='2019-01-01', freq='Y', periods=12), [i * 1000 + 10000 for i in range(12)],
                      0.035)
        cp.info()

    def create_test_data(self):
        # build up test data: a 4-type, 3-share, 21-day matrix of prices that contains nan values in some days
        # for some share_pool

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
        share2_high = [7.06, 7.13, 7.15, 7.15, 7.14, 7.21, 7.27, 7.33, 7.39, np.nan, np.nan,
                       np.nan, np.nan, np.nan, np.nan, np.nan, 7.8, 8.11, 7.93, 7.8, 7.74]
        share2_low = [6.94, 6.94, 7.06, 7.05, 7.03, 7.06, 7.07, 7.1, 7.26, np.nan, np.nan,
                      np.nan, np.nan, np.nan, np.nan, np.nan, 7.37, 7.43, 7.33, 7.38, 7.44]

        # for share3:
        share3_close = [13.89, 14.13, 14.27, np.nan, np.nan, 14.53, 14.25, 14.56, 14.61,
                        14.61, 14.01, 13.85, 13.93, 14.00, 13.98, 13.85, 13.85, 13.99,
                        13.64, 13.82, 13.71]
        share3_open = [13.92, 13.85, 14.14, np.nan, np.nan, 14.38, 14.39, 14.26, 14.69,
                       14.68, 14.12, 13.99, 13.85, 14.02, 14., 13.95, 13.85, 13.86,
                       13.99, 13.63, 13.82]
        share3_high = [14.02, 14.16, 14.47, np.nan, np.nan, 14.8, 14.51, 14.58, 14.73,
                       14.77, 14.22, 13.99, 13.96, 14.04, 14.06, 14.08, 13.95, 14.01,
                       14.13, 13.84, 13.83]
        share3_low = [13.8, 13.8, 14.11, np.nan, np.nan, 14.15, 14.24, 14.14, 14.48,
                      14.5, 13.94, 13.79, 13.8, 13.91, 13.95, 13.83, 13.76, 13.8,
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

    def test_operator_generate(self):
        """

        :return:
        """
        self.op = qt.Operator(timing_types=['DMA'], selecting_types=['simple'], ricon_types=['urgent'])
        self.assertIsInstance(self.op, qt.Operator, 'Operator Creation Error')

    def test_operator_parameter_setting(self):
        """

        :return:
        """
        print('testing operator objects')
        self.op = qt.Operator(timing_types=['DMA'], selecting_types=['simple', 'random'], ricon_types=['urgent'])
        self.op.set_parameter('s-1', (0.5,))
        self.assertEqual(self.op.selecting[1].pars, (0.5,))



def suite():
    suite = unittest.TestSuite()
    # suite.addTest(TestHP())
    suite.addTest(TestOperator())
    suite.addTest(TestRates())
    suite.addTest(TestSpace())
    suite.addTest(TestUnify())
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())


