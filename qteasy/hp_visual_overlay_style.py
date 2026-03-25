# coding=utf-8
# ======================================
# File:     hp_visual_overlay_style.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-03-24
# Desc:
#   HistoryPanel 双标的 overlay 主次视觉参量：Plotly 与 Matplotlib 共用，避免静态/动态分叉。
# ======================================

from __future__ import annotations

from typing import Literal, Optional, Tuple

# 与交互图 hp_visual_plotly 一致；导入方勿在业务中重复魔数。
HP_OVERLAY_SECONDARY_OPACITY: float = 0.45
HP_OVERLAY_PRIMARY_OPACITY: float = 1.0
HP_OVERLAY_PRIMARY_SCATTER_LINE_WIDTH: float = 1.35
HP_OVERLAY_SECONDARY_SCATTER_LINE_WIDTH: float = 0.65
HP_OVERLAY_PRIMARY_CANDLE_LINE_SCALE: float = 1.18
HP_OVERLAY_SECONDARY_CANDLE_LINE_SCALE: float = 0.82

OverlayVisualRole = Optional[Literal['primary', 'secondary']]


def overlay_trace_visual_bundle(
    is_overlay_group: bool,
    s_idx: int,
    active_share: int,
    *,
    base_candle_inc_w: float,
    base_candle_dec_w: float,
) -> Tuple[float, float, float, float]:
    """计算单条 Plotly trace 的 opacity 与线宽参量。

    Parameters
    ----------
    is_overlay_group : bool
        是否为双标的 overlay 组。
    s_idx : int
        当前 trace 对应的 share 下标。
    active_share : int
        当前主视觉 share 下标。
    base_candle_inc_w, base_candle_dec_w : float
        主题蜡烛 increasing / decreasing 线宽基准。

    Returns
    -------
    tuple
        ``(opacity, scatter_line_width, candle_inc_w, candle_dec_w)``；非 overlay 时 scatter 宽度为 ``1.0``。
    """
    if not is_overlay_group:
        return (
            HP_OVERLAY_PRIMARY_OPACITY,
            1.0,
            float(base_candle_inc_w),
            float(base_candle_dec_w),
        )
    primary = s_idx == active_share
    op = HP_OVERLAY_PRIMARY_OPACITY if primary else HP_OVERLAY_SECONDARY_OPACITY
    slw = HP_OVERLAY_PRIMARY_SCATTER_LINE_WIDTH if primary else HP_OVERLAY_SECONDARY_SCATTER_LINE_WIDTH
    k = HP_OVERLAY_PRIMARY_CANDLE_LINE_SCALE if primary else HP_OVERLAY_SECONDARY_CANDLE_LINE_SCALE
    inc = max(0.35, float(base_candle_inc_w) * k)
    dec = max(0.35, float(base_candle_dec_w) * k)
    return op, slw, inc, dec


def mpl_overlay_candle_strokes(
    share_idx: int,
    active_share: int,
    *,
    wick_lw: float,
    body_edge: float,
    doji_lw: float,
) -> Tuple[float, float, float]:
    """Matplotlib 蜡烛三类线宽，与 Plotly 主次蜡烛标尺一致。

    Parameters
    ----------
    share_idx : int
        当前绘制的 share 下标（左 0 / 右 1）。
    active_share : int
        主视觉 share（静态图固定为 0）。
    wick_lw, body_edge, doji_lw : float
        主题给出的影线、实体边、十字星线宽。

    Returns
    -------
    tuple
        ``(wick, body_edge, doji)`` 已按主次比例缩放。
    """
    k = (
        HP_OVERLAY_PRIMARY_CANDLE_LINE_SCALE
        if share_idx == active_share
        else HP_OVERLAY_SECONDARY_CANDLE_LINE_SCALE
    )
    return (
        max(0.35, float(wick_lw) * k),
        max(0.35, float(body_edge) * k),
        max(0.35, float(doji_lw) * k),
    )


def mpl_overlay_plot_line_width(share_idx: int, active_share: int) -> float:
    """Matplotlib 折线线宽，与 Plotly Scatter 主次一致。

    Parameters
    ----------
    share_idx : int
        当前 share 下标。
    active_share : int
        主视觉 share 下标。

    Returns
    -------
    float
        线宽（pt），取自 ``HP_OVERLAY_*_SCATTER_LINE_WIDTH``。
    """
    return (
        HP_OVERLAY_PRIMARY_SCATTER_LINE_WIDTH
        if share_idx == active_share
        else HP_OVERLAY_SECONDARY_SCATTER_LINE_WIDTH
    )


def overlay_visual_role_to_share_idx(role: Literal['primary', 'secondary']) -> int:
    """静态 overlay 左主右次：角色到 share 下标。

    Parameters
    ----------
    role : {'primary', 'secondary'}

    Returns
    -------
    int
        ``0`` 或 ``1``。
    """
    return 0 if role == 'primary' else 1
