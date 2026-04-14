# live_trading 配置与运行

本页给出最小可运行路径，帮助你在最短时间内把模拟实盘运行起来。

## 0. 适用场景

- 你已经有可运行的 `Operator`，准备从回测进入模拟实盘
- 你希望先跑通最小路径，再逐步补充风控与运维细节

## 1. 前置条件

- 已创建可用的 `Operator` 与策略组
- 本地数据源可用（可支持运行频率的数据）
- 已设置或准备设置 live 账户参数

## 2. 最小配置集

常见必配项包括：

- `mode=0`
- `asset_type`
- `live_trade_account_id` 或 `live_trade_account_name`
- `live_trade_broker_type`（通常为 `simulator`）
- `live_price_acquire_channel`
- `live_price_acquire_freq`

建议同时显式确认以下运行相关配置，避免“能启动但行为不符合预期”：

- `trade_batch_size` / `sell_batch_size`
- `cash_decimal_places` / `amount_decimal_places`
- `sys_log_file_path` / `trade_log_file_path`

## 3. 推荐配置模板

### 模板 A：股票路径（E + simulator）

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

### 模板 B：基金路径（FD + simulator）

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

## 4. 启动流程

1. 完成配置并检查账户参数  
2. （可选）先打印关键配置，确认本次运行快照  
3. 调用 `qt.run(op)` 进入 live 运行  
4. 在 CLI/TUI 观察运行状态、订单变化和日志输出  

建议在启动前做一次配置确认：

```python
import qteasy as qt

print(qt.get_config('mode'))
print(qt.get_config('asset_type'))
print(qt.get_config('live_trade_broker_type'))
print(qt.get_config('live_price_acquire_channel'))
```

## 5. 运行前检查清单

- 账户 ID/名称是否可用
- `asset_type` 与资产池是否匹配
- broker 类型是否与当前测试目的一致
- 数据获取频率是否与策略运行频率协调

## 6. 启动后关键观测点

- 是否成功进入 live 主循环
- 下单后是否有提交反馈
- 拒单是否包含英文 `rule_id` / `reason`
- 日志目录中是否生成预期产物

推荐按下面顺序判定“是否跑通”：

1. 能稳定进入运行循环  
2. 能看到至少一次订单相关反馈（提交或拒绝）  
3. 能在日志中对齐同一事件（界面提示与日志一致）  

## 7. 常见启动失败与处理

- **配置校验失败**：先修复提示字段，再重启
- **账户不可用**：检查账户 ID/名称及初始化参数
- **数据不可用**：检查数据渠道与频率设置
- **路径问题**：检查日志路径配置是否合法且可写
- **频率不协调**：检查策略运行频率与 live 价格频率是否匹配

## 8. 相关跳转

- 风控与状态：`live_trading/3-risk-and-order-lifecycle.md`
- 排错手册：`live_trading/5-artifacts-and-troubleshooting.md`
- 完整演练：`tutorials/8-live-trade-risk-and-broker-walkthrough.md`

## 9. 最小验收标准

- [ ] 可在 E 或 FD 路径下稳定启动  
- [ ] 可观察到一条订单提交或拒绝事件  
- [ ] 若拒绝，可读到英文 `rule_id` / `reason`  
- [ ] 日志目录中可找到对应运行产物
