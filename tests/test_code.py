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
    def test_class(self):
        code = 'SZ.000001'
        qt_code = QtCode(code)

        print(qt_code)
        print(qt_code == '000001.SZ')
        self.assertIsInstance(qt_code, QtCode)
        self.assertIsInstance(qt_code, str)

        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000001'
        qt_code = QtCode(code)
        print(qt_code)
        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '000001.SH'
        qt_code = QtCode(code)
        print(qt_code)
        self.assertEqual(qt_code, '000001.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'IDX')

        code = '600001'
        qt_code = QtCode(code)
        print(qt_code)
        self.assertEqual(qt_code, '600001.SH')
        self.assertEqual(qt_code.market, 'SH')
        self.assertEqual(qt_code.symbol, '600001')
        self.assertEqual(qt_code.asset_type, 'E')

        code = '0045'
        qt_code = QtCode(code)
        print(qt_code)
        self.assertEqual(qt_code, '0045.HK')
        self.assertEqual(qt_code.market, 'HK')
        self.assertEqual(qt_code.symbol, '0045')
        self.assertEqual(qt_code.asset_type, 'E')

        code = 'MSFT'
        qt_code = QtCode(code)
        print(qt_code)
        self.assertEqual(qt_code, 'MSFT.US')
        self.assertEqual(qt_code.market, 'US')
        self.assertEqual(qt_code.symbol, 'MSFT')
        self.assertEqual(qt_code.asset_type, 'E')

        code = 'AAPL'
        qt_code = QtCode(code)
        print(qt_code)
        self.assertEqual(qt_code, 'AAPL.US')
        self.assertEqual(qt_code.market, 'US')
        self.assertEqual(qt_code.symbol, 'AAPL')
        self.assertEqual(qt_code.asset_type, 'E')


if __name__ == '__main__':
    unittest.main()
