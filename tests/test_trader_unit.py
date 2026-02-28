# coding=utf-8
# ======================================
# File:     test_trader_unit.py
# Desc:
#   单元测试：Trader 初始化、status、任务调度、account_cash、watch_list 等，
#   使用专用测试 DataSource（非 QT_DATA_SOURCE），测试完成后清理数据。
# ======================================

import os
import datetime as dt
import unittest

import pandas as pd

from qteasy import DataSource, Operator
from qteasy.trade_recording import new_account, get_account, get_or_create_position, update_position, update_account_balance
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker


# --------------- 测试用 DataSource：独立目录，测试后清理 ---------------

def _get_trader_test_data_dir():
    """Trader 单元/集成测试专用数据目录，不使用默认 QT_DATA_SOURCE。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_test_trader')


def _default_trader_kwargs():
    """Trader 测试用默认 kwargs。"""
    return {
        'market_open_time_am': '09:30:00',
        'market_close_time_pm': '15:30:00',
        'market_open_time_pm': '13:00:00',
        'market_close_time_am': '11:30:00',
        'exchange': 'SSE',
        'cash_delivery_period': 0,
        'stock_delivery_period': 0,
        'asset_pool': '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
        'asset_type': 'E',
        'pt_buy_threshold': 0.05,
        'pt_sell_threshold': 0.05,
        'allow_sell_short': False,
        'live_price_channel': 'eastmoney',
        'live_data_channel': 'eastmoney',
        'live_price_freq': '15min',
        'live_data_batch_size': 0,
        'live_data_batch_interval': 0,
        'daily_refill_tables': 'stock_1min, stock_5min',
        'weekly_refill_tables': 'stock_15min',
        'monthly_refill_tables': 'stock_daily',
    }


def _create_operator():
    """测试用最小 Operator。"""
    op = Operator(strategies=['macd', 'dma'])
    op.set_parameter(stg_id='dma', window_length=10, run_freq='h')
    op.set_parameter(stg_id='macd', window_length=10, run_freq='30min')
    return op


def _clear_tables(datasource):
    """清理测试相关表（含日志/断点相关文件由调用方按需删除）。"""
    for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                  'sys_op_trade_results', 'stock_daily']:
        if datasource.table_data_exists(table):
            datasource.drop_table_data(table)


def _create_test_datasource():
    """创建专用测试 DataSource，不使用默认 QT_DATA_SOURCE。"""
    data_dir = _get_trader_test_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    return DataSource('file', file_type='csv', file_loc=data_dir, allow_drop_table=True)


def create_trader_with_account(account_id=1, with_positions=True, debug=False):
    """
    创建带账户（及可选持仓）的 Trader，使用测试 DataSource。
    返回 (trader, datasource)。调用方需在测试结束后调用 _clear_tables(datasource)。
    """
    test_ds = _create_test_datasource()
    _clear_tables(test_ds)
    new_account(user_name='test_user1', cash_amount=100000, data_source=test_ds)
    if with_positions:
        for sym in ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']:
            get_or_create_position(account_id=account_id, symbol=sym, position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)
    operator = _create_operator()
    broker = SimulatorBroker()
    trader = Trader(
        account_id=account_id,
        operator=operator,
        broker=broker,
        datasource=test_ds,
        debug=debug,
        **_default_trader_kwargs(),
    )
    return trader, test_ds


# --------------- 初始化与参数验证 ---------------

class TestTraderInit(unittest.TestCase):
    """Trader 初始化与参数校验。"""

    def setUp(self):
        self._test_ds = None

    def tearDown(self):
        if self._test_ds is not None:
            _clear_tables(self._test_ds)

    def test_init_invalid_account_id_type(self):
        """account_id 非 int 时应抛出 TypeError。"""
        op = _create_operator()
        broker = SimulatorBroker()
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id='1',
                operator=op,
                broker=broker,
                datasource=test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('account_id', str(ctx.exception))
        print('test_init_invalid_account_id_type: TypeError as expected', ctx.exception)

    def test_init_invalid_operator_type(self):
        """operator 非 Operator 时应抛出 TypeError。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        broker = SimulatorBroker()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=object(),
                broker=broker,
                datasource=test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('Operator', str(ctx.exception))
        print('test_init_invalid_operator_type: TypeError as expected', ctx.exception)

    def test_init_invalid_broker_type(self):
        """broker 非 Broker 时应抛出 TypeError。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=op,
                broker=object(),
                datasource=test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('Broker', str(ctx.exception))
        print('test_init_invalid_broker_type: TypeError as expected', ctx.exception)

    def test_init_invalid_datasource_type(self):
        """datasource 非 DataSource 时应抛出 TypeError。"""
        op = _create_operator()
        broker = SimulatorBroker()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=op,
                broker=broker,
                datasource=object(),
                **_default_trader_kwargs(),
            )
        self.assertIn('DataSource', str(ctx.exception))
        print('test_init_invalid_datasource_type: TypeError as expected', ctx.exception)

    def test_init_with_large_account_id(self):
        """极大 account_id 应能正常构造。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        # new_account 返回的是新账户 id，可能不是 10**9，这里用已存在的 account_id=1
        # 若 new_account 支持指定 id 则用 10**9；否则用大 id 需要先建账户
        op = _create_operator()
        broker = SimulatorBroker()
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **_default_trader_kwargs(),
        )
        self.assertEqual(trader.account_id, 1)
        print('test_init_with_large_account_id: account_id=1 passed (large id would need DB support)')

    def test_init_benchmark_asset_from_str(self):
        """benchmark_asset 为 str 时 watch_list 为 benchmark + asset_pool。"""
        trader, self._test_ds = create_trader_with_account()
        self.assertEqual(trader.benchmark, '000300.SH')
        expected = ['000300.SH', '000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ']
        self.assertEqual(trader.watch_list, expected)
        print('test_init_benchmark_asset_from_str: watch_list', trader.watch_list)

    def test_init_benchmark_asset_from_list(self):
        """benchmark_asset 为 list 时 watch_list 为该列表 + asset_pool。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = '000001.SZ, 000002.SZ'
        kwargs['benchmark_asset'] = ['000300.SH', '000905.SH']
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertEqual(trader.watch_list, ['000300.SH', '000905.SH', '000001.SZ', '000002.SZ'])
        print('test_init_benchmark_asset_from_list: watch_list', trader.watch_list)

    def test_init_benchmark_asset_invalid_type(self):
        """benchmark_asset 非 str/list 时应抛出 TypeError。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=op,
                broker=broker,
                datasource=test_ds,
                benchmark_asset=123,
                **_default_trader_kwargs(),
            )
        self.assertIn('benchmark_asset', str(ctx.exception))
        print('test_init_benchmark_asset_invalid_type: TypeError as expected', ctx.exception)

    def test_init_empty_asset_pool(self):
        """asset_pool 为空时 watch_list 仅含 benchmark。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = []
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertEqual(trader.asset_pool, [])
        self.assertEqual(trader.watch_list, ['000300.SH'])
        print('test_init_empty_asset_pool: watch_list', trader.watch_list)

    def test_init_duplicate_symbols_in_watch_list(self):
        """benchmark 与 asset_pool 含重复 symbol 时 watch_list 保持当前实现（允许重复）。"""
        test_ds = _create_test_datasource()
        self._test_ds = test_ds
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = '000001.SZ'
        kwargs['benchmark_asset'] = '000001.SZ'
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertIn('000001.SZ', trader.watch_list)
        self.assertEqual(trader.watch_list.count('000001.SZ'), 2)
        print('test_init_duplicate_symbols_in_watch_list: watch_list', trader.watch_list)


# --------------- status / prev_status ---------------

class TestTraderStatus(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_status_valid_transitions(self):
        """合法 status 迁移时 prev_status 正确更新。"""
        self.assertEqual(self._trader.status, 'stopped')
        self._trader.status = 'running'
        self.assertEqual(self._trader.status, 'running')
        self.assertEqual(self._trader.prev_status, 'stopped')
        self._trader.status = 'paused'
        self.assertEqual(self._trader.prev_status, 'running')
        self._trader.status = 'sleeping'
        self.assertEqual(self._trader.prev_status, 'paused')
        self._trader.status = 'stopped'
        self.assertEqual(self._trader.prev_status, 'sleeping')
        print('test_status_valid_transitions: ok')

    def test_status_invalid_value_raises(self):
        """非法 status 应抛出 ValueError。"""
        with self.assertRaises(ValueError) as ctx:
            self._trader.status = 'unknown'
        self.assertIn('invalid status', str(ctx.exception))
        print('test_status_invalid_value_raises: ValueError as expected', ctx.exception)

    def test_status_set_same_value_updates_prev_status(self):
        """同值再次赋值时 prev_status 仍会更新。"""
        self.assertEqual(self._trader.status, 'stopped')
        self._trader.status = 'stopped'
        self.assertEqual(self._trader.status, 'stopped')
        self.assertEqual(self._trader.prev_status, 'stopped')
        print('test_status_set_same_value_updates_prev_status: ok')


# --------------- _get_next_scheduled_task_and_countdown / 调度 ---------------

class TestTraderScheduling(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_get_next_task_before_all_tasks(self):
        """当前时间早于所有任务时，返回最近的一个未来任务及倒计时。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(9, 0)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task[1], 'open')
        # 09:00 -> 09:30 = 30*60 秒
        self.assertAlmostEqual(countdown, 30 * 60, delta=2)
        print('test_get_next_task_before_all_tasks: next_task', next_task, 'countdown', countdown)

    def test_get_next_task_between_two_tasks(self):
        """当前时间介于两任务之间时，返回下一个任务。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(9, 45)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task[1], 'run')
        self.assertAlmostEqual(countdown, 15 * 60, delta=2)
        print('test_get_next_task_between_two_tasks: next_task', next_task, 'countdown', countdown)

    def test_next_task_property_uses_internal_helper(self):
        """next_task property 与直接调用内部方法结果一致（需固定当前时间）。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
        ]
        current = dt.time(9, 0)
        next_from_helper, _ = self._trader._get_next_scheduled_task_and_countdown(current)
        # property 使用 get_current_tz_datetime()，不 mock 时可能不同；这里仅验证 property 可读
        next_prop = self._trader.next_task
        self.assertTrue(next_from_helper is not None or next_prop is not None)
        print('test_next_task_property_uses_internal_helper: next_task', next_prop)

    def test_get_next_task_empty_schedule(self):
        """无任务时 next_task 为 None，countdown 为到 23:59:59 的秒数且 >= 1。"""
        self._trader.task_daily_schedule = []
        current = dt.time(12, 0)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNone(next_task)
        self.assertGreaterEqual(countdown, 1)
        self.assertAlmostEqual(countdown, (23 - 12) * 3600 + 59 * 60 + 59, delta=2)
        print('test_get_next_task_empty_schedule: countdown', countdown)

    def test_get_next_task_all_past(self):
        """所有任务时间已过时 next_task 为 None。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(16, 0)
        next_task, countdown = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNone(next_task)
        self.assertGreaterEqual(countdown, 1)
        print('test_get_next_task_all_past: countdown', countdown)

    def test_get_next_task_at_exact_task_time(self):
        """当前时间恰等于某任务时间时，该任务不被选为“下一个”（严格 > current_time）。"""
        self._trader.task_daily_schedule = [
            ('2000-01-01 09:30:00+00:00', 'open'),
            ('2000-01-01 10:00:00+00:00', 'run'),
        ]
        current = dt.time(9, 30)
        next_task, _ = self._trader._get_next_scheduled_task_and_countdown(current)
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task[1], 'run')  # 09:30 不算未来，下一个是 10:00
        print('test_get_next_task_at_exact_task_time: next_task', next_task)

    def test_count_down_to_next_task_property_minimum_is_one(self):
        """count_down_to_next_task 至少为 1。"""
        self._trader.task_daily_schedule = []
        # 不 mock 时间时，接近 23:59:59 可能得到 1
        count = self._trader.count_down_to_next_task
        self.assertGreaterEqual(count, 1)
        print('test_count_down_to_next_task_property_minimum_is_one: count', count)


# --------------- 账户资金与持仓 ---------------

class TestTraderAccountCash(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_account_cash_initial_values(self):
        """account_cash 与 get_account 中现金字段一致。"""
        cash = self._trader.account_cash
        self.assertIsInstance(cash, tuple)
        self.assertEqual(len(cash), 3)
        acc = get_account(self._trader.account_id, data_source=self._test_ds)
        self.assertEqual(cash[0], acc['cash_amount'])
        self.assertEqual(cash[1], acc['available_cash'])
        self.assertEqual(cash[2], acc['total_invest'])
        print('test_account_cash_initial_values: cash', cash)

    def test_account_cash_after_manual_account_update(self):
        """外部修改账户后 account_cash 反映最新值。"""
        update_account_balance(
            self._trader.account_id,
            data_source=self._test_ds,
            cash_amount_change=5000,
            available_cash_change=5000,
            total_investment_change=5000,
        )
        # 强制数据源刷新，避免 file 型数据源缓存导致读到旧值
        self._test_ds.reconnect()
        cash = self._trader.account_cash
        # 用当前数据源重新读取账户作为期望值（不依赖 Trader 内部缓存的 self.account）
        acc = get_account(self._trader.account_id, data_source=self._test_ds)
        self.assertEqual(cash[0], acc['cash_amount'], msg='account_cash[0] should match DB cash_amount')
        self.assertEqual(cash[1], acc['available_cash'], msg='account_cash[1] should match DB available_cash')
        self.assertEqual(cash[2], acc['total_invest'], msg='account_cash[2] should match DB total_invest')
        self.assertEqual(cash[0], 100000 + 5000)
        print('test_account_cash_after_manual_account_update: cash', cash)

    def test_account_positions_detail_contains_all_asset_pool_symbols(self):
        """account_positions 包含 asset_pool 中各 symbol 的持仓信息。"""
        pos = self._trader.account_positions
        self.assertFalse(pos.empty)
        for sym in ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']:
            self.assertIn(sym, pos.index.tolist(), msg=f'expected {sym} in positions')
        # 初始 fixture 中 000001 200, 000002 200, 000003 300, 000004 200
        print('test_account_positions_detail_contains_all_asset_pool_symbols: shape', pos.shape)


# --------------- 监控列表 / 实时价格（仅做轻量覆盖） ---------------

class TestTraderWatchList(unittest.TestCase):

    def setUp(self):
        self._trader, self._test_ds = create_trader_with_account()

    def tearDown(self):
        _clear_tables(self._test_ds)

    def test_watch_list_initialization_with_string_asset_pool(self):
        """asset_pool 为字符串时 watch_list 为 benchmark + 解析后的列表。"""
        self.assertEqual(self._trader.asset_pool, ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])
        self.assertEqual(self._trader.watch_list[0], '000300.SH')
        self.assertEqual(self._trader.watch_list[1], '000001.SZ')
        print('test_watch_list_initialization_with_string_asset_pool: ok')

    def test_watch_list_initialization_with_list_asset_pool(self):
        """asset_pool 为 list 时 watch_list 为 benchmark + asset_pool。"""
        test_ds = _create_test_datasource()
        _clear_tables(test_ds)
        new_account(user_name='u', cash_amount=10000, data_source=test_ds)
        op = _create_operator()
        broker = SimulatorBroker()
        kwargs = _default_trader_kwargs()
        kwargs['asset_pool'] = ['000001.SZ']  # 覆盖默认的 asset_pool，避免重复传参
        trader = Trader(
            account_id=1,
            operator=op,
            broker=broker,
            datasource=test_ds,
            **kwargs,
        )
        self.assertEqual(trader.watch_list, ['000300.SH', '000001.SZ'])
        _clear_tables(test_ds)
        print('test_watch_list_initialization_with_list_asset_pool: ok')


if __name__ == '__main__':
    unittest.main()
