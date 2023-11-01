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

from qteasy.eastmoney import acquire_data, gen_eastmoney_code, get_k_history


class TestEastmoney(unittest.TestCase):
    """ Test eastmoney data acquiring functions and apis """

    def SetUp(self):
        pass

    def test_get_k_history(self):
        """ Test get_k_history function """
        code = '000001'
        res = get_k_history(code=code, beg='20231101', klt=60)
        print(res)
        self.assertIsInstance(res, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()
