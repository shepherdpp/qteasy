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

        self.assertEqual(qt_code, '000001.SZ')
        self.assertEqual(qt_code.market, 'SZ')
        self.assertEqual(qt_code.symbol, '000001')
        self.assertEqual(qt_code.asset_type, 'E')


if __name__ == '__main__':
    unittest.main()
