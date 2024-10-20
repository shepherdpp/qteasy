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
        code = '000001.SH'
        qt_code = QtCode(code)
        code = '600001'
        qt_code = QtCode(code)
        code = '0045'
        qt_code = QtCode(code)
        code = 'MSFT'
        qt_code = QtCode(code)
        code = 'AAPL'
        qt_code = QtCode(code)

if __name__ == '__main__':
    unittest.main()
