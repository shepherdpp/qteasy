# Operator 与 Group：谁在何时运行

## 1. 运行层在整体中的位置

运行层负责**按时间驱动**策略执行、汇总各策略信号，并将结果交给回测/实盘/优化使用。核心是 **Operator**：它既是策略的容器，也是统一的运行入口（`op.run(config, datasource, logger)`）。Operator 通过 **Group** 与 **group_timing_table** 决定“每个时间步由哪些策略运行、信号如何混合”，从而实现与回测区间和运行频率一致的可重复执行。

## 2. Operator 的角色

- **策略容器**：持有多个 **Group**，每个 Group 内包含若干策略（Strategy）。用户通过 `add_strategy` / `Operator([...])` 添加策略时，根据 **run_freq**、**run_timing** 将策略归入已有 Group 或新建 Group。
- **运行入口**：对外提供 **run(config, datasource, logger)**。config 中包含资产池、回测区间、成本、资金计划等；datasource 提供历史或实时数据；运行逻辑按 **group_timing_table** 逐步执行各组策略并汇总信号。
- **持有 group_timing_table**：该表在运行前根据回测区间（或实盘 schedule）与各 Group 的 run_freq、run_timing 生成，每一行对应一个时间步，每一列对应一个 Group，取值为 1 表示该步该组运行、0 表示不运行。

## 3. Group 的概念

- **定义**：一个 Group 是一组具有相同 **run_freq**、**run_timing** 的策略集合，并拥有统一的 **signal_type**（PT/PS/VS）和 **blender**（混合规则）。
- **为何按“运行时机”分组**：同一时刻运行的策略共享同一套“当前时间步”的数据与调度；混合时也按“同组信号”用 blender 合并，再按 group_merge_type 处理多组并存的情况，便于理解和配置。

## 4. Operator 与 Group 的关系

- Operator 包含多个 Group；每个 Group 包含多个 Strategy。
- 添加策略时，若已存在相同 run_freq、run_timing 的 Group，则策略加入该 Group；否则新建 Group。因此 Group 的划分完全由“运行时机”决定，策略类自身不保存 run_freq/run_timing，由所属 Group 管理。

## 5. group_timing_table

- **含义**：二维表，行 = 时间步（与回测区间或实盘 schedule 对齐），列 = Group；单元格为 1 表示该步运行该 Group，0 表示不运行。
- **与回测区间、run_freq 的关系**：回测时，根据 invest_start、invest_end 与交易日历生成时间轴，再根据各 Group 的 run_freq、run_timing 在该时间轴上标记“哪些步运行哪些 Group”，得到 group_timing_table。实盘时同理，按实际运行日与 run_freq/run_timing 决定何时触发哪些 Group。

## 6. blender

- **作用**：同一 Group 内可能有多个策略，每步各策略输出一个信号（标量或数组）。**blender** 将这些信号按一定规则混合成该 Group 的**一个**合并信号（如加权平均、求和等）。
- **配置方式**：可为表达式（如 `0.5*s0+0.5*s1`），或使用默认规则：PT 下常用各策略目标仓位的平均，PS/VS 下常用求和等，具体以文档与 API 为准。
- **结果**：混合后的信号作为该步、该组的输出，再根据 group_merge_type 与其它组的输出合并（若有多组同时运行）。

## 7. group_merge_type

当同一时间步有多个 Group 运行时，**group_merge_type** 决定各组信号如何合并：

- **None**：各 Group 独立输出，不合并（多组时可能产生多条执行路径，取决于上层如何使用）。
- **And**：各组信号相乘等逻辑与合并。
- **Or**：各组信号相加等逻辑或合并。

具体语义以当前版本文档为准；通常单组使用时无需关心。

## 8. 小结

Operator 通过 Group 与 group_timing_table 实现“按时间步、按组”的统一调度：每一步只运行该步标记为 1 的 Group，组内策略共享数据注入与 blender，输出合并信号供回测/实盘/优化使用。更多用法见《使用教程》与 API 文档。
