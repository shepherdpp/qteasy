# coding=utf-8
# tafuncs.py

# ======================================
# This file contains wrapper functions
# that allow TA-lib functions to be
# used in qtesay
# ======================================

from talib import BBANDS, DEMA, EMA, HT_TRENDLINE, KAMA, MA, MAMA, MAVP, MIDPOINT, MIDPRICE, SAR, SAREXT, \
    SMA, T3, TEMA, TRIMA, WMA, ADX, ADXR, APO, BOP, CCI, CMO, DX, MACD, MACDEXT, AROON, AROONOSC, \
    MACDFIX, MFI, MINUS_DI, MINUS_DM, MOM, PLUS_DI, PLUS_DM, PPO, ROC, ROCP, ROCR, ROCR100, RSI, STOCH, \
    STOCHF, STOCHRSI, TRIX, ULTOSC, WILLR, AD, ADOSC, OBV, ATR, NATR, TRANGE, AVGPRICE, MEDPRICE, TYPPRICE, \
    WCLPRICE, HT_DCPERIOD, HT_DCPHASE, HT_PHASOR, HT_SINE, HT_TRENDMODE, CDL2CROWS, CDL3BLACKCROWS, \
    CDL3INSIDE, CDL3LINESTRIKE, CDL3OUTSIDE, CDL3STARSINSOUTH, CDL3WHITESOLDIERS, CDLABANDONEDBABY, \
    CDLADVANCEBLOCK, CDLBELTHOLD, CDLBREAKAWAY, CDLCLOSINGMARUBOZU, CDLCONCEALBABYSWALL, CDLCOUNTERATTACK, \
    CDLDARKCLOUDCOVER, CDLDOJI, CDLDOJISTAR, CDLDRAGONFLYDOJI, CDLENGULFING, CDLEVENINGDOJISTAR, CDLEVENINGSTAR, \
    CDLGAPSIDESIDEWHITE, CDLGRAVESTONEDOJI, CDLHAMMER, CDLHANGINGMAN, CDLHARAMI, CDLHARAMICROSS, CDLHIGHWAVE, \
    CDLHIKKAKE, CDLHIKKAKEMOD, CDLHOMINGPIGEON, CDLIDENTICAL3CROWS, CDLINNECK, CDLINVERTEDHAMMER, CDLKICKING, \
    CDLKICKINGBYLENGTH, CDLLADDERBOTTOM, CDLLONGLEGGEDDOJI, CDLLONGLINE, CDLMARUBOZU, CDLMATCHINGLOW, CDLMATHOLD, \
    CDLMORNINGDOJISTAR, CDLMORNINGSTAR, CDLONNECK, CDLPIERCING, CDLRICKSHAWMAN, CDLRISEFALL3METHODS, \
    CDLSEPARATINGLINES, CDLSHOOTINGSTAR, CDLSHORTLINE, CDLSPINNINGTOP, CDLSTALLEDPATTERN, CDLSTICKSANDWICH, \
    CDLTAKURI, CDLTASUKIGAP, CDLTHRUSTING, CDLTRISTAR, CDLUNIQUE3RIVER, CDLUPSIDEGAP2CROWS, CDLXSIDEGAP3METHODS, \
    BETA, CORREL, LINEARREG, LINEARREG_ANGLE, LINEARREG_INTERCEPT, LINEARREG_SLOPE, STDDEV, TSF, VAR, ACOS, ASIN, \
    ATAN, CEIL, COS, COSH, EXP, FLOOR, LN, LOG10, SIN, SINH, SQRT, TAN, TANH, ADD, DIV, MAX, MAXINDEX, MIN, MININDEX, \
    MINMAX, MINMAXINDEX, MULT, SUB, SUM


# 以Technical Analysis talib为基础创建的一个金融函数库，包括talib库中已经实现的所有技术分析函数
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
        :middleband,
        :lowerband: np.ndarray
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
# Volatility Indicators


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
# Price Transform Functions


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


# =====================================
# Cycle Indicators


def ht_dcperiod(close):
    """Hilbert Transform - Dominant Cycle Period

    :param close:
    :return:
    """
    return HT_DCPERIOD(close)


def ht_dcphase(close):
    """Hilbert Transform - Dominant Cycle Phase

    :param close:
    :return:
    """
    return HT_DCPHASE(close)


def ht_phasor(close):
    """Hilbert Transform - Phasor Components

    :param close:
    :return:
    inphase,
    quadrature
    """
    return HT_PHASOR(close)


def ht_sine(close):
    """Hilbert Transform - SineWave

    :param close:
    :return:
    """
    return HT_SINE(close)


def ht_trendmode(close):
    """Hilbert Transform - Trend vs Cycle Mode

    :param close:
    :return:
    """
    return HT_TRENDMODE(close)


# =================================================
# Pattern Recognition


def cdl2crows(opn, high, low, close):
    """Two Crows

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL2CROWS(opn, high, low, close)


def cdl3blackcrows(opn, high, low, close):
    """Three Black Crows

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL3BLACKCROWS(opn, high, low, close)


def cdl3inside(opn, high, low, close):
    """Three Inside Up/Down

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL3INSIDE(opn, high, low, close)


def cdl3linestrike(opn, high, low, close):
    """Three-Line Strike

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL3LINESTRIKE(opn, high, low, close)


def cdl3outside(opn, high, low, close):
    """Three Outside Up/Down

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL3OUTSIDE(opn, high, low, close)


def cdl3starsinsouth(opn, high, low, close):
    """Three Stars In The South

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL3STARSINSOUTH(opn, high, low, close)


def cdl3whitesoldiers(opn, high, low, close):
    """Three Advancing White Soldiers

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDL3WHITESOLDIERS(opn, high, low, close)


def cdlabandonedbaby(opn, high, low, close):
    """Abandoned Baby

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLABANDONEDBABY(opn, high, low, close)


def cdladvanceblock(opn, high, low, close):
    """Advance Block

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLADVANCEBLOCK(opn, high, low, close)


def cdlbelthold(opn, high, low, close):
    """Belt-hold

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLBELTHOLD(opn, high, low, close)


def cdlbreakaway(opn, high, low, close):
    """Breakaway

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLBREAKAWAY(opn, high, low, close)


def cdlclosingmarubozu(opn, high, low, close):
    """Closing Marubozu

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLCLOSINGMARUBOZU(opn, high, low, close)


def cdlconcealbabyswall(opn, high, low, close):
    """Concealing Baby Swallow

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLCONCEALBABYSWALL(opn, high, low, close)


def cdlcounterattack(opn, high, low, close):
    """Counterattack

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLCOUNTERATTACK(opn, high, low, close)


def cdldarkcloudcover(opn, high, low, close):
    """Dark Cloud Cover

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLDARKCLOUDCOVER(opn, high, low, close)


def cdldoji(opn, high, low, close):
    """Doji

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLDOJI(opn, high, low, close)


def cdldojistar(opn, high, low, close):
    """Doji Star

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLDOJISTAR(opn, high, low, close)


def cdldragonflydoji(opn, high, low, close):
    """Dragonfly Doji

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLDRAGONFLYDOJI(opn, high, low, close)


def cdlengulfing(opn, high, low, close):
    """Engulfing Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLENGULFING(opn, high, low, close)


def cdleveningdojistar(opn, high, low, close):
    """Evening Doji Star

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLEVENINGDOJISTAR(opn, high, low, close)


def cdleveningstar(opn, high, low, close):
    """Evening Star

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLEVENINGSTAR(opn, high, low, close)


def cdlgapsidesidewhite(opn, high, low, close):
    """Up/Down-gap side-by-side white lines

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLGAPSIDESIDEWHITE(opn, high, low, close)


def cdlgravestonedoji(opn, high, low, close):
    """Gravestone Doji

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLGRAVESTONEDOJI(opn, high, low, close)


def cdlhammer(opn, high, low, close):
    """Hammer

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHAMMER(opn, high, low, close)


def cdlhangingman(opn, high, low, close):
    """Hanging Man

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHANGINGMAN(opn, high, low, close)


def cdlharami(opn, high, low, close):
    """Harami Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHARAMI(opn, high, low, close)


def cdlharamicross(opn, high, low, close):
    """Harami Cross Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHARAMICROSS(opn, high, low, close)


def cdlhighwave(opn, high, low, close):
    """High-Wave Candle

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHIGHWAVE(opn, high, low, close)


def cdlhikkake(opn, high, low, close):
    """Hikkake Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHIKKAKE(opn, high, low, close)


def cdlhikkakemod(opn, high, low, close):
    """Modified Hikkake Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHIKKAKEMOD(opn, high, low, close)


def cdlhomingpigeon(opn, high, low, close):
    """Homing Pigeon

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLHOMINGPIGEON(opn, high, low, close)


def cdlidentical3crows(opn, high, low, close):
    """Identical Three Crows

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLIDENTICAL3CROWS(opn, high, low, close)


def cdlinneck(opn, high, low, close):
    """In-Neck Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLINNECK(opn, high, low, close)


def cdlinvertedhammer(opn, high, low, close):
    """Inverted Hammer

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLINVERTEDHAMMER(opn, high, low, close)


def cdlkicking(opn, high, low, close):
    """Kicking

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLKICKING(opn, high, low, close)


def cdlkickingbylength(opn, high, low, close):
    """Kicking - bull/bear determined by the longer marubozu

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLKICKINGBYLENGTH(opn, high, low, close)


def cdlladderbottom(opn, high, low, close):
    """Ladder Bottom

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLLADDERBOTTOM(opn, high, low, close)


def cdllongleggeddoji(opn, high, low, close):
    """Long Legged Doji

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLLONGLEGGEDDOJI(opn, high, low, close)


def cdllongline(opn, high, low, close):
    """Long Line Candle

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLLONGLINE(opn, high, low, close)


def cdlmarubozu(opn, high, low, close):
    """Marubozu

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLMARUBOZU(opn, high, low, close)


def cdlmatchinglow(opn, high, low, close):
    """Matching Low

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLMATCHINGLOW(opn, high, low, close)


def cdlmathold(opn, high, low, close):
    """Mat Hold

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLMATHOLD(opn, high, low, close)


def cdlmorningdojistar(opn, high, low, close):
    """Morning Doji Star

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLMORNINGDOJISTAR(opn, high, low, close)


def cdlmorningstar(opn, high, low, close):
    """Morning Star

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLMORNINGSTAR(opn, high, low, close)


def cdlonneck(opn, high, low, close):
    """On-Neck Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLONNECK(opn, high, low, close)


def cdlpiercing(opn, high, low, close):
    """Piercing Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLPIERCING(opn, high, low, close)


def cdlrickshawman(opn, high, low, close):
    """Rickshaw Man

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLRICKSHAWMAN(opn, high, low, close)


def cdlrisefall3methods(opn, high, low, close):
    """Rising/Falling Three Methods

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLRISEFALL3METHODS(opn, high, low, close)


def cdlseparatinglines(opn, high, low, close):
    """Separating Lines

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLSEPARATINGLINES(opn, high, low, close)


def cdlshootingstar(opn, high, low, close):
    """Shooting Star

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLSHOOTINGSTAR(opn, high, low, close)


def cdlshortline(opn, high, low, close):
    """Short Line Candle

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLSHORTLINE(opn, high, low, close)


def cdlspinningtop(opn, high, low, close):
    """Spinning Top

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLSPINNINGTOP(opn, high, low, close)


def cdlstalledpattern(opn, high, low, close):
    """Stalled Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLSTALLEDPATTERN(opn, high, low, close)


def cdlsticksandwich(opn, high, low, close):
    """Stick Sandwich

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLSTICKSANDWICH(opn, high, low, close)


def cdltakuri(opn, high, low, close):
    """Takuri (Dragonfly Doji with very long lower shadow)

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLTAKURI(opn, high, low, close)


def cdltasukigap(opn, high, low, close):
    """Tasuki Gap

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLTASUKIGAP(opn, high, low, close)


def cdlthrusting(opn, high, low, close):
    """Thrusting Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLTHRUSTING(opn, high, low, close)


def cdltristar(opn, high, low, close):
    """Tristar Pattern

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLTRISTAR(opn, high, low, close)


def cdlunique3river(opn, high, low, close):
    """Unique 3 River

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLUNIQUE3RIVER(opn, high, low, close)


def cdlupsidegap2crows(opn, high, low, close):
    """Upside Gap Two Crows

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLUPSIDEGAP2CROWS(opn, high, low, close)


def cdlxsidegap3methods(opn, high, low, close):
    """Upside/Downside Gap Three Methods

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return CDLXSIDEGAP3METHODS(opn, high, low, close)


# ===========================
# Statistic Functions


def beta(high, low, timeperiod=5):
    """Beta

    :param high:
    :param low:
    :param timeperiod:
    :return:
        :real:
    """
    return BETA(high, low, timeperiod)


def correl(high, low, timeperiod=30):
    """Pearson's Correlation Coefficient (r)

    :param high:
    :param low:
    :param timeperiod:
    :return:
        :real:
    """
    return CORREL(high, low, timeperiod)


def linearreg(close, timeperiod=14):
    """Linear Regression

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return LINEARREG(close, timeperiod)


def linearreg_angle(close, timeperiod=14):
    """Linear Regression Angle

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return LINEARREG_ANGLE(close, timeperiod)


def linearreg_intercept(close, timeperiod=14):
    """Linear Regression Intercept

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return LINEARREG_INTERCEPT(close, timeperiod)


def linearreg_slope(close, timeperiod=14):
    """Linear Regression Slope

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return LINEARREG_SLOPE(close, timeperiod)


def stddev(close, timeperiod=5, nbdev=1):
    """Standard Deviation

    :param close:
    :param timeperiod:
    :param nbdev:
    :return:
        :real:
    """
    return STDDEV(close, timeperiod, nbdev)


def tsf(close, timeperiod=14):
    """Time Series Forecast

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return TSF(close, timeperiod)


def var(close, timeperiod=5, nbdev=1):
    """Variance

    :param close:
    :param timeperiod:
    :param nbdev:
    :return:
        :real:
    """
    return VAR(close, timeperiod, nbdev)


# ===========================
# Math Operation Functions


def acos(close):
    """Vector Trigonometric ACos

    :param close:
    :return:
        :real:
    """
    return ACOS(close)


def asin(close):
    """Vector Trigonometric ASin

    :param close:
    :return:
        :real:
    """
    return ASIN(close)


def atan(close):
    """Vector Trigonometric ATan

    :param close:
    :return:
        :real:
    """
    return ATAN(close)


def ceil(close):
    """Vector Ceil

    :param close:
    :return:
        :real:
    """
    return CEIL(close)


def cos(close):
    """Vector Trigonometric Cos

    :param close:
    :return:
        :real:
    """
    return COS(close)


def cosh(close):
    """Vector Trigonometric Cosh

    :param close:
    :return:
        :real:
    """
    return COSH(close)


def exp(close):
    """Vector Arithmetic Exp

    :param close:
    :return:
        :real:
    """
    return EXP(close)


def floor(close):
    """Vector Floor

    :param close:
    :return:
        :real:
    """
    return FLOOR(close)


def ln(close):
    """Vector Log Natural

    :param close:
    :return:
        :real:
    """
    return LN(close)


def log10(close):
    """Vector Log10

    :param close:
    :return:
        :real:
    """
    return LOG10(close)


def sin(close):
    """Vector Trigonometric Sin

    :param close:
    :return:
        :real:
    """
    return SIN(close)


def sinh(close):
    """Vector Trigonometric Sinh

    :param close:
    :return:
        :real:
    """
    return SINH(close)


def sqrt(close):
    """Vector Square Root

    :param close:
    :return:
        :real:
    """
    return SQRT(close)


def tan(close):
    """Vector Trigonometric Tan

    :param close:
    :return:
        :real:
    """
    return TAN(close)


def tanh(close):
    """Vector Trigonometric Tanh

    :param close:
    :return:
        :real:
    """
    return TANH(close)


# ===========================
# Math Operator Functions


def add(high, low):
    """Vector Arithmetic Add

    :param high:
    :param low:
    :return:
        :real:
    """
    return ADD(high, low)


def div(high, low):
    """Vector Arithmetic Div

    :param high:
    :param low:
    :return:
        :real:
    """
    return DIV(high, low)


def max(close, timeperiod=30):
    """Highest value over a specified period

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return MAX(close, timeperiod)


def maxindex(close, timeperiod=30):
    """Index of highest value over a specified period

    :param close:
    :param timeperiod:
    :return:
        :integer:
    """
    return MAXINDEX(close, timeperiod)


def min(close, timeperiod=30):
    """Lowest value over a specified period

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return MIN(close, timeperiod)


def minindex(close, timeperiod=30):
    """Index of lowest value over a specified period

    :param close:
    :param timeperiod:
    :return:
        :integer:
    """
    return MININDEX(close, timeperiod)


def minmax(close, timeperiod=30):
    """Lowest and highest values over a specified period

    :param close:
    :param timeperiod:
    :return:
        :min:
        :max:
    """
    return MINMAX(close, timeperiod)


def minmaxindex(close, timeperiod=30):
    """Indexes of lowest and highest values over a specified period

    :param close:
    :param timeperiod:
    :return:
        :minidx:
        :maxidx:
    """
    return MINMAXINDEX(close, timeperiod)


def mult(high, low):
    """Vector Arithmetic Mult

    :param high:
    :param low:
    :return:
        :real:
    """
    return MULT(high, low)


def sub(high, low):
    """Vector Arithmetic Substraction

    :param high:
    :param low:
    :return:
        :real:
    """
    return SUB(high, low)


def sum(close, timeperiod=30):
    """Summation

    :param close:
    :param timeperiod:
    :return:
        :real:
    """
    return SUM(close, timeperiod)