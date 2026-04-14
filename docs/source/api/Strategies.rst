交易策略基类
================

本页提供 Strategy 相关核心类的 API 自动文档入口。  
设计思路与使用教程请参考：

- 设计文档：``design/10-live-trading-s1.3-architecture.md``
- 策略管理文档：``manage_strategies/*``
- 实操教程：``tutorials/*``

BaseStrategy
----------------

.. autoclass:: qteasy.BaseStrategy
   :members: info, update_par_values, get_pars
   :show-inheritance:

GeneralStg
----------------

.. autoclass:: qteasy.GeneralStg
   :show-inheritance:

FactorSorter
----------------

.. autoclass:: qteasy.FactorSorter
   :show-inheritance:

RuleIterator
----------------

.. autoclass:: qteasy.RuleIterator
   :show-inheritance:

交易策略参数对象
====================

Parameter 用于定义策略可调参数的类型、范围与取值方式。

.. autoclass:: qteasy.Parameter
   :members: get_value, set_value, update_par_range
