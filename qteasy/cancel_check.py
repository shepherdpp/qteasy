# coding=utf-8
# ======================================
# File: cancel_check.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-09-27
# Desc:
# 协作式取消：循环在下一步边界查询 callable。
# ======================================

"""协作式取消。默认不取消；调用方在 ``qt.run`` / refill 期间绑定检查函数。"""

from __future__ import annotations

import contextvars
from typing import Callable, Optional

CancelCheck = Callable[[], bool]

_CANCEL: contextvars.ContextVar[Optional[CancelCheck]] = contextvars.ContextVar(
    "qteasy_cancel_check",
    default=None,
)


class RunCancelled(Exception):
    """循环在下一步边界退出。已经进入 numba 的那一步会返回。"""


def bind_cancel_check(fn: Optional[CancelCheck]):
    """绑定当前上下文的取消检查。返回 token，供 ``reset_cancel_check`` 使用。"""

    return _CANCEL.set(fn)


def reset_cancel_check(token) -> None:
    """恢复 ``bind_cancel_check`` 之前的检查函数。"""

    _CANCEL.reset(token)


def should_cancel(explicit: Optional[CancelCheck] = None) -> bool:
    """当前步之后是否应停止。

    Parameters
    ----------
    explicit : callable, optional
        本次调用专用的检查。缺省时读上下文里绑定的函数。

    Returns
    -------
    bool
        为真时调用方应退出循环。
    """

    fn = explicit if explicit is not None else _CANCEL.get()
    if fn is None:
        return False
    return bool(fn())
