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

from qteasy.finance import (
    apply_execution_slippage,
    get_selling_result,
    get_purchase_result,
    get_cost_params,
    update_cost,
)


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
        self.prices_with_nan = np.array([10., np.nan, np.nan])
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

    def test_price_with_nan(self):
        """测试价格中包含NaN的情况, 此时交易结果应该为0, 交易费用应该为0"""
        self.r['buy_rate'] = 0.003
        self.r['sell_rate'] = 0.001
        self.r['buy_fix'] = 0.
        self.r['sell_fix'] = 0.
        self.r['buy_min'] = 0.
        self.r['sell_min'] = 0.
        self.r['slippage'] = 0.
        r = get_cost_params(self.r)

        print('\nSell result with price containing NaN:')
        print(f'selling {self.amounts_to_sell} with prices {self.prices_with_nan}')
        test_price_with_nan_result = get_selling_result(self.prices_with_nan, self.amounts_to_sell, 0, r)
        print(f'result {test_price_with_nan_result}')
        self.assertIs(np.allclose(test_price_with_nan_result[0], [0., 0., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[1].sum(), 0., msg='result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[2].sum(), 0., msg='result incorrect')

        print('\nSell short result with price containing NaN:')
        print(f'selling short {self.short_amounts_to_sell} with prices {self.prices_with_nan}')
        test_price_with_nan_result = get_selling_result(self.prices_with_nan, self.short_amounts_to_sell, 0, r)
        print(f'result{test_price_with_nan_result}')
        self.assertIs(np.allclose(test_price_with_nan_result[0], [0., 0., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[1].sum(), 0., msg='result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[2].sum(), 0., msg='result incorrect')

        print(f'\nPurchase result with price containing NaN:')
        print(f'buying with cash {self.cash_to_spend} and prices {self.prices_with_nan}')
        test_price_with_nan_result = get_purchase_result(self.prices_with_nan, self.cash_to_spend, 0, r)
        print(f'result{test_price_with_nan_result}')
        self.assertIs(np.allclose(test_price_with_nan_result[0], [0., 0., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[1].sum(), 0.0, msg='result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[2].sum(), 0.0, msg='result incorrect')

        print(f'\nPurchase short result with price containing NaN:')
        print(f'buying short with cash {self.short_cash_to_spend} and prices {self.prices_with_nan}')
        test_price_with_nan_result = get_purchase_result(self.prices_with_nan, self.short_cash_to_spend, 0, r)
        print(f'result{test_price_with_nan_result}')
        self.assertIs(np.allclose(test_price_with_nan_result[0], [0., 0., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[1].sum(), 0., msg='result incorrect')
        self.assertAlmostEqual(test_price_with_nan_result[2].sum(), 0., msg='result incorrect')

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
        """内核中 slippage 不参与费率折算；与 slippage=0 一致，且数值与金标准一致（滑点由回测执行层追加）"""
        self.r['buy_fix'] = 0
        self.r['sell_fix'] = 0
        self.r['buy_min'] = 0
        self.r['sell_min'] = 0
        self.r['buy_rate'] = 0.003
        self.r['sell_rate'] = 0.001
        self.r['slippage'] = 1e-6
        r_slip = get_cost_params(self.r)
        self.r['slippage'] = 0.0
        r0 = get_cost_params(self.r)
        print('\n[test_slippage] prices:', self.prices)
        print('[test_slippage] cash_to_spend:', self.cash_to_spend)
        print('[test_slippage] amounts_to_sell:', self.amounts_to_sell)
        print('[test_slippage] r_slip:', r_slip, 'r0:', r0)

        # --- 买入 moq=0：与 test_rate_fee 金标准一致；slip 与 r0 输出一致 ---
        pu_s = get_purchase_result(self.prices, self.cash_to_spend, 0, r_slip)
        pu_0 = get_purchase_result(self.prices, self.cash_to_spend, 0, r0)
        print('[test_slippage] purchase moq=0 amounts (slip):', pu_s[0])
        print('[test_slippage] purchase moq=0 cash_spent (slip):', pu_s[1])
        print('[test_slippage] purchase moq=0 fees (slip):', pu_s[2])
        print('[test_slippage] purchase moq=0 amounts (r0):', pu_0[0])
        print('[test_slippage] purchase moq=0 cash_spent (r0):', pu_0[1])
        print('[test_slippage] purchase moq=0 fees (r0):', pu_0[2])
        self.assertTrue(np.allclose(pu_s[0], pu_0[0]), msg='purchase moq=0 amounts: slip vs r0 differ')
        self.assertTrue(np.allclose(pu_s[1], pu_0[1]), msg='purchase moq=0 cash_spent: slip vs r0 differ')
        self.assertTrue(np.allclose(pu_s[2], pu_0[2]), msg='purchase moq=0 fees: slip vs r0 differ')
        self.assertIs(np.allclose(pu_0[0], [0., 997.00897308, 0.]), True, 'purchase moq=0 amounts golden incorrect')
        self.assertAlmostEqual(float(pu_0[1].sum()), -20000.0, msg='purchase moq=0 cash_spent sum golden incorrect')
        self.assertAlmostEqual(float(pu_0[2].sum()), 59.82053838484547, msg='purchase moq=0 fees sum golden incorrect')

        # --- 买入 moq=100：金标准 + slip 与 r0 一致 ---
        pu100_s = get_purchase_result(self.prices, self.cash_to_spend, 100, r_slip)
        pu100_0 = get_purchase_result(self.prices, self.cash_to_spend, 100, r0)
        print('[test_slippage] purchase moq=100 amounts (slip):', pu100_s[0])
        print('[test_slippage] purchase moq=100 cash_spent (slip):', pu100_s[1])
        print('[test_slippage] purchase moq=100 fees (slip):', pu100_s[2])
        print('[test_slippage] purchase moq=100 amounts (r0):', pu100_0[0])
        print('[test_slippage] purchase moq=100 cash_spent (r0):', pu100_0[1])
        print('[test_slippage] purchase moq=100 fees (r0):', pu100_0[2])
        self.assertTrue(np.allclose(pu100_s[0], pu100_0[0]), msg='purchase moq=100 amounts: slip vs r0 differ')
        self.assertTrue(np.allclose(pu100_s[1], pu100_0[1]), msg='purchase moq=100 cash_spent: slip vs r0 differ')
        self.assertTrue(np.allclose(pu100_s[2], pu100_0[2]), msg='purchase moq=100 fees: slip vs r0 differ')
        self.assertIs(np.allclose(pu100_0[0], [0., 900., 0.]), True, 'purchase moq=100 amounts golden incorrect')
        self.assertAlmostEqual(float(pu100_0[1].sum()), -18054.0, msg='purchase moq=100 cash_spent sum golden incorrect')
        self.assertAlmostEqual(float(pu100_0[2].sum()), 54.0, msg='purchase moq=100 fees sum golden incorrect')

        # --- 卖出 moq=0：与 test_rate_fee 金标准一致；slip 与 r0 一致 ---
        se_s = get_selling_result(self.prices, self.amounts_to_sell, 0, r_slip)
        se_0 = get_selling_result(self.prices, self.amounts_to_sell, 0, r0)
        print('[test_slippage] sell moq=0 amounts (slip):', se_s[0])
        print('[test_slippage] sell moq=0 cash_gained (slip):', se_s[1])
        print('[test_slippage] sell moq=0 fees (slip):', se_s[2])
        print('[test_slippage] sell moq=0 amounts (r0):', se_0[0])
        print('[test_slippage] sell moq=0 cash_gained (r0):', se_0[1])
        print('[test_slippage] sell moq=0 fees (r0):', se_0[2])
        self.assertTrue(np.allclose(se_s[0], se_0[0]), msg='sell moq=0 amounts: slip vs r0 differ')
        self.assertTrue(np.allclose(se_s[1], se_0[1]), msg='sell moq=0 cash_gained: slip vs r0 differ')
        self.assertTrue(np.allclose(se_s[2], se_0[2]), msg='sell moq=0 fees: slip vs r0 differ')
        self.assertIs(np.allclose(se_0[0], [0., 0., -3333.3333]), True, 'sell moq=0 amounts golden incorrect')
        self.assertAlmostEqual(float(se_0[1].sum()), 33299.999667, msg='sell moq=0 cash_gained sum golden incorrect')
        self.assertAlmostEqual(float(se_0[2].sum()), 33.333333, msg='sell moq=0 fees sum golden incorrect')

    def test_get_purchase_result_ignores_slippage_in_rates(self):
        """极大 slippage 下买入数量/现金/费用应与 slippage=0 一致，且等于金标准"""
        print('\n[test_get_purchase_result_ignores_slippage_in_rates]')
        print('  prices:', self.prices, 'cash_to_spend:', self.cash_to_spend)
        self.r['buy_rate'] = 0.003
        self.r['sell_rate'] = 0.001
        self.r['buy_min'] = 0.0
        self.r['sell_min'] = 0.0
        self.r['slippage'] = 0.5
        r_hi = get_cost_params(self.r)
        self.r['slippage'] = 0.0
        r0 = get_cost_params(self.r)
        print('  r_hi (slippage=0.5):', r_hi)
        print('  r0 (slippage=0):', r0)
        a_hi, c_hi, f_hi = get_purchase_result(self.prices, self.cash_to_spend, 0, r_hi)
        a0, c0, f0 = get_purchase_result(self.prices, self.cash_to_spend, 0, r0)
        print('  amounts r_hi:', a_hi, 'cash_spent:', c_hi, 'fees:', f_hi)
        print('  amounts r0:  ', a0, 'cash_spent:', c0, 'fees:', f0)
        self.assertTrue(np.allclose(a_hi, a0), msg='purchase qty should ignore slippage')
        self.assertTrue(np.allclose(c_hi, c0), msg='cash_spent should ignore slippage in kernel')
        self.assertTrue(np.allclose(f_hi, f0), msg='fees should ignore slippage in kernel')
        self.assertIs(np.allclose(a0, [0., 997.00897308, 0.]), True, 'golden amounts incorrect')
        self.assertAlmostEqual(float(c0.sum()), -20000.0, msg='golden cash_spent sum incorrect')
        self.assertAlmostEqual(float(f0.sum()), 59.82053838484547, msg='golden fees sum incorrect')

    def test_get_selling_result_ignores_slippage_in_rates(self):
        """极大 slippage 下卖出应与 slippage=0 一致，且等于金标准"""
        print('\n[test_get_selling_result_ignores_slippage_in_rates]')
        print('  prices:', self.prices, 'amounts_to_sell:', self.amounts_to_sell)
        self.r['buy_rate'] = 0.003
        self.r['sell_rate'] = 0.001
        self.r['buy_min'] = 0.0
        self.r['sell_min'] = 0.0
        self.r['slippage'] = 0.5
        r_hi = get_cost_params(self.r)
        self.r['slippage'] = 0.0
        r0 = get_cost_params(self.r)
        print('  r_hi:', r_hi, 'r0:', r0)
        a_hi, cg_hi, fe_hi = get_selling_result(self.prices, self.amounts_to_sell, 0, r_hi)
        a0, cg0, fe0 = get_selling_result(self.prices, self.amounts_to_sell, 0, r0)
        print('  a_sold r_hi:', a_hi, 'cash_gained:', cg_hi, 'fees:', fe_hi)
        print('  a_sold r0:  ', a0, 'cash_gained:', cg0, 'fees:', fe0)
        self.assertTrue(np.allclose(a_hi, a0), msg='sold qty should ignore slippage')
        self.assertTrue(np.allclose(cg_hi, cg0), msg='cash_gained should ignore slippage in kernel')
        self.assertTrue(np.allclose(fe_hi, fe0), msg='fees should ignore slippage in kernel')
        self.assertIs(np.allclose(a0, [0., 0., -3333.3333]), True, 'golden a_sold incorrect')
        self.assertAlmostEqual(float(cg0.sum()), 33299.999667, msg='golden cash_gained sum incorrect')
        self.assertAlmostEqual(float(fe0.sum()), 33.333333, msg='golden fees sum incorrect')

    def test_backtest_execution_slippage_adjusts_cash_not_qty(self):
        """执行层滑点：数量不变，现金与费用变化"""
        print('\n[test_backtest_execution_slippage_adjusts_cash_not_qty]')
        prices = np.array([10.0, 20.0])
        amount_purchased = np.array([100.0, 0.0])
        amount_sold = np.array([0.0, -50.0])
        cash_spent = np.array([-1050.0, 0.0])
        cash_gained = np.array([0.0, 950.0])
        fee = np.array([50.0, 50.0])
        slip = 0.01
        print('  before: prices', prices, 'amount_purchased', amount_purchased, 'amount_sold', amount_sold)
        print('  before: cash_spent', cash_spent, 'cash_gained', cash_gained, 'fee', fee, 'slip', slip)
        ap0 = amount_purchased.copy()
        as0 = amount_sold.copy()
        apply_execution_slippage(
                prices, amount_purchased, amount_sold, cash_spent, cash_gained, fee, slip,
        )
        print('  after:  cash_spent', cash_spent, 'cash_gained', cash_gained, 'fee', fee)
        print('  expected cash_spent[0]=-1060 fee[0]=60 cash_gained[1]=940 fee[1]=60 (qty unchanged)')
        self.assertTrue(np.allclose(amount_purchased, ap0), msg='amount_purchased must not change')
        self.assertTrue(np.allclose(amount_sold, as0), msg='amount_sold must not change')
        # 买 100@10: slip 10 -> cash_spent 更负 10, fee +10
        self.assertAlmostEqual(float(cash_spent[0]), -1060.0, msg='buy cash_spent should include slip cost')
        self.assertAlmostEqual(float(fee[0]), 60.0, msg='buy fee should include slip')
        # 卖 50@20: notional 1000, slip 10 -> cash_gained 减少 10, fee +10
        self.assertAlmostEqual(float(cash_gained[1]), 940.0, msg='sell cash_gained reduced by slip')
        self.assertAlmostEqual(float(fee[1]), 60.0, msg='sell fee includes slip')
        self.assertAlmostEqual(float(cash_spent[1]), 0.0, msg='no buy on leg 1')
        self.assertAlmostEqual(float(cash_gained[0]), 0.0, msg='no sell on leg 0')

    def test_sell_long_tiny_proceeds_below_min_fee_zeroed(self):
        """多头卖出时若所得现金小于最低手续费（净收入为负），该笔应置为不成交：a_sold/fees/cash_gained 置 0"""
        self.r['buy_rate'] = 0.
        self.r['sell_rate'] = 0.
        self.r['buy_fix'] = 0.
        self.r['sell_fix'] = 0.
        self.r['buy_min'] = 0.
        self.r['sell_min'] = 100.
        self.r['slippage'] = 0.
        r = get_cost_params(self.r)

        # 仅第三只股票小额多头卖出：1 份 @ 10，金额 10 < sell_min 100，净收入为负，应置零
        prices = np.array([10., 20., 10.])
        a_to_sell_single_tiny = np.array([0., 0., -1.])
        a_sold, cash_gained, fees = get_selling_result(prices, a_to_sell_single_tiny, 0, r)
        print('\ntest_sell_long_tiny_proceeds_below_min_fee_zeroed: single tiny long sell')
        print(f'prices: {prices}, a_to_sell: {a_to_sell_single_tiny}, sell_min: 100')
        print(f'a_sold: {a_sold}, cash_gained: {cash_gained}, fees: {fees}')
        self.assertTrue(np.allclose(a_sold, [0., 0., 0.]), f'a_sold should be zeroed, got {a_sold}')
        self.assertTrue(np.allclose(fees, [0., 0., 0.]), f'fees should be zeroed, got {fees}')
        self.assertTrue(np.allclose(cash_gained, [0., 0., 0.]), f'cash_gained should be zeroed, got {cash_gained}')

        # 混合：第二只正常卖出、第三只小额卖出应置零
        a_to_sell_mixed = np.array([0., -100., -1.])
        a_sold, cash_gained, fees = get_selling_result(prices, a_to_sell_mixed, 0, r)
        print('\ntest_sell_long_tiny_proceeds_below_min_fee_zeroed: mixed (normal + tiny)')
        print(f'prices: {prices}, a_to_sell: {a_to_sell_mixed}, sell_min: 100')
        print(f'a_sold: {a_sold}, cash_gained: {cash_gained}, fees: {fees}')
        self.assertTrue(np.allclose(a_sold, [0., -100., 0.]), f'a_sold 3rd should be 0, got {a_sold}')
        self.assertTrue(np.allclose(fees, [0., 100., 0.]), f'fees 3rd should be 0, got {fees}')
        self.assertAlmostEqual(cash_gained[1], 1900., msg='cash_gained[1] = -(sold_values+fees) = -(-2000+100) = 1900')
        self.assertAlmostEqual(cash_gained[2], 0., msg='cash_gained[2] should be zeroed')
        self.assertAlmostEqual(cash_gained[0], 0., msg='cash_gained[0] no trade')

        # 空头卖出不受影响：即使 cash_gained 为负也不置零（仅对多头卖出且净收入为负的置零）
        short_sell = np.array([0., 0., 1.])
        a_sold_short, cash_gained_short, fees_short = get_selling_result(prices, short_sell, 0, r)
        print('\ntest_sell_long_tiny_proceeds_below_min_fee_zeroed: short sell unchanged')
        print(f'a_to_sell (short): {short_sell}, a_sold: {a_sold_short}, cash_gained: {cash_gained_short}, fees: {fees_short}')
        self.assertTrue(np.allclose(a_sold_short, [0., 0., 1.]), 'short sell a_sold should remain')
        self.assertAlmostEqual(cash_gained_short[2], -10. - 100., msg='short sell: cash_gained = -(sold_values+fees)')

    def test_apply_execution_slippage_zero_slippage_returns_same_arrays(self):
        """§5.11 AES-ZERO：slippage=0 时与拷贝数组逐元素一致（早退路径）。"""
        print('\n[TestCost] AES-ZERO apply_execution_slippage slippage=0')
        prices = np.array([10.0, 20.0])
        amount_purchased = np.array([100.0, 0.0])
        amount_sold = np.array([0.0, 50.0])
        cash_spent = np.array([-1000.0, 0.0])
        cash_gained = np.array([0.0, 900.0])
        fee = np.array([10.0, 10.0])
        cg0, cs0, ap0, as0, f0 = (
                cash_gained.copy(),
                cash_spent.copy(),
                amount_purchased.copy(),
                amount_sold.copy(),
                fee.copy(),
        )
        out = apply_execution_slippage(
                prices, amount_purchased, amount_sold, cash_spent, cash_gained, fee, 0.0,
        )
        print('  out is same tuple objects as inputs (early return):', out[0] is cash_gained)
        self.assertTrue(np.allclose(cash_gained, cg0))
        self.assertTrue(np.allclose(cash_spent, cs0))
        self.assertTrue(np.allclose(amount_purchased, ap0))
        self.assertTrue(np.allclose(amount_sold, as0))
        self.assertTrue(np.allclose(fee, f0))

    def test_apply_execution_slippage_inf_price_skips_slip_on_that_leg(self):
        """§5.11 AES-INF：价格为 inf 的成交腿不追加执行层滑点。"""
        print('\n[TestCost] AES-INF apply_execution_slippage price[0]=inf')
        prices = np.array([np.inf, 20.0])
        amount_purchased = np.array([100.0, 0.0])
        amount_sold = np.array([0.0, 50.0])
        cash_spent = np.array([-1000.0, 0.0])
        cash_gained = np.array([0.0, 900.0])
        fee = np.array([10.0, 10.0])
        slip = 0.01
        apply_execution_slippage(
                prices, amount_purchased, amount_sold, cash_spent, cash_gained, fee, slip,
        )
        print('  cash_spent', cash_spent, 'cash_gained', cash_gained, 'fee', fee)
        # 第一腿 buy_ok 为 False，无滑点；第二腿卖出 50@20 -> slip 10
        self.assertAlmostEqual(float(cash_spent[0]), -1000.0)
        self.assertAlmostEqual(float(cash_gained[1]), 890.0)
        self.assertAlmostEqual(float(fee[1]), 20.0)


if __name__ == '__main__':
    unittest.main()