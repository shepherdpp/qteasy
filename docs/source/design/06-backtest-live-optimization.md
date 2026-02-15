# 回测、实盘与优化：统一入口与不同模式

## 1. 统一入口

用户通过 **qt.run(op, mode=..., **kwargs)** 触发运行。内部会：

- 将 kwargs 与全局配置合并为 **config**（ConfigDict）。
- 调用 **op.run(config, datasource, logger)**，并传入 qteasy 的默认 datasource 与 logger。

**mode** 决定走哪条分支：

- **mode=0**：实盘模式，进入 Trader 流程（定时触发、获取实时数据、生成信号、下单并记录）。
- **mode=1**：回测模式，构建 Backtester，按 group_timing_table 逐步运行 Operator，模拟成交并输出资金曲线与绩效。
- **mode=2**：优化模式，Optimizer 在参数空间搜索，每组参数执行一次回测，按目标函数汇总结果。
- **mode=3/4**：追踪、预测等模式，参见文档与 API。

因此，**同一 Operator** 在不同 mode 下复用同一套“按时间步运行策略、混合信号”的机制，差异仅在数据来源与结果处理。

## 2. 配置（config）的作用

**config** 包含资产池、回测区间、成本参数、资金计划等，回测/实盘/优化共用同一套配置结构。例如：

- 资产池、资产类型、回测起止日；
- 交易成本（费率、最低费用等）；
- 资金投入计划（invest_cash_amounts 等）；
- 实盘相关（账户、Broker 类型等，mode=0 时使用）。

config 由 **qt.run(..., **kwargs)** 与全局 QT_CONFIG 合并得到，并传入 **op.run(config, ...)**，由 Backtester、Trader、Optimizer 分别读取所需字段。

## 3. 回测模式（mode=1）

1. **准备历史数据**：根据 config 中的资产池、回测区间与 Operator 内所有策略的 data_types、window_length，调用 **check_and_prepare_backtest_data** 等，从 DataSource 拉取并组装所需历史数据（含足够的历史窗口以覆盖区间起点）。
2. **构建 Backtester**：传入 Operator、资产列表、资金计划、交易价格数据、成本参数等，生成 **Backtester** 实例。
3. **按步运行**：按 **group_timing_table** 的每个时间步，调用 **op.run_strategies(steps)**（或等价接口），得到每一步的 (signal_type, signal)。
4. **解析与模拟成交**：将信号按 signal_type（PT/PS/VS）解析为买卖意图，再通过 **backtest_step** 等逻辑更新持仓、资金与交割队列，得到每日资金曲线与交易记录。
5. **评价与输出**：对资金曲线与交易记录做绩效评价（如夏普、回撤等），返回给用户并可选生成报告与图表。

## 4. 实盘模式（mode=0）

1. **Trader** 持有 Operator 与 config，按 **run_freq**、**run_timing** 与交易日历在交易日内的指定时刻触发任务。
2. **获取当前时刻数据**：根据策略声明从 DataSource（或实时接口）获取当前步所需的数据窗口。
3. **运行 Operator**：在该步调用 Operator 生成信号（与回测相同的 run_strategy 流程）。
4. **解析并下单**：将信号解析为订单，交给 **Broker** 执行（模拟或真实券商接口），并记录成交与持仓。

## 5. 优化模式（mode=2）

1. **Optimizer** 根据策略的 **Parameter** 定义确定参数空间（如网格、随机采样、遗传算法等）。
2. 对每组参数：通过 **set_parameter** 等将参数写入 Operator，然后执行一次**回测**（即 mode=1 的流程）。
3. 根据回测结果计算**目标函数**（如夏普比、收益回撤比等），汇总所有参数组合的结果。
4. 输出较优参数组合及对应回测结果，供用户选择。

## 6. 小结

回测、实盘、优化共享“Operator + 按时间步运行”的机制：都是先准备数据与 config，再按 group_timing_table 逐步调用策略并混合信号。差异仅在于：回测使用历史数据与 Backtester 模拟成交；实盘使用实时数据与 Trader/Broker 执行订单；优化则多次回测并比较目标函数。更多参数与用法见《使用教程》《回测并评价交易策略》《优化交易策略》与 API 参考。
