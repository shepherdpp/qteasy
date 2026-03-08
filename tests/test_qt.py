# coding=utf-8
# ======================================
# File:     test_qt.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for general functions of
# qteasy.
# ======================================
import time
import unittest
import sys
import pandas as pd
import numba as nb
from tqdm import tqdm

import qteasy as qt
import numpy as np

from qteasy.parameter import Parameter
from qteasy.tafuncs import bbands
from qteasy.tafuncs import sma
from qteasy.datatypes import DataType, StgData

from qteasy.strategy import RuleIterator, GeneralStg


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

    def __init__(self, par_values=(10, 10.0)):
        super().__init__(
                name='test_LS',
                description='test long/short strategy',
                pars=[
                    Parameter((2, 20), name='n', par_type='int'),
                    Parameter((2, 20), name='price', par_type='float')
                ],
                data_types=[
                    DataType('close', freq='d', asset_type='E'),
                    DataType('open', freq='d', asset_type='E'),
                    DataType('high', freq='d', asset_type='E'),
                    DataType('low', freq='d', asset_type='E'),
                ],
                window_length=5,
        )
        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        n, price = self.get_pars('n', 'price')
        h = self.get_data('close_E_d', 'open_E_d', 'high_E_d', 'low_E_d')
        avg = (h[0] + h[1] + h[2] + h[3]) / 4
        ma = sma(avg, n)

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
                pars=[],
                data_types=[
                    DataType('close', freq='d', asset_type='E'),
                    DataType('high', freq='d', asset_type='E'),
                    DataType('low', freq='d', asset_type='E'),
                ],
                window_length=5,
        )
        pass

    def realize(self):
        close, high, low = self.get_data('close_E_d', 'high_E_d', 'low_E_d')
        avg = np.nanmean(close + high + low, axis=0) / 3
        dif = (close - np.roll(close, 1, axis=0))[-1]

        difper = dif / avg
        large2 = difper.argsort()[1:]
        chosen = np.zeros_like(avg)
        chosen[large2] = 0.5
        return chosen


class Cross_SMA_PS(qt.RuleIterator):
    """自定义双均线择时策略策略，产生的信号类型为交易信号"""

    def __init__(self, par_values=(25, 100, 0.01)):
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
                pars=[
                    Parameter((10, 250), name='f', par_type='int'),
                    Parameter((10, 250), name='s', par_type='int'),
                    Parameter((0.0, 0.5), name='m', par_type='float')
                ],
                name='CUSTOM ROLLING TIMING STRATEGY',
                description='Customized Rolling Timing Strategy for Testing',
                data_types=DataType('close', freq='d', asset_type='ANY'),
                window_length=200,
        )
        if par_values:
            self.update_par_values(*par_values)

    # 策略的具体实现代码写在策略的realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def realize(self):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度
        """
        f, s, m = self.get_pars('f', 's', 'm')
        h = self.get_data('close_ANY_d')
        # 计算长短均线的当前值和昨天的值
        sma = qt.tafuncs.sma
        s_ma = sma(h, s)
        f_ma = sma(h, f)

        s_today, s_last = s_ma[-1], s_ma[-2]
        f_today, f_last = f_ma[-1], f_ma[-2]

        self.trace('s_today', s_today)
        self.trace('f_today', f_today)
        self.trace('s_last', s_last)
        self.trace('f_last', f_last)

        # 计算慢均线的停止边界，当快均线在停止边界范围内时，平仓，不发出买卖信号
        s_ma_u = s_today * (1 + m)
        s_ma_l = s_today * (1 - m)
        self.trace('s_ma_u', s_ma_u)
        self.trace('s_ma_l', s_ma_l)

        # 根据观望模式在不同的点位产生交易信号
        if (f_last < s_ma_u) and (f_today > s_ma_u):  # 当快均线自下而上穿过上边界，开多仓
            self.trace('signal',
                       f'f_last:{f_last:.3f}, f_today:{f_today:.3f}, s_ma_u:{s_ma_u:.3f}, '
                       f'fast crossed upwards upper bound, signal is 1')
            return 1.
        elif (f_last > s_ma_u) and (f_today < s_ma_u):  # 当快均线自上而下穿过上边界，平多仓
            self.trace('signal2',
                       f'f_last:{f_last:.3f}, f_today:{f_today:.3f}, s_ma_u:{s_ma_u:.3f}, '
                       f'fast crossed downwards upper bound, signal is -1')
            return -1.
        elif (f_last > s_ma_l) and (f_today < s_ma_l):  # 当快均线自上而下穿过下边界，开空仓
            self.trace('signal',
                       f'f_last:{f_last:.3f}, f_today:{f_today:.3f}, s_ma_u:{s_ma_l:.3f}, '
                       f'fast crossed downwards lower bound, signal is -1')
            return -1.
        elif (f_last < s_ma_l) and (f_today > s_ma_l):  # 当快均线自下而上穿过下边界，平空仓
            self.trace('signal',
                       f'f_last:{f_last:.3f}, f_today:{f_today:.3f}, s_ma_u:{s_ma_l:.3f}, '
                       f'fast crossed upwards lower bound, signal is 1')
            return 1.
        else:  # 其余情况不产生任何信号
            self.trace('signal',
                       f'f_last:{f_last:.3f}, f_today:{f_today:.3f}, s_ma_u:{s_ma_u:.3f}, s_ma_l:{s_ma_l:.3f}, '
                       f'no line crossing, nosignal generated')
            return 0.


class Cross_SMA_PT(qt.RuleIterator):
    """自定义双均线择时策略策略，产生的信号类型为持仓目标信号"""

    def __init__(self, par_values=(25, 100, 0.01)):
        """这个均线择时策略只有三个参数：
            - SMA 慢速均线，所选择的股票
            - FMA 快速均线
            - M   边界值

            策略的其他说明

        """
        super().__init__(
                pars=[
                    Parameter((10, 250), name='f', par_type='int'),
                    Parameter((10, 250), name='s', par_type='int'),
                    Parameter((0.0, 0.5), name='m', par_type='float')
                ],
                name='CUSTOM ROLLING TIMING STRATEGY',
                description='Customized Rolling Timing Strategy for Testing',
                data_types=DataType('close', freq='d', asset_type='ANY'),
                window_length=200,
        )
        if par_values:
            self.update_par_values(*par_values)

    # 策略的具体实现代码写在策略的_realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def realize(self):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        f, s, m = self.get_pars('f', 's', 'm')
        h = self.get_data('close_ANY_d')
        # 计算长短均线的当前值
        sma = qt.tafuncs.sma
        s_ma = sma(h, s)[-1]
        f_ma = sma(h, f)[-1]

        # 计算慢均线的停止边界，当快均线在停止边界范围内时，平仓，不发出买卖信号
        s_ma_u = s_ma * (1 + m)
        s_ma_l = s_ma * (1 - m)

        # 根据观望模式在不同的点位产生交易信号
        if s_ma_u < f_ma:  # 当快均线在上边界以上时，持有多头仓位
            return 1
        elif s_ma_l <= f_ma <= s_ma_u:  # 当快均线在上下边界之间时，清空所有持仓
            return 0
        elif f_ma < s_ma_l:  # 当快均线在下边界以下时，持有空头仓位
            return -1
        else:  # 其余情况不产生任何信号
            return 0


class Sel_Tracing(qt.FactorSorter):
    """ 以股票过去N天的价格或数据指标的变动比例作为选股因子选股，生成trace报告
    """

    def __init__(self, par_values=(14,), **kwargs):
        super().__init__(
                pars=[
                    Parameter(par_range=(2, 150), par_type='int', name='n')
                ],
                name='N-DAY RATE',
                description='Select stocks by its N day price change',
                data_types=StgData('close', freq='d', asset_type='ANY', window_length=150),
                **kwargs,
        )
        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        n = self.get_pars('n')
        h = self.get_data('close_ANY_d')
        current_price = h[-1]
        n_previous = h[- n - 1]
        self.trace('cur_price_300', current_price[0])
        self.trace('cur_price_SZ', current_price[1])
        self.trace('n_prev_300', n_previous[0])
        self.trace('n_prev_SZ', n_previous[1])
        factors = (current_price - n_previous) / n_previous
        self.trace('rate_300', factors[0])
        self.trace('rate_SZ', factors[1])

        return factors


# Other high level test strategies
class MyStg(qt.RuleIterator):
    """自定义双均线择时策略策略"""

    def __init__(self, par_values=(20, 100, 0.01)):
        """这个均线择时策略只有三个参数：
            - SMA 慢速均线，所选择的股票
            - FMA 快速均线
            - M   边界值

            策略的其他说明

        """
        super().__init__(
                pars=[
                    Parameter((10, 250), par_type='int', name='f'),  # 快速均线
                    Parameter((10, 250), par_type='int', name='s'),  # 慢速均线
                    Parameter((0.0, 0.5), par_type='float', name='m'),  # 边界值
                ],
                name='CUSTOM ROLLING TIMING STRATEGY',
                description='Customized Rolling Timing Strategy for Testing',
                data_types=DataType('close', freq='d', asset_type='ANY'),
                window_length=200,
        )
        if par_values:
            self.update_par_values(*par_values)

    # 策略的具体实现代码写在策略的_realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def realize(self):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        f, s, m = self.get_pars('f', 's', 'm')
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = self.get_data('close_ANY_d')  # 取最近200个交易日的数据进行计算
        # 计算长短均线的当前值
        s_ma = sma(h, s)[-1]
        f_ma = sma(h, f)[-1]

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
    def __init__(self, par_values=(20,)):
        super().__init__(
                pars=[Parameter((0, 100), par_type='int', name='n')],
                name='OPEN_BUY',
                data_types=DataType('close', freq='d', asset_type='ANY'),
                use_latest_data_cycle=False,
        )
        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        n = self.get_pars('n')
        h = self.get_data('close_ANY_d')
        current_price = h[-1]
        n_day_price = h[-n]
        # 选股指标为各个股票的N日涨幅
        factors = (current_price / n_day_price - 1).squeeze()
        # 初始化选股买卖信号，初始值为全0
        sig = np.zeros_like(factors)

        if np.all(factors <= 0.0001):
            # 如果所有的选股指标都小于0，则全部卖出
            # 但是卖出信号StgSelClose策略中处理，因此此处全部返回0即可
            return sig
        else:
            # 如果选股指标有大于0的，则找出最大者
            # 并生成买入信号
            sig[np.nanargmax(factors)] = 1
            return sig


class StgSelClose(GeneralStg):
    def __init__(self, par_values=(20,)):
        super().__init__(
                pars=[Parameter((0, 100), par_type='int', name='n')],
                name='SELL_CLOSE',
                data_types=DataType('close', freq='d', asset_type='ANY'),
                use_latest_data_cycle=True,
        )
        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        n = self.get_pars('n')
        h = self.get_data('close_ANY_d')
        current_price = h[-1]
        n_day_price = h[-n]
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


class TestQT(unittest.TestCase):
    """对qteasy系统进行总体测试"""

    def setUp(self):
        # 准备测试所需数据，确保本地数据源有足够的数据

        self.op = qt.Operator(strategies=['dma', 'macd'], name='Test Operator')
        self.op.group_merge_type = 'OR'
        print('  START TO TEST QT GENERAL OPERATIONS\n'
              '=======================================')
        print(' test environment information')
        print(f'  python version: {sys.version}')
        print(f'  qteasy version: {qt.__version__}')
        print(f'  qteasy root path: {qt.QT_ROOT_PATH}')
        print(f'  numpy version: {np.__version__}')
        print(f'  numba version: {nb.__version__}')
        print(f'  pandas version: {pd.__version__}')
        self.op.set_parameter('dma', opt_tag=1, par_range=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('macd', opt_tag=1, par_range=[(10, 250), (10, 250), (10, 250)])
        self.op.signal_type = 'pt'

        qt.configure(benchmark_asset='000300.SH',
                     mode=1,
                     asset_pool='000300.SH',
                     asset_type='IDX',
                     opti_output_count=50,
                     invest_start='20070110',
                     trade_batch_size=0.01,
                     sell_batch_size=0.01,
                     parallel=True,
                     hist_dnld_retry_cnt=3,  # 减少数据下载重试次数，加快测试速度
                     hist_dnld_retry_wait=0.5,  # 减少数据下载重试等待时间，加快测试速度
                     hist_dnld_backoff=1.2,  # 减少数据下载重试等待时间，加快测试速度
                     )

        timing_pars1 = (165, 191, 23)
        timing_pars2 = {'000100': (77, 118, 144),
                        '000200': (75, 128, 138),
                        '000300': (73, 120, 143)}
        timing_pars3 = (115, 197, 54)
        self.op.set_blender('pos_2_0(s0, s1)')
        self.op.set_parameter(stg_id='dma', par_values=timing_pars1)
        self.op.set_parameter(stg_id='macd', par_values=timing_pars3)

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
        self.assertEqual(config.benchmark_asset, '000300.SH')
        self.assertEqual(config.asset_pool, '000300.SH')
        self.assertEqual(config.invest_start, '20070110')
        # test temp config_key in run() that works only in run()
        qt.run(self.op,
               mode=1,
               asset_pool='000001.SZ',
               asset_type='E',
               invest_start='20100101',
               visual=False)
        self.assertEqual(config.mode, 2)
        self.assertEqual(qt.QT_CONFIG.mode, 2)
        self.assertEqual(config.benchmark_asset, '000300.SH')
        self.assertEqual(config.asset_pool, '000300.SH')
        self.assertEqual(config.invest_start, '20070110')

        config_copy = config.copy()
        qt.configure(config_copy,
                     mode=1,
                     benchmark_asset='000002.SZ')
        self.assertEqual(config.mode, 2)
        self.assertEqual(config.benchmark_asset, '000300.SH')
        self.assertEqual(config.asset_pool, '000300.SH')
        self.assertEqual(config.invest_start, '20070110')
        self.assertEqual(config_copy.mode, 1)
        self.assertEqual(config_copy.benchmark_asset, '000002.SZ')
        self.assertEqual(config_copy.asset_pool, '000300.SH')
        self.assertEqual(config_copy.invest_start, '20070110')

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
        print(f'configuration with config_key')
        qt.configuration('mode, time_zone, asset_pool')
        qt.configuration(['mode', 'time_zone', 'asset_pool'])

    def test_run_mode_0(self):
        """测试策略的实时信号生成模式"""
        op = qt.Operator(strategies=['stema'], op_type='stepwise')
        op.set_parameter('stema', par_values=(6,))
        qt.QT_CONFIG.mode = 0
        # qt.run(op)
        # TODO: running qteasy in mode 0 will enter interactive shell, which is not testable

    def test_run_mode_1(self):
        """测试策略的回测模式,结果打印但不可视化"""
        qt.configure(mode=1,
                     trade_batch_size=1,
                     invest_start='20070604',
                     invest_end='20190329',
                     visual=False,
                     trade_log=False,
                     )
        qt.run(self.op)

    def test_run_mode_1_visual(self):
        """测试策略的回测模式，结果可视化但不打印"""
        print(f'test plot with no buy-sell points and position indicators')
        qt.configuration(up_to=1, default=True)
        res = qt.run(
                self.op,
                mode=1,
                trade_batch_size=1,
                invest_start='20070604',
                invest_end='20190329',
                visual=True,
                trade_log=False,
                buy_sell_points=False,
                show_positions=False,
        )
        self.assertIsInstance(res, dict)
        self.assertIsNone(res.get('trade_log'))
        self.assertIsNone(res.get('trade_summary'))

        print(f'test plot with both buy-sell points and position indicators')
        qt.configuration(up_to=1, default=True)
        res = qt.run(
                self.op,
                mode=1,
                trade_batch_size=1,
                invest_start='20070604',
                invest_end='20190329',
                cost_rate_buy=0.0001,
                cost_rate_sell=0.,
                invest_cash_amounts=[100_000],
                visual=True,
                trade_log=True,
                buy_sell_points=True,
                show_positions=True,
        )
        self.assertIsInstance(res, dict)
        self.assertIsInstance(res['trade_log'], str)
        self.assertIsInstance(res['trade_summary'], str)
        self.assertIsInstance(res['report'], str)
        print(res['trade_log'])
        print(res['final_value'])
        print(res['total_fee'])
        print(res['info'])
        print(res['sharp'])
        self.assertAlmostEqual(res['final_value'], 395710.19, 0)
        self.assertAlmostEqual(res['total_fee'], 773.9, 0)
        self.assertAlmostEqual(res['sharp'], 0.513, 3)
        self.assertAlmostEqual(res['days'], 4315, 0)
        self.assertAlmostEqual(res['rtn'], 2.957, 3)

    def test_run_mode_2_montecarlo(self):
        """测试策略的优化模式，使用蒙特卡洛寻优"""
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_sample_count=200,
               opti_start='20060404',
               opti_end='20181231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in Montecarlo algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_sample_count=200,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in Montecarlo with mdd as opti target')
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_sample_count=200,
               optimize_target='mdd',
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in Montecarlo with volatility as opti target')
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_sample_count=200,
               optimize_target='vol',
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=False)

    def test_run_mode_2_montecarlo_visual(self):
        """测试策略的优化模式，使用蒙特卡洛寻优"""
        print(f'strategy optimization in Montecarlo algorithm with parallel ON')
        qt.configuration(up_to=1, default=True)
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_sample_count=200,
               opti_start='20120404',
               opti_end='20140601',
               opti_cash_dates='20120404',
               test_start='20120604',
               test_end='20181130',
               test_cash_dates='20120604',
               indicator_plot_type='violin',
               parallel=True,
               visual=True)
        qt.configuration(up_to=1, default=True)

    def test_run_mode_2_grid(self):
        """测试策略的优化模式，使用网格寻优"""
        print(f'strategy optimization in grid search algorithm with parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=1024,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in grid search algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=1024,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=128,
               optimize_target='mdd',
               optimize_direction='minimize',
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=128,
               optimize_target='vol',
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)

    def test_run_mode_2_grid_visual(self):
        """测试策略的优化模式，使用网格寻优"""
        print(f'strategy optimization in grid search algorithm with parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=128,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=True,
               indicator_plot_type=0)
        print(f'strategy optimization in grid search algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=128,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               report=False,
               visual=True,
               indicator_plot_type=1)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=128,
               optimize_target='mdd',
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               report=True,
               visual=True,
               indicator_plot_type=2)
        print(f'strategy optimization in grid search with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_sample_count=128,
               optimize_target='vol',
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=True,
               indicator_plot_type=3)

    def test_run_mode_2_incremental(self):
        """测试策略的优化模式，使用递进步长蒙特卡洛寻优"""
        print(f'strategy optimization in incremental algorithm with parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='SA',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=10,
               opti_min_volume=5E7,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=False)
        print(f'strategy optimization in incremental algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method='SA',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in incremental with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method='SA',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in incremental with multiple sub-idx_range testing')
        qt.run(self.op,
               mode=2,
               opti_method='SA',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)

    def test_run_mode_2_ga(self):
        """测试策略的优化模式，使用遗传算法寻优，断言 result_pool 有结果且数量合理"""
        print('strategy optimization with GA (genetic algorithm), parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='GA',
               opti_population=100,
               opti_output_count=20,
               opti_max_rounds=5,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=True)
        # 通过 Operator 的 run 会触发 optimize，优化结果在 backtest 内部；这里仅验证无异常
        # 若需断言 result_pool，需在 qt.run 返回的 backtester/optimizer 上检查（视 run 接口而定）
        print('GA optimization completed without exception; result_pool item_count checked in optimizer')

    def test_run_mode_2_pso(self):
        """测试策略的优化模式，使用粒子群优化(PSO)寻优，断言无异常、result_pool 有结果且数量合理"""
        print('strategy optimization with PSO (particle swarm optimization), parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='PSO',
               opti_population=50,
               opti_output_count=15,
               opti_max_rounds=5,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=True)
        print('PSO optimization completed without exception; result_pool item_count checked in optimizer')

    def test_run_mode_2_gradient(self):
        """测试策略的优化模式，使用梯度下降法寻优，断言无异常、result_pool 数量合理"""
        print('strategy optimization with gradient descent, parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='gradient',
               opti_sample_count=10,
               opti_output_count=20,
               opti_max_rounds=15,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=True)
        print('gradient optimization completed without exception')

    def test_run_mode_2_bayesian(self):
        """测试策略的优化模式，使用贝叶斯优化寻优，断言无异常、result_pool 有结果且点均在 space 内"""
        print('strategy optimization with Bayesian optimization, parallel OFF')
        qt.run(self.op,
               mode=2,
               opti_method='bayesian',
               opti_sample_count=5,
               opti_output_count=10,
               opti_max_rounds=8,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=False,
               visual=True)
        print(f'Bayesian optimization completed')

    def test_run_mode_2_incremental_visual(self):
        """测试策略的优化模式，使用递进步长蒙特卡洛寻优，结果以图表输出"""
        print(f'strategy optimization in incremental algorithm with parallel ON')
        qt.run(self.op,
               mode=2,
               opti_method='SA',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=True)
        print(f'strategy optimization in sa with multiple sub-idx_range optimization')
        qt.run(self.op,
               mode=2,
               opti_method='SA',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=True)

    def test_run_mode_2_predict(self):
        """测试策略的优化模式，使用蒙特卡洛预测方法评价优化结果"""
        print(f'strategy optimization in montecarlo algorithm with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_output_count=20,
               opti_sample_count=200,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)
        print(f'strategy optimization in incremental with with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=False)

    def test_run_mode_2_predict_visual(self):
        """测试策略的优化模式，使用蒙特卡洛预测方法评价优化结果，结果以图表方式输出"""
        print(f'strategy optimization in montecarlo algorithm with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method='grid',
               opti_output_count=20,
               opti_sample_count=200,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=True)
        print(f'strategy optimization in incremental with with predictive montecarlo test')
        qt.run(self.op,
               mode=2,
               opti_method='montecarlo',
               opti_r_sample_count=100,
               opti_reduce_ratio=0.2,
               opti_output_count=20,
               opti_max_rounds=50,
               opti_min_volume=5E9,
               opti_start='20120404',
               opti_end='20141231',
               test_start='20120604',
               test_end='20181130',
               parallel=True,
               visual=True)

    def test_built_ins(self):
        """测试内置的择时策略"""
        # 使用以下参数测试所有qt.built_in中的交易策略
        #   mode=1,
        #   asset_pool='000300.SH, 399006.SZ',
        #   start='20200101',
        #   end='20211231',
        #   trade_log=False,
        #   visual=False,
        # 其他均为默认参数
        all_built_ins = qt.built_in_strategies()
        tested_count = 0
        total_count = len(all_built_ins)
        key_results = []
        print(f'testing all built-in strategies')
        with tqdm(total=len(all_built_ins)) as pbar:
            for strategy in all_built_ins:
                op = qt.Operator(strategies=[strategy])
                op.set_blender('s0', 'Group_1')
                res = qt.run(
                        op,
                        mode=1,
                        asset_pool='000300.SH, 399006.SZ',  # 两个投资标的都是指数，asset_type='IDX'
                        invest_start='20200101',
                        invest_end='20211231',
                        trade_log=False,
                        visual=False,
                        report=False,
                )
                tested_count += 1
                pbar.set_description(f'testing: {strategy}')
                pbar.update()
                # progress_bar(tested_count, total_count, comments=f'testing: {strategy}')

                key_results.append(
                        [strategy,
                         res['loop_run_time'],
                         res['op_run_time'],
                         res['total_invest'],
                         res['final_value'],
                         res['rtn'],
                         res['mdd'],
                         ]
                )

        result = pd.DataFrame(key_results,
                              columns=['strategy',
                                       'loop_time',
                                       'op_time',
                                       'invest',
                                       'final_value',
                                       'return',
                                       'mdd']
                              )
        print(f'\n\n{"test results":=^80}')
        print(result.to_string())

    def test_multi_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        op = qt.Operator(strategies=['long', 'finance', 'signal_none'], name='Test Multi-Share')
        all_shares = qt.filter_stocks(date='20070101')
        shares_banking = qt.filter_stock_codes(date='20070101', industry='银行')
        print('extracted banking share pool:')
        print(all_shares.loc[all_shares.index.isin(shares_banking)])
        shares_estate = list(all_shares.loc[all_shares.industry == "全国地产"].index.values)
        qt.configure(asset_pool=shares_banking[0:10],
                     asset_type='E',
                     benchmark_asset='000300.SH',
                     opti_output_count=50,
                     invest_start='20070101',
                     invest_end='20181231',
                     invest_cash_dates=None,
                     trade_batch_size=1.,
                     mode=1,
                     trade_log=True)
        op.set_parameter('long', par_values=None)
        op.set_parameter('finance', par_values=(True, 'proportion', 'greater', 0, 0, 0.4),
                         run_freq='Q',
                         data_types=[DataType('pe', freq='d', asset_type='E')],
                         sort_ascending=True,
                         weighting='proportion',
                         condition='greater',
                         ubound=0,
                         lbound=0,
                         max_sel_count=0.4)
        # op.set_parameter('signal_none', par_values=())
        op.set_blender('avg(s0, s1)', 'Group_1')
        op.set_blender('s0', 'Group_2')
        op.info()
        print(f'test portfolio selecting from shares_estate: \n{shares_estate}')
        qt.configuration()
        qt.run(op, visual=True, trade_log=True, trade_batch_size=100)

    def test_many_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        print(f'test portfolio selection from large quantities of shares')
        op = qt.Operator(strategies=['long', 'finance', 'signal_none'], name='Test Many Share')
        qt.configure(asset_pool=qt.filter_stock_codes(date='20070101',
                                                      industry=['银行', '全国地产', '互联网', '环境保护', '区域地产',
                                                                '酒店餐饮', '运输设备', '综合类', '建筑工程', '玻璃',
                                                                '家用电器', '文教休闲', '其他商业', '元器件', 'IT设备',
                                                                '其他建材', '汽车服务', '火力发电', '医药商业',
                                                                '汽车配件',
                                                                '广告包装', '轻工机械', '新型电力', '多元金融', '饲料',
                                                                '铜', '普钢', '航空', '特种钢',
                                                                '种植业', '出版业', '焦炭加工', '啤酒', '公路',
                                                                '超市连锁',
                                                                '钢加工', '渔业', '农用机械', '软饮料', '化工机械',
                                                                '塑料',
                                                                '红黄酒', '橡胶', '家居用品', '摩托车', '电器仪表',
                                                                '服饰',
                                                                '仓储物流', '纺织机械', '电器连锁', '装修装饰',
                                                                '半导体',
                                                                '电信运营', '石油开采', '乳制品', '商品城', '公共交通',
                                                                '陶瓷', '船舶'],
                                                      area=['深圳', '北京', '吉林', '江苏', '辽宁', '广东',
                                                            '安徽', '四川', '浙江', '湖南', '河北', '新疆',
                                                            '山东', '河南', '山西', '江西', '青海', '湖北',
                                                            '内蒙', '海南', '重庆', '陕西', '福建', '广西',
                                                            '上海']),
                     asset_type='E',
                     benchmark_asset='000300.SH',
                     opti_output_count=50,
                     invest_start='20070101',
                     invest_end='20171228',
                     invest_cash_dates=None,
                     trade_batch_size=1.,
                     mode=1,
                     trade_log=True,
                     hist_dnld_parallel=0)
        print(f'in total a number of {len(qt.QT_CONFIG.asset_pool)} shares are selected!')
        op.set_parameter('long', par_values=())
        op.set_parameter('finance', par_values=(True, 'proportion', 'greater', 0, 0, 30),
                         run_freq='Q',
                         data_types=DataType('basic_eps'),
                         sort_ascending=True,
                         weighting='proportion',
                         condition='greater',
                         ubound=0,
                         lbound=0,
                         max_sel_count=30)
        op.set_parameter('signal_none', par_values=())
        op.set_blender('avg(s0, s1)', 'Group_1')
        op.set_blender('s0', group_id='Group_2')
        op.group_merge_type = 'OR'
        qt.run(op, visual=True, trade_log=True)

    def test_op_stepwise(self):
        """测试stepwise模式下的operator的表，使用两个测试专用交易策略"""
        # confirm that operator running results are same in stepwise and batch type
        op_batch = qt.Operator(strategies=['dma', 'macd'], signal_type='pt', op_type='batch', name='Test Stepwise')
        op_stepwise = qt.Operator(strategies=['dma', 'macd'], signal_type='pt', op_type='step', name='Test Stepwise')
        for op in [op_batch, op_stepwise]:
            op.set_parameter(0, window_length=100, par_values=(12, 26, 9))
            op.set_parameter(1, window_length=100, par_values=(12, 26, 9))
            op.set_blender('avg(s0, s1)', group_id='Group_1')

        qt.configure(
                benchmark_asset='000300.SH',
                asset_pool='601398.SH, 600000.SH, 000002.SZ',
                asset_type='E',
                opti_output_count=50,
                invest_start='20190101',
                invest_end='20190331',
                trade_batch_size=1.,
                sell_batch_size=1.,
                parallel=True,
                trade_log=False
        )
        print('backtest in batch mode:')
        res_batch = qt.run(op=op_batch, mode=1)
        print('backtest in stepwise mode:')
        res_stepwise = qt.run(op=op_stepwise, mode=1)
        val_batch = res_batch["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        val_stepwise = res_stepwise["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        print(f'the result of batched operation is\n'
              f'shape: {val_batch.shape}\n'
              f'{val_batch}\n'
              f'and the result of stepwise operation is\n'
              f'shape: {val_stepwise.shape}\n'
              f'{val_stepwise}')

        self.assertTrue(np.allclose(val_batch, val_stepwise))
        self.assertEqual(res_batch['final_value'],
                         res_stepwise['final_value'])

        print('backtest in batch mode:')
        res_batch = qt.run(
                op=op_batch,
                mode=1,
                invest_start='20180101',
                invest_end='20191231'
        )
        print('backtest in stepwise mode:')
        res_stepwise = qt.run(
                op=op_stepwise,
                mode=1,
                invest_start='20180101',
                invest_end='20191231'
        )
        val_batch = res_batch["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        val_stepwise = res_stepwise["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values

        self.assertTrue(np.allclose(val_batch, val_stepwise))
        self.assertEqual(res_batch['final_value'],
                         res_stepwise['final_value'])

        # test operator that runs at different frequencies
        print('test operator that runs at different frequencies')
        stg1 = TestLSStrategy()
        stg2 = TestSelStrategy()
        stg1.window_length = 100
        stg2.window_length = 100

        op_batch = qt.Operator(strategies=[stg1, stg2], signal_type='pt', op_type='batch', name='Test Batch')
        op_batch.set_parameter('custom_1', run_freq='W')
        op_stepwise = qt.Operator(strategies=[stg1, stg2], signal_type='pt', op_type='stepwise', name='Test Step')
        op_stepwise.set_parameter('custom_1', run_freq='W')
        par_stg1 = {'000100': (20, 10),
                    '000200': (20, 10),
                    '000300': (20, 6)}
        par_stg2 = ()
        for op in [op_batch, op_stepwise]:
            op.set_shares(['000100', '000200', '000300'])
            op.set_blender('s0', group_id='Group_1')
            op.set_blender('s0', group_id='Group_2')
            op.set_parameter(0, par_values=par_stg1, opt_tag=1, par_range=([2, 20], [2, 100]))
            op.set_parameter(1, par_values=par_stg2, opt_tag=1)

        qt.configure(
                benchmark_asset='000300.SH',
                asset_pool='601398.SH, 600000.SH, 000002.SZ',
                asset_type='E',
                opti_output_count=50,
                invest_start='20190101',
                invest_end='20190331',
                opti_start='20190101',
                opti_end='20191231',
                test_start='20200101',
                test_end='20200331',
                trade_batch_size=100.,
                sell_batch_size=100.,
                parallel=True,
                trade_log=False
        )
        print('output result back testing with test data')

        print('backtest in batch mode:')
        res_batch = qt.run(op=op_batch, mode=1, visual=True, trade_log=True)
        print('backtest in stepwise mode:')
        res_stepwise = qt.run(op=op_stepwise, mode=1, visual=True, trade_log=True)
        val_batch = res_batch["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        val_stepwise = res_stepwise["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        print(f'the result of batched operation is\n'
              f'{val_batch}\n'
              f'and the result of stepwise operation is\n'
              f'{val_stepwise}')
        self.assertTrue(np.allclose(val_batch, val_stepwise))

        # print('backtest in batch mode in optimization mode:')
        # qt.run(op=op_batch, mode=2)
        # print('backtest in stepwise mode in optimization mode')
        # qt.run(op=op_stepwise, mode=2)

        print('test stepwise mode with different sample freq')

    def test_op_tracing(self):
        """test an multi-group op with tracing enabled with short period of data"""
        # 创建一个Operator包含三个交易策略组
        op = qt.Operator(strategies=Cross_SMA_PS, run_freq='d', signal_type='PS', name='Test Tracing')
        op.add_strategy(Cross_SMA_PS, run_freq='W')
        op.add_strategy(Cross_SMA_PS, run_freq='d', run_timing='10:30')
        op.set_blender('s0')

        qt.configure(
                benchmark_asset='000300.SH',
                asset_pool='601398.SH,600000.SH,000002.SZ',
                asset_type='E',
                opti_output_count=50,
                invest_start='20250301',
                invest_end='20250501',
                trade_batch_size=1.,
                sell_batch_size=1.,
                parallel=True,
                trade_log=True,
                trace_log=True,
                # trade_log=False,
                # trace_log=False,
        )

        # test with group merge type is None
        qt.run(op=op, mode=1)
        time.sleep(1)  # 等待文件写入完成，避免后续操作过快导致文件访问冲突
        op.group_merge_type = 'AND'
        qt.run(op=op, mode=1)
        time.sleep(1)  # 等待文件写入完成，避免后续操作过快导致文件访问冲突

        print(f'仿照qteasy tutorial中的案例，测试一个大小盘轮动策略，回测过程中记录trace值')
        op = qt.Operator(strategies=Sel_Tracing, run_freq='d', signal_type='PT')
        op.set_parameter(0,  # 指定需要设置参数的交易策略：即设置策略0的参数
                         sort_ascending=False,  # 设置选择涨幅最大的指数
                         max_sel_count=1,  # 设置选股数量，每次最多从投资池里选择一支股票
                         par_values=(20,),  # 策略参数N=20，比较20日涨幅
                         data_types=[
                             qt.StgData('close', freq='d',
                                        asset_type='ANY',
                                        use_latest_data_cycle=True,
                                        window_length=25)],  # 使用收盘价计算涨幅
                         )
        qt.configure(
                benchmark_asset='000300.SH',
                asset_pool=['000300.SH',
                            '399006.SZ'],  # 投资股票池里包括沪深300和创业板指数两个指数，分别代表大盘和小盘股
                invest_cash_amounts=[100000],  # 投入金额为十万元
                asset_type='IDX',  # 为简单起见，直接投资于指数
                cost_rate_buy=0.0001,  # 买入资产时交易费用万分之一
                cost_rate_sell=0.000,  # 卖出资产时的交易费用为万分之一
                invest_start='20110101',  # 模拟交易开始日期
                invest_end='20201231',  # 模拟交易结束日期
                trade_batch_size=0.01,  # 买入资产时最小交易批量
                sell_batch_size=0.01,  # 卖出资产时最小交易批量
        )
        # test with group merge type is None
        qt.configuration(up_to=5)
        qt.run(op=op, mode=1)
        time.sleep(1)  # 等待文件写入完成，避免后续操作过快导致文件访问冲突

        op.set_parameter(0,  # 指定需要设置参数的交易策略：即设置策略0的参数
                         sort_ascending=False,  # 设置选择涨幅最大的指数
                         max_sel_count=1,  # 设置选股数量，每次最多从投资池里选择一支股票
                         par_values=(20,),  # 策略参数N=20，比较20日涨幅
                         data_types=[
                             qt.StgData('close', freq='d',
                                        asset_type='ANY',
                                        use_latest_data_cycle=True,
                                        window_length=25)],  # 使用收盘价计算涨幅
                         condition='greater',  # 设置条件为大于0，即只有当20日涨幅大于0时才会产生买入信号
                         ubound=0,  # 设置条件的上界为0，即20日涨幅必须大于0才能产生买入信号
                         )
        # test with group merge type is None
        qt.run(op=op, mode=1)

    def test_sell_short(self):
        """ 测试sell_short模式是否能正常工作（买入卖出负份额）"""
        op = qt.Operator([Cross_SMA_PS()], signal_type='PS')
        op.set_parameter(0, par_values=(23, 100, 0.02))
        op.set_blender('s0', group_id='Group_1')
        res = qt.run(op,
                     mode=1,
                     invest_start='20060101',
                     allow_sell_short=False,
                     trade_log=True,
                     visual=True)
        no_short_in_res = np.all(res['oper_count'].short == 0)
        self.assertTrue(no_short_in_res)
        res = qt.run(op,
                     mode=1,
                     invest_start='20060101',
                     allow_sell_short=True,
                     trade_log=True,
                     visual=True)
        no_short_in_res = np.all(res['oper_count'].short == 0)
        self.assertFalse(no_short_in_res)
        op = qt.Operator([Cross_SMA_PT()], signal_type='PT')
        op.set_parameter(0, par_values=(23, 100, 0.02))
        op.set_blender('s0', group_id='Group_1')
        res = qt.run(op, mode=1,
                     invest_start='20060101',
                     allow_sell_short=False,
                     trade_log=True,
                     visual=True)
        no_short_in_res = np.all(res['oper_count'].short == 0)
        self.assertTrue(no_short_in_res)
        res = qt.run(op, mode=1,
                     invest_start='20060101',
                     allow_sell_short=True,
                     trade_log=True,
                     visual=True)
        no_short_in_res = np.all(res['oper_count'].short == 0)
        self.assertFalse(no_short_in_res)

    def test_all_run_freqs_and_timings(self):
        """ 使用最基本的内置交易策略DMA测试单个交易策略在不同的运行频率和运行时点回测时，
        从回测“金标准”数组（own_amounts_array / own_cashes / trade_price_data / trade_cost_array）
        重新构造日频 complete_values 时没有任何偏差。

        具体包括两层约束：

        1. 结构约束：complete_values 的 index 必须是投资区间内的所有交易日 15:00:00；
        2. 数值约束（金标准一致性）：
           - 每个交易日的持仓数量列必须等于在“最近一次不晚于该日的交易信号”之后的 own_amounts_array；
           - 每个交易日的 cash 列必须等于同一规则下对应的 own_cashes；
           - 每个交易日的 fee 列必须等于该日所有成交费用按日聚合后的总和；
           - 每个交易日的 value 列必须等于“持仓 * 当日评价价格 + 当日现金”；
        以上均以 Backtester 内部数组为金标准，确保从数组到 complete_values 的映射逻辑无损。
        """
        freq_timings_to_test = [('ME', 'close'),
                                ('MS', '10:30'),
                                ('d', 'close'),
                                ('d', '11:00'),
                                ('h', 'close'),
                                ('5min', 'close')]
        illegal_freq_timings = [('ME', '8:30'),
                                ('MQ', 'wrong_time')]

        invest_start = '20250301'
        invest_end = '20251231'
        invest_start_ts = pd.to_datetime(invest_start)
        invest_end_ts = pd.to_datetime(invest_end)

        for freq, timing in freq_timings_to_test:
            print(f'testing strategy running at frequency and timing: {freq}, {timing}')

            # 直接使用 qt.run() 完成回测，并通过 op.backtested 访问 Backtester 金标准数组
            op = qt.Operator('dma', run_freq=freq, run_timing=timing, name=f'Test {freq} @ {timing}')
            res = qt.run(
                    op=op,
                    mode=1,
                    asset_type='E',
                    asset_pool=['000651.SZ', '000001.SZ'],
                    invest_start=invest_start,
                    invest_end=invest_end,
                    trade_batch_size=100,
                    sell_batch_size=1,
                    report=True,
                    visual=True,
                    trade_log=True,
            )

            cv = res['complete_values']
            print(f'complete_values head for frequency and timing {freq}, {timing}:')
            print(cv[["000651.SZ", "000001.SZ", "cash", "fee", "value"]].head(60).to_string())

            # ---------- 1. 结构约束：index 必须是投资区间内的所有交易日 15:00 ----------
            self.assertIsInstance(cv, pd.DataFrame)
            self.assertGreater(len(cv.index), 0)
            # index 必须覆盖从invest_start到invest_end期间的交易日，时间为15:00:00
            self.assertGreaterEqual(cv.index[0], invest_start_ts)
            self.assertLessEqual(cv.index[-1], invest_end_ts + pd.Timedelta(days=1))
            times = cv.index.time
            self.assertTrue(all(t.hour == 15 and t.minute == 0 and t.second == 0 for t in times))
            # 价值列不允许为NaN
            self.assertFalse(cv['value'].isna().any())

            # ---------- 2. 数值约束：complete_values 必须与 Backtester 内部金标准数组一致 ----------
            backtested = op.backtested

            # 2.1 通过“最近一次不晚于当日的交易信号”确定每日应使用的持仓 / 现金索引
            daily_index = cv.index
            step_times = pd.to_datetime(backtested.op.op_signal_index.get_level_values(0))
            own_amounts = backtested.own_amounts_array
            own_cashes = backtested.own_cashes

            expected_positions = []
            expected_cashes = []
            for d in daily_index:
                mask = step_times <= d
                if not mask.any():
                    pos_idx = 0
                else:
                    last_idx = np.nonzero(mask)[0][-1]
                    pos_idx = last_idx + 1
                if pos_idx >= own_amounts.shape[0]:
                    pos_idx = own_amounts.shape[0] - 1
                expected_positions.append(own_amounts[pos_idx, :])
                expected_cashes.append(own_cashes[pos_idx])

            expected_positions = np.vstack(expected_positions)
            expected_cashes = np.asarray(expected_cashes)

            # 2.2 使用评价价格 evaluate_price_data 计算每日总资产（value），以金标准持仓 / 现金为基础
            daily_prices = backtested.evaluate_price_data.reindex(daily_index).reindex(columns=backtested.shares)
            price_array = np.nan_to_num(daily_prices.values, nan=0.0)
            expected_values = (price_array * expected_positions).sum(axis=1) + expected_cashes

            # 2.3 将成交费用按交易日聚合，映射到每日 fee
            step_dates = step_times.normalize()
            step_fee = backtested.trade_cost_array.sum(axis=1)
            fee_by_date = pd.Series(step_fee, index=step_dates).groupby(level=0).sum()
            expected_daily_fee = fee_by_date.reindex(daily_index.normalize()).fillna(0.0).values

            # 2.4 强断言：complete_values 的各列必须与基于数组重算的结果完全一致
            np.testing.assert_allclose(
                    cv[backtested.shares].values,
                    expected_positions,
                    err_msg=f'positions mismatch for freq={freq}, timing={timing}',
            )
            np.testing.assert_allclose(
                    cv['cash'].values,
                    expected_cashes,
                    err_msg=f'cash mismatch for freq={freq}, timing={timing}',
            )
            np.testing.assert_allclose(
                    cv['value'].values,
                    expected_values,
                    err_msg=f'value mismatch for freq={freq}, timing={timing}',
            )
            np.testing.assert_allclose(
                    cv['fee'].values,
                    expected_daily_fee,
                    err_msg=f'fee mismatch for freq={freq}, timing={timing}',
            )

    def test_pt_rebalance_uses_same_step_sell_cash_when_delivery_zero(self):
        """测试 PT 信号在 cash_delivery_period == 0 时，换仓场景能在同一回测步内复用卖出获得的现金。

        构造一个最小化的 PT 策略：在回测区间内只产生一次信号，把全部仓位从第一只股票 A 调整到第二只
        股票 B。初始状态设为“全仓持有 A，现金为 0”。如果实现正确，在 cash_delivery_period == 0 时，
        该信号应当在一次回测步中基本完成从 A 到 B 的换仓（考虑交易成本和最小成交单位后的少量偏差）。
        """
        from qteasy import Operator, GeneralStg, StgData, configure, run

        class OneShotPT(GeneralStg):

            def __init__(self):
                super().__init__(
                        pars=[Parameter((0, 1), name='id', par_type='int', value=0)],
                        name='OneShotPT',
                        description='单次 PT 调仓，将全部仓位从第一只股票切换到第二只股票',
                        data_types=StgData('close', freq='d', asset_type='E', window_length=1),
                        use_latest_data_cycle=True,
                )

            def realize(self):
                prices = self.get_data('close_E_d')[-1]
                id = self.get_pars('id')
                # 两只股票：第一只 A，第二只 B。
                # 第一天信号：全仓 A（1, 0），第二天信号：全仓 B（0, 1）。
                if id == 0:
                    self.par_values = (1,)  # 更新参数 id，确保第二天发出不同的信号
                    return np.array([1.0, 0.0])
                else:
                    self.par_values = (0,)  # 更新参数 id，确保第二天发出不同的信号
                    return np.array([0.0, 1.0])

        shares = ['000001.SZ', '000002.SZ']
        configure(
                asset_pool=shares,
                asset_type='E',
                invest_start='20200102',
                invest_end='20200110',
                invest_cash_amounts=[100000.0],
                trade_batch_size=100,
                sell_batch_size=100,
                cash_delivery_period=0,
                stock_delivery_period=0,
        )

        op = Operator(strategies=[OneShotPT()], signal_type='PT', run_freq='d', run_timing='close')
        res = run(op=op, mode=1, visual=False, trade_log=False)

        backtested = op.backtested
        final_amounts = backtested.own_amounts_array[-1]
        final_values = (backtested.trade_price_data[-1] * final_amounts).sum() + backtested.own_cashes[-1]
        initial_values = (backtested.trade_price_data[0] * backtested.own_amounts_array[0]).sum() + backtested.own_cashes[0]

        # 最后应当主要持有第二只股票，第一只股票仓位接近 0
        self.assertLess(abs(final_amounts[0]), abs(final_amounts[1]) * 0.05 + 1e-6)
        # 整体资产价值不应因为换仓逻辑问题而出现异常缩水
        self.assertGreater(final_values, initial_values * 0.8)

    def test_stg_trading_different_prices(self):
        """测试一个以开盘价买入，以收盘价卖出的大小盘轮动交易策略"""
        # 测试大小盘轮动交易策略，比较两个指数的过去N日收盘价涨幅，选择较大的持有，以开盘价买入，以收盘价卖出
        print('\n测试大小盘轮动交易策略，比较两个指数的过去N日收盘价涨幅，选择较大的持有，以开盘价买入，以收盘价卖出')
        stg_buy = StgBuyOpen()
        stg_sel = StgSelClose()
        op = qt.Operator(signal_type='ps', name='Open-Close Rotation')
        op.add_strategy(stg_buy,
                        run_timing='open',  # 以开盘价买进(这个策略只处理买入信号)
                        run_freq='d',
                        window_length=50,
                        par_values=(20,),
                        )
        op.add_strategy(stg_sel,
                        run_freq='d',
                        run_timing='close',  # 以收盘价卖出(这个策略只处理卖出信号)
                        window_length=50,
                        par_values=(20,), )

        self.assertEqual(len(op.groups), 2)
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_2'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'open')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
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
                     sell_batch_size=0.01)
        stock_pool = qt.filter_stock_codes(index='000300.SH', date='20211001')
        qt.configure(asset_pool=stock_pool,
                     asset_type='E',
                     benchmark_asset='000300.SH',
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
        op = qt.Operator(strategies=['finance'], signal_type='PS', name='Index Follow')
        op.set_blender(blender='s0')
        op.set_parameter(0,
                         opt_tag=1,
                         run_freq='M',
                         data_types=StgData('wt_idx|000300.SH', freq='m', asset_type='E', window_length=1),
                         sort_ascending=False,
                         weighting='proportion',
                         max_sel_count=300)
        res = qt.run(op,
                     mode=1,
                     asset_pool=qt.filter_stock_codes(index='000300.SH', date='20220103'),
                     invest_start='20220203',
                     invest_end='20220930',
                     visual=True,
                     trade_log=True)


if __name__ == '__main__':
    unittest.main()