# coding=utf-8
# ======================================
# File: risk.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
#   实盘/模拟盘下单前风控规则纯逻辑引擎（无 IO），供 Trader 侧集成。
# ======================================

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Collection, Mapping, Protocol, Sequence, runtime_checkable

__all__ = [
    'AccountSnapshot',
    'DailyTurnoverCapRule',
    'MaxOrderNotionalRule',
    'MaxOrderQtyRule',
    'OrderIntent',
    'PositionQtyCapRule',
    'RiskDecision',
    'RiskManager',
    'RiskRule',
    'SymbolWhitelistRule',
    'TradingSessionRule',
    'order_notional',
]


@dataclass(frozen=True)
class OrderIntent:
    """待评估的一笔下单意图（与 trade_io 字段语义对齐，非同一 dict 类型）。

    Parameters
    ----------
    symbol : str
        标的代码。
    position : str
        持仓方向，如 ``long`` / ``short``。
    direction : str
        交易方向，如 ``buy`` / ``sell``。
    order_type : str
        订单类型，如 ``market`` / ``limit``。
    qty : float
        数量。
    price : float
        价格；市价意图仍应填入用于风控的名义价或最近价。
    notional_override : float or None, optional
        若非空则 ``order_notional`` 直接使用该值，否则使用 ``abs(qty)*price``。
    """

    symbol: str
    position: str
    direction: str
    order_type: str
    qty: float
    price: float
    notional_override: float | None = None


@dataclass(frozen=True)
class AccountSnapshot:
    """评估时刻的账户只读快照（由调用方从账本/行情组装）。

    Parameters
    ----------
    as_of : datetime
        评估时刻（naive 本地时间即可，与时段规则一致）。
    positions : Mapping[tuple[str, str], float]
        键为 ``(symbol, position)``，值为持仓数量。
    daily_turnover_used : float, optional
        当日已计入的成交额（不含本笔）。
    trading_date : date or None, optional
        交易日；为空时规则实现可使用 ``as_of.date()``。
    """

    as_of: datetime
    positions: Mapping[tuple[str, str], float]
    daily_turnover_used: float = 0.0
    trading_date: date | None = None


@dataclass(frozen=True)
class RiskDecision:
    """单条规则的评估结果；拒绝时 ``reason`` 为面向用户的英文说明。

    Parameters
    ----------
    allowed : bool
        是否允许通过本规则。
    reason : str or None
        拒绝原因；允许时为 ``None``。
    rule_id : str or None
        触发决策的规则标识；``RiskManager`` 全链通过时可为 ``None``。
    """

    allowed: bool
    reason: str | None
    rule_id: str | None


@runtime_checkable
class RiskRule(Protocol):
    """风控规则协议：实现 ``rule_id`` 与 ``evaluate`` 即可接入 ``RiskManager``。"""

    rule_id: str

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        ...


def order_notional(order: OrderIntent) -> float:
    """计算本笔意图的成交额名义（用于限额与日累计）。

    若 ``notional_override`` 非空则直接返回该值（可正可负，由调用方约定）；
    否则返回 ``abs(order.qty) * order.price``。

    Parameters
    ----------
    order : OrderIntent
        下单意图。

    Returns
    -------
    float
        名义金额；当价格为 NaN 时返回 NaN。

    Examples
    --------
    >>> from datetime import datetime
    >>> o = OrderIntent('000001', 'long', 'buy', 'limit', 100.0, 10.5)
    >>> order_notional(o)
    1050.0
    """
    if order.notional_override is not None:
        return float(order.notional_override)
    return abs(float(order.qty)) * float(order.price)


def _in_session(t: time, windows: Sequence[tuple[time, time]]) -> bool:
    for start, end in windows:
        if start <= t < end:
            return True
    return False


class TradingSessionRule:
    """仅允许落在给定半开时间窗内的下单（使用 ``snapshot.as_of.time()``）。"""

    def __init__(
        self,
        rule_id: str,
        windows: Sequence[tuple[time, time]],
        *,
        reject_when_no_windows: bool = True,
    ) -> None:
        """构造时段规则。

        Parameters
        ----------
        rule_id : str
            规则标识，写入 ``RiskDecision.rule_id``。
        windows : Sequence[tuple[time, time]]
            允许交易半开区间序列 ``[start, end)``。
        reject_when_no_windows : bool, optional
            当 ``windows`` 为空时若为 ``True`` 则一律拒绝；若为 ``False`` 则一律放行。
        """
        self.rule_id = rule_id
        self._windows = tuple(windows)
        self._reject_when_no_windows = reject_when_no_windows

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """判断 ``snapshot.as_of`` 是否落在任一时间窗内。

        Parameters
        ----------
        snapshot : AccountSnapshot
            含评估时刻的快照。
        order : OrderIntent
            下单意图（本规则不读字段，为接口统一而保留）。

        Returns
        -------
        RiskDecision
            在窗内则 ``allowed=True``，否则 ``allowed=False`` 且 ``reason`` 为英文。
        """
        if not self._windows:
            if self._reject_when_no_windows:
                return RiskDecision(
                    allowed=False,
                    reason='Outside trading session: no session windows configured.',
                    rule_id=self.rule_id,
                )
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        t = snapshot.as_of.time()
        if _in_session(t, self._windows):
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        return RiskDecision(
            allowed=False,
            reason=f'Outside trading session at {t.isoformat(timespec="seconds")}.',
            rule_id=self.rule_id,
        )


class SymbolWhitelistRule:
    """仅允许白名单内标的；空集合表示不允许任何标的（需关闭本规则请勿注册）。"""

    def __init__(self, rule_id: str, allowed_symbols: Collection[str]) -> None:
        """构造白名单规则。

        Parameters
        ----------
        rule_id : str
            规则标识。
        allowed_symbols : Collection[str]
            允许交易的标的代码集合；字符串严格相等匹配，不做 strip。
        """
        self.rule_id = rule_id
        self._allowed = frozenset(allowed_symbols)

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """判断 ``order.symbol`` 是否在白名单内。

        Parameters
        ----------
        snapshot : AccountSnapshot
            账户快照（本规则不使用）。
        order : OrderIntent
            下单意图。

        Returns
        -------
        RiskDecision
            在白名单内则放行，否则拒绝并给出英文原因。
        """
        if order.symbol in self._allowed:
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        return RiskDecision(
            allowed=False,
            reason=f'Symbol {order.symbol!r} is not in the tradable whitelist.',
            rule_id=self.rule_id,
        )


class MaxOrderQtyRule:
    """单笔订单数量上限（按 ``abs(qty)``）。"""

    def __init__(self, rule_id: str, max_qty: float) -> None:
        """构造数量上限规则。

        Parameters
        ----------
        rule_id : str
            规则标识。
        max_qty : float
            允许的最大 ``abs(qty)``。
        """
        self.rule_id = rule_id
        self._max_qty = float(max_qty)

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """比较 ``abs(order.qty)`` 与上限。

        Parameters
        ----------
        snapshot : AccountSnapshot
            账户快照（本规则不使用）。
        order : OrderIntent
            下单意图。

        Returns
        -------
        RiskDecision
            数量合法则放行；``qty`` 为 NaN 时拒绝。
        """
        q = abs(float(order.qty))
        if math.isnan(q):
            return RiskDecision(
                allowed=False,
                reason='Order quantity is NaN.',
                rule_id=self.rule_id,
            )
        if q <= self._max_qty:
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        return RiskDecision(
            allowed=False,
            reason=f'Order qty {q} exceeds max_order_qty {self._max_qty}.',
            rule_id=self.rule_id,
        )


class MaxOrderNotionalRule:
    """单笔名义金额上限（默认 ``abs(qty)*price``）；价格为 NaN 时拒绝。"""

    def __init__(self, rule_id: str, max_notional: float) -> None:
        """构造单笔名义金额上限规则。

        Parameters
        ----------
        rule_id : str
            规则标识。
        max_notional : float
            允许的最大名义金额。
        """
        self.rule_id = rule_id
        self._max_notional = float(max_notional)

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """比较 ``order_notional(order)`` 与上限。

        Parameters
        ----------
        snapshot : AccountSnapshot
            账户快照（本规则不使用）。
        order : OrderIntent
            下单意图。

        Returns
        -------
        RiskDecision
            名义为 NaN 或超过上限则拒绝。
        """
        n = order_notional(order)
        if math.isnan(n):
            return RiskDecision(
                allowed=False,
                reason='Order notional is NaN (invalid price or override).',
                rule_id=self.rule_id,
            )
        if n <= self._max_notional:
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        return RiskDecision(
            allowed=False,
            reason=f'Order notional {n} exceeds max_order_notional {self._max_notional}.',
            rule_id=self.rule_id,
        )


class DailyTurnoverCapRule:
    """日累计成交额上限：``snapshot.daily_turnover_used + 本笔名义 <= daily_cap``。"""

    def __init__(self, rule_id: str, daily_cap: float) -> None:
        """构造日成交额上限规则。

        Parameters
        ----------
        rule_id : str
            规则标识。
        daily_cap : float
            当日允许的最大累计名义成交额。
        """
        self.rule_id = rule_id
        self._daily_cap = float(daily_cap)

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """判断本笔是否会使 ``daily_turnover_used + notional`` 超过 ``daily_cap``。

        Parameters
        ----------
        snapshot : AccountSnapshot
            含 ``daily_turnover_used`` 的快照。
        order : OrderIntent
            下单意图。

        Returns
        -------
        RiskDecision
            不超限则放行；本笔名义为 NaN 时拒绝。
        """
        n = order_notional(order)
        if math.isnan(n):
            return RiskDecision(
                allowed=False,
                reason='Order notional is NaN; cannot evaluate daily turnover cap.',
                rule_id=self.rule_id,
            )
        used = float(snapshot.daily_turnover_used)
        if used + n <= self._daily_cap:
            return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
        return RiskDecision(
            allowed=False,
            reason=(
                f'Daily turnover would exceed cap: used={used}, order_notional={n}, '
                f'cap={self._daily_cap}.'
            ),
            rule_id=self.rule_id,
        )


class PositionQtyCapRule:
    """按标的限制 long/short 持仓数量：仅拦截会增加对应腿持仓的 buy。"""

    def __init__(
        self,
        rule_id: str,
        per_symbol_max_long: Mapping[str, float] | None = None,
        per_symbol_max_short: Mapping[str, float] | None = None,
    ) -> None:
        """构造持仓数量上限规则。

        Parameters
        ----------
        rule_id : str
            规则标识。
        per_symbol_max_long : Mapping[str, float] or None, optional
            各标的多头持仓上限；未出现的标的不做多头侧拦截。
        per_symbol_max_short : Mapping[str, float] or None, optional
            各标的空头持仓上限；逻辑与多头对称，仅对 ``buy+short`` 增仓校验。
        """
        self.rule_id = rule_id
        self._max_long = dict(per_symbol_max_long) if per_symbol_max_long else {}
        self._max_short = dict(per_symbol_max_short) if per_symbol_max_short else {}

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """对 ``buy+long`` / ``buy+short`` 做增仓后数量与上限比较；卖出不拦截。

        Parameters
        ----------
        snapshot : AccountSnapshot
            含 ``positions`` 的快照。
        order : OrderIntent
            下单意图。

        Returns
        -------
        RiskDecision
            增仓后仍不超过对应上限则放行；无该标的上限配置则放行。
        """
        sym = order.symbol
        if order.direction == 'buy' and order.position == 'long':
            if sym not in self._max_long:
                return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
            cap = float(self._max_long[sym])
            cur = float(snapshot.positions.get((sym, 'long'), 0.0))
            post = cur + float(order.qty)
            if post <= cap:
                return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
            return RiskDecision(
                allowed=False,
                reason=(
                    f'Long position for {sym!r} would exceed cap: '
                    f'current={cur}, buy_qty={order.qty}, cap={cap}.'
                ),
                rule_id=self.rule_id,
            )
        if order.direction == 'buy' and order.position == 'short':
            if sym not in self._max_short:
                return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
            cap = float(self._max_short[sym])
            cur = float(snapshot.positions.get((sym, 'short'), 0.0))
            post = cur + float(order.qty)
            if post <= cap:
                return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)
            return RiskDecision(
                allowed=False,
                reason=(
                    f'Short position for {sym!r} would exceed cap: '
                    f'current={cur}, buy_qty={order.qty}, cap={cap}.'
                ),
                rule_id=self.rule_id,
            )
        return RiskDecision(allowed=True, reason=None, rule_id=self.rule_id)


class RiskManager:
    """按注册顺序评估规则链，首个 ``allowed=False`` 的结果立即返回。"""

    def __init__(self, rules: Sequence[RiskRule]) -> None:
        """构造风控管理器。

        Parameters
        ----------
        rules : Sequence[RiskRule]
            有序规则列表；先注册先执行。
        """
        self._rules = tuple(rules)

    def evaluate(self, snapshot: AccountSnapshot, order: OrderIntent) -> RiskDecision:
        """依次调用规则直至出现拒绝或全部通过。

        Parameters
        ----------
        snapshot : AccountSnapshot
            账户快照。
        order : OrderIntent
            下单意图。

        Returns
        -------
        RiskDecision
            若规则序列为空，返回 ``allowed=True`` 且 ``rule_id=None``；
            否则返回首个拒绝决策，或全通过时 ``allowed=True``、``rule_id=None``。
        """
        for rule in self._rules:
            decision = rule.evaluate(snapshot, order)
            if not decision.allowed:
                return decision
        return RiskDecision(allowed=True, reason=None, rule_id=None)
