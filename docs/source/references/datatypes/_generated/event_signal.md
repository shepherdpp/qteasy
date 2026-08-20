<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-19 17:34 UTC -->
<!-- acquisition_type: event_signal -->
<!-- row_count: 62 -->

# 事件信号（event_signal）

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 生成，共 **62** 条。

请勿手改；更新内置类型后请重跑生成脚本。

| name | freq | asset_type | description | table_name | kind | usable_in |
| --- | --- | --- | --- | --- | --- | --- |
| block_trade_amount | d | E | 大宗交易 - 成交金额 | block_trade | history | history_panel,strategy |
| block_trade_buyer | d | E | 大宗交易 - 买方营业部 | block_trade | history | history_panel,strategy |
| block_trade_price | d | E | 大宗交易 - 成交价 | block_trade | history | history_panel,strategy |
| block_trade_seller | d | E | 大宗交易 - 卖方营业部 | block_trade | history | history_panel,strategy |
| block_trade_vol | d | E | 大宗交易 - 成交量（万股） | block_trade | history | history_panel,strategy |
| buy | d | E | 龙虎榜机构明细 - 买入额（元） | top_inst | history | history_panel,strategy |
| buy_rate | d | E | 龙虎榜机构明细 - 买入占总成交比例 | top_inst | history | history_panel,strategy |
| change_reason | d | E | 业绩变动原因 | forecast | history | history_panel,strategy |
| exalter | d | E | 龙虎榜机构明细 - 营业部名称 | top_inst | history | history_panel,strategy |
| first_ann_date | d | E | 首次公告日 | forecast | history | history_panel,strategy |
| is_HS_top10 | d | E | 沪深港通十大成交股上榜 | hs_top10_stock | history | history_panel,strategy |
| is_suspended | d | E | 停复牌类型：S-停牌，R-复牌 | stock_suspend | history | history_panel,strategy |
| last_parent_net | d | E | 上年同期归属母公司净利润 | forecast | history | history_panel,strategy |
| margin_detail_rqchl | d | E | 融资融券交易明细 - 融券偿还量(股) | margin_detail | history | history_panel,strategy |
| margin_detail_rqmcl | d | E | 融资融券交易明细 - 融券卖出量(股,份,手) | margin_detail | history | history_panel,strategy |
| margin_detail_rqye | d | E | 融资融券交易明细 - 融券余额(元) | margin_detail | history | history_panel,strategy |
| margin_detail_rqyl | d | E | 融资融券交易明细 - 融券余量（股） | margin_detail | history | history_panel,strategy |
| margin_detail_rzche | d | E | 融资融券交易明细 - 融资偿还额(元) | margin_detail | history | history_panel,strategy |
| margin_detail_rzmre | d | E | 融资融券交易明细 - 融资买入额(元) | margin_detail | history | history_panel,strategy |
| margin_detail_rzrqye | d | E | 融资融券交易明细 - 融资融券余额(元) | margin_detail | history | history_panel,strategy |
| margin_detail_rzye | d | E | 融资融券交易明细 - 融资余额(元) | margin_detail | history | history_panel,strategy |
| net_buy | d | E | 龙虎榜机构明细 - 净成交额（元） | top_inst | history | history_panel,strategy |
| net_profit_max | d | E | 预告净利润上限(万元) | forecast | history | history_panel,strategy |
| net_profit_min | d | E | 预告净利润下限(万元) | forecast | history | history_panel,strategy |
| p_change_max | d | E | 预告净利润变动幅度上限(%) | forecast | history | history_panel,strategy |
| p_change_min | d | E | 预告净利润变动幅度下限(%) | forecast | history | history_panel,strategy |
| reason | d | E | 龙虎榜机构明细 - 上榜理由 | top_inst | history | history_panel,strategy |
| sell | d | E | 龙虎榜机构明细 - 卖出额（元） | top_inst | history | history_panel,strategy |
| sell_rate | d | E | 龙虎榜机构明细 - 卖出占总成交比例 | top_inst | history | history_panel,strategy |
| side | d | E | 龙虎榜机构明细 - 买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名 | top_inst | history | history_panel,strategy |
| stock_holder_trade_after_ratio | d | E | 股东交易 - 变动后占流通比例（%） | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_after_share | d | E | 股东交易 - 变动后持股 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_avg_price | d | E | 股东交易 - 平均价格 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_begin_date | d | E | 股东交易 - 增减持开始日期 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_change_ratio | d | E | 股东交易 - 占流通比例（%） | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_change_vol | d | E | 股东交易 - 变动数量 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_close_date | d | E | 股东交易 - 增减持结束日期 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_in_de | d | E | 股东交易 - 类型IN增持DE减持 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_name | d | E | 股东交易 - 股东名称 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_total_share | d | E | 股东交易 - 持股总数 | stock_holder_trade | history | history_panel,strategy |
| stock_holder_trade_type | d | E | 股东交易 - 股东类型G高管P个人C公司 | stock_holder_trade | history | history_panel,strategy |
| summary | d | E | 业绩预告摘要 | forecast | history | history_panel,strategy |
| suspend_timing | d | E | 日内停牌时间段 | stock_suspend | history | history_panel,strategy |
| top10_amount | d | E | 沪深港通十大成交股上榜 - 成交金额（元） | hs_top10_stock | history | history_panel,strategy |
| top10_buy | d | E | 沪深港通十大成交股上榜 - 买入金额（元） | hs_top10_stock | history | history_panel,strategy |
| top10_change | d | E | 沪深港通十大成交股上榜 - 涨跌额 | hs_top10_stock | history | history_panel,strategy |
| top10_close | d | E | 沪深港通十大成交股上榜 - 收盘价 | hs_top10_stock | history | history_panel,strategy |
| top10_net_amount | d | E | 沪深港通十大成交股上榜 - 净成交金额（元） | hs_top10_stock | history | history_panel,strategy |
| top10_rank | d | E | 沪深港通十大成交股上榜 - 资金排名 | hs_top10_stock | history | history_panel,strategy |
| top10_sell | d | E | 沪深港通十大成交股上榜 - 卖出金额（元） | hs_top10_stock | history | history_panel,strategy |
| top_list_amount | d | E | 龙虎榜交易明细 - 总成交额 | top_list | history | history_panel,strategy |
| top_list_amount_rate | d | E | 龙虎榜交易明细 - 龙虎榜成交额占比 | top_list | history | history_panel,strategy |
| top_list_close | d | E | 龙虎榜交易明细 - 收盘价 | top_list | history | history_panel,strategy |
| top_list_float_values | d | E | 龙虎榜交易明细 - 当日流通市值 | top_list | history | history_panel,strategy |
| top_list_l_amount | d | E | 龙虎榜交易明细- 龙虎榜成交额 | top_list | history | history_panel,strategy |
| top_list_l_buy | d | E | 龙虎榜交易明细 - 龙虎榜买入额 | top_list | history | history_panel,strategy |
| top_list_l_sell | d | E | 龙虎榜交易明细 - 龙虎榜卖出额 | top_list | history | history_panel,strategy |
| top_list_net_amount | d | E | 龙虎榜交易明细 - 龙虎榜净买入额 | top_list | history | history_panel,strategy |
| top_list_net_rate | d | E | 龙虎榜交易明细 - 龙虎榜净买额占比 | top_list | history | history_panel,strategy |
| top_list_pct_change | d | E | 龙虎榜交易明细 - 涨跌幅 | top_list | history | history_panel,strategy |
| top_list_reason | d | E | 龙虎榜交易明细 - 上榜理由 | top_list | history | history_panel,strategy |
| top_list_turnover_rate | d | E | 龙虎榜交易明细 - 换手率 | top_list | history | history_panel,strategy |
