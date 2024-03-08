# coding=utf-8
# ======================================
# File:     test_tafuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all TA-Lib wrapper
#   functions.
# ======================================
import unittest
import numpy as np

from qteasy.tafuncs import bbands, dema, ema, ht, kama, ma, mama, mavp, mid_point
from qteasy.tafuncs import mid_price, sar, sarext, sma, t3, tema, trima, wma, adx, adxr
from qteasy.tafuncs import apo, bop, cci, cmo, dx, macd, macdext, aroon, aroonosc
from qteasy.tafuncs import macdfix, mfi, minus_di, minus_dm, mom, plus_di, plus_dm
from qteasy.tafuncs import ppo, roc, rocp, rocr, rocr100, rsi, stoch, stochf, stochrsi
from qteasy.tafuncs import trix, ultosc, willr, ad, adosc, obv, atr, natr, trange
from qteasy.tafuncs import avgprice, medprice, typprice, wclprice, ht_dcperiod
from qteasy.tafuncs import ht_dcphase, ht_phasor, ht_sine, ht_trendmode, cdl2crows
from qteasy.tafuncs import cdl3blackcrows, cdl3inside, cdl3linestrike, cdl3outside
from qteasy.tafuncs import cdl3starsinsouth, cdl3whitesoldiers, cdlabandonedbaby
from qteasy.tafuncs import cdladvanceblock, cdlbelthold, cdlbreakaway, cdlclosingmarubozu
from qteasy.tafuncs import cdlconcealbabyswall, cdlcounterattack, cdldarkcloudcover
from qteasy.tafuncs import cdldoji, cdldojistar, cdldragonflydoji, cdlengulfing
from qteasy.tafuncs import cdleveningdojistar, cdleveningstar, cdlgapsidesidewhite
from qteasy.tafuncs import cdlgravestonedoji, cdlhammer, cdlhangingman, cdlharami
from qteasy.tafuncs import cdlharamicross, cdlhighwave, cdlhikkake, cdlhikkakemod
from qteasy.tafuncs import cdlhomingpigeon, cdlidentical3crows, cdlinneck
from qteasy.tafuncs import cdlinvertedhammer, cdlkicking, cdlkickingbylength
from qteasy.tafuncs import cdlladderbottom, cdllongleggeddoji, cdllongline, cdlmarubozu
from qteasy.tafuncs import cdlmatchinglow, cdlmathold, cdlmorningdojistar, cdlmorningstar
from qteasy.tafuncs import cdlonneck, cdlpiercing, cdlrickshawman, cdlrisefall3methods
from qteasy.tafuncs import cdlseparatinglines, cdlshootingstar, cdlshortline, cdlspinningtop
from qteasy.tafuncs import cdlstalledpattern, cdlsticksandwich, cdltakuri, cdltasukigap
from qteasy.tafuncs import cdlthrusting, cdltristar, cdlunique3river, cdlupsidegap2crows
from qteasy.tafuncs import cdlxsidegap3methods, beta, correl, linearreg, linearreg_angle
from qteasy.tafuncs import linearreg_intercept, linearreg_slope, stddev, tsf, var, acos
from qteasy.tafuncs import asin, atan, ceil, cos, cosh, exp, floor, ln, log10, sin, sinh
from qteasy.tafuncs import sqrt, tan, tanh, add, div, max, maxindex, min, minindex, minmax
from qteasy.tafuncs import minmaxindex, mult, sub, sum


class TestTAFuncs(unittest.TestCase):
    """测试所有的TAlib函数输出正常"""

    def setUp(self):
        self.data_rows = 50

        self.close = np.array([10.04, 10, 10, 9.99, 9.97, 9.99, 10.03, 10.03, 10.06, 10.06, 10.11,
                               10.09, 10.07, 10.06, 10.09, 10.03, 10.03, 10.06, 10.08, 10, 9.99,
                               10.03, 10.03, 10.06, 10.03, 9.97, 9.94, 9.83, 9.77, 9.84, 9.91, 9.93,
                               9.96, 9.91, 9.91, 9.88, 9.91, 9.64, 9.56, 9.57, 9.55, 9.57, 9.61, 9.61,
                               9.55, 9.57, 9.63, 9.64, 9.65, 9.62])
        self.open = np.array([10.02, 10, 9.98, 9.97, 9.99, 10.01, 10.04, 10.06, 10.06, 10.11,
                              10.11, 10.07, 10.06, 10.09, 10.03, 10.02, 10.06, 10.08, 9.99, 10,
                              10.03, 10.02, 10.06, 10.03, 9.97, 9.94, 9.83, 9.78, 9.77, 9.91, 9.92,
                              9.97, 9.91, 9.9, 9.88, 9.91, 9.63, 9.64, 9.57, 9.55, 9.58, 9.61, 9.62,
                              9.55, 9.57, 9.61, 9.63, 9.64, 9.61, 9.56])
        self.high = np.array([10.07, 10, 10, 10, 10.03, 10.03, 10.04, 10.09, 10.1, 10.14, 10.11, 10.1,
                              10.09, 10.09, 10.1, 10.05, 10.07, 10.09, 10.1, 10, 10.04, 10.04, 10.06,
                              10.09, 10.05, 9.97, 9.96, 9.86, 9.77, 9.92, 9.94, 9.97, 9.97, 9.92, 9.92,
                              9.92, 9.93, 9.64, 9.58, 9.6, 9.58, 9.62, 9.62, 9.64, 9.59, 9.62, 9.63,
                              9.7, 9.66, 9.64])
        self.low = np.array([9.99, 10, 9.97, 9.97, 9.97, 9.98, 9.99, 10.03, 10.03, 10.04, 10.11, 10.07,
                             10.05, 10.03, 10.03, 10.01, 9.99, 10.03, 9.95, 10, 9.95, 10, 10.01, 9.99,
                             9.96, 9.89, 9.83, 9.77, 9.77, 9.8, 9.9, 9.91, 9.89, 9.89, 9.87, 9.85, 9.6,
                             9.64, 9.53, 9.55, 9.54, 9.55, 9.58, 9.54, 9.53, 9.53, 9.63, 9.64, 9.59, 9.56])
        self.volume = np.array([602422, 992935, 397181, 979150, 616616, 816010, 330009, 554499,
                                431742, 155719, 324684, 986208, 840540, 704761, 968846, 863191,
                                282875, 487998, 91664, 811549, 569464, 708073, 978526, 246066,
                                169516, 563430, 671046, 264677, 158782, 992361, 350309, 468395,
                                178206, 83145, 384713, 308022, 380623, 423506, 833615, 473541,
                                841975, 450572, 162390, 550347, 415988, 133953, 754915, 476105,
                                120871, 629045]).astype('float')

    def test_bbands(self):
        print(f'test TA function: bbands\n'
              f'========================')
        upper, middle, lower = bbands(self.close, timeperiod=5)
        print(f'results are\nupper:\n{upper}\nmiddle:\n{middle}\nlower:\n{lower}')

    def test_dema(self):
        print(f'test TA function: dema\n'
              f'======================')
        res = dema(self.close, period=5)
        print(f'result is\n{res}')

    def test_ema(self):
        print(f'test TA function: ema\n'
              f'======================')
        res = ema(self.close, span=5)
        print(f'result is\n{res}')

    def test_ht(self):
        print(f'test TA function: ht\n'
              f'======================')
        res = ht(self.close)
        print(f'result is\n{res}')

    def test_kama(self):
        print(f'test TA function: ht\n'
              f'======================')
        res = kama(self.close, timeperiod=5)
        print(f'result is\n{res}')

    def test_ma(self):
        print(f'test TA function: ma\n'
              f'=====================')
        res = ma(self.close)
        print(f'result is \n{res}')

    def test_mama(self):
        print(f'test TA function: mama\n'
              f'=======================')
        ma, fa = mama(self.close, fastlimit=0.2, slowlimit=0.5)
        print(f'results are \nma:\n{ma}\nfa:\n{fa}')

    def test_mavp(self):
        print(f'test TA function: mavp\n'
              f'=======================')
        periods = np.array([0.1, 0.2, 0.3])
        res = mavp(self.close, periods=self.low)
        print(f'result is \n{res}')

    def test_mid_point(self):
        print(f'test TA function: mid_point\n'
              f'============================')
        res = mid_point(self.close)
        print(f'result is \n{res}')

    def test_mid_price(self):
        print(f'test TA function: mid_price\n'
              f'============================')
        res = mid_price(self.high, self.low)
        print(f'result is \n{res}')

    def test_sar(self):
        print(f'test TA function: sar\n'
              f'======================')
        res = sar(self.high, self.low)
        print(f'result is \n{res}')

    def test_sarext(self):
        print(f'test TA function: sarext\n'
              f'=========================')
        res = sarext(self.high, self.low)
        print(f'result is \n{res}')

    def test_sma(self):
        print(f'test TA function: sma\n'
              f'======================')
        res = sma(self.close)
        print(f'result is \n{res}')

    def test_t3(self):
        print(f'test TA function: t3\n'
              f'=====================')
        res = t3(self.close)
        print(f'result is \n{res}')

    def test_tema(self):
        print(f'test TA function: tema\n'
              f'=======================')
        res = tema(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_trima(self):
        print(f'test TA function: trima\n'
              f'========================')
        res = trima(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_wma(self):
        print(f'test TA function: wma\n'
              f'======================')
        res = wma(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_adx(self):
        print(f'test TA function: adx\n'
              f'======================')
        res = adx(self.high, self.low, self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_adxr(self):
        print(f'test TA function: adxr\n'
              f'=======================')
        res = adxr(self.high, self.low, self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_apo(self):
        print(f'test TA function: apo\n'
              f'======================')
        res = apo(self.close)
        print(f'result is \n{res}')

    def test_aroon(self):
        print(f'test TA function: aroon\n'
              f'========================')
        down, up = aroon(self.high, self.low)
        print(f'results are:\naroon down:\n{down}\naroon up:\n{up}')

    def test_aroonosc(self):
        print(f'test TA function: aroonosc\n'
              f'===========================')
        res = aroonosc(self.high, self.low)
        print(f'result is \n{res}')

    def test_bop(self):
        print(f'test TA function: bop\n'
              f'======================')
        res = bop(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cci(self):
        print(f'test TA function: cci\n'
              f'======================')
        res = cci(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cmo(self):
        print(f'test TA function: cmo\n'
              f'======================')
        res = cmo(self.close)
        print(f'result is \n{res}')

    def test_dx(self):
        print(f'test TA function: dx\n'
              f'=====================')
        res = dx(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_macd(self):
        print(f'test TA function: macd\n'
              f'=======================')
        macd_res, macdsignal, macdhist = macd(self.close)
        print(f'results are:\nmacd:\n{macd_res}\nmacd signal:\n{macdsignal}\nmacd hist:\n{macdhist}')

    def test_macdext(self):
        print(f'test TA function: macdext\n'
              f'==========================')
        macd_res, macdsignal, macdhist = macdext(self.close)
        print(f'results are:\nmacd:\n{macd_res}\nmacd signal:\n{macdsignal}\nmacd hist:\n{macdhist}')

    def test_macdfix(self):
        print(f'test TA function: macdfix\n'
              f'==========================')
        macd_res, macdsignal, macdhist = macdfix(self.close)
        print(f'results are:\nmacd:\n{macd_res}\nmacd signal:\n{macdsignal}\nmacd hist:\n{macdhist}')

    def test_mfi(self):
        print(f'test TA function: mfi\n'
              f'======================')
        res = mfi(self.high, self.low, self.close, self.volume)
        print(f'result is \n{res}')

    def test_minus_di(self):
        print(f'test TA function: minus_di\n'
              f'===========================')
        res = minus_di(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_minus_dm(self):
        print(f'test TA function: minus_dm\n'
              f'===========================')
        res = minus_dm(self.high, self.low)
        print(f'result is \n{res}')

    def test_mom(self):
        print(f'test TA function: mom\n'
              f'======================')
        res = mom(self.close)
        print(f'result is \n{res}')

    def test_plus_di(self):
        print(f'test TA function: plus_di\n'
              f'==========================')
        res = plus_di(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_plus_dm(self):
        print(f'test TA function: plus_dm\n'
              f'==========================')
        res = plus_dm(self.high, self.low)
        print(f'result is \n{res}')

    def test_ppo(self):
        print(f'test TA function: ppo\n'
              f'======================')
        res = ppo(self.close)
        print(f'result is \n{res}')

    def test_roc(self):
        print(f'test TA function: roc\n'
              f'======================')
        res = roc(self.close)
        print(f'result is \n{res}')

    def test_rocp(self):
        print(f'test TA function: rocp\n'
              f'=======================')
        res = rocp(self.close)
        print(f'result is \n{res}')

    def test_rocr(self):
        print(f'test TA function: rocr\n'
              f'=======================')
        res = rocr(self.close)
        print(f'result is \n{res}')

    def test_rocr100(self):
        print(f'test TA function: rocr100\n'
              f'==========================')
        res = rocr100(self.close)
        print(f'result is \n{res}')

    def test_rsi(self):
        print(f'test TA function: rsi\n'
              f'======================')
        res = rsi(self.close)
        print(f'result is \n{res}')

    def test_stoch(self):
        print(f'test TA function: stoch\n'
              f'========================')
        slowk, slowd = stoch(self.high, self.low, self.close)
        print(f'results are\nslowk:\n{slowk}\nslowd:\n{slowd}')

    def test_stochf(self):
        print(f'test TA function: stochf\n'
              f'=========================')
        fastk, fastd = stochf(self.high, self.low, self.close)
        print(f'results are\nfastk:\n{fastk}\nfastd:\n{fastd}')

    def test_stochrsi(self):
        print(f'test TA function: stochrsi\n'
              f'===========================')
        fastk, fastd = stochrsi(self.close)
        print(f'results are\nfastk:\n{fastk}\nfastd:\n{fastd}')

    def test_trix(self):
        print(f'test TA function: trix\n'
              f'=======================')
        res = trix(self.close, timeperiod=5)
        print(f'result is \n{res}')

    def test_ultosc(self):
        print(f'test TA function: ultosc\n'
              f'=========================')
        res = ultosc(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_willr(self):
        print(f'test TA function: willr\n'
              f'========================')
        res = willr(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_ad(self):
        print(f'test TA function: ad\n'
              f'=====================')
        res = ad(self.high, self.low, self.close, self.volume)
        print(f'result is \n{res}')

    def test_adosc(self):
        print(f'test TA function: adosc\n'
              f'========================')
        res = adosc(self.high, self.low, self.close, self.volume)
        print(f'result is \n{res}')

    def test_obv(self):
        print(f'test TA function: obv\n'
              f'======================')
        res = obv(self.close, self.volume)
        print(f'result is \n{res}')

    def test_atr(self):
        print(f'test TA function: atr\n'
              f'======================')
        res = atr(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_natr(self):
        print(f'test TA function: natr\n'
              f'=======================')
        res = natr(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_trange(self):
        print(f'test TA function: trange\n'
              f'=========================')
        res = trange(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_avgprice(self):
        print(f'test TA function: avgprice\n'
              f'===========================')
        res = avgprice(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_medprice(self):
        print(f'test TA function: medprice\n'
              f'===========================')
        res = medprice(self.high, self.low)
        print(f'result is \n{res}')

    def test_typprice(self):
        print(f'test TA function: typprice\n'
              f'===========================')
        res = typprice(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_wclprice(self):
        print(f'test TA function: wclprice\n'
              f'===========================')
        res = wclprice(self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_ht_dcperiod(self):
        print(f'test TA function: ht_dcperiod\n'
              f'==============================')
        res = ht_dcperiod(self.close)
        print(f'result is \n{res}')

    def test_ht_dcphase(self):
        print(f'test TA function: ht_dcphase\n'
              f'=============================')
        res = ht_dcphase(self.close)
        print(f'result is \n{res}')

    def test_ht_phasor(self):
        print(f'test TA function: ht_phasor\n'
              f'============================')
        inphase, quadrature = ht_phasor(self.close)
        print(f'results are\ninphase:\n{inphase}\nquadrature:\n{quadrature}')

    def test_ht_sine(self):
        print(f'test TA function: ht_sine\n'
              f'==========================')
        res_a, res_b = ht_sine(self.close / 10)
        print(f'results are:\nres_a:\n{res_a}\nres_b:\n{res_b}')

    def test_ht_trendmode(self):
        print(f'test TA function: ht_trendmode\n'
              f'===============================')
        res = ht_trendmode(self.close)
        print(f'result is \n{res}')

    def test_cdl2crows(self):
        print(f'test TA function: cdl2crows\n'
              f'============================')
        res = cdl2crows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3blackcrows(self):
        print(f'test TA function: cdl3blackcrows\n'
              f'=================================')
        res = cdl3blackcrows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3inside(self):
        print(f'test TA function: cdl3inside\n'
              f'=============================')
        res = cdl3inside(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3linestrike(self):
        print(f'test TA function: cdl3linestrike\n'
              f'=================================')
        res = cdl3linestrike(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3outside(self):
        print(f'test TA function: cdl3outside\n'
              f'==============================')
        res = cdl3outside(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3starsinsouth(self):
        print(f'test TA function: cdl3starsinsouth\n'
              f'===================================')
        res = cdl3starsinsouth(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdl3whitesoldiers(self):
        print(f'test TA function: cdl3whitesoldiers\n'
              f'====================================')
        res = cdl3whitesoldiers(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlabandonedbaby(self):
        print(f'test TA function: cdlabandonedbaby\n'
              f'===================================')
        res = cdlabandonedbaby(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdladvanceblock(self):
        print(f'test TA function: cdladvanceblock\n'
              f'==================================')
        res = cdladvanceblock(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlbelthold(self):
        print(f'test TA function: cdlbelthold\n'
              f'==============================')
        res = cdlbelthold(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlbreakaway(self):
        print(f'test TA function: cdlbreakaway\n'
              f'===============================')
        res = cdlbreakaway(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlclosingmarubozu(self):
        print(f'test TA function: cdlclosingmarubozu\n'
              f'=====================================')
        res = cdlclosingmarubozu(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlconcealbabyswall(self):
        print(f'test TA function: cdlconcealbabyswall\n'
              f'======================================')
        res = cdlconcealbabyswall(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlcounterattack(self):
        print(f'test TA function: cdlcounterattack\n'
              f'===================================')
        res = cdlcounterattack(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldarkcloudcover(self):
        print(f'test TA function: cdldarkcloudcover\n'
              f'====================================')
        res = cdldarkcloudcover(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldoji(self):
        print(f'test TA function: cdldoji\n'
              f'==========================')
        res = cdldoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldojistar(self):
        print(f'test TA function: cdldojistar\n'
              f'==============================')
        res = cdldojistar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdldragonflydoji(self):
        print(f'test TA function: cdldragonflydoji\n'
              f'===================================')
        res = cdldragonflydoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlengulfing(self):
        print(f'test TA function: cdlengulfing\n'
              f'===============================')
        res = cdlengulfing(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdleveningdojistar(self):
        print(f'test TA function: cdleveningdojistar\n'
              f'=====================================')
        res = cdleveningdojistar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdleveningstar(self):
        print(f'test TA function: cdleveningstar\n'
              f'=================================')
        res = cdleveningstar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlgapsidesidewhite(self):
        print(f'test TA function: cdlgapsidesidewhite\n'
              f'======================================')
        res = cdlgapsidesidewhite(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlgravestonedoji(self):
        print(f'test TA function: cdlgravestonedoji\n'
              f'====================================')
        res = cdlgravestonedoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhammer(self):
        print(f'test TA function: cdlhammer\n'
              f'============================')
        res = cdlhammer(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhangingman(self):
        print(f'test TA function: cdlhangingman\n'
              f'================================')
        res = cdlhangingman(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlharami(self):
        print(f'test TA function: cdlharami\n'
              f'============================')
        res = cdlharami(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlharamicross(self):
        print(f'test TA function: cdlharamicross\n'
              f'=================================')
        res = cdlharamicross(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhighwave(self):
        print(f'test TA function: cdlhighwave\n'
              f'==============================')
        res = cdlhighwave(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhikkake(self):
        print(f'test TA function: cdlhikkake\n'
              f'=============================')
        res = cdlhikkake(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhikkakemod(self):
        print(f'test TA function: cdlhikkakemod\n'
              f'================================')
        res = cdlhikkakemod(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlhomingpigeon(self):
        print(f'test TA function: cdlhomingpigeon\n'
              f'==================================')
        res = cdlhomingpigeon(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlidentical3crows(self):
        print(f'test TA function: cdlidentical3crows\n'
              f'=====================================')
        res = cdlidentical3crows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlinneck(self):
        print(f'test TA function: cdlinneck\n'
              f'============================')
        res = cdlinneck(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlinvertedhammer(self):
        print(f'test TA function: cdlinvertedhammer\n'
              f'====================================')
        res = cdlinvertedhammer(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlkicking(self):
        print(f'test TA function: cdlkicking\n'
              f'=============================')
        res = cdlkicking(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlkickingbylength(self):
        print(f'test TA function: cdlkickingbylength\n'
              f'=====================================')
        res = cdlkickingbylength(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlladderbottom(self):
        print(f'test TA function: cdlladderbottom\n'
              f'==================================')
        res = cdlladderbottom(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdllongleggeddoji(self):
        print(f'test TA function: cdllongleggeddoji\n'
              f'====================================')
        res = cdllongleggeddoji(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdllongline(self):
        print(f'test TA function: cdllongline\n'
              f'==============================')
        res = cdllongline(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmarubozu(self):
        print(f'test TA function: cdlmarubozu\n'
              f'==============================')
        res = cdlmarubozu(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmatchinglow(self):
        print(f'test TA function: cdlmatchinglow\n'
              f'=================================')
        res = cdlmatchinglow(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmathold(self):
        print(f'test TA function: cdlmathold\n'
              f'=============================')
        res = cdlmathold(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmorningdojistar(self):
        print(f'test TA function: cdlmorningdojistar\n'
              f'=====================================')
        res = cdlmorningdojistar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlmorningstar(self):
        print(f'test TA function: cdlmorningstar\n'
              f'=================================')
        res = cdlmorningstar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlonneck(self):
        print(f'test TA function: cdlonneck\n'
              f'============================')
        res = cdlonneck(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlpiercing(self):
        print(f'test TA function: cdlpiercing\n'
              f'==============================')
        res = cdlpiercing(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlrickshawman(self):
        print(f'test TA function: cdlrickshawman\n'
              f'=================================')
        res = cdlrickshawman(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlrisefall3methods(self):
        print(f'test TA function: cdlrisefall3methods\n'
              f'======================================')
        res = cdlrisefall3methods(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlseparatinglines(self):
        print(f'test TA function: cdlseparatinglines\n'
              f'=====================================')
        res = cdlseparatinglines(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlshootingstar(self):
        print(f'test TA function: cdlshootingstar\n'
              f'==================================')
        res = cdlshootingstar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlshortline(self):
        print(f'test TA function: cdlshortline\n'
              f'===============================')
        res = cdlshortline(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlspinningtop(self):
        print(f'test TA function: cdlspinningtop\n'
              f'=================================')
        res = cdlspinningtop(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlstalledpattern(self):
        print(f'test TA function: cdlstalledpattern\n'
              f'====================================')
        res = cdlstalledpattern(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlsticksandwich(self):
        print(f'test TA function: cdlsticksandwich\n'
              f'===================================')
        res = cdlsticksandwich(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdltakuri(self):
        print(f'test TA function: cdltakuri\n'
              f'============================')
        res = cdltakuri(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdltasukigap(self):
        print(f'test TA function: cdltasukigap\n'
              f'===============================')
        res = cdltasukigap(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlthrusting(self):
        print(f'test TA function: cdlthrusting\n'
              f'===============================')
        res = cdlthrusting(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdltristar(self):
        print(f'test TA function: cdltristar\n'
              f'=============================')
        res = cdltristar(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlunique3river(self):
        print(f'test TA function: cdlunique3river\n'
              f'==================================')
        res = cdlunique3river(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlupsidegap2crows(self):
        print(f'test TA function: cdlupsidegap2crows\n'
              f'=====================================')
        res = cdlupsidegap2crows(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_cdlxsidegap3methods(self):
        print(f'test TA function: cdlxsidegap3methods\n'
              f'======================================')
        res = cdlxsidegap3methods(self.open, self.high, self.low, self.close)
        print(f'result is \n{res}')

    def test_beta(self):
        print(f'test TA function: beta\n'
              f'=======================')
        res = beta(self.high, self.low)
        print(f'result is \n{res}')

    def test_correl(self):
        print(f'test TA function: correl\n'
              f'=========================')
        res = correl(self.high, self.low)
        print(f'result is \n{res}')

    def test_linearreg(self):
        print(f'test TA function: linearreg\n'
              f'============================')
        res = linearreg(self.close)
        print(f'result is \n{res}')

    def test_linearreg_angle(self):
        print(f'test TA function: linearreg_angle\n'
              f'==================================')
        res = linearreg_angle(self.close)
        print(f'result is \n{res}')

    def test_linearreg_intercept(self):
        print(f'test TA function: linearreg_intercept\n'
              f'======================================')
        res = linearreg_intercept(self.close)
        print(f'result is \n{res}')

    def test_linearreg_slope(self):
        print(f'test TA function: linearreg_slope\n'
              f'==================================')
        res = linearreg_slope(self.close)
        print(f'result is \n{res}')

    def test_stddev(self):
        print(f'test TA function: stddev\n'
              f'=========================')
        res = stddev(self.close)
        print(f'result is \n{res}')

    def test_tsf(self):
        print(f'test TA function: tsf\n'
              f'======================')
        res = tsf(self.close)
        print(f'result is \n{res}')

    def test_var(self):
        print(f'test TA function: var\n'
              f'======================')
        res = var(self.close)
        print(f'result is \n{res}')

    def test_acos(self):
        print(f'test TA function: acos\n'
              f'=======================')
        res = acos(self.close)
        print(f'result is \n{res}')

    def test_asin(self):
        print(f'test TA function: asin\n'
              f'=======================')
        res = asin(self.close / 10)
        print(f'result is \n{res}')

    def test_atan(self):
        print(f'test TA function: atan\n'
              f'=======================')
        res = atan(self.close)
        print(f'result is \n{res}')

    def test_ceil(self):
        print(f'test TA function: ceil\n'
              f'=======================')
        res = ceil(self.close)
        print(f'result is \n{res}')

    def test_cos(self):
        print(f'test TA function: cos\n'
              f'======================')
        res = cos(self.close)
        print(f'result is \n{res}')

    def test_cosh(self):
        print(f'test TA function: cosh\n'
              f'=======================')
        res = cosh(self.close)
        print(f'result is \n{res}')

    def test_exp(self):
        print(f'test TA function: exp\n'
              f'======================')
        res = exp(self.close)
        print(f'result is \n{res}')

    def test_floor(self):
        print(f'test TA function: floor\n'
              f'========================')
        res = floor(self.close)
        print(f'result is \n{res}')

    def test_ln(self):
        print(f'test TA function: ln\n'
              f'=====================')
        res = ln(self.close)
        print(f'result is \n{res}')

    def test_log10(self):
        print(f'test TA function: log10\n'
              f'========================')
        res = log10(self.close)
        print(f'result is \n{res}')

    def test_sin(self):
        print(f'test TA function: sin\n'
              f'======================')
        res = sin(self.close)
        print(f'result is \n{res}')

    def test_sinh(self):
        print(f'test TA function: sinh\n'
              f'=======================')
        res = sinh(self.close)
        print(f'result is \n{res}')

    def test_sqrt(self):
        print(f'test TA function: sqrt\n'
              f'=======================')
        res = sqrt(self.close)
        print(f'result is \n{res}')

    def test_tan(self):
        print(f'test TA function: tan\n'
              f'======================')
        res = tan(self.close)
        print(f'result is \n{res}')

    def test_tanh(self):
        print(f'test TA function: tanh\n'
              f'=======================')
        res = tanh(self.close)
        print(f'result is \n{res}')

    def test_add(self):
        print(f'test TA function: add\n'
              f'======================')
        res = add(self.high, self.low)
        print(f'result is \n{res}')

    def test_div(self):
        print(f'test TA function: div\n'
              f'======================')
        res = div(self.high, self.low)
        print(f'result is \n{res}')

    def test_max(self):
        print(f'test TA function: max\n'
              f'======================')
        res = max(self.close)
        print(f'result is \n{res}')

    def test_maxindex(self):
        print(f'test TA function: maxindex\n'
              f'===========================')
        res = maxindex(self.close)
        print(f'result is \n{res}')

    def test_min(self):
        print(f'test TA function: min\n'
              f'======================')
        res = min(self.close)
        print(f'result is \n{res}')

    def test_minindex(self):
        print(f'test TA function: minindex\n'
              f'===========================')
        res = minindex(self.close)
        print(f'result is \n{res}')

    def test_minmax(self):
        print(f'test TA function: minmax\n'
              f'=========================')
        min, max = minmax(self.close)
        print(f'results are:\nmin:\n{min}\nmax:\n{max}')

    def test_minmaxindex(self):
        print(f'test TA function: minmaxindex\n'
              f'==============================')
        minidx, maxidx = minmaxindex(self.close)
        print(f'results are:\nmin index:\n{minidx}\nmax index:\n{maxidx}')

    def test_mult(self):
        print(f'test TA function: mult\n'
              f'=======================')
        res = mult(self.high, self.low)
        print(f'result is \n{res}')

    def test_sub(self):
        print(f'test TA function: sub\n'
              f'======================')
        res = sub(self.high, self.low)
        print(f'result is \n{res}')

    def test_sum(self):
        print(f'test TA function: sum\n'
              f'======================')
        res = sum(self.close)
        print(f'result is \n{res}')


if __name__ == '__main__':
    unittest.main()