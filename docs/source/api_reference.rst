API References
==============

Configuration
-------------

查看qteasy的配置信息:

.. autofunction:: qteasy.configuration

.. autofunction:: qteasy.get_config

.. autofunction:: qteasy.get_configurations

修改qteasy的配置信息:

.. autofunction:: qteasy.configure

.. autofunction:: qteasy.set_config

将所有的配置变量重置为默认值:

.. autofunction:: qteasy.reset_config

从文件中读取配置信息:

.. autofunction:: qteasy.load_config

将配置信息写入文件:

.. autofunction:: qteasy.save_config

Historical Data Manipulation
----------------------------

查找历史数据:

.. autofunction:: qteasy.find_history_data

获取基础数据:

.. autofunction:: qteasy.get_basic_info

.. autofunction:: qteasy.get_stock_info

.. autofunction:: qteasy.filter_stock_codes

.. autofunction:: qteasy.filter_stocks

历史数据类HistoryPanel:

.. autoclass:: qteasy.HistoryPanel
    :members:

.. autofunction:: qteasy.get_history_data

.. autofunction:: qteasy.stack_dataframes

.. autofunction:: qteasy.dataframe_to_hp

Built-in Strategies
-------------------

.. autofunction:: qteasy.built_ins

.. autofunction:: qteasy.built_in_list

.. autofunction:: qteasy.built_in_strategies
