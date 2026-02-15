# Strategy 如何运行：时机、数据与参数

## 1. 策略运行时机

策略的**运行时机**（何时、以何频率运行）不由策略类内部保存，而由其所处的 **Group** 决定。Group 的 **run_freq**、**run_timing** 在将策略加入 Operator 时指定（如 `add_strategy(stg, run_freq='d', run_timing='close')`）。因此，同一策略实例放入不同 run_freq/run_timing 的 Group，就会在不同时刻被调用。

## 2. 单步运行流程（细化）

对**当前时间步**（step_index）：

1. **查 group_timing_table**：取该步对应行，得到本步要运行的 Group 列表（取值为 1 的列）。
2. **对每个运行中的 Group**：
   - 对该 Group 内**每个 Strategy**：根据其 data_types、window_length 与当前步，从已准备的数据中切出本步的**数据窗口**，并调用 **update_running_data_window** 注入到该策略实例（按 dtype_id 写入）。
   - 依次调用该 Group 内每个策略的 **generate()**（内部会调用无参的 **realize()**），收集各策略返回的信号，组成列表。
   - 用该 Group 的 **blender** 将列表中的信号混合成该组的一个合并信号。
3. **若本步有多个 Group 运行**：再按 **group_merge_type** 将各组合并信号合并为一个（或分别输出，依实现而定）。
4. 该步的最终信号交给上层：回测时交给 Backtester 解析为买卖并更新持仓，实盘时交给 Trader/Broker 生成订单。

## 3. Strategy 内部：realize() 与 get_pars / get_data

- **realize()**：无参数。策略逻辑只在此方法内实现；不通过参数接收数据或时间，而是通过 **get_pars(name, ...)** 取可调参数、**get_data(dtype_id)** 取本步已注入的数据窗口。
- **返回值**：标量或一维数组，依策略基类而定（RuleIterator 常为标量，FactorSorter 为因子数组，GeneralStg 为每资产一个信号）。同一段 realize() 在回测与实盘中复用，保证行为一致。

## 4. 可调参数（Parameter）

- **定义**：在策略类的 **__init__** 中通过 **pars**（Parameter 列表或字典）定义可调参数的名称、类型、取值范围等。
- **运行前设置**：通过 **set_parameter**（如 `op.set_parameter(stg_id, pars=(...))`）在运行前写入当前要用的参数值。
- **优化**：Optimizer 在参数空间（由 Parameter 的 par_range 等确定）上采样或搜索，每组参数 set 到 Operator 后执行一次回测，根据目标函数（如夏普比）汇总结果，从而找到较优参数组合。

## 5. 三种策略基类的输入/输出差异

| 基类 | 输入（get_data 等） | 输出（realize 返回值） | 典型用途 |
|------|---------------------|------------------------|----------|
| **RuleIterator** | 单资产或多资产数据窗口，按 dtype_id 取 | 标量（如 1/-1/0），同一规则迭代作用于所有资产 | 择时、单规则多标的 |
| **FactorSorter** | 多资产截面（如每只股票的因子值） | 一维因子数组，引擎按排序与筛选规则选股 | 因子选股 |
| **GeneralStg** | 多资产、多 dtype 的窗口 | 一维信号数组（每资产一个目标仓位或比例） | 通用多资产信号 |

## 6. 小结

同一套“按步 → 准备数据 → 注入 → realize() → 混合”的流程，同时服务回测与实盘：策略不关心当前是回测还是实盘，只依赖 get_pars/get_data 与所属 Group 的时机；运行层负责在不同模式下提供对应数据并处理输出信号。更多实现细节见《使用教程》与 API 参考。
