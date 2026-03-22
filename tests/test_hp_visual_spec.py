# coding=utf-8
# ======================================
# File:     test_hp_visual_spec.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-03-13
# Desc:
#   Unittest for HistoryPanel 可视化规格：图表类型注册表与规格生成器（Phase 1）.
# ======================================

import unittest
import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel
from qteasy.hp_visual_spec import (
    ChartTypeInfo,
    ChartTypeRegistry,
    get_chart_type_registry,
    build_kline_spec,
    build_volume_spec,
    build_macd_spec,
    build_line_spec,
)
from qteasy.hp_visual_render import (
    render_spec,
    render_kline_spec,
    render_volume_spec,
    render_macd_spec,
    render_line_spec,
)


def _make_hp(htypes: list, n_shares: int = 1, n_dates: int = 20) -> HistoryPanel:
    """构造小型 HistoryPanel，形状 (n_shares, n_dates, len(htypes))，数值为简单序列。"""
    n = len(htypes)
    values = np.tile(np.arange(n_dates, dtype=float).reshape(1, -1), (n_shares, 1))
    values = np.stack([values + i * 0.1 for i in range(n)], axis=2)
    shares = [f'S{i:03d}' for i in range(n_shares)]
    rows = pd.date_range('2020-01-01', periods=n_dates, freq='B')
    return HistoryPanel(values=values, levels=shares, rows=rows, columns=htypes)


def _specs_per_group_stack_two_shares(hp: HistoryPanel):
    """
    模拟 ``HistoryPanel.plot(..., layout='stack')`` 且两只 share 时的
    ``specs_per_group`` / ``types_info`` / ``group_titles``，供交互图单测。
    """
    registry = get_chart_type_registry()
    types_info = registry.get_applicable_types(hp.htypes)
    share_list = list(hp.shares)
    if len(share_list) < 2:
        raise ValueError('need at least 2 shares')
    groups = [[share_list[0]], [share_list[1]]]
    specs_per_group = []
    group_titles = []
    for grp in groups:
        row = []
        for info in types_info:
            tid = info.id
            if tid == 'kline':
                spec = build_kline_spec(hp, shares=grp)
            elif tid == 'volume':
                spec = build_volume_spec(hp, shares=grp)
            elif tid == 'macd':
                spec = build_macd_spec(hp, shares=grp)
            else:
                spec = build_line_spec(hp, shares=grp)
            row.append(spec)
        kline_idx = next((i for i, t in enumerate(types_info) if t.id == 'kline'), None)
        vol_idx = next((i for i, t in enumerate(types_info) if t.id == 'volume'), None)
        if (
            kline_idx is not None and vol_idx is not None
            and row[kline_idx] is not None and row[vol_idx] is not None
            and 'open' in row[kline_idx].get('data', {}) and 'close' in row[kline_idx].get('data', {})
        ):
            vol_spec = dict(row[vol_idx])
            vol_spec['data'] = dict(vol_spec.get('data', {}))
            vol_spec['data']['open'] = row[kline_idx]['data']['open']
            vol_spec['data']['close'] = row[kline_idx]['data']['close']
            row[vol_idx] = vol_spec
        specs_per_group.append(row)
        group_titles.append(grp[0] if len(grp) == 1 else ','.join(grp[:3]))
    return specs_per_group, types_info, group_titles


class TestChartTypeRegistry(unittest.TestCase):
    """注册表：get_applicable_types 返回类型及重要性."""

    def setUp(self):
        self.registry = get_chart_type_registry()
        print('\n[TestChartTypeRegistry] using default registry')

    def test_registry_ohlc_returns_kline_main(self):
        print('\n[P1-1] 注册表：仅 OHLC 返回 kline(main)，无 volume/macd')
        htypes = ['open', 'high', 'low', 'close']
        result = self.registry.get_applicable_types(htypes)
        ids = [t.id for t in result]
        self.assertIn('kline', ids)
        k = next(t for t in result if t.id == 'kline')
        self.assertEqual(k.importance, 'main')
        self.assertNotIn('volume', ids)
        self.assertNotIn('macd', ids)
        print('  applicable:', ids, 'kline importance:', k.importance)

    def test_registry_ohlc_vol_returns_kline_and_volume(self):
        print('\n[P1-2] 注册表：OHLC+vol 返回 kline(main)、volume(secondary)，顺序 kline 在前')
        htypes = ['open', 'high', 'low', 'close', 'vol']
        result = self.registry.get_applicable_types(htypes)
        ids = [t.id for t in result]
        self.assertIn('kline', ids)
        self.assertIn('volume', ids)
        self.assertLess(ids.index('kline'), ids.index('volume'))
        k = next(t for t in result if t.id == 'kline')
        v = next(t for t in result if t.id == 'volume')
        self.assertEqual(k.importance, 'main')
        self.assertEqual(v.importance, 'secondary')
        print('  order:', ids, 'kline=', k.importance, 'volume=', v.importance)

    def test_registry_only_open_high_returns_line_not_kline(self):
        print('\n[P1-3] 注册表：仅 open+high 不返回 kline，折线适用 open/high，importance main')
        htypes = ['open', 'high']
        result = self.registry.get_applicable_types(htypes)
        ids = [t.id for t in result]
        self.assertNotIn('kline', ids)
        self.assertIn('line', ids)
        line = next(t for t in result if t.id == 'line')
        self.assertEqual(line.importance, 'main')
        print('  applicable:', ids, 'line importance:', line.importance)

    def test_registry_only_close_returns_line_main(self):
        print('\n[P1-4] 注册表：仅 close 返回 line(main)，无 kline/volume/macd')
        htypes = ['close']
        result = self.registry.get_applicable_types(htypes)
        ids = [t.id for t in result]
        self.assertNotIn('kline', ids)
        self.assertNotIn('volume', ids)
        self.assertNotIn('macd', ids)
        self.assertIn('line', ids)
        line = next(t for t in result if t.id == 'line')
        self.assertEqual(line.importance, 'main')
        print('  applicable:', ids)

    def test_registry_ohlc_vol_macd_returns_three_types(self):
        print('\n[P1-5] 注册表：OHLC+vol+MACD 模式匹配返回 kline(main)、volume、macd(secondary)')
        htypes = [
            'open', 'high', 'low', 'close', 'vol',
            'macd_12_26_9', 'macd_signal_12_26_9', 'macd_hist_12_26_9',
        ]
        result = self.registry.get_applicable_types(htypes)
        ids = [t.id for t in result]
        self.assertIn('kline', ids)
        self.assertIn('volume', ids)
        self.assertIn('macd', ids)
        self.assertLess(ids.index('kline'), ids.index('volume'))
        self.assertLess(ids.index('volume'), ids.index('macd'))
        print('  applicable:', ids)


class TestKlineSpecBuilder(unittest.TestCase):
    """K 线规格生成器：OHLC 必选，不含 vol；仅 open+high 或缺 close 返回 None."""

    def test_kline_spec_ohlc_no_vol(self):
        print('\n[P1-6] K 线规格：OHLC 无 vol，片段不含成交量，chart_type=kline importance=main')
        hp = _make_hp(['open', 'high', 'low', 'close'])
        spec = build_kline_spec(hp)
        self.assertIsNotNone(spec)
        self.assertEqual(spec['chart_type'], 'kline')
        self.assertEqual(spec['importance'], 'main')
        self.assertNotIn('vol', spec.get('data', {}))
        self.assertNotIn('volume', spec.get('data', {}))
        self.assertIn('open', spec['data'])
        self.assertIn('close', spec['data'])
        print('  chart_type:', spec['chart_type'], 'keys:', list(spec['data'].keys()))

    def test_kline_spec_ohlc_vol_separate_volume_spec(self):
        print('\n[P1-7] K 线+成交量：K 线片段仅 OHLC，volume 由 build_volume_spec 单独返回')
        hp = _make_hp(['open', 'high', 'low', 'close', 'vol'])
        kspec = build_kline_spec(hp)
        vspec = build_volume_spec(hp)
        self.assertIsNotNone(kspec)
        self.assertIsNotNone(vspec)
        self.assertNotIn('vol', kspec['data'])
        self.assertNotIn('volume', kspec['data'])
        self.assertIn('vol', vspec['data'])
        print('  kline data keys:', list(kspec['data'].keys()), 'volume data keys:', list(vspec['data'].keys()))

    def test_kline_spec_only_open_high_returns_none(self):
        print('\n[P1-8] K 线规格：仅 open+high 不产出 K 线，返回 None')
        hp = _make_hp(['open', 'high'])
        spec = build_kline_spec(hp)
        self.assertIsNone(spec)
        line_spec = build_line_spec(hp)
        self.assertIsNotNone(line_spec)
        self.assertIn('open', line_spec['htypes_used'])
        self.assertIn('high', line_spec['htypes_used'])
        print('  kline_spec:', spec, 'line_spec htypes_used:', line_spec['htypes_used'])

    def test_kline_spec_missing_close_returns_none(self):
        print('\n[P1-9] K 线规格：缺 close 不产出 K 线')
        hp = _make_hp(['open', 'high', 'low'])
        spec = build_kline_spec(hp)
        self.assertIsNone(spec)
        print('  build_kline_spec(hp):', spec)


class TestVolumeSpecBuilder(unittest.TestCase):
    """成交量规格生成器."""

    def test_volume_spec_has_vol(self):
        print('\n[P1-10] 成交量规格：HP 含 vol 则返回 volume 片段，importance=secondary')
        hp = _make_hp(['close', 'vol'])
        spec = build_volume_spec(hp)
        self.assertIsNotNone(spec)
        self.assertEqual(spec['chart_type'], 'volume')
        self.assertEqual(spec['importance'], 'secondary')
        print('  chart_type:', spec['chart_type'], 'importance:', spec['importance'])

    def test_volume_spec_no_vol_returns_none(self):
        print('\n[P1-11] 成交量规格：HP 不含 vol/volume 返回 None')
        hp = _make_hp(['open', 'high', 'low', 'close'])
        spec = build_volume_spec(hp)
        self.assertIsNone(spec)
        print('  build_volume_spec(hp):', spec)


class TestMacdSpecBuilder(unittest.TestCase):
    """MACD 规格生成器：模式匹配三列，缺一列则 None."""

    def test_macd_spec_three_cols_ok(self):
        print('\n[P1-12] MACD 规格：与 macd() 输出一致的三列齐全则非 None，能区分柱/线')
        htypes = ['macd_12_26_9', 'macd_signal_12_26_9', 'macd_hist_12_26_9']
        hp = _make_hp(htypes)
        spec = build_macd_spec(hp)
        self.assertIsNotNone(spec)
        self.assertEqual(spec['chart_type'], 'macd')
        self.assertIn('series_kind', spec)
        for col in htypes:
            self.assertIn(col, spec['data'])
            self.assertIn(spec['series_kind'][col], ('line', 'bar'))
        print('  series_kind:', spec['series_kind'])

    def test_macd_spec_missing_one_returns_none(self):
        print('\n[P1-13] MACD 规格：仅两列则 None')
        hp = _make_hp(['macd_12_26_9', 'macd_signal_12_26_9'])
        spec = build_macd_spec(hp)
        self.assertIsNone(spec)
        print('  build_macd_spec(hp):', spec)


class TestLineSpecBuilder(unittest.TestCase):
    """折线规格：仅 close、open+high 等."""

    def test_line_spec_only_close(self):
        print('\n[P1-14] 折线规格：仅 close 可产出折线片段，无 K 线时 importance=main')
        hp = _make_hp(['close'])
        spec = build_line_spec(hp)
        self.assertIsNotNone(spec)
        self.assertIn('close', spec['htypes_used'])
        self.assertEqual(spec['importance'], 'main')
        print('  htypes_used:', spec['htypes_used'], 'importance:', spec['importance'])

    def test_line_spec_open_high_no_ohlc(self):
        print('\n[P1-15] 折线规格：仅 open+high 时折线覆盖两条线，K 线规格为 None')
        hp = _make_hp(['open', 'high'])
        kspec = build_kline_spec(hp)
        line_spec = build_line_spec(hp)
        self.assertIsNone(kspec)
        self.assertIsNotNone(line_spec)
        self.assertIn('open', line_spec['htypes_used'])
        self.assertIn('high', line_spec['htypes_used'])
        self.assertEqual(len(line_spec['data']), 2)
        print('  line_spec htypes_used:', line_spec['htypes_used'])


class TestQ01AdjOhlcKline(unittest.TestCase):
    """Q01：复权列名 open|b…close|b 下 K 线注册与规格；裸价与复权并存时优先裸价族。"""

    def setUp(self):
        self.registry = get_chart_type_registry()

    def test_q01_registry_back_adj_ohlc_returns_kline_volume_order(self):
        print('\n[Q01-1] 注册表：open|b…close|b+vol 适用 kline(main)、volume，顺序正确')
        htypes = ['open|b', 'high|b', 'low|b', 'close|b', 'vol']
        result = self.registry.get_applicable_types(htypes)
        ids = [t.id for t in result]
        self.assertIn('kline', ids)
        self.assertIn('volume', ids)
        self.assertLess(ids.index('kline'), ids.index('volume'))
        print('  applicable:', ids)

    def test_q01_kline_spec_back_adj_data_keys_and_values(self):
        print('\n[Q01-2] K 线规格：后复权四列 -> data 仍为 open…close 键，数值等于 HP 对应列')
        htypes = ['open|b', 'high|b', 'low|b', 'close|b']
        hp = _make_hp(htypes)
        spec = build_kline_spec(hp)
        self.assertIsNotNone(spec)
        self.assertEqual(spec['chart_type'], 'kline')
        for canon in ('open', 'high', 'low', 'close'):
            self.assertIn(canon, spec['data'])
        self.assertEqual(
            spec['htypes_used'],
            ['open|b', 'high|b', 'low|b', 'close|b'],
        )
        for canon, actual in zip(
            ('open', 'high', 'low', 'close'),
            ('open|b', 'high|b', 'low|b', 'close|b'),
        ):
            ci = hp.htypes.index(actual)
            np.testing.assert_array_almost_equal(
                spec['data'][canon],
                hp.values[:, :, ci].astype(float),
            )
        print('  htypes_used:', spec['htypes_used'])

    def test_q01_kline_prefers_bare_ohlc_when_both_suffix_and_bare_exist(self):
        print('\n[Q01-3] 裸 OHLC 与 |b 全套并存时，K 线选用裸名四列')
        htypes = ['open', 'high', 'low', 'close', 'open|b', 'high|b', 'low|b', 'close|b']
        hp = _make_hp(htypes)
        spec = build_kline_spec(hp)
        self.assertIsNotNone(spec)
        self.assertEqual(spec['htypes_used'], ['open', 'high', 'low', 'close'])
        ci_open = hp.htypes.index('open')
        np.testing.assert_array_almost_equal(
            spec['data']['open'],
            hp.values[:, :, ci_open].astype(float),
        )
        print('  selected htypes_used:', spec['htypes_used'])

    def test_q01_line_spec_excludes_kline_adj_columns(self):
        print('\n[Q01-4] 仅后复权四列时折线规格不包含 OHLC（避免与 K 线重复）')
        htypes = ['open|b', 'high|b', 'low|b', 'close|b']
        hp = _make_hp(htypes)
        self.assertIsNotNone(build_kline_spec(hp))
        line_spec = build_line_spec(hp)
        self.assertIsNone(line_spec)
        print('  build_line_spec:', line_spec)

    def test_q01_render_kline_back_adj_smoke(self):
        print('\n[Q01-5] 后复权 K 线规格 + 静态 render_kline_spec 烟测')
        hp = _make_hp(['open|b', 'high|b', 'low|b', 'close|b'])
        spec = build_kline_spec(hp)
        self.assertIsNotNone(spec)
        fig = render_kline_spec(spec)
        self.assertEqual(len(fig.axes), 1)
        print('  axes count:', len(fig.axes))


class TestSpecDataFromHpOnly(unittest.TestCase):
    """规格数据仅来自 HP 切片，无额外计算."""

    def test_spec_values_match_hp_values(self):
        print('\n[P1-16] 规格数据与 hp.values 对应切片一致')
        hp = _make_hp(['open', 'high', 'low', 'close'], n_shares=2, n_dates=10)
        kspec = build_kline_spec(hp)
        self.assertIsNotNone(kspec)
        for h in ['open', 'close']:
            col_idx = hp.htypes.index(h)
            expected = hp.values[:, :, col_idx].astype(float)
            np.testing.assert_array_almost_equal(kspec['data'][h], expected)
        print('  kline data open shape:', kspec['data']['open'].shape, 'hp.values slice shape:', hp.values[:, :, 0].shape)


class TestKlineOptionalMaBbands(unittest.TestCase):
    """K 线可选 ma/bbands 叠加；仅 ma 或仅 bbands 无 OHLC 不产出 K 线."""

    def test_kline_spec_ohlc_with_ma_or_bbands(self):
        print('\n[P1-17] K 线规格：OHLC+ma/bbands 可选叠加，htypes_used 含对应列名')
        hp = _make_hp(['open', 'high', 'low', 'close', 'sma_20'])
        spec = build_kline_spec(hp)
        self.assertIsNotNone(spec)
        self.assertIn('sma_20', spec['htypes_used'])
        self.assertIn('sma_20', spec['data'])
        hp2 = _make_hp(['open', 'high', 'low', 'close', 'bbands_upper_20_2_2', 'bbands_middle_20_2_2', 'bbands_lower_20_2_2'])
        spec2 = build_kline_spec(hp2)
        self.assertIsNotNone(spec2)
        for b in ['bbands_upper_20_2_2', 'bbands_middle_20_2_2', 'bbands_lower_20_2_2']:
            self.assertIn(b, spec2['htypes_used'])
        print('  kline with sma_20 htypes_used:', spec['htypes_used'])

    def test_kline_spec_only_ma_or_only_bbands_returns_none(self):
        print('\n[P1-18] 仅 ma 或仅 bbands 无 OHLC 不产出 K 线，折线可承接')
        hp_ma = _make_hp(['sma_20'])
        spec_ma = build_kline_spec(hp_ma)
        self.assertIsNone(spec_ma)
        line_ma = build_line_spec(hp_ma)
        self.assertIsNotNone(line_ma)
        self.assertIn('sma_20', line_ma['htypes_used'])
        hp_bb = _make_hp(['bbands_upper_20_2_2', 'bbands_middle_20_2_2', 'bbands_lower_20_2_2'])
        spec_bb = build_kline_spec(hp_bb)
        self.assertIsNone(spec_bb)
        line_bb = build_line_spec(hp_bb)
        self.assertIsNotNone(line_bb)
        self.assertEqual(len(line_bb['htypes_used']), 3)
        print('  only sma_20 -> kline:', spec_ma, 'line htypes:', line_ma['htypes_used'])


class TestStaticRender(unittest.TestCase):
    """Phase 2：静态渲染层 — 给定规格+数据→Figure，返回类型与轴数量符合预期。"""

    def test_render_kline_returns_figure_one_axes(self):
        print('\n[Phase2] 单类型单 share：K 线规格渲染返回 Figure，至少 1 个 axes')
        hp = _make_hp(['open', 'high', 'low', 'close'])
        spec = build_kline_spec(hp)
        self.assertIsNotNone(spec)
        fig = render_kline_spec(spec)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  figure type:', type(fig).__name__, 'n_axes:', len(fig.axes))

    def test_render_volume_returns_figure_one_axes(self):
        print('\n[Phase2] 成交量规格渲染返回 Figure，至少 1 个 axes')
        hp = _make_hp(['close', 'vol'])
        spec = build_volume_spec(hp)
        self.assertIsNotNone(spec)
        fig = render_volume_spec(spec)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))

    def test_render_macd_returns_figure_one_axes(self):
        print('\n[Phase2] MACD 规格渲染返回 Figure，至少 1 个 axes')
        hp = _make_hp(['macd_12_26_9', 'macd_signal_12_26_9', 'macd_hist_12_26_9'])
        spec = build_macd_spec(hp)
        self.assertIsNotNone(spec)
        fig = render_macd_spec(spec)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))

    def test_render_line_returns_figure_one_axes(self):
        print('\n[Phase2] 折线规格渲染返回 Figure，至少 1 个 axes')
        hp = _make_hp(['close'])
        spec = build_line_spec(hp)
        self.assertIsNotNone(spec)
        fig = render_line_spec(spec)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))

    def test_render_spec_dispatches_by_chart_type(self):
        print('\n[Phase2] render_spec 按 chart_type 分发，返回 Figure')
        hp = _make_hp(['open', 'high', 'low', 'close'])
        spec = build_kline_spec(hp)
        fig = render_spec(spec)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        hp2 = _make_hp(['close'])
        spec2 = build_line_spec(hp2)
        fig2 = render_spec(spec2)
        self.assertIsNotNone(fig2)
        print('  kline fig axes:', len(fig.axes), 'line fig axes:', len(fig2.axes))


class TestPlotOrchestrator(unittest.TestCase):
    """Phase 3：hp.plot() 编排器 — 1/2/多 shares、分组与组内子图数量."""

    def test_plot_one_share_returns_figure(self):
        print('\n[Phase3] 1 share：hp.plot() 返回 Figure，组内子图数量=适用图表类型数')
        hp = _make_hp(['open', 'high', 'low', 'close'], n_shares=1)
        fig = hp.plot()
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))

    def test_plot_only_close_returns_one_subplot(self):
        print('\n[Phase3] 仅 close：仅 line 类型，1 个子图')
        hp = _make_hp(['close'], n_shares=1)
        fig = hp.plot()
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))

    def test_plot_ohlc_vol_two_subplots(self):
        print('\n[Phase3] OHLC+vol：kline+volume，2 个子图')
        hp = _make_hp(['open', 'high', 'low', 'close', 'vol'], n_shares=1)
        fig = hp.plot()
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 2)
        print('  n_axes:', len(fig.axes))

    def test_plot_two_shares_stack_two_groups(self):
        print('\n[Phase3] 2 shares layout=stack：2 组，每组子图数=类型数')
        hp = _make_hp(['open', 'high', 'low', 'close'], n_shares=2)
        fig = hp.plot(layout='stack')
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))


class TestHighlight(unittest.TestCase):
    """Phase 4：highlight 子模块 — condition + style，接入 hp.plot(..., highlight=...). 对应计划 8.7."""

    def test_p4_1_highlight_none_no_error(self):
        print('\n[P4-1] highlight=None 不报错，正常出图')
        hp = _make_hp(['close'], n_shares=1)
        fig = hp.plot(highlight=None)
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)
        ax = fig.axes[0]
        self.assertEqual(len(ax.collections), 0)
        print('  n_axes:', len(fig.axes), 'n_collections:', len(ax.collections))

    def test_p4_2_highlight_max_string_line(self):
        print('\n[P4-2] highlight=\"max\" 折线图，仅 close 最大值点高亮')
        hp = _make_hp(['close'], n_shares=1)
        fig = hp.plot(highlight='max')
        self.assertIsNotNone(fig)
        ax = fig.axes[0]
        collections = [c for c in ax.collections if hasattr(c, 'get_sizes')]
        self.assertGreaterEqual(len(collections), 1)
        print('  n_collections:', len(collections))

    def test_p4_3_highlight_condition_min_line(self):
        print('\n[P4-3] highlight={\"condition\": \"min\"} 折线图，最小值点高亮')
        hp = _make_hp(['close'], n_shares=1)
        spec = build_line_spec(hp)
        self.assertIsNotNone(spec)
        spec = dict(spec)
        spec['highlight'] = {'condition': 'min'}
        fig = render_line_spec(spec)
        self.assertIsNotNone(fig)
        ax = fig.axes[0]
        self.assertGreaterEqual(len(ax.collections), 1)
        print('  n_collections:', len(ax.collections))

    def test_p4_4_highlight_with_style(self):
        print('\n[P4-4] highlight 含 style，高亮点颜色与大小与 style 一致')
        hp = _make_hp(['close'], n_shares=1, n_dates=10)
        spec = build_line_spec(hp)
        spec = dict(spec)
        spec['highlight'] = {'condition': 'max', 'style': {'color': 'red', 's': 60}}
        fig = render_line_spec(spec)
        self.assertIsNotNone(fig)
        ax = fig.axes[0]
        self.assertGreaterEqual(len(ax.collections), 1)
        coll = ax.collections[0]
        self.assertEqual(coll.get_facecolor().shape[0], 1)
        self.assertAlmostEqual(coll.get_sizes()[0], 60)
        print('  collection sizes:', coll.get_sizes(), 'facecolor:', coll.get_facecolor())

    def test_p4_5_highlight_condition_bool_array(self):
        print('\n[P4-5] condition 为布尔数组，仅 True 处高亮')
        hp = _make_hp(['close'], n_shares=1, n_dates=15)
        spec = build_line_spec(hp)
        self.assertIsNotNone(spec)
        spec = dict(spec)
        mask = np.zeros(15, dtype=bool)
        mask[7] = True
        spec['highlight'] = {'condition': mask}
        fig = render_line_spec(spec)
        self.assertIsNotNone(fig)
        ax = fig.axes[0]
        self.assertGreaterEqual(len(ax.collections), 1)
        offs = ax.collections[0].get_offsets()
        self.assertEqual(offs.shape[0], 1)
        self.assertEqual(int(offs[0, 0]), 7)
        print('  single scatter at index:', int(offs[0, 0]))

    def test_p4_6_multi_group_stack_highlight(self):
        print('\n[P4-6] 多组 stack 时 highlight=\"max\"，每组折线各自 close 最大值高亮')
        hp = _make_hp(['close'], n_shares=2, n_dates=20)
        fig = hp.plot(layout='stack', highlight='max')
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 2)
        for i, ax in enumerate(fig.axes):
            collections = [c for c in ax.collections if hasattr(c, 'get_sizes')]
            self.assertGreaterEqual(len(collections), 1, f'group {i} should have highlight scatter')
        print('  n_axes:', len(fig.axes), 'each has scatter')

    def test_plot_with_highlight_max_dict(self):
        print('\n[Phase4] hp.plot(..., highlight={\"condition\": \"max\"}) 不报错，返回 Figure')
        hp = _make_hp(['close'], n_shares=1)
        fig = hp.plot(highlight={'condition': 'max'})
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)
        ax = fig.axes[0]
        collections = [c for c in ax.collections if hasattr(c, 'get_sizes')]
        self.assertGreaterEqual(len(collections), 1)
        print('  n_axes:', len(fig.axes), 'n_collections:', len(ax.collections))

    def test_render_line_spec_with_highlight_min(self):
        print('\n[Phase4] render_line_spec(spec with highlight condition=min) 绘制高亮点')
        hp = _make_hp(['close'], n_shares=1)
        spec = build_line_spec(hp)
        self.assertIsNotNone(spec)
        spec = dict(spec)
        spec['highlight'] = {'condition': 'min', 'style': {'color': 'red', 'marker': 'o'}}
        fig = render_line_spec(spec)
        self.assertIsNotNone(fig)
        ax = fig.axes[0]
        self.assertGreaterEqual(len(ax.collections), 1)
        print('  n_collections:', len(ax.collections))


class TestInteractiveBackend(unittest.TestCase):
    """Phase 5：hp.plot(..., interactive=True) 返回 Plotly Figure，结构可用."""

    def test_plot_interactive_true_returns_figure(self):
        print('\n[Phase5] hp.plot(interactive=True) 返回 Figure，结构可用')
        hp = _make_hp(['close'], n_shares=1)
        try:
            fig = hp.plot(interactive=True)
        except RuntimeError as e:
            if 'plotly' in str(e).lower():
                self.skipTest('plotly not installed, skip interactive test')
            raise
        self.assertIsNotNone(fig)
        if hasattr(fig, 'data'):
            self.assertGreaterEqual(len(fig.data), 1, 'Plotly figure should have at least one trace')
            print('  plotly fig.data traces:', len(fig.data))
        else:
            self.assertGreaterEqual(len(fig.axes), 1)
            print('  n_axes:', len(fig.axes))

    def test_plot_interactive_two_shares_stack(self):
        print('\n[Phase5] 2 shares layout=stack interactive 返回多 trace、多组')
        hp = _make_hp(['close'], n_shares=2)
        try:
            fig = hp.plot(interactive=True, layout='stack')
        except RuntimeError as e:
            if 'plotly' in str(e).lower():
                self.skipTest('plotly not installed')
            raise
        self.assertIsNotNone(fig)
        if hasattr(fig, 'data'):
            self.assertGreaterEqual(len(fig.data), 2)
            print('  plotly traces:', len(fig.data))

    def test_plotly_backend_app_invalid_raises(self):
        print('\n[Phase5] plotly_backend_app 非法取值抛 ValueError')
        hp = _make_hp(['close'], n_shares=1)
        try:
            import plotly  # noqa: F401
        except ImportError:
            self.skipTest('plotly not installed')
        with self.assertRaises(ValueError) as ctx:
            hp.plot(interactive=True, plotly_backend_app='widget')
        self.assertIn('plotly_backend_app', str(ctx.exception).lower())
        print('  message:', ctx.exception)

    def test_plotly_backend_app_requires_interactive(self):
        print('\n[Phase5] plotly_backend_app 非 auto 时必须 interactive=True')
        hp = _make_hp(['close'], n_shares=1)
        with self.assertRaises(ValueError) as ctx:
            hp.plot(interactive=False, plotly_backend_app='html')
        self.assertIn('interactive', str(ctx.exception).lower())
        print('  message:', ctx.exception)

    def test_normalize_plotly_backend_app_aliases(self):
        print('\n[Phase5] _normalize_plotly_backend_app 大小写与 auto')
        from qteasy.hp_visual_plotly import _normalize_plotly_backend_app

        self.assertEqual(_normalize_plotly_backend_app('auto'), 'auto')
        self.assertEqual(_normalize_plotly_backend_app('FigureWidget'), 'figurewidget')
        self.assertEqual(_normalize_plotly_backend_app('HTML'), 'html')


class TestQ02SubplotTitlesHtmlExport(unittest.TestCase):
    """Q02：Notebook HTML 路径保留 subplot 分组标题，与 FigureWidget 的 annotation 前缀语义一致。"""

    def test_q02_html_export_preserves_subplot_title_annotations(self):
        print('\n[Q02] 双组 stack+OHLC：subplot_annotation_count 与 HTML 导出保留分组标题')
        try:
            import plotly.graph_objects as go  # noqa: F401
        except ImportError:
            self.skipTest('plotly not installed')
        from qteasy.hp_visual_plotly import (
            _PlotlyFigureWrapper,
            _annotations_for_plotly_html_export,
            build_interactive_figure_from_specs,
        )

        hp = _make_hp(['open', 'high', 'low', 'close', 'vol'], n_shares=2, n_dates=12)
        specs_per_group, types_info, group_titles = _specs_per_group_stack_two_shares(hp)
        x_dates = list(hp.hdates)
        fig = build_interactive_figure_from_specs(
            specs_per_group,
            types_info,
            x_dates=x_dates,
            group_titles=group_titles,
        )
        meta = getattr(fig, '_hp_plotly_meta', {})
        self.assertTrue(meta.get('show_ohlc_header'))
        n_sub = int(meta.get('subplot_annotation_count', 0))
        self.assertGreater(n_sub, 0, 'stack two groups should have subplot title annotations')
        ann_full = list(fig.layout.annotations) if fig.layout.annotations else []
        self.assertEqual(len(ann_full), n_sub)
        print('  subplot_annotation_count:', n_sub, 'len(layout.annotations):', len(ann_full))

        kept = _annotations_for_plotly_html_export(fig.layout, meta)
        self.assertEqual(len(kept), n_sub)
        title_blob = ' '.join(str(getattr(a, 'text', '') or '') for a in kept)
        self.assertIn('S000', title_blob)
        self.assertIn('S001', title_blob)
        print('  kept annotation texts contain share codes:', 'S000' in title_blob, 'S001' in title_blob)

        wrapper = _PlotlyFigureWrapper(fig)
        html_str = wrapper._repr_html_()
        self.assertGreater(len(html_str), 100)
        # 分组标题应出现在序列化后的 Plotly 数据中（不仅依赖 trace name_prefix）
        self.assertIn('"S000"', html_str)
        self.assertIn('"S001"', html_str)
        print('  _repr_html_ contains quoted S000/S001 in payload')


class TestHistoryPanelPlotP1Parity(unittest.TestCase):
    """P1：静态/交互表头、字体转译、图例 inset、蜡烛转译（双模对齐）。"""

    def test_p1a_static_ohlc_vol_header_last_bar(self):
        print('\n[T-P1a-1] 静态 OHLC+vol：顶栏 axes + 末根 close 出现在摘要中')
        hp = _make_hp(['open', 'high', 'low', 'close', 'vol'], n_dates=8, n_shares=1)
        fig = hp.plot()
        self.assertEqual(len(fig.axes), 4)
        hdr = fig.axes[0]
        self.assertTrue(getattr(hdr, '_hp_ohlc_header', False))
        ci = hp.htypes.index('close')
        last_close = float(hp.values[0, -1, ci])
        blob = ''.join(t.get_text() for t in hdr.texts)
        self.assertIn(f'{last_close:.2f}', blob)
        print('  header texts contain last close:', last_close)

    def test_p1a_no_kline_no_header_static_and_interactive_meta(self):
        print('\n[T-P1a-2] 无 K 线：静态无顶栏；交互不启用 OHLC 表头')
        hp = _make_hp(['close'], n_shares=1)
        fig = hp.plot()
        self.assertEqual(len(fig.axes), 1)
        self.assertFalse(getattr(fig.axes[0], '_hp_ohlc_header', False))
        try:
            fig2 = hp.plot(interactive=True)
        except RuntimeError as e:
            if 'plotly' in str(e).lower():
                self.skipTest('plotly not installed')
            raise
        base = fig2.figure if hasattr(fig2, 'figure') else fig2
        meta = getattr(base, '_hp_plotly_meta', {})
        self.assertFalse(meta.get('show_ohlc_header', True))
        self.assertFalse(bool(meta.get('initial_header_html')))
        print('  show_ohlc_header:', meta.get('show_ohlc_header'))

    def test_p1b_font_resolve_plotly_tick_vs_mpl(self):
        print('\n[T-P1b-1] 字体转译：plotly 轴刻度 = base+1；matplotlib 轴刻度 = max(7, base-1)')
        from qteasy.hp_visual_render import _get_theme
        from qteasy.hp_visual_theme_adapt import resolve_font_size

        theme = _get_theme()
        base = int(theme['font_size'])
        mpl_t = resolve_font_size('matplotlib', 'axis_tick', theme)
        ply_t = resolve_font_size('plotly', 'axis_tick', theme)
        self.assertEqual(ply_t, base + 1)
        self.assertEqual(mpl_t, max(7, base - 1))
        print('  mpl axis_tick:', mpl_t, 'plotly axis_tick:', ply_t)

    def test_p1c_plotly_legend_paper_inset(self):
        print('\n[T-P1c-1] 交互 K 线+MA：图例为 paper 坐标左上 inset')
        htypes = ['open', 'high', 'low', 'close', 'sma_20']
        hp = _make_hp(htypes, n_dates=15, n_shares=1)
        try:
            fig = hp.plot(interactive=True)
        except RuntimeError as e:
            if 'plotly' in str(e).lower():
                self.skipTest('plotly not installed')
            raise
        base = fig.figure if hasattr(fig, 'figure') else fig
        leg = base.layout.legend
        self.assertIsNotNone(leg)
        self.assertEqual(getattr(leg, 'xref', None), 'paper')
        self.assertLess(float(leg.x), 0.2)
        print('  legend.x:', leg.x, 'y:', leg.y, 'xref:', leg.xref)

    def test_p1d_candle_style_adapt_and_trace(self):
        print('\n[T-P1d-1] 蜡烛颜色转译稳定且交互图含 Candlestick 样式')
        from qteasy.hp_visual_render import _get_theme
        from qteasy.hp_visual_theme_adapt import resolve_candle_style_plotly

        theme = _get_theme()
        c1 = resolve_candle_style_plotly(theme)
        c2 = resolve_candle_style_plotly(theme)
        self.assertEqual(c1, c2)
        self.assertIn('increasing_line_color', c1)
        w0 = float(theme.get('candle_plotly_whiskerwidth', 0.18))
        self.assertAlmostEqual(c1['whiskerwidth'], w0)
        hp = _make_hp(['open', 'high', 'low', 'close'])
        try:
            fig = hp.plot(interactive=True)
        except RuntimeError as e:
            if 'plotly' in str(e).lower():
                self.skipTest('plotly not installed')
            raise
        base = fig.figure if hasattr(fig, 'figure') else fig
        candle = next((tr for tr in base.data if getattr(tr, 'type', '') == 'candlestick'), None)
        self.assertIsNotNone(candle)
        inc = getattr(candle, 'increasing', None)
        fill = getattr(inc, 'fillcolor', None) if inc is not None else None
        self.assertIsNotNone(fill)
        print('  whiskerwidth:', c1['whiskerwidth'], 'increasing.fillcolor:', fill)


class TestHpVisualLayoutSpec(unittest.TestCase):
    """HpVisualLayoutSpec：单组/多组 stack 共用布局，表头占整图垂直比例一致。"""

    def test_mpl_header_absolute_inches_stable_across_group_count(self):
        print('\n[layout] MPL：多组时表头绝对高度（英寸）与单组参考一致，不随 fig 变高而倍增')
        from qteasy.hp_visual_layout import compute_hp_visual_layout_spec
        from qteasy.hp_visual_render import _get_theme

        class _TI:
            def __init__(self, tid: str, imp: str) -> None:
                self.id = tid
                self.importance = imp

        def _header_abs_inches(sp) -> float:
            fh = sp['mpl_figsize'][1]
            ratios = sp['mpl_height_ratios']
            if not ratios or sp['row_off'] == 0:
                return 0.0
            return fh * ratios[0] / sum(ratios)

        theme = _get_theme()
        f = float(theme['hp_header_vertical_fraction'])
        h_floor = float(theme['hp_mpl_fig_height_floor'])
        h_base = float(theme['hp_mpl_fig_height_base'])
        h_int = float(theme['hp_mpl_fig_height_intercept'])
        fig_h_ref = max(h_floor, h_base * 1.0 + h_int)
        target_abs = fig_h_ref * f
        types_info = [_TI('kline', 'main'), _TI('volume', 'secondary')]

        spec1 = compute_hp_visual_layout_spec(
            1, 2, types_info, theme, row_off=1, show_ohlc_header=True,
        )
        spec5 = compute_hp_visual_layout_spec(
            5, 2, types_info, theme, row_off=1, show_ohlc_header=True,
        )
        a1 = _header_abs_inches(spec1)
        a5 = _header_abs_inches(spec5)
        self.assertAlmostEqual(a1, target_abs, places=5)
        self.assertAlmostEqual(a5, target_abs, places=5)
        frac1 = spec1['mpl_height_ratios'][0] / sum(spec1['mpl_height_ratios'])
        frac5 = spec5['mpl_height_ratios'][0] / sum(spec5['mpl_height_ratios'])
        self.assertLess(frac5, frac1)
        print('  header abs inches 1grp/5grp:', a1, a5, 'target:', target_abs, 'frac5<frac1:', frac5, frac1)

    def test_plotly_row_heights_match_chart_ratios(self):
        print('\n[layout] Plotly 行高列表与 chart_height_ratios 一致（无表头行）')
        from qteasy.hp_visual_layout import compute_hp_visual_layout_spec
        from qteasy.hp_visual_render import _get_theme

        class _TI:
            def __init__(self, tid: str, imp: str) -> None:
                self.id = tid
                self.importance = imp

        theme = _get_theme()
        types_info = [_TI('kline', 'main'), _TI('volume', 'secondary')]
        spec = compute_hp_visual_layout_spec(
            2, 2, types_info, theme, row_off=1, show_ohlc_header=True,
        )
        self.assertEqual(spec['plotly_row_heights'], spec['chart_height_ratios'])
        self.assertEqual(spec['plotly_n_subplot_rows'], len(spec['chart_height_ratios']))
        print('  plotly rows:', spec['plotly_n_subplot_rows'])

    def test_mpl_header_gap_increases_fig_height_and_pre_chart_rows(self):
        print('\n[layout] MPL：默认 8mm 间隔行，fig 高度 +D 英寸，mpl_pre_chart_rows==2')
        from qteasy.hp_visual_layout import compute_hp_visual_layout_spec
        from qteasy.hp_visual_render import _get_theme

        class _TI:
            def __init__(self, tid: str, imp: str) -> None:
                self.id = tid
                self.importance = imp

        theme = _get_theme()
        types_info = [_TI('kline', 'main'), _TI('volume', 'secondary')]
        spec = compute_hp_visual_layout_spec(
            1, 2, types_info, theme, row_off=1, show_ohlc_header=True,
        )
        d_exp = float(theme['hp_mpl_header_gap_below_mm']) / 25.4
        h0 = max(
            float(theme['hp_mpl_fig_height_floor']),
            float(theme['hp_mpl_fig_height_base']) * 1.0 + float(theme['hp_mpl_fig_height_intercept']),
        )
        self.assertEqual(spec['mpl_pre_chart_rows'], 2)
        self.assertAlmostEqual(spec['mpl_header_gap_below_inches'], d_exp, places=5)
        self.assertAlmostEqual(spec['mpl_figsize'][1], h0 + d_exp, places=5)
        self.assertEqual(len(spec['mpl_height_ratios']), 2 + len(spec['type_ratios']))
        print('  fig_h:', spec['mpl_figsize'][1], 'h0+d:', h0 + d_exp, 'pre_chart_rows:', spec['mpl_pre_chart_rows'])


class TestPlotlyFigureWidgetHeaderPaperY(unittest.TestCase):
    """FigureWidget 表头：paper y 随 layout 高度反解，距顶毫米稳定。"""

    def test_plotly_header_paper_y_formula_and_order(self):
        print('\n[plotly-header-y] 反解 y1>y2，且随 height 变化')
        from qteasy.hp_visual_plotly import _plotly_header_paper_y_from_layout
        from qteasy.hp_visual_render import _get_theme

        theme = dict(_get_theme())
        mt, mb = 120.0, 40.0
        y1_400, y2_400 = _plotly_header_paper_y_from_layout(400.0, mt, mb, theme)
        y1_900, y2_900 = _plotly_header_paper_y_from_layout(900.0, mt, mb, theme)
        self.assertGreater(y1_400, y2_400)
        self.assertGreater(y1_900, y2_900)
        h_plot_400 = 400.0 - mt - mb
        d1 = float(theme['plotly_header_line1_top_mm']) * 96.0 / 25.4
        exp_y1 = 1.0 + (mt - d1) / h_plot_400
        self.assertAlmostEqual(y1_400, min(max(exp_y1, 1.02), 1.42), places=5)
        self.assertNotAlmostEqual(y1_400, y1_900, places=3)
        print('  y1@400/900:', y1_400, y1_900, 'y2@400:', y2_400)

    def test_layout_height_margin_tb_defaults(self):
        print('\n[plotly-header-y] _layout_height_margin_tb 缺省 margin')
        from qteasy.hp_visual_plotly import _layout_height_margin_tb
        from qteasy.hp_visual_render import _get_theme

        theme = _get_theme()

        class _Lay:
            height = 500
            margin = None

        h, t, b = _layout_height_margin_tb(_Lay(), theme, has_ohlc_header=True)
        self.assertEqual(h, 500.0)
        self.assertEqual(t, float(theme['plotly_margin_top_with_header']))
        self.assertEqual(b, 40.0)
        print('  height', h, 'margin_t', t, 'margin_b', b)


if __name__ == '__main__':
    unittest.main()
