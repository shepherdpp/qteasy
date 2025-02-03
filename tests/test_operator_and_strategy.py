# coding=utf-8
# ======================================
# File:     test_operator_and_strategy.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all Operator and
#   Strategy class attributes and
#   methods.
# ======================================
import unittest

import qteasy as qt
import pandas as pd
import numpy as np
import math
from qteasy.utilfuncs import rolling_window
from qteasy.built_in import SelectingAvgIndicator, DMA, MACD, CDL
from qteasy.tafuncs import sma
from qteasy.strategy import BaseStrategy, RuleIterator, GeneralStg, FactorSorter
from qteasy.blender import _exp_to_token, blender_parser, signal_blend, human_blender


class TestLSStrategy(RuleIterator):
    """用于test测试的简单多空蒙板生成策略。基于RuleIterator策略模版，将下列策略循环应用到所有股票上
        同时，针对不同股票策略参数可以不相同

    该策略有两个参数，N与Price
    如果给出的历史数据不包含参考数据时，策略逻辑如下：
     - 计算OHLC价格平均值的N日简单移动平均，判断：当移动平均价大于等于Price时，状态为看多，否则为看空
    如果给出参考数据时，策略逻辑变为：
     - 计算OHLC价格平均值的N日简单移动平均，判断：当移动平均价大于等于当日参考数据时，状态为看多，否则为看空
    如果给出交易结果数据时，策略逻辑变为：
     - 计算OHLC价格平均值的N日简单移动平均，判断：当移动平均价大于等于上次交易价时，状态为看多，否则为看空

    """

    def __init__(self):
        super().__init__(
                name='test_LS',
                description='test long/short strategy',
                par_count=2,
                par_types='discr, conti',
                par_range=([1, 5], [2, 10]),
                strategy_data_types='close, open, high, low',
                data_freq='d',
                window_length=5,
                use_latest_data_cycle=False,
        )
        pass

    def realize(self, h, r=None, t=None, pars=None):
        if pars is not None:
            n, price = pars
        else:
            n, price = self.pars
        h = h.T
        avg = (h[0] + h[1] + h[2] + h[3]) / 4
        ma = sma(avg, n)
        if r is not None:
            # 处理参考数据生成信号并返回
            ref_price = r[-1, 0]  # 当天的参考数据，r[-1
            if ma[-1] < ref_price:
                return 0
            else:
                return 1

        if t is not None:
            # 处理交易结果数据生成信号并返回
            last_price = t[4]  # 获取最近的交易价格
            if np.isnan(last_price):
                return 1  # 生成第一次交易信号
            if ma[-1] < last_price:
                return 1
            else:
                return 0

        if ma[-1] < price:
            return 0
        else:
            return 1


class TestSelStrategy(GeneralStg):
    """用于Test测试的通用交易策略，基于GeneralStrategy策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，按以下逻辑选择股票并设定多空状态：
    当历史数据不含参考数据和交易结果数据时：
     - 计算：今日变化率 = (今收-昨收)/平均股价(HLC平均股价)，
     - 选择今日变化率最高的两支，设定投资比率50%，否则投资比例为0
    当给出参考数据时，按下面逻辑设定多空：
     - 计算：今日相对变化率 = (今收-昨收)/HLC平均股价/参考数据
     - 选择相对变化率最高的两只股票，设定投资比率为50%，否则为0
    当给出交易结果数据时，按下面逻辑设定多空：
     - 计算：交易价差变化率 = (今收-昨收)/上期交易价格
     - 选择交易价差变化率最高的两只股票，设定投资比率为50%，否则为0
    """

    def __init__(self):
        super().__init__(
                name='test_SEL',
                description='test portfolio selection strategy',
                par_count=0,
                par_types='',
                par_range=(),
                strategy_data_types='high, low, close',
                data_freq='d',
                strategy_run_freq='10d',
                window_length=5,
                use_latest_data_cycle=False,
        )
        pass

    def realize(self, h, r=None, t=None):
        avg = np.nanmean(h, axis=(1, 2))
        dif = (h[:, :, 2] - np.roll(h[:, :, 2], 1, 1))
        dif_no_nan = np.array([arr[~np.isnan(arr)][-1] for arr in dif])
        if r is not None:
            # calculate difper while r
            ref_price = np.nanmean(r[:, 0])
            difper = dif_no_nan / avg / ref_price
            large2 = difper.argsort()[1:]
            chosen = np.zeros_like(avg)
            chosen[large2] = 0.5
            return chosen

        if t is not None:
            # calculate difper while t
            last_price = t[:, 4]
            if np.all(np.isnan(last_price)):
                return np.ones_like(avg) * 0.333
            difper = dif_no_nan / last_price
            large2 = difper.argsort()[1:]
            chosen = np.zeros_like(avg)
            chosen[large2] = 0.5
            return chosen

        difper = dif_no_nan / avg
        large2 = difper.argsort()[1:]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        return chosen


class TestSelStrategyDiffTime(GeneralStg):
    """用于Test测试的简单选股策略，基于Selecting策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，从股票池的三只股票中选出今日变化率 = (今收-昨收)/平均股价（OHLC平均股价）最高的两支，放入中选池，否则落选。
    选股比例为平均分配
    """

    def __init__(self):
        super().__init__(
                name='test_SEL',
                description='test portfolio selection strategy',
                par_count=0,
                par_types='',
                par_range=(),
                strategy_data_types='close, low, open',
                data_freq='d',
                strategy_run_freq='w',
                window_length=2,
                use_latest_data_cycle=False,
        )
        pass

    def realize(self, h, r=None, t=None):
        avg = h.mean(axis=1).squeeze()
        difper = (h[:, :, 0] - np.roll(h[:, :, 0], 1))[:, -1] / avg
        large2 = difper.argsort()[0:2]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        return chosen


class TestSigStrategy(GeneralStg):
    """用于Test测试的简单信号生成策略，基于GeneralStrategy策略生成

    策略有三个参数，第一个参数为ratio，另外两个参数为price1以及price2
    ratio是k线形状比例的阈值，定义为abs((C-O)/(H-L))。当这个比值小于ratio阈值时，判断该K线为十字交叉（其实还有丁字等多种情形，但这里做了
    简化处理。
    如果历史数据中没有给出参考数据，也没有给出交易结果数据时，信号生成的规则如下：
     1，当某个K线出现十字交叉，且昨收与今收之差大于price1时，买入信号
     2，当某个K线出现十字交叉，且昨收与今收之差小于price2时，卖出信号
    如果给出参考数据(参考数据包含两个种类type1与type2)时，信号生成的规则如下：
     1，当某个K线出现十字交叉，且昨收与今收之差大于参考数据type1时，买入信号
     2，当某个K线出现十字交叉，且昨收与今收之差小于参考数据type2时，卖出信号
    如果给出交易结果数据时，信号生成的规则如下：
     1，当某个K线出现十字交叉，且昨收与今收之差大于上期交易价格时，买入信号
     2，当某个K线出现十字交叉，且昨收与今收之差小于上期交易价格时，卖出信号
    """

    def __init__(self):
        super().__init__(
                name='test_SIG',
                description='test signal creation strategy',
                par_count=3,
                par_types='conti, conti, conti',
                par_range=([0, 10], [-3, 3], [-3, 3]),
                strategy_data_types='close, open, high, low',
                window_length=2,
                use_latest_data_cycle=False,
        )
        pass

    def realize(self, h, r=None, t=None):
        max_ratio, price1, price2 = self.pars
        ratio = np.abs((h[:, -1, 0] - h[:, -1, 1]) / (h[:, -1, 3] - h[:, -1, 2]))
        diff = h[:, -1, 0] - h[:, -2, 0]

        if r is not None:
            type1 = r[-1, 0]
            type2 = r[-1, 1]
            sig = np.where((ratio < max_ratio) & (diff > type1),
                           1,
                           np.where((ratio < max_ratio) & (diff < type2), -1, 0))
            return sig

        if t is not None:
            pass

        sig = np.where((ratio < max_ratio) & (diff > price1),
                       1,
                       np.where((ratio < max_ratio) & (diff < price2), -1, 0))

        return sig


class MyStg(qt.RuleIterator):
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
                par_types=['int', 'int', 'float'],
                par_range=[(10, 250), (10, 250), (0.0, 0.5)],
                name='CUSTOM ROLLING TIMING STRATEGY',
                description='Customized Rolling Timing Strategy for Testing',
                strategy_data_types='close',
                window_length=200,
        )

    # 策略的具体实现代码写在策略的_realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def realize(self, h, r=None, t=None, pars=None):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        f, s, m = pars
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = h.T
        # 计算长短均线的当前值
        s_ma = sma(h[0], s)[-1]
        f_ma = sma(h[0], f)[-1]

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


class StgBuyOpen(GeneralStg):
    def __init__(self, pars=(20,)):
        super().__init__(
                pars=pars,
                par_count=1,
                par_types=['int'],
                name='OPEN_BUY',
                par_range=[(0, 100)],
                strategy_run_timing='open',
                use_latest_data_cycle=False,
        )
        pass

    def realize(self, h, r=None, t=None):
        n, = self.pars
        current_price = h[:, -1, 0]
        n_day_price = h[:, -n, 0]
        # 选股指标为各个股票的N日涨幅
        factors = (current_price / n_day_price - 1).squeeze()
        # 初始化选股买卖信号，初始值为全0
        sig = np.zeros_like(factors)
        # buy_pos = np.nanargmax(factors)
        # sig[buy_pos] = 1
        # return sig
        if np.all(factors <= 0.002):
            # 如果所有的选股指标都小于0，则全部卖出
            # 但是卖出信号StgSelClose策略中处理，因此此处全部返回0即可
            return sig
        else:
            # 如果选股指标有大于0的，则找出最大者
            # 并生成买入信号
            sig[np.nanargmax(factors)] = 1
            return sig


class StgSelClose(GeneralStg):
    def __init__(self, pars=(20,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         name='SELL_CLOSE',
                         par_range=[(0, 100)],
                         strategy_run_timing='close')
        pass

    def realize(self, h, r=None, t=None):
        n, = self.pars
        current_price = h[:, -1, 0]
        n_day_price = h[:, -n, 0]
        # 选股指标为各个股票的N日涨幅
        factors = (current_price / n_day_price - 1).squeeze()
        # 初始化选股买卖信号，初始值为全-1
        sig = -np.ones_like(factors)
        # sig[np.nanargmax(factors)] = 0
        # return sig
        if np.all(factors <= 0.002):
            # 如果所有的选股指标都小于0，则全部卖出
            return sig
        else:
            # 如果选股指标有大于0的，则除最大者不卖出以外，其余全部
            # 产生卖出信号
            sig[np.nanargmax(factors)] = 0
            return sig


class TestOperatorAndStrategy(unittest.TestCase):
    """全面测试Operator对象的所有功能。包括：

        1, Strategy 参数的设置
        2, 历史数据的获取与分配提取
        3, 策略优化参数的批量设置和优化空间的获取
        4, 策略输出值的正确性验证
        5, 策略结果的混合结果确认
    """

    def setUp(self):
        """prepare arr for Operator test"""

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

        # for reference history data
        reference_data = np.array([[9.68],
                                   [9.87],
                                   [10],
                                   [9.87],
                                   [np.nan],
                                   [9.82],
                                   [6.85],
                                   [10.03],
                                   [10.06],
                                   [9.58],
                                   [10.11],
                                   [5.91],
                                   [9.75],
                                   [10.06],
                                   [6.23],
                                   [10.04],
                                   [10.06],
                                   [6.27],
                                   [10.24],
                                   [10],
                                   [10.24],
                                   [9.86],
                                   [5.69],
                                   [10.12],
                                   [10.03],
                                   [6.25],
                                   [9.94],
                                   [9.83],
                                   [9.77],
                                   [10.64],
                                   [6.06],
                                   [9.93],
                                   [5.69],
                                   [5.46],
                                   [10.24],
                                   [9.88],
                                   [7.43],
                                   [7.72],
                                   [8.16],
                                   [10.37],
                                   [8.7],
                                   [11.02],
                                   [np.nan],
                                   [np.nan],
                                   [9.55],
                                   [10.87],
                                   [11.01],
                                   [9.64],
                                   [7.97],
                                   [8.25]])
        reference_data2 = np.array([[0.03403, -0.00679],
                                    [0.00822, -0.00270],
                                    [0.03831, -0.04480],
                                    [0.03389, -0.03428],
                                    [0.00495, -0.03510],
                                    [0.01980, -0.03766],
                                    [0.02131, -0.03213],
                                    [0.03938, -0.00722],
                                    [0.01447, -0.02826],
                                    [0.02945, -0.04790],
                                    [0.02360, -0.04789],
                                    [0.00619, -0.04531],
                                    [0.04896, -0.04129],
                                    [0.03516, -0.04309],
                                    [0.03458, -0.03919],
                                    [0.02444, -0.00516],
                                    [0.02023, -0.02297],
                                    [0.02938, -0.02868],
                                    [0.03827, -0.00575],
                                    [0.02168, -0.03163],
                                    [0.01129, -0.04463],
                                    [0.01640, -0.00991],
                                    [0.01592, -0.04192],
                                    [0.04553, -0.00682],
                                    [0.00105, -0.04323],
                                    [0.01473, -0.04458],
                                    [0.04922, -0.00244],
                                    [0.01109, -0.00762],
                                    [0.04486, -0.01096],
                                    [0.03808, -0.03854],
                                    [0.04887, -0.04125],
                                    [0.00573, -0.03636],
                                    [0.02493, -0.01269],
                                    [0.00295, -0.03817],
                                    [0.03691, -0.02565],
                                    [0.00501, -0.04381],
                                    [0.02859, -0.03429],
                                    [0.02525, -0.01701],
                                    [0.02570, -0.01181],
                                    [0.02488, -0.00623],
                                    [0.02396, -0.04004],
                                    [0.00127, -0.00818],
                                    [0.02775, -0.03364],
                                    [0.03757, -0.00792],
                                    [0.04514, -0.00222],
                                    [0.02610, -0.02855],
                                    [0.04426, -0.03365],
                                    [0.02742, -0.04061],
                                    [0.02031, -0.01752],
                                    [0.02251, -0.03796]])

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
        self.test_data_sel_finance = np.empty((3, data_rows, 1))
        self.test_ref_data = np.zeros((1, data_rows, 1))
        self.test_ref_data2 = np.zeros((1, data_rows, 2))

        # fill in 3D data
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

        # fill in reference data
        self.test_ref_data[0, :, :] = reference_data
        self.test_ref_data2[0, :, :] = reference_data2

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
        self.assertIsInstance(op.strategies[0], DMA)
        op = qt.Operator('dma, macd')
        self.assertIsInstance(op, qt.Operator)
        op = qt.Operator(['dma', 'macd'])
        self.assertIsInstance(op, qt.Operator)

    def test_repr(self):
        """ test basic representation of Opeartor class"""
        op = qt.Operator()
        self.assertEqual(op.__repr__(), 'Operator([], \'pt\', \'batch\')')

        op = qt.Operator('macd, dma, trix, random, ndayavg')
        self.assertEqual(op.__repr__(), 'Operator([macd, dma, trix, random, ndayavg], \'pt\', \'batch\')')
        self.assertEqual(op['dma'].__repr__(), 'RULE-ITER(DMA)')
        self.assertEqual(op['macd'].__repr__(), 'RULE-ITER(MACD)')
        self.assertEqual(op['trix'].__repr__(), 'RULE-ITER(TRIX)')
        self.assertEqual(op['random'].__repr__(), 'GENERAL(RANDOM)')
        self.assertEqual(op['ndayavg'].__repr__(), 'FACTOR(N-DAY AVG)')

    def test_info(self):
        """Test information output of Operator"""
        stg = qt.built_in.SelectingNDayRateChange()
        print(f'test printing information of strategies, in verbose mode')
        self.op[0].info()
        stg.info()

        print(f'test printing information of strategies, in simple mode')
        self.op[0].info(verbose=False)
        stg.info(verbose=False)

        print(f'test printing information of operator object')
        self.op.info()

    def test_set_pars(self):
        """ 测试设置策略参数"""
        stg_dma = self.op2[0]
        stg_macd = self.op2[1]
        stg_trix = self.op2[2]

        stg_dma.pars = (10, 20, 30)
        self.assertEqual(stg_dma.pars, (10, 20, 30))
        stg_macd.pars = (10, 20, 30)
        self.assertEqual(stg_macd.pars, (10, 20, 30))
        stg_trix.set_pars((10, 20))
        self.assertEqual(stg_trix.pars, (10, 20))
        stg_dma.set_pars({'a': (10, 20, 30),
                          'b': (11, 21, 31),
                          'c': (12, 22, 32)})
        self.assertEqual(stg_dma.pars,
                         {'a': (10, 20, 30),
                          'b': (11, 21, 31),
                          'c': (12, 22, 32)})

        # test errors
        self.assertRaises(AssertionError, stg_dma.set_pars, 'wrong input')   # wrong input type
        self.assertRaises(ValueError, stg_dma.set_pars, (10, -100))  # par count does not match
        self.assertRaises(ValueError, stg_dma.set_pars, (10, 10, -10))   # par out of range
        wrong_dict_pars = {'a': (10, 20, 30),
                           'b': (11, 21, 31),
                           'c': (12, 22, 32)}
        self.assertRaises(ValueError, stg_trix.set_pars, wrong_dict_pars)  # par count not match in dict
        wrong_dict_pars = {'a': 'wrong_type',
                           'b': (11, 21),
                           'c': (12, 22)}
        self.assertRaises(TypeError, stg_trix.set_pars, wrong_dict_pars)  # wrong input type in dict
        wrong_dict_pars = {'a': (10, 20),
                           'b': (11, 21),
                           'c': (12, -22)}
        self.assertRaises(ValueError, stg_trix.set_pars, wrong_dict_pars)  # par out of range in dict
        # raise NotImplementedError

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
        """ test method __getitem__(), it should be the same as geting strategies by stg_id"""
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
        op.set_parameter('macd', strategy_run_timing='open')
        op.set_parameter('dma', strategy_run_timing='close')
        op.set_parameter('trix', strategy_run_timing='open')
        stg_close = op.get_strategies_by_run_timing('close')
        stg_open = op.get_strategies_by_run_timing('open')
        stg_high = op.get_strategies_by_run_timing('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, [op.strategies[1]])
        self.assertEqual(stg_open, [op.strategies[0], op.strategies[2]])
        self.assertEqual(stg_high, [])

        stg_wrong = op.get_strategies_by_run_timing(123)
        self.assertIsInstance(stg_wrong, list)
        self.assertEqual(stg_wrong, [])

    def test_get_strategy_count_by_run_timing(self):
        """ test get_strategy_count_by_run_timing"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', strategy_run_timing='open')
        op.set_parameter('dma', strategy_run_timing='close')
        op.set_parameter('trix', strategy_run_timing='open')
        stg_close = op.get_strategy_count_by_run_timing('close')
        stg_open = op.get_strategy_count_by_run_timing('open')
        stg_high = op.get_strategy_count_by_run_timing('high')

        self.assertIsInstance(stg_close, int)
        self.assertIsInstance(stg_open, int)
        self.assertIsInstance(stg_high, int)

        self.assertEqual(stg_close, 1)
        self.assertEqual(stg_open, 2)
        self.assertEqual(stg_high, 0)

        stg_wrong = op.get_strategy_count_by_run_timing(123)
        self.assertIsInstance(stg_wrong, int)
        self.assertEqual(stg_wrong, 0)

    def test_get_strategy_names_by_price_type(self):
        """ test get_strategy_names_by_price_type"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', strategy_run_timing='open')
        op.set_parameter('dma', strategy_run_timing='close')
        op.set_parameter('trix', strategy_run_timing='open')
        stg_close = op.get_strategy_names_by_run_timing('close')
        stg_open = op.get_strategy_names_by_run_timing('open')
        stg_high = op.get_strategy_names_by_run_timing('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, ['DMA'])
        self.assertEqual(stg_open, ['MACD', 'TRIX'])
        self.assertEqual(stg_high, [])

        stg_wrong = op.get_strategy_names_by_run_timing(123)
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
        op.set_parameter('macd', strategy_run_timing='open')
        op.set_parameter('dma', strategy_run_timing='close')
        op.set_parameter('trix', strategy_run_timing='open')
        stg_close = op.get_strategy_id_by_run_timing('close')
        stg_open = op.get_strategy_id_by_run_timing('open')
        stg_high = op.get_strategy_id_by_run_timing('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, ['dma'])
        self.assertEqual(stg_open, ['macd', 'trix'])
        self.assertEqual(stg_high, [])

        op.add_strategies('dma, macd')
        op.set_parameter('dma_1', strategy_run_timing='open')
        op.set_parameter('macd', strategy_run_timing='open')
        op.set_parameter('macd_1', strategy_run_timing='close')
        op.set_parameter('trix', strategy_run_timing='close')
        print(f'Operator strategy id:\n'
              f'{op.strategies} on memory pos:\n'
              f'{[id(stg) for stg in op.strategies]}')
        stg_close = op.get_strategy_id_by_run_timing('close')
        stg_open = op.get_strategy_id_by_run_timing('open')
        stg_all = op.get_strategy_id_by_run_timing()
        print(f'All IDs of strategies:\n'
              f'{stg_all}\n'
              f'All price types of strategies:\n'
              f'{[stg.strategy_run_timing for stg in op.strategies]}')
        self.assertEqual(stg_close, ['dma', 'trix', 'macd_1'])
        self.assertEqual(stg_open, ['macd', 'dma_1'])

        stg_wrong = op.get_strategy_id_by_run_timing(123)
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
        self.assertIsInstance(strategies[0], DMA)
        op = qt.Operator('dma, macd, cdl')
        strategies = op.strategies
        op.info()
        self.assertIsInstance(strategies, list)
        self.assertIsInstance(strategies[0], DMA)
        self.assertIsInstance(strategies[1], MACD)
        self.assertIsInstance(strategies[2], CDL)

    def test_property_strategy_count(self):
        """ test Property strategy_count, and the method get_strategy_count_by_run_timing()"""
        self.assertEqual(self.op.strategy_count, 1)
        self.assertEqual(self.op2.strategy_count, 3)
        self.assertEqual(self.op.get_strategy_count_by_run_timing(), 1)
        self.assertEqual(self.op2.get_strategy_count_by_run_timing(), 3)
        self.assertEqual(self.op.get_strategy_count_by_run_timing('close'), 1)
        self.assertEqual(self.op.get_strategy_count_by_run_timing('high'), 0)
        self.assertEqual(self.op2.get_strategy_count_by_run_timing('close'), 3)
        self.assertEqual(self.op2.get_strategy_count_by_run_timing('open'), 0)

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
        op.strategy_blenders = 's1+s2'
        self.assertEqual(op.strategy_blenders, {'close': ['+', 's2', 's1']})

        op.clear_strategies()
        self.assertEqual(op.strategy_blenders, {})
        op.add_strategies('dma, trix, macd, dma')
        op.set_parameter('dma', strategy_run_timing='open')
        op.set_parameter('trix', strategy_run_timing='close')

        op.set_blender('s1+s2', 'open')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(blender_open, ['+', 's2', 's1'])
        self.assertEqual(blender_close, None)
        self.assertEqual(blender_high, None)

        op.set_blender('s1+2+3', 'open')
        op.set_blender('s1+2+3', 'abc')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        blender_abc = op.get_blender('abc')
        self.assertEqual(op.strategy_blenders, {'open': ['+', '3', '+', '2', 's1']})
        self.assertEqual(blender_open, ['+', '3', '+', '2', 's1'])
        self.assertEqual(blender_close, None)
        self.assertEqual(blender_high, None)
        self.assertEqual(blender_abc, None)

        op.set_blender('s1+s1', None)
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        blender_high = op.get_blender('high')
        self.assertEqual(op.strategy_timings, ['close', 'open'])
        self.assertEqual(op.get_blender(), {'close': ['+', 's1', 's1'],
                                            'open':  ['+', 's1', 's1'], })
        self.assertEqual(blender_open, ['+', 's1', 's1'])
        self.assertEqual(blender_close, ['+', 's1', 's1'])

        op.set_blender(['s1+s2+1', 's0+4'])
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['+', '4', 's0'])
        self.assertEqual(blender_close, ['+', '1', '+', 's2', 's1'])
        self.assertEqual(op.view_blender('open'), 'dma + 4')
        self.assertEqual(op.view_blender('close'), 'macd + dma_1 + 1')

        op.strategy_blenders = (['s1+2', 's0*3'])
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['*', '3', 's0'])
        self.assertEqual(blender_close, ['+', '2', 's1'])
        self.assertEqual(op.view_blender('open'), 'dma * 3')
        self.assertEqual(op.view_blender('close'), 'macd + 2')

        # test error inputs:
        self.assertRaises(TypeError, op.set_blender, 123, 'open')
        # wrong type of price_type
        self.assertRaises(TypeError, op.set_blender, '1+3', 1)
        # price_type not found, no change is made
        op.set_blender('1+3', 'volume')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['*', '3', 's0'])
        self.assertEqual(blender_close, ['+', '2', 's1'])
        # price_type not valid, no change is made
        op.set_blender('1+2', 'wrong_timing')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['*', '3', 's0'])
        self.assertEqual(blender_close, ['+', '2', 's1'])
        # wrong type of blender, no change is made
        self.assertRaises(TypeError, op.set_blender, 55, 'open')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['*', '3', 's0'])
        self.assertEqual(blender_close, ['+', '2', 's1'])
        # wrong type of blender, no change is made
        self.assertRaises(TypeError, op.set_blender, ['1+2'], 'close')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['*', '3', 's0'])
        self.assertEqual(blender_close, ['+', '2', 's1'])
        # can't parse blender, raise and no change is made
        # self.assertWarns(Warning, op.set_blender, 'a+bc', 'high')
        self.assertRaises(ValueError, op.set_blender, 'a+bc', 'close')
        blender_open = op.get_blender('open')
        blender_close = op.get_blender('close')
        self.assertEqual(blender_open, ['*', '3', 's0'])
        self.assertEqual(blender_close, ['+', '2', 's1'])
        self.assertIs(blender_high, None)

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
        print(f'Error will be raised if Invalid signal type encountered')
        self.assertRaises(
                ValueError,
                qt.Operator,
                None,
                'wrong value',
                None
        )

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
        # op交易策略存在多个数据频率的情况尚未得到支持，以后支持该情况后可以实现下列功能
        # dtf = op.op_data_freq
        # self.assertIsInstance(dtf, list)
        # self.assertEqual(len(dtf), 2)
        # self.assertEqual(dtf[0], 'd')
        # self.assertEqual(dtf[1], 'm')

    def test_property_bt_price_types(self):
        """ test property strategy_timings"""
        print('------test property bt_price_tyeps-------')
        op = qt.Operator()
        self.assertIsInstance(op.strategy_timings, list)
        self.assertEqual(len(op.strategy_timings), 0)
        self.assertEqual(op.strategy_timings, [])

        op = qt.Operator('macd, dma, trix')
        btp = op.strategy_timings
        self.assertIsInstance(btp, list)
        self.assertEqual(btp[0], 'close')
        op.set_parameter('macd', strategy_run_timing='open')
        btp = op.strategy_timings
        btpc = op.bt_price_type_count
        print(f'price_types are \n{btp}')
        self.assertIsInstance(btp, list)
        self.assertEqual(len(btp), 2)
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.add_strategies(['dma', 'macd'])
        op.set_parameter('dma_1', strategy_run_timing='close')
        btp = op.strategy_timings
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.remove_strategy('dma_1')
        btp = op.strategy_timings
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.remove_strategy('macd_1')
        btp = op.strategy_timings
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
        op.set_parameter('macd', strategy_data_types='open, close')
        ohd = op.op_data_type_list
        print(f'ohd is {ohd}')
        self.assertIsInstance(ohd, list)
        self.assertEqual(len(ohd), 4)
        self.assertEqual(ohd[0], ['open', 'close'])
        self.assertEqual(ohd[1], ['close'])
        self.assertEqual(ohd[2], ['close'])
        self.assertEqual(ohd[3], ['open', 'high', 'low', 'close'])

    def test_property_op_history_data(self):
        """ Test this important function to get operation history arr that shall be used in
            signal generation
            these arr are stored in list of nd-arrays, each ndarray represents the arr
            that is needed for each and every strategy
        """
        print(f'------- Test getting operation history arr ---------')
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
        self.assertEqual(osp[0], [(10, 250), (10, 250), (5, 250), (10, 250), (10, 250), (5, 250)])
        self.assertEqual(osp[1], ['int', 'int', 'int', 'int', 'int', 'int'])

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
        op.set_parameter('macd', strategy_run_timing='open')
        op.set_parameter('dma', strategy_run_timing='open')
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
        #  a_to_sell.set_parameter('dma, cdl', price_type='open')
        op.set_parameter('dma', strategy_run_timing='open')
        op.set_parameter('cdl', strategy_run_timing='open')
        sb = op.strategy_blenders
        st = op.signal_type
        self.assertIsInstance(sb, dict)
        print(f'before setting: strategy_blenders={sb}')
        self.assertEqual(sb, {})
        op.strategy_blenders = '1+s2 * 3'
        sb = op.strategy_blenders
        print(f'after setting strategy_blender={sb}')
        self.assertEqual(sb, {'close': ['+', '*', '3', 's2', '1'],
                              'open':  ['+', '*', '3', 's2', '1']})
        op.strategy_blenders = ['s1+2', '3-s4']
        sb = op.strategy_blenders
        print(f'after setting strategy_blender={sb}')
        self.assertEqual(sb, {'close': ['+', '2', 's1'],
                              'open':  ['-', 's4', '3']})

    def test_operator_ready(self):
        """test the method ready of Operator"""
        op = qt.Operator()
        print(f'operator is ready? "{op.ready}"')

    def test_operator_add_strategy(self):
        """test adding strategies to Operator"""
        op = qt.Operator('dma, all, sellrate')

        self.assertIsInstance(op, qt.Operator)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[1], qt.built_in.SelectingAll)
        self.assertIsInstance(op.strategies[2], qt.built_in.SellRate)
        self.assertIsInstance(op[0], qt.built_in.DMA)
        self.assertIsInstance(op[1], qt.built_in.SelectingAll)
        self.assertIsInstance(op[2], qt.built_in.SellRate)
        self.assertIsInstance(op['dma'], qt.built_in.DMA)
        self.assertIsInstance(op['all'], qt.built_in.SelectingAll)
        self.assertIsInstance(op['sellrate'], qt.built_in.SellRate)
        self.assertEqual(op.strategy_count, 3)
        print(f'test adding strategies into existing op')
        print('test adding strategy by string')
        op.add_strategy('macd')
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[3], qt.built_in.MACD)
        self.assertEqual(op.strategy_count, 4)
        op.add_strategy('random')
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[4], qt.built_in.SelectingRandom)
        self.assertEqual(op.strategy_count, 5)
        test_ls = TestLSStrategy()
        op.add_strategy(test_ls)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[5], TestLSStrategy)
        self.assertEqual(op.strategy_count, 6)
        print(f'Test different instance of objects are added to operator')
        op.add_strategy('dma')
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[6], qt.built_in.DMA)
        self.assertIsNot(op.strategies[0], op.strategies[6])

    def test_operator_add_strategies(self):
        """ etst adding multiple strategies to Operator"""
        op = qt.Operator('dma, all, sellrate')
        self.assertEqual(op.strategy_count, 3)
        print('test adding multiple strategies -- adding strategy by list of strings')
        op.add_strategies(['dma', 'macd'])
        self.assertEqual(op.strategy_count, 5)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[3], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[4], qt.built_in.MACD)
        print('test adding multiple strategies -- adding strategy by comma separated strings')
        op.add_strategies('dma, macd')
        self.assertEqual(op.strategy_count, 7)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[5], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[6], qt.built_in.MACD)
        print('test adding multiple strategies -- adding strategy by list of strategies')
        op.add_strategies([qt.built_in.DMA(), qt.built_in.MACD()])
        self.assertEqual(op.strategy_count, 9)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[7], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[8], qt.built_in.MACD)
        print('test adding multiple strategies -- adding strategy by list of strategy and str')
        op.add_strategies(['DMA', qt.built_in.MACD()])
        self.assertEqual(op.strategy_count, 11)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[9], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[10], qt.built_in.MACD)
        self.assertIsNot(op.strategies[0], op.strategies[9])
        self.assertIs(type(op.strategies[0]), type(op.strategies[9]))
        print('test adding fault arr')
        self.assertRaises(AssertionError, op.add_strategies, 123)
        self.assertRaises(AssertionError, op.add_strategies, None)

    def test_operator_remove_strategy(self):
        """ test method remove strategy"""
        op = qt.Operator('dma, all, sellrate')
        op.add_strategies(['dma', 'macd'])
        op.add_strategies(['DMA', TestLSStrategy()])
        self.assertEqual(op.strategy_count, 7)
        print('test removing strategies from Operator')
        op.remove_strategy('dma')
        self.assertEqual(op.strategy_count, 6)
        self.assertEqual(op.strategy_ids, ['all', 'sellrate', 'dma_1', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['sellrate'])
        self.assertEqual(op.strategies[2], op['dma_1'])
        self.assertEqual(op.strategies[3], op['macd'])
        self.assertEqual(op.strategies[4], op['dma_2'])
        self.assertEqual(op.strategies[5], op['custom'])
        op.remove_strategy('dma_1')
        self.assertEqual(op.strategy_count, 5)
        self.assertEqual(op.strategy_ids, ['all', 'sellrate', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['sellrate'])
        self.assertEqual(op.strategies[2], op['macd'])
        self.assertEqual(op.strategies[3], op['dma_2'])
        self.assertEqual(op.strategies[4], op['custom'])

    def test_operator_clear_strategies(self):
        """ test operator clear strategies"""
        op = qt.Operator('dma, all, sellrate')
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
        self.assertEqual(type(op.strategies[0]), DMA)
        self.assertEqual(op.strategies[0].pars, (12, 123, 25))
        op.clear_strategies()
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

    def test_operator_assign_history_data(self):
        """测试分配Operator运行所需历史数据"""
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
        self.op.strategies[0].pars = None
        self.assertRaises(AssertionError,
                          self.op.assign_hist_data,
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
        self.op.assign_hist_data(
                hist_data=self.hp1,
                cash_plan=on_spot_cash,
        )  # TODO: 测试交易策略不需要使用当前数据周期的情况(stg.use_latest_data_cycle==False) for version 1.0.7
        # test if all historical data related properties are set
        self.assertIsInstance(self.op._op_list_shares, dict)
        self.assertIsInstance(self.op._op_list_hdates, dict)
        self.assertIsInstance(self.op._op_list_price_types, dict)

        self.assertIsInstance(self.op._op_history_data, dict)
        self.assertEqual(len(self.op._op_history_data), 3)
        self.assertEqual(list(self.op._op_history_data.keys()), ['custom', 'custom_1', 'custom_2'])
        self.assertIsInstance(self.op._op_hist_data_rolling_windows, dict)
        self.assertEqual(len(self.op._op_hist_data_rolling_windows), 3)
        self.assertEqual(list(self.op._op_hist_data_rolling_windows.keys()), ['custom', 'custom_1', 'custom_2'])
        print(self.op._op_hist_data_rolling_windows)
        self.assertEqual(self.op._op_hist_data_rolling_windows['custom'].shape, (45, 3, 5, 4))
        self.assertEqual(self.op._op_hist_data_rolling_windows['custom_1'].shape, (45, 3, 5, 3))
        self.assertEqual(self.op._op_hist_data_rolling_windows['custom_2'].shape, (45, 3, 2, 4))

        target_hist_data_rolling_window = np.array(
                [[[10.04, 10.02, 10.07, 9.99],
                  [10., 10., 10., 10.],
                  [10., 9.98, 10., 9.97],
                  [9.99, 9.97, 10., 9.97],
                  [9.97, 9.99, 10.03, 9.97]],

                 [[9.68, 9.88, 9.91, 9.63],
                  [9.87, 9.88, 10.04, 9.84],
                  [9.86, 9.89, 9.93, 9.81],
                  [9.87, 9.75, 10.04, 9.74],
                  [9.79, 9.74, 9.84, 9.67]],

                 [[6.64, 7.26, 7.41, 6.53],
                  [7.26, 7., 7.31, 6.87],
                  [7.03, 6.88, 7.14, 6.83],
                  [6.87, 6.91, 7., 6.7],
                  [np.nan, np.nan, np.nan, np.nan]]]
        )
        target_comparison = np.allclose(self.op._op_hist_data_rolling_windows['custom'][0],
                                        target_hist_data_rolling_window,
                                        equal_nan=True)
        self.assertTrue(target_comparison)
        target_hist_data_rolling_window = np.array(
                [[[10.07, 9.99, 10.04],
                  [10., 10., 10.],
                  [10., 9.97, 10.],
                  [10., 9.97, 9.99],
                  [10.03, 9.97, 9.97]],

                 [[9.91, 9.63, 9.68],
                  [10.04, 9.84, 9.87],
                  [9.93, 9.81, 9.86],
                  [10.04, 9.74, 9.87],
                  [9.84, 9.67, 9.79]],

                 [[7.41, 6.53, 6.64],
                  [7.31, 6.87, 7.26],
                  [7.14, 6.83, 7.03],
                  [7., 6.7, 6.87],
                  [np.nan, np.nan, np.nan]]]
        )
        target_comparison = np.allclose(self.op._op_hist_data_rolling_windows['custom_1'][0],
                                        target_hist_data_rolling_window,
                                        equal_nan=True)
        self.assertTrue(target_comparison)
        target_hist_data_rolling_window = np.array(
                [[[9.99, 9.97, 10., 9.97],
                  [9.97, 9.99, 10.03, 9.97]],

                 [[9.87, 9.75, 10.04, 9.74],
                  [9.79, 9.74, 9.84, 9.67]],

                 [[6.87, 6.91, 7., 6.7],
                  [np.nan, np.nan, np.nan, np.nan]]]
        )
        target_comparison = np.allclose(self.op._op_hist_data_rolling_windows['custom_2'][0],
                                        target_hist_data_rolling_window,
                                        equal_nan=True)
        self.assertTrue(target_comparison)
        # test if automatic strategy blenders are set
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['+', 's2', '+', 's1', 's0']})
        tim_hist_data = self.op._op_history_data['custom']
        sel_hist_data = self.op._op_history_data['custom_1']
        ric_hist_data = self.op._op_history_data['custom_2']

        print(f'in test_prepare_data in TestOperator:')
        print('selecting history arr:\n', sel_hist_data)
        print('originally passed arr in correct sequence:\n', self.test_data_3D[:, 3:, [2, 3, 0]])
        print('difference is \n', sel_hist_data - self.test_data_3D[:, :, [2, 3, 0]])
        self.assertTrue(np.allclose(sel_hist_data, self.test_data_3D[:, :, [2, 3, 0]], equal_nan=True))
        self.assertTrue(np.allclose(tim_hist_data, self.test_data_3D, equal_nan=True))
        self.assertTrue(np.allclose(ric_hist_data, self.test_data_3D[:, :, :], equal_nan=True))

        # raises Value Error if empty history panel is given
        empty_hp = qt.HistoryPanel()
        correct_hp = qt.HistoryPanel(values=np.random.randint(10, size=(3, 50, 4)),
                                     columns=self.types,
                                     levels=self.shares,
                                     rows=self.date_indices)
        too_many_shares = qt.HistoryPanel(values=np.random.randint(10, size=(5, 50, 4)),
                                          columns=self.types,
                                          rows=self.date_indices)
        too_many_types = qt.HistoryPanel(values=np.random.randint(10, size=(3, 50, 5)),
                                         rows=self.date_indices)
        # raises Error when history panel is empty
        self.assertRaises(ValueError,
                          self.op.assign_hist_data,
                          empty_hp,
                          on_spot_cash)
        # raises Error when first investment date is too early
        self.assertRaises(ValueError,
                          self.op.assign_hist_data,
                          correct_hp,
                          early_cash)
        # raises Error when last investment date is too late
        self.assertRaises(ValueError,
                          self.op.assign_hist_data,
                          correct_hp,
                          late_cash)
        # # raises Error when number of shares in history data does not fit
        # self.assertRaises(AssertionError,
        #                   self.op.assign_hist_data,
        #                   too_many_shares,
        #                   on_spot_cash)
        # raises Error when too early cash investment date
        self.assertRaises(ValueError,
                          self.op.assign_hist_data,
                          correct_hp,
                          too_early_cash)
        # raises Error when number of d_types in history data does not fit
        self.assertRaises(KeyError,
                          self.op.assign_hist_data,
                          too_many_types,
                          on_spot_cash)

        # test the effect of data type sequence in strategy definition

    def test_operator_generate(self):
        """ 测试operator对象生成完整交易信号

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
        self.op.assign_hist_data(
                hist_data=self.hp1,
                cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000),
        )
        print('--test operator information in normal mode--')
        self.op.info()
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['+', 's1', 's0']})
        self.op.set_blender('s0*s1')
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['*', 's1', 's0']})
        print('--test operation signal created in Proportional Target (PT) Mode--')
        op_list = self.op.create_signal()

        self.assertTrue(isinstance(op_list, np.ndarray))
        backtest_price_types = self.op.op_list_price_types
        self.assertEqual(backtest_price_types, ['close'])
        self.assertEqual(op_list.shape, (3, 45, 1))
        reduced_op_list = op_list.squeeze().T
        print(f'op_list created, it is a 3 share/45 days/1 htype array, to make comparison happen, \n'
              f'it will be squeezed to a 2-d array to compare on share-wise:\n'
              f'{reduced_op_list}')
        target_op_values = np.array([[0.0, 0.0, 0.0],
                                     [0.0, 0.0, 0.0],
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
                              strategy_run_timing='open')
        self.op.set_parameter(stg_id='custom_3',
                              strategy_run_timing='open')
        self.assertEqual(self.op['custom'].strategy_run_timing, 'close')
        self.assertEqual(self.op['custom_2'].strategy_run_timing, 'open')
        self.op.set_parameter(stg_id='custom_2',
                              pars={'000010': (5, 10.),
                                    '000030': (5, 10.),
                                    '000039': (5, 6.)})
        self.op.set_parameter(stg_id='custom_3',
                              pars=())
        self.op.set_blender(blender='s0 or s1', run_timing='open')
        self.op.assign_hist_data(
                hist_data=self.hp1,
                cash_plan=qt.CashPlan(dates='2016-07-08', amounts=10000),
        )
        print('--test how operator information is printed out--')
        self.op.info()
        self.assertEqual(self.op.strategy_blenders,
                         {'close': ['*', 's1', 's0'],
                          'open':  ['or', 's1', 's0']})
        print('--test opeartion signal created in Proportional Target (PT) Mode--')
        op_list = self.op.create_signal()

        self.assertTrue(isinstance(op_list, np.ndarray))
        signal_close = op_list[:, :, 0].squeeze().T
        signal_open = op_list[:, :, 1].squeeze().T
        self.assertEqual(signal_close.shape, (45, 3))
        self.assertEqual(signal_open.shape, (45, 3))

        target_op_close = np.array([[0.0, 0.0, 0.0],
                                    [0.0, 0.0, 0.0],
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
                                   [1.0, 1.0, 1.0],
                                   [1.0, 1.0, 1.0],
                                   [1.0, 1.0, 1.0],
                                   [1.0, 0.5, 0.0],
                                   [1.0, 0.5, 0.0],
                                   [1.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.0, 1.0, 0.5],
                                   [0.5, 1.0, 0.0],
                                   [0.5, 1.0, 0.0],
                                   [0.5, 1.0, 0.0],
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

    def test_operator_generate_stepwise(self):
        """ 测试operator对象在实时模式下生成交易信号

        :return:
        """
        # TODO: implement this test
        pass

    def test_stg_parameter_setting(self):
        """ test setting parameters of strategies
        test the method set_parameters

        :return:
        """
        op = qt.Operator(strategies='dma, all, sellrate')
        print(op.strategies, '\n', [qt.built_in.DMA, qt.built_in.SelectingAll, qt.built_in.SellRate])
        print(f'info of Timing strategy in new op: \n{op.strategies[0].info()}')
        # TODO: allow set_parameters to a list of strategies or str-listed strategies
        # TODO: allow set_parameters to all strategies of specific bt price type
        print(f'Set up strategy parameters by strategy id')
        op.set_parameter('dma',
                         opt_tag=1,
                         par_range=((5, 10), (5, 15), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('dma',
                         pars=(5, 10, 5))
        op.set_parameter('all',
                         window_length=20)
        op.set_parameter('all', strategy_run_timing='close')
        print(f'Can also set up strategy parameters by strategy index')
        op.set_parameter(2, strategy_run_timing='open')
        op.set_parameter(2,
                         opt_tag=1,
                         pars=(9, -0.09),
                         window_length=10)
        self.assertEqual(op.strategies[0].pars, (5, 10, 5))
        self.assertEqual(op.strategies[0].par_range, ((5, 10), (5, 15), (5, 15)))
        self.assertEqual(op.strategies[2].pars, (9, -0.09))
        self.assertEqual(op.op_data_freq, 'd')
        self.assertEqual(op.op_data_types, ['close', 'high', 'open'])
        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (5, 15), (1, 100), (-0.5, 0.5)],
                          ['int', 'int', 'int', 'int', 'float']))
        self.assertEqual(op.max_window_length, 20)
        print(f'KeyError will be raised if wrong strategy id is given')
        self.assertRaises(KeyError, op.set_parameter, stg_id='t-1', pars=(1, 2))
        self.assertRaises(KeyError, op.set_parameter, stg_id='wrong_input', pars=(1, 2))
        print(f'ValueError will be raised if parameter can be set')
        self.assertRaises(ValueError, op.set_parameter, stg_id=0, pars=('wrong input', 'wrong input'))
        # test blenders of different price types
        # test setting blenders to different price types

        # self.assertEqual(a_to_sell.get_blender('close'), 'str-1.2')
        self.assertEqual(op.strategy_timings, ['close', 'open'])
        op.set_blender('s0 and s1 or s2', 'open')
        self.assertEqual(op.get_blender('open'), ['or', 's2', 'and', 's1', 's0'])
        op.set_blender('s0 or s1 and s2', 'close')
        self.assertEqual(op.get_blender(), {'close': ['or', 'and', 's2', 's1', 's0'],
                                            'open':  ['or', 's2', 'and', 's1', 's0']})

        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (5, 15), (1, 100), (-0.5, 0.5)],
                          ['int', 'int', 'int', 'int', 'float']))
        self.assertEqual(op.opt_tags, [1, 0, 1])

    def test_signal_blend(self):
        self.assertEqual(blender_parser('s0 & 1'), ['&', '1', 's0'])
        self.assertEqual(blender_parser('s0 or 1'), ['or', '1', 's0'])
        self.assertEqual(blender_parser('s0 & s1 | s2'), ['|', 's2', '&', 's1', 's0'])
        blender = blender_parser('s0 & s1 | s2')
        self.assertEqual(signal_blend([1, 1, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 1, 0], blender), 1)
        self.assertEqual(signal_blend([0, 1, 1], blender), 1)
        self.assertEqual(signal_blend([0, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 0], blender), 0)
        self.assertEqual(signal_blend([0, 1, 0], blender), 0)
        self.assertEqual(signal_blend([0, 0, 0], blender), 0)
        # parse: '0 & ( 1 | 2 )'
        self.assertEqual(blender_parser('s0 & ( s1 | s2 )'), ['&', '|', 's2', 's1', 's0'])
        blender = blender_parser('s0 & ( s1 | s2 )')
        self.assertEqual(signal_blend([1, 1, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 1, 0], blender), 1)
        self.assertEqual(signal_blend([0, 1, 1], blender), 0)
        self.assertEqual(signal_blend([0, 0, 1], blender), 0)
        self.assertEqual(signal_blend([1, 0, 0], blender), 0)
        self.assertEqual(signal_blend([0, 1, 0], blender), 0)
        self.assertEqual(signal_blend([0, 0, 0], blender), 0)
        # parse: '(1-2) and 3 + ~0'
        self.assertEqual(blender_parser('(s1-s2)/s3 + s0'), ['+', 's0', '/', 's3', '-', 's2', 's1'])
        blender = blender_parser('(s1-s2)/s3 + s0')
        self.assertEqual(signal_blend([5, 9, 1, 4], blender), 7)
        # parse: '(1-2)/3 + 0'
        self.assertEqual(blender_parser('(s1-s2)/s3 + s0'), ['+', 's0', '/', 's3', '-', 's2', 's1'])
        blender = blender_parser('(s1-s2)/s3 + s0')
        self.assertEqual(signal_blend([5, 9, 1, 4], blender), 7)
        # pars: '(0*1/2*(3+4))+5*(6+7)-8'
        self.assertEqual(blender_parser('(s0*s1/s2*(s3+s4))+s5*(s6+s7)-s8'),
                         ['-', 's8', '+', '*', '+', 's7', 's6', 's5', '*', '+', 's4', 's3', '/', 's2', '*', 's1', 's0'])
        blender = blender_parser('(s0*s1/s2*(s3+s4))+s5*(s6+s7)-s8')
        self.assertEqual(signal_blend([1, 1, 1, 1, 1, 1, 1, 1, 1], blender), 3)
        self.assertEqual(signal_blend([2, 1, 4, 3, 5, 5, 2, 2, 10], blender), 14)
        # parse: '0/max(2,1,3 + 5)+4'
        self.assertEqual(blender_parser('s0/max(s2,s1,s3 + s5)+s4'),
                         ['+', 's4', '/', 'max(3)', '+', 's5', 's3', 's1', 's2', 's0'])
        blender = blender_parser('s0/max(s2,s1,s3 + 5)+s4')
        self.assertEqual(signal_blend([8.0, 4, 3, 5.0, 0.125, 5], blender), 0.925)
        self.assertEqual(signal_blend([2, 1, 4, 3, 5, 5, 2, 2, 10], blender), 5.25)

        print('speed test')
        import time
        st = time.time()
        blender = blender_parser('s0+max(s1,s2,(s3+s4)*s5, max(s6, (s7+s8)*s9), s10-s11) * (s12+s13)')
        res = []
        for i in range(10000):
            res = signal_blend([1, 1, 2, 3, 4, 5, 3, 4, 5, 6, 7, 8, 2, 3], blender)
        et = time.time()
        print(f'total time for RPN processing: {et - st}, got result: {res}')

        blender = blender_parser("s0 + s1 * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 7)
        blender = blender_parser("(s0 + s1) * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(s0+s1) * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(s0 + s1)   * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(s0-s1)/s2 + s3")
        print(f'RPN of notation: "(s0-s1)/s2 + s3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), -0.33333333)
        blender = blender_parser("-(s0-s1)/s2 + s3")
        print(f'RPN of notation: "-(s0-s1)/s2 + s3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), 0.33333333)
        blender = blender_parser("~(0-1)/s2 + s3")
        print(f'RPN of notation: "~(s0-s1)/s2 + s3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), 0.33333333)
        blender = blender_parser("s0 + s1 / s2")
        print(f'RPN of notation: "0 + 1 / 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, math.pi, 4], blender), 1.78539816)
        blender = blender_parser("(s0 + s1) / s2")
        print(f'RPN of notation: "(0 + 1) / 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(signal_blend([1, 2, 3], blender), 1)
        blender = blender_parser("(s0 + s1 * s2) / s3")
        print(f'RPN of notation: "(0 + 1 * 2) / 3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([3, math.e, 10, 10], blender), 3.0182818284590454)
        blender = blender_parser("s0 / s1 * s2")
        print(f'RPN of notation: "0 / 1 * 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(signal_blend([1, 3, 6], blender), 2)
        blender = blender_parser("(s0 - s1 + s2) * s4")
        print(f'RPN of notation: "(0 - 1 + 2) * 4" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 1, -1, np.nan, math.pi], blender), -3.141592653589793)
        blender = blender_parser("s0 * s1")
        print(f'RPN of notation: "0 * 1" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([math.pi, math.e], blender), 8.539734222673566)

        blender = blender_parser('abs(s3-sqrt(s2) /  cos(s1))')
        print(f'RPN of notation: "abs(3-sqrt(2) /  cos(1))" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['abs(1)', '-', '/', 'cos(1)', 's1', 'sqrt(1)', 's2', 's3'])
        blender = blender_parser('s0/max(s2,s1,s3 + s5)+s4')
        print(f'RPN of notation: "0/max(2,1,3 + 5)+4" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', 's4', '/', 'max(3)', '+', 's5', 's3', 's1', 's2', 's0'])

        blender = blender_parser('s1 + sum(s1,s2,s3+s3, sum(s1, s2) + s3) *s5')
        print(f'RPN of notation: "1 + sum(1,2,3+3, sum(1, 2) + 3) *5" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '*', 's5', 'sum(4)', '+', 's3', 'sum(2)', 's2', 's1',
                                   '+', 's3', 's3', 's2', 's1', 's1'])
        blender = blender_parser('s1+sum(1,2,(s3+s5)*s4, sum(s3, (4+s5)*s6), s7-s8) * (s2+s3)')
        print(f'RPN of notation: "1+sum(1,2,(3+5)*4, sum(3, (4+5)*6), 7-8) * (2+3)" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '*', '+', 's3', 's2', 'sum(5)', '-', 's8', 's7',
                                   'sum(2)', '*', 's6', '+', 's5', '4', 's3', '*', 's4',
                                   '+', 's5', 's3', '2', '1', 's1'])

    def test_tokenizer(self):
        self.assertListEqual(_exp_to_token('s1+s1'),
                             ['s1', '+', 's1'])
        print(_exp_to_token('s1+s1'))
        self.assertListEqual(_exp_to_token('1+1'),
                             ['1', '+', '1'])
        print(_exp_to_token('1+1'))
        self.assertListEqual(_exp_to_token('1 & 1'),
                             ['1', '&', '1'])
        print(_exp_to_token('1&1'))
        self.assertListEqual(_exp_to_token('1 and 1'),
                             ['1', 'and', '1'])
        print(_exp_to_token('1 and 1'))
        self.assertListEqual(_exp_to_token('-1 and 1'),
                             ['-1', 'and', '1'])
        print(_exp_to_token('s0 and s1'))
        self.assertListEqual(_exp_to_token('s0 or s1'),
                             ['s0', 'or', 's1'])
        print(_exp_to_token('1 and 1'))
        self.assertListEqual(_exp_to_token('1 or 1'),
                             ['1', 'or', '1'])
        print(_exp_to_token('1 or 1'))
        self.assertListEqual(_exp_to_token('(1 - 1 + -1) * pi'),
                             ['(', '1', '-', '1', '+', '-1', ')', '*', 'pi'])
        print(_exp_to_token('(1 - 1 + -1) * pi'))
        self.assertListEqual(_exp_to_token('(s1 - s1 + -1) * pi'),
                             ['(', 's1', '-', 's1', '+', '-1', ')', '*', 'pi'])
        print(_exp_to_token('(s1 - s1 + -1) * pi'))
        self.assertListEqual(_exp_to_token('abs(5-sqrt(2) /  cos(pi))'),
                             ['abs(', '5', '-', 'sqrt(', '2', ')', '/', 'cos(', 'pi', ')', ')'])
        print(_exp_to_token('abs(5-sqrt(2) /  cos(pi))'))
        self.assertListEqual(_exp_to_token('abs(s5-sqrt(s2) /  cos(pi))'),
                             ['abs(', 's5', '-', 'sqrt(', 's2', ')', '/', 'cos(', 'pi', ')', ')'])
        print(_exp_to_token('abs(s5-sqrt(s2) /  cos(pi))'))
        self.assertListEqual(_exp_to_token('sin(pi) + 2.14'),
                             ['sin(', 'pi', ')', '+', '2.14'])
        print(_exp_to_token('sin(pi) + 2.14'))
        self.assertListEqual(_exp_to_token('-sin(pi) + 2.14'),
                             ['-1', '*', 'sin(', 'pi', ')', '+', '2.14'])
        print(_exp_to_token('-sin(pi) + 2.14'))
        self.assertListEqual(_exp_to_token('(1-2)/3.0 + 0.0000'),
                             ['(', '1', '-', '2', ')', '/', '3.0', '+', '0.0000'])
        print(_exp_to_token('(1-2)/3.0 + 0.0000'))
        self.assertListEqual(_exp_to_token('-(1. + .2) * max(1, 3, 5)'),
                             ['-1', '*', '(', '1.', '+', '.2', ')', '*', 'max(', '1', ',', '3', ',', '5', ')'])
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
        self.assertListEqual(_exp_to_token('abs(-1.14)+power(2, 3)and log(3.14)'),
                             ['abs(', '-1.14', ')', '+', 'power(', '2', ',', '3', ')', 'and', 'log(', '3.14', ')'])
        print(_exp_to_token('abs(-1.14)+power(2, 3)and log(3.14)'))
        self.assertListEqual(_exp_to_token('strength_1.25(0, 1, 2)'),
                             ['strength_1.25(', '0', ',', '1', ',', '2', ')'])
        print(_exp_to_token('strength_1.25(0, 1, 2)'))
        self.assertListEqual(_exp_to_token('avg_pos_3_1.25(0, 1,2)'),
                             ['avg_pos_3_1.25(', '0', ',', '1', ',', '2', ')'])
        print(_exp_to_token('avg_pos_3_1.25(0, 1,2)'))
        self.assertListEqual(_exp_to_token('clip_-1_1(pos_5_0.2(0, 1, 2, 3, 4))'),
                             ['clip_-1_1(', 'pos_5_0.2(', '0', ',', '1', ',', '2', ',', '3', ',', '4', ')', ')'])
        print(_exp_to_token('clip_-1_1(pos_5_0.2(0, 1, 2, 3, 4))'))

    def test_all_blending_funcs(self):
        """ 测试其他信号组合函数是否正常工作"""
        # 生成五个示例交易信号
        signal0 = np.array([[0.12, 0.35, 0.11],
                            [0.81, 0.22, 0.29],
                            [0.86, 0.47, 0.29],
                            [0.46, 0.81, 0.60],
                            [0.42, 0.55, 0.74]])
        signal1 = np.array([[0.94, 0.66, 0.69],
                            [0.85, 0.30, 0.65],
                            [0.87, 0.06, 0.24],
                            [0.73, 0.20, 0.19],
                            [0.43, 0.18, 0.44]])
        signal2 = np.array([[0.24, 0.81, 0.44],
                            [0.66, 0.92, 0.99],
                            [0.18, 0.17, 0.11],
                            [0.48, 0.57, 0.55],
                            [0.37, 0.66, 0.01]])
        signal3 = np.array([[0.92, 0.88, 0.16],
                            [0.89, 0.79, 0.27],
                            [0.48, 0.77, 0.20],
                            [0.43, 0.33, 0.25],
                            [0.90, 0.30, 0.49]])
        signal4 = np.array([[0.05, 0.17, 0.30],
                            [0.16, 0.62, 0.61],
                            [0.52, 0.83, 0.57],
                            [0.16, 0.36, 0.28],
                            [0.99, 0.57, 0.04]])
        # 将示例信号组合为交易信号组，与operator输出形式相同
        signals = [signal0, signal1, signal2, signal3, signal4]

        # 开始测试blender functions
        print('\ntest average functions')
        blender_exp = 'avg(s0, s1, s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.454, 0.574, 0.340],
                           [0.674, 0.570, 0.562],
                           [0.582, 0.460, 0.282],
                           [0.452, 0.454, 0.374],
                           [0.622, 0.452, 0.344]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest comparison functions')
        blender_exp = 'combo(s0, s1, s2) + min(s0, s1,s2)-max(s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.50,  1.29,  0.91],
                           [2.09,  0.74,  1.23],
                           [1.57, -0.07,  0.18],
                           [1.65,  1.21,  0.98],
                           [0.60,  0.91,  0.71]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest mathematical functions')
        blender_exp = 'abs(s0) + ceil(s1) * pow(s0, s1) + floor(s2+s3+s4) - exp(s3) and log(s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[8.77344165, 6.12214254, 1.74092762],
                           [7.10858499, 3.90823377, 2.38476921],
                           [3.79382222, 2.82813777, 1.71955085],
                           [4.84445021, 4.18981584, 4.14202468],
                           [3.13336769, 3.20675832, 6.87013820]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function strength')
        blender_exp = 'strength_1.35(s0, s1, s2)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0., 1., 0.],
                           [1., 1., 1.],
                           [1., 0., 0.],
                           [1., 1., 0.],
                           [0., 1., 0.]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function position')
        blender_exp = 'pos_3_0.5(s0, s1, s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0., 1., 0.],
                           [1., 1., 1.],
                           [1., 0., 0.],
                           [0., 0., 0.],
                           [0., 1., 0.]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function clip')
        blender_exp = 'clip_-1_0.8(pos_5_0.2(s0, s1, s2, s3, s4))'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.0, 0.0, 0.0],
                           [0.0, 0.8, 0.8],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.8, 0.0],
                           [0.8, 0.0, 0.0]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function avg position')
        blender_exp = 'avgpos_3_0.5(s0, s1, s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.000, 0.574, 0.000],
                           [0.674, 0.570, 0.562],
                           [0.582, 0.000, 0.000],
                           [0.000, 0.000, 0.000],
                           [0.000, 0.452, 0.000]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function unify')
        blender_exp = 'unify(avgpos_3_0.5(s0, s1, s2, s3, s4))'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.00000000, 1.00000000, 0.00000000],
                           [0.37320044, 0.31561462, 0.31118494],
                           [1.00000000, 0.00000000, 0.00000000],
                           [0.00000000, 0.00000000, 0.00000000],
                           [0.00000000, 1.00000000, 0.00000000]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function with pure numbers')
        blender_exp = 'avgpos_3_0.5(s0, 1.5*s1, 2*s2, 0.5*s3, 2+s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.000, 1.114, 0.881],
                           [1.202, 0.000, 1.198],
                           [1.057, 0.000, 0.000],
                           [0.978, 0.955, 0.878],
                           [1.049, 0.972, 0.741]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        # test human_blender function:
        print('\ntest human_blender function')
        strategy_ids = ['MACD', 'DMA', 'CROSSLINE', 'TRIX', 'KDJ']
        blender_exp = 'avgpos_3_0.5(s0, s1, s2, s3, s4)'
        res = human_blender(blender_exp, strategy_ids)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        self.assertEqual(res, 'avgpos_3_0.5(MACD, DMA, CROSSLINE, TRIX, KDJ)')

        blender_exp = 'max(s0, s1, s2)+s3*s4'
        res = human_blender(blender_exp, strategy_ids)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        self.assertEqual(res, 'max(MACD, DMA, CROSSLINE) + TRIX * KDJ')

        blender_exp = 'max(s0, s1/s0)+s1and0.5*s4'
        res = human_blender(blender_exp, strategy_ids)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        self.assertEqual(res, 'max(MACD, DMA / MACD) + DMA and 0.5 * KDJ')

        blender_exp = 'max(s0, s1/s0)+s1^0.5*s6'
        self.assertRaises(IndexError, human_blender, blender_exp, strategy_ids)

    def test_set_opt_par(self):
        """ test setting opt pars in batch"""
        print(f'--------- Testing setting Opt Pars: set_opt_par -------')
        op = qt.Operator('dma, random, crossline')
        op.set_parameter('dma',
                         opt_tag=1,
                         par_range=((5, 10), (5, 15), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('dma',
                         pars=(5, 10, 5))
        self.assertEqual(op.strategies[0].pars, (5, 10, 5))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (35, 120, 0.02))
        self.assertEqual(op.opt_tags, [1, 0, 0])
        op.set_opt_par((5, 12, 9))
        self.assertEqual(op.strategies[0].pars, (5, 12, 9))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (35, 120, 0.02))

        op.set_parameter('crossline',
                         opt_tag=1,
                         par_range=((5, 10), (5, 35), (0, 1)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('crossline',
                         pars=(5, 10, 0.1))
        self.assertEqual(op.opt_tags, [1, 0, 1])
        op.set_opt_par((5, 12, 9, 8, 26, 0.09))
        self.assertEqual(op.strategies[0].pars, (5, 12, 9))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (8, 26, 0.09))

        op.set_opt_par((9, 200, 155, 8, 26, 0.09, 5, 12, 9))
        self.assertEqual(op.strategies[0].pars, (9, 200, 155))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (8, 26, 0.09))

        # test set_opt_par when opt_tag is set to be 2 (enumerate type of parameters)
        op.set_parameter('crossline',
                         opt_tag=2,
                         par_range=((5, 10), (5, 35), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('crossline',
                         pars=(5, 10, 5))
        self.assertEqual(op.opt_tags, [1, 0, 2])
        self.assertEqual(op.strategies[0].pars, (9, 200, 155))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (5, 10, 5))
        op.set_opt_par((5, 12, 9, (8, 26, 9)))
        self.assertEqual(op.strategies[0].pars, (5, 12, 9))
        self.assertEqual(op.strategies[1].pars, (0.5,))
        self.assertEqual(op.strategies[2].pars, (8, 26, 9))

        # Test Errors
        # op.set_opt_par主要在优化过程中自动生成，已经保证了参数的正确性，因此不再检查参数正确性

    def test_stg_attribute_get_and_set(self):
        self.stg = qt.built_in.CROSSLINE()
        self.stg_type = 'RULE-ITER'
        self.stg_name = "CROSSLINE"
        self.stg_text = 'Moving average crossline strategy, determine long/short position according to the cross ' \
                        'point' \
                        ' of long and short term moving average prices '
        self.pars = (35, 120, 0.02)
        self.par_boes = [(10, 250), (10, 250), (0, 0.1)]
        self.par_count = 3
        self.par_types = ['int', 'int', 'float']
        self.opt_tag = 0
        self.data_types = ['close']
        self.data_freq = 'd'
        self.sample_freq = 'd'
        self.window_length = 270

        self.assertEqual(self.stg.stg_type, self.stg_type)
        self.assertEqual(self.stg.name, self.stg_name)
        self.assertEqual(self.stg.description, self.stg_text)
        self.assertEqual(self.stg.pars, self.pars)
        self.assertEqual(self.stg.par_types, self.par_types)
        self.assertEqual(self.stg.par_range, self.par_boes)
        self.assertEqual(self.stg.par_count, self.par_count)
        self.assertEqual(self.stg.opt_tag, self.opt_tag)
        self.assertEqual(self.stg.data_freq, self.data_freq)
        self.assertEqual(self.stg.strategy_run_freq, self.sample_freq)
        self.assertEqual(self.stg.data_types, self.data_types)
        self.assertEqual(self.stg.window_length, self.window_length)
        self.stg.name = 'NEW NAME'
        self.stg.description = 'NEW TEXT'
        self.assertEqual(self.stg.name, 'NEW NAME')
        self.assertEqual(self.stg.description, 'NEW TEXT')
        self.stg.pars = (10, 20, 0.03)
        self.assertEqual(self.stg.pars, (10, 20, 0.03))
        self.stg.par_count = 3
        self.assertEqual(self.stg.par_count, 3)
        self.stg.par_range = [(1, 10), (1, 10), (1, 10), (1, 10)]
        self.assertEqual(self.stg.par_range, [(1, 10), (1, 10), (1, 10), (1, 10)])
        self.stg.par_types = ['float', 'float', 'int', 'enum']
        self.assertEqual(self.stg.par_types, ['float', 'float', 'int', 'enum'])
        self.stg.par_types = 'float, float, int, float'
        self.assertEqual(self.stg.par_types, ['float', 'float', 'int', 'float'])
        self.stg.data_types = 'close, open'
        self.assertEqual(self.stg.data_types, ['close', 'open'])
        self.stg.data_types = ['close', 'high', 'low']
        self.assertEqual(self.stg.data_types, ['close', 'high', 'low'])
        self.stg.data_freq = 'w'
        self.assertEqual(self.stg.data_freq, 'w')
        self.stg.window_length = 300
        self.assertEqual(self.stg.window_length, 300)

    def test_rule_iterator(self):
        """测试rule_iterator类型策略"""
        stg = TestLSStrategy()
        self.assertIsInstance(stg, BaseStrategy)
        self.assertIsInstance(stg, RuleIterator)
        stg_pars = {'000100': (5, 10),
                    '000200': (5, 10),
                    '000300': (5, 6)}
        stg.set_pars(stg_pars)
        history_data = self.hp1.values[:, :-1]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)

        # test strategy generate with only hist_data
        print(f'test strategy generate with only hist_data')
        output = stg.generate(hist_data=history_data_rolling_window,
                              data_idx=np.arange(len(history_data_rolling_window)))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0]])
        self.assertEqual(output.shape, lsmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {lsmask[i]}')
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

        # test strategy generate with history data and reference_data
        print(f'\ntest strategy generate with reference_data')
        ref_data = self.test_ref_data[0, :, :]
        ref_rolling_window = rolling_window(ref_data, stg.window_length, 0)
        output = stg.generate(hist_data=history_data_rolling_window,
                              ref_data=ref_rolling_window,
                              data_idx=np.arange(len(history_data_rolling_window)))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[1.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 1.0]])
        self.assertEqual(output.shape, lsmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {lsmask[i]}')
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

        # test strategy generate with trade_data
        print(f'\ntest strategy generate with trade_data')
        output = []
        trade_data = np.empty(shape=(3, 5))  # 生成的trade_data符合5行
        trade_data.fill(np.nan)
        recent_prices = np.zeros(shape=(3,))
        for step in range(len(history_data_rolling_window)):
            output.append(
                    stg.generate(
                            hist_data=history_data_rolling_window,
                            trade_data=trade_data,
                            data_idx=step
                    )
            )
            current_prices = history_data_rolling_window[step, :, -1, 0]
            current_signals = output[-1]
            recent_prices = np.where(current_signals == 1., current_prices, recent_prices)
            trade_data[:, 4] = recent_prices
        output = np.array(output, dtype='float')

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[1.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0]])
        self.assertEqual(output.shape, lsmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {lsmask[i]}')
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

    def test_general_strategy(self):
        """ 测试第一种基础策略类General Strategy"""
        # test strategy with only history data
        stg = TestSelStrategy()
        self.assertIsInstance(stg, BaseStrategy)
        self.assertIsInstance(stg, GeneralStg)
        stg_pars = ()
        stg.set_pars(stg_pars)
        history_data = self.hp1['high, low, close', :, :-1]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)

        output = stg.generate(hist_data=history_data_rolling_window,
                              data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test strategy with history data and reference data
        print(f'\ntest strategy generate with reference_data')
        ref_data = self.test_ref_data[0, :, :]
        ref_rolling_window = rolling_window(ref_data, stg.window_length, 0)
        output = stg.generate(hist_data=history_data_rolling_window,
                              ref_data=ref_rolling_window,
                              data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])
        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test strategy generate with trade_data
        print(f'\ntest strategy generate with trade_data')
        output = []
        trade_data = np.empty(shape=(3, 5))  # 生成的trade_data符合5行
        trade_data.fill(np.nan)
        recent_prices = np.zeros(shape=(3,))
        prev_signals = np.zeros(shape=(3,))
        for step in range(len(history_data_rolling_window)):
            output.append(
                    stg.generate(
                            hist_data=history_data_rolling_window,
                            trade_data=trade_data,
                            data_idx=step
                    )
            )
            current_prices = history_data_rolling_window[step, :, -1, 2]
            current_signals = output[-1]
            recent_prices = np.where(current_signals != prev_signals, current_prices, recent_prices)
            trade_data[:, 4] = recent_prices
            prev_signals = current_signals
        output = np.array(output, dtype='float')

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.33333, 0.33333, 0.33333],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0, 0.5],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0, 0.5],
                            [0.5, 0, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0, 0.5],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5]])
        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, atol=0.001, equal_nan=True))

    def test_general_strategy2(self):
        """ 测试第二种general strategy通用策略类型"""
        # test strategy with only historical data
        stg = TestSigStrategy()
        stg_pars = (0.2, 0.02, -0.02)
        stg.set_pars(stg_pars)
        history_data = self.hp1['close, open, high, low', :, 4:50]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)

        # test generate signal in real time mode:
        output = []
        for step in [0, 3, 5, 7, 10]:
            output.append(stg.generate(hist_data=history_data_rolling_window, data_idx=step))
        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0]])
        for signal, target in zip(output, sigmatrix):
            self.assertIsInstance(signal, np.ndarray)
            self.assertEqual(signal.shape, (3,))
            self.assertTrue(np.allclose(signal, target))

        # test generate signal in batch mode:
        output = stg.generate(hist_data=history_data_rolling_window,
                              data_idx=np.arange(len(history_data_rolling_window)))

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
                              [0.0, 0.0, 0.0],
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

        side_by_side_array = [[i, out_line, sig_line]
                                       for
                                       i, out_line, sig_line
                                       in zip(range(len(output)), output, sigmatrix)]
        # side_by_side_array = np.array(side_by_side_array)
        print(f'output and signal matrix lined up side by side is \n'
              f'{side_by_side_array}')
        self.assertEqual(sigmatrix.shape, output.shape)
        self.assertTrue(np.allclose(np.array(output), sigmatrix))

        # test strategy with also reference data
        print(f'\ntest strategy generate with reference_data')
        stg_pars = (0.3, 0.02, -0.02)
        stg.set_pars(stg_pars)
        history_data = self.hp1['close, open, high, low', :, 4:50]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)
        reference_data = self.test_ref_data2[0, 4:50, :]
        ref_rolling_windows = rolling_window(reference_data, stg.window_length, 0)

        # test generate signal in real time mode:
        output = []
        for step in [0, 3, 5, 7, 10]:
            output.append(stg.generate(
                    hist_data=history_data_rolling_window,
                    ref_data=ref_rolling_windows,
                    data_idx=step
            ))
        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [1.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 1.0, 0.0]])
        for signal, target in zip(output, sigmatrix):
            self.assertIsInstance(signal, np.ndarray)
            self.assertEqual(signal.shape, (3,))
            self.assertTrue(np.allclose(signal, target))

        # test generate signal in batch mode:
        output = stg.generate(
                hist_data=history_data_rolling_window,
                ref_data=ref_rolling_windows,
                data_idx=np.arange(len(history_data_rolling_window))
        )

        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [1.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [1.0, 0.0, 1.0],
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
                              [1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 1.0, 0.0]])

        side_by_side_array = [[i, out_line == sig_line, out_line, sig_line]
                                       for
                                       i, out_line, sig_line
                                       in zip(range(len(output)), output, sigmatrix)]
        # side_by_side_array = np.array(side_by_side_array)
        print(f'output and signal matrix lined up side by side is \n'
              f'{side_by_side_array}')
        self.assertEqual(sigmatrix.shape, output.shape)
        self.assertTrue(np.allclose(np.array(output), sigmatrix, equal_nan=True))

    def test_factor_sorter(self):
        """Test Factor Sorter 策略, test all built-in strategy parameters"""
        print(f'\ntest strategy generate with only history data')
        stg = SelectingAvgIndicator()
        self.assertIsInstance(stg, BaseStrategy)
        self.assertIsInstance(stg, FactorSorter)
        stg_pars = (False, 'even', 'greater', 0, 0, 0.67)
        stg.set_pars(stg_pars)
        stg.window_length = 5
        stg.data_freq = 'd'
        stg.strategy_run_freq = '10d'
        stg.sort_ascending = False
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.max_sel_count = 0.67
        # test additional FactorSorter properties
        self.assertEqual(stg_pars, (False, 'even', 'greater', 0, 0, 0.67))
        self.assertEqual(stg.window_length, 5)
        self.assertEqual(stg.data_freq, 'd')
        self.assertEqual(stg.strategy_run_freq, '10d')
        self.assertEqual(stg.sort_ascending, False)
        self.assertEqual(stg.condition, 'greater')
        self.assertEqual(stg.lbound, 0)
        self.assertEqual(stg.ubound, 0)
        self.assertEqual(stg.max_sel_count, 0.67)

        history_data = self.hp2.values[:, :-1]
        hist_data_rolling_window = rolling_window(history_data, window=stg.window_length, axis=1)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.0, 1.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        print(pd.DataFrame(output, index=self.hp1.hdates[5:], columns=self.hp1.shares))
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test single factor, get mininum factor
        stg_pars = (True, 'even', 'less', 1, 1, 0.67)
        stg.sort_ascending = True
        stg.condition = 'less'
        stg.lbound = 1
        stg.ubound = 1
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0.5, 0.5, 0.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.0, 1.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        print(pd.DataFrame(output, index=self.hp1.hdates[5:], columns=self.hp1.shares))
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test single factor, get max factor in linear weight
        stg_pars = (False, 'linear', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'linear'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0.0, 0.33333333, 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.66666667, 0.33333333],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.33333333, 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0., 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0., 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0.66666667, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test single factor, get max factor in linear weight
        stg_pars = (False, 'distance', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'distance'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0., 0.08333333, 0.91666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.91666667, 0.08333333],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.08333333, 0., 0.91666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.08333333, 0., 0.91666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.08333333, 0.91666667, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, 0.001, equal_nan=True))

        # test single factor, get max factor in proportion weight
        stg_pars = (False, 'proportion', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'proportion'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0., 0.4, 0.6],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.6, 0.4],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0., 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.25, 0., 0.75],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.375, 0.625, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, 0.001, equal_nan=True))

        # test single factor, get max factor in linear weight, threshold 0.2
        stg_pars = (False, 'even', 'greater', 0.2, 0.2, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'even'
        stg.condition = 'greater'
        stg.lbound = 0.2
        stg.ubound = 0.2
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, 0.001, equal_nan=True))

        print(f'\ntest financial generate with reference data')
        # to be added

    def test_stg_trading_different_prices(self):
        """测试一个以开盘价买入，以收盘价卖出的大小盘轮动交易策略"""
        # 测试大小盘轮动交易策略，比较两个指数的过去N日收盘价涨幅，选择较大的持有，以开盘价买入，以收盘价卖出
        print('\n测试大小盘轮动交易策略，比较两个指数的过去N日收盘价涨幅，选择较大的持有，以开盘价买入，以收盘价卖出')
        stg_buy = StgBuyOpen()
        stg_sel = StgSelClose()
        op = qt.Operator(strategies=[stg_buy, stg_sel], signal_type='ps')
        op.set_parameter(
                0,
                data_freq='d',
                strategy_run_freq='d',
                window_length=50,
                pars=(20,),
                strategy_data_types='close',  # 考察收盘价变化率
                strategy_run_timing='open',   # 以开盘价买进(这个策略只处理买入信号)
        )
        op.set_parameter(
                1,
                data_freq='d',
                strategy_run_freq='d',
                window_length=50,
                pars=(20,),
                strategy_data_types='close',  # 考察收盘价的变化率
                strategy_run_timing='close',  # 以收盘价卖出(这个策略只处理卖出信号)
        )
        op.set_blender(blender='s0')
        op.get_blender()
        qt.configure(asset_pool=['000300.SH',
                                 '399006.SZ'],
                     asset_type='IDX')
        res = qt.run(op,
                     mode=1,
                     visual=True,
                     trade_log=True,
                     invest_start='20110725',
                     invest_end='20220401',
                     trade_batch_size=1,
                     sell_batch_size=0)
        stock_pool = qt.filter_stock_codes(index='000300.SH', date='20211001')
        qt.configure(asset_pool=stock_pool,
                     asset_type='E',
                     benchmark_asset='000300.SH',
                     benchmark_asset_type='IDX',
                     opti_output_count=50,
                     invest_start='20211013',
                     invest_end='20211231',
                     opti_sample_count=100,
                     trade_batch_size=100.,
                     sell_batch_size=100.,
                     invest_cash_amounts=[1000000],
                     mode=1,
                     trade_log=True,
                     PT_buy_threshold=0.03,
                     PT_sell_threshold=0.03,
                     backtest_price_adj='none')

    def test_stg_index_follow(self):
        # 跟踪沪深300指数的价格，买入沪深300指数成分股并持有，计算收益率
        print('\n跟踪沪深300指数的价格，买入沪深300指数成分股并持有，计算收益率')
        op = qt.Operator(strategies=['finance'], signal_type='PS')
        op.set_parameter(0,
                         opt_tag=1,
                         strategy_run_freq='m',
                         strategy_data_types='wt_idx|000300.SH',
                         sort_ascending=False,
                         weighting='proportion',
                         max_sel_count=300)
        res = qt.run(op,
                     mode=1,
                     visual=True,
                     trade_log=True)

    def test_non_day_data_freqs(self):
        """测试除d之外的其他数据频率交易策略"""
        op_min = qt.Operator(strategies='DMA, MACD, ALL', signal_type='pt')
        op_min.set_parameter(0, data_freq='h', strategy_run_freq='h')
        op_min.set_parameter(1, data_freq='h', strategy_run_freq='d')
        op_min.set_parameter(2, data_freq='h', strategy_run_freq='y')
        op_min.set_blender(blender='(s0+s1)*s2')
        qt.configure(asset_pool=['000001.SZ', '000002.SZ', '000005.SZ', '000006.SZ', '000007.SZ',
                                 '000918.SZ', '000819.SZ', '000899.SZ'],
                     asset_type='E',
                     visual=True,
                     trade_log=False)
        res = qt.run(op_min,
                     mode=1,
                     visual=True,
                     trade_log=False,
                     invest_start='20160225',
                     invest_end='20161023',
                     trade_batch_size=100,
                     sell_batch_size=100)

    def test_long_short_position_limits(self):
        """ 测试多头和空头仓位的最高仓位限制 """
        # TODO: implement this test
        pass


if __name__ == '__main__':
    # get all stock prices from year 2020 to year 2022
    qt.refill_data_source(qt.QT_DATA_SOURCE, tables='stock_daily', start_date='20200101', end_date='20221231')

    # get index prices of 000300 and 399006 data from 2005 to year 2022
    qt.refill_data_source(qt.QT_DATA_SOURCE, tables='index_daily', start_date='20050101', end_date='20221231',
                          code_range='000300,399006')

    # get hourly price data for a few stocks in year 2016
    qt.refill_data_source(qt.QT_DATA_SOURCE, tables='stock_hourly', start_date='20160101', end_date='20161231',
                          code_range=['000001', '000002', '000005', '000006', '000007', '000918', '000819',
                                      '000899'])
    unittest.main()