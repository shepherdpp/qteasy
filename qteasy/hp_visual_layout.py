# coding=utf-8
# ======================================
# File:     hp_visual_layout.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-03-21
# Desc:
#   HistoryPanel 可视化统一布局规范：单组/多组 stack 共用 chart 区比例与行号；
#   Matplotlib 表头行权重按「与单组参考图同绝对高度（英寸）」反解，避免多组 fig 变高时表头被同比拉高。
# ======================================

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Sequence, Tuple, TypedDict


class HpVisualLayoutSpec(TypedDict):
    """
    HistoryPanel 多组图表的布局决策结果（TypedDict）。

    Matplotlib 将 OHLC 表头占独立 gridspec 行，可在其下增加空白间隔行（``mpl_pre_chart_rows``）；
    Plotly 表头走 margin + annotations/HTML，故 ``plotly_*`` 仅描述数据子图行，不含表头行。
    """

    n_groups: int
    n_types: int
    row_off: int
    show_ohlc_header: bool
    type_ratios: List[float]
    chart_height_ratios: List[float]
    mpl_header_weight: float
    mpl_figsize: Tuple[float, float]
    mpl_height_ratios: List[float]
    mpl_hspace: float
    mpl_header_line1_yaxes: float
    mpl_header_line2_yaxes: float
    title_pad: float
    plotly_row_heights: List[float]
    plotly_n_subplot_rows: int
    plotly_vertical_spacing: float
    plotly_subplot_titles: List[str]
    plotly_margin_top: int
    plotly_header_y1: float
    plotly_header_y2: float
    spacer_ratio: float
    spacer_between_groups: bool
    mpl_pre_chart_rows: int
    mpl_header_gap_below_inches: float


def _type_ratios_from_types_info(types_info: Sequence[Any]) -> List[float]:
    """由 types_info 的 importance 得到每类子图的相对高度（与旧逻辑一致）。"""
    n_types = len(types_info) if types_info else 0
    if n_types == 0:
        return []
    ratios: List[float] = []
    for info in types_info:
        imp = getattr(info, 'importance', 'secondary')
        ratios.append(2.0 if imp == 'main' else 0.5)
    has_main = any(getattr(t, 'importance', '') == 'main' for t in types_info)
    has_secondary = any(getattr(t, 'importance', '') == 'secondary' for t in types_info)
    if not (has_main and has_secondary):
        ratios = [1.0] * n_types
    return ratios


def _build_chart_height_ratios(
    n_groups: int,
    n_types: int,
    type_ratios: Sequence[float],
    spacer_ratio: float,
) -> Tuple[List[float], bool]:
    """
    构造仅含「数据子图 + 组间 spacer」的高度比例列表（不含 MPL 表头行）。

    Returns
    -------
    chart_ratios, spacer_between_groups
    """
    if n_types <= 0:
        return [], False
    spacer_between = n_groups > 1
    out: List[float] = []
    for g in range(n_groups):
        out.extend(type_ratios)
        if spacer_between and g < n_groups - 1:
            out.append(float(spacer_ratio))
    return out, spacer_between


def _mpl_header_weight(
    chart_sum: float,
    row_off: int,
    fig_height_inches: float,
    theme: Mapping[str, Any],
) -> float:
    """
    表头行在 gridspec height_ratios 中的权重。

    默认使表头在图上的**绝对高度（英寸）**与「参考图高、单组」时一致：先取
    ``C = fig_h_ref * hp_header_vertical_fraction``，再令
    ``fig_height_inches * header_w/(header_w+chart_sum) = C`` 反解 ``header_w``。
    这样多组时整张图变高，表头不会按比例被拉高（此前固定「占整图比例 f」会导致多组表头过高）。

    若配置 ``hp_mpl_header_height_ratio`` 为 float 则仍使用该固定权重（旧行为）。
    """
    if row_off <= 0 or chart_sum <= 0:
        return 0.0
    fixed = theme.get('hp_mpl_header_height_ratio')
    if isinstance(fixed, (int, float)) and float(fixed) > 0:
        return float(fixed)
    f = float(theme.get('hp_header_vertical_fraction', 0.26 / (0.26 + 2.0 + 0.5)))
    f = min(max(f, 1e-6), 1.0 - 1e-6)
    h_floor = float(theme.get('hp_mpl_fig_height_floor', 8.0))
    h_base = float(theme.get('hp_mpl_fig_height_base', 4.0))
    h_int = float(theme.get('hp_mpl_fig_height_intercept', 1.0))
    ref_ng = float(theme.get('hp_mpl_header_ref_n_groups', 1.0))
    ref_ng = max(ref_ng, 1e-6)
    fig_h_ref = max(h_floor, h_base * ref_ng + h_int)
    target_abs = fig_h_ref * f
    fh = max(float(fig_height_inches), 1e-9)
    numer = target_abs / fh
    numer = min(max(numer, 1e-9), 1.0 - 1e-9)
    return chart_sum * numer / (1.0 - numer)


def compute_hp_visual_layout_spec(
    n_groups: int,
    n_types: int,
    types_info: Sequence[Any],
    theme: Mapping[str, Any],
    *,
    row_off: int,
    show_ohlc_header: bool,
    group_titles: Optional[Sequence[str]] = None,
) -> HpVisualLayoutSpec:
    """
    根据组数、类型与主题计算统一布局规范，供静态图与 Plotly 共用。

    Parameters
    ----------
    n_groups : int
        资产组数（stack 垂直排列的组数）。
    n_types : int
        每组内子图类型数（与 ``types_info`` 长度一致）。
    types_info : sequence
        类型描述序列，含 ``importance``，用于推导 ``type_ratios``。
    theme : mapping
        主题字典，含 ``hp_*`` / ``plotly_*`` / ``mpl_*`` 等布局键。
        MPL 表头：默认 ``hp_header_vertical_fraction`` 表示「参考图高（见 ``hp_mpl_header_ref_n_groups`` 与
        ``hp_mpl_fig_height_*``）下表头占该参考图高度的比例」，实际多组时反解行权重使表头**绝对高度（英寸）**
        与参考一致；若设 ``hp_mpl_header_height_ratio`` 则仍为固定权重。
        ``hp_mpl_header_gap_below_mm`` 在表头与第一行子图之间插入留白（毫米），图总高增加等量英寸，不压缩表头与图表区。
    row_off : int
        Matplotlib 是否在 gridspec 顶部预留表头行（0 或 1）；与是否已有 last bar 记录一致。
    show_ohlc_header : bool
        是否存在 K 线表头语义（含 Plotly margin / 元数据）；可与 ``row_off`` 同时为真。
    group_titles : sequence of str, optional
        每组主标题；用于 ``plotly_subplot_titles`` 首行标签。

    Returns
    -------
    HpVisualLayoutSpec
        完整布局字段。
    """
    type_ratios = _type_ratios_from_types_info(types_info) if n_types else []
    spacer_ratio = float(theme.get('hp_spacer_ratio_between_groups', 0.4))
    chart_height_ratios, spacer_between = _build_chart_height_ratios(
        n_groups, n_types, type_ratios, spacer_ratio,
    )
    chart_sum = float(sum(chart_height_ratios))

    w_in = float(theme.get('hp_mpl_fig_width_inches', 12.0))
    h_floor = float(theme.get('hp_mpl_fig_height_floor', 8.0))
    h_base = float(theme.get('hp_mpl_fig_height_base', 4.0))
    h_int = float(theme.get('hp_mpl_fig_height_intercept', 1.0))
    fig_h0 = max(h_floor, h_base * float(n_groups) + h_int)

    gap_mm = float(theme.get('hp_mpl_header_gap_below_mm', 8.0))
    d_in = max(0.0, gap_mm / 25.4) if row_off > 0 else 0.0

    mpl_pre_chart_rows = 0
    mpl_header_gap_below_inches = 0.0
    mpl_figsize: Tuple[float, float]
    mpl_height_ratios: List[float]
    header_w: float

    if row_off > 0 and chart_sum > 0:
        header_w = _mpl_header_weight(chart_sum, row_off, fig_h0, theme)
        c_hdr = fig_h0 * header_w / (header_w + chart_sum)
        if d_in > 0.0:
            fig_h1 = fig_h0 + d_in
            t_new = chart_sum / (1.0 - (c_hdr + d_in) / fig_h1)
            hp = t_new * c_hdr / fig_h1
            gap_w = t_new * d_in / fig_h1
            mpl_height_ratios = [hp, gap_w] + chart_height_ratios
            mpl_figsize = (w_in, fig_h1)
            mpl_pre_chart_rows = 2
            mpl_header_gap_below_inches = d_in
            header_w = hp
        else:
            mpl_height_ratios = [header_w] + chart_height_ratios
            mpl_figsize = (w_in, fig_h0)
            mpl_pre_chart_rows = 1
    else:
        header_w = 0.0
        mpl_height_ratios = list(chart_height_ratios)
        mpl_figsize = (w_in, fig_h0)

    mpl_hspace = float(theme.get('hp_mpl_gridspec_hspace', 0.06))
    y1 = float(theme.get('mpl_header_line1_yaxes', 0.88))
    y2 = float(theme.get('mpl_header_line2_yaxes', 0.38))
    title_pad = float(theme.get('hp_plot_title_pad', 14.0))

    plotly_row_heights = list(chart_height_ratios)
    plotly_n = len(plotly_row_heights)
    plotly_vspace = float(theme.get('hp_plotly_vertical_spacing', 0.0))
    margin_top = int(
        theme.get(
            'plotly_margin_top_with_header',
            120,
        ) if show_ohlc_header else theme.get('plotly_margin_top_no_header', 80),
    )
    py1 = float(theme.get('plotly_header_annotation_y1', 1.115))
    py2 = float(theme.get('plotly_header_annotation_y2', 1.085))

    subplot_titles: List[str] = []
    if n_groups > 1 and n_types > 0:
        for g in range(n_groups):
            for t in range(n_types):
                title = ''
                if t == 0 and group_titles and g < len(group_titles) and group_titles[g]:
                    title = str(group_titles[g])
                subplot_titles.append(title)
            if g < n_groups - 1:
                subplot_titles.append('')
    elif n_types > 0:
        for t in range(n_types):
            title = ''
            if t == 0 and group_titles and len(group_titles) > 0 and group_titles[0]:
                title = str(group_titles[0])
            subplot_titles.append(title)

    out: HpVisualLayoutSpec = {
        'n_groups': n_groups,
        'n_types': n_types,
        'row_off': row_off,
        'show_ohlc_header': show_ohlc_header,
        'type_ratios': type_ratios,
        'chart_height_ratios': chart_height_ratios,
        'mpl_header_weight': header_w,
        'mpl_figsize': mpl_figsize,
        'mpl_height_ratios': mpl_height_ratios,
        'mpl_hspace': mpl_hspace,
        'mpl_header_line1_yaxes': y1,
        'mpl_header_line2_yaxes': y2,
        'title_pad': title_pad,
        'plotly_row_heights': plotly_row_heights,
        'plotly_n_subplot_rows': plotly_n,
        'plotly_vertical_spacing': plotly_vspace,
        'plotly_subplot_titles': subplot_titles,
        'plotly_margin_top': margin_top,
        'plotly_header_y1': py1,
        'plotly_header_y2': py2,
        'spacer_ratio': spacer_ratio,
        'spacer_between_groups': spacer_between,
        'mpl_pre_chart_rows': mpl_pre_chart_rows,
        'mpl_header_gap_below_inches': mpl_header_gap_below_inches,
    }
    return out


def mpl_gridspec_row_index(spec: HpVisualLayoutSpec, group: int, type_idx: int) -> int:
    """Matplotlib ``add_subplot(gs[row, 0])`` 使用的 0-based 行下标（表头 + 可选间隔行之后为第一行 chart）。"""
    base = spec['mpl_pre_chart_rows']
    ng = spec['n_groups']
    nt = spec['n_types']
    if ng > 1:
        return base + group * (nt + 1) + type_idx
    return base + type_idx


def plotly_trace_row_1based(spec: HpVisualLayoutSpec, group: int, type_idx: int) -> int:
    """Plotly ``add_trace(..., row=..., col=1)`` 使用的 1-based 行号（无表头行）。"""
    ng = spec['n_groups']
    nt = spec['n_types']
    if ng > 1:
        return group * (nt + 1) + type_idx + 1
    return type_idx + 1
