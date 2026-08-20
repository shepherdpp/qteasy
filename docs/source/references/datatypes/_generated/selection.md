<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-19 17:34 UTC -->
<!-- acquisition_type: selection -->
<!-- row_count: 14 -->

# 筛选型（selection）

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 生成，共 **14** 条。

请勿手改；更新内置类型后请重跑生成脚本。

| name | freq | asset_type | description | table_name | kind | usable_in |
| --- | --- | --- | --- | --- | --- | --- |
| is_trade_day\|% | d | None | 是否交易日-市场代码：% | trade_calendar | reference | reference_api,strategy |
| libor_eur\|% | d | None | 伦敦银行间行业拆放利率(LIBOR) EUR - % | libor | reference | reference_api,strategy |
| libor_gbp\|% | d | None | 伦敦银行间行业拆放利率(LIBOR) GBP - % | libor | reference | reference_api,strategy |
| libor_usd\|% | d | None | 伦敦银行间行业拆放利率(LIBOR) USD - % | libor | reference | reference_api,strategy |
| pre_trade_day\|% | d | None | 上一交易日 | trade_calendar | reference | reference_api,strategy |
| rqmcl\|% | d | None | 融资融券交易汇总 - 融券卖出量(股,份,手) | margin | reference | reference_api,strategy |
| rqye\|% | d | None | 融资融券交易汇总 - 融券余额(元) | margin | reference | reference_api,strategy |
| rqyl\|% | d | None | 融资融券交易汇总 - 融券余量(股,份,手) | margin | reference | reference_api,strategy |
| rzche\|% | d | None | 融资融券交易汇总 - 融资偿还额(元) | margin | reference | reference_api,strategy |
| rzmre\|% | d | None | 融资融券交易汇总 - 融资买入额(元) | margin | reference | reference_api,strategy |
| rzrqye\|% | d | None | 融资融券交易汇总 - 融资融券余额(元) | margin | reference | reference_api,strategy |
| rzye\|% | d | None | 融资融券交易汇总 - 融资余额(元) | margin | reference | reference_api,strategy |
| sw\|% | None | IDX | 申万行业分类筛选 - % | sw_industry_basic | static | static_api,universe |
| sw_level\|% | None | IDX | 申万行业分类筛选 - % | sw_industry_basic | static | static_api,universe |
