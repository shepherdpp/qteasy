# 教程 8：模拟实盘中的风控与 Broker 适配（双路径）

本教程通过两条完整路径，带你在模拟实盘中验证 S1.3 的关键行为：

- 路径 A：`asset_type='E' + simulator`
- 路径 B：`asset_type='FD' + simulator`

目标是“跑通 + 观测 + 验证”，而不是只看概念。

## 0. 教程目标

- 跑通两条路径（E 与 FD）
- 人工触发一次拒单并定位原因
- 观察分批成交状态从 `partial-filled` 到 `filled` 的可见行为

## 1. 前置准备

- 已有可运行的 `Operator`
- 本地数据可支持运行频率
- 已配置 live 账户参数

建议先准备一个“可稳定触发拒单”的规则配置（例如较小的单笔数量上限），便于复现实验。

## 2. 路径 A：E + simulator

### 步骤 1：设置配置

```python
import qteasy as qt

qt.configure(
    mode=0,
    asset_type='E',
    live_trade_broker_type='simulator',
    live_price_acquire_channel='eastmoney',
    live_price_acquire_freq='15MIN',
)
```

### 步骤 2：启动运行

```python
qt.run(op)
```

### 步骤 3：提交一笔测试订单并观察反馈

- 关注是否出现提交成功提示
- 关注是否出现风控拒单提示（英文）
- 记录一次订单 ID（后续对照日志）

## 3. 路径 B：FD + simulator

### 步骤 1：切换资产类型配置

```python
import qteasy as qt

qt.configure(
    mode=0,
    asset_type='FD',
    live_trade_broker_type='simulator',
    live_price_acquire_channel='eastmoney',
    live_price_acquire_freq='15MIN',
)
```

### 步骤 2：重复启动与下单

```python
qt.run(op)
```

### 步骤 3：验证行为一致性

- FD 路径应可进入 live 运行链路
- 拒单/提交/日志的观察方式与 E 路径一致
- 同一类订单在两条路径下应有一致的反馈语义

## 4. 人工触发一次风控拒单

建议临时设置严格规则（如单笔数量上限），提交超限订单。  
你应看到类似英文提示：

```text
Order rejected by risk rule [MAX_ORDER_QTY]: order quantity exceeds limit
```

并可在 `risk_log` 中检索到对应记录。

建议至少验证两次：

1. 一次被拒（确认拒因可见）  
2. 一次放行（确认策略可继续运行）

## 5. 观察订单状态变化

重点观察是否出现：

- `submitted -> partial-filled -> filled`

在分批成交场景中，最终状态应与累计成交量一致。

如果你看到了 `partial-filled` 长时间不变，请回到排错页按“状态理解偏差”剧本核对日志。

## 6. 教程验收清单

- [ ] E 路径可运行  
- [ ] FD 路径可运行  
- [ ] 可触发并识别风控拒单  
- [ ] 可在日志中定位拒单原因  
- [ ] 可观察并理解分批成交状态变化
- [ ] 至少完成一次“拒单 -> 调整参数 -> 放行”闭环验证

## 7. 下一步

- 深入机制：`live_trading/3-risk-and-order-lifecycle`
- 扩展 Broker：`live_trading/4-broker-adapter-and-integration`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting`

## 8. 结果判定标准

当你完成本教程后，应能独立回答以下问题：

- 当前订单是被风控拒绝，还是已提交但未成交？
- 为什么某笔订单会停留在 `partial-filled`？
- 需要去哪个日志文件先看、再看什么字段？

若以上三题都能独立回答，说明你已经具备 live 场景下的基本排错能力。
