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

        Bollinger Bands® are a technical analysis tool developed by John Bollinger
        for generating oversold or overbought signals.
        There are three lines that compose Bollinger Bands: A simple moving average
        (middle band) and an upper and lower band.
        The upper and lower bands are typically 2 standard deviations ± from a
        20-day simple moving average, but can be modified.

        The Bollinger bands are calculated as following:

        BOLU=MA(TP,n)+m∗σ[TP,n]
        BOLD=MA(TP,n)−m∗σ[TP,n]

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

        The DEMA uses two exponential moving averages (EMAs) to eliminate lag,
        as some traders view lag as a problem. The DEMA is used in a similar way
        to traditional moving averages (MA). The average helps confirm up-trends
        when the price is above the average, and helps confirm downtrends when
        the price is below the average.

        formula used for calculating DEMA is like following:

        DEMA=2×EMA_N − EMA of EMA_N

    :param close:
    :param period:
    :return:
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

    input：
        :param close: 1-D ndarray, 输入数据，一维矩阵
        :param span: int, optional, 1 < span, 跨度
    output：=====
        :return: 1-D ndarray; 输入数据的指数平滑移动平均值
    """
    return EMA(close, span)


def ht(close):
    """Hilbert Transform - Instantaneous Trendline 希尔伯特变换-瞬时趋势线

    In mathematics and in signal processing, the Hilbert transform is a
    specific linear operator that takes a function, u(t) of a real
    variable and produces another function of a real variable H(u)(t).
    This linear operator is given by convolution with the function
    1/(πt):

    :param close:
    :return:
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

    input:
    :param close:
    :param timeperiod:
    :return:

    """
    return KAMA(close, timeperiod)


def ma(close, timeperiod: int = 30, matype: int = 0):
    """Moving Average移动平均值

    For a simple moving average, the formula is the sum of the data
    points over a given period divided by the number of periods.

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

    the MESA Adaptive Moving Average is a technical trend-following
    indicator which, according to its creator, adapts to price movement
    “based on the rate change of phase as measured by the Hilbert
    Transform Discriminator”. This method of adaptation features a fast
    and a slow moving average so that the composite moving average swiftly
    responds to price changes and holds the average value until the next
    bars close.



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

    The parabolic SAR is a technical indicator used to determine the
    price direction of an asset, as well as draw attention to when
    the price direction is changing. Sometimes known as the "stop
    and reversal system".
    The parabolic SAR indicator appears on a chart as a series of
    dots, either above or below an asset's price, depending on the
    direction the price is moving.
    A dot is placed below the price when it is trending upward, and
    above the price when it is trending downward.



    :param high:
    :param low:
    :param acceleration:
    :param maximum:
    :return:
    """
    return SAR(high, low, acceleration, maximum)


def sarext(high, low, acceleration=0, maximum=0):
    """Parabolic SAR Extended 扩展抛物线SAR

    he Parabolic SAR Extended is an indicator developed by PlayOptions
    that derives from the classic Parabolic SAR. The interpretation is
    very simple.
    It is an indicator designed for optionists as it is reactive in
    the beginning of the trend, but then remains little influenced by
    the movements, although significant, but which do not change the
    current trend.

    Operation:
        BUY signals are generated when the indicator is above 0;
        SELL signals are generated when the indicator is below 0.

    :param high:
    :param low:
    :param acceleration:
    :param maximum:
    :return:
    """
    return SAREXT(high, low, acceleration, maximum)


def sma(close, timeperiod=30):
    """Simple Moving Average 简单移动平均

    For a simple moving average, the formula is the sum of the data
    points over a given period divided by the number of periods.

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

    The triple exponential moving average was designed to smooth
    price fluctuations, thereby making it easier to identify trends
    without the lag associated with traditional moving averages (MA).
    It does this by taking multiple exponential moving averages (EMA)
    of the original EMA and subtracting out some of the lag.


    :param close:
    :param timeperiod:
    :return:
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

    :param close:
    :param timeperiod:
    :return:
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

    :param close:
    :param timeperiod:
    :return:
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

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return ADX(high, low, close, timeperiod)


def adxr(high, low, close, timeperiod=14):
    """Average Directional Movement Index Rating 平均定向运动指数评级

    The Average Directional Movement Index Rating (ADXR) measures the strength
    of the Average Directional Movement Index (ADX). It's calculated by taking
    the average of the current ADX and the ADX from one time period before
    (time periods can vary, but the most typical period used is 14 days).

    ADXR = (ADX + ADX n-periods ago) / 2

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
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

    :param close:
    :param fastperiod:
    :param slowperiod:
    :param matype:
    :return:
    """
    return APO(close, fastperiod, slowperiod, matype)


def aroon(high, low, timeperiod=14):
    """Aroon

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

    The Aroon Oscillator is a trend-following indicator that uses
    aspects of the Aroon Indicator (Aroon Up and Aroon Down) to
    gauge the strength of a current trend and the likelihood that
    it will continue. Readings above zero indicate that an uptrend
    is present, while readings below zero indicate that a downtrend
    is present. Traders watch for zero line crossovers to signal
    potential trend changes. They also watch for big moves, above
    50 or below -50 to signal strong price moves.



    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return AROONOSC(high, low, timeperiod)


def bop(opn, high, low, close):
    """Balance Of Power:

    :param opn:
    :param high:
    :param low:
    :param close:
    :return:
    """
    return BOP(opn, high, low, close)


def cci(high, low, close, timeperiod=14):
    """Commodity Channel Index:

    Developed by Donald Lambert, the Commodity Channel Index​ (CCI)
    is a momentum-based oscillator used to help determine when an
    investment vehicle is reaching a condition of being overbought
    or oversold. It is also used to assess price trend direction
    and strength. This information allows traders to determine if
    they want to enter or exit a trade, refrain from taking a trade,
    or add to an existing position. In this way, the indicator can
    be used to provide trade signals when it acts in a certain way.

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
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
    trend lines. Also look for support or resistance on the CMO.

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

    :param close:
    :param timeperiod:
    :return:
    """
    return CMO(close, timeperiod)


def dx(high, low, close, timeperiod=14):
    """Directional Movement Index 方向运动指数:

    The Directional Movement Index (DMI) assists in determining if a security
    is trending and attempts to measure the strength of the trend. The DMI
    disregards the direction of the security. It only attempts to determine
    if there is a trend and that trends strength.
    The indicator is made up of four indicator lines:

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
    when DMI- crosses above DMI+. The ADX and ADXR lines are then used to measure
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

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
    """
    return DX(high, low, close, timeperiod)


def macd(close, fastperiod=12, slowperiod=26, signalperiod=9):
    """Moving Average Convergence/Divergence:

    The Moving Average Convergence/Divergence indicator is a momentum oscillator
    primarily used to trade trends. Although it is an oscillator, it is not
    typically used to identify over bought or oversold conditions. It appears on
    the chart as two lines which oscillate without boundaries. The crossover of
    the two lines give trading signals similar to a two moving average system.

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

    MACD extention: different ma types can be applied.

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
    """Money Flow Index:

    The Money Flow Index (MFI) is a momentum indicator that measures the
    flow of money into and out of a security over a specified period of time.
    It is related to the Relative Strength Index (RSI) but incorporates volume,
    whereas the RSI only considers price. The MFI is calculated by accumulating
    positive and negative Money Flow values (see Money Flow), then creating a
    Money Ratio. The Money Ratio is then normalized into the MFI oscillator
    form.

    - Oversold levels typically occur below 20 and overbought levels typically
    occur above 80. These levels may change depending on market conditions.
    Level lines should cut across the highest peaks and the lowest troughs.
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

    input:
        :param high:
        :param low:
        :param close:
        :param timeperiod:
    :return:
    """
    return MINUS_DI(high, low, close, timeperiod)


def minus_dm(high, low, timeperiod=14):
    """Minus Directional Movement / Directional Movement Index:

    The Directional Movement Index, or DMI, is an indicator developed by J. Welles
    Wilder in 1978 that identifies in which direction the price of an asset is moving.
    The indicator does this by comparing prior highs and lows and drawing two lines: a
    positive directional movement line (+DI) and a negative directional movement line
    (-DI). An optional third line, called directional movement (DX) shows the
    difference between the lines. When +DI is above -DI, there is more upward pressure
    than downward pressure in the price. If -DI is above +DI, then there is more
    downward pressure in the price. This indicator may help traders assess the trend
    direction. Crossovers between the lines are also sometimes used as trade signals
    to buy or sell.

    - A +DI line above the -DI line means there is more upward movement than downward movement.

    - A -DI line above the +DI line means there is more downward movement than upward movement.

    - Crossovers can be used to signal emerging trends. For example, the +DI crossing above
    the -DI may signal the start of an uptrend in price.

    - The larger the spread between the two lines, the stronger the price trend. If +DI is way
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

    :param high:
    :param low:
    :param timeperiod:
    :return:
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
    current closing price (CP) and a closing price "n" periods ago (CPn).1
﻿    You determine the value of "n."
    M = CP – CPn
    or
    M = (CP / CPn) * 100

    :param close:
    :param timeperiod:
    :return:
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

    :param high:
    :param low:
    :param close:
    :param timeperiod:
    :return:
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
    - TR is the greater of the Current High - Current Low, Current High - Previous Close,
    or Current Low - Previous Close.
    - Smooth the 14-periods of +DM and TR using the formula below. Substitute TR for +DM
    to calculate ATR. [The calculation below shows a smoothed TR formula, which is
    slightly different than the official ATR formula. Either formula can be used, but use
    one consistently].
    - First 14-period +DM = Sum of first 14 +DM readings.
    - Next 14-period +DM value = First 14 +DM value - (Prior 14 DM/14) + Current +DM
    - Next, divide the smoothed +DM value by the ATR value to get +DI. Multiply by 100.

    :param high:
    :param low:
    :param timeperiod:
    :return:
    """
    return PLUS_DM(high, low, timeperiod)


def ppo(close, fastperiod=12, slowperiod=26, matype=0):
    """Percentage Price Oscillator

    The percentage price oscillator (PPO) is a technical momentum indicator that shows
    the relationship between two moving averages in percentage terms. The moving averages
    are a 26-period and 12-period exponential moving average (EMA).

    The PPO is used to compare asset performance and volatility, spot divergence which
    could lead to price reversals, generate trade signals, and help confirm trend direction.
    The PPO is identical to the moving average convergence divergence (MACD) indicator,
    except the PPO measures percentage difference between two EMAs, while the MACD measures
    absolute (dollar) difference. Some traders prefer the PPO because readings are
    comparable between assets with different prices, whereas MACD readings are not comparable.

    - The PPO typical contains two lines, the PPO line, and the signal line. The signal line
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
    these two lines.

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
    """Relative Strength Index:

    The relative strength index (RSI) is a momentum indicator used in technical analysis
    that measures the magnitude of recent price changes to evaluate overbought or oversold
    conditions in the price of a stock or other asset. The RSI is displayed as an
    oscillator (a line graph that moves between two extremes) and can have a reading from
    0 to 100. The indicator was originally developed by J. Welles Wilder Jr. and introduced
    in his seminal 1978 book, "New Concepts in Technical Trading Systems."

    - An asset is usually considered overbought when the RSI is above 70% and oversold
    when it is below 30%.

    

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