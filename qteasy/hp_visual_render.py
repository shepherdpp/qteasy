# coding=utf-8
# ======================================
# File:     hp_visual_render.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-03-13
# Desc:
#   HistoryPanel 可视化静态渲染层：根据规格片段（ChartSpecFragment）在 matplotlib 上绘制。
#   主题/样式使用内部默认，仅保留扩展接口。
# ======================================

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.axes import Axes
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False
    Figure = Any  # type: ignore[misc, assignment]
    Axes = Any  # type: ignore[misc, assignment]


def _resolve_highlight_condition(
    condition: Any,
    data_1d: np.ndarray,
    n: int,
) -> Optional[np.ndarray]:
    """将 condition 解析为长度为 n 的布尔数组。condition 可为 bool 数组、'max'/'min'。"""
    if condition is None:
        return None
    if isinstance(condition, str):
        if condition == 'max':
            idx = np.nanargmax(data_1d[:n]) if np.any(np.isfinite(data_1d[:n])) else None
            if idx is None:
                return None
            out = np.zeros(n, dtype=bool)
            out[idx] = True
            return out
        if condition == 'min':
            idx = np.nanargmin(data_1d[:n]) if np.any(np.isfinite(data_1d[:n])) else None
            if idx is None:
                return None
            out = np.zeros(n, dtype=bool)
            out[idx] = True
            return out
        return None
    arr = np.asarray(condition, dtype=bool).ravel()
    if len(arr) >= n:
        return arr[:n]
    return None


def _get_theme() -> Dict[str, Any]:
    """内部默认主题，与 qt.candle / InterCandle 风格一致；风格扩展接口预留。"""
    return {
        'figure_facecolor': (0.82, 0.83, 0.85),
        'axes_facecolor': (1, 1, 1),
        'grid_alpha': 0.3,
        'grid_linestyle': '-',
        'highlight_color': 'black',
        'line_color_up': 'red',
        'line_color_down': 'green',
        'line_color_neutral': '#3498db',
        'volume_color': '#95a5a6',
        'volume_color_up': 'red',
        'volume_color_down': 'green',
        'macd_hist_up': 'red',
        'macd_hist_down': 'green',
        'font_size': 10,
        'title_font_size': 12,
        'datetime_format': '%y/%m/%d',
        'xrotation': 0,
        'max_x_ticks': 12,
    }


def _format_x_label(ts: Any, fmt: str = '%y/%m/%d') -> str:  # noqa: ANN401
    """将时间戳格式化为 X 轴标签，默认 %y/%m/%d 与 qt.candle 一致。"""
    try:
        import pandas as pd
        return pd.Timestamp(ts).strftime(fmt)
    except Exception:
        s = str(ts)
        return s[:10] if len(s) > 10 else s


def _to_1d(arr: np.ndarray, share_idx: int = 0) -> np.ndarray:
    """取单 share 序列：若 shape 为 (n_share, n_time) 取 [share_idx, :]，否则 ravel。"""
    arr = np.asarray(arr, dtype=float)
    if arr.ndim == 2:
        return arr[share_idx, :]
    return np.ravel(arr)


def render_kline_spec(
    spec: Dict[str, Any],
    ax: Optional[Axes] = None,
    share_idx: int = 0,
    x_dates: Optional[Sequence] = None,
    show_x_labels: bool = True,
) -> Figure:
    """将 K 线规格绘制到 axes；若无 ax 则创建新 figure。返回所在 Figure。"""
    if not _HAS_MPL:
        raise RuntimeError('matplotlib is required for static rendering')
    data = spec.get('data', {})
    n = None
    for key in ('open', 'high', 'low', 'close'):
        if key not in data:
            continue
        arr = _to_1d(data[key], share_idx)
        if n is None:
            n = len(arr)
        else:
            n = min(n, len(arr))
    if n is None or n == 0:
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        return fig
    x = np.arange(n)
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 5), facecolor=_get_theme()['figure_facecolor'])
    else:
        fig = ax.figure
    theme = _get_theme()
    ax.set_facecolor(theme['axes_facecolor'])
    ax.grid(True, alpha=theme['grid_alpha'], linestyle=theme['grid_linestyle'])
    o = _to_1d(data['open'], share_idx)[:n]
    h = _to_1d(data['high'], share_idx)[:n]
    l = _to_1d(data['low'], share_idx)[:n]
    c = _to_1d(data['close'], share_idx)[:n]
    width = 0.6
    for i in range(len(x)):
        color = theme['line_color_up'] if c[i] >= o[i] else theme['line_color_down']
        low_i, high_i = l[i], h[i]
        open_i, close_i = o[i], c[i]
        body_bottom = min(open_i, close_i)
        body_height = abs(close_i - open_i)
        ax.vlines(x[i], low_i, high_i, color=color, linewidth=0.8)
        if body_height > 0:
            ax.bar(x[i], body_height, bottom=body_bottom, width=width, color=color, edgecolor=color, linewidth=0.5)
        else:
            ax.hlines(open_i, x[i] - width / 2, x[i] + width / 2, colors=color, linewidth=1)
    for key in data:
        if key in ('open', 'high', 'low', 'close'):
            continue
        arr = _to_1d(data[key], share_idx)[:n]
        ax.plot(x, arr, label=key, alpha=0.8)
    extra = [k for k in data if k not in ('open', 'high', 'low', 'close')]
    if extra:
        ax.legend(loc='upper left', fontsize=theme['font_size'])
    ylabel = 'Price, MA:' + str(extra) if extra else 'Price'
    ax.set_ylabel(ylabel, fontsize=theme['font_size'])
    if show_x_labels and x_dates is not None and len(x_dates) >= n:
        step = max(1, n // theme.get('max_x_ticks', 12))
        ax.set_xticks(x[:: step])
        ax.set_xticklabels(
            [_format_x_label(x_dates[i], theme.get('datetime_format', '%y/%m/%d')) for i in range(0, n, step)],
            rotation=theme.get('xrotation', 0),
        )
    highlight = spec.get('highlight')
    if highlight and isinstance(highlight, dict):
        cond = highlight.get('condition')
        style = highlight.get('style') or {}
        mask = _resolve_highlight_condition(cond, c, n)
        if mask is not None and np.any(mask):
            color = style.get('color', theme['highlight_color'])
            marker = style.get('marker', 'o')
            size = style.get('s', 40)
            ax.scatter(x[mask], c[mask], c=color, marker=marker, s=size, zorder=5)
    return fig


def render_volume_spec(
    spec: Dict[str, Any],
    ax: Optional[Axes] = None,
    share_idx: int = 0,
    x_dates: Optional[Sequence] = None,
    show_x_labels: bool = True,
) -> Figure:
    """将成交量柱状图规格绘制到 axes。若有 open/close 则按涨跌着色（红涨绿跌）。"""
    if not _HAS_MPL:
        raise RuntimeError('matplotlib is required for static rendering')
    data = spec.get('data', {})
    if not data:
        fig, ax = plt.subplots(1, 1, figsize=(8, 2))
        return fig
    vol_name = next((k for k in ('vol', 'volume') if k in data), next(iter(data)))
    arr = _to_1d(data[vol_name], share_idx)
    n = len(arr)
    x = np.arange(n)
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 2), facecolor=_get_theme()['figure_facecolor'])
    else:
        fig = ax.figure
    theme = _get_theme()
    ax.set_facecolor(theme['axes_facecolor'])
    ax.grid(True, alpha=theme['grid_alpha'], linestyle=theme['grid_linestyle'])
    if 'open' in data and 'close' in data:
        o = _to_1d(data['open'], share_idx)[:n]
        c = _to_1d(data['close'], share_idx)[:n]
        up = c >= o
        color_up = theme.get('volume_color_up', 'red')
        color_dn = theme.get('volume_color_down', 'green')
        colors = np.where(up, color_up, color_dn)
        ax.bar(x, arr, color=colors, alpha=0.7, width=0.8)
    else:
        ax.bar(x, arr, color=theme['volume_color'], alpha=0.7, width=0.8)
    ax.set_ylabel('Volume', fontsize=theme['font_size'])
    if show_x_labels and x_dates is not None and len(x_dates) >= n:
        step = max(1, n // theme.get('max_x_ticks', 12))
        ax.set_xticks(x[:: step])
        ax.set_xticklabels(
            [_format_x_label(x_dates[i], theme.get('datetime_format', '%y/%m/%d')) for i in range(0, n, step)],
            rotation=theme.get('xrotation', 0),
        )
    return fig


def render_macd_spec(
    spec: Dict[str, Any],
    ax: Optional[Axes] = None,
    share_idx: int = 0,
    x_dates: Optional[Sequence] = None,
    show_x_labels: bool = True,
) -> Figure:
    """将 MACD 规格绘制到 axes（线 + 柱）；柱按 macd_hist 正负分红绿。"""
    if not _HAS_MPL:
        raise RuntimeError('matplotlib is required for static rendering')
    data = spec.get('data', {})
    series_kind = spec.get('series_kind', {})
    if not data:
        fig, ax = plt.subplots(1, 1, figsize=(8, 2))
        return fig
    n = min(len(_to_1d(arr, share_idx)) for arr in data.values())
    x = np.arange(n)
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 2), facecolor=_get_theme()['figure_facecolor'])
    else:
        fig = ax.figure
    theme = _get_theme()
    ax.set_facecolor(theme['axes_facecolor'])
    ax.grid(True, alpha=theme['grid_alpha'], linestyle=theme['grid_linestyle'])
    hist_col = None
    for col, arr in data.items():
        a = _to_1d(arr, share_idx)[:n]
        kind = series_kind.get(col, 'line')
        if kind == 'bar':
            hist_col = col
            continue
        ax.plot(x, a, label=col, alpha=0.9)
    if hist_col and hist_col in data:
        a = _to_1d(data[hist_col], share_idx)[:n]
        bar_r = np.where(a > 0, a, 0)
        bar_g = np.where(a <= 0, a, 0)
        ax.bar(x, bar_r, color=theme.get('macd_hist_up', 'red'), alpha=0.6, width=0.8)
        ax.bar(x, bar_g, color=theme.get('macd_hist_down', 'green'), alpha=0.6, width=0.8)
    macd_par = spec.get('macd_par')  # optional, e.g. (12, 26, 9)
    ylabel = f'macd: \n{macd_par}' if macd_par else 'macd'
    ax.set_ylabel(ylabel, fontsize=theme['font_size'])
    if len(data) > 1:
        ax.legend(loc='upper left', fontsize=theme['font_size'])
    if show_x_labels and x_dates is not None and len(x_dates) >= n:
        step = max(1, n // theme.get('max_x_ticks', 12))
        ax.set_xticks(x[:: step])
        ax.set_xticklabels(
            [_format_x_label(x_dates[i], theme.get('datetime_format', '%y/%m/%d')) for i in range(0, n, step)],
            rotation=theme.get('xrotation', 0),
        )
    return fig


def render_line_spec(
    spec: Dict[str, Any],
    ax: Optional[Axes] = None,
    share_idx: int = 0,
    x_dates: Optional[Sequence] = None,
    show_x_labels: bool = True,
) -> Figure:
    """将折线规格绘制到 axes。"""
    if not _HAS_MPL:
        raise RuntimeError('matplotlib is required for static rendering')
    data = spec.get('data', {})
    if not data:
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        return fig
    n = min(len(_to_1d(arr, share_idx)) for arr in data.values())
    x = np.arange(n)
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 4), facecolor=_get_theme()['figure_facecolor'])
    else:
        fig = ax.figure
    theme = _get_theme()
    ax.set_facecolor(theme['axes_facecolor'])
    ax.grid(True, alpha=theme['grid_alpha'], linestyle=theme['grid_linestyle'])
    for col, arr in data.items():
        a = _to_1d(arr, share_idx)[:n]
        ax.plot(x, a, label=col, alpha=0.9)
    ax.set_ylabel('Line', fontsize=theme['font_size'])
    if len(data) > 1:
        ax.legend(loc='upper left', fontsize=theme['font_size'])
    if show_x_labels and x_dates is not None and len(x_dates) >= n:
        step = max(1, n // theme.get('max_x_ticks', 12))
        ax.set_xticks(x[:: step])
        ax.set_xticklabels(
            [_format_x_label(x_dates[i], theme.get('datetime_format', '%y/%m/%d')) for i in range(0, n, step)],
            rotation=theme.get('xrotation', 0),
        )
    highlight = spec.get('highlight')
    if highlight and isinstance(highlight, dict):
        cond = highlight.get('condition')
        style = highlight.get('style') or {}
        first_arr = _to_1d(next(iter(data.values())), share_idx)[:n]
        mask = _resolve_highlight_condition(cond, first_arr, n)
        if mask is not None and np.any(mask):
            color = style.get('color', theme['line_color_up'])
            marker = style.get('marker', 'o')
            size = style.get('s', 40)
            ax.scatter(x[mask], first_arr[mask], c=color, marker=marker, s=size, zorder=5)
    return fig


def render_spec(
    spec: Dict[str, Any],
    ax: Optional[Axes] = None,
    share_idx: int = 0,
    x_dates: Optional[Sequence] = None,
    show_x_labels: bool = True,
) -> Figure:
    """根据 spec['chart_type'] 分发到对应渲染函数，返回 Figure。"""
    ct = spec.get('chart_type', '')
    if ct == 'kline':
        return render_kline_spec(spec, ax=ax, share_idx=share_idx, x_dates=x_dates, show_x_labels=show_x_labels)
    if ct == 'volume':
        return render_volume_spec(spec, ax=ax, share_idx=share_idx, x_dates=x_dates, show_x_labels=show_x_labels)
    if ct == 'macd':
        return render_macd_spec(spec, ax=ax, share_idx=share_idx, x_dates=x_dates, show_x_labels=show_x_labels)
    if ct == 'line':
        return render_line_spec(spec, ax=ax, share_idx=share_idx, x_dates=x_dates, show_x_labels=show_x_labels)
    if _HAS_MPL:
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        return fig
    raise RuntimeError('matplotlib is required for static rendering')


def build_figure_from_specs(
    specs_per_group: Sequence[Sequence[Optional[Dict[str, Any]]]],
    types_info: Sequence[Any],
    x_dates: Optional[Sequence] = None,
    group_titles: Optional[Sequence[str]] = None,
) -> Figure:
    """
    根据多组规格与类型信息绘制一张 Figure。
    同组内所有子图共享时间轴（sharex），仅最下方子图显示 X 刻度。
    layout=stack 时多组垂直上下排列（每组占若干行）；单组时单列多行。
    specs_per_group[group_idx][type_idx] = spec 或 None。
    types_info 与每行 type 对应，含 .importance。
    group_titles[group_idx] 为每组主标题，使用较大字号加粗。
    """
    if not _HAS_MPL:
        raise RuntimeError('matplotlib is required for static rendering')
    n_groups = len(specs_per_group)
    n_types = len(types_info) if types_info else 0
    if n_types == 0:
        fig, _ = plt.subplots(1, 1, figsize=(12, 8))
        return fig
    type_ratios = []
    for info in types_info:
        imp = getattr(info, 'importance', 'secondary')
        type_ratios.append(2.0 if imp == 'main' else 0.5)
    has_main = any(getattr(t, 'importance', '') == 'main' for t in types_info)
    has_secondary = any(getattr(t, 'importance', '') == 'secondary' for t in types_info)
    if not (has_main and has_secondary):
        type_ratios = [1.0] * n_types
    theme = _get_theme()
    title_font_size = theme.get('title_font_size', 12)
    if n_groups > 1:
        spacer_ratio = 0.4
        n_rows_total = n_groups * n_types + (n_groups - 1)
        height_ratios = []
        for g in range(n_groups):
            height_ratios.extend(type_ratios)
            if g < n_groups - 1:
                height_ratios.append(spacer_ratio)
        fig = plt.figure(
            figsize=(12, 4 * n_groups),
            facecolor=theme['figure_facecolor'],
        )
        gs = fig.add_gridspec(n_rows_total, 1, height_ratios=height_ratios, hspace=0)
        for g in range(n_groups):
            ax_share = None
            for t in range(n_types):
                row_idx = g * (n_types + 1) + t
                spec = specs_per_group[g][t] if g < len(specs_per_group) and t < len(specs_per_group[g]) else None
                if ax_share is None:
                    ax = fig.add_subplot(gs[row_idx, 0])
                    ax_share = ax
                else:
                    ax = fig.add_subplot(gs[row_idx, 0], sharex=ax_share)
                ax.set_facecolor(theme['axes_facecolor'])
                if spec is not None:
                    render_spec(
                        spec,
                        ax=ax,
                        share_idx=0,
                        x_dates=x_dates,
                        show_x_labels=(t == n_types - 1 and g == n_groups - 1),
                    )
                if t < n_types - 1 or g < n_groups - 1:
                    plt.setp(ax.get_xticklabels(), visible=False)
                if group_titles and g < len(group_titles) and t == 0:
                    ax.set_title(group_titles[g], fontsize=title_font_size, fontweight='bold')
    else:
        fig = plt.figure(
            figsize=(12, 8),
            facecolor=theme['figure_facecolor'],
        )
        gs = fig.add_gridspec(n_types, 1, height_ratios=type_ratios, hspace=0)
        ax_share = None
        for r in range(n_types):
            spec = specs_per_group[0][r] if r < len(specs_per_group[0]) else None
            if ax_share is None:
                ax = fig.add_subplot(gs[r, 0])
                ax_share = ax
            else:
                ax = fig.add_subplot(gs[r, 0], sharex=ax_share)
            ax.set_facecolor(theme['axes_facecolor'])
            if spec is not None:
                render_spec(
                    spec,
                    ax=ax,
                    share_idx=0,
                    x_dates=x_dates,
                    show_x_labels=(r == n_types - 1),
                )
            if r < n_types - 1:
                plt.setp(ax.get_xticklabels(), visible=False)
            if group_titles and len(group_titles) > 0 and r == 0:
                ax.set_title(group_titles[0], fontsize=title_font_size, fontweight='bold')
    return fig
