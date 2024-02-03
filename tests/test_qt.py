# coding=utf-8
# ======================================
# File:     test_qt.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for general functions of
#   qteasy.
# ======================================
import unittest

import qteasy as qt
import numpy as np
from qteasy.tsfuncs import stock_basic

from qteasy.tafuncs import bbands
from qteasy.tafuncs import sma

from qteasy.strategy import BaseStrategy, RuleIterator, GeneralStg


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
        super().__init__(name='test_LS',
                         description='test long/short strategy',
                         par_count=2,
                         par_types='discr, conti',
                         par_range=([1, 20], [2, 20]),
                         strategy_data_types='close, open, high, low',
                         data_freq='d',
                         window_length=5)
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
        super().__init__(name='test_SEL',
                         description='test portfolio selection strategy',
                         par_count=0,
                         par_types='',
                         par_range=(),
                         strategy_data_types='high, low, close',
                         data_freq='d',
                         strategy_run_freq='10d',
                         window_length=5,
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


class Cross_SMA_PS(qt.RuleIterator):
    """自定义双均线择时策略策略，产生的信号类型为交易信号"""

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
                pars=(25, 100, 0.01),
                par_count=3,
                par_types=['discr', 'discr', 'conti'],
                par_range=[(10, 250), (10, 250), (0.0, 0.5)],
                name='CUSTOM ROLLING TIMING STRATEGY',
                description='Customized Rolling Timing Strategy for Testing',
                strategy_data_types='close',
                window_length=200,
        )

    # 策略的具体实现代码写在策略的realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def realize(self, h, r=None, t=None, pars=None):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度
        """
        f, s, m = pars
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = h.T
        # 计算长短均线的当前值和昨天的值
        sma = qt.tafuncs.sma
        s_ma = sma(h[0], s)
        f_ma = sma(h[0], f)

        s_today, s_last = s_ma[-1], s_ma[-2]
        f_today, f_last = f_ma[-1], f_ma[-2]

        # 计算慢均线的停止边界，当快均线在停止边界范围内时，平仓，不发出买卖信号
        s_ma_u = s_today * (1 + m)
        s_ma_l = s_today * (1 - m)

        # 根据观望模式在不同的点位产生交易信号
        if (f_last < s_ma_u) and (f_today > s_ma_u):  # 当快均线自下而上穿过上边界，开多仓
            return 1.
        elif (f_last > s_ma_u) and (f_today < s_ma_u):  # 当快均线自上而下穿过上边界，平多仓
            return -1.
        elif (f_last > s_ma_l) and (f_today < s_ma_l):  # 当快均线自上而下穿过下边界，开空仓
            return -1.
        elif (f_last < s_ma_l) and (f_today > s_ma_l):  # 当快均线自下而上穿过下边界，平空仓
            return 1.
        else:  # 其余情况不产生任何信号
            return 0.


class Cross_SMA_PT(qt.RuleIterator):
    """自定义双均线择时策略策略，产生的信号类型为持仓目标信号"""

    def __init__(self):
        """这个均线择时策略只有三个参数：
            - SMA 慢速均线，所选择的股票
            - FMA 快速均线
            - M   边界值

            策略的其他说明

        """
        super().__init__(
                pars=(25, 100, 0.01),
                par_count=3,
                par_types=['discr', 'discr', 'conti'],
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
        sma = qt.tafuncs.sma
        s_ma = sma(h[0], s)[-1]
        f_ma = sma(h[0], f)[-1]

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


class TestQT(unittest.TestCase):
    """对qteasy系统进行总体测试"""

    def setUp(self):
        # 准备测试所需数据，确保本地数据源有足够的数据

        self.op = qt.Operator(strategies=['dma', 'macd'])
        print('  START TO TEST QT GENERAL OPERATIONS\n'
              '=======================================')
        self.op.set_parameter('dma', opt_tag=1, par_range=[(10, 250), (10, 250), (10, 250)])
        self.op.set_parameter('macd', opt_tag=1, par_range=[(10, 250), (10, 250), (10, 250)])
        self.op.signal_type = 'pt'

        qt.configure(benchmark_asset='000300.SH',
                     mode=1,
                     benchmark_asset_type='IDX',
                     asset_pool='000300.SH',
                     asset_type='IDX',
                     opti_output_count=50,
                     invest_start='20070110',
                     trade_batch_size=0.,
                     sell_batch_size=0.,
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
        self.assertEqual(config.benchmark_asset, '000300.SH')
        self.assertEqual(config.benchmark_asset_type, 'IDX')
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
        self.assertEqual(config.benchmark_asset_type, 'IDX')
        self.assertEqual(config.asset_pool, '000300.SH')
        self.assertEqual(config.invest_start, '20070110')

        config_copy = config.copy()
        qt.configure(config_copy,
                     mode=1,
                     benchmark_asset='000002.SZ',
                     benchmark_asset_type='E')
        self.assertEqual(config.mode, 2)
        self.assertEqual(config.benchmark_asset, '000300.SH')
        self.assertEqual(config.benchmark_asset_type, 'IDX')
        self.assertEqual(config.asset_pool, '000300.SH')
        self.assertEqual(config.invest_start, '20070110')
        self.assertEqual(config_copy.mode, 1)
        self.assertEqual(config_copy.benchmark_asset, '000002.SZ')
        self.assertEqual(config_copy.benchmark_asset_type, 'E')
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

    def test_run_mode_0(self):
        """测试策略的实时信号生成模式"""
        op = qt.Operator(strategies=['stema'], op_type='stepwise')
        op.set_parameter('stema', pars=(6,))
        qt.QT_CONFIG.mode = 0
        # qt.run(op)
        # TODO: running qteasy in mode 0 will enter interactive shell, which is not testable

    def test_run_mode_1(self):
        """测试策略的回测模式,结果打印但不可视化"""
        qt.configure(mode=1,
                     trade_batch_size=1,
                     visual=False,
                     trade_log=True,
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
               trade_log=False,
               buy_sell_points=False,
               show_positions=False,
               invest_cash_dates='20070616')

        print(f'test plot with both buy-sell points and position indicators')
        qt.configuration(up_to=1, default=True)
        qt.run(self.op,
               mode=1,
               trade_batch_size=1,
               visual=True,
               trade_log=False,
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
        # 使用以下参数测试所有qt.built_in中的交易策略
        #   mode=1,
        #   asset_pool='000300.SH, 399006.SZ',
        #   start='20200101',
        #   end='20211231',
        #   trade_log=False,
        #   visual=False,
        # 其他均为默认参数
        print(f'testing built-in strategies')
        for strategy in qt.built_in_strategies():
            print(f'testing strategy {strategy}')
            op = qt.Operator(strategies=[strategy])
            qt.run(
                    op,
                    mode=1,
                    asset_pool='000300.SH, 399006.SZ',
                    invest_start='20200101',
                    invest_end='20211231',
                    trade_log=False,
                    visual=False,
            )

    def test_multi_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        op = qt.Operator(strategies=['long', 'finance', 'signal_none'])
        all_shares = qt.filter_stocks(date='20070101')
        shares_banking = qt.filter_stock_codes(date='20070101', industry='银行')
        print('extracted banking share pool:')
        print(all_shares.loc[all_shares.index.isin(shares_banking)])
        shares_estate = list(all_shares.loc[all_shares.industry == "全国地产"].index.values)
        qt.configure(asset_pool=shares_banking[0:10],
                     asset_type='E',
                     benchmark_asset='000300.SH',
                     benchmark_asset_type='IDX',
                     opti_output_count=50,
                     invest_start='20070101',
                     invest_end='20181231',
                     invest_cash_dates=None,
                     trade_batch_size=1.,
                     mode=1,
                     trade_log=True)
        op.set_parameter('long', pars=())
        op.set_parameter('finance', pars=(True, 'proportion', 'greater', 0, 0, 0.4),
                         strategy_run_freq='Q',
                         strategy_data_types='pe',
                         sort_ascending=True,
                         weighting='proportion',
                         condition='greater',
                         ubound=0,
                         lbound=0,
                         max_sel_count=0.4)
        op.set_parameter('signal_none', pars=())
        op.set_blender('avg(s0, s1, s2)', 'ls')
        op.info()
        print(f'test portfolio selecting from shares_estate: \n{shares_estate}')
        qt.configuration()
        qt.run(op, visual=True, trade_log=True, trade_batch_size=100)

    def test_many_share_mode_1(self):
        """test built-in strategy selecting finance
        """
        print(f'test portfolio selection from large quantities of shares')
        op = qt.Operator(strategies=['long', 'finance', 'signal_none'])
        qt.configure(asset_pool=qt.filter_stock_codes(date='20070101',
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
                     benchmark_asset='000300.SH',
                     benchmark_asset_type='IDX',
                     opti_output_count=50,
                     invest_start='20070101',
                     invest_end='20171228',
                     invest_cash_dates=None,
                     trade_batch_size=1.,
                     mode=1,
                     trade_log=False,
                     hist_dnld_parallel=0)
        print(f'in total a number of {len(qt.QT_CONFIG.asset_pool)} shares are selected!')
        op.set_parameter('long', pars=())
        op.set_parameter('finance', pars=(True, 'proportion', 'greater', 0, 0, 30),
                         strategy_run_freq='Q',
                         strategy_data_types='basic_eps',
                         sort_ascending=True,
                         weighting='proportion',
                         condition='greater',
                         ubound=0,
                         lbound=0,
                         max_sel_count=30)
        op.set_parameter('signal_none', pars=())
        op.set_blender('avg(s0, s1, s2)', 'close')
        qt.run(op, visual=False, trade_log=True)

    def test_op_stepwise(self):
        """测试stepwise模式下的operator的表，使用两个测试专用交易策略"""
        # confirm that operator running results are same in stepwise and batch type
        op_batch = qt.Operator(strategies=['dma', 'macd'], signal_type='pt', op_type='batch')
        op_stepwise = qt.Operator(strategies=['dma', 'macd'], signal_type='pt', op_type='step')
        for op in [op_batch, op_stepwise]:
            op.set_parameter(0, window_length=100, pars=(12, 26, 9))
            op.set_parameter(1, window_length=100, pars=(12, 26, 9))

        qt.configure(
                benchmark_asset='000300.SH',
                benchmark_asset_type='IDX',
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
        res_batch = op_batch.run(mode=1)
        print('backtest in stepwise mode:')
        res_stepwise = op_stepwise.run(mode=1)
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
        res_batch = op_batch.run(
                mode=1,
                invest_start='20180101',
                invest_end='20191231'
        )
        print('backtest in stepwise mode:')
        res_stepwise = op_stepwise.run(
                mode=1,
                invest_start='20180101',
                invest_end='20191231'
        )
        val_batch = res_batch["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        val_stepwise = res_stepwise["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values

        self.assertTrue(np.allclose(val_batch, val_stepwise))
        self.assertEqual(res_batch['final_value'],
                         res_stepwise['final_value'])

        # test operator that utilizes trade data
        stg1 = TestLSStrategy()
        stg2 = TestSelStrategy()
        stg1.window_length = 100
        stg2.window_length = 100
        stg2.strategy_run_freq = '2w'
        op_batch = qt.Operator(strategies=[stg1, stg2], signal_type='pt', op_type='batch')
        op_stepwise = qt.Operator(strategies=[stg1, stg2], signal_type='pt', op_type='stepwise')
        par_stg1 = {'000100': (20, 10),
                    '000200': (20, 10),
                    '000300': (20, 6)}
        par_stg2 = ()
        for op in [op_batch, op_stepwise]:
            op.set_parameter(0, pars=par_stg1, opt_tag=1, par_range=([1, 20], [2, 100]))
            op.set_parameter(1, pars=par_stg2, opt_tag=1)

        qt.configure(
                benchmark_asset='000300.SH',
                benchmark_asset_type='IDX',
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
        res_batch = op_batch.run(mode=1)
        print('backtest in stepwise mode:')
        res_stepwise = op_stepwise.run(mode=1)
        val_batch = res_batch["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        val_stepwise = res_stepwise["complete_values"][["601398.SH", "600000.SH", "000002.SZ"]].values
        print(f'the result of batched operation is\n'
              f'{val_batch}\n'
              f'and the result of stepwise operation is\n'
              f'{val_stepwise}')

        print('backtest in batch mode in optimization mode:')
        op_batch.run(mode=2)
        print('backtest in stepwise mode in optimization mode')
        op_stepwise.run(mode=2)

        print('test stepwise mode with different sample freq')

    def test_sell_short(self):
        """ 测试sell_short模式是否能正常工作（买入卖出负份额）"""
        op = qt.Operator([Cross_SMA_PS()], signal_type='PS')
        op.set_parameter(0, pars=(23, 100, 0.02))
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
        op.set_parameter(0, (23, 100, 0.02))
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