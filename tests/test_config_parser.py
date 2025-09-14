# coding=utf-8
# ======================================
# File:     test_config_parser.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-09-13
# Desc:
#   Unittest for functions that generate
# specific information from qteasy
# configuration settings.
# ======================================
import unittest
import pandas as pd

from qteasy.config_parser import (
    parse_backtest_start_end_dates,
    parse_backtest_data_package,
    parse_backtest_cash_plan,
)


class TestConfigParser(unittest.TestCase):
    def test_parse_backtest_cash_plan(self):
        raise NotImplementedError

    def test_parse_backtest_start_end_dates(self):
        """ test the function parse_backtest_start_end_dates"""
        # test normal parameters
        config = {
            'invest_start': '20200101',
            'invest_end': '20200304'
        }
        start, end = parse_backtest_start_end_dates(config=config)
        self.assertEqual(start, '2020-01-01')
        self.assertEqual(end, '2020-03-04')

        # test parameters in different string formats
        config = {
            'invest_start': '20200101 12:00:00',
            'invest_end': '2020/03/04 01:00:00'
        }
        start, end = parse_backtest_start_end_dates(config=config)
        self.assertEqual(start, '2020-01-01')
        self.assertEqual(end, '2020-03-04')

        # test parameters with missing end date, today will be returned
        config = {
            'invest_start': '2020/01/01 12:00:00',
        }
        today = pd.Timestamp.today().strftime('%Y-%m-%d')
        start, end = parse_backtest_start_end_dates(config=config)
        self.assertEqual(start, '2020-01-01')
        self.assertEqual(end, today)

        # test parameters with missing start date, one year ago will be returned
        config = {
            'invest_end': '2020/03/04'
        }
        one_year_ago = '2019-03-04'
        start, end = parse_backtest_start_end_dates(config=config)
        self.assertEqual(start, one_year_ago)
        self.assertEqual(end, '2020-03-04')

        # test parameters with missing both start and end date, one year ago from today will be returned
        config = {}
        today = pd.Timestamp.today()
        one_year_ago = (today - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
        start, end = parse_backtest_start_end_dates(config=config)
        self.assertEqual(start, one_year_ago)

        # test parameters with start date later than end date, ValueError will be raised
        config = {
            'invest_start': '2020/03/04',
            'invest_end': '2020/01/01'
        }
        with self.assertRaises(ValueError):
            parse_backtest_start_end_dates(config=config)

        # test wrong formats
        config = {
            'invest_start': '2020-13-01',
            'invest_end': '2020/01/32'
        }
        with self.assertRaises(ValueError):
            parse_backtest_start_end_dates(config=config)

        # test non-string formats
        config = {
            'invest_start': 'wrong_format',
            'invest_end': '20200304'
        }
        with self.assertRaises(ValueError):
            parse_backtest_start_end_dates(config=config)

    def test_parse_backtest_data_packages(self):
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()