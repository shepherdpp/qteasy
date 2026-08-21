<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-20 10:10 UTC -->
<!-- business_group: macro -->
<!-- row_count: 157 -->

# 宏观、利率与资金

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 按**业务类别**生成，共 **157** 条。

请勿手改；更新内置类型后请重跑生成脚本。列含义与推荐读法见 [清单入口](../index.md)。`acquisition_type` / `table_name` 仅供对照 refill。

| name | freq | asset_type | description | kind | usable_in | acquisition_type | table_name |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cn_gdp | q | None | GDP累计值（亿元） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_pi | q | None | 第一产业累计值（亿元） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_pi_yoy | q | None | 第一产业同比增速（%） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_si | q | None | 第二产业累计值（亿元） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_si_yoy | q | None | 第二产业同比增速（%） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_ti | q | None | 第三产业累计值（亿元） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_ti_yoy | q | None | 第三产业同比增速（%） | reference | reference_api,strategy | reference | cn_gdp |
| cn_gdp_yoy | q | None | 当季同比增速（%） | reference | reference_api,strategy | reference | cn_gdp |
| cn_m0 | m | None | M0（亿元） | reference | reference_api,strategy | reference | cn_money |
| cn_m0_mom | m | None | M0环比（%） | reference | reference_api,strategy | reference | cn_money |
| cn_m0_yoy | m | None | M0同比（%） | reference | reference_api,strategy | reference | cn_money |
| cn_m1 | m | None | M1（亿元） | reference | reference_api,strategy | reference | cn_money |
| cn_m1_mom | m | None | M1环比（%） | reference | reference_api,strategy | reference | cn_money |
| cn_m1_yoy | m | None | M1同比（%） | reference | reference_api,strategy | reference | cn_money |
| cn_m2 | m | None | M2（亿元） | reference | reference_api,strategy | reference | cn_money |
| cn_m2_mom | m | None | M2环比（%） | reference | reference_api,strategy | reference | cn_money |
| cn_m2_yoy | m | None | M2同比（%） | reference | reference_api,strategy | reference | cn_money |
| cnt_accu | m | None | 农村累计值 | reference | reference_api,strategy | reference | cn_cpi |
| cnt_mom | m | None | 农村环比（%） | reference | reference_api,strategy | reference | cn_cpi |
| cnt_val | m | None | 农村当月值 | reference | reference_api,strategy | reference | cn_cpi |
| cnt_yoy | m | None | 农村同比（%） | reference | reference_api,strategy | reference | cn_cpi |
| ggt_ss | d | Any | 沪深港通资金流向 - 港股通（上海） | reference | reference_api,strategy | reference | hs_money_flow |
| ggt_sz | d | Any | 沪深港通资金流向 - 港股通（深圳） | reference | reference_api,strategy | reference | hs_money_flow |
| gz_d10 | d | None | 小额贷市场平均利率（十天） | reference | reference_api,strategy | reference | gz_index |
| gz_long | d | None | 小额贷市场平均利率（长期） | reference | reference_api,strategy | reference | gz_index |
| gz_m1 | d | None | 小额贷市场平均利率（一月期） | reference | reference_api,strategy | reference | gz_index |
| gz_m12 | d | None | 小额贷市场平均利率（一年期） | reference | reference_api,strategy | reference | gz_index |
| gz_m3 | d | None | 小额贷市场平均利率（三月期） | reference | reference_api,strategy | reference | gz_index |
| gz_m6 | d | None | 小额贷市场平均利率（六月期） | reference | reference_api,strategy | reference | gz_index |
| hgt | d | Any | 沪深港通资金流向 - 沪股通（百万元） | reference | reference_api,strategy | reference | hs_money_flow |
| hibor\|% | d | None | 香港银行间行业拆放利率(HIBOR) - % | reference | reference_api,strategy | reference | hibor |
| inc_cumval | m | None | 社融增量累计值（亿元） | reference | reference_api,strategy | reference | cn_sf |
| inc_month | m | None | 社融增量当月值（亿元） | reference | reference_api,strategy | reference | cn_sf |
| libor_eur\|% | d | None | 伦敦银行间行业拆放利率(LIBOR) EUR - % | reference | reference_api,strategy | selection | libor |
| libor_gbp\|% | d | None | 伦敦银行间行业拆放利率(LIBOR) GBP - % | reference | reference_api,strategy | selection | libor |
| libor_usd\|% | d | None | 伦敦银行间行业拆放利率(LIBOR) USD - % | reference | reference_api,strategy | selection | libor |
| north_money | d | Any | 沪深港通资金流向 - 北向资金（百万元） | reference | reference_api,strategy | reference | hs_money_flow |
| nt_accu | m | None | 全国累计值 | reference | reference_api,strategy | reference | cn_cpi |
| nt_mom | m | None | 全国环比（%） | reference | reference_api,strategy | reference | cn_cpi |
| nt_val | m | None | 全国当月值 | reference | reference_api,strategy | reference | cn_cpi |
| nt_yoy | m | None | 全国同比（%） | reference | reference_api,strategy | reference | cn_cpi |
| pmi010000 | m | None | 制造业PMI | reference | reference_api,strategy | reference | cn_pmi |
| pmi010100 | m | None | 制造业PMI:企业规模/大型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010200 | m | None | 制造业PMI:企业规模/中型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010300 | m | None | 制造业PMI:企业规模/小型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010400 | m | None | 制造业PMI:构成指数/生产指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010401 | m | None | 制造业PMI:构成指数/生产指数:企业规模/大型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010402 | m | None | 制造业PMI:构成指数/生产指数:企业规模/中型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010403 | m | None | 制造业PMI:构成指数/生产指数:企业规模/小型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010500 | m | None | 制造业PMI:构成指数/新订单指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010501 | m | None | 制造业PMI:构成指数/新订单指数:企业规模/大型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010502 | m | None | 制造业PMI:构成指数/新订单指数:企业规模/中型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010503 | m | None | 制造业PMI:构成指数/新订单指数:企业规模/小型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010600 | m | None | 制造业PMI:构成指数/供应商配送时间指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010601 | m | None | 制造业PMI:构成指数/供应商配送时间指数:企业规模/大型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010602 | m | None | 制造业PMI:构成指数/供应商配送时间指数:企业规模/中型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010603 | m | None | 制造业PMI:构成指数/供应商配送时间指数:企业规模/小型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010700 | m | None | 制造业PMI:构成指数/原材料库存指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010701 | m | None | 制造业PMI:构成指数/原材料库存指数:企业规模/大型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010702 | m | None | 制造业PMI:构成指数/原材料库存指数:企业规模/中型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010703 | m | None | 制造业PMI:构成指数/原材料库存指数:企业规模/小型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010800 | m | None | 制造业PMI:构成指数/从业人员指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010801 | m | None | 制造业PMI:构成指数/从业人员指数:企业规模/大型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010802 | m | None | 制造业PMI:构成指数/从业人员指数:企业规模/中型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010803 | m | None | 制造业PMI:构成指数/从业人员指数:企业规模/小型企业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi010900 | m | None | 制造业PMI:其他/新出口订单 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011000 | m | None | 制造业PMI:其他/进口 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011100 | m | None | 制造业PMI:其他/采购量 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011200 | m | None | 制造业PMI:其他/主要原材料购进价格 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011300 | m | None | 制造业PMI:其他/出厂价格 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011400 | m | None | 制造业PMI:其他/产成品库存 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011500 | m | None | 制造业PMI:其他/在手订单 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011600 | m | None | 制造业PMI:其他/生产经营活动预期 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011700 | m | None | 制造业PMI:分行业/装备制造业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011800 | m | None | 制造业PMI:分行业/高技术制造业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi011900 | m | None | 制造业PMI:分行业/基础原材料制造业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi012000 | m | None | 制造业PMI:分行业/消费品制造业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020100 | m | None | 非制造业PMI:商务活动 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020101 | m | None | 非制造业PMI:商务活动:分行业/建筑业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020102 | m | None | 非制造业PMI:商务活动:分行业/服务业业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020200 | m | None | 非制造业PMI:新订单指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020201 | m | None | 非制造业PMI:新订单指数:分行业/建筑业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020202 | m | None | 非制造业PMI:新订单指数:分行业/服务业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020300 | m | None | 非制造业PMI:投入品价格指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020301 | m | None | 非制造业PMI:投入品价格指数:分行业/建筑业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020302 | m | None | 非制造业PMI:投入品价格指数:分行业/服务业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020400 | m | None | 非制造业PMI:销售价格指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020401 | m | None | 非制造业PMI:销售价格指数:分行业/建筑业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020402 | m | None | 非制造业PMI:销售价格指数:分行业/服务业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020500 | m | None | 非制造业PMI:从业人员指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020501 | m | None | 非制造业PMI:从业人员指数:分行业/建筑业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020502 | m | None | 非制造业PMI:从业人员指数:分行业/服务业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020600 | m | None | 非制造业PMI:业务活动预期指数 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020601 | m | None | 非制造业PMI:业务活动预期指数:分行业/建筑业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020602 | m | None | 非制造业PMI:业务活动预期指数:分行业/服务业 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020700 | m | None | 非制造业PMI:新出口订单 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020800 | m | None | 非制造业PMI:在手订单 | reference | reference_api,strategy | reference | cn_pmi |
| pmi020900 | m | None | 非制造业PMI:存货 | reference | reference_api,strategy | reference | cn_pmi |
| pmi021000 | m | None | 非制造业PMI:供应商配送时间 | reference | reference_api,strategy | reference | cn_pmi |
| pmi030000 | m | None | 中国综合PMI:产出指数 | reference | reference_api,strategy | reference | cn_pmi |
| ppi_accu | m | None | PPI：全部工业品：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_accu | m | None | PPI：生活资料：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_adu_accu | m | None | PPI：生活资料：一般日用品类：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_adu_mom | m | None | PPI：生活资料：一般日用品类：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_adu_yoy | m | None | PPI：生活资料：一般日用品类：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_c_accu | m | None | PPI：生活资料：衣着类：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_c_mom | m | None | PPI：生活资料：衣着类：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_c_yoy | m | None | PPI：生活资料：衣着类：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_dcg_accu | m | None | PPI：生活资料：耐用消费品类：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_dcg_mom | m | None | PPI：生活资料：耐用消费品类：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_dcg_yoy | m | None | PPI：生活资料：耐用消费品类：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_f_accu | m | None | PPI：生活资料：食品类：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_f_mom | m | None | PPI：生活资料：食品类：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_f_yoy | m | None | PPI：生活资料：食品类：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_mom | m | None | PPI：生活资料：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_cg_yoy | m | None | PPI：生活资料：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mom | m | None | PPI：全部工业品：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_accu | m | None | PPI：生产资料：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_mom | m | None | PPI：生产资料：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_p_accu | m | None | PPI：生产资料：加工业：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_p_mom | m | None | PPI：生产资料：加工业：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_p_yoy | m | None | PPI：生产资料：加工业：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_qm_accu | m | None | PPI：生产资料：采掘业：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_qm_mom | m | None | PPI：生产资料：采掘业：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_qm_yoy | m | None | PPI：生产资料：采掘业：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_rm_accu | m | None | PPI：生产资料：原料业：累计同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_rm_mom | m | None | PPI：生产资料：原料业：环比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_rm_yoy | m | None | PPI：生产资料：原料业：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_mp_yoy | m | None | PPI：生产资料：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| ppi_yoy | m | None | PPI：全部工业品：当月同比 | reference | reference_api,strategy | reference | cn_ppi |
| rqmcl\|% | d | None | 融资融券交易汇总 - 融券卖出量(股,份,手) | reference | reference_api,strategy | selection | margin |
| rqye\|% | d | None | 融资融券交易汇总 - 融券余额(元) | reference | reference_api,strategy | selection | margin |
| rqyl\|% | d | None | 融资融券交易汇总 - 融券余量(股,份,手) | reference | reference_api,strategy | selection | margin |
| rzche\|% | d | None | 融资融券交易汇总 - 融资偿还额(元) | reference | reference_api,strategy | selection | margin |
| rzmre\|% | d | None | 融资融券交易汇总 - 融资买入额(元) | reference | reference_api,strategy | selection | margin |
| rzrqye\|% | d | None | 融资融券交易汇总 - 融资融券余额(元) | reference | reference_api,strategy | selection | margin |
| rzye\|% | d | None | 融资融券交易汇总 - 融资余额(元) | reference | reference_api,strategy | selection | margin |
| sgt | d | Any | 沪深港通资金流向 - 深股通（百万元） | reference | reference_api,strategy | reference | hs_money_flow |
| shibor\|% | d | None | 上海银行间行业拆放利率(SHIBOR) - % | reference | reference_api,strategy | reference | shibor |
| south_money | d | Any | 沪深港通资金流向 - 南向资金（百万元） | reference | reference_api,strategy | reference | hs_money_flow |
| stk_endval | m | None | 社融存量期末值（万亿元） | reference | reference_api,strategy | reference | cn_sf |
| town_accu | m | None | 城市累计值 | reference | reference_api,strategy | reference | cn_cpi |
| town_mom | m | None | 城市环比（%） | reference | reference_api,strategy | reference | cn_cpi |
| town_val | m | None | 城市当月值 | reference | reference_api,strategy | reference | cn_cpi |
| town_yoy | m | None | 城市同比（%） | reference | reference_api,strategy | reference | cn_cpi |
| wz_aa | d | None | 农村互助会互助金费率 | reference | reference_api,strategy | reference | wz_index |
| wz_center | d | None | 民间借贷服务中心利率 | reference | reference_api,strategy | reference | wz_index |
| wz_cm | d | None | 民间资本管理公司融资价格 | reference | reference_api,strategy | reference | wz_index |
| wz_comp | d | None | 温州民间融资综合利率指数 | reference | reference_api,strategy | reference | wz_index |
| wz_long | d | None | 温州地区民间借贷分期限利率（长期） | reference | reference_api,strategy | reference | wz_index |
| wz_m1 | d | None | 温州地区民间借贷分期限利率（一月期） | reference | reference_api,strategy | reference | wz_index |
| wz_m12 | d | None | 温州地区民间借贷分期限利率（一年期） | reference | reference_api,strategy | reference | wz_index |
| wz_m3 | d | None | 温州地区民间借贷分期限利率（三月期） | reference | reference_api,strategy | reference | wz_index |
| wz_m6 | d | None | 温州地区民间借贷分期限利率（六月期） | reference | reference_api,strategy | reference | wz_index |
| wz_micro | d | None | 小额贷款公司放款利率 | reference | reference_api,strategy | reference | wz_index |
| wz_om | d | None | 其他市场主体利率 | reference | reference_api,strategy | reference | wz_index |
| wz_sdb | d | None | 社会直接借贷利率 | reference | reference_api,strategy | reference | wz_index |
