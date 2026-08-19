# qteasy 开发入口（ROADMAP）

**进度真源**在顶层展望 **[§七、任务进度与执行索引](.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md#七任务进度与执行索引)**。本文档仅作快捷入口，不维护完整任务表。

---

## 新 Session 如何开始

1. `@.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md` — 方向、任务定义与 **§七 进度**
2. `@docs/DEV_CONTEXT.md` — 协作背景与文档层级约定
3. 说明本步任务 ID（如 `S2.1`、`M2.2`、`Q-AI.1`）→ 打开展望 **§7.2** 链到的次顶层 plan → 执行

**qteasy-ai**：代码在 [shepherdpp/qteasy-ai](https://github.com/shepherdpp/qteasy-ai)；Q-AI 计划书仍在 **本仓** `.cursor/plans/`。建议打开 `~/Projects/qteasy-ecosystem.code-workspace`（qteasy + qteasy-ai 双根）。

---

## 当前聚焦（2026-08-20）

详见展望 **§7.4 战术偏移**：

- **Jackie 主线（qteasy）**：**S1.5** DataType 消费契约（待审核后执行）；S2.1 xtQuant 协作等待期内不阻塞 S1.5
- **文档分轨**：**S4.6** DataType 用户文档与目录（与 S1.5 契约一致、分开审核执行）
- **数据体验续作**：**M2.2** HistoryPanel 二阶段 — **已收官**（2.6.3）
- **Jackie 副线（qteasy-ai）**：**Q-AI.1 ✅ 已完成**（0.1.0）；下一可选 **Q-AI.2** skills 扩展
- **协作轨（低占用）**：S2.1-XT（Spike / v0.1 Review）

更新进度时改展望 **§7.1**，勿改本文档任务表。

---

## 常用链接

| 文档 | 用途 |
| --- | --- |
| [量化工具对比与 qteasy 展望](.cursor/plans/量化工具对比与qteasy展望_f384dd4a.plan.md) | 顶层战略计划（master-plan） |
| [M2.2 HP 二阶段扩展](.cursor/plans/m2.2_hp二阶段扩展_da0c19a3.plan.md) | HistoryPanel 内核补齐 + `qteasy.research`（已完成） |
| [S1.5 DataType 消费契约](.cursor/plans/s1.5_datatype消费契约与三入口_a8f21c09.plan.md) | History/Reference/Static 三入口（planned，待审核） |
| [S4.6 DataType 用户文档](.cursor/plans/s4.6_datatype用户文档与目录_c4e7b2d1.plan.md) | 概念章与业务目录（planned，契约跟 S1.5） |
| [S1.1 HistoryPanel 数据体验扩展](.cursor/plans/historypanel-数据体验扩展_4e4a5f97.plan.md) | S1.1 次顶层（已完成） |
| [qteasy-ai（GitHub）](https://github.com/shepherdpp/qteasy-ai) | AI 外壳独立代码仓 |
| [S1.4 剥离 qteasy-ai 计划](.cursor/plans/s1.4_剥离_qteasy-ai_10ba0551.plan.md) | Q-AI Session 0～4 拆工与交付记录 |
| [S1.4A 人工测试金标准](.cursor/plans/s1.4a人工测试金标准_6d66df64.plan.md) | Q-AI.1 三模式 smoke（Jackie） |
| [S3.3 数据通道配置与文档](.cursor/plans/s3.3_数据通道配置与文档_c7d4e8f1.plan.md) | 四通道用户文档（已收官） |
| [qteasy-xtquant 协作](.cursor/plans/qteasy-xtquant-collaboration/) | S2.1 逐步执行 |
| [docs/source/roadmap.rst](docs/source/roadmap.rst) | 面向用户的功能路线图 |

*最后更新：2026-08-20 — 立项 S1.5 / S4.6；M2.2 已收官；Q-AI.1 已完成。*
