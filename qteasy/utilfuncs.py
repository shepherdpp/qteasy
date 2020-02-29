# coding=utf-8

from talib import BBANDS, DEMA, EMA, HT_TRENDLINE, KAMA, MA, MAMA, MAVP, MIDPOINT, MIDPRICE, SAR, SAREXT, \
    SMA, T3, TEMA, TRIMA, WMA, ADX, ADXR, APO, BOP, CCI, CMO, DX, MACD, MACDEXT, AROON, AROONOSC, \
    MACDFIX, MFI, MINUS_DI, MINUS_DM, MOM, PLUS_DI, PLUS_DM, PPO, ROC, ROCP, ROCR, ROCR100, RSI, STOCH, \
    STOCHF, STOCHRSI, TRIX, ULTOSC, WILLR, AD, ADOSC, OBV, ATR, NATR, TRANGE, AVGPRICE, MEDPRICE, TYPPRICE, \
    WCLPRICE


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
    return BBANDS(close, timeperiod, nbdevup, nbdevdn, matype)


def dema(close, period: int = 30):
    """Double Exponential Moving Average 双重指数平滑移动平均

    :param close:
    :param period:
    :return:
    """
    return DEMA(close, period)


def ema(close, span: int = 30):
    """Exponential Moving Average指数移动平均值

    input：
        :param close: 1-D ndarray, 输入数据，一维矩阵
        :param span: int, optional, 1 < span, 跨度
    output：=====
        :return: 1-D ndarray; 输入数据的指数平滑移动平均值
    """
    return EMA(close, span)


def ht(close):
    """Hilbert Transform - Instantaneous Trendline 希尔伯特变换-瞬时趋势线

    :param close:
    :return:
    """
    return HT_TRENDLINE(close)


def kama(close, timeperiod: int = 30):
    """Kaufman Adaptive Moving Average 考夫曼自适应移动平均线

    input:
    :param close:
    :param timeperiod:
    :return:

    """
    return KAMA(close, timeperiod)


def ma(close, timeperiod: int = 30, matype: int = 0):
    """Moving Average移动平均值

    input：
        :param close: type: 1-D np.ndarray 输入数据，一维矩阵
        :param timeperiod: type: int, 1 < window, 时间滑动窗口
        :param matype: type: int:
    return：
        :return: ndarray, 完成计算的移动平均序列
    """
    return MA(close, timeperiod, matype)


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
    return MAMA(close, fastlimit, slowlimit)


def mavp(close, periods, minperiod: int = 2, maxperiod: int = 30, matype: int = 0):
    """Moving average with variable period 可变周期的移动平均线

    :param close:
    :param periods:
    :param minperiod:
    :param maxperiod:
    :param matype:
    :return:
    """
    return MAVP(close, periods, minperiod, maxperiod, matype)


def mid_point(close, timeperiod=14):
    """MidPoint over period

    :param close:
    :param timeperiod:
    :return:
    """
    return MIDPOINT(close, timeperiod)


def mid_price(high, low, timeperiod: int = 14):
    """Midpoint Price over period 期间中点价格

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return MIDPRICE(high, low, timeperiod)


def sar(high, low, acceleration=0, maximum=0):
    """Parabolic SAR 抛物线SAR

    :param high:
    :param low:
    :param acceleration:
    :param maximum:
    :return:
    """
    return SAR(high, low, acceleration, maximum)


def sarext(high, low, acceleration=0, maximum=0):
    """Parabolic SAR Extended 扩展抛物线SAR

    :param high:
    :param low:
    :param acceleration:
    :param maximum:
    :return:
    """
    return SAREXT(high, low, acceleration, maximum)


def sma(close, timeperiod=30):
    """Simple Moving Average 简单移动平均

    :param close:
    :param timeperiod:
    :return:
    """
    return SMA(close, timeperiod)


def t3(close, timeperiod=5, vfactor=0):
    """Triple Exponential Moving Average 三重指数移动平均线

    :param close:
    :param timeperiod:
    :param vfactor:
    :return:
    """
    return T3(close, timeperiod, vfactor)


def tema(close, timeperiod=30):
    """Triple Exponential Moving Average 三重指数移动平均线

    :param close:
    :param timeperiod:
    :return:
    """
    return TEMA(close, timeperiod)


def trima(close, timeperiod=30):
    """Triangular Moving Average 三角移动平均线

    :param close:
    :param timeperiod:
    :return:
    """
    return TRIMA(close, timeperiod)


def wma(close, timeperiod=30):
    """Weighted Moving Average 加权移动平均线

    :param close:
    :param timeperiod:
    :return:
    """
    return WMA(close, timeperiod)


# =============================================================
# Momentum Indicators 动量指标函数


def adx(high, low, close, timeperiod=14):
    """Average Directional Movement Index 平均定向运动指数

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return ADX(high, low, close, timeperiod)


def adxr(high, low, close, timeperiod=14):
    """Average Directional Movement Index Rating 平均定向运动指数评级

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return ADXR(high, low, close, timeperiod)


def apo(close, fastperiod=12, slowperiod=26, matype=0):
    """Absolute Price Oscillator 绝对价格震荡指标

    :param close:
    :param fastperiod:
    :param slowperiod:
    :param matype:
    :return:
    """
    return APO(close, fastperiod, slowperiod, matype)


def aroon(high, low, timeperiod=14):
    """Aroon

    :param high:
    :param low:
    :param timeperiod:
    :return:
        aroondown,
        aroonup
    """
    return AROON(high, low, timeperiod)


def aroonosc(high, low, timeperiod=14):
    """Aroon Oscillator

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return AROONOSC(high, low, timeperiod)


def bop(opn, high, low, close):
    """Balance Of Power

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return BOP(opn, high, low, close)


def cci(high, low, close, timeperiod=14):
    """Commodity Channel Index

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return CCI(high, low, close, timeperiod)


def cmo(close, timeperiod=14):
    """Chande Momentum Oscillator 钱德动量振荡器

    :param close:
    :param timeperiod:
    :return:
    """
    return CMO(close, timeperiod)


def dx(high, low, close, timeperiod=14):
    """Directional Movement Index 方向运动指数

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return DX(high, low, close, timeperiod)


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
    return MACD(close, fastperiod, slowperiod, signalperiod)


def macdext(close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0):
    """MACD with controllable MA type

    input:
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
    return MACDEXT(close, fastperiod, fastmatype, slowperiod, slowmatype, signalperiod, signalmatype)


def macdfix(close, signalperiod=9):
    """Moving Average Convergence/Divergence Fix 12/26

    input:
        :param close:
        :param signalperiod:
    :return:
        macd,
        macdsignal,
        macdhist
    """
    return MACDFIX(close, signalperiod)


def mfi(high, low, close, volume, timeperiod=14):
    """Money Flow Index

    input:
        :param high:
        :param low:
        :param close:
        :param volume:
        :param timeperiod:
    :return:
    """
    return MFI(high, low, close, volume, timeperiod)


def minus_di(high, low, close, timeperiod=14):
    """Minus Directional Indicator

    input:
        :param high:
        :param low:
        :param close:
        :param timeperiod:
    :return:
    """
    return MINUS_DI(high, low, close, timeperiod)


def minus_dm(high, low, timeperiod=14):
    """Minus Directional Movement

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return MINUS_DM(high, low, timeperiod)


def mom(close, timeperiod=10):
    """Momentum

    :param close:
    :param timeperiod:
    :return:
    """
    return MOM(close, timeperiod)


def plus_di(high, low, close, timeperiod=14):
    """Plus Directional Indicator

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return PLUS_DI(high, low, close, timeperiod)


def plus_dm(high, low, timeperiod=14):
    """Plus Directional Movement

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return PLUS_DM(high, low, timeperiod)


def ppo(close, fastperiod=12, slowperiod=26, matype=0):
    """Percentage Price Oscillator

    :param close:
    :param fastperiod:
    :param slowperiod:
    :param matype:
    :return:
    """
    return PPO(close, fastperiod, slowperiod, matype)


def roc(close, timeperiod=10):
    """Rate of change : ((price/prevPrice)-1)*100

    :param close:
    :param timeperiod:
    :return:
    """
    return ROC(close, timeperiod)


def rocp(close, timeperiod=10):
    """Rate of change Percentage: (price-prevPrice)/prevPrice

    :param close:
    :param timeperiod:
    :return:
    """
    return ROCP(close, timeperiod)


def rocr(close, timeperiod=10):
    """Rate of change ratio: (price/prevPrice)

    :param close:
    :param timeperiod:
    :return:
    """
    return ROCR(close, timeperiod)


def rocr100(close, timeperiod=10):
    """Rate of change ratio 100 scale: (price/prevPrice)*100

    :param close:
    :param timeperiod:
    :return:
    """
    return ROCR100(close, timeperiod)


def rsi(close, timeperiod=14):
    """Relative Strength Index

    :param close:
    :param timeperiod:
    :return:
    """
    return RSI(close, timeperiod)


def stoch(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0):
    """Stochastic

    :param high:
    :param low:
    :param close:
    :param fastk_period:
    :param slowk_period:
    :param slowk_matype:
    :param slowd_period:
    :param slowd_matype:
    :return:
        slowk,
        slowd
    """
    return STOCH(high, low, close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)


def stochf(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0):
    """Stochastic Fast

    :param high:
    :param low:
    :param close:
    :param fastk_period:
    :param fastd_period:
    :param fastd_matype:
    :return:
        fastk,
        fastd
    """
    return STOCHF(high, low, close, fastk_period, fastd_period, fastd_matype)


def stochrsi(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0):
    """Stochastic Relative Strength Index

    :param close:
    :param timeperiod:
    :param fastk_period:
    :param fastd_period:
    :param fastd_matype:
    :return:
    fastk,
    fastd
    """
    return STOCHRSI(close, timeperiod, fastk_period, fastd_period, fastd_matype)


def trix(close, timeperiod=30):
    """1-day Rate-Of-Change (ROC) of a Triple Smooth EMA

    :param close:
    :param timeperiod:
    :return:
    """
    return TRIX(close, timeperiod)


def ultosc(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28):
    """Ultimate Oscillator

    :param high:
    :param low:
    :param close:
    :param timeperiod1:
    :param timeperiod2:
    :param timeperiod3:
    :return:
    """
    return ULTOSC(high, low, close, timeperiod1, timeperiod2, timeperiod3)


def willr(high, low, close, timeperiod=14):
    """Williams' %R

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return WILLR(high, low, close, timeperiod)


# =============================================================
# Volume Indicators 量指标函数


def ad(high, low, close, volume):
    """Chaikin A/D Line

    :param high:
    :param low:
    :param close:
    :param volume:
    :return:
    """
    return AD(high, low, close, volume)


def adosc(high, low, close, volume, fastperiod=3, slowperiod=10):
    """Chaikin A/D Oscillator

    :param high:
    :param low:
    :param close:
    :param volume:
    :param fastperiod:
    :param slowperiod:
    :return:
    """
    return ADOSC(high, low, close, volume, fastperiod, slowperiod)


def obv(close, volume):
    """

    :param close:
    :param volume:
    :return:
    """
    return OBV(close, volume)


# ===========================
# Volume Indicators


def atr(high, low, close, timeperiod=14):
    """Average True Range

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return ATR(high, low, close, timeperiod)


def natr(high, low, close, timeperiod=14):
    """Normalized Average True Range

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return NATR(high, low, close, timeperiod)


def trange(high, low, close):
    """True Range

    :param high:
    :param low:
    :param close:
    :return:
    """
    return TRANGE(high, low, close)


# ===========================
# Volatility Indicators


def avgprice(opn, high, low, close):
    """Average Price

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return AVGPRICE(opn, high, low, close)


def medprice(high, low):
    """Median Price

    :param high:
    :param low:
    :return:
    """
    return MEDPRICE(high, low)


def typprice(high, low, close):
    """Typical Price

    :param high:
    :param low:
    :param close:
    :return:
    """
    return TYPPRICE(high, low, close)


def wclprice(high, low, close):
    """Weighted Close Price

    :param high:
    :param low:
    :param close:
    :return:
    """
    return WCLPRICE(high, low, close)
