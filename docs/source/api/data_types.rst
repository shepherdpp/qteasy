管理历史数据的类型——DataType
===================================================

``DataType`` 以「名称 + 频率 + 资产类型」三元组描述单一历史数据类型，是数据管线与策略声明历史数据需求时的统一语言。qteasy 预置了一千余种内置类型；日常取数通常通过 ``get_history_data(htype_names=...)`` / ``get_kline`` 引用类型 **name**，而不必每次手写 ``DataType(...)``。

概念、精选表与发现方式见 :doc:`manage_data 章节「以标准化方式从数据表中提取信息」 <../manage_data/02. datatypes>`；
按获取方式浏览的完整内置清单见 :doc:`内置 DataType 完整清单 <../references/datatypes/index>`。

清单与检索
----------

.. autofunction:: qteasy.datatypes.get_dtype_map

.. autofunction:: qteasy.find_history_data

``find_history_data`` 亦在 :doc:`历史数据获取和管理 <history_data>` 中列出；此处与 DataType 概念并列，便于对照清单使用。

DataType 类
-----------

.. autoclass:: qteasy.DataType
    :members:
    :exclude-members: _get_operation, _get_relations, _get_complex, _unsymbolised
    :special-members: __init__
