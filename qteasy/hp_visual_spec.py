# coding=utf-8
# ======================================
# File:     hp_visual_spec.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-03-13
# Desc:
#   HistoryPanel 可视化规格：图表类型注册表与规格生成器。
#   仅根据 HP 已有 htypes 决定图表类型与规格，不计算、不扩展数据。
# ======================================

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np

from qteasy.history import HistoryPanel

# 重要性等级：仅 main / secondary；编排层用 main×2、secondary×0.5 分配高度
ChartTypeImportance = Literal['main', 'secondary']


@dataclass
class ChartTypeInfo:
    """注册表单项：图表类型标识、必需/可选 htype、匹配器、重要性与顺序。"""

    id: str
    importance: ChartTypeImportance
    order: int
    required_htypes: Optional[Sequence[str]] = None
    htype_matcher: Optional[Callable[[Sequence[str]], Optional[Sequence[str]]]] = None

    def is_applicable(self, htypes: Sequence[str]) -> Optional[Sequence[str]]:
        """若当前 htypes 满足该图表类型，返回使用的列名序列；否则返回 None。"""
        if self.required_htypes:
            hset = set(htypes)
            if not all(r in hset for r in self.required_htypes):
                return None
            return list(self.required_htypes)
        if self.htype_matcher:
            return self.htype_matcher(list(htypes))
        return None


def _match_macd_htypes(htypes: Sequence[str]) -> Optional[Tuple[str, str, str]]:
    """从 htypes 中识别一组完整 MACD 三列（macd_*, macd_signal_*, macd_hist_*，tag 一致）。"""
    macd_cols: List[str] = []
    signal_cols: List[str] = []
    hist_cols: List[str] = []
    for h in htypes:
        if h.startswith('macd_') and not h.startswith('macd_signal_') and not h.startswith('macd_hist_'):
            macd_cols.append(h)
        elif h.startswith('macd_signal_'):
            signal_cols.append(h)
        elif h.startswith('macd_hist_'):
            hist_cols.append(h)
    for m in macd_cols:
        tag = m[5:]  # after 'macd_'
        sig = f'macd_signal_{tag}'
        hist = f'macd_hist_{tag}'
        if sig in signal_cols and hist in hist_cols:
            return (m, sig, hist)
    return None


def _match_bbands_htypes(htypes: Sequence[str]) -> Optional[Tuple[str, str, str]]:
    """从 htypes 中识别一组完整布林带三列（bbands_upper_*, bbands_middle_*, bbands_lower_*，tag 一致）。"""
    seen: Dict[str, List[str]] = {}
    for h in htypes:
        for prefix in ('bbands_upper_', 'bbands_middle_', 'bbands_lower_'):
            if h.startswith(prefix):
                tag = h[len(prefix):]
                if tag not in seen:
                    seen[tag] = []
                seen[tag].append(h)
                break
    for tag, names in seen.items():
        if len(names) != 3:
            continue
        u = next((n for n in names if n.startswith('bbands_upper_')), None)
        m = next((n for n in names if n.startswith('bbands_middle_')), None)
        l = next((n for n in names if n.startswith('bbands_lower_')), None)
        if u and m and l:
            return (u, m, l)
    return None


def _macd_matcher(htypes: Sequence[str]) -> Optional[Sequence[str]]:
    t = _match_macd_htypes(htypes)
    return list(t) if t else None


# 固定列名：K 线必需 OHLC（根名）；面板上可为裸名或复权列如 open|b、close|f
OHLC = ('open', 'high', 'low', 'close')

# 成交量列名（任选其一）
VOL_NAMES = ('vol', 'volume')


def _split_ohlc_htype(h: str) -> Optional[Tuple[str, str]]:
    """若 h 为价格 OHLC 根名或 root|后缀，返回 (根名, 后缀)；后缀为 '' 或 '|b' 等。"""
    for root in OHLC:
        if h == root:
            return (root, '')
        if h.startswith(root + '|'):
            return (root, h[len(root):])
    return None


def _match_ohlc_family(htypes: Sequence[str]) -> Optional[Tuple[str, str, str, str]]:
    """从 htypes 中选出一套完整 OHLC 列名（同后缀族），顺序 open, high, low, close。

    优先级：无后缀 > |b > |f > 其余后缀字典序。若无任何一族凑齐四列则返回 None。
    """
    groups: Dict[str, Dict[str, str]] = defaultdict(dict)
    for h in htypes:
        sp = _split_ohlc_htype(h)
        if sp is None:
            continue
        root, suf = sp
        groups[suf][root] = h

    def complete(suf: str) -> bool:
        g = groups.get(suf, {})
        return all(r in g for r in OHLC)

    for suf in ('', '|b', '|f'):
        if complete(suf):
            g = groups[suf]
            return (g['open'], g['high'], g['low'], g['close'])
    for suf in sorted(k for k in groups if k not in ('', '|b', '|f')):
        if complete(suf):
            g = groups[suf]
            return (g['open'], g['high'], g['low'], g['close'])
    return None


def _kline_htype_matcher(htypes: Sequence[str]) -> Optional[Sequence[str]]:
    """K 线注册用：返回实际四列名（open→high→low→close 顺序），不满足则 None。"""
    t = _match_ohlc_family(htypes)
    return list(t) if t else None


def _build_default_registry() -> List[ChartTypeInfo]:
    """构建默认图表类型注册表（顺序：kline → volume → macd → line）。"""
    return [
        ChartTypeInfo(
            id='kline',
            required_htypes=None,
            htype_matcher=_kline_htype_matcher,
            importance='main',
            order=0,
        ),
        ChartTypeInfo(
            id='volume',
            required_htypes=None,
            htype_matcher=lambda h: [v] if (v := next((x for x in VOL_NAMES if x in h), None)) else None,
            importance='secondary',
            order=1,
        ),
        ChartTypeInfo(
            id='macd',
            required_htypes=None,
            htype_matcher=_macd_matcher,
            importance='secondary',
            order=2,
        ),
        ChartTypeInfo(
            id='line',
            required_htypes=None,
            htype_matcher=lambda h: None,  # line 在 get_applicable_types 中按「剩余 htypes」单独加入
            importance='secondary',
            order=3,
        ),
    ]


class ChartTypeRegistry:
    """图表类型注册表：根据 htypes 返回适用的图表类型列表（含重要性、有序）。"""

    def __init__(self, types: Optional[Sequence[ChartTypeInfo]] = None):
        self._types = list(types) if types is not None else _build_default_registry()
        self._types.sort(key=lambda t: t.order)

    def get_applicable_types(self, htypes: Sequence[str]) -> List[ChartTypeInfo]:
        """返回当前 htypes 下适用的图表类型列表，保持 order 有序。"""
        hlist = list(htypes)
        result: List[ChartTypeInfo] = []
        used_htypes: set = set()

        for info in self._types:
            if info.id == 'line':
                continue
            used = info.is_applicable(hlist)
            if used is None:
                continue
            if info.id == 'kline':
                used_htypes.update(used)
                for h in hlist:
                    if h in used_htypes:
                        continue
                    if re.match(r'^ma_', h) or re.match(r'^sma_[0-9]+', h) or re.match(r'^ema_[0-9]+', h):
                        used_htypes.add(h)
                    elif h.startswith('bbands_upper_') or h.startswith('bbands_middle_') or h.startswith('bbands_lower_'):
                        used_htypes.add(h)
                bbands = _match_bbands_htypes(hlist)
                if bbands:
                    used_htypes.update(bbands)
            elif info.id == 'volume':
                used_htypes.update(used)
            elif info.id == 'macd':
                used_htypes.update(used)
            result.append(info)

        # line：剩余 htypes 或全部（当无 kline 时折线为 main）
        remaining = [h for h in hlist if h not in used_htypes]
        if remaining:
            line_info = next((t for t in self._types if t.id == 'line'), None)
            if line_info:
                has_kline = any(t.id == 'kline' for t in result)
                imp: ChartTypeImportance = 'secondary' if has_kline else 'main'
                result.append(ChartTypeInfo(
                    id='line',
                    required_htypes=None,
                    htype_matcher=None,
                    importance=imp,
                    order=line_info.order,
                ))
        return result


# 全局单例
_registry: Optional[ChartTypeRegistry] = None


def get_chart_type_registry() -> ChartTypeRegistry:
    """获取图表类型注册表单例。"""
    global _registry
    if _registry is None:
        _registry = ChartTypeRegistry()
    return _registry


def _hp_slice_htype(hp: HistoryPanel, htype: str, shares: Optional[Sequence[str]] = None) -> np.ndarray:
    """从 HP 中切片出单列 htype 数据，形状 (n_share, n_time)。"""
    if hp.is_empty or htype not in hp.htypes:
        raise ValueError(f'htype "{htype}" not in panel htypes: {hp.htypes}')
    ci = hp.htypes.index(htype)
    arr = np.asarray(hp.values[:, :, ci], dtype=float)
    if shares is not None:
        share_set = set(shares)
        idx = [i for i, s in enumerate(hp.shares) if s in share_set]
        if idx:
            arr = arr[idx, :]
    return arr


def build_kline_spec(
    hp: HistoryPanel,
    shares: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    若 HP 中存在一整套 OHLC（裸名或同后缀复权列如 open|b…close|b）则返回 K 线规格，否则 None。

    规格 ``data`` 中仍使用标准键 open/high/low/close，数值来自匹配到的实际列切片。
    可选叠加 ma_*、bbands_* 列；不包含 vol/volume。
    """
    if hp.is_empty:
        return None
    htypes = list(hp.htypes)
    ohlc_cols = _match_ohlc_family(htypes)
    if ohlc_cols is None:
        return None
    data: Dict[str, np.ndarray] = {}
    htypes_used: List[str] = []
    for canon, actual in zip(OHLC, ohlc_cols):
        data[canon] = _hp_slice_htype(hp, actual, shares)
        htypes_used.append(actual)
    for h in htypes:
        if h in data:
            continue
        if re.match(r'^ma_', h) or re.match(r'^sma_[0-9]+', h) or re.match(r'^ema_[0-9]+', h):
            data[h] = _hp_slice_htype(hp, h, shares)
            htypes_used.append(h)
    bbands = _match_bbands_htypes(htypes)
    if bbands:
        for b in bbands:
            if b not in data:
                data[b] = _hp_slice_htype(hp, b, shares)
                htypes_used.append(b)
    return {
        'chart_type': 'kline',
        'importance': 'main',
        'htypes_used': htypes_used,
        'data': data,
    }


def build_volume_spec(
    hp: HistoryPanel,
    shares: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    """若 HP 包含 vol 或 volume 则返回成交量柱状图规格片段，否则返回 None。"""
    if hp.is_empty:
        return None
    vol_name = next((v for v in VOL_NAMES if v in hp.htypes), None)
    if vol_name is None:
        return None
    data = {vol_name: _hp_slice_htype(hp, vol_name, shares)}
    return {
        'chart_type': 'volume',
        'importance': 'secondary',
        'htypes_used': [vol_name],
        'data': data,
    }


def build_macd_spec(
    hp: HistoryPanel,
    shares: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    """若 HP 包含一组完整 MACD 三列（命名与 kline.macd() 一致）则返回规格，否则返回 None。"""
    if hp.is_empty:
        return None
    triple = _match_macd_htypes(hp.htypes)
    if triple is None:
        return None
    macd_col, signal_col, hist_col = triple
    data: Dict[str, np.ndarray] = {}
    for c in triple:
        data[c] = _hp_slice_htype(hp, c, shares)
    series_kind = {
        macd_col: 'line',
        signal_col: 'line',
        hist_col: 'bar',
    }
    return {
        'chart_type': 'macd',
        'importance': 'secondary',
        'htypes_used': list(triple),
        'data': data,
        'series_kind': series_kind,
    }


def build_line_spec(
    hp: HistoryPanel,
    shares: Optional[Sequence[str]] = None,
    htypes: Optional[Sequence[str]] = None,
    consumed_htypes: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    折线/面积规格：用于未被 kline/volume/macd 占用的 htype，或仅存在此类 htype 时。
    consumed_htypes：已被其他图表类型占用的列，若不传则根据 HP 自动推断（kline/volume/macd 占用的）。
    """
    if hp.is_empty:
        return None
    all_htypes = list(hp.htypes)
    if consumed_htypes is None:
        consumed = set()
        ohlc_family = _match_ohlc_family(all_htypes)
        if ohlc_family is not None:
            consumed.update(ohlc_family)
            bbands_triple = _match_bbands_htypes(all_htypes)
            if bbands_triple:
                consumed.update(bbands_triple)
            for h in all_htypes:
                if re.match(r'^ma_', h) or re.match(r'^sma_[0-9]+', h) or re.match(r'^ema_[0-9]+', h):
                    consumed.add(h)
        for v in VOL_NAMES:
            if v in all_htypes:
                consumed.add(v)
        macd_triple = _match_macd_htypes(all_htypes)
        if macd_triple:
            consumed.update(macd_triple)
    else:
        consumed = set(consumed_htypes)
    if htypes is not None:
        line_htypes = [h for h in htypes if h in all_htypes and h not in consumed]
    else:
        line_htypes = [h for h in all_htypes if h not in consumed]
    if not line_htypes:
        return None
    has_kline = _match_ohlc_family(all_htypes) is not None
    importance: ChartTypeImportance = 'secondary' if has_kline else 'main'
    data: Dict[str, np.ndarray] = {}
    for h in line_htypes:
        data[h] = _hp_slice_htype(hp, h, shares)
    return {
        'chart_type': 'line',
        'importance': importance,
        'htypes_used': line_htypes,
        'data': data,
    }
