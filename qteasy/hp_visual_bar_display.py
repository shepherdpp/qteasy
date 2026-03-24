# coding=utf-8
# ======================================
# File:     hp_visual_bar_display.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-03-21
# Desc:
#   HistoryPanel 可视化：按组、按 bar 构建 OHLC 顶部展示区数据（与 Plotly/静态表头共用）。
# ======================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from qteasy.hp_visual_theme_adapt import HeaderFontRole


def specs_contain_kline(
    specs_per_group: Sequence[Sequence[Optional[Dict[str, Any]]]],
    types_info: Sequence[Any],
) -> bool:
    """是否存在任意一组的非空 K 线规格（决定是否显示 OHLC 表头）。"""
    for row in specs_per_group:
        for i, t in enumerate(types_info):
            if getattr(t, 'id', '') == 'kline' and i < len(row) and row[i] is not None:
                return True
    return False


def primary_kline_group_index(
    specs_per_group: Sequence[Sequence[Optional[Dict[str, Any]]]],
    types_info: Sequence[Any],
) -> Optional[int]:
    """第一个含 K 线规格的组索引；无 K 线时返回 None。"""
    for g, row in enumerate(specs_per_group):
        for i, t in enumerate(types_info):
            if getattr(t, 'id', '') == 'kline' and i < len(row) and row[i] is not None:
                return g
    return None


def build_bar_display_data(
    specs_per_group: Sequence[Sequence[Optional[Dict[str, Any]]]],
    types_info: Sequence[Any],
    x_dates: Sequence[Any],
    theme: Optional[Dict[str, Any]] = None,
    share_idx: int = 0,
) -> List[List[Dict[str, Any]]]:
    """
    为每组、每个时间索引构建顶部展示区所需的数据。

    含 close、date_str、open/high/low、volume、value、last_close、pct_change、涨跌停参考、MA 等。
    """
    from qteasy.hp_visual_render import _format_x_label, _get_theme, _to_1d

    theme = theme or _get_theme()
    fmt = theme.get('datetime_format', '%y/%m/%d')
    out: List[List[Dict[str, Any]]] = []
    n = len(x_dates) if x_dates else 0
    if n == 0:
        return out

    for g, row in enumerate(specs_per_group):
        group_data: List[Dict[str, Any]] = []
        kline_spec = next(
            (row[i] for i, t in enumerate(types_info) if t.id == 'kline' and row[i] is not None),
            None,
        )
        vol_spec = next(
            (row[i] for i, t in enumerate(types_info) if t.id == 'volume' and row[i] is not None),
            None,
        )

        o = h = l = c = None
        vol = None
        ma_dict: Dict[str, np.ndarray] = {}

        if kline_spec:
            data = kline_spec.get('data', {})
            for key in ('open', 'high', 'low', 'close'):
                if key in data:
                    arr = _to_1d(np.asarray(data[key]), share_idx)
                    if key == 'open':
                        o = arr[:n]
                    elif key == 'high':
                        h = arr[:n]
                    elif key == 'low':
                        l = arr[:n]
                    else:
                        c = arr[:n]
            for key in data:
                if key in ('open', 'high', 'low', 'close'):
                    continue
                if key.startswith('ma_') or key.startswith('sma_') or key.startswith('ema_'):
                    ma_dict[key] = _to_1d(np.asarray(data[key]), share_idx)[:n]

        if vol_spec:
            data = vol_spec.get('data', {})
            vol_name = next((k for k in ('vol', 'volume') if k in data), None)
            if vol_name:
                vol = _to_1d(np.asarray(data[vol_name]), share_idx)[:n]

        close_ary = c if c is not None else np.full(n, np.nan)
        last_close = np.roll(close_ary, 1)
        last_close[0] = np.nan

        for i in range(n):
            rec: Dict[str, Any] = {
                'date_str': _format_x_label(x_dates[i], fmt) if i < len(x_dates) else '',
                'close': float(close_ary[i]) if np.isfinite(close_ary[i]) else None,
                'open': float(o[i]) if o is not None and np.isfinite(o[i]) else None,
                'high': float(h[i]) if h is not None and np.isfinite(h[i]) else None,
                'low': float(l[i]) if l is not None and np.isfinite(l[i]) else None,
            }
            if vol is not None and np.isfinite(vol[i]):
                rec['volume'] = float(vol[i])
                rec['value'] = float(vol[i] * close_ary[i]) if np.isfinite(close_ary[i]) else None
            else:
                rec['volume'] = None
                rec['value'] = None

            lc = last_close[i]
            if np.isfinite(lc) and lc != 0:
                rec['last_close'] = float(lc)
                chg = close_ary[i] - lc
                rec['change'] = float(chg)
                rec['pct_change'] = float(chg / lc * 100)
                rec['upper_lim'] = float(lc * 1.1)
                rec['lower_lim'] = float(lc * 0.9)
            else:
                rec['last_close'] = None
                rec['change'] = None
                rec['pct_change'] = None
                rec['upper_lim'] = None
                rec['lower_lim'] = None

            rec['ma'] = {k: float(ma_dict[k][i]) for k in ma_dict if np.isfinite(ma_dict[k][i])}
            group_data.append(rec)
        out.append(group_data)
    return out


def ohlc_header_text_lines(rec: Dict[str, Any]) -> Tuple[str, str]:
    """
    静态 matplotlib 表头两行英文文本（与 Plotly 表头字段一致，便于双模对照）。

    Parameters
    ----------
    rec : dict
        单 bar 的 build_bar_display_data 记录。

    Returns
    -------
    tuple[str, str]
        第一行、第二行纯文本。
    """
    chg = rec.get('change')
    if chg is not None:
        sign = '+' if chg > 0 else ''
        chg_str = f'{sign}{chg:.3f}'
    else:
        chg_str = ''
    pct = rec.get('pct_change')
    pct_str = f' [{pct:+.3f}%]' if pct is not None else ''

    parts1: List[str] = []
    o, c = rec.get('open'), rec.get('close')
    if o is not None and c is not None:
        parts1.append(f'O/C {o:.2f} / {c:.2f}')
    if rec.get('high') is not None:
        parts1.append(f'H {rec["high"]:.3f}')
    if rec.get('volume') is not None:
        parts1.append(f'Vol(10k) {rec["volume"] / 1e4:.3f}')
    if rec.get('upper_lim') is not None:
        parts1.append(f'Up limit {rec["upper_lim"]:.3f}')
    if rec.get('ma'):
        v0 = next(iter(rec['ma'].values()))
        parts1.append(f'Avg {v0:.3f}')

    parts2: List[str] = []
    parts2.append(str(rec.get('date_str', '')))
    if chg_str:
        parts2.append(chg_str + pct_str)
    if rec.get('low') is not None:
        parts2.append(f'L {rec["low"]:.3f}')
    if rec.get('value') is not None:
        parts2.append(f'Turn(100M) {rec["value"] / 1e8:.3f}')
    if rec.get('lower_lim') is not None:
        parts2.append(f'Dn limit {rec["lower_lim"]:.3f}')
    if rec.get('last_close') is not None:
        parts2.append(f'Prev {rec["last_close"]:.3f}')

    return '  |  '.join(parts1) if parts1 else '', '  |  '.join(parts2) if parts2 else ''


def mpl_ohlc_header_segments(
    rec: Dict[str, Any],
) -> Tuple[List[Tuple[str, HeaderFontRole]], List[Tuple[str, HeaderFontRole]]]:
    """
    静态/交互表头共用分段：每段为 (text, HeaderFontRole)。

    七种角色与 theme 中 ``header_font_*`` 对齐：组标题用 ``header_title``（本函数不含）；
    标签名 ``header_normal_label``；开/收 ``header_large_red/green``；其余价格
    ``header_small_red/green``；与涨跌无关数字 ``header_normal``。
    """
    NL = 'header_normal_label'
    LR = 'header_large_red'
    LG = 'header_large_green'
    SR = 'header_small_red'
    SG = 'header_small_green'
    NM = 'header_normal'

    chg = rec.get('change')
    o, c = rec.get('open'), rec.get('close')
    bar_up = o is not None and c is not None and c >= o
    large_up = LR if bar_up else LG

    line1: List[Tuple[str, HeaderFontRole]] = []
    line2: List[Tuple[str, HeaderFontRole]] = []
    first = True

    if o is not None and c is not None:
        line1.append(('O/C ', NL))
        line1.append((f'{o:.2f}', large_up))
        line1.append((' / ', NL))
        line1.append((f'{c:.2f}', large_up))
        first = False
    if rec.get('high') is not None:
        if not first:
            line1.append(('  |  ', NL))
        line1.append(('H ', NL))
        line1.append((f'{rec["high"]:.3f}', SR))
        first = False
    if rec.get('volume') is not None:
        if not first:
            line1.append(('  |  ', NL))
        line1.append(('Vol(10k) ', NL))
        line1.append((f'{rec["volume"] / 1e4:.3f}', NM))
        first = False
    if rec.get('upper_lim') is not None:
        if not first:
            line1.append(('  |  ', NL))
        line1.append(('Up limit ', NL))
        line1.append((f'{rec["upper_lim"]:.3f}', SR))
        first = False
    if rec.get('ma'):
        v0 = next(iter(rec['ma'].values()))
        if not first:
            line1.append(('  |  ', NL))
        line1.append(('Avg ', NL))
        line1.append((f'{v0:.3f}', NM))

    first2 = True
    ds = str(rec.get('date_str', ''))
    if ds:
        line2.append((ds, NM))
        first2 = False
    if chg is not None:
        sign = '+' if chg > 0 else ''
        chg_str = f'{sign}{chg:.3f}'
        pct = rec.get('pct_change')
        pct_str = f' [{pct:+.3f}%]' if pct is not None else ''
        if not first2:
            line2.append(('  |  ', NL))
        chg_role: HeaderFontRole = SR if chg > 0 else (SG if chg < 0 else NM)
        line2.append((chg_str + pct_str, chg_role))
        first2 = False
    if rec.get('low') is not None:
        if not first2:
            line2.append(('  |  ', NL))
        line2.append(('L ', NL))
        line2.append((f'{rec["low"]:.3f}', SG))
        first2 = False
    if rec.get('value') is not None:
        if not first2:
            line2.append(('  |  ', NL))
        line2.append(('Turn(100M) ', NL))
        line2.append((f'{rec["value"] / 1e8:.3f}', NM))
        first2 = False
    if rec.get('lower_lim') is not None:
        if not first2:
            line2.append(('  |  ', NL))
        line2.append(('Dn limit ', NL))
        line2.append((f'{rec["lower_lim"]:.3f}', SG))
        first2 = False
    if rec.get('last_close') is not None:
        if not first2:
            line2.append(('  |  ', NL))
        line2.append(('Prev ', NL))
        line2.append((f'{rec["last_close"]:.3f}', NM))

    return line1, line2
