import unittest
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np
from numpy import int64
import itertools
import datetime


class TestCost(unittest.TestCase):
    def setUp(self):
        self.amounts = np.array([10000, 20000, 10000])
        self.op = np.array([0, 1, -1])
        self.prices = np.array([10, 20, 10])
        self.r = qt.Cost()

    def test_rate_creation(self):
        print('testing rates objects\n')
        self.assertIsInstance(self.r, qt.Cost, 'Type should be Rate')

    def test_rate_operations(self):
        self.assertEqual(self.r['buy_fix'], 0.0, 'Item got is incorrect')
        self.assertEqual(self.r['sell_fix'], 0.0, 'Item got is wrong')
        self.assertEqual(self.r['buy_rate'], 0.003, 'Item got is incorrect')
        self.assertEqual(self.r['sell_rate'], 0.001, 'Item got is incorrect')
        self.assertEqual(self.r['buy_min'], 5., 'Item got is incorrect')
        self.assertEqual(self.r['sell_min'], 0.0, 'Item got is incorrect')
        self.assertEqual(self.r['slipage'], 0.0, 'Item got is incorrect')
        self.assertEqual(np.allclose(self.r(self.amounts), [0.003, 0.003, 0.003]), True, 'fee calculation wrong')

    def test_rate_fee(self):
        self.r.buy_rate = 0.003
        self.r.sell_rate = 0.001
        print('Sell result with fixed rate = 0.001:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0, 0, -10000]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 99900.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], -100.0, msg='result incorrect')
        print('Purchase result with fixed rate = 0.003 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        print('Purchase result with fixed rate = 0.003 and moq = 1:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 1))
        print('Purchase result with fixed rate = 0.003 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))

        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997.00897308, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 59.82053838484547, msg='result incorrect')

        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 1)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -19999.819999999996, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 59.82, msg='result incorrect')

        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -18053.999999999996, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 54.0, msg='result incorrect')

    def test_min_fee(self):
        self.r.sell_fix = 0
        self.r.buy_fix = 0
        self.r.buy_min = 300
        self.r.sell_min = 300
        self.r.slipage = 0
        print('purchase result with fixed cost rate with min fee = 300:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 985, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('selling result with fixed cost rate with min fee = 300:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -10000]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 99700.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], -300.0, msg='result incorrect')

    def test_fixed_fee(self):
        self.r.buy_fix = 200
        self.r.sell_fix = 150
        print('purchase result of fixed cost with fixed fee = 200/150:\n')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -10000]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], 99850.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], -150.0, msg='result incorrect')

        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 990., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 200.0, msg='result incorrect')

        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -18200.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 200.0, msg='result incorrect')

    def test_slipage(self):
        self.r.buy_fix = 0
        self.r.sell_fix = 0
        self.r.buy_min = 0
        self.r.sell_min = 0
        self.r.buy_rate = 0.003
        self.r.sell_rate = 0.001
        self.r.slipage = 1E-9
        print('purchase result of fixed rate = 0.003 and slipage = 1E-10 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        print('purchase result of fixed rate = 0.003 and slipage = 1E-10 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))
        print('selling result with fixed rate = 0.001 and slipage = 1E-10:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))

        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -10000]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], 99890.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], -110.0, msg='result incorrect')

        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 996.98909294, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 60.21814121353513, msg='result incorrect')

        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -18054.36, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 54.36, msg='result incorrect')


class TestSpace(unittest.TestCase):
    def test_creation(self):
        """
            test if creation of space object is fine
        """
        # first group of inputs, output Space with two discr axis from [0,10]
        print('testing space objects\n')
        # pars_list = [[(0, 10), (0, 10)],
        #              [[0, 10], [0, 10]]]
        #
        # types_list = ['discr',
        #               ['discr', 'discr']]
        #
        # input_pars = itertools.product(pars_list, types_list)
        # for p in input_pars:
        #     # print(p)
        #     s = qt.Space(*p)
        #     b = s.boes
        #     t = s.types
        #     # print(s, t)
        #     self.assertIsInstance(s, qt.Space)
        #     self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
        #     self.assertEqual(t, ['discr', 'discr'], 'types incorrect')
        #
        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['foo, bar',
                      ['foo', 'bar']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            # print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            # print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['enum', 'enum'], 'types incorrect')

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = [['discr', 'foobar']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            # print(p)
            s = qt.Space(*p)
            b = s.boes
            t = s.types
            # print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'enum'], 'types incorrect')

        pars_list = [(0., 10), (0, 10)]
        s = qt.Space(pars=pars_list, par_types=None)
        self.assertEqual(s.types, ['conti', 'discr'])
        #
        pars_list = [(0., 10), (0, 10)]
        s = qt.Space(pars=pars_list, par_types='conti, enum')
        self.assertEqual(s.types, ['conti', 'enum'])

    def test_extract(self):
        """

        :return:
        """
        pars_list = [(0, 10), (0, 10)]
        types_list = ['discr', 'discr']
        s = qt.Space(pars=pars_list, par_types=types_list)
        extracted_int, count = s.extract(3, 'interval')
        extracted_int_list = list(extracted_int)
        print('extracted int\n', extracted_int_list)
        self.assertEqual(count, 16, 'extraction count wrong!')
        self.assertEqual(extracted_int_list, [(0, 0), (0, 3), (0, 6), (0, 9), (3, 0), (3, 3),
                                              (3, 6), (3, 9), (6, 0), (6, 3), (6, 6), (6, 9),
                                              (9, 0), (9, 3), (9, 6), (9, 9)],
                         'space extraction wrong!')
        extracted_rand, count = s.extract(10, 'rand')
        extracted_rand_list = list(extracted_rand)
        self.assertEqual(count, 10, 'extraction count wrong!')
        print('extracted rand\n', extracted_rand_list)
        for point in list(extracted_rand_list):
            self.assertEqual(len(point), 2)
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertLessEqual(point[1], 10)
            self.assertGreaterEqual(point[1], 0)

        pars_list = [(0., 10), (0, 10)]
        s = qt.Space(pars=pars_list, par_types=None)
        extracted_int2, count = s.extract(3, 'interval')
        self.assertEqual(count, 16, 'extraction count wrong!')
        extracted_int_list2 = list(extracted_int2)
        self.assertEqual(extracted_int_list2, [(0, 0), (0, 3), (0, 6), (0, 9), (3, 0), (3, 3),
                                               (3, 6), (3, 9), (6, 0), (6, 3), (6, 6), (6, 9),
                                               (9, 0), (9, 3), (9, 6), (9, 9)],
                         'space extraction wrong!')
        print('extracted int list 2\n', extracted_int_list2)
        self.assertIsInstance(extracted_int_list2[0][0], float)
        self.assertIsInstance(extracted_int_list2[0][1], (int, int64))
        extracted_rand2, count = s.extract(10, 'rand')
        self.assertEqual(count, 10, 'extraction count wrong!')
        extracted_rand_list2 = list(extracted_rand2)
        print('extracted rand list 2:\n', extracted_rand_list2)
        for point in extracted_rand_list2:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], float)
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertIsInstance(point[1], (int, int64))
            self.assertLessEqual(point[1], 10)
            self.assertGreaterEqual(point[1], 0)

        pars_list = [(0., 10), ('a', 'b')]
        s = qt.Space(pars=pars_list, par_types='enum, enum')
        extracted_int3, count = s.extract(1, 'interval')
        self.assertEqual(count, 4, 'extraction count wrong!')
        extracted_int_list3 = list(extracted_int3)
        self.assertEqual(extracted_int_list3, [(0., 'a'), (0, 'b'), (10., 'a'), (10., 'b')],
                         'space extraction wrong!')
        print('extracted int list 2\n', extracted_int_list3)
        self.assertIsInstance(extracted_int_list3[0][0], float)
        self.assertIsInstance(extracted_int_list3[0][1], str)
        extracted_rand3, count = s.extract(3, 'rand')
        self.assertEqual(count, 3, 'extraction count wrong!')
        extracted_rand_list3 = list(extracted_rand3)
        print('extracted rand list 2:\n', extracted_rand_list3)
        for point in extracted_rand_list3:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], float)
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertIsInstance(point[1], str)
            self.assertIn(point[1], ['a', 'b'])


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
        self.cp1
        self.cp2
        self.cp3
        # test __str__()
        self.cp1.info()
        self.cp2.info()
        self.cp3.info()
        # test assersion errors
        self.assertRaises(AssertionError, qt.CashPlan, '2016-01-01', [10000, 10000])
        self.assertRaises(KeyError, qt.CashPlan, '2020-20-20', 10000)

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
        self.assertAlmostEqual(self.cp3.closing_value, 220385.3483685)

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


class TestPool(unittest.TestCase):
    def setUp(self):
        self.p = qt.ResultPool(5)
        self.items = ['first', 'second', (1, 2, 3), 'this', 24]
        self.perfs = [1, 2, 3, 4, 5]
        self.additional_result1 = ('abc', 12)
        self.additional_result2 = ([1, 2], -1)
        self.additional_result3 = (12, 5)

    def test_create(self):
        self.assertIsInstance(self.p, qt.ResultPool)

    def test_operation(self):
        self.p.in_pool(self.additional_result1[0], self.additional_result1[1])
        self.p.cut()
        self.assertEqual(self.p.item_count, 1)
        self.assertEqual(self.p.pars, ['abc'])
        for item, perf in zip(self.items, self.perfs):
            self.p.in_pool(item, perf)
        self.assertEqual(self.p.item_count, 6)
        self.assertEqual(self.p.pars, ['abc', 'first', 'second', (1, 2, 3), 'this', 24])
        self.p.cut()
        self.assertEqual(self.p.pars, ['second', (1, 2, 3), 'this', 24, 'abc'])
        self.assertEqual(self.p.perfs, [2, 3, 4, 5, 12])

        self.p.in_pool(self.additional_result2[0], self.additional_result2[1])
        self.p.in_pool(self.additional_result3[0], self.additional_result3[1])
        self.assertEqual(self.p.item_count, 7)
        self.p.cut(keep_largest=False)
        self.assertEqual(self.p.pars, [[1, 2], 'second', (1, 2, 3), 'this', 24])
        self.assertEqual(self.p.perfs, [-1, 2, 3, 4, 5])


class TestCoreSubFuncs(unittest.TestCase):
    """Test all functions in core.py"""

    def setUp(self):
        pass

    def test_input_to_list(self):
        print('Testing input_to_list() function')
        input_str = 'first'
        self.assertEqual(qt.input_to_list(input_str, 3), ['first', 'first', 'first'])
        self.assertEqual(qt.input_to_list(input_str, 4), ['first', 'first', 'first', 'first'])
        self.assertEqual(qt.input_to_list(input_str, 2, None), ['first', 'first'])
        input_list = ['first', 'second']
        self.assertEqual(qt.input_to_list(input_list, 3), ['first', 'second', None])
        self.assertEqual(qt.input_to_list(input_list, 4, 'padder'), ['first', 'second', 'padder', 'padder'])
        self.assertEqual(qt.input_to_list(input_list, 1), ['first', 'second'])
        self.assertEqual(qt.input_to_list(input_list, -5), ['first', 'second'])

    def test_point_in_space(self):
        sp = qt.Space([(0., 10.), (0., 10.), (0., 10.)])
        p1 = (5.5, 3.2, 7)
        p2 = (-1, 3, 10)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')
        self.assertFalse(p2 in sp)
        print(f'point {p2} is not in space {sp}')
        sp = qt.Space([(0., 10.), (0., 10.), range(40, 3, -2)], 'conti, conti, enum')
        p1 = (5.5, 3.2, 8)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')

    def test_space_around_centre(self):
        sp = qt.Space([(0., 10.), (0., 10.), (0., 10.)])
        p1 = (5.5, 3.2, 7)
        ssp = qt.space_around_centre(space=sp, centre=p1, radius=1.2)
        print(ssp.boes)
        print('\ntest multiple diameters:')
        self.assertEqual(ssp.boes, [(4.3, 6.7), (2.0, 4.4), (5.8, 8.2)])
        ssp = qt.space_around_centre(space=sp, centre=p1, radius=[1, 2, 1])
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(4.5, 6.5), (1.2000000000000002, 5.2), (6.0, 8.0)])
        print('\ntest points on edge:')
        p2 = (5.5, 3.2, 10)
        ssp = qt.space_around_centre(space=sp, centre=p1, radius=3.9)
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(1.6, 9.4), (0.0, 7.1), (3.1, 10.0)])
        print('\ntest enum spaces')
        sp = qt.Space([(0, 100), range(40, 3, -2)], 'discr, enum')
        p1 = [34, 12]
        ssp = qt.space_around_centre(space=sp, centre=p1, radius=5, ignore_enums=False)
        self.assertEqual(ssp.boes, [(29, 39), (22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(ssp.boes)
        print('\ntest enum space and ignore enum axis')
        ssp = qt.space_around_centre(space=sp, centre=p1, radius=5)
        self.assertEqual(ssp.boes, [(29, 39),
                                    (40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(sp.boes)

    def test_time_string_format(self):
        print('Testing qt.time_string_format() function:')
        t = 3.14
        self.assertEqual(qt.time_str_format(t), '3s 140.0ms')
        self.assertEqual(qt.time_str_format(t, estimation=True), '3s ')
        self.assertEqual(qt.time_str_format(t, short_form=True), '3"140')
        self.assertEqual(qt.time_str_format(t, estimation=True, short_form=True), '3"')
        t = 300.14
        self.assertEqual(qt.time_str_format(t), '5min 140.0ms')
        self.assertEqual(qt.time_str_format(t, estimation=True), '5min ')
        self.assertEqual(qt.time_str_format(t, short_form=True), "5'140")
        self.assertEqual(qt.time_str_format(t, estimation=True, short_form=True), "5'")
        t = 7435.0014
        self.assertEqual(qt.time_str_format(t), '2hrs 3min 55s 1.4ms')
        self.assertEqual(qt.time_str_format(t, estimation=True), '2hrs ')
        self.assertEqual(qt.time_str_format(t, short_form=True), "2H3'55\"001")
        self.assertEqual(qt.time_str_format(t, estimation=True, short_form=True), "2H")
        t = 88425.0509
        self.assertEqual(qt.time_str_format(t), '1days 33min 45s 50.9ms')
        self.assertEqual(qt.time_str_format(t, estimation=True), '1days ')
        self.assertEqual(qt.time_str_format(t, short_form=True), "1D33'45\"051")
        self.assertEqual(qt.time_str_format(t, estimation=True, short_form=True), "1D")


class TestEvaluations(unittest.TestCase):
    """Test all evaluation functions in core.py"""

    def setUp(self):
        """用np.random生成测试用数据，使用cumsum()模拟股票走势"""
        self.test_data1 = pd.DataFrame([5.34892759, 5.65768696, 5.79227076, 5.56266871, 5.88189632,
                                        6.24795001, 5.92755558, 6.38748165, 6.31331899, 5.86001665,
                                        5.61048472, 5.30696736, 5.40406792, 5.03180571, 5.37886353,
                                        5.78608307, 6.26540339, 6.59348026, 6.90943801, 6.70911677,
                                        6.33015954, 6.06697417, 5.9752499, 6.45786408, 6.95273763,
                                        6.7691991, 6.70355481, 6.28048969, 6.61344541, 6.24620003,
                                        6.47409983, 6.4522311, 6.8773094, 6.99727832, 6.59262674,
                                        6.59014938, 6.63758237, 6.38331869, 6.09902105, 6.35390109,
                                        6.51993567, 6.87244592, 6.83963485, 7.08797815, 6.88003144,
                                        6.83657323, 6.97819483, 7.01600276, 7.12554256, 7.58941523,
                                        7.61014457, 7.21224091, 7.48174399, 7.66490854, 7.51371968,
                                        7.11586198, 6.97147399, 6.67453301, 6.2042138, 6.33967015,
                                        6.22187938, 5.98426993, 6.37096079, 6.55897161, 6.26422645,
                                        6.69363762, 7.12668015, 6.83232926, 7.30524081, 7.4262041,
                                        7.54031383, 7.17545919, 7.20659257, 7.44886016, 7.37094393,
                                        6.88011022, 7.08142491, 6.74992833, 6.5967097, 6.21336693,
                                        6.35565105, 6.82347596, 6.44773408, 6.84538053, 6.47966466,
                                        6.09699528, 5.63927014, 6.01081024, 6.20585303, 6.60528206,
                                        7.01594726, 7.03684251, 6.76574977, 7.08740846, 6.65336462,
                                        7.07126686, 6.80058956, 6.79241977, 6.47843472, 6.39245474],
                                       columns=['value'])

        self.test_data2 = pd.DataFrame([5.09276527, 4.83828592, 4.6000911, 4.63170487, 4.63566451,
                                        4.50546921, 4.96390044, 4.64557907, 4.25787855, 3.76585551,
                                        3.38826334, 3.76243422, 4.06365426, 3.87084726, 3.91400935,
                                        4.13438822, 4.27064542, 4.56776104, 5.03800296, 5.31070529,
                                        5.39902276, 5.21186286, 5.05683114, 4.68842046, 5.11895168,
                                        5.27151571, 5.72294993, 6.09961056, 6.26569635, 6.48806151,
                                        6.16058885, 6.2582459, 6.38934791, 6.57831057, 6.19508831,
                                        5.70155153, 5.20435735, 5.36538825, 5.40450056, 5.2227697,
                                        5.37828693, 5.53058991, 6.02996797, 5.76802181, 5.66166713,
                                        6.07988994, 5.61794367, 5.63218151, 6.10728013, 6.0324168,
                                        6.27164431, 6.27551239, 6.52329665, 7.00470007, 7.34163113,
                                        7.33699083, 7.67661334, 8.09395749, 7.68086668, 7.58341161,
                                        7.46219819, 7.58671899, 7.19348298, 7.40088323, 7.47562005,
                                        7.93342043, 8.2286081, 8.3521632, 8.43590025, 8.34977395,
                                        8.57563095, 8.81586328, 9.08738649, 9.01542031, 8.8653815,
                                        9.21763111, 9.04233017, 8.59533999, 8.47590075, 8.70857222,
                                        8.78890756, 8.92697606, 9.35743773, 9.68280866, 10.15622021,
                                        10.55908549, 10.6337894, 10.55197128, 10.65435176, 10.54611045,
                                        10.19432562, 10.48320884, 10.36176768, 10.03186854, 10.23656092,
                                        10.0062843, 10.13669686, 10.30758958, 9.87904176, 10.05126375],
                                       columns=['value'])

        self.test_data3 = pd.DataFrame([5.02851874, 5.20700348, 5.02410709, 5.49836387, 5.06834371,
                                        5.10956737, 5.15314979, 5.02256472, 5.09746382, 5.23909247,
                                        4.93410336, 4.96316186, 5.40026682, 5.7353255, 5.53438319,
                                        5.79092139, 5.67528173, 5.89840855, 5.75379463, 6.10855386,
                                        5.77322365, 5.84538021, 5.6103973, 5.7518655, 5.49729695,
                                        5.13610628, 5.30524121, 5.68093462, 5.73251319, 6.04420783,
                                        6.26929843, 6.59610234, 6.09872345, 6.25475121, 6.72927396,
                                        6.91395783, 7.00693283, 7.36217783, 7.71516676, 7.67580263,
                                        7.62477511, 7.73600568, 7.53457914, 7.46170277, 7.83658014,
                                        8.11481319, 8.03705544, 7.64948845, 7.52043731, 7.67247943,
                                        7.46511982, 7.43541798, 7.58856517, 7.9392717, 8.25406287,
                                        7.77031632, 8.03223447, 7.86799055, 7.57630999, 7.33230519,
                                        7.22378732, 6.85972264, 7.17548456, 7.5387846, 7.2392632,
                                        6.8455644, 6.59557185, 6.6496796, 6.73685623, 7.18598015,
                                        7.13619128, 6.88060157, 7.1399681, 7.30308077, 6.94942434,
                                        7.0247815, 7.37567798, 7.50080197, 7.59719284, 7.14520561,
                                        7.29913484, 7.79551341, 8.15497781, 8.40456095, 8.86516528,
                                        8.53042688, 8.94268762, 8.52048006, 8.80036284, 8.91602364,
                                        9.19953385, 8.70828953, 8.24613093, 8.18770453, 7.79548389,
                                        7.68627967, 7.23205036, 6.98302636, 7.06515819, 6.95068113],
                                       columns=['value'])

        self.test_data4 = pd.DataFrame([4.97926539, 5.44016005, 5.45122915, 5.74485615, 5.45600553, 5.44858945, 5.2435413, 5.47315161, 5.58464303, 5.36179749, 5.38236326, 5.29614981, 5.76523508, 5.75102892, 6.15316618, 6.03852528, 6.01442228, 5.70510182, 5.22748133, 5.46762379, 5.78926267, 5.8221362, 5.61236849, 5.30615725, 5.24200611, 5.41042642, 5.59940342, 5.28306781, 4.99451932, 5.08799266, 5.38865647, 5.58229139, 5.33492845, 5.48206276, 5.09721379, 5.39190493, 5.29965087, 5.0374415, 5.50798022, 5.43107577, 5.22759507, 4.991809, 5.43153084, 5.39966868, 5.59916352, 5.66412137, 6.00611838, 5.63564902, 5.66723484, 5.29863863, 4.91115153, 5.3749929, 5.75082334, 6.08308148, 6.58091182, 6.77848803, 7.19588758, 7.64862286, 7.99818347, 7.91824794, 8.30341071, 8.45984973, 7.98700002, 8.18924931, 8.60755649, 8.66233396, 8.91018407, 9.0782739, 9.33515448, 8.95870245, 8.98426422, 8.50340317, 8.64916085, 8.93592407, 8.63145745, 8.65322862, 8.39543204, 8.37969997, 8.23394504, 8.04062872, 7.91259763, 7.57252171, 7.72670114, 7.74486117, 8.06908188, 7.99166889, 7.92155906, 8.39956136, 8.80181323, 8.47464091, 8.06557064, 7.87145573, 8.0237959, 8.39481998, 8.68525692, 8.81185461, 8.98632237, 9.0989835, 8.89787405, 8.86508591],
                                       columns=['value'])

        self.test_data5 = pd.DataFrame([4.50258923, 4.35142568, 4.07459514, 3.87791297, 3.73715985, 3.98455684, 4.07587908, 4.00042472, 4.28276612, 4.01362051, 4.13713565, 4.49312372, 4.48633159, 4.4641207, 4.13444605, 3.79107217, 4.22941629, 4.56548511, 4.92472163, 5.27723158, 5.67409193, 6.00176917, 5.88889928, 5.55256103, 5.39308314, 5.2610492, 5.30738908, 5.22222408, 4.90332238, 4.57499908, 4.96097146, 4.81531011, 4.39115442, 4.63200662, 5.04588813, 4.67866025, 5.01705123, 4.83562258, 4.60381702, 4.66187576, 4.41292828, 4.86604507, 4.42280124, 4.07517294, 4.16317319, 4.10316596, 4.42913598, 4.06609666, 3.96725913, 4.15965746, 4.12379564, 4.04054068, 3.84342851, 3.45902867, 3.17649855, 3.09773586, 3.5502119, 3.66396995, 3.66306483, 3.29131401, 2.79558533, 2.88319542, 3.03671098, 3.44645857, 3.88167161, 3.57961874, 3.60180276, 3.96702102, 4.05429995, 4.40056979, 4.05653231, 3.59600456, 3.60792477, 4.09989922, 3.73503663, 4.01892626, 3.94597242, 3.81466605, 3.71417992, 3.93767156, 4.42806557, 4.06988106, 4.03713636, 4.34408673, 4.79810156, 5.18115011, 4.89798406, 5.3960077, 5.72504875, 5.61894017, 5.1958197, 4.85275896, 5.17550207, 4.71548987, 4.62408567, 4.55488535, 4.36532649, 4.26031979, 4.25225607, 4.58627048],
                                       columns=['value'])

        self.test_data6 = pd.DataFrame([5.08639513, 5.05761083, 4.76160923, 4.62166504, 4.62923183, 4.25070173, 4.13447513, 3.90890013, 3.76687608, 3.43342482, 3.67648224, 3.6274775, 3.9385404, 4.39771627, 4.03199346, 3.93265288, 3.50059789, 3.3851961, 3.29743973, 3.2544872, 2.93692949, 2.70893003, 2.55461976, 2.20922332, 2.29054475, 2.2144714, 2.03726827, 2.39007617, 2.29866155, 2.40607111, 2.40440444, 2.79374649, 2.66541922, 2.27018079, 2.08505127, 2.55478864, 2.22415625, 2.58517923, 2.58802256, 2.94870959, 2.69301739, 2.19991535, 2.69473146, 2.64704637, 2.62753542, 2.14240825, 2.38565154, 1.94592117, 2.32243877, 2.69337246, 2.51283854, 2.62484451, 2.15559054, 2.35410875, 2.31219177, 1.96018265, 2.34711266, 2.58083322, 2.40290041, 2.20439791, 2.31472425, 2.16228248, 2.16439749, 2.20080737, 1.73293206, 1.9264407, 2.25089861, 2.69269101, 2.59296687, 2.1420998, 1.67819153, 1.98419023, 2.14479494, 1.89055376, 1.96720648, 1.9916694, 2.37227761, 2.14446036, 2.34573903, 1.86162546, 2.1410721, 2.39204939, 2.52529064, 2.47079939, 2.9299031, 3.09452923, 2.93276708, 3.21731309, 3.06248964, 2.90413406, 2.67844632, 2.45621213, 2.41463398, 2.7373913, 3.14917045, 3.4033949, 3.82283446, 4.02285451, 3.7619638, 4.10346795],
                                       columns=['value'])

        self.test_data7 = pd.DataFrame([4.75233583, 4.47668283, 4.55894263, 4.61765848, 4.622892, 4.58941116, 4.32535872, 3.88112797, 3.47237806, 3.50898953, 3.82530406, 3.6718017, 3.78918195, 4.1800752, 4.01818557, 4.40822582, 4.65474654, 4.89287256, 4.40879274, 4.65505126, 4.36876403, 4.58418934, 4.75687172, 4.3689799, 4.16126498, 4.0203982, 3.77148242, 3.38198096, 3.07261764, 2.9014741, 2.5049543, 2.756105, 2.28779058, 2.16986991, 1.8415962, 1.83319008, 2.20898291, 2.00128981, 1.75747025, 1.26676663, 1.40316876, 1.11126484, 1.60376367, 1.22523829, 1.58816681, 1.49705679, 1.80244138, 1.55128293, 1.35339409, 1.50985759, 1.0808451, 1.05892796, 1.43414812, 1.43039101, 1.73631655, 1.43940867, 1.82864425, 1.71088265, 2.12015154, 2.45417128, 2.84777618, 2.7925612, 2.90975121, 3.25920745, 3.13801182, 3.52733677, 3.65468491, 3.69395211, 3.49862035, 3.24786017, 3.64463138, 4.00331929, 3.62509565, 3.78013949, 3.4174012, 3.76312271, 3.62054004, 3.67206716, 3.60596058, 3.38636199, 3.42580676, 3.32921095, 3.02976759, 3.28258676, 3.45760838, 3.24917528, 2.94618304, 2.86980011, 2.63191259, 2.39566759, 2.53159917, 2.96273967, 3.25626185, 2.97425402, 3.16412191, 3.58280763, 3.23257727, 3.62353556, 3.12806399, 2.92532313],
                                       columns=['value'])

    def test_fv(self):
        print(f'test with test data and empty DataFrame')
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data1), 1.39245474)
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data2), 5.05126375)
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data3), 1.95068113)
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data4), 3.86508591)
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data5), -0.41372952)
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data6), -0.89653205)
        self.assertAlmostEqual(qt.core._eval_fv(self.test_data7), -2.07467687)
        self.assertAlmostEqual(qt.core._eval_fv(pd.DataFrame()), -np.inf)
        print(f'Error testing')
        self.assertRaises(AssertionError, qt.core._eval_fv, 15)
        self.assertRaises(KeyError,
                          qt.core._eval_fv,
                          pd.DataFrame([1,2,3], columns=['non_value']))

    def test_max_drawdown(self):
        print(f'test with test data and empty DataFrame')
        self.assertAlmostEqual(qt.core._eval_max_drawdown(self.test_data1)[0], 0.977076663)
        self.assertEqual(qt.core._eval_max_drawdown(self.test_data1)[1], 13)
        self.assertAlmostEqual(qt.core._eval_max_drawdown(self.test_data2)[0], 18.37435422)
        self.assertEqual(qt.core._eval_max_drawdown(self.test_data2)[1], 10)
        self.assertAlmostEqual(qt.core._eval_max_drawdown(self.test_data3)[0], 1.132225958)
        self.assertEqual(qt.core._eval_max_drawdown(self.test_data3)[1], 10)
        self.assertAlmostEqual(qt.core._eval_max_drawdown(self.test_data6)[0], 39.4490245)
        self.assertEqual(qt.core._eval_max_drawdown(self.test_data6)[1], 70)
        self.assertEqual(qt.core._eval_max_drawdown(pd.DataFrame()), -np.inf)
        print(f'Error testing')
        self.assertRaises(AssertionError, qt.core._eval_fv, 15)
        self.assertRaises(KeyError,
                          qt.core._eval_fv,
                          pd.DataFrame([1, 2, 3], columns=['non_value']))
        # divided by zero error:
        self.assertRaises(ZeroDivisionError, qt.core._eval_max_drawdown, self.test_data4)

    def test_info_ratio(self):
        pass

    def test_volatility(self):
        pass

    def test_sharp(self):
        pass

    def test_beta(self):
        pass

    def test_alpha(self):
        pass

    def test_benchmark(self):
        pass


class TestLoop(unittest.TestCase):
    def setUp(self):
        pass

    def test_loop_step(self):
        pass

    def test_loop(self):
        pass


class TestOperatorSubFuncs(unittest.TestCase):
    def setUp(self):
        mask_list = [[0.0, 0.0, 0.0, 0.0],
                     [0.5, 0.0, 0.0, 1.0],
                     [0.5, 0.0, 0.3, 1.0],
                     [0.5, 0.0, 0.3, 0.5],
                     [0.5, 0.5, 0.3, 0.5],
                     [0.5, 0.5, 0.3, 1.0],
                     [0.3, 0.5, 0.0, 1.0],
                     [0.3, 1.0, 0.0, 1.0]]
        signal_list = [[0.0, 0.0, 0.0, 0.0],
                       [0.5, 0.0, 0.0, 1.0],
                       [0.0, 0.0, 0.3, 0.0],
                       [0.0, 0.0, 0.0, -0.5],
                       [0.0, 0.5, 0.0, 0.0],
                       [0.0, 0.0, 0.0, 0.5],
                       [-0.4, 0.0, -1.0, 0.0],
                       [0.0, 0.5, 0.0, 0.0]]

        self.mask = np.array(mask_list)
        self.correct_signal = np.array(signal_list)
        self.op = qt.Operator()

    def test_ls_blend(self):
        """测试多空蒙板的混合器，三种混合方式均需要测试"""
        ls_mask1 = [[0.0, 0.0, 0.0, -0.0],
                    [1.0, 0.0, 0.0, -1.0],
                    [1.0, 0.0, 1.0, -1.0],
                    [1.0, 0.0, 1.0, -1.0],
                    [1.0, 1.0, 1.0, -1.0],
                    [1.0, 1.0, 1.0, -1.0],
                    [0.0, 1.0, 0.0, -1.0],
                    [0.0, 1.0, 0.0, -1.0]]
        ls_mask2 = [[0.0, 0.0, 0.5, -0.5],
                    [0.0, 0.0, 0.5, -0.3],
                    [0.0, 0.5, 0.5, -0.0],
                    [0.5, 0.5, 0.3, -0.0],
                    [0.5, 0.5, 0.3, -0.3],
                    [0.5, 0.5, 0.0, -0.5],
                    [0.3, 0.5, 0.0, -1.0],
                    [0.3, 1.0, 0.0, -1.0]]
        ls_mask3 = [[0.5, 0.0, 1.0, -0.4],
                    [0.4, 0.0, 1.0, -0.3],
                    [0.3, 0.0, 0.8, -0.2],
                    [0.2, 0.0, 0.6, -0.1],
                    [0.1, 0.2, 0.4, -0.2],
                    [0.1, 0.3, 0.2, -0.5],
                    [0.1, 0.4, 0.0, -0.5],
                    [0.1, 0.5, 0.0, -1.0]]
        ls_blnd_avg = [[0.16666667, 0.00000000, 0.50000000, -0.3],
                       [0.46666667, 0.00000000, 0.50000000, -0.53333333],
                       [0.43333333, 0.16666667, 0.76666667, -0.4],
                       [0.56666667, 0.16666667, 0.63333333, -0.36666667],
                       [0.53333333, 0.56666667, 0.56666667, -0.5],
                       [0.53333333, 0.60000000, 0.40000000, -0.66666667],
                       [0.13333333, 0.63333333, 0.00000000, -0.83333333],
                       [0.13333333, 0.83333333, 0.00000000, -1.]]
        # result with blender 'str-1.5'
        ls_blnd_str_15 = [[0, 0, 1, 0],
                          [0, 0, 1, -1],
                          [0, 0, 1, 0],
                          [1, 0, 1, 0],
                          [1, 1, 1, -1],
                          [1, 1, 0, -1],
                          [0, 1, 0, -1],
                          [0, 1, 0, -1]]
        # result with blender 'pos-2' == 'pos-2-0'
        ls_blnd_pos_2 = [[0.00, 0.00, 0.75, -0.45],
                         [0.70, 0.00, 0.75, -0.80],
                         [0.65, 0.00, 1.00, -0.60],
                         [0.85, 0.00, 0.95, -0.55],
                         [0.80, 0.85, 0.85, -0.75],
                         [0.80, 0.90, 0.60, -1.00],
                         [0.20, 0.95, 0.00, -1.00],
                         [0.20, 1.00, 0.00, -1.00]]
        # result with blender 'pos-2-0.25'
        ls_blnd_pos_2_25 = [[0.00, 0.00, 0.75, -0.45],
                            [0.70, 0.00, 0.75, -0.8],
                            [0.65, 0.00, 1.00, 0.],
                            [0.85, 0.00, 0.95, 0.],
                            [0.80, 0.85, 0.85, -0.75],
                            [0.80, 0.90, 0.00, -1.],
                            [0.00, 0.95, 0.00, -1.],
                            [0.00, 1.00, 0.00, -1.]]

        ls_masks = [np.array(ls_mask1), np.array(ls_mask2), np.array(ls_mask3)]

        # test A: the ls_blender 'str-T'
        self.op.set_blender('ls', 'str-1.5')
        res = qt.Operator._ls_blend(self.op, ls_masks)
        print(res)
        self.assertTrue(np.allclose(res, ls_blnd_str_15))

        # test B: the ls_blender 'pos-N-T'
        self.op.set_blender('ls', 'pos-2')
        res = qt.Operator._ls_blend(self.op, ls_masks)
        print(res)
        self.assertTrue(np.allclose(res, ls_blnd_pos_2))

        self.op.set_blender('ls', 'pos-2-0.25')
        res = qt.Operator._ls_blend(self.op, ls_masks)
        print(res)
        self.assertTrue(np.allclose(res, ls_blnd_pos_2_25))

        # test C: the ls_blender 'avg'
        self.op.set_blender('ls', 'avg')
        res = qt.Operator._ls_blend(self.op, ls_masks)
        print(res)
        self.assertTrue(np.allclose(res, ls_blnd_avg))

    def test_sel_blend(self):
        """测试选股蒙板的混合器，包括所有的混合模式"""
        # step2, test blending of sel masks
        pass

    def test_bs_blend(self):
        """测试买卖信号混合模式"""
        # step3, test blending of op signals
        pass

    def test_unify(self):
        print('Testing Unify functions\n')
        l1 = np.array([[3, 2, 5], [5, 3, 2]])
        res = qt.unify(l1)
        target = np.array([[0.3, 0.2, 0.5], [0.5, 0.3, 0.2]])

        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')
        l1 = np.array([[1, 1, 1, 1, 1], [2, 2, 2, 2, 2]])
        res = qt.unify(l1)
        target = np.array([[0.2, 0.2, 0.2, 0.2, 0.2], [0.2, 0.2, 0.2, 0.2, 0.2]])

        self.assertIs(np.allclose(res, target), True, 'sum of all elements is 1')

    def test_mask_to_signal(self):
        self.signal = qt.mask_to_signal(self.mask)
        print(self.signal)
        self.assertTrue(np.allclose(self.signal, self.correct_signal))


class TestLSStrategy(qt.RollingTiming):
    """用于test测试的简单多空蒙板生成策略。基于RollingTiming滚动择时方法生成

    该策略有两个参数，N与Price
    N用于计算OHLC价格平均值的N日简单移动平均，判断，当移动平均值大于等于Price时，状态为看多，否则为看空
    """

    def __init__(self):
        super().__init__(stg_name='test_LS',
                         stg_text='test long/short strategy',
                         par_count=2,
                         par_types='discr, conti',
                         par_bounds_or_enums=([1, 5], [2, 10]),
                         data_types='close, open, high, low',
                         data_freq='d',
                         window_length=5)
        pass

    def _realize(self, hist_data: np.ndarray, params: tuple):
        n, price = params
        h = hist_data.T

        avg = (h[0] + h[1] + h[2] + h[3]) / 4
        ma = qt.sma(avg, n)
        if ma[-1] < price:
            return 0
        else:
            return 1


class TestSelStrategy(qt.Selecting):
    """用于Test测试的简单选股策略，基于Selecting策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，从股票池的三只股票中选出今日变化率 = (今收-昨收)/平均股价（OHLC平均股价）最高的两支，放入中选池，否则落选。
    选股比例为平均分配
    """

    def __init__(self):
        super().__init__(stg_name='test_SEL',
                         stg_text='test portfolio selection strategy',
                         par_count=0,
                         par_types='',
                         par_bounds_or_enums=(),
                         data_types='high, low, close',
                         data_freq='d',
                         sample_freq='10d',
                         window_length=5)
        pass

    def _realize(self, hist_data: np.ndarray):
        avg = np.nanmean(hist_data, axis=(1, 2))
        dif = (hist_data[:, :, 2] - np.roll(hist_data[:, :, 2], 1, 1))
        dif_no_nan = np.array([arr[~np.isnan(arr)][-1] for arr in dif])
        difper = dif_no_nan / avg
        large2 = difper.argsort()[1:]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        # debug
        # print(f'avg is \n{np.nanmean(hist_data, axis=(1, 2))}\n')
        # print(f'last close price is\n{hist_data[:, :, 2]}\n')
        # print(f'last close price difference is\n{(hist_data[:, :, 2] - np.roll(hist_data[:, :, 2], 1, 1))}\n')
        # print(f'selected largest two args: {large2} in'
        #       f'\n{(hist_data[:, :, 2] - np.roll(hist_data[:, :, 2], 1, 1))[:, -1] / avg}\n'
        #       f'and got result chosen:\n{chosen}\n')
        return chosen


class TestSelStrategyDiffTime(qt.Selecting):
    """用于Test测试的简单选股策略，基于Selecting策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，从股票池的三只股票中选出今日变化率 = (今收-昨收)/平均股价（OHLC平均股价）最高的两支，放入中选池，否则落选。
    选股比例为平均分配
    """

    def __init__(self):
        super().__init__(stg_name='test_SEL',
                         stg_text='test portfolio selection strategy',
                         par_count=0,
                         par_types='',
                         par_bounds_or_enums=(),
                         data_types='close, low, open',
                         data_freq='d',
                         sample_freq='w',
                         window_length=2)
        pass

    def _realize(self, hist_data: np.ndarray):
        avg = hist_data.mean(axis=1).squeeze()
        difper = (hist_data[:, :, 0] - np.roll(hist_data[:, :, 0], 1))[:, -1] / avg
        large2 = difper.argsort()[0:2]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        return chosen


class TestSigStrategy(qt.SimpleTiming):
    """用于Test测试的简单信号生成策略，基于SimpleTiming策略生成

    策略有三个参数，第一个参数为ratio，另外两个参数为price1以及price2
    ratio是k线形状比例的阈值，定义为abs((C-O)/(H-L))。当这个比值小于ratio阈值时，判断该K线为十字交叉（其实还有丁字等多种情形，但这里做了
    简化处理。
    信号生成的规则如下：
    1，当某个K线出现十字交叉，且昨收与今收之差大于price1时，买入信号
    2，当某个K线出现十字交叉，且昨收与今收之差小于price2时，卖出信号
    """

    def __init__(self):
        super().__init__(stg_name='test_SIG',
                         stg_text='test signal creation strategy',
                         par_count=3,
                         par_types='conti, conti, conti',
                         par_bounds_or_enums=([2, 10], [0, 3], [0, 3]),
                         data_types='close, open, high, low',
                         window_length=2)
        pass

    def _realize(self, hist_data: np.ndarray, params: tuple):
        r, price1, price2 = params
        h = hist_data.T

        ratio = np.abs((h[0] - h[1]) / (h[3] - h[2]))
        diff = h[0] - np.roll(h[0], 1)

        sig = np.where((ratio < r) & (diff > price1),
                       1,
                       np.where((ratio < r) & (diff < price2), -1, 0))
        # debug
        # print(f'In TestSigStrategy: \nthe history data is\n{h}\nthe ratio is \n{ratio}\nthe diff is\n{diff}')

        return sig


class TestOperator(unittest.TestCase):
    """全面测试Operator对象的所有功能。包括：

        1, Strategy 参数的设置
        2, 历史数据的获取与分配提取
        3, 策略优化参数的批量设置和优化空间的获取
        4, 策略输出值的正确性验证
        5, 策略结果的混合结果确认
    """

    def setUp(self):
        """prepare data for Operator test"""
        print('start testing HistoryPanel object\n')

        # build up test data: a 4-type, 3-share, 50-day matrix of prices that contains nan values in some days
        # for some share_pool

        # for share1:
        data_rows = 50

        share1_close = [10.04, 10, 10, 9.99, 9.97, 9.99, 10.03, 10.03, 10.06, 10.06, 10.11,
                        10.09, 10.07, 10.06, 10.09, 10.03, 10.03, 10.06, 10.08, 10, 9.99,
                        10.03, 10.03, 10.06, 10.03, 9.97, 9.94, 9.83, 9.77, 9.84, 9.91, 9.93,
                        9.96, 9.91, 9.91, 9.88, 9.91, 9.64, 9.56, 9.57, 9.55, 9.57, 9.61, 9.61,
                        9.55, 9.57, 9.63, 9.64, 9.65, 9.62]
        share1_open = [10.02, 10, 9.98, 9.97, 9.99, 10.01, 10.04, 10.06, 10.06, 10.11,
                       10.11, 10.07, 10.06, 10.09, 10.03, 10.02, 10.06, 10.08, 9.99, 10,
                       10.03, 10.02, 10.06, 10.03, 9.97, 9.94, 9.83, 9.78, 9.77, 9.91, 9.92,
                       9.97, 9.91, 9.9, 9.88, 9.91, 9.63, 9.64, 9.57, 9.55, 9.58, 9.61, 9.62,
                       9.55, 9.57, 9.61, 9.63, 9.64, 9.61, 9.56]
        share1_high = [10.07, 10, 10, 10, 10.03, 10.03, 10.04, 10.09, 10.1, 10.14, 10.11, 10.1,
                       10.09, 10.09, 10.1, 10.05, 10.07, 10.09, 10.1, 10, 10.04, 10.04, 10.06,
                       10.09, 10.05, 9.97, 9.96, 9.86, 9.77, 9.92, 9.94, 9.97, 9.97, 9.92, 9.92,
                       9.92, 9.93, 9.64, 9.58, 9.6, 9.58, 9.62, 9.62, 9.64, 9.59, 9.62, 9.63,
                       9.7, 9.66, 9.64]
        share1_low = [9.99, 10, 9.97, 9.97, 9.97, 9.98, 9.99, 10.03, 10.03, 10.04, 10.11, 10.07,
                      10.05, 10.03, 10.03, 10.01, 9.99, 10.03, 9.95, 10, 9.95, 10, 10.01, 9.99,
                      9.96, 9.89, 9.83, 9.77, 9.77, 9.8, 9.9, 9.91, 9.89, 9.89, 9.87, 9.85, 9.6,
                      9.64, 9.53, 9.55, 9.54, 9.55, 9.58, 9.54, 9.53, 9.53, 9.63, 9.64, 9.59, 9.56]

        # for share2:
        share2_close = [9.68, 9.87, 9.86, 9.87, 9.79, 9.82, 9.8, 9.66, 9.62, 9.58, 9.69, 9.78, 9.75,
                        9.96, 9.9, 10.04, 10.06, 10.08, 10.24, 10.24, 10.24, 9.86, 10.13, 10.12,
                        10.1, 10.25, 10.24, 10.22, 10.75, 10.64, 10.56, 10.6, 10.42, 10.25, 10.24,
                        10.49, 10.57, 10.63, 10.48, 10.37, 10.96, 11.02, np.nan, np.nan, 10.88, 10.87, 11.01,
                        11.01, 11.58, 11.8]
        share2_open = [9.88, 9.88, 9.89, 9.75, 9.74, 9.8, 9.62, 9.65, 9.58, 9.67, 9.81, 9.8, 10,
                       9.95, 10.1, 10.06, 10.14, 9.9, 10.2, 10.29, 9.86, 9.48, 10.01, 10.24, 10.26,
                       10.24, 10.12, 10.65, 10.64, 10.56, 10.42, 10.43, 10.29, 10.3, 10.44, 10.6,
                       10.67, 10.46, 10.39, 10.9, 11.01, 11.01, np.nan, np.nan, 10.82, 11.02, 10.96,
                       11.55, 11.74, 11.8]
        share2_high = [9.91, 10.04, 9.93, 10.04, 9.84, 9.88, 9.99, 9.7, 9.67, 9.71, 9.85, 9.9, 10,
                       10.2, 10.11, 10.18, 10.21, 10.26, 10.38, 10.47, 10.42, 10.07, 10.24, 10.27,
                       10.38, 10.43, 10.39, 10.65, 10.84, 10.65, 10.73, 10.63, 10.51, 10.35, 10.46,
                       10.63, 10.74, 10.76, 10.54, 11.02, 11.12, 11.17, np.nan, np.nan, 10.92, 11.15,
                       11.11, 11.55, 11.95, 11.93]
        share2_low = [9.63, 9.84, 9.81, 9.74, 9.67, 9.72, 9.57, 9.54, 9.51, 9.47, 9.68, 9.63, 9.75,
                      9.65, 9.9, 9.93, 10.03, 9.8, 10.14, 10.09, 9.78, 9.21, 9.11, 9.68, 10.05,
                      10.12, 9.89, 9.89, 10.59, 10.43, 10.34, 10.32, 10.21, 10.2, 10.18, 10.36,
                      10.51, 10.41, 10.32, 10.37, 10.87, 10.95, np.nan, np.nan, 10.65, 10.71, 10.75,
                      10.91, 11.31, 11.58]

        # for share3:
        share3_close = [6.64, 7.26, 7.03, 6.87, np.nan, 6.64, 6.85, 6.7, 6.39, 6.22, 5.92, 5.91, 6.11,
                        5.91, 6.23, 6.28, 6.28, 6.27, np.nan, 5.56, 5.67, 5.16, 5.69, 6.32, 6.14, 6.25,
                        5.79, 5.26, 5.05, 5.45, 6.06, 6.21, 5.69, 5.46, 6.02, 6.69, 7.43, 7.72, 8.16,
                        7.83, 8.7, 8.71, 8.88, 8.54, 8.87, 8.87, 8.18, 7.8, 7.97, 8.25]
        share3_open = [7.26, 7, 6.88, 6.91, np.nan, 6.81, 6.63, 6.45, 6.16, 6.24, 5.96, 5.97, 5.96,
                       6.2, 6.35, 6.11, 6.37, 5.58, np.nan, 5.65, 5.19, 5.42, 6.3, 6.15, 6.05, 5.89,
                       5.22, 5.2, 5.07, 6.04, 6.12, 5.85, 5.67, 6.02, 6.04, 7.07, 7.64, 7.99, 7.59,
                       8.73, 8.72, 8.97, 8.58, 8.71, 8.77, 8.4, 7.95, 7.76, 8.25, 7.51]
        share3_high = [7.41, 7.31, 7.14, 7, np.nan, 6.82, 6.96, 6.85, 6.5, 6.34, 6.04, 6.02, 6.12, 6.38,
                       6.43, 6.46, 6.43, 6.27, np.nan, 6.01, 5.67, 5.67, 6.35, 6.32, 6.43, 6.36, 5.79,
                       5.47, 5.65, 6.04, 6.14, 6.23, 5.83, 6.25, 6.27, 7.12, 7.82, 8.14, 8.27, 8.92,
                       8.76, 9.15, 8.9, 9.01, 9.16, 9, 8.27, 7.99, 8.33, 8.25]
        share3_low = [6.53, 6.87, 6.83, 6.7, np.nan, 6.63, 6.57, 6.41, 6.15, 6.07, 5.89, 5.82, 5.73, 5.81,
                      6.1, 6.06, 6.16, 5.57, np.nan, 5.51, 5.19, 5.12, 5.69, 6.01, 5.97, 5.86, 5.18, 5.19,
                      4.96, 5.45, 5.84, 5.85, 5.28, 5.42, 6.02, 6.69, 7.28, 7.64, 7.25, 7.83, 8.41, 8.66,
                      8.53, 8.54, 8.73, 8.27, 7.95, 7.67, 7.8, 7.51]

        self.date_indices = ['2016-07-01', '2016-07-04', '2016-07-05', '2016-07-06',
                             '2016-07-07', '2016-07-08', '2016-07-11', '2016-07-12',
                             '2016-07-13', '2016-07-14', '2016-07-15', '2016-07-18',
                             '2016-07-19', '2016-07-20', '2016-07-21', '2016-07-22',
                             '2016-07-25', '2016-07-26', '2016-07-27', '2016-07-28',
                             '2016-07-29', '2016-08-01', '2016-08-02', '2016-08-03',
                             '2016-08-04', '2016-08-05', '2016-08-08', '2016-08-09',
                             '2016-08-10', '2016-08-11', '2016-08-12', '2016-08-15',
                             '2016-08-16', '2016-08-17', '2016-08-18', '2016-08-19',
                             '2016-08-22', '2016-08-23', '2016-08-24', '2016-08-25',
                             '2016-08-26', '2016-08-29', '2016-08-30', '2016-08-31',
                             '2016-09-01', '2016-09-02', '2016-09-05', '2016-09-06',
                             '2016-09-07', '2016-09-08']

        self.shares = ['000010', '000030', '000039']

        self.types = ['close', 'open', 'high', 'low']

        self.test_data_3D = np.zeros((3, data_rows, 4))
        self.test_data_2D = np.zeros((data_rows, 3))
        self.test_data_2D2 = np.zeros((data_rows, 4))

        # Build up 3D data
        self.test_data_3D[0, :, 0] = share1_close
        self.test_data_3D[0, :, 1] = share1_open
        self.test_data_3D[0, :, 2] = share1_high
        self.test_data_3D[0, :, 3] = share1_low

        self.test_data_3D[1, :, 0] = share2_close
        self.test_data_3D[1, :, 1] = share2_open
        self.test_data_3D[1, :, 2] = share2_high
        self.test_data_3D[1, :, 3] = share2_low

        self.test_data_3D[2, :, 0] = share3_close
        self.test_data_3D[2, :, 1] = share3_open
        self.test_data_3D[2, :, 2] = share3_high
        self.test_data_3D[2, :, 3] = share3_low

        self.hp1 = qt.HistoryPanel(values=self.test_data_3D,
                                   levels=self.shares,
                                   columns=self.types,
                                   rows=self.date_indices)
        self.op = qt.Operator(selecting_types=['simple'], timing_types='dma', ricon_types='urgent')

    def test_property_get(self):
        self.assertIsInstance(self.op, qt.Operator)
        self.assertIsInstance(self.op.timing[0], qt.TimingDMA)
        self.assertIsInstance(self.op.selecting[0], qt.SelectingSimple)
        self.assertIsInstance(self.op.ricon[0], qt.RiconUrgent)
        self.assertEqual(self.op.selecting_count, 1)
        self.assertEqual(self.op.strategy_count, 3)
        self.assertEqual(self.op.ricon_count, 1)
        self.assertEqual(self.op.timing_count, 1)
        print(self.op.strategies, '\n', [qt.TimingDMA, qt.SelectingSimple, qt.RiconUrgent])
        self.assertEqual(len(self.op.strategies), 3)
        self.assertIsInstance(self.op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(self.op.strategies[1], qt.SelectingSimple)
        self.assertIsInstance(self.op.strategies[2], qt.RiconUrgent)
        self.assertEqual(self.op.strategy_count, 3)
        self.assertEqual(self.op.op_data_freq, 'd')
        self.assertEqual(self.op.op_data_types, ['close'])
        self.assertEqual(self.op.opt_space_par, ([], []))
        self.assertEqual(self.op.max_window_length, 270)
        self.assertEqual(self.op.ls_blender, 'pos-1')
        self.assertEqual(self.op.selecting_blender, '0')
        self.assertEqual(self.op.ricon_blender, 'add')
        self.assertEqual(self.op.opt_types, [0, 0, 0])

    def test_prepare_data(self):
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        test_sig = TestSigStrategy()
        self.op = qt.Operator(timing_types=[test_ls],
                              selecting_types=[test_sel],
                              ricon_types=[test_sig])
        too_early_cash = qt.CashPlan(dates='2016-01-01', amounts=10000)
        early_cash = qt.CashPlan(dates='2016-07-01', amounts=10000)
        on_spot_cash = qt.CashPlan(dates='2016-07-08', amounts=10000)
        late_cash = qt.CashPlan(dates='2016-12-31', amounts=10000)
        multi_cash = qt.CashPlan(dates='2016-07-08, 2016-08-08', amounts=[10000, 10000])
        self.op.set_parameter(stg_id='t-0',
                              pars={'000300': (5, 10.),
                                    '000400': (5, 10.),
                                    '000500': (5, 6.)})
        self.op.set_parameter(stg_id='s-0',
                              pars=())
        self.op.set_parameter(stg_id='r-0',
                              pars=(0.2, 0.02, -0.02))
        self.op.prepare_data(hist_data=self.hp1,
                             cash_plan=on_spot_cash)
        self.assertIsInstance(self.op._selecting_history_data, list)
        self.assertIsInstance(self.op._timing_history_data, list)
        self.assertIsInstance(self.op._ricon_history_data, list)
        self.assertEqual(len(self.op._selecting_history_data), 1)
        self.assertEqual(len(self.op._timing_history_data), 1)
        self.assertEqual(len(self.op._ricon_history_data), 1)
        sel_hist_data = self.op._selecting_history_data[0]
        tim_hist_data = self.op._timing_history_data[0]
        ric_hist_data = self.op._ricon_history_data[0]
        print('selecting history data:\n', sel_hist_data)
        print('originally passed data in correct sequence:\n', self.test_data_3D[:, 3:, [2, 3, 0]])
        print('difference is \n', sel_hist_data - self.test_data_3D[:, :, [2, 3, 0]])
        # TODO: 为什么生成的数据的行数都这么奇怪？为什么不是把所有的数据带入计算？尤其是RollingTiming，第一条结果也需要利用之前的数据生成的
        self.assertTrue(np.allclose(sel_hist_data, self.test_data_3D[:, :, [2, 3, 0]], equal_nan=True))
        self.assertTrue(np.allclose(tim_hist_data, self.test_data_3D, equal_nan=True))
        self.assertTrue(np.allclose(ric_hist_data, self.test_data_3D[:, 3:, :], equal_nan=True))

        # raises Value Error if empty history panel is given
        empty_hp = qt.HistoryPanel()
        correct_hp = qt.HistoryPanel(values=np.random.randint(10, size=(3, 50, 4)))
        too_many_shares = qt.HistoryPanel(values=np.random.randint(10, size=(5, 50, 4)))
        too_many_types = qt.HistoryPanel(values=np.random.randint(10, size=(3, 50, 5)))
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          empty_hp,
                          on_spot_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          early_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          late_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          multi_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          too_many_shares,
                          on_spot_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          too_early_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          too_many_types,
                          on_spot_cash)
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          too_many_types,
                          on_spot_cash)

        # test the effect of data type sequence in strategy definition

    def test_operator_generate(self):
        """

        :return:
        """
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        test_sig = TestSigStrategy()
        self.op = qt.Operator(timing_types=[test_ls],
                              selecting_types=[test_sel],
                              ricon_types=[test_sig])
        self.assertIsInstance(self.op, qt.Operator, 'Operator Creation Error')
        self.op.set_parameter(stg_id='t-0',
                              pars={'000300': (5, 10.),
                                    '000400': (5, 10.),
                                    '000500': (5, 6.)})
        self.op.set_parameter(stg_id='s-0',
                              pars=())
        # 在所有策略的参数都设置好之前调用prepare_data会发生assertion Error
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          hist_data=self.hp1,
                          cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000))
        self.op.set_parameter(stg_id='r-0',
                              pars=(0.2, 0.02, -0.02))
        self.op.prepare_data(hist_data=self.hp1,
                             cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000))
        self.op.info()

        op_list = self.op.create_signal(hist_data=self.hp1)
        print(f'operation list is created: as following:\n {op_list}')
        self.assertTrue(isinstance(op_list, pd.DataFrame))
        self.assertEqual(op_list.shape, (23, 3))
        target_op_dates = ['2016/07/08', '2016/07/12', '2016/07/13', '2016/07/14',
                           '2016/07/18', '2016/07/26', '2016/07/27', '2016/07/28',
                           '2016/08/02', '2016/08/03', '2016/08/04', '2016/08/05',
                           '2016/08/08', '2016/08/10', '2016/08/18', '2016/08/24',
                           '2016/08/26', '2016/08/29', '2016/08/30', '2016/09/01',
                           '2016/09/05', '2016/09/06', '2016/09/08']
        target_op_values = np.array([[0.0, 1.0, 0.0],
                                     [0.5, -1.0, 0.0],
                                     [1.0, 0.0, 0.0],
                                     [0.0, 0.0, -1.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, -1.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, -1.0, 0.0],
                                     [0.0, 0.0, -1.0],
                                     [0.0, 1.0, 0.0],
                                     [-1.0, 0.0, 0.0],
                                     [0.0, 0.0, -1.0],
                                     [0.0, 0.0, 1.0],
                                     [-1.0, 0.0, 0.0],
                                     [0.0, 1.0, 1.0],
                                     [0.0, 1.0, 0.5],
                                     [0.0, -1.0, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, -1.0],
                                     [0.0, 1.0, 0.0]])
        target_op = pd.DataFrame(data=target_op_values, index=target_op_dates, columns=['000010', '000030', '000039'])
        target_op = target_op.rename(index=pd.Timestamp)
        print(f'target operation list is as following:\n {target_op}')
        dates_pairs = [[date1, date2, date1 == date2]
                       for date1, date2
                       in zip(target_op.index.strftime('%m-%d'), op_list.index.strftime('%m-%d'))]
        signal_pairs = [[list(sig1), list(sig2), all(sig1 == sig2)]
                        for sig1, sig2
                        in zip(list(target_op.values), list(op_list.values))]
        print(f'dates side by side:\n '
              f'{dates_pairs}')
        print(f'signals side by side:\n'
              f'{signal_pairs}')
        self.assertTrue(np.allclose(target_op.values, op_list.values))
        self.assertTrue(all([date1 == date2
                             for date1, date2
                             in zip(target_op.index.strftime('%m-%d'), op_list.index.strftime('%m-%d'))]))

    def test_operator_parameter_setting(self):
        """

        :return:
        """
        self.op.set_parameter('t-0',
                              pars=(5, 10, 5),
                              opt_tag=1,
                              par_boes=((5, 10), (5, 15), (10, 15)),
                              window_length=10,
                              data_types=['close', 'open', 'high'])
        self.op.set_parameter(stg_id='s-0',
                              pars=None,
                              opt_tag=1,
                              sample_freq='10d',
                              window_length=10,
                              data_types='close, open')
        self.op.set_parameter(stg_id='r-0',
                              pars=None,
                              opt_tag=0,
                              sample_freq='d',
                              window_length=20,
                              data_types='close, open')
        self.assertEqual(self.op.timing[0].pars, (5, 10, 5))
        self.assertEqual(self.op.timing[0].par_boes, ((5, 10), (5, 15), (10, 15)))

        self.assertEqual(self.op.op_data_freq, 'd')
        self.assertEqual(self.op.op_data_types, ['close', 'high', 'open'])
        self.assertEqual(self.op.opt_space_par,
                         ([(5, 10), (5, 15), (10, 15), (0, 1)], ['discr', 'discr', 'discr', 'conti']))
        self.assertEqual(self.op.max_window_length, 20)
        self.assertRaises(AssertionError, self.op.set_parameter, stg_id='t-1', pars=(1, 2))
        self.assertRaises(AssertionError, self.op.set_parameter, stg_id='t1', pars=(1, 2))
        self.assertRaises(AssertionError, self.op.set_parameter, stg_id=32, pars=(1, 2))

        self.op.set_blender('selecting', '0 and 1 or 2')
        self.op.set_blender('ls', 'str-1.2')
        self.assertEqual(self.op.ls_blender, 'str-1.2')
        self.assertEqual(self.op.selecting_blender, '0 and 1 or 2')
        self.assertEqual(self.op.selecting_blender_expr, ['or', 'and', '0', '1', '2'])
        self.assertEqual(self.op.ricon_blender, 'add')

        self.assertRaises(ValueError, self.op.set_blender, 'select', '0 and 1')
        self.assertRaises(TypeError, self.op.set_blender, 35, '0 and 1')

        self.assertEqual(self.op.opt_space_par,
                         ([(5, 10), (5, 15), (10, 15), (0, 1)], ['discr', 'discr', 'discr', 'conti']))
        self.assertEqual(self.op.opt_types, [1, 1, 0])

    def test_exp_to_blender(self):
        self.op.set_blender('selecting', '0 and 1 or 2')
        self.assertEqual(self.op.selecting_blender_expr, ['or', 'and', '0', '1', '2'])
        self.op.set_blender('selecting', '0 and ( 1 or 2 )')
        self.assertEqual(self.op.selecting_blender_expr, ['and', '0', 'or', '1', '2'])
        self.assertRaises(ValueError, self.op.set_blender, 'selecting', '0 and (1 or 2)')

    def test_set_opt_par(self):
        self.op.set_parameter('t-0',
                              pars=(5, 10, 5),
                              opt_tag=1,
                              par_boes=((5, 10), (5, 15), (10, 15)),
                              window_length=10,
                              data_types=['close', 'open', 'high'])
        self.op.set_parameter(stg_id='s-0',
                              pars=(0.5,),
                              opt_tag=0,
                              sample_freq='10d',
                              window_length=10,
                              data_types='close, open')
        self.op.set_parameter(stg_id='r-0',
                              pars=(9, -0.23),
                              opt_tag=1,
                              sample_freq='d',
                              window_length=20,
                              data_types='close, open')
        self.assertEqual(self.op.timing[0].pars, (5, 10, 5))
        self.assertEqual(self.op.selecting[0].pars, (0.5,))
        self.assertEqual(self.op.ricon[0].pars, (9, -0.23))
        self.assertEqual(self.op.opt_types, [1, 0, 1])
        self.op.set_opt_par((5, 12, 9, 8, -0.1))
        self.assertEqual(self.op.timing[0].pars, (5, 12, 9))
        self.assertEqual(self.op.selecting[0].pars, (0.5,))
        self.assertEqual(self.op.ricon[0].pars, (8, -0.1))

        self.assertRaises(ValueError, self.op.set_opt_par, (5, 12, 9, 8))

    def test_stg_attribute_get_and_set(self):
        self.stg = qt.TimingCrossline()
        self.stg_type = 'TIMING'
        self.stg_name = "CROSSLINE STRATEGY"
        self.stg_text = 'Moving average crossline strategy, determine long/short position according to the cross ' \
                        'point' \
                        ' of long and short term moving average prices '
        self.pars = None
        self.par_boes = [(10, 250), (10, 250), (1, 100), ('buy', 'sell', 'none')]
        self.par_count = 4
        self.par_types = ['discr', 'discr', 'conti', 'enum']
        self.opt_tag = 0
        self.data_types = ['close']
        self.data_freq = 'd'
        self.sample_freq = 'd'
        self.window_length = 270

        self.assertEqual(self.stg.stg_type, self.stg_type)
        self.assertEqual(self.stg.stg_name, self.stg_name)
        self.assertEqual(self.stg.stg_text, self.stg_text)
        self.assertEqual(self.stg.pars, self.pars)
        self.assertEqual(self.stg.par_types, self.par_types)
        self.assertEqual(self.stg.par_boes, self.par_boes)
        self.assertEqual(self.stg.par_count, self.par_count)
        self.assertEqual(self.stg.opt_tag, self.opt_tag)
        self.assertEqual(self.stg.data_freq, self.data_freq)
        self.assertEqual(self.stg.sample_freq, self.sample_freq)
        self.assertEqual(self.stg.data_types, self.data_types)
        self.assertEqual(self.stg.window_length, self.window_length)
        self.stg.stg_name = 'NEW NAME'
        self.stg.stg_text = 'NEW TEXT'
        self.assertEqual(self.stg.stg_name, 'NEW NAME')
        self.assertEqual(self.stg.stg_text, 'NEW TEXT')
        self.stg.pars = (1, 2, 3, 4)
        self.assertEqual(self.stg.pars, (1, 2, 3, 4))
        self.stg.par_count = 3
        self.assertEqual(self.stg.par_count, 3)
        self.stg.par_boes = [(1, 10), (1, 10), (1, 10), (1, 10)]
        self.assertEqual(self.stg.par_boes, [(1, 10), (1, 10), (1, 10), (1, 10)])
        self.stg.par_types = ['conti', 'conti', 'discr', 'enum']
        self.assertEqual(self.stg.par_types, ['conti', 'conti', 'discr', 'enum'])
        self.stg.par_types = 'conti, conti, discr, conti'
        self.assertEqual(self.stg.par_types, ['conti', 'conti', 'discr', 'conti'])
        self.stg.data_types = 'close, open'
        self.assertEqual(self.stg.data_types, ['close', 'open'])
        self.stg.data_types = ['close', 'high', 'low']
        self.assertEqual(self.stg.data_types, ['close', 'high', 'low'])
        self.stg.data_freq = 'w'
        self.assertEqual(self.stg.data_freq, 'w')
        self.stg.window_length = 300
        self.assertEqual(self.stg.window_length, 300)

    def test_rolling_timing(self):
        stg = TestLSStrategy()
        stg_pars = {'000100': (5, 10),
                    '000200': (5, 10),
                    '000300': (5, 6)}
        stg.set_pars(stg_pars)
        history_data = self.hp1.values
        output = stg.generate(hist_data=history_data)

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[0., 0., 1.],
                           [0., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 0., 1.],
                           [1., 1., 1.],
                           [1., 1., 0.],
                           [1., 1., 1.],
                           [1., 1., 0.],
                           [1., 1., 0.],
                           [1., 1., 0.],
                           [1., 0., 0.],
                           [1., 0., 0.],
                           [1., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 0.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 0., 1.],
                           [0., 0., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.]])
        # debug
        # print(f'output is\n{output}\n and lsmask target is\n{lsmask}')
        # TODO: Issue to be solved: the np.nan value are converted to 0 in the lsmask，这样做可能会有意想不到的后果
        # TODO: 需要解决nan值的问题
        self.assertEqual(output.shape, lsmask.shape)
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

    def test_sel_timing(self):
        stg = TestSelStrategy()
        stg_pars = ()
        stg.set_pars(stg_pars)
        history_data = self.hp1['high, low, close', :, :]
        seg_pos, seg_length, seg_count = stg._seg_periods(dates=self.hp1.hdates, freq=stg.sample_freq)
        self.assertEqual(list(seg_pos), [0, 5, 11, 19, 26, 33, 41, 47, 49])
        self.assertEqual(list(seg_length), [5, 6, 8, 7, 7, 8, 6, 2])
        self.assertEqual(seg_count, 8)

        output = stg.generate(hist_data=history_data, shares=self.hp1.shares, dates=self.hp1.hdates)

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0]])
        # # debug
        # print(f'output is\n{pd.DataFrame(output)}\n and sel_mask target is\n{pd.DataFrame(selmask)}')

        self.assertEqual(output.shape, selmask.shape)
        self.assertTrue(np.allclose(output, selmask))

    def test_simple_timing(self):
        stg = TestSigStrategy()
        stg_pars = (0.2, 0.02, -0.02)
        stg.set_pars(stg_pars)
        history_data = self.hp1['close, open, high, low', :, 3:50]
        output = stg.generate(hist_data=history_data, shares=self.shares, dates=self.date_indices)

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0]])

        # debug
        # print(f'the output is \n{pd.DataFrame(output)}\nand signal matrix is \n{pd.DataFrame(sigmatrix)}')
        side_by_side_array = np.array([[i, out_line, sig_line]
                                       for
                                       i, out_line, sig_line
                                       in zip(range(len(output)), output, sigmatrix)])
        print(f'output and signal matrix lined up side by side is \n'
              f'{side_by_side_array}')
        self.assertEqual(sigmatrix.shape, output.shape)
        self.assertTrue(np.allclose(output, sigmatrix))


class TestLog(unittest.TestCase):
    def test_init(self):
        pass


class TestContext(unittest.TestCase):
    def test_init(self):
        pass


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
        self.data4 = np.random.randint(10, size=(10))
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.htypes, rows=self.index)
        self.hp2 = qt.HistoryPanel(values=self.data2, levels=self.shares, columns='close', rows=self.index)
        self.hp3 = qt.HistoryPanel(values=self.data3, levels='000100', columns=self.htypes, rows=self.index2)
        self.hp4 = qt.HistoryPanel(values=self.data4, levels='000100', columns='close', rows=self.index3)
        self.hp5 = qt.HistoryPanel(values=self.data)
        self.hp6 = qt.HistoryPanel(values=self.data, levels=self.shares, rows=self.index3)

    def test_create_history_panel(self):
        """ test the creation of a HistoryPanel object by passing all data explicitly

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

        # Error testing during HistoryPanel creating
        # shape does not match
        self.assertRaises(AssertionError,
                          qt.HistoryPanel,
                          self.data,
                          levels=self.shares, columns='close', rows=self.index)
        # valus is not np.ndarray
        self.assertRaises(AssertionError,
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
        self.assertTrue(np.allclose(self.hp['close'], self.data[:, :, 0:1]))
        self.assertTrue(np.allclose(self.hp['close,open'], self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp[['close', 'open']], self.data[:, :, 0:2]))
        self.assertTrue(np.allclose(self.hp['close:high'], self.data[:, :, 0:3]))
        self.assertTrue(np.allclose(self.hp['close,high'], self.data[:, :, [0, 2]]))
        self.assertTrue(np.allclose(self.hp[:, '000100'], self.data[0:1, :, ]))
        self.assertTrue(np.allclose(self.hp[:, '000100,000101'], self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:, ['000100', '000101']], self.data[0:2, :]))
        self.assertTrue(np.allclose(self.hp[:, '000100:000102'], self.data[0:3, :]))
        self.assertTrue(np.allclose(self.hp[:, '000100,000102'], self.data[[0, 2], :]))
        self.assertTrue(np.allclose(self.hp['close,open', '000100,000102'], self.data[[0, 2], :, 0:2]))
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
        self.assertTrue(np.allclose(hp['close', :, :], data[:, :, 0:1], equal_nan=True))
        print(f'==========================\n输出close和open类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1], :, :], data[:, :, 0:2], equal_nan=True))
        print(f'==========================\n输出第一只股票的所有类型历史数据\n')
        self.assertTrue(np.allclose(hp[:, [0], :], data[0:1, :, :], equal_nan=True))
        print('==========================\n输出第0、1、2个htype对应的所有股票全部历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1, 2]], data[:, :, 0:3], equal_nan=True))
        print('==========================\n输出close、high两个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp[['close', 'high']], data[:, :, [0, 2]], equal_nan=True))
        print('==========================\n输出0、1两个htype的所有历史数据\n')
        self.assertTrue(np.allclose(hp[[0, 1]], data[:, :, 0:2], equal_nan=True))
        print('==========================\n输出close、high两个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close,high'], data[:, :, [0, 2]], equal_nan=True))
        print('==========================\n输出close起到high止的三个类型的所有历史数据\n')
        self.assertTrue(np.allclose(hp['close:high'], data[:, :, 0:3], equal_nan=True))
        print('==========================\n输出0、1、3三个股票的全部历史数据\n')
        self.assertTrue(np.allclose(hp[:, [0, 1, 3]], data[[0, 1, 3], :, :], equal_nan=True))
        print('==========================\n输出000100、000102两只股票的所有历史数据\n')
        self.assertTrue(np.allclose(hp[:, ['000100', '000102']], data[[0, 2], :, :], equal_nan=True))
        print('==========================\n输出0、1、2三个股票的历史数据\n', hp[:, 0: 3])
        self.assertTrue(np.allclose(hp[:, 0: 3], data[0:3, :, :], equal_nan=True))
        print('==========================\n输出000100、000102两只股票的所有历史数据\n')
        self.assertTrue(np.allclose(hp[:, '000100, 000102'], data[[0, 2], :, :], equal_nan=True))
        print('==========================\n输出所有股票的0-7日历史数据\n')
        self.assertTrue(np.allclose(hp[:, :, 0:8], data[:, 0:8, :], equal_nan=True))
        print('==========================\n输出000100股票的0-7日历史数据\n')
        self.assertTrue(np.allclose(hp[:, '000100', 0:8], data[0, 0:8, :], equal_nan=True))
        print('==========================\nstart testing multy axis slicing of HistoryPanel object')
        print('==========================\n输出000100、000120两只股票的close、open两组历史数据\n',
              hp['close,open', ['000100', '000102']])
        print('==========================\n输出000100、000120两只股票的close到open三组历史数据\n',
              hp['close,open', '000100, 000102'])
        print(f'historyPanel: hp:\n{hp}')
        print(f'data is:\n{data}')
        hp.htypes = 'open,high,low,close'
        hp.info()
        hp.shares = ['000300', '600227', '600222', '000123', '000129']
        hp.info()

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
        pass

    def test_hdf_to_hp(self):
        pass

    def test_hp_join(self):
        print(f'join two simple HistoryPanels with same shares')
        temp_hp = self.hp.join(self.hp2, same_shares=True)
        self.assertIsInstance(temp_hp, qt.HistoryPanel)

    def test_df_to_hp(self):
        print(f'test converting DataFrame to HistoryPanel')
        data = np.random.randint(10, size=(10, 5))
        df1 = pd.DataFrame(data)
        df2 = pd.DataFrame(data, columns=qt.str_to_list(self.shares))
        df3 = pd.DataFrame(data[:, 0:4])
        df4 = pd.DataFrame(data[:, 0:4], columns=qt.str_to_list(self.htypes))
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
        self.assertEqual(hp.shares, qt.str_to_list(self.shares))
        self.assertEqual(hp.htypes, ['close'])
        hp = qt.dataframe_to_hp(df3, shares='000100', column_type='htypes')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, ['000100'])
        self.assertEqual(hp.htypes, [0, 1, 2, 3])
        hp = qt.dataframe_to_hp(df4, shares='000100', htypes=self.htypes, column_type='htypes')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, ['000100'])
        self.assertEqual(hp.htypes, qt.str_to_list(self.htypes))
        hp.info()
        self.assertRaises(KeyError, qt.dataframe_to_hp, df1)

    def test_to_dataframe(self):
        """ 测试HistoryPanel对象的to_dataframe方法

        """
        print(f'START TEST == test_to_dataframe')
        print(f'test converting test hp to dataframe with share == "000102":')
        df_test = self.hp.to_dataframe(share='000102')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.htypes), list(df_test.columns))
        self.assertTrue(np.allclose(self.hp[:, '000102'], df_test.values))

        print(f'test DataFrame conversion with share == "000100"')
        df_test = self.hp.to_dataframe(share='000100')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.htypes), list(df_test.columns))
        self.assertTrue(np.allclose(self.hp[:, '000100'], df_test.values))

        print(f'test DataFrame conversion error: type incorrect')
        self.assertRaises(AssertionError, self.hp.to_dataframe, share=3)

        print(f'test DataFrame error raising with share not found error')
        self.assertRaises(KeyError, self.hp.to_dataframe, share='000300')

        print(f'test DataFrame conversion with htype == "close"')
        df_test = self.hp.to_dataframe(htype='close')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        self.assertTrue(np.allclose(self.hp['close'].T, df_test.values))

        print(f'test DataFrame conversion with htype == "high"')
        df_test = self.hp.to_dataframe(htype='high')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        self.assertTrue(np.allclose(self.hp['high'].T, df_test.values))

        print(f'test DataFrame conversion error: type incorrect')
        self.assertRaises(AssertionError, self.hp.to_dataframe, htype=pd.DataFrame())

        print(f'test DataFrame error raising with share not found error')
        self.assertRaises(KeyError, self.hp.to_dataframe, htype='non_type')

        print(f'Raises ValueError when both or none parameter is given')
        self.assertRaises(KeyError, self.hp.to_dataframe)
        self.assertRaises(KeyError, self.hp.to_dataframe, share='000100', htype='close')

    def test_to_csv(self):
        pass

    def test_to_hdf(self):
        pass

    def test_fill_na(self):
        print(self.hp)
        new_values = self.hp.values.astype(float)
        new_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = np.nan
        print(new_values)
        temp_hp = qt.HistoryPanel(values=new_values, levels=self.hp.levels, rows=self.hp.rows, columns=self.hp.columns)
        self.assertTrue(np.allclose(temp_hp.values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]], np.nan, equal_nan=True))
        temp_hp.fillna(2.3)
        new_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = 2.3
        self.assertTrue(np.allclose(temp_hp.values,
                                    new_values, equal_nan=True))


class TestHistorySubFuncs(unittest.TestCase):
    def setUp(self):
        pass

    def test_str_to_list(self):
        self.assertEqual(qt.str_to_list('a,b,c,d,e'), ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(qt.str_to_list('a, b, c '), ['a', 'b', 'c'])
        self.assertEqual(qt.str_to_list('a, b: c', sep_char=':'), ['a,b', 'c'])

    def test_list_or_slice(self):
        str_dict = {'close': 0, 'open': 1, 'high': 2, 'low': 3}
        self.assertEqual(qt.list_or_slice(slice(1, 2, 1), str_dict), slice(1, 2, 1))
        self.assertEqual(qt.list_or_slice('open', str_dict), [1])
        self.assertEqual(list(qt.list_or_slice('close, high, low', str_dict)), [0, 2, 3])
        self.assertEqual(list(qt.list_or_slice('close:high', str_dict)), [0, 1, 2])
        self.assertEqual(list(qt.list_or_slice(['open'], str_dict)), [1])
        self.assertEqual(list(qt.list_or_slice(['open', 'high'], str_dict)), [1, 2])
        self.assertEqual(list(qt.list_or_slice(0, str_dict)), [0])
        self.assertEqual(list(qt.list_or_slice([0, 2], str_dict)), [0, 2])
        self.assertEqual(list(qt.list_or_slice([True, False, True, False], str_dict)), [0, 2])

    def test_label_to_dict(self):
        target_list = [0, 1, 10, 100]
        target_dict = {'close': 0, 'open': 1, 'high': 2, 'low': 3}
        target_dict2 = {'close': 0, 'open': 2, 'high': 1, 'low': 3}
        self.assertEqual(qt.labels_to_dict('close, open, high, low', target_list), target_dict)
        self.assertEqual(qt.labels_to_dict(['close', 'open', 'high', 'low'], target_list), target_dict)
        self.assertEqual(qt.labels_to_dict('close, high, open, low', target_list), target_dict2)
        self.assertEqual(qt.labels_to_dict(['close', 'high', 'open', 'low'], target_list), target_dict2)

    def test_stack_dataframes(self):
        print('test stack dataframes')
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

        hp1 = qt.stack_dataframes([df1, df2, df3], stack_along='shares',
                                  shares=['000100', '000200', '000300'])
        hp2 = qt.stack_dataframes([df1, df2, df3], stack_along='shares',
                                  shares='000100, 000300, 000200')
        print('hp1 is:\n', hp1)
        print('hp2 is:\n', hp2)
        self.assertEqual(hp1.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp1.shares, ['000100', '000200', '000300'])
        self.assertTrue(np.allclose(hp1.values, values1, equal_nan=True))
        self.assertEqual(hp2.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp2.shares, ['000100', '000300', '000200'])
        self.assertTrue(np.allclose(hp2.values, values1, equal_nan=True))

        hp3 = qt.stack_dataframes([df1, df2, df3], stack_along='htypes',
                                  htypes=['close', 'high', 'low'])
        hp4 = qt.stack_dataframes([df1, df2, df3], stack_along='htypes',
                                  htypes='open, close, high')
        print('hp3 is:\n', hp3.values)
        print('hp4 is:\n', hp4.values)
        self.assertEqual(hp3.htypes, ['close', 'high', 'low'])
        self.assertEqual(hp3.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp3.values, values2, equal_nan=True))
        self.assertEqual(hp4.htypes, ['open', 'close', 'high'])
        self.assertEqual(hp4.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp4.values, values2, equal_nan=True))

    def test_regulate_date_format(self):
        self.assertEqual(qt.regulate_date_format('2019/11/06'), '20191106')
        self.assertEqual(qt.regulate_date_format('2019-11-06'), '20191106')
        self.assertEqual(qt.regulate_date_format('20191106'), '20191106')
        self.assertEqual(qt.regulate_date_format('191106'), '20061119')
        self.assertEqual(qt.regulate_date_format('830522'), '19830522')
        self.assertEqual(qt.regulate_date_format(datetime.datetime(2010, 3, 15)), '20100315')
        self.assertEqual(qt.regulate_date_format(pd.Timestamp('2010.03.15')), '20100315')
        self.assertRaises(ValueError, qt.regulate_date_format, 'abc')
        self.assertRaises(ValueError, qt.regulate_date_format, '2019/13/43')
        self.assertRaises(TypeError, qt.regulate_date_format, 123)

    def test_list_to_str_format(self):
        self.assertEqual(qt.list_to_str_format(['close', 'open', 'high', 'low']),
                         'close,open,high,low')
        self.assertEqual(qt.list_to_str_format(['letters', '  ', '123  4', 123, '   kk  l']),
                         'letters,,1234,kkl')
        self.assertEqual(qt.list_to_str_format('a string input'),
                         'a,string,input')
        self.assertEqual(qt.list_to_str_format('already,a,good,string'),
                         'already,a,good,string')
        self.assertRaises(AssertionError, qt.list_to_str_format, 123)


class TestTushare(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_price_type_raw_data(self):
        pass

    def test_get_financial_report_type_raw_data(self):
        pass

    def test_get_composite_type_raw_data(self):
        pass

    def test_stock_basic(self):
        pass

    def test_trade_calendar(self):
        pass

    def test_name_change(self):
        pass

    def test_new_share(self):
        pass

    def test_stock_company(self):
        pass

    def test_get_bar(self):
        pass

    def test_get_index(self):
        pass

    def test_income(self):
        pass

    def test_balance(self):
        pass

    def test_cash_flow(self):
        pass

    def test_indicators(self):
        pass

    def test_top_list(self):
        pass

    def test_index_basic(self):
        pass

    def test_composit(self):
        pass

    def test_fund_net_value(self):
        pass

    def test_future_basic(self):
        pass

    def test_options_basic(self):
        pass

    def test_future_daily(self):
        pass

    def test_options_daily(self):
        pass


class TestTAFuncs(unittest.TestCase):
    def setUp(self):
        pass

    def test_bbands(self):
        pass


class TestQT(unittest.TestCase):
    """对qteasy系统进行总体测试"""

    def setUp(self):
        self.op = qt.Operator(timing_types=['DMA', 'DMA'],
                              selecting_types=['simple'],
                              ricon_types=['Urgent'])
        self.cont = qt.Context(moq=0)
        print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
        self.op.set_parameter('s-0', pars=(2,), sample_freq='y')
        self.op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('t-1', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        # self.op.set_parameter('t-2', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('r-0', opt_tag=1, par_boes=[(5, 14), (-0.2, 0)])
        # print('CREATE CONTEXT OBJECT\n=======================')

        self.cont.reference_asset = '000300.SH'
        self.cont.reference_asset_type = 'I'
        self.cont.share_pool = '000300.SH'
        self.cont.asset_type = 'I'
        self.cont.output_count = 50
        self.cont.invest_start = '20020101'
        self.cont.moq = 1
        # print(cont)
        # print(f'TRANSACTION RATE OBJECT CREATED, RATE IS: \n==========================\n{cont.rate}')

        timing_pars1 = (94, 36, 107)
        timing_pars2 = {'000100': (77, 118, 144),
                        '000200': (75, 128, 138),
                        '000300': (73, 120, 143)}
        timing_pars3 = (98, 177, 158)
        timing_pars4 = (37, 44)
        print('START TO SET TIMING PARAMETERS TO STRATEGIES: \n===================')
        self.op.set_blender('ls', 'avg')
        self.op.set_parameter(stg_id='t-0', pars=timing_pars1)
        self.op.set_parameter(stg_id='t-1', pars=timing_pars3)
        # self.op.set_parameter(stg_id='t-2', pars=timing_pars1)
        # op.set_parameter(stg_id='t-2', pars=timing_pars4, opt_tag=1, par_boes=[(90, 100), (700, 100)])
        # op.set_parameter('t-3', pars=timing_pars1)
        print('START TO SET RICON PARAMETERS TO STRATEGIES:\n===================')
        self.op.set_parameter('r-0', pars=(6, -0.06))
        # op.info()
        # print('\nTime of creating operation list:')
        # op.info()
        print(f'\n START QT RUNNING\n===========================\n')
        self.cont.parallel = True
        self.cont.print_log = True

    def test_run_mode_0(self):
        """测试策略的实时信号生成模式"""
        self.cont.mode = 0
        qt.run(self.op, self.cont)

    def test_run_mode_1(self):
        """测试策略的回测模式"""
        self.cont.mode = 1
        qt.run(self.op, self.cont)

    def test_run_mode_2(self):
        """测试策略的优化模式"""
        self.cont.mode = 2
        self.cont.opti_method = 1
        self.cont.opti_method_sample_size = 10
        self.cont.opti_method_step_size = 32
        self.cont.opti_method_init_step_size = 16
        self.cont.opti_method_min_step_size = 1
        self.cont.opti_method_incre_ratio = 2
        qt.run(self.op, self.cont)

    def test_built_in_strategies(self):
        pass


class TestVisual(unittest.TestCase):
    """ Test the visual effects and charts

    """

    def test_ohlc(self):
        qt.ohlc('513100.SH', start='2020-04-01', asset_type='FD', no_visual=True)

    def test_candle(self):
        qt.candle('513100.SH', start='2020-04-01', asset_type='FD', no_visual=True)

    def test_renko(self):
        qt.renko('513100.SH', start='2020-04-01', asset_type='FD', no_visual=True)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestCost())
    suite.addTest(TestSpace())
    suite.addTests(tests=[TestLog(), TestContext(), TestOperator()])
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(test_suite())