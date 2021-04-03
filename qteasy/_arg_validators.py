# coding=utf-8
# _arg_validators.py

# ======================================
# This file contains validators and dict
# constructive codes for run kwargs,
# and related other functions.
# ======================================

import pandas as pd
import numpy as np
import datetime

PRICE_TYPE_DATA = ['close',
                   'open',
                   'high',
                   'low',
                   'pre_close',
                   'change',
                   'pct_chg',
                   'vol',
                   'amount']
INCOME_TYPE_DATA = ['basic_eps',
                    'diluted_eps',
                    'total_revenue',
                    'revenue',
                    'int_income',
                    'prem_earned',
                    'comm_income',
                    'n_commis_income',
                    'n_oth_income',
                    'n_oth_b_income',
                    'prem_income',
                    'out_prem',
                    'une_prem_reser',
                    'reins_income',
                    'n_sec_tb_income',
                    'n_sec_uw_income',
                    'n_asset_mg_income',
                    'oth_b_income',
                    'fv_value_chg_gain',
                    'invest_income',
                    'ass_invest_income',
                    'forex_gain',
                    'total_cogs',
                    'oper_cost',
                    'int_exp',
                    'comm_exp',
                    'biz_tax_surchg',
                    'sell_exp',
                    'admin_exp',
                    'fin_exp',
                    'assets_impair_loss',
                    'prem_refund',
                    'compens_payout',
                    'reser_insur_liab',
                    'div_payt',
                    'reins_exp',
                    'oper_exp',
                    'compens_payout_refu',
                    'insur_reser_refu',
                    'reins_cost_refund',
                    'other_bus_cost',
                    'operate_profit',
                    'non_oper_income',
                    'non_oper_exp',
                    'nca_disploss',
                    'total_profit',
                    'income_tax',
                    'n_income',
                    'n_income_attr_p',
                    'minority_gain',
                    'oth_compr_income',
                    't_compr_income',
                    'compr_inc_attr_p',
                    'compr_inc_attr_m_s',
                    'ebit',
                    'ebitda',
                    'insurance_exp',
                    'undist_profit',
                    'distable_profit']
BALANCE_TYPE_DATA = ['total_share',
                     'cap_rese',
                     'undistr_porfit',
                     'surplus_rese',
                     'special_rese',
                     'money_cap',
                     'trad_asset',
                     'notes_receiv',
                     'accounts_receiv',
                     'oth_receiv',
                     'prepayment',
                     'div_receiv',
                     'int_receiv',
                     'inventories',
                     'amor_exp',
                     'nca_within_1y',
                     'sett_rsrv',
                     'loanto_oth_bank_fi',
                     'premium_receiv',
                     'reinsur_receiv',
                     'reinsur_res_receiv',
                     'pur_resale_fa',
                     'oth_cur_assets',
                     'total_cur_assets',
                     'fa_avail_for_sale',
                     'htm_invest',
                     'lt_eqt_invest',
                     'invest_real_estate',
                     'time_deposits',
                     'oth_assets',
                     'lt_rec',
                     'fix_assets',
                     'cip',
                     'const_materials',
                     'fixed_assets_disp',
                     'produc_bio_assets',
                     'oil_and_gas_assets',
                     'intan_assets',
                     'r_and_d',
                     'goodwill',
                     'lt_amor_exp',
                     'defer_tax_assets',
                     'decr_in_disbur',
                     'oth_nca',
                     'total_nca',
                     'cash_reser_cb',
                     'depos_in_oth_bfi',
                     'prec_metals',
                     'deriv_assets',
                     'rr_reins_une_prem',
                     'rr_reins_outstd_cla',
                     'rr_reins_lins_liab',
                     'rr_reins_lthins_liab',
                     'refund_depos',
                     'ph_pledge_loans',
                     'refund_cap_depos',
                     'indep_acct_assets',
                     'client_depos',
                     'client_prov',
                     'transac_seat_fee',
                     'invest_as_receiv',
                     'total_assets',
                     'lt_borr',
                     'st_borr',
                     'cb_borr',
                     'depos_ib_deposits',
                     'loan_oth_bank',
                     'trading_fl',
                     'notes_payable',
                     'acct_payable',
                     'adv_receipts',
                     'sold_for_repur_fa',
                     'comm_payable',
                     'payroll_payable',
                     'taxes_payable',
                     'int_payable',
                     'div_payable',
                     'oth_payable',
                     'acc_exp',
                     'deferred_inc',
                     'st_bonds_payable',
                     'payable_to_reinsurer',
                     'rsrv_insur_cont',
                     'acting_trading_sec',
                     'acting_uw_sec',
                     'non_cur_liab_due_1y',
                     'oth_cur_liab',
                     'total_cur_liab',
                     'bond_payable',
                     'lt_payable',
                     'specific_payables',
                     'estimated_liab',
                     'defer_tax_liab',
                     'defer_inc_non_cur_liab',
                     'oth_ncl',
                     'total_ncl',
                     'depos_oth_bfi',
                     'deriv_liab',
                     'depos',
                     'agency_bus_liab',
                     'oth_liab',
                     'prem_receiv_adva',
                     'depos_received',
                     'ph_invest',
                     'reser_une_prem',
                     'reser_outstd_claims',
                     'reser_lins_liab',
                     'reser_lthins_liab',
                     'indept_acc_liab',
                     'pledge_borr',
                     'indem_payable',
                     'policy_div_payable',
                     'total_liab',
                     'treasury_share',
                     'ordin_risk_reser',
                     'forex_differ',
                     'invest_loss_unconf',
                     'minority_int',
                     'total_hldr_eqy_exc_min_int',
                     'total_hldr_eqy_inc_min_int',
                     'total_liab_hldr_eqy',
                     'lt_payroll_payable',
                     'oth_comp_income',
                     'oth_eqt_tools',
                     'oth_eqt_tools_p_shr',
                     'lending_funds',
                     'acc_receivable',
                     'st_fin_payable',
                     'payables',
                     'hfs_assets',
                     'hfs_sales',
                     'update_flag']
CASHFLOW_TYPE_DATA = ['net_profit',
                      'finan_exp',
                      'c_fr_sale_sg',
                      'recp_tax_rends',
                      'n_depos_incr_fi',
                      'n_incr_loans_cb',
                      'n_inc_borr_oth_fi',
                      'prem_fr_orig_contr',
                      'n_incr_insured_dep',
                      'n_reinsur_prem',
                      'n_incr_disp_tfa',
                      'ifc_cash_incr',
                      'n_incr_disp_faas',
                      'n_incr_loans_oth_bank',
                      'n_cap_incr_repur',
                      'c_fr_oth_operate_a',
                      'c_inf_fr_operate_a',
                      'c_paid_goods_s',
                      'c_paid_to_for_empl',
                      'c_paid_for_taxes',
                      'n_incr_clt_loan_adv',
                      'n_incr_dep_cbob',
                      'c_pay_claims_orig_inco',
                      'pay_handling_chrg',
                      'pay_comm_insur_plcy',
                      'oth_cash_pay_oper_act',
                      'st_cash_out_act',
                      'n_cashflow_act',
                      'oth_recp_ral_inv_act',
                      'c_disp_withdrwl_invest',
                      'c_recp_return_invest',
                      'n_recp_disp_fiolta',
                      'n_recp_disp_sobu',
                      'stot_inflows_inv_act',
                      'c_pay_acq_const_fiolta',
                      'c_paid_invest',
                      'n_disp_subs_oth_biz',
                      'oth_pay_ral_inv_act',
                      'n_incr_pledge_loan',
                      'stot_out_inv_act',
                      'n_cashflow_inv_act',
                      'c_recp_borrow',
                      'proc_issue_bonds',
                      'oth_cash_recp_ral_fnc_act',
                      'stot_cash_in_fnc_act',
                      'free_cashflow',
                      'c_prepay_amt_borr',
                      'c_pay_dist_dpcp_int_exp',
                      'incl_dvd_profit_paid_sc_ms',
                      'oth_cashpay_ral_fnc_act',
                      'stot_cashout_fnc_act',
                      'n_cash_flows_fnc_act',
                      'eff_fx_flu_cash',
                      'n_incr_cash_cash_equ',
                      'c_cash_equ_beg_period',
                      'c_cash_equ_end_period',
                      'c_recp_cap_contrib',
                      'incl_cash_rec_saims',
                      'uncon_invest_loss',
                      'prov_depr_assets',
                      'depr_fa_coga_dpba',
                      'amort_intang_assets',
                      'lt_amort_deferred_exp',
                      'decr_deferred_exp',
                      'incr_acc_exp',
                      'loss_disp_fiolta',
                      'loss_scr_fa',
                      'loss_fv_chg',
                      'invest_loss',
                      'decr_def_inc_tax_assets',
                      'incr_def_inc_tax_liab',
                      'decr_inventories',
                      'decr_oper_payable',
                      'incr_oper_payable',
                      'others',
                      'im_net_cashflow_oper_act',
                      'conv_debt_into_cap',
                      'conv_copbonds_due_within_1y',
                      'fa_fnc_leases',
                      'end_bal_cash',
                      'beg_bal_cash',
                      'end_bal_cash_equ',
                      'beg_bal_cash_equ',
                      'im_n_incr_cash_equ']
INDICATOR_TYPE_DATA = ['eps',
                       'dt_eps',
                       'total_revenue_ps',
                       'revenue_ps',
                       'capital_rese_ps',
                       'surplus_rese_ps',
                       'undist_profit_ps',
                       'extra_item',
                       'profit_dedt',
                       'gross_margin',
                       'current_ratio',
                       'quick_ratio',
                       'cash_ratio',
                       'invturn_days',
                       'arturn_days',
                       'inv_turn',
                       'ar_turn',
                       'ca_turn',
                       'fa_turn',
                       'assets_turn',
                       'op_income',
                       'valuechange_income',
                       'interst_income',
                       'daa',
                       'ebit',
                       'ebitda',
                       'fcff',
                       'fcfe',
                       'current_exint',
                       'noncurrent_exint',
                       'interestdebt',
                       'netdebt',
                       'tangible_asset',
                       'working_capital',
                       'networking_capital',
                       'invest_capital',
                       'retained_earnings',
                       'diluted2_eps',
                       'bps',
                       'ocfps',
                       'retainedps',
                       'cfps',
                       'ebit_ps',
                       'fcff_ps',
                       'fcfe_ps',
                       'netprofit_margin',
                       'grossprofit_margin',
                       'cogs_of_sales',
                       'expense_of_sales',
                       'profit_to_gr',
                       'saleexp_to_gr',
                       'adminexp_of_gr',
                       'finaexp_of_gr',
                       'impai_ttm',
                       'gc_of_gr',
                       'op_of_gr',
                       'ebit_of_gr',
                       'roe',
                       'roe_waa',
                       'roe_dt',
                       'roa',
                       'npta',
                       'roic',
                       'roe_yearly',
                       'roa2_yearly',
                       'roe_avg',
                       'opincome_of_ebt',
                       'investincome_of_ebt',
                       'n_op_profit_of_ebt',
                       'tax_to_ebt',
                       'dtprofit_to_profit',
                       'salescash_to_or',
                       'ocf_to_or',
                       'ocf_to_opincome',
                       'capitalized_to_da',
                       'debt_to_assets',
                       'assets_to_eqt',
                       'dp_assets_to_eqt',
                       'ca_to_assets',
                       'nca_to_assets',
                       'tbassets_to_totalassets',
                       'int_to_talcap',
                       'eqt_to_talcapital',
                       'currentdebt_to_debt',
                       'longdeb_to_debt',
                       'ocf_to_shortdebt',
                       'debt_to_eqt',
                       'eqt_to_debt',
                       'eqt_to_interestdebt',
                       'tangibleasset_to_debt',
                       'tangasset_to_intdebt',
                       'tangibleasset_to_netdebt',
                       'ocf_to_debt',
                       'ocf_to_interestdebt',
                       'ocf_to_netdebt',
                       'ebit_to_interest',
                       'longdebt_to_workingcapital',
                       'ebitda_to_debt',
                       'turn_days',
                       'roa_yearly',
                       'roa_dp',
                       'fixed_assets',
                       'profit_prefin_exp',
                       'non_op_profit',
                       'op_to_ebt',
                       'nop_to_ebt',
                       'ocf_to_profit',
                       'cash_to_liqdebt',
                       'cash_to_liqdebt_withinterest',
                       'op_to_liqdebt',
                       'op_to_debt',
                       'roic_yearly',
                       'total_fa_trun',
                       'profit_to_op',
                       'q_opincome',
                       'q_investincome',
                       'q_dtprofit',
                       'q_eps',
                       'q_netprofit_margin',
                       'q_gsprofit_margin',
                       'q_exp_to_sales',
                       'q_profit_to_gr',
                       'q_saleexp_to_gr',
                       'q_adminexp_to_gr',
                       'q_finaexp_to_gr',
                       'q_impair_to_gr_ttm',
                       'q_gc_to_gr',
                       'q_op_to_gr',
                       'q_roe',
                       'q_dt_roe',
                       'q_npta',
                       'q_opincome_to_ebt',
                       'q_investincome_to_ebt',
                       'q_dtprofit_to_profit',
                       'q_salescash_to_or',
                       'q_ocf_to_sales',
                       'q_ocf_to_or',
                       'basic_eps_yoy',
                       'dt_eps_yoy',
                       'cfps_yoy',
                       'op_yoy',
                       'ebt_yoy',
                       'netprofit_yoy',
                       'dt_netprofit_yoy',
                       'ocf_yoy',
                       'roe_yoy',
                       'bps_yoy',
                       'assets_yoy',
                       'eqt_yoy',
                       'tr_yoy',
                       'or_yoy',
                       'q_gr_yoy',
                       'q_gr_qoq',
                       'q_sales_yoy',
                       'q_sales_qoq',
                       'q_op_yoy',
                       'q_op_qoq',
                       'q_profit_yoy',
                       'q_profit_qoq',
                       'q_netprofit_yoy',
                       'q_netprofit_qoq',
                       'equity_yoy',
                       'rd_exp',
                       'update_flag']
FINANCE_TYPE_DATA = INCOME_TYPE_DATA + BALANCE_TYPE_DATA + CASHFLOW_TYPE_DATA + INDICATOR_TYPE_DATA
COMPOSIT_TYPE_DATA = []


class ConfigDict(dict):
    """ 继承自dict的一个类，用于构造qt.run()函数的参数表字典对象
        比dict多出一个功能，即通过属性来访问字典的键值，提供访问便利性

        即：
        config.attr = config['attr']

    """

    def __init__(self, *args, **kwargs):
        super(ConfigDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def _valid_qt_kwargs():
    """
    Construct and return the "valid kwargs table" for the qteasy.run() function.
    A valid kwargs table is a `dict` of `dict`s.  The keys of the outer dict are the
    valid key-words for the function.  The value for each key is a dict containing
    4 specific keys: "Default", "Validator", "level", and "text" with the following values:
        "Default"      - The default value for the kwarg if none is specified.
        "Validator"    - A function that takes the caller specified value for the kwarg,
                         and validates that it is the correct type, and (for kwargs with
                         a limited set of allowed values) may also validate that the
                         kwarg value is one of the allowed values.
        "level"        - The display level of the key-word, for the user can choose to
                         display different levels of key-words at a time to save time
        "text"         - The explanatory text of the key-words, can be displayed for
                         easy access

    :return:
    """
    today = datetime.datetime.today().date()
    vkwargs = {
        'mode':                {'Default':   1,  # 运行模式
                                'Validator': lambda value: value in (0, 1, 2, 3),
                                'level':     0,
                                'text':      'qteasy 的运行模式: \n'
                                             '0: 实时信号生成模式\n'
                                             '1: 回测-评价模式\n'
                                             '2: 策略优化模式\n'
                                             '3: 统计预测模式\n'},

        'asset_pool':          {'Default':   '000300.SH',  #
                                'Validator': lambda value: isinstance(value, (str, list))
                                                           and _validate_asset_pool(value),
                                'level':     0,
                                'text':      '可用投资产品池，投资组合基于池中的产品创建'},

        'asset_type':          {'Default':   'I',  #
                                'Validator': lambda value: isinstance(value, str)
                                                           and _validate_asset_type(value),
                                'level':     0,
                                'text':      '投资产品的资产类型，包括：\n'
                                             'I  : 指数\n'
                                             'E  : 股票\n'
                                             'F  : 期货\n'
                                             'FD : 基金\n'},

        'trade_batch_size':    {'Default':   0.0,
                                'Validator': lambda value: isinstance(value, (int, float))
                                                           and value >= 0,
                                'level':     0,
                                'text':      '投资产品的最小申购批量大小，浮点数，例如：\n'
                                             '0. : 可以购买任意份额的投资产品，包括小数份额\n'
                                             '1. : 只能购买整数份额的投资产品\n'
                                             '100: 可以购买100的整数倍份额投资产品\n'
                                             'n  : 可以购买的投资产品份额为n的整数倍，n不必为整数\n'},

        'sell_batch_size':     {'Default':   0.0,
                                'Validator': lambda value: isinstance(value, (int, float))
                                                           and value >= 0,
                                'level':     0,
                                'text':      '投资产品的最小卖出或赎回批量大小，浮点数，例如：\n'
                                             '0. : 可以购买任意份额的投资产品，包括小数份额\n'
                                             '1. : 只能购买整数份额的投资产品\n'
                                             '100: 可以购买100的整数倍份额投资产品\n'
                                             'n  : 可以购买的投资产品份额为n的整数倍，n不必为整数\n'},

        'riskfree_ir':         {'Default':   0.0035,
                                'Validator': lambda value: isinstance(value, float)
                                                           and 0 <= value < 1,
                                'level':     1,
                                'text':      '无风险利率，如果选择"考虑现金的时间价值"，则回测时现金按此年利率增值'},

        'parallel':            {'Default':   False,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     1,
                                'text':      '如果True，策略参数寻优时将利用多核心CPU进行并行计算提升效率'},

        'hist_dnld_parallel':  {'Default':   0,
                                'Validator': lambda value: isinstance(value, int) and value >= 0,
                                'level':     3,
                                'text':      '下载历史数据时启用的线程数量，为0或1时采用单线程下载，大于1时启用多线程'},

        'hist_dnld_delay':     {'Default':   None,
                                'Validator': lambda value: isinstance(value, float) and value >= 0,
                                'level':     3,
                                'text':      '为防止服务器数据压力过大，下载历史数据时下载一定数量的数据后延迟的时间长度，单位为秒'},

        'hist_dnld_delay_evy': {'Default':   None,
                                'Validator': lambda value: isinstance(value, int) and value >= 0,
                                'level':     3,
                                'text':      '为防止服务器数据压力过大，下载历史数据时，每下载一定数量的数据，就延迟一段时间。\n'
                                             '此参数为两次延迟之间的数据下载量'},

        'hist_dnld_prog_bar':  {'Default':   None,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     3,
                                'text':      '下载历史数据时是否显示进度条'},

        'gpu':                 {'Default':   False,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     1,
                                'text':      '如果True，策略参数寻优时使用GPU加速计算'},

        'hist_data_channel':   {'Default':   'local',
                                'Validator': lambda value: isinstance(value, str) and value in ['local', 'online'],
                                'level':     2,
                                'text':      '确定如何获取历史数据：\n'
                                             'local   - 优先从本地读取历史数据，未存储在本地的数据再从网上下载，并确保本地数据更新\n'
                                             'online  - 从网上下载数据，不更新本地数据'},

        'print_backtest_log':  {'Default':   False,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     1,
                                'text':      '如果True，在回测过程中会打印回测的详细交易记录'},

        'reference_asset':     {'Default':   '000300.SH',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _validate_asset_id(value),
                                'level':     0,
                                'text':      '用来产生回测结果评价结果的参考价格，默认参考价格为沪深300指数'
                                             '参考价格用来生成多用评价结果如alpha、beta比率等，因为这些指标除了考察投资收益的'
                                             '绝对值意外，还需要考虑同时期的市场平均表现，只有当投资收益优于市场平均表现的，才会'
                                             '被算作超额收益或alpha收益，这才是投资策略追求的目标'},

        'ref_asset_type':      {'Default':   'I',
                                'Validator': lambda value: _validate_asset_type(value),
                                'level':     0,
                                'text':      '参考价格的资产类型，包括：\n'
                                             'I  : 指数\n'
                                             'E  : 股票\n'
                                             'F  : 期货\n'
                                             'FD : 基金\n'},

        'ref_asset_dtype':     {'Default':   'close',
                                'Validator': lambda value: value in PRICE_TYPE_DATA,
                                'level':     0,
                                'text':      '作为参考价格的资产的价格类型。'},

        'visual':              {'Default':   True,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     0,
                                'text':      '为True时使用图表显示回测的结果'},

        'buy_sell_points':     {'Default':   True,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     2,
                                'text':      '为True时在回测图表中显示买卖点，使用红色和绿色箭头标示出买卖点的位置'},

        'show_positions':      {'Default':   True,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     2,
                                'text':      '为True时在回测图表中用色带显示投资仓位'},

        'cost_fixed_buy':      {'Default':    0,
                                'Validator': lambda value: isinstance(value, float)
                                                           and value >= 0,
                                'level':     1,
                                'text':      '买入证券或资产时的固定成本或固定佣金，该金额不随买入金额变化'
                                             '默认值为10元'},

        'cost_fixed_sell':     {'Default':    0,
                                'Validator': lambda value: isinstance(value, float)
                                                           and value >= 0,
                                'level':     1,
                                'text':      '卖出证券或资产时的固定成本或固定佣金，该金额不随卖出金额变化'
                                             '默认值为0'},

        'cost_rate_buy':       {'Default':   0.0003,
                                'Validator': lambda value: isinstance(value, float)
                                                           and 0 <= value < 1,
                                'level':     0,
                                'text':      '买入证券或资产时的成本费率或佣金比率，以买入金额的比例计算'
                                             '默认值为万分之三'},

        'cost_rate_sell':      {'Default':   0.0001,
                                'Validator': lambda value: isinstance(value, float)
                                                           and 0 <= value < 1,
                                'level':     1,
                                'text':      '卖出证券或资产时的成本费率或佣金比率，以卖出金额的比例计算'
                                             '默认值为万分之一'},

        'cost_min_buy':        {'Default':   5.0,
                                'Validator': lambda value: isinstance(value, float)
                                                           and value >= 0,
                                'level':     1,
                                'text':      '买入证券或资产时的最低成本或佣金，买入佣金只能大于或等于该最低金额'
                                             '默认值为5元'},

        'cost_min_sell':       {'Default':   0.0,
                                'Validator': lambda value: isinstance(value, float)
                                                           and value >= 0,
                                'level':     1,
                                'text':      '卖出证券或资产时的最低成本或佣金，卖出佣金只能大于或等于该最低金额'},

        'cost_slippage':       {'Default':   0.0,
                                'Validator': lambda value: isinstance(value, float)
                                                           and 0 <= value < 1,
                                'level':     1,
                                'text':      '交易滑点，一个预设参数，模拟由于交易延迟或交易金额过大产生的额外交易成本'},

        'log':                 {'Default':   True,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     1,
                                'text':      '是否生成日志'},

        'invest_start':        {'Default':   '20160405',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _is_datelike(value),
                                'level':     0,
                                'text':      '回测模式下的回测开始日期'},

        'invest_end':          {'Default':   '20210201',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _is_datelike(value),
                                'level':     0,
                                'text':      '回测模式下的回测结束日期'},

        'invest_cash_amounts': {'Default':   [100000.0],
                                'Validator': lambda value: isinstance(value, (tuple, list))
                                                           and all(isinstance(item, (float, int))
                                                                   for item in value)
                                                           and all(item > 1 for item in value),
                                'level':     1,
                                'text':      '投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入'},

        'invest_cash_dates':   {'Default':   None,
                                'Validator': lambda value: isinstance(value, (str, list))
                                                           and all(isinstance(item, str)
                                                                   for item in value) or value is None,
                                'level':     1,
                                'text':      '回测操作现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None\n'
                                             '当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖\n'
                                             'invest_start\n'
                                             '参数输入类型为str时，格式为"YYYYMMDD"\n'
                                             '如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型\n'
                                             '以下两种输入方式等效：\n'
                                             '"20100104,20100202,20100304"'
                                             '["20100104", "20100202", "20100304"]'},

        'opti_start':          {'Default':   '20160405',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _is_datelike(value),
                                'level':     0,
                                'text':      '优化模式下的策略优化区间开始日期'},

        'opti_end':            {'Default':   '20191231',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _is_datelike(value),
                                'level':     0,
                                'text':      '优化模式下的策略优化区间结束日期'},

        'opti_cash_amounts':   {'Default':   [100000.0],
                                'Validator': lambda value: isinstance(value, (tuple, list))
                                                           and all(isinstance(item, (float, int))
                                                                   for item in value)
                                                           and all(item > 1 for item in value),
                                'level':     1,
                                'text':      '优化模式投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入'},

        'opti_cash_dates':     {'Default':   None,
                                'Validator': lambda value: isinstance(value, (str, list))
                                                           and all(isinstance(item, str)
                                                                   for item in value) or value is None,
                                'level':     1,
                                'text':      '策略优化区间现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None\n'
                                             '当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖\n'
                                             'invest_start\n'
                                             '参数输入类型为str时，格式为"YYYYMMDD"\n'
                                             '如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型\n'
                                             '以下两种输入方式等效：\n'
                                             '"20100104,20100202,20100304"'
                                             '["20100104", "20100202", "20100304"]'},

        'opti_type':           {'Default':   'single',
                                'Validator': lambda value: isinstance(value, str) and value in ['single', 'multiple'],
                                'level':     2,
                                'text':      '优化类型。指优化数据的利用方式:\n'
                                             '"single"   - 在每一回合的优化测试中，在优化区间上进行覆盖整个区间的单次回测并评价'
                                             '回测结果\n'
                                             '"multiple" - 在每一回合的优化测试中，将优化区间的数据划分为多个子区间，在这些子区间'
                                             '上分别测试，并根据所有测试的结果确定策略在整个区间上的评价结果'},

        'opti_sub_periods':    {'Default':   5,
                                'Validator': lambda value: isinstance(value, int) and value >= 1,
                                'level':     2,
                                'text':      '仅对无监督优化有效。且仅当优化类型为"multiple"时有效。将优化区间切分为子区间的数量'},

        'opti_sub_prd_length': {'Default':   0.6,
                                'Validator': lambda value: isinstance(value, float) and 0 <= value <= 1.,
                                'level':     2,
                                'text':      '仅当优化类型为"multiple"时有效。每一个优化子区间长度占整个优化区间长度的比例'
                                             '例如，当优化区间长度为10年时，本参数为0.6代表每一个优化子区间长度为6年'},

        'test_start':          {'Default':   '20200106',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _is_datelike(value),
                                'level':     0,
                                'text':      '优化模式下的策略测试区间开始日期'
                                             '格式为"YYYYMMDD"'
                                             '字符串类型输入'},

        'test_end':            {'Default':   '20210201',
                                'Validator': lambda value: isinstance(value, str)
                                                           and _is_datelike(value),
                                'level':     0,
                                'text':      '优化模式下的策略测试区间结束日期'
                                             '格式为"YYYYMMDD"'
                                             '字符串类型输入'},

        'test_cash_amounts':   {'Default':   [100000.0],
                                'Validator': lambda value: isinstance(value, (tuple, list))
                                                           and all(isinstance(item, (float, int))
                                                                   for item in value)
                                                           and all(item > 1 for item in value),
                                'level':     1,
                                'text':      '优化模式策略测试投资的金额，一个tuple或list，每次投入资金的金额。'
                                             '模拟现金多次定投投入时，输入多个数字表示多次投入'
                                             '输入的数字的个数必须与cash_dates中的日期数量相同'},

        'test_cash_dates':     {'Default':   None,
                                'Validator': lambda value: isinstance(value, (str, list))
                                                           and all(isinstance(item, str)
                                                                   for item in value) or value is None,
                                'level':     1,
                                'text':      '策略优化区间现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None\n'
                                             '当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖\n'
                                             'invest_start参数\n'
                                             '参数输入类型为str时，格式为"YYYYMMDD"\n'
                                             '如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型\n'
                                             '以下两种输入方式等效：\n'
                                             '"20100104,20100202,20100304"'
                                             '["20100104", "20100202", "20100304"]'},

        'test_type':           {'Default':   'single',
                                'Validator': lambda value: isinstance(value, str) and
                                                           value in ['single', 'multiple', 'montecarlo'],
                                'level':     2,
                                'text':      '测试类型。指测试数据的利用方式:\n'
                                             '"single"     - 在每一回合的优化测试中，在测试区间上进行覆盖整个区间的单次回测并评价'
                                             '               回测结果\n'
                                             '"multiple"   - 在每一回合的优化测试中，将测试区间的数据划分为多个子区间，在这些子区间'
                                             '               上分别测试，并根据所有测试的结果确定策略在整个区间上的评价结果\n'
                                             '"montecarlo" - 蒙特卡洛测试，根据测试区间历史数据的统计性质，随机生成大量的模拟价格变'
                                             '               化数据，用这些数据对策略的表现进行评价，最后给出统计意义的评价结果'},

        'test_indicators':     {'Default':   'years,fv,return,mdd,v,ref,alpha,beta,sharp,info',
                                'Validator': lambda value: isinstance(value, str),
                                'level':     2,
                                'text':      '对优化后的策略参数进行测试评价的评价指标。'
                                             '格式为逗号分隔的字符串，多个评价指标会以字典的形式输出，包含以下类型中的一种或多种\n'
                                             '"years"       - total year\n'
                                             '"fv"          - final values\n'
                                             '"return"      - total return rate\n'
                                             '"mdd"         - max draw down\n'
                                             '"ref"         - reference data return\n'
                                             '"alpha"       - alpha rate\n'
                                             '"beta"        - beta rate\n'
                                             '"sharp"       - sharp rate\n'
                                             '"info"        - info rate'},

        'indicator_plot_type': {'Default':   2,
                                'Validator': lambda value: isinstance(value, (int, str)) and
                                                           ((value in ['errorbar',
                                                                       'scatter',
                                                                       'histo',
                                                                       'violin',
                                                                       'box']) or (0 <= value <= 4)),
                                'level':     2,
                                'text':      '优化或测试结果评价指标的可视化图表类型:\n'
                                             '0  - errorbar 类型\n'
                                             '1  - scatter 类型\n'
                                             '2  - histo 类型\n'
                                             '3  - violin 类型\n'
                                             '4  - box 类型'},

        'test_sub_periods':    {'Default':   3,
                                'Validator': lambda value: isinstance(value, int) and value >= 1,
                                'level':     2,
                                'text':      '仅当测试类型为"multiple"时有效。将测试区间切分为子区间的数量'},

        'test_sub_prd_length': {'Default':   0.75,
                                'Validator': lambda value: isinstance(value, float) and 0 <= value <= 1.,
                                'level':     2,
                                'text':      '仅当测试类型为"multiple"时有效。每一个测试子区间长度占整个测试区间长度的比例'
                                             '例如，当测试区间长度为4年时，本参数0.75代表每个测试子区间长度为3年'},

        'test_cycle_count':    {'Default':   100,
                                'Validator': lambda value: isinstance(value, int) and value >= 1,
                                'level':     2,
                                'text':      '仅当测试类型为"montecarlo"时有效。生成的模拟测试数据的数量。'
                                             '默认情况下生成100组模拟价格数据，并进行100次策略回测并评价其统计结果'},

        'optimize_target':     {'Default':   'final_value',
                                'Validator': lambda value: isinstance(value, str)
                                                           and value in ['final_value', 'FV', 'SHARP'],
                                'level':     1,
                                'text':      '策略的优化目标。即优化时以找到该指标最佳的策略为目标'},

        'maximize_target':     {'Default':   True,
                                'Validator': lambda value: isinstance(value, bool),
                                'level':     1,
                                'text':      '为True时寻找目标值最大的策略，为False时寻找目标值最低的策略'},

        'opti_method':         {'Default':   1,
                                'Validator': lambda value: isinstance(value, int)
                                                           and value <= 3,
                                'level':     1,
                                'text':      '策略优化算法，可选值如下:\n'
                                             '0 - 网格法，按照一定间隔对整个向量空间进行网格搜索\n'
                                             '1 - 蒙特卡洛法，在向量空间中随机取出一定的点搜索最佳策略\n'
                                             '2 - 递进步长法，对向量空间进行多轮搜索，每一轮搜索结束后根据结果选择部分子空间，缩小\n'
                                             '    步长进一步搜索\n'
                                             '3 - 遗传算法，模拟生物种群在环境压力下不断进化的方法寻找全局最优（尚未完成）\n'
                                             '4 - ML方法，基于机器学习的最佳策略搜索算法（尚未完成）\n'},

        'opti_grid_size':      {'Default':   1,
                                'Validator': lambda value: _num_or_seq_of_num(value) and value > 0,
                                'level':     1,
                                'text':      '使用穷举法搜索最佳策略时有用，搜索步长'},

        'opti_sample_count':   {'Default':   1000,
                                'Validator': lambda value: isinstance(value, int) and value > 0,
                                'level':     1,
                                'text':      '使用蒙特卡洛法搜索最佳策略时有用，在向量空间中采样的数量'},

        'opti_r_sample_count': {'Default':   16,
                                'Validator': lambda value: _num_or_seq_of_num(value)
                                                           and value >= 0,
                                'level':     1,
                                'text':      '在使用递进步长法搜索最佳策略时有用，每一轮随机取样的数量'},

        'opti_reduce_ratio':   {'Default':   0.1,
                                'Validator': lambda value: isinstance(value, float)
                                                           and 0 < value < 1,
                                'level':     1,
                                'text':      '在使用递进步长法搜索最佳策略时有用，\n'
                                             '每一轮随机取样后择优留用的比例，同样也是子空间缩小的比例\n'},

        'opti_max_rounds':     {'Default':   5,
                                'Validator': lambda value: isinstance(value, int)
                                                           and value > 1,
                                'level':     1,
                                'text':      '在使用递进步长法搜索最佳策略时有用，多轮搜索的最大轮数，轮数大于该值时停止搜索'},

        'opti_min_volume':     {'Default':   1000,
                                'Validator': lambda value: isinstance(value, (float, int))
                                                           and value > 0,
                                'level':     1,
                                'text':      '在使用递进步长法搜索最佳策略时有用，空间最小体积，当空间volume低于该值时停止搜索'},

        'opti_population':     {'Default':   1000.0,
                                'Validator': lambda value: isinstance(value, float)
                                                           and value >= 0,
                                'level':     1,
                                'text':      '在使用遗传算法搜索最佳策略时有用，种群的数量'},

        'opti_output_count':   {'Default':   30,
                                'Validator': lambda value: isinstance(value, int)
                                                           and value > 0,
                                'level':     1,
                                'text':      '策略参数优化后输出的最优参数数量'},

    }
    _validate_vkwargs_dict(vkwargs)

    return vkwargs


def _validate_vkwargs_dict(vkwargs):
    """ Check that we didn't make a typo in any of the things
        that should be the same for all vkwargs dict items:

    :param vkwargs:
    :return:
    """
    for key, value in vkwargs.items():
        if len(value) != 4:
            raise ValueError(f'Items != 2 in valid kwarg table, for kwarg {key}')
        if 'Default' not in value:
            raise ValueError(f'Missing "Default" value for kwarg {key}')
        if 'Validator' not in value:
            raise ValueError(f'Missing "Validator" function for kwarg {key}')
        if 'level' not in value:
            raise ValueError(f'Missing "level" identifier for kwarg {key}')
        if 'text' not in value:
            raise ValueError(f'Missing "text" string for kwarg {key}')


def _vkwargs_to_text(kwargs, level=0, info=False, verbose=False):
    """ Given a list of kwargs, verify that all kwargs are in the valid kwargs,
        and display their values and other information according to given
        parameters. return a string with all formulated information

    :param kwargs: list or tuple, kwargs that are to be displayed
    :param level:
    :param info:
    :param verbose:
    :return:
    """
    COLUMN_W_KEY = 21
    COLUMN_W_CURRENT = 15
    COLUMN_OFFSET_DESCRIPTION = 4
    vkwargs = _valid_qt_kwargs()
    output_strings = list()
    if info:
        output_strings.append('Key                   Current        Default\n')
        if verbose:
            output_strings.append('Description\n')
        output_strings.append('------------------------------------------------\n')
    else:
        output_strings.append('Key                   Current        \n')
        output_strings.append('-------------------------------------\n')
    for key in kwargs:
        if key not in vkwargs:
            raise KeyError(f'Unrecognized kwarg={str(key)}')
        else:
            cur_level = vkwargs[key]['level']
            if cur_level <= level:  # only display kwargs that are at higher level
                cur_value = str(QT_CONFIG[key])
                default_value = str(vkwargs[key]['Default'])
                description = str(vkwargs[key]['text'])
                output_strings.append(f'{str(key)}:{" "*(COLUMN_W_KEY - len(str(key)))}')
                if info:
                    output_strings.append(f'{cur_value}{" "*(COLUMN_W_CURRENT - len(cur_value))}'
                                          f'<{default_value}>\n')
                    if verbose:
                        output_strings.append(f'{" "*COLUMN_OFFSET_DESCRIPTION}{description}\n')
                else:
                    output_strings.append(f'{cur_value}\n')
    return ''.join(output_strings)


def _process_kwargs(kwargs, vkwargs):
    """ Given a "valid kwargs table" and some kwargs, verify that each key-word
        is valid per the kwargs table, and that the value of the kwarg is the
        correct type.  Fill a configuration dictionary with the default value
        for each kwarg, and then substitute in any values that were provided
        as kwargs and return the configuration dictionary.

    :param kwargs: keywords that is given by user
    :param vkwargs: valid keywords table usd for validating given kwargs
    :return:
    """
    # initialize configuration from valid_kwargs_table:
    config = ConfigDict()
    for key, value in vkwargs.items():
        config[key] = value['Default']

    # now validate kwargs, and for any valid kwargs
    #  replace the appropriate value in config:
    for key in kwargs.keys():
        value = kwargs[key]
        _validate_key_and_value(key, value)
        config[key] = value

    return config


def _validate_key_and_value(key, value):
    """ given one key, validate the key according to vkwargs dict
        return True if the key is valid
        raise if the key is not valid

    :param key:
    :param value:
    :return:
    """
    vkwargs = _valid_qt_kwargs()
    if key not in vkwargs:
        raise KeyError(f'Unrecognized kwarg={str(key)}')
    else:
        try:
            valid = vkwargs[key]['Validator'](value)
        except Exception as ex:
            ex.extra_info = f'kwarg {key} validator raised exception to value: {str(value)}'
            raise
        if not valid:
            import inspect
            v = inspect.getsource(vkwargs[key]['Validator']).strip()
            raise TypeError(
                    f'kwarg {key} validator returned False for value: {str(value)}\n'
                    f'Extra information: \n{vkwargs[key]["text"]}\n    ' + v)
            # ---------------------------------------------------------------
            #      At this point , if we have not raised an exception,
            #      then kwarg is valid as far as we can tell.

    return True


def _validate_asset_id(value):
    """

    :param value:
    :return:
    """
    return True


def _validate_asset_type(value):
    """

    :param value:
    :return:
    """
    return value in ['I', 'E', 'F', 'FD']


def _is_datelike(value):
    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.date)):
        return True
    if isinstance(value, str):
        try:
            dt = pd.to_datetime(value)
            return True
        except:
            return False
    return False


def _num_or_seq_of_num(value):
    return (isinstance(value, (int, float)) or
            (isinstance(value, (list, tuple, np.ndarray)) and
             all([isinstance(v, (int, float)) for v in value]))
            )


def _bypass_kwarg_validation(value):
    ''' For some kwargs, we either don't know enough, or
        the validation is too complex to make it worth while,
        so we bypass kwarg validation.  If the kwarg is
        invalid, then eventually an exception will be
        raised at the time the kwarg value is actually used.
    '''
    return True


def _kwarg_not_implemented(value):
    ''' If you want to list a kwarg in a valid_kwargs dict for a given
        function, but you have not yet, or don't yet want to, implement
        the kwarg; or you simply want to (temporarily) disable the kwarg,
        then use this function as the kwarg validator
    '''
    raise NotImplementedError('kwarg NOT implemented.')


def _validate_asset_pool(kwargs):
    """

    :param kwargs:
    :return:
    """
    return True


QT_CONFIG = _process_kwargs({}, _valid_qt_kwargs())