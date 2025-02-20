# coding=utf-8
# ======================================
# File:     test_eastmoney.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-11-01
# Desc:
#   Unittest for all eastmoney data
# acquiring functions and apis.
# ======================================

import unittest

import pandas as pd
import numpy as np

from qteasy.emfuncs import (
    stock_daily,
    stock_weekly,
    stock_1min,
    _stock_bars,
    real_time_klines,
    real_time_quote,
)
from qteasy.utilfuncs import is_market_trade_day


class TestEastmoney(unittest.TestCase):
    """ Test eastmoney data acquiring functions and apis """

    def SetUp(self):
        pass

    def test_get_k_history(self):
        """ Test _get_k_history function """
        code = '000651'
        date = (pd.to_datetime('today') - pd.Timedelta(days=3)).strftime('%Y%m%d')  # 最多只能获取过去10个交易日的5分钟K线
        end = pd.to_datetime('today').strftime('%Y%m%d')
        res = _stock_bars(qt_code=code, start=date, end=end, freq='5min')
        print(res)

        self.assertIsInstance(res, pd.DataFrame)
        if is_market_trade_day(end):
            self.assertFalse(res.empty)
        else:
            self.assertTrue(res.empty)
        code = '000651'
        res = stock_daily(qt_code=code, start='20231102', end='20240301')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)
        self.assertTrue(np.all(res.close == res.pre_close + res.change))
        self.assertTrue(np.all(np.abs(res.pct_chg - (res.change / res.pre_close) * 100) < 0.01))
        code = '000651.SZ'
        res = stock_weekly(qt_code=code, start='20231102', end='20240301')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)
        code = '000001.SH'
        res = stock_1min(qt_code=code, start='20231102', end='20240301')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)

    def test_real_time_kline_price(self):
        """ Test real_time_klines function """

        code = '000016.SZ'
        date = '20241227'
        res = real_time_klines(qt_code=code, freq='D', date=date)
        print(f'data acquied for code \'000016.SZ\': {res}')
        self.assertIsInstance(res, pd.DataFrame)
        from qteasy.utilfuncs import is_market_trade_day
        if is_market_trade_day(date):
            self.assertFalse(res.empty)
            self.assertEqual(len(res), 2)
            self.assertEqual(res.columns.to_list(),
                             ['symbol', 'name', 'pre_close', 'open', 'close', 'high', 'low', 'vol', 'amount'])
            self.assertEqual(res.index.name, 'trade_date')
            self.assertTrue(all(item in code for item in res.symbol))
            # some items may not have real time price at the moment
            # self.assertTrue(all(item in res.symbol.to_list() for item in code))
        else:
            print(f'not a trade day, no real time k-line data acquired!')
            self.assertTrue(res.empty)

        code = '000025.SZ'
        date = '20241231'
        res = real_time_klines(qt_code=code, date=date, freq='D')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)

        code = '000016.SZ'
        date = (pd.to_datetime('today') - pd.Timedelta(days=3)).strftime('%Y%m%d')  # 最多只能获取过去10个交易日的5分钟K线
        res = real_time_klines(qt_code=code, date=date, freq='5min')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        if is_market_trade_day(date):
            self.assertFalse(res.empty)
            self.assertEqual(res.columns.to_list(), ['symbol', 'name', 'pre_close', 'open', 'close',
                                                     'high', 'low', 'vol', 'amount'])
            self.assertEqual(res.index.name, 'trade_time')
            self.assertTrue(all(item in code for item in res.symbol))
            # some items may not have real time price at the moment
            # self.assertTrue(all(item in res.symbol.to_list() for item in code))
        else:
            print(f'not a trade day, no real time k-line data acquired!')
            self.assertTrue(res.empty)

        print('test acquiring Index prices')
        codes = '399001.SZ'
        date = (pd.to_datetime('today')).strftime('%Y%m%d')  # 最多只能今天交易日的1分钟K线
        res = real_time_klines(qt_code=codes, date=date, freq='1min')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        if is_market_trade_day(date):
            self.assertFalse(res.empty)
            self.assertEqual(res.columns.to_list(), ['symbol', 'name', 'pre_close', 'open', 'close',
                                                     'high', 'low', 'vol', 'amount'])
            self.assertEqual(res.index.name, 'trade_time')
            self.assertTrue(all(item in codes for item in res.symbol))
            # some items may not have real time price at the moment
            # self.assertTrue(all(item in res.symbol.to_list() for item in code))
        else:
            print(f'not a trade day, no real time k-line data acquired!')
            self.assertTrue(res.empty)

        print('test acquiring ETF price data')
        codes = '510300.SH'
        date = (pd.to_datetime('today') - pd.Timedelta(days=3)).strftime('%Y%m%d')  # 最多只能获取过去10个交易日的60分钟K线
        res = real_time_klines(qt_code=codes, date=date, freq='h')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        if is_market_trade_day(date):
            self.assertFalse(res.empty)
            self.assertEqual(res.columns.to_list(), ['symbol', 'name', 'pre_close', 'open', 'close',
                                                     'high', 'low', 'vol', 'amount'])
            self.assertEqual(res.index.name, 'trade_time')
            self.assertTrue(all(item in codes for item in res.symbol))
            # some items may not have real time price at the moment
            # self.assertTrue(all(item in res.symbol.to_list() for item in code))
        else:
            print(f'not a trade day, no real time k-line data acquired!')
            self.assertTrue(res.empty)

    def test_real_time_quote(self):
        """ testing function get real time quote"""
        code = '399001.SZ'
        res = real_time_quote(qt_code=code)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()
