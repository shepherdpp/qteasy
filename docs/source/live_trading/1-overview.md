# live_trading 模块总览

`live_trading` 模块用于说明 qteasy 在模拟实盘（`mode=0`）下的核心能力与使用路径。  
对于第一次进入 live 运行的用户，本页只解决三个问题：能做什么、有哪些新变化、下一步看哪里。

## 0. 适用场景

- 你已经完成策略回测，准备进入模拟实盘阶段
- 你需要快速建立“配置 -> 下单 -> 成交 -> 日志 -> 排错”的整体认知
- 你计划后续扩展 broker 适配能力

## 1. 这个模块解决什么问题

- 统一解释 live 运行中“配置、下单、成交、日志、排错”的完整链路
- 降低从回测切换到模拟实盘时的理解成本
- 给后续扩展真实柜台适配（如 QMT）提供稳定文档入口

## 2. S1.3 完成后的能力地图

- **配置可校验**：live 参数在运行前集中校验，错误更早暴露
- **风控可插拔**：订单提交前可执行规则链评估
- **拒单可审计**：拒因可通过 `rule_id` 和 `reason` 在日志中检索
- **Broker 可扩展**：新增适配层接口，兼容 legacy 队列链路
- **状态更一致**：`partial-filled -> filled` 的可见行为更准确

## 3. 核心术语速览

- `LiveTradeConfig`：live 运行配置快照
- `RiskDecision`：风控评估结果（是否放行 + 拒因）
- `broker adapter`：`connect/submit/poll_fills` 等适配层接口
- `risk_log`：风险拒绝与相关风控事件日志
- `partial-filled`：订单部分成交状态

## 4. 推荐阅读路径

1. 先读 :doc:`2-configuration-and-run`，完成最小可运行配置  
2. 再读 :doc:`../tutorials/8-live-trade-risk-and-broker-walkthrough`，按步骤走一遍  
3. 遇到问题时查 :doc:`5-artifacts-and-troubleshooting`  
4. 需要扩展 Broker 时读 :doc:`4-broker-adapter-and-integration`

## 5. 相关索引

- API 视角清单：`references/1-simulation-overview.md`
- CLI 功能清单：`references/5-simulate-operation-in-CLI.md`
- TUI 功能清单：`references/6-simulate-operation-in-TUI.md`
- 设计理念：`design/10-live-trading-s1.3-architecture.md`
