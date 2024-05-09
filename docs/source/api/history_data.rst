历史数据获取和管理
============================

使用qteasy可以获取并管理大量的历史数据。qteasy可以管理的历史数据涵盖股票、基金、指数、期货等等，种类包含价格数据、技术指标、宏观经济、公司财报、宏观金融等等。

所有数据都可以通过tushare的接口获取，下载到本地之后，就可以通过qteasy的接口进行管理和调用了。

查找支持历史数据:

.. autofunction:: qteasy.find_history_data

下载历史数据

.. autofunction:: qteasy.refill_data_source

历史数据下载到本地之后，可以检查、管理、调用这些数据。

检查本地数据:

.. autofunction:: qteasy.get_table_info

获取已经下载的本地数据总览:

.. autofunction:: qteasy.get_table_overview

.. autofunction:: qteasy.get_data_overview

下载数据基础数据:

.. autofunction:: qteasy.get_basic_info

.. autofunction:: qteasy.get_stock_info

.. autofunction:: qteasy.filter_stock_codes

.. autofunction:: qteasy.filter_stocks

