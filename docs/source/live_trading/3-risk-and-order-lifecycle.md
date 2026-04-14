# 风控与订单生命周期

本页说明两条主线：

- 风控如何影响订单是否进入执行链路
- 订单在提交后如何从未成交走向部分成交或完成

## 0. 适用场景

- 你已经可以运行 live，但需要判断“未成交/拒单/撤单”到底发生了什么
- 你想把界面提示、日志记录和订单状态串成同一条可解释链路

## 1. 风控评估链路

在 live 下单前，系统会基于订单意图与账户快照进行评估，产出 `RiskDecision`。

- 若放行：继续进入建单、校验、提交流程
- 若拒绝：不会写入订单表，也不会进入 Broker 执行队列

可简化理解为：

`OrderIntent -> RiskDecision -> (allow -> submit) / (reject -> stop)`

## 2. 拒单语义与可见性

S1.3 之后，拒单可见性增强：

- CLI/TUI 会显示英文拒因摘要（`rule_id` + `reason`）
- 日志链路可检索拒绝信息，便于审计与复盘
- 拒单兼容语义保持不变：提交接口仍可返回空结果表示未放行

示例（用户可见文案）：

```text
Order rejected by risk rule [MAX_ORDER_QTY]: order quantity exceeds limit
```

## 3. 订单状态生命周期

典型状态流转：

`submitted -> partial-filled -> filled`

也可能出现：

`submitted -> canceled`

建议把“状态不符合预期”的问题拆成两类：

- **未提交类**：通常是风控拒绝或提交前校验失败
- **已提交未完成类**：通常要看成交回报是否持续到达

## 4. 分批成交状态的用户侧变化

optional backlog B1 修复后，分批成交状态判定更贴近实际累计成交量。  
当累计成交量达到目标数量时，状态应由 `partial-filled` 进入 `filled`。

## 5. 收盘后处理（用户视角）

收盘后系统会处理未完成订单，相关逻辑通过 Broker 统一 API 协调。  
这使得撤单与队列排空职责边界更清晰，行为也更稳定可预期。

## 6. 遇到异常时先看什么

1. CLI/TUI 即时反馈  
2. `risk_log` 中的拒绝记录  
3. 订单与成交记录中的状态序列

## 7. 快速判定清单

- [ ] 这笔订单是否进入了提交链路（有无提交记录）  
- [ ] 若未提交，是否能定位到 `rule_id` / `reason`  
- [ ] 若已提交，是否存在对应回报记录  
- [ ] 当前状态是否与累计成交量一致  

## 8. 相关跳转

- 配置启动：`live_trading/2-configuration-and-run.md`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting.md`
- 双路径教程：`tutorials/8-live-trade-risk-and-broker-walkthrough.md`
