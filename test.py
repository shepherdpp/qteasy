import unittest
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np
import math
from numpy import int64
import itertools
import datetime
import logging

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, time_str_format, str_to_list
from qteasy.utilfuncs import maybe_trade_day, is_market_trade_day, prev_trade_day, next_trade_day
from qteasy.utilfuncs import next_market_trade_day, unify, list_or_slice, labels_to_dict, retry
from qteasy.utilfuncs import weekday_name, prev_market_trade_day, is_number_like, list_truncate, input_to_list

from qteasy.space import Space, Axis, space_around_centre, ResultPool
from qteasy.core import apply_loop
from qteasy.built_in import SelectingFinanceIndicator, TimingDMA, TimingMACD, TimingCDL, TimingTRIX

from qteasy.tsfuncs import income, indicators, name_change, get_bar
from qteasy.tsfuncs import stock_basic, trade_calendar, new_share, get_index
from qteasy.tsfuncs import balance, cashflow, top_list, index_indicators, composite
from qteasy.tsfuncs import future_basic, future_daily, options_basic, options_daily
from qteasy.tsfuncs import fund_basic, fund_net_value, index_basic, stock_company

from qteasy.evaluate import eval_alpha, eval_benchmark, eval_beta, eval_fv
from qteasy.evaluate import eval_info_ratio, eval_max_drawdown, eval_sharp
from qteasy.evaluate import eval_volatility

from qteasy.tafuncs import bbands, dema, ema, ht, kama, ma, mama, mavp, mid_point
from qteasy.tafuncs import mid_price, sar, sarext, sma, t3, tema, trima, wma, adx, adxr
from qteasy.tafuncs import apo, bop, cci, cmo, dx, macd, macdext, aroon, aroonosc
from qteasy.tafuncs import macdfix, mfi, minus_di, minus_dm, mom, plus_di, plus_dm
from qteasy.tafuncs import ppo, roc, rocp, rocr, rocr100, rsi, stoch, stochf, stochrsi
from qteasy.tafuncs import trix, ultosc, willr, ad, adosc, obv, atr, natr, trange
from qteasy.tafuncs import avgprice, medprice, typprice, wclprice, ht_dcperiod
from qteasy.tafuncs import ht_dcphase, ht_phasor, ht_sine, ht_trendmode, cdl2crows
from qteasy.tafuncs import cdl3blackcrows, cdl3inside, cdl3linestrike, cdl3outside
from qteasy.tafuncs import cdl3starsinsouth, cdl3whitesoldiers, cdlabandonedbaby
from qteasy.tafuncs import cdladvanceblock, cdlbelthold, cdlbreakaway, cdlclosingmarubozu
from qteasy.tafuncs import cdlconcealbabyswall, cdlcounterattack, cdldarkcloudcover
from qteasy.tafuncs import cdldoji, cdldojistar, cdldragonflydoji, cdlengulfing
from qteasy.tafuncs import cdleveningdojistar, cdleveningstar, cdlgapsidesidewhite
from qteasy.tafuncs import cdlgravestonedoji, cdlhammer, cdlhangingman, cdlharami
from qteasy.tafuncs import cdlharamicross, cdlhighwave, cdlhikkake, cdlhikkakemod
from qteasy.tafuncs import cdlhomingpigeon, cdlidentical3crows, cdlinneck
from qteasy.tafuncs import cdlinvertedhammer, cdlkicking, cdlkickingbylength
from qteasy.tafuncs import cdlladderbottom, cdllongleggeddoji, cdllongline, cdlmarubozu
from qteasy.tafuncs import cdlmatchinglow, cdlmathold, cdlmorningdojistar, cdlmorningstar
from qteasy.tafuncs import cdlonneck, cdlpiercing, cdlrickshawman, cdlrisefall3methods
from qteasy.tafuncs import cdlseparatinglines, cdlshootingstar, cdlshortline, cdlspinningtop
from qteasy.tafuncs import cdlstalledpattern, cdlsticksandwich, cdltakuri, cdltasukigap
from qteasy.tafuncs import cdlthrusting, cdltristar, cdlunique3river, cdlupsidegap2crows
from qteasy.tafuncs import cdlxsidegap3methods, beta, correl, linearreg, linearreg_angle
from qteasy.tafuncs import linearreg_intercept, linearreg_slope, stddev, tsf, var, acos
from qteasy.tafuncs import asin, atan, ceil, cos, cosh, exp, floor, ln, log10, sin, sinh
from qteasy.tafuncs import sqrt, tan, tanh, add, div, max, maxindex, min, minindex, minmax
from qteasy.tafuncs import minmaxindex, mult, sub, sum

from qteasy.history import get_financial_report_type_raw_data, get_price_type_raw_data
from qteasy.history import stack_dataframes, dataframe_to_hp, HistoryPanel

from qteasy.database import DataSource, set_primary_key_index, set_primary_key_frame

from qteasy.strategy import Strategy, SimpleTiming, RollingTiming, SimpleSelecting, FactoralSelecting

from qteasy._arg_validators import _parse_string_kwargs, _valid_qt_kwargs

from qteasy.blender import _exp_to_token, blender_parser, signal_blend


class TestCost(unittest.TestCase):
    def setUp(self):
        self.amounts = np.array([10000., 20000., 10000.])
        self.op = np.array([0., 1., -0.33333333])
        self.amounts_to_sell = np.array([0., 0., -3333.3333])
        self.cash_to_spend = np.array([0., 20000., 0.])
        self.prices = np.array([10., 20., 10.])
        self.r = qt.Cost(0.0)

    def test_rate_creation(self):
        """测试对象生成"""
        print('testing rates objects\n')
        self.assertIsInstance(self.r, qt.Cost, 'Type should be Rate')
        self.assertEqual(self.r.buy_fix, 0)
        self.assertEqual(self.r.sell_fix, 0)

    def test_rate_operations(self):
        """测试交易费率对象"""
        self.assertEqual(self.r['buy_fix'], 0.0, 'Item got is incorrect')
        self.assertEqual(self.r['sell_fix'], 0.0, 'Item got is wrong')
        self.assertEqual(self.r['buy_rate'], 0.003, 'Item got is incorrect')
        self.assertEqual(self.r['sell_rate'], 0.001, 'Item got is incorrect')
        self.assertEqual(self.r['buy_min'], 5., 'Item got is incorrect')
        self.assertEqual(self.r['sell_min'], 0.0, 'Item got is incorrect')
        self.assertEqual(self.r['slipage'], 0.0, 'Item got is incorrect')
        self.assertEqual(np.allclose(self.r.calculate(self.amounts),
                                     [0.003, 0.003, 0.003]),
                         True,
                         'fee calculation wrong')

    def test_rate_fee(self):
        """测试买卖交易费率"""
        self.r.buy_rate = 0.003
        self.r.sell_rate = 0.001
        self.r.buy_fix = 0.
        self.r.sell_fix = 0.
        self.r.buy_min = 0.
        self.r.sell_min = 0.
        self.r.slipage = 0.

        print('\nSell result with fixed rate = 0.001 and moq = 0:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 33299.999667, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 33.333332999999996, msg='result incorrect')

        print('\nSell result with fixed rate = 0.001 and moq = 1:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 1.))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 1)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 33296.67, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 33.33, msg='result incorrect')

        print('\nSell result with fixed rate = 0.001 and moq = 100:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 100))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 100)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 32967.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 33, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 0))
        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 0)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997.00897308, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 59.82053838484547, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 1:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 1))
        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 1)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -19999.82, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 59.82, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 100))
        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 100)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -18054., msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 54.0, msg='result incorrect')

    def test_min_fee(self):
        """测试最低交易费用"""
        self.r.buy_rate = 0.
        self.r.sell_rate = 0.
        self.r.buy_fix = 0.
        self.r.sell_fix = 0.
        self.r.buy_min = 300
        self.r.sell_min = 300
        self.r.slipage = 0.
        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 0))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 0)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 985, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 10:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 10))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 10)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 980, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -19900.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 100))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 100)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 900, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -18300.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 0:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 33033.333)
        self.assertAlmostEqual(test_min_fee_result[2], 300.0)

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 1:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 1))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 1)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 33030)
        self.assertAlmostEqual(test_min_fee_result[2], 300.0)

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 100:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 100))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 100)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 32700)
        self.assertAlmostEqual(test_min_fee_result[2], 300.0)

    def test_rate_with_min(self):
        """测试最低交易费用对其他交易费率参数的影响"""
        self.r.buy_rate = 0.0153
        self.r.sell_rate = 0.01
        self.r.buy_fix = 0.
        self.r.sell_fix = 0.
        self.r.buy_min = 300
        self.r.sell_min = 333
        self.r.slipage = 0.
        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 0))
        test_rate_with_min_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 0)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 984.9305624, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2], 301.3887520929774, msg='result incorrect')

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 10:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 10))
        test_rate_with_min_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 10)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 980, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], -19900.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2], 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 100))
        test_rate_with_min_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 100)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 900, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], -18300.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2], 300.0, msg='result incorrect')

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 0:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell))
        test_rate_with_min_result = self.r.get_selling_result(self.prices, self.amounts_to_sell)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], 32999.99967)
        self.assertAlmostEqual(test_rate_with_min_result[2], 333.33333)

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 1:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 1))
        test_rate_with_min_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 1)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], 32996.7)
        self.assertAlmostEqual(test_rate_with_min_result[2], 333.3)

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 100:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 100))
        test_rate_with_min_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 100)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], 32667.0)
        self.assertAlmostEqual(test_rate_with_min_result[2], 333.0)

    def test_fixed_fee(self):
        """测试固定交易费用"""
        self.r.buy_rate = 0.
        self.r.sell_rate = 0.
        self.r.buy_fix = 200
        self.r.sell_fix = 150
        self.r.buy_min = 0
        self.r.sell_min = 0
        self.r.slipage = 0
        print('\nselling result of fixed cost with fixed fee = 150 and moq=0:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 0))
        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], 33183.333, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 150.0, msg='result incorrect')

        print('\nselling result of fixed cost with fixed fee = 150 and moq=100:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell, 100))
        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell, 100)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3300.]), True,
                      f'result incorrect, {test_fixed_fee_result[0]} does not equal to [0,0,-3400]')
        self.assertAlmostEqual(test_fixed_fee_result[1], 32850., msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 150., msg='result incorrect')

        print('\npurchase result of fixed cost with fixed fee = 200:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 0))
        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 0)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 990., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 200.0, msg='result incorrect')

        print('\npurchase result of fixed cost with fixed fee = 200:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 100))
        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 100)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -18200.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 200.0, msg='result incorrect')

    def test_slipage(self):
        """测试交易滑点"""
        self.r.buy_fix = 0
        self.r.sell_fix = 0
        self.r.buy_min = 0
        self.r.sell_min = 0
        self.r.buy_rate = 0.003
        self.r.sell_rate = 0.001
        self.r.slipage = 1E-9
        print('\npurchase result of fixed rate = 0.003 and slipage = 1E-10 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 0))
        print('\npurchase result of fixed rate = 0.003 and slipage = 1E-10 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.cash_to_spend, 100))
        print('\nselling result with fixed rate = 0.001 and slipage = 1E-10:')
        print(self.r.get_selling_result(self.prices, self.amounts_to_sell))

        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.amounts_to_sell)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3333.3333]), True,
                      f'{test_fixed_fee_result[0]} does not equal to [0, 0, -10000]')
        self.assertAlmostEqual(test_fixed_fee_result[1], 33298.88855591,
                               msg=f'{test_fixed_fee_result[1]} does not equal to 99890.')
        self.assertAlmostEqual(test_fixed_fee_result[2], 34.44444409,
                               msg=f'{test_fixed_fee_result[2]} does not equal to -36.666663.')

        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 0)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 996.98909294, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 60.21814121353513, msg='result incorrect')

        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.cash_to_spend, 100)
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
            s = Space(*p)
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
            s = Space(*p)
            b = s.boes
            t = s.types
            # print(s, t)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['discr', 'enum'], 'types incorrect')

        pars_list = [(0., 10), (0, 10)]
        s = Space(pars=pars_list, par_types=None)
        self.assertEqual(s.types, ['conti', 'discr'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10.0, 11))
        self.assertEqual(s.shape, (np.inf, 11))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        pars_list = [(0., 10), (0, 10)]
        s = Space(pars=pars_list, par_types='conti, enum')
        self.assertEqual(s.types, ['conti', 'enum'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10.0, 2))
        self.assertEqual(s.shape, (np.inf, 2))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        pars_list = [(1, 2), (2, 3), (3, 4)]
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['discr', 'discr', 'discr'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (2, 2, 2))
        self.assertEqual(s.shape, (2, 2, 2))
        self.assertEqual(s.count, 8)
        self.assertEqual(s.boes, [(1, 2), (2, 3), (3, 4)])

        pars_list = [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['enum', 'enum', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (3, 3, 3))
        self.assertEqual(s.shape, (3, 3, 3))
        self.assertEqual(s.count, 27)
        self.assertEqual(s.boes, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])

        pars_list = [((1, 2, 3), (2, 3, 4), (3, 4, 5))]
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['enum'])
        self.assertEqual(s.dim, 1)
        self.assertEqual(s.size, (3,))
        self.assertEqual(s.shape, (3,))
        self.assertEqual(s.count, 3)

        pars_list = ((1, 2, 3), (2, 3, 4), (3, 4, 5))
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['enum', 'enum', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (3, 3, 3))
        self.assertEqual(s.shape, (3, 3, 3))
        self.assertEqual(s.count, 27)
        self.assertEqual(s.boes, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])

    def test_extract(self):
        """

        :return:
        """
        pars_list = [(0, 10), (0, 10)]
        types_list = ['discr', 'discr']
        s = Space(pars=pars_list, par_types=types_list)
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
        s = Space(pars=pars_list, par_types=None)
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
        s = Space(pars=pars_list, par_types='enum, enum')
        extracted_int3, count = s.extract(1, 'interval')
        self.assertEqual(count, 4, 'extraction count wrong!')
        extracted_int_list3 = list(extracted_int3)
        self.assertEqual(extracted_int_list3, [(0., 'a'), (0., 'b'), (10, 'a'), (10, 'b')],
                         'space extraction wrong!')
        print('extracted int list 3\n', extracted_int_list3)
        self.assertIsInstance(extracted_int_list3[0][0], float)
        self.assertIsInstance(extracted_int_list3[0][1], str)
        extracted_rand3, count = s.extract(3, 'rand')
        self.assertEqual(count, 3, 'extraction count wrong!')
        extracted_rand_list3 = list(extracted_rand3)
        print('extracted rand list 3:\n', extracted_rand_list3)
        for point in extracted_rand_list3:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], (float, int))
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertIsInstance(point[1], str)
            self.assertIn(point[1], ['a', 'b'])

        pars_list = [((0, 10), (1, 'c'), ('a', 'b'), (1, 14))]
        s = Space(pars=pars_list, par_types='enum')
        extracted_int4, count = s.extract(1, 'interval')
        self.assertEqual(count, 4, 'extraction count wrong!')
        extracted_int_list4 = list(extracted_int4)
        it = zip(extracted_int_list4, [(0, 10), (1, 'c'), (0, 'b'), (1, 14)])
        for item, item2 in it:
            print(item, item2)
        self.assertTrue(all([tuple(ext_item) == item for ext_item, item in it]))
        print('extracted int list 4\n', extracted_int_list4)
        self.assertIsInstance(extracted_int_list4[0], tuple)
        extracted_rand4, count = s.extract(3, 'rand')
        self.assertEqual(count, 3, 'extraction count wrong!')
        extracted_rand_list4 = list(extracted_rand4)
        print('extracted rand list 4:\n', extracted_rand_list4)
        for point in extracted_rand_list4:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], (int, str))
            self.assertIn(point[0], [0, 1, 'a'])
            self.assertIsInstance(point[1], (int, str))
            self.assertIn(point[1], [10, 14, 'b', 'c'])
            self.assertIn(point, [(0., 10), (1, 'c'), ('a', 'b'), (1, 14)])

        pars_list = [((0, 10), (1, 'c'), ('a', 'b'), (1, 14)), (1, 4)]
        s = Space(pars=pars_list, par_types='enum, discr')
        extracted_int5, count = s.extract(1, 'interval')
        self.assertEqual(count, 16, 'extraction count wrong!')
        extracted_int_list5 = list(extracted_int5)
        for item, item2 in extracted_int_list5:
            print(item, item2)
        self.assertTrue(all([tuple(ext_item) == item for ext_item, item in it]))
        print('extracted int list 5\n', extracted_int_list5)
        self.assertIsInstance(extracted_int_list5[0], tuple)
        extracted_rand5, count = s.extract(5, 'rand')
        self.assertEqual(count, 5, 'extraction count wrong!')
        extracted_rand_list5 = list(extracted_rand5)
        print('extracted rand list 5:\n', extracted_rand_list5)
        for point in extracted_rand_list5:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], tuple)
            print(f'type of point[1] is {type(point[1])}')
            self.assertIsInstance(point[1], (int, np.int64))
            self.assertIn(point[0], [(0., 10), (1, 'c'), ('a', 'b'), (1, 14)])

        print(f'test incremental extraction')
        pars_list = [(10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250)]
        s = Space(pars_list)
        ext, count = s.extract(64, 'interval')
        self.assertEqual(count, 4096)
        points = list(ext)
        # 已经取出所有的点，围绕其中10个点生成十个subspaces
        # 检查是否每个subspace都为Space，是否都在s范围内，使用32生成点集，检查生成数量是否正确
        for point in points[1000:1010]:
            subspace = s.from_point(point, 64)
            self.assertIsInstance(subspace, Space)
            self.assertTrue(subspace in s)
            self.assertEqual(subspace.dim, 6)
            self.assertEqual(subspace.types, ['conti', 'conti', 'conti', 'conti', 'conti', 'conti'])
            ext, count = subspace.extract(32)
            points = list(ext)
            self.assertGreaterEqual(count, 512)
            self.assertLessEqual(count, 4096)
            print(f'\n---------------------------------'
                  f'\nthe space created around point <{point}> is'
                  f'\n{subspace.boes}'
                  f'\nand extracted {count} points, the first 5 are:'
                  f'\n{points[:5]}')

    def test_axis_extract(self):
        # test axis object with conti type
        axis = Axis((0., 5))
        self.assertIsInstance(axis, Axis)
        self.assertEqual(axis.axis_type, 'conti')
        self.assertEqual(axis.axis_boe, (0., 5.))
        self.assertEqual(axis.count, np.inf)
        self.assertEqual(axis.size, 5.0)
        self.assertTrue(np.allclose(axis.extract(1, 'int'), [0., 1., 2., 3., 4.]))
        self.assertTrue(np.allclose(axis.extract(0.5, 'int'), [0., 0.5, 1., 1.5, 2., 2.5, 3., 3.5, 4., 4.5]))
        extracted = axis.extract(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(0 <= item <= 5) for item in extracted]))

        # test axis object with discrete type
        axis = Axis((1, 5))
        self.assertIsInstance(axis, Axis)
        self.assertEqual(axis.axis_type, 'discr')
        self.assertEqual(axis.axis_boe, (1, 5))
        self.assertEqual(axis.count, 5)
        self.assertEqual(axis.size, 5)
        self.assertTrue(np.allclose(axis.extract(1, 'int'), [1, 2, 3, 4, 5]))
        self.assertRaises(ValueError, axis.extract, 0.5, 'int')
        extracted = axis.extract(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(item in [1, 2, 3, 4, 5]) for item in extracted]))

        # test axis object with enumerate type
        axis = Axis((1, 5, 7, 10, 'A', 'F'))
        self.assertIsInstance(axis, Axis)
        self.assertEqual(axis.axis_type, 'enum')
        self.assertEqual(axis.axis_boe, (1, 5, 7, 10, 'A', 'F'))
        self.assertEqual(axis.count, 6)
        self.assertEqual(axis.size, 6)
        self.assertEqual(axis.extract(1, 'int'), [1, 5, 7, 10, 'A', 'F'])
        self.assertRaises(ValueError, axis.extract, 0.5, 'int')
        extracted = axis.extract(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(item in [1, 5, 7, 10, 'A', 'F']) for item in extracted]))

    def test_from_point(self):
        """测试从一个点生成一个space"""
        # 生成一个space，指定space中的一个点以及distance，生成一个sub-space
        pars_list = [(0., 10), (0, 10)]
        s = Space(pars=pars_list, par_types=None)
        self.assertEqual(s.types, ['conti', 'discr'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10., 11))
        self.assertEqual(s.shape, (np.inf, 11))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        print('create subspace from a point in space')
        p = (3, 3)
        distance = 2
        subspace = s.from_point(p, distance)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['conti', 'discr'])
        self.assertEqual(subspace.dim, 2)
        self.assertEqual(subspace.size, (4.0, 5))
        self.assertEqual(subspace.shape, (np.inf, 5))
        self.assertEqual(subspace.count, np.inf)
        self.assertEqual(subspace.boes, [(1, 5), (1, 5)])

        print('create subspace from a 6 dimensional discrete space')
        s = Space(pars=[(10, 250), (10, 250), (10, 250), (10, 250), (10, 250), (10, 250)])
        p = (15, 200, 150, 150, 150, 150)
        d = 10
        subspace = s.from_point(p, d)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['discr', 'discr', 'discr', 'discr', 'discr', 'discr'])
        self.assertEqual(subspace.dim, 6)
        self.assertEqual(subspace.volume, 65345616)
        self.assertEqual(subspace.size, (16, 21, 21, 21, 21, 21))
        self.assertEqual(subspace.shape, (16, 21, 21, 21, 21, 21))
        self.assertEqual(subspace.count, 65345616)
        self.assertEqual(subspace.boes, [(10, 25), (190, 210), (140, 160), (140, 160), (140, 160), (140, 160)])

        print('create subspace from a 6 dimensional continuous space')
        s = Space(pars=[(10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250)])
        p = (15, 200, 150, 150, 150, 150)
        d = 10
        subspace = s.from_point(p, d)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['conti', 'conti', 'conti', 'conti', 'conti', 'conti'])
        self.assertEqual(subspace.dim, 6)
        self.assertEqual(subspace.volume, 48000000)
        self.assertEqual(subspace.size, (15.0, 20.0, 20.0, 20.0, 20.0, 20.0))
        self.assertEqual(subspace.shape, (np.inf, np.inf, np.inf, np.inf, np.inf, np.inf))
        self.assertEqual(subspace.count, np.inf)
        self.assertEqual(subspace.boes, [(10, 25), (190, 210), (140, 160), (140, 160), (140, 160), (140, 160)])

        print('create subspace with different distances on each dimension')
        s = Space(pars=[(10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250)])
        p = (15, 200, 150, 150, 150, 150)
        d = [10, 5, 5, 10, 10, 5]
        subspace = s.from_point(p, d)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['conti', 'conti', 'conti', 'conti', 'conti', 'conti'])
        self.assertEqual(subspace.dim, 6)
        self.assertEqual(subspace.volume, 6000000)
        self.assertEqual(subspace.size, (15.0, 10.0, 10.0, 20.0, 20.0, 10.0))
        self.assertEqual(subspace.shape, (np.inf, np.inf, np.inf, np.inf, np.inf, np.inf))
        self.assertEqual(subspace.count, np.inf)
        self.assertEqual(subspace.boes, [(10, 25), (195, 205), (145, 155), (140, 160), (140, 160), (145, 155)])


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
        self.assertIsInstance(self.cp1.plan, pd.DataFrame)
        self.assertIsInstance(self.cp2.plan, pd.DataFrame)
        self.assertIsInstance(self.cp3.plan, pd.DataFrame)

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
        self.p = ResultPool(5)
        self.items = ['first', 'second', (1, 2, 3), 'this', 24]
        self.perfs = [1, 2, 3, 4, 5]
        self.additional_result1 = ('abc', 12)
        self.additional_result2 = ([1, 2], -1)
        self.additional_result3 = (12, 5)

    def test_create(self):
        self.assertIsInstance(self.p, ResultPool)

    def test_operation(self):
        self.p.in_pool(self.additional_result1[0], self.additional_result1[1])
        self.p.cut()
        self.assertEqual(self.p.item_count, 1)
        self.assertEqual(self.p.items, ['abc'])
        for item, perf in zip(self.items, self.perfs):
            self.p.in_pool(item, perf)
        self.assertEqual(self.p.item_count, 6)
        self.assertEqual(self.p.items, ['abc', 'first', 'second', (1, 2, 3), 'this', 24])
        self.p.cut()
        self.assertEqual(self.p.items, ['second', (1, 2, 3), 'this', 24, 'abc'])
        self.assertEqual(self.p.perfs, [2, 3, 4, 5, 12])

        self.p.in_pool(self.additional_result2[0], self.additional_result2[1])
        self.p.in_pool(self.additional_result3[0], self.additional_result3[1])
        self.assertEqual(self.p.item_count, 7)
        self.p.cut(keep_largest=False)
        self.assertEqual(self.p.items, [[1, 2], 'second', (1, 2, 3), 'this', 24])
        self.assertEqual(self.p.perfs, [-1, 2, 3, 4, 5])


class TestCoreSubFuncs(unittest.TestCase):
    """Test all functions in core.py"""

    def setUp(self):
        pass

    def test_input_to_list(self):
        print('Testing input_to_list() function')
        input_str = 'first'
        self.assertEqual(qt.utilfuncs.input_to_list(input_str, 3), ['first', 'first', 'first'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_str, 4), ['first', 'first', 'first', 'first'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_str, 2, None), ['first', 'first'])
        input_list = ['first', 'second']
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, 3), ['first', 'second', None])
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, 4, 'padder'), ['first', 'second', 'padder', 'padder'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, 1), ['first', 'second'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, -5), ['first', 'second'])

    def test_point_in_space(self):
        sp = Space([(0., 10.), (0., 10.), (0., 10.)])
        p1 = (5.5, 3.2, 7)
        p2 = (-1, 3, 10)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')
        self.assertFalse(p2 in sp)
        print(f'point {p2} is not in space {sp}')
        sp = Space([(0., 10.), (0., 10.), range(40, 3, -2)], 'conti, conti, enum')
        p1 = (5.5, 3.2, 8)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')

    def test_space_in_space(self):
        print('test if a space is in another space')
        sp = Space([(0., 10.), (0., 10.), (0., 10.)])
        sp2 = Space([(0., 10.), (0., 10.), (0., 10.)])
        self.assertTrue(sp2 in sp)
        self.assertTrue(sp in sp2)
        print(f'space {sp2} is in space {sp}\n'
              f'and space {sp} is in space {sp2}\n'
              f'they are equal to each other\n')
        sp2 = Space([(0, 5.), (2, 7.), (3., 9.)])
        self.assertTrue(sp2 in sp)
        self.assertFalse(sp in sp2)
        print(f'space {sp2} is in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'{sp2} is a sub space of {sp}\n')
        sp2 = Space([(0, 5), (2, 7), (3., 9)])
        self.assertFalse(sp2 in sp)
        self.assertFalse(sp in sp2)
        print(f'space {sp2} is not in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'they have different types of axes\n')
        sp = Space([(0., 10.), (0., 10.), range(40, 3, -2)])
        self.assertFalse(sp in sp2)
        self.assertFalse(sp2 in sp)
        print(f'space {sp2} is not in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'they have different types of axes\n')

    def test_space_around_centre(self):
        sp = Space([(0., 10.), (0., 10.), (0., 10.)])
        p1 = (5.5, 3.2, 7)
        ssp = space_around_centre(space=sp, centre=p1, radius=1.2)
        print(ssp.boes)
        print('\ntest multiple diameters:')
        self.assertEqual(ssp.boes, [(4.3, 6.7), (2.0, 4.4), (5.8, 8.2)])
        ssp = space_around_centre(space=sp, centre=p1, radius=[1, 2, 1])
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(4.5, 6.5), (1.2000000000000002, 5.2), (6.0, 8.0)])
        print('\ntest points on edge:')
        p2 = (5.5, 3.2, 10)
        ssp = space_around_centre(space=sp, centre=p1, radius=3.9)
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(1.6, 9.4), (0.0, 7.1), (3.1, 10.0)])
        print('\ntest enum spaces')
        sp = Space([(0, 100), range(40, 3, -2)], 'discr, enum')
        p1 = [34, 12]
        ssp = space_around_centre(space=sp, centre=p1, radius=5, ignore_enums=False)
        self.assertEqual(ssp.boes, [(29, 39), (22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(ssp.boes)
        print('\ntest enum space and ignore enum axis')
        ssp = space_around_centre(space=sp, centre=p1, radius=5)
        self.assertEqual(ssp.boes, [(29, 39),
                                    (40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(sp.boes)

    def test_get_stock_pool(self):
        print(f'start test building stock pool function\n')
        share_basics = stock_basic(fields='ts_code,symbol,name,area,industry,market,list_date,exchange')

        print(f'\nselect all stocks by area')
        stock_pool = qt.get_stock_pool(area='上海')
        print(f'{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "上海"\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['area'].eq('上海').all())

        print(f'\nselect all stocks by multiple areas')
        stock_pool = qt.get_stock_pool(area='贵州,北京,天津')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are in list of ["贵州", "北京", "天津"]\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['area'].isin(['贵州',
                                                                                              '北京',
                                                                                              '天津']).all())

        print(f'\nselect all stocks by area and industry')
        stock_pool = qt.get_stock_pool(area='四川', industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "四川", and industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['industry'].isin(['银行', '金融']).all())
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['area'].isin(['四川']).all())

        print(f'\nselect all stocks by industry')
        stock_pool = qt.get_stock_pool(industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['industry'].isin(['银行', '金融']).all())

        print(f'\nselect all stocks by market')
        stock_pool = qt.get_stock_pool(market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板"\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['market'].isin(['主板']).all())

        print(f'\nselect all stocks by market and list date')
        stock_pool = qt.get_stock_pool(date='2000-01-01', market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板", and list date after "2000-01-01"\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['market'].isin(['主板']).all())
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['list_date'].le('2000-01-01').all())

        print(f'\nselect all stocks by list date')
        stock_pool = qt.get_stock_pool(date='1997-01-01')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all list date after "1997-01-01"\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['list_date'].le('1997-01-01').all())

        print(f'\nselect all stocks by exchange')
        stock_pool = qt.get_stock_pool(exchange='SSE')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are "SSE"\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['exchange'].eq('SSE').all())

        print(f'\nselect all stocks by industry, area and list date')
        industry_list = ['银行', '全国地产', '互联网', '环境保护', '区域地产',
                         '酒店餐饮', '运输设备', '综合类', '建筑工程', '玻璃',
                         '家用电器', '文教休闲', '其他商业', '元器件', 'IT设备',
                         '其他建材', '汽车服务', '火力发电', '医药商业', '汽车配件',
                         '广告包装', '轻工机械', '新型电力', '多元金融', '饲料']
        area_list = ['深圳', '北京', '吉林', '江苏', '辽宁', '广东',
                     '安徽', '四川', '浙江', '湖南', '河北', '新疆',
                     '山东', '河南', '山西', '江西', '青海', '湖北',
                     '内蒙', '海南', '重庆', '陕西', '福建', '广西',
                     '上海']
        stock_pool = qt.get_stock_pool(date='19980101',
                                       industry=industry_list,
                                       area=area_list)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are "SSE"\n'
              f'{share_basics[np.isin(share_basics.ts_code, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['list_date'].le('1998-01-01').all())
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['industry'].isin(industry_list).all())
        self.assertTrue(share_basics[np.isin(share_basics.ts_code, stock_pool)]['area'].isin(area_list).all())

        self.assertRaises(KeyError, qt.get_stock_pool, industry=25)
        self.assertRaises(KeyError, qt.get_stock_pool, share_name='000300.SH')
        self.assertRaises(KeyError, qt.get_stock_pool, markets='SSE')


class TestEvaluations(unittest.TestCase):
    """Test all evaluation functions in core.py"""

    # 以下手动计算结果在Excel文件中
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

        self.test_data4 = pd.DataFrame([4.97926539, 5.44016005, 5.45122915, 5.74485615, 5.45600553,
                                        5.44858945, 5.2435413, 5.47315161, 5.58464303, 5.36179749,
                                        5.38236326, 5.29614981, 5.76523508, 5.75102892, 6.15316618,
                                        6.03852528, 6.01442228, 5.70510182, 5.22748133, 5.46762379,
                                        5.78926267, 5.8221362, 5.61236849, 5.30615725, 5.24200611,
                                        5.41042642, 5.59940342, 5.28306781, 4.99451932, 5.08799266,
                                        5.38865647, 5.58229139, 5.33492845, 5.48206276, 5.09721379,
                                        5.39190493, 5.29965087, 5.0374415, 5.50798022, 5.43107577,
                                        5.22759507, 4.991809, 5.43153084, 5.39966868, 5.59916352,
                                        5.66412137, 6.00611838, 5.63564902, 5.66723484, 5.29863863,
                                        4.91115153, 5.3749929, 5.75082334, 6.08308148, 6.58091182,
                                        6.77848803, 7.19588758, 7.64862286, 7.99818347, 7.91824794,
                                        8.30341071, 8.45984973, 7.98700002, 8.18924931, 8.60755649,
                                        8.66233396, 8.91018407, 9.0782739, 9.33515448, 8.95870245,
                                        8.98426422, 8.50340317, 8.64916085, 8.93592407, 8.63145745,
                                        8.65322862, 8.39543204, 8.37969997, 8.23394504, 8.04062872,
                                        7.91259763, 7.57252171, 7.72670114, 7.74486117, 8.06908188,
                                        7.99166889, 7.92155906, 8.39956136, 8.80181323, 8.47464091,
                                        8.06557064, 7.87145573, 8.0237959, 8.39481998, 8.68525692,
                                        8.81185461, 8.98632237, 9.0989835, 8.89787405, 8.86508591],
                                       columns=['value'])

        self.test_data5 = pd.DataFrame([4.50258923, 4.35142568, 4.07459514, 3.87791297, 3.73715985,
                                        3.98455684, 4.07587908, 4.00042472, 4.28276612, 4.01362051,
                                        4.13713565, 4.49312372, 4.48633159, 4.4641207, 4.13444605,
                                        3.79107217, 4.22941629, 4.56548511, 4.92472163, 5.27723158,
                                        5.67409193, 6.00176917, 5.88889928, 5.55256103, 5.39308314,
                                        5.2610492, 5.30738908, 5.22222408, 4.90332238, 4.57499908,
                                        4.96097146, 4.81531011, 4.39115442, 4.63200662, 5.04588813,
                                        4.67866025, 5.01705123, 4.83562258, 4.60381702, 4.66187576,
                                        4.41292828, 4.86604507, 4.42280124, 4.07517294, 4.16317319,
                                        4.10316596, 4.42913598, 4.06609666, 3.96725913, 4.15965746,
                                        4.12379564, 4.04054068, 3.84342851, 3.45902867, 3.17649855,
                                        3.09773586, 3.5502119, 3.66396995, 3.66306483, 3.29131401,
                                        2.79558533, 2.88319542, 3.03671098, 3.44645857, 3.88167161,
                                        3.57961874, 3.60180276, 3.96702102, 4.05429995, 4.40056979,
                                        4.05653231, 3.59600456, 3.60792477, 4.09989922, 3.73503663,
                                        4.01892626, 3.94597242, 3.81466605, 3.71417992, 3.93767156,
                                        4.42806557, 4.06988106, 4.03713636, 4.34408673, 4.79810156,
                                        5.18115011, 4.89798406, 5.3960077, 5.72504875, 5.61894017,
                                        5.1958197, 4.85275896, 5.17550207, 4.71548987, 4.62408567,
                                        4.55488535, 4.36532649, 4.26031979, 4.25225607, 4.58627048],
                                       columns=['value'])

        self.test_data6 = pd.DataFrame([5.08639513, 5.05761083, 4.76160923, 4.62166504, 4.62923183,
                                        4.25070173, 4.13447513, 3.90890013, 3.76687608, 3.43342482,
                                        3.67648224, 3.6274775, 3.9385404, 4.39771627, 4.03199346,
                                        3.93265288, 3.50059789, 3.3851961, 3.29743973, 3.2544872,
                                        2.93692949, 2.70893003, 2.55461976, 2.20922332, 2.29054475,
                                        2.2144714, 2.03726827, 2.39007617, 2.29866155, 2.40607111,
                                        2.40440444, 2.79374649, 2.66541922, 2.27018079, 2.08505127,
                                        2.55478864, 2.22415625, 2.58517923, 2.58802256, 2.94870959,
                                        2.69301739, 2.19991535, 2.69473146, 2.64704637, 2.62753542,
                                        2.14240825, 2.38565154, 1.94592117, 2.32243877, 2.69337246,
                                        2.51283854, 2.62484451, 2.15559054, 2.35410875, 2.31219177,
                                        1.96018265, 2.34711266, 2.58083322, 2.40290041, 2.20439791,
                                        2.31472425, 2.16228248, 2.16439749, 2.20080737, 1.73293206,
                                        1.9264407, 2.25089861, 2.69269101, 2.59296687, 2.1420998,
                                        1.67819153, 1.98419023, 2.14479494, 1.89055376, 1.96720648,
                                        1.9916694, 2.37227761, 2.14446036, 2.34573903, 1.86162546,
                                        2.1410721, 2.39204939, 2.52529064, 2.47079939, 2.9299031,
                                        3.09452923, 2.93276708, 3.21731309, 3.06248964, 2.90413406,
                                        2.67844632, 2.45621213, 2.41463398, 2.7373913, 3.14917045,
                                        3.4033949, 3.82283446, 4.02285451, 3.7619638, 4.10346795],
                                       columns=['value'])

        self.test_data7 = pd.DataFrame([4.75233583, 4.47668283, 4.55894263, 4.61765848, 4.622892,
                                        4.58941116, 4.32535872, 3.88112797, 3.47237806, 3.50898953,
                                        3.82530406, 3.6718017, 3.78918195, 4.1800752, 4.01818557,
                                        4.40822582, 4.65474654, 4.89287256, 4.40879274, 4.65505126,
                                        4.36876403, 4.58418934, 4.75687172, 4.3689799, 4.16126498,
                                        4.0203982, 3.77148242, 3.38198096, 3.07261764, 2.9014741,
                                        2.5049543, 2.756105, 2.28779058, 2.16986991, 1.8415962,
                                        1.83319008, 2.20898291, 2.00128981, 1.75747025, 1.26676663,
                                        1.40316876, 1.11126484, 1.60376367, 1.22523829, 1.58816681,
                                        1.49705679, 1.80244138, 1.55128293, 1.35339409, 1.50985759,
                                        1.0808451, 1.05892796, 1.43414812, 1.43039101, 1.73631655,
                                        1.43940867, 1.82864425, 1.71088265, 2.12015154, 2.45417128,
                                        2.84777618, 2.7925612, 2.90975121, 3.25920745, 3.13801182,
                                        3.52733677, 3.65468491, 3.69395211, 3.49862035, 3.24786017,
                                        3.64463138, 4.00331929, 3.62509565, 3.78013949, 3.4174012,
                                        3.76312271, 3.62054004, 3.67206716, 3.60596058, 3.38636199,
                                        3.42580676, 3.32921095, 3.02976759, 3.28258676, 3.45760838,
                                        3.24917528, 2.94618304, 2.86980011, 2.63191259, 2.39566759,
                                        2.53159917, 2.96273967, 3.25626185, 2.97425402, 3.16412191,
                                        3.58280763, 3.23257727, 3.62353556, 3.12806399, 2.92532313],
                                       columns=['value'])

        # 建立一个长度为 500 个数据点的测试数据, 用于测试数据点多于250个的情况下的评价过程
        self.long_data = pd.DataFrame([9.879, 9.916, 10.109, 10.214, 10.361, 10.768, 10.594, 10.288,
                                       10.082, 9.994, 10.125, 10.126, 10.384, 10.734, 10.4, 10.87,
                                       11.338, 11.061, 11.415, 11.724, 12.077, 12.196, 12.064, 12.423,
                                       12.19, 11.729, 11.677, 11.448, 11.485, 10.989, 11.242, 11.239,
                                       11.113, 11.075, 11.471, 11.745, 11.754, 11.782, 12.079, 11.97,
                                       12.178, 11.95, 12.438, 12.612, 12.804, 12.952, 12.612, 12.867,
                                       12.832, 12.832, 13.015, 13.315, 13.249, 12.904, 12.776, 12.64,
                                       12.543, 12.287, 12.225, 11.844, 11.985, 11.945, 11.542, 11.871,
                                       12.245, 12.228, 12.362, 11.899, 11.962, 12.374, 12.816, 12.649,
                                       12.252, 12.579, 12.3, 11.988, 12.177, 12.312, 12.744, 12.599,
                                       12.524, 12.82, 12.67, 12.876, 12.986, 13.271, 13.606, 13.82,
                                       14.161, 13.833, 13.831, 14.137, 13.705, 13.414, 13.037, 12.759,
                                       12.642, 12.948, 13.297, 13.483, 13.836, 14.179, 13.709, 13.655,
                                       13.198, 13.508, 13.953, 14.387, 14.043, 13.987, 13.561, 13.391,
                                       12.923, 12.555, 12.503, 12.292, 11.877, 12.34, 12.141, 11.687,
                                       11.992, 12.458, 12.131, 11.75, 11.739, 11.263, 11.762, 11.976,
                                       11.578, 11.854, 12.136, 12.422, 12.311, 12.56, 12.879, 12.861,
                                       12.973, 13.235, 13.53, 13.531, 13.137, 13.166, 13.31, 13.103,
                                       13.007, 12.643, 12.69, 12.216, 12.385, 12.046, 12.321, 11.9,
                                       11.772, 11.816, 11.871, 11.59, 11.518, 11.94, 11.803, 11.924,
                                       12.183, 12.136, 12.361, 12.406, 11.932, 11.684, 11.292, 11.388,
                                       11.874, 12.184, 12.002, 12.16, 11.741, 11.26, 11.123, 11.534,
                                       11.777, 11.407, 11.275, 11.679, 11.62, 11.218, 11.235, 11.352,
                                       11.366, 11.061, 10.661, 10.582, 10.899, 11.352, 11.792, 11.475,
                                       11.263, 11.538, 11.183, 10.936, 11.399, 11.171, 11.214, 10.89,
                                       10.728, 11.191, 11.646, 11.62, 11.195, 11.178, 11.18, 10.956,
                                       11.205, 10.87, 11.098, 10.639, 10.487, 10.507, 10.92, 10.558,
                                       10.119, 9.882, 9.573, 9.515, 9.845, 9.852, 9.495, 9.726,
                                       10.116, 10.452, 10.77, 11.225, 10.92, 10.824, 11.096, 11.542,
                                       11.06, 10.568, 10.585, 10.884, 10.401, 10.068, 9.964, 10.285,
                                       10.239, 10.036, 10.417, 10.132, 9.839, 9.556, 9.084, 9.239,
                                       9.304, 9.067, 8.587, 8.471, 8.007, 8.321, 8.55, 9.008,
                                       9.138, 9.088, 9.434, 9.156, 9.65, 9.431, 9.654, 10.079,
                                       10.411, 10.865, 10.51, 10.205, 10.519, 10.367, 10.855, 10.642,
                                       10.298, 10.622, 10.173, 9.792, 9.995, 9.904, 9.771, 9.597,
                                       9.506, 9.212, 9.688, 10.032, 9.723, 9.839, 9.918, 10.332,
                                       10.236, 9.989, 10.192, 10.685, 10.908, 11.275, 11.72, 12.158,
                                       12.045, 12.244, 12.333, 12.246, 12.552, 12.958, 13.11, 13.53,
                                       13.123, 13.138, 13.57, 13.389, 13.511, 13.759, 13.698, 13.744,
                                       13.467, 13.795, 13.665, 13.377, 13.423, 13.772, 13.295, 13.073,
                                       12.718, 12.388, 12.399, 12.185, 11.941, 11.818, 11.465, 11.811,
                                       12.163, 11.86, 11.935, 11.809, 12.145, 12.624, 12.768, 12.321,
                                       12.277, 11.889, 12.11, 12.606, 12.943, 12.945, 13.112, 13.199,
                                       13.664, 14.051, 14.189, 14.339, 14.611, 14.656, 15.112, 15.086,
                                       15.263, 15.021, 15.346, 15.572, 15.607, 15.983, 16.151, 16.215,
                                       16.096, 16.089, 16.32, 16.59, 16.657, 16.752, 16.583, 16.743,
                                       16.373, 16.662, 16.243, 16.163, 16.491, 16.958, 16.977, 17.225,
                                       17.637, 17.344, 17.684, 17.892, 18.036, 18.182, 17.803, 17.588,
                                       17.101, 17.538, 17.124, 16.787, 17.167, 17.138, 16.955, 17.148,
                                       17.135, 17.635, 17.718, 17.675, 17.622, 17.358, 17.754, 17.729,
                                       17.576, 17.772, 18.239, 18.441, 18.729, 18.319, 18.608, 18.493,
                                       18.069, 18.122, 18.314, 18.423, 18.709, 18.548, 18.384, 18.391,
                                       17.988, 17.986, 17.653, 17.249, 17.298, 17.06, 17.36, 17.108,
                                       17.348, 17.596, 17.46, 17.635, 17.275, 17.291, 16.933, 17.337,
                                       17.231, 17.146, 17.148, 16.751, 16.891, 17.038, 16.735, 16.64,
                                       16.231, 15.957, 15.977, 16.077, 16.054, 15.797, 15.67, 15.911,
                                       16.077, 16.17, 15.722, 15.258, 14.877, 15.138, 15., 14.811,
                                       14.698, 14.407, 14.583, 14.704, 15.153, 15.436, 15.634, 15.453,
                                       15.877, 15.696, 15.563, 15.927, 16.255, 16.696, 16.266, 16.698,
                                       16.365, 16.493, 16.973, 16.71, 16.327, 16.605, 16.486, 16.846,
                                       16.935, 17.21, 17.389, 17.546, 17.773, 17.641, 17.485, 17.794,
                                       17.354, 16.904, 16.675, 16.43, 16.898, 16.819, 16.921, 17.201,
                                       17.617, 17.368, 17.864, 17.484],
                                      columns=['value'])

        self.long_bench = pd.DataFrame([9.7, 10.179, 10.321, 9.855, 9.936, 10.096, 10.331, 10.662,
                                        10.59, 11.031, 11.154, 10.945, 10.625, 10.233, 10.284, 10.252,
                                        10.221, 10.352, 10.444, 10.773, 10.904, 11.104, 10.797, 10.55,
                                        10.943, 11.352, 11.641, 11.983, 11.696, 12.138, 12.365, 12.379,
                                        11.969, 12.454, 12.947, 13.119, 13.013, 12.763, 12.632, 13.034,
                                        12.681, 12.561, 12.938, 12.867, 13.202, 13.132, 13.539, 13.91,
                                        13.456, 13.692, 13.771, 13.904, 14.069, 13.728, 13.97, 14.228,
                                        13.84, 14.041, 13.963, 13.689, 13.543, 13.858, 14.118, 13.987,
                                        13.611, 14.028, 14.229, 14.41, 14.74, 15.03, 14.915, 15.207,
                                        15.354, 15.665, 15.877, 15.682, 15.625, 15.175, 15.105, 14.893,
                                        14.86, 15.097, 15.178, 15.293, 15.238, 15., 15.283, 14.994,
                                        14.907, 14.664, 14.888, 15.297, 15.313, 15.368, 14.956, 14.802,
                                        14.506, 14.257, 14.619, 15.019, 15.049, 14.625, 14.894, 14.978,
                                        15.434, 15.578, 16.038, 16.107, 16.277, 16.365, 16.204, 16.465,
                                        16.401, 16.895, 17.057, 16.621, 16.225, 16.075, 15.863, 16.292,
                                        16.551, 16.724, 16.817, 16.81, 17.192, 16.86, 16.745, 16.707,
                                        16.552, 16.133, 16.301, 16.08, 15.81, 15.75, 15.909, 16.127,
                                        16.457, 16.204, 16.329, 16.748, 16.624, 17.011, 16.548, 16.831,
                                        16.653, 16.791, 16.57, 16.778, 16.928, 16.932, 17.22, 16.876,
                                        17.301, 17.422, 17.689, 17.316, 17.547, 17.534, 17.409, 17.669,
                                        17.416, 17.859, 17.477, 17.307, 17.245, 17.352, 17.851, 17.412,
                                        17.144, 17.138, 17.085, 16.926, 16.674, 16.854, 17.064, 16.95,
                                        16.609, 16.957, 16.498, 16.552, 16.175, 15.858, 15.697, 15.781,
                                        15.583, 15.36, 15.558, 16.046, 15.968, 15.905, 16.358, 16.783,
                                        17.048, 16.762, 17.224, 17.363, 17.246, 16.79, 16.608, 16.423,
                                        15.991, 15.527, 15.147, 14.759, 14.792, 15.206, 15.148, 15.046,
                                        15.429, 14.999, 15.407, 15.124, 14.72, 14.713, 15.022, 15.092,
                                        14.982, 15.001, 14.734, 14.713, 14.841, 14.562, 15.005, 15.483,
                                        15.472, 15.277, 15.503, 15.116, 15.12, 15.442, 15.476, 15.789,
                                        15.36, 15.764, 16.218, 16.493, 16.642, 17.088, 16.816, 16.645,
                                        16.336, 16.511, 16.2, 15.994, 15.86, 15.929, 16.316, 16.416,
                                        16.746, 17.173, 17.531, 17.627, 17.407, 17.49, 17.768, 17.509,
                                        17.795, 18.147, 18.63, 18.945, 19.021, 19.518, 19.6, 19.744,
                                        19.63, 19.32, 18.933, 19.297, 19.598, 19.446, 19.236, 19.198,
                                        19.144, 19.159, 19.065, 19.032, 18.586, 18.272, 18.119, 18.3,
                                        17.894, 17.744, 17.5, 17.083, 17.092, 16.864, 16.453, 16.31,
                                        16.681, 16.342, 16.447, 16.715, 17.068, 17.067, 16.822, 16.673,
                                        16.675, 16.592, 16.686, 16.397, 15.902, 15.597, 15.357, 15.162,
                                        15.348, 15.603, 15.283, 15.257, 15.082, 14.621, 14.366, 14.039,
                                        13.957, 14.141, 13.854, 14.243, 14.414, 14.033, 13.93, 14.104,
                                        14.461, 14.249, 14.053, 14.165, 14.035, 14.408, 14.501, 14.019,
                                        14.265, 14.67, 14.797, 14.42, 14.681, 15.16, 14.715, 14.292,
                                        14.411, 14.656, 15.094, 15.366, 15.055, 15.198, 14.762, 14.294,
                                        13.854, 13.811, 13.549, 13.927, 13.897, 13.421, 13.037, 13.32,
                                        13.721, 13.511, 13.999, 13.529, 13.418, 13.881, 14.326, 14.362,
                                        13.987, 14.015, 13.599, 13.343, 13.307, 13.689, 13.851, 13.404,
                                        13.577, 13.395, 13.619, 13.195, 12.904, 12.553, 12.294, 12.649,
                                        12.425, 11.967, 12.062, 11.71, 11.645, 12.058, 12.136, 11.749,
                                        11.953, 12.401, 12.044, 11.901, 11.631, 11.396, 11.036, 11.244,
                                        10.864, 11.207, 11.135, 11.39, 11.723, 12.084, 11.8, 11.471,
                                        11.33, 11.504, 11.295, 11.3, 10.901, 10.494, 10.825, 11.054,
                                        10.866, 10.713, 10.875, 10.846, 10.947, 11.422, 11.158, 10.94,
                                        10.521, 10.36, 10.411, 10.792, 10.472, 10.305, 10.525, 10.853,
                                        10.556, 10.72, 10.54, 10.583, 10.299, 10.061, 10.004, 9.903,
                                        9.796, 9.472, 9.246, 9.54, 9.456, 9.177, 9.484, 9.557,
                                        9.493, 9.968, 9.536, 9.39, 8.922, 8.423, 8.518, 8.686,
                                        8.771, 9.098, 9.281, 8.858, 9.027, 8.553, 8.784, 8.996,
                                        9.379, 9.846, 9.855, 9.502, 9.608, 9.761, 9.409, 9.4,
                                        9.332, 9.34, 9.284, 8.844, 8.722, 8.376, 8.775, 8.293,
                                        8.144, 8.63, 8.831, 8.957, 9.18, 9.601, 9.695, 10.018,
                                        9.841, 9.743, 9.292, 8.85, 9.316, 9.288, 9.519, 9.738,
                                        9.289, 9.785, 9.804, 10.06, 10.188, 10.095, 9.739, 9.881,
                                        9.7, 9.991, 10.391, 10.002],
                                       columns=['value'])

    def test_performance_stats(self):
        """test the function performance_statistics()
        """
        pass

    def test_fv(self):
        print(f'test with test data and empty DataFrame')
        self.assertAlmostEqual(eval_fv(self.test_data1), 6.39245474)
        self.assertAlmostEqual(eval_fv(self.test_data2), 10.05126375)
        self.assertAlmostEqual(eval_fv(self.test_data3), 6.95068113)
        self.assertAlmostEqual(eval_fv(self.test_data4), 8.86508591)
        self.assertAlmostEqual(eval_fv(self.test_data5), 4.58627048)
        self.assertAlmostEqual(eval_fv(self.test_data6), 4.10346795)
        self.assertAlmostEqual(eval_fv(self.test_data7), 2.92532313)
        self.assertAlmostEqual(eval_fv(pd.DataFrame()), -np.inf)
        print(f'Error testing')
        self.assertRaises(AssertionError, eval_fv, 15)
        self.assertRaises(KeyError,
                          eval_fv,
                          pd.DataFrame([1, 2, 3], columns=['non_value']))

    def test_max_drawdown(self):
        print(f'test with test data and empty DataFrame')
        self.assertAlmostEqual(eval_max_drawdown(self.test_data1)[0], 0.264274308)
        self.assertEqual(eval_max_drawdown(self.test_data1)[1], 53)
        self.assertEqual(eval_max_drawdown(self.test_data1)[2], 86)
        self.assertTrue(np.isnan(eval_max_drawdown(self.test_data1)[3]))
        self.assertAlmostEqual(eval_max_drawdown(self.test_data2)[0], 0.334690849)
        self.assertEqual(eval_max_drawdown(self.test_data2)[1], 0)
        self.assertEqual(eval_max_drawdown(self.test_data2)[2], 10)
        self.assertEqual(eval_max_drawdown(self.test_data2)[3], 19)
        self.assertAlmostEqual(eval_max_drawdown(self.test_data3)[0], 0.244452899)
        self.assertEqual(eval_max_drawdown(self.test_data3)[1], 90)
        self.assertEqual(eval_max_drawdown(self.test_data3)[2], 99)
        self.assertTrue(np.isnan(eval_max_drawdown(self.test_data3)[3]))
        self.assertAlmostEqual(eval_max_drawdown(self.test_data4)[0], 0.201849684)
        self.assertEqual(eval_max_drawdown(self.test_data4)[1], 14)
        self.assertEqual(eval_max_drawdown(self.test_data4)[2], 50)
        self.assertEqual(eval_max_drawdown(self.test_data4)[3], 54)
        self.assertAlmostEqual(eval_max_drawdown(self.test_data5)[0], 0.534206456)
        self.assertEqual(eval_max_drawdown(self.test_data5)[1], 21)
        self.assertEqual(eval_max_drawdown(self.test_data5)[2], 60)
        self.assertTrue(np.isnan(eval_max_drawdown(self.test_data5)[3]))
        self.assertAlmostEqual(eval_max_drawdown(self.test_data6)[0], 0.670062689)
        self.assertEqual(eval_max_drawdown(self.test_data6)[1], 0)
        self.assertEqual(eval_max_drawdown(self.test_data6)[2], 70)
        self.assertTrue(np.isnan(eval_max_drawdown(self.test_data6)[3]))
        self.assertAlmostEqual(eval_max_drawdown(self.test_data7)[0], 0.783577449)
        self.assertEqual(eval_max_drawdown(self.test_data7)[1], 17)
        self.assertEqual(eval_max_drawdown(self.test_data7)[2], 51)
        self.assertTrue(np.isnan(eval_max_drawdown(self.test_data7)[3]))
        self.assertEqual(eval_max_drawdown(pd.DataFrame()), -np.inf)
        print(f'Error testing')
        self.assertRaises(AssertionError, eval_fv, 15)
        self.assertRaises(KeyError,
                          eval_fv,
                          pd.DataFrame([1, 2, 3], columns=['non_value']))
        # test max drawdown == 0:
        # TODO: investigate: how does divide by zero change?
        self.assertAlmostEqual(eval_max_drawdown(self.test_data4 - 5)[0], 1.0770474121951792)
        self.assertEqual(eval_max_drawdown(self.test_data4 - 5)[1], 14)
        self.assertEqual(eval_max_drawdown(self.test_data4 - 5)[2], 50)

    def test_info_ratio(self):
        reference = self.test_data1
        self.assertAlmostEqual(eval_info_ratio(self.test_data2, reference, 'value'), 0.075553316)
        self.assertAlmostEqual(eval_info_ratio(self.test_data3, reference, 'value'), 0.018949457)
        self.assertAlmostEqual(eval_info_ratio(self.test_data4, reference, 'value'), 0.056328143)
        self.assertAlmostEqual(eval_info_ratio(self.test_data5, reference, 'value'), -0.004270068)
        self.assertAlmostEqual(eval_info_ratio(self.test_data6, reference, 'value'), 0.009198027)
        self.assertAlmostEqual(eval_info_ratio(self.test_data7, reference, 'value'), -0.000890283)

    def test_volatility(self):
        self.assertAlmostEqual(eval_volatility(self.test_data1), 0.748646166)
        self.assertAlmostEqual(eval_volatility(self.test_data2), 0.75527442)
        self.assertAlmostEqual(eval_volatility(self.test_data3), 0.654188853)
        self.assertAlmostEqual(eval_volatility(self.test_data4), 0.688375814)
        self.assertAlmostEqual(eval_volatility(self.test_data5), 1.089989522)
        self.assertAlmostEqual(eval_volatility(self.test_data6), 1.775419308)
        self.assertAlmostEqual(eval_volatility(self.test_data7), 1.962758406)
        self.assertAlmostEqual(eval_volatility(self.test_data1, logarithm=False), 0.750993311)
        self.assertAlmostEqual(eval_volatility(self.test_data2, logarithm=False), 0.75571473)
        self.assertAlmostEqual(eval_volatility(self.test_data3, logarithm=False), 0.655331424)
        self.assertAlmostEqual(eval_volatility(self.test_data4, logarithm=False), 0.692683021)
        self.assertAlmostEqual(eval_volatility(self.test_data5, logarithm=False), 1.09602969)
        self.assertAlmostEqual(eval_volatility(self.test_data6, logarithm=False), 1.774789504)
        self.assertAlmostEqual(eval_volatility(self.test_data7, logarithm=False), 2.003329156)

        self.assertEqual(eval_volatility(pd.DataFrame()), -np.inf)
        self.assertRaises(AssertionError, eval_volatility, [1, 2, 3])

        # 测试长数据的Volatility计算
        expected_volatility = np.array([np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        np.nan, np.nan, np.nan, np.nan, np.nan,
                                        0.39955371, 0.39974258, 0.40309866, 0.40486593, 0.4055514,
                                        0.40710639, 0.40708157, 0.40609006, 0.4073625, 0.40835305,
                                        0.41155304, 0.41218193, 0.41207489, 0.41300276, 0.41308415,
                                        0.41292392, 0.41207645, 0.41238397, 0.41229291, 0.41164056,
                                        0.41316317, 0.41348842, 0.41462249, 0.41474574, 0.41652625,
                                        0.41649176, 0.41701556, 0.4166593, 0.41684221, 0.41491689,
                                        0.41435209, 0.41549087, 0.41849338, 0.41998049, 0.41959106,
                                        0.41907311, 0.41916103, 0.42120773, 0.42052391, 0.42111225,
                                        0.42124589, 0.42356445, 0.42214672, 0.42324022, 0.42476639,
                                        0.42621689, 0.42549439, 0.42533678, 0.42539414, 0.42545038,
                                        0.42593637, 0.42652095, 0.42665489, 0.42699563, 0.42798159,
                                        0.42784512, 0.42898006, 0.42868781, 0.42874188, 0.42789631,
                                        0.4277768, 0.42776827, 0.42685216, 0.42660989, 0.42563155,
                                        0.42618281, 0.42606281, 0.42505222, 0.42653242, 0.42555378,
                                        0.42500842, 0.42561939, 0.42442059, 0.42395414, 0.42384356,
                                        0.42319135, 0.42397497, 0.42488579, 0.42449729, 0.42508766,
                                        0.42509878, 0.42456616, 0.42535577, 0.42681884, 0.42688552,
                                        0.42779918, 0.42706058, 0.42792887, 0.42762114, 0.42894045,
                                        0.42977398, 0.42919859, 0.42829041, 0.42780946, 0.42825318,
                                        0.42858952, 0.42858315, 0.42805601, 0.42764751, 0.42744107,
                                        0.42775518, 0.42707283, 0.4258592, 0.42615335, 0.42526286,
                                        0.4248906, 0.42368986, 0.4232565, 0.42265079, 0.42263954,
                                        0.42153046, 0.42132051, 0.41995353, 0.41916605, 0.41914271,
                                        0.41876945, 0.41740175, 0.41583884, 0.41614026, 0.41457908,
                                        0.41472411, 0.41310876, 0.41261041, 0.41212369, 0.41211677,
                                        0.4100645, 0.40852504, 0.40860297, 0.40745338, 0.40698661,
                                        0.40644546, 0.40591375, 0.40640744, 0.40620663, 0.40656649,
                                        0.40727154, 0.40797605, 0.40807137, 0.40808913, 0.40809676,
                                        0.40711767, 0.40724628, 0.40713077, 0.40772698, 0.40765157,
                                        0.40658297, 0.4065991, 0.405011, 0.40537645, 0.40432626,
                                        0.40390177, 0.40237701, 0.40291623, 0.40301797, 0.40324145,
                                        0.40312864, 0.40328316, 0.40190955, 0.40246506, 0.40237663,
                                        0.40198407, 0.401969, 0.40185623, 0.40198313, 0.40005643,
                                        0.39940743, 0.39850438, 0.39845398, 0.39695093, 0.39697295,
                                        0.39663201, 0.39675444, 0.39538699, 0.39331959, 0.39326074,
                                        0.39193287, 0.39157266, 0.39021327, 0.39062591, 0.38917591,
                                        0.38976991, 0.38864187, 0.38872158, 0.38868096, 0.38868377,
                                        0.38842057, 0.38654784, 0.38649517, 0.38600464, 0.38408115,
                                        0.38323049, 0.38260215, 0.38207663, 0.38142669, 0.38003262,
                                        0.37969367, 0.37768092, 0.37732108, 0.37741991, 0.37617779,
                                        0.37698504, 0.37606784, 0.37499276, 0.37533731, 0.37350437,
                                        0.37375172, 0.37385382, 0.37384003, 0.37338938, 0.37212288,
                                        0.37273075, 0.370559, 0.37038506, 0.37062153, 0.36964661,
                                        0.36818564, 0.3656634, 0.36539259, 0.36428672, 0.36502487,
                                        0.3647148, 0.36551435, 0.36409919, 0.36348181, 0.36254383,
                                        0.36166601, 0.36142665, 0.35954942, 0.35846915, 0.35886759,
                                        0.35813867, 0.35642888, 0.35375231, 0.35061783, 0.35078463,
                                        0.34995508, 0.34688918, 0.34548257, 0.34633158, 0.34622833,
                                        0.34652111, 0.34622774, 0.34540951, 0.34418809, 0.34276593,
                                        0.34160916, 0.33811193, 0.33822709, 0.3391685, 0.33883381])
        test_volatility = eval_volatility(self.long_data)
        test_volatility_roll = self.long_data['volatility'].values
        self.assertAlmostEqual(test_volatility, np.nanmean(expected_volatility))
        self.assertTrue(np.allclose(expected_volatility, test_volatility_roll, equal_nan=True))

    def test_sharp(self):
        self.assertAlmostEqual(eval_sharp(self.test_data1, 5, 0), 0.06135557)
        self.assertAlmostEqual(eval_sharp(self.test_data2, 5, 0), 0.167858667)
        self.assertAlmostEqual(eval_sharp(self.test_data3, 5, 0), 0.09950547)
        self.assertAlmostEqual(eval_sharp(self.test_data4, 5, 0), 0.154928241)
        self.assertAlmostEqual(eval_sharp(self.test_data5, 5, 0.002), 0.007868673)
        self.assertAlmostEqual(eval_sharp(self.test_data6, 5, 0.002), 0.018306537)
        self.assertAlmostEqual(eval_sharp(self.test_data7, 5, 0.002), 0.006259971)

        # 测试长数据的sharp率计算
        expected_sharp = np.array([np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   -0.02346815, -0.02618783, -0.03763912, -0.03296276, -0.03085698,
                                   -0.02851101, -0.02375842, -0.02016746, -0.01107885, -0.01426613,
                                   -0.00787204, -0.01135784, -0.01164232, -0.01003481, -0.00022512,
                                   -0.00046792, -0.01209378, -0.01278892, -0.01298135, -0.01938214,
                                   -0.01671044, -0.02120509, -0.0244281, -0.02416067, -0.02763238,
                                   -0.027579, -0.02372774, -0.02215294, -0.02467094, -0.02091266,
                                   -0.02590194, -0.03049876, -0.02077131, -0.01483653, -0.02488144,
                                   -0.02671638, -0.02561547, -0.01957986, -0.02479803, -0.02703162,
                                   -0.02658087, -0.01641755, -0.01946472, -0.01647757, -0.01280889,
                                   -0.00893643, -0.00643275, -0.00698457, -0.00549962, -0.00654677,
                                   -0.00494757, -0.0035633, -0.00109037, 0.00750654, 0.00451208,
                                   0.00625502, 0.01221367, 0.01326454, 0.01535037, 0.02269538,
                                   0.02028715, 0.02127712, 0.02333264, 0.02273159, 0.01670643,
                                   0.01376513, 0.01265342, 0.02211647, 0.01612449, 0.00856706,
                                   -0.00077147, -0.00268848, 0.00210993, -0.00443934, -0.00411912,
                                   -0.0018756, -0.00867461, -0.00581601, -0.00660835, -0.00861137,
                                   -0.00678614, -0.01188408, -0.00589617, -0.00244323, -0.00201891,
                                   -0.01042846, -0.01471016, -0.02167034, -0.02258554, -0.01306809,
                                   -0.00909086, -0.01233746, -0.00595166, -0.00184208, 0.00750497,
                                   0.01481886, 0.01761972, 0.01562886, 0.01446414, 0.01285826,
                                   0.01357719, 0.00967613, 0.01636272, 0.01458437, 0.02280183,
                                   0.02151903, 0.01700276, 0.01597368, 0.02114336, 0.02233297,
                                   0.02585631, 0.02768459, 0.03519235, 0.04204535, 0.04328161,
                                   0.04672855, 0.05046191, 0.04619848, 0.04525853, 0.05381529,
                                   0.04598861, 0.03947394, 0.04665006, 0.05586077, 0.05617728,
                                   0.06495018, 0.06205172, 0.05665466, 0.06500615, 0.0632062,
                                   0.06084328, 0.05851466, 0.05659229, 0.05159347, 0.0432977,
                                   0.0474047, 0.04231723, 0.03613176, 0.03618391, 0.03591012,
                                   0.03885674, 0.0402686, 0.03846423, 0.04534014, 0.04721458,
                                   0.05130912, 0.05026281, 0.05394312, 0.05529349, 0.05949243,
                                   0.05463304, 0.06195165, 0.06767606, 0.06880985, 0.07048996,
                                   0.07078815, 0.07420767, 0.06773439, 0.0658441, 0.06470875,
                                   0.06302349, 0.06456876, 0.06411282, 0.06216669, 0.067094,
                                   0.07055075, 0.07254976, 0.07119253, 0.06173308, 0.05393352,
                                   0.05681246, 0.05250643, 0.06099845, 0.0655544, 0.06977334,
                                   0.06636514, 0.06177949, 0.06869908, 0.06719767, 0.06178738,
                                   0.05915714, 0.06882277, 0.06756821, 0.06507994, 0.06489791,
                                   0.06553941, 0.073123, 0.07576757, 0.06805446, 0.06063571,
                                   0.05033801, 0.05206971, 0.05540306, 0.05249118, 0.05755587,
                                   0.0586174, 0.05051288, 0.0564852, 0.05757284, 0.06358355,
                                   0.06130082, 0.04925482, 0.03834472, 0.04163981, 0.04648316,
                                   0.04457858, 0.04324626, 0.04328791, 0.04156207, 0.04818652,
                                   0.04972634, 0.06024123, 0.06489556, 0.06255485, 0.06069815,
                                   0.06466389, 0.07081163, 0.07895358, 0.0881782, 0.09374151,
                                   0.08336506, 0.08764795, 0.09080174, 0.08808926, 0.08641158,
                                   0.07811943, 0.06885318, 0.06479503, 0.06851185, 0.07382819,
                                   0.07047903, 0.06658251, 0.07638379, 0.08667974, 0.08867918,
                                   0.08245323, 0.08961866, 0.09905298, 0.0961908, 0.08562706,
                                   0.0839014, 0.0849072, 0.08338395, 0.08783487, 0.09463609,
                                   0.10332336, 0.11806497, 0.11220297, 0.11589097, 0.11678405])
        test_sharp = eval_sharp(self.long_data, 5, 0.00035)
        self.assertAlmostEqual(np.nanmean(expected_sharp), test_sharp)
        self.assertTrue(np.allclose(self.long_data['sharp'].values, expected_sharp, equal_nan=True))

    def test_beta(self):
        reference = self.test_data1
        self.assertAlmostEqual(eval_beta(self.test_data2, reference, 'value'), -0.017148939)
        self.assertAlmostEqual(eval_beta(self.test_data3, reference, 'value'), -0.042204233)
        self.assertAlmostEqual(eval_beta(self.test_data4, reference, 'value'), -0.15652986)
        self.assertAlmostEqual(eval_beta(self.test_data5, reference, 'value'), -0.049195532)
        self.assertAlmostEqual(eval_beta(self.test_data6, reference, 'value'), -0.026995082)
        self.assertAlmostEqual(eval_beta(self.test_data7, reference, 'value'), -0.01147809)

        self.assertRaises(TypeError, eval_beta, [1, 2, 3], reference, 'value')
        self.assertRaises(TypeError, eval_beta, self.test_data3, [1, 2, 3], 'value')
        self.assertRaises(KeyError, eval_beta, self.test_data3, reference, 'not_found_value')

        # 测试长数据的beta计算
        expected_beta = np.array([np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  np.nan, np.nan, np.nan, np.nan, np.nan,
                                  -0.04988841, -0.05127618, -0.04692104, -0.04272652, -0.04080598,
                                  -0.0493347, -0.0460858, -0.0416761, -0.03691527, -0.03724924,
                                  -0.03678865, -0.03987324, -0.03488321, -0.02567672, -0.02690303,
                                  -0.03010128, -0.02437967, -0.02571932, -0.02455681, -0.02839811,
                                  -0.03358653, -0.03396697, -0.03466321, -0.03050966, -0.0247583,
                                  -0.01629325, -0.01880895, -0.01480403, -0.01348783, -0.00544294,
                                  -0.00648176, -0.00467036, -0.01135331, -0.0156841, -0.02340763,
                                  -0.02615705, -0.02730771, -0.02906174, -0.02860664, -0.02412914,
                                  -0.02066416, -0.01744816, -0.02185133, -0.02145285, -0.02681765,
                                  -0.02827694, -0.02394581, -0.02744096, -0.02778825, -0.02703065,
                                  -0.03160023, -0.03615371, -0.03681072, -0.04265126, -0.04344738,
                                  -0.04232421, -0.04705272, -0.04533344, -0.04605934, -0.05272737,
                                  -0.05156463, -0.05134196, -0.04730733, -0.04425352, -0.03869831,
                                  -0.04159571, -0.04223998, -0.04346747, -0.04229844, -0.04740093,
                                  -0.04992507, -0.04621232, -0.04477644, -0.0486915, -0.04598224,
                                  -0.04943463, -0.05006391, -0.05362256, -0.04994067, -0.05464769,
                                  -0.05443275, -0.05513493, -0.05173594, -0.04500994, -0.04662891,
                                  -0.03903505, -0.0419592, -0.04307773, -0.03925718, -0.03711574,
                                  -0.03992631, -0.0433058, -0.04533641, -0.0461183, -0.05600344,
                                  -0.05758377, -0.05959874, -0.05605942, -0.06002859, -0.06253002,
                                  -0.06747014, -0.06427915, -0.05931947, -0.05769974, -0.04791515,
                                  -0.05175088, -0.05748039, -0.05385232, -0.05072975, -0.05052637,
                                  -0.05125567, -0.05005785, -0.05325104, -0.04977727, -0.04947867,
                                  -0.05148544, -0.05739156, -0.05742069, -0.06047279, -0.0558414,
                                  -0.06086126, -0.06265151, -0.06411129, -0.06828052, -0.06781762,
                                  -0.07083409, -0.07211207, -0.06799162, -0.06913295, -0.06775162,
                                  -0.0696265, -0.06678248, -0.06867502, -0.06581961, -0.07055823,
                                  -0.06448184, -0.06097973, -0.05795587, -0.0618383, -0.06130145,
                                  -0.06050652, -0.05936661, -0.05749424, -0.0499, -0.05050495,
                                  -0.04962687, -0.05033439, -0.05070116, -0.05422009, -0.05369759,
                                  -0.05548943, -0.05907353, -0.05933035, -0.05927918, -0.06227663,
                                  -0.06011455, -0.05650432, -0.05828134, -0.05620949, -0.05715323,
                                  -0.05482478, -0.05387113, -0.05095559, -0.05377999, -0.05334267,
                                  -0.05220438, -0.04001521, -0.03892434, -0.03660782, -0.04282708,
                                  -0.04324623, -0.04127048, -0.04227559, -0.04275226, -0.04347049,
                                  -0.04125853, -0.03806295, -0.0330632, -0.03155531, -0.03277152,
                                  -0.03304518, -0.03878731, -0.03830672, -0.03727434, -0.0370571,
                                  -0.04509224, -0.04207632, -0.04116198, -0.04545179, -0.04584584,
                                  -0.05287341, -0.05417433, -0.05175836, -0.05005509, -0.04268674,
                                  -0.03442321, -0.03457309, -0.03613426, -0.03524391, -0.03629479,
                                  -0.04361312, -0.02626705, -0.02406115, -0.03046384, -0.03181044,
                                  -0.03375164, -0.03661673, -0.04520779, -0.04926951, -0.05726738,
                                  -0.0584486, -0.06220608, -0.06800563, -0.06797431, -0.07562211,
                                  -0.07481996, -0.07731229, -0.08413381, -0.09031826, -0.09691925,
                                  -0.11018071, -0.11952675, -0.10826026, -0.11173895, -0.10756359,
                                  -0.10775916, -0.11664559, -0.10505051, -0.10606547, -0.09855355,
                                  -0.10004159, -0.10857084, -0.12209301, -0.11605758, -0.11105113,
                                  -0.1155195, -0.11569505, -0.10513348, -0.09611072, -0.10719791,
                                  -0.10843965, -0.11025856, -0.10247839, -0.10554044, -0.10927647,
                                  -0.10645088, -0.09982498, -0.10542734, -0.09631372, -0.08229695])
        test_beta_mean = eval_beta(self.long_data, self.long_bench, 'value')
        test_beta_roll = self.long_data['beta'].values
        self.assertAlmostEqual(test_beta_mean, np.nanmean(expected_beta))
        self.assertTrue(np.allclose(test_beta_roll, expected_beta, equal_nan=True))

    def test_alpha(self):
        reference = self.test_data1
        self.assertAlmostEqual(eval_alpha(self.test_data2, 5, reference, 'value', 0.5), 11.63072977)
        self.assertAlmostEqual(eval_alpha(self.test_data3, 5, reference, 'value', 0.5), 1.886590071)
        self.assertAlmostEqual(eval_alpha(self.test_data4, 5, reference, 'value', 0.5), 6.827021872)
        self.assertAlmostEqual(eval_alpha(self.test_data5, 5, reference, 'value', 0.92), -1.192265168)
        self.assertAlmostEqual(eval_alpha(self.test_data6, 5, reference, 'value', 0.92), -1.437142359)
        self.assertAlmostEqual(eval_alpha(self.test_data7, 5, reference, 'value', 0.92), -1.781311545)

        # 测试长数据的alpha计算
        expected_alpha = np.array([np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   np.nan, np.nan, np.nan, np.nan, np.nan,
                                   -0.09418119, -0.11188463, -0.17938358, -0.15588172, -0.1462678,
                                   -0.13089586, -0.10780125, -0.09102891, -0.03987585, -0.06075686,
                                   -0.02459503, -0.04104284, -0.0444565, -0.04074585, 0.02191275,
                                   0.02255955, -0.05583375, -0.05875539, -0.06055551, -0.09648245,
                                   -0.07913737, -0.10627829, -0.12320965, -0.12368335, -0.1506743,
                                   -0.15768033, -0.13638829, -0.13065298, -0.14537834, -0.127428,
                                   -0.15504529, -0.18184636, -0.12652146, -0.09190138, -0.14847221,
                                   -0.15840648, -0.1525789, -0.11859418, -0.14700954, -0.16295761,
                                   -0.16051645, -0.10364859, -0.11961134, -0.10258267, -0.08090148,
                                   -0.05727746, -0.0429945, -0.04672356, -0.03581408, -0.0439215,
                                   -0.03429495, -0.0260362, -0.01075022, 0.04931808, 0.02779388,
                                   0.03984083, 0.08311951, 0.08995566, 0.10522428, 0.16159058,
                                   0.14238174, 0.14759783, 0.16257712, 0.158908, 0.11302115,
                                   0.0909566, 0.08272888, 0.15261884, 0.10546376, 0.04990313,
                                   -0.01284111, -0.02720704, 0.00454725, -0.03965491, -0.03818265,
                                   -0.02186992, -0.06574751, -0.04846454, -0.05204211, -0.06316498,
                                   -0.05095099, -0.08502656, -0.04681162, -0.02362027, -0.02205091,
                                   -0.07706374, -0.10371841, -0.14434688, -0.14797935, -0.09055402,
                                   -0.06739549, -0.08824959, -0.04855888, -0.02291244, 0.04027138,
                                   0.09370505, 0.11472939, 0.10243593, 0.0921445, 0.07662648,
                                   0.07946651, 0.05450718, 0.10497677, 0.09068334, 0.15462924,
                                   0.14231034, 0.10544952, 0.09980256, 0.14035223, 0.14942974,
                                   0.17624102, 0.19035477, 0.2500807, 0.30724652, 0.31768915,
                                   0.35007521, 0.38412975, 0.34356521, 0.33614463, 0.41206165,
                                   0.33999177, 0.28045963, 0.34076789, 0.42220356, 0.42314636,
                                   0.50790423, 0.47713348, 0.42520169, 0.50488411, 0.48705211,
                                   0.46252601, 0.44325578, 0.42640573, 0.37986783, 0.30652822,
                                   0.34503393, 0.2999069, 0.24928617, 0.24730218, 0.24326897,
                                   0.26657905, 0.27861168, 0.26392824, 0.32552649, 0.34177792,
                                   0.37837011, 0.37025267, 0.4030612, 0.41339361, 0.45076809,
                                   0.40383354, 0.47093422, 0.52505036, 0.53614256, 0.5500943,
                                   0.55319293, 0.59021451, 0.52358459, 0.50605947, 0.49359168,
                                   0.47895956, 0.49320243, 0.4908336, 0.47310767, 0.51821564,
                                   0.55105932, 0.57291504, 0.5599809, 0.46868842, 0.39620087,
                                   0.42086934, 0.38317217, 0.45934108, 0.50048866, 0.53941991,
                                   0.50676751, 0.46500915, 0.52993663, 0.51668366, 0.46405428,
                                   0.44100603, 0.52726147, 0.51565458, 0.49186248, 0.49001081,
                                   0.49367648, 0.56422294, 0.58882785, 0.51334664, 0.44386256,
                                   0.35056709, 0.36490029, 0.39205071, 0.3677061, 0.41134736,
                                   0.42315067, 0.35356394, 0.40324562, 0.41340007, 0.46503322,
                                   0.44355762, 0.34854314, 0.26412842, 0.28633753, 0.32335224,
                                   0.30761141, 0.29709569, 0.29570487, 0.28000063, 0.32802547,
                                   0.33967726, 0.42511212, 0.46252357, 0.44244974, 0.42152907,
                                   0.45436727, 0.50482359, 0.57339198, 0.6573356, 0.70912003,
                                   0.60328917, 0.6395092, 0.67015805, 0.64241557, 0.62779142,
                                   0.55028063, 0.46448736, 0.43709245, 0.46777983, 0.51789439,
                                   0.48594916, 0.4456216, 0.52008189, 0.60548684, 0.62792473,
                                   0.56645031, 0.62766439, 0.71829315, 0.69481356, 0.59550329,
                                   0.58133754, 0.59014148, 0.58026655, 0.61719273, 0.67373203,
                                   0.75573056, 0.89501633, 0.8347253, 0.87964685, 0.89015835])
        test_alpha_mean = eval_alpha(self.long_data, 100, self.long_bench, 'value')
        test_alpha_roll = self.long_data['alpha'].values
        self.assertAlmostEqual(test_alpha_mean, np.nanmean(expected_alpha))
        self.assertTrue(np.allclose(test_alpha_roll, expected_alpha, equal_nan=True))

    def test_calmar(self):
        """test evaluate function eval_calmar()"""
        pass

    def test_benchmark(self):
        reference = self.test_data1
        tr, yr = eval_benchmark(self.test_data2, reference, 'value')
        self.assertAlmostEqual(tr, 0.19509091)
        self.assertAlmostEqual(yr, 0.929154957)
        tr, yr = eval_benchmark(self.test_data3, reference, 'value')
        self.assertAlmostEqual(tr, 0.19509091)
        self.assertAlmostEqual(yr, 0.929154957)
        tr, yr = eval_benchmark(self.test_data4, reference, 'value')
        self.assertAlmostEqual(tr, 0.19509091)
        self.assertAlmostEqual(yr, 0.929154957)
        tr, yr = eval_benchmark(self.test_data5, reference, 'value')
        self.assertAlmostEqual(tr, 0.19509091)
        self.assertAlmostEqual(yr, 0.929154957)
        tr, yr = eval_benchmark(self.test_data6, reference, 'value')
        self.assertAlmostEqual(tr, 0.19509091)
        self.assertAlmostEqual(yr, 0.929154957)
        tr, yr = eval_benchmark(self.test_data7, reference, 'value')
        self.assertAlmostEqual(tr, 0.19509091)
        self.assertAlmostEqual(yr, 0.929154957)

    def test_evaluate(self):
        pass


class TestLoop(unittest.TestCase):
    """通过一个假设但精心设计的例子来测试loop_step以及loop方法的正确性"""

    def setUp(self):
        # 精心设计的模拟股票名称、交易日期、以及股票价格
        self.shares = ['share1', 'share2', 'share3', 'share4', 'share5', 'share6', 'share7']
        self.dates = ['2016/07/01', '2016/07/04', '2016/07/05', '2016/07/06', '2016/07/07',
                      '2016/07/08', '2016/07/11', '2016/07/12', '2016/07/13', '2016/07/14',
                      '2016/07/15', '2016/07/18', '2016/07/19', '2016/07/20', '2016/07/21',
                      '2016/07/22', '2016/07/25', '2016/07/26', '2016/07/27', '2016/07/28',
                      '2016/07/29', '2016/08/01', '2016/08/02', '2016/08/03', '2016/08/04',
                      '2016/08/05', '2016/08/08', '2016/08/09', '2016/08/10', '2016/08/11',
                      '2016/08/12', '2016/08/15', '2016/08/16', '2016/08/17', '2016/08/18',
                      '2016/08/19', '2016/08/22', '2016/08/23', '2016/08/24', '2016/08/25',
                      '2016/08/26', '2016/08/29', '2016/08/30', '2016/08/31', '2016/09/01',
                      '2016/09/02', '2016/09/05', '2016/09/06', '2016/09/07', '2016/09/08',
                      '2016/09/09', '2016/09/12', '2016/09/13', '2016/09/14', '2016/09/15',
                      '2016/09/16', '2016/09/19', '2016/09/20', '2016/09/21', '2016/09/22',
                      '2016/09/23', '2016/09/26', '2016/09/27', '2016/09/28', '2016/09/29',
                      '2016/09/30', '2016/10/10', '2016/10/11', '2016/10/12', '2016/10/13',
                      '2016/10/14', '2016/10/17', '2016/10/18', '2016/10/19', '2016/10/20',
                      '2016/10/21', '2016/10/23', '2016/10/24', '2016/10/25', '2016/10/26',
                      '2016/10/27', '2016/10/29', '2016/10/30', '2016/10/31', '2016/11/01',
                      '2016/11/02', '2016/11/05', '2016/11/06', '2016/11/07', '2016/11/08',
                      '2016/11/09', '2016/11/12', '2016/11/13', '2016/11/14', '2016/11/15',
                      '2016/11/16', '2016/11/19', '2016/11/20', '2016/11/21', '2016/11/22']
        self.dates = [pd.Timestamp(date_text) for date_text in self.dates]
        self.prices = np.array([[5.35, 5.09, 5.03, 4.98, 4.50, 5.09, 4.75],
                                [5.66, 4.84, 5.21, 5.44, 4.35, 5.06, 4.48],
                                [5.79, 4.60, 5.02, 5.45, 4.07, 4.76, 4.56],
                                [5.56, 4.63, 5.50, 5.74, 3.88, 4.62, 4.62],
                                [5.88, 4.64, 5.07, 5.46, 3.74, 4.63, 4.62],
                                [6.25, 4.51, 5.11, 5.45, 3.98, 4.25, 4.59],
                                [5.93, 4.96, 5.15, 5.24, 4.08, 4.13, 4.33],
                                [6.39, 4.65, 5.02, 5.47, 4.00, 3.91, 3.88],
                                [6.31, 4.26, 5.10, 5.58, 4.28, 3.77, 3.47],
                                [5.86, 3.77, 5.24, 5.36, 4.01, 3.43, 3.51],
                                [5.61, 3.39, 4.93, 5.38, 4.14, 3.68, 3.83],
                                [5.31, 3.76, 4.96, 5.30, 4.49, 3.63, 3.67],
                                [5.40, 4.06, 5.40, 5.77, 4.49, 3.94, 3.79],
                                [5.03, 3.87, 5.74, 5.75, 4.46, 4.40, 4.18],
                                [5.38, 3.91, 5.53, 6.15, 4.13, 4.03, 4.02],
                                [5.79, 4.13, 5.79, 6.04, 3.79, 3.93, 4.41],
                                [6.27, 4.27, 5.68, 6.01, 4.23, 3.50, 4.65],
                                [6.59, 4.57, 5.90, 5.71, 4.57, 3.39, 4.89],
                                [6.91, 5.04, 5.75, 5.23, 4.92, 3.30, 4.41],
                                [6.71, 5.31, 6.11, 5.47, 5.28, 3.25, 4.66],
                                [6.33, 5.40, 5.77, 5.79, 5.67, 2.94, 4.37],
                                [6.07, 5.21, 5.85, 5.82, 6.00, 2.71, 4.58],
                                [5.98, 5.06, 5.61, 5.61, 5.89, 2.55, 4.76],
                                [6.46, 4.69, 5.75, 5.31, 5.55, 2.21, 4.37],
                                [6.95, 5.12, 5.50, 5.24, 5.39, 2.29, 4.16],
                                [6.77, 5.27, 5.14, 5.41, 5.26, 2.21, 4.02],
                                [6.70, 5.72, 5.31, 5.60, 5.31, 2.04, 3.77],
                                [6.28, 6.10, 5.68, 5.28, 5.22, 2.39, 3.38],
                                [6.61, 6.27, 5.73, 4.99, 4.90, 2.30, 3.07],
                                [6.25, 6.49, 6.04, 5.09, 4.57, 2.41, 2.90],
                                [6.47, 6.16, 6.27, 5.39, 4.96, 2.40, 2.50],
                                [6.45, 6.26, 6.60, 5.58, 4.82, 2.79, 2.76],
                                [6.88, 6.39, 6.10, 5.33, 4.39, 2.67, 2.29],
                                [7.00, 6.58, 6.25, 5.48, 4.63, 2.27, 2.17],
                                [6.59, 6.20, 6.73, 5.10, 5.05, 2.09, 1.84],
                                [6.59, 5.70, 6.91, 5.39, 4.68, 2.55, 1.83],
                                [6.64, 5.20, 7.01, 5.30, 5.02, 2.22, 2.21],
                                [6.38, 5.37, 7.36, 5.04, 4.84, 2.59, 2.00],
                                [6.10, 5.40, 7.72, 5.51, 4.60, 2.59, 1.76],
                                [6.35, 5.22, 7.68, 5.43, 4.66, 2.95, 1.27],
                                [6.52, 5.38, 7.62, 5.23, 4.41, 2.69, 1.40],
                                [6.87, 5.53, 7.74, 4.99, 4.87, 2.20, 1.11],
                                [6.84, 6.03, 7.53, 5.43, 4.42, 2.69, 1.60],
                                [7.09, 5.77, 7.46, 5.40, 4.08, 2.65, 1.23],
                                [6.88, 5.66, 7.84, 5.60, 4.16, 2.63, 1.59],
                                [6.84, 6.08, 8.11, 5.66, 4.10, 2.14, 1.50],
                                [6.98, 5.62, 8.04, 6.01, 4.43, 2.39, 1.80],
                                [7.02, 5.63, 7.65, 5.64, 4.07, 1.95, 1.55],
                                [7.13, 6.11, 7.52, 5.67, 3.97, 2.32, 1.35],
                                [7.59, 6.03, 7.67, 5.30, 4.16, 2.69, 1.51],
                                [7.61, 6.27, 7.47, 4.91, 4.12, 2.51, 1.08],
                                [7.21, 6.28, 7.44, 5.37, 4.04, 2.62, 1.06],
                                [7.48, 6.52, 7.59, 5.75, 3.84, 2.16, 1.43],
                                [7.66, 7.00, 7.94, 6.08, 3.46, 2.35, 1.43],
                                [7.51, 7.34, 8.25, 6.58, 3.18, 2.31, 1.74],
                                [7.12, 7.34, 7.77, 6.78, 3.10, 1.96, 1.44],
                                [6.97, 7.68, 8.03, 7.20, 3.55, 2.35, 1.83],
                                [6.67, 8.09, 7.87, 7.65, 3.66, 2.58, 1.71],
                                [6.20, 7.68, 7.58, 8.00, 3.66, 2.40, 2.12],
                                [6.34, 7.58, 7.33, 7.92, 3.29, 2.20, 2.45],
                                [6.22, 7.46, 7.22, 8.30, 2.80, 2.31, 2.85],
                                [5.98, 7.59, 6.86, 8.46, 2.88, 2.16, 2.79],
                                [6.37, 7.19, 7.18, 7.99, 3.04, 2.16, 2.91],
                                [6.56, 7.40, 7.54, 8.19, 3.45, 2.20, 3.26],
                                [6.26, 7.48, 7.24, 8.61, 3.88, 1.73, 3.14],
                                [6.69, 7.93, 6.85, 8.66, 3.58, 1.93, 3.53],
                                [7.13, 8.23, 6.60, 8.91, 3.60, 2.25, 3.65],
                                [6.83, 8.35, 6.65, 9.08, 3.97, 2.69, 3.69],
                                [7.31, 8.44, 6.74, 9.34, 4.05, 2.59, 3.50],
                                [7.43, 8.35, 7.19, 8.96, 4.40, 2.14, 3.25],
                                [7.54, 8.58, 7.14, 8.98, 4.06, 1.68, 3.64],
                                [7.18, 8.82, 6.88, 8.50, 3.60, 1.98, 4.00],
                                [7.21, 9.09, 7.14, 8.65, 3.61, 2.14, 3.63],
                                [7.45, 9.02, 7.30, 8.94, 4.10, 1.89, 3.78],
                                [7.37, 8.87, 6.95, 8.63, 3.74, 1.97, 3.42],
                                [6.88, 9.22, 7.02, 8.65, 4.02, 1.99, 3.76],
                                [7.08, 9.04, 7.38, 8.40, 3.95, 2.37, 3.62],
                                [6.75, 8.60, 7.50, 8.38, 3.81, 2.14, 3.67],
                                [6.60, 8.48, 7.60, 8.23, 3.71, 2.35, 3.61],
                                [6.21, 8.71, 7.15, 8.04, 3.94, 1.86, 3.39],
                                [6.36, 8.79, 7.30, 7.91, 4.43, 2.14, 3.43],
                                [6.82, 8.93, 7.80, 7.57, 4.07, 2.39, 3.33],
                                [6.45, 9.36, 8.15, 7.73, 4.04, 2.53, 3.03],
                                [6.85, 9.68, 8.40, 7.74, 4.34, 2.47, 3.28],
                                [6.48, 10.16, 8.87, 8.07, 4.80, 2.93, 3.46],
                                [6.10, 10.56, 8.53, 7.99, 5.18, 3.09, 3.25],
                                [5.64, 10.63, 8.94, 7.92, 4.90, 2.93, 2.95],
                                [6.01, 10.55, 8.52, 8.40, 5.40, 3.22, 2.87],
                                [6.21, 10.65, 8.80, 8.80, 5.73, 3.06, 2.63],
                                [6.61, 10.55, 8.92, 8.47, 5.62, 2.90, 2.40],
                                [7.02, 10.19, 9.20, 8.07, 5.20, 2.68, 2.53],
                                [7.04, 10.48, 8.71, 7.87, 4.85, 2.46, 2.96],
                                [6.77, 10.36, 8.25, 8.02, 5.18, 2.41, 3.26],
                                [7.09, 10.03, 8.19, 8.39, 4.72, 2.74, 2.97],
                                [6.65, 10.24, 7.80, 8.69, 4.62, 3.15, 3.16],
                                [7.07, 10.01, 7.69, 8.81, 4.55, 3.40, 3.58],
                                [6.80, 10.14, 7.23, 8.99, 4.37, 3.82, 3.23],
                                [6.79, 10.31, 6.98, 9.10, 4.26, 4.02, 3.62],
                                [6.48, 9.88, 7.07, 8.90, 4.25, 3.76, 3.13],
                                [6.39, 10.05, 6.95, 8.87, 4.59, 4.10, 2.93]])

        # 精心设计的模拟PT持股仓位目标信号：
        self.pt_signals = np.array([[0.000, 0.000, 0.000, 0.000, 0.250, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.250, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.250, 0.100, 0.150],
                                    [0.200, 0.200, 0.000, 0.000, 0.250, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.250, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.200, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.100, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.050, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.050, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.050, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.050, 0.000, 0.062, 0.100, 0.150],
                                    [0.133, 0.200, 0.050, 0.000, 0.062, 0.100, 0.000],
                                    [0.133, 0.200, 0.050, 0.000, 0.262, 0.100, 0.000],
                                    [0.133, 0.200, 0.050, 0.000, 0.262, 0.100, 0.000],
                                    [0.133, 0.200, 0.050, 0.000, 0.262, 0.100, 0.000],
                                    [0.066, 0.200, 0.050, 0.150, 0.262, 0.100, 0.000],
                                    [0.066, 0.200, 0.050, 0.150, 0.262, 0.100, 0.000],
                                    [0.066, 0.200, 0.050, 0.150, 0.262, 0.100, 0.000],
                                    [0.066, 0.200, 0.050, 0.150, 0.262, 0.100, 0.000],
                                    [0.066, 0.200, 0.050, 0.150, 0.262, 0.100, 0.000],
                                    [0.066, 0.200, 0.250, 0.150, 0.000, 0.300, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.386, 0.136, 0.170, 0.102, 0.000, 0.204, 0.000],
                                    [0.460, 0.119, 0.149, 0.089, 0.000, 0.179, 0.000],
                                    [0.460, 0.119, 0.149, 0.089, 0.000, 0.179, 0.000],
                                    [0.460, 0.119, 0.149, 0.089, 0.000, 0.179, 0.000],
                                    [0.446, 0.116, 0.145, 0.087, 0.000, 0.087, 0.116],
                                    [0.446, 0.116, 0.145, 0.087, 0.000, 0.087, 0.116],
                                    [0.446, 0.116, 0.145, 0.087, 0.000, 0.087, 0.116],
                                    [0.446, 0.116, 0.145, 0.087, 0.000, 0.087, 0.116],
                                    [0.446, 0.116, 0.145, 0.087, 0.000, 0.087, 0.116],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.400, 0.208, 0.130, 0.078, 0.000, 0.078, 0.104],
                                    [0.370, 0.193, 0.120, 0.072, 0.072, 0.072, 0.096],
                                    [0.000, 0.222, 0.138, 0.222, 0.083, 0.222, 0.111],
                                    [0.000, 0.222, 0.138, 0.222, 0.083, 0.222, 0.111],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.121, 0.195, 0.121, 0.195, 0.073, 0.195, 0.097],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.200, 0.320, 0.200, 0.000, 0.120, 0.000, 0.160],
                                    [0.047, 0.380, 0.238, 0.000, 0.142, 0.000, 0.190],
                                    [0.047, 0.380, 0.238, 0.000, 0.142, 0.000, 0.190],
                                    [0.043, 0.434, 0.217, 0.000, 0.130, 0.000, 0.173],
                                    [0.043, 0.434, 0.217, 0.000, 0.130, 0.000, 0.173],
                                    [0.043, 0.434, 0.217, 0.000, 0.130, 0.000, 0.173],
                                    [0.043, 0.434, 0.217, 0.000, 0.130, 0.000, 0.173],
                                    [0.043, 0.434, 0.217, 0.000, 0.130, 0.000, 0.173],
                                    [0.043, 0.434, 0.217, 0.000, 0.130, 0.000, 0.173],
                                    [0.045, 0.454, 0.227, 0.000, 0.000, 0.000, 0.272],
                                    [0.045, 0.454, 0.227, 0.000, 0.000, 0.000, 0.272],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.050, 0.000, 0.250, 0.000, 0.000, 0.000, 0.300],
                                    [0.000, 0.000, 0.400, 0.000, 0.000, 0.000, 0.300],
                                    [0.000, 0.000, 0.400, 0.000, 0.000, 0.000, 0.300],
                                    [0.000, 0.000, 0.400, 0.000, 0.000, 0.000, 0.300]])

        # 精心设计的模拟PS比例交易信号，与模拟PT信号高度相似
        self.ps_signals = np.array([[0.000, 0.000, 0.000, 0.000, 0.250, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.100, 0.150],
                                    [0.200, 0.200, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.100, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, -0.750, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [-0.333, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, -0.500, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, -1.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.200, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [-0.500, 0.000, 0.000, 0.150, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.200, 0.000, -1.000, 0.200, 0.000],
                                    [0.500, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.200, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, -0.500, 0.200],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.200, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.150, 0.000, 0.000],
                                    [-1.000, 0.000, 0.000, 0.250, 0.000, 0.250, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.250, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, -1.000, 0.000, -1.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [-0.800, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.100, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, -1.000, 0.000, 0.100],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, -1.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [-1.000, 0.000, 0.150, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                                    [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]])

        # 精心设计的模拟VS股票交易信号，与模拟PS信号类似
        self.vs_signals = np.array([[000, 000, 000, 000, 500, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 300, 300],
                                    [400, 400, 000, 000, 000, 000, 000],
                                    [000, 000, 250, 000, 000, 000, 000],
                                    [000, 000, 000, 000, -400, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [-200, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, -200, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, -300],
                                    [000, 000, 000, 000, 500, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [-200, 000, 000, 300, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 400, 000, -300, 600, 000],
                                    [500, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [600, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, -400, 600],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 500, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 300, 000, 000],
                                    [-500, 000, 000, 500, 000, 200, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [500, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, -700, 000, -600, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [-400, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 300, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, -600, 000, 300],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, -300, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [-200, 000, 700, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000],
                                    [000, 000, 000, 000, 000, 000, 000]])

        # 精心设计的模拟多价格交易信号，模拟50个交易日对三只股票的操作
        self.multi_shares = ['000010', '000030', '000039']
        self.multi_dates = ['2016/07/01', '2016/07/04', '2016/07/05', '2016/07/06', '2016/07/07',
                            '2016/07/08', '2016/07/11', '2016/07/12', '2016/07/13', '2016/07/14',
                            '2016/07/15', '2016/07/18', '2016/07/19', '2016/07/20', '2016/07/21',
                            '2016/07/22', '2016/07/25', '2016/07/26', '2016/07/27', '2016/07/28',
                            '2016/07/29', '2016/08/01', '2016/08/02', '2016/08/03', '2016/08/04',
                            '2016/08/05', '2016/08/08', '2016/08/09', '2016/08/10', '2016/08/11',
                            '2016/08/12', '2016/08/15', '2016/08/16', '2016/08/17', '2016/08/18',
                            '2016/08/19', '2016/08/22', '2016/08/23', '2016/08/24', '2016/08/25',
                            '2016/08/26', '2016/08/29', '2016/08/30', '2016/08/31', '2016/09/01',
                            '2016/09/02', '2016/09/05', '2016/09/06', '2016/09/07', '2016/09/08']
        self.multi_dates = [pd.Timestamp(date_text) for date_text in self.multi_dates]
        # 操作的交易价格包括开盘价、最高价和收盘价
        self.multi_prices_open = np.array([[10.02, 9.88, 7.26],
                                           [10.00, 9.88, 7.00],
                                           [9.98, 9.89, 6.88],
                                           [9.97, 9.75, 6.91],
                                           [9.99, 9.74, np.nan],
                                           [10.01, 9.80, 6.81],
                                           [10.04, 9.62, 6.63],
                                           [10.06, 9.65, 6.45],
                                           [10.06, 9.58, 6.16],
                                           [10.11, 9.67, 6.24],
                                           [10.11, 9.81, 5.96],
                                           [10.07, 9.80, 5.97],
                                           [10.06, 10.00, 5.96],
                                           [10.09, 9.95, 6.20],
                                           [10.03, 10.10, 6.35],
                                           [10.02, 10.06, 6.11],
                                           [10.06, 10.14, 6.37],
                                           [10.08, 9.90, 5.58],
                                           [9.99, 10.20, 5.65],
                                           [10.00, 10.29, 5.65],
                                           [10.03, 9.86, 5.19],
                                           [10.02, 9.48, 5.42],
                                           [10.06, 10.01, 6.30],
                                           [10.03, 10.24, 6.15],
                                           [9.97, 10.26, 6.05],
                                           [9.94, 10.24, 5.89],
                                           [9.83, 10.12, 5.22],
                                           [9.78, 10.65, 5.20],
                                           [9.77, 10.64, 5.07],
                                           [9.91, 10.56, 6.04],
                                           [9.92, 10.42, 6.12],
                                           [9.97, 10.43, 5.85],
                                           [9.91, 10.29, 5.67],
                                           [9.90, 10.30, 6.02],
                                           [9.88, 10.44, 6.04],
                                           [9.91, 10.60, 7.07],
                                           [9.63, 10.67, 7.64],
                                           [9.64, 10.46, 7.99],
                                           [9.57, 10.39, 7.59],
                                           [9.55, 10.90, 8.73],
                                           [9.58, 11.01, 8.72],
                                           [9.61, 11.01, 8.97],
                                           [9.62, np.nan, 8.58],
                                           [9.55, np.nan, 8.71],
                                           [9.57, 10.82, 8.77],
                                           [9.61, 11.02, 8.40],
                                           [9.63, 10.96, 7.95],
                                           [9.64, 11.55, 7.76],
                                           [9.61, 11.74, 8.25],
                                           [9.56, 11.80, 7.51]])
        self.multi_prices_high = np.array([[10.07, 9.91, 7.41],
                                           [10.00, 10.04, 7.31],
                                           [10.00, 9.93, 7.14],
                                           [10.00, 10.04, 7.00],
                                           [10.03, 9.84, np.nan],
                                           [10.03, 9.88, 6.82],
                                           [10.04, 9.99, 6.96],
                                           [10.09, 9.70, 6.85],
                                           [10.10, 9.67, 6.50],
                                           [10.14, 9.71, 6.34],
                                           [10.11, 9.85, 6.04],
                                           [10.10, 9.90, 6.02],
                                           [10.09, 10.00, 6.12],
                                           [10.09, 10.20, 6.38],
                                           [10.10, 10.11, 6.43],
                                           [10.05, 10.18, 6.46],
                                           [10.07, 10.21, 6.43],
                                           [10.09, 10.26, 6.27],
                                           [10.10, 10.38, 5.77],
                                           [10.00, 10.47, 6.01],
                                           [10.04, 10.42, 5.67],
                                           [10.04, 10.07, 5.67],
                                           [10.06, 10.24, 6.35],
                                           [10.09, 10.27, 6.32],
                                           [10.05, 10.38, 6.43],
                                           [9.97, 10.43, 6.36],
                                           [9.96, 10.39, 5.79],
                                           [9.86, 10.65, 5.47],
                                           [9.77, 10.84, 5.65],
                                           [9.92, 10.65, 6.04],
                                           [9.94, 10.73, 6.14],
                                           [9.97, 10.63, 6.23],
                                           [9.97, 10.51, 5.83],
                                           [9.92, 10.35, 6.25],
                                           [9.92, 10.46, 6.27],
                                           [9.92, 10.63, 7.12],
                                           [9.93, 10.74, 7.82],
                                           [9.64, 10.76, 8.14],
                                           [9.58, 10.54, 8.27],
                                           [9.60, 11.02, 8.92],
                                           [9.58, 11.12, 8.76],
                                           [9.62, 11.17, 9.15],
                                           [9.62, np.nan, 8.90],
                                           [9.64, np.nan, 9.01],
                                           [9.59, 10.92, 9.16],
                                           [9.62, 11.15, 9.00],
                                           [9.63, 11.11, 8.27],
                                           [9.70, 11.55, 7.99],
                                           [9.66, 11.95, 8.33],
                                           [9.64, 11.93, 8.25]])
        self.multi_prices_close = np.array([[10.04, 9.68, 6.64],
                                            [10.00, 9.87, 7.26],
                                            [10.00, 9.86, 7.03],
                                            [9.99, 9.87, 6.87],
                                            [9.97, 9.79, np.nan],
                                            [9.99, 9.82, 6.64],
                                            [10.03, 9.80, 6.85],
                                            [10.03, 9.66, 6.70],
                                            [10.06, 9.62, 6.39],
                                            [10.06, 9.58, 6.22],
                                            [10.11, 9.69, 5.92],
                                            [10.09, 9.78, 5.91],
                                            [10.07, 9.75, 6.11],
                                            [10.06, 9.96, 5.91],
                                            [10.09, 9.90, 6.23],
                                            [10.03, 10.04, 6.28],
                                            [10.03, 10.06, 6.28],
                                            [10.06, 10.08, 6.27],
                                            [10.08, 10.24, 5.70],
                                            [10.00, 10.24, 5.56],
                                            [9.99, 10.24, 5.67],
                                            [10.03, 9.86, 5.16],
                                            [10.03, 10.13, 5.69],
                                            [10.06, 10.12, 6.32],
                                            [10.03, 10.10, 6.14],
                                            [9.97, 10.25, 6.25],
                                            [9.94, 10.24, 5.79],
                                            [9.83, 10.22, 5.26],
                                            [9.77, 10.75, 5.05],
                                            [9.84, 10.64, 5.45],
                                            [9.91, 10.56, 6.06],
                                            [9.93, 10.60, 6.21],
                                            [9.96, 10.42, 5.69],
                                            [9.91, 10.25, 5.46],
                                            [9.91, 10.24, 6.02],
                                            [9.88, 10.49, 6.69],
                                            [9.91, 10.57, 7.43],
                                            [9.64, 10.63, 7.72],
                                            [9.56, 10.48, 8.16],
                                            [9.57, 10.37, 7.83],
                                            [9.55, 10.96, 8.70],
                                            [9.57, 11.02, 8.71],
                                            [9.61, np.nan, 8.88],
                                            [9.61, np.nan, 8.54],
                                            [9.55, 10.88, 8.87],
                                            [9.57, 10.87, 8.87],
                                            [9.63, 11.01, 8.18],
                                            [9.64, 11.01, 7.80],
                                            [9.65, 11.58, 7.97],
                                            [9.62, 11.80, 8.25]])
        # 交易信号包括三组，分别作用与开盘价、最高价和收盘价
        # 此时的关键是股票交割期的处理，交割期不为0时，以交易日为单位交割
        self.multi_signals = []
        # multisignal的第一组信号为开盘价信号
        self.multi_signals.append(
                pd.DataFrame(np.array([[0.000, 0.000, 0.000],
                                       [0.000, -0.500, 0.000],
                                       [0.000, -0.500, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.150, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.300, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.300],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.350, 0.250],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.100, 0.000, 0.350],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.200, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.050, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000]]),
                             columns=self.multi_shares,
                             index=self.multi_dates
                             )
        )
        # 第二组信号为最高价信号
        self.multi_signals.append(
                pd.DataFrame(np.array([[0.000, 0.150, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, -0.200, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.200],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000]]),
                             columns=self.multi_shares,
                             index=self.multi_dates
                             )
        )
        # 第三组信号为收盘价信号
        self.multi_signals.append(
                pd.DataFrame(np.array([[0.000, 0.200, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [-0.500, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, -0.800],
                                       [0.000, 0.000, 0.000],
                                       [0.000, -1.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [-0.750, 0.000, 0.000],
                                       [0.000, 0.000, -0.850],
                                       [0.000, 0.000, 0.000],
                                       [0.000, -0.700, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, -1.000],
                                       [0.000, 0.000, 0.000],
                                       [0.000, 0.000, 0.000],
                                       [-1.000, 0.000, 0.000],
                                       [0.000, -1.000, 0.000],
                                       [0.000, 0.000, 0.000]]),
                             columns=self.multi_shares,
                             index=self.multi_dates
                             )
        )

        # 交易回测所需的价格也有三组，分别是开盘价、最高价和收盘价
        self.multi_histories = []
        # multisignal的第一组信号为开盘价信号
        self.multi_histories.append(
                pd.DataFrame(self.multi_prices_open,
                             columns=self.multi_shares,
                             index=self.multi_dates
                             )
        )
        # 第二组信号为最高价信号
        self.multi_histories.append(
                pd.DataFrame(self.multi_prices_high,
                             columns=self.multi_shares,
                             index=self.multi_dates
                             )
        )
        # 第三组信号为收盘价信号
        self.multi_histories.append(
                pd.DataFrame(self.multi_prices_close,
                             columns=self.multi_shares,
                             index=self.multi_dates
                             )
        )

        # 设置回测参数
        self.cash = qt.CashPlan(['2016/07/01', '2016/08/12', '2016/09/23'], [10000, 10000, 10000])
        self.rate = qt.Cost(buy_fix=0,
                            sell_fix=0,
                            buy_rate=0,
                            sell_rate=0,
                            buy_min=0,
                            sell_min=0,
                            slipage=0)
        self.rate2 = qt.Cost(buy_fix=0,
                             sell_fix=0,
                             buy_rate=0,
                             sell_rate=0,
                             buy_min=10,
                             sell_min=5,
                             slipage=0)
        self.pt_signal_hp = dataframe_to_hp(
                pd.DataFrame(self.pt_signals, index=self.dates, columns=self.shares),
                htypes='close'
        )
        self.ps_signal_hp = dataframe_to_hp(
                pd.DataFrame(self.ps_signals, index=self.dates, columns=self.shares),
                htypes='close'
        )
        self.vs_signal_hp = dataframe_to_hp(
                pd.DataFrame(self.vs_signals, index=self.dates, columns=self.shares),
                htypes='close'
        )
        self.multi_signal_hp = stack_dataframes(
                self.multi_signals,
                stack_along='htypes',
                htypes='open, high, close'
        )
        self.history_list = dataframe_to_hp(
                pd.DataFrame(self.prices, index=self.dates, columns=self.shares),
                htypes='close'
        )
        self.multi_history_list = stack_dataframes(
                self.multi_histories,
                stack_along='htypes',
                htypes='open, high, close'
        )

        # 模拟PT信号回测结果
        # PT信号，先卖后买，交割期为0
        self.pt_res_sb00 = np.array(
                [[0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 10000.0000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 9916.6667],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 321.0892, 6035.8333, 0.0000, 9761.1111],
                 [348.0151, 417.9188, 0.0000, 0.0000, 555.5556, 0.0000, 321.0892, 2165.9050, 0.0000, 9674.8209],
                 [348.0151, 417.9188, 0.0000, 0.0000, 555.5556, 0.0000, 321.0892, 2165.9050, 0.0000, 9712.5872],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9910.7240],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9919.3782],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9793.0692],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9513.8217],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9123.5935],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9000.5995],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9053.4865],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9248.7142],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9161.1372],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9197.3369],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9504.6981],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9875.2461],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10241.5400],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10449.2398],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10628.3269],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10500.7893],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 0.0000, 5233.1396, 0.0000, 10449.2776],
                 [348.0151, 417.9188, 0.0000, 0.0000, 459.8694, 0.0000, 0.0000, 3433.8551, 0.0000, 10338.2857],
                 [348.0151, 417.9188, 0.0000, 0.0000, 459.8694, 0.0000, 0.0000, 3433.8551, 0.0000, 10194.3474],
                 [348.0151, 417.9188, 0.0000, 0.0000, 459.8694, 0.0000, 0.0000, 3433.8551, 0.0000, 10471.0008],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10411.2629],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10670.0618],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10652.4799],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10526.1488],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10458.6614],
                 [101.4983, 417.9188, 821.7315, 288.6672, 0.0000, 2576.1284, 0.0000, 4487.0722, 0.0000, 20609.0270],
                 [1216.3282, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21979.4972],
                 [1216.3282, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21880.9628],
                 [1216.3282, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21630.0454],
                 [1216.3282, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 20968.0007],
                 [1216.3282, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21729.9339],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 21107.6400],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 21561.1745],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 21553.0916],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 22316.9366],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 22084.2862],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 21777.3543],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 22756.8225],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 22843.4697],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 0.0000, 2172.0393, 0.0000, 22762.1766],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 1448.0262, 0.0000, 0.0000, 22257.0973],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 1448.0262, 0.0000, 0.0000, 23136.5259],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 1448.0262, 0.0000, 0.0000, 21813.7852],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 1448.0262, 0.0000, 0.0000, 22395.3204],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 1448.0262, 0.0000, 0.0000, 23717.6858],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 1607.1030, 1448.0262, 0.0000, 0.0000, 22715.4263],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 22498.3254],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 23341.1733],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 24162.3941],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 24847.1508],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 23515.9755],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 24555.8997],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 24390.6372],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 24073.3309],
                 [1216.3282, 417.9188, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 2455.7405, 0.0000, 24394.6500],
                 [2076.3314, 903.0334, 511.8829, 288.6672, 0.0000, 669.7975, 1448.0262, 3487.5655, 0.0000, 34904.8150],
                 [0.0000, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 4608.8037, 0.0000, 34198.4475],
                 [0.0000, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 4608.8037, 0.0000, 33753.0190],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 34953.8178],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 33230.2498],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 35026.7819],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 36976.2649],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 38673.8147],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 38717.3429],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 36659.0854],
                 [644.7274, 903.0334, 511.8829, 897.4061, 0.0000, 3514.8404, 1448.0262, 379.3918, 0.0000, 35877.9607],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 36874.4840],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 37010.2695],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 38062.3510],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 36471.1357],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 37534.9927],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 37520.2569],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 36747.7952],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 36387.9409],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 35925.9715],
                 [644.7274, 1337.8498, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 2853.5665, 0.0000, 36950.7028],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 0.0000, 0.0000, 37383.2463],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 0.0000, 0.0000, 37761.2724],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 0.0000, 0.0000, 39548.2653],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 0.0000, 0.0000, 41435.1291],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 0.0000, 0.0000, 41651.6261],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 1229.1495, 0.0000, 1448.0262, 0.0000, 0.0000, 41131.9920],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 0.0000, 0.0000, 41286.4702],
                 [644.7274, 1657.3981, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 0.0000, 0.0000, 40978.7259],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 40334.5453],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 41387.9172],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 42492.6707],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 42953.7188],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 42005.1092],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 42017.9106],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 43750.2824],
                 [644.7274, 0.0000, 1071.9327, 0.0000, 0.0000, 0.0000, 3760.7116, 17485.5497, 0.0000, 41766.8679],
                 [0.0000, 0.0000, 2461.8404, 0.0000, 0.0000, 0.0000, 3760.7116, 12161.6930, 0.0000, 42959.1150],
                 [0.0000, 0.0000, 2461.8404, 0.0000, 0.0000, 0.0000, 3760.7116, 12161.6930, 0.0000, 41337.9320],
                 [0.0000, 0.0000, 2461.8404, 0.0000, 0.0000, 0.0000, 3760.7116, 12161.6930, 0.0000, 40290.3688]])
        # PT信号，先买后卖，交割期为0
        self.pt_res_bs00 = np.array(
                [[0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 10000.0000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 9916.6667],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 321.0892, 6035.8333, 0.0000, 9761.1111],
                 [348.0151, 417.9188, 0.0000, 0.0000, 555.5556, 0.0000, 321.0892, 2165.9050, 0.0000, 9674.8209],
                 [348.0151, 417.9188, 0.0000, 0.0000, 555.5556, 0.0000, 321.0892, 2165.9050, 0.0000, 9712.5872],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9910.7240],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9919.3782],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9793.0692],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9513.8217],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9123.5935],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9000.5995],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9053.4865],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9248.7142],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9161.1372],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9197.3369],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9504.6981],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 9875.2461],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10241.5400],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10449.2398],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10628.3269],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 321.0892, 3762.5512, 0.0000, 10500.7893],
                 [348.0151, 417.9188, 0.0000, 0.0000, 154.3882, 0.0000, 0.0000, 5233.1396, 0.0000, 10449.2776],
                 [348.0151, 417.9188, 0.0000, 0.0000, 459.8694, 0.0000, 0.0000, 3433.8551, 0.0000, 10338.2857],
                 [348.0151, 417.9188, 0.0000, 0.0000, 459.8694, 0.0000, 0.0000, 3433.8551, 0.0000, 10194.3474],
                 [348.0151, 417.9188, 0.0000, 0.0000, 459.8694, 0.0000, 0.0000, 3433.8551, 0.0000, 10471.0008],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10411.2629],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10670.0618],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10652.4799],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10526.1488],
                 [101.4983, 417.9188, 0.0000, 288.6672, 459.8694, 0.0000, 0.0000, 3541.0848, 0.0000, 10458.6614],
                 [101.4983, 417.9188, 821.7315, 288.6672, 0.0000, 2576.1284, 0.0000, 4487.0722, 0.0000, 20609.0270],
                 [797.1684, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 2703.5808, 0.0000, 21979.4972],
                 [1190.1307, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21700.7241],
                 [1190.1307, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21446.6630],
                 [1190.1307, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 20795.3593],
                 [1190.1307, 417.9188, 821.7315, 288.6672, 0.0000, 1607.1030, 0.0000, 0.0000, 0.0000, 21557.2924],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 20933.6887],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 21392.5581],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 21390.2918],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 22147.7562],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 21910.9053],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 21594.2980],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 22575.4380],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 22655.8312],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 0.0000, 2201.6110, 0.0000, 22578.4365],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 1467.7407, 0.0000, 0.0000, 22073.2661],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 1467.7407, 0.0000, 0.0000, 22955.2367],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 1467.7407, 0.0000, 0.0000, 21628.1647],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 1467.7407, 0.0000, 0.0000, 22203.4237],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 1607.1030, 1467.7407, 0.0000, 0.0000, 23516.2598],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 22505.8428],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 22199.1042],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 23027.9302],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 23848.5806],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 24540.8871],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 23205.6838],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 24267.6685],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 24115.3796],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 23814.3667],
                 [1190.1307, 417.9188, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 2278.3728, 0.0000, 24133.6611],
                 [2061.6837, 896.6628, 507.6643, 288.6672, 0.0000, 699.3848, 1467.7407, 3285.8830, 0.0000, 34658.5742],
                 [0.0000, 896.6628, 507.6643, 466.6033, 0.0000, 1523.7106, 1467.7407, 12328.8684, 0.0000, 33950.7917],
                 [0.0000, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 4380.3797, 0.0000, 33711.4045],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 34922.0959],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 33237.1081],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 35031.8071],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 36976.3376],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 38658.5245],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 38712.2854],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 36655.3125],
                 [644.1423, 896.6628, 507.6643, 936.6623, 0.0000, 3464.7832, 1467.7407, 154.8061, 0.0000, 35904.3692],
                 [644.1423, 902.2617, 514.8253, 0.0000, 15.5990, 0.0000, 1467.7407, 14821.9004, 0.0000, 36873.9080],
                 [644.1423, 902.2617, 514.8253, 0.0000, 1220.8683, 0.0000, 1467.7407, 10470.8781, 0.0000, 36727.7895],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 37719.9840],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 36138.1277],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 37204.0760],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 37173.1201],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 36398.2298],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 36034.2178],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 35583.6399],
                 [644.1423, 1338.1812, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 2753.1120, 0.0000, 36599.2645],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 0.0000, 0.0000, 37013.3408],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 0.0000, 0.0000, 37367.7449],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 0.0000, 0.0000, 39143.8273],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 0.0000, 0.0000, 41007.3074],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 0.0000, 0.0000, 41225.4657],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 1220.8683, 0.0000, 1467.7407, 0.0000, 0.0000, 40685.9525],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 0.0000, 0.0000, 1467.7407, 6592.6891, 0.0000, 40851.5435],
                 [644.1423, 1646.4805, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 0.0000, 0.0000, 41082.1210],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 40385.0135],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 41455.1513],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 42670.6769],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 43213.7233],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 42205.2480],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 42273.9386],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 44100.0777],
                 [644.1423, 0.0000, 1033.4242, 0.0000, 0.0000, 0.0000, 3974.4666, 17370.3689, 0.0000, 42059.7208],
                 [0.0000, 0.0000, 2483.9522, 0.0000, 0.0000, 0.0000, 3974.4666, 11619.4102, 0.0000, 43344.9653],
                 [0.0000, 0.0000, 2483.9522, 0.0000, 0.0000, 0.0000, 3974.4666, 11619.4102, 0.0000, 41621.0324],
                 [0.0000, 0.0000, 2483.9522, 0.0000, 0.0000, 0.0000, 3974.4666, 11619.4102, 0.0000, 40528.0648]])
        # PT信号，先卖后买，交割期为2天（股票）0天（现金）以便利用先卖的现金继续买入
        self.pt_res_sb20 = np.array(
                [[0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 10000.000],
                 [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 9916.667],
                 [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 321.089, 6035.833, 0.000, 9761.111],
                 [348.015, 417.919, 0.000, 0.000, 555.556, 0.000, 321.089, 2165.905, 0.000, 9674.821],
                 [348.015, 417.919, 0.000, 0.000, 555.556, 0.000, 321.089, 2165.905, 0.000, 9712.587],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9910.724],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9919.378],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9793.069],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9513.822],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9123.593],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9000.600],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9053.487],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9248.714],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9161.137],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9197.337],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9504.698],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9875.246],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10241.540],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10449.240],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10628.327],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10500.789],
                 [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 0.000, 5233.140, 0.000, 10449.278],
                 [348.015, 417.919, 0.000, 0.000, 459.869, 0.000, 0.000, 3433.855, 0.000, 10338.286],
                 [348.015, 417.919, 0.000, 0.000, 459.869, 0.000, 0.000, 3433.855, 0.000, 10194.347],
                 [348.015, 417.919, 0.000, 0.000, 459.869, 0.000, 0.000, 3433.855, 0.000, 10471.001],
                 [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10411.263],
                 [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10670.062],
                 [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10652.480],
                 [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10526.149],
                 [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10458.661],
                 [101.498, 417.919, 821.732, 288.667, 0.000, 2576.128, 0.000, 4487.072, 0.000, 20609.027],
                 [797.168, 417.919, 821.732, 288.667, 0.000, 2576.128, 0.000, 0.000, 0.000, 21979.497],
                 [1156.912, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21584.441],
                 [1156.912, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21309.576],
                 [1156.912, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 20664.323],
                 [1156.912, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21445.597],
                 [1156.912, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 2223.240, 0.000, 20806.458],
                 [1156.912, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 2223.240, 0.000, 21288.441],
                 [1156.912, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 2223.240, 0.000, 21294.365],
                 [1156.912, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 2223.240, 0.000, 22058.784],
                 [1156.912, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 2223.240, 0.000, 21805.540],
                 [1156.912, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 2223.240, 0.000, 21456.333],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22459.720],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22611.602],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22470.912],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21932.634],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22425.864],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21460.103],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22376.968],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 23604.295],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 22704.826],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 22286.293],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 23204.755],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 24089.017],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 24768.185],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 23265.196],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 24350.540],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 24112.706],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 23709.076],
                 [1481.947, 417.919, 504.579, 288.667, 0.000, 763.410, 1577.904, 0.000, 0.000, 24093.545],
                 [2060.275, 896.050, 504.579, 288.667, 0.000, 763.410, 1577.904, 2835.944, 0.000, 34634.888],
                 [578.327, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 732.036, 0.000, 33912.261],
                 [0.000, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 4415.981, 0.000, 33711.951],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 34951.433],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 33224.596],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 35065.209],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 37018.699],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 38706.035],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 38724.569],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 36647.268],
                 [644.683, 896.050, 504.579, 889.896, 0.000, 3485.427, 1577.904, 186.858, 0.000, 35928.930],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 36967.229],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 37056.598],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 38129.862],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 36489.333],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 37599.602],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 37566.823],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 36799.280],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 36431.196],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 35940.942],
                 [644.683, 1341.215, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 2367.759, 0.000, 36973.050],
                 [644.683, 1606.361, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 0.000, 0.000, 37393.292],
                 [644.683, 1606.361, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 0.000, 0.000, 37711.276],
                 [644.683, 1606.361, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 0.000, 0.000, 39515.991],
                 [644.683, 1606.361, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 0.000, 0.000, 41404.440],
                 [644.683, 1606.361, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 0.000, 0.000, 41573.523],
                 [644.683, 1606.361, 1074.629, 0.000, 1232.241, 0.000, 1577.904, 0.000, 0.000, 41011.613],
                 [644.683, 1606.361, 1074.629, 0.000, 0.000, 0.000, 3896.406, 0.000, 0.000, 41160.181],
                 [644.683, 1606.361, 1074.629, 0.000, 0.000, 0.000, 3896.406, 0.000, 0.000, 40815.512],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 40145.531],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 41217.281],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 42379.061],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 42879.589],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 41891.452],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 41929.003],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 43718.052],
                 [644.683, 0.000, 1074.629, 0.000, 0.000, 0.000, 3896.406, 16947.110, 0.000, 41685.916],
                 [0.000, 0.000, 2460.195, 0.000, 0.000, 0.000, 3896.406, 11653.255, 0.000, 42930.410],
                 [0.000, 0.000, 2460.195, 0.000, 0.000, 0.000, 3896.406, 11653.255, 0.000, 41242.589],
                 [0.000, 0.000, 2460.195, 0.000, 0.000, 0.000, 3896.406, 11653.255, 0.000, 40168.084]])
        # PT信号，先买后卖，交割期为2天（股票）1天（现金）
        self.pt_res_bs21 = np.array([
            [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 10000.000],
            [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 9916.667],
            [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 321.089, 6035.833, 0.000, 9761.111],
            [348.015, 417.919, 0.000, 0.000, 555.556, 0.000, 321.089, 2165.905, 0.000, 9674.821],
            [348.015, 417.919, 0.000, 0.000, 555.556, 0.000, 321.089, 2165.905, 0.000, 9712.587],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9910.724],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9919.378],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9793.069],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9513.822],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9123.593],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9000.600],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9053.487],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9248.714],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9161.137],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9197.337],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9504.698],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 9875.246],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10241.540],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10449.240],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10628.327],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 321.089, 3762.551, 0.000, 10500.789],
            [348.015, 417.919, 0.000, 0.000, 154.388, 0.000, 0.000, 5233.140, 0.000, 10449.278],
            [348.015, 417.919, 0.000, 0.000, 459.869, 0.000, 0.000, 3433.855, 0.000, 10338.286],
            [348.015, 417.919, 0.000, 0.000, 459.869, 0.000, 0.000, 3433.855, 0.000, 10194.347],
            [348.015, 417.919, 0.000, 0.000, 459.869, 0.000, 0.000, 3433.855, 0.000, 10471.001],
            [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10411.263],
            [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10670.062],
            [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10652.480],
            [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10526.149],
            [101.498, 417.919, 0.000, 288.667, 459.869, 0.000, 0.000, 3541.085, 0.000, 10458.661],
            [101.498, 417.919, 821.732, 288.667, 0.000, 2576.128, 0.000, 4487.072, 0.000, 20609.027],
            [797.168, 417.919, 821.732, 288.667, 0.000, 2576.128, 0.000, 0.000, 0.000, 21979.497],
            [797.168, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 2475.037, 0.000, 21584.441],
            [1150.745, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21266.406],
            [1150.745, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 20623.683],
            [1150.745, 417.919, 821.732, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21404.957],
            [1150.745, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 2230.202, 0.000, 20765.509],
            [1150.745, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 2230.202, 0.000, 21248.748],
            [1150.745, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 2230.202, 0.000, 21256.041],
            [1150.745, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 2230.202, 0.000, 22018.958],
            [1150.745, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 2230.202, 0.000, 21764.725],
            [1150.745, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 2230.202, 0.000, 21413.241],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22417.021],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22567.685],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22427.699],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21889.359],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22381.938],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 21416.358],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 1649.148, 0.000, 0.000, 0.000, 22332.786],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 0.000, 2386.698, 0.000, 23557.595],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 23336.992],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 22907.742],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 24059.201],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 24941.902],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 25817.514],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 24127.939],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 25459.688],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 25147.370],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 2209.906, 0.000, 0.000, 25005.842],
            [1476.798, 417.919, 503.586, 288.667, 0.000, 761.900, 1086.639, 2752.004, 0.000, 25598.700],
            [2138.154, 929.921, 503.586, 288.667, 0.000, 761.900, 1086.639, 4818.835, 0.000, 35944.098],
            [661.356, 929.921, 503.586, 553.843, 0.000, 1954.237, 1086.639, 8831.252, 0.000, 35237.243],
            [0.000, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 9460.955, 0.000, 35154.442],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 36166.632],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 34293.883],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 35976.901],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 37848.552],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 39512.574],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 39538.024],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 37652.984],
            [667.098, 929.921, 503.586, 553.843, 0.000, 3613.095, 1086.639, 5084.792, 0.000, 36687.909],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 37749.277],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 37865.518],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 38481.190],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 37425.087],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 38051.341],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 38065.478],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 37429.495],
            [667.098, 1108.871, 745.260, 0.000, 512.148, 0.000, 1086.639, 11861.593, 0.000, 37154.479],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 36692.717],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 37327.055],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 37937.630],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 38298.645],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 39689.369],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 40992.397],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 41092.265],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 1086.639, 7576.628, 0.000, 40733.622],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 3726.579, 0.000, 0.000, 40708.515],
            [667.098, 1600.830, 745.260, 0.000, 512.148, 0.000, 3726.579, 0.000, 0.000, 40485.321],
            [667.098, 0.000, 745.260, 0.000, 512.148, 0.000, 3726.579, 16888.760, 0.000, 39768.059],
            [667.098, 0.000, 745.260, 0.000, 512.148, 0.000, 3726.579, 16888.760, 0.000, 40519.595],
            [667.098, 0.000, 745.260, 0.000, 512.148, 0.000, 3726.579, 16888.760, 0.000, 41590.937],
            [667.098, 0.000, 1283.484, 0.000, 512.148, 0.000, 3726.579, 12448.413, 0.000, 42354.983],
            [667.098, 0.000, 1283.484, 0.000, 512.148, 0.000, 3726.579, 12448.413, 0.000, 41175.149],
            [667.098, 0.000, 1283.484, 0.000, 512.148, 0.000, 3726.579, 12448.413, 0.000, 41037.902],
            [667.098, 0.000, 1283.484, 0.000, 512.148, 0.000, 3726.579, 12448.413, 0.000, 42706.213],
            [667.098, 0.000, 1283.484, 0.000, 512.148, 0.000, 3726.579, 12448.413, 0.000, 40539.205],
            [0.000, 0.000, 2384.452, 0.000, 512.148, 0.000, 3726.579, 9293.252, 0.000, 41608.692],
            [0.000, 0.000, 2384.452, 0.000, 512.148, 0.000, 3726.579, 9293.252, 0.000, 39992.148],
            [0.000, 0.000, 2384.452, 0.000, 512.148, 0.000, 3726.579, 9293.252, 0.000, 39134.828]])
        # 模拟PS信号回测结果
        # PS信号，先卖后买，交割期为0
        self.ps_res_sb00 = np.array(
                [[0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 10000.0000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 9916.6667],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 205.0654, 321.0892, 5059.7222, 0.0000, 9761.1111],
                 [346.9824, 416.6787, 0.0000, 0.0000, 555.5556, 205.0654, 321.0892, 1201.2775, 0.0000, 9646.1118],
                 [346.9824, 416.6787, 191.0372, 0.0000, 555.5556, 205.0654, 321.0892, 232.7189, 0.0000, 9685.5858],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9813.2184],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9803.1288],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9608.0198],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9311.5727],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 8883.6246],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 8751.3900],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 8794.1811],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9136.5704],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9209.3588],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9093.8294],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9387.5537],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9585.9589],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 9928.7771],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 10060.3806],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 10281.0021],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 10095.5613],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 0.0000, 4506.3926, 0.0000, 10029.9571],
                 [231.4373, 416.6787, 95.5186, 0.0000, 474.2238, 205.0654, 0.0000, 2531.2699, 0.0000, 9875.6133],
                 [231.4373, 416.6787, 95.5186, 0.0000, 474.2238, 205.0654, 0.0000, 2531.2699, 0.0000, 9614.9463],
                 [231.4373, 416.6787, 95.5186, 0.0000, 474.2238, 205.0654, 0.0000, 2531.2699, 0.0000, 9824.1722],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9732.5743],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9968.3391],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 10056.1579],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9921.4925],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9894.1621],
                 [115.7186, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 6179.7742, 0.0000, 20067.9370],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21133.5080],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20988.8485],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20596.7429],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 19910.7730],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20776.7070],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20051.7969],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20725.3884],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20828.8795],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21647.1811],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21310.1687],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20852.0993],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21912.3952],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21937.8282],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21962.4576],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 21389.4018],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 22027.4535],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 20939.9992],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 21250.0636],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 22282.7812],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 21407.0658],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 21160.2373],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 21826.7682],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 22744.9403],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 23466.1185],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 22017.8821],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 23191.4662],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 23099.0822],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 22684.7671],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 1339.2073, 0.0000, 0.0000, 22842.1346],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 1785.2055, 938.6967, 1339.2073, 5001.4246, 0.0000,
                  33323.8359],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 32820.2901],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 32891.2308],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 34776.5296],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 33909.0325],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 34560.1906],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 36080.4552],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 38618.4454],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 38497.9230],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 37110.0991],
                 [0.0000, 416.6787, 735.6442, 944.9611, 1785.2055, 3582.8836, 1339.2073, 0.0000, 0.0000, 35455.2467],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 35646.1860],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 35472.3020],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 36636.4694],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 35191.7035],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 36344.2242],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 36221.6005],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 35943.5708],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 35708.2608],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 35589.0286],
                 [0.0000, 416.6787, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 15126.2788, 0.0000, 36661.0285],
                 [0.0000, 823.2923, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 11495.2197, 0.0000, 36310.5909],
                 [0.0000, 823.2923, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 11495.2197, 0.0000, 36466.7637],
                 [0.0000, 823.2923, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 11495.2197, 0.0000, 37784.4918],
                 [0.0000, 823.2923, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 11495.2197, 0.0000, 39587.6766],
                 [0.0000, 823.2923, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 11495.2197, 0.0000, 40064.0191],
                 [0.0000, 823.2923, 735.6442, 0.0000, 1785.2055, 0.0000, 1339.2073, 11495.2197, 0.0000, 39521.6439],
                 [0.0000, 823.2923, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 17142.1018, 0.0000, 39932.2761],
                 [0.0000, 823.2923, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 17142.1018, 0.0000, 39565.2475],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 38943.1632],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 39504.1184],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 40317.8004],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 40798.5768],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 39962.5711],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 40194.4793],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 41260.4003],
                 [0.0000, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 2730.5758, 25827.8351, 0.0000, 39966.3024],
                 [0.0000, 0.0000, 1613.4518, 0.0000, 0.0000, 0.0000, 2730.5758, 19700.7377, 0.0000, 40847.3160],
                 [0.0000, 0.0000, 1613.4518, 0.0000, 0.0000, 0.0000, 2730.5758, 19700.7377, 0.0000, 39654.5445],
                 [0.0000, 0.0000, 1613.4518, 0.0000, 0.0000, 0.0000, 2730.5758, 19700.7377, 0.0000, 38914.8151]])
        # PS信号，先买后卖，交割期为0
        self.ps_res_bs00 = np.array(
                [[0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 10000.0000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 0.0000, 0.0000, 7500.0000, 0.0000, 9916.6667],
                 [0.0000, 0.0000, 0.0000, 0.0000, 555.5556, 205.0654, 321.0892, 5059.7222, 0.0000, 9761.1111],
                 [346.9824, 416.6787, 0.0000, 0.0000, 555.5556, 205.0654, 321.0892, 1201.2775, 0.0000, 9646.1118],
                 [346.9824, 416.6787, 191.0372, 0.0000, 555.5556, 205.0654, 321.0892, 232.7189, 0.0000, 9685.5858],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9813.2184],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9803.1288],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9608.0198],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9311.5727],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 8883.6246],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 8751.3900],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 8794.1811],
                 [346.9824, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 1891.0523, 0.0000, 9136.5704],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9209.3588],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9093.8294],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9387.5537],
                 [231.4373, 416.6787, 191.0372, 0.0000, 138.8889, 205.0654, 321.0892, 2472.2444, 0.0000, 9585.9589],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 9928.7771],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 10060.3806],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 10281.0021],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 321.0892, 3035.8041, 0.0000, 10095.5613],
                 [231.4373, 416.6787, 95.5186, 0.0000, 138.8889, 205.0654, 0.0000, 4506.3926, 0.0000, 10029.9571],
                 [231.4373, 416.6787, 95.5186, 0.0000, 474.2238, 205.0654, 0.0000, 2531.2699, 0.0000, 9875.6133],
                 [231.4373, 416.6787, 95.5186, 0.0000, 474.2238, 205.0654, 0.0000, 2531.2699, 0.0000, 9614.9463],
                 [231.4373, 416.6787, 95.5186, 0.0000, 474.2238, 205.0654, 0.0000, 2531.2699, 0.0000, 9824.1722],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9732.5743],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9968.3391],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 10056.1579],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9921.4925],
                 [115.7186, 416.6787, 95.5186, 269.8496, 474.2238, 205.0654, 0.0000, 1854.7990, 0.0000, 9894.1621],
                 [115.7186, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 6179.7742, 0.0000, 20067.9370],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21133.5080],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20988.8485],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20596.7429],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 19910.7730],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20776.7070],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20051.7969],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20725.3884],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20828.8795],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21647.1811],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21310.1687],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 20852.0993],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21912.3952],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21937.8282],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 1877.3934, 0.0000, 0.0000, 0.0000, 21962.4576],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 2008.8110, 0.0000, 21389.4018],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 2008.8110, 0.0000, 21625.6913],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 2008.8110, 0.0000, 20873.0389],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 2008.8110, 0.0000, 21450.9447],
                 [1073.8232, 416.6787, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 2008.8110, 0.0000, 22269.3892],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 21969.5329],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 21752.6924],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 22000.6088],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 23072.5655],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 23487.5201],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 22441.0460],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 23201.2700],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 23400.9485],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 22306.2008],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 0.0000, 938.6967, 0.0000, 0.0000, 0.0000, 21989.5913],
                 [1073.8232, 737.0632, 735.6442, 269.8496, 1708.7766, 938.6967, 0.0000, 5215.4255, 0.0000, 31897.1636],
                 [0.0000, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 6421.4626, 0.0000, 31509.5059],
                 [0.0000, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 6421.4626, 0.0000, 31451.7888],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 32773.4592],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 32287.0318],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 32698.1938],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 34031.5183],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 35537.8336],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 36212.6487],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 36007.5294],
                 [978.8815, 737.0632, 735.6442, 578.0898, 1708.7766, 2145.9711, 0.0000, 0.0000, 0.0000, 34691.3797],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 33904.8810],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 34341.6098],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 35479.9505],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 34418.4455],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 34726.7182],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 34935.0407],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 34136.7505],
                 [978.8815, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 9162.7865, 0.0000, 33804.1575],
                 [195.7763, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 14025.8697, 0.0000, 33653.8970],
                 [195.7763, 737.0632, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 14025.8697, 0.0000, 34689.8757],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 10562.2913, 0.0000, 34635.7841],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 10562.2913, 0.0000, 35253.2755],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 10562.2913, 0.0000, 36388.1051],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 10562.2913, 0.0000, 37987.4204],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 10562.2913, 0.0000, 38762.2103],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 1708.7766, 0.0000, 0.0000, 10562.2913, 0.0000, 38574.0544],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 15879.4935, 0.0000, 39101.9156],
                 [195.7763, 1124.9219, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 15879.4935, 0.0000, 39132.5587],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 38873.2941],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 39336.6594],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 39565.9568],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 39583.4317],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 39206.8350],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 39092.6551],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 39666.1834],
                 [195.7763, 0.0000, 735.6442, 0.0000, 0.0000, 0.0000, 1362.4361, 27747.4200, 0.0000, 38798.0749],
                 [0.0000, 0.0000, 1576.8381, 0.0000, 0.0000, 0.0000, 1362.4361, 23205.2077, 0.0000, 39143.5561],
                 [0.0000, 0.0000, 1576.8381, 0.0000, 0.0000, 0.0000, 1362.4361, 23205.2077, 0.0000, 38617.8779],
                 [0.0000, 0.0000, 1576.8381, 0.0000, 0.0000, 0.0000, 1362.4361, 23205.2077, 0.0000, 38156.1701]])
        # PS信号，先卖后买，交割期为2天（股票）1天（现金）
        self.ps_res_sb20 = np.array(
                [[0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 10000.000],
                 [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 9916.667],
                 [0.000, 0.000, 0.000, 0.000, 555.556, 205.065, 321.089, 5059.722, 0.000, 9761.111],
                 [346.982, 416.679, 0.000, 0.000, 555.556, 205.065, 321.089, 1201.278, 0.000, 9646.112],
                 [346.982, 416.679, 191.037, 0.000, 555.556, 205.065, 321.089, 232.719, 0.000, 9685.586],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 9813.218],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 9803.129],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 9608.020],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 9311.573],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 8883.625],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 8751.390],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 8794.181],
                 [346.982, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 1891.052, 0.000, 9136.570],
                 [231.437, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 2472.244, 0.000, 9209.359],
                 [231.437, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 2472.244, 0.000, 9093.829],
                 [231.437, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 2472.244, 0.000, 9387.554],
                 [231.437, 416.679, 191.037, 0.000, 138.889, 205.065, 321.089, 2472.244, 0.000, 9585.959],
                 [231.437, 416.679, 95.519, 0.000, 138.889, 205.065, 321.089, 3035.804, 0.000, 9928.777],
                 [231.437, 416.679, 95.519, 0.000, 138.889, 205.065, 321.089, 3035.804, 0.000, 10060.381],
                 [231.437, 416.679, 95.519, 0.000, 138.889, 205.065, 321.089, 3035.804, 0.000, 10281.002],
                 [231.437, 416.679, 95.519, 0.000, 138.889, 205.065, 321.089, 3035.804, 0.000, 10095.561],
                 [231.437, 416.679, 95.519, 0.000, 138.889, 205.065, 0.000, 4506.393, 0.000, 10029.957],
                 [231.437, 416.679, 95.519, 0.000, 474.224, 205.065, 0.000, 2531.270, 0.000, 9875.613],
                 [231.437, 416.679, 95.519, 0.000, 474.224, 205.065, 0.000, 2531.270, 0.000, 9614.946],
                 [231.437, 416.679, 95.519, 0.000, 474.224, 205.065, 0.000, 2531.270, 0.000, 9824.172],
                 [115.719, 416.679, 95.519, 269.850, 474.224, 205.065, 0.000, 1854.799, 0.000, 9732.574],
                 [115.719, 416.679, 95.519, 269.850, 474.224, 205.065, 0.000, 1854.799, 0.000, 9968.339],
                 [115.719, 416.679, 95.519, 269.850, 474.224, 205.065, 0.000, 1854.799, 0.000, 10056.158],
                 [115.719, 416.679, 95.519, 269.850, 474.224, 205.065, 0.000, 1854.799, 0.000, 9921.492],
                 [115.719, 416.679, 95.519, 269.850, 474.224, 205.065, 0.000, 1854.799, 0.000, 9894.162],
                 [115.719, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 6179.774, 0.000, 20067.937],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 21133.508],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20988.848],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20596.743],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 19910.773],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20776.707],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20051.797],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20725.388],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20828.880],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 21647.181],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 21310.169],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 20852.099],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 21912.395],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 21937.828],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 1877.393, 0.000, 0.000, 0.000, 21962.458],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 21389.402],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 22027.453],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 20939.999],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 21250.064],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 22282.781],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 21407.066],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 21160.237],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 21826.768],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 22744.940],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 23466.118],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 22017.882],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 23191.466],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 23099.082],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 22684.767],
                 [1073.823, 416.679, 735.644, 269.850, 0.000, 938.697, 1339.207, 0.000, 0.000, 22842.135],
                 [1073.823, 416.679, 735.644, 269.850, 1785.205, 938.697, 1339.207, 5001.425, 0.000, 33323.836],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 32820.290],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 32891.231],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 34776.530],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 33909.032],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 34560.191],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 36080.455],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 38618.445],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 38497.923],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 37110.099],
                 [0.000, 416.679, 735.644, 944.961, 1785.205, 3582.884, 1339.207, 0.000, 0.000, 35455.247],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 35646.186],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 35472.302],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 36636.469],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 35191.704],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 36344.224],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 36221.601],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 35943.571],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 35708.261],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 35589.029],
                 [0.000, 416.679, 735.644, 0.000, 1785.205, 0.000, 1339.207, 15126.279, 0.000, 36661.029],
                 [0.000, 823.292, 735.644, 0.000, 1785.205, 0.000, 1339.207, 11495.220, 0.000, 36310.591],
                 [0.000, 823.292, 735.644, 0.000, 1785.205, 0.000, 1339.207, 11495.220, 0.000, 36466.764],
                 [0.000, 823.292, 735.644, 0.000, 1785.205, 0.000, 1339.207, 11495.220, 0.000, 37784.492],
                 [0.000, 823.292, 735.644, 0.000, 1785.205, 0.000, 1339.207, 11495.220, 0.000, 39587.677],
                 [0.000, 823.292, 735.644, 0.000, 1785.205, 0.000, 1339.207, 11495.220, 0.000, 40064.019],
                 [0.000, 823.292, 735.644, 0.000, 1785.205, 0.000, 1339.207, 11495.220, 0.000, 39521.644],
                 [0.000, 823.292, 735.644, 0.000, 0.000, 0.000, 2730.576, 17142.102, 0.000, 39932.276],
                 [0.000, 823.292, 735.644, 0.000, 0.000, 0.000, 2730.576, 17142.102, 0.000, 39565.248],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 38943.163],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 39504.118],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 40317.800],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 40798.577],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 39962.571],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 40194.479],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 41260.400],
                 [0.000, 0.000, 735.644, 0.000, 0.000, 0.000, 2730.576, 25827.835, 0.000, 39966.302],
                 [0.000, 0.000, 1613.452, 0.000, 0.000, 0.000, 2730.576, 19700.738, 0.000, 40847.316],
                 [0.000, 0.000, 1613.452, 0.000, 0.000, 0.000, 2730.576, 19700.738, 0.000, 39654.544],
                 [0.000, 0.000, 1613.452, 0.000, 0.000, 0.000, 2730.576, 19700.738, 0.000, 38914.815]])
        # PS信号，先买后卖，交割期为2天（股票）1天（现金）
        self.ps_res_bs21 = np.array(
                [[0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 10000.000],
                 [0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 9916.667],
                 [0.000, 0.000, 0.000, 0.000, 555.556, 208.333, 326.206, 5020.833, 0.000, 9761.111],
                 [351.119, 421.646, 0.000, 0.000, 555.556, 208.333, 326.206, 1116.389, 0.000, 9645.961],
                 [351.119, 421.646, 190.256, 0.000, 555.556, 208.333, 326.206, 151.793, 0.000, 9686.841],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 9813.932],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 9803.000],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 9605.334],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 9304.001],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 8870.741],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 8738.282],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 8780.664],
                 [351.119, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 1810.126, 0.000, 9126.199],
                 [234.196, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 2398.247, 0.000, 9199.746],
                 [234.196, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 2398.247, 0.000, 9083.518],
                 [234.196, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 2398.247, 0.000, 9380.932],
                 [234.196, 421.646, 190.256, 0.000, 138.889, 208.333, 326.206, 2398.247, 0.000, 9581.266],
                 [234.196, 421.646, 95.128, 0.000, 138.889, 208.333, 326.206, 2959.501, 0.000, 9927.154],
                 [234.196, 421.646, 95.128, 0.000, 138.889, 208.333, 326.206, 2959.501, 0.000, 10059.283],
                 [234.196, 421.646, 95.128, 0.000, 138.889, 208.333, 326.206, 2959.501, 0.000, 10281.669],
                 [234.196, 421.646, 95.128, 0.000, 138.889, 208.333, 326.206, 2959.501, 0.000, 10093.263],
                 [234.196, 421.646, 95.128, 0.000, 138.889, 208.333, 0.000, 4453.525, 0.000, 10026.289],
                 [234.196, 421.646, 95.128, 0.000, 479.340, 208.333, 0.000, 2448.268, 0.000, 9870.523],
                 [234.196, 421.646, 95.128, 0.000, 479.340, 208.333, 0.000, 2448.268, 0.000, 9606.437],
                 [234.196, 421.646, 95.128, 0.000, 479.340, 208.333, 0.000, 2448.268, 0.000, 9818.691],
                 [117.098, 421.646, 95.128, 272.237, 479.340, 208.333, 0.000, 1768.219, 0.000, 9726.556],
                 [117.098, 421.646, 95.128, 272.237, 479.340, 208.333, 0.000, 1768.219, 0.000, 9964.547],
                 [117.098, 421.646, 95.128, 272.237, 479.340, 208.333, 0.000, 1768.219, 0.000, 10053.449],
                 [117.098, 421.646, 95.128, 272.237, 479.340, 208.333, 0.000, 1768.219, 0.000, 9917.440],
                 [117.098, 421.646, 95.128, 272.237, 479.340, 208.333, 0.000, 1768.219, 0.000, 9889.495],
                 [117.098, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 6189.948, 0.000, 20064.523],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 21124.484],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 20827.077],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 20396.124],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 19856.445],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 20714.156],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 19971.485],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 20733.948],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 20938.903],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 21660.772],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 21265.298],
                 [708.171, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 2377.527, 0.000, 20684.378],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 0.000, 0.000, 21754.770],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 0.000, 0.000, 21775.215],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 1865.791, 0.000, 0.000, 0.000, 21801.488],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 932.896, 0.000, 1996.397, 0.000, 21235.427],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 932.896, 0.000, 1996.397, 0.000, 21466.714],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 932.896, 0.000, 1996.397, 0.000, 20717.431],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 932.896, 0.000, 1996.397, 0.000, 21294.450],
                 [1055.763, 421.646, 729.561, 272.237, 0.000, 932.896, 0.000, 1996.397, 0.000, 22100.247],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 21802.552],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 21593.608],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 21840.028],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 22907.725],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 23325.945],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 22291.942],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 23053.050],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 23260.084],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 22176.244],
                 [1055.763, 740.051, 729.561, 272.237, 0.000, 932.896, 0.000, 0.000, 0.000, 21859.297],
                 [1055.763, 740.051, 729.561, 272.237, 1706.748, 932.896, 0.000, 5221.105, 0.000, 31769.617],
                 [0.000, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 6313.462, 0.000, 31389.961],
                 [0.000, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 6313.462, 0.000, 31327.498],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 32647.140],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 32170.095],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 32577.742],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 33905.444],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 35414.492],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 36082.120],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 35872.293],
                 [962.418, 740.051, 729.561, 580.813, 1706.748, 2141.485, 0.000, 0.000, 0.000, 34558.132],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 33778.138],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 34213.578],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 35345.791],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 34288.014],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 34604.406],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 34806.850],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 34012.232],
                 [962.418, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 9177.053, 0.000, 33681.345],
                 [192.484, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 13958.345, 0.000, 33540.463],
                 [192.484, 740.051, 729.561, 0.000, 1706.748, 0.000, 0.000, 13958.345, 0.000, 34574.280],
                 [192.484, 1127.221, 729.561, 0.000, 1706.748, 0.000, 0.000, 10500.917, 0.000, 34516.781],
                 [192.484, 1127.221, 729.561, 0.000, 1706.748, 0.000, 0.000, 10500.917, 0.000, 35134.412],
                 [192.484, 1127.221, 729.561, 0.000, 1706.748, 0.000, 0.000, 10500.917, 0.000, 36266.530],
                 [192.484, 1127.221, 729.561, 0.000, 1706.748, 0.000, 0.000, 10500.917, 0.000, 37864.376],
                 [192.484, 1127.221, 729.561, 0.000, 1706.748, 0.000, 0.000, 10500.917, 0.000, 38642.633],
                 [192.484, 1127.221, 729.561, 0.000, 1706.748, 0.000, 0.000, 10500.917, 0.000, 38454.227],
                 [192.484, 1127.221, 729.561, 0.000, 0.000, 0.000, 1339.869, 15871.934, 0.000, 38982.227],
                 [192.484, 1127.221, 729.561, 0.000, 0.000, 0.000, 1339.869, 15871.934, 0.000, 39016.154],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 38759.803],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 39217.182],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 39439.690],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 39454.081],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 39083.341],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 38968.694],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 39532.030],
                 [192.484, 0.000, 729.561, 0.000, 0.000, 0.000, 1339.869, 27764.114, 0.000, 38675.507],
                 [0.000, 0.000, 1560.697, 0.000, 0.000, 0.000, 1339.869, 23269.751, 0.000, 39013.741],
                 [0.000, 0.000, 1560.697, 0.000, 0.000, 0.000, 1339.869, 23269.751, 0.000, 38497.668],
                 [0.000, 0.000, 1560.697, 0.000, 0.000, 0.000, 1339.869, 23269.751, 0.000, 38042.410]])
        # 模拟VS信号回测结果
        # VS信号，先卖后买，交割期为0
        self.vs_res_sb00 = np.array(
                [[0.0000, 0.0000, 0.0000, 0.0000, 500.0000, 0.0000, 0.0000, 7750.0000, 0.0000, 10000.0000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 500.0000, 0.0000, 0.0000, 7750.0000, 0.0000, 9925.0000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 500.0000, 300.0000, 300.0000, 4954.0000, 0.0000, 9785.0000],
                 [400.0000, 400.0000, 0.0000, 0.0000, 500.0000, 300.0000, 300.0000, 878.0000, 0.0000, 9666.0000],
                 [400.0000, 400.0000, 173.1755, 0.0000, 500.0000, 300.0000, 300.0000, 0.0000, 0.0000, 9731.0000],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 9830.9270],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 9785.8540],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 9614.3412],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 9303.1953],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 8834.4398],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 8712.7554],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 8717.9507],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592.0000, 0.0000, 9079.1479],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598.0000, 0.0000, 9166.0276],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598.0000, 0.0000, 9023.6607],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598.0000, 0.0000, 9291.6864],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598.0000, 0.0000, 9411.6371],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9706.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9822.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9986.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9805.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 0.0000, 4993.7357, 0.0000, 9704.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 600.0000, 300.0000, 0.0000, 2048.7357, 0.0000, 9567.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 600.0000, 300.0000, 0.0000, 2048.7357, 0.0000, 9209.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 600.0000, 300.0000, 0.0000, 2048.7357, 0.0000, 9407.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9329.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9545.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9652.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9414.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9367.7357],
                 [0.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 9319.7357, 0.0000, 19556.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 20094.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19849.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19802.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19487.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19749.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19392.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19671.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19756.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 20111.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19867.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19775.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 1990.7357, 0.0000, 20314.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 1990.7357, 0.0000, 20310.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 1990.7357, 0.0000, 20253.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20044.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20495.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 19798.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20103.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20864.7357],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 20425.7357],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 20137.8405],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 20711.3567],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 21470.3891],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 21902.9538],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 20962.9538],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 21833.5184],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 21941.8169],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 21278.5184],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0.0000, 0.0000, 21224.4700],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 600.0000, 500.0000, 600.0000, 9160.0000, 0.0000, 31225.2119],
                 [600.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 7488.0000, 0.0000, 30894.5748],
                 [600.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 7488.0000, 0.0000, 30764.3811],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 31815.5828],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 31615.4215],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 32486.1394],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 33591.2847],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 34056.5428],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 34756.4863],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 34445.5428],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208.0000, 0.0000, 34433.9541],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  33870.4703],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  34014.3010],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  34680.5671],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  33890.9945],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  34004.6640],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  34127.7768],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  33421.1638],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346.0000, 0.0000,
                  33120.9057],
                 [700.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 13830.0000, 0.0000, 32613.3171],
                 [700.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 13830.0000, 0.0000, 33168.1558],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151.0000, 0.0000,
                  33504.6236],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151.0000, 0.0000,
                  33652.1318],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151.0000, 0.0000,
                  34680.4867],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151.0000, 0.0000,
                  35557.5191],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151.0000, 0.0000,
                  35669.7128],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151.0000, 0.0000,
                  35211.4466],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13530.0000, 0.0000, 35550.6079],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13530.0000, 0.0000, 35711.6563],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 35682.6079],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 35880.8336],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 36249.8740],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 36071.6159],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 35846.1562],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 35773.3578],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 36274.9465],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695.0000, 0.0000, 35739.3094],
                 [500.0000, 710.4842, 1100.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13167.0000, 0.0000, 36135.0917],
                 [500.0000, 710.4842, 1100.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13167.0000, 0.0000, 35286.5835],
                 [500.0000, 710.4842, 1100.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13167.0000, 0.0000, 35081.3658]])
        # VS信号，先买后卖，交割期为0
        self.vs_res_bs00 = np.array(
                [[0.0000, 0.0000, 0.0000, 0.0000, 500.0000, 0.0000, 0.0000, 7750, 0.0000, 10000],
                 [0.0000, 0.0000, 0.0000, 0.0000, 500.0000, 0.0000, 0.0000, 7750, 0.0000, 9925],
                 [0.0000, 0.0000, 0.0000, 0.0000, 500.0000, 300.0000, 300.0000, 4954, 0.0000, 9785],
                 [400.0000, 400.0000, 0.0000, 0.0000, 500.0000, 300.0000, 300.0000, 878, 0.0000, 9666],
                 [400.0000, 400.0000, 173.1755, 0.0000, 500.0000, 300.0000, 300.0000, 0, 0.0000, 9731],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 9830.927022],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 9785.854043],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 9614.341223],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 9303.195266],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 8834.439842],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 8712.755424],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 8717.95069],
                 [400.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 1592, 0.0000, 9079.147929],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598, 0.0000, 9166.027613],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598, 0.0000, 9023.66075],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598, 0.0000, 9291.686391],
                 [200.0000, 400.0000, 173.1755, 0.0000, 100.0000, 300.0000, 300.0000, 2598, 0.0000, 9411.637081],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9706.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9822.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9986.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 300.0000, 3619.7357, 0.0000, 9805.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 100.0000, 300.0000, 0.0000, 4993.7357, 0.0000, 9704.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 600.0000, 300.0000, 0.0000, 2048.7357, 0.0000, 9567.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 600.0000, 300.0000, 0.0000, 2048.7357, 0.0000, 9209.7357],
                 [200.0000, 400.0000, 0.0000, 0.0000, 600.0000, 300.0000, 0.0000, 2048.7357, 0.0000, 9407.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9329.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9545.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9652.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9414.7357],
                 [0.0000, 400.0000, 0.0000, 300.0000, 600.0000, 300.0000, 0.0000, 1779.7357, 0.0000, 9367.7357],
                 [0.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 9319.7357, 0.0000, 19556.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 20094.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19849.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19802.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19487.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19749.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19392.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19671.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19756.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 20111.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19867.7357],
                 [500.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 6094.7357, 0.0000, 19775.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 1990.7357, 0.0000, 20314.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 1990.7357, 0.0000, 20310.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 900.0000, 0.0000, 1990.7357, 0.0000, 20253.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20044.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20495.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 19798.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20103.7357],
                 [1100.0000, 400.0000, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 1946.7357, 0.0000, 20864.7357],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 20425.7357],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 20137.84054],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 20711.35674],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 21470.38914],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 21902.95375],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 20962.95375],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 21833.51837],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 21941.81688],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 21278.51837],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 300.0000, 500.0000, 600.0000, 0, 0.0000, 21224.46995],
                 [1100.0000, 710.4842, 400.0000, 300.0000, 600.0000, 500.0000, 600.0000, 9160, 0.0000, 31225.21185],
                 [600.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 7488, 0.0000, 30894.57479],
                 [600.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 7488, 0.0000, 30764.38113],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 31815.5828],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 31615.42154],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 32486.13941],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 33591.28466],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 34056.54276],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 34756.48633],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 34445.54276],
                 [1100.0000, 710.4842, 400.0000, 800.0000, 600.0000, 700.0000, 600.0000, 4208, 0.0000, 34433.95412],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 33870.47032],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 34014.30104],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 34680.56715],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 33890.99452],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 34004.66398],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 34127.77683],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 33421.1638],
                 [1100.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11346, 0.0000, 33120.9057],
                 [700.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 13830, 0.0000, 32613.31706],
                 [700.0000, 710.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 13830, 0.0000, 33168.15579],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151, 0.0000, 33504.62357],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151, 0.0000, 33652.13176],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151, 0.0000, 34680.4867],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151, 0.0000, 35557.51909],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151, 0.0000, 35669.71276],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 600.0000, 100.0000, 600.0000, 11151, 0.0000, 35211.44665],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13530, 0.0000, 35550.60792],
                 [700.0000, 1010.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13530, 0.0000, 35711.65633],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 35682.60792],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 35880.83362],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 36249.87403],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 36071.61593],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 35846.15615],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 35773.35783],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 36274.94647],
                 [700.0000, 710.4842, 400.0000, 100.0000, 0.0000, 100.0000, 900.0000, 16695, 0.0000, 35739.30941],
                 [500.0000, 710.4842, 1100.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13167, 0.0000, 36135.09172],
                 [500.0000, 710.4842, 1100.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13167, 0.0000, 35286.58353],
                 [500.0000, 710.4842, 1100.0000, 100.0000, 0.0000, 100.0000, 900.0000, 13167, 0.0000, 35081.36584]])
        # VS信号，先卖后买，交割期为2天（股票）1天（现金）
        self.vs_res_sb20 = np.array(
                [[0.000, 0.000, 0.000, 0.000, 500.000, 0.000, 0.000, 7750.000, 0.000, 10000.000],
                 [0.000, 0.000, 0.000, 0.000, 500.000, 0.000, 0.000, 7750.000, 0.000, 9925.000],
                 [0.000, 0.000, 0.000, 0.000, 500.000, 300.000, 300.000, 4954.000, 0.000, 9785.000],
                 [400.000, 400.000, 0.000, 0.000, 500.000, 300.000, 300.000, 878.000, 0.000, 9666.000],
                 [400.000, 400.000, 173.176, 0.000, 500.000, 300.000, 300.000, 0.000, 0.000, 9731.000],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9830.927],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9785.854],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9614.341],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9303.195],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 8834.440],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 8712.755],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 8717.951],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9079.148],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9166.028],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9023.661],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9291.686],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9411.637],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9706.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9822.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9986.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9805.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 0.000, 4993.736, 0.000, 9704.736],
                 [200.000, 400.000, 0.000, 0.000, 600.000, 300.000, 0.000, 2048.736, 0.000, 9567.736],
                 [200.000, 400.000, 0.000, 0.000, 600.000, 300.000, 0.000, 2048.736, 0.000, 9209.736],
                 [200.000, 400.000, 0.000, 0.000, 600.000, 300.000, 0.000, 2048.736, 0.000, 9407.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9329.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9545.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9652.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9414.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9367.736],
                 [0.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 9319.736, 0.000, 19556.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 20094.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19849.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19802.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19487.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19749.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19392.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19671.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19756.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 20111.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19867.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19775.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 1990.736, 0.000, 20314.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 1990.736, 0.000, 20310.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 1990.736, 0.000, 20253.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20044.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20495.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 19798.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20103.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20864.736],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20425.736],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20137.841],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20711.357],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21470.389],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21902.954],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20962.954],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21833.518],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21941.817],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21278.518],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21224.470],
                 [1100.000, 710.484, 400.000, 300.000, 600.000, 500.000, 600.000, 9160.000, 0.000, 31225.212],
                 [600.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 7488.000, 0.000, 30894.575],
                 [600.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 7488.000, 0.000, 30764.381],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 31815.583],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 31615.422],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 32486.139],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 33591.285],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34056.543],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34756.486],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34445.543],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34433.954],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33870.470],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34014.301],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34680.567],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33890.995],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34004.664],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34127.777],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33421.164],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33120.906],
                 [700.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 13830.000, 0.000, 32613.317],
                 [700.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 13830.000, 0.000, 33168.156],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 33504.624],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 33652.132],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 34680.487],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 35557.519],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 35669.713],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 35211.447],
                 [700.000, 1010.484, 400.000, 100.000, 0.000, 100.000, 900.000, 13530.000, 0.000, 35550.608],
                 [700.000, 1010.484, 400.000, 100.000, 0.000, 100.000, 900.000, 13530.000, 0.000, 35711.656],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35682.608],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35880.834],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 36249.874],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 36071.616],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35846.156],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35773.358],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 36274.946],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35739.309],
                 [500.000, 710.484, 1100.000, 100.000, 0.000, 100.000, 900.000, 13167.000, 0.000, 36135.092],
                 [500.000, 710.484, 1100.000, 100.000, 0.000, 100.000, 900.000, 13167.000, 0.000, 35286.584],
                 [500.000, 710.484, 1100.000, 100.000, 0.000, 100.000, 900.000, 13167.000, 0.000, 35081.366]])
        # VS信号，先买后卖，交割期为2天（股票）1天（现金）
        self.vs_res_bs21 = np.array(
                [[0.000, 0.000, 0.000, 0.000, 500.000, 0.000, 0.000, 7750.000, 0.000, 10000.000],
                 [0.000, 0.000, 0.000, 0.000, 500.000, 0.000, 0.000, 7750.000, 0.000, 9925.000],
                 [0.000, 0.000, 0.000, 0.000, 500.000, 300.000, 300.000, 4954.000, 0.000, 9785.000],
                 [400.000, 400.000, 0.000, 0.000, 500.000, 300.000, 300.000, 878.000, 0.000, 9666.000],
                 [400.000, 400.000, 173.176, 0.000, 500.000, 300.000, 300.000, 0.000, 0.000, 9731.000],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9830.927],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9785.854],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9614.341],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9303.195],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 8834.440],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 8712.755],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 8717.951],
                 [400.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 1592.000, 0.000, 9079.148],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9166.028],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9023.661],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9291.686],
                 [200.000, 400.000, 173.176, 0.000, 100.000, 300.000, 300.000, 2598.000, 0.000, 9411.637],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9706.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9822.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9986.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 300.000, 3619.736, 0.000, 9805.736],
                 [200.000, 400.000, 0.000, 0.000, 100.000, 300.000, 0.000, 4993.736, 0.000, 9704.736],
                 [200.000, 400.000, 0.000, 0.000, 600.000, 300.000, 0.000, 2048.736, 0.000, 9567.736],
                 [200.000, 400.000, 0.000, 0.000, 600.000, 300.000, 0.000, 2048.736, 0.000, 9209.736],
                 [200.000, 400.000, 0.000, 0.000, 600.000, 300.000, 0.000, 2048.736, 0.000, 9407.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9329.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9545.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9652.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9414.736],
                 [0.000, 400.000, 0.000, 300.000, 600.000, 300.000, 0.000, 1779.736, 0.000, 9367.736],
                 [0.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 9319.736, 0.000, 19556.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 20094.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19849.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19802.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19487.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19749.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19392.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19671.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19756.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 20111.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19867.736],
                 [500.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 6094.736, 0.000, 19775.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 1990.736, 0.000, 20314.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 1990.736, 0.000, 20310.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 900.000, 0.000, 1990.736, 0.000, 20253.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20044.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20495.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 19798.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20103.736],
                 [1100.000, 400.000, 400.000, 300.000, 300.000, 500.000, 600.000, 1946.736, 0.000, 20864.736],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20425.736],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20137.841],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20711.357],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21470.389],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21902.954],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 20962.954],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21833.518],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21941.817],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21278.518],
                 [1100.000, 710.484, 400.000, 300.000, 300.000, 500.000, 600.000, 0.000, 0.000, 21224.470],
                 [1100.000, 710.484, 400.000, 300.000, 600.000, 500.000, 600.000, 9160.000, 0.000, 31225.212],
                 [600.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 7488.000, 0.000, 30894.575],
                 [600.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 7488.000, 0.000, 30764.381],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 31815.583],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 31615.422],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 32486.139],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 33591.285],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34056.543],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34756.486],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34445.543],
                 [1100.000, 710.484, 400.000, 800.000, 600.000, 700.000, 600.000, 4208.000, 0.000, 34433.954],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33870.470],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34014.301],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34680.567],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33890.995],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34004.664],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 34127.777],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33421.164],
                 [1100.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11346.000, 0.000, 33120.906],
                 [700.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 13830.000, 0.000, 32613.317],
                 [700.000, 710.484, 400.000, 100.000, 600.000, 100.000, 600.000, 13830.000, 0.000, 33168.156],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 33504.624],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 33652.132],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 34680.487],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 35557.519],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 35669.713],
                 [700.000, 1010.484, 400.000, 100.000, 600.000, 100.000, 600.000, 11151.000, 0.000, 35211.447],
                 [700.000, 1010.484, 400.000, 100.000, 0.000, 100.000, 900.000, 13530.000, 0.000, 35550.608],
                 [700.000, 1010.484, 400.000, 100.000, 0.000, 100.000, 900.000, 13530.000, 0.000, 35711.656],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35682.608],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35880.834],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 36249.874],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 36071.616],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35846.156],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35773.358],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 36274.946],
                 [700.000, 710.484, 400.000, 100.000, 0.000, 100.000, 900.000, 16695.000, 0.000, 35739.309],
                 [500.000, 710.484, 1100.000, 100.000, 0.000, 100.000, 900.000, 13167.000, 0.000, 36135.092],
                 [500.000, 710.484, 1100.000, 100.000, 0.000, 100.000, 900.000, 13167.000, 0.000, 35286.584],
                 [500.000, 710.484, 1100.000, 100.000, 0.000, 100.000, 900.000, 13167.000, 0.000, 35081.366]])

        # Multi信号处理结果，先卖后买，使用卖出的现金买进，交割期为2天（股票）0天（现金）
        self.multi_res = np.array(
                [[0.0000, 357.2545, 0.0000, 6506.9627, 0.0000, 9965.1867],
                 [0.0000, 357.2545, 0.0000, 6506.9627, 0.0000, 10033.0650],
                 [0.0000, 178.6273, 0.0000, 8273.5864, 0.0000, 10034.8513],
                 [0.0000, 178.6273, 0.0000, 8273.5864, 0.0000, 10036.6376],
                 [150.3516, 178.6273, 0.0000, 6771.5740, 0.0000, 10019.3404],
                 [150.3516, 178.6273, 0.0000, 6771.5740, 0.0000, 10027.7062],
                 [150.3516, 178.6273, 0.0000, 6771.5740, 0.0000, 10030.1477],
                 [150.3516, 178.6273, 0.0000, 6771.5740, 0.0000, 10005.1399],
                 [150.3516, 178.6273, 0.0000, 6771.5740, 0.0000, 10002.5054],
                 [150.3516, 489.4532, 0.0000, 3765.8877, 0.0000, 9967.3860],
                 [75.1758, 391.5625, 0.0000, 5490.1377, 0.0000, 10044.4059],
                 [75.1758, 391.5625, 0.0000, 5490.1377, 0.0000, 10078.1430],
                 [75.1758, 391.5625, 846.3525, 392.3025, 0.0000, 10138.2709],
                 [75.1758, 391.5625, 846.3525, 392.3025, 0.0000, 10050.4768],
                 [75.1758, 391.5625, 846.3525, 392.3025, 0.0000, 10300.0711],
                 [75.1758, 391.5625, 846.3525, 392.3025, 0.0000, 10392.6970],
                 [75.1758, 391.5625, 169.2705, 4644.3773, 0.0000, 10400.5282],
                 [75.1758, 391.5625, 169.2705, 4644.3773, 0.0000, 10408.9220],
                 [75.1758, 0.0000, 169.2705, 8653.9776, 0.0000, 10376.5914],
                 [75.1758, 0.0000, 169.2705, 8653.9776, 0.0000, 10346.8794],
                 [75.1758, 0.0000, 169.2705, 8653.9776, 0.0000, 10364.7474],
                 [75.1758, 381.1856, 645.5014, 2459.1665, 0.0000, 10302.4570],
                 [18.7939, 381.1856, 645.5014, 3024.6764, 0.0000, 10747.4929],
                 [18.7939, 381.1856, 96.8252, 6492.3097, 0.0000, 11150.9107],
                 [18.7939, 381.1856, 96.8252, 6492.3097, 0.0000, 11125.2946],
                 [18.7939, 114.3557, 96.8252, 9227.3166, 0.0000, 11191.9956],
                 [18.7939, 114.3557, 96.8252, 9227.3166, 0.0000, 11145.7486],
                 [18.7939, 114.3557, 96.8252, 9227.3166, 0.0000, 11090.0768],
                 [132.5972, 114.3557, 864.3802, 4223.9548, 0.0000, 11113.8733],
                 [132.5972, 114.3557, 864.3802, 4223.9548, 0.0000, 11456.3281],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 21983.7333],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 22120.6165],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 21654.5327],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 21429.6550],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 21912.5643],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 22516.3100],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 23169.0777],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 23390.8080],
                 [132.5972, 114.3557, 864.3802, 14223.9548, 0.0000, 23743.3742],
                 [132.5972, 559.9112, 864.3802, 9367.3999, 0.0000, 23210.7311],
                 [132.5972, 559.9112, 864.3802, 9367.3999, 0.0000, 24290.4375],
                 [132.5972, 559.9112, 864.3802, 9367.3999, 0.0000, 24335.3279],
                 [132.5972, 559.9112, 864.3802, 9367.3999, 0.0000, 18317.3553],
                 [132.5972, 559.9112, 864.3802, 9367.3999, 0.0000, 18023.4660],
                 [259.4270, 559.9112, 0.0000, 15820.6915, 0.0000, 24390.0527],
                 [259.4270, 559.9112, 0.0000, 15820.6915, 0.0000, 24389.6421],
                 [259.4270, 559.9112, 0.0000, 15820.6915, 0.0000, 24483.5953],
                 [0.0000, 559.9112, 0.0000, 18321.5674, 0.0000, 24486.1895],
                 [0.0000, 0.0000, 0.0000, 24805.3389, 0.0000, 24805.3389],
                 [0.0000, 0.0000, 0.0000, 24805.3389, 0.0000, 24805.3389]])

    def test_loop_step_pt_sb00(self):
        """ test loop step PT-signal, sell first"""
        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=10000,
                                                     own_amounts=np.zeros(7, dtype='float'),
                                                     available_cash=10000,
                                                     available_amounts=np.zeros(7, dtype='float'),
                                                     op=self.pt_signals[0],
                                                     prices=self.prices[0],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash_change:     +{c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = 10000 + c_g + c_s
        amounts = np.zeros(7, dtype='float') + a_p + a_s
        self.assertAlmostEqual(cash, 7500)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 555.5555556, 0, 0])))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_sb00[2][7],
                                                     own_amounts=self.pt_res_sb00[2][0:7],
                                                     available_cash=self.pt_res_sb00[2][7],
                                                     available_amounts=self.pt_res_sb00[2][0:7],
                                                     op=self.pt_signals[3],
                                                     prices=self.prices[3],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_sb00[2][7] + c_g + c_s
        amounts = self.pt_res_sb00[2][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_sb00[3][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_sb00[3][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_sb00[30][7],
                                                     own_amounts=self.pt_res_sb00[30][0:7],
                                                     available_cash=self.pt_res_sb00[30][7],
                                                     available_amounts=self.pt_res_sb00[30][0:7],
                                                     op=self.pt_signals[31],
                                                     prices=self.prices[31],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_sb00[30][7] + c_g + c_s
        amounts = self.pt_res_sb00[30][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_sb00[31][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_sb00[31][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_sb00[59][7] + 10000,
                                                     own_amounts=self.pt_res_sb00[59][0:7],
                                                     available_cash=self.pt_res_sb00[59][7] + 10000,
                                                     available_amounts=self.pt_res_sb00[59][0:7],
                                                     op=self.pt_signals[60],
                                                     prices=self.prices[60],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_sb00[59][7] + c_g + c_s + 10000
        amounts = self.pt_res_sb00[59][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_sb00[60][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_sb00[60][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.pt_signals[61],
                                                     prices=self.prices[61],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_sb00[61][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_sb00[61][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_sb00[95][7],
                                                     own_amounts=self.pt_res_sb00[95][0:7],
                                                     available_cash=self.pt_res_sb00[95][7],
                                                     available_amounts=self.pt_res_sb00[95][0:7],
                                                     op=self.pt_signals[96],
                                                     prices=self.prices[96],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_sb00[96][7] + c_g + c_s
        amounts = self.pt_res_sb00[96][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_sb00[96][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_sb00[96][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.pt_signals[97],
                                                     prices=self.prices[97],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_sb00[97][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_sb00[97][0:7]))

    def test_loop_step_pt_bs00(self):
        """ test loop step PT-signal, buy first"""
        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=10000,
                                                     own_amounts=np.zeros(7, dtype='float'),
                                                     available_cash=10000,
                                                     available_amounts=np.zeros(7, dtype='float'),
                                                     op=self.pt_signals[0],
                                                     prices=self.prices[0],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash_change:     +{c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = 10000 + c_g + c_s
        amounts = np.zeros(7, dtype='float') + a_p + a_s
        self.assertAlmostEqual(cash, 7500)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 555.5555556, 0, 0])))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_bs00[2][7],
                                                     own_amounts=self.pt_res_bs00[2][0:7],
                                                     available_cash=self.pt_res_bs00[2][7],
                                                     available_amounts=self.pt_res_bs00[2][0:7],
                                                     op=self.pt_signals[3],
                                                     prices=self.prices[3],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_bs00[2][7] + c_g + c_s
        amounts = self.pt_res_bs00[2][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_bs00[3][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_bs00[3][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_bs00[30][7],
                                                     own_amounts=self.pt_res_bs00[30][0:7],
                                                     available_cash=self.pt_res_bs00[30][7],
                                                     available_amounts=self.pt_res_bs00[30][0:7],
                                                     op=self.pt_signals[31],
                                                     prices=self.prices[31],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_bs00[30][7] + c_g + c_s
        amounts = self.pt_res_bs00[30][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_bs00[31][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_bs00[31][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_bs00[59][7] + 10000,
                                                     own_amounts=self.pt_res_bs00[59][0:7],
                                                     available_cash=self.pt_res_bs00[59][7] + 10000,
                                                     available_amounts=self.pt_res_bs00[59][0:7],
                                                     op=self.pt_signals[60],
                                                     prices=self.prices[60],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_bs00[59][7] + c_g + c_s + 10000
        amounts = self.pt_res_bs00[59][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_bs00[60][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_bs00[60][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.pt_signals[61],
                                                     prices=self.prices[61],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_bs00[61][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_bs00[61][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=self.pt_res_bs00[95][7],
                                                     own_amounts=self.pt_res_bs00[95][0:7],
                                                     available_cash=self.pt_res_bs00[95][7],
                                                     available_amounts=self.pt_res_bs00[95][0:7],
                                                     op=self.pt_signals[96],
                                                     prices=self.prices[96],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.pt_res_bs00[96][7] + c_g + c_s
        amounts = self.pt_res_bs00[96][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_bs00[96][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_bs00[96][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=0,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.pt_signals[97],
                                                     prices=self.prices[97],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.pt_res_bs00[97][7], 2)
        self.assertTrue(np.allclose(amounts, self.pt_res_bs00[97][0:7]))

    def test_loop_step_ps_sb00(self):
        """ test loop step PS-signal, sell first"""
        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=10000,
                                                     own_amounts=np.zeros(7, dtype='float'),
                                                     available_cash=10000,
                                                     available_amounts=np.zeros(7, dtype='float'),
                                                     op=self.ps_signals[0],
                                                     prices=self.prices[0],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash_change:     +{c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = 10000 + c_g + c_s
        amounts = np.zeros(7, dtype='float') + a_p + a_s
        self.assertAlmostEqual(cash, 7500)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 555.5555556, 0, 0])))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_sb00[2][7],
                                                     own_amounts=self.ps_res_sb00[2][0:7],
                                                     available_cash=self.ps_res_sb00[2][7],
                                                     available_amounts=self.ps_res_sb00[2][0:7],
                                                     op=self.ps_signals[3],
                                                     prices=self.prices[3],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_sb00[2][7] + c_g + c_s
        amounts = self.ps_res_sb00[2][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_sb00[3][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_sb00[3][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_sb00[30][7],
                                                     own_amounts=self.ps_res_sb00[30][0:7],
                                                     available_cash=self.ps_res_sb00[30][7],
                                                     available_amounts=self.ps_res_sb00[30][0:7],
                                                     op=self.ps_signals[31],
                                                     prices=self.prices[31],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_sb00[30][7] + c_g + c_s
        amounts = self.ps_res_sb00[30][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_sb00[31][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_sb00[31][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_sb00[59][7] + 10000,
                                                     own_amounts=self.ps_res_sb00[59][0:7],
                                                     available_cash=self.ps_res_sb00[59][7] + 10000,
                                                     available_amounts=self.ps_res_sb00[59][0:7],
                                                     op=self.ps_signals[60],
                                                     prices=self.prices[60],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_sb00[59][7] + c_g + c_s + 10000
        amounts = self.ps_res_sb00[59][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_sb00[60][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_sb00[60][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.ps_signals[61],
                                                     prices=self.prices[61],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_sb00[61][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_sb00[61][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_sb00[95][7],
                                                     own_amounts=self.ps_res_sb00[95][0:7],
                                                     available_cash=self.ps_res_sb00[95][7],
                                                     available_amounts=self.ps_res_sb00[95][0:7],
                                                     op=self.ps_signals[96],
                                                     prices=self.prices[96],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_sb00[96][7] + c_g + c_s
        amounts = self.ps_res_sb00[96][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_sb00[96][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_sb00[96][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.ps_signals[97],
                                                     prices=self.prices[97],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_sb00[97][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_sb00[97][0:7]))

    def test_loop_step_ps_bs00(self):
        """ test loop step PS-signal, buy first"""
        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=10000,
                                                     own_amounts=np.zeros(7, dtype='float'),
                                                     available_cash=10000,
                                                     available_amounts=np.zeros(7, dtype='float'),
                                                     op=self.ps_signals[0],
                                                     prices=self.prices[0],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash_change:     +{c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = 10000 + c_g + c_s
        amounts = np.zeros(7, dtype='float') + a_p + a_s
        self.assertAlmostEqual(cash, 7500)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 555.5555556, 0, 0])))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_bs00[2][7],
                                                     own_amounts=self.ps_res_sb00[2][0:7],
                                                     available_cash=self.ps_res_bs00[2][7],
                                                     available_amounts=self.ps_res_bs00[2][0:7],
                                                     op=self.ps_signals[3],
                                                     prices=self.prices[3],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_bs00[2][7] + c_g + c_s
        amounts = self.ps_res_bs00[2][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_bs00[3][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_bs00[3][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_bs00[30][7],
                                                     own_amounts=self.ps_res_sb00[30][0:7],
                                                     available_cash=self.ps_res_bs00[30][7],
                                                     available_amounts=self.ps_res_bs00[30][0:7],
                                                     op=self.ps_signals[31],
                                                     prices=self.prices[31],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_bs00[30][7] + c_g + c_s
        amounts = self.ps_res_bs00[30][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_bs00[31][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_bs00[31][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_bs00[59][7] + 10000,
                                                     own_amounts=self.ps_res_bs00[59][0:7],
                                                     available_cash=self.ps_res_bs00[59][7] + 10000,
                                                     available_amounts=self.ps_res_bs00[59][0:7],
                                                     op=self.ps_signals[60],
                                                     prices=self.prices[60],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_bs00[59][7] + c_g + c_s + 10000
        amounts = self.ps_res_bs00[59][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_bs00[60][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_bs00[60][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.ps_signals[61],
                                                     prices=self.prices[61],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_bs00[61][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_bs00[61][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=self.ps_res_bs00[95][7],
                                                     own_amounts=self.ps_res_bs00[95][0:7],
                                                     available_cash=self.ps_res_bs00[95][7],
                                                     available_amounts=self.ps_res_bs00[95][0:7],
                                                     op=self.ps_signals[96],
                                                     prices=self.prices[96],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.ps_res_bs00[96][7] + c_g + c_s
        amounts = self.ps_res_bs00[96][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_bs00[96][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_bs00[96][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=1,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.ps_signals[97],
                                                     prices=self.prices[97],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.ps_res_bs00[97][7], 2)
        self.assertTrue(np.allclose(amounts, self.ps_res_bs00[97][0:7]))

    def test_loop_step_vs_sb00(self):
        """test loop step of Volume Signal type of signals"""
        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=10000,
                                                     own_amounts=np.zeros(7, dtype='float'),
                                                     available_cash=10000,
                                                     available_amounts=np.zeros(7, dtype='float'),
                                                     op=self.vs_signals[0],
                                                     prices=self.prices[0],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash_change:     +{c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = 10000 + c_g + c_s
        amounts = np.zeros(7, dtype='float') + a_p + a_s
        self.assertAlmostEqual(cash, 7750)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 500., 0, 0])))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_sb00[2][7],
                                                     own_amounts=self.vs_res_sb00[2][0:7],
                                                     available_cash=self.vs_res_sb00[2][7],
                                                     available_amounts=self.vs_res_sb00[2][0:7],
                                                     op=self.vs_signals[3],
                                                     prices=self.prices[3],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_sb00[2][7] + c_g + c_s
        amounts = self.vs_res_sb00[2][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_sb00[3][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_sb00[3][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_sb00[30][7],
                                                     own_amounts=self.vs_res_sb00[30][0:7],
                                                     available_cash=self.vs_res_sb00[30][7],
                                                     available_amounts=self.vs_res_sb00[30][0:7],
                                                     op=self.vs_signals[31],
                                                     prices=self.prices[31],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_sb00[30][7] + c_g + c_s
        amounts = self.vs_res_sb00[30][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_sb00[31][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_sb00[31][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_sb00[59][7] + 10000,
                                                     own_amounts=self.vs_res_sb00[59][0:7],
                                                     available_cash=self.vs_res_sb00[59][7] + 10000,
                                                     available_amounts=self.vs_res_sb00[59][0:7],
                                                     op=self.vs_signals[60],
                                                     prices=self.prices[60],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_sb00[59][7] + c_g + c_s + 10000
        amounts = self.vs_res_sb00[59][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_sb00[60][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_sb00[60][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.vs_signals[61],
                                                     prices=self.prices[61],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_sb00[61][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_sb00[61][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_sb00[95][7],
                                                     own_amounts=self.vs_res_sb00[95][0:7],
                                                     available_cash=self.vs_res_sb00[95][7],
                                                     available_amounts=self.vs_res_sb00[95][0:7],
                                                     op=self.vs_signals[96],
                                                     prices=self.prices[96],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_sb00[96][7] + c_g + c_s
        amounts = self.vs_res_sb00[96][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_sb00[96][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_sb00[96][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.vs_signals[97],
                                                     prices=self.prices[97],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=True,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_sb00[97][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_sb00[97][0:7]))

    def test_loop_step_vs_bs00(self):
        """test loop step of Volume Signal type of signals"""
        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=10000,
                                                     own_amounts=np.zeros(7, dtype='float'),
                                                     available_cash=10000,
                                                     available_amounts=np.zeros(7, dtype='float'),
                                                     op=self.vs_signals[0],
                                                     prices=self.prices[0],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash_change:     +{c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = 10000 + c_g + c_s
        amounts = np.zeros(7, dtype='float') + a_p + a_s
        self.assertAlmostEqual(cash, 7750)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 500., 0, 0])))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_bs00[2][7],
                                                     own_amounts=self.vs_res_bs00[2][0:7],
                                                     available_cash=self.vs_res_bs00[2][7],
                                                     available_amounts=self.vs_res_bs00[2][0:7],
                                                     op=self.vs_signals[3],
                                                     prices=self.prices[3],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_bs00[2][7] + c_g + c_s
        amounts = self.vs_res_bs00[2][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_bs00[3][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_bs00[3][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_bs00[30][7],
                                                     own_amounts=self.vs_res_bs00[30][0:7],
                                                     available_cash=self.vs_res_bs00[30][7],
                                                     available_amounts=self.vs_res_bs00[30][0:7],
                                                     op=self.vs_signals[31],
                                                     prices=self.prices[31],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_bs00[30][7] + c_g + c_s
        amounts = self.vs_res_bs00[30][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_bs00[31][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_bs00[31][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_bs00[59][7] + 10000,
                                                     own_amounts=self.vs_res_bs00[59][0:7],
                                                     available_cash=self.vs_res_bs00[59][7] + 10000,
                                                     available_amounts=self.vs_res_bs00[59][0:7],
                                                     op=self.vs_signals[60],
                                                     prices=self.prices[60],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_bs00[59][7] + c_g + c_s + 10000
        amounts = self.vs_res_bs00[59][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_bs00[60][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_bs00[60][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.vs_signals[61],
                                                     prices=self.prices[61],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_bs00[61][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_bs00[61][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=self.vs_res_bs00[95][7],
                                                     own_amounts=self.vs_res_bs00[95][0:7],
                                                     available_cash=self.vs_res_bs00[95][7],
                                                     available_amounts=self.vs_res_bs00[95][0:7],
                                                     op=self.vs_signals[96],
                                                     prices=self.prices[96],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = self.vs_res_bs00[96][7] + c_g + c_s
        amounts = self.vs_res_bs00[96][0:7] + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_bs00[96][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_bs00[96][0:7]))

        c_g, c_s, a_p, a_s, fee = qt.core._loop_step(signal_type=2,
                                                     own_cash=cash,
                                                     own_amounts=amounts,
                                                     available_cash=cash,
                                                     available_amounts=amounts,
                                                     op=self.vs_signals[97],
                                                     prices=self.prices[97],
                                                     rate=self.rate,
                                                     pt_buy_threshold=0.1,
                                                     pt_sell_threshold=0.1,
                                                     maximize_cash_usage=False,
                                                     allow_sell_short=False,
                                                     moq_buy=0,
                                                     moq_sell=0,
                                                     print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash_change:     + {c_g:.2f} / {c_s:.2f}\n'
              f'amount_changed:  \npurchased: {np.round(a_p, 2)}\nsold:{np.round(a_s, 2)}\n'
              f'----------------------------------\n')
        cash = cash + c_g + c_s
        amounts = amounts + a_p + a_s
        self.assertAlmostEqual(cash, self.vs_res_bs00[97][7], 2)
        self.assertTrue(np.allclose(amounts, self.vs_res_bs00[97][0:7]))

    def test_loop_pt(self):
        """ Test looping of PT proportion target signals, with
            stock delivery delay = 0 days
            cash delivery delay = 0 day
            buy-sell sequence = sell first
        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 0 days \n'
              'cash delivery delay = 0 day \n'
              'buy-sell sequence = sell first')
        res = apply_loop(op_type=0,
                         op_list=self.pt_signal_hp,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate,
                         moq_buy=0,
                         moq_sell=0,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        # print(f'in test_loop:\nresult of loop test is \n{res}')
        self.assertTrue(np.allclose(res, self.pt_res_bs00, 2))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(op_type=0,
                         op_list=self.ps_signal_hp,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate2,
                         moq_buy=100,
                         moq_sell=1,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        # print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_pt_with_delay(self):
        """ Test looping of PT proportion target signals, with:
            stock delivery delay = 2 days
            cash delivery delay = 1 day
            use_sell_cash = False

        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 2 days \n'
              'cash delivery delay = 1 day \n'
              'maximize_cash = False (buy and sell at the same time)')
        res = apply_loop(
                op_type=0,
                op_list=self.pt_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate,
                moq_buy=0,
                moq_sell=0,
                inflation_rate=0,
                cash_delivery_period=1,
                stock_delivery_period=2,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.pt_res_bs21[i]))
            print()
        self.assertTrue(np.allclose(res, self.pt_res_bs21, 3))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(
                op_type=1,
                op_list=self.ps_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate2,
                moq_buy=100,
                moq_sell=1,
                inflation_rate=0,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_pt_with_delay_use_cash(self):
        """ Test looping of PT proportion target signals, with:
            stock delivery delay = 2 days
            cash delivery delay = 0 day
            use sell cash = True    (sell stock first to use cash when possible
                                    (not possible when cash delivery period != 0))

        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 2 days \n'
              'cash delivery delay = 1 day \n'
              'maximize cash usage = True \n'
              'but not applicable because cash delivery period == 1')
        res = apply_loop(
                op_type=0,
                op_list=self.pt_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate,
                moq_buy=0,
                moq_sell=0,
                cash_delivery_period=0,
                stock_delivery_period=2,
                inflation_rate=0,
                max_cash_usage=True,
                print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.pt_res_sb20[i]))
            print()
        self.assertTrue(np.allclose(res, self.pt_res_sb20, 3))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(
                op_type=1,
                op_list=self.ps_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate2,
                moq_buy=100,
                moq_sell=1,
                cash_delivery_period=1,
                stock_delivery_period=2,
                inflation_rate=0,
                print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_ps(self):
        """ Test looping of PS Proportion Signal type of signals

        """
        res = apply_loop(op_type=1,
                         op_list=self.ps_signal_hp,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate,
                         moq_buy=0,
                         moq_sell=0,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')
        self.assertTrue(np.allclose(res, self.ps_res_bs00, 5))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(op_type=1,
                         op_list=self.ps_signal_hp,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate2,
                         moq_buy=100,
                         moq_sell=1,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_ps_with_delay(self):
        """ Test looping of PT proportion target signals, with:
            stock delivery delay = 2 days
            cash delivery delay = 1 day
            use_sell_cash = False

        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 2 days \n'
              'cash delivery delay = 1 day \n'
              'maximize_cash = False (buy and sell at the same time)')
        res = apply_loop(
                op_type=1,
                op_list=self.ps_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate,
                moq_buy=0,
                moq_sell=0,
                inflation_rate=0,
                cash_delivery_period=1,
                stock_delivery_period=2,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.ps_res_bs21[i]))
            print()
        self.assertTrue(np.allclose(res, self.ps_res_bs21, 3))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(
                op_type=1,
                op_list=self.ps_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate2,
                moq_buy=100,
                moq_sell=1,
                inflation_rate=0,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_ps_with_delay_use_cash(self):
        """ Test looping of PT proportion target signals, with:
            stock delivery delay = 2 days
            cash delivery delay = 0 day
            use sell cash = True    (sell stock first to use cash when possible
                                    (not possible when cash delivery period != 0))

        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 2 days \n'
              'cash delivery delay = 1 day \n'
              'maximize cash usage = True \n'
              'but not applicable because cash delivery period == 1')
        res = apply_loop(
                op_type=1,
                op_list=self.ps_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate,
                moq_buy=0,
                moq_sell=0,
                cash_delivery_period=0,
                stock_delivery_period=2,
                inflation_rate=0,
                max_cash_usage=True,
                print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.ps_res_sb20[i]))
            print()
        self.assertTrue(np.allclose(res, self.ps_res_sb20, 3))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(
                op_type=1,
                op_list=self.ps_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate2,
                moq_buy=100,
                moq_sell=1,
                cash_delivery_period=1,
                stock_delivery_period=2,
                inflation_rate=0,
                print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_vs(self):
        """ Test looping of VS Volume Signal type of signals

        """
        res = apply_loop(op_type=2,
                         op_list=self.vs_signal_hp,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate,
                         moq_buy=0,
                         moq_sell=0,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')
        self.assertTrue(np.allclose(res, self.vs_res_bs00, 5))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(op_type=2,
                         op_list=self.vs_signal_hp,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate2,
                         moq_buy=100,
                         moq_sell=1,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_vs_with_delay(self):
        """ Test looping of PT proportion target signals, with:
            stock delivery delay = 2 days
            cash delivery delay = 1 day
            use_sell_cash = False

        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 2 days \n'
              'cash delivery delay = 1 day \n'
              'maximize_cash = False (buy and sell at the same time)')
        res = apply_loop(
                op_type=2,
                op_list=self.vs_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate,
                moq_buy=0,
                moq_sell=0,
                inflation_rate=0,
                cash_delivery_period=1,
                stock_delivery_period=2,
                print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.vs_res_bs21[i]))
            print()
        self.assertTrue(np.allclose(res, self.vs_res_bs21, 3))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.vs_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.vs_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(
                op_type=1,
                op_list=self.vs_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate2,
                moq_buy=100,
                moq_sell=1,
                inflation_rate=0,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_vs_with_delay_use_cash(self):
        """ Test looping of PT proportion target signals, with:
            stock delivery delay = 2 days
            cash delivery delay = 0 day
            use sell cash = True    (sell stock first to use cash when possible
                                    (not possible when cash delivery period != 0))

        """
        print('Test looping of PT proportion target signals, with:\n'
              'stock delivery delay = 2 days \n'
              'cash delivery delay = 1 day \n'
              'maximize cash usage = True \n'
              'but not applicable because cash delivery period == 1')
        res = apply_loop(
                op_type=2,
                op_list=self.vs_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate,
                moq_buy=0,
                moq_sell=0,
                cash_delivery_period=0,
                stock_delivery_period=2,
                inflation_rate=0,
                max_cash_usage=True,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.vs_res_sb20[i]))
            print()
        self.assertTrue(np.allclose(res, self.vs_res_sb20, 3))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.vs_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.vs_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(
                op_type=1,
                op_list=self.vs_signal_hp,
                history_list=self.history_list,
                cash_plan=self.cash,
                cost_rate=self.rate2,
                moq_buy=100,
                moq_sell=1,
                cash_delivery_period=1,
                stock_delivery_period=2,
                inflation_rate=0,
                print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')

    def test_loop_multiple_signal(self):
        """ Test looping of PS Proportion Signal type of signals

        """
        res = apply_loop(op_type=1,
                         op_list=self.multi_signal_hp,
                         history_list=self.multi_history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate,
                         moq_buy=0,
                         moq_sell=0,
                         cash_delivery_period=0,
                         stock_delivery_period=2,
                         max_cash_usage=True,
                         inflation_rate=0,
                         print_log=False)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}\n'
              f'result comparison line by line:')
        for i in range(len(res)):
            print(np.around(res.values[i]))
            print(np.around(self.multi_res[i]))
            print()

        self.assertTrue(np.allclose(res, self.multi_res, 5))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          0,
                          self.ps_signal_hp,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(op_type=1,
                         op_list=self.multi_signal_hp,
                         history_list=self.multi_history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate2,
                         moq_buy=100,
                         moq_sell=1,
                         cash_delivery_period=0,
                         stock_delivery_period=2,
                         max_cash_usage=False,
                         inflation_rate=0,
                         print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')


class TestStrategy(unittest.TestCase):
    """ test all properties and methods of strategy base class"""

    def setUp(self) -> None:
        pass


class TestLSStrategy(RollingTiming):
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
        ma = sma(avg, n)
        if ma[-1] < price:
            return 0
        else:
            return 1


class TestSelStrategy(SimpleSelecting):
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

    def _realize(self, hist_data: np.ndarray, params: tuple):
        avg = np.nanmean(hist_data, axis=(1, 2))
        dif = (hist_data[:, :, 2] - np.roll(hist_data[:, :, 2], 1, 1))
        dif_no_nan = np.array([arr[~np.isnan(arr)][-1] for arr in dif])
        difper = dif_no_nan / avg
        large2 = difper.argsort()[1:]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        return chosen


class TestSelStrategyDiffTime(SimpleSelecting):
    """用于Test测试的简单选股策略，基于Selecting策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，从股票池的三只股票中选出今日变化率 = (今收-昨收)/平均股价（OHLC平均股价）最高的两支，放入中选池，否则落选。
    选股比例为平均分配
    """

    # TODO: This strategy is not working, find out why and improve
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

    def _realize(self, hist_data: np.ndarray, params: tuple):
        avg = hist_data.mean(axis=1).squeeze()
        difper = (hist_data[:, :, 0] - np.roll(hist_data[:, :, 0], 1))[:, -1] / avg
        large2 = difper.argsort()[0:2]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        return chosen


class TestSigStrategy(SimpleTiming):
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

        return sig


class MyStg(qt.RollingTiming):
    """自定义双均线择时策略策略"""

    def __init__(self):
        """这个均线择时策略只有三个参数：
            - SMA 慢速均线，所选择的股票
            - FMA 快速均线
            - M   边界值

            策略的其他说明

        """
        """
        必须初始化的关键策略参数清单：

        """
        super().__init__(
                pars=(20, 100, 0.01),
                par_count=3,
                par_types=['discr', 'discr', 'conti'],
                par_bounds_or_enums=[(10, 250), (10, 250), (0.0, 0.5)],
                stg_name='CUSTOM ROLLING TIMING STRATEGY',
                stg_text='Customized Rolling Timing Strategy for Testing',
                data_types='close',
                window_length=200,
        )

    # 策略的具体实现代码写在策略的_realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def _realize(self, hist_price, params):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        f, s, m = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        # 计算长短均线的当前值
        s_ma = qt.sma(h[0], s)[-1]
        f_ma = qt.sma(h[0], f)[-1]

        # 计算慢均线的停止边界，当快均线在停止边界范围内时，平仓，不发出买卖信号
        s_ma_u = s_ma * (1 + m)
        s_ma_l = s_ma * (1 - m)
        # 根据观望模式在不同的点位产生Long/short/empty标记

        if f_ma > s_ma_u:  # 当快均线在慢均线停止范围以上时，持有多头头寸
            return 1
        elif s_ma_l <= f_ma <= s_ma_u:  # 当均线在停止边界以内时，平仓
            return 0
        else:  # f_ma < s_ma_l   当快均线在慢均线停止范围以下时，持有空头头寸
            return -1


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

        # for sel_finance test
        shares_eps = np.array([[np.nan, np.nan, np.nan],
                               [0.1, np.nan, np.nan],
                               [np.nan, 0.2, np.nan],
                               [np.nan, np.nan, 0.3],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, 0.2],
                               [0.1, np.nan, np.nan],
                               [np.nan, 0.3, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [0.3, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, 0.3, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, 0.3],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, 0, 0.2],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [0.1, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, 0.2],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [0.15, np.nan, np.nan],
                               [np.nan, 0.1, np.nan],
                               [np.nan, np.nan, np.nan],
                               [0.1, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, 0.3],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [np.nan, np.nan, np.nan],
                               [0.2, np.nan, np.nan],
                               [np.nan, 0.5, np.nan],
                               [0.4, np.nan, 0.3],
                               [np.nan, np.nan, np.nan],
                               [np.nan, 0.3, np.nan],
                               [0.9, np.nan, np.nan],
                               [np.nan, np.nan, 0.1]])

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
        self.sel_finance_tyeps = ['eps']

        self.test_data_3D = np.zeros((3, data_rows, 4))
        self.test_data_2D = np.zeros((data_rows, 3))
        self.test_data_2D2 = np.zeros((data_rows, 4))
        self.test_data_sel_finance = np.empty((3, data_rows, 1))

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

        self.test_data_sel_finance[:, :, 0] = shares_eps.T

        self.hp1 = qt.HistoryPanel(values=self.test_data_3D,
                                   levels=self.shares,
                                   columns=self.types,
                                   rows=self.date_indices)
        print(f'in test Operator, history panel is created for timing test')
        self.hp1.info()
        self.hp2 = qt.HistoryPanel(values=self.test_data_sel_finance,
                                   levels=self.shares,
                                   columns=self.sel_finance_tyeps,
                                   rows=self.date_indices)
        print(f'in test_Operator, history panel is created for selection finance test:')
        self.hp2.info()
        self.op = qt.Operator(strategies='dma', signal_type='PS')
        self.op2 = qt.Operator(strategies='dma, macd, trix')

    def test_init(self):
        """ test initialization of Operator class"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.signal_type, 'pt')
        self.assertIsInstance(op.strategies, list)
        self.assertEqual(len(op.strategies), 0)
        op = qt.Operator('dma')
        self.assertIsInstance(op, qt.Operator)
        self.assertIsInstance(op.strategies, list)
        self.assertIsInstance(op.strategies[0], TimingDMA)
        op = qt.Operator('dma, macd')
        self.assertIsInstance(op, qt.Operator)
        op = qt.Operator(['dma', 'macd'])
        self.assertIsInstance(op, qt.Operator)

    def test_repr(self):
        """ test basic representation of Opeartor class"""
        op = qt.Operator()
        self.assertEqual(op.__repr__(), 'Operator()')

        op = qt.Operator('macd, dma, trix, random, avg_low')
        self.assertEqual(op.__repr__(), 'Operator(macd, dma, trix, random, avg_low)')
        self.assertEqual(op['dma'].__repr__(), 'Q-TIMING(DMA)')
        self.assertEqual(op['macd'].__repr__(), 'R-TIMING(MACD)')
        self.assertEqual(op['trix'].__repr__(), 'R-TIMING(TRIX)')
        self.assertEqual(op['random'].__repr__(), 'SELECT(RANDOM)')
        self.assertEqual(op['avg_low'].__repr__(), 'FACTOR(AVG LOW)')

    def test_info(self):
        """Test information output of Operator"""
        print(f'test printing information of operator object')
        self.op.info()

    def test_get_strategy_by_id(self):
        """ test get_strategy_by_id()"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        self.assertEqual(op.strategy_ids, ['macd', 'dma', 'trix'])
        self.assertIs(op.get_strategy_by_id('macd'), op.strategies[0])
        self.assertIs(op.get_strategy_by_id(1), op.strategies[1])
        self.assertIs(op.get_strategy_by_id('trix'), op.strategies[2])

    def test_get_items(self):
        """ test method __getitem__(), it should be the same as geting strategies by id"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        self.assertEqual(op.strategy_ids, ['macd', 'dma', 'trix'])
        self.assertIs(op['macd'], op.strategies[0])
        self.assertIs(op['trix'], op.strategies[2])
        self.assertIs(op[1], op.strategies[1])
        self.assertIs(op[3], op.strategies[2])

    def test_get_strategies_by_price_type(self):
        """ test get_strategies_by_price_type"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', price_type='open')
        op.set_parameter('dma', price_type='close')
        op.set_parameter('trix', price_type='open')
        stg_close = op.get_strategies_by_price_type('close')
        stg_open = op.get_strategies_by_price_type('open')
        stg_high = op.get_strategies_by_price_type('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, [op.strategies[1]])
        self.assertEqual(stg_open, [op.strategies[0], op.strategies[2]])
        self.assertEqual(stg_high, [])

        stg_wrong = op.get_strategies_by_price_type(123)
        self.assertIsInstance(stg_wrong, list)
        self.assertEqual(stg_wrong, [])

    def test_get_strategy_count_by_price_type(self):
        """ test get_strategy_count_by_price_type"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', price_type='open')
        op.set_parameter('dma', price_type='close')
        op.set_parameter('trix', price_type='open')
        stg_close = op.get_strategy_count_by_price_type('close')
        stg_open = op.get_strategy_count_by_price_type('open')
        stg_high = op.get_strategy_count_by_price_type('high')

        self.assertIsInstance(stg_close, int)
        self.assertIsInstance(stg_open, int)
        self.assertIsInstance(stg_high, int)

        self.assertEqual(stg_close, 1)
        self.assertEqual(stg_open, 2)
        self.assertEqual(stg_high, 0)

        stg_wrong = op.get_strategy_count_by_price_type(123)
        self.assertIsInstance(stg_wrong, int)
        self.assertEqual(stg_wrong, 0)

    def test_get_strategy_names_by_price_type(self):
        """ test get_strategy_names_by_price_type"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', price_type='open')
        op.set_parameter('dma', price_type='close')
        op.set_parameter('trix', price_type='open')
        stg_close = op.get_strategy_names_by_price_type('close')
        stg_open = op.get_strategy_names_by_price_type('open')
        stg_high = op.get_strategy_names_by_price_type('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, ['DMA'])
        self.assertEqual(stg_open, ['MACD', 'TRIX'])
        self.assertEqual(stg_high, [])

        stg_wrong = op.get_strategy_names_by_price_type(123)
        self.assertIsInstance(stg_wrong, list)
        self.assertEqual(stg_wrong, [])

    def test_get_strategy_id_by_price_type(self):
        """ test get_strategy_IDs_by_price_type"""
        print('-----Test get strategy IDs by price type------\n')
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', price_type='open')
        op.set_parameter('dma', price_type='close')
        op.set_parameter('trix', price_type='open')
        stg_close = op.get_strategy_id_by_price_type('close')
        stg_open = op.get_strategy_id_by_price_type('open')
        stg_high = op.get_strategy_id_by_price_type('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, ['dma'])
        self.assertEqual(stg_open, ['macd', 'trix'])
        self.assertEqual(stg_high, [])

        op.add_strategies('dma, macd')
        op.set_parameter('dma_1', price_type='open')
        op.set_parameter('macd', price_type='open')
        op.set_parameter('macd_1', price_type='high')
        op.set_parameter('trix', price_type='close')
        print(f'Operator strategy id:\n'
              f'{op.strategies} on memory pos:\n'
              f'{[id(stg) for stg in op.strategies]}')
        stg_close = op.get_strategy_id_by_price_type('close')
        stg_open = op.get_strategy_id_by_price_type('open')
        stg_high = op.get_strategy_id_by_price_type('high')
        stg_all = op.get_strategy_id_by_price_type()
        print(f'All IDs of strategies:\n'
              f'{stg_all}\n'
              f'All price types of strategies:\n'
              f'{[stg.price_type for stg in op.strategies]}')
        self.assertEqual(stg_close, ['dma', 'trix'])
        self.assertEqual(stg_open, ['macd', 'dma_1'])
        self.assertEqual(stg_high, ['macd_1'])

        stg_wrong = op.get_strategy_id_by_price_type(123)
        self.assertIsInstance(stg_wrong, list)
        self.assertEqual(stg_wrong, [])

    def test_property_strategies(self):
        """ test property strategies"""
        print(f'created a new simple Operator with only one strategy: DMA')
        op = qt.Operator('dma')
        strategies = op.strategies
        self.assertIsInstance(strategies, list)
        op.info()

        print(f'created the second simple Operator with three strategies')
        self.assertIsInstance(strategies[0], TimingDMA)
        op = qt.Operator('dma, macd, cdl')
        strategies = op.strategies
        op.info()
        self.assertIsInstance(strategies, list)
        self.assertIsInstance(strategies[0], TimingDMA)
        self.assertIsInstance(strategies[1], TimingMACD)
        self.assertIsInstance(strategies[2], TimingCDL)

    def test_property_strategy_count(self):
        """ test Property strategy_count, and the method get_strategy_count_by_price_type()"""
        self.assertEqual(self.op.strategy_count, 1)
        self.assertEqual(self.op2.strategy_count, 3)
        self.assertEqual(self.op.get_strategy_count_by_price_type(), 1)
        self.assertEqual(self.op2.get_strategy_count_by_price_type(), 3)
        self.assertEqual(self.op.get_strategy_count_by_price_type('close'), 1)
        self.assertEqual(self.op.get_strategy_count_by_price_type('high'), 0)
        self.assertEqual(self.op2.get_strategy_count_by_price_type('close'), 3)
        self.assertEqual(self.op2.get_strategy_count_by_price_type('open'), 0)

    def test_property_strategy_names(self):
        """ test property strategy_ids"""
        op = qt.Operator('dma')
        self.assertIsInstance(op.strategy_ids, list)
        names = op.strategy_ids[0]
        print(f'names are {names}')
        self.assertEqual(names, 'dma')

        op = qt.Operator('dma, macd, trix, cdl')
        self.assertIsInstance(op.strategy_ids, list)
        self.assertEqual(op.strategy_ids[0], 'dma')
        self.assertEqual(op.strategy_ids[1], 'macd')
        self.assertEqual(op.strategy_ids[2], 'trix')
        self.assertEqual(op.strategy_ids[3], 'cdl')

        op = qt.Operator('dma, macd, trix, dma, dma')
        self.assertIsInstance(op.strategy_ids, list)
        self.assertEqual(op.strategy_ids[0], 'dma')
        self.assertEqual(op.strategy_ids[1], 'macd')
        self.assertEqual(op.strategy_ids[2], 'trix')
        self.assertEqual(op.strategy_ids[3], 'dma_1')
        self.assertEqual(op.strategy_ids[4], 'dma_2')

    def test_property_strategy_blenders(self):
        """ test property strategy blenders including property setter,
            and test the method get_blender()"""
        print(f'------- Test property strategy blenders ---------')
        op = qt.Operator()
        self.assertIsInstance(op.strategy_blenders, dict)
        self.assertIsInstance(op.signal_type, str)
        self.assertEqual(op.strategy_blenders, {})
        self.assertEqual(op.signal_type, 'pt')
        # test adding blender to empty operator
        op.strategy_blenders = '1 + 2'
        op.signal_type = 'proportion signal'
        self.assertEqual(op.strategy_blenders, {})
        self.assertEqual(op.signal_type, 'ps')

        op.add_strategy('dma')
        op.strategy_blenders = '1+2'
        self.assertEqual(op.strategy_blenders, {'close': ['+', '2', '1']})

        op.clear_strategies()
        self.assertEqual(op.strategy_blenders, {})
        op.add_strategies('dma, trix, macd, dma')
        op.set_parameter('dma', price_type='open')
        op.set_parameter('trix', price_type='high')

        op.set_blender('open', '1+2')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, ['+', '2', '1'])
        self.assertEqual(blender_close, None)
        self.assertEqual(blender_high, None)

        op.set_blender('open', '1+2+3')
        op.set_blender('abc', '1+2+3')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        blender_abc = op.get_blender('abc')
        self.assertEqual(op.strategy_blenders, {'open': ['+', '3', '+', '2', '1']})
        self.assertEqual(blender_open, ['+', '3', '+', '2', '1'])
        self.assertEqual(blender_close, None)
        self.assertEqual(blender_high, None)
        self.assertEqual(blender_abc, None)

        op.set_blender('open', 123)
        blender_open = op.get_blender('open')
        self.assertEqual(blender_open, [])

        op.set_blender(None, '1+1')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(op.bt_price_types, ['close', 'high', 'open'])
        self.assertEqual(op.get_blender(), {'close': ['+', '1', '1'],
                                            'open':  ['+', '1', '1'],
                                            'high':  ['+', '1', '1']})
        self.assertEqual(blender_open, ['+', '1', '1'])
        self.assertEqual(blender_close, ['+', '1', '1'])
        self.assertEqual(blender_high, ['+', '1', '1'])

        op.set_blender(None, ['1+1', '3+4'])
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, ['+', '4', '3'])
        self.assertEqual(blender_close, ['+', '1', '1'])
        self.assertEqual(blender_high, ['+', '4', '3'])
        self.assertEqual(op.view_blender('open'), '3+4')
        self.assertEqual(op.view_blender('close'), '1+1')
        self.assertEqual(op.view_blender('high'), '3+4')

        op.strategy_blenders = (['1+2', '2*3', '1+4'])
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, ['+', '4', '1'])
        self.assertEqual(blender_close, ['+', '2', '1'])
        self.assertEqual(blender_high, ['*', '3', '2'])
        self.assertEqual(op.view_blender('open'), '1+4')
        self.assertEqual(op.view_blender('close'), '1+2')
        self.assertEqual(op.view_blender('high'), '2*3')

        # test error inputs:
        # wrong type of price_type
        self.assertRaises(TypeError, op.set_blender, 1, '1+3')
        # price_type not found, no change is made
        op.set_blender('volume', '1+3')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, ['+', '4', '1'])
        self.assertEqual(blender_close, ['+', '2', '1'])
        self.assertEqual(blender_high, ['*', '3', '2'])
        # price_type not valid, no change is made
        op.set_blender('closee', '1+2')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, ['+', '4', '1'])
        self.assertEqual(blender_close, ['+', '2', '1'])
        self.assertEqual(blender_high, ['*', '3', '2'])
        # wrong type of blender, set to empty list
        op.set_blender('open', 55)
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, [])
        self.assertEqual(blender_close, ['+', '2', '1'])
        self.assertEqual(blender_high, ['*', '3', '2'])
        # wrong type of blender, set to empty list
        op.set_blender('close', ['1+2'])
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, [])
        self.assertEqual(blender_close, [])
        self.assertEqual(blender_high, ['*', '3', '2'])
        # can't parse blender, set to empty list
        op.set_blender('high', 'a+bc')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, [])
        self.assertEqual(blender_close, [])
        self.assertEqual(blender_high, [])

    def test_property_singal_type(self):
        """ test property signal_type"""
        op = qt.Operator()
        self.assertIsInstance(op.signal_type, str)
        self.assertEqual(op.signal_type, 'pt')
        op = qt.Operator(signal_type='ps')
        self.assertIsInstance(op.signal_type, str)
        self.assertEqual(op.signal_type, 'ps')
        op = qt.Operator(signal_type='PS')
        self.assertEqual(op.signal_type, 'ps')
        op = qt.Operator(signal_type='proportion signal')
        self.assertEqual(op.signal_type, 'ps')
        print(f'"pt" will be the default type if wrong value is given')
        op = qt.Operator(signal_type='wrong value')
        self.assertEqual(op.signal_type, 'pt')

        print(f'test signal_type.setter')
        op.signal_type = 'ps'
        self.assertEqual(op.signal_type, 'ps')
        print(f'test error raising')
        self.assertRaises(TypeError, setattr, op, 'signal_type', 123)
        self.assertRaises(ValueError, setattr, op, 'signal_type', 'wrong value')

    def test_property_op_data_types(self):
        """ test property op_data_types"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_types, list)
        self.assertEqual(op.op_data_types, [])

        op = qt.Operator('macd, dma, trix')
        dt = op.op_data_types
        self.assertEqual(dt[0], 'close')

        op = qt.Operator('macd, cdl')
        dt = op.op_data_types
        self.assertEqual(dt[0], 'close')
        self.assertEqual(dt[1], 'high')
        self.assertEqual(dt[2], 'low')
        self.assertEqual(dt[3], 'open')
        self.assertEqual(dt, ['close', 'high', 'low', 'open'])
        op.add_strategy('dma')
        dt = op.op_data_types
        self.assertEqual(dt[0], 'close')
        self.assertEqual(dt[1], 'high')
        self.assertEqual(dt[2], 'low')
        self.assertEqual(dt[3], 'open')
        self.assertEqual(dt, ['close', 'high', 'low', 'open'])

    def test_property_op_data_type_count(self):
        """ test property op_data_type_count"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_type_count, int)
        self.assertEqual(op.op_data_type_count, 0)

        op = qt.Operator('macd, dma, trix')
        dtn = op.op_data_type_count
        self.assertEqual(dtn, 1)
        op = qt.Operator('macd, cdl')
        dtn = op.op_data_type_count
        self.assertEqual(dtn, 4)
        op.add_strategy('dma')
        dtn = op.op_data_type_count
        self.assertEqual(dtn, 4)

    def test_property_op_data_freq(self):
        """ test property op_data_freq"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_freq, str)
        self.assertEqual(len(op.op_data_freq), 0)
        self.assertEqual(op.op_data_freq, '')

        op = qt.Operator('macd, dma, trix')
        dtf = op.op_data_freq
        self.assertIsInstance(dtf, str)
        self.assertEqual(dtf[0], 'd')
        op.set_parameter('macd', data_freq='m')
        dtf = op.op_data_freq
        self.assertIsInstance(dtf, list)
        self.assertEqual(len(dtf), 2)
        self.assertEqual(dtf[0], 'd')
        self.assertEqual(dtf[1], 'm')

    def test_property_bt_price_types(self):
        """ test property bt_price_types"""
        print('------test property bt_price_tyeps-------')
        op = qt.Operator()
        self.assertIsInstance(op.bt_price_types, list)
        self.assertEqual(len(op.bt_price_types), 0)
        self.assertEqual(op.bt_price_types, [])

        op = qt.Operator('macd, dma, trix')
        btp = op.bt_price_types
        self.assertIsInstance(btp, list)
        self.assertEqual(btp[0], 'close')
        op.set_parameter('macd', price_type='open')
        btp = op.bt_price_types
        btpc = op.bt_price_type_count
        print(f'price_types are \n{btp}')
        self.assertIsInstance(btp, list)
        self.assertEqual(len(btp), 2)
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.add_strategies(['dma', 'macd'])
        op.set_parameter('dma_1', price_type='high')
        btp = op.bt_price_types
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'high')
        self.assertEqual(btp[2], 'open')
        self.assertEqual(btpc, 3)

        op.remove_strategy('dma_1')
        btp = op.bt_price_types
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.remove_strategy('macd_1')
        btp = op.bt_price_types
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

    def test_property_op_data_type_list(self):
        """ test property op_data_type_list"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_type_list, list)
        self.assertEqual(len(op.op_data_type_list), 0)
        self.assertEqual(op.op_data_type_list, [])

        op = qt.Operator('macd, dma, trix, cdl')
        ohd = op.op_data_type_list
        print(f'ohd is {ohd}')
        self.assertIsInstance(ohd, list)
        self.assertEqual(ohd[0], ['close'])
        op.set_parameter('macd', data_types='open, close')
        ohd = op.op_data_type_list
        print(f'ohd is {ohd}')
        self.assertIsInstance(ohd, list)
        self.assertEqual(len(ohd), 4)
        self.assertEqual(ohd[0], ['open', 'close'])
        self.assertEqual(ohd[1], ['close'])
        self.assertEqual(ohd[2], ['close'])
        self.assertEqual(ohd[3], ['open', 'high', 'low', 'close'])

    def test_property_op_history_data(self):
        """ Test this important function to get operation history data that shall be used in
            signal generation
            these data are stored in list of nd-arrays, each ndarray represents the data
            that is needed for each and every strategy
        """
        print(f'------- Test getting operation history data ---------')
        op = qt.Operator()
        self.assertIsInstance(op.strategy_blenders, dict)
        self.assertIsInstance(op.signal_type, str)
        self.assertEqual(op.strategy_blenders, {})
        self.assertEqual(op.op_history_data, {})
        self.assertEqual(op.signal_type, 'pt')

    def test_property_opt_space_par(self):
        """ test property opt_space_par"""
        print(f'-----test property opt_space_par--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.opt_space_par, tuple)
        self.assertIsInstance(op.opt_space_par[0], list)
        self.assertIsInstance(op.opt_space_par[1], list)
        self.assertEqual(len(op.opt_space_par), 2)
        self.assertEqual(op.opt_space_par, ([], []))

        op = qt.Operator('macd, dma, trix, cdl')
        osp = op.opt_space_par
        print(f'before setting opt_tags opt_space_par is empty:\n'
              f'osp is {osp}\n')
        self.assertIsInstance(osp, tuple)
        self.assertEqual(osp[0], [])
        self.assertEqual(osp[1], [])
        op.set_parameter('macd', opt_tag=1)
        op.set_parameter('dma', opt_tag=1)
        osp = op.opt_space_par
        print(f'after setting opt_tags opt_space_par is not empty:\n'
              f'osp is {osp}\n')
        self.assertIsInstance(osp, tuple)
        self.assertEqual(len(osp), 2)
        self.assertIsInstance(osp[0], list)
        self.assertIsInstance(osp[1], list)
        self.assertEqual(len(osp[0]), 6)
        self.assertEqual(len(osp[1]), 6)
        self.assertEqual(osp[0], [(10, 250), (10, 250), (10, 250), (10, 250), (10, 250), (10, 250)])
        self.assertEqual(osp[1], ['discr', 'discr', 'discr', 'discr', 'discr', 'discr'])

    def test_property_opt_types(self):
        """ test property opt_tags"""
        print(f'-----test property opt_tags--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.opt_tags, list)
        self.assertEqual(len(op.opt_tags), 0)
        self.assertEqual(op.opt_tags, [])

        op = qt.Operator('macd, dma, trix, cdl')
        otp = op.opt_tags
        print(f'before setting opt_tags opt_space_par is empty:\n'
              f'otp is {otp}\n')
        self.assertIsInstance(otp, list)
        self.assertEqual(otp, [0, 0, 0, 0])
        op.set_parameter('macd', opt_tag=1)
        op.set_parameter('dma', opt_tag=1)
        otp = op.opt_tags
        print(f'after setting opt_tags opt_space_par is not empty:\n'
              f'otp is {otp}\n')
        self.assertIsInstance(otp, list)
        self.assertEqual(len(otp), 4)
        self.assertEqual(otp, [1, 1, 0, 0])

    def test_property_max_window_length(self):
        """ test property max_window_length"""
        print(f'-----test property max window length--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.max_window_length, int)
        self.assertEqual(op.max_window_length, 0)

        op = qt.Operator('macd, dma, trix, cdl')
        mwl = op.max_window_length
        print(f'before setting window_length the value is 270:\n'
              f'mwl is {mwl}\n')
        self.assertIsInstance(mwl, int)
        self.assertEqual(mwl, 270)
        op.set_parameter('macd', window_length=300)
        op.set_parameter('dma', window_length=350)
        mwl = op.max_window_length
        print(f'after setting window_length the value is new set value:\n'
              f'mwl is {mwl}\n')
        self.assertIsInstance(mwl, int)
        self.assertEqual(mwl, 350)

    def test_property_bt_price_type_count(self):
        """ test property bt_price_type_count"""
        print(f'-----test property bt_price_type_count--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.bt_price_type_count, int)
        self.assertEqual(op.bt_price_type_count, 0)

        op = qt.Operator('macd, dma, trix, cdl')
        otp = op.bt_price_type_count
        print(f'before setting price_type the price count is 1:\n'
              f'otp is {otp}\n')
        self.assertIsInstance(otp, int)
        self.assertEqual(otp, 1)
        op.set_parameter('macd', price_type='open')
        op.set_parameter('dma', price_type='open')
        otp = op.bt_price_type_count
        print(f'after setting price_type the price type count is 2:\n'
              f'otp is {otp}\n')
        self.assertIsInstance(otp, int)
        self.assertEqual(otp, 2)

    def test_property_set(self):
        """ test all property setters:
            setting following properties:
            - strategy_blenders
            - signal_type
            other properties can not be set"""
        print(f'------- Test setting properties ---------')
        op = qt.Operator()
        self.assertIsInstance(op.strategy_blenders, dict)
        self.assertIsInstance(op.signal_type, str)
        self.assertEqual(op.strategy_blenders, {})
        self.assertEqual(op.signal_type, 'pt')
        op.strategy_blenders = '1 + 2'
        op.signal_type = 'proportion signal'
        self.assertEqual(op.strategy_blenders, {})
        self.assertEqual(op.signal_type, 'ps')

        op = qt.Operator('macd, dma, trix, cdl')
        # TODO: 修改set_parameter()，使下面的用法成立
        # a_to_sell.set_parameter('dma, cdl', price_type='open')
        op.set_parameter('dma', price_type='open')
        op.set_parameter('cdl', price_type='open')
        sb = op.strategy_blenders
        st = op.signal_type
        self.assertIsInstance(sb, dict)
        print(f'before setting: strategy_blenders={sb}')
        self.assertEqual(sb, {})
        op.strategy_blenders = '1+2 * 3'
        sb = op.strategy_blenders
        print(f'after setting strategy_blender={sb}')
        self.assertEqual(sb, {'close': ['+', '*', '3', '2', '1'],
                              'open':  ['+', '*', '3', '2', '1']})
        op.strategy_blenders = ['1+2', '3-4']
        sb = op.strategy_blenders
        print(f'after setting strategy_blender={sb}')
        self.assertEqual(sb, {'close': ['+', '2', '1'],
                              'open':  ['-', '4', '3']})

    def test_operator_ready(self):
        """test the method ready of Operator"""
        op = qt.Operator()
        print(f'operator is ready? "{op.ready}"')

    def test_operator_add_strategy(self):
        """test adding strategies to Operator"""
        op = qt.Operator('dma, all, urgent')

        self.assertIsInstance(op, qt.Operator)
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[1], qt.SelectingAll)
        self.assertIsInstance(op.strategies[2], qt.RiconUrgent)
        self.assertIsInstance(op[0], qt.TimingDMA)
        self.assertIsInstance(op[1], qt.SelectingAll)
        self.assertIsInstance(op[2], qt.RiconUrgent)
        self.assertIsInstance(op['dma'], qt.TimingDMA)
        self.assertIsInstance(op['all'], qt.SelectingAll)
        self.assertIsInstance(op['urgent'], qt.RiconUrgent)
        self.assertEqual(op.strategy_count, 3)
        print(f'test adding strategies into existing op')
        print('test adding strategy by string')
        op.add_strategy('macd')
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[3], qt.TimingMACD)
        self.assertEqual(op.strategy_count, 4)
        op.add_strategy('random')
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[4], qt.SelectingRandom)
        self.assertEqual(op.strategy_count, 5)
        test_ls = TestLSStrategy()
        op.add_strategy(test_ls)
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[5], TestLSStrategy)
        self.assertEqual(op.strategy_count, 6)
        print(f'Test different instance of objects are added to operator')
        op.add_strategy('dma')
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[6], qt.TimingDMA)
        self.assertIsNot(op.strategies[0], op.strategies[6])

    def test_operator_add_strategies(self):
        """ etst adding multiple strategies to Operator"""
        op = qt.Operator('dma, all, urgent')
        self.assertEqual(op.strategy_count, 3)
        print('test adding multiple strategies -- adding strategy by list of strings')
        op.add_strategies(['dma', 'macd'])
        self.assertEqual(op.strategy_count, 5)
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[3], qt.TimingDMA)
        self.assertIsInstance(op.strategies[4], qt.TimingMACD)
        print('test adding multiple strategies -- adding strategy by comma separated strings')
        op.add_strategies('dma, macd')
        self.assertEqual(op.strategy_count, 7)
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[5], qt.TimingDMA)
        self.assertIsInstance(op.strategies[6], qt.TimingMACD)
        print('test adding multiple strategies -- adding strategy by list of strategies')
        op.add_strategies([qt.TimingDMA(), qt.TimingMACD()])
        self.assertEqual(op.strategy_count, 9)
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[7], qt.TimingDMA)
        self.assertIsInstance(op.strategies[8], qt.TimingMACD)
        print('test adding multiple strategies -- adding strategy by list of strategy and str')
        op.add_strategies(['DMA', qt.TimingMACD()])
        self.assertEqual(op.strategy_count, 11)
        self.assertIsInstance(op.strategies[0], qt.TimingDMA)
        self.assertIsInstance(op.strategies[9], qt.TimingDMA)
        self.assertIsInstance(op.strategies[10], qt.TimingMACD)
        self.assertIsNot(op.strategies[0], op.strategies[9])
        self.assertIs(type(op.strategies[0]), type(op.strategies[9]))
        print('test adding fault data')
        self.assertRaises(AssertionError, op.add_strategies, 123)
        self.assertRaises(AssertionError, op.add_strategies, None)

    def test_opeartor_remove_strategy(self):
        """ test method remove strategy"""
        op = qt.Operator('dma, all, urgent')
        op.add_strategies(['dma', 'macd'])
        op.add_strategies(['DMA', TestLSStrategy()])
        self.assertEqual(op.strategy_count, 7)
        print('test removing strategies from Operator')
        op.remove_strategy('dma')
        self.assertEqual(op.strategy_count, 6)
        self.assertEqual(op.strategy_ids, ['all', 'urgent', 'dma_1', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['urgent'])
        self.assertEqual(op.strategies[2], op['dma_1'])
        self.assertEqual(op.strategies[3], op['macd'])
        self.assertEqual(op.strategies[4], op['dma_2'])
        self.assertEqual(op.strategies[5], op['custom'])
        op.remove_strategy('dma_1')
        self.assertEqual(op.strategy_count, 5)
        self.assertEqual(op.strategy_ids, ['all', 'urgent', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['urgent'])
        self.assertEqual(op.strategies[2], op['macd'])
        self.assertEqual(op.strategies[3], op['dma_2'])
        self.assertEqual(op.strategies[4], op['custom'])

    def test_opeartor_clear_strategies(self):
        """ test operator clear strategies"""
        op = qt.Operator('dma, all, urgent')
        op.add_strategies(['dma', 'macd'])
        op.add_strategies(['DMA', TestLSStrategy()])
        self.assertEqual(op.strategy_count, 7)
        print('test removing strategies from Operator')
        op.clear_strategies()
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])
        op.add_strategy('dma', pars=(12, 123, 25))
        self.assertEqual(op.strategy_count, 1)
        self.assertEqual(op.strategy_ids, ['dma'])
        self.assertEqual(type(op.strategies[0]), TimingDMA)
        self.assertEqual(op.strategies[0].pars, (12, 123, 25))
        op.clear_strategies()
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

    def test_operator_prepare_data(self):
        """test processes that related to prepare data"""
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        test_sig = TestSigStrategy()
        self.op = qt.Operator(strategies=[test_ls, test_sel, test_sig])
        too_early_cash = qt.CashPlan(dates='2016-01-01', amounts=10000)
        early_cash = qt.CashPlan(dates='2016-07-01', amounts=10000)
        on_spot_cash = qt.CashPlan(dates='2016-07-08', amounts=10000)
        no_trade_cash = qt.CashPlan(dates='2016-07-08, 2016-07-30, 2016-08-11, 2016-09-03',
                                    amounts=[10000, 10000, 10000, 10000])
        # 在所有策略的参数都设置好之前调用prepare_data会发生assertion Error
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          hist_data=self.hp1,
                          cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000))
        late_cash = qt.CashPlan(dates='2016-12-31', amounts=10000)
        multi_cash = qt.CashPlan(dates='2016-07-08, 2016-08-08', amounts=[10000, 10000])
        self.op.set_parameter(stg_id='custom',
                              pars={'000300': (5, 10.),
                                    '000400': (5, 10.),
                                    '000500': (5, 6.)})
        self.assertEqual(self.op.strategies[0].pars, {'000300': (5, 10.),
                                                      '000400': (5, 10.),
                                                      '000500': (5, 6.)})
        self.op.set_parameter(stg_id='custom_1',
                              pars=())
        self.assertEqual(self.op.strategies[1].pars, ()),
        self.op.set_parameter(stg_id='custom_2',
                              pars=(0.2, 0.02, -0.02))
        self.assertEqual(self.op.strategies[2].pars, (0.2, 0.02, -0.02)),
        self.op.prepare_data(hist_data=self.hp1,
                             cash_plan=on_spot_cash)
        self.assertIsInstance(self.op._op_history_data, dict)
        self.assertEqual(len(self.op._op_history_data), 3)
        # test if automatic strategy blenders are set
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['+', '2', '+', '1', '0']})
        tim_hist_data = self.op._op_history_data['custom']
        sel_hist_data = self.op._op_history_data['custom_1']
        ric_hist_data = self.op._op_history_data['custom_2']

        print(f'in test_prepare_data in TestOperator:')
        print('selecting history data:\n', sel_hist_data)
        print('originally passed data in correct sequence:\n', self.test_data_3D[:, 3:, [2, 3, 0]])
        print('difference is \n', sel_hist_data - self.test_data_3D[:, :, [2, 3, 0]])
        self.assertTrue(np.allclose(sel_hist_data, self.test_data_3D[:, :, [2, 3, 0]], equal_nan=True))
        self.assertTrue(np.allclose(tim_hist_data, self.test_data_3D, equal_nan=True))
        self.assertTrue(np.allclose(ric_hist_data, self.test_data_3D[:, 3:, :], equal_nan=True))

        # raises Value Error if empty history panel is given
        empty_hp = qt.HistoryPanel()
        correct_hp = qt.HistoryPanel(values=np.random.randint(10, size=(3, 50, 4)),
                                     columns=self.types,
                                     levels=self.shares,
                                     rows=self.date_indices)
        too_many_shares = qt.HistoryPanel(values=np.random.randint(10, size=(5, 50, 4)))
        too_many_types = qt.HistoryPanel(values=np.random.randint(10, size=(3, 50, 5)))
        # raises Error when history panel is empty
        self.assertRaises(ValueError,
                          self.op.prepare_data,
                          empty_hp,
                          on_spot_cash)
        # raises Error when first investment date is too early
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          early_cash)
        # raises Error when last investment date is too late
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          late_cash)
        # raises Error when some of the investment dates are on no-trade-days
        self.assertRaises(ValueError,
                          self.op.prepare_data,
                          correct_hp,
                          no_trade_cash)
        # raises Error when number of shares in history data does not fit
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          too_many_shares,
                          on_spot_cash)
        # raises Error when too early cash investment date
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          correct_hp,
                          too_early_cash)
        # raises Error when number of d_types in history data does not fit
        self.assertRaises(AssertionError,
                          self.op.prepare_data,
                          too_many_types,
                          on_spot_cash)

        # test the effect of data type sequence in strategy definition

    def test_operator_generate(self):
        """ Test signal generation process of operator objects

        :return:
        """
        # 使用test模块的自定义策略生成三种交易策略
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        test_sel2 = TestSelStrategyDiffTime()
        test_sig = TestSigStrategy()
        print('--Test PT type signal generation--')
        # 测试PT类型的信号生成：
        # 创建一个Operator对象，信号类型为PT（比例目标信号）
        # 这个Operator对象包含两个策略，分别为LS-Strategy以及Sel-Strategy，代表择时和选股策略
        # 两个策略分别生成PT信号后混合成一个信号输出
        self.op = qt.Operator(strategies=[test_ls, test_sel])
        self.op.set_parameter(stg_id='custom',
                              pars={'000010': (5, 10.),
                                    '000030': (5, 10.),
                                    '000039': (5, 6.)})
        self.op.set_parameter(stg_id=1,
                              pars=())
        # self.a_to_sell.set_blender(blender='0+1+2')
        self.op.prepare_data(hist_data=self.hp1,
                             cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000))
        print('--test operator information in normal mode--')
        self.op.info()
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['+', '1', '0']})
        self.op.set_blender(None, '0*1')
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['*', '1', '0']})
        print('--test operation signal created in Proportional Target (PT) Mode--')
        op_list = self.op.create_signal(hist_data=self.hp1)

        self.assertTrue(isinstance(op_list, HistoryPanel))
        backtest_price_types = op_list.htypes
        self.assertEqual(backtest_price_types[0], 'close')
        self.assertEqual(op_list.shape, (3, 45, 1))
        reduced_op_list = op_list.values.squeeze().T
        print(f'op_list created, it is a 3 share/45 days/1 htype array, to make comparison happen, \n'
              f'it will be squeezed to a 2-d array to compare on share-wise:\n'
              f'{reduced_op_list}')
        target_op_values = np.array([[0.0, 0.0, 0.0],
                                     [0.0, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.0, 0.0],
                                     [0.5, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.5],
                                     [0.0, 0.5, 0.5],
                                     [0.0, 0.5, 0.5],
                                     [0.0, 0.5, 0.5],
                                     [0.0, 0.5, 0.5],
                                     [0.0, 0.5, 0.5],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0],
                                     [0.0, 0.5, 0.0]])

        self.assertTrue(np.allclose(target_op_values, reduced_op_list, equal_nan=True))

        print('--Test two separate signal generation for different price types--')
        # 测试两组PT类型的信号生成：
        # 在Operator对象中增加两个SigStrategy策略，策略类型相同但是策略的参数不同，回测价格类型为"OPEN"
        # Opeartor应该生成两组交易信号，分别用于"close"和"open"两中不同的价格类型
        # 这里需要重新生成两个新的交易策略对象，否则在op的strategies列表中产生重复的对象引用，从而引起错误
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        self.op.add_strategies([test_ls, test_sel])
        self.op.set_parameter(stg_id='custom_2',
                              price_type='open')
        self.op.set_parameter(stg_id='custom_3',
                              price_type='open')
        self.assertEqual(self.op['custom'].price_type, 'close')
        self.assertEqual(self.op['custom_2'].price_type, 'open')
        self.op.set_parameter(stg_id='custom_2',
                              pars={'000010': (5, 10.),
                                    '000030': (5, 10.),
                                    '000039': (5, 6.)})
        self.op.set_parameter(stg_id='custom_3',
                              pars=())
        self.op.set_blender(blender='0 or 1', price_type='open')
        self.op.prepare_data(hist_data=self.hp1,
                             cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000))
        print('--test how operator information is printed out--')
        self.op.info()
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['*', '1', '0'],
                          'open':  ['or', '1', '0']})
        print('--test opeartion signal created in Proportional Target (PT) Mode--')
        op_list = self.op.create_signal(hist_data=self.hp1)

        self.assertTrue(isinstance(op_list, HistoryPanel))
        signal_close = op_list['close'].squeeze().T
        signal_open = op_list['open'].squeeze().T
        self.assertEqual(signal_close.shape, (45, 3))
        self.assertEqual(signal_open.shape, (45, 3))

        target_op_close = np.array([[0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.0, 0.0],
                                    [0.5, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.5],
                                    [0.0, 0.5, 0.5],
                                    [0.0, 0.5, 0.5],
                                    [0.0, 0.5, 0.5],
                                    [0.0, 0.5, 0.5],
                                    [0.0, 0.5, 0.5],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0],
                                    [0.0, 0.5, 0.0]])
        target_op_open = np.array([[0.5, 0.5, 1.0],
                                   [0.5, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 0.5, 1.0],
                                   [1.0, 1.0, 1.0],
                                   [1.0, 1.0, 1.0],
                                   [1.0, 1.0, 1.0],
                                   [1.0, 1.0, 0.0],
                                   [1.0, 1.0, 0.0],
                                   [1.0, 1.0, 0.0],
                                   [1.0, 0.5, 0.0],
                                   [1.0, 0.5, 0.0],
                                   [1.0, 1.0, 0.0],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.5, 1.0, 0.0],
                                   [0.5, 1.0, 0.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.0, 1.0, 1.0],
                                   [0.0, 1.0, 1.0],
                                   [0.0, 1.0, 1.0],
                                   [0.0, 1.0, 1.0],
                                   [0.0, 1.0, 1.0],
                                   [0.0, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0],
                                   [0.5, 1.0, 1.0]])

        signal_pairs = [[list(sig1), list(sig2), sig1 == sig2]
                        for sig1, sig2
                        in zip(list(target_op_close), list(signal_close))]
        print(f'signals side by side:\n'
              f'{signal_pairs}')
        self.assertTrue(np.allclose(target_op_close, signal_close, equal_nan=True))
        signal_pairs = [[list(sig1), list(sig2), sig1 == sig2]
                        for sig1, sig2
                        in zip(list(target_op_open), list(signal_open))]
        print(f'signals side by side:\n'
              f'{signal_pairs}')
        self.assertTrue(np.allclose(target_op_open, signal_open, equal_nan=True))

        print('--Test two separate signal generation for different price types--')
        # 更多测试集合

    def test_stg_parameter_setting(self):
        """ test setting parameters of strategies
        test the method set_parameters

        :return:
        """
        op = qt.Operator(strategies='dma, all, urgent')
        print(op.strategies, '\n', [qt.TimingDMA, qt.SelectingAll, qt.RiconUrgent])
        print(f'info of Timing strategy in new op: \n{op.strategies[0].info()}')
        # TODO: allow set_parameters to a list of strategies or str-listed strategies
        # TODO: allow set_parameters to all strategies of specific bt price type
        print(f'Set up strategy parameters by strategy id')
        op.set_parameter('dma',
                         pars=(5, 10, 5),
                         opt_tag=1,
                         par_boes=((5, 10), (5, 15), (10, 15)),
                         window_length=10,
                         data_types=['close', 'open', 'high'])
        op.set_parameter('all',
                         window_length=20)
        op.set_parameter('all', price_type='high')
        print(f'Can also set up strategy parameters by strategy index')
        op.set_parameter(2, price_type='open')
        op.set_parameter(2,
                         opt_tag=1,
                         pars=(9, -0.09),
                         window_length=10)
        self.assertEqual(op.strategies[0].pars, (5, 10, 5))
        self.assertEqual(op.strategies[0].par_boes, ((5, 10), (5, 15), (10, 15)))
        self.assertEqual(op.strategies[2].pars, (9, -0.09))
        self.assertEqual(op.op_data_freq, 'd')
        self.assertEqual(op.op_data_types, ['close', 'high', 'open'])
        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (10, 15), (1, 40), (-0.5, 0.5)],
                          ['discr', 'discr', 'discr', 'discr', 'conti']))
        self.assertEqual(op.max_window_length, 20)
        print(f'KeyError will be raised if wrong strategy id is given')
        self.assertRaises(KeyError, op.set_parameter, stg_id='t-1', pars=(1, 2))
        self.assertRaises(KeyError, op.set_parameter, stg_id='wrong_input', pars=(1, 2))
        print(f'ValueError will be raised if parameter can be set')
        self.assertRaises(ValueError, op.set_parameter, stg_id=0, pars=('wrong input', 'wrong input'))
        # test blenders of different price types
        # test setting blenders to different price types
        # TODO: to allow operands like "and", "or", "not", "xor"
        # a_to_sell.set_blender('close', '0 and 1 or 2')
        # self.assertEqual(a_to_sell.get_blender('close'), 'str-1.2')
        self.assertEqual(op.bt_price_types, ['close', 'high', 'open'])
        op.set_blender('open', '0 & 1 | 2')
        self.assertEqual(op.get_blender('open'), ['|', '2', '&', '1', '0'])
        op.set_blender('high', '(0|1) & 2')
        self.assertEqual(op.get_blender('high'), ['&', '2', '|', '1', '0'])
        op.set_blender('close', '0 & 1 | 2')
        self.assertEqual(op.get_blender(), {'close': ['|', '2', '&', '1', '0'],
                                            'high':  ['&', '2', '|', '1', '0'],
                                            'open':  ['|', '2', '&', '1', '0']})

        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (10, 15), (1, 40), (-0.5, 0.5)],
                          ['discr', 'discr', 'discr', 'discr', 'conti']))
        self.assertEqual(op.opt_tags, [1, 0, 1])

    def test_signal_blend(self):
        self.assertEqual(blender_parser('0 & 1'), ['&', '1', '0'])
        self.assertEqual(blender_parser('0 or 1'), ['or', '1', '0'])
        self.assertEqual(blender_parser('0 & 1 | 2'), ['|', '2', '&', '1', '0'])
        blender = blender_parser('0 & 1 | 2')
        self.assertEqual(signal_blend([1, 1, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 1, 0], blender), 1)
        self.assertEqual(signal_blend([0, 1, 1], blender), 1)
        self.assertEqual(signal_blend([0, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 0], blender), 0)
        self.assertEqual(signal_blend([0, 1, 0], blender), 0)
        self.assertEqual(signal_blend([0, 0, 0], blender), 0)
        # parse: '0 & ( 1 | 2 )'
        self.assertEqual(blender_parser('0 & ( 1 | 2 )'), ['&', '|', '2', '1', '0'])
        blender = blender_parser('0 & ( 1 | 2 )')
        self.assertEqual(signal_blend([1, 1, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 1, 0], blender), 1)
        self.assertEqual(signal_blend([0, 1, 1], blender), 0)
        self.assertEqual(signal_blend([0, 0, 1], blender), 0)
        self.assertEqual(signal_blend([1, 0, 0], blender), 0)
        self.assertEqual(signal_blend([0, 1, 0], blender), 0)
        self.assertEqual(signal_blend([0, 0, 0], blender), 0)
        # parse: '(1-2)/3 + 0'
        self.assertEqual(blender_parser('(1-2)/3 + 0'), ['+', '0', '/', '3', '-', '2', '1'])
        blender = blender_parser('(1-2)/3 + 0')
        self.assertEqual(signal_blend([5, 9, 1, 4], blender), 7)
        # pars: '(0*1/2*(3+4))+5*(6+7)-8'
        self.assertEqual(blender_parser('(0*1/2*(3+4))+5*(6+7)-8'), ['-', '8', '+', '*', '+', '7', '6', '5', '*',
                                                                     '+', '4', '3', '/', '2', '*', '1', '0'])
        blender = blender_parser('(0*1/2*(3+4))+5*(6+7)-8')
        self.assertEqual(signal_blend([1, 1, 1, 1, 1, 1, 1, 1, 1], blender), 3)
        self.assertEqual(signal_blend([2, 1, 4, 3, 5, 5, 2, 2, 10], blender), 14)
        # parse: '0/max(2,1,3 + 5)+4'
        self.assertEqual(blender_parser('0/max(2,1,3 + 5)+4'), ['+', '4', '/', 'max(3)', '+', '5', '3', '1', '2', '0'])
        blender = blender_parser('0/max(2,1,3 + 5)+4')
        self.assertEqual(signal_blend([8.0, 4, 3, 5.0, 0.125, 5], blender), 0.925)
        self.assertEqual(signal_blend([2, 1, 4, 3, 5, 5, 2, 2, 10], blender), 5.25)

        print('speed test')
        import time
        st = time.time()
        blender = blender_parser('0+max(1,2,(3+4)*5, max(6, (7+8)*9), 10-11) * (12+13)')
        res = []
        for i in range(10000):
            res = signal_blend([1, 1, 2, 3, 4, 5, 3, 4, 5, 6, 7, 8, 2, 3], blender)
        et = time.time()
        print(f'total time for RPN processing: {et - st}, got result: {res}')

        blender = blender_parser("0 + 1 * 2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 7)
        blender = blender_parser("(0 + 1) * 2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(0+1) * 2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(0 + 1)   * 2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        # TODO: 目前对于-(1+2)这样的表达式还无法处理
        # self.a_to_sell.set_blender('selecting', "-(0 + 1) * 2")
        # self.assertEqual(self.a_to_sell.signal_blend([1, 2, 3]), -9)
        blender = blender_parser("(0-1)/2 + 3")
        print(f'RPN of notation: "(0-1)/2 + 3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), -0.33333333)
        blender = blender_parser("0 + 1 / 2")
        print(f'RPN of notation: "0 + 1 / 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, math.pi, 4], blender), 1.78539816)
        blender = blender_parser("(0 + 1) / 2")
        print(f'RPN of notation: "(0 + 1) / 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(signal_blend([1, 2, 3], blender), 1)
        blender = blender_parser("(0 + 1 * 2) / 3")
        print(f'RPN of notation: "(0 + 1 * 2) / 3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([3, math.e, 10, 10], blender), 3.0182818284590454)
        blender = blender_parser("0 / 1 * 2")
        print(f'RPN of notation: "0 / 1 * 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(signal_blend([1, 3, 6], blender), 2)
        blender = blender_parser("(0 - 1 + 2) * 4")
        print(f'RPN of notation: "(0 - 1 + 2) * 4" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 1, -1, np.nan, math.pi], blender), -3.141592653589793)
        blender = blender_parser("0 * 1")
        print(f'RPN of notation: "0 * 1" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([math.pi, math.e], blender), 8.539734222673566)

        blender = blender_parser('abs(3-sqrt(2) /  cos(1))')
        print(f'RPN of notation: "abs(3-sqrt(2) /  cos(1))" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['abs(1)', '-', '/', 'cos(1)', '1', 'sqrt(1)', '2', '3'])
        blender = blender_parser('0/max(2,1,3 + 5)+4')
        print(f'RPN of notation: "0/max(2,1,3 + 5)+4" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '4', '/', 'max(3)', '+', '5', '3', '1', '2', '0'])

        blender = blender_parser('1 + sum(1,2,3+3, sum(1, 2) + 3) *5')
        print(f'RPN of notation: "1 + sum(1,2,3+3, sum(1, 2) + 3) *5" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '*', '5', 'sum(4)', '+', '3', 'sum(2)', '2', '1',
                                   '+', '3', '3', '2', '1', '1'])
        blender = blender_parser('1+sum(1,2,(3+5)*4, sum(3, (4+5)*6), 7-8) * (2+3)')
        print(f'RPN of notation: "1+sum(1,2,(3+5)*4, sum(3, (4+5)*6), 7-8) * (2+3)" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '*', '+', '3', '2', 'sum(5)', '-', '8', '7',
                                   'sum(2)', '*', '6', '+', '5', '4', '3', '*', '4',
                                   '+', '5', '3', '2', '1', '1'])

        # TODO: ndarray type of signals to be tested:

    def test_set_opt_par(self):
        """ test setting opt pars in batch"""
        print(f'--------- Testing setting Opt Pars: set_opt_par -------')
        op = qt.Operator('dma, random, crossline')
        op.set_parameter('dma',
                         pars=(5, 10, 5),
                         opt_tag=1,
                         par_boes=((5, 10), (5, 15), (10, 15)),
                         window_length=10,
                         data_types=['close', 'open', 'high'])
        self.assertEqual(op.strategies[0].pars, (5, 10, 5))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (35, 120, 10, 'buy'))
        self.assertEqual(op.opt_tags, [1, 0, 0])
        op.set_opt_par((5, 12, 9))
        self.assertEqual(op.strategies[0].pars, (5, 12, 9))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (35, 120, 10, 'buy'))

        op.set_parameter('crossline',
                         pars=(5, 10, 5, 'sell'),
                         opt_tag=1,
                         par_boes=((5, 10), (5, 15), (10, 15), ('buy', 'sell', 'none')),
                         window_length=10,
                         data_types=['close', 'open', 'high'])
        self.assertEqual(op.opt_tags, [1, 0, 1])
        op.set_opt_par((5, 12, 9, 8, 26, 9, 'buy'))
        self.assertEqual(op.strategies[0].pars, (5, 12, 9))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (8, 26, 9, 'buy'))

        op.set_opt_par((9, 200, 155, 8, 26, 9, 'buy', 5, 12, 9))
        self.assertEqual(op.strategies[0].pars, (9, 200, 155))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (8, 26, 9, 'buy'))

        # test set_opt_par when opt_tag is set to be 2 (enumerate type of parameters)
        op.set_parameter('crossline',
                         pars=(5, 10, 5, 'sell'),
                         opt_tag=2,
                         par_boes=((5, 10), (5, 15), (10, 15), ('buy', 'sell', 'none')),
                         window_length=10,
                         data_types=['close', 'open', 'high'])
        self.assertEqual(op.opt_tags, [1, 0, 2])
        self.assertEqual(op.strategies[0].pars, (9, 200, 155))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (5, 10, 5, 'sell'))
        op.set_opt_par((5, 12, 9, (8, 26, 9, 'buy')))
        self.assertEqual(op.strategies[0].pars, (5, 12, 9))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (8, 26, 9, 'buy'))

        # Test Errors
        # Not enough values for parameter
        op.set_parameter('crossline', opt_tag=1)
        self.assertRaises(ValueError, op.set_opt_par, (5, 12, 9, 8))
        # wrong type of input
        self.assertRaises(AssertionError, op.set_opt_par, [5, 12, 9, 7, 15, 12, 'sell'])

    def test_stg_attribute_get_and_set(self):
        self.stg = qt.TimingCrossline()
        self.stg_type = 'R-TIMING'
        self.stg_name = "CROSSLINE"
        self.stg_text = 'Moving average crossline strategy, determine long/short position according to the cross ' \
                        'point' \
                        ' of long and short term moving average prices '
        self.pars = (35, 120, 10, 'buy')
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
                           [1., 1., 1.],
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
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.],
                           [0., 1., 1.]])
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
                              [0.0, 1.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0]])

        side_by_side_array = np.array([[i, out_line, sig_line]
                                       for
                                       i, out_line, sig_line
                                       in zip(range(len(output)), output, sigmatrix)])
        print(f'output and signal matrix lined up side by side is \n'
              f'{side_by_side_array}')
        self.assertEqual(sigmatrix.shape, output.shape)
        self.assertTrue(np.allclose(output, sigmatrix))

    def test_sel_finance(self):
        """Test selecting_finance strategy, test all built-in strategy parameters"""
        stg = SelectingFinanceIndicator()
        stg_pars = (False, 'even', 'greater', 0, 0, 0.67)
        stg.set_pars(stg_pars)
        stg.window_length = 5
        stg.data_freq = 'd'
        stg.sample_freq = '10d'
        stg.sort_ascending = False
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg._poq = 0.67
        history_data = self.hp2.values
        print(f'Start to test financial selection parameter {stg_pars}')

        seg_pos, seg_length, seg_count = stg._seg_periods(dates=self.hp1.hdates, freq=stg.sample_freq)
        self.assertEqual(list(seg_pos), [0, 5, 11, 19, 26, 33, 41, 47, 49])
        self.assertEqual(list(seg_length), [5, 6, 8, 7, 7, 8, 6, 2])
        self.assertEqual(seg_count, 8)

        output = stg.generate(hist_data=history_data, shares=self.hp1.shares, dates=self.hp1.hdates)

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0]])

        self.assertEqual(output.shape, selmask.shape)
        self.assertTrue(np.allclose(output, selmask))

        # test single factor, get mininum factor
        stg_pars = (True, 'even', 'less', 1, 1, 0.67)
        stg.sort_ascending = True
        stg.condition = 'less'
        stg.lbound = 1
        stg.ubound = 1
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=history_data, shares=self.hp1.shares, dates=self.hp1.hdates)
        selmask = np.array([[0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
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
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5],
                            [0.5, 0.0, 0.5]])

        self.assertEqual(output.shape, selmask.shape)
        self.assertTrue(np.allclose(output, selmask))

        # test single factor, get max factor in linear weight
        stg_pars = (False, 'linear', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'linear'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=history_data, shares=self.hp1.shares, dates=self.hp1.hdates)
        selmask = np.array([[0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.66667, 0.33333],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.00000, 0.33333, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.00000, 0.66667],
                            [0.33333, 0.66667, 0.00000],
                            [0.33333, 0.66667, 0.00000],
                            [0.33333, 0.66667, 0.00000]])

        self.assertEqual(output.shape, selmask.shape)
        self.assertTrue(np.allclose(output, selmask))

        # test single factor, get max factor in linear weight
        stg_pars = (False, 'proportion', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'proportion'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=history_data, shares=self.hp1.shares, dates=self.hp1.hdates)
        selmask = np.array([[0.00000, 0.08333, 0.91667],
                            [0.00000, 0.08333, 0.91667],
                            [0.00000, 0.08333, 0.91667],
                            [0.00000, 0.08333, 0.91667],
                            [0.00000, 0.08333, 0.91667],
                            [0.00000, 0.08333, 0.91667],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.91667, 0.08333],
                            [0.00000, 0.50000, 0.50000],
                            [0.00000, 0.50000, 0.50000],
                            [0.00000, 0.50000, 0.50000],
                            [0.00000, 0.50000, 0.50000],
                            [0.00000, 0.50000, 0.50000],
                            [0.00000, 0.50000, 0.50000],
                            [0.00000, 0.50000, 0.50000],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.00000, 0.00000, 1.00000],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.00000, 0.91667],
                            [0.08333, 0.91667, 0.00000],
                            [0.08333, 0.91667, 0.00000],
                            [0.08333, 0.91667, 0.00000]])

        self.assertEqual(output.shape, selmask.shape)
        self.assertTrue(np.allclose(output, selmask, 0.001))

        # test single factor, get max factor in linear weight, threshold 0.2
        stg_pars = (False, 'even', 'greater', 0.2, 0.2, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'even'
        stg.condition = 'greater'
        stg.lbound = 0.2
        stg.ubound = 0.2
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=history_data, shares=self.hp1.shares, dates=self.hp1.hdates)
        selmask = np.array([[0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.5, 0.5],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.0, 0.0, 1.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0],
                            [0.5, 0.5, 0.0]])

        self.assertEqual(output.shape, selmask.shape)
        self.assertTrue(np.allclose(output, selmask, 0.001))

    def test_tokenizer(self):
        self.assertListEqual(_exp_to_token('1+1'),
                             ['1', '+', '1'])
        print(_exp_to_token('1+1'))
        self.assertListEqual(_exp_to_token('1 & 1'),
                             ['1', '&', '1'])
        print(_exp_to_token('1&1'))
        self.assertListEqual(_exp_to_token('1 and 1'),
                             ['1', 'and', '1'])
        print(_exp_to_token('1 and 1'))
        self.assertListEqual(_exp_to_token('1 or 1'),
                             ['1', 'or', '1'])
        print(_exp_to_token('1 or 1'))
        self.assertListEqual(_exp_to_token('(1 - 1 + -1) * pi'),
                             ['(', '1', '-', '1', '+', '-1', ')', '*', 'pi'])
        print(_exp_to_token('(1 - 1 + -1) * pi'))
        self.assertListEqual(_exp_to_token('abs(5-sqrt(2) /  cos(pi))'),
                             ['abs(', '5', '-', 'sqrt(', '2', ')', '/', 'cos(', 'pi', ')', ')'])
        print(_exp_to_token('abs(5-sqrt(2) /  cos(pi))'))
        self.assertListEqual(_exp_to_token('sin(pi) + 2.14'),
                             ['sin(', 'pi', ')', '+', '2.14'])
        print(_exp_to_token('sin(pi) + 2.14'))
        self.assertListEqual(_exp_to_token('(1-2)/3.0 + 0.0000'),
                             ['(', '1', '-', '2', ')', '/', '3.0', '+', '0.0000'])
        print(_exp_to_token('(1-2)/3.0 + 0.0000'))
        self.assertListEqual(_exp_to_token('-(1. + .2) * max(1, 3, 5)'),
                             ['-', '(', '1.', '+', '.2', ')', '*', 'max(', '1', ',', '3', ',', '5', ')'])
        print(_exp_to_token('-(1. + .2) * max(1, 3, 5)'))
        self.assertListEqual(_exp_to_token('(x + e * 10) / 10'),
                             ['(', 'x', '+', 'e', '*', '10', ')', '/', '10'])
        print(_exp_to_token('(x + e * 10) / 10'))
        self.assertListEqual(_exp_to_token('8.2/((-.1+abs3(3,4,5))*0.12)'),
                             ['8.2', '/', '(', '(', '-.1', '+', 'abs3(', '3', ',', '4', ',', '5', ')', ')', '*', '0.12',
                              ')'])
        print(_exp_to_token('8.2/((-.1+abs3(3,4,5))*0.12)'))
        self.assertListEqual(_exp_to_token('8.2/abs3(3,4,25.34 + 5)*0.12'),
                             ['8.2', '/', 'abs3(', '3', ',', '4', ',', '25.34', '+', '5', ')', '*', '0.12'])
        print(_exp_to_token('8.2/abs3(3,4,25.34 + 5)*0.12'))


class TestLog(unittest.TestCase):
    def test_init(self):
        pass


class TestConfig(unittest.TestCase):
    """测试Config对象以及QT_CONFIG变量的设置和获取值"""

    def test_init(self):
        pass

    def test_invest(self):
        pass

    def test_pars_string_to_type(self):
        _parse_string_kwargs('000300', 'asset_pool', _valid_qt_kwargs())


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

    def test_properties(self):
        """ test all properties of HistoryPanel
        """
        self.assertFalse(self.hp.is_empty)
        self.assertEqual(self.hp.row_count, 10)
        self.assertEqual(self.hp.column_count, 4)
        self.assertEqual(self.hp.level_count, 5)
        self.assertEqual(self.hp.shape, (5, 10, 4))
        self.assertSequenceEqual(self.hp.htypes, ['close', 'open', 'high', 'low'])
        self.assertSequenceEqual(self.hp.shares, ['000100', '000101', '000102', '000103', '000104'])
        self.assertSequenceEqual(list(self.hp.hdates), list(self.index))
        self.assertDictEqual(self.hp.columns, {'close': 0, 'open': 1, 'high': 2, 'low': 3})
        self.assertDictEqual(self.hp.levels, {'000100': 0, '000101': 1, '000102': 2, '000103': 3, '000104': 4})
        row_dict = {Timestamp('2020-01-01 00:00:00', freq='D'): 0,
                    Timestamp('2020-01-02 00:00:00', freq='D'): 1,
                    Timestamp('2020-01-03 00:00:00', freq='D'): 2,
                    Timestamp('2020-01-04 00:00:00', freq='D'): 3,
                    Timestamp('2020-01-05 00:00:00', freq='D'): 4,
                    Timestamp('2020-01-06 00:00:00', freq='D'): 5,
                    Timestamp('2020-01-07 00:00:00', freq='D'): 6,
                    Timestamp('2020-01-08 00:00:00', freq='D'): 7,
                    Timestamp('2020-01-09 00:00:00', freq='D'): 8,
                    Timestamp('2020-01-10 00:00:00', freq='D'): 9}
        self.assertDictEqual(self.hp.rows, row_dict)

    def test_len(self):
        """ test the function len(HistoryPanel)

        :return:
        """
        self.assertEqual(len(self.hp), 10)

    def test_empty_history_panel(self):
        """测试空HP或者特殊HP如维度标签为纯数字的HP"""
        test_hp = qt.HistoryPanel(self.data)
        self.assertFalse(test_hp.is_empty)
        self.assertIsInstance(test_hp, qt.HistoryPanel)
        self.assertEqual(test_hp.shape[0], 5)
        self.assertEqual(test_hp.shape[1], 10)
        self.assertEqual(test_hp.shape[2], 4)
        self.assertEqual(test_hp.level_count, 5)
        self.assertEqual(test_hp.row_count, 10)
        self.assertEqual(test_hp.column_count, 4)
        self.assertEqual(test_hp.shares, list(range(5)))
        self.assertEqual(test_hp.hdates, list(pd.date_range(start='20200730', periods=10, freq='d')))
        self.assertEqual(test_hp.htypes, list(range(4)))
        self.assertTrue(np.allclose(test_hp.values, self.data))
        print(f'shares: {test_hp.shares}\nhtypes: {test_hp.htypes}')
        print(test_hp)

        # HistoryPanel should be empty if no value is given
        empty_hp = qt.HistoryPanel()
        self.assertTrue(empty_hp.is_empty)
        self.assertIsInstance(empty_hp, qt.HistoryPanel)
        self.assertEqual(empty_hp.shape[0], 0)
        self.assertEqual(empty_hp.shape[1], 0)
        self.assertEqual(empty_hp.shape[2], 0)
        self.assertEqual(empty_hp.level_count, 0)
        self.assertEqual(empty_hp.row_count, 0)
        self.assertEqual(empty_hp.column_count, 0)

        # HistoryPanel should also be empty if empty value (np.array([])) is given
        empty_hp = qt.HistoryPanel(np.empty((5, 0, 4)), levels=self.shares, columns=self.htypes)
        self.assertTrue(empty_hp.is_empty)
        self.assertIsInstance(empty_hp, qt.HistoryPanel)
        self.assertEqual(empty_hp.shape[0], 0)
        self.assertEqual(empty_hp.shape[1], 0)
        self.assertEqual(empty_hp.shape[2], 0)
        self.assertEqual(empty_hp.level_count, 0)
        self.assertEqual(empty_hp.row_count, 0)
        self.assertEqual(empty_hp.column_count, 0)

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

        print('test creating HistoryPanel with very limited data')
        print('test creating HistoryPanel with 2D data')
        temp_data = np.random.randint(10, size=(7, 3)).astype('float')
        temp_hp = qt.HistoryPanel(temp_data)

        # Error testing during HistoryPanel creating
        # shape does not match
        self.assertRaises(AssertionError,
                          qt.HistoryPanel,
                          self.data,
                          levels=self.shares, columns='close', rows=self.index)
        # valus is not np.ndarray
        self.assertRaises(TypeError,
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
        """测试HistoryPanel的各种切片方法
        包括通过标签名称切片，通过数字切片，通过逗号分隔的标签名称切片，通过冒号分隔的标签名称切片等切片方式"""
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

    def test_segment(self):
        """测试历史数据片段的获取"""
        test_hp = qt.HistoryPanel(self.data,
                                  levels=self.shares,
                                  columns=self.htypes,
                                  rows=self.index2)
        self.assertFalse(test_hp.is_empty)
        self.assertIsInstance(test_hp, qt.HistoryPanel)
        self.assertEqual(test_hp.shape[0], 5)
        self.assertEqual(test_hp.shape[1], 10)
        self.assertEqual(test_hp.shape[2], 4)
        print(f'Test segment with None parameters')
        seg1 = test_hp.segment()
        seg2 = test_hp.segment('20150202')
        seg3 = test_hp.segment(end_date='20201010')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        self.assertIsInstance(seg2, qt.HistoryPanel)
        self.assertIsInstance(seg3, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp.values
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp.values
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp.values
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        self.assertEqual(seg2.htypes, test_hp.htypes)
        self.assertEqual(seg2.shares, test_hp.shares)
        self.assertEqual(seg3.htypes, test_hp.htypes)
        self.assertEqual(seg3.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)
        self.assertEqual(seg2.hdates, test_hp.hdates)
        self.assertEqual(seg3.hdates, test_hp.hdates)

        print(f'Test segment with proper dates')
        seg1 = test_hp.segment()
        seg2 = test_hp.segment('20160704')
        seg3 = test_hp.segment(start_date='2016-07-05',
                               end_date='20160708')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        self.assertIsInstance(seg2, qt.HistoryPanel)
        self.assertIsInstance(seg3, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp[:, :, :]
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp[:, :, 1:10]
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp[:, :, 2:6]
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        self.assertEqual(seg2.htypes, test_hp.htypes)
        self.assertEqual(seg2.shares, test_hp.shares)
        self.assertEqual(seg3.htypes, test_hp.htypes)
        self.assertEqual(seg3.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)
        self.assertEqual(seg2.hdates, test_hp.hdates[1:10])
        self.assertEqual(seg3.hdates, test_hp.hdates[2:6])

        print(f'Test segment with non-existing but in range dates')
        seg1 = test_hp.segment()
        seg2 = test_hp.segment('20160703')
        seg3 = test_hp.segment(start_date='2016-07-03',
                               end_date='20160710')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        self.assertIsInstance(seg2, qt.HistoryPanel)
        self.assertIsInstance(seg3, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp[:, :, :]
        ))
        self.assertTrue(np.allclose(
                seg2.values, test_hp[:, :, 1:10]
        ))
        self.assertTrue(np.allclose(
                seg3.values, test_hp[:, :, 1:6]
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        self.assertEqual(seg2.htypes, test_hp.htypes)
        self.assertEqual(seg2.shares, test_hp.shares)
        self.assertEqual(seg3.htypes, test_hp.htypes)
        self.assertEqual(seg3.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)
        self.assertEqual(seg2.hdates, test_hp.hdates[1:10])
        self.assertEqual(seg3.hdates, test_hp.hdates[1:6])

        print(f'Test segment with out-of-range dates')
        seg1 = test_hp.segment(start_date='2016-05-03',
                               end_date='20160910')
        self.assertIsInstance(seg1, qt.HistoryPanel)
        # check values
        self.assertTrue(np.allclose(
                seg1.values, test_hp[:, :, :]
        ))
        # check that htypes and shares should be same
        self.assertEqual(seg1.htypes, test_hp.htypes)
        self.assertEqual(seg1.shares, test_hp.shares)
        # check that hdates are the same
        self.assertEqual(seg1.hdates, test_hp.hdates)

    def test_slice(self):
        """测试历史数据切片的获取"""
        test_hp = qt.HistoryPanel(self.data,
                                  levels=self.shares,
                                  columns=self.htypes,
                                  rows=self.index2)
        self.assertFalse(test_hp.is_empty)
        self.assertIsInstance(test_hp, qt.HistoryPanel)
        self.assertEqual(test_hp.shape[0], 5)
        self.assertEqual(test_hp.shape[1], 10)
        self.assertEqual(test_hp.shape[2], 4)
        print(f'Test slice with shares')
        share = '000101'
        slc = test_hp.slice(shares=share)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000101'])
        self.assertEqual(slc.htypes, test_hp.htypes)
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp[:, '000101']))

        share = '000101, 000103'
        slc = test_hp.slice(shares=share)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000101', '000103'])
        self.assertEqual(slc.htypes, test_hp.htypes)
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp[:, '000101, 000103']))

        print(f'Test slice with htypes')
        htype = 'open'
        slc = test_hp.slice(htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, test_hp.shares)
        self.assertEqual(slc.htypes, ['open'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['open']))

        htype = 'open, close'
        slc = test_hp.slice(htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, test_hp.shares)
        self.assertEqual(slc.htypes, ['open', 'close'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['open, close']))
        # test that slicing of "open, close" does NOT equal to "close, open"
        self.assertFalse(np.allclose(slc.values, test_hp['close, open']))

        print(f'Test slicing with both htypes and shares')
        share = '000103, 000101'
        htype = 'high, low, close'
        slc = test_hp.slice(shares=share, htypes=htype)
        self.assertIsInstance(slc, qt.HistoryPanel)
        self.assertEqual(slc.shares, ['000103', '000101'])
        self.assertEqual(slc.htypes, ['high', 'low', 'close'])
        self.assertEqual(slc.hdates, test_hp.hdates)
        self.assertTrue(np.allclose(slc.values, test_hp['high, low, close', '000103, 000101']))

        print(f'Test Error cases')
        # duplicated input
        htype = 'open, close, open'
        self.assertRaises(AssertionError, test_hp.slice, htypes=htype)

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
        # TODO: 这里需要加强，需要用具体的例子确认hp_join的结果正确
        # TODO: 尤其是不同的shares、htypes、hdates，以及它们在顺
        # TODO: 序不同的情况下是否能正确地组合
        print(f'join two simple HistoryPanels with same shares')
        temp_hp = self.hp.join(self.hp2, same_shares=True)
        self.assertIsInstance(temp_hp, qt.HistoryPanel)

    def test_df_to_hp(self):
        print(f'test converting DataFrame to HistoryPanel')
        data = np.random.randint(10, size=(10, 5))
        df1 = pd.DataFrame(data)
        df2 = pd.DataFrame(data, columns=str_to_list(self.shares))
        df3 = pd.DataFrame(data[:, 0:4])
        df4 = pd.DataFrame(data[:, 0:4], columns=str_to_list(self.htypes))
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
        self.assertEqual(hp.shares, str_to_list(self.shares))
        self.assertEqual(hp.htypes, ['close'])
        hp = qt.dataframe_to_hp(df3, shares='000100', column_type='htypes')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, ['000100'])
        self.assertEqual(hp.htypes, [0, 1, 2, 3])
        hp = qt.dataframe_to_hp(df4, shares='000100', htypes=self.htypes, column_type='htypes')
        self.assertIsInstance(hp, qt.HistoryPanel)
        self.assertEqual(hp.shares, ['000100'])
        self.assertEqual(hp.htypes, str_to_list(self.htypes))
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
        values = df_test.values
        self.assertTrue(np.allclose(self.hp[:, '000102'], values))

        print(f'test DataFrame conversion with share == "000100"')
        df_test = self.hp.to_dataframe(share='000100')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.htypes), list(df_test.columns))
        values = df_test.values
        self.assertTrue(np.allclose(self.hp[:, '000100'], values))

        print(f'test DataFrame conversion error: type incorrect')
        self.assertRaises(AssertionError, self.hp.to_dataframe, share=3.0)

        print(f'test DataFrame error raising with share not found error')
        self.assertRaises(KeyError, self.hp.to_dataframe, share='000300')

        print(f'test DataFrame conversion with htype == "close"')
        df_test = self.hp.to_dataframe(htype='close')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        self.assertTrue(np.allclose(self.hp['close'].T, values))

        print(f'test DataFrame conversion with htype == "high"')
        df_test = self.hp.to_dataframe(htype='high')
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        self.assertTrue(np.allclose(self.hp['high'].T, values))

        print(f'test DataFrame conversion with htype == "high" and dropna')
        v = self.hp.values.astype('float')
        v[:, 3, :] = np.nan
        v[:, 4, :] = np.inf
        test_hp = qt.HistoryPanel(v, levels=self.shares, columns=self.htypes, rows=self.index)
        df_test = test_hp.to_dataframe(htype='high', dropna=True)
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates[:3]) + list(self.hp.hdates[4:]), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        target_values = test_hp['high'].T
        target_values = target_values[np.where(~np.isnan(target_values))].reshape(9, 5)
        self.assertTrue(np.allclose(target_values, values))

        print(f'test DataFrame conversion with htype == "high", dropna and treat infs as na')
        v = self.hp.values.astype('float')
        v[:, 3, :] = np.nan
        v[:, 4, :] = np.inf
        test_hp = qt.HistoryPanel(v, levels=self.shares, columns=self.htypes, rows=self.index)
        df_test = test_hp.to_dataframe(htype='high', dropna=True, inf_as_na=True)
        self.assertIsInstance(df_test, pd.DataFrame)
        self.assertEqual(list(self.hp.hdates[:3]) + list(self.hp.hdates[5:]), list(df_test.index))
        self.assertEqual(list(self.hp.shares), list(df_test.columns))
        values = df_test.values
        target_values = test_hp['high'].T
        target_values = target_values[np.where(~np.isnan(target_values) & ~np.isinf(target_values))].reshape(8, 5)
        self.assertTrue(np.allclose(target_values, values))

        print(f'test DataFrame conversion error: type incorrect')
        self.assertRaises(AssertionError, self.hp.to_dataframe, htype=pd.DataFrame())

        print(f'test DataFrame error raising with share not found error')
        self.assertRaises(KeyError, self.hp.to_dataframe, htype='non_type')

        print(f'Raises ValueError when both or none parameter is given')
        self.assertRaises(KeyError, self.hp.to_dataframe)
        self.assertRaises(KeyError, self.hp.to_dataframe, share='000100', htype='close')

    def test_to_df_dict(self):
        """测试HistoryPanel公有方法to_df_dict"""

        print('test convert history panel slice by share')
        df_dict = self.hp.to_df_dict('share')
        self.assertEqual(self.hp.shares, list(df_dict.keys()))
        df_dict = self.hp.to_df_dict()
        self.assertEqual(self.hp.shares, list(df_dict.keys()))

        print('test convert historypanel slice by htype ')
        df_dict = self.hp.to_df_dict('htype')
        self.assertEqual(self.hp.htypes, list(df_dict.keys()))

        print('test raise assertion error')
        self.assertRaises(AssertionError, self.hp.to_df_dict, by='random text')
        self.assertRaises(AssertionError, self.hp.to_df_dict, by=3)

        print('test empty hp')
        df_dict = qt.HistoryPanel().to_df_dict('share')
        self.assertEqual(df_dict, {})

    def test_stack_dataframes(self):
        print('test stack dataframes in a list')
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

        hp1 = stack_dataframes([df1, df2, df3], stack_along='shares',
                               shares=['000100', '000200', '000300'])
        hp2 = stack_dataframes([df1, df2, df3], stack_along='shares',
                               shares='000100, 000300, 000200')
        print('hp1 is:\n', hp1)
        print('hp2 is:\n', hp2)
        self.assertEqual(hp1.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp1.shares, ['000100', '000200', '000300'])
        self.assertTrue(np.allclose(hp1.values, values1, equal_nan=True))
        self.assertEqual(hp2.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp2.shares, ['000100', '000300', '000200'])
        self.assertTrue(np.allclose(hp2.values, values1, equal_nan=True))

        hp3 = stack_dataframes([df1, df2, df3], stack_along='htypes',
                               htypes=['close', 'high', 'low'])
        hp4 = stack_dataframes([df1, df2, df3], stack_along='htypes',
                               htypes='open, close, high')
        print('hp3 is:\n', hp3.values)
        print('hp4 is:\n', hp4.values)
        self.assertEqual(hp3.htypes, ['close', 'high', 'low'])
        self.assertEqual(hp3.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp3.values, values2, equal_nan=True))
        self.assertEqual(hp4.htypes, ['open', 'close', 'high'])
        self.assertEqual(hp4.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp4.values, values2, equal_nan=True))

        print('test stack dataframes in a dict')
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

        hp1 = stack_dataframes(dfs={'000001.SZ': df1, '000002.SZ': df2, '000003.SZ': df3},
                               stack_along='shares')
        hp2 = stack_dataframes(dfs={'000001.SZ': df1, '000002.SZ': df2, '000003.SZ': df3},
                               stack_along='shares',
                               shares='000100, 000300, 000200')
        print('hp1 is:\n', hp1)
        print('hp2 is:\n', hp2)
        self.assertEqual(hp1.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp1.shares, ['000001.SZ', '000002.SZ', '000003.SZ'])
        self.assertTrue(np.allclose(hp1.values, values1, equal_nan=True))
        self.assertEqual(hp2.htypes, ['a', 'b', 'c', 'd'])
        self.assertEqual(hp2.shares, ['000100', '000300', '000200'])
        self.assertTrue(np.allclose(hp2.values, values1, equal_nan=True))

        hp3 = stack_dataframes(dfs={'close': df1, 'high': df2, 'low': df3},
                               stack_along='htypes')
        hp4 = stack_dataframes(dfs={'close': df1, 'low': df2, 'high': df3},
                               stack_along='htypes',
                               htypes='open, close, high')
        print('hp3 is:\n', hp3.values)
        print('hp4 is:\n', hp4.values)
        self.assertEqual(hp3.htypes, ['close', 'high', 'low'])
        self.assertEqual(hp3.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp3.values, values2, equal_nan=True))
        self.assertEqual(hp4.htypes, ['open', 'close', 'high'])
        self.assertEqual(hp4.shares, ['a', 'b', 'c', 'd'])
        self.assertTrue(np.allclose(hp4.values, values2, equal_nan=True))

    def test_to_csv(self):
        pass

    def test_to_hdf(self):
        pass

    def test_fill_na(self):
        """测试填充无效值"""
        print(self.hp)
        new_values = self.hp.values.astype(float)
        new_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = np.nan
        print(new_values)
        temp_hp = qt.HistoryPanel(values=new_values, levels=self.hp.levels, rows=self.hp.rows, columns=self.hp.columns)
        self.assertTrue(np.allclose(temp_hp.values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]], np.nan, equal_nan=True))
        temp_hp.fillna(2.3)
        filled_values = new_values.copy()
        filled_values[[0, 1, 3, 2], [1, 3, 0, 2], [1, 3, 2, 2]] = 2.3
        self.assertTrue(np.allclose(temp_hp.values,
                                    filled_values, equal_nan=True))

    def test_fill_inf(self):
        """测试填充无限值"""

    def test_get_history_panel(self):
        # TODO: implement this test case
        # test get only one line of data
        pass

    def test_get_price_type_raw_data(self):
        shares = '000039.SZ, 600748.SH, 000040.SZ'
        start = '20200101'
        end = '20200131'
        htypes = 'open, high, low, close'

        target_price_000039 = [[9.45, 9.49, 9.12, 9.17],
                               [9.46, 9.56, 9.4, 9.5],
                               [9.7, 9.76, 9.5, 9.51],
                               [9.7, 9.75, 9.7, 9.72],
                               [9.73, 9.77, 9.7, 9.73],
                               [9.83, 9.85, 9.71, 9.72],
                               [9.85, 9.85, 9.75, 9.79],
                               [9.96, 9.96, 9.83, 9.86],
                               [9.87, 9.94, 9.77, 9.93],
                               [9.82, 9.9, 9.76, 9.87],
                               [9.8, 9.85, 9.77, 9.82],
                               [9.84, 9.86, 9.71, 9.72],
                               [9.83, 9.93, 9.81, 9.86],
                               [9.7, 9.87, 9.7, 9.82],
                               [9.83, 9.86, 9.69, 9.79],
                               [9.8, 9.94, 9.8, 9.86]]

        target_price_600748 = [[5.68, 5.68, 5.32, 5.37],
                               [5.62, 5.68, 5.46, 5.65],
                               [5.72, 5.72, 5.61, 5.62],
                               [5.76, 5.77, 5.6, 5.73],
                               [5.78, 5.84, 5.73, 5.75],
                               [5.89, 5.91, 5.76, 5.77],
                               [6.03, 6.04, 5.87, 5.89],
                               [5.94, 6.07, 5.94, 6.02],
                               [5.96, 5.98, 5.88, 5.97],
                               [6.04, 6.06, 5.95, 5.96],
                               [5.98, 6.04, 5.96, 6.03],
                               [6.1, 6.11, 5.89, 5.94],
                               [6.02, 6.12, 6., 6.1],
                               [5.96, 6.05, 5.88, 6.01],
                               [6.03, 6.03, 5.95, 5.99],
                               [6.02, 6.12, 5.99, 5.99]]

        target_price_000040 = [[3.63, 3.83, 3.63, 3.65],
                               [3.99, 4.07, 3.97, 4.03],
                               [4.1, 4.11, 3.93, 3.95],
                               [4.12, 4.13, 4.06, 4.11],
                               [4.13, 4.19, 4.07, 4.13],
                               [4.27, 4.28, 4.11, 4.12],
                               [4.37, 4.38, 4.25, 4.29],
                               [4.34, 4.5, 4.32, 4.41],
                               [4.28, 4.35, 4.2, 4.34],
                               [4.41, 4.43, 4.29, 4.31],
                               [4.42, 4.45, 4.36, 4.41],
                               [4.51, 4.56, 4.33, 4.35],
                               [4.35, 4.55, 4.31, 4.55],
                               [4.3, 4.41, 4.22, 4.36],
                               [4.27, 4.44, 4.23, 4.34],
                               [4.23, 4.27, 4.18, 4.25]]

        print(f'test get price type raw data with single thread')
        df_list = get_price_type_raw_data(start=start, end=end, shares=shares, htypes=htypes, freq='d')
        self.assertIsInstance(df_list, dict)
        self.assertEqual(len(df_list), 3)
        self.assertTrue(np.allclose(df_list['000039.SZ'].values, np.array(target_price_000039)))
        self.assertTrue(np.allclose(df_list['600748.SH'].values, np.array(target_price_600748)))
        self.assertTrue(np.allclose(df_list['000040.SZ'].values, np.array(target_price_000040)))
        print(f'in get financial report type raw data, got DataFrames: \n"000039.SZ":\n'
              f'{df_list["000039.SZ"]}\n"600748.SH":\n'
              f'{df_list["600748.SH"]}\n"000040.SZ":\n{df_list["000040.SZ"]}')

        print(f'test get price type raw data with with multi threads')
        df_list = get_price_type_raw_data(start=start, end=end, shares=shares, htypes=htypes, freq='d', parallel=10)
        self.assertIsInstance(df_list, dict)
        self.assertEqual(len(df_list), 3)
        self.assertTrue(np.allclose(df_list['000039.SZ'].values, np.array(target_price_000039)))
        self.assertTrue(np.allclose(df_list['600748.SH'].values, np.array(target_price_600748)))
        self.assertTrue(np.allclose(df_list['000040.SZ'].values, np.array(target_price_000040)))
        print(f'in get financial report type raw data, got DataFrames: \n"000039.SZ":\n'
              f'{df_list["000039.SZ"]}\n"600748.SH":\n'
              f'{df_list["600748.SH"]}\n"000040.SZ":\n{df_list["000040.SZ"]}')

    def test_get_financial_report_type_raw_data(self):
        shares = '000039.SZ, 600748.SH, 000040.SZ'
        start = '20160101'
        end = '20201231'
        htypes = 'eps,basic_eps,diluted_eps,total_revenue,revenue,total_share,' \
                 'cap_rese,undistr_porfit,surplus_rese,net_profit'

        target_eps_000039 = [[1.41],
                             [0.1398],
                             [-0.0841],
                             [-0.1929],
                             [0.37],
                             [0.1357],
                             [0.1618],
                             [0.1191],
                             [1.11],
                             [0.759],
                             [0.3061],
                             [0.1409],
                             [0.81],
                             [0.4187],
                             [0.2554],
                             [0.1624],
                             [0.14],
                             [-0.0898],
                             [-0.1444],
                             [0.1291]]
        target_eps_600748 = [[0.41],
                             [0.22],
                             [0.22],
                             [0.09],
                             [0.42],
                             [0.23],
                             [0.22],
                             [0.09],
                             [0.36],
                             [0.16],
                             [0.15],
                             [0.07],
                             [0.47],
                             [0.19],
                             [0.12],
                             [0.07],
                             [0.32],
                             [0.22],
                             [0.14],
                             [0.07]]
        target_eps_000040 = [[-0.6866],
                             [-0.134],
                             [-0.189],
                             [-0.036],
                             [-0.6435],
                             [0.05],
                             [0.062],
                             [0.0125],
                             [0.8282],
                             [1.05],
                             [0.985],
                             [0.811],
                             [0.41],
                             [0.242],
                             [0.113],
                             [0.027],
                             [0.19],
                             [0.17],
                             [0.17],
                             [0.064]]

        target_basic_eps_000039 = [[1.3980000e-01, 1.3980000e-01, 6.3591954e+10, 6.3591954e+10],
                                   [-8.4100000e-02, -8.4100000e-02, 3.9431807e+10, 3.9431807e+10],
                                   [-1.9290000e-01, -1.9290000e-01, 1.5852177e+10, 1.5852177e+10],
                                   [3.7000000e-01, 3.7000000e-01, 8.5815341e+10, 8.5815341e+10],
                                   [1.3570000e-01, 1.3430000e-01, 6.1660271e+10, 6.1660271e+10],
                                   [1.6180000e-01, 1.6040000e-01, 4.2717729e+10, 4.2717729e+10],
                                   [1.1910000e-01, 1.1900000e-01, 1.9099547e+10, 1.9099547e+10],
                                   [1.1100000e+00, 1.1000000e+00, 9.3497622e+10, 9.3497622e+10],
                                   [7.5900000e-01, 7.5610000e-01, 6.6906147e+10, 6.6906147e+10],
                                   [3.0610000e-01, 3.0380000e-01, 4.3560398e+10, 4.3560398e+10],
                                   [1.4090000e-01, 1.4050000e-01, 1.9253639e+10, 1.9253639e+10],
                                   [8.1000000e-01, 8.1000000e-01, 7.6299930e+10, 7.6299930e+10],
                                   [4.1870000e-01, 4.1710000e-01, 5.3962706e+10, 5.3962706e+10],
                                   [2.5540000e-01, 2.5440000e-01, 3.3387152e+10, 3.3387152e+10],
                                   [1.6240000e-01, 1.6200000e-01, 1.4675987e+10, 1.4675987e+10],
                                   [1.4000000e-01, 1.4000000e-01, 5.1111652e+10, 5.1111652e+10],
                                   [-8.9800000e-02, -8.9800000e-02, 3.4982614e+10, 3.4982614e+10],
                                   [-1.4440000e-01, -1.4440000e-01, 2.3542843e+10, 2.3542843e+10],
                                   [1.2910000e-01, 1.2860000e-01, 1.0412416e+10, 1.0412416e+10],
                                   [7.2000000e-01, 7.1000000e-01, 5.8685804e+10, 5.8685804e+10]]
        target_basic_eps_600748 = [[2.20000000e-01, 2.20000000e-01, 5.29423397e+09, 5.29423397e+09],
                                   [2.20000000e-01, 2.20000000e-01, 4.49275653e+09, 4.49275653e+09],
                                   [9.00000000e-02, 9.00000000e-02, 1.59067065e+09, 1.59067065e+09],
                                   [4.20000000e-01, 4.20000000e-01, 8.86555586e+09, 8.86555586e+09],
                                   [2.30000000e-01, 2.30000000e-01, 5.44850143e+09, 5.44850143e+09],
                                   [2.20000000e-01, 2.20000000e-01, 4.34978927e+09, 4.34978927e+09],
                                   [9.00000000e-02, 9.00000000e-02, 1.73793793e+09, 1.73793793e+09],
                                   [3.60000000e-01, 3.60000000e-01, 8.66375241e+09, 8.66375241e+09],
                                   [1.60000000e-01, 1.60000000e-01, 4.72875116e+09, 4.72875116e+09],
                                   [1.50000000e-01, 1.50000000e-01, 3.76879016e+09, 3.76879016e+09],
                                   [7.00000000e-02, 7.00000000e-02, 1.31785454e+09, 1.31785454e+09],
                                   [4.70000000e-01, 4.70000000e-01, 7.23391685e+09, 7.23391685e+09],
                                   [1.90000000e-01, 1.90000000e-01, 3.76072215e+09, 3.76072215e+09],
                                   [1.20000000e-01, 1.20000000e-01, 2.35845364e+09, 2.35845364e+09],
                                   [7.00000000e-02, 7.00000000e-02, 1.03831865e+09, 1.03831865e+09],
                                   [3.20000000e-01, 3.20000000e-01, 6.48880919e+09, 6.48880919e+09],
                                   [2.20000000e-01, 2.20000000e-01, 3.72209142e+09, 3.72209142e+09],
                                   [1.40000000e-01, 1.40000000e-01, 2.22563924e+09, 2.22563924e+09],
                                   [7.00000000e-02, 7.00000000e-02, 8.96647052e+08, 8.96647052e+08],
                                   [4.80000000e-01, 4.80000000e-01, 6.61917508e+09, 6.61917508e+09]]
        target_basic_eps_000040 = [[-1.34000000e-01, -1.34000000e-01, 2.50438755e+09, 2.50438755e+09],
                                   [-1.89000000e-01, -1.89000000e-01, 1.32692347e+09, 1.32692347e+09],
                                   [-3.60000000e-02, -3.60000000e-02, 5.59073338e+08, 5.59073338e+08],
                                   [-6.43700000e-01, -6.43700000e-01, 6.80576162e+09, 6.80576162e+09],
                                   [5.00000000e-02, 5.00000000e-02, 6.38891620e+09, 6.38891620e+09],
                                   [6.20000000e-02, 6.20000000e-02, 5.23267082e+09, 5.23267082e+09],
                                   [1.25000000e-02, 1.25000000e-02, 2.22420874e+09, 2.22420874e+09],
                                   [8.30000000e-01, 8.30000000e-01, 8.67628947e+09, 8.67628947e+09],
                                   [1.05000000e+00, 1.05000000e+00, 5.29431716e+09, 5.29431716e+09],
                                   [9.85000000e-01, 9.85000000e-01, 3.56822382e+09, 3.56822382e+09],
                                   [8.11000000e-01, 8.11000000e-01, 1.06613439e+09, 1.06613439e+09],
                                   [4.10000000e-01, 4.10000000e-01, 8.13102532e+09, 8.13102532e+09],
                                   [2.42000000e-01, 2.42000000e-01, 5.17971521e+09, 5.17971521e+09],
                                   [1.13000000e-01, 1.13000000e-01, 3.21704120e+09, 3.21704120e+09],
                                   [2.70000000e-02, 2.70000000e-02, 8.41966738e+08, 8.24272235e+08],
                                   [1.90000000e-01, 1.90000000e-01, 3.77350171e+09, 3.77350171e+09],
                                   [1.70000000e-01, 1.70000000e-01, 2.38643892e+09, 2.38643892e+09],
                                   [1.70000000e-01, 1.70000000e-01, 1.29127117e+09, 1.29127117e+09],
                                   [6.40000000e-02, 6.40000000e-02, 6.03256858e+08, 6.03256858e+08],
                                   [1.30000000e-01, 1.30000000e-01, 1.66572918e+09, 1.66572918e+09]]

        target_total_share_000039 = [[3.5950140e+09, 4.8005360e+09, 2.1573660e+10, 3.5823430e+09],
                                     [3.5860750e+09, 4.8402300e+09, 2.0750827e+10, 3.5823430e+09],
                                     [3.5860750e+09, 4.9053550e+09, 2.0791307e+10, 3.5823430e+09],
                                     [3.5845040e+09, 4.8813110e+09, 2.1482857e+10, 3.5823430e+09],
                                     [3.5831490e+09, 4.9764250e+09, 2.0926816e+10, 3.2825850e+09],
                                     [3.5825310e+09, 4.8501270e+09, 2.1020418e+10, 3.2825850e+09],
                                     [2.9851110e+09, 5.4241420e+09, 2.2438350e+10, 3.2825850e+09],
                                     [2.9849890e+09, 4.1284000e+09, 2.2082769e+10, 3.2825850e+09],
                                     [2.9849610e+09, 4.0838010e+09, 2.1045994e+10, 3.2815350e+09],
                                     [2.9849560e+09, 4.2491510e+09, 1.9694345e+10, 3.2815350e+09],
                                     [2.9846970e+09, 4.2351600e+09, 2.0016361e+10, 3.2815350e+09],
                                     [2.9828890e+09, 4.2096630e+09, 1.9734494e+10, 3.2815350e+09],
                                     [2.9813960e+09, 3.4564240e+09, 1.8562738e+10, 3.2793790e+09],
                                     [2.9803530e+09, 3.0759650e+09, 1.8076208e+10, 3.2793790e+09],
                                     [2.9792680e+09, 3.1376690e+09, 1.7994776e+10, 3.2793790e+09],
                                     [2.9785770e+09, 3.1265850e+09, 1.7495053e+10, 3.2793790e+09],
                                     [2.9783640e+09, 3.1343850e+09, 1.6740840e+10, 3.2035780e+09],
                                     [2.9783590e+09, 3.1273880e+09, 1.6578389e+10, 3.2035780e+09],
                                     [2.9782780e+09, 3.1169280e+09, 1.8047639e+10, 3.2035780e+09],
                                     [2.9778200e+09, 3.1818630e+09, 1.7663145e+10, 3.2035780e+09]]
        target_total_share_600748 = [[1.84456289e+09, 2.60058426e+09, 5.72443733e+09, 4.58026529e+08],
                                     [1.84456289e+09, 2.60058426e+09, 5.72096899e+09, 4.58026529e+08],
                                     [1.84456289e+09, 2.60058426e+09, 5.65738237e+09, 4.58026529e+08],
                                     [1.84456289e+09, 2.60058426e+09, 5.50257806e+09, 4.58026529e+08],
                                     [1.84456289e+09, 2.59868164e+09, 5.16741523e+09, 4.44998882e+08],
                                     [1.84456289e+09, 2.59684471e+09, 5.14677280e+09, 4.44998882e+08],
                                     [1.84456289e+09, 2.59684471e+09, 4.94955591e+09, 4.44998882e+08],
                                     [1.84456289e+09, 2.59684471e+09, 4.79001451e+09, 4.44998882e+08],
                                     [1.84456289e+09, 3.11401684e+09, 4.46326988e+09, 4.01064256e+08],
                                     [1.84456289e+09, 3.11596723e+09, 4.45419136e+09, 4.01064256e+08],
                                     [1.84456289e+09, 3.11596723e+09, 4.39652948e+09, 4.01064256e+08],
                                     [1.84456289e+09, 3.18007783e+09, 4.26608403e+09, 4.01064256e+08],
                                     [1.84456289e+09, 3.10935622e+09, 3.78417688e+09, 3.65651701e+08],
                                     [1.84456289e+09, 3.10935622e+09, 3.65806574e+09, 3.65651701e+08],
                                     [1.84456289e+09, 3.10935622e+09, 3.62063090e+09, 3.65651701e+08],
                                     [1.84456289e+09, 3.10935622e+09, 3.50063915e+09, 3.65651701e+08],
                                     [1.41889453e+09, 3.55940850e+09, 3.22272993e+09, 3.62124939e+08],
                                     [1.41889453e+09, 3.56129650e+09, 3.11477476e+09, 3.62124939e+08],
                                     [1.41889453e+09, 3.59632888e+09, 3.06836903e+09, 3.62124939e+08],
                                     [1.08337087e+09, 3.37400726e+07, 3.00918704e+09, 3.62124939e+08]]
        target_total_share_000040 = [[1.48687387e+09, 1.06757900e+10, 8.31900755e+08, 2.16091994e+08],
                                     [1.48687387e+09, 1.06757900e+10, 7.50177302e+08, 2.16091994e+08],
                                     [1.48687387e+09, 1.06757899e+10, 9.90255974e+08, 2.16123282e+08],
                                     [1.48687387e+09, 1.06757899e+10, 1.03109866e+09, 2.16091994e+08],
                                     [1.48687387e+09, 1.06757910e+10, 2.07704745e+09, 2.16123282e+08],
                                     [1.48687387e+09, 1.06757910e+10, 2.09608665e+09, 2.16123282e+08],
                                     [1.48687387e+09, 1.06803833e+10, 2.13354083e+09, 2.16123282e+08],
                                     [1.48687387e+09, 1.06804090e+10, 2.11489364e+09, 2.16123282e+08],
                                     [1.33717327e+09, 8.87361727e+09, 2.42939924e+09, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 2.34220254e+09, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 2.16390368e+09, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 1.07961915e+09, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 8.58866066e+08, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 6.87024393e+08, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 5.71554565e+08, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361727e+09, 5.54241222e+08, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361726e+09, 5.10059576e+08, 1.88489589e+08],
                                     [1.33717327e+09, 8.87361726e+09, 4.59351639e+08, 1.88489589e+08],
                                     [4.69593364e+08, 2.78355875e+08, 4.13430814e+08, 1.88489589e+08],
                                     [4.69593364e+08, 2.74235459e+08, 3.83557678e+08, 1.88489589e+08]]

        target_net_profit_000039 = [[np.nan],
                                    [2.422180e+08],
                                    [np.nan],
                                    [2.510113e+09],
                                    [np.nan],
                                    [1.102220e+09],
                                    [np.nan],
                                    [4.068455e+09],
                                    [np.nan],
                                    [1.315957e+09],
                                    [np.nan],
                                    [3.158415e+09],
                                    [np.nan],
                                    [1.066509e+09],
                                    [np.nan],
                                    [7.349830e+08],
                                    [np.nan],
                                    [-5.411600e+08],
                                    [np.nan],
                                    [2.271961e+09]]
        target_net_profit_600748 = [[np.nan],
                                    [4.54341757e+08],
                                    [np.nan],
                                    [9.14476670e+08],
                                    [np.nan],
                                    [5.25360283e+08],
                                    [np.nan],
                                    [9.24502415e+08],
                                    [np.nan],
                                    [4.66560302e+08],
                                    [np.nan],
                                    [9.15265285e+08],
                                    [np.nan],
                                    [2.14639674e+08],
                                    [np.nan],
                                    [7.45093049e+08],
                                    [np.nan],
                                    [2.10967312e+08],
                                    [np.nan],
                                    [6.04572711e+08]]
        target_net_profit_000040 = [[np.nan],
                                    [-2.82458846e+08],
                                    [np.nan],
                                    [-9.57130872e+08],
                                    [np.nan],
                                    [9.22114527e+07],
                                    [np.nan],
                                    [1.12643819e+09],
                                    [np.nan],
                                    [1.31715269e+09],
                                    [np.nan],
                                    [5.39940093e+08],
                                    [np.nan],
                                    [1.51440838e+08],
                                    [np.nan],
                                    [1.75339071e+08],
                                    [np.nan],
                                    [8.04740415e+07],
                                    [np.nan],
                                    [6.20445815e+07]]

        print('test get financial data, in multi thread mode')
        df_list = get_financial_report_type_raw_data(start=start, end=end, shares=shares, htypes=htypes, parallel=4)
        self.assertIsInstance(df_list, tuple)
        self.assertEqual(len(df_list), 4)
        self.assertEqual(len(df_list[0]), 3)
        self.assertEqual(len(df_list[1]), 3)
        self.assertEqual(len(df_list[2]), 3)
        self.assertEqual(len(df_list[3]), 3)
        # 检查确认所有数据类型正确
        self.assertTrue(all(isinstance(item, pd.DataFrame) for subdict in df_list for item in subdict.values()))
        # 检查是否有空数据
        print(all(item.empty for subdict in df_list for item in subdict.values()))
        # 检查获取的每组数据正确，且所有数据的顺序一致, 如果取到空数据，则忽略
        if df_list[0]['000039.SZ'].empty:
            print(f'income data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[0]['000039.SZ'].values, target_basic_eps_000039))
        if df_list[0]['600748.SH'].empty:
            print(f'income data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[0]['600748.SH'].values, target_basic_eps_600748))
        if df_list[0]['000040.SZ'].empty:
            print(f'income data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[0]['000040.SZ'].values, target_basic_eps_000040))

        if df_list[1]['000039.SZ'].empty:
            print(f'indicator data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[1]['000039.SZ'].values, target_eps_000039))
        if df_list[1]['600748.SH'].empty:
            print(f'indicator data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[1]['600748.SH'].values, target_eps_600748))
        if df_list[1]['000040.SZ'].empty:
            print(f'indicator data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[1]['000040.SZ'].values, target_eps_000040))

        if df_list[2]['000039.SZ'].empty:
            print(f'balance data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[2]['000039.SZ'].values, target_total_share_000039))
        if df_list[2]['600748.SH'].empty:
            print(f'balance data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[2]['600748.SH'].values, target_total_share_600748))
        if df_list[2]['000040.SZ'].empty:
            print(f'balance data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[2]['000040.SZ'].values, target_total_share_000040))

        if df_list[3]['000039.SZ'].empty:
            print(f'cash flow data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[3]['000039.SZ'].values, target_net_profit_000039, equal_nan=True))
        if df_list[3]['600748.SH'].empty:
            print(f'cash flow data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[3]['600748.SH'].values, target_net_profit_600748, equal_nan=True))
        if df_list[3]['000040.SZ'].empty:
            print(f'cash flow data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[3]['000040.SZ'].values, target_net_profit_000040, equal_nan=True))

        print('test get financial data, in single thread mode')
        df_list = get_financial_report_type_raw_data(start=start, end=end, shares=shares, htypes=htypes, parallel=0)
        self.assertIsInstance(df_list, tuple)
        self.assertEqual(len(df_list), 4)
        self.assertEqual(len(df_list[0]), 3)
        self.assertEqual(len(df_list[1]), 3)
        self.assertEqual(len(df_list[2]), 3)
        self.assertEqual(len(df_list[3]), 3)
        # 检查确认所有数据类型正确
        self.assertTrue(all(isinstance(item, pd.DataFrame) for subdict in df_list for item in subdict.values()))
        # 检查是否有空数据，因为网络问题，有可能会取到空数据
        self.assertFalse(all(item.empty for subdict in df_list for item in subdict.values()))
        # 检查获取的每组数据正确，且所有数据的顺序一致, 如果取到空数据，则忽略
        if df_list[0]['000039.SZ'].empty:
            print(f'income data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[0]['000039.SZ'].values, target_basic_eps_000039))
        if df_list[0]['600748.SH'].empty:
            print(f'income data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[0]['600748.SH'].values, target_basic_eps_600748))
        if df_list[0]['000040.SZ'].empty:
            print(f'income data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[0]['000040.SZ'].values, target_basic_eps_000040))

        if df_list[1]['000039.SZ'].empty:
            print(f'indicator data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[1]['000039.SZ'].values, target_eps_000039))
        if df_list[1]['600748.SH'].empty:
            print(f'indicator data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[1]['600748.SH'].values, target_eps_600748))
        if df_list[1]['000040.SZ'].empty:
            print(f'indicator data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[1]['000040.SZ'].values, target_eps_000040))

        if df_list[2]['000039.SZ'].empty:
            print(f'balance data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[2]['000039.SZ'].values, target_total_share_000039))
        if df_list[2]['600748.SH'].empty:
            print(f'balance data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[2]['600748.SH'].values, target_total_share_600748))
        if df_list[2]['000040.SZ'].empty:
            print(f'balance data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[2]['000040.SZ'].values, target_total_share_000040))

        if df_list[3]['000039.SZ'].empty:
            print(f'cash flow data for "000039.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[3]['000039.SZ'].values, target_net_profit_000039, equal_nan=True))
        if df_list[3]['600748.SH'].empty:
            print(f'cash flow data for "600748.SH" is empty')
        else:
            self.assertTrue(np.allclose(df_list[3]['600748.SH'].values, target_net_profit_600748, equal_nan=True))
        if df_list[3]['000040.SZ'].empty:
            print(f'cash flow data for "000040.SZ" is empty')
        else:
            self.assertTrue(np.allclose(df_list[3]['000040.SZ'].values, target_net_profit_000040, equal_nan=True))

    def test_get_composite_type_raw_data(self):
        pass


class RetryableError(Exception):
    """ 用于retry测试的自定义Error Type"""
    pass


class AnotherRetryableError(Exception):
    """ 用于retry测试的自定义Error Type"""
    pass


class UnexpectedError(Exception):
    """ 用于retry测试的自定义Error Type"""
    pass


class TestUtilityFuncs(unittest.TestCase):
    def setUp(self):
        pass

    def test_unify(self):
        n1 = 2
        self.assertEqual(unify(n1), 2)
        n2 = np.array([[1., 1., 1., 1.], [0., 1., 0., 1.]])
        n3 = np.array([[.25, .25, .25, .25], [0., .5, 0., .5]])
        self.assertTrue(np.allclose(unify(n2), n3))

    def test_time_string_format(self):
        print('Testing qt.time_string_format() function:')
        t = 3.14
        self.assertEqual(time_str_format(t), '3s 140.0ms')
        self.assertEqual(time_str_format(t, estimation=True), '3s ')
        self.assertEqual(time_str_format(t, short_form=True), '3"140')
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), '3"')
        t = 300.14
        self.assertEqual(time_str_format(t), '5min 140.0ms')
        self.assertEqual(time_str_format(t, estimation=True), '5min ')
        self.assertEqual(time_str_format(t, short_form=True), "5'140")
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), "5'")
        t = 7435.0014
        self.assertEqual(time_str_format(t), '2hrs 3min 55s 1.4ms')
        self.assertEqual(time_str_format(t, estimation=True), '2hrs ')
        self.assertEqual(time_str_format(t, short_form=True), "2H3'55\"001")
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), "2H")
        t = 88425.0509
        self.assertEqual(time_str_format(t), '1days 33min 45s 50.9ms')
        self.assertEqual(time_str_format(t, estimation=True), '1days ')
        self.assertEqual(time_str_format(t, short_form=True), "1D33'45\"051")
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), "1D")

    def test_str_to_list(self):
        self.assertEqual(str_to_list('a,b,c,d,e'), ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(str_to_list('a, b, c '), ['a', 'b', 'c'])
        self.assertEqual(str_to_list('a, b: c', sep_char=':'), ['a,b', 'c'])
        self.assertEqual(str_to_list('abc'), ['abc'])
        self.assertEqual(str_to_list(''), [])
        self.assertRaises(AssertionError, str_to_list, 123)

    def test_list_or_slice(self):
        str_dict = {'close': 0, 'open': 1, 'high': 2, 'low': 3}
        self.assertEqual(list_or_slice(slice(1, 2, 1), str_dict), slice(1, 2, 1))
        self.assertEqual(list_or_slice('open', str_dict), [1])
        self.assertEqual(list(list_or_slice('close, high, low', str_dict)), [0, 2, 3])
        self.assertEqual(list(list_or_slice('close:high', str_dict)), [0, 1, 2])
        self.assertEqual(list(list_or_slice(['open'], str_dict)), [1])
        self.assertEqual(list(list_or_slice(['open', 'high'], str_dict)), [1, 2])
        self.assertEqual(list(list_or_slice(0, str_dict)), [0])
        self.assertEqual(list(list_or_slice([0, 2], str_dict)), [0, 2])
        self.assertEqual(list(list_or_slice([True, False, True, False], str_dict)), [0, 2])

    def test_labels_to_dict(self):
        target_list = [0, 1, 10, 100]
        target_dict = {'close': 0, 'open': 1, 'high': 2, 'low': 3}
        target_dict2 = {'close': 0, 'open': 2, 'high': 1, 'low': 3}
        self.assertEqual(labels_to_dict('close, open, high, low', target_list), target_dict)
        self.assertEqual(labels_to_dict(['close', 'open', 'high', 'low'], target_list), target_dict)
        self.assertEqual(labels_to_dict('close, high, open, low', target_list), target_dict2)
        self.assertEqual(labels_to_dict(['close', 'high', 'open', 'low'], target_list), target_dict2)

    def test_input_to_list(self):
        """ test util function input_to_list()"""
        self.assertEqual(input_to_list(5, 3), [5, 5, 5])
        self.assertEqual(input_to_list(5, 3, 0), [5, 5, 5])
        self.assertEqual(input_to_list([5], 3, 0), [5, 0, 0])
        self.assertEqual(input_to_list([5, 4], 3, 0), [5, 4, 0])

    def test_regulate_date_format(self):
        self.assertEqual(regulate_date_format('2019/11/06'), '20191106')
        self.assertEqual(regulate_date_format('2019-11-06'), '20191106')
        self.assertEqual(regulate_date_format('20191106'), '20191106')
        self.assertEqual(regulate_date_format('191106'), '20061119')
        self.assertEqual(regulate_date_format('830522'), '19830522')
        self.assertEqual(regulate_date_format(datetime.datetime(2010, 3, 15)), '20100315')
        self.assertEqual(regulate_date_format(pd.Timestamp('2010.03.15')), '20100315')
        self.assertRaises(ValueError, regulate_date_format, 'abc')
        self.assertRaises(ValueError, regulate_date_format, '2019/13/43')

    def test_list_to_str_format(self):
        self.assertEqual(list_to_str_format(['close', 'open', 'high', 'low']),
                         'close,open,high,low')
        self.assertEqual(list_to_str_format(['letters', '  ', '123  4', 123, '   kk  l']),
                         'letters,,1234,kkl')
        self.assertEqual(list_to_str_format('a string input'),
                         'a,string,input')
        self.assertEqual(list_to_str_format('already,a,good,string'),
                         'already,a,good,string')
        self.assertRaises(AssertionError, list_to_str_format, 123)

    def test_is_trade_day(self):
        """test if the funcion maybe_trade_day() and is_market_trade_day() works properly
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        date_weekend = '20210424'
        date_seems_trade_day = '20210217'
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'

        self.assertTrue(maybe_trade_day(date_trade))
        self.assertFalse(maybe_trade_day(date_holiday))
        self.assertFalse(maybe_trade_day(date_weekend))
        self.assertTrue(maybe_trade_day(date_seems_trade_day))
        self.assertTrue(maybe_trade_day(date_too_early))
        self.assertTrue(maybe_trade_day(date_too_late))
        self.assertTrue(maybe_trade_day(date_christmas))
        self.assertTrue(is_market_trade_day(date_trade))
        self.assertFalse(is_market_trade_day(date_holiday))
        self.assertFalse(is_market_trade_day(date_weekend))
        self.assertFalse(is_market_trade_day(date_seems_trade_day))
        self.assertFalse(is_market_trade_day(date_too_early))
        self.assertFalse(is_market_trade_day(date_too_late))
        self.assertTrue(is_market_trade_day(date_christmas))
        self.assertFalse(is_market_trade_day(date_christmas, exchange='XHKG'))

        date_trade = pd.to_datetime('20210401')
        date_holiday = pd.to_datetime('20210102')
        date_weekend = pd.to_datetime('20210424')

        self.assertTrue(maybe_trade_day(date_trade))
        self.assertFalse(maybe_trade_day(date_holiday))
        self.assertFalse(maybe_trade_day(date_weekend))

    def test_weekday_name(self):
        """ test util func weekday_name()"""
        self.assertEqual(weekday_name(0), 'Monday')
        self.assertEqual(weekday_name(1), 'Tuesday')
        self.assertEqual(weekday_name(2), 'Wednesday')
        self.assertEqual(weekday_name(3), 'Thursday')
        self.assertEqual(weekday_name(4), 'Friday')
        self.assertEqual(weekday_name(5), 'Saturday')
        self.assertEqual(weekday_name(6), 'Sunday')

    def test_list_truncate(self):
        """ test util func list_truncate()"""
        l = [1, 2, 3, 4, 5]
        ls = list_truncate(l, 2)
        self.assertEqual(ls[0], [1, 2])
        self.assertEqual(ls[1], [3, 4])
        self.assertEqual(ls[2], [5])

        self.assertRaises(AssertionError, list_truncate, l, 0)
        self.assertRaises(AssertionError, list_truncate, 12, 0)
        self.assertRaises(AssertionError, list_truncate, 0, l)

    def test_maybe_trade_day(self):
        """ test util function maybe_trade_day()"""
        self.assertTrue(maybe_trade_day('20220104'))
        self.assertTrue(maybe_trade_day('2021-12-31'))
        self.assertTrue(maybe_trade_day(pd.to_datetime('2020/03/06')))

        self.assertFalse(maybe_trade_day('2020-01-01'))
        self.assertFalse(maybe_trade_day('2020/10/06'))

        self.assertRaises(TypeError, maybe_trade_day, 'aaa')

    def test_prev_trade_day(self):
        """test the function prev_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        prev_holiday = pd.to_datetime(date_holiday) - pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        prev_weekend = pd.to_datetime(date_weekend) - pd.Timedelta(1, 'd')
        date_seems_trade_day = '20210217'
        prev_seems_trade_day = '20210217'
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        self.assertEqual(pd.to_datetime(prev_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_holiday)),
                         pd.to_datetime(prev_holiday))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_weekend)),
                         pd.to_datetime(prev_weekend))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_seems_trade_day)),
                         pd.to_datetime(prev_seems_trade_day))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_too_early)),
                         pd.to_datetime(date_too_early))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_too_late)),
                         pd.to_datetime(date_too_late))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_christmas)),
                         pd.to_datetime(date_christmas))

    def test_next_trade_day(self):
        """ test the function next_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        next_holiday = pd.to_datetime(date_holiday) + pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        next_weekend = pd.to_datetime(date_weekend) + pd.Timedelta(2, 'd')
        date_seems_trade_day = '20210217'
        next_seems_trade_day = '20210217'
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        self.assertEqual(pd.to_datetime(next_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(next_trade_day(date_holiday)),
                         pd.to_datetime(next_holiday))
        self.assertEqual(pd.to_datetime(next_trade_day(date_weekend)),
                         pd.to_datetime(next_weekend))
        self.assertEqual(pd.to_datetime(next_trade_day(date_seems_trade_day)),
                         pd.to_datetime(next_seems_trade_day))
        self.assertEqual(pd.to_datetime(next_trade_day(date_too_early)),
                         pd.to_datetime(date_too_early))
        self.assertEqual(pd.to_datetime(next_trade_day(date_too_late)),
                         pd.to_datetime(date_too_late))
        self.assertEqual(pd.to_datetime(next_trade_day(date_christmas)),
                         pd.to_datetime(date_christmas))

    def test_prev_market_trade_day(self):
        """ test the function prev_market_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        prev_holiday = pd.to_datetime(date_holiday) - pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        prev_weekend = pd.to_datetime(date_weekend) - pd.Timedelta(1, 'd')
        date_seems_trade_day = '20210217'
        prev_seems_trade_day = pd.to_datetime(date_seems_trade_day) - pd.Timedelta(7, 'd')
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        prev_christmas_xhkg = '20201224'
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_holiday)),
                         pd.to_datetime(prev_holiday))
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_weekend)),
                         pd.to_datetime(prev_weekend))
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_seems_trade_day)),
                         pd.to_datetime(prev_seems_trade_day))
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_too_early)),
                         None)
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_too_late)),
                         None)
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_christmas, 'SSE')),
                         pd.to_datetime(date_christmas))
        self.assertEqual(pd.to_datetime(prev_market_trade_day(date_christmas, 'XHKG')),
                         pd.to_datetime(prev_christmas_xhkg))

    def test_next_market_trade_day(self):
        """ test the function next_market_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        next_holiday = pd.to_datetime(date_holiday) + pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        next_weekend = pd.to_datetime(date_weekend) + pd.Timedelta(2, 'd')
        date_seems_trade_day = '20210217'
        next_seems_trade_day = pd.to_datetime(date_seems_trade_day) + pd.Timedelta(1, 'd')
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        next_christmas_xhkg = '20201228'
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_holiday)),
                         pd.to_datetime(next_holiday))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_weekend)),
                         pd.to_datetime(next_weekend))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_seems_trade_day)),
                         pd.to_datetime(next_seems_trade_day))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_too_early)),
                         None)
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_too_late)),
                         None)
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_christmas, 'SSE')),
                         pd.to_datetime(date_christmas))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_christmas, 'XHKG')),
                         pd.to_datetime(next_christmas_xhkg))

    def test_is_number_like(self):
        """test the function: is_number_like()"""
        self.assertTrue(is_number_like(123))
        self.assertTrue(is_number_like(23.7))
        self.assertTrue(is_number_like('2.3'))
        self.assertTrue(is_number_like('-0.2'))
        self.assertTrue(is_number_like('0.03'))
        self.assertTrue(is_number_like('345'))
        self.assertTrue(is_number_like('-45.321'))

        self.assertFalse(is_number_like('-..023'))
        self.assertFalse(is_number_like('abc'))
        self.assertFalse(is_number_like('0.32a'))
        self.assertFalse(is_number_like('0-2'))

    def test_retry_decorator(self):
        """ test the retry decorator"""
        print(f'test no retry needed functions')
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def succeeds():
            self.counter += 1
            return 'success'

        r = succeeds()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 1)

        print(f'test retry only once')
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        r = fails_once()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 2)

        print(f'test retry limit is reached')
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def always_fails():
            self.counter += 1
            raise RetryableError('failed')

        with self.assertRaises(RetryableError):
            always_fails()
        self.assertEqual(self.counter, 4)

        print(f'test checking for multiple exceptions')
        self.counter = 0

        @retry((RetryableError, AnotherRetryableError), tries=4, delay=0.1)
        def raise_multiple_exceptions():
            self.counter += 1
            if self.counter == 1:
                raise RetryableError('a retryable error')
            elif self.counter == 2:
                raise AnotherRetryableError('another retryable error')
            else:
                return 'success'

        r = raise_multiple_exceptions()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 3)

        print(f'does not retry when unexpected error occurs')

        @retry(RetryableError, tries=4, delay=0.1)
        def raise_unexpected_error():
            raise UnexpectedError('unexpected error')

        with self.assertRaises(UnexpectedError):
            raise_unexpected_error()

        print(f'test recording info with a logger')
        self.counter = 0
        # set up the logger object
        sh = logging.StreamHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(sh)

        @retry(RetryableError, tries=4, delay=0.1, logger=logger)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        fails_once()


class TestTushare(unittest.TestCase):
    """测试所有Tushare函数的运行正确"""

    def setUp(self):
        pass

    def test_stock_basic(self):
        print(f'test tushare function: stock_basic')
        df = stock_basic()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_trade_calendar(self):
        print(f'test tushare function: trade_calendar')
        df = trade_calendar(exchange='SSE')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_name_change(self):
        print(f'test tushare function: name_change')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = name_change(shares=shares)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

        df = name_change(shares=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_new_share(self):
        print(f'test tushare function: new_share')
        start = '20180101'
        end = '20191231'
        df = new_share()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

        df = new_share(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    # TODO: solve this problem, error message thrown out: no such module
    # TODO: called "stock_company"
    def test_stock_company(self):
        print(f'test tushare function: stock_company')
        shares = '600748.SH'
        df = stock_company(shares=shares)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_get_bar(self):
        print(f'test tushare function: get_bar')
        print(f'test type: one share asset type E')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = get_bar(shares=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

        print(f'test type: one share asset type I')
        shares = '000300.SH'
        start = '20180101'
        end = '20191231'
        df = get_bar(shares=shares, start=start, end=end, asset_type='I')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

        print(f'test type: one share asset type E lots of data')
        shares = '000001.SZ'
        start = '19910101'
        end = '20201231'
        df = get_bar(shares=shares, start=start, end=end, asset_type='E')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 7053)
        self.assertEqual(len(df.loc[np.isnan(df.close)]), 0)
        self.assertEqual(len(df.loc[np.isnan(df.open)]), 0)
        self.assertEqual(len(df.loc[np.isnan(df.high)]), 0)
        self.assertEqual(len(df.loc[np.isnan(df.low)]), 0)
        self.assertEqual(len(df.loc[np.isnan(df.pre_close)]), 0)
        self.assertEqual(len(df.loc[np.isnan(df.change)]), 0)
        print(df.iloc[4986])
        print(df.iloc[4987])
        self.assertEqual(df.iloc[4986].trade_date, "19991008")
        self.assertAlmostEqual(df.iloc[4986].open, 485.235, 2)
        self.assertAlmostEqual(df.iloc[4986].high, 490.296, 2)
        self.assertAlmostEqual(df.iloc[4986].low, 474.691, 2)
        self.assertAlmostEqual(df.iloc[4986].close, 477.221, 2)
        self.assertAlmostEqual(df.iloc[4986].pre_close, 491.139, 2)
        self.assertAlmostEqual(df.iloc[4986].change, -13.9181, 2)
        self.assertEqual(df.iloc[4987].trade_date, "19990930")
        self.assertAlmostEqual(df.iloc[4987].open, 499.786, 2)
        self.assertAlmostEqual(df.iloc[4987].high, 505.901, 2)
        self.assertAlmostEqual(df.iloc[4987].low, 488.82, 2)
        self.assertAlmostEqual(df.iloc[4987].close, 491.139, 2)
        self.assertAlmostEqual(df.iloc[4987].pre_close, 499.575, 2)
        self.assertAlmostEqual(df.iloc[4987].change, -8.4352, 2)
        # test all close prices are equal to next pre_close
        total_unfit = 0
        for i in range(7052):
            cur_close = df.iloc[i + 1].close
            pre_close = df.iloc[i].pre_close
            if abs(cur_close - pre_close) > 1:
                print(f'found discrepencies in close data:'
                      f'cur_close: {cur_close}, pre_close: {pre_close} @ iloc[{i}]\n'
                      f'{df.iloc[i:i + 2]}')
                total_unfit += 1
        self.assertLessEqual(total_unfit, 5)
        df.info()
        print(df)

        print(f'test type: multiple shares asset type E, raise Error')
        shares = '600748.SH,000616.SZ,000620.SZ,000667.SZ'
        start = '20180101'
        end = '20191231'
        self.assertRaises(AssertionError, get_bar, shares=shares, start=start, end=end, asset_type='E')

        print(f'test type: multiple shares asset type E, with freq = "30min" -> authority issue!')
        shares = '000620.SZ,000667.SZ'
        start = '20180101'
        end = '20191231'
        # df = get_bar(shares=shares, start=start, end=end, asset_type='E', freq='30min')
        # self.assertIsInstance(df, pd.DataFrame)
        # self.assertFalse(df.empty)
        # df.info()
        # print(df.head(30))

    def test_get_index(self):
        print(f'test tushare function: get_index')
        index = '000300.SH'
        start = '20180101'
        end = '20191231'
        df = get_index(index=index, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_income(self):
        print(f'test tushare function: income')
        shares = '600748.SH'
        rpt_date = '20181231'
        start = '20180101'
        end = '20191231'
        df = income(share=shares,
                    rpt_date=rpt_date,
                    start=start,
                    end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        df = income(share=shares,
                    start=start,
                    end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'Test income: extracted single share income: \n{df}')

        # test another shares data extraction:
        shares = '000010.SZ'
        fields = 'ts_code,ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue, ' \
                 'int_income, prem_earned, comm_income, n_commis_income, n_oth_income, n_oth_b_income'
        df = income(share=shares,
                    start=start,
                    end=end,
                    fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \n{df}')
        self.assertFalse(df.empty)

        shares = '000010.SZ'
        fields = 'ts_code,ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue, ' \
                 'int_income, prem_earned, comm_income, n_commis_income, n_oth_income, n_oth_b_income'
        df = income(share=shares,
                    start=start,
                    end='20210307',
                    fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income with end date = today: \n{df}')
        self.assertFalse(df.empty)

        # test long idx_range data extraction:
        shares = '000039.SZ'
        start = '20080101'
        end = '20201231'
        fields = 'ts_code,ann_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue, ' \
                 'int_income, prem_earned, comm_income, n_commis_income, n_oth_income, n_oth_b_income, ' \
                 'prem_income, out_prem, une_prem_reser, reins_income, n_sec_tb_income, n_sec_uw_income, ' \
                 'n_asset_mg_income'
        df = income(share=shares,
                    start=start,
                    end=end,
                    fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \ninfo:\n{df.info()}')
        self.assertFalse(df.empty)

    def test_balance(self):
        print(f'test tushare function: balance')
        shares = '000039.SZ'
        start = '20080101'
        end = '20201231'
        fields = 'special_rese, money_cap,trad_asset,notes_receiv,accounts_receiv,oth_receiv,' \
                 'prepayment,div_receiv,int_receiv,inventories,amor_exp, nca_within_1y,sett_rsrv' \
                 ',loanto_oth_bank_fi,premium_receiv,reinsur_receiv,reinsur_res_receiv'
        df = balance(share=shares,
                     start=start,
                     end=end,
                     fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \ninfo:\n{df.info()}\nhead:\n{df.head()}')
        self.assertFalse(df.empty)

    def test_cashflow(self):
        print(f'test tushare function: cashflow')
        fields = ['net_profit',
                  'finan_exp',
                  'c_fr_sale_sg',
                  'recp_tax_rends',
                  'n_depos_incr_fi',
                  'n_incr_loans_cb',
                  'n_inc_borr_oth_fi',
                  'prem_fr_orig_contr',
                  'n_incr_insured_dep',
                  'n_reinsur_prem',
                  'n_incr_disp_tfa']
        fields = list_to_str_format(fields)
        shares = '000039.SZ'
        start = '20080101'
        end = '20201231'
        df = cashflow(share=shares,
                      start=start,
                      end=end,
                      fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \ninfo:\n{df.info()}\nhead:\n{df.head()}')
        self.assertFalse(df.empty)

    def test_indicators(self):
        print(f'test tushare function: indicators')
        shares = '600016.SH'
        rpt_date = '20180101'
        start = '20180101'
        end = '20191231'
        df = indicators(share=shares,
                        rpt_date=rpt_date,
                        start=start,
                        end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        df = indicators(share=shares,
                        start=start,
                        end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'\nTest indicators 2: extracted indicator: \n{df}')

    def test_top_list(self):
        shares = '000732.SZ'
        trade_date = '20180104'
        print(f'test tushare function: top_list')
        print(f'test 1: test no specific shares')
        df = top_list(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: test one specific share')
        df = top_list(trade_date=trade_date, shares=shares)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: test multiple specific share')  # tushare does not allow multiple share codes in top_list
        shares = '000672.SZ, 000732.SZ'
        df = top_list(trade_date=trade_date, shares=shares)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

    def test_index_basic(self):
        """test function index_basic"""
        print(f'test tushare function: index_basic\n'
              f'=======================================')
        print(f'test 1: basic usage of the function')
        df = index_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: get all information of index with market')
        df = index_basic(market='SSE')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3: thrown error on bad parameters')
        df = index_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_index_indicators(self):
        print(f'test tushare function: index_indicators\n'
              f'=======================================')
        index = '000300.SH'
        trade_date = '20180104'
        start = '20180101'
        end = '20180115'

        print(f'test 1: test single index single date\n'
              f'=====================================')
        df = index_indicators(trade_date=trade_date, index=index)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: test single index in date idx_range\n'
              f'=======================================')
        df = index_indicators(index=index, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3: test multiple specific indices in single date\n'
              f'=====================================================')
        index = '000300.SH, 000001.SH'  # tushare does not support multiple indices in index_indicators
        df = index_indicators(trade_date=trade_date, index=index)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        print(f'test 4: test all indices in single date\n'
              f'=======================================')
        df = index_indicators(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_composite(self):
        print(f'test tushare function: composit\n'
              f'===============================')
        index = '399300.SZ'
        start = '20190101'
        end = '20190930'

        print(f'test 1: find composit of one specific index in months\n'
              f'===============================')
        df = composite(index=index, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

        index = '399001.SZ'
        df = composite(index=index, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

        print(f'test 2: find composit of one specific index in exact trade date\n'
              f'===============================')
        index = '000300.SH'
        trade_date = '20200430'
        df = composite(index=index, trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("weight", ascending=False).head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

        trade_date = '20201008'
        df = composite(index=index, trade_date=trade_date)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        print(f'test 3: find composit of all indices in one specific trade date\n'
              f'===============================')
        index = '000300.SH'
        trade_date = '20201009'
        df = composite(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("index_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.index_code.nunique()} unique index_codes\n'
              f'they are: \n{list(df.index_code.unique())}')

    def test_fund_basic(self):
        """ 测试函数fund_basic()

        :return:
        """
        print(f'test tushare function fund_basic\n'
              f'===============================')

        print(f'test 1: find basic information for all funds')
        df = fund_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: find basic information for all funds that are traded inside market')
        df = fund_basic(market='E')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test3: find basic info for all funds that are being issued')
        df = fund_basic(status='I')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test4, test error thrown out due to bad parameter')
        df = fund_basic(market=3)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertTrue(df.empty)

    def test_fund_net_value(self):
        print(f'test tushare function: fund_net_value\n'
              f'===============================')
        fund = '399300.SZ'
        trade_date = '20180909'

        print(f'test 1: find all funds in one specific date, exchanging in market\n'
              f'===============================')
        df = fund_net_value(date=trade_date, market='E')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

        print(f'test 1: find all funds in one specific date, exchange outside market\n'
              f'===============================')
        df = fund_net_value(date=trade_date, market='O')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

        print(f'test 2: find value of one fund in history\n'
              f'===============================')
        fund = '512960.SH'
        df = fund_net_value(fund=fund)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ann_date.nunique()} unique trade dates\n'
              f'first 10 items of them are: \n{list(df.ann_date.unique()[:9])}')

        print(f'test 3: find value of multiple funds in history\n'
              f'===============================')
        fund = '511770.SH, 511650.SH, 511950.SH, 002760.OF, 002759.OF'
        trade_date = '20201009'
        df = fund_net_value(fund=fund, date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertEqual(set(df.ts_code.unique()), set(str_to_list(fund)))
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

    def test_future_basic(self):
        print(f'test tushare function: future_basic')
        print(f'test 1, load basic future information with default input\n'
              f'========================================================')
        df = future_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

        print(f'test 2, load basic future information in SHFE type == 1\n'
              f'========================================================')
        exchange = 'SHFE'
        df = future_basic(exchange=exchange, future_type='1')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

    def test_options_basic(self):
        print(f'test tushare function: options_basic')
        print(f'test 1, load basic options information with default input\n'
              f'========================================================')
        df = options_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

    def test_future_daily(self):
        print(f'test tushare function: future_daily')
        print(f'test 1, load basic future information at one specific date\n'
              f'==========================================================')
        future = 'AL1905.SHF'
        trade_date = '20190628'
        start = '20190101'
        end = '20190930'
        df = future_daily(trade_date=trade_date, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2, load basic future information for one ts_code\n'
              f'==========================================================')
        df = future_daily(future=future, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3, error raising when both future and trade_date are None\n'
              f'==============================================================')
        self.assertRaises(ValueError, future_daily, start=start, end=end)

    def test_options_daily(self):
        print(f'test tushare function: options_daily')
        print(f'test 1, load option information at one specific date\n'
              f'==========================================================')
        option = '10001677.SH'
        trade_date = '20190628'
        start = '20190101'
        end = '20190930'
        df = options_daily(trade_date=trade_date, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2, load basic future information for one ts_code\n'
              f'==========================================================')
        df = options_daily(option=option, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3, error raising when both future and trade_date are None\n'
              f'==============================================================')
        self.assertRaises(ValueError, future_daily, start=start, end=end)


class TestTAFuncs(unittest.TestCase):
    """测试所有的TAlib函数输出正常"""

    def setUp(self):
        self.data_rows = 50

        self.close = np.array([10.04, 10, 10, 9.99, 9.97, 9.99, 10.03, 10.03, 10.06, 10.06, 10.11,
                               10.09, 10.07, 10.06, 10.09, 10.03, 10.03, 10.06, 10.08, 10, 9.99,
                               10.03, 10.03, 10.06, 10.03, 9.97, 9.94, 9.83, 9.77, 9.84, 9.91, 9.93,
                               9.96, 9.91, 9.91, 9.88, 9.91, 9.64, 9.56, 9.57, 9.55, 9.57, 9.61, 9.61,
                               9.55, 9.57, 9.63, 9.64, 9.65, 9.62])
        self.open = np.array([10.02, 10, 9.98, 9.97, 9.99, 10.01, 10.04, 10.06, 10.06, 10.11,
                              10.11, 10.07, 10.06, 10.09, 10.03, 10.02, 10.06, 10.08, 9.99, 10,
                              10.03, 10.02, 10.06, 10.03, 9.97, 9.94, 9.83, 9.78, 9.77, 9.91, 9.92,
                              9.97, 9.91, 9.9, 9.88, 9.91, 9.63, 9.64, 9.57, 9.55, 9.58, 9.61, 9.62,
                              9.55, 9.57, 9.61, 9.63, 9.64, 9.61, 9.56])
        self.high = np.array([10.07, 10, 10, 10, 10.03, 10.03, 10.04, 10.09, 10.1, 10.14, 10.11, 10.1,
                              10.09, 10.09, 10.1, 10.05, 10.07, 10.09, 10.1, 10, 10.04, 10.04, 10.06,
                              10.09, 10.05, 9.97, 9.96, 9.86, 9.77, 9.92, 9.94, 9.97, 9.97, 9.92, 9.92,
                              9.92, 9.93, 9.64, 9.58, 9.6, 9.58, 9.62, 9.62, 9.64, 9.59, 9.62, 9.63,
                              9.7, 9.66, 9.64])
        self.low = np.array([9.99, 10, 9.97, 9.97, 9.97, 9.98, 9.99, 10.03, 10.03, 10.04, 10.11, 10.07,
                             10.05, 10.03, 10.03, 10.01, 9.99, 10.03, 9.95, 10, 9.95, 10, 10.01, 9.99,
                             9.96, 9.89, 9.83, 9.77, 9.77, 9.8, 9.9, 9.91, 9.89, 9.89, 9.87, 9.85, 9.6,
                             9.64, 9.53, 9.55, 9.54, 9.55, 9.58, 9.54, 9.53, 9.53, 9.63, 9.64, 9.59, 9.56])
        self.volume = np.array([602422, 992935, 397181, 979150, 616616, 816010, 330009, 554499,
                                431742, 155719, 324684, 986208, 840540, 704761, 968846, 863191,
                                282875, 487998, 91664, 811549, 569464, 708073, 978526, 246066,
                                169516, 563430, 671046, 264677, 158782, 992361, 350309, 468395,
                                178206, 83145, 384713, 308022, 380623, 423506, 833615, 473541,
                                841975, 450572, 162390, 550347, 415988, 133953, 754915, 476105,
                                120871, 629045]).astype('float')

    def test_bbands(self):
        print(f'test TA function: bbands\n'
              f'========================')
        upper, middle, lower = bbands(self.close, timeperiod=5)
        print(f'results are\nupper:\n{upper}\nmiddle:\n{middle}\nlower:\n{lower}')

    def test_dema(self):
        print(f'test TA function: dema\n'
              f'======================')
        res = dema(self.close, period=5)
        print(f'result is\n{res}')

    def test_ema(self):
        print(f'test TA function: ema\n'
              f'======================')
        res = ema(self.close, span=5)
        print(f'result is\n{res}')

    def test_ht(self):
        print(f'test TA function: ht\n'
              f'======================')
        res = ht(self.close)
        print(f'result is\n{res}')

    def test_kama(self):
        print(f'test TA function: ht\n'
              f'======================')
        res = kama(self.close, timeperiod=5)
        print(f'result is\n{res}')

    def test_ma(self):
        print(f'test TA function: ma\n'
              f'=====================')
        res = ma(self.close)
        print(f'result is \n{res}')

    def test_mama(self):
        print(f'test TA function: mama\n'
              f'=======================')
        ma, fa = mama(self.close, fastlimit=0.2, slowlimit=0.5)
        print(f'results are \nma:\n{ma}\nfa:\n{fa}')

    def test_mavp(self):
        print(f'test TA function: mavp\n'
              f'=======================')
        periods = np.array([0.1, 0.2, 0.3])
        res = mavp(self.close, periods=self.low)
        print(f'result is \n{res}')

    def test_mid_point(self):
        print(f'test TA function: mid_point\n'
              f'============================')
        res = mid_point(self.close)
        print(f'result is \n{res}')

    def test_mid_price(self):
        print(f'test TA function: mid_price\n'
              f'============================')
        res = mid_price(self.high, self.low)
        print(f'result is \n{res}')

    def test_sar(self):
        print(f'test TA function: sar\n'
              f'======================')
        res = sar(self.high, self.low)
        print(f'result is \n{res}')

    def test_sarext(self):
        print(f'test TA function: sarext\n'
              f'=========================')
        res = sarext(self.high, self.low)
        print(f'result is \n{res}')

    def test_sma(self):
        print(f'test TA function: sma\n'
              f'======================')
        res = sma(self.close)
        print(f'result is \n{res}')

    def test_t3(self):
        print(f'test TA function: t3\n'
              f'=====================')
        res = t3(self.close)
        print(f'result is \n{res}')

    def test_tema(self):
        print(f'test TA function: tema\n'
              f'=======================')
        res = tema(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_trima(self):
        print(f'test TA function: trima\n'
              f'========================')
        res = trima(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_wma(self):
        print(f'test TA function: wma\n'
              f'======================')
        res = wma(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_adx(self):
        print(f'test TA function: adx\n'
              f'======================')
        res = adx(self.high, self.low, self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_adxr(self):
        print(f'test TA function: adxr\n'
              f'=======================')
        res = adxr(self.high, self.low, self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_apo(self):
        print(f'test TA function: apo\n'
              f'======================')
        res = apo(self.close)
        print(f'result is \n{res}')

    def test_aroon(self):
        print(f'test TA function: aroon\n'
              f'========================')
        down, up = aroon(self.high, self.low)
        print(f'results are:\naroon down:\n{down}\naroon up:\n{up}')

    def test_aroonosc(self):
        print(f'test TA function: aroonosc\n'
              f'===========================')
        res = aroonosc(self.high, self.low)
        print(f'result is \n{res}')

    def test_bop(self):
        print(f'test TA function: bop\n'
              f'======================')
        res = bop(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cci(self):
        print(f'test TA function: cci\n'
              f'======================')
        res = cci(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cmo(self):
        print(f'test TA function: cmo\n'
              f'======================')
        res = cmo(self.close)
        print(f'result is \n{res}')

    def test_dx(self):
        print(f'test TA function: dx\n'
              f'=====================')
        res = dx(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_macd(self):
        print(f'test TA function: macd\n'
              f'=======================')
        macd_res, macdsignal, macdhist = macd(self.close)
        print(f'results are:\nmacd:\n{macd_res}\nmacd signal:\n{macdsignal}\nmacd hist:\n{macdhist}')

    def test_macdext(self):
        print(f'test TA function: macdext\n'
              f'==========================')
        macd_res, macdsignal, macdhist = macdext(self.close)
        print(f'results are:\nmacd:\n{macd_res}\nmacd signal:\n{macdsignal}\nmacd hist:\n{macdhist}')

    def test_macdfix(self):
        print(f'test TA function: macdfix\n'
              f'==========================')
        macd_res, macdsignal, macdhist = macdfix(self.close)
        print(f'results are:\nmacd:\n{macd_res}\nmacd signal:\n{macdsignal}\nmacd hist:\n{macdhist}')

    def test_mfi(self):
        print(f'test TA function: mfi\n'
              f'======================')
        res = mfi(self.high, self.low, self.close, self.volume)
        print(f'result is \n{res}')

    def test_minus_di(self):
        print(f'test TA function: minus_di\n'
              f'===========================')
        res = minus_di(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_minus_dm(self):
        print(f'test TA function: minus_dm\n'
              f'===========================')
        res = minus_dm(self.high, self.low)
        print(f'result is \n{res}')

    def test_mom(self):
        print(f'test TA function: mom\n'
              f'======================')
        res = mom(self.close)
        print(f'result is \n{res}')

    def test_plus_di(self):
        print(f'test TA function: plus_di\n'
              f'==========================')
        res = plus_di(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_plus_dm(self):
        print(f'test TA function: plus_dm\n'
              f'==========================')
        res = plus_dm(self.high, self.low)
        print(f'result is \n{res}')

    def test_ppo(self):
        print(f'test TA function: ppo\n'
              f'======================')
        res = ppo(self.close)
        print(f'result is \n{res}')

    def test_roc(self):
        print(f'test TA function: roc\n'
              f'======================')
        res = roc(self.close)
        print(f'result is \n{res}')

    def test_rocp(self):
        print(f'test TA function: rocp\n'
              f'=======================')
        res = rocp(self.close)
        print(f'result is \n{res}')

    def test_rocr(self):
        print(f'test TA function: rocr\n'
              f'=======================')
        res = rocr(self.close)
        print(f'result is \n{res}')

    def test_rocr100(self):
        print(f'test TA function: rocr100\n'
              f'==========================')
        res = rocr100(self.close)
        print(f'result is \n{res}')

    def test_rsi(self):
        print(f'test TA function: rsi\n'
              f'======================')
        res = rsi(self.close)
        print(f'result is \n{res}')

    def test_stoch(self):
        print(f'test TA function: stoch\n'
              f'========================')
        slowk, slowd = stoch(self.high, self.low, self.close)
        print(f'results are\nslowk:\n{slowk}\nslowd:\n{slowd}')

    def test_stochf(self):
        print(f'test TA function: stochf\n'
              f'=========================')
        fastk, fastd = stochf(self.high, self.low, self.close)
        print(f'results are\nfastk:\n{fastk}\nfastd:\n{fastd}')

    def test_stochrsi(self):
        print(f'test TA function: stochrsi\n'
              f'===========================')
        fastk, fastd = stochrsi(self.close)
        print(f'results are\nfastk:\n{fastk}\nfastd:\n{fastd}')

    def test_trix(self):
        print(f'test TA function: trix\n'
              f'=======================')
        res = trix(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_ultosc(self):
        print(f'test TA function: ultosc\n'
              f'=========================')
        res = ultosc(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_willr(self):
        print(f'test TA function: willr\n'
              f'========================')
        res = willr(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_ad(self):
        print(f'test TA function: ad\n'
              f'=====================')
        res = ad(self.high, self.low, self.close, self.volume)
        print(f'result is \n{res}')

    def test_adosc(self):
        print(f'test TA function: adosc\n'
              f'========================')
        res = adosc(self.high, self.low, self.close, self.volume)
        print(f'result is \n{res}')

    def test_obv(self):
        print(f'test TA function: obv\n'
              f'======================')
        res = obv(self.close, self.volume)
        print(f'result is \n{res}')

    def test_atr(self):
        print(f'test TA function: atr\n'
              f'======================')
        res = atr(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_natr(self):
        print(f'test TA function: natr\n'
              f'=======================')
        res = natr(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_trange(self):
        print(f'test TA function: trange\n'
              f'=========================')
        res = trange(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_avgprice(self):
        print(f'test TA function: avgprice\n'
              f'===========================')
        res = avgprice(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_medprice(self):
        print(f'test TA function: medprice\n'
              f'===========================')
        res = medprice(self.high, self.low)
        print(f'result is \n{res}')

    def test_typprice(self):
        print(f'test TA function: typprice\n'
              f'===========================')
        res = typprice(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_wclprice(self):
        print(f'test TA function: wclprice\n'
              f'===========================')
        res = wclprice(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_ht_dcperiod(self):
        print(f'test TA function: ht_dcperiod\n'
              f'==============================')
        res = ht_dcperiod(self.close)
        print(f'result is \n{res}')

    def test_ht_dcphase(self):
        print(f'test TA function: ht_dcphase\n'
              f'=============================')
        res = ht_dcphase(self.close)
        print(f'result is \n{res}')

    def test_ht_phasor(self):
        print(f'test TA function: ht_phasor\n'
              f'============================')
        inphase, quadrature = ht_phasor(self.close)
        print(f'results are\ninphase:\n{inphase}\nquadrature:\n{quadrature}')

    def test_ht_sine(self):
        print(f'test TA function: ht_sine\n'
              f'==========================')
        res_a, res_b = ht_sine(self.close / 10)
        print(f'results are:\nres_a:\n{res_a}\nres_b:\n{res_b}')

    def test_ht_trendmode(self):
        print(f'test TA function: ht_trendmode\n'
              f'===============================')
        res = ht_trendmode(self.close)
        print(f'result is \n{res}')

    def test_cdl2crows(self):
        print(f'test TA function: cdl2crows\n'
              f'============================')
        res = cdl2crows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3blackcrows(self):
        print(f'test TA function: cdl3blackcrows\n'
              f'=================================')
        res = cdl3blackcrows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3inside(self):
        print(f'test TA function: cdl3inside\n'
              f'=============================')
        res = cdl3inside(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3linestrike(self):
        print(f'test TA function: cdl3linestrike\n'
              f'=================================')
        res = cdl3linestrike(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3outside(self):
        print(f'test TA function: cdl3outside\n'
              f'==============================')
        res = cdl3outside(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3starsinsouth(self):
        print(f'test TA function: cdl3starsinsouth\n'
              f'===================================')
        res = cdl3starsinsouth(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3whitesoldiers(self):
        print(f'test TA function: cdl3whitesoldiers\n'
              f'====================================')
        res = cdl3whitesoldiers(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlabandonedbaby(self):
        print(f'test TA function: cdlabandonedbaby\n'
              f'===================================')
        res = cdlabandonedbaby(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdladvanceblock(self):
        print(f'test TA function: cdladvanceblock\n'
              f'==================================')
        res = cdladvanceblock(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlbelthold(self):
        print(f'test TA function: cdlbelthold\n'
              f'==============================')
        res = cdlbelthold(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlbreakaway(self):
        print(f'test TA function: cdlbreakaway\n'
              f'===============================')
        res = cdlbreakaway(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlclosingmarubozu(self):
        print(f'test TA function: cdlclosingmarubozu\n'
              f'=====================================')
        res = cdlclosingmarubozu(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlconcealbabyswall(self):
        print(f'test TA function: cdlconcealbabyswall\n'
              f'======================================')
        res = cdlconcealbabyswall(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlcounterattack(self):
        print(f'test TA function: cdlcounterattack\n'
              f'===================================')
        res = cdlcounterattack(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldarkcloudcover(self):
        print(f'test TA function: cdldarkcloudcover\n'
              f'====================================')
        res = cdldarkcloudcover(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldoji(self):
        print(f'test TA function: cdldoji\n'
              f'==========================')
        res = cdldoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldojistar(self):
        print(f'test TA function: cdldojistar\n'
              f'==============================')
        res = cdldojistar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldragonflydoji(self):
        print(f'test TA function: cdldragonflydoji\n'
              f'===================================')
        res = cdldragonflydoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlengulfing(self):
        print(f'test TA function: cdlengulfing\n'
              f'===============================')
        res = cdlengulfing(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdleveningdojistar(self):
        print(f'test TA function: cdleveningdojistar\n'
              f'=====================================')
        res = cdleveningdojistar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdleveningstar(self):
        print(f'test TA function: cdleveningstar\n'
              f'=================================')
        res = cdleveningstar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlgapsidesidewhite(self):
        print(f'test TA function: cdlgapsidesidewhite\n'
              f'======================================')
        res = cdlgapsidesidewhite(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlgravestonedoji(self):
        print(f'test TA function: cdlgravestonedoji\n'
              f'====================================')
        res = cdlgravestonedoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhammer(self):
        print(f'test TA function: cdlhammer\n'
              f'============================')
        res = cdlhammer(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhangingman(self):
        print(f'test TA function: cdlhangingman\n'
              f'================================')
        res = cdlhangingman(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlharami(self):
        print(f'test TA function: cdlharami\n'
              f'============================')
        res = cdlharami(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlharamicross(self):
        print(f'test TA function: cdlharamicross\n'
              f'=================================')
        res = cdlharamicross(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhighwave(self):
        print(f'test TA function: cdlhighwave\n'
              f'==============================')
        res = cdlhighwave(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhikkake(self):
        print(f'test TA function: cdlhikkake\n'
              f'=============================')
        res = cdlhikkake(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhikkakemod(self):
        print(f'test TA function: cdlhikkakemod\n'
              f'================================')
        res = cdlhikkakemod(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhomingpigeon(self):
        print(f'test TA function: cdlhomingpigeon\n'
              f'==================================')
        res = cdlhomingpigeon(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlidentical3crows(self):
        print(f'test TA function: cdlidentical3crows\n'
              f'=====================================')
        res = cdlidentical3crows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlinneck(self):
        print(f'test TA function: cdlinneck\n'
              f'============================')
        res = cdlinneck(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlinvertedhammer(self):
        print(f'test TA function: cdlinvertedhammer\n'
              f'====================================')
        res = cdlinvertedhammer(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlkicking(self):
        print(f'test TA function: cdlkicking\n'
              f'=============================')
        res = cdlkicking(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlkickingbylength(self):
        print(f'test TA function: cdlkickingbylength\n'
              f'=====================================')
        res = cdlkickingbylength(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlladderbottom(self):
        print(f'test TA function: cdlladderbottom\n'
              f'==================================')
        res = cdlladderbottom(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdllongleggeddoji(self):
        print(f'test TA function: cdllongleggeddoji\n'
              f'====================================')
        res = cdllongleggeddoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdllongline(self):
        print(f'test TA function: cdllongline\n'
              f'==============================')
        res = cdllongline(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmarubozu(self):
        print(f'test TA function: cdlmarubozu\n'
              f'==============================')
        res = cdlmarubozu(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmatchinglow(self):
        print(f'test TA function: cdlmatchinglow\n'
              f'=================================')
        res = cdlmatchinglow(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmathold(self):
        print(f'test TA function: cdlmathold\n'
              f'=============================')
        res = cdlmathold(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmorningdojistar(self):
        print(f'test TA function: cdlmorningdojistar\n'
              f'=====================================')
        res = cdlmorningdojistar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmorningstar(self):
        print(f'test TA function: cdlmorningstar\n'
              f'=================================')
        res = cdlmorningstar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlonneck(self):
        print(f'test TA function: cdlonneck\n'
              f'============================')
        res = cdlonneck(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlpiercing(self):
        print(f'test TA function: cdlpiercing\n'
              f'==============================')
        res = cdlpiercing(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlrickshawman(self):
        print(f'test TA function: cdlrickshawman\n'
              f'=================================')
        res = cdlrickshawman(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlrisefall3methods(self):
        print(f'test TA function: cdlrisefall3methods\n'
              f'======================================')
        res = cdlrisefall3methods(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlseparatinglines(self):
        print(f'test TA function: cdlseparatinglines\n'
              f'=====================================')
        res = cdlseparatinglines(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlshootingstar(self):
        print(f'test TA function: cdlshootingstar\n'
              f'==================================')
        res = cdlshootingstar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlshortline(self):
        print(f'test TA function: cdlshortline\n'
              f'===============================')
        res = cdlshortline(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlspinningtop(self):
        print(f'test TA function: cdlspinningtop\n'
              f'=================================')
        res = cdlspinningtop(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlstalledpattern(self):
        print(f'test TA function: cdlstalledpattern\n'
              f'====================================')
        res = cdlstalledpattern(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlsticksandwich(self):
        print(f'test TA function: cdlsticksandwich\n'
              f'===================================')
        res = cdlsticksandwich(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdltakuri(self):
        print(f'test TA function: cdltakuri\n'
              f'============================')
        res = cdltakuri(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdltasukigap(self):
        print(f'test TA function: cdltasukigap\n'
              f'===============================')
        res = cdltasukigap(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlthrusting(self):
        print(f'test TA function: cdlthrusting\n'
              f'===============================')
        res = cdlthrusting(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdltristar(self):
        print(f'test TA function: cdltristar\n'
              f'=============================')
        res = cdltristar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlunique3river(self):
        print(f'test TA function: cdlunique3river\n'
              f'==================================')
        res = cdlunique3river(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlupsidegap2crows(self):
        print(f'test TA function: cdlupsidegap2crows\n'
              f'=====================================')
        res = cdlupsidegap2crows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlxsidegap3methods(self):
        print(f'test TA function: cdlxsidegap3methods\n'
              f'======================================')
        res = cdlxsidegap3methods(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_beta(self):
        print(f'test TA function: beta\n'
              f'=======================')
        res = beta(self.high, self.low)
        print(f'result is \n{res}')

    def test_correl(self):
        print(f'test TA function: correl\n'
              f'=========================')
        res = correl(self.high, self.low)
        print(f'result is \n{res}')

    def test_linearreg(self):
        print(f'test TA function: linearreg\n'
              f'============================')
        res = linearreg(self.close)
        print(f'result is \n{res}')

    def test_linearreg_angle(self):
        print(f'test TA function: linearreg_angle\n'
              f'==================================')
        res = linearreg_angle(self.close)
        print(f'result is \n{res}')

    def test_linearreg_intercept(self):
        print(f'test TA function: linearreg_intercept\n'
              f'======================================')
        res = linearreg_intercept(self.close)
        print(f'result is \n{res}')

    def test_linearreg_slope(self):
        print(f'test TA function: linearreg_slope\n'
              f'==================================')
        res = linearreg_slope(self.close)
        print(f'result is \n{res}')

    def test_stddev(self):
        print(f'test TA function: stddev\n'
              f'=========================')
        res = stddev(self.close)
        print(f'result is \n{res}')

    def test_tsf(self):
        print(f'test TA function: tsf\n'
              f'======================')
        res = tsf(self.close)
        print(f'result is \n{res}')

    def test_var(self):
        print(f'test TA function: var\n'
              f'======================')
        res = var(self.close)
        print(f'result is \n{res}')

    def test_acos(self):
        print(f'test TA function: acos\n'
              f'=======================')
        res = acos(self.close)
        print(f'result is \n{res}')

    def test_asin(self):
        print(f'test TA function: asin\n'
              f'=======================')
        res = asin(self.close / 10)
        print(f'result is \n{res}')

    def test_atan(self):
        print(f'test TA function: atan\n'
              f'=======================')
        res = atan(self.close)
        print(f'result is \n{res}')

    def test_ceil(self):
        print(f'test TA function: ceil\n'
              f'=======================')
        res = ceil(self.close)
        print(f'result is \n{res}')

    def test_cos(self):
        print(f'test TA function: cos\n'
              f'======================')
        res = cos(self.close)
        print(f'result is \n{res}')

    def test_cosh(self):
        print(f'test TA function: cosh\n'
              f'=======================')
        res = cosh(self.close)
        print(f'result is \n{res}')

    def test_exp(self):
        print(f'test TA function: exp\n'
              f'======================')
        res = exp(self.close)
        print(f'result is \n{res}')

    def test_floor(self):
        print(f'test TA function: floor\n'
              f'========================')
        res = floor(self.close)
        print(f'result is \n{res}')

    def test_ln(self):
        print(f'test TA function: ln\n'
              f'=====================')
        res = ln(self.close)
        print(f'result is \n{res}')

    def test_log10(self):
        print(f'test TA function: log10\n'
              f'========================')
        res = log10(self.close)
        print(f'result is \n{res}')

    def test_sin(self):
        print(f'test TA function: sin\n'
              f'======================')
        res = sin(self.close)
        print(f'result is \n{res}')

    def test_sinh(self):
        print(f'test TA function: sinh\n'
              f'=======================')
        res = sinh(self.close)
        print(f'result is \n{res}')

    def test_sqrt(self):
        print(f'test TA function: sqrt\n'
              f'=======================')
        res = sqrt(self.close)
        print(f'result is \n{res}')

    def test_tan(self):
        print(f'test TA function: tan\n'
              f'======================')
        res = tan(self.close)
        print(f'result is \n{res}')

    def test_tanh(self):
        print(f'test TA function: tanh\n'
              f'=======================')
        res = tanh(self.close)
        print(f'result is \n{res}')

    def test_add(self):
        print(f'test TA function: add\n'
              f'======================')
        res = add(self.high, self.low)
        print(f'result is \n{res}')

    def test_div(self):
        print(f'test TA function: div\n'
              f'======================')
        res = div(self.high, self.low)
        print(f'result is \n{res}')

    def test_max(self):
        print(f'test TA function: max\n'
              f'======================')
        res = max(self.close)
        print(f'result is \n{res}')

    def test_maxindex(self):
        print(f'test TA function: maxindex\n'
              f'===========================')
        res = maxindex(self.close)
        print(f'result is \n{res}')

    def test_min(self):
        print(f'test TA function: min\n'
              f'======================')
        res = min(self.close)
        print(f'result is \n{res}')

    def test_minindex(self):
        print(f'test TA function: minindex\n'
              f'===========================')
        res = minindex(self.close)
        print(f'result is \n{res}')

    def test_minmax(self):
        print(f'test TA function: minmax\n'
              f'=========================')
        min, max = minmax(self.close)
        print(f'results are:\nmin:\n{min}\nmax:\n{max}')

    def test_minmaxindex(self):
        print(f'test TA function: minmaxindex\n'
              f'==============================')
        minidx, maxidx = minmaxindex(self.close)
        print(f'results are:\nmin index:\n{minidx}\nmax index:\n{maxidx}')

    def test_mult(self):
        print(f'test TA function: mult\n'
              f'=======================')
        res = mult(self.high, self.low)
        print(f'result is \n{res}')

    def test_sub(self):
        print(f'test TA function: sub\n'
              f'======================')
        res = sub(self.high, self.low)
        print(f'result is \n{res}')

    def test_sum(self):
        print(f'test TA function: sum\n'
              f'======================')
        res = sum(self.close)
        print(f'result is \n{res}')


class TestQT(unittest.TestCase):
    """对qteasy系统进行总体测试"""

    def setUp(self):
        self.op = qt.Operator(strategies=['dma', 'macd'])
        print('  START TO TEST QT GENERAL OPERATIONS\n'
              '=======================================')
        self.op.set_parameter('dma', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('macd', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        self.op.signal_type = 'pt'

        qt.configure(reference_asset='000300.SH',
                     mode=1,
                     ref_asset_type='I',
                     asset_pool='000300.SH',
                     asset_type='I',
                     opti_output_count=50,
                     invest_start='20070110',
                     trade_batch_size=0,
                     parallel=True)

        timing_pars1 = (165, 191, 23)
        timing_pars2 = {'000100': (77, 118, 144),
                        '000200': (75, 128, 138),
                        '000300': (73, 120, 143)}
        timing_pars3 = (115, 197, 54)
        self.op.set_blender('ls', 'pos-2')
        self.op.set_parameter(stg_id='dma', pars=timing_pars1)
        self.op.set_parameter(stg_id='macd', pars=timing_pars3)

    def test_configure(self):
        """测试参数设置
            通过configure设置参数
            通过QR_CONFIG直接设置参数
            设置不存在的参数时报错
            设置不合法参数时报错
            参数设置后可以重用

        """
        config = qt.QT_CONFIG
        self.assertEqual(config.mode, 1)
        qt.configure(mode=2)
        self.assertEqual(config.mode, 2)
        self.assertEqual(qt.QT_CONFIG.mode, 2)

    def test_configuration(self):
        """ 测试CONFIG的显示"""
        print(f'configuration without argument\n')
        qt.configuration()
        print(f'configuration with level=1\n')
        qt.configuration(level=1)
        print(f'configuration with level2\n')
        qt.configuration(level=2)
        print(f'configuration with level3\n')
        qt.configuration(level=3)
        print(f'configuration with level4\n')
        qt.configuration(level=4)
        print(f'configuration with level=1, up_to=3\n')
        qt.configuration(level=1, up_to=3)
        print(f'configuration with info=True\n')
        qt.configuration(default=True)
        print(f'configuration with info=True, verbose=True\n')
        qt.configuration(default=True, verbose=True)

    def test_run_mode_0(self):
        """测试策略的实时信号生成模式"""
        op = qt.Operator(strategies=['stema'])
        op.set_parameter('stema', pars=(6,))
        qt.QT_CONFIG.mode = 0
        qt.run(op)

    def test_run_mode_1(self):
        """测试策略的回测模式,结果打印但不可视化"""
        qt.configure(mode=1,
                     trade_batch_size=1,
                     visual=False,
                     print_backtest_log=True,
                     invest_cash_dates='20070604', )
        qt.run(self.op)

    def test_run_mode_1_visual(self):
        """测试策略的回测模式，结果可视化但不打印"""
        print(f'test plot with no buy-sell points and position indicators')
        qt.configuration(up_to=1, default=True)
        qt.run(self.op,
               mode=1,
               trade_batch_size=1,
               visual=True,
               print_backtest_log=False,
               buy_sell_points=False,
               show_positions=False,
               invest_cash_dates='20070616')

        print(f'test plot with both buy-sell points and position indicators')
        qt.configuration(up_to=1, default=True)
        qt.run(self.op,
               mode=1,
               trade_batch_size=1,
               visual=True,
               print_backtest_log=False,
               buy_sell_points=True,
               show_positions=True,
               invest_cash_dates='20070604')

    def test_run_mode_2_montecarlo(self):
        """测试策略的优化模式，使用蒙特卡洛寻优"""
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='single',
               test_type='single',
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in Montecarlo algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='single',
               test_type='single',
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in Montecarlo with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='multiple',
               test_type='single',
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in Montecarlo with multiple sub-idx_range testing')
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='multiple',
               test_type='multiple',
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)

    def test_run_mode_2_montecarlo_visual(self):
        """测试策略的优化模式，使用蒙特卡洛寻优"""
        print(f'strategy optimization in Montecarlo algorithm with parallel ON')
        qt.configuration(up_to=1, default=True)
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='single',
               test_type='single',
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20140601',
               opti_cash_dates='20060407',
               test_start='20120604',
               test_end='20201130',
               test_cash_dates='20140604',
               test_indicators='years,fv,return,mdd,v,ref,alpha,beta,sharp,info',
               # 'years,fv,return,mdd,v,ref,alpha,beta,sharp,info'
               indicator_plot_type='violin',
               parallel=True,
               visual=True)
        qt.configuration(up_to=1, default=True)

    def test_run_mode_2_grid(self):
        """测试策略的优化模式，使用网格寻优"""
        print(f'strategy optimization in grid search algorithm with parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='single',
               test_type='single',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in grid search algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='single',
               test_type='single',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='multiple',
               test_type='single',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='multiple',
               test_type='multiple',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)

    def test_run_mode_2_grid_visual(self):
        """测试策略的优化模式，使用网格寻优"""
        print(f'strategy optimization in grid search algorithm with parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='single',
               test_type='single',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=False,
               visual=True,
               indicator_plot_type=0)
        print(f'strategy optimization in grid search algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='single',
               test_type='single',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True,
               indicator_plot_type=1)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='multiple',
               test_type='single',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True,
               indicator_plot_type=2)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=0,
               opti_type='multiple',
               test_type='multiple',
               opti_grid_size=128,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True,
               indicator_plot_type=3)

    def test_run_mode_2_incremental(self):
        """测试策略的优化模式，使用递进步长蒙特卡洛寻优"""
        print(f'strategy optimization in incremental algorithm with parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=10,
               opti_min_volume=5E7,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in incremental algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in incremental with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_type='multiple',
               test_type='single',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in incremental with multiple sub-idx_range testing')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_type='multiple',
               test_type='multiple',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)

    def test_run_mode_2_incremental_visual(self):
        """测试策略的优化模式，使用递进步长蒙特卡洛寻优，结果以图表输出"""
        print(f'strategy optimization in incremental algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True)
        print(f'strategy optimization in incremental with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_type='multiple',
               test_type='single',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True)

    def test_run_mode_2_predict(self):
        """测试策略的优化模式，使用蒙特卡洛预测方法评价优化结果"""
        print(f'strategy optimization in montecarlo algorithm with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='single',
               test_type='montecarlo',
               opti_output_count=20,
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in incremental with with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_type='single',
               test_type='montecarlo',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=False)

    def test_run_mode_2_predict_visual(self):
        """测试策略的优化模式，使用蒙特卡洛预测方法评价优化结果，结果以图表方式输出"""
        print(f'strategy optimization in montecarlo algorithm with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method=1,
               opti_type='single',
               test_type='montecarlo',
               opti_output_count=20,
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True)
        print(f'strategy optimization in incremental with with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method=2,
               opti_type='single',
               test_type='montecarlo',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20060404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20201130',
               parallel=True,
               visual=True)

    def test_built_in_timing(self):
        """测试内置的择时策略"""

    def test_multi_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        op = qt.Operator(strategies=['long', 'finance', 'ricon_none'])
        all_shares = stock_basic()
        shares_banking = qt.get_stock_pool(date='20070101', industry='银行')
        print('extracted banking share pool:')
        print(all_shares.loc[all_shares['ts_code'].isin(shares_banking)])
        shares_estate = list((all_shares.loc[all_shares.industry == "全国地产"]['ts_code']).values)
        qt.configure(asset_pool=shares_banking[0:10],
                     asset_type='E',
                     reference_asset='000300.SH',
                     ref_asset_type='I',
                     opti_output_count=50,
                     invest_start='20070101',
                     invest_end='20181231',
                     invest_cash_dates=None,
                     trade_batch_size=1.,
                     mode=1,
                     log=False)
        op.set_parameter('long', pars=())
        op.set_parameter('finance', pars=(True, 'proportion', 'greater', 0, 0, 0.4),
                         sample_freq='Q',
                         data_types='basic_eps',
                         sort_ascending=True,
                         weighting='proportion',
                         condition='greater',
                         ubound=0,
                         lbound=0,
                         _poq=0.4)
        op.set_parameter('ricon_none', pars=())
        op.set_blender('ls', 'avg')
        op.info()
        print(f'test portfolio selecting from shares_estate: \n{shares_estate}')
        qt.configuration()
        qt.run(op, visual=True, trade_batch_size=100)
        qt.run(op, visual=False, print_backtest_log=True, trade_batch_size=100)

    def test_many_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        print(f'test portfolio selection from large quantities of shares')
        op = qt.Operator(strategies=['long', 'finance', 'ricon_none'])
        qt.configure(asset_pool=qt.get_stock_pool(date='20070101',
                                                  industry=['银行', '全国地产', '互联网', '环境保护', '区域地产',
                                                            '酒店餐饮', '运输设备', '综合类', '建筑工程', '玻璃',
                                                            '家用电器', '文教休闲', '其他商业', '元器件', 'IT设备',
                                                            '其他建材', '汽车服务', '火力发电', '医药商业', '汽车配件',
                                                            '广告包装', '轻工机械', '新型电力', '多元金融', '饲料',
                                                            '铜', '普钢', '航空', '特种钢',
                                                            '种植业', '出版业', '焦炭加工', '啤酒', '公路', '超市连锁',
                                                            '钢加工', '渔业', '农用机械', '软饮料', '化工机械', '塑料',
                                                            '红黄酒', '橡胶', '家居用品', '摩托车', '电器仪表', '服饰',
                                                            '仓储物流', '纺织机械', '电器连锁', '装修装饰', '半导体',
                                                            '电信运营', '石油开采', '乳制品', '商品城', '公共交通',
                                                            '陶瓷', '船舶'],
                                                  area=['深圳', '北京', '吉林', '江苏', '辽宁', '广东',
                                                        '安徽', '四川', '浙江', '湖南', '河北', '新疆',
                                                        '山东', '河南', '山西', '江西', '青海', '湖北',
                                                        '内蒙', '海南', '重庆', '陕西', '福建', '广西',
                                                        '上海']),
                     asset_type='E',
                     reference_asset='000300.SH',
                     ref_asset_type='I',
                     opti_output_count=50,
                     invest_start='20070101',
                     invest_end='20171228',
                     invest_cash_dates=None,
                     trade_batch_size=1.,
                     mode=1,
                     log=False,
                     hist_dnld_parallel=0)
        print(f'in total a number of {len(qt.QT_CONFIG.asset_pool)} shares are selected!')
        op.set_parameter('long', pars=())
        op.set_parameter('finance', pars=(True, 'proportion', 'greater', 0, 0, 30),
                         sample_freq='Q',
                         data_types='basic_eps',
                         sort_ascending=True,
                         weighting='proportion',
                         condition='greater',
                         ubound=0,
                         lbound=0,
                         _poq=30)
        op.set_parameter('ricon_none', pars=())
        op.set_blender('ls', 'avg')
        qt.run(op, visual=True, print_backtest_log=True)


class TestVisual(unittest.TestCase):
    """ Test the visual effects and charts

    """

    def test_ohlc(self):
        print(f'test mpf plot in ohlc form')
        qt.ohlc(stock='513100.SH', start='2020-04-01', asset_type='FD', no_visual=False)
        print(f'get data from mpf plot function')
        daily = qt.ohlc('513100.SH', start='2020-04-01', asset_type='FD', no_visual=False)
        daily.drop(columns=['volume'], inplace=True)
        print(f'test plot mpf data directly from DataFrame without volume')
        qt.ohlc(stock_data=daily, no_visual=False)

    def test_candle(self):
        print(f'test mpf plot in candle form')
        self.data = qt.candle('513100.SH', start='2020-12-01', asset_type='FD')
        # print(f'get data from mpf plot function for adj = "none"')
        # qt.candle('000002.SZ', start='2018-12-01', end='2019-03-31', asset_type='E', adj='none')
        # print(f'get data from mpf plot function for adj = "hfq"')
        # qt.candle('600000.SH', start='2018-12-01', end='2019-03-31', asset_type='E', adj='hfq')
        print(f'test plot mpf data with indicator macd')
        qt.candle(stock_data=self.data, indicator='macd', indicator_par=(12, 26, 9))

    def test_renko(self):
        print(f'test mpf plot in renko form')
        qt.renko('513100.SH', start='2020-04-01', asset_type='FD', no_visual=True)
        print(f'get data from mpf plot function')
        daily = qt.renko('513100.SH', start='2020-04-01', asset_type='FD', no_visual=True)
        daily.drop(columns=['volume'], inplace=True)
        print(f'test plot mpf data directly from DataFrame without volume')
        qt.renko(stock_data=daily, no_visual=True)

    def test_indicators(self):
        print(f'test mpf plot in candle form with indicator dema')
        qt.candle('513100.SH', start='2020-04-01', asset_type='FD', indicator='dema', indicator_par=(20,))
        print(f'test mpf plot in candle form with indicator rsi')
        qt.candle('513100.SH', start='2020-04-01', asset_type='FD', indicator='rsi', indicator_par=(12,))
        print(f'test mpf plot in candle form with indicator macd')
        qt.candle('513100.SH', start='2020-04-01', asset_type='FD', indicator='macd', indicator_par=(12, 26, 9))
        print(f'test mpf plot in candle form with indicator bbands')
        qt.candle('513100.SH', start='2020-04-01', asset_type='FD', indicator='bbands', indicator_par=(12, 26, 9))

    def test_prepare_mpf_data(self):
        """

        :return:
        """


class TestBuiltIns(unittest.TestCase):
    """Test all built-in strategies

    """

    def setUp(self):
        qt.configure(invest_start='20200113',
                     invest_end='20210413',
                     asset_pool='000300.SH',
                     asset_type='I',
                     reference_asset='000300.SH',
                     opti_sample_count=100)

    def test_crossline(self):
        op = qt.Operator(strategies=['crossline'])
        op.set_parameter(0, pars=(35, 120, 10, 'buy'))
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1, invest_start='20080103', allow_sell_short=True)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20080103')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        # qt.run(op, mode=2, invest_start='20080103')

    def test_macd(self):
        op = qt.Operator(strategies=['macd'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dma(self):
        op = qt.Operator(strategies=['dma'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1, allow_sell_short=True)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_trix(self):
        op = qt.Operator(strategies=['trix'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_cdl(self):
        op = qt.Operator(strategies=['cdl'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        # built-in cdl is not optimizable

    def test_ssma(self):
        op = qt.Operator(strategies=['ssma'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sdema(self):
        op = qt.Operator(strategies=['sdema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sema(self):
        op = qt.Operator(strategies=['sema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sht(self):
        op = qt.Operator(strategies=['sht'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        # built-in strategy sht is not optimizable

    def test_skama(self):
        op = qt.Operator(strategies=['skama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_smama(self):
        op = qt.Operator(strategies=['smama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sfama(self):
        op = qt.Operator(strategies=['sfama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_st3(self):
        op = qt.Operator(strategies=['st3'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_stema(self):
        op = qt.Operator(strategies=['stema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_strima(self):
        op = qt.Operator(strategies=['strima'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_swma(self):
        op = qt.Operator(strategies=['swma'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dsma(self):
        op = qt.Operator(strategies=['dsma'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_ddema(self):
        op = qt.Operator(strategies=['ddema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dema(self):
        op = qt.Operator(strategies=['dema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dkama(self):
        op = qt.Operator(strategies=['dkama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dmama(self):
        op = qt.Operator(strategies=['dmama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dfama(self):
        op = qt.Operator(strategies=['dfama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dt3(self):
        op = qt.Operator(strategies=['dt3'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dtema(self):
        op = qt.Operator(strategies=['dtema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dtrima(self):
        op = qt.Operator(strategies=['dtrima'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dwma(self):
        op = qt.Operator(strategies=['dwma'])
        op.set_parameter(0, pars=(200, 22))
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slsma(self):
        op = qt.Operator(strategies=['slsma'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sldema(self):
        op = qt.Operator(strategies=['sldema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slema(self):
        op = qt.Operator(strategies=['slema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slht(self):
        op = qt.Operator(strategies=['slht'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        # built-in strategy slht is not optimizable

    def test_slkama(self):
        op = qt.Operator(strategies=['slkama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slmama(self):
        op = qt.Operator(strategies=['slmama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slfama(self):
        op = qt.Operator(strategies=['slfama'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slt3(self):
        op = qt.Operator(strategies=['slt3'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sltema(self):
        op = qt.Operator(strategies=['sltema'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sltrima(self):
        op = qt.Operator(strategies=['sltrima'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slwma(self):
        op = qt.Operator(strategies=['slwma'])
        op.set_parameter(0, opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)


class FastExperiments(unittest.TestCase):
    """This test case is created to have experiments done that can be quickly called from Command line"""

    def setUp(self):
        pass

    def test_fast_experiments(self):
        op = qt.Operator(strategies=[MyStg()], signal_type='pt')
        op.set_parameter(0, (25, 123, 0.01))
        qt.run(op, mode=1, invest_start='20080101', allow_sell_short=True, print_backtest_log=False)


# noinspection SqlDialectInspection,PyTypeChecker
class TestDataBase(unittest.TestCase):
    """test local historical file database management methods"""

    def setUp(self):
        from qteasy import QT_ROOT_PATH
        self.qt_root_path = QT_ROOT_PATH
        self.ds_db = DataSource('db',
                                host='localhost',
                                port=3306,
                                user='jackie',
                                password='iama007',
                                db='test_db')
        self.ds_csv = DataSource('file', file_type='csv')
        self.ds_hdf = DataSource('file', file_type='hdf')
        self.ds_fth = DataSource('file', file_type='fth')
        self.df = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'trade_date': ['20211112', '20211112', '20211112', '20211112', '20211112',
                           '20211113', '20211113', '20211113', '20211113', '20211113'],
            'open':       [1., 2., 3., 4., 5., 6., 7., 8., 9., 10.],
            'high':       [2., 3., 4., 5., 6., 7., 8., 9., 10., 1.],
            'low':        [3., 4., 5., 6., 7., 8., 9., 10., 1., 2.],
            'close':      [4., 5., 6., 7., 8., 9., 10., 1., 2., 3.]
        })
        # 以下df_add中的数据大部分主键与df相同，但有四行不同，主键与df相同的行数据与df不同，用于测试新增及更新
        self.df_add = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000006.SZ', '000007.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000006.SZ', '000007.SZ'],
            'trade_date': ['20211112', '20211112', '20211112', '20211112', '20211112',
                           '20211113', '20211113', '20211113', '20211113', '20211113'],
            'open':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'high':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'low':        [10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'close':      [10., 10., 10., 10., 10., 10., 10., 10., 10., 10.]
        })
        # 以下df_res中的数据是更新后的结果
        self.df_res = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000001.SZ', '000002.SZ', '000002.SZ', '000003.SZ', '000003.SZ', '000004.SZ',
                           '000004.SZ', '000005.SZ', '000005.SZ', '000006.SZ', '000006.SZ', '000007.SZ', '000007.SZ'],
            'trade_date': ['20211112', '20211113', '20211112', '20211113', '20211112', '20211113', '20211112',
                           '20211113', '20211112', '20211113', '20211112', '20211113', '20211112', '20211113'],
            'open':       [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 4.0, 9.0, 5.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            'high':       [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 5.0, 10.0, 6.0, 1.0, 10.0, 10.0, 10.0, 10.0],
            'low':        [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 6.0, 1.0, 7.0, 2.0, 10.0, 10.0, 10.0, 10.0],
            'close':      [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 7.0, 2.0, 8.0, 3.0, 10.0, 10.0, 10.0, 10.0]
        })
        self.df2 = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000006.SZ', '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ'],
            'name':       ['name1', 'name2', 'name3', 'name4', 'name5', 'name6', 'name7', 'name8', 'name9', 'name10'],
            'industry':   ['industry1', 'industry2', 'industry3', 'industry4', 'industry5',
                           'industry6', 'industry7', 'industry8', 'industry9', 'industry10'],
            'area':       ['area1', 'area2', 'area3', 'area4', 'area5', 'area6', 'area7', 'area8', 'area9', 'area10'],
            'market':     ['market1', 'market2', 'market3', 'market4', 'market5',
                           'market6', 'market7', 'market8', 'market9', 'market10']
        })
        # 以下df用于测试写入/读出/新增修改系统内置标准数据表
        self.built_in_df = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'trade_date': ['20211112', '20211112', '20211112', '20211112', '20211112',
                           '20211113', '20211113', '20211113', '20211113', '20211113',
                           '20211114', '20211114', '20211114', '20211114', '20211114'],
            'open':       [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 6., 7., 8., 9., 10.],
            'high':       [2., 3., 4., 5., 6., 7., 8., 9., 10., 1., 7., 8., 9., 10., 1.],
            'low':        [3., 4., 5., 6., 7., 8., 9., 10., 1., 2., 8., 9., 10., 1., 2.],
            'close':      [4., 5., 6., 7., 8., 9., 10., 1., 2., 3., 9., 10., 1., 2., 3.],
            'pre_close':  [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 6., 7., 8., 9., 10.],
            'change':     [2., 3., 4., 5., 6., 7., 8., 9., 10., 1., 7., 8., 9., 10., 1.],
            'pct_chg':    [3., 4., 5., 6., 7., 8., 9., 10., 1., 2., 8., 9., 10., 1., 2.],
            'vol':        [4., 5., 6., 7., 8., 9., 10., 1., 2., 3., 9., 10., 1., 2., 3.],
            'amount':     [4., 5., 6., 7., 8., 9., 10., 1., 2., 3., 9., 10., 1., 2., 3.]
        })
        # 以下df用于测试新增数据写入/读出系统内置标准数据表，与第一次写入表中的数据相比，部分数据的
        # 主键与第一次相同，大部分主键不同。主键相同的数据中，价格与原来的值不同。
        # 正确的输出应该确保写入本地表的数据中不含重复的主键，用户可以选择用新的数据替换已有数据，或
        # 者忽略新的数据
        self.built_in_add_df = pd.DataFrame({
            'ts_code':    ['000006.SZ', '000007.SZ', '000008.SZ', '000004.SZ', '000005.SZ',
                           '000006.SZ', '000007.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'trade_date': ['20211115', '20211115', '20211115', '20211115', '20211115',
                           '20211116', '20211116', '20211116', '20211116', '20211116',
                           '20211114', '20211114', '20211114', '20211114', '20211114'],
            'open':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'high':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'low':        [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'close':      [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'pre_close':  [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'change':     [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'pct_chg':    [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'vol':        [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'amount':     [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.]
        })

    def test_primary_key_manipulate(self):
        """ test manipulating DataFrame primary key as indexes and frames
            with testing functions:
                set_primary_key_index() and,
                set_primary_key_frame()
        """
        print(f'df before converting primary keys to index:\n{self.df}')
        set_primary_key_index(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'date'])

        print(f'df after converting primary keys to index:\n{self.df}')
        self.assertEqual(list(self.df.index.names), ['ts_code', 'trade_date'])
        self.assertEqual(self.df.index[0], ('000001.SZ', Timestamp('2021-11-12 00:00:00')))
        self.assertEqual(self.df.columns.to_list(), ['open', 'high', 'low', 'close'])

        res = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'date'])
        print(f'df after converting primary keys to frame:\n{res}')
        self.assertEqual(list(res.index.names), [None])
        self.assertEqual(res.ts_code[0], '000001.SZ')
        self.assertEqual(res.trade_date[0], Timestamp('2021-11-12 00:00:00'))
        self.assertEqual(res.columns.to_list(), ['ts_code', 'trade_date', 'open', 'high', 'low', 'close'])

        print(f'df2 before converting primary keys to index:\n{self.df2}')
        set_primary_key_index(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])

        print(f'df2 after converting primary keys to index:\n{self.df2}')
        self.assertEqual(list(self.df2.index.names), ['ts_code'])
        self.assertEqual(self.df2.index[0], '000001.SZ')
        self.assertEqual(self.df2.columns.to_list(), ['name', 'industry', 'area', 'market'])

        res = set_primary_key_frame(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])
        print(f'df2 after converting primary keys to frame:\n{res}')
        self.assertEqual(list(res.index.names), [None])
        self.assertEqual(res.ts_code[0], '000001.SZ')
        self.assertEqual(res.columns.to_list(), ['ts_code', 'name', 'industry', 'area', 'market'])

    def test_datasource_creation(self):
        """ test creation of all kinds of data sources"""
        self.assertIsInstance(self.ds_db, DataSource)
        self.assertIs(self.ds_db.file_type, None)
        self.assertIs(self.ds_db.file_path, None)

        self.assertIsInstance(self.ds_csv, DataSource)
        self.assertEqual(self.ds_csv.file_type, 'csv')
        self.assertEqual(self.ds_csv.file_path, self.qt_root_path + 'qteasy/data/')
        self.assertIs(self.ds_csv.engine, None)

        self.assertIsInstance(self.ds_hdf, DataSource)
        self.assertEqual(self.ds_hdf.file_type, 'hdf')
        self.assertEqual(self.ds_hdf.file_path, self.qt_root_path + 'qteasy/data/')
        self.assertIs(self.ds_hdf.engine, None)

        self.assertIsInstance(self.ds_fth, DataSource)
        self.assertEqual(self.ds_fth.file_type, 'fth')
        self.assertEqual(self.ds_fth.file_path, self.qt_root_path + 'qteasy/data/')
        self.assertIs(self.ds_fth.engine, None)

    def test_file_manipulates(self):
        """ test DataSource method file_exists and drop_file"""
        print(f'returning True while source type is database')
        self.assertTrue(self.ds_db.file_exists('basic_eps.dat'))

        print(f'test file that existed')
        f_name = self.ds_csv.file_path + 'test_file.csv'
        with open(f_name, 'w') as f:
            f.write('a test csv file')
        self.assertTrue(self.ds_csv.file_exists('test_file'))
        self.ds_csv.drop_file('test_file')
        self.assertFalse(self.ds_csv.file_exists('test_file'))

        f_name = self.ds_hdf.file_path + 'test_file.hdf'
        with open(f_name, 'w') as f:
            f.write('a test csv file')
        self.assertTrue(self.ds_hdf.file_exists('test_file'))
        self.ds_hdf.drop_file('test_file')
        self.assertFalse(self.ds_hdf.file_exists('test_file'))

        f_name = self.ds_fth.file_path + 'test_file.fth'
        with open(f_name, 'w') as f:
            f.write('a test csv file')
        self.assertTrue(self.ds_fth.file_exists('test_file'))
        self.ds_fth.drop_file('test_file')
        self.assertFalse(self.ds_fth.file_exists('test_file'))

        print(f'test file that does not exist')
        # 事先删除可能存在于磁盘上的文件，并判断是否存在
        import os
        f_name = self.ds_csv.file_path + "file_that_does_not_exist.csv"
        try:
            os.remove(f_name)
        except:
            pass
        f_name = self.ds_hdf.file_path + "file_that_does_not_exist.hdf"
        try:
            os.remove(f_name)
        except:
            pass
        f_name = self.ds_fth.file_path + "file_that_does_not_exist.fth"
        try:
            os.remove(f_name)
        except:
            pass
        self.assertFalse(self.ds_csv.file_exists('file_that_does_not_exist'))
        self.assertFalse(self.ds_hdf.file_exists('file_that_does_not_exist'))
        self.assertFalse(self.ds_fth.file_exists('file_that_does_not_exist'))

    def test_db_table_operates(self):
        """ test all database operation functions"""
        self.ds_db.drop_db_table('new_test_table')
        self.assertFalse(self.ds_db.db_table_exists('new_test_table'))

        print(f'test function creating new table')
        self.ds_db.new_db_table('new_test_table',
                                ['ts_code', 'trade_date', 'col1', 'col2'],
                                ['varchar(9)', 'varchar(9)', 'int', 'int'],
                                ['ts_code', 'trade_date'])
        self.ds_db.db_table_exists('new_test_table')

        sql = f"SELECT COLUMN_NAME, DATA_TYPE " \
              f"FROM INFORMATION_SCHEMA.COLUMNS " \
              f"WHERE TABLE_SCHEMA = Database() " \
              f"AND table_name = 'new_test_table'"
        self.ds_db.cursor.execute(sql)
        results = self.ds_db.cursor.fetchall()
        # 为了方便，将cur_columns和new_columns分别包装成一个字典
        test_columns = {}
        for col, typ in results:
            test_columns[col] = typ
        self.assertEqual(list(test_columns.keys()), ['ts_code', 'trade_date', 'col1', 'col2'])
        self.assertEqual(list(test_columns.values()), ['varchar', 'varchar', 'int', 'int'])

        self.ds_db.alter_db_table('new_test_table',
                                  ['ts_code', 'col1', 'col2', 'col3', 'col4'],
                                  ['varchar(9)', 'float', 'float', 'int', 'float'],
                                  ['ts_code'])
        sql = f"SELECT COLUMN_NAME, DATA_TYPE " \
              f"FROM INFORMATION_SCHEMA.COLUMNS " \
              f"WHERE TABLE_SCHEMA = Database() " \
              f"AND table_name = 'new_test_table'"
        self.ds_db.cursor.execute(sql)
        results = self.ds_db.cursor.fetchall()
        # 为了方便，将cur_columns和new_columns分别包装成一个字典
        test_columns = {}
        for col, typ in results:
            test_columns[col] = typ
        self.assertEqual(list(test_columns.keys()), ['ts_code', 'col1', 'col2', 'col3', 'col4'])
        self.assertEqual(list(test_columns.values()), ['varchar', 'float', 'float', 'int', 'float'])

        self.ds_db.drop_db_table('new_test_table')

    def test_write_and_read_file(self):
        """ test DataSource method write_file and read_file"""
        print(f'write and read a MultiIndex dataframe to all types of local sources')
        df = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        set_primary_key_index(df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        print(f'following dataframe with multiple index will be written to disk in all formats:\n'
              f'{df}')
        self.ds_csv.write_file(df, 'test_csv_file')
        self.assertTrue(self.ds_csv.file_exists('test_csv_file'))
        loaded_df = self.ds_csv.read_file('test_csv_file',
                                          primary_key=['ts_code', 'trade_date'],
                                          pk_dtypes=['str', 'TimeStamp'])
        saved_index = df.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        self.assertTrue(np.allclose(saved_values, loaded_values))
        self.assertEqual(list(df.columns), list(loaded_df.columns))

        self.ds_hdf.write_file(df, 'test_hdf_file')
        self.assertTrue(self.ds_hdf.file_exists('test_hdf_file'))
        loaded_df = self.ds_hdf.read_file('test_hdf_file',
                                          primary_key=['ts_code', 'trade_date'],
                                          pk_dtypes=['str', 'TimeStamp'])
        saved_index = df.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved hdf file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        self.assertTrue(np.allclose(saved_values, loaded_values))
        self.assertEqual(list(df.columns), list(loaded_df.columns))

        self.ds_fth.write_file(df, 'test_fth_file')
        self.assertTrue(self.ds_fth.file_exists('test_fth_file'))
        loaded_df = self.ds_fth.read_file('test_fth_file',
                                          primary_key=['ts_code', 'trade_date'],
                                          pk_dtypes=['str', 'TimeStamp'])
        saved_index = df.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved feather file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        self.assertTrue(np.allclose(saved_values, loaded_values))
        self.assertEqual(list(df.columns), list(loaded_df.columns))

        # test writing and reading Single Index dataframe to local files
        print(f'write and read a MultiIndex dataframe to all types of local files')
        df2 = set_primary_key_frame(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])
        set_primary_key_index(df2, primary_key=['ts_code'], pk_dtypes=['str'])
        print(f'following dataframe with multiple index will be written to disk in all formats:\n'
              f'{df2}')
        self.ds_csv.write_file(df2, 'test_csv_file2')
        self.assertTrue(self.ds_csv.file_exists('test_csv_file2'))
        loaded_df = self.ds_csv.read_file('test_csv_file2',
                                          primary_key=['ts_code'],
                                          pk_dtypes=['str'])
        saved_index = df2.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(df2.columns), list(loaded_df.columns))

        self.ds_hdf.write_file(df2, 'test_hdf_file2')
        self.assertTrue(self.ds_hdf.file_exists('test_hdf_file2'))
        loaded_df = self.ds_hdf.read_file('test_hdf_file2',
                                          primary_key=['ts_code'],
                                          pk_dtypes=['str'])
        saved_index = df2.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved hdf file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(df2.columns), list(loaded_df.columns))

        self.ds_fth.write_file(df2, 'test_fth_file2')
        self.assertTrue(self.ds_fth.file_exists('test_fth_file2'))
        loaded_df = self.ds_fth.read_file('test_fth_file2',
                                          primary_key=['ts_code'],
                                          pk_dtypes=['str'])
        saved_index = df2.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved feather file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(df2.columns), list(loaded_df.columns))

    def test_write_and_read_database(self):
        """ test DataSource method read_database and write_database"""
        print(f'write and read a MultiIndex dataframe to database')
        df = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        print(f'following dataframe with multiple index will be written to local database:\n'
              f'{df}')
        con = self.ds_db.con
        cursor = self.ds_db.cursor
        TABLE_NAME = 'test_db_table'
        # 删除数据库中的临时表
        sql = f"DROP TABLE IF EXISTS {TABLE_NAME}"
        cursor.execute(sql)
        con.commit()
        # 为确保update顺利进行，建立新表并设置primary_key

        self.ds_db.write_database(df, TABLE_NAME)
        loaded_df = self.ds_db.read_database(TABLE_NAME)
        saved_index = df.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'retrieve whole data table from database\n'
              f'df retrieved from database is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(self.df.columns), list(loaded_df.columns))
        # test reading partial of the datatable
        loaded_df = self.ds_db.read_database(TABLE_NAME,
                                             share_like_pk='ts_code',
                                             shares=["000001.SZ", "000003.SZ"],
                                             date_like_pk='trade_date',
                                             start='20211112',
                                             end='20211112')
        print(f'retrieve partial data table from database with:\n'
              f'shares = ["000001.SZ", "000003.SZ"]\n'
              f'start/end = 20211112/20211112\n'
              f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        saved_index = df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        # 逐一判断读取出来的df的每一行是否正确
        row, col = saved_values.shape
        for j in range(col):
            self.assertEqual(saved_values[0, j], loaded_values[0, j])
            self.assertEqual(saved_values[2, j], loaded_values[1, j])
        self.assertEqual(list(self.df.columns), list(loaded_df.columns))

        print(f'write and read a MultiIndex dataframe to database')
        print(f'following dataframe with multiple index will be written to database:\n'
              f'{self.df2}')
        TABLE_NAME = 'test_db_table2'
        # 删除数据库中的临时表
        sql = f"DROP TABLE IF EXISTS {TABLE_NAME}"
        cursor.execute(sql)
        con.commit()

        self.ds_db.write_database(self.df2, TABLE_NAME)
        loaded_df = self.ds_db.read_database(TABLE_NAME)
        saved_index = self.df2.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(self.df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(self.df2.columns), list(loaded_df.columns))
        # test reading partial of the datatable
        loaded_df = self.ds_db.read_database(TABLE_NAME,
                                             share_like_pk='ts_code',
                                             shares=["000001.SZ", "000003.SZ", "000004.SZ", "000009.SZ", "000005.SZ"])
        print(f'retrieve partial data table from database with:\n'
              f'shares = ["000001.SZ", "000003.SZ", "000004.SZ", "000009.SZ", "000005.SZ"]\n'
              f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        saved_values = np.array(self.df2.values)
        loaded_values = np.array(loaded_df.values)
        # 逐一判断读取出来的df的每一行是否正确
        row, col = saved_values.shape
        for j in range(col):
            self.assertEqual(saved_values[0, j], loaded_values[0, j])
            self.assertEqual(saved_values[2, j], loaded_values[1, j])
            self.assertEqual(saved_values[3, j], loaded_values[2, j])
            self.assertEqual(saved_values[4, j], loaded_values[3, j])
            self.assertEqual(saved_values[8, j], loaded_values[4, j])
        self.assertEqual(list(self.df2.columns), list(loaded_df.columns))

    def test_update_database(self):
        """ test the function update_database()"""
        print(f'update a database table with new data on same primary key')
        df = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        df_add = set_primary_key_frame(self.df_add, primary_key=['ts_code', 'trade_date'],
                                       pk_dtypes=['str', 'TimeStamp'])
        df_res = set_primary_key_frame(self.df_res, primary_key=['ts_code', 'trade_date'],
                                       pk_dtypes=['str', 'TimeStamp'])
        print(f'following dataframe with be written to an empty database table:\n'
              f'{df}\n'
              f'and following dataframe will be used to updated that database table\n'
              f'{df_add}')
        table_name = 'test_db_table'
        # 删除数据库中的临时表
        self.ds_db.drop_table(table_name)
        # 为确保update顺利进行，建立新表并设置primary_key
        self.ds_db.new_db_table(table_name,
                                columns=['ts_code', 'trade_date', 'open', 'high', 'low', 'close'],
                                dtypes=['varchar(9)', 'date', 'float', 'float', 'float', 'float'],
                                primary_key=['ts_code', 'trade_date'])
        self.ds_db.write_database(df, table_name)
        self.ds_db.update_database(df_add, table_name, ['ts_code', 'trade_date'])
        loaded_df = self.ds_db.read_database(table_name)
        saved_index = df_res.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df_res.values)
        loaded_values = np.array(loaded_df.values)
        print(f'retrieve whole data table from database\n'
              f'df retrieved from database is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(self.df.columns), list(loaded_df.columns))

    # noinspection PyPep8Naming
    def test_read_write_update_table_data(self):
        """ test DataSource method read_table_data() and write_table_data()
            will test both built-in tables and user-defined tables

            **WARNING: TABLE WILL BE DELETED! DO NOT run this test on real system!**
            **警告：请不要在工作系统中进行此项测试，数据表将被删除**
        """
        # 测试前删除已经存在的（真实）数据表
        test_table = 'stock_daily'
        all_data_sources = [self.ds_csv, self.ds_hdf, self.ds_fth, self.ds_db]
        for data_source in all_data_sources:
            data_source.drop_table(test_table)
        # 测试写入标准表数据
        for data_source in all_data_sources:
            data_source.write_table_data(self.built_in_df, test_table)

        # 测试完整读出标准表数据
        for data_source in all_data_sources:
            df = data_source.read_table_data(test_table)
            print(f'df read from data source: \n{data_source.source_type}-{data_source.file_type} \nis:\n{df}')

        # 测试读出并筛选部分标准表数据
        for data_source in all_data_sources:
            df = data_source.read_table_data(test_table,
                                             shares=['000001.SZ', '000002.SZ', '000005.SZ', '000007.SZ'],
                                             start='20211113',
                                             end='20211116')
            print(f'df read from data source: \n{data_source.source_type}-{data_source.file_type} \nis:\n{df}')

        # 测试update table数据到本地文件或数据，合并类型为"ignore"
        for data_source in all_data_sources:
            df = data_source.acquire_table_data(test_table, 'df', df=self.built_in_add_df)
            data_source.update_table_data(test_table, df, 'ignore')
            df = data_source.read_table_data(test_table)
            print(f'df read from data source after updating with merge type IGNORE:\n'
                  f'{data_source.source_type}-{data_source.file_type}\n{df}')

        # 测试update table数据到本地文件或数据，合并类型为"update"
        # 测试前删除已经存在的（真实）数据表
        test_table = 'stock_daily'
        all_data_sources = [self.ds_csv, self.ds_hdf, self.ds_fth, self.ds_db]
        for data_source in all_data_sources:
            data_source.drop_table(test_table)
        # 测试写入标准表数据
        for data_source in all_data_sources:
            data_source.write_table_data(self.built_in_df, test_table)
        # 测试写入新增数据并设置合并类型为"update"
        for data_source in all_data_sources:
            df = data_source.acquire_table_data(test_table, 'df', df=self.built_in_add_df)
            data_source.update_table_data(test_table, df, 'update')
            df = data_source.read_table_data(test_table)
            print(f'df read from data source after updating with merge type UPDATE:\n'
                  f'{data_source.source_type}-{data_source.file_type}\n{df}')

        # 测试读出并筛选部分标准表数据
        for data_source in all_data_sources:
            df = data_source.read_table_data(test_table,
                                             shares=['000001.SZ', '000002.SZ', '000005.SZ', '000007.SZ'],
                                             start='20211113',
                                             end='20211116')
            print(f'df read from data source: \n{data_source.source_type}-{data_source.file_type} \nis:\n{df}')

    def test_download_update_table_data(self):
        """ test downloading data from tushare"""
        tables_to_test = {'stock_daily':        {'share': None,
                                                 'trade_date': '20211112'},
                          'stock_weekly':       {'share': None,
                                                 'trade_date': '20211008'},
                          'stock_indicator':    {'shares': None,
                                                 'trade_date': '20211112'},
                          'trade_calendar':     {'exchange': 'SSE'}
                          }
        tables_to_add = {'stock_daily':        {'share': None,
                                                'trade_date': '20211115'},
                         'stock_weekly':       {'share': None,
                                                'trade_date': '20211015'},
                         'stock_indicator':    {'shares': None,
                                                'trade_date': '20211113'},
                         'trade_calendar':     {'exchange': 'SZSE'}
                         }
        all_data_sources = [self.ds_csv, self.ds_hdf, self.ds_fth, self.ds_db]

        for table in tables_to_test:
            # 删除已有的表
            for ds in all_data_sources:
                ds.drop_table(table)
            # 下载并写入数据到表中
            print(f'downloading table data ({table}) with parameter: \n'
                  f'{tables_to_test[table]}')
            df = ds.acquire_table_data(table, 'tushare', 'ignore', **tables_to_test[table])
            print(f'---------- Done! got:---------------\n{df}\n--------------------------------')
            for ds in all_data_sources:
                print(f'updating IGNORE table data ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.file_type}')
                ds.update_table_data(table, df, 'ignore')
                print(f'-- Done! --')

            for ds in all_data_sources:
                print(f'reading table data ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.file_type}')
                if table != 'trade_calendar':
                    df = ds.read_table_data(table, shares=['000001.SZ', '000002.SZ', '000007.SZ', '600067.SH'])
                else:
                    df = ds.read_table_data(table, start='20200101', end='20200301')
                print(f'got data from data source {ds.source_type}-{ds.file_type}:\n{df}')

            # 下载数据并添加到表中
            print(f'downloading table data ({table}) with parameter: \n'
                  f'{tables_to_add[table]}')
            df = ds.acquire_table_data(table, 'tushare', 'ignore', **tables_to_add[table])
            print(f'---------- Done! got:---------------\n{df}\n--------------------------------')
            for ds in all_data_sources:
                print(f'updating UPDATE table data ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.file_type}')
                ds.update_table_data(table, df, 'ignore')
                print(f'-- Done! --')

            for ds in all_data_sources:
                print(f'reading table data ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.file_type}')
                if table != 'trade_calendar':
                    df = ds.read_table_data(table, shares=['000004.SZ', '000005.SZ', '000006.SZ'])
                else:
                    df = ds.read_table_data(table, start='20200101', end='20200301')
                print(f'got data from data source {ds.source_type}-{ds.file_type}:\n{df}')


def test_suite(*args):
    suite = unittest.TestSuite()
    for arg_item in args:
        if arg_item == 'internal':
            suite.addTests(tests=[TestCost(),
                                  TestSpace(),
                                  TestLog(),
                                  TestCashPlan()])
        elif arg_item == 'core':
            suite.addTests(tests=[TestOperator(),
                                  TestLoop(),
                                  TestEvaluations(),
                                  TestBuiltIns()])
        elif arg_item == 'external':
            suite.addTests(tests=[TestQT(),
                                  TestVisual(),
                                  TestTushare(),
                                  TestHistoryPanel()])
    return suite


if __name__ == '__main__':
    unittest.main()