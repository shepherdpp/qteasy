# coding=utf-8
# ======================================
# File:     test_qt_run.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-11-16
# Desc:
#   Unittest for functions supporting qt
# run process.
# ======================================

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import os
import shutil
import tempfile
from typing import List, Dict

from qteasy.qt_operator import Operator
from qteasy.strategy import BaseStrategy
from qteasy.database import DataSource
from qteasy.history import HistoryPanel
from qteasy.datatypes import DataType

from qteasy.core import (
    check_and_prepare_backtest_data,
    check_and_prepare_trade_prices,
    check_and_prepare_benchmark_data,
)


class TestStrategy(BaseStrategy):
    """用于测试的简单策略类"""

    def __init__(self):
        super().__init__()
        self.data_types = ['close']
        self.window_length = 10


class TestCheckAndPrepareBacktestData(unittest.TestCase):
    """check_and_prepare_backtest_data 函数的单元测试类（不使用Mock）"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试数据库
        self.test_db_path = './test_data_source'
        if os.path.exists(self.test_db_path):
            shutil.rmtree(self.test_db_path)
        os.makedirs(self.test_db_path)

        # 创建测试数据源
        self.datasource = DataSource(
                source_type='file',
                file_path=self.test_db_path,
                file_type='csv'
        )

        # 创建测试策略和Operator
        self.test_strategy = TestStrategy()
        self.operator = Operator(strategies=[self.test_strategy])

        # 测试日期
        self.backtest_start = '20200101'
        self.backtest_end = '20201231'
        self.shares_list = ['000001.SZ', '000002.SZ']
        self.single_share = '000001.SZ'

        # 创建测试数据
        self._create_test_data()

    def _create_test_data(self):
        """创建测试用的历史数据"""
        # 创建股票基础信息表
        stock_basic_data = pd.DataFrame({
            'ts_code':   ['000001.SZ', '000002.SZ'],
            'symbol':    ['000001', '000002'],
            'name':      ['平安银行', '万科A'],
            'area':      ['深圳', '深圳'],
            'industry':  ['银行', '房地产'],
            'market':    ['主板', '主板'],
            'list_date': ['19910403', '19910129'],
            'exchange':  ['SZSE', 'SZSE']
        })

        # 创建交易日历数据
        dates = pd.date_range('20191001', '20210101', freq='D')
        # 过滤掉周末（简化处理，实际交易日历需要更精确）
        trade_dates = dates[dates.weekday < 5]
        trade_calendar_data = pd.DataFrame({
            'date':    trade_dates.strftime('%Y%m%d'),
            'is_open': 1
        })

        # 创建股票日线数据
        date_range = pd.date_range('20191001', '20201231', freq='D')
        # 过滤掉周末
        trade_days = date_range[date_range.weekday < 5]

        # 为每只股票创建价格数据
        for stock in self.shares_list:
            stock_data = pd.DataFrame({
                'ts_code':    stock,
                'trade_date': trade_days.strftime('%Y%m%d'),
                'open':       np.random.uniform(10, 20, len(trade_days)),
                'high':       np.random.uniform(10, 20, len(trade_days)) + 1,
                'low':        np.random.uniform(10, 20, len(trade_days)) - 1,
                'close':      np.random.uniform(10, 20, len(trade_days)),
                'vol':        np.random.uniform(100000, 1000000, len(trade_days))
            })

            # 保存数据到数据源
            table_name = f'{stock.replace(".", "_")}_daily'
            stock_data.to_csv(f'{self.test_db_path}/{table_name}.csv', index=False)

        # 保存基础数据
        stock_basic_data.to_csv(f'{self.test_db_path}/stock_basic.csv', index=False)
        trade_calendar_data.to_csv(f'{self.test_db_path}/trade_calendar.csv', index=False)

    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试数据源
        if os.path.exists(self.test_db_path):
            shutil.rmtree(self.test_db_path)

    def test_normal_case_with_shares_list(self):
        """测试用例：正常输入参数，shares为列表"""
        # 执行被测函数
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.backtest_start,
                backtest_end=self.backtest_end,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        for share in self.shares_list:
            self.assertIn(share, result)
            self.assertIsInstance(result[share], pd.DataFrame)
            self.assertFalse(result[share].empty)
            # 检查DataFrame包含必要的列
            expected_columns = ['open', 'high', 'low', 'close', 'vol']
            for col in expected_columns:
                self.assertIn(col, result[share].columns)

    def test_single_share_string_input(self):
        """测试用例：shares参数为单个股票字符串"""
        # 执行被测函数
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.backtest_start,
                backtest_end=self.backtest_end,
                shares=self.single_share,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        self.assertIn(self.single_share, result)
        self.assertIsInstance(result[self.single_share], pd.DataFrame)
        self.assertFalse(result[self.single_share].empty)

    def test_empty_shares_list(self):
        """测试用例：空的shares列表"""
        # 执行被测函数
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.backtest_start,
                backtest_end=self.backtest_end,
                shares=[],
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_date_range_calculation(self):
        """测试日期范围计算是否正确（提前60天）"""
        # 执行被测函数
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.backtest_start,
                backtest_end=self.backtest_end,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证结果包含足够早的数据
        for share in self.shares_list:
            if not result[share].empty:
                # 检查数据是否包含回测开始日期之前的数据
                earliest_date = result[share].index.min()
                start_date = pd.to_datetime(self.backtest_start)
                # 应该包含至少60天前的数据
                self.assertLessEqual(earliest_date, start_date - pd.Timedelta(days=30))

    def test_result_data_structure(self):
        """测试返回数据的结构是否正确"""
        # 执行被测函数
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.backtest_start,
                backtest_end=self.backtest_end,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证返回数据结构
        self.assertIsInstance(result, dict)
        for share in self.shares_list:
            self.assertIn(share, result)
            df = result[share]
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)

            # 检查索引是否为日期类型
            self.assertIsInstance(df.index, pd.DatetimeIndex)

            # 检查必要的列是否存在
            required_columns = ['open', 'high', 'low', 'close', 'vol']
            for col in required_columns:
                self.assertIn(col, df.columns)

            # 检查数据类型
            for col in required_columns:
                self.assertIn(df[col].dtype, [np.dtype('float64'), np.dtype('float32')])

    def test_multiple_data_types(self):
        """测试多种数据类型的支持"""

        # 创建一个需要多种数据类型的策略
        class MultiDataTypeStrategy(BaseStrategy):
            def __init__(self):
                super().__init__()
                self.data_types = ['open', 'close', 'high', 'low', 'vol']
                self.window_length = 5

        multi_strategy = MultiDataTypeStrategy()
        multi_operator = Operator(strategies=[multi_strategy])

        # 执行被测函数
        result = check_and_prepare_backtest_data(
                op=multi_operator,
                backtest_start=self.backtest_start,
                backtest_end=self.backtest_end,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, dict)
        for share in self.shares_list:
            self.assertIn(share, result)
            df = result[share]
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)

            # 检查所有需要的列都存在
            required_columns = ['open', 'close', 'high', 'low', 'vol']
            for col in required_columns:
                self.assertIn(col, df.columns)


class TestCheckAndPrepareTradePrices(unittest.TestCase):
    """check_and_prepare_trade_prices 函数的单元测试类（不使用Mock）"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试数据库
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_db')
        os.makedirs(self.db_path)

        # 创建测试数据源
        self.datasource = DataSource(
                source_type='file',
                file_path=self.db_path,
                file_type='csv'
        )

        # 创建测试策略和Operator
        self.test_strategy = SimpleStrategy()
        self.operator = Operator(strategies=[self.test_strategy])

        # 测试日期
        self.start_date = '20200101'
        self.end_date = '20201231'
        self.shares_list = ['000001.SZ', '000002.SZ']
        self.single_share = '000001.SZ'

        # 创建测试数据
        self._create_test_data()

    def _create_test_data(self):
        """创建测试用的历史数据"""
        # 创建交易日历数据
        dates = pd.date_range('20191201', '20210131', freq='D')
        # 过滤掉周末（简化处理）
        trade_dates = dates[dates.weekday < 5]
        trade_calendar_data = pd.DataFrame({
            'date':    trade_dates.strftime('%Y%m%d'),
            'is_open': 1
        })

        # 创建股票基础信息表
        stock_basic_data = pd.DataFrame({
            'ts_code':   ['000001.SZ', '000002.SZ'],
            'symbol':    ['000001', '000002'],
            'name':      ['平安银行', '万科A'],
            'area':      ['深圳', '深圳'],
            'industry':  ['银行', '房地产'],
            'market':    ['主板', '主板'],
            'list_date': ['19910403', '19910129'],
            'exchange':  ['SZSE', 'SZSE']
        })

        # 创建股票日线数据
        date_range = pd.date_range('20191201', '20201231', freq='D')
        # 过滤掉周末
        trade_days = date_range[date_range.weekday < 5]

        # 为每只股票创建价格数据
        for stock in self.shares_list:
            # 生成随机价格数据
            n_days = len(trade_days)
            open_prices = np.random.uniform(10, 20, n_days)
            close_prices = open_prices + np.random.uniform(-0.5, 0.5, n_days)
            high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 1, n_days)
            low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 1, n_days)
            volumes = np.random.uniform(100000, 1000000, n_days)

            stock_data = pd.DataFrame({
                'ts_code':    stock,
                'trade_date': trade_days.strftime('%Y%m%d'),
                'open':       open_prices,
                'high':       high_prices,
                'low':        low_prices,
                'close':      close_prices,
                'vol':        volumes,
                'amount':     open_prices * volumes
            })

            # 保存数据到数据源
            table_name = f'{stock.replace(".", "_")}_daily'
            stock_data.to_csv(os.path.join(self.db_path, f'{table_name}.csv'), index=False)

        # 保存基础数据
        stock_basic_data.to_csv(os.path.join(self.db_path, 'stock_basic.csv'), index=False)
        trade_calendar_data.to_csv(os.path.join(self.db_path, 'trade_calendar.csv'), index=False)

        # 创建复权因子数据
        for stock in self.shares_list:
            adj_data = pd.DataFrame({
                'ts_code':    stock,
                'trade_date': trade_days.strftime('%Y%m%d'),
                'adj_factor': np.ones(len(trade_days))  # 简化处理，复权因子为1
            })
            table_name = f'{stock.replace(".", "_")}_adj_factor'
            adj_data.to_csv(os.path.join(self.db_path, f'{table_name}.csv'), index=False)

    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试数据
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_normal_case_with_shares_list(self):
        """测试用例：正常输入参数，shares为列表"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        for share in self.shares_list:
            self.assertIn(share, result.columns)

        # 检查数据类型
        for share in self.shares_list:
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32')])

        # 检查日期范围
        self.assertGreaterEqual(result.index.min(), pd.to_datetime(self.start_date))
        self.assertLessEqual(result.index.max(), pd.to_datetime(self.end_date))

    def test_single_share_string_input(self):
        """测试用例：shares参数为单个股票字符串"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=self.single_share,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)
        self.assertIn(self.single_share, result.columns)
        self.assertIsInstance(result.index, pd.DatetimeIndex)

    def test_empty_shares_list(self):
        """测试用例：空的shares列表"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=[],
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_date_range_validation(self):
        """测试日期范围处理"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证日期范围
        self.assertFalse(result.empty)
        self.assertGreaterEqual(result.index.min(), pd.to_datetime(self.start_date))
        self.assertLessEqual(result.index.max(), pd.to_datetime(self.end_date))

    def test_result_data_structure(self):
        """测试返回数据的结构是否正确"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证返回数据结构
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        for share in self.shares_list:
            self.assertIn(share, result.columns)

        # 检查数据完整性
        self.assertFalse(result.isnull().all().all())

        # 检查数据类型
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))

    def test_multiple_shares_data_consistency(self):
        """测试多个股票数据的一致性"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证多个股票数据
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result.columns), len(self.shares_list))

        # 检查是否有共同的日期索引
        self.assertFalse(result.empty)

        # 检查所有股票都有数据
        for share in self.shares_list:
            self.assertIn(share, result.columns)
            self.assertFalse(result[share].empty)
            self.assertFalse(result[share].isnull().all())

    def test_operator_frequency_handling(self):
        """测试Operator频率处理"""
        # 创建不同频率的策略
        daily_strategy = SimpleStrategy()
        daily_strategy.run_freq = 'd'

        weekly_strategy = SimpleStrategy()
        weekly_strategy.run_freq = 'w'

        operator_multi_freq = Operator(strategies=[daily_strategy, weekly_strategy])

        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=operator_multi_freq,
                start=self.start_date,
                end=self.end_date,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查列
        for share in self.shares_list:
            self.assertIn(share, result.columns)

    def test_data_source_integration(self):
        """测试数据源集成"""
        # 执行被测函数
        result = check_and_prepare_trade_prices(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                shares=self.shares_list,
                datasource=self.datasource
        )

        # 验证数据源正确集成
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查数据是否来自正确的数据源
        for share in self.shares_list:
            self.assertIn(share, result.columns)
            self.assertFalse(result[share].empty)


class DummyStrategy(BaseStrategy):
    """用于测试的虚拟策略类"""

    def __init__(self):
        super().__init__()
        self.name = 'dummy_strategy'
        self.description = 'A dummy strategy for testing'
        self.data_types = ['close']
        self.window_length = 10
        self.run_freq = 'd'


class TestCheckAndPrepareBenchmarkDataWithoutMock(unittest.TestCase):
    """check_and_prepare_benchmark_data 函数的单元测试类（不使用Mock）"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试数据库
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_db')
        os.makedirs(self.db_path)

        # 创建测试数据源
        self.datasource = DataSource(
                source_type='file',
                file_path=self.db_path,
                file_type='csv'
        )

        # 创建测试策略和Operator
        self.test_strategy = DummyStrategy()
        self.operator = Operator(strategies=[self.test_strategy])

        # 测试日期
        self.start_date = '20200101'
        self.end_date = '20201231'
        self.benchmark_code = '000300.SH'

        # 创建测试数据
        self._create_test_data()

    def _create_test_data(self):
        """创建测试用的历史数据"""
        # 创建交易日历数据
        dates = pd.date_range('20191201', '20210131', freq='D')
        # 过滤掉周末（简化处理）
        trade_dates = dates[dates.weekday < 5]
        trade_calendar_data = pd.DataFrame({
            'date':    trade_dates.strftime('%Y%m%d'),
            'is_open': 1
        })

        # 创建指数基础信息表
        index_basic_data = pd.DataFrame({
            'ts_code':   ['000300.SH'],
            'name':      ['沪深300指数'],
            'fullname':  ['沪深300指数'],
            'publisher': ['中证公司'],
            'category':  ['规模指数'],
            'list_date': ['20050408'],
            'exchange':  [' SSE']
        })

        # 创建指数日线数据
        date_range = pd.date_range('20191201', '20201231', freq='D')
        # 过滤掉周末
        trade_days = date_range[date_range.weekday < 5]

        # 生成指数价格数据
        n_days = len(trade_days)
        base_price = 4000.0
        # 生成随机游走的价格序列
        returns = np.random.normal(0, 0.01, n_days)
        prices = [base_price]
        for r in returns[1:]:
            prices.append(prices[-1] * (1 + r))

        index_data = pd.DataFrame({
            'ts_code':    self.benchmark_code,
            'trade_date': trade_days.strftime('%Y%m%d'),
            'open':       [p * (1 + np.random.uniform(-0.005, 0.005)) for p in prices],
            'high':       [p * (1 + np.random.uniform(0, 0.01)) for p in prices],
            'low':        [p * (1 - np.random.uniform(0, 0.01)) for p in prices],
            'close':      prices,
            'vol':        np.random.uniform(1e9, 2e9, n_days),
            'amount':     [p * v for p, v in zip(prices, np.random.uniform(1e9, 2e9, n_days))]
        })

        # 创建复权因子数据
        adj_data = pd.DataFrame({
            'ts_code':    self.benchmark_code,
            'trade_date': trade_days.strftime('%Y%m%d'),
            'adj_factor': np.ones(len(trade_days))  # 简化处理，复权因子为1
        })

        # 保存数据到数据源
        index_data.to_csv(os.path.join(self.db_path, '000300_SH_daily.csv'), index=False)
        adj_data.to_csv(os.path.join(self.db_path, '000300_SH_adj_factor.csv'), index=False)
        index_basic_data.to_csv(os.path.join(self.db_path, 'index_basic.csv'), index=False)
        trade_calendar_data.to_csv(os.path.join(self.db_path, 'trade_calendar.csv'), index=False)

    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试数据
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_normal_case_returns_dataframe(self):
        """测试用例：正常输入参数，返回DataFrame"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                benchmark=self.benchmark_code,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_code, result.columns)

        # 检查数据类型
        self.assertIn(result[self.benchmark_code].dtype, [np.dtype('float64'), np.dtype('float32')])

        # 检查日期范围
        self.assertGreaterEqual(result.index.min(), pd.to_datetime(self.start_date))
        self.assertLessEqual(result.index.max(), pd.to_datetime(self.end_date))

    def test_empty_benchmark_code(self):
        """测试用例：空的benchmark代码"""
        with self.assertRaises(Exception):  # 空代码应该导致异常
            check_and_prepare_benchmark_data(
                    op=self.operator,
                    start=self.start_date,
                    end=self.end_date,
                    benchmark='',
                    datasource=self.datasource
            )

    def test_invalid_date_format(self):
        """测试用例：无效的日期格式"""
        with self.assertRaises(ValueError):
            check_and_prepare_benchmark_data(
                    op=self.operator,
                    start='invalid_date',
                    end=self.end_date,
                    benchmark=self.benchmark_code,
                    datasource=self.datasource
            )

    def test_date_range_validation(self):
        """测试日期范围处理"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                benchmark=self.benchmark_code,
                datasource=self.datasource
        )

        # 验证日期范围
        self.assertFalse(result.empty)
        self.assertGreaterEqual(result.index.min(), pd.to_datetime(self.start_date))
        self.assertLessEqual(result.index.max(), pd.to_datetime(self.end_date))

    def test_result_data_structure(self):
        """测试返回数据的结构是否正确"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                benchmark=self.benchmark_code,
                datasource=self.datasource
        )

        # 验证返回数据结构
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_code, result.columns)

        # 检查数据完整性
        self.assertFalse(result.isnull().all().all())

        # 检查数据类型
        self.assertTrue(pd.api.types.is_numeric_dtype(result[self.benchmark_code]))

    def test_nonexistent_benchmark(self):
        """测试用例：不存在的benchmark代码"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                benchmark='NONEXIST.SH',
                datasource=self.datasource
        )

        # 对于不存在的代码，应该返回空的DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_operator_frequency_handling(self):
        """测试Operator频率处理"""
        # 创建不同频率的策略
        daily_strategy = DummyStrategy()
        daily_strategy.run_freq = 'd'

        operator_daily = Operator(strategies=[daily_strategy])

        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=operator_daily,
                start=self.start_date,
                end=self.end_date,
                benchmark=self.benchmark_code,
                datasource=self.datasource
        )

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)
        self.assertIn(self.benchmark_code, result.columns)

    def test_data_source_integration(self):
        """测试数据源集成"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                start=self.start_date,
                end=self.end_date,
                benchmark=self.benchmark_code,
                datasource=self.datasource
        )

        # 验证数据源正确集成
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)
        self.assertIn(self.benchmark_code, result.columns)
        # 检查是否有实际数据
        self.assertFalse(result[self.benchmark_code].empty)
        self.assertFalse(result[self.benchmark_code].isnull().all())


if __name__ == '__main__':
    unittest.main()