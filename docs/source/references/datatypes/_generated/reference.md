<!-- AUTO-GENERATED: do not edit -->
<!-- generated_at: 2026-08-19 17:34 UTC -->
<!-- acquisition_type: reference -->
<!-- row_count: 147 -->

# 引用型（reference）

本分册由 `docs/scripts/generate_datatype_catalog.py` 从 `qteasy.datatypes.get_dtype_map()` 生成，共 **147** 条。

请勿手改；更新内置类型后请重跑生成脚本。

| name | freq | asset_type | description | table_name | kind | usable_in |
| --- | --- | --- | --- | --- | --- | --- |
| cn_gdp | q | None | GDP累计值（亿元） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_pi | q | None | 第一产业累计值（亿元） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_pi_yoy | q | None | 第一产业同比增速（%） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_si | q | None | 第二产业累计值（亿元） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_si_yoy | q | None | 第二产业同比增速（%） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_ti | q | None | 第三产业累计值（亿元） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_ti_yoy | q | None | 第三产业同比增速（%） | cn_gdp | reference | reference_api,strategy |
| cn_gdp_yoy | q | None | 当季同比增速（%） | cn_gdp | reference | reference_api,strategy |
| cn_m0 | m | None | M0（亿元） | cn_money | reference | reference_api,strategy |
| cn_m0_mom | m | None | M0环比（%） | cn_money | reference | reference_api,strategy |
| cn_m0_yoy | m | None | M0同比（%） | cn_money | reference | reference_api,strategy |
| cn_m1 | m | None | M1（亿元） | cn_money | reference | reference_api,strategy |
| cn_m1_mom | m | None | M1环比（%） | cn_money | reference | reference_api,strategy |
| cn_m1_yoy | m | None | M1同比（%） | cn_money | reference | reference_api,strategy |
| cn_m2 | m | None | M2（亿元） | cn_money | reference | reference_api,strategy |
| cn_m2_mom | m | None | M2环比（%） | cn_money | reference | reference_api,strategy |
| cn_m2_yoy | m | None | M2同比（%） | cn_money | reference | reference_api,strategy |
| cnt_accu | m | None | 农村累计值 | cn_cpi | reference | reference_api,strategy |
| cnt_mom | m | None | 农村环比（%） | cn_cpi | reference | reference_api,strategy |
| cnt_val | m | None | 农村当月值 | cn_cpi | reference | reference_api,strategy |
| cnt_yoy | m | None | 农村同比（%） | cn_cpi | reference | reference_api,strategy |
| ggt_ss | d | Any | 沪深港通资金流向 - 港股通（上海） | hs_money_flow | reference | reference_api,strategy |
| ggt_sz | d | Any | 沪深港通资金流向 - 港股通（深圳） | hs_money_flow | reference | reference_api,strategy |
| gz_d10 | d | None | 小额贷市场平均利率（十天） | gz_index | reference | reference_api,strategy |
| gz_long | d | None | 小额贷市场平均利率（长期） | gz_index | reference | reference_api,strategy |
| gz_m1 | d | None | 小额贷市场平均利率（一月期） | gz_index | reference | reference_api,strategy |
| gz_m12 | d | None | 小额贷市场平均利率（一年期） | gz_index | reference | reference_api,strategy |
| gz_m3 | d | None | 小额贷市场平均利率（三月期） | gz_index | reference | reference_api,strategy |
| gz_m6 | d | None | 小额贷市场平均利率（六月期） | gz_index | reference | reference_api,strategy |
| hgt | d | Any | 沪深港通资金流向 - 沪股通（百万元） | hs_money_flow | reference | reference_api,strategy |
| hibor\|% | d | None | 香港银行间行业拆放利率(HIBOR) - % | hibor | reference | reference_api,strategy |
| inc_cumval | m | None | 社融增量累计值（亿元） | cn_sf | reference | reference_api,strategy |
| inc_month | m | None | 社融增量当月值（亿元） | cn_sf | reference | reference_api,strategy |
| north_money | d | Any | 沪深港通资金流向 - 北向资金（百万元） | hs_money_flow | reference | reference_api,strategy |
| nt_accu | m | None | 全国累计值 | cn_cpi | reference | reference_api,strategy |
| nt_mom | m | None | 全国环比（%） | cn_cpi | reference | reference_api,strategy |
| nt_val | m | None | 全国当月值 | cn_cpi | reference | reference_api,strategy |
| nt_yoy | m | None | 全国同比（%） | cn_cpi | reference | reference_api,strategy |
| pmi010000 | m | None | 制造业PMI | cn_pmi | reference | reference_api,strategy |
| pmi010100 | m | None | 制造业PMI:企业规模/大型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010200 | m | None | 制造业PMI:企业规模/中型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010300 | m | None | 制造业PMI:企业规模/小型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010400 | m | None | 制造业PMI:构成指数/生产指数 | cn_pmi | reference | reference_api,strategy |
| pmi010401 | m | None | 制造业PMI:构成指数/生产指数:企业规模/大型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010402 | m | None | 制造业PMI:构成指数/生产指数:企业规模/中型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010403 | m | None | 制造业PMI:构成指数/生产指数:企业规模/小型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010500 | m | None | 制造业PMI:构成指数/新订单指数 | cn_pmi | reference | reference_api,strategy |
| pmi010501 | m | None | 制造业PMI:构成指数/新订单指数:企业规模/大型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010502 | m | None | 制造业PMI:构成指数/新订单指数:企业规模/中型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010503 | m | None | 制造业PMI:构成指数/新订单指数:企业规模/小型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010600 | m | None | 制造业PMI:构成指数/供应商配送时间指数 | cn_pmi | reference | reference_api,strategy |
| pmi010601 | m | None | 制造业PMI:构成指数/供应商配送时间指数:企业规模/大型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010602 | m | None | 制造业PMI:构成指数/供应商配送时间指数:企业规模/中型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010603 | m | None | 制造业PMI:构成指数/供应商配送时间指数:企业规模/小型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010700 | m | None | 制造业PMI:构成指数/原材料库存指数 | cn_pmi | reference | reference_api,strategy |
| pmi010701 | m | None | 制造业PMI:构成指数/原材料库存指数:企业规模/大型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010702 | m | None | 制造业PMI:构成指数/原材料库存指数:企业规模/中型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010703 | m | None | 制造业PMI:构成指数/原材料库存指数:企业规模/小型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010800 | m | None | 制造业PMI:构成指数/从业人员指数 | cn_pmi | reference | reference_api,strategy |
| pmi010801 | m | None | 制造业PMI:构成指数/从业人员指数:企业规模/大型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010802 | m | None | 制造业PMI:构成指数/从业人员指数:企业规模/中型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010803 | m | None | 制造业PMI:构成指数/从业人员指数:企业规模/小型企业 | cn_pmi | reference | reference_api,strategy |
| pmi010900 | m | None | 制造业PMI:其他/新出口订单 | cn_pmi | reference | reference_api,strategy |
| pmi011000 | m | None | 制造业PMI:其他/进口 | cn_pmi | reference | reference_api,strategy |
| pmi011100 | m | None | 制造业PMI:其他/采购量 | cn_pmi | reference | reference_api,strategy |
| pmi011200 | m | None | 制造业PMI:其他/主要原材料购进价格 | cn_pmi | reference | reference_api,strategy |
| pmi011300 | m | None | 制造业PMI:其他/出厂价格 | cn_pmi | reference | reference_api,strategy |
| pmi011400 | m | None | 制造业PMI:其他/产成品库存 | cn_pmi | reference | reference_api,strategy |
| pmi011500 | m | None | 制造业PMI:其他/在手订单 | cn_pmi | reference | reference_api,strategy |
| pmi011600 | m | None | 制造业PMI:其他/生产经营活动预期 | cn_pmi | reference | reference_api,strategy |
| pmi011700 | m | None | 制造业PMI:分行业/装备制造业 | cn_pmi | reference | reference_api,strategy |
| pmi011800 | m | None | 制造业PMI:分行业/高技术制造业 | cn_pmi | reference | reference_api,strategy |
| pmi011900 | m | None | 制造业PMI:分行业/基础原材料制造业 | cn_pmi | reference | reference_api,strategy |
| pmi012000 | m | None | 制造业PMI:分行业/消费品制造业 | cn_pmi | reference | reference_api,strategy |
| pmi020100 | m | None | 非制造业PMI:商务活动 | cn_pmi | reference | reference_api,strategy |
| pmi020101 | m | None | 非制造业PMI:商务活动:分行业/建筑业 | cn_pmi | reference | reference_api,strategy |
| pmi020102 | m | None | 非制造业PMI:商务活动:分行业/服务业业 | cn_pmi | reference | reference_api,strategy |
| pmi020200 | m | None | 非制造业PMI:新订单指数 | cn_pmi | reference | reference_api,strategy |
| pmi020201 | m | None | 非制造业PMI:新订单指数:分行业/建筑业 | cn_pmi | reference | reference_api,strategy |
| pmi020202 | m | None | 非制造业PMI:新订单指数:分行业/服务业 | cn_pmi | reference | reference_api,strategy |
| pmi020300 | m | None | 非制造业PMI:投入品价格指数 | cn_pmi | reference | reference_api,strategy |
| pmi020301 | m | None | 非制造业PMI:投入品价格指数:分行业/建筑业 | cn_pmi | reference | reference_api,strategy |
| pmi020302 | m | None | 非制造业PMI:投入品价格指数:分行业/服务业 | cn_pmi | reference | reference_api,strategy |
| pmi020400 | m | None | 非制造业PMI:销售价格指数 | cn_pmi | reference | reference_api,strategy |
| pmi020401 | m | None | 非制造业PMI:销售价格指数:分行业/建筑业 | cn_pmi | reference | reference_api,strategy |
| pmi020402 | m | None | 非制造业PMI:销售价格指数:分行业/服务业 | cn_pmi | reference | reference_api,strategy |
| pmi020500 | m | None | 非制造业PMI:从业人员指数 | cn_pmi | reference | reference_api,strategy |
| pmi020501 | m | None | 非制造业PMI:从业人员指数:分行业/建筑业 | cn_pmi | reference | reference_api,strategy |
| pmi020502 | m | None | 非制造业PMI:从业人员指数:分行业/服务业 | cn_pmi | reference | reference_api,strategy |
| pmi020600 | m | None | 非制造业PMI:业务活动预期指数 | cn_pmi | reference | reference_api,strategy |
| pmi020601 | m | None | 非制造业PMI:业务活动预期指数:分行业/建筑业 | cn_pmi | reference | reference_api,strategy |
| pmi020602 | m | None | 非制造业PMI:业务活动预期指数:分行业/服务业 | cn_pmi | reference | reference_api,strategy |
| pmi020700 | m | None | 非制造业PMI:新出口订单 | cn_pmi | reference | reference_api,strategy |
| pmi020800 | m | None | 非制造业PMI:在手订单 | cn_pmi | reference | reference_api,strategy |
| pmi020900 | m | None | 非制造业PMI:存货 | cn_pmi | reference | reference_api,strategy |
| pmi021000 | m | None | 非制造业PMI:供应商配送时间 | cn_pmi | reference | reference_api,strategy |
| pmi030000 | m | None | 中国综合PMI:产出指数 | cn_pmi | reference | reference_api,strategy |
| ppi_accu | m | None | PPI：全部工业品：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_accu | m | None | PPI：生活资料：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_adu_accu | m | None | PPI：生活资料：一般日用品类：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_adu_mom | m | None | PPI：生活资料：一般日用品类：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_adu_yoy | m | None | PPI：生活资料：一般日用品类：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_c_accu | m | None | PPI：生活资料：衣着类：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_c_mom | m | None | PPI：生活资料：衣着类：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_c_yoy | m | None | PPI：生活资料：衣着类：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_dcg_accu | m | None | PPI：生活资料：耐用消费品类：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_dcg_mom | m | None | PPI：生活资料：耐用消费品类：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_dcg_yoy | m | None | PPI：生活资料：耐用消费品类：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_f_accu | m | None | PPI：生活资料：食品类：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_f_mom | m | None | PPI：生活资料：食品类：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_f_yoy | m | None | PPI：生活资料：食品类：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_mom | m | None | PPI：生活资料：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_cg_yoy | m | None | PPI：生活资料：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mom | m | None | PPI：全部工业品：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_accu | m | None | PPI：生产资料：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_mom | m | None | PPI：生产资料：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_p_accu | m | None | PPI：生产资料：加工业：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_p_mom | m | None | PPI：生产资料：加工业：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_p_yoy | m | None | PPI：生产资料：加工业：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_qm_accu | m | None | PPI：生产资料：采掘业：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_qm_mom | m | None | PPI：生产资料：采掘业：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_qm_yoy | m | None | PPI：生产资料：采掘业：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_rm_accu | m | None | PPI：生产资料：原料业：累计同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_rm_mom | m | None | PPI：生产资料：原料业：环比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_rm_yoy | m | None | PPI：生产资料：原料业：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_mp_yoy | m | None | PPI：生产资料：当月同比 | cn_ppi | reference | reference_api,strategy |
| ppi_yoy | m | None | PPI：全部工业品：当月同比 | cn_ppi | reference | reference_api,strategy |
| sgt | d | Any | 沪深港通资金流向 - 深股通（百万元） | hs_money_flow | reference | reference_api,strategy |
| shibor\|% | d | None | 上海银行间行业拆放利率(SHIBOR) - % | shibor | reference | reference_api,strategy |
| south_money | d | Any | 沪深港通资金流向 - 南向资金（百万元） | hs_money_flow | reference | reference_api,strategy |
| stk_endval | m | None | 社融存量期末值（万亿元） | cn_sf | reference | reference_api,strategy |
| town_accu | m | None | 城市累计值 | cn_cpi | reference | reference_api,strategy |
| town_mom | m | None | 城市环比（%） | cn_cpi | reference | reference_api,strategy |
| town_val | m | None | 城市当月值 | cn_cpi | reference | reference_api,strategy |
| town_yoy | m | None | 城市同比（%） | cn_cpi | reference | reference_api,strategy |
| wz_aa | d | None | 农村互助会互助金费率 | wz_index | reference | reference_api,strategy |
| wz_center | d | None | 民间借贷服务中心利率 | wz_index | reference | reference_api,strategy |
| wz_cm | d | None | 民间资本管理公司融资价格 | wz_index | reference | reference_api,strategy |
| wz_comp | d | None | 温州民间融资综合利率指数 | wz_index | reference | reference_api,strategy |
| wz_long | d | None | 温州地区民间借贷分期限利率（长期） | wz_index | reference | reference_api,strategy |
| wz_m1 | d | None | 温州地区民间借贷分期限利率（一月期） | wz_index | reference | reference_api,strategy |
| wz_m12 | d | None | 温州地区民间借贷分期限利率（一年期） | wz_index | reference | reference_api,strategy |
| wz_m3 | d | None | 温州地区民间借贷分期限利率（三月期） | wz_index | reference | reference_api,strategy |
| wz_m6 | d | None | 温州地区民间借贷分期限利率（六月期） | wz_index | reference | reference_api,strategy |
| wz_micro | d | None | 小额贷款公司放款利率 | wz_index | reference | reference_api,strategy |
| wz_om | d | None | 其他市场主体利率 | wz_index | reference | reference_api,strategy |
| wz_sdb | d | None | 社会直接借贷利率 | wz_index | reference | reference_api,strategy |
