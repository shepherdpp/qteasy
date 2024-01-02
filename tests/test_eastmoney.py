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

from qteasy.emfuncs import acquire_data, get_k_history


class TestEastmoney(unittest.TestCase):
    """ Test eastmoney data acquiring functions and apis """

    def SetUp(self):
        pass

    def test_get_k_history(self):
        """ Test get_k_history function """
        code = '000651'
        res = get_k_history(code=code, beg='20231102', klt=5)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        code = '000651'
        res = get_k_history(code=code, beg='20231102', klt=101, verbose=True)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        code = '000651.SZ'
        res = get_k_history(code=code, beg='20231102', klt=101, verbose=True)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        code = '000001.SH'
        res = get_k_history(code=code, beg='20231102', klt=101, verbose=True)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)

    def test_stock_live_daily_price(self):
        """ Test stock_live_kline_price function """

        code = ['000016.SZ', '000025.SZ', '000333.SZ']
        res = acquire_data('stock_live_kline_price', symbols=code, freq='D')
        print(f'data acquied for codes [\'000016.SZ\', \'000025.SZ\', \'000333.SZ\']: {res}')
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)
        self.assertEqual(res.columns.to_list(), ['symbol', 'open', 'close', 'high', 'low', 'vol', 'amount'])
        self.assertEqual(res.index.name, 'trade_time')
        self.assertTrue(all(item in code for item in res.symbol))
        # some items may not have real time price at the moment
        # self.assertTrue(all(item in res.symbol.to_list() for item in code))

        code = ['000016.SZ', '000025.SZ', '000333.SZ']
        res = acquire_data('stock_live_kline_price', symbols=code, freq='D', verbose=True)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)

        code = ['000016.SZ', '000025.SZ', '000333.SZ', '000404.SZ', '000428.SZ', '000521.SZ', '000541.SZ', '000550.SZ',
                '000572.SZ', '000625.SZ', '000651.SZ', '000721.SZ', '000753.SZ', '000757.SZ', '000800.SZ', '000801.SZ',
                '000810.SZ', '000868.SZ', '000921.SZ', '000951.SZ', '000957.SZ', '000996.SZ', '001259.SZ', '002005.SZ',
                '002011.SZ', '002032.SZ', '002035.SZ', '002050.SZ', '002076.SZ', '002186.SZ', '002242.SZ', '002290.SZ',
                '002403.SZ', '002418.SZ', '002420.SZ', '002429.SZ', '002508.SZ', '002543.SZ', '002594.SZ', '002614.SZ',
                '002668.SZ', '002676.SZ', '002677.SZ', '002705.SZ', '002723.SZ', '002758.SZ', '002759.SZ', '002848.SZ',
                '002860.SZ', '002959.SZ', '003023.SZ', '300100.SZ', '300160.SZ', '300217.SZ', '300272.SZ', '300342.SZ',
                '300403.SZ', '300625.SZ', '300808.SZ', '300824.SZ', '300825.SZ', '300894.SZ', '300911.SZ', '301008.SZ',
                '301039.SZ', '301073.SZ', '301187.SZ', '301215.SZ', '301332.SZ', '301525.SZ', '600006.SH', '600060.SH',
                '600066.SH', '600099.SH', '600104.SH', '600166.SH', '600213.SH', '600258.SH', '600261.SH', '600297.SH',
                '600303.SH', '600335.SH', '600336.SH', '600375.SH', '600386.SH', '600418.SH', '600619.SH', '600653.SH',
                '600686.SH', '600690.SH', '600733.SH', '600754.SH', '600822.SH', '600839.SH', '600854.SH', '600983.SH',
                '601007.SH', '601127.SH', '601238.SH', '601258.SH', '601633.SH', '601956.SH', '601965.SH', '603195.SH',
                '603215.SH', '603219.SH', '603303.SH', '603311.SH', '603355.SH', '603366.SH', '603377.SH', '603486.SH',
                '603515.SH', '603519.SH', '603579.SH', '603657.SH', '603677.SH', '603726.SH', '603868.SH', '605108.SH',
                '605336.SH', '605365.SH', '605555.SH', '688169.SH', '688609.SH', '688696.SH', '688793.SH']
        res = acquire_data('stock_live_kline_price', symbols=code, freq='M')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)
        self.assertEqual(res.columns.to_list(), ['symbol', 'open', 'close', 'high', 'low', 'vol', 'amount'])
        self.assertEqual(res.index.name, 'trade_time')
        self.assertTrue(all(item in code for item in res.symbol))
        # some items may not have real time price at the moment
        # self.assertTrue(all(item in res.symbol.to_list() for item in code))

        print('test acquiring Index prices')
        codes = ['000001.SH', '000300.SH', '399001.SZ']
        res = acquire_data('stock_live_kline_price', symbols=codes, freq='D')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)
        self.assertEqual(res.columns.to_list(), ['symbol', 'open', 'close', 'high', 'low', 'vol', 'amount'])
        self.assertEqual(res.index.name, 'trade_time')
        self.assertTrue(all(item in codes for item in res.symbol))
        # some items may not have real time price at the moment
        # self.assertTrue(all(item in res.symbol.to_list() for item in code))

        print('test acquiring ETF price data')
        codes = ['510050.SH', '510300.SH', '510500.SH', '510880.SH', '510900.SH', '512000.SH', '512010.SH']
        res = acquire_data('stock_live_kline_price', symbols=codes, freq='D')
        print(res)
        self.assertIsInstance(res, pd.DataFrame)
        self.assertFalse(res.empty)
        self.assertEqual(res.columns.to_list(), ['symbol', 'open', 'close', 'high', 'low', 'vol', 'amount'])
        self.assertEqual(res.index.name, 'trade_time')
        self.assertTrue(all(item in codes for item in res.symbol))
        # some items may not have real time price at the moment
        # self.assertTrue(all(item in res.symbol.to_list() for item in code))


if __name__ == '__main__':
    unittest.main()
