# coding=utf-8
# ======================================
# File:     trade_io.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-04-12
# Desc:
#   实盘/模拟盘交易订单与原始成交结果的 dict 契约与校验，供 Trader、Broker 共用。
# ======================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Final, Mapping, TypedDict

import numpy as np
import pandas as pd

__all__ = [
    'TradeOrderDict',
    'RawTradeResultDict',
    'TRADE_ORDER_STATUSES',
    'RAW_RESULT_STATUSES',
    'validate_trade_order',
    'validate_raw_trade_result',
]

_TRADE_ORDER_REQUIRED_KEYS: Final[tuple[str, ...]] = (
    'order_id',
    'pos_id',
    'direction',
    'order_type',
    'qty',
    'price',
    'status',
    'submitted_time',
)

_RAW_TRADE_RESULT_REQUIRED_KEYS: Final[tuple[str, ...]] = (
    'order_id',
    'filled_qty',
    'price',
    'transaction_fee',
    'execution_time',
    'canceled_qty',
    'delivery_amount',
    'delivery_status',
)

TRADE_ORDER_STATUSES: Final[frozenset[str]] = frozenset({'submitted'})
RAW_RESULT_STATUSES: Final[frozenset[str]] = frozenset({'filled', 'partial-filled', 'canceled'})


class TradeOrderDict(TypedDict, total=False):
    """进入 Broker 队列前的订单 dict 形状说明（校验以 validate_trade_order 为准）。"""

    order_id: int
    pos_id: int
    direction: str
    order_type: str
    qty: float
    price: float
    status: str
    submitted_time: str | None
    symbol: str
    position: str


class RawTradeResultDict(TypedDict, total=False):
    """进入 result_queue / write_trade_result 前的原始成交 dict 形状说明。"""

    order_id: int
    filled_qty: float
    price: float
    transaction_fee: float
    execution_time: str
    canceled_qty: float
    delivery_amount: float
    delivery_status: str
    broker_order_id: str
    status: str
    raw_status: str


def _is_int_like(x: Any) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, bool)


def _is_real_scalar(x: Any) -> bool:
    if isinstance(x, bool):
        return False
    if isinstance(x, (int, float, np.integer, np.floating)):
        return True
    return False


def _fmt_ctx(context: str, msg: str) -> str:
    return f'{context}: {msg}'


def validate_trade_order(order: Mapping[str, Any], *, context: str = 'trade_order') -> None:
    """校验进入 Broker 处理链之前的交易订单 dict 形状与取值。

    必选键与取值需与 ``record_trade_order`` / ``submit_order`` 成功后的语义一致；
    ``symbol`` / ``position`` 为可选扩展（P6），若出现则校验类型与取值。

    Parameters
    ----------
    order : Mapping[str, Any]
        待校验的订单 dict。
    context : str, optional
        异常消息前缀，便于定位调用方。

    Returns
    -------
    None

    Raises
    ------
    TypeError
        非 dict 或字段类型不合法。
    ValueError
        缺键、枚举或数值范围不合法。

    Examples
    --------
    >>> od = {'order_id': 1, 'pos_id': 1, 'direction': 'buy', 'order_type': 'limit',
    ...       'qty': 100, 'price': 10.0, 'status': 'submitted', 'submitted_time': None}
    >>> validate_trade_order(od)
    """
    if not isinstance(order, dict):
        raise TypeError(_fmt_ctx(context, f'trade order must be a dict, got {type(order)!r}'))

    for key in _TRADE_ORDER_REQUIRED_KEYS:
        if key not in order:
            raise ValueError(_fmt_ctx(context, f'missing required key {key!r}'))

    if not _is_int_like(order['order_id']) or int(order['order_id']) <= 0:
        raise ValueError(
            _fmt_ctx(context, f'order_id must be a positive int, got {order["order_id"]!r}'),
        )
    if not _is_int_like(order['pos_id']) or int(order['pos_id']) <= 0:
        raise ValueError(
            _fmt_ctx(context, f'pos_id must be a positive int, got {order["pos_id"]!r}'),
        )

    direction = order['direction']
    if not isinstance(direction, str):
        raise TypeError(_fmt_ctx(context, f'direction must be str, got {type(direction)!r}'))
    if direction not in ('buy', 'sell'):
        raise ValueError(_fmt_ctx(context, f'direction must be buy or sell, got {direction!r}'))

    order_type = order['order_type']
    if not isinstance(order_type, str):
        raise TypeError(_fmt_ctx(context, f'order_type must be str, got {type(order_type)!r}'))
    if order_type not in ('market', 'limit'):
        raise ValueError(_fmt_ctx(context, f'order_type must be market or limit, got {order_type!r}'))

    qty = order['qty']
    if not _is_real_scalar(qty):
        raise TypeError(_fmt_ctx(context, f'qty must be a numeric scalar, got {type(qty)!r}'))
    if float(qty) <= 0:
        raise ValueError(_fmt_ctx(context, f'qty must be greater than 0, got {qty!r}'))

    price = order['price']
    if not _is_real_scalar(price):
        raise TypeError(_fmt_ctx(context, f'price must be a numeric scalar, got {type(price)!r}'))
    if float(price) <= 0:
        raise ValueError(_fmt_ctx(context, f'price must be greater than 0, got {price!r}'))

    status = order['status']
    if not isinstance(status, str):
        raise TypeError(_fmt_ctx(context, f'status must be str, got {type(status)!r}'))
    if status not in TRADE_ORDER_STATUSES:
        raise ValueError(
            _fmt_ctx(
                context,
                f'status must be one of {sorted(TRADE_ORDER_STATUSES)!r} for broker queue, got {status!r}',
            ),
        )

    st = order['submitted_time']
    if st is not None:
        if isinstance(st, (pd.Timestamp, datetime)):
            st_norm = pd.Timestamp(st).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(st, str):
            st_norm = st
        else:
            raise TypeError(_fmt_ctx(context, f'submitted_time must be str, datetime, Timestamp or None, got {type(st)!r}'))
        try:
            pd.to_datetime(st_norm).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as exc:
            raise ValueError(
                _fmt_ctx(context, f'submitted_time {st!r} is not a valid datetime ({exc})'),
            ) from exc

    if 'symbol' in order:
        sym = order['symbol']
        if not isinstance(sym, str) or not sym.strip():
            raise ValueError(_fmt_ctx(context, 'symbol must be a non-empty str when present'))
    if 'position' in order:
        pos = order['position']
        if not isinstance(pos, str):
            raise TypeError(_fmt_ctx(context, f'position must be str when present, got {type(pos)!r}'))
        if pos not in ('long', 'short'):
            raise ValueError(_fmt_ctx(context, f'position must be long or short when present, got {pos!r}'))


def validate_raw_trade_result(raw: Mapping[str, Any], *, context: str = 'raw_trade_result') -> None:
    """校验 Broker 放入 ``result_queue`` 的原始成交 dict，与 ``write_trade_result`` 约束对齐。

    ``broker_order_id`` / ``status`` / ``raw_status`` 为可选扩展（P6），若出现则校验。

    Parameters
    ----------
    raw : Mapping[str, Any]
        待校验的原始成交 dict。
    context : str, optional
        异常消息前缀。

    Returns
    -------
    None

    Raises
    ------
    TypeError
        非 mapping 或字段类型不合法。
    ValueError
        缺键、枚举或数值范围不合法。
    RuntimeError
        ``execution_time`` 无法解析为时间（与 ``write_trade_result`` 行为对齐）。

    Examples
    --------
    >>> raw = {'order_id': 1, 'filled_qty': 10.0, 'price': 5.0, 'transaction_fee': 0.1,
    ...        'execution_time': '2020-01-01 10:00:00', 'canceled_qty': 0.0,
    ...        'delivery_amount': 0.0, 'delivery_status': 'ND'}
    >>> validate_raw_trade_result(raw)
    """
    if not isinstance(raw, dict):
        raise TypeError(_fmt_ctx(context, f'raw_trade_result must be a dict, got {type(raw)!r}'))

    for key in _RAW_TRADE_RESULT_REQUIRED_KEYS:
        if key not in raw:
            raise ValueError(_fmt_ctx(context, f'missing required key {key!r}'))

    oid = raw['order_id']
    if not _is_int_like(oid) or int(oid) <= 0:
        raise ValueError(_fmt_ctx(context, f'order_id must be a positive int, got {oid!r}'))

    for name in ('filled_qty', 'price', 'transaction_fee', 'canceled_qty', 'delivery_amount'):
        val = raw[name]
        if not _is_real_scalar(val):
            raise TypeError(_fmt_ctx(context, f'{name} must be a numeric scalar, got {type(val)!r}'))
        if float(val) < 0 and name != 'delivery_amount':
            raise ValueError(_fmt_ctx(context, f'{name} must be >= 0, got {val!r}'))
    # delivery_amount 允许为负，与 write_trade_result 不对负值抛错一致

    ds = raw['delivery_status']
    if not isinstance(ds, str) or ds not in ('ND', 'DL'):
        raise ValueError(_fmt_ctx(context, f'delivery_status must be ND or DL, got {ds!r}'))

    et = raw['execution_time']
    if not isinstance(et, str):
        raise TypeError(_fmt_ctx(context, f'execution_time must be str, got {type(et)!r}'))
    try:
        pd.to_datetime(et).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as exc:
        raise RuntimeError(
            _fmt_ctx(context, f'Invalid execution_time {et!r}, can not be converted to datetime format ({exc})'),
        ) from exc

    if 'broker_order_id' in raw:
        bid = raw['broker_order_id']
        if not isinstance(bid, str) or not bid.strip():
            raise ValueError(_fmt_ctx(context, 'broker_order_id must be a non-empty str when present'))
    if 'status' in raw:
        st = raw['status']
        if not isinstance(st, str):
            raise TypeError(_fmt_ctx(context, f'status must be str when present, got {type(st)!r}'))
        if st not in RAW_RESULT_STATUSES:
            raise ValueError(
                _fmt_ctx(
                    context,
                    f'status must be one of {sorted(RAW_RESULT_STATUSES)!r} when present, got {st!r}',
                ),
            )
    if 'raw_status' in raw:
        rs = raw['raw_status']
        if not isinstance(rs, str):
            raise TypeError(_fmt_ctx(context, f'raw_status must be str when present, got {type(rs)!r}'))

