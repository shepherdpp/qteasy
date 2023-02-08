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
import pandas as pd
from pandas import Timestamp
import numpy as np
import math
from numpy import int64
import itertools
import datetime
import logging

from qteasy import QT_CONFIG, QT_DATA_SOURCE, CashPlan

from qteasy.finance import get_selling_result, get_purchase_result, calculate

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, time_str_format, str_to_list
from qteasy.utilfuncs import maybe_trade_day, is_market_trade_day, prev_trade_day, next_trade_day
from qteasy.utilfuncs import next_market_trade_day, unify, list_or_slice, labels_to_dict, retry
from qteasy.utilfuncs import weekday_name, nearest_market_trade_day, is_number_like, list_truncate, input_to_list
from qteasy.utilfuncs import match_ts_code, _lev_ratio, _partial_lev_ratio, _wildcard_match, rolling_window
from qteasy.utilfuncs import reindent

from qteasy.space import Space, Axis, space_around_centre, ResultPool
from qteasy.core import apply_loop, process_loop_results
from qteasy.built_in import SelectingAvgIndicator, DMA, MACD, CDL

from qteasy.tsfuncs import income, indicators, name_change
from qteasy.tsfuncs import stock_basic, trade_calendar, new_share
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

from qteasy.history import stack_dataframes, dataframe_to_hp, ffill_3d_data

from qteasy.database import DataSource, set_primary_key_index, set_primary_key_frame
from qteasy.database import get_primary_key_range, htype_to_table_col, _trade_time_index
from qteasy.database import _resample_data, freq_dither, get_main_freq_level, next_main_freq
from qteasy.database import get_main_freq

from qteasy.strategy import BaseStrategy, RuleIterator, GeneralStg, FactorSorter

from qteasy._arg_validators import _parse_string_kwargs, _valid_qt_kwargs

from qteasy.blender import _exp_to_token, blender_parser, signal_blend


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