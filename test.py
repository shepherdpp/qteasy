import unittest
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np
import math
from numpy import int64
import itertools
import datetime

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, time_str_format, str_to_list, is_number_like
from qteasy.utilfuncs import maybe_trade_day, is_market_trade_day, prev_trade_day, next_trade_day, prev_market_trade_day
from qteasy.utilfuncs import next_market_trade_day, unify, mask_to_signal, list_or_slice, labels_to_dict
from qteasy.space import Space, Axis, space_around_centre, ResultPool
from qteasy.core import apply_loop
from qteasy.built_in import SelectingFinanceIndicator, TimingDMA, TimingMACD, TimingCDL, TimingTRIX
from qteasy.history import stack_dataframes
from qteasy.tsfuncs import income, indicators, name_change, get_bar
from qteasy.tsfuncs import stock_basic, trade_calendar, new_share, get_index
from qteasy.tsfuncs import balance, cashflow, top_list, index_indicators, composite
from qteasy.tsfuncs import future_basic, future_daily, options_basic, options_daily
from qteasy.tsfuncs import fund_basic, fund_net_value, index_basic

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

from qteasy.database import DataSource

from qteasy.strategy import Strategy, SimpleTiming, RollingTiming, SimpleSelecting, FactoralSelecting

from qteasy._arg_validators import _parse_string_kwargs, _valid_qt_kwargs


class TestCost(unittest.TestCase):
    def setUp(self):
        self.amounts = np.array([10000, 20000, 10000])
        self.op = np.array([0, 1, -0.33333333])
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
        self.r.buy_fix = 0
        self.r.sell_fix = 0
        self.r.buy_min = 0
        self.r.sell_min = 0
        self.r.slipage = 0

        print('\nSell result with fixed rate = 0.001 and moq = 0:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 33299.999667, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 33.333332999999996, msg='result incorrect')

        print('\nSell result with fixed rate = 0.001 and moq = 1:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 1))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 1)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 33296.67, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 33.33, msg='result incorrect')

        print('\nSell result with fixed rate = 0.001 and moq = 100:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 100))
        test_rate_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 0., -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], 32967.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 33, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997.00897308, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 59.82053838484547, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 1:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 1))
        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 1)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 997., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -19999.82, msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 59.82, msg='result incorrect')

        print('\nPurchase result with fixed rate = 0.003 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))
        test_rate_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_rate_fee_result[0], [0., 900., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[1], -18054., msg='result incorrect')
        self.assertAlmostEqual(test_rate_fee_result[2], 54.0, msg='result incorrect')

    def test_min_fee(self):
        self.r.buy_rate = 0.
        self.r.sell_rate = 0.
        self.r.buy_fix = 0.
        self.r.sell_fix = 0.
        self.r.buy_min = 300
        self.r.sell_min = 300
        self.r.slipage = 0.
        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 985, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 10:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 10))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 10)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 980, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -19900.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with min fee = 300 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))
        test_min_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_min_fee_result[0], [0., 900, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], -18300.0, msg='result incorrect')
        self.assertAlmostEqual(test_min_fee_result[2], 300.0, msg='result incorrect')

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 0:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 33033.333)
        self.assertAlmostEqual(test_min_fee_result[2], 300.0)

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 1:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 1))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 1)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 33030)
        self.assertAlmostEqual(test_min_fee_result[2], 300.0)

        print('\nselling result with fixed cost rate with min fee = 300 and moq = 100:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 100))
        test_min_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_min_fee_result[0], [0, 0, -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_min_fee_result[1], 32700)
        self.assertAlmostEqual(test_min_fee_result[2], 300.0)

    def test_rate_with_min(self):
        """Test transaction cost calculated by rate with min_fee"""
        self.r.buy_rate = 0.0153
        self.r.sell_rate = 0.01
        self.r.buy_fix = 0.
        self.r.sell_fix = 0.
        self.r.buy_min = 300
        self.r.sell_min = 333
        self.r.slipage = 0.
        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        test_rate_with_min_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 984.9305624, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2], 301.3887520929774, msg='result incorrect')

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 10:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 10))
        test_rate_with_min_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 10)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 980, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], -19900.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2], 300.0, msg='result incorrect')

        print('\npurchase result with fixed cost rate with buy_rate = 0.0153, min fee = 300 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))
        test_rate_with_min_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0., 900, 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], -18300.0, msg='result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[2], 300.0, msg='result incorrect')

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 0:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))
        test_rate_with_min_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], 32999.99967)
        self.assertAlmostEqual(test_rate_with_min_result[2], 333.33333)

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 1:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 1))
        test_rate_with_min_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 1)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], 32996.7)
        self.assertAlmostEqual(test_rate_with_min_result[2], 333.3)

        print('\nselling result with fixed cost rate with sell_rate = 0.01, min fee = 333 and moq = 100:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 100))
        test_rate_with_min_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_rate_with_min_result[0], [0, 0, -3300]), True, 'result incorrect')
        self.assertAlmostEqual(test_rate_with_min_result[1], 32667.0)
        self.assertAlmostEqual(test_rate_with_min_result[2], 333.0)

    def test_fixed_fee(self):
        self.r.buy_rate = 0.
        self.r.sell_rate = 0.
        self.r.buy_fix = 200
        self.r.sell_fix = 150
        self.r.buy_min = 0
        self.r.sell_min = 0
        self.r.slipage = 0
        print('\nselling result of fixed cost with fixed fee = 150 and moq=0:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 0))
        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3333.3333]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], 33183.333, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 150.0, msg='result incorrect')

        print('\nselling result of fixed cost with fixed fee = 150 and moq=100:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts, 100))
        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts, 100)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3300.]), True,
                      f'result incorrect, {test_fixed_fee_result[0]} does not equal to [0,0,-3400]')
        self.assertAlmostEqual(test_fixed_fee_result[1], 32850., msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 150., msg='result incorrect')

        print('\npurchase result of fixed cost with fixed fee = 200:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        test_fixed_fee_result = self.r.get_purchase_result(self.prices, self.op, self.amounts, 0)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0., 990., 0.]), True, 'result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[1], -20000.0, msg='result incorrect')
        self.assertAlmostEqual(test_fixed_fee_result[2], 200.0, msg='result incorrect')

        print('\npurchase result of fixed cost with fixed fee = 200:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))
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
        print('\npurchase result of fixed rate = 0.003 and slipage = 1E-10 and moq = 0:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 0))
        print('\npurchase result of fixed rate = 0.003 and slipage = 1E-10 and moq = 100:')
        print(self.r.get_purchase_result(self.prices, self.op, self.amounts, 100))
        print('\nselling result with fixed rate = 0.001 and slipage = 1E-10:')
        print(self.r.get_selling_result(self.prices, self.op, self.amounts))

        test_fixed_fee_result = self.r.get_selling_result(self.prices, self.op, self.amounts)
        self.assertIs(np.allclose(test_fixed_fee_result[0], [0, 0, -3333.3333]), True,
                      f'{test_fixed_fee_result[0]} does not equal to [0, 0, -10000]')
        self.assertAlmostEqual(test_fixed_fee_result[1], 33298.88855591,
                               msg=f'{test_fixed_fee_result[1]} does not equal to 99890.')
        self.assertAlmostEqual(test_fixed_fee_result[2], 34.44444409,
                               msg=f'{test_fixed_fee_result[2]} does not equal to -36.666663.')

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
        self.op_signals = np.array([[0, 0, 0, 0, 0.25, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0.1, 0.15],
                                    [0.2, 0.2, 0, 0, 0, 0, 0],
                                    [0, 0, 0.1, 0, 0, 0, 0],
                                    [0, 0, 0, 0, -0.75, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [-0.333, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, -0.5, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, -1],
                                    [0, 0, 0, 0, 0.2, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [-0.5, 0, 0, 0.15, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0.2, 0, -1, 0.2, 0],
                                    [0.5, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0.2, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, -0.5, 0.2],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0.2, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0.15, 0, 0],
                                    [-1, 0, 0.25, 0.25, 0, 0.25, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0.25, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0.2, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, -1, 0, 0.2],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, -1, 0, 0, 0, 0, 0],
                                    [-1, 0, 0.15, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 0, 0, 0]])
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
        self.op_signal_df = pd.DataFrame(self.op_signals, index=self.dates, columns=self.shares)
        self.history_list = pd.DataFrame(self.prices, index=self.dates, columns=self.shares)
        self.res = np.array([[0.000, 0.000, 0.000, 0.000, 555.556, 0.000, 0.000, 7500.000, 0.000, 10000.000],
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
                             [1073.823, 416.679, 735.644, 269.850, 1785.205, 938.697, 1339.207, 5001.425, 0, 33323.836],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 32820.290],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 33174.614],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 35179.466],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 34465.195],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 34712.354],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 35755.550],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37895.223],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37854.284],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37198.374],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 35916.711],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 35806.937],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 36317.592],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37103.973],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 35457.883],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 36717.685],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37641.463],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 36794.298],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37073.817],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 35244.299],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37062.382],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 37420.067],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 38089.058],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 39260.542],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 42609.684],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 43109.309],
                             [0.000, 416.679, 1290.692, 719.924, 1785.205, 2701.488, 1339.207, 0.000, 0.000, 42283.408],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 43622.444],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 42830.254],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 41266.463],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 41164.839],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 41797.937],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 42440.861],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 42113.839],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 43853.588],
                             [0.000, 416.679, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 915.621, 0.000, 46216.760],
                             [0.000, 0.000, 1290.692, 719.924, 0.000, 2701.488, 4379.099, 5140.743, 0.000, 45408.737],
                             [0.000, 0.000, 2027.188, 719.924, 0.000, 2701.488, 4379.099, 0.000, 0.000, 47413.401],
                             [0.000, 0.000, 2027.188, 719.924, 0.000, 2701.488, 4379.099, 0.000, 0.000, 44603.718],
                             [0.000, 0.000, 2027.188, 719.924, 0.000, 2701.488, 4379.099, 0.000, 0.000, 44381.544]])

    def test_loop_step(self):
        cash, amounts, fee, value = qt.core._loop_step(pre_cash=10000,
                                                       pre_amounts=np.zeros(7, dtype='float'),
                                                       op=self.op_signals[0],
                                                       prices=self.prices[0],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 1 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 7500)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 0, 0, 555.5555556, 0, 0])))
        self.assertAlmostEqual(value, 10000.00)

        cash, amounts, fee, value = qt.core._loop_step(pre_cash=5059.722222,
                                                       pre_amounts=np.array([0, 0, 0, 0, 555.5555556,
                                                                             205.0653595, 321.0891813]),
                                                       op=self.op_signals[3],
                                                       prices=self.prices[3],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 4 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 1201.2775195, 5)
        self.assertTrue(np.allclose(amounts, np.array([346.9824373, 416.6786936, 0, 0,
                                                       555.5555556, 205.0653595, 321.0891813])))
        self.assertAlmostEqual(value, 9646.111756, 5)

        cash, amounts, fee, value = qt.core._loop_step(pre_cash=6179.77423,
                                                       pre_amounts=np.array([115.7186428, 416.6786936, 735.6441811,
                                                                             269.8495646, 0, 1877.393446, 0]),
                                                       op=self.op_signals[31],
                                                       prices=self.prices[31],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 32 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 0, 5)
        self.assertTrue(np.allclose(amounts, np.array([1073.823175, 416.6786936, 735.6441811,
                                                       269.8495646, 0, 1877.393446, 0])))
        self.assertAlmostEqual(value, 21133.50798, 5)

        cash, amounts, fee, value = qt.core._loop_step(pre_cash=10000,
                                                       pre_amounts=np.array([1073.823175, 416.6786936, 735.6441811,
                                                                             269.8495646, 0, 938.6967231, 1339.207325]),
                                                       op=self.op_signals[60],
                                                       prices=self.prices[60],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 61 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 5001.424618, 5)
        self.assertTrue(np.allclose(amounts, np.array([1073.823175, 416.6786936, 735.6441811, 269.8495646,
                                                       1785.205494, 938.6967231, 1339.207325])))
        self.assertAlmostEqual(value, 33323.83588, 5)

        cash, amounts, fee, value = qt.core._loop_step(pre_cash=cash,
                                                       pre_amounts=amounts,
                                                       op=self.op_signals[61],
                                                       prices=self.prices[61],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 62 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 0, 5)
        self.assertTrue(np.allclose(amounts, np.array([0, 416.6786936, 1290.69215, 719.9239224,
                                                       1785.205494, 2701.487958, 1339.207325])))
        self.assertAlmostEqual(value, 32820.29007, 5)

        cash, amounts, fee, value = qt.core._loop_step(pre_cash=915.6208259,
                                                       pre_amounts=np.array([0, 416.6786936, 1290.69215, 719.9239224,
                                                                             0, 2701.487958, 4379.098907]),
                                                       op=self.op_signals[96],
                                                       prices=self.prices[96],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 97 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 5140.742779, 5)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 1290.69215, 719.9239224, 0, 2701.487958, 4379.098907])))
        self.assertAlmostEqual(value, 45408.73655, 4)

        cash, amounts, fee, value = qt.core._loop_step(pre_cash=cash,
                                                       pre_amounts=amounts,
                                                       op=self.op_signals[97],
                                                       prices=self.prices[97],
                                                       rate=self.rate,
                                                       moq_buy=0,
                                                       moq_sell=0,
                                                       print_log=True)
        print(f'day 98 result in complete looping: \n'
              f'cash:     {cash}\n'
              f'amounts:  {np.round(amounts, 2)}\n'
              f'value:    {value}')
        self.assertAlmostEqual(cash, 0, 5)
        self.assertTrue(np.allclose(amounts, np.array([0, 0, 2027.18825, 719.9239224, 0, 2701.487958, 4379.098907])))
        self.assertAlmostEqual(value, 47413.40131, 4)

    def test_loop(self):
        res = apply_loop(op_list=self.op_signal_df,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate,
                         moq_buy=0,
                         moq_sell=0,
                         inflation_rate=0,
                         print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')
        self.assertTrue(np.allclose(res.values, self.res, 5))
        print(f'test assertion errors in apply_loop: detect moqs that are not compatible')
        self.assertRaises(AssertionError,
                          apply_loop,
                          self.op_signal_df,
                          self.history_list,
                          self.cash,
                          self.rate,
                          0, 1,
                          0,
                          False)
        self.assertRaises(AssertionError,
                          apply_loop,
                          self.op_signal_df,
                          self.history_list,
                          self.cash,
                          self.rate,
                          1, 5,
                          0,
                          False)
        print(f'test loop results with moq equal to 100')
        res = apply_loop(op_list=self.op_signal_df,
                         history_list=self.history_list,
                         cash_plan=self.cash,
                         cost_rate=self.rate2,
                         moq_buy=100,
                         moq_sell=1,
                         inflation_rate=0,
                         print_log=True)
        self.assertIsInstance(res, pd.DataFrame)
        print(f'in test_loop:\nresult of loop test is \n{res}')


class TestStrategy(unittest.TestCase):
    """ test all properties and methods of strategy base class"""
    def setUp(self) -> None:
        pass


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
        ma = sma(avg, n)
        if ma[-1] < price:
            return 0
        else:
            return 1


class TestSelStrategy(qt.SimpleSelecting):
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


class TestSelStrategyDiffTime(qt.SimpleSelecting):
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

    def _realize(self, hist_data: np.ndarray, params: tuple):
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

    def test_info(self):
        """Test information output of Operator"""
        print(f'test printing information of operator object')
        self.op.info()

    def test_get_strategy_by_name(self):
        """ test get_strategy_by_name()"""
        pass

    def test_get_strategies_by_price_type(self):
        """ test get_strategies_by_price_type"""
        pass

    def test_get_strategy_count_by_price_type(self):
        """ test get_strategy_count_by_price_type"""
        pass

    def test_get_strategy_names_by_price_type(self):
        """ test get_strategy_names_by_price_type"""
        pass

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
        """ test property strategy_names"""
        op = qt.Operator('dma')
        self.assertIsInstance(op.strategy_names, list)
        names = op.strategy_names[0]
        print(f'names are {names}')
        self.assertEqual(names, 'QUICK DMA STRATEGY')

        op = qt.Operator('dma, macd, trix, cdl')
        self.assertIsInstance(op.strategy_names, list)
        self.assertEqual(op.strategy_names[0], 'QUICK DMA STRATEGY')
        self.assertEqual(op.strategy_names[1], 'MACD STRATEGY')
        self.assertEqual(op.strategy_names[2], 'TRIX STRATEGY')
        self.assertEqual(op.strategy_names[3], 'CDL INDICATOR STRATEGY')

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
        op.set_parameter('macd strategy', data_freq='m')
        dtf = op.op_data_freq
        self.assertIsInstance(dtf, list)
        self.assertEqual(len(dtf), 2)
        self.assertEqual(dtf[0], 'm')
        self.assertEqual(dtf[1], 'd')

    def test_property_bt_price_types(self):
        """ test property bt_price_types"""
        raise NotImplementedError

    def test_property_op_history_data(self):
        """ test property op_history_data"""
        raise NotImplementedError

    def test_property_opt_space_par(self):
        """ test property opt_space_par"""
        raise NotImplementedError

    def test_property_opt_types(self):
        """ test property opt_types"""
        raise NotImplementedError

    def test_property_max_window_length(self):
        """ test property max_window_length"""
        raise NotImplementedError

    def test_property_bt_price_type_count(self):
        """ test property bt_price_type_count"""
        raise NotImplementedError

    def test_property_set(self):
        """ test all property setters"""
        raise NotImplementedError

    def test_operator_ready(self):
        """test the method ready of Operator"""
        pass
        # print(f'operator is ready? "{self.op.ready}"')

    def test_operator_add_strategy(self):
        """test adding strategies to Operator"""
        pass
        # self.assertIsInstance(self.op, qt.Operator)
        # self.assertIsInstance(self.op.timing[0], qt.TimingDMA)
        # self.assertIsInstance(self.op.selecting[0], qt.SelectingAll)
        # self.assertIsInstance(self.op.ricon[0], qt.RiconUrgent)
        # self.assertEqual(self.op.selecting_count, 1)
        # self.assertEqual(self.op.strategy_count, 3)
        # self.assertEqual(self.op.ricon_count, 1)
        # self.assertEqual(self.op.timing_count, 1)
        # self.assertEqual(self.op.ls_blender, 'pos-1')
        # print(f'test adding strategies into existing op')
        # print('test adding strategy by string')
        # self.op.add_strategy('macd', 'timing')
        # self.assertIsInstance(self.op.timing[0], qt.TimingDMA)
        # self.assertIsInstance(self.op.timing[1], qt.TimingMACD)
        # self.assertEqual(self.op.selecting_count, 1)
        # self.assertEqual(self.op.strategy_count, 4)
        # self.assertEqual(self.op.ricon_count, 1)
        # self.assertEqual(self.op.timing_count, 2)
        # self.assertEqual(self.op.ls_blender, 'pos-1')
        # self.op.add_strategy('random', 'selecting')
        # self.assertIsInstance(self.op.selecting[0], qt.TimingDMA)
        # self.assertIsInstance(self.op.selecting[1], qt.TimingMACD)
        # self.assertEqual(self.op.selecting_count, 2)
        # self.assertEqual(self.op.strategy_count, 5)
        # self.assertEqual(self.op.ricon_count, 1)
        # self.assertEqual(self.op.timing_count, 2)
        # self.assertEqual(self.op.selecting_blender, '0 or 1')
        # self.op.add_strategy('none', 'ricon')
        # self.assertIsInstance(self.op.ricon[0], qt.TimingDMA)
        # self.assertIsInstance(self.op.ricon[1], qt.TimingMACD)
        # self.assertEqual(self.op.selecting_count, 2)
        # self.assertEqual(self.op.strategy_count, 6)
        # self.assertEqual(self.op.ricon_count, 2)
        # self.assertEqual(self.op.timing_count, 2)
        # print('test adding strategy by list')
        # self.op.add_strategy(['dma', 'macd'], 'timing')
        # print('test adding strategy by object')
        # test_ls = TestLSStrategy()
        # self.op.add_strategy(test_ls, 'timing')

    def test_operator_remove_strategy(self):
        """test removing strategies from Operator"""
        pass
        # self.op.remove_strategy(stg='macd')    def test_prepare_data(self):
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        test_sig = TestSigStrategy()
        self.op = qt.Operator(strategies=[test_ls],
                              pt=[test_sel],
                              vs=[test_sig])
        too_early_cash = qt.CashPlan(dates='2016-01-01', amounts=10000)
        early_cash = qt.CashPlan(dates='2016-07-01', amounts=10000)
        on_spot_cash = qt.CashPlan(dates='2016-07-08', amounts=10000)
        no_trade_cash = qt.CashPlan(dates='2016-07-08, 2016-07-30, 2016-08-11, 2016-09-03',
                                    amounts=[10000, 10000, 10000, 10000])
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
        self.assertIsInstance(self.op._signal_history_data, list)
        self.assertIsInstance(self.op._ricon_history_data, list)
        self.assertEqual(len(self.op._selecting_history_data), 1)
        self.assertEqual(len(self.op._signal_history_data), 1)
        self.assertEqual(len(self.op._ricon_history_data), 1)
        sel_hist_data = self.op._selecting_history_data[0]
        tim_hist_data = self.op._signal_history_data[0]
        ric_hist_data = self.op._ricon_history_data[0]
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
        """

        :return:
        """
        test_ls = TestLSStrategy()
        test_sel = TestSelStrategy()
        test_sig = TestSigStrategy()
        self.op = qt.Operator(strategies=[test_ls],
                              pt=[test_sel],
                              vs=[test_sig])
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
        self.assertEqual(op_list.shape, (26, 3))
        # 删除去掉重复信号的code后，信号从原来的23条变为26条，包含三条重复信号，但是删除重复信号可能导致将不应该删除的信号删除，详见
        # operator.py的create_signal()函数注释836行
        target_op_dates = ['2016/07/08', '2016/07/12', '2016/07/13', '2016/07/14',
                           '2016/07/18', '2016/07/20', '2016/07/22', '2016/07/26',
                           '2016/07/27', '2016/07/28', '2016/08/02', '2016/08/03',
                           '2016/08/04', '2016/08/05', '2016/08/08', '2016/08/10',
                           '2016/08/16', '2016/08/18', '2016/08/24', '2016/08/26',
                           '2016/08/29', '2016/08/30', '2016/08/31', '2016/09/05',
                           '2016/09/06', '2016/09/08']
        target_op_values = np.array([[0.0, 1.0, 0.0],
                                     [0.5, -1.0, 0.0],
                                     [1.0, 0.0, 0.0],
                                     [0.0, 0.0, -1.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 1.0, 0.0],
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
                                     [0.0, 0.0, -1.0],
                                     [0.0, 0.0, 1.0],
                                     [-1.0, 0.0, 0.0],
                                     [0.0, 1.0, 1.0],
                                     [0.0, 1.0, 0.5],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 1.0, 0.0],
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
        print([item[2] for item in dates_pairs])
        print([item[2] for item in signal_pairs])
        self.assertTrue(np.allclose(target_op.values, op_list.values, equal_nan=True))
        self.assertTrue(all([date1 == date2
                             for date1, date2
                             in zip(target_op.index.strftime('%m-%d'), op_list.index.strftime('%m-%d'))]))

    def test_operator_parameter_setting(self):
        """

        :return:
        """
        new_op = qt.Operator(pt=['all'], strategies='dma', vs='urgent')
        print(new_op.strategies, '\n', [qt.TimingDMA, qt.SelectingAll, qt.RiconUrgent])
        print(f'info of Timing strategy in new op: \n{new_op.strategies[0].info()}')
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
        self.assertEqual(self.op.selecting_blender, '0 & 1 | 2')
        self.assertEqual(self.op.selecting_blender_expr, ['|', '&', '0', '1', '2'])
        self.assertEqual(self.op.ricon_blender, 'add')

        self.assertRaises(ValueError, self.op.set_blender, 'select', '0and1')
        self.assertRaises(TypeError, self.op.set_blender, 35, '0 and 1')

        self.assertEqual(self.op.opt_space_par,
                         ([(5, 10), (5, 15), (10, 15), (0, 1)], ['discr', 'discr', 'discr', 'conti']))
        self.assertEqual(self.op.opt_types, [1, 1, 0])

    def test_selecting_blend(self):
        self.op.set_blender('selecting', '0 & 1 | 2')
        self.assertEqual(self.op.selecting_blender_expr, ['|', '2', '&', '1', '0'])
        self.assertEqual(self.op._selecting_blend([1, 1, 1]), 1)
        self.assertEqual(self.op._selecting_blend([1, 0, 1]), 1)
        self.assertEqual(self.op._selecting_blend([1, 1, 0]), 1)
        self.assertEqual(self.op._selecting_blend([0, 1, 1]), 1)
        self.assertEqual(self.op._selecting_blend([0, 0, 1]), 1)
        self.assertEqual(self.op._selecting_blend([1, 0, 0]), 0)
        self.assertEqual(self.op._selecting_blend([0, 1, 0]), 0)
        self.assertEqual(self.op._selecting_blend([0, 0, 0]), 0)
        self.op.set_blender('selecting', '0 & ( 1 | 2 )')
        self.assertEqual(self.op.selecting_blender_expr, ['&', '|', '2', '1', '0'])
        self.assertEqual(self.op._selecting_blend([1, 1, 1]), 1)
        self.assertEqual(self.op._selecting_blend([1, 0, 1]), 1)
        self.assertEqual(self.op._selecting_blend([1, 1, 0]), 1)
        self.assertEqual(self.op._selecting_blend([0, 1, 1]), 0)
        self.assertEqual(self.op._selecting_blend([0, 0, 1]), 0)
        self.assertEqual(self.op._selecting_blend([1, 0, 0]), 0)
        self.assertEqual(self.op._selecting_blend([0, 1, 0]), 0)
        self.assertEqual(self.op._selecting_blend([0, 0, 0]), 0)
        self.op.set_blender('selecting', '(1-2)/3 + 0')
        self.assertEqual(self.op.selecting_blender_expr, ['+', '0', '/', '3', '-', '2', '1'])
        self.assertEqual(self.op._selecting_blend([5, 9, 1, 4]), 7)
        self.op.set_blender('selecting', '(0*1/2*(3+4))+5*(6+7)-8')
        self.assertEqual(self.op.selecting_blender_expr, ['-', '8', '+', '*', '+', '7', '6', '5', '*',
                                                          '+', '4', '3', '/', '2', '*', '1', '0'])
        self.assertEqual(self.op._selecting_blend([1, 1, 1, 1, 1, 1, 1, 1, 1]), 3)
        self.assertEqual(self.op._selecting_blend([2, 1, 4, 3, 5, 5, 2, 2, 10]), 14)
        self.op.set_blender('selecting', '0/max(2,1,3 + 5)+4')
        self.assertEqual(self.op.selecting_blender_expr, ['+', '4', '/', 'max(3)', '+', '5', '3', '1', '2', '0'])
        self.assertEqual(self.op._selecting_blend([8.0, 4, 3, 5.0, 0.125, 5]), 0.925)
        self.assertEqual(self.op._selecting_blend([2, 1, 4, 3, 5, 5, 2, 2, 10]), 5.25)
        self.op.set_blender('selecting', '0/max(2,1,3 + 5)+4')
        self.assertEqual(self.op._selecting_blend([8.0, 4, 3, 5.0, 0.125, 5]), 0.925)
        self.assertEqual(self.op._selecting_blend([2, 1, 4, 3, 5, 5, 2, 2, 10]), 5.25)

        print('speed test')
        import time
        st = time.time()
        self.op.set_blender('selecting', '0+max(1,2,(3+4)*5, max(6, (7+8)*9), 10-11) * (12+13)')
        for i in range(10000):
            res = self.op._selecting_blend([1, 1, 2, 3, 4, 5, 3, 4, 5, 6, 7, 8, 2, 3])
        et = time.time()
        print(f'total time for RPN processing: {et - st}, got result: {res}')

        self.op.set_blender('selecting', "0 + 1 * 2")
        self.assertEqual(self.op._selecting_blend([1, 2, 3]), 7)
        self.op.set_blender('selecting', "(0 + 1) * 2")
        self.assertEqual(self.op._selecting_blend([1, 2, 3]), 9)
        self.op.set_blender('selecting', "(0+1) * 2")
        self.assertEqual(self.op._selecting_blend([1, 2, 3]), 9)
        self.op.set_blender('selecting', "(0 + 1)   * 2")
        self.assertEqual(self.op._selecting_blend([1, 2, 3]), 9)
        # TODO: 目前对于-(1+2)这样的表达式还无法处理
        # self.op.set_blender('selecting', "-(0 + 1) * 2")
        # self.assertEqual(self.op.signal_blend([1, 2, 3]), -9)
        self.op.set_blender('selecting', "(0-1)/2 + 3")
        print(f'RPN of notation: "(0-1)/2 + 3" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertAlmostEqual(self.op._selecting_blend([1, 2, 3, 0.0]), -0.33333333)
        self.op.set_blender('selecting', "0 + 1 / 2")
        print(f'RPN of notation: "0 + 1 / 2" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertAlmostEqual(self.op._selecting_blend([1, math.pi, 4]), 1.78539816)
        self.op.set_blender('selecting', "(0 + 1) / 2")
        print(f'RPN of notation: "(0 + 1) / 2" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertEqual(self.op._selecting_blend([1, 2, 3]), 1)
        self.op.set_blender('selecting', "(0 + 1 * 2) / 3")
        print(f'RPN of notation: "(0 + 1 * 2) / 3" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertAlmostEqual(self.op._selecting_blend([3, math.e, 10, 10]), 3.0182818284590454)
        self.op.set_blender('selecting', "0 / 1 * 2")
        print(f'RPN of notation: "0 / 1 * 2" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertEqual(self.op._selecting_blend([1, 3, 6]), 2)
        self.op.set_blender('selecting', "(0 - 1 + 2) * 4")
        print(f'RPN of notation: "(0 - 1 + 2) * 4" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertAlmostEqual(self.op._selecting_blend([1, 1, -1, np.nan, math.pi]), -3.141592653589793)
        self.op.set_blender('selecting', "0 * 1")
        print(f'RPN of notation: "0 * 1" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertAlmostEqual(self.op._selecting_blend([math.pi, math.e]), 8.539734222673566)

        self.op.set_blender('selecting', 'abs(3-sqrt(2) /  cos(1))')
        print(f'RPN of notation: "abs(3-sqrt(2) /  cos(1))" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertEqual(self.op.selecting_blender_expr, ['abs(1)', '-', '/', 'cos(1)', '1', 'sqrt(1)', '2', '3'])
        self.op.set_blender('selecting', '0/max(2,1,3 + 5)+4')
        print(f'RPN of notation: "0/max(2,1,3 + 5)+4" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertEqual(self.op.selecting_blender_expr, ['+', '4', '/', 'max(3)', '+', '5', '3', '1', '2', '0'])

        self.op.set_blender('selecting', '1 + sum(1,2,3+3, sum(1, 2) + 3) *5')
        print(f'RPN of notation: "1 + sum(1,2,3+3, sum(1, 2) + 3) *5" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertEqual(self.op.selecting_blender_expr, ['+', '*', '5', 'sum(4)', '+', '3', 'sum(2)', '2', '1',
                                                          '+', '3', '3', '2', '1', '1'])
        self.op.set_blender('selecting', '1+sum(1,2,(3+5)*4, sum(3, (4+5)*6), 7-8) * (2+3)')
        print(f'RPN of notation: "1+sum(1,2,(3+5)*4, sum(3, (4+5)*6), 7-8) * (2+3)" is:\n'
              f'{" ".join(self.op.selecting_blender_expr[::-1])}')
        self.assertEqual(self.op.selecting_blender_expr, ['+', '*', '+', '3', '2', 'sum(5)', '-', '8', '7',
                                                          'sum(2)', '*', '6', '+', '5', '4', '3', '*', '4',
                                                          '+', '5', '3', '2', '1', '1'])

        # self.assertRaises(ValueError, self.op.set_blender, 'selecting', '0 and (1 or 2)')

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

        # test set_opt_par when opt_tag is set to be 2 (enumerate type of parameters)

        self.assertRaises(ValueError, self.op.set_opt_par, (5, 12, 9, 8))

    def test_stg_attribute_get_and_set(self):
        self.stg = qt.TimingCrossline()
        self.stg_type = 'TIMING'
        self.stg_name = "CROSSLINE STRATEGY"
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
        self.assertListEqual(self.op._exp_to_token('(1 - 1 + -1) * pi'),
                             ['(', '1', '-', '1', '+', '-1', ')', '*', 'pi'])
        print(self.op._exp_to_token('(1 - 1 + -1) * pi'))
        self.assertListEqual(self.op._exp_to_token('abs(5-sqrt(2) /  cos(pi))'),
                             ['abs(', '5', '-', 'sqrt(', '2', ')', '/', 'cos(', 'pi', ')', ')'])
        print(self.op._exp_to_token('abs(5-sqrt(2) /  cos(pi))'))
        self.assertListEqual(self.op._exp_to_token('sin(pi) + 2.14'),
                             ['sin(', 'pi', ')', '+', '2.14'])
        print(self.op._exp_to_token('sin(pi) + 2.14'))
        self.assertListEqual(self.op._exp_to_token('(1-2)/3.0 + 0.0000'),
                             ['(', '1', '-', '2', ')', '/', '3.0', '+', '0.0000'])
        print(self.op._exp_to_token('(1-2)/3.0 + 0.0000'))
        self.assertListEqual(self.op._exp_to_token('-(1. + .2) * max(1, 3, 5)'),
                             ['-', '(', '1.', '+', '.2', ')', '*', 'max(', '1', ',', '3', ',', '5', ')'])
        print(self.op._exp_to_token('-(1. + .2) * max(1, 3, 5)'))
        self.assertListEqual(self.op._exp_to_token('(x + e * 10) / 10'),
                             ['(', 'x', '+', 'e', '*', '10', ')', '/', '10'])
        print(self.op._exp_to_token('(x + e * 10) / 10'))
        self.assertListEqual(self.op._exp_to_token('8.2/((-.1+abs3(3,4,5))*0.12)'),
                             ['8.2', '/', '(', '(', '-.1', '+', 'abs3(', '3', ',', '4', ',', '5', ')', ')', '*', '0.12', ')'])
        print(self.op._exp_to_token('8.2/((-.1+abs3(3,4,5))*0.12)'))
        self.assertListEqual(self.op._exp_to_token('8.2/abs3(3,4,25.34 + 5)*0.12'),
                             ['8.2', '/', 'abs3(', '3', ',', '4', ',', '25.34', '+', '5', ')', '*', '0.12'])
        print(self.op._exp_to_token('8.2/abs3(3,4,25.34 + 5)*0.12'))


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

        empty_hp = qt.HistoryPanel()
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


class TestUtilityFuncs(unittest.TestCase):
    def setUp(self):
        pass

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
        raise NotImplementedError

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

    def test_is_market_trade_day(self):
        """ test util func is_market_trade_day()"""
        raise NotImplementedError

    def test_weekday_name(self):
        """ test util func weekday_name()"""
        raise NotImplementedError

    def test_list_truncate(self):
        """ test util func list_truncate()"""
        raise NotImplementedError

    def test_maybe_trade_day(self):
        """ test util function maybe_trade_day()"""
        raise NotImplementedError

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
        # shares = '600748.SH'
        # df = stock_company(shares=shares)
        # self.assertIsInstance(df, pd.DataFrame)
        # self.assertFalse(df.empty)
        # df.info()
        # print(df.head(10))

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
        self.op.set_parameter('s-0', pars=(2,), sample_freq='y')
        self.op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('t-1', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        # self.op.set_parameter('t-2', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, 0)])

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
        self.op.set_parameter(stg_id='t-0', pars=timing_pars1)
        self.op.set_parameter(stg_id='t-1', pars=timing_pars3)
        self.op.set_parameter('r-0', pars=(9, -0.1595))

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
        op.set_parameter('t-0', pars=(6,))
        op.set_parameter('s-0', (0.5,))
        op.set_parameter('r-0', ())
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
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        """测试策略的优化模式，使用递进步长网格寻优"""
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        """测试策略的优化模式，使用递进步长网格寻优"""
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        """测试策略的优化模式，使用递进步长网格寻优"""
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        """测试策略的优化模式，使用递进步长网格寻优"""
        # TODO: investigate, function does not work while
        # TODO: setting parallel = True
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
        pass

    def test_multi_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        # TODO: Investigate, error when invest_end being set to "20181231", problem probably
        # TODO: related to trade day calendar.
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
                     invest_end='20181229',
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
        op.set_parameter('t-0', pars=(35, 120, 10, 'buy'))
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_macd(self):
        op = qt.Operator(strategies=['macd'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dma(self):
        op = qt.Operator(strategies=['dma'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_trix(self):
        op = qt.Operator(strategies=['trix'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_cdl(self):
        op = qt.Operator(strategies=['cdl'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        # built-in cdl is not optimizable

    def test_ssma(self):
        op = qt.Operator(strategies=['ssma'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sdema(self):
        op = qt.Operator(strategies=['sdema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sema(self):
        op = qt.Operator(strategies=['sema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sht(self):
        op = qt.Operator(strategies=['sht'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        # built-in strategy sht is not optimizable

    def test_skama(self):
        op = qt.Operator(strategies=['skama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_smama(self):
        op = qt.Operator(strategies=['smama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sfama(self):
        op = qt.Operator(strategies=['sfama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_st3(self):
        op = qt.Operator(strategies=['st3'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_stema(self):
        op = qt.Operator(strategies=['stema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_strima(self):
        op = qt.Operator(strategies=['strima'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_swma(self):
        op = qt.Operator(strategies=['swma'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dsma(self):
        op = qt.Operator(strategies=['dsma'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_ddema(self):
        op = qt.Operator(strategies=['ddema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dema(self):
        op = qt.Operator(strategies=['dema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dkama(self):
        op = qt.Operator(strategies=['dkama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dmama(self):
        op = qt.Operator(strategies=['dmama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dfama(self):
        op = qt.Operator(strategies=['dfama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dt3(self):
        op = qt.Operator(strategies=['dt3'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dtema(self):
        op = qt.Operator(strategies=['dtema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dtrima(self):
        op = qt.Operator(strategies=['dtrima'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_dwma(self):
        op = qt.Operator(strategies=['dwma'])
        op.set_parameter('t-0', pars=(200, 22))
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slsma(self):
        op = qt.Operator(strategies=['slsma'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sldema(self):
        op = qt.Operator(strategies=['sldema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slema(self):
        op = qt.Operator(strategies=['slema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slht(self):
        op = qt.Operator(strategies=['slht'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        # built-in strategy slht is not optimizable

    def test_slkama(self):
        op = qt.Operator(strategies=['slkama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slmama(self):
        op = qt.Operator(strategies=['slmama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slfama(self):
        op = qt.Operator(strategies=['slfama'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slt3(self):
        op = qt.Operator(strategies=['slt3'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sltema(self):
        op = qt.Operator(strategies=['sltema'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_sltrima(self):
        op = qt.Operator(strategies=['sltrima'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)

    def test_slwma(self):
        op = qt.Operator(strategies=['slwma'])
        op.set_parameter('t-0', opt_tag=1)
        qt.run(op, mode=1)
        self.assertEqual(qt.QT_CONFIG.invest_start, '20200113')
        self.assertEqual(qt.QT_CONFIG.opti_sample_count, 100)
        qt.run(op, mode=2)


class FastExperiments(unittest.TestCase):
    """This test case is created to have experiments done that can be quickly called from Command line"""

    def setUp(self):
        pass

    def test_fast_experiments(self):
        op = qt.Operator('macd, dma', 'close')
        print(op)
        print(f'operator object created, properties are:\n'
              f'info: \n'
              f'{op.info()}\n'
              f'strategies: {op.strategies}')
        op.add_strategy('trix')
        print(f'after adding strategy, {op.strategies}')
        op.add_strategy('trix', price_type='open')
        print(f'after adding strategy: {op.strategies}\n'
              f'price types of strategies: {op.bt_price_types}')


class TestDataBase(unittest.TestCase):
    """test local historical file database management methods"""

    def setUp(self):
        self.data_source = DataSource()

    def test_get_and_update_data(self):
        # import pdb;
        # pdb.set_trace()

        # print(f'test expanded date time idx_range from 2020 07 01')
        ds = self.data_source
        # hp = ds.get_and_update_data(start='20200901',
        #                             end='20201231',
        #                             freq='d',
        #                             shares=['600748.SH', '000616.SZ', '000620.SZ', '000667.SZ',
        #                                     '000001.SZ', '000002.SZ'],
        #                             htypes=['close'],
        #                             adj='hfq',
        #                             parallel=10)
        # hp.info()
        # hp = qt.HistoryPanel()
        # print(hp)
        #
        # print(f'test different share scope, added 000005.SZ')
        # hp = ds.get_and_update_data(start='20200101',
        #                             end='20200901',
        #                             freq='d',
        #                             shares=['600748.SH', '000616.SZ', '000620.SZ', '000005.SZ'],
        #                             htypes=['close', 'open'],
        #                             parallel=0)
        # hp.info()
        # hp = qt.HistoryPanel()
        #
        # print(f'test getting and updating adjusted price data')
        # hp = ds.get_and_update_data(start='20180101',
        #                             end='20211201',
        #                             freq='d',
        #                             shares=qt.get_stock_pool(date='today',
        #                                                      market='主板,中小板'),
        #                             htypes=['close', 'open', 'high', 'low'],
        #                             adj='hfq',
        #                             parallel=16,
        #                             delay=180,
        #                             delay_every=80)
        # hp.info()
        # hp = qt.HistoryPanel()

        # print(f'test getting and updating refresh data')
        # hp = ds.get_and_update_data(start='19950101',
        #                             end='20211231',
        #                             freq='d',
        #                             shares=['000812.SZ', '600748.SH', '000616.SZ',
        #                                     '000620.SZ', '000667.SZ', '000001.SZ'],
        #                             htypes='open, high, low, close, vol',
        #                             refresh=True,
        #                             parallel=10,
        #                             delay=125,
        #                             delay_every=80)
        # hp.info()
        # hp = qt.HistoryPanel()

        # print(f'test getting and updating refresh data')
        # hp = ds.get_and_update_data(start='20060101',
        #                             end='20201231',
        #                             freq='d',
        #                             shares=qt.get_stock_pool(date='today',
        #                                                      market='主板,中小板'),
        #                             htypes=['vol'],
        #                             parallel=10,
        #                             delay=125,
        #                             delay_every=80)
        # hp.info()
        # hp = qt.HistoryPanel()
        #
        # print(f'test getting and updating lots of mixed data')
        # hp = ds.get_and_update_data(start='19950101',
        #                             end='20200901',
        #                             freq='d',
        #                             shares=qt.get_stock_pool(date='today',
        #                                                      market='主板,中小板'),
        #                             htypes=['close', 'open', 'high', 'low', 'net_profit',
        #                                     'finan_exp', 'total_share', 'eps',
        #                                     'dt_eps', 'total_revenue_ps', 'cap_rese'],
        #                             parallel=10,
        #                             delay=125,
        #                             delay_every=80)
        # hp.info()
        # hp = qt.HistoryPanel()


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