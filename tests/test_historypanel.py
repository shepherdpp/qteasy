# coding=utf-8
# ======================================
# File:     test_historypanel.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all HistoryPanel class
#   attributes and methods.
# ======================================
import unittest

import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, sec_to_duration, str_to_list
from qteasy.history import stack_dataframes, dataframe_to_hp, ffill_3d_data


class TestHistoryPanel(unittest.TestCase):
    def setUp(self):
        print('start testing HistoryPanel object\n')
        self.data = np.random.randint(10, size=(5, 10, 4))
        self.index = pd.date_range(start='20200101', freq='d', periods=10)
        self.index2 = ['2016-07-01', '2016-07-04', '2016-07-05', '2016-07-06',
                       '2016-07-07', '2016-07-08', '2016-07-11', '2016-07-12',
                       '2016-07-13', '2016-07-14']
        self.index3 = '2016-07-01, 2016-07-04, 2016-07-05, 2016-07-06, 2016-07-07, ' \
                      '2016-07-08, 2016-07-11, 2016-07-12, 2016-07-13, 2016-07-14'
        self.shares = '000100,000101,000102,000103,000104'
        self.htypes = 'close,open,high,low'
        self.data2 = np.random.randint(10, size=(10, 5))
        self.data3 = np.random.randint(10, size=(10, 4))
        self.data4 = np.random.randint(10, size=(10,))
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.htypes, rows=self.index)
        self.hp2 = qt.HistoryPanel(values=self.data2, levels=self.shares, columns='close', rows=self.index)
        self.hp3 = qt.HistoryPanel(values=self.data3, levels='000100', columns=self.htypes, rows=self.index2)
        self.hp4 = qt.HistoryPanel(values=self.data4, levels='000100', columns='close', rows=self.index3)
        self.hp5 = qt.HistoryPanel(values=self.data)
        self.hp6 = qt.HistoryPanel(values=self.data, levels=self.shares, rows=self.index3)

    def test_properties(self):
        """ test all properties of HistoryPanel
        """
        self.assertFalse(self.hp.is_empty)
        self.assertEqual(self.hp.row_count, 10)
        self.assertEqual(self.hp.column_count, 4)
        self.assertEqual(self.hp.level_count, 5)
        self.assertEqual(self.hp.shape, (5, 10, 4))
        self.assertSequenceEqual(self.hp.htypes, ['close', 'open', 'high', 'low'])
        self.assertSequenceEqual(self.hp.shares, ['000100', '000101', '000102', '000103', '000104'])
        self.assertSequenceEqual(list(self.hp.hdates), list(self.index))
        self.assertDictEqual(self.hp.columns, {'close': 0, 'open': 1, 'high': 2, 'low': 3})
        self.assertDictEqual(self.hp.levels, {'000100': 0, '000101': 1, '000102': 2, '000103': 3, '000104': 4})
        row_dict = {Timestamp('2020-01-01 00:00:00', freq='D'): 0,
                    Timestamp('2020-01-02 00:00:00', freq='D'): 1,
                    Timestamp('2020-01-03 00:00:00', freq='D'): 2,
                    Timestamp('2020-01-04 00:00:00', freq='D'): 3,
                    Timestamp('2020-01-05 00:00:00', freq='D'): 4,
                    Timestamp('2020-01-06 00:00:00', freq='D'): 5,
                    Timestamp('2020-01-07 00:00:00', freq='D'): 6,
                    Timestamp('2020-01-08 00:00:00', freq='D'): 7,
                    Timestamp('2020-01-09 00:00:00', freq='D'): 8,
                    Timestamp('2020-01-10 00:00:00', freq='D'): 9}
        self.assertDictEqual(self.hp.rows, row_dict)

    def test_len(self):
        """ test the function len(HistoryPanel)

        :return:
        """
        self.assertEqual(len(self.hp), 10)

    def test_empty_history_panel(self):
        """测试空HP或者特殊HP如维度标签为纯数字的HP"""
        test_hp = qt.HistoryPanel(self.data)
        self.assertFalse(test_hp.is_empty)
        self.assertIsInstance(test_hp, qt.HistoryPanel)
        self.assertEqual(test_hp.shape[0], 5)
        self.assertEqual(test_hp.shape[1], 10)
        self.assertEqual(test_hp.shape[2], 4)
        self.assertEqual(test_hp.level_count, 5)
        self.assertEqual(test_hp.row_count, 10)
        self.assertEqual(test_hp.column_count, 4)
        self.assertEqual(test_hp.shares, list(range(5)))
        self.assertEqual(test_hp.hdates, list(pd.date_range(start='20200730', periods=10, freq='d')))
        self.assertEqual(test_hp.htypes, list(range(4)))
        self.assertTrue(np.allclose(test_hp.values, self.data))
        print(f'shares: {test_hp.shares}\nhtypes: {test_hp.htypes}')
        print(test_hp)

        # HistoryPanel should be empty if no value is given
        empty_hp = qt.HistoryPanel()
        self.assertTrue(empty_hp.is_empty)
        self.assertIsInstance(empty_hp, qt.HistoryPanel)
        self.assertEqual(empty_hp.shape[0], 0)
        self.assertEqual(empty_hp.shape[1], 0)
        self.assertEqual(empty_hp.shape[2], 0)
        self.assertEqual(empty_hp.level_count, 0)
        self.assertEqual(empty_hp.row_count, 0)
        self.assertEqual(empty_hp.column_count, 0)

        # HistoryPanel should also be empty if empty value (np.array([])) is given
        empty_hp = qt.HistoryPanel(np.empty((5, 0, 4)), levels=self.shares, columns=self.htypes)
        self.assertTrue(empty_hp.is_empty)
        self.assertIsInstance(empty_hp, qt.HistoryPanel)
        self.assertEqual(empty_hp.shape[0], 0)
        self.assertEqual(empty_hp.shape[1], 0)
        self.assertEqual(empty_hp.shape[2], 0)
        self.assertEqual(empty_hp.level_count, 0)
        self.assertEqual(empty_hp.row_count, 0)
        self.assertEqual(empty_hp.column_count, 0)

    def test_create_history_panel(self):
        """ test the creation of a HistoryPanel object by passing all arr explicitly

        """
        self.assertIsInstance(self.hp, qt.HistoryPanel)
        self.assertEqual(self.hp.shape[0], 5)
        self.assertEqual(self.hp.shape[1], 10)
        self.assertEqual(self.hp.shape[2], 4)
        self.assertEqual(self.hp.level_count, 5)
        self.assertEqual(self.hp.row_count, 10)
        self.assertEqual(self.hp.column_count, 4)
        self.assertEqual(list(self.hp.levels.keys()), self.shares.split(','))
        self.assertEqual(list(self.hp.columns.keys()), self.htypes.split(','))
        self.assertEqual(list(self.hp.rows.keys())[0], pd.Timestamp('20200101'))

        self.assertIsInstance(self.hp2, qt.HistoryPanel)
        self.assertEqual(self.hp2.shape[0], 5)
        self.assertEqual(self.hp2.shape[1], 10)
        self.assertEqual(self.hp2.shape[2], 1)
        self.assertEqual(self.hp2.level_count, 5)
        self.assertEqual(self.hp2.row_count, 10)
        self.assertEqual(self.hp2.column_count, 1)
        self.assertEqual(list(self.hp2.levels.keys()), self.shares.split(','))
        self.assertEqual(list(self.hp2.columns.keys()), ['close'])
        self.assertEqual(list(self.hp2.rows.keys())[0], pd.Timestamp('20200101'))

        self.assertIsInstance(self.hp3, qt.HistoryPanel)
        self.assertEqual(self.hp3.shape[0], 1)
        self.assertEqual(self.hp3.shape[1], 10)
        self.assertEqual(self.hp3.shape[2], 4)
        self.assertEqual(self.hp3.level_count, 1)
        self.assertEqual(self.hp3.row_count, 10)
        self.assertEqual(self.hp3.column_count, 4)
        self.assertEqual(list(self.hp3.levels.keys()), ['000100'])
        self.assertEqual(list(self.hp3.columns.keys()), self.htypes.split(','))
        self.assertEqual(list(self.hp3.rows.keys())[0], pd.Timestamp('2016-07-01'))

        self.assertIsInstance(self.hp4, qt.HistoryPanel)
        self.assertEqual(self.hp4.shape[0], 1)
        self.assertEqual(self.hp4.shape[1], 10)
        self.assertEqual(self.hp4.shape[2], 1)
        self.assertEqual(self.hp4.level_count, 1)
        self.assertEqual(self.hp4.row_count, 10)
        self.assertEqual(self.hp4.column_count, 1)
        self.assertEqual(list(self.hp4.levels.keys()), ['000100'])
        self.assertEqual(list(self.hp4.columns.keys()), ['close'])
        self.assertEqual(list(self.hp4.rows.keys())[0], pd.Timestamp('2016-07-01'))

        self.hp5.info()
        self.assertIsInstance(self.hp5, qt.HistoryPanel)
        self.assertTrue(np.allclose(self.hp5.values, self.data))
        self.assertEqual(self.hp5.shape[0], 5)
        self.assertEqual(self.hp5.shape[1], 10)
        self.assertEqual(self.hp5.shape[2], 4)
        self.assertEqual(self.hp5.level_count, 5)
        self.assertEqual(self.hp5.row_count, 10)
        self.assertEqual(self.hp5.column_count, 4)
        self.assertEqual(list(self.hp5.levels.keys()), [0, 1, 2, 3, 4])
        self.assertEqual(list(self.hp5.columns.keys()), [0, 1, 2, 3])
        self.assertEqual(list(self.hp5.rows.keys())[0], pd.Timestamp('2020-07-30'))

        self.hp6.info()
        self.assertIsInstance(self.hp6, qt.HistoryPanel)
        self.assertTrue(np.allclose(self.hp6.values, self.data))
        self.assertEqual(self.hp6.shape[0], 5)
        self.assertEqual(self.hp6.shape[1], 10)
        self.assertEqual(self.hp6.shape[2], 4)
        self.assertEqual(self.hp6.level_count, 5)
        self.assertEqual(self.hp6.row_count, 10)
        self.assertEqual(self.hp6.column_count, 4)
        self.assertEqual(list(self.hp6.levels.keys()), ['000100', '000101', '000102', '000103', '000104'])
        self.assertEqual(list(self.hp6.columns.keys()), [0, 1, 2, 3])
        self.assertEqual(list(self.hp6.rows.keys())[0], pd.Timestamp('2016-07-01'))

        print('test creating HistoryPanel with very limited arr')
        print('test creating HistoryPanel with 2D arr')
        temp_data = np.random.randint(10, size=(7, 3)).astype('float')
        temp_hp = qt.HistoryPanel(temp_data)

        # Error testing during HistoryPanel creating
        # shape does not match
        self.assertRaises(AssertionError,
                          qt.HistoryPanel,
                          self.data,
                          levels=self.shares, columns='close', rows=self.index)
        # valus is not np.ndarray
        self.assertRaises(TypeError,
                          qt.HistoryPanel,
                          list(self.data))
        # dimension/shape does not match
        self.assertRaises(AssertionError,
                          qt.HistoryPanel,
                          self.data2,
                          levels='000100', columns=self.htypes, rows=self.index)
        # value dimension over 3
        self.assertRaises(AssertionError,
                          qt.HistoryPanel,
                          np.random.randint(10, size=(5, 10, 4, 2)))
        # lebel value not valid
        self.assertRaises(ValueError,
                          qt.HistoryPanel,
                          self.data2,
                          levels=self.shares, columns='close',
                          rows='a,b,c,d,e,f,g,h,i,j')

    def test_history_panel_slicing(self):
        """测试HistoryPanel的各种切片方法
        包括通过标签名称切片，通过数字切片，通过逗号分隔的标签名称切片，通过冒号分隔的标签名称切片等切片方式"""
        self.assertTrue(np.allclose(self.hp['close'], self.data[:, :, 0:1]))
        self.assertTrue(np.allclose(self.hp['close,open'], self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp[['close', 'open']], self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp['close:high'], self.data[:, :, 0:3]))
        self.assertTrue(np.allclose(self.hp['close,high'], self.data[:, :, [0, 2]]))
        self.assertTrue(np.allclose(self.hp[:, '000100'], self.data[0:1, :, ]))
        self.assertTrue(np.allclose(self.hp[:, '000100,000101'], self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:, ['000100', '000101']], self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:, '000100:000102'], self.data[0:3, :]))
        self.assertTrue(np.allclose(self.hp[:, '000100,000102'], self.data[[0, 2], :]))
        self.assertTrue(np.allclose(self.hp['close,open', '000100,000102'], self.data[[0, 2], :, 0:2]))
        print('start testing HistoryPanel')
        data = np.random.randint(10, size=(10, 5))
        # index = pd.date_range(start='20200101', freq='d', periods=10)
        shares = '000100,000101,000102,000103,000104'
        dtypes = 'close'
        df = pd.DataFrame(data)
        print('=========================\nTesting HistoryPanel creation from DataFrame')
        hp = qt.dataframe_to_hp(df=df, shares=shares, htypes=dtypes)
        hp.info()
        hp = qt.dataframe_to_hp(df=df, shares='000100', htypes='close, open, high, low, middle', column_type='htypes')
        hp.info()

        print('=========================\nTesting HistoryPanel creation from initialization')
        data = np.random.randint(10, size=(5, 10, 4)).astype('float')
        index = pd.date_range(start='20200101', freq='d', periods=10)
        dtypes = 'close, open, high,low'
        data[0, [5, 6, 9], [0, 1, 3]] = np.nan
        data[1:4, [4, 7, 6, 2], [1, 1, 3, 0]] = np.nan
        data[4:5, [2, 9, 1, 2], [0, 3, 2, 1]] = np.nan
        hp = qt.HistoryPanel(data, levels=shares, columns=dtypes, rows=index)
        hp.info()
        print('==========================\n输出close类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close', :, :], data[:, :, 0:1], equal_nan=True))
        print(f'==========================\n输出close和open类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1], :, :], data[:, :, 0:2], equal_nan=True))
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
        print(f'arr is:\n{data}')
        hp.htypes = 'open,high,low,close'
        hp.info()
        hp.shares = ['000300', '600227', '600222', '000123', '000129']
        hp.info()

    def test_segment(self):
        """测试历史数据片段的获取"""
        test_hp = qt.HistoryPanel(self.data,
                                  levels=self.shares,
                                  columns=self.htypes,
                                  rows=self.index2)
        self.assertFalse(test_hp.is_empty)
        self.assertIsInstance(test_hp, qt.HistoryPanel)
        self.assertEqual(test_hp.shape[0], 5)
        self.assertEqual(test_hp.shape[1], 10)
        self.assertEqual(test_hp.shape[2], 4)
        print(f'Test segment with None parameters')
        seg1 = test_hp.segment()
        seg2 = test_hp.segment('20150202')
        seg3 = test_hp.segment(end_date='20201010')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        self.assertIsInstance(seg2, qt.HistoryPanel)
        self.assertIsInstance(seg3, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp.values
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp.values
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp.values
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        self.assertEqual(seg2.htypes, test_hp.htypes)
        self.assertEqual(seg2.shares, test_hp.shares)
        self.assertEqual(seg3.htypes, test_hp.htypes)
        self.assertEqual(seg3.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)
        self.assertEqual(seg2.hdates, test_hp.hdates)
        self.assertEqual(seg3.hdates, test_hp.hdates)

        print(f'Test segment with proper dates')
        seg1 = test_hp.segment()
        seg2 = test_hp.segment('20160704')
        seg3 = test_hp.segment(start_date='2016-07-05',
                               end_date='20160708')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        self.assertIsInstance(seg2, qt.HistoryPanel)
        self.assertIsInstance(seg3, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp[:, :, :]
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp[:, :, 1:10]
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp[:, :, 2:6]
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        self.assertEqual(seg2.htypes, test_hp.htypes)
        self.assertEqual(seg2.shares, test_hp.shares)
        self.assertEqual(seg3.htypes, test_hp.htypes)
        self.assertEqual(seg3.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)
        self.assertEqual(seg2.hdates, test_hp.hdates[1:10])
        self.assertEqual(seg3.hdates, test_hp.hdates[2:6])

        print(f'Test segment with non-existing but in range dates')
        seg1 = test_hp.segment()
        seg2 = test_hp.segment('20160703')
        seg3 = test_hp.segment(start_date='2016-07-03',
                               end_date='20160710')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        self.assertIsInstance(seg2, qt.HistoryPanel)
        self.assertIsInstance(seg3, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp[:, :, :]
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp[:, :, 1:10]
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp[:, :, 1:6]
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        self.assertEqual(seg2.htypes, test_hp.htypes)
        self.assertEqual(seg2.shares, test_hp.shares)
        self.assertEqual(seg3.htypes, test_hp.htypes)
        self.assertEqual(seg3.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)
        self.assertEqual(seg2.hdates, test_hp.hdates[1:10])
        self.assertEqual(seg3.hdates, test_hp.hdates[1:6])

        print(f'Test segment with out-of-range dates')
        seg1 = test_hp.segment(start_date='2016-05-03',
                               end_date='20160910')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp[:, :, :]
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)

    def test_slice(self):
        """测试历史数据切片的获取"""
        test_hp = qt.HistoryPanel(self.data,
                                  levels=self.shares,
                                  columns=self.htypes,
                                  rows=self.index2)
        self.assertFalse(test_hp.is_empty)
        self.assertIsInstance(test_hp, qt.HistoryPanel)
        self.assertEqual(test_hp.shape[0], 5)
        self.assertEqual(test_hp.shape[1], 10)
        self.assertEqual(test_hp.shape[2], 4)
        print(f'Test slice with shares')
        share = '000101'
        slc = test_hp.slice(shares=share)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000101'])
        self.assertEqual(slc.htypes, test_hp.htypes)
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp[:, '000101']))

        share = '000101, 000103'
        slc = test_hp.slice(shares=share)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000101', '000103'])
        self.assertEqual(slc.htypes, test_hp.htypes)
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp[:, '000101, 000103']))

        print(f'Test slice with htypes')
        htype = 'open'
        slc = test_hp.slice(htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, test_hp.shares)
        self.assertEqual(slc.htypes, ['open'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['open']))

        htype = 'open, close'
        slc = test_hp.slice(htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, test_hp.shares)
        self.assertEqual(slc.htypes, ['open', 'close'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['open, close']))
        # test that slicing of "open, close" does NOT equal to "close, open"
        self.assertFalse(np.allclose(slc.values, test_hp['close, open']))

        print(f'Test slicing with both htypes and shares')
        share = '000103, 000101'
        htype = 'high, low, close'
        slc = test_hp.slice(shares=share, htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000103', '000101'])
        self.assertEqual(slc.htypes, ['high', 'low', 'close'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['high, low, close', '000103, 000101']))

        print(f'Test Error cases')
        # duplicated input
        htype = 'open, close, open'
        self.assertRaises(AssertionError, test_hp.slice, htypes=htype)

    def test_relabel(self):
        new_shares_list = ['000001', '000002', '000003', '000004', '000005']
        new_shares_str = '000001, 000002, 000003, 000004, 000005'
        new_htypes_list = ['close', 'volume', 'value', 'exchange']
        new_htypes_str = 'close, volume, value, exchange'
        temp_hp = self.hp.copy()
        temp_hp.re_label(shares=new_shares_list)
        print(temp_hp.info())
        print(temp_hp.htypes)
        self.assertTrue(np.allclose(self.hp.values, temp_hp.values))
        self.assertEqual(self.hp.htypes, temp_hp.htypes)
        self.assertEqual(self.hp.hdates, temp_hp.hdates)
        self.assertEqual(temp_hp.shares, new_shares_list)
        temp_hp = self.hp.copy()
        temp_hp.re_label(shares=new_shares_str)
        self.assertTrue(np.allclose(self.hp.values, temp_hp.values))
        self.assertEqual(self.hp.htypes, temp_hp.htypes)
        self.assertEqual(self.hp.hdates, temp_hp.hdates)
        self.assertEqual(temp_hp.shares, new_shares_list)
        temp_hp = self.hp.copy()
        temp_hp.re_label(htypes=new_htypes_list)
        self.assertTrue(np.allclose(self.hp.values, temp_hp.values))
        self.assertEqual(self.hp.shares, temp_hp.shares)
        self.assertEqual(self.hp.hdates, temp_hp.hdates)
        self.assertEqual(temp_hp.htypes, new_htypes_list)
        temp_hp = self.hp.copy()
        temp_hp.re_label(htypes=new_htypes_str)
        self.assertTrue(np.allclose(self.hp.values, temp_hp.values))
        self.assertEqual(self.hp.shares, temp_hp.shares)
        self.assertEqual(self.hp.hdates, temp_hp.hdates)
        self.assertEqual(temp_hp.htypes, new_htypes_list)
        print(f'test errors raising')
        temp_hp = self.hp.copy()
        self.assertRaises(AssertionError, temp_hp.re_label, htypes=new_shares_str)
        self.assertRaises(TypeError, temp_hp.re_label, htypes=123)
        self.assertRaises(AssertionError, temp_hp.re_label, htypes='wrong input!')

    def test_csv_to_hp(self):
        """ 测试从csv文件中读取HistoryPanel"""
        # TODO: implement this test
        pass

    def test_hdf_to_hp(self):
        """ 测试从hdf文件中读取HistoryPanel"""
        # TODO: implement this test
        pass

    def test_hp_join(self):
        # TODO: 这里需要加强，需要用具体的例子确认hp_join的结果正确
        #  尤其是不同的shares、htypes、hdates，以及它们在顺
        #  序不同的情况下是否能正确地组合
        print(f'join two simple HistoryPanels with same shares')
        temp_hp = self.hp.join(self.hp2, same_shares=True)
        self.assertIsInstance(temp_hp, qt.HistoryPanel)

    def test_df_to_hp(self):
        print(f'test converting DataFrame to HistoryPanel')
        data = np.random.randint(10, size=(10, 5))
        df1 = pd.DataFrame(data)
        df2 = pd.DataFrame(data, columns=str_to_list(self.shares))
        df3 = pd.DataFrame(data[:, 0:4])
        df4 = pd.DataFrame(data[:, 0:4], columns=str_to_list(self.htypes))
        hp = qt.dataframe_to_hp(df1, htypes='close')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, [0, 1, 2, 3, 4])
        self.assertEqual(hp.htypes, ['close'])
        self.assertEqual(hp.hdates, [pd.Timestamp('1970-01-01 00:00:00'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000001'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000002'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000003'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000004'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000005'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000006'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000007'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000008'),
                                     pd.Timestamp('1970-01-01 00:00:00.000000009')])
        hp = qt.dataframe_to_hp(df2, shares=self.shares, htypes='close')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, str_to_list(self.shares))
        self.assertEqual(hp.htypes, ['close'])
        hp = qt.dataframe_to_hp(df3, shares='000100', column_type='htypes')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, ['000100'])
        self.assertEqual(hp.htypes, [0, 1, 2, 3])
        hp = qt.dataframe_to_hp(df4, shares='000100', htypes=self.htypes, column_type='htypes')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, ['000100'])
        self.assertEqual(hp.htypes, str_to_list(self.htypes))
        hp.info()
        self.assertRaises(KeyError, qt.dataframe_to_hp, df1)

    # noinspection PyTypeChecker
    def test_to_dataframe(self):
        """ 测试HistoryPanel对象的to_dataframe方法

        """
        print(f'START TEST == test_to_dataframe')
        print(f'test converting test hp to dataframe with share == "000102":')
        df_test = self.hp.slice_to_dataframe(share='000102')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.htypes), list(df_test.columns))
        values = df_test.values
        self.assertTrue(np.allclose(self.hp[:, '000102'], values))

        print(f'test DataFrame conversion with share == "000100"')
        df_test = self.hp.slice_to_dataframe(share='000100')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.htypes), list(df_test.columns))
        values = df_test.values
        self.assertTrue(np.allclose(self.hp[:, '000100'], values))

        print(f'test DataFrame conversion error: type incorrect')
        self.assertRaises(AssertionError, self.hp.slice_to_dataframe, share=3.0)

        print(f'test DataFrame error raising with share not found error')
        self.assertRaises(KeyError, self.hp.slice_to_dataframe, share='000300')

        print(f'test DataFrame conversion with htype == "close"')
        df_test = self.hp.slice_to_dataframe(htype='close')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        # noinspection PyTypeChecker
        self.assertTrue(np.allclose(self.hp['close'].T, values))

        print(f'test DataFrame conversion with htype == "high"')
        df_test = self.hp.slice_to_dataframe(htype='high')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        # noinspection PyTypeChecker
        self.assertTrue(np.allclose(self.hp['high'].T, values))

        print(f'test DataFrame conversion with htype == "high" and dropna')
        v = self.hp.values.astype('float')
        v[:, 3, :] = np.nan
        v[:, 4, :] = np.inf
        test_hp = qt.HistoryPanel(v, levels=self.shares, columns=self.htypes, rows=self.index)
        df_test = test_hp.slice_to_dataframe(htype='high', dropna=True)
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates[:3]) + list(self.hp.hdates[4:]), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        target_values = test_hp['high'].T
        target_values = target_values[np.where(~np.isnan(target_values))].reshape(9, 5)
        self.assertTrue(np.allclose(target_values, values))

        print(f'test DataFrame conversion with htype == "high", dropna and treat infs as na')
        v = self.hp.values.astype('float')
        v[:, 3, :] = np.nan
        v[:, 4, :] = np.inf
        test_hp = qt.HistoryPanel(v, levels=self.shares, columns=self.htypes, rows=self.index)
        df_test = test_hp.slice_to_dataframe(htype='high', dropna=True, inf_as_na=True)
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates[:3]) + list(self.hp.hdates[5:]), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        target_values = test_hp['high'].T
        target_values = target_values[np.where(~np.isnan(target_values) & ~np.isinf(target_values))].reshape(8, 5)
        self.assertTrue(np.allclose(target_values, values))

        print(f'test DataFrame conversion error: type incorrect')
        self.assertRaises(AssertionError, self.hp.slice_to_dataframe, htype=pd.DataFrame())

        print(f'test DataFrame error raising with share not found error')
        self.assertRaises(KeyError, self.hp.slice_to_dataframe, htype='non_type')

        print(f'Raises ValueError when both or none parameter is given')
        self.assertRaises(KeyError, self.hp.slice_to_dataframe)
        self.assertRaises(KeyError, self.hp.slice_to_dataframe, share='000100', htype='close')

    def test_to_df_dict(self):
        """测试HistoryPanel公有方法to_df_dict"""

        print('test convert history panel slice by share')
        df_dict = self.hp.to_df_dict('share')
        self.assertEqual(self.hp.shares, list(df_dict.keys()))
        df_dict = self.hp.to_df_dict()
        self.assertEqual(self.hp.shares, list(df_dict.keys()))

        print('test convert historypanel slice by htype ')
        df_dict = self.hp.to_df_dict('htype')
        self.assertEqual(self.hp.htypes, list(df_dict.keys()))

        print('test raise assertion error')
        self.assertRaises(AssertionError, self.hp.to_df_dict, by='random text')
        self.assertRaises(TypeError, self.hp.to_df_dict, by=3)

        print('test empty hp')
        df_dict = qt.HistoryPanel().to_df_dict('share')
        self.assertEqual(df_dict, {})

    def test_stack_dataframes(self):
        print('test stack dataframes in a list')
        df1 = pd.DataFrame({'a': [1, 2, 3, 4], 'b': [2, 3, 4, 5], 'c': [3, 4, 5, 6]})
        df1.index = ['20200101', '20200102', '20200103', '20200104']
        df2 = pd.DataFrame({'b': [4, 3, 2, 1], 'd': [1, 1, 1, 1], 'c': [6, 5, 4, 3]})
        df2.index = ['20200101', '20200102', '20200104', '20200105']
        df3 = pd.DataFrame({'a': [6, 6, 6, 6], 'd': [4, 4, 4, 4], 'b': [2, 4, 6, 8]})
        df3.index = ['20200101', '20200102', '20200103', '20200106']
        values1 = np.array([[[1., 2., 3., np.nan],
                             [2., 3., 4., np.nan],
                             [3., 4., 5., np.nan],
                             [4., 5., 6., np.nan],
                             [np.nan, np.nan, np.nan, np.nan],
                             [np.nan, np.nan, np.nan, np.nan]],
                            [[np.nan, 4., 6., 1.],
                             [np.nan, 3., 5., 1.],
                             [np.nan, np.nan, np.nan, np.nan],
                             [np.nan, 2., 4., 1.],
                             [np.nan, 1., 3., 1.],
                             [np.nan, np.nan, np.nan, np.nan]],
                            [[6., 2., np.nan, 4.],
                             [6., 4., np.nan, 4.],
                             [6., 6., np.nan, 4.],
                             [np.nan, np.nan, np.nan, np.nan],
                             [np.nan, np.nan, np.nan, np.nan],
                             [6., 8., np.nan, 4.]]])
        values2 = np.array([[[1., np.nan, 6.],
                             [2., np.nan, 6.],
                             [3., np.nan, 6.],
                             [4., np.nan, np.nan],
                             [np.nan, np.nan, np.nan],
                             [np.nan, np.nan, 6.]],
                            [[2., 4., 2.],
                             [3., 3., 4.],
                             [4., np.nan, 6.],
                             [5., 2., np.nan],
                             [np.nan, 1., np.nan],
                             [np.nan, np.nan, 8.]],
                            [[3., 6., np.nan],
                             [4., 5., np.nan],
                             [5., np.nan, np.nan],
                             [6., 4., np.nan],
                             [np.nan, 3., np.nan],
                             [np.nan, np.nan, np.nan]],
                            [[np.nan, 1., 4.],
                             [np.nan, 1., 4.],
                             [np.nan, np.nan, 4.],
                             [np.nan, 1., np.nan],
                             [np.nan, 1., np.nan],
                             [np.nan, np.nan, 4.]]])
        print(df1.rename(index=pd.to_datetime))
        print(df2.rename(index=pd.to_datetime))
        print(df3.rename(index=pd.to_datetime))

        hp1 = stack_dataframes([df1, df2, df3], dataframe_as='shares',
                               shares=['000100', '000200', '000300'])
        hp2 = stack_dataframes([df1, df2, df3], dataframe_as='shares',
                               shares='000100, 000300, 000200')
        print('hp1 is:\n', hp1)
        print('hp2 is:\n', hp2)
        self.assertEqual(hp1.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp1.shares, ['000100', '000200', '000300'])
        self.assertTrue(np.allclose(hp1.values, values1, equal_nan=True))
        self.assertEqual(hp2.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp2.shares, ['000100', '000300', '000200'])
        self.assertTrue(np.allclose(hp2.values, values1, equal_nan=True))

        hp3 = stack_dataframes([df1, df2, df3], dataframe_as='htypes',
                               htypes=['close', 'high', 'low'])
        hp4 = stack_dataframes([df1, df2, df3], dataframe_as='htypes',
                               htypes='open, close, high')
        print('hp3 is:\n', hp3.values)
        print('hp4 is:\n', hp4.values)
        self.assertEqual(hp3.htypes, ['close', 'high', 'low'])
        self.assertEqual(hp3.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp3.values, values2, equal_nan=True))
        self.assertEqual(hp4.htypes, ['open', 'close', 'high'])
        self.assertEqual(hp4.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp4.values, values2, equal_nan=True))

        print('test stack dataframes in a dict')
        df1 = pd.DataFrame({'a': [1, 2, 3, 4], 'b': [2, 3, 4, 5], 'c': [3, 4, 5, 6]})
        df1.index = ['20200101', '20200102', '20200103', '20200104']
        df2 = pd.DataFrame({'b': [4, 3, 2, 1], 'd': [1, 1, 1, 1], 'c': [6, 5, 4, 3]})
        df2.index = ['20200101', '20200102', '20200104', '20200105']
        df3 = pd.DataFrame({'a': [6, 6, 6, 6], 'd': [4, 4, 4, 4], 'b': [2, 4, 6, 8]})
        df3.index = ['20200101', '20200102', '20200103', '20200106']
        values1 = np.array([[[1., 2., 3., np.nan],
                             [2., 3., 4., np.nan],
                             [3., 4., 5., np.nan],
                             [4., 5., 6., np.nan],
                             [np.nan, np.nan, np.nan, np.nan],
                             [np.nan, np.nan, np.nan, np.nan]],
                            [[np.nan, 4., 6., 1.],
                             [np.nan, 3., 5., 1.],
                             [np.nan, np.nan, np.nan, np.nan],
                             [np.nan, 2., 4., 1.],
                             [np.nan, 1., 3., 1.],
                             [np.nan, np.nan, np.nan, np.nan]],
                            [[6., 2., np.nan, 4.],
                             [6., 4., np.nan, 4.],
                             [6., 6., np.nan, 4.],
                             [np.nan, np.nan, np.nan, np.nan],
                             [np.nan, np.nan, np.nan, np.nan],
                             [6., 8., np.nan, 4.]]])
        values2 = np.array([[[1., np.nan, 6.],
                             [2., np.nan, 6.],
                             [3., np.nan, 6.],
                             [4., np.nan, np.nan],
                             [np.nan, np.nan, np.nan],
                             [np.nan, np.nan, 6.]],
                            [[2., 4., 2.],
                             [3., 3., 4.],
                             [4., np.nan, 6.],
                             [5., 2., np.nan],
                             [np.nan, 1., np.nan],
                             [np.nan, np.nan, 8.]],
                            [[3., 6., np.nan],
                             [4., 5., np.nan],
                             [5., np.nan, np.nan],
                             [6., 4., np.nan],
                             [np.nan, 3., np.nan],
                             [np.nan, np.nan, np.nan]],
                            [[np.nan, 1., 4.],
                             [np.nan, 1., 4.],
                             [np.nan, np.nan, 4.],
                             [np.nan, 1., np.nan],
                             [np.nan, 1., np.nan],
                             [np.nan, np.nan, 4.]]])
        print(df1.rename(index=pd.to_datetime))
        print(df2.rename(index=pd.to_datetime))
        print(df3.rename(index=pd.to_datetime))

        hp1 = stack_dataframes(dfs={'000001.SZ': df1, '000002.SZ': df2, '000003.SZ': df3},
                               dataframe_as='shares')
        hp2 = stack_dataframes(dfs={'000001.SZ': df1, '000002.SZ': df2, '000003.SZ': df3},
                               dataframe_as='shares',
                               shares='000100, 000300, 000200')
        print('hp1 is:\n', hp1)
        print('hp2 is:\n', hp2)
        self.assertEqual(hp1.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp1.shares, ['000001.SZ', '000002.SZ', '000003.SZ'])
        self.assertTrue(np.allclose(hp1.values, values1, equal_nan=True))
        self.assertEqual(hp2.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp2.shares, ['000100', '000300', '000200'])
        self.assertTrue(np.allclose(hp2.values, values1, equal_nan=True))

        hp3 = stack_dataframes(dfs={'close': df1, 'high': df2, 'low': df3},
                               dataframe_as='htypes')
        hp4 = stack_dataframes(dfs={'close': df1, 'low': df2, 'high': df3},
                               dataframe_as='htypes',
                               htypes='open, close, high')
        print('hp3 is:\n', hp3.values)
        print('hp4 is:\n', hp4.values)
        self.assertEqual(hp3.htypes, ['close', 'high', 'low'])
        self.assertEqual(hp3.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp3.values, values2, equal_nan=True))
        self.assertEqual(hp4.htypes, ['open', 'close', 'high'])
        self.assertEqual(hp4.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp4.values, values2, equal_nan=True))

    def test_to_csv(self):
        """ 测试将HistoryPanel保存为csv文件"""
        # TODO: implement this test
        pass

    def test_to_hdf(self):
        """ 测试将HistoryPanel保存为hdf文件"""
        # TODO: implement this test
        pass

    def test_fill_na(self):
        """测试填充无效值"""
        print(self.hp)
        new_values = self.hp.values.astype(float)
        new_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = np.nan
        print(new_values)
        temp_hp = qt.HistoryPanel(values=new_values, levels=self.hp.levels, rows=self.hp.rows, columns=self.hp.columns)
        self.assertTrue(np.allclose(temp_hp.values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]], np.nan, equal_nan=True))
        temp_hp.fillna(2.3)
        filled_values = new_values.copy()
        filled_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = 2.3
        self.assertTrue(np.allclose(temp_hp.values,
                                    filled_values, equal_nan=True))

    def test_fill_inf(self):
        """测试填充无限值"""

    def test_ffill(self):
        """ 测试前向填充函数"""
        # print(f'original values of history panel: \n{self.hp.values}')
        new_values = self.hp.values.astype(float)
        new_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = np.nan
        # print(f'values with nan from origin: \n{new_values}')
        temp_hp = qt.HistoryPanel(values=new_values, levels=self.hp.levels, rows=self.hp.rows, columns=self.hp.columns)
        self.assertTrue(np.allclose(temp_hp.values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]], np.nan, equal_nan=True))
        before_ffill = new_values.copy()
        temp_hp.ffill()
        print(f'ffilled values result and target side by side:')
        for i in range(5):
            print(f'values before ffill: \n{before_ffill[i]}')
            print(f'values after ffill: \n{temp_hp.values[i]}')
        self.assertTrue(np.allclose(new_values, temp_hp.values, 7, equal_nan=True))
        where_nan = list(np.where(np.isnan(temp_hp.values)))
        self.assertEqual(where_nan, [np.array(3), np.array(0), np.array(2)])

        # test ffill with init value
        # print(f'original values of history panel: \n{self.hp.values}')
        new_values = self.hp.values.astype(float)
        new_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = np.nan
        # print(f'values with nan from origin: \n{new_values}')
        temp_hp = qt.HistoryPanel(values=new_values, levels=self.hp.levels, rows=self.hp.rows, columns=self.hp.columns)
        self.assertTrue(np.allclose(temp_hp.values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]], np.nan, equal_nan=True))
        before_ffill = new_values.copy()
        temp_hp.ffill(0)
        print(f'ffilled values result and target side by side:')
        for i in range(5):
            print(f'values before ffill: \n{before_ffill[i]}')
            print(f'values after ffill: \n{temp_hp.values[i]}')
        self.assertTrue(np.allclose(new_values, temp_hp.values, 7, equal_nan=True))
        self.assertTrue(np.all(~np.isnan(temp_hp.values)))

    def test_ffill_data(self):
        """ 测试前向填充NaN值"""
        d = np.array([[[0.03, 0.88, 0.2],
                       [0.62, np.nan, np.nan],
                       [0.46, np.nan, 0.37],
                       [0.52, np.nan, 0.84],
                       [0.1, 0.42, 0.32]],

                      [[0.67, 0.05, 0.97],
                       [0.05, 0.47, 0.14],
                       [0.25, 0.36, 0.32],
                       [np.nan, np.nan, np.nan],
                       [0.81, 0.94, 0.04]]])

        t = np.array([[[0.03, 0.88, 0.2],
                       [0.62, 0.88, 0.2],
                       [0.46, 0.88, 0.37],
                       [0.52, 0.88, 0.84],
                       [0.1, 0.42, 0.32]],

                      [[0.67, 0.05, 0.97],
                       [0.05, 0.47, 0.14],
                       [0.25, 0.36, 0.32],
                       [0.25, 0.36, 0.32],
                       [0.81, 0.94, 0.04]]])
        self.assertTrue(np.allclose(ffill_3d_data(d, 0), t))

        d = np.array([[[np.nan, 0.88, 0.2],
                       [0.62, np.nan, np.nan],
                       [0.46, np.nan, 0.37],
                       [0.52, np.nan, 0.84],
                       [0.1, 0.42, 0.32]],

                      [[0.67, np.nan, 0.97],
                       [0.05, 0.47, 0.14],
                       [0.25, 0.36, 0.32],
                       [np.nan, np.nan, np.nan],
                       [0.81, 0.94, 0.04]]])

        t = np.array([[[0.0, 0.88, 0.2],
                       [0.62, 0.88, 0.2],
                       [0.46, 0.88, 0.37],
                       [0.52, 0.88, 0.84],
                       [0.1, 0.42, 0.32]],

                      [[0.67, 0., 0.97],
                       [0.05, 0.47, 0.14],
                       [0.25, 0.36, 0.32],
                       [0.25, 0.36, 0.32],
                       [0.81, 0.94, 0.04]]])
        self.assertTrue(np.allclose(ffill_3d_data(d, 0), t))

    def test_get_history_panel(self):
        """ 测试是否能正确获取HistoryPanel"""
        print('test get history panel data')  #
        hp = qt.history.get_history_panel(htypes='wt-000003.SH, close, wt-000300.SH',
                                          shares='000001.SZ, 000002.SZ, 900901.SH, 601728.SH', start='20210101',
                                          end='20210802', freq='m', asset_type='any', adj='none')
        self.assertEqual(hp.htypes, ['wt-000003.SH', 'close', 'wt-000300.SH'])
        self.assertEqual(hp.shares, ['000001.SZ', '000002.SZ', '900901.SH', '601728.SH'])
        print(hp)

        print('test get history panel data without shares')
        hp = qt.history.get_history_panel(htypes='close-000002.SZ, pe-000001.SZ, open-000300.SH', shares=None,
                                          start='20210101', end='20210202', freq='d', asset_type='any', adj='none',
                                          drop_nan=True)
        self.assertEqual(hp.htypes, ['close-000002.SZ', 'pe-000001.SZ', 'open-000300.SH'])
        self.assertEqual(hp.shares, ['none'])
        print(hp)

        print('test get history panel data from converting multiple frequencies')
        hp = qt.history.get_history_panel(htypes='wt-000003.SH, close, pe, eps, revenue_ps',
                                          shares='000001.SZ, 000002.SZ, 900901.SH, 601728.SH', start='20210101',
                                          end='20210502', freq='w', asset_type='any', adj='none', drop_nan=True)
        self.assertEqual(hp.htypes, ['wt-000003.SH', 'close', 'pe', 'eps', 'revenue_ps'])
        self.assertEqual(hp.shares, ['000001.SZ', '000002.SZ', '900901.SH', '601728.SH'])
        print(hp)

        print('test get history panel data with / without all NaN values')
        hp = qt.history.get_history_panel(htypes='open, high, low, close', shares='000002.SZ, 000001.SZ, 000300.SH',
                                          start='20210101', end='20210115', freq='d', asset_type='any', adj='none',
                                          drop_nan=False, resample_method='none', b_days_only=False)
        print(hp)
        self.assertEqual(hp.htypes, ['open', 'high', 'low', 'close'])
        self.assertEqual(hp.shares, ['000002.SZ', '000001.SZ', '000300.SH'])
        first_3_rows = hp[:, :, 0:3]
        row_9_til_10 = hp[:, :, 8:10]
        self.assertTrue(np.all(np.isnan(first_3_rows)))
        self.assertTrue(np.all(np.isnan(row_9_til_10)))

        print('test getting history panel specific asset_type')
        hp = qt.history.get_history_panel(htypes='open, high, low, close', shares='000002.SZ, 000001.SZ, 000300.SH',
                                          start='20210101', end='20210115', freq='d', asset_type='E', adj='f')
        print(hp)
        self.assertEqual(hp.htypes, ['open', 'high', 'low', 'close'])
        self.assertEqual(hp.shares, ['000002.SZ', '000001.SZ', '000300.SH'])
        all_idx_data = hp[:, '000300.SH']
        self.assertTrue(np.all(np.isnan(all_idx_data)))

        print('test getting history panel with wrong parameters')
        print('datetime not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          htypes='open, high, low, close',
                          start='not_a_time',
                          end='20210115',
                          freq='d',
                          asset_type='E',
                          adj='f')
        print('freq not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          htypes='open, high, low, close',
                          start='20210101',
                          end='20210115',
                          freq='wrong_freq',
                          asset_type='E',
                          adj='f')
        print('asset_type not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          htypes='open, high, low, close',
                          start='202101001',
                          end='20210115',
                          freq='d',
                          asset_type='wront_asset_type',
                          adj='f')
        print('adj not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          htypes='open, high, low, close',
                          start='202101001',
                          end='20210115',
                          freq='d',
                          asset_type='E',
                          adj='wrong_adj')

    def test_flatten_to_dataframe(self):
        """ 测试函数 flatten_to_dataframe() """

        hp = self.hp
        print('test flatten_to_dataframe(along="row")')
        df = hp.flatten_to_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (hp.shape[0] * hp.shape[1], hp.shape[2]))
        self.assertEqual(df.columns.to_list(), hp.htypes)
        for share in hp.shares:
            self.assertTrue(np.allclose(df.loc[share].values, hp[:, share].squeeze()))

        print('test flatten_to_dataframe(along="col")')
        df = hp.flatten_to_dataframe(along='col')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (hp.shape[1], hp.shape[0] * hp.shape[2]))
        self.assertEqual(df.index.to_list(), hp.hdates)
        for share in hp.shares:
            self.assertTrue(np.allclose(df[share].values, hp[:, share].squeeze()))

        print('test error raises')
        self.assertRaises(TypeError, hp.flatten_to_dataframe, along=35)
        self.assertRaises(ValueError, hp.flatten_to_dataframe, along='wrong_value')
        self.assertRaises(Exception, hp.flatten_to_dataframe, along='col', drop_nan=True)
        # test empty history panel
        hp = qt.HistoryPanel()
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertIsInstance(hp.flatten_to_dataframe(), pd.DataFrame)
        self.assertTrue(hp.flatten_to_dataframe().empty)

    def test_head_and_tail(self):
        """ 测试函数 head() 和 ellipsis() """

        hp = self.hp

        head = hp.head(3)
        print(f'test head()\nhp is {hp}\nhead(3) is {head}')
        self.assertIsInstance(head, qt.HistoryPanel)
        self.assertEqual(head.shape, (hp.shape[0], 3, hp.shape[2]))
        self.assertEqual(head.hdates, hp.hdates[0:3])
        self.assertEqual(head.htypes, hp.htypes)
        self.assertEqual(head.shares, hp.shares)
        self.assertTrue(np.allclose(head.values, hp.values[:, 0:3]))

        tail = hp.tail(3)
        print(f'test ellipsis()\nhp is {hp}\nellipsis(3) is {tail}')
        self.assertIsInstance(tail, qt.HistoryPanel)
        self.assertEqual(tail.shape, (hp.shape[0], 3, hp.shape[2]))
        self.assertEqual(tail.hdates, hp.hdates[-3:])
        self.assertEqual(tail.htypes, hp.htypes)
        self.assertEqual(tail.shares, hp.shares)
        self.assertTrue(np.allclose(tail.values, hp.values[:, -3:]))

        head = hp.flattened_head(3)
        print(f'test flattened_head()\nhp is \n{hp}\n flattened_head(3):\n{head}')
        self.assertIsInstance(head, pd.DataFrame)
        self.assertEqual(head.shape, (3, hp.shape[0] * hp.shape[2]))
        self.assertEqual(list(head.index), hp.hdates[0:3])
        self.assertEqual(head.columns.unique(level=1).to_list(), hp.htypes)
        self.assertEqual(head.columns.unique(level=0).to_list(), hp.shares)
        self.assertTrue(np.allclose(head['000100'].values, hp.values[0, 0:3]))
        self.assertTrue(np.allclose(head['000101'].values, hp.values[1, 0:3]))
        self.assertTrue(np.allclose(head['000102'].values, hp.values[2, 0:3]))
        self.assertTrue(np.allclose(head['000103'].values, hp.values[3, 0:3]))
        self.assertTrue(np.allclose(head['000104'].values, hp.values[4, 0:3]))

        tail = hp.flattened_tail(3)
        print(f'test flattened_tail()\nhp is \n{hp}\n flattened_tail(3):\n{tail}')
        self.assertIsInstance(tail, pd.DataFrame)
        self.assertEqual(tail.shape, (3, hp.shape[0] * hp.shape[2]))
        self.assertEqual(list(tail.index), list(hp.hdates[-3:]))
        self.assertEqual(tail.columns.unique(level=1).to_list(), hp.htypes)
        self.assertEqual(tail.columns.unique(level=0).to_list(), hp.shares)
        self.assertTrue(np.allclose(tail['000100'].values, hp.values[0, -3:]))
        self.assertTrue(np.allclose(tail['000101'].values, hp.values[1, -3:]))
        self.assertTrue(np.allclose(tail['000102'].values, hp.values[2, -3:]))
        self.assertTrue(np.allclose(tail['000103'].values, hp.values[3, -3:]))
        self.assertTrue(np.allclose(tail['000104'].values, hp.values[4, -3:]))

        print('test error raises')
        self.assertRaises(TypeError, hp.head, '3')
        self.assertRaises(ValueError, hp.head, -1)
        self.assertRaises(TypeError, hp.tail, '3')
        self.assertRaises(ValueError, hp.tail, -1)
        self.assertRaises(TypeError, hp.flattened_head, '3')
        self.assertRaises(ValueError, hp.flattened_head, -1)
        self.assertRaises(TypeError, hp.flattened_tail, '3')
        self.assertRaises(ValueError, hp.flattened_tail, -1)


if __name__ == '__main__':
    unittest.main()