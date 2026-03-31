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
        self.assertTrue(np.allclose(self.hp['close'].values, self.data[:, :, 0:1]))
        self.assertTrue(np.allclose(self.hp['close,open'].values, self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp[['close', 'open']].values, self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp['close:high'].values, self.data[:, :, 0:3]))
        self.assertTrue(np.allclose(self.hp['close,high'].values, self.data[:, :, [0, 2]]))
        self.assertTrue(np.allclose(self.hp[:, '000100'].values, self.data[0:1, :, ]))
        self.assertTrue(np.allclose(self.hp[:, '000100,000101'].values, self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:, ['000100', '000101']].values, self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:, '000100:000102'].values, self.data[0:3, :]))
        self.assertTrue(np.allclose(self.hp[:, '000100,000102'].values, self.data[[0, 2], :]))
        self.assertTrue(np.allclose(self.hp['close,open', '000100,000102'].values, self.data[[0, 2], :, 0:2]))
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
        self.assertTrue(np.allclose(hp['close', :, :].values, data[:, :, 0:1], equal_nan=True))
        print(f'==========================\n输出close和open类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1], :, :].values, data[:, :, 0:2], equal_nan=True))
        print(f'==========================\n输出第一只股票的所有类型历史数据\n')
        self.assertTrue(np.allclose(hp[:, [0], :].values, data[0:1, :, :], equal_nan=True))
        print('==========================\n输出第0、1、2个htype对应的所有股票全部历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1, 2]].values, data[:, :, 0:3], equal_nan=True))
        print('==========================\n输出close、high两个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[['close', 'high']].values, data[:, :, [0, 2]], equal_nan=True))
        print('==========================\n输出0、1两个htype的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1]].values, data[:, :, 0:2], equal_nan=True))
        print('==========================\n输出close、high两个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close,high'].values, data[:, :, [0, 2]], equal_nan=True))
        print('==========================\n输出close起到high止的三个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close:high'].values, data[:, :, 0:3], equal_nan=True))
        print('==========================\n输出0、1、3三个股票的全部历史数据\n')
        self.assertTrue(np.allclose(hp[:, [0, 1, 3]].values, data[[0, 1, 3], :, :], equal_nan=True))
        print('==========================\n输出000100、000102两只股票的所有历史数据\n')
        self.assertTrue(np.allclose(hp[:, ['000100', '000102']].values, data[[0, 2], :, :], equal_nan=True))
        print('==========================\n输出0、1、2三个股票的历史数据\n', hp[:, 0: 3])
        self.assertTrue(np.allclose(hp[:, 0: 3].values, data[0:3, :, :], equal_nan=True))
        print('==========================\n输出000100、000102两只股票的所有历史数据\n')
        self.assertTrue(np.allclose(hp[:, '000100, 000102'].values, data[[0, 2], :, :], equal_nan=True))
        print('==========================\n输出所有股票的0-7日历史数据\n')
        self.assertTrue(np.allclose(hp[:, :, 0:8].values, data[:, 0:8, :], equal_nan=True))
        print('==========================\n输出000100股票的0-7日历史数据\n')
        self.assertTrue(np.allclose(hp[:, '000100', 0:8].values, data[0, 0:8, :], equal_nan=True))
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
                seg1.values, test_hp[:, :, :].values
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp[:, :, 1:10].values
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp[:, :, 2:6].values
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
                seg1.values, test_hp[:, :, :].values
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp[:, :, 1:10].values
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp[:, :, 1:6].values
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
                seg1.values, test_hp[:, :, :].values
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
        self.assertTrue(np.allclose(slc.values, test_hp[:, '000101'].values))

        share = '000101, 000103'
        slc = test_hp.slice(shares=share)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000101', '000103'])
        self.assertEqual(slc.htypes, test_hp.htypes)
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp[:, '000101, 000103'].values))

        print(f'Test slice with htypes')
        htype = 'open'
        slc = test_hp.slice(htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, test_hp.shares)
        self.assertEqual(slc.htypes, ['open'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['open'].values))

        htype = 'open, close'
        slc = test_hp.slice(htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, test_hp.shares)
        self.assertEqual(slc.htypes, ['open', 'close'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['open, close'].values))
        # test that slicing of "open, close" does NOT equal to "close, open"
        self.assertFalse(np.allclose(slc.values, test_hp['close, open'].values))

        print(f'Test slicing with both htypes and shares')
        share = '000103, 000101'
        htype = 'high, low, close'
        slc = test_hp.slice(shares=share, htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000103', '000101'])
        self.assertEqual(slc.htypes, ['high', 'low', 'close'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['high, low, close', '000103, 000101'].values))

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
        self.assertTrue(np.allclose(self.hp[:, '000102'].values, values))

        print(f'test DataFrame conversion with share == "000100"')
        df_test = self.hp.slice_to_dataframe(share='000100')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.htypes), list(df_test.columns))
        values = df_test.values
        self.assertTrue(np.allclose(self.hp[:, '000100'].values, values))

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
        self.assertTrue(np.allclose(self.hp['close'].values.T, values))

        print(f'test DataFrame conversion with htype == "high"')
        df_test = self.hp.slice_to_dataframe(htype='high')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        # noinspection PyTypeChecker
        self.assertTrue(np.allclose(self.hp['high'].values.T, values))

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
        target_values = test_hp['high'].values.T
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
        target_values = test_hp['high'].values.T
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
        self.assertTrue(np.all(np.isnan(first_3_rows.values)))
        self.assertTrue(np.all(np.isnan(row_9_til_10.values)))

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
        self.assertTrue(np.all(np.isnan(all_idx_data.values)))
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
        self.assertTrue(np.all(np.isnan(all_idx_data.values)))
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
            self.assertTrue(np.allclose(df.loc[share].values, hp[:, share].values.squeeze()))

        print('test flatten_to_dataframe(along="col")')
        df = hp.flatten_to_dataframe(along='col')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (hp.shape[1], hp.shape[0] * hp.shape[2]))
        self.assertEqual(df.index.to_list(), hp.hdates)
        for share in hp.shares:
            self.assertTrue(np.allclose(df[share].values, hp[:, share].values.squeeze()))

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
                    [[1.0], [2.0], [3.0], [4.0], [5.0]],
                    [[10.0], [11.0], [12.0], [13.0], [14.0]],
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
        # s1 close: [1,2,3,4,5]，sma(2): [nan,1.5,2.5,3.5,4.5]
        self.assertTrue(np.isnan(out.values[0, 0, 1]))
        self.assertAlmostEqual(out.values[0, 1, 1], 1.5)
        self.assertAlmostEqual(out.values[0, 2, 1], 2.5)

    def test_kline_ema(self):
        """ kline.ema 在 Panel 后追加 ema_{span} 列。"""
        print('\n[TestHistoryPanelKlineIndicators] kline.ema')
        values = np.array(
                [
                    [[1.0], [2.0], [3.0], [4.0], [5.0]],
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


class TestHistoryPanelPhase6KlineInplace(unittest.TestCase):
    """阶段六：kline 访问器增加 inplace 参数。"""

    def test_kline_sma_inplace_false_does_not_mutate(self):
        """inplace=False 返回新面板，不污染原面板。"""
        print('\n[TestHistoryPanelPhase6KlineInplace] sma inplace=False does not mutate')
        values = np.array(
                [
                    [[1.0], [2.0], [3.0], [4.0], [5.0]],
                    [[10.0], [11.0], [12.0], [13.0], [14.0]],
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        out = hp.kline.sma(window=2, price_htype='close', inplace=False)
        print('  hp.htypes:', hp.htypes)
        print('  out.htypes:', out.htypes, 'shape:', out.shape)

        self.assertIsInstance(out, HistoryPanel)
        self.assertIsNot(out, hp)
        self.assertEqual(hp.htypes, ['close'])
        self.assertEqual(out.htypes, ['close', 'sma_2'])
        self.assertEqual(out.shape, (2, 5, 2))
        # 功能性断言：s1 close: [1,2,3,4,5]，sma(2): [nan,1.5,2.5,3.5,4.5]
        self.assertTrue(np.isnan(out.values[0, 0, 1]))
        self.assertAlmostEqual(out.values[0, 1, 1], 1.5)
        self.assertAlmostEqual(out.values[0, 2, 1], 2.5)

    def test_kline_sma_inplace_true_mutates_and_returns_self(self):
        """inplace=True 原地扩列并返回绑定的 HistoryPanel。"""
        print('\n[TestHistoryPanelPhase6KlineInplace] sma inplace=True mutates and returns self')
        values = np.array(
                [
                    [[1.0], [2.0], [3.0], [4.0], [5.0]],
                ]
        )
        shares = ['s1']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        ret = hp.kline.sma(window=2, price_htype='close', inplace=True)
        print('  ret is hp:', ret is hp)
        print('  hp.htypes:', hp.htypes, 'shape:', hp.shape)

        self.assertIs(ret, hp)
        self.assertEqual(hp.htypes, ['close', 'sma_2'])
        # 关键数值点
        sma_idx = hp.htypes.index('sma_2')
        self.assertTrue(np.isnan(hp.values[0, 0, sma_idx]))
        self.assertAlmostEqual(hp.values[0, 1, sma_idx], 1.5)

    def test_kline_chain_inplace(self):
        """连续 inplace 扩列可链式调用。"""
        print('\n[TestHistoryPanelPhase6KlineInplace] chain inplace')
        values = np.array(
                [
                    [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]],
                ]
        )
        shares = ['s1']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        hp2 = hp.kline.sma(window=2, inplace=True).kline.ema(span=2, inplace=True)
        print('  hp2 is hp:', hp2 is hp)
        print('  hp.htypes:', hp.htypes)

        self.assertIs(hp2, hp)
        self.assertIn('sma_2', hp.htypes)
        self.assertIn('ema_2', hp.htypes)

    def test_kline_inplace_new_htype_conflict_raises(self):
        """new_htype 冲突时应抛出 ValueError。"""
        print('\n[TestHistoryPanelPhase6KlineInplace] new_htype conflict raises')
        values = np.ones((1, 5, 1), dtype=float)
        hp = HistoryPanel(values=values, levels=['s1'], rows=['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'], columns=['close'])
        with self.assertRaises(ValueError):
            hp.kline.sma(window=2, price_htype='close', new_htype='close', inplace=True)

    def test_kline_inplace_empty_panel_raises(self):
        """空面板上 kline 指标应抛出 ValueError（不返回空面板）。"""
        print('\n[TestHistoryPanelPhase6KlineInplace] empty panel raises')
        hp = HistoryPanel()
        with self.assertRaises(ValueError):
            hp.kline.sma(window=2, price_htype='close', inplace=False)

    def test_kline_macd_inplace_true_adds_three_columns_and_hist_relation(self):
        """macd(inplace=True) 原地追加三列，且 hist ≈ macd - signal。"""
        print('\n[TestHistoryPanelPhase6KlineInplace] macd inplace=True adds columns and relation holds')
        # 构造一条足够长的序列，避免全 NaN
        close = np.linspace(10.0, 20.0, 60, dtype=float)
        values = close.reshape(1, -1, 1)
        hp = HistoryPanel(
            values=values,
            levels=['s1'],
            rows=pd.date_range('2023-01-01', periods=60),
            columns=['close'],
        )
        ret = hp.kline.macd(inplace=True)
        self.assertIs(ret, hp)
        print('  htypes tail:', hp.htypes[-3:])

        tag = '12_26_9'
        n1, n2, n3 = f'macd_{tag}', f'macd_signal_{tag}', f'macd_hist_{tag}'
        self.assertIn(n1, hp.htypes)
        self.assertIn(n2, hp.htypes)
        self.assertIn(n3, hp.htypes)

        macd_arr = hp.values[0, :, hp.htypes.index(n1)]
        sig_arr = hp.values[0, :, hp.htypes.index(n2)]
        hist_arr = hp.values[0, :, hp.htypes.index(n3)]
        diff = macd_arr - sig_arr
        print('  macd/signal/hist first valid:', macd_arr[~np.isnan(macd_arr)][:3], sig_arr[~np.isnan(sig_arr)][:3], hist_arr[~np.isnan(hist_arr)][:3])
        self.assertTrue(np.allclose(hist_arr, diff, equal_nan=True))


class TestHistoryPanelPhase7ResearchPreset(unittest.TestCase):
    """阶段七：research_preset 作为第一入口。"""

    def test_research_preset_ohlcv_macd_ma_inplace_false_returns_new_panel(self):
        """inplace=False 返回新面板，新增列集合正确且结果关系满足定义。"""
        print('\n[TestHistoryPanelPhase7ResearchPreset] ohlcv_macd_ma inplace=False returns new panel')
        n = 60
        close = np.linspace(10.0, 20.0, n, dtype=float)
        open_ = close - 0.2
        high = close + 0.3
        low = close - 0.5
        vol = np.linspace(1000.0, 2000.0, n, dtype=float)
        values = np.stack([open_, high, low, close, vol], axis=1).reshape(1, n, 5)
        hp = HistoryPanel(
            values=values,
            levels=['s1'],
            rows=pd.date_range('2023-01-01', periods=n),
            columns=['open', 'high', 'low', 'close', 'vol'],
        )

        hp2 = hp.research_preset('ohlcv_macd_ma', inplace=False)
        print('  hp.htypes:', hp.htypes)
        print('  hp2.htypes tail:', hp2.htypes[-8:])

        self.assertIsInstance(hp2, HistoryPanel)
        self.assertIsNot(hp2, hp)
        self.assertEqual(hp.htypes, ['open', 'high', 'low', 'close', 'vol'])
        # 至少包含：MACD 三列 + 一条均线列
        self.assertIn('macd_12_26_9', hp2.htypes)
        self.assertIn('macd_signal_12_26_9', hp2.htypes)
        self.assertIn('macd_hist_12_26_9', hp2.htypes)
        self.assertIn('sma_20', hp2.htypes)

        # 关系断言：hist = macd - signal
        macd_arr = hp2.values[0, :, hp2.htypes.index('macd_12_26_9')]
        sig_arr = hp2.values[0, :, hp2.htypes.index('macd_signal_12_26_9')]
        hist_arr = hp2.values[0, :, hp2.htypes.index('macd_hist_12_26_9')]
        self.assertTrue(np.allclose(hist_arr, macd_arr - sig_arr, equal_nan=True))

        # 数值正确性：sma_20 与 tafuncs.sma 对齐（抽检末端 5 点）
        import qteasy.tafuncs as tafuncs
        expected = np.asarray(tafuncs.sma(close, timeperiod=20)).ravel()
        got = hp2.values[0, :, hp2.htypes.index('sma_20')]
        print('  sma_20 last 5 expected/got:', expected[-5:], got[-5:])
        self.assertTrue(np.allclose(got[-5:], expected[-5:], equal_nan=True))

    def test_research_preset_inplace_true_mutates_and_returns_self(self):
        """inplace=True 原地扩列并返回原面板。"""
        print('\n[TestHistoryPanelPhase7ResearchPreset] inplace=True mutates and returns self')
        n = 40
        close = np.linspace(1.0, 2.0, n, dtype=float)
        values = np.stack([close - 0.1, close + 0.2, close - 0.2, close, np.ones(n) * 1000.0], axis=1).reshape(1, n, 5)
        hp = HistoryPanel(values=values, levels=['s1'], rows=pd.date_range('2023-01-01', periods=n), columns=['open', 'high', 'low', 'close', 'vol'])
        ret = hp.research_preset('ohlcv_macd_ma', inplace=True)
        print('  ret is hp:', ret is hp)
        self.assertIs(ret, hp)
        self.assertIn('macd_12_26_9', hp.htypes)
        self.assertIn('sma_20', hp.htypes)

    def test_research_preset_invalid_name_raises_and_lists_available(self):
        """非法 preset 名应抛 ValueError，并提示可用 preset。"""
        print('\n[TestHistoryPanelPhase7ResearchPreset] invalid preset name raises')
        hp = HistoryPanel(values=np.ones((1, 3, 1)), levels=['s1'], rows=['2023-01-01', '2023-01-02', '2023-01-03'], columns=['close'])
        with self.assertRaises(ValueError) as cm:
            hp.research_preset('not_exists', inplace=False)
        msg = str(cm.exception)
        print('  error message:', msg)
        self.assertIn('available', msg.lower())

    def test_research_preset_missing_columns_gives_suggestion(self):
        """缺列时应抛 ValueError，信息包含 missing 列与建议。"""
        print('\n[TestHistoryPanelPhase7ResearchPreset] missing columns gives suggestion')
        # 只有 close，无 open/high/low/vol
        hp = HistoryPanel(values=np.ones((1, 10, 1)), levels=['s1'], rows=pd.date_range('2023-01-01', periods=10), columns=['close'])
        with self.assertRaises(ValueError) as cm:
            hp.research_preset('ohlcv_macd_ma', inplace=False)
        msg = str(cm.exception)
        print('  error message:', msg)
        self.assertIn('missing', msg.lower())
        self.assertIn('open', msg.lower())
        self.assertIn('vol', msg.lower())


class TestHistoryPanelTAApplyAndPatterns(unittest.TestCase):
    """ 测试 HistoryPanel.apply_ta 与 candle_pattern。"""

    def test_apply_ta_sma_as_panel(self):
        """ apply_ta('sma') 应等价于对每只股票调用 tafuncs.sma，并在 Panel 中追加一列。"""
        print('\n[TestHistoryPanelTAApplyAndPatterns] apply_ta sma as_panel')
        values = np.array(
                [
                    [[1.0], [2.0], [3.0], [4.0], [5.0]],
                    [[2.0], [3.0], [4.0], [5.0], [6.0]],
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        hp_out = hp.apply_ta('sma', htype='close', as_panel=True, timeperiod=2)
        print('  hp_out.htypes:', hp_out.htypes, 'shape:', hp_out.shape)

        # 原 htypes 保留，并新增一个以 func_name 命名的列
        self.assertIn('close', hp_out.htypes)
        self.assertIn('sma', hp_out.htypes)
        self.assertEqual(hp_out.shares, shares)

        import qteasy.tafuncs as tafuncs
        idx = pd.to_datetime(hdates)
        for i, share in enumerate(shares):
            s = pd.Series(values[i, :, 0], index=idx)
            expected = tafuncs.sma(s, timeperiod=2)
            got = hp_out.values[i, :, hp_out.htypes.index('sma')]
            self.assertTrue(np.allclose(got, expected.values, equal_nan=True))

    def test_apply_ta_invalid_name_raises(self):
        """ func_name 不存在时应抛出 ValueError。"""
        print('\n[TestHistoryPanelTAApplyAndPatterns] apply_ta invalid func raises')
        values = np.ones((1, 3, 1))
        hp = HistoryPanel(values=values, levels=['s1'], rows=['2023-01-01', '2023-01-02', '2023-01-03'], columns=['close'])
        with self.assertRaises(ValueError):
            hp.apply_ta('non_exist_func', htype='close', as_panel=True)

    def test_candle_pattern_basic(self):
        """ candle_pattern 返回整型信号矩阵，与 tafuncs 中形态函数结果一致。"""
        print('\n[TestHistoryPanelTAApplyAndPatterns] candle_pattern basic')
        # 构造一个简单的 OHLC 序列，这里不强求真是 hammer，只验证调用与对齐行为
        values = np.array(
                [
                    [
                        [10.0, 11.0, 9.5, 10.5],
                        [10.5, 11.5, 10.0, 11.0],
                    ],
                ]
        )
        shares = ['s1']
        hdates = ['2023-01-01', '2023-01-02']
        htypes = ['open', 'high', 'low', 'close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)

        import qteasy.tafuncs as tafuncs
        idx = pd.to_datetime(hdates)
        open_s = pd.Series([10.0, 10.5], index=idx)
        high_s = pd.Series([11.0, 11.5], index=idx)
        low_s = pd.Series([9.5, 10.0], index=idx)
        close_s = pd.Series([10.5, 11.0], index=idx)
        expected = tafuncs.cdlhammer(open_s, high_s, low_s, close_s)

        df = hp.candle_pattern('cdlhammer', as_panel=False)
        print('  candle_pattern df:\n', df)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(list(df.index), list(idx))
        self.assertEqual(list(df.columns), shares)
        self.assertTrue(np.allclose(df['s1'].values, expected.values))


class TestHistoryPanelIntegration(unittest.TestCase):
    """ HistoryPanel 统计 / 因子 / K 线 API 的简单集成验收。"""

    def test_factor_flow_end_to_end(self):
        """ 从价格 → 收益率 / 波动率 → 技术指标 → 形态识别 的最小闭环。"""
        print('\n[TestHistoryPanelIntegration] factor flow end-to-end')
        # 构造两只股票的 OHLC 序列
        values = np.array(
                [
                    # s1: open, high, low, close
                    [
                        [10.0, 11.0, 9.5, 10.5],
                        [10.5, 11.5, 10.0, 11.0],
                        [11.0, 12.0, 10.5, 11.5],
                        [11.5, 12.5, 11.0, 12.0],
                        [12.0, 13.0, 11.5, 12.5],
                    ],
                    # s2: open, high, low, close
                    [
                        [20.0, 21.0, 19.5, 20.5],
                        [20.5, 21.5, 20.0, 21.0],
                        [21.0, 22.0, 20.5, 21.5],
                        [21.5, 22.5, 21.0, 22.0],
                        [22.0, 23.0, 21.5, 22.5],
                    ],
                ]
        )
        shares = ['s1', 's2']
        hdates = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
        htypes = ['open', 'high', 'low', 'close']
        hp = HistoryPanel(values=values, levels=shares, rows=hdates, columns=htypes)
        print('  hp shape:', hp.shape, 'shares:', hp.shares, 'htypes:', hp.htypes)

        # 1) 收益率 & 波动率
        ret_df = hp.returns(price_htype='close', method='simple', as_panel=False)
        vol_df = hp.volatility(window=3, price_htype='close', annualize=False, as_panel=False)
        print('  returns:\n', ret_df)
        print('  volatility:\n', vol_df)

        self.assertEqual(list(ret_df.columns), shares)
        self.assertEqual(list(vol_df.columns), shares)
        self.assertEqual(list(ret_df.index), list(pd.to_datetime(hdates)))

        # 2) K 线指标（SMA）
        hp_sma = hp.kline.sma(window=2, price_htype='close')
        print('  hp_sma.htypes:', hp_sma.htypes)
        self.assertIn('sma_2', hp_sma.htypes)
        self.assertEqual(hp_sma.shares, shares)
        self.assertEqual(hp_sma.hdates, list(pd.to_datetime(hdates)))

        # 3) 通过 apply_ta 再生成一条 SMA 因子
        hp_ta = hp_sma.apply_ta('sma', htype='close', as_panel=True, timeperiod=3)
        print('  hp_ta.htypes:', hp_ta.htypes)
        self.assertIn('sma', hp_ta.htypes)

        # 4) 蜡烛形态识别
        pattern_df = hp.candle_pattern('cdlhammer', as_panel=False)
        print('  candle_pattern:\n', pattern_df)
        self.assertIsInstance(pattern_df, pd.DataFrame)
        self.assertEqual(list(pattern_df.columns), shares)
        self.assertEqual(list(pattern_df.index), list(pd.to_datetime(hdates)))


class TestHistoryPanelPhase1Indexing(unittest.TestCase):
    """阶段一：__getitem__ 返回子 HistoryPanel、to_numpy、subpanel。"""

    def setUp(self):
        print('\n[TestHistoryPanelPhase1Indexing] setUp')
        self.data = np.random.randint(10, size=(5, 10, 4))
        self.index = pd.date_range(start='20200101', freq='d', periods=10)
        self.shares = '000100,000101,000102,000103,000104'
        self.htypes = 'close,open,high,low'
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.htypes, rows=self.index)

    def test_getitem_returns_history_panel(self):
        """单列 / 单标的切片应为 HistoryPanel，且轴标签与数值与旧 ndarray 语义一致。"""
        print('\n[TestHistoryPanelPhase1Indexing] getitem returns HistoryPanel')
        sub = self.hp['close']
        self.assertIsInstance(sub, qt.HistoryPanel)
        self.assertEqual(sub.shape, (5, 10, 1))
        self.assertEqual(sub.htypes, ['close'])
        self.assertTrue(np.allclose(sub.values, self.data[:, :, 0:1]))
        sub2 = self.hp['close', '000100']
        print('  sub2.shape:', sub2.shape, 'htypes:', sub2.htypes, 'shares:', sub2.shares)
        self.assertIsInstance(sub2, qt.HistoryPanel)
        self.assertEqual(sub2.shares, ['000100'])
        self.assertEqual(sub2.htypes, ['close'])
        sub3 = self.hp[:, :, 0:3]
        self.assertEqual(sub3.hdates, list(self.index[:3]))
        self.assertTrue(np.allclose(sub3.values, self.data[:, 0:3, :]))

    def test_empty_panel_getitem_returns_empty_panel(self):
        """空面板上任意索引返回空 HistoryPanel，不返回 None。"""
        print('\n[TestHistoryPanelPhase1Indexing] empty getitem -> empty panel')
        empty = qt.HistoryPanel()
        for keys in (None, slice(None), 'close'):
            sub = empty[keys]
            self.assertIsInstance(sub, qt.HistoryPanel, msg=f'keys={keys!r}')
            self.assertTrue(sub.is_empty, msg=f'keys={keys!r}')

    def test_to_numpy_copy_semantics(self):
        """to_numpy(copy=False) 可与底层共享；copy=True 修改不污染原件；空面板形状 (0,0,0)。"""
        print('\n[TestHistoryPanelPhase1Indexing] to_numpy copy semantics')
        a0 = self.hp.to_numpy(copy=False)
        a1 = self.hp.to_numpy(copy=True)
        self.assertTrue(np.shares_memory(a0, self.hp.values))
        a1[0, 0, 0] = -99999.0
        self.assertNotEqual(self.hp.values[0, 0, 0], -99999.0)
        empty = qt.HistoryPanel()
        self.assertEqual(empty.to_numpy().shape, (0, 0, 0))

    def test_subpanel_named_args_equivalent_to_getitem(self):
        """subpanel 具名参数与等价 __getitem__ 在 copy=False 下数值与轴一致。"""
        print('\n[TestHistoryPanelPhase1Indexing] subpanel vs getitem')
        g = self.hp['close', '000100', 0:5]
        s = self.hp.subpanel(htypes='close', shares='000100', hdates=slice(0, 5), copy=False)
        self.assertTrue(np.allclose(g.values, s.values))
        self.assertEqual(g.shares, s.shares)
        self.assertEqual(g.hdates, s.hdates)
        self.assertEqual(g.htypes, s.htypes)

    def test_subpanel_copy_true_detaches_values(self):
        """subpanel(copy=True) 得到的数据拷贝，修改子面板不改动父面板。"""
        print('\n[TestHistoryPanelPhase1Indexing] subpanel copy=True detaches')
        sub = self.hp.subpanel(htypes='close', shares='000100', copy=True)
        sub.values[0, 0, 0] = -12345.0
        self.assertNotEqual(self.hp.values[0, 0, 0], -12345.0)


class TestHistoryPanelPhase2Setitem(unittest.TestCase):
    """阶段二：__setitem__ 单列扩列/覆盖与 copy 语义。"""

    def setUp(self):
        print('\n[TestHistoryPanelPhase2Setitem] setUp')
        np.random.seed(42)
        self.data = np.random.randint(10, size=(5, 10, 4))
        self.index = pd.date_range(start='20200101', freq='d', periods=10)
        self.shares = '000100,000101,000102,000103,000104'
        self.htypes = 'close,open,high,low'
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.htypes, rows=self.index)
        print('  hp.shape:', self.hp.shape, 'htypes:', self.hp.htypes)

    def test_setitem_raises_on_empty_panel(self):
        """空面板上 __setitem__ 抛 ValueError。"""
        print('\n[TestHistoryPanelPhase2Setitem] empty panel -> ValueError')
        empty = qt.HistoryPanel()
        with self.assertRaises(ValueError) as ctx:
            empty['x'] = 1.0
        self.assertIn('empty', str(ctx.exception).lower())

    def test_setitem_rejects_non_str_key(self):
        """非 str 列名 -> TypeError（英文）。"""
        print('\n[TestHistoryPanelPhase2Setitem] non-str key -> TypeError')
        arr = np.zeros((5, 10), dtype=float)
        with self.assertRaises(TypeError) as ctx:
            self.hp[0] = arr
        self.assertIn('str', str(ctx.exception).lower())
        with self.assertRaises(TypeError):
            self.hp[('close', '000100')] = arr

    def test_setitem_new_column_scalar_broadcast(self):
        """标量广播为新列，追加在 htypes 末尾。"""
        print('\n[TestHistoryPanelPhase2Setitem] scalar broadcast new column')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        hp['factor_a'] = 3.0
        self.assertEqual(hp.shape, (5, 10, 5))
        self.assertEqual(hp.htypes[-1], 'factor_a')
        self.assertTrue(np.all(hp.values[:, :, -1] == 3.0))

    def test_setitem_new_column_2d_array(self):
        """(M,L) 数组新列。"""
        print('\n[TestHistoryPanelPhase2Setitem] 2d new column')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        arr = np.arange(50, dtype=float).reshape(5, 10)
        hp['factor_b'] = arr
        self.assertIn('factor_b', hp.htypes)
        idx = hp.htypes.index('factor_b')
        self.assertTrue(np.allclose(hp.values[:, :, idx], arr))

    def test_setitem_new_column_broadcast_ml1(self):
        """(M,L,1) 广播等价于 (M,L)。"""
        print('\n[TestHistoryPanelPhase2Setitem] (M,L,1) broadcast')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        arr = np.arange(50, dtype=float).reshape(5, 10, 1)
        hp['factor_c'] = arr
        idx = hp.htypes.index('factor_c')
        self.assertTrue(np.allclose(hp.values[:, :, idx].ravel(), np.arange(50, dtype=float)))

    def test_setitem_overwrites_existing_column(self):
        """同名列静默覆盖，htypes 长度不变。"""
        print('\n[TestHistoryPanelPhase2Setitem] overwrite existing column')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        ncols_before = len(hp.htypes)
        repl = np.full((5, 10), np.nan, dtype=float)
        hp['close'] = repl
        self.assertEqual(len(hp.htypes), ncols_before)
        self.assertEqual(hp.htypes[0], 'close')
        ci = hp.htypes.index('close')
        self.assertTrue(np.all(np.isnan(hp.values[:, :, ci])))

    def test_setitem_wrong_shape_raises_valueerror(self):
        """无法广播到 (M,L) -> ValueError（英文）。"""
        print('\n[TestHistoryPanelPhase2Setitem] wrong shape -> ValueError')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        with self.assertRaises(ValueError):
            hp['bad'] = np.zeros((5, 9), dtype=float)
        with self.assertRaises(ValueError):
            hp['bad2'] = np.zeros((4, 10), dtype=float)
        with self.assertRaises(ValueError):
            hp['bad3'] = np.zeros((5, 10, 2), dtype=float)

    def test_setitem_parent_mutate_does_not_affect_subpanel_copy_true(self):
        """subpanel(copy=True) 在父扩列后不变。"""
        print('\n[TestHistoryPanelPhase2Setitem] subpanel copy=True unchanged after parent setitem')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        sub = hp.subpanel(htypes='close', copy=True)
        sub_close_before = sub.values.copy()
        hp['newcol'] = 7.0
        self.assertNotIn('newcol', sub.htypes)
        self.assertTrue(np.allclose(sub.values, sub_close_before))

    def test_setitem_after_getitem_copy_false_subpanel_does_not_see_new_column(self):
        """父面板扩列后，copy=False 子面板不自动出现新列。"""
        print('\n[TestHistoryPanelPhase2Setitem] copy=False subpanel does not see new column')
        hp = qt.HistoryPanel(values=self.data.copy(), levels=self.shares, columns=self.htypes, rows=self.index)
        sub = hp['close']
        self.assertEqual(sub.shape[2], 1)
        hp['newcol'] = 5.0
        self.assertEqual(hp.shape[2], 5)
        self.assertNotIn('newcol', sub.htypes)
        self.assertEqual(sub.shape[2], 1)
        print('  parent htypes:', hp.htypes, 'sub htypes:', sub.htypes)


def _where_broadcast_bool(cond, target_shape):
    """与 ``HistoryPanel.where`` 一致的期望：含 (M,L)/(M,)/(M,1) 沿 htype 轴展开。"""
    m, l_count, n = target_shape
    b = np.asarray(cond, dtype=bool)
    if b.shape == target_shape:
        return np.array(b, copy=True)
    if b.ndim == 0:
        return np.broadcast_to(b, target_shape)
    if b.ndim == 2 and b.shape == (m, l_count):
        b = b[:, :, np.newaxis]
    elif b.ndim == 1 and b.shape == (m,):
        b = b.reshape(m, 1, 1)
    elif b.ndim == 2 and b.shape == (m, 1):
        b = b.reshape(m, 1, 1)
    return np.broadcast_to(b, target_shape)


def _make_history_panel_345():
    """阶段三功能性用例金标准：shape (3,4,5)，values[m,l,n]=20*m+5*l+n。"""
    values = np.arange(60, dtype=np.float64).reshape(3, 4, 5)
    rows = pd.date_range('2020-01-01', periods=4, freq='D')
    return qt.HistoryPanel(
        values=values,
        levels=['S0', 'S1', 'S2'],
        rows=rows,
        columns=['h0', 'h1', 'h2', 'h3', 'h4'],
    )


class TestHistoryPanelPhase3Where(unittest.TestCase):
    """阶段三：where 广播为 (M,L,N) bool 与 mask 契约。"""

    def setUp(self):
        print('\n[TestHistoryPanelPhase3Where] setUp (5,10,4)')
        np.random.seed(7)
        self.data = np.random.randint(10, size=(5, 10, 4))
        self.index = pd.date_range(start='20200101', freq='d', periods=10)
        self.shares = '000100,000101,000102,000103,000104'
        self.htypes = 'close,open,high,low'
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.htypes, rows=self.index)

    # --- §3.1 边界与契约 ---

    def test_where_empty_panel_returns_bool_zeros_shape(self):
        """空面板 where -> (0,0,0) bool。"""
        print('\n[TestHistoryPanelPhase3Where] empty panel')
        empty = qt.HistoryPanel()
        out = empty.where(True)
        self.assertEqual(out.shape, (0, 0, 0))
        self.assertEqual(out.dtype, bool)
        self.assertEqual(out.size, 0)

    def test_where_mln_same_shape_passthrough_values(self):
        """(M,L,N) bool 与输出逐元素一致；不修改 hp 与传入数组。"""
        print('\n[TestHistoryPanelPhase3Where] mln passthrough')
        cond = np.random.rand(5, 10, 4) > 0.5
        cond = np.asarray(cond, dtype=bool)
        cond_copy = cond.copy()
        vals_before = self.hp.values.copy()
        out = self.hp.where(cond)
        self.assertTrue(np.array_equal(out, cond))
        self.assertEqual(out.shape, self.hp.shape)
        self.assertTrue(np.array_equal(self.hp.values, vals_before))
        self.assertTrue(np.array_equal(cond, cond_copy))

    def test_where_ml_broadcasts_to_mln(self):
        """(M,L) True 则整根 n 为 True。"""
        print('\n[TestHistoryPanelPhase3Where] ml broadcast')
        cond = np.zeros((5, 10), dtype=bool)
        cond[2, 7] = True
        out = self.hp.where(cond)
        self.assertEqual(out.shape, self.hp.shape)
        self.assertTrue(bool(out[2, 7, 0]) and bool(out[2, 7, 3]))
        self.assertFalse(bool(out[0, 0, 0]))

    def test_where_ml1_broadcasts_to_mln(self):
        """(M,L,1) 与 (M,L) 等价广播。"""
        print('\n[TestHistoryPanelPhase3Where] ml1 broadcast')
        cond = np.zeros((5, 10, 1), dtype=bool)
        cond[1, 3, 0] = True
        out = self.hp.where(cond)
        self.assertTrue(bool(out[1, 3, 2]))
        self.assertFalse(bool(out[1, 4, 2]))

    def test_where_scalar_broadcasts(self):
        """标量 True/False。"""
        print('\n[TestHistoryPanelPhase3Where] scalar')
        t = self.hp.where(True)
        self.assertTrue(np.all(t))
        f = self.hp.where(False)
        self.assertFalse(np.any(f))

    def test_where_all_true_all_false(self):
        """全 True / 全 False 的 (M,L,N)。"""
        print('\n[TestHistoryPanelPhase3Where] all true false')
        tt = np.ones(self.hp.shape, dtype=bool)
        ff = np.zeros(self.hp.shape, dtype=bool)
        self.assertTrue(np.array_equal(self.hp.where(tt), tt))
        self.assertTrue(np.array_equal(self.hp.where(ff), ff))

    def test_where_callable_returns_ml(self):
        """callable 返回 (M,L)。"""
        print('\n[TestHistoryPanelPhase3Where] callable ml')
        out = self.hp.where(lambda p: np.ones((5, 10), dtype=bool))
        self.assertTrue(np.all(out))
        self.assertEqual(out.shape, self.hp.shape)

    def test_where_callable_returns_mln(self):
        """callable 返回与 values 同形比较。"""
        print('\n[TestHistoryPanelPhase3Where] callable mln')
        expected = self.hp.values > 0.5
        out = self.hp.where(lambda p: p.values > 0.5)
        self.assertTrue(np.array_equal(out, expected))

    def test_where_does_not_mutate_panel(self):
        """where 不改变面板。"""
        print('\n[TestHistoryPanelPhase3Where] no mutate')
        h = self.hp
        before_v = h.values.copy()
        before_ht = list(h.htypes)
        before_sh = list(h.shares)
        _ = h.where(lambda p: p.values >= 0)
        self.assertTrue(np.array_equal(h.values, before_v))
        self.assertEqual(list(h.htypes), before_ht)
        self.assertEqual(list(h.shares), before_sh)

    def test_where_wrong_shape_raises_valueerror(self):
        """不可广播形状 -> ValueError（英文）。"""
        print('\n[TestHistoryPanelPhase3Where] wrong shape')
        with self.assertRaises(ValueError) as ctx:
            self.hp.where(np.zeros((5, 9), dtype=bool))
        self.assertIn('broadcast', str(ctx.exception).lower())
        with self.assertRaises(ValueError):
            self.hp.where(np.zeros((4, 10), dtype=bool))
        with self.assertRaises(ValueError):
            self.hp.where(np.zeros((5, 10, 3), dtype=bool))

    def test_where_invalid_type_raises_typeerror(self):
        """str -> TypeError。"""
        print('\n[TestHistoryPanelPhase3Where] str -> TypeError')
        with self.assertRaises(TypeError) as ctx:
            self.hp.where('not_valid')
        self.assertIn('str', str(ctx.exception).lower())

    # --- §3.2 功能性 (3,4,5) ---

    def test_where_functional_scalar_true(self):
        print('\n[TestHistoryPanelPhase3Where] F1 scalar True')
        hp = _make_history_panel_345()
        out = hp.where(True)
        expected = np.ones((3, 4, 5), dtype=bool)
        self.assertTrue(np.array_equal(out, expected))
        print('  out.sum():', out.sum())

    def test_where_functional_scalar_false(self):
        print('\n[TestHistoryPanelPhase3Where] F2 scalar False')
        hp = _make_history_panel_345()
        out = hp.where(False)
        expected = np.zeros((3, 4, 5), dtype=bool)
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_threshold_on_full_values(self):
        print('\n[TestHistoryPanelPhase3Where] F3 threshold')
        hp = _make_history_panel_345()
        cond = hp.values > 35
        out = hp.where(cond)
        self.assertTrue(np.array_equal(out, hp.values > 35))
        print('  true count:', out.sum())

    def test_where_functional_time_slice_ml(self):
        print('\n[TestHistoryPanelPhase3Where] F4 time slice')
        hp = _make_history_panel_345()
        cond_ml = np.zeros((3, 4), dtype=bool)
        cond_ml[:, 2] = True
        out = hp.where(cond_ml)
        expected = _where_broadcast_bool(cond_ml, (3, 4, 5))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_share_dimension(self):
        print('\n[TestHistoryPanelPhase3Where] F5 share dim')
        hp = _make_history_panel_345()
        cond_m = np.array([False, True, False], dtype=bool).reshape(3, 1)
        out = hp.where(cond_m)
        expected = _where_broadcast_bool(cond_m, (3, 4, 5))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_ml1_replicate_across_htypes(self):
        print('\n[TestHistoryPanelPhase3Where] F6 ml1 replicate')
        hp = _make_history_panel_345()
        values = hp.values
        cond = np.zeros((3, 4, 1), dtype=bool)
        cond[:, :, 0] = (values[:, :, 0] % 3 == 0)
        out = hp.where(cond)
        expected = _where_broadcast_bool(cond, (3, 4, 5))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_htype_axis_broadcast(self):
        print('\n[TestHistoryPanelPhase3Where] F6b htype axis')
        hp = _make_history_panel_345()
        cond = np.zeros((1, 1, 5), dtype=bool)
        cond[0, 0, 1] = True
        cond[0, 0, 3] = True
        out = hp.where(cond)
        expected = _where_broadcast_bool(cond, (3, 4, 5))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_single_share_leading_dim(self):
        print('\n[TestHistoryPanelPhase3Where] F7 leading 1 on share')
        hp = _make_history_panel_345()
        values = hp.values
        cond = np.zeros((1, 4, 5), dtype=bool)
        cond[0, :, :] = values[0, :, :] < 12
        out = hp.where(cond)
        expected = _where_broadcast_bool(cond, (3, 4, 5))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_nan_mask(self):
        print('\n[TestHistoryPanelPhase3Where] F8 nan')
        hp = _make_history_panel_345()
        values2 = hp.values.copy()
        values2[1, 2, 3] = np.nan
        hp_nan = qt.HistoryPanel(
            values=values2,
            levels=hp.shares,
            rows=hp.hdates,
            columns=hp.htypes,
        )
        out = hp_nan.where(np.isnan(hp_nan.values))
        self.assertTrue(np.array_equal(out, np.isnan(values2)))

    def test_where_functional_integer01_ml(self):
        print('\n[TestHistoryPanelPhase3Where] F9 int01')
        hp = _make_history_panel_345()
        g = np.indices((3, 4))
        cond = ((g[0] + g[1]) % 2).astype(np.int32)
        out = hp.where(cond)
        expected = _where_broadcast_bool(cond.astype(bool), (3, 4, 5))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_callable_compare_first_htype(self):
        print('\n[TestHistoryPanelPhase3Where] F10 callable first htype')
        hp = _make_history_panel_345()
        values = hp.values
        slab = (values[:, :, 0] >= 15)[:, :, np.newaxis]
        expected = _where_broadcast_bool(slab, (3, 4, 5))
        out = hp.where(lambda p: p.values[:, :, 0] >= 15)
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_callable_compound(self):
        print('\n[TestHistoryPanelPhase3Where] F11 compound')
        hp = _make_history_panel_345()
        values = hp.values
        expected = (values >= 10) & (values <= 50)
        out = hp.where(lambda p: (p.values >= 10) & (p.values <= 50))
        self.assertTrue(np.array_equal(out, expected))

    def test_where_functional_callable_reads_panel(self):
        print('\n[TestHistoryPanelPhase3Where] F12 callable reads panel')
        hp = _make_history_panel_345()
        out = hp.where(lambda p: np.ones(p.shape, dtype=bool) & (p.values == p.values))
        self.assertTrue(np.all(out))


class TestHistoryPanelPhase13HtypeAttr(unittest.TestCase):
    """阶段十三：合法 htype 属性访问与 hp['col'] 对齐。"""

    def setUp(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] setUp')
        np.random.seed(7)
        self.data = np.random.randint(1, 100, size=(3, 8, 4)).astype(float)
        self.index = pd.date_range('2020-01-01', periods=8, freq='D')
        self.hp = qt.HistoryPanel(
            values=self.data,
            levels=['A', 'B', 'C'],
            rows=self.index,
            columns=['open', 'high', 'low', 'close'],
        )

    def test_attr_close_open_align_bracket(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] close/open vs bracket')
        for col in ('close', 'open'):
            sub_b = self.hp[col]
            sub_a = getattr(self.hp, col)
            self.assertIsInstance(sub_a, qt.HistoryPanel)
            self.assertEqual(sub_a.shape, sub_b.shape)
            self.assertEqual(sub_a.htypes, sub_b.htypes)
            self.assertTrue(np.allclose(sub_a.values, sub_b.values))

    def test_attr_low_matches_full_getitem(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] low vs bracket / htype axis')
        sub = self.hp.low
        self.assertTrue(np.allclose(sub.values, self.hp['low'].values))
        self.assertTrue(np.allclose(sub.values, self.hp['low', :, :].values))

    def test_non_identifier_htype_only_bracket(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] close|b getattr')
        data = np.ones((2, 4, 1))
        idx = pd.date_range('2021-01-01', periods=4, freq='D')
        hp = qt.HistoryPanel(values=data, levels=['X', 'Y'], rows=idx, columns=['close|b'])
        self.assertIn('close|b', hp.htypes)
        with self.assertRaises(AttributeError) as ctx:
            getattr(hp, 'close|b')
        self.assertIn('bracket', str(ctx.exception).lower())
        sub = hp['close|b']
        self.assertEqual(sub.shape, (2, 4, 1))

    def test_reserved_api_not_shadowed_by_column_where(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] column where vs method')
        data = np.random.rand(2, 3, 3)
        idx = pd.date_range('2020-06-01', periods=3, freq='D')
        hp = qt.HistoryPanel(
            values=data,
            levels=['S0', 'S1'],
            rows=idx,
            columns=['close', 'open', 'where'],
        )
        self.assertTrue(callable(hp.where))
        wcol = hp['where']
        self.assertIsInstance(wcol, qt.HistoryPanel)
        self.assertEqual(wcol.shape, (2, 3, 1))
        self.assertEqual(wcol.htypes, ['where'])

    def test_unknown_attr_attribute_error(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] unknown attr')
        with self.assertRaises(AttributeError) as ctx:
            _ = self.hp.not_a_real_column_xyz
        self.assertIn('bracket', str(ctx.exception).lower())

    def test_empty_panel_attr_matches_getitem(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] empty panel')
        empty = qt.HistoryPanel()
        sub_g = empty['close']
        sub_a = empty.close
        self.assertIsInstance(sub_g, qt.HistoryPanel)
        self.assertIsInstance(sub_a, qt.HistoryPanel)
        self.assertTrue(sub_g.is_empty and sub_a.is_empty)

    def test_values_property_still_ndarray_or_none(self):
        print('\n[TestHistoryPanelPhase13HtypeAttr] values not column')
        self.assertTrue(
            self.hp.values is None or isinstance(self.hp.values, np.ndarray)
        )


class TestHistoryPanelPhase14Compare(unittest.TestCase):
    """阶段十四：比较运算返回 bool ndarray 并与 where 衔接。"""

    def setUp(self):
        print('\n[TestHistoryPanelPhase14Compare] setUp')
        np.random.seed(11)
        self.data = np.random.randint(1, 50, size=(4, 6, 3)).astype(float)
        self.data[0, 0, 0] = np.nan
        self.index = pd.date_range('2019-01-01', periods=6, freq='D')
        self.hp = qt.HistoryPanel(
            values=self.data,
            levels=['a', 'b', 'c', 'd'],
            rows=self.index,
            columns=['close', 'open', 'vol'],
        )

    def test_full_panel_gt_scalar(self):
        print('\n[TestHistoryPanelPhase14Compare] full > 0')
        m = self.hp > 0
        self.assertEqual(m.dtype, bool)
        self.assertEqual(m.shape, self.hp.shape)
        self.assertTrue(np.array_equal(m, self.hp.values > 0))

    def test_full_panel_eq_self(self):
        print('\n[TestHistoryPanelPhase14Compare] hp == hp')
        m = self.hp == self.hp
        self.assertTrue(np.array_equal(m, self.hp.values == self.hp.values))

    def test_close_gt_scalar_and_where(self):
        print('\n[TestHistoryPanelPhase14Compare] close > 15 + where')
        m1 = self.hp.close > 15
        m2 = self.hp['close'] > 15
        self.assertTrue(np.array_equal(m1, m2))
        out = self.hp.where(self.hp.close > 15)
        self.assertEqual(out.shape, self.hp.shape)
        self.assertEqual(out.dtype, bool)
        self.assertTrue(np.array_equal(out, _where_broadcast_bool(m1, self.hp.shape)))

    def test_close_gt_open_where_chain(self):
        print('\n[TestHistoryPanelPhase14Compare] close > open')
        m = self.hp['close'] > self.hp['open']
        exp = self.hp['close'].values > self.hp['open'].values
        self.assertTrue(np.array_equal(m, exp))
        out = self.hp.where(self.hp.close > self.hp.open)
        self.assertTrue(np.array_equal(out, _where_broadcast_bool(m, self.hp.shape)))

    def test_reflected_comparison(self):
        print('\n[TestHistoryPanelPhase14Compare] 5 < hp')
        m_left = 5 < self.hp
        m_right = self.hp > 5
        self.assertTrue(np.array_equal(m_left, m_right))

    def test_mismatched_labels_value_error(self):
        print('\n[TestHistoryPanelPhase14Compare] label mismatch')
        hp2 = qt.HistoryPanel(
            values=self.data.copy(),
            levels=['a', 'b', 'c', 'd'],
            rows=self.index,
            columns=['open', 'close', 'vol'],
        )
        with self.assertRaises(ValueError):
            _ = self.hp > hp2

    def test_compare_ndarray_bad_broadcast_value_error(self):
        print('\n[TestHistoryPanelPhase14Compare] ndarray bad broadcast')
        bad = np.zeros((2, 3))
        with self.assertRaises(ValueError):
            _ = self.hp['close'] > bad

    def test_compare_str_type_error(self):
        print('\n[TestHistoryPanelPhase14Compare] str operand')
        with self.assertRaises(TypeError):
            _ = self.hp > 'x'

    def test_nan_compare_numpy_rules(self):
        print('\n[TestHistoryPanelPhase14Compare] NaN rules')
        v = self.hp.values
        eq = self.hp == self.hp
        self.assertFalse(bool(eq[0, 0, 0]))
        gt = self.hp > 0
        self.assertFalse(bool(gt[0, 0, 0]))
        ne = self.hp != self.hp
        self.assertTrue(bool(ne[0, 0, 0]))
        self.assertTrue(np.isnan(v[0, 0, 0]))

    def test_empty_panel_compare_scalar(self):
        print('\n[TestHistoryPanelPhase14Compare] empty panel')
        empty = qt.HistoryPanel()
        m = empty > 1
        self.assertEqual(m.shape, (0, 0, 0))
        self.assertEqual(m.dtype, bool)


class TestHistoryPanelPhase15Loc(unittest.TestCase):
    """阶段十五：loc 等价 hp[:, :, key]；拒绝三维 bool。"""

    def setUp(self):
        print('\n[TestHistoryPanelPhase15Loc] setUp')
        np.random.seed(13)
        self.data = np.random.rand(3, 7, 2)
        self.index = pd.date_range('2022-01-01', periods=7, freq='D')
        self.hp = qt.HistoryPanel(
            values=self.data,
            levels=['u', 'v', 'w'],
            rows=self.index,
            columns=['c0', 'c1'],
        )

    def _assert_loc_equiv(self, key):
        a = self.hp.loc[key]
        b = self.hp[:, :, key]
        self.assertTrue(np.allclose(a.values, b.values))
        self.assertEqual(a.shares, b.shares)
        self.assertEqual(a.hdates, b.hdates)
        self.assertEqual(a.htypes, b.htypes)

    def test_loc_equiv_slice_single_list_colon(self):
        print('\n[TestHistoryPanelPhase15Loc] slice date list colon')
        self._assert_loc_equiv(slice(0, 4))
        self._assert_loc_equiv(self.index[2])
        self._assert_loc_equiv([self.index[1], self.index[3]])
        self._assert_loc_equiv(slice(None, None, None))

    def test_loc_bool_list_and_ndarray(self):
        print('\n[TestHistoryPanelPhase15Loc] 1d bool')
        L = len(self.hp.hdates)
        mask_l = [True, True, True] + [False] * (L - 3)
        self._assert_loc_equiv(mask_l)
        self._assert_loc_equiv(np.array(mask_l, dtype=bool))

    def test_loc_slice_shares_memory(self):
        print('\n[TestHistoryPanelPhase15Loc] shares_memory')
        sub = self.hp.loc[1:5]
        self.assertTrue(np.shares_memory(sub.values, self.hp.values))
        sub_copy = self.hp.subpanel(hdates=slice(1, 5), copy=True)
        self.assertFalse(np.shares_memory(sub_copy.values, self.hp.values))

    def test_loc_rejects_mln_where_mask(self):
        print('\n[TestHistoryPanelPhase15Loc] reject MLN bool')
        w = self.hp.where(lambda p: p.values > 0.5)
        msg = None
        with self.assertRaises((TypeError, ValueError)) as ctx:
            _ = self.hp.loc[w]
        msg = str(ctx.exception).lower()
        self.assertTrue('where' in msg or 'mask' in msg)

    def test_loc_rejects_wrong_length_bool(self):
        print('\n[TestHistoryPanelPhase15Loc] bool length')
        with self.assertRaises(ValueError) as ctx:
            _ = self.hp.loc[[True, False]]
        self.assertIn('length', str(ctx.exception).lower())

    def test_loc_rejects_ml_bool(self):
        print('\n[TestHistoryPanelPhase15Loc] ML bool')
        bad = np.zeros((3, 7), dtype=bool)
        with self.assertRaises(ValueError):
            _ = self.hp.loc[bad]

    def test_loc_empty_panel(self):
        print('\n[TestHistoryPanelPhase15Loc] empty')
        empty = qt.HistoryPanel()
        self.assertTrue(empty.loc[:].is_empty)

    def test_getitem_third_axis_ndarray_bool_matches_loc(self):
        print('\n[TestHistoryPanelPhase15Loc] [:,:,ndarray] vs loc')
        L = len(self.hp.hdates)
        mask = np.array([True] * 2 + [False] * (L - 2))
        a = self.hp.loc[mask]
        b = self.hp[:, :, mask]
        self.assertTrue(np.allclose(a.values, b.values))


class TestHistoryPanelPhase4CumReturnNormalize(unittest.TestCase):
    """阶段四：cum_return / normalize（研究向，TDD）。"""

    def test_c1_two_shares_close_no_mask(self):
        print('\n[Phase4 C1] 两 share、单列 close，无 mask')
        values = np.array(
            [
                [[10.0], [11.0], [12.0]],
                [[100.0], [100.0], [110.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['s0', 's1'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        cs = hp.cum_return(method='simple')
        cl = hp.cum_return(method='log')
        nz = hp.normalize(base_index=0)
        print('  cum simple s0:', cs.values[0, :, 0])
        self.assertEqual(cs.htypes, ['cumret_close'])
        np.testing.assert_allclose(cs.values[0, :, 0], [0.0, 0.1, 0.2], rtol=0, atol=1e-12)
        np.testing.assert_allclose(cs.values[1, :, 0], [0.0, 0.0, 0.1], rtol=0, atol=1e-12)
        np.testing.assert_allclose(cl.values[0, :, 0], [0.0, np.log(1.1), np.log(1.2)], rtol=0, atol=1e-12)
        np.testing.assert_allclose(nz.values[0, :, 0], [1.0, 1.1, 1.2], rtol=0, atol=1e-12)
        np.testing.assert_allclose(nz.values[1, :, 0], [1.0, 1.0, 1.1], rtol=0, atol=1e-12)

    def test_c2_multi_htypes_order_and_names(self):
        print('\n[Phase4 C2] 多列 htypes 顺序与命名')
        values = np.array(
            [
                [[10.0, 1.0], [20.0, 2.0]],
                [[5.0, 3.0], [10.0, 6.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['a', 'b'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close', 'open'],
        )
        c = hp.cum_return(htypes=['close', 'open'], method='simple')
        n = hp.normalize(htypes=['close', 'open'], base_index=0)
        print('  cum htypes:', c.htypes)
        self.assertEqual(c.htypes, ['cumret_close', 'cumret_open'])
        self.assertEqual(n.htypes, ['norm_close', 'norm_open'])
        np.testing.assert_allclose(c.values[0, :, 0], [0.0, 1.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(c.values[0, :, 1], [0.0, 1.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(n.values[1, :, 1], [1.0, 2.0], rtol=0, atol=1e-12)

    def test_c3_aligns_with_returns_compound(self):
        print('\n[Phase4 C3] cum_return 与 returns 复利末值一致')
        p = np.array([[[1.0], [2.0], [4.0], [4.0], [8.0]]])
        hp = HistoryPanel(
            values=p,
            levels=['x'],
            rows=pd.date_range('2023-01-01', periods=5),
            columns=['close'],
        )
        ret = hp.returns(price_htype='close', method='simple', as_panel=False)
        r = ret['x'].values
        finite = r[np.isfinite(r)]
        prod_simple = np.prod(1.0 + finite) - 1.0
        cs = hp.cum_return(method='simple')
        print('  prod(1+r)-1:', prod_simple, 'cum last:', cs.values[0, -1, 0])
        self.assertAlmostEqual(cs.values[0, -1, 0], prod_simple, places=12)

        ret_log = hp.returns(price_htype='close', method='log', as_panel=False)
        rl = ret_log['x'].values
        sum_log = np.nansum(rl)
        cl = hp.cum_return(method='log')
        self.assertAlmostEqual(np.exp(cl.values[0, -1, 0]), np.exp(sum_log), places=12)
        self.assertAlmostEqual(np.exp(sum_log) - 1.0, prod_simple, places=12)

    def test_c4_adj_close_column_name_still_user_root(self):
        print('\n[Phase4 C4] 仅 close|b，列名为 cumret_close')
        values = np.array([[[100.0], [110.0]], [[50.0], [55.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['u', 'v'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close|b'],
        )
        cs = hp.cum_return()
        print('  htypes:', cs.htypes, 's0:', cs.values[0, :, 0])
        self.assertEqual(cs.htypes, ['cumret_close'])
        np.testing.assert_allclose(cs.values[0, :, 0], [0.0, 0.1], rtol=0, atol=1e-12)
        np.testing.assert_allclose(cs.values[1, :, 0], [0.0, 0.1], rtol=0, atol=1e-12)

    def test_c5_leading_nan_t0_shifted(self):
        print('\n[Phase4 C5] 首段 NaN，t0 后移')
        values = np.array([[[np.nan], [10.0], [11.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['s'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        cs = hp.cum_return(method='simple')
        print('  cum:', cs.values[0, :, 0])
        self.assertTrue(np.isnan(cs.values[0, 0, 0]))
        np.testing.assert_allclose(cs.values[0, 1:, 0], [0.0, 0.1], rtol=0, atol=1e-12)

    def test_c6_middle_nan_breaks_path(self):
        print('\n[Phase4 C6] 中间 NaN，断点及之后为 NaN')
        values = np.array([[[10.0], [np.nan], [12.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['s'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        cs = hp.cum_return(method='simple')
        print('  cum simple:', cs.values[0, :, 0])
        np.testing.assert_allclose(cs.values[0, 0, 0], 0.0, rtol=0, atol=1e-12)
        self.assertTrue(np.isnan(cs.values[0, 1, 0]))
        self.assertTrue(np.isnan(cs.values[0, 2, 0]))

    def test_c7_non_positive_breaks_path(self):
        print('\n[Phase4 C7] 非正价格，断点及之后 NaN')
        values = np.array([[[10.0], [5.0], [-1.0], [20.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['s'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'],
            columns=['close'],
        )
        cs = hp.cum_return(method='simple')
        print('  cum:', cs.values[0, :, 0])
        np.testing.assert_allclose(cs.values[0, 0, 0], 0.0, rtol=0, atol=1e-12)
        np.testing.assert_allclose(cs.values[0, 1, 0], -0.5, rtol=0, atol=1e-12)
        self.assertTrue(np.isnan(cs.values[0, 2, 0]))
        self.assertTrue(np.isnan(cs.values[0, 3, 0]))

    def test_c8_mask_with_where(self):
        print('\n[Phase4 C8] mask=hp.where(...)')
        values = np.array(
            [
                [[10.0], [11.0], [12.0]],
                [[1.0], [2.0], [3.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        m = hp.where(hp.values > 10.5)
        cs = hp.cum_return(mask=m, method='simple')
        print('  masked cum s0:', cs.values[0, :, 0])
        self.assertTrue(np.isnan(cs.values[0, 0, 0]))
        np.testing.assert_allclose(cs.values[0, 1, 0], 0.0, rtol=0, atol=1e-12)
        np.testing.assert_allclose(cs.values[0, 2, 0], 12.0 / 11.0 - 1.0, rtol=0, atol=1e-12)

    def test_c9_mask_all_false_column_all_nan(self):
        print('\n[Phase4 C9] 单列全 False mask')
        values = np.array([[[1.0], [2.0], [3.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['s'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        m = np.zeros((1, 3, 1), dtype=bool)
        cs = hp.cum_return(mask=m)
        print('  cum:', cs.values[0, :, 0])
        self.assertTrue(np.all(np.isnan(cs.values[0, :, 0])))

    def test_c10_normalize_base_index_and_masked_base(self):
        print('\n[Phase4 C10] normalize base_index 与基准被 mask')
        values = np.array([[[1.0], [2.0], [6.0], [3.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['s'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'],
            columns=['close'],
        )
        n = hp.normalize(base_index=2)
        print('  norm:', n.values[0, :, 0])
        np.testing.assert_allclose(
            n.values[0, :, 0],
            [1.0 / 6.0, 2.0 / 6.0, 1.0, 3.0 / 6.0],
            rtol=0,
            atol=1e-12,
        )
        m = np.ones((1, 4, 1), dtype=bool)
        m[0, 2, 0] = False
        n2 = hp.normalize(base_index=2, mask=m)
        self.assertTrue(np.all(np.isnan(n2.values[0, :, 0])))
        with self.assertRaises(ValueError):
            hp.normalize(base_index=10)

    def test_c11_empty_panel(self):
        print('\n[Phase4 C11] 空面板')
        empty = HistoryPanel()
        self.assertTrue(empty.cum_return().is_empty)
        self.assertTrue(empty.normalize().is_empty)

    def test_b1_invalid_method(self):
        print('\n[Phase4 B1] 非法 method')
        hp = HistoryPanel(
            values=np.array([[[1.0], [2.0]]]),
            levels=['s'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.cum_return(method='compound')

    def test_b2_mask_bad_shape(self):
        print('\n[Phase4 B2] mask 无法广播')
        hp = HistoryPanel(
            values=np.ones((2, 3, 1)),
            levels=['a', 'b'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        bad = np.zeros((2, 2), dtype=bool)
        with self.assertRaises(ValueError):
            hp.cum_return(mask=bad)

    def test_b3_unknown_htype(self):
        print('\n[Phase4 B3] 未知 htype')
        hp = HistoryPanel(
            values=np.ones((1, 2, 1)),
            levels=['s'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.cum_return(htypes='nope')

    def test_b4_single_bar(self):
        print('\n[Phase4 B4] L=1')
        hp = HistoryPanel(
            values=np.array([[[100.0]]]),
            levels=['s'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        cs = hp.cum_return(method='simple')
        cl = hp.cum_return(method='log')
        nz = hp.normalize(base_index=0)
        print('  cum simple:', cs.values[0, 0, 0])
        self.assertAlmostEqual(cs.values[0, 0, 0], 0.0)
        self.assertAlmostEqual(cl.values[0, 0, 0], 0.0)
        self.assertAlmostEqual(nz.values[0, 0, 0], 1.0)

    def test_b5_output_name_conflict(self):
        print('\n[Phase4 B5] 输出列名与已有列冲突')
        values = np.array([[[10.0, 0.0], [11.0, 0.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['s'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close', 'cumret_close'],
        )
        with self.assertRaises(ValueError) as ctx:
            hp.cum_return()
        self.assertIn('cumret_close', str(ctx.exception).lower())


class TestHistoryPanelPhase5Portfolio(unittest.TestCase):
    """阶段五：portfolio（研究向组合聚合，TDD）。"""

    def test_f1_equal_weight_two_shares(self):
        print('\n[Phase5 F1] 两 share 等权 close')
        values = np.array(
            [
                [[10.0], [12.0]],
                [[20.0], [16.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        out = hp.portfolio(htypes='close', mode='equal', benchmark_output='none')
        print('  out shape:', out.shape, 'shares:', out.shares, 'values:', out.values)
        self.assertEqual(out.shares, ['PORTFOLIO'])
        self.assertEqual(out.htypes, ['close'])
        self.assertEqual(out.shape, (1, 2, 1))
        np.testing.assert_allclose(out.values[0, :, 0], [15.0, 14.0], rtol=0, atol=1e-12)

    def test_f2_weighted_three_shares_normalize_true(self):
        print('\n[Phase5 F2] 三 share 加权 normalize_weights=True')
        values = np.array(
            [
                [[1.0], [2.0]],
                [[2.0], [4.0]],
                [[3.0], [6.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['s0', 's1', 's2'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        w = np.array([0.25, 0.25, 0.5])
        out = hp.portfolio(
            mode='weighted',
            weights=w,
            normalize_weights=True,
            benchmark_output='none',
        )
        exp0 = 0.25 * 1.0 + 0.25 * 2.0 + 0.5 * 3.0
        exp1 = 0.25 * 2.0 + 0.25 * 4.0 + 0.5 * 6.0
        print('  t0 t1:', out.values[0, :, 0])
        np.testing.assert_allclose(out.values[0, :, 0], [exp0, exp1], rtol=0, atol=1e-12)

    def test_f3_weighted_normalize_false_same_as_ratio(self):
        print('\n[Phase5 F3] 加权 normalize_weights=False 与 sum(wx)/sum(w)')
        values = np.array(
            [
                [[1.0]],
                [[2.0]],
                [[3.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['s0', 's1', 's2'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        w = np.array([1.0, 1.0, 2.0])
        out = hp.portfolio(
            mode='weighted',
            weights=w,
            normalize_weights=False,
            benchmark_output='none',
        )
        exp = (1.0 * 1.0 + 1.0 * 2.0 + 2.0 * 3.0) / (1.0 + 1.0 + 2.0)
        print('  exp:', exp, 'got:', out.values[0, 0, 0])
        self.assertAlmostEqual(out.values[0, 0, 0], exp, places=12)

    def test_f4_groups_two_rows_order(self):
        print('\n[Phase5 F4] groups 两组，键插入序')
        values = np.array(
            [
                [[10.0]],
                [[30.0]],
                [[50.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['a', 'b', 'c'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        groups = {'G2': ['c'], 'G1': ['a', 'b']}
        out = hp.portfolio(mode='equal', groups=groups, benchmark_output='none')
        print('  shares:', out.shares, 'vals:', out.values[:, 0, 0])
        self.assertEqual(out.shares, ['G2', 'G1'])
        np.testing.assert_allclose(out.values[0, 0, 0], 50.0, rtol=0, atol=1e-12)
        np.testing.assert_allclose(out.values[1, 0, 0], 20.0, rtol=0, atol=1e-12)

    def test_f5_close_b_resolve(self):
        print('\n[Phase5 F5] 仅 close|b')
        values = np.array([[[100.0], [110.0]], [[200.0], [220.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['x', 'y'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close|b'],
        )
        out = hp.portfolio(htypes='close', mode='equal', benchmark_output='none')
        self.assertEqual(out.htypes, ['close'])
        np.testing.assert_allclose(out.values[0, :, 0], [150.0, 165.0], rtol=0, atol=1e-12)

    def test_f6_multi_htypes(self):
        print('\n[Phase5 F6] close + open 两列')
        values = np.array(
            [
                [[1.0, 10.0], [3.0, 30.0]],
                [[5.0, 50.0], [7.0, 70.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close', 'open'],
        )
        out = hp.portfolio(htypes=['close', 'open'], mode='equal', benchmark_output='none')
        self.assertEqual(out.htypes, ['close', 'open'])
        np.testing.assert_allclose(out.values[0, 0, :], [3.0, 30.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(out.values[0, 1, :], [5.0, 50.0], rtol=0, atol=1e-12)

    def test_f7_benchmark_tag_along(self):
        print('\n[Phase5 F7] benchmark tag_along')
        values = np.array(
            [
                [[10.0], [20.0]],
                [[30.0], [40.0]],
                [[1000.0], [2000.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B', 'IDX'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        out = hp.portfolio(
            mode='equal',
            benchmark='IDX',
            benchmark_output='tag_along',
            new_share_name='EW',
        )
        print('  shares:', out.shares)
        self.assertEqual(out.shares, ['EW', 'IDX'])
        np.testing.assert_allclose(out.values[0, :, 0], [20.0, 30.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(out.values[1, :, 0], [1000.0, 2000.0], rtol=0, atol=1e-12)

    def test_f8_benchmark_excess_only(self):
        print('\n[Phase5 F8] benchmark excess_only')
        values = np.array(
            [
                [[10.0], [20.0]],
                [[30.0], [60.0]],
                [[100.0], [100.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B', 'BENCH'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        out = hp.portfolio(
            mode='equal',
            benchmark='BENCH',
            benchmark_output='excess_only',
            new_share_name='EW',
        )
        port = np.array([20.0, 40.0])
        bench = np.array([100.0, 100.0])
        self.assertEqual(out.shares, ['EW'])
        self.assertEqual(out.htypes, ['excess_close'])
        np.testing.assert_allclose(out.values[0, :, 0], port - bench, rtol=0, atol=1e-12)

    def test_b1_mask_drops_share_one_day(self):
        print('\n[Phase5 B1] mask 剔除某日一 share')
        values = np.array(
            [
                [[10.0], [12.0]],
                [[20.0], [16.0]],
            ]
        )
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        m = np.ones((2, 2, 1), dtype=bool)
        m[0, 1, 0] = False
        out = hp.portfolio(mode='equal', mask=m, benchmark_output='none')
        self.assertAlmostEqual(out.values[0, 0, 0], 15.0)
        self.assertAlmostEqual(out.values[0, 1, 0], 16.0)

    def test_b2_all_masked_nan(self):
        print('\n[Phase5 B2] 全日无有效成员 -> NaN')
        values = np.array([[[1.0]], [[2.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        m = np.zeros((2, 1, 1), dtype=bool)
        out = hp.portfolio(mode='equal', mask=m, benchmark_output='none')
        self.assertTrue(np.isnan(out.values[0, 0, 0]))

    def test_b3_groups_overlap_raises(self):
        print('\n[Phase5 B3] groups 重叠')
        hp = HistoryPanel(
            values=np.ones((2, 1, 1)),
            levels=['A', 'B'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        groups = {'G1': ['A', 'B'], 'G2': ['B']}
        with self.assertRaises(ValueError):
            hp.portfolio(mode='equal', groups=groups, benchmark_output='none')

    def test_b4_allow_ungrouped_error(self):
        print('\n[Phase5 B4] allow_ungrouped=error 漏 share')
        hp = HistoryPanel(
            values=np.ones((3, 1, 1)),
            levels=['A', 'B', 'C'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        groups = {'G1': ['A', 'B']}
        with self.assertRaises(ValueError):
            hp.portfolio(mode='equal', groups=groups, allow_ungrouped='error', benchmark_output='none')

    def test_b5_benchmark_not_in_shares(self):
        print('\n[Phase5 B5] benchmark 不存在')
        hp = HistoryPanel(
            values=np.ones((1, 1, 1)),
            levels=['A'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.portfolio(benchmark='Z', benchmark_output='tag_along')

    def test_b6_weights_bad_length(self):
        print('\n[Phase5 B6] weights 长度不等于 M')
        hp = HistoryPanel(
            values=np.ones((2, 1, 1)),
            levels=['A', 'B'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.portfolio(mode='weighted', weights=np.array([1.0]), benchmark_output='none')

    def test_b7_empty_panel(self):
        print('\n[Phase5 B7] 空面板')
        self.assertTrue(HistoryPanel().portfolio(benchmark_output='none').is_empty)

    def test_b8_empty_group_raises(self):
        print('\n[Phase5 B8] 空组')
        hp = HistoryPanel(
            values=np.ones((1, 1, 1)),
            levels=['A'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.portfolio(groups={'G': []}, benchmark_output='none')

    def test_b9_mask_bad_broadcast(self):
        print('\n[Phase5 B9] mask 形状错误')
        hp = HistoryPanel(
            values=np.ones((2, 3, 1)),
            levels=['A', 'B'],
            rows=['2023-01-01', '2023-01-02', '2023-01-03'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.portfolio(mask=np.zeros((2, 2), dtype=bool), benchmark_output='none')

    def test_mode_weight_mismatch(self):
        print('\n[Phase5] mode 与 weights 不一致')
        hp = HistoryPanel(
            values=np.ones((2, 1, 1)),
            levels=['A', 'B'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.portfolio(mode='equal', weights=np.array([0.5, 0.5]), benchmark_output='none')
        with self.assertRaises(ValueError):
            hp.portfolio(mode='weighted', benchmark_output='none')

    def test_benchmark_none_requires_output_none(self):
        print('\n[Phase5] 无 benchmark 时 benchmark_output 须为 none')
        hp = HistoryPanel(
            values=np.ones((2, 1, 1)),
            levels=['A', 'B'],
            rows=['2023-01-01'],
            columns=['close'],
        )
        with self.assertRaises(ValueError):
            hp.portfolio(mode='equal', benchmark_output='tag_along')

    def test_f9_mask_via_where(self):
        print('\n[Phase5 F9] mask=hp.where(...)')
        values = np.array([[[10.0], [12.0]], [[20.0], [16.0]]])
        hp = HistoryPanel(
            values=values,
            levels=['A', 'B'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['close'],
        )
        m = hp.where(hp.values >= 12.0)
        out = hp.portfolio(mode='equal', mask=m, benchmark_output='none')
        self.assertAlmostEqual(out.values[0, 0, 0], 20.0)
        self.assertAlmostEqual(out.values[0, 1, 0], 14.0)


if __name__ == '__main__':
    unittest.main()
