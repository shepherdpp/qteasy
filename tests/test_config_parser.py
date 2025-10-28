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
    parse_cash_invest_and_delivery_arrays,
)
from qteasy.datatypes import DataType
from qteasy.trading_util import trade_time_index


class TestConfigParser(unittest.TestCase):
    def test_parse_backtest_cash_plan(self):
        """ tet the function parse_backtest_cash_plan"""
        # test normal parameters without invest_cash_dates
        config = {
            'invest_start':        '20200101',
            'invest_cash_dates':   None,
            'invest_cash_amounts': [10000],
            'riskfree_ir':         0.03
        }
        cash_plan = parse_backtest_cash_plan(config=config)
        self.assertEqual(cash_plan.first_day, pd.Timestamp('2020-01-02'))  # next market day
        self.assertEqual(cash_plan.amounts, [10000])
        self.assertEqual(cash_plan.ir, 0.03)

        # test normal parameters with invest_cash_dates
        config = {
            'invest_start':        '20200101',
            'invest_cash_dates':   '20200101, 20200201, 20200301',
            'invest_cash_amounts': [10000, 15000, 20000],
            'riskfree_ir':         0.03
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
            'invest_start':        '20200101',
            'invest_cash_dates':   '20200101, 20200201, 20200301',
            'invest_cash_amounts': [10000],
            'riskfree_ir':         0.03
        }
        with self.assertRaises(ValueError):
            parse_backtest_cash_plan(config=config)

        # test parameters with wrong type of invest_cash_amounts
        config = {
            'invest_start':        '20200101',
            'invest_cash_dates':   '20200101, 20200201, 20200301',
            'invest_cash_amounts': '10000, 15000, 20000',
            'riskfree_ir':         0.03
        }
        with self.assertRaises(TypeError):
            parse_backtest_cash_plan(config=config)

        # test parameters with invest_cash_dates but missing invest_cash_amounts, ValueError will be raised
        config = {
            'invest_start':        '20200101',
            'invest_cash_dates':   '20200101, 20200201, 20200301',
            'invest_cash_amounts': None,
            'riskfree_ir':         0.03
        }
        with self.assertRaises(TypeError):
            parse_backtest_cash_plan(config=config)

    def test_parse_backtest_start_end_dates(self):
        """ test the function parse_backtest_start_end_dates"""
        # test normal parameters
        config = {
            'invest_start': '20200101',
            'invest_end':   '20200304'
        }
        start, end = parse_backtest_start_end_dates(config=config)
        self.assertEqual(start, '2020-01-01')
        self.assertEqual(end, '2020-03-04')

        # test parameters in different string formats
        config = {
            'invest_start': '20200101 12:00:00',
            'invest_end':   '2020/03/04 01:00:00'
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
            'invest_end':   '2020/01/01'
        }
        with self.assertRaises(ValueError):
            parse_backtest_start_end_dates(config=config)

        # test wrong formats
        config = {
            'invest_start': '2020-13-01',
            'invest_end':   '2020/01/32'
        }
        with self.assertRaises(ValueError):
            parse_backtest_start_end_dates(config=config)

        # test non-string formats
        config = {
            'invest_start': 'wrong_format',
            'invest_end':   '20200304'
        }
        with self.assertRaises(ValueError):
            parse_backtest_start_end_dates(config=config)

    def test_parse_backtest_data_packages(self):
        """ test the function parse_backtest_data_package"""
        # test normal parameters
        config = {
            'invest_start': '20200101',
            'invest_end':   '20200304',
            'asset_pool':   ['000001.SZ', '000002.SZ', '000004.SZ'],
            'data_source':  QT_DATA_SOURCE,
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
            'cost_rate_buy':  0.001,
            'cost_rate_sell': 0.002,
            'cost_min_buy':   5.0,
            'cost_min_sell':  5.0,
            'cost_slipage':   0.0,
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

        # parse raise with missing parameters
        config = {}

        with self.assertRaises(KeyError):
            parse_trade_cost_params(config=config)

        # parse raise with wrong parameter types
        config = {
            'cost_rate_buy':  'wrong_type',
            'cost_rate_sell': 0.002,
            'cost_min_buy':   5.0,
            'cost_min_sell':  5.0,
            'cost_slipage':   0.0,
        }
        with self.assertRaises(ValueError):
            parse_trade_cost_params(config=config)

        # parse raise with invalid negative values
        config = {
            'cost_rate_buy':  -0.001,
            'cost_rate_sell': 0.002,
            'cost_min_buy':   5.0,
            'cost_min_sell':  5.0,
            'cost_slipage':   0.0,
        }
        with self.assertRaises(ValueError):
            parse_trade_cost_params(config=config)

    def test_parse_investment_and_inflation_arrays(self):
        """ test the function parse_cash_invest_and_delivery_arrays"""
        config = {
            'invest_start':        '20200101',
            'invest_end':          '20200131',
            'invest_cash_dates':   '20200102,20200106,20200112,20200115',
            'invest_cash_amounts': [10000, 15000, 20000, 25000],
            'riskfree_ir':         0.03,
        }
        op_schedule = trade_time_index(
                start='2020-01-01',
                end='2020-01-31',
                freq='d',
        )
        investment_array, inflation_array, day_indicators, day_count = parse_cash_invest_and_delivery_arrays(
                config=config,
                op_schedule=op_schedule,
        )
        self.assertIsInstance(investment_array, np.ndarray)
        self.assertIsInstance(inflation_array, np.ndarray)
        self.assertIsInstance(day_indicators, np.ndarray)
        self.assertIsInstance(day_count, np.ndarray)
        print(f'investment_array: {investment_array}')
        print(f'inflation_array: {inflation_array}')
        print(f'day_indicators: {day_indicators}')
        print(f'day_count: {day_count}')
        self.assertEqual(len(investment_array), len(op_schedule))
        self.assertEqual(len(inflation_array), len(op_schedule))
        self.assertEqual(len(day_indicators), len(op_schedule))
        self.assertEqual(len(day_count), len(op_schedule))
        # assert investment amounts on specific dates
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-02')], 10000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-06')], 15000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-13')], 20000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-15')], 25000)
        # assert inflation array values
        target_inflation_array = np.array([1., 1.00008219, 1.00032877, 1.00041096, 1.00049315, 1.00057534
                                              , 1.00065753, 1.00090411, 1.0009863, 1.00106849, 1.00115068, 1.00123288
                                              , 1.00147945, 1.00156164, 1.00164384, 1.00172603])
        self.assertTrue(np.allclose(inflation_array, target_inflation_array, atol=1e-8))
        target_day_indicators = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertTrue(np.array_equal(day_indicators, target_day_indicators))
        target_day_count = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
        self.assertTrue(np.array_equal(day_count, target_day_count))

        # test op_schedule with hourly frequency
        config = {
            'invest_start':        '20200101',
            'invest_end':          '20200110',
            'invest_cash_dates':   '20200102,20200104,20200107',
            'invest_cash_amounts': [10000, 15000, 20000],
            'riskfree_ir':         0.1,
        }
        op_schedule = trade_time_index(
                start='2020-01-01',
                end='2020-01-10',
                freq='h',
        )
        investment_array, inflation_array, day_indicator, day_count = parse_cash_invest_and_delivery_arrays(
                config=config,
                op_schedule=op_schedule,
        )
        print(f'investment_array (hourly): {investment_array}')
        print(f'inflation_array (hourly): {inflation_array}')
        print(f'day_indicator (hourly): {day_indicator}')
        print(f'day_count (hourly): {day_count}')
        self.assertIsInstance(investment_array, np.ndarray)
        self.assertIsInstance(inflation_array, np.ndarray)
        self.assertIsInstance(day_indicator, np.ndarray)
        self.assertIsInstance(day_count, np.ndarray)
        self.assertEqual(len(investment_array), len(op_schedule))
        self.assertEqual(len(inflation_array), len(op_schedule))
        self.assertEqual(len(day_indicator), len(op_schedule))
        self.assertEqual(len(day_count), len(op_schedule))
        # assert investment amounts on specific dates
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-02 09:30:00')], 10000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-06 09:30:00')], 15000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-07 09:30:00')], 20000)
        # assert inflation array values on specific dates
        target_inflation_array = np.array([1., 1., 1., 1., 1., 1.00027397
                                              , 1.00027397, 1.00027397, 1.00027397, 1.00027397, 1.00109589, 1.00109589
                                              , 1.00109589, 1.00109589, 1.00109589, 1.00136986, 1.00136986, 1.00136986
                                              , 1.00136986, 1.00136986, 1.00164384, 1.00164384, 1.00164384, 1.00164384
                                              , 1.00164384, 1.00191781, 1.00191781, 1.00191781, 1.00191781, 1.00191781])
        self.assertTrue(np.allclose(inflation_array, target_inflation_array, atol=1e-8))
        # assert day_indicator values on specific dates
        target_day_indicators = np.array([1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0])
        self.assertTrue(np.array_equal(day_indicator, target_day_indicators))
        # assert day_count values on specific dates
        target_day_count = np.array([1, 1, 1, 1, 1,
                                     2, 2, 2, 2, 2,
                                     3, 3, 3, 3, 3,
                                     4, 4, 4, 4, 4,
                                     5, 5, 5, 5, 5,
                                     6, 6, 6, 6, 6])
        self.assertTrue(np.array_equal(day_count, target_day_count))


if __name__ == '__main__':
    unittest.main()