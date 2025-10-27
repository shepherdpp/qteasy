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
import numpy as np

from qteasy import QT_DATA_SOURCE
from qteasy.config_parser import (
    parse_backtest_start_end_dates,
    parse_backtest_data_package,
    parse_backtest_cash_plan,
    parse_trade_cost_params,
    parse_cash_investment_and_inflation_arrays,
)
from qteasy.datatypes import DataType
from qteasy.trading_util import trade_time_index


class TestConfigParser(unittest.TestCase):
    def test_parse_backtest_cash_plan(self):
        """ tet the function parse_backtest_cash_plan"""
        # test normal parameters without invest_cash_dates
        config = {
            'invest_start': '20200101',
            'invest_cash_dates': None,
            'invest_cash_amounts': [10000],
            'riskfree_ir': 0.03
        }
        cash_plan = parse_backtest_cash_plan(config=config)
        self.assertEqual(cash_plan.first_day, pd.Timestamp('2020-01-02'))  # next market day
        self.assertEqual(cash_plan.amounts, [10000])
        self.assertEqual(cash_plan.ir, 0.03)

        # test normal parameters with invest_cash_dates
        config = {
            'invest_start': '20200101',
            'invest_cash_dates': '20200101, 20200201, 20200301',
            'invest_cash_amounts': [10000, 15000, 20000],
            'riskfree_ir': 0.03
        }
        cash_plan = parse_backtest_cash_plan(config=config)
        self.assertEqual(cash_plan.first_day, pd.Timestamp('2020-01-02'))
        self.assertEqual(cash_plan.dates, [
            pd.Timestamp('2020-01-02'),
            pd.Timestamp('2020-02-03'),
            pd.Timestamp('2020-03-02')
        ])
        self.assertEqual(cash_plan.amounts, [10000, 15000, 20000])
        self.assertEqual(cash_plan.ir, 0.03)

        # test parameters with single invest_cash_amount but multiple invest_cash_dates
        config = {
            'invest_start': '20200101',
            'invest_cash_dates': '20200101, 20200201, 20200301',
            'invest_cash_amounts': [10000],
            'riskfree_ir': 0.03
        }
        with self.assertRaises(ValueError):
            parse_backtest_cash_plan(config=config)

        # test parameters with wrong type of invest_cash_amounts
        config = {
            'invest_start': '20200101',
            'invest_cash_dates': '20200101, 20200201, 20200301',
            'invest_cash_amounts': '10000, 15000, 20000',
            'riskfree_ir': 0.03
        }
        with self.assertRaises(TypeError):
            parse_backtest_cash_plan(config=config)

        # test parameters with invest_cash_dates but missing invest_cash_amounts, ValueError will be raised
        config = {
            'invest_start': '20200101',
            'invest_cash_dates': '20200101, 20200201, 20200301',
            'invest_cash_amounts': None,
            'riskfree_ir': 0.03
        }
        with self.assertRaises(TypeError):
            parse_backtest_cash_plan(config=config)

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
        """ test the function parse_backtest_data_package"""
        # test normal parameters
        config = {
            'invest_start': '20200101',
            'invest_end': '20200304',
            'asset_pool': ['000001.SZ', '000002.SZ', '000004.SZ'],
            'data_source': QT_DATA_SOURCE,
        }
        dtypes = [
            DataType('close', freq='d', asset_type='E'),
            DataType('pe', freq='d', asset_type='E'),
            DataType('close', freq='w', asset_type='E')
        ]
        data_package = parse_backtest_data_package(config=config, dtypes=dtypes)
        print(data_package)
        self.assertIsInstance(data_package, dict)
        self.assertIn('close_E_d', data_package)
        self.assertIn('pe_E_d', data_package)
        self.assertIn('close_E_w', data_package)
        self.assertIsInstance(data_package['close_E_d'], pd.DataFrame)
        self.assertIsInstance(data_package['pe_E_d'], pd.DataFrame)
        self.assertIsInstance(data_package['close_E_w'], pd.DataFrame)

    def test_trade_cost_params(self):
        """ test the function parse_trade_cost_params"""
        config = {
            'buy_cost_rate': 0.001,
            'sell_cost_rate': 0.002,
            'min_cost_per_trade': 5.0
        }
        cost_params = parse_trade_cost_params(config=config)
        self.assertIsInstance(cost_params, dict)
        self.assertIn('buy_rate', cost_params)
        self.assertIn('sell_rate', cost_params)
        self.assertIn('buy_min', cost_params)
        self.assertIn('sell_min', cost_params)
        self.assertIn('slipage', cost_params)
        self.assertEqual(cost_params['buy_rate'], 0.001)
        self.assertEqual(cost_params['sell_rate'], 0.002)
        self.assertEqual(cost_params['buy_min'], 5.0)
        self.assertEqual(cost_params['sell_min'], 5.0)
        self.assertEqual(cost_params['slipage'], 0.0)

    def test_parse_investment_and_inflation_arrays(self):
        """ test the function parse_cash_investment_and_inflation_arrays"""
        config = {
            'invest_start': '20200101',
            'invest_end': '20200131',
            'invest_cash_dates': '20200102,20200106,20200112,20200115',
            'invest_cash_amounts': [10000, 15000, 20000, 25000],
            'riskfree_ir': 0.03,
        }
        op_schedule = trade_time_index(
                start='2020-01-01',
                end='2020-01-31',
                freq='d',
        )
        investment_array, inflation_array = parse_cash_investment_and_inflation_arrays(
                config=config,
                op_schedule=op_schedule,
        )
        self.assertIsInstance(investment_array, np.ndarray)
        self.assertIsInstance(inflation_array, np.ndarray)
        print(f'investment_array: {investment_array}')
        print(f'inflation_array: {inflation_array}')
        self.assertEqual(len(investment_array), len(op_schedule))
        self.assertEqual(len(inflation_array), len(op_schedule))

        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()