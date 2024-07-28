.. qteasy documentation master file, created by
   sphinx-quickstart on Sun Nov 19 21:52:20 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

欢迎使用 ``QTEASY`` 文档!
================================

.. image:: img/qteasy_logo_horizontal.png
    :width: 900px
    :align: center

.. note::

   目前 ``qteays`` 正处于密集开发测试阶段，软件中不免存在一些漏洞和bug，如果大家使用中出现问题，欢迎 `报告Issue`_ 或者提交 `新功能需求`_ 给我，也可以进入 `讨论区`_ 参与讨论。欢迎各位贡献代码！

.. _报告Issue: https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=bug-report---bug报告.md&title=
.. _新功能需求: https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=feature-request--功能需求.md&title=
.. _讨论区: https://github.com/shepherdpp/qteasy/discussions

- Author: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `1.2.15`
- License: BSD 3-Clause

Introduction
------------

``QTEASY`` 是为量化交易人员开发的一套量化交易策略开发工具包，基本功能如下：

1. 金融历史数据的获取、清洗、整理、可视化、本地存储查询及应用；支持多种数据存储方式，包括本地文件、MySQL数据库等，数据来源包括 ``Tushare`` 、 ``EastMoney`` 等
2. 投资交易策略的创建、回测、性能评价，并且通过定义策略的可调参数，提供多种优化算法实现交易策略的参数调优
3. 交易策略的部署、实盘运行、模拟交易结果、并跟踪记录交易日志、股票持仓、账户资金变化等信息

What Can You Do with ``QTEASY`` ?
-----------------------------

下载金融历史数据
~~~~~~~~~~~~~~~~~~~~

- 获取、清洗、本地存储大量金融历史数据
- 检索、处理、调用本地数据
- 本地金融数据可视化

.. image:: img/output_3_4.png
    :width: 900px
    :align: center

创建交易策略
~~~~~~~~~~~~~~~~~~~~

- 提供近七十种内置交易策略，可以直接搭积木式使用
- 快速创建自定义交易策略，灵活设置可调参数
- 交易策略的回测、优化、评价，可视化输出回测结果

.. image:: img/output_14_3.png
    :width: 900px
    :align: center

实盘交易模拟
~~~~~~~~~~~~~~~~~~~~

- 读取实时市场数据，实盘运行交易策略
- 生成交易信号，模拟交易结果
- 跟踪记录交易日志、股票持仓、账户资金变化等信息
- 随时查看交易过程，检查盈亏情况
- 手动控制交易进程、调整交易参数，手动下单

.. image:: examples/img/trader_app_1.png
    :width: 900px
    :align: center


.. image:: examples/img/trader_app_1.png
    :width: 900px
    :align: center


.. image:: examples/img/trader_app_light_theme.png
    :width: 900px
    :align: center


.. toctree::
   :caption: GETTING STARTED 快速入门
   :maxdepth: 1
   :glob:

   getting_started
   help
   roadmap.rst
   CONTRIBUTING
   CODE_OF_CONDUCT


.. toctree::
   :caption: TUTORIALS 使用教程
   :numbered: 2
   :maxdepth: 1
   :glob:

   tutorials/*


.. toctree::
    :caption: REFERENCES 参考文档
    :numbered: 2
    :maxdepth: 1
    :glob:

    references/*


.. toctree::
    :caption: EXAMPLES 自定义策略示例
    :numbered: 2
    :maxdepth: 1
    :glob:

    examples/*


.. toctree::
   :caption: API REFERENCE 参考
   :numbered: 1
   :maxdepth: 1
   :glob:

   api/api_reference.rst
   api/history_data.rst
   api/history_data_types.rst
   api/built_in_strategies.rst
   api/Strategies.rst
   api/use_qteasy.rst


.. toctree::
   :caption: RELEASE HISTORY 发行版本历史
   :maxdepth: 1
   :glob:

   RELEASE_HISTORY


.. toctree::
   :caption: LICENSE

   LICENSE


.. toctree::
   :caption: ABOUT 关于
   :maxdepth: 1
   :glob:

   about

.. toctree::
   :caption: FAQ 常见问题
   :maxdepth: 1
   :glob:

   faq

