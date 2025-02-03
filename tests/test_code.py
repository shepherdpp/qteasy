# coding=utf-8
# ======================================
# File:     test_code.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-10-20
# Desc:
#   Unittest for qt_code class.
# ======================================


import unittest
from qteasy.qt_code import QtCode


class TestCode(unittest.TestCase):
    def test_class_code(self):
        """ testing create class with only code"""
        code = 'SZ.000001'
        qt_code = QtCode(code)

        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertIsInstance(qt_code, QtCode)
        # self.assertIsInstance(qt_code, str)

        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000001'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000001.SH'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'IDX')

        code = '600001'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '600001.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '600001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '00451'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '00451.HK')
        self.assertEqual(qt_code.market, 'HK')
        self.assertEqual(qt_code.symbol, '00451')
        self.assertEqual(qt_code.asset_type, 'E')

        code = 'MSFT'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, 'MSFT.US')
        self.assertEqual(qt_code.market, 'US')
        self.assertEqual(qt_code.symbol, 'MSFT')
        self.assertEqual(qt_code.asset_type, 'E')

        code = 'AAPL'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, 'AAPL.US')
        self.assertEqual(qt_code.market, 'US')
        self.assertEqual(qt_code.symbol, 'AAPL')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000651'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000651.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000651')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '550300'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '550300.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '550300')
        self.assertEqual(qt_code.asset_type, 'FD')

        code = 'A0001'  # Futures
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, 'A0001.DCE')
        self.assertEqual(qt_code.market, 'DCE')
        self.assertEqual(qt_code.symbol, 'A0001')
        self.assertEqual(qt_code.asset_type, 'FT')

        code = '10001909'  # Options
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '10001909.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '10001909')
        self.assertEqual(qt_code.asset_type, 'OPT')

        code = '960032'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '960032.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '960032')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '960032.OF'
        qt_code = QtCode(code)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '960032.OF')
        self.assertEqual(qt_code.market, 'OF')
        self.assertEqual(qt_code.symbol, '960032')
        self.assertEqual(qt_code.asset_type, 'FD')

    def test_class(self):
        """ test creating class with more than code"""
        code = '000001'
        market = 'SZ'
        qt_code = QtCode(code, market=market)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000001'
        market = 'SH'
        qt_code = QtCode(code, market=market)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'IDX')

        code = '000001'
        asset_type = 'E'
        qt_code = QtCode(code, asset_type=asset_type)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000001'
        asset_type = 'IDX'
        qt_code = QtCode(code, asset_type=asset_type)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SZ') # default like this but it is wrong
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'IDX')

        code = '000001'
        market = 'SH'
        qt_code = QtCode(code, market=market)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '000001.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'IDX')

        code = '00001'
        market = 'HK'
        asset_type = 'E'
        qt_code = QtCode(code, market=market, asset_type=asset_type)
        print(qt_code, qt_code.market, qt_code.symbol, qt_code.asset_type)
        self.assertEqual(qt_code, '00001.HK')
        self.assertEqual(qt_code.market, 'HK')
        self.assertEqual(qt_code.symbol, '00001')
        self.assertEqual(qt_code.asset_type, 'E')

    def test_methods(self):
        """ test methods of the class"""
        qt_code = QtCode('000001.SZ')
        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        self.assertEqual(len(qt_code), 9)
        self.assertEqual(qt_code.market_name, 'Shenzhen')
        self.assertEqual(qt_code == '000001.SZ', True)
        self.assertEqual(qt_code == '000001.SH', False)
        self.assertEqual(qt_code.lower(), '000001.sz')
        self.assertEqual(qt_code.upper(), '000001.SZ')
        self.assertEqual(qt_code.title(), '000001.Sz')
        self.assertEqual(qt_code[0], '0')
        self.assertEqual(qt_code[-1], 'Z')
        self.assertEqual(qt_code[1:4], '000')

        qt_code2 = QtCode('000001.SZ')
        self.assertEqual(qt_code == qt_code2, True)
        self.assertEqual(qt_code != qt_code2, False)
        self.assertEqual(qt_code.__hash__(), hash('000001.SZ'))
        self.assertEqual(qt_code.__ne__('000001.SZ'), False)
        self.assertEqual(qt_code.__lt__('000001.SZ'), False)
        self.assertEqual(qt_code.__repr__(), '000001.SZ')
        self.assertEqual(qt_code.__str__(), '000001.SZ')
        self.assertEqual(qt_code + qt_code2, '000001.SZ000001.SZ')
        self.assertEqual(qt_code * 2, '000001.SZ000001.SZ')
        self.assertEqual(qt_code * 0, '')

        for i in qt_code:
            print(i)
            self.assertIsInstance(i, str)
            self.assertIn(i, qt_code)
            idx = qt_code.index(i)
            self.assertTrue(i == qt_code[idx])


if __name__ == '__main__':
    unittest.main()
