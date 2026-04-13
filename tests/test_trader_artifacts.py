# coding=utf-8
# ======================================
# File: test_trader_artifacts.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
# Unittest for S1.3 P5 live-trade artifact paths, risk_log, delete_account cleanup,
# and compatibility with log path hot refresh.
# ======================================

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

import qteasy as qt
from qteasy.broker import SimulatorBroker
from qteasy.qt_operator import Operator
from qteasy.risk import RiskManager, SymbolWhitelistRule
from qteasy.trade_recording import (
    delete_account,
    new_account,
    get_or_create_position,
    query_trade_orders,
)
from qteasy.trader import Trader
from qteasy.trading_util import (
    append_live_trade_risk_log_line,
    break_point_file_path_name,
    list_live_trade_artifacts,
    risk_log_file_path_name,
    sys_log_file_path_name,
    trade_log_file_path_name,
)

from tests.trader_test_helpers import (
    clear_tables,
    create_operator,
    create_test_datasource,
    default_trader_kwargs,
)


def _make_trader(ds, *, risk_manager=None, account_id: int = 1) -> Trader:
    op = create_operator()
    br = SimulatorBroker()
    return Trader(
        account_id=account_id,
        operator=op,
        broker=br,
        datasource=ds,
        debug=False,
        risk_manager=risk_manager,
        **default_trader_kwargs(),
    )


class TestListLiveTradeArtifacts(unittest.TestCase):
    """产物清单：键与路径与 helper 一致。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        new_account(user_name='artifact_u1', cash_amount=100000.0, data_source=self.ds)

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_list_live_trade_artifacts_keys_and_paths(self) -> None:
        print('\n[TestListLiveTradeArtifacts] keys and paths vs helpers')
        aid = 1
        arts = list_live_trade_artifacts(aid, data_source=self.ds)
        print(' artifacts:', arts)
        self.assertIsInstance(arts, dict)
        self.assertEqual(set(arts.keys()), {'sys_log', 'trade_log', 'break_point', 'risk_log'})
        for k, v in arts.items():
            self.assertIsInstance(v, str, msg=k)
            self.assertTrue(os.path.isabs(v), msg=k)
        self.assertEqual(arts['sys_log'], sys_log_file_path_name(aid, self.ds))
        self.assertEqual(arts['trade_log'], trade_log_file_path_name(aid, self.ds))
        self.assertEqual(arts['break_point'], break_point_file_path_name(aid, self.ds))
        self.assertEqual(arts['risk_log'], risk_log_file_path_name(aid, self.ds))

    def test_list_live_trade_artifacts_unknown_account_raises(self) -> None:
        print('\n[TestListLiveTradeArtifacts] unknown account KeyError')
        with self.assertRaises(KeyError):
            list_live_trade_artifacts(99999, data_source=self.ds)

    def test_list_live_trade_artifacts_type_error_on_bad_datasource(self) -> None:
        print('\n[TestListLiveTradeArtifacts] bad data_source TypeError')
        with self.assertRaises(TypeError):
            list_live_trade_artifacts(1, data_source='not_a_datasource')  # type: ignore[arg-type]


class TestRiskLogAndReject(unittest.TestCase):
    """风控拒单写 risk_log。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        new_account(user_name='risklog_u1', cash_amount=100000.0, data_source=self.ds)
        get_or_create_position(1, '000001.SZ', 'long', data_source=self.ds)
        wl = RiskManager((SymbolWhitelistRule('wl', frozenset({'000001.SZ'})),))
        self.trader = _make_trader(self.ds, risk_manager=wl)
        self.trader.renew_trade_log_file()

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_risk_reject_appends_risk_log_line(self) -> None:
        print('\n[TestRiskLogAndReject] reject writes risk_log')
        rpath = risk_log_file_path_name(1, self.ds)
        if os.path.exists(rpath):
            os.remove(rpath)
        before = len(query_trade_orders(1, data_source=self.ds))
        res = self.trader.submit_trade_order(
            symbol='000002.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=1,
            price=10.0,
        )
        print(' risk path:', rpath, ' res:', res, ' orders before:', before)
        self.assertEqual(res, {})
        self.assertEqual(len(query_trade_orders(1, data_source=self.ds)), before)
        self.assertTrue(os.path.isfile(rpath), msg='risk_log file should exist')
        with open(rpath, 'r', encoding='utf-8') as f:
            text = f.read()
        print(' risk log content:', text.strip())
        self.assertIn('<RISK REJECTED>', text)
        self.assertIn('rule_id=', text)
        self.assertIn('reason=', text)

    def test_append_multiple_rejects_multiple_lines(self) -> None:
        print('\n[TestRiskLogAndReject] two rejects -> two lines')
        rpath = risk_log_file_path_name(1, self.ds)
        if os.path.exists(rpath):
            os.remove(rpath)
        wl = RiskManager((SymbolWhitelistRule('wl', frozenset({'000001.SZ'})),))
        tr = _make_trader(self.ds, risk_manager=wl)
        tr.renew_trade_log_file()
        tr.submit_trade_order(
            symbol='000002.SZ', position='long', direction='buy',
            order_type='limit', qty=1, price=10.0,
        )
        tr.submit_trade_order(
            symbol='000002.SZ', position='long', direction='buy',
            order_type='limit', qty=2, price=11.0,
        )
        with open(rpath, 'r', encoding='utf-8') as f:
            lines = [ln for ln in f.readlines() if '<RISK REJECTED>' in ln]
        print(' reject lines count:', len(lines), ' lines:', lines)
        self.assertEqual(len(lines), 2)


class TestDeleteAccountArtifacts(unittest.TestCase):
    """delete_account 清理四类产品文件。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        new_account(user_name='delart_u1', cash_amount=100000.0, data_source=self.ds)

    def tearDown(self) -> None:
        if self.ds.table_data_exists('sys_op_live_accounts'):
            clear_tables(self.ds)

    def test_delete_account_removes_risk_log_when_present(self) -> None:
        print('\n[TestDeleteAccountArtifacts] delete removes four files')
        aid = 1
        paths = list_live_trade_artifacts(aid, data_source=self.ds)
        for p in paths.values():
            os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                f.write('x')
        for k, p in paths.items():
            self.assertTrue(os.path.isfile(p), msg=f'precondition {k}: {p}')
            print(' before exists', k, p)
        delete_account(aid, data_source=self.ds, keep_account_id=True)
        for k, p in paths.items():
            self.assertFalse(os.path.isfile(p), msg=f'after delete {k}: {p}')
            print(' after exists', k, os.path.isfile(p))

    def test_delete_account_no_risk_file_no_error(self) -> None:
        print('\n[TestDeleteAccountArtifacts] no risk file still ok')
        delete_account(1, data_source=self.ds, keep_account_id=True)
        acc = self.ds.read_sys_table_data('sys_op_live_accounts')
        print(' accounts rows after delete keep id:', len(acc))
        self.assertFalse(acc.empty)


class TestRiskLogFilenameSanitized(unittest.TestCase):
    """user_name 需清洗时 risk_log  basename 安全。"""

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_risk_log_filename_sanitized(self) -> None:
        print('\n[TestRiskLogFilenameSanitized] special user_name')
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        new_account(user_name='weird Name/<>*', cash_amount=1.0, data_source=self.ds)
        rpath = risk_log_file_path_name(1, self.ds)
        base = os.path.basename(rpath)
        print(' risk path:', rpath, ' basename:', base)
        self.assertTrue(base.endswith('.risk.log'))
        self.assertNotIn('/', base)
        self.assertTrue(rpath.startswith(os.path.normpath(qt.QT_TRADE_LOG_PATH)))


class TestConfigureArtifactPaths(unittest.TestCase):
    """configure 热更新后清单路径前缀变化。"""

    def setUp(self) -> None:
        self._old_sys = qt.QT_CONFIG.get('sys_log_file_path')
        self._old_trade = qt.QT_CONFIG.get('trade_log_file_path')
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        new_account(user_name='cfg_art_u1', cash_amount=100000.0, data_source=self.ds)

    def tearDown(self) -> None:
        clear_tables(self.ds)
        qt.configure(sys_log_file_path=self._old_sys, trade_log_file_path=self._old_trade)

    def test_list_matches_post_configure_paths(self) -> None:
        print('\n[TestConfigureArtifactPaths] after configure paths')
        tmp_sys = tempfile.mkdtemp(prefix='qt_sys_')
        tmp_trade = tempfile.mkdtemp(prefix='qt_trd_')
        try:
            abs_sys = os.path.abspath(tmp_sys)
            abs_trade = os.path.abspath(tmp_trade)
            qt.configure(sys_log_file_path=abs_sys, trade_log_file_path=abs_trade)
            arts = list_live_trade_artifacts(1, data_source=self.ds)
            print(' artifacts after configure:', arts)
            ns = os.path.normpath(abs_sys)
            nt = os.path.normpath(abs_trade)
            self.assertTrue(
                os.path.normpath(arts['sys_log']).startswith(ns),
                msg=arts['sys_log'],
            )
            self.assertTrue(
                os.path.normpath(arts['trade_log']).startswith(nt),
                msg=arts['trade_log'],
            )
            self.assertTrue(
                os.path.normpath(arts['risk_log']).startswith(nt),
                msg=arts['risk_log'],
            )
            self.assertTrue(
                os.path.normpath(arts['break_point']).startswith(ns),
                msg=arts['break_point'],
            )
        finally:
            shutil.rmtree(tmp_sys, ignore_errors=True)
            shutil.rmtree(tmp_trade, ignore_errors=True)


class TestAppendRiskLogLineDirect(unittest.TestCase):
    """append_live_trade_risk_log_line 直接调用。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)
        clear_tables(self.ds)
        new_account(user_name='append_u1', cash_amount=1.0, data_source=self.ds)

    def tearDown(self) -> None:
        clear_tables(self.ds)

    def test_append_writes_file(self) -> None:
        print('\n[TestAppendRiskLogLineDirect] append creates line')
        p = risk_log_file_path_name(1, self.ds)
        if os.path.exists(p):
            os.remove(p)
        append_live_trade_risk_log_line(1, 'LINE_A', self.ds)
        with open(p, 'r', encoding='utf-8') as f:
            s = f.read()
        print(' content:', repr(s))
        self.assertEqual(s.strip(), 'LINE_A')


if __name__ == '__main__':
    unittest.main()
