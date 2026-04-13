# coding=utf-8
# ======================================
# File:     test_trader_tui.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-04-09
# Desc:
#   Unittest for the Trader TUI.
#   使用专用测试 DataSource（非 QT_DATA_SOURCE），测试结束后清理测试数据。
# ======================================

import os
import unittest

import qteasy.trader
from qteasy import Operator, DataSource
from qteasy.trader_tui import TraderApp
from qteasy.broker import SimulatorBroker
from qteasy.trade_recording import new_account
from qteasy.risk import MaxOrderQtyRule, RiskManager


def _get_tui_test_data_dir():
    """TUI 测试专用数据目录，不使用默认 QT_DATA_SOURCE。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_test_trader_tui')


def _clear_tui_test_tables(datasource):
    """清理 TUI 测试用到的表数据，测试完成后调用。"""
    for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
        if datasource.table_data_exists(table):
            datasource.drop_table_data(table)


class TestTraderTUI(unittest.TestCase):

    def setUp(self) -> None:
        """Set up test fixtures, if any."""
        print('Setting up test Trader...')
        data_test_dir = _get_tui_test_data_dir()
        os.makedirs(data_test_dir, exist_ok=True)
        test_ds = DataSource('file', file_type='csv', file_loc=data_test_dir, allow_drop_table=True)
        _clear_tui_test_tables(test_ds)
        new_account(user_name='test_user1', cash_amount=100000, data_source=test_ds)

        operator = Operator(strategies=['macd', 'dma'], op_type='step')
        operator.set_parameter(stg_id='dma', window_length=20, run_freq='H')
        operator.set_parameter(stg_id='macd', window_length=30, run_freq='30min')
        broker = SimulatorBroker()
        config = {
            'time_zone':             'local',
            'market_open_time_am':   '09:30:00',
            'market_close_time_pm':  '15:30:00',
            'market_open_time_pm':   '13:00:00',
            'market_close_time_am':  '11:30:00',
            'exchange':              'SSE',
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
            'asset_pool':            '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
            'asset_type':            'E',
            'pt_buy_threshold':      0.05,
            'pt_sell_threshold':     0.05,
            'allow_sell_short':      False,
        }
        self.trader = qteasy.trader.Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                datasource=test_ds,
                **config,
        )

    def tearDown(self) -> None:
        """测试结束后清理测试数据。"""
        if getattr(self, 'trader', None) is not None:
            _clear_tui_test_tables(self.trader.datasource)

    def test_app_initialization_binds_trader(self):
        """TraderApp 初始化后正确绑定 Trader。"""
        app = TraderApp(trader=self.trader)
        self.assertIs(app.trader, self.trader)
        self.assertIsInstance(app.dark, bool)
        print('test_app_initialization_binds_trader: ok')

    def test_action_toggle_dark(self):
        """action_toggle_dark 切换 dark 状态。"""
        trader = self.trader
        app = TraderApp(trader=trader)
        initial = app.dark
        app.action_toggle_dark()
        self.assertEqual(app.dark, not initial)
        app.action_toggle_dark()
        self.assertEqual(app.dark, initial)
        print('test_action_toggle_dark: ok')

    def test_action_toggle_dark_twice_back_to_original(self):
        """连续两次 toggle_dark 后恢复初始状态。"""
        app = TraderApp(trader=self.trader)
        original = app.dark
        app.action_toggle_dark()
        app.action_toggle_dark()
        self.assertEqual(app.dark, original, msg='two toggles should restore original')
        print('test_action_toggle_dark_twice_back_to_original: ok')

    def test_submit_order_logs_risk_reject_summary(self):
        """submit_order 在风控拒单时写入摘要日志。"""
        print('\n[TestTraderTUI] submit_order writes risk reject summary')

        class _DummySysLog:
            def __init__(self):
                self.messages = []

            def write_with_timestamp(self, msg):
                self.messages.append(str(msg))

        app = TraderApp(trader=self.trader)
        self.trader.risk_manager = RiskManager((MaxOrderQtyRule('mx', 5.0),))
        dummy_log = _DummySysLog()
        app.query_one = lambda *args, **kwargs: dummy_log

        app.submit_order(symbol='000001.SZ', position='long', qty=100, price=10.0, direction='buy')
        print(' syslog messages:', dummy_log.messages)
        self.assertTrue(any('Order submission rejected by risk manager' in m for m in dummy_log.messages))
        self.assertTrue(any('rule_id=' in m for m in dummy_log.messages))
        self.assertTrue(any('reason=' in m for m in dummy_log.messages))
        self.assertTrue(self.trader.broker.order_queue.empty())


if __name__ == '__main__':
    unittest.main()
