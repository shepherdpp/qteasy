# 模拟实盘交易——TUI 功能清单

本文从功能清单角度介绍 TUI 的模拟实盘能力。  
如需手把手步骤，请阅读 `tutorials/8-live-trade-risk-and-broker-walkthrough.md`。

## 0. 文档边界

- 本页是 TUI 能力索引，不替代步骤教程
- 重点回答“在界面上看哪里、发生异常先看什么”

## 1. 面板与交互能力

- 账户与资金状态展示
- 订单提交与撤单交互
- 成交与历史信息查看
- 系统日志与风险反馈显示

## 2. 核心反馈语义

- 风控拒单摘要在交互中更容易识别
- 订单状态变化（特别是分批成交）更一致
- 日志链路更清晰，便于从界面跳转排查

示例（用户可见反馈）：

```text
Order rejected by risk rule [MAX_ORDER_QTY]: order quantity exceeds limit
```

## 3. 快速问题分流（TUI 视角）

- “界面没报错但下单失败”通常是风控拒绝，不是系统崩溃
- “订单一直 partial-filled”需要结合累计成交量判断最终状态

## 4. 面板-文档映射

| 关注点 | 先看哪里 |
|---|---|
| 运行启动与配置核对 | `live_trading/2-configuration-and-run.md` |
| 拒单/状态解释 | `live_trading/3-risk-and-order-lifecycle.md` |
| 日志排障 | `live_trading/5-artifacts-and-troubleshooting.md` |
| 完整实操路径 | `tutorials/8-live-trade-risk-and-broker-walkthrough.md` |

## 5. 跳转导航

- 配置与运行：`live_trading/2-configuration-and-run.md`
- 生命周期：`live_trading/3-risk-and-order-lifecycle.md`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting.md`