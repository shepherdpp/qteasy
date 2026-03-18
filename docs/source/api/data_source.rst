历史数据的存储——DataSource对象
===============================================

DataSource 负责对接本地历史数据存储，可以管理基于文件的存储（如 csv/hdf/feather）
或基于数据库的存储（如 MySQL/MariaDB），对上层暴露统一的表结构与读取接口；数据的
下载与更新通常通过 ``qt.refill_data_source()`` 完成，而非由 DataSource 自动拉取。

.. autoclass:: qteasy.DataSource
    :members:
