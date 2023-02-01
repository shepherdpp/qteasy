# coding=utf-8
# ======================================
# File:     test_utilityfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy utility
#   functionalities.
# ======================================
import unittest

import pandas as pd
import numpy as np
import datetime
import logging

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, time_str_format, str_to_list
from qteasy.utilfuncs import maybe_trade_day, is_market_trade_day, prev_trade_day, next_trade_day
from qteasy.utilfuncs import next_market_trade_day, unify, list_or_slice, labels_to_dict, retry
from qteasy.utilfuncs import weekday_name, nearest_market_trade_day, is_number_like, list_truncate, input_to_list
from qteasy.utilfuncs import match_ts_code, _lev_ratio, _partial_lev_ratio, _wildcard_match, rolling_window
from qteasy.utilfuncs import reindent, truncate_string


class RetryableError(Exception):
    """ 用于retry测试的自定义Error Type"""
    pass


class AnotherRetryableError(Exception):
    """ 用于retry测试的自定义Error Type"""
    pass


class UnexpectedError(Exception):
    """ 用于retry测试的自定义Error Type"""
    pass


class TestUtilityFuncs(unittest.TestCase):
    def setUp(self):
        pass

    def test_unify(self):
        n1 = 2
        self.assertEqual(unify(n1), 2)
        n2 = np.array([[1., 1., 1., 1.], [0., 1., 0., 1.]])
        n3 = np.array([[.25, .25, .25, .25], [0., .5, 0., .5]])
        self.assertTrue(np.allclose(unify(n2), n3))

    def test_time_string_format(self):
        print('Testing qt.time_string_format() function:')
        t = 3.14
        self.assertEqual(time_str_format(t), '3s 140.0ms')
        self.assertEqual(time_str_format(t, estimation=True), '3s ')
        self.assertEqual(time_str_format(t, short_form=True), '3"140')
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), '3"')
        t = 300.14
        self.assertEqual(time_str_format(t), '5min 140.0ms')
        self.assertEqual(time_str_format(t, estimation=True), '5min ')
        self.assertEqual(time_str_format(t, short_form=True), "5'140")
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), "5'")
        t = 7435.0014
        self.assertEqual(time_str_format(t), '2hrs 3min 55s 1.4ms')
        self.assertEqual(time_str_format(t, estimation=True), '2hrs ')
        self.assertEqual(time_str_format(t, short_form=True), "2H3'55\"001")
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), "2H")
        t = 88425.0509
        self.assertEqual(time_str_format(t), '1days 33min 45s 50.9ms')
        self.assertEqual(time_str_format(t, estimation=True), '1days ')
        self.assertEqual(time_str_format(t, short_form=True), "1D33'45\"051")
        self.assertEqual(time_str_format(t, estimation=True, short_form=True), "1D")

    def test_str_to_list(self):
        self.assertEqual(str_to_list('a,b,c,d,e'), ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(str_to_list('a, b, c '), ['a', 'b', 'c'])
        self.assertEqual(str_to_list('a, b: c', sep_char=':'), ['a,b', 'c'])
        self.assertEqual(str_to_list('abc'), ['abc'])
        self.assertEqual(str_to_list(''), [])
        self.assertRaises(AssertionError, str_to_list, 123)

    def test_list_or_slice(self):
        str_dict = {'close': 0, 'open': 1, 'high': 2, 'low': 3}
        self.assertEqual(list_or_slice(slice(1, 2, 1), str_dict), slice(1, 2, 1))
        self.assertEqual(list_or_slice('open', str_dict), [1])
        self.assertEqual(list(list_or_slice('close, high, low', str_dict)), [0, 2, 3])
        self.assertEqual(list(list_or_slice('close:high', str_dict)), [0, 1, 2])
        self.assertEqual(list(list_or_slice(['open'], str_dict)), [1])
        self.assertEqual(list(list_or_slice(['open', 'high'], str_dict)), [1, 2])
        self.assertEqual(list(list_or_slice(0, str_dict)), [0])
        self.assertEqual(list(list_or_slice([0, 2], str_dict)), [0, 2])
        self.assertEqual(list(list_or_slice([True, False, True, False], str_dict)), [0, 2])

    def test_labels_to_dict(self):
        target_list = [0, 1, 10, 100]
        target_dict = {'close': 0, 'open': 1, 'high': 2, 'low': 3}
        target_dict2 = {'close': 0, 'open': 2, 'high': 1, 'low': 3}
        self.assertEqual(labels_to_dict('close, open, high, low', target_list), target_dict)
        self.assertEqual(labels_to_dict(['close', 'open', 'high', 'low'], target_list), target_dict)
        self.assertEqual(labels_to_dict('close, high, open, low', target_list), target_dict2)
        self.assertEqual(labels_to_dict(['close', 'high', 'open', 'low'], target_list), target_dict2)

    def test_input_to_list(self):
        """ test util function input_to_list()"""
        self.assertEqual(input_to_list(5, 3), [5, 5, 5])
        self.assertEqual(input_to_list(5, 3, 0), [5, 5, 5])
        self.assertEqual(input_to_list([5], 3, 0), [5, 0, 0])
        self.assertEqual(input_to_list([5, 4], 3, 0), [5, 4, 0])

    def test_regulate_date_format(self):
        self.assertEqual(regulate_date_format('2019/11/06'), '20191106')
        self.assertEqual(regulate_date_format('2019-11-06'), '20191106')
        self.assertEqual(regulate_date_format('20191106'), '20191106')
        self.assertEqual(regulate_date_format('191106'), '20061119')
        self.assertEqual(regulate_date_format('830522'), '19830522')
        self.assertEqual(regulate_date_format(datetime.datetime(2010, 3, 15)), '20100315')
        self.assertEqual(regulate_date_format(pd.Timestamp('2010.03.15')), '20100315')
        self.assertRaises(ValueError, regulate_date_format, 'abc')
        self.assertRaises(ValueError, regulate_date_format, '2019/13/43')

    def test_list_to_str_format(self):
        self.assertEqual(list_to_str_format(['close', 'open', 'high', 'low']),
                         'close,open,high,low')
        self.assertEqual(list_to_str_format(['letters', '  ', '123  4', 123, '   kk  l']),
                         'letters,,1234,kkl')
        self.assertEqual(list_to_str_format('a string input'),
                         'a,string,input')
        self.assertEqual(list_to_str_format('already,a,good,string'),
                         'already,a,good,string')
        self.assertRaises(AssertionError, list_to_str_format, 123)

    def test_is_trade_day(self):
        """test if the funcion maybe_trade_day() and is_market_trade_day() works properly
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        date_weekend = '20210424'
        date_seems_trade_day = '20210217'
        date_too_early = '19890601'
        date_too_late = '20500105'
        date_christmas = '20201225'

        self.assertTrue(maybe_trade_day(date_trade))
        self.assertFalse(maybe_trade_day(date_holiday))
        self.assertFalse(maybe_trade_day(date_weekend))
        self.assertTrue(maybe_trade_day(date_seems_trade_day))
        self.assertTrue(maybe_trade_day(date_too_early))
        self.assertTrue(maybe_trade_day(date_too_late))
        self.assertTrue(maybe_trade_day(date_christmas))
        self.assertTrue(is_market_trade_day(date_trade))
        self.assertFalse(is_market_trade_day(date_holiday))
        self.assertFalse(is_market_trade_day(date_weekend))
        self.assertFalse(is_market_trade_day(date_seems_trade_day))
        self.assertTrue(is_market_trade_day(date_christmas))
        self.assertFalse(is_market_trade_day(date_christmas, exchange='XHKG'))

        # raises when date out of range
        self.assertRaises(ValueError, is_market_trade_day, date_too_early)
        self.assertRaises(ValueError, is_market_trade_day, date_too_late)

        date_trade = pd.to_datetime('20210401')
        date_holiday = pd.to_datetime('20210102')
        date_weekend = pd.to_datetime('20210424')

        self.assertTrue(maybe_trade_day(date_trade))
        self.assertFalse(maybe_trade_day(date_holiday))
        self.assertFalse(maybe_trade_day(date_weekend))

    def test_weekday_name(self):
        """ test util func weekday_name()"""
        self.assertEqual(weekday_name(0), 'Monday')
        self.assertEqual(weekday_name(1), 'Tuesday')
        self.assertEqual(weekday_name(2), 'Wednesday')
        self.assertEqual(weekday_name(3), 'Thursday')
        self.assertEqual(weekday_name(4), 'Friday')
        self.assertEqual(weekday_name(5), 'Saturday')
        self.assertEqual(weekday_name(6), 'Sunday')

    def test_list_truncate(self):
        """ test util func list_truncate()"""
        the_list = [1, 2, 3, 4, 5]
        ls = list_truncate(the_list, 2)
        self.assertEqual(ls[0], [1, 2])
        self.assertEqual(ls[1], [3, 4])
        self.assertEqual(ls[2], [5])

        self.assertRaises(AssertionError, list_truncate, the_list, 0)
        self.assertRaises(AssertionError, list_truncate, 12, 0)
        self.assertRaises(AssertionError, list_truncate, 0, the_list)

    def test_maybe_trade_day(self):
        """ test util function maybe_trade_day()"""
        self.assertTrue(maybe_trade_day('20220104'))
        self.assertTrue(maybe_trade_day('2021-12-31'))
        self.assertTrue(maybe_trade_day(pd.to_datetime('2020/03/06')))

        self.assertFalse(maybe_trade_day('2020-01-01'))
        self.assertFalse(maybe_trade_day('2020/10/06'))

        self.assertRaises(Exception, maybe_trade_day, 'aaa')

    def test_prev_trade_day(self):
        """test the function prev_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        prev_holiday = pd.to_datetime(date_holiday) - pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        prev_weekend = pd.to_datetime(date_weekend) - pd.Timedelta(1, 'd')
        date_seems_trade_day = '20210217'
        prev_seems_trade_day = '20210217'
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        self.assertEqual(pd.to_datetime(prev_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_holiday)),
                         pd.to_datetime(prev_holiday))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_weekend)),
                         pd.to_datetime(prev_weekend))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_seems_trade_day)),
                         pd.to_datetime(prev_seems_trade_day))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_too_early)),
                         pd.to_datetime(date_too_early))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_too_late)),
                         pd.to_datetime(date_too_late))
        self.assertEqual(pd.to_datetime(prev_trade_day(date_christmas)),
                         pd.to_datetime(date_christmas))

    def test_next_trade_day(self):
        """ test the function next_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        next_holiday = pd.to_datetime(date_holiday) + pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        next_weekend = pd.to_datetime(date_weekend) + pd.Timedelta(2, 'd')
        date_seems_trade_day = '20210217'
        next_seems_trade_day = '20210217'
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        self.assertEqual(pd.to_datetime(next_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(next_trade_day(date_holiday)),
                         pd.to_datetime(next_holiday))
        self.assertEqual(pd.to_datetime(next_trade_day(date_weekend)),
                         pd.to_datetime(next_weekend))
        self.assertEqual(pd.to_datetime(next_trade_day(date_seems_trade_day)),
                         pd.to_datetime(next_seems_trade_day))
        self.assertEqual(pd.to_datetime(next_trade_day(date_too_early)),
                         pd.to_datetime(date_too_early))
        self.assertEqual(pd.to_datetime(next_trade_day(date_too_late)),
                         pd.to_datetime(date_too_late))
        self.assertEqual(pd.to_datetime(next_trade_day(date_christmas)),
                         pd.to_datetime(date_christmas))

    def test_nearest_market_trade_day(self):
        """ test the function nearest_market_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        prev_holiday = pd.to_datetime(date_holiday) - pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        prev_weekend = pd.to_datetime(date_weekend) - pd.Timedelta(1, 'd')
        date_seems_trade_day = '20210217'
        prev_seems_trade_day = pd.to_datetime(date_seems_trade_day) - pd.Timedelta(7, 'd')
        date_too_early = '19890601'
        date_too_late = '20240105'
        date_christmas = '20201225'
        prev_christmas_xhkg = '20201224'
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_holiday)),
                         pd.to_datetime(prev_holiday))
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_weekend)),
                         pd.to_datetime(prev_weekend))
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_seems_trade_day)),
                         pd.to_datetime(prev_seems_trade_day))
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_too_early)),
                         None)
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_too_late)),
                         None)
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_christmas, 'SSE')),
                         pd.to_datetime(date_christmas))
        self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_christmas, 'XHKG')),
                         pd.to_datetime(prev_christmas_xhkg))

    def test_next_market_trade_day(self):
        """ test the function next_market_trade_day()
        """
        date_trade = '20210401'
        date_holiday = '20210102'
        next_holiday = pd.to_datetime(date_holiday) + pd.Timedelta(2, 'd')
        date_weekend = '20210424'
        next_weekend = pd.to_datetime(date_weekend) + pd.Timedelta(2, 'd')
        date_seems_trade_day = '20210217'
        next_seems_trade_day = pd.to_datetime(date_seems_trade_day) + pd.Timedelta(1, 'd')
        date_too_early = '19890601'
        date_too_late = '20230105'
        date_christmas = '20201225'
        next_christmas_xhkg = '20201228'
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_trade)),
                         pd.to_datetime(date_trade))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_holiday)),
                         pd.to_datetime(next_holiday))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_weekend)),
                         pd.to_datetime(next_weekend))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_seems_trade_day)),
                         pd.to_datetime(next_seems_trade_day))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_too_early)),
                         None)
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_too_late)),
                         None)
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_christmas, 'SSE')),
                         pd.to_datetime(date_christmas))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_christmas, 'XHKG')),
                         pd.to_datetime(next_christmas_xhkg))

    def test_is_number_like(self):
        """test the function: is_number_like()"""
        self.assertTrue(is_number_like(123))
        self.assertTrue(is_number_like(23.7))
        self.assertTrue(is_number_like('2.3'))
        self.assertTrue(is_number_like('-0.2'))
        self.assertTrue(is_number_like('0.03'))
        self.assertTrue(is_number_like('345'))
        self.assertTrue(is_number_like('-45.321'))

        self.assertFalse(is_number_like('-..023'))
        self.assertFalse(is_number_like('abc'))
        self.assertFalse(is_number_like('0.32a'))
        self.assertFalse(is_number_like('0-2'))

    def test_retry_decorator(self):
        """ test the retry decorator"""
        print(f'test no retry needed functions')
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def succeeds():
            self.counter += 1
            return 'success'

        r = succeeds()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 1)

        print(f'test retry only once')
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        r = fails_once()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 2)

        print(f'test retry limit is reached')
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def always_fails():
            self.counter += 1
            raise RetryableError('failed')

        with self.assertRaises(RetryableError):
            always_fails()
        self.assertEqual(self.counter, 4)

        print(f'test checking for multiple exceptions')
        self.counter = 0

        @retry((RetryableError, AnotherRetryableError), tries=4, delay=0.1)
        def raise_multiple_exceptions():
            self.counter += 1
            if self.counter == 1:
                raise RetryableError('a retryable error')
            elif self.counter == 2:
                raise AnotherRetryableError('another retryable error')
            else:
                return 'success'

        r = raise_multiple_exceptions()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 3)

        print(f'does not retry when unexpected error occurs')

        @retry(RetryableError, tries=4, delay=0.1)
        def raise_unexpected_error():
            raise UnexpectedError('unexpected error')

        with self.assertRaises(UnexpectedError):
            raise_unexpected_error()

        print(f'test recording info with a logger')
        self.counter = 0
        # set up the logger object
        sh = logging.StreamHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(sh)

        @retry(RetryableError, tries=4, delay=0.1, logger=logger)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        fails_once()

    def test_lev_match(self):
        """ 测试字符串模糊匹配"""
        print(_lev_ratio('abc', 'ABC'))
        print(_lev_ratio('abcdefg', 'abDdefh'))
        print(_lev_ratio('中国移动', '中国移动总公司'))
        print(_lev_ratio('平安', '平安银行股份有限公司'))
        print(_lev_ratio('中国平安', '平安银行股份有限公司'))
        print(_lev_ratio('平安', '万科企业股份有限公司'))

        print(_partial_lev_ratio('abc', 'ABC'))
        print(_partial_lev_ratio('abcdefg', 'abDdefh'))
        print(_partial_lev_ratio('中国移动', '中国移动总公司'))
        print(_partial_lev_ratio('平安', '平安银行股份有限公司'))
        print(_partial_lev_ratio('中国平安', '平安银行股份有限公司'))
        print(_partial_lev_ratio('平安', '万科企业股份有限公司'))
        print(_partial_lev_ratio('常辅股份', '常州电站辅机股份有限公司'))

        print(_partial_lev_ratio('平?', '万科企业股份有限公司'))
        print(_partial_lev_ratio('常?股份', '常州电站辅机股份有限公司'))

    def test_wildcard_match(self):
        """ 测试字符串通配符匹配"""
        wordlist = ["color", "colour", "work", "working", "fox", "worker", "working"]
        print(_wildcard_match('col?r', wordlist))
        print(_wildcard_match('col*r', wordlist))
        print(_wildcard_match('wor.?', wordlist))
        print(_wildcard_match('?o?', wordlist))

    def test_match_ts_code(self):
        """ 测试匹配ts_code"""
        print(f"matching {'000001'}: \n{match_ts_code('000001')}")
        print(f"matching {'000001.CZC'}: \n{match_ts_code('000001.CZC')}")
        print(f"matching {'ABC.CZC'}: \n{match_ts_code('ABC.CZC')}")
        print(f"matching {'中国电信'}: \n{match_ts_code('中国电信')}")
        print(f"matching {'嘉实服务'}: \n{match_ts_code('嘉实服务')}")
        print(f"matching {'中?集团'}: \n{match_ts_code('中?集团')}")
        print(f"matching {'中*金'}: \n{match_ts_code('中*金')}")
        print(f"matching {'工商银行'}: \n{match_ts_code('工商银行')}")
        print(f"matching {'贵州钢绳'}: \n{match_ts_code('贵州钢绳')}")
        print(f"matching {'贵州钢绳'} with match_full_name: \n{match_ts_code('贵州钢绳', match_full_name=True)}")
        print(f"matching {'招商银行'} with asset_type = 'E, FD': \n{match_ts_code('招商银行', asset_types='E, FD')}")
        print(f"matching {'贵阳银行'} with asset_type = 'E, FT': \n{match_ts_code('贵阳银行', asset_types='E, FT')}")

    def test_rolling_window(self):
        """ 测试含税rolling_window()"""
        # test 1d array
        arr = np.array([1, 2, 3, 4, 5])
        window = rolling_window(arr, window=3, axis=0)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[1, 2, 3],
                           [2, 3, 4],
                           [3, 4, 5]])
        self.assertTrue(np.allclose(window, target))
        # test 2d array
        arr = np.array([[1, 2, 3, 4],
                        [5, 6, 7, 8],
                        [9, 0, 1, 2]])
        window = rolling_window(arr, window=2, axis=0)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[[1, 2, 3, 4],
                            [5, 6, 7, 8]],
                           [[5, 6, 7, 8],
                            [9, 0, 1, 2]]])
        self.assertTrue(np.allclose(window, target))
        window = rolling_window(arr, window=3, axis=1)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[[1, 2, 3],
                            [5, 6, 7],
                            [9, 0, 1]],
                           [[2, 3, 4],
                            [6, 7, 8],
                            [0, 1, 2]]])
        self.assertTrue(np.allclose(window, target))
        # test 3d array
        arr = np.array([[[1, 2, 3, 4],
                         [5, 6, 7, 8],
                         [9, 0, 1, 2]],

                        [[3, 4, 5, 6],
                         [7, 8, 9, 0],
                         [1, 2, 3, 4]],

                        [[5, 6, 7, 8],
                         [9, 0, 1, 2],
                         [3, 4, 5, 6]]])
        window = rolling_window(arr, window=2, axis=0)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[[[1, 2, 3, 4],
                             [5, 6, 7, 8],
                             [9, 0, 1, 2]],

                            [[3, 4, 5, 6],
                             [7, 8, 9, 0],
                             [1, 2, 3, 4]]],

                           [[[3, 4, 5, 6],
                             [7, 8, 9, 0],
                             [1, 2, 3, 4]],

                            [[5, 6, 7, 8],
                             [9, 0, 1, 2],
                             [3, 4, 5, 6]]]])
        self.assertTrue(np.allclose(window, target))
        window = rolling_window(arr, window=2, axis=1)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[[[1, 2, 3, 4],
                             [5, 6, 7, 8]],

                            [[3, 4, 5, 6],
                             [7, 8, 9, 0]],

                            [[5, 6, 7, 8],
                             [9, 0, 1, 2]]],

                           [[[5, 6, 7, 8],
                             [9, 0, 1, 2]],

                            [[7, 8, 9, 0],
                             [1, 2, 3, 4]],

                            [[9, 0, 1, 2],
                             [3, 4, 5, 6]]]])
        self.assertTrue(np.allclose(window, target))
        window = rolling_window(arr, window=3, axis=2)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[[[1, 2, 3],
                             [5, 6, 7],
                             [9, 0, 1]],

                            [[3, 4, 5],
                             [7, 8, 9],
                             [1, 2, 3]],

                            [[5, 6, 7],
                             [9, 0, 1],
                             [3, 4, 5]]],

                           [[[2, 3, 4],
                             [6, 7, 8],
                             [0, 1, 2]],

                            [[4, 5, 6],
                             [8, 9, 0],
                             [2, 3, 4]],

                            [[6, 7, 8],
                             [0, 1, 2],
                             [4, 5, 6]]]
                           ])
        self.assertTrue(np.allclose(window, target))

        # test false input
        arr = np.array([[[1, 2, 3, 4],
                         [5, 6, 7, 8],
                         [9, 0, 1, 2]],

                        [[3, 4, 5, 6],
                         [7, 8, 9, 0],
                         [1, 2, 3, 4]],

                        [[5, 6, 7, 8],
                         [9, 0, 1, 2],
                         [3, 4, 5, 6]]])
        self.assertRaises(TypeError, rolling_window, 1, 1, 1)
        self.assertRaises(TypeError, rolling_window, 1, 's', 1)
        self.assertRaises(TypeError, rolling_window, 1, 1, 's')
        self.assertRaises(ValueError, rolling_window, arr, 1, -1)
        self.assertRaises(ValueError, rolling_window, arr, -1, -1)
        self.assertRaises(ValueError, rolling_window, arr, 5, 1)
        self.assertRaises(ValueError, rolling_window, arr, 2, 3)

    def test_reindent(self):
        """ 测试reindent函数"""
        string = 'a random string'
        mul_str = 'a multiple-line random string\n' \
                  ' a multiple-line random string\n' \
                  'a multiple-line random string'

        self.assertEqual(reindent(string, 4), '    a random string')
        self.assertEqual(reindent(mul_str, 4), '    a multiple-line random string\n'
                                               '    a multiple-line random string\n'
                                               '    a multiple-line random string')

        self.assertRaises(TypeError, reindent, 123, 123)
        self.assertRaises(TypeError, reindent, '123', '123')
        self.assertRaises(ValueError, reindent, '123', 123)

    def test_truncate_string(self):
        """ 测试函数truncates_string"""
        self.assertEqual(truncate_string('this is a long string', 2), '..')
        self.assertEqual(truncate_string('this is a long string', 7), 'this...')
        self.assertEqual(truncate_string('this is a long string', 21), 'this is a long string')
        self.assertEqual(truncate_string('this is a long string', 20), 'this is a long st...')

        self.assertEqual(truncate_string('this is a long string', 10, '*'), 'this is***')
        self.assertRaises(TypeError, truncate_string, 123, 10)
        self.assertRaises(TypeError, truncate_string, 123, 'this ia a string')
        self.assertRaises(ValueError, truncate_string, 'this is a long string', 5, '__')

        self.assertRaises(ValueError, truncate_string, 'this is a long string', 0)


if __name__ == '__main__':
    unittest.main()