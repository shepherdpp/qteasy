# coding=utf-8
# ======================================
# File:     test_akshare.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-02-02
# Desc:
#   Unittest for all akshare data
#   acquiring APIs.
# ======================================

import unittest

import pandas as pd

from qteasy.akfuncs import (
    _code_to_ts_code,
    _normalize_adj_frame,
    _normalize_daily_frame,
    _normalize_min_frame,
    _normalize_stock_basic,
    _normalize_trade_calendar,
)
from qteasy.data_channels import (
    AKSHARE_API_MAP,
    get_table_fetch_spec,
    iter_table_fetch_plan,
    list_channel_tables,
)

# S3.2b 已实现表（不含 REALTIME 映射）
AKSHARE_IMPLEMENTED_TABLES = [
    'trade_calendar', 'stock_basic', 'index_basic', 'fund_basic',
    'stock_daily', 'stock_weekly', 'stock_monthly',
    'stock_1min', 'stock_5min', 'stock_15min', 'stock_30min', 'stock_hourly',
    'stock_adj_factor',
    'index_daily', 'index_weekly', 'index_monthly',
    'fund_daily', 'fund_weekly', 'fund_monthly', 'fund_1min',
    'stock_suspend', 'money_flow', 'dividend', 'new_share', 'stock_company',
]


class TestAKShare(unittest.TestCase):

    def test_akshare_api_map_should_cover_p1_batch(self):
        """AKShare 映射应覆盖 S3.2b 扩表后的 P1 批次表。"""
        print('\n[TestAKShare] check AKSHARE_API_MAP P1 batch coverage')
        print(' map size:', len(AKSHARE_API_MAP))
        print(' map keys:', sorted(AKSHARE_API_MAP.keys()))
        for table in AKSHARE_IMPLEMENTED_TABLES:
            self.assertIn(table, AKSHARE_API_MAP, f'missing table in map: {table}')
        self.assertGreaterEqual(len(AKSHARE_API_MAP), len(AKSHARE_IMPLEMENTED_TABLES))

    def test_akshare_list_channel_tables_matches_map(self):
        """list_channel_tables 与 AKSHARE_API_MAP 键集合一致。"""
        print('\n[TestAKShare] list_channel_tables vs map keys')
        tables = list_channel_tables('akshare')
        print(' channel tables count:', len(tables))
        self.assertEqual(set(tables), set(AKSHARE_API_MAP.keys()))

    def test_akshare_p0_specs_should_be_discoverable(self):
        """首批 P0 表必须能通过统一 spec 接口发现。"""
        print('\n[TestAKShare] check P0 specs are discoverable')
        p0_tables = ['stock_daily', 'index_daily', 'fund_daily', 'stock_1min']
        for table in p0_tables:
            spec = get_table_fetch_spec('akshare', table)
            print(
                f' table={table}, api={spec.api}, fill_arg_name={spec.fill_arg_name}, '
                f'fill_arg_type={spec.fill_arg_type}, allow_start_end={spec.allow_start_end}'
            )
            self.assertIsInstance(spec.api, str)
            self.assertTrue(spec.api)
            self.assertEqual(spec.fill_arg_name, 'qt_code')
            self.assertEqual(spec.fill_arg_type, 'table_index')
            self.assertEqual(spec.allow_start_end.upper(), 'Y')

    def test_akshare_basics_specs(self):
        """基础表 spec：list 或 none 类型。"""
        print('\n[TestAKShare] basics table specs')
        trade_spec = get_table_fetch_spec('akshare', 'trade_calendar')
        print(' trade_calendar:', trade_spec.fill_arg_type, trade_spec.api)
        self.assertEqual(trade_spec.api, 'trade_cal')
        self.assertEqual(trade_spec.fill_arg_type, 'list')
        index_spec = get_table_fetch_spec('akshare', 'index_basic')
        print(' index_basic:', index_spec.fill_arg_type, index_spec.api)
        self.assertEqual(index_spec.api, 'index_basic')
        self.assertEqual(index_spec.fill_arg_type, 'list')

    def test_akshare_index_weekly_monthly_specs(self):
        """指数周月线应可发现且为 table_index。"""
        print('\n[TestAKShare] index weekly/monthly specs')
        for table in ('index_weekly', 'index_monthly'):
            spec = get_table_fetch_spec('akshare', table)
            print(f' {table}: api={spec.api}, type={spec.fill_arg_type}')
            self.assertEqual(spec.api, table)
            self.assertEqual(spec.fill_arg_type, 'table_index')

    def test_akshare_parse_args_contract(self):
        """AKShare 参数解析应生成 qt_code + start/end 契约。"""
        print('\n[TestAKShare] check parse args contract for akshare bars')
        args = list(iter_table_fetch_plan(
            table='stock_daily',
            channel='akshare',
            symbols='000001.SZ',
            start_date='20240101',
            end_date='20240110',
            list_arg_filter=None,
            reversed_par_seq=False,
        ))
        print(' arg count:', len(args))
        print(' first arg:', args[0] if args else None)
        self.assertGreater(len(args), 0)
        self.assertIn('qt_code', args[0])
        self.assertIn('start', args[0])
        self.assertIn('end', args[0])

    def test_akshare_trade_calendar_parse_contract(self):
        """交易日历应按 exchange 列表解析参数。"""
        print('\n[TestAKShare] trade_calendar parse contract')
        args = list(iter_table_fetch_plan(
            table='trade_calendar',
            channel='akshare',
            symbols=None,
            start_date='20240101',
            end_date='20240110',
            list_arg_filter='SSE',
            reversed_par_seq=False,
        ))
        print(' args:', args)
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0]['exchange'], 'SSE')

    def test_code_to_ts_code_rules(self):
        """6 位代码到 ts_code 规则应稳定。"""
        print('\n[TestAKShare] code_to_ts_code rules')
        samples = {
            '000001': '000001.SZ',
            '600000': '600000.SH',
            '688001': '688001.SH',
            '430047': '430047.BJ',
        }
        for code, expected in samples.items():
            got = _code_to_ts_code(code)
            print(f' {code} -> {got}')
            self.assertEqual(got, expected)

    def test_akshare_daily_normalization_contract(self):
        """日线字段规范化应输出 qteasy bars 标准列。"""
        print('\n[TestAKShare] check daily normalization contract')
        raw = pd.DataFrame({
            '日期': ['2024-01-02', '2024-01-03'],
            '开盘': [10.0, 10.5],
            '最高': [10.8, 10.9],
            '最低': [9.9, 10.1],
            '收盘': [10.6, 10.3],
            '成交量': [123456, 98765],
            '成交额': [1234500, 1012300],
        })
        norm = _normalize_daily_frame(raw, qt_code='000001.SZ')
        print(' normalized daily columns:', norm.columns.tolist())
        print(' normalized daily frame:\n', norm)
        self.assertEqual(
            norm.columns.tolist(),
            ['ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
             'pre_close', 'change', 'pct_chg', 'vol', 'amount']
        )
        self.assertEqual(norm.iloc[0]['trade_date'], '20240102')
        self.assertEqual(norm.iloc[1]['ts_code'], '000001.SZ')

    def test_akshare_adj_normalization_contract(self):
        """复权因子规范化应输出 adj_factors 标准列。"""
        print('\n[TestAKShare] adj normalization contract')
        raw = pd.DataFrame({
            'date': ['2024-01-02', '2024-01-03'],
            'qfq_factor': [1.0, 1.01],
        })
        norm = _normalize_adj_frame(raw, qt_code='000001.SZ')
        print(' adj norm:\n', norm)
        self.assertEqual(norm.columns.tolist(), ['ts_code', 'trade_date', 'adj_factor'])
        self.assertAlmostEqual(norm.iloc[1]['adj_factor'], 1.01)

    def test_akshare_trade_calendar_normalization_contract(self):
        """交易日历规范化应含 exchange 与 pretrade_date。"""
        print('\n[TestAKShare] trade calendar normalization')
        raw_dates = pd.Series(['2024-01-02', '2024-01-03'])
        norm = _normalize_trade_calendar(raw_dates, exchange='SSE')
        print(' calendar norm:\n', norm)
        self.assertIsNone(norm.iloc[0]['pretrade_date'])
        self.assertEqual(norm.iloc[1]['pretrade_date'], '20240102')
        self.assertEqual(norm.iloc[1]['exchange'], 'SSE')
        self.assertEqual(int(norm.iloc[1]['is_open']), 1)

    def test_akshare_stock_basic_date_columns_use_sql_null(self):
        """stock_basic 未知上市/退市日期须为 None，避免 MySQL DATE 写入空串。"""
        print('\n[TestAKShare] stock_basic date columns for SQL NULL')
        raw = pd.DataFrame({'code': ['000001', '600000'], 'name': ['平安银行', '浦发银行']})
        norm = _normalize_stock_basic(raw)
        print(' stock_basic sample:\n', norm[['ts_code', 'list_date', 'delist_date']].head())
        self.assertTrue(norm['list_date'].isna().all())
        self.assertTrue(norm['delist_date'].isna().all())
        self.assertEqual(norm.iloc[0]['ts_code'], '000001.SZ')

    def test_akshare_min_normalization_contract(self):
        """分钟字段规范化应输出 qteasy min_bars 标准列。"""
        print('\n[TestAKShare] check minute normalization contract')
        raw = pd.DataFrame({
            '时间': ['2024-01-03 09:31:00', '2024-01-03 09:32:00'],
            '开盘': [10.1, 10.2],
            '最高': [10.2, 10.4],
            '最低': [10.0, 10.1],
            '收盘': [10.15, 10.35],
            '成交量': [1000, 1500],
            '成交额': [10100, 15200],
        })
        norm = _normalize_min_frame(raw, qt_code='000001.SZ')
        print(' normalized minute columns:', norm.columns.tolist())
        print(' normalized minute frame:\n', norm)
        self.assertEqual(
            norm.columns.tolist(),
            ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount']
        )
        self.assertEqual(norm.iloc[0]['trade_time'], '20240103 09:31:00')
        self.assertEqual(norm.iloc[1]['ts_code'], '000001.SZ')


if __name__ == '__main__':
    unittest.main()
