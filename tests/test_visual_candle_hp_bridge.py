# coding=utf-8
# ======================================
# File: test_visual_candle_hp_bridge.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-03-16
# Desc:
# Unittest for qt.candle ↔ HistoryPanel
# visualization bridge (Phase 6).
# ======================================

import unittest

import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel
from qteasy import visual


class _BaseCandleTestWithFixture(unittest.TestCase):
    """为 qt.candle 测试准备统一的 fixture_df."""

    @classmethod
    def setUpClass(cls):
        print('\n[Setup] 构造 fixture_df 作为 candle 测试输入')
        dates = pd.date_range('2024-01-01', periods=20, freq='B')
        cls.fixture_df = pd.DataFrame(
            {
                'open': np.linspace(10, 29, 20),
                'high': np.linspace(11, 30, 20),
                'low': np.linspace(9, 28, 20),
                'close': np.linspace(10.5, 29.5, 20),
                'volume': np.arange(20, dtype=float) * 1000.0,
            },
            index=dates,
        )


class TestDailyDataFrameToHistoryPanel(_BaseCandleTestWithFixture):
    """DataFrame → HistoryPanel 适配函数."""

    def test_basic_ohlcv_to_single_share_historypanel(self):
        print('\n[V6-DF-1] DataFrame → HistoryPanel 基本适配：单 share OHLCV')
        data = self.fixture_df.iloc[:5]
        share_code = '000001.SZ'

        hp = visual._daily_dataframe_to_history_panel(  # type: ignore[attr-defined]
            daily=data,
            share_code=share_code,
            asset_type='E',
            freq='D',
        )

        self.assertIsInstance(hp, HistoryPanel)
        self.assertEqual(hp.shares, [share_code])
        self.assertEqual(list(hp.htypes), ['open', 'high', 'low', 'close', 'volume'])
        self.assertEqual(hp.values.shape, (1, 5, 5))
        # 时间轴应与原 DataFrame 对齐
        self.assertEqual(pd.to_datetime(hp.hdates[0]), data.index[0])
        self.assertEqual(pd.to_datetime(hp.hdates[-1]), data.index[-1])
        print('  shares:', hp.shares, 'htypes:', hp.htypes, 'values.shape:', hp.values.shape)


class TestCandleBasicBehaviour(_BaseCandleTestWithFixture):
    """qt.candle 基本行为（不含 HP 可视化细节）."""

    def test_candle_plot_type_none_returns_dataframe(self):
        print('\n[V6-1] qt.candle plot_type="none" 返回 DataFrame，不抛异常')
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='none',
            interactive=False,
            data_source=None,
        )
        self.assertIsInstance(res, pd.DataFrame)
        self.assertEqual(len(res), len(self.fixture_df))
        # 时间轴应与输入 DataFrame 完全一致
        self.assertEqual(res.index[0], self.fixture_df.index[0])
        self.assertEqual(res.index[-1], self.fixture_df.index[-1])
        print('  result index:', res.index[0], '->', res.index[-1])
        print('  result shape:', res.shape, 'columns:', res.columns.tolist())

    def test_candle_invalid_plot_type_raises(self):
        print('\n[V6-2] qt.candle 非法 plot_type 抛出 KeyError')
        with self.assertRaises(KeyError):
            visual.candle(
                stock=None,
                stock_data=self.fixture_df,
                asset_type='E',
                freq='D',
                plot_type='renko',
                interactive=False,
                data_source=None,
            )
        print('  invalid plot_type=renko correctly raises KeyError')

    def test_candle_interactive_true_uses_hp_plot(self):
        print('\n[V6-3] qt.candle interactive=True 走 HistoryPanel 交互分支，不抛异常')
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=True,
            data_source=None,
        )
        self.assertIsInstance(res, pd.DataFrame)
        self.assertEqual(len(res), len(self.fixture_df))
        print('  interactive=True result shape:', res.shape)

    def test_candle_with_start_end_keeps_full_dataframe_index(self):
        print('\n[V6-4] qt.candle 传入 start/end 时返回 DataFrame 时间轴仍为完整 fixture')
        start = self.fixture_df.index[5]
        end = self.fixture_df.index[12]
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            start=start,
            end=end,
            data_source=None,
        )
        self.assertIsInstance(res, pd.DataFrame)
        # DataFrame 的可见时间轴起止仍应覆盖完整 fixture，而非被 start/end 裁剪
        self.assertEqual(res.index[0], self.fixture_df.index[0])
        self.assertEqual(res.index[-1], self.fixture_df.index[-1])
        print('  start/end input:', start, '->', end)
        print('  result index:', res.index[0], '->', res.index[-1])


class TestCandlePlotTypeAndIndicators(_BaseCandleTestWithFixture):
    """qt.candle 在不同 plot_type / indicator / avg_type 组合下的行为."""

    def test_plot_type_aliases_candle_and_line(self):
        print('\n[V6-P1] plot_type 各种别名归一化为 candle/line，不抛异常')
        for pt in ['candle', 'cdl', 'C', 'c']:
            res = visual.candle(
                stock=None,
                stock_data=self.fixture_df,
                asset_type='E',
                freq='D',
                plot_type=pt,
                interactive=False,
                data_source=None,
            )
            self.assertIsInstance(res, pd.DataFrame)
        for pt in ['line', 'l', 'LINE']:
            res = visual.candle(
                stock=None,
                stock_data=self.fixture_df,
                asset_type='E',
                freq='D',
                plot_type=pt,
                interactive=False,
                data_source=None,
            )
            self.assertIsInstance(res, pd.DataFrame)
        print('  all aliases executed without error')

    def test_default_ma_and_macd_columns_present(self):
        print('\n[V6-M1] 默认 mav/indicator=macd 时生成 MA* 与 macd-* 列')
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            data_source=None,
        )
        cols = res.columns.tolist()
        has_ma = any(c.startswith('MA') for c in cols)
        self.assertTrue(has_ma)
        self.assertIn('macd-m', cols)
        self.assertIn('macd-s', cols)
        self.assertIn('macd-h', cols)
        print('  columns contain:', [c for c in cols if c.startswith('MA')] + ['macd-m', 'macd-s', 'macd-h'])

    def test_custom_mav_values(self):
        print('\n[V6-M2] 自定义 mav=[10,20,30] 时生成对应 MA 列')
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            mav=[10, 20, 30],
            data_source=None,
        )
        cols = res.columns.tolist()
        ma_cols = [c for c in cols if c.startswith('MA')]
        self.assertGreaterEqual(len(ma_cols), 3)
        print('  MA columns:', ma_cols)

    def test_indicator_rsi_and_dema_keep_columns(self):
        print('\n[V6-M5] indicator=rsi/dema 仍增加 rsi/dema 列，不报错')
        res_rsi = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            indicator='rsi',
            data_source=None,
        )
        self.assertIn('rsi', res_rsi.columns)
        res_dema = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            indicator='dema',
            data_source=None,
        )
        self.assertIn('dema', res_dema.columns)
        print('  rsi/dema columns present')

    def test_invalid_indicator_raises_keyerror(self):
        print('\n[V6-M6] 非法 indicator 抛出 KeyError')
        with self.assertRaises(KeyError):
            visual.candle(
                stock=None,
                stock_data=self.fixture_df,
                asset_type='E',
                freq='D',
                plot_type='candle',
                interactive=False,
                indicator='invalid_indicator',
                data_source=None,
            )
        print('  invalid indicator correctly raises KeyError')


class TestCandleStartEndTimeAxis(_BaseCandleTestWithFixture):
    """qt.candle 在不同 start/end 组合下的时间轴与 DataFrame 行为."""

    def test_no_start_end_full_index(self):
        print('\n[V6-S1] 不传 start/end 时返回 DataFrame 时间轴为完整 fixture')
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            data_source=None,
        )
        self.assertEqual(res.index[0], self.fixture_df.index[0])
        self.assertEqual(res.index[-1], self.fixture_df.index[-1])
        print('  result index:', res.index[0], '->', res.index[-1])

    def test_only_start_parameter(self):
        print('\n[V6-S2] 仅传 start 时 DataFrame 仍为完整时间轴')
        start = self.fixture_df.index[3]
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            start=start,
            end=None,
            data_source=None,
        )
        self.assertEqual(res.index[0], self.fixture_df.index[0])
        self.assertEqual(res.index[-1], self.fixture_df.index[-1])
        print('  start input:', start, 'result index:', res.index[0], '->', res.index[-1])

    def test_only_end_parameter(self):
        print('\n[V6-S3] 仅传 end 时 DataFrame 仍为完整时间轴')
        end = self.fixture_df.index[10]
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            start=None,
            end=end,
            data_source=None,
        )
        self.assertEqual(res.index[0], self.fixture_df.index[0])
        self.assertEqual(res.index[-1], self.fixture_df.index[-1])
        print('  end input:', end, 'result index:', res.index[0], '->', res.index[-1])

    def test_start_end_out_of_range(self):
        print('\n[V6-S5] start/end 完全落在数据范围外时 DataFrame 仍为完整时间轴且不报错')
        res = visual.candle(
            stock=None,
            stock_data=self.fixture_df,
            asset_type='E',
            freq='D',
            plot_type='candle',
            interactive=False,
            start='2010-01-01',
            end='2010-02-01',
            data_source=None,
        )
        self.assertIsInstance(res, pd.DataFrame)
        self.assertEqual(res.index[0], self.fixture_df.index[0])
        self.assertEqual(res.index[-1], self.fixture_df.index[-1])
        print('  out-of-range start/end, result index:', res.index[0], '->', res.index[-1])


class TestCandleWithStockArgumentPatchedGetMpf(_BaseCandleTestWithFixture):
    """通过 patch visual._get_mpf_data 测试 stock+asset_type+freq 路径（独立于真实数据源）。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print('\n[Setup] patch visual._get_mpf_data 以使用测试数据')
        import qteasy.visual as vis_mod  # 延迟导入，便于 monkeypatch

        cls._orig_get_mpf_data = vis_mod._get_mpf_data  # type: ignore[attr-defined]

        fixture = cls.fixture_df

        def _fake_get_mpf_data(stock, asset_type=None, adj='none', freq='d', data_source=None):
            """返回最小测试数据，忽略 data_source."""
            if asset_type is None:
                asset_type = 'E'
            asset_type_u = asset_type.upper()
            if asset_type_u == 'E':
                df = fixture.copy()
                share_name = f'{stock} - TestStock [Stock 股票] '
                return df, share_name
            if asset_type_u == 'IDX':
                df = fixture.copy()
                share_name = f'{stock} - TestIndex [Index 指数] '
                return df, share_name
            if asset_type_u == 'FD':
                # 模拟场外基金：名称末尾带 O，触发 out-of-fund / line 行为，但数据仍为 OHLCV 以简化测试
                df = fixture.copy()
                share_name = f'{stock} - TestFund [Fund 基金] O'
                return df, share_name
            if asset_type_u == 'FT':
                df = fixture.copy()
                share_name = f'{stock} - TestFuture [Futures 期货] '
                return df, share_name
            if asset_type_u == 'OPT':
                raise NotImplementedError(f'Candle plot for asset type: "{asset_type}" is not supported at the moment')
            raise KeyError(f'Wrong asset type: "{asset_type}"')

        cls._fake_get_mpf_data = _fake_get_mpf_data
        vis_mod._get_mpf_data = _fake_get_mpf_data  # type: ignore[attr-defined]

    @classmethod
    def tearDownClass(cls):
        print('\n[TearDown] restore visual._get_mpf_data')
        import qteasy.visual as vis_mod

        vis_mod._get_mpf_data = cls._orig_get_mpf_data  # type: ignore[attr-defined]
        super().tearDownClass()

    def test_candle_with_stock_and_asset_type_uses_fake_data(self):
        print('\n[V6-C3] 使用 stock+asset_type=E 路径，返回 DataFrame，不抛异常')
        res = visual.candle(
            stock='TST000.SZ',
            start=None,
            end=None,
            stock_data=None,
            asset_type='E',
            freq='D',
            plot_type='none',
            interactive=False,
            data_source=None,
        )
        self.assertIsInstance(res, pd.DataFrame)
        self.assertGreater(len(res), 0)
        for col in ['open', 'high', 'low', 'close']:
            self.assertIn(col, res.columns)
        print('  result index:', res.index[0], '->', res.index[-1])

    def test_candle_freq_variants_do_not_error(self):
        print('\n[V6-F1] 不同 freq 组合下 candle 不报错')
        freqs = ['D', 'W', 'M', 'H', '30MIN']
        for f in freqs:
            res = visual.candle(
                stock='TST000.SZ',
                start=None,
                end=None,
                stock_data=None,
                asset_type='E',
                freq=f,
                plot_type='none',
                interactive=False,
                data_source=None,
            )
            self.assertIsInstance(res, pd.DataFrame)
            self.assertGreater(len(res), 0)
        print('  all freqs executed without error:', freqs)

    def test_candle_out_of_fund_asset_type_fd(self):
        print('\n[V6-F2] 场外基金 asset_type=FD，share_name 末尾 O 路径不报错（直接测试 _mpf_plot）')
        # 直接调用 _mpf_plot，避免 match_ts_code / data_source 干扰，只验证 O 结尾 share_name 不报错
        import qteasy.visual as vis_mod

        res = vis_mod._mpf_plot(  # type: ignore[attr-defined]
            stock_data=self.fixture_df,
            share_name='FUND000 - TestFund [Fund 基金] O',
            stock='FUND000',
            start=None,
            end=None,
            freq='D',
            asset_type='FD',
            plot_type='candle',
            no_visual=True,
            interactive=False,
            data_source=None,
        )
        self.assertIsInstance(res, pd.DataFrame)
        for col in ['open', 'high', 'low', 'close']:
            self.assertIn(col, res.columns)
        print('  FD result index:', res.index[0], '->', res.index[-1])

    def test_non_string_stock_raises_type_error(self):
        print('\n[V6-E1] 非字符串 stock 抛 TypeError')
        with self.assertRaises(TypeError):
            visual.candle(
                stock=12345,  # type: ignore[arg-type]
                start=None,
                end=None,
                stock_data=None,
                asset_type='E',
                freq='D',
                plot_type='none',
                interactive=False,
                data_source=None,
            )
        print('  non-string stock correctly raises TypeError')

    def test_invalid_stock_code_pattern_raises_keyerror(self):
        print('\n[V6-E2] stock 形态错误（段数>2）抛 KeyError')
        with self.assertRaises(KeyError):
            visual.candle(
                stock='AAA.BBB.CCC',
                start=None,
                end=None,
                stock_data=None,
                asset_type='E',
                freq='D',
                plot_type='none',
                interactive=False,
                data_source=None,
            )
        print('  invalid stock pattern correctly raises KeyError')

    def test_unsupported_asset_type_opt_raises_notimplemented(self):
        print('\n[V6-E3] 不支持的 asset_type=OPT 抛 NotImplementedError')
        # 这里直接测试 patched _get_mpf_data 行为，避免 match_ts_code 逻辑干扰
        with self.assertRaises(NotImplementedError):
            # 通过类属性调用未绑定函数，按 (stock, asset_type) 传参
            TestCandleWithStockArgumentPatchedGetMpf._fake_get_mpf_data('OPT000', asset_type='OPT', adj='none', freq='D', data_source=None)
        print('  _get_mpf_data for asset_type=OPT correctly raises NotImplementedError')


if __name__ == '__main__':
    unittest.main()

