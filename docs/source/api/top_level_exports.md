本文件用于开发维护：列出 `qteasy/__init__.py::__all__` 顶层导出 API 的来源模块与文档落点，便于做全局 API 文档一致性审计。

注意：本文件不作为用户教程入口（不会自动出现在 Sphinx TOC 中），仅用于仓库内维护。

## 1. 顶层导出（按 `__all__` 分类）

### 1.1 启动/运行入口（core / configure）

- `run`（`qteasy/core.py`）：统一运行入口（回测/优化/实盘等）
- `is_ready`（`qteasy/core.py`）：检查运行条件
- `info`（`qteasy/core.py`）：帮助/信息入口（目前未实现）
- `configure`（`qteasy/configure.py`）：配置入口
- `set_config`（`qteasy/configure.py`）：配置别名
- `configuration` / `get_config` / `get_configurations`（`qteasy/configure.py`）：查看配置
- `save_config` / `load_config` / `reset_config` / `view_config_files`（`qteasy/configure.py`）：配置文件与重置
- `start_up_settings` / `update_start_up_setting` / `remove_start_up_setting` / `get_start_up_settings`（`qteasy/configure.py`）：启动配置维护
- `start_up_config`（`qteasy/__init__.py`）：启动配置解析结果（常量）

对应文档入口：
- `docs/source/api/use_qteasy.rst`（启动与运行）
- `docs/source/api/api_reference.rst`（配置与参考）

### 1.2 数据获取/概览（core）

- `get_basic_info` / `get_stock_info`（`qteasy/core.py`）
- `get_data_overview` / `refill_data_source`（`qteasy/core.py`）
- `get_history_data` / `get_kline`（`qteasy/core.py`）
- `filter_stock_codes` / `filter_stocks`（`qteasy/core.py`）
- `get_table_info` / `get_table_overview`（`qteasy/core.py`）

对应文档入口：
- `docs/source/api/history_data.rst`
- `docs/source/references/2-get-history-data.md`

### 1.3 研究容器（history）

- `HistoryPanel`（`qteasy/history.py`）
- `dataframe_to_hp` / `stack_dataframes`（`qteasy/history.py`）

对应文档入口：
- `docs/source/api/HistoryPanel.rst`
- `docs/source/tutorials/2.5-historypanel-data-analysis.md`（含 §9–§11：研究→回测迁移、多源拼板、导出 statsmodels）
- `docs/source/design/10-historypanel-factor-research-layer.md`（可选 FactorResearch 层评估）
- 示例：`examples/historypanel_research_to_strategy.py`、`examples/historypanel_multisource_research.py`、`examples/historypanel_statsmodels_export.py`

### 1.4 策略与算子（operator / strategy / built_in）

- `Operator`（`qteasy/qt_operator.py`）
- `BaseStrategy` / `RuleIterator` / `GeneralStg` / `FactorSorter`（`qteasy/strategy.py`）
- `built_ins` / `built_in_list` / `built_in_strategies` / `get_built_in_strategy`（`qteasy/built_in.py`）

对应文档入口：
- `docs/source/api/Operators.rst`
- `docs/source/api/Strategies.rst`
- `docs/source/api/built_in_strategies.rst`

### 1.5 数据源与数据类型（database / datatypes）

- `DataSource`（`qteasy/database.py`）
- `DataType` / `StgData` / `find_history_data`（`qteasy/datatypes.py`）

对应文档入口：
- `docs/source/api/data_source.rst`
- `docs/source/api/data_types.rst`

### 1.6 可视化与费用（visual / finance）

- `candle`（`qteasy/visual.py`）
- `CashPlan` / `set_cost` / `update_cost`（`qteasy/finance.py`）

对应文档入口：
- `docs/source/api/use_qteasy.rst`（入口）

### 1.7 常量与全局对象（__init__）

- 模式常量：`LIVE_MODE` / `BACKTEST_MODE` / `OPTIMIZE_MODE` / `PREDICT_MODE` 及别名
- 路径与对象：`QT_ROOT_PATH` / `QT_SYS_LOG_PATH` / `QT_TRADE_LOG_PATH` / `QT_CONFIG` / `QT_DATA_SOURCE` / `logger_core`
- 版本：`__version__` / `version_info`

对应文档入口：
- `docs/source/api/use_qteasy.rst`（运行模式与常量速查）

