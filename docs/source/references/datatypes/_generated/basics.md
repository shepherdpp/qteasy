<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-17 16:38 UTC -->
<!-- acquisition_type: basics -->
<!-- row_count: 113 -->

# 基本信息（basics）

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 生成，共 **113** 条。

请勿手改；更新内置类型后请重跑生成脚本。

| name | freq | asset_type | description | table_name |
| --- | --- | --- | --- | --- |
| area | None | E | 股票基本信息 - 地域 | stock_basic |
| ballot | d | E | 新股上市信息 - 中签率 | new_share |
| base_date | None | IDX | 指数基本信息 - 基期 | index_basic |
| base_point | None | IDX | 指数基本信息 - 基点 | index_basic |
| benchmark | None | FD | 基金基本信息 - 业绩比较基准 | fund_basic |
| business_scope | d | E | 公司信息 - 经营范围 | stock_company |
| c_fee | None | FD | 基金基本信息 - 托管费 | fund_basic |
| call_put | None | OPT | 期权基本信息 - 期权类型 | opt_basic |
| category | None | IDX | 指数基本信息 - 指数类别 | index_basic |
| chairman | d | E | 公司信息 - 法人代表 | stock_company |
| city | d | E | 公司信息 - 所在城市 | stock_company |
| cnspell | None | E | 股票基本信息 - 拼音缩写 | stock_basic |
| curr_type | None | E | 股票基本信息 - 交易货币 | stock_basic |
| custodian | None | FD | 基金基本信息 - 托管人 | fund_basic |
| d_mode_desc | None | FT | 期货基本信息 - 交割方式说明 | future_basic |
| d_month | None | FT | 期货基本信息 - 交割月份 | future_basic |
| delist_date | None | E | 股票基本信息 - 退市日期 | stock_basic |
| delist_date | None | FD | 基金基本信息 - 退市日期 | fund_basic |
| delist_date | None | FT | 期货基本信息 - 最后交易日期 | future_basic |
| delist_date | None | OPT | 期权基本信息 - 最后交易日期 | opt_basic |
| desc | None | IDX | 指数基本信息 - 描述 | index_basic |
| due_date | None | FD | 基金基本信息 - 到期日期 | fund_basic |
| duration_year | None | FD | 基金基本信息 - 存续期 | fund_basic |
| email | d | E | 公司信息 - 电子邮件 | stock_company |
| employees | d | E | 公司信息 - 员工人数 | stock_company |
| enname | None | E | 股票基本信息 - 英文全称 | stock_basic |
| exchange | None | E | 股票基本信息 - 交易所代码 | stock_basic |
| exchange | None | FT | 期货基本信息 - 交易市场 | future_basic |
| exchange | None | OPT | 期权基本信息 - 交易市场 | opt_basic |
| exercise_price | None | OPT | 期权基本信息 - 行权价格 | opt_basic |
| exercise_type | None | OPT | 期权基本信息 - 行权方式 | opt_basic |
| exp_date | None | IDX | 指数基本信息 - 终止日期 | index_basic |
| exp_return | None | FD | 基金基本信息 - 预期收益率 | fund_basic |
| found_date | None | FD | 基金基本信息 - 成立日期 | fund_basic |
| fullname | None | E | 股票基本信息 - 股票全称 | stock_basic |
| fund_name | None | FD | 基金基本信息 - 简称 | fund_basic |
| fund_type | None | FD | 基金基本信息 - 投资类型 | fund_basic |
| funds | d | E | 新股上市信息 - 募集资金（亿元） | new_share |
| fut_code | None | FT | 期货基本信息 - 合约产品代码 | future_basic |
| index_type | None | IDX | 指数基本信息 - 指数风格 | index_basic |
| industry | None | E | 股票基本信息 - 所属行业 | stock_basic |
| initial_pe | d | E | 新股上市信息 - 发行市盈率 | new_share |
| initial_price | d | E | 新股上市信息 - 发行价格 | new_share |
| introduction | d | E | 公司信息 - 公司介绍 | stock_company |
| invest_type | None | FD | 基金基本信息 - 投资风格 | fund_basic |
| IPO_amount | d | E | 新股上市信息 - 发行总量（万股） | new_share |
| ipo_date | d | E | 新股上市信息 - 上网发行日期 | new_share |
| is_hs | None | E | 股票基本信息 - 是否沪深港通标的 | stock_basic |
| issue_amount | None | FD | 基金基本信息 - 发行份额(亿) | fund_basic |
| issue_date | None | FD | 基金基本信息 - 发行日期 | fund_basic |
| issue_date | d | E | 新股上市信息 - 上市日期 | new_share |
| last_ddate | None | FT | 期货基本信息 - 最后交割日 | future_basic |
| last_ddate | None | OPT | 期权基本信息 - 最后交割日期 | opt_basic |
| last_edate | None | OPT | 期权基本信息 - 最后行权日期 | opt_basic |
| limit_amount | d | E | 新股上市信息 - 个人申购上限（万股） | new_share |
| list_date | None | E | 股票基本信息 - 上市日期 | stock_basic |
| list_date | None | FD | 基金基本信息 - 上市时间 | fund_basic |
| list_date | None | FT | 期货基本信息 - 上市日期 | future_basic |
| list_date | None | IDX | 指数基本信息 - 发布日期 | index_basic |
| list_date | None | OPT | 期权基本信息 - 开始交易日期 | opt_basic |
| list_price | None | OPT | 期权基本信息 - 挂牌基准价 | opt_basic |
| list_status | None | E | 股票基本信息 - 上市状态 L上市 D退市 P暂停上市 | stock_basic |
| m_fee | None | FD | 基金基本信息 - 管理费 | fund_basic |
| main_business | d | E | 公司信息 - 主要业务及产品 | stock_company |
| management | None | FD | 基金基本信息 - 管理人 | fund_basic |
| manager | d | E | 公司信息 - 总经理 | stock_company |
| market | None | E | 股票基本信息 - 市场类型 | stock_basic |
| market | None | FD | 基金基本信息 - E场内O场外 | fund_basic |
| market | None | IDX | 指数基本信息 - 市场 | index_basic |
| market_amount | d | E | 新股上市信息 - 上网发行总量（万股） | new_share |
| maturity_date | None | OPT | 期权基本信息 - 到期日 | opt_basic |
| min_amount | None | FD | 基金基本信息 - 起点金额(万元) | fund_basic |
| min_price_chg | None | OPT | 期权基本信息 - 最小价格波幅 | opt_basic |
| multiplier | None | FT | 期货基本信息 - 合约乘数(只适用于国债期货、指数期货) | future_basic |
| name | None | FT | 期货基本信息 - 中文简称 | future_basic |
| name | None | OPT | 期权基本信息 - 合约名称 | opt_basic |
| office | d | E | 公司信息 - 办公室 | stock_company |
| opt_code | None | OPT | 期权基本信息 - 标的合约代码 | opt_basic |
| opt_type | None | OPT | 期权基本信息 - 合约类型 | opt_basic |
| p_value | None | FD | 基金基本信息 - 面值 | fund_basic |
| per_unit | None | FT | 期货基本信息 - 交易单位(每手) | future_basic |
| per_unit | None | OPT | 期权基本信息 - 合约单位 | opt_basic |
| province | d | E | 公司信息 - 所在省份 | stock_company |
| publisher | None | IDX | 指数基本信息 - 发布方 | index_basic |
| purc_startdate | None | FD | 基金基本信息 - 日常申购起始日 | fund_basic |
| quote_unit | None | FT | 期货基本信息 - 报价单位 | future_basic |
| quote_unit | None | OPT | 期权基本信息 - 报价单位 | opt_basic |
| quote_unit_desc | None | FT | 期货基本信息 - 最小报价单位说明 | future_basic |
| redm_startdate | None | FD | 基金基本信息 - 日常赎回起始日 | fund_basic |
| reg_capital | d | E | 公司信息 - 注册资本 | stock_company |
| s_month | None | OPT | 期权基本信息 - 结算月 | opt_basic |
| secretary | d | E | 公司信息 - 董秘 | stock_company |
| setup_date | d | E | 公司信息 - 注册日期 | stock_company |
| status | None | FD | 基金基本信息 - 存续状态D摘牌 I发行 L已上市 | fund_basic |
| stock_name | None | E | 股票基本信息 - 股票名称 | stock_basic |
| stock_symbol | None | E | 股票基本信息 - 股票代码 | stock_basic |
| sw_industry_code | None | IDX | 申万行业分类 - 行业代码 | sw_industry_basic |
| sw_industry_name | None | IDX | 申万行业分类 - 名称 | sw_industry_basic |
| sw_level | None | IDX | 申万行业分类 - 级别 | sw_industry_basic |
| sw_parent_code | None | IDX | 申万行业分类 - 上级行业代码 | sw_industry_basic |
| sw_published | None | IDX | 申万行业分类 - 是否发布 | sw_industry_basic |
| sw_source | None | IDX | 申万行业分类 - 分类版本 | sw_industry_basic |
| symbol | None | FT | 期货基本信息 - 交易标识 | future_basic |
| ths_industry_count | None | IDX | 同花顺行业分类基本信息 - 股票数量 | ths_index_basic |
| ths_industry_date | None | IDX | 同花顺行业分类基本信息 - 发布日期 | ths_index_basic |
| ths_industry_exchange | None | IDX | 同花顺行业分类基本信息 - 交易所 | ths_index_basic |
| ths_industry_name | None | IDX | 同花顺行业分类基本信息 - 行业名称 | ths_index_basic |
| trade_time_desc | None | FT | 期货基本信息 - 交易时间说明 | future_basic |
| trade_unit | None | FT | 期货基本信息 - 交易计量单位 | future_basic |
| trustee | None | FD | 基金基本信息 - 受托人 | fund_basic |
| type | None | FD | 基金基本信息 - 基金类型 | fund_basic |
| website | d | E | 公司信息 - 公司主页 | stock_company |
| weight_rule | None | IDX | 指数基本信息 - 加权方式 | index_basic |
