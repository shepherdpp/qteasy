# Live Trading S1.3 设计理念与架构

本文从设计视角解释 S1.3 的 live trading 改造思路：为什么这样分层、如何保持兼容、以及这些设计如何帮助后续扩展。

## 0. 文档定位

- 本文是设计说明，不是使用教程
- 重点回答“为什么这样做”，而不是“如何一步步操作”
- 若需要实操路径，请转到 `live_trading/2-configuration-and-run.md` 与 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`

## 1. 设计目标

- 在不破坏既有用户路径的前提下，提升 live 链路的可校验性与可审计性
- 把风险控制前置到“下单写库之前”
- 抽象 Broker 适配层，为未来真实柜台接入预留稳定边界

## 2. 分层结构

S1.3 的 live 相关职责可抽象为：

- `Operator`：策略运行调度与信号来源
- `Trader`：订单意图落地、风险闸门与执行协调
- `RiskManager`：纯逻辑规则评估，不依赖 IO
- `Broker`：提交、取消、回报、连接语义
- `trade_io`：订单/成交数据契约校验

## 3. 关键设计原则

### 3.1 契约先行

订单 dict 与成交 dict 在边界处校验，避免“结构错了还能跑”导致的静默错误。

### 3.2 风控前置

风险评估在写库和入队之前完成，拒单不污染执行数据。

### 3.3 适配解耦

通过 broker adapter API 承载未来接入，降低 Trader 与具体柜台的耦合度。

### 3.4 可审计

拒因以 `rule_id` 和英文 `reason` 对外可见，支持运维检索与复盘。

## 4. 典型疑难点与取舍

### 4.1 拒单兼容语义

保持历史兼容（拒单可表现为空结果），同时增强可见性（CLI/TUI 摘要 + 日志）。

### 4.2 新旧链路并存

保留 legacy queue 兼容路径，避免一次性迁移带来的回归风险。

### 4.3 状态一致性

分批成交场景下，状态应以累计成交量为准，减少用户观察到的语义偏差。

## 5. 与 S2.1 的关系

S1.3 不是柜台接入终点，而是前置地基：

- 先稳定接口边界
- 再逐步接入真实柜台
- 最后在不破坏上层用法的前提下扩展能力

## 6. 对用户行为的影响

- 配置错误更早暴露
- 拒单原因更容易定位
- live 运行中的状态变化更容易解释
- 扩展第三方 broker 的成本更可控

## 7. 相关阅读

- 模块总览：`live_trading/1-overview.md`
- 运行与配置：`live_trading/2-configuration-and-run.md`
- 风控与状态：`live_trading/3-risk-and-order-lifecycle.md`
- Broker 接入：`live_trading/4-broker-adapter-and-integration.md`
