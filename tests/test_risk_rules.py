# coding=utf-8
# ======================================
# File: test_risk_rules.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
# Unittest for qteasy.risk live-trade risk rule engine (pure logic, no IO).
# ======================================

from __future__ import annotations

import unittest
from datetime import date, datetime, time
from typing import List

import numpy as np

from qteasy.risk import (
    AccountSnapshot,
    DailyTurnoverCapRule,
    MaxOrderNotionalRule,
    MaxOrderQtyRule,
    OrderIntent,
    PositionQtyCapRule,
    RiskDecision,
    RiskManager,
    SymbolWhitelistRule,
    TradingSessionRule,
    order_notional,
)


def _snap(
    *,
    as_of: datetime,
    positions: dict | None = None,
    daily_turnover_used: float = 0.0,
    trading_date: date | None = None,
) -> AccountSnapshot:
    return AccountSnapshot(
        as_of=as_of,
        positions=positions or {},
        daily_turnover_used=daily_turnover_used,
        trading_date=trading_date,
    )


def _order(
    *,
    symbol: str = '000001',
    position: str = 'long',
    direction: str = 'buy',
    order_type: str = 'limit',
    qty: float = 100.0,
    price: float = 10.0,
    notional_override: float | None = None,
) -> OrderIntent:
    return OrderIntent(
        symbol=symbol,
        position=position,
        direction=direction,
        order_type=order_type,
        qty=qty,
        price=price,
        notional_override=notional_override,
    )


class CountingRule:
    """测试用规则：记录 evaluate 调用顺序，可配置放行/拒绝。"""

    def __init__(self, rule_id: str, call_log: List[str], allow: bool) -> None:
        self.rule_id = rule_id
        self._call_log = call_log
        self._allow = allow

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        self._call_log.append(self.rule_id)
        if self._allow:
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        return RiskDecision(allowed=False, reason='blocked by counting rule', rule_id=self.rule_id)


class TestRiskDecisionAndManager(unittest.TestCase):
    """RiskManager 空链与 RiskDecision 形状。"""

    def test_risk_manager_empty_rules_allows(self) -> None:
        print('\n[TestRiskDecisionAndManager] empty RiskManager allows any order')
        mgr = RiskManager(())
        snap = _snap(as_of=datetime(2024, 1, 2, 10, 0, 0))
        order = _order()
        decision = mgr.evaluate(snap, order)
        print(' decision:', decision)
        self.assertIsInstance(decision, RiskDecision)
        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.reason)
        self.assertIsNone(decision.rule_id)

    def test_risk_manager_empty_rules_decision_shape(self) -> None:
        print('\n[TestRiskDecisionAndManager] empty manager returns RiskDecision shape')
        mgr = RiskManager([])
        d = mgr.evaluate(_snap(as_of=datetime(2024, 1, 2, 9, 31)), _order())
        print(' decision:', d)
        self.assertIsInstance(d, RiskDecision)
        self.assertIsNone(d.rule_id)


class TestTradingSessionRule(unittest.TestCase):
    """TradingSessionRule 功能与半开区间边界。"""

    _windows = (
        (time(9, 30), time(11, 30)),
        (time(13, 0), time(15, 0)),
    )

    def test_session_allows_inside_morning_window(self) -> None:
        print('\n[TestTradingSessionRule] 10:00 inside morning window')
        rule = TradingSessionRule('session', self._windows)
        snap = _snap(as_of=datetime(2024, 1, 2, 10, 0, 0))
        order = _order()
        d = rule.evaluate(snap, order)
        print(' snapshot as_of:', snap.as_of, ' decision:', d)
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, 'session')

    def test_session_allows_inside_afternoon_window(self) -> None:
        print('\n[TestTradingSessionRule] 14:00 inside afternoon window')
        rule = TradingSessionRule('session', self._windows)
        snap = _snap(as_of=datetime(2024, 1, 2, 14, 0, 0))
        d = rule.evaluate(snap, _order())
        print(' decision:', d)
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, 'session')

    def test_session_rejects_lunch(self) -> None:
        print('\n[TestTradingSessionRule] 12:00 lunch rejected')
        rule = TradingSessionRule('session', self._windows)
        snap = _snap(as_of=datetime(2024, 1, 2, 12, 0, 0))
        d = rule.evaluate(snap, _order())
        print(' decision:', d)
        self.assertFalse(d.allowed)
        self.assertIsNotNone(d.reason)
        self.assertNotEqual(len(d.reason.strip()), 0)
        self.assertIn('session', d.reason.lower())
        self.assertTrue(d.reason.isascii())

    def test_session_boundary_start_inclusive(self) -> None:
        print('\n[TestTradingSessionRule] 09:30 start inclusive')
        rule = TradingSessionRule('session', self._windows)
        snap = _snap(as_of=datetime(2024, 1, 2, 9, 30, 0))
        d = rule.evaluate(snap, _order())
        print(' decision:', d)
        self.assertTrue(d.allowed)

    def test_session_boundary_end_exclusive(self) -> None:
        print('\n[TestTradingSessionRule] 11:30 end exclusive')
        rule = TradingSessionRule('session', self._windows)
        snap = _snap(as_of=datetime(2024, 1, 2, 11, 30, 0))
        d = rule.evaluate(snap, _order())
        print(' decision:', d)
        self.assertFalse(d.allowed)

    def test_session_no_windows_config_rejects(self) -> None:
        print('\n[TestTradingSessionRule] empty windows reject')
        rule = TradingSessionRule('session', (), reject_when_no_windows=True)
        snap = _snap(as_of=datetime(2024, 1, 2, 10, 0, 0))
        d = rule.evaluate(snap, _order())
        print(' decision:', d)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, 'session')
        self.assertIn('window', d.reason.lower())


class TestSymbolWhitelistRule(unittest.TestCase):
    """SymbolWhitelistRule。"""

    def test_whitelist_allows_listed_symbol(self) -> None:
        print('\n[TestSymbolWhitelistRule] listed symbol allowed')
        rule = SymbolWhitelistRule('wl', frozenset({'000001'}))
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(symbol='000001'))
        print(' decision:', d)
        self.assertTrue(d.allowed)

    def test_whitelist_rejects_unlisted_symbol(self) -> None:
        print('\n[TestSymbolWhitelistRule] unlisted symbol rejected')
        rule = SymbolWhitelistRule('wl', frozenset({'000001'}))
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(symbol='000002'))
        print(' decision:', d)
        self.assertFalse(d.allowed)
        self.assertIn('000002', d.reason)

    def test_whitelist_empty_set_rejects_any(self) -> None:
        print('\n[TestSymbolWhitelistRule] empty whitelist rejects')
        rule = SymbolWhitelistRule('wl', frozenset())
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(symbol='000001'))
        print(' decision:', d)
        self.assertFalse(d.allowed)

    def test_whitelist_strict_string_equality(self) -> None:
        print('\n[TestSymbolWhitelistRule] no strip on symbol')
        rule = SymbolWhitelistRule('wl', frozenset({'000001'}))
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(symbol='000001 '))
        print(' decision:', d)
        self.assertFalse(d.allowed)


class TestMaxOrderQtyRule(unittest.TestCase):
    """MaxOrderQtyRule。"""

    def test_max_qty_rejects_over_limit(self) -> None:
        print('\n[TestMaxOrderQtyRule] qty over max')
        rule = MaxOrderQtyRule('max_qty', 500.0)
        order = _order(qty=501.0)
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), order)
        print(' order.qty:', order.qty, ' max:', 500, ' decision:', d)
        self.assertGreater(order.qty, 500.0)
        self.assertFalse(d.allowed)

    def test_max_qty_allows_equal_limit(self) -> None:
        print('\n[TestMaxOrderQtyRule] qty equals max')
        rule = MaxOrderQtyRule('max_qty', 500.0)
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(qty=500.0))
        print(' decision:', d)
        self.assertTrue(d.allowed)

    def test_max_qty_uses_abs_for_sell(self) -> None:
        print('\n[TestMaxOrderQtyRule] negative qty uses abs')
        rule = MaxOrderQtyRule('max_qty', 500.0)
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(qty=-500.0, direction='sell'))
        print(' decision:', d)
        self.assertTrue(d.allowed)
        d2 = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order(qty=-501.0, direction='sell'))
        print(' decision over:', d2)
        self.assertFalse(d2.allowed)


class TestMaxOrderNotionalRule(unittest.TestCase):
    """MaxOrderNotionalRule。"""

    def test_max_notional_rejects_over_limit(self) -> None:
        print('\n[TestMaxOrderNotionalRule] notional over cap')
        rule = MaxOrderNotionalRule('max_notional', 999.0)
        order = _order(qty=100.0, price=10.0)
        n = order_notional(order)
        print(' notional:', n, ' cap:', 999.0)
        self.assertEqual(n, 1000.0)
        self.assertGreater(n, 999.0)
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), order)
        print(' decision:', d)
        self.assertFalse(d.allowed)

    def test_max_notional_allows_equal_limit(self) -> None:
        print('\n[TestMaxOrderNotionalRule] notional equals cap')
        rule = MaxOrderNotionalRule('max_notional', 1000.0)
        order = _order(qty=100.0, price=10.0)
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), order)
        print(' notional:', order_notional(order), ' decision:', d)
        self.assertTrue(d.allowed)

    def test_max_notional_rejects_nan_price(self) -> None:
        print('\n[TestMaxOrderNotionalRule] NaN price rejected')
        rule = MaxOrderNotionalRule('max_notional', 1e9)
        order = _order(qty=100.0, price=float('nan'))
        n = order_notional(order)
        print(' notional is nan:', np.isnan(n))
        self.assertTrue(np.isnan(n))
        d = rule.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), order)
        print(' decision:', d)
        self.assertFalse(d.allowed)


class TestDailyTurnoverCapRule(unittest.TestCase):
    """DailyTurnoverCapRule。"""

    def test_daily_turnover_rejects_when_exceeds_cap(self) -> None:
        print('\n[TestDailyTurnoverCapRule] used + order exceeds cap')
        rule = DailyTurnoverCapRule('daily', 1000.0)
        snap = _snap(as_of=datetime(2024, 1, 2, 10, 0), daily_turnover_used=900.0)
        order = _order(qty=20.0, price=10.0)
        n = order_notional(order)
        print(' used:', 900.0, ' n:', n, ' cap:', 1000.0, ' sum:', 900.0 + n)
        self.assertGreater(900.0 + n, 1000.0)
        d = rule.evaluate(snap, order)
        print(' decision:', d)
        self.assertFalse(d.allowed)

    def test_daily_turnover_allows_exact_remaining(self) -> None:
        print('\n[TestDailyTurnoverCapRule] exact remaining')
        rule = DailyTurnoverCapRule('daily', 1000.0)
        snap = _snap(as_of=datetime(2024, 1, 2, 10, 0), daily_turnover_used=900.0)
        order = _order(qty=10.0, price=10.0)
        d = rule.evaluate(snap, order)
        print(' sum:', 900.0 + order_notional(order), ' decision:', d)
        self.assertTrue(d.allowed)

    def test_daily_turnover_rejects_one_unit_over(self) -> None:
        print('\n[TestDailyTurnoverCapRule] float boundary over cap')
        rule = DailyTurnoverCapRule('daily', 1000.0)
        snap = _snap(as_of=datetime(2024, 1, 2, 10, 0), daily_turnover_used=999.9)
        order = _order(qty=0.02, price=10.0)
        n = order_notional(order)
        print(' used+n:', 999.9 + n)
        self.assertAlmostEqual(999.9 + n, 1000.1, places=10)
        d = rule.evaluate(snap, order)
        print(' decision:', d)
        self.assertFalse(d.allowed)


class TestPositionQtyCapRule(unittest.TestCase):
    """PositionQtyCapRule long 侧。"""

    def test_long_cap_rejects_buy_that_exceeds_cap(self) -> None:
        print('\n[TestPositionQtyCapRule] buy exceeds long cap')
        rule = PositionQtyCapRule('pos', per_symbol_max_long={'000001': 1000.0})
        snap = _snap(
            as_of=datetime(2024, 1, 2, 10, 0),
            positions={('000001', 'long'): 900.0},
        )
        order = _order(symbol='000001', direction='buy', position='long', qty=150.0)
        post = 900.0 + 150.0
        print(' post-trade long:', post, ' cap:', 1000.0)
        self.assertGreater(post, 1000.0)
        d = rule.evaluate(snap, order)
        print(' decision:', d)
        self.assertFalse(d.allowed)

    def test_long_cap_allows_buy_within_cap(self) -> None:
        print('\n[TestPositionQtyCapRule] buy within cap')
        rule = PositionQtyCapRule('pos', per_symbol_max_long={'000001': 1000.0})
        snap = _snap(
            as_of=datetime(2024, 1, 2, 10, 0),
            positions={('000001', 'long'): 900.0},
        )
        order = _order(symbol='000001', direction='buy', position='long', qty=100.0)
        d = rule.evaluate(snap, order)
        print(' post:', 900.0 + 100.0, ' decision:', d)
        self.assertTrue(d.allowed)

    def test_long_cap_ignores_sell_orders(self) -> None:
        print('\n[TestPositionQtyCapRule] sell ignored for long cap')
        rule = PositionQtyCapRule('pos', per_symbol_max_long={'000001': 1000.0})
        snap = _snap(
            as_of=datetime(2024, 1, 2, 10, 0),
            positions={('000001', 'long'): 1000.0},
        )
        order = _order(symbol='000001', direction='sell', position='long', qty=100.0)
        d = rule.evaluate(snap, order)
        print(' decision:', d)
        self.assertTrue(d.allowed)

    def test_long_cap_allows_equal_post_trade(self) -> None:
        print('\n[TestPositionQtyCapRule] post-trade equals cap')
        rule = PositionQtyCapRule('pos', per_symbol_max_long={'000001': 1000.0})
        snap = _snap(
            as_of=datetime(2024, 1, 2, 10, 0),
            positions={('000001', 'long'): 500.0},
        )
        order = _order(symbol='000001', direction='buy', position='long', qty=500.0)
        d = rule.evaluate(snap, order)
        print(' post:', 500.0 + 500.0, ' decision:', d)
        self.assertTrue(d.allowed)


class TestRiskManagerOrdering(unittest.TestCase):
    """多规则短路与顺序。"""

    def test_manager_short_circuits_on_first_reject(self) -> None:
        print('\n[TestRiskManagerOrdering] short-circuit after first reject')
        log: List[str] = []
        r1 = CountingRule('pass_rule', log, allow=True)
        r2 = CountingRule('fail_rule', log, allow=False)
        r3 = CountingRule('third', log, allow=True)
        mgr = RiskManager((r1, r2, r3))
        d = mgr.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order())
        print(' call_log:', log, ' decision:', d)
        self.assertEqual(log, ['pass_rule', 'fail_rule'])
        self.assertEqual(d.rule_id, 'fail_rule')
        self.assertFalse(d.allowed)
        self.assertNotIn('third', log)

    def test_manager_order_stable_different_first_fail(self) -> None:
        print('\n[TestRiskManagerOrdering] order swap changes first failure')
        log1: List[str] = []
        a = CountingRule('A', log1, allow=False)
        b = CountingRule('B', log1, allow=False)
        d1 = RiskManager((a, b)).evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order())
        log2: List[str] = []
        a2 = CountingRule('A', log2, allow=False)
        b2 = CountingRule('B', log2, allow=False)
        d2 = RiskManager((b2, a2)).evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order())
        print(' first order decision rule_id:', d1.rule_id, ' second:', d2.rule_id)
        self.assertEqual(d1.rule_id, 'A')
        self.assertEqual(d2.rule_id, 'B')
        self.assertEqual(log1, ['A'])
        self.assertEqual(log2, ['B'])

    def test_manager_all_rules_pass(self) -> None:
        print('\n[TestRiskManagerOrdering] all rules pass')
        log: List[str] = []
        mgr = RiskManager(
            (
                CountingRule('r1', log, allow=True),
                CountingRule('r2', log, allow=True),
            )
        )
        d = mgr.evaluate(_snap(as_of=datetime(2024, 1, 2, 10, 0)), _order())
        print(' log:', log, ' decision:', d)
        self.assertTrue(d.allowed)
        self.assertEqual(log, ['r1', 'r2'])


if __name__ == '__main__':
    unittest.main()
