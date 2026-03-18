
交易策略类
================

在 qteasy 中，所有交易策略都基于 ``BaseStrategy`` 抽象基类：通过可调参数
（pars）、历史数据声明（data_types + window_length 等）以及 ``realize()`` 中
的交易逻辑生成不同风格的信号，最终由 Operator 按 PT/PS/VS 信号语义解析为具体
交易指令。更多关于 Strategy / Group / Operator 的架构与自定义策略教程，见设计
文档与 manage_strategies 系列文档。

.. autoclass:: qteasy.BaseStrategy
    :members:

三种交易策略类
-----------------------

.. autoclass:: qteasy.GeneralStg

.. autoclass:: qteasy.FactorSorter

.. autoclass:: qteasy.RuleIterator

交易策略的可调参数
-----------------------



.. autoclass:: qteasy.Parameter
    :members:
