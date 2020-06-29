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

    def test_space_around_centre(self):
        pass

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
        pass

    def test_blend(self):
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
        pass

    def test_timing_blend_change(self):
        pass


class TestOperator(unittest.TestCase):
    def setUp(self):
        print('start testing HistoryPanel object\n')
        self.data = np.random.randint(10, size=(5, 10, 4))
        self.index = pd.date_range(start='20200101', freq='d', periods=10)
        self.shares = '000100,000101,000102,000103,000104'
        self.dtypes = 'close,open,high,low'
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.dtypes, rows=self.index)

    def create_test_data(self):
        # build up test data: a 4-type, 3-share, 21-day matrix of prices that contains nan values in some days
        # for some share_pool

        # for share1:
        share1_close = [7.74, 7.83, 7.79, 7.93, 7.84, 7.83, 7.77, 7.84, 7.86, 7.92, 7.84,
                        7.83, 7.85, 8.14, 8.05, 8., 8.07, 8.1, 7.74, 7.71, 7.69]
        share1_open = [7.88, 7.93, 7.86, 7.95, 7.92, 7.95, 8.01, 7.87, 7.88, 7.94, 7.93,
                       7.88, 7.86, 8.43, 8.2, 8.19, 8.12, 8.15, 8.19, 7.79, 7.93]
        share1_high = [7.88, 7.93, 7.86, 7.95, 7.92, 7.95, 8.01, 7.87, 7.88, 7.94, 7.93,
                       7.88, 7.86, 8.43, 8.2, 8.19, 8.12, 8.15, 8.19, 7.79, 7.93]
        share1_low = [7.68, 7.66, 7.76, 7.76, 7.75, 7.79, 7.76, 7.65, 7.81, 7.79, 7.81,
                      7.7, 7.74, 7.82, 8., 7.97, 7.93, 8.01, 7.6, 7.58, 7.67]

        # for share2:
        share2_close = [6.98, 7.1, 7.14, 7.12, 7.1, 7.1, 7.11, 7.32, 7.36, np.nan, np.nan,
                        np.nan, np.nan, np.nan, np.nan, np.nan, 7.58, 7.97, 7.47, 7.75, 7.51]
        share2_open = [7.04, 6.94, 7.11, 7.14, 7.1, 7.11, 7.11, 7.11, 7.29, np.nan, np.nan,
                       np.nan, np.nan, np.nan, np.nan, np.nan, 7.8, 7.43, 7.9, 7.43, 7.7]
        share2_high = [7.06, 7.13, 7.15, 7.15, 7.14, 7.21, 7.27, 7.33, 7.39, np.nan, np.nan,
                       np.nan, np.nan, np.nan, np.nan, np.nan, 7.8, 8.11, 7.93, 7.8, 7.74]
        share2_low = [6.94, 6.94, 7.06, 7.05, 7.03, 7.06, 7.07, 7.1, 7.26, np.nan, np.nan,
                      np.nan, np.nan, np.nan, np.nan, np.nan, 7.37, 7.43, 7.33, 7.38, 7.44]

        # for share3:
        share3_close = [13.89, 14.13, 14.27, np.nan, np.nan, 14.53, 14.25, 14.56, 14.61,
                        14.61, 14.01, 13.85, 13.93, 14.00, 13.98, 13.85, 13.85, 13.99,
                        13.64, 13.82, 13.71]
        share3_open = [13.92, 13.85, 14.14, np.nan, np.nan, 14.38, 14.39, 14.26, 14.69,
                       14.68, 14.12, 13.99, 13.85, 14.02, 14., 13.95, 13.85, 13.86,
                       13.99, 13.63, 13.82]
        share3_high = [14.02, 14.16, 14.47, np.nan, np.nan, 14.8, 14.51, 14.58, 14.73,
                       14.77, 14.22, 13.99, 13.96, 14.04, 14.06, 14.08, 13.95, 14.01,
                       14.13, 13.84, 13.83]
        share3_low = [13.8, 13.8, 14.11, np.nan, np.nan, 14.15, 14.24, 14.14, 14.48,
                      14.5, 13.94, 13.79, 13.8, 13.91, 13.95, 13.83, 13.76, 13.8,
                      13.46, 13.58, 13.68]

        date_indices = ['2016-07-01', '2016-07-04', '2016-07-05', '2016-07-06',
                        '2016-07-07', '2016-07-08', '2016-07-11', '2016-07-12',
                        '2016-07-13', '2016-07-14', '2016-07-15', '2016-07-18',
                        '2016-07-19', '2016-07-20', '2016-07-21', '2016-07-22',
                        '2016-07-25', '2016-07-26', '2016-07-27', '2016-07-28',
                        '2016-07-29']

        shares = ['000010', '000030', '000039']

        types = ['close', 'open', 'high', 'low']

        self.test_data_3D = np.zeros((3, 4, 21))
        self.test_data_2D = np.zeros((3, 21))

        # Build up 3D data
        self.test_data_3D[0, 0, :] = share1_close
        self.test_data_3D[0, 1, :] = share1_open
        self.test_data_3D[0, 2, :] = share1_high
        self.test_data_3D[0, 3, :] = share1_low

        self.test_data_3D[1, 0, :] = share2_close
        self.test_data_3D[1, 1, :] = share2_open
        self.test_data_3D[1, 2, :] = share2_high
        self.test_data_3D[1, 3, :] = share2_low

        self.test_data_3D[2, 0, :] = share3_close
        self.test_data_3D[2, 1, :] = share3_open
        self.test_data_3D[2, 2, :] = share3_high
        self.test_data_3D[2, 3, :] = share3_low

        # Build up 2D data
        self.test_data_2D[0, :] = share1_close
        self.test_data_2D[1, :] = share2_close
        self.test_data_2D[2, :] = share3_close

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
        print('testing operator objects')
        self.op = qt.Operator(timing_types=['DMA'], selecting_types=['simple', 'random'], ricon_types=['urgent'])
        self.op.set_parameter('s-1', (0.5,))
        self.assertEqual(self.op.selecting[1].pars, (0.5,))

    def test_exp_to_blender(self):
        pass


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
        self.dtypes = 'close,open,high,low'
        self.hp = qt.HistoryPanel(values=self.data, levels=self.shares, columns=self.dtypes, rows=self.index)

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
        self.assertEqual(list(self.hp.columns.keys), self.dtypes.split())

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
        hp = qt.dataframe_to_hp(df=df, shares='000100', htypes='close, open, high, low, middle', column_type='dtypes')
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

    def test_csv_to_hp(self):
        pass

    def test_hdf_to_hp(self):
        pass

    def test_hp_join(self):
        pass

    def test_df_to_hp(self):
        pass


class TestHistorySubFuncs(unittest.TestCase):
    def setUp(self):
        pass

    def test_str_to_list(self):
        pass

    def list_or_slice(self):
        pass

    def test_label_to_dict(self):
        pass

    def test_stack_dataframes(self):
        pass

    def test_regulate_date_format(self):
        pass

    def test_list_to_str_format(self):
        pass


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