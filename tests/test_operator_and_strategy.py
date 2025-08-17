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

from qteasy.parameter import Parameter
from qteasy.built_in import SelectingAvgIndicator, DMA, MACD, CDL
from qteasy.tafuncs import sma
from qteasy.strategy import RuleIterator, GeneralStg, FactorSorter
from qteasy.datatypes import DataType

# test parameters and datatypes:
param1 = Parameter(
        name='param1',
        par_type='int',
        par_range=(1, 100),
        value=50,
)

param2 = Parameter(
        name='param2',
        par_type='float',
        par_range=(0.0, 10.),
        value=0.5,
)

param3 = Parameter(
        name='param3',
        par_type='enum',
        par_range=('option1', 'option2', 'option3'),
        value='option1',
)

param4 = Parameter(
        name='param4',
        par_type='array[3,]',
        par_range=(1.0, 5.0),
        value=np.array([1.0, 2.0, 3.0]),
)

dtype_1 = DataType(
        name='close',
        freq='d',
        asset_type='E',
)

dtype_2 = DataType(
        name='close',
        freq='h',
        asset_type='E',
)

dtype_3 = DataType(
        name='close',
        freq='5min',
        asset_type='E',
)

dtype_4 = DataType(
        name='close',
        freq='15min',
        asset_type='E',
)

dtype_5 = DataType(
        name='close',
        freq='w',
        asset_type='E',
)


# basic test strategies
class TestGenStg(GeneralStg):
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

    def __init__(self, par_values: tuple = None):
        super().__init__(
                name='test_gen',
                description='test general strategy',
                run_freq='d',
                run_timing='close',
                pars=[param1, param2],
                data_types={'close_E_d': dtype_1, 'close_E_5min': dtype_3},
                use_latest_data_cycle=[True, False],
                window_length=[7, 9],
        )

        if par_values:
            self.update_par_values(*par_values)

    def realize(self):

        print("GeneralStg realized")
        print(f"got datas:\n{self.close_E_d}\n and \n{self.close_E_5min}")
        dt1_avg = np.mean(self.close_E_d, axis=0)
        dt2_avg = np.mean(self.close_E_5min, axis=0)
        print(f"average 1: \n{dt1_avg}, \naverage 2: \n{dt2_avg}")
        avg = dt1_avg * self.param1 + dt2_avg * self.param2
        print(f'avg = avg1 * {self.param1} + avg2 * {self.param2} = \n{avg}')
        signal = np.zeros_like(avg)
        signal[np.argmax(avg)] = 1
        print(f'got signal: \n{signal}')

        return signal


class TestFactorSorter(FactorSorter):
    """用于Test测试的简单选股策略，基于Selecting策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，从股票池的三只股票中选出今日变化率 = (今收-昨收)/平均股价（OHLC平均股价）最高的两支，放入中选池，否则落选。
    选股比例为平均分配
    """

    def __init__(self, par_values=None, **kwargs):
        super().__init__(
                name='test_factor_sorter',
                description='test factor sorter strategy',
                run_freq='d',
                run_timing='close',
                pars=[param1, param2],
                data_types={'close_E_d': dtype_1, 'close_E_5min': dtype_3},
                use_latest_data_cycle=[True, False],
                window_length=[7, 9],
                **kwargs,
        )

        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        print("FactorSorter realized")
        print(f"got datas:\n{self.close_E_d}\n and \n{self.close_E_5min}")
        dt1_avg = np.mean(self.close_E_d, axis=0)
        dt2_avg = np.mean(self.close_E_5min, axis=0)
        print(f"average 1: \n{dt1_avg}, \naverage 2: \n{dt2_avg}")
        avg = dt1_avg * self.param1 + dt2_avg * self.param2
        print(f'signal sorter = avg1 * {self.param1} + avg2 * {self.param2} = \n{avg}')

        return avg


class TestRuleIter(RuleIterator):
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

    def __init__(self, par_values=None):
        super().__init__(
                name='test_rule_iterator',
                description='test rule iterator strategy',
                run_freq='d',
                run_timing='close',
                # TODO: user-defined parameter names should also be allowed
                pars=[self.param1, self.param2],
                # TODO: user-defined dtype names should be allowed using {name: Dtype} form
                data_types={'close_E_d': self.dtype_1, 'close_E_5min': self.dtype_3},
                use_latest_data_cycle=[True, False],
                window_length=[7, 9],
        )

        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        print("RuleIterator realized")
        print(f"got datas:\n{self.close_E_d}\n and \n{self.close_E_5min}")
        dt1_avg = np.mean(self.close_E_d, axis=0)
        dt2_avg = np.mean(self.close_E_5min, axis=0)
        print(f"average 1: \n{dt1_avg}, \naverage 2: \n{dt2_avg}")
        criteria = dt1_avg * self.param1 >= dt2_avg * self.param2
        print(f'criteria = avg1 * {self.param1} >= avg2 * {self.param2} = {criteria}')
        if criteria:
            return 1
        else:
            return 0


# Other high level test strategies
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
        n, = self.par_values
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
        n, = self.par_values
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

        close_E_d = np.array(
                [[0.994, 0.412, 0.876],
                 [1.117, 1.257, 1.447],
                 [2.315, 2.08, 2.799],
                 [3.704, 3.87, 3.62],
                 [4.091, 4.127, 4.218],
                 [5.177, 5.337, 5.294],
                 [6.24, 6.254, 6.626],
                 [7.552, 7.446, 7.739],
                 [8.754, 8.192, 8.65],
                 [9.877, 9.685, 9.885],
                 [10.556, 10.774, 10.25],
                 [11.167, 11.026, 11.999],
                 [12.58, 12.236, 12.307],
                 [13.599, 13.797, 13.155],
                 [14.921, 14.938, 14.481],
                 [15.281, 15.604, 15.348],
                 [16.062, 16.559, 16.88],
                 [17.39, 17.247, 17.393],
                 [18.902, 18.344, 18.878],
                 [19.127, 19.099, 19.396],
                 [20.332, 20.854, 20.131],
                 [21.482, 21.229, 21.578],
                 [22.435, 22.952, 22.289],
                 [23.605, 23.377, 23.311],
                 [24.676, 24.23, 24.839]],
        )
        close_E_h = np.array(
                [[0.593, 0.82, 0.13],
                 [1.343, 1.253, 1.198],
                 [2.732, 2.43, 2.873],
                 [3.539, 3.9, 3.725],
                 [4.394, 4.374, 4.294],
                 [5.898, 5.237, 5.132],
                 [6.447, 6.394, 6.976],
                 [7.14, 7.871, 7.544],
                 [8.816, 8.267, 8.663],
                 [9.108, 9.517, 9.412],
                 [10.754, 10.051, 10.161],
                 [11.798, 11.445, 11.558],
                 [12.103, 12.778, 12.4],
                 [13.564, 13.616, 13.387],
                 [14.858, 14.465, 14.478],
                 [15.973, 15.728, 15.84],
                 [16.733, 16.323, 16.027],
                 [17.705, 17.642, 17.954],
                 [18.808, 18.995, 18.233],
                 [19.418, 19.02, 19.943],
                 [20.712, 20.348, 0.239],
                 [21.569, 21.743, 1.552],
                 [22.931, 22.382, 2.153],
                 [23.571, 23.224, 3.841],
                 [24.853, 24.294, 4.279]]
        )
        close_E_5min = np.array(
                [[0.97, 0.892, 0.784],
                 [1.526, 1.455, 1.606],
                 [2.509, 2.662, 2.306],
                 [3.882, 3.308, 3.838],
                 [4.766, 4.977, 4.34],
                 [5.708, 5.401, 5.724],
                 [6.744, 6.793, 6.576],
                 [7.32, 7.943, 7.124],
                 [8.906, 8.529, 8.188],
                 [9.742, 9.037, 9.896],
                 [10.576, 10.528, 10.546],
                 [11.267, 11.595, 11.761],
                 [12.747, 12.589, 12.211],
                 [13.071, 13.948, 13.95],
                 [14.499, 14.872, 14.306],
                 [15.521, 15.553, 15.939],
                 [16.383, 16.966, 16.419],
                 [17.322, 17.845, 17.583],
                 [18.631, 18.327, 18.274],
                 [19.192, 19.413, 19.882],
                 [20.533, 20.566, 20.406],
                 [21.585, 21.583, 21.433],
                 [22.381, 22.428, 22.356],
                 [23.833, 23.275, 23.104],
                 [24.514, 24.537, 24.06]]
        )
        close_E_15min = np.array(
                [[0.704, 0.179, 0.9],
                 [0.882, 0.831, 1.206],
                 [0.61, 1.024, 1.473],
                 [0.797, 1.126, 1.37],
                 [1.632, 1.767, 1.102],
                 [1.802, 1.893, 1.783],
                 [1.861, 1.88, 1.854],
                 [2.515, 2.584, 2.603],
                 [2.326, 2.737, 2.25],
                 [2.55, 2.545, 2.654],
                 [3.418, 2.655, 2.9],
                 [2.924, 3.673, 3.706],
                 [3.653, 3.95, 3.319],
                 [3.314, 4.181, 4.022],
                 [3.523, 4.29, 4.267],
                 [4.598, 4.282, 3.935],
                 [4.08, 4.105, 4.498],
                 [4.757, 5.032, 4.547],
                 [4.529, 4.91, 4.535],
                 [5.229, 5.288, 5.085],
                 [5.641, 5.074, 5.016],
                 [6.222, 6.181, 5.866],
                 [6.025, 5.769, 5.506],
                 [6.365, 6.512, 6.316],
                 [6.104, 6.982, 6.779],
                 [6.258, 6.899, 6.395],
                 [7.316, 7.388, 6.71],
                 [7.377, 7.422, 7.299],
                 [7.701, 7.688, 7.205],
                 [7.312, 7.975, 7.673],
                 [8.476, 8.472, 8.487],
                 [8.591, 8.63, 7.768],
                 [8.726, 8.918, 8.23],
                 [8.554, 8.39, 8.686],
                 [8.946, 8.794, 8.688],
                 [8.75, 9.532, 9.151],
                 [9.551, 9.622, 9.375],
                 [9.604, 9.958, 10.159],
                 [9.817, 9.933, 10.225],
                 [10.231, 9.784, 10.579],
                 [10.947, 10.895, 10.823],
                 [10.324, 10.699, 10.652],
                 [11.19, 10.514, 10.977],
                 [10.878, 11.261, 11.267],
                 [11.92, 11.524, 11.359],
                 [12.032, 12.097, 11.81],
                 [11.901, 12.379, 12.362],
                 [12.067, 12.299, 11.844],
                 [12.117, 12.482, 12.886],
                 [12.759, 12.631, 12.658],
                 [13.363, 12.705, 12.758],
                 [13.507, 13.302, 13.375],
                 [13.691, 13.421, 13.15],
                 [13.913, 13.977, 14.13],
                 [13.812, 14.027, 14.423],
                 [14.148, 13.96, 13.978],
                 [14.363, 14.556, 14.241],
                 [14.624, 15.074, 15.048],
                 [14.814, 14.968, 15.132],
                 [14.756, 15.669, 15.643],
                 [15.564, 15.386, 15.105],
                 [15.624, 16.184, 15.963],
                 [15.629, 16.339, 15.819],
                 [16.567, 16.013, 16.575],
                 [16.24, 16.318, 16.011],
                 [16.881, 16.95, 16.276],
                 [16.911, 16.986, 17.131],
                 [16.986, 17.052, 17.523],
                 [17.389, 17.634, 17.998],
                 [17.404, 18.193, 17.411],
                 [17.633, 18.462, 18.201],
                 [18.316, 18.651, 18.633],
                 [18.941, 18.129, 18.014],
                 [18.834, 18.3, 18.316],
                 [19.303, 19.457, 19.35],
                 [18.842, 19.071, 19.253],
                 [19.528, 19.033, 19.273],
                 [19.385, 19.665, 20.08],
                 [19.936, 19.765, 20.262],
                 [20.512, 20.441, 20.379],
                 [20.018, 20.994, 20.374],
                 [20.35, 20.754, 20.633],
                 [21.176, 21.46, 20.546],
                 [20.934, 21.328, 21.421],
                 [21.414, 21.486, 21.426],
                 [21.352, 21.786, 21.56],
                 [21.552, 22.29, 21.921],
                 [22.095, 21.885, 22.069],
                 [22.795, 22.686, 22.516],
                 [22.594, 23.153, 22.951],
                 [22.87, 23.063, 22.501],
                 [23.224, 23.51, 23.647],
                 [23.048, 23.83, 23.679],
                 [23.733, 23.355, 23.633],
                 [23.658, 23.856, 23.99],
                 [24.408, 24.181, 23.931],
                 [24.716, 24.531, 24.268],
                 [25.195, 24.866, 24.897],
                 [25.384, 24.922, 25.486],
                 [25.144, 25.661, 25.176]]
        )
        close_E_w = np.array(
                [[0.134, 0.207, 0.095],
                 [1.015, 0.591, 0.615],
                 [1.255, 0.85, 0.992],
                 [1.56, 1.107, 1.132],
                 [1, 1.111, 1.224],
                 [1.396, 1.325, 1.72],
                 [2.414, 1.651, 2.119],
                 [2.497, 2.406, 2.44],
                 [2.04, 2.279, 2.832],
                 [2.317, 2.473, 3.226],
                 [2.825, 2.836, 2.73],
                 [3.019, 3.574, 3.335],
                 [3.306, 3.45, 3.36],
                 [3.295, 3.401, 3.63],
                 [3.639, 4.088, 4.026],
                 [4.341, 4.214, 4.059],
                 [4.834, 4.739, 4.775],
                 [4.952, 5.152, 4.537],
                 [4.896, 4.833, 4.583],
                 [4.877, 5.266, 5.092],
                 [5.47, 5.128, 5.494],
                 [6.169, 5.552, 5.914],
                 [5.799, 5.543, 5.553],
                 [6.7, 5.976, 6.339],
                 [6.862, 6.864, 6.431],
                 [6.35, 7.196, 6.714],
                 [6.952, 6.798, 6.641],
                 [7.043, 7.416, 7.084],
                 [7.162, 7.636, 7.993],
                 [7.736, 8.095, 7.391],
                 [8.293, 8.066, 7.843],
                 [7.765, 7.795, 8.341],
                 [8.216, 8.063, 8.15],
                 [8.832, 8.347, 8.769],
                 [9.405, 8.91, 9.19],
                 [8.936, 9.377, 9.006],
                 [9.9, 9.414, 9.804],
                 [10.249, 10.085, 9.407],
                 [9.777, 9.765, 10.366],
                 [10.239, 10.05, 10.212],
                 [10.011, 10.026, 10.426],
                 [10.269, 11.219, 10.592],
                 [10.834, 11.453, 11.207],
                 [10.833, 11.703, 11.019],
                 [11.687, 11.513, 11.004],
                 [11.782, 11.565, 11.978],
                 [12.149, 12.344, 12.271],
                 [12.119, 12.728, 12.153],
                 [12.659, 12.777, 12.797],
                 [12.456, 13.043, 13.096],
                 [12.896, 12.598, 12.665],
                 [12.827, 13.557, 13.685],
                 [13.544, 13.513, 13.874],
                 [13.768, 13.322, 13.779],
                 [13.916, 13.816, 13.701],
                 [14.616, 13.817, 14.543],
                 [14.917, 14.383, 14.929],
                 [14.908, 14.919, 14.6],
                 [14.982, 15.08, 14.569],
                 [15.524, 15.283, 15.204],
                 [15.17, 15.168, 15.544],
                 [15.305, 16.242, 15.304],
                 [15.857, 16.32, 16.169],
                 [16.513, 16.501, 16.436],
                 [16.348, 16.775, 16.457],
                 [17.06, 16.416, 16.727],
                 [16.765, 16.743, 17.164],
                 [16.781, 17.367, 17.243],
                 [17.276, 17.242, 17.586],
                 [17.417, 17.519, 17.352],
                 [17.632, 17.625, 17.965],
                 [18.121, 17.759, 18.735],
                 [18.433, 18.643, 18.416],
                 [18.696, 19.104, 19.131],
                 [18.568, 18.507, 18.979],
                 [19.406, 19.572, 19.007],
                 [19.416, 19.216, 19.95],
                 [19.894, 19.411, 19.353],
                 [20.363, 19.79, 19.849],
                 [20.131, 19.823, 19.844],
                 [20.187, 20.775, 20.502],
                 [20.894, 20.286, 20.253],
                 [21.228, 21.335, 21.061],
                 [21.201, 21.002, 20.979],
                 [21.266, 21.771, 21.111],
                 [22.058, 22.077, 21.413],
                 [21.537, 22.34, 21.619],
                 [22.374, 22.441, 22.309],
                 [22.522, 22.259, 22.563],
                 [23.248, 22.452, 22.542],
                 [22.768, 22.674, 23.169],
                 [23.585, 23.053, 23.749],
                 [23.649, 23.068, 23.016],
                 [24.154, 23.828, 23.791],
                 [24.146, 24.483, 23.912],
                 [23.989, 23.954, 23.899],
                 [24.663, 24.686, 24.552],
                 [24.958, 24.981, 24.41],
                 [24.847, 25.181, 24.871],
                 [24.873, 25.657, 24.869]]
        )

        trade_price_h_data = np.array(
                [[37.58, 32.50, 24.14],
                 [38.65, 33.31, 23.80],
                 [38.50, 34.20, 24.52],
                 [38.38, 34.10, 23.95],
                 [38.80, 34.09, 26.35],
                 [38.25, 34.12, 25.96],
                 [38.92, 34.43, 25.14],
                 [39.05, 34.12, 24.89],
                 [39.66, 34.45, 25.78],
                 [40.47, 35.48, 26.37],
                 [40.68, 35.45, 25.99],
                 [40.38, 35.21, 25.28],
                 [40.65, 35.10, 24.91],
                 [41.05, 35.05, 24.92],
                 [42.03, 35.05, 25.30],
                 [41.21, 34.63, 25.84],
                 [40.54, 34.95, 26.08],
                 [40.03, 34.88, 27.32],
                 [39.30, 34.70, 27.18],
                 [38.35, 33.84, 27.16],
                 [38.41, 34.42, 27.16],
                 [38.49, 34.29, 26.85],
                 [38.49, 34.35, 28.50],
                 [38.16, 34.27, 29.48],
                 [37.72, 34.71, 28.93],
                 [38.00, 34.87, 28.71],
                 [37.17, 34.54, 29.28],
                 [37.27, 34.15, 29.64],
                 [36.71, 33.97, 29.23],
                 [38.49, 35.15, 30.44],
                 [38.69, 36.14, 29.67],
                 [38.16, 36.08, 30.13],
                 [38.27, 37.03, 29.54],
                 [37.46, 36.56, 29.42],
                 [37.16, 35.21, 29.02],
                 [37.31, 35.52, 28.85],
                 [38.25, 36.42, 29.18],
                 [38.25, 36.61, 29.51],
                 [38.25, 36.97, 28.69],
                 [37.00, 36.91, 28.80],
                 [36.56, 36.24, 28.18],
                 [36.00, 36.49, 28.19],
                 [35.58, 36.62, 28.00],
                 [35.03, 35.61, 27.41],
                 [35.05, 37.11, 27.70],
                 [34.58, 36.94, 27.47],
                 [34.88, 37.45, 27.24]]
        )

        close_d_df = pd.DataFrame(
                close_E_d, columns=['A', 'B', 'C'], index=pd.date_range(start='2023-01-01', periods=25, freq='D')
        )
        close_h_df = pd.DataFrame(
                close_E_h, columns=['A', 'B', 'C'], index=pd.date_range(start='2023-01-01', periods=25, freq='D')
        )
        close_5min_df = pd.DataFrame(
                close_E_5min, columns=['A', 'B', 'C'], index=pd.date_range(start='2023-01-01', periods=25, freq='D')
        )
        close_15min_df = pd.DataFrame(
                close_E_15min, columns=['A', 'B', 'C'], index=pd.date_range(start='2023-01-01', periods=100, freq='6h')
        )
        close_w_df = pd.DataFrame(
                close_E_w, columns=['A', 'B', 'C'], index=pd.date_range(start='2023-01-01', periods=100, freq='6h')
        )

        trade_price_h_df = pd.DataFrame(
                trade_price_h_data, columns=['A', 'B', 'C'],
                index=pd.date_range(start='2023-01-01', periods=47, freq='4h')
        )

        # 1， 准备模拟历史数据对象

        open_d = DataType(
                name='open',
                freq='d',
                asset_type='E'
        )

        volume_d = DataType(
                name='volume',
                freq='d',
                asset_type='E'
        )

        close_d = DataType(
                name='close',
                freq='d',
                asset_type='E'
        )

        high_h = DataType(
                name='high',
                freq='h',
                asset_type='E',
        )

        close_h = DataType(
                name='close',
                freq='h',
                asset_type='E',
        )

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

        stg_dma.par_values = (10, 20, 30)
        self.assertEqual(stg_dma.par_values, (10, 20, 30))
        stg_macd.par_values = (10, 20, 30)
        self.assertEqual(stg_macd.par_values, (10, 20, 30))
        stg_trix.set_pars((10, 20))
        self.assertEqual(stg_trix.par_values, (10, 20))
        stg_dma.set_pars({'a': (10, 20, 30),
                          'b': (11, 21, 31),
                          'c': (12, 22, 32)})
        self.assertEqual(stg_dma.par_values,
                         {'a': (10, 20, 30),
                          'b': (11, 21, 31),
                          'c': (12, 22, 32)})

        # test errors
        self.assertRaises(AssertionError, stg_dma.set_pars, 'wrong input')  # wrong input type
        self.assertRaises(ValueError, stg_dma.set_pars, (10, -100))  # par count does not match
        self.assertRaises(ValueError, stg_dma.set_pars, (10, 10, -10))  # par out of range
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
        op.set_parameter('macd', run_timing='open')
        op.set_parameter('dma', run_timing='close')
        op.set_parameter('trix', run_timing='open')
        stg_close = op.get_strategies_by_group('close')
        stg_open = op.get_strategies_by_group('open')
        stg_high = op.get_strategies_by_group('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, [op.strategies[1]])
        self.assertEqual(stg_open, [op.strategies[0], op.strategies[2]])
        self.assertEqual(stg_high, [])

        stg_wrong = op.get_strategies_by_group(123)
        self.assertIsInstance(stg_wrong, list)
        self.assertEqual(stg_wrong, [])

    def test_get_strategy_count_by_run_timing(self):
        """ test get_strategy_count_by_group"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', run_timing='open')
        op.set_parameter('dma', run_timing='close')
        op.set_parameter('trix', run_timing='open')
        stg_close = op.get_strategy_count_by_group('close')
        stg_open = op.get_strategy_count_by_group('open')
        stg_high = op.get_strategy_count_by_group('high')

        self.assertIsInstance(stg_close, int)
        self.assertIsInstance(stg_open, int)
        self.assertIsInstance(stg_high, int)

        self.assertEqual(stg_close, 1)
        self.assertEqual(stg_open, 2)
        self.assertEqual(stg_high, 0)

        stg_wrong = op.get_strategy_count_by_group(123)
        self.assertIsInstance(stg_wrong, int)
        self.assertEqual(stg_wrong, 0)

    def test_get_strategy_names_by_price_type(self):
        """ test get_strategy_names_by_price_type"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        op.set_parameter('macd', run_timing='open')
        op.set_parameter('dma', run_timing='close')
        op.set_parameter('trix', run_timing='open')
        stg_close = op.get_strategy_names_by_group('close')
        stg_open = op.get_strategy_names_by_group('open')
        stg_high = op.get_strategy_names_by_group('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, ['DMA'])
        self.assertEqual(stg_open, ['MACD', 'TRIX'])
        self.assertEqual(stg_high, [])

        stg_wrong = op.get_strategy_names_by_group(123)
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
        op.set_parameter('macd', run_timing='open')
        op.set_parameter('dma', run_timing='close')
        op.set_parameter('trix', run_timing='open')
        stg_close = op.get_strategy_id_by_group('close')
        stg_open = op.get_strategy_id_by_group('open')
        stg_high = op.get_strategy_id_by_group('high')

        self.assertIsInstance(stg_close, list)
        self.assertIsInstance(stg_open, list)
        self.assertIsInstance(stg_high, list)

        self.assertEqual(stg_close, ['dma'])
        self.assertEqual(stg_open, ['macd', 'trix'])
        self.assertEqual(stg_high, [])

        op.add_strategies('dma, macd')
        op.set_parameter('dma_1', run_timing='open')
        op.set_parameter('macd', run_timing='open')
        op.set_parameter('macd_1', run_timing='close')
        op.set_parameter('trix', run_timing='close')
        print(f'Operator strategy id:\n'
              f'{op.strategies} on memory pos:\n'
              f'{[id(stg) for stg in op.strategies]}')
        stg_close = op.get_strategy_id_by_group('close')
        stg_open = op.get_strategy_id_by_group('open')
        stg_all = op.get_strategy_id_by_group()
        print(f'All IDs of strategies:\n'
              f'{stg_all}\n'
              f'All price types of strategies:\n'
              f'{[stg.strategy_run_timing for stg in op.strategies]}')
        self.assertEqual(stg_close, ['dma', 'trix', 'macd_1'])
        self.assertEqual(stg_open, ['macd', 'dma_1'])

        stg_wrong = op.get_strategy_id_by_group(123)
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
        """ test Property strategy_count, and the method get_strategy_count_by_group()"""
        self.assertEqual(self.op.strategy_count, 1)
        self.assertEqual(self.op2.strategy_count, 3)
        self.assertEqual(self.op.get_strategy_count_by_group(), 1)
        self.assertEqual(self.op2.get_strategy_count_by_group(), 3)
        self.assertEqual(self.op.get_strategy_count_by_group('close'), 1)
        self.assertEqual(self.op.get_strategy_count_by_group('high'), 0)
        self.assertEqual(self.op2.get_strategy_count_by_group('close'), 3)
        self.assertEqual(self.op2.get_strategy_count_by_group('open'), 0)

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
        op.set_parameter('dma', run_timing='open')
        op.set_parameter('trix', run_timing='close')

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
        self.assertEqual(op.strategy_groups, ['close', 'open'])
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
        """ test property strategy_groups"""
        print('------test property bt_price_tyeps-------')
        op = qt.Operator()
        self.assertIsInstance(op.strategy_groups, list)
        self.assertEqual(len(op.strategy_groups), 0)
        self.assertEqual(op.strategy_groups, [])

        op = qt.Operator('macd, dma, trix')
        btp = op.strategy_groups
        self.assertIsInstance(btp, list)
        self.assertEqual(btp[0], 'close')
        op.set_parameter('macd', run_timing='open')
        btp = op.strategy_groups
        btpc = op.bt_price_type_count
        print(f'price_types are \n{btp}')
        self.assertIsInstance(btp, list)
        self.assertEqual(len(btp), 2)
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.add_strategies(['dma', 'macd'])
        op.set_parameter('dma_1', run_timing='close')
        btp = op.strategy_groups
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.remove_strategy('dma_1')
        btp = op.strategy_groups
        btpc = op.bt_price_type_count
        self.assertEqual(btp[0], 'close')
        self.assertEqual(btp[1], 'open')
        self.assertEqual(btpc, 2)

        op.remove_strategy('macd_1')
        btp = op.strategy_groups
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
        op.set_parameter('macd', run_timing='open')
        op.set_parameter('dma', run_timing='open')
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
        op.set_parameter('dma', run_timing='open')
        op.set_parameter('cdl', run_timing='open')
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
        self.assertEqual(op.strategies[0].par_values, (12, 123, 25))
        op.clear_strategies()
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

    def test_operator_assign_history_data(self):
        """测试分配Operator运行所需历史数据"""
        raise NotImplementedError

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
        op.set_parameter('all', run_timing='close')
        print(f'Can also set up strategy parameters by strategy index')
        op.set_parameter(2, run_timing='open')
        op.set_parameter(2,
                         opt_tag=1,
                         pars=(9, -0.09),
                         window_length=10)
        self.assertEqual(op.strategies[0].par_values, (5, 10, 5))
        self.assertEqual(op.strategies[0].par_range, ((5, 10), (5, 15), (5, 15)))
        self.assertEqual(op.strategies[2].par_values, (9, -0.09))
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
        self.assertEqual(op.strategy_groups, ['close', 'open'])
        op.set_blender('s0 and s1 or s2', 'open')
        self.assertEqual(op.get_blender('open'), ['or', 's2', 'and', 's1', 's0'])
        op.set_blender('s0 or s1 and s2', 'close')
        self.assertEqual(op.get_blender(), {'close': ['or', 'and', 's2', 's1', 's0'],
                                            'open':  ['or', 's2', 'and', 's1', 's0']})

        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (5, 15), (1, 100), (-0.5, 0.5)],
                          ['int', 'int', 'int', 'int', 'float']))
        self.assertEqual(op.opt_tags, [1, 0, 1])

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
        self.assertEqual(op.strategies[0].par_values, (5, 10, 5))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (35, 120, 0.02))
        self.assertEqual(op.opt_tags, [1, 0, 0])
        op.set_opt_par((5, 12, 9))
        self.assertEqual(op.strategies[0].par_values, (5, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (35, 120, 0.02))

        op.set_parameter('crossline',
                         opt_tag=1,
                         par_range=((5, 10), (5, 35), (0, 1)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('crossline',
                         pars=(5, 10, 0.1))
        self.assertEqual(op.opt_tags, [1, 0, 1])
        op.set_opt_par((5, 12, 9, 8, 26, 0.09))
        self.assertEqual(op.strategies[0].par_values, (5, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (8, 26, 0.09))

        op.set_opt_par((9, 200, 155, 8, 26, 0.09, 5, 12, 9))
        self.assertEqual(op.strategies[0].par_values, (9, 200, 155))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (8, 26, 0.09))

        # test set_opt_par when opt_tag is set to be 2 (enumerate type of parameters)
        op.set_parameter('crossline',
                         opt_tag=2,
                         par_range=((5, 10), (5, 35), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('crossline',
                         pars=(5, 10, 5))
        self.assertEqual(op.opt_tags, [1, 0, 2])
        self.assertEqual(op.strategies[0].par_values, (9, 200, 155))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (5, 10, 5))
        op.set_opt_par((5, 12, 9, (8, 26, 9)))
        self.assertEqual(op.strategies[0].par_values, (5, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (8, 26, 9))

        # Test Errors
        # op.set_opt_par主要在优化过程中自动生成，已经保证了参数的正确性，因此不再检查参数正确性

    def test_operator_generate(self):
        """ 测试operator对象生成完整交易信号

        :return:
        """
        raise NotImplementedError

    def test_operator_generate_stepwise(self):
        """ 测试operator对象在实时模式下生成交易信号

        :return:
        """
        # TODO: implement this test
        raise NotImplementedError

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
                run_freq='d',
                window_length=50,
                pars=(20,),
                strategy_data_types='close',  # 考察收盘价变化率
                run_timing='open',  # 以开盘价买进(这个策略只处理买入信号)
        )
        op.set_parameter(
                1,
                data_freq='d',
                run_freq='d',
                window_length=50,
                pars=(20,),
                strategy_data_types='close',  # 考察收盘价的变化率
                run_timing='close',  # 以收盘价卖出(这个策略只处理卖出信号)
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
                         run_freq='m',
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
        op_min.set_parameter(0, data_freq='h', run_freq='h')
        op_min.set_parameter(1, data_freq='h', run_freq='d')
        op_min.set_parameter(2, data_freq='h', run_freq='y')
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