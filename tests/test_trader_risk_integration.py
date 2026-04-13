# coding=utf-8
# ======================================
# File: test_trader_risk_integration.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
# Unittest for Trader risk_manager integration and get_account_snapshot (S1.3 P4).
# ======================================

from __future__ import annotations

import os
import unittest
from datetime import date, datetime

from qteasy.broker import SimulatorBroker
from qteasy.qt_operator import Operator
from qteasy.risk import MaxOrderQtyRule, RiskManager, SymbolWhitelistRule
from qteasy.trade_io import validate_trade_order
from qteasy.trade_recording import (
    get_account_positions,
    get_or_create_position,
    query_trade_orders,
    record_trade_order,
)
from qteasy.trader import Trader
from qteasy.trading_util import submit_order

from tests.trader_test_helpers import (
    clear_tables,
    create_operator,
    create_test_datasource,
    default_trader_kwargs,
)


def _make_trader(ds, *, risk_manager=None, account_id: int = 1, debug: bool = False) -> Trader:
    op = create_operator()
    br = SimulatorBroker()
    return Trader(
        account_id=account_id,
        operator=op,
        broker=br,
        datasource=ds,
        debug=debug,
        risk_manager=risk_manager,
        **default_trader_kwargs(),
    )


class TestGetAccountSnapshot(unittest.TestCase):
    """A. get_account_snapshot 功能与边界。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        from qteasy.trade_recording import new_account

        new_account(user_name='risk_snap_u1', cash_amount=100000.0, data_source=self.ds)
        for sym in ['000001.SZ', '000002.SZ']:
            get_or_create_position(account_id=1, symbol=sym, position_type='long', data_source=self.ds)
        from qteasy.trade_recording import update_position

        update_position(position_id=1, data_source=self.ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=self.ds, qty_change=150, available_qty_change=150)
        self.trader = _make_trader(self.ds, risk_manager=None)

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_snapshot_positions_match_sys_op_positions(self) -> None:
        print('\n[TestGetAccountSnapshot] positions vs sys_op_positions')
        snap = self.trader.get_account_snapshot(as_of=datetime(2024, 6, 1, 10, 0, 0))
        pos_df = get_account_positions(1, data_source=self.ds)
        print(' snapshot.positions:', snap.positions)
        print(' pos_df:\n', pos_df)
        for _, row in pos_df.iterrows():
            key = (str(row['symbol']), str(row['position']))
            self.assertAlmostEqual(snap.positions[key], float(row['qty']), places=6)

    def test_snapshot_daily_turnover_sums_submitted_orders(self) -> None:
        print('\n[TestGetAccountSnapshot] daily turnover sum')
        self.trader.renew_trade_log_file()
        self.trader.init_system_logger()
        pid = get_or_create_position(1, '000004.SZ', 'long', data_source=self.ds)
        o1 = {
            'pos_id': pid,
            'direction': 'buy',
            'order_type': 'limit',
            'qty': 100.0,
            'price': 10.0,
            'submitted_time': None,
            'status': 'created',
        }
        oid1 = record_trade_order(o1, data_source=self.ds)
        self.assertIsNotNone(submit_order(oid1, self.ds))
        o2 = {
            'pos_id': pid,
            'direction': 'buy',
            'order_type': 'limit',
            'qty': 50.0,
            'price': 20.0,
            'submitted_time': None,
            'status': 'created',
        }
        oid2 = record_trade_order(o2, data_source=self.ds)
        self.assertIsNotNone(submit_order(oid2, self.ds))
        n1 = 100.0 * 10.0
        n2 = 50.0 * 20.0
        exp = n1 + n2
        snap = self.trader.get_account_snapshot()
        print(' daily_turnover_used:', snap.daily_turnover_used, ' expected:', exp)
        self.assertAlmostEqual(snap.daily_turnover_used, exp, places=6)

    def test_snapshot_empty_positions_zero_turnover(self) -> None:
        print('\n[TestGetAccountSnapshot] empty account positions and turnover')
        ds2 = create_test_datasource(legacy=False)
        clear_tables(ds2)
        from qteasy.trade_recording import new_account

        new_account(user_name='risk_empty', cash_amount=10000.0, data_source=ds2)
        tr = _make_trader(ds2, risk_manager=None)
        snap = tr.get_account_snapshot(as_of=datetime(2024, 7, 1, 9, 30, 0))
        print(' positions:', snap.positions, ' used:', snap.daily_turnover_used)
        self.assertEqual(snap.positions, {})
        self.assertEqual(snap.daily_turnover_used, 0.0)
        clear_tables(ds2)

    def test_snapshot_trading_date_override_filters_orders(self) -> None:
        print('\n[TestGetAccountSnapshot] trading_date filters submitted_time')
        self.trader.renew_trade_log_file()
        self.trader.init_system_logger()
        pid = get_or_create_position(1, '000005.SZ', 'long', data_source=self.ds)
        o1 = {
            'pos_id': pid,
            'direction': 'buy',
            'order_type': 'limit',
            'qty': 10.0,
            'price': 5.0,
            'submitted_time': None,
            'status': 'created',
        }
        oid1 = record_trade_order(o1, data_source=self.ds)
        submit_order(oid1, self.ds)
        o2 = dict(o1)
        o2['qty'] = 20.0
        o2['price'] = 6.0
        oid2 = record_trade_order(o2, data_source=self.ds)
        submit_order(oid2, self.ds)
        self.ds.update_sys_table_data(
            'sys_op_trade_orders',
            record_id=int(oid1),
            submitted_time='2024-01-02 10:00:00',
        )
        self.ds.update_sys_table_data(
            'sys_op_trade_orders',
            record_id=int(oid2),
            submitted_time='2024-01-03 10:00:00',
        )
        n_day2 = 10.0 * 5.0
        snap = self.trader.get_account_snapshot(
            as_of=datetime(2024, 1, 3, 12, 0, 0),
            trading_date=date(2024, 1, 2),
        )
        print(' used for 2024-01-02:', snap.daily_turnover_used, ' expected:', n_day2)
        self.assertAlmostEqual(snap.daily_turnover_used, n_day2, places=6)
        clear_tables(self.ds)


class TestSubmitWithoutRiskManager(unittest.TestCase):
    """B. 无 risk_manager 回归。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        from qteasy.trade_recording import new_account

        new_account(user_name='risk_b1', cash_amount=100000.0, data_source=self.ds)
        get_or_create_position(1, '000001.SZ', 'long', data_source=self.ds)
        self.trader = _make_trader(self.ds, risk_manager=None)

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_submit_without_risk_manager_unchanged(self) -> None:
        print('\n[TestSubmitWithoutRiskManager] submit with risk_manager None')
        before = len(query_trade_orders(1, data_source=self.ds))
        res = self.trader.submit_trade_order(
            symbol='000001.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=10,
            price=50.0,
        )
        print(' res:', res, ' before:', before, ' after:', len(query_trade_orders(1, data_source=self.ds)))
        self.assertIn('order_id', res)
        self.assertGreater(res['order_id'], 0)
        df = query_trade_orders(1, data_source=self.ds)
        self.assertGreaterEqual(len(df), before + 1)


class TestRiskRejectPaths(unittest.TestCase):
    """C. 风控拒绝。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        from qteasy.trade_recording import new_account

        new_account(user_name='risk_rej', cash_amount=100000.0, data_source=self.ds)
        for sym in ['000001.SZ', '000002.SZ']:
            get_or_create_position(1, sym, 'long', data_source=self.ds)
        wl = RiskManager((SymbolWhitelistRule('wl', frozenset({'000001.SZ'})),))
        self.trader = _make_trader(self.ds, risk_manager=wl)
        self.trader.renew_trade_log_file()
        path = __import__('qteasy.trading_util', fromlist=['sys_log_file_path_name']).sys_log_file_path_name(
            self.trader.account_id, self.trader.datasource,
        )
        if os.path.exists(path):
            os.remove(path)
        self.trader.live_sys_logger = None
        self.trader.init_system_logger()

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_risk_reject_whitelist_no_order_row(self) -> None:
        print('\n[TestRiskRejectPaths] whitelist reject no new order')
        before = len(query_trade_orders(1, data_source=self.ds))
        res = self.trader.submit_trade_order(
            symbol='000002.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=10,
            price=10.0,
        )
        after = len(query_trade_orders(1, data_source=self.ds))
        print(' before:', before, ' after:', after, ' res:', res)
        self.assertEqual(res, {})
        self.assertEqual(before, after)

    def test_risk_reject_max_qty_no_order_row(self) -> None:
        print('\n[TestRiskRejectPaths] max qty reject')
        rm = RiskManager((MaxOrderQtyRule('mx', 5.0),))
        tr = _make_trader(self.ds, risk_manager=rm)
        tr.renew_trade_log_file()
        before = len(query_trade_orders(1, data_source=self.ds))
        res = tr.submit_trade_order(
            symbol='000001.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=100,
            price=10.0,
        )
        print(' res:', res, ' orders before/after:', before, len(query_trade_orders(1, data_source=self.ds)))
        self.assertEqual(res, {})
        self.assertEqual(len(query_trade_orders(1, data_source=self.ds)), before)

    def test_risk_reject_sends_english_sys_message(self) -> None:
        print('\n[TestRiskRejectPaths] sys log contains RISK REJECTED')
        res = self.trader.submit_trade_order(
            symbol='000002.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=1,
            price=10.0,
        )
        self.assertEqual(res, {})
        lines = self.trader.read_sys_log(row_count=50)
        print(' last log lines:', lines[-3:] if lines else [])
        hit = [ln for ln in lines if '<RISK REJECTED>' in ln]
        self.assertTrue(any('<RISK REJECTED>' in ln for ln in lines))
        self.assertTrue(any('rule_id=' in ln for ln in hit))
        self.assertTrue(any('reason=' in ln for ln in hit))


class TestRiskAllowPaths(unittest.TestCase):
    """D. 风控放行。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        from qteasy.trade_recording import new_account

        new_account(user_name='risk_ok', cash_amount=100000.0, data_source=self.ds)
        get_or_create_position(1, '000001.SZ', 'long', data_source=self.ds)

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_risk_allow_creates_submitted_order(self) -> None:
        print('\n[TestRiskAllowPaths] whitelist allows submit')
        wl = RiskManager((SymbolWhitelistRule('wl', frozenset({'000001.SZ'})),))
        tr = _make_trader(self.ds, risk_manager=wl)
        res = tr.submit_trade_order(
            symbol='000001.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=10,
            price=50.0,
        )
        print(' res:', res)
        self.assertIn('order_id', res)
        self.assertGreater(res['order_id'], 0)
        validate_trade_order(res, context='integration.allow')

    def test_risk_manager_empty_rules_allows_submit(self) -> None:
        print('\n[TestRiskAllowPaths] empty RiskManager allows')
        tr = _make_trader(self.ds, risk_manager=RiskManager(()))
        res = tr.submit_trade_order(
            symbol='000001.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=5,
            price=40.0,
        )
        print(' res:', res)
        self.assertIn('order_id', res)
        self.assertGreater(res['order_id'], 0)


class TestRejectNoQueuePollution(unittest.TestCase):
    """E. 拒单与入队条件（由调用方 if trade_order 守卫）。"""

    def test_reject_empty_dict_blocks_put_pattern(self) -> None:
        print('\n[TestRejectNoQueuePollution] falsy dict would not enqueue')
        self.assertFalse(bool({}))
        self.assertTrue(bool({'order_id': 1}))


if __name__ == '__main__':
    unittest.main()
