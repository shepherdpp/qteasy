# coding=utf-8
# ======================================
# File: test_refresh_datasource_table_mismatch.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-19
# Desc:
# Unittest for refresh_datasource_price_data table mapping by asset_type
# ======================================

import unittest

import pandas as pd

import qteasy.trader as trader_module
from qteasy.trader import Trader, _resolve_tables_for_refresh


class _FakeDataSource:
    """记录写表行为的最小数据源替身。"""

    def __init__(self):
        self.written_tables = []

    def update_table_data(self, table, df, merge_type='update'):
        self.written_tables.append((table, int(len(df)), merge_type))
        return int(len(df))

    def __repr__(self):
        return '<FakeDataSource>'


class _DummyTrader:
    """仅提供 refresh_datasource_price_data 所需属性。"""

    def __init__(self, asset_type: str):
        self.asset_type = asset_type
        self.live_price_channel = 'dummy_channel'
        self.asset_pool = ['518880.SH', '513100.SH']
        self._datasource = _FakeDataSource()
        self._messages = []

    @property
    def datasource(self):
        return self._datasource

    def send_message(self, message: str, debug=False):
        self._messages.append((message, debug))


class TestResolveTablesForRefresh(unittest.TestCase):

    def test_resolve_tables_for_refresh_basic_cases(self):
        print('\n[TestResolveTablesForRefresh] basic single-asset mapping')
        cases = [
            ('E', '1min', ['stock_1min']),
            ('FD', 'min', ['fund_1min']),
            ('IDX', 'h', ['index_hourly']),
            ('FT', '5min', ['future_5min']),
        ]
        for asset_type, unit, expected in cases:
            result = _resolve_tables_for_refresh(asset_type, unit)
            print(f' case asset_type={asset_type}, unit={unit}, result={result}')
            self.assertEqual(result, expected)

    def test_resolve_tables_for_refresh_multi_asset_and_case_insensitive(self):
        print('\n[TestResolveTablesForRefresh] multi-asset and case-insensitive input')
        result = _resolve_tables_for_refresh('e, fd, idx', 'MIN')
        print(' resolved tables:', result)
        self.assertEqual(result, ['stock_1min', 'fund_1min', 'index_1min'])

    def test_resolve_tables_for_refresh_invalid_combo_raises_key_error(self):
        print('\n[TestResolveTablesForRefresh] invalid combo should raise KeyError')
        with self.assertRaises(KeyError) as cm:
            _resolve_tables_for_refresh('FD', '2min')
        err_msg = str(cm.exception)
        print(' error:', err_msg)
        self.assertIn('Unsupported refresh table mapping', err_msg)


class TestRefreshDatasourcePriceDataMapping(unittest.TestCase):

    def setUp(self):
        self._orig_fetch = trader_module.fetch_real_time_klines

        def _fake_fetch_real_time_klines(**kwargs):
            return pd.DataFrame({
                'ts_code': ['518880.SH', '513100.SH'],
                'trade_time': ['2026-04-17 10:49:00', '2026-04-17 10:49:00'],
                'close': [1.23, 2.34],
                'pre_close': [1.20, 2.30],
            })

        trader_module.fetch_real_time_klines = _fake_fetch_real_time_klines

    def tearDown(self):
        trader_module.fetch_real_time_klines = self._orig_fetch

    def test_refresh_writes_fd_min_to_fund_1min(self):
        print('\n[TestRefreshDatasourcePriceDataMapping] FD + min should write fund_1min')
        dummy = _DummyTrader(asset_type='FD')
        Trader.refresh_datasource_price_data(dummy, unit='min')
        print(' written tables:', dummy.datasource.written_tables)
        self.assertEqual(dummy.datasource.written_tables[0][0], 'fund_1min')

    def test_refresh_writes_idx_h_to_index_hourly(self):
        print('\n[TestRefreshDatasourcePriceDataMapping] IDX + h should write index_hourly')
        dummy = _DummyTrader(asset_type='IDX')
        Trader.refresh_datasource_price_data(dummy, unit='h')
        print(' written tables:', dummy.datasource.written_tables)
        self.assertEqual(dummy.datasource.written_tables[0][0], 'index_hourly')

    def test_refresh_writes_e_1min_to_stock_1min(self):
        print('\n[TestRefreshDatasourcePriceDataMapping] E + 1min should write stock_1min')
        dummy = _DummyTrader(asset_type='E')
        Trader.refresh_datasource_price_data(dummy, unit='1min')
        print(' written tables:', dummy.datasource.written_tables)
        self.assertEqual(dummy.datasource.written_tables[0][0], 'stock_1min')

    def test_refresh_writes_multi_asset_to_all_target_tables(self):
        print('\n[TestRefreshDatasourcePriceDataMapping] E,FD should write both stock_1min and fund_1min')
        dummy = _DummyTrader(asset_type='E, FD')
        Trader.refresh_datasource_price_data(dummy, unit='min')
        written_table_names = [item[0] for item in dummy.datasource.written_tables]
        print(' written tables:', written_table_names)
        self.assertEqual(written_table_names, ['stock_1min', 'fund_1min'])


if __name__ == '__main__':
    unittest.main()
