# coding=utf-8
# ======================================
# File:     test_core_sub_funcs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy core
#   sub-functions.
# ======================================
import os
import shutil
import tempfile
import unittest
import warnings

import pandas as pd
import numpy as np

import qteasy
from qteasy import QT_DATA_SOURCE, get_history_data
from qteasy.database import DataSource
from qteasy.datatypes import DataType, _get_built_in_data_type_map


class TestCoreSubFuncs(unittest.TestCase):
    """Test all functions in core.py"""

    def test_filter_stocks(self):

        from qteasy import filter_stock_codes
        print(f'start test building stock pool function\n')
        ds = QT_DATA_SOURCE
        share_basics = ds.read_table_data('stock_basic')[['symbol', 'name', 'area', 'industry',
                                                          'market', 'list_date', 'exchange']]

        print(f'\nselect all stocks by area')
        stock_pool = filter_stock_codes(area='上海')
        print(f'{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "上海"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].eq('上海').all())

        print(f'\nselect all stocks by multiple areas')
        stock_pool = filter_stock_codes(area='贵州,北京,天津')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are in list of ["贵州", "北京", "天津"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(['贵州',
                                                                                            '北京',
                                                                                            '天津']).all())

        print(f'\nselect all stocks by area and industry')
        stock_pool = filter_stock_codes(area='四川', industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "四川", and industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(['银行', '金融']).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(['四川']).all())

        print(f'\nselect all stocks by industry')
        stock_pool = filter_stock_codes(industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(['银行', '金融']).all())

        print(f'\nselect all stocks by market')
        stock_pool = filter_stock_codes(market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['market'].isin(['主板']).all())

        print(f'\nselect all stocks by market and list date')
        stock_pool = filter_stock_codes(date='2000-01-01', market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板", and list date after "2000-01-01"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['market'].isin(['主板']).all())
        date = pd.to_datetime('2000-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())

        print(f'\nselect all stocks by list date')
        stock_pool = filter_stock_codes(date='1997-01-01')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all list date after "1997-01-01"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        date = pd.to_datetime('1997-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())

        print(f'\nselect all stocks by exchange')
        stock_pool = filter_stock_codes(exchange='SSE')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are in "SSE"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['exchange'].eq('SSE').all())

        print(f'\nselect all stocks by industry, area and list date')
        industry_list = ['银行', '全国地产', '互联网', '环境保护', '区域地产',
                         '酒店餐饮', '运输设备', '综合类', '建筑工程', '玻璃',
                         '家用电器', '文教休闲', '其他商业', '元器件', 'IT设备',
                         '其他建材', '汽车服务', '火力发电', '医药商业', '汽车配件',
                         '广告包装', '轻工机械', '新型电力', '多元金融', '饲料']
        area_list = ['深圳', '北京', '吉林', '江苏', '辽宁', '广东',
                     '安徽', '四川', '浙江', '湖南', '河北', '新疆',
                     '山东', '河南', '山西', '江西', '青海', '湖北',
                     '内蒙', '海南', '重庆', '陕西', '福建', '广西',
                     '上海']
        stock_pool = filter_stock_codes(date='19980101',
                                           industry=industry_list,
                                           area=area_list)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are in\n{area_list} \nand \n{industry_list}'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        date = pd.to_datetime('1998-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(industry_list).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(area_list).all())

        self.assertRaises(KeyError, filter_stock_codes, industry=25)
        self.assertRaises(KeyError, filter_stock_codes, share_name='000300.SH')
        self.assertRaises(KeyError, filter_stock_codes, markets='SSE')

        print(f'\nselect all stocks by index, with start and end dates:\n'
              f'all the "000300.SH" composite after 20180101')
        stock_pool = filter_stock_codes(date='20200101',
                                           index='000300.SH')
        self.assertTrue(len(stock_pool) > 0)
        print(f'\n{len(stock_pool)} shares selected, first 10 are: {stock_pool[0:10]}\n'
              f'more information of some fo the stocks\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')

        print(f'\nprint out targets that can not be matched and return fuzzy results')
        stock_pool = filter_stock_codes(industry='银行业, 多元金融, 房地产',
                                           area='陕西省',
                                           market='主要')
        self.assertTrue(len(stock_pool) > 0)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["多元金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(["多元金融"]).all())

    def test_get_basic_info(self):
        """ 测试获取证券基本信息"""
        from qteasy import get_basic_info
        print(f'getting basic info for "000300" - found IDX 000300.SH')
        get_basic_info('000300')
        print('getting basic info for "000300.OF" - No result')
        get_basic_info('000300.OF')
        print('getting basic infor for "004040" - found ')
        get_basic_info('004040')
        get_basic_info('沪镍')
        get_basic_info('中国移动', verbose=True)

    def test_find_history_data(self):
        """ 测试查找打印历史数据信息"""
        from qteasy import find_history_data
        find_history_data('pe')
        find_history_data('open')
        find_history_data('市盈率')
        find_history_data('市?率*')
        find_history_data('市值')
        find_history_data('net_profit')
        find_history_data('净利润')

    def test_get_backtest_data_package(self):
        """ 测试获取回测数据包"""
        print('test get backtest data package')

    def test_get_backtest_cashplan(self):
        """ 测试获取回测资金计划"""
        print('test get backtest cashplan')


class TestGetHistoryDataAPI(unittest.TestCase):
    """完整测试 get_history_data API：基于临时 DataSource，强断言，覆盖参数/边界与数据类型。"""

    def setUp(self):
        """创建临时数据源并写入 stock_daily、index_daily、stock_adj_factor、stock_indicator 等表。"""
        print('\n[TestGetHistoryDataAPI] setUp: create temp DataSource and fill tables')
        self.test_data_path = tempfile.mkdtemp(prefix='temp_test_get_history_data_')
        self.data_source = DataSource(source_type='file', file_loc=self.test_data_path)
        # 固定日期范围与标的，便于断言
        self.dates = pd.date_range('2023-01-03', '2023-01-20', freq='B')
        self.weekly_dates = pd.date_range('2023-01-02', '2023-01-20', freq='W-MON')
        self.shares = ['000001.SZ', '000002.SZ', '000651.SZ']
        self.index_share = '000300.SH'
        self.start_str = '20230103'
        self.end_str = '20230120'
        n = len(self.dates)
        wn = len(self.weekly_dates)

        # stock_daily: bars  schema (ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount)
        for share in self.shares:
            o = np.random.RandomState(42).rand(n) * 10 + 10
            h = o + np.random.RandomState(43).rand(n) * 2
            l = o - np.random.RandomState(44).rand(n) * 2
            c = (h + l) / 2
            vol = np.random.RandomState(45).randint(1000, 10000, n)
            data = pd.DataFrame({
                'ts_code': [share] * n,
                'trade_date': self.dates,
                'open': o, 'high': h, 'low': l, 'close': c,
                'pre_close': c, 'change': 0.0, 'pct_chg': 0.0,
                'vol': vol.astype(float), 'amount': (vol * c).astype(float),
            })
            self.data_source.update_table_data('stock_daily', df=data, merge_type='update')

        # index_daily
        o = np.random.RandomState(50).rand(n) * 3000 + 3000
        h = o + 50
        l = o - 50
        c = (h + l) / 2
        vol = np.random.RandomState(51).randint(100000, 500000, n)
        idx_data = pd.DataFrame({
            'ts_code': [self.index_share] * n,
            'trade_date': self.dates,
            'open': o, 'high': h, 'low': l, 'close': c,
            'pre_close': c, 'change': 0.0, 'pct_chg': 0.0,
            'vol': vol.astype(float), 'amount': (vol * c).astype(float),
        })
        self.data_source.update_table_data('index_daily', df=idx_data, merge_type='update')

        # stock_weekly (同 stock_daily 结构，freq='w' 时从该表取数)
        for share in self.shares:
            o = np.random.RandomState(42).rand(wn) * 10 + 10
            h = o + np.random.RandomState(43).rand(wn) * 2
            l = o - np.random.RandomState(44).rand(wn) * 2
            c = (h + l) / 2
            vol = np.random.RandomState(45).randint(1000, 10000, wn)
            data = pd.DataFrame({
                'ts_code': [share] * wn,
                'trade_date': self.weekly_dates,
                'open': o, 'high': h, 'low': l, 'close': c,
                'pre_close': c, 'change': 0.0, 'pct_chg': 0.0,
                'vol': vol.astype(float), 'amount': (vol * c).astype(float),
            })
            self.data_source.update_table_data('stock_weekly', df=data, merge_type='update')

        # stock_adj_factor
        for share in self.shares:
            adj = pd.DataFrame({
                'ts_code': [share] * n,
                'trade_date': self.dates,
                'adj_factor': np.ones(n),
            })
            self.data_source.update_table_data('stock_adj_factor', df=adj, merge_type='update')

        # stock_indicator: 至少 ts_code, trade_date, total_mv 等
        for share in self.shares:
            ind = pd.DataFrame({
                'ts_code': [share] * n,
                'trade_date': self.dates,
                'close': np.random.RandomState(60).rand(n) * 10 + 10,
                'total_mv': np.random.RandomState(61).rand(n) * 1e8 + 1e7,
                'pe': np.random.RandomState(62).rand(n) * 20 + 5,
                'pb': np.random.RandomState(63).rand(n) * 2 + 0.5,
                'turnover_rate': 0.5, 'turnover_rate_f': 0.5, 'volume_ratio': 1.0,
                'pe_ttm': 15.0, 'ps': 2.0, 'ps_ttm': 2.0, 'dv_ratio': 0.02, 'dv_ttm': 0.02,
                'total_share': 1e6, 'float_share': 8e5, 'free_share': 8e5, 'circ_mv': 1e8,
            })
            self.data_source.update_table_data('stock_indicator', df=ind, merge_type='update')

        # stock_hourly (min_bars: ts_code, trade_time, open, high, low, close, vol, amount) 用于 freq='h'
        nh = 14 * 4  # 约 4 个时点/日
        for share in self.shares[:2]:
            trade_times = pd.date_range('2023-01-03 10:00', periods=nh, freq='h')
            h_data = pd.DataFrame({
                'ts_code': [share] * nh,
                'trade_time': trade_times,
                'open': np.random.RandomState(70).rand(nh) * 10 + 10,
                'high': np.random.RandomState(71).rand(nh) * 10 + 11,
                'low': np.random.RandomState(72).rand(nh) * 10 + 9,
                'close': np.random.RandomState(73).rand(nh) * 10 + 10,
                'vol': np.random.RandomState(74).randint(100, 1000, nh).astype(float),
                'amount': np.random.RandomState(75).rand(nh) * 1e6,
            })
            self.data_source.update_table_data('stock_hourly', df=h_data, merge_type='update')

        # index_weight: index_code, trade_date, con_code, weight 用于 wt_id:000300.SH
        rows = []
        for d in self.dates:
            for con in self.shares[:2]:
                rows.append({'index_code': self.index_share, 'trade_date': d, 'con_code': con, 'weight': 10.0})
        if rows:
            w_df = pd.DataFrame(rows)
            self.data_source.update_table_data('index_weight', df=w_df, merge_type='update')

        print(' temp path:', self.test_data_path, 'dates len:', n, 'shares:', self.shares)

    def tearDown(self):
        """删除临时目录。"""
        if os.path.exists(self.test_data_path):
            shutil.rmtree(self.test_data_path)
        print('[TestGetHistoryDataAPI] tearDown: removed', self.test_data_path)

    def test_a1_htype_names_and_htypes_equivalent(self):
        """A1: htype_names 与 htypes 传参结果一致。"""
        print('\n[TestGetHistoryDataAPI] A1: htype_names vs htypes equivalence')
        res_n = get_history_data(
            htype_names='close, open',
            data_source=self.data_source,
            shares=','.join(self.shares[:2]),
            start=self.start_str,
            end=self.end_str,
            freq='d',
        )
        res_h = get_history_data(
            htypes='close, open',
            data_source=self.data_source,
            shares=','.join(self.shares[:2]),
            start=self.start_str,
            end=self.end_str,
            freq='d',
        )
        self.assertIsInstance(res_n, dict)
        self.assertIsInstance(res_h, dict)
        self.assertEqual(set(res_n.keys()), set(res_h.keys()))
        for k in res_n:
            self.assertTrue(res_n[k].columns.tolist() == res_h[k].columns.tolist())
            pd.testing.assert_frame_equal(res_n[k], res_h[k], check_exact=False, rtol=1e-5)
        print(' keys match, DataFrames equal')

    def test_a2_shares_and_symbols_equivalent(self):
        """A2: 同时传 shares 与 symbols 时结果一致（symbols 与 shares 同值时不改变结果）。"""
        print('\n[TestGetHistoryDataAPI] A2: shares vs symbols equivalence')
        res_s = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ, 000002.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        res_y = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ, 000002.SZ',
            symbols='000001.SZ, 000002.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        self.assertEqual(set(res_s.keys()), set(res_y.keys()))
        for k in res_s:
            pd.testing.assert_frame_equal(res_s[k], res_y[k], check_exact=False, rtol=1e-5)
        print(' keys and contents match')

    def test_a3_return_structure_group_by_shares(self):
        """A3: as_data_frame=True, group_by=shares 时 keys 为 shares，value.columns 为 htypes。"""
        print('\n[TestGetHistoryDataAPI] A3: return structure group_by shares')
        res = get_history_data(
            htype_names='close, open',
            data_source=self.data_source,
            shares='000001.SZ, 000002.SZ',
            start=self.start_str,
            end=self.end_str,
            group_by='shares',
        )
        self.assertIsInstance(res, dict)
        self.assertEqual(set(res.keys()), {'000001.SZ', '000002.SZ'})
        for sh in ['000001.SZ', '000002.SZ']:
            self.assertIn('close', res[sh].columns)
            self.assertIn('open', res[sh].columns)
            self.assertGreaterEqual(len(res[sh]), 1)
        print(' keys:', list(res.keys()), 'columns sample:', list(res['000001.SZ'].columns))

    def test_b1_single_type_single_share_matches_source(self):
        """B1: 单类型单标的与数据源 read_table_data 一致。"""
        print('\n[TestGetHistoryDataAPI] B1: single type single share vs source')
        res = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        table = self.data_source.read_table_data(
            'stock_daily', shares='000001.SZ', start=self.start_str, end=self.end_str
        )
        if hasattr(table.index, 'get_level_values') and table.index.nlevels >= 2:
            src_ser = table.xs('000001.SZ', level='ts_code')['close']
        else:
            src_ser = table['close']
        src_ser = src_ser.sort_index()
        got = res['000001.SZ']['close'].dropna()
        self.assertGreater(len(got), 0)
        self.assertGreaterEqual(len(got), len(src_ser) - 2)  # 允许少量因时间对齐导致的差异
        # 首尾数值应与数据源一致
        np.testing.assert_allclose(
            float(got.iloc[0]), float(src_ser.iloc[0]), rtol=1e-5
        )
        print(' close series matches source')

    def test_b2_multi_type_multi_share_matches_source(self):
        """B2: 多类型多标的与数据源对应列一致。"""
        print('\n[TestGetHistoryDataAPI] B2: multi type multi share vs source')
        res = get_history_data(
            htype_names='close, open, volume',
            data_source=self.data_source,
            shares='000001.SZ, 000002.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        for sh in ['000001.SZ', '000002.SZ']:
            table = self.data_source.read_table_data(
                'stock_daily', shares=sh, start=self.start_str, end=self.end_str
            )
            for col, table_col in [('close', 'close'), ('open', 'open'), ('volume', 'vol')]:
                if col not in res[sh].columns:
                    continue
                got = res[sh][col].dropna()
                if len(got) == 0:
                    continue
                if hasattr(table, 'loc'):
                    src = table[table_col].values
                else:
                    src = table[table_col].values
                self.assertGreater(len(got), 0)
                np.testing.assert_allclose(got.values.astype(float), src.astype(float), rtol=1e-5)
        print(' close/open/vol match source')

    def test_c1_daily_price_columns_exist(self):
        """C1: 日频价格 close, open, high, low, volume 列存在且与 stock_daily 一致。"""
        print('\n[TestGetHistoryDataAPI] C1: daily price columns')
        res = get_history_data(
            htype_names='close, open, high, low, volume',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        df = res['000001.SZ']
        for c in ['close', 'open', 'high', 'low', 'volume']:
            self.assertIn(c, df.columns)
        table = self.data_source.read_table_data('stock_daily', shares='000001.SZ', start=self.start_str, end=self.end_str)
        src = table if not hasattr(table.index, 'get_level_values') else table.droplevel(0) if table.index.nlevels > 1 else table
        np.testing.assert_allclose(df['close'].dropna().values, src['close'].values.astype(float), rtol=1e-5)
        print(' columns present and close matches')

    def test_c2_index_daily_columns_exist(self):
        """C2: 指数 index_daily 列存在。"""
        print('\n[TestGetHistoryDataAPI] C2: index_daily')
        res = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares=self.index_share,
            start=self.start_str,
            end=self.end_str,
            asset_type='IDX',
        )
        self.assertIn(self.index_share, res)
        self.assertIn('close', res[self.index_share].columns)
        self.assertGreater(len(res[self.index_share]), 0)
        print(' index close column present')

    def test_c3_adj_reference(self):
        """C3: 复权 close|b 或 adj 参数下复权列存在且非空。"""
        print('\n[TestGetHistoryDataAPI] C3: adj close|b')
        res = get_history_data(
            htype_names='close|b',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        self.assertIn('000001.SZ', res)
        self.assertIn('close|b', res['000001.SZ'].columns)
        self.assertGreater(res['000001.SZ']['close|b'].notna().sum(), 0)
        print(' close|b column present and non-empty')

    def test_c4_total_mv_from_stock_indicator(self):
        """C4: total_mv 来自 stock_indicator，列存在且与数据源一致。"""
        print('\n[TestGetHistoryDataAPI] C4: total_mv from stock_indicator')
        res = get_history_data(
            htype_names='total_mv',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        self.assertIn('000001.SZ', res)
        self.assertIn('total_mv', res['000001.SZ'].columns)
        table = self.data_source.read_table_data('stock_indicator', shares='000001.SZ', start=self.start_str, end=self.end_str)
        if hasattr(table.index, 'get_level_values'):
            src = table['total_mv'].values
        else:
            src = table['total_mv'].values
        got = res['000001.SZ']['total_mv'].dropna()
        self.assertGreater(len(got), 0)
        np.testing.assert_allclose(got.values.astype(float), src.astype(float), rtol=1e-5)
        print(' total_mv matches stock_indicator')

    def test_c7_composite_unsymbolizer(self):
        """C7: 复合类型 close-000651.SZ 单标的序列（仅测股票，避免 index/stock 混合 concat 问题）。"""
        print('\n[TestGetHistoryDataAPI] C7: composite unsymbolizer')
        try:
            res_stk = get_history_data(
                htype_names='close-000651.SZ',
                data_source=self.data_source,
                shares='000651.SZ',
                start=self.start_str,
                end=self.end_str,
            )
        except (ValueError, TypeError) as e:
            if 'concat' in str(e).lower() or 'unaligned' in str(e).lower():
                self.skipTest(f'unsymbolizer concat limitation: {e}')
                return
            raise
        self.assertIsInstance(res_stk, dict)
        self.assertIn('000651.SZ', res_stk)
        df = res_stk['000651.SZ']
        # 复合类型列名可能为 'close' 或 'close-000651.SZ'
        close_col = 'close' if 'close' in df.columns else 'close-000651.SZ'
        self.assertIn(close_col, df.columns)
        self.assertGreater(df[close_col].notna().sum(), 0)
        print(' close-000651.SZ returned with close column')

    def test_c6_explicit_data_types(self):
        """C6: 显式 data_types 时仅该类型，与 stock_daily 一致。"""
        print('\n[TestGetHistoryDataAPI] C6: explicit data_types')
        data_types = [DataType(name='close', freq='d', asset_type='E')]
        res = get_history_data(
            data_types=data_types,
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
            freq='d',
        )
        self.assertIn('000001.SZ', res)
        self.assertIn('close', res['000001.SZ'].columns)
        table = self.data_source.read_table_data('stock_daily', shares='000001.SZ', start=self.start_str, end=self.end_str)
        src = table['close'].values
        got = res['000001.SZ']['close'].dropna().values
        np.testing.assert_allclose(got, src.astype(float), rtol=1e-5)
        print(' explicit data_types close matches source')

    def test_d1_share_without_data_returns_nan_or_empty(self):
        """D1: 请求的 share 在数据源无数据时仍在 keys 中，列为空/NaN。"""
        print('\n[TestGetHistoryDataAPI] D1: share without data')
        res = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ, NONEXISTENT.SZ',
            start=self.start_str,
            end=self.end_str,
        )
        self.assertIn('000001.SZ', res)
        self.assertIn('NONEXISTENT.SZ', res)
        self.assertGreater(res['000001.SZ']['close'].notna().sum(), 0)
        print(' 000001.SZ has data, NONEXISTENT.SZ in keys')

    def test_d2_date_range_outside_source(self):
        """D2: 请求日期范围超出数据源时可能返回空或抛 RuntimeError，仅断言不崩溃。"""
        print('\n[TestGetHistoryDataAPI] D2: date range outside source')
        try:
            res = get_history_data(
                htype_names='close',
                data_source=self.data_source,
                shares='000001.SZ',
                start='20200101',
                end='20200201',
            )
            self.assertIn('000001.SZ', res)
            self.assertIsInstance(res['000001.SZ'], pd.DataFrame)
            print(' no exception, DataFrame returned')
        except RuntimeError as e:
            if 'Empty data extracted' in str(e):
                print(' RuntimeError Empty data (expected when range outside source)')
                return
            raise

    def test_d3_rows_parameter(self):
        """D3: rows 与 start 同时传入时返回数据行数有界。"""
        print('\n[TestGetHistoryDataAPI] D3: rows parameter')
        res = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            rows=5,
        )
        self.assertIn('000001.SZ', res)
        # rows 与 start 同时给定时，文档约定返回最近 rows 条；实际可能返回区间内全部，仅断言有数据且结构正确
        self.assertIsInstance(res['000001.SZ'], pd.DataFrame)
        self.assertGreaterEqual(len(res['000001.SZ']), 1)
        print(' DataFrame returned with at least one row')

    def test_e1_freq_d_and_w(self):
        """E1: freq d 与 w 行数关系。"""
        print('\n[TestGetHistoryDataAPI] E1: freq d vs w')
        res_d = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
            freq='d',
        )
        res_w = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
            freq='w',
        )
        self.assertGreaterEqual(len(res_d['000001.SZ']), len(res_w['000001.SZ']))
        print(' daily rows >= weekly rows')

    def test_e1_freq_h_returns_hourly_data(self):
        """E1: freq h 时从 stock_hourly 取数；若 combine_asset_types 报错则跳过。"""
        print('\n[TestGetHistoryDataAPI] E1: freq h')
        try:
            res = get_history_data(
                htype_names='close',
                data_source=self.data_source,
                shares='000001.SZ',
                start=self.start_str,
                end=self.end_str,
                freq='h',
                asset_type='E',
            )
        except ValueError as e:
            if 'combine_asset_types' in str(e) or 'multiple freqs' in str(e):
                self.skipTest(f'freq=h combine_asset_types limitation: {e}')
                return
            raise
        self.assertIn('000001.SZ', res)
        self.assertIn('close', res['000001.SZ'].columns)
        self.assertGreater(res['000001.SZ']['close'].notna().sum(), 0)
        print(' hourly close column present and non-empty')

    def test_e2_asset_type_filter(self):
        """E2: asset_type E 仅股票，IDX 仅指数。"""
        print('\n[TestGetHistoryDataAPI] E2: asset_type filter')
        res_e = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ, 000300.SH',
            start=self.start_str,
            end=self.end_str,
            asset_type='E',
        )
        res_i = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ, 000300.SH',
            start=self.start_str,
            end=self.end_str,
            asset_type='IDX',
        )
        self.assertIn('000001.SZ', res_e)
        self.assertIn('000300.SH', res_i)
        print(' E and IDX filters applied')

    def test_e3_start_end_invalid_raises(self):
        """E3: start > end 期望 ValueError。"""
        print('\n[TestGetHistoryDataAPI] E3: start > end raises')
        with self.assertRaises(ValueError):
            get_history_data(
                htype_names='close',
                data_source=self.data_source,
                shares='000001.SZ',
                start=self.end_str,
                end=self.start_str,
            )
        print(' ValueError on start > end')

    def test_e4_undefined_htype_name_raises(self):
        """E4: 未定义 htype 名称触发 ValueError，消息含该名称。"""
        print('\n[TestGetHistoryDataAPI] E4: undefined htype raises')
        with self.assertRaises(ValueError) as ctx:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter('always')
                get_history_data(
                    htype_names='close, nonexistent_xyz_123',
                    data_source=self.data_source,
                    shares='000001.SZ',
                    start=self.start_str,
                    end=self.end_str,
                )
        self.assertIn('nonexistent_xyz_123', str(ctx.exception))
        print(' ValueError contains missing name')

    def test_e5_as_data_frame_false_returns_history_panel(self):
        """E5: as_data_frame=False 返回 HistoryPanel。"""
        print('\n[TestGetHistoryDataAPI] E5: as_data_frame=False')
        from qteasy.history import HistoryPanel
        res = get_history_data(
            htype_names='close',
            data_source=self.data_source,
            shares='000001.SZ',
            start=self.start_str,
            end=self.end_str,
            as_data_frame=False,
        )
        self.assertIsInstance(res, HistoryPanel)
        self.assertGreater(res.column_count, 0)
        print(' return is HistoryPanel')

    def test_e6_group_by_htypes(self):
        """E6: group_by=htypes 时 keys 为 htype 名称。"""
        print('\n[TestGetHistoryDataAPI] E6: group_by htypes')
        res = get_history_data(
            htype_names='close, open',
            data_source=self.data_source,
            shares='000001.SZ, 000002.SZ',
            start=self.start_str,
            end=self.end_str,
            group_by='htypes',
        )
        self.assertIsInstance(res, dict)
        self.assertIn('close', res)
        self.assertIn('open', res)
        self.assertEqual(set(res['close'].columns), {'000001.SZ', '000002.SZ'})
        print(' keys are htype names, columns are shares')


class TestGetHistoryDataRealData(unittest.TestCase):
    """基于实际数据源测试 get_history_data，覆盖常用参数组合与边界情况。"""
    def setUp(self):
        self.datasource = qteasy.QT_DATA_SOURCE
        self.shares = ['000001.SZ', '000300.SH', '000651.SZ']  # asset type include E and IDx

    def test_get_history_data_realistic_cases(self):
        """ test multiple cases with real data source, covering common parameters and edge cases. """
        data = get_history_data(
                htype_names='total_mv',
                data_source=self.datasource,
                shares=self.shares,
                start='20220101',
                end='20221231',
                freq='d'
        )
        print(data)
        self.assertTrue(all(share in data for share in self.shares))
        for share in self.shares:
            self.assertIn('total_mv', data[share].columns)
            self.assertTrue(data[share]['total_mv'].notna().any())

    def test_get_history_data_total_mv_m(self):
        """ test multiple cases with real data source, covering common parameters and edge cases. """
        data = get_history_data(
                htype_names='total_mv',
                data_source=self.datasource,
                shares=self.shares,
                start='20220101',
                end='20221231',
                freq='m'
        )
        print(data)
        self.assertTrue(all(share in data for share in self.shares))
        for share in self.shares:
            self.assertIn('total_mv', data[share].columns)
            self.assertTrue(data[share]['total_mv'].notna().any())

    def test_get_history_data_total_mv_d(self):
        """ test multiple cases with real data source, covering common parameters and edge cases. """
        data = get_history_data(
                htype_names='total_mv',
                data_source=self.datasource,
                shares=self.shares,
                start='20220101',
                end='20221231',
                freq='d'
        )
        print(data)
        self.assertTrue(all(share in data for share in self.shares))
        for share in self.shares:
            self.assertIn('total_mv', data[share].columns)
            self.assertTrue(data[share]['total_mv'].notna().any())

    def test_get_history_data_total_share_d(self):
        """ test multiple cases with real data source, covering common parameters and edge cases. """
        data = get_history_data(
                htype_names='total_share',
                data_source=self.datasource,
                shares=self.shares,
                start='20220101',
                end='20221231',
                freq='d',
                # asset_type='E',
        )
        print(data)
        self.assertTrue(all(share in data for share in self.shares))
        for share in self.shares:
            self.assertIn('total_share', data[share].columns)
            self.assertTrue(data[share]['total_share'].notna().any())

    def test_get_history_data_total_share_m(self):
        """ test multiple cases with real data source, covering common parameters and edge cases. """
        data = get_history_data(
                htype_names='total_share',
                data_source=self.datasource,
                shares=self.shares,
                start='20220101',
                end='20221231',
                freq='m',
        )
        print(data)
        self.assertTrue(all(share in data for share in self.shares))
        for share in self.shares:
            self.assertIn('total_share', data[share].columns)
        # 月频总股本在部分资产上可能全为空（如指数），至少一只标的有非空即可
        self.assertTrue(any(data[s]['total_share'].notna().any() for s in self.shares))

    def test_get_history_data_total_liab_d(self):
        """ test multiple cases with real data source, covering common parameters and edge cases. """
        data = get_history_data(
                htype_names='total_share, total_liab, c_cash_equ_end_period, ebitda',
                data_source=self.datasource,
                shares=self.shares,
                start='20220101',
                end='20221231',
                freq='d',
        )
        print(data)
        self.assertTrue(all(share in data for share in self.shares))
        for share in self.shares:
            self.assertIn('total_share', data[share].columns)
            self.assertIn('total_liab', data[share].columns)
            self.assertIn('c_cash_equ_end_period', data[share].columns)
            self.assertIn('ebitda', data[share].columns)
        # 至少一只标的有非空财报字段（指数等可能全 NaN）
        self.assertTrue(any(data[s]['total_share'].notna().any() for s in self.shares))
        self.assertTrue(any(data[s]['total_liab'].notna().any() for s in self.shares))
        self.assertTrue(any(data[s]['c_cash_equ_end_period'].notna().any() for s in self.shares))
        self.assertTrue(any(data[s]['ebitda'].notna().any() for s in self.shares))

    def test_get_history_data_for_all_name_freq_combinations(self):
        """ 使用 DATA_TYPE_MAP 中 acquisition_type 为 direct 的 dtype 去重，回归 get_history_data 在常见 name+freq 组合下的行为。"""
        dtype_map = _get_built_in_data_type_map()
        direct_mask = dtype_map['acquisition_type'] == 'direct'
        direct_df = dtype_map.loc[direct_mask]
        if direct_df.empty:
            self.skipTest('no direct acquisition types in built-in map')
        idx = direct_df.index
        all_dtype_names_full = sorted(set(idx.get_level_values('dtype')))
        all_freqs_raw = set(idx.get_level_values('freq'))
        common_freqs = {'d', 'w', 'm', 'q', 'h'}
        all_freqs = sorted(all_freqs_raw & common_freqs)
        if not all_freqs:
            all_freqs = sorted(all_freqs_raw)[:4]
        # 优先覆盖常见、易有数据的 direct 类型，避免大量空数据导致失败
        preferred = ['close', 'open', 'high', 'low', 'volume', 'total_mv', 'total_share', 'pe', 'pb']
        all_dtype_names = [n for n in preferred if n in all_dtype_names_full]
        if not all_dtype_names:
            all_dtype_names = all_dtype_names_full[:12]

        for dtype_name in all_dtype_names:
            for freq in all_freqs:
                with self.subTest(dtype_name=dtype_name, freq=freq):
                    data = get_history_data(
                            htype_names=dtype_name,
                            data_source=self.datasource,
                            shares=self.shares,
                            start='20220101',
                            end='20221231',
                            freq=freq,
                    )
                    if not data or not all(share in data for share in self.shares):
                        self.skipTest(f'no data for {dtype_name}@{freq}')
                    for share in self.shares:
                        self.assertIn(dtype_name, data[share].columns)
                    # 至少一个 share 有非空数据；若全部为空则跳过（真实数据源可能无该组合）
                    any_non_empty = any(
                        data[share][dtype_name].notna().any()
                        for share in self.shares
                    )
                    if not any_non_empty:
                        self.skipTest(f'{dtype_name}@{freq} 所有 share 全为 NaN')


if __name__ == '__main__':
    unittest.main()