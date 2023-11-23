# coding=utf-8
# ======================================
# File:     tafuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-09-27
# Desc:
#   Interfaces to ta-lib functions.
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


# TODO: 假设talib没有正确安装时，需要提供替代办法计算相应值，或者针对部分最常用内置策略
#  提供替代版本解决方案，对其他内置策略，使用恰当的提示方式提示用户应该及如何安装TA-lib

# 以Technical Analysis talib为基础创建的一个金融函数库，包括talib库中已经实现的所有技术分析函数

# ========================
# Overlap Studies Functions 滚动窗口叠加算例函数

def bbands(close, timeperiod: int = 20, nbdevup: int = 2, nbdevdn: int = 2, matype: int = 0):
    """Bollinger Bands 布林带线

        Bollinger Bands® are a technical analysis tool developed by John Bollinger
        for generating oversold or overbought signals.
        There are three config_lines that compose Bollinger Bands: A simple moving average
        (middle band) and an upper and lower band.
        The upper and lower bands are typically 2 standard deviations ± from a
        20-day simple moving average, but can be modified.

        The Bollinger bands are calculated as following:

        BOLU=MA(TP,n)+m∗σ[TP,n]
        BOLD=MA(TP,n)−m∗σ[TP,n]

    Parameters
    ----------
        close: float,收盘价
        timeperiod:
        nbdevup:
        nbdevdn:
        matype:

    Return
    ------
        :upperband,
        :middleband,
        :lowerband: np.ndarray
    """
    return BBANDS(close, timeperiod, nbdevup, nbdevdn, matype)


def dema(close, period: int = 30):
    """Double Exponential Moving Average 双重指数平滑移动平均

        The DEMA uses two exponential moving averages (EMAs) to eliminate lag,
        as some traders view lag as a problem. The DEMA is used in a similar way
        to traditional moving averages (MA). The average helps confirm up-trends
        when the price is above the average, and helps confirm downtrends when
        the price is below the average.

        formula used for calculating DEMA is like following:

        DEMA=2×EMA_N − EMA of EMA_N

    close: float,收盘价
    period:

    Return
    ------
    """
    return DEMA(close, period)


def ema(close, span: int = 30):
    """Exponential Moving Average指数移动平均值

        The EMA is a type of weighted moving average (WMA) that gives
        more weighting or importance to recent price data. Like the
        simple moving average, the exponential moving average is used
        to see price trends over time, and watching several EMAs at
        the same time is easy to do with moving average ribbons.

        EMA is calculated with following formula:

        EMA=Price(t)×k+EMA(y)×(1−k)

    Parameters
    ----------
    close: float,收盘价 1-D ndarray, 输入数据，一维矩阵
    span: int, optional, 1 < span, 跨度

    Return
    ------
    1-D ndarray; 输入数据的指数平滑移动平均值
    """
    return EMA(close, span)


def ht(close):
    """Hilbert Transform - Instantaneous Trendline 希尔伯特变换-瞬时趋势线

    In mathematics and in signal processing, the Hilbert transform is a
    specific linear operator that takes a function, u(t) of a real
    variable and produces another function of a real variable H(u)(t).
    This linear operator is given by convolution with the function
    1/(πt):

    close: float,收盘价

    Return
    ------
    """
    return HT_TRENDLINE(close)


def kama(close, timeperiod: int = 30):
    """Kaufman Adaptive Moving Average 考夫曼自适应移动平均线

    Kaufman's Adaptive Moving Average (KAMA) is a moving average designed
    to account for market noise or volatility. KAMA will closely follow
    prices when the price swings are relatively small and the noise is
    low. KAMA will adjust when the price swings widen and follow prices
    from a greater distance. This trend-following indicator can be used to
    identify the overall trend, time turning points and filter price
    movements.

    Calculation:

    Before calculating KAMA, we need to calculate the Efficiency Ratio
    (ER) and the Smoothing Constant (SC). Thus calculation of KAMA takes
    following steps:

    step1, Efficiency Ratio (ER):

    ER = Change/Volatility
    Change = ABS(Close - Close (10 periods ago))
    Volatility = Sum10(ABS(Close - Prior Close))

    Volatility is the sum of the absolute value of the last ten price
    changes (Close - Prior Close).

    step2, Smoothing Constant (SC)

    SC = [ER x (fastest SC - slowest SC) + slowest SC]2
    SC = [ER x (2/(2+1) - 2/(30+1)) + 2/(30+1)]2

    step3. Kama:

    Current KAMA = Prior KAMA + SC x (Price - Prior KAMA)

    Parameters
    ----------
    close: float,收盘价
    timeperiod:

    Return
    ------

    """
    return KAMA(close, timeperiod)


def ma(close, timeperiod: int = 30, matype: int = 0):
    """Moving Average移动平均值

    For a simple moving average, the formula is the sum of the data
    points over a given period divided by the number of periods.

    Parameters
    ----------
    close: float,收盘价 type: 1-D np.ndarray 输入数据，一维矩阵
    timeperiod: type: int, 1 < window, 时间滑动窗口
    matype: type: int:

    Return
    ------
    ndarray, 完成计算的移动平均序列
    """
    return MA(close, timeperiod, matype)


def mama(close, fastlimit=0, slowlimit=0):
    """MESA Adaptive Moving Average MESA自适应移动平均线

    the MESA Adaptive Moving Average is a technical trend-following
    indicator which, according to its creator, adapts to price movement
    “based on the rate change of phase as measured by the Hilbert
    Transform Discriminator”. This method of adaptation features a fast
    and a slow moving average so that the composite moving average swiftly
    responds to price changes and holds the average value until the next
    bars close.

    Parameters
    ----------
    close: float,收盘价
    fastlimit:
    slowlimit:

    Return
    ------
        :mama,
        :fama:
    """
    return MAMA(close, fastlimit, slowlimit)


def mavp(close, periods, minperiod: int = 2, maxperiod: int = 30, matype: int = 0):
    """Moving average with variable period 可变周期的移动平均线

    Parameters
    ----------
    close: float,收盘价
    periods:
    minperiod:
    maxperiod:
    matype: 0 ~ 8

    Return
    ------
    """
    return MAVP(close, periods, minperiod, maxperiod, matype)


def mid_point(close, timeperiod=14):
    """MidPoint over period

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return MIDPOINT(close, timeperiod)


def mid_price(high, low, timeperiod: int = 14):
    """Midpoint Price over period 期间中点价格

    Parameters
    ----------
    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
    """
    return MIDPRICE(high, low, timeperiod)


def sar(high, low, acceleration=0, maximum=0):
    """Parabolic SAR 抛物线SAR

    The parabolic SAR is a technical indicator used to determine the
    price direction of an asset, as well as draw attention to when
    the price direction is changing. Sometimes known as the "stop
    and reversal system".
    The parabolic SAR indicator appears on a chart as a series of
    dots, either above or below an asset's price, depending on the
    direction the price is moving.
    A dot is placed below the price when it is trending upward, and
    above the price when it is trending downward.

    Parameters
    ----------
    high: float, 最高价
    low: float, 最低价
    acceleration:
    maximum:

    Return
    ------
    """
    return SAR(high, low, acceleration, maximum)


def sarext(high, low, acceleration=0, maximum=0):
    """Parabolic SAR Extended 扩展抛物线SAR

    the Parabolic SAR Extended is an indicator developed by PlayOptions
    that derives from the classic Parabolic SAR. The interpretation is
    very simple.
    It is an indicator designed for optionists as it is reactive in
    the beginning of the trend, but then remains little influenced by
    the movements, although significant, but which do not change the
    current trend.

    Operation:
        BUY signals are generated when the indicator is above 0;
        SELL signals are generated when the indicator is below 0.

    Parameters
    ----------
    high: float, 最高价
    low: float, 最低价
    acceleration:
    maximum:

    Return
    ------
    """
    return SAREXT(high, low, acceleration, maximum)


def sma(close, timeperiod=30):  # TODO: TA-Lib free
    """Simple Moving Average 简单移动平均

    For a simple moving average, the formula is the sum of the data
    points over a given period divided by the number of periods.

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return SMA(close, timeperiod)


def t3(close, timeperiod=5, vfactor=0):
    """Triple Exponential Moving Average 三重指数移动平均线

    close: float,收盘价
    timeperiod:
    vfactor:

    Return
    ------
    """
    return T3(close, timeperiod, vfactor)


def tema(close, timeperiod=30):
    """Triple Exponential Moving Average 三重指数移动平均线

    The triple exponential moving average was designed to smooth
    price fluctuations, thereby making it easier to identify trends
    without the lag associated with traditional moving averages (MA).
    It does this by taking multiple exponential moving averages (EMA)
    of the original EMA and subtracting out some of the lag.


    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return TEMA(close, timeperiod)


def trima(close, timeperiod=30):
    """Triangular Moving Average 三角移动平均线

    the triangular moving average (TMA) is a technical indicator that
    is similar to other moving averages. The TMA shows the average
    (or mean) price of an asset over a specified number of data
    points—usually a number of price bars. However, the triangular
    moving average differs in that it is double smoothed—which also
    means averaged twice.

    The TMA can also be expressed as:
    TMA = SUM (SMA values) / N
    SMA = (P1 + P2 + P3 + P4 + ... + PN) / N

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return TRIMA(close, timeperiod)


def wma(close, timeperiod=30):
    """Weighted Moving Average 加权移动平均线

    The weighted moving average (WMA) is a technical indicator
    that traders use to generate trade direction and make a buy
    or sell decision. It assigns greater weighting to recent data
    points and less weighting on past data points. The weighted
    moving average is calculated by multiplying each observation
    in the data set by a predetermined weighting factor.

    WMA can be calculated with following formula:

    WMA = (P1 * N + P2 * (N-1) + ... + PN) / (N * (N + 1))/2

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return WMA(close, timeperiod)


# =============================================================
# Momentum Indicators 动量指标函数


def adx(high, low, close, timeperiod=14):
    """Average Directional Movement Index 平均定向运动指数

    ADX stands for Average Directional Movement Index and can be
    used to help measure the overall strength of a trend. The ADX
    indicator is an average of expanding price range values. The
    ADX is a component of the Directional Movement System developed
    by Welles Wilder. This system attempts to measure the strength
    of price movement in positive and negative direction using the
    DMI+ and DMI- indicators along with the ADX.

    the ADX indicates movements of prices as following:

    - Wilder suggests that a strong trend is present when ADX is above
    25 and no trend is present when below 20.

    - When the ADX turns down from high values, then the trend may be
    ending. You may want to do additional research to determine if
    closing open positions is appropriate for you.

    - If the ADX is declining, it could be an indication that the market
    is becoming less directional, and the current trend is weakening. You
    may want to avoid trading trend systems as the trend changes.

    - If after staying low for a lengthy time, the ADX rises by 4 or 5
    units, (for example, from 15 to 20), it may be giving a signal to
    trade the current trend.

    - If the ADX is rising then the market is showing a strengthening trend.
    The value of the ADX is proportional to the slope of the trend. The
    slope of the ADX line is proportional to the acceleration of the price
    movement (changing trend slope). If the trend is a constant slope then
    the ADX value tends to flatten out.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ADX(high, low, close, timeperiod)


def adxr(high, low, close, timeperiod=14):
    """Average Directional Movement Index Rating 平均定向运动指数评级

    The Average Directional Movement Index Rating (ADXR) measures the strength
    of the Average Directional Movement Index (ADX). It's calculated by taking
    the average of the current ADX and the ADX from one time period before
    (time periods can vary, but the most typical period used is 14 days).

    ADXR = (ADX + ADX n-periods ago) / 2

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ADXR(high, low, close, timeperiod)


def apo(close, fastperiod=12, slowperiod=26, matype=0):
    """Absolute Price Oscillator 绝对价格震荡指标

    The Absolute Price Oscillator displays the difference between two exponential
    moving averages of a security's price and is expressed as an absolute value.

    - APO crossing above zero is considered bullish, while crossing below zero is
    bearish.

    - A positive indicator value indicates an upward movement, while negative readings
    signal a downward trend.

    - Divergences form when a new high or low in price is not confirmed by the
    Absolute Price Oscillator (APO). A bullish divergence forms when price make a
    lower low, but the APO forms a higher low. This indicates less downward momentum
    that could foreshadow a bullish reversal. A bearish divergence forms when price
    makes a higher high, but the APO forms a lower high. This shows less upward momentum
    that could foreshadow a bearish reversal.

    APO = Shorter Period EMA – Longer Period EMA

    close: float,收盘价
    fastperiod:
    slowperiod:
    matype:

    Return
    ------
    """
    return APO(close, fastperiod, slowperiod, matype)


def aroon(high, low, timeperiod=14):
    """AROON

    The Aroon indicator, developed by Tushar Chande, indicates if a price is
    trending or is in a trading range. It can also reveal the beginning of a
    new trend, its strength and can help anticipate changes from trading
    ranges to trends. AroonDown and the AroonUp indicators are used together
    and combined are called the Aroon indicator.

    - If the Aroon-Up crosses above the Aroon-Down, then a new uptrend may
    start soon. Conversely, if Aroon-Down crosses above the Aroon-Up, then
    a new downtrend may start soon.

    - When Aroon-Up reaches 100, a new uptrend may have begun. If it remains
    persistently between 70 and 100, and the Aroon-Down remains between 0 and
    30, then a new uptrend is underway.

    - When Aroon-Down reaches 100, a new downtrend may have begun. If it remains
    persistently between 70 and 100, and the Aroon-Up remains between 0 and
    30, then a new downtrend is underway. When Aroon-Up and Aroon-Down move
    in parallel (horizontal, sloping up or down) with each other at roughly
    the same level, then price is range trading or consolidating.

    Aroon-Up = [(Period Specified – Periods Since the Highest High within Period Specified) / Period Specified] x 100
    Aroon-Down = [(Period Specified – Periods Since the Lowest Low for Period Specified) / Period Specified] x 100

    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
        aroondown,
        aroonup
    """
    return AROON(high, low, timeperiod)


def aroonosc(high, low, timeperiod=14):
    """Aroon Oscillator (AROON振荡指标)

    The Aroon Oscillator is a trend-following indicator that uses
    aspects of the Aroon Indicator (Aroon Up and Aroon Down) to
    gauge the strength of a current trend and the likelihood that
    it will continue. Readings above zero indicate that an uptrend
    is present, while readings below zero indicate that a downtrend
    is present. Traders watch for zero line crossovers to signal
    potential trend changes. They also watch for big moves, above
    50 or below -50 to signal strong price moves.

    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
    """
    return AROONOSC(high, low, timeperiod)


def bop(opn, high, low, close):
    """Balance Of Power:

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return BOP(opn, high, low, close)


def cci(high, low, close, timeperiod=14):
    """Commodity Channel Index: (商品渠道指数)

    Developed by Donald Lambert, the Commodity Channel Index​ (CCI)
    is a momentum-based oscillator used to help determine when an
    investment vehicle is reaching a condition of being overbought
    or oversold. It is also used to assess price trend direction
    and strength. This information allows traders to determine if
    they want to enter or exit a trade, refrain from taking a trade,
    or add to an existing position. In this way, the indicator can
    be used to provide trade signals when it acts in a certain way.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return CCI(high, low, close, timeperiod)


def cmo(close, timeperiod=14):
    """Chande Momentum Oscillator 钱德动量振荡器

    The Chande Momentum Oscillator (CMO) is a technical momentum
    indicator developed by Tushar Chande. The CMO indicator is
    created by calculating the difference between the sum of all
    recent higher closes and the sum of all recent lower closes and
    then dividing the result by the sum of all price movement over
    a given time period. The result is multiplied by 100 to give
    the -100 to +100 range. The defined time period is usually 20
    periods.

    - CMO indicates overbought conditions when it reaches the 50
    level and oversold conditions when it reaches −50. You can
    also look for signals based on the CMO crossing above and
    below a signal line composed of a 9-period moving average of
    the 20 period CMO.

    - CMO measures the trend strength. The higher the absolute
    value of the CMO, the stronger the trend. Lower absolute
    values of the CMO indicate sideways trading ranges.

    - CMO often forms chart patterns which may not show on the
    underlying price chart, such as double tops and bottoms and
    trend config_lines. Also look for support or resistance on the CMO.

    - If underlying prices make a new high or low that is not
    confirmed by the CMO, the divergence can signal a price reversal.

    Calculation:
    CMO = 100 * ((Su - Sd)/ ( Su + Sd ) )
    Where:
    Su = Sum of the difference between the current close and previous
    close on up days for the specified period. Up days are days when
    the current close is greater than the previous close.
    Sd = Sum of the absolute value of the difference between the
    current close and the previous close on down days for the specified
    period. Down days are days when the current close is less than the
    previous close.

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return CMO(close, timeperiod)


def dx(high, low, close, timeperiod=14):
    """Directional Movement Index 方向运动指数:

    The Directional Movement Index (DMI) assists in determining if a security
    is trending and attempts to measure the strength of the trend. The DMI
    disregards the direction of the security. It only attempts to determine
    if there is a trend and that trends strength.
    The indicator is made up of four indicator config_lines:

    - Positive Directional Indicator (+DMI) shows the difference between today’s
    high price and yesterday’s high price. These values are then added up from
    the past 14 periods and then plotted.
    - Negative Directional Indicator (–DMI) shows the difference between today’s
    low price and yesterday’s low price. These values are then summed up from
    the past 14 periods and plotted.
    - Average Directional Movement Index (ADX). ADX is a smoothing of the DX.
    - Average Directional Movement Index Rating (ADXR) is a simple average of
    today’s ADX value and the ADX from 14 periods ago.

    How to use:

    - High and rising levels of the ADX and ADXR indicate a strong trend, either
    up or down, signifying a trend following system may be appropriate. Typically
    if the ADX is above 25 it indicates a strong trend.

    - Low and falling levels of the ADX and ADXR indicate a trendless market.
    Typically if the ADX is below 20 it indicates a trendless market.

    - A buy signal is given when DMI+ crosses above DMI-. A sell signal is given
    when DMI- crosses above DMI+. The ADX and ADXR config_lines are then used to measure
    the strength of these signals.

    Calculation
    Calculate the True Range, +DI, and –DI for each period:
    True Range is the greater of:
    Current High – Current Low
    Absolute value of Current High – Previous Close
    Absolute value of Current Low – Previous Close

    +DI
    IF Current High – Previous High > Previous Low – Current Low
        THEN +DI = the greater of Current High – Previous High OR 0

    -DI
    IF Previous Low – Current Low > Current High – Previous High
        THEN –DI = the greater of Previous Low – Current Low OR 0

    IF +DI AND -DI are both negative
        THEN both +DI and –DI = 0

    IF +DI AND -DI are both positive AND +DI > -DI
        THEN +DI = Current High – Previous High AND –DI = 0
    Else IF +DI < -DI
        THEN +DI = 0 AND –DI = Previous Low – Current Low
        Smooth the True Range, +DI, and –DI using Wilder’s smoothing technique.
        Divide the smoothed +DI by the smoothed True Range and multiply by 100 (this is
        the +DI that is plotted for the specified period).

    Divide the smoothed –DI by the smooth True Range and multiply by 100 (this is the
    –DI that is plotted for the specified period).

    Next calculate the Directional Movement Index (DX) which equals the (absolute
    value of the smoothed +DI – the smoothed –DI) /( the sum of the smoothed +DI and
    smoothed –DI )and multiply by 100.

    Next calculate the Average Directional Index (ADX). The first value for ADX is an
    average of the DX over the specified period. The following values are smoothed by
    multiplying the previous ADX value by the specified period – 1, adding the current
    DX value, and dividing this total by the period specified.

    Finally the Directional Movement Rating (ADXR) is calculated by the averaging the
    current ADX and the ADX value n-periods ago.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return DX(high, low, close, timeperiod)


def macd(close, fastperiod=12, slowperiod=26, signalperiod=9):  # TODO: TA-Lib free
    """Moving Average Convergence/Divergence:

    The Moving Average Convergence/Divergence indicator is a momentum oscillator
    primarily used to trade trends. Although it is an oscillator, it is not
    typically used to identify over bought or oversold conditions. It appears on
    the chart as two config_lines which oscillate without boundaries. The crossover of
    the two config_lines give trading signals similar to a two moving average system.

    - MACD crossing above zero is considered bullish, while crossing below zero
    is bearish. Secondly, when MACD turns up from below zero it is considered
    bullish. When it turns down from above zero it is considered bearish.

    - When the MACD line crosses from below to above the signal line, the indicator
    is considered bullish. The further below the zero line the stronger the signal.

    - When the MACD line crosses from above to below the signal line, the indicator
    is considered bearish. The further above the zero line the stronger the signal.

    - During trading ranges the MACD will whipsaw, with the fast line crossing back
    and forth across the signal line. Users of the MACD generally avoid trading in
    this situation or close positions to reduce volatility within the portfolio.

    - Divergence between the MACD and the price action is a stronger signal when it
    confirms the crossover signals.

    Calculation
    An approximated MACD can be calculated by subtracting the value of a 26 period
    Exponential Moving Average (EMA) from a 12 period EMA. The shorter EMA is
    constantly converging toward, and diverging away from, the longer EMA. This
    causes MACD to oscillate around the zero level. A signal line is created with
    a 9 period EMA of the MACD line.

    Parameters
    ----------
        close: float,收盘价
        fastperiod:
        slowperiod:
        signalperiod:

    Return
    ------
        macd,
        macdsignal,
        macdhist
    """
    return MACD(close, fastperiod, slowperiod, signalperiod)


def macdext(close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0):
    """MACD with controllable MA type

    MACD extention: different ma types can be applied.

    Parameters
    ----------
        close: float,收盘价
        fastperiod:
        fastmatype:
        slowperiod:
        slowmatype:
        signalperiod:
        signalmatype:

    Return
    ------
        :macd,
        :macdsignal,
        :macdhist
    """
    return MACDEXT(close, fastperiod, fastmatype, slowperiod, slowmatype, signalperiod, signalmatype)


def macdfix(close, signalperiod=9):
    """Moving Average Convergence/Divergence Fix 12/26

    Parameters
    ----------
        close: float,收盘价
        signalperiod:

    Return
    ------
        macd,
        macdsignal,
        macdhist
    """
    return MACDFIX(close, signalperiod)


def mfi(high, low, close, volume, timeperiod=14):
    """Money Flow Index (货币流向指标):

    The Money Flow Index (MFI) is a momentum indicator that measures the
    flow of money into and out of a security over a specified period of time.
    It is related to the Relative Strength Index (RSI) but incorporates volume,
    whereas the RSI only considers price. The MFI is calculated by accumulating
    positive and negative Money Flow values (see Money Flow), then creating a
    Money Ratio. The Money Ratio is then normalized into the MFI oscillator
    form.

    - Oversold levels typically occur below 20 and overbought levels typically
    occur above 80. These levels may change depending on market conditions.
    Level config_lines should cut across the highest peaks and the lowest troughs.
    Oversold/Overbought levels are generally not reason enough to buy/sell; and
    traders should consider additional technical analysis or research to confirm
    the security's turning point. Keep in mind, during strong trends, the MFI
    may remain overbought or oversold for extended periods.

    - If the underlying price makes a new high or low that isn't confirmed by
    the MFI, this divergence can signal a price reversal.

    Calculation
    The Money Flow Index requires a series of calculations.
    - First, the period's Typical Price is calculated.
    - Typical Price = (High + Low + Close)/3
    - Next, Money Flow (not the Money Flow Index) is calculated by multiplying
    the period's Typical Price by the volume.
    - Money Flow = Typical Price * Volume
    - If today's Typical Price is greater than yesterday's Typical Price, it is
    considered Positive Money Flow. If today's price is less, it is considered
    Negative Money Flow.
    - Positive Money Flow is the sum of the Positive Money over the specified
    number of periods.
    - Negative Money Flow is the sum of the Negative Money over the specified
    number of periods.
    - The Money Ratio is then calculated by dividing the Positive Money Flow by
    the Negative Money Flow.
    - Money Ratio = Positive Money Flow / Negative Money Flow
    - Finally, the Money Flow Index is calculated using the Money Ratio.

    Parameters
    ----------
        high: float, 最高价
        low: float, 最低价
        close: float,收盘价
        volume:
        timeperiod:

    Return
    ------
    """
    return MFI(high, low, close, volume, timeperiod)


def minus_di(high, low, close, timeperiod=14):
    """Minus Directional Indicator / Negative Directional Indicator:

    The Negative Directional Indicator (-DI) measures the presence of a downtrend
    and is part of the Average Directional Index (ADX). If -DI is sloping upward,
    it's a sign that the price downtrend is getting stronger. This indicator is
    nearly always plotted along with the Positive Directional Indicator (+DI).

    - When the Negative Directional Indicator (-DI) moves up, and is above the
    Postive Directional Indicator (+DI), then the price downtrend is getting
    stronger.

    - When -DI is moving down, and below the +DI, then the price uptrend is
    strengthening.

    - When +DI and -DI crossover, it indicates the possibility of a new trend.
    If -DI crosses above the +DI then a new downtrend could be starting.

    Calculate the Negative Directional Indicator (+DI)
    - Calculate -DI by finding -DM and True Range (TR).
    - -DM = Prior Low - Current Low
    - Any period is counted as a -DM if the Previous Low - Current Low >
    Current High - Previous High. Use +DM when Current High - Previous High
    > Previous Low - Current Low.
    - TR is the greater of the Current High - Current Low, Current High -
    Previous Close, or Current Low - Previous Close.
    - Smooth the 14-periods of -DM and TR using the formula below. Substitute
    TR for -DM to calculate ATR. [The calculation below shows a smoothed TR
    formula, which is slightly different than the official ATR formula. Either
    formula can be used, but use one consistently].
    - First 14-period -DM = Sum of first 14 -DM readings.
    - Next 14-period -DM value = First 14 -DM value - (Prior 14 DM/14) + Current -DM
    - Next, divide the smoothed -DM value by the smoothed TR (or ATR) value
    to get -DI. Multiply by 100.

    Parameters
    ----------
        high: float, 最高价
        low: float, 最低价
        close: float,收盘价
        timeperiod:

    Return
    ------
    """
    return MINUS_DI(high, low, close, timeperiod)


def minus_dm(high, low, timeperiod=14):
    """Minus Directional Movement / Directional Movement Index:

    The Directional Movement Index, or DMI, is an indicator developed by J. Welles
    Wilder in 1978 that identifies in which direction the price of an asset is moving.
    The indicator does this by comparing prior highs and lows and drawing two config_lines: a
    positive directional movement line (+DI) and a negative directional movement line
    (-DI). An optional third line, called directional movement (DX) shows the
    difference between the config_lines. When +DI is above -DI, there is more upward pressure
    than downward pressure in the price. If -DI is above +DI, then there is more
    downward pressure in the price. This indicator may help traders assess the trend
    direction. Crossovers between the config_lines are also sometimes used as trade signals
    to buy or sell.

    - A +DI line above the -DI line means there is more upward movement than downward movement.

    - A -DI line above the +DI line means there is more downward movement than upward movement.

    - Crossovers can be used to signal emerging trends. For example, the +DI crossing above
    the -DI may signal the start of an uptrend in price.

    - The larger the spread between the two config_lines, the stronger the price trend. If +DI is way
    above -DI the price trend is strongly up. If -DI is way above +DI then the price trend is
    strongly down.

    Calculating the Directional Movement Index (DMI)
    - Calculate +DM, -DM, and True Range (TR) for each period. Typically 14 periods are used.
    - +DM is the Current High - Previous High.
    - -DM is the Previous Low - Current Low.
    - Use +DM when Current High - Previous High is greater than Previous Low - Current Low.
    Use -DM when Previous Low - Current Low is greater than Current High - Previous High.
    - TR is the greater of the Current High - Current Low, Current High - Previous Close, or
    Current Low - Previous Close.
    - Smooth the 14-period averages of +DM, -DM, and TR. Below is the formula for TR. Insert
    the -DM and +DM values to calculate the smoothed averages of those as well.
    - First 14TR = Sum of first 14 TR readings.
    - Next 14TR value = First 14TR - (Prior 14TR/14) + Current TR
    - Next, divide the smoothed +DM value by the smoothed TR value to get +DI. Multiply by 100.
    - Divide the smoothed -DM value by the smoothed TR value to get-DI. Multiply by 100.
    - The optional Directional Movement Index (DX) is +DI minus -DI, divided by the sum of +DI
    and -DI (all absolute values). Multiply by 100.

    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
    """
    return MINUS_DM(high, low, timeperiod)


def mom(close, timeperiod=10):
    """Momentum:

    The momentum indicator identifies when the price is moving upward or downward and
    how strongly. When the first version of the momentum indicator is a positive number,
    the price is above the price "n" periods ago. When it's a negative number, the price
    is below the price "n" periods ago.

    The momentum of a price is very easy to calculate. There are couple different versions
    of the formula, but whichever one is used, the momentum (M) is a comparison between the
    current closing price (CP) and a closing price "n" periods ago (CPn).1 You determine the value of "n."
    M = CP – CPn
    or
    M = (CP / CPn) * 100

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return MOM(close, timeperiod)


def plus_di(high, low, close, timeperiod=14):
    """Plus Directional Indicator / Positive Directional Indicator

    The Positive Directional Indicator (+DI) is a component of the Average
    Directional Index (ADX) and is used to measure the presence of an uptrend.
    When the +DI is sloping upward, it is a signal that the uptrend is getting
    stronger. This indicator is nearly always plotted along with the Negative
    Directional Indicator (-DI).

    - When the Positive Directional Indicator (+DI) is moving up, and above the
    Negative Directional Indicator (-DI), then the price uptrend is strengthening.

    - When the +DI is moving down, and below the -DI, then the price downtrend
    is strengthening.

    - When +DI and -DI crossover, it indicates the possibility of a new trend.
    If -DI crosses above the +DI then a new downtrend could be starting.

    Calculate the Negative Directional Indicator (+DI)
    - Calculate +DI by finding +DM and True Range (TR).
    - +DM = Current High - Previous High.
    - Any period is counted as a +DM if the Current High - Previous High > Previous
    Low - Current Low. Use -DM when Previous Low - Current Low > Current High -
    Previous High.
    - TR is the greater of the Current High - Current Low, Current High - Previous
    Close, or Current Low - Previous Close.
    - Smooth the 14-periods of +DM and TR using the formula below. Substitute TR
    for +DM to calculate ATR. [The calculation below shows a smoothed TR formula,
    which is slightly different than the official ATR formula. Either formula can
    be used, but use one consistently].
    - First 14-period +DM = Sum of first 14 +DM readings.
    - Next 14-period +DM value = First 14 +DM value - (Prior 14 DM/14) + Current +DM
    - Next, divide the smoothed +DM value by the ATR value to get +DI. Multiply by 100.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return PLUS_DI(high, low, close, timeperiod)


def plus_dm(high, low, timeperiod=14):
    """Plus Directional Movement / Positive Directional Movement:

    The Positive Directional Indicator (+DI) is a component of the Average Directional
    Index (ADX) and is used to measure the presence of an uptrend. When the +DI is
    sloping upward, it is a signal that the uptrend is getting stronger. This indicator
    is nearly always plotted along with the Negative Directional Indicator (-DI).

    - When the Positive Directional Indicator (+DI) is moving up, and above the Negative
    Directional Indicator (-DI), then the price uptrend is strengthening.

    - When the +DI is moving down, and below the -DI, then the price downtrend is
    strengthening.

    - Crossovers between the +DI and -DI are sometimes used as trade signals as the
    crossover indicates the possibility of a new trend emerging. For example, the +DI
    crossing above the -DI signals the possibility of a new uptrend and a potential long
    position.

    How to Calculate the Positive Directional Indicator (+DI)
    - Calculate +DI by finding +DM and True Range (TR).
    - +DM = Current High - Previous High.
    - Any period is counted as a +DM if the Current High - Previous High > Previous Low -
    Current Low. Use -DM when Previous Low - Current Low > Current High - Previous High.
    - TR is the greatest of the Current High - Current Low, Current High - Previous Close,
    or Current Low - Previous Close.
    - Smooth the 14-periods of +DM and TR using the formula below. Substitute TR for +DM
    to calculate ATR. [The calculation below shows a smoothed TR formula, which is
    slightly different from the official ATR formula. Either formula can be used, but use
    one consistently].
    - First 14-period +DM = Sum of first 14 +DM readings.
    - Next 14-period +DM value = First 14 +DM value - (Prior 14 DM/14) + Current +DM
    - Next, divide the smoothed +DM value by the ATR value to get +DI. Multiply by 100.

    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
    """
    return PLUS_DM(high, low, timeperiod)


def ppo(close, fastperiod=12, slowperiod=26, matype=0):
    """Percentage Price Oscillator 百分比价格振荡器

    The percentage price oscillator (PPO) is a technical momentum indicator that shows
    the relationship between two moving averages in percentage terms. The moving averages
    periods and type are provided as arguments.

    The PPO is used to compare asset performance and volatility, spot divergence which
    could lead to price reversals, generate trade signals, and help confirm trend direction.
    The PPO is identical to the moving average convergence divergence (MACD) indicator,
    except the PPO measures percentage difference between two EMAs, while the MACD measures
    absolute (dollar) difference. Some traders prefer the PPO because readings are
    comparable between assets with different prices, whereas MACD readings are not comparable.

    - The PPO typical contains two config_lines, the PPO line, and the signal line. The signal line
    is an EMA of PPO, so it moves slower than the PPO.

    - The PPO crossing the signal line is used by some traders as a trade signal. When it
    crosses above from below, that is a buy, when it crosses below from above that is a sell.

    - When the PPO is above zero that helps indicate an uptrend, as the short-term EMA is
    above the longer-term EMA.

    - When the PPO is below zero, the short-term average is below the longer-term average,
    which helps indicate a downtrend.

    Calculation:
    - Calculate the 12-period EMA of the asset's price.
    - Calculate the 26-period EMA of the asset's price.
    - Apply these to the PPO formula to get the current PPO value.
    - Once there are at least nine PPO values, generate the signal line by calculating the
    nine-period EMA of the PPO.
    - To generate a histogram reading, subtract the current PPO value from the current signal
    line value. The histogram is an optional visual representation of the distance between
    these two config_lines.

    close: float,收盘价
    fastperiod:
    slowperiod:
    matype:

    Return
    ------
    """
    return PPO(close, fastperiod, slowperiod, matype)


def roc(close, timeperiod=10):
    """Rate of change : ((price/prevPrice)-1)*100

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ROC(close, timeperiod)


def rocp(close, timeperiod=10):
    """Rate of change Percentage: (price-prevPrice)/prevPrice

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ROCP(close, timeperiod)


def rocr(close, timeperiod=10):
    """Rate of change ratio: (price/prevPrice)

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ROCR(close, timeperiod)


def rocr100(close, timeperiod=10):
    """Rate of change ratio 100 scale: (price/prevPrice)*100

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ROCR100(close, timeperiod)


def rsi(close, timeperiod=14):
    """Relative Strength Index:

    The relative strength index (RSI) is a momentum indicator used in technical analysis
    that measures the magnitude of recent price changes to evaluate overbought or oversold
    conditions in the price of a stock or other asset. The RSI is displayed as an
    oscillator (a line graph that moves between two extremes) and can have a reading from
    0 to 100. The indicator was originally developed by J. Welles Wilder Jr. and introduced
    in his seminal 1978 book, "New Concepts in Technical Trading Systems."

    - An asset is usually considered overbought when the RSI is above 70% and oversold
    when it is below 30%.

    

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return RSI(close, timeperiod)


def stoch(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0):
    """Stochastic:

    The stochastic indicator is a momentum indicator developed by George C. Lane in the 1950s,
    which shows the position of the most recent closing price relative to the previous high-low
    range. The indicator measures momentum by comparing the closing price with the previous
    trading range over a specific period of time.

    The stochastic indicator is widely used in the Forex community. It consists of two config_lines:
    the indicator line %K, and the signal or trigger line %D. The stochastic indicator can be
    used to identify oversold and overbought conditions, as well as to spot divergences between
    the price and the indicator.

    - A reading above 80 is usually considered as overbought, while a reading below 20 is
    considered oversold. However, the price can remain in overbought and oversold conditions
    for a long period of time, especially during strong up- and downtrends.

    - A divergence occurs when the price “diverges” from the indicator, i.e. the price makes
    lower lows while the indicator makes higher lows, or the price makes higher highs while the
    indicator makes lower highs.

    - As with any momentum indicator, traders should wait for additional confirmation signals
    to enter a trade, as these types of indicators can occasionally give false signals.

    The stochastic indicator is calculated using the following formula:

    %K = (Most Recent Closing Price - Lowest Low) / (Highest High - Lowest Low) × 100

    %D = 3-day SMA of %K

    Lowest Low = the lowest low of the specified time period

    Highest High = the highest high of the specified time period

    Parameters
    ----------
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    fastk_period:
    slowk_period:
    slowk_matype:
    slowd_period:
    slowd_matype:

    Return
    ------
        slowk,
        slowd
    """
    return STOCH(high, low, close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)


def stochf(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0):
    """Stochastic Fast:

    The "fast" stochastic indicator is taken as %D = 3-period moving average of %K. The
    general theory serving as the foundation for this indicator is that in a market
    trending upward, prices will close near the high, and in a market trending downward,
    prices close near the low.

    Parameters
    ----------
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    fastk_period:
    fastd_period:
    fastd_matype:

    Return
    ------
        fastk,
        fastd
    """
    return STOCHF(high, low, close, fastk_period, fastd_period, fastd_matype)


def stochrsi(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0):
    """Stochastic Relative Strength Index:

    The Stochastic RSI (StochRSI) is an indicator used in technical analysis that ranges
    between zero and one (or zero and 100 on some charting platforms) and is created by
    applying the Stochastic oscillator formula to a set of relative strength index (RSI)
    values rather than to standard price data. Using RSI values within the Stochastic
    formula gives traders an idea of whether the current RSI value is overbought or
    oversold.

    - A StochRSI reading above 0.8 is considered overbought, while a reading below 0.2
    is considered oversold. On the zero to 100 scale, above 80 is overbought, and below
    20 is oversold.

    - Overbought doesn't necessarily mean the price will reverse lower, just like
    oversold doesn't mean the price will reverse higher. Rather the overbought and
    oversold conditions simply alert traders that the RSI is near the extremes of its
    recent readings.

    - A reading of zero means the RSI is at its lowest level in 14 periods (or whatever
    lookback period is chosen). A reading of 1 (or 100) means the RSI is at the highest
    level in the last 14 periods.

    - Other StochRSI values show where the RSI is relative to a high or low

    How to Calculate the Stochastic RSI
    The StochRSI is based on RSI readings. The RSI has an input value, typically 14,
    which tells the indicator how many periods of data it is using in its calculation.
    These RSI levels are then used in the StochRSI formula.

    - Record RSI levels for 14 periods.

    - On the 14th period, note the current RSI reading, the highest RSI reading, and
    lowest RSI reading. It is now possible to fill in all the formula variables for
    StochRSI.

    - On the 15th period, note the current RSI reading, highest RSI reading, and lowest
    reading, but only for the last 14 period (not the last 15). Compute the new StochRSI.

    - As each period ends compute the new StochRSI value, only using the last 14 RSI
    values.

    close: float,收盘价
    timeperiod:
    fastk_period:
    fastd_period:
    fastd_matype:

    Return
    ------
    fastk,
    fastd
    """
    return STOCHRSI(close, timeperiod, fastk_period, fastd_period, fastd_matype)


def trix(close, timeperiod=30):  # TODO: TA-Lib free
    """1-day Rate-Of-Change (ROC) of a Triple Smooth EMA

    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return TRIX(close, timeperiod)


def ultosc(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28):
    """Ultimate Oscillator:

    The Ultimate Oscillator is a technical indicator that was developed by Larry Williams
    in 1976 to measure the price momentum of an asset across multiple timeframes. By using
    the weighted average of three different timeframes the indicator has less volatility
    and fewer trade signals compared to other oscillators that rely on a single timeframe.
    Buy and sell signals are generated following divergences. The Ultimately Oscillator
    generates fewer divergence signals than other oscillators due to its multi-timeframe
    construction.

    - The indicator uses three timeframes in its calculation: seven, 14, and 28 periods.

    - The shorter timeframe has the most weight in the calculation, while the longer
    timeframe has the least weight.

    - Buy signals occur when there is bullish divergence, the divergence low is below 30
    on the indicator, and the oscillator then rises above the divergence high.

    - A sell signal occurs when there is bearish divergence, the divergence high is above
    70, and the oscillator then falls below the divergence low.

    How to Calculate the Ultimate Oscillator

    - Calculate the Buying Pressure (BP) which is the close price of the period less the
    low of that period or prior close, whichever is lower. Record these values for each
    period as they will be summed up over the last seven, 14, and 28 periods to create
    BP Sum.

    - Calculate the True Range (TR) which is the current period's high or the prior close,
    whichever is higher, minus the lowest value of the current period's low or the prior
    close. Record these values for each period as they will be summed up over the last
    seven, 14, and 28 periods to create TR Sum.

    - Calculate Average7, 14, and 28 using the BP and TR Sums calculations from steps one
    and two. For example, the Average7 BP Sum is the calculated BP values added together
    for the last seven periods.

    - Calculate the Ultimate Oscillator using the Average7, 14, and 28 values. Average7
    has a weight of four, Average14 has a weight of two, and Average28 has a weight of
    one. Sum the weights in the denominator (in this case, the sum is seven, or 4+2+1).
    Multiply by 100 when other calculations are complete.

    Ultimate Oscillator 是一种技术指标，由 Larry Williams 于 1976 年开发，用于衡量资产在多个时间
    范围内的价格动量。通过使用三个不同时间框架的加权平均值，与其他依赖单一时间框架的振荡器相比，该指标的
    波动性和交易信号更少。出现分歧后会产生买入和卖出信号。由于其多时间框架结构，最终振荡器产生的发散信号
    少于其他振荡器。

    - 该指标在其计算中使用三个时间框架：7、14 和 28 个周期。

    - 较短的时间范围在计算中的权重最大，而较长的时间范围的权重最小。

    - 当出现看涨背离时出现买入信号，指标上背离低点低于 30，然后震荡指标升至背离高点上方。

    - 当出现看跌背离时出现卖出信号，背离高点高于 70，然后震荡指标跌破背离低点。

    如何计算终极振荡器

    - 计算买入压力 (BP)，即该时段的收盘价减去该时段的低点或前一收盘价，以较低者为准。记录每个时期的这些值，
    因为它们将在过去 7 个、14 个和 28 个时期相加，以创建 BP 总和。

    - 计算真实范围 (TR)，即当前时段的高点或前收盘价，以较高者为准，减去当前时段的低点或前收盘价的最低值。
    记录每个时期的这些值，因为它们将在过去 7 个、14 个和 28 个时期相加，以创建 TR Sum。

    - 使用第一步和第二步中的 BP 和 TR 总和计算来计算平均值 7、14 和 28。例如，Average7 BP Sum 是过去
    七个期间计算的 BP 值相加。

    - 使用平均 7、14 和 28 值计算终极振荡器。平均 7 的权重为 4，平均 14 的权重为 2，平均 28 的权重为 1。
    将分母中的权重相加（在这种情况下，和为 7，或 4+2+1）。其他计算完成后乘以 100。

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod1:
    timeperiod2:
    timeperiod3:

    Return
    ------
    """
    return ULTOSC(high, low, close, timeperiod1, timeperiod2, timeperiod3)


def willr(high, low, close, timeperiod=14):
    """Williams' %R:

    Williams %R, also known as the Williams Percent Range, is a type of momentum
    indicator that moves between 0 and -100 and measures overbought and oversold levels.
    The Williams %R may be used to find entry and exit points in the market. The
    indicator is very similar to the Stochastic oscillator and is used in the same way.
    It was developed by Larry Williams and it compares a stock’s closing price to the
    high-low range over a specific period, typically 14 days or periods.

    Williams %R moves between zero and -100.
    - A reading above -20 is overbought.

    - A reading below -80 is oversold.

    - An overbought or oversold reading doesn't mean the price will reverse. Overbought
    simply means the price is near the highs of its recent range, and oversold means the
    price is in the lower end of its recent range.

    - Can be used to generate trade signals when the price and the indicator move out of
    overbought or oversold territory.

    How to Calculate the Williams %R

    The Williams %R is calculated based on price, typically over the last 14 periods.

    - Record the high and low for each period over 14 periods.

    - On the 14th period, note the current price, the highest price, and lowest price.
    It is now possible to fill in all the formula variables for Williams %R.

    - On the 15th period, note the current price, highest price, and lowest price, but
    only for the last 14 periods (not the last 15). Compute the new Williams %R value.

    - As each period ends compute the new Williams %R, only using the last 14 periods
    of data.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return WILLR(high, low, close, timeperiod)


# =============================================================
# Volume & Price Indicators 量价指标函数


def ad(high, low, close, volume):
    """Chaikin A/D Line:

    Developed by Marc Chaikin, the Accumulation Distribution Line is a volume-based
    indicator designed to measure the cumulative flow of money into and out of a security.
    Chaikin originally referred to the indicator as the Cumulative Money Flow Line. As
    with cumulative indicators, the Accumulation Distribution Line is a running total of
    each period's Money Flow Volume. First, a multiplier is calculated based on the
    relationship of the close to the high-low range. Second, the Money Flow Multiplier is
    multiplied by the period's volume to come up with a Money Flow Volume. A running total
    of the Money Flow Volume forms the Accumulation Distribution Line. Chartists can use
    this indicator to affirm a security's underlying trend or anticipate reversals when
    the indicator diverges from the security price.

    Chaikin A/D Line measures the Advance/Decline of the market. This script takes that
    data to calculate a user-defined Moving Average and uses the direction of the MA to
    signal buys and sells.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    volume:

    Return
    ------
    """
    return AD(high, low, close, volume)


def adosc(high, low, close, volume, fastperiod=3, slowperiod=10):
    """Chaikin A/D Oscillator:

    The Chaikin oscillator is named for its creator Marc Chaikin. The oscillator measures
    the accumulation-distribution line of moving average convergence-divergence (MACD).
    To calculate the Chaikin oscillator, subtract a 10-day exponential moving average
    (EMA) of the accumulation-distribution line from a 3-day EMA of the
    accumulation-distribution line. This measures momentum predicted by oscillations
    around the accumulation-distribution line.

    - The Chaikin Indicator applies MACD to the accumulation-distribution line rather
    than closing price.

    - A cross above the accumulation-distribution line indicates that market players are
    accumulating shares, securities or contracts, which is typically bullish.

    How to Calculate the Chaikin Oscillator?
    Calculate the accumulation-distribution line (ADL) in three steps. The fourth step
    yields the Chaikin Oscillator.

    - Calculate the Money Flow Multiplier (N).

    - Multiply the Money Flow Multiplier (N) by volume to calculate Money Flow Volume (N).

    - List a running total of N to draw the accumulation-distribution line (ADL).

    - Compute the difference between 10 period and 3 period exponential moving averages
    to calculate the Chaikin oscillator.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    volume:
    fastperiod:
    slowperiod:

    Return
    ------
    """
    return ADOSC(high, low, close, volume, fastperiod, slowperiod)


def obv(close, volume):
    """On-Balance Volume:

    On-balance volume (OBV) is a technical trading momentum indicator that uses volume
    flow to predict changes in stock price. Joseph Granville first developed the OBV metric
    in the 1963 book Granville's New Key to Stock Market Profits.

    - On-balance volume (OBV) is a technical indicator of momentum, using volume changes to
    make price predictions.
    - OBV shows crowd sentiment that can predict a bullish or bearish outcome.
    - Comparing relative action between price bars and OBV generates more actionable signals
    than the green or red volume histograms commonly found at the bottom of price charts.

    Calculating OBV
    On-balance volume provides a running total of an asset's trading volume and indicates
    whether this volume is flowing in or out of a given security or currency pair. The OBV
    is a cumulative total of volume (positive and negative). There are three rules
    implemented when calculating the OBV. They are:

    - If today's closing price is higher than yesterday's closing price, then:
    Current OBV = Previous OBV + today's volume

    - If today's closing price is lower than yesterday's closing price, then:
    Current OBV = Previous OBV - today's volume

    - If today's closing price equals yesterday's closing price, then:
    Current OBV = Previous OBV

    close: float,收盘价
    volume:

    Return
    ------
    """
    return OBV(close, volume)


# ===========================
# Volatility Indicators


def atr(high, low, close, timeperiod=14):
    """Average True Range:

    Average True Range (ATR) is the average of true ranges over the specified period. ATR
    measures volatility, taking into account any gaps in the price movement. Typically,
    the ATR calculation is based on 14 periods, which can be intraday, daily, weekly, or
    monthly. To measure recent volatility, use a shorter average, such as 2 to 10 periods.
    For longer-term volatility, use 20 to 50 periods.

    - An expanding ATR indicates increased volatility in the market, with the range of each
    bar getting larger. A reversal in price with an increase in ATR would indicate strength
    behind that move. ATR is not directional so an expanding ATR can indicate selling
    pressure or buying pressure. High ATR values usually result from a sharp advance or
    decline and are unlikely to be sustained for extended periods.

    - A low ATR value indicates a series of periods with small ranges (quiet days). These
    low ATR values are found during extended sideways price action, thus the lower
    volatility. A prolonged period of low ATR values may indicate a consolidation area and
    the possibility of a continuation move or reversal.

    - ATR is very useful for stops or entry triggers, signaling changes in volatility.
    Whereas fixed dollar- point or percentage stops will not allow for volatility, the ATR
    stop will adapt to sharp price moves or consolidation areas, which can trigger an
    abnormal price movement in either direction. Use a multiple of ATR, such as 1.5 x ATR,
    to catch these abnormal price moves.

    Calculation
    ATR = (Previous ATR * (n - 1) + TR) / n
    Where:
    ATR = Average True Range
    n = number of periods or bars
    TR = True Range
    The True Range for today is the greatest of the following:
        - Today's high minus today's low
        - The absolute value of today's high minus yesterday's close
        - The absolute value of today's low minus yesterday's close

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return ATR(high, low, close, timeperiod)


def natr(high, low, close, timeperiod=14):
    """Normalized Average True Range:

    Normalized Average True Range (NATR) attempts to normalize the average true range values
    across instruments by using the formula below: float, 最低价

    Formula

    - NATR = ATR(n) / Close * 100

    Where: ATR(n) = Average True Range over ‘n’

 periods.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价
    timeperiod:

    Return
    ------
    """
    return NATR(high, low, close, timeperiod)


def trange(high, low, close):
    """True Range:

    Welles Wilder described these calculations to determine the trading range for a stock or
    commodity. True Range is defined as the largest of the following:

    - The distance from today's high to today's low.
    - The distance from yesterday's close to today's high.
    - The distance from yesterday's close to today's low.

    The raw True Range is then smoothed (a 14-period smoothing is common) to give an Average
    True Range (ATR). The True Range can be smoothed using a variety of moving average types,
    including Simple, Exponential, Welles Wilder, etc.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return TRANGE(high, low, close)


# ===========================
# Price Transform Functions


def avgprice(opn, high, low, close):
    """Average Price:

    *To be tested*
    In basic mathematics, an average price is a representative measure of a range of prices
    that is calculated by taking the sum of the values and dividing it by the number of
    prices being examined.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return AVGPRICE(opn, high, low, close)


def medprice(high, low):
    """Median Price:

    *To be tested*
    The Median Price indicator is simply the midpoint of each day's price. The Typical Price
    and Weighted Close are similar indicators. The Median Price indicator provides a simple,
    single-line chart of the day's "average price." This average price is useful when you
    want a simpler view of prices.

    high: float, 最高价
    low: float, 最低价

    Return
    ------
    """
    return MEDPRICE(high, low)


def typprice(high, low, close):
    """Typical Price:

    The Typical Price indicates an average of each day’s price.

    Typical Price is calculated by adding the high, low, and closing prices together, and
    then dividing by three. The result is the average, or typical price.

    - Typical Price = ( High + Low + Close ) / 3

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return TYPPRICE(high, low, close)


def wclprice(high, low, close):
    """Weighted Close Price:

    The Weighted Close indicator is simply an average of each day's price. It gets its name
    from the fact that extra weight is given to the closing price. The Median Price and
    Typical Price are similar indicators. ... The result is the average price with extra
    weight given to the closing price.

    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return WCLPRICE(high, low, close)


# =====================================
# Cycle Indicators


def ht_dcperiod(close):
    """Hilbert Transform - Dominant Cycle Period:

    The Hilbert Transform is a technique used to generate inphase and quadrature components
    of a de-trended real-valued "analytic-like" signal (such as a Price Series) in order to
    analyze variations of the instantaneous phase and amplitude. HTPeriod (or MESA
    Instantaneous Period) returns the period of the Dominant Cycle of the analytic signal as
    generated by the Hilbert Transform. The Dominant Cycle can be thought of as being the
    "most likely" period (in the range of 10 to 40) of a sine function of the Price Series.

    The HTPeriod at a specific bar gives the current Hilbert Transform Period as
    instantaneously measured at that bar in the range of 10 to 40. It is meaningful only
    during a cyclic period of the analytic signal waveform (price series) being measured.
    The HTPeriod, or one of its sub-periods, is often used to adjust other indicators; for
    example, Stochastics and RSIs work best when using a half cycle period to peak their
    performance. Similarly other indicators can be made to be adaptive by using the HTPeriod,
    or one of its sub-periods, as the period of the indicator.

    The basic flow and simplified pseudo code for the computation for the Dominant Cycle Period is:

    Compute the Hilbert Transform
    {Detrend Price}
    {Compute InPhase and Quadrature components}

    Compute the Period of the Dominant Cycle
    {Use ArcTangent to compute the current phase}
    {Resolve the ArcTangent ambiguity}
    {Compute a differential phase, resolve phase wraparound, and limit delta phase errors}
    {Sum DeltaPhases to reach 360 degrees. The sum is the instantaneous period.}
    {Resolve Instantaneous Period errors and smooth}

    Return the Hilbert Transform Period measured at the current bar

    close: float,收盘价

    Return
    ------
    """
    return HT_DCPERIOD(close)


def ht_dcphase(close):
    """Hilbert Transform - Dominant Cycle Phase:

    The Hilbert Transform is a technique used to generate inphase and quadrature components
    of a de-trended real-valued "analytic-like" signal (such as a Price Series) in order to
    analyze variations of the instantaneous phase and amplitude.. HTDCPhase returns the
    Hilbert Transform Phase of the Dominant Cycle. The Dominant Cycle Phase lies in the
    range of 0 to 360 degrees. The Hilbert Transform Sine is just the sine of the DC Phase.

    The DC Phase at a specific bar gives the phase position from 0 to 360 degrees within the
    current Hilbert Transform Period instantaneously measured at that bar. The HTSin is the
    sine of the DC Phase at a specific bar. The HTLeadSin is the sine of the DC Phase at a
    specific bar. They are most often used together to identify cyclic turning points.

    The basic flow and simplified pseudo code for the computation for the Dominant Cycle
    Phase as part of the computation of the Dominant Cycle is:

    Compute the Hilbert Transform
        {Detrend Price}
        {Compute InPhase and Quadrature components}
    Compute the Period of the Dominant Cycle
        {Use ArcTangent to compute the current phase}
        {Resolve the ArcTangent ambiguity}
        {Compute a differential phase, resolve phase wraparound, and limit delta phase errors}
        {Sum DeltaPhases to reach 360 degrees.  The sum is the instantaneous period.}
        {Resolve Instantaneous Period errors and smooth}
    Compute Dominant Cycle Phase
    Compute the Sine of the Dominant Cycle Phase
    Return the Sine of the Dominant Cycle Phase at the current bar of the Hilbert Transform
    Period measured at that bar

    The basic flow and simplified pseudo code for the computation for the HTLeadSin is:

    Compute the Hilbert Transform
        {Detrend Price}
        {Compute InPhase and Quadrature components}
    Compute the Period of the Dominant Cycle
        {Use ArcTangent to compute the current phase}
        {Resolve the ArcTangent ambiguity}
        {Compute a differential phase, resolve phase wraparound, and limit delta phase errors}
        {Sum DeltaPhases to reach 360 degrees.  The sum is the instantaneous period.}
        {Resolve Instantaneous Period errors and smooth}
    Compute Dominant Cycle Phase
    Compute the Sine of the Dominant Cycle Phase
    Advance the Sine by 45 degrees to compute the HT Lead Sine
    Return the Lead Sine of the Dominant Cycle Phase at the current bar of the Hilbert Transform Period measured at that bar

    close: float,收盘价

    Return
    ------
    """
    return HT_DCPHASE(close)


def ht_phasor(close):
    """Hilbert Transform - Phasor Components

    close: float,收盘价

    Return
    ------
    inphase,
    quadrature
    """
    return HT_PHASOR(close)


def ht_sine(close):
    """Hilbert Transform - SineWave

    close: float,收盘价

    Return
    ------
    """
    return HT_SINE(close)


def ht_trendmode(close):
    """Hilbert Transform - Trend vs Cycle Mode

    close: float,收盘价

    Return
    ------
    """
    return HT_TRENDMODE(close)


# =================================================
# Pattern Recognition


def cdl2crows(opn, high, low, close):
    """Two Crows:

    The Two Crows is a three-line bearish reversal candlestick pattern. The pattern requires
    confirmation, that is, the following candles should break a trendline or the nearest
    support area which may be formed by the first candle's line. If the pattern is not
    confirmed it may act only as a temporary pause within an uptrend.

    Forecast: bearish reversal
    Trend prior to the pattern: uptrend
    Opposite pattern: none
    See Also: Upside Gap Two Crows

    Construction:

    First candle
    - a candle in an uptrend
    - white body
    Second candle
    - black body
    - the closing price above the prior closing price (gap between bodies)
    Third candle
    - black body
    - the opening price within the prior body
    - the closing price within the body of the first line (gap close)

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL2CROWS(opn, high, low, close)


def cdl3blackcrows(opn, high, low, close):
    """Three Black Crows:

    Three black crows indicate a bearish candlestick pattern that predicts the reversal of
    an uptrend. Candlestick charts show the opening, high, low, and the closing price on a
    particular security. For stocks moving higher the candlestick is white or green. When
    moving lower, they are black or red.

    - Three black crows are a reliable reversal pattern when confirmed by other technical
    indicators like the relative strength index (RSI).

    - The size of the three black crows and the shadow can be used to judge whether the
    reversal is at risk of a retracement.

    - The opposite pattern of three black crows is three white soldiers indicating a
    reversal of a downtrend.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL3BLACKCROWS(opn, high, low, close)


def cdl3inside(opn, high, low, close):
    """Three Inside Up/Down:

    Three inside up and three inside down are three-candle reversal patterns that appear
    on candlestick charts. The pattern requires three candles to form in a specific sequence,
    showing that the current trend has lost momentum and a move in the other direction might
    be starting.

    - The three inside up pattern is a bullish reversal composed of a large down candle,
    a smaller up candle contained within the prior candle, and then another up candle
    that closes above the close of the second candle.

    - The three inside down pattern is a bearish reversal composed of a large up candle,
    a smaller down candle contained within the prior candle, then another down candle
    that closes below the close of the second candle.

    - The pattern is short-term in nature, and may not always result in a significant or
    even minor trend change.

    - Consider using the pattern within the context of an overall trend. For example, use
    the three inside up during a pullback in an overall uptrend

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL3INSIDE(opn, high, low, close)


def cdl3linestrike(opn, high, low, close):
    """Three-Line Strike:

    The bullish three line strike reversal pattern carves out three black candles within a
    downtrend. Each bar posts a lower low and closes near the intrabar low. The fourth bar
    opens even lower but reverses in a wide-range outside bar that closes above the high
    of the first candle in the series. The opening print also marks the low of the fourth
    bar. According to Bulkowski, this reversal predicts higher prices with an 83% accuracy
    rate.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL3LINESTRIKE(opn, high, low, close)


def cdl3outside(opn, high, low, close):
    """Three Outside Up/Down:

    The three outside up and three outside down describe a pair of three-candle reversal
    patterns that appear on candlestick charts. In either, a dark candlestick is followed
    by two white ones, or vice-versa.

    - Three outside up/down are patterns of three candlesticks that often signal a reversal
    in trend.

    - The three outside up and three outside down patterns are characterized by one
    candlestick immediately followed by two candlesticks of opposite shading.

    - Each tries to leverage market psychology in order to read near-term changes in sentiment.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL3OUTSIDE(opn, high, low, close)


def cdl3starsinsouth(opn, high, low, close):
    """Three Stars In The South:

    Forecast: bullish reversal
    Trend prior to the pattern: downtrend
    Opposite pattern: none

    Construction:

    First candle
    a candle in a downtrend
    black body
    long lower shadow
    Second candle
    black body
    the opening below the prior opening
    the closing below or at the prior closing
    the low above the prior low
    Third candle
    a marubozu candle with black body
    appears as a short line
    a candle is located within the prior candle

    The three stars in the south is a three-candle bullish reversal pattern that appears on
    candlestick charts. It may appear after a decline, and it signals that the bearishness is
    fading. The pattern is very rare.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL3STARSINSOUTH(opn, high, low, close)


def cdl3whitesoldiers(opn, high, low, close):
    """Three Advancing White Soldiers:

    Three white soldiers is a bullish candlestick pattern that is used to predict the
    reversal of the current downtrend in a pricing chart. The pattern consists of three
    consecutive long-bodied candlesticks that open within the previous candle's real
    body and a close that exceeds the previous candle's high. These candlesticks should
    not have very long shadows and ideally open within the real body of the preceding
    candle in the pattern.

    - Three white soldiers are considered a reliable reversal pattern when confirmed by
    other technical indicators like the relative strength index (RSI).

    - The size of the candles and the length of the shadow is used to judge whether there
    is a risk of retracement.

    - The opposite pattern of three white soldiers is three black crows, which indicates
    a reversal of an uptrend.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDL3WHITESOLDIERS(opn, high, low, close)


def cdlabandonedbaby(opn, high, low, close):
    """Abandoned Baby:

    The bullish abandoned baby is a type of candlestick pattern that is used by traders
    to signal a reversal of a downtrend. It forms in a downtrend and is composed of three
    price bars. The first is a large down candle, followed by a doji candle that gaps
    below the first candle. The next candle opens higher than the doji and moves
    aggressively to the upside.

    - The bullish abandoned baby is a three-bar pattern following a downtrend. It consists
    of a strong down candle, a gapped down doji, and then a strong bullish candle that
    gaps up.

    - The pattern signals the potential end of a downtrend and the start of a price move
    higher.

    - Some traders allow for slight variation. There may be more than one doji, or gaps
    may not be present after the first or second candle. But the overall psychology of
    the pattern should still be

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLABANDONEDBABY(opn, high, low, close)


def cdladvanceblock(opn, high, low, close):
    """Advance Block:

    Advance block is the name given to a candlestick trading pattern. The pattern is a
    three-candle bearish setup that is considered to be a reversal pattern—a suggestion
    that price action is about to change from what had been an upward trend to a downward
    trend in relatively short time frames. Some authors suggest that in practice the
    formation often leads to a bullish continuation instead of a reversal.

    - An advance block is a three-period candlestick pattern considered to forecast a
    reversal.

    - The pattern's success at predicting reversal is barely above random.

    - Reversals are more prevalent when this pattern occurs in a larger downward trend.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLADVANCEBLOCK(opn, high, low, close)


def cdlbelthold(opn, high, low, close):
    """Belt-hold:

    A bullish belt hold is a single bar Japanese candlestick pattern that suggests a
    possible reversal of the prevailing downtrend.

    - A bullish belt hold is a single bar Japanese candlestick pattern that suggests a
    possible reversal of the prevailing downtrend.
    - Bullish belt hold's potency is enhanced if it forms near a support level, such a
    trend line, a moving average, or at market pivot points.
    - The bullish belt hold can be found across all time frames, but is more reliable
    on the daily and weekly charts.

    A bearish belt hold is a candlestick pattern that forms during an upward trend.
    This is what happens in the pattern:

    - Following a stretch of bullish trades, a bearish or black candlestick occurs.

    - The opening price, which becomes the high for the day, is higher than the close
    of the previous day.

    - The stock price declines throughout the day, resulting in a long black candlestick
    with a short lower shadow and no upper shadow.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLBELTHOLD(opn, high, low, close)


def cdlbreakaway(opn, high, low, close):
    """Breakaway:

    Forecast: bearish reversal
    Trend prior to the pattern: uptrend
    Opposite pattern: Bullish Breakaway
    Number of candle config_lines: 5

    Construction:

    First candle
    - a tall white candle
    Second candle
    - a white candle
    - candle opens above the previous closing price (upward price gap, shadows can overlap)
    Third candle
    - a white or black candle
    - candle opens above the previous opening price
    Fourth candle
    - a white candle
    - candle closes above the previous closing price
    Fifth candle
    - a tall black candle
    - candle opens below the previous closing price
    - candle closes below the second line's opening price and above the first line's closing price
    - the price gap formed between the first and the second line is not closed

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLBREAKAWAY(opn, high, low, close)


def cdlclosingmarubozu(opn, high, low, close):
    """Closing Marubozu:

    Forecast: reversal or continuation of the trend
    Trend prior to the pattern: n/a
    Opposite candlestick: Closing White Marubozu

    Construction:

    black body
    no upper shadow
    upper shadow smaller than the body
    appears as a short or long line

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLCLOSINGMARUBOZU(opn, high, low, close)


def cdlconcealbabyswall(opn, high, low, close):
    """Concealing Baby Swallow: float, 最低价

    Forecast: bullish reversal
    Trend prior to the pattern: downtrend
    Opposite pattern: none
    Number of candle config_lines: 4

    Construction:

    First candle
    - a Black Marubozu candle in a downtrend
    Second candle
    - a Black Marubozu candle
    - candle opens within the prior candle's body
    - candle closes below the prior closing price
    Third candle
    - a High Wave basic candle with no lower shadow
    - candle opens below the prior closing price
    - upper shadow enters the prior candle's body
    Fourth candle
    - black body
    - candle’s body engulfs the prior candle’s body including the shadows

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLCONCEALBABYSWALL(opn, high, low, close)


def cdlcounterattack(opn, high, low, close):
    """Counterattack:

    The counterattack config_lines pattern is a two-candle reversal pattern that appears on
    candlestick charts. It can occur during an uptrend or downtrend.

    - For a bullish reversal during a downtrend, the first candle is a long black (down)
    candle, and the second candle gaps down but then closes higher, near the close of
    the first candle. It shows that sellers were in control, but they may be losing
    that control as the buyers were able to close the gap down.

    - For a bearish reversal during an uptrend, the first candle is a long white (up)
    candle, and the second candle gaps higher but then closes lower, near the close of
    the first candle.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLCOUNTERATTACK(opn, high, low, close)


def cdldarkcloudcover(opn, high, low, close):
    """Dark Cloud Cover:

    Dark Cloud Cover is a bearish reversal candlestick pattern where a down candle
    (typically black or red) opens above the close of the prior up candle (typically white
    or green), and then closes below the midpoint of the up candle.

    The pattern is significant as it shows a shift in the momentum from the upside to the
    downside. The pattern is created by an up candle followed by a down candle. Traders look
    for the price to continue lower on the next (third) candle. This is called confirmation.

    - Dark Cloud Cover is a candlestick pattern that shows a shift in momentum to the downside
    following a price rise.

    - The pattern is composed of a bearish candle that opens above but then closes below the
    midpoint of the prior bullish candle.

    - Both candles should be relatively large, showing strong participation by traders and
    investors. When the pattern occurs with small candles it is typically less significant.

    - Traders typically see if the candle following the bearish candle also shows declining
    prices. A further price decline following the bearish candle is called confirmation.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLDARKCLOUDCOVER(opn, high, low, close)


def cdldoji(opn, high, low, close):
    """Doji:

    A doji—or more accurately, "dо̄ji"—is a name for a session in which the candlestick for a
    security has an open and close that are virtually equal and are often components in
    patterns. Doji candlesticks look like a cross, inverted cross or plus sign. Alone, doji
    are neutral patterns that are also featured in a number of important patterns.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLDOJI(opn, high, low, close)


def cdldojistar(opn, high, low, close):
    """Doji Star:

    Forecast: bullish reversal
    Trend prior to the pattern: downtrend
    Opposite pattern: Bearish Doji Star

    Construction:

    First candle
    - a candle in a downtrend
    - black body
    Second candle
    - a doji candle
    - a body below the first candle's body

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLDOJISTAR(opn, high, low, close)


def cdldragonflydoji(opn, high, low, close):
    """Dragonfly Doji:

    A Dragonfly Doji is a type of candlestick pattern that can signal a potential reversal
    in price to the downside or upside, depending on past price action. It's formed when the
    asset's high, open, and close prices are the same. The long lower shadow suggests that
    there was aggressive selling during the period of the candle, but since the price closed
    near the open it shows that buyers were able to absorb the selling and push the price
    back up.

    - A dragonfly doji can occur after a price rise or a price decline.

    - The open, high, and close prices match each other, and the low of the period is
    significantly lower than the former three. This creates a "T" shape.

    - The appearance of a dragonfly doji after a price advance warns of a potential price
    decline. A move lower on the next candle provides confirmation.

    - A dragonfly doji after a price decline warns the price may rise. If the next candle
    rises that provides confirmation.

    - Candlestick traders typically wait for the confirmation candle before acting on the
    dragonfly doji.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLDRAGONFLYDOJI(opn, high, low, close)


def cdlengulfing(opn, high, low, close):
    """Engulfing Pattern:

    Bullish engulfing pattern:
    The bullish engulfing pattern is a two-candle reversal pattern. The second candle
    completely ‘engulfs’ the real body of the first one, without regard to the length of
    the ellipsis shadows. The Bullish Engulfing pattern appears in a downtrend and is a
    combination of one dark candle followed by a larger hollow candle. On the second day
    of the pattern, price opens lower than the previous low, yet buying pressure pushes
    the price up to a higher level than the previous high, culminating in an obvious win
    for the buyers. It is advisable to enter a long position when the price moves higher
    than the high of the second engulfing candle—in other words when the downtrend
    reversal is confirmed.

    - A bullish engulfing pattern is a candlestick chart pattern that forms when a small
    black candlestick is followed the next day by a large white candlestick, the body of
    which completely overlaps or engulfs the body of the previous day’s candlestick.

    - Bullish engulfing patterns are more likely to signal reversals when they are preceded
    by four or more black candlesticks.

    - Investors should look not only to the two candlesticks which form the bullish
    engulfing pattern but also to the preceding candlesticks

    Bearish engulfing pattern:
    A bearish engulfing pattern is a technical chart pattern that signals lower prices to
    come. The pattern consists of an up (white or green) candlestick followed by a large
    down (black or red) candlestick that eclipses or "engulfs" the smaller up candle. The
    pattern can be important because it shows sellers have overtaken the buyers and are
    pushing the price more aggressively down (down candle) than the buyers were able to
    push it up (up candle).

    - A bearish engulfing pattern can occur anywhere, but it is more significant if it
    occurs after a price advance. This could be an uptrend or a pullback to the upside
    with a larger downtrend.

    - Ideally, both candles are of substantial size relative to the price bars around them.
    Two very small bars may create an engulfing pattern, but it is far less significant
    than if both candles are large.

    - The real body—the difference between the open and close price—of the candlesticks is
    what matters. The real body of the down candle must engulf the up candle.

    - The pattern has far less significance in choppy markets.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLENGULFING(opn, high, low, close)


def cdleveningdojistar(opn, high, low, close):
    """Evening Doji Star:

    The Evening Doji Star is a bearish reversal pattern, being very similar to the Evening
    Star. The only difference is that the Evening Doji Star needs to have a doji candle
    (except the Four-Price Doji) on the second line. The doji candle (second line) should
    not be preceded by or followed by a price gap.

    Forecast: bearish reversal
    Trend prior to the pattern: uptrend
    Opposite pattern: Morning Doji Star

    Construction:

    First candle
    - a candle in an uptrend
    - white body
    Second candle
    - a doji candle
    - a doji body above the previous candle body
    - the low price below the previous candle high price
    Third candle
    - black body
    - candle body below the previous candle body
    - the closing price below the midpoint of the first candle body

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLEVENINGDOJISTAR(opn, high, low, close)


def cdleveningstar(opn, high, low, close):
    """Evening Star:

    An Evening Star is a stock-price chart pattern used by technical analysts to detect when
    a trend is about to reverse. It is a bearish candlestick pattern consisting of three
    candles: a large white candlestick, a small-bodied candle, and a red candle.

    Evening Star patterns are associated with the top of a price uptrend, signifying that
    the uptrend is nearing its end. The opposite of the Evening Star is the Morning Star
    pattern, which is viewed as a bullish indicator.

    - An Evening Star is a pattern used by technical analysts to predict future price
    declines.

    - Although it is rare, the Evening Star pattern is considered a reliable technical
    indicator.

    - The Evening Star is the opposite of the Morning Star pattern. The two are bearish
    and bullish indicators, respectively.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLEVENINGSTAR(opn, high, low, close)


def cdlgapsidesidewhite(opn, high, low, close):
    """Up/Down-gap side-by-side white config_lines:

    The side-by-side white config_lines pattern is a three-candle continuation pattern that
    occurs on candlestick charts. The up version is a large up (white or green) candle
    followed by a gap and then two more white candles of similar size to each other. The
    down version is a large down (black or red) candle followed by two white candles of
    similar size. When the pattern occurs, which is rare, it is expected that the price
    will continue moving in the current trend direction, down or up, as the case may be.

    - There is an up and down version of the pattern. The up version is a white candle
    followed by a gap up and two white candles of similar size. The down version is a
    black candle followed by a gap down and two white candles of similar size.

    - The pattern is a continuation pattern, meaning the price is expected to move in
    the direction of the trend (first candle) following the pattern.

    - The pattern has moderate reliability in terms of the trend continuing after the
    pattern, but quite often the price move after the pattern will be muted, indicating
    it is not a highly significant pattern.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLGAPSIDESIDEWHITE(opn, high, low, close)


def cdlgravestonedoji(opn, high, low, close):
    """Gravestone Doji:

    A gravestone doji is a bearish reversal candlestick pattern that is formed when the
    open, low, and closing prices are all near each other with a long upper shadow. The
    long upper shadow suggests that the bullish advance in the beginning of the session
    was overcome by bears by the end of the session, which often comes just before a
    longer term bearish downtrend.

    - A gravestone doji is a bearish pattern that suggests a reversal followed by a
    downtrend in the price action.

    - A gravestone pattern can be used as a sign to take profits on a bullish position
    or enter a bearish trade.

    - The opposite of a gravestone doji is a dragonfly doji

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLGRAVESTONEDOJI(opn, high, low, close)


def cdlhammer(opn, high, low, close):
    """Hammer:

    A hammer is a price pattern in candlestick charting that occurs when a security trades
    significantly lower than its opening, but rallies within the period to close near
    opening price. This pattern forms a hammer-shaped candlestick, in which the lower
    shadow is at least twice the size of the real body. The body of the candlestick
    represents the difference between the open and closing prices, while the shadow shows
    the high and low prices for the period.

    - Hammers have a small real body and a long lower shadow.

    - Hammers occur after a price decline.

    - The hammer candlestick shows sellers came into the market during the period but by
    the close the selling had been absorbed and buyers had pushed the price back to near
    the open.

    - The close can be above or below the open, although the close should be near the open
    in order for the real body to remain small.

    - The lower shadow should be at least two times the height of the real body.

    - Hammer candlesticks indicate a potential price reversal to the upside. The price
    must start moving up following the hammer; this is called confirmation.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHAMMER(opn, high, low, close)


def cdlhangingman(opn, high, low, close):
    """Hanging Man:

    A hanging man candlestick occurs during an uptrend and warns that prices may start
    falling. The candle is composed of a small real body, a long lower shadow, and little or
    no upper shadow. The hanging man shows that selling interest is starting to increase. In
    order for the pattern to be valid, the candle following the hanging man must see the
    price of the asset decline.

    - A hanging man is a bearish reversal candlestick pattern that occurs after a price
    advance. The advance can be small or large, but should be composed of at least a few
    price bars moving higher overall.

    - The candle must have a small real body and a long lower shadow that is at least twice
    the size as the real body. There is little or no upper shadow.

    - The close of the hanging man can be above or below open, it just needs to be near the
    open so the real body is small.

    - The long lower shadow of the hanging man shows that sellers were able to take control
    for part of the trading period.

    - The hanging man pattern is just a warning. The price must move lower on the next candle
    in order for the hanging man to be a valid reversal pattern. This is called confirmation.

    - Traders typically exit long trades or enter short trades during or after the
    confirmation candle, not before.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHANGINGMAN(opn, high, low, close)


def cdlharami(opn, high, low, close):
    """Harami Pattern:

    Bullish Harami:
    A bullish harami is a candlestick chart indicator suggesting that a bearish trend may be
    coming to end. Some investors may look at a bullish harami as a good sign that they should
    enter a long position on an asset.

    - A bullish harami is a candlestick chart indicator for reversal in a bear price movement.

    - It is generally indicated by a small increase in price (signified by a white candle) that
    can be contained within the given equity's downward price movement (signified by black
    candles) from the past couple of days

    Bearish Harami:
    A bearish harami is a two bar Japanese candlestick pattern that suggests prices may soon
    reverse to the downside. The pattern consists of a long white candle followed by a small
    black candle. The opening and closing prices of the second candle must be contained within
    the body of the first candle. An uptrend precedes the formation of a bearish harami.

    - A bearish harami is a candlestick chart indicator for reversal in a bull price movement.

    - It is generally indicated by a small decrease in price (signified by a black candle) that
    can be contained within the given equity's upward price movement (signified by white
    candles) from the past day or two.

    - Traders can use technical indicators, such as the relative strength index (RSI) and the
    stochastic oscillator with a bearish harami to increase the chance of a successful trade.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHARAMI(opn, high, low, close)


def cdlharamicross(opn, high, low, close):
    """Harami Cross Pattern:

    A harami cross is a Japanese candlestick pattern that consists of a large candlestick that
    moves in the direction of the trend, followed by a small doji candlestick. The doji is
    completely contained within the prior candlestick’s body. The harami cross pattern suggests
    that the previous trend may be about to reverse. The pattern can be either bullish or
    bearish. The bullish pattern signals a possible price reversal to the upside, while the
    bearish pattern signals a possible price reversal to the downside.

    - A bullish harami cross is a large down candle followed by a doji. It occurs during a downtrend.

    - The bullish harami cross is confirmed by a price move higher following the pattern.

    - A bearish harami cross is a large up candle followed by a doji. It occurs during an uptrend.

    - The bearish pattern is confirmed by a price move lower following the pattern.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHARAMICROSS(opn, high, low, close)


def cdlhighwave(opn, high, low, close):
    """High-Wave Candle:

    The High Wave is a special kind of spinning top basic candle with one or two very long shadows.
    The opening and closing price are not equal, but slightly different from each other. In this
    case, body color does not matter. The High Wave is similar to the Long-Legged Doji

    Forecast: lack of determination
    Trend prior to the pattern: n/a
    Opposite candlestick: none

    Construction:

    - a black or white body
    - very small body
    - at least one shadow required
    - appears on as a long line
    - the length of at least one shadows is at least 3 times larger than the body

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHIGHWAVE(opn, high, low, close)


def cdlhikkake(opn, high, low, close):
    """Hikkake Pattern:

    The hikkake pattern is a price pattern used by technical analysts and traders hoping to
    identify a short-term move in the market's direction. The pattern has two different setups,
    one implying a short-term downward movement in price action, and a second setup implying a
    short-term upward trend in price.

    - Complex chart pattern consisting of an inside day, a fake-out move and then a
    reversal-and-breakout move.

    - The pattern appears to work based on traders expectations of price moving one way, and then
    collectively bailing out as price reverses.

    - The pattern has two variations, a bullish and a bearish setup.

    - The bullish variation is more frequently observed

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHIKKAKE(opn, high, low, close)


def cdlhikkakemod(opn, high, low, close):
    """Modified Hikkake Pattern:

    The modified hikkake pattern is a less frequent variant of the basic hikkake pattern and is
    viewed as a reversal pattern. The concept of the modified version is similar to the basic
    version, except that a "context bar" is used prior to the inside price bar/candle. Therefore,
    the modified version consists of a context bar, an inside bar, a fake move, followed by a
    move above (bullish) or below (bearish) the inside bar high or low, respectively.

    - The modified hikkake adds a context bar to the basic hikkake pattern. There is a bullish
    and bearish version of the modified hikkake.

    - The bearish version consists of a context bar that closes near the high but has a smaller
    range than the prior candle. This followed by an inside bar, then a candle with a higher high
    and higher low. The pattern completes when the price drops below the inside bar low.

    - The bullish version consists of a context bar that closes near the low but has a smaller
    range than the prior candle. This followed by an inside bar, then a candle with a lower high
    and lower low. The pattern completes when the price rises above the inside bar high.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHIKKAKEMOD(opn, high, low, close)


def cdlhomingpigeon(opn, high, low, close):
    """Homing Pigeon:

    The bullish homing pigeon is a candlestick pattern where one large candle is followed by a
    smaller candle with a body is located within the range of the larger candle's body. Both
    candles in the pattern must be black, or filled, indicating that the closing price was lower
    than the opening price. The pattern may indicate that there is a weakening of the current
    downward trend, which increases the likelihood of an upward reversal.

    - A bullish homing pigeon is an upside reversal pattern. Although, it can also be a bearish
    continuation pattern.

    - The pattern occurs during downtrends, or during pullbacks within an uptrend.

    - The pattern is composed of a large real body followed by a smaller real body, and both
    candles are black (filled) or red indicating the close is below the open.

    - Bullish homing pigeon patterns don't provide profit targets, and a stop loss is typically
    placed below the bottom of the pattern after an upside move is confirmed.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLHOMINGPIGEON(opn, high, low, close)


def cdlidentical3crows(opn, high, low, close):
    """Identical Three Crows:

    The Identical Three Crows is a three-line bearish reversal candlestick pattern. Every candle appears as a long line having a black body.

    Forecast: bearish reversal
    Trend prior to the pattern: uptrend
    Opposite pattern: none
    See Also: Three Black Crows

    Construction:

    First candle
    - a candle in an uptrend
    - black body
    Second candle
    - black body
    - the opening price at or near the prior close
    Third candle
    - black body
    - the opening price at or near the prior close

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLIDENTICAL3CROWS(opn, high, low, close)


def cdlinneck(opn, high, low, close):
    """In-Neck Pattern:

    The In Neck pattern is a two-line bearish continuation pattern what implies that the pattern
     appears in a downtrend. The first line is a black candle appearing in a downtrend. The second
     line is a white candle, and the lower and upper shadow length cannot exceed more than twice
     the body length. Additionally the second candle's closing price needs to be slightly above
     the previous closing price (up to 15% of the first line body).

    Forecast: bearish continuation
    Trend prior to the pattern: downtrend
    Opposite pattern: none

    Construction:

    First candle
    - a candle in a downtrend
    - black body
    - appears on as a long line
    Second candle
    - white body
    - the opening price below the previous closing price
    - the closing price is slightly above the previous closing price (up to 15% of the first line body)

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLINNECK(opn, high, low, close)


def cdlinvertedhammer(opn, high, low, close):
    """Inverted Hammer:

    The hammer pattern is a single-candle bullish reversal pattern that can be spotted at the end
    of a downtrend. The opening price, close, and top are approximately at the same price, while
    there is a long wick that extends lower, twice as big as the short body.



    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLINVERTEDHAMMER(opn, high, low, close)


def cdlkicking(opn, high, low, close):
    """Kicking:

    The kicking candlestick pattern is a two candlestick reversal pattern that begins a new trend
    opposite to the trend previous.

    A bullish kicking pattern occurs after a downtrend. The first day candlestick is a bearish
    marabozu candlestick (a bearish candlestick with little to no upper or lower shadow, where the
    price opens at the high of the day and closes at the low of the day). The second day gaps up
    massively and opens above the previous day’s opening price. This second day candlestick is a
    bullish marabozu (a bullish candlestick with little to no upper or lower shadow, where the price
    opens at the low of the day and closes at the high of the day). There is a gap or, as the
    Japanese refer to it, a window between day one’s bearish candlestick and day two’s bullish
    candlestick.

    A bearish kicking pattern occurs after an uptrend and signals a reversal for a new downtrend.
    The first day candlestick is a bullish marabozu candlestick. The second day gaps down massively
    and opens below the previous day’s opening price. This second day candlestick is a bearish
    marabozu. There is a gap between day one’s bearish candlestick and day two’s bullish candlestick.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLKICKING(opn, high, low, close)


def cdlkickingbylength(opn, high, low, close):
    """Kicking - bull/bear determined by the longer marubozu

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLKICKINGBYLENGTH(opn, high, low, close)


def cdlladderbottom(opn, high, low, close):
    """Ladder Bottom:

    Ladder Bottom
    The ladder bottom is a five candle reversal pattern, indicating a rise is commencing
    following a decline. The chart pattern is created by a series of lower closes,
    followed by a sharp price increase.

    Ladder Top
    The ladder top is a five candle reversal pattern, pointing to a fall in price following
    a rise. The pattern is composed of a series of higher closes, followed by a sharp price
    drop.

    - In theory, the ladder bottom indicates a price reversal to the upside following a
    downtrend.

    - In theory, the ladder top indicates a price reversal to the downside following an
    uptrend.

    - In reality, the pattern acts as a reversal pattern a little more than 50% of the time.

    - The pattern is quite rare, so opportunities for trading the pattern are limited.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLLADDERBOTTOM(opn, high, low, close)


def cdllongleggeddoji(opn, high, low, close):
    """Long Legged Doji:

    The long-legged doji is a candlestick that consists of long upper and lower shadows and
    has approximately the same opening and closing price. The candlestick signals indecision
    about the future direction of the underlying security.

    It is used by some traders to warn that indecision is entering the market after a strong
    advance. It may also warn that a strong downtrend may be experiencing indecision before
    making a move to the upside.

    - The long-legged doji has long upper and lower shadows and a small real body.

    - The pattern shows indecision and is most significant when it occurs after a strong
    advance or decline.

    - While some traders may act on the one-candle pattern, others want to see what the price
    does after the long-legged doji.

    - The pattern is not always significant, and won't always mark the end of a trend. It
    could mark the start of a consolidation period, or it may just end up being an
    insignificant blip in the current trend

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLLONGLEGGEDDOJI(opn, high, low, close)


def cdllongline(opn, high, low, close):
    """Long Line Candle

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLLONGLINE(opn, high, low, close)


def cdlmarubozu(opn, high, low, close):
    """Marubozu:

    The word marubozu means "bald head" or "shaved head" in Japanese, and this is
    reflected in the candlestick's lack of wicks. When you see a Marubozu candlestick,
    the fact that there are no wicks tells you that the session opened at the high
    price of the day and closed at the low price of the day. In a bullish Marubozu,
    the buyers maintained control of the price throughout the day, from the opening
    bell to the close. In a bearish Marubozu, the sellers controlled the price from
    the opening bell to the close.

    Depending on where a Marubozu is located and what color it is, you can make
    predictions:

    - If a White Marubozu occurs at the end of an uptrend, a continuation is likely.
    - If a White Marubozu occurs at the end of a downtrend, a reversal is likely.
    - If a Black Marubozu occurs at the end of a downtrend, a continuation is likely.
    - If a Black Marubozu occurs at the end of an uptrend, a reversal is likely.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLMARUBOZU(opn, high, low, close)


def cdlmatchinglow(opn, high, low, close):
    """Matching Low: float, 最低价

    A matching low is a two-candle bullish reversal pattern that appears on candlestick
    charts. It occurs after a downtrend and, in theory, signals a potential end to the
    selling via two long down (black or red) candlesticks with matching closes. It is
    confirmed by a price move higher following the pattern.

    In reality, the matching low more often acts as a continuation pattern to the downside.

    - The matching low pattern is created by two down candlesticks with similar or
    matching closing prices.

    - The pattern occurs following a price decline and signals a potential bottom or
    that price has reached a support level.

    - In reality, the price could go either direction following the pattern, and more
    often it continues to the downside.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLMATCHINGLOW(opn, high, low, close)


def cdlmathold(opn, high, low, close):
    """Mat Hold:

    A mat hold pattern is a pattern found in the technical analysis of stocks that
    ultimately indicates the stock will continue its previous directional trend,
    meaning bullish or bearish.

    This type of pattern is initially indicated by a significant trading day in one
    direction or another, followed by three small opposite trending days. The fifth
    day then continues the first day's trend, pushing higher or lower, in the same
    direction as the first day's movement.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLMATHOLD(opn, high, low, close)


def cdlmorningdojistar(opn, high, low, close):
    """Morning Doji Star:

    The Morning Doji Star is a bullish reversal pattern, being very similar to the Morning Star. The only difference is that the Morning Doji Star needs to have a doji candle (except the Four-Price Doji) on the second line. The doji candle (second line) should not be preceded by or followed by a price gap.

    Forecast: bullish reversal
    Trend prior to the pattern: downtrend
    Opposite pattern: Evening Doji Star

    Construction:

    First candle
    - a candle in a downtrend
    - black body
    Second candle
    - a doji candle
    - a doji body below the previous candle body
    - the high price above the previous candle low price
    Third candle
    - white body
    - candle body above the previous candle body
    - the closing price above the midpoint of the first candle body

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLMORNINGDOJISTAR(opn, high, low, close)


def cdlmorningstar(opn, high, low, close):
    """Morning Star:

    A morning star is a visual pattern consisting of three candlesticks that is interpreted
    as a bullish sign by technical analysts. A morning star forms following a downward trend
    and it indicates the start of an upward climb. It is a sign of a reversal in the
    revious price trend. Traders watch for the formation of a morning star and then seek
    confirmation that a reversal is indeed occurring using additional indicators.

    - A morning star is a visual pattern made up of a tall black candlestick, a smaller black
    or white candlestick with a short body and long wicks, and a third tall white candlestick.

    - The middle candle of the morning star captures a moment of market indecision where the
    bears begin to give way to bulls. The third candle confirms the reversal and can mark a
    new uptrend.

    - The opposite pattern to a morning star is the evening star, which signals a reversal of
    an uptrend into a downtrend.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLMORNINGSTAR(opn, high, low, close)


def cdlonneck(opn, high, low, close):
    """On-Neck Pattern:

    The on neck pattern occurs when a long real bodied down candle is followed by a smaller
    real bodied up candle that gaps down on the open but then closes near the prior candle's
    close. The pattern is called a neckline because the two closing prices are the same (or
    almost the same) across the two candles, forming a horizontal neckline.

    The pattern is theoretically considered a continuation pattern, indicating that the price
    will continue lower following the pattern. In reality, that only occurs about half the
    time. Therefore, the pattern also often indicates at least a short-term reversal higher.

    - The pattern is created by a long real bodied down candle, followed by a smaller real
    bodied up candle with the same close as the prior candle.

    - In theory, the pattern is a continuation pattern to the downside, but in reality, it
    acts as a continuation pattern and a reversal pattern with nearly the same frequency.

    - Trading on the pattern could result in any number of variations.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLONNECK(opn, high, low, close)


def cdlpiercing(opn, high, low, close):
    """Piercing Pattern:

    A piercing pattern is a two-day, candlestick price pattern that marks a potential short-term
    reversal from a downward trend to an upward trend. The pattern includes the first day opening
    near the high and closing near the low with an average or larger-sized trading range. It also
    includes a gap down after the first day where the second day begins trading, opening near the
    low and closing near the high. The close should also be a candlestick that covers at least
    half of the upward length of the previous day's red candlestick body.

    - The piercing pattern is a two-day candle pattern that implies a potential reversal from a
    downward trend to an upward trend.

    - This candle pattern typically only forecasts about five days out.

    - Three characteristics of this pattern include a downward trend before the pattern, a gap
    after the first day, and a strong reversal as the second candle in the pattern.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLPIERCING(opn, high, low, close)


def cdlrickshawman(opn, high, low, close):
    """Rickshaw Man:

    The rickshaw man is a type of long-legged doji candlestick where the body can be found at or
    very near the middle of the candle. The candlestick shows the high, low, open, and close
    prices. The open and close are at or very close to the same price level, creating the doji.
    The high and low are far apart, creating long shadows on the candlestick. The rickshaw man
    shows indecision on the part of participants in a market.

    - The rickshaw man signals indecision in the marketplace. When used on its own, it is not a
    highly reliable candlestick pattern for trading.

    - The rickshaw man should be used in conjunction with other technical indicators, price action
    analysis, or chart patterns to signal a potential trend change or continuation.

    - The rickshaw man has long upper and lower shadows, with a small real body near the center
    of the candle.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLRICKSHAWMAN(opn, high, low, close)


def cdlrisefall3methods(opn, high, low, close):
    """Rising/Falling Three Methods:

    Rising Three Methods:
    "Rising three methods" is a bullish continuation candlestick pattern that occurs in an uptrend
    and whose conclusion sees a resumption of that trend.This can be contrasted with a falling
    three method.

    - Rising three methods is a bullish continuation candlestick pattern that occurs in an uptrend
    and whose conclusion sees a resumption of that trend.

    - The decisive (fifth) strongly bullish candle is proof that sellers did not have enough
    conviction to reverse the prior uptrend and that buyers have regained control of the market.

    - The rising three methods may be more effective if the initial bullish candlestick's wicks,
    denoting the high and low traded price for that period, are shallow.

    Falling Three Methods:
    The "falling three methods" is a bearish, five candle continuation pattern that signals an
    interruption, but not a reversal, of the current downtrend. The pattern is characterized by
    two long candlesticks in the direction of the trend, in this case down, at the beginning and
    end, with three shorter counter-trend candlesticks in the middle.
    This can be contrasted with a rising three method.

    - The "falling three methods" is a bearish, five candle continuation pattern that signals an
    interruption, but not a reversal, of the current downtrend.

    - A falling three methods pattern is characterized by two long candlesticks in the direction
    of the trend, in this case down, at the beginning and end, with three shorter counter-trend
    candlesticks in the middle.

    - The falling three methods pattern is important because it shows traders that the bulls still
    do not have enough conviction to reverse the trend and it is used by some active traders as a
    signal to initiate new, or add to their existing, short positions.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLRISEFALL3METHODS(opn, high, low, close)


def cdlseparatinglines(opn, high, low, close):
    """Separating Lines:

    Bullish Separating Lines Pattern:
    With just two candles – one black (or red) and one white (or green) – the Bullish Separating
    Lines pattern is easy to learn and spot. To confirm its presence, seek out the following
    criteria:
    First, the pattern must begin with a clear and defined uptrend. Second, a long bearish candle
    (black or red) must appear. Third, the next day must be defined by a long bullish candle (white
    or green), which will open at the same place the first day opened.The white candle should not
    have a lower wick, which means that the price can not drop below the opening price throughout
    the course of the session.

    Bearish Separating Lines Pattern:
    The Bearish Separating Lines pattern encompasses just two candles. To spot it, look for the
    following criteria:
    First, the pattern must begin with a clear and defined downtrend. Second, a long bullish candle
    (white or green) must appear. Third, the next day must be defined by a long bearish candle (black
    or red), which will open at the same place as the first day opened. Ideally, the second candle
    will not have an upper wick.


    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLSEPARATINGLINES(opn, high, low, close)


def cdlshootingstar(opn, high, low, close):
    """Shooting Star：

    A shooting star is a bearish candlestick with a long upper shadow, little or no lower shadow,
    and a small real body near the low of the day. It appears after an uptrend. Said differently,
    a shooting star is a type of candlestick that forms when a security opens, advances
    significantly, but then closes the day near the open again.

    For a candlestick to be considered a shooting star, the formation must appear during a price
    advance. Also, the distance between the highest price of the day and the opening price must
    be more than twice as large as the shooting star's body. There should be little to no shadow
    below the real body.

    - A shooting star occurs after an advance and indicates the price could start falling.

    - The formation is bearish because the price tried to rise significantly during the day, but
    then the sellers took over and pushed the price back down toward the open.

    - Traders typically wait to see what the next candle (period) does following a shooting star.
    If the price declines during the next period they may sell or short.

    - If the price rises after a shooting star, the formation may have been a false signal or the
    candle is marking a potential resistance area around the price range of the candle.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLSHOOTINGSTAR(opn, high, low, close)


def cdlshortline(opn, high, low, close):
    """Short Line Candle：

    Short line candles—also known as short candles—are candles on a candlestick chart that have
    a short real body. This one-bar pattern occurs when there is only a small difference between
    the opening price and the closing price over a given period. The length of the upper and
    lower shadows—representing the high and low for the period—do not make a difference in
    defining a short line candle.

    In other words, a short line candle may have a wide or narrow high and low range for the
    period but will always have a narrow open and close range.

    - A short-line, or short candles are candlesticks that have short bodies.

    - This short-body shape indicates that the open and close prices of the security were quite
    close to another.

    - Short-body candles may indicate a period of consolidation in a stock or other asset, but
    their interpretation will vary based on what other price action has preceded and follows it.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLSHORTLINE(opn, high, low, close)


def cdlspinningtop(opn, high, low, close):
    """Spinning Top：

    A spinning top is a candlestick pattern with a short real body that's vertically centered
    between long upper and lower shadows. The candlestick pattern represents indecision about
    the future direction of the asset. Neither the buyers nor the sellers could gain the upper
    hand. The buyers pushed the price up during the period, and the sellers pushed the price
    down during the period, but ultimately the closing price ended up very close to the open.
    After a strong price advance or decline, spinning tops can signal a potential price
    reversal, if the candle that follows confirms.

    A spinning top can have a close above or below the open, but the two prices need to be
    close together.

    - Spinning tops are symmetrical, with upper and lower shadows of approximately equal length.

    - The real body should be small, showing little difference between the open and close prices.

    - Since buyers and sellers both pushed the price, but couldn't maintain it, the pattern
    shows indecision and that more sideways movement could follow.

    - Following a strong move higher or lower, a spinning top shows that the trend traders may
    be losing conviction. For example, following a strong up move, a spinning top shows buyers
    may be losing some of their control and a reversal to the downside could be near.

    - Spinning tops, and nearly all candlestick patterns, require confirmation. If a spinning
    top could be the start of a reversal, the next candle should confirm. If the spinning top is
    showing indecision, then the next candle should also move sideways within the range.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLSPINNINGTOP(opn, high, low, close)


def cdlstalledpattern(opn, high, low, close):
    """Stalled Pattern：

    A stalled pattern is a candlestick chart pattern that occurs during an uptrend, but
    indicates a likely bearish reversal. It is also known as a deliberation pattern.

    Candlestick charts are price charts that show the open and closing prices of a security, as
    well as their highs and lows for a specific period. They get their name from the way the
    illustrations in the chart resemble candles and their wicks.

    A stalled pattern indicates indecision in the market. It may suggest a limited ability for
    traders turn a quick profit through short-term trades.
    A stalled pattern chart consists of three white candles and must meet a specific set of
    criteria. First, each candle’s open and close must be higher than that of the previous candle
    in the pattern. Second, the third candle must have a shorter real body than the other two
    candles. Finally, the third candle must have a tall upper shadow, and an open that is near
    the close of the second candle.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLSTALLEDPATTERN(opn, high, low, close)


def cdlsticksandwich(opn, high, low, close):
    """Stick Sandwich：

    A stick sandwich is a technical trading pattern in which three candlesticks form what appears
    to resemble a sandwich on a trader's screen. Stick sandwiches will have the middle candlestick
    oppositely colored of the candlesticks on either side of it, both of which will have a larger
    trading range than the middle candlestick. Stick sandwich patterns can occur in both bearish
    and bullish indications.

    - Candlestick charts are used by traders to determine possible price movement based on past
    patterns.

    - One candlestick pattern is the stick sandwich because it resembles a sandwich when plotted on
    a price chart - they will have the middle candlestick oppositely colored vs. the candlesticks
    on either side of it, both of which will have a larger trading range than the middle candlestick.

    - These patterns may indicate either bullish or bearish trends, and so should be used in
    conjunction with other methods of signals

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLSTICKSANDWICH(opn, high, low, close)


def cdltakuri(opn, high, low, close):
    """Takuri (Dragonfly Doji with very long lower shadow):

    The Takuri Line pattern is very similar to Hammer. The only difference is that Hammer's lower
    shadow length cannot exceed more than twice its body length, whereas Takuri Line's lower shadow
    cannot be shorter than at least three times its body.

    The Takuri Line is more reliable when is formed in a clear downtrend, or within a support zone.
    An occurrence of Takuri Line pattern after the short-term declines usually does not matter. Very
    important is its market context. In the algorithm implemented within CandleScanner, we used some
    constraint in which the candle is recognized as a valid pattern only when the body is fully
    located under the trend line.

    Forecast: bullish reversal
    Trend prior to the pattern: downtrend
    Opposite pattern: Hanging Man

    Construction:

    - white or black candle with a small body
    - no upper shadow or the shadow cannot be longer than the body
    - lower shadow at least three times longer than the body
    - if the gap is created at the opening or at the closing, it makes the signal stronger
    - appears as a long line

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLTAKURI(opn, high, low, close)


def cdltasukigap(opn, high, low, close):
    """Tasuki Gap:

    Upside Tasuki Gap:
    An Upside Tasuki Gap is a three-bar candlestick formation that is commonly used to signal the
    continuation of the current trend.

    1. The first bar is a large white/green candlestick within a defined uptrend.
    2. The second bar is another white/green candlestick with an opening price that has gapped above
    the close of the previous bar.
    3. The third bar is a black/red candlestick that partially closes the gap between the first two
    bars.

    - The Upside Tasuki Gap is a three-bar candlestick formation that signals the continuation of
    the current uptrend.

    - The Upside Tasuki Gap’s third candle partially closes the gap between the first two bars.

    - Traders often use other gap patterns in conjunction with the Upside Tasuki gap to confirm
    bullish price action.

    Downside Tasuki Gap:
    A Downside Tasuki Gap is a candlestick formation that is commonly used to signal the continuation
    of the current downtrend. The pattern is formed when a series of candlesticks have demonstrated
    the following characteristics:

    1. The first bar is a red candlestick within a defined downtrend.
    2. The second bar is another red candlestick that has gapped below the close of the previous bar.
    3. The last bar is a white candlestick that closes within the gap of the first two bars. It is
    important to note that the white candle does not need to fully close the gap.


    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLTASUKIGAP(opn, high, low, close)


def cdlthrusting(opn, high, low, close):
    """Thrusting Pattern:

    A thrusting pattern is a type of price chart pattern used by technical analysts. It is formed
    when a long black (down) candle is followed by a white (up) candle. The white candle closes above
    the black candle's close, but it doesn't close above the midpoint of the black candle's real body.

    Thrusting patterns are generally considered to be a bearish continuation pattern. However,
    evidence suggests that they can also signal a bullish reversal. Therefore, the thrusting pattern
    is best used in combination with other trading signals.

    - A thrusting pattern is a long black candle followed by a white candle that closes near the
    midpoint of the black candle's real body.

    - The pattern is thought to act as a continuation pattern, but in reality, it acts as a reversal
    pattern about half the time.

    - Thrusting patterns are fairly common, don't necessarily result in large price moves, and are
    most useful when combined with other types of evidence.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLTHRUSTING(opn, high, low, close)


def cdltristar(opn, high, low, close):
    """Tristar Pattern:

    A tri-star is a three line candlestick pattern that can signal a possible reversal in the current
    trend, be it bullish or bearish.

    - A tri-star is a three line candlestick pattern that can signal a possible reversal in the current
    trend, be it bullish or bearish.

    - Tri-star patterns form when three consecutive doji candlesticks appear at the end of a prolonged
    trend.

    - A tri-star pattern near a significant support or resistance level increases the probability of a
    successful trade.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLTRISTAR(opn, high, low, close)


def cdlunique3river(opn, high, low, close):
    """Unique 3 River:

    The unique three river is a candlestick chart pattern that predicts a bullish reversal,
    although there is some evidence that it could act as a bearish continuation pattern. The
    unique three river pattern is composed of three price candles. If the price moves higher
    after the pattern, then it is considered a bullish reversal. If the price moves lower after
    the pattern, then it is a bearish continuation pattern.

    - The unique three river pattern is composed of three candlesticks, in a specific sequence:
    a long downward real body, a hammer that makes a new low, and a third candle with a small
    upward real body that stays within the range of the hammer.

    - Traditionally, the pattern indicates a bullish reversal but the price can actually move
    either direction after the pattern occurs.

    - Traders often use the direction of a confirmation candle, which is the fourth candle, to
    signal which direction the price is likely to move following the pattern.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLUNIQUE3RIVER(opn, high, low, close)


def cdlupsidegap2crows(opn, high, low, close):
    """Upside Gap Two Crows:

    The upside gap two crows pattern is a three-day formation on candlestick charts that typically
    develops in the following manner: Day 1 - A bullish day that continues the uptrend, represented
    by a long white candlestick, which indicates that the closing price of the index or security is
    well above the opening price.
    The upside gap two crows is viewed by chartists as a somewhat ominous pattern, since it
    potentially signals that the index or security may be rolling over as its upward move ends and
    a downtrend begins. The rationale for this interpretation is that despite two stronger opens
    (on Days 2 and 3), the bulls have been unable to maintain upward momentum, suggesting that
    sentiment is turning from bullish to bearish.
    Although fairly rare, the upside gap two crows pattern certainly can certainly be foreboding.
    The high opens fail to hold, the market continues to close lower than it opens, and the crows
    are "circling overhead." So, if a trader spots these two crows, they should watch until they
    receive confirmation that provides enough confidence to step forward and make a successful
    trade. Without confirmation, the upside gap two crows is simply a small pause in an uptrend.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLUPSIDEGAP2CROWS(opn, high, low, close)


def cdlxsidegap3methods(opn, high, low, close):
    """Upside/Downside Gap Three Methods:

    The Gap Three Methods is a three-bar Japanese candlestick pattern that indicates a continuation
    of the current trend. It is a variant of the Upside Tasuki Gap pattern, but the third candle
    completely closes the gap between the first two candles.

    - The Upside/Downside Gap Three Methods is a three-bar candlestick pattern.

    - The Upside Gap Three Methods pattern suggests a bullish continuation of the trend.

    - The Downside Gap Three Methods pattern suggests a bearish continuation of the trend.

    UPSIDE GAP THREE METHODS:
    The Upside Gap Three methods is a bullish continuation pattern with the following characteristics:

    - The market is in an uptrend.
    - The first bar is a white candle with a long real body.
    - The second bar is a white candle with a long real body where the shadows over both candles
    don’t overlap.
    - The third bar is a black candle that has an open within the real body of the first candle and
    a close within the real body of the second candle.

    DOWNSIDE GAP THREE METHODS:
    The Downside Gap Three Methods is a bearish continuation pattern with the following characteristics:

    - The market is in a downtrend.
    - The first bar is a black candle with a long real body.
    - The second bar is a black candle with a long real body where the shadows over both candles don’t
    overlap.
    - The third bar is a white candle that has an open within the real body of the second candle and a
    close within the real body of the first candle.

    opn: float, 开盘价
    high: float, 最高价
    low: float, 最低价
    close: float,收盘价

    Return
    ------
    """
    return CDLXSIDEGAP3METHODS(opn, high, low, close)


# ===========================
# Statistic Functions


def beta(high, low, timeperiod=5):
    """Beta

    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
        :real:
    """
    return BETA(high, low, timeperiod)


def correl(high, low, timeperiod=30):
    """Pearson's Correlation Coefficient (r)

    high: float, 最高价
    low: float, 最低价
    timeperiod:

    Return
    ------
        :real:
    """
    return CORREL(high, low, timeperiod)


def linearreg(close, timeperiod=14):
    """Linear Regression

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return LINEARREG(close, timeperiod)


def linearreg_angle(close, timeperiod=14):
    """Linear Regression Angle

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return LINEARREG_ANGLE(close, timeperiod)


def linearreg_intercept(close, timeperiod=14):
    """Linear Regression Intercept

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return LINEARREG_INTERCEPT(close, timeperiod)


def linearreg_slope(close, timeperiod=14):
    """Linear Regression Slope

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return LINEARREG_SLOPE(close, timeperiod)


def stddev(close, timeperiod=5, nbdev=1):
    """Standard Deviation

    close: float,收盘价
    timeperiod:
    nbdev:

    Return
    ------
        :real:
    """
    return STDDEV(close, timeperiod, nbdev)


def tsf(close, timeperiod=14):
    """Time Series Forecast

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return TSF(close, timeperiod)


def var(close, timeperiod=5, nbdev=1):
    """Variance

    close: float,收盘价
    timeperiod:
    nbdev:

    Return
    ------
        :real:
    """
    return VAR(close, timeperiod, nbdev)


# ===========================
# Math Operation Functions


def acos(close):
    """Vector Trigonometric ACos

    close: float,收盘价

    Return
    ------
        :real:
    """
    return ACOS(close)


def asin(close):
    """Vector Trigonometric ASin

    close: float,收盘价

    Return
    ------
        :real:
    """
    return ASIN(close)


def atan(close):
    """Vector Trigonometric ATan

    close: float,收盘价

    Return
    ------
        :real:
    """
    return ATAN(close)


def ceil(close):
    """Vector Ceil

    close: float,收盘价

    Return
    ------
        :real:
    """
    return CEIL(close)


def cos(close):
    """Vector Trigonometric Cos

    close: float,收盘价

    Return
    ------
        :real:
    """
    return COS(close)


def cosh(close):
    """Vector Trigonometric Cosh

    close: float,收盘价

    Return
    ------
        :real:
    """
    return COSH(close)


def exp(close):
    """Vector Arithmetic Exp

    close: float,收盘价

    Return
    ------
        :real:
    """
    return EXP(close)


def floor(close):
    """Vector Floor

    close: float,收盘价

    Return
    ------
        :real:
    """
    return FLOOR(close)


def ln(close):
    """Vector Log Natural

    close: float,收盘价

    Return
    ------
        :real:
    """
    return LN(close)


def log10(close):
    """Vector Log10

    close: float,收盘价

    Return
    ------
        :real:
    """
    return LOG10(close)


def sin(close):
    """Vector Trigonometric Sin

    close: float,收盘价

    Return
    ------
        :real:
    """
    return SIN(close)


def sinh(close):
    """Vector Trigonometric Sinh

    close: float,收盘价

    Return
    ------
        :real:
    """
    return SINH(close)


def sqrt(close):
    """Vector Square Root

    close: float,收盘价

    Return
    ------
        :real:
    """
    return SQRT(close)


def tan(close):
    """Vector Trigonometric Tan

    close: float,收盘价

    Return
    ------
        :real:
    """
    return TAN(close)


def tanh(close):
    """Vector Trigonometric Tanh

    close: float,收盘价

    Return
    ------
        :real:
    """
    return TANH(close)


def add(high, low):
    """Vector Arithmetic Add

    high: float, 最高价
    low: float, 最低价

    Return
    ------
        :real:
    """
    return ADD(high, low)


def div(high, low):
    """Vector Arithmetic Div

    high: float, 最高价
    low: float, 最低价

    Return
    ------
        :real:
    """
    return DIV(high, low)


def max(close, timeperiod=30):
    """Highest value over a specified period

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return MAX(close, timeperiod)


def maxindex(close, timeperiod=30):
    """Index of highest value over a specified period

    close: float,收盘价
    timeperiod:

    Return
    ------
        :integer:
    """
    return MAXINDEX(close, timeperiod)


def min(close, timeperiod=30):
    """Lowest value over a specified period

    close: float,收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return MIN(close, timeperiod)


def minindex(close, timeperiod=30):
    """Index of lowest value over a specified period

    close: float,收盘价
    timeperiod:

    Return
    ------
        :integer:
    """
    return MININDEX(close, timeperiod)


def minmax(close, timeperiod=30):
    """Lowest and highest values over a specified period

    close: float,收盘价
    timeperiod:

    Return
    ------
        :min:
        :max:
    """
    return MINMAX(close, timeperiod)


def minmaxindex(close, timeperiod=30):
    """Indexes of lowest and highest values over a specified period

    close: float,收盘价
    timeperiod:

    Return
    ------
        :minidx:
        :maxidx:
    """
    return MINMAXINDEX(close, timeperiod)


def mult(high, low):
    """Vector Arithmetic Mult

    high: float, 最高价
    low: float, 最低价

    Return
    ------
        :real:
    """
    return MULT(high, low)


def sub(high, low):
    """Vector Arithmetic Substraction

    high: float, 最高价
    low: float, 最低价

    Return
    ------
        :real:
    """
    return SUB(high, low)


def sum(close, timeperiod=30):
    """Summation

    close: float, 收盘价
    timeperiod:

    Return
    ------
        :real:
    """
    return SUM(close, timeperiod)