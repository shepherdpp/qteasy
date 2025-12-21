# coding=utf-8
# ======================================
# File:     test_cost.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy back test
#   cost related functions.
# ======================================
import unittest

import qteasy as qt
import numpy as np

from qteasy.finance import get_selling_result, get_purchase_result, get_cost_params, update_cost


class TestCost(unittest.TestCase):
    """ 测试所有跟交易成本计算相关的函数"""
    def setUp(self):
        self.amounts = np.array([10000., 20000., 10000.])
        self.amounts_2 = np.array([10000., -20000., 0.])  # 用于测试买卖混合的交易?
        self.op = np.array([0., 1., -0.33333333])
        self.amounts_to_sell = np.array([0., 0., -3333.3333])
        self.short_amounts_to_sell = np.array([0., 0., 3333.3333])
        self.cash_to_spend = np.array([0., 20000., 0.])
        self.short_cash_to_spend = np.array([0., -20555., 0.])
        self.prices = np.array([10., 20., 10.])
        self.r = qt.set_cost()

    def test_rate_creation(self):
        """测试对象生成"""
        print('testing rates objects\n')
        self.assertIsInstance(self.r, dict, 'Type should be a dict')
        self.assertEqual(self.r['buy_rate'], 0.003, 'Item got is incorrect')
        self.assertEqual(self.r['sell_rate'], 0.001, 'Item got is incorrect')
        self.assertEqual(self.r['buy_min'], 5.0, 'Item got is incorrect')
        self.assertEqual(self.r['sell_min'], 0.0, 'Item got is incorrect')
        self.assertEqual(self.r['slippage'], 0.0, 'Item got is incorrect')

    def test_rate_fee(self):
        """测试买卖交易费率"""
        self.r['buy_rate'] = 0.003
        self.r['sell_rate'] = 0.001
        self.r['buy_fix'] = 0.
        self.r['sell_fix'] = 0.
        self.r['buy_min'] = 0.
        self.r['sell_min'] = 0.
        self.r['slippage'] = 0.
        r = get_cost_params(self.r)

        print('\nSell result with fixed rate = 0.001 and moq = 0:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 0, r))
        test_rate_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 0, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), 33299.999667, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 33.333333, msg='result incorrect')

        print(f'\nSell short result with fixed rate = 0.001 and moq = 0:')
        print(f'selling short {self.short_amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.short_amounts_to_sell, 0, r))
        test_rate_fee_result = get_selling_result(self.prices, self.short_amounts_to_sell, 0, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., 3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), -33366.666333, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 33.333333, msg='result incorrect')

        print('\nSell result with fixed rate = 0.001 and moq = 1:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 1., r))
        test_rate_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 1, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), 33296.67, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 33.33, msg='result incorrect')

        print('\nSell short result with fixed rate = 0.001 and moq = 1:')
        print(f'selling short {self.short_amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.short_amounts_to_sell, 1., r))
        test_rate_fee_result = get_selling_result(self.prices, self.short_amounts_to_sell, 1, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., 3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), -33363.33, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 33.33, msg='result incorrect')

        print('\nSell result with fixed rate = 0.001 and moq = 100:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 100, r))
        test_rate_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 100, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), 32967.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 33, msg='result incorrect')

        print('\nSell short result with fixed rate = 0.001 and moq = 100:')
        print(f'selling {self.short_amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.short_amounts_to_sell, 100, r))
        test_rate_fee_result = get_selling_result(self.prices, self.short_amounts_to_sell, 100, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., 3300.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), -33033.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 33., msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 0:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 0, r))
        test_rate_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997.00897308, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 59.82053838484547, msg='result incorrect')

        print(f'\nPurchase short result with fixed rate = 0.003 and moq = 0:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 0, r))
        test_rate_fee_result = get_purchase_result(self.prices, self.short_cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., -1027.75, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), 20493.335, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 61.665, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 1:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 1, r))
        test_rate_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 1, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), -19999.82, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 59.82, msg='result incorrect')

        print(f'\nPurchase short result with fixed rate = 0.003 and moq = 1:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 1, r))
        test_rate_fee_result = get_purchase_result(self.prices, self.short_cash_to_spend, 1, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., -1027., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), 20478.38, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 61.62, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 100:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 100, r))
        test_rate_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), -18054., msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 54.0, msg='result incorrect')

        print(f'\nPurchase short result with fixed rate = 0.003 and moq = 100:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 100, r))
        test_rate_fee_result = get_purchase_result(self.prices, self.short_cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., -1000., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1].sum(), 19940., msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2].sum(), 60.0, msg='result incorrect')

    def test_min_fee(self):
        """测试最低交易费用"""
        self.r['buy_rate'] = 0.
        self.r['sell_rate'] = 0.
        self.r['buy_fix'] = 0.
        self.r['sell_fix'] = 0.
        self.r['buy_min'] = 300
        self.r['sell_min'] = 300
        self.r['slippage'] = 0.
        r = get_cost_params(self.r)

        print(f'\npurchase result with fixed cost rate with min fee = 300 and moq = 0:\n'
              f'r = {r}')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 0, r))
        test_min_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 985, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0, msg='result incorrect')

        print(f'\npurchase short result with fixed cost rate with min fee = 300 and moq = 0:'
              f'r = {r}')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 0, r))
        test_min_fee_result = get_purchase_result(self.prices, self.short_cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., -1027.75, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), 20255.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 10:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 10, r))
        test_min_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 10, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 980, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), -19900.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0, msg='result incorrect')

        print(f'\npurchase short result with fixed cost rate with min fee = 300 and moq = 10:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 10, r))
        test_min_fee_result = get_purchase_result(self.prices, self.short_cash_to_spend, 10, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., -1020, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), 20100.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 100:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 100, r))
        test_min_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 900, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), -18300.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0, msg='result incorrect')

        print(f'\npurchase short result with fixed cost rate with min fee = 300 and moq = 100:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 100, r))
        test_min_fee_result = get_purchase_result(self.prices, self.short_cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., -1000, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), 19700.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0, msg='result incorrect')

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 0:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 0, r))
        test_min_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 0, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), 33033.333)
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0)

        print(f'\nselling short result with fixed cost rate with min fee = 300 and moq = 0:')
        print(f'selling short {self.short_amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.short_amounts_to_sell, 0, r))
        test_min_fee_result = get_selling_result(self.prices, self.short_amounts_to_sell, 0, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, 3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), -33633.333)
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0)

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 1:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 1, r))
        test_min_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 1, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), 33030)
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0)

        print(f'\nselling short result with fixed cost rate with min fee = 300 and moq = 1:')
        print(f'selling short {self.short_amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.short_amounts_to_sell, 1, r))
        test_min_fee_result = get_selling_result(self.prices, self.short_amounts_to_sell, 1, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, 3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), -33630)
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0)

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 100:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 100, r))
        test_min_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 100, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), 32700)
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0)

        print(f'\nselling short result with fixed cost rate with min fee = 300 and moq = 100:')
        print(f'selling short {self.short_amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.short_amounts_to_sell, 100, r))
        test_min_fee_result = get_selling_result(self.prices, self.short_amounts_to_sell, 100, r)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, 3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1].sum(), -33300)
        self.assertAlmostEqual(test_min_fee_result[2].sum(), 300.0)

    def test_rate_with_min(self):
        """测试最低交易费用对其他交易费率参数的影响"""
        self.r['buy_rate'] = 0.0153
        self.r['sell_rate'] = 0.01
        self.r['buy_fix'] = 0.
        self.r['sell_fix'] = 0.
        self.r['buy_min'] = 300
        self.r['sell_min'] = 333
        self.r['slippage'] = 0.
        r = get_cost_params(self.r)

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 0:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 0, r))
        test_rate_with_min_result = get_purchase_result(self.prices, self.cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 984.9305624, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 301.3887520929774, msg='result incorrect')

        print(f'\npurchase short result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 0:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 0, r))
        test_rate_with_min_result = get_purchase_result(self.prices, self.short_cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., -1027.75, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), 20240.5085, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 314.4915, msg='result incorrect')

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 10:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 10, r))
        test_rate_with_min_result = get_purchase_result(self.prices, self.cash_to_spend, 10, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 980, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), -19900.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 300.0, msg='result incorrect')

        print(f'\npurchase short result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 10:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 10, r))
        test_rate_with_min_result = get_purchase_result(self.prices, self.short_cash_to_spend, 10, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., -1020, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), 20087.88, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 312.12, msg='result incorrect')

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 100:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.cash_to_spend, 100, r))
        test_rate_with_min_result = get_purchase_result(self.prices, self.cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 900, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), -18300.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 300.0, msg='result incorrect')

        print(f'\npurchase short result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 100:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices}')
        print(get_purchase_result(self.prices, self.short_cash_to_spend, 100, r))
        test_rate_with_min_result = get_purchase_result(self.prices, self.short_cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., -1000, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), 19694.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 306.0, msg='result incorrect')

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 0:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 0, r))
        test_rate_with_min_result = get_selling_result(self.prices, self.amounts_to_sell, 0, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), 32999.99967)
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 333.33333)

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 1:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 1, r))
        test_rate_with_min_result = get_selling_result(self.prices, self.amounts_to_sell, 1, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), 32996.7)
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 333.3)

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 100:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices}')
        print(get_selling_result(self.prices, self.amounts_to_sell, 100, r))
        test_rate_with_min_result = get_selling_result(self.prices, self.amounts_to_sell, 100, r)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1].sum(), 32667.0)
        self.assertAlmostEqual(test_rate_with_min_result[2].sum(), 333.0)

    def test_slippage(self):
        """测试交易滑点"""
        self.r['buy_fix'] = 0
        self.r['sell_fix'] = 0
        self.r['buy_min'] = 0
        self.r['sell_min'] = 0
        self.r['buy_rate'] = 0.003
        self.r['sell_rate'] = 0.001
        self.r['slippage'] = 1E-9
        r = get_cost_params(self.r)
        print('\npurchase result of fixed rate = 0.003 and slippage = 1E-10 and moq = 0:')
        print(get_purchase_result(self.prices, self.cash_to_spend, 0, r))
        print('\npurchase result of fixed rate = 0.003 and slippage = 1E-10 and moq = 100:')
        print(get_purchase_result(self.prices, self.cash_to_spend, 100, r))
        print('\nselling result with fixed rate = 0.001 and slippage = 1E-10:')
        print(get_selling_result(self.prices, self.amounts_to_sell, 0, r))

        test_fixed_fee_result = get_selling_result(self.prices, self.amounts_to_sell, 0, r)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3333.3333]), True,
                      f'{test_fixed_fee_result[0]} does not equal to [0, 0, -10000]')
        self.assertAlmostEqual(test_fixed_fee_result[1].sum(), 33298.88855591,
                                msg=f'{test_fixed_fee_result[1]} does not equal to 33298.')
        self.assertAlmostEqual(test_fixed_fee_result[2].sum(), 34.44444409,
                                msg=f'{test_fixed_fee_result[2]} does not equal to -36.666663.')

        test_fixed_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 0, r)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 996.98909294, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1].sum(), -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2].sum(), 60.21814121353513, msg='result incorrect')

        test_fixed_fee_result = get_purchase_result(self.prices, self.cash_to_spend, 100, r)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1].sum(), -18054.36, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2].sum(), 54.36, msg='result incorrect')


if __name__ == '__main__':
    unittest.main()