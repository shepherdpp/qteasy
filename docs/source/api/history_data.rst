历史数据获取和管理
============================

使用 qteasy 可以获取并管理大量金融数据。本地库涵盖股票、基金、指数、期货等，种类包含价格、技术指标、宏观、财报等。

数据通常经远端渠道下载到本地 DataSource 后，再按 **DataType 信息 ID** 与消费形状选用入口提取。

查找支持的数据类型
----------------------

使用 ``qt.find_history_data()`` 可以按名称、中文描述或通配符搜索内置类型。
结构化结果（``as_data_frame=True``）含 ``kind``、``usable_in``、``recommended_api``；
请按推荐入口取数，不要一律调用 ``get_history_data``。

.. autofunction:: qteasy.find_history_data

下载历史数据
----------------------

通过 ``qt.refill_data_source()`` 可以从远端金融数据 API 批量下载指定表或用途的数据
（支持按数据类型、频率、资产类型等筛选），并在本地 DataSource 中完成清洗与写入；
依赖表与交易日历的刷新会在内部自动处理，具体工作流与推荐参数组合见 manage_data 系列文档。

.. autofunction:: qteasy.refill_data_source

历史数据下载到本地之后，可以检查、管理、调用这些数据。

检查本地数据
--------------------------------

.. autofunction:: qteasy.get_table_info

获取已经下载的本地数据总览
--------------------------------------------------

``qt.get_table_overview()`` 与 ``qt.get_data_overview()`` 会汇总展示本地数据源中各类
数据表当前是否有数据、占用磁盘空间、记录条数以及时间覆盖范围，适合作为检查数据准备
情况的入口。

.. autofunction:: qteasy.get_table_overview

.. autofunction:: qteasy.get_data_overview

使用下载的数据——基础数据
---------------------------------------------------

``qt.get_basic_info()`` 和 ``qt.get_stock_info()`` 提供按代码或名称查询股票/基金/指数等
基础信息的入口，可配合 ``filter_stock_codes()`` 与 ``filter_stocks()`` 构建资产池或
做前置筛选。截面属性（行业、上市日等）的标准化入口见下文 ``get_static_data``。

.. autofunction:: qteasy.get_basic_info

.. autofunction:: qteasy.get_stock_info

.. autofunction:: qteasy.filter_stock_codes

.. autofunction:: qteasy.filter_stocks

使用下载的数据——按形状取数
----------------------------------------------------

按 **消费形状** 选择入口（概念见 :doc:`DataType 概念章 <../manage_data/02. datatypes>`）：

- **History**（时间 × 标的）：``get_history_data`` / ``get_kline`` —— 可编入 HistoryPanel / 策略窗口
- **Reference**（仅时间）：``get_reference_data`` —— 宏观、资金流，或 ``close-000300.SH`` 这类基准造法
- **Static**（仅标的）：``get_static_data`` —— 行业、上市日等截面属性

错形状会报错并提示正确入口。完整 id 与业务分册清单见
:doc:`内置 DataType 完整清单 <../references/datatypes/index>`。

``qteasy.history.get_history_panel()`` 面向已明确 ``DataType`` 列表与 ``DataSource``、
需要直接组装 ``HistoryPanel`` 的偏低层场景；用户文档以公开三入口为主线。

.. autofunction:: qteasy.get_history_data

.. autofunction:: qteasy.get_reference_data

.. autofunction:: qteasy.get_static_data

.. autofunction:: qteasy.get_kline
