<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-20 10:10 UTC -->
<!-- business_group: static -->
<!-- row_count: 116 -->

# 静态证券信息

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 按**业务类别**生成，共 **116** 条。

请勿手改；更新内置类型后请重跑生成脚本。列含义与推荐读法见 [清单入口](../index.md)。`acquisition_type` / `table_name` 仅供对照 refill。

| name | freq | asset_type | description | kind | usable_in | acquisition_type | table_name |
| --- | --- | --- | --- | --- | --- | --- | --- |
| area | None | E | 股票基本信息 - 地域 | static | static_api,universe | basics | stock_basic |
| ballot | d | E | 新股上市信息 - 中签率 | static | static_api,universe | basics | new_share |
| base_date | None | IDX | 指数基本信息 - 基期 | static | static_api,universe | basics | index_basic |
| base_point | None | IDX | 指数基本信息 - 基点 | static | static_api,universe | basics | index_basic |
| benchmark | None | FD | 基金基本信息 - 业绩比较基准 | static | static_api,universe | basics | fund_basic |
| business_scope | d | E | 公司信息 - 经营范围 | static | static_api,universe | basics | stock_company |
| c_fee | None | FD | 基金基本信息 - 托管费 | static | static_api,universe | basics | fund_basic |
| call_put | None | OPT | 期权基本信息 - 期权类型 | static | static_api,universe | basics | opt_basic |
| category | None | IDX | 指数基本信息 - 指数类别 | static | static_api,universe | basics | index_basic |
| chairman | d | E | 公司信息 - 法人代表 | static | static_api,universe | basics | stock_company |
| city | d | E | 公司信息 - 所在城市 | static | static_api,universe | basics | stock_company |
| cnspell | None | E | 股票基本信息 - 拼音缩写 | static | static_api,universe | basics | stock_basic |
| curr_type | None | E | 股票基本信息 - 交易货币 | static | static_api,universe | basics | stock_basic |
| custodian | None | FD | 基金基本信息 - 托管人 | static | static_api,universe | basics | fund_basic |
| d_mode_desc | None | FT | 期货基本信息 - 交割方式说明 | static | static_api,universe | basics | future_basic |
| d_month | None | FT | 期货基本信息 - 交割月份 | static | static_api,universe | basics | future_basic |
| delist_date | None | E | 股票基本信息 - 退市日期 | static | static_api,universe | basics | stock_basic |
| delist_date | None | FD | 基金基本信息 - 退市日期 | static | static_api,universe | basics | fund_basic |
| delist_date | None | FT | 期货基本信息 - 最后交易日期 | static | static_api,universe | basics | future_basic |
| delist_date | None | OPT | 期权基本信息 - 最后交易日期 | static | static_api,universe | basics | opt_basic |
| desc | None | IDX | 指数基本信息 - 描述 | static | static_api,universe | basics | index_basic |
| due_date | None | FD | 基金基本信息 - 到期日期 | static | static_api,universe | basics | fund_basic |
| duration_year | None | FD | 基金基本信息 - 存续期 | static | static_api,universe | basics | fund_basic |
| email | d | E | 公司信息 - 电子邮件 | static | static_api,universe | basics | stock_company |
| employees | d | E | 公司信息 - 员工人数 | static | static_api,universe | basics | stock_company |
| enname | None | E | 股票基本信息 - 英文全称 | static | static_api,universe | basics | stock_basic |
| exchange | None | E | 股票基本信息 - 交易所代码 | static | static_api,universe | basics | stock_basic |
| exchange | None | FT | 期货基本信息 - 交易市场 | static | static_api,universe | basics | future_basic |
| exchange | None | OPT | 期权基本信息 - 交易市场 | static | static_api,universe | basics | opt_basic |
| exercise_price | None | OPT | 期权基本信息 - 行权价格 | static | static_api,universe | basics | opt_basic |
| exercise_type | None | OPT | 期权基本信息 - 行权方式 | static | static_api,universe | basics | opt_basic |
| exp_date | None | IDX | 指数基本信息 - 终止日期 | static | static_api,universe | basics | index_basic |
| exp_return | None | FD | 基金基本信息 - 预期收益率 | static | static_api,universe | basics | fund_basic |
| found_date | None | FD | 基金基本信息 - 成立日期 | static | static_api,universe | basics | fund_basic |
| fullname | None | E | 股票基本信息 - 股票全称 | static | static_api,universe | basics | stock_basic |
| fund_name | None | FD | 基金基本信息 - 简称 | static | static_api,universe | basics | fund_basic |
| fund_type | None | FD | 基金基本信息 - 投资类型 | static | static_api,universe | basics | fund_basic |
| funds | d | E | 新股上市信息 - 募集资金（亿元） | static | static_api,universe | basics | new_share |
| fut_code | None | FT | 期货基本信息 - 合约产品代码 | static | static_api,universe | basics | future_basic |
| index_type | None | IDX | 指数基本信息 - 指数风格 | static | static_api,universe | basics | index_basic |
| industry | None | E | 股票基本信息 - 所属行业 | static | static_api,universe | basics | stock_basic |
| initial_pe | d | E | 新股上市信息 - 发行市盈率 | static | static_api,universe | basics | new_share |
| initial_price | d | E | 新股上市信息 - 发行价格 | static | static_api,universe | basics | new_share |
| introduction | d | E | 公司信息 - 公司介绍 | static | static_api,universe | basics | stock_company |
| invest_type | None | FD | 基金基本信息 - 投资风格 | static | static_api,universe | basics | fund_basic |
| IPO_amount | d | E | 新股上市信息 - 发行总量（万股） | static | static_api,universe | basics | new_share |
| ipo_date | d | E | 新股上市信息 - 上网发行日期 | static | static_api,universe | basics | new_share |
| is_hs | None | E | 股票基本信息 - 是否沪深港通标的 | static | static_api,universe | basics | stock_basic |
| issue_amount | None | FD | 基金基本信息 - 发行份额(亿) | static | static_api,universe | basics | fund_basic |
| issue_date | None | FD | 基金基本信息 - 发行日期 | static | static_api,universe | basics | fund_basic |
| issue_date | d | E | 新股上市信息 - 上市日期 | static | static_api,universe | basics | new_share |
| last_ddate | None | FT | 期货基本信息 - 最后交割日 | static | static_api,universe | basics | future_basic |
| last_ddate | None | OPT | 期权基本信息 - 最后交割日期 | static | static_api,universe | basics | opt_basic |
| last_edate | None | OPT | 期权基本信息 - 最后行权日期 | static | static_api,universe | basics | opt_basic |
| limit_amount | d | E | 新股上市信息 - 个人申购上限（万股） | static | static_api,universe | basics | new_share |
| list_date | None | E | 股票基本信息 - 上市日期 | static | static_api,universe | basics | stock_basic |
| list_date | None | FD | 基金基本信息 - 上市时间 | static | static_api,universe | basics | fund_basic |
| list_date | None | FT | 期货基本信息 - 上市日期 | static | static_api,universe | basics | future_basic |
| list_date | None | IDX | 指数基本信息 - 发布日期 | static | static_api,universe | basics | index_basic |
| list_date | None | OPT | 期权基本信息 - 开始交易日期 | static | static_api,universe | basics | opt_basic |
| list_price | None | OPT | 期权基本信息 - 挂牌基准价 | static | static_api,universe | basics | opt_basic |
| list_status | None | E | 股票基本信息 - 上市状态 L上市 D退市 P暂停上市 | static | static_api,universe | basics | stock_basic |
| m_fee | None | FD | 基金基本信息 - 管理费 | static | static_api,universe | basics | fund_basic |
| main_business | d | E | 公司信息 - 主要业务及产品 | static | static_api,universe | basics | stock_company |
| management | None | FD | 基金基本信息 - 管理人 | static | static_api,universe | basics | fund_basic |
| manager | d | E | 公司信息 - 总经理 | static | static_api,universe | basics | stock_company |
| market | None | E | 股票基本信息 - 市场类型 | static | static_api,universe | basics | stock_basic |
| market | None | FD | 基金基本信息 - E场内O场外 | static | static_api,universe | basics | fund_basic |
| market | None | IDX | 指数基本信息 - 市场 | static | static_api,universe | basics | index_basic |
| market_amount | d | E | 新股上市信息 - 上网发行总量（万股） | static | static_api,universe | basics | new_share |
| maturity_date | None | OPT | 期权基本信息 - 到期日 | static | static_api,universe | basics | opt_basic |
| min_amount | None | FD | 基金基本信息 - 起点金额(万元) | static | static_api,universe | basics | fund_basic |
| min_price_chg | None | OPT | 期权基本信息 - 最小价格波幅 | static | static_api,universe | basics | opt_basic |
| multiplier | None | FT | 期货基本信息 - 合约乘数(只适用于国债期货、指数期货) | static | static_api,universe | basics | future_basic |
| name | None | FT | 期货基本信息 - 中文简称 | static | static_api,universe | basics | future_basic |
| name | None | OPT | 期权基本信息 - 合约名称 | static | static_api,universe | basics | opt_basic |
| office | d | E | 公司信息 - 办公室 | static | static_api,universe | basics | stock_company |
| opt_code | None | OPT | 期权基本信息 - 标的合约代码 | static | static_api,universe | basics | opt_basic |
| opt_type | None | OPT | 期权基本信息 - 合约类型 | static | static_api,universe | basics | opt_basic |
| p_value | None | FD | 基金基本信息 - 面值 | static | static_api,universe | basics | fund_basic |
| per_unit | None | FT | 期货基本信息 - 交易单位(每手) | static | static_api,universe | basics | future_basic |
| per_unit | None | OPT | 期权基本信息 - 合约单位 | static | static_api,universe | basics | opt_basic |
| province | d | E | 公司信息 - 所在省份 | static | static_api,universe | basics | stock_company |
| publisher | None | IDX | 指数基本信息 - 发布方 | static | static_api,universe | basics | index_basic |
| purc_startdate | None | FD | 基金基本信息 - 日常申购起始日 | static | static_api,universe | basics | fund_basic |
| quote_unit | None | FT | 期货基本信息 - 报价单位 | static | static_api,universe | basics | future_basic |
| quote_unit | None | OPT | 期权基本信息 - 报价单位 | static | static_api,universe | basics | opt_basic |
| quote_unit_desc | None | FT | 期货基本信息 - 最小报价单位说明 | static | static_api,universe | basics | future_basic |
| redm_startdate | None | FD | 基金基本信息 - 日常赎回起始日 | static | static_api,universe | basics | fund_basic |
| reg_capital | d | E | 公司信息 - 注册资本 | static | static_api,universe | basics | stock_company |
| s_month | None | OPT | 期权基本信息 - 结算月 | static | static_api,universe | basics | opt_basic |
| secretary | d | E | 公司信息 - 董秘 | static | static_api,universe | basics | stock_company |
| setup_date | d | E | 公司信息 - 注册日期 | static | static_api,universe | basics | stock_company |
| status | None | FD | 基金基本信息 - 存续状态D摘牌 I发行 L已上市 | static | static_api,universe | basics | fund_basic |
| stock_name | None | E | 股票基本信息 - 股票名称 | static | static_api,universe | basics | stock_basic |
| stock_symbol | None | E | 股票基本信息 - 股票代码 | static | static_api,universe | basics | stock_basic |
| sw\|% | None | IDX | 申万行业分类筛选 - % | static | static_api,universe | selection | sw_industry_basic |
| sw_industry_code | None | IDX | 申万行业分类 - 行业代码 | static | static_api,universe | basics | sw_industry_basic |
| sw_industry_name | None | IDX | 申万行业分类 - 名称 | static | static_api,universe | basics | sw_industry_basic |
| sw_level | None | IDX | 申万行业分类 - 级别 | static | static_api,universe | basics | sw_industry_basic |
| sw_level\|% | None | IDX | 申万行业分类筛选 - % | static | static_api,universe | selection | sw_industry_basic |
| sw_parent_code | None | IDX | 申万行业分类 - 上级行业代码 | static | static_api,universe | basics | sw_industry_basic |
| sw_published | None | IDX | 申万行业分类 - 是否发布 | static | static_api,universe | basics | sw_industry_basic |
| sw_source | None | IDX | 申万行业分类 - 分类版本 | static | static_api,universe | basics | sw_industry_basic |
| symbol | None | FT | 期货基本信息 - 交易标识 | static | static_api,universe | basics | future_basic |
| ths_category | None | E | 股票同花顺行业分类 | static | static_api,universe | category | ths_index_weight |
| ths_industry_count | None | IDX | 同花顺行业分类基本信息 - 股票数量 | static | static_api,universe | basics | ths_index_basic |
| ths_industry_date | None | IDX | 同花顺行业分类基本信息 - 发布日期 | static | static_api,universe | basics | ths_index_basic |
| ths_industry_exchange | None | IDX | 同花顺行业分类基本信息 - 交易所 | static | static_api,universe | basics | ths_index_basic |
| ths_industry_name | None | IDX | 同花顺行业分类基本信息 - 行业名称 | static | static_api,universe | basics | ths_index_basic |
| trade_time_desc | None | FT | 期货基本信息 - 交易时间说明 | static | static_api,universe | basics | future_basic |
| trade_unit | None | FT | 期货基本信息 - 交易计量单位 | static | static_api,universe | basics | future_basic |
| trustee | None | FD | 基金基本信息 - 受托人 | static | static_api,universe | basics | fund_basic |
| type | None | FD | 基金基本信息 - 基金类型 | static | static_api,universe | basics | fund_basic |
| website | d | E | 公司信息 - 公司主页 | static | static_api,universe | basics | stock_company |
| weight_rule | None | IDX | 指数基本信息 - 加权方式 | static | static_api,universe | basics | index_basic |
