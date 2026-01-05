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
import pandas as pd
import numpy as np
import os
import shutil
import tempfile

from qteasy.qt_operator import Operator
from qteasy.group import Group
from qteasy.strategy import GeneralStg
from qteasy.database import DataSource
from qteasy.datatypes import DataType
from qteasy.trading_util import trade_time_index as tti

from qteasy.history import (
    check_and_prepare_backtest_data,
    check_and_prepare_trade_prices,
    check_and_prepare_benchmark_data,
)


class DailyStrategy(GeneralStg):
    """用于测试的简单策略类"""

    def __init__(self, run_timing='close'):
        super().__init__(
                name='test_strategy',
                description='A simple test strategy',
                data_types=[DataType('close|b', freq='d'),  # 复权收盘价
                            DataType('close-000300.SH', freq='d', asset_type='IDX'),  # 指数收盘价作为参考数据
                            DataType('open', freq='d')],  # 不复权开盘价，测试不同的availability time
                window_length=[5, 7, 8],
                run_timing=run_timing,
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


class TestOperatorPrepareRunningSchedule(unittest.TestCase):

    def setUp(self):
        """设置测试环境"""
        self.operator = Operator()
        self.operator._groups = []

        # 创建测试用的策略组
        self.group1 = Group(name='group1')
        self.group1._run_freq = 'd'
        self.group1._run_timing = 'close'

        self.group2 = Group(name='group2')
        self.group2._run_freq = 'h'  # 修改为小时频率
        self.group2._run_timing = 'open'

        self.group3 = Group(name='group3')
        self.group3._run_freq = 'w'
        self.group3._run_timing = 'close'

    def test_prepare_running_schedule_daily_freq(self):
        """测试日频策略组的时间表生成"""
        # 设置operator的策略组
        self.operator._groups = [self.group1]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        # 打印结果
        print("Daily frequency running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证group_schedules中是否包含group1
        self.assertIn('group1', self.operator.group_schedules)

        # 验证时间表结构
        schedule_df = self.operator.group_schedules['group1']
        self.assertIsInstance(schedule_df, pd.DataFrame)
        self.assertIn('is_running', schedule_df.columns)
        self.assertTrue(np.all(schedule_df['is_running'] == 1))

        # 验证最终的时间表
        timing_table = self.operator.group_timing_table
        self.assertIsInstance(timing_table, pd.DataFrame)
        self.assertIn('group1', timing_table.columns)
        self.assertTrue(np.all(timing_table['group1'] == 1))
        self.assertEqual(timing_table.index.name, None)

        print(f'timing_table.index: {timing_table.index}')

        expected_index = pd.DatetimeIndex(['2023-03-01 15:00:00', '2023-03-02 15:00:00',
                                           '2023-03-03 15:00:00', '2023-03-06 15:00:00',
                                           '2023-03-07 15:00:00', '2023-03-08 15:00:00',
                                           '2023-03-09 15:00:00'])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)

    def test_prepare_running_schedule_hourly_freq(self):
        """测试小时级策略组的时间表生成"""
        # 设置operator的策略组
        self.operator._groups = [self.group2]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        # 打印结果
        print("Hourly frequency running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证group_schedules中是否包含group2
        self.assertIn('group2', self.operator.group_schedules)

        # 验证时间表结构
        schedule_df = self.operator.group_schedules['group2']
        self.assertIsInstance(schedule_df, pd.DataFrame)
        self.assertIn('is_running', schedule_df.columns)
        self.assertTrue(np.all(schedule_df['is_running'] == 1))

        # 验证最终的时间表
        timing_table = self.operator.group_timing_table
        self.assertIn('group2', timing_table.columns)
        self.assertTrue(np.all(timing_table['group2'] == 1))

        print(f'timing_table.index: {timing_table.index}')

        expected_index = pd.DatetimeIndex(['2023-03-01 09:30:00', '2023-03-01 10:30:00',
                                           '2023-03-01 11:30:00', '2023-03-01 14:00:00',
                                           '2023-03-01 15:00:00', '2023-03-02 09:30:00',
                                           '2023-03-02 10:30:00', '2023-03-02 11:30:00',
                                           '2023-03-02 14:00:00', '2023-03-02 15:00:00',
                                           '2023-03-03 09:30:00', '2023-03-03 10:30:00',
                                           '2023-03-03 11:30:00', '2023-03-03 14:00:00',
                                           '2023-03-03 15:00:00', '2023-03-06 09:30:00',
                                           '2023-03-06 10:30:00', '2023-03-06 11:30:00',
                                           '2023-03-06 14:00:00', '2023-03-06 15:00:00',
                                           '2023-03-07 09:30:00', '2023-03-07 10:30:00',
                                           '2023-03-07 11:30:00', '2023-03-07 14:00:00',
                                           '2023-03-07 15:00:00', '2023-03-08 09:30:00',
                                           '2023-03-08 10:30:00', '2023-03-08 11:30:00',
                                           '2023-03-08 14:00:00', '2023-03-08 15:00:00',
                                           '2023-03-09 09:30:00', '2023-03-09 10:30:00',
                                           '2023-03-09 11:30:00', '2023-03-09 14:00:00',
                                           '2023-03-09 15:00:00'])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)

    def test_prepare_running_schedule_weekly_freq(self):
        """测试周频策略组的时间表生成"""
        # 设置operator的策略组
        self.operator._groups = [self.group3]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-18')

        # 打印结果
        print("Weekly frequency running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证group_schedules中是否包含group3
        self.assertIn('group3', self.operator.group_schedules)

        # 验证时间表结构
        schedule_df = self.operator.group_schedules['group3']
        self.assertIsInstance(schedule_df, pd.DataFrame)
        self.assertIn('is_running', schedule_df.columns)
        self.assertTrue(np.all(schedule_df['is_running'] == 1))

        # 验证最终的时间表
        timing_table = self.operator.group_timing_table
        self.assertIn('group3', timing_table.columns)
        self.assertTrue(np.all(timing_table['group3'] == 1))

        print(f'timing_table.index: {timing_table.index}')

        expected_index = pd.DatetimeIndex(['2023-03-03 15:00:00', '2023-03-10 15:00:00'])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)

    def test_prepare_running_schedule_multiple_groups(self):
        """测试多个策略组的时间表生成"""
        # 设置operator的策略组
        self.operator._groups = [self.group1, self.group2, self.group3]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-11')

        # 打印结果
        print("Multiple groups running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证所有策略组都被包含
        self.assertIn('group1', self.operator.group_schedules)
        self.assertIn('group2', self.operator.group_schedules)
        self.assertIn('group3', self.operator.group_schedules)

        # 验证最终的时间表包含所有组
        timing_table = self.operator.group_timing_table
        self.assertIn('group1', timing_table.columns)
        self.assertIn('group2', timing_table.columns)
        self.assertIn('group3', timing_table.columns)

        print(f'timing_table.index: {timing_table.index}')
        print(f'timing_table.values: {timing_table.values}')

        expected_index = pd.DatetimeIndex(['2023-03-01 09:30:00', '2023-03-01 10:30:00',
                                           '2023-03-01 11:30:00', '2023-03-01 14:00:00',
                                           '2023-03-01 15:00:00', '2023-03-02 09:30:00',
                                           '2023-03-02 10:30:00', '2023-03-02 11:30:00',
                                           '2023-03-02 14:00:00', '2023-03-02 15:00:00',
                                           '2023-03-03 09:30:00', '2023-03-03 10:30:00',
                                           '2023-03-03 11:30:00', '2023-03-03 14:00:00',
                                           '2023-03-03 15:00:00', '2023-03-06 09:30:00',
                                           '2023-03-06 10:30:00', '2023-03-06 11:30:00',
                                           '2023-03-06 14:00:00', '2023-03-06 15:00:00',
                                           '2023-03-07 09:30:00', '2023-03-07 10:30:00',
                                           '2023-03-07 11:30:00', '2023-03-07 14:00:00',
                                           '2023-03-07 15:00:00', '2023-03-08 09:30:00',
                                           '2023-03-08 10:30:00', '2023-03-08 11:30:00',
                                           '2023-03-08 14:00:00', '2023-03-08 15:00:00',
                                           '2023-03-09 09:30:00', '2023-03-09 10:30:00',
                                           '2023-03-09 11:30:00', '2023-03-09 14:00:00',
                                           '2023-03-09 15:00:00', '2023-03-10 09:30:00',
                                           '2023-03-10 10:30:00', '2023-03-10 11:30:00',
                                           '2023-03-10 14:00:00', '2023-03-10 15:00:00'])

        expected_values = np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 1],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0],
                                    [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 0]])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)
        self.assertTrue(np.allclose(timing_table.values, expected_values))

    def test_prepare_running_schedule_missing_run_freq(self):
        """测试缺少运行频率参数时的错误处理"""
        # 创建一个缺少run_freq的策略组
        invalid_group = Group(name='invalid_group')
        invalid_group._run_freq = None
        invalid_group._run_timing = 'close'
        self.operator._groups = [invalid_group]

        # 验证抛出ValueError
        with self.assertRaises(ValueError) as context:
            self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        self.assertIn("has no run timing or frequency defined", str(context.exception))

    def test_prepare_running_schedule_custom_timing(self):
        """测试自定义时间偏移"""
        # 创建使用自定义时间的策略组
        custom_group = Group(name='custom_group')
        custom_group._run_freq = 'd'
        custom_group._run_timing = '10:30'
        self.operator._groups = [custom_group]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        # 打印结果
        print("Custom timing running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证group_schedules中是否包含custom_group
        self.assertIn('custom_group', self.operator.group_schedules)

        # 验证时间表结构
        schedule_df = self.operator.group_schedules['custom_group']
        self.assertIsInstance(schedule_df, pd.DataFrame)
        self.assertIn('is_running', schedule_df.columns)
        self.assertTrue(np.all(schedule_df['is_running'] == 1))

        # 验证最终的时间表
        timing_table = self.operator.group_timing_table
        self.assertIn('custom_group', timing_table.columns)
        self.assertTrue(np.all(timing_table['custom_group'] == 1))

        print(f'timing_table.index: {timing_table.index}')

        expected_index = pd.DatetimeIndex(['2023-03-01 10:30:00', '2023-03-02 10:30:00',
                                           '2023-03-03 10:30:00', '2023-03-06 10:30:00',
                                           '2023-03-07 10:30:00', '2023-03-08 10:30:00',
                                           '2023-03-09 10:30:00'])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)

        # 检查生成的group_timing_table的index是否正确
        self.assertIsInstance(timing_table.index, pd.DatetimeIndex)

    def test_prepare_running_schedule_open_timing(self):
        """测试开盘时间设置"""
        # 创建使用开盘时间的策略组
        open_group = Group(name='open_group')
        open_group._run_freq = 'd'
        open_group._run_timing = 'open'
        self.operator._groups = [open_group]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        # 打印结果
        print("Open timing running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证group_schedules中是否包含open_group
        self.assertIn('open_group', self.operator.group_schedules)

        # 验证时间表结构
        schedule_df = self.operator.group_schedules['open_group']
        self.assertIsInstance(schedule_df, pd.DataFrame)
        self.assertIn('is_running', schedule_df.columns)
        self.assertTrue(np.all(schedule_df['is_running'] == 1))

        # 验证最终的时间表
        timing_table = self.operator.group_timing_table
        self.assertIn('open_group', timing_table.columns)
        self.assertTrue(np.all(timing_table['open_group'] == 1))

        print(f'timing_table.index: {timing_table.index}')

        expected_index = pd.DatetimeIndex(['2023-03-01 09:30:00', '2023-03-02 09:30:00',
                                           '2023-03-03 09:30:00', '2023-03-06 09:30:00',
                                           '2023-03-07 09:30:00', '2023-03-08 09:30:00',
                                           '2023-03-09 09:30:00'])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)

        # 检查生成的group_timing_table的index是否正确
        self.assertIsInstance(timing_table.index, pd.DatetimeIndex)

    def test_prepare_running_schedule_close_and_custom_timing(self):
        """测试收盘时间设置"""
        # 创建使用收盘时间的策略组
        # 创建使用自定义时间的策略组
        custom_group = Group(name='custom_group')
        custom_group._run_freq = 'd'
        custom_group._run_timing = '10:30'
        close_group = Group(name='close_group')
        close_group._run_freq = 'd'
        close_group._run_timing = 'close'
        self.operator._groups = [close_group, custom_group]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        # 打印结果
        print("Close timing running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证属性是否被设置
        self.assertIsNotNone(self.operator.group_schedules)
        self.assertIsNotNone(self.operator.group_timing_table)

        # 验证group_schedules中是否包含close_group
        self.assertIn('close_group', self.operator.group_schedules)

        # 验证时间表结构
        schedule_df = self.operator.group_schedules['close_group']
        self.assertIsInstance(schedule_df, pd.DataFrame)
        self.assertIn('is_running', schedule_df.columns)
        self.assertTrue(np.all(schedule_df['is_running'] == 1))

        # 验证最终的时间表
        timing_table = self.operator.group_timing_table
        self.assertIn('close_group', timing_table.columns)
        self.assertIn('custom_group', timing_table.columns)

        print(f'timing_table.index: {timing_table.index}')
        print(f'timing_table.values: {timing_table.values}')

        expected_index = pd.DatetimeIndex(['2023-03-01 10:30:00', '2023-03-01 15:00:00',
                                           '2023-03-02 10:30:00', '2023-03-02 15:00:00',
                                           '2023-03-03 10:30:00', '2023-03-03 15:00:00',
                                           '2023-03-06 10:30:00', '2023-03-06 15:00:00',
                                           '2023-03-07 10:30:00', '2023-03-07 15:00:00',
                                           '2023-03-08 10:30:00', '2023-03-08 15:00:00',
                                           '2023-03-09 10:30:00', '2023-03-09 15:00:00'])

        expected_values = np.array([[0, 1], [1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1],
                                    [1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1], [1, 0]])

        # 检查生成的group_timing_table的index是否正确
        pd.testing.assert_index_equal(timing_table.index, expected_index)
        self.assertTrue(np.allclose(timing_table.values, expected_values))

    def test_prepare_running_schedule_data_types(self):
        """测试生成的数据类型正确性"""
        # 设置operator的策略组
        self.operator._groups = [self.group1]

        # 调用方法
        self.operator.prepare_running_schedule(start_date='2023-03-01', end_date='2023-03-10')

        # 打印结果
        print("Data types running schedule:")
        print("Group schedules:")
        for group_name, schedule in self.operator.group_schedules.items():
            print(f"  {group_name}:")
            print(f"    {schedule}")
        print("Timing table:")
        print(f"  {self.operator.group_timing_table}")

        # 验证数据类型
        timing_table = self.operator.group_timing_table
        self.assertTrue(timing_table.dtypes.apply(lambda x: np.issubdtype(x, np.integer)).all())

        # 验证值的范围
        self.assertTrue((timing_table >= 0).all().all())
        self.assertTrue((timing_table <= 1).all().all())

        # 检查生成的group_timing_table的index是否正确
        self.assertIsInstance(timing_table.index, pd.DatetimeIndex)


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
        print(f'generated daily index ({len(daily_index)}): \n{daily_index[0:30]}')
        print(f'generated hourly index ({len(hourly_index)}): \n{hourly_index[0:30]}')

        # 生成000001以及000002的stock_daily数据
        stock_daily_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        stock_daily_df_000001['ts_code'] = '000001.SZ'
        # 删除2020-06-15的数据，制造一个缺口
        stock_daily_df_000001 = stock_daily_df_000001.drop(pd.to_datetime('2020-06-15'), errors='ignore')

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

        self.datasource.update_table_data('stock_daily',
                                          df=stock_daily_df.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('stock_hourly',
                                          df=stock_hourly_df.reset_index().rename(columns={'index': 'trade_time'}))
        self.datasource.update_table_data('stock_adj_factor',
                                          df=stock_adj_factor.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('index_daily',
                                          df=index_daily_df_000300.reset_index().rename(
                                                  columns={'index': 'trade_date'}))

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
        self.datasource.allow_drop_table = True
        self.datasource.drop_table_data('stock_daily')
        self.datasource.drop_table_data('stock_hourly')
        self.datasource.drop_table_data('index_daily')
        self.datasource.drop_table_data('stock_adj_factors')
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
            start_index = int(np.searchsorted(df.index, self.backtest_start))
            end_index = int(np.searchsorted(df.index, self.backtest_end))
            print(f'for dtype ({dtype}) start_date({self.backtest_start}) is in the df index at '
                  f'pos ({start_index}): {df.index[start_index]}\n'
                  f'end_date({self.backtest_end}) is in the df index at pos ({end_index}): {df.index[end_index - 1]}')

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
            start_index = int(np.searchsorted(df.index, self.backtest_start))
            end_index = int(np.searchsorted(df.index, self.backtest_end))
            print(f'for dtype ({dtype}) start_date({self.backtest_start}) is in the df index at '
                  f'pos ({start_index}): {df.index[start_index]}\n'
                  f'end_date({self.backtest_end}) is in the df index at pos ({end_index}): {df.index[end_index - 1]}')
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

    # noinspection PyTypeChecker
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
                    datasource=self.datasource,
            )
        # 测试backtest_start在可用数据范围但数据窗口不足，不会raise，但是数据会不足
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start=self.out_of_range_start,
                backtest_end=self.backtest_end,
                shares=self.shares_list,
                datasource=self.datasource,
        )
        print(f'got backtest data result with empty shares input:\n{result}')

        # 测试获取的数据中包含缺口数据的情形（缺口数据在2020-06-15），不会raise
        result = check_and_prepare_backtest_data(
                op=self.operator,
                backtest_start='20200613',
                backtest_end='20200623',
                shares=self.shares_list,
                datasource=self.datasource,
        )
        print(f'got backtest data result with missing data range:\n{result}')
        # 确认20200615当天000001.SZ的数据为NaN
        for dtype, df in result.items():
            if dtype == 'close|b_E_d':
                self.assertTrue(np.isnan(df.loc[pd.to_datetime('2020-06-15 15:00:00'), '000001.SZ']))
            elif dtype == 'open_E_d':
                self.assertTrue(np.isnan(df.loc[pd.to_datetime('2020-06-15 09:30:00'), '000001.SZ']))

        max_window_length = self.operator.max_window_length
        for dtype, df in result.items():
            # 检查索引是否为日期类型
            self.assertIsInstance(df.index, pd.DatetimeIndex)
            # 检查日期索引是否覆盖所有数据窗口长度
            start_index = np.searchsorted(df.index, self.out_of_range_start)
            end_index = np.searchsorted(df.index, self.backtest_end)
            print(f'for dtype ({dtype}) start_date({self.out_of_range_start}) is in the df index at '
                  f'pos ({start_index}): {df.index[start_index]}\n'
                  f'end_date({self.backtest_end}) is in the df index at pos ({end_index}): {df.index[end_index]}')
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
     - 当Operator的交易信号清单包含不同频率时，获取相应频率的交易价格数据
        - Operator包含日频和小时频率的策略
        - Operator仅包含日频策略
     - 当Operator的交易时机包含不同时间点时，获取相应时间点的交易价格数据
        - run_timing='open'
        - run_timing='close'
        - run_timing='14:58:00' 任意时间从分钟K线中读取
     - 当adjustment参数不同取值时，获取相应的交易价格数据
        - adjustment='none'
        - adjustment='forward'/'f'
        - adjustment='backward'/'b'
     - 检查返回数据的结构正确性，包括索引类型、列类型、数据类型和日期范围
     - 错误情况处理：
        - 空的股票列表
        - Operator没有创建timing_table

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
        self.daily_strategy = DailyStrategy()
        self.hourly_strategy = HourlyStrategy()
        self.daily_open_stg = DailyStrategy(run_timing='open')
        self.daily_timing_stg = DailyStrategy(run_timing='14:58')
        self.op_complex = Operator(strategies=[self.daily_strategy, self.hourly_strategy])
        self.op_simple = Operator(strategies=[self.daily_strategy])
        self.op_open = Operator(strategies=[self.daily_open_stg, self.hourly_strategy])
        self.op_timing = Operator(strategies=[self.daily_timing_stg, self.hourly_strategy])
        self.op_not_ready = Operator(strategies=[self.daily_timing_stg, self.hourly_strategy])

        # 向data_source中填充测试数据，测试数据随机生成，包括20200101～20201231之间的下面数据：
        # - 股票日线价格：000001.SZ, 000002.SZ两只股票
        # - 股票分钟K线价格：000001.SZ, 000002.SZ两只股票，用于获取交易时机为任意交易时刻的交易价格
        # - 股票复权因子：000001.SZ, 000002.SZ两只股票
        # - 股票小时K线价格：000001.SZ, 000002.SZ两只股票
        # - 指数日线价格：000300.SH指数
        # - 指数分钟K线价格：000300.SH指数， 用于获取交易时机为任意交易时刻的交易价格
        # - 场外基金日线净值：161039.OF，包括净值、累计净值和复权净值
        daily_index = tti(start='20200101', end='20201231', freq='d', trade_days_only=True)
        hourly_index = tti(start='20200101', end='20201231', freq='h')
        min_index = tti(start='20200501', end='20200731', freq='1min', trade_days_only=True)

        # 生成000001以及000002的stock_daily数据
        stock_daily_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        stock_daily_df_000001['ts_code'] = '000001.SZ'
        # 删除2020-06-15的数据，制造一个缺口
        stock_daily_df_000001 = stock_daily_df_000001.drop(pd.to_datetime('2020-06-15'), errors='ignore')

        stock_daily_df_000002 = pd.DataFrame(
                np.random.randint(20, 200, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        stock_daily_df_000002['ts_code'] = '000002.SZ'
        stock_daily_df = pd.concat([stock_daily_df_000001, stock_daily_df_000002])

        # 生成000001/000002的stock_1min数据
        stock_min_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(min_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=min_index,
        )
        stock_min_df_000001['ts_code'] = '000001.SZ'
        # 删除2020-06-15的数据，制造一个缺口
        stock_min_df_000001 = stock_min_df_000001.drop(pd.to_datetime('2020-06-15'), errors='ignore')

        stock_min_df_000002 = pd.DataFrame(
                np.random.randint(20, 200, size=(len(min_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=min_index,
        )
        stock_min_df_000002['ts_code'] = '000002.SZ'
        stock_min_df = pd.concat([stock_min_df_000001, stock_daily_df_000002])

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

        # 添加000300.SH的分钟K线数据到index_1min表中，供指数参考数据使用
        index_min_df_000300 = pd.DataFrame(
                np.random.randint(2000, 4000, size=(len(min_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=min_index,
        )
        index_min_df_000300['ts_code'] = '000300.SH'

        # 添加161039.OF的场外基金净值数据到fund_nav表中
        fund_nav_df_161039 = pd.DataFrame(
                np.random.uniform(1.0, 2.0, size=(len(daily_index), 4)),
                columns=['unit_nav', 'accum_nav', 'adj_nav', 'accum_div'],
                index=daily_index,
        )
        fund_nav_df_161039['ts_code'] = '161039.OF'

        self.datasource.update_table_data('stock_daily',
                                          df=stock_daily_df.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('stock_hourly',
                                          df=stock_hourly_df.reset_index().rename(columns={'index': 'trade_time'}))
        self.datasource.update_table_data('stock_1min',
                                          df=stock_min_df.reset_index().rename(columns={'index': 'trade_time'}))
        self.datasource.update_table_data('stock_adj_factor',
                                          df=stock_adj_factor.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('index_daily',
                                          df=index_daily_df_000300.reset_index().rename(
                                                  columns={'index': 'trade_date'}))
        self.datasource.update_table_data('index_1min',
                                          df=index_min_df_000300.reset_index().rename(columns={'index': 'trade_time'}))
        self.datasource.update_table_data('fund_nav',
                                          df=fund_nav_df_161039.reset_index().rename(columns={'index': 'nav_date'}))

        # 创建测试计划
        self.op_simple.prepare_running_schedule(
                start_date='20200525',
                end_date='20200610',
        )
        self.op_complex.prepare_running_schedule(
                start_date='20200610',
                end_date='20200620',
        )
        self.op_open.prepare_running_schedule(
                start_date='20200710',
                end_date='20200715',
        )
        self.op_timing.prepare_running_schedule(
                start_date='20200625',
                end_date='20200710',
        )

        # 测试资产
        self.shares_list = ['000001.SZ', '000002.SZ']
        self.single_share = '000001.SZ'
        self.share_index_list = ['000001.SZ', '000300.SH']
        self.share_index_fund_list = ['000001.SZ', '000300.SH', '161039.OF']

    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试数据
        self.datasource.allow_drop_table = True
        self.datasource.drop_table_data('stock_daily')
        self.datasource.drop_table_data('stock_hourly')
        self.datasource.drop_table_data('stock_1min')
        self.datasource.drop_table_data('index_daily')
        self.datasource.drop_table_data('index_1min')
        self.datasource.drop_table_data('fund_nav')
        self.datasource.drop_table_data('stock_adj_factors')
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)

    def test_share_list_with_simple_operator(self):
        """测试用例：正常输入参数，简单operator，测试各种share组合"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_simple,
                shares=self.shares_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with simple operator and shares list:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_simple.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.shares_list:
            self.assertIn(share, result.columns)

        # 检查数据全部是数值类型且不含NaN
        for share in self.shares_list:
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_list_with_complex_operator(self):
        """测试用例：正常输入参数，shares为列表，复杂operator"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_complex,
                shares=self.shares_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with simple operator and shares list:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_complex.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.shares_list:
            self.assertIn(share, result.columns)

        # 检查数据全部是数值类型且不含NaN
        for share in self.shares_list:
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_single_share_with_simple_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_simple,
                shares=self.single_share,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with simple operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_simple.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        self.assertIn(self.single_share, result.columns)

        # 检查数据全部是数值类型且不含NaN
        self.assertIn(result[self.single_share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                        np.dtype('int64'), np.dtype('int32')])
        self.assertFalse(result[self.single_share].isnull().all())

    def test_single_share_with_complex_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_complex,
                shares=self.single_share,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with complex operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_complex.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        self.assertIn(self.single_share, result.columns)

        # 检查数据全部是数值类型且不含NaN
        self.assertIn(result[self.single_share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                        np.dtype('int64'), np.dtype('int32')])
        self.assertFalse(result[self.single_share].isnull().all())

    def test_share_index_with_simple_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_simple,
                shares=self.share_index_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with simple operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_simple.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_with_complex_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_complex,
                shares=self.share_index_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with complex operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_complex.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_fund_with_simple_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_simple,
                shares=self.share_index_fund_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with simple operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_simple.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_fund_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_fund_with_complex_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_complex,
                shares=self.share_index_fund_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with complex operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_complex.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_fund_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_fund_with_open_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_open,
                shares=self.share_index_fund_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with open-timing operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_open.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_fund_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_fund_with_timing_operator(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_timing,
                shares=self.share_index_fund_list,
                price_adj='none',
                datasource=self.datasource
        )
        print(f'got trade prices with 14:58-timing operator and single_share:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_timing.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_fund_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_fund_with_timing_operator_forward(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_timing,
                shares=self.share_index_fund_list,
                price_adj='forward',
                datasource=self.datasource
        )
        print(f'got trade prices with 14:58-timing operator with forward adj:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_timing.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_fund_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_share_index_fund_with_timing_operator_backward(self):
        """测试用例：shares参数为单个股票字符串"""
        # 测试简单operator以及简单share_list的情形
        result = check_and_prepare_trade_prices(
                op=self.op_timing,
                shares=self.share_index_fund_list,
                price_adj='back',
                datasource=self.datasource
        )
        print(f'got trade prices with 14:58-timing operator with backward adj:\n{result}')

        # 验证结果是DataFrame，且不为空
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型正确，且索引与operator的group_timing_table的index一致
        self.assertIsInstance(result.index, pd.DatetimeIndex)
        timing_table_index = self.op_timing.group_timing_table.index
        print(f'expected timing table index:\n{timing_table_index}')
        print(f'got trade prices index:\n{result.index}')
        self.assertTrue(result.index.equals(timing_table_index))

        # 检查列包含所有的shares
        for share in self.share_index_fund_list:
            self.assertIn(share, result.columns)

            # 检查数据全部是数值类型且不含NaN
            self.assertIn(result[share].dtype, [np.dtype('float64'), np.dtype('float32'),
                                                np.dtype('int64'), np.dtype('int32')])
            self.assertFalse(result[share].isnull().all())

    def test_with_problematic_parameters(self):
        """测试有问题的输入参数"""
        with self.assertRaises(ValueError):
            check_and_prepare_trade_prices(
                    op=self.op_not_ready,
                    shares=self.shares_list,
                    price_adj='none',
                    datasource=self.datasource
            )
            check_and_prepare_trade_prices(
                    op=self.op_simple,
                    shares=[],
                    price_adj='none',
                    datasource=self.datasource
            )
            check_and_prepare_trade_prices(
                    op=self.op_simple,
                    shares=self.shares_list,
                    price_adj='wrong adj type',
                    datasource=self.datasource
            )

        self.op_not_ready.prepare_running_schedule(
                start_date='20250101',
                end_date='20250131',  # running schedule out of datasource coverage
        )
        with self.assertRaises(RuntimeError):
            check_and_prepare_trade_prices(
                    op=self.op_not_ready,
                    shares=self.shares_list,
                    price_adj='back',
                    datasource=self.datasource
            )


class TestCheckAndPrepareBenchmarkData(unittest.TestCase):
    """check_and_prepare_benchmark_data 函数的单元测试类

    测试通过operator信息获取业绩评价基准数据。业绩评价基准可以是股票、指数或者基金，但是
    只能包含单一资产的价格数据。

    测试用例：
     - 测试数据源中包含一只股票、一个指数、一只场内基金和一只场外基金在2020年全年内的日K线数据以及小时K线数据，以及相关复权因子用于计算复权价格
     - 测试Operator使用Daily/Hourly两个交易策略，生成的交易信号清单同时包含日频和小时频率的时间点，测试混合运行情况下的业绩基准数据获取
     - 测试Operator使用Daily交易策略，生成的交易信号清单包含日频时间点，测试简单情况下的业绩基准数据获取

    测试项目如下：
     - 对于同一个running_timing_table，使用股票作为业绩基准，测试返回数据的正确性
     - 对于同一个running_timing_table，使用指数作为业绩基准，测试返回数据的正确性
     - 对于同一个running_timing_table，使用场内基金作为业绩基准，测试返回数据的正确性
     - 对于同一个running_timing_table，使用场外基金作为业绩基准，测试返回数据的正确性
    测试错误的输入参数处理：
     - 测试空的benchmark代码处理
     - 测试operator没有正确生成running_schedule时的处理
     - 测试无法读到benchmark数据时的处理
    """

    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试数据库
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_db')
        os.makedirs(self.test_db_path)

        # 创建测试数据源
        self.datasource = DataSource(
                source_type='file',
                file_loc=self.test_db_path
        )

        # 向测试数据源中填充数据，测试数据随机生成，包括20200101～20201231之间的下面数据：
        # - 股票日线价格：000001.SZ
        # - 股票复权因子：000001.SZ
        # - 股票小时K线价格：000001.SZ
        # - 指数日线价格：000300.SH指数
        # - 指数小时K线价格：000300.SH
        # - 场内基金日线价格：510050.SH
        # - 场外基金日线净值：161039.OF，包括净值、累计净值和复权净值
        daily_index = tti(start='20200101', end='20201231', freq='d', trade_days_only=True)
        hourly_index = tti(start='20200101', end='20201231', freq='h')

        # 生成000001的stock_daily数据
        stock_daily_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        stock_daily_df_000001['ts_code'] = '000001.SZ'
        # 生成000001的stock_hourly数据
        stock_hourly_df_000001 = pd.DataFrame(
                np.random.randint(10, 100, size=(len(hourly_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=hourly_index,
        )
        stock_hourly_df_000001['ts_code'] = '000001.SZ'
        # 生成000001的adj_factor数据
        stock_adj_factor_000001 = pd.DataFrame(
                np.random.uniform(0.8, 1.2, size=(len(daily_index), 1)),
                columns=['adj_factor'],
                index=daily_index,
        )
        stock_adj_factor_000001['ts_code'] = '000001.SZ'
        # 生成000300.SH数据
        index_daily_df_000300 = pd.DataFrame(
                np.random.randint(2000, 4000, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        index_daily_df_000300['ts_code'] = '000300.SH'
        # 生成000300.SH数据
        index_hourly_df_000300 = pd.DataFrame(
                np.random.randint(2000, 4000, size=(len(hourly_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=hourly_index,
        )
        index_hourly_df_000300['ts_code'] = '000300.SH'
        # 生成510050.SH数据
        fund_daily_df_510050 = pd.DataFrame(
                np.random.randint(2, 10, size=(len(daily_index), 6)),
                columns=['open', 'high', 'low', 'close', 'vol', 'amount'],
                index=daily_index,
        )
        fund_daily_df_510050['ts_code'] = '510050.SH'
        # 生成510050.SH的adj_factor数据
        fund_adj_factor_510050 = pd.DataFrame(
                np.random.uniform(0.8, 1.2, size=(len(daily_index), 1)),
                columns=['adj_factor'],
                index=daily_index,
        )
        fund_adj_factor_510050['ts_code'] = '510050.SH'
        # 生成161039.OF的数据
        fund_nav_df_161039 = pd.DataFrame(
                np.random.uniform(1.0, 2.0, size=(len(daily_index), 4)),
                columns=['unit_nav', 'accum_nav', 'adj_nav', 'accum_div'],
                index=daily_index,
        )
        fund_nav_df_161039['ts_code'] = '161039.OF'

        # 更新数据到数据源
        self.datasource.update_table_data('stock_daily',
                                          df=stock_daily_df_000001.reset_index().rename(
                                                  columns={'index': 'trade_date'}))
        self.datasource.update_table_data('stock_hourly',
                                          df=stock_hourly_df_000001.reset_index().rename(
                                                  columns={'index': 'trade_time'}))
        self.datasource.update_table_data('stock_adj_factor',
                                          df=stock_adj_factor_000001.reset_index().rename(
                                                  columns={'index': 'trade_date'}))
        self.datasource.update_table_data('index_daily',
                                          df=index_daily_df_000300.reset_index().rename(
                                                  columns={'index': 'trade_date'}))
        self.datasource.update_table_data('index_hourly',
                                          df=index_hourly_df_000300.reset_index().rename(
                                                  columns={'index': 'trade_time'}))
        self.datasource.update_table_data('fund_daily',
                                          df=fund_daily_df_510050.reset_index().rename(columns={'index': 'trade_date'}))
        self.datasource.update_table_data('fund_adj_factor',
                                          df=fund_adj_factor_510050.reset_index().rename(
                                                  columns={'index': 'trade_date'}))
        self.datasource.update_table_data('fund_nav',
                                          df=fund_nav_df_161039.reset_index().rename(columns={'index': 'nav_date'}))

        # 创建测试策略和Operator
        self.daily_strategy = DailyStrategy()
        self.hourly_strategy = HourlyStrategy()
        self.operator = Operator(strategies=[self.daily_strategy, self.hourly_strategy])
        self.daily_operator = Operator(strategies=[self.daily_strategy])
        self.wrong_operator = Operator(strategies=[self.daily_strategy])

        self.operator.prepare_running_schedule(
                start_date='20200525',
                end_date='20200610',
        )
        self.daily_operator.prepare_running_schedule(
                start_date='20200525',
                end_date='20200610',
        )

        # 测试股票代码
        self.benchmark_stock = '000001.SZ'
        self.benchmark_index = '000300.SH'
        self.benchmark_fund_in = '510050.SH'
        self.benchmark_fund_out = '161039.OF'

    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试数据
        self.datasource.allow_drop_table = True
        self.datasource.drop_table_data('stock_hourly')
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_daily_benchmark_with_stock(self):
        """测试用例：正常输入参数，返回DataFrame"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.daily_operator,
                benchmark_symbol=self.benchmark_stock,
                datasource=self.datasource
        )
        print(f'got benchmark data for stock {self.benchmark_stock}:\n{result}')

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_stock, result.columns)

        # 检查数据中没有NaN值
        self.assertFalse(result[self.benchmark_stock].isnull().any())

        # 检查index与operator的group_timing_table一致
        print(f'operator timing table index:\n{self.daily_operator.group_timing_table.index}')
        print(f'benchmark data index:\n{result.index}')
        self.assertTrue(result.index.equals(self.daily_operator.group_timing_table.index))

    def test_benchmark_with_stock(self):
        """测试用例：正常输入参数，返回DataFrame"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                benchmark_symbol=self.benchmark_stock,
                datasource=self.datasource
        )
        print(f'got benchmark data for stock {self.benchmark_stock}:\n{result}')

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_stock, result.columns)

        # 检查数据中没有NaN值
        self.assertFalse(result[self.benchmark_stock].isnull().any())

        # 检查index与operator的group_timing_table一致
        self.assertTrue(result.index.equals(self.operator.group_timing_table.index))

    def test_benchmark_with_index(self):
        """测试用例：空的benchmark代码"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                benchmark_symbol=self.benchmark_index,
                datasource=self.datasource
        )
        print(f'got benchmark data for index {self.benchmark_index}:\n{result}')

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_index, result.columns)

        # 检查数据中没有NaN值
        self.assertFalse(result[self.benchmark_index].isnull().any())

        # 检查index与operator的group_timing_table一致
        self.assertTrue(result.index.equals(self.operator.group_timing_table.index))

    def test_benchmark_with_fund(self):
        """测试日期范围处理"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                benchmark_symbol=self.benchmark_fund_in,
                datasource=self.datasource
        )
        print(f'got benchmark data for fund in {self.benchmark_fund_in}:\n{result}')

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_fund_in, result.columns)

        # 检查数据中没有NaN值
        self.assertFalse(result[self.benchmark_fund_in].isnull().any())

        # 检查index与operator的group_timing_table一致
        self.assertTrue(result.index.equals(self.operator.group_timing_table.index))

    def test_benchmark_with_fund_out(self):
        """测试返回数据的结构是否正确"""
        # 执行被测函数
        result = check_and_prepare_benchmark_data(
                op=self.operator,
                benchmark_symbol=self.benchmark_fund_out,
                datasource=self.datasource
        )
        print(f'got benchmark data for fund in {self.benchmark_fund_out}:\n{result}')

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

        # 检查索引类型
        self.assertIsInstance(result.index, pd.DatetimeIndex)

        # 检查列
        self.assertIn(self.benchmark_fund_out, result.columns)

        # 检查数据中没有NaN值
        self.assertFalse(result[self.benchmark_fund_out].isnull().any())

        # 检查index与operator的group_timing_table一致
        self.assertTrue(result.index.equals(self.operator.group_timing_table.index))

    def test_nonexistent_benchmark(self):
        """测试用例：不存在的benchmark代码"""
        # 执行被测函数
        with self.assertRaises(ValueError):
            check_and_prepare_benchmark_data(
                    op=self.operator,
                    benchmark_symbol='NONEXIST',
                    datasource=self.datasource
            )

    def test_missing_data_in_source(self):
        """测试数据源集成"""

        # operator没有运行计划
        with self.assertRaises(ValueError):
            check_and_prepare_benchmark_data(
                    op=self.wrong_operator,
                    benchmark_symbol='000999.SZ',  # 假设该代码在数据源中不存在
                    datasource=self.datasource
            )

        # 超出范围的operater运行计划
        self.wrong_operator.prepare_running_schedule(
                start_date='20220101',
                end_date='20220131',  # 超出数据源覆盖范围
        )
        # 由于symbol超范围或运行计划超范围，导致找不到benchmark数据
        with self.assertRaises(RuntimeError):
            check_and_prepare_benchmark_data(
                    op=self.operator,
                    benchmark_symbol='000999.SZ',  # 假设该代码在数据源中不存在
                    datasource=self.datasource
            )
            check_and_prepare_benchmark_data(
                    op=self.wrong_operator,
                    benchmark_symbol='000001.SZ',
                    datasource=self.datasource
            )


if __name__ == '__main__':
    unittest.main()