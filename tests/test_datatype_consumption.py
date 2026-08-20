# coding=utf-8
# ======================================
# File:     test_datatype_consumption.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-20
# Desc:
#   Unittest for DataType consumption
#   metadata: kind and usable_in (S1.5 Phase 0).
# ======================================

import unittest

from qteasy.datatypes import (
    DATA_TYPE_MAP,
    get_dtype_map,
    infer_dtype_kind,
    infer_dtype_usable_in,
)

# 金标准：MAP 三元组 → (kind, usable_in 规范串)
# usable_in 成员按字母序拼接；none 独占
GOLD_MAP_ROWS = {
    ('close', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('pe', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('is_suspended', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('up_limit', 'd', 'E'): ('history', 'history_panel,strategy'),
    ('wt_idx|%', 'm', 'E'): ('history', 'history_panel,strategy,universe'),
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
            acq = DATA_TYPE_MAP[(name, freq, asset_type)][1]
            got = infer_dtype_usable_in(
                name=name,
                freq=freq,
                asset_type=asset_type,
                acquisition_type=acq,
            )
            print(f'  {name!r} -> usable_in={got!r} (expect {usable!r}), kind={kind!r}')
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


if __name__ == '__main__':
    unittest.main()
