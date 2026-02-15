# 核心概念速览

本章用表格和简短说明梳理 qteasy 中的核心概念，便于在阅读后续章节或使用 API 时快速查阅。更完整的结构与关系见 [总体架构与设计思路](00-overview.md)。

## 1. 概念表（名称 / 含义 / 在文档中的位置）

| 概念 | 含义 | 本系列中的位置 |
|------|------|----------------|
| **DataSource** | 本地数据存储的抽象，管理文件或数据库中的历史数据表，不主动拉取数据 | [数据获取、存储与数据类型](02-data-layer.md) |
| **数据表** | DataSource 中的表，按统一结构存储行情、财务、宏观等数据 | [数据获取、存储与数据类型](02-data-layer.md) |
| **DataType** | “策略可引用的信息”的类型描述，由 name、freq、asset_type 等确定 | [数据获取、存储与数据类型](02-data-layer.md)、[策略如何声明与使用数据](03-data-in-strategies.md) |
| **htype** | 历史数据类型名称（如 close、open），常与 freq、asset_type 一起用来标识一种数据 | [数据获取、存储与数据类型](02-data-layer.md) |
| **dtype_id** | DataType 的唯一标识，形如 `name_assettype_freq`（如 `close_E_d`） | 下文“dtype_id 的构成与示例” |
| **Operator** | 策略容器与运行入口，持有 Group 列表与 group_timing_table，提供 run(config) | [Operator 与 Group](04-operator-and-groups.md) |
| **Group** | 具有相同 run_freq、run_timing 的策略集合，拥有 signal_type 与 blender | [Operator 与 Group](04-operator-and-groups.md) |
| **Strategy** | 策略基类及其子类，声明 data_types/window_length、Parameter，实现 realize() | [Strategy 如何运行](05-strategy-lifecycle.md) |
| **run_freq** | 策略（组）的运行频率，如 `'d'` 日、`'m'` 月 | [Operator 与 Group](04-operator-and-groups.md) |
| **run_timing** | 策略（组）在周期内的运行时机，如 `'close'` 收盘、`'open'` 开盘 | [Operator 与 Group](04-operator-and-groups.md) |
| **group_timing_table** | 时间步 × Group 的表，标记每个时间步哪些 Group 运行 | [Operator 与 Group](04-operator-and-groups.md) |
| **blender** | 同 Group 内多策略信号的混合方式（表达式或默认规则） | [Operator 与 Group](04-operator-and-groups.md) |
| **signal_type** | 信号类型：PT（目标仓位）、PS（比例买卖）、VS（数量买卖） | 下文“三种信号类型 PT/PS/VS” |
| **Parameter** | 策略可调参数的定义（名称、类型、取值范围等） | [Strategy 如何运行](05-strategy-lifecycle.md) |
| **data_types** | 策略声明的所需数据类型（DataType 或列表） | [策略如何声明与使用数据](03-data-in-strategies.md) |
| **window_length** | 策略所需历史数据的窗口长度（如 20 天） | [策略如何声明与使用数据](03-data-in-strategies.md) |
| **realize()** | 策略逻辑入口，无参数，通过 get_pars/get_data 取数并返回信号 | [Strategy 如何运行](05-strategy-lifecycle.md) |
| **get_data / get_pars** | 在 realize() 内按 dtype_id 取数据、按参数名取可调参数 | [策略如何声明与使用数据](03-data-in-strategies.md) |
| **Backtester** | 回测执行器，按 group_timing_table 驱动 Operator 并模拟成交 | [回测、实盘与优化](06-backtest-live-optimization.md) |
| **Optimizer** | 优化器，在参数空间搜索并多次回测，汇总目标函数 | [回测、实盘与优化](06-backtest-live-optimization.md) |
| **Trader** | 实盘交易管理，按 schedule 触发 Operator 并协调 Broker | [回测、实盘与优化](06-backtest-live-optimization.md) |
| **Broker** | 订单执行与成交回报的接口抽象 | [回测、实盘与优化](06-backtest-live-optimization.md) |
| **config** | 运行配置（资产池、区间、成本、资金计划等），回测/实盘/优化共用 | [回测、实盘与优化](06-backtest-live-optimization.md) |
| **qt.run** | 统一入口：qt.run(op, mode=..., **kwargs) → op.run(config, datasource, logger) | [回测、实盘与优化](06-backtest-live-optimization.md) |

## 2. dtype_id 的构成与示例

dtype_id 由三部分拼接而成：**name_assettype_freq**。

- **name**：数据类型名称（如 close、open、total_mv、pe）。
- **assettype**：资产类型，如 `E`（股票）、`IDX`（指数）、`ANY`（任意）。
- **freq**：数据频率，如 `d`（日）、`w`（周）、`m`（月）、`q`（季）。

示例：

| dtype_id | 含义 |
|----------|------|
| `close_E_d` | 股票日频收盘价 |
| `close_IDX_d` | 指数日频收盘价 |
| `close_ANY_d` | 任意资产日频收盘价 |
| `total_mv_E_q` | 股票季频总市值 |
| `pe_E_d` | 股票日频市盈率（若存在） |

策略在 `get_data(dtype_id)` 时使用的 id 需与策略声明的 DataType 所生成的 dtype_id 一致（通常可通过策略的 `data_type_ids` 属性查看）。

## 3. 三种信号类型 PT/PS/VS 的语义对比表

| 类型 | 全称 | 含义（一句话） | 示例 |
|------|------|----------------|------|
| **PT** | Position Target | 目标持仓比例，信号表示希望达到的多空仓位比例 | 0.5 表示目标 50% 多头仓位 |
| **PS** | Proportion Signal | 比例买卖，信号表示用资金或持仓的多少比例买入/卖出 | 0.5 表示用 50% 资金买入或卖出 50% 持仓 |
| **VS** | Volume Signal | 数量买卖，信号表示买入/卖出的数量（股或份） | 100 表示买入 100 股，-50 表示卖出 50 股 |

同一数值在不同 signal_type 下会被解析为不同的委托意图；Group 的 signal_type 在添加策略时确定，同组内策略输出同一类型信号再由 blender 混合。

## 4. 三种策略基类的输入/输出对比表

| 基类 | 典型用途 | 输入（get_data 等） | 输出（realize 返回值） |
|------|----------|---------------------|------------------------|
| **RuleIterator** | 择时、单规则迭代 | 单资产或多资产的数据窗口（按 dtype_id） | 标量信号（如 1 / -1 / 0），同一规则作用于所有资产 |
| **FactorSorter** | 因子选股 | 多资产截面数据（如多只股票的因子值） | 一维因子数组（每资产一个值），引擎按因子排序与筛选规则选股 |
| **GeneralStg** | 通用多资产策略 | 多资产、多数据类型的数据窗口 | 一维信号数组（每资产一个目标仓位或买卖比例） |

更多细节见 [Strategy 如何运行：时机、数据与参数](05-strategy-lifecycle.md)。
