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

from qteasy.finance import CashPlan

from qteasy.config_parser import (
    parse_backtest_start_end_dates,
    parse_backtest_cash_plan,
    parse_trade_cost_params,
    parse_cash_invest_and_delivery_arrays,
    parse_signal_parsing_params,
    parse_trading_moq_params,
    parse_trading_delivery_params,
    parse_optimization_start_end_dates,
    parse_optimization_cash_plan,
)

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
        self.assertEqual(cash_plan.first_day, pd.Timestamp('2020-01-01'))  # next market day
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
        self.assertEqual(cash_plan.first_day, pd.Timestamp('2020-01-01'))
        self.assertEqual(cash_plan.dates, [
            pd.Timestamp('2020-01-01'),
            pd.Timestamp('2020-02-01'),
            pd.Timestamp('2020-03-01')
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

        # test raise when cash dates does not meet invest_start date
        config = {
            'invest_start':        '20200115',
            'invest_cash_dates':   '20200101, 20200201, 20200301',
            'invest_cash_amounts': [10000, 15000, 20000],
            'riskfree_ir':         0.03
        }
        with self.assertRaises(RuntimeError):
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

    def test_trade_cost_params(self):
        """ test the function parse_trade_cost_params"""
        config = {
            'cost_rate_buy':  0.001,
            'cost_rate_sell': 0.002,
            'cost_min_buy':   5.0,
            'cost_min_sell':  5.0,
            'cost_slippage':  0.0,
        }
        cost_params = parse_trade_cost_params(config=config)
        self.assertIsInstance(cost_params, dict)
        self.assertIn('buy_rate', cost_params)
        self.assertIn('sell_rate', cost_params)
        self.assertIn('buy_min', cost_params)
        self.assertIn('sell_min', cost_params)
        self.assertIn('slippage', cost_params)
        self.assertEqual(cost_params['buy_rate'], 0.001)
        self.assertEqual(cost_params['sell_rate'], 0.002)
        self.assertEqual(cost_params['buy_min'], 5.0)
        self.assertEqual(cost_params['sell_min'], 5.0)
        self.assertEqual(cost_params['slippage'], 0.0)

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
            'cost_slippage':  0.0,
        }
        with self.assertRaises(ValueError):
            parse_trade_cost_params(config=config)

        # parse raise with invalid negative values
        config = {
            'cost_rate_buy':  -0.001,
            'cost_rate_sell': 0.002,
            'cost_min_buy':   5.0,
            'cost_min_sell':  5.0,
            'cost_slippage':  0.0,
        }
        with self.assertRaises(ValueError):
            parse_trade_cost_params(config=config)

    def test_parse_investment_and_delivery_arrays(self):
        """ test the function parse_cash_invest_and_delivery_arrays"""
        config = {
            'invest_start':        '20200101',
            'invest_end':          '20200131',
            'invest_cash_dates':   '20200101,20200106,20200112,20200115',
            'invest_cash_amounts': [10000, 15000, 20000, 25000],
            'riskfree_ir':         0.03,
        }
        op_schedule = trade_time_index(
                start='2020-01-01',
                end='2020-01-31',
                freq='d',
        )
        investment_array, inflation_array, day_indicators = parse_cash_invest_and_delivery_arrays(
                config=config,
                op_schedule=op_schedule,
        )
        self.assertIsInstance(investment_array, np.ndarray)
        self.assertIsInstance(inflation_array, np.ndarray)
        self.assertIsInstance(day_indicators, np.ndarray)
        print(f'investment_array: {investment_array}')
        print(f'inflation_array: {inflation_array}')
        print(f'day_indicators: {day_indicators}')
        self.assertEqual(len(investment_array), len(op_schedule))
        self.assertEqual(len(inflation_array), len(op_schedule))
        self.assertEqual(len(day_indicators), len(op_schedule))
        # assert investment amounts on specific dates
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-02')], 10000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-06')], 15000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-13')], 20000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-15')], 25000)
        # assert inflation array values
        target_inflation_array = np.array([1., 1.00008219, 1.00024656, 1.00008216, 1.00008216, 1.00008215,
                                           1.00008214, 1.00024641, 1.00008212, 1.00008211, 1.0000821, 1.0000821,
                                           1.00024627, 1.00008207, 1.00008206, 1.00008206])
        self.assertTrue(np.allclose(inflation_array, target_inflation_array, atol=1e-8))
        target_day_indicators = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertTrue(np.array_equal(day_indicators, target_day_indicators))

        # test op_schedule with hourly frequency
        config = {
            'invest_start':        '20200101',
            'invest_end':          '20200110',
            'invest_cash_dates':   '20200101,20200104,20200107',
            'invest_cash_amounts': [10000, 15000, 20000],
            'riskfree_ir':         0.1,
        }
        op_schedule = trade_time_index(
                start='2020-01-01',
                end='2020-01-10',
                freq='h',
        )
        investment_array, inflation_array, day_indicator = parse_cash_invest_and_delivery_arrays(
                config=config,
                op_schedule=op_schedule,

        )
        print(f'investment_array (hourly): {investment_array}')
        print(f'inflation_array (hourly): {inflation_array}')
        print(f'day_indicator (hourly): {day_indicator}')
        self.assertIsInstance(investment_array, np.ndarray)
        self.assertIsInstance(inflation_array, np.ndarray)
        self.assertIsInstance(day_indicator, np.ndarray)
        self.assertEqual(len(investment_array), len(op_schedule))
        self.assertEqual(len(inflation_array), len(op_schedule))
        self.assertEqual(len(day_indicator), len(op_schedule))
        # assert investment amounts on specific dates
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-02 09:30:00')], 10000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-06 09:30:00')], 15000)
        self.assertEqual(investment_array[op_schedule.get_loc('2020-01-07 09:30:00')], 20000)
        # assert inflation array values on specific dates
        target_inflation_array = np.array([1., 1., 1., 1., 1., 1.00027397,
                                           1., 1., 1., 1., 1.00082169, 1.,
                                           1., 1., 1., 1.00027367, 1., 1.,
                                           1., 1., 1.0002736, 1., 1., 1.,
                                           1., 1.00027352, 1., 1., 1., 1., ])
        self.assertTrue(np.allclose(inflation_array, target_inflation_array, atol=1e-8))
        # assert day_indicator values on specific dates
        target_day_indicators = np.array([1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0,
                                          1, 0, 0, 0, 0])
        self.assertTrue(np.array_equal(day_indicator, target_day_indicators))


class TestParseSignalParsingParams(unittest.TestCase):

    def test_normal_case(self):
        """测试正常情况下参数解析"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        result = parse_signal_parsing_params(config)
        expected = {
            'pt_buy_threshold':  0.5,
            'pt_sell_threshold': 0.3,
            'long_pos_limit':    1.0,
            'short_pos_limit':   -0.5,
            'allow_sell_short':  True
        }
        self.assertEqual(result, expected)

    def test_PT_buy_threshold_type_error(self):
        """测试PT_buy_threshold类型错误的情况"""
        config = {
            'PT_buy_threshold':     "invalid",
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("PT_buy_threshold should be a float number between 0 and 1", str(context.exception))

    def test_PT_buy_threshold_out_of_range_low(self):
        """测试PT_buy_threshold低于有效范围的情况"""
        config = {
            'PT_buy_threshold':     -0.1,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("PT_buy_threshold should be a float number between 0 and 1", str(context.exception))

    def test_PT_buy_threshold_out_of_range_high(self):
        """测试PT_buy_threshold高于有效范围的情况"""
        config = {
            'PT_buy_threshold':     1.0,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("PT_buy_threshold should be a float number between 0 and 1", str(context.exception))

    def test_pt_sell_threshold_type_error(self):
        """测试pt_sell_threshold类型错误的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    "invalid",
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("PT_sell_threshold should be a float number between 0 and 1", str(context.exception))

    def test_pt_sell_threshold_out_of_range_low(self):
        """测试pt_sell_threshold低于有效范围的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    -0.1,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("PT_sell_threshold should be a float number between 0 and 1", str(context.exception))

    def test_pt_sell_threshold_out_of_range_high(self):
        """测试pt_sell_threshold高于有效范围的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    1.0,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("PT_sell_threshold should be a float number between 0 and 1", str(context.exception))

    def test_long_pos_limit_type_error(self):
        """测试long_pos_limit类型错误的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  "invalid",
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("long_position_limit should be a positive float number", str(context.exception))

    def test_long_pos_limit_not_positive(self):
        """测试long_pos_limit不是正数的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  0,
            'short_position_limit': -0.5,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("long_position_limit should be a positive float number", str(context.exception))

    def test_short_pos_limit_type_error(self):
        """测试short_pos_limit类型错误的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': "invalid",
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("short_position_limit should be a negative float number", str(context.exception))

    def test_short_pos_limit_not_negative(self):
        """测试short_pos_limit不是负数的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': 0,
            'allow_sell_short':     True
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("short_position_limit should be a negative float number", str(context.exception))

    def test_allow_sell_short_type_error(self):
        """测试allow_sell_short类型错误的情况"""
        config = {
            'PT_buy_threshold':     0.5,
            'PT_sell_threshold':    0.3,
            'long_position_limit':  1.0,
            'short_position_limit': -0.5,
            'allow_sell_short':     "invalid"
        }
        with self.assertRaises(ValueError) as context:
            parse_signal_parsing_params(config)
        self.assertIn("allow_sell_short should be a boolean value", str(context.exception))


class TestParseTradingMoqParams(unittest.TestCase):
    """测试parse_trading_moq_params函数"""

    def test_normal_case_with_positive_integers(self):
        """TC001: 测试正常情况 - 输入合法的正整数参数"""
        config = {
            'trade_batch_size': 100,
            'sell_batch_size':  50
        }
        expected_result = {
            'moq_buy':  100,
            'moq_sell': 50
        }
        result = parse_trading_moq_params(config)
        self.assertEqual(result, expected_result)

    def test_normal_case_with_positive_floats(self):
        """TC002: 测试正常情况 - 输入合法的正浮点数参数"""
        config = {
            'trade_batch_size': 100.5,
            'sell_batch_size':  50.25
        }
        expected_result = {
            'moq_buy':  100.5,
            'moq_sell': 50.25
        }
        result = parse_trading_moq_params(config)
        self.assertEqual(result, expected_result)

    def test_normal_case_with_mixed_types(self):
        """TC003: 测试正常情况 - 输入混合整数和浮点数参数"""
        config = {
            'trade_batch_size': 100,
            'sell_batch_size':  50.75
        }
        expected_result = {
            'moq_buy':  100,
            'moq_sell': 50.75
        }
        result = parse_trading_moq_params(config)
        self.assertEqual(result, expected_result)

    def test_exception_case_moq_buy_negative(self):
        """TC004: 测试异常情况 - moq_buy为负数"""
        config = {
            'trade_batch_size': -100,
            'sell_batch_size':  50
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_moq_params(config)
        self.assertIn('moq_buy should be a positive float number or zero', str(context.exception))

    def test_exception_case_moq_buy_non_numeric(self):
        """TC006: 测试异常情况 - moq_buy为非数字类型"""
        config = {
            'trade_batch_size': 'invalid',
            'sell_batch_size':  50
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_moq_params(config)
        self.assertIn('moq_buy should be a positive float number or zero', str(context.exception))

    def test_exception_case_moq_sell_negative(self):
        """TC007: 测试异常情况 - moq_sell为负数"""
        config = {
            'trade_batch_size': 100,
            'sell_batch_size':  -50
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_moq_params(config)
        self.assertIn('moq_sell should be a positive float number or zero', str(context.exception))

    def test_exception_case_moq_sell_non_numeric(self):
        """TC009: 测试异常情况 - moq_sell为非数字类型"""
        config = {
            'trade_batch_size': 100,
            'sell_batch_size':  'invalid'
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_moq_params(config)
        self.assertIn('moq_sell should be a positive float number', str(context.exception))


class TestParseTradingDeliveryParams(unittest.TestCase):
    """测试 parse_trading_delivery_params 函数"""

    def test_normal_case(self):
        """测试正常情况：输入有效的非负整数参数"""
        config = {
            'cash_delivery_period':  2,
            'stock_delivery_period': 3
        }
        expected = {
            'cash_delivery_period':  2,
            'stock_delivery_period': 3
        }
        result = parse_trading_delivery_params(config)
        self.assertEqual(result, expected)

    def test_boundary_values(self):
        """测试边界值：参数为0的情况"""
        config = {
            'cash_delivery_period':  0,
            'stock_delivery_period': 0
        }
        expected = {
            'cash_delivery_period':  0,
            'stock_delivery_period': 0
        }
        result = parse_trading_delivery_params(config)
        self.assertEqual(result, expected)

    def test_negative_cash_delivery_period(self):
        """测试 cash_delivery_period 为负数的情况"""
        config = {
            'cash_delivery_period':  -1,
            'stock_delivery_period': 3
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_delivery_params(config)
        self.assertIn('cash_delivery_period should be a non-negative integer', str(context.exception))

    def test_non_integer_cash_delivery_period(self):
        """测试 cash_delivery_period 为非整数类型的情况"""
        config = {
            'cash_delivery_period':  '2',
            'stock_delivery_period': 3
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_delivery_params(config)
        self.assertIn('cash_delivery_period should be a non-negative integer', str(context.exception))

    def test_negative_stock_delivery_period(self):
        """测试 stock_delivery_period 为负数的情况"""
        config = {
            'cash_delivery_period':  2,
            'stock_delivery_period': -1
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_delivery_params(config)
        self.assertIn('stock_delivery_period should be a non-negative integer', str(context.exception))

    def test_non_integer_stock_delivery_period(self):
        """测试 stock_delivery_period 为非整数类型的情况"""
        config = {
            'cash_delivery_period':  2,
            'stock_delivery_period': '3'
        }
        with self.assertRaises(ValueError) as context:
            parse_trading_delivery_params(config)
        self.assertIn('stock_delivery_period should be a non-negative integer', str(context.exception))

    def test_missing_keys(self):
        """测试缺少必要键的情况"""
        config = {
            'cash_delivery_period': 2
            # 缺少 'stock_delivery_period' 键
        }
        with self.assertRaises(KeyError):
            parse_trading_delivery_params(config)


class TestParseOptimizationStartEndDates(unittest.TestCase):

    def test_all_dates_provided_and_valid(self):
        """测试所有日期都提供且合法的情况"""
        config = {
            'opti_start': '2023-01-01',
            'opti_end':   '2023-12-31',
            'test_start': '2024-01-01',
            'test_end':   '2024-12-31'
        }
        result = parse_optimization_start_end_dates(config)
        print(f'got dates from config: {config}\n'
              f' - opti_start: {result[0]}, \n - opti_end: {result[1]}, \n'
              f' - test_start: {result[2]}, \n - test_end: {result[3]}')
        expected = ('2023-01-01', '2023-12-31', '2024-01-01', '2024-12-31')
        self.assertEqual(result, expected)

    def test_missing_opti_end_uses_default(self):
        """测试缺少opti_end时使用默认值（今天减6个月）"""
        config = {
            'opti_start': '2023-01-01',
            'test_start': '2024-07-01',
            'test_end':   '2025-01-01'
        }
        # 注意：由于没有mock pd.Timestamp.today()，这里的结果会基于运行当天的实际日期
        # 因此我们只验证逻辑正确性而不精确匹配日期
        result = parse_optimization_start_end_dates(config)
        opt_start, opt_end, val_start, val_end = result
        print(f'got dates from config: {config}\n'
              f' - opti_start: {opt_start}, \n - opti_end: {opt_end}, \n'
              f' - test_start: {val_start}, \n - test_end: {val_end}')

        # 验证基本结构和相对关系
        self.assertLess(pd.to_datetime(opt_start), pd.to_datetime(opt_end))
        self.assertLess(pd.to_datetime(val_start), pd.to_datetime(val_end))

    def test_missing_opti_start_uses_default(self):
        """测试缺少opti_start时使用默认值（opt_end减1年）"""
        config = {
            'opti_end':   '2024-06-30',
            'test_start': '2024-07-01',
            'test_end':   '2025-01-01'
        }
        result = parse_optimization_start_end_dates(config)
        opt_start, opt_end, val_start, val_end = result
        print(f'got dates from config: {config}\n'
              f' - opti_start: {opt_start}, \n - opti_end: {opt_end}, \n'
              f' - test_start: {val_start}, \n - test_end: {val_end}')

        expected_opt_start = pd.to_datetime('2023-06-30').strftime('%Y-%m-%d')
        self.assertEqual(opt_start, expected_opt_start)
        self.assertEqual(opt_end, '2024-06-30')
        self.assertEqual(val_start, '2024-07-01')
        self.assertEqual(val_end, '2025-01-01')

    def test_missing_test_end_uses_today(self):
        """测试缺少test_end时使用今天作为默认值"""
        config = {
            'opti_start': '2023-01-01',
            'opti_end':   '2023-12-31',
            'test_start': '2024-01-01'
        }
        result = parse_optimization_start_end_dates(config)
        opt_start, opt_end, val_start, val_end = result
        print(f'got dates from config: {config}\n'
              f' - opti_start: {opt_start}, \n - opti_end: {opt_end}, \n'
              f' - test_start: {val_start}, \n - test_end: {val_end}')

        # 验证test_end接近今天
        today = pd.Timestamp.today().strftime('%Y-%m-%d')
        self.assertEqual(val_end, today)

    def test_missing_test_start_uses_default(self):
        """测试缺少test_start时使用默认值（test_end减6个月）"""
        config = {
            'opti_start': '2023-01-01',
            'opti_end':   '2023-12-31',
            'test_end':   '2025-01-01'
        }
        result = parse_optimization_start_end_dates(config)
        opt_start, opt_end, val_start, val_end = result
        print(f'got dates from config: {config}\n'
              f' - opti_start: {opt_start}, \n - opti_end: {opt_end}, \n'
              f' - test_start: {val_start}, \n - test_end: {val_end}')

        expected_val_start = pd.to_datetime('2024-07-01').strftime('%Y-%m-%d')
        self.assertEqual(val_start, expected_val_start)

    def test_all_dates_missing_uses_defaults(self):
        """测试所有日期都缺失时使用默认值"""
        config = {}
        result = parse_optimization_start_end_dates(config)
        opt_start, opt_end, val_start, val_end = result
        print(f'got dates from config: {config}\n'
              f' - opti_start: {opt_start}, \n - opti_end: {opt_end}, \n'
              f' - test_start: {val_start}, \n - test_end: {val_end}')

        # 验证各个日期之间的合理关系
        self.assertLess(pd.to_datetime(opt_start), pd.to_datetime(opt_end))
        self.assertLess(pd.to_datetime(val_start), pd.to_datetime(val_end))

        # 验证时间间隔大致正确
        opt_duration = pd.to_datetime(opt_end) - pd.to_datetime(opt_start)
        val_duration = pd.to_datetime(val_end) - pd.to_datetime(val_start)

        # 优化期应该大约是一年
        self.assertAlmostEqual(opt_duration.days, 365, delta=5)
        # 验证期应该大约是半年
        self.assertAlmostEqual(val_duration.days, 183, delta=5)

    def test_invalid_opt_start_ge_opt_end_raises_error(self):
        """测试opt_start >= opt_end时抛出ValueError"""
        config = {
            'opti_start': '2024-01-01',
            'opti_end':   '2023-12-31'
        }
        with self.assertRaises(ValueError) as context:
            parse_optimization_start_end_dates(config)
        self.assertIn("should be earlier than", str(context.exception))

    def test_invalid_val_start_ge_val_end_raises_error(self):
        """测试val_start >= val_end时抛出ValueError"""
        config = {
            'test_start': '2024-01-01',
            'test_end':   '2023-12-31'
        }
        with self.assertRaises(ValueError) as context:
            parse_optimization_start_end_dates(config)
        self.assertIn("should be earlier than", str(context.exception))

    def test_edge_case_same_opt_start_and_end(self):
        """测试opt_start等于opt_end时抛出ValueError"""
        config = {
            'opti_start': '2023-11-17',
            'opti_end':   '2023-11-17'
        }
        with self.assertRaises(ValueError) as context:
            parse_optimization_start_end_dates(config)
        self.assertIn("should be earlier than", str(context.exception))

    def test_edge_case_same_val_start_and_end(self):
        """测试val_start等于val_end时抛出ValueError"""
        config = {
            'test_start': '2024-11-17',
            'test_end':   '2024-11-17'
        }
        with self.assertRaises(ValueError) as context:
            parse_optimization_start_end_dates(config)
        self.assertIn("should be earlier than", str(context.exception))


class TestParseOptimizationCashPlan(unittest.TestCase):

    def setUp(self):
        # 基础配置，适用于大多数测试场景
        self.base_config = {
            'opti_start':        '2023-06-01',
            'opti_end':          '2023-09-01',
            'test_start':        '2023-09-02',
            'test_end':          '2023-12-01',
            'opti_cash_dates':   None,
            'opti_cash_amounts': [100000],
            'test_cash_dates':   None,
            'test_cash_amounts': [100000],
            'riskfree_ir':       0.03
        }

    def test_tc01_default_single_investment_both_phases(self):
        """
        TC01: 默认单次投资（opt_cash_dates=None）
        测试默认情况下（cash_dates=None），自动计算首个交易日，并生成 CashPlan
        """
        result = parse_optimization_cash_plan(self.base_config)
        print(f'Created cash plan with config: {self.base_config}\n'
              f' - opti_cash_plan: {result[0]}\n'
              f' - test_cash_plan: {result[1]}')

        self.assertIsInstance(result[0], CashPlan)
        self.assertIsInstance(result[1], CashPlan)
        # 验证基础属性存在
        self.assertTrue(hasattr(result[0], 'plan'))
        self.assertTrue(hasattr(result[1], 'plan'))

    def test_tc02_custom_multiple_investments_valid_first_day(self):
        """
        TC02: 自定义多次投资且首日一致
        测试用户自定义多笔投资，且首日正确的情况
        """
        custom_config = self.base_config.copy()
        custom_config.update({
            'opti_cash_dates':   '2023-06-01,2023-07-01',
            'opti_cash_amounts': [50000, 50000],
            'test_cash_dates':   '2023-09-02,2023-10-01',
            'test_cash_amounts': [60000, 40000]
        })

        result = parse_optimization_cash_plan(custom_config)
        print(f'Created cash plan with config: {custom_config}\n'
              f' - opti_cash_plan: {result[0]}\n'
              f' - test_cash_plan: {result[1]}')

        self.assertIsInstance(result[0], CashPlan)
        self.assertEqual(len(result[0].dates), 2)
        self.assertIsInstance(result[1], CashPlan)
        self.assertEqual(len(result[1].dates), 2)

    def test_tc03_custom_multiple_investments_invalid_first_day_opt(self):
        """
        TC03: 自定义多次投资但优化期首日不一致
        测试优化期首日不一致时应抛出 RuntimeError
        """
        invalid_config = self.base_config.copy()
        invalid_config.update({
            'opti_cash_dates':   '2023-06-05,2023-07-01',  # 第一天不是 opti_start
            'opti_cash_amounts': [50000, 50000]
        })

        with self.assertRaises(RuntimeError) as context:
            parse_optimization_cash_plan(invalid_config)

        self.assertIn("first cash investment date", str(context.exception))
        self.assertIn("must be equal to", str(context.exception))

    def test_tc04_custom_multiple_investments_invalid_first_day_test(self):
        """
        TC04: 自定义多次投资但验证期首日不一致
        测试验证期首日不一致时应抛出 RuntimeError
        """
        invalid_config = self.base_config.copy()
        invalid_config.update({
            'test_cash_dates':   '2023-09-05,2023-10-01',  # 第一天不是 test_start
            'test_cash_amounts': [60000, 40000]
        })

        with self.assertRaises(RuntimeError) as context:
            parse_optimization_cash_plan(invalid_config)

        self.assertIn("first cash investment date", str(context.exception))
        self.assertIn("must be equal to", str(context.exception))

    def test_tc05_insufficient_cash_amounts(self):
        """
        TC05: cash_amounts 数量不足或格式错误
        测试当 cash_amounts 为空列表时触发 CashPlan 初始化失败
        """
        invalid_config = self.base_config.copy()
        invalid_config.update({
            'opti_cash_amounts': []  # 空列表导致初始化失败
        })

        with self.assertRaises(Exception):  # CashPlan 初始化会失败
            parse_optimization_cash_plan(invalid_config)

    def test_tc06_both_custom_dates_with_correct_first_days(self):
        """
        TC06: 优化期和验证期都使用自定义日期但首日正确
        测试两个阶段都使用自定义投资日期且首日正确的完整流程
        """
        custom_config = self.base_config.copy()
        custom_config.update({
            'opti_cash_dates':   '2023-06-01,2023-06-15,2023-07-01',
            'opti_cash_amounts': [30000, 30000, 40000],
            'test_cash_dates':   '2023-09-02,2023-09-15,2023-10-01',
            'test_cash_amounts': [40000, 30000, 30000]
        })

        result = parse_optimization_cash_plan(custom_config)
        print(f'Created cash plan with config: {custom_config}\n'
              f' - opti_cash_plan: {result[0]}\n'
              f' - test_cash_plan: {result[1]}')

        # 验证返回类型
        self.assertIsInstance(result[0], CashPlan)
        self.assertIsInstance(result[1], CashPlan)

        # 验证计划长度
        self.assertEqual(len(result[0].dates), 3)
        self.assertEqual(len(result[1].dates), 3)

        # 验证首日正确性
        self.assertEqual(result[0].first_day.strftime('%Y-%m-%d'), '2023-06-01')
        self.assertEqual(result[1].first_day.strftime('%Y-%m-%d'), '2023-09-02')

        # 验证总金额
        self.assertAlmostEqual(sum(result[0].amounts), 100000, places=2)
        self.assertAlmostEqual(sum(result[1].amounts), 100000, places=2)


if __name__ == '__main__':
    unittest.main()