# qteasy AI Shell A0 实施顺序与 L1/L2 验收口径

本文用于冻结 S1.4A 阶段的实施顺序与验收边界，避免执行过程中口径漂移。

## 1. 实施顺序（A0 → A → B → C → D）

1. **A0（局部重构）**
   - 冻结四条 ADR；
   - 完成 Hybrid Planner v2 三段式；
   - 接入 ConfigCenter；
   - 接入 SkillRuntime v2；
   - 接入 PlanSchema v2 最小 DAG。
2. **A（只读 MVP 外壳）**
   - 只读 skills 与基础图表导出；
   - plan/dry-run 与 execute 闭环稳定。
3. **B（高副作用基础能力）**
   - 下载、回测、优化最小闭环；
   - 强化确认门控与可追溯。
4. **C（Provider/记忆/UI 完善）**
   - 多 Provider 绑定；
   - profile/env_facts/runs 体验增强。
5. **D（StrategyBuilder 一条龙）**
   - NL→Spec→代码→回测/优化→实盘 plan only。

## 2. L1 验收口径（A0/A 必须满足）

- 能稳定展示并追踪“三段式规划链路”：候选计划→校验修订→最终计划；
- 高副作用步骤遵循“先 plan 后确认”；
- 执行链路支持最小 DAG 字段：`depends_on` / `run_if` / `on_fail`；
- 失败可定位（统一 error code/message/details）；
- 全链路可复盘（run 记录 + artifacts）。

## 3. L2 验收口径（后续阶段目标）

- 支持复杂多步 DAG 与条件分支研究编排；
- 支持跨技能数据流与失败恢复策略组合；
- 支持 StrategyBuilder 端到端工作流；
- 保持“实盘默认 plan-only + 显式确认”的硬边界。

## 4. A0 完成判定（退出条件）

- 单元测试覆盖以下能力：
  - ConfigCenter 优先级；
  - Hybrid Planner `planner_trace`；
  - SkillRuntime precheck 与 side-effects 门控；
  - PlanExecutor 最小 DAG 与 retry 策略；
- 核心模块（contracts/planner/executor/registry/provider）接口在本阶段冻结，不做破坏性改动；
- 文档中已明确回滚策略与监控指标。

