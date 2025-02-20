# coding=utf-8
# ======================================
# File:     test_datatypes.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-25
# Desc:
#   Unittest for all built-in data
# types.
# ======================================

import unittest

import pandas as pd

from qteasy.database import DataSource
from qteasy.utilfuncs import (
    progress_bar,
    str_to_list,
    list_to_str_format,
)

from qteasy.datatypes import (
    DataType,
    get_history_data_from_source,
    get_reference_data_from_source,
    get_tables_by_dtypes, infer_data_types,
)

ALL_TYPES_TO_TEST_WITH_FULL_ID = [
    ('is_trade_day|SSE', 'd', 'None'),
    ('is_trade_day|SZSE', 'd', 'None'),
    ('is_trade_day|SSE', 'd', 'None'),
    ('pre_trade_day|SSE', 'd', 'None'),
    ('pre_trade_day|CFFEX', 'd', 'None'),
    ('stock_symbol', 'None', 'E'),
    ('stock_name', 'None', 'E'),
    ('area', 'None', 'E'),
    ('industry', 'None', 'E'),
    ('fullname', 'None', 'E'),
    ('enname', 'None', 'E'),
    ('cnspell', 'None', 'E'),
    ('market', 'None', 'E'),
    ('exchange', 'None', 'E'),
    ('curr_type', 'None', 'E'),
    ('list_status', 'None', 'E'),
    ('list_date', 'None', 'E'),
    ('delist_date', 'None', 'E'),
    ('is_hs', 'None', 'E'),
    ('wt_idx|000001.SH', 'd', 'E'),
    ('wt_idx|000002.SH', 'd', 'E'),
    ('wt_idx|000003.SH', 'd', 'E'),
    ('wt_idx|000004.SH', 'd', 'E'),
    ('wt_idx|000005.SH', 'd', 'E'),
    ('wt_idx|000006.SH', 'd', 'E'),
    ('wt_idx|000007.SH', 'd', 'E'),
    ('wt_idx|000016.SH', 'd', 'E'),
    ('wt_idx|000010.SH', 'd', 'E'),
    ('wt_idx|000009.SH', 'd', 'E'),
    ('wt_idx|000043.SH', 'd', 'E'),
    ('wt_idx|000044.SH', 'd', 'E'),
    ('wt_idx|000045.SH', 'd', 'E'),
    ('wt_idx|000300.SH', 'd', 'E'),
    ('wt_idx|399001.SZ', 'd', 'E'),
    ('wt_idx|399006.SZ', 'd', 'E'),
    ('wt_idx|399004.SZ', 'd', 'E'),
    ('wt_idx|399009.SZ', 'd', 'E'),
    ('wt_idx|399007.SZ', 'd', 'E'),
    ('wt_idx|399010.SZ', 'd', 'E'),
    ('wt_idx|399011.SZ', 'd', 'E'),
    ('ths_category', 'None', 'E'),
    # ('sw_category','None','E'),
    ('market', 'None', 'IDX'),
    ('publisher', 'None', 'IDX'),
    ('index_type', 'None', 'IDX'),
    ('category', 'None', 'IDX'),
    ('base_date', 'None', 'IDX'),
    ('base_point', 'None', 'IDX'),
    ('list_date', 'None', 'IDX'),
    ('weight_rule', 'None', 'IDX'),
    ('desc', 'None', 'IDX'),
    ('exp_date', 'None', 'IDX'),
    ('sw_industry_name', 'None', 'IDX'),
    ('sw_parent_code', 'None', 'IDX'),
    ('sw_level', 'None', 'IDX'),
    ('sw_industry_code', 'None', 'IDX'),
    ('sw_published', 'None', 'IDX'),
    ('sw_source', 'None', 'IDX'),
    ('sw_level|L1', 'None', 'IDX'),
    ('sw_level|L2', 'None', 'IDX'),
    ('sw_level|L3', 'None', 'IDX'),
    ('sw|SW2014', 'None', 'IDX'),
    ('sw|SW2021', 'None', 'IDX'),
    ('ths_industry_name', 'None', 'IDX'),
    ('ths_industry_count', 'None', 'IDX'),
    ('ths_industry_exchange', 'None', 'IDX'),
    ('ths_industry_date', 'None', 'IDX'),
    ('fund_name', 'None', 'FD'),
    ('management', 'None', 'FD'),
    ('custodian', 'None', 'FD'),
    ('fund_type', 'None', 'FD'),
    ('found_date', 'None', 'FD'),
    ('due_date', 'None', 'FD'),
    ('list_date', 'None', 'FD'),
    ('issue_date', 'None', 'FD'),
    ('delist_date', 'None', 'FD'),
    ('issue_amount', 'None', 'FD'),
    ('m_fee', 'None', 'FD'),
    ('c_fee', 'None', 'FD'),
    ('duration_year', 'None', 'FD'),
    ('p_value', 'None', 'FD'),
    ('min_amount', 'None', 'FD'),
    ('exp_return', 'None', 'FD'),
    ('benchmark', 'None', 'FD'),
    ('status', 'None', 'FD'),
    ('invest_type', 'None', 'FD'),
    ('type', 'None', 'FD'),
    ('trustee', 'None', 'FD'),
    ('purc_startdate', 'None', 'FD'),
    ('redm_startdate', 'None', 'FD'),
    ('market', 'None', 'FD'),
    ('symbol', 'None', 'FT'),
    ('exchange', 'None', 'FT'),
    ('name', 'None', 'FT'),
    ('fut_code', 'None', 'FT'),
    ('multiplier', 'None', 'FT'),
    ('trade_unit', 'None', 'FT'),
    ('per_unit', 'None', 'FT'),
    ('quote_unit', 'None', 'FT'),
    ('quote_unit_desc', 'None', 'FT'),
    ('d_mode_desc', 'None', 'FT'),
    ('list_date', 'None', 'FT'),
    ('delist_date', 'None', 'FT'),
    ('d_month', 'None', 'FT'),
    ('last_ddate', 'None', 'FT'),
    ('trade_time_desc', 'None', 'FT'),
    ('exchange', 'None', 'OPT'),
    ('name', 'None', 'OPT'),
    ('per_unit', 'None', 'OPT'),
    ('opt_code', 'None', 'OPT'),
    ('opt_type', 'None', 'OPT'),
    ('call_put', 'None', 'OPT'),
    ('exercise_type', 'None', 'OPT'),
    ('exercise_price', 'None', 'OPT'),
    ('s_month', 'None', 'OPT'),
    ('maturity_date', 'None', 'OPT'),
    ('list_price', 'None', 'OPT'),
    ('list_date', 'None', 'OPT'),
    ('delist_date', 'None', 'OPT'),
    ('last_edate', 'None', 'OPT'),
    ('last_ddate', 'None', 'OPT'),
    ('quote_unit', 'None', 'OPT'),
    ('min_price_chg', 'None', 'OPT'),
    ('chairman', 'd', 'E'),
    ('manager', 'd', 'E'),
    ('secretary', 'd', 'E'),
    ('reg_capital', 'd', 'E'),
    ('setup_date', 'd', 'E'),
    ('province', 'd', 'E'),
    ('city', 'd', 'E'),
    ('introduction', 'd', 'E'),
    ('website', 'd', 'E'),
    ('email', 'd', 'E'),
    ('office', 'd', 'E'),
    ('employees', 'd', 'E'),
    ('main_business', 'd', 'E'),
    ('business_scope', 'd', 'E'),
    ('managers_name', 'd', 'E'),
    ('managers_gender', 'd', 'E'),
    ('managers_lev', 'd', 'E'),
    ('manager_title', 'd', 'E'),
    ('managers_edu', 'd', 'E'),
    ('managers_national', 'd', 'E'),
    ('managers_birthday', 'd', 'E'),
    ('managers_resume', 'd', 'E'),
    # ('manager_salary_name','d','E'),
    # ('manager_salary_title','d','E'),
    # ('reward','d','E'),
    # ('hold_vol','d','E'),
    ('ipo_date', 'd', 'E'),
    ('issue_date', 'd', 'E'),
    ('IPO_amount', 'd', 'E'),
    ('market_amount', 'd', 'E'),
    ('initial_price', 'd', 'E'),
    ('initial_pe', 'd', 'E'),
    ('limit_amount', 'd', 'E'),
    ('funds', 'd', 'E'),
    ('ballot', 'd', 'E'),
    ('hk_top10_close', 'd', 'E'),
    ('hk_top10_p_change', 'd', 'E'),
    ('hk_top10_rank', 'd', 'E'),
    ('hk_top10_amount', 'd', 'E'),
    ('hk_top10_net_amount', 'd', 'E'),
    ('hk_top10_sh_amount', 'd', 'E'),
    ('hk_top10_sh_net_amount', 'd', 'E'),
    ('hk_top10_sh_buy', 'd', 'E'),
    ('hk_top10_sh_sell', 'd', 'E'),
    ('hk_top10_sz_amount', 'd', 'E'),
    ('hk_top10_sz_net_amount', 'd', 'E'),
    ('hk_top10_sh_buy', 'd', 'E'),
    ('hk_top10_sh_sell', 'd', 'E'),
    ('open|b', 'd', 'E'),
    ('high|b', 'd', 'E'),
    ('low|b', 'd', 'E'),
    ('close|b', 'd', 'E'),
    ('open|f', 'd', 'E'),
    ('high|f', 'd', 'E'),
    ('low|f', 'd', 'E'),
    ('close|f', 'd', 'E'),
    ('open-000651.SZ', 'd', 'E'),  # 测试历史数据+qt_code转参考数据
    ('open', 'd', 'E'),
    ('high', 'd', 'E'),
    ('low', 'd', 'E'),
    ('close', 'd', 'E'),
    ('volume', 'd', 'E'),
    ('amount', 'd', 'E'),
    ('open|b', 'w', 'E'),
    ('high|b', 'w', 'E'),
    ('low|b', 'w', 'E'),
    ('close|b', 'w', 'E'),
    ('open|f', 'w', 'E'),
    ('high|f', 'w', 'E'),
    ('low|f', 'w', 'E'),
    ('close|f', 'w', 'E'),
    ('open', 'w', 'E'),
    ('high', 'w', 'E'),
    ('low', 'w', 'E'),
    ('close', 'w', 'E'),
    ('volume', 'w', 'E'),
    ('amount', 'w', 'E'),
    ('open|b', 'm', 'E'),
    ('high|b', 'm', 'E'),
    ('low|b', 'm', 'E'),
    ('close|b', 'm', 'E'),
    ('open|f', 'm', 'E'),
    ('high|f', 'm', 'E'),
    ('low|f', 'm', 'E'),
    ('close|f', 'm', 'E'),
    ('open', 'm', 'E'),
    ('high', 'm', 'E'),
    ('low', 'm', 'E'),
    ('close', 'm', 'E'),
    ('volume', 'm', 'E'),
    ('amount', 'm', 'E'),
    ('open|b', '1min', 'E'),
    ('high|b', '1min', 'E'),
    ('low|b', '1min', 'E'),
    ('close|b', '1min', 'E'),
    ('open|f', '1min', 'E'),
    ('high|f', '1min', 'E'),
    ('low|f', '1min', 'E'),
    ('close|f', '1min', 'E'),
    ('open', '1min', 'E'),
    ('high', '1min', 'E'),
    ('low', '1min', 'E'),
    ('close', '1min', 'E'),
    ('volume', '1min', 'E'),
    ('amount', '1min', 'E'),
    ('open|b', '5min', 'E'),
    ('high|b', '5min', 'E'),
    ('low|b', '5min', 'E'),
    ('close|b', '5min', 'E'),
    ('open|f', '5min', 'E'),
    ('high|f', '5min', 'E'),
    ('low|f', '5min', 'E'),
    ('close|f', '5min', 'E'),
    ('open', '5min', 'E'),
    ('high', '5min', 'E'),
    ('low', '5min', 'E'),
    ('close', '5min', 'E'),
    ('volume', '5min', 'E'),
    ('amount', '5min', 'E'),
    ('open|b', '15min', 'E'),
    ('high|b', '15min', 'E'),
    ('low|b', '15min', 'E'),
    ('close|b', '15min', 'E'),
    ('open|f', '15min', 'E'),
    ('high|f', '15min', 'E'),
    ('low|f', '15min', 'E'),
    ('close|f', '15min', 'E'),
    ('open', '15min', 'E'),
    ('high', '15min', 'E'),
    ('low', '15min', 'E'),
    ('close', '15min', 'E'),
    ('volume', '15min', 'E'),
    ('amount', '15min', 'E'),
    ('open|b', '30min', 'E'),
    ('high|b', '30min', 'E'),
    ('low|b', '30min', 'E'),
    ('close|b', '30min', 'E'),
    ('open|f', '30min', 'E'),
    ('high|f', '30min', 'E'),
    ('low|f', '30min', 'E'),
    ('close|f', '30min', 'E'),
    ('open', '30min', 'E'),
    ('high', '30min', 'E'),
    ('low', '30min', 'E'),
    ('close', '30min', 'E'),
    ('volume', '30min', 'E'),
    ('amount', '30min', 'E'),
    ('open|b', 'h', 'E'),
    ('high|b', 'h', 'E'),
    ('low|b', 'h', 'E'),
    ('close|b', 'h', 'E'),
    ('open|f', 'h', 'E'),
    ('high|f', 'h', 'E'),
    ('low|f', 'h', 'E'),
    ('close|f', 'h', 'E'),
    ('open', 'h', 'E'),
    ('high', 'h', 'E'),
    ('low', 'h', 'E'),
    ('close', 'h', 'E'),
    ('volume', 'h', 'E'),
    ('amount', 'h', 'E'),
    ('ths_open', 'd', 'IDX'),
    ('ths_high', 'd', 'IDX'),
    ('ths_low', 'd', 'IDX'),
    ('ths_close', 'd', 'IDX'),
    ('ths_change', 'd', 'IDX'),
    ('ths_avg_price', 'd', 'IDX'),
    ('ths_pct_change', 'd', 'IDX'),
    ('ths_vol', 'd', 'IDX'),
    ('ths_turnover', 'd', 'IDX'),
    ('ths_float_mv', 'd', 'IDX'),
    ('ths_total_mv', 'd', 'IDX'),
    ('ci_open', 'd', 'IDX'),
    ('ci_high', 'd', 'IDX'),
    ('ci_low', 'd', 'IDX'),
    ('ci_close', 'd', 'IDX'),
    ('ci_change', 'd', 'IDX'),
    ('ci_pct_change', 'd', 'IDX'),
    ('ci_vol', 'd', 'IDX'),
    ('ci_amount', 'd', 'IDX'),
    ('ci_pre_close', 'd', 'IDX'),
    ('sw_open', 'd', 'IDX'),
    ('sw_high', 'd', 'IDX'),
    ('sw_low', 'd', 'IDX'),
    ('sw_close', 'd', 'IDX'),
    ('sw_change', 'd', 'IDX'),
    ('sw_pct_change', 'd', 'IDX'),
    ('sw_vol', 'd', 'IDX'),
    ('sw_amount', 'd', 'IDX'),
    ('sw_pe', 'd', 'IDX'),
    ('sw_pb', 'd', 'IDX'),
    ('sw_float_mv', 'd', 'IDX'),
    ('sw_total_mv', 'd', 'IDX'),
    ('g_index_open', 'd', 'IDX'),
    ('g_index_high', 'd', 'IDX'),
    ('g_index_low', 'd', 'IDX'),
    ('g_index_close', 'd', 'IDX'),
    ('g_index_change', 'd', 'IDX'),
    ('g_index_pct_change', 'd', 'IDX'),
    ('g_index_vol', 'd', 'IDX'),
    ('g_index_amount', 'd', 'IDX'),
    ('g_index_pre_close', 'd', 'IDX'),
    ('g_index_swing', 'd', 'IDX'),
    ('open', 'd', 'IDX'),
    ('high', 'd', 'IDX'),
    ('low', 'd', 'IDX'),
    ('close', 'd', 'IDX'),
    ('close-000300.SH', 'd', 'IDX'),  # 测试历史数据转参考数据
    ('volume', 'd', 'IDX'),
    ('amount', 'd', 'IDX'),
    ('open', 'w', 'IDX'),
    ('high', 'w', 'IDX'),
    ('low', 'w', 'IDX'),
    ('close', 'w', 'IDX'),
    ('volume', 'w', 'IDX'),
    ('amount', 'w', 'IDX'),
    ('open', 'm', 'IDX'),
    ('high', 'm', 'IDX'),
    ('low', 'm', 'IDX'),
    ('close', 'm', 'IDX'),
    ('volume', 'm', 'IDX'),
    ('amount', 'm', 'IDX'),
    ('open', '1min', 'IDX'),
    ('high', '1min', 'IDX'),
    ('low', '1min', 'IDX'),
    ('close', '1min', 'IDX'),
    ('volume', '1min', 'IDX'),
    ('amount', '1min', 'IDX'),
    ('open', '5min', 'IDX'),
    ('high', '5min', 'IDX'),
    ('low', '5min', 'IDX'),
    ('close', '5min', 'IDX'),
    ('close-000300.SH', '5min', 'IDX'),  # 测试历史数据转参考数据
    ('volume', '5min', 'IDX'),
    ('amount', '5min', 'IDX'),
    ('open', '15min', 'IDX'),
    ('high', '15min', 'IDX'),
    ('low', '15min', 'IDX'),
    ('close', '15min', 'IDX'),
    ('volume', '15min', 'IDX'),
    ('amount', '15min', 'IDX'),
    ('open', '30min', 'IDX'),
    ('high', '30min', 'IDX'),
    ('low', '30min', 'IDX'),
    ('close', '30min', 'IDX'),
    ('volume', '30min', 'IDX'),
    ('amount', '30min', 'IDX'),
    ('open', 'h', 'IDX'),
    ('high', 'h', 'IDX'),
    ('low', 'h', 'IDX'),
    ('close', 'h', 'IDX'),
    ('volume', 'h', 'IDX'),
    ('amount', 'h', 'IDX'),
    ('open', 'd', 'FT'),
    ('high', 'd', 'FT'),
    ('low', 'd', 'FT'),
    ('close', 'd', 'FT'),
    ('volume', 'd', 'FT'),
    ('amount', 'd', 'FT'),
    ('settle', 'd', 'FT'),
    ('close_chg', 'd', 'FT'),
    ('settle_chg', 'd', 'FT'),
    ('oi', 'd', 'FT'),
    ('oi_chg', 'd', 'FT'),
    ('delf_settle', 'd', 'FT'),
    ('open', 'w', 'FT'),
    ('high', 'w', 'FT'),
    ('low', 'w', 'FT'),
    ('close', 'w', 'FT'),
    ('volume', 'w', 'FT'),
    ('amount', 'w', 'FT'),
    ('settle', 'w', 'FT'),
    ('close_chg', 'w', 'FT'),
    ('settle_chg', 'w', 'FT'),
    ('oi', 'w', 'FT'),
    ('oi_chg', 'w', 'FT'),
    ('delf_settle', 'w', 'FT'),
    ('open', 'm', 'FT'),
    ('high', 'm', 'FT'),
    ('low', 'm', 'FT'),
    ('close', 'm', 'FT'),
    ('volume', 'm', 'FT'),
    ('amount', 'm', 'FT'),
    ('settle', 'm', 'FT'),
    ('close_chg', 'm', 'FT'),
    ('settle_chg', 'm', 'FT'),
    ('oi', 'm', 'FT'),
    ('oi_chg', 'm', 'FT'),
    ('delf_settle', 'm', 'FT'),
    ('open', '1min', 'FT'),
    ('high', '1min', 'FT'),
    ('low', '1min', 'FT'),
    ('close', '1min', 'FT'),
    ('volume', '1min', 'FT'),
    ('amount', '1min', 'FT'),
    ('open', '5min', 'FT'),
    ('high', '5min', 'FT'),
    ('low', '5min', 'FT'),
    ('close', '5min', 'FT'),
    ('volume', '5min', 'FT'),
    ('amount', '5min', 'FT'),
    ('open', '15min', 'FT'),
    ('high', '15min', 'FT'),
    ('low', '15min', 'FT'),
    ('close', '15min', 'FT'),
    ('volume', '15min', 'FT'),
    ('amount', '15min', 'FT'),
    ('open', '30min', 'FT'),
    ('high', '30min', 'FT'),
    ('low', '30min', 'FT'),
    ('close', '30min', 'FT'),
    ('volume', '30min', 'FT'),
    ('amount', '30min', 'FT'),
    ('open', 'h', 'FT'),
    ('high', 'h', 'FT'),
    ('low', 'h', 'FT'),
    ('close', 'h', 'FT'),
    ('volume', 'h', 'FT'),
    ('amount', 'h', 'FT'),
    ('open', 'd', 'OPT'),
    ('high', 'd', 'OPT'),
    ('low', 'd', 'OPT'),
    ('close', 'd', 'OPT'),
    ('volume', 'd', 'OPT'),
    ('amount', 'd', 'OPT'),
    ('open', '1min', 'OPT'),
    ('high', '1min', 'OPT'),
    ('low', '1min', 'OPT'),
    ('close', '1min', 'OPT'),
    ('volume', '1min', 'OPT'),
    ('amount', '1min', 'OPT'),
    ('open', '5min', 'OPT'),
    ('high', '5min', 'OPT'),
    ('low', '5min', 'OPT'),
    ('close', '5min', 'OPT'),
    ('volume', '5min', 'OPT'),
    ('amount', '5min', 'OPT'),
    ('open', '15min', 'OPT'),
    ('high', '15min', 'OPT'),
    ('low', '15min', 'OPT'),
    ('close', '15min', 'OPT'),
    ('volume', '15min', 'OPT'),
    ('amount', '15min', 'OPT'),
    ('open', '30min', 'OPT'),
    ('high', '30min', 'OPT'),
    ('low', '30min', 'OPT'),
    ('close', '30min', 'OPT'),
    ('volume', '30min', 'OPT'),
    ('amount', '30min', 'OPT'),
    ('open', 'h', 'OPT'),
    ('high', 'h', 'OPT'),
    ('low', 'h', 'OPT'),
    ('close', 'h', 'OPT'),
    ('volume', 'h', 'OPT'),
    ('amount', 'h', 'OPT'),
    ('open|b', 'd', 'FD'),
    ('high|b', 'd', 'FD'),
    ('low|b', 'd', 'FD'),
    ('close|b', 'd', 'FD'),
    ('open|f', 'd', 'FD'),
    ('high|f', 'd', 'FD'),
    ('low|f', 'd', 'FD'),
    ('close|f', 'd', 'FD'),
    ('open', 'd', 'FD'),
    ('high', 'd', 'FD'),
    ('low', 'd', 'FD'),
    ('close', 'd', 'FD'),
    ('volume', 'd', 'FD'),
    ('amount', 'd', 'FD'),
    ('open|b', '1min', 'FD'),
    ('high|b', '1min', 'FD'),
    ('low|b', '1min', 'FD'),
    ('close|b', '1min', 'FD'),
    ('open|f', '1min', 'FD'),
    ('high|f', '1min', 'FD'),
    ('low|f', '1min', 'FD'),
    ('close|f', '1min', 'FD'),
    ('open', '1min', 'FD'),
    ('high', '1min', 'FD'),
    ('low', '1min', 'FD'),
    ('close', '1min', 'FD'),
    ('volume', '1min', 'FD'),
    ('amount', '1min', 'FD'),
    ('open|b', '5min', 'FD'),
    ('high|b', '5min', 'FD'),
    ('low|b', '5min', 'FD'),
    ('close|b', '5min', 'FD'),
    ('open|f', '5min', 'FD'),
    ('high|f', '5min', 'FD'),
    ('low|f', '5min', 'FD'),
    ('close|f', '5min', 'FD'),
    ('open', '5min', 'FD'),
    ('high', '5min', 'FD'),
    ('low', '5min', 'FD'),
    ('close', '5min', 'FD'),
    ('volume', '5min', 'FD'),
    ('amount', '5min', 'FD'),
    ('open|b', '15min', 'FD'),
    ('high|b', '15min', 'FD'),
    ('low|b', '15min', 'FD'),
    ('close|b', '15min', 'FD'),
    ('open|f', '15min', 'FD'),
    ('high|f', '15min', 'FD'),
    ('low|f', '15min', 'FD'),
    ('close|f', '15min', 'FD'),
    ('open', '15min', 'FD'),
    ('high', '15min', 'FD'),
    ('low', '15min', 'FD'),
    ('close', '15min', 'FD'),
    ('volume', '15min', 'FD'),
    ('amount', '15min', 'FD'),
    ('open|b', '30min', 'FD'),
    ('high|b', '30min', 'FD'),
    ('low|b', '30min', 'FD'),
    ('close|b', '30min', 'FD'),
    ('open|f', '30min', 'FD'),
    ('high|f', '30min', 'FD'),
    ('low|f', '30min', 'FD'),
    ('close|f', '30min', 'FD'),
    ('open', '30min', 'FD'),
    ('high', '30min', 'FD'),
    ('low', '30min', 'FD'),
    ('close', '30min', 'FD'),
    ('volume', '30min', 'FD'),
    ('amount', '30min', 'FD'),
    ('open|b', 'h', 'FD'),
    ('high|b', 'h', 'FD'),
    ('low|b', 'h', 'FD'),
    ('close|b', 'h', 'FD'),
    ('open|f', 'h', 'FD'),
    ('high|f', 'h', 'FD'),
    ('low|f', 'h', 'FD'),
    ('close|f', 'h', 'FD'),
    ('open', 'h', 'FD'),
    ('high', 'h', 'FD'),
    ('low', 'h', 'FD'),
    ('close', 'h', 'FD'),
    ('volume', 'h', 'FD'),
    ('amount', 'h', 'FD'),
    ('unit_nav', 'd', 'FD'),
    ('accum_nav', 'd', 'FD'),
    ('accum_div', 'd', 'FD'),
    ('net_asset', 'd', 'FD'),
    ('total_netasset', 'd', 'FD'),
    ('adj_nav', 'd', 'FD'),
    ('buy_sm_vol', 'd', 'E'),
    ('buy_sm_amount', 'd', 'E'),
    ('sell_sm_vol', 'd', 'E'),
    ('sell_sm_amount', 'd', 'E'),
    ('buy_md_vol', 'd', 'E'),
    ('buy_md_amount', 'd', 'E'),
    ('sell_md_vol', 'd', 'E'),
    ('sell_md_amount', 'd', 'E'),
    ('buy_lg_vol', 'd', 'E'),
    ('buy_lg_amount', 'd', 'E'),
    ('sell_lg_vol', 'd', 'E'),
    ('sell_lg_amount', 'd', 'E'),
    ('buy_elg_vol', 'd', 'E'),
    ('buy_elg_amount', 'd', 'E'),
    ('sell_elg_vol', 'd', 'E'),
    ('sell_elg_amount', 'd', 'E'),
    ('net_mf_vol', 'd', 'E'),
    ('net_mf_amount', 'd', 'E'),
    ('up_limit', 'd', 'E'),
    ('down_limit', 'd', 'E'),
    ('ggt_ss', 'd', 'Any'),
    ('ggt_sz', 'd', 'Any'),
    ('hgt', 'd', 'Any'),
    ('sgt', 'd', 'Any'),
    ('north_money', 'd', 'Any'),
    ('south_money', 'd', 'Any'),
    ('basic_eps', 'q', 'E'),
    ('diluted_eps', 'q', 'E'),
    ('total_revenue', 'q', 'E'),
    ('revenue', 'q', 'E'),
    ('int_income', 'q', 'E'),
    ('prem_earned', 'q', 'E'),
    ('comm_income', 'q', 'E'),
    ('n_commis_income', 'q', 'E'),
    ('n_oth_income', 'q', 'E'),
    ('n_oth_b_income', 'q', 'E'),
    ('prem_income', 'q', 'E'),
    ('out_prem', 'q', 'E'),
    ('une_prem_reser', 'q', 'E'),
    ('reins_income', 'q', 'E'),
    ('n_sec_tb_income', 'q', 'E'),
    ('n_sec_uw_income', 'q', 'E'),
    ('n_asset_mg_income', 'q', 'E'),
    ('oth_b_income', 'q', 'E'),
    ('fv_value_chg_gain', 'q', 'E'),
    ('invest_income', 'q', 'E'),
    ('ass_invest_income', 'q', 'E'),
    ('forex_gain', 'q', 'E'),
    ('total_cogs', 'q', 'E'),
    ('oper_cost', 'q', 'E'),
    ('int_exp', 'q', 'E'),
    ('comm_exp', 'q', 'E'),
    ('biz_tax_surchg', 'q', 'E'),
    ('sell_exp', 'q', 'E'),
    ('admin_exp', 'q', 'E'),
    ('fin_exp', 'q', 'E'),
    ('assets_impair_loss', 'q', 'E'),
    ('prem_refund', 'q', 'E'),
    ('compens_payout', 'q', 'E'),
    ('reser_insur_liab', 'q', 'E'),
    ('div_payt', 'q', 'E'),
    ('reins_exp', 'q', 'E'),
    ('oper_exp', 'q', 'E'),
    ('compens_payout_refu', 'q', 'E'),
    ('insur_reser_refu', 'q', 'E'),
    ('reins_cost_refund', 'q', 'E'),
    ('other_bus_cost', 'q', 'E'),
    ('operate_profit', 'q', 'E'),
    ('non_oper_income', 'q', 'E'),
    ('non_oper_exp', 'q', 'E'),
    ('nca_disploss', 'q', 'E'),
    ('total_profit', 'q', 'E'),
    ('income_tax', 'q', 'E'),
    ('net_income', 'q', 'E'),
    ('n_income_attr_p', 'q', 'E'),
    ('minority_gain', 'q', 'E'),
    ('oth_compr_income', 'q', 'E'),
    ('t_compr_income', 'q', 'E'),
    ('compr_inc_attr_p', 'q', 'E'),
    ('compr_inc_attr_m_s', 'q', 'E'),
    ('income_ebit', 'q', 'E'),
    ('income_ebitda', 'q', 'E'),
    ('insurance_exp', 'q', 'E'),
    ('undist_profit', 'q', 'E'),
    ('distable_profit', 'q', 'E'),
    ('income_rd_exp', 'q', 'E'),
    ('fin_exp_int_exp', 'q', 'E'),
    ('fin_exp_int_inc', 'q', 'E'),
    ('transfer_surplus_rese', 'q', 'E'),
    ('transfer_housing_imprest', 'q', 'E'),
    ('transfer_oth', 'q', 'E'),
    ('adj_lossgain', 'q', 'E'),
    ('withdra_legal_surplus', 'q', 'E'),
    ('withdra_legal_pubfund', 'q', 'E'),
    ('withdra_biz_devfund', 'q', 'E'),
    ('withdra_rese_fund', 'q', 'E'),
    ('withdra_oth_ersu', 'q', 'E'),
    ('workers_welfare', 'q', 'E'),
    ('distr_profit_shrhder', 'q', 'E'),
    ('prfshare_payable_dvd', 'q', 'E'),
    ('comshare_payable_dvd', 'q', 'E'),
    ('capit_comstock_div', 'q', 'E'),
    ('net_after_nr_lp_correct', 'q', 'E'),
    ('income_credit_impa_loss', 'q', 'E'),
    ('net_expo_hedging_benefits', 'q', 'E'),
    ('oth_impair_loss_assets', 'q', 'E'),
    ('total_opcost', 'q', 'E'),
    ('amodcost_fin_assets', 'q', 'E'),
    ('oth_income', 'q', 'E'),
    ('asset_disp_income', 'q', 'E'),
    ('continued_net_profit', 'q', 'E'),
    ('end_net_profit', 'q', 'E'),
    ('total_share', 'q', 'E'),
    ('cap_rese', 'q', 'E'),
    ('undistr_porfit', 'q', 'E'),
    ('surplus_rese', 'q', 'E'),
    ('special_rese', 'q', 'E'),
    ('money_cap', 'q', 'E'),
    ('trad_asset', 'q', 'E'),
    ('notes_receiv', 'q', 'E'),
    ('accounts_receiv', 'q', 'E'),
    ('oth_receiv', 'q', 'E'),
    ('prepayment', 'q', 'E'),
    ('div_receiv', 'q', 'E'),
    ('int_receiv', 'q', 'E'),
    ('inventories', 'q', 'E'),
    ('amor_exp', 'q', 'E'),
    ('nca_within_1y', 'q', 'E'),
    ('sett_rsrv', 'q', 'E'),
    ('loanto_oth_bank_fi', 'q', 'E'),
    ('premium_receiv', 'q', 'E'),
    ('reinsur_receiv', 'q', 'E'),
    ('reinsur_res_receiv', 'q', 'E'),
    ('pur_resale_fa', 'q', 'E'),
    ('oth_cur_assets', 'q', 'E'),
    ('total_cur_assets', 'q', 'E'),
    ('fa_avail_for_sale', 'q', 'E'),
    ('htm_invest', 'q', 'E'),
    ('lt_eqt_invest', 'q', 'E'),
    ('invest_real_estate', 'q', 'E'),
    ('time_deposits', 'q', 'E'),
    ('oth_assets', 'q', 'E'),
    ('lt_rec', 'q', 'E'),
    ('fix_assets', 'q', 'E'),
    ('cip', 'q', 'E'),
    ('const_materials', 'q', 'E'),
    ('fixed_assets_disp', 'q', 'E'),
    ('produc_bio_assets', 'q', 'E'),
    ('oil_and_gas_assets', 'q', 'E'),
    ('intan_assets', 'q', 'E'),
    ('r_and_d', 'q', 'E'),
    ('goodwill', 'q', 'E'),
    ('lt_amor_exp', 'q', 'E'),
    ('defer_tax_assets', 'q', 'E'),
    ('decr_in_disbur', 'q', 'E'),
    ('oth_nca', 'q', 'E'),
    ('total_nca', 'q', 'E'),
    ('cash_reser_cb', 'q', 'E'),
    ('depos_in_oth_bfi', 'q', 'E'),
    ('prec_metals', 'q', 'E'),
    ('deriv_assets', 'q', 'E'),
    ('rr_reins_une_prem', 'q', 'E'),
    ('rr_reins_outstd_cla', 'q', 'E'),
    ('rr_reins_lins_liab', 'q', 'E'),
    ('rr_reins_lthins_liab', 'q', 'E'),
    ('refund_depos', 'q', 'E'),
    ('ph_pledge_loans', 'q', 'E'),
    ('refund_cap_depos', 'q', 'E'),
    ('indep_acct_assets', 'q', 'E'),
    ('client_depos', 'q', 'E'),
    ('client_prov', 'q', 'E'),
    ('transac_seat_fee', 'q', 'E'),
    ('invest_as_receiv', 'q', 'E'),
    ('total_assets', 'q', 'E'),
    ('lt_borr', 'q', 'E'),
    ('st_borr', 'q', 'E'),
    ('cb_borr', 'q', 'E'),
    ('depos_ib_deposits', 'q', 'E'),
    ('loan_oth_bank', 'q', 'E'),
    ('trading_fl', 'q', 'E'),
    ('notes_payable', 'q', 'E'),
    ('acct_payable', 'q', 'E'),
    ('adv_receipts', 'q', 'E'),
    ('sold_for_repur_fa', 'q', 'E'),
    ('comm_payable', 'q', 'E'),
    ('payroll_payable', 'q', 'E'),
    ('taxes_payable', 'q', 'E'),
    ('int_payable', 'q', 'E'),
    ('div_payable', 'q', 'E'),
    ('oth_payable', 'q', 'E'),
    ('acc_exp', 'q', 'E'),
    ('deferred_inc', 'q', 'E'),
    ('st_bonds_payable', 'q', 'E'),
    ('payable_to_reinsurer', 'q', 'E'),
    ('rsrv_insur_cont', 'q', 'E'),
    ('acting_trading_sec', 'q', 'E'),
    ('acting_uw_sec', 'q', 'E'),
    ('non_cur_liab_due_1y', 'q', 'E'),
    ('oth_cur_liab', 'q', 'E'),
    ('total_cur_liab', 'q', 'E'),
    ('bond_payable', 'q', 'E'),
    ('lt_payable', 'q', 'E'),
    ('specific_payables', 'q', 'E'),
    ('estimated_liab', 'q', 'E'),
    ('defer_tax_liab', 'q', 'E'),
    ('defer_inc_non_cur_liab', 'q', 'E'),
    ('oth_ncl', 'q', 'E'),
    ('total_ncl', 'q', 'E'),
    ('depos_oth_bfi', 'q', 'E'),
    ('deriv_liab', 'q', 'E'),
    ('depos', 'q', 'E'),
    ('agency_bus_liab', 'q', 'E'),
    ('oth_liab', 'q', 'E'),
    ('prem_receiv_adva', 'q', 'E'),
    ('depos_received', 'q', 'E'),
    ('ph_invest', 'q', 'E'),
    ('reser_une_prem', 'q', 'E'),
    ('reser_outstd_claims', 'q', 'E'),
    ('reser_lins_liab', 'q', 'E'),
    ('reser_lthins_liab', 'q', 'E'),
    ('indept_acc_liab', 'q', 'E'),
    ('pledge_borr', 'q', 'E'),
    ('indem_payable', 'q', 'E'),
    ('policy_div_payable', 'q', 'E'),
    ('total_liab', 'q', 'E'),
    ('treasury_share', 'q', 'E'),
    ('ordin_risk_reser', 'q', 'E'),
    ('forex_differ', 'q', 'E'),
    ('invest_loss_unconf', 'q', 'E'),
    ('minority_int', 'q', 'E'),
    ('total_hldr_eqy_exc_min_int', 'q', 'E'),
    ('total_hldr_eqy_inc_min_int', 'q', 'E'),
    ('total_liab_hldr_eqy', 'q', 'E'),
    ('lt_payroll_payable', 'q', 'E'),
    ('oth_comp_income', 'q', 'E'),
    ('oth_eqt_tools', 'q', 'E'),
    ('oth_eqt_tools_p_shr', 'q', 'E'),
    ('lending_funds', 'q', 'E'),
    ('acc_receivable', 'q', 'E'),
    ('st_fin_payable', 'q', 'E'),
    ('payables', 'q', 'E'),
    ('hfs_assets', 'q', 'E'),
    ('hfs_sales', 'q', 'E'),
    ('cost_fin_assets', 'q', 'E'),
    ('fair_value_fin_assets', 'q', 'E'),
    ('cip_total', 'q', 'E'),
    ('oth_pay_total', 'q', 'E'),
    ('long_pay_total', 'q', 'E'),
    ('debt_invest', 'q', 'E'),
    ('oth_debt_invest', 'q', 'E'),
    ('oth_eq_invest', 'q', 'E'),
    ('oth_illiq_fin_assets', 'q', 'E'),
    ('oth_eq_ppbond', 'q', 'E'),
    ('receiv_financing', 'q', 'E'),
    ('use_right_assets', 'q', 'E'),
    ('lease_liab', 'q', 'E'),
    ('contract_assets', 'q', 'E'),
    ('contract_liab', 'q', 'E'),
    ('accounts_receiv_bill', 'q', 'E'),
    ('accounts_pay', 'q', 'E'),
    ('oth_rcv_total', 'q', 'E'),
    ('fix_assets_total', 'q', 'E'),
    ('net_profit', 'q', 'E'),
    ('finan_exp', 'q', 'E'),
    ('c_fr_sale_sg', 'q', 'E'),
    ('recp_tax_rends', 'q', 'E'),
    ('n_depos_incr_fi', 'q', 'E'),
    ('n_incr_loans_cb', 'q', 'E'),
    ('n_inc_borr_oth_fi', 'q', 'E'),
    ('prem_fr_orig_contr', 'q', 'E'),
    ('n_incr_insured_dep', 'q', 'E'),
    ('n_reinsur_prem', 'q', 'E'),
    ('n_incr_disp_tfa', 'q', 'E'),
    ('ifc_cash_incr', 'q', 'E'),
    ('n_incr_disp_faas', 'q', 'E'),
    ('n_incr_loans_oth_bank', 'q', 'E'),
    ('n_cap_incr_repur', 'q', 'E'),
    ('c_fr_oth_operate_a', 'q', 'E'),
    ('c_inf_fr_operate_a', 'q', 'E'),
    ('c_paid_goods_s', 'q', 'E'),
    ('c_paid_to_for_empl', 'q', 'E'),
    ('c_paid_for_taxes', 'q', 'E'),
    ('n_incr_clt_loan_adv', 'q', 'E'),
    ('n_incr_dep_cbob', 'q', 'E'),
    ('c_pay_claims_orig_inco', 'q', 'E'),
    ('pay_handling_chrg', 'q', 'E'),
    ('pay_comm_insur_plcy', 'q', 'E'),
    ('oth_cash_pay_oper_act', 'q', 'E'),
    ('st_cash_out_act', 'q', 'E'),
    ('n_cashflow_act', 'q', 'E'),
    ('oth_recp_ral_inv_act', 'q', 'E'),
    ('c_disp_withdrwl_invest', 'q', 'E'),
    ('c_recp_return_invest', 'q', 'E'),
    ('n_recp_disp_fiolta', 'q', 'E'),
    ('n_recp_disp_sobu', 'q', 'E'),
    ('stot_inflows_inv_act', 'q', 'E'),
    ('c_pay_acq_const_fiolta', 'q', 'E'),
    ('c_paid_invest', 'q', 'E'),
    ('n_disp_subs_oth_biz', 'q', 'E'),
    ('oth_pay_ral_inv_act', 'q', 'E'),
    ('n_incr_pledge_loan', 'q', 'E'),
    ('stot_out_inv_act', 'q', 'E'),
    ('n_cashflow_inv_act', 'q', 'E'),
    ('c_recp_borrow', 'q', 'E'),
    ('proc_issue_bonds', 'q', 'E'),
    ('oth_cash_recp_ral_fnc_act', 'q', 'E'),
    ('stot_cash_in_fnc_act', 'q', 'E'),
    ('free_cashflow', 'q', 'E'),
    ('c_prepay_amt_borr', 'q', 'E'),
    ('c_pay_dist_dpcp_int_exp', 'q', 'E'),
    ('incl_dvd_profit_paid_sc_ms', 'q', 'E'),
    ('oth_cashpay_ral_fnc_act', 'q', 'E'),
    ('stot_cashout_fnc_act', 'q', 'E'),
    ('n_cash_flows_fnc_act', 'q', 'E'),
    ('eff_fx_flu_cash', 'q', 'E'),
    ('n_incr_cash_cash_equ', 'q', 'E'),
    ('c_cash_equ_beg_period', 'q', 'E'),
    ('c_cash_equ_end_period', 'q', 'E'),
    ('c_recp_cap_contrib', 'q', 'E'),
    ('incl_cash_rec_saims', 'q', 'E'),
    ('uncon_invest_loss', 'q', 'E'),
    ('prov_depr_assets', 'q', 'E'),
    ('depr_fa_coga_dpba', 'q', 'E'),
    ('amort_intang_assets', 'q', 'E'),
    ('lt_amort_deferred_exp', 'q', 'E'),
    ('decr_deferred_exp', 'q', 'E'),
    ('incr_acc_exp', 'q', 'E'),
    ('loss_disp_fiolta', 'q', 'E'),
    ('loss_scr_fa', 'q', 'E'),
    ('loss_fv_chg', 'q', 'E'),
    ('invest_loss', 'q', 'E'),
    ('decr_def_inc_tax_assets', 'q', 'E'),
    ('incr_def_inc_tax_liab', 'q', 'E'),
    ('decr_inventories', 'q', 'E'),
    ('decr_oper_payable', 'q', 'E'),
    ('incr_oper_payable', 'q', 'E'),
    ('others', 'q', 'E'),
    ('im_net_cashflow_oper_act', 'q', 'E'),
    ('conv_debt_into_cap', 'q', 'E'),
    ('conv_copbonds_due_within_1y', 'q', 'E'),
    ('fa_fnc_leases', 'q', 'E'),
    ('im_n_incr_cash_equ', 'q', 'E'),
    ('net_dism_capital_add', 'q', 'E'),
    ('net_cash_rece_sec', 'q', 'E'),
    ('cashflow_credit_impa_loss', 'q', 'E'),
    ('use_right_asset_dep', 'q', 'E'),
    ('oth_loss_asset', 'q', 'E'),
    ('end_bal_cash', 'q', 'E'),
    ('beg_bal_cash', 'q', 'E'),
    ('end_bal_cash_equ', 'q', 'E'),
    ('beg_bal_cash_equ', 'q', 'E'),
    ('express_revenue', 'q', 'E'),
    ('express_operate_profit', 'q', 'E'),
    ('express_total_profit', 'q', 'E'),
    ('express_n_income', 'q', 'E'),
    ('express_total_assets', 'q', 'E'),
    ('express_total_hldr_eqy_exc_min_int', 'q', 'E'),
    ('express_diluted_eps', 'q', 'E'),
    ('diluted_roe', 'q', 'E'),
    ('yoy_net_profit', 'q', 'E'),
    ('bps', 'q', 'E'),
    ('yoy_sales', 'q', 'E'),
    ('yoy_op', 'q', 'E'),
    ('yoy_tp', 'q', 'E'),
    ('yoy_dedu_np', 'q', 'E'),
    ('yoy_eps', 'q', 'E'),
    ('yoy_roe', 'q', 'E'),
    ('growth_assets', 'q', 'E'),
    ('yoy_equity', 'q', 'E'),
    ('growth_bps', 'q', 'E'),
    ('or_last_year', 'q', 'E'),
    ('op_last_year', 'q', 'E'),
    ('tp_last_year', 'q', 'E'),
    ('np_last_year', 'q', 'E'),
    ('eps_last_year', 'q', 'E'),
    ('open_net_assets', 'q', 'E'),
    ('open_bps', 'q', 'E'),
    ('perf_summary', 'q', 'E'),
    ('eps', 'q', 'E'),
    ('dt_eps', 'q', 'E'),
    ('total_revenue_ps', 'q', 'E'),
    ('revenue_ps', 'q', 'E'),
    ('capital_rese_ps', 'q', 'E'),
    ('surplus_rese_ps', 'q', 'E'),
    ('undist_profit_ps', 'q', 'E'),
    ('extra_item', 'q', 'E'),
    ('profit_dedt', 'q', 'E'),
    ('gross_margin', 'q', 'E'),
    ('current_ratio', 'q', 'E'),
    ('quick_ratio', 'q', 'E'),
    ('cash_ratio', 'q', 'E'),
    ('invturn_days', 'q', 'E'),
    ('arturn_days', 'q', 'E'),
    ('inv_turn', 'q', 'E'),
    ('ar_turn', 'q', 'E'),
    ('ca_turn', 'q', 'E'),
    ('fa_turn', 'q', 'E'),
    ('assets_turn', 'q', 'E'),
    ('op_income', 'q', 'E'),
    ('valuechange_income', 'q', 'E'),
    ('interst_income', 'q', 'E'),
    ('daa', 'q', 'E'),
    ('ebit', 'q', 'E'),
    ('ebitda', 'q', 'E'),
    ('fcff', 'q', 'E'),
    ('fcfe', 'q', 'E'),
    ('current_exint', 'q', 'E'),
    ('noncurrent_exint', 'q', 'E'),
    ('interestdebt', 'q', 'E'),
    ('netdebt', 'q', 'E'),
    ('tangible_asset', 'q', 'E'),
    ('working_capital', 'q', 'E'),
    ('networking_capital', 'q', 'E'),
    ('invest_capital', 'q', 'E'),
    ('retained_earnings', 'q', 'E'),
    ('diluted2_eps', 'q', 'E'),
    ('express_bps', 'q', 'E'),
    ('ocfps', 'q', 'E'),
    ('retainedps', 'q', 'E'),
    ('cfps', 'q', 'E'),
    ('ebit_ps', 'q', 'E'),
    ('fcff_ps', 'q', 'E'),
    ('fcfe_ps', 'q', 'E'),
    ('netprofit_margin', 'q', 'E'),
    ('grossprofit_margin', 'q', 'E'),
    ('cogs_of_sales', 'q', 'E'),
    ('expense_of_sales', 'q', 'E'),
    ('profit_to_gr', 'q', 'E'),
    ('saleexp_to_gr', 'q', 'E'),
    ('adminexp_of_gr', 'q', 'E'),
    ('finaexp_of_gr', 'q', 'E'),
    ('impai_ttm', 'q', 'E'),
    ('gc_of_gr', 'q', 'E'),
    ('op_of_gr', 'q', 'E'),
    ('ebit_of_gr', 'q', 'E'),
    ('roe', 'q', 'E'),
    ('roe_waa', 'q', 'E'),
    ('roe_dt', 'q', 'E'),
    ('roa', 'q', 'E'),
    ('npta', 'q', 'E'),
    ('roic', 'q', 'E'),
    ('roe_yearly', 'q', 'E'),
    ('roa2_yearly', 'q', 'E'),
    ('roe_avg', 'q', 'E'),
    ('opincome_of_ebt', 'q', 'E'),
    ('investincome_of_ebt', 'q', 'E'),
    ('n_op_profit_of_ebt', 'q', 'E'),
    ('tax_to_ebt', 'q', 'E'),
    ('dtprofit_to_profit', 'q', 'E'),
    ('salescash_to_or', 'q', 'E'),
    ('ocf_to_or', 'q', 'E'),
    ('ocf_to_opincome', 'q', 'E'),
    ('capitalized_to_da', 'q', 'E'),
    ('debt_to_assets', 'q', 'E'),
    ('assets_to_eqt', 'q', 'E'),
    ('dp_assets_to_eqt', 'q', 'E'),
    ('ca_to_assets', 'q', 'E'),
    ('nca_to_assets', 'q', 'E'),
    ('tbassets_to_totalassets', 'q', 'E'),
    ('int_to_talcap', 'q', 'E'),
    ('eqt_to_talcapital', 'q', 'E'),
    ('currentdebt_to_debt', 'q', 'E'),
    ('longdeb_to_debt', 'q', 'E'),
    ('ocf_to_shortdebt', 'q', 'E'),
    ('debt_to_eqt', 'q', 'E'),
    ('eqt_to_debt', 'q', 'E'),
    ('eqt_to_interestdebt', 'q', 'E'),
    ('tangibleasset_to_debt', 'q', 'E'),
    ('tangasset_to_intdebt', 'q', 'E'),
    ('tangibleasset_to_netdebt', 'q', 'E'),
    ('ocf_to_debt', 'q', 'E'),
    ('ocf_to_interestdebt', 'q', 'E'),
    ('ocf_to_netdebt', 'q', 'E'),
    ('ebit_to_interest', 'q', 'E'),
    ('longdebt_to_workingcapital', 'q', 'E'),
    ('ebitda_to_debt', 'q', 'E'),
    ('turn_days', 'q', 'E'),
    ('roa_yearly', 'q', 'E'),
    ('roa_dp', 'q', 'E'),
    ('fixed_assets', 'q', 'E'),
    ('profit_prefin_exp', 'q', 'E'),
    ('non_op_profit', 'q', 'E'),
    ('op_to_ebt', 'q', 'E'),
    ('nop_to_ebt', 'q', 'E'),
    ('ocf_to_profit', 'q', 'E'),
    ('cash_to_liqdebt', 'q', 'E'),
    ('cash_to_liqdebt_withinterest', 'q', 'E'),
    ('op_to_liqdebt', 'q', 'E'),
    ('op_to_debt', 'q', 'E'),
    ('roic_yearly', 'q', 'E'),
    ('total_fa_trun', 'q', 'E'),
    ('profit_to_op', 'q', 'E'),
    ('q_opincome', 'q', 'E'),
    ('q_investincome', 'q', 'E'),
    ('q_dtprofit', 'q', 'E'),
    ('q_eps', 'q', 'E'),
    ('q_netprofit_margin', 'q', 'E'),
    ('q_gsprofit_margin', 'q', 'E'),
    ('q_exp_to_sales', 'q', 'E'),
    ('q_profit_to_gr', 'q', 'E'),
    ('q_saleexp_to_gr', 'q', 'E'),
    ('q_adminexp_to_gr', 'q', 'E'),
    ('q_finaexp_to_gr', 'q', 'E'),
    ('q_impair_to_gr_ttm', 'q', 'E'),
    ('q_gc_to_gr', 'q', 'E'),
    ('q_op_to_gr', 'q', 'E'),
    ('q_roe', 'q', 'E'),
    ('q_dt_roe', 'q', 'E'),
    ('q_npta', 'q', 'E'),
    ('q_opincome_to_ebt', 'q', 'E'),
    ('q_investincome_to_ebt', 'q', 'E'),
    ('q_dtprofit_to_profit', 'q', 'E'),
    ('q_salescash_to_or', 'q', 'E'),
    ('q_ocf_to_sales', 'q', 'E'),
    ('q_ocf_to_or', 'q', 'E'),
    ('basic_eps_yoy', 'q', 'E'),
    ('dt_eps_yoy', 'q', 'E'),
    ('cfps_yoy', 'q', 'E'),
    ('op_yoy', 'q', 'E'),
    ('ebt_yoy', 'q', 'E'),
    ('netprofit_yoy', 'q', 'E'),
    ('dt_netprofit_yoy', 'q', 'E'),
    ('ocf_yoy', 'q', 'E'),
    ('roe_yoy', 'q', 'E'),
    ('bps_yoy', 'q', 'E'),
    ('assets_yoy', 'q', 'E'),
    ('eqt_yoy', 'q', 'E'),
    ('tr_yoy', 'q', 'E'),
    ('or_yoy', 'q', 'E'),
    ('q_gr_yoy', 'q', 'E'),
    ('q_gr_qoq', 'q', 'E'),
    ('q_sales_yoy', 'q', 'E'),
    ('q_sales_qoq', 'q', 'E'),
    ('q_op_yoy', 'q', 'E'),
    ('q_op_qoq', 'q', 'E'),
    ('q_profit_yoy', 'q', 'E'),
    ('q_profit_qoq', 'q', 'E'),
    ('q_netprofit_yoy', 'q', 'E'),
    ('q_netprofit_qoq', 'q', 'E'),
    ('equity_yoy', 'q', 'E'),
    ('rd_exp', 'q', 'E'),
    ('rzye|SSE', 'd', 'None'),
    ('rzmre|SSE', 'd', 'None'),
    ('rzche|SSE', 'd', 'None'),
    ('rqye|SSE', 'd', 'None'),
    ('rqmcl|SZSE', 'd', 'None'),
    ('rzrqye|SZSE', 'd', 'None'),
    ('rqyl|SZSE', 'd', 'None'),
    ('top_list_close', 'd', 'E'),
    ('top_list_pct_change', 'd', 'E'),
    ('top_list_turnover_rate', 'd', 'E'),
    ('top_list_amount', 'd', 'E'),
    ('top_list_l_sell', 'd', 'E'),
    ('top_list_l_buy', 'd', 'E'),
    ('top_list_l_amount', 'd', 'E'),
    ('top_list_net_amount', 'd', 'E'),
    ('top_list_net_rate', 'd', 'E'),
    ('top_list_amount_rate', 'd', 'E'),
    ('top_list_float_values', 'd', 'E'),
    ('top_list_reason', 'd', 'E'),
    ('total_mv', 'd', 'IDX'),
    ('float_mv', 'd', 'IDX'),
    ('total_share     float', 'd', 'IDX'),
    ('float_share', 'd', 'IDX'),
    ('free_share', 'd', 'IDX'),
    ('turnover_rate', 'd', 'IDX'),
    ('turnover_rate_f', 'd', 'IDX'),
    ('pe', 'd', 'IDX'),
    ('pe_ttm', 'd', 'IDX'),
    ('pb', 'd', 'IDX'),
    ('turnover_rate', 'd', 'E'),
    ('turnover_rate_f', 'd', 'E'),
    ('volume_ratio', 'd', 'E'),
    ('pe', 'd', 'E'),
    ('pe_ttm', 'd', 'E'),
    ('pb', 'd', 'E'),
    ('ps', 'd', 'E'),
    ('ps_ttm', 'd', 'E'),
    ('dv_ratio', 'd', 'E'),
    ('dv_ttm', 'd', 'E'),
    ('total_share', 'd', 'E'),
    ('float_share', 'd', 'E'),
    ('free_share', 'd', 'E'),
    ('total_mv', 'd', 'E'),
    ('circ_mv', 'd', 'E'),
    ('vol_ratio', 'd', 'E'),
    ('turn_over', 'd', 'E'),
    ('swing', 'd', 'E'),
    ('selling', 'd', 'E'),
    ('buying', 'd', 'E'),
    ('total_share_b', 'd', 'E'),
    ('float_share_b', 'd', 'E'),
    ('pe_2', 'd', 'E'),
    ('float_mv_2', 'd', 'E'),
    ('total_mv_2', 'd', 'E'),
    ('avg_price', 'd', 'E'),
    ('strength', 'd', 'E'),
    ('activity', 'd', 'E'),
    ('avg_turnover', 'd', 'E'),
    ('attack', 'd', 'E'),
    ('interval_3', 'd', 'E'),
    ('interval_6', 'd', 'E'),
    ('cur_name', 'd', 'E'),
    ('change_reason', 'd', 'E'),
    ('suspend_timing', 'd', 'E'),
    ('is_suspended', 'd', 'E'),
    ('is_HS_top10', 'd', 'E'),
    ('top10_close', 'd', 'E'),
    ('top10_change', 'd', 'E'),
    ('top10_rank', 'd', 'E'),
    ('top10_amount', 'd', 'E'),
    ('top10_net_amount', 'd', 'E'),
    ('top10_buy', 'd', 'E'),
    ('top10_sell', 'd', 'E'),
    ('fd_share', 'd', 'FD'),
    ('managers_name', 'd', 'FD'),
    ('managers_gender', 'd', 'FD'),
    ('managers_birth_year', 'd', 'FD'),
    ('managers_edu', 'd', 'FD'),
    ('nationality', 'd', 'FD'),
    ('managers_resume', 'd', 'FD'),
    ('stk_div_planned', 'd', 'E'),
    ('stk_bo_rate_planned', 'd', 'E'),
    ('stk_co_rate_planned', 'd', 'E'),
    ('cash_div_planned', 'd', 'E'),
    ('cash_div_tax_planned', 'd', 'E'),
    ('stk_div_approved', 'd', 'E'),
    ('stk_bo_rate_approved', 'd', 'E'),
    ('stk_co_rate_approved', 'd', 'E'),
    ('cash_div_approved', 'd', 'E'),
    ('cash_div_tax_approved', 'd', 'E'),
    ('stk_div', 'd', 'E'),
    ('stk_bo_rate', 'd', 'E'),
    ('stk_co_rate', 'd', 'E'),
    ('cash_div', 'd', 'E'),
    ('cash_div_tax', 'd', 'E'),
    ('record_date', 'd', 'E'),
    ('ex_date', 'd', 'E'),
    ('pay_date', 'd', 'E'),
    ('imp_ann_date', 'd', 'E'),
    ('base_date', 'd', 'E'),
    ('base_share', 'd', 'E'),
    ('exalter', 'd', 'E'),
    ('side', 'd', 'E'),
    ('buy', 'd', 'E'),
    ('buy_rate', 'd', 'E'),
    ('sell', 'd', 'E'),
    ('sell_rate', 'd', 'E'),
    ('net_buy', 'd', 'E'),
    ('reason', 'd', 'E'),
    ('shibor|on', 'd', 'None'),
    ('shibor|1w', 'd', 'None'),
    ('shibor|2w', 'd', 'None'),
    ('shibor|1m', 'd', 'None'),
    ('shibor|3m', 'd', 'None'),
    ('shibor|6m', 'd', 'None'),
    ('shibor|9m', 'd', 'None'),
    ('shibor|1y', 'd', 'None'),
    ('libor_usd|on', 'd', 'None'),
    ('libor_usd|1w', 'd', 'None'),
    ('libor_usd|1m', 'd', 'None'),
    ('libor_usd|2m', 'd', 'None'),
    ('libor_usd|3m', 'd', 'None'),
    ('libor_usd|6m', 'd', 'None'),
    ('libor_usd|12m', 'd', 'None'),
    # ('libor_eur|on', 'd', 'None'),
    # ('libor_eur|1w', 'd', 'None'),
    # ('libor_eur|1m', 'd', 'None'),
    # ('libor_eur|2m', 'd', 'None'),
    # ('libor_eur|3m', 'd', 'None'),
    # ('libor_eur|6m', 'd', 'None'),
    # ('libor_eur|1y', 'd', 'None'),
    # ('libor_gbp|on', 'd', 'None'),
    # ('libor_gbp|1w', 'd', 'None'),
    # ('libor_gbp|1m', 'd', 'None'),
    # ('libor_gbp|2m', 'd', 'None'),
    # ('libor_gbp|3m', 'd', 'None'),
    # ('libor_gbp|6m', 'd', 'None'),
    # ('libor_gbp|1y', 'd', 'None'),
    ('hibor|on', 'd', 'None'),
    ('hibor|1w', 'd', 'None'),
    ('hibor|1m', 'd', 'None'),
    ('hibor|2m', 'd', 'None'),
    ('hibor|3m', 'd', 'None'),
    ('hibor|6m', 'd', 'None'),
    ('hibor|12m', 'd', 'None'),
    ('wz_comp', 'd', 'None'),
    ('wz_center', 'd', 'None'),
    ('wz_micro', 'd', 'None'),
    ('wz_cm', 'd', 'None'),
    ('wz_sdb', 'd', 'None'),
    ('wz_om', 'd', 'None'),
    ('wz_aa', 'd', 'None'),
    ('wz_m1', 'd', 'None'),
    ('wz_m3', 'd', 'None'),
    ('wz_m6', 'd', 'None'),
    ('wz_m12', 'd', 'None'),
    ('wz_long', 'd', 'None'),
    ('gz_d10', 'd', 'None'),
    ('gz_m1', 'd', 'None'),
    ('gz_m3', 'd', 'None'),
    ('gz_m6', 'd', 'None'),
    ('gz_m12', 'd', 'None'),
    ('gz_long', 'd', 'None'),
    ('cn_gdp', 'q', 'None'),
    ('cn_gdp_yoy', 'q', 'None'),
    ('cn_gdp_pi', 'q', 'None'),
    ('cn_gdp_pi_yoy', 'q', 'None'),
    ('cn_gdp_si', 'q', 'None'),
    ('cn_gdp_si_yoy', 'q', 'None'),
    ('cn_gdp_ti', 'q', 'None'),
    ('cn_gdp_ti_yoy', 'q', 'None'),
    ('nt_val', 'm', 'None'),
    ('nt_yoy', 'm', 'None'),
    ('nt_mom', 'm', 'None'),
    ('nt_accu', 'm', 'None'),
    ('town_val', 'm', 'None'),
    ('town_yoy', 'm', 'None'),
    ('town_mom', 'm', 'None'),
    ('town_accu', 'm', 'None'),
    ('cnt_val', 'm', 'None'),
    ('cnt_yoy', 'm', 'None'),
    ('cnt_mom', 'm', 'None'),
    ('cnt_accu', 'm', 'None'),
    ('ppi_yoy', 'm', 'None'),
    ('ppi_mp_yoy', 'm', 'None'),
    ('ppi_mp_qm_yoy', 'm', 'None'),
    ('ppi_mp_rm_yoy', 'm', 'None'),
    ('ppi_mp_p_yoy', 'm', 'None'),
    ('ppi_cg_yoy', 'm', 'None'),
    ('ppi_cg_f_yoy', 'm', 'None'),
    ('ppi_cg_c_yoy', 'm', 'None'),
    ('ppi_cg_adu_yoy', 'm', 'None'),
    ('ppi_cg_dcg_yoy', 'm', 'None'),
    ('ppi_mom', 'm', 'None'),
    ('ppi_mp_mom', 'm', 'None'),
    ('ppi_mp_qm_mom', 'm', 'None'),
    ('ppi_mp_rm_mom', 'm', 'None'),
    ('ppi_mp_p_mom', 'm', 'None'),
    ('ppi_cg_mom', 'm', 'None'),
    ('ppi_cg_f_mom', 'm', 'None'),
    ('ppi_cg_c_mom', 'm', 'None'),
    ('ppi_cg_adu_mom', 'm', 'None'),
    ('ppi_cg_dcg_mom', 'm', 'None'),
    ('ppi_accu', 'm', 'None'),
    ('ppi_mp_accu', 'm', 'None'),
    ('ppi_mp_qm_accu', 'm', 'None'),
    ('ppi_mp_rm_accu', 'm', 'None'),
    ('ppi_mp_p_accu', 'm', 'None'),
    ('ppi_cg_accu', 'm', 'None'),
    ('ppi_cg_f_accu', 'm', 'None'),
    ('ppi_cg_c_accu', 'm', 'None'),
    ('ppi_cg_adu_accu', 'm', 'None'),
    ('ppi_cg_dcg_accu', 'm', 'None'),
    ('cn_m0', 'm', 'None'),
    ('cn_m0_yoy', 'm', 'None'),
    ('cn_m0_mom', 'm', 'None'),
    ('cn_m1', 'm', 'None'),
    ('cn_m1_yoy', 'm', 'None'),
    ('cn_m1_mom', 'm', 'None'),
    ('cn_m2', 'm', 'None'),
    ('cn_m2_yoy', 'm', 'None'),
    ('cn_m2_mom', 'm', 'None'),
    ('inc_month', 'm', 'None'),
    ('inc_cumval', 'm', 'None'),
    ('stk_endval', 'm', 'None'),
    ('pmi010000', 'm', 'None'),
    ('pmi010100', 'm', 'None'),
    ('pmi010200', 'm', 'None'),
    ('pmi010300', 'm', 'None'),
    ('pmi010400', 'm', 'None'),
    ('pmi010401', 'm', 'None'),
    ('pmi010402', 'm', 'None'),
    ('pmi010403', 'm', 'None'),
    ('pmi010500', 'm', 'None'),
    ('pmi010501', 'm', 'None'),
    ('pmi010502', 'm', 'None'),
    ('pmi010503', 'm', 'None'),
    ('pmi010600', 'm', 'None'),
    ('pmi010601', 'm', 'None'),
    ('pmi010602', 'm', 'None'),
    ('pmi010603', 'm', 'None'),
    ('pmi010700', 'm', 'None'),
    ('pmi010701', 'm', 'None'),
    ('pmi010702', 'm', 'None'),
    ('pmi010703', 'm', 'None'),
    ('pmi010800', 'm', 'None'),
    ('pmi010801', 'm', 'None'),
    ('pmi010802', 'm', 'None'),
    ('pmi010803', 'm', 'None'),
    ('pmi010900', 'm', 'None'),
    ('pmi011000', 'm', 'None'),
    ('pmi011100', 'm', 'None'),
    ('pmi011200', 'm', 'None'),
    ('pmi011300', 'm', 'None'),
    ('pmi011400', 'm', 'None'),
    ('pmi011500', 'm', 'None'),
    ('pmi011600', 'm', 'None'),
    ('pmi011700', 'm', 'None'),
    ('pmi011800', 'm', 'None'),
    ('pmi011900', 'm', 'None'),
    ('pmi012000', 'm', 'None'),
    ('pmi020100', 'm', 'None'),
    ('pmi020101', 'm', 'None'),
    ('pmi020102', 'm', 'None'),
    ('pmi020200', 'm', 'None'),
    ('pmi020201', 'm', 'None'),
    ('pmi020202', 'm', 'None'),
    ('pmi020300', 'm', 'None'),
    ('pmi020301', 'm', 'None'),
    ('pmi020302', 'm', 'None'),
    ('pmi020400', 'm', 'None'),
    ('pmi020401', 'm', 'None'),
    ('pmi020402', 'm', 'None'),
    ('pmi020500', 'm', 'None'),
    ('pmi020501', 'm', 'None'),
    ('pmi020502', 'm', 'None'),
    ('pmi020600', 'm', 'None'),
    ('pmi020601', 'm', 'None'),
    ('pmi020602', 'm', 'None'),
    ('pmi020700', 'm', 'None'),
    ('pmi020800', 'm', 'None'),
    ('pmi020900', 'm', 'None'),
    ('pmi021000', 'm', 'None'),
    ('pmi030000', 'm', 'None'),
    ('p_change_min', 'd', 'E'),
    ('p_change_max', 'd', 'E'),
    ('net_profit_min', 'd', 'E'),
    ('net_profit_max', 'd', 'E'),
    ('last_parent_net', 'd', 'E'),
    ('first_ann_date', 'd', 'E'),
    ('summary', 'd', 'E'),
    ('change_reason', 'd', 'E'),
    ('block_trade_price', 'd', 'E'),
    ('block_trade_vol', 'd', 'E'),
    ('block_trade_amount', 'd', 'E'),
    ('block_trade_buyer', 'd', 'E'),
    ('block_trade_seller', 'd', 'E'),
    ('stock_holder_trade_name', 'd', 'E'),
    ('stock_holder_trade_type', 'd', 'E'),
    ('stock_holder_trade_in_de', 'd', 'E'),
    ('stock_holder_trade_change_vol', 'd', 'E'),
    ('stock_holder_trade_change_ratio', 'd', 'E'),
    ('stock_holder_trade_after_share', 'd', 'E'),
    ('stock_holder_trade_after_ratio', 'd', 'E'),
    ('stock_holder_trade_avg_price', 'd', 'E'),
    ('stock_holder_trade_total_share', 'd', 'E'),
    ('stock_holder_trade_begin_date', 'd', 'E'),
    ('stock_holder_trade_close_date', 'd', 'E'),
    ('margin_detail_rzye', 'd', 'E'),
    ('margin_detail_rqye', 'd', 'E'),
    ('margin_detail_rzmre', 'd', 'E'),
    ('margin_detail_rqyl', 'd', 'E'),
    ('margin_detail_rzche', 'd', 'E'),
    ('margin_detail_rqchl', 'd', 'E'),
    ('margin_detail_rqmcl', 'd', 'E'),
    ('margin_detail_rzrqye', 'd', 'E'),
]

ALL_TYPES_TO_TEST_WITH_SOME_ID = [
    'stock_name',
    'area',
    'industry',
    'close',
    'close|b',
    'high|f',
    ('low|forward', None, 'E'),
    ('open', 'w', None),
    ('pe', 'd', 'IDX'),
    ('pe', 'd', 'E'),
    ('pe', None, 'E'),
    ('ths_category', 'None', 'E'),
    ('weight_rule', 'None', 'IDX'),
    ('is_trade_day|SSE', 'd', 'None'),
    ('high-000300.SH', '5min', 'IDX'),
]


class TestDataTypes(unittest.TestCase):

    def setUp(self):

        from qteasy import QT_CONFIG, QT_DATA_SOURCE

        print('preparing test data sources with configurations...')
        self.ds = DataSource(
                'db',
                host=QT_CONFIG['test_db_host'],
                port=QT_CONFIG['test_db_port'],
                user=QT_CONFIG['test_db_user'],
                password=QT_CONFIG['test_db_password'],
                db_name=QT_CONFIG['test_db_name']
        )

        self.ds = QT_DATA_SOURCE

    def test_init(self):
        for k in ALL_TYPES_TO_TEST_WITH_SOME_ID:
            if isinstance(k, tuple):
                name, freq, asset_type = k
            else:
                name = k
                freq = None
                asset_type = None

            dtype = DataType(
                    name=name,
                    freq=freq,
                    asset_type=asset_type,
            )

            print(f'got input: {name}, {freq}, {asset_type}, created dtype: {dtype}:\n'
                  f'name:     {dtype.name}\n'
                  f'freq:     {dtype.freq}\n'
                  # f'all freqs: {dtype.available_freqs}\n'
                  f'asset_type: {dtype.asset_type}\n'
                  # f'all a_types: {dtype.available_asset_types}\n'
                  f'unsymbolizer: {dtype.unsymbolizer}\n'
                  f'desc:     {dtype.description}\n'
                  f'acq_type: {dtype.acquisition_type}\n'
                  f'kwargs:   {dtype.kwargs}\n')
            self.assertIsInstance(dtype, DataType)
            self.assertEqual(dtype.name, name)
            if freq is not None:
                self.assertEqual(dtype.freq, freq)
            if asset_type is not None:
                self.assertEqual(dtype.asset_type, asset_type)

        # test special case that was found fault:
        d1 = DataType(name='close|b')
        d2 = DataType(name='close|f')

        print(f'dtype 1: {d1}, and dtype 2: {d2}')
        self.assertEqual(d1.name, 'close|b')
        self.assertEqual(d2.name, 'close|f')
        d1_adj = d1.kwargs.get('adj_type')
        d2_adj = d2.kwargs.get('adj_type')
        self.assertEqual(d1_adj, 'b')
        self.assertEqual(d2_adj, 'f')

    def test_all_types_with_full_id(self):
        ds = self.ds
        total = len(ALL_TYPES_TO_TEST_WITH_FULL_ID)
        acquired = 0
        empty_count = 0
        empty_types = []
        empty_type_descs = []
        empty_type_acq_types = []
        all_tables = ds.all_data_tables
        for k in ALL_TYPES_TO_TEST_WITH_FULL_ID:
            self.assertIsInstance(k, tuple)

            # create a new instance of the data type
            name, freq, asset_type = k

            dtype = DataType(
                    name=name,
                    freq=freq,
                    asset_type=asset_type,
            )
            self.assertIsInstance(dtype, DataType)
            self.assertEqual(dtype.name, name)
            self.assertEqual(dtype.freq, freq)
            self.assertEqual(dtype.asset_type, asset_type)

            acq_type = dtype.acquisition_type
            desc = dtype.description

            table_name = dtype.kwargs['table_name']

            shares = None
            starts = '2019-09-01'
            ends = '2020-09-12'

            type_with_shares = ['direct', 'basics', 'adjustment', 'operation', 'composition', 'category']
            type_with_events = ['event_status', 'event_signal', 'event_multi_stat', 'selected_events']
            if (acq_type in type_with_shares) and (asset_type == 'E'):
                shares = ['000651.SZ', '000001.SZ', '002936.SZ', '603810.SH']
                if table_name == 'index_weight':
                    starts = '2018-09-01'
                    ends = '2020-12-31'
                if table_name in ['money_flow', 'stock_limit', ]:
                    starts = '2024-04-01'
                    ends = '2024-05-01'
            elif (acq_type in type_with_shares) and (asset_type == 'IDX'):
                shares = ['000300.SH', '000001.SH']
                if table_name == 'sw_industry_basic':
                    shares = ['801140.SI', '801710.SI', '801230.SI', '801770.SI', '801880.SI']
                if table_name == 'ths_index_basic':
                    shares = ['885566.TI', '885760.TI', '885599.TI', '885841.TI', '885883.TI']
                if table_name == 'ths_index_daily':
                    shares = ['700001.TI', '700002.TI', '700003.TI', '700004.TI', '700005.TI']
                    starts = '2024-04-01'
                    ends = '2024-05-01'
                if table_name == 'ci_index_daily':
                    shares = ['CI005001.CI', 'CI005005.CI', 'CI005010.CI', 'CI005014.CI', 'CI005015.CI']
                    starts = '2024-04-01'
                    ends = '2024-05-01'
                if table_name == 'sw_index_daily':
                    shares = ['801140.SI', '801710.SI', '801230.SI', '801770.SI', '801880.SI']
                    starts = '2024-04-01'
                    ends = '2024-05-01'
                if table_name == 'global_index_daily':
                    shares = ['AS51', 'CKLSE', 'CSX5P', 'DJI', 'HKAH']
                    starts = '2024-04-01'
                    ends = '2024-05-01'
            elif (acq_type in type_with_shares) and (asset_type == 'FD'):
                shares = ['515630.SH']
            elif (acq_type in type_with_shares) and (asset_type == 'FT'):
                shares = ['AG.SHF', 'A.DCE', 'CU.SHF', 'C.DCE']
                if table_name in ['future_weekly', 'future_monthly']:
                    starts = '2024-12-01'
                    ends = '2025-02-01'
            elif (acq_type in type_with_shares) and (asset_type == 'OPT'):
                shares = ['10000001.SH', '10001909.SH', '10001910.SH', '10001911.SH', '10007976.SH']
            elif (acq_type in type_with_events) and (asset_type == 'E'):
                shares = ['000007.SZ', '000017.SZ', '000003.SZ', '600019.SH', '600009.SH']
                starts = '2018-01-01'
                ends = '2020-05-01'
                # for special tables:
                if table_name == 'stock_suspend':
                    starts = '2020-03-10'
                    ends = '2020-03-13'
                elif table_name in ['top_list', 'hs_top10_stock', 'top_inst']:
                    shares = ['000651.SZ', '000001.SZ', '002936.SZ', '603810.SH']
                    starts = '2024-01-01'
                    ends = '2024-05-01'
                elif table_name in ['dividend']:
                    shares = ['000001.SZ', '000007.SZ', '000003.SZ', '000017.SZ', '000009.SZ']
                    starts = '2018-01-01'
                    ends = '2025-01-01'
            elif (acq_type in type_with_events) and (asset_type == 'FD'):
                shares = ['000152.OF', '960032.OF']
                starts = '2018-01-01'
                ends = '2020-05-01'

            if (asset_type in 'E') and (freq[-3:] == 'min'):
                starts = '2022-04-01'
                ends = '2022-04-15'
            elif (asset_type == 'FT') and (freq[-3:] == 'min'):
                starts = '2023-08-25'
                ends = '2023-08-27'
            elif (asset_type == 'OPT') and (freq[-3:] == 'min'):
                starts = '2024-09-27'
                ends = '2024-09-28'
            elif (asset_type == 'FD') and (freq == 'h'):
                starts = '2021-09-20'
                ends = '2021-09-30'
            elif freq[-3:] == 'min':
                starts = '2022-04-01'
                ends = '2022-04-15'

            if table_name in ['hk_top10_stock']:
                shares = ['00700.HK', '00857.HK', '00939.HK', '00941.HK', '01810.HK']
                starts = '2024-04-02'
                ends = '2024-04-05'

            if table_name in ['hs_money_flow', 'hibor', 'shibor', 'libor']:
                starts = '2024-04-01'
                ends = '2024-04-15'
            if table_name in ['hibor', 'libor']:
                starts = '2020-04-01'
                ends = '2020-06-15'
            if table_name in ['gz_index']:
                starts = '2015-01-01'
                ends = '2015-02-20'
            if table_name in ['cn_gdp', 'cn_cpi', 'cn_ppi', 'cn_sf', 'cn_money', 'cn_pmi']:
                starts = '2024-01-01'
                ends = '2024-12-31'

            if table_name in ['block_trade']:
                shares = ['000603.SZ', '000723.SZ', '000783.SZ', '000796.SZ', '000895.SZ', '002203.SZ']
                starts = '2024-04-01'
                ends = '2024-05-01'

            if table_name == 'stock_holder_trade':
                shares = ['002243.SZ', '300328.SZ', '300504.SZ', '300710.SZ', '300832.SZ',]
                starts = '2024-04-01'
                ends = '2024-05-01'

            if table_name == 'margin_detail':
                shares = ['300978.SZ', '300979.SZ', '300980.SZ', '300981.SZ', '300982.SZ', '300983.SZ', ]
                starts = '2024-04-01'
                ends = '2024-05-01'

            if table_name == 'stock_suspend':
                shares = ['000005.SZ', '000599.SZ', '002490.SZ', '600375.SH', '872931.BJ', '600165.SH', ]
                starts = '2024-04-01'
                ends = '2024-05-01'

            # print(f'testing dtype {dtype} with parameters: \n'
            #       f'shares: {shares}\n'
            #       f'starts/ends: {starts}/{ends}\n')

            if shares is not None:
                shares = list_to_str_format(shares)
            if table_name in ['cn_money']:
                # import pdb; pdb.set_trace()
                pass
            data = dtype.get_data_from_source(
                    ds,
                    symbols=shares,
                    starts=starts,
                    ends=ends,
            )

            acquired += 1
            progress_bar(acquired, total, comments=f'{dtype} - {dtype.description}', column_width=120)

            try:
                all_tables.remove(table_name)
            except ValueError:
                pass

            if data.empty:
                if freq in ['h', '30min', '15min', '5min', '1min',]:
                    continue
                empty_count += 1
                empty_types.append(k)
                empty_type_descs.append(desc)
                empty_type_acq_types.append(acq_type)
                print(f'\nempty data for {dtype} - {dtype.description}')
                continue

            print(f'\ngot data for {dtype}: \n{data}')

            # checking the datatypes and start / end dates of the data
            if acq_type in ['basics', 'category']:
                # index are shares
                self.assertIsInstance(data, pd.Series)
                self.assertTrue(data.index.dtype == 'object')
                self.assertTrue(all(share in shares for share in data.index))
            elif (acq_type in ['reference']) or (dtype.unsymbolizer is not None):
                self.assertIsInstance(data, pd.Series)
                self.assertEqual(data.index.dtype, 'datetime64[ns]')
                starts = pd.to_datetime(starts)
                ends = pd.to_datetime(ends)
                self.assertTrue(all(date >= starts for date in data.index))
                self.assertTrue(all(date <= ends for date in data.index))
            elif (acq_type in type_with_shares) and (dtype.unsymbolizer is None):
                self.assertIsInstance(data, pd.DataFrame)
                if not data.empty:
                    try:
                        self.assertEqual(data.index.dtype, 'datetime64[ns]')
                        self.assertGreaterEqual(data.index[0].date(), pd.Timestamp(starts).date())
                        self.assertLessEqual(data.index[-1].date(), pd.Timestamp(ends).date())
                    except AssertionError:
                        # import pdb;
                        # pdb.set_trace()
                        pass
            elif acq_type in type_with_events:
                self.assertIsInstance(data, pd.DataFrame)
                if not data.empty:
                    try:
                        self.assertEqual(data.index.dtype, 'datetime64[ns]')
                        self.assertGreaterEqual(data.index[0].date(), pd.Timestamp(starts).date())
                        self.assertLessEqual(data.index[-1].date(), pd.Timestamp(ends).date())
                    except AssertionError:
                        # import pdb
                        # pdb.set_trace()
                        pass
            else:
                self.assertIsInstance(data, pd.Series)

        print(f'\n{empty_count} out of {total} empty data types (except those in min freq data tables):')
        emptys = pd.DataFrame({
            'type':             empty_types,
            'description':      empty_type_descs,
            'acquisition_type': empty_type_acq_types
        })
        print(emptys.to_string())
        print('\n')
        print(f'{len(all_tables)} tables are not covered, those are:\n'
              f'{"=" * 80}\n')
        for table in all_tables:
            print(ds.get_table_info(table))

    def test_get_tables_by_dtypes(self):
        """ test module function get_tables_by_dtypes()"""
        tables = get_tables_by_dtypes(
                dtypes=['close', 'high', 'low'],
                freqs=['d', 'w', 'm'],
                asset_types=['E', 'IDX'],
        )
        print(f'\n{len(tables)} tables are covered by the data types:')
        print(tables)
        self.assertEqual(len(tables), 6)
        self.assertEqual(
                tables,
                {'stock_daily', 'index_monthly', 'stock_weekly', 'stock_monthly', 'index_weekly', 'index_daily'}
        )

        tables = get_tables_by_dtypes(
                dtypes=['close', 'high', 'low'],
                freqs=None,
                asset_types=['E', 'IDX'],
        )

        print(f'\n{len(tables)} tables are covered by the data types:')
        print(tables)
        self.assertEqual(len(tables), 16)
        self.assertEqual(
                tables,
                {'stock_daily', 'index_monthly', 'stock_weekly', 'stock_monthly', 'index_weekly', 'index_daily',
                 'stock_1min', 'index_1min', 'stock_hourly', 'stock_5min', 'stock_15min', 'stock_30min',
                 'index_hourly', 'index_5min', 'index_15min', 'index_30min', 'index_1min'}
        )

    def test_get_history_data(self):
        """ test getting arr, from real database """
        # test getting simple daily data with basic types without combination
        shares = ['000001.SZ', '000002.SZ', '600067.SH', '000300.SH', '518860.SH']
        htype_names = 'pe,close|b,open,swing,strength'
        htype_names = str_to_list(htype_names)
        start = '20210101'
        end = '20210301'
        asset_type = ['E', 'IDX', 'FD']
        freq = 'd'
        htypes = []
        # 逐个生成htype并添加到htypes清单中
        for at in asset_type:
            for htype_name in htype_names:
                try:
                    htype = DataType(name=htype_name, freq=freq, asset_type=at)
                    htypes.append(htype)
                except:
                    print(f'failed to create htype with parameters: {htype_name}, {freq}, {at}')
                    continue
        shares = list_to_str_format(shares)
        print(f'getting data without combination for htypes: \n{[at.__str__() for at in htypes]}')
        htype_ids = [htype.id for htype in htypes]

        dfs = get_history_data_from_source(
                self.ds,
                qt_codes=shares,
                htypes=htypes,
                start=start,
                end=end,
                freq=freq,
        )
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htype_ids)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))

        print(f'got history panel:\n{dfs}')

        # testing getting simple daily data with basic types with combination

        print(f'getting data with combination for htypes: \n{[at.__str__() for at in htypes]}')
        dfs = get_history_data_from_source(
                self.ds,
                htypes=htypes,
                qt_codes=shares,
                start=start,
                end=end,
                freq=freq,
                combine_htype_names=True,
        )
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))

        print(f'got history panel:\n{dfs}')

        # testing getting re-freq hourly data with combination
        # some of the data can be directly get from data source but others should be re-freqed

        start = '20230901'
        end = '20230910'
        freq = 'h'
        htype_names = ['pe', 'close', 'open', 'swing', 'strength']
        # 逐个生成htype并添加到htypes清单中
        h_types = [DataType(name='pe', freq='d', asset_type='E'),
                   DataType(name='close', freq='h', asset_type='E'),
                   DataType(name='open', freq='h', asset_type='E'),
                   DataType(name='swing', freq='d', asset_type='E'),
                   DataType(name='strength', freq='d', asset_type='E'),
                   DataType(name='pe', freq='d', asset_type='IDX'),
                   DataType(name='close', freq='h', asset_type='IDX'),
                   DataType(name='open', freq='h', asset_type='IDX'),
                   DataType(name='close', freq='h', asset_type='FD'),
                   DataType(name='open', freq='h', asset_type='FD'),
                   ]

        print(f'getting re-freq data with combination for htypes: \n{[at.__str__() for at in h_types]}')
        dfs = get_history_data_from_source(
                self.ds,
                htypes=h_types,
                qt_codes=shares,
                start=start,
                end=end,
                freq=freq,
                combine_htype_names=True,
        )
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))

        print(f'got history panel:\n{dfs}')

        print(f'getting data with only row_count parameter without starts or ends')
        htype_ids = [htype.id for htype in h_types]

        dfs = get_history_data_from_source(
                self.ds,
                qt_codes=shares,
                htypes=h_types,
                start='20210203',
                row_count=20,
                freq=freq,
                combine_htype_names=True,
        )
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(f'got history panel: \n{dfs}')
        for df in dfs:
            self.assertLessEqual(len(df), 20)

    def test_get_reference_data(self):
        """ test function get_reference_data()"""
        # test getting simple daily reference data
        htype_names = 'shibor|on, wz_cm, is_trade_day|SSE'
        htype_names = str_to_list(htype_names)
        start = '20210101'
        end = '20210301'
        freq = 'd'
        htypes = []
        # 逐个生成htype并添加到htypes清单中
        for htype_name in htype_names:
            try:
                htype = DataType(name=htype_name, freq=freq)
                htypes.append(htype)
            except:
                print(f'failed to create htype with parameters: {htype_name}, {freq}')
                continue
        print(f'getting simple reference data for htypes: \n{[at.__str__() for at in htypes]}')
        htype_names = [htype.name for htype in htypes]

        ser = get_reference_data_from_source(
                self.ds,
                htypes=htypes,
                start=start,
                end=end,
                freq=freq,
        )
        self.assertIsInstance(ser, dict)
        self.assertEqual(list(ser.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.Series) for item in ser.values()))

        print(f'got history panel:\n{ser}')

        # test getting simple daily reference data with unsymbolized history data
        htype_names = 'shibor|on, wz_cm, close|b-000651.SZ, close-000300.SH'
        htype_names = str_to_list(htype_names)
        start = '20210101'
        end = '20210301'
        freq = 'd'
        asset_types = ['None', 'E', 'IDX']
        htypes = []
        # 逐个生成htype并添加到htypes清单中
        for at in asset_types:
            for htype_name in htype_names:
                try:
                    htype = DataType(name=htype_name, freq=freq, asset_type=at)
                    htypes.append(htype)
                except:
                    print(f'failed to create htype with parameters: {htype_name}, {freq}, {at}')
                    continue
        print(f'getting reference data with unsymbolizer for htypes: \n{[at.__str__() for at in htypes]}')
        htype_names = ['shibor|on', 'wz_cm', 'close|b-000651.SZ', 'close-000300.SH']

        ser = get_reference_data_from_source(
                self.ds,
                htypes=htypes,
                start=start,
                end=end,
                freq=freq,
        )
        self.assertIsInstance(ser, dict)
        self.assertEqual(list(ser.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.Series) for item in ser.values()))

        print(f'got history panel:\n{ser}')

        # test getting simple daily reference data with unsymbolized history data
        start = '20230601'
        end = '20230610'
        freq = '5min'
        htypes = []
        # 逐个生成htype并添加到htypes清单中
        h_types = [DataType(name='shibor|on', freq='d', asset_type='None'),
                   DataType(name='wz_cm', freq='d', asset_type='None'),
                   DataType(name='close|b-000651.SZ', freq='5min', asset_type='E'),
                   DataType(name='close-000300.SH', freq='5min', asset_type='IDX'),
                   ]
        print(f'getting re-freq reference data for htypes: \n{[at.__str__() for at in h_types]}')
        htype_names = ['shibor|on', 'wz_cm', 'close|b-000651.SZ', 'close-000300.SH']

        ser = get_reference_data_from_source(
                self.ds,
                htypes=h_types,
                start=start,
                end=end,
                freq=freq,
        )
        self.assertIsInstance(ser, dict)
        self.assertEqual(list(ser.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.Series) for item in ser.values()))

        print(f'got history panel:\n{ser}')

        print(f'{"=" * 80}\ngetting data with only row_count parameter without starts and ends')
        htype_names = [htype.name for htype in h_types]

        dfs = get_reference_data_from_source(
                self.ds,
                htypes=h_types,
                end=end,
                row_count=20,
                freq=freq,
        )
        print(f'got reference data: \n{dfs}')
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htype_names)
        self.assertTrue(all(isinstance(item, pd.Series) for item in dfs.values() if not item.empty))
        for df in dfs:
            self.assertLessEqual(len(df), 20)

    def test_infer_data_types(self):
        """ test function infer_data_types"""
        # test infer data types with full parameters
        names = ['pe', 'close', 'basic_eps']
        freqs = ['d', 'q']
        assert_types = ['E', 'IDX']
        data_types = infer_data_types(names=names, freqs=freqs, asset_types=assert_types)
        print(f'inferred datatypes with full parameters: \n{data_types}')
        expected_data_types = [
            DataType(name='pe', freq='d', asset_type='E'),
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='E'),
            DataType(name='close', freq='d', asset_type='IDX'),
            DataType(name='basic_eps', freq='q', asset_type='E'),
        ]
        self.assertEqual(len(data_types), 5)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # test infer data types with missing freq parameters
        missing_freqs = ['d']  # 'q' is missing for name basic_eps
        data_types = infer_data_types(names=names, freqs=missing_freqs, asset_types=assert_types)
        print(f'Inferred data types with missing freqs: \n{data_types}')
        expected_data_types = [
            DataType(name='pe', freq='d', asset_type='E'),
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='E'),
            DataType(name='close', freq='d', asset_type='IDX'),
        ]
        self.assertEqual(len(data_types), 4)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # test infer data types with missing asset type parameters
        missing_asset_types = ['IDX']  # 'E' is missing for name basic_eps
        data_types = infer_data_types(names=names, freqs=freqs, asset_types=missing_asset_types)
        print(f'Inferred data types with missing asset types: \n{data_types}')
        expected_data_types = [
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='IDX'),
        ]
        self.assertEqual(len(data_types), 2)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # test infer data types with missing freq but force match freq
        data_types = infer_data_types(names=names, freqs=missing_freqs, asset_types=assert_types, force_match_freq=True)
        print(f'Inferred data types with missing freqs and force match freq: \n{data_types}')
        expected_data_types = [
            DataType(name='pe', freq='d', asset_type='E'),
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='E'),
            DataType(name='close', freq='d', asset_type='IDX'),
            DataType(name='basic_eps', freq='q', asset_type='E'),
        ]
        self.assertEqual(len(data_types), 5)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # test infer data types with missing asset_type but forced match asset type
        data_types = infer_data_types(names=names, freqs=freqs, asset_types=missing_asset_types,
                                      force_match_asset_type=True)
        print(f'Inferred data types with missing asset types and forced match asset type: \n{data_types}')
        expected_data_types = [
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='IDX'),
            DataType(name='basic_eps', freq='q', asset_type='E')
        ]
        self.assertEqual(len(data_types), 3)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # teset infer data types with adj parameter
        data_types = infer_data_types(names=names, freqs=missing_freqs, asset_types=assert_types,
                                      adj='back',
                                      force_match_freq=True)
        print(f'Inferred data types with adj = "b": \n{data_types}')
        expected_data_types = [
            DataType(name='pe', freq='d', asset_type='E'),
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='close|b', freq='d', asset_type='E'),
            DataType(name='basic_eps', freq='q', asset_type='E'),
        ]
        self.assertEqual(len(data_types), 4)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # test infer data types with multiple duplicated cases
        names = ['close', 'close|b', 'pe', 'basic_eps', 'initial_pe', 'ballot', 'exp_date', 'is_trade_day|SSE']
        freqs = ['h', 'd', 'm']
        asset_types = ['E', 'IDX', 'FD']
        data_types = infer_data_types(names=names, freqs=freqs, asset_types=asset_types)
        print(f'Inferred data types with multiple duplicated cases with no forced freq: \n{data_types}')
        expected_data_types = [
            DataType(name='close', freq='h', asset_type='E'),
            DataType(name='close', freq='h', asset_type='IDX'),
            DataType(name='close', freq='h', asset_type='FD'),
            DataType(name='close', freq='d', asset_type='E'),
            DataType(name='close', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='FD'),
            DataType(name='close', freq='m', asset_type='E'),
            DataType(name='close', freq='m', asset_type='IDX'),
            DataType(name='close', freq='m', asset_type='FD'),
            DataType(name='close|b', freq='h', asset_type='E'),
            DataType(name='close|b', freq='h', asset_type='FD'),
            DataType(name='close|b', freq='d', asset_type='E'),
            DataType(name='close|b', freq='d', asset_type='FD'),
            DataType(name='close|b', freq='m', asset_type='E'),
            DataType(name='close|b', freq='m', asset_type='FD'),
            DataType(name='pe', freq='d', asset_type='E'),
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='initial_pe', freq='d', asset_type='E'),
            DataType(name='ballot', freq='d', asset_type='E'),
        ]

        self.assertEqual(len(data_types), 19)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))

        # test infer data types with multiple duplicated cases with forced freq and asset_type
        names = ['close', 'close|b', 'pe', 'basic_eps', 'initial_pe', 'ballot', 'exp_date', 'is_trade_day|SSE', 'name']
        freqs = ['h', 'd', 'm']
        asset_types = ['E', 'IDX', 'FD']
        data_types = infer_data_types(names=names, freqs=freqs, asset_types=asset_types,
                                      force_match_freq=True,
                                      force_match_asset_type=True)
        print(f'Inferred data types with multiple duplicated cases with forced freq and asset_type: \n{data_types}')
        expected_data_types = [
            DataType(name='close', freq='h', asset_type='E'),
            DataType(name='close', freq='h', asset_type='IDX'),
            DataType(name='close', freq='h', asset_type='FD'),
            DataType(name='close', freq='d', asset_type='E'),
            DataType(name='close', freq='d', asset_type='IDX'),
            DataType(name='close', freq='d', asset_type='FD'),
            DataType(name='close', freq='m', asset_type='E'),
            DataType(name='close', freq='m', asset_type='IDX'),
            DataType(name='close', freq='m', asset_type='FD'),
            DataType(name='close|b', freq='h', asset_type='E'),
            DataType(name='close|b', freq='h', asset_type='FD'),
            DataType(name='close|b', freq='d', asset_type='E'),
            DataType(name='close|b', freq='d', asset_type='FD'),
            DataType(name='close|b', freq='m', asset_type='E'),
            DataType(name='close|b', freq='m', asset_type='FD'),
            DataType(name='pe', freq='d', asset_type='E'),
            DataType(name='pe', freq='d', asset_type='IDX'),
            DataType(name='initial_pe', freq='d', asset_type='E'),
            DataType(name='ballot', freq='d', asset_type='E'),
            DataType(name='basic_eps', freq='q', asset_type='E'),
            DataType(name='exp_date', freq='None', asset_type='IDX'),
            DataType(name='is_trade_day|SSE', freq='d', asset_type='None'),
            DataType(name='name', freq='None', asset_type='FT')
        ]
        self.assertEqual(len(data_types), 23)
        self.assertTrue(all(dt in expected_data_types for dt in data_types))
        self.assertTrue(all(dt in data_types for dt in expected_data_types))


if __name__ == '__main__':
    unittest.main()