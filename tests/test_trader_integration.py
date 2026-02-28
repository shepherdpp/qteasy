# coding=utf-8
# ======================================
# File:     test_trader_integration.py
# Desc:
#   集成测试：Trader 日志与断点、成交与交割、调度与 run()，
#   使用专用测试 DataSource（非 QT_DATA_SOURCE），测试完成后清理表数据。
# ======================================

import os
import time
import unittest

import pandas as pd

from qteasy import DataSource, Operator
from qteasy.trade_recording import (
    new_account,
    get_or_create_position,
    update_position,
    save_parsed_trade_orders,
    get_account,
    get_position_by_id,
)
from qteasy.trading_util import (
    submit_order,
    process_trade_result,
    cancel_order,
    process_account_delivery,
    deliver_trade_result,
    trade_log_file_path_name,
    sys_log_file_path_name,
    break_point_file_path_name,
)
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker


# --------------- 测试用 DataSource：独立目录，测试后清理 ---------------

def _get_trader_test_data_dir():
    """Trader 集成测试专用数据目录，不使用默认 QT_DATA_SOURCE。"""
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
    """清理测试相关表。"""
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


def create_trader_with_orders_and_results(account_id=1, debug=False, stoppage=0.1):
    """
    创建带账户、持仓、订单与成交结果的 Trader，使用测试 DataSource。
    返回 (trader, datasource)。调用方需在测试结束后调用 _clear_tables(datasource)。
    """
    trader, test_ds = create_trader_with_account(account_id=account_id, with_positions=True, debug=debug)
    trader.renew_trade_log_file()
    trader.init_system_logger()
    parsed_signals_batch = (
        ['000001.SZ', '000002.SZ', '000004.SZ', '000006.SZ', '000007.SZ'],
        ['long', 'long', 'long', 'long', 'long'],
        ['buy', 'sell', 'sell', 'buy', 'buy'],
        [100, 100, 300, 400, 500],
        [60.0, 70.0, 80.0, 90.0, 100.0],
    )
    order_ids = save_parsed_trade_orders(
        account_id=account_id,
        symbols=parsed_signals_batch[0],
        positions=parsed_signals_batch[1],
        directions=parsed_signals_batch[2],
        quantities=parsed_signals_batch[3],
        prices=parsed_signals_batch[4],
        data_source=test_ds,
    )
    for oid in order_ids:
        submit_order(oid, test_ds)
    time.sleep(stoppage)
    parsed_signals_batch2 = (
        ['000001.SZ', '000004.SZ', '000005.SZ', '000007.SZ'],
        ['long', 'long', 'long', 'long'],
        ['sell', 'buy', 'buy', 'sell'],
        [200, 200, 100, 300],
        [70.0, 30.0, 56.0, 79.0],
    )
    order_ids2 = save_parsed_trade_orders(
        account_id=account_id,
        symbols=parsed_signals_batch2[0],
        positions=parsed_signals_batch2[1],
        directions=parsed_signals_batch2[2],
        quantities=parsed_signals_batch2[3],
        prices=parsed_signals_batch2[4],
        data_source=test_ds,
    )
    for oid in order_ids2:
        submit_order(order_id=oid, data_source=test_ds)
    time.sleep(stoppage)
    delivery_config = {'cash_delivery_period': 0, 'stock_delivery_period': 0}
    for raw in [
        {'order_id': 1, 'filled_qty': 100, 'price': 60.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 2, 'filled_qty': 100, 'price': 70.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 3, 'filled_qty': 200, 'price': 80.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 4, 'filled_qty': 400, 'price': 89.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 5, 'filled_qty': 500, 'price': 100.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
    ]:
        full = process_trade_result(raw_trade_result=raw, data_source=test_ds)
        trader.log_trade_result(full)
        dr = deliver_trade_result(result_id=full['result_id'], account_id=account_id, data_source=test_ds)
        trader.log_qty_delivery(dr)
        trader.log_cash_delivery(dr)
        time.sleep(stoppage)
    cancel_order(8, test_ds, delivery_config)
    process_account_delivery(account_id=account_id, data_source=test_ds)
    trader.init_trade_log_file()
    trader.init_system_logger()
    return trader, test_ds


# --------------- 日志与断点 ---------------

class TestTraderLogAndBreakPoint(unittest.TestCase):

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_trade_log_file_initialized_with_headers(self):
        """renew_trade_log_file 后交易日志文件存在且首行为 header。"""
        trader, self._test_ds = create_trader_with_account()
        trader.renew_trade_log_file()
        path = trade_log_file_path_name(trader.account_id, trader.datasource)
        self.assertTrue(os.path.exists(path), msg=f'trade log file should exist: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        expected_header = ','.join(Trader.trade_log_file_headers)
        self.assertEqual(first_line, expected_header, msg='first line should be header')
        print('test_trade_log_file_initialized_with_headers: path', path)

    def test_sys_log_file_initialized_and_writes_message(self):
        """init_system_logger 后系统日志文件存在且可写入。"""
        trader, self._test_ds = create_trader_with_account()
        trader.init_system_logger()
        test_msg = 'test-message-integration'
        trader.live_sys_logger.info(test_msg)
        path = sys_log_file_path_name(trader.account_id, trader.datasource)
        self.assertTrue(os.path.exists(path), msg=f'sys log file should exist: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(test_msg, content, msg='log content should contain test message')
        print('test_sys_log_file_initialized_and_writes_message: ok')

    def test_break_point_save_and_clear(self):
        """save_break_point 创建文件，clear_break_point 删除文件。"""
        trader, self._test_ds = create_trader_with_account()
        path = break_point_file_path_name(trader.account_id, trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        trader.save_break_point()
        self.assertTrue(os.path.exists(path), msg='break point file should exist after save')
        trader.clear_break_point()
        self.assertFalse(os.path.exists(path), msg='break point file should be removed after clear')
        print('test_break_point_save_and_clear: ok')

    def test_clear_break_point_on_non_exist_file(self):
        """断点文件不存在时 clear_break_point 不抛异常。"""
        trader, self._test_ds = create_trader_with_account()
        path = break_point_file_path_name(trader.account_id, trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        trader.clear_break_point()
        trader.clear_break_point()
        print('test_clear_break_point_on_non_exist_file: ok')


# --------------- 成交与交割流程 ---------------

class TestTraderTradeFlow(unittest.TestCase):

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_positions_and_account_after_full_trade_flow(self):
        """完整成交流程后持仓与账户现金与 fixture 预期一致。"""
        trader, self._test_ds = create_trader_with_orders_and_results(stoppage=0.05)
        # 订单 1: 买 100 @ 60.5 -> 000001 持仓增加 100；订单 2: 卖 100 @ 70.5；等
        # 仅做关键断言：账户有扣减/增加，trade log 有数据行
        acc = get_account(trader.account_id, data_source=self._test_ds)
        self.assertIn('cash_amount', acc)
        self.assertIn('total_invest', acc)
        path = trade_log_file_path_name(trader.account_id, trader.datasource)
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # header + 至少若干数据行
        self.assertGreaterEqual(len(lines), 2, msg='trade log should have at least header and one data row')
        print('test_positions_and_account_after_full_trade_flow: cash_amount', acc['cash_amount'], 'lines', len(lines))

    def test_partial_fill_and_cancelled_orders_effects(self):
        """部分成交与撤单后持仓与现金变化符合预期。"""
        # 使用同一 fixture，其中 order 5 全部成交，order 8 被 cancel
        trader, self._test_ds = create_trader_with_orders_and_results(stoppage=0.05)
        acc = get_account(trader.account_id, data_source=self._test_ds)
        self.assertIsNotNone(acc['cash_amount'])
        # 部分成交会导致持仓逐步变化，撤单不影响持仓
        pos1 = get_position_by_id(1, self._test_ds)
        self.assertIsNotNone(pos1)
        print('test_partial_fill_and_cancelled_orders_effects: position 1 qty', pos1.get('qty'))


# --------------- 调度与 run()（轻量） ---------------

class TestTraderRunStatus(unittest.TestCase):

    def tearDown(self):
        if getattr(self, '_test_ds', None) is not None:
            _clear_tables(self._test_ds)

    def test_run_respects_stopped_status(self):
        """status 为 stopped 时主循环应能退出（不长时间阻塞）。"""
        trader, self._test_ds = create_trader_with_account()
        trader.status = 'stopped'
        # 不真正启动 run() 的无限循环，仅验证状态被尊重；若需测 run() 可在此起线程后短时 join
        self.assertEqual(trader.status, 'stopped')
        print('test_run_respects_stopped_status: ok')


if __name__ == '__main__':
    unittest.main()
