# S1.4 阶段A：AI 外壳增强版设计

本文档描述 qteasy AI 外壳在 S1.4 阶段A（增强版）的实现边界与使用方式。

## 1. 阶段目标

- 提供统一交互链路：自然语言 -> ToolPlan -> 用户确认 -> 执行 -> 结构化结果
- 落地基础骨架：`SkillRegistry`、`Planner`、`PlanExecutor`
- 提供 3 个只读技能：策略知识、K 线摘要、K 线导出
- 同步支持 Notebook 与 CLI 两个入口
- 落地最小记忆：`profile` / `env_facts` / `runs`
- 支持至少一个真实 Provider 适配（OpenAI-compatible）

## 2. 目录结构

- `qteasy/ai/contracts.py`：统一契约
- `qteasy/ai/registry.py`：技能注册与发现
- `qteasy/ai/planner.py`：规则驱动计划生成
- `qteasy/ai/executor.py`：计划执行与 run 记录
- `qteasy/ai/provider.py`：Provider 抽象与 OpenAI-compatible 实现
- `qteasy/ai/memory_store.py`：本地记忆与执行记录
- `qteasy/ai/skills/*.py`：阶段A只读技能
- `qteasy/ai/cli.py`：CLI 入口
- `qteasy/ai/app.py`：Notebook/CLI 共享应用层

## 3. 运行模式

- Ask：只返回 plan，不执行技能
- Plan：默认返回 dry-run plan
- Run：确认后执行并写入 `runs`

## 4. 本地配置

### 4.1 记忆目录

- 默认：`./.qteasy/ai/`
- 可通过环境变量覆盖：`QTEASY_AI_HOME`

### 4.2 Provider 配置

- `QTEASY_AI_MODEL`
- `QTEASY_AI_API_KEY`
- `QTEASY_AI_BASE_URL`

当上述配置完整时，可通过 `OpenAICompatProvider` 发起真实请求。

## 5. CLI 用法

```bash
qteasy-ai ask "list built-in strategies"
qteasy-ai plan "show kline summary of 000300.SH"
qteasy-ai run "export kline of 000300.SH"
qteasy-ai provider-check
```

## 6. 输出契约摘要

技能统一返回字段：

- `ok`
- `skill_name`
- `run_id`
- `inputs_echo`
- `metrics`
- `data_summary`
- `artifacts`
- `warnings`
- `error`

用户可见错误信息保持英文，便于统一对外输出约定。
