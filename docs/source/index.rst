.. qteasy documentation master file, created by
   sphinx-quickstart on Sun Nov 19 21:52:20 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

欢迎使用QTEASY文档!
=================

.. note::

   This project is under active development.

- Author: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `1.0.7`
- License: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

Introduction
============

QTEASY是为量化交易人员开发的一套量化交易策略开发工具包，基本功能如下：

1. 金融历史数据的获取、清洗、整理、可视化、本地存储查询及应用；支持多种数据存储方式，包括本地文件、MySQL数据库等，数据来源包括Tushare、EastMoney等
2. 投资交易策略的创建、回测、性能评价，并且通过定义策略的可调参数，提供多种优化算法实现交易策略的参数调优
3. 交易策略的部署、实盘运行、模拟交易结果、并跟踪记录交易日志、股票持仓、账户资金变化等信息

以下功能在开发计划中：

1. *提供常用的金融统计数据分析工具，用于数据分析、操作及可视化*
2. *与自动化交易系统连接、实现自动化交易*


Getting Started
===============

.. toctree::
   :maxdepth: 1
   :glob:

   getting_started

Tutorials
=========

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
========

.. toctree::
    :maxdepth: 1
    :glob:

    examples/*


API Reference
=============

.. toctree::
   :maxdepth: 1
   :glob:

   api_reference.md
   tutorials/Reference 01 - 内置交易策略的回测结果

Change Log
==========

.. toctree::
   :maxdepth: 1
   :glob:

   RELEASE_HISTORY


LICENSE
=======

.. license
   :doc: LICENSE

ABOUT
=====

.. toctree::
   :maxdepth: 1
   :glob:

   about

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
