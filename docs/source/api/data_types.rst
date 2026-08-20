数据类型与消费入口——DataType
===================================================

日常请把 DataType 当作**信息 ID**（字符串）：宽匹配名如 ``close``、``pe``，完整 id 如 ``close_E_d``。
按消费形状选用入口，而不是一律 ``get_history_data``：

- **History**（时间 × 标的）：``get_history_data`` / ``get_kline``
- **Reference**（仅时间）：``get_reference_data``（含 ``cn_gdp``、``close-000300.SH``）
- **Static**（仅标的）：``get_static_data``（如 ``industry``、``list_date``）

概念、四条工作路径、双 ID 与精选表见
:doc:`manage_data 章节「用稳定的信息 ID 取数」 <../manage_data/02. datatypes>`；
按业务浏览的完整内置清单见 :doc:`内置 DataType 完整清单 <../references/datatypes/index>`。

三入口（公开 API）
------------------

.. autofunction:: qteasy.get_history_data

.. autofunction:: qteasy.get_reference_data

.. autofunction:: qteasy.get_static_data

``get_kline`` 是标准 OHLCV 的语法糖，底层仍走 History 管线；签名见
:doc:`历史数据获取和管理 <history_data>`。

清单与检索
----------

``find_history_data`` 返回的结构化结果含 ``kind``、``usable_in``、``recommended_api``；
打印路径按行推荐入口，**不要**假定每一行都能 ``get_history_data``。

.. autofunction:: qteasy.datatypes.get_dtype_map

.. autofunction:: qteasy.find_history_data

``find_history_data`` 亦在 :doc:`历史数据获取和管理 <history_data>` 中列出。

高级：DataType 类
-----------------

专家层与内置策略可直接构造 ``DataType`` 对象；普通取数与策略声明优先使用字符串 ID。

.. autoclass:: qteasy.DataType
    :members:
    :exclude-members: _get_operation, _get_relations, _get_complex, _unsymbolised
    :special-members: __init__
