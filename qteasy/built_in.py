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
from qteasy.strategy import RuleIterator, GeneralStg, FactorSorter
# commonly used ta-lib funcs that have a None ta-lib version
from .tafuncs import sma, ema, trix, bbands
from .tafuncs import ht, kama, mama, t3, tema, trima, wma, sarext, adx
from .tafuncs import aroon, aroonosc, cci, cmo, macdext, mfi, minus_di
from .tafuncs import plus_di, minus_dm, plus_dm, mom, ppo, rsi, stoch, stochf
from .tafuncs import stochrsi, ultosc, willr, ad, dema, apo, cdldoji, atr


# Built-in Rolling timing strategies:
def built_in_list(stg_id=None):
    """ 获取内置的交易策略列表, 如果给出stg_id，则显示该策略的详细信息并返回该策略

    Parameters
    ----------
    stg_id: str, optional
        策略ID，如果给出ID且该策略存在，则显示该策略的docstring

    Returns
    -------
    dict: 如果stg_id为None，则返回所有内置策略的字典
    stg_func: 如果stg_id不为None，则返回该策略的函数对象
    None: 如果stg_id不为None，但该策略不存在，则返回None

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.built_in_list()
    {
     'crossline': qteasy.built_in.Crossline,
     'macd': qteasy.built_in.MACD,
     'dma': qteasy.built_in.DMA,
     'trix': qteasy.built_in.TRIX,
     ...
      'ndaychg': qteasy.built_in.SelectingNDayChange,
     'ndayvol': qteasy.built_in.SelectingNDayVolatility
    }

    >>> stg = built_in_list('macd')
    MACD择时策略类，运用MACD均线策略，生成目标仓位百分比
    --------------------
    策略参数：
        s: int, 短周期指数平滑均线计算日期；
        l: int, 长周期指数平滑均线计算日期；
        m: int, MACD中间值DEA的计算周期；
    信号类型：
        PT型：目标仓位百分比
    信号规则：
        计算MACD值：
        1，当MACD值大于0时，设置仓位目标为1
        2，当MACD值小于0时，设置仓位目标为0
    策略属性缺省值：
    默认参数：(12, 26, 9)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(10, 250), (10, 250), (5, 250)]
    策略不支持参考数据，不支持交易数据

    >>> stg
    RULE-ITER(MACD)
    """
    if stg_id is None:
        return BUILT_IN_STRATEGIES
    if isinstance(stg_id, str):
        stg_id = stg_id.lower()
    stg_func = BUILT_IN_STRATEGIES.get(stg_id, None)
    if stg_func is None:
        print(f'Strategy Not found! Stg stg_id: ({stg_id})')
        return None

    print(stg_func.__doc__)
    return stg_func


def built_ins(stg_id=None):
    """ 获取内置的交易策略列表, 如果给出stg_id，则显示该策略的详细信息, 等同于 built_in_list()

    Parameters
    ----------
    stg_id: str, optional
        策略ID，如果给出ID且该策略存在，则显示该策略的docstring

    Returns
    -------
    dict: 如果stg_id为None，则返回所有内置策略的字典
    stg_func: 如果stg_id不为None，则返回该策略的函数对象
    None: 如果stg_id不为None，但该策略不存在，则返回None

    See Also
    --------
    built_in_list()
    """
    return built_in_list(stg_id)


def built_in_strategies(stg_id=None):
    """ 获取内置的交易策略列表, 如果给出stg_id，则显示该策略的详细信息, 等同于 built_in_list()

    Parameters
    ----------
    stg_id: str, optional
        策略ID，如果给出ID且该策略存在，则显示该策略的docstring

    Returns
    -------
    dict: 如果stg_id为None，则返回所有内置策略的字典
    stg_func: 如果stg_id不为None，则返回该策略的函数对象
    None: 如果stg_id不为None，但该策略不存在，则返回None

    See Also
    --------
    built_in_list()
    """
    return built_in_list(stg_id)


def get_built_in_strategy(stg_id):
    """ 使用ID获取交易策略

    Parameters
    ----------
    stg_id: str
        策略ID

    Returns
    -------
    stg: 内置交易策略对象

    Raises
    ------
    TypeError: 如果id不是字符串类型
    ValueError: 如果id不是内置策略ID

    Examples
    --------
    >>> get_built_in_strategy('macd')
    MACD strategy
    """
    if not isinstance(stg_id, str):
        raise TypeError(f'stg_id should be a string, got {type(stg_id)} instead')
    stg_id = stg_id.lower()
    if stg_id not in BUILT_IN_STRATEGIES.keys():
        raise ValueError(f'stg_id ({stg_id}) is not valid, please check your input')

    return BUILT_IN_STRATEGIES[stg_id]()


# All following strategies can be used to create strategies by referring to its strategy ID
# Basic technical analysis based Timing strategies
class Crossline(RuleIterator):
    """crossline择时策略类，利用长短均线的交叉确定多空状态

    策略参数：
        s: int, 短均线计算日期；
        l: int, 长均线计算日期；
        m: float, 均线边界宽度（百分比）；
    信号类型：
        PT型：目标仓位百分比
    信号规则：
        1，当短均线位于长均线上方，且距离大于l*m%时，设置仓位目标为1
        2，当短均线位于长均线下方，且距离大于l*m%时，设置仓位目标为-1
        3，当长短均线之间的距离不大于l*m%时，设置仓位目标为0

    策略属性缺省值：
    默认参数：(35, 120, 0.02)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(10, 250), (10, 250), (0, 1)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars: tuple = (35, 120, 0.02)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'float'],
                         par_range=[(10, 250), (10, 250), (0, 0.1)],
                         name='CROSSLINE',
                         description='Moving average crossline strategy, determine long/short position according '
                                     'to the cross point of long and short term moving average prices ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            s, l, m = self.pars
        else:
            s, l, m = pars
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = h.T
        # 计算长短均线之间的距离
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        m = m * l
        if diff < -m:
            return 1
        elif diff > m:
            return -1
        else:
            return 0


class CDL(RuleIterator):
    """CDL择时策略，在K线图中找到符合要求的cdldoji模式

    策略参数：
        无
    信号类型：
        PS型：百分比交易信号
        VS型：交易数量信号
    信号规则：
        搜索历史数据窗口内出现的cdldoji模式（匹配度0～100之间），加总后/100，计算
        等效cdldoji匹配数量，以匹配数量为交易信号。

    策略属性缺省值：
    默认参数：()
    数据类型：open, high, low, close 开盘，最高，最低，收盘价
    采样频率：天
    窗口长度：100
    参数范围：None
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=None,
                         par_range=None,
                         name='CDL INDICATOR',
                         description='CDL Indicators, determine buy/sell signals according to CDL Indicators',
                         window_length=200,
                         strategy_data_types='open,high,low,close')

    def realize(self, h, r=None, t=None, pars=None):
        h = h.T
        cat = (cdldoji(h[0], h[1], h[2], h[3]).cumsum() // 100)

        return float(cat[-1])


class SoftBBand(RuleIterator):
    """布林带线渐进交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，
        交易信号不是一次性产生的，而是逐步渐进买入和卖出。

    策略参数：
        p: int, 均线周期，用于计算布林带线的均线周期
        u: float，上轨偏移量，单位为标准差的倍数，如2表示上偏移2倍标准差
        d: float，下轨偏移量，单位为标准差的倍数，如2表示下偏移2倍标准差
        m: int，移动均线类型，取值范围0~8，表示9种不同的均线类型：
    信号类型：
        PS型：百分比例交易信号
    信号规则：
        计算BBAND，检查价格是否超过BBAND的上轨或下轨：
        1，当价格大于上轨后，每天产生10%的比例买入交易信号
        2，当价格低于下轨后，每天产生33%的比例卖出交易信号

    策略属性缺省值：
    默认参数：(20, 2, 2, 0)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 100), (0.5, 5), (0.5, 5), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(20, 2, 2, 0)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['int', 'float', 'float', 'int'],
                         par_range=[(2, 100), (0.5, 5), (0.5, 5), (0, 8)],
                         name='Soft Bolinger Band',
                         description='Soft-BBand strategy, determine buy/sell signals according to BBand positions',
                         window_length=200,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, u, d, m = self.pars
        else:
            p, u, d, m = pars
        h = h.T
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


class BBand(RuleIterator):
    """ 布林带线交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，
        在价格上穿或下穿布林带线上下轨时产生交易信号。
        布林带线的均线类型不可选

    策略参数：
        p: int, 均线周期，用于计算布林带线的均线周期
        u: float，上轨偏移量，单位为标准差的倍数，如2表示上偏移2倍标准差
        d: float，下轨偏移量，单位为标准差的倍数，如2表示下偏移2倍标准差
    信号类型：
        PS型：百分比例交易信号
    信号规则：
        计算BBAND，检查价格是否超过BBAND的上轨或下轨：
        1，当价格上穿上轨时，产生全仓买入信号
        2，当价格下穿下轨时，产生全仓卖出信号

    策略属性缺省值：
    默认参数：(20, 2, 2)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 100), (0.5, 5), (0.5, 5)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(20, 2, 2)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'float', 'float'],
                         par_range=[(10, 250), (0.5, 2.5), (0.5, 2.5)],
                         name='BBand',
                         description='BBand strategy, determine long/short position according to Bollinger bands',
                         data_freq='d',
                         strategy_run_freq='d',
                         window_length=270,
                         strategy_data_types=['close'])

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            span, upper, lower = self.pars
        else:
            span, upper, lower = pars
        # 计算指数的指数移动平均价格
        h = h.T
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


# Built-in Single-cross-line strategies:
# these strateges are basically adopting same philosaphy:
# they track the close price vs its moving average config_lines
# and trigger trading signals while the two config_lines cross each other
# differences between these strategies are the types of
# moving averages.

class SCRSSMA(RuleIterator):
    """ 单均线交叉策略——SMA均线(简单移动平均线)：根据股价与SMA均线的相对位置设定持仓比例

    策略参数：
        rng: int, 均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(3, 250)],
                         name='SINGLE CROSSLINE - SMA',
                         description='Single moving average strategy that uses simple moving average as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            rng, = self.pars
        else:
            rng, = pars
        h = h.T
        diff = (sma(h[0], rng) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return -1


class SCRSDEMA(RuleIterator):
    """ 单均线交叉策略——DEMA均线(双重指数平滑移动平均线)：根据股价与DEMA均线的相对位置设定持仓比例

    策略参数：
        rng: int, 均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(3, 250)],
                         name='SINGLE CROSSLINE - DEMA',
                         description='Single moving average strategy that uses DEMA as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            rng, = self.pars
        else:
            rng, = pars
        h = h.T
        diff = (dema(h[0], rng) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSEMA(RuleIterator):
    """ 单均线交叉策略——EMA均线(指数平滑移动均线)：根据股价与EMA均线的相对位置设定持仓比例

    策略参数：
        rng: int, 均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(3, 250)],
                         name='SINGLE CROSSLINE - EMA',
                         description='Single moving average strategy that uses EMA as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            rng, = self.pars
        else:
            rng, = pars
        h = h.T
        diff = (ema(h[0], rng) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSHT(RuleIterator):
    """ 单均线交叉策略——HT(希尔伯特变换瞬时趋势线)：根据股价与HT线的相对位置设定持仓比例

    策略参数：
        None: 计算HT线不需要参数
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于HT线时，设定持仓比例为1
        2，当价格低于HT线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        try:  # if ta-lib is installed
            from .tafuncs import ht
        except Exception as e:  # if ta-lib is not installed, warn user to install ta-lib
            raise NotImplementedError('This strategy requires ta-lib, please install ta-lib first')
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=[],
                         par_range=[],
                         name='SINGLE CROSSLINE - HT',
                         description='Single moving average strategy that uses HT line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        h = h.T
        diff = (ht(h[0]) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSKAMA(RuleIterator):
    """ 单均线交叉策略——KAMA均线(考夫曼自适应移动均线)：根据股价与KAMA均线的相对位置设定持仓比例

    策略参数：
        rng: int, 均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(3, 250)],
                         name='SINGLE CROSSLINE - KAMA',
                         description='Single moving average strategy that uses KAMA line as the '
                                  'trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            rng, = self.pars
        else:
            rng, = pars
        h = h.T
        diff = (kama(h[0], rng) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSMAMA(RuleIterator):
    """ 单均线交叉策略——MAMA均线(MESA自适应移动平均线)：根据股价与MAMA均线的相对位置设定持仓比例

    策略参数：
        f: float between 0 and 1, 快速移动极限
        s: float between 0 and 1, 慢速移动极限
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(0.5, 0.05)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(0.01, 0.99), (0.01, 0.99)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(0.5, 0.05)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['float', 'float'],
                         par_range=[(0.01, 0.99), (0.01, 0.99)],
                         name='SINGLE CROSSLINE - MAMA',
                         description='Single moving average strategy that uses MAMA line as the '
                                     'trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, s = self.pars
        else:
            f, s = pars
        h = h.T
        diff = (mama(h[0], f, s)[0] - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRST3(RuleIterator):
    """ 单均线交叉策略——T3均线(三重指数平滑移动平均线)：根据股价与T3均线的相对位置设定持仓比例

    策略参数：
        p: int 均线计算周期
        v: float v因子，调整因子，取值范围0～1之间
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(12, 0.5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20), (0, 1)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 0.5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'float'],
                         par_range=[(2, 20), (0, 1)],
                         name='SINGLE CROSSLINE - T3',
                         description='Single moving average strategy that uses T3 line as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, v = self.pars
        else:
            p, v = pars
        h = h.T
        diff = (t3(h[0], p, v) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSTEMA(RuleIterator):
    """ 单均线交叉策略——TEMA均线(三重指数平滑移动平均线)：根据股价与TEMA均线的相对位置设定持仓比例

    策略参数：
        p: int 均线计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(6,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(6,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 20)],
                         name='SINGLE CROSSLINE - TEMA',
                         description='Single moving average strategy that uses TEMA line as the '
                                     'trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        diff = (tema(h[0], p) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSTRIMA(RuleIterator):
    """ 单均线交叉策略——TRIMA均线(三重指数平滑移动平均线)：根据股价与TRIMA均线的相对位置设定持仓比例

    策略参数：
        p: int 均线计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 200)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(3, 200)],
                         name='SINGLE CROSSLINE - TRIMA',
                         description='Single moving average strategy that uses TRIMA line as the '
                                     'trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        diff = (trima(h[0], p) - h[0])[-1]
        if diff < 0:
            return 1
        else:
            return 0


class SCRSWMA(RuleIterator):
    """ 单均线交叉策略——WMA均线(加权移动平均线)：根据股价与WMA均线的相对位置设定持仓比例

    策略参数：
        p: int 均线计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        检查当前价格与均线的关系：
        1，当价格高于均线时，设定持仓比例为1
        2，当价格低于均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 200)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(3, 200)],
                         name='SINGLE CROSSLINE - WMA',
                         description='Single moving average strategy that uses MAMA line as the '
                                     'trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
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


class DCRSSMA(RuleIterator):
    """ 双均线交叉策略——SMA均线(简单移动平均线)：
        基于SMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        l: int, 长周期，慢速均线的计算周期
        s: int, 短周期，快速均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (3, 250)],
                         name='SINGLE CROSSLINE - SMA',
                         description='Double moving average strategy that uses simple moving average as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            l, s = self.pars
        else:
            l, s = pars
        h = h.T
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSDEMA(RuleIterator):
    """ 双均线交叉策略——DEMA均线(简单移动平均线)：
        基于DEMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        l: int, 长周期，慢速均线的计算周期
        s: int, 短周期，快速均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (3, 250)],
                         name='DOUBLE CROSSLINE - DEMA',
                         description='Double moving average strategy that uses DEMA as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            l, s = self.pars
        else:
            l, s = pars
        h = h.T
        diff = (dema(h[0], l) - dema(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSEMA(RuleIterator):
    """ 双均线交叉策略——EMA均线(指数平滑移动平均线)：
        基于EMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        l: int, 长周期，慢速均线的计算周期
        s: int, 短周期，快速均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(20, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (3, 250)],
                         name='DOUBLE CROSSLINE - EMA',
                         description='Double moving average strategy that uses EMA as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            l, s = self.pars
        else:
            l, s = pars
        h = h.T
        diff = (ema(h[0], l) - ema(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSKAMA(RuleIterator):
    """ 双均线交叉策略——KAMA均线(考夫曼自适应移动平均线)：
        基于KAMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        l: int, 长周期，慢速均线的计算周期
        s: int, 短周期，快速均线的计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (3, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (3, 250)],
                         name='DOUBLE CROSSLINE - KAMA',
                         description='Double moving average strategy that uses KAMA line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            l, s = self.pars
        else:
            l, s = pars
        h = h.T
        diff = (kama(h[0], l) - kama(h[0], s))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSMAMA(RuleIterator):
    """ 双均线交叉策略——MAMA均线(MESA自适应移动平均线)：
        基于MAMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        lf: float, 长周期快速移动极限，慢速均线的KAMA计算参数
        ls: float, 长周期慢速移动极限，慢速均线的KAMA计算参数
        sf: float, 短周期快速移动极限，快速均线的KAMA计算参数
        ss: float, 短周期慢速移动极限，快速均线的KAMA计算参数
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(0.15, 0.05, 0.55, 0.25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(0.01, 0.99), (0.01, 0.99), (0.01, 0.99), (0.01, 0.99)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(0.15, 0.05, 0.55, 0.25)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['float', 'float', 'float', 'float'],
                         par_range=[(0.01, 0.99), (0.01, 0.99), (0.01, 0.99), (0.01, 0.99)],
                         name='DOUBLE CROSSLINE - MAMA',
                         description='Double moving average strategy that uses MAMA line as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            lf, ls, sf, ss = self.pars
        else:
            lf, ls, sf, ss = pars
        h = h.T
        diff = (mama(h[0], lf, ls)[0] - mama(h[0], sf, ss)[0])[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRST3(RuleIterator):
    """ 双均线交叉策略——T3均线(三重指数平滑移动平均线)：
        基于T3均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        lp: int 长周期参数，用于计算慢均线
        lv: float 长周期v因子，调整因子，取值范围0～1之间，用于计算慢均线
        sp: int 短周期参数，用于计算快均线
        sv: float 短周期v因子，调整因子，取值范围0～1之间，用于计算快均线
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(20, 0.5, 5, 0.5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20), (0, 1), (2, 20), (0, 1)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(20, 0.5, 5, 0.5)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['int', 'float', 'int', 'float'],
                         par_range=[(2, 20), (0, 1), (2, 20), (0, 1)],
                         name='DOUBLE CROSSLINE - T3',
                         description='Double moving average strategy that uses T3 line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            lp, lv, sp, sv = self.pars
        else:
            lp, lv, sp, sv = pars
        h = h.T
        diff = (t3(h[0], lp, lv) - t3(h[0], sp, sv))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSTEMA(RuleIterator):
    """ 双均线交叉策略——TEMA均线(三重指数平滑移动平均线)：
        基于TEMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        lp: int 长周期参数，用于计算慢均线
        sp: int 短周期参数，用于计算快均线
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(11, 6)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(11, 6)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(2, 20), (2, 20)],
                         name='DOUBLE CROSSLINE - TEMA',
                         description='Double moving average strategy that uses TEMA line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            lp, sp = self.pars
        else:
            lp, sp = pars
        h = h.T
        diff = (tema(h[0], lp) - tema(h[0], sp))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSTRIMA(RuleIterator):
    """ 双均线交叉策略——TRIMA均线(三重指数平滑移动平均线)：
        基于TRIMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        lp: int 长周期参数，用于计算慢均线
        sp: int 短周期参数，用于计算快均线
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 200), (3, 200)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 200), (3, 200)],
                         name='DOUBLE CROSSLINE - TRIMA',
                         description='Double moving average strategy that uses TRIMA line as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            lp, sp = self.pars
        else:
            lp, sp = pars
        h = h.T
        diff = (trima(h[0], lp) - trima(h[0], sp))[-1]
        if diff < 0:
            return 1
        else:
            return -1


class DCRSWMA(RuleIterator):
    """ 双均线交叉策略——WMA均线(加权移动平均线)：
        基于WMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例

    策略参数：
        lp: int 长周期参数，用于计算慢均线
        sp: int 短周期参数，用于计算快均线
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        用长短两个周期分别计算慢快两根均线：
        1，当快均线高于慢均线时，设定持仓比例为1
        2，当慢均线高于快均线时，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 25)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 200), (3, 200)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(125, 25)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 200), (3, 200)],
                         name='DOUBLE CROSSLINE - WMA',
                         description='Double moving average strategy that uses WMA line as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            lp, sp = self.pars
        else:
            lp, sp = pars
        h = h.T
        diff = (wma(h[0], lp) - wma(h[0], sp))[-1]
        if diff < 0:
            return 1
        else:
            return -1


# Built-in Sloping strategies:
# these strateges are basically adopting same philosaphy:
# the operation signals or long/short categorizations are
# determined by the slop of price trend config_lines, which are
# generated by different methodologies such as moving
# average, or low-pass filtration
class SLPSMA(RuleIterator):
    """ 均线斜率交易策略——SMA均线(简单移动平均线)：
        基于SMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: int, 均线的计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(35, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(35, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (2, 20)],
                         name='SLOPE - SMA',
                         description='Smoothed Curve Slope strategy that uses simple moving average as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = sma(h[0], f)
        # TODO 取N个最近的curve点进行线性回归
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPDEMA(RuleIterator):
    """ 均线斜率交易策略——DEMA均线(双重指数平滑移动平均线)：
        基于DEMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: int, 均线的计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(35, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(35, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (2, 20)],
                         name='SLOPE - DEMA',
                         description='Smoothed Curve Slope Strategy that uses DEMA as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = dema(h[0], f)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPEMA(RuleIterator):
    """ 均线斜率交易策略——EMA均线(指数平滑移动平均线)：
        基于EMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: int, 均线的计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(35, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(35, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (2, 20)],
                         name='SLOPE - EMA',
                         description='Smoothed Curve Slope Strategy that uses EMA as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = ema(h[0], f)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPHT(RuleIterator):
    """ 均线斜率交易策略——HT均线(希尔伯特变换——瞬时趋势线线)：
        基于HT计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(5,)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(5, )):
        try:  # if ta-lib is installed
            from .tafuncs import ht
        except Exception as e:  # if ta-lib is not installed, warn user to install ta-lib
            raise NotImplementedError('This strategy requires ta-lib, please install ta-lib first')
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 20)],
                         name='SLOPE - HT',
                         description='Smoothed Curve Slope Strategy that uses HT line as the '
                                     'trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n = self.pars
        else:
            n = pars
        h = h.T
        curve = ht(h[0])
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPKAMA(RuleIterator):
    """ 均线斜率交易策略——KAMA均线(考夫曼自适应移动平均线)：
        基于KAMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: int, 均线的计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(35, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 250), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(35, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 250), (2, 20)],
                         name='SLOPE - KAMA',
                         description='Smoothed Curve Slope Strategy that uses KAMA line as the '
                                     'trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = kama(h[0], f)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPMAMA(RuleIterator):
    """ 均线斜率交易策略——MAMA均线(MESA自适应移动平均线)：
        基于MAMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: float, 高速移动极限值
        s: float, 低速移动极限值
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(0.5, 0.05, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(0.01, 0.99), (0.01, 0.99), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(0.5, 0.05, 5)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['float', 'float', 'int'],
                         par_range=[(0.01, 0.99), (0.01, 0.99), (2, 20)],
                         name='SLOPE - MAMA',
                         description='Smoothed Curve Slope Strategy that uses MAMA line as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, s, n = self.pars
        else:
            f, s, n = pars
        h = h.T
        curve = mama(h[0], f, s)[0]
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPT3(RuleIterator):
    """ 均线斜率交易策略——T3均线(三重指数平滑移动平均线)：
        基于T3计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        p: int 均线计算周期
        v: float v因子，调整因子，取值范围0～1之间
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(12, 0.25, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20), (0, 1), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 0.25, 5)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'float', 'int'],
                         par_range=[(2, 20), (0, 1), (2, 20)],
                         name='SLOPE - T3',
                         description='Smoothed Curve Slope Strategy that uses T3 line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, v, n = self.pars
        else:
            p, v, n = pars
        h = h.T
        curve = t3(h[0], p, v)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPTEMA(RuleIterator):
    """ 均线斜率交易策略——TEMA均线(三重指数平滑移动平均线)：
        基于TEMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        p: int 均线计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(6, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 20), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(6, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(2, 20), (2, 20)],
                         name='SLOPE - TEMA',
                         description='Smoothed Curve Slope Strategy that uses TEMA line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = ema(h[0], f)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPTRIMA(RuleIterator):
    """ 均线斜率交易策略——TRIMA均线(三重指数平滑移动平均线)：
        基于TRIMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: int 均线计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(35, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 200), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(35, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 200), (2, 20)],
                         name='SLOPE - TRIMA',
                         description='Smoothed Curve Slope Strategy that uses TRIMA line as the trade line',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = trima(h[0], f)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


class SLPWMA(RuleIterator):
    """ 均线斜率交易策略——WMA均线(加权移动平均线)：
        基于WMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标
        （当均线斜率为正时，表示价格趋势向上，提高持仓比例，当均线斜率为负时，表示趋势
        向下，设定持仓比例为负一或零）

    策略参数：
        f: int, 均线计算周期
        N: int, 估算斜率使用的数据点数量
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算价格的移动均线，并且计算均线的当前斜率slope
        slope使用最近的N个移动均线数据点通过线性回归得到：
        1，当slope斜率大于零时，判断趋势向上，设定持仓比例为1
        2，当slope斜率小于零时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(125, 5)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(3, 200), (2, 20)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(125, 5)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(3, 200), (2, 20)],
                         name='SLOPE - WMA',
                         description='Smoothed Curve Slope Strategy that uses WMA line as the trade line ',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, n = self.pars
        else:
            f, n = pars
        h = h.T
        curve = wma(h[0], f)
        slope = curve[-1] - curve[-n]
        if slope > 0:
            return 1
        else:
            return -1


# momentum-based strategies:
# this group of strategies are based on momentum of prices
# the long/short positions or operation signals are generated
# according to the momentum of prices calculated in different
# methods
class SAREXT(RuleIterator):
    """扩展抛物线SAR策略，当指标大于0时发出买入信号，当指标小于0时发出卖出信号

    策略参数：
        a: int, Parabolic SAR参数：加速度
        m: float, maximum最大值
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        计算Parabolic SAR：
        1，当Parabolic SAR大于0时，输出多头
        2，当Parabolic SAR小于0时，输出空头

    策略属性缺省值：
    默认参数：(0, 3)
    数据类型：high, low最高价和最低价，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(-100, 100), (0, 5)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(0, 3)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'float'],
                         par_range=[(-100, 100), (0, 5)],
                         name='Parabolic SAREXT',
                         description='Parabolic SAR Extended Strategy, determine buy/sell signals by Parabolic SAR',
                         window_length=200,
                         strategy_data_types='high, low')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            a, m = self.pars
        else:
            a, m = pars
        h = h.T
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


class MACD(RuleIterator):
    """MACD择时策略类，运用MACD均线策略，生成目标仓位百分比

    策略参数：
        s: int, 短周期指数平滑均线计算日期；
        l: int, 长周期指数平滑均线计算日期；
        m: int, MACD中间值DEA的计算周期；
    信号类型：
        PT型：目标仓位百分比
    信号规则：
        计算MACD值：
        1，当MACD值大于0时，设置仓位目标为1
        2，当MACD值小于0时，设置仓位目标为0

    策略属性缺省值：
    默认参数：(12, 26, 9)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(10, 250), (10, 250), (5, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars: tuple = (12, 26, 9)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(10, 250), (10, 250), (5, 250)],
                         name='MACD',
                         description='MACD strategy, determine long/short position according to differences of '
                                     'exponential weighted moving average prices',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            s, l, m = self.pars
        else:
            s, l, m = pars
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = h.T

        # 计算指数的指数移动平均价格
        diff = ema(h[0], s) - ema(h[0], l)
        dea = ema(diff, m)
        _macd = 2 * (diff - dea)
        cat = 1 if _macd[-1] > 0 else 0
        return cat


class TRIX(RuleIterator):
    """TRIX择时策略，使用股票价格的三重平滑指数移动平均价格进行多空判断

    策略参数：
        s: int, 均线参数，单位为日，用于计算周期为S的三重平滑指数移动平均线TRIX
        m: int, 平滑均线参数，用于计算TRIX的M日简单移动平均线
    信号类型：
        PT型：目标仓位百分比
    信号规则：
        计算价格的三重平滑指数移动平均价TRIX，再计算M日TRIX的移动平均：
        1， TRIX位于MATRIX上方时，设置仓位目标为1
        2， TRIX位于MATRIX下方时，设置仓位目标位-1

    策略属性缺省值：
    默认参数：(12, 12)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 50), (3, 150)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 12)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(2, 50), (3, 150)],
                         name='TRIX',
                         description='TRIX strategy, determine long/short position according to triple exponential '
                                     'weighted moving average prices',
                         data_freq='d',
                         strategy_run_freq='d',
                         window_length=270,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            s, m = self.pars
        else:
            s, m = pars
        h = h.T
        trx = trix(h[0], s) * 100
        matrix = sma(trx, m)
        if trx[-1] > matrix[-1]:
            return 1
        else:
            return -1


class ADX(RuleIterator):
    """ ADX指标（平均定向运动指数）选股策略：
        基于ADX指标判断当前趋势的强度，从而根据趋势强度产生交易信号

    策略参数：
        p: int, ADX计算时间周期，取值范围2～35
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算ADX趋势强度：
        1, 当ADX大于25时，判断趋势向上，设定持仓比例为1
        2, 当ADX介于20到25之间时，判断为中性趋势，设定持仓比例为0
        3, 当ADX小于20时，判断趋势向下，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high, low, close 最高价，最低价，收盘价，多数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(2, 35)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 35)],
                         name='ADX',
                         description='Average Directional Movement Index, determine buy/sell signals by ADX Indicator',
                         window_length=200,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        res = adx(h[0], h[1], h[2], p)[-1]
        # TODO 策略:
        #  指标比较复杂，需要深入研究一下
        #  指标大于25时属于强趋势。。。未完待续
        if res > 25:
            cat = 1.
        elif res < 20:
            cat = -1.
        else:
            cat = 0.
        return cat


class APO(RuleIterator):
    """ APO指标（绝对价格震荡指标）选股策略：
        APO指标通过两条均线的相对关系生成，
        基于APO指标判断当前股价变动的牛熊趋势，从而根据趋势产生交易信号

    策略参数：
        f: int, 快速均线周期
        s: int, 慢速均线周期
        m: int, 移动均线类型，取值范围0～8
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算APO趋势：
        1, 当APO大于0时，判断为牛市趋势，设定持仓比例为1
        2, 当ADX小于0时，判断为熊市趋势，设定持仓比例为-1

    策略属性缺省值：
    默认参数：(12, 26, 0)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(10, 100), (10, 100), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 26, 0)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(10, 100), (10, 100), (0, 8)],
                         name='APO',
                         description='Absolute Price Oscillator, determine buy/sell signals according to APO Indicators',
                         window_length=200,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, s, m = self.pars
        else:
            f, s, m = pars
        h = h.T
        res = apo(h[0], f, s, m)[-1]
        # 策略:
        # 当指标大于0时，输出多头
        # 当指标小于0时，输出空头
        if res > 0:
            cat = 1.
        elif res < 0:
            cat = -1.
        else:
            cat = 0.
        return cat


class AROON(RuleIterator):
    """ AROON指标选股策略：
        AROON指标被用于判断当前股价处于趋势区间还是僵持区间，通过计算AROON指标
        策略可以根据趋势的强弱程度输出强多/空头和弱多/空头

    策略参数：
        p: int, 趋势判断周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算AROON UP / DOWN两条趋势线，并生成持仓比例信号：
        1, 当UP在DOWN的上方时，输出弱多头
        2, 当UP位于DOWN下方时，输出弱空头
        3, 当UP大于70且DOWN小于30时，输出强多头
        4, 当UP小于30且DOWN大于70时，输出强空头

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high, low 最高价，最低价，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 100)],
                         name='AROON',
                         description='Aroon, determine buy/sell signals according to AROON Indicators',
                         window_length=200,
                         strategy_data_types='high, low')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        ups, dns = aroon(h[0], h[1], p)

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


class AROONOSC(RuleIterator):
    """ AROON Oscillator (AROON震荡指标) 选股策略：
        AROONOSC指标基于AROON指标计算，用于判断当前价格变动的趋势以及趋势强度
        当AROONOSC大于0时表示价格趋势向上，反之趋势向下，绝对值大于50时表示强烈的趋势

    策略参数：
        p: int, 趋势判断周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算AROONOSC，并生成持仓比例信号：
        1, 当AROONOSC大于0时，输出弱多头
        2, 当AROONOSC小于0时，输出弱空头
        3, 当AROONOSC大于50时，输出强多头
        4, 当AROONOSC小于-50时，输出强空头

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high, low 最高价，最低价，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 100)],
                         name='AROON Oscillator',
                         description='Aroon Oscillator, determine buy/sell signals according to AROON Indicators',
                         window_length=200,
                         strategy_data_types='high, low')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        res = aroonosc(h[0], p)[-1]

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


class CCI(RuleIterator):
    """ CCI (Commodity Channel Index商品渠道指数) 选股策略：
        CCI商品渠道指数被用来判断当前股价位于超卖还是超买区间，本策略使用这个指标
        生成投资仓位目标

    策略参数：
        p: int, 趋势判断周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算CCI，并生成持仓比例信号：
        1, 当CCI大于0时，输出弱多头
        2, 当CCI小于0时，输出弱空头
        3, 当CCI大于50时，输出强多头
        4, 当CCI小于-50时，输出强空头

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high, low, close 最高价，最低，收盘价，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 100)],
                         name='CCI',
                         description='CCI, determine long/short positions according to CC Indicators',
                         window_length=200,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        res = cci(h[0], h[1], h[2], p)[-1]

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


class CMO(RuleIterator):
    """ CMO (Chande Momentum Oscillator 钱德动量振荡器) 选股策略：
        CMO 是一个在-100到100之间波动的动量指标，它被用来判断当前股价位于
        超卖还是超买区间，本策略使用这个指标生成投资仓位目标

    策略参数：
        p: int, 动量计算周期
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算CMO，并生成持仓比例信号：
        1, 当CMO大于0时，输出弱多头
        2, 当CMO小于0时，输出弱空头
        3, 当CMO大于50时，输出强多头
        4, 当CMO小于-50时，输出强空头

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high, low, close 最高价，最低，收盘价，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 100)],
                         name='CMO',
                         description='CMO, determine long/short positions according to CMO Indicators',
                         window_length=200,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        res = cmo(h[0], p)[-1]

        if 50 > res > 0:
            cat = 0.5
        elif res > 50:
            cat = 1
        elif -50 < res < 0:
            cat = -0.5
        elif res < -50:
            cat = -1
        else:
            cat = 0
        return cat


class MACDEXT(RuleIterator):
    """ MACDEXT (Extendec MACD 扩展MACD指数) 选股策略：
        本策略使用MACD指标生成持仓目标，但是与标准的MACD不同，MACDEXT的快、慢、及信号均线的类型均可选

    策略参数：
        fp: int, 快速均线计算周期
        ft: int, 快速均线类型，取值范围0～8
        sp: int, 慢速均线计算周期
        st: int, 慢速均线类型，取值范围0～8
        s:  int, MACD信号线计算周期
        t:  int, MACD信号线类型，取值范围0～8
    信号类型：
        PT型：仓位百分比目标信号
    信号规则：
        按照规则计算MACD，根据MACD的H线生成持仓比例信号：
        1, 当hist>0时输出多头
        2, 当hist<0时输出空头

    策略属性缺省值：
    默认参数：(12, 0, 26, 0, 9, 0)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 35), (0, 8), (2, 35), (0, 8), (2, 35), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 0, 26, 0, 9, 0)):
        super().__init__(pars=pars,
                         par_count=6,
                         par_types=['int', 'int', 'int', 'int', 'int', 'int'],
                         par_range=[(2, 35), (0, 8), (2, 35), (0, 8), (2, 35), (0, 8)],
                         name='MACD Extension',
                         description='MACD Extension, determine long/short position according to extended MACD',
                         window_length=200,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            fp, ft, sp, st, p, t = self.pars
        else:
            fp, ft, sp, st, p, t = pars
        h = h.T
        m, sig, hist = macdext(h[0], fp, ft, sp, st, p, t)[-1]

        if m > 0:
            cat = 1
        else:
            cat = -1
        return cat


class MFI(RuleIterator):
    """ MFI (Money Flow Index 货币流向指数) 交易策略：
        MFI指数用于判断股价属于超买还是超卖状态，本策略使用MFI指标生成交易信号

    策略参数：
        p:  int, MFI信号计算周期
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        按照规则计算MFI，根据MFI的值生成比例交易信号：
        1, 当MFI>20时，持续不断产生10%买入交易信号
        2, 当MFI>80时，持续不断产生30%卖出交易信号，持续卖出持仓股票

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high, low, close, volume 最高价，最低，收盘，交易量，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(2, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 100)],
                         name='MFI',
                         description='MFI, determine buy/sell signals according to MFI Indicators',
                         window_length=200,
                         strategy_data_types='high, low, close, volume')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        res = mfi(h[0], h[1], h[2], h[3], p)[-1]

        if res < 20:
            sig = 0.1
        elif res > 80:
            sig = -0.3
        else:
            sig = 0
        return sig


class DI(RuleIterator):
    """ DI (Directory Indicator 方向指标) 交易策略：
        DI 指标包含负方向指标与正方向指标，它们分别表示价格上行和下行的趋势强度，本策略使用±DI指标生成交易信号

    策略参数：
        n:  int, 负DI信号计算周期
        p:  int, 正DI信号计算周期
    信号类型：
        PT型：百分比持仓目标信号
    信号规则：
        按照规则计算正负DI，根据DI的值生成持仓目标信号：
        1, 当+DI > -DI时，设置持仓目标为1
        2, 当+DI < -DI时，设置持仓目标为-1

    策略属性缺省值：
    默认参数：(14, 14)
    数据类型：high, low, close 最高价，最低，收盘，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(1, 100), (1, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14, 14)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(1, 100), (1, 100)],
                         name='DI',
                         description='DI, determine long/short positions according to +/- DI Indicators',
                         window_length=200,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, p, = self.pars
        else:
            n, p, = pars
        h = h.T
        ndi = minus_di(h[0], h[1], h[2], n)[-1]
        pdi = plus_di(h[0], h[1], h[2], p)[-1]

        if pdi > ndi:
            cat = 1
        elif pdi < ndi:
            cat = -1
        else:
            cat = 0
        return cat


class DM(RuleIterator):
    """ DM (Directional Movement 方向运动指标) 交易策略：
        DM 指标包含负方向运动指标(Negative Directional Movement)与正方向运动指标(Positive Directional Movement)，
        它们分别表示价格上行和下行的趋势，本策略使用±DM指标生成交易信号

    策略参数：
        n:  int, 负DM信号计算周期
        p:  int, 正DM信号计算周期
    信号类型：
        PT型：百分比持仓目标信号
    信号规则：
        按照规则计算正负DM，根据DM的值生成持仓目标信号：
        1, 当+DM > -DM时，设置持仓目标为1
        2, 当+DM < -DM时，设置持仓目标为-1
        3, 其余情况设置持仓目标为0

    策略属性缺省值：
    默认参数：(14, 14)
    数据类型：high, low 最高价，最低，多数据输入
    采样频率：天
    窗口长度：200
    参数范围：[(1, 100), (1, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14, 14)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(1, 100), (1, 100)],
                         name='DM',
                         description='DM, determine long/short positions according to +/- DM Indicators',
                         window_length=200,
                         strategy_data_types='high, low')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, p, = self.pars
        else:
            n, p, = pars
        h = h.T
        ndm = minus_dm(h[0], h[1], n)[-1]
        pdm = plus_dm(h[0], h[1], p)[-1]

        if pdm > ndm:
            cat = 1
        elif pdm < ndm:
            cat = -1
        else:
            cat = 0
        return cat


class MOM(RuleIterator):
    """ MOM (momentum indicator 动量指标) 交易策略：
        MOM 指标可以用于识别价格的上行或下行趋势的强度，当前价格高于N日前价格时，MOM为正，反之为负。

    策略参数：
        n:  int, MOM信号计算周期
    信号类型：
        PT型：百分比持仓目标信号
    信号规则：
        按照规则计算MOM，根据MOM的值生成持仓目标信号：
        1, 当MOM > 0时，设置持仓目标为1
        2, 当MOM < 0时，设置持仓目标为-1
        3, 其余情况设置持仓目标为0

    策略属性缺省值：
    默认参数：(14, )
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(1, 100)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(1, 100)],
                         name='MOM',
                         description='MOM, determine long/short positions according to MOM Indicators',
                         window_length=100,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, = self.pars
        else:
            p, = pars
        h = h.T
        res = mom(h[0], p)[-1]

        if res > 0:
            cat = 1
        elif res < 0:
            cat = -1
        else:
            cat = 0
        return cat


class PPO(RuleIterator):
    """ PPO (Percentage Price Oscillator 百分比价格振荡器) 交易策略：
        PPO 指标表示快慢两根移动均线之间的百分比差值，用于判断价格的变化趋势。长短均线的计算周期和
        均线类型均为策略参数。

    策略参数：
        fp: int, 快速均线计算周期
        sp: int, 慢速均线计算周期
        m: int, 移动均线类型（取值范围0～8）
    信号类型：
        PT型：百分比持仓目标信号
    信号规则：
        按照规则计算PPO，根据PPO的值生成持仓目标信号：
        1, 当PPO > 0时，设置持仓目标为1
        2, 当PPO < 0时，设置持仓目标为-1
        3, 其余情况设置持仓目标为0

    策略属性缺省值：
    默认参数：(12, 26, 0)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(2, 100), (20, 200), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 26, 0)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(2, 100), (20, 200), (0, 8)],
                         name='PPO',
                         description='PPO, determine long/short positions according to PPO Indicators',
                         window_length=100,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            fp, sp, m = self.pars
        else:
            fp, sp, m = pars
        h = h.T
        res = ppo(h[0], fp, sp, m)[-1]

        if res > 0:
            cat = 1
        elif res < 0:
            cat = -1
        else:
            cat = 0
        return cat


class RSI(RuleIterator):
    """ RSI (Relative Strength Index 相对强度指数) 交易策略：
        RSI 指标度量最近价格变化的幅度，从而判断目前股票属于超卖还是超买状态，并据此判断变化趋势。RSI指标总是在0到100之间
        震荡，是一条震荡曲线。

    策略参数：
        p: int, RSI计算周期
        ulim: int, 触发多头仓位的最低限
        llim: int, 触发空头仓位的最高限
    信号类型：
        PT型：百分比持仓目标信号
    信号规则：
        按照规则计算RSI，根据RSI的值与ulim/llim的关系生成持仓目标信号：
        1, 当RSI > ulim时，设置持仓目标为1
        2, 当RSI < llim时，设置持仓目标为-1
        3, 其余情况设置持仓目标为0

    策略属性缺省值：
    默认参数：(12, 70, 30)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(2, 100), (50, 100), (0, 50)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 70, 30)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(2, 100), (50, 100), (0, 50)],
                         name='RSI',
                         description='RSI, determine long/short positions according to RSI Indicators',
                         window_length=100,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, ulim, llim = self.pars
        else:
            p, ulim, llim = pars
        h = h.T
        res = rsi(h[0], p)[-1]

        if res > ulim:
            cat = 1
        elif res < llim:
            cat = -1
        else:
            cat = 0
        return cat


class STOCH(RuleIterator):
    """ STOCH (Stochastic Indicator 随机指数) 交易策略：
        STOCH 指标度量价格变化的动量，并且动量的大小判断价格趋势，并生成比例买卖交易信号。

    策略参数：
        fk: int, 快速均线计算周期
        sk: int, 慢速K均线计算周期
        skm: int, 慢速K均线类型，取值范围0～8
        sd: int, 慢速D均线计算周期
        sdm: int, 慢速D均线类型，取值范围0～8
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        按照规则计算k值和d值，根据k值生成比例买卖交易信号：
        1, 当k > 80时，产生逐步卖出信号，每周期卖出持有份额的30%
        2, 当k < 20时，产生逐步买入信号，每周期买入总投资额的10%
        3, 当k和d发生背离的时候，也会产生信号（未来改进）

    策略属性缺省值：
    默认参数：(5, 3, 0, 3, 0)
    数据类型：high, low, close 最高价，最低价，收盘价，多数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(2, 100), (2, 100), (0, 8), (2, 100), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(5, 3, 0, 3, 0)):
        super().__init__(pars=pars,
                         par_count=5,
                         par_types=['int', 'int', 'int', 'int', 'int'],
                         par_range=[(2, 100), (2, 100), (0, 8), (2, 100), (0, 8)],
                         name='Stochastic',
                         description='Stochastic, determine buy/sell signals according to Stochastic Indicator',
                         window_length=100,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            fk, sk, skm, sd, sdm = self.pars
        else:
            fk, sk, skm, sd, sdm = pars
        h = h.T
        k, d = stoch(h[0], h[1], h[2], fk, sk, skm, sd, sdm)

        if k[-1] > 80:
            sig = -0.3
        elif k[-1] < 20:
            sig = 0.1
        else:
            sig = 0
        return sig


class STOCHF(RuleIterator):
    """ STOCHF (Stochastic Fast Indicator 快速随机指标) 交易策略：
        STOCHF 指标度量价格变化的动量，与STOCH策略类似，使用快速随机指标判断价格趋势，并生成比例买卖交易信号。

    策略参数：
        fk: int, 快速K均线计算周期
        fd: int, 快速D均线计算周期
        fdm: int, 快速D均线类型，取值范围0～8
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        按照规则计算k值和d值，根据k值生成比例买卖交易信号：
        1, 当k > 80时，产生逐步卖出信号，每周期卖出持有份额的30%
        2, 当k < 20时，产生逐步买入信号，每周期买入总投资额的10%
        3, 当k和d发生背离的时候，也会产生信号（未来改进）

    策略属性缺省值：
    默认参数：(5, 3, 0)
    数据类型：high, low, close 最高价，最低价，收盘价，多数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(2, 100), (2, 100), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(5, 3, 0)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(2, 100), (2, 100), (0, 8)],
                         name='Fast Stochastic',
                         description='Fast Stoch, determine buy/sell signals according to Stochastic Indicator',
                         window_length=100,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            fk, fd, fdm = self.pars
        else:
            fk, fd, fdm = pars
        h = h.T
        k, d = stochf(h[0], h[1], h[2], fk, fd, fdm)

        if k[-1] > 80:
            sig = -0.3
        elif k[-1] < 20:
            sig = 0.1
        else:
            sig = 0
        return sig


class STOCHRSI(RuleIterator):
    """ STOCHRSI (Stochastic Relative Strength Index 随机相对强弱指标) 交易策略：
        STOCHRSI 指标度量价格变化的动量，该指标在0～1之间波动，表示相对的价格趋势强弱程度，并生成比例买卖交易信号。

    策略参数：
        p: int, 计算周期
        fk: int, 快速K均线计算周期
        fd: int, 快速D均线计算周期
        fdm: int, 快速D均线类型，取值范围0～8
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        按照规则计算k值和d值，根据k值生成比例买卖交易信号：
        1, 当k > 0.8时，产生逐步卖出信号，每周期卖出持有份额的30%
        2, 当k < 0.2时，产生逐步买入信号，每周期买入总投资额的10%
        3, 当k和d发生背离的时候，也会产生信号（未来改进）

    策略属性缺省值：
    默认参数：(14, 5, 3, 0)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(2, 100), (2, 100), (2, 100), (0, 8)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14, 5, 3, 0)):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['int', 'int', 'int', 'int'],
                         par_range=[(2, 100), (2, 100), (2, 100), (0, 8)],
                         name='Stochastic RSI',
                         description='Stochastic RSI, determine buy/sell signals according to Stochastic RSI Indicator',
                         window_length=100,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, fk, fd, fdm = self.pars
        else:
            p, fk, fd, fdm = pars
        h = h.T
        k, d = stochrsi(h[0], p, fk, fd, fdm)

        if k[-1] > 0.8:
            sig = -0.3
        elif k[-1] < 0.2:
            sig = 0.1
        else:
            sig = 0
        return sig


class ULTOSC(RuleIterator):
    """ ULTOSC (Ultimate Oscillator Indicator 终极振荡器指标) 交易策略：
        ULTOSC 指标通过三个不同的时间跨度计算价格动量，并根据多种不同动量之间的偏离值生成交易信号。

    策略参数：
        p1: int, 动量计算周期 1
        p2: int, 动量计算周期 2
        p3: int, 动量计算周期 3
        u:  int, 卖出信号阈值
        l:  int, 买入信号阈值
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        计算ULTOSC指标，并根据指标的大小生成交易信号：
        1, 当ULTOSC > u时，产生逐步卖出信号，每周期卖出持有份额的30%
        2, 当ULTOSC < l时，产生逐步买入信号，每周期买入总投资额的10%

    策略属性缺省值：
    默认参数：(7, 14, 28, 70, 30)
    数据类型：high, low, close 最高价，最低价，收盘价，多数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(1, 100), (1, 100), (1, 100), (70, 99), (1, 30)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(7, 14, 28, 70, 30)):
        super().__init__(pars=pars,
                         par_count=5,
                         par_types=['int', 'int', 'int', 'int', 'int'],
                         par_range=[(1, 100), (1, 100), (1, 100), (70, 99), (1, 30)],
                         name='Ultimate Oscillator',
                         description='Ultimate Oscillator, determine buy/sell signals according to multiple momentum',
                         window_length=100,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p1, p2, p3, u, l = self.pars
        else:
            p1, p2, p3, u, l = pars
        h = h.T
        res = ultosc(h[0], h[1], h[2], p1, p2, p3)[-1]

        if res > u:
            sig = -0.3
        elif res < l:
            sig = 0.1
        else:
            sig = 0
        return sig


class WILLR(RuleIterator):
    """ WILLR (William's %R 威廉姆斯百分比) 交易策略：
        WILLR 指标被用于计算股价当前处于超买还是超卖区间，并用于生成交易信号

    策略参数：
        p:  int, 动量计算周期
        u:  int, 卖出信号阈值
        l:  int, 买入信号阈值
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        计算WILLR指标，并根据指标的大小生成交易信号：
        1, 当WILLR > -l时，产生逐步卖出信号，每周期卖出持有份额的30%
        2, 当WILLR < -u时，产生逐步买入信号，每周期买入总投资额的10%

    策略属性缺省值：
    默认参数：(14, 80, 20)
    数据类型：high, low, close 最高价，最低价，收盘价，多数据输入
    采样频率：天
    窗口长度：100
    参数范围：[(2, 100), (70, 99), (1, 30)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14, 80, 20)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(2, 100), (70, 99), (1, 30)],
                         name='Williams\' R',
                         description='Williams R, determine buy/sell signals according to Williams R',
                         window_length=100,
                         strategy_data_types='high, low, close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            p, u, l = self.pars
        else:
            p, u, l = pars
        h = h.T
        res = willr(h[0], h[1], h[2], p)
        if res > -l:
            sig = -0.3
        elif res < -u:
            sig = 0.1
        else:
            sig = 0
        return sig


# Volume & Price Indicator based strategies


class AD(RuleIterator):
    """
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=[],
                         par_range=[],
                         name='AD',
                         description='Accumulation Distribution Line Strategy',
                         window_length=100,
                         strategy_data_types='high, low, close, volume')

    def realize(self, h, r=None, t=None, pars=None):
        h = h.T
        res = ad(h[0], h[1], h[2], h[3])
        if res > 0:
            sig = -0.3
        elif res < 0:
            sig = 0.1
        else:
            sig = 0
        return sig


class ADOSC(RuleIterator):
    """
    """

    def __init__(self, pars=(3, 10)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'int'],
                         par_range=[(2, 10), (10, 99)],
                         name='A/D Oscillator',
                         description='Accumulation Distribution Line Oscillator',
                         window_length=100,
                         strategy_data_types='high, low, close, volume')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            f, s = self.pars
        else:
            f, s = pars
        h = h.T
        res = ad(h[0], h[1], h[2], h[3], f, s)
        if res > 0:
            sig = -0.3
        elif res < 0:
            sig = 0.1
        else:
            sig = 0
        return sig


class OBV(RuleIterator):
    """
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=[],
                         par_range=[],
                         name='AD',
                         description='Accumulation Distribution Line Strategy',
                         window_length=100,
                         strategy_data_types='close, volume')

    def realize(self, h, r=None, t=None, pars=None):
        h = h.T
        res = ad(h[0], h[1])
        if res > 0:
            sig = -0.3
        elif res < 0:
            sig = 0.1
        else:
            sig = 0
        return sig


# Built-in Simple timing strategies:

class SignalNone(RuleIterator):
    """ 空交易信号策略：
        不生成任何交易信号的策略

    策略参数：
        none
    信号类型：
        PT型：百分比持仓比例信号
        PS型：百分比买卖交易信号
        VS型：买卖交易信号
    信号规则：
        整个信号周期内不产生任何交易信号

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='NONE',
                         description='Do not take any risk control activity')

    def realize(self, h, r=None, t=None, pars=None):
        return 0.


class SellRate(RuleIterator):
    """ 变化率卖出信号策略：
        当价格的变化率超过阈值时，产生卖出信号

    策略参数：
        day, int, 涨跌幅计算周期
        change, float，涨跌幅阈值
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        在下面情况下产生卖出信号：
        1，当change > 0，且day日涨幅大于change时，产生-1卖出信号
        2，当change < 0，且day日跌幅大于change时，产生-1卖出信号

    策略属性缺省值：
    默认参数：(20, 0.1)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(1, 100), (-0.5, 0.5)]
    策略不支持参考数据，不支持交易数据

    """

    # 跌幅控制策略，当N日涨跌幅超过p%的时候，强制生成卖出信号

    def __init__(self, pars=(20, 0.1)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'float'],
                         par_range=[(1, 100), (-0.5, 0.5)],
                         window_length=100,
                         name='SELLRATE',
                         description='Generate selling signal when N-day change rate is over a certain value')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            day, change = self.pars
        else:
            day, change = pars
        h = h
        diff = h[-1] - h[-day]
        if (change >= 0) and (diff > change):
            return -1
        if (change < 0) and (diff < change):
            return -1
        return 0


class BuyRate(RuleIterator):
    """ 变化率买入信号策略：
        当价格的变化率超过阈值时，产生买入信号

    策略参数：
        day, int, 涨跌幅计算周期
        change, float，涨跌幅阈值
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        在下面情况下产生买入信号：
        1，当change > 0，且day日涨幅大于change时，产生1买入信号
        2，当change < 0，且day日跌幅大于change时，产生1买入信号

    策略属性缺省值：
    默认参数：(20, 0.1)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(1, 100), (-0.5, 0.5)]
    策略不支持参考数据，不支持交易数据

    """

    # 跌幅控制策略，当N日涨跌幅超过p%的时候，强制生成卖出信号

    def __init__(self, pars=(20, 0.1)):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['int', 'float'],
                         par_range=[(1, 100), (-0.5, 0.5)],
                         window_length=100,
                         name='BUYRATE',
                         description='Generate buying signal when N-day change rate is over a certain value')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            day, change = self.pars
        else:
            day, change = pars
        h = h
        diff = h[-1] - h[-day]
        if (change >= 0) and (diff > change):
            return 1
        if (change < 0) and (diff < change):
            return 1
        return 0


class TimingLong(GeneralStg):
    """ 简单择时策略，整个历史周期上固定保持多头全仓状态

    策略参数：
        none
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        整个信号周期内持仓比例恒定为100%满仓

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='Long',
                         description='Simple Timing strategy, return constant long position on the whole history')

    def realize(self, h, r=None, t=None, pars=None):
        sc, wl, htp = h.shape
        return np.ones(shape=(sc, ))


class TimingShort(GeneralStg):
    """ 简单择时策略，整个历史周期上固定保持空头全仓状态

    策略参数：
        none
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        整个信号周期内持仓比例恒定为-100%空头全仓

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='Short',
                         description='Simple Timing strategy, return constant Short (minus) position on '
                                     'the whole history')

    def realize(self, h, r=None, t=None, pars=None):
        sc, wl, htp = h.shape
        return -np.ones(shape=(sc, ))


class TimingZero(GeneralStg):
    """ 简单择时策略，整个历史周期上固定保持空仓状态

    策略参数：
        none
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        整个信号周期内持仓比例恒定为0%空仓

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='Zero',
                         description='Simple Timing strategy, return constant Zero position ratio on the whole history')

    def realize(self, h, r=None, t=None, pars=None):
        sc, wl, htp = h.shape
        return np.zeros(shape=(sc, ))


class DMA(RuleIterator):
    """ DMA择时策略

    策略参数：
        s, int, 短均线周期
        l, int, 长均线周期
        d, int, DMA周期
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        在下面情况下产生买入信号：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0
        3， DMA与股价发生背离时的交叉信号，可信度较高

    策略属性缺省值：
    默认参数：(12, 26, 9)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(10, 250), (10, 250), (8, 250)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(12, 26, 9)):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['int', 'int', 'int'],
                         par_range=[(10, 250), (10, 250), (5, 250)],
                         name='DMA',
                         description='Quick DMA strategy, determine long/short position according to differences of '
                                     'moving average prices with simple timing strategy',
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            s, l, d = self.pars
        else:
            s, l, d = pars

        h = h.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)

        cat = 1 if dma[-1] > ama[-1] else 0
        return cat


# Built-in GeneralStg strategies:

class SelectingAll(GeneralStg):
    """ 基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配

    策略参数：
        none
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        整个信号周期内持仓比例恒定，且所有投资组合的持仓比例相同

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='SIMPLE ',
                         description='GeneralStg all share and distribute weights evenly')

    def realize(self, h, r=None, t=None, pars=None):
        # 所有股票全部被选中，投资比例平均分配
        share_count = h.shape[0]
        return np.ones(shape=(share_count,)) / share_count


class SelectingNone(GeneralStg):
    """基础选股策略：保持历史股票池中的所有股票都不被选中，投资仓位为0

    策略参数：
        none
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        整个信号周期内持仓比例恒定，且所有投资组合的持仓比例都为0

    策略属性缺省值：
    默认参数：()
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=()):
        super().__init__(pars=pars,
                         name='NONE ',
                         description='None of the shares will be selected')

    def realize(self, h, r=None, t=None, pars=None):
        share_count = h.shape[0]
        return [0.] * share_count


class SelectingRandom(GeneralStg):
    """ 基础选股策略：在每个历史分段中，按照指定的比例（p<1时）随机抽取若干股票，
        或随机抽取指定数量（p>=1）的股票进入投资组合，投资比例平均分配

    策略参数：
        p: float, 抽取的股票的数量(p>=1)或比例(p<1)
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        当p>=1时，从所有股票池中随机抽取p支股票，并设定所有被选中股票的持仓比例都为1/p
        当0>p>1时，从股票池中以p为比例抽取若干股票，并设定所有股票的持仓比例都相同且和为1

    策略属性缺省值：
    默认参数：(0.5, )
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(0, np.inf)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(0.5,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['float'],
                         par_range=[(0, np.inf)],
                         name='RANDOM',
                         description='GeneralStg share Randomly and distribute weights evenly')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            pct, = self.pars
        else:
            pct, = pars
        share_count = h.shape[0]
        if pct < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size=share_count, p=[pct, 1 - pct])
        else:  # pct >= 1 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(share_count, size=(int(pct)), replace=False)
            chosen = np.zeros(share_count)
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum()  # 投资比例平均分配


# Built-in FactorSorter strategies:

class SelectingAvgIndicator(FactorSorter):
    """ 以股票过去一段时间内的财务指标的平均值作为选股因子选股
        基础选股策略。以股票的历史指标的平均值作为选股因子，因子排序参数可以作为策略参数传入
        改变策略数据类型，根据不同的历史数据选股，选股参数可以通过pars传入
    策略参数:
        - sort_ascending: enum, 是否升序排列因子
            - True: 优先选择因子最小的股票,
            - False, 优先选择因子最大的股票
        - weighting: enum, 股票仓位分配比例权重
            - 'even'       :默认值, 所有被选中的股票都获得同样的权重
            - 'linear'     :权重根据因子排序线性分配
            - 'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
            - 'proportion' :权重与股票的因子分值成正比
        - condition: enum, 股票筛选条件
            - 'any'        :默认值，选择所有可用股票
            - 'greater'    :筛选出因子大于ubound的股票
            - 'less'       :筛选出因子小于lbound的股票
            - 'between'    :筛选出因子介于lbound与ubound之间的股票
            - 'not_between':筛选出因子不在lbound与ubound之间的股票
        - lbound: float, 股票筛选下限值, 默认值np.-inf
        - ubound: float, 股票筛选上限值, 默认值np.inf
        - max_sel_count: float, 抽取的股票的数量(p>=1)或比例(p<1), 默认值：0.5，表示选中50%的股票
    信号类型:
        PT型：百分比持仓比例信号
    信号规则:
        使用data_types指定一种数据类型，将股票过去的datatypes数据取平均值，将该平均值作为选股因子进行选股
    策略属性缺省值:
        默认参数：(True, 'even', 'greater', 0, 0, 0.25)
        数据类型：eps 每股收益，单数据输入
        采样频率：年
        窗口长度：270
        参数范围：[(True, False),
        ('even', 'linear', 'proportion'),
        ('any', 'greater', 'less', 'between', 'not_between'),
        (-np.inf, np.inf),
        (-np.inf, np.inf),
        (0, 1.)]

    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(True, 'even', 'greater', 0, 0, 0.25)):
        super().__init__(pars=pars,
                         par_count=6,
                         par_types=['enum', 'enum', 'enum', 'float', 'float', 'float'],
                         par_range=[(True, False),
                                    ('even', 'linear', 'distance', 'proportion'),
                                    ('any', 'greater', 'less', 'between', 'not_between'),
                                    (-np.inf, np.inf),
                                    (-np.inf, np.inf),
                                    (0, np.inf)],
                         name='FINANCE',
                         description='GeneralStg share_pool according to financial report EPS indicator',
                         data_freq='d',
                         strategy_run_freq='y',
                         window_length=90,
                         strategy_data_types='eps')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is not None:
            self.sort_ascending, self.weighting, self.condition, self.lbound, self.ubound, self.max_sel_count = pars
        factors = np.nanmean(h, axis=1)

        return factors


class SelectingNDayLast(FactorSorter):
    """ 以股票N天前的价格或数据指标作为选股因子选股
        基础选股策略，以股票的N日前历史数据作为选股因子，因子排序参数以策略属性的形式控制

    策略参数:
        n: int, 股票历史数据的前置期
    信号类型:
        PT型: 百分比持仓比例信号
    信号规则:
        在每个选股周期使用N日前的历史数据作为选股因子进行选股
        通过以下策略属性控制选股方法：
        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False,
                                    True: 优先选择因子最小的股票,
                                    False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比
    策略属性缺省值：
        默认参数：(2,)
        数据类型：close 收盘价，单数据输入
        采样频率：月
        窗口长度：100
        参数范围：[(2, 100)]
        策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(2,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 100)],
                         name='N-DAY LAST',
                         description='Select stocks according their previous prices',
                         data_freq='d',
                         strategy_run_freq='m',
                         window_length=100,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, = self.pars
        else:
            n, = pars
        factors = h[:, -n-1, 0]

        return factors


class SelectingNDayAvg(FactorSorter):
    """ 以股票过去N天的价格或数据指标的平均值作为选股因子选股
        基础选股策略：以股票的前N日历史数据平均值作为选股因子，因子排序参数以策略属性的形式控制

    策略参数：
        n: int, 股票历史数据的选择期
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        在每个选股周期使用过去N日的历史数据平均值作为选股因子进行选股
        通过以下策略属性控制选股方法：
        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False,
                                    True: 优先选择因子最小的股票,
                                    False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：月
    窗口长度：150
    参数范围：[(2, 150)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 150)],
                         name='N-DAY AVG',
                         description='Select stocks by its N day average open price',
                         data_freq='d',
                         strategy_run_freq='M',
                         window_length=150,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, = self.pars
        else:
            n, = pars
        n_average = h[:, -n-1:, 0].mean(axis=1)
        factors = n_average

        return factors


class SelectingNDayChange(FactorSorter):
    """ 以股票过去N天的价格或数据指标的变动值作为选股因子选股
    基础选股策略：根据股票以前n天的股价或数据变动幅度作为选股因子进行选股

    策略参数：
        n: int, 股票历史数据的选择期
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        在每个选股周期使用过去N日的历史数据平均值作为选股因子进行选股
        通过以下策略属性控制选股方法：
        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False,
                                    True: 优先选择因子最小的股票,
                                    False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：月
    窗口长度：150
    参数范围：[(2, 150)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 150)],
                         name='N-DAY CHANGE',
                         description='Select stocks by its N day price change',
                         data_freq='d',
                         strategy_run_freq='M',
                         window_length=150,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, = self.pars
        else:
            n, = pars
        current_price = h[:, -1, 0]
        n_previous = h[:, -n-1, 0]
        factors = current_price - n_previous

        return factors


class SelectingNDayRateChange(FactorSorter):
    """ 以股票过去N天的价格或数据指标的变动比例作为选股因子选股
    基础选股策略：根据股票以前n天的股价变动比例作为选股因子

    策略参数：
        n: int, 股票历史数据的选择期
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        在每个选股周期使用以前n天的股价变动比例作为选股因子进行选股
        通过以下策略属性控制选股方法：
        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False,
                                    True: 优先选择因子最小的股票,
                                    False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比

    策略属性缺省值：
    默认参数：(14,)
    数据类型：close 收盘价，单数据输入
    采样频率：月
    窗口长度：150
    参数范围：[(2, 150)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 150)],
                         name='N-DAY RATE',
                         description='Select stocks by its N day price change',
                         data_freq='d',
                         strategy_run_freq='M',
                         window_length=150,
                         strategy_data_types='close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, = self.pars
        else:
            n, = pars
        current_price = h[:, -1, 0]
        n_previous = h[:, -n-1, 0]
        factors = (current_price - n_previous) / n_previous

        return factors


class SelectingNDayVolatility(FactorSorter):
    """ 根据股票以前N天的股价波动率作为选股因子

    策略参数：
        n: int, 股票历史数据的选择期
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        在每个选股周期使用以前n天的股价的ATR波动率作为选股因子进行选股
        通过以下策略属性控制选股方法：
        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False,
                                    True: 优先选择因子最小的股票,
                                    False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比

    策略属性缺省值：
    默认参数：(14,)
    数据类型：high,low,close 最高价，最低价，收盘价，多数据输入
    采样频率：月
    窗口长度：150
    参数范围：[(2, 150)]
    策略不支持参考数据，不支持交易数据
    """

    def __init__(self, pars=(14,)):
        super().__init__(pars=pars,
                         par_count=1,
                         par_types=['int'],
                         par_range=[(2, 150)],
                         name='N-DAY VOL',
                         description='Select stocks by its N day price change',
                         data_freq='d',
                         strategy_run_freq='M',
                         window_length=150,
                         strategy_data_types='high,low,close')

    def realize(self, h, r=None, t=None, pars=None):
        if pars is None:
            n, = self.pars
        else:
            n, = pars
        high = h[:, :, 0]
        low = h[:, :, 1]
        close = h[:, :, 2]

        # 计算ATR波动率, 因为输入数据包含多个股票的数据，因此需要分别计算每个股票的ATR，然后将结果合并，最后取最后一列（最后一天的ATR）
        factors = np.array(list(map(atr, high, low, close, [n]*len(high))))[:, -1]

        return factors


BUILT_IN_STRATEGIES = {'crossline':     Crossline,  # TODO: TA-Lib free
                       'macd':          MACD,  # TODO: TA-Lib free
                       'dma':           DMA,  # TODO: TA-Lib free
                       'trix':          TRIX,  # TODO: TA-Lib free
                       'cdl':           CDL,
                       'bband':         BBand,
                       's-bband':       SoftBBand,
                       'sarext':        SAREXT,
                       'ssma':          SCRSSMA,
                       'sdema':         SCRSDEMA,
                       'sema':          SCRSEMA,
                       'sht':           SCRSHT,
                       'skama':         SCRSKAMA,
                       'smama':         SCRSMAMA,
                       'st3':           SCRST3,
                       'stema':         SCRSTEMA,
                       'strima':        SCRSTRIMA,
                       'swma':          SCRSWMA,
                       'dsma':          DCRSSMA,
                       'ddema':         DCRSDEMA,
                       'dema':          DCRSEMA,
                       'dkama':         DCRSKAMA,
                       'dmama':         DCRSMAMA,
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
                       'slt3':          SLPT3,
                       'sltema':        SLPTEMA,
                       'sltrima':       SLPTRIMA,
                       'slwma':         SLPWMA,
                       'adx':           ADX,
                       'apo':           APO,
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
                       'ultosc':        ULTOSC,
                       'willr':         WILLR,
                       'signal_none':   SignalNone,
                       'sellrate':      SellRate,
                       'buyrate':       BuyRate,
                       'long':          TimingLong,
                       'short':         TimingShort,
                       'zero':          TimingZero,
                       'all':           SelectingAll,
                       'select_none':   SelectingNone,
                       'random':        SelectingRandom,
                       'finance':       SelectingAvgIndicator,
                       'ndaylast':      SelectingNDayLast,
                       'ndayavg':       SelectingNDayAvg,
                       'ndayrate':      SelectingNDayRateChange,
                       'ndaychg':       SelectingNDayChange,
                       'ndayvol':       SelectingNDayVolatility
                       }


available_built_in_strategies = BUILT_IN_STRATEGIES.values()