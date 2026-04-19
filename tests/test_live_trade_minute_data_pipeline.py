# coding=utf-8
# ======================================
# File: test_live_trade_minute_data_pipeline.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-19
# Desc:
# Unittest for live minute data pipeline fixes
# ======================================

import shutil
import tempfile
import unittest

import pandas as pd

import qteasy.data_channels as data_channels_module
import qteasy.history as history_module
import qteasy.trader as trader_module
from qteasy.database import DataSource
from qteasy.history import _merge_live_prices_into_package, check_and_prepare_live_trade_data
from qteasy.trader import Trader


class _FakeDataSource:
    """记录写表行为的最小数据源替身。"""

    def __init__(self):
        self.writes = []

    def update_table_data(self, table, df, merge_type='update'):
        self.writes.append((table, df.copy(), merge_type))
        return len(df)


class _DummyTrader:
    """仅提供 refresh_datasource_price_data 所需属性。"""

    def __init__(self):
        self.asset_type = 'E'
        self.live_price_channel = 'dummy'
        self.asset_pool = ['000001.SZ']
        self._datasource = _FakeDataSource()

    @property
    def datasource(self):
        return self._datasource

    def send_message(self, message, debug=False):
        pass


class TestMaturedKlineScope(unittest.TestCase):
    """测试 matured_kline_scope 的兼容语义。"""

    def setUp(self):
        self._orig_get_func = data_channels_module._get_realtime_kline_func
        self._orig_now = data_channels_module.get_current_timezone_datetime

        def _fake_get_realtime_kline_func(_channel):
            def _fake_fetch(qt_code, date, freq):
                idx = pd.to_datetime([
                    '2026-04-19 09:31:00',
                    '2026-04-19 09:32:00',
                    '2026-04-19 09:33:00',
                ])
                df = pd.DataFrame({
                    'open': [10.0, 10.1, 10.2],
                    'close': [10.05, 10.15, 10.25],
                    'high': [10.06, 10.16, 10.26],
                    'low': [9.98, 10.08, 10.18],
                    'vol': [100.0, 200.0, 300.0],
                    'amount': [1000.0, 2000.0, 3000.0],
                }, index=idx)
                df.index.name = 'trade_time'
                return df

            return _fake_fetch

        data_channels_module._get_realtime_kline_func = _fake_get_realtime_kline_func
        data_channels_module.get_current_timezone_datetime = lambda _tz='local': pd.Timestamp('2026-04-19 09:32:30')

    def tearDown(self):
        data_channels_module._get_realtime_kline_func = self._orig_get_func
        data_channels_module.get_current_timezone_datetime = self._orig_now

    def test_matured_scope_last_keeps_compatibility(self):
        print('\n[TestMaturedKlineScope] scope=last should return one matured bar')
        df = data_channels_module.fetch_real_time_klines(
            channel='dummy',
            qt_codes=['000001.SZ'],
            freq='1min',
            parallel=False,
            verbose=False,
            matured_kline_only=True,
            matured_kline_scope='last',
        )
        print(' returned rows:', len(df))
        print(' returned index:', list(df.index))
        self.assertEqual(len(df), 1)
        self.assertEqual(df.index[0], pd.Timestamp('2026-04-19 09:32:00'))

    def test_matured_scope_all_returns_all_matured_rows(self):
        print('\n[TestMaturedKlineScope] scope=all should return all matured bars')
        df = data_channels_module.fetch_real_time_klines(
            channel='dummy',
            qt_codes=['000001.SZ'],
            freq='1min',
            parallel=False,
            verbose=False,
            matured_kline_only=True,
            matured_kline_scope='all',
        )
        print(' returned rows:', len(df))
        print(' returned index:', list(df.index))
        self.assertEqual(len(df), 2)
        self.assertEqual(df.index.max(), pd.Timestamp('2026-04-19 09:32:00'))

    def test_invalid_matured_scope_raises(self):
        print('\n[TestMaturedKlineScope] invalid scope should raise ValueError')
        with self.assertRaises(ValueError) as cm:
            data_channels_module.fetch_real_time_klines(
                channel='dummy',
                qt_codes=['000001.SZ'],
                freq='1min',
                parallel=False,
                verbose=False,
                matured_kline_only=True,
                matured_kline_scope='invalid',
            )
        print(' error:', cm.exception)
        self.assertIn('Invalid matured_kline_scope', str(cm.exception))


class TestReadFileDatetimeFilter(unittest.TestCase):
    """测试 _read_file 对 datetime/date 主键过滤行为。"""

    def setUp(self):
        print('\n[TestReadFileDatetimeFilter] setUp temp file datasource')
        self.temp_dir = tempfile.mkdtemp(prefix='temp_live_minute_filter_')
        self.ds = DataSource(source_type='file', file_loc=self.temp_dir)

    def tearDown(self):
        print('[TestReadFileDatetimeFilter] tearDown remove temp dir')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_file_datetime_pk_keeps_intraday_rows(self):
        print('\n[TestReadFileDatetimeFilter] datetime pk should keep intraday rows')
        df = pd.DataFrame({
            'ts_code': ['000001.SZ', '000001.SZ', '000001.SZ'],
            'trade_time': ['2026-04-19 09:31:00', '2026-04-19 14:59:00', '2026-04-20 09:31:00'],
            'close': [10.1, 10.9, 11.2],
        })
        self.ds._write_file(df, 'minute_case')
        out = self.ds._read_file(
            file_name='minute_case',
            primary_key=['ts_code', 'trade_time'],
            pk_dtypes=['str', 'datetime'],
            share_like_pk='ts_code',
            shares=['000001.SZ'],
            date_like_pk='trade_time',
            start='2026-04-19',
            end='2026-04-19',
        )
        print(' output index:', out.index.tolist())
        print(' output close:', out['close'].tolist())
        self.assertEqual(len(out), 2)
        self.assertIn(pd.Timestamp('2026-04-19 14:59:00'), out.index.get_level_values('trade_time'))

    def test_read_file_date_pk_behavior_not_regressed(self):
        print('\n[TestReadFileDatetimeFilter] date pk should keep date-only behavior')
        df = pd.DataFrame({
            'ts_code': ['000001.SZ', '000001.SZ', '000001.SZ'],
            'trade_date': ['2026-04-19', '2026-04-20', '2026-04-21'],
            'close': [10.1, 10.2, 10.3],
        })
        self.ds._write_file(df, 'date_case')
        out = self.ds._read_file(
            file_name='date_case',
            primary_key=['ts_code', 'trade_date'],
            pk_dtypes=['str', 'date'],
            share_like_pk='ts_code',
            shares=['000001.SZ'],
            date_like_pk='trade_date',
            start='2026-04-20',
            end='2026-04-20',
        )
        print(' output index:', out.index.tolist())
        print(' output close:', out['close'].tolist())
        self.assertEqual(len(out), 1)
        self.assertEqual(out.index.get_level_values('trade_date')[0], pd.Timestamp('2026-04-20 00:00:00'))


class TestLivePricesMerge(unittest.TestCase):
    """测试 live_prices 合并进历史数据包。"""

    def test_merge_simple_price_frame_into_close_package(self):
        print('\n[TestLivePricesMerge] merge simple price frame')
        hist_data_package = {
            'close_E_1min': pd.DataFrame(
                [[10.0, 20.0]],
                index=[pd.Timestamp('2026-04-18 15:00:00')],
                columns=['000001.SZ', '000002.SZ'],
            ),
        }
        live_prices = pd.DataFrame(
            {'price': [10.5, 21.0]},
            index=['000001.SZ', '000002.SZ'],
        )
        merged = _merge_live_prices_into_package(hist_data_package, live_prices, '2026-04-19')
        merged_df = merged['close_E_1min']
        print(' merged index tail:', merged_df.index[-2:].tolist())
        print(' merged tail values:\n', merged_df.tail(1))
        self.assertGreater(merged_df.index.max(), pd.Timestamp('2026-04-18 15:00:00'))
        self.assertAlmostEqual(float(merged_df.iloc[-1]['000001.SZ']), 10.5, places=6)
        self.assertAlmostEqual(float(merged_df.iloc[-1]['000002.SZ']), 21.0, places=6)

    def test_merge_kline_frame_updates_ohlcv_fields(self):
        print('\n[TestLivePricesMerge] merge kline frame with OHLCV fields')
        base_index = [pd.Timestamp('2026-04-18 15:00:00')]
        cols = ['000001.SZ']
        hist_data_package = {
            'close_E_1min': pd.DataFrame([[10.0]], index=base_index, columns=cols),
            'open_E_1min': pd.DataFrame([[9.9]], index=base_index, columns=cols),
            'high_E_1min': pd.DataFrame([[10.2]], index=base_index, columns=cols),
            'low_E_1min': pd.DataFrame([[9.8]], index=base_index, columns=cols),
            'volume_E_1min': pd.DataFrame([[100.0]], index=base_index, columns=cols),
            'amount_E_1min': pd.DataFrame([[1000.0]], index=base_index, columns=cols),
        }
        live_prices = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_time': ['2026-04-19 10:31:00'],
            'open': [10.1],
            'close': [10.3],
            'high': [10.4],
            'low': [10.0],
            'vol': [500.0],
            'amount': [5150.0],
        })
        merged = _merge_live_prices_into_package(hist_data_package, live_prices, '2026-04-19')
        target_time = pd.Timestamp('2026-04-19 10:31:00')
        print(' merged close row:', merged['close_E_1min'].loc[target_time].to_dict())
        print(' merged vol row:', merged['volume_E_1min'].loc[target_time].to_dict())
        self.assertAlmostEqual(float(merged['close_E_1min'].loc[target_time, '000001.SZ']), 10.3, places=6)
        self.assertAlmostEqual(float(merged['open_E_1min'].loc[target_time, '000001.SZ']), 10.1, places=6)
        self.assertAlmostEqual(float(merged['volume_E_1min'].loc[target_time, '000001.SZ']), 500.0, places=6)


class TestMinutePipelineEndToEnd(unittest.TestCase):
    """最小端到端链路：refresh -> live merge。"""

    def test_refresh_and_live_prepare_pipeline(self):
        print('\n[TestMinutePipelineEndToEnd] refresh datasource and merge into package')
        orig_fetch = trader_module.fetch_real_time_klines
        orig_prepare = history_module.check_and_prepare_backtest_data
        try:
            def _fake_fetch_real_time_klines(**kwargs):
                print(' fetch kwargs:', kwargs)
                self.assertTrue(kwargs.get('matured_kline_only'))
                self.assertEqual(kwargs.get('matured_kline_scope'), 'all')
                return pd.DataFrame({
                    'ts_code': ['000001.SZ', '000001.SZ'],
                    'trade_time': ['2026-04-19 10:30:00', '2026-04-19 10:31:00'],
                    'open': [10.0, 10.1],
                    'close': [10.2, 10.3],
                    'high': [10.25, 10.35],
                    'low': [9.95, 10.05],
                    'vol': [100.0, 120.0],
                    'amount': [1010.0, 1236.0],
                })

            def _fake_prepare_backtest_data(**kwargs):
                print(' prepare kwargs keys:', list(kwargs.keys()))
                return {
                    'close_E_1min': pd.DataFrame(
                        [[9.8]],
                        index=[pd.Timestamp('2026-04-18 15:00:00')],
                        columns=['000001.SZ'],
                    )
                }

            trader_module.fetch_real_time_klines = _fake_fetch_real_time_klines
            history_module.check_and_prepare_backtest_data = _fake_prepare_backtest_data

            dummy = _DummyTrader()
            Trader.refresh_datasource_price_data(dummy, unit='min')
            self.assertEqual(len(dummy.datasource.writes), 1)
            written_df = dummy.datasource.writes[0][1]
            print(' written rows:', len(written_df))
            print(' written trade_time list:', written_df['trade_time'].tolist())

            data_package = check_and_prepare_live_trade_data(
                op=object(),
                trade_date='2026-04-19',
                datasource=None,
                shares=['000001.SZ'],
                live_prices=written_df,
            )
            close_df = data_package['close_E_1min']
            print(' merged close index tail:', close_df.index[-2:].tolist())
            print(' merged close tail:\n', close_df.tail(2))
            self.assertIn(pd.Timestamp('2026-04-19 10:31:00'), close_df.index)
            self.assertAlmostEqual(float(close_df.loc[pd.Timestamp('2026-04-19 10:31:00'), '000001.SZ']), 10.3, places=6)
        finally:
            trader_module.fetch_real_time_klines = orig_fetch
            history_module.check_and_prepare_backtest_data = orig_prepare


if __name__ == '__main__':
    unittest.main()
