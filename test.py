import unittest
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np
from numpy import int64
import itertools


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
        self.oplist = []
        self.reference = []
        self.valuelist = []

    def test_operation(self):
        pass

    def test_fv(self):
        pass

    def test_max_drawdown(self):
        pass

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


class TestOperator(unittest.TestCase):
    """全面测试Operator对象的所有功能。包括：

        1，
    """

    def setUp(self):
        """prepare data for Operator test"""
        print('start testing HistoryPanel object\n')

        # build up test data: a 4-type, 3-share, 50-day matrix of prices that contains nan values in some days
        # for some share_pool

        # for share1:
        DATA_ROWS = 50

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
                        5.91, 6.23, 6.28, 6.28, 6.27, 5.7, 5.56, 5.67, 5.16, 5.69, 6.32, 6.14, 6.25,
                        5.79, 5.26, 5.05, 5.45, 6.06, 6.21, 5.69, 5.46, 6.02, 6.69, 7.43, 7.72, 8.16,
                        7.83, 8.7, 8.71, 8.88, 8.54, 8.87, 8.87, 8.18, 7.8, 7.97, 8.25]
        share3_open = [7.26, 7, 6.88, 6.91, np.nan, 6.81, 6.63, 6.45, 6.16, 6.24, 5.96, 5.97, 5.96,
                       6.2, 6.35, 6.11, 6.37, 5.58, 5.65, 5.65, 5.19, 5.42, 6.3, 6.15, 6.05, 5.89,
                       5.22, 5.2, 5.07, 6.04, 6.12, 5.85, 5.67, 6.02, 6.04, 7.07, 7.64, 7.99, 7.59,
                       8.73, 8.72, 8.97, 8.58, 8.71, 8.77, 8.4, 7.95, 7.76, 8.25, 7.51]
        share3_high = [7.41, 7.31, 7.14, 7, np.nan, 6.82, 6.96, 6.85, 6.5, 6.34, 6.04, 6.02, 6.12, 6.38,
                       6.43, 6.46, 6.43, 6.27, 5.77, 6.01, 5.67, 5.67, 6.35, 6.32, 6.43, 6.36, 5.79,
                       5.47, 5.65, 6.04, 6.14, 6.23, 5.83, 6.25, 6.27, 7.12, 7.82, 8.14, 8.27, 8.92,
                       8.76, 9.15, 8.9, 9.01, 9.16, 9, 8.27, 7.99, 8.33, 8.25]
        share3_low = [6.53, 6.87, 6.83, 6.7, np.nan, 6.63, 6.57, 6.41, 6.15, 6.07, 5.89, 5.82, 5.73, 5.81,
                      6.1, 6.06, 6.16, 5.57, 5.54, 5.51, 5.19, 5.12, 5.69, 6.01, 5.97, 5.86, 5.18, 5.19,
                      4.96, 5.45, 5.84, 5.85, 5.28, 5.42, 6.02, 6.69, 7.28, 7.64, 7.25, 7.83, 8.41, 8.66,
                      8.53, 8.54, 8.73, 8.27, 7.95, 7.67, 7.8, 7.51]

        date_indices = ['2016-07-01', '2016-07-04', '2016-07-05', '2016-07-06',
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

        shares = ['000010', '000030', '000039']

        types = ['close', 'open', 'high', 'low']

        self.test_data_3D = np.zeros((3, DATA_ROWS, 4))
        self.test_data_2D = np.zeros((DATA_ROWS, 3))
        self.test_data_2D2 = np.zeros((DATA_ROWS, 4))

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

        self.hp1 = qt.HistoryPanel(values=self.test_data_3D, levels=shares, columns=types, rows=date_indices)
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
        pass

    def test_operator_generate(self):
        """

        :return:
        """
        self.op = qt.Operator(timing_types=['DMA'], selecting_types=['simple'], ricon_types=['urgent'])
        self.assertIsInstance(self.op, qt.Operator, 'Operator Creation Error')

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


class TestStrategy(unittest.TestCase):
    def setUp(self):
        self.stg = qt.TimingCrossline()
        self.stg_type = 'TIMING'
        self.stg_name = "CROSSLINE STRATEGY"
        self.stg_text = 'Moving average crossline strategy, determin long/short position according to the cross point ' \
                        '' \
                        '' \
                        '' \
                        '' \
                        '' \
                        '' \
                        '' \
                        '' \
                        'of long and short term moving average prices '
        self.pars = None
        self.par_boes = [(10, 250), (10, 250), (1, 100), ('buy', 'sell', 'none')]
        self.par_count = 4
        self.par_types = ['discr', 'discr', 'conti', 'enum']
        self.opt_tag = 0
        self.data_types = ['close']
        self.data_freq = 'd'
        self.sample_freq = 'd'
        self.window_length = 270

    def test_attribute_get_and_set(self):
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
        self.shares = '000100,000101,000102,000103,000104'
        self.htypes = 'close,open,high,low'
        self.data2 = np.random.randint(10, size=(10, 5))
        self.data3 = np.random.randint(10, size=(10, 4))
        self.data4 = np.random.randint(10, size=(10))
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.htypes, rows=self.index)
        self.hp2 = qt.HistoryPanel(values=self.data2, levels=self.shares, columns='close', rows=self.index)
        self.hp3 = qt.HistoryPanel(values=self.data3, levels='000100', columns=self.htypes, rows=self.index)
        self.hp4 = qt.HistoryPanel(values=self.data4, levels='000100', columns='close', rows=self.index)

    def create_history_panel(self):
        """ test the creation of a HistoryPanel object by passing all data explicitly

        """
        self.assertIsInstance(self.hp, qt.HistoryPanel)
        self.assertEqual(self.hp.shape[0], 5)
        self.assertEqual(self.hp.shape[1], 10)
        self.assertEqual(self.hp.shape[2], 4)
        self.assertEqual(self.hp.level_count, 5)
        self.assertEqual(self.hp.row_count, 11)
        self.assertEqual(self.hp.column_count, 4)
        self.assertEqual(list(self.hp.levels.keys), self.shares.split())
        self.assertEqual(list(self.hp.columns.keys), self.htypes.split())

        self.assertIsInstance(self.hp2, qt.HistoryPanel)
        self.assertEqual(self.hp2.shape[0], 5)
        self.assertEqual(self.hp2.shape[1], 10)
        self.assertEqual(self.hp2.shape[2], 4)
        self.assertEqual(self.hp2.level_count, 5)
        self.assertEqual(self.hp2.row_count, 11)
        self.assertEqual(self.hp2.column_count, 4)
        self.assertEqual(list(self.hp2.levels.keys), self.shares.split())
        self.assertEqual(list(self.hp2.columns.keys), self.htypes.split())

        self.assertIsInstance(self.hp3, qt.HistoryPanel)
        self.assertEqual(self.hp3.shape[0], 5)
        self.assertEqual(self.hp3.shape[1], 10)
        self.assertEqual(self.hp3.shape[2], 4)
        self.assertEqual(self.hp3.level_count, 5)
        self.assertEqual(self.hp3.row_count, 11)
        self.assertEqual(self.hp3.column_count, 4)
        self.assertEqual(list(self.hp3.levels.keys), self.shares.split())
        self.assertEqual(list(self.hp3.columns.keys), self.htypes.split())

        self.assertIsInstance(self.hp4, qt.HistoryPanel)
        self.assertEqual(self.hp4.shape[0], 5)
        self.assertEqual(self.hp4.shape[1], 10)
        self.assertEqual(self.hp4.shape[2], 4)
        self.assertEqual(self.hp4.level_count, 5)
        self.assertEqual(self.hp4.row_count, 11)
        self.assertEqual(self.hp4.column_count, 4)
        self.assertEqual(list(self.hp4.levels.keys), self.shares.split())
        self.assertEqual(list(self.hp4.columns.keys), self.htypes.split())

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

    def test_csv_to_hp(self):
        pass

    def test_hdf_to_hp(self):
        pass

    def test_hp_join(self):
        pass

    def test_df_to_hp(self):
        pass

    def test_to_dataframe(self):
        pass

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
        self.assertTrue(np.allclose(hp1.values, values1, equal_nan=True), True)
        self.assertEqual(hp2.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp2.shares, ['000100', '000300', '000200'])
        self.assertTrue(np.allclose(hp2.values, values1, equal_nan=True), True)

        hp3 = qt.stack_dataframes([df1, df2, df3], stack_along='htypes',
                                  htypes=['close', 'high', 'low'])
        hp4 = qt.stack_dataframes([df1, df2, df3], stack_along='htypes',
                                  htypes='open, close, high')
        print('hp3 is:\n', hp3.values)
        print('hp4 is:\n', hp4.values)
        self.assertEqual(hp3.htypes, ['close', 'high', 'low'])
        self.assertEqual(hp3.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp3.values, values2, equal_nan=True), True)
        self.assertEqual(hp4.htypes, ['open', 'close', 'high'])
        self.assertEqual(hp4.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp4.values, values2, equal_nan=True), True)

    def test_regulate_date_format(self):
        self.assertEqual(qt.regulate_date_format('2019/11/06'), '20191106')
        self.assertEqual(qt.regulate_date_format('2019-11-06'), '20191106')
        self.assertEqual(qt.regulate_date_format('20191106'), '20191106')
        self.assertEqual(qt.regulate_date_format('191106'), '20061119')
        self.assertEqual(qt.regulate_date_format('830522'), '19830522')

    def test_list_to_str_format(self):
        self.assertEqual(qt.list_to_str_format(['close', 'open', 'high', 'low']),
                         'close,open,high,low')
        self.assertEqual(qt.list_to_str_format(['letters', '  ', '123  4', 123, '   kk  l']),
                         'letter,,1234,kkl')
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestCost())
    suite.addTest(TestSpace())
    suite.addTests(tests=[TestLog(), TestContext(), TestOperator()])
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(test_suite())