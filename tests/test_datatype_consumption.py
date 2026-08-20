# coding=utf-8
# ======================================
# File:     test_datatype_consumption.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-20
# Desc:
#   Unittest for DataType consumption
#   metadata (kind / usable_in), dual-ID parse,
#   non-numeric history usable_in=none gate,
#   and qt.get_reference_data (Phase 2).
# ======================================

import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

from qteasy.core import get_reference_data
from qteasy.database import DataSource
from qteasy.datatypes import (
    DATA_TYPE_MAP,
    DataType,
    get_dtype_map,
    get_reference_data_from_source,
    infer_dtype_kind,
    infer_dtype_usable_in,
    parse_dtype_user_string,
    format_full_dtype_id,
    _sql_dtype_is_numeric,
    _history_payload_is_numeric,
)
from qteasy.datatables import get_table_column_dtype
from qteasy.history import get_history_data_packages
from qteasy.qt_operator import Operator
from qteasy.strategy import GeneralStg
from qteasy.parameter import Parameter

# 金标准：MAP 三元组 → (kind, usable_in 规范串)
# usable_in 成员按字母序拼接；none 独占
GOLD_MAP_ROWS = {
    ('close', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('pe', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('is_suspended', 'd', 'E'): ('history', 'none'),  # suspend_type 为 varchar
    ('up_limit', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('wt_idx|%', 'm', 'E'): ('history', 'history_panel,strategy,universe'),
    ('block_trade_buyer', 'd', 'E'): ('history', 'none'),  # text
    ('block_trade_seller', 'd', 'E'): ('history', 'none'),  # text
    ('block_trade_price', 'd', 'E'): ('history', 'history_panel,strategy'),  # float
    ('cn_gdp', 'q', 'None'): ('reference', 'reference_api,strategy'),
    ('north_money', 'd', 'Any'): ('reference', 'reference_api,strategy'),
    ('trade_cal', 'd', 'None'): ('reference', 'reference_api,strategy'),
    ('is_trade_day|%', 'd', 'None'): ('reference', 'reference_api,strategy'),
    ('industry', 'None', 'E'): ('static', 'static_api,universe'),
    ('list_date', 'None', 'E'): ('static', 'static_api,universe'),
    ('stock_name', 'None', 'E'): ('static', 'static_api,universe'),
    ('ths_category', 'None', 'E'): ('static', 'static_api,universe'),
    ('sw_level|%', 'None', 'IDX'): ('static', 'static_api,universe'),
    ('managers_name', 'd', 'E'): ('history', 'none'),
}

ALLOWED_KINDS = frozenset({'history', 'reference', 'static'})
ALLOWED_USABLE = frozenset({
    'strategy',
    'history_panel',
    'reference_api',
    'static_api',
    'universe',
    'none',
})


def _usable_in_set(value: str) -> frozenset:
    """把 usable_in 规范串拆成集合，便于核对成员。"""
    return frozenset(part.strip() for part in str(value).split(',') if part.strip())


class TestInferDtypeKind(unittest.TestCase):
    """派生函数的形状金标准（含 unsymbolizer 与优先级）。"""

    def test_gold_kind_from_map_keys(self):
        print('\n[TestInferDtypeKind] MAP 抽样 kind 金标准')
        for (name, freq, asset_type), (kind, _) in GOLD_MAP_ROWS.items():
            acq = DATA_TYPE_MAP[(name, freq, asset_type)][1]
            got = infer_dtype_kind(
                name=name,
                freq=freq,
                asset_type=asset_type,
                acquisition_type=acq,
            )
            print(f'  {name!r} {freq}/{asset_type} acq={acq!r} -> kind={got!r} (expect {kind!r})')
            self.assertEqual(got, kind)

    def test_unsymbolizer_name_is_reference(self):
        print('\n[TestInferDtypeKind] close-000300.SH 为 reference')
        got = infer_dtype_kind(
            name='close-000300.SH',
            freq='d',
            asset_type='E',
            acquisition_type='direct',
        )
        print(f'  kind={got!r}')
        self.assertEqual(got, 'reference')

    def test_priority_none_asset_beats_selection_static(self):
        print('\n[TestInferDtypeKind] asset_type=None 的 selection 走 reference 而非 static')
        got = infer_dtype_kind(
            name='is_trade_day|%',
            freq='d',
            asset_type='None',
            acquisition_type='selection',
        )
        print(f'  kind={got!r}')
        self.assertEqual(got, 'reference')

    def test_omitted_asset_type_does_not_mean_map_none(self):
        print('\n[TestInferDtypeKind] Python None 表示未给出，不得把 close 判成 reference')
        got = infer_dtype_kind(
            name='close',
            freq='d',
            asset_type=None,
            acquisition_type='direct',
        )
        print(f'  kind={got!r}')
        self.assertEqual(got, 'history')

    def test_omitted_freq_does_not_mean_map_none(self):
        print('\n[TestInferDtypeKind] Python None 频率未给出，不得把 close 判成 static')
        got = infer_dtype_kind(
            name='close',
            freq=None,
            asset_type='E',
            acquisition_type='direct',
        )
        print(f'  kind={got!r}')
        self.assertEqual(got, 'history')

    def test_adjustment_is_history(self):
        print('\n[TestInferDtypeKind] close|% 复权为 history')
        got = infer_dtype_kind(
            name='close|%',
            freq='d',
            asset_type='E',
            acquisition_type='adjustment',
        )
        print(f'  kind={got!r}')
        self.assertEqual(got, 'history')


class TestInferDtypeUsableIn(unittest.TestCase):
    """usable_in 金标准：独立核对规范串，不只比较两路派生。"""

    def test_gold_usable_in_from_map_keys(self):
        print('\n[TestInferDtypeUsableIn] MAP 抽样 usable_in 金标准')
        for (name, freq, asset_type), (kind, usable) in GOLD_MAP_ROWS.items():
            row = DATA_TYPE_MAP[(name, freq, asset_type)]
            acq = row[1]
            kwargs = row[2]
            got = infer_dtype_usable_in(
                name=name,
                freq=freq,
                asset_type=asset_type,
                acquisition_type=acq,
                kwargs=kwargs,
            )
            print(
                f'  {name!r} kwargs_col={kwargs.get("column")!r} '
                f'-> usable_in={got!r} (expect {usable!r}), kind={kind!r}'
            )
            self.assertEqual(got, usable)
            self.assertEqual(_usable_in_set(got), _usable_in_set(usable))

    def test_unsymbolizer_usable_in(self):
        print('\n[TestInferDtypeUsableIn] close-000300.SH usable_in')
        got = infer_dtype_usable_in(
            name='close-000300.SH',
            freq='d',
            asset_type='E',
            acquisition_type='direct',
        )
        print(f'  usable_in={got!r}')
        self.assertEqual(got, 'reference_api,strategy')
        self.assertEqual(_usable_in_set(got), frozenset({'reference_api', 'strategy'}))

    def test_none_is_exclusive(self):
        print('\n[TestInferDtypeUsableIn] event_multi_stat 的 none 独占')
        got = infer_dtype_usable_in(
            name='managers_name',
            freq='d',
            asset_type='E',
            acquisition_type='event_multi_stat',
        )
        print(f'  usable_in={got!r}')
        self.assertEqual(got, 'none')
        self.assertEqual(_usable_in_set(got), frozenset({'none'}))

    def test_history_missing_kwargs_is_none(self):
        print('\n[TestInferDtypeUsableIn] history 缺 kwargs 失败关闭为 none')
        got = infer_dtype_usable_in(
            name='close',
            freq='d',
            asset_type='E',
            acquisition_type='direct',
            kind='history',
            kwargs=None,
        )
        print(f'  usable_in={got!r}')
        self.assertEqual(got, 'none')


class TestHistoryPayloadNumeric(unittest.TestCase):
    """SQL 列类型与 history payload 数值门禁金标准。"""

    def test_sql_dtype_is_numeric_gold(self):
        print('\n[TestHistoryPayloadNumeric] _sql_dtype_is_numeric 金标准')
        cases = [
            ('float', True),
            ('double', True),
            ('int', True),
            ('int(11)', True),
            ('decimal', True),
            ('varchar(14)', False),
            ('text', False),
            ('date', False),
            ('datetime', False),
            (None, False),
            ('', False),
            ('interval', False),
        ]
        for sql_dtype, expect in cases:
            got = _sql_dtype_is_numeric(sql_dtype)
            print(f'  {sql_dtype!r} -> {got} (expect {expect})')
            self.assertEqual(got, expect)

    def test_get_table_column_dtype_block_trade(self):
        print('\n[TestHistoryPayloadNumeric] block_trade 列 dtype')
        buyer = get_table_column_dtype('block_trade', 'buyer')
        price = get_table_column_dtype('block_trade', 'price')
        missing = get_table_column_dtype('block_trade', 'no_such_col')
        print(f'  buyer={buyer!r}, price={price!r}, missing={missing!r}')
        self.assertEqual(buyer, 'text')
        self.assertEqual(price, 'float')
        self.assertIsNone(missing)

    def test_history_payload_block_trade(self):
        print('\n[TestHistoryPayloadNumeric] block_trade kwargs payload')
        buyer_kw = {'table_name': 'block_trade', 'column': 'buyer'}
        price_kw = {'table_name': 'block_trade', 'column': 'price'}
        empty_kw = {}
        print(f'  buyer numeric={_history_payload_is_numeric(buyer_kw)}')
        print(f'  price numeric={_history_payload_is_numeric(price_kw)}')
        print(f'  empty numeric={_history_payload_is_numeric(empty_kw)}')
        self.assertFalse(_history_payload_is_numeric(buyer_kw))
        self.assertTrue(_history_payload_is_numeric(price_kw))
        self.assertFalse(_history_payload_is_numeric(empty_kw))
        self.assertFalse(_history_payload_is_numeric(None))


class TestGetDtypeMapConsumptionColumns(unittest.TestCase):
    """get_dtype_map 增加 kind / usable_in，行数与现网 MAP 一致。"""

    def test_row_count_matches_data_type_map(self):
        print('\n[TestGetDtypeMapConsumptionColumns] 行数与 DATA_TYPE_MAP 一致')
        dtype_map = get_dtype_map()
        map_len = len(DATA_TYPE_MAP)
        print(f'  len(DATA_TYPE_MAP)={map_len}, len(get_dtype_map())={len(dtype_map)}')
        self.assertEqual(len(dtype_map), map_len)

    def test_columns_and_every_row_filled(self):
        print('\n[TestGetDtypeMapConsumptionColumns] 每行 kind / usable_in 非空且取值合法')
        dtype_map = get_dtype_map()
        print(f'  columns={dtype_map.columns.tolist()}')
        self.assertIn('kind', dtype_map.columns)
        self.assertIn('usable_in', dtype_map.columns)
        self.assertIn('acquisition_type', dtype_map.columns)

        kinds = dtype_map['kind']
        usables = dtype_map['usable_in']
        print(f'  kind value counts:\n{kinds.value_counts().to_string()}')
        print(f'  usable_in unique count={usables.nunique()}')
        self.assertFalse(kinds.isna().any())
        self.assertFalse(usables.isna().any())
        self.assertFalse((kinds.astype(str).str.strip() == '').any())
        self.assertFalse((usables.astype(str).str.strip() == '').any())
        self.assertTrue(set(kinds.unique()).issubset(ALLOWED_KINDS))

        for raw in usables.unique():
            tokens = _usable_in_set(raw)
            print(f'  usable_in sample {raw!r} -> {sorted(tokens)}')
            self.assertTrue(tokens)
            self.assertTrue(tokens.issubset(ALLOWED_USABLE))
            if 'none' in tokens:
                self.assertEqual(tokens, frozenset({'none'}))

    def test_gold_rows_on_map(self):
        print('\n[TestGetDtypeMapConsumptionColumns] 抽样行与金标准一致')
        dtype_map = get_dtype_map()
        for key, (kind, usable) in GOLD_MAP_ROWS.items():
            row = dtype_map.loc[key]
            print(
                f'  {key}: kind={row["kind"]!r} usable_in={row["usable_in"]!r}'
                f' (expect {kind!r}, {usable!r})'
            )
            self.assertEqual(row['kind'], kind)
            self.assertEqual(row['usable_in'], usable)

    def test_original_columns_preserved(self):
        print('\n[TestGetDtypeMapConsumptionColumns] 原有列仍在')
        dtype_map = get_dtype_map()
        print(f'  columns={dtype_map.columns.tolist()}')
        for col in ('description', 'acquisition_type', 'kwargs'):
            self.assertIn(col, dtype_map.columns)
        close_desc = dtype_map.loc[('close', 'd', 'E'), 'description']
        print(f'  close description={close_desc!r}')
        self.assertEqual(close_desc, '股票日K线 - 收盘价')


class TestParseDtypeUserString(unittest.TestCase):
    """S1.5 Phase 1：宽名 / 完整 id 解析金标准。"""

    def test_wide_and_full_id_gold(self):
        print('\n[TestParseDtypeUserString] 宽名与完整 id 解析金标准')
        cases = [
            ('close', 'wide', 'close', None, None),
            ('close_E_d', 'full', 'close', 'E', 'd'),
            ('close|b', 'wide', 'close|b', None, None),
            ('close|b_E_d', 'full', 'close|b', 'E', 'd'),
            ('close-000300.SH', 'wide', 'close-000300.SH', None, None),
            ('close-000300.SH_IDX_d', 'full', 'close-000300.SH', 'IDX', 'd'),
            ('wt_idx|000300.SH', 'wide', 'wt_idx|000300.SH', None, None),
            ('wt_idx|000300.SH_E_m', 'full', 'wt_idx|000300.SH', 'E', 'm'),
            ('c_cash_equ_end_period', 'wide', 'c_cash_equ_end_period', None, None),
            ('c_cash_equ_end_period_E_q', 'full', 'c_cash_equ_end_period', 'E', 'q'),
            ('industry_E_None', 'full', 'industry', 'E', 'None'),
            ('north_money_Any_d', 'full', 'north_money', 'Any', 'd'),
        ]
        for raw, form, wide, asset, freq in cases:
            parsed = parse_dtype_user_string(raw)
            print(
                f'  {raw!r} -> form={parsed.form!r} wide={parsed.wide_name!r} '
                f'asset={parsed.asset_type!r} freq={parsed.freq!r}'
            )
            self.assertEqual(parsed.form, form)
            self.assertEqual(parsed.wide_name, wide)
            self.assertEqual(parsed.asset_type, asset)
            self.assertEqual(parsed.freq, freq)

    def test_colon_separator_rejected(self):
        print('\n[TestParseDtypeUserString] 冒号分隔符拒绝')
        for raw in ('close:b', 'wt_id:000300.SH', 'open:b'):
            with self.assertRaises(ValueError) as ctx:
                parse_dtype_user_string(raw)
            msg = str(ctx.exception)
            print(f'  {raw!r} -> {msg}')
            self.assertIn("colon ':' is no longer a DataType separator", msg)
            self.assertIn("'|'", msg)
            self.assertIn("'-'", msg)

    def test_format_full_dtype_id_gold(self):
        print('\n[TestParseDtypeUserString] format_full_dtype_id 金标准')
        got = format_full_dtype_id('close|b', 'E', 'd')
        print(f'  format_full_dtype_id={got!r}')
        self.assertEqual(got, 'close|b_E_d')
        self.assertEqual(format_full_dtype_id('close', 'E,IDX', 'd'), 'close_E,IDX_d')


class TestDataTypeDualIdInit(unittest.TestCase):
    """S1.5 Phase 1：DataType 构造接受完整 id，宽名歧义报错。"""

    def test_full_id_constructs_same_as_explicit_params(self):
        print('\n[TestDataTypeDualIdInit] 完整 id 与显式参数等价')
        dt_full = DataType('close_E_d')
        dt_parts = DataType(name='close', freq='d', asset_type='E')
        print(
            f'  full: name={dt_full.name!r} freq={dt_full.freq!r} '
            f'asset={dt_full.asset_type!r} dtype_id={dt_full.dtype_id!r}'
        )
        print(
            f'  parts: name={dt_parts.name!r} freq={dt_parts.freq!r} '
            f'asset={dt_parts.asset_type!r} dtype_id={dt_parts.dtype_id!r}'
        )
        self.assertEqual(dt_full.name, 'close')
        self.assertEqual(dt_full.freq, 'd')
        self.assertEqual(dt_full.asset_type, 'E')
        self.assertEqual(dt_full.dtype_id, 'close_E_d')
        self.assertEqual(dt_full.dtype_id, dt_parts.dtype_id)
        self.assertEqual(dt_full, dt_parts)

        dt_adj = DataType('close|b_E_d')
        print(f'  close|b_E_d: name={dt_adj.name!r} dtype_id={dt_adj.dtype_id!r}')
        self.assertEqual(dt_adj.name, 'close|b')
        self.assertEqual(dt_adj.freq, 'd')
        self.assertEqual(dt_adj.asset_type, 'E')
        self.assertEqual(dt_adj.dtype_id, 'close|b_E_d')

    def test_full_id_conflicts_with_kwargs(self):
        print('\n[TestDataTypeDualIdInit] 完整 id 与显式参数冲突')
        with self.assertRaises(ValueError) as ctx:
            DataType('close_E_d', freq='w')
        msg = str(ctx.exception)
        print(f'  freq conflict: {msg}')
        self.assertIn('conflicts with freq=', msg)
        with self.assertRaises(ValueError) as ctx:
            DataType('close_E_d', asset_type='IDX')
        msg = str(ctx.exception)
        print(f'  asset conflict: {msg}')
        self.assertIn('conflicts with asset_type=', msg)

    def test_ambiguous_wide_name_lists_full_ids(self):
        print('\n[TestDataTypeDualIdInit] 宽名歧义列出完整 id')
        with self.assertRaises(ValueError) as ctx:
            DataType('close')
        msg = str(ctx.exception)
        print(f'  close -> {msg}')
        self.assertIn('Ambiguous DataType name', msg)
        self.assertIn('close_E_d', msg)
        self.assertIn('close_IDX_d', msg)

        with self.assertRaises(ValueError) as ctx:
            DataType('close|b')
        msg = str(ctx.exception)
        print(f'  close|b -> {msg}')
        self.assertIn('Ambiguous DataType name', msg)
        self.assertIn('close|b_E_d', msg)

    def test_unique_wide_name_succeeds(self):
        print('\n[TestDataTypeDualIdInit] 无歧义宽名可构造')
        dt = DataType('industry')
        print(f'  industry dtype_id={dt.dtype_id!r} freq={dt.freq!r} asset={dt.asset_type!r}')
        self.assertEqual(dt.dtype_id, 'industry_E_None')
        self.assertEqual(dt.freq, 'None')
        self.assertEqual(dt.asset_type, 'E')

    def test_explicit_multi_asset_still_allowed(self):
        print('\n[TestDataTypeDualIdInit] 显式多资产仍走第一匹配')
        dt = DataType(name='pe', freq='d', asset_type='E, IDX')
        print(f'  pe E,IDX -> asset={dt.asset_type!r} dtype_id={dt.dtype_id!r}')
        self.assertEqual(dt.name, 'pe')
        self.assertEqual(dt.freq, 'd')
        self.assertIn(dt.asset_type, ('E', 'IDX'))

    def test_colon_on_datatype_init(self):
        print('\n[TestDataTypeDualIdInit] DataType 拒绝冒号')
        with self.assertRaises(ValueError) as ctx:
            DataType('close:b')
        msg = str(ctx.exception)
        print(f'  {msg}')
        self.assertIn("colon ':' is no longer a DataType separator", msg)


class TestGetReferenceDataAPI(unittest.TestCase):
    """公开入口 qt.get_reference_data：宏观无 shares、unsymbolizer、错形状报错。"""

    def setUp(self):
        print('\n[TestGetReferenceDataAPI] setUp: temp DataSource + cn_gdp / north_money / index_daily')
        self.test_data_path = tempfile.mkdtemp(prefix='temp_test_get_reference_data_')
        self.data_source = DataSource(source_type='file', file_loc=self.test_data_path)
        self.dates = pd.date_range('2023-01-03', '2023-01-20', freq='B')
        self.index_share = '000300.SH'
        n = len(self.dates)

        # 北向资金（日频宏观，无标的维）
        self.north_gold = np.array(
            [101.0, 102.5, 103.0, 104.5, 105.0, 106.5, 107.0, 108.5,
             109.0, 110.5, 111.0, 112.5, 113.0, 114.5],
            dtype=float,
        )
        north_df = pd.DataFrame({
            'trade_date': self.dates,
            'ggt_ss': 1.0,
            'ggt_sz': 1.0,
            'hgt': 1.0,
            'sgt': 1.0,
            'north_money': self.north_gold,
            'south_money': 2.0,
        })
        self.data_source.update_table_data('hs_money_flow', df=north_df, merge_type='update')

        # GDP（季度宏观）
        self.gdp_quarters = ['2022Q1', '2022Q2', '2022Q3', '2022Q4']
        self.gdp_gold = np.array([270000.0, 280000.0, 290000.0, 300000.0], dtype=float)
        gdp_df = pd.DataFrame({
            'quarter': self.gdp_quarters,
            'gdp': self.gdp_gold,
            'gdp_yoy': 5.0,
            'pi': 1.0,
            'pi_yoy': 1.0,
            'si': 1.0,
            'si_yoy': 1.0,
            'ti': 1.0,
            'ti_yoy': 1.0,
        })
        self.data_source.update_table_data('cn_gdp', df=gdp_df, merge_type='update')

        # 指数日线，供 close-000300.SH unsymbolizer
        rng = np.random.RandomState(50)
        o = rng.rand(n) * 3000 + 3000
        self.index_close_gold = (o + 50 + o - 50) / 2
        idx_data = pd.DataFrame({
            'ts_code': [self.index_share] * n,
            'trade_date': self.dates,
            'open': o,
            'high': o + 50,
            'low': o - 50,
            'close': self.index_close_gold,
            'pre_close': self.index_close_gold,
            'change': 0.0,
            'pct_chg': 0.0,
            'vol': rng.randint(100000, 500000, n).astype(float),
            'amount': (rng.rand(n) * 1e9),
        })
        self.data_source.update_table_data('index_daily', df=idx_data, merge_type='update')
        print('  path:', self.test_data_path, 'n_dates:', n)

    def tearDown(self):
        if os.path.exists(self.test_data_path):
            shutil.rmtree(self.test_data_path)
        print('[TestGetReferenceDataAPI] tearDown: removed', self.test_data_path)

    def test_macro_north_money_without_shares(self):
        print('\n[TestGetReferenceDataAPI] north_money 无需 shares')
        res = get_reference_data(
            'north_money',
            data_source=self.data_source,
            start='20230103',
            end='20230120',
            freq='d',
        )
        print('  keys:', list(res.keys()))
        self.assertIsInstance(res, dict)
        self.assertIn('north_money_Any_d', res)
        ser = res['north_money_Any_d']
        print('  series head:\n', ser.head())
        print('  gold:', self.north_gold[:5])
        self.assertIsInstance(ser, pd.Series)
        self.assertFalse(ser.empty)
        np.testing.assert_allclose(
            ser.dropna().values.astype(float),
            self.north_gold.astype(float),
            rtol=1e-5,
        )

    def test_macro_cn_gdp_without_shares(self):
        print('\n[TestGetReferenceDataAPI] cn_gdp 无需 shares')
        res = get_reference_data(
            'cn_gdp',
            data_source=self.data_source,
            start='20220101',
            end='20231231',
        )
        print('  keys:', list(res.keys()))
        self.assertIn('cn_gdp_None_q', res)
        ser = res['cn_gdp_None_q']
        print('  series:\n', ser)
        print('  gold:', self.gdp_gold)
        self.assertIsInstance(ser, pd.Series)
        np.testing.assert_allclose(
            ser.dropna().values.astype(float),
            self.gdp_gold.astype(float),
            rtol=1e-5,
        )

    def test_unsymbolizer_close_index(self):
        print('\n[TestGetReferenceDataAPI] close-000300.SH_IDX_d unsymbolizer')
        res = get_reference_data(
            'close-000300.SH_IDX_d',
            data_source=self.data_source,
            start='20230103',
            end='20230120',
            freq='d',
        )
        key = 'close-000300.SH_IDX_d'
        print('  keys:', list(res.keys()))
        self.assertIn(key, res)
        ser = res[key]
        print('  series head:\n', ser.head())
        print('  gold head:', self.index_close_gold[:5])
        self.assertIsInstance(ser, pd.Series)
        np.testing.assert_allclose(
            ser.dropna().values.astype(float),
            self.index_close_gold.astype(float),
            rtol=1e-5,
        )

    def test_unsymbolizer_wide_with_asset_type(self):
        print('\n[TestGetReferenceDataAPI] 宽名 close-000300.SH + asset_type=IDX')
        res = get_reference_data(
            'close-000300.SH',
            data_source=self.data_source,
            start='20230103',
            end='20230120',
            freq='d',
            asset_type='IDX',
        )
        ser = res['close-000300.SH_IDX_d']
        print('  first values:', ser.dropna().values[:3])
        print('  gold first:', self.index_close_gold[:3])
        np.testing.assert_allclose(
            ser.dropna().values.astype(float),
            self.index_close_gold.astype(float),
            rtol=1e-5,
        )

    def test_api_matches_from_source_and_packages(self):
        print('\n[TestGetReferenceDataAPI] API / from_source / packages 数值一致 + 金标准')
        dtype = DataType(name='close-000300.SH', freq='d', asset_type='IDX')
        api = get_reference_data(
            'close-000300.SH_IDX_d',
            data_source=self.data_source,
            start='20230103',
            end='20230120',
            freq='d',
        )
        from_src = get_reference_data_from_source(
            self.data_source,
            htypes=[dtype],
            start='20230103',
            end='20230120',
            freq='d',
        )
        packages = get_history_data_packages(
            data_types=dtype,
            data_source=self.data_source,
            shares=None,
            start='20230103',
            end='20230120',
        )
        key = 'close-000300.SH_IDX_d'
        api_ser = api[key]
        src_ser = from_src[key]
        pkg_val = packages[key]
        if isinstance(pkg_val, pd.DataFrame):
            pkg_ser = pkg_val.iloc[:, 0]
        else:
            pkg_ser = pkg_val
        print('  api head:', api_ser.dropna().values[:3])
        print('  from_src head:', src_ser.dropna().values[:3])
        print('  packages head:', np.asarray(pkg_ser.dropna().values[:3], dtype=float))
        print('  gold head:', self.index_close_gold[:3])
        np.testing.assert_allclose(
            api_ser.dropna().values.astype(float),
            self.index_close_gold.astype(float),
            rtol=1e-5,
        )
        np.testing.assert_allclose(
            api_ser.dropna().values.astype(float),
            src_ser.dropna().values.astype(float),
            rtol=1e-5,
        )
        np.testing.assert_allclose(
            api_ser.dropna().values.astype(float),
            np.asarray(pkg_ser.dropna().values, dtype=float),
            rtol=1e-5,
        )

    def test_rejects_history_shape(self):
        print('\n[TestGetReferenceDataAPI] 误传 history 指向 get_history_data')
        with self.assertRaises(ValueError) as ctx:
            get_reference_data(
                'close_E_d',
                data_source=self.data_source,
                start='20230103',
                end='20230120',
            )
        msg = str(ctx.exception)
        print(f'  {msg}')
        self.assertIn('get_history_data', msg)
        self.assertIn('history', msg.lower())

    def test_rejects_static_shape(self):
        print('\n[TestGetReferenceDataAPI] 误传 static 指向 get_static_data')
        with self.assertRaises(ValueError) as ctx:
            get_reference_data(
                'industry',
                data_source=self.data_source,
                start='20230103',
                end='20230120',
            )
        msg = str(ctx.exception)
        print(f'  {msg}')
        self.assertIn('get_static_data', msg)
        self.assertIn('static', msg.lower())

    def test_operator_buffer_keeps_reference_series(self):
        print('\n[TestGetReferenceDataAPI] Operator 缓冲保留 Reference Series')
        ref = get_reference_data(
            'close-000300.SH_IDX_d',
            data_source=self.data_source,
            start='20230103',
            end='20230120',
            freq='d',
        )
        ref_key = 'close-000300.SH_IDX_d'
        ref_ser = ref[ref_key]
        # 历史侧用与参考同 index 的假面板，仅验证 Series 可进缓冲
        close_df = pd.DataFrame(
            {'A': np.linspace(1.0, 2.0, len(ref_ser))},
            index=ref_ser.index,
        )

        class _RefBufStg(GeneralStg):
            def __init__(self):
                super().__init__(
                    name='ref_buf_stg',
                    description='reference buffer smoke',
                    pars=[Parameter((1, 3), name='n', par_type='int', value=1)],
                    data_types=[
                        DataType(name='close', freq='d', asset_type='E'),
                        DataType(name='close-000300.SH', freq='d', asset_type='IDX'),
                    ],
                    window_length=[3, 3],
                    use_latest_data_cycle=[False, False],
                )

            def realize(self):
                close_w = self.get_data('close_E_d')
                ref_w = self.get_data('close-000300.SH_IDX_d')
                return np.zeros(close_w.shape[-1] if close_w.ndim > 1 else 1)

        op = Operator(strategies=[_RefBufStg], signal_type='PS')
        op.prepare_data_buffer(
            start_date=ref_ser.index[3],
            end_date=ref_ser.index[-1],
            data_package={
                'close_E_d': close_df,
                ref_key: ref_ser,
            },
        )
        buffered = op.data_buffers[ref_key]
        print('  buffered type:', type(buffered).__name__, 'len:', len(buffered))
        print('  buffered head:', buffered.head().values)
        print('  gold head:', self.index_close_gold[:5])
        self.assertIsInstance(buffered, pd.Series)
        np.testing.assert_allclose(
            buffered.dropna().values.astype(float),
            self.index_close_gold.astype(float),
            rtol=1e-5,
        )


if __name__ == '__main__':
    unittest.main()
