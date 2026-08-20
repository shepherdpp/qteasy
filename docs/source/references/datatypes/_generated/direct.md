<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-19 17:34 UTC -->
<!-- acquisition_type: direct -->
<!-- row_count: 884 -->

# 直读（direct）

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 生成，共 **884** 条。

请勿手改；更新内置类型后请重跑生成脚本。

| name | freq | asset_type | description | table_name | kind | usable_in |
| --- | --- | --- | --- | --- | --- | --- |
| acc_exp | q | E | 上市公司资产负债表 - 预提费用 | balance | history | history_panel,strategy |
| acc_receivable | q | E | 上市公司资产负债表 - 应收款项 | balance | history | history_panel,strategy |
| accounts_pay | q | E | 上市公司资产负债表 - 应付票据及应付账款 | balance | history | history_panel,strategy |
| accounts_receiv | q | E | 上市公司资产负债表 - 应收账款 | balance | history | history_panel,strategy |
| accounts_receiv_bill | q | E | 上市公司资产负债表 - 应收票据及应收账款 | balance | history | history_panel,strategy |
| acct_payable | q | E | 上市公司资产负债表 - 应付账款 | balance | history | history_panel,strategy |
| accum_div | d | FD | 基金净值 - 累计分红 | fund_nav | history | history_panel,strategy |
| accum_nav | d | FD | 基金净值 - 累计净值 | fund_nav | history | history_panel,strategy |
| acting_trading_sec | q | E | 上市公司资产负债表 - 代理买卖证券款 | balance | history | history_panel,strategy |
| acting_uw_sec | q | E | 上市公司资产负债表 - 代理承销证券款 | balance | history | history_panel,strategy |
| activity | d | E | 股票技术指标 - 活跃度(%) | stock_indicator2 | history | history_panel,strategy |
| adj_lossgain | q | E | 上市公司利润表 - 调整以前年度损益 | income | history | history_panel,strategy |
| adj_nav | d | FD | 基金净值 - 复权净值 | fund_nav | history | history_panel,strategy |
| admin_exp | q | E | 上市公司利润表 - 减:管理费用 | income | history | history_panel,strategy |
| adminexp_of_gr | q | E | 上市公司财务指标 - 管理费用/营业总收入 | financial | history | history_panel,strategy |
| adv_receipts | q | E | 上市公司资产负债表 - 预收款项 | balance | history | history_panel,strategy |
| agency_bus_liab | q | E | 上市公司资产负债表 - 代理业务负债 | balance | history | history_panel,strategy |
| amodcost_fin_assets | q | E | 上市公司利润表 - 以摊余成本计量的金融资产终止确认收益 | income | history | history_panel,strategy |
| amor_exp | q | E | 上市公司资产负债表 - 长期待摊费用 | balance | history | history_panel,strategy |
| amort_intang_assets | q | E | 上市公司现金流量表 - 无形资产摊销 | cashflow | history | history_panel,strategy |
| amount | 15min | E | 股票15分钟K线 - 成交额 （千元） | stock_15min | history | history_panel,strategy |
| amount | 15min | FD | 基金15分钟K线 - 成交额 （千元） | fund_15min | history | history_panel,strategy |
| amount | 15min | FT | 期货15分钟K线 - 成交额 （千元） | future_15min | history | history_panel,strategy |
| amount | 15min | IDX | 指数15分钟K线 - 成交额 （千元） | index_15min | history | history_panel,strategy |
| amount | 15min | OPT | 期权15分钟K线 - 成交额 （千元） | options_15min | history | history_panel,strategy |
| amount | 1min | E | 股票60秒K线 - 成交额 （千元） | stock_1min | history | history_panel,strategy |
| amount | 1min | FD | 基金60秒K线 - 成交额 （千元） | fund_1min | history | history_panel,strategy |
| amount | 1min | FT | 期货60秒K线 - 成交额 （千元） | future_1min | history | history_panel,strategy |
| amount | 1min | IDX | 指数60秒K线 - 成交额 （千元） | index_1min | history | history_panel,strategy |
| amount | 1min | OPT | 期权60秒K线 - 成交额 （千元） | options_1min | history | history_panel,strategy |
| amount | 30min | E | 股票30分钟K线 - 成交额 （千元） | stock_30min | history | history_panel,strategy |
| amount | 30min | FD | 基金30分钟K线 - 成交额 （千元） | fund_30min | history | history_panel,strategy |
| amount | 30min | FT | 期货30分钟K线 - 成交额 （千元） | future_30min | history | history_panel,strategy |
| amount | 30min | IDX | 指数30分钟K线 - 成交额 （千元） | index_30min | history | history_panel,strategy |
| amount | 30min | OPT | 期权30分钟K线 - 成交额 （千元） | options_30min | history | history_panel,strategy |
| amount | 5min | E | 股票5分钟K线 - 成交额 （千元） | stock_5min | history | history_panel,strategy |
| amount | 5min | FD | 基金5分钟K线 - 成交额 （千元） | fund_5min | history | history_panel,strategy |
| amount | 5min | FT | 期货5分钟K线 - 成交额 （千元） | future_5min | history | history_panel,strategy |
| amount | 5min | IDX | 指数5分钟K线 - 成交额 （千元） | index_5min | history | history_panel,strategy |
| amount | 5min | OPT | 期权5分钟K线 - 成交额 （千元） | options_5min | history | history_panel,strategy |
| amount | d | E | 股票日K线 - 成交额 （千元） | stock_daily | history | history_panel,strategy |
| amount | d | FD | 基金日K线 - 成交额 （千元） | fund_daily | history | history_panel,strategy |
| amount | d | FT | 期货日K线 - 成交额 （千元） | future_daily | history | history_panel,strategy |
| amount | d | IDX | 指数日K线 - 成交额 （千元） | index_daily | history | history_panel,strategy |
| amount | d | OPT | 期权日K线 - 成交额 （千元） | options_daily | history | history_panel,strategy |
| amount | h | E | 股票小时K线 - 成交额 （千元） | stock_hourly | history | history_panel,strategy |
| amount | h | FD | 基金小时K线 - 成交额 （千元） | fund_hourly | history | history_panel,strategy |
| amount | h | FT | 期货小时K线 - 成交额 （千元） | future_hourly | history | history_panel,strategy |
| amount | h | IDX | 指数小时K线 - 成交额 （千元） | index_hourly | history | history_panel,strategy |
| amount | h | OPT | 期权小时K线 - 成交额 （千元） | options_hourly | history | history_panel,strategy |
| amount | m | E | 股票月K线 - 成交额 （千元） | stock_monthly | history | history_panel,strategy |
| amount | m | FD | 基金月K线 - 成交额 （千元） | fund_monthly | history | history_panel,strategy |
| amount | m | FT | 期货月K线 - 成交额 （千元） | future_monthly | history | history_panel,strategy |
| amount | m | IDX | 指数月K线 - 成交额 （千元） | index_monthly | history | history_panel,strategy |
| amount | w | E | 股票周K线 - 成交额 （千元） | stock_weekly | history | history_panel,strategy |
| amount | w | FD | 基金周K线 - 成交额 （千元） | fund_weekly | history | history_panel,strategy |
| amount | w | FT | 期货周K线 - 成交额 （千元） | future_weekly | history | history_panel,strategy |
| amount | w | IDX | 指数周K线 - 成交额 （千元） | index_weekly | history | history_panel,strategy |
| ar_turn | q | E | 上市公司财务指标 - 应收账款周转率 | financial | history | history_panel,strategy |
| arturn_days | q | E | 上市公司财务指标 - 应收账款周转天数 | financial | history | history_panel,strategy |
| ass_invest_income | q | E | 上市公司利润表 - 其中:对联营企业和合营企业的投资收益 | income | history | history_panel,strategy |
| asset_disp_income | q | E | 上市公司利润表 - 资产处置收益 | income | history | history_panel,strategy |
| assets_impair_loss | q | E | 上市公司利润表 - 减:资产减值损失 | income | history | history_panel,strategy |
| assets_to_eqt | q | E | 上市公司财务指标 - 权益乘数 | financial | history | history_panel,strategy |
| assets_turn | q | E | 上市公司财务指标 - 总资产周转率 | financial | history | history_panel,strategy |
| assets_yoy | q | E | 上市公司财务指标 - 资产总计相对年初增长率(%) | financial | history | history_panel,strategy |
| attack | d | E | 股票技术指标 - 攻击波(%) | stock_indicator2 | history | history_panel,strategy |
| avg_price | d | E | 股票技术指标 - 平均价 | stock_indicator2 | history | history_panel,strategy |
| avg_turnover | d | E | 股票技术指标 - 笔换手 | stock_indicator2 | history | history_panel,strategy |
| basic_eps | q | E | 上市公司利润表 - 基本每股收益 | income | history | history_panel,strategy |
| basic_eps_yoy | q | E | 上市公司财务指标 - 基本每股收益同比增长率(%) | financial | history | history_panel,strategy |
| beg_bal_cash | q | E | 上市公司现金流量表 - 减:现金的期初余额 | cashflow | history | history_panel,strategy |
| beg_bal_cash_equ | q | E | 上市公司现金流量表 - 减:现金等价物的期初余额 | cashflow | history | history_panel,strategy |
| biz_tax_surchg | q | E | 上市公司利润表 - 减:营业税金及附加 | income | history | history_panel,strategy |
| bond_payable | q | E | 上市公司资产负债表 - 应付债券 | balance | history | history_panel,strategy |
| bps | q | E | 上市公司业绩快报 - 每股净资产 | express | history | history_panel,strategy |
| bps_yoy | q | E | 上市公司财务指标 - 每股净资产相对年初增长率(%) | financial | history | history_panel,strategy |
| buy_elg_amount | d | E | 个股资金流向 - 特大单买入金额（万元） | money_flow | history | history_panel,strategy |
| buy_elg_vol | d | E | 个股资金流向 - 特大单买入量（手） | money_flow | history | history_panel,strategy |
| buy_lg_amount | d | E | 个股资金流向 - 大单买入金额（万元） | money_flow | history | history_panel,strategy |
| buy_lg_vol | d | E | 个股资金流向 - 大单买入量（手） | money_flow | history | history_panel,strategy |
| buy_md_amount | d | E | 个股资金流向 - 中单买入金额（万元） | money_flow | history | history_panel,strategy |
| buy_md_vol | d | E | 个股资金流向 - 中单买入量（手） | money_flow | history | history_panel,strategy |
| buy_sm_amount | d | E | 个股资金流向 - 小单买入金额（万元） | money_flow | history | history_panel,strategy |
| buy_sm_vol | d | E | 个股资金流向 - 小单买入量（手） | money_flow | history | history_panel,strategy |
| buying | d | E | 股票技术指标 - 外盘（主动买， 手） | stock_indicator2 | history | history_panel,strategy |
| c_cash_equ_beg_period | q | E | 上市公司现金流量表 - 期初现金及现金等价物余额 | cashflow | history | history_panel,strategy |
| c_cash_equ_end_period | q | E | 上市公司现金流量表 - 期末现金及现金等价物余额 | cashflow | history | history_panel,strategy |
| c_disp_withdrwl_invest | q | E | 上市公司现金流量表 - 收回投资收到的现金 | cashflow | history | history_panel,strategy |
| c_fr_oth_operate_a | q | E | 上市公司现金流量表 - 收到其他与经营活动有关的现金 | cashflow | history | history_panel,strategy |
| c_fr_sale_sg | q | E | 上市公司现金流量表 - 销售商品、提供劳务收到的现金 | cashflow | history | history_panel,strategy |
| c_inf_fr_operate_a | q | E | 上市公司现金流量表 - 经营活动现金流入小计 | cashflow | history | history_panel,strategy |
| c_paid_for_taxes | q | E | 上市公司现金流量表 - 支付的各项税费 | cashflow | history | history_panel,strategy |
| c_paid_goods_s | q | E | 上市公司现金流量表 - 购买商品、接受劳务支付的现金 | cashflow | history | history_panel,strategy |
| c_paid_invest | q | E | 上市公司现金流量表 - 投资支付的现金 | cashflow | history | history_panel,strategy |
| c_paid_to_for_empl | q | E | 上市公司现金流量表 - 支付给职工以及为职工支付的现金 | cashflow | history | history_panel,strategy |
| c_pay_acq_const_fiolta | q | E | 上市公司现金流量表 - 购建固定资产、无形资产和其他长期资产支付的现金 | cashflow | history | history_panel,strategy |
| c_pay_claims_orig_inco | q | E | 上市公司现金流量表 - 支付原保险合同赔付款项的现金 | cashflow | history | history_panel,strategy |
| c_pay_dist_dpcp_int_exp | q | E | 上市公司现金流量表 - 分配股利、利润或偿付利息支付的现金 | cashflow | history | history_panel,strategy |
| c_prepay_amt_borr | q | E | 上市公司现金流量表 - 偿还债务支付的现金 | cashflow | history | history_panel,strategy |
| c_recp_borrow | q | E | 上市公司现金流量表 - 取得借款收到的现金 | cashflow | history | history_panel,strategy |
| c_recp_cap_contrib | q | E | 上市公司现金流量表 - 吸收投资收到的现金 | cashflow | history | history_panel,strategy |
| c_recp_return_invest | q | E | 上市公司现金流量表 - 取得投资收益收到的现金 | cashflow | history | history_panel,strategy |
| ca_to_assets | q | E | 上市公司财务指标 - 流动资产/总资产 | financial | history | history_panel,strategy |
| ca_turn | q | E | 上市公司财务指标 - 流动资产周转率 | financial | history | history_panel,strategy |
| cap_rese | q | E | 上市公司资产负债表 - 资本公积金 | balance | history | history_panel,strategy |
| capit_comstock_div | q | E | 上市公司利润表 - 转作股本的普通股股利 | income | history | history_panel,strategy |
| capital_rese_ps | q | E | 上市公司财务指标 - 每股资本公积 | financial | history | history_panel,strategy |
| capitalized_to_da | q | E | 上市公司财务指标 - 资本支出/折旧和摊销 | financial | history | history_panel,strategy |
| cash_ratio | q | E | 上市公司财务指标 - 保守速动比率 | financial | history | history_panel,strategy |
| cash_reser_cb | q | E | 上市公司资产负债表 - 现金及存放中央银行款项 | balance | history | history_panel,strategy |
| cash_to_liqdebt | q | E | 上市公司财务指标 - 货币资金／流动负债 | financial | history | history_panel,strategy |
| cash_to_liqdebt_withinterest | q | E | 上市公司财务指标 - 货币资金／带息流动负债 | financial | history | history_panel,strategy |
| cashflow_credit_impa_loss | q | E | 上市公司现金流量表 - 信用减值损失 | cashflow | history | history_panel,strategy |
| cb_borr | q | E | 上市公司资产负债表 - 向中央银行借款 | balance | history | history_panel,strategy |
| cfps | q | E | 上市公司财务指标 - 每股现金流量净额 | financial | history | history_panel,strategy |
| cfps_yoy | q | E | 上市公司财务指标 - 每股经营活动产生的现金流量净额同比增长率(%) | financial | history | history_panel,strategy |
| ci_amount | d | IDX | 中信指数日K线 - 成交额 （万元） | ci_index_daily | history | history_panel,strategy |
| ci_change | d | IDX | 中信指数日K线 - 涨跌额 | ci_index_daily | history | history_panel,strategy |
| ci_close | d | IDX | 中信指数日K线 - 收盘价 | ci_index_daily | history | history_panel,strategy |
| ci_high | d | IDX | 中信指数日K线 - 最高价 | ci_index_daily | history | history_panel,strategy |
| ci_low | d | IDX | 中信指数日K线 - 最低价 | ci_index_daily | history | history_panel,strategy |
| ci_open | d | IDX | 中信指数日K线 - 开盘价 | ci_index_daily | history | history_panel,strategy |
| ci_pct_change | d | IDX | 中信指数日K线 - 涨跌幅 | ci_index_daily | history | history_panel,strategy |
| ci_pre_close | d | IDX | 中信指数日K线 - 昨日收盘点位 | ci_index_daily | history | history_panel,strategy |
| ci_vol | d | IDX | 中信指数日K线 - 成交量 （万股） | ci_index_daily | history | history_panel,strategy |
| cip | q | E | 上市公司资产负债表 - 在建工程 | balance | history | history_panel,strategy |
| cip_total | q | E | 上市公司资产负债表 - 在建工程(合计)(元) | balance | history | history_panel,strategy |
| circ_mv | d | E | 股票技术指标 - 流通市值（万元） | stock_indicator | history | history_panel,strategy |
| client_depos | q | E | 上市公司资产负债表 - 其中：客户资金存款 | balance | history | history_panel,strategy |
| client_prov | q | E | 上市公司资产负债表 - 其中：客户备付金 | balance | history | history_panel,strategy |
| close | 15min | E | 股票15分钟K线 - 收盘价 | stock_15min | history | history_panel,strategy |
| close | 15min | FD | 基金15分钟K线 - 收盘价 | fund_15min | history | history_panel,strategy |
| close | 15min | FT | 期货15分钟K线 - 收盘价 | future_15min | history | history_panel,strategy |
| close | 15min | IDX | 指数15分钟K线 - 收盘价 | index_15min | history | history_panel,strategy |
| close | 15min | OPT | 期权15分钟K线 - 收盘价 | options_15min | history | history_panel,strategy |
| close | 1min | E | 股票60秒K线 - 收盘价 | stock_1min | history | history_panel,strategy |
| close | 1min | FD | 基金60秒K线 - 收盘价 | fund_1min | history | history_panel,strategy |
| close | 1min | FT | 期货60秒K线 - 收盘价 | future_1min | history | history_panel,strategy |
| close | 1min | IDX | 指数60秒K线 - 收盘价 | index_1min | history | history_panel,strategy |
| close | 1min | OPT | 期权60秒K线 - 收盘价 | options_1min | history | history_panel,strategy |
| close | 30min | E | 股票30分钟K线 - 收盘价 | stock_30min | history | history_panel,strategy |
| close | 30min | FD | 基金30分钟K线 - 收盘价 | fund_30min | history | history_panel,strategy |
| close | 30min | FT | 期货30分钟K线 - 收盘价 | future_30min | history | history_panel,strategy |
| close | 30min | IDX | 指数30分钟K线 - 收盘价 | index_30min | history | history_panel,strategy |
| close | 30min | OPT | 期权30分钟K线 - 收盘价 | options_30min | history | history_panel,strategy |
| close | 5min | E | 股票5分钟K线 - 收盘价 | stock_5min | history | history_panel,strategy |
| close | 5min | FD | 基金5分钟K线 - 收盘价 | fund_5min | history | history_panel,strategy |
| close | 5min | FT | 期货5分钟K线 - 收盘价 | future_5min | history | history_panel,strategy |
| close | 5min | IDX | 指数5分钟K线 - 收盘价 | index_5min | history | history_panel,strategy |
| close | 5min | OPT | 期权5分钟K线 - 收盘价 | options_5min | history | history_panel,strategy |
| close | d | E | 股票日K线 - 收盘价 | stock_daily | history | history_panel,strategy |
| close | d | FD | 基金日K线 - 收盘价 | fund_daily | history | history_panel,strategy |
| close | d | FT | 期货日K线 - 收盘价 | future_daily | history | history_panel,strategy |
| close | d | IDX | 指数日K线 - 收盘价 | index_daily | history | history_panel,strategy |
| close | d | OPT | 期权日K线 - 收盘价 | options_daily | history | history_panel,strategy |
| close | h | E | 股票小时K线 - 收盘价 | stock_hourly | history | history_panel,strategy |
| close | h | FD | 基金小时K线 - 收盘价 | fund_hourly | history | history_panel,strategy |
| close | h | FT | 期货小时K线 - 收盘价 | future_hourly | history | history_panel,strategy |
| close | h | IDX | 指数小时K线 - 收盘价 | index_hourly | history | history_panel,strategy |
| close | h | OPT | 期权小时K线 - 收盘价 | options_hourly | history | history_panel,strategy |
| close | m | E | 股票月K线 - 收盘价 | stock_monthly | history | history_panel,strategy |
| close | m | FD | 基金月K线 - 收盘价 | fund_monthly | history | history_panel,strategy |
| close | m | FT | 期货月K线 - 收盘价 | future_monthly | history | history_panel,strategy |
| close | m | IDX | 指数月K线 - 收盘价 | index_monthly | history | history_panel,strategy |
| close | w | E | 股票周K线 - 收盘价 | stock_weekly | history | history_panel,strategy |
| close | w | FD | 基金周K线 - 收盘价 | fund_weekly | history | history_panel,strategy |
| close | w | FT | 期货周K线 - 收盘价 | future_weekly | history | history_panel,strategy |
| close | w | IDX | 指数周K线 - 收盘价 | index_weekly | history | history_panel,strategy |
| close_chg | d | FT | 期货日K线 - 收盘价涨跌 | future_daily | history | history_panel,strategy |
| close_chg | m | FT | 期货月K线 - 收盘价涨跌 | future_monthly | history | history_panel,strategy |
| close_chg | w | FT | 期货周K线 - 收盘价涨跌 | future_weekly | history | history_panel,strategy |
| cogs_of_sales | q | E | 上市公司财务指标 - 销售成本率 | financial | history | history_panel,strategy |
| comm_exp | q | E | 上市公司利润表 - 减:手续费及佣金支出 | income | history | history_panel,strategy |
| comm_income | q | E | 上市公司利润表 - 手续费及佣金收入 | income | history | history_panel,strategy |
| comm_payable | q | E | 上市公司资产负债表 - 应付手续费及佣金 | balance | history | history_panel,strategy |
| compens_payout | q | E | 上市公司利润表 - 赔付总支出 | income | history | history_panel,strategy |
| compens_payout_refu | q | E | 上市公司利润表 - 减:摊回赔付支出 | income | history | history_panel,strategy |
| compr_inc_attr_m_s | q | E | 上市公司利润表 - 归属于少数股东的综合收益总额 | income | history | history_panel,strategy |
| compr_inc_attr_p | q | E | 上市公司利润表 - 归属于母公司(或股东)的综合收益总额 | income | history | history_panel,strategy |
| comshare_payable_dvd | q | E | 上市公司利润表 - 应付普通股股利 | income | history | history_panel,strategy |
| const_materials | q | E | 上市公司资产负债表 - 工程物资 | balance | history | history_panel,strategy |
| continued_net_profit | q | E | 上市公司利润表 - 持续经营净利润 | income | history | history_panel,strategy |
| contract_assets | q | E | 上市公司资产负债表 - 合同资产 | balance | history | history_panel,strategy |
| contract_liab | q | E | 上市公司资产负债表 - 合同负债 | balance | history | history_panel,strategy |
| conv_copbonds_due_within_1y | q | E | 上市公司现金流量表 - 一年内到期的可转换公司债券 | cashflow | history | history_panel,strategy |
| conv_debt_into_cap | q | E | 上市公司现金流量表 - 债务转为资本 | cashflow | history | history_panel,strategy |
| cost_fin_assets | q | E | 上市公司资产负债表 - 以摊余成本计量的金融资产 | balance | history | history_panel,strategy |
| current_exint | q | E | 上市公司财务指标 - 无息流动负债 | financial | history | history_panel,strategy |
| current_ratio | q | E | 上市公司财务指标 - 流动比率 | financial | history | history_panel,strategy |
| currentdebt_to_debt | q | E | 上市公司财务指标 - 流动负债/负债合计 | financial | history | history_panel,strategy |
| daa | q | E | 上市公司财务指标 - 折旧与摊销 | financial | history | history_panel,strategy |
| debt_invest | q | E | 上市公司资产负债表 - 债权投资(元) | balance | history | history_panel,strategy |
| debt_to_assets | q | E | 上市公司财务指标 - 资产负债率 | financial | history | history_panel,strategy |
| debt_to_eqt | q | E | 上市公司财务指标 - 产权比率 | financial | history | history_panel,strategy |
| decr_def_inc_tax_assets | q | E | 上市公司现金流量表 - 递延所得税资产减少 | cashflow | history | history_panel,strategy |
| decr_deferred_exp | q | E | 上市公司现金流量表 - 待摊费用减少 | cashflow | history | history_panel,strategy |
| decr_in_disbur | q | E | 上市公司资产负债表 - 发放贷款及垫款 | balance | history | history_panel,strategy |
| decr_inventories | q | E | 上市公司现金流量表 - 存货的减少 | cashflow | history | history_panel,strategy |
| decr_oper_payable | q | E | 上市公司现金流量表 - 经营性应收项目的减少 | cashflow | history | history_panel,strategy |
| defer_inc_non_cur_liab | q | E | 上市公司资产负债表 - 递延收益-非流动负债 | balance | history | history_panel,strategy |
| defer_tax_assets | q | E | 上市公司资产负债表 - 递延所得税资产 | balance | history | history_panel,strategy |
| defer_tax_liab | q | E | 上市公司资产负债表 - 递延所得税负债 | balance | history | history_panel,strategy |
| deferred_inc | q | E | 上市公司资产负债表 - 递延收益 | balance | history | history_panel,strategy |
| delf_settle | d | FT | 期货日K线 - 交割结算价 | future_daily | history | history_panel,strategy |
| delf_settle | m | FT | 期货月K线 - 交割结算价 | future_monthly | history | history_panel,strategy |
| delf_settle | w | FT | 期货周K线 - 交割结算价 | future_weekly | history | history_panel,strategy |
| depos | q | E | 上市公司资产负债表 - 吸收存款 | balance | history | history_panel,strategy |
| depos_ib_deposits | q | E | 上市公司资产负债表 - 吸收存款及同业存放 | balance | history | history_panel,strategy |
| depos_in_oth_bfi | q | E | 上市公司资产负债表 - 存放同业和其它金融机构款项 | balance | history | history_panel,strategy |
| depos_oth_bfi | q | E | 上市公司资产负债表 - 同业和其它金融机构存放款项 | balance | history | history_panel,strategy |
| depos_received | q | E | 上市公司资产负债表 - 存入保证金 | balance | history | history_panel,strategy |
| depr_fa_coga_dpba | q | E | 上市公司现金流量表 - 固定资产折旧、油气资产折耗、生产性生物资产折旧 | cashflow | history | history_panel,strategy |
| deriv_assets | q | E | 上市公司资产负债表 - 衍生金融资产 | balance | history | history_panel,strategy |
| deriv_liab | q | E | 上市公司资产负债表 - 衍生金融负债 | balance | history | history_panel,strategy |
| diluted2_eps | q | E | 上市公司财务指标 - 期末摊薄每股收益 | financial | history | history_panel,strategy |
| diluted_eps | q | E | 上市公司利润表 - 稀释每股收益 | income | history | history_panel,strategy |
| diluted_roe | q | E | 上市公司业绩快报 - 净资产收益率(摊薄)(%) | express | history | history_panel,strategy |
| distable_profit | q | E | 上市公司利润表 - 可分配利润 | income | history | history_panel,strategy |
| distr_profit_shrhder | q | E | 上市公司利润表 - 可供股东分配的利润 | income | history | history_panel,strategy |
| div_payable | q | E | 上市公司资产负债表 - 应付股利 | balance | history | history_panel,strategy |
| div_payt | q | E | 上市公司利润表 - 保户红利支出 | income | history | history_panel,strategy |
| div_receiv | q | E | 上市公司资产负债表 - 应收股利 | balance | history | history_panel,strategy |
| down_limit | d | E | 跌停板 - 跌停价 | stock_limit | history | history_panel,strategy |
| dp_assets_to_eqt | q | E | 上市公司财务指标 - 权益乘数(杜邦分析) | financial | history | history_panel,strategy |
| dt_eps | q | E | 上市公司财务指标 - 稀释每股收益 | financial | history | history_panel,strategy |
| dt_eps_yoy | q | E | 上市公司财务指标 - 稀释每股收益同比增长率(%) | financial | history | history_panel,strategy |
| dt_netprofit_yoy | q | E | 上市公司财务指标 - 归属母公司股东的净利润-扣除非经常损益同比增长率(%) | financial | history | history_panel,strategy |
| dtprofit_to_profit | q | E | 上市公司财务指标 - 扣除非经常损益后的净利润/净利润 | financial | history | history_panel,strategy |
| dv_ratio | d | E | 股票技术指标 - 股息率 （%） | stock_indicator | history | history_panel,strategy |
| dv_ttm | d | E | 股票技术指标 - 股息率（TTM）（%） | stock_indicator | history | history_panel,strategy |
| ebit | q | E | 上市公司财务指标 - 息税前利润 | financial | history | history_panel,strategy |
| ebit_of_gr | q | E | 上市公司财务指标 - 息税前利润/营业总收入 | financial | history | history_panel,strategy |
| ebit_ps | q | E | 上市公司财务指标 - 每股息税前利润 | financial | history | history_panel,strategy |
| ebit_to_interest | q | E | 上市公司财务指标 - 已获利息倍数(EBIT/利息费用) | financial | history | history_panel,strategy |
| ebitda | q | E | 上市公司财务指标 - 息税折旧摊销前利润 | financial | history | history_panel,strategy |
| ebitda_to_debt | q | E | 上市公司财务指标 - 息税折旧摊销前利润/负债合计 | financial | history | history_panel,strategy |
| ebt_yoy | q | E | 上市公司财务指标 - 利润总额同比增长率(%) | financial | history | history_panel,strategy |
| eff_fx_flu_cash | q | E | 上市公司现金流量表 - 汇率变动对现金的影响 | cashflow | history | history_panel,strategy |
| end_bal_cash | q | E | 上市公司现金流量表 - 现金的期末余额 | cashflow | history | history_panel,strategy |
| end_bal_cash_equ | q | E | 上市公司现金流量表 - 加:现金等价物的期末余额 | cashflow | history | history_panel,strategy |
| end_net_profit | q | E | 上市公司利润表 - 终止经营净利润 | income | history | history_panel,strategy |
| eps | q | E | 上市公司财务指标 - 基本每股收益 | financial | history | history_panel,strategy |
| eps_last_year | q | E | 上市公司业绩快报 - 去年同期每股收益 | express | history | history_panel,strategy |
| eqt_to_debt | q | E | 上市公司财务指标 - 归属于母公司的股东权益/负债合计 | financial | history | history_panel,strategy |
| eqt_to_interestdebt | q | E | 上市公司财务指标 - 归属于母公司的股东权益/带息债务 | financial | history | history_panel,strategy |
| eqt_to_talcapital | q | E | 上市公司财务指标 - 归属于母公司的股东权益/全部投入资本 | financial | history | history_panel,strategy |
| eqt_yoy | q | E | 上市公司财务指标 - 归属母公司的股东权益相对年初增长率(%) | financial | history | history_panel,strategy |
| equity_yoy | q | E | 上市公司财务指标 - 净资产同比增长率 | financial | history | history_panel,strategy |
| estimated_liab | q | E | 上市公司资产负债表 - 预计负债 | balance | history | history_panel,strategy |
| expense_of_sales | q | E | 上市公司财务指标 - 销售期间费用率 | financial | history | history_panel,strategy |
| express_bps | q | E | 上市公司财务指标 - 每股净资产 | financial | history | history_panel,strategy |
| express_diluted_eps | q | E | 上市公司业绩快报 - 每股收益(摊薄)(元) | express | history | history_panel,strategy |
| express_n_income | q | E | 上市公司业绩快报 - 净利润(元) | express | history | history_panel,strategy |
| express_operate_profit | q | E | 上市公司业绩快报 - 营业利润(元) | express | history | history_panel,strategy |
| express_revenue | q | E | 上市公司业绩快报 - 营业收入(元) | express | history | history_panel,strategy |
| express_total_assets | q | E | 上市公司业绩快报 - 总资产(元) | express | history | history_panel,strategy |
| express_total_hldr_eqy_exc_min_int | q | E | 上市公司业绩快报 - 股东权益合计(不含少数股东权益)(元) | express | history | history_panel,strategy |
| express_total_profit | q | E | 上市公司业绩快报 - 利润总额(元) | express | history | history_panel,strategy |
| extra_item | q | E | 上市公司财务指标 - 非经常性损益 | financial | history | history_panel,strategy |
| fa_avail_for_sale | q | E | 上市公司资产负债表 - 可供出售金融资产 | balance | history | history_panel,strategy |
| fa_fnc_leases | q | E | 上市公司现金流量表 - 融资租入固定资产 | cashflow | history | history_panel,strategy |
| fa_turn | q | E | 上市公司财务指标 - 固定资产周转率 | financial | history | history_panel,strategy |
| fair_value_fin_assets | q | E | 上市公司资产负债表 - 以公允价值计量且其变动计入其他综合收益的金融资产 | balance | history | history_panel,strategy |
| fcfe | q | E | 上市公司财务指标 - 股权自由现金流量 | financial | history | history_panel,strategy |
| fcfe_ps | q | E | 上市公司财务指标 - 每股股东自由现金流量 | financial | history | history_panel,strategy |
| fcff | q | E | 上市公司财务指标 - 企业自由现金流量 | financial | history | history_panel,strategy |
| fcff_ps | q | E | 上市公司财务指标 - 每股企业自由现金流量 | financial | history | history_panel,strategy |
| fd_share | d | FD | 基金份额（万） | fund_share | history | history_panel,strategy |
| fin_exp | q | E | 上市公司利润表 - 减:财务费用 | income | history | history_panel,strategy |
| fin_exp_int_exp | q | E | 上市公司利润表 - 财务费用:利息费用 | income | history | history_panel,strategy |
| fin_exp_int_inc | q | E | 上市公司利润表 - 财务费用:利息收入 | income | history | history_panel,strategy |
| finaexp_of_gr | q | E | 上市公司财务指标 - 财务费用/营业总收入 | financial | history | history_panel,strategy |
| finan_exp | q | E | 上市公司现金流量表 - 财务费用 | cashflow | history | history_panel,strategy |
| fix_assets | q | E | 上市公司资产负债表 - 固定资产 | balance | history | history_panel,strategy |
| fix_assets_total | q | E | 上市公司资产负债表 - 固定资产(合计)(元) | balance | history | history_panel,strategy |
| fixed_assets | q | E | 上市公司财务指标 - 固定资产合计 | financial | history | history_panel,strategy |
| fixed_assets_disp | q | E | 上市公司资产负债表 - 固定资产清理 | balance | history | history_panel,strategy |
| float_mv | d | IDX | 指数技术指标 - 当日流通市值（元） | index_indicator | history | history_panel,strategy |
| float_mv_2 | d | E | 股票技术指标 - 流通市值(亿元) | stock_indicator2 | history | history_panel,strategy |
| float_share | d | E | 股票技术指标 - 流通股本 （万股） | stock_indicator | history | history_panel,strategy |
| float_share | d | IDX | 指数技术指标 - 当日流通股本（股） | index_indicator | history | history_panel,strategy |
| float_share_b | d | E | 股票技术指标 - 流通股本(亿) | stock_indicator2 | history | history_panel,strategy |
| forex_differ | q | E | 上市公司资产负债表 - 外币报表折算差额 | balance | history | history_panel,strategy |
| forex_gain | q | E | 上市公司利润表 - 加:汇兑净收益 | income | history | history_panel,strategy |
| free_cashflow | q | E | 上市公司现金流量表 - 企业自由现金流量 | cashflow | history | history_panel,strategy |
| free_share | d | E | 股票技术指标 - 自由流通股本（万） | stock_indicator | history | history_panel,strategy |
| free_share | d | IDX | 指数技术指标 - 当日自由流通股本（股） | index_indicator | history | history_panel,strategy |
| fv_value_chg_gain | q | E | 上市公司利润表 - 加:公允价值变动净收益 | income | history | history_panel,strategy |
| g_index_amount | d | IDX | 全球指数日K线行情 - 成交额 | global_index_daily | history | history_panel,strategy |
| g_index_change | d | IDX | 全球指数日K线行情 - 最低价 | global_index_daily | history | history_panel,strategy |
| g_index_close | d | IDX | 全球指数日K线行情 - 收盘价 | global_index_daily | history | history_panel,strategy |
| g_index_high | d | IDX | 全球指数日K线行情 - 最高价 | global_index_daily | history | history_panel,strategy |
| g_index_low | d | IDX | 全球指数日K线行情 - 最低价 | global_index_daily | history | history_panel,strategy |
| g_index_open | d | IDX | 全球指数日K线行情 - 开盘价 | global_index_daily | history | history_panel,strategy |
| g_index_pct_change | d | IDX | 全球指数日K线行情 - 收盘价 | global_index_daily | history | history_panel,strategy |
| g_index_pre_close | d | IDX | 全球指数日K线行情 - 昨日收盘价 | global_index_daily | history | history_panel,strategy |
| g_index_swing | d | IDX | 全球指数日K线行情 - 振幅 | global_index_daily | history | history_panel,strategy |
| g_index_vol | d | IDX | 全球指数日K线行情 - 成交量 | global_index_daily | history | history_panel,strategy |
| gc_of_gr | q | E | 上市公司财务指标 - 营业总成本/营业总收入 | financial | history | history_panel,strategy |
| goodwill | q | E | 上市公司资产负债表 - 商誉 | balance | history | history_panel,strategy |
| gross_margin | q | E | 上市公司财务指标 - 毛利 | financial | history | history_panel,strategy |
| grossprofit_margin | q | E | 上市公司财务指标 - 销售毛利率 | financial | history | history_panel,strategy |
| growth_assets | q | E | 上市公司业绩快报 - 比年初增长率:总资产 | express | history | history_panel,strategy |
| growth_bps | q | E | 上市公司业绩快报 - 比年初增长率:归属于母公司股东的每股净资产 | express | history | history_panel,strategy |
| hfs_assets | q | E | 上市公司资产负债表 - 持有待售的资产 | balance | history | history_panel,strategy |
| hfs_sales | q | E | 上市公司资产负债表 - 持有待售的负债 | balance | history | history_panel,strategy |
| high | 15min | E | 股票15分钟K线 - 最高价 | stock_15min | history | history_panel,strategy |
| high | 15min | FD | 基金15分钟K线 - 最高价 | fund_15min | history | history_panel,strategy |
| high | 15min | FT | 期货15分钟K线 - 最高价 | future_15min | history | history_panel,strategy |
| high | 15min | IDX | 指数15分钟K线 - 最高价 | index_15min | history | history_panel,strategy |
| high | 15min | OPT | 期权15分钟K线 - 最高价 | options_15min | history | history_panel,strategy |
| high | 1min | E | 股票60秒K线 - 最高价 | stock_1min | history | history_panel,strategy |
| high | 1min | FD | 基金60秒K线 - 最高价 | fund_1min | history | history_panel,strategy |
| high | 1min | FT | 期货60秒K线 - 最高价 | future_1min | history | history_panel,strategy |
| high | 1min | IDX | 指数60秒K线 - 最高价 | index_1min | history | history_panel,strategy |
| high | 1min | OPT | 期权60秒K线 - 最高价 | options_1min | history | history_panel,strategy |
| high | 30min | E | 股票30分钟K线 - 最高价 | stock_30min | history | history_panel,strategy |
| high | 30min | FD | 基金30分钟K线 - 最高价 | fund_30min | history | history_panel,strategy |
| high | 30min | FT | 期货30分钟K线 - 最高价 | future_30min | history | history_panel,strategy |
| high | 30min | IDX | 指数30分钟K线 - 最高价 | index_30min | history | history_panel,strategy |
| high | 30min | OPT | 期权30分钟K线 - 最高价 | options_30min | history | history_panel,strategy |
| high | 5min | E | 股票5分钟K线 - 最高价 | stock_5min | history | history_panel,strategy |
| high | 5min | FD | 基金5分钟K线 - 最高价 | fund_5min | history | history_panel,strategy |
| high | 5min | FT | 期货5分钟K线 - 最高价 | future_5min | history | history_panel,strategy |
| high | 5min | IDX | 指数5分钟K线 - 最高价 | index_5min | history | history_panel,strategy |
| high | 5min | OPT | 期权5分钟K线 - 最高价 | options_5min | history | history_panel,strategy |
| high | d | E | 股票日K线 - 最高价 | stock_daily | history | history_panel,strategy |
| high | d | FD | 基金日K线 - 最高价 | fund_daily | history | history_panel,strategy |
| high | d | FT | 期货日K线 - 最高价 | future_daily | history | history_panel,strategy |
| high | d | IDX | 指数日K线 - 最高价 | index_daily | history | history_panel,strategy |
| high | d | OPT | 期权日K线 - 最高价 | options_daily | history | history_panel,strategy |
| high | h | E | 股票小时K线 - 最高价 | stock_hourly | history | history_panel,strategy |
| high | h | FD | 基金小时K线 - 最高价 | fund_hourly | history | history_panel,strategy |
| high | h | FT | 期货小时K线 - 最高价 | future_hourly | history | history_panel,strategy |
| high | h | IDX | 指数小时K线 - 最高价 | index_hourly | history | history_panel,strategy |
| high | h | OPT | 期权小时K线 - 最高价 | options_hourly | history | history_panel,strategy |
| high | m | E | 股票月K线 - 最高价 | stock_monthly | history | history_panel,strategy |
| high | m | FD | 基金月K线 - 最高价 | fund_monthly | history | history_panel,strategy |
| high | m | FT | 期货月K线 - 最高价 | future_monthly | history | history_panel,strategy |
| high | m | IDX | 指数月K线 - 最高价 | index_monthly | history | history_panel,strategy |
| high | w | E | 股票周K线 - 最高价 | stock_weekly | history | history_panel,strategy |
| high | w | FD | 基金周K线 - 最高价 | fund_weekly | history | history_panel,strategy |
| high | w | FT | 期货周K线 - 最高价 | future_weekly | history | history_panel,strategy |
| high | w | IDX | 指数周K线 - 最高价 | index_weekly | history | history_panel,strategy |
| hk_top10_amount | d | E | 港股通十大成交 - 累计成交额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_close | d | E | 港股通十大成交 - 收盘价 | hk_top10_stock | history | history_panel,strategy |
| hk_top10_net_amount | d | E | 港股通十大成交 - 净买入金额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_p_change | d | E | 港股通十大成交 - 涨跌幅 | hk_top10_stock | history | history_panel,strategy |
| hk_top10_rank | d | E | 港股通十大成交 - 排名 | hk_top10_stock | history | history_panel,strategy |
| hk_top10_sh_amount | d | E | 港股通十大成交 - 沪市成交额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_sh_buy | d | E | 港股通十大成交 - 深市净买入金额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_sh_net_amount | d | E | 港股通十大成交 - 沪市净买入额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_sh_sell | d | E | 港股通十大成交 - 深市净买入金额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_sz_amount | d | E | 港股通十大成交 - 深市成交金额（元） | hk_top10_stock | history | history_panel,strategy |
| hk_top10_sz_net_amount | d | E | 港股通十大成交 - 深市净买入额（元） | hk_top10_stock | history | history_panel,strategy |
| htm_invest | q | E | 上市公司资产负债表 - 持有至到期投资 | balance | history | history_panel,strategy |
| ifc_cash_incr | q | E | 上市公司现金流量表 - 收取利息和手续费净增加额 | cashflow | history | history_panel,strategy |
| im_n_incr_cash_equ | q | E | 上市公司现金流量表 - 现金及现金等价物净增加额(间接法) | cashflow | history | history_panel,strategy |
| im_net_cashflow_oper_act | q | E | 上市公司现金流量表 - 经营活动产生的现金流量净额(间接法) | cashflow | history | history_panel,strategy |
| impai_ttm | q | E | 上市公司财务指标 - 资产减值损失/营业总收入 | financial | history | history_panel,strategy |
| incl_cash_rec_saims | q | E | 上市公司现金流量表 - 其中:子公司吸收少数股东投资收到的现金 | cashflow | history | history_panel,strategy |
| incl_dvd_profit_paid_sc_ms | q | E | 上市公司现金流量表 - 其中:子公司支付给少数股东的股利、利润 | cashflow | history | history_panel,strategy |
| income_credit_impa_loss | q | E | 上市公司利润表 - 信用减值损失 | income | history | history_panel,strategy |
| income_ebit | q | E | 上市公司利润表 - 息税前利润 | income | history | history_panel,strategy |
| income_ebitda | q | E | 上市公司利润表 - 息税折旧摊销前利润 | income | history | history_panel,strategy |
| income_rd_exp | q | E | 上市公司利润表 - 研发费用 | income | history | history_panel,strategy |
| income_tax | q | E | 上市公司利润表 - 所得税费用 | income | history | history_panel,strategy |
| incr_acc_exp | q | E | 上市公司现金流量表 - 预提费用增加 | cashflow | history | history_panel,strategy |
| incr_def_inc_tax_liab | q | E | 上市公司现金流量表 - 递延所得税负债增加 | cashflow | history | history_panel,strategy |
| incr_oper_payable | q | E | 上市公司现金流量表 - 经营性应付项目的增加 | cashflow | history | history_panel,strategy |
| indem_payable | q | E | 上市公司资产负债表 - 应付赔付款 | balance | history | history_panel,strategy |
| indep_acct_assets | q | E | 上市公司资产负债表 - 独立账户资产 | balance | history | history_panel,strategy |
| indept_acc_liab | q | E | 上市公司资产负债表 - 独立账户负债 | balance | history | history_panel,strategy |
| insur_reser_refu | q | E | 上市公司利润表 - 减:摊回保险责任准备金 | income | history | history_panel,strategy |
| insurance_exp | q | E | 上市公司利润表 - 保险业务支出 | income | history | history_panel,strategy |
| int_exp | q | E | 上市公司利润表 - 减:利息支出 | income | history | history_panel,strategy |
| int_income | q | E | 上市公司利润表 - 利息收入 | income | history | history_panel,strategy |
| int_payable | q | E | 上市公司资产负债表 - 应付利息 | balance | history | history_panel,strategy |
| int_receiv | q | E | 上市公司资产负债表 - 应收利息 | balance | history | history_panel,strategy |
| int_to_talcap | q | E | 上市公司财务指标 - 带息债务/全部投入资本 | financial | history | history_panel,strategy |
| intan_assets | q | E | 上市公司资产负债表 - 无形资产 | balance | history | history_panel,strategy |
| interestdebt | q | E | 上市公司财务指标 - 带息债务 | financial | history | history_panel,strategy |
| interst_income | q | E | 上市公司财务指标 - 利息费用 | financial | history | history_panel,strategy |
| interval_3 | d | E | 股票技术指标 - 近3月涨幅 | stock_indicator2 | history | history_panel,strategy |
| interval_6 | d | E | 股票技术指标 - 近6月涨幅 | stock_indicator2 | history | history_panel,strategy |
| inv_turn | q | E | 上市公司财务指标 - 存货周转率 | financial | history | history_panel,strategy |
| inventories | q | E | 上市公司资产负债表 - 存货 | balance | history | history_panel,strategy |
| invest_as_receiv | q | E | 上市公司资产负债表 - 应收款项类投资 | balance | history | history_panel,strategy |
| invest_capital | q | E | 上市公司财务指标 - 全部投入资本 | financial | history | history_panel,strategy |
| invest_income | q | E | 上市公司利润表 - 加:投资净收益 | income | history | history_panel,strategy |
| invest_loss | q | E | 上市公司现金流量表 - 投资损失 | cashflow | history | history_panel,strategy |
| invest_loss_unconf | q | E | 上市公司资产负债表 - 未确认的投资损失 | balance | history | history_panel,strategy |
| invest_real_estate | q | E | 上市公司资产负债表 - 投资性房地产 | balance | history | history_panel,strategy |
| investincome_of_ebt | q | E | 上市公司财务指标 - 价值变动净收益/利润总额 | financial | history | history_panel,strategy |
| invturn_days | q | E | 上市公司财务指标 - 存货周转天数 | financial | history | history_panel,strategy |
| lease_liab | q | E | 上市公司资产负债表 - 租赁负债 | balance | history | history_panel,strategy |
| lending_funds | q | E | 上市公司资产负债表 - 融出资金 | balance | history | history_panel,strategy |
| loan_oth_bank | q | E | 上市公司资产负债表 - 拆入资金 | balance | history | history_panel,strategy |
| loanto_oth_bank_fi | q | E | 上市公司资产负债表 - 拆出资金 | balance | history | history_panel,strategy |
| long_pay_total | q | E | 上市公司资产负债表 - 长期应付款(合计)(元) | balance | history | history_panel,strategy |
| longdeb_to_debt | q | E | 上市公司财务指标 - 非流动负债/负债合计 | financial | history | history_panel,strategy |
| longdebt_to_workingcapital | q | E | 上市公司财务指标 - 长期债务与营运资金比率 | financial | history | history_panel,strategy |
| loss_disp_fiolta | q | E | 上市公司现金流量表 - 处置固定、无形资产和其他长期资产的损失 | cashflow | history | history_panel,strategy |
| loss_fv_chg | q | E | 上市公司现金流量表 - 公允价值变动损失 | cashflow | history | history_panel,strategy |
| loss_scr_fa | q | E | 上市公司现金流量表 - 固定资产报废损失 | cashflow | history | history_panel,strategy |
| low | 15min | E | 股票15分钟K线 - 最低价 | stock_15min | history | history_panel,strategy |
| low | 15min | FD | 基金15分钟K线 - 最低价 | fund_15min | history | history_panel,strategy |
| low | 15min | FT | 期货15分钟K线 - 最低价 | future_15min | history | history_panel,strategy |
| low | 15min | IDX | 指数15分钟K线 - 最低价 | index_15min | history | history_panel,strategy |
| low | 15min | OPT | 期权15分钟K线 - 最低价 | options_15min | history | history_panel,strategy |
| low | 1min | E | 股票60秒K线 - 最低价 | stock_1min | history | history_panel,strategy |
| low | 1min | FD | 基金60秒K线 - 最低价 | fund_1min | history | history_panel,strategy |
| low | 1min | FT | 期货60秒K线 - 最低价 | future_1min | history | history_panel,strategy |
| low | 1min | IDX | 指数60秒K线 - 最低价 | index_1min | history | history_panel,strategy |
| low | 1min | OPT | 期权60秒K线 - 最低价 | options_1min | history | history_panel,strategy |
| low | 30min | E | 股票30分钟K线 - 最低价 | stock_30min | history | history_panel,strategy |
| low | 30min | FD | 基金30分钟K线 - 最低价 | fund_30min | history | history_panel,strategy |
| low | 30min | FT | 期货30分钟K线 - 最低价 | future_30min | history | history_panel,strategy |
| low | 30min | IDX | 指数30分钟K线 - 最低价 | index_30min | history | history_panel,strategy |
| low | 30min | OPT | 期权30分钟K线 - 最低价 | options_30min | history | history_panel,strategy |
| low | 5min | E | 股票5分钟K线 - 最低价 | stock_5min | history | history_panel,strategy |
| low | 5min | FD | 基金5分钟K线 - 最低价 | fund_5min | history | history_panel,strategy |
| low | 5min | FT | 期货5分钟K线 - 最低价 | future_5min | history | history_panel,strategy |
| low | 5min | IDX | 指数5分钟K线 - 最低价 | index_5min | history | history_panel,strategy |
| low | 5min | OPT | 期权5分钟K线 - 最低价 | options_5min | history | history_panel,strategy |
| low | d | E | 股票日K线 - 最低价 | stock_daily | history | history_panel,strategy |
| low | d | FD | 基金日K线 - 最低价 | fund_daily | history | history_panel,strategy |
| low | d | FT | 期货日K线 - 最低价 | future_daily | history | history_panel,strategy |
| low | d | IDX | 指数日K线 - 最低价 | index_daily | history | history_panel,strategy |
| low | d | OPT | 期权日K线 - 最低价 | options_daily | history | history_panel,strategy |
| low | h | E | 股票小时K线 - 最低价 | stock_hourly | history | history_panel,strategy |
| low | h | FD | 基金小时K线 - 最低价 | fund_hourly | history | history_panel,strategy |
| low | h | FT | 期货小时K线 - 最低价 | future_hourly | history | history_panel,strategy |
| low | h | IDX | 指数小时K线 - 最低价 | index_hourly | history | history_panel,strategy |
| low | h | OPT | 期权小时K线 - 最低价 | options_hourly | history | history_panel,strategy |
| low | m | E | 股票月K线 - 最低价 | stock_monthly | history | history_panel,strategy |
| low | m | FD | 基金月K线 - 最低价 | fund_monthly | history | history_panel,strategy |
| low | m | FT | 期货月K线 - 最低价 | future_monthly | history | history_panel,strategy |
| low | m | IDX | 指数月K线 - 最低价 | index_monthly | history | history_panel,strategy |
| low | w | E | 股票周K线 - 最低价 | stock_weekly | history | history_panel,strategy |
| low | w | FD | 基金周K线 - 最低价 | fund_weekly | history | history_panel,strategy |
| low | w | FT | 期货周K线 - 最低价 | future_weekly | history | history_panel,strategy |
| low | w | IDX | 指数周K线 - 最低价 | index_weekly | history | history_panel,strategy |
| lt_amor_exp | q | E | 上市公司资产负债表 - 长期待摊费用 | balance | history | history_panel,strategy |
| lt_amort_deferred_exp | q | E | 上市公司现金流量表 - 长期待摊费用摊销 | cashflow | history | history_panel,strategy |
| lt_borr | q | E | 上市公司资产负债表 - 长期借款 | balance | history | history_panel,strategy |
| lt_eqt_invest | q | E | 上市公司资产负债表 - 长期股权投资 | balance | history | history_panel,strategy |
| lt_payable | q | E | 上市公司资产负债表 - 长期应付款 | balance | history | history_panel,strategy |
| lt_payroll_payable | q | E | 上市公司资产负债表 - 长期应付职工薪酬 | balance | history | history_panel,strategy |
| lt_rec | q | E | 上市公司资产负债表 - 长期应收款 | balance | history | history_panel,strategy |
| minority_gain | q | E | 上市公司利润表 - 少数股东损益 | income | history | history_panel,strategy |
| minority_int | q | E | 上市公司资产负债表 - 少数股东权益 | balance | history | history_panel,strategy |
| money_cap | q | E | 上市公司资产负债表 - 货币资金 | balance | history | history_panel,strategy |
| n_asset_mg_income | q | E | 上市公司利润表 - 受托客户资产管理业务净收入 | income | history | history_panel,strategy |
| n_cap_incr_repur | q | E | 上市公司现金流量表 - 回购业务资金净增加额 | cashflow | history | history_panel,strategy |
| n_cash_flows_fnc_act | q | E | 上市公司现金流量表 - 筹资活动产生的现金流量净额 | cashflow | history | history_panel,strategy |
| n_cashflow_act | q | E | 上市公司现金流量表 - 经营活动产生的现金流量净额 | cashflow | history | history_panel,strategy |
| n_cashflow_inv_act | q | E | 上市公司现金流量表 - 投资活动产生的现金流量净额 | cashflow | history | history_panel,strategy |
| n_commis_income | q | E | 上市公司利润表 - 手续费及佣金净收入 | income | history | history_panel,strategy |
| n_depos_incr_fi | q | E | 上市公司现金流量表 - 客户存款和同业存放款项净增加额 | cashflow | history | history_panel,strategy |
| n_disp_subs_oth_biz | q | E | 上市公司现金流量表 - 取得子公司及其他营业单位支付的现金净额 | cashflow | history | history_panel,strategy |
| n_inc_borr_oth_fi | q | E | 上市公司现金流量表 - 向其他金融机构拆入资金净增加额 | cashflow | history | history_panel,strategy |
| n_income_attr_p | q | E | 上市公司利润表 - 净利润(不含少数股东损益) | income | history | history_panel,strategy |
| n_incr_cash_cash_equ | q | E | 上市公司现金流量表 - 现金及现金等价物净增加额 | cashflow | history | history_panel,strategy |
| n_incr_clt_loan_adv | q | E | 上市公司现金流量表 - 客户贷款及垫款净增加额 | cashflow | history | history_panel,strategy |
| n_incr_dep_cbob | q | E | 上市公司现金流量表 - 存放央行和同业款项净增加额 | cashflow | history | history_panel,strategy |
| n_incr_disp_faas | q | E | 上市公司现金流量表 - 处置可供出售金融资产净增加额 | cashflow | history | history_panel,strategy |
| n_incr_disp_tfa | q | E | 上市公司现金流量表 - 处置交易性金融资产净增加额 | cashflow | history | history_panel,strategy |
| n_incr_insured_dep | q | E | 上市公司现金流量表 - 保户储金净增加额 | cashflow | history | history_panel,strategy |
| n_incr_loans_cb | q | E | 上市公司现金流量表 - 向中央银行借款净增加额 | cashflow | history | history_panel,strategy |
| n_incr_loans_oth_bank | q | E | 上市公司现金流量表 - 拆入资金净增加额 | cashflow | history | history_panel,strategy |
| n_incr_pledge_loan | q | E | 上市公司现金流量表 - 质押贷款净增加额 | cashflow | history | history_panel,strategy |
| n_op_profit_of_ebt | q | E | 上市公司财务指标 - 营业外收支净额/利润总额 | financial | history | history_panel,strategy |
| n_oth_b_income | q | E | 上市公司利润表 - 加:其他业务净收益 | income | history | history_panel,strategy |
| n_oth_income | q | E | 上市公司利润表 - 其他经营净收益 | income | history | history_panel,strategy |
| n_recp_disp_fiolta | q | E | 上市公司现金流量表 - 处置固定资产、无形资产和其他长期资产收回的现金净额 | cashflow | history | history_panel,strategy |
| n_recp_disp_sobu | q | E | 上市公司现金流量表 - 处置子公司及其他营业单位收到的现金净额 | cashflow | history | history_panel,strategy |
| n_reinsur_prem | q | E | 上市公司现金流量表 - 收到再保业务现金净额 | cashflow | history | history_panel,strategy |
| n_sec_tb_income | q | E | 上市公司利润表 - 代理买卖证券业务净收入 | income | history | history_panel,strategy |
| n_sec_uw_income | q | E | 上市公司利润表 - 证券承销业务净收入 | income | history | history_panel,strategy |
| nca_disploss | q | E | 上市公司利润表 - 其中:减:非流动资产处置净损失 | income | history | history_panel,strategy |
| nca_to_assets | q | E | 上市公司财务指标 - 非流动资产/总资产 | financial | history | history_panel,strategy |
| nca_within_1y | q | E | 上市公司资产负债表 - 一年内到期的非流动资产 | balance | history | history_panel,strategy |
| net_after_nr_lp_correct | q | E | 上市公司利润表 - 扣除非经常性损益后的净利润（更正前） | income | history | history_panel,strategy |
| net_asset | d | FD | 基金净值 - 资产净值 | fund_nav | history | history_panel,strategy |
| net_cash_rece_sec | q | E | 上市公司现金流量表 - 代理买卖证券收到的现金净额(元) | cashflow | history | history_panel,strategy |
| net_dism_capital_add | q | E | 上市公司现金流量表 - 拆出资金净增加额 | cashflow | history | history_panel,strategy |
| net_expo_hedging_benefits | q | E | 上市公司利润表 - 净敞口套期收益 | income | history | history_panel,strategy |
| net_income | q | E | 上市公司利润表 - 净利润(含少数股东损益) | income | history | history_panel,strategy |
| net_mf_amount | d | E | 个股资金流向 - 净流入额（万元） | money_flow | history | history_panel,strategy |
| net_mf_vol | d | E | 个股资金流向 - 净流入量（手） | money_flow | history | history_panel,strategy |
| net_profit | q | E | 上市公司现金流量表 - 净利润 | cashflow | history | history_panel,strategy |
| netdebt | q | E | 上市公司财务指标 - 净债务 | financial | history | history_panel,strategy |
| netprofit_margin | q | E | 上市公司财务指标 - 销售净利率 | financial | history | history_panel,strategy |
| netprofit_yoy | q | E | 上市公司财务指标 - 归属母公司股东的净利润同比增长率(%) | financial | history | history_panel,strategy |
| networking_capital | q | E | 上市公司财务指标 - 营运流动资本 | financial | history | history_panel,strategy |
| non_cur_liab_due_1y | q | E | 上市公司资产负债表 - 一年内到期的非流动负债 | balance | history | history_panel,strategy |
| non_op_profit | q | E | 上市公司财务指标 - 非营业利润 | financial | history | history_panel,strategy |
| non_oper_exp | q | E | 上市公司利润表 - 减:营业外支出 | income | history | history_panel,strategy |
| non_oper_income | q | E | 上市公司利润表 - 加:营业外收入 | income | history | history_panel,strategy |
| noncurrent_exint | q | E | 上市公司财务指标 - 无息非流动负债 | financial | history | history_panel,strategy |
| nop_to_ebt | q | E | 上市公司财务指标 - 非营业利润／利润总额 | financial | history | history_panel,strategy |
| notes_payable | q | E | 上市公司资产负债表 - 应付票据 | balance | history | history_panel,strategy |
| notes_receiv | q | E | 上市公司资产负债表 - 应收票据 | balance | history | history_panel,strategy |
| np_last_year | q | E | 上市公司业绩快报 - 去年同期净利润 | express | history | history_panel,strategy |
| npta | q | E | 上市公司财务指标 - 总资产净利润 | financial | history | history_panel,strategy |
| ocf_to_debt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/负债合计 | financial | history | history_panel,strategy |
| ocf_to_interestdebt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/带息债务 | financial | history | history_panel,strategy |
| ocf_to_netdebt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/净债务 | financial | history | history_panel,strategy |
| ocf_to_opincome | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/经营活动净收益 | financial | history | history_panel,strategy |
| ocf_to_or | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/营业收入 | financial | history | history_panel,strategy |
| ocf_to_profit | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额／营业利润 | financial | history | history_panel,strategy |
| ocf_to_shortdebt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/流动负债 | financial | history | history_panel,strategy |
| ocf_yoy | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额同比增长率(%) | financial | history | history_panel,strategy |
| ocfps | q | E | 上市公司财务指标 - 每股经营活动产生的现金流量净额 | financial | history | history_panel,strategy |
| oi | d | FT | 期货日K线 - 持仓量（手） | future_daily | history | history_panel,strategy |
| oi | m | FT | 期货月K线 - 持仓量（手） | future_monthly | history | history_panel,strategy |
| oi | w | FT | 期货周K线 - 持仓量（手） | future_weekly | history | history_panel,strategy |
| oi_chg | d | FT | 期货日K线 - 持仓量变化 | future_daily | history | history_panel,strategy |
| oi_chg | m | FT | 期货月K线 - 持仓量变化 | future_monthly | history | history_panel,strategy |
| oi_chg | w | FT | 期货周K线 - 持仓量变化 | future_weekly | history | history_panel,strategy |
| oil_and_gas_assets | q | E | 上市公司资产负债表 - 油气资产 | balance | history | history_panel,strategy |
| op_income | q | E | 上市公司财务指标 - 经营活动净收益 | financial | history | history_panel,strategy |
| op_last_year | q | E | 上市公司业绩快报 - 去年同期营业利润 | express | history | history_panel,strategy |
| op_of_gr | q | E | 上市公司财务指标 - 营业利润/营业总收入 | financial | history | history_panel,strategy |
| op_to_debt | q | E | 上市公司财务指标 - 营业利润／负债合计 | financial | history | history_panel,strategy |
| op_to_ebt | q | E | 上市公司财务指标 - 营业利润／利润总额 | financial | history | history_panel,strategy |
| op_to_liqdebt | q | E | 上市公司财务指标 - 营业利润／流动负债 | financial | history | history_panel,strategy |
| op_yoy | q | E | 上市公司财务指标 - 营业利润同比增长率(%) | financial | history | history_panel,strategy |
| open | 15min | E | 股票15分钟K线 - 开盘价 | stock_15min | history | history_panel,strategy |
| open | 15min | FD | 基金15分钟K线 - 开盘价 | fund_15min | history | history_panel,strategy |
| open | 15min | FT | 期货15分钟K线 - 开盘价 | future_15min | history | history_panel,strategy |
| open | 15min | IDX | 指数15分钟K线 - 开盘价 | index_15min | history | history_panel,strategy |
| open | 15min | OPT | 期权15分钟K线 - 开盘价 | options_15min | history | history_panel,strategy |
| open | 1min | E | 股票60秒K线 - 开盘价 | stock_1min | history | history_panel,strategy |
| open | 1min | FD | 基金60秒K线 - 开盘价 | fund_1min | history | history_panel,strategy |
| open | 1min | FT | 期货60秒K线 - 开盘价 | future_1min | history | history_panel,strategy |
| open | 1min | IDX | 指数60秒K线 - 开盘价 | index_1min | history | history_panel,strategy |
| open | 1min | OPT | 期权60秒K线 - 开盘价 | options_1min | history | history_panel,strategy |
| open | 30min | E | 股票30分钟K线 - 开盘价 | stock_30min | history | history_panel,strategy |
| open | 30min | FD | 基金30分钟K线 - 开盘价 | fund_30min | history | history_panel,strategy |
| open | 30min | FT | 期货30分钟K线 - 开盘价 | future_30min | history | history_panel,strategy |
| open | 30min | IDX | 指数30分钟K线 - 开盘价 | index_30min | history | history_panel,strategy |
| open | 30min | OPT | 期权30分钟K线 - 开盘价 | options_30min | history | history_panel,strategy |
| open | 5min | E | 股票5分钟K线 - 开盘价 | stock_5min | history | history_panel,strategy |
| open | 5min | FD | 基金5分钟K线 - 开盘价 | fund_5min | history | history_panel,strategy |
| open | 5min | FT | 期货5分钟K线 - 开盘价 | future_5min | history | history_panel,strategy |
| open | 5min | IDX | 指数5分钟K线 - 开盘价 | index_5min | history | history_panel,strategy |
| open | 5min | OPT | 期权5分钟K线 - 开盘价 | options_5min | history | history_panel,strategy |
| open | d | E | 股票日K线 - 开盘价 | stock_daily | history | history_panel,strategy |
| open | d | FD | 基金日K线 - 开盘价 | fund_daily | history | history_panel,strategy |
| open | d | FT | 期货日K线 - 开盘价 | future_daily | history | history_panel,strategy |
| open | d | IDX | 指数日K线 - 开盘价 | index_daily | history | history_panel,strategy |
| open | d | OPT | 期权日K线 - 开盘价 | options_daily | history | history_panel,strategy |
| open | h | E | 股票小时K线 - 开盘价 | stock_hourly | history | history_panel,strategy |
| open | h | FD | 基金小时K线 - 开盘价 | fund_hourly | history | history_panel,strategy |
| open | h | FT | 期货小时K线 - 开盘价 | future_hourly | history | history_panel,strategy |
| open | h | IDX | 指数小时K线 - 开盘价 | index_hourly | history | history_panel,strategy |
| open | h | OPT | 期权小时K线 - 开盘价 | options_hourly | history | history_panel,strategy |
| open | m | E | 股票月K线 - 开盘价 | stock_monthly | history | history_panel,strategy |
| open | m | FD | 基金月K线 - 开盘价 | fund_monthly | history | history_panel,strategy |
| open | m | FT | 期货月K线 - 开盘价 | future_monthly | history | history_panel,strategy |
| open | m | IDX | 指数月K线 - 开盘价 | index_monthly | history | history_panel,strategy |
| open | w | E | 股票周K线 - 开盘价 | stock_weekly | history | history_panel,strategy |
| open | w | FD | 基金周K线 - 开盘价 | fund_weekly | history | history_panel,strategy |
| open | w | FT | 期货周K线 - 开盘价 | future_weekly | history | history_panel,strategy |
| open | w | IDX | 指数周K线 - 开盘价 | index_weekly | history | history_panel,strategy |
| open_bps | q | E | 上市公司业绩快报 - 期初每股净资产 | express | history | history_panel,strategy |
| open_net_assets | q | E | 上市公司业绩快报 - 期初净资产 | express | history | history_panel,strategy |
| oper_cost | q | E | 上市公司利润表 - 减:营业成本 | income | history | history_panel,strategy |
| oper_exp | q | E | 上市公司利润表 - 营业支出 | income | history | history_panel,strategy |
| operate_profit | q | E | 上市公司利润表 - 营业利润 | income | history | history_panel,strategy |
| opincome_of_ebt | q | E | 上市公司财务指标 - 经营活动净收益/利润总额 | financial | history | history_panel,strategy |
| or_last_year | q | E | 上市公司业绩快报 - 去年同期营业收入 | express | history | history_panel,strategy |
| or_yoy | q | E | 上市公司财务指标 - 营业收入同比增长率(%) | financial | history | history_panel,strategy |
| ordin_risk_reser | q | E | 上市公司资产负债表 - 一般风险准备 | balance | history | history_panel,strategy |
| oth_assets | q | E | 上市公司资产负债表 - 其他资产 | balance | history | history_panel,strategy |
| oth_b_income | q | E | 上市公司利润表 - 其他业务收入 | income | history | history_panel,strategy |
| oth_cash_pay_oper_act | q | E | 上市公司现金流量表 - 支付其他与经营活动有关的现金 | cashflow | history | history_panel,strategy |
| oth_cash_recp_ral_fnc_act | q | E | 上市公司现金流量表 - 收到其他与筹资活动有关的现金 | cashflow | history | history_panel,strategy |
| oth_cashpay_ral_fnc_act | q | E | 上市公司现金流量表 - 支付其他与筹资活动有关的现金 | cashflow | history | history_panel,strategy |
| oth_comp_income | q | E | 上市公司资产负债表 - 其他综合收益 | balance | history | history_panel,strategy |
| oth_compr_income | q | E | 上市公司利润表 - 其他综合收益 | income | history | history_panel,strategy |
| oth_cur_assets | q | E | 上市公司资产负债表 - 其他流动资产 | balance | history | history_panel,strategy |
| oth_cur_liab | q | E | 上市公司资产负债表 - 其他流动负债 | balance | history | history_panel,strategy |
| oth_debt_invest | q | E | 上市公司资产负债表 - 其他债权投资(元) | balance | history | history_panel,strategy |
| oth_eq_invest | q | E | 上市公司资产负债表 - 其他权益工具投资(元) | balance | history | history_panel,strategy |
| oth_eq_ppbond | q | E | 上市公司资产负债表 - 其他权益工具:永续债(元) | balance | history | history_panel,strategy |
| oth_eqt_tools | q | E | 上市公司资产负债表 - 其他权益工具 | balance | history | history_panel,strategy |
| oth_eqt_tools_p_shr | q | E | 上市公司资产负债表 - 其他权益工具(优先股) | balance | history | history_panel,strategy |
| oth_illiq_fin_assets | q | E | 上市公司资产负债表 - 其他非流动金融资产(元) | balance | history | history_panel,strategy |
| oth_impair_loss_assets | q | E | 上市公司利润表 - 其他资产减值损失 | income | history | history_panel,strategy |
| oth_income | q | E | 上市公司利润表 - 其他收益 | income | history | history_panel,strategy |
| oth_liab | q | E | 上市公司资产负债表 - 其他负债 | balance | history | history_panel,strategy |
| oth_loss_asset | q | E | 上市公司现金流量表 - 其他资产减值损失 | cashflow | history | history_panel,strategy |
| oth_nca | q | E | 上市公司资产负债表 - 其他非流动资产 | balance | history | history_panel,strategy |
| oth_ncl | q | E | 上市公司资产负债表 - 其他非流动负债 | balance | history | history_panel,strategy |
| oth_pay_ral_inv_act | q | E | 上市公司现金流量表 - 支付其他与投资活动有关的现金 | cashflow | history | history_panel,strategy |
| oth_pay_total | q | E | 上市公司资产负债表 - 其他应付款(合计)(元) | balance | history | history_panel,strategy |
| oth_payable | q | E | 上市公司资产负债表 - 其他应付款 | balance | history | history_panel,strategy |
| oth_rcv_total | q | E | 上市公司资产负债表 - 其他应收款(合计)（元） | balance | history | history_panel,strategy |
| oth_receiv | q | E | 上市公司资产负债表 - 其他应收款 | balance | history | history_panel,strategy |
| oth_recp_ral_inv_act | q | E | 上市公司现金流量表 - 收到其他与投资活动有关的现金 | cashflow | history | history_panel,strategy |
| other_bus_cost | q | E | 上市公司利润表 - 其他业务成本 | income | history | history_panel,strategy |
| others | q | E | 上市公司现金流量表 - 其他 | cashflow | history | history_panel,strategy |
| out_prem | q | E | 上市公司利润表 - 减:分出保费 | income | history | history_panel,strategy |
| pay_comm_insur_plcy | q | E | 上市公司现金流量表 - 支付保单红利的现金 | cashflow | history | history_panel,strategy |
| pay_handling_chrg | q | E | 上市公司现金流量表 - 支付手续费的现金 | cashflow | history | history_panel,strategy |
| payable_to_reinsurer | q | E | 上市公司资产负债表 - 应付分保账款 | balance | history | history_panel,strategy |
| payables | q | E | 上市公司资产负债表 - 应付款项 | balance | history | history_panel,strategy |
| payroll_payable | q | E | 上市公司资产负债表 - 应付职工薪酬 | balance | history | history_panel,strategy |
| pb | d | E | 股票技术指标 - 市净率（总市值/净资产） | stock_indicator | history | history_panel,strategy |
| pb | d | IDX | 指数技术指标 - 市净率 | index_indicator | history | history_panel,strategy |
| pe | d | E | 股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空） | stock_indicator | history | history_panel,strategy |
| pe | d | IDX | 指数技术指标 - 市盈率 | index_indicator | history | history_panel,strategy |
| pe_2 | d | E | 股票技术指标 - 动态市盈率 | stock_indicator2 | history | history_panel,strategy |
| pe_ttm | d | E | 股票技术指标 - 市盈率（TTM，亏损的PE为空） | stock_indicator | history | history_panel,strategy |
| pe_ttm | d | IDX | 指数技术指标 - 市盈率TTM | index_indicator | history | history_panel,strategy |
| perf_summary | q | E | 上市公司业绩快报 - 业绩简要说明 | express | history | history_panel,strategy |
| ph_invest | q | E | 上市公司资产负债表 - 保户储金及投资款 | balance | history | history_panel,strategy |
| ph_pledge_loans | q | E | 上市公司资产负债表 - 保户质押贷款 | balance | history | history_panel,strategy |
| pledge_borr | q | E | 上市公司资产负债表 - 其中:质押借款 | balance | history | history_panel,strategy |
| policy_div_payable | q | E | 上市公司资产负债表 - 应付保单红利 | balance | history | history_panel,strategy |
| prec_metals | q | E | 上市公司资产负债表 - 贵金属 | balance | history | history_panel,strategy |
| prem_earned | q | E | 上市公司利润表 - 已赚保费 | income | history | history_panel,strategy |
| prem_fr_orig_contr | q | E | 上市公司现金流量表 - 收到原保险合同保费取得的现金 | cashflow | history | history_panel,strategy |
| prem_income | q | E | 上市公司利润表 - 保险业务收入 | income | history | history_panel,strategy |
| prem_receiv_adva | q | E | 上市公司资产负债表 - 预收保费 | balance | history | history_panel,strategy |
| prem_refund | q | E | 上市公司利润表 - 退保金 | income | history | history_panel,strategy |
| premium_receiv | q | E | 上市公司资产负债表 - 应收保费 | balance | history | history_panel,strategy |
| prepayment | q | E | 上市公司资产负债表 - 预付款项 | balance | history | history_panel,strategy |
| prfshare_payable_dvd | q | E | 上市公司利润表 - 应付优先股股利 | income | history | history_panel,strategy |
| proc_issue_bonds | q | E | 上市公司现金流量表 - 发行债券收到的现金 | cashflow | history | history_panel,strategy |
| produc_bio_assets | q | E | 上市公司资产负债表 - 生产性生物资产 | balance | history | history_panel,strategy |
| profit_dedt | q | E | 上市公司财务指标 - 扣除非经常性损益后的净利润（扣非净利润） | financial | history | history_panel,strategy |
| profit_prefin_exp | q | E | 上市公司财务指标 - 扣除财务费用前营业利润 | financial | history | history_panel,strategy |
| profit_to_gr | q | E | 上市公司财务指标 - 净利润/营业总收入 | financial | history | history_panel,strategy |
| profit_to_op | q | E | 上市公司财务指标 - 利润总额／营业收入 | financial | history | history_panel,strategy |
| prov_depr_assets | q | E | 上市公司现金流量表 - 加:资产减值准备 | cashflow | history | history_panel,strategy |
| ps | d | E | 股票技术指标 - 市销率 | stock_indicator | history | history_panel,strategy |
| ps_ttm | d | E | 股票技术指标 - 市销率（TTM） | stock_indicator | history | history_panel,strategy |
| pur_resale_fa | q | E | 上市公司资产负债表 - 买入返售金融资产 | balance | history | history_panel,strategy |
| q_adminexp_to_gr | q | E | 上市公司财务指标 - 管理费用／营业总收入 (单季度) | financial | history | history_panel,strategy |
| q_dt_roe | q | E | 上市公司财务指标 - 净资产单季度收益率(扣除非经常损益) | financial | history | history_panel,strategy |
| q_dtprofit | q | E | 上市公司财务指标 - 扣除非经常损益后的单季度净利润 | financial | history | history_panel,strategy |
| q_dtprofit_to_profit | q | E | 上市公司财务指标 - 扣除非经常损益后的净利润／净利润(单季度) | financial | history | history_panel,strategy |
| q_eps | q | E | 上市公司财务指标 - 每股收益(单季度) | financial | history | history_panel,strategy |
| q_exp_to_sales | q | E | 上市公司财务指标 - 销售期间费用率(单季度) | financial | history | history_panel,strategy |
| q_finaexp_to_gr | q | E | 上市公司财务指标 - 财务费用／营业总收入 (单季度) | financial | history | history_panel,strategy |
| q_gc_to_gr | q | E | 上市公司财务指标 - 营业总成本／营业总收入 (单季度) | financial | history | history_panel,strategy |
| q_gr_qoq | q | E | 上市公司财务指标 - 营业总收入环比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_gr_yoy | q | E | 上市公司财务指标 - 营业总收入同比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_gsprofit_margin | q | E | 上市公司财务指标 - 销售毛利率(单季度) | financial | history | history_panel,strategy |
| q_impair_to_gr_ttm | q | E | 上市公司财务指标 - 资产减值损失／营业总收入(单季度) | financial | history | history_panel,strategy |
| q_investincome | q | E | 上市公司财务指标 - 价值变动单季度净收益 | financial | history | history_panel,strategy |
| q_investincome_to_ebt | q | E | 上市公司财务指标 - 价值变动净收益／利润总额(单季度) | financial | history | history_panel,strategy |
| q_netprofit_margin | q | E | 上市公司财务指标 - 销售净利率(单季度) | financial | history | history_panel,strategy |
| q_netprofit_qoq | q | E | 上市公司财务指标 - 归属母公司股东的净利润环比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_netprofit_yoy | q | E | 上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_npta | q | E | 上市公司财务指标 - 总资产净利润(单季度) | financial | history | history_panel,strategy |
| q_ocf_to_or | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额／经营活动净收益(单季度) | financial | history | history_panel,strategy |
| q_ocf_to_sales | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额／营业收入(单季度) | financial | history | history_panel,strategy |
| q_op_qoq | q | E | 上市公司财务指标 - 营业利润环比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_op_to_gr | q | E | 上市公司财务指标 - 营业利润／营业总收入(单季度) | financial | history | history_panel,strategy |
| q_op_yoy | q | E | 上市公司财务指标 - 营业利润同比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_opincome | q | E | 上市公司财务指标 - 经营活动单季度净收益 | financial | history | history_panel,strategy |
| q_opincome_to_ebt | q | E | 上市公司财务指标 - 经营活动净收益／利润总额(单季度) | financial | history | history_panel,strategy |
| q_profit_qoq | q | E | 上市公司财务指标 - 净利润环比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_profit_to_gr | q | E | 上市公司财务指标 - 净利润／营业总收入(单季度) | financial | history | history_panel,strategy |
| q_profit_yoy | q | E | 上市公司财务指标 - 净利润同比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_roe | q | E | 上市公司财务指标 - 净资产收益率(单季度) | financial | history | history_panel,strategy |
| q_saleexp_to_gr | q | E | 上市公司财务指标 - 销售费用／营业总收入 (单季度) | financial | history | history_panel,strategy |
| q_sales_qoq | q | E | 上市公司财务指标 - 营业收入环比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_sales_yoy | q | E | 上市公司财务指标 - 营业收入同比增长率(%)(单季度) | financial | history | history_panel,strategy |
| q_salescash_to_or | q | E | 上市公司财务指标 - 销售商品提供劳务收到的现金／营业收入(单季度) | financial | history | history_panel,strategy |
| quick_ratio | q | E | 上市公司财务指标 - 速动比率 | financial | history | history_panel,strategy |
| r_and_d | q | E | 上市公司资产负债表 - 研发支出 | balance | history | history_panel,strategy |
| rd_exp | q | E | 上市公司财务指标 - 研发费用 | financial | history | history_panel,strategy |
| receiv_financing | q | E | 上市公司资产负债表 - 应收款项融资 | balance | history | history_panel,strategy |
| recp_tax_rends | q | E | 上市公司现金流量表 - 收到的税费返还 | cashflow | history | history_panel,strategy |
| refund_cap_depos | q | E | 上市公司资产负债表 - 存出资本保证金 | balance | history | history_panel,strategy |
| refund_depos | q | E | 上市公司资产负债表 - 存出保证金 | balance | history | history_panel,strategy |
| reins_cost_refund | q | E | 上市公司利润表 - 减:摊回分保费用 | income | history | history_panel,strategy |
| reins_exp | q | E | 上市公司利润表 - 分保费用 | income | history | history_panel,strategy |
| reins_income | q | E | 上市公司利润表 - 其中:分保费收入 | income | history | history_panel,strategy |
| reinsur_receiv | q | E | 上市公司资产负债表 - 应收分保账款 | balance | history | history_panel,strategy |
| reinsur_res_receiv | q | E | 上市公司资产负债表 - 应收分保合同准备金 | balance | history | history_panel,strategy |
| reser_insur_liab | q | E | 上市公司利润表 - 提取保险责任准备金 | income | history | history_panel,strategy |
| reser_lins_liab | q | E | 上市公司资产负债表 - 寿险责任准备金 | balance | history | history_panel,strategy |
| reser_lthins_liab | q | E | 上市公司资产负债表 - 长期健康险责任准备金 | balance | history | history_panel,strategy |
| reser_outstd_claims | q | E | 上市公司资产负债表 - 未决赔款准备金 | balance | history | history_panel,strategy |
| reser_une_prem | q | E | 上市公司资产负债表 - 未到期责任准备金 | balance | history | history_panel,strategy |
| retained_earnings | q | E | 上市公司财务指标 - 留存收益 | financial | history | history_panel,strategy |
| retainedps | q | E | 上市公司财务指标 - 每股留存收益 | financial | history | history_panel,strategy |
| revenue | q | E | 上市公司利润表 - 营业收入 | income | history | history_panel,strategy |
| revenue_ps | q | E | 上市公司财务指标 - 每股营业收入 | financial | history | history_panel,strategy |
| roa | q | E | 上市公司财务指标 - 总资产报酬率 | financial | history | history_panel,strategy |
| roa2_yearly | q | E | 上市公司财务指标 - 年化总资产报酬率 | financial | history | history_panel,strategy |
| roa_dp | q | E | 上市公司财务指标 - 总资产净利率(杜邦分析) | financial | history | history_panel,strategy |
| roa_yearly | q | E | 上市公司财务指标 - 年化总资产净利率 | financial | history | history_panel,strategy |
| roe | q | E | 上市公司财务指标 - 净资产收益率 | financial | history | history_panel,strategy |
| roe_avg | q | E | 上市公司财务指标 - 平均净资产收益率(增发条件) | financial | history | history_panel,strategy |
| roe_dt | q | E | 上市公司财务指标 - 净资产收益率(扣除非经常损益) | financial | history | history_panel,strategy |
| roe_waa | q | E | 上市公司财务指标 - 加权平均净资产收益率 | financial | history | history_panel,strategy |
| roe_yearly | q | E | 上市公司财务指标 - 年化净资产收益率 | financial | history | history_panel,strategy |
| roe_yoy | q | E | 上市公司财务指标 - 净资产收益率(摊薄)同比增长率(%) | financial | history | history_panel,strategy |
| roic | q | E | 上市公司财务指标 - 投入资本回报率 | financial | history | history_panel,strategy |
| roic_yearly | q | E | 上市公司财务指标 - 年化投入资本回报率 | financial | history | history_panel,strategy |
| rr_reins_lins_liab | q | E | 上市公司资产负债表 - 应收分保寿险责任准备金 | balance | history | history_panel,strategy |
| rr_reins_lthins_liab | q | E | 上市公司资产负债表 - 应收分保长期健康险责任准备金 | balance | history | history_panel,strategy |
| rr_reins_outstd_cla | q | E | 上市公司资产负债表 - 应收分保未决赔款准备金 | balance | history | history_panel,strategy |
| rr_reins_une_prem | q | E | 上市公司资产负债表 - 应收分保未到期责任准备金 | balance | history | history_panel,strategy |
| rsrv_insur_cont | q | E | 上市公司资产负债表 - 保险合同准备金 | balance | history | history_panel,strategy |
| saleexp_to_gr | q | E | 上市公司财务指标 - 销售费用/营业总收入 | financial | history | history_panel,strategy |
| salescash_to_or | q | E | 上市公司财务指标 - 销售商品提供劳务收到的现金/营业收入 | financial | history | history_panel,strategy |
| sell_elg_amount | d | E | 个股资金流向 - 特大单卖出金额（万元） | money_flow | history | history_panel,strategy |
| sell_elg_vol | d | E | 个股资金流向 - 特大单卖出量（手） | money_flow | history | history_panel,strategy |
| sell_exp | q | E | 上市公司利润表 - 减:销售费用 | income | history | history_panel,strategy |
| sell_lg_amount | d | E | 个股资金流向 - 大单卖出金额（万元） | money_flow | history | history_panel,strategy |
| sell_lg_vol | d | E | 个股资金流向 - 大单卖出量（手） | money_flow | history | history_panel,strategy |
| sell_md_amount | d | E | 个股资金流向 - 中单卖出金额（万元） | money_flow | history | history_panel,strategy |
| sell_md_vol | d | E | 个股资金流向 - 中单卖出量（手） | money_flow | history | history_panel,strategy |
| sell_sm_amount | d | E | 个股资金流向 - 小单卖出金额（万元） | money_flow | history | history_panel,strategy |
| sell_sm_vol | d | E | 个股资金流向 - 小单卖出量（手） | money_flow | history | history_panel,strategy |
| selling | d | E | 股票技术指标 - 内盘（主动卖，手） | stock_indicator2 | history | history_panel,strategy |
| sett_rsrv | q | E | 上市公司资产负债表 - 结算备付金 | balance | history | history_panel,strategy |
| settle | d | FT | 期货日K线 - 结算价 | future_daily | history | history_panel,strategy |
| settle | m | FT | 期货月K线 - 结算价 | future_monthly | history | history_panel,strategy |
| settle | w | FT | 期货周K线 - 结算价 | future_weekly | history | history_panel,strategy |
| settle_chg | d | FT | 期货日K线 - 结算价涨跌 | future_daily | history | history_panel,strategy |
| settle_chg | m | FT | 期货月K线 - 结算价涨跌 | future_monthly | history | history_panel,strategy |
| settle_chg | w | FT | 期货周K线 - 结算价涨跌 | future_weekly | history | history_panel,strategy |
| sold_for_repur_fa | q | E | 上市公司资产负债表 - 卖出回购金融资产款 | balance | history | history_panel,strategy |
| special_rese | q | E | 上市公司资产负债表 - 专项储备 | balance | history | history_panel,strategy |
| specific_payables | q | E | 上市公司资产负债表 - 专项应付款 | balance | history | history_panel,strategy |
| st_bonds_payable | q | E | 上市公司资产负债表 - 应付短期债券 | balance | history | history_panel,strategy |
| st_borr | q | E | 上市公司资产负债表 - 短期借款 | balance | history | history_panel,strategy |
| st_cash_out_act | q | E | 上市公司现金流量表 - 经营活动现金流出小计 | cashflow | history | history_panel,strategy |
| st_fin_payable | q | E | 上市公司资产负债表 - 应付短期融资款 | balance | history | history_panel,strategy |
| stot_cash_in_fnc_act | q | E | 上市公司现金流量表 - 筹资活动现金流入小计 | cashflow | history | history_panel,strategy |
| stot_cashout_fnc_act | q | E | 上市公司现金流量表 - 筹资活动现金流出小计 | cashflow | history | history_panel,strategy |
| stot_inflows_inv_act | q | E | 上市公司现金流量表 - 投资活动现金流入小计 | cashflow | history | history_panel,strategy |
| stot_out_inv_act | q | E | 上市公司现金流量表 - 投资活动现金流出小计 | cashflow | history | history_panel,strategy |
| strength | d | E | 股票技术指标 - 强弱度(%) | stock_indicator2 | history | history_panel,strategy |
| surplus_rese | q | E | 上市公司资产负债表 - 盈余公积金 | balance | history | history_panel,strategy |
| surplus_rese_ps | q | E | 上市公司财务指标 - 每股盈余公积 | financial | history | history_panel,strategy |
| sw_amount | d | IDX | 申万指数日K线 - 成交额 （万元） | sw_index_daily | history | history_panel,strategy |
| sw_change | d | IDX | 申万指数日K线 - 涨跌额 | sw_index_daily | history | history_panel,strategy |
| sw_close | d | IDX | 申万指数日K线 - 收盘价 | sw_index_daily | history | history_panel,strategy |
| sw_float_mv | d | IDX | 申万指数日K线 - 流通市值 （万元） | sw_index_daily | history | history_panel,strategy |
| sw_high | d | IDX | 申万指数日K线 - 最高价 | sw_index_daily | history | history_panel,strategy |
| sw_low | d | IDX | 申万指数日K线 - 最低价 | sw_index_daily | history | history_panel,strategy |
| sw_open | d | IDX | 申万指数日K线 - 开盘价 | sw_index_daily | history | history_panel,strategy |
| sw_pb | d | IDX | 申万指数日K线 - 市净率 | sw_index_daily | history | history_panel,strategy |
| sw_pct_change | d | IDX | 申万指数日K线 - 涨跌幅 | sw_index_daily | history | history_panel,strategy |
| sw_pe | d | IDX | 申万指数日K线 - 市盈率 | sw_index_daily | history | history_panel,strategy |
| sw_total_mv | d | IDX | 申万指数日K线 - 总市值 （万元） | sw_index_daily | history | history_panel,strategy |
| sw_vol | d | IDX | 申万指数日K线 - 成交量 （万股） | sw_index_daily | history | history_panel,strategy |
| swing | d | E | 股票技术指标 - 振幅 | stock_indicator2 | history | history_panel,strategy |
| t_compr_income | q | E | 上市公司利润表 - 综合收益总额 | income | history | history_panel,strategy |
| tangasset_to_intdebt | q | E | 上市公司财务指标 - 有形资产/带息债务 | financial | history | history_panel,strategy |
| tangible_asset | q | E | 上市公司财务指标 - 有形资产 | financial | history | history_panel,strategy |
| tangibleasset_to_debt | q | E | 上市公司财务指标 - 有形资产/负债合计 | financial | history | history_panel,strategy |
| tangibleasset_to_netdebt | q | E | 上市公司财务指标 - 有形资产/净债务 | financial | history | history_panel,strategy |
| tax_to_ebt | q | E | 上市公司财务指标 - 所得税/利润总额 | financial | history | history_panel,strategy |
| taxes_payable | q | E | 上市公司资产负债表 - 应交税费 | balance | history | history_panel,strategy |
| tbassets_to_totalassets | q | E | 上市公司财务指标 - 有形资产/总资产 | financial | history | history_panel,strategy |
| ths_avg_price | d | IDX | 同花顺指数日K线 - 平均价 | ths_index_daily | history | history_panel,strategy |
| ths_change | d | IDX | 同花顺指数日K线 - 最低价 | ths_index_daily | history | history_panel,strategy |
| ths_close | d | IDX | 同花顺指数日K线 - 收盘价 | ths_index_daily | history | history_panel,strategy |
| ths_float_mv | d | IDX | 同花顺指数日K线 - 流通市值 （万元） | ths_index_daily | history | history_panel,strategy |
| ths_high | d | IDX | 同花顺指数日K线 - 最高价 | ths_index_daily | history | history_panel,strategy |
| ths_low | d | IDX | 同花顺指数日K线 - 最低价 | ths_index_daily | history | history_panel,strategy |
| ths_open | d | IDX | 同花顺指数日K线 - 开盘价 | ths_index_daily | history | history_panel,strategy |
| ths_pct_change | d | IDX | 同花顺指数日K线 - 涨跌幅 | ths_index_daily | history | history_panel,strategy |
| ths_total_mv | d | IDX | 同花顺指数日K线 - 总市值 （万元） | ths_index_daily | history | history_panel,strategy |
| ths_turnover | d | IDX | 同花顺指数日K线 - 换手率 | ths_index_daily | history | history_panel,strategy |
| ths_vol | d | IDX | 同花顺指数日K线 - 成交量 （万股） | ths_index_daily | history | history_panel,strategy |
| time_deposits | q | E | 上市公司资产负债表 - 定期存款 | balance | history | history_panel,strategy |
| total_assets | q | E | 上市公司资产负债表 - 资产总计 | balance | history | history_panel,strategy |
| total_cogs | q | E | 上市公司利润表 - 营业总成本 | income | history | history_panel,strategy |
| total_cur_assets | q | E | 上市公司资产负债表 - 流动资产合计 | balance | history | history_panel,strategy |
| total_cur_liab | q | E | 上市公司资产负债表 - 流动负债合计 | balance | history | history_panel,strategy |
| total_fa_trun | q | E | 上市公司财务指标 - 固定资产合计周转率 | financial | history | history_panel,strategy |
| total_hldr_eqy_exc_min_int | q | E | 上市公司资产负债表 - 股东权益合计(不含少数股东权益) | balance | history | history_panel,strategy |
| total_hldr_eqy_inc_min_int | q | E | 上市公司资产负债表 - 股东权益合计(含少数股东权益) | balance | history | history_panel,strategy |
| total_liab | q | E | 上市公司资产负债表 - 负债合计 | balance | history | history_panel,strategy |
| total_liab_hldr_eqy | q | E | 上市公司资产负债表 - 负债及股东权益总计 | balance | history | history_panel,strategy |
| total_mv | d | E | 股票技术指标 - 总市值 （万元） | stock_indicator | history | history_panel,strategy |
| total_mv | d | IDX | 指数技术指标 - 当日总市值（元） | index_indicator | history | history_panel,strategy |
| total_mv_2 | d | E | 股票技术指标 - 总市值(亿元) | stock_indicator2 | history | history_panel,strategy |
| total_nca | q | E | 上市公司资产负债表 - 非流动资产合计 | balance | history | history_panel,strategy |
| total_ncl | q | E | 上市公司资产负债表 - 非流动负债合计 | balance | history | history_panel,strategy |
| total_netasset | d | FD | 基金净值 - 累计资产净值 | fund_nav | history | history_panel,strategy |
| total_opcost | q | E | 上市公司利润表 - 营业总成本（二） | income | history | history_panel,strategy |
| total_profit | q | E | 上市公司利润表 - 利润总额 | income | history | history_panel,strategy |
| total_revenue | q | E | 上市公司利润表 - 营业总收入 | income | history | history_panel,strategy |
| total_revenue_ps | q | E | 上市公司财务指标 - 每股营业总收入 | financial | history | history_panel,strategy |
| total_share | d | E | 股票技术指标 - 总股本 （万股） | stock_indicator | history | history_panel,strategy |
| total_share | d | IDX | 指数技术指标 - 当日总股本（股） | index_indicator | history | history_panel,strategy |
| total_share | q | E | 上市公司资产负债表 - 期末总股本 | balance | history | history_panel,strategy |
| total_share_b | d | E | 股票技术指标 - 总股本(亿) | stock_indicator2 | history | history_panel,strategy |
| tp_last_year | q | E | 上市公司业绩快报 - 去年同期利润总额 | express | history | history_panel,strategy |
| tr_yoy | q | E | 上市公司财务指标 - 营业总收入同比增长率(%) | financial | history | history_panel,strategy |
| trad_asset | q | E | 上市公司资产负债表 - 交易性金融资产 | balance | history | history_panel,strategy |
| trade_cal | d | None | 交易日历 | trade_calendar | reference | reference_api,strategy |
| trading_fl | q | E | 上市公司资产负债表 - 交易性金融负债 | balance | history | history_panel,strategy |
| transac_seat_fee | q | E | 上市公司资产负债表 - 其中:交易席位费 | balance | history | history_panel,strategy |
| transfer_housing_imprest | q | E | 上市公司利润表 - 住房周转金转入 | income | history | history_panel,strategy |
| transfer_oth | q | E | 上市公司利润表 - 其他转入 | income | history | history_panel,strategy |
| transfer_surplus_rese | q | E | 上市公司利润表 - 盈余公积转入 | income | history | history_panel,strategy |
| treasury_share | q | E | 上市公司资产负债表 - 减:库存股 | balance | history | history_panel,strategy |
| turn_days | q | E | 上市公司财务指标 - 营业周期 | financial | history | history_panel,strategy |
| turn_over | d | E | 股票技术指标 - 换手率 | stock_indicator2 | history | history_panel,strategy |
| turnover_rate | d | E | 股票技术指标 - 换手率（%） | stock_indicator | history | history_panel,strategy |
| turnover_rate | d | IDX | 指数技术指标 - 换手率 | index_indicator | history | history_panel,strategy |
| turnover_rate_f | d | E | 股票技术指标 - 换手率（自由流通股） | stock_indicator | history | history_panel,strategy |
| turnover_rate_f | d | IDX | 指数技术指标 - 换手率(基于自由流通股本) | index_indicator | history | history_panel,strategy |
| uncon_invest_loss | q | E | 上市公司现金流量表 - 未确认投资损失 | cashflow | history | history_panel,strategy |
| undist_profit | q | E | 上市公司利润表 - 年初未分配利润 | income | history | history_panel,strategy |
| undist_profit_ps | q | E | 上市公司财务指标 - 每股未分配利润 | financial | history | history_panel,strategy |
| undistr_porfit | q | E | 上市公司资产负债表 - 未分配利润 | balance | history | history_panel,strategy |
| une_prem_reser | q | E | 上市公司利润表 - 提取未到期责任准备金 | income | history | history_panel,strategy |
| unit_nav | d | FD | 基金净值 - 单位净值 | fund_nav | history | history_panel,strategy |
| up_limit | d | E | 涨停板 - 涨停价 | stock_limit | history | history_panel,strategy |
| use_right_asset_dep | q | E | 上市公司现金流量表 - 使用权资产折旧 | cashflow | history | history_panel,strategy |
| use_right_assets | q | E | 上市公司资产负债表 - 使用权资产 | balance | history | history_panel,strategy |
| valuechange_income | q | E | 上市公司财务指标 - 价值变动净收益 | financial | history | history_panel,strategy |
| vol_ratio | d | E | 股票技术指标 - 量比 | stock_indicator2 | history | history_panel,strategy |
| volume | 15min | E | 股票15分钟K线 - 成交量 （手） | stock_15min | history | history_panel,strategy |
| volume | 15min | FD | 基金15分钟K线 - 成交量 （手） | fund_15min | history | history_panel,strategy |
| volume | 15min | FT | 期货15分钟K线 - 成交量 （手） | future_15min | history | history_panel,strategy |
| volume | 15min | IDX | 指数15分钟K线 - 成交量 （手） | index_15min | history | history_panel,strategy |
| volume | 15min | OPT | 期权15分钟K线 - 成交量 （手） | options_15min | history | history_panel,strategy |
| volume | 1min | E | 股票60秒K线 - 成交量 （手） | stock_1min | history | history_panel,strategy |
| volume | 1min | FD | 基金60秒K线 - 成交量 （手） | fund_1min | history | history_panel,strategy |
| volume | 1min | FT | 期货60秒K线 - 成交量 （手） | future_1min | history | history_panel,strategy |
| volume | 1min | IDX | 指数60秒K线 - 成交量 （手） | index_1min | history | history_panel,strategy |
| volume | 1min | OPT | 期权60秒K线 - 成交量 （手） | options_1min | history | history_panel,strategy |
| volume | 30min | E | 股票30分钟K线 - 成交量 （手） | stock_30min | history | history_panel,strategy |
| volume | 30min | FD | 基金30分钟K线 - 成交量 （手） | fund_30min | history | history_panel,strategy |
| volume | 30min | FT | 期货30分钟K线 - 成交量 （手） | future_30min | history | history_panel,strategy |
| volume | 30min | IDX | 指数30分钟K线 - 成交量 （手） | index_30min | history | history_panel,strategy |
| volume | 30min | OPT | 期权30分钟K线 - 成交量 （手） | options_30min | history | history_panel,strategy |
| volume | 5min | E | 股票5分钟K线 - 成交量 （手） | stock_5min | history | history_panel,strategy |
| volume | 5min | FD | 基金5分钟K线 - 成交量 （手） | fund_5min | history | history_panel,strategy |
| volume | 5min | FT | 期货5分钟K线 - 成交量 （手） | future_5min | history | history_panel,strategy |
| volume | 5min | IDX | 指数5分钟K线 - 成交量 （手） | index_5min | history | history_panel,strategy |
| volume | 5min | OPT | 期权5分钟K线 - 成交量 （手） | options_5min | history | history_panel,strategy |
| volume | d | E | 股票日K线 - 成交量 （手） | stock_daily | history | history_panel,strategy |
| volume | d | FD | 基金日K线 - 成交量 （手） | fund_daily | history | history_panel,strategy |
| volume | d | FT | 期货日K线 - 成交量 （手） | future_daily | history | history_panel,strategy |
| volume | d | IDX | 指数日K线 - 成交量 （手） | index_daily | history | history_panel,strategy |
| volume | d | OPT | 期权日K线 - 成交量 （手） | options_daily | history | history_panel,strategy |
| volume | h | E | 股票小时K线 - 成交量 （手） | stock_hourly | history | history_panel,strategy |
| volume | h | FD | 基金小时K线 - 成交量 （手） | fund_hourly | history | history_panel,strategy |
| volume | h | FT | 期货小时K线 - 成交量 （手） | future_hourly | history | history_panel,strategy |
| volume | h | IDX | 指数小时K线 - 成交量 （手） | index_hourly | history | history_panel,strategy |
| volume | h | OPT | 期权小时K线 - 成交量 （手） | options_hourly | history | history_panel,strategy |
| volume | m | E | 股票月K线 - 成交量 （手） | stock_monthly | history | history_panel,strategy |
| volume | m | FD | 基金月K线 - 成交量 （手） | fund_monthly | history | history_panel,strategy |
| volume | m | FT | 期货月K线 - 成交量（手） | future_monthly | history | history_panel,strategy |
| volume | m | IDX | 指数月K线 - 成交量 （手） | index_monthly | history | history_panel,strategy |
| volume | w | E | 股票周K线 - 成交量 （手） | stock_weekly | history | history_panel,strategy |
| volume | w | FD | 基金周K线 - 成交量 （手） | fund_weekly | history | history_panel,strategy |
| volume | w | FT | 期货周K线 - 成交量（手） | future_weekly | history | history_panel,strategy |
| volume | w | IDX | 指数周K线 - 成交量 （手） | index_weekly | history | history_panel,strategy |
| volume_ratio | d | E | 股票技术指标 - 量比 | stock_indicator | history | history_panel,strategy |
| withdra_biz_devfund | q | E | 上市公司利润表 - 提取企业发展基金 | income | history | history_panel,strategy |
| withdra_legal_pubfund | q | E | 上市公司利润表 - 提取法定公益金 | income | history | history_panel,strategy |
| withdra_legal_surplus | q | E | 上市公司利润表 - 提取法定盈余公积 | income | history | history_panel,strategy |
| withdra_oth_ersu | q | E | 上市公司利润表 - 提取任意盈余公积金 | income | history | history_panel,strategy |
| withdra_rese_fund | q | E | 上市公司利润表 - 提取储备基金 | income | history | history_panel,strategy |
| workers_welfare | q | E | 上市公司利润表 - 职工奖金福利 | income | history | history_panel,strategy |
| working_capital | q | E | 上市公司财务指标 - 营运资金 | financial | history | history_panel,strategy |
| yoy_dedu_np | q | E | 上市公司业绩快报 - 同比增长率:归属母公司股东的净利润 | express | history | history_panel,strategy |
| yoy_eps | q | E | 上市公司业绩快报 - 同比增长率:基本每股收益 | express | history | history_panel,strategy |
| yoy_equity | q | E | 上市公司业绩快报 - 比年初增长率:归属母公司的股东权益 | express | history | history_panel,strategy |
| yoy_net_profit | q | E | 上市公司业绩快报 - 去年同期修正后净利润 | express | history | history_panel,strategy |
| yoy_op | q | E | 上市公司业绩快报 - 同比增长率:营业利润 | express | history | history_panel,strategy |
| yoy_roe | q | E | 上市公司业绩快报 - 同比增减:加权平均净资产收益率 | express | history | history_panel,strategy |
| yoy_sales | q | E | 上市公司业绩快报 - 同比增长率:营业收入 | express | history | history_panel,strategy |
| yoy_tp | q | E | 上市公司业绩快报 - 同比增长率:利润总额 | express | history | history_panel,strategy |
