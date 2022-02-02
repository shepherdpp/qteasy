# coding=utf-8
# database.py

# ======================================
# This file contains DataSource class, that
# maintains and manages local historical
# data in a specific folder, and provide
# seamless historical data operation for
# qteasy.
# ======================================

import pymysql
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from os import path
from qteasy import QT_ROOT_PATH

from .history import stack_dataframes, get_price_type_raw_data, get_financial_report_type_raw_data
from .utilfuncs import str_to_list, progress_bar

from ._arg_validators import PRICE_TYPE_DATA
from ._arg_validators import BALANCE_TYPE_DATA, CASHFLOW_TYPE_DATA
from ._arg_validators import INDICATOR_TYPE_DATA

LOCAL_DATA_FOLDER = 'qteasy/data/'
LOCAL_DATA_FILE_EXT = '.dat'

""" 
这里定义AVAILABLE_TABLES 以及 TABLE_STRUCTURES
"""
DATA_MAPPING_TABLE = []

# 定义Table structure，定义所有数据表的主键和内容
AVAILABLE_TABLES = {

    'trade_calendar':   {'columns':     ['exchange', 'start_date', 'end_date', 'is_open'],
                         'dtypes':      ['str', 'str', 'str', 'str'],
                         'remarks':     ['交易所:SSE上交所,SZSE深交所,CFFEX中金所,SHFE上期所,CZCE郑商所,DCE大商所,INE上能源',
                                         '开始日期 （格式:YYYYMMDD）',
                                         '结束日期',
                                         '是否交易 "0"休市 "1"交易'],
                         'prime_keys':  [0]},

    'stock_basic':      {'columns':     ['ts_code', 'symbol', 'name', 'area', 'industry', 'fullname',
                                         'enname', 'cnspell', 'market', 'exchange', 'curr_type',
                                         'list_status', 'list_date', 'delist_date', 'is_hs'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str',
                                         'str', 'str', 'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['TS代码', '股票代码', '股票名称', '地域', '所属行业', '股票全称',
                                         '英文全称', '拼音缩写', '市场类型（主板/创业板/科创板/CDR）',
                                         '交易所代码', '交易货币', '上市状态 L上市 D退市 P暂停上市',
                                         '上市日期', '退市日期', '是否沪深港通标的，N否 H沪股通 S深股通'],
                         'prime_keys':  [0]},

    'previous_names':   {'columns':     ['ts_code', 'name', 'start_date', 'end_date', 'ann_date', 'change_reason'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['TS代码', '证券名称', '开始日期', '结束日期', '公告日期', '变更原因'],
                         'prime_keys':  [0]},

    'index_basic':      {'columns':     ['ts_code', 'name', 'fullname', 'market', 'publisher', 'index_type',
                                         'category', 'base_date', 'base_point', 'list_date', 'weight_rule',
                                         'desc', 'exp_date'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'float', 'str',
                                         'str', 'str', 'str'],
                         'remarks':     ['TS代码', '简称', '指数全称', '市场', '发布方', '指数风格', '指数类别', '基期',
                                         '基点', '发布日期', '加权方式', '描述', '终止日期'],
                         'prime_keys':  [0]},

    'fund_basic':       {'columns':     ['ts_code', 'name', 'management', 'custodian', 'fund_type', 'found_date',
                                         'due_date', 'list_date', 'issue_date', 'delist_date', 'issue_amount',
                                         'm_fee', 'c_fee', 'duration_year', 'p_value', 'min_amount', 'exp_return',
                                         'benchmark', 'status', 'invest_type', 'type', 'trustee', 'purc_startdate',
                                         'redm_startdate', 'market'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'str', 'str', 'str',
                                         'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['基金代码', '简称', '管理人', '托管人', '投资类型', '成立日期', '到期日期', '上市时间',
                                         '发行日期', '退市日期', '发行份额(亿)', '管理费', '托管费', '存续期', '面值',
                                         '起点金额(万元)', '预期收益率', '业绩比较基准', '存续状态D摘牌 I发行 L已上市',
                                         '投资风格', '基金类型', '受托人', '日常申购起始日', '日常赎回起始日', 'E场内O场外'],
                         'prime_keys':  [0]},

    'future_basic':     {'columns':     ['ts_code', 'symbol', 'exchange', 'name', 'fut_code', 'multiplier',
                                         'trade_unit', 'per_unit', 'quote_unit', 'quote_unit_desc', 'd_mode_desc',
                                         'list_date', 'delist_date', 'd_month', 'last_ddate', 'trade_time_desc'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'float', 'str', 'float', 'str', 'str',
                                         'str', 'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['合约代码', '交易标识', '交易市场', '中文简称', '合约产品代码', '合约乘数',
                                         '交易计量单位', '交易单位(每手)', '报价单位', '最小报价单位说明', '交割方式说明',
                                         '上市日期', '最后交易日期', '交割月份', '最后交割日', '交易时间说明'],
                         'prime_keys':  [0]},

    'opt_basic':        {'columns':     ['ts_code', 'exchange', 'name', 'per_unit', 'opt_code', 'opt_type', 'call_put',
                                         'exercise_type', 'exercise_price', 's_month', 'maturity_date', 'list_price',
                                         'list_date', 'delist_date', 'last_edate', 'last_ddate', 'quote_unit',
                                         'min_price_chg'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'float', 'str', 'str',
                                         'float', 'str', 'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['TS代码', '交易市场', '合约名称', '合约单位', '标准合约代码', '合约类型', '期权类型',
                                         '行权方式', '行权价格', '结算月', '到期日', '挂牌基准价', '开始交易日期',
                                         '最后交易日期', '最后行权日期', '最后交割日期', '报价单位', '最小价格波幅'],
                         'prime_keys':  [0]},

    # 下面的stock_bars表适用于stock_1min / stock_5min / stock_30min / stock_hourly /
    # stock_daily / stock_weekly / stock_monthly / index_daily / index_weekly /
    # index_monthly / fund_daily 等数据表
    'stock_bars':       {'columns':     ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close',
                                         'change', 'pct_chg', 'vol', 'amount'],
                         'dtypes':      ['str', 'str', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float'],
                         'remarks':     ['股票代码', '交易日期', '开盘价', '最高价', '最低价', '收盘价', '昨收价', '涨跌额',
                                         '涨跌幅', '成交量 （手）', '成交额 （千元）'],
                         'prime_keys':  [0]},

    # 以下adj_factors表结构可以同时用于stock_adj_factors / func_adj_factors两张表
    'adj_factors':      {'columns':     ['ts_code', 'trade_date', 'adj_factor'],
                         'dtypes':      ['str', 'str', 'float'],
                         'remarks':     ['股票/基金代码', '交易日期', '复权因子'],
                         'prime_keys':  [0]},

    'fund_nav':         {'columns':     ['ts_code', 'ann_date', 'nav_date', 'unit_nav', 'accum_nav', 'accum_div',
                                         'net_asset', 'total_netasset', 'adj_nav'],
                         'dtypes':      ['str', 'str', 'str', 'float', 'float', 'float', 'float', 'float', 'float'],
                         'remarks':     ['TS代码', '公告日期', '净值日期', '单位净值', '累计净值', '累计分红', '资产净值',
                                         '合计资产净值', '复权单位净值'],
                         'prime_keys':  [0]},

    'fund_share':       {'columns':     ['ts_code', 'trade_date', 'fd_share'],
                         'dtypes':      ['str', 'str', 'float'],
                         'remarks':     ['基金代码', '变动日期，格式YYYYMMDD', '基金份额（万）'],
                         'prime_keys':  [0]},

    'fund_manager':     {'columns':     ['ts_code', 'ann_date', 'name', 'gender', 'birth_year', 'edu', 'nationality',
                                         'begin_date', 'end_date', 'resume'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['基金代码', '公告日期', '基金经理姓名', '性别', '出生年份', '学历', '国籍', '任职日期',
                                         '离任日期', '简历'],
                         'prime_keys':  [0]},

    'future_daily':     {'columns':     ['ts_code', 'trade_date', 'pre_close', 'pre_settle', 'open', 'high', 'low',
                                         'close', 'settle', 'change1', 'change2', 'vol', 'amount', 'oi', 'oi_chg',
                                         'delv_settle'],
                         'dtypes':      ['str', 'str', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float'],
                         'remarks':     ['TS合约代码', '交易日期', '昨收盘价', '昨结算价', '开盘价', '最高价', '最低价',
                                         '收盘价', '结算价', '涨跌1 收盘价-昨结算价', '涨跌2 结算价-昨结算价', '成交量(手)',
                                         '成交金额(万元)', '持仓量(手)', '持仓量变化', '交割结算价'],
                         'prime_keys':  [0]},

    'stock_indicator':  {'columns':     ['ts_code', 'trade_date', 'close', 'turnover_rate', 'turnover_rate_f',
                                         'volume_ratio', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm',
                                         'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv'],
                         'dtypes':      ['str', 'str', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float'],
                         'remarks':     ['TS股票代码', '交易日期', '当日收盘价', '换手率（%）', '换手率（自由流通股）', '量比',
                                         '市盈率（总市值/净利润， 亏损的PE为空）', '市盈率（TTM，亏损的PE为空）',
                                         '市净率（总市值/净资产）', '市销率', '市销率（TTM）', '股息率 （%）',
                                         '股息率（TTM）（%）', '总股本 （万股）', '流通股本 （万股）', '自由流通股本 （万）',
                                         '总市值 （万元）', '流通市值（万元）'],
                         'prime_keys':  [0]},

    'stock_indicator2': {'columns':     ['ts_code', 'trade_date', 'name', 'pct_change', 'close', 'change', 'open',
                                         'high', 'low', 'pre_close', 'vol_ratio', 'turn_over', 'swing', 'vol',
                                         'amount', 'selling', 'buying', 'total_share', 'float_share', 'pe', 'industry',
                                         'area', 'float_mv', 'total_mv', 'avg_price', 'strength', 'activity',
                                         'avg_turnover', 'attack', 'interval_3', 'interval_6'],
                         'dtypes':      ['str', 'str', 'str', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'str', 'str', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float'],
                         'remarks':     ['股票代码', '交易日期', '股票名称', '涨跌幅', '收盘价', '涨跌额', '开盘价', '最高价',
                                         '最低价', '昨收价', '量比', '换手率', '振幅', '成交量', '成交额', '内盘（主动卖，手）',
                                         '外盘（主动买， 手）', '总股本(亿)', '流通股本(亿)', '市盈(动)', '所属行业', '所属地域',
                                         '流通市值', '总市值', '平均价', '强弱度(%)', '活跃度(%)', '笔换手', '攻击波(%)',
                                         '近3月涨幅', '近6月涨幅'],
                         'prime_keys':  [0]},

    'index_indicator':  {'columns':     ['ts_code', 'trade_date', 'total_mv', 'float_mv', 'total_share', 'float_share',
                                         'free_share', 'turnover_rate', 'turnover_rate_f', 'pe', 'pe_ttm', 'pb'],
                         'dtypes':      ['str', 'str', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float'],
                         'remarks':     ['TS代码', '交易日期', '当日总市值（元）', '当日流通市值（元）', '当日总股本（股）',
                                         '当日流通股本（股）', '当日自由流通股本（股）', '换手率', '换手率(基于自由流通股本)',
                                         '市盈率', '市盈率TTM', '市净率'],
                         'prime_keys':  [0]},

    'index_weight':     {'columns':     ['index_code', 'con_code', 'trade_date', 'weight'],
                         'dtypes':      ['str', 'str', 'str', 'float'],
                         'remarks':     ['指数代码', '成分代码', '交易日期', '权重'],
                         'prime_keys':  [0]},

    'income':           {'columns':     ['ts_code', 'ann_date', 'f_ann_date', 'end_date', 'report_type', 'comp_type',
                                         'end_type', 'basic_eps', 'diluted_eps', 'total_revenue', 'revenue',
                                         'int_income', 'prem_earned', 'comm_income', 'n_commis_income', 'n_oth_income',
                                         'n_oth_b_income', 'prem_income', 'out_prem', 'une_prem_reser', 'reins_income',
                                         'n_sec_tb_income', 'n_sec_uw_income', 'n_asset_mg_income', 'oth_b_income',
                                         'fv_value_chg_gain', 'invest_income', 'ass_invest_income', 'forex_gain',
                                         'total_cogs', 'oper_cost', 'int_exp', 'comm_exp', 'biz_tax_surchg', 'sell_exp',
                                         'admin_exp', 'fin_exp', 'assets_impair_loss', 'prem_refund', 'compens_payout',
                                         'reser_insur_liab', 'div_payt', 'reins_exp', 'oper_exp', 'compens_payout_refu',
                                         'insur_reser_refu', 'reins_cost_refund', 'other_bus_cost', 'operate_profit',
                                         'non_oper_income', 'non_oper_exp', 'nca_disploss', 'total_profit',
                                         'income_tax', 'n_income', 'n_income_attr_p', 'minority_gain',
                                         'oth_compr_income', 't_compr_income', 'compr_inc_attr_p', 'compr_inc_attr_m_s',
                                         'ebit', 'ebitda', 'insurance_exp', 'undist_profit', 'distable_profit',
                                         'rd_exp', 'fin_exp_int_exp', 'fin_exp_int_inc', 'transfer_surplus_rese',
                                         'transfer_housing_imprest', 'transfer_oth', 'adj_lossgain',
                                         'withdra_legal_surplus', 'withdra_legal_pubfund', 'withdra_biz_devfund',
                                         'withdra_rese_fund', 'withdra_oth_ersu', 'workers_welfare',
                                         'distr_profit_shrhder', 'prfshare_payable_dvd', 'comshare_payable_dvd',
                                         'capit_comstock_div', 'net_after_nr_lp_correct', 'credit_impa_loss',
                                         'net_expo_hedging_benefits', 'oth_impair_loss_assets', 'total_opcost',
                                         'amodcost_fin_assets', 'oth_income', 'asset_disp_income',
                                         'continued_net_profit', 'end_net_profit', 'update_flag'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'str'],
                         'remarks':     ['TS代码', '公告日期', '实际公告日期', '报告期', '报告类型 见底部表',
                                         '公司类型(1一般工商业2银行3保险4证券)', '报告期类型', '基本每股收益', '稀释每股收益',
                                         '营业总收入', '营业收入', '利息收入', '已赚保费', '手续费及佣金收入', '手续费及佣金净收入',
                                         '其他经营净收益', '加:其他业务净收益', '保险业务收入', '减:分出保费',
                                         '提取未到期责任准备金', '其中:分保费收入', '代理买卖证券业务净收入', '证券承销业务净收入',
                                         '受托客户资产管理业务净收入', '其他业务收入', '加:公允价值变动净收益', '加:投资净收益',
                                         '其中:对联营企业和合营企业的投资收益', '加:汇兑净收益', '营业总成本', '减:营业成本',
                                         '减:利息支出', '减:手续费及佣金支出', '减:营业税金及附加', '减:销售费用', '减:管理费用',
                                         '减:财务费用', '减:资产减值损失', '退保金', '赔付总支出', '提取保险责任准备金',
                                         '保户红利支出', '分保费用', '营业支出', '减:摊回赔付支出', '减:摊回保险责任准备金',
                                         '减:摊回分保费用', '其他业务成本', '营业利润', '加:营业外收入', '减:营业外支出',
                                         '其中:减:非流动资产处置净损失', '利润总额', '所得税费用', '净利润(含少数股东损益)',
                                         '净利润(不含少数股东损益)', '少数股东损益', '其他综合收益', '综合收益总额',
                                         '归属于母公司(或股东)的综合收益总额', '归属于少数股东的综合收益总额', '息税前利润',
                                         '息税折旧摊销前利润', '保险业务支出', '年初未分配利润', '可分配利润', '研发费用',
                                         '财务费用:利息费用', '财务费用:利息收入', '盈余公积转入', '住房周转金转入', '其他转入',
                                         '调整以前年度损益', '提取法定盈余公积', '提取法定公益金', '提取企业发展基金',
                                         '提取储备基金', '提取任意盈余公积金', '职工奖金福利', '可供股东分配的利润',
                                         '应付优先股股利', '应付普通股股利', '转作股本的普通股股利',
                                         '扣除非经常性损益后的净利润（更正前）', '信用减值损失', '净敞口套期收益',
                                         '其他资产减值损失', '营业总成本（二）', '以摊余成本计量的金融资产终止确认收益',
                                         '其他收益', '资产处置收益', '持续经营净利润', '终止经营净利润', '更新标识'],
                         'prime_keys':  [0, 1]},

    'balance':          {'columns':     ['ts_code', 'ann_date', 'f_ann_date', 'end_date', 'report_type', 'comp_type',
                                         'end_type', 'total_share', 'cap_rese', 'undistr_porfit', 'surplus_rese',
                                         'special_rese', 'money_cap', 'trad_asset', 'notes_receiv', 'accounts_receiv',
                                         'oth_receiv', 'prepayment', 'div_receiv', 'int_receiv', 'inventories',
                                         'amor_exp', 'nca_within_1y', 'sett_rsrv', 'loanto_oth_bank_fi',
                                         'premium_receiv', 'reinsur_receiv', 'reinsur_res_receiv', 'pur_resale_fa',
                                         'oth_cur_assets', 'total_cur_assets', 'fa_avail_for_sale', 'htm_invest',
                                         'lt_eqt_invest', 'invest_real_estate', 'time_deposits', 'oth_assets', 'lt_rec',
                                         'fix_assets', 'cip', 'const_materials', 'fixed_assets_disp',
                                         'produc_bio_assets', 'oil_and_gas_assets', 'intan_assets', 'r_and_d',
                                         'goodwill', 'lt_amor_exp', 'defer_tax_assets', 'decr_in_disbur', 'oth_nca',
                                         'total_nca', 'cash_reser_cb', 'depos_in_oth_bfi', 'prec_metals',
                                         'deriv_assets', 'rr_reins_une_prem', 'rr_reins_outstd_cla',
                                         'rr_reins_lins_liab', 'rr_reins_lthins_liab', 'refund_depos',
                                         'ph_pledge_loans', 'refund_cap_depos', 'indep_acct_assets', 'client_depos',
                                         'client_prov', 'transac_seat_fee', 'invest_as_receiv', 'total_assets',
                                         'lt_borr', 'st_borr', 'cb_borr', 'depos_ib_deposits', 'loan_oth_bank',
                                         'trading_fl', 'notes_payable', 'acct_payable', 'adv_receipts',
                                         'sold_for_repur_fa', 'comm_payable', 'payroll_payable', 'taxes_payable',
                                         'int_payable', 'div_payable', 'oth_payable', 'acc_exp', 'deferred_inc',
                                         'st_bonds_payable', 'payable_to_reinsurer', 'rsrv_insur_cont',
                                         'acting_trading_sec', 'acting_uw_sec', 'non_cur_liab_due_1y', 'oth_cur_liab',
                                         'total_cur_liab', 'bond_payable', 'lt_payable', 'specific_payables',
                                         'estimated_liab', 'defer_tax_liab', 'defer_inc_non_cur_liab', 'oth_ncl',
                                         'total_ncl', 'depos_oth_bfi', 'deriv_liab', 'depos', 'agency_bus_liab',
                                         'oth_liab', 'prem_receiv_adva', 'depos_received', 'ph_invest',
                                         'reser_une_prem', 'reser_outstd_claims', 'reser_lins_liab',
                                         'reser_lthins_liab', 'indept_acc_liab', 'pledge_borr', 'indem_payable',
                                         'policy_div_payable', 'total_liab', 'treasury_share', 'ordin_risk_reser',
                                         'forex_differ', 'invest_loss_unconf', 'minority_int',
                                         'total_hldr_eqy_exc_min_int', 'total_hldr_eqy_inc_min_int',
                                         'total_liab_hldr_eqy', 'lt_payroll_payable', 'oth_comp_income',
                                         'oth_eqt_tools', 'oth_eqt_tools_p_shr', 'lending_funds', 'acc_receivable',
                                         'st_fin_payable', 'payables', 'hfs_assets', 'hfs_sales', 'cost_fin_assets',
                                         'fair_value_fin_assets', 'cip_total', 'oth_pay_total', 'long_pay_total',
                                         'debt_invest', 'oth_debt_invest', 'oth_eq_invest', 'oth_illiq_fin_assets',
                                         'oth_eq_ppbond', 'receiv_financing', 'use_right_assets', 'lease_liab',
                                         'contract_assets', 'contract_liab', 'accounts_receiv_bill', 'accounts_pay',
                                         'oth_rcv_total', 'fix_assets_total', 'update_flag'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'str'],
                         'remarks':     ['TS股票代码', '公告日期', '实际公告日期', '报告期', '报表类型', '公司类型', '报告期类型',
                                         '期末总股本', '资本公积金', '未分配利润', '盈余公积金', '专项储备', '货币资金',
                                         '交易性金融资产', '应收票据', '应收账款', '其他应收款', '预付款项', '应收股利',
                                         '应收利息', '存货', '长期待摊费用', '一年内到期的非流动资产', '结算备付金', '拆出资金',
                                         '应收保费', '应收分保账款', '应收分保合同准备金', '买入返售金融资产', '其他流动资产',
                                         '流动资产合计', '可供出售金融资产', '持有至到期投资', '长期股权投资', '投资性房地产',
                                         '定期存款', '其他资产', '长期应收款', '固定资产', '在建工程', '工程物资', '固定资产清理',
                                         '生产性生物资产', '油气资产', '无形资产', '研发支出', '商誉', '长期待摊费用',
                                         '递延所得税资产', '发放贷款及垫款', '其他非流动资产', '非流动资产合计',
                                         '现金及存放中央银行款项', '存放同业和其它金融机构款项', '贵金属', '衍生金融资产',
                                         '应收分保未到期责任准备金', '应收分保未决赔款准备金', '应收分保寿险责任准备金',
                                         '应收分保长期健康险责任准备金', '存出保证金', '保户质押贷款', '存出资本保证金',
                                         '独立账户资产', '其中：客户资金存款', '其中：客户备付金', '其中:交易席位费',
                                         '应收款项类投资', '资产总计', '长期借款', '短期借款', '向中央银行借款',
                                         '吸收存款及同业存放', '拆入资金', '交易性金融负债', '应付票据', '应付账款', '预收款项',
                                         '卖出回购金融资产款', '应付手续费及佣金', '应付职工薪酬', '应交税费', '应付利息',
                                         '应付股利', '其他应付款', '预提费用', '递延收益', '应付短期债券', '应付分保账款',
                                         '保险合同准备金', '代理买卖证券款', '代理承销证券款', '一年内到期的非流动负债',
                                         '其他流动负债', '流动负债合计', '应付债券', '长期应付款', '专项应付款', '预计负债',
                                         '递延所得税负债', '递延收益-非流动负债', '其他非流动负债', '非流动负债合计',
                                         '同业和其它金融机构存放款项', '衍生金融负债', '吸收存款', '代理业务负债', '其他负债',
                                         '预收保费', '存入保证金', '保户储金及投资款', '未到期责任准备金', '未决赔款准备金',
                                         '寿险责任准备金', '长期健康险责任准备金', '独立账户负债', '其中:质押借款', '应付赔付款',
                                         '应付保单红利', '负债合计', '减:库存股', '一般风险准备', '外币报表折算差额',
                                         '未确认的投资损失', '少数股东权益', '股东权益合计(不含少数股东权益)',
                                         '股东权益合计(含少数股东权益)', '负债及股东权益总计', '长期应付职工薪酬', '其他综合收益',
                                         '其他权益工具', '其他权益工具(优先股)', '融出资金', '应收款项', '应付短期融资款',
                                         '应付款项', '持有待售的资产', '持有待售的负债', '以摊余成本计量的金融资产',
                                         '以公允价值计量且其变动计入其他综合收益的金融资产', '在建工程(合计)(元)',
                                         '其他应付款(合计)(元)', '长期应付款(合计)(元)', '债权投资(元)', '其他债权投资(元)',
                                         '其他权益工具投资(元)', '其他非流动金融资产(元)', '其他权益工具:永续债(元)',
                                         '应收款项融资', '使用权资产', '租赁负债', '合同资产', '合同负债', '应收票据及应收账款',
                                         '应付票据及应付账款', '其他应收款(合计)（元）', '固定资产(合计)(元)', '更新标识'],
                         'prime_keys':  [0, 1]},

    'cashflow':          {'columns':     ['ts_code', 'ann_date', 'f_ann_date', 'end_date', 'comp_type', 'report_type',
                                         'end_type', 'net_profit', 'finan_exp', 'c_fr_sale_sg', 'recp_tax_rends',
                                         'n_depos_incr_fi', 'n_incr_loans_cb', 'n_inc_borr_oth_fi',
                                         'prem_fr_orig_contr', 'n_incr_insured_dep', 'n_reinsur_prem',
                                         'n_incr_disp_tfa', 'ifc_cash_incr', 'n_incr_disp_faas',
                                         'n_incr_loans_oth_bank', 'n_cap_incr_repur', 'c_fr_oth_operate_a',
                                         'c_inf_fr_operate_a', 'c_paid_goods_s', 'c_paid_to_for_empl',
                                         'c_paid_for_taxes', 'n_incr_clt_loan_adv', 'n_incr_dep_cbob',
                                         'c_pay_claims_orig_inco', 'pay_handling_chrg', 'pay_comm_insur_plcy',
                                         'oth_cash_pay_oper_act', 'st_cash_out_act', 'n_cashflow_act',
                                         'oth_recp_ral_inv_act', 'c_disp_withdrwl_invest', 'c_recp_return_invest',
                                         'n_recp_disp_fiolta', 'n_recp_disp_sobu', 'stot_inflows_inv_act',
                                         'c_pay_acq_const_fiolta', 'c_paid_invest', 'n_disp_subs_oth_biz',
                                         'oth_pay_ral_inv_act', 'n_incr_pledge_loan', 'stot_out_inv_act',
                                         'n_cashflow_inv_act', 'c_recp_borrow', 'proc_issue_bonds',
                                         'oth_cash_recp_ral_fnc_act', 'stot_cash_in_fnc_act', 'free_cashflow',
                                         'c_prepay_amt_borr', 'c_pay_dist_dpcp_int_exp', 'incl_dvd_profit_paid_sc_ms',
                                         'oth_cashpay_ral_fnc_act', 'stot_cashout_fnc_act', 'n_cash_flows_fnc_act',
                                         'eff_fx_flu_cash', 'n_incr_cash_cash_equ', 'c_cash_equ_beg_period',
                                         'c_cash_equ_end_period', 'c_recp_cap_contrib', 'incl_cash_rec_saims',
                                         'uncon_invest_loss', 'prov_depr_assets', 'depr_fa_coga_dpba',
                                         'amort_intang_assets', 'lt_amort_deferred_exp', 'decr_deferred_exp',
                                         'incr_acc_exp', 'loss_disp_fiolta', 'loss_scr_fa', 'loss_fv_chg',
                                         'invest_loss', 'decr_def_inc_tax_assets', 'incr_def_inc_tax_liab',
                                         'decr_inventories', 'decr_oper_payable', 'incr_oper_payable', 'others',
                                         'im_net_cashflow_oper_act', 'conv_debt_into_cap',
                                         'conv_copbonds_due_within_1y', 'fa_fnc_leases', 'im_n_incr_cash_equ',
                                         'net_dism_capital_add', 'net_cash_rece_sec', 'credit_impa_loss',
                                         'use_right_asset_dep', 'oth_loss_asset', 'end_bal_cash', 'beg_bal_cash',
                                         'end_bal_cash_equ', 'beg_bal_cash_equ', 'update_flag'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'str'],
                         'remarks':     ['TS股票代码', '公告日期', '实际公告日期', '报告期', '公司类型', '报表类型', '报告期类型',
                                         '净利润', '财务费用', '销售商品、提供劳务收到的现金', '收到的税费返还',
                                         '客户存款和同业存放款项净增加额', '向中央银行借款净增加额', '向其他金融机构拆入资金净增加额',
                                         '收到原保险合同保费取得的现金', '保户储金净增加额', '收到再保业务现金净额',
                                         '处置交易性金融资产净增加额', '收取利息和手续费净增加额', '处置可供出售金融资产净增加额',
                                         '拆入资金净增加额', '回购业务资金净增加额', '收到其他与经营活动有关的现金',
                                         '经营活动现金流入小计', '购买商品、接受劳务支付的现金', '支付给职工以及为职工支付的现金',
                                         '支付的各项税费', '客户贷款及垫款净增加额', '存放央行和同业款项净增加额',
                                         '支付原保险合同赔付款项的现金', '支付手续费的现金', '支付保单红利的现金',
                                         '支付其他与经营活动有关的现金', '经营活动现金流出小计', '经营活动产生的现金流量净额',
                                         '收到其他与投资活动有关的现金', '收回投资收到的现金', '取得投资收益收到的现金',
                                         '处置固定资产、无形资产和其他长期资产收回的现金净额',
                                         '处置子公司及其他营业单位收到的现金净额', '投资活动现金流入小计',
                                         '购建固定资产、无形资产和其他长期资产支付的现金', '投资支付的现金',
                                         '取得子公司及其他营业单位支付的现金净额', '支付其他与投资活动有关的现金',
                                         '质押贷款净增加额', '投资活动现金流出小计', '投资活动产生的现金流量净额',
                                         '取得借款收到的现金', '发行债券收到的现金', '收到其他与筹资活动有关的现金',
                                         '筹资活动现金流入小计', '企业自由现金流量', '偿还债务支付的现金',
                                         '分配股利、利润或偿付利息支付的现金', '其中:子公司支付给少数股东的股利、利润',
                                         '支付其他与筹资活动有关的现金', '筹资活动现金流出小计', '筹资活动产生的现金流量净额',
                                         '汇率变动对现金的影响', '现金及现金等价物净增加额', '期初现金及现金等价物余额',
                                         '期末现金及现金等价物余额', '吸收投资收到的现金', '其中:子公司吸收少数股东投资收到的现金',
                                         '未确认投资损失', '加:资产减值准备', '固定资产折旧、油气资产折耗、生产性生物资产折旧',
                                         '无形资产摊销', '长期待摊费用摊销', '待摊费用减少', '预提费用增加',
                                         '处置固定、无形资产和其他长期资产的损失', '固定资产报废损失', '公允价值变动损失',
                                         '投资损失', '递延所得税资产减少', '递延所得税负债增加', '存货的减少',
                                         '经营性应收项目的减少', '经营性应付项目的增加', '其他',
                                         '经营活动产生的现金流量净额(间接法)', '债务转为资本', '一年内到期的可转换公司债券',
                                         '融资租入固定资产', '现金及现金等价物净增加额(间接法)', '拆出资金净增加额',
                                         '代理买卖证券收到的现金净额(元)', '信用减值损失', '使用权资产折旧', '其他资产减值损失',
                                         '现金的期末余额', '减:现金的期初余额', '加:现金等价物的期末余额',
                                         '减:现金等价物的期初余额', '更新标志(1最新）'],
                         'prime_keys':  [0, 1]},

    'financial':         {'columns':     ['ts_code', 'ann_date', 'end_date', 'eps', 'dt_eps', 'total_revenue_ps',
                                         'revenue_ps', 'capital_rese_ps', 'surplus_rese_ps', 'undist_profit_ps',
                                         'extra_item', 'profit_dedt', 'gross_margin', 'current_ratio', 'quick_ratio',
                                         'cash_ratio', 'invturn_days', 'arturn_days', 'inv_turn', 'ar_turn', 'ca_turn',
                                         'fa_turn', 'assets_turn', 'op_income', 'valuechange_income', 'interst_income',
                                         'daa', 'ebit', 'ebitda', 'fcff', 'fcfe', 'current_exint', 'noncurrent_exint',
                                         'interestdebt', 'netdebt', 'tangible_asset', 'working_capital',
                                         'networking_capital', 'invest_capital', 'retained_earnings', 'diluted2_eps',
                                         'bps', 'ocfps', 'retainedps', 'cfps', 'ebit_ps', 'fcff_ps', 'fcfe_ps',
                                         'netprofit_margin', 'grossprofit_margin', 'cogs_of_sales', 'expense_of_sales',
                                         'profit_to_gr', 'saleexp_to_gr', 'adminexp_of_gr', 'finaexp_of_gr',
                                         'impai_ttm', 'gc_of_gr', 'op_of_gr', 'ebit_of_gr', 'roe', 'roe_waa', 'roe_dt',
                                         'roa', 'npta', 'roic', 'roe_yearly', 'roa2_yearly', 'roe_avg',
                                         'opincome_of_ebt', 'investincome_of_ebt', 'n_op_profit_of_ebt', 'tax_to_ebt',
                                         'dtprofit_to_profit', 'salescash_to_or', 'ocf_to_or', 'ocf_to_opincome',
                                         'capitalized_to_da', 'debt_to_assets', 'assets_to_eqt', 'dp_assets_to_eqt',
                                         'ca_to_assets', 'nca_to_assets', 'tbassets_to_totalassets', 'int_to_talcap',
                                         'eqt_to_talcapital', 'currentdebt_to_debt', 'longdeb_to_debt',
                                         'ocf_to_shortdebt', 'debt_to_eqt', 'eqt_to_debt', 'eqt_to_interestdebt',
                                         'tangibleasset_to_debt', 'tangasset_to_intdebt', 'tangibleasset_to_netdebt',
                                         'ocf_to_debt', 'ocf_to_interestdebt', 'ocf_to_netdebt', 'ebit_to_interest',
                                         'longdebt_to_workingcapital', 'ebitda_to_debt', 'turn_days', 'roa_yearly',
                                         'roa_dp', 'fixed_assets', 'profit_prefin_exp', 'non_op_profit', 'op_to_ebt',
                                         'nop_to_ebt', 'ocf_to_profit', 'cash_to_liqdebt',
                                         'cash_to_liqdebt_withinterest', 'op_to_liqdebt', 'op_to_debt', 'roic_yearly',
                                         'total_fa_trun', 'profit_to_op', 'q_opincome', 'q_investincome', 'q_dtprofit',
                                         'q_eps', 'q_netprofit_margin', 'q_gsprofit_margin', 'q_exp_to_sales',
                                         'q_profit_to_gr', 'q_saleexp_to_gr', 'q_adminexp_to_gr', 'q_finaexp_to_gr',
                                         'q_impair_to_gr_ttm', 'q_gc_to_gr', 'q_op_to_gr', 'q_roe', 'q_dt_roe',
                                         'q_npta', 'q_opincome_to_ebt', 'q_investincome_to_ebt', 'q_dtprofit_to_profit',
                                         'q_salescash_to_or', 'q_ocf_to_sales', 'q_ocf_to_or', 'basic_eps_yoy',
                                         'dt_eps_yoy', 'cfps_yoy', 'op_yoy', 'ebt_yoy', 'netprofit_yoy',
                                         'dt_netprofit_yoy', 'ocf_yoy', 'roe_yoy', 'bps_yoy', 'assets_yoy', 'eqt_yoy',
                                         'tr_yoy', 'or_yoy', 'q_gr_yoy', 'q_gr_qoq', 'q_sales_yoy', 'q_sales_qoq',
                                         'q_op_yoy', 'q_op_qoq', 'q_profit_yoy', 'q_profit_qoq', 'q_netprofit_yoy',
                                         'q_netprofit_qoq', 'equity_yoy', 'rd_exp', 'update_flag'],
                         'dtypes':      ['str', 'str', 'str', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'str'],
                         'remarks':     ['TS代码', '公告日期', '报告期', '基本每股收益', '稀释每股收益', '每股营业总收入',
                                         '每股营业收入', '每股资本公积', '每股盈余公积', '每股未分配利润', '非经常性损益',
                                         '扣除非经常性损益后的净利润（扣非净利润）', '毛利', '流动比率', '速动比率', '保守速动比率',
                                         '存货周转天数', '应收账款周转天数', '存货周转率', '应收账款周转率', '流动资产周转率',
                                         '固定资产周转率', '总资产周转率', '经营活动净收益', '价值变动净收益', '利息费用',
                                         '折旧与摊销', '息税前利润', '息税折旧摊销前利润', '企业自由现金流量', '股权自由现金流量',
                                         '无息流动负债', '无息非流动负债', '带息债务', '净债务', '有形资产', '营运资金',
                                         '营运流动资本', '全部投入资本', '留存收益', '期末摊薄每股收益', '每股净资产',
                                         '每股经营活动产生的现金流量净额', '每股留存收益', '每股现金流量净额', '每股息税前利润',
                                         '每股企业自由现金流量', '每股股东自由现金流量', '销售净利率', '销售毛利率', '销售成本率',
                                         '销售期间费用率', '净利润/营业总收入', '销售费用/营业总收入', '管理费用/营业总收入',
                                         '财务费用/营业总收入', '资产减值损失/营业总收入', '营业总成本/营业总收入',
                                         '营业利润/营业总收入', '息税前利润/营业总收入', '净资产收益率', '加权平均净资产收益率',
                                         '净资产收益率(扣除非经常损益)', '总资产报酬率', '总资产净利润', '投入资本回报率',
                                         '年化净资产收益率', '年化总资产报酬率', '平均净资产收益率(增发条件)',
                                         '经营活动净收益/利润总额', '价值变动净收益/利润总额', '营业外收支净额/利润总额',
                                         '所得税/利润总额', '扣除非经常损益后的净利润/净利润', '销售商品提供劳务收到的现金/营业收入',
                                         '经营活动产生的现金流量净额/营业收入', '经营活动产生的现金流量净额/经营活动净收益',
                                         '资本支出/折旧和摊销', '资产负债率', '权益乘数', '权益乘数(杜邦分析)', '流动资产/总资产',
                                         '非流动资产/总资产', '有形资产/总资产', '带息债务/全部投入资本',
                                         '归属于母公司的股东权益/全部投入资本', '流动负债/负债合计', '非流动负债/负债合计',
                                         '经营活动产生的现金流量净额/流动负债', '产权比率', '归属于母公司的股东权益/负债合计',
                                         '归属于母公司的股东权益/带息债务', '有形资产/负债合计', '有形资产/带息债务',
                                         '有形资产/净债务', '经营活动产生的现金流量净额/负债合计',
                                         '经营活动产生的现金流量净额/带息债务', '经营活动产生的现金流量净额/净债务',
                                         '已获利息倍数(EBIT/利息费用)', '长期债务与营运资金比率', '息税折旧摊销前利润/负债合计',
                                         '营业周期', '年化总资产净利率', '总资产净利率(杜邦分析)', '固定资产合计',
                                         '扣除财务费用前营业利润', '非营业利润', '营业利润／利润总额', '非营业利润／利润总额',
                                         '经营活动产生的现金流量净额／营业利润', '货币资金／流动负债', '货币资金／带息流动负债',
                                         '营业利润／流动负债', '营业利润／负债合计', '年化投入资本回报率', '固定资产合计周转率',
                                         '利润总额／营业收入', '经营活动单季度净收益', '价值变动单季度净收益',
                                         '扣除非经常损益后的单季度净利润', '每股收益(单季度)', '销售净利率(单季度)',
                                         '销售毛利率(单季度)', '销售期间费用率(单季度)', '净利润／营业总收入(单季度)',
                                         '销售费用／营业总收入 (单季度)', '管理费用／营业总收入 (单季度)',
                                         '财务费用／营业总收入 (单季度)', '资产减值损失／营业总收入(单季度)',
                                         '营业总成本／营业总收入 (单季度)', '营业利润／营业总收入(单季度)', '净资产收益率(单季度)',
                                         '净资产单季度收益率(扣除非经常损益)', '总资产净利润(单季度)',
                                         '经营活动净收益／利润总额(单季度)', '价值变动净收益／利润总额(单季度)',
                                         '扣除非经常损益后的净利润／净利润(单季度)', '销售商品提供劳务收到的现金／营业收入(单季度)',
                                         '经营活动产生的现金流量净额／营业收入(单季度)',
                                         '经营活动产生的现金流量净额／经营活动净收益(单季度)', '基本每股收益同比增长率(%)',
                                         '稀释每股收益同比增长率(%)', '每股经营活动产生的现金流量净额同比增长率(%)',
                                         '营业利润同比增长率(%)', '利润总额同比增长率(%)', '归属母公司股东的净利润同比增长率(%)',
                                         '归属母公司股东的净利润-扣除非经常损益同比增长率(%)',
                                         '经营活动产生的现金流量净额同比增长率(%)', '净资产收益率(摊薄)同比增长率(%)',
                                         '每股净资产相对年初增长率(%)', '资产总计相对年初增长率(%)',
                                         '归属母公司的股东权益相对年初增长率(%)', '营业总收入同比增长率(%)',
                                         '营业收入同比增长率(%)', '营业总收入同比增长率(%)(单季度)',
                                         '营业总收入环比增长率(%)(单季度)', '营业收入同比增长率(%)(单季度)',
                                         '营业收入环比增长率(%)(单季度)', '营业利润同比增长率(%)(单季度)',
                                         '营业利润环比增长率(%)(单季度)', '净利润同比增长率(%)(单季度)',
                                         '净利润环比增长率(%)(单季度)', '归属母公司股东的净利润同比增长率(%)(单季度)',
                                         '归属母公司股东的净利润环比增长率(%)(单季度)', '净资产同比增长率', '研发费用', '更新标识'],
                         'prime_keys':  [0]},

    'forecast':         {'columns':     ['ts_code', 'ann_date', 'end_date', 'type', 'p_change_min', 'p_change_max',
                                         'net_profit_min', 'net_profit_max', 'last_parent_net', 'first_ann_date',
                                         'summary', 'change_reason'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'float', 'float', 'float', 'float', 'float',
                                         'str', 'str', 'str'],
                         'remarks':     ['TS股票代码', '公告日期', '报告期', '业绩预告类型', '预告净利润变动幅度下限（%）',
                                         '预告净利润变动幅度上限（%）', '预告净利润下限（万元）', '预告净利润上限（万元）',
                                         '上年同期归属母公司净利润', '首次公告日', '业绩预告摘要', '业绩变动原因'],
                         # 业绩预告类型包括：预增/预减/扭亏/首亏/续亏/续盈/略增/略减
                         'prime_keys':  [0]},

    'express':          {'columns':     ['ts_code', 'ann_date', 'end_date', 'revenue', 'operate_profit', 'total_profit',
                                         'n_income', 'total_assets', 'total_hldr_eqy_exc_min_int', 'diluted_eps',
                                         'diluted_roe', 'yoy_net_profit', 'bps', 'yoy_sales', 'yoy_op', 'yoy_tp',
                                         'yoy_dedu_np', 'yoy_eps', 'yoy_roe', 'growth_assets', 'yoy_equity',
                                         'growth_bps', 'or_last_year', 'op_last_year', 'tp_last_year', 'np_last_year',
                                         'eps_last_year', 'open_net_assets', 'open_bps', 'perf_summary', 'is_audit',
                                         'remark'],
                         'dtypes':      ['str', 'str', 'str', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float',
                                         'float', 'float', 'float', 'float', 'str', 'int', 'str'],
                         'remarks':     ['TS股票代码', '公告日期', '报告期', '营业收入(元)', '营业利润(元)', '利润总额(元)',
                                         '净利润(元)', '总资产(元)', '股东权益合计(不含少数股东权益)(元)', '每股收益(摊薄)(元)',
                                         '净资产收益率(摊薄)(%)', '去年同期修正后净利润', '每股净资产', '同比增长率:营业收入',
                                         '同比增长率:营业利润', '同比增长率:利润总额', '同比增长率:归属母公司股东的净利润',
                                         '同比增长率:基本每股收益', '同比增减:加权平均净资产收益率', '比年初增长率:总资产',
                                         '比年初增长率:归属母公司的股东权益', '比年初增长率:归属于母公司股东的每股净资产',
                                         '去年同期营业收入', '去年同期营业利润', '去年同期利润总额', '去年同期净利润',
                                         '去年同期每股收益', '期初净资产', '期初每股净资产', '业绩简要说明', '是否审计： 1是 0否',
                                         '备注'],
                         'prime_keys':  [0]}

}


class DataSource:
    """ DataSource 对象管理存储在本地的历史数据文件或数据库.

    通过DataSource对象，History模块可以容易地从本地存储的数据中读取并组装所需要的历史数据
    并确保历史数据符合HistoryPannel的要求。
    所有的历史数据必须首先从网络数据提供商处下载下来并存储在本地文件或数据库中，DataSource
    对象会检查数据的格式，确保格式正确并删除重复的数据。
    下载下来的历史数据可以存储成不同的格式，但是不管任何存储格式，所有数据表的结构都是一样
    的，而且都是与Pandas的DataFrame兼容的数据表格式。目前兼容的文件存储格式包括csv, hdf,
    ftr(feather)，兼容的数据库包括mysql和MariaDB。
    如果HistoryPanel所要求的数据未存放在本地，DataSource对象不会主动下载缺失的数据，仅会
    返回空DataFrame。
    DataSource对象可以按要求定期刷新或从NDP拉取数据，也可以手动操作

    """
    def __init__(self,
                 source_type: str,
                 file_type: str = None,
                 file_loc: str = None,
                 host: str = None,
                 port: int = None,
                 user: str = None,
                 password: str = None):
        """

        :param kwargs: the args can be improved in the future
        """
        assert source_type in ['file', 'database', 'db']

        if source_type == 'file':
            # set up file type and file location
            pass
        else: # source_type == 'database' or 'db'
            # set up connection to the data base
            if host is None: host = 'localhost'
            if port is None: port = 3306
            if user is None: raise ValueError(f'Missing user name for database connection')
            if password is None: raise ValueError(f'Missing password for database connection')
            # try to create pymysql connections
            try:
                self.con = pymysql.connect(host=host,
                                             port=port,
                                             user=user,
                                             password=password,
                                             db='ts_db')
                self.cursor = self.con.cursor()
                
            except Exception as e:
                raise e
            # try to create sqlalchemy engine:
            self.engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/ts_db')

        pass

    def file_exists(self, file_name):
        """ returns whether a file exists or not

        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        return path.exists(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)

    def new_file(self, file_name, dataframe):
        """ create given dataframe into a new file with file_name

        :param dataframe:
        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        df = self.validated_dataframe(dataframe)

        if self.file_exists(file_name):
            raise FileExistsError(f'the file with name {file_name} already exists!')
        # dataframe.to_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        dataframe.reset_index().to_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        return file_name

    def del_file(self, file_name):
        """ delete file

        :param file_name:
        :return:
        """
        raise NotImplementedError

    def open_file(self, file_name):
        """ open the file with name file_name and return the df

        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        if not self.file_exists(file_name):
            raise FileNotFoundError(f'File {QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT} '
                                    f'not found!')

        # df = pd.read_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT, index_col=0)
        df = pd.read_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        df.index = df['date']
        df.drop(columns=['date'], inplace=True)
        df = self.validated_dataframe(df)
        return df

    # 以下函数是新架构所需要的
    def read_table_data(self):
        """

        """
        pass

    def write_table_data(self):
        """

        """
        pass

    def prep_table_data(self):
        """

        """
        pass

    # 以上函数是新架构需要的
