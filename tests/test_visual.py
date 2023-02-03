# coding=utf-8
# ======================================
# File:     test_visual.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy visual
#   effects.
# ======================================
import unittest
import qteasy as qt


class TestVisual(unittest.TestCase):
    """ 测试图表视觉效果

    """

    def test_candle(self):
        print(f'test mpf plot in candle form')
        self.data = qt.candle('513100.SH', start='2020-12-01', end='20210131', asset_type='FD')
        print(f'get arr from mpf plot function for adj = "none"')
        qt.candle('000002.SZ', start='2018-12-01', end='2019-01-31', asset_type='E', adj='none')
        print(f'get arr from mpf plot function for adj = "back"')
        qt.candle('600000.SH', start='2018-12-01', end='2019-01-31', asset_type='E', adj='back')
        print(f'get arr from mpf plot function for other parameters')
        qt.candle('600000.SH', start='2018-12-01', end='2019-01-31',
                  asset_type='E',
                  adj='back',
                  mav=[9, 12, 6],
                  avg_type='bb',
                  indicator='rsi',
                  indicator_par=(12,))
        print(f'test plot mpf arr with indicator macd')
        qt.candle(stock_data=self.data,
                  start='20201101',
                  end='20201231',
                  indicator='macd', indicator_par=(12, 26, 9))
        print('test candle with pre_defined simple parameters')
        print('all following function calls will generate correct plot')
        qt.candle('000001')
        qt.candle('000001', asset_type='E')
        qt.candle('000001', asset_type='IDX')
        qt.candle('000001', asset_type='E', adj='f')
        qt.candle('000001', mav=[9, 12, 26], adj='b')
        qt.candle('000300')
        qt.candle('000300', asset_type='IDX')

        qt.candle('159601', start='20200121', freq='h', adj='n')
        qt.candle('沪镍主力', start='20211021')
        qt.candle('000001.OF', start='20200101', asset_type='FD', adj='b')
        qt.candle('000001.OF', start='20200101', asset_type='FD', adj='n', mav=[])

    def test_indicators(self):
        print(f'test mpf plot in candle form with indicator dema')
        qt.candle('513100.SH', start='2020-04-01', end='20200601', asset_type='FD', indicator='dema',
                  indicator_par=(20,))
        print(f'test mpf plot in candle form with indicator rsi')
        qt.candle('513100.SH', start='2020-04-01', end='20200601', asset_type='FD', indicator='rsi',
                  indicator_par=(12,))
        print(f'test mpf plot in candle form with indicator macd')
        qt.candle('513100.SH', start='2020-04-01', end='20200601', asset_type='FD', indicator='macd',
                  indicator_par=(12, 26, 9))
        print(f'test mpf plot in candle form with indicator bbands')
        qt.candle('513100.SH', start='2020-04-01', end='20200601', asset_type='FD', indicator='bbands',
                  indicator_par=(12, 26, 9))


if __name__ == '__main__':
    unittest.main()