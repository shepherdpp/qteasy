# coding=utf-8
# ======================================
# File:     test_qt_run.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-11-16
# Desc:
#   Unittest for functions supporting qt
# run processes.
# ======================================

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import os
import shutil
import tempfile
from typing import Union

from qteasy.qt_operator import Operator
from qteasy.strategy import GeneralStg
from qteasy.database import DataSource
from qteasy.datatypes import DataType
from qteasy.trading_util import trade_time_index as tti

from qteasy.core import (
    check_and_prepare_backtest_data,
    check_and_prepare_trade_prices,
    check_and_prepare_benchmark_data,
)


class DailyStrategy(GeneralStg):
    """用于测试的简单策略类"""

    def __init__(self):
        super().__init__(
                name='test_strategy',
                description='A simple test strategy',
                data_types=[DataType('close|b', freq='d'),  # 复权收盘价
                            DataType('close-000300.SH', freq='d', asset_type='IDX'),  # 指数收盘价作为参考数据
                            DataType('open', freq='d')],  # 不复权开盘价，测试不同的availability time
                window_length=[5, 7, 8],
                run_timing='close',
                run_freq='d',
        )


class HourlyStrategy(GeneralStg):
    """用于测试的虚拟策略类"""

    def __init__(self):
        super().__init__(
                name='dummy_strategy',
                description='A dummy strategy for testing',
                data_types=[DataType('close', freq='d', asset_type='E'),  # 不复权收盘价，频率与运行频率不同
                            DataType('high|f', freq='h', asset_type='E'),  # 前复权最高价，频率相同但需复权
                            DataType('low', freq='h', asset_type='E')],  # 不复权最低价
                window_length=6,
                run_freq='h',
        )


class TestCheckAndPrepareBacktestData(unittest.TestCase):
    """check_and_prepare_backtest_data 函数的单元测试类，测试从DataSource获取
    回测数据包（即包含Operator所有数据类型所需数据的字典）

    测试用例：
     - 测试数据源中包含两只股票在2020年全年内的日K线和小时K线数据，以及复权因子用于计算复权价格，其中第一个股票日K存在一个空缺'2020
     - 测试Operator使用Daily/Hourly两个交易策略，需要五种交易数据，包含前复权、后复权和不复权、日频和小时频
    测试项目如下：
     - 给出正常参数（两只股票），回测期间在范围内的输出，检查数据结构正确性以及日期覆盖正确性
     - 给出单只股票和空股票情形确认输出正确
     - 检查错误情况：数据范围超限/输入格式错误/股票代码超范围的情况

    """

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
                file_loc=self.test_db_path
        )

        # 创建测试策略和Operator
        self.daily_strategy = DailyStrategy()
        self.hourly_strategy = HourlyStrategy()
        self.operator = Operator(strategies=[self.daily_strategy,
                                             self.hourly_strategy])

        # 预计结果
        self.expected_dtypes = ['close|b_E_d', 'close_E_d', 'open_E_d', 'high|f_E_h',
                                'low_E_h', 'close-000300.SH_IDX_d']

        # 向data_source中填充测试数据，测试数据随机生成，包括股票日线价格数据（stock_daily）、复权因子数据（stock_adj_factor)
        # 以及股票小时K线价格数据(stock_hourly)(4个价格/天)
        # 数据从20200101到20201231，共365天，包含两只股票：000001.SZ和000002.SZ
        daily_index = tti(start='20200101', end='20201231', freq='d', trade_days_only=True)
        hourly_index = tti(start='20200101', end='20201231', freq='h')
        print(f'generated daily index ({len(daily_index)}): \n{daily_index}')
        print(f'generated hourly index ({len(hourly_index)}): \n{hourly_index}')

        # 生成000001以及000002的stock_daily数据
        stock_daily_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        stock_daily_df_000001['ts_code'] = '000001.SZ'
        stock_daily_df_000002 = pd.DataFrame(
                np.random.randint(20, 200, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        stock_daily_df_000002['ts_code'] = '000002.SZ'
        stock_daily_df = pd.concat([stock_daily_df_000001, stock_daily_df_000002])

        # 生成000001/000002的stock_hourly数据
        stock_hourly_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(hourly_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=hourly_index,
        )
        stock_hourly_df_000001['ts_code'] = '000001.SZ'
        stock_hourly_df_000002 = pd.DataFrame(
                np.random.randint(20, 200, size=(len(hourly_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=hourly_index,
        )
        stock_hourly_df_000002['ts_code'] = '000002.SZ'
        stock_hourly_df = pd.concat([stock_hourly_df_000001, stock_hourly_df_000002])

        # 生成000001/000002的adj_factor数据
        stock_adj_factor_000001 = pd.DataFrame(
                np.random.uniform(0.8, 1.2, size=(len(daily_index), 1)),
                columns=['adj_factor'],
                index=daily_index,
        )
        stock_adj_factor_000001['ts_code'] = '000001.SZ'
        stock_adj_factor_000002 = pd.DataFrame(
                np.random.uniform(0.8, 1.2, size=(len(daily_index), 1)),
                columns=['adj_factor'],
                index=daily_index,
        )
        stock_adj_factor_000002['ts_code'] = '000002.SZ'
        stock_adj_factor = pd.concat([stock_adj_factor_000001, stock_adj_factor_000002])

        # 添加000300.SH的日线数据到index_daily表中，供指数参考数据使用
        index_daily_df_000300 = pd.DataFrame(
                np.random.randint(2000, 4000, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        index_daily_df_000300['ts_code'] = '000300.SH'

        # 引入一个空缺日期到000001的日线数据中，测试数据完整性处理
        stock_daily_df = stock_daily_df.drop(stock_daily_df[(stock_daily_df['ts_code'] == '000001.SZ') &
                                                       (stock_daily_df.index == pd.to_datetime('2020-06-15'))].index)

        self.datasource.update_table_data('stock_daily',
                                          df=stock_daily_df.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('stock_hourly',
                                          df=stock_hourly_df.reset_index().rename(columns={'index': 'trade_time'}))
        self.datasource.update_table_data('stock_adj_factor',
                                          df=stock_adj_factor.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('index_daily',
                                          df=index_daily_df_000300.reset_index().rename(columns={'index': 'trade_date'}))

        # 测试日期
        self.backtest_start = '20200201'
        self.backtest_end = '20200301'
        self.shares_list = ['000001.SZ', '000002.SZ']
        self.single_share = '000001.SZ'
        self.out_of_range_start = '20200101'
        self.out_of_range_end = '20251231'
        self.wrong_shares = ['wrong', 'symbol']

    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试数据源
        self.datasource.allow_drop_table=True
        self.datasource.drop_table_data('stock_daily')
        self.datasource.drop_table_data('stock_hourly')
        self.datasource.drop_table_data('stock_adj_factors')

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
        print(f'got backtest data result with normal input:\n{result}')

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(dtype in self.expected_dtypes for dtype in result.keys()))
        self.assertTrue(all(dtype in result.keys() for dtype in self.expected_dtypes))

        max_window_length = self.operator.max_window_length

        for dtype, df in result.items():
            # 检查索引是否为日期类型
            self.assertIsInstance(df.index, pd.DatetimeIndex)
            # 检查日期索引是否覆盖所有数据窗口长度
            start_index = np.searchsorted(df.index, self.backtest_start)
            end_index = np.searchsorted(df.index, self.backtest_end)
            print(f'for dtype ({dtype}) start_date({self.backtest_start}) is in the df index at '
                  f'pos ({start_index}): {df.index[start_index]}\n'
                  f'end_date({self.backtest_end}) is in the df index at pos ({end_index}): {df.index[end_index-1]}')
            self.assertGreater(start_index, max_window_length)
            self.assertLessEqual(end_index, len(df.index))

            # 当数据类型的name属性为open时，数据所有index的时间部分都是09:30:00
            if dtype == 'open_E_d':
                for dt in df.index:
                    self.assertEqual(dt.hour, 9)
                    self.assertEqual(dt.minute, 30)
                    self.assertEqual(dt.second, 0)

            # 当数据类型的name属性为open时，数据所有index的时间部分都是09:30:00
            if dtype in ['close_E_d', 'close|b_E_d', 'close-000300.SH_IDX_d']:
                for dt in df.index:
                    self.assertEqual(dt.hour, 15)
                    self.assertEqual(dt.minute, 0)
                    self.assertEqual(dt.second, 0)

            # 检查DataFrame包含必要的列
            for share in self.shares_list:
                if dtype == 'close-000300.SH_IDX_d':
                    self.assertIsInstance(df, pd.Series)
                    self.assertFalse(df.empty)
                    self.assertEqual(df.name, 'close-000300.SH_IDX_d')
                else:
                    self.assertIn(share, df)
                    self.assertIsInstance(df, pd.DataFrame)
                    self.assertFalse(df.empty)

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
        print(f'got backtest data result with normal input:\n{result}')

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(dtype in self.expected_dtypes for dtype in result.keys()))
        self.assertTrue(all(dtype in result.keys() for dtype in self.expected_dtypes))

        max_window_length = self.operator.max_window_length

        for dtype, df in result.items():
            # 检查索引是否为日期类型
            self.assertIsInstance(df.index, pd.DatetimeIndex)
            # 检查日期索引是否覆盖所有数据窗口长度
            start_index = np.searchsorted(df.index, self.backtest_start)
            end_index = np.searchsorted(df.index, self.backtest_end)
            print(f'for dtype ({dtype}) start_date({self.backtest_start}) is in the df index at '
                  f'pos ({start_index}): {df.index[start_index]}\n'
                  f'end_date({self.backtest_end}) is in the df index at pos ({end_index}): {df.index[end_index-1]}')
            self.assertGreater(start_index, max_window_length)
            self.assertLessEqual(end_index, len(df.index))

            self.assertFalse(df.empty)
            if dtype == 'close-000300.SH_IDX_d':
                self.assertIsInstance(df, pd.Series)
                self.assertEqual(df.name, 'close-000300.SH_IDX_d')
            else:
                self.assertIsInstance(df, pd.DataFrame)
                # 检查DataFrame包含必要的列
                expected_columns = self.shares_list
                for col in expected_columns:
                    if col == self.single_share:
                        self.assertIn(col, df.columns)
                    else:
                        self.assertNotIn(col, df.columns)

    def test_problematic_parameters(self):
        """测试用例：空的shares列表，此时应该抱错"""
        # 测试raise ValueError: shares can not be an empty list
        with self.assertRaises(ValueError):
            # let shares = []
            check_and_prepare_backtest_data(
                    op=self.operator,
                    backtest_start=self.backtest_start,
                    backtest_end=self.backtest_end,
                    shares=[],
                    datasource=self.datasource
            )
            # let shares = ''
            check_and_prepare_backtest_data(
                    op=self.operator,
                    backtest_start=self.backtest_start,
                    backtest_end=self.backtest_end,
                    shares='',
                    datasource=self.datasource
            )
        # 测试backtest_start在可用数据范围但数据窗口不足，不会raise，但是数据会不足
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.out_of_range_start,
                backtest_end=self.backtest_end,
                shares=self.shares_list,
                datasource=self.datasource
        )
        print(f'got backtest data result with empty shares input:\n{result}')
        max_window_length = self.operator.max_window_length
        for dtype, df in result.items():
            # 检查索引是否为日期类型
            self.assertIsInstance(df.index, pd.DatetimeIndex)
            # 检查日期索引是否覆盖所有数据窗口长度
            start_index = np.searchsorted(df.index, self.out_of_range_start)
            end_index = np.searchsorted(df.index, self.backtest_end)
            print(f'for dtype ({dtype}) start_date({self.out_of_range_start}) is in the df index at '
                  f'pos ({start_index}): {df.index[start_index]}\n'
                  f'end_date({self.backtest_end}) is in the df index at pos ({end_index}): {df.index[end_index-1]}')
            self.assertLessEqual(start_index, max_window_length)
            self.assertLessEqual(end_index, len(df.index))

        # 测试完全没有数据可以获取到时，会raise RuntimeError
        with self.assertRaises(RuntimeError):
            check_and_prepare_backtest_data(
                    op=self.operator,
                    backtest_start='20190101',
                    backtest_end='20191231',
                    shares=self.shares_list,
                    datasource=self.datasource
            )

        # 测试输入错误的时间格式或错误的数据源
        with self.assertRaises(ValueError):
            check_and_prepare_backtest_data(
                    op=self.operator,
                    backtest_start='wrong_date',
                    backtest_end=self.backtest_end,
                    shares=self.shares_list,
                    datasource=self.datasource
            )
            check_and_prepare_backtest_data(
                    op=self.operator,
                    backtest_start=self.backtest_start,
                    backtest_end='wrong_date',
                    shares=self.shares_list,
                    datasource=self.datasource
            )
            check_and_prepare_backtest_data(
                    op=self.operator,
                    backtest_start=self.backtest_start,
                    backtest_end=self.backtest_end,
                    shares=self.shares_list,
                    datasource='wrong_datasource',
            )
            check_and_prepare_backtest_data(
                    op='wrong operator',
                    backtest_start=self.backtest_start,
                    backtest_end=self.backtest_end,
                    shares=self.shares_list,
                    datasource=self.datasource
            )


class TestCheckAndPrepareTradePrices(unittest.TestCase):
    """check_and_prepare_trade_prices 函数的单元测试类，测试从DataSource获取
    交易回测计算所需的所有股票的交易价格，即一个DataFrame，行索引包括Operator生成
    的交易信号清单中的所有日期时间，列索引为所有股票代码，数据为对应的交易价格

    测试用例：
     - 测试数据源中包含两只股票在2020年全年内的分钟K线数据和日K线数据，以及复权因子用于计算复权价格
     - 测试Operator使用Daily/Hourly两个交易策略，生成的交易信号清单同时包含日频和小时频率的时间点，测试混合频率的交易价格获取
     - 测试Operator使用Daily交易策略，生成的交易信号清单全部为日频，测试单一频率交易价格的获取
    测试项目如下：
     - 当输入的shares包含不同类型资产时，获取相应的交易价格数据：
        - 当shares为单个股票字符串时
        - 当shares同时包含股票和指数时
        - 当shares包含股票、指数和ETF基金时
        - 当shares包含场外基金时（价格在每日收盘后更新到nav中）
     - 当Operator的交易信号为混合频率

     """

    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试数据库
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_db')
        os.makedirs(self.db_path)

        # 创建测试数据源
        self.datasource = DataSource(
                source_type='file',
                file_loc=self.db_path,
        )

        # 创建测试策略和Operator
        self.test_strategy = TestStrategy()
        self.operator = Operator(strategies=[self.test_strategy])

        # 向data_source中填充测试数据，测试数据随机生成，包括股票日线价格数据（stock_daily）以及复权因子数据（stock_adj_factor)
        # 数据从20200101到20201231，共365天，包含两只股票：000001.SZ和000002.SZ
        stock_daily_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(365, 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=pd.date_range('20200101', periods=365, freq='D'),
        )
        stock_daily_df_000001['ts_code'] = '000001.SZ'
        stock_daily_df_000002 = pd.DataFrame(
                np.random.randint(20, 200, size=(365, 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=pd.date_range('20200101', periods=365, freq='D'),
        )
        stock_daily_df_000002['ts_code'] = '000002.SZ'
        stock_daily_df = pd.concat([stock_daily_df_000001, stock_daily_df_000002])

        stock_adj_factor_000001 = pd.DataFrame(
                np.random.uniform(0.8, 1.2, size=(365, 1)),
                columns=['adj_factor'],
                index=pd.date_range('20200101', periods=365, freq='D'),
        )
        stock_adj_factor_000001['ts_code'] = '000001.SZ'
        stock_adj_factor_000002 = pd.DataFrame(
                np.random.uniform(0.8, 1.2, size=(365, 1)),
                columns=['adj_factor'],
                index=pd.date_range('20200101', periods=365, freq='D'),
        )
        stock_adj_factor_000002['ts_code'] = '000002.SZ'
        stock_adj_factor = pd.concat([stock_adj_factor_000001, stock_adj_factor_000002])

        self.datasource.update_table_data('stock_daily',
                                          df=stock_daily_df.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('stock_adj_factor',
                                          df=stock_adj_factor.reset_index().rename(columns={'index': 'trade_date'}))

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
                shares=self.shares_list,
                price_adj='none',
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