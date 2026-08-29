# qteasy 开发入口（ROADMAP）

**进度真源**在顶层展望 **[§七、任务进度与执行索引](.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md#七任务进度与执行索引)**。本文档仅作快捷入口，不维护完整任务表。

---

## 新 Session 如何开始

1. `@.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md` — 方向、任务定义与 **§七 进度**
2. `@docs/DEV_CONTEXT.md` — 协作背景与文档层级约定
3. 说明本步任务 ID（如 `S2.1`、`M2.2`、`Q-AI.2`）→ 打开展望 **§7.2** 链到的次顶层 plan → 执行

**qteasy-ai**：代码在 [shepherdpp/qteasy-ai](https://github.com/shepherdpp/qteasy-ai)；Q-AI 计划书仍在 **本仓** `.cursor/plans/`。建议打开 `~/Projects/qteasy-ecosystem.code-workspace`（qteasy + qteasy-ai 双根）。产品顶层金标准：[qteasy_ai_top_level_design](.cursor/plans/qteasy_ai_top_level_design.plan.md)。

---

## 当前聚焦（2026-08-29）

详见展望 **§7.4 战术偏移**：

- **Jackie 主线（qteasy）**：**S1.5 / S4.6** 已发版 **2.6.4**；S2.1 xtQuant 协作等待期内可推进文档余量或 **M2.1** 规划
- **数据体验**：**M2.2** HistoryPanel 二阶段 — **已收官**（2.6.3）
- **Jackie 副线（qteasy-ai）**：**Q-AI.3 开发已收口**；**Q-AI.4 D.0 已拍板**；下一编码 **D.1**；**Q-AI.5 / 阶段 E** 已立项、非当前编码（建议 1.0 闸门）
- **协作轨（低占用）**：S2.1-XT（Spike / v0.1 Review）

更新进度时改展望 **§7.1**，勿改本文档任务表。

---

## 常用链接

| 文档 | 用途 |
| --- | --- |
| [量化工具对比与 qteasy 展望](.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md) | 顶层战略计划（master-plan） |
| [qteasy-ai 产品顶层金标准](.cursor/plans/qteasy_ai_top_level_design.plan.md) | Q-AI 愿景/架构/运行模式冻结 |
| [M2.2 HP 二阶段扩展](knowledge/runlog/plans-closure-historypanel-m22-2026-08.md) | HistoryPanel 内核补齐 + `qteasy.research`（已完成；plan 已收口） |
| [S1.5 DataType 消费契约](knowledge/runlog/s15-s46-datatype-consumption-delivery.md) | History/Reference/Static 三入口（**已完成**） |
| [S4.6 DataType 用户文档](knowledge/domain/datatype-catalog-docs.md) | 概念章与业务目录（**已完成**） |
| [S1.1 HistoryPanel 数据体验扩展](knowledge/runlog/plans-closure-historypanel-m22-2026-08.md) | S1.1 次顶层（已完成；plan 已收口） |
| [qteasy-ai（GitHub）](https://github.com/shepherdpp/qteasy-ai) | AI 外壳独立代码仓 |
| [qteasy_ai execution plan](.cursor/plans/qteasy_ai_execution_plan_1c8aecc7.plan.md) | Q-AI 阶段拆工 |
| [S1.4 剥离 qteasy-ai 计划](.cursor/plans/s1.4_剥离_qteasy-ai_10ba0551.plan.md) | Q-AI Session 0～4 拆工与交付记录 |
| [S1.4A 人工测试金标准](.cursor/plans/s1.4a人工测试金标准_6d66df64.plan.md) | Q-AI.1 三模式 smoke（Jackie） |
| [S3.3 数据通道配置与文档](knowledge/runlog/plans-closure-data-channels-s32-s33-2026-08.md) | 四通道用户文档（已收官；plan 已收口） |
| [qteasy-xtquant 协作](.cursor/plans/qteasy-xtquant-collaboration/) | S2.1 逐步执行 |
| [docs/source/roadmap.rst](docs/source/roadmap.rst) | 面向用户的功能路线图 |

*最后更新：2026-08-29 — Q-AI.3 收口；Q-AI.4 D.0 已拍板。*
