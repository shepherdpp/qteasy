# coding=utf-8
# ======================================
# File:     datatable.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-06
# Desc:
#   Definition of data related variables
# all data tables, table masters,
# connection APIs and mapping from data
# types to data tables.
# ======================================

import warnings
import pandas as pd

from functools import lru_cache

from .utilfuncs import (
    str_to_list,
)


AVAILABLE_DATA_FILE_TYPES = ['csv', 'hdf', 'hdf5', 'feather', 'fth']
AVAILABLE_CHANNELS = ['df', 'csv', 'excel', 'tushare', 'akshare']
ADJUSTABLE_PRICE_TYPES = ['open', 'high', 'low', 'close']
TABLE_USAGES = [
    'sys',   # 系统数据表，用于存储系统数据
    'cal',   # 交易日历，用于存储交易状态
    'basics',   # 基本信息表，用于存储与个股有关的，但与时间无关的基本特征信息
    'data',   # 数据表，用于存储与个股有关的，且随时间连续变化的变量，连续变化的频率可以有多种
    'mins',   # 使用方法等同于data，用于存储分钟线数据
    'adj',   # 使用方法等同于data，复权系数，用于存储复权因子等数据，
    'events',  # 事件表，用于存储与个股有关，但是不定期发生的事件数据，数据是稀疏的，且这些数据对个股的影响是瞬时的
    'status',  # 状态变化表，用于存储与个股有关，不定期发生的状态的改变，数据也是稀疏的，但状态可以持续一段时间，该表中存储状态的起止时间
    'comp',  # 成分表，用于存储指数、基金、期货等金融产品的成分以及比例数据
    'report',   # 相当于事件表，用于存储公司财务报表数据
    'reference',  # 参考数据表，用于存储与任何特定资产都无关的参考数据，如宏观经济数据等，使用方法同data
]

"""
量化投资研究所需用到各种金融数据，Qteasy通过DataTypes和DataSource两个类提供了管理金融数据的方式，同时又通过
不同的DataChannel来提供不同的数据获取渠道，其运转方式如下：

-----------------------------------数据获取-----------------------------------
1, 从tushare或akshare等数据渠道获取数据
2, 所有数据进行统一清洗、去重、整理为统一的数据格式，修改为统一的数据表结构
---------------------------------数据存储及管理--------------------------------
3, 将统一的数据表存储在本地，以csv、hdf5等多种文件形式存储
4, 提供统一的数据访问接口，不同格式的数据文件以统一的方式访问，支持数据的增删改查
5, 用户可以自定义数据表，自定义数据表的结构和操作方式与内置数据表一致
-----------------------------------数据使用-----------------------------------
6, 用户通过引用数据的类型名称（htype）来获取数据，不同的数据类型对应不同的数据表或获取方式
7, 简单的数据类型直接引用某个数据表中的一列数据
8, 复杂的数据类型，需要通过表内查询获取，或者多表关联获取
9, 每种数据类型的获取方式内置在DataType类中，数据的获取接口和返回值都是统一的
10, 用户可以自定义数据类型，自定义数据类型的获取方式由用户定义，接口和返回值必须与内置数据类型一致

DataTypes：定义了所有的金融数据类型，包括历史数据、基本面数据、事件数据等，每种数据类型都有一个唯一的ID
DataSource：定义了所有的数据表，每种数据类型都存储在一个数据表中，数据表的结构由TABLE_MASTER和TABLE_SCHEMAS定义

数据表是金融数据在本地存储的逻辑结构，本地的金融数据包含若干张数据表，每张表内保存一类数据
数据表可以在本地以csv等文件形式，也可以以MySQL数据库的形式存储，不论存储方式如何，操作接口都是一致的，只是性能有区别

这里定义了qteasy内置的数据表，数据表的结构由两个字典（表）来定义：

完整的数据结构由三个字典（表）来定义：
TABLE_MASTER:           定义数据表的基本属性和下载API来源（目前仅包括tushare，未来会添加其他API)
TABLE_SCHEMAS:          定义数据表的表结构，包括每一列的名称、数据类型、主键以及每一列的说明


1, TABLE_MASTER

table source mapping定义了一张数据表的基本属性以及数据来源： 
table_name(key):            数据表的名称（主键）自定义表名称不能与内置表名称重复
---------------------------------------------------------------------------------------------------------
1, schema:                  数据表的结构名称，根据该名称在TABLE_STRUCTUERS表中可以查到表格包含的所有列、主键、数据类
                            型和详情描述
                            数据表的数据结构存储在不同的数据结构表中，许多表拥有相同的数据结构

2, desc:                    数据表的中文描述

3, table_usage:             数据表的用途，用于筛选不同的数据表:
                            -  sys: 系统数据表，包含系统运行所需的数据
                            -  cal: 交易日历表，包含交易日历数据
                            -  basics: 基本面数据表，包含资产基本信息
                            -  data: 历史数据表，包含历史价格、成交量等数据，仅限频率低于或等于日线的数据
                            -  adj: 复权数据表，包含复权价格因子等数据
                            -  events: 事件数据表，包含与资产相关的不定期事件数据，如公司更名、分红停牌等
                            -  comp: 成分数据表，包含指数、基金、期货等金融产品的成分数据
                            -  report: 财务报表数据表，包含公司财务报表数据
                            -  mins: 分钟数据表，包含分钟线数据
                            -  reference: 参考数据表，包含各种与任何特定资产都无关的参考数据，如宏观经济数据等

4, asset_type:              表内数据对应的资产类型，none表示不对应任何特定资产类型

5, freq:                    表内数据的频率，如分钟、日、周等
                            设置为'D'、'W'等，用于筛选不同的数据表
                            
6, index_column:            数据表的索引列，除了数据表的Primary Key以外需要额外创建的索引列, 使用mysql数据库存储
                            数据时设置索引可以大大提高查询性能，对于文件存储形式无效
7, partition_column:        数据表的分区列，使用mysql数据库存储时，使用KEY(column)分区方式，对于文件存储形式无效
8, partitions:              数据表的分区数量，使用mysql数据库存储时，使用KEY(column)分区方式，对于文件存储形式无效
---------------------------------------------------------------------------------------------------------

2, TABLE_SCHEMAS:
Table schema表定义了数据表的数据结构：
table_schema_name:          数据结构名称（主键）
---------------------------------------------------------------------------------------------------------
columns:                    数据列名称

dtypes:                     数据列的数据类型，包括：
                            varchar(N) - 长度不超过N的字符串类型
                            float:
                            double:
                            date:
                            int:

remarks:                    数据列含义说明

prime_keys:                 一个列表，包含一个或多个整数，它们代表的列是这个表的数据主键
---------------------------------------------------------------------------------------------------------
"""

# Table_masters，用于存储表的基本信息
TABLE_MASTER_COLUMNS = [
    'schema',  # 1, 数据表schema
    'desc',  # 2, 数据表描述
    'table_usage',  # 3, 数据表用途
    'asset_type',  # 4, 资产类型
    'freq',  # 5, 数据频率
    'index_column',  # 6, 数据表index column信息，除了数据表的Primary Key以外需要额外创建的索引列
    'partition_column',  # 7, 数据表分区列名
    'partitions',  # 8, 数据表分区数量
]
TABLE_MASTERS = {

    'sys_op_live_accounts':
        ['sys_op_live_accounts', '实盘运行基本信息主记录表', 'sys', '', '', '', '', ''],

    'sys_op_positions':
        ['sys_op_positions', '实盘运行持仓记录', 'sys', '', '', '', '', ''],

    'sys_op_trade_orders':
        ['sys_op_trade_orders', '实盘运行交易订单记录表', 'sys', '', '', '', '', ''],

    'sys_op_trade_results':
        ['sys_op_trade_results', '实盘运行交易结果记录表', 'sys', '', '', '', '', ''],

    'trade_calendar':
        ['trade_calendar', '交易日历', 'cal', 'none', 'none', '', '', ''],

    'hk_trade_calendar':
        ['foreign_trade_cal', '港股交易日历', 'cal', 'none', 'none', '', '', ''],

    'us_trade_calendar':
        ['foreign_trade_cal', '美股交易日历', 'cal', 'none', 'none', '', '', ''],

    'stock_basic':
        ['stock_basic', '股票基本信息', 'basics', 'E', 'none', '', '', ''],

    'hk_stock_basic':
        ['hk_stock_basic', '港股基本信息', 'not_implemented', 'HK', 'none', '', '', ''],

    'us_stock_basic':
        ['us_stock_basic', '美股基本信息', 'not_implemented', 'US', 'none', '', '', ''],

    'stock_names':  # Complete, 股票名称变更
        ['name_changes', '股票名称变更', 'events', 'E', 'none', '', '', ''],

    'stock_company':
        ['stock_company', '上市公司基本信息', 'basics', 'E', 'none', '', '', ''],

    'stk_managers':
        ['stk_managers', '上市公司管理层', 'events', 'E', 'd', '', '', ''],

    'new_share':
        ['new_share', 'IPO新股列表', 'basics', 'E', 'd', '', '', ''],

    'money_flow':  # New, 个股资金流向!
        ['money_flow', '资金流向', 'data', 'E', 'd', '', '', ''],

    'stock_limit':  # New, 涨跌停价格!
        ['stock_limit', '涨跌停价格', 'data', 'E,FD', 'd', '', '', ''],

    'stock_suspend':  # New, 停复牌信息!
        ['stock_suspend', '停复牌信息', 'events', 'E', 'd', '', '', ''],

    'hs_money_flow':  # New, 沪深股通资金流向!
        ['hs_money_flow', '沪深股通资金流向', 'reference', 'none', 'd', '', '', ''],

    'hs_top10_stock':  # New, 沪深股通十大成交股!
        ['hs_top10_stock', '沪深股通十大成交股', 'events', 'E', 'd', '', '', ''],

    'hk_top10_stock':  # New, 港股通十大成交股!
        ['hk_top10_stock', '港股通十大成交股', 'events', 'E', 'd', '', '', ''],

    'index_basic':
        ['index_basic', '指数基本信息', 'basics', 'IDX', 'none', '', '', ''],

    'fund_basic':
        ['fund_basic', '基金基本信息', 'basics', 'FD', 'none', '', '', ''],

    'future_basic':
        ['future_basic', '期货基本信息', 'basics', 'FT', 'none', '', '', ''],

    'opt_basic':
        ['opt_basic', '期权基本信息', 'basics', 'OPT', 'none', '', '', ''],

    'ths_index_basic':  # New, 同花顺指数基本信息
        ['ths_index_basic', '同花顺指数基本信息', 'basics', 'THS', 'none', '', '', ''],

    'sw_industry_basic':  # New, 申万行业分类
        ['sw_industry_basic', '申万行业分类', 'basics', 'IDX', 'none', '', '', ''],

    'stock_1min':
        ['min_bars', '股票分钟K线行情', 'mins', 'E', '1min', '', 'ts_code', '30'],  # 10

    'stock_5min':
        ['min_bars', '股票5分钟K线行情', 'mins', 'E', '5min', '', 'ts_code', '10'],

    'stock_15min':
        ['min_bars', '股票15分钟K线行情', 'mins', 'E', '15min', '', 'ts_code', '10'],  # 5

    'stock_30min':
        ['min_bars', '股票30分钟K线行情', 'mins', 'E', '30min', '', 'ts_code', '5'],  # 5

    'stock_hourly':
        ['min_bars', '股票60分钟K线行情', 'mins', 'E', 'h', '', 'ts_code', '5'],  # 5

    'stock_daily':
        ['bars', '股票日线行情', 'data', 'E', 'd', '', '', ''],

    'stock_weekly':
        ['bars', '股票周线行情', 'data', 'E', 'w', '', '', ''],

    'stock_monthly':
        ['bars', '股票月线行情', 'data', 'E', 'm', '', '', ''],

    'hk_stock_daily':
        ['hk_daily', '港股日线行情', 'not_implemented', 'HK', 'd', '', '', ''],

    'us_stock_daily':
        ['us_daily', '美股日线行情', 'not_implemented', 'US', 'd', '', '', ''],

    'index_1min':
        ['min_bars', '指数分钟K线行情', 'mins', 'IDX', '1min', '', 'ts_code', '30'],  # 30

    'index_5min':
        ['min_bars', '指数5分钟K线行情', 'mins', 'IDX', '5min', '', 'ts_code', '10'],  # 10

    'index_15min':
        ['min_bars', '指数15分钟K线行情', 'mins', 'IDX', '15min', '', 'ts_code', '10'],  # 10

    'index_30min':
        ['min_bars', '指数30分钟K线行情', 'mins', 'IDX', '30min', '', 'ts_code', '5'],  # 5

    'index_hourly':
        ['min_bars', '指数60分钟K线行情', 'mins', 'IDX', 'h', '', 'ts_code', '5'],  # 5

    'index_daily':
        ['bars', '指数日线行情', 'data', 'IDX', 'd', '', '', ''],

    'index_weekly':
        ['bars', '指数周线行情', 'data', 'IDX', 'w', '', '', ''],

    'index_monthly':
        ['bars', '指数月度行情', 'data', 'IDX', 'm', '', '', ''],

    'ths_index_daily':  # New, 同花顺行业指数日线行情!
        ['ths_index_daily', '同花顺行业指数日线行情', 'data', 'THS', 'd', '', '', ''],

    'ths_index_weight':  # New, 同花顺行业指数成分股权重!
        ['ths_index_weight', '同花顺行业指数成分股权重', 'comp', 'THS', 'd', '', '', ''],

    'ci_index_daily':  # New, 中信指数日线行情!
        ['ci_index_daily', '中证指数日线行情', 'reference', 'none', 'd', '', '', ''],

    'sw_index_daily':  # New, 申万指数日线行情!
        ['sw_index_daily', '申万指数日线行情', 'reference', 'none', 'd', '', '', ''],

    'global_index_daily':  # New, 全球指数日线行情!
        ['global_index_daily', '全球指数日线行情', 'reference', 'none', 'd', '', '', ''],

    'fund_1min':
        ['min_bars', '场内基金分钟K线行情', 'mins', 'FD', '1min', '', 'ts_code', '30'],

    'fund_5min':
        ['min_bars', '场内基金5分钟K线行情', 'mins', 'FD', '5min', '', 'ts_code', '10'],

    'fund_15min':
        ['min_bars', '场内基金15分钟K线行情', 'mins', 'FD', '15min', '', 'ts_code', '10'],

    'fund_30min':
        ['min_bars', '场内基金30分钟K线行情', 'mins', 'FD', '30min', '', 'ts_code', '5'],

    'fund_hourly':
        ['min_bars', '场内基金60分钟K线行情', 'mins', 'FD', 'h', '', 'ts_code', '5'],

    'fund_daily':
        ['bars', '场内基金每日K线行情', 'data', 'FD', 'd', '', '', ''],

    'fund_weekly':
        ['bars', '场内基金周K线行情', 'data', 'FD', 'w', '', '', ''],

    'fund_monthly':
        ['bars', '场内基金月K线行情', 'data', 'FD', 'm', '', '', ''],

    'fund_nav':
        ['fund_nav', '场外基金每日净值', 'data', 'FD', 'd', '', '', ''],

    'fund_share':
        ['fund_share', '基金份额', 'data', 'FD', 'none', '', '', ''],

    'fund_manager':
        ['fund_manager', '基金经理', 'events', 'FD', 'none', '', '', ''],

    'future_mapping':  # New, 期货合约映射表!
        ['future_mapping', '期货合约映射表', 'data', 'FT', 'd', '', '', ''],

    'future_1min':  # future_xmin 表应该通过trade_time(start/end)来切表索引，而不是通过table_index
        ['future_mins', '期货分钟K线行情', 'mins', 'FT', '1min', '', 'ts_code', '30'],

    'future_5min':
        ['future_mins', '期货5分钟K线行情', 'mins', 'FT', '5min', '', 'ts_code', '10'],

    'future_15min':
        ['future_mins', '期货15分钟K线行情', 'mins', 'FT', '15min', '', 'ts_code', '10'],

    'future_30min':
        ['future_mins', '期货30分钟K线行情', 'mins', 'FT', '30min', '', 'ts_code', '5'],

    'future_hourly':
        ['future_mins', '期货60分钟K线行情', 'mins', 'FT', 'h', '', 'ts_code', '5'],

    'future_daily':
        ['future_daily', '期货每日行情', 'data', 'FT', 'd', '', '', ''],

    'future_weekly':  # New, 期货周线行情!
        ['future_daily', '期货周线行情', 'data', 'FT', 'w', '', '', ''],

    'future_monthly':  # New, 期货月线行情!
        ['future_daily', '期货月线行情', 'data', 'FT', 'm', '', '', ''],

    'options_1min':  # options_xmin 表应该通过trade_time(start/end)来切表索引，而不是通过table_index
        ['min_bars', '期权分钟K线行情', 'mins', 'OPT', '1min', '', 'ts_code', '30'],

    'options_5min':
        ['min_bars', '期权5分钟K线行情', 'mins', 'OPT', '5min', '', 'ts_code', '10'],

    'options_15min':
        ['min_bars', '期权15分钟K线行情', 'mins', 'OPT', '15min', '', 'ts_code', '10'],

    'options_30min':
        ['min_bars', '期权30分钟K线行情', 'mins', 'OPT', '30min', '', 'ts_code', '5'],

    'options_hourly':
        ['min_bars', '期权60分钟K线行情', 'mins', 'OPT', 'h', '', 'ts_code', '5'],

    'options_daily':
        ['options_daily', '期权每日行情', 'data', 'OPT', 'd', '', '', ''],

    'stock_adj_factor':
        ['adj_factors', '股票价格复权系数', 'adj', 'E', 'd', '', '', ''],

    'fund_adj_factor':
        ['adj_factors', '基金价格复权系数', 'adj', 'FD', 'd', '', '', ''],

    'stock_indicator':
        ['stock_indicator', '股票技术指标', 'data', 'E', 'd', '', '', ''],

    'stock_indicator2':
        ['stock_indicator2', '股票技术指标备用表', 'data', 'E', 'd', '', '', ''],

    'hk_stock_indicator':
        ['hk_us_indicators', '港股技术指标', 'not_implemented', 'HK', 'd', '', '', ''],

    'us_stock_indicator':
        ['hk_us_indicators', '美股技术指标', 'not_implemented', 'US', 'd', '', '', ''],

    'index_indicator':
        ['index_indicator', '指数关键指标', 'data', 'IDX', 'd', '', '', ''],

    'index_weight':
        ['index_weight', '指数成分', 'comp', 'IDX', 'd', '', '', ''],

    'income':
        ['income', '上市公司利润表', 'report', 'E', 'q', '', '', ''],

    'balance':
        ['balance', '上市公司资产负债表', 'report', 'E', 'q', '', '', ''],

    'cashflow':
        ['cashflow', '上市公司现金流量表', 'report', 'E', 'q', '', '', ''],

    'financial':
        ['financial', '上市公司财务指标', 'report', 'E', 'q', '', '', ''],

    'forecast':
        ['forecast', '上市公司财报预测', 'report', 'E', 'q', '', '', ''],

    'express':
        ['express', '上市公司财报快报', 'report', 'E', 'q', '', '', ''],

    'dividend':  # New, 分红送股!
        ['dividend', '分红送股', 'events', 'E', 'd', '', '', ''],

    'top_list':  # New, 龙虎榜交易明细!
        ['top_list', '龙虎榜交易明细', 'events', 'E', 'd', '', '', ''],

    'top_inst':  # New, 龙虎榜机构交易明细!
        ['top_inst', '龙虎榜机构交易明细', 'events', 'E', 'd', '', '', ''],

    'sw_industry_detail':  # New, 申万行业分类明细(成分股)!
        ['sw_industry_detail', '申万行业分类明细', 'comp', 'IDX', 'none', '', '', ''],

    'block_trade':  # New, 大宗交易!
        ['block_trade', '大宗交易', 'events', 'E', 'd', '', '', ''],

    'stock_holder_trade':  # New, 股东交易（股东增减持）!
        ['stock_holder_trade', '股东交易', 'events', 'E', 'd', '', '', ''],

    'margin':  # New, 融资融券交易概况!
        ['margin', '融资融券交易概况', 'reference', 'none', 'd', '', '', ''],

    'margin_detail':  # New, 融资融券交易明！
        ['margin_detail', '融资融券交易明细', 'events', 'E', 'd', '', '', ''],

    'shibor':
        ['shibor', '上海银行间行业拆放利率(SHIBOR)', 'reference', 'none', 'd', '', '', ''],

    'libor':
        ['libor', '伦敦银行间行业拆放利率(LIBOR)', 'reference', 'none', 'd', '', '', ''],

    'hibor':
        ['hibor', '香港银行间行业拆放利率(HIBOR)', 'reference', 'none', 'd', '', '', ''],

    'wz_index':  # New, 温州民间借贷指数!
        ['wz_index', '温州民间借贷指数', 'reference', 'none', 'd', '', '', ''],

    'gz_index':  # New, 广州民间借贷指数!
        ['gz_index', '广州民间借贷指数', 'reference', 'none', 'd', '', '', ''],

    'cn_gdp':  # New, 国内生产总值季度数据!
        ['cn_gdp', '国内生产总值年度数据', 'reference', 'none', 'q', '', '', ''],

    'cn_cpi':  # New, 居民消费价格指数月度数据!
        ['cn_cpi', '居民消费价格指数月度数据', 'reference', 'none', 'm', '', '', ''],

    'cn_ppi':  # New, 工业品出厂价格指数月度数据!
        ['cn_ppi', '工业品出厂价格指数月度数据', 'reference', 'none', 'm', '', '', ''],

    'cn_money':  # New, 中国货币供应量!
        ['cn_money', '中国货币供应量', 'reference', 'none', 'm', '', '', ''],

    'cn_sf':  # New, 中国社会融资规模月度数据!
        ['cn_sf', '中国社会融资规模月度数据', 'reference', 'none', 'm', '', '', ''],

    'cn_pmi':  # New, 采购经理人指数月度数据!
        ['cn_pmi', '采购经理人指数月度数据', 'reference', 'none', 'm', '', '', ''],

}
# Table schema，定义所有数据表的列名、数据类型、限制、主键以及注释，用于定义数据表的结构
TABLE_SCHEMA = {

    # TODO: for v1.5:
    #  在live_account_master表中增加运行基本设置的字段如交易柜台连接设置、log设置、交易时间段设置、用户权限设置等，动态修改
    'sys_op_live_accounts':  # 实盘交易账户表
        {'columns':    ['account_id', 'user_name', 'created_time', 'cash_amount', 'available_cash', 'total_invest'],
         'dtypes':     ['int', 'varchar(20)', 'datetime', 'double', 'double', 'double'],
         'remarks':    ['运行账号ID', '用户名', '创建时间', '现金总额', '可用现金总额', '总投资额'],
         'prime_keys': [0],
         },

    'sys_op_positions':  # 实盘持仓表
        {'columns':    ['pos_id', 'account_id', 'symbol', 'position', 'qty', 'available_qty', 'cost'],
         'dtypes':     ['int', 'int', 'varchar(20)', 'varchar(5)', 'double', 'double', 'double'],
         'remarks':    ['持仓ID', '运行账号ID', '资产代码', '持仓类型(多long/空short)', '持仓数量', '可用数量',
                        '持仓成本'],
         'prime_keys': [0],
         },

    'sys_op_trade_orders':  # 实盘交易订单表
        {'columns':    ['order_id', 'pos_id', 'direction', 'order_type', 'qty', 'price',
                        'submitted_time', 'status'],
         'dtypes':     ['int', 'int', 'varchar(10)', 'varchar(8)', 'double', 'double',
                        'datetime', 'varchar(15)'],
         'remarks':    ['交易订单ID', '持仓ID', '交易方向(买Buy/卖Sell)', '委托类型(市价单/限价单)', '委托数量',
                        '委托报价',
                        '委托时间', '状态(提交submitted/部分成交partial-filled/全部成交filled/取消canceled)'],
         'prime_keys': [0]
         },

    'sys_op_trade_results':  # 实盘交易结果表
        {'columns':    ['result_id', 'order_id', 'filled_qty', 'price', 'transaction_fee', 'execution_time',
                        'canceled_qty', 'delivery_amount', 'delivery_status'],
         'dtypes':     ['int', 'int', 'double', 'double', 'double', 'datetime',
                        'double', 'double', 'varchar(2)'],
         'remarks':    ['交易结果ID', '交易订单ID', '成交数量', '成交价格', '交易费用', '成交时间',
                        '取消交易数量', '交割数量(现金或证券)', '交割状态{ND, DL}'],
         'prime_keys': [0],
         },

    'trade_calendar':  # 交易日历表
        {'columns':    ['cal_date', 'exchange', 'is_open', 'pretrade_date'],
         'dtypes':     ['date', 'varchar(9)', 'tinyint', 'date'],
         'remarks':    ['日期', '交易所', '是否交易', '上一交易日'],
         'prime_keys': [0, 1]
         },

    'foreign_trade_cal':  # 国外股市交易日历表
        {'columns':    ['cal_date', 'is_open', 'pretrade_date'],
         'dtypes':     ['date', 'tinyint', 'date'],
         'remarks':    ['日期', '是否交易', '上一交易日'],
         'prime_keys': [0]
         },

    'stock_basic':  # 股票基本信息表
        {'columns':    ['ts_code', 'symbol', 'name', 'area', 'industry', 'fullname',
                        'enname', 'cnspell', 'market', 'exchange', 'curr_type', 'list_status',
                        'list_date', 'delist_date', 'is_hs'],
         'dtypes':     ['varchar(9)', 'varchar(6)', 'varchar(20)', 'varchar(10)', 'varchar(10)', 'varchar(50)',
                        'varchar(120)', 'varchar(40)', 'varchar(6)', 'varchar(6)', 'varchar(6)', 'varchar(4)',
                        'date', 'date', 'varchar(2)'],
         'remarks':    ['证券代码', '股票代码', '股票名称', '地域', '所属行业', '股票全称',
                        '英文全称', '拼音缩写', '市场类型', '交易所代码', '交易货币', '上市状态',
                        '上市日期', '退市日期', '是否沪深港通'],
         'prime_keys': [0]
         },

    'hk_stock_basic':  # 港股基本信息表
        {'columns':    ['ts_code', 'name', 'fullname', 'enname', 'cn_spell', 'market',
                        'list_status', 'list_date', 'delist_date', 'trade_unit', 'isin', 'curr_type'],
         'dtypes':     ['varchar(20)', 'varchar(40)', 'text', 'varchar(80)', 'varchar(20)', 'varchar(6)',
                        'varchar(6)', 'datetime', 'datetime', 'float', 'varchar(16)', 'varchar(6)'],
         'remarks':    ['股票代码', '股票简称', '公司全称', '英文名称', '拼音', '市场类别',
                        '上市状态', '上市日期', '退市日期', '交易单位', 'ISIN代码', '货币代码'],
         'prime_keys': [0]
         },

    'us_stock_basic':  # 美股基本信息表
        {'columns':    ['ts_code', 'name', 'enname', 'classify',
                        'list_date', 'delist_date'],
         'dtypes':     ['varchar(20)', 'varchar(40)', 'varchar(80)', 'varchar(6)',
                        'datetime', 'datetime'],
         'remarks':    ['美股代码', '中文名称', '英文名称', '分类:ADR/GDR/EQT',
                        '上市日期', '退市日期'],
         'prime_keys': [0]
        },

    'name_changes':  # 股票名称变更表
        {'columns':    ['ts_code', 'start_date', 'name', 'end_date', 'ann_date', 'change_reason'],
         'dtypes':     ['varchar(9)', 'date', 'varchar(8)', 'date', 'date', 'text'],
         'remarks':    ['证券代码', '开始日期', '证券名称', '结束日期', '公告日期', '变更原因'],
         'prime_keys': [0, 1]
         },

    'stock_company':  # 上市公司基本信息表
        {'columns':    ['ts_code', 'exchange', 'chairman', 'manager', 'secretary',
                        'reg_capital', 'setup_date', 'province', 'city', 'introduction',
                        'website', 'email', 'office', 'employees', 'main_business', 'business_scope'],
         'dtypes':     ['varchar(10)', 'varchar(10)', 'varchar(48)', 'varchar(48)', 'varchar(48)',
                        'float', 'date', 'varchar(20)', 'varchar(20)', 'text',
                        'varchar(75)', 'text', 'text', 'int', 'text', 'text'],
         'remarks':    ['股票代码', '交易所代码', '法人代表', '总经理', '董秘',
                        '注册资本', '注册日期', '所在省份', '所在城市', '公司介绍',
                        '公司主页', '电子邮件', '办公室地址', '员工人数', '主要业务及产品', '经营范围'],
         'prime_keys': [0]
         },

    'stk_managers':  # 上市公司管理层表 -- REFINE!
        {'columns':    ['ts_code', 'ann_date', 'name', 'gender', 'lev',
                        'title', 'edu', 'national', 'birthday', 'begin_date',
                        'end_date', 'resume'],
         'dtypes':     ['varchar(10)', 'date', 'varchar(48)', 'varchar(10)', 'varchar(48)',
                        'varchar(48)', 'varchar(30)', 'varchar(30)', 'varchar(10)', 'varchar(10)',
                        'varchar(10)', 'text'],
         'remarks':    ['TS股票代码', '公告日期', '姓名', '性别', '岗位类别',
                        '岗位', '学历', '国籍', '出生年月', '上任日期',
                        '离任日期', '个人简历'],
         'prime_keys': [0, 1, 2]
         },

    'new_share':  # IPO新股列表
        {'columns':     ['ts_code', 'sub_code', 'name', 'ipo_date', 'issue_date',
                         'amount', 'market_amount', 'price', 'pe', 'limit_amount',
                         'funds', 'ballot'],
         'dtypes':      ['varchar(20)', 'varchar(20)', 'varchar(50)', 'date', 'date',
                         'float', 'float', 'float', 'float', 'float',
                         'float', 'float'],
         'remarks':     ['TS股票代码', '申购代码', '名称', '上网发行日期', '上市日期',
                         '发行总量（万股）', '上网发行总量（万股）', '发行价格', '市盈率', '个人申购上限（万股）',
                         '募集资金（亿元）', '中签率'],
         'prime_keys':  [0]
         },

    'money_flow':  # New, 个股资金流向!
        {'columns':     ["ts_code", "trade_date", "buy_sm_vol", "buy_sm_amount", "sell_sm_vol", "sell_sm_amount",
                         "buy_md_vol", "buy_md_amount", "sell_md_vol", "sell_md_amount", "buy_lg_vol", "buy_lg_amount",
                         "sell_lg_vol", "sell_lg_amount", "buy_elg_vol", "buy_elg_amount", "sell_elg_vol",
                         "sell_elg_amount", "net_mf_vol", "net_mf_amount"],
         'dtypes':      ["varchar(10)", "date", "int", "float", "int", "float",
                         "int", "float", "int", "float", "int", "float",
                         "int", "float", "int", "float", "int",
                         "float", "int", "float"],
         'remarks':     ["证券代码", "交易日期", "小单买入量（手）", "小单买入金额（万元）", "小单卖出量（手）", "小单卖出金额（万元）",
                         "中单买入量（手）", "中单买入金额（万元）", "中单卖出量（手）", "中单卖出金额（万元）", "大单买入量（手）", "大单买入金额（万元）",
                         "大单卖出量（手）", "大单卖出金额（万元）", "特大单买入量（手）", "特大单买入金额（万元）", "特大单卖出量（手）",
                         "特大单卖出金额（万元）", "净流入量（手）", "净流入额（万元）"],
         'prime_keys':  [0, 1]
         },

    'stock_limit':  # New, 涨跌停价格!
        {'columns':     ["ts_code", "trade_date", "pre_close", "up_limit", "down_limit"],
         'dtypes':      ["varchar(10)", "date", "float", "float", "float"],
         'remarks':     ["TS股票代码", "交易日期", "昨日收盘价", "涨停价", "跌停价"],
         'prime_keys':  [0, 1]
         },

    'stock_suspend':  # New, 停复牌信息!
        {'columns':     ["ts_code", "trade_date", "suspend_timing", "suspend_type"],
         'dtypes':      ["varchar(10)", "date", "varchar(40)", "varchar(2)"],
         'remarks':     ["证券代码", "停复牌日期", "日内停牌时间段", "停复牌类型：S-停牌，R-复牌"],
         'prime_keys':  [0, 1]
         },

    'hs_money_flow':  # New, 沪深股通资金流向!
        {'columns':     ["trade_date", "ggt_ss", "ggt_sz", "hgt", "sgt", "north_money",
                         "south_money"],
         'dtypes':      ["date", "float", "float", "float", "float", "float",
                         "float"],
         'remarks':     ["交易日期", "港股通（上海）", "港股通（深圳）", "沪股通（百万元）", "深股通（百万元）", "北向资金（百万元）",
                         "南向资金（百万元）"],
         'prime_keys':  [0]
         },

    'hs_top10_stock':  # New, 沪深股通十大成交股!
        {'columns':     ["ts_code", "trade_date", "name", "close", "change", "rank", "market_type", "amount",
                         "net_amount", "buy", "sell"],
         'dtypes':      ["varchar(10)", "date", "varchar(10)", "float", "float", "int", "varchar(3)", "float",
                         "float", "float", "float"],
         'remarks':     ["证券代码", "交易日期", "股票名称", "收盘价", "涨跌额", "资金排名", "市场类型（1：沪市 3：深市）", "成交金额（元）",
                         "净成交金额（元）", "买入金额（元）", "卖出金额（元）"],
         'prime_keys':  [0, 1]
         },

    'hk_top10_stock':  # New, 港股通十大成交股!
        {'columns':     ["ts_code", "trade_date", "name", "close", "p_change", "rank", "market_type",
                         "amount", "net_amount", "sh_amount", "sh_net_amount", "sh_buy", "sh_sell",
                         "sz_amount", "sz_net_amount", "sz_buy", "sz_sell"],
         'dtypes':      ["varchar(10)", "date", "varchar(10)", "float", "float", "varchar(10)", "varchar(4)",
                         "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float"],
         'remarks':     ["证券代码", "交易日期", "股票名称", "收盘价", "涨跌幅", "资金排名", "市场类型 2：港股通（沪） 4：港股通（深）",
                         "累计成交金额（元）", "净买入金额（元）", "沪市成交金额（元）", "沪市净买入金额（元）", "沪市买入金额（元）", "沪市卖出金额",
                         "深市成交金额（元）", "深市净买入金额（元）", "深市买入金额（元）", "深市卖出金额（元）"],
         'prime_keys':  [0, 1]
         },

    'index_basic':  # 指数基本信息表
        {'columns':    ['ts_code', 'name', 'fullname', 'market', 'publisher',
                        'index_type', 'category', 'base_date', 'base_point', 'list_date', 'weight_rule',
                        'desc', 'exp_date'],
         'dtypes':     ['varchar(24)', 'varchar(80)', 'varchar(80)', 'varchar(8)', 'varchar(30)',
                        'varchar(30)', 'varchar(6)', 'date', 'float', 'date', 'text',
                        'text', 'date'],
         'remarks':    ['证券代码', '简称', '指数全称', '市场', '发布方',
                        '指数风格', '指数类别', '基期', '基点', '发布日期', '加权方式',
                        '描述', '终止日期'],
         'prime_keys': [0]
         },

    'fund_basic':  # 基金基本信息表
        {'columns':    ['ts_code', 'name', 'management', 'custodian', 'fund_type', 'found_date',
                        'due_date', 'list_date', 'issue_date', 'delist_date', 'issue_amount', 'm_fee',
                        'c_fee', 'duration_year', 'p_value', 'min_amount', 'exp_return', 'benchmark',
                        'status', 'invest_type', 'type', 'trustee', 'purc_startdate', 'redm_startdate',
                        'market'],
         'dtypes':     ['varchar(24)', 'varchar(48)', 'varchar(20)', 'varchar(20)', 'varchar(8)',
                        'date', 'date', 'date', 'date', 'date', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float', 'text', 'varchar(2)', 'varchar(10)', 'varchar(10)',
                        'varchar(10)', 'date', 'date', 'varchar(2)'],
         'remarks':    ['证券代码', '简称', '管理人', '托管人', '投资类型', '成立日期', '到期日期', '上市时间',
                        '发行日期', '退市日期', '发行份额(亿)', '管理费', '托管费', '存续期', '面值',
                        '起点金额(万元)', '预期收益率', '业绩比较基准', '存续状态D摘牌 I发行 L已上市',
                        '投资风格', '基金类型', '受托人', '日常申购起始日', '日常赎回起始日', 'E场内O场外'],
         'prime_keys': [0]
         },

    'future_basic':  # 期货基本信息表
        {'columns':    ['ts_code', 'symbol', 'exchange', 'name', 'fut_code', 'multiplier', 'trade_unit',
                        'per_unit', 'quote_unit', 'quote_unit_desc', 'd_mode_desc', 'list_date',
                        'delist_date', 'd_month', 'last_ddate', 'trade_time_desc'],
         'dtypes':     ['varchar(24)', 'varchar(12)', 'varchar(8)', 'varchar(40)', 'varchar(12)',
                        'float', 'varchar(4)', 'float', 'varchar(80)', 'varchar(80)', 'varchar(20)',
                        'date', 'date', 'varchar(6)', 'date', 'varchar(80)'],
         'remarks':    ['证券代码', '交易标识', '交易市场', '中文简称', '合约产品代码', '合约乘数',
                        '交易计量单位', '交易单位(每手)', '报价单位', '最小报价单位说明', '交割方式说明',
                        '上市日期', '最后交易日期', '交割月份', '最后交割日', '交易时间说明'],
         'prime_keys': [0]
         },

    'opt_basic':  # 期权基本信息表
        {'columns':    ['ts_code', 'exchange', 'name', 'per_unit', 'opt_code', 'opt_type', 'call_put',
                        'exercise_type', 'exercise_price', 's_month', 'maturity_date', 'list_price',
                        'list_date', 'delist_date', 'last_edate', 'last_ddate', 'quote_unit',
                        'min_price_chg'],
         'dtypes':     ['varchar(24)', 'varchar(6)', 'varchar(50)', 'varchar(10)', 'varchar(12)',
                        'varchar(6)', 'varchar(6)', 'varchar(6)', 'float', 'varchar(8)', 'date',
                        'float', 'date', 'date', 'date', 'date', 'varchar(12)', 'varchar(6)'],
         'remarks':    ['证券代码', '交易市场', '合约名称', '合约单位', '标准合约代码', '合约类型', '期权类型',
                        '行权方式', '行权价格', '结算月', '到期日', '挂牌基准价', '开始交易日期',
                        '最后交易日期', '最后行权日期', '最后交割日期', '报价单位', '最小价格波幅'],
         'prime_keys': [0]
         },

    'ths_index_basic':  # New, 同花顺指数基本信息
        {'columns':     ["ts_code", "name", "count", "exchange", "list_date", "type"],
         'dtypes':      ["varchar(14)", "text", "int", "varchar(4)", "date", "varchar(4)"],
         'remarks':     ["代码", "名称", "成分个数", "交易所", "上市日期", "N概念指数S特色指数"],
         'prime_keys':  [0]
         },

    'sw_industry_basic':  # New, 申万行业分类
        {'columns':     ["index_code", "industry_name", "parent_code", "level", "industry_code",
                         "is_pub", "src"],
         'dtypes':      ["varchar(14)", "varchar(40)", "varchar(6)", "varchar(6)", "varchar(10)",
                         "varchar(4)", "varchar(8)"],
         'remarks':     ["指数代码", "行业名称", "父级代码", "行业名称", "行业代码",
                         "是否发布了指数", "行业分类（SW申万）"],
         'prime_keys':  [0]
         },

    'bars':  # 日线行情表
        {'columns':    ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change',
                        'pct_chg', 'vol', 'amount'],
         'dtypes':     ['varchar(20)', 'date', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float', 'double', 'double'],
         'remarks':    ['证券代码', '交易日期', '开盘价', '最高价', '最低价', '收盘价', '昨收价', '涨跌额',
                        '涨跌幅', '成交量(手)', '成交额(千元)'],
         'prime_keys': [0, 1]
         },

    'min_bars':  # 分钟K线行情表
        {'columns':    ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount'],
         'dtypes':     ['varchar(20)', 'datetime', 'float', 'float', 'float', 'float', 'double',
                        'double'],
         'remarks':    ['证券代码', '交易日期时间', '开盘价', '最高价', '最低价', '收盘价', '成交量(股)',
                        '成交额(元)'],
         'prime_keys': [0, 1]
         },

    'hk_daily': # 港股日线行情表
        {'columns':    ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount'],
         'dtypes':     ['varchar(20)', 'datetime', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float'],
         'remarks':    ['股票代码', '交易日期', '开盘价', '最高价', '最低价', '收盘价', '昨收价', '涨跌额',
                        '涨跌幅(%)', '成交量(股)', '成交额(元)'],
         'prime_keys': [0, 1]
         },

    'us_daily': # 美股日线行情表
        {'columns':    ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'pre_close', 'change',
                        'pct_change', 'vol', 'amount', 'vwap', 'turnover_ratio', 'total_mv', 'pe', 'pb'],
         'dtypes':     ['varchar(20)', 'datetime', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float'],
         'remarks':    ['股票代码', '交易日期', '收盘价', '开盘价', '最高价', '最低价', '昨收价', '涨跌额',
                        '涨跌幅', '成交量', '成交额', '平均价', '换手率', '总市值', 'PE-市盈率', 'PB-市净率'],
         'prime_keys': [0, 1]
         },

    'hk_us_indicators':
        {'columns':    ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'pre_close', 'change', 'pct_change', 'vol', 'amount', 'vwap', 'adj_factor', 'turnover_ratio', 'free_share', 'total_share', 'free_mv', 'total_mv', 'exchange'],
         'dtypes':     ['str', 'str', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'None', 'float', 'float', 'float', 'float', 'None', 'None', 'float', 'float', 'str'],
         'remarks':    ['股票代码', '交易日期', '收盘价', '开盘价', '最高价', '最低价', '昨收价', '涨跌额', '涨跌幅', '成交量', '成交额', '平均价', '复权因子', '换手率', '流通股本', '总股本', '流通市值', '总市值', '交易所代码'],
         'prime_keys': [0, 1]},

    'adj_factors':  # 复权因子表
        {'columns':    ['ts_code', 'trade_date', 'adj_factor'],
         'dtypes':     ['varchar(24)', 'date', 'double'],
         'remarks':    ['证券代码', '交易日期', '复权因子'],
         'prime_keys': [0, 1]
         },

    'ths_index_daily':  # New, 同花顺行业指数日线行情!
        {'columns':     ["ts_code", "trade_date", "close", "open", "high", "low", "pre_close", "avg_price",
                         "change", "pct_change", "vol", "turnover_rate", "total_mv", "float_mv"],
         'dtypes':      ["varchar(14)", "date", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float"],
         'remarks':     ["TS指数代码", "交易日", "收盘点位", "开盘点位", "最高点位", "最低点位", "昨日收盘点", "平均价",
                         "涨跌点位", "涨跌幅", "成交量", "换手率", "总市值", "流通市值"],
         'prime_keys':  [0, 1]
         },

    'ths_index_weight':  # New, 同花顺行业指数成分股权重!
        {'columns':     ["ts_code", "con_code", "con_name", "weight", "in_date", "out_date", "is_new"],
         'dtypes':      ["varchar(10)", "varchar(10)", "varchar(80)", "float", "varchar(10)", "varchar(10)", "varchar(2)"],
         'remarks':     ["指数代码", "股票代码", "股票名称", "权重(暂无)", "纳入日期(暂无)", "剔除日期(暂无)", "是否最新Y是N否"],
         'prime_keys':  [0, 1]
         },

    'ci_index_daily':  # New, 中信行业指数日线行情!
        {'columns':     ["ts_code", "trade_date", "open", "low", "high", "close", "pre_close", "change",
                         "pct_change", "vol", "amount"],
         'dtypes':      ["varchar(14)", "date", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float"],
         'remarks':     ["指数代码", "交易日期", "开盘点位", "最低点位", "最高点位", "收盘点位", "昨日收盘点位", "涨跌点位",
                         "涨跌幅", "成交量（万股）", "成交额（万元）"],
         'prime_keys':  [0, 1]
         },

    'sw_index_daily':  # New, 申万指数日线行情!
        {'columns':     ["ts_code", "trade_date", "name", "open", "low", "high", "close", "change",
                         "pct_change", "vol", "amount", "pe", "pb", "float_mv", "total_mv"],
         'dtypes':      ["varchar(14)", "date", "varchar(24)", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["指数代码", "交易日期", "指数名称", "开盘点位", "最低点位", "最高点位", "收盘点位", "涨跌点位",
                         "涨跌幅", "成交量（万股）", "成交额（万元）", "市盈率", "市净率", "流通市值（万元）", "总市值（万元）"],
         'prime_keys':  [0, 1]
         },

    'global_index_daily':  # New, 全球指数日线行情!
        {'columns':     ["ts_code", "trade_date", "open", "close", "high", "low", "pre_close", "change",
                         "pct_chg", "swing", "vol", "amount"],
         'dtypes':      ["varchar(14)", "date", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float"],
         'remarks':     ["TS指数代码", "交易日", "开盘点位", "收盘点位", "最高点位", "最低点位", "昨日收盘点", "涨跌点位",
                         "涨跌幅", "振幅", "成交量 （大部分无此项数据）", "成交额 （大部分无此项数据）"],
         'prime_keys':  [0, 1]
         },

    'fund_nav':  # 基金净值表
        {'columns':    ['ts_code', 'nav_date', 'ann_date', 'unit_nav', 'accum_nav', 'accum_div',
                        'net_asset', 'total_netasset', 'adj_nav', 'update_flag'],
         'dtypes':     ['varchar(24)', 'date', 'date', 'float', 'float', 'float', 'double', 'double',
                        'float', 'varchar(2)'],
         'remarks':    ['证券代码', '净值日期', '公告日期', '单位净值', '累计净值', '累计分红', '资产净值',
                        '合计资产净值', '复权单位净值', '更新标记'],
         'prime_keys': [0, 1]
         },

    'fund_share':  # 基金份额表
        {'columns':    ['ts_code', 'trade_date', 'fd_share'],
         'dtypes':     ['varchar(24)', 'date', 'float'],
         'remarks':    ['证券代码', '变动日期，格式YYYYMMDD', '基金份额(万)'],
         'prime_keys': [0, 1]
         },

    'fund_manager':  # 基金经理表 -- REFINE
        {'columns':    ['ts_code', 'ann_date', 'name', 'gender', 'birth_year', 'edu', 'nationality',
                        'begin_date', 'end_date', 'resume'],
         'dtypes':     ['varchar(24)', 'date', 'varchar(20)', 'varchar(2)', 'varchar(12)',
                        'varchar(30)', 'varchar(4)', 'date', 'date', 'text'],
         'remarks':    ['证券代码', '公告日期', '基金经理姓名', '性别', '出生年份', '学历', '国籍', '任职日期',
                        '离任日期', '简历'],
         'prime_keys': [0, 1, 2]
         },

    'future_mapping':  # New, 期货合约映射表!
        {'columns':    ["ts_code", "trade_date", "mapping_ts_code"],
         'dtypes':     ["varchar(14)", "date", "varchar(18)"],
         'remarks':    ["连续合约代码", "起始日期", "期货合约代码"],
         'prime_keys': [0, 1]
         },

    'future_daily':  # 期货日线行情表
        {'columns':    ['ts_code', 'trade_date', 'pre_close', 'pre_settle', 'open', 'high', 'low',
                        'close', 'settle', 'change1', 'change2', 'vol', 'amount', 'oi', 'oi_chg',
                        'delv_settle'],
         'dtypes':     ['varchar(20)', 'date', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float', 'double', 'double', 'double', 'double', 'float'],
         'remarks':    ['证券代码', '交易日期', '昨收盘价', '昨结算价', '开盘价', '最高价', '最低价',
                        '收盘价', '结算价', '涨跌1 收盘价-昨结算价', '涨跌2 结算价-昨结算价', '成交量(手)',
                        '成交金额(万元)', '持仓量(手)', '持仓量变化', '交割结算价'],
         'prime_keys': [0, 1]
         },

    'future_mins':  # 期货分钟K线行情表
        {'columns':    ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount', 'oi'],
         'dtypes':     ['varchar(20)', 'datetime', 'float', 'float', 'float', 'float', 'double',
                        'double', 'double'],
         'remarks':    ['证券代码', '交易日期时间', '开盘价', '最高价', '最低价', '收盘价', '成交量(手)',
                        '成交金额(元)', '持仓量(手)'],
         'prime_keys': [0, 1]
         },

    'options_daily':  # 期权日线行情表
        {'columns':    ['ts_code', 'trade_date', 'exchange', 'pre_settle', 'pre_close', 'open', 'high',
                        'low', 'close', 'settle', 'vol', 'amount', 'oi'],
         'dtypes':     ['varchar(20)', 'date', 'varchar(8)', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float', 'double', 'double', 'double'],
         'remarks':    ['证券代码', '交易日期', '交易市场', '昨结算价', '昨收盘价', '开盘价', '最高价', '最低价',
                        '收盘价', '结算价', '成交量(手)', '成交金额(万元)', '持仓量(手)'],
         'prime_keys': [0, 1]
         },

    'stock_indicator':  # 股票技术指标表
        {'columns':    ['ts_code', 'trade_date', 'close', 'turnover_rate', 'turnover_rate_f',
                        'volume_ratio', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm',
                        'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv'],
         'dtypes':     ['varchar(9)', 'date', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float', 'float', 'float', 'double', 'double', 'double',
                        'double', 'double'],
         'remarks':    ['证券代码', '交易日期', '当日收盘价', '换手率(%)', '换手率(自由流通股)', '量比',
                        '市盈率(总市值/净利润， 亏损的PE为空)', '市盈率(TTM，亏损的PE为空)',
                        '市净率(总市值/净资产)', '市销率', '市销率(TTM)', '股息率(%)',
                        '股息率(TTM)(%)', '总股本(万股)', '流通股本(万股)', '自由流通股本(万)',
                        '总市值(万元)', '流通市值(万元)'],
         'prime_keys': [0, 1]
         },

    'stock_indicator2':  # 股票技术指标备用表
        {'columns':    ['ts_code', 'trade_date', 'vol_ratio', 'turn_over', 'swing',
                        'selling', 'buying', 'total_share', 'float_share', 'pe',
                        'float_mv', 'total_mv', 'avg_price', 'strength', 'activity', 'avg_turnover',
                        'attack', 'interval_3', 'interval_6'],
         'dtypes':     ['varchar(9)', 'date', 'float', 'float', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'float', 'float'],
         'remarks':    ['证券代码', '交易日期', '量比', '换手率', '振幅', '内盘(主动卖，手)',
                        '外盘(主动买， 手)', '总股本(亿)', '流通股本(亿)', '市盈(动)',
                        '流通市值', '总市值', '平均价', '强弱度(%)', '活跃度(%)', '笔换手', '攻击波(%)',
                        '近3月涨幅', '近6月涨幅'],
         'prime_keys': [0, 1]
         },

    'index_indicator':  # 指数关键指标表
        {'columns':    ['ts_code', 'trade_date', 'total_mv', 'float_mv', 'total_share', 'float_share',
                        'free_share', 'turnover_rate', 'turnover_rate_f', 'pe', 'pe_ttm', 'pb'],
         'dtypes':     ['varchar(9)', 'date', 'double', 'double', 'double', 'double', 'double', 'float',
                        'float', 'float', 'float', 'float'],
         'remarks':    ['证券代码', '交易日期', '当日总市值(元)', '当日流通市值(元)', '当日总股本(股)',
                        '当日流通股本(股)', '当日自由流通股本(股)', '换手率', '换手率(基于自由流通股本)',
                        '市盈率', '市盈率TTM', '市净率'],
         'prime_keys': [0, 1]
         },

    'index_weight':  # 指数成分表
        {'columns':    ['index_code', 'trade_date', 'con_code', 'weight'],
         'dtypes':     ['varchar(24)', 'date', 'varchar(20)', 'float'],
         'remarks':    ['指数代码', '交易日期', '成分代码', '权重(%)'],
         'prime_keys': [0, 1, 2]
         },

    'income':  # 上市公司利润表
        {'columns':    ['ts_code', 'end_date', 'ann_date', 'f_ann_date', 'report_type', 'comp_type',
                        'end_type', 'basic_eps', 'diluted_eps', 'total_revenue', 'revenue',
                        'int_income', 'prem_earned', 'comm_income', 'n_commis_income', 'n_oth_income',
                        'n_oth_b_income', 'prem_income', 'out_prem', 'une_prem_reser', 'reins_income',
                        'n_sec_tb_income', 'n_sec_uw_income', 'n_asset_mg_income', 'oth_b_income',
                        'fv_value_chg_gain', 'invest_income', 'ass_invest_income', 'forex_gain',
                        'total_cogs', 'oper_cost', 'int_exp', 'comm_exp', 'biz_tax_surchg', 'sell_exp',
                        'admin_exp', 'fin_exp', 'assets_impair_loss', 'prem_refund', 'compens_payout',
                        'reser_insur_liab', 'div_payt', 'reins_exp', 'oper_exp', 'compens_payout_refu',
                        'insur_reser_refu', 'reins_cost_refund', 'other_bus_cost', 'operate_profit',
                        'non_oper_income', 'non_oper_exp', 'nca_disploss', 'total_profit',
                        'income_tax', 'n_income', 'n_income_attr_p', 'minority_gain',
                        'oth_compr_income', 't_compr_income', 'compr_inc_attr_p', 'compr_inc_attr_m_s',
                        'ebit', 'ebitda', 'insurance_exp', 'undist_profit', 'distable_profit',
                        'rd_exp', 'fin_exp_int_exp', 'fin_exp_int_inc', 'transfer_surplus_rese',
                        'transfer_housing_imprest', 'transfer_oth', 'adj_lossgain',
                        'withdra_legal_surplus', 'withdra_legal_pubfund', 'withdra_biz_devfund',
                        'withdra_rese_fund', 'withdra_oth_ersu', 'workers_welfare',
                        'distr_profit_shrhder', 'prfshare_payable_dvd', 'comshare_payable_dvd',
                        'capit_comstock_div', 'net_after_nr_lp_correct', 'credit_impa_loss',
                        'net_expo_hedging_benefits', 'oth_impair_loss_assets', 'total_opcost',
                        'amodcost_fin_assets', 'oth_income', 'asset_disp_income',
                        'continued_net_profit', 'end_net_profit', 'update_flag'],
         'dtypes':     ['varchar(9)', 'date', 'date', 'date', 'varchar(6)', 'varchar(6)', 'varchar(6)',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'varchar(4)'],
         'remarks':    ['证券代码', '报告期', '公告日期', '实际公告日期', '报告类型 见底部表',
                        '公司类型(1一般工商业2银行3保险4证券)', '报告期类型', '基本每股收益', '稀释每股收益',
                        '营业总收入', '营业收入', '利息收入', '已赚保费', '手续费及佣金收入', '手续费及佣金净收入',
                        '其他经营净收益', '加:其他业务净收益', '保险业务收入', '减:分出保费',
                        '提取未到期责任准备金', '其中:分保费收入', '代理买卖证券业务净收入', '证券承销业务净收入',
                        '受托客户资产管理业务净收入', '其他业务收入', '加:公允价值变动净收益', '加:投资净收益',
                        '其中:对联营企业和合营企业的投资收益', '加:汇兑净收益', '营业总成本', '减:营业成本',
                        '减:利息支出', '减:手续费及佣金支出', '减:营业税金及附加', '减:销售费用', '减:管理费用',
                        '减:财务费用', '减:资产减值损失', '退保金', '赔付总支出', '提取保险责任准备金',
                        '保户红利支出', '分保费用', '营业支出', '减:摊回赔付支出', '减:摊回保险责任准备金',
                        '减:摊回分保费用', '其他业务成本', '营业利润', '加:营业外收入', '减:营业外支出',
                        '其中:减:非流动资产处置净损失', '利润总额', '所得税费用', '净利润(含少数股东损益)',
                        '净利润(不含少数股东损益)', '少数股东损益', '其他综合收益', '综合收益总额',
                        '归属于母公司(或股东)的综合收益总额', '归属于少数股东的综合收益总额', '息税前利润',
                        '息税折旧摊销前利润', '保险业务支出', '年初未分配利润', '可分配利润', '研发费用',
                        '财务费用:利息费用', '财务费用:利息收入', '盈余公积转入', '住房周转金转入', '其他转入',
                        '调整以前年度损益', '提取法定盈余公积', '提取法定公益金', '提取企业发展基金',
                        '提取储备基金', '提取任意盈余公积金', '职工奖金福利', '可供股东分配的利润',
                        '应付优先股股利', '应付普通股股利', '转作股本的普通股股利',
                        '扣除非经常性损益后的净利润(更正前)', '信用减值损失', '净敞口套期收益',
                        '其他资产减值损失', '营业总成本(二)', '以摊余成本计量的金融资产终止确认收益',
                        '其他收益', '资产处置收益', '持续经营净利润', '终止经营净利润', '更新标识'],
         'prime_keys': [0, 1]
         },

    'balance':  # 上市公司资产负债表
        {'columns':    ['ts_code', 'end_date', 'ann_date', 'f_ann_date', 'report_type', 'comp_type',
                        'end_type', 'total_share', 'cap_rese', 'undistr_porfit', 'surplus_rese',
                        'special_rese', 'money_cap', 'trad_asset', 'notes_receiv', 'accounts_receiv',
                        'oth_receiv', 'prepayment', 'div_receiv', 'int_receiv', 'inventories',
                        'amor_exp', 'nca_within_1y', 'sett_rsrv', 'loanto_oth_bank_fi',
                        'premium_receiv', 'reinsur_receiv', 'reinsur_res_receiv', 'pur_resale_fa',
                        'oth_cur_assets', 'total_cur_assets', 'fa_avail_for_sale', 'htm_invest',
                        'lt_eqt_invest', 'invest_real_estate', 'time_deposits', 'oth_assets', 'lt_rec',
                        'fix_assets', 'cip', 'const_materials', 'fixed_assets_disp',
                        'produc_bio_assets', 'oil_and_gas_assets', 'intan_assets', 'r_and_d',
                        'goodwill', 'lt_amor_exp', 'defer_tax_assets', 'decr_in_disbur', 'oth_nca',
                        'total_nca', 'cash_reser_cb', 'depos_in_oth_bfi', 'prec_metals',
                        'deriv_assets', 'rr_reins_une_prem', 'rr_reins_outstd_cla',
                        'rr_reins_lins_liab', 'rr_reins_lthins_liab', 'refund_depos',
                        'ph_pledge_loans', 'refund_cap_depos', 'indep_acct_assets', 'client_depos',
                        'client_prov', 'transac_seat_fee', 'invest_as_receiv', 'total_assets',
                        'lt_borr', 'st_borr', 'cb_borr', 'depos_ib_deposits', 'loan_oth_bank',
                        'trading_fl', 'notes_payable', 'acct_payable', 'adv_receipts',
                        'sold_for_repur_fa', 'comm_payable', 'payroll_payable', 'taxes_payable',
                        'int_payable', 'div_payable', 'oth_payable', 'acc_exp', 'deferred_inc',
                        'st_bonds_payable', 'payable_to_reinsurer', 'rsrv_insur_cont',
                        'acting_trading_sec', 'acting_uw_sec', 'non_cur_liab_due_1y', 'oth_cur_liab',
                        'total_cur_liab', 'bond_payable', 'lt_payable', 'specific_payables',
                        'estimated_liab', 'defer_tax_liab', 'defer_inc_non_cur_liab', 'oth_ncl',
                        'total_ncl', 'depos_oth_bfi', 'deriv_liab', 'depos', 'agency_bus_liab',
                        'oth_liab', 'prem_receiv_adva', 'depos_received', 'ph_invest',
                        'reser_une_prem', 'reser_outstd_claims', 'reser_lins_liab',
                        'reser_lthins_liab', 'indept_acc_liab', 'pledge_borr', 'indem_payable',
                        'policy_div_payable', 'total_liab', 'treasury_share', 'ordin_risk_reser',
                        'forex_differ', 'invest_loss_unconf', 'minority_int',
                        'total_hldr_eqy_exc_min_int', 'total_hldr_eqy_inc_min_int',
                        'total_liab_hldr_eqy', 'lt_payroll_payable', 'oth_comp_income',
                        'oth_eqt_tools', 'oth_eqt_tools_p_shr', 'lending_funds', 'acc_receivable',
                        'st_fin_payable', 'payables', 'hfs_assets', 'hfs_sales', 'cost_fin_assets',
                        'fair_value_fin_assets', 'cip_total', 'oth_pay_total', 'long_pay_total',
                        'debt_invest', 'oth_debt_invest', 'oth_eq_invest', 'oth_illiq_fin_assets',
                        'oth_eq_ppbond', 'receiv_financing', 'use_right_assets', 'lease_liab',
                        'contract_assets', 'contract_liab', 'accounts_receiv_bill', 'accounts_pay',
                        'oth_rcv_total', 'fix_assets_total', 'update_flag'],
         'dtypes':     ['varchar(9)', 'date', 'date', 'date', 'varchar(10)', 'varchar(10)',
                        'varchar(10)', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'varchar(2)'],
         'remarks':    ['证券代码', '报告期', '公告日期', '实际公告日期', '报表类型', '公司类型', '报告期类型',
                        '期末总股本', '资本公积金', '未分配利润', '盈余公积金', '专项储备', '货币资金',
                        '交易性金融资产', '应收票据', '应收账款', '其他应收款', '预付款项', '应收股利',
                        '应收利息', '存货', '长期待摊费用', '一年内到期的非流动资产', '结算备付金', '拆出资金',
                        '应收保费', '应收分保账款', '应收分保合同准备金', '买入返售金融资产', '其他流动资产',
                        '流动资产合计', '可供出售金融资产', '持有至到期投资', '长期股权投资', '投资性房地产',
                        '定期存款', '其他资产', '长期应收款', '固定资产', '在建工程', '工程物资', '固定资产清理',
                        '生产性生物资产', '油气资产', '无形资产', '研发支出', '商誉', '长期待摊费用',
                        '递延所得税资产', '发放贷款及垫款', '其他非流动资产', '非流动资产合计',
                        '现金及存放中央银行款项', '存放同业和其它金融机构款项', '贵金属', '衍生金融资产',
                        '应收分保未到期责任准备金', '应收分保未决赔款准备金', '应收分保寿险责任准备金',
                        '应收分保长期健康险责任准备金', '存出保证金', '保户质押贷款', '存出资本保证金',
                        '独立账户资产', '其中：客户资金存款', '其中：客户备付金', '其中:交易席位费',
                        '应收款项类投资', '资产总计', '长期借款', '短期借款', '向中央银行借款',
                        '吸收存款及同业存放', '拆入资金', '交易性金融负债', '应付票据', '应付账款', '预收款项',
                        '卖出回购金融资产款', '应付手续费及佣金', '应付职工薪酬', '应交税费', '应付利息',
                        '应付股利', '其他应付款', '预提费用', '递延收益', '应付短期债券', '应付分保账款',
                        '保险合同准备金', '代理买卖证券款', '代理承销证券款', '一年内到期的非流动负债',
                        '其他流动负债', '流动负债合计', '应付债券', '长期应付款', '专项应付款', '预计负债',
                        '递延所得税负债', '递延收益-非流动负债', '其他非流动负债', '非流动负债合计',
                        '同业和其它金融机构存放款项', '衍生金融负债', '吸收存款', '代理业务负债', '其他负债',
                        '预收保费', '存入保证金', '保户储金及投资款', '未到期责任准备金', '未决赔款准备金',
                        '寿险责任准备金', '长期健康险责任准备金', '独立账户负债', '其中:质押借款', '应付赔付款',
                        '应付保单红利', '负债合计', '减:库存股', '一般风险准备', '外币报表折算差额',
                        '未确认的投资损失', '少数股东权益', '股东权益合计(不含少数股东权益)',
                        '股东权益合计(含少数股东权益)', '负债及股东权益总计', '长期应付职工薪酬', '其他综合收益',
                        '其他权益工具', '其他权益工具(优先股)', '融出资金', '应收款项', '应付短期融资款',
                        '应付款项', '持有待售的资产', '持有待售的负债', '以摊余成本计量的金融资产',
                        '以公允价值计量且其变动计入其他综合收益的金融资产', '在建工程(合计)(元)',
                        '其他应付款(合计)(元)', '长期应付款(合计)(元)', '债权投资(元)', '其他债权投资(元)',
                        '其他权益工具投资(元)', '其他非流动金融资产(元)', '其他权益工具:永续债(元)',
                        '应收款项融资', '使用权资产', '租赁负债', '合同资产', '合同负债', '应收票据及应收账款',
                        '应付票据及应付账款', '其他应收款(合计)(元)', '固定资产(合计)(元)', '更新标识'],
         'prime_keys': [0, 1]
         },

    'cashflow':  # 上市公司现金流量表
        {'columns':    ['ts_code', 'end_date', 'ann_date', 'f_ann_date', 'comp_type', 'report_type',
                        'end_type', 'net_profit', 'finan_exp', 'c_fr_sale_sg', 'recp_tax_rends',
                        'n_depos_incr_fi', 'n_incr_loans_cb', 'n_inc_borr_oth_fi',
                        'prem_fr_orig_contr', 'n_incr_insured_dep', 'n_reinsur_prem',
                        'n_incr_disp_tfa', 'ifc_cash_incr', 'n_incr_disp_faas',
                        'n_incr_loans_oth_bank', 'n_cap_incr_repur', 'c_fr_oth_operate_a',
                        'c_inf_fr_operate_a', 'c_paid_goods_s', 'c_paid_to_for_empl',
                        'c_paid_for_taxes', 'n_incr_clt_loan_adv', 'n_incr_dep_cbob',
                        'c_pay_claims_orig_inco', 'pay_handling_chrg', 'pay_comm_insur_plcy',
                        'oth_cash_pay_oper_act', 'st_cash_out_act', 'n_cashflow_act',
                        'oth_recp_ral_inv_act', 'c_disp_withdrwl_invest', 'c_recp_return_invest',
                        'n_recp_disp_fiolta', 'n_recp_disp_sobu', 'stot_inflows_inv_act',
                        'c_pay_acq_const_fiolta', 'c_paid_invest', 'n_disp_subs_oth_biz',
                        'oth_pay_ral_inv_act', 'n_incr_pledge_loan', 'stot_out_inv_act',
                        'n_cashflow_inv_act', 'c_recp_borrow', 'proc_issue_bonds',
                        'oth_cash_recp_ral_fnc_act', 'stot_cash_in_fnc_act', 'free_cashflow',
                        'c_prepay_amt_borr', 'c_pay_dist_dpcp_int_exp', 'incl_dvd_profit_paid_sc_ms',
                        'oth_cashpay_ral_fnc_act', 'stot_cashout_fnc_act', 'n_cash_flows_fnc_act',
                        'eff_fx_flu_cash', 'n_incr_cash_cash_equ', 'c_cash_equ_beg_period',
                        'c_cash_equ_end_period', 'c_recp_cap_contrib', 'incl_cash_rec_saims',
                        'uncon_invest_loss', 'prov_depr_assets', 'depr_fa_coga_dpba',
                        'amort_intang_assets', 'lt_amort_deferred_exp', 'decr_deferred_exp',
                        'incr_acc_exp', 'loss_disp_fiolta', 'loss_scr_fa', 'loss_fv_chg',
                        'invest_loss', 'decr_def_inc_tax_assets', 'incr_def_inc_tax_liab',
                        'decr_inventories', 'decr_oper_payable', 'incr_oper_payable', 'others',
                        'im_net_cashflow_oper_act', 'conv_debt_into_cap',
                        'conv_copbonds_due_within_1y', 'fa_fnc_leases', 'im_n_incr_cash_equ',
                        'net_dism_capital_add', 'net_cash_rece_sec', 'credit_impa_loss',
                        'use_right_asset_dep', 'oth_loss_asset', 'end_bal_cash', 'beg_bal_cash',
                        'end_bal_cash_equ', 'beg_bal_cash_equ', 'update_flag'],
         'dtypes':     ['varchar(9)', 'date', 'date', 'date', 'varchar(10)', 'varchar(10)',
                        'varchar(10)', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'varchar(2)'],
         'remarks':    ['证券代码', '报告期', '公告日期', '实际公告日期', '公司类型', '报表类型', '报告期类型',
                        '净利润', '财务费用', '销售商品、提供劳务收到的现金', '收到的税费返还',
                        '客户存款和同业存放款项净增加额', '向中央银行借款净增加额', '向其他金融机构拆入资金净增加额',
                        '收到原保险合同保费取得的现金', '保户储金净增加额', '收到再保业务现金净额',
                        '处置交易性金融资产净增加额', '收取利息和手续费净增加额', '处置可供出售金融资产净增加额',
                        '拆入资金净增加额', '回购业务资金净增加额', '收到其他与经营活动有关的现金',
                        '经营活动现金流入小计', '购买商品、接受劳务支付的现金', '支付给职工以及为职工支付的现金',
                        '支付的各项税费', '客户贷款及垫款净增加额', '存放央行和同业款项净增加额',
                        '支付原保险合同赔付款项的现金', '支付手续费的现金', '支付保单红利的现金',
                        '支付其他与经营活动有关的现金', '经营活动现金流出小计', '经营活动产生的现金流量净额',
                        '收到其他与投资活动有关的现金', '收回投资收到的现金', '取得投资收益收到的现金',
                        '处置固定资产、无形资产和其他长期资产收回的现金净额',
                        '处置子公司及其他营业单位收到的现金净额', '投资活动现金流入小计',
                        '购建固定资产、无形资产和其他长期资产支付的现金', '投资支付的现金',
                        '取得子公司及其他营业单位支付的现金净额', '支付其他与投资活动有关的现金',
                        '质押贷款净增加额', '投资活动现金流出小计', '投资活动产生的现金流量净额',
                        '取得借款收到的现金', '发行债券收到的现金', '收到其他与筹资活动有关的现金',
                        '筹资活动现金流入小计', '企业自由现金流量', '偿还债务支付的现金',
                        '分配股利、利润或偿付利息支付的现金', '其中:子公司支付给少数股东的股利、利润',
                        '支付其他与筹资活动有关的现金', '筹资活动现金流出小计', '筹资活动产生的现金流量净额',
                        '汇率变动对现金的影响', '现金及现金等价物净增加额', '期初现金及现金等价物余额',
                        '期末现金及现金等价物余额', '吸收投资收到的现金', '其中:子公司吸收少数股东投资收到的现金',
                        '未确认投资损失', '加:资产减值准备', '固定资产折旧、油气资产折耗、生产性生物资产折旧',
                        '无形资产摊销', '长期待摊费用摊销', '待摊费用减少', '预提费用增加',
                        '处置固定、无形资产和其他长期资产的损失', '固定资产报废损失', '公允价值变动损失',
                        '投资损失', '递延所得税资产减少', '递延所得税负债增加', '存货的减少',
                        '经营性应收项目的减少', '经营性应付项目的增加', '其他',
                        '经营活动产生的现金流量净额(间接法)', '债务转为资本', '一年内到期的可转换公司债券',
                        '融资租入固定资产', '现金及现金等价物净增加额(间接法)', '拆出资金净增加额',
                        '代理买卖证券收到的现金净额(元)', '信用减值损失', '使用权资产折旧', '其他资产减值损失',
                        '现金的期末余额', '减:现金的期初余额', '加:现金等价物的期末余额',
                        '减:现金等价物的期初余额', '更新标志(1最新)'],
         'prime_keys': [0, 1]
         },

    'financial':  # 上市公司财务指标数据
        {'columns':    ['ts_code', 'end_date', 'ann_date', 'eps', 'dt_eps', 'total_revenue_ps',
                        'revenue_ps', 'capital_rese_ps', 'surplus_rese_ps', 'undist_profit_ps',
                        'extra_item', 'profit_dedt', 'gross_margin', 'current_ratio', 'quick_ratio',
                        'cash_ratio', 'invturn_days', 'arturn_days', 'inv_turn', 'ar_turn', 'ca_turn',
                        'fa_turn', 'assets_turn', 'op_income', 'valuechange_income', 'interst_income',
                        'daa', 'ebit', 'ebitda', 'fcff', 'fcfe', 'current_exint', 'noncurrent_exint',
                        'interestdebt', 'netdebt', 'tangible_asset', 'working_capital',
                        'networking_capital', 'invest_capital', 'retained_earnings', 'diluted2_eps',
                        'bps', 'ocfps', 'retainedps', 'cfps', 'ebit_ps', 'fcff_ps', 'fcfe_ps',
                        'netprofit_margin', 'grossprofit_margin', 'cogs_of_sales', 'expense_of_sales',
                        'profit_to_gr', 'saleexp_to_gr', 'adminexp_of_gr', 'finaexp_of_gr',
                        'impai_ttm', 'gc_of_gr', 'op_of_gr', 'ebit_of_gr', 'roe', 'roe_waa', 'roe_dt',
                        'roa', 'npta', 'roic', 'roe_yearly', 'roa2_yearly', 'roe_avg',
                        'opincome_of_ebt', 'investincome_of_ebt', 'n_op_profit_of_ebt', 'tax_to_ebt',
                        'dtprofit_to_profit', 'salescash_to_or', 'ocf_to_or', 'ocf_to_opincome',
                        'capitalized_to_da', 'debt_to_assets', 'assets_to_eqt', 'dp_assets_to_eqt',
                        'ca_to_assets', 'nca_to_assets', 'tbassets_to_totalassets', 'int_to_talcap',
                        'eqt_to_talcapital', 'currentdebt_to_debt', 'longdeb_to_debt',
                        'ocf_to_shortdebt', 'debt_to_eqt', 'eqt_to_debt', 'eqt_to_interestdebt',
                        'tangibleasset_to_debt', 'tangasset_to_intdebt', 'tangibleasset_to_netdebt',
                        'ocf_to_debt', 'ocf_to_interestdebt', 'ocf_to_netdebt', 'ebit_to_interest',
                        'longdebt_to_workingcapital', 'ebitda_to_debt', 'turn_days', 'roa_yearly',
                        'roa_dp', 'fixed_assets', 'profit_prefin_exp', 'non_op_profit', 'op_to_ebt',
                        'nop_to_ebt', 'ocf_to_profit', 'cash_to_liqdebt',
                        'cash_to_liqdebt_withinterest', 'op_to_liqdebt', 'op_to_debt', 'roic_yearly',
                        'total_fa_trun', 'profit_to_op', 'q_opincome', 'q_investincome', 'q_dtprofit',
                        'q_eps', 'q_netprofit_margin', 'q_gsprofit_margin', 'q_exp_to_sales',
                        'q_profit_to_gr', 'q_saleexp_to_gr', 'q_adminexp_to_gr', 'q_finaexp_to_gr',
                        'q_impair_to_gr_ttm', 'q_gc_to_gr', 'q_op_to_gr', 'q_roe', 'q_dt_roe',
                        'q_npta', 'q_opincome_to_ebt', 'q_investincome_to_ebt', 'q_dtprofit_to_profit',
                        'q_salescash_to_or', 'q_ocf_to_sales', 'q_ocf_to_or', 'basic_eps_yoy',
                        'dt_eps_yoy', 'cfps_yoy', 'op_yoy', 'ebt_yoy', 'netprofit_yoy',
                        'dt_netprofit_yoy', 'ocf_yoy', 'roe_yoy', 'bps_yoy', 'assets_yoy', 'eqt_yoy',
                        'tr_yoy', 'or_yoy', 'q_gr_yoy', 'q_gr_qoq', 'q_sales_yoy', 'q_sales_qoq',
                        'q_op_yoy', 'q_op_qoq', 'q_profit_yoy', 'q_profit_qoq', 'q_netprofit_yoy',
                        'q_netprofit_qoq', 'equity_yoy', 'rd_exp', 'update_flag'],
         'dtypes':     ['varchar(9)', 'date', 'date', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'varchar(4)'],
         'remarks':    ['证券代码', '报告期', '公告日期', '基本每股收益', '稀释每股收益', '每股营业总收入',
                        '每股营业收入', '每股资本公积', '每股盈余公积', '每股未分配利润', '非经常性损益',
                        '扣除非经常性损益后的净利润(扣非净利润)', '毛利', '流动比率', '速动比率', '保守速动比率',
                        '存货周转天数', '应收账款周转天数', '存货周转率', '应收账款周转率', '流动资产周转率',
                        '固定资产周转率', '总资产周转率', '经营活动净收益', '价值变动净收益', '利息费用',
                        '折旧与摊销', '息税前利润', '息税折旧摊销前利润', '企业自由现金流量', '股权自由现金流量',
                        '无息流动负债', '无息非流动负债', '带息债务', '净债务', '有形资产', '营运资金',
                        '营运流动资本', '全部投入资本', '留存收益', '期末摊薄每股收益', '每股净资产',
                        '每股经营活动产生的现金流量净额', '每股留存收益', '每股现金流量净额', '每股息税前利润',
                        '每股企业自由现金流量', '每股股东自由现金流量', '销售净利率', '销售毛利率', '销售成本率',
                        '销售期间费用率', '净利润/营业总收入', '销售费用/营业总收入', '管理费用/营业总收入',
                        '财务费用/营业总收入', '资产减值损失/营业总收入', '营业总成本/营业总收入',
                        '营业利润/营业总收入', '息税前利润/营业总收入', '净资产收益率', '加权平均净资产收益率',
                        '净资产收益率(扣除非经常损益)', '总资产报酬率', '总资产净利润', '投入资本回报率',
                        '年化净资产收益率', '年化总资产报酬率', '平均净资产收益率(增发条件)',
                        '经营活动净收益/利润总额', '价值变动净收益/利润总额', '营业外收支净额/利润总额',
                        '所得税/利润总额', '扣除非经常损益后的净利润/净利润', '销售商品提供劳务收到的现金/营业收入',
                        '经营活动产生的现金流量净额/营业收入', '经营活动产生的现金流量净额/经营活动净收益',
                        '资本支出/折旧和摊销', '资产负债率', '权益乘数', '权益乘数(杜邦分析)', '流动资产/总资产',
                        '非流动资产/总资产', '有形资产/总资产', '带息债务/全部投入资本',
                        '归属于母公司的股东权益/全部投入资本', '流动负债/负债合计', '非流动负债/负债合计',
                        '经营活动产生的现金流量净额/流动负债', '产权比率', '归属于母公司的股东权益/负债合计',
                        '归属于母公司的股东权益/带息债务', '有形资产/负债合计', '有形资产/带息债务',
                        '有形资产/净债务', '经营活动产生的现金流量净额/负债合计',
                        '经营活动产生的现金流量净额/带息债务', '经营活动产生的现金流量净额/净债务',
                        '已获利息倍数(EBIT/利息费用)', '长期债务与营运资金比率', '息税折旧摊销前利润/负债合计',
                        '营业周期', '年化总资产净利率', '总资产净利率(杜邦分析)', '固定资产合计',
                        '扣除财务费用前营业利润', '非营业利润', '营业利润／利润总额', '非营业利润／利润总额',
                        '经营活动产生的现金流量净额／营业利润', '货币资金／流动负债', '货币资金／带息流动负债',
                        '营业利润／流动负债', '营业利润／负债合计', '年化投入资本回报率', '固定资产合计周转率',
                        '利润总额／营业收入', '经营活动单季度净收益', '价值变动单季度净收益',
                        '扣除非经常损益后的单季度净利润', '每股收益(单季度)', '销售净利率(单季度)',
                        '销售毛利率(单季度)', '销售期间费用率(单季度)', '净利润／营业总收入(单季度)',
                        '销售费用／营业总收入(单季度)', '管理费用／营业总收入(单季度)',
                        '财务费用／营业总收入(单季度)', '资产减值损失／营业总收入(单季度)',
                        '营业总成本／营业总收入(单季度)', '营业利润／营业总收入(单季度)', '净资产收益率(单季度)',
                        '净资产单季度收益率(扣除非经常损益)', '总资产净利润(单季度)',
                        '经营活动净收益／利润总额(单季度)', '价值变动净收益／利润总额(单季度)',
                        '扣除非经常损益后的净利润／净利润(单季度)', '销售商品提供劳务收到的现金／营业收入(单季度)',
                        '经营活动产生的现金流量净额／营业收入(单季度)',
                        '经营活动产生的现金流量净额／经营活动净收益(单季度)', '基本每股收益同比增长率(%)',
                        '稀释每股收益同比增长率(%)', '每股经营活动产生的现金流量净额同比增长率(%)',
                        '营业利润同比增长率(%)', '利润总额同比增长率(%)', '归属母公司股东的净利润同比增长率(%)',
                        '归属母公司股东的净利润-扣除非经常损益同比增长率(%)',
                        '经营活动产生的现金流量净额同比增长率(%)', '净资产收益率(摊薄)同比增长率(%)',
                        '每股净资产相对年初增长率(%)', '资产总计相对年初增长率(%)',
                        '归属母公司的股东权益相对年初增长率(%)', '营业总收入同比增长率(%)',
                        '营业收入同比增长率(%)', '营业总收入同比增长率(%)(单季度)',
                        '营业总收入环比增长率(%)(单季度)', '营业收入同比增长率(%)(单季度)',
                        '营业收入环比增长率(%)(单季度)', '营业利润同比增长率(%)(单季度)',
                        '营业利润环比增长率(%)(单季度)', '净利润同比增长率(%)(单季度)',
                        '净利润环比增长率(%)(单季度)', '归属母公司股东的净利润同比增长率(%)(单季度)',
                        '归属母公司股东的净利润环比增长率(%)(单季度)', '净资产同比增长率', '研发费用', '更新标识'],
         'prime_keys': [0, 1]
         },

    'forecast':  # 业绩预告
        {'columns':    ['ts_code', 'end_date', 'ann_date', 'type', 'p_change_min', 'p_change_max',
                        'net_profit_min', 'net_profit_max', 'last_parent_net', 'first_ann_date',
                        'summary', 'change_reason'],
         'dtypes':     ['varchar(9)', 'date', 'date', 'varchar(9)', 'float', 'float', 'double',
                        'double', 'double', 'date', 'text', 'text'],
         'remarks':    ['证券代码', '报告期', '公告日期', '业绩预告类型', '预告净利润变动幅度下限(%)',
                        '预告净利润变动幅度上限(%)', '预告净利润下限(万元)', '预告净利润上限(万元)',
                        '上年同期归属母公司净利润', '首次公告日', '业绩预告摘要', '业绩变动原因'],
         # 业绩预告类型包括：预增/预减/扭亏/首亏/续亏/续盈/略增/略减
         'prime_keys': [0, 1, 2]
         },

    'express':  # 业绩快报
        {'columns':    ['ts_code', 'end_date', 'ann_date', 'revenue', 'operate_profit', 'total_profit',
                        'n_income', 'total_assets', 'total_hldr_eqy_exc_min_int', 'diluted_eps',
                        'diluted_roe', 'yoy_net_profit', 'bps', 'yoy_sales', 'yoy_op', 'yoy_tp',
                        'yoy_dedu_np', 'yoy_eps', 'yoy_roe', 'growth_assets', 'yoy_equity',
                        'growth_bps', 'or_last_year', 'op_last_year', 'tp_last_year', 'np_last_year',
                        'eps_last_year', 'open_net_assets', 'open_bps', 'perf_summary', 'is_audit',
                        'remark'],
         'dtypes':     ['varchar(9)', 'date', 'date', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'double', 'double', 'double',
                        'double', 'double', 'double', 'double', 'double', 'text', 'varchar(9)', 'text'],
         'remarks':    ['证券代码', '报告期', '公告日期', '营业收入(元)', '营业利润(元)', '利润总额(元)',
                        '净利润(元)', '总资产(元)', '股东权益合计(不含少数股东权益)(元)', '每股收益(摊薄)(元)',
                        '净资产收益率(摊薄)(%)', '去年同期修正后净利润', '每股净资产', '同比增长率:营业收入',
                        '同比增长率:营业利润', '同比增长率:利润总额', '同比增长率:归属母公司股东的净利润',
                        '同比增长率:基本每股收益', '同比增减:加权平均净资产收益率', '比年初增长率:总资产',
                        '比年初增长率:归属母公司的股东权益', '比年初增长率:归属于母公司股东的每股净资产',
                        '去年同期营业收入', '去年同期营业利润', '去年同期利润总额', '去年同期净利润',
                        '去年同期每股收益', '期初净资产', '期初每股净资产', '业绩简要说明', '是否审计： 1是 0否',
                        '备注'],
         'prime_keys': [0, 1]
         },

    'dividend':  # New, 分红送股!
        {'columns':     ["ts_code", "end_date", "div_proc", "ann_date", "stk_div", "stk_bo_rate", "stk_co_rate",
                         "cash_div", "cash_div_tax", "record_date", "ex_date", "pay_date", "div_listdate",
                         "imp_ann_date", "base_date", "base_share"],
         'dtypes':      ["varchar(14)", "date", "varchar(14)", "date", "float", "float", "float",
                         "float", "float", "date", "date", "date", "date",
                         "date", "date", "float"],
         'remarks':     ["证券代码", "分红年度", "实施进度", "预案公告日", "每股送转", "每股送股比例", "每股转增比例",
                         "每股分红（税后）", "每股分红（税前）", "股权登记日", "除权除息日", "派息日", "红股上市日",
                         "实施公告日", "基准日", "基准股本（万）"],
         'prime_keys':  [0, 1, 2]
         },

    'top_list':  # New, 龙虎榜交易明细!
        {'columns':     ["ts_code", "trade_date", "name", "close", "pct_change", "turnover_rate", "amount", "l_sell",
                         "l_buy", "l_amount", "net_amount", "net_rate", "amount_rate",
                         "float_values", "reason"],
         'dtypes':      ["varchar(14)", "date", "varchar(10)", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float",
                         "float", "text"],
         'remarks':     ["证券代码", "交易日期", "名称", "收盘价", "涨跌幅", "换手率", "总成交额", "龙虎榜卖出额",
                         "龙虎榜买入额", "龙虎榜成交额", "龙虎榜净买入额", "龙虎榜净买额占比", "龙虎榜成交额占比",
                         "当日流通市值", "上榜理由"],
         'prime_keys':  [0, 1]
         },

    'top_inst':  # New, 龙虎榜机构交易明细!
        {'columns':     ["ts_code", "trade_date", "exalter", "side", "buy",
                         "buy_rate", "sell", "sell_rate", "net_buy", "reason"],
         'dtypes':      ["varchar(14)", "date", "text", "varchar(2)", "float",
                         "float", "float", "float", "float", "text"],
         'remarks':     ["证券代码", "交易日期", "营业部名称", "买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名",
                         "买入额（元）", "买入占总成交比例", "卖出额（元）", "卖出占总成交比例", "净成交额（元）", "上榜理由"],
         'prime_keys':  [0, 1]
         },

    'sw_industry_detail':  # New, 申万行业分类明细(成分股)!
        {'columns':     ["l1_code", "l2_code", "l3_code", "ts_code",
                         "l1_name", "l2_name", "l3_name", "name",
                         "in_date", "out_date", "is_new"],
         'dtypes':      ["varchar(14)", "varchar(14)", "varchar(14)", "varchar(14)",
                         "varchar(24)", "varchar(24)", "varchar(24)", "varchar(24)",
                         "date", "date", "varchar(2)"],
         'remarks':     ["一级行业代码", "二级行业代码", "三级行业代码", "成分股票代码",
                         "一级行业名称", "二级行业名称", "三级行业名称", "成分股票名称",
                         "纳入日期", "剔除日期", "是否最新Y是N否"],
         'prime_keys':  [0, 1, 2, 3]
         },

    'block_trade':  # New, 大宗交易!
        {'columns':     ["ts_code", "trade_date", "price", "vol", "amount", "buyer", "seller"],
         'dtypes':      ["varchar(14)", "date", "float", "float", "float", "text", "text"],
         'remarks':     ["证券代码", "交易日历", "成交价", "成交量（万股）", "成交金额", "买方营业部", "卖方营业部"],
         'prime_keys':  [0, 1]
         },

    'stock_holder_trade':  # New, 股东交易（股东增减持）!
        {'columns':     ["ts_code", "ann_date", "holder_name", "holder_type", "in_de", "change_vol",
                         "change_ratio", "after_share", "after_ratio", "avg_price", "total_share", "begin_date",
                         "close_date"],
         'dtypes':      ["varchar(14)", "date", "text", "varchar(2)", "varchar(4)", "float",
                         "float", "float", "float", "float", "float", "date",
                         "date"],
         'remarks':     ["证券代码", "公告日期", "股东名称", "股东类型G高管P个人C公司", "类型IN增持DE减持", "变动数量",
                         "占流通比例（%）", "变动后持股", "变动后占流通比例（%）", "平均价格", "持股总数", "增减持开始日期",
                         "增减持结束日期"],
         'prime_keys':  [0, 1]
         },

    'margin':  # New, 融资融券交易概况!
        {'columns':     ["trade_date", "exchange_id", "rzye", "rzmre", "rzche",
                         "rqye", "rqmcl", "rzrqye", "rqyl"],
         'dtypes':      ["date", "varchar(6)", "float", "float", "float",
                         "float", "float", "float", "float"],
         'remarks':     ["交易日期", "交易所代码（SSE上交所SZSE深交所BSE北交所）", "融资余额(元)", "融资买入额(元)", "融资偿还额(元)",
                         "融券余额(元)", "融券卖出量(股,份,手)", "融资融券余额(元)", "融券余量(股,份,手)"],
         'prime_keys':  [0, 1]
         },

    'margin_detail':  # New, 融资融券交易明！
        {'columns':     ["ts_code", "trade_date", "rzye", "rqye", "rzmre", "rqyl",
                         "rzche", "rqchl", "rqmcl", "rzrqye"],
         'dtypes':      ["varchar(14)", "date", "float", "float", "float", "float",
                         "float", "float", "float", "float"],
         'remarks':     ["证券代码", "交易日期", "融资余额(元)", "融券余额(元)", "融资买入额(元)", "融券余量（股）",
                         "融资偿还额(元)", "融券偿还量(股)", "融券卖出量(股,份,手)", "融资融券余额(元)"],
         'prime_keys':  [0, 1]
         },

    'shibor':  # 上海银行间同业拆放利率
        {'columns':    ['date', 'on', '1w', '2w', '1m', '3m', '6m', '9m', '1y'],
         'dtypes':     ['date', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float'],
         'remarks':    ['日期', '隔夜', '1周', '2周', '1个月', '3个月', '6个月', '9个月', '1年'],
         'prime_keys': [0]
         },

    'libor':  # 伦敦银行间同业拆借利率
        {'columns':    ['date', 'curr_type', 'on', '1w', '1m', '2m', '3m', '6m', '12m'],
         'dtypes':     ['date', 'varchar(9)', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float'],
         'remarks':    ['日期', '货币', '隔夜', '1周', '1个月', '2个月', '3个月', '6个月', '12个月'],
         'prime_keys': [0, 1]
         },

    'hibor':  # 香港银行间同业拆借利率
        {'columns':    ['date', 'on', '1w', '2w', '1m', '2m', '3m', '6m', '12m'],
         'dtypes':     ['date', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float'],
         'remarks':    ['日期', '隔夜', '1周', '2周', '1个月', '2个月', '3个月', '6个月', '12个月'],
         'prime_keys': [0]
         },

    'wz_index':  # New, 温州民间借贷指数!
        {'columns':     ["date", "comp_rate", "center_rate", "micro_rate", "cm_rate", "sdb_rate", "om_rate", "aa_rate",
                         "m1_rate", "m3_rate", "m6_rate", "m12_rate", "long_rate"],
         'dtypes':      ["date", "float", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float"],
         'remarks':     ["日期", "温州民间融资综合利率指数 (%，下同)", "民间借贷服务中心利率", "小额贷款公司放款利率", "民间资本管理公司融资价格",
                         "社会直接借贷利率", "其他市场主体利率", "农村互助会互助金费率", "温州地区民间借贷分期限利率（一月期）", "温州地区民间借贷分期限利率（三月期）",
                         "温州地区民间借贷分期限利率（六月期）", "温州地区民间借贷分期限利率（一年期）", "温州地区民间借贷分期限利率（长期）"],
         'prime_keys':  [0]
         },

    'gz_index':  # New, 广州民间借贷指数!
        {'columns':     ["date", "d10_rate", "m1_rate", "m3_rate", "m6_rate", "m12_rate", "long_rate"],
         'dtypes':      ["date", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["日期", "小额贷市场平均利率（十天） （单位：%，下同）", "小额贷市场平均利率（一月期）", "小额贷市场平均利率（三月期）",
                         "小额贷市场平均利率（六月期）", "小额贷市场平均利率（一年期）", "小额贷市场平均利率（长期）"],
         'prime_keys':  [0]
         },

    'cn_gdp':  # New, 国内生产总值季度数据!
        {'columns':     ["quarter", "gdp", "gdp_yoy", "pi", "pi_yoy", "si", "si_yoy", "ti", "ti_yoy"],
         'dtypes':      ["varchar(8)", "float", "float", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["季度", "GDP累计值（亿元）", "当季同比增速（%）", "第一产业累计值（亿元）", "第一产业同比增速（%）",
                         "第二产业累计值（亿元）", "第二产业同比增速（%）", "第三产业累计值（亿元）", "第三产业同比增速（%）"],
         'prime_keys':  [0]
         },

    'cn_cpi':  # New, 居民消费价格指数月度数据!
        {'columns':     ["month", "nt_val", "nt_yoy", "nt_mom", "nt_accu", "town_val", "town_yoy",
                         "town_mom", "town_accu", "cnt_val", "cnt_yoy", "cnt_mom", "cnt_accu"],
         'dtypes':      ["varchar(8)", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float"],
         'remarks':     ["月份YYYYMM", "全国当月值", "全国同比（%）", "全国环比（%）", "全国累计值", "城市当月值", "城市同比（%）",
                         "城市环比（%）", "城市累计值", "农村当月值", "农村同比（%）", "农村环比（%）", "农村累计值"],
         'prime_keys':  [0]
         },

    'cn_ppi':  # New, 工业品出厂价格指数月度数据!
        {'columns':     ["month", "ppi_yoy", "ppi_mp_yoy", "ppi_mp_qm_yoy", "ppi_mp_rm_yoy", "ppi_mp_p_yoy",
                         "ppi_cg_yoy", "ppi_cg_f_yoy", "ppi_cg_c_yoy", "ppi_cg_adu_yoy", "ppi_cg_dcg_yoy", "ppi_mom",
                         "ppi_mp_mom", "ppi_mp_qm_mom", "ppi_mp_rm_mom", "ppi_mp_p_mom", "ppi_cg_mom", "ppi_cg_f_mom",
                         "ppi_cg_c_mom", "ppi_cg_adu_mom", "ppi_cg_dcg_mom", "ppi_accu", "ppi_mp_accu",
                         "ppi_mp_qm_accu", "ppi_mp_rm_accu", "ppi_mp_p_accu", "ppi_cg_accu", "ppi_cg_f_accu",
                         "ppi_cg_c_accu", "ppi_cg_adu_accu", "ppi_cg_dcg_accu"],
         'dtypes':      ["varchar(8)", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float",
                         "float", "float", "float"],
         'remarks':     ["月份YYYYMM", "PPI：全部工业品：当月同比", "PPI：生产资料：当月同比", "PPI：生产资料：采掘业：当月同比",
                         "PPI：生产资料：原料业：当月同比", "PPI：生产资料：加工业：当月同比", "PPI：生活资料：当月同比",
                         "PPI：生活资料：食品类：当月同比", "PPI：生活资料：衣着类：当月同比", "PPI：生活资料：一般日用品类：当月同比",
                         "PPI：生活资料：耐用消费品类：当月同比", "PPI：全部工业品：环比", "PPI：生产资料：环比",
                         "PPI：生产资料：采掘业：环比", "PPI：生产资料：原料业：环比", "PPI：生产资料：加工业：环比",
                         "PPI：生活资料：环比", "PPI：生活资料：食品类：环比", "PPI：生活资料：衣着类：环比",
                         "PPI：生活资料：一般日用品类：环比", "PPI：生活资料：耐用消费品类：环比", "PPI：全部工业品：累计同比",
                         "PPI：生产资料：累计同比", "PPI：生产资料：采掘业：累计同比", "PPI：生产资料：原料业：累计同比",
                         "PPI：生产资料：加工业：累计同比", "PPI：生活资料：累计同比", "PPI：生活资料：食品类：累计同比",
                         "PPI：生活资料：衣着类：累计同比", "PPI：生活资料：一般日用品类：累计同比", "PPI：生活资料：耐用消费品类：累计同比"],
         'prime_keys':  [0]
         },

    'cn_money':  # New, 中国货币供应量!
        {'columns':     ["month", "m0", "m0_yoy", "m0_mom", "m1", "m1_yoy", "m1_mom", "m2", "m2_yoy", "m2_mom"],
         'dtypes':      ["varchar(8)", "float", "float", "float", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["月份YYYYMM", "M0（亿元）", "M0同比（%）", "M0环比（%）", "M1（亿元）", "M1同比（%）", "M1环比（%）",
                         "M2（亿元）", "M2同比（%）", "M2环比（%）"],
         'prime_keys':  [0]
         },

    'cn_sf':  # New, 中国社会融资规模月度数据!
        {'columns':     ["month", "inc_month", "inc_cumval", "stk_endval"],
         'dtypes':      ["varchar(8)", "float", "float", "float"],
         'remarks':     ["月度", "社融增量当月值（亿元）", "社融增量累计值（亿元）", "社融存量期末值（万亿元）"],
         'prime_keys':  [0]
         },

    'cn_pmi':  # New, 采购经理人指数月度数据!
        {'columns':     ["month", "pmi010000", "pmi010100", "pmi010200", "pmi010300", "pmi010400", "pmi010401",
                         "pmi010402", "pmi010403", "pmi010500", "pmi010501", "pmi010502", "pmi010503", "pmi010600",
                         "pmi010601", "pmi010602", "pmi010603", "pmi010700", "pmi010701", "pmi010702", "pmi010703",
                         "pmi010800", "pmi010801", "pmi010802", "pmi010803", "pmi010900", "pmi011000", "pmi011100",
                         "pmi011200", "pmi011300", "pmi011400", "pmi011500", "pmi011600", "pmi011700", "pmi011800",
                         "pmi011900", "pmi012000", "pmi020100", "pmi020101", "pmi020102", "pmi020200", "pmi020201",
                         "pmi020202", "pmi020300", "pmi020301", "pmi020302", "pmi020400", "pmi020401", "pmi020402",
                         "pmi020500", "pmi020501", "pmi020502", "pmi020600", "pmi020601", "pmi020602", "pmi020700",
                         "pmi020800", "pmi020900", "pmi021000", "pmi030000"],
         'dtypes':      ["varchar(8)", "float", "float", "float", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["月份YYYYMM", "制造业PMI", "制造业PMI:企业规模/大型企业", "制造业PMI:企业规模/中型企业",
                         "制造业PMI:企业规模/小型企业", "制造业PMI:构成指数/生产指数", "制造业PMI:构成指数/生产指数:企业规模/大型企业",
                         "制造业PMI:构成指数/生产指数:企业规模/中型企业", "制造业PMI:构成指数/生产指数:企业规模/小型企业",
                         "制造业PMI:构成指数/新订单指数", "制造业PMI:构成指数/新订单指数:企业规模/大型企业",
                         "制造业PMI:构成指数/新订单指数:企业规模/中型企业", "制造业PMI:构成指数/新订单指数:企业规模/小型企业",
                         "制造业PMI:构成指数/供应商配送时间指数", "制造业PMI:构成指数/供应商配送时间指数:企业规模/大型企业",
                         "制造业PMI:构成指数/供应商配送时间指数:企业规模/中型企业", "制造业PMI:构成指数/供应商配送时间指数:企业规模/小型企业",
                         "制造业PMI:构成指数/原材料库存指数", "制造业PMI:构成指数/原材料库存指数:企业规模/大型企业",
                         "制造业PMI:构成指数/原材料库存指数:企业规模/中型企业", "制造业PMI:构成指数/原材料库存指数:企业规模/小型企业",
                         "制造业PMI:构成指数/从业人员指数", "制造业PMI:构成指数/从业人员指数:企业规模/大型企业",
                         "制造业PMI:构成指数/从业人员指数:企业规模/中型企业", "制造业PMI:构成指数/从业人员指数:企业规模/小型企业",
                         "制造业PMI:其他/新出口订单", "制造业PMI:其他/进口", "制造业PMI:其他/采购量", "制造业PMI:其他/主要原材料购进价格",
                         "制造业PMI:其他/出厂价格", "制造业PMI:其他/产成品库存", "制造业PMI:其他/在手订单", "制造业PMI:其他/生产经营活动预期",
                         "制造业PMI:分行业/装备制造业", "制造业PMI:分行业/高技术制造业", "制造业PMI:分行业/基础原材料制造业",
                         "制造业PMI:分行业/消费品制造业", "非制造业PMI:商务活动", "非制造业PMI:商务活动:分行业/建筑业", "非制造业PMI:商务活动:分行业/服务业业",
                         "非制造业PMI:新订单指数", "非制造业PMI:新订单指数:分行业/建筑业", "非制造业PMI:新订单指数:分行业/服务业", "非制造业PMI:投入品价格指数",
                         "非制造业PMI:投入品价格指数:分行业/建筑业", "非制造业PMI:投入品价格指数:分行业/服务业", "非制造业PMI:销售价格指数",
                         "非制造业PMI:销售价格指数:分行业/建筑业", "非制造业PMI:销售价格指数:分行业/服务业", "非制造业PMI:从业人员指数",
                         "非制造业PMI:从业人员指数:分行业/建筑业", "非制造业PMI:从业人员指数:分行业/服务业", "非制造业PMI:业务活动预期指数",
                         "非制造业PMI:业务活动预期指数:分行业/建筑业", "非制造业PMI:业务活动预期指数:分行业/服务业", "非制造业PMI:新出口订单",
                         "非制造业PMI:在手订单", "非制造业PMI:存货", "非制造业PMI:供应商配送时间", "中国综合PMI:产出指数"],
         'prime_keys':  [0]
         },

}


def get_table_map() -> pd.DataFrame:  # deprecated
    """ 获取所有内置数据表的清单，to be deprecated

    Returns
    -------
    pd.DataFrame
    数据表清单
    """
    warnings.warn('get_table_map() is deprecated, use get_table_master() instead', DeprecationWarning)
    return get_table_master()


@lru_cache(maxsize=1)
def get_table_master() -> pd.DataFrame:
    """ 获取所有内置数据表的清单

    Returns
    -------
    table_masters: pd.DataFrame
    数据表清单, 包含以下字段:
    """
    table_master = pd.DataFrame(TABLE_MASTERS).T
    table_master.columns = TABLE_MASTER_COLUMNS
    return table_master


def ensure_sys_table(table: str) -> None:
    """ 检察table是不是sys表

    Parameters
    ----------
    table: str
        表名称

    Returns
    -------
    None

    Raises
    ------
    KeyError: 当输入的表名称不正确时，或筛选条件字段名不存在时
    TypeError: 当输入的表名称类型不正确，或表使用方式不是sys类型时
    """

    # 检察输入的table名称，以及是否属于sys表
    if not isinstance(table, str):
        err = TypeError(f'table name should be a string, got {type(table)} instead.')
        raise err
    try:
        table_usage = TABLE_MASTERS[table][2]
        if not table_usage == 'sys':
            err = TypeError(f'Table {table}<{table_usage}> is not subjected to sys use')
            raise err
    except KeyError as e:
        raise KeyError(f'"{e}" is not a valid table name')
    except Exception as e:
        err = RuntimeError(f'{e}: An error occurred when checking table usage')
        raise err


def get_tables_by_name_or_usage(tables: str or [str],
                                include_sys_tables=False) -> set:
    """ 根据输入的参数，生成需要下载的数据表清单

    Parameters
    ----------
    tables: str or list of str
        数据表名称或用途
    include_sys_tables: bool
        是否包含系统表

    Returns
    -------
    set:
        需要下载的数据表清单
    """

    if isinstance(tables, str):
        tables = str_to_list(tables)

    table_master = get_table_master()

    if include_sys_tables:
        all_tables = table_master.index.to_list()
    else:
        all_tables = table_master.loc[table_master.table_usage != 'sys'].index.to_list()

    table_usages = table_master.table_usage.unique()
    tables_to_refill = set()

    if isinstance(tables, str):
        tables = str_to_list(tables)
    tables = [item.lower() for item in tables]

    if 'all' in tables:
        # add all tables from TABLE_MASTERS
        tables_to_refill.update(all_tables)

    for item in tables:
        if item in all_tables:
            tables_to_refill.add(item)
        elif item in table_usages:
            tables_to_refill.update(
                    table_master.loc[table_master.table_usage == item.lower()].index.to_list()
            )

    return tables_to_refill


# 以下是通用dataframe操作函数
def set_primary_key_index(df, primary_key, pk_dtypes):
    """ df是一个DataFrame，primary key是df的某一列或多列的列名，将primary key所指的
    列设置为df的行标签，设置正确的时间日期格式，并删除primary key列后返回新的df

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的DataFrame
    primary_key: list of str
        需要设置为行标签的列名，所有列名必须出现在df的列名中
    pk_dtypes: list of str
        需要设置为行标签的列的数据类型，日期数据需要小心处理

    Returns
    -------
    None
    """
    if not isinstance(df, pd.DataFrame):
        err = TypeError(f'df should be a pandas DataFrame, got {type(df)} instead')
        raise err
    if df.empty:
        return df
    if not isinstance(primary_key, list):
        err = TypeError(f'primary key should be a list, got {type(primary_key)} instead')
        raise err
    all_columns = df.columns
    if not all(item in all_columns for item in primary_key):
        err = KeyError(f'primary key contains invalid value: '
                       f'{[item for item in primary_key if item not in all_columns]}')
        raise err

    # 设置正确的时间日期格式(找到pk_dtype中是否有"date"或"TimeStamp"类型，将相应的列设置为TimeStamp
    set_datetime_format_frame(df, primary_key, pk_dtypes)

    # 设置正确的Index或MultiIndex
    pk_count = len(primary_key)
    if pk_count == 1:
        # 当primary key只包含一列时，创建single index
        df.index = df[primary_key[0]]
    elif pk_count > 1:
        # 当primary key包含多列时，创建MultiIndex
        m_index = pd.MultiIndex.from_frame(df[primary_key])
        df.index = m_index
    else:
        # for other unexpected cases
        err = ValueError(f'wrong input!')
        raise err
    df.drop(columns=primary_key, inplace=True)

    return None


# noinspection PyUnresolvedReferences
def set_primary_key_frame(df: pd.DataFrame, primary_key: [str], pk_dtypes: [str]) -> pd.DataFrame:
    """ 与set_primary_key_index的功能相反，将index中的值放入DataFrame中，
        并重设df的index为0，1，2，3，4...

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list
        primary key的名称
    pk_dtypes: list
        primary key的数据类型

    Returns
    -------
    df: pd.DataFrame

    Examples
    --------
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df = set_primary_key_frame(df, ['a'], ['int'])
    >>> df
         a  b
    0    1  4
    1    2  5
    2    3  6
    >>> set_primary_key_index(df, ['a'], ['int'])
    >>> df
         b
    a
    1    4
    2    5
    3    6
    """

    if not isinstance(df, pd.DataFrame):
        err = TypeError(f'df should be a pandas DataFrame, got {type(df)} instead')
        raise err
    if df.empty:
        return df
    if not isinstance(primary_key, list):
        err = TypeError(f'primary key should be a list, got {type(primary_key)} instead')
        raise err
    if not isinstance(pk_dtypes, list):
        err = TypeError(f'primary key should be a list, got {type(primary_key)} instead')
        raise err

    all_columns = df.columns.to_list()
    all_columns.extend(df.index.names)
    # 检查primary_key是否能在dataframe的所有column或者index中找到
    if not all(item in all_columns for item in primary_key):
        msg = f'primary key contains invalid value: {[item for item in primary_key if item not in all_columns]}'
        raise KeyError(msg)

    idx_columns = list(df.index.names)
    pk_columns = primary_key

    if idx_columns != [None]:
        # index中有值，需要将index中的值放入DataFrame中
        index_frame = df.index.to_frame()
        for col in idx_columns:
            df[col] = index_frame[col]

    df.index = range(len(df))
    # 此时primary key有可能被放到了columns的最后面，需要将primary key移动到columns的最前面：
    columns = df.columns.to_list()
    new_col = [col for col in columns if col not in pk_columns]
    new_col = pk_columns + new_col
    df = df.reindex(columns=new_col, copy=False)

    # 设置正确的时间日期格式(找到pk_dtype中是否有"date"或"TimeStamp"类型，将相应的列设置为TimeStamp
    set_datetime_format_frame(df, primary_key, pk_dtypes)

    return df


def set_datetime_format_frame(df, primary_key: [str], pk_dtypes: [str]) -> None:
    """ 根据primary_key的rule为df的主键设置正确的时间日期类型

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list of str
        主键列
    pk_dtypes: list of str
        主键数据类型，主要关注"date" 和"TimeStamp"

    Returns
    -------
    None

    Examples
    --------
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df = set_primary_key_frame(df, ['a'], [int])
    >>> df
         a    b
    0    1    4
    1    2    5
    2    3    6
    >>> set_primary_key_index(df, ['a'], ['int'])
    >>> df
         b
    a
    1    4
    2    5
    3    6
    >>> set_datetime_format_frame(df, ['a'], ['date'])
    >>> df
                                     b
    a
    1970-01-01 00:00:00.000000001    4
    1970-01-01 00:00:00.000000002    5
    1970-01-01 00:00:00.000000003    6

    """
    # 设置正确的时间日期格式(找到pk_dtype中是否有"date", "datetime"或"TimeStamp"类型，将相应的列设置为TimeStamp
    datetime_dtypes = ['date', 'datetime', 'TimeStamp']

    if any(dtype in pk_dtypes for dtype in datetime_dtypes):
        # 需要设置正确的时间日期格式：
        # 有时候pk会包含多列，可能有多个时间日期，因此需要逐个设置
        for pk_item, dtype in zip(primary_key, pk_dtypes):
            if dtype in datetime_dtypes:
                df[pk_item] = pd.to_datetime(df[pk_item])
    return None


def get_primary_key_range(df, primary_key: [str], pk_dtypes: [str]) -> dict:
    """ 给定一个dataframe，给出这个df表的主键的范围，用于下载数据时用作传入参数
        如果主键类型为string，则给出一个list，包含所有的元素
        如果主键类型为date，则给出上下界

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list of str
        以列表形式给出的primary_key列名
    pk_dtypes: list of str
        primary_key的数据类型

    Returns
    -------
    dict，形式为{primary_key1: [values], 'start': start_date, 'end': end_date}

    # TODO: 下面的Example由Copilot生成，需要检查
    Examples
    --------
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df
            a  b
    0    1    4
    1    2    5
    2    3    6
    >>> df = set_primary_key_index(df, ['a'], ['int'])
    >>> df
            b
    a
    1    4
    2    5
    3    6
    >>> get_primary_key_range(df, ['a'], ['int'])
    {'shares': [1, 2, 3]}
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df = set_primary_key_frame(df, ['a'], ['date'])
    >>> df
            a  b
    0    1    4
    1    2    5
    2    3    6
    >>> df = set_primary_key_index(df, ['a'], ['date'])
    >>> df
            b
    a
    1970-01-01 00:00:00.000000001    4
    1970-01-01 00:00:00.000000002    5
    1970-01-01 00:00:00.000000003    6
    >>> get_primary_key_range(df, ['a'], ['date'])
    {'start': Timestamp('1970-01-01 00:00:00.000000001'), 'end': Timestamp('1970-01-01 00:00:00.000000003')}

    """
    if df.index.name is not None:
        df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtypes)
    res = {}
    for pk, dtype in zip(primary_key, pk_dtypes):
        if (dtype == 'str') or (dtype[:7] == 'varchar'):
            res['shares'] = (list(set(df[pk].values)))
        elif dtype.lower() in ['date', 'timestamp', 'datetime', 'int', 'float', 'double']:
            res['start'] = df[pk].min()
            res['end'] = df[pk].max()
        else:
            raise KeyError(f'invalid dtype: {dtype}')
    return res


@lru_cache(maxsize=16)
def get_built_in_table_schema(table, *, with_remark=False, with_primary_keys=True) -> tuple:
    """ 给出数据表的名称，从相关TABLE中找到表的主键名称及其数据类型

    Parameters
    ----------
    table:
        str, 表名称(注意不是表的结构名称)
    with_remark: bool
        为True时返回remarks，否则不返回
    with_primary_keys: bool
        为True时返回primary_keys以及primary_key的数据类型，否则不返回

    Returns
    -------
    Tuple: 包含四个List，包括:
        columns: 整张表的列名称
        dtypes: 整张表所有列的数据类型
        primary_keys: 主键列名称
        pk_dtypes: 主键列的数据类型
    """
    if not isinstance(table, str):
        err = TypeError(f'table name should be a string, got {type(table)} instead')
        raise err
    if table not in TABLE_MASTERS.keys():
        raise KeyError(f'invalid table name')

    table_schema = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('schema')]
    schema = TABLE_SCHEMA[table_schema]
    columns = schema['columns']
    dtypes = schema['dtypes']
    remarks = schema['remarks']
    pk_loc = schema['prime_keys']
    primary_keys = [columns[i] for i in pk_loc]
    pk_dtypes = [dtypes[i] for i in pk_loc]

    if (not with_remark) and with_primary_keys:
        return columns, dtypes, primary_keys, pk_dtypes
    if with_remark and (not with_primary_keys):
        return columns, dtypes, remarks
    if (not with_remark) and (not with_primary_keys):
        return columns, dtypes
    if with_remark and with_primary_keys:
        return columns, dtypes, remarks, primary_keys, pk_dtypes


class DataConflictWarning(Warning):
    """ Warning Type: Data conflict detected"""
    pass


class MissingDataWarning(Warning):
    """ Warning Type: Local Data Missing"""
    pass

