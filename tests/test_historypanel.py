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

import os
import shutil
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np

from qteasy.database import DataSource
from qteasy.utilfuncs import str_to_list
from qteasy.datatypes import (
    infer_data_types,
    DataType,
)
from qteasy.history import (
    HistoryPanel,
    stack_dataframes,
    ffill_3d_data,
    get_history_data_packages
)


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
        self.ds = qt.QT_DATA_SOURCE

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
        row_dict = {Timestamp('2020-01-01 00:00:00'): 0,
                    Timestamp('2020-01-02 00:00:00'): 1,
                    Timestamp('2020-01-03 00:00:00'): 2,
                    Timestamp('2020-01-04 00:00:00'): 3,
                    Timestamp('2020-01-05 00:00:00'): 4,
                    Timestamp('2020-01-06 00:00:00'): 5,
                    Timestamp('2020-01-07 00:00:00'): 6,
                    Timestamp('2020-01-08 00:00:00'): 7,
                    Timestamp('2020-01-09 00:00:00'): 8,
                    Timestamp('2020-01-10 00:00:00'): 9}
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
        print('test get history panel data')
        data_types = infer_data_types(
                names='wt_idx|000003.SH, close, wt_idx|000300.SH',
                freqs='m',
                asset_types='any',
                adj='none',
                allow_ignore_freq=True,
        )
        hp = qt.history.get_history_panel(data_source=self.ds, data_types=data_types,
                                          shares='000001.SZ, 000002.SZ, 900901.SH, 601728.SH',
                                          start='20210101', end='20210802', freq='m')
        expected_htypes = ['wt_idx|000003.SH', 'close', 'close', 'wt_idx|000300.SH']
        expected_shares = ['000001.SZ', '000002.SZ', '900901.SH', '601728.SH']
        print(f'HistoryPanel obtained is:\n{hp}')
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))

        print('test get history panel data without shares')
        data_types = infer_data_types(
                names='close-000002.SZ, pe-000001.SZ, open-000300.SH',
                freqs='d',
                asset_types='any',
        )
        hp = qt.history.get_history_panel(data_source=self.ds, data_types=data_types, shares=None,
                                          start='20210101', end='20210202', freq='d',
                                          drop_nan=True)
        expected_htypes = ['close-000002.SZ', 'pe-000001.SZ', 'open-000300.SH']
        expected_shares = ['none']
        print(f'HistoryPanel obtained is:\n{hp}')
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))

        print('test get history panel data from converting multiple frequencies')
        data_types = infer_data_types(
                names='wt_idx|000003.SH, close, pe, eps, revenue_ps',
                freqs='w',
                asset_types='any',
                allow_ignore_freq=True,
        )
        hp = qt.history.get_history_panel(data_types=data_types, data_source=self.ds,
                                          shares='000001.SZ, 000002.SZ, 900901.SH, 601728.SH', start='20210101',
                                          end='20210502', freq='w', drop_nan=True)
        expected_htypes = ['wt_idx|000003.SH', 'close', 'pe', 'eps', 'revenue_ps']
        expected_shares = ['000001.SZ', '000002.SZ', '900901.SH', '601728.SH']
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))
        print(hp)

        print('test get history panel data with / without all NaN values')
        data_types = infer_data_types(
                names='open, high, low|f, close|b',
                freqs='d',
                asset_types='any',
        )
        hp = qt.history.get_history_panel(data_types=data_types, data_source=self.ds,
                                          shares='000002.SZ, 000001.SZ, 000300.SH',
                                          start='20210101', end='20210115', freq='d',
                                          drop_nan=False, resample_method='none', b_days_only=False)
        print(hp)
        expected_htypes = ['open', 'high', 'low|f', 'close|b']
        expected_shares = ['000002.SZ', '000001.SZ', '000300.SH']
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))
        first_3_rows = hp[:, :, 0:3]
        row_9_til_10 = hp[:, :, 8:10]
        self.assertTrue(np.all(np.isnan(first_3_rows)))
        self.assertTrue(np.all(np.isnan(row_9_til_10)))

        print('test getting history panel with row_counts and only end')

        data_types = infer_data_types(
                names='open, high, close|b, pe',
                freqs='h',
                asset_types='E',
                allow_ignore_freq=True,
        )
        hp = qt.history.get_history_panel(data_types=data_types, data_source=self.ds,
                                          shares='000002.SZ, 000001.SZ, 000300.SH',
                                          end='20210115', freq='h',
                                          rows=20, )
        print(hp)
        expected_htypes = ['open', 'high', 'close|b', 'pe']
        expected_shares = ['000002.SZ', '000001.SZ', '000300.SH']
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))
        all_idx_data = hp[:, '000300.SH']
        self.assertTrue(np.all(np.isnan(all_idx_data)))
        self.assertEqual(len(hp), 20)

        print('test getting history panel with row_counts and only start')

        data_types = infer_data_types(
                names='open, high, close|b, pe',
                freqs='h',
                asset_types='E',
                allow_ignore_freq=True,
        )
        hp = qt.history.get_history_panel(data_types=data_types, data_source=self.ds,
                                          shares='000002.SZ, 000001.SZ, 000300.SH',
                                          start='20210114', freq='h',
                                          rows=20, )
        print(hp)
        expected_htypes = ['open', 'high', 'close|b', 'pe']
        expected_shares = ['000002.SZ', '000001.SZ', '000300.SH']
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))
        # here check that all idx data are nan and row count is correct (20)
        all_idx_data = hp[:, '000300.SH']
        self.assertTrue(np.all(np.isnan(all_idx_data)))
        self.assertLessEqual(len(hp), 20)

        print('test get history panel data')
        data_types = infer_data_types(
                names='wt_idx|000003.SH, close, wt_idx|000300.SH',
                freqs='m',
                asset_types='any',
                adj='none',
                allow_ignore_freq=True,
        )
        hp = qt.history.get_history_panel(data_source=self.ds, data_types=data_types,
                                          shares='000001.SZ, 000002.SZ, 900901.SH, 601728.SH',
                                          start='20210101', end='20210802', freq='m')
        expected_htypes = ['wt_idx|000003.SH', 'close', 'wt_idx|000300.SH']
        expected_shares = ['000001.SZ', '000002.SZ', '900901.SH', '601728.SH']
        self.assertTrue(all(i in expected_htypes for i in hp.htypes))
        self.assertTrue(all(i in hp.htypes for i in expected_htypes))
        self.assertTrue(all(i in expected_shares for i in hp.shares))
        self.assertTrue(all(i in hp.shares for i in expected_shares))
        print(hp)

        print('test getting history panel with wrong parameters')
        print('datetime not recognized')
        data_types = infer_data_types(
                names='open, high, low, close',
                freqs='d',
                asset_types='E',
                adj='f',
        )
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          data_types=data_types,
                          data_source=self.ds,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          start='not_a_time',
                          end='20210115',
                          freq='d',)
        print('freq not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          data_types=data_types,
                          data_source=self.ds,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          start='20210101',
                          end='20210115',
                          freq='wrong_freq',)
        print('data_types not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          data_types=['wrong data types'],
                          data_source=self.ds,
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          htypes='open, high, low, close',
                          start='202101001',
                          end='20210115',
                          freq='d',)
        print('data_source not recognized')
        self.assertRaises(Exception,
                          qt.history.get_history_panel,
                          data_types=data_types,
                          data_source='not a data source',
                          shares='000002.SZ, 000001.SZ, 000300.SH',
                          start='202101001',
                          end='20210115',
                          freq='d',)

        print(f'test getting data with different freq but same asset type and name, ValueError expected')
        data_types = [qt.DataType('close', freq='d', asset_type='E'),
                      qt.DataType('close', freq='w', asset_type='E'),
                      qt.DataType('close', freq='m', asset_type='E')]
        # 这里原来的期望值是不允许相同name相同AT但不同freq的data type共存，因为这样会导致无法确定应该用哪个
        # data type来获取数据，但是后来在升级到2.1.4版本时为了解决freq与AT冲突的问题，修改了不同地方的代码逻辑，
        # 使得出现这种情况时仍然会强制汇总获取的不同数据到同一列，因此这里的期望值也修改为不报错，但是还需要进一步
        # 观察这种修改是否会引入其他问题
        # with self.assertRaises(ValueError):
        #     hp = qt.history.get_history_panel(data_source=self.ds, data_types=data_types,
        #                                       shares='000001.SZ, 000002.SZ, 900901.SH, 601728.SH',
        #                                       start='20210101', end='20210202', freq='m')

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


class TestGetHistoryDataPackages(unittest.TestCase):

    def setUp(self):
        """设置测试环境，创建测试数据源和测试数据"""
        # 创建临时目录用于测试数据源
        self.test_data_path = "./temp_test_data"
        os.makedirs(self.test_data_path, exist_ok=True)

        # 创建测试数据源
        self.data_source = DataSource(
                source_type='file',
                file_loc=self.test_data_path,
        )
        # 创建测试数据close_E_d
        self.dates = pd.date_range('2023-01-01', '2023-01-20', freq='D')
        self.shares = ['000001.SZ', '000002.SZ']
        self.shares_and_index = ['000001.SZ', '000002.SZ', '000001.SH']

        # 为每只股票创建测试数据文件
        for share in self.shares:
            data = pd.DataFrame({
                'trade_date':   self.dates,
                'ts_code':      [share] * 20,
                'open':   np.random.rand(20) * 100,
                'high':   np.random.rand(20) * 100,
                'low':    np.random.rand(20) * 100,
                'close':  np.random.rand(20) * 100,
                'vol': np.random.randint(1000, 10000, 20)
            })
            print(f'updating data for share {share}:\n{data}')
            self.data_source.update_table_data('stock_daily', df=data, merge_type='update')

        # 创建指数（参考）数据文件（如指数数据）
        index_data = pd.DataFrame({
            'trade_date':   self.dates,
            'ts_code':      ['000001.SH'] * 20,
            'open':   np.random.rand(20) * 5000,
            'high':   np.random.rand(20) * 5000,
            'low':    np.random.rand(20) * 5000,
            'close':  np.random.rand(20) * 5000,
            'vol': np.random.randint(100000, 1000000, 20)
        })
        print(f'updating index data:\n{index_data}')
        self.data_source.update_table_data('index_daily', df=index_data, merge_type='update')

        # 检查确认数据已经存入datasource
        self.data_source.get_table_info('stock_daily')

        # 创建DataType对象
        self.price_type = DataType('close', freq='d', asset_type='E')
        self.volume_type = DataType('volume', freq='d', asset_type='E')
        self.index_close = DataType('close', freq='d', asset_type='IDX')

    def tearDown(self):
        """清理测试环境"""
        print(f'tearing down test environment')
        # 删除临时目录
        if os.path.exists(self.test_data_path):
            shutil.rmtree(self.test_data_path)
            print(f'deleted test data path: {self.test_data_path}')

    def test_get_single_data_type_with_shares(self):
        """测试获取单个数据类型和指定股票的数据"""
        result = get_history_data_packages(
                data_types=self.price_type,
                data_source=self.data_source,
                shares=self.shares_and_index,
                start='2023-01-01',
                end='2023-01-10'
        )
        print(f'get data result is:\n{result}')

        # 验证返回值类型
        self.assertIsInstance(result, dict)
        self.assertIn('close_E_d', result)
        self.assertIsInstance(result['close_E_d'], pd.DataFrame)

        # 验证DataFrame内容
        df = result['close_E_d']
        self.assertEqual(len(df), 10)  # 10个交易日
        self.assertEqual(len(df.columns), 3)  # 2只股票
        self.assertTrue(all(share in df.columns for share in self.shares))

        # 从datasource读取数据
        table_data = self.data_source.read_table_data('stock_daily', shares=self.shares,
                                                      start='2023-01-01', end='2023-01-10')
        print(f'table_data from data source:\n{table_data}')
        self.assertTrue(np.allclose(df['000001.SZ'].values, table_data[table_data.index.get_level_values('ts_code') == '000001.SZ']['close'].values))
        self.assertTrue(np.allclose(df['000002.SZ'].values, table_data[table_data.index.get_level_values('ts_code') == '000002.SZ']['close'].values))

        self.assertTrue(all(np.isnan(df['000001.SH'].values)))

    def test_get_multiple_data_types_with_shares(self):
        """测试获取多个数据类型和指定股票的数据"""
        result = get_history_data_packages(
                data_types=[self.price_type, self.volume_type, self.index_close],
                data_source=self.data_source,
                shares=self.shares_and_index,
                start='2023-01-01',
                end='2023-01-10'
        )
        print(f'get data result is:\n{result}')

        # 验证返回值
        self.assertIsInstance(result, dict)
        self.assertIn('close_E_d', result)
        self.assertIn('volume_E_d', result)
        self.assertIn('close_IDX_d', result)
        self.assertIsInstance(result['close_E_d'], pd.DataFrame)
        self.assertIsInstance(result['volume_E_d'], pd.DataFrame)
        self.assertIsInstance(result['close_IDX_d'], pd.DataFrame)

        # 验证DataFrame内容
        price_df = result['close_E_d']
        volume_df = result['volume_E_d']
        index_df = result['close_IDX_d']
        self.assertEqual(len(price_df), 10)
        self.assertEqual(len(volume_df), 10)
        self.assertEqual(len(index_df), 10)
        self.assertEqual(len(price_df.columns), 3)
        self.assertEqual(len(volume_df.columns), 3)
        self.assertEqual(len(index_df.columns), 3)

        # 验证DataFrame'close_E_d'内容
        df = result['close_E_d']

        # 从datasource读取数据
        table_data = self.data_source.read_table_data('stock_daily', shares=self.shares,
                                                      start='2023-01-01', end='2023-01-10')
        print(f'table_data from data source:\n{table_data}')
        self.assertTrue(np.allclose(df['000001.SZ'].values, table_data[table_data.index.get_level_values('ts_code') == '000001.SZ']['close'].values))
        self.assertTrue(np.allclose(df['000002.SZ'].values, table_data[table_data.index.get_level_values('ts_code') == '000002.SZ']['close'].values))

        # 验证DataFrame'close_IDX_d'内容
        df = result['close_IDX_d']

        # 从datasource读取数据
        table_data = self.data_source.read_table_data('index_daily', shares='000001.SH',
                                                      start='2023-01-01', end='2023-01-10')
        print(f'table_data from data source:\n{table_data}')
        self.assertTrue(np.allclose(df['000001.SH'].values, table_data[table_data.index.get_level_values('ts_code') == '000001.SH']['close'].values))

    def test_get_data_with_date_range(self):
        """测试使用日期范围获取数据"""
        result = get_history_data_packages(
                data_types=self.price_type,
                data_source=self.data_source,
                shares=self.shares,
                start='2023-01-03',
                end='2023-01-07'
        )
        print(f'get data result is:\n{result}')

        df = result['close_E_d']
        self.assertEqual(len(df), 5)  # 5个交易日
        self.assertTrue(pd.Timestamp('2023-01-03 15:00:00') in df.index)
        self.assertTrue(pd.Timestamp('2023-01-07 15:00:00') in df.index)

    def test_get_data_with_row_count(self):
        """测试使用行数限制获取数据"""
        print(f'testing get data with start and row count')
        result = get_history_data_packages(
                data_types=self.price_type,
                data_source=self.data_source,
                shares=self.shares,
                start='2023-01-05',
                rows=5,
        )
        print(f'get data result is:\n{result}')

        df = result['close_E_d']
        self.assertEqual(len(df), 5)  # 最近5个交易日
        self.assertEqual(df.index[0], pd.Timestamp('2023-01-05 15:00:00'))

        print(f'testing get data with end and row count')
        result = get_history_data_packages(
                data_types=self.price_type,
                data_source=self.data_source,
                shares=self.shares,
                end='2023-01-07',
                rows=5,
        )
        print(f'get data result is:\n{result}')

        df = result['close_E_d']
        self.assertEqual(len(df), 5)  # 最近5个交易日
        self.assertEqual(df.index[-1], pd.Timestamp('2023-01-07 15:00:00'))

    def test_get_reference_data_without_shares(self):
        """测试获取无股票代码的参考数据"""

        # 创建参考数据类型
        index_type = DataType('close-000001.SH', freq='d', asset_type='IDX')
        print(f'Created data type that is unsymbolized: {index_type.unsymbolized}')

        result = get_history_data_packages(
                data_types=index_type,
                data_source=self.data_source,
                shares=None,
                start='2023-01-03',
                end='2023-01-09'
        )
        print(f'get data result is:\n{result}')

        self.assertIsInstance(result, dict)
        self.assertIn('close-000001.SH_IDX_d', result)
        self.assertIsInstance(result['close-000001.SH_IDX_d'], pd.Series)
        result_df = result['close-000001.SH_IDX_d']
        self.assertEqual(result_df.shape, (7, ))  # 7个交易日，1列数据
        self.assertEqual(result_df.name, 'close-000001.SH_IDX_d')  # 列名为'none'
        self.assertEqual(result_df.index[0], pd.Timestamp('2023-01-03 15:00:00'))
        self.assertEqual(result_df.index[-1], pd.Timestamp('2023-01-09 15:00:00'))

    def test_invalid_data_types(self):
        """测试无效的数据类型参数"""
        with self.assertRaises(TypeError):
            get_history_data_packages(
                    data_types="invalid_type",
                    data_source=self.data_source,
                    shares=self.shares,
                    start='2023-01-01',
                    end='2023-01-10'
            )

        with self.assertRaises(TypeError):
            get_history_data_packages(
                    data_types=["invalid_type"],
                    data_source=self.data_source,
                    shares=self.shares,
                    start='2023-01-01',
                    end='2023-01-10'
            )

    def test_empty_result(self):
        """测试无数据返回的情况"""

        print(f'testing get data with date range that has no data')

        # 当下载的数据为空时，raise RuntimeError:
        with self.assertRaises(RuntimeError):
            # 使用不存在的日期范围
            get_history_data_packages(
                    data_types=self.price_type,
                    data_source=self.data_source,
                    shares=self.shares,
                    start='2024-01-01',
                    end='2024-01-10'
            )


class TestHistoryPanelStats(unittest.TestCase):
    """ 测试 HistoryPanel 的基础统计方法 describe/mean/std/min/max。"""

    def setUp(self):
        print('\n[TestHistoryPanelStats] setUp basic HistoryPanel for stats')
        # 构造一个小而可手工验证的 HistoryPanel
        # shares: s1, s2; dates: 3; htypes: close, open
        values = np.array(
                [
                    [[1.0, 4.0],
                     [2.0, 5.0],
                     [3.0, 6.0]],
                    [[2.0, 1.0],
                     [4.0, 3.0],
                     [6.0, 5.0]],
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03']
        htypes = ['close', 'open']
        self.hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

    def test_mean_by_share_and_htype(self):
        """ mean(by='share'/'htype') 应按约定轴向聚合，并返回 DataFrame。"""
        print('\n[TestHistoryPanelStats] mean by share and by htype')
        hp = self.hp

        # by='share'：对每只股票在时间轴上求均值，结果形状 (shares, htypes)
        mean_by_share = hp.mean(by='share')
        print('  mean_by_share:\n', mean_by_share)
        self.assertIsInstance(mean_by_share, pd.DataFrame)
        self.assertEqual(list(mean_by_share.index), hp.shares)
        self.assertEqual(list(mean_by_share.columns), hp.htypes)
        # 手工计算期望值
        expected_s1_close = np.mean([1.0, 2.0, 3.0])
        expected_s1_open = np.mean([4.0, 5.0, 6.0])
        expected_s2_close = np.mean([2.0, 4.0, 6.0])
        expected_s2_open = np.mean([1.0, 3.0, 5.0])
        self.assertAlmostEqual(mean_by_share.loc['s1', 'close'], expected_s1_close)
        self.assertAlmostEqual(mean_by_share.loc['s1', 'open'], expected_s1_open)
        self.assertAlmostEqual(mean_by_share.loc['s2', 'close'], expected_s2_close)
        self.assertAlmostEqual(mean_by_share.loc['s2', 'open'], expected_s2_open)

        # by='htype'：对每个 htype 在股票轴上求均值，结果形状 (htypes, shares)
        mean_by_htype = hp.mean(by='htype')
        print('  mean_by_htype:\n', mean_by_htype)
        self.assertIsInstance(mean_by_htype, pd.DataFrame)
        self.assertEqual(list(mean_by_htype.index), hp.htypes)
        self.assertEqual(list(mean_by_htype.columns), hp.shares)
        # close: (s1,s2) 在所有时间上的均值再按 share 维度聚合
        expected_close_s1 = expected_s1_close
        expected_close_s2 = expected_s2_close
        self.assertAlmostEqual(mean_by_htype.loc['close', 's1'], expected_close_s1)
        self.assertAlmostEqual(mean_by_htype.loc['close', 's2'], expected_close_s2)

        # 非法 by 值应抛出 ValueError
        with self.assertRaises(ValueError):
            hp.mean(by='wrong_axis')

    def test_std_min_max_by_share(self):
        """ std/min/max(by='share') 返回形状正确，且数值与 numpy 结果一致。"""
        print('\n[TestHistoryPanelStats] std/min/max by share')
        hp = self.hp

        std_by_share = hp.std(by='share')
        min_by_share = hp.min(by='share')
        max_by_share = hp.max(by='share')
        print('  std_by_share:\n', std_by_share)
        print('  min_by_share:\n', min_by_share)
        print('  max_by_share:\n', max_by_share)

        # 形状检查
        for df in [std_by_share, min_by_share, max_by_share]:
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(list(df.index), hp.shares)
            self.assertEqual(list(df.columns), hp.htypes)

        # 数值检查（使用 numpy 手算）
        data = hp.values
        # share s1, close 系列: [1,2,3]
        s1_close = data[0, :, 0]
        s1_open = data[0, :, 1]
        s2_close = data[1, :, 0]
        s2_open = data[1, :, 1]
        self.assertAlmostEqual(std_by_share.loc['s1', 'close'], np.std(s1_close, ddof=1))
        self.assertAlmostEqual(std_by_share.loc['s1', 'open'], np.std(s1_open, ddof=1))
        self.assertAlmostEqual(std_by_share.loc['s2', 'close'], np.std(s2_close, ddof=1))
        self.assertAlmostEqual(std_by_share.loc['s2', 'open'], np.std(s2_open, ddof=1))
        self.assertEqual(min_by_share.loc['s1', 'close'], np.min(s1_close))
        self.assertEqual(max_by_share.loc['s2', 'open'], np.max(s2_open))

    def test_describe_by_share_and_global(self):
        """ describe(by='share'/None) 应返回约定结构，并与 pandas.describe 保持一致。"""
        print('\n[TestHistoryPanelStats] describe by share and global')
        hp = self.hp

        desc_by_share = hp.describe(by='share')
        print('  desc_by_share:\n', desc_by_share)
        self.assertIsInstance(desc_by_share, pd.DataFrame)
        # index 为 shares，columns 为 MultiIndex[htype, stat]
        self.assertEqual(list(desc_by_share.index), hp.shares)
        self.assertTrue(isinstance(desc_by_share.columns, pd.MultiIndex))
        self.assertEqual(sorted(set(l[0] for l in desc_by_share.columns)), sorted(hp.htypes))

        # 用单只股票 + pandas.DataFrame.describe 比较一个 htype 的统计量
        df_s1 = hp.slice_to_dataframe(share='s1')
        pandas_desc = df_s1['close'].describe()
        for stat in ['mean', 'std', 'min', 'max']:
            self.assertAlmostEqual(
                    desc_by_share.loc['s1', ('close', stat)],
                    pandas_desc[stat],
            )

        # 全局 describe(by=None) 只返回一行，全局样本池描述
        desc_global = hp.describe(by=None)
        print('  desc_global:\n', desc_global)
        self.assertIsInstance(desc_global, pd.DataFrame)
        self.assertEqual(desc_global.shape[0], 1)
        for stat in ['mean', 'std', 'min', 'max']:
            self.assertIn(stat, desc_global.columns)


class TestHistoryPanelToShareFrame(unittest.TestCase):
    """ 测试 HistoryPanel.to_share_frame 语法糖行为。"""

    def test_to_share_frame_basic(self):
        """ 单股票全指标切片，index 为 hdates，columns 为全部 htypes。"""
        print('\n[TestHistoryPanelToShareFrame] basic to_share_frame')
        values = np.array(
                [
                    [[1.0, 2.0, 3.0],
                     [4.0, 5.0, 6.0]],
                    [[7.0, 8.0, 9.0],
                     [10.0, 11.0, 12.0]],
                ]
        )
        shares = ['000001.SZ', '000002.SZ']
        hdates = ['2023-01-03', '2023-01-04']
        htypes = ['open', 'high', 'low']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)
        df = hp.to_share_frame('000001.SZ')
        print('  df shape:', df.shape, 'index:', df.index.tolist(), 'columns:', df.columns.tolist())
        expected = hp.slice_to_dataframe(share='000001.SZ')
        pd.testing.assert_frame_equal(df, expected)
        self.assertEqual(list(df.index), list(hp.hdates))
        self.assertEqual(list(df.columns), htypes)

    def test_to_share_frame_invalid_share_raises(self):
        """ 非法 share 时应抛出 KeyError。"""
        print('\n[TestHistoryPanelToShareFrame] invalid share raises')
        values = np.ones((1, 2, 2))
        shares = ['000001.SZ']
        hdates = ['2023-01-03', '2023-01-04']
        htypes = ['open', 'close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)
        with self.assertRaises(KeyError):
            hp.to_share_frame('000002.SZ')


class TestHistoryPanelRolling(unittest.TestCase):
    """ 测试 HistoryPanel.rolling 与 HistoryPanelRolling 的基本行为。"""

    def test_rolling_mean_basic(self):
        """ 简单滚动均值：对每个 (share, htype) 序列沿时间滚动。"""
        print('\n[TestHistoryPanelRolling] basic rolling mean')
        values = np.array(
                [
                    [[1.0, 10.0],
                     [3.0, 14.0],
                     [5.0, 18.0],
                     [7.0, 22.0]],
                    [[2.0, 20.0],
                     [4.0, 24.0],
                     [6.0, 28.0],
                     [8.0, 32.0]],
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
        htypes = ['close', 'open']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        rolling_hp = hp.rolling(window=2).mean()
        print('  rolling mean values:\n', rolling_hp.values)

        # 形状与标签不变
        self.assertEqual(rolling_hp.shape, hp.shape)
        self.assertEqual(rolling_hp.shares, shares)
        self.assertEqual(rolling_hp.htypes, htypes)
        self.assertEqual(rolling_hp.hdates, list(pd.to_datetime(hdates)))

        # 对单个序列使用 pandas 计算期望结果进行对比
        s1_close = pd.Series([1.0, 3.0, 5.0, 7.0], index=pd.to_datetime(hdates))
        expected = s1_close.rolling(window=2, min_periods=2).mean().values
        # s1, close 对应 level=0, htype=0
        self.assertTrue(np.allclose(rolling_hp.values[0, :, 0], expected, equal_nan=True))

        # 非法 window / by 参数抛出 ValueError
        with self.assertRaises(ValueError):
            hp.rolling(window=0)
        with self.assertRaises(ValueError):
            hp.rolling(window=2, by='wrong')


class TestHistoryPanelReturnsAndRisk(unittest.TestCase):
    """ 测试 HistoryPanel.returns 与 volatility。"""

    def test_returns_simple_dataframe(self):
        """ returns(method='simple') 返回 DataFrame，index=时间、columns=shares。"""
        print('\n[TestHistoryPanelReturnsAndRisk] returns simple as DataFrame')
        # 价格 [1, 2, 4] -> 简单收益率 [nan, 1.0, 1.0]
        values = np.array(
                [
                    [[1.0], [2.0], [4.0]],   # s1 close
                    [[2.0], [4.0], [8.0]],   # s2 close
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        ret_df = hp.returns(price_htype='close', method='simple', as_panel=False)
        print('  ret_df:\n', ret_df)

        self.assertIsInstance(ret_df, pd.DataFrame)
        self.assertEqual(list(ret_df.index), list(pd.to_datetime(hdates)))
        self.assertEqual(list(ret_df.columns), shares)
        # 第一行无前值，应为 NaN
        self.assertTrue(np.isnan(ret_df.loc[ret_df.index[0], 's1']))
        self.assertTrue(np.isnan(ret_df.loc[ret_df.index[0], 's2']))
        # s1: (2-1)/1=1, (4-2)/2=1
        self.assertAlmostEqual(ret_df.loc[ret_df.index[1], 's1'], 1.0)
        self.assertAlmostEqual(ret_df.loc[ret_df.index[2], 's1'], 1.0)
        self.assertAlmostEqual(ret_df.loc[ret_df.index[1], 's2'], 1.0)
        self.assertAlmostEqual(ret_df.loc[ret_df.index[2], 's2'], 1.0)

    def test_returns_log_and_as_panel(self):
        """ returns(method='log', as_panel=True) 返回 HistoryPanel，htype 为 ret_close。"""
        print('\n[TestHistoryPanelReturnsAndRisk] returns log as_panel')
        values = np.array(
                [
                    [[np.e], [np.e ** 2]],   # s1 close: 1期后 e^2/e = e, log(e)=1
                    [[1.0], [2.0]],          # s2 close
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        ret_hp = hp.returns(price_htype='close', method='log', as_panel=True)
        print('  ret_hp.htypes:', ret_hp.htypes, 'shape:', ret_hp.shape)

        self.assertIsInstance(ret_hp, HistoryPanel)
        self.assertEqual(ret_hp.shares, shares)
        self.assertEqual(ret_hp.hdates, list(pd.to_datetime(hdates)))
        self.assertEqual(ret_hp.htypes, ['ret_close'])
        self.assertEqual(ret_hp.shape, (2, 2, 1))
        # 首期无前值 NaN
        self.assertTrue(np.isnan(ret_hp.values[0, 0, 0]))
        self.assertTrue(np.isnan(ret_hp.values[1, 0, 0]))
        # s1 log(e^2/e)=1
        self.assertAlmostEqual(ret_hp.values[0, 1, 0], 1.0)
        # s2 log(2/1)=ln2
        self.assertAlmostEqual(ret_hp.values[1, 1, 0], np.log(2.0))

    def test_volatility_basic(self):
        """ volatility 基于 returns 的滚动标准差，annualize 可关。"""
        print('\n[TestHistoryPanelReturnsAndRisk] volatility basic')
        # 5 个时间点，便于 window=3 滚动
        values = np.array(
                [
                    [[1.0], [2.0], [3.0], [4.0], [5.0]],  # s1 close
                    [[10.0], [11.0], [12.0], [13.0], [14.0]],  # s2 close
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        vol_df = hp.volatility(window=3, price_htype='close', annualize=False, as_panel=False)
        print('  vol_df:\n', vol_df)

        self.assertIsInstance(vol_df, pd.DataFrame)
        self.assertEqual(list(vol_df.columns), shares)
        # 第一行 NaN，第二行起开始有滚动标准差（考虑 returns 首行 NaN 的影响）
        self.assertTrue(np.isnan(vol_df.iloc[0]['s1']))
        self.assertTrue(np.isnan(vol_df.iloc[1]['s1']))
        # 第 3 行开始（索引 2）有首个有效波动率
        ret_s1 = hp.returns(price_htype='close', method='simple', as_panel=False)['s1']
        expected_std_2 = ret_s1.iloc[0:3].std()
        self.assertAlmostEqual(vol_df.iloc[2]['s1'], expected_std_2)

    def test_alpha_beta_basic(self):
        """ alpha_beta 基本回归：构造严格线性关系，beta≈2，alpha≈0。"""
        print('\n[TestHistoryPanelReturnsAndRisk] alpha_beta basic')
        # 人为构造收益率: r_b=[0.1,0.2,0.3,0.4], r_s=2*r_b
        r_b = np.array([0.1, 0.2, 0.3, 0.4])
        r_s = 2 * r_b
        # 将收益率积分为价格序列 p_t = p_{t-1} * (1 + r_t)
        bench_prices = [1.0]
        stock_prices = [1.0]
        for rb, rs in zip(r_b, r_s):
            bench_prices.append(bench_prices[-1] * (1.0 + rb))
            stock_prices.append(stock_prices[-1] * (1.0 + rs))
        bench_dates = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])
        bench_price = pd.Series(bench_prices, index=bench_dates)

        values = np.array(
                [
                    [[stock_prices[0]], [stock_prices[1]], [stock_prices[2]], [stock_prices[3]], [stock_prices[4]]],
                ]
        )
        shares = ['s1']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        res = hp.alpha_beta(benchmark=bench_price, price_htype='close', method='simple', freq=None, annualize=False)
        print('  alpha_beta result:\n', res)

        self.assertIsInstance(res, pd.DataFrame)
        self.assertEqual(list(res.index), shares)
        # 有效观测点为 4（首期 NaN 不参与）
        self.assertEqual(res.loc['s1', 'n_obs'], 4)
        # beta≈2, alpha≈0, R^2≈1
        self.assertAlmostEqual(res.loc['s1', 'beta'], 2.0, places=6)
        self.assertAlmostEqual(res.loc['s1', 'alpha'], 0.0, places=6)
        self.assertAlmostEqual(res.loc['s1', 'r2'], 1.0, places=6)


class TestHistoryPanelKlineIndicators(unittest.TestCase):
    """ 测试 HistoryPanel.kline 访问器：sma、ema。"""

    def test_kline_sma(self):
        """ kline.sma 在 Panel 后追加 sma_{window} 列。"""
        print('\n[TestHistoryPanelKlineIndicators] kline.sma')
        values = np.array(
                [
                    [[1.0, 2.0, 3.0, 4.0, 5.0]],
                    [[10.0, 11.0, 12.0, 13.0, 14.0]],
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        out = hp.kline.sma(window=2, price_htype='close')
        print('  out.htypes:', out.htypes, 'shape:', out.shape)

        self.assertEqual(out.htypes, ['close', 'sma_2'])
        self.assertEqual(out.shares, shares)
        self.assertEqual(out.shape, (2, 5, 2))
        # s1 close 前2个: [1,2,3,4,5], sma(2) 第2个起 (1+2)/2=1.5, (2+3)/2=2.5, ...
        self.assertTrue(np.isnan(out.values[0, 0, 1]))
        self.assertAlmostEqual(out.values[0, 1, 1], 1.5)
        self.assertAlmostEqual(out.values[0, 2, 1], 2.5)

    def test_kline_ema(self):
        """ kline.ema 在 Panel 后追加 ema_{span} 列。"""
        print('\n[TestHistoryPanelKlineIndicators] kline.ema')
        values = np.array(
                [
                    [[1.0, 2.0, 3.0, 4.0, 5.0]],
                ]
        )
        shares = ['s1']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        out = hp.kline.ema(span=2, price_htype='close')
        print('  out.htypes:', out.htypes)

        self.assertEqual(out.htypes, ['close', 'ema_2'])
        self.assertEqual(out.shape, (1, 5, 2))
        # 首点 EMA 常为 NaN 或等于价格，后续为指数均
        self.assertFalse(np.all(np.isnan(out.values[0, :, 1])))


if __name__ == '__main__':
    unittest.main()
