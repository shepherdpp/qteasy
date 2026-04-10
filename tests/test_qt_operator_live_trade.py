# coding=utf-8
# ======================================
# File: test_qt_operator_live_trade.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-10
# Desc:
# Unittest for Operator.run_live_trade asset_type (E/FD) and Trader wiring.
# ======================================

import os
import unittest
from unittest.mock import patch

import pandas as pd

from qteasy import QT_CONFIG, DataSource, Operator
from qteasy.trade_recording import new_account


def _live_trade_config_base(account_id: int) -> dict:
    """从全局 QT_CONFIG 复制一份并填入 run_live_trade 所需键，避免手写遗漏。"""
    cfg = QT_CONFIG.copy()
    cfg['mode'] = 0
    cfg['live_trade_account_id'] = account_id
    cfg['live_trade_init_holdings'] = None
    cfg['live_trade_broker_type'] = 'simulator'
    cfg['live_trade_broker_params'] = None
    cfg['live_trade_ui_type'] = 'cli'
    cfg['asset_pool'] = '000001.SZ'
    return cfg


class TestQtOperatorLiveTradeAssetType(unittest.TestCase):
    """P0-fd：live-trade 对 E/FD 的白名单与 Trader.asset_type 透传。"""

    @classmethod
    def setUpClass(cls):
        cls._data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data_test_qt_operator_live',
        )
        os.makedirs(cls._data_dir, exist_ok=True)

    def setUp(self):
        print('\n[TestQtOperatorLiveTradeAssetType] setUp')
        self.test_ds = DataSource(
            'file',
            file_type='csv',
            file_loc=self._data_dir,
            allow_drop_table=True,
        )
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                      'sys_op_trade_results', 'stock_daily']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)
        self.live_account_id = new_account(
            user_name='live_test_u', cash_amount=1_000_000.0, data_source=self.test_ds)

    def tearDown(self):
        if getattr(self, 'test_ds', None) is not None:
            for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                          'sys_op_trade_results', 'stock_daily']:
                if self.test_ds.table_data_exists(table):
                    self.test_ds.drop_table_data(table)

    @patch('qteasy.trader_cli.TraderShell')
    @patch('qteasy.trader.refill_missing_datasource_data')
    def test_run_live_trade_accepts_fd_with_simulator(self, _mock_refill, _mock_shell):
        print('\n[TestQtOperatorLiveTradeAssetType] test_run_live_trade_accepts_fd_with_simulator')
        cfg = _live_trade_config_base(self.live_account_id)
        cfg['asset_type'] = 'FD'
        op = Operator(strategies=['macd'])
        op.set_parameter(stg_id='macd', window_length=5, run_freq='d')
        op.run_live_trade(config=cfg, datasource=self.test_ds)
        created = _mock_shell.call_args[0][0]
        self.assertEqual(created.asset_type, 'FD')

    @patch('qteasy.trader_cli.TraderShell')
    @patch('qteasy.trader.refill_missing_datasource_data')
    def test_run_live_trade_passes_asset_type_e_and_fd(self, _mock_refill, _mock_shell):
        print('\n[TestQtOperatorLiveTradeAssetType] test_run_live_trade_passes_asset_type_e_and_fd')
        op = Operator(strategies=['macd'])
        op.set_parameter(stg_id='macd', window_length=5, run_freq='d')
        for at in ('E', 'FD'):
            cfg = _live_trade_config_base(self.live_account_id)
            cfg['asset_type'] = at
            op.run_live_trade(config=cfg, datasource=self.test_ds)
            trader = _mock_shell.call_args[0][0]
            self.assertEqual(trader.asset_type, at, msg=f'asset_type={at}')
            print(f' passed asset_type={at} -> trader.asset_type={trader.asset_type}')

    def test_run_live_trade_rejects_unsupported_asset_type(self):
        print('\n[TestQtOperatorLiveTradeAssetType] test_run_live_trade_rejects_unsupported_asset_type')
        cfg = _live_trade_config_base(self.live_account_id)
        cfg['asset_type'] = 'X'
        op = Operator(strategies=['macd'])
        op.set_parameter(stg_id='macd', window_length=5, run_freq='d')
        with self.assertRaises(ValueError) as ctx:
            op.run_live_trade(config=cfg, datasource=self.test_ds)
        msg = str(ctx.exception)
        self.assertTrue(all(ord(c) < 128 for c in msg), msg='user-facing error must be ASCII/English')
        self.assertIn('E', msg)
        self.assertIn('FD', msg)
        print(' error message:', msg[:200])


class TestTraderAccountPositionInfoAssetType(unittest.TestCase):
    """account_position_info 在补历史价时应使用 Trader.asset_type。"""

    def setUp(self):
        print('\n[TestTraderAccountPositionInfoAssetType] setUp')
        self._calls = []

        data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data_test_qt_operator_live',
        )
        os.makedirs(data_dir, exist_ok=True)
        self.test_ds = DataSource('file', file_type='csv', file_loc=data_dir, allow_drop_table=True)
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                      'sys_op_trade_results', 'stock_daily']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)
        new_account(user_name='pos_info_u', cash_amount=100_000.0, data_source=self.test_ds)

        from tests.trader_test_helpers import create_operator
        from qteasy.trade_recording import get_or_create_position, update_position
        from qteasy.trader import Trader
        from qteasy.broker import SimulatorBroker

        get_or_create_position(account_id=1, symbol='515630.SH', position_type='long', data_source=self.test_ds)
        update_position(position_id=1, data_source=self.test_ds, qty_change=100.0, available_qty_change=100.0)
        op = create_operator()
        self.trader_fd = Trader(
            account_id=1,
            operator=op,
            broker=SimulatorBroker(),
            datasource=self.test_ds,
            asset_pool=['515630.SH'],
            asset_type='FD',
        )
        self.trader_fd.live_price = None

    def tearDown(self):
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                      'sys_op_trade_results', 'stock_daily']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)

    def test_trader_account_position_info_uses_trader_asset_type_for_history(self):
        print('\n[TestTraderAccountPositionInfoAssetType] history branch uses self.asset_type')

        captured = {}

        def fake_get_history_data(**kwargs):
            captured['asset_type'] = kwargs.get('asset_type')
            # 最小 close 序列，满足 .iloc[-1] 索引
            idx = pd.to_datetime(['2020-01-02', '2020-01-03'])
            return pd.DataFrame({'close': [1.0, 2.0]}, index=idx)

        with patch('qteasy.core.get_history_data', side_effect=fake_get_history_data):
            _ = self.trader_fd.account_position_info

        self.assertEqual(captured.get('asset_type'), 'FD')
        print(' captured asset_type:', captured)


if __name__ == '__main__':
    unittest.main()
