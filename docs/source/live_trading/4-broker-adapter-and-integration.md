# Broker 适配层与集成

本页面向需要扩展或接入新 Broker 的用户与开发者，重点说明 S1.3 引入的适配层边界。

## 0. 适用场景

- 你希望对接新的 broker（或未来柜台），并保持与现有 Trader 逻辑兼容
- 你需要先打通“提交 -> 回报 -> 状态更新”的最小闭环，再逐步增强

## 1. 适配层目标

- 为 future broker（如 QMT）提供稳定接入点
- 保持与现有 legacy queue 链路兼容
- 在提交与回报阶段维持统一的数据契约

## 2. 核心接口

S1.3 中 Broker 适配层新增/明确了以下接口：

- `connect()`
- `disconnect()`
- `submit(order)`
- `cancel(broker_order_id)`
- `poll_fills(timeout=0.0)`
- `get_remote_orders(account_id=None)`
- `get_remote_positions(account_id=None)`
- `get_remote_cash(account_id=None)`

建议按“最小闭环优先”理解接口职责：

- 连接语义：`connect` / `disconnect`
- 交易语义：`submit` / `cancel`
- 回报语义：`poll_fills`
- 查询语义：`get_remote_*`

## 3. 新旧链路并存关系

- 适配层接口提供“同步提交 + 异步回报”的扩展路径
- legacy `run()+queue` 机制保持可用，确保历史行为兼容
- 收盘处理等路径通过 Broker API 抽象，减少直接操作内部队列

## 4. 契约与校验要点

- 提交订单前应满足订单 dict 契约
- 回报成交结果应满足原始成交 dict 契约
- 不满足契约时应尽早失败，避免错误传播到账本阶段

实践建议：

- 先保证“字段齐全且类型正确”
- 再优化“字段语义与边界行为”一致性

## 5. 最小接入清单（建议）

1. 完成连接/断开语义  
2. 打通 `submit -> poll_fills` 回路  
3. 确保回报字段可通过契约校验  
4. 补齐取消语义与异常路径  
5. 在 CLI/TUI 场景下验证可观测性  

## 6. 边界语义提醒

- 未连接时调用提交/轮询应给出明确错误
- 取消未知订单应返回稳定且可预期的结果
- 轮询超时时应返回空结果而非脏数据

## 7. 最小验收标准

- [ ] `connect` 后可正常提交订单  
- [ ] `submit` 之后可通过 `poll_fills` 获取回报  
- [ ] 回报可通过契约校验  
- [ ] 未连接/未知订单/超时等边界行为稳定  
- [ ] CLI/TUI 场景下可观察到一致反馈  

## 8. 相关跳转

- 生命周期：`live_trading/3-risk-and-order-lifecycle.md`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting.md`
- 设计说明：`design/10-live-trading-s1.3-architecture.md`
