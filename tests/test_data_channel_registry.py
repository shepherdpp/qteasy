# coding=utf-8
# ======================================
# File: test_data_channel_registry.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-06-01
# Desc:
# Unittest for data channel registry and
# abstraction contracts in S3.1.
# ======================================

import unittest
from unittest.mock import patch

import pandas as pd

from qteasy.data_channels import (
    BUILTIN_DATA_CHANNELS,
    API_MAP_COLUMNS,
    FeatureNotImplementedError,
    TableNotSupportedInChannelError,
    channel_supports_table,
    fetch_bars,
    fetch_basics,
    fetch_real_time_quotes,
    fetch_table_once,
    get_api_map,
    get_channel,
    get_table_fetch_spec,
    iter_table_fetch_plan,
    list_builtin_channels,
    list_channel_tables,
    normalize_table_frame,
    scrub_table_data,
    validate_channel,
)


class TestDataChannelRegistry(unittest.TestCase):

    def test_channel_registry_lists_four_builtin_channels(self):
        print('\n[TestDataChannelRegistry] check builtin channel list')
        channels = list_builtin_channels()
        print(' channels:', channels)
        self.assertEqual(set(channels), set(BUILTIN_DATA_CHANNELS))
        self.assertIn('sina', channels)

    def test_get_channel_unknown_raises(self):
        print('\n[TestDataChannelRegistry] check unknown channel raise')
        with self.assertRaises(ValueError):
            get_channel('unknown_channel')

    def test_validate_channel_alias_emoney(self):
        print('\n[TestDataChannelRegistry] check emoney alias normalization')
        normalized = validate_channel('emoney')
        print(' normalized:', normalized)
        self.assertEqual(normalized, 'eastmoney')

    def test_get_api_map_columns_unchanged(self):
        print('\n[TestDataChannelRegistry] check api map columns and sample row')
        api_map = get_api_map('tushare')
        print(' columns:', api_map.columns.to_list())
        sample = api_map.loc['stock_daily']
        print(' stock_daily spec:', sample.to_dict())
        self.assertEqual(api_map.columns.to_list(), API_MAP_COLUMNS)
        self.assertEqual(sample['fill_arg_name'], 'trade_date')
        self.assertEqual(sample['fill_arg_type'], 'trade_date')

    def test_channel_supports_table_and_listing(self):
        print('\n[TestDataChannelRegistry] check supports_table and list_channel_tables')
        supports = channel_supports_table('tushare', 'stock_daily')
        ak_tables = list_channel_tables('akshare')
        sina_tables = list_channel_tables('sina')
        print(' tushare supports stock_daily:', supports)
        print(' akshare tables:', ak_tables)
        print(' sina tables sample:', sina_tables[:5])
        self.assertTrue(supports)
        self.assertEqual(ak_tables, [])
        self.assertIn('stock_daily', sina_tables)

    def test_get_table_fetch_spec_raises(self):
        print('\n[TestDataChannelRegistry] check unsupported table error')
        with self.assertRaises(TableNotSupportedInChannelError):
            get_table_fetch_spec('akshare', 'stock_daily')

    def test_iter_table_fetch_plan_matches_existing_behavior(self):
        print('\n[TestDataChannelRegistry] check iter_table_fetch_plan output')
        plan = list(iter_table_fetch_plan(
            table='stock_basic',
            channel='tushare',
            symbols='000651.SZ:000660.SZ',
            start_date='20210101',
            end_date='20210321',
            list_arg_filter=None,
            reversed_par_seq=False,
        ))
        print(' plan:', plan)
        self.assertEqual(plan, [{'exchange': 'SSE'}, {'exchange': 'SZSE'}, {'exchange': 'BSE'}])

    def test_normalize_table_frame_stock_basic(self):
        print('\n[TestDataChannelRegistry] check normalize_table_frame for stock_basic')
        raw = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'symbol': ['000001'],
            'name': ['平安银行'],
            'extra_col': [123],
        })
        normalized = normalize_table_frame('stock_basic', raw)
        print(' normalized columns:', normalized.columns.to_list()[:8], '...')
        print(' normalized first row keys:', normalized.iloc[0].dropna().to_dict().keys())
        self.assertIn('ts_code', normalized.columns)
        self.assertIn('symbol', normalized.columns)
        self.assertNotIn('extra_col', normalized.columns)
        self.assertEqual(normalized.loc[0, 'ts_code'], '000001.SZ')

    def test_scrub_table_data_calls_normalize(self):
        print('\n[TestDataChannelRegistry] check scrub_table_data behavior')
        raw = pd.DataFrame({
            'ts_code': ['000002.SZ'],
            'symbol': ['000002'],
            'name': ['万科A'],
            'extra_col': [999],
        })
        normalized = normalize_table_frame('stock_basic', raw)
        scrubbed = scrub_table_data(raw, 'stock_basic')
        print(' scrubbed head:', scrubbed.head(1).to_dict(orient='records'))
        self.assertTrue(normalized.equals(scrubbed))

    def test_fetch_table_once_delegates_to_channel_fetcher(self):
        print('\n[TestDataChannelRegistry] check fetch_table_once delegation')
        expected = pd.DataFrame({'a': [1]})
        with patch('qteasy.data_channels._get_fetch_table_func') as mocked:
            mocked.return_value = lambda table, **kwargs: expected
            out = fetch_table_once(channel='tushare', table='stock_basic', exchange='SSE')
        print(' output shape:', out.shape)
        self.assertTrue(out.equals(expected))

    def test_fetch_real_time_quotes_reports_feature_gap(self):
        print('\n[TestDataChannelRegistry] check realtime quotes feature gap')
        with self.assertRaises(FeatureNotImplementedError):
            fetch_real_time_quotes(channel='tushare', shares=['000001.SZ'])

    def test_fetch_basics_and_fetch_bars_plan_filters(self):
        print('\n[TestDataChannelRegistry] check fetch_basics/fetch_bars wrappers')
        with patch('qteasy.datatables.get_tables_by_name_or_usage') as mocked_tables:
            mocked_tables.return_value = {'stock_basic', 'trade_calendar'}
            basics = fetch_basics(channel='tushare', start_date='20210101', end_date='20210110')
        with patch('qteasy.datatables.get_tables_by_name_or_usage') as mocked_tables:
            mocked_tables.return_value = {'stock_daily'}
            bars = fetch_bars(channel='tushare', start_date='20210101', end_date='20210110')
        print(' basics keys:', list(basics.keys()))
        print(' bars keys:', list(bars.keys()))
        self.assertIn('stock_basic', basics)
        self.assertIn('stock_daily', bars)


if __name__ == '__main__':
    unittest.main()
