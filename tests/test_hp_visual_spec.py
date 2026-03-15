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
    """Phase 5：hp.plot(..., interactive=True) 返回类型与基本结构."""

    def test_plot_interactive_true_returns_figure(self):
        print('\n[Phase5] hp.plot(interactive=True) 返回 Figure，结构可用')
        hp = _make_hp(['close'], n_shares=1)
        fig = hp.plot(interactive=True)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)
        print('  n_axes:', len(fig.axes))


if __name__ == '__main__':
    unittest.main()
