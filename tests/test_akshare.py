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

from qteasy.akfuncs import _normalize_daily_frame, _normalize_min_frame
from qteasy.data_channels import (
    AKSHARE_API_MAP,
    get_table_fetch_spec,
    iter_table_fetch_plan,
)


class TestAKShare(unittest.TestCase):

    def test_akshare_api_map_should_not_be_empty(self):
        """AKShare 映射至少应包含首批 P0 数据表。"""
        print('\n[TestAKShare] check AKSHARE_API_MAP is not empty')
        print(' map size:', len(AKSHARE_API_MAP))
        print(' map keys sample:', list(AKSHARE_API_MAP.keys())[:8])
        self.assertGreater(len(AKSHARE_API_MAP), 0)

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