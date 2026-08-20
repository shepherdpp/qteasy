# 数据获取、存储与数据类型

## 1. 数据层在整体中的位置

数据层为策略层与运行层提供“按类型、按窗口”的历史信息。策略不直接访问原始数据表，而是声明自己需要哪些 **DataType** 以及多长的 **window_length**；运行前，引擎根据这些声明从 **DataSource** 中取出对应数据、整理成数据窗口并注入策略。这样既保证了回测与实盘使用同一套数据视图，也从机制上避免了策略使用“未来数据”。

## 2. 从原始数据到本地存储

### 2.1 数据流

外部数据源（如 Tushare、东方财富等）→ 拉取与清洗（格式统一、去重、对齐）→ **DataSource**（文件或数据库）→ 以统一结构写入多张**数据表**。

### 2.2 DataSource 的角色

- **统一存储抽象**：无论底层是 CSV/HDF/Feather 文件还是 MySQL 等数据库，对上层而言都是“按表名、按列”读写。
- **多引擎支持**：可配置为 file（csv/hdf/fth）或 db（mysql 等），满足不同部署需求。
- **不主动拉数**：DataSource 只负责读写本地已存在的数据；从网络拉取与更新由用户或定时任务调用数据接口完成，再写入 DataSource。

因此，数据层设计把“拉取”和“存储”分开：拉取得到的数据经清洗后写入 DataSource，策略与回测只消费 DataSource 中已有的数据。

## 3. 数据表

- **内置表划分**：qteasy 预定义了多张数据表，大致包括行情类（如日线、分钟线）、财务类（利润表、资产负债表等）、宏观与指数等。每张表有固定的表名、主键与列结构。
- **表结构与 DataType 的对应关系**：一种“可被策略引用的信息”往往对应某张表的某列（或若干列经计算得到）。DataType 的 **name**（及 freq、asset_type）与数据表/列的映射在系统内维护，策略只需通过 DataType 或 **dtype_id** 声明需求，无需关心具体表名或列名。

## 4. DataType：从“表里的数据”到“策略可引用的信息”

用户日常写**字符串信息 ID**；`DataType(...)` 对象多为专家/内置策略层。内部字段 `acquisition_type`（直读、复权、事件等）是提取算法，**不是**用户分类。

### 4.1 三种消费形状（kind）

| kind | 形状 | 例子 | 公开入口 |
| --- | --- | --- | --- |
| `history` | 时间 × 标的 | `close`、`pe`、停牌标记 | `get_history_data` / `get_kline` |
| `reference` | 仅时间 | `cn_gdp`、`north_money`；以及把单标的行情抽成基准的 `close-000300.SH` | `get_reference_data` |
| `static` | 仅标的 | `industry`、`list_date` | `get_static_data` |

`close-000300.SH` 是 Reference 的**一种造法**（策略里把某标的当市场基准），不是宏观数据的唯一来源。目录用 `usable_in` 标明推荐入口；`usable_in=none` 表示已登记但暂无一等用法（例如无法编入数值 HistoryPanel 的文本列）。

### 4.2 name、freq、asset_type 与 dtype_id

- **name**：数据类型名称（如 close、open、total_mv、pe），对应某类可用的信息；可带参数（如 `close|b`）或 unsymbolizer（如 `close-000300.SH`）。
- **freq**：数据频率（如 d/w/m/q）；Static 常为 `None`（与频率无关）。
- **asset_type**：适用的资产类型（如 E、IDX、None、Any）。
- **完整 dtype_id**：由上述三者生成，规则为 `{wide_name}_{asset_type}_{freq}`（从右侧拆），例如 `close_E_d`。策略 `get_data` 查找键为完整 id；研究侧可用宽名，歧义时改完整 id。

### 4.3 内置 DataType 与数据表/列的映射

系统内置大量 DataType，分别映射到不同数据表的列或衍生列。具体表名、列名见《下载并管理金融历史数据》与按业务分册的清单；本系列仅强调：**策略与分析通过信息 ID 引用数据，不直接依赖表结构**，表结构演进时只需调整映射关系。

## 5. 小结：为什么策略只接触 DataType 而不直接读表

- **一致性**：回测与实盘都通过同一套“声明信息 ID + 引擎按窗口注入”的路径取数，避免两套逻辑。
- **防未来函数**：引擎严格按当前时间步和 window_length 准备过去的数据窗口，策略无法访问未注入的将来数据。
- **接口统一**：策略用 `get_data(dtype_id)` 取 History/Reference 窗口；截面 Static 走 `get_static_data`，**不**进入 `get_data` 时间窗。

更多用法见 manage_data「DataType」概念章与 API 参考。
