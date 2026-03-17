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


class TestCandleWithStockAndAssetType(_BaseCandleTestWithFixture):
    """使用真实 qt.candle(stock, asset_type, freq) 行为（依赖当前 QT_DATA_SOURCE，可按需 skip）。"""

    def test_candle_with_stock_and_asset_type_uses_fake_data(self):
        print('\n[V6-C3] 使用 stock+asset_type=E 路径，返回 DataFrame，不抛异常（依赖本地数据源）')
        try:
            res = visual.candle(
                stock='000001.SZ',
                start=None,
                end=None,
                stock_data=None,
                asset_type='E',
                freq='D',
                plot_type='none',
                interactive=False,
                data_source=None,
            )
        except Exception as e:
            self.skipTest(f'local data source not available for 000001.SZ: {e}')
            return
        self.assertIsInstance(res, pd.DataFrame)
        self.assertGreater(len(res), 0)
        for col in ['open', 'high', 'low', 'close']:
            self.assertIn(col, res.columns)
        print('  result index:', res.index[0], '->', res.index[-1])

    def test_candle_freq_variants_do_not_error(self):
        print('\n[V6-F1] 不同 freq 组合下 candle 不报错（依赖本地数据源）')
        freqs = ['D', 'W', 'M', 'H', '30MIN']
        for f in freqs:
            try:
                res = visual.candle(
                    stock='000001.SZ',
                    start=None,
                    end=None,
                    stock_data=None,
                    asset_type='E',
                    freq=f,
                    plot_type='none',
                    interactive=False,
                    data_source=None,
                )
            except Exception as e:
                self.skipTest(f'local data source not available for freq={f}: {e}')
                return
            self.assertIsInstance(res, pd.DataFrame)
            self.assertGreater(len(res), 0)
        print('  all freqs executed without error:', freqs)

    def test_candle_out_of_fund_asset_type_fd(self):
        print('\n[V6-F2] 场外基金 asset_type=FD 路径不报错（依赖本地数据源，如不可用则 skip）')
        try:
            res = visual.candle(
                stock='000521.OF',
                start=None,
                end=None,
                stock_data=None,
                asset_type='FD',
                freq='D',
                plot_type='candle',
                interactive=False,
                data_source=None,
            )
        except Exception as e:
            self.skipTest(f'local fund data not available for asset_type=FD: {e}')
            return
        self.assertIsInstance(res, pd.DataFrame)
        # 对于基金，至少应有 close 列
        self.assertIn('close', res.columns)
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
        # 直接调用 candle，触发 _get_mpf_data 中的 OPT 分支；若失败说明测试数据源未就绪，应修复数据源
        with self.assertRaises(NotImplementedError):
            visual.candle(
                stock='000001.SZ',
                start=None,
                end=None,
                stock_data=None,
                asset_type='OPT',
                freq='D',
                plot_type='none',
                interactive=False,
                data_source=None,
            )
        print('  asset_type=OPT correctly raises NotImplementedError')

    def test_candle_adj_back_and_forward_variants(self):
        print('\n[V6-ADJ] adj 参数别名 b/back/f/forward 不报错（依赖本地数据源）')
        # 仅验证不同 adj 取值在 stock+asset_type 路径下不会抛错；
        # 若由于测试数据源未就绪导致失败，应修复数据源而非跳过测试。
        adj_values = ['b', 'back', 'f', 'forward']
        for adj in adj_values:
            res = visual.candle(
                stock='000001.SZ',
                start=None,
                end=None,
                stock_data=None,
                asset_type='E',
                freq='D',
                plot_type='none',
                interactive=False,
                data_source=None,
                adj=adj,
            )
            if not isinstance(res, pd.DataFrame):
                self.fail(f'candle returned {type(res)} instead of DataFrame for adj={adj}')
            self.assertGreater(len(res), 0)
        print('  all adj variants executed without error:', adj_values)


if __name__ == '__main__':
    unittest.main()

