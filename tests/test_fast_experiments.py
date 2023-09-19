# coding=utf-8
# ======================================
# File:     test_fast_experiments.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Temporary test file for quick
#   function tests.
# ======================================
import unittest

import qteasy as qt


class FastExperiments(unittest.TestCase):
    """This test case is created to have experiments done that can be quickly called from Command line"""

    def setUp(self):
        pass

    def test_fast_experiments(self):
        """temp test"""
        stocks = qt.filter_stock_codes(index='000300.SH', date='20150101')  # [0:90]
        # op = qt.Operator(strategies='dma')
        # op.set_parameter('dma', pars=(23, 166, 196))
        # res = qt.run(op, mode=1, invest_start='20160501', visual=True, trade_log=True)


if __name__ == '__main__':
    unittest.main()