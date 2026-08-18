<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-17 16:38 UTC -->
<!-- acquisition_type: direct -->
<!-- row_count: 884 -->

# 直读（direct）

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 生成，共 **884** 条。

请勿手改；更新内置类型后请重跑生成脚本。

| name | freq | asset_type | description | table_name |
| --- | --- | --- | --- | --- |
| acc_exp | q | E | 上市公司资产负债表 - 预提费用 | balance |
| acc_receivable | q | E | 上市公司资产负债表 - 应收款项 | balance |
| accounts_pay | q | E | 上市公司资产负债表 - 应付票据及应付账款 | balance |
| accounts_receiv | q | E | 上市公司资产负债表 - 应收账款 | balance |
| accounts_receiv_bill | q | E | 上市公司资产负债表 - 应收票据及应收账款 | balance |
| acct_payable | q | E | 上市公司资产负债表 - 应付账款 | balance |
| accum_div | d | FD | 基金净值 - 累计分红 | fund_nav |
| accum_nav | d | FD | 基金净值 - 累计净值 | fund_nav |
| acting_trading_sec | q | E | 上市公司资产负债表 - 代理买卖证券款 | balance |
| acting_uw_sec | q | E | 上市公司资产负债表 - 代理承销证券款 | balance |
| activity | d | E | 股票技术指标 - 活跃度(%) | stock_indicator2 |
| adj_lossgain | q | E | 上市公司利润表 - 调整以前年度损益 | income |
| adj_nav | d | FD | 基金净值 - 复权净值 | fund_nav |
| admin_exp | q | E | 上市公司利润表 - 减:管理费用 | income |
| adminexp_of_gr | q | E | 上市公司财务指标 - 管理费用/营业总收入 | financial |
| adv_receipts | q | E | 上市公司资产负债表 - 预收款项 | balance |
| agency_bus_liab | q | E | 上市公司资产负债表 - 代理业务负债 | balance |
| amodcost_fin_assets | q | E | 上市公司利润表 - 以摊余成本计量的金融资产终止确认收益 | income |
| amor_exp | q | E | 上市公司资产负债表 - 长期待摊费用 | balance |
| amort_intang_assets | q | E | 上市公司现金流量表 - 无形资产摊销 | cashflow |
| amount | 15min | E | 股票15分钟K线 - 成交额 （千元） | stock_15min |
| amount | 15min | FD | 基金15分钟K线 - 成交额 （千元） | fund_15min |
| amount | 15min | FT | 期货15分钟K线 - 成交额 （千元） | future_15min |
| amount | 15min | IDX | 指数15分钟K线 - 成交额 （千元） | index_15min |
| amount | 15min | OPT | 期权15分钟K线 - 成交额 （千元） | options_15min |
| amount | 1min | E | 股票60秒K线 - 成交额 （千元） | stock_1min |
| amount | 1min | FD | 基金60秒K线 - 成交额 （千元） | fund_1min |
| amount | 1min | FT | 期货60秒K线 - 成交额 （千元） | future_1min |
| amount | 1min | IDX | 指数60秒K线 - 成交额 （千元） | index_1min |
| amount | 1min | OPT | 期权60秒K线 - 成交额 （千元） | options_1min |
| amount | 30min | E | 股票30分钟K线 - 成交额 （千元） | stock_30min |
| amount | 30min | FD | 基金30分钟K线 - 成交额 （千元） | fund_30min |
| amount | 30min | FT | 期货30分钟K线 - 成交额 （千元） | future_30min |
| amount | 30min | IDX | 指数30分钟K线 - 成交额 （千元） | index_30min |
| amount | 30min | OPT | 期权30分钟K线 - 成交额 （千元） | options_30min |
| amount | 5min | E | 股票5分钟K线 - 成交额 （千元） | stock_5min |
| amount | 5min | FD | 基金5分钟K线 - 成交额 （千元） | fund_5min |
| amount | 5min | FT | 期货5分钟K线 - 成交额 （千元） | future_5min |
| amount | 5min | IDX | 指数5分钟K线 - 成交额 （千元） | index_5min |
| amount | 5min | OPT | 期权5分钟K线 - 成交额 （千元） | options_5min |
| amount | d | E | 股票日K线 - 成交额 （千元） | stock_daily |
| amount | d | FD | 基金日K线 - 成交额 （千元） | fund_daily |
| amount | d | FT | 期货日K线 - 成交额 （千元） | future_daily |
| amount | d | IDX | 指数日K线 - 成交额 （千元） | index_daily |
| amount | d | OPT | 期权日K线 - 成交额 （千元） | options_daily |
| amount | h | E | 股票小时K线 - 成交额 （千元） | stock_hourly |
| amount | h | FD | 基金小时K线 - 成交额 （千元） | fund_hourly |
| amount | h | FT | 期货小时K线 - 成交额 （千元） | future_hourly |
| amount | h | IDX | 指数小时K线 - 成交额 （千元） | index_hourly |
| amount | h | OPT | 期权小时K线 - 成交额 （千元） | options_hourly |
| amount | m | E | 股票月K线 - 成交额 （千元） | stock_monthly |
| amount | m | FD | 基金月K线 - 成交额 （千元） | fund_monthly |
| amount | m | FT | 期货月K线 - 成交额 （千元） | future_monthly |
| amount | m | IDX | 指数月K线 - 成交额 （千元） | index_monthly |
| amount | w | E | 股票周K线 - 成交额 （千元） | stock_weekly |
| amount | w | FD | 基金周K线 - 成交额 （千元） | fund_weekly |
| amount | w | FT | 期货周K线 - 成交额 （千元） | future_weekly |
| amount | w | IDX | 指数周K线 - 成交额 （千元） | index_weekly |
| ar_turn | q | E | 上市公司财务指标 - 应收账款周转率 | financial |
| arturn_days | q | E | 上市公司财务指标 - 应收账款周转天数 | financial |
| ass_invest_income | q | E | 上市公司利润表 - 其中:对联营企业和合营企业的投资收益 | income |
| asset_disp_income | q | E | 上市公司利润表 - 资产处置收益 | income |
| assets_impair_loss | q | E | 上市公司利润表 - 减:资产减值损失 | income |
| assets_to_eqt | q | E | 上市公司财务指标 - 权益乘数 | financial |
| assets_turn | q | E | 上市公司财务指标 - 总资产周转率 | financial |
| assets_yoy | q | E | 上市公司财务指标 - 资产总计相对年初增长率(%) | financial |
| attack | d | E | 股票技术指标 - 攻击波(%) | stock_indicator2 |
| avg_price | d | E | 股票技术指标 - 平均价 | stock_indicator2 |
| avg_turnover | d | E | 股票技术指标 - 笔换手 | stock_indicator2 |
| basic_eps | q | E | 上市公司利润表 - 基本每股收益 | income |
| basic_eps_yoy | q | E | 上市公司财务指标 - 基本每股收益同比增长率(%) | financial |
| beg_bal_cash | q | E | 上市公司现金流量表 - 减:现金的期初余额 | cashflow |
| beg_bal_cash_equ | q | E | 上市公司现金流量表 - 减:现金等价物的期初余额 | cashflow |
| biz_tax_surchg | q | E | 上市公司利润表 - 减:营业税金及附加 | income |
| bond_payable | q | E | 上市公司资产负债表 - 应付债券 | balance |
| bps | q | E | 上市公司业绩快报 - 每股净资产 | express |
| bps_yoy | q | E | 上市公司财务指标 - 每股净资产相对年初增长率(%) | financial |
| buy_elg_amount | d | E | 个股资金流向 - 特大单买入金额（万元） | money_flow |
| buy_elg_vol | d | E | 个股资金流向 - 特大单买入量（手） | money_flow |
| buy_lg_amount | d | E | 个股资金流向 - 大单买入金额（万元） | money_flow |
| buy_lg_vol | d | E | 个股资金流向 - 大单买入量（手） | money_flow |
| buy_md_amount | d | E | 个股资金流向 - 中单买入金额（万元） | money_flow |
| buy_md_vol | d | E | 个股资金流向 - 中单买入量（手） | money_flow |
| buy_sm_amount | d | E | 个股资金流向 - 小单买入金额（万元） | money_flow |
| buy_sm_vol | d | E | 个股资金流向 - 小单买入量（手） | money_flow |
| buying | d | E | 股票技术指标 - 外盘（主动买， 手） | stock_indicator2 |
| c_cash_equ_beg_period | q | E | 上市公司现金流量表 - 期初现金及现金等价物余额 | cashflow |
| c_cash_equ_end_period | q | E | 上市公司现金流量表 - 期末现金及现金等价物余额 | cashflow |
| c_disp_withdrwl_invest | q | E | 上市公司现金流量表 - 收回投资收到的现金 | cashflow |
| c_fr_oth_operate_a | q | E | 上市公司现金流量表 - 收到其他与经营活动有关的现金 | cashflow |
| c_fr_sale_sg | q | E | 上市公司现金流量表 - 销售商品、提供劳务收到的现金 | cashflow |
| c_inf_fr_operate_a | q | E | 上市公司现金流量表 - 经营活动现金流入小计 | cashflow |
| c_paid_for_taxes | q | E | 上市公司现金流量表 - 支付的各项税费 | cashflow |
| c_paid_goods_s | q | E | 上市公司现金流量表 - 购买商品、接受劳务支付的现金 | cashflow |
| c_paid_invest | q | E | 上市公司现金流量表 - 投资支付的现金 | cashflow |
| c_paid_to_for_empl | q | E | 上市公司现金流量表 - 支付给职工以及为职工支付的现金 | cashflow |
| c_pay_acq_const_fiolta | q | E | 上市公司现金流量表 - 购建固定资产、无形资产和其他长期资产支付的现金 | cashflow |
| c_pay_claims_orig_inco | q | E | 上市公司现金流量表 - 支付原保险合同赔付款项的现金 | cashflow |
| c_pay_dist_dpcp_int_exp | q | E | 上市公司现金流量表 - 分配股利、利润或偿付利息支付的现金 | cashflow |
| c_prepay_amt_borr | q | E | 上市公司现金流量表 - 偿还债务支付的现金 | cashflow |
| c_recp_borrow | q | E | 上市公司现金流量表 - 取得借款收到的现金 | cashflow |
| c_recp_cap_contrib | q | E | 上市公司现金流量表 - 吸收投资收到的现金 | cashflow |
| c_recp_return_invest | q | E | 上市公司现金流量表 - 取得投资收益收到的现金 | cashflow |
| ca_to_assets | q | E | 上市公司财务指标 - 流动资产/总资产 | financial |
| ca_turn | q | E | 上市公司财务指标 - 流动资产周转率 | financial |
| cap_rese | q | E | 上市公司资产负债表 - 资本公积金 | balance |
| capit_comstock_div | q | E | 上市公司利润表 - 转作股本的普通股股利 | income |
| capital_rese_ps | q | E | 上市公司财务指标 - 每股资本公积 | financial |
| capitalized_to_da | q | E | 上市公司财务指标 - 资本支出/折旧和摊销 | financial |
| cash_ratio | q | E | 上市公司财务指标 - 保守速动比率 | financial |
| cash_reser_cb | q | E | 上市公司资产负债表 - 现金及存放中央银行款项 | balance |
| cash_to_liqdebt | q | E | 上市公司财务指标 - 货币资金／流动负债 | financial |
| cash_to_liqdebt_withinterest | q | E | 上市公司财务指标 - 货币资金／带息流动负债 | financial |
| cashflow_credit_impa_loss | q | E | 上市公司现金流量表 - 信用减值损失 | cashflow |
| cb_borr | q | E | 上市公司资产负债表 - 向中央银行借款 | balance |
| cfps | q | E | 上市公司财务指标 - 每股现金流量净额 | financial |
| cfps_yoy | q | E | 上市公司财务指标 - 每股经营活动产生的现金流量净额同比增长率(%) | financial |
| ci_amount | d | IDX | 中信指数日K线 - 成交额 （万元） | ci_index_daily |
| ci_change | d | IDX | 中信指数日K线 - 涨跌额 | ci_index_daily |
| ci_close | d | IDX | 中信指数日K线 - 收盘价 | ci_index_daily |
| ci_high | d | IDX | 中信指数日K线 - 最高价 | ci_index_daily |
| ci_low | d | IDX | 中信指数日K线 - 最低价 | ci_index_daily |
| ci_open | d | IDX | 中信指数日K线 - 开盘价 | ci_index_daily |
| ci_pct_change | d | IDX | 中信指数日K线 - 涨跌幅 | ci_index_daily |
| ci_pre_close | d | IDX | 中信指数日K线 - 昨日收盘点位 | ci_index_daily |
| ci_vol | d | IDX | 中信指数日K线 - 成交量 （万股） | ci_index_daily |
| cip | q | E | 上市公司资产负债表 - 在建工程 | balance |
| cip_total | q | E | 上市公司资产负债表 - 在建工程(合计)(元) | balance |
| circ_mv | d | E | 股票技术指标 - 流通市值（万元） | stock_indicator |
| client_depos | q | E | 上市公司资产负债表 - 其中：客户资金存款 | balance |
| client_prov | q | E | 上市公司资产负债表 - 其中：客户备付金 | balance |
| close | 15min | E | 股票15分钟K线 - 收盘价 | stock_15min |
| close | 15min | FD | 基金15分钟K线 - 收盘价 | fund_15min |
| close | 15min | FT | 期货15分钟K线 - 收盘价 | future_15min |
| close | 15min | IDX | 指数15分钟K线 - 收盘价 | index_15min |
| close | 15min | OPT | 期权15分钟K线 - 收盘价 | options_15min |
| close | 1min | E | 股票60秒K线 - 收盘价 | stock_1min |
| close | 1min | FD | 基金60秒K线 - 收盘价 | fund_1min |
| close | 1min | FT | 期货60秒K线 - 收盘价 | future_1min |
| close | 1min | IDX | 指数60秒K线 - 收盘价 | index_1min |
| close | 1min | OPT | 期权60秒K线 - 收盘价 | options_1min |
| close | 30min | E | 股票30分钟K线 - 收盘价 | stock_30min |
| close | 30min | FD | 基金30分钟K线 - 收盘价 | fund_30min |
| close | 30min | FT | 期货30分钟K线 - 收盘价 | future_30min |
| close | 30min | IDX | 指数30分钟K线 - 收盘价 | index_30min |
| close | 30min | OPT | 期权30分钟K线 - 收盘价 | options_30min |
| close | 5min | E | 股票5分钟K线 - 收盘价 | stock_5min |
| close | 5min | FD | 基金5分钟K线 - 收盘价 | fund_5min |
| close | 5min | FT | 期货5分钟K线 - 收盘价 | future_5min |
| close | 5min | IDX | 指数5分钟K线 - 收盘价 | index_5min |
| close | 5min | OPT | 期权5分钟K线 - 收盘价 | options_5min |
| close | d | E | 股票日K线 - 收盘价 | stock_daily |
| close | d | FD | 基金日K线 - 收盘价 | fund_daily |
| close | d | FT | 期货日K线 - 收盘价 | future_daily |
| close | d | IDX | 指数日K线 - 收盘价 | index_daily |
| close | d | OPT | 期权日K线 - 收盘价 | options_daily |
| close | h | E | 股票小时K线 - 收盘价 | stock_hourly |
| close | h | FD | 基金小时K线 - 收盘价 | fund_hourly |
| close | h | FT | 期货小时K线 - 收盘价 | future_hourly |
| close | h | IDX | 指数小时K线 - 收盘价 | index_hourly |
| close | h | OPT | 期权小时K线 - 收盘价 | options_hourly |
| close | m | E | 股票月K线 - 收盘价 | stock_monthly |
| close | m | FD | 基金月K线 - 收盘价 | fund_monthly |
| close | m | FT | 期货月K线 - 收盘价 | future_monthly |
| close | m | IDX | 指数月K线 - 收盘价 | index_monthly |
| close | w | E | 股票周K线 - 收盘价 | stock_weekly |
| close | w | FD | 基金周K线 - 收盘价 | fund_weekly |
| close | w | FT | 期货周K线 - 收盘价 | future_weekly |
| close | w | IDX | 指数周K线 - 收盘价 | index_weekly |
| close_chg | d | FT | 期货日K线 - 收盘价涨跌 | future_daily |
| close_chg | m | FT | 期货月K线 - 收盘价涨跌 | future_monthly |
| close_chg | w | FT | 期货周K线 - 收盘价涨跌 | future_weekly |
| cogs_of_sales | q | E | 上市公司财务指标 - 销售成本率 | financial |
| comm_exp | q | E | 上市公司利润表 - 减:手续费及佣金支出 | income |
| comm_income | q | E | 上市公司利润表 - 手续费及佣金收入 | income |
| comm_payable | q | E | 上市公司资产负债表 - 应付手续费及佣金 | balance |
| compens_payout | q | E | 上市公司利润表 - 赔付总支出 | income |
| compens_payout_refu | q | E | 上市公司利润表 - 减:摊回赔付支出 | income |
| compr_inc_attr_m_s | q | E | 上市公司利润表 - 归属于少数股东的综合收益总额 | income |
| compr_inc_attr_p | q | E | 上市公司利润表 - 归属于母公司(或股东)的综合收益总额 | income |
| comshare_payable_dvd | q | E | 上市公司利润表 - 应付普通股股利 | income |
| const_materials | q | E | 上市公司资产负债表 - 工程物资 | balance |
| continued_net_profit | q | E | 上市公司利润表 - 持续经营净利润 | income |
| contract_assets | q | E | 上市公司资产负债表 - 合同资产 | balance |
| contract_liab | q | E | 上市公司资产负债表 - 合同负债 | balance |
| conv_copbonds_due_within_1y | q | E | 上市公司现金流量表 - 一年内到期的可转换公司债券 | cashflow |
| conv_debt_into_cap | q | E | 上市公司现金流量表 - 债务转为资本 | cashflow |
| cost_fin_assets | q | E | 上市公司资产负债表 - 以摊余成本计量的金融资产 | balance |
| current_exint | q | E | 上市公司财务指标 - 无息流动负债 | financial |
| current_ratio | q | E | 上市公司财务指标 - 流动比率 | financial |
| currentdebt_to_debt | q | E | 上市公司财务指标 - 流动负债/负债合计 | financial |
| daa | q | E | 上市公司财务指标 - 折旧与摊销 | financial |
| debt_invest | q | E | 上市公司资产负债表 - 债权投资(元) | balance |
| debt_to_assets | q | E | 上市公司财务指标 - 资产负债率 | financial |
| debt_to_eqt | q | E | 上市公司财务指标 - 产权比率 | financial |
| decr_def_inc_tax_assets | q | E | 上市公司现金流量表 - 递延所得税资产减少 | cashflow |
| decr_deferred_exp | q | E | 上市公司现金流量表 - 待摊费用减少 | cashflow |
| decr_in_disbur | q | E | 上市公司资产负债表 - 发放贷款及垫款 | balance |
| decr_inventories | q | E | 上市公司现金流量表 - 存货的减少 | cashflow |
| decr_oper_payable | q | E | 上市公司现金流量表 - 经营性应收项目的减少 | cashflow |
| defer_inc_non_cur_liab | q | E | 上市公司资产负债表 - 递延收益-非流动负债 | balance |
| defer_tax_assets | q | E | 上市公司资产负债表 - 递延所得税资产 | balance |
| defer_tax_liab | q | E | 上市公司资产负债表 - 递延所得税负债 | balance |
| deferred_inc | q | E | 上市公司资产负债表 - 递延收益 | balance |
| delf_settle | d | FT | 期货日K线 - 交割结算价 | future_daily |
| delf_settle | m | FT | 期货月K线 - 交割结算价 | future_monthly |
| delf_settle | w | FT | 期货周K线 - 交割结算价 | future_weekly |
| depos | q | E | 上市公司资产负债表 - 吸收存款 | balance |
| depos_ib_deposits | q | E | 上市公司资产负债表 - 吸收存款及同业存放 | balance |
| depos_in_oth_bfi | q | E | 上市公司资产负债表 - 存放同业和其它金融机构款项 | balance |
| depos_oth_bfi | q | E | 上市公司资产负债表 - 同业和其它金融机构存放款项 | balance |
| depos_received | q | E | 上市公司资产负债表 - 存入保证金 | balance |
| depr_fa_coga_dpba | q | E | 上市公司现金流量表 - 固定资产折旧、油气资产折耗、生产性生物资产折旧 | cashflow |
| deriv_assets | q | E | 上市公司资产负债表 - 衍生金融资产 | balance |
| deriv_liab | q | E | 上市公司资产负债表 - 衍生金融负债 | balance |
| diluted2_eps | q | E | 上市公司财务指标 - 期末摊薄每股收益 | financial |
| diluted_eps | q | E | 上市公司利润表 - 稀释每股收益 | income |
| diluted_roe | q | E | 上市公司业绩快报 - 净资产收益率(摊薄)(%) | express |
| distable_profit | q | E | 上市公司利润表 - 可分配利润 | income |
| distr_profit_shrhder | q | E | 上市公司利润表 - 可供股东分配的利润 | income |
| div_payable | q | E | 上市公司资产负债表 - 应付股利 | balance |
| div_payt | q | E | 上市公司利润表 - 保户红利支出 | income |
| div_receiv | q | E | 上市公司资产负债表 - 应收股利 | balance |
| down_limit | d | E | 跌停板 - 跌停价 | stock_limit |
| dp_assets_to_eqt | q | E | 上市公司财务指标 - 权益乘数(杜邦分析) | financial |
| dt_eps | q | E | 上市公司财务指标 - 稀释每股收益 | financial |
| dt_eps_yoy | q | E | 上市公司财务指标 - 稀释每股收益同比增长率(%) | financial |
| dt_netprofit_yoy | q | E | 上市公司财务指标 - 归属母公司股东的净利润-扣除非经常损益同比增长率(%) | financial |
| dtprofit_to_profit | q | E | 上市公司财务指标 - 扣除非经常损益后的净利润/净利润 | financial |
| dv_ratio | d | E | 股票技术指标 - 股息率 （%） | stock_indicator |
| dv_ttm | d | E | 股票技术指标 - 股息率（TTM）（%） | stock_indicator |
| ebit | q | E | 上市公司财务指标 - 息税前利润 | financial |
| ebit_of_gr | q | E | 上市公司财务指标 - 息税前利润/营业总收入 | financial |
| ebit_ps | q | E | 上市公司财务指标 - 每股息税前利润 | financial |
| ebit_to_interest | q | E | 上市公司财务指标 - 已获利息倍数(EBIT/利息费用) | financial |
| ebitda | q | E | 上市公司财务指标 - 息税折旧摊销前利润 | financial |
| ebitda_to_debt | q | E | 上市公司财务指标 - 息税折旧摊销前利润/负债合计 | financial |
| ebt_yoy | q | E | 上市公司财务指标 - 利润总额同比增长率(%) | financial |
| eff_fx_flu_cash | q | E | 上市公司现金流量表 - 汇率变动对现金的影响 | cashflow |
| end_bal_cash | q | E | 上市公司现金流量表 - 现金的期末余额 | cashflow |
| end_bal_cash_equ | q | E | 上市公司现金流量表 - 加:现金等价物的期末余额 | cashflow |
| end_net_profit | q | E | 上市公司利润表 - 终止经营净利润 | income |
| eps | q | E | 上市公司财务指标 - 基本每股收益 | financial |
| eps_last_year | q | E | 上市公司业绩快报 - 去年同期每股收益 | express |
| eqt_to_debt | q | E | 上市公司财务指标 - 归属于母公司的股东权益/负债合计 | financial |
| eqt_to_interestdebt | q | E | 上市公司财务指标 - 归属于母公司的股东权益/带息债务 | financial |
| eqt_to_talcapital | q | E | 上市公司财务指标 - 归属于母公司的股东权益/全部投入资本 | financial |
| eqt_yoy | q | E | 上市公司财务指标 - 归属母公司的股东权益相对年初增长率(%) | financial |
| equity_yoy | q | E | 上市公司财务指标 - 净资产同比增长率 | financial |
| estimated_liab | q | E | 上市公司资产负债表 - 预计负债 | balance |
| expense_of_sales | q | E | 上市公司财务指标 - 销售期间费用率 | financial |
| express_bps | q | E | 上市公司财务指标 - 每股净资产 | financial |
| express_diluted_eps | q | E | 上市公司业绩快报 - 每股收益(摊薄)(元) | express |
| express_n_income | q | E | 上市公司业绩快报 - 净利润(元) | express |
| express_operate_profit | q | E | 上市公司业绩快报 - 营业利润(元) | express |
| express_revenue | q | E | 上市公司业绩快报 - 营业收入(元) | express |
| express_total_assets | q | E | 上市公司业绩快报 - 总资产(元) | express |
| express_total_hldr_eqy_exc_min_int | q | E | 上市公司业绩快报 - 股东权益合计(不含少数股东权益)(元) | express |
| express_total_profit | q | E | 上市公司业绩快报 - 利润总额(元) | express |
| extra_item | q | E | 上市公司财务指标 - 非经常性损益 | financial |
| fa_avail_for_sale | q | E | 上市公司资产负债表 - 可供出售金融资产 | balance |
| fa_fnc_leases | q | E | 上市公司现金流量表 - 融资租入固定资产 | cashflow |
| fa_turn | q | E | 上市公司财务指标 - 固定资产周转率 | financial |
| fair_value_fin_assets | q | E | 上市公司资产负债表 - 以公允价值计量且其变动计入其他综合收益的金融资产 | balance |
| fcfe | q | E | 上市公司财务指标 - 股权自由现金流量 | financial |
| fcfe_ps | q | E | 上市公司财务指标 - 每股股东自由现金流量 | financial |
| fcff | q | E | 上市公司财务指标 - 企业自由现金流量 | financial |
| fcff_ps | q | E | 上市公司财务指标 - 每股企业自由现金流量 | financial |
| fd_share | d | FD | 基金份额（万） | fund_share |
| fin_exp | q | E | 上市公司利润表 - 减:财务费用 | income |
| fin_exp_int_exp | q | E | 上市公司利润表 - 财务费用:利息费用 | income |
| fin_exp_int_inc | q | E | 上市公司利润表 - 财务费用:利息收入 | income |
| finaexp_of_gr | q | E | 上市公司财务指标 - 财务费用/营业总收入 | financial |
| finan_exp | q | E | 上市公司现金流量表 - 财务费用 | cashflow |
| fix_assets | q | E | 上市公司资产负债表 - 固定资产 | balance |
| fix_assets_total | q | E | 上市公司资产负债表 - 固定资产(合计)(元) | balance |
| fixed_assets | q | E | 上市公司财务指标 - 固定资产合计 | financial |
| fixed_assets_disp | q | E | 上市公司资产负债表 - 固定资产清理 | balance |
| float_mv | d | IDX | 指数技术指标 - 当日流通市值（元） | index_indicator |
| float_mv_2 | d | E | 股票技术指标 - 流通市值(亿元) | stock_indicator2 |
| float_share | d | E | 股票技术指标 - 流通股本 （万股） | stock_indicator |
| float_share | d | IDX | 指数技术指标 - 当日流通股本（股） | index_indicator |
| float_share_b | d | E | 股票技术指标 - 流通股本(亿) | stock_indicator2 |
| forex_differ | q | E | 上市公司资产负债表 - 外币报表折算差额 | balance |
| forex_gain | q | E | 上市公司利润表 - 加:汇兑净收益 | income |
| free_cashflow | q | E | 上市公司现金流量表 - 企业自由现金流量 | cashflow |
| free_share | d | E | 股票技术指标 - 自由流通股本（万） | stock_indicator |
| free_share | d | IDX | 指数技术指标 - 当日自由流通股本（股） | index_indicator |
| fv_value_chg_gain | q | E | 上市公司利润表 - 加:公允价值变动净收益 | income |
| g_index_amount | d | IDX | 全球指数日K线行情 - 成交额 | global_index_daily |
| g_index_change | d | IDX | 全球指数日K线行情 - 最低价 | global_index_daily |
| g_index_close | d | IDX | 全球指数日K线行情 - 收盘价 | global_index_daily |
| g_index_high | d | IDX | 全球指数日K线行情 - 最高价 | global_index_daily |
| g_index_low | d | IDX | 全球指数日K线行情 - 最低价 | global_index_daily |
| g_index_open | d | IDX | 全球指数日K线行情 - 开盘价 | global_index_daily |
| g_index_pct_change | d | IDX | 全球指数日K线行情 - 收盘价 | global_index_daily |
| g_index_pre_close | d | IDX | 全球指数日K线行情 - 昨日收盘价 | global_index_daily |
| g_index_swing | d | IDX | 全球指数日K线行情 - 振幅 | global_index_daily |
| g_index_vol | d | IDX | 全球指数日K线行情 - 成交量 | global_index_daily |
| gc_of_gr | q | E | 上市公司财务指标 - 营业总成本/营业总收入 | financial |
| goodwill | q | E | 上市公司资产负债表 - 商誉 | balance |
| gross_margin | q | E | 上市公司财务指标 - 毛利 | financial |
| grossprofit_margin | q | E | 上市公司财务指标 - 销售毛利率 | financial |
| growth_assets | q | E | 上市公司业绩快报 - 比年初增长率:总资产 | express |
| growth_bps | q | E | 上市公司业绩快报 - 比年初增长率:归属于母公司股东的每股净资产 | express |
| hfs_assets | q | E | 上市公司资产负债表 - 持有待售的资产 | balance |
| hfs_sales | q | E | 上市公司资产负债表 - 持有待售的负债 | balance |
| high | 15min | E | 股票15分钟K线 - 最高价 | stock_15min |
| high | 15min | FD | 基金15分钟K线 - 最高价 | fund_15min |
| high | 15min | FT | 期货15分钟K线 - 最高价 | future_15min |
| high | 15min | IDX | 指数15分钟K线 - 最高价 | index_15min |
| high | 15min | OPT | 期权15分钟K线 - 最高价 | options_15min |
| high | 1min | E | 股票60秒K线 - 最高价 | stock_1min |
| high | 1min | FD | 基金60秒K线 - 最高价 | fund_1min |
| high | 1min | FT | 期货60秒K线 - 最高价 | future_1min |
| high | 1min | IDX | 指数60秒K线 - 最高价 | index_1min |
| high | 1min | OPT | 期权60秒K线 - 最高价 | options_1min |
| high | 30min | E | 股票30分钟K线 - 最高价 | stock_30min |
| high | 30min | FD | 基金30分钟K线 - 最高价 | fund_30min |
| high | 30min | FT | 期货30分钟K线 - 最高价 | future_30min |
| high | 30min | IDX | 指数30分钟K线 - 最高价 | index_30min |
| high | 30min | OPT | 期权30分钟K线 - 最高价 | options_30min |
| high | 5min | E | 股票5分钟K线 - 最高价 | stock_5min |
| high | 5min | FD | 基金5分钟K线 - 最高价 | fund_5min |
| high | 5min | FT | 期货5分钟K线 - 最高价 | future_5min |
| high | 5min | IDX | 指数5分钟K线 - 最高价 | index_5min |
| high | 5min | OPT | 期权5分钟K线 - 最高价 | options_5min |
| high | d | E | 股票日K线 - 最高价 | stock_daily |
| high | d | FD | 基金日K线 - 最高价 | fund_daily |
| high | d | FT | 期货日K线 - 最高价 | future_daily |
| high | d | IDX | 指数日K线 - 最高价 | index_daily |
| high | d | OPT | 期权日K线 - 最高价 | options_daily |
| high | h | E | 股票小时K线 - 最高价 | stock_hourly |
| high | h | FD | 基金小时K线 - 最高价 | fund_hourly |
| high | h | FT | 期货小时K线 - 最高价 | future_hourly |
| high | h | IDX | 指数小时K线 - 最高价 | index_hourly |
| high | h | OPT | 期权小时K线 - 最高价 | options_hourly |
| high | m | E | 股票月K线 - 最高价 | stock_monthly |
| high | m | FD | 基金月K线 - 最高价 | fund_monthly |
| high | m | FT | 期货月K线 - 最高价 | future_monthly |
| high | m | IDX | 指数月K线 - 最高价 | index_monthly |
| high | w | E | 股票周K线 - 最高价 | stock_weekly |
| high | w | FD | 基金周K线 - 最高价 | fund_weekly |
| high | w | FT | 期货周K线 - 最高价 | future_weekly |
| high | w | IDX | 指数周K线 - 最高价 | index_weekly |
| hk_top10_amount | d | E | 港股通十大成交 - 累计成交额（元） | hk_top10_stock |
| hk_top10_close | d | E | 港股通十大成交 - 收盘价 | hk_top10_stock |
| hk_top10_net_amount | d | E | 港股通十大成交 - 净买入金额（元） | hk_top10_stock |
| hk_top10_p_change | d | E | 港股通十大成交 - 涨跌幅 | hk_top10_stock |
| hk_top10_rank | d | E | 港股通十大成交 - 排名 | hk_top10_stock |
| hk_top10_sh_amount | d | E | 港股通十大成交 - 沪市成交额（元） | hk_top10_stock |
| hk_top10_sh_buy | d | E | 港股通十大成交 - 深市净买入金额（元） | hk_top10_stock |
| hk_top10_sh_net_amount | d | E | 港股通十大成交 - 沪市净买入额（元） | hk_top10_stock |
| hk_top10_sh_sell | d | E | 港股通十大成交 - 深市净买入金额（元） | hk_top10_stock |
| hk_top10_sz_amount | d | E | 港股通十大成交 - 深市成交金额（元） | hk_top10_stock |
| hk_top10_sz_net_amount | d | E | 港股通十大成交 - 深市净买入额（元） | hk_top10_stock |
| htm_invest | q | E | 上市公司资产负债表 - 持有至到期投资 | balance |
| ifc_cash_incr | q | E | 上市公司现金流量表 - 收取利息和手续费净增加额 | cashflow |
| im_n_incr_cash_equ | q | E | 上市公司现金流量表 - 现金及现金等价物净增加额(间接法) | cashflow |
| im_net_cashflow_oper_act | q | E | 上市公司现金流量表 - 经营活动产生的现金流量净额(间接法) | cashflow |
| impai_ttm | q | E | 上市公司财务指标 - 资产减值损失/营业总收入 | financial |
| incl_cash_rec_saims | q | E | 上市公司现金流量表 - 其中:子公司吸收少数股东投资收到的现金 | cashflow |
| incl_dvd_profit_paid_sc_ms | q | E | 上市公司现金流量表 - 其中:子公司支付给少数股东的股利、利润 | cashflow |
| income_credit_impa_loss | q | E | 上市公司利润表 - 信用减值损失 | income |
| income_ebit | q | E | 上市公司利润表 - 息税前利润 | income |
| income_ebitda | q | E | 上市公司利润表 - 息税折旧摊销前利润 | income |
| income_rd_exp | q | E | 上市公司利润表 - 研发费用 | income |
| income_tax | q | E | 上市公司利润表 - 所得税费用 | income |
| incr_acc_exp | q | E | 上市公司现金流量表 - 预提费用增加 | cashflow |
| incr_def_inc_tax_liab | q | E | 上市公司现金流量表 - 递延所得税负债增加 | cashflow |
| incr_oper_payable | q | E | 上市公司现金流量表 - 经营性应付项目的增加 | cashflow |
| indem_payable | q | E | 上市公司资产负债表 - 应付赔付款 | balance |
| indep_acct_assets | q | E | 上市公司资产负债表 - 独立账户资产 | balance |
| indept_acc_liab | q | E | 上市公司资产负债表 - 独立账户负债 | balance |
| insur_reser_refu | q | E | 上市公司利润表 - 减:摊回保险责任准备金 | income |
| insurance_exp | q | E | 上市公司利润表 - 保险业务支出 | income |
| int_exp | q | E | 上市公司利润表 - 减:利息支出 | income |
| int_income | q | E | 上市公司利润表 - 利息收入 | income |
| int_payable | q | E | 上市公司资产负债表 - 应付利息 | balance |
| int_receiv | q | E | 上市公司资产负债表 - 应收利息 | balance |
| int_to_talcap | q | E | 上市公司财务指标 - 带息债务/全部投入资本 | financial |
| intan_assets | q | E | 上市公司资产负债表 - 无形资产 | balance |
| interestdebt | q | E | 上市公司财务指标 - 带息债务 | financial |
| interst_income | q | E | 上市公司财务指标 - 利息费用 | financial |
| interval_3 | d | E | 股票技术指标 - 近3月涨幅 | stock_indicator2 |
| interval_6 | d | E | 股票技术指标 - 近6月涨幅 | stock_indicator2 |
| inv_turn | q | E | 上市公司财务指标 - 存货周转率 | financial |
| inventories | q | E | 上市公司资产负债表 - 存货 | balance |
| invest_as_receiv | q | E | 上市公司资产负债表 - 应收款项类投资 | balance |
| invest_capital | q | E | 上市公司财务指标 - 全部投入资本 | financial |
| invest_income | q | E | 上市公司利润表 - 加:投资净收益 | income |
| invest_loss | q | E | 上市公司现金流量表 - 投资损失 | cashflow |
| invest_loss_unconf | q | E | 上市公司资产负债表 - 未确认的投资损失 | balance |
| invest_real_estate | q | E | 上市公司资产负债表 - 投资性房地产 | balance |
| investincome_of_ebt | q | E | 上市公司财务指标 - 价值变动净收益/利润总额 | financial |
| invturn_days | q | E | 上市公司财务指标 - 存货周转天数 | financial |
| lease_liab | q | E | 上市公司资产负债表 - 租赁负债 | balance |
| lending_funds | q | E | 上市公司资产负债表 - 融出资金 | balance |
| loan_oth_bank | q | E | 上市公司资产负债表 - 拆入资金 | balance |
| loanto_oth_bank_fi | q | E | 上市公司资产负债表 - 拆出资金 | balance |
| long_pay_total | q | E | 上市公司资产负债表 - 长期应付款(合计)(元) | balance |
| longdeb_to_debt | q | E | 上市公司财务指标 - 非流动负债/负债合计 | financial |
| longdebt_to_workingcapital | q | E | 上市公司财务指标 - 长期债务与营运资金比率 | financial |
| loss_disp_fiolta | q | E | 上市公司现金流量表 - 处置固定、无形资产和其他长期资产的损失 | cashflow |
| loss_fv_chg | q | E | 上市公司现金流量表 - 公允价值变动损失 | cashflow |
| loss_scr_fa | q | E | 上市公司现金流量表 - 固定资产报废损失 | cashflow |
| low | 15min | E | 股票15分钟K线 - 最低价 | stock_15min |
| low | 15min | FD | 基金15分钟K线 - 最低价 | fund_15min |
| low | 15min | FT | 期货15分钟K线 - 最低价 | future_15min |
| low | 15min | IDX | 指数15分钟K线 - 最低价 | index_15min |
| low | 15min | OPT | 期权15分钟K线 - 最低价 | options_15min |
| low | 1min | E | 股票60秒K线 - 最低价 | stock_1min |
| low | 1min | FD | 基金60秒K线 - 最低价 | fund_1min |
| low | 1min | FT | 期货60秒K线 - 最低价 | future_1min |
| low | 1min | IDX | 指数60秒K线 - 最低价 | index_1min |
| low | 1min | OPT | 期权60秒K线 - 最低价 | options_1min |
| low | 30min | E | 股票30分钟K线 - 最低价 | stock_30min |
| low | 30min | FD | 基金30分钟K线 - 最低价 | fund_30min |
| low | 30min | FT | 期货30分钟K线 - 最低价 | future_30min |
| low | 30min | IDX | 指数30分钟K线 - 最低价 | index_30min |
| low | 30min | OPT | 期权30分钟K线 - 最低价 | options_30min |
| low | 5min | E | 股票5分钟K线 - 最低价 | stock_5min |
| low | 5min | FD | 基金5分钟K线 - 最低价 | fund_5min |
| low | 5min | FT | 期货5分钟K线 - 最低价 | future_5min |
| low | 5min | IDX | 指数5分钟K线 - 最低价 | index_5min |
| low | 5min | OPT | 期权5分钟K线 - 最低价 | options_5min |
| low | d | E | 股票日K线 - 最低价 | stock_daily |
| low | d | FD | 基金日K线 - 最低价 | fund_daily |
| low | d | FT | 期货日K线 - 最低价 | future_daily |
| low | d | IDX | 指数日K线 - 最低价 | index_daily |
| low | d | OPT | 期权日K线 - 最低价 | options_daily |
| low | h | E | 股票小时K线 - 最低价 | stock_hourly |
| low | h | FD | 基金小时K线 - 最低价 | fund_hourly |
| low | h | FT | 期货小时K线 - 最低价 | future_hourly |
| low | h | IDX | 指数小时K线 - 最低价 | index_hourly |
| low | h | OPT | 期权小时K线 - 最低价 | options_hourly |
| low | m | E | 股票月K线 - 最低价 | stock_monthly |
| low | m | FD | 基金月K线 - 最低价 | fund_monthly |
| low | m | FT | 期货月K线 - 最低价 | future_monthly |
| low | m | IDX | 指数月K线 - 最低价 | index_monthly |
| low | w | E | 股票周K线 - 最低价 | stock_weekly |
| low | w | FD | 基金周K线 - 最低价 | fund_weekly |
| low | w | FT | 期货周K线 - 最低价 | future_weekly |
| low | w | IDX | 指数周K线 - 最低价 | index_weekly |
| lt_amor_exp | q | E | 上市公司资产负债表 - 长期待摊费用 | balance |
| lt_amort_deferred_exp | q | E | 上市公司现金流量表 - 长期待摊费用摊销 | cashflow |
| lt_borr | q | E | 上市公司资产负债表 - 长期借款 | balance |
| lt_eqt_invest | q | E | 上市公司资产负债表 - 长期股权投资 | balance |
| lt_payable | q | E | 上市公司资产负债表 - 长期应付款 | balance |
| lt_payroll_payable | q | E | 上市公司资产负债表 - 长期应付职工薪酬 | balance |
| lt_rec | q | E | 上市公司资产负债表 - 长期应收款 | balance |
| minority_gain | q | E | 上市公司利润表 - 少数股东损益 | income |
| minority_int | q | E | 上市公司资产负债表 - 少数股东权益 | balance |
| money_cap | q | E | 上市公司资产负债表 - 货币资金 | balance |
| n_asset_mg_income | q | E | 上市公司利润表 - 受托客户资产管理业务净收入 | income |
| n_cap_incr_repur | q | E | 上市公司现金流量表 - 回购业务资金净增加额 | cashflow |
| n_cash_flows_fnc_act | q | E | 上市公司现金流量表 - 筹资活动产生的现金流量净额 | cashflow |
| n_cashflow_act | q | E | 上市公司现金流量表 - 经营活动产生的现金流量净额 | cashflow |
| n_cashflow_inv_act | q | E | 上市公司现金流量表 - 投资活动产生的现金流量净额 | cashflow |
| n_commis_income | q | E | 上市公司利润表 - 手续费及佣金净收入 | income |
| n_depos_incr_fi | q | E | 上市公司现金流量表 - 客户存款和同业存放款项净增加额 | cashflow |
| n_disp_subs_oth_biz | q | E | 上市公司现金流量表 - 取得子公司及其他营业单位支付的现金净额 | cashflow |
| n_inc_borr_oth_fi | q | E | 上市公司现金流量表 - 向其他金融机构拆入资金净增加额 | cashflow |
| n_income_attr_p | q | E | 上市公司利润表 - 净利润(不含少数股东损益) | income |
| n_incr_cash_cash_equ | q | E | 上市公司现金流量表 - 现金及现金等价物净增加额 | cashflow |
| n_incr_clt_loan_adv | q | E | 上市公司现金流量表 - 客户贷款及垫款净增加额 | cashflow |
| n_incr_dep_cbob | q | E | 上市公司现金流量表 - 存放央行和同业款项净增加额 | cashflow |
| n_incr_disp_faas | q | E | 上市公司现金流量表 - 处置可供出售金融资产净增加额 | cashflow |
| n_incr_disp_tfa | q | E | 上市公司现金流量表 - 处置交易性金融资产净增加额 | cashflow |
| n_incr_insured_dep | q | E | 上市公司现金流量表 - 保户储金净增加额 | cashflow |
| n_incr_loans_cb | q | E | 上市公司现金流量表 - 向中央银行借款净增加额 | cashflow |
| n_incr_loans_oth_bank | q | E | 上市公司现金流量表 - 拆入资金净增加额 | cashflow |
| n_incr_pledge_loan | q | E | 上市公司现金流量表 - 质押贷款净增加额 | cashflow |
| n_op_profit_of_ebt | q | E | 上市公司财务指标 - 营业外收支净额/利润总额 | financial |
| n_oth_b_income | q | E | 上市公司利润表 - 加:其他业务净收益 | income |
| n_oth_income | q | E | 上市公司利润表 - 其他经营净收益 | income |
| n_recp_disp_fiolta | q | E | 上市公司现金流量表 - 处置固定资产、无形资产和其他长期资产收回的现金净额 | cashflow |
| n_recp_disp_sobu | q | E | 上市公司现金流量表 - 处置子公司及其他营业单位收到的现金净额 | cashflow |
| n_reinsur_prem | q | E | 上市公司现金流量表 - 收到再保业务现金净额 | cashflow |
| n_sec_tb_income | q | E | 上市公司利润表 - 代理买卖证券业务净收入 | income |
| n_sec_uw_income | q | E | 上市公司利润表 - 证券承销业务净收入 | income |
| nca_disploss | q | E | 上市公司利润表 - 其中:减:非流动资产处置净损失 | income |
| nca_to_assets | q | E | 上市公司财务指标 - 非流动资产/总资产 | financial |
| nca_within_1y | q | E | 上市公司资产负债表 - 一年内到期的非流动资产 | balance |
| net_after_nr_lp_correct | q | E | 上市公司利润表 - 扣除非经常性损益后的净利润（更正前） | income |
| net_asset | d | FD | 基金净值 - 资产净值 | fund_nav |
| net_cash_rece_sec | q | E | 上市公司现金流量表 - 代理买卖证券收到的现金净额(元) | cashflow |
| net_dism_capital_add | q | E | 上市公司现金流量表 - 拆出资金净增加额 | cashflow |
| net_expo_hedging_benefits | q | E | 上市公司利润表 - 净敞口套期收益 | income |
| net_income | q | E | 上市公司利润表 - 净利润(含少数股东损益) | income |
| net_mf_amount | d | E | 个股资金流向 - 净流入额（万元） | money_flow |
| net_mf_vol | d | E | 个股资金流向 - 净流入量（手） | money_flow |
| net_profit | q | E | 上市公司现金流量表 - 净利润 | cashflow |
| netdebt | q | E | 上市公司财务指标 - 净债务 | financial |
| netprofit_margin | q | E | 上市公司财务指标 - 销售净利率 | financial |
| netprofit_yoy | q | E | 上市公司财务指标 - 归属母公司股东的净利润同比增长率(%) | financial |
| networking_capital | q | E | 上市公司财务指标 - 营运流动资本 | financial |
| non_cur_liab_due_1y | q | E | 上市公司资产负债表 - 一年内到期的非流动负债 | balance |
| non_op_profit | q | E | 上市公司财务指标 - 非营业利润 | financial |
| non_oper_exp | q | E | 上市公司利润表 - 减:营业外支出 | income |
| non_oper_income | q | E | 上市公司利润表 - 加:营业外收入 | income |
| noncurrent_exint | q | E | 上市公司财务指标 - 无息非流动负债 | financial |
| nop_to_ebt | q | E | 上市公司财务指标 - 非营业利润／利润总额 | financial |
| notes_payable | q | E | 上市公司资产负债表 - 应付票据 | balance |
| notes_receiv | q | E | 上市公司资产负债表 - 应收票据 | balance |
| np_last_year | q | E | 上市公司业绩快报 - 去年同期净利润 | express |
| npta | q | E | 上市公司财务指标 - 总资产净利润 | financial |
| ocf_to_debt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/负债合计 | financial |
| ocf_to_interestdebt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/带息债务 | financial |
| ocf_to_netdebt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/净债务 | financial |
| ocf_to_opincome | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/经营活动净收益 | financial |
| ocf_to_or | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/营业收入 | financial |
| ocf_to_profit | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额／营业利润 | financial |
| ocf_to_shortdebt | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额/流动负债 | financial |
| ocf_yoy | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额同比增长率(%) | financial |
| ocfps | q | E | 上市公司财务指标 - 每股经营活动产生的现金流量净额 | financial |
| oi | d | FT | 期货日K线 - 持仓量（手） | future_daily |
| oi | m | FT | 期货月K线 - 持仓量（手） | future_monthly |
| oi | w | FT | 期货周K线 - 持仓量（手） | future_weekly |
| oi_chg | d | FT | 期货日K线 - 持仓量变化 | future_daily |
| oi_chg | m | FT | 期货月K线 - 持仓量变化 | future_monthly |
| oi_chg | w | FT | 期货周K线 - 持仓量变化 | future_weekly |
| oil_and_gas_assets | q | E | 上市公司资产负债表 - 油气资产 | balance |
| op_income | q | E | 上市公司财务指标 - 经营活动净收益 | financial |
| op_last_year | q | E | 上市公司业绩快报 - 去年同期营业利润 | express |
| op_of_gr | q | E | 上市公司财务指标 - 营业利润/营业总收入 | financial |
| op_to_debt | q | E | 上市公司财务指标 - 营业利润／负债合计 | financial |
| op_to_ebt | q | E | 上市公司财务指标 - 营业利润／利润总额 | financial |
| op_to_liqdebt | q | E | 上市公司财务指标 - 营业利润／流动负债 | financial |
| op_yoy | q | E | 上市公司财务指标 - 营业利润同比增长率(%) | financial |
| open | 15min | E | 股票15分钟K线 - 开盘价 | stock_15min |
| open | 15min | FD | 基金15分钟K线 - 开盘价 | fund_15min |
| open | 15min | FT | 期货15分钟K线 - 开盘价 | future_15min |
| open | 15min | IDX | 指数15分钟K线 - 开盘价 | index_15min |
| open | 15min | OPT | 期权15分钟K线 - 开盘价 | options_15min |
| open | 1min | E | 股票60秒K线 - 开盘价 | stock_1min |
| open | 1min | FD | 基金60秒K线 - 开盘价 | fund_1min |
| open | 1min | FT | 期货60秒K线 - 开盘价 | future_1min |
| open | 1min | IDX | 指数60秒K线 - 开盘价 | index_1min |
| open | 1min | OPT | 期权60秒K线 - 开盘价 | options_1min |
| open | 30min | E | 股票30分钟K线 - 开盘价 | stock_30min |
| open | 30min | FD | 基金30分钟K线 - 开盘价 | fund_30min |
| open | 30min | FT | 期货30分钟K线 - 开盘价 | future_30min |
| open | 30min | IDX | 指数30分钟K线 - 开盘价 | index_30min |
| open | 30min | OPT | 期权30分钟K线 - 开盘价 | options_30min |
| open | 5min | E | 股票5分钟K线 - 开盘价 | stock_5min |
| open | 5min | FD | 基金5分钟K线 - 开盘价 | fund_5min |
| open | 5min | FT | 期货5分钟K线 - 开盘价 | future_5min |
| open | 5min | IDX | 指数5分钟K线 - 开盘价 | index_5min |
| open | 5min | OPT | 期权5分钟K线 - 开盘价 | options_5min |
| open | d | E | 股票日K线 - 开盘价 | stock_daily |
| open | d | FD | 基金日K线 - 开盘价 | fund_daily |
| open | d | FT | 期货日K线 - 开盘价 | future_daily |
| open | d | IDX | 指数日K线 - 开盘价 | index_daily |
| open | d | OPT | 期权日K线 - 开盘价 | options_daily |
| open | h | E | 股票小时K线 - 开盘价 | stock_hourly |
| open | h | FD | 基金小时K线 - 开盘价 | fund_hourly |
| open | h | FT | 期货小时K线 - 开盘价 | future_hourly |
| open | h | IDX | 指数小时K线 - 开盘价 | index_hourly |
| open | h | OPT | 期权小时K线 - 开盘价 | options_hourly |
| open | m | E | 股票月K线 - 开盘价 | stock_monthly |
| open | m | FD | 基金月K线 - 开盘价 | fund_monthly |
| open | m | FT | 期货月K线 - 开盘价 | future_monthly |
| open | m | IDX | 指数月K线 - 开盘价 | index_monthly |
| open | w | E | 股票周K线 - 开盘价 | stock_weekly |
| open | w | FD | 基金周K线 - 开盘价 | fund_weekly |
| open | w | FT | 期货周K线 - 开盘价 | future_weekly |
| open | w | IDX | 指数周K线 - 开盘价 | index_weekly |
| open_bps | q | E | 上市公司业绩快报 - 期初每股净资产 | express |
| open_net_assets | q | E | 上市公司业绩快报 - 期初净资产 | express |
| oper_cost | q | E | 上市公司利润表 - 减:营业成本 | income |
| oper_exp | q | E | 上市公司利润表 - 营业支出 | income |
| operate_profit | q | E | 上市公司利润表 - 营业利润 | income |
| opincome_of_ebt | q | E | 上市公司财务指标 - 经营活动净收益/利润总额 | financial |
| or_last_year | q | E | 上市公司业绩快报 - 去年同期营业收入 | express |
| or_yoy | q | E | 上市公司财务指标 - 营业收入同比增长率(%) | financial |
| ordin_risk_reser | q | E | 上市公司资产负债表 - 一般风险准备 | balance |
| oth_assets | q | E | 上市公司资产负债表 - 其他资产 | balance |
| oth_b_income | q | E | 上市公司利润表 - 其他业务收入 | income |
| oth_cash_pay_oper_act | q | E | 上市公司现金流量表 - 支付其他与经营活动有关的现金 | cashflow |
| oth_cash_recp_ral_fnc_act | q | E | 上市公司现金流量表 - 收到其他与筹资活动有关的现金 | cashflow |
| oth_cashpay_ral_fnc_act | q | E | 上市公司现金流量表 - 支付其他与筹资活动有关的现金 | cashflow |
| oth_comp_income | q | E | 上市公司资产负债表 - 其他综合收益 | balance |
| oth_compr_income | q | E | 上市公司利润表 - 其他综合收益 | income |
| oth_cur_assets | q | E | 上市公司资产负债表 - 其他流动资产 | balance |
| oth_cur_liab | q | E | 上市公司资产负债表 - 其他流动负债 | balance |
| oth_debt_invest | q | E | 上市公司资产负债表 - 其他债权投资(元) | balance |
| oth_eq_invest | q | E | 上市公司资产负债表 - 其他权益工具投资(元) | balance |
| oth_eq_ppbond | q | E | 上市公司资产负债表 - 其他权益工具:永续债(元) | balance |
| oth_eqt_tools | q | E | 上市公司资产负债表 - 其他权益工具 | balance |
| oth_eqt_tools_p_shr | q | E | 上市公司资产负债表 - 其他权益工具(优先股) | balance |
| oth_illiq_fin_assets | q | E | 上市公司资产负债表 - 其他非流动金融资产(元) | balance |
| oth_impair_loss_assets | q | E | 上市公司利润表 - 其他资产减值损失 | income |
| oth_income | q | E | 上市公司利润表 - 其他收益 | income |
| oth_liab | q | E | 上市公司资产负债表 - 其他负债 | balance |
| oth_loss_asset | q | E | 上市公司现金流量表 - 其他资产减值损失 | cashflow |
| oth_nca | q | E | 上市公司资产负债表 - 其他非流动资产 | balance |
| oth_ncl | q | E | 上市公司资产负债表 - 其他非流动负债 | balance |
| oth_pay_ral_inv_act | q | E | 上市公司现金流量表 - 支付其他与投资活动有关的现金 | cashflow |
| oth_pay_total | q | E | 上市公司资产负债表 - 其他应付款(合计)(元) | balance |
| oth_payable | q | E | 上市公司资产负债表 - 其他应付款 | balance |
| oth_rcv_total | q | E | 上市公司资产负债表 - 其他应收款(合计)（元） | balance |
| oth_receiv | q | E | 上市公司资产负债表 - 其他应收款 | balance |
| oth_recp_ral_inv_act | q | E | 上市公司现金流量表 - 收到其他与投资活动有关的现金 | cashflow |
| other_bus_cost | q | E | 上市公司利润表 - 其他业务成本 | income |
| others | q | E | 上市公司现金流量表 - 其他 | cashflow |
| out_prem | q | E | 上市公司利润表 - 减:分出保费 | income |
| pay_comm_insur_plcy | q | E | 上市公司现金流量表 - 支付保单红利的现金 | cashflow |
| pay_handling_chrg | q | E | 上市公司现金流量表 - 支付手续费的现金 | cashflow |
| payable_to_reinsurer | q | E | 上市公司资产负债表 - 应付分保账款 | balance |
| payables | q | E | 上市公司资产负债表 - 应付款项 | balance |
| payroll_payable | q | E | 上市公司资产负债表 - 应付职工薪酬 | balance |
| pb | d | E | 股票技术指标 - 市净率（总市值/净资产） | stock_indicator |
| pb | d | IDX | 指数技术指标 - 市净率 | index_indicator |
| pe | d | E | 股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空） | stock_indicator |
| pe | d | IDX | 指数技术指标 - 市盈率 | index_indicator |
| pe_2 | d | E | 股票技术指标 - 动态市盈率 | stock_indicator2 |
| pe_ttm | d | E | 股票技术指标 - 市盈率（TTM，亏损的PE为空） | stock_indicator |
| pe_ttm | d | IDX | 指数技术指标 - 市盈率TTM | index_indicator |
| perf_summary | q | E | 上市公司业绩快报 - 业绩简要说明 | express |
| ph_invest | q | E | 上市公司资产负债表 - 保户储金及投资款 | balance |
| ph_pledge_loans | q | E | 上市公司资产负债表 - 保户质押贷款 | balance |
| pledge_borr | q | E | 上市公司资产负债表 - 其中:质押借款 | balance |
| policy_div_payable | q | E | 上市公司资产负债表 - 应付保单红利 | balance |
| prec_metals | q | E | 上市公司资产负债表 - 贵金属 | balance |
| prem_earned | q | E | 上市公司利润表 - 已赚保费 | income |
| prem_fr_orig_contr | q | E | 上市公司现金流量表 - 收到原保险合同保费取得的现金 | cashflow |
| prem_income | q | E | 上市公司利润表 - 保险业务收入 | income |
| prem_receiv_adva | q | E | 上市公司资产负债表 - 预收保费 | balance |
| prem_refund | q | E | 上市公司利润表 - 退保金 | income |
| premium_receiv | q | E | 上市公司资产负债表 - 应收保费 | balance |
| prepayment | q | E | 上市公司资产负债表 - 预付款项 | balance |
| prfshare_payable_dvd | q | E | 上市公司利润表 - 应付优先股股利 | income |
| proc_issue_bonds | q | E | 上市公司现金流量表 - 发行债券收到的现金 | cashflow |
| produc_bio_assets | q | E | 上市公司资产负债表 - 生产性生物资产 | balance |
| profit_dedt | q | E | 上市公司财务指标 - 扣除非经常性损益后的净利润（扣非净利润） | financial |
| profit_prefin_exp | q | E | 上市公司财务指标 - 扣除财务费用前营业利润 | financial |
| profit_to_gr | q | E | 上市公司财务指标 - 净利润/营业总收入 | financial |
| profit_to_op | q | E | 上市公司财务指标 - 利润总额／营业收入 | financial |
| prov_depr_assets | q | E | 上市公司现金流量表 - 加:资产减值准备 | cashflow |
| ps | d | E | 股票技术指标 - 市销率 | stock_indicator |
| ps_ttm | d | E | 股票技术指标 - 市销率（TTM） | stock_indicator |
| pur_resale_fa | q | E | 上市公司资产负债表 - 买入返售金融资产 | balance |
| q_adminexp_to_gr | q | E | 上市公司财务指标 - 管理费用／营业总收入 (单季度) | financial |
| q_dt_roe | q | E | 上市公司财务指标 - 净资产单季度收益率(扣除非经常损益) | financial |
| q_dtprofit | q | E | 上市公司财务指标 - 扣除非经常损益后的单季度净利润 | financial |
| q_dtprofit_to_profit | q | E | 上市公司财务指标 - 扣除非经常损益后的净利润／净利润(单季度) | financial |
| q_eps | q | E | 上市公司财务指标 - 每股收益(单季度) | financial |
| q_exp_to_sales | q | E | 上市公司财务指标 - 销售期间费用率(单季度) | financial |
| q_finaexp_to_gr | q | E | 上市公司财务指标 - 财务费用／营业总收入 (单季度) | financial |
| q_gc_to_gr | q | E | 上市公司财务指标 - 营业总成本／营业总收入 (单季度) | financial |
| q_gr_qoq | q | E | 上市公司财务指标 - 营业总收入环比增长率(%)(单季度) | financial |
| q_gr_yoy | q | E | 上市公司财务指标 - 营业总收入同比增长率(%)(单季度) | financial |
| q_gsprofit_margin | q | E | 上市公司财务指标 - 销售毛利率(单季度) | financial |
| q_impair_to_gr_ttm | q | E | 上市公司财务指标 - 资产减值损失／营业总收入(单季度) | financial |
| q_investincome | q | E | 上市公司财务指标 - 价值变动单季度净收益 | financial |
| q_investincome_to_ebt | q | E | 上市公司财务指标 - 价值变动净收益／利润总额(单季度) | financial |
| q_netprofit_margin | q | E | 上市公司财务指标 - 销售净利率(单季度) | financial |
| q_netprofit_qoq | q | E | 上市公司财务指标 - 归属母公司股东的净利润环比增长率(%)(单季度) | financial |
| q_netprofit_yoy | q | E | 上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)(单季度) | financial |
| q_npta | q | E | 上市公司财务指标 - 总资产净利润(单季度) | financial |
| q_ocf_to_or | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额／经营活动净收益(单季度) | financial |
| q_ocf_to_sales | q | E | 上市公司财务指标 - 经营活动产生的现金流量净额／营业收入(单季度) | financial |
| q_op_qoq | q | E | 上市公司财务指标 - 营业利润环比增长率(%)(单季度) | financial |
| q_op_to_gr | q | E | 上市公司财务指标 - 营业利润／营业总收入(单季度) | financial |
| q_op_yoy | q | E | 上市公司财务指标 - 营业利润同比增长率(%)(单季度) | financial |
| q_opincome | q | E | 上市公司财务指标 - 经营活动单季度净收益 | financial |
| q_opincome_to_ebt | q | E | 上市公司财务指标 - 经营活动净收益／利润总额(单季度) | financial |
| q_profit_qoq | q | E | 上市公司财务指标 - 净利润环比增长率(%)(单季度) | financial |
| q_profit_to_gr | q | E | 上市公司财务指标 - 净利润／营业总收入(单季度) | financial |
| q_profit_yoy | q | E | 上市公司财务指标 - 净利润同比增长率(%)(单季度) | financial |
| q_roe | q | E | 上市公司财务指标 - 净资产收益率(单季度) | financial |
| q_saleexp_to_gr | q | E | 上市公司财务指标 - 销售费用／营业总收入 (单季度) | financial |
| q_sales_qoq | q | E | 上市公司财务指标 - 营业收入环比增长率(%)(单季度) | financial |
| q_sales_yoy | q | E | 上市公司财务指标 - 营业收入同比增长率(%)(单季度) | financial |
| q_salescash_to_or | q | E | 上市公司财务指标 - 销售商品提供劳务收到的现金／营业收入(单季度) | financial |
| quick_ratio | q | E | 上市公司财务指标 - 速动比率 | financial |
| r_and_d | q | E | 上市公司资产负债表 - 研发支出 | balance |
| rd_exp | q | E | 上市公司财务指标 - 研发费用 | financial |
| receiv_financing | q | E | 上市公司资产负债表 - 应收款项融资 | balance |
| recp_tax_rends | q | E | 上市公司现金流量表 - 收到的税费返还 | cashflow |
| refund_cap_depos | q | E | 上市公司资产负债表 - 存出资本保证金 | balance |
| refund_depos | q | E | 上市公司资产负债表 - 存出保证金 | balance |
| reins_cost_refund | q | E | 上市公司利润表 - 减:摊回分保费用 | income |
| reins_exp | q | E | 上市公司利润表 - 分保费用 | income |
| reins_income | q | E | 上市公司利润表 - 其中:分保费收入 | income |
| reinsur_receiv | q | E | 上市公司资产负债表 - 应收分保账款 | balance |
| reinsur_res_receiv | q | E | 上市公司资产负债表 - 应收分保合同准备金 | balance |
| reser_insur_liab | q | E | 上市公司利润表 - 提取保险责任准备金 | income |
| reser_lins_liab | q | E | 上市公司资产负债表 - 寿险责任准备金 | balance |
| reser_lthins_liab | q | E | 上市公司资产负债表 - 长期健康险责任准备金 | balance |
| reser_outstd_claims | q | E | 上市公司资产负债表 - 未决赔款准备金 | balance |
| reser_une_prem | q | E | 上市公司资产负债表 - 未到期责任准备金 | balance |
| retained_earnings | q | E | 上市公司财务指标 - 留存收益 | financial |
| retainedps | q | E | 上市公司财务指标 - 每股留存收益 | financial |
| revenue | q | E | 上市公司利润表 - 营业收入 | income |
| revenue_ps | q | E | 上市公司财务指标 - 每股营业收入 | financial |
| roa | q | E | 上市公司财务指标 - 总资产报酬率 | financial |
| roa2_yearly | q | E | 上市公司财务指标 - 年化总资产报酬率 | financial |
| roa_dp | q | E | 上市公司财务指标 - 总资产净利率(杜邦分析) | financial |
| roa_yearly | q | E | 上市公司财务指标 - 年化总资产净利率 | financial |
| roe | q | E | 上市公司财务指标 - 净资产收益率 | financial |
| roe_avg | q | E | 上市公司财务指标 - 平均净资产收益率(增发条件) | financial |
| roe_dt | q | E | 上市公司财务指标 - 净资产收益率(扣除非经常损益) | financial |
| roe_waa | q | E | 上市公司财务指标 - 加权平均净资产收益率 | financial |
| roe_yearly | q | E | 上市公司财务指标 - 年化净资产收益率 | financial |
| roe_yoy | q | E | 上市公司财务指标 - 净资产收益率(摊薄)同比增长率(%) | financial |
| roic | q | E | 上市公司财务指标 - 投入资本回报率 | financial |
| roic_yearly | q | E | 上市公司财务指标 - 年化投入资本回报率 | financial |
| rr_reins_lins_liab | q | E | 上市公司资产负债表 - 应收分保寿险责任准备金 | balance |
| rr_reins_lthins_liab | q | E | 上市公司资产负债表 - 应收分保长期健康险责任准备金 | balance |
| rr_reins_outstd_cla | q | E | 上市公司资产负债表 - 应收分保未决赔款准备金 | balance |
| rr_reins_une_prem | q | E | 上市公司资产负债表 - 应收分保未到期责任准备金 | balance |
| rsrv_insur_cont | q | E | 上市公司资产负债表 - 保险合同准备金 | balance |
| saleexp_to_gr | q | E | 上市公司财务指标 - 销售费用/营业总收入 | financial |
| salescash_to_or | q | E | 上市公司财务指标 - 销售商品提供劳务收到的现金/营业收入 | financial |
| sell_elg_amount | d | E | 个股资金流向 - 特大单卖出金额（万元） | money_flow |
| sell_elg_vol | d | E | 个股资金流向 - 特大单卖出量（手） | money_flow |
| sell_exp | q | E | 上市公司利润表 - 减:销售费用 | income |
| sell_lg_amount | d | E | 个股资金流向 - 大单卖出金额（万元） | money_flow |
| sell_lg_vol | d | E | 个股资金流向 - 大单卖出量（手） | money_flow |
| sell_md_amount | d | E | 个股资金流向 - 中单卖出金额（万元） | money_flow |
| sell_md_vol | d | E | 个股资金流向 - 中单卖出量（手） | money_flow |
| sell_sm_amount | d | E | 个股资金流向 - 小单卖出金额（万元） | money_flow |
| sell_sm_vol | d | E | 个股资金流向 - 小单卖出量（手） | money_flow |
| selling | d | E | 股票技术指标 - 内盘（主动卖，手） | stock_indicator2 |
| sett_rsrv | q | E | 上市公司资产负债表 - 结算备付金 | balance |
| settle | d | FT | 期货日K线 - 结算价 | future_daily |
| settle | m | FT | 期货月K线 - 结算价 | future_monthly |
| settle | w | FT | 期货周K线 - 结算价 | future_weekly |
| settle_chg | d | FT | 期货日K线 - 结算价涨跌 | future_daily |
| settle_chg | m | FT | 期货月K线 - 结算价涨跌 | future_monthly |
| settle_chg | w | FT | 期货周K线 - 结算价涨跌 | future_weekly |
| sold_for_repur_fa | q | E | 上市公司资产负债表 - 卖出回购金融资产款 | balance |
| special_rese | q | E | 上市公司资产负债表 - 专项储备 | balance |
| specific_payables | q | E | 上市公司资产负债表 - 专项应付款 | balance |
| st_bonds_payable | q | E | 上市公司资产负债表 - 应付短期债券 | balance |
| st_borr | q | E | 上市公司资产负债表 - 短期借款 | balance |
| st_cash_out_act | q | E | 上市公司现金流量表 - 经营活动现金流出小计 | cashflow |
| st_fin_payable | q | E | 上市公司资产负债表 - 应付短期融资款 | balance |
| stot_cash_in_fnc_act | q | E | 上市公司现金流量表 - 筹资活动现金流入小计 | cashflow |
| stot_cashout_fnc_act | q | E | 上市公司现金流量表 - 筹资活动现金流出小计 | cashflow |
| stot_inflows_inv_act | q | E | 上市公司现金流量表 - 投资活动现金流入小计 | cashflow |
| stot_out_inv_act | q | E | 上市公司现金流量表 - 投资活动现金流出小计 | cashflow |
| strength | d | E | 股票技术指标 - 强弱度(%) | stock_indicator2 |
| surplus_rese | q | E | 上市公司资产负债表 - 盈余公积金 | balance |
| surplus_rese_ps | q | E | 上市公司财务指标 - 每股盈余公积 | financial |
| sw_amount | d | IDX | 申万指数日K线 - 成交额 （万元） | sw_index_daily |
| sw_change | d | IDX | 申万指数日K线 - 涨跌额 | sw_index_daily |
| sw_close | d | IDX | 申万指数日K线 - 收盘价 | sw_index_daily |
| sw_float_mv | d | IDX | 申万指数日K线 - 流通市值 （万元） | sw_index_daily |
| sw_high | d | IDX | 申万指数日K线 - 最高价 | sw_index_daily |
| sw_low | d | IDX | 申万指数日K线 - 最低价 | sw_index_daily |
| sw_open | d | IDX | 申万指数日K线 - 开盘价 | sw_index_daily |
| sw_pb | d | IDX | 申万指数日K线 - 市净率 | sw_index_daily |
| sw_pct_change | d | IDX | 申万指数日K线 - 涨跌幅 | sw_index_daily |
| sw_pe | d | IDX | 申万指数日K线 - 市盈率 | sw_index_daily |
| sw_total_mv | d | IDX | 申万指数日K线 - 总市值 （万元） | sw_index_daily |
| sw_vol | d | IDX | 申万指数日K线 - 成交量 （万股） | sw_index_daily |
| swing | d | E | 股票技术指标 - 振幅 | stock_indicator2 |
| t_compr_income | q | E | 上市公司利润表 - 综合收益总额 | income |
| tangasset_to_intdebt | q | E | 上市公司财务指标 - 有形资产/带息债务 | financial |
| tangible_asset | q | E | 上市公司财务指标 - 有形资产 | financial |
| tangibleasset_to_debt | q | E | 上市公司财务指标 - 有形资产/负债合计 | financial |
| tangibleasset_to_netdebt | q | E | 上市公司财务指标 - 有形资产/净债务 | financial |
| tax_to_ebt | q | E | 上市公司财务指标 - 所得税/利润总额 | financial |
| taxes_payable | q | E | 上市公司资产负债表 - 应交税费 | balance |
| tbassets_to_totalassets | q | E | 上市公司财务指标 - 有形资产/总资产 | financial |
| ths_avg_price | d | IDX | 同花顺指数日K线 - 平均价 | ths_index_daily |
| ths_change | d | IDX | 同花顺指数日K线 - 最低价 | ths_index_daily |
| ths_close | d | IDX | 同花顺指数日K线 - 收盘价 | ths_index_daily |
| ths_float_mv | d | IDX | 同花顺指数日K线 - 流通市值 （万元） | ths_index_daily |
| ths_high | d | IDX | 同花顺指数日K线 - 最高价 | ths_index_daily |
| ths_low | d | IDX | 同花顺指数日K线 - 最低价 | ths_index_daily |
| ths_open | d | IDX | 同花顺指数日K线 - 开盘价 | ths_index_daily |
| ths_pct_change | d | IDX | 同花顺指数日K线 - 涨跌幅 | ths_index_daily |
| ths_total_mv | d | IDX | 同花顺指数日K线 - 总市值 （万元） | ths_index_daily |
| ths_turnover | d | IDX | 同花顺指数日K线 - 换手率 | ths_index_daily |
| ths_vol | d | IDX | 同花顺指数日K线 - 成交量 （万股） | ths_index_daily |
| time_deposits | q | E | 上市公司资产负债表 - 定期存款 | balance |
| total_assets | q | E | 上市公司资产负债表 - 资产总计 | balance |
| total_cogs | q | E | 上市公司利润表 - 营业总成本 | income |
| total_cur_assets | q | E | 上市公司资产负债表 - 流动资产合计 | balance |
| total_cur_liab | q | E | 上市公司资产负债表 - 流动负债合计 | balance |
| total_fa_trun | q | E | 上市公司财务指标 - 固定资产合计周转率 | financial |
| total_hldr_eqy_exc_min_int | q | E | 上市公司资产负债表 - 股东权益合计(不含少数股东权益) | balance |
| total_hldr_eqy_inc_min_int | q | E | 上市公司资产负债表 - 股东权益合计(含少数股东权益) | balance |
| total_liab | q | E | 上市公司资产负债表 - 负债合计 | balance |
| total_liab_hldr_eqy | q | E | 上市公司资产负债表 - 负债及股东权益总计 | balance |
| total_mv | d | E | 股票技术指标 - 总市值 （万元） | stock_indicator |
| total_mv | d | IDX | 指数技术指标 - 当日总市值（元） | index_indicator |
| total_mv_2 | d | E | 股票技术指标 - 总市值(亿元) | stock_indicator2 |
| total_nca | q | E | 上市公司资产负债表 - 非流动资产合计 | balance |
| total_ncl | q | E | 上市公司资产负债表 - 非流动负债合计 | balance |
| total_netasset | d | FD | 基金净值 - 累计资产净值 | fund_nav |
| total_opcost | q | E | 上市公司利润表 - 营业总成本（二） | income |
| total_profit | q | E | 上市公司利润表 - 利润总额 | income |
| total_revenue | q | E | 上市公司利润表 - 营业总收入 | income |
| total_revenue_ps | q | E | 上市公司财务指标 - 每股营业总收入 | financial |
| total_share | d | E | 股票技术指标 - 总股本 （万股） | stock_indicator |
| total_share | d | IDX | 指数技术指标 - 当日总股本（股） | index_indicator |
| total_share | q | E | 上市公司资产负债表 - 期末总股本 | balance |
| total_share_b | d | E | 股票技术指标 - 总股本(亿) | stock_indicator2 |
| tp_last_year | q | E | 上市公司业绩快报 - 去年同期利润总额 | express |
| tr_yoy | q | E | 上市公司财务指标 - 营业总收入同比增长率(%) | financial |
| trad_asset | q | E | 上市公司资产负债表 - 交易性金融资产 | balance |
| trade_cal | d | None | 交易日历 | trade_calendar |
| trading_fl | q | E | 上市公司资产负债表 - 交易性金融负债 | balance |
| transac_seat_fee | q | E | 上市公司资产负债表 - 其中:交易席位费 | balance |
| transfer_housing_imprest | q | E | 上市公司利润表 - 住房周转金转入 | income |
| transfer_oth | q | E | 上市公司利润表 - 其他转入 | income |
| transfer_surplus_rese | q | E | 上市公司利润表 - 盈余公积转入 | income |
| treasury_share | q | E | 上市公司资产负债表 - 减:库存股 | balance |
| turn_days | q | E | 上市公司财务指标 - 营业周期 | financial |
| turn_over | d | E | 股票技术指标 - 换手率 | stock_indicator2 |
| turnover_rate | d | E | 股票技术指标 - 换手率（%） | stock_indicator |
| turnover_rate | d | IDX | 指数技术指标 - 换手率 | index_indicator |
| turnover_rate_f | d | E | 股票技术指标 - 换手率（自由流通股） | stock_indicator |
| turnover_rate_f | d | IDX | 指数技术指标 - 换手率(基于自由流通股本) | index_indicator |
| uncon_invest_loss | q | E | 上市公司现金流量表 - 未确认投资损失 | cashflow |
| undist_profit | q | E | 上市公司利润表 - 年初未分配利润 | income |
| undist_profit_ps | q | E | 上市公司财务指标 - 每股未分配利润 | financial |
| undistr_porfit | q | E | 上市公司资产负债表 - 未分配利润 | balance |
| une_prem_reser | q | E | 上市公司利润表 - 提取未到期责任准备金 | income |
| unit_nav | d | FD | 基金净值 - 单位净值 | fund_nav |
| up_limit | d | E | 涨停板 - 涨停价 | stock_limit |
| use_right_asset_dep | q | E | 上市公司现金流量表 - 使用权资产折旧 | cashflow |
| use_right_assets | q | E | 上市公司资产负债表 - 使用权资产 | balance |
| valuechange_income | q | E | 上市公司财务指标 - 价值变动净收益 | financial |
| vol_ratio | d | E | 股票技术指标 - 量比 | stock_indicator2 |
| volume | 15min | E | 股票15分钟K线 - 成交量 （手） | stock_15min |
| volume | 15min | FD | 基金15分钟K线 - 成交量 （手） | fund_15min |
| volume | 15min | FT | 期货15分钟K线 - 成交量 （手） | future_15min |
| volume | 15min | IDX | 指数15分钟K线 - 成交量 （手） | index_15min |
| volume | 15min | OPT | 期权15分钟K线 - 成交量 （手） | options_15min |
| volume | 1min | E | 股票60秒K线 - 成交量 （手） | stock_1min |
| volume | 1min | FD | 基金60秒K线 - 成交量 （手） | fund_1min |
| volume | 1min | FT | 期货60秒K线 - 成交量 （手） | future_1min |
| volume | 1min | IDX | 指数60秒K线 - 成交量 （手） | index_1min |
| volume | 1min | OPT | 期权60秒K线 - 成交量 （手） | options_1min |
| volume | 30min | E | 股票30分钟K线 - 成交量 （手） | stock_30min |
| volume | 30min | FD | 基金30分钟K线 - 成交量 （手） | fund_30min |
| volume | 30min | FT | 期货30分钟K线 - 成交量 （手） | future_30min |
| volume | 30min | IDX | 指数30分钟K线 - 成交量 （手） | index_30min |
| volume | 30min | OPT | 期权30分钟K线 - 成交量 （手） | options_30min |
| volume | 5min | E | 股票5分钟K线 - 成交量 （手） | stock_5min |
| volume | 5min | FD | 基金5分钟K线 - 成交量 （手） | fund_5min |
| volume | 5min | FT | 期货5分钟K线 - 成交量 （手） | future_5min |
| volume | 5min | IDX | 指数5分钟K线 - 成交量 （手） | index_5min |
| volume | 5min | OPT | 期权5分钟K线 - 成交量 （手） | options_5min |
| volume | d | E | 股票日K线 - 成交量 （手） | stock_daily |
| volume | d | FD | 基金日K线 - 成交量 （手） | fund_daily |
| volume | d | FT | 期货日K线 - 成交量 （手） | future_daily |
| volume | d | IDX | 指数日K线 - 成交量 （手） | index_daily |
| volume | d | OPT | 期权日K线 - 成交量 （手） | options_daily |
| volume | h | E | 股票小时K线 - 成交量 （手） | stock_hourly |
| volume | h | FD | 基金小时K线 - 成交量 （手） | fund_hourly |
| volume | h | FT | 期货小时K线 - 成交量 （手） | future_hourly |
| volume | h | IDX | 指数小时K线 - 成交量 （手） | index_hourly |
| volume | h | OPT | 期权小时K线 - 成交量 （手） | options_hourly |
| volume | m | E | 股票月K线 - 成交量 （手） | stock_monthly |
| volume | m | FD | 基金月K线 - 成交量 （手） | fund_monthly |
| volume | m | FT | 期货月K线 - 成交量（手） | future_monthly |
| volume | m | IDX | 指数月K线 - 成交量 （手） | index_monthly |
| volume | w | E | 股票周K线 - 成交量 （手） | stock_weekly |
| volume | w | FD | 基金周K线 - 成交量 （手） | fund_weekly |
| volume | w | FT | 期货周K线 - 成交量（手） | future_weekly |
| volume | w | IDX | 指数周K线 - 成交量 （手） | index_weekly |
| volume_ratio | d | E | 股票技术指标 - 量比 | stock_indicator |
| withdra_biz_devfund | q | E | 上市公司利润表 - 提取企业发展基金 | income |
| withdra_legal_pubfund | q | E | 上市公司利润表 - 提取法定公益金 | income |
| withdra_legal_surplus | q | E | 上市公司利润表 - 提取法定盈余公积 | income |
| withdra_oth_ersu | q | E | 上市公司利润表 - 提取任意盈余公积金 | income |
| withdra_rese_fund | q | E | 上市公司利润表 - 提取储备基金 | income |
| workers_welfare | q | E | 上市公司利润表 - 职工奖金福利 | income |
| working_capital | q | E | 上市公司财务指标 - 营运资金 | financial |
| yoy_dedu_np | q | E | 上市公司业绩快报 - 同比增长率:归属母公司股东的净利润 | express |
| yoy_eps | q | E | 上市公司业绩快报 - 同比增长率:基本每股收益 | express |
| yoy_equity | q | E | 上市公司业绩快报 - 比年初增长率:归属母公司的股东权益 | express |
| yoy_net_profit | q | E | 上市公司业绩快报 - 去年同期修正后净利润 | express |
| yoy_op | q | E | 上市公司业绩快报 - 同比增长率:营业利润 | express |
| yoy_roe | q | E | 上市公司业绩快报 - 同比增减:加权平均净资产收益率 | express |
| yoy_sales | q | E | 上市公司业绩快报 - 同比增长率:营业收入 | express |
| yoy_tp | q | E | 上市公司业绩快报 - 同比增长率:利润总额 | express |
