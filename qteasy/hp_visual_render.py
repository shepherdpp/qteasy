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

from typing import Any, Dict, Optional, Sequence, Tuple, TYPE_CHECKING

import numpy as np

from qteasy.hp_visual_bar_display import (
    build_bar_display_data,
    mpl_ohlc_header_segments,
    primary_kline_group_index,
    specs_contain_kline,
)
from qteasy.hp_visual_layout import compute_hp_visual_layout_spec, mpl_gridspec_row_index
from qteasy.hp_visual_theme_adapt import (
    HeaderFontRole,
    resolve_candle_style_matplotlib,
    resolve_font_size,
    resolve_header_font_matplotlib,
)

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
        # 逻辑字号：旧版 resolve_font_size(header_body/header_emphasis)，表头分段已改用 header_font_*
        'header_font_size': 11,
        'header_emphasis_font_size': 16,
        # 可选：覆盖七种表头字体，见 hp_visual_theme_adapt.merge_header_font_theme
        # 'header_font_title': {'size': 16},
        # 蜡烛：逻辑线宽/透明度，经转译层落到 mpl / Plotly
        'candle_wick_linewidth': 0.8,
        'candle_body_edgewidth': 0.5,
        'candle_doji_linewidth': 1.0,
        'candle_bar_width': 0.6,
        'candle_plotly_fill_alpha': 0.82,
        'candle_plotly_line_width': 1.15,
        'candle_plotly_whiskerwidth': 0.18,
        'datetime_format': '%y/%m/%d',
        'xrotation': 0,
        'max_x_ticks': 12,
        # 表头占「表头 + 全部数据子图区」的垂直比例；用于单组/多组统一 MPL 表头行权重
        'hp_header_vertical_fraction': 0.26 / (0.26 + 2.0 + 0.5),
        # 若设为 float，则 MPL 表头 gridspec 行权重固定为该值，忽略 hp_header_vertical_fraction
        'hp_mpl_header_height_ratio': None,
        # MPL 表头绝对高度参考：用「该组数」对应的 fig 高度 × hp_header_vertical_fraction 作为目标英寸高度
        'hp_mpl_header_ref_n_groups': 1.0,
        # 表头轴与第一组子图之间的垂直留白（毫米）；仅 MPL；图总高增加等量英寸以免压缩表头/图表区
        'hp_mpl_header_gap_below_mm': 8.0,
        'hp_mpl_gridspec_hspace': 0.06,
        'hp_spacer_ratio_between_groups': 0.4,
        'hp_mpl_fig_width_inches': 12.0,
        'hp_mpl_fig_height_base': 4.0,
        'hp_mpl_fig_height_floor': 8.0,
        'hp_mpl_fig_height_intercept': 1.0,
        'plotly_margin_top_with_header': 120,
        'plotly_margin_top_no_header': 80,
        'plotly_header_annotation_y1': 1.115,
        'plotly_header_annotation_y2': 1.085,
        # FigureWidget 表头：距整图顶边的目标毫米（paper y 由 layout 反解）
        'plotly_header_line1_top_mm': 6.0,
        'plotly_header_line2_top_mm': 14.5,
        'plotly_css_px_per_inch': 96.0,
        'plotly_header_h_plot_px_min': 80.0,
        'plotly_header_paper_y_min': 1.02,
        'plotly_header_paper_y_max': 1.42,
        'hp_plotly_vertical_spacing': 0.0,
        'mpl_header_line1_yaxes': 0.88,
        'mpl_header_line2_yaxes': 0.38,
        'hp_plot_title_pad': 14.0,
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
    alpha: float = 1.0,
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
    cst = resolve_candle_style_matplotlib(theme)
    ax.set_facecolor(theme['axes_facecolor'])
    ax.grid(True, alpha=theme['grid_alpha'], linestyle=theme['grid_linestyle'])
    o = _to_1d(data['open'], share_idx)[:n]
    h = _to_1d(data['high'], share_idx)[:n]
    l = _to_1d(data['low'], share_idx)[:n]
    c = _to_1d(data['close'], share_idx)[:n]
    width = cst['bar_width']
    wick_lw = cst['wick_linewidth']
    body_edge = cst['body_edgewidth']
    doji_lw = cst['doji_linewidth']
    for i in range(len(x)):
        color = cst['line_color_up'] if c[i] >= o[i] else cst['line_color_down']
        low_i, high_i = l[i], h[i]
        open_i, close_i = o[i], c[i]
        body_bottom = min(open_i, close_i)
        body_height = abs(close_i - open_i)
        ax.vlines(x[i], low_i, high_i, color=color, linewidth=wick_lw, alpha=alpha)
        if body_height > 0:
            ax.bar(
                x[i], body_height, bottom=body_bottom, width=width,
                color=color, edgecolor=color, linewidth=body_edge, alpha=alpha,
            )
        else:
            ax.hlines(open_i, x[i] - width / 2, x[i] + width / 2, colors=color, linewidth=doji_lw, alpha=alpha)
    for key in data:
        if key in ('open', 'high', 'low', 'close'):
            continue
        arr = _to_1d(data[key], share_idx)[:n]
        ax.plot(x, arr, label=key, alpha=min(1.0, 0.8 * alpha))
    extra = [k for k in data if k not in ('open', 'high', 'low', 'close')]
    fs_leg = resolve_font_size('matplotlib', 'legend', theme)
    fs_y = resolve_font_size('matplotlib', 'axis_ylabel', theme)
    if extra:
        ax.legend(loc='upper left', fontsize=fs_leg)
    ylabel = 'Price, MA:' + str(extra) if extra else 'Price'
    ax.set_ylabel(ylabel, fontsize=fs_y)
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
    alpha: float = 1.0,
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
        ax.bar(x, arr, color=colors, alpha=min(1.0, 0.7 * alpha), width=0.8)
    else:
        ax.bar(x, arr, color=theme['volume_color'], alpha=min(1.0, 0.7 * alpha), width=0.8)
    ax.set_ylabel('Volume', fontsize=resolve_font_size('matplotlib', 'axis_ylabel', theme))
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
    alpha: float = 1.0,
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
        ax.plot(x, a, label=col, alpha=min(1.0, 0.9 * alpha))
    if hist_col and hist_col in data:
        a = _to_1d(data[hist_col], share_idx)[:n]
        bar_r = np.where(a > 0, a, 0)
        bar_g = np.where(a <= 0, a, 0)
        ax.bar(x, bar_r, color=theme.get('macd_hist_up', 'red'), alpha=min(1.0, 0.6 * alpha), width=0.8)
        ax.bar(x, bar_g, color=theme.get('macd_hist_down', 'green'), alpha=min(1.0, 0.6 * alpha), width=0.8)
    macd_par = spec.get('macd_par')  # optional, e.g. (12, 26, 9)
    ylabel = f'macd: \n{macd_par}' if macd_par else 'macd'
    ax.set_ylabel(ylabel, fontsize=resolve_font_size('matplotlib', 'axis_ylabel', theme))
    if len(data) > 1:
        ax.legend(loc='upper left', fontsize=resolve_font_size('matplotlib', 'legend', theme))
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
    alpha: float = 1.0,
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
        ax.plot(x, a, label=col, alpha=min(1.0, 0.9 * alpha))
    ax.set_ylabel('Line', fontsize=resolve_font_size('matplotlib', 'axis_ylabel', theme))
    if len(data) > 1:
        ax.legend(loc='upper left', fontsize=resolve_font_size('matplotlib', 'legend', theme))
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
    alpha: float = 1.0,
    x_dates: Optional[Sequence] = None,
    show_x_labels: bool = True,
) -> Figure:
    """根据 spec['chart_type'] 分发到对应渲染函数，返回 Figure。"""
    ct = spec.get('chart_type', '')
    if ct == 'kline':
        return render_kline_spec(spec, ax=ax, share_idx=share_idx, alpha=alpha, x_dates=x_dates, show_x_labels=show_x_labels)
    if ct == 'volume':
        return render_volume_spec(spec, ax=ax, share_idx=share_idx, alpha=alpha, x_dates=x_dates, show_x_labels=show_x_labels)
    if ct == 'macd':
        return render_macd_spec(spec, ax=ax, share_idx=share_idx, alpha=alpha, x_dates=x_dates, show_x_labels=show_x_labels)
    if ct == 'line':
        return render_line_spec(spec, ax=ax, share_idx=share_idx, alpha=alpha, x_dates=x_dates, show_x_labels=show_x_labels)
    if _HAS_MPL:
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        return fig
    raise RuntimeError('matplotlib is required for static rendering')


def _draw_static_ohlc_header(
    ax: Axes,
    rec: Dict[str, Any],
    theme: Dict[str, Any],
    *,
    line1_yaxes: Optional[float] = None,
    line2_yaxes: Optional[float] = None,
) -> None:
    """在专用 Axes 上绘制英文 OHLC 摘要；字体由 theme 七种 ``header_font_*`` 统一规定。"""
    setattr(ax, '_hp_ohlc_header', True)
    ax.set_facecolor(theme.get('figure_facecolor', (1, 1, 1)))
    ax.axis('off')
    segs1, segs2 = mpl_ohlc_header_segments(rec)
    y1 = float(line1_yaxes if line1_yaxes is not None else theme.get('mpl_header_line1_yaxes', 0.88))
    y2 = float(line2_yaxes if line2_yaxes is not None else theme.get('mpl_header_line2_yaxes', 0.38))

    def _draw_line(y_axes: float, segments: Sequence[Tuple[str, HeaderFontRole]]) -> None:
        x = 0.01
        for text, role in segments:
            if not text:
                continue
            fd = resolve_header_font_matplotlib(theme, role)
            fs = fd['fontsize']
            ax.text(
                x, y_axes, text, transform=ax.transAxes, va='top', ha='left',
                clip_on=False, **fd,
            )
            x += len(text) * 0.0078 * (fs / 11.0) + 0.0025

    if segs1:
        _draw_line(y1, segs1)
    if segs2:
        _draw_line(y2, segs2)


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
    theme = _get_theme()
    title_fd = resolve_header_font_matplotlib(theme, 'header_title')
    tick_fs = resolve_font_size('matplotlib', 'axis_tick', theme)

    show_header = specs_contain_kline(specs_per_group, types_info)
    last_rec: Optional[Dict[str, Any]] = None
    if show_header and x_dates is not None and len(x_dates) > 0:
        bar_all = build_bar_display_data(specs_per_group, types_info, list(x_dates), theme=theme)
        g_k = primary_kline_group_index(specs_per_group, types_info)
        if g_k is not None and bar_all and g_k < len(bar_all) and bar_all[g_k]:
            last_rec = bar_all[g_k][-1]

    row_off = 1 if (show_header and bool(last_rec)) else 0

    layout_spec = compute_hp_visual_layout_spec(
        n_groups,
        n_types,
        types_info,
        theme,
        row_off=row_off,
        show_ohlc_header=show_header,
        group_titles=group_titles,
    )
    fig = plt.figure(
        figsize=layout_spec['mpl_figsize'],
        facecolor=theme['figure_facecolor'],
    )
    gs = fig.add_gridspec(
        len(layout_spec['mpl_height_ratios']),
        1,
        height_ratios=layout_spec['mpl_height_ratios'],
        hspace=layout_spec['mpl_hspace'],
    )
    if layout_spec['row_off'] and last_rec is not None:
        ax_h = fig.add_subplot(gs[0, 0])
        _draw_static_ohlc_header(
            ax_h,
            last_rec,
            theme,
            line1_yaxes=layout_spec['mpl_header_line1_yaxes'],
            line2_yaxes=layout_spec['mpl_header_line2_yaxes'],
        )
    if layout_spec['mpl_pre_chart_rows'] >= 2:
        ax_gap = fig.add_subplot(gs[1, 0])
        ax_gap.axis('off')
        ax_gap.set_navigate(False)
        setattr(ax_gap, '_hp_mpl_gap', True)
    title_pad = layout_spec['title_pad']
    for g in range(n_groups):
        n_share_group = 1
        for t in range(n_types):
            spec_probe = specs_per_group[g][t] if g < len(specs_per_group) and t < len(specs_per_group[g]) else None
            if spec_probe is None:
                continue
            data_probe = spec_probe.get('data', {})
            if not data_probe:
                continue
            arr_probe = next(iter(data_probe.values()), None)
            if hasattr(arr_probe, 'ndim') and getattr(arr_probe, 'ndim', 1) == 2:
                n_share_group = max(1, int(arr_probe.shape[0]))
                break
        is_overlay_group = n_share_group == 2
        share_alpha = 0.55 if is_overlay_group else 1.0
        ax_share = None
        for t in range(n_types):
            row_idx = mpl_gridspec_row_index(layout_spec, g, t)
            spec = specs_per_group[g][t] if g < len(specs_per_group) and t < len(specs_per_group[g]) else None
            if ax_share is None:
                ax = fig.add_subplot(gs[row_idx, 0])
                ax_share = ax
            else:
                ax = fig.add_subplot(gs[row_idx, 0], sharex=ax_share)
            ax.set_facecolor(theme['axes_facecolor'])
            if spec is not None:
                if is_overlay_group:
                    # overlay 双标的：左轴主视觉、右轴次视觉，分别按各自数据自适应
                    render_spec(
                        spec,
                        ax=ax,
                        share_idx=0,
                        alpha=1.0,
                        x_dates=x_dates,
                        show_x_labels=(t == n_types - 1 and g == n_groups - 1),
                    )
                    ax_r = ax.twinx()
                    ax_r.set_facecolor((0, 0, 0, 0))
                    render_spec(
                        spec,
                        ax=ax_r,
                        share_idx=1,
                        alpha=share_alpha,
                        x_dates=x_dates,
                        show_x_labels=False,
                    )
                    ylab = ax.get_ylabel()
                    if ylab:
                        ax_r.set_ylabel(f'{ylab} (R)')
                else:
                    for s_idx in range(n_share_group):
                        render_spec(
                            spec,
                            ax=ax,
                            share_idx=s_idx,
                            alpha=share_alpha,
                            x_dates=x_dates,
                            show_x_labels=(t == n_types - 1 and g == n_groups - 1),
                        )
            if t < n_types - 1 or g < n_groups - 1:
                plt.setp(ax.get_xticklabels(), visible=False)
            if group_titles and g < len(group_titles) and t == 0:
                ax.set_title(
                    group_titles[g],
                    fontsize=title_fd['fontsize'],
                    fontweight=title_fd['fontweight'],
                    color=title_fd['color'],
                    fontfamily=title_fd['fontfamily'],
                    pad=title_pad,
                )

    for ax in fig.axes:
        if getattr(ax, '_hp_ohlc_header', False):
            continue
        if getattr(ax, '_hp_mpl_gap', False):
            continue
        ax.tick_params(axis='both', labelsize=tick_fs)
    return fig
