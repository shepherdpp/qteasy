# coding=utf-8
# ======================================
# File:     test_tsfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all tushare wrapper
#   functions.
# ======================================
import unittest

import pandas as pd

from qteasy.utilfuncs import list_to_str_format, regulate_date_format, sec_to_duration, str_to_list
from qteasy.tsfuncs import income, indicators, name_change
from qteasy.tsfuncs import stock_basic, trade_calendar, new_share
from qteasy.tsfuncs import balance, cashflow, top_list, index_indicators, composite
from qteasy.tsfuncs import future_basic, future_daily, options_basic, options_daily
from qteasy.tsfuncs import fund_basic, fund_net_value, index_basic, stock_company


class TestTushare(unittest.TestCase):
    """测试所有Tushare函数的运行正确"""

    def setUp(self):
        # 减少重试，缩短测试时间
        import qteasy as qt
        qt.tsfuncs.data_download_retry_cnt = 3
        qt.tsfuncs.data_download_retry_wait = 0.1
        qt.tsfuncs.data_download_retry_backoff = 1.0

    def test_stock_basic(self):
        print(f'test tushare function: stock_basic')
        df = stock_basic()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_trade_calendar(self):
        print(f'test tushare function: trade_calendar')
        df = trade_calendar(exchange='SSE')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_name_change(self):
        print(f'test tushare function: name_change')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = name_change(ts_code=shares)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

        df = name_change(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_new_share(self):
        print(f'test tushare function: new_share')
        start = '20180101'
        end = '20191231'
        df = new_share()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

        df = new_share(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_stock_company(self):
        print(f'test tushare function: stock_company')
        shares = '600748.SH'
        df = stock_company(ts_code=shares)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_income(self):
        print(f'test tushare function: income')
        shares = '600748.SH'
        rpt_date = '20181231'
        start = '20180101'
        end = '20191231'
        df = income(ts_code=shares,
                    rpt_date=rpt_date,
                    start=start,
                    end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        df = income(ts_code=shares,
                    start='20170101',
                    end='20220101')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'Test income: extracted single share income: \n{df}')

        # test another shares data extraction:
        shares = '000010.SZ'
        fields = 'ts_code,ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue, ' \
                 'int_income, prem_earned, comm_income, n_commis_income, n_oth_income, n_oth_b_income'
        df = income(ts_code=shares,
                    start=start,
                    end=end,
                    fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \n{df}')
        self.assertFalse(df.empty)

        shares = '000010.SZ'
        fields = 'ts_code,ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue, ' \
                 'int_income, prem_earned, comm_income, n_commis_income, n_oth_income, n_oth_b_income'
        df = income(ts_code=shares,
                    start=start,
                    end='20210307',
                    fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income with end date = today: \n{df}')
        self.assertFalse(df.empty)

        # test long idx_range data extraction:
        shares = '000039.SZ'
        start = '20080101'
        end = '20201231'
        fields = 'ts_code,ann_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue, ' \
                 'int_income, prem_earned, comm_income, n_commis_income, n_oth_income, n_oth_b_income, ' \
                 'prem_income, out_prem, une_prem_reser, reins_income, n_sec_tb_income, n_sec_uw_income, ' \
                 'n_asset_mg_income'
        df = income(ts_code=shares,
                    start=start,
                    end=end,
                    fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \ninfo:\n{df.info()}')
        self.assertFalse(df.empty)

    def test_balance(self):
        print(f'test tushare function: balance')
        shares = '000039.SZ'
        start = '20080101'
        end = '20201231'
        fields = 'special_rese, money_cap,trad_asset,notes_receiv,accounts_receiv,oth_receiv,' \
                 'prepayment,div_receiv,int_receiv,inventories,amor_exp, nca_within_1y,sett_rsrv' \
                 ',loanto_oth_bank_fi,premium_receiv,reinsur_receiv,reinsur_res_receiv'
        df = balance(ts_code=shares,
                     start=start,
                     end=end,
                     fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \ninfo:\n{df.info()}\nhead:\n{df.head()}')
        self.assertFalse(df.empty)

    def test_cashflow(self):
        print(f'test tushare function: cashflow')
        fields = ['net_profit',
                  'finan_exp',
                  'c_fr_sale_sg',
                  'recp_tax_rends',
                  'n_depos_incr_fi',
                  'n_incr_loans_cb',
                  'n_inc_borr_oth_fi',
                  'prem_fr_orig_contr',
                  'n_incr_insured_dep',
                  'n_reinsur_prem',
                  'n_incr_disp_tfa']
        fields = list_to_str_format(fields)
        shares = '000039.SZ'
        start = '20080101'
        end = '20201231'
        df = cashflow(ts_code=shares,
                      start=start,
                      end=end,
                      fields=fields)
        self.assertIsInstance(df, pd.DataFrame)
        print(f'Test income: extracted multiple share income: \ninfo:\n{df.info()}\nhead:\n{df.head()}')
        self.assertFalse(df.empty)

    def test_indicators(self):
        print(f'test tushare function: indicators')
        shares = '600016.SH'
        rpt_date = '20180101'
        start = '20180101'
        end = '20191231'
        df = indicators(ts_code=shares,
                        rpt_date=rpt_date,
                        start=start,
                        end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        df = indicators(ts_code=shares,
                        start='20150101',
                        end='20220101')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'\nTest indicators 2: extracted indicator: \n{df}')

    def test_top_list(self):
        shares = '000732.SZ'
        trade_date = '20180104'
        print(f'test tushare function: top_list')
        print(f'test 1: test no specific shares')
        df = top_list(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: test one specific share')
        df = top_list(trade_date=trade_date, shares=shares)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: test multiple specific share')  # tushare does not allow multiple share codes in top_list
        shares = '000672.SZ, 000732.SZ'
        df = top_list(trade_date=trade_date, shares=shares)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

    def test_index_basic(self):
        """test function index_basic"""
        print(f'test tushare function: index_basic\n'
              f'=======================================')
        print(f'test 1: basic usage of the function')
        df = index_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: get all information of index with market')
        df = index_basic(market='SSE')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3: thrown error on bad parameters')
        df = index_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_index_indicators(self):
        print(f'test tushare function: index_indicators\n'
              f'=======================================')
        index = '000300.SH'
        trade_date = '20180104'
        start = '20180101'
        end = '20180115'

        print(f'test 1: test single index single date\n'
              f'=====================================')
        df = index_indicators(trade_date=trade_date, ts_code=index)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: test single index in date idx_range\n'
              f'=======================================')
        df = index_indicators(ts_code=index, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3: test multiple specific indices in single date\n'
              f'=====================================================')
        index = '000300.SH, 000001.SH'  # tushare does not support multiple indices in index_indicators
        df = index_indicators(trade_date=trade_date, ts_code=index)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        print(f'test 4: test all indices in single date\n'
              f'=======================================')
        df = index_indicators(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_composite(self):
        print(f'test tushare function: composit\n'
              f'===============================')
        index = '399300.SZ'
        start = '20190101'
        end = '20190930'

        print(f'test 1: find composit of one specific index in months\n'
              f'===============================')
        df = composite(index=index, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

        index = '399001.SZ'
        df = composite(index=index, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

        print(f'test 2: find composit of one specific index in exact trade date\n'
              f'===============================')
        index = '000300.SH'
        trade_date = '20200430'
        df = composite(index=index, trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("weight", ascending=False).head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.trade_date.nunique()} unique trade dates\n'
              f'they are: \n{list(df.trade_date.unique())}')

        trade_date = '20201008'
        df = composite(index=index, trade_date=trade_date)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

        print(f'test 3: find composit of all indices in one specific trade date\n'
              f'===============================')
        index = '000300.SH'
        trade_date = '20201009'
        df = composite(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("index_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.index_code.nunique()} unique index_codes\n'
              f'they are: \n{list(df.index_code.unique())}')

    def test_fund_basic(self):
        """ 测试函数fund_basic()

        :return:
        """
        print(f'test tushare function fund_basic\n'
              f'===============================')

        print(f'test 1: find basic information for all funds')
        df = fund_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2: find basic information for all funds that are traded inside market')
        df = fund_basic(market='E')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test3: find basic info for all funds that are being issued')
        df = fund_basic(status='L')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test4, test error thrown out due to bad parameter')
        # noinspection PyTypeChecker
        df = fund_basic(market=3)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertTrue(df.empty)

    def test_fund_net_value(self):
        print(f'test tushare function: fund_net_value\n'
              f'===============================')
        fund = '399300.SZ'
        trade_date = '20180909'

        print(f'test 1: find all funds in one specific date, exchanging in market\n'
              f'===============================')
        df = fund_net_value(nav_date=trade_date, market='E')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

        print(f'test 1: find all funds in one specific date, exchange outside market\n'
              f'===============================')
        df = fund_net_value(nav_date=trade_date, market='O')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

        print(f'test 2: find value of one fund in history\n'
              f'===============================')
        fund = '512960.SH'
        df = fund_net_value(ts_code=fund)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ann_date.nunique()} unique trade dates\n'
              f'first 10 items of them are: \n{list(df.ann_date.unique()[:9])}')

        print(f'test 3: find value of multiple funds in history\n'
              f'===============================')
        fund = '511770.SH, 511650.SH, 511950.SH, 002760.OF, 002759.OF'
        trade_date = '20201009'
        df = fund_net_value(ts_code=fund, nav_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertEqual(set(df.ts_code.unique()), set(str_to_list(fund)))
        print(f'found in df records in {df.index.nunique()} unique trade dates\n'
              f'they are: \n{list(df.index.unique())}')

    def test_future_basic(self):
        print(f'test tushare function: future_basic')
        print(f'test 1, load basic future information with default input\n'
              f'========================================================')
        df = future_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

        print(f'test 2, load basic future information in SHFE type == 1\n'
              f'========================================================')
        exchange = 'SHFE'
        df = future_basic(exchange=exchange, future_type='1')
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

    def test_options_basic(self):
        print(f'test tushare function: options_basic')
        print(f'test 1, load basic options information with default input\n'
              f'========================================================')
        df = options_basic()
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print(f'found in df records in {df.ts_code.nunique()} unique trade dates\n'
              f'they are: \n{list(df.ts_code.unique())}')

    def test_future_daily(self):
        print(f'test tushare function: future_daily')
        print(f'test 1, load basic future information at one specific date\n'
              f'==========================================================')
        future = 'AL1905.SHF'
        trade_date = '20190628'
        start = '20190101'
        end = '20190930'
        df = future_daily(trade_date=trade_date, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2, load basic future information for one ts_code\n'
              f'==========================================================')
        df = future_daily(future=future, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3, error raising when both future and trade_date are None\n'
              f'==============================================================')
        self.assertRaises(ValueError, future_daily, start=start, end=end)

    def test_options_daily(self):
        print(f'test tushare function: options_daily')
        print(f'test 1, load option information at one specific date\n'
              f'==========================================================')
        option = '10001677.SH'
        trade_date = '20190628'
        start = '20190101'
        end = '20190930'
        df = options_daily(trade_date=trade_date, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 2, load basic future information for one ts_code\n'
              f'==========================================================')
        df = options_daily(option=option, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

        print(f'test 3, error raising when both future and trade_date are None\n'
              f'==============================================================')
        self.assertRaises(ValueError, options_daily, start=start, end=end)


if __name__ == '__main__':
    unittest.main()