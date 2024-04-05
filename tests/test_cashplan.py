# coding=utf-8
# ======================================
# File:     test_cashplan.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all cash plan module
#   related functions.
# ======================================
import unittest

import qteasy as qt
import pandas as pd
from pandas import Timestamp

from qteasy import CashPlan


class TestCashPlan(unittest.TestCase):
    def setUp(self):
        self.cp1 = qt.CashPlan(['2012-01-01', '2010-01-01'], [10000, 20000], 0.1)
        self.cp1.info()
        self.cp2 = qt.CashPlan(['20100501'], 10000)
        self.cp2.info()
        self.cp3 = qt.CashPlan(pd.date_range(start='2019-01-01',
                                             freq='Y',
                                             periods=12),
                               [i * 1000 + 10000 for i in range(12)],
                               0.035)
        self.cp3.info()

    def test_creation(self):
        self.assertIsInstance(self.cp1, qt.CashPlan, 'CashPlan object creation wrong')
        self.assertIsInstance(self.cp2, qt.CashPlan, 'CashPlan object creation wrong')
        self.assertIsInstance(self.cp3, qt.CashPlan, 'CashPlan object creation wrong')
        # test __repr__()
        print(self.cp1)
        print(self.cp2)
        print(self.cp3)
        # test __str__()
        self.cp1.info()
        self.cp2.info()
        self.cp3.info()
        # test assersion errors
        self.assertRaises(ValueError, qt.CashPlan, '2016-01-01', [10000, 10000])
        self.assertRaises(TypeError, qt.CashPlan, '', '')
        self.assertRaises(ValueError, qt.CashPlan, '', [])
        self.assertRaises(KeyError, qt.CashPlan, '2020-20-20', 10000)
        # test empty cash plan
        empty = CashPlan([], [])
        print(empty)

    def test_properties(self):
        self.assertEqual(self.cp1.amounts, [20000, 10000], 'property wrong')
        self.assertEqual(self.cp1.first_day, Timestamp('2010-01-01'))
        self.assertEqual(self.cp1.last_day, Timestamp('2012-01-01'))
        self.assertEqual(self.cp1.investment_count, 2)
        self.assertEqual(self.cp1.period, 730)
        self.assertEqual(self.cp1.dates, [Timestamp('2010-01-01'), Timestamp('2012-01-01')])
        self.assertEqual(self.cp1.ir, 0.1)
        self.assertAlmostEqual(self.cp1.closing_value, 34200)
        self.assertAlmostEqual(self.cp2.closing_value, 10000)
        self.assertAlmostEqual(self.cp3.closing_value, 220385.35)
        self.assertIsInstance(self.cp1.plan, pd.DataFrame)
        self.assertIsInstance(self.cp2.plan, pd.DataFrame)
        self.assertIsInstance(self.cp3.plan, pd.DataFrame)
        # test empty cash plan
        empty = CashPlan([], [])
        self.assertEqual(empty.amounts, [], 'property wrong')
        self.assertEqual(empty.first_day, None)
        self.assertEqual(empty.last_day, None)
        self.assertEqual(empty.investment_count, 0)
        self.assertEqual(empty.total, 0)
        self.assertEqual(empty.period, 0)
        self.assertEqual(empty.dates, [])
        self.assertEqual(empty.ir, 0.0)
        self.assertAlmostEqual(empty.closing_value, 0)
        self.assertAlmostEqual(empty.opening_value, 0)
        self.assertIsInstance(empty.plan, pd.DataFrame)
        self.assertTrue(empty.plan.empty)

    def test_operation(self):
        cp_self_add = self.cp1 + self.cp1
        cp_add = self.cp1 + self.cp2
        cp_add_int = self.cp1 + 10000
        cp_mul_int = self.cp1 * 2
        cp_mul_float = self.cp2 * 1.5
        cp_mul_time = 3 * self.cp2
        cp_mul_time2 = 2 * self.cp1
        cp_mul_time3 = 2 * self.cp3
        cp_mul_float2 = 2. * self.cp3
        self.assertIsInstance(cp_self_add, qt.CashPlan)
        self.assertEqual(cp_self_add.amounts, [40000, 20000])
        self.assertEqual(cp_add.amounts, [20000, 10000, 10000])
        self.assertEqual(cp_add_int.amounts, [30000, 20000])
        self.assertEqual(cp_mul_int.amounts, [40000, 20000])
        self.assertEqual(cp_mul_float.amounts, [15000])
        self.assertEqual(cp_mul_float.dates, [Timestamp('2010-05-01')])
        self.assertEqual(cp_mul_time.amounts, [10000, 10000, 10000])
        self.assertEqual(cp_mul_time.dates, [Timestamp('2010-05-01'),
                                             Timestamp('2011-05-01'),
                                             Timestamp('2012-04-30')])
        self.assertEqual(cp_mul_time2.amounts, [20000, 10000, 20000, 10000])
        self.assertEqual(cp_mul_time2.dates, [Timestamp('2010-01-01'),
                                              Timestamp('2012-01-01'),
                                              Timestamp('2014-01-01'),
                                              Timestamp('2016-01-01')])
        self.assertEqual(cp_mul_time3.dates, [Timestamp('2019-12-31'),
                                              Timestamp('2020-12-31'),
                                              Timestamp('2021-12-31'),
                                              Timestamp('2022-12-31'),
                                              Timestamp('2023-12-31'),
                                              Timestamp('2024-12-31'),
                                              Timestamp('2025-12-31'),
                                              Timestamp('2026-12-31'),
                                              Timestamp('2027-12-31'),
                                              Timestamp('2028-12-31'),
                                              Timestamp('2029-12-31'),
                                              Timestamp('2030-12-31'),
                                              Timestamp('2031-12-29'),
                                              Timestamp('2032-12-29'),
                                              Timestamp('2033-12-29'),
                                              Timestamp('2034-12-29'),
                                              Timestamp('2035-12-29'),
                                              Timestamp('2036-12-29'),
                                              Timestamp('2037-12-29'),
                                              Timestamp('2038-12-29'),
                                              Timestamp('2039-12-29'),
                                              Timestamp('2040-12-29'),
                                              Timestamp('2041-12-29'),
                                              Timestamp('2042-12-29')])
        self.assertEqual(cp_mul_float2.dates, [Timestamp('2019-12-31'),
                                               Timestamp('2020-12-31'),
                                               Timestamp('2021-12-31'),
                                               Timestamp('2022-12-31'),
                                               Timestamp('2023-12-31'),
                                               Timestamp('2024-12-31'),
                                               Timestamp('2025-12-31'),
                                               Timestamp('2026-12-31'),
                                               Timestamp('2027-12-31'),
                                               Timestamp('2028-12-31'),
                                               Timestamp('2029-12-31'),
                                               Timestamp('2030-12-31')])
        self.assertEqual(cp_mul_float2.amounts, [20000.0,
                                                 22000.0,
                                                 24000.0,
                                                 26000.0,
                                                 28000.0,
                                                 30000.0,
                                                 32000.0,
                                                 34000.0,
                                                 36000.0,
                                                 38000.0,
                                                 40000.0,
                                                 42000.0])


if __name__ == '__main__':
    unittest.main()
    