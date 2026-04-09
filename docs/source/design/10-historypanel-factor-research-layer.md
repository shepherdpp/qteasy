# HistoryPanel 与可选「FactorResearch」辅助层（评估结论）

本文档回答路线图中的评估项：**是否需要在 `HistoryPanel` 之上再抽象一层轻量 API（工作名 `FactorResearch`），专门计算 IC/IR、分位数组合收益、long-short 曲线等？**

## 1. 当前能力边界（已满足的部分）

以下能力已由 `HistoryPanel` 及相关 API 覆盖，无需重复造轮子：

- **因子列生产**：`assign`、`__setitem__`、`returns`、`kline`、`apply_ta` 等；
- **截面变换**：`rank`、`zscore(method='cs'|'ts')`；
- **粗组合与基准**：`portfolio`（等权/加权、`groups`、`benchmark`）；
- **研究向收益展示**：`cum_return`、`normalize` 与 `mask=`；
- **可视化**：`plot` 与 `(M,L)` mask 高亮；
- **与计量工具衔接**：`to_df_dict`、手工长表化后接 pandas / statsmodels（见教程 2.5 §11）。

对「轻量因子研究 + 粗验」目标，上述已构成**完整底座**。

## 2. 若增加 `FactorResearch` 层，能解决什么？

典型封装可包括：

- 给定 **因子列** 与 **收益列**（或标签），输出 **逐期 IC**、**IC 均值/IR**；
- **分位数组合**（按截面分桶）的净值或收益序列；
- **多空组合**（top minus bottom）的时间序列。

这些均可用现有 `rank` / `portfolio` / `values` + pandas **在用户侧或独立模块中**几十行实现；封装的价值在于 **API 稳定、参数约定统一、减少复制粘贴错误**。

## 3. 结论（短期不引入类库级 `FactorResearch`）

**结论：当前阶段不在 qteasy 内核或 HistoryPanel 上强制增加 `FactorResearch` 类/子模块。**

理由简述：

1. **职责清晰**：`HistoryPanel` 已定位为三维研究容器与显式对齐/重采样；IC/IR、分位组合等属于**研究工作流约定**更强的「分析配方」，放在独立教程、示例或未来可选包中更合适，避免 HP API 膨胀。
2. **避免错误预期**：单独命名模块易让用户以为框架已内置「发表级因子检验」（如多重检验、样本划分、HAC 标准误），而实际仍需用户在 statsmodels 等侧完成推断。
3. **与中期「内置因子库」的关系**：顶层路线图中的 **内置因子库（M2.1）** 若落地，更自然的做法是 **因子定义 + 注册 + 与 FactorSorter/回测衔接**；批量 IC/分层可作为因子库周边的 **可选工具函数**，而非 HistoryPanel 实例方法。
4. **维护成本**：IC 需约定收益前瞻窗口、停牌、退市、权重（市值加权 vs 等权）等，参数组合多，若无统一数据契约易引发支持成本。

## 4. 若未来引入，建议形态（备忘）

若社区需求明确，推荐 **独立模块**（例如 `qteasy.research.factor_stats` 或项目外 `qteasy-research`），而非 `HistoryPanel` 方法：

- 入参：`HistoryPanel` 或 `DataFrame` + 列名 + 前瞻期数；
- 出参：`DataFrame` / `Series`（可再绘图为辅）；
- 文档：明确 **非** 替代 Backtester，且 **不** 内置 Fama–MacBeth / Newey–West（仍导出到 statsmodels）。

届时应配套 **TDD** 与英文 `ValueError` 契约，与现有 HP 测试风格一致。

## 5. 与教程的关系

实操路径以 [教程 2.5：使用 HistoryPanel 操作和分析历史数据](../tutorials/2.5-historypanel-data-analysis.md) 的 §9–§11 为准；本设计文档仅记录 **架构层面的评估结论**，不增加用户必读的 API 面。
