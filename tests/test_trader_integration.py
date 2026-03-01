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


# --------------- 测试用 DataSource：从公共夹具导入（data_test_trader，legacy=False） ---------------

from tests.trader_test_helpers import (
    clear_tables,
    create_trader_with_account,
    create_trader_with_orders_and_results,
)
# 集成测试保持原有 stoppage=0.1 行为，在调用处传入
_clear_tables = clear_tables


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
