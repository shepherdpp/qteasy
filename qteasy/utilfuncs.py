# coding=utf-8

import talib


# TODO: 以talib为基础创建一个金融函数库
# ========================
# Overlap Studies Functions 滚动窗口叠加算例函数

def bbands(close, timeperiod: int = 5, nbdevup: int = 2, nbdevdn: int = 2, matype: int = 0):
    """Bollinger Bands 布林带线

    input:
        :param close:
        :param timeperiod:
        :param nbdevup:
        :param nbdevdn:
        :param matype:
    :return:
        :upperband,
        middleband,
        lowerband: np.ndarray
    """
    return talib.BBANDS(close, timeperiod, nbdevup, nbdevdn, matype)


def dema(close, period: int = 30):
    """Double Exponential Moving Average 双重指数平滑移动平均

    :param close:
    :param period:
    :return:
    """
    return talib.DEMA(close, period)


def ema(close, span: int = 30):
    """Exponential Moving Average指数移动平均值

    input：
        :param close: 1-D ndarray, 输入数据，一维矩阵
        :param span: int, optional, 1 < span, 跨度
    output：=====
        :return: 1-D ndarray; 输入数据的指数平滑移动平均值
    """
    return talib.EMA(close, span)


def ht(close):
    """Hilbert Transform - Instantaneous Trendline 希尔伯特变换-瞬时趋势线

    :param close:
    :return:
    """
    return talib.HT_TRENDLINE(close)


def kama(close, timeperiod: int = 30):
    """Kaufman Adaptive Moving Average 考夫曼自适应移动平均线

    input:
    :param close:
    :param timeperiod:
    :return:

    """
    return talib.KAMA(close, timeperiod)


def ma(arr, timeperiod: int = 30, matype: int = 0):
    """Moving Average移动平均值

    input：
        :param close: type: 1-D np.ndarray 输入数据，一维矩阵
        :param timeperiod: type: int, 1 < window, 时间滑动窗口
        :param matype: type: int:
    return：
        :return: ndarray, 完成计算的移动平均序列
    """
    return talib.SMA(arr, timeperiod, matype)


def mama(close, fastlimit=0, slowlimit=0):
    """MESA Adaptive Moving Average MESA自适应移动平均线

    input:
    :param close:
    :param fastlimit:
    :param slowlimit:
    :return:
        :mama,
        :fama:
    """
    return talib.MAMA(close, fastlimit, slowlimit)


def mavp(close, periods, minperiod:int=2, maxperiod:int=30, matype:int=0):
    """Moving average with variable period 可变周期的移动平均线

    :param close:
    :param periods:
    :param minperiod:
    :param maxperiod:
    :param matype:
    :return:
    """
    return talib.MAVP(close, periods, minperiod, maxperiod, matype)

def mid_price(high, low, timeperiod:int=14):
    """Midpoint Price over period 期间中点价格

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return talib.MIDPRICE(high, low, timeperiod)

def sar(high, low, acceleration=0, maximum=0):
    """Parabolic SAR 抛物线SAR

    :param high:
    :param low:
    :param acceleration:
    :param maximum:
    :return:
    """
    return talib.SAR(high, low, acceleration, maximum)


def sarext(high, low, acceleration=0, maximum=0):
    """Parabolic SAR Extended 扩展抛物线SAR

    :param high:
    :param low:
    :param acceleration:
    :param maximum:
    :return:
    """
    return talib.SAREXT(high, low, acceleration, maximum)


def sma(close, timeperiod=30):
    """Simple Moving Average 简单移动平均

    :param close:
    :param timeperiod:
    :return:
    """
    return talib.SMA(close, timeperiod)


def t3(close, timeperiod=5, vfactor=0):
    """Triple Exponential Moving Average 三重指数移动平均线

    :param close:
    :param timeperiod:
    :param vfactor:
    :return:
    """
    return talib.T3(close, timeperiod, vfactor)


def tema(close, timeperiod=30):
    """Triple Exponential Moving Average 三重指数移动平均线

    :param close:
    :param timeperiod:
    :return:
    """
    return talib.TEMA(close, timeperiod)


def trima(close, timeperiod=30):
    """Triangular Moving Average 三角移动平均线

    :param close:
    :param timeperiod:
    :return:
    """
    return talib.TRIMA(close, timeperiod)


def wma(close, timeperiod=30):
    """Weighted Moving Average 加权移动平均线

    :param close:
    :param timeperiod:
    :return:
    """
    return talib.WMA(close, timeperiod)

# =============================
# Momentum Indicators 动量指标函数

def adx(high, low, close, timeperiod=14):
    """Average Directional Movement Index 平均定向运动指数

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return talib.ADX(high, low, close, timeperiod)


def adxr(high, low, close, timeperiod=14):
    """Average Directional Movement Index Rating 平均定向运动指数评级

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return talib.ADXR(high, low, close, timeperiod)


def apo(close, fastperiod=12, slowperiod=26, matype=0):
    """Absolute Price Oscillator 绝对价格震荡指标

    :param close:
    :param fastperiod:
    :param slowperiod:
    :param matype:
    :return:
    """
    return talib.APO(close, fastperiod, slowperiod, matype)


def aroon(high, low, timeperiod=14):
    """Aroon

    :param high:
    :param low:
    :param timeperiod:
    :return:
        aroondown,
        aroonup
    """
    return talib.AROON(high, low, timeperiod)


def aroonosc(high, low, timeperiod=14):
    """Aroon Oscillator

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return talib.AROONOSC(high, low, timeperiod)


def bop(open, high, low, close):
    """Balance Of Power

    :param open:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return talib.BOP(open, high, low, close)


def cci(high, low, close, timeperiod=14):
    """Commodity Channel Index

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return talib.CCI(high, low, close, timeperiod)


def cmo(close, timeperiod=14):
    """Chande Momentum Oscillator 钱德动量振荡器

    :param close:
    :param timeperiod:
    :return:
    """
    return talib.CMO(close, timeperiod)


def dx(high, low, close, timeperiod=14):
    """Directional Movement Index 方向运动指数

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return talib.DX(high, low, close, timeperiod)


def macd(close, fastperiod=12, slowperiod=26, signalperiod=9):
    """Moving Average Convergence/Divergence

    input
        :param close:
        :param fastperiod:
        :param slowperiod:
        :param signalperiod:
    :return:
        macd,
        macdsignal,
        macdhist
    """
    return talib.MACD(close, fastperiod, slowperiod, signalperiod)


def macdext(close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0):
    """MACD with controllable MA type

    :param close:
    :param fastperiod:
    :param fastmatype:
    :param slowperiod:
    :param slowmatype:
    :param signalperiod:
    :param signalmatype:
    :return:
    :macd,
    :macdsignal,
    :macdhist
    """
    return talib.MACDEXT(close, fastperiod, fastmatype, slowperiod, slowmatype, signalperiod, signalmatype)


def macdfix(close, signalperiod=9):
    """Moving Average Convergence/Divergence Fix 12/26

    :param close:
    :param signalperiod:
    :return:
    """
    return talib.MACDFIX(close, signalperiod)