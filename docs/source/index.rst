.. qteasy documentation master file, created by
   sphinx-quickstart on Sun Nov 19 21:52:20 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

欢迎使用QTEASY文档!
================================

.. note::

   This project is under active development.

- Author: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `1.0.19`
- License: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

Introduction
------------

QTEASY是为量化交易人员开发的一套量化交易策略开发工具包，基本功能如下：

1. 金融历史数据的获取、清洗、整理、可视化、本地存储查询及应用；支持多种数据存储方式，包括本地文件、MySQL数据库等，数据来源包括Tushare、EastMoney等
2. 投资交易策略的创建、回测、性能评价，并且通过定义策略的可调参数，提供多种优化算法实现交易策略的参数调优
3. 交易策略的部署、实盘运行、模拟交易结果、并跟踪记录交易日志、股票持仓、账户资金变化等信息

Why QTEASY?
-----------

使用QTEASY有哪些好处？

1. 数据下载、清洗、存储、查询，策略创建、回测、优化、实盘运行，一站式解决方案
2. 我的策略我做主，策略完全本地运行，本地数据回测，不依赖于网络平台，不受任何平台的限制
3. 提供大量内置交易策略，支持多个策略的组合，自定义组合公式，支持自定义交易策略
4. 可以设定可调参数优化策略性能，提供多种优化算法，包括网格搜索、随机搜索、遗传算法等
5. 回测速度快，精度高，多角度自定义交易费率和交易规则，支持多种回测结果的可视化

Getting Started
---------------

.. toctree::
   :maxdepth: 1
   :glob:

   getting_started

Tutorials
---------

.. toctree::
   :maxdepth: 1
   :glob:

   tutorials/Tutorial 01 - 系统基础配置
   tutorials/Tutorial 02 - 金融数据获取及管理
   tutorials/Tutorial 03 - 交易策略及回测基本操作
   tutorials/Tutorial 04 - 使用内置交易策略
   tutorials/Tutorial 05 - 创建自定义交易策略
   tutorials/Tutorial 06 - 交易策略的优化
   tutorials/Tutorial 07 - 交易策略的部署及运行
   tutorials/Tutorial 08 - 历史数据的操作和分析

Examples
--------

.. toctree::
    :maxdepth: 1
    :glob:

    tutorials/Reference 01 - 内置交易策略的回测结果
    examples/*


API Reference
-------------

.. toctree::
   :maxdepth: 1
   :glob:

   api_reference
   use_qteasy
   History_Data
   Built_In
   Strategies
   HistoryPanel
   Operators

Change Log
----------

.. toctree::
   :maxdepth: 1
   :glob:

   RELEASE_HISTORY


LICENSE
-------

.. license
   :doc: LICENSE

ABOUT
-----

.. toctree::
   :maxdepth: 1
   :glob:

   about

FAQ
---
.. toctree::
   :maxdepth: 1
   :glob:

   faq
