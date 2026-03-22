# coding=utf-8
# ======================================
# File:     hp_visual_theme_adapt.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-03-21
# Desc:
#   HistoryPanel 可视化：逻辑主题到 matplotlib / Plotly 实际字号与蜡烛样式的转译层。
#   用户只维护一套 theme；后端差异集中在此模块。
#   表头七种字体（header_font_title 等）与 qt.candle / InterCandle 命名对齐，见 merge_header_font_theme。
# ======================================

from __future__ import annotations

import platform
from typing import Any, Dict, Literal, Mapping, Tuple

# 图元角色：轴刻度、Y 轴标题、分组标题、图例、OHLC 表头
FontRole = Literal[
    'axis_tick',
    'axis_title',
    'axis_ylabel',
    'group_title',
    'legend',
    'header_body',
    'header_emphasis',
]
VisualBackend = Literal['matplotlib', 'plotly']

# 表头七种字体角色（与 qt.candle / InterCandle 的 title_font、normal_label_font、
# large_red/green、small_red/green、normal_font 语义对齐，便于两套图表统一调参）
HeaderFontRole = Literal[
    'header_title',
    'header_normal_label',
    'header_large_red',
    'header_large_green',
    'header_small_red',
    'header_small_green',
    'header_normal',
]

_HEADER_FONT_KEYS: Tuple[Tuple[HeaderFontRole, str], ...] = (
    ('header_title', 'header_font_title'),
    ('header_normal_label', 'header_font_normal_label'),
    ('header_large_red', 'header_font_large_red'),
    ('header_large_green', 'header_font_large_green'),
    ('header_small_red', 'header_font_small_red'),
    ('header_small_green', 'header_font_small_green'),
    ('header_normal', 'header_font_normal'),
)


def _zh_font_family_fallback() -> str:
    """与 visual.InterCandle 一致：优先 QT_CONFIG 的中文字体名，否则 Arial。"""
    try:
        from qteasy import QT_CONFIG
        system = platform.system()
        if system == 'Darwin':
            return str(QT_CONFIG.get('ZH_font_name_MAC', 'Arial'))
        if system == 'Windows':
            return str(QT_CONFIG.get('ZH_font_name_WIN', 'Arial'))
        if system == 'Linux':
            return str(QT_CONFIG.get('ZH_font_name_LINUX', 'Arial'))
    except Exception:
        pass
    return 'Arial'


def default_header_font_specs(zh_family: str) -> Dict[HeaderFontRole, Dict[str, Any]]:
    """
    七种表头字体的默认逻辑属性（对齐 visual.py:180-217 的量级与字重）。

    每个子 dict 含：family, size, color, weight。
    """
    arial = 'Arial'
    return {
        'header_title': {
            'family': zh_family,
            'size': 16,
            'color': 'black',
            'weight': 'bold',
        },
        'header_normal_label': {
            'family': zh_family,
            'size': 12,
            'color': 'black',
            'weight': 'normal',
        },
        'header_large_red': {
            'family': arial,
            'size': 22,
            'color': 'red',
            'weight': 'bold',
        },
        'header_large_green': {
            'family': arial,
            'size': 22,
            'color': 'green',
            'weight': 'bold',
        },
        'header_small_red': {
            'family': arial,
            'size': 12,
            'color': 'red',
            'weight': 'bold',
        },
        'header_small_green': {
            'family': arial,
            'size': 12,
            'color': 'green',
            'weight': 'bold',
        },
        'header_normal': {
            'family': arial,
            'size': 12,
            'color': 'black',
            'weight': 'normal',
        },
    }


def merge_header_font_theme(theme: Mapping[str, Any]) -> Dict[HeaderFontRole, Dict[str, Any]]:
    """
    将 theme 中用户覆盖的 header_font_* 与默认值合并，返回七种角色的完整规格。
    """
    zh = _zh_font_family_fallback()
    base = default_header_font_specs(zh)
    out: Dict[HeaderFontRole, Dict[str, Any]] = {}
    for role, key in _HEADER_FONT_KEYS:
        spec = dict(base[role])
        override = theme.get(key)
        if isinstance(override, Mapping):
            for k, v in override.items():
                if v is not None:
                    spec[str(k)] = v
        out[role] = spec
    return out


def resolve_header_font_matplotlib(theme: Mapping[str, Any], role: HeaderFontRole) -> Dict[str, Any]:
    """
    表头分段绘制用 kwargs，可直接传入 matplotlib ``Axes.text``（与 va='top'、ha='left' 等配合）。

    静态图在逻辑 ``merge_header_font_theme`` 字号基础上整体减 2；Plotly 表头用
    ``resolve_header_font_plotly`` / ``header_font_span_style``，不减字号。

    Returns
    -------
    dict
        fontsize, fontfamily, color, fontweight。
    """
    specs = merge_header_font_theme(theme)
    s = specs[role]
    logical_sz = int(s['size'])
    # 七种表头角色统一比 theme 标准小 2pt，避免过小可读性丧失
    mpl_sz = max(6, logical_sz - 2)
    return {
        'fontsize': mpl_sz,
        'fontfamily': str(s['family']),
        'color': str(s['color']),
        'fontweight': str(s['weight']),
    }


def resolve_header_font_plotly(theme: Mapping[str, Any], role: HeaderFontRole) -> Dict[str, Any]:
    """Plotly ``layout.annotations[].font`` 或 trace 文本用。"""
    specs = merge_header_font_theme(theme)
    s = specs[role]
    return {
        'size': int(s['size']),
        'family': str(s['family']),
        'color': str(s['color']),
        'weight': str(s['weight']),
    }


def header_font_span_style(theme: Mapping[str, Any], role: HeaderFontRole) -> str:
    """HTML 表头 ``<span style="...">`` 内联样式字符串（英文页面）。"""
    specs = merge_header_font_theme(theme)
    s = specs[role]
    fam = str(s['family']).replace("'", "\\'")
    wt = str(s['weight'])
    return (
        f"font-family:{fam},sans-serif;font-size:{int(s['size'])}px;"
        f"color:{s['color']};font-weight:{wt}"
    )


def resolve_font_size(
    backend: VisualBackend,
    role: FontRole,
    theme: Dict[str, Any],
) -> int:
    """
    将逻辑 theme 中的字号转译为指定后端、图元角色的实际像素字号。

    Parameters
    ----------
    backend : {'matplotlib', 'plotly'}
        渲染后端。
    role : str
        图元角色，见 FontRole。
    theme : dict
        逻辑主题，须含 font_size、title_font_size；可选 header_font_size、header_emphasis_font_size。

    Returns
    -------
    int
        实际 fontsize（像素级整数）。
    """
    base = int(theme.get('font_size', 10))
    title_sz = int(theme.get('title_font_size', 12))
    hb = int(theme.get('header_font_size', max(9, round(base * 1.1))))
    he = int(theme.get('header_emphasis_font_size', max(hb + 2, round(title_sz * 1.33))))
    # Y 轴刻度与 Y 轴标题比原逻辑小一号（静态图）；表头价格数字与 axis_ylabel 对齐
    mpl_tick = max(7, base - 1)
    mpl_ylab = max(7, base - 1)

    if backend == 'matplotlib':
        table: Dict[FontRole, int] = {
            'axis_tick': mpl_tick,
            'axis_title': mpl_tick,
            'axis_ylabel': mpl_ylab,
            'group_title': title_sz,
            'legend': base,
            'header_body': hb,
            'header_emphasis': he,
        }
    else:
        # Plotly：轴刻度/轴标题字号保持 +1；加粗在布局 font 中单独设置
        table = {
            'axis_tick': base + 1,
            'axis_title': base + 1,
            'axis_ylabel': base + 1,
            'group_title': title_sz,
            'legend': base,
            'header_body': hb,
            'header_emphasis': he,
        }
    return table[role]


def plotly_font_dict(size: int, *, color: str = '#000000', weight: str = 'bold') -> Dict[str, Any]:
    """Plotly 轴/标题用 font 字典（加粗）。"""
    return dict(size=size, color=color, family='Arial', weight=weight)


def theme_color_to_plotly_string(theme_val: Any, alpha: float = 1.0) -> str:
    """将 theme 中的颜色（tuple/str）转为 Plotly 可用的 rgb/rgba 字符串。"""
    if isinstance(theme_val, str):
        if alpha >= 1.0:
            return theme_val
        # 简单颜色名无法拆通道时直接返回
        if theme_val.startswith('#') and len(theme_val) == 7:
            r = int(theme_val[1:3], 16)
            g = int(theme_val[3:5], 16)
            b = int(theme_val[5:7], 16)
            return f'rgba({r},{g},{b},{alpha})'
        return theme_val
    if isinstance(theme_val, (list, tuple)) and len(theme_val) >= 3:
        r, g, b = float(theme_val[0]), float(theme_val[1]), float(theme_val[2])
        a = float(theme_val[3]) if len(theme_val) > 3 else 1.0
        return f'rgba({int(r * 255)},{int(g * 255)},{int(b * 255)},{min(1.0, a * alpha)})'
    return 'gray'


def resolve_candle_style_matplotlib(theme: Dict[str, Any]) -> Dict[str, Any]:
    """
    蜡烛图在 matplotlib 侧实际绘制参数（逻辑涨跌色 + 线宽等）。

    Returns
    -------
    dict
        line_color_up, line_color_down, wick_linewidth, body_edgewidth,
        doji_linewidth, bar_width。
    """
    return {
        'line_color_up': theme.get('line_color_up', 'red'),
        'line_color_down': theme.get('line_color_down', 'green'),
        'wick_linewidth': float(theme.get('candle_wick_linewidth', 0.8)),
        'body_edgewidth': float(theme.get('candle_body_edgewidth', 0.5)),
        'doji_linewidth': float(theme.get('candle_doji_linewidth', 1.0)),
        'bar_width': float(theme.get('candle_bar_width', 0.6)),
    }


def resolve_candle_style_plotly(theme: Dict[str, Any]) -> Dict[str, Any]:
    """
    蜡烛图在 Plotly Candlestick 上的实际参数（填充略透明以接近 mpl 实心块观感）。

    Returns
    -------
    dict
        increasing_line_color, decreasing_line_color,
        increasing_fillcolor, decreasing_fillcolor,
        increasing_line_width, decreasing_line_width, whiskerwidth。
    """
    up = theme.get('line_color_up', 'red')
    dn = theme.get('line_color_down', 'green')
    fill_alpha = float(theme.get('candle_plotly_fill_alpha', 0.82))
    line_w = float(theme.get('candle_plotly_line_width', 1.15))
    whisker = float(theme.get('candle_plotly_whiskerwidth', 0.18))
    return {
        'increasing_line_color': theme_color_to_plotly_string(up, 1.0),
        'decreasing_line_color': theme_color_to_plotly_string(dn, 1.0),
        'increasing_fillcolor': theme_color_to_plotly_string(up, fill_alpha),
        'decreasing_fillcolor': theme_color_to_plotly_string(dn, fill_alpha),
        'increasing_line_width': line_w,
        'decreasing_line_width': line_w,
        'whiskerwidth': whisker,
    }
