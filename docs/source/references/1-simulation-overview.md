# 模拟实盘功能总览（API 视角）

本文从 API 和功能清单角度介绍 qteasy 的模拟实盘能力。  
如需手把手操作，请阅读 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`。

## 0. 文档边界

- 本页只给出“对象/接口清单 + 行为速查 + 跳转索引”
- 不展开步骤教程、不展开底层实现推导

## 1. 核心对象与职责

| 对象 | 主要职责 | 常见入口 |
|---|---|---|
| `Operator` | 运行策略与生成信号 | `qt.run(op)` |
| `Trader` | 下单协同、风控衔接、状态维护 | live 运行主链路 |
| `RiskManager` | 规则链评估与放行/拒绝决策 | `submit_trade_order` 前 |
| `Broker` | 提交、取消、回报、远端查询 | `submit/cancel/poll_fills` |
| `trade_io` | 订单与成交字典契约校验 | 提交前与回报后 |

## 2. 功能分区清单

| 功能区 | 核心能力 | 对应页面 |
|---|---|---|
| 配置与启动 | live 配置校验与运行快照 | `live_trading/2-configuration-and-run.md` |
| 下单与风控 | 提交前评估、拒单可见性 | `live_trading/3-risk-and-order-lifecycle.md` |
| 成交与状态 | 分批成交与状态收敛 | `live_trading/3-risk-and-order-lifecycle.md` |
| 适配与扩展 | adapter API 与兼容边界 | `live_trading/4-broker-adapter-and-integration.md` |
| 日志与排错 | `sys_log/trade_log/risk_log` 排查顺序 | `live_trading/5-artifacts-and-troubleshooting.md` |

## 3. S1.3 行为变化速查

- `asset_type='FD'` 的模拟实盘可运行性增强
- 风控拒单在 CLI/TUI 中更可见
- Broker 适配层接口补齐，便于后续柜台接入
- 分批成交状态显示更一致

## 4. 入口索引

- CLI 清单：`references/5-simulate-operation-in-CLI.md`
- TUI 清单：`references/6-simulate-operation-in-TUI.md`
- API 自动文档：`api/api_reference.rst`

## 5. 相关阅读

- 模块总览：`live_trading/1-overview.md`
- 配置运行：`live_trading/2-configuration-and-run.md`
- 风控与生命周期：`live_trading/3-risk-and-order-lifecycle.md`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting.md`