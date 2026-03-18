历史数据获取和管理
============================

使用qteasy可以获取并管理大量的历史数据。qteasy可以管理的历史数据涵盖股票、基金、指数、期货等等，种类包含价格数据、技术指标、宏观经济、公司财报、宏观金融等等。

所有数据都可以通过tushare的接口获取，下载到本地之后，就可以通过qteasy的接口进行管理和调用了。

查找支持历史数据
----------------------

使用 ``qt.find_history_data()`` 可以按名称、中文描述或通配符在全部已知历史数据类型中
进行搜索，并按需要返回兼容 ``get_history_data()`` 的 data_id 列表或结构化的 DataFrame
结果，便于探索可用的数据字段。

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
做前置筛选。

.. autofunction:: qteasy.get_basic_info

.. autofunction:: qteasy.get_stock_info

.. autofunction:: qteasy.filter_stock_codes

.. autofunction:: qteasy.filter_stocks

使用下载的数据——获取价格或技术指标
----------------------------------------------------

.. autofunction:: qteasy.get_history_data

