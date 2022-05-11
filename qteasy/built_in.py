# coding=utf-8
# ======================================
# File:     built_in.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-09-27
# Desc:
#   Qteasy built-in Strategies.
# ======================================

import numpy as np
import qteasy.strategy as stg
from .tafuncs import sma, ema, dema, trix, cdldoji, bbands, atr, apo
from .tafuncs import ht, kama, mama, t3, tema, trima, wma, sarext, adx
from .tafuncs import aroon, aroonosc, cci, cmo, macdext, mfi, minus_di
from .tafuncs import plus_di, minus_dm, plus_dm, mom, ppo, rsi, stoch, stochf
from .tafuncs import stochrsi, ultosc, willr


# All following strategies can be used to create strategies by referring to its stragety ID

# Built-in Rolling timing strategies:
def built_in_list(*args, **kwargs):
    """display information of built-in strategies"""
    return BUILT_IN_STRATEGIES


def built_ins(*args, **kwargs):
    """alias of built_in_list()"""
    return built_in_list(*args, **kwargs)


def built_in_strategies(*args, **kwargs):
    """alias of built_in_list()"""
    return built_in_list(*args, **kwargs)


# Basic technical analysis based Timing strategies
class TimingCrossline(stg.RuleIterator):
    """crossline择时策略类，利用长短均线的交叉确定多空状态

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用4个参数，
        s: int, 短均线计算日期；
        l: int, 长均线计算日期；
        m: int, 均线边界宽度；
        hesitate: str, 均线跨越类型
    参数输入数据范围：[(10, 250), (10, 250), (10, 250), ('buy', 'sell', 'none')]

    """

    def __init__(self, pars: tuple = (35, 120, 10, 'buy')):
        """Crossline交叉线策略只有一个动态属性，其余属性均不可变"""
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'discr', 'conti', 'enum'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (1, 100), ('buy', 'sell', 'none')],
                         name='CROSSLINE',
                         description='Moving average crossline strategy, determine long/short position according to the ' \
                                  'cross point of long and short term moving average prices ',
                         data_types='close')

    def _realize(self, hist_data, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        # 计算长短均线之间的距离
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        # 根据观望模式在不同的点位产生Long/short标记
        if hesitate == 'buy':
            pass
            # m = -m
        elif hesitate == 'sell':
            pass
        else:  # hesitate == 'none'
            pass
            # m = 0
        if diff < -m:
            return 1
        elif diff > m:
            return -1
        else:
            return 0


class TimingMACD(stg.RuleIterator):
    """MACD择时策略类，运用MACD均线策略，在hist_price Series对象上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars: tuple = (12, 26, 9)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         name='MACD',
                         description='MACD strategy, determine long/short position according to differences of '
                                  'exponential weighted moving average prices',
                         data_types='close')

    def _realize(self, hist_data, params):
        """生成单只个股的择时多空信号
        生成MACD多空判断：
        1， MACD柱状线为正，多头状态，为负空头状态：由于MACD = diff - dea

        输入:
            idx: 指定的参考指数历史数据
            sRange, 短均线参数，短均线的指数移动平均计算窗口宽度，单位为日
            lRange, 长均线参数，长均线的指数移动平均计算窗口宽度，单位为日
            dRange, DIFF的指数移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """

        s, l, m = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T

        # 计算指数的指数移动平均价格
        diff = ema(h[0], s) - ema(h[0], l)
        dea = ema(diff, m)
        _macd = 2 * (diff - dea)
        # 以下使用tafuncs中的macd函数（基于talib）生成相同结果，但速度稍慢
        # diff, dea, _macd = macd(hist_data, s, l, m)

        if _macd[-1] > 0:
            return 1
        else:
            return -1


class TimingTRIX(stg.RuleIterator):
    """TRIX择时策略，运用TRIX均线策略，利用历史序列上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270天
    策略使用2个参数，
        s: int, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        m: int, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”
    参数输入数据范围：[(10, 250), (10, 250)]
    """

    def __init__(self, pars=(25, 125)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(2, 50), (3, 150)],
                         name='TRIX',
                         description='TRIX strategy, determine long/short position according to triple exponential '
                                  'weighted moving average prices',
                         data_freq='d',
                         sample_freq='d',
                         window_length=270,
                         data_types='close')

    def _realize(self, hist_data, params):
        """参数:

        input:
        :param hist_data:
        :param params:
        :return:

        """
        s, m = params
        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        trx = trix(h[0], s) * 100
        matrix = sma(trx, m)
        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = 1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 0
        if trx[-1] > matrix[-1]:
            return 1
        else:
            return -1


class TimingCDL(stg.RuleIterator):
    """CDL择时策略，在K线图中找到符合要求的cdldoji模式

    数据类型：open, high, low, close 开盘，最高，最低，收盘价，多数据输入
    数据分析频率：天
    数据窗口长度：100天
    参数数量：0个，参数类型：N/A，输入数据范围：N/A
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=None,
                         par_bounds_or_enums=None,
                         name='CDL INDICATOR',
                         description='CDL Indicators, determine buy/sell signals according to CDL Indicators',
                         window_length=200,
                         data_types='open,high,low,close')

    def _realize(self, hist_data, params=None):
        """参数:

        input:
            None
        """
        # 计算历史数据上的CDL指标
        h = hist_data.T
        cat = (cdldoji(h[0], h[1], h[2], h[3]).cumsum() // 100)

        return float(cat[-1])


class SoftBBand(stg.RuleIterator):
    """布林带线择时策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空, 均线的种类可选"""

    def __init__(self, pars=(20, 2, 2, 0)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'conti', 'conti', 'discr'],
                         par_bounds_or_enums=[(2, 100), (0.5, 5), (0.5, 5), (0, 8)],
                         name='Soft Bolinger Band',
                         description='Soft-BBand strategy, determine buy/sell signals according to BBand positions',
                         window_length=200,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
            u: number deviation up
            d: number deviation down
            m: ma type
        """
        p, u, d, m = params
        h = hist_data.T
        hi, mid, low = bbands(h[0], p, u, d, m)
        # 策略:
        # 如果价格低于下轨，则逐步买入，每次买入可分配投资总额的10%
        # 如果价格高于上轨，则逐步卖出，每次卖出投资总额的33.3%
        if h[0][-1] < low[-1]:
            sig = -0.333
        elif h[0][-1] > hi[-1]:
            sig = 0.1
        else:
            sig = 0
        return sig


class TimingBBand(stg.RuleIterator):
    """BBand择时策略，运用布林带线策略，利用历史序列上生成交易信号

        数据类型：close 收盘价，单数据输入
        数据分析频率：天
        数据窗口长度：270天
        策略使用2个参数，
            span: int, 移动平均计算窗口宽度，单位为日
            upper: float, 布林带的上边缘所处的标准差倍数
            lower: float, 布林带的下边缘所处的标准差倍数
        参数输入数据范围：[(10, 250), (0.5, 2.5), (0.5, 2.5)]
        """

    def __init__(self, pars=(20, 2, 2)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'conti', 'conti'],
                         par_bounds_or_enums=[(10, 250), (0.5, 2.5), (0.5, 2.5)],
                         name='BBand',
                         description='BBand strategy, determine long/short position according to Bollinger bands',
                         data_freq='d',
                         sample_freq='d',
                         window_length=270,
                         data_types=['close'])

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:

        span, upper, lower = params
        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        price = h[0]
        upper, middle, lower = bbands(close=price, timeperiod=span, nbdevup=upper, nbdevdn=lower)
        # 生成BBANDS操作信号判断：
        # 1, 当avg_price从上至下穿过布林带上缘时，产生空头建仓或平多仓信号 -1
        # 2, 当avg_price从下至上穿过布林带下缘时，产生多头建仓或平空仓信号 +1
        # 3, 其余时刻不产生任何信号
        if price[-2] >= upper[-2] and price[-1] < upper[-1]:
            return +1.
        elif price[-2] <= lower[-2] and price[-1] > lower[-1]:
            return -1.
        else:
            return 0.


class TimingSAREXT(stg.RuleIterator):
    """扩展抛物线SAR策略，当指标大于0时发出买入信号，当指标小于0时发出卖出信号
    """

    def __init__(self, pars=(0, 3)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(-100, 100), (0, 5)],
                         name='Parabolic SAREXT',
                         description='Parabolic SAR Extended Strategy, determine buy/sell signals according to CDL Indicators',
                         window_length=200,
                         data_types='high, low')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
            u: number deviation up
            d: number deviation down
            m: ma type
        """
        a, m = params
        h = hist_data.T
        sar = sarext(h[0], h[1], a, m)[-1]
        # 策略:
        # 当指标大于0时，输出多头
        # 当指标小于0时，输出空头
        if sar > 0:
            cat = 1
        elif sar < 0:
            cat = -1
        else:
            cat = 0
        return cat


# Built-in Single-cross-line strategies:
# these strateges are basically adopting same philosaphy:
# they track the close price vs its moving average config_lines
# and trigger trading signals while the two config_lines cross each other
# differences between these strategies are the types of
# moving averages.

class SCRSSMA(stg.RuleIterator):
    """ Single cross line strategy with simple moving average

        two parameters:
        - range - range of simple moving average
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SINGLE CROSSLINE - SMA',
                         description='Single moving average strategy that uses simple moving average as the trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        r, = params
        h = hist_data.T
        diff = (sma(h[0], r) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return -1


class SCRSDEMA(stg.RuleIterator):
    """ Single cross line strategy with DEMA

        two parameters:
        - range - range of DEMA
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SINGLE CROSSLINE - DEMA',
                         description='Single moving average strategy that uses DEMA as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        r, = params
        h = hist_data.T
        diff = (dema(h[0], r) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSEMA(stg.RuleIterator):
    """ Single cross line strategy with EMA

        two parameters:
        - range - range of EMA
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SINGLE CROSSLINE - EMA',
                         description='Single moving average strategy that uses EMA as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        r, = params
        h = hist_data.T
        diff = (ema(h[0], r) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSHT(stg.RuleIterator):
    """ Single cross line strategy with ht line

        zero parameters:
        - range - range of ht
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=[],
                         par_bounds_or_enums=[],
                         name='SINGLE CROSSLINE - HT',
                         description='Single moving average strategy that uses HT line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        h = hist_data.T
        diff = (ht(h[0]) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSKAMA(stg.RuleIterator):
    """ Single cross line strategy with KAMA line

        one parameters:
        - range - range of KAMA
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SINGLE CROSSLINE - KAMA',
                         description='Single moving average strategy that uses KAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        r, = params
        h = hist_data.T
        diff = (kama(h[0], r) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSMAMA(stg.RuleIterator):
    """ Single cross line strategy with MAMA line

        two parameters:
        - fastlimit -> fastlimit, float between 0 and 1, not included
        - slowlimit -> slowlimit, float between 0 and 1, not included
    """

    def __init__(self, pars=(0.5, 0.05)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['conti', 'conti'],
                         par_bounds_or_enums=[(0.01, 0.99), (0.01, 0.99)],
                         name='SINGLE CROSSLINE - MAMA',
                         description='Single moving average strategy that uses MAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, s = params
        h = hist_data.T
        diff = (mama(h[0], f, s)[0] - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSFAMA(stg.RuleIterator):
    """ Single cross line strategy with FAMA line

        two parameters:
        - fastlimit -> fastlimit, float between 0 and 1, not included
        - slowlimit -> slowlimit, float between 0 and 1, not included
    """

    def __init__(self, pars=(0.5, 0.05)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['conti', 'conti'],
                         par_bounds_or_enums=[(0.01, 0.99), (0.01, 0.99)],
                         name='SINGLE CROSSLINE - FAMA',
                         description='Single moving average strategy that uses MAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, s = params
        h = hist_data.T
        diff = (mama(h[0], f, s)[1] - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRST3(stg.RuleIterator):
    """ Single cross line strategy with T3 line

        two parameters:
        - timeperiod - timeperiod
        - vfactor = vfactor
    """

    def __init__(self, pars=(12, 0.5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(2, 20), (0, 1)],
                         name='SINGLE CROSSLINE - T3',
                         description='Single moving average strategy that uses T3 line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        p, v = params
        h = hist_data.T
        diff = (t3(h[0], p, v) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSTEMA(stg.RuleIterator):
    """ Single cross line strategy with TEMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(6,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 20)],
                         name='SINGLE CROSSLINE - TEMA',
                         description='Single moving average strategy that uses TEMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        p, = params
        h = hist_data.T
        diff = (tema(h[0], p) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSTRIMA(stg.RuleIterator):
    """ Single cross line strategy with TRIMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 200)],
                         name='SINGLE CROSSLINE - TRIMA',
                         description='Single moving average strategy that uses TRIMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        p, = params
        h = hist_data.T
        diff = (trima(h[0], p) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSWMA(stg.RuleIterator):
    """ Single cross line strategy with WMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 200)],
                         name='SINGLE CROSSLINE - WMA',
                         description='Single moving average strategy that uses MAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        p, = params
        h = hist_data.T
        diff = (wma(h[0], p) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


# Built-in Double-cross-line strategies:
# these strateges are basically adopting same philosaphy:
# they track a long term moving average vs short term MA
# and trigger trading signals while the two config_lines cross
# differences between these strategies are the types of
# moving averages.


class DCRSSMA(stg.RuleIterator):
    """ Double cross line strategy with simple moving average

    two parameters:
    - fast
    - slow
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(3, 250), (3, 250)],
                         name='SINGLE CROSSLINE - SMA',
                         description='Single moving average strategy that uses simple moving average as the trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        l, s = params
        h = hist_data.T
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSDEMA(stg.RuleIterator):
    """ Double cross line strategy with DEMA

        two parameters:
        - range - range of DEMA
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(3, 250), (3, 250)],
                         name='DOUBLE CROSSLINE - DEMA',
                         description='Double moving average strategy that uses DEMA as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        l, s = params
        h = hist_data.T
        diff = (dema(h[0], l) - dema(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSEMA(stg.RuleIterator):
    """ Double cross line strategy with EMA

        two parameters:
        - range - range of EMA
    """

    def __init__(self, pars=(20, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(3, 250), (3, 250)],
                         name='DOUBLE CROSSLINE - EMA',
                         description='Double moving average strategy that uses EMA as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        l, s = params
        h = hist_data.T
        diff = (ema(h[0], l) - ema(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSKAMA(stg.RuleIterator):
    """ Double cross line strategy with KAMA line

        one parameters:
        - range - range of KAMA
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(3, 250), (3, 250)],
                         name='DOUBLE CROSSLINE - KAMA',
                         description='Double moving average strategy that uses KAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        l, s = params
        h = hist_data.T
        diff = (kama(h[0], l) - kama(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSMAMA(stg.RuleIterator):
    """ Double cross line strategy with MAMA line

        two parameters:
        - fastlimit - fastlimit
        - slowlimit = slowlimit
    """

    def __init__(self, pars=(0.15, 0.05, 0.55, 0.25)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['conti', 'conti', 'conti', 'conti'],
                         par_bounds_or_enums=[(0.01, 0.99), (0.01, 0.99), (0.01, 0.99), (0.01, 0.99)],
                         name='DOUBLE CROSSLINE - MAMA',
                         description='Double moving average strategy that uses MAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        lf, ls, sf, ss = params
        h = hist_data.T
        diff = (mama(h[0], lf, ls)[0] - mama(h[0], sf, ss)[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSFAMA(stg.RuleIterator):
    """ Double cross line strategy with FAMA line

        two parameters:
        - fastlimit - fastlimit
        - slowlimit = slowlimit
    """

    def __init__(self, pars=(0.15, 0.05, 0.55, 0.25)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['conti', 'conti', 'conti', 'conti'],
                         par_bounds_or_enums=[(0.01, 0.99), (0.01, 0.99), (0.01, 0.99), (0.01, 0.99)],
                         name='DOUBLE CROSSLINE - FAMA',
                         description='Double moving average strategy that uses FAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        lf, ls, sf, ss = params
        h = hist_data.T
        diff = (mama(h[0], lf, ls)[1] - mama(h[0], sf, ss)[1])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRST3(stg.RuleIterator):
    """ Double cross line strategy with T3 line

        two parameters:
        - timeperiod - timeperiod
        - vfactor = vfactor
    """

    def __init__(self, pars=(20, 0.5, 5, 0.5)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'conti', 'discr', 'conti'],
                         par_bounds_or_enums=[(2, 20), (0, 1), (2, 20), (0, 1)],
                         name='DOUBLE CROSSLINE - T3',
                         description='Double moving average strategy that uses T3 line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        fp, fv, sp, sv = params
        h = hist_data.T
        diff = (t3(h[0], fp, fv) - t3(h[0], sp, sv))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSTEMA(stg.RuleIterator):
    """ Double cross line strategy with TEMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(11, 6)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(2, 20), (2, 20)],
                         name='DOUBLE CROSSLINE - TEMA',
                         description='Double moving average strategy that uses TEMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        fp, sp = params
        h = hist_data.T
        diff = (tema(h[0], fp) - tema(h[0], sp))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSTRIMA(stg.RuleIterator):
    """ Double cross line strategy with TRIMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(3, 200), (3, 200)],
                         name='DOUBLE CROSSLINE - TRIMA',
                         description='Double moving average strategy that uses TRIMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        fp, sp = params
        h = hist_data.T
        diff = (trima(h[0], fp) - trima(h[0], sp))[-1]
        if diff < 0:
            return 1
        else:
            return 0


class DCRSWMA(stg.RuleIterator):
    """ Double cross line strategy with WMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(3, 200), (3, 200)],
                         name='DOUBLE CROSSLINE - WMA',
                         description='Double moving average strategy that uses WMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        fp, sp = params
        h = hist_data.T
        diff = (wma(h[0], fp) - wma(h[0], sp))[-1]
        if diff < 0:
            return 1
        else:
            return 0


# Built-in Sloping strategies:
# these strateges are basically adopting same philosaphy:
# the operation signals or long/short categorizations are
# determined by the slop of price trend config_lines, which are
# generated by different methodologies such as moving
# average, or low-pass filtration


class SLPSMA(stg.RuleIterator):
    """ Double cross line strategy with simple moving average

    """

    def __init__(self, pars=(35,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SLOPE - SMA',
                         description='Smoothed Curve Slope strategy that uses simple moving average as the trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = sma(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPDEMA(stg.RuleIterator):
    """ Curve Slope  strategy with DEMA line

        two parameters:
        - range - range of DEMA
    """

    def __init__(self, pars=(35,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SLOPE - DEMA',
                         description='Smoothed Curve Slope Strategy that uses DEMA as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = dema(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPEMA(stg.RuleIterator):
    """ Curve Slope  strategy with EMA

        two parameters:
        - range - range of EMA
    """

    def __init__(self, pars=(35,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SLOPE - EMA',
                         description='Smoothed Curve Slope Strategy that uses EMA as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = ema(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPHT(stg.RuleIterator):
    """ Curve Slope  strategy with ht line

        zero parameters:
        - range - range of ht
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=[],
                         par_bounds_or_enums=[],
                         name='SLOPE - HT',
                         description='Smoothed Curve Slope Strategy that uses HT line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        h = hist_data.T
        curve = ht(h[0])
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPKAMA(stg.RuleIterator):
    """ Curve Slope  strategy with KAMA line

        one parameters:
        - range - range of KAMA
    """

    def __init__(self, pars=(35,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 250)],
                         name='SLOPE - KAMA',
                         description='Smoothed Curve Slope Strategy that uses KAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = kama(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPMAMA(stg.RuleIterator):
    """ Curve Slope  strategy with MAMA line

        two parameters:
        - fastlimit - fastlimit
        - slowlimit = slowlimit
    """

    def __init__(self, pars=(0.5, 0.05)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['conti', 'conti'],
                         par_bounds_or_enums=[(0.01, 0.99), (0.01, 0.99)],
                         name='SLOPE - MAMA',
                         description='Smoothed Curve Slope Strategy that uses MAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, s = params
        h = hist_data.T
        curve = mama(h[0], f, s)[0]
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPFAMA(stg.RuleIterator):
    """ Curve Slope  strategy with FAMA line

        two parameters:
        - fastlimit - fastlimit
        - slowlimit = slowlimit
    """

    def __init__(self, pars=(0.5, 0.05)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['conti', 'conti'],
                         par_bounds_or_enums=[(0.01, 0.99), (0.01, 0.99)],
                         name='SLOPE - FAMA',
                         description='Smoothed Curve Slope Strategy that uses FAMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, s = params
        h = hist_data.T
        curve = mama(h[0], f, s)[1]
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPT3(stg.RuleIterator):
    """ Curve Slope  strategy with T3 line

        two parameters:
        - timeperiod - timeperiod
        - vfactor = vfactor
    """

    def __init__(self, pars=(12, 0.25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(2, 20), (0, 1)],
                         name='SLOPE - T3',
                         description='Smoothed Curve Slope Strategy that uses T3 line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        p, v = params
        h = hist_data.T
        curve = t3(h[0], p, v)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPTEMA(stg.RuleIterator):
    """ Curve Slope strategy with TEMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(6,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 20)],
                         name='SLOPE - TEMA',
                         description='Smoothed Curve Slope Strategy that uses TEMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = ema(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPTRIMA(stg.RuleIterator):
    """ Curve Slope  strategy with TRIMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(35,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 200)],
                         name='SLOPE - TRIMA',
                         description='Smoothed Curve Slope Strategy that uses TRIMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = trima(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


class SLPWMA(stg.RuleIterator):
    """ Curve Slope  strategy with WMA line

        two parameters:
        - timeperiod - timeperiod
    """

    def __init__(self, pars=(125,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(3, 200)],
                         name='SLOPE - WMA',
                         description='Smoothed Curve Slope Strategy that uses WMA line as the '
                                  'trade line ',
                         data_types='close')

    def _realize(self, hist_data, params):
        f, = params
        h = hist_data.T
        curve = wma(h[0], f)
        slope = curve[-1] - curve[-2]
        if slope > 0:
            return 1
        else:
            return 0


# momentum-based strategies:
# this group of strategies are based on momentum of prices
# the long/short positions or operation signals are generated
# according to the momentum of prices calculated in different
# methods

class ADX(stg.RuleIterator):
    """ADX 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 35)],
                         name='ADX',
                         description='Average Directional Movement Index, determine buy/sell signals according to ADX Indicators',
                         window_length=200,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
            u: number deviation up
            d: number deviation down
            m: ma type
        """
        p, = params
        h = hist_data.T
        res = adx(h[0], h[1], h[2], p)[-1]
        # 策略:
        # 指标比较复杂，需要深入研究一下
        # 指标大于25时属于强趋势。。。未完待续
        if res > 25:
            cat = 1
        elif res < 20:
            cat = -1
        else:
            cat = 0
        return cat


class APO(stg.RuleIterator):
    """APO 策略
    """

    def __init__(self, pars=(12, 26, 0)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 100), (10, 100), (0, 8)],
                         name='APO',
                         description='Absolute Price Oscillator, determine buy/sell signals according to APO Indicators',
                         window_length=200,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
            u: number deviation up
            d: number deviation down
            m: ma type
        """
        f, s, m = params
        h = hist_data.T
        res = apo(h[0], f, s, m)[-1]
        # 策略:
        # 当指标大于0时，输出多头
        # 当指标小于0时，输出空头
        if res > 0:
            cat = 1
        elif res < 0:
            cat = -1
        else:
            cat = 0
        return cat


class AROON(stg.RuleIterator):
    """APOON 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='AROON',
                         description='Aroon, determine buy/sell signals according to AROON Indicators',
                         window_length=200,
                         data_types='high, low')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
            u: number deviation up
            d: number deviation down
            m: ma type
        """
        p, = params
        h = hist_data.T
        ups, dns = aroon(h[0], h[1], p)
        # 策略:
        # 当up在dn的上方时，输出弱多头
        # 当up位于dn下方时，输出弱空头
        # 当up大于70且dn小于30时，输出强多头
        # 当up小于30且dn大于70时，输出强空头
        if ups[-1] > dns[-1]:
            cat = 0.5
        elif ups[-1] > 70 and dns[-1] < 30:
            cat = 1
        elif ups[-1] < dns[-1]:
            cat = -0.5
        elif ups[-1] < 30 and dns[-1] > 70:
            cat = -1
        else:
            cat = 0
        return cat


class AROONOSC(stg.RuleIterator):
    """AROON Oscillator 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='AROON Oscilator',
                         description='Aroon Oscilator, determine buy/sell signals according to AROON Indicators',
                         window_length=200,
                         data_types='high, low')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
        """
        p, = params
        h = hist_data.T
        res = aroonosc(h[0], p)[-1]
        # 策略:
        # 当res大于0时，输出弱多头
        # 当res小于0时，输出弱空头
        # 当res大于50时，输出强多头
        # 当res小于-50时，输出强空头
        if res > 0:
            cat = 0.5
        elif res > 50:
            cat = 1
        elif res < 0:
            cat = -0.5
        elif res < -50:
            cat = -1
        else:
            cat = 0
        return cat


class CCI(stg.RuleIterator):
    """CCI the Commodity Channel Index 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='CCI',
                         description='CCI, determine long/short positions according to CC Indicators',
                         window_length=200,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
        """
        p, = params
        h = hist_data.T
        res = cci(h[0], h[1], h[2], p)[-1]
        # 策略:
        # 当res大于0时输出多头，大于50时输出强多头
        # 当res小于0时输出空头，小于-50时输出强空头
        if res > 0:
            cat = 0.5
        elif res > 50:
            cat = 1
        elif res < 0:
            cat = -0.5
        elif res < -50:
            cat = -1
        else:
            cat = 0
        return cat


class CMO(stg.RuleIterator):
    """CMO Chande Momentum Oscillator 钱德动量振荡器 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='CMO',
                         description='CMO, determine long/short positions according to CMO Indicators',
                         window_length=200,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
        """
        p, = params
        h = hist_data.T
        res = cmo(h[0], p)[-1]
        # 策略:
        # 当res大于0时，输出弱多头
        # 当res小于0时，输出弱空头
        # 当res大于50时，输出强多头
        # 当res小于-50时，输出强空头
        if res > 0:
            cat = 0.5
        elif res > 50:
            cat = 1
        elif res < 0:
            cat = -0.5
        elif res < -50:
            cat = -1
        else:
            cat = 0
        return cat


class MACDEXT(stg.RuleIterator):
    """MACD Extention 策略
    """

    def __init__(self, pars=(12, 0, 26, 0, 9, 0)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr', 'discr', 'discr', 'discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(2, 35), (0, 8), (2, 35), (0, 8), (2, 35), (0, 8)],
                         name='MACD Extention',
                         description='MACD Extention, determine long/short position according to extended MACD Indicators',
                         window_length=200,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            fp: fast periods
            ft: fast ma type
            sp: slow periods
            st: slow ma type
            s: signal periods
            t: signal ma type
        """
        fp, ft, sp, st, p, t = params
        h = hist_data.T
        m, sig, hist = macdext(h[0], fp, ft, sp, st, p, t)[-1]
        # 策略:
        # 当hist>0时输出多头
        # 当hist<0时输出空头
        if hist > 0:
            cat = 1
        else:
            cat = 0
        return cat


class MFI(stg.RuleIterator):
    """MFI money flow index 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='MFI',
                         description='MFI, determine buy/sell signals according to MFI Indicators',
                         window_length=200,
                         data_types='high, low, close, volume')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: period
        """
        p, = params
        h = hist_data.T
        res = mfi(h[0], h[1], h[2], h[3], p)[-1]
        # 策略:
        # 当res小于20时，分批买入
        # 当res大于80时，分批卖出
        if res > 20:
            sig = 0.1
        elif res < 80:
            sig = -0.3
        else:
            sig = 0
        return sig


class DI(stg.RuleIterator):
    """DI index that uses both negtive and positive DI 策略
    """

    def __init__(self, pars=(14, 14)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(1, 100), (1, 100)],
                         name='DI',
                         description='DI, determine long/short positions according to +/- DI Indicators',
                         window_length=200,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            m: periods for negtive DI
            p: periods for positive DI
        """
        m, p, = params
        h = hist_data.T
        ndi = minus_di(h[0], h[1], h[2], m)[-1]
        pdi = plus_di(h[0], h[1], h[2], p)[-1]
        # 策略:
        # 当ndi小于pdi时，输出多头
        # 当ndi大于pdi时，输出空头
        if pdi > ndi:
            cat = 1
        elif ndi < pdi:
            cat = -1
        else:
            cat = 0
        return cat


class DM(stg.RuleIterator):
    """ DM index that uses both negtive and positive DM 策略
    """

    def __init__(self, pars=(14, 14)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(1, 100), (1, 100)],
                         name='DM',
                         description='DM, determine long/short positions according to +/- DM Indicators',
                         window_length=200,
                         data_types='high, low')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            m: periods for negtive DM
            p: periods for positive DM
        """
        m, p, = params
        h = hist_data.T
        ndm = minus_dm(h[0], h[1], m)[-1]
        pdm = plus_dm(h[0], h[1], p)[-1]
        # 策略:
        # 当ndi小于pdi时，输出多头
        # 当ndi大于pdi时，输出空头
        if pdm > ndm:
            cat = 1
        elif ndm < pdm:
            cat = -1
        else:
            cat = 0
        return cat


class MOM(stg.RuleIterator):
    """ Momentum 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(1, 100)],
                         name='MOM',
                         description='MOM, determine long/short positions according to MOM Indicators',
                         window_length=100,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: periods
        """
        p, = params
        h = hist_data.T
        res = mom(h[0], p)[-1]
        # 策略:
        # 当res小于0时，输出空头
        # 当res大于0时，输出多头
        if res > 0:
            cat = 1
        elif res < 0:
            cat = -1
        else:
            cat = 0
        return cat


class PPO(stg.RuleIterator):
    """ PPO 策略
    """

    def __init__(self, pars=(12, 26, 0)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(2, 100), (2, 100), (0, 8)],
                         name='PPO',
                         description='PPO, determine long/short positions according to PPO Indicators',
                         window_length=100,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            fp: fast moving periods
            sp: slow moving periods
            m: ma type
        """
        fp, sp, m = params
        h = hist_data.T
        res = ppo(h[0], fp, sp, m)[-1]
        # 策略:
        # 当res小于0时，输出空头
        # 当res大于0时，输出多头
        if res > 0:
            cat = 1
        elif res < 0:
            cat = -1
        else:
            cat = 0
        return cat


class RSI(stg.RuleIterator):
    """ RSI Relative Strength Index 策略
    """

    def __init__(self, pars=(12,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='RSI',
                         description='RSI, determine long/short positions according to RSI Indicators',
                         window_length=100,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: periods
        """
        p, = params
        h = hist_data.T
        res = rsi(h[0], p)[-1]
        # 策略:
        # 当res小于40时，输出空头
        # 当res大于60时，输出多头
        if res > 60:
            cat = 1
        elif res < 40:
            cat = -1
        else:
            cat = 0
        return cat


class STOCH(stg.RuleIterator):
    """ Stochastic 策略
    """

    def __init__(self, pars=(5, 3, 0, 3, 0)):
        super().__init__(pars=pars,
                         par_count=5,
                         par_types=['discr', 'discr', 'discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(2, 100), (2, 100), (0, 8), (2, 100), (0, 8)],
                         name='Stochastic',
                         description='Stoch, determine buy/sell signals according to Stochastic Indicator',
                         window_length=100,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            fk: periods
            sk: slowk
            skm: slowk ma type
            sd: slow d
            sdm: slow d ma type
        """
        fk, sk, skm, sd, sdm = params
        h = hist_data.T
        k, d = stoch(h[0], h[1], h[2], fk, sk, skm, sd, sdm)
        # 策略:
        # 当k小于20时，逐步买进
        # 当k大于80时，逐步卖出
        # 当k与d背离的时候，同样会产生信号，需要研究
        if k[-1] > 80:
            sig = -0.3
        elif k[-1] < 20:
            sig = 0.1
        else:
            sig = 0
        return sig


class STOCHF(stg.RuleIterator):
    """ Stochastic Fast 策略
    """

    def __init__(self, pars=(5, 3, 0)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(2, 100), (2, 100), (0, 8)],
                         name='Fast Stochastic',
                         description='Fast Stoch, determine buy/sell signals according to Stochastic Indicator',
                         window_length=100,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            fk: periods
            fd: fast d
            fdm: fast d ma type
        """
        fk, fd, fdm = params
        h = hist_data.T
        k, d = stochf(h[0], h[1], h[2], fk, fd, fdm)
        # 策略:
        # 当k小于20时，逐步买进
        # 当k大于80时，逐步卖出
        # 当k与d背离的时候，同样会产生信号，需要研究
        if k[-1] > 80:
            sig = -0.3
        elif k[-1] < 20:
            sig = 0.1
        else:
            sig = 0
        return sig


class STOCHRSI(stg.RuleIterator):
    """ Stochastic RSI 策略
    """

    def __init__(self, pars=(14, 5, 3, 0)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(2, 100), (2, 100), (2, 100), (0, 8)],
                         name='Stochastic RSI',
                         description='Stochaxtic RSI, determine buy/sell signals according to Stochastic RSI Indicator',
                         window_length=100,
                         data_types='close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: periods
            fk: fastk
            sk: slowk
            skm: slowk ma type
            sd: slow d
            sdm: slow d ma type
        """
        p, fk, fd, fdm = params
        h = hist_data.T
        k, d = stochrsi(h[0], p, fk, fd, fdm)
        # 策略:
        # 当k小于0.2时，逐步买进
        # 当k大于0.8时，逐步卖出
        # 当k与d背离的时候，同样会产生信号，需要研究
        if k[-1] > 0.8:
            sig = -0.3
        elif k[-1] < 0.2:
            sig = 0.1
        else:
            sig = 0
        return sig


class ULTOSC(stg.RuleIterator):
    """ Ultimate Oscillator 策略
    """

    def __init__(self, pars=(7, 14, 28)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(1, 100), (1, 100), (1, 100)],
                         name='Ultimate Oscillator',
                         description='Ultimate Oscillator, determine buy/sell signals according to Stochastic Indicator',
                         window_length=100,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p1: time period 1
            p2: time period 2
            p3: time period 3
        """
        p1, p2, p3 = params
        h = hist_data.T
        res = stochf(h[0], h[1], h[2], p1, p2, p3)[-1]
        # 策略:
        # 当res小于30时，逐步买进
        # 当res大于70时，逐步卖出
        if res > 70:
            sig = -0.3
        elif res < 30:
            sig = 0.1
        else:
            sig = 0
        return sig


class WILLR(stg.RuleIterator):
    """ Williams' %R 策略
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='Williams\' R',
                         description='Williams R, determine buy/sell signals according to Williams R',
                         window_length=100,
                         data_types='high, low, close')

    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
        """参数:
        input:
            p: periods
        """
        p, = params
        h = hist_data.T
        res = stochf(h[0], h[1], h[2], p)
        # 策略:
        # 当res小于-80时，逐步买进
        # 当res大于-20时，逐步卖出
        if res > -20:
            sig = -0.3
        elif res < -80:
            sig = 0.1
        else:
            sig = 0
        return sig


# Built-in Simple timing strategies:

class RiconNone(stg.RuleIterator):
    """无风险控制策略，不对任何风险进行控制"""

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='NONE',
                         description='Do not take any risk control activity')

    def _realize(self, hist_data: np.ndarray, params: tuple):
        return np.zeros_like(hist_data.squeeze())


class TimingLong(stg.RuleIterator):
    """简单择时策略，返回整个历史周期上的恒定多头状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='Long',
                         description='Simple Timing strategy, return constant long position on the whole history')

    def _realize(self, hist_data: np.ndarray, params: tuple):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return np.ones_like(hist_data.squeeze())


class TimingShort(stg.RuleIterator):
    """简单择时策略，返回整个历史周期上的恒定空头状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='Short',
                         description='Simple Timing strategy, return constant Short position on the whole history')

    def _realize(self, hist_data, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return -np.ones_like(hist_data.squeeze())


class TimingZero(stg.RuleIterator):
    """简单择时策略，返回整个历史周期上的空仓状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='Zero',
                         description='Simple Timing strategy, return constant Zero position ratio on the whole history')

    def _realize(self, hist_data, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return np.zeros_like(hist_data.squeeze())


class TimingDMA(stg.RuleIterator):
    """DMA择时策略
    生成DMA多空判断：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        3， DMA与股价发生背离时的交叉信号，可信度较高

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars=(12, 26, 9)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         name='DMA',
                         description='Quick DMA strategy, determine long/short position according to differences of '
                                  'moving average prices with simple timing strategy',
                         data_types='close')

    def _realize(self, hist_data, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick dma Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)
        # print('qDMA generated DMA and ama signal:', dma.size, dma, '\n', ama.size, ama)

        cat = np.where(dma > ama, 1, 0)
        return cat


class RiconUrgent(stg.RuleIterator):
    """urgent风控类，继承自Ricon类，重写_realize方法"""

    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号

    def __init__(self, pars=(0, 0)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(1, 40), (-0.5, 0.5)],
                         name='URGENT',
                         description='Generate selling signal when N-day drop rate reaches target')

    def _realize(self, hist_data, params):
        """
        # 根据N日内下跌百分比确定的卖出信号，让N日内下跌百分比达到pct时产生卖出信号

        input =====
            :type hist_data: tuple like (N, pct): type N: int, Type pct: float
                输入参数对，当股价在N天内下跌百分比达到pct时，产生卖出信号
        return ====
            :rtype: object np.ndarray: 包含紧急卖出信号的ndarray
        """
        assert self._pars is not None, 'Parameter of Risk Control-Urgent should be a pair of numbers like (N, ' \
                                       'pct)\nN as days, pct as percent drop '
        assert isinstance(hist_data, np.ndarray), \
            f'Type Error: input historical data should be ndarray, got {type(hist_data)}'
        day, drop = self._pars
        h = hist_data
        diff = (h - np.roll(h, day)) / h
        diff[:day] = h[:day]
        return np.where(diff < drop, -1, 0).squeeze()


# Built-in GeneralStg strategies:

class SelectingAll(stg.GeneralStg):
    """基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配"""

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         stg_name='SIMPLE ',
                         stg_text='GeneralStg all share and distribute weights evenly')

    def _realize(self, hist_data, params):
        # 所有股票全部被选中，投资比例平均分配
        share_count = hist_data.shape[0]
        return [1. / share_count] * share_count


class SelectingNone(stg.GeneralStg):
    """基础选股策略：保持历史股票池中的所有股票都不被选中，投资比例平均分配"""

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         stg_name='NONE ',
                         stg_text='None of the shares will be selected')

    def _realize(self, hist_data, params):
        # 所有股票全部被选中，投资比例平均分配
        share_count = hist_data.shape[0]
        return [0.] * share_count


class SelectingRandom(stg.GeneralStg):
    """基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配"""

    def __init__(self, pars=(0.5,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['conti'],
                         par_bounds_or_enums=[(0, np.inf)],
                         stg_name='RANDOM',
                         stg_text='GeneralStg share Randomly and distribute weights evenly')

    def _realize(self, hist_data, params):
        pct = self.pars[0]
        share_count = hist_data.shape[0]
        if pct < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size=share_count, p=[pct, 1 - pct])
        else:  # pct >= 1 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(share_count, size=(int(pct)), replace=False)
            chosen = np.zeros(share_count)
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum()  # 投资比例平均分配


# Built-in FactorSorter strategies:

class SelectingAvgIndicator(stg.FactorSorter):
    """ 以股票过去一段时间内的财务指标的平均值作为选股因子选股

    """

    def __init__(self, pars=(True, 'even', 'greater', 0, 0, 0.25)):
        super().__init__(pars=pars,
                         par_count=6,
                         par_types=['enum', 'enum', 'enum', 'conti', 'conti', 'conti'],
                         par_bounds_or_enums=[(True, False),
                                              ('even', 'linear', 'proportion'),
                                              ('any', 'greater', 'less', 'between', 'not_between'),
                                              (-np.inf, np.inf),
                                              (-np.inf, np.inf),
                                              (0, 1.)],
                         name='FINANCE',
                         description='GeneralStg share_pool according to financial report EPS indicator',
                         data_freq='d',
                         sample_freq='y',
                         window_length=90,
                         data_types='eps')

    def _realize(self, hist_data, params):
        """ 根据hist_segment中的EPS数据选择一定数量的股票

        """
        factors = np.nanmean(hist_data, axis=1).squeeze()

        return factors


class SelectingNDayLast(stg.FactorSorter):
    """ 以股票过去N天前的量价作为选股指标
        N是策略参数，通过pars设置，选择的股价种类为策略属性，通过data_types设置
        默认的data_types为'close'

    """

    def __init__(self, pars=(2,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 100)],
                         name='N-DAY LAST',
                         description='Select stocks according their previous prices',
                         data_freq='d',
                         sample_freq='m',
                         window_length=100,
                         data_types='close')

    def _realize(self, hist_data, params):
        """ 以股票过去N天前的量价作为选股指标
            N是策略参数，通过pars设置，选择的股价种类为策略属性，通过data_types设置
            默认的data_types为'close'

        """
        n, = self.pars
        factors = hist_data[:, -n-1, 0]

        return factors


class SelectingNDayAvg(stg.FactorSorter):
    """ 根据股票以前n天的平均价格选股
        价格类型可以选open/high/low/close/vol等
        具体的价格类型在data_types属性中设置，默认价格为'close'

        策略参数为n，一个大于2小于150的正整数

    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 150)],
                         name='N-DAY AVG',
                         description='Select stocks by its N day average open price',
                         data_freq='d',
                         sample_freq='M',
                         window_length=150,
                         data_types='close')

    def _realize(self, hist_data, params):
        """ 获取的数据为昨天的开盘价

        """
        n, = self.pars
        n_average = hist_data[:, -n-1:, 0].mean(axis=1)
        factors = n_average

        return factors


class SelectingNDayChange(stg.FactorSorter):
    """ 根据股票以前n天的股价变动幅度作为选股因子
        具体的价格类型在data_types属性中设置，默认价格为'close'

        策略参数为n，一个大于2小于150的正整数

    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['discr'],
                         par_bounds_or_enums=[(2, 150)],
                         name='N-DAY CHANGE',
                         description='Select stocks by its N day price change',
                         data_freq='d',
                         sample_freq='M',
                         window_length=150,
                         data_types='close')

    def _realize(self, hist_data, params):
        """ 获取的数据为昨天的开盘价

        """
        n, = self.pars
        current_price = hist_data[:, -1, 0]
        n_previous = hist_data[:, -n-1, 0]
        factors = current_price - n_previous

        return factors


class SelectingNDayRateChange(stg.FactorSorter):
    """ 根据股票以前n天的股价变动比例作为选股因子
        具体的价格类型在data_types属性中设置，默认价格为'close'

        策略参数为n，一个大于2小于150的正整数

    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_bounds_or_enums=[(2, 150)],
                         name='N-DAY RATE',
                         description='Select stocks by its N day price change',
                         data_freq='d',
                         sample_freq='M',
                         window_length=150,
                         data_types='close')

    def _realize(self, hist_data, params):
        """ 获取的数据为昨天的开盘价

        """
        n, = self.pars
        current_price = hist_data[:, -1, 0]
        n_previous = hist_data[:, -n-1, 0]
        factors = (current_price - n_previous) / n_previous

        return factors


class SelectingNDayVolatility(stg.FactorSorter):
    """ 根据股票以前n天的股价变动幅度作为选股因子

        策略参数为n，一个大于2小于150的正整数

    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_bounds_or_enums=[(2, 150)],
                         name='N-DAY VOL',
                         description='Select stocks by its N day price change',
                         data_freq='d',
                         sample_freq='M',
                         window_length=150,
                         data_types='high,low,close')

    def _realize(self, hist_data, params):
        """ 获取的数据为昨天的开盘价

        """
        n, = self.pars
        factors = atr(hist_data, n)

        return factors


BUILT_IN_STRATEGIES = {'crossline':     TimingCrossline,
                       'macd':          TimingMACD,
                       'dma':           TimingDMA,
                       'trix':          TimingTRIX,
                       'cdl':           TimingCDL,
                       'bband':         TimingBBand,
                       's-bband':       SoftBBand,
                       'sarext':        TimingSAREXT,
                       'ssma':          SCRSSMA,
                       'sdema':         SCRSDEMA,
                       'sema':          SCRSEMA,
                       'sht':           SCRSHT,
                       'skama':         SCRSKAMA,
                       'smama':         SCRSMAMA,
                       'sfama':         SCRSFAMA,
                       'st3':           SCRST3,
                       'stema':         SCRSTEMA,
                       'strima':        SCRSTRIMA,
                       'swma':          SCRSWMA,
                       'dsma':          DCRSSMA,
                       'ddema':         DCRSDEMA,
                       'dema':          DCRSEMA,
                       'dkama':         DCRSKAMA,
                       'dmama':         DCRSMAMA,
                       'dfama':         DCRSFAMA,
                       'dt3':           DCRST3,
                       'dtema':         DCRSTEMA,
                       'dtrima':        DCRSTRIMA,
                       'dwma':          DCRSWMA,
                       'slsma':         SLPSMA,
                       'sldema':        SLPDEMA,
                       'slema':         SLPEMA,
                       'slht':          SLPHT,
                       'slkama':        SLPKAMA,
                       'slmama':        SLPMAMA,
                       'slfama':        SLPFAMA,
                       'slt3':          SLPT3,
                       'sltema':        SLPTEMA,
                       'sltrima':       SLPTRIMA,
                       'slwma':         SLPWMA,
                       'adx':           ADX,
                       'apd':           APO,
                       'aroon':         AROON,
                       'aroonosc':      AROONOSC,
                       'cci':           CCI,
                       'cmo':           CMO,
                       'macdext':       MACDEXT,
                       'mfi':           MFI,
                       'di':            DI,
                       'dm':            DM,
                       'mom':           MOM,
                       'ppo':           PPO,
                       'rsi':           RSI,
                       'stoch':         STOCH,
                       'stochf':        STOCHF,
                       'stochrsi':      STOCHRSI,
                       'ultosc':     ULTOSC,
                       'willr':      WILLR,
                       'ricon_none': RiconNone,
                       'urgent':     RiconUrgent,
                       'long':       TimingLong,
                       'short':      TimingShort,
                       'zero':       TimingZero,
                       'all':        SelectingAll,
                       'none':       SelectingNone,
                       'random':     SelectingRandom,
                       'finance':    SelectingAvgIndicator,
                       'ndaylast':   SelectingNDayLast,
                       'ndayavg':    SelectingNDayAvg,
                       'ndayrate':   SelectingNDayRateChange,
                       'ndaychg':    SelectingNDayChange,
                       'ndayvol':    SelectingNDayVolatility
                       }

AVAILABLE_BUILT_IN_STRATEGIES = BUILT_IN_STRATEGIES.values()