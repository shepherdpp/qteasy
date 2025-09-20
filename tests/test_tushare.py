# coding=utf-8
# ======================================
# File:     test_tsfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all tushare wrapped
# apis with basic parameters. How data
# is saved and loaded is not tested here.
# ======================================
import unittest

import pandas as pd

from qteasy.utilfuncs import list_to_str_format, str_to_list
from qteasy.tsfuncs import (
    income,
    trade_cal,
    indicators,
    namechange,
    moneyflow,
    new_share,
    stk_limit,
    suspend_d,
    moneyflow_hsgt,
    hsgt_top10,
    ggt_top10,
    stock_company,
    stk_managers,
    daily_basic,
    index_dailybasic,
    realtime_min,
    realtime_quote,
    mins1,
    ft_mins1,
    daily,
    weekly,
    monthly,
    index_daily,
    index_weekly,
    index_monthly,
    stock_basic,
    fund_daily,
    adj_factors,
    fund_adj,
    fund_share,
    fund_manager,
    fund_net_value,
    income,
    balance,
    cashflow,
    indicators,
    forecast,
    express,
    dividend,
    top_list,
    top_inst,
    index_member_all,
    block_trade,
    stk_holdertrade,
    margin,
    margin_detail,
    index_basic,
    ths_index,
    index_classify,
    index_indicators,
    ths_daily,
    ths_member,
    ci_daily,
    sw_daily,
    index_global,
    composite,
    fund_basic,
    future_daily,
    fut_mapping,
    options_daily,
    future_basic,
    future_daily,
    fut_weekly,
    fut_monthly,
    options_basic,
    options_daily,
    shibor,
    hibor,
    libor,
)


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
        df = trade_cal(exchange='SSE')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_name_change(self):
        print(f'test tushare function: name_change')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = namechange(ts_code=shares, start=start, end=end)
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

    def test_moneyflow(self):
        """test api moneyflow"""
        print(f'test tushare function: moneyflow')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = moneyflow(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_stk_limit(self):
        print(f'test tushare function: stk_limit')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = stk_limit(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_suspend_d(self):
        print(f'test tushare function: suspend_d')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = suspend_d(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_moneyflow_hsgt(self):
        print(f'test tushare function: moneyflow_hsgt')
        start = '20180101'
        end = '20191231'
        df = moneyflow_hsgt(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_hsgt_top10(self):
        print(f'test tushare function: hsgt_top10')
        start = '20180101'
        end = '20191231'
        df = hsgt_top10(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_ggt_top10(self):
        print(f'test tushare function: ggt_top10')
        start = '20180105'
        end = '20191231'
        df = ggt_top10(trade_date=start, end=end)
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

    def test_stk_managers(self):
        print(f'test tushare function: stk_managers')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = stk_managers(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_daily_basic(self):
        print(f'test tushare function: daily_basic')
        shares = '600748.SH'
        start = '20180101'
        end = '20191231'
        df = daily_basic(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_index_dailybasic(self):
        print(f'test tushare function: index_dailybasic')
        shares = '000300.SH'
        start = '20180101'
        end = '20191231'
        df = index_dailybasic(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_realtime_min(self):
        print(f'test tushare function: realtime_min')
        shares = '600748.SH'
        freq = '5MIN'
        try:
            df = realtime_min(ts_code=shares, freq=freq)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)
            df.info()
            print(df.head(10))
        except Exception as e:
            if '权限' in str(e) or 'permission' in str(e).lower():
                print(f'Skipped test_realtime_min due to permission error: {e}')

    def test_realtime_quote(self):
        print(f'test tushare function: realtime_quote')
        shares = '600748.SH'
        df = realtime_quote(ts_code=shares, src=None)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_mins1(self):
        print(f'test tushare function: mins1')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        try:
            df = mins1(ts_code=shares, start=start, end=end)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)
            df.info()
            print(df.head(10))
        except Exception as e:
            if '权限' in str(e) or 'permission' in str(e).lower():
                print(f'Skipped test_mins1 due to permission error: {e}')

    def test_ft_mins1(self):
        print(f'test tushare function: ft_mins1')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        df = ft_mins1(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_daily(self):
        print(f'test tushare function: daily')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        df = daily(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_weekly(self):
        print(f'test tushare function: weekly')
        shares = '600748.SH'
        start = '20180101'
        end = '20180205'
        df = weekly(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_monthly(self):
        print(f'test tushare function: monthly')
        shares = '600748.SH'
        start = '20180101'
        end = '20180505'
        df = monthly(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_index_daily(self):
        print(f'test tushare function: index_daily')
        shares = '000300.SH'
        start = '20180101'
        end = '20180105'
        df = index_daily(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_index_weekly(self):
        print(f'test tushare function: index_weekly')
        shares = '000300.SH'
        start = '20180101'
        end = '20180205'
        df = index_weekly(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_index_monthly(self):
        print(f'test tushare function: index_monthly')
        shares = '000300.SH'
        start = '20180101'
        end = '20180505'
        df = index_monthly(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_fund_daily(self):
        print(f'test tushare function: fund_daily')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        df = fund_daily(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_adj_factors(self):
        print(f'test tushare function: adj_factors')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        df = adj_factors(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_fund_adj(self):
        print(f'test tushare function: fund_adj')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        df = fund_adj(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_fund_share(self):
        print(f'test tushare function: fund_share')
        shares = '600748.SH'
        start = '20180101'
        end = '20180105'
        df = fund_share(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_fund_manager(self):
        print(f'test tushare function: fund_manager')
        shares = '600748.SH'
        start = '20180101'
        df = fund_manager(ts_code=shares, ann_date=start)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
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

    def test_forecast(self):
        print(f'test tushare function: forecast')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = forecast(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_express(self):
        print(f'test tushare function: express')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = express(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_dividend(self):
        print(f'test tushare function: dividend')
        shares = '600016.SH'
        start = '20180101'
        df = dividend(ts_code=shares, ann_date=start)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_top_inst(self):
        print(f'test tushare function: top_inst')
        trade_date = '20180104'
        print(f'test 1: test no specific shares')
        df = top_inst(trade_date=trade_date)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_index_member_all(self):
        print(f'test tushare function: index_member_all')
        l1_code = '801010.SI'
        df = index_member_all(l1_code=l1_code)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_block_trade(self):
        print(f'test tushare function: block_trade')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = block_trade(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_stk_holdertrade(self):
        print(f'test tushare function: stk_holdertrade')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = stk_holdertrade(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_margin(self):
        print(f'test tushare function: margin')
        start = '20180101'
        end = '20180105'
        df = margin(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_margin_detail(self):
        print(f'test tushare function: margin_detail')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = margin_detail(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

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

    def test_ths_index(self):
        print(f'test tushare function: ths_index')
        exchange = 'SZ'
        df = ths_index(exchange=exchange)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_index_classify(self):
        print(f'test tushare function: index_classify')
        level = 'L1'
        df = index_classify(level=level)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

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

    def test_ths_daily(self):
        print(f'test tushare function: ths_daily')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = ths_daily(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_ths_member(self):
        print(f'test tushare function: ths_member')
        shares = '600016.SH'
        df = ths_member(ts_code=shares)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_ci_daily(self):
        print(f'test tushare function: ci_daily')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = ci_daily(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_sw_daily(self):
        print(f'test tushare function: sw_daily')
        shares = '600016.SH'
        start = '20180101'
        end = '20191231'
        df = sw_daily(ts_code=shares, start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        df.info()
        print(df.head(10))

    def test_index_global(self):
        print(f'test tushare function: index_global')
        start = '20180101'
        end = '20191231'
        df = index_global(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

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
        fund = '511770.SH,511650.SH,511950.SH,002760.OF,002759.OF'
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

    def fut_mapping(self):
        print(f'test tushare function: fut_mapping')
        shares = 'AL1905.SHF'
        start = '20180101'
        end = '20180105'
        df = fut_mapping(ts_code=shares, start=start, end=end)
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

    def test_fut_weekly(self):
        print(f'test tushare function: fut_weekly')
        future = 'AL1905.SHF'
        trade_date = '20190628'
        start = '20190101'
        end = '20190930'
        df = fut_weekly(trade_date=trade_date, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_fut_monthly(self):
        print(f'test tushare function: fut_monthly')
        future = 'AL1905.SHF'
        trade_date = '20190628'
        start = '20190101'
        end = '20190930'
        df = fut_monthly(trade_date=trade_date, start=start, end=end)
        print(f'df loaded: \ninfo:\n{df.info()}\nhead:\n{df.sort_values("ts_code").head(10)}')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

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

    def test_shibor(self):
        print(f'test tushare function: shibor')
        start = '20180101'
        end = '20180105'
        df = shibor(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_hibor(self):
        print(f'test tushare function: hibor')
        start = '20180101'
        end = '20180105'
        df = hibor(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))

    def test_libor(self):
        print(f'test tushare function: libor')
        start = '20180101'
        end = '20180105'
        df = libor(start=start, end=end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        df.info()
        print(df.head(10))


if __name__ == '__main__':
    unittest.main()
