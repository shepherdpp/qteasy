<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-20 06:16 UTC -->
<!-- business_group: events -->
<!-- row_count: 132 -->

# 交易行为与事件

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 按**业务类别**生成，共 **132** 条。

请勿手改；更新内置类型后请重跑生成脚本。列含义与推荐读法见 [清单入口](../index.md)。`acquisition_type` / `table_name` 仅供对照 refill。

| name | freq | asset_type | description | kind | usable_in | acquisition_type | table_name |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base_date | d | E | 实施-基准日 | history | history_panel,strategy | selected_events | dividend |
| base_share | d | E | 实施-基准股本（万） | history | history_panel,strategy | selected_events | dividend |
| block_trade_amount | d | E | 大宗交易 - 成交金额 | history | history_panel,strategy | event_signal | block_trade |
| block_trade_buyer | d | E | 大宗交易 - 买方营业部 | history | history_panel,strategy | event_signal | block_trade |
| block_trade_price | d | E | 大宗交易 - 成交价 | history | history_panel,strategy | event_signal | block_trade |
| block_trade_seller | d | E | 大宗交易 - 卖方营业部 | history | history_panel,strategy | event_signal | block_trade |
| block_trade_vol | d | E | 大宗交易 - 成交量（万股） | history | history_panel,strategy | event_signal | block_trade |
| buy | d | E | 龙虎榜机构明细 - 买入额（元） | history | history_panel,strategy | event_signal | top_inst |
| buy_elg_amount | d | E | 个股资金流向 - 特大单买入金额（万元） | history | history_panel,strategy | direct | money_flow |
| buy_elg_vol | d | E | 个股资金流向 - 特大单买入量（手） | history | history_panel,strategy | direct | money_flow |
| buy_lg_amount | d | E | 个股资金流向 - 大单买入金额（万元） | history | history_panel,strategy | direct | money_flow |
| buy_lg_vol | d | E | 个股资金流向 - 大单买入量（手） | history | history_panel,strategy | direct | money_flow |
| buy_md_amount | d | E | 个股资金流向 - 中单买入金额（万元） | history | history_panel,strategy | direct | money_flow |
| buy_md_vol | d | E | 个股资金流向 - 中单买入量（手） | history | history_panel,strategy | direct | money_flow |
| buy_rate | d | E | 龙虎榜机构明细 - 买入占总成交比例 | history | history_panel,strategy | event_signal | top_inst |
| buy_sm_amount | d | E | 个股资金流向 - 小单买入金额（万元） | history | history_panel,strategy | direct | money_flow |
| buy_sm_vol | d | E | 个股资金流向 - 小单买入量（手） | history | history_panel,strategy | direct | money_flow |
| cash_div | d | E | 实施-每股分红（税后） | history | history_panel,strategy | selected_events | dividend |
| cash_div_approved | d | E | 股东大会批准-每股分红（税后） | history | history_panel,strategy | selected_events | dividend |
| cash_div_planned | d | E | 预案-每股分红（税后） | history | history_panel,strategy | selected_events | dividend |
| cash_div_tax | d | E | 实施-每股分红（税前） | history | history_panel,strategy | selected_events | dividend |
| cash_div_tax_approved | d | E | 股东大会批准-每股分红（税前） | history | history_panel,strategy | selected_events | dividend |
| cash_div_tax_planned | d | E | 预案-每股分红（税前） | history | history_panel,strategy | selected_events | dividend |
| change_reason | d | E | 业绩变动原因 | history | history_panel,strategy | event_signal | forecast |
| cur_name | d | E | 股票 - 当前最新证券名称 | history | history_panel,strategy | event_status | stock_names |
| down_limit | d | E | 跌停板 - 跌停价 | history | history_panel,strategy | direct | stock_limit |
| ex_date | d | E | 实施-除权除息日 | history | history_panel,strategy | selected_events | dividend |
| exalter | d | E | 龙虎榜机构明细 - 营业部名称 | history | history_panel,strategy | event_signal | top_inst |
| first_ann_date | d | E | 首次公告日 | history | history_panel,strategy | event_signal | forecast |
| hk_top10_amount | d | E | 港股通十大成交 - 累计成交额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_close | d | E | 港股通十大成交 - 收盘价 | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_net_amount | d | E | 港股通十大成交 - 净买入金额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_p_change | d | E | 港股通十大成交 - 涨跌幅 | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_rank | d | E | 港股通十大成交 - 排名 | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_sh_amount | d | E | 港股通十大成交 - 沪市成交额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_sh_buy | d | E | 港股通十大成交 - 深市净买入金额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_sh_net_amount | d | E | 港股通十大成交 - 沪市净买入额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_sh_sell | d | E | 港股通十大成交 - 深市净买入金额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_sz_amount | d | E | 港股通十大成交 - 深市成交金额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| hk_top10_sz_net_amount | d | E | 港股通十大成交 - 深市净买入额（元） | history | history_panel,strategy | direct | hk_top10_stock |
| imp_ann_date | d | E | 实施-实施公告日 | history | history_panel,strategy | selected_events | dividend |
| is_HS_top10 | d | E | 沪深港通十大成交股上榜 | history | history_panel,strategy | event_signal | hs_top10_stock |
| is_suspended | d | E | 停复牌类型：S-停牌，R-复牌 | history | history_panel,strategy | event_signal | stock_suspend |
| is_trade_day\|% | d | None | 是否交易日-市场代码：% | reference | reference_api,strategy | selection | trade_calendar |
| last_parent_net | d | E | 上年同期归属母公司净利润 | history | history_panel,strategy | event_signal | forecast |
| manager_title | d | E | 公司高管信息 - 岗位 | history | none | event_multi_stat | stk_managers |
| managers_birth_year | d | FD | 基金经理 - 出生年份 | history | none | event_multi_stat | fund_manager |
| managers_birthday | d | E | 公司高管信息 - 出生年月 | history | none | event_multi_stat | stk_managers |
| managers_edu | d | E | 公司高管信息 - 学历 | history | none | event_multi_stat | stk_managers |
| managers_edu | d | FD | 基金经理 - 学历 | history | none | event_multi_stat | fund_manager |
| managers_gender | d | E | 公司高管信息 - 性别 | history | none | event_multi_stat | stk_managers |
| managers_gender | d | FD | 基金经理 - 性别 | history | none | event_multi_stat | fund_manager |
| managers_lev | d | E | 公司高管信息 - 岗位类别 | history | none | event_multi_stat | stk_managers |
| managers_name | d | E | 公司高管信息 - 高管姓名 | history | none | event_multi_stat | stk_managers |
| managers_name | d | FD | 基金经理姓名 | history | none | event_multi_stat | fund_manager |
| managers_national | d | E | 公司高管信息 - 国籍 | history | none | event_multi_stat | stk_managers |
| managers_resume | d | E | 公司高管信息 - 个人简历 | history | none | event_multi_stat | stk_managers |
| managers_resume | d | FD | 基金经理 - 简历 | history | none | event_multi_stat | fund_manager |
| margin_detail_rqchl | d | E | 融资融券交易明细 - 融券偿还量(股) | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rqmcl | d | E | 融资融券交易明细 - 融券卖出量(股,份,手) | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rqye | d | E | 融资融券交易明细 - 融券余额(元) | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rqyl | d | E | 融资融券交易明细 - 融券余量（股） | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rzche | d | E | 融资融券交易明细 - 融资偿还额(元) | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rzmre | d | E | 融资融券交易明细 - 融资买入额(元) | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rzrqye | d | E | 融资融券交易明细 - 融资融券余额(元) | history | history_panel,strategy | event_signal | margin_detail |
| margin_detail_rzye | d | E | 融资融券交易明细 - 融资余额(元) | history | history_panel,strategy | event_signal | margin_detail |
| nationality | d | FD | 基金经理 - 国籍 | history | none | event_multi_stat | fund_manager |
| net_buy | d | E | 龙虎榜机构明细 - 净成交额（元） | history | history_panel,strategy | event_signal | top_inst |
| net_mf_amount | d | E | 个股资金流向 - 净流入额（万元） | history | history_panel,strategy | direct | money_flow |
| net_mf_vol | d | E | 个股资金流向 - 净流入量（手） | history | history_panel,strategy | direct | money_flow |
| net_profit_max | d | E | 预告净利润上限(万元) | history | history_panel,strategy | event_signal | forecast |
| net_profit_min | d | E | 预告净利润下限(万元) | history | history_panel,strategy | event_signal | forecast |
| p_change_max | d | E | 预告净利润变动幅度上限(%) | history | history_panel,strategy | event_signal | forecast |
| p_change_min | d | E | 预告净利润变动幅度下限(%) | history | history_panel,strategy | event_signal | forecast |
| pay_date | d | E | 实施-派息日 | history | history_panel,strategy | selected_events | dividend |
| pre_trade_day\|% | d | None | 上一交易日 | reference | reference_api,strategy | selection | trade_calendar |
| reason | d | E | 龙虎榜机构明细 - 上榜理由 | history | history_panel,strategy | event_signal | top_inst |
| record_date | d | E | 实施-股权登记日 | history | history_panel,strategy | selected_events | dividend |
| sell | d | E | 龙虎榜机构明细 - 卖出额（元） | history | history_panel,strategy | event_signal | top_inst |
| sell_elg_amount | d | E | 个股资金流向 - 特大单卖出金额（万元） | history | history_panel,strategy | direct | money_flow |
| sell_elg_vol | d | E | 个股资金流向 - 特大单卖出量（手） | history | history_panel,strategy | direct | money_flow |
| sell_lg_amount | d | E | 个股资金流向 - 大单卖出金额（万元） | history | history_panel,strategy | direct | money_flow |
| sell_lg_vol | d | E | 个股资金流向 - 大单卖出量（手） | history | history_panel,strategy | direct | money_flow |
| sell_md_amount | d | E | 个股资金流向 - 中单卖出金额（万元） | history | history_panel,strategy | direct | money_flow |
| sell_md_vol | d | E | 个股资金流向 - 中单卖出量（手） | history | history_panel,strategy | direct | money_flow |
| sell_rate | d | E | 龙虎榜机构明细 - 卖出占总成交比例 | history | history_panel,strategy | event_signal | top_inst |
| sell_sm_amount | d | E | 个股资金流向 - 小单卖出金额（万元） | history | history_panel,strategy | direct | money_flow |
| sell_sm_vol | d | E | 个股资金流向 - 小单卖出量（手） | history | history_panel,strategy | direct | money_flow |
| side | d | E | 龙虎榜机构明细 - 买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名 | history | history_panel,strategy | event_signal | top_inst |
| stk_bo_rate | d | E | 实施-每股送股比例 | history | history_panel,strategy | selected_events | dividend |
| stk_bo_rate_approved | d | E | 股东大会批准-每股送股比例 | history | history_panel,strategy | selected_events | dividend |
| stk_bo_rate_planned | d | E | 预案-每股送股比例 | history | history_panel,strategy | selected_events | dividend |
| stk_co_rate | d | E | 实施-每股转增比例 | history | history_panel,strategy | selected_events | dividend |
| stk_co_rate_approved | d | E | 股东大会批准-每股转增比例 | history | history_panel,strategy | selected_events | dividend |
| stk_co_rate_planned | d | E | 预案-每股转增比例 | history | history_panel,strategy | selected_events | dividend |
| stk_div | d | E | 实施-每股送转 | history | history_panel,strategy | selected_events | dividend |
| stk_div_approved | d | E | 股东大会批准-每股送转 | history | history_panel,strategy | selected_events | dividend |
| stk_div_planned | d | E | 预案-每股送转 | history | history_panel,strategy | selected_events | dividend |
| stock_holder_trade_after_ratio | d | E | 股东交易 - 变动后占流通比例（%） | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_after_share | d | E | 股东交易 - 变动后持股 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_avg_price | d | E | 股东交易 - 平均价格 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_begin_date | d | E | 股东交易 - 增减持开始日期 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_change_ratio | d | E | 股东交易 - 占流通比例（%） | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_change_vol | d | E | 股东交易 - 变动数量 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_close_date | d | E | 股东交易 - 增减持结束日期 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_in_de | d | E | 股东交易 - 类型IN增持DE减持 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_name | d | E | 股东交易 - 股东名称 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_total_share | d | E | 股东交易 - 持股总数 | history | history_panel,strategy | event_signal | stock_holder_trade |
| stock_holder_trade_type | d | E | 股东交易 - 股东类型G高管P个人C公司 | history | history_panel,strategy | event_signal | stock_holder_trade |
| summary | d | E | 业绩预告摘要 | history | history_panel,strategy | event_signal | forecast |
| suspend_timing | d | E | 日内停牌时间段 | history | history_panel,strategy | event_signal | stock_suspend |
| top10_amount | d | E | 沪深港通十大成交股上榜 - 成交金额（元） | history | history_panel,strategy | event_signal | hs_top10_stock |
| top10_buy | d | E | 沪深港通十大成交股上榜 - 买入金额（元） | history | history_panel,strategy | event_signal | hs_top10_stock |
| top10_change | d | E | 沪深港通十大成交股上榜 - 涨跌额 | history | history_panel,strategy | event_signal | hs_top10_stock |
| top10_close | d | E | 沪深港通十大成交股上榜 - 收盘价 | history | history_panel,strategy | event_signal | hs_top10_stock |
| top10_net_amount | d | E | 沪深港通十大成交股上榜 - 净成交金额（元） | history | history_panel,strategy | event_signal | hs_top10_stock |
| top10_rank | d | E | 沪深港通十大成交股上榜 - 资金排名 | history | history_panel,strategy | event_signal | hs_top10_stock |
| top10_sell | d | E | 沪深港通十大成交股上榜 - 卖出金额（元） | history | history_panel,strategy | event_signal | hs_top10_stock |
| top_list_amount | d | E | 龙虎榜交易明细 - 总成交额 | history | history_panel,strategy | event_signal | top_list |
| top_list_amount_rate | d | E | 龙虎榜交易明细 - 龙虎榜成交额占比 | history | history_panel,strategy | event_signal | top_list |
| top_list_close | d | E | 龙虎榜交易明细 - 收盘价 | history | history_panel,strategy | event_signal | top_list |
| top_list_float_values | d | E | 龙虎榜交易明细 - 当日流通市值 | history | history_panel,strategy | event_signal | top_list |
| top_list_l_amount | d | E | 龙虎榜交易明细- 龙虎榜成交额 | history | history_panel,strategy | event_signal | top_list |
| top_list_l_buy | d | E | 龙虎榜交易明细 - 龙虎榜买入额 | history | history_panel,strategy | event_signal | top_list |
| top_list_l_sell | d | E | 龙虎榜交易明细 - 龙虎榜卖出额 | history | history_panel,strategy | event_signal | top_list |
| top_list_net_amount | d | E | 龙虎榜交易明细 - 龙虎榜净买入额 | history | history_panel,strategy | event_signal | top_list |
| top_list_net_rate | d | E | 龙虎榜交易明细 - 龙虎榜净买额占比 | history | history_panel,strategy | event_signal | top_list |
| top_list_pct_change | d | E | 龙虎榜交易明细 - 涨跌幅 | history | history_panel,strategy | event_signal | top_list |
| top_list_reason | d | E | 龙虎榜交易明细 - 上榜理由 | history | history_panel,strategy | event_signal | top_list |
| top_list_turnover_rate | d | E | 龙虎榜交易明细 - 换手率 | history | history_panel,strategy | event_signal | top_list |
| trade_cal | d | None | 交易日历 | reference | reference_api,strategy | direct | trade_calendar |
| up_limit | d | E | 涨停板 - 涨停价 | history | history_panel,strategy | direct | stock_limit |
