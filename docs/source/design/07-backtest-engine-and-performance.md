# 回测引擎与性能（设计视角）

本章从**架构与实现**角度说明 qteasy 回测引擎的向量化与 Numba 使用方式，以及与 VectorBT 等框架的差异，供需要深入理解或做技术选型的读者参考。使用层面的说明见《回测并评价交易策略》中的 [6. 回测引擎与性能](../back_testing/6.%20backtest_engine_and_performance.md)。

## 1. 回测引擎在整体中的位置

回测模式（mode=1）的流程在 [回测、实盘与优化](06-backtest-live-optimization.md) 中已概括：准备历史数据 → 构建 Backtester → 按 group_timing_table 逐步运行 Operator 生成信号 → 解析信号并模拟成交 → 评价与输出。其中，“解析信号并模拟成交”由 **backtest** 模块中的 Numba 函数完成，实现“时间维顺序、标的维向量化”。

## 2. Numba 使用点与向量化结构

### 2.1 核心函数

在 `qteasy/backtest.py` 中：

- **backtest_step**：`@njit(nogil=True, cache=True)`。单步内根据信号与当前持仓、现金、交割队列，计算买卖量、费用、持仓更新与交割队列更新；对整批标的做数组运算。
- **calculate_trade_results**：`@njit`，用于交易结果与资金变动计算。
- **backtest_batch_steps**：`@njit(nogil=True, cache=True)`。在 Numba 内按 `signal_count`（时间步数）循环，每步调用 `backtest_step`，完成整段回测，实现“时间维顺序、标的维向量化”。
- **backtest_flash_steps**：`@njit(nogil=True, cache=True)`。与 `backtest_batch_steps` 类似，但不保留中间资金与持仓序列，仅保留最终状态，用于优化阶段多组参数回测时节省内存。

在 `qteasy/blender.py` 中，信号混合用的部分算子（如 `op_sum`、`op_floor` 等）也使用 `@njit` 加速。

### 2.2 时间维顺序与标的维向量化

- **时间维必须顺序**：因为存在交割队列、T+1、MOQ 等状态，下一笔交易依赖当前持仓与交割状态，无法在时间轴上完全并行或一次性矩阵化。
- **标的维向量化**：在每一个时间步内，对所有标的的 signal、持仓、买卖量、费用等用 NumPy 数组与 Numba 内联运算，避免 Python 层循环。

因此，单次回测可以理解为：**一层 Numba 内的时间步循环 + 每步内的向量化计算**。

### 2.3 优化阶段

在 `qteasy/optimization.py` 中，多组参数通过多进程（如 `ProcessPoolExecutor`）并行执行回测；每组内部使用 `backtest_flash_steps` 等路径，只保留最终资金/持仓，以降低内存占用并提高吞吐。

## 3. 与 VectorBT 的架构差异

| 维度       | qteasy | VectorBT |
|------------|--------|----------|
| 时间维度   | 顺序步进（for 步），每步内向量化 | 全时间轴一次性矩阵运算，无显式时间循环 |
| 标的维度   | 每步对全部标的做数组运算（1D 数组） | 标的与时间一起参与广播，多策略/多参数可一并广播 |
| 核心加速   | backtest_step、backtest_batch_steps、backtest_flash_steps 等为 @njit；信号解析、交割队列等也用 Numba | NumPy + Numba，策略表达为纯数组运算 |
| 状态与约束 | 显式维护现金、持仓、交割队列（T+1 等），状态依赖下一笔，故时间维必须顺序 | 多为简化资金曲线，不强调 T+1/交割/MOQ，易做全矩阵 |

**结论**：qteasy 并非“缺乏向量化/Numba”，而是在保证**状态正确性**（T+1、交割、MOQ、多策略合并等）的前提下，选择了“时间顺序 + 标的维向量化 + Numba 单步”的折中；与 VectorBT 的“全矩阵广播”各有适用场景（qteasy 偏规则严谨与实盘一致，VectorBT 偏海量参数快速筛选）。

## 4. 相关文档

- 统一入口与模式：[回测、实盘与优化](06-backtest-live-optimization.md)。
- 使用侧说明：[回测并评价交易策略 - 回测引擎与性能](../back_testing/6.%20backtest_engine_and_performance.md)。
- 设计初衷与数据隔离：[设计初衷与独特优势](08-design-rationale-and-advantages.md)。
