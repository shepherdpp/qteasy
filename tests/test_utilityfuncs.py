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

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, sec_to_duration, str_to_list
from qteasy.utilfuncs import maybe_trade_day, is_market_trade_day, prev_trade_day, next_trade_day
from qteasy.utilfuncs import next_market_trade_day, unify, list_or_slice, labels_to_dict, retry
from qteasy.utilfuncs import weekday_name, nearest_market_trade_day, is_number_like, list_truncate, input_to_list
from qteasy.utilfuncs import match_ts_code, _lev_ratio, _partial_lev_ratio, _wildcard_match, rolling_window
from qteasy.utilfuncs import reindent, adjust_string_length, is_float_like, is_integer_like
from qteasy.utilfuncs import is_cn_stock_symbol_like, is_complete_cn_stock_symbol_like


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
        self.assertEqual(sec_to_duration(t), '3 sec 140.0 ms')
        self.assertEqual(sec_to_duration(t, estimation=True), 'about 3 sec')
        self.assertEqual(sec_to_duration(t, short_form=True), '3"140')
        self.assertEqual(sec_to_duration(t, estimation=True, short_form=True), '~3"')
        t = 300.14
        self.assertEqual(sec_to_duration(t), '5 min 140.0 ms')
        self.assertEqual(sec_to_duration(t, estimation=True), 'about 5 min')
        self.assertEqual(sec_to_duration(t, short_form=True), "5'140")
        self.assertEqual(sec_to_duration(t, estimation=True, short_form=True), "~5'")
        t = 7435.0014
        self.assertEqual(sec_to_duration(t), '2 hours 3 min 55 sec 1.4 ms')
        self.assertEqual(sec_to_duration(t, estimation=True), 'about 2 hours')
        self.assertEqual(sec_to_duration(t, short_form=True), "2H3'55\"001")
        self.assertEqual(sec_to_duration(t, estimation=True, short_form=True), "~2H")
        t = 86120.0509
        self.assertEqual(sec_to_duration(t), '23 hours 55 min 20 sec 50.9 ms')
        self.assertEqual(sec_to_duration(t, estimation=True), 'about 1 day')
        self.assertEqual(sec_to_duration(t, short_form=True), "23H55'20\"051")
        self.assertEqual(sec_to_duration(t, estimation=True, short_form=True), "~1D")
        t = 88425.0509
        self.assertEqual(sec_to_duration(t), '1 day 33 min 45 sec 50.9 ms')
        self.assertEqual(sec_to_duration(t, estimation=True), 'about 1 day 1 hour')
        self.assertEqual(sec_to_duration(t, short_form=True), "1D33'45\"051")
        self.assertEqual(sec_to_duration(t, estimation=True, short_form=True), "~1D1H")
        t = 288425.0509
        self.assertEqual(sec_to_duration(t), '3 days 8 hours 7 min 5 sec 50.9 ms')
        self.assertEqual(sec_to_duration(t, estimation=True), 'about 3 days 8 hours')
        self.assertEqual(sec_to_duration(t, short_form=True), "3D8H7'5\"051")
        self.assertEqual(sec_to_duration(t, estimation=True, short_form=True), "~3D8H")

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
        self.assertEqual(regulate_date_format('2019/11/06'), '2019-11-06')
        self.assertEqual(regulate_date_format('2019-11-06'), '2019-11-06')
        self.assertEqual(regulate_date_format('20191106'), '2019-11-06')
        self.assertEqual(regulate_date_format('191106'), '2006-11-19')
        self.assertEqual(regulate_date_format('830522'), '1983-05-22')
        self.assertEqual(regulate_date_format(datetime.datetime(2010, 3, 15)), '2010-03-15')
        self.assertEqual(regulate_date_format(datetime.datetime(2010, 3, 15, 12, 12, 23)), '2010-03-15 12:12:23')
        self.assertEqual(regulate_date_format('20191106 16:20:48'), '2019-11-06 16:20:48')
        self.assertEqual(regulate_date_format(pd.Timestamp('2010.03.15')), '2010-03-15')
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
        # self.assertFalse(is_market_trade_day(date_christmas, exchange='XHKG'))
        # test trade dates in some strange text formats:
        self.assertTrue(is_market_trade_day('2021-04-01'))
        self.assertTrue(is_market_trade_day(pd.to_datetime('2021-04-01 00:00:00')))
        self.assertTrue(is_market_trade_day('2021-04-01 00:00:00'))
        self.assertTrue(is_market_trade_day(datetime.date(2021, 4, 1)))
        self.assertTrue(is_market_trade_day(datetime.date(2021, 4, 1), 'SSE'))

        # raises when date out of range
        self.assertRaises(KeyError, is_market_trade_day, date_too_early)
        self.assertRaises(KeyError, is_market_trade_day, date_too_late)

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
        ls = list_truncate(the_list, 2, as_list=True)
        self.assertEqual(ls[0], [1, 2])
        self.assertEqual(ls[1], [3, 4])
        self.assertEqual(ls[2], [5])

        self.assertRaises(ValueError, list_truncate, the_list, 0)
        self.assertRaises(TypeError, list_truncate, 12, 0)
        self.assertRaises(TypeError, list_truncate, 0, the_list)

        ls = list_truncate(the_list, 7, as_list=True)
        self.assertEqual(ls[0], [1, 2, 3, 4, 5])

        g = list_truncate(the_list, 2, as_list=False)
        self.assertEqual(next(g), [1, 2])
        self.assertEqual(next(g), [3, 4])
        self.assertEqual(next(g), [5])
        self.assertRaises(StopIteration, next, g)

        g = list_truncate(the_list, 7, as_list=False)
        self.assertEqual(next(g), [1, 2, 3, 4, 5])

        # test if the function works with generator, NotImplemented
        # lst = (i for i in range(10))
        #
        # g = list_truncate(lst, 3, as_list=False)
        # self.assertEqual(next(g), [0, 1, 2])
        # self.assertEqual(next(g), [3, 4, 5])
        # self.assertEqual(next(g), [6, 7, 8])
        # self.assertEqual(next(g), [9])

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
        date_too_late = '20990105'
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
        # self.assertEqual(pd.to_datetime(nearest_market_trade_day(date_christmas, 'XHKG')),
        #                  pd.to_datetime(prev_christmas_xhkg))

    def test_next_market_trade_day(self):
        """ test the function next_market_trade_day()
        """
        date_trade = '20210401'
        next_date = '20210402'
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
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_trade, nearest_only=False)),
                         pd.to_datetime(next_date))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_holiday)),
                         pd.to_datetime(next_holiday))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_weekend)),
                         pd.to_datetime(next_weekend))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_seems_trade_day)),
                         pd.to_datetime(next_seems_trade_day))
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_too_early)),
                         None)
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_too_late)),
                         pd.to_datetime(date_too_late))  # data too late is not any more a problem
        self.assertEqual(pd.to_datetime(next_market_trade_day(date_christmas, 'SSE')),
                         pd.to_datetime(date_christmas))
        # self.assertEqual(pd.to_datetime(next_market_trade_day(date_christmas, 'XHKG')),
        #                  pd.to_datetime(next_christmas_xhkg))

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

    def test_is_integer_like(self):
        """test the function: is_integer_like()"""
        self.assertTrue(is_integer_like(123))
        self.assertTrue(is_integer_like('123'))
        self.assertTrue(is_integer_like('-123'))
        self.assertTrue(is_integer_like('0'))
        self.assertTrue(is_integer_like('-0'))

        self.assertFalse(is_integer_like('0000'))
        self.assertFalse(is_integer_like(123.4))
        self.assertFalse(is_integer_like('123.4'))
        self.assertFalse(is_integer_like('-123.4'))
        self.assertFalse(is_integer_like('0.0'))
        self.assertFalse(is_integer_like('-0.0'))
        self.assertFalse(is_integer_like('0000.0'))
        self.assertFalse(is_integer_like('000.0'))
        self.assertFalse(is_integer_like('abc'))
        self.assertFalse(is_integer_like('0.32a'))
        self.assertFalse(is_integer_like('0-2'))

    def test_is_float_like(self):
        """test the function: is_float_like()"""
        self.assertTrue(is_float_like(123))
        self.assertTrue(is_float_like('123'))
        self.assertTrue(is_float_like('-123'))
        self.assertTrue(is_float_like('0'))
        self.assertTrue(is_float_like('-0'))
        self.assertTrue(is_float_like(123.4))
        self.assertTrue(is_float_like('123.4'))
        self.assertTrue(is_float_like('-123.4'))
        self.assertTrue(is_float_like('0.0'))
        self.assertTrue(is_float_like('-0.0'))

        self.assertFalse(is_float_like('0000.0'))
        self.assertFalse(is_float_like('000.0'))
        self.assertFalse(is_float_like('0000'))
        self.assertFalse(is_float_like('000'))
        self.assertFalse(is_float_like('abc'))
        self.assertFalse(is_float_like('0.32a'))
        self.assertFalse(is_float_like('0-2'))

    def test_is_stock_symbol_like(self):
        """ test functions is_cn_stock_symbol_like() and is_complete_cn_stock_symbol_like() """
        self.assertTrue(is_cn_stock_symbol_like('000001'))
        self.assertTrue(is_cn_stock_symbol_like('100001'))
        self.assertFalse(is_cn_stock_symbol_like('0000001'))
        self.assertFalse(is_cn_stock_symbol_like('00001'))
        self.assertFalse(is_cn_stock_symbol_like('00001a'))
        self.assertFalse(is_cn_stock_symbol_like('00001A'))
        self.assertFalse(is_cn_stock_symbol_like('00001.'))
        self.assertFalse(is_cn_stock_symbol_like('00001.0'))
        self.assertFalse(is_cn_stock_symbol_like('00001.00'))

        self.assertTrue(is_complete_cn_stock_symbol_like('000001.SZ'))
        self.assertTrue(is_complete_cn_stock_symbol_like('100001.SZ'))
        self.assertTrue(is_complete_cn_stock_symbol_like('000001.SH'))
        self.assertTrue(is_complete_cn_stock_symbol_like('100001.BJ'))
        self.assertFalse(is_complete_cn_stock_symbol_like('0000001.SZ'))
        self.assertFalse(is_complete_cn_stock_symbol_like('00001.SZ'))
        self.assertFalse(is_complete_cn_stock_symbol_like('000011'))
        self.assertFalse(is_complete_cn_stock_symbol_like('00001a.SZ'))
        self.assertFalse(is_complete_cn_stock_symbol_like('00001A.SZ'))
        self.assertFalse(is_complete_cn_stock_symbol_like('00001.ZH'))

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
        arr = np.array([1, 2, 3, 4, 5]).astype('int64')
        window = rolling_window(arr, window=3, axis=0)
        print(f'origin array: \n{arr}\n'
              f'rolling window: \n{window}')
        target = np.array([[1, 2, 3],
                           [2, 3, 4],
                           [3, 4, 5]])
        self.assertTrue(np.allclose(window, target))
        # test 1d array with int32 dtype
        arr = np.array([1, 2, 3, 4, 5]).astype('int32')
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
                            [9, 0, 1, 2]]]).astype('int64')
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
        # test 2d array with int32 dtype
        arr = np.array([[1, 2, 3, 4],
                        [5, 6, 7, 8],
                        [9, 0, 1, 2]]).astype('int32')
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
        self.assertEqual(adjust_string_length('this is a long string', 23), 'this is a long string  ')
        self.assertEqual(adjust_string_length('this is a long string', 22), 'this is a long string ')
        self.assertEqual(adjust_string_length('this is a long string', 21), 'this is a long string')
        self.assertEqual(adjust_string_length('this is a long string', 20), 'this is a lo...tring')
        self.assertEqual(adjust_string_length('this is a long string', 19), 'this is a l...tring')
        self.assertEqual(adjust_string_length('this is a long string', 18), 'this is a ...tring')
        self.assertEqual(adjust_string_length('this is a long string', 17), 'this is a ...ring')
        self.assertEqual(adjust_string_length('this is a long string', 16), 'this is a...ring')
        self.assertEqual(adjust_string_length('this is a long string', 15), 'this is ...ring')
        self.assertEqual(adjust_string_length('this is a long string', 10), 'this ...ng')
        self.assertEqual(adjust_string_length('this is a long string', 7), 'thi...g')
        self.assertEqual(adjust_string_length('this is a long string', 6), 'th...g')
        self.assertEqual(adjust_string_length('this is a long string', 5), 't...g')
        self.assertEqual(adjust_string_length('this is a long string', 4), 't...')
        self.assertEqual(adjust_string_length('this is a long string', 3), 't..')
        self.assertEqual(adjust_string_length('this is a long string', 2), '..')
        self.assertEqual(adjust_string_length('this is a long string', 1), '.')

        self.assertEqual(adjust_string_length('this is a long string', 10, filler='*'), 'this ***ng')
        self.assertEqual(adjust_string_length('short string', 15), 'short string   ')
        self.assertEqual(adjust_string_length('中文字符string', 20, hans_aware=True),
                         '中文字符string      ')
        self.assertEqual(adjust_string_length('中文字符string', 20, hans_aware=False),
                         '中文字符string          ')
        self.assertEqual(adjust_string_length('中文字符string', 20, padder='*', hans_aware=True),
                         '中文字符string******')
        self.assertEqual(adjust_string_length('中国平安', 8, hans_aware=True),
                         '中国平安')
        self.assertEqual(adjust_string_length('中国龙A', 8, hans_aware=True),
                         '中国龙A ')
        self.assertEqual(adjust_string_length('ST中国', 8, hans_aware=True),
                         'ST中国  ')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 20, hans_aware=False),
                         'this is a 含有...tring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 19, hans_aware=False),
                         'this is a 含...tring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 18, hans_aware=False),
                         'this is a ...tring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 17, hans_aware=False),
                         'this is a ...ring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 16, hans_aware=False),
                         'this is a...ring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 15, hans_aware=False),
                         'this is ...ring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 20, hans_aware=True),
                         'this is a 含...tring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 19, hans_aware=True),
                         'this is a 含..tring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 18, hans_aware=True),
                         'this is a ...tring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 17, hans_aware=True),
                         'this is a ...ring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 16, hans_aware=True),
                         'this is a...ring')
        self.assertEqual(adjust_string_length('this is a 含有中文字符的 string', 15, hans_aware=True),
                         'this is ...ring')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 20, hans_aware=False),
                         '含有中文字符的 string      ')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 10, hans_aware=False),
                         '含有中文字...ng')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 9, hans_aware=False),
                         '含有中文...ng')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 8, hans_aware=False),
                         '含有中文...g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 7, hans_aware=False),
                         '含有中...g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 6, hans_aware=False),
                         '含有...g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 5, hans_aware=False),
                         '含...g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 4, hans_aware=False),
                         '含...')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 3, hans_aware=False),
                         '含..')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 2, hans_aware=False),
                         '..')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 1, hans_aware=False),
                         '.')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 20, hans_aware=True),
                         '含有中文字符...tring')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 10, hans_aware=True),
                         '含有中..ng')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 9, hans_aware=True),
                         '含有...ng')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 8, hans_aware=True),
                         '含有...g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 7, hans_aware=True),
                         '含有..g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 6, hans_aware=True),
                         '含...g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 5, hans_aware=True),
                         '含..g')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 4, hans_aware=True),
                         '含..')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 3, hans_aware=True),
                         '含.')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 2, hans_aware=True),
                         '..')
        self.assertEqual(adjust_string_length('含有中文字符的 string', 1, hans_aware=True),
                         '.')
        self.assertEqual(adjust_string_length('中文字符占据2个位置', 14, hans_aware=True),
                         '中文字符..位置')
        self.assertEqual(adjust_string_length('中文字符占据2个位置', 13, hans_aware=True),
                         '中文字符.位置')
        self.assertEqual(
            adjust_string_length('[red]string[/red] [blue]with[/blue] [yellow]format[/yellow] [green]tags[/green]', 13,
                                 format_tags=True), '[red]string[/red] [blue]...[/blue][yellow][/yellow][green]ags['
                                                    '/green]')
        self.assertEqual(adjust_string_length(
            '[red]string[/red] [blue]with[/blue] [yellow]format[/yellow] [green]tags[/green]及[white]中文字符[/white]',
            13, hans_aware=False, format_tags=True),
                '[red]string[/red] [blue]...[/blue][yellow][/yellow][green][/green][white]文字符[/white]')
        self.assertEqual(adjust_string_length(
            '[red]string[/red] [blue]with[/blue] [yellow]format[/yellow] [green]tags[/green]及[white]中文字符[/white]',
            13, hans_aware=True, format_tags=True),
                '[red]string[/red] [blue]..[/blue][yellow][/yellow][green][/green][white]字符[/white]')
        self.assertEqual(adjust_string_length(
            '[red]完全[/red][blue]由[/blue][yellow]中文字符[/yellow][green]组成[/green]的[white]字符串[/white]', 10,
            hans_aware=False, format_tags=True),
                '[red]完全[/red][blue]由[/blue][yellow]中文..[/yellow][green].[/green][white]符串[/white]')
        self.assertEqual(adjust_string_length(
            '[red]完全[/red][blue]由[/blue][yellow]中文字符[/yellow][green]组成[/green]的[white]字符串[/white]', 13,
            hans_aware=True, format_tags=True),
                '[red]完全[/red][blue]由[/blue][yellow]中.[/yellow][green][/green][white]符串[/white]')
        self.assertEqual(adjust_string_length('this is a long string', 7, format_tags=True), 'thi...g')

        self.assertRaises(TypeError, adjust_string_length, 123, 10)
        self.assertRaises(TypeError, adjust_string_length, 123, 'this ia a string')
        self.assertRaises(ValueError, adjust_string_length, 'this is a long string', 5, filler='__')
        self.assertRaises(ValueError, adjust_string_length, 'this is a long string', 0)


if __name__ == '__main__':
    unittest.main()