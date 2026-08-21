<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-20 10:10 UTC -->
<!-- business_group: quotes -->
<!-- row_count: 358 -->

# 行情与复权

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 按**业务类别**生成，共 **358** 条。

请勿手改；更新内置类型后请重跑生成脚本。列含义与推荐读法见 [清单入口](../index.md)。`acquisition_type` / `table_name` 仅供对照 refill。

| name | freq | asset_type | description | kind | usable_in | acquisition_type | table_name |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accum_div | d | FD | 基金净值 - 累计分红 | history | history_panel,strategy | direct | fund_nav |
| accum_nav | d | FD | 基金净值 - 累计净值 | history | history_panel,strategy | direct | fund_nav |
| adj_nav | d | FD | 基金净值 - 复权净值 | history | history_panel,strategy | direct | fund_nav |
| amount | 15min | E | 股票15分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_15min |
| amount | 15min | FD | 基金15分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_15min |
| amount | 15min | FT | 期货15分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_15min |
| amount | 15min | IDX | 指数15分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_15min |
| amount | 15min | OPT | 期权15分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | options_15min |
| amount | 1min | E | 股票60秒K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_1min |
| amount | 1min | FD | 基金60秒K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_1min |
| amount | 1min | FT | 期货60秒K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_1min |
| amount | 1min | IDX | 指数60秒K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_1min |
| amount | 1min | OPT | 期权60秒K线 - 成交额 （千元） | history | history_panel,strategy | direct | options_1min |
| amount | 30min | E | 股票30分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_30min |
| amount | 30min | FD | 基金30分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_30min |
| amount | 30min | FT | 期货30分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_30min |
| amount | 30min | IDX | 指数30分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_30min |
| amount | 30min | OPT | 期权30分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | options_30min |
| amount | 5min | E | 股票5分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_5min |
| amount | 5min | FD | 基金5分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_5min |
| amount | 5min | FT | 期货5分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_5min |
| amount | 5min | IDX | 指数5分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_5min |
| amount | 5min | OPT | 期权5分钟K线 - 成交额 （千元） | history | history_panel,strategy | direct | options_5min |
| amount | d | E | 股票日K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_daily |
| amount | d | FD | 基金日K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_daily |
| amount | d | FT | 期货日K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_daily |
| amount | d | IDX | 指数日K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_daily |
| amount | d | OPT | 期权日K线 - 成交额 （千元） | history | history_panel,strategy | direct | options_daily |
| amount | h | E | 股票小时K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_hourly |
| amount | h | FD | 基金小时K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_hourly |
| amount | h | FT | 期货小时K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_hourly |
| amount | h | IDX | 指数小时K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_hourly |
| amount | h | OPT | 期权小时K线 - 成交额 （千元） | history | history_panel,strategy | direct | options_hourly |
| amount | m | E | 股票月K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_monthly |
| amount | m | FD | 基金月K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_monthly |
| amount | m | FT | 期货月K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_monthly |
| amount | m | IDX | 指数月K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_monthly |
| amount | w | E | 股票周K线 - 成交额 （千元） | history | history_panel,strategy | direct | stock_weekly |
| amount | w | FD | 基金周K线 - 成交额 （千元） | history | history_panel,strategy | direct | fund_weekly |
| amount | w | FT | 期货周K线 - 成交额 （千元） | history | history_panel,strategy | direct | future_weekly |
| amount | w | IDX | 指数周K线 - 成交额 （千元） | history | history_panel,strategy | direct | index_weekly |
| ci_amount | d | IDX | 中信指数日K线 - 成交额 （万元） | history | history_panel,strategy | direct | ci_index_daily |
| ci_change | d | IDX | 中信指数日K线 - 涨跌额 | history | history_panel,strategy | direct | ci_index_daily |
| ci_close | d | IDX | 中信指数日K线 - 收盘价 | history | history_panel,strategy | direct | ci_index_daily |
| ci_high | d | IDX | 中信指数日K线 - 最高价 | history | history_panel,strategy | direct | ci_index_daily |
| ci_low | d | IDX | 中信指数日K线 - 最低价 | history | history_panel,strategy | direct | ci_index_daily |
| ci_open | d | IDX | 中信指数日K线 - 开盘价 | history | history_panel,strategy | direct | ci_index_daily |
| ci_pct_change | d | IDX | 中信指数日K线 - 涨跌幅 | history | history_panel,strategy | direct | ci_index_daily |
| ci_pre_close | d | IDX | 中信指数日K线 - 昨日收盘点位 | history | history_panel,strategy | direct | ci_index_daily |
| ci_vol | d | IDX | 中信指数日K线 - 成交量 （万股） | history | history_panel,strategy | direct | ci_index_daily |
| close | 15min | E | 股票15分钟K线 - 收盘价 | history | history_panel,strategy | direct | stock_15min |
| close | 15min | FD | 基金15分钟K线 - 收盘价 | history | history_panel,strategy | direct | fund_15min |
| close | 15min | FT | 期货15分钟K线 - 收盘价 | history | history_panel,strategy | direct | future_15min |
| close | 15min | IDX | 指数15分钟K线 - 收盘价 | history | history_panel,strategy | direct | index_15min |
| close | 15min | OPT | 期权15分钟K线 - 收盘价 | history | history_panel,strategy | direct | options_15min |
| close | 1min | E | 股票60秒K线 - 收盘价 | history | history_panel,strategy | direct | stock_1min |
| close | 1min | FD | 基金60秒K线 - 收盘价 | history | history_panel,strategy | direct | fund_1min |
| close | 1min | FT | 期货60秒K线 - 收盘价 | history | history_panel,strategy | direct | future_1min |
| close | 1min | IDX | 指数60秒K线 - 收盘价 | history | history_panel,strategy | direct | index_1min |
| close | 1min | OPT | 期权60秒K线 - 收盘价 | history | history_panel,strategy | direct | options_1min |
| close | 30min | E | 股票30分钟K线 - 收盘价 | history | history_panel,strategy | direct | stock_30min |
| close | 30min | FD | 基金30分钟K线 - 收盘价 | history | history_panel,strategy | direct | fund_30min |
| close | 30min | FT | 期货30分钟K线 - 收盘价 | history | history_panel,strategy | direct | future_30min |
| close | 30min | IDX | 指数30分钟K线 - 收盘价 | history | history_panel,strategy | direct | index_30min |
| close | 30min | OPT | 期权30分钟K线 - 收盘价 | history | history_panel,strategy | direct | options_30min |
| close | 5min | E | 股票5分钟K线 - 收盘价 | history | history_panel,strategy | direct | stock_5min |
| close | 5min | FD | 基金5分钟K线 - 收盘价 | history | history_panel,strategy | direct | fund_5min |
| close | 5min | FT | 期货5分钟K线 - 收盘价 | history | history_panel,strategy | direct | future_5min |
| close | 5min | IDX | 指数5分钟K线 - 收盘价 | history | history_panel,strategy | direct | index_5min |
| close | 5min | OPT | 期权5分钟K线 - 收盘价 | history | history_panel,strategy | direct | options_5min |
| close | d | E | 股票日K线 - 收盘价 | history | history_panel,strategy | direct | stock_daily |
| close | d | FD | 基金日K线 - 收盘价 | history | history_panel,strategy | direct | fund_daily |
| close | d | FT | 期货日K线 - 收盘价 | history | history_panel,strategy | direct | future_daily |
| close | d | IDX | 指数日K线 - 收盘价 | history | history_panel,strategy | direct | index_daily |
| close | d | OPT | 期权日K线 - 收盘价 | history | history_panel,strategy | direct | options_daily |
| close | h | E | 股票小时K线 - 收盘价 | history | history_panel,strategy | direct | stock_hourly |
| close | h | FD | 基金小时K线 - 收盘价 | history | history_panel,strategy | direct | fund_hourly |
| close | h | FT | 期货小时K线 - 收盘价 | history | history_panel,strategy | direct | future_hourly |
| close | h | IDX | 指数小时K线 - 收盘价 | history | history_panel,strategy | direct | index_hourly |
| close | h | OPT | 期权小时K线 - 收盘价 | history | history_panel,strategy | direct | options_hourly |
| close | m | E | 股票月K线 - 收盘价 | history | history_panel,strategy | direct | stock_monthly |
| close | m | FD | 基金月K线 - 收盘价 | history | history_panel,strategy | direct | fund_monthly |
| close | m | FT | 期货月K线 - 收盘价 | history | history_panel,strategy | direct | future_monthly |
| close | m | IDX | 指数月K线 - 收盘价 | history | history_panel,strategy | direct | index_monthly |
| close | w | E | 股票周K线 - 收盘价 | history | history_panel,strategy | direct | stock_weekly |
| close | w | FD | 基金周K线 - 收盘价 | history | history_panel,strategy | direct | fund_weekly |
| close | w | FT | 期货周K线 - 收盘价 | history | history_panel,strategy | direct | future_weekly |
| close | w | IDX | 指数周K线 - 收盘价 | history | history_panel,strategy | direct | index_weekly |
| close\|% | 15min | E | 股票15分钟K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_15min |
| close\|% | 15min | FD | 基金15分钟K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_15min |
| close\|% | 1min | E | 股票60秒K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_1min |
| close\|% | 1min | FD | 基金60秒K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_1min |
| close\|% | 30min | E | 股票30分钟K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_30min |
| close\|% | 30min | FD | 基金30分钟K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_30min |
| close\|% | 5min | E | 股票5分钟K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_5min |
| close\|% | 5min | FD | 基金5分钟K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_5min |
| close\|% | d | E | 股票日K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_daily |
| close\|% | d | FD | 基金日K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_daily |
| close\|% | h | E | 股票小时K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_hourly |
| close\|% | h | FD | 基金小时K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_hourly |
| close\|% | m | E | 股票月K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_monthly |
| close\|% | m | FD | 基金月K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_monthly |
| close\|% | w | E | 股票周K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_weekly |
| close\|% | w | FD | 基金周K线 - 复权收盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_weekly |
| close_chg | d | FT | 期货日K线 - 收盘价涨跌 | history | history_panel,strategy | direct | future_daily |
| close_chg | m | FT | 期货月K线 - 收盘价涨跌 | history | history_panel,strategy | direct | future_monthly |
| close_chg | w | FT | 期货周K线 - 收盘价涨跌 | history | history_panel,strategy | direct | future_weekly |
| delf_settle | d | FT | 期货日K线 - 交割结算价 | history | history_panel,strategy | direct | future_daily |
| delf_settle | m | FT | 期货月K线 - 交割结算价 | history | history_panel,strategy | direct | future_monthly |
| delf_settle | w | FT | 期货周K线 - 交割结算价 | history | history_panel,strategy | direct | future_weekly |
| g_index_amount | d | IDX | 全球指数日K线行情 - 成交额 | history | history_panel,strategy | direct | global_index_daily |
| g_index_change | d | IDX | 全球指数日K线行情 - 最低价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_close | d | IDX | 全球指数日K线行情 - 收盘价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_high | d | IDX | 全球指数日K线行情 - 最高价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_low | d | IDX | 全球指数日K线行情 - 最低价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_open | d | IDX | 全球指数日K线行情 - 开盘价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_pct_change | d | IDX | 全球指数日K线行情 - 收盘价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_pre_close | d | IDX | 全球指数日K线行情 - 昨日收盘价 | history | history_panel,strategy | direct | global_index_daily |
| g_index_swing | d | IDX | 全球指数日K线行情 - 振幅 | history | history_panel,strategy | direct | global_index_daily |
| g_index_vol | d | IDX | 全球指数日K线行情 - 成交量 | history | history_panel,strategy | direct | global_index_daily |
| high | 15min | E | 股票15分钟K线 - 最高价 | history | history_panel,strategy | direct | stock_15min |
| high | 15min | FD | 基金15分钟K线 - 最高价 | history | history_panel,strategy | direct | fund_15min |
| high | 15min | FT | 期货15分钟K线 - 最高价 | history | history_panel,strategy | direct | future_15min |
| high | 15min | IDX | 指数15分钟K线 - 最高价 | history | history_panel,strategy | direct | index_15min |
| high | 15min | OPT | 期权15分钟K线 - 最高价 | history | history_panel,strategy | direct | options_15min |
| high | 1min | E | 股票60秒K线 - 最高价 | history | history_panel,strategy | direct | stock_1min |
| high | 1min | FD | 基金60秒K线 - 最高价 | history | history_panel,strategy | direct | fund_1min |
| high | 1min | FT | 期货60秒K线 - 最高价 | history | history_panel,strategy | direct | future_1min |
| high | 1min | IDX | 指数60秒K线 - 最高价 | history | history_panel,strategy | direct | index_1min |
| high | 1min | OPT | 期权60秒K线 - 最高价 | history | history_panel,strategy | direct | options_1min |
| high | 30min | E | 股票30分钟K线 - 最高价 | history | history_panel,strategy | direct | stock_30min |
| high | 30min | FD | 基金30分钟K线 - 最高价 | history | history_panel,strategy | direct | fund_30min |
| high | 30min | FT | 期货30分钟K线 - 最高价 | history | history_panel,strategy | direct | future_30min |
| high | 30min | IDX | 指数30分钟K线 - 最高价 | history | history_panel,strategy | direct | index_30min |
| high | 30min | OPT | 期权30分钟K线 - 最高价 | history | history_panel,strategy | direct | options_30min |
| high | 5min | E | 股票5分钟K线 - 最高价 | history | history_panel,strategy | direct | stock_5min |
| high | 5min | FD | 基金5分钟K线 - 最高价 | history | history_panel,strategy | direct | fund_5min |
| high | 5min | FT | 期货5分钟K线 - 最高价 | history | history_panel,strategy | direct | future_5min |
| high | 5min | IDX | 指数5分钟K线 - 最高价 | history | history_panel,strategy | direct | index_5min |
| high | 5min | OPT | 期权5分钟K线 - 最高价 | history | history_panel,strategy | direct | options_5min |
| high | d | E | 股票日K线 - 最高价 | history | history_panel,strategy | direct | stock_daily |
| high | d | FD | 基金日K线 - 最高价 | history | history_panel,strategy | direct | fund_daily |
| high | d | FT | 期货日K线 - 最高价 | history | history_panel,strategy | direct | future_daily |
| high | d | IDX | 指数日K线 - 最高价 | history | history_panel,strategy | direct | index_daily |
| high | d | OPT | 期权日K线 - 最高价 | history | history_panel,strategy | direct | options_daily |
| high | h | E | 股票小时K线 - 最高价 | history | history_panel,strategy | direct | stock_hourly |
| high | h | FD | 基金小时K线 - 最高价 | history | history_panel,strategy | direct | fund_hourly |
| high | h | FT | 期货小时K线 - 最高价 | history | history_panel,strategy | direct | future_hourly |
| high | h | IDX | 指数小时K线 - 最高价 | history | history_panel,strategy | direct | index_hourly |
| high | h | OPT | 期权小时K线 - 最高价 | history | history_panel,strategy | direct | options_hourly |
| high | m | E | 股票月K线 - 最高价 | history | history_panel,strategy | direct | stock_monthly |
| high | m | FD | 基金月K线 - 最高价 | history | history_panel,strategy | direct | fund_monthly |
| high | m | FT | 期货月K线 - 最高价 | history | history_panel,strategy | direct | future_monthly |
| high | m | IDX | 指数月K线 - 最高价 | history | history_panel,strategy | direct | index_monthly |
| high | w | E | 股票周K线 - 最高价 | history | history_panel,strategy | direct | stock_weekly |
| high | w | FD | 基金周K线 - 最高价 | history | history_panel,strategy | direct | fund_weekly |
| high | w | FT | 期货周K线 - 最高价 | history | history_panel,strategy | direct | future_weekly |
| high | w | IDX | 指数周K线 - 最高价 | history | history_panel,strategy | direct | index_weekly |
| high\|% | 15min | E | 股票15分钟K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_15min |
| high\|% | 15min | FD | 基金15分钟K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_15min |
| high\|% | 1min | E | 股票60秒K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_1min |
| high\|% | 1min | FD | 基金60秒K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_1min |
| high\|% | 30min | E | 股票30分钟K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_30min |
| high\|% | 30min | FD | 基金30分钟K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_30min |
| high\|% | 5min | E | 股票5分钟K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_5min |
| high\|% | 5min | FD | 基金5分钟K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_5min |
| high\|% | d | E | 股票日K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_daily |
| high\|% | d | FD | 基金日K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_daily |
| high\|% | h | E | 股票小时K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_hourly |
| high\|% | h | FD | 基金小时K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_hourly |
| high\|% | m | E | 股票月K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_monthly |
| high\|% | m | FD | 基金月K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_monthly |
| high\|% | w | E | 股票周K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_weekly |
| high\|% | w | FD | 基金周K线 - 复权最高价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_weekly |
| low | 15min | E | 股票15分钟K线 - 最低价 | history | history_panel,strategy | direct | stock_15min |
| low | 15min | FD | 基金15分钟K线 - 最低价 | history | history_panel,strategy | direct | fund_15min |
| low | 15min | FT | 期货15分钟K线 - 最低价 | history | history_panel,strategy | direct | future_15min |
| low | 15min | IDX | 指数15分钟K线 - 最低价 | history | history_panel,strategy | direct | index_15min |
| low | 15min | OPT | 期权15分钟K线 - 最低价 | history | history_panel,strategy | direct | options_15min |
| low | 1min | E | 股票60秒K线 - 最低价 | history | history_panel,strategy | direct | stock_1min |
| low | 1min | FD | 基金60秒K线 - 最低价 | history | history_panel,strategy | direct | fund_1min |
| low | 1min | FT | 期货60秒K线 - 最低价 | history | history_panel,strategy | direct | future_1min |
| low | 1min | IDX | 指数60秒K线 - 最低价 | history | history_panel,strategy | direct | index_1min |
| low | 1min | OPT | 期权60秒K线 - 最低价 | history | history_panel,strategy | direct | options_1min |
| low | 30min | E | 股票30分钟K线 - 最低价 | history | history_panel,strategy | direct | stock_30min |
| low | 30min | FD | 基金30分钟K线 - 最低价 | history | history_panel,strategy | direct | fund_30min |
| low | 30min | FT | 期货30分钟K线 - 最低价 | history | history_panel,strategy | direct | future_30min |
| low | 30min | IDX | 指数30分钟K线 - 最低价 | history | history_panel,strategy | direct | index_30min |
| low | 30min | OPT | 期权30分钟K线 - 最低价 | history | history_panel,strategy | direct | options_30min |
| low | 5min | E | 股票5分钟K线 - 最低价 | history | history_panel,strategy | direct | stock_5min |
| low | 5min | FD | 基金5分钟K线 - 最低价 | history | history_panel,strategy | direct | fund_5min |
| low | 5min | FT | 期货5分钟K线 - 最低价 | history | history_panel,strategy | direct | future_5min |
| low | 5min | IDX | 指数5分钟K线 - 最低价 | history | history_panel,strategy | direct | index_5min |
| low | 5min | OPT | 期权5分钟K线 - 最低价 | history | history_panel,strategy | direct | options_5min |
| low | d | E | 股票日K线 - 最低价 | history | history_panel,strategy | direct | stock_daily |
| low | d | FD | 基金日K线 - 最低价 | history | history_panel,strategy | direct | fund_daily |
| low | d | FT | 期货日K线 - 最低价 | history | history_panel,strategy | direct | future_daily |
| low | d | IDX | 指数日K线 - 最低价 | history | history_panel,strategy | direct | index_daily |
| low | d | OPT | 期权日K线 - 最低价 | history | history_panel,strategy | direct | options_daily |
| low | h | E | 股票小时K线 - 最低价 | history | history_panel,strategy | direct | stock_hourly |
| low | h | FD | 基金小时K线 - 最低价 | history | history_panel,strategy | direct | fund_hourly |
| low | h | FT | 期货小时K线 - 最低价 | history | history_panel,strategy | direct | future_hourly |
| low | h | IDX | 指数小时K线 - 最低价 | history | history_panel,strategy | direct | index_hourly |
| low | h | OPT | 期权小时K线 - 最低价 | history | history_panel,strategy | direct | options_hourly |
| low | m | E | 股票月K线 - 最低价 | history | history_panel,strategy | direct | stock_monthly |
| low | m | FD | 基金月K线 - 最低价 | history | history_panel,strategy | direct | fund_monthly |
| low | m | FT | 期货月K线 - 最低价 | history | history_panel,strategy | direct | future_monthly |
| low | m | IDX | 指数月K线 - 最低价 | history | history_panel,strategy | direct | index_monthly |
| low | w | E | 股票周K线 - 最低价 | history | history_panel,strategy | direct | stock_weekly |
| low | w | FD | 基金周K线 - 最低价 | history | history_panel,strategy | direct | fund_weekly |
| low | w | FT | 期货周K线 - 最低价 | history | history_panel,strategy | direct | future_weekly |
| low | w | IDX | 指数周K线 - 最低价 | history | history_panel,strategy | direct | index_weekly |
| low\|% | 15min | E | 股票15分钟K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_15min |
| low\|% | 15min | FD | 基金15分钟K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_15min |
| low\|% | 1min | E | 股票60秒K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_1min |
| low\|% | 1min | FD | 基金60秒K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_1min |
| low\|% | 30min | E | 股票30分钟K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_30min |
| low\|% | 30min | FD | 基金30分钟K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_30min |
| low\|% | 5min | E | 股票5分钟K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_5min |
| low\|% | 5min | FD | 基金5分钟K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_5min |
| low\|% | d | E | 股票日K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_daily |
| low\|% | d | FD | 基金日K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_daily |
| low\|% | h | E | 股票小时K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_hourly |
| low\|% | h | FD | 基金小时K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_hourly |
| low\|% | m | E | 股票月K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_monthly |
| low\|% | m | FD | 基金月K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_monthly |
| low\|% | w | E | 股票周K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_weekly |
| low\|% | w | FD | 基金周K线 - 复权最低价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_weekly |
| net_asset | d | FD | 基金净值 - 资产净值 | history | history_panel,strategy | direct | fund_nav |
| oi | d | FT | 期货日K线 - 持仓量（手） | history | history_panel,strategy | direct | future_daily |
| oi | m | FT | 期货月K线 - 持仓量（手） | history | history_panel,strategy | direct | future_monthly |
| oi | w | FT | 期货周K线 - 持仓量（手） | history | history_panel,strategy | direct | future_weekly |
| oi_chg | d | FT | 期货日K线 - 持仓量变化 | history | history_panel,strategy | direct | future_daily |
| oi_chg | m | FT | 期货月K线 - 持仓量变化 | history | history_panel,strategy | direct | future_monthly |
| oi_chg | w | FT | 期货周K线 - 持仓量变化 | history | history_panel,strategy | direct | future_weekly |
| open | 15min | E | 股票15分钟K线 - 开盘价 | history | history_panel,strategy | direct | stock_15min |
| open | 15min | FD | 基金15分钟K线 - 开盘价 | history | history_panel,strategy | direct | fund_15min |
| open | 15min | FT | 期货15分钟K线 - 开盘价 | history | history_panel,strategy | direct | future_15min |
| open | 15min | IDX | 指数15分钟K线 - 开盘价 | history | history_panel,strategy | direct | index_15min |
| open | 15min | OPT | 期权15分钟K线 - 开盘价 | history | history_panel,strategy | direct | options_15min |
| open | 1min | E | 股票60秒K线 - 开盘价 | history | history_panel,strategy | direct | stock_1min |
| open | 1min | FD | 基金60秒K线 - 开盘价 | history | history_panel,strategy | direct | fund_1min |
| open | 1min | FT | 期货60秒K线 - 开盘价 | history | history_panel,strategy | direct | future_1min |
| open | 1min | IDX | 指数60秒K线 - 开盘价 | history | history_panel,strategy | direct | index_1min |
| open | 1min | OPT | 期权60秒K线 - 开盘价 | history | history_panel,strategy | direct | options_1min |
| open | 30min | E | 股票30分钟K线 - 开盘价 | history | history_panel,strategy | direct | stock_30min |
| open | 30min | FD | 基金30分钟K线 - 开盘价 | history | history_panel,strategy | direct | fund_30min |
| open | 30min | FT | 期货30分钟K线 - 开盘价 | history | history_panel,strategy | direct | future_30min |
| open | 30min | IDX | 指数30分钟K线 - 开盘价 | history | history_panel,strategy | direct | index_30min |
| open | 30min | OPT | 期权30分钟K线 - 开盘价 | history | history_panel,strategy | direct | options_30min |
| open | 5min | E | 股票5分钟K线 - 开盘价 | history | history_panel,strategy | direct | stock_5min |
| open | 5min | FD | 基金5分钟K线 - 开盘价 | history | history_panel,strategy | direct | fund_5min |
| open | 5min | FT | 期货5分钟K线 - 开盘价 | history | history_panel,strategy | direct | future_5min |
| open | 5min | IDX | 指数5分钟K线 - 开盘价 | history | history_panel,strategy | direct | index_5min |
| open | 5min | OPT | 期权5分钟K线 - 开盘价 | history | history_panel,strategy | direct | options_5min |
| open | d | E | 股票日K线 - 开盘价 | history | history_panel,strategy | direct | stock_daily |
| open | d | FD | 基金日K线 - 开盘价 | history | history_panel,strategy | direct | fund_daily |
| open | d | FT | 期货日K线 - 开盘价 | history | history_panel,strategy | direct | future_daily |
| open | d | IDX | 指数日K线 - 开盘价 | history | history_panel,strategy | direct | index_daily |
| open | d | OPT | 期权日K线 - 开盘价 | history | history_panel,strategy | direct | options_daily |
| open | h | E | 股票小时K线 - 开盘价 | history | history_panel,strategy | direct | stock_hourly |
| open | h | FD | 基金小时K线 - 开盘价 | history | history_panel,strategy | direct | fund_hourly |
| open | h | FT | 期货小时K线 - 开盘价 | history | history_panel,strategy | direct | future_hourly |
| open | h | IDX | 指数小时K线 - 开盘价 | history | history_panel,strategy | direct | index_hourly |
| open | h | OPT | 期权小时K线 - 开盘价 | history | history_panel,strategy | direct | options_hourly |
| open | m | E | 股票月K线 - 开盘价 | history | history_panel,strategy | direct | stock_monthly |
| open | m | FD | 基金月K线 - 开盘价 | history | history_panel,strategy | direct | fund_monthly |
| open | m | FT | 期货月K线 - 开盘价 | history | history_panel,strategy | direct | future_monthly |
| open | m | IDX | 指数月K线 - 开盘价 | history | history_panel,strategy | direct | index_monthly |
| open | w | E | 股票周K线 - 开盘价 | history | history_panel,strategy | direct | stock_weekly |
| open | w | FD | 基金周K线 - 开盘价 | history | history_panel,strategy | direct | fund_weekly |
| open | w | FT | 期货周K线 - 开盘价 | history | history_panel,strategy | direct | future_weekly |
| open | w | IDX | 指数周K线 - 开盘价 | history | history_panel,strategy | direct | index_weekly |
| open\|% | 15min | E | 股票15分钟K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_15min |
| open\|% | 15min | FD | 基金15分钟K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_15min |
| open\|% | 1min | E | 股票60秒K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_1min |
| open\|% | 1min | FD | 基金60秒K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_1min |
| open\|% | 30min | E | 股票30分钟K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_30min |
| open\|% | 30min | FD | 基金30分钟K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_30min |
| open\|% | 5min | E | 股票5分钟K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_5min |
| open\|% | 5min | FD | 基金5分钟K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_5min |
| open\|% | d | E | 股票日K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_daily |
| open\|% | d | FD | 基金日K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_daily |
| open\|% | h | E | 股票小时K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_hourly |
| open\|% | h | FD | 基金小时K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_hourly |
| open\|% | m | E | 股票月K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_monthly |
| open\|% | m | FD | 基金月K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_monthly |
| open\|% | w | E | 股票周K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | stock_weekly |
| open\|% | w | FD | 基金周K线 - 复权开盘价-b:后复权f:前复权 | history | history_panel,strategy | adjustment | fund_weekly |
| settle | d | FT | 期货日K线 - 结算价 | history | history_panel,strategy | direct | future_daily |
| settle | m | FT | 期货月K线 - 结算价 | history | history_panel,strategy | direct | future_monthly |
| settle | w | FT | 期货周K线 - 结算价 | history | history_panel,strategy | direct | future_weekly |
| settle_chg | d | FT | 期货日K线 - 结算价涨跌 | history | history_panel,strategy | direct | future_daily |
| settle_chg | m | FT | 期货月K线 - 结算价涨跌 | history | history_panel,strategy | direct | future_monthly |
| settle_chg | w | FT | 期货周K线 - 结算价涨跌 | history | history_panel,strategy | direct | future_weekly |
| sw_amount | d | IDX | 申万指数日K线 - 成交额 （万元） | history | history_panel,strategy | direct | sw_index_daily |
| sw_change | d | IDX | 申万指数日K线 - 涨跌额 | history | history_panel,strategy | direct | sw_index_daily |
| sw_close | d | IDX | 申万指数日K线 - 收盘价 | history | history_panel,strategy | direct | sw_index_daily |
| sw_float_mv | d | IDX | 申万指数日K线 - 流通市值 （万元） | history | history_panel,strategy | direct | sw_index_daily |
| sw_high | d | IDX | 申万指数日K线 - 最高价 | history | history_panel,strategy | direct | sw_index_daily |
| sw_low | d | IDX | 申万指数日K线 - 最低价 | history | history_panel,strategy | direct | sw_index_daily |
| sw_open | d | IDX | 申万指数日K线 - 开盘价 | history | history_panel,strategy | direct | sw_index_daily |
| sw_pb | d | IDX | 申万指数日K线 - 市净率 | history | history_panel,strategy | direct | sw_index_daily |
| sw_pct_change | d | IDX | 申万指数日K线 - 涨跌幅 | history | history_panel,strategy | direct | sw_index_daily |
| sw_pe | d | IDX | 申万指数日K线 - 市盈率 | history | history_panel,strategy | direct | sw_index_daily |
| sw_total_mv | d | IDX | 申万指数日K线 - 总市值 （万元） | history | history_panel,strategy | direct | sw_index_daily |
| sw_vol | d | IDX | 申万指数日K线 - 成交量 （万股） | history | history_panel,strategy | direct | sw_index_daily |
| ths_avg_price | d | IDX | 同花顺指数日K线 - 平均价 | history | history_panel,strategy | direct | ths_index_daily |
| ths_change | d | IDX | 同花顺指数日K线 - 最低价 | history | history_panel,strategy | direct | ths_index_daily |
| ths_close | d | IDX | 同花顺指数日K线 - 收盘价 | history | history_panel,strategy | direct | ths_index_daily |
| ths_float_mv | d | IDX | 同花顺指数日K线 - 流通市值 （万元） | history | history_panel,strategy | direct | ths_index_daily |
| ths_high | d | IDX | 同花顺指数日K线 - 最高价 | history | history_panel,strategy | direct | ths_index_daily |
| ths_low | d | IDX | 同花顺指数日K线 - 最低价 | history | history_panel,strategy | direct | ths_index_daily |
| ths_open | d | IDX | 同花顺指数日K线 - 开盘价 | history | history_panel,strategy | direct | ths_index_daily |
| ths_pct_change | d | IDX | 同花顺指数日K线 - 涨跌幅 | history | history_panel,strategy | direct | ths_index_daily |
| ths_total_mv | d | IDX | 同花顺指数日K线 - 总市值 （万元） | history | history_panel,strategy | direct | ths_index_daily |
| ths_turnover | d | IDX | 同花顺指数日K线 - 换手率 | history | history_panel,strategy | direct | ths_index_daily |
| ths_vol | d | IDX | 同花顺指数日K线 - 成交量 （万股） | history | history_panel,strategy | direct | ths_index_daily |
| total_netasset | d | FD | 基金净值 - 累计资产净值 | history | history_panel,strategy | direct | fund_nav |
| unit_nav | d | FD | 基金净值 - 单位净值 | history | history_panel,strategy | direct | fund_nav |
| volume | 15min | E | 股票15分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_15min |
| volume | 15min | FD | 基金15分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_15min |
| volume | 15min | FT | 期货15分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | future_15min |
| volume | 15min | IDX | 指数15分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | index_15min |
| volume | 15min | OPT | 期权15分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | options_15min |
| volume | 1min | E | 股票60秒K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_1min |
| volume | 1min | FD | 基金60秒K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_1min |
| volume | 1min | FT | 期货60秒K线 - 成交量 （手） | history | history_panel,strategy | direct | future_1min |
| volume | 1min | IDX | 指数60秒K线 - 成交量 （手） | history | history_panel,strategy | direct | index_1min |
| volume | 1min | OPT | 期权60秒K线 - 成交量 （手） | history | history_panel,strategy | direct | options_1min |
| volume | 30min | E | 股票30分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_30min |
| volume | 30min | FD | 基金30分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_30min |
| volume | 30min | FT | 期货30分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | future_30min |
| volume | 30min | IDX | 指数30分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | index_30min |
| volume | 30min | OPT | 期权30分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | options_30min |
| volume | 5min | E | 股票5分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_5min |
| volume | 5min | FD | 基金5分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_5min |
| volume | 5min | FT | 期货5分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | future_5min |
| volume | 5min | IDX | 指数5分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | index_5min |
| volume | 5min | OPT | 期权5分钟K线 - 成交量 （手） | history | history_panel,strategy | direct | options_5min |
| volume | d | E | 股票日K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_daily |
| volume | d | FD | 基金日K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_daily |
| volume | d | FT | 期货日K线 - 成交量 （手） | history | history_panel,strategy | direct | future_daily |
| volume | d | IDX | 指数日K线 - 成交量 （手） | history | history_panel,strategy | direct | index_daily |
| volume | d | OPT | 期权日K线 - 成交量 （手） | history | history_panel,strategy | direct | options_daily |
| volume | h | E | 股票小时K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_hourly |
| volume | h | FD | 基金小时K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_hourly |
| volume | h | FT | 期货小时K线 - 成交量 （手） | history | history_panel,strategy | direct | future_hourly |
| volume | h | IDX | 指数小时K线 - 成交量 （手） | history | history_panel,strategy | direct | index_hourly |
| volume | h | OPT | 期权小时K线 - 成交量 （手） | history | history_panel,strategy | direct | options_hourly |
| volume | m | E | 股票月K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_monthly |
| volume | m | FD | 基金月K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_monthly |
| volume | m | FT | 期货月K线 - 成交量（手） | history | history_panel,strategy | direct | future_monthly |
| volume | m | IDX | 指数月K线 - 成交量 （手） | history | history_panel,strategy | direct | index_monthly |
| volume | w | E | 股票周K线 - 成交量 （手） | history | history_panel,strategy | direct | stock_weekly |
| volume | w | FD | 基金周K线 - 成交量 （手） | history | history_panel,strategy | direct | fund_weekly |
| volume | w | FT | 期货周K线 - 成交量（手） | history | history_panel,strategy | direct | future_weekly |
| volume | w | IDX | 指数周K线 - 成交量 （手） | history | history_panel,strategy | direct | index_weekly |
