# coding=utf-8
# ======================================
# File:     database.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-11-29
# Desc:
#   Local historical data management.
# ======================================
import os
from os import path
import pandas as pd
import warnings

from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache

from .utilfuncs import progress_bar, sec_to_duration, nearest_market_trade_day, input_to_list
from .utilfuncs import is_market_trade_day, str_to_list, regulate_date_format
from .utilfuncs import _wildcard_match, _partial_lev_ratio, _lev_ratio, human_file_size, human_units
from .utilfuncs import freq_dither

AVAILABLE_DATA_FILE_TYPES = ['csv', 'hdf', 'hdf5', 'feather', 'fth']
AVAILABLE_CHANNELS = ['df', 'csv', 'excel', 'tushare']
ADJUSTABLE_PRICE_TYPES = ['open', 'high', 'low', 'close']
TABLE_USAGES = ['sys', 'cal', 'basics', 'data', 'adj', 'events', 'comp', 'report', 'mins']

'''
量化投资研究所需用到各种金融数据，DataSource提供了管理金融数据的方式：

数据表是金融数据在本地存储的逻辑结构，本地的金融数据包含若干张数据表，每张表内保存一类数据
数据表可以在本地以csv等文件形式，也可以以MySQL数据库的形式存储，不论存储方式如何，操作接口都是一致的，只是性能有区别

用户需要任何一种金融数据，只要这种数据存在于本地数据表中，就可以通过引用金融数据的"类型名称"也就是htype来获取
例如，通过"close"获取收盘价，通过"pe"获取市盈率，通过"ebitda"获取息税前利润等。

上述所有的金融数据类型，都存储在不同的数据表中，并且通过一个DATA_TABLE_MAPPING表来索引。

除了这里定义的"内置"数据表以外，用户还可以自定义数据表，自定义数据表的结构直接存储在DataSource的自定义结构表中。
一旦定义好了自定义数据表，其操作方式与内置数据表是一样的。

完整的数据结构由三个字典（表）来定义：
DATA_TABLE_MAP:         定义数据类型与数据表之间的对应关系，以查询每种数据可以再哪一张表里查到
                        每种数据类型都有一个唯一的ID，且每种数据类型都只有一个唯一的存储位置
TABLE_MASTER:           定义数据表的基本属性和下载API来源（目前仅包括tushare，未来会添加其他API)
TABLE_SCHEMAS:          定义数据表的表结构，包括每一列的名称、数据类型、主键以及每一列的说明

1, DATA_TABLE_MAP:

Data table mapping中各列的含义如下：
htype_name(key):            数据类型名称（主键）

freq(key):                  数据的可用频率（主键）
                            1min
                            d
                            w
                            m
                            q
                            
asset_type(key):            数据对应的金融资产类型:
                            E 
                            IDX
                            FT
                            FD
---------------------------------------------------------------------------------------------------------
table_name:                 历史数据所在的表的名称

column:                     历史数据在表中的列名称

description:                历史数据的详细描述，可以用于列搜索
---------------------------------------------------------------------------------------------------------

2, TABLE_MASTER

table source mapping定义了一张数据表的基本属性以及数据来源： 
table_name(key):            数据表的名称（主键）自定义表名称不能与内置表名称重复
---------------------------------------------------------------------------------------------------------
schema:                     数据表的结构名称，根据该名称在TABLE_STRUCTUERS表中可以查到表格包含的所有列、主键、数据类
                            型和详情描述
                            数据表的数据结构存储在不同的数据结构表中，许多表拥有相同的数据结构
                            
desc:                       数据表的中文描述
  
table_usage:                数据表的用途，用于筛选不同的数据表
  
asset_type:                 表内数据对应的资产类型，none表示不对应特定资产类型
  
freq:                       表内数据的频率，如分钟、日、周等
                            设置为'D'、'W'等，用于筛选不同的数据表
                            'none'表示无频率
  
tushare:                    对应的tushare API函数名
  
fill_arg_name:              从tushare下载数据时的关键参数，使用该关键参数来分多次下载完整的数据
                            例如，所有股票所有日期的日K线数据一共有超过1500万行，这些数据无法一次性下载
                            必须分步多次下载。要么每次下载一只股票所有日期的数据，要么下载每天所有股票的数据。
                            -   如果每次下载一只股票的数据，股票的代码就是关键参数，将所有股票的代码依次作为关键参数
                                输入tushare API，就可以下载所有数据
                            -   如果每次下载一天的数据，交易日期就是关键参数，将所有的交易日作为关键参数，也可以下载
                                所有的数据
                            对很多API来说，上述两种方式都是可行的，但是以日期为关键参数的方式更好，因为两个原因：
                            1,  作为关键参数，交易日的数量更少，每年200个交易日，20年的数据也只需要下载4000次，如果
                                使用股票代码，很多证券类型的代码远远超过4000个
                            2,  补充下载数据时更方便，如果过去20年的数据都已经下载好了，仅需要补充下载最新一天的数据
                                如果使用日期作为关键参数，仅下载一次就可以了，如果使用证券代码作为关键参数，需要下载
                                数千次
                            因此，应该尽可能使用日期作为关键参数
                            可惜的是，并不是所有API都支持使用日期作为关键参数，所以，只要能用日期的数据表，都用日期
                            为关键参数，否则采用其他类型的关键参数。
  
fill_arg_type:              关键参数的数据类型，可以为list、table_index、datetime、trade_date，含义分别为：
                            -   list: 
                                列表类型，这个关键参数的取值只能是列表中的某一个元素
                            -   table_index: 
                                表索引，这个关键参数的取值只能是另一张数据表的索引值，这通常表示tushare不支持使用日期
                                作为关键参数，因此必须使用一系列股票或证券代码作为关键参数的值，这些值保存在另一张数据
                                表中，且是这个表的索引值。例如，所有股票的代码就保存在stock_basic表的索引中。
                                
                            -   datetime:
                                日期类型，表示使用日期作为下载数据的关键参数。此时的日期不带时间类型，包含交易日与非
                                交易日
                            -   trade_date:
                                交易日，与日期类型功能相同，但作为关键参数的日期必须为交易日
  
arg_rng:                    关键参数的取值范围，
                            -   如果数据类型为datetime或trade_date，是一个起始日期，表示取值范围从该日期到今日之间
                            -   如果数据类型为table_index，取值范围是一张表，如stock_basic，表示数据从stock_basic的
                                索引中取值
                            -   如果数据类型为list，则直接给出取值范围，如"SSE,SZSE"表示可以取值SSE以及SZSE。
                            
arg_allowed_code_suffix:    table_index类型取值范围的限制值，限制只有特定后缀的证券代码才会被用作参数下载数据。
                            例如，取值"SH,SZ"表示只有以SH、SZ结尾的证券代码才会被用作参数从tushare下载数据。
                            
arg_allow_start_end:        使用table_index类型参数时，是否同时允许传入开始结束日期作为参数。如果设置为"Y"，则会在使用
                            table_index中的代码作为参数下载数据时，同时传入开始和结束日期作为附加参数，否则仅传入代码
                            
start_end_chunk_size:       传入开始结束日期作为附加参数时，是否分块下载。可以设置一个正整数或空字符串如"300"。如果设置了
                            一个正整数字符串，表示一个天数，并将开始结束日期之间的数据分块下载，每个块中数据的时间跨度不超
                            过这个天数。
                            例如，设置该参数为100，则每个分块内的时间跨度不超过100天
---------------------------------------------------------------------------------------------------------

3, TABLE_SCHEMAS:
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
'''
DATA_TABLE_MAP_COLUMNS = ['table_name', 'column', 'description']
DATA_TABLE_MAP_INDEX_NAMES = ['dtype', 'freq', 'asset_type']
DATA_TABLE_MAP = {
    ('chairman', 'd', 'E'):                           ['stock_company', 'chairman', '公司信息 - 法人代表'],
    ('manager', 'd', 'E'):                            ['stock_company', 'manager', '公司信息 - 总经理'],
    ('secretary', 'd', 'E'):                          ['stock_company', 'secretary', '公司信息 - 董秘'],
    ('reg_capital', 'd', 'E'):                        ['stock_company', 'reg_capital', '公司信息 - 注册资本'],
    ('setup_date', 'd', 'E'):                         ['stock_company', 'setup_date', '公司信息 - 注册日期'],
    ('province', 'd', 'E'):                           ['stock_company', 'province', '公司信息 - 所在省份'],
    ('city', 'd', 'E'):                               ['stock_company', 'city', '公司信息 - 所在城市'],
    ('introduction', 'd', 'E'):                       ['stock_company', 'introduction', '公司信息 - 公司介绍'],
    ('website', 'd', 'E'):                            ['stock_company', 'website', '公司信息 - 公司主页'],
    ('email', 'd', 'E'):                              ['stock_company', 'email', '公司信息 - 电子邮件'],
    ('office', 'd', 'E'):                             ['stock_company', 'office', '公司信息 - 办公室'],
    ('employees', 'd', 'E'):                          ['stock_company', 'employees', '公司信息 - 员工人数'],
    ('main_business', 'd', 'E'):                      ['stock_company', 'main_business', '公司信息 - 主要业务及产品'],
    ('business_scope', 'd', 'E'):                     ['stock_company', 'business_scope', '公司信息 - 经营范围'],
    ('manager_name', 'd', 'E'):                       ['stk_managers', 'name', '公司高管信息 - 高管姓名'],
    ('gender', 'd', 'E'):                             ['stk_managers', 'gender', '公司高管信息 - 性别'],
    ('lev', 'd', 'E'):                                ['stk_managers', 'lev', '公司高管信息 - 岗位类别'],
    ('manager_title', 'd', 'E'):                      ['stk_managers', 'title', '公司高管信息 - 岗位'],
    ('edu', 'd', 'E'):                                ['stk_managers', 'edu', '公司高管信息 - 学历'],
    ('national', 'd', 'E'):                           ['stk_managers', 'national', '公司高管信息 - 国籍'],
    ('birthday', 'd', 'E'):                           ['stk_managers', 'birthday', '公司高管信息 - 出生年月'],
    ('begin_date', 'd', 'E'):                         ['stk_managers', 'begin_date', '公司高管信息 - 上任日期'],
    ('end_date', 'd', 'E'):                           ['stk_managers', 'end_date', '公司高管信息 - 离任日期'],
    ('resume', 'd', 'E'):                             ['stk_managers', 'resume', '公司高管信息 - 个人简历'],
    ('manager_salary_name', 'd', 'E'):                ['stk_rewards', 'name', '管理层薪酬 - 姓名'],
    ('manager_salary_title', 'd', 'E'):               ['stk_rewards', 'title', '管理层薪酬 - 职务'],
    ('reward', 'd', 'E'):                             ['stk_rewards', 'reward', '管理层薪酬 - 报酬'],
    ('hold_vol', 'd', 'E'):                           ['stk_rewards', 'hold_vol', '管理层薪酬 - 持股数'],
    ('ipo_date', 'd', 'E'):                           ['new_share', 'ipo_date', '新股上市信息 - 上网发行日期'],
    ('issue_date', 'd', 'E'):                         ['new_share', 'issue_date', '新股上市信息 - 上市日期'],
    ('IPO_amount', 'd', 'E'):                         ['new_share', 'amount', '新股上市信息 - 发行总量（万股）'],
    ('market_amount', 'd', 'E'):                      ['new_share', 'market_amount',
                                                       '新股上市信息 - 上网发行总量（万股）'],
    ('initial_price', 'd', 'E'):                      ['new_share', 'price', '新股上市信息 - 发行价格'],
    ('initial_pe', 'd', 'E'):                         ['new_share', 'pe', '新股上市信息 - 发行市盈率'],
    ('limit_amount', 'd', 'E'):                       ['new_share', 'limit_amount',
                                                       '新股上市信息 - 个人申购上限（万股）'],
    ('funds', 'd', 'E'):                              ['new_share', 'funds', '新股上市信息 - 募集资金（亿元）'],
    ('ballot', 'd', 'E'):                             ['new_share', 'ballot', '新股上市信息 - 中签率'],
    ('open', 'd', 'E'):                               ['stock_daily', 'open', '股票日K线 - 开盘价'],
    ('high', 'd', 'E'):                               ['stock_daily', 'high', '股票日K线 - 最高价'],
    ('low', 'd', 'E'):                                ['stock_daily', 'low', '股票日K线 - 最低价'],
    ('close', 'd', 'E'):                              ['stock_daily', 'close', '股票日K线 - 收盘价'],
    ('vol', 'd', 'E'):                                ['stock_daily', 'vol', '股票日K线 - 成交量 （手）'],
    ('amount', 'd', 'E'):                             ['stock_daily', 'amount', '股票日K线 - 成交额 （千元）'],
    ('open', 'w', 'E'):                               ['stock_weekly', 'open', '股票周K线 - 开盘价'],
    ('high', 'w', 'E'):                               ['stock_weekly', 'high', '股票周K线 - 最高价'],
    ('low', 'w', 'E'):                                ['stock_weekly', 'low', '股票周K线 - 最低价'],
    ('close', 'w', 'E'):                              ['stock_weekly', 'close', '股票周K线 - 收盘价'],
    ('vol', 'w', 'E'):                                ['stock_weekly', 'vol', '股票周K线 - 成交量 （手）'],
    ('amount', 'w', 'E'):                             ['stock_weekly', 'amount', '股票周K线 - 成交额 （千元）'],
    ('open', 'm', 'E'):                               ['stock_monthly', 'open', '股票月K线 - 开盘价'],
    ('high', 'm', 'E'):                               ['stock_monthly', 'high', '股票月K线 - 最高价'],
    ('low', 'm', 'E'):                                ['stock_monthly', 'low', '股票月K线 - 最低价'],
    ('close', 'm', 'E'):                              ['stock_monthly', 'close', '股票月K线 - 收盘价'],
    ('vol', 'm', 'E'):                                ['stock_monthly', 'vol', '股票月K线 - 成交量 （手）'],
    ('amount', 'm', 'E'):                             ['stock_monthly', 'amount', '股票月K线 - 成交额 （千元）'],
    ('open', '1min', 'E'):                            ['stock_1min', 'open', '股票60秒K线 - 开盘价'],
    ('high', '1min', 'E'):                            ['stock_1min', 'high', '股票60秒K线 - 最高价'],
    ('low', '1min', 'E'):                             ['stock_1min', 'low', '股票60秒K线 - 最低价'],
    ('close', '1min', 'E'):                           ['stock_1min', 'close', '股票60秒K线 - 收盘价'],
    ('vol', '1min', 'E'):                             ['stock_1min', 'vol', '股票60秒K线 - 成交量 （手）'],
    ('amount', '1min', 'E'):                          ['stock_1min', 'amount', '股票60秒K线 - 成交额 （千元）'],
    ('open', '5min', 'E'):                            ['stock_5min', 'open', '股票5分钟K线 - 开盘价'],
    ('high', '5min', 'E'):                            ['stock_5min', 'high', '股票5分钟K线 - 最高价'],
    ('low', '5min', 'E'):                             ['stock_5min', 'low', '股票5分钟K线 - 最低价'],
    ('close', '5min', 'E'):                           ['stock_5min', 'close', '股票5分钟K线 - 收盘价'],
    ('vol', '5min', 'E'):                             ['stock_5min', 'vol', '股票5分钟K线 - 成交量 （手）'],
    ('amount', '5min', 'E'):                          ['stock_5min', 'amount', '股票5分钟K线 - 成交额 （千元）'],
    ('open', '15min', 'E'):                           ['stock_15min', 'open', '股票15分钟K线 - 开盘价'],
    ('high', '15min', 'E'):                           ['stock_15min', 'high', '股票15分钟K线 - 最高价'],
    ('low', '15min', 'E'):                            ['stock_15min', 'low', '股票15分钟K线 - 最低价'],
    ('close', '15min', 'E'):                          ['stock_15min', 'close', '股票15分钟K线 - 收盘价'],
    ('vol', '15min', 'E'):                            ['stock_15min', 'vol', '股票15分钟K线 - 成交量 （手）'],
    ('amount', '15min', 'E'):                         ['stock_15min', 'amount', '股票15分钟K线 - 成交额 （千元）'],
    ('open', '30min', 'E'):                           ['stock_30min', 'open', '股票30分钟K线 - 开盘价'],
    ('high', '30min', 'E'):                           ['stock_30min', 'high', '股票30分钟K线 - 最高价'],
    ('low', '30min', 'E'):                            ['stock_30min', 'low', '股票30分钟K线 - 最低价'],
    ('close', '30min', 'E'):                          ['stock_30min', 'close', '股票30分钟K线 - 收盘价'],
    ('vol', '30min', 'E'):                            ['stock_30min', 'vol', '股票30分钟K线 - 成交量 （手）'],
    ('amount', '30min', 'E'):                         ['stock_30min', 'amount', '股票30分钟K线 - 成交额 （千元）'],
    ('open', 'h', 'E'):                               ['stock_hourly', 'open', '股票小时K线 - 开盘价'],
    ('high', 'h', 'E'):                               ['stock_hourly', 'high', '股票小时K线 - 最高价'],
    ('low', 'h', 'E'):                                ['stock_hourly', 'low', '股票小时K线 - 最低价'],
    ('close', 'h', 'E'):                              ['stock_hourly', 'close', '股票小时K线 - 收盘价'],
    ('vol', 'h', 'E'):                                ['stock_hourly', 'vol', '股票小时K线 - 成交量 （手）'],
    ('amount', 'h', 'E'):                             ['stock_hourly', 'amount', '股票小时K线 - 成交额 （千元）'],
    ('open', 'd', 'IDX'):                             ['index_daily', 'open', '指数日K线 - 开盘价'],
    ('high', 'd', 'IDX'):                             ['index_daily', 'high', '指数日K线 - 最高价'],
    ('low', 'd', 'IDX'):                              ['index_daily', 'low', '指数日K线 - 最低价'],
    ('close', 'd', 'IDX'):                            ['index_daily', 'close', '指数日K线 - 收盘价'],
    ('vol', 'd', 'IDX'):                              ['index_daily', 'vol', '指数日K线 - 成交量 （手）'],
    ('amount', 'd', 'IDX'):                           ['index_daily', 'amount', '指数日K线 - 成交额 （千元）'],
    ('open', 'w', 'IDX'):                             ['index_weekly', 'open', '指数周K线 - 开盘价'],
    ('high', 'w', 'IDX'):                             ['index_weekly', 'high', '指数周K线 - 最高价'],
    ('low', 'w', 'IDX'):                              ['index_weekly', 'low', '指数周K线 - 最低价'],
    ('close', 'w', 'IDX'):                            ['index_weekly', 'close', '指数周K线 - 收盘价'],
    ('vol', 'w', 'IDX'):                              ['index_weekly', 'vol', '指数周K线 - 成交量 （手）'],
    ('amount', 'w', 'IDX'):                           ['index_weekly', 'amount', '指数周K线 - 成交额 （千元）'],
    ('open', 'm', 'IDX'):                             ['index_monthly', 'open', '指数月K线 - 开盘价'],
    ('high', 'm', 'IDX'):                             ['index_monthly', 'high', '指数月K线 - 最高价'],
    ('low', 'm', 'IDX'):                              ['index_monthly', 'low', '指数月K线 - 最低价'],
    ('close', 'm', 'IDX'):                            ['index_monthly', 'close', '指数月K线 - 收盘价'],
    ('vol', 'm', 'IDX'):                              ['index_monthly', 'vol', '指数月K线 - 成交量 （手）'],
    ('amount', 'm', 'IDX'):                           ['index_monthly', 'amount', '指数月K线 - 成交额 （千元）'],
    ('open', '1min', 'IDX'):                          ['index_1min', 'open', '指数60秒K线 - 开盘价'],
    ('high', '1min', 'IDX'):                          ['index_1min', 'high', '指数60秒K线 - 最高价'],
    ('low', '1min', 'IDX'):                           ['index_1min', 'low', '指数60秒K线 - 最低价'],
    ('close', '1min', 'IDX'):                         ['index_1min', 'close', '指数60秒K线 - 收盘价'],
    ('vol', '1min', 'IDX'):                           ['index_1min', 'vol', '指数60秒K线 - 成交量 （手）'],
    ('amount', '1min', 'IDX'):                        ['index_1min', 'amount', '指数60秒K线 - 成交额 （千元）'],
    ('open', '5min', 'IDX'):                          ['index_5min', 'open', '指数5分钟K线 - 开盘价'],
    ('high', '5min', 'IDX'):                          ['index_5min', 'high', '指数5分钟K线 - 最高价'],
    ('low', '5min', 'IDX'):                           ['index_5min', 'low', '指数5分钟K线 - 最低价'],
    ('close', '5min', 'IDX'):                         ['index_5min', 'close', '指数5分钟K线 - 收盘价'],
    ('vol', '5min', 'IDX'):                           ['index_5min', 'vol', '指数5分钟K线 - 成交量 （手）'],
    ('amount', '5min', 'IDX'):                        ['index_5min', 'amount', '指数5分钟K线 - 成交额 （千元）'],
    ('open', '15min', 'IDX'):                         ['index_15min', 'open', '指数15分钟K线 - 开盘价'],
    ('high', '15min', 'IDX'):                         ['index_15min', 'high', '指数15分钟K线 - 最高价'],
    ('low', '15min', 'IDX'):                          ['index_15min', 'low', '指数15分钟K线 - 最低价'],
    ('close', '15min', 'IDX'):                        ['index_15min', 'close', '指数15分钟K线 - 收盘价'],
    ('vol', '15min', 'IDX'):                          ['index_15min', 'vol', '指数15分钟K线 - 成交量 （手）'],
    ('amount', '15min', 'IDX'):                       ['index_15min', 'amount', '指数15分钟K线 - 成交额 （千元）'],
    ('open', '30min', 'IDX'):                         ['index_30min', 'open', '指数30分钟K线 - 开盘价'],
    ('high', '30min', 'IDX'):                         ['index_30min', 'high', '指数30分钟K线 - 最高价'],
    ('low', '30min', 'IDX'):                          ['index_30min', 'low', '指数30分钟K线 - 最低价'],
    ('close', '30min', 'IDX'):                        ['index_30min', 'close', '指数30分钟K线 - 收盘价'],
    ('vol', '30min', 'IDX'):                          ['index_30min', 'vol', '指数30分钟K线 - 成交量 （手）'],
    ('amount', '30min', 'IDX'):                       ['index_30min', 'amount', '指数30分钟K线 - 成交额 （千元）'],
    ('open', 'h', 'IDX'):                             ['index_hourly', 'open', '指数小时K线 - 开盘价'],
    ('high', 'h', 'IDX'):                             ['index_hourly', 'high', '指数小时K线 - 最高价'],
    ('low', 'h', 'IDX'):                              ['index_hourly', 'low', '指数小时K线 - 最低价'],
    ('close', 'h', 'IDX'):                            ['index_hourly', 'close', '指数小时K线 - 收盘价'],
    ('vol', 'h', 'IDX'):                              ['index_hourly', 'vol', '指数小时K线 - 成交量 （手）'],
    ('amount', 'h', 'IDX'):                           ['index_hourly', 'amount', '指数小时K线 - 成交额 （千元）'],
    ('open', 'd', 'FT'):                              ['future_daily', 'open', '期货日K线 - 开盘价'],
    ('high', 'd', 'FT'):                              ['future_daily', 'high', '期货日K线 - 最高价'],
    ('low', 'd', 'FT'):                               ['future_daily', 'low', '期货日K线 - 最低价'],
    ('close', 'd', 'FT'):                             ['future_daily', 'close', '期货日K线 - 收盘价'],
    ('vol', 'd', 'FT'):                               ['future_daily', 'vol', '期货日K线 - 成交量 （手）'],
    ('amount', 'd', 'FT'):                            ['future_daily', 'amount', '期货日K线 - 成交额 （千元）'],
    ('open', '1min', 'FT'):                           ['future_1min', 'open', '期货60秒K线 - 开盘价'],
    ('high', '1min', 'FT'):                           ['future_1min', 'high', '期货60秒K线 - 最高价'],
    ('low', '1min', 'FT'):                            ['future_1min', 'low', '期货60秒K线 - 最低价'],
    ('close', '1min', 'FT'):                          ['future_1min', 'close', '期货60秒K线 - 收盘价'],
    ('vol', '1min', 'FT'):                            ['future_1min', 'vol', '期货60秒K线 - 成交量 （手）'],
    ('amount', '1min', 'FT'):                         ['future_1min', 'amount', '期货60秒K线 - 成交额 （千元）'],
    ('open', '5min', 'FT'):                           ['future_5min', 'open', '期货5分钟K线 - 开盘价'],
    ('high', '5min', 'FT'):                           ['future_5min', 'high', '期货5分钟K线 - 最高价'],
    ('low', '5min', 'FT'):                            ['future_5min', 'low', '期货5分钟K线 - 最低价'],
    ('close', '5min', 'FT'):                          ['future_5min', 'close', '期货5分钟K线 - 收盘价'],
    ('vol', '5min', 'FT'):                            ['future_5min', 'vol', '期货5分钟K线 - 成交量 （手）'],
    ('amount', '5min', 'FT'):                         ['future_5min', 'amount', '期货5分钟K线 - 成交额 （千元）'],
    ('open', '15min', 'FT'):                          ['future_15min', 'open', '期货15分钟K线 - 开盘价'],
    ('high', '15min', 'FT'):                          ['future_15min', 'high', '期货15分钟K线 - 最高价'],
    ('low', '15min', 'FT'):                           ['future_15min', 'low', '期货15分钟K线 - 最低价'],
    ('close', '15min', 'FT'):                         ['future_15min', 'close', '期货15分钟K线 - 收盘价'],
    ('vol', '15min', 'FT'):                           ['future_15min', 'vol', '期货15分钟K线 - 成交量 （手）'],
    ('amount', '15min', 'FT'):                        ['future_15min', 'amount', '期货15分钟K线 - 成交额 （千元）'],
    ('open', '30min', 'FT'):                          ['future_30min', 'open', '期货30分钟K线 - 开盘价'],
    ('high', '30min', 'FT'):                          ['future_30min', 'high', '期货30分钟K线 - 最高价'],
    ('low', '30min', 'FT'):                           ['future_30min', 'low', '期货30分钟K线 - 最低价'],
    ('close', '30min', 'FT'):                         ['future_30min', 'close', '期货30分钟K线 - 收盘价'],
    ('vol', '30min', 'FT'):                           ['future_30min', 'vol', '期货30分钟K线 - 成交量 （手）'],
    ('amount', '30min', 'FT'):                        ['future_30min', 'amount', '期货30分钟K线 - 成交额 （千元）'],
    ('open', 'h', 'FT'):                              ['future_hourly', 'open', '期货小时K线 - 开盘价'],
    ('high', 'h', 'FT'):                              ['future_hourly', 'high', '期货小时K线 - 最高价'],
    ('low', 'h', 'FT'):                               ['future_hourly', 'low', '期货小时K线 - 最低价'],
    ('close', 'h', 'FT'):                             ['future_hourly', 'close', '期货小时K线 - 收盘价'],
    ('vol', 'h', 'FT'):                               ['future_hourly', 'vol', '期货小时K线 - 成交量 （手）'],
    ('amount', 'h', 'FT'):                            ['future_hourly', 'amount', '期货小时K线 - 成交额 （千元）'],
    ('open', 'd', 'OPT'):                             ['options_daily', 'open', '期权日K线 - 开盘价'],
    ('high', 'd', 'OPT'):                             ['options_daily', 'high', '期权日K线 - 最高价'],
    ('low', 'd', 'OPT'):                              ['options_daily', 'low', '期权日K线 - 最低价'],
    ('close', 'd', 'OPT'):                            ['options_daily', 'close', '期权日K线 - 收盘价'],
    ('vol', 'd', 'OPT'):                              ['options_daily', 'vol', '期权日K线 - 成交量 （手）'],
    ('amount', 'd', 'OPT'):                           ['options_daily', 'amount', '期权日K线 - 成交额 （千元）'],
    ('open', '1min', 'OPT'):                          ['options_1min', 'open', '期权60秒K线 - 开盘价'],
    ('high', '1min', 'OPT'):                          ['options_1min', 'high', '期权60秒K线 - 最高价'],
    ('low', '1min', 'OPT'):                           ['options_1min', 'low', '期权60秒K线 - 最低价'],
    ('close', '1min', 'OPT'):                         ['options_1min', 'close', '期权60秒K线 - 收盘价'],
    ('vol', '1min', 'OPT'):                           ['options_1min', 'vol', '期权60秒K线 - 成交量 （手）'],
    ('amount', '1min', 'OPT'):                        ['options_1min', 'amount', '期权60秒K线 - 成交额 （千元）'],
    ('open', '5min', 'OPT'):                          ['options_5min', 'open', '期权5分钟K线 - 开盘价'],
    ('high', '5min', 'OPT'):                          ['options_5min', 'high', '期权5分钟K线 - 最高价'],
    ('low', '5min', 'OPT'):                           ['options_5min', 'low', '期权5分钟K线 - 最低价'],
    ('close', '5min', 'OPT'):                         ['options_5min', 'close', '期权5分钟K线 - 收盘价'],
    ('vol', '5min', 'OPT'):                           ['options_5min', 'vol', '期权5分钟K线 - 成交量 （手）'],
    ('amount', '5min', 'OPT'):                        ['options_5min', 'amount', '期权5分钟K线 - 成交额 （千元）'],
    ('open', '15min', 'OPT'):                         ['options_15min', 'open', '期权15分钟K线 - 开盘价'],
    ('high', '15min', 'OPT'):                         ['options_15min', 'high', '期权15分钟K线 - 最高价'],
    ('low', '15min', 'OPT'):                          ['options_15min', 'low', '期权15分钟K线 - 最低价'],
    ('close', '15min', 'OPT'):                        ['options_15min', 'close', '期权15分钟K线 - 收盘价'],
    ('vol', '15min', 'OPT'):                          ['options_15min', 'vol', '期权15分钟K线 - 成交量 （手）'],
    ('amount', '15min', 'OPT'):                       ['options_15min', 'amount', '期权15分钟K线 - 成交额 （千元）'],
    ('open', '30min', 'OPT'):                         ['options_30min', 'open', '期权30分钟K线 - 开盘价'],
    ('high', '30min', 'OPT'):                         ['options_30min', 'high', '期权30分钟K线 - 最高价'],
    ('low', '30min', 'OPT'):                          ['options_30min', 'low', '期权30分钟K线 - 最低价'],
    ('close', '30min', 'OPT'):                        ['options_30min', 'close', '期权30分钟K线 - 收盘价'],
    ('vol', '30min', 'OPT'):                          ['options_30min', 'vol', '期权30分钟K线 - 成交量 （手）'],
    ('amount', '30min', 'OPT'):                       ['options_30min', 'amount', '期权30分钟K线 - 成交额 （千元）'],
    ('open', 'h', 'OPT'):                             ['options_hourly', 'open', '期权小时K线 - 开盘价'],
    ('high', 'h', 'OPT'):                             ['options_hourly', 'high', '期权小时K线 - 最高价'],
    ('low', 'h', 'OPT'):                              ['options_hourly', 'low', '期权小时K线 - 最低价'],
    ('close', 'h', 'OPT'):                            ['options_hourly', 'close', '期权小时K线 - 收盘价'],
    ('vol', 'h', 'OPT'):                              ['options_hourly', 'vol', '期权小时K线 - 成交量 （手）'],
    ('amount', 'h', 'OPT'):                           ['options_hourly', 'amount', '期权小时K线 - 成交额 （千元）'],
    ('open', 'd', 'FD'):                              ['fund_daily', 'open', '基金日K线 - 开盘价'],
    ('high', 'd', 'FD'):                              ['fund_daily', 'high', '基金日K线 - 最高价'],
    ('low', 'd', 'FD'):                               ['fund_daily', 'low', '基金日K线 - 最低价'],
    ('close', 'd', 'FD'):                             ['fund_daily', 'close', '基金日K线 - 收盘价'],
    ('vol', 'd', 'FD'):                               ['fund_daily', 'vol', '基金日K线 - 成交量 （手）'],
    ('amount', 'd', 'FD'):                            ['fund_daily', 'amount', '基金日K线 - 成交额 （千元）'],
    ('open', '1min', 'FD'):                           ['fund_1min', 'open', '基金60秒K线 - 开盘价'],
    ('high', '1min', 'FD'):                           ['fund_1min', 'high', '基金60秒K线 - 最高价'],
    ('low', '1min', 'FD'):                            ['fund_1min', 'low', '基金60秒K线 - 最低价'],
    ('close', '1min', 'FD'):                          ['fund_1min', 'close', '基金60秒K线 - 收盘价'],
    ('vol', '1min', 'FD'):                            ['fund_1min', 'vol', '基金60秒K线 - 成交量 （手）'],
    ('amount', '1min', 'FD'):                         ['fund_1min', 'amount', '基金60秒K线 - 成交额 （千元）'],
    ('open', '5min', 'FD'):                           ['fund_5min', 'open', '基金5分钟K线 - 开盘价'],
    ('high', '5min', 'FD'):                           ['fund_5min', 'high', '基金5分钟K线 - 最高价'],
    ('low', '5min', 'FD'):                            ['fund_5min', 'low', '基金5分钟K线 - 最低价'],
    ('close', '5min', 'FD'):                          ['fund_5min', 'close', '基金5分钟K线 - 收盘价'],
    ('vol', '5min', 'FD'):                            ['fund_5min', 'vol', '基金5分钟K线 - 成交量 （手）'],
    ('amount', '5min', 'FD'):                         ['fund_5min', 'amount', '基金5分钟K线 - 成交额 （千元）'],
    ('open', '15min', 'FD'):                          ['fund_15min', 'open', '基金15分钟K线 - 开盘价'],
    ('high', '15min', 'FD'):                          ['fund_15min', 'high', '基金15分钟K线 - 最高价'],
    ('low', '15min', 'FD'):                           ['fund_15min', 'low', '基金15分钟K线 - 最低价'],
    ('close', '15min', 'FD'):                         ['fund_15min', 'close', '基金15分钟K线 - 收盘价'],
    ('vol', '15min', 'FD'):                           ['fund_15min', 'vol', '基金15分钟K线 - 成交量 （手）'],
    ('amount', '15min', 'FD'):                        ['fund_15min', 'amount', '基金15分钟K线 - 成交额 （千元）'],
    ('open', '30min', 'FD'):                          ['fund_30min', 'open', '基金30分钟K线 - 开盘价'],
    ('high', '30min', 'FD'):                          ['fund_30min', 'high', '基金30分钟K线 - 最高价'],
    ('low', '30min', 'FD'):                           ['fund_30min', 'low', '基金30分钟K线 - 最低价'],
    ('close', '30min', 'FD'):                         ['fund_30min', 'close', '基金30分钟K线 - 收盘价'],
    ('vol', '30min', 'FD'):                           ['fund_30min', 'vol', '基金30分钟K线 - 成交量 （手）'],
    ('amount', '30min', 'FD'):                        ['fund_30min', 'amount', '基金30分钟K线 - 成交额 （千元）'],
    ('open', 'h', 'FD'):                              ['fund_hourly', 'open', '基金小时K线 - 开盘价'],
    ('high', 'h', 'FD'):                              ['fund_hourly', 'high', '基金小时K线 - 最高价'],
    ('low', 'h', 'FD'):                               ['fund_hourly', 'low', '基金小时K线 - 最低价'],
    ('close', 'h', 'FD'):                             ['fund_hourly', 'close', '基金小时K线 - 收盘价'],
    ('vol', 'h', 'FD'):                               ['fund_hourly', 'vol', '基金小时K线 - 成交量 （手）'],
    ('amount', 'h', 'FD'):                            ['fund_hourly', 'amount', '基金小时K线 - 成交额 （千元）'],
    ('unit_nav', 'd', 'FD'):                          ['fund_nav', 'unit_nav', '基金净值 - 单位净值'],
    ('accum_nav', 'd', 'FD'):                         ['fund_nav', 'accum_nav', '基金净值 - 累计净值'],
    ('accum_div', 'd', 'FD'):                         ['fund_nav', 'accum_div', '基金净值 - 累计分红'],
    ('net_asset', 'd', 'FD'):                         ['fund_nav', 'net_asset', '基金净值 - 资产净值'],
    ('total_netasset', 'd', 'FD'):                    ['fund_nav', 'total_netasset', '基金净值 - 累计资产净值'],
    ('adj_nav', 'd', 'FD'):                           ['fund_nav', 'adj_nav', '基金净值 - 复权净值'],
    ('buy_sm_vol', 'd', 'E'):                         ['money_flow', 'buy_sm_vol', '个股资金流向 - 小单买入量（手）'],
    ('buy_sm_amount', 'd', 'E'):                      ['money_flow', 'buy_sm_amount',
                                                       '个股资金流向 - 小单买入金额（万元）'],
    ('sell_sm_vol', 'd', 'E'):                        ['money_flow', 'sell_sm_vol', '个股资金流向 - 小单卖出量（手）'],
    ('sell_sm_amount', 'd', 'E'):                     ['money_flow', 'sell_sm_amount',
                                                       '个股资金流向 - 小单卖出金额（万元）'],
    ('buy_md_vol', 'd', 'E'):                         ['money_flow', 'buy_md_vol', '个股资金流向 - 中单买入量（手）'],
    ('buy_md_amount', 'd', 'E'):                      ['money_flow', 'buy_md_amount',
                                                       '个股资金流向 - 中单买入金额（万元）'],
    ('sell_md_vol', 'd', 'E'):                        ['money_flow', 'sell_md_vol', '个股资金流向 - 中单卖出量（手）'],
    ('sell_md_amount', 'd', 'E'):                     ['money_flow', 'sell_md_amount',
                                                       '个股资金流向 - 中单卖出金额（万元）'],
    ('buy_lg_vol', 'd', 'E'):                         ['money_flow', 'buy_lg_vol', '个股资金流向 - 大单买入量（手）'],
    ('buy_lg_amount', 'd', 'E'):                      ['money_flow', 'buy_lg_amount',
                                                       '个股资金流向 - 大单买入金额（万元）'],
    ('sell_lg_vol', 'd', 'E'):                        ['money_flow', 'sell_lg_vol', '个股资金流向 - 大单卖出量（手）'],
    ('sell_lg_amount', 'd', 'E'):                     ['money_flow', 'sell_lg_amount',
                                                       '个股资金流向 - 大单卖出金额（万元）'],
    ('buy_elg_vol', 'd', 'E'):                        ['money_flow', 'buy_elg_vol', '个股资金流向 - 特大单买入量（手）'],
    ('buy_elg_amount', 'd', 'E'):                     ['money_flow', 'buy_elg_amount',
                                                       '个股资金流向 - 特大单买入金额（万元）'],
    ('sell_elg_vol', 'd', 'E'):                       ['money_flow', 'sell_elg_vol', '个股资金流向 - 特大单卖出量（手）'],
    ('sell_elg_amount', 'd', 'E'):                    ['money_flow', 'sell_elg_amount',
                                                       '个股资金流向 - 特大单卖出金额（万元）'],
    ('net_mf_vol', 'd', 'E'):                         ['money_flow', 'net_mf_vol', '个股资金流向 - 净流入量（手）'],
    ('net_mf_amount', 'd', 'E'):                      ['money_flow', 'net_mf_amount', '个股资金流向 - 净流入额（万元）'],
    ('ggt_ss', 'd', 'Any'):                           ['moneyflow_hsgt', 'ggt_ss', '沪深港通资金流向 - 港股通（上海）'],
    ('ggt_sz', 'd', 'Any'):                           ['moneyflow_hsgt', 'ggt_sz', '沪深港通资金流向 - 港股通（深圳）'],
    ('hgt', 'd', 'Any'):                              ['moneyflow_hsgt', 'hgt', '沪深港通资金流向 - 沪股通（百万元）'],
    ('sgt', 'd', 'Any'):                              ['moneyflow_hsgt', 'sgt', '沪深港通资金流向 - 深股通（百万元）'],
    ('north_money', 'd', 'Any'):                      ['moneyflow_hsgt', 'north_money',
                                                       '沪深港通资金流向 - 北向资金（百万元）'],
    ('south_money', 'd', 'Any'):                      ['moneyflow_hsgt', 'south_money',
                                                       '沪深港通资金流向 - 南向资金（百万元）'],
    ('basic_eps', 'q', 'E'):                          ['income', 'basic_eps', '上市公司利润表 - 基本每股收益'],
    ('diluted_eps', 'q', 'E'):                        ['income', 'diluted_eps', '上市公司利润表 - 稀释每股收益'],
    ('total_revenue', 'q', 'E'):                      ['income', 'total_revenue', '上市公司利润表 - 营业总收入'],
    ('revenue', 'q', 'E'):                            ['income', 'revenue', '上市公司利润表 - 营业收入'],
    ('int_income', 'q', 'E'):                         ['income', 'int_income', '上市公司利润表 - 利息收入'],
    ('prem_earned', 'q', 'E'):                        ['income', 'prem_earned', '上市公司利润表 - 已赚保费'],
    ('comm_income', 'q', 'E'):                        ['income', 'comm_income', '上市公司利润表 - 手续费及佣金收入'],
    ('n_commis_income', 'q', 'E'):                    ['income', 'n_commis_income',
                                                       '上市公司利润表 - 手续费及佣金净收入'],
    ('n_oth_income', 'q', 'E'):                       ['income', 'n_oth_income', '上市公司利润表 - 其他经营净收益'],
    ('n_oth_b_income', 'q', 'E'):                     ['income', 'n_oth_b_income',
                                                       '上市公司利润表 - 加:其他业务净收益'],
    ('prem_income', 'q', 'E'):                        ['income', 'prem_income', '上市公司利润表 - 保险业务收入'],
    ('out_prem', 'q', 'E'):                           ['income', 'out_prem', '上市公司利润表 - 减:分出保费'],
    ('une_prem_reser', 'q', 'E'):                     ['income', 'une_prem_reser',
                                                       '上市公司利润表 - 提取未到期责任准备金'],
    ('reins_income', 'q', 'E'):                       ['income', 'reins_income', '上市公司利润表 - 其中:分保费收入'],
    ('n_sec_tb_income', 'q', 'E'):                    ['income', 'n_sec_tb_income',
                                                       '上市公司利润表 - 代理买卖证券业务净收入'],
    ('n_sec_uw_income', 'q', 'E'):                    ['income', 'n_sec_uw_income',
                                                       '上市公司利润表 - 证券承销业务净收入'],
    ('n_asset_mg_income', 'q', 'E'):                  ['income', 'n_asset_mg_income',
                                                       '上市公司利润表 - 受托客户资产管理业务净收入'],
    ('oth_b_income', 'q', 'E'):                       ['income', 'oth_b_income', '上市公司利润表 - 其他业务收入'],
    ('fv_value_chg_gain', 'q', 'E'):                  ['income', 'fv_value_chg_gain',
                                                       '上市公司利润表 - 加:公允价值变动净收益'],
    ('invest_income', 'q', 'E'):                      ['income', 'invest_income', '上市公司利润表 - 加:投资净收益'],
    ('ass_invest_income', 'q', 'E'):                  ['income', 'ass_invest_income',
                                                       '上市公司利润表 - 其中:对联营企业和合营企业的投资收益'],
    ('forex_gain', 'q', 'E'):                         ['income', 'forex_gain', '上市公司利润表 - 加:汇兑净收益'],
    ('total_cogs', 'q', 'E'):                         ['income', 'total_cogs', '上市公司利润表 - 营业总成本'],
    ('oper_cost', 'q', 'E'):                          ['income', 'oper_cost', '上市公司利润表 - 减:营业成本'],
    ('int_exp', 'q', 'E'):                            ['income', 'int_exp', '上市公司利润表 - 减:利息支出'],
    ('comm_exp', 'q', 'E'):                           ['income', 'comm_exp', '上市公司利润表 - 减:手续费及佣金支出'],
    ('biz_tax_surchg', 'q', 'E'):                     ['income', 'biz_tax_surchg',
                                                       '上市公司利润表 - 减:营业税金及附加'],
    ('sell_exp', 'q', 'E'):                           ['income', 'sell_exp', '上市公司利润表 - 减:销售费用'],
    ('admin_exp', 'q', 'E'):                          ['income', 'admin_exp', '上市公司利润表 - 减:管理费用'],
    ('fin_exp', 'q', 'E'):                            ['income', 'fin_exp', '上市公司利润表 - 减:财务费用'],
    ('assets_impair_loss', 'q', 'E'):                 ['income', 'assets_impair_loss',
                                                       '上市公司利润表 - 减:资产减值损失'],
    ('prem_refund', 'q', 'E'):                        ['income', 'prem_refund', '上市公司利润表 - 退保金'],
    ('compens_payout', 'q', 'E'):                     ['income', 'compens_payout', '上市公司利润表 - 赔付总支出'],
    ('reser_insur_liab', 'q', 'E'):                   ['income', 'reser_insur_liab',
                                                       '上市公司利润表 - 提取保险责任准备金'],
    ('div_payt', 'q', 'E'):                           ['income', 'div_payt', '上市公司利润表 - 保户红利支出'],
    ('reins_exp', 'q', 'E'):                          ['income', 'reins_exp', '上市公司利润表 - 分保费用'],
    ('oper_exp', 'q', 'E'):                           ['income', 'oper_exp', '上市公司利润表 - 营业支出'],
    ('compens_payout_refu', 'q', 'E'):                ['income', 'compens_payout_refu',
                                                       '上市公司利润表 - 减:摊回赔付支出'],
    ('insur_reser_refu', 'q', 'E'):                   ['income', 'insur_reser_refu',
                                                       '上市公司利润表 - 减:摊回保险责任准备金'],
    ('reins_cost_refund', 'q', 'E'):                  ['income', 'reins_cost_refund',
                                                       '上市公司利润表 - 减:摊回分保费用'],
    ('other_bus_cost', 'q', 'E'):                     ['income', 'other_bus_cost', '上市公司利润表 - 其他业务成本'],
    ('operate_profit', 'q', 'E'):                     ['income', 'operate_profit', '上市公司利润表 - 营业利润'],
    ('non_oper_income', 'q', 'E'):                    ['income', 'non_oper_income', '上市公司利润表 - 加:营业外收入'],
    ('non_oper_exp', 'q', 'E'):                       ['income', 'non_oper_exp', '上市公司利润表 - 减:营业外支出'],
    ('nca_disploss', 'q', 'E'):                       ['income', 'nca_disploss',
                                                       '上市公司利润表 - 其中:减:非流动资产处置净损失'],
    ('total_profit', 'q', 'E'):                       ['income', 'total_profit', '上市公司利润表 - 利润总额'],
    ('income_tax', 'q', 'E'):                         ['income', 'income_tax', '上市公司利润表 - 所得税费用'],
    ('net_income', 'q', 'E'):                         ['income', 'n_income', '上市公司利润表 - 净利润(含少数股东损益)'],
    ('n_income_attr_p', 'q', 'E'):                    ['income', 'n_income_attr_p',
                                                       '上市公司利润表 - 净利润(不含少数股东损益)'],
    ('minority_gain', 'q', 'E'):                      ['income', 'minority_gain', '上市公司利润表 - 少数股东损益'],
    ('oth_compr_income', 'q', 'E'):                   ['income', 'oth_compr_income', '上市公司利润表 - 其他综合收益'],
    ('t_compr_income', 'q', 'E'):                     ['income', 't_compr_income', '上市公司利润表 - 综合收益总额'],
    ('compr_inc_attr_p', 'q', 'E'):                   ['income', 'compr_inc_attr_p',
                                                       '上市公司利润表 - 归属于母公司(或股东)的综合收益总额'],
    ('compr_inc_attr_m_s', 'q', 'E'):                 ['income', 'compr_inc_attr_m_s',
                                                       '上市公司利润表 - 归属于少数股东的综合收益总额'],
    ('income_ebit', 'q', 'E'):                        ['income', 'ebit', '上市公司利润表 - 息税前利润'],
    ('income_ebitda', 'q', 'E'):                      ['income', 'ebitda', '上市公司利润表 - 息税折旧摊销前利润'],
    ('insurance_exp', 'q', 'E'):                      ['income', 'insurance_exp', '上市公司利润表 - 保险业务支出'],
    ('undist_profit', 'q', 'E'):                      ['income', 'undist_profit', '上市公司利润表 - 年初未分配利润'],
    ('distable_profit', 'q', 'E'):                    ['income', 'distable_profit', '上市公司利润表 - 可分配利润'],
    ('income_rd_exp', 'q', 'E'):                      ['income', 'rd_exp', '上市公司利润表 - 研发费用'],
    ('fin_exp_int_exp', 'q', 'E'):                    ['income', 'fin_exp_int_exp',
                                                       '上市公司利润表 - 财务费用:利息费用'],
    ('fin_exp_int_inc', 'q', 'E'):                    ['income', 'fin_exp_int_inc',
                                                       '上市公司利润表 - 财务费用:利息收入'],
    ('transfer_surplus_rese', 'q', 'E'):              ['income', 'transfer_surplus_rese',
                                                       '上市公司利润表 - 盈余公积转入'],
    ('transfer_housing_imprest', 'q', 'E'):           ['income', 'transfer_housing_imprest',
                                                       '上市公司利润表 - 住房周转金转入'],
    ('transfer_oth', 'q', 'E'):                       ['income', 'transfer_oth', '上市公司利润表 - 其他转入'],
    ('adj_lossgain', 'q', 'E'):                       ['income', 'adj_lossgain', '上市公司利润表 - 调整以前年度损益'],
    ('withdra_legal_surplus', 'q', 'E'):              ['income', 'withdra_legal_surplus',
                                                       '上市公司利润表 - 提取法定盈余公积'],
    ('withdra_legal_pubfund', 'q', 'E'):              ['income', 'withdra_legal_pubfund',
                                                       '上市公司利润表 - 提取法定公益金'],
    ('withdra_biz_devfund', 'q', 'E'):                ['income', 'withdra_biz_devfund',
                                                       '上市公司利润表 - 提取企业发展基金'],
    ('withdra_rese_fund', 'q', 'E'):                  ['income', 'withdra_rese_fund', '上市公司利润表 - 提取储备基金'],
    ('withdra_oth_ersu', 'q', 'E'):                   ['income', 'withdra_oth_ersu',
                                                       '上市公司利润表 - 提取任意盈余公积金'],
    ('workers_welfare', 'q', 'E'):                    ['income', 'workers_welfare', '上市公司利润表 - 职工奖金福利'],
    ('distr_profit_shrhder', 'q', 'E'):               ['income', 'distr_profit_shrhder',
                                                       '上市公司利润表 - 可供股东分配的利润'],
    ('prfshare_payable_dvd', 'q', 'E'):               ['income', 'prfshare_payable_dvd',
                                                       '上市公司利润表 - 应付优先股股利'],
    ('comshare_payable_dvd', 'q', 'E'):               ['income', 'comshare_payable_dvd',
                                                       '上市公司利润表 - 应付普通股股利'],
    ('capit_comstock_div', 'q', 'E'):                 ['income', 'capit_comstock_div',
                                                       '上市公司利润表 - 转作股本的普通股股利'],
    ('net_after_nr_lp_correct', 'q', 'E'):            ['income', 'net_after_nr_lp_correct',
                                                       '上市公司利润表 - 扣除非经常性损益后的净利润（更正前）'],
    ('income_credit_impa_loss', 'q', 'E'):            ['income', 'credit_impa_loss', '上市公司利润表 - 信用减值损失'],
    ('net_expo_hedging_benefits', 'q', 'E'):          ['income', 'net_expo_hedging_benefits',
                                                       '上市公司利润表 - 净敞口套期收益'],
    ('oth_impair_loss_assets', 'q', 'E'):             ['income', 'oth_impair_loss_assets',
                                                       '上市公司利润表 - 其他资产减值损失'],
    ('total_opcost', 'q', 'E'):                       ['income', 'total_opcost', '上市公司利润表 - 营业总成本（二）'],
    ('amodcost_fin_assets', 'q', 'E'):                ['income', 'amodcost_fin_assets',
                                                       '上市公司利润表 - 以摊余成本计量的金融资产终止确认收益'],
    ('oth_income', 'q', 'E'):                         ['income', 'oth_income', '上市公司利润表 - 其他收益'],
    ('asset_disp_income', 'q', 'E'):                  ['income', 'asset_disp_income', '上市公司利润表 - 资产处置收益'],
    ('continued_net_profit', 'q', 'E'):               ['income', 'continued_net_profit',
                                                       '上市公司利润表 - 持续经营净利润'],
    ('end_net_profit', 'q', 'E'):                     ['income', 'end_net_profit', '上市公司利润表 - 终止经营净利润'],
    ('total_share', 'q', 'E'):                        ['balance', 'total_share', '上市公司资产负债表 - 期末总股本'],
    ('cap_rese', 'q', 'E'):                           ['balance', 'cap_rese', '上市公司资产负债表 - 资本公积金'],
    ('undistr_porfit', 'q', 'E'):                     ['balance', 'undistr_porfit', '上市公司资产负债表 - 未分配利润'],
    ('surplus_rese', 'q', 'E'):                       ['balance', 'surplus_rese', '上市公司资产负债表 - 盈余公积金'],
    ('special_rese', 'q', 'E'):                       ['balance', 'special_rese', '上市公司资产负债表 - 专项储备'],
    ('money_cap', 'q', 'E'):                          ['balance', 'money_cap', '上市公司资产负债表 - 货币资金'],
    ('trad_asset', 'q', 'E'):                         ['balance', 'trad_asset', '上市公司资产负债表 - 交易性金融资产'],
    ('notes_receiv', 'q', 'E'):                       ['balance', 'notes_receiv', '上市公司资产负债表 - 应收票据'],
    ('accounts_receiv', 'q', 'E'):                    ['balance', 'accounts_receiv', '上市公司资产负债表 - 应收账款'],
    ('oth_receiv', 'q', 'E'):                         ['balance', 'oth_receiv', '上市公司资产负债表 - 其他应收款'],
    ('prepayment', 'q', 'E'):                         ['balance', 'prepayment', '上市公司资产负债表 - 预付款项'],
    ('div_receiv', 'q', 'E'):                         ['balance', 'div_receiv', '上市公司资产负债表 - 应收股利'],
    ('int_receiv', 'q', 'E'):                         ['balance', 'int_receiv', '上市公司资产负债表 - 应收利息'],
    ('inventories', 'q', 'E'):                        ['balance', 'inventories', '上市公司资产负债表 - 存货'],
    ('amor_exp', 'q', 'E'):                           ['balance', 'amor_exp', '上市公司资产负债表 - 长期待摊费用'],
    ('nca_within_1y', 'q', 'E'):                      ['balance', 'nca_within_1y',
                                                       '上市公司资产负债表 - 一年内到期的非流动资产'],
    ('sett_rsrv', 'q', 'E'):                          ['balance', 'sett_rsrv', '上市公司资产负债表 - 结算备付金'],
    ('loanto_oth_bank_fi', 'q', 'E'):                 ['balance', 'loanto_oth_bank_fi',
                                                       '上市公司资产负债表 - 拆出资金'],
    ('premium_receiv', 'q', 'E'):                     ['balance', 'premium_receiv', '上市公司资产负债表 - 应收保费'],
    ('reinsur_receiv', 'q', 'E'):                     ['balance', 'reinsur_receiv',
                                                       '上市公司资产负债表 - 应收分保账款'],
    ('reinsur_res_receiv', 'q', 'E'):                 ['balance', 'reinsur_res_receiv',
                                                       '上市公司资产负债表 - 应收分保合同准备金'],
    ('pur_resale_fa', 'q', 'E'):                      ['balance', 'pur_resale_fa',
                                                       '上市公司资产负债表 - 买入返售金融资产'],
    ('oth_cur_assets', 'q', 'E'):                     ['balance', 'oth_cur_assets',
                                                       '上市公司资产负债表 - 其他流动资产'],
    ('total_cur_assets', 'q', 'E'):                   ['balance', 'total_cur_assets',
                                                       '上市公司资产负债表 - 流动资产合计'],
    ('fa_avail_for_sale', 'q', 'E'):                  ['balance', 'fa_avail_for_sale',
                                                       '上市公司资产负债表 - 可供出售金融资产'],
    ('htm_invest', 'q', 'E'):                         ['balance', 'htm_invest', '上市公司资产负债表 - 持有至到期投资'],
    ('lt_eqt_invest', 'q', 'E'):                      ['balance', 'lt_eqt_invest', '上市公司资产负债表 - 长期股权投资'],
    ('invest_real_estate', 'q', 'E'):                 ['balance', 'invest_real_estate',
                                                       '上市公司资产负债表 - 投资性房地产'],
    ('time_deposits', 'q', 'E'):                      ['balance', 'time_deposits', '上市公司资产负债表 - 定期存款'],
    ('oth_assets', 'q', 'E'):                         ['balance', 'oth_assets', '上市公司资产负债表 - 其他资产'],
    ('lt_rec', 'q', 'E'):                             ['balance', 'lt_rec', '上市公司资产负债表 - 长期应收款'],
    ('fix_assets', 'q', 'E'):                         ['balance', 'fix_assets', '上市公司资产负债表 - 固定资产'],
    ('cip', 'q', 'E'):                                ['balance', 'cip', '上市公司资产负债表 - 在建工程'],
    ('const_materials', 'q', 'E'):                    ['balance', 'const_materials', '上市公司资产负债表 - 工程物资'],
    ('fixed_assets_disp', 'q', 'E'):                  ['balance', 'fixed_assets_disp',
                                                       '上市公司资产负债表 - 固定资产清理'],
    ('produc_bio_assets', 'q', 'E'):                  ['balance', 'produc_bio_assets',
                                                       '上市公司资产负债表 - 生产性生物资产'],
    ('oil_and_gas_assets', 'q', 'E'):                 ['balance', 'oil_and_gas_assets',
                                                       '上市公司资产负债表 - 油气资产'],
    ('intan_assets', 'q', 'E'):                       ['balance', 'intan_assets', '上市公司资产负债表 - 无形资产'],
    ('r_and_d', 'q', 'E'):                            ['balance', 'r_and_d', '上市公司资产负债表 - 研发支出'],
    ('goodwill', 'q', 'E'):                           ['balance', 'goodwill', '上市公司资产负债表 - 商誉'],
    ('lt_amor_exp', 'q', 'E'):                        ['balance', 'lt_amor_exp', '上市公司资产负债表 - 长期待摊费用'],
    ('defer_tax_assets', 'q', 'E'):                   ['balance', 'defer_tax_assets',
                                                       '上市公司资产负债表 - 递延所得税资产'],
    ('decr_in_disbur', 'q', 'E'):                     ['balance', 'decr_in_disbur',
                                                       '上市公司资产负债表 - 发放贷款及垫款'],
    ('oth_nca', 'q', 'E'):                            ['balance', 'oth_nca', '上市公司资产负债表 - 其他非流动资产'],
    ('total_nca', 'q', 'E'):                          ['balance', 'total_nca', '上市公司资产负债表 - 非流动资产合计'],
    ('cash_reser_cb', 'q', 'E'):                      ['balance', 'cash_reser_cb',
                                                       '上市公司资产负债表 - 现金及存放中央银行款项'],
    ('depos_in_oth_bfi', 'q', 'E'):                   ['balance', 'depos_in_oth_bfi',
                                                       '上市公司资产负债表 - 存放同业和其它金融机构款项'],
    ('prec_metals', 'q', 'E'):                        ['balance', 'prec_metals', '上市公司资产负债表 - 贵金属'],
    ('deriv_assets', 'q', 'E'):                       ['balance', 'deriv_assets', '上市公司资产负债表 - 衍生金融资产'],
    ('rr_reins_une_prem', 'q', 'E'):                  ['balance', 'rr_reins_une_prem',
                                                       '上市公司资产负债表 - 应收分保未到期责任准备金'],
    ('rr_reins_outstd_cla', 'q', 'E'):                ['balance', 'rr_reins_outstd_cla',
                                                       '上市公司资产负债表 - 应收分保未决赔款准备金'],
    ('rr_reins_lins_liab', 'q', 'E'):                 ['balance', 'rr_reins_lins_liab',
                                                       '上市公司资产负债表 - 应收分保寿险责任准备金'],
    ('rr_reins_lthins_liab', 'q', 'E'):               ['balance', 'rr_reins_lthins_liab',
                                                       '上市公司资产负债表 - 应收分保长期健康险责任准备金'],
    ('refund_depos', 'q', 'E'):                       ['balance', 'refund_depos', '上市公司资产负债表 - 存出保证金'],
    ('ph_pledge_loans', 'q', 'E'):                    ['balance', 'ph_pledge_loans',
                                                       '上市公司资产负债表 - 保户质押贷款'],
    ('refund_cap_depos', 'q', 'E'):                   ['balance', 'refund_cap_depos',
                                                       '上市公司资产负债表 - 存出资本保证金'],
    ('indep_acct_assets', 'q', 'E'):                  ['balance', 'indep_acct_assets',
                                                       '上市公司资产负债表 - 独立账户资产'],
    ('client_depos', 'q', 'E'):                       ['balance', 'client_depos',
                                                       '上市公司资产负债表 - 其中：客户资金存款'],
    ('client_prov', 'q', 'E'):                        ['balance', 'client_prov',
                                                       '上市公司资产负债表 - 其中：客户备付金'],
    ('transac_seat_fee', 'q', 'E'):                   ['balance', 'transac_seat_fee',
                                                       '上市公司资产负债表 - 其中:交易席位费'],
    ('invest_as_receiv', 'q', 'E'):                   ['balance', 'invest_as_receiv',
                                                       '上市公司资产负债表 - 应收款项类投资'],
    ('total_assets', 'q', 'E'):                       ['balance', 'total_assets', '上市公司资产负债表 - 资产总计'],
    ('lt_borr', 'q', 'E'):                            ['balance', 'lt_borr', '上市公司资产负债表 - 长期借款'],
    ('st_borr', 'q', 'E'):                            ['balance', 'st_borr', '上市公司资产负债表 - 短期借款'],
    ('cb_borr', 'q', 'E'):                            ['balance', 'cb_borr', '上市公司资产负债表 - 向中央银行借款'],
    ('depos_ib_deposits', 'q', 'E'):                  ['balance', 'depos_ib_deposits',
                                                       '上市公司资产负债表 - 吸收存款及同业存放'],
    ('loan_oth_bank', 'q', 'E'):                      ['balance', 'loan_oth_bank', '上市公司资产负债表 - 拆入资金'],
    ('trading_fl', 'q', 'E'):                         ['balance', 'trading_fl', '上市公司资产负债表 - 交易性金融负债'],
    ('notes_payable', 'q', 'E'):                      ['balance', 'notes_payable', '上市公司资产负债表 - 应付票据'],
    ('acct_payable', 'q', 'E'):                       ['balance', 'acct_payable', '上市公司资产负债表 - 应付账款'],
    ('adv_receipts', 'q', 'E'):                       ['balance', 'adv_receipts', '上市公司资产负债表 - 预收款项'],
    ('sold_for_repur_fa', 'q', 'E'):                  ['balance', 'sold_for_repur_fa',
                                                       '上市公司资产负债表 - 卖出回购金融资产款'],
    ('comm_payable', 'q', 'E'):                       ['balance', 'comm_payable',
                                                       '上市公司资产负债表 - 应付手续费及佣金'],
    ('payroll_payable', 'q', 'E'):                    ['balance', 'payroll_payable',
                                                       '上市公司资产负债表 - 应付职工薪酬'],
    ('taxes_payable', 'q', 'E'):                      ['balance', 'taxes_payable', '上市公司资产负债表 - 应交税费'],
    ('int_payable', 'q', 'E'):                        ['balance', 'int_payable', '上市公司资产负债表 - 应付利息'],
    ('div_payable', 'q', 'E'):                        ['balance', 'div_payable', '上市公司资产负债表 - 应付股利'],
    ('oth_payable', 'q', 'E'):                        ['balance', 'oth_payable', '上市公司资产负债表 - 其他应付款'],
    ('acc_exp', 'q', 'E'):                            ['balance', 'acc_exp', '上市公司资产负债表 - 预提费用'],
    ('deferred_inc', 'q', 'E'):                       ['balance', 'deferred_inc', '上市公司资产负债表 - 递延收益'],
    ('st_bonds_payable', 'q', 'E'):                   ['balance', 'st_bonds_payable',
                                                       '上市公司资产负债表 - 应付短期债券'],
    ('payable_to_reinsurer', 'q', 'E'):               ['balance', 'payable_to_reinsurer',
                                                       '上市公司资产负债表 - 应付分保账款'],
    ('rsrv_insur_cont', 'q', 'E'):                    ['balance', 'rsrv_insur_cont',
                                                       '上市公司资产负债表 - 保险合同准备金'],
    ('acting_trading_sec', 'q', 'E'):                 ['balance', 'acting_trading_sec',
                                                       '上市公司资产负债表 - 代理买卖证券款'],
    ('acting_uw_sec', 'q', 'E'):                      ['balance', 'acting_uw_sec',
                                                       '上市公司资产负债表 - 代理承销证券款'],
    ('non_cur_liab_due_1y', 'q', 'E'):                ['balance', 'non_cur_liab_due_1y',
                                                       '上市公司资产负债表 - 一年内到期的非流动负债'],
    ('oth_cur_liab', 'q', 'E'):                       ['balance', 'oth_cur_liab', '上市公司资产负债表 - 其他流动负债'],
    ('total_cur_liab', 'q', 'E'):                     ['balance', 'total_cur_liab',
                                                       '上市公司资产负债表 - 流动负债合计'],
    ('bond_payable', 'q', 'E'):                       ['balance', 'bond_payable', '上市公司资产负债表 - 应付债券'],
    ('lt_payable', 'q', 'E'):                         ['balance', 'lt_payable', '上市公司资产负债表 - 长期应付款'],
    ('specific_payables', 'q', 'E'):                  ['balance', 'specific_payables',
                                                       '上市公司资产负债表 - 专项应付款'],
    ('estimated_liab', 'q', 'E'):                     ['balance', 'estimated_liab', '上市公司资产负债表 - 预计负债'],
    ('defer_tax_liab', 'q', 'E'):                     ['balance', 'defer_tax_liab',
                                                       '上市公司资产负债表 - 递延所得税负债'],
    ('defer_inc_non_cur_liab', 'q', 'E'):             ['balance', 'defer_inc_non_cur_liab',
                                                       '上市公司资产负债表 - 递延收益-非流动负债'],
    ('oth_ncl', 'q', 'E'):                            ['balance', 'oth_ncl', '上市公司资产负债表 - 其他非流动负债'],
    ('total_ncl', 'q', 'E'):                          ['balance', 'total_ncl', '上市公司资产负债表 - 非流动负债合计'],
    ('depos_oth_bfi', 'q', 'E'):                      ['balance', 'depos_oth_bfi',
                                                       '上市公司资产负债表 - 同业和其它金融机构存放款项'],
    ('deriv_liab', 'q', 'E'):                         ['balance', 'deriv_liab', '上市公司资产负债表 - 衍生金融负债'],
    ('depos', 'q', 'E'):                              ['balance', 'depos', '上市公司资产负债表 - 吸收存款'],
    ('agency_bus_liab', 'q', 'E'):                    ['balance', 'agency_bus_liab',
                                                       '上市公司资产负债表 - 代理业务负债'],
    ('oth_liab', 'q', 'E'):                           ['balance', 'oth_liab', '上市公司资产负债表 - 其他负债'],
    ('prem_receiv_adva', 'q', 'E'):                   ['balance', 'prem_receiv_adva', '上市公司资产负债表 - 预收保费'],
    ('depos_received', 'q', 'E'):                     ['balance', 'depos_received', '上市公司资产负债表 - 存入保证金'],
    ('ph_invest', 'q', 'E'):                          ['balance', 'ph_invest', '上市公司资产负债表 - 保户储金及投资款'],
    ('reser_une_prem', 'q', 'E'):                     ['balance', 'reser_une_prem',
                                                       '上市公司资产负债表 - 未到期责任准备金'],
    ('reser_outstd_claims', 'q', 'E'):                ['balance', 'reser_outstd_claims',
                                                       '上市公司资产负债表 - 未决赔款准备金'],
    ('reser_lins_liab', 'q', 'E'):                    ['balance', 'reser_lins_liab',
                                                       '上市公司资产负债表 - 寿险责任准备金'],
    ('reser_lthins_liab', 'q', 'E'):                  ['balance', 'reser_lthins_liab',
                                                       '上市公司资产负债表 - 长期健康险责任准备金'],
    ('indept_acc_liab', 'q', 'E'):                    ['balance', 'indept_acc_liab',
                                                       '上市公司资产负债表 - 独立账户负债'],
    ('pledge_borr', 'q', 'E'):                        ['balance', 'pledge_borr', '上市公司资产负债表 - 其中:质押借款'],
    ('indem_payable', 'q', 'E'):                      ['balance', 'indem_payable', '上市公司资产负债表 - 应付赔付款'],
    ('policy_div_payable', 'q', 'E'):                 ['balance', 'policy_div_payable',
                                                       '上市公司资产负债表 - 应付保单红利'],
    ('total_liab', 'q', 'E'):                         ['balance', 'total_liab', '上市公司资产负债表 - 负债合计'],
    ('treasury_share', 'q', 'E'):                     ['balance', 'treasury_share', '上市公司资产负债表 - 减:库存股'],
    ('ordin_risk_reser', 'q', 'E'):                   ['balance', 'ordin_risk_reser',
                                                       '上市公司资产负债表 - 一般风险准备'],
    ('forex_differ', 'q', 'E'):                       ['balance', 'forex_differ',
                                                       '上市公司资产负债表 - 外币报表折算差额'],
    ('invest_loss_unconf', 'q', 'E'):                 ['balance', 'invest_loss_unconf',
                                                       '上市公司资产负债表 - 未确认的投资损失'],
    ('minority_int', 'q', 'E'):                       ['balance', 'minority_int', '上市公司资产负债表 - 少数股东权益'],
    ('total_hldr_eqy_exc_min_int', 'q', 'E'):         ['balance', 'total_hldr_eqy_exc_min_int',
                                                       '上市公司资产负债表 - 股东权益合计(不含少数股东权益)'],
    ('total_hldr_eqy_inc_min_int', 'q', 'E'):         ['balance', 'total_hldr_eqy_inc_min_int',
                                                       '上市公司资产负债表 - 股东权益合计(含少数股东权益)'],
    ('total_liab_hldr_eqy', 'q', 'E'):                ['balance', 'total_liab_hldr_eqy',
                                                       '上市公司资产负债表 - 负债及股东权益总计'],
    ('lt_payroll_payable', 'q', 'E'):                 ['balance', 'lt_payroll_payable',
                                                       '上市公司资产负债表 - 长期应付职工薪酬'],
    ('oth_comp_income', 'q', 'E'):                    ['balance', 'oth_comp_income',
                                                       '上市公司资产负债表 - 其他综合收益'],
    ('oth_eqt_tools', 'q', 'E'):                      ['balance', 'oth_eqt_tools', '上市公司资产负债表 - 其他权益工具'],
    ('oth_eqt_tools_p_shr', 'q', 'E'):                ['balance', 'oth_eqt_tools_p_shr',
                                                       '上市公司资产负债表 - 其他权益工具(优先股)'],
    ('lending_funds', 'q', 'E'):                      ['balance', 'lending_funds', '上市公司资产负债表 - 融出资金'],
    ('acc_receivable', 'q', 'E'):                     ['balance', 'acc_receivable', '上市公司资产负债表 - 应收款项'],
    ('st_fin_payable', 'q', 'E'):                     ['balance', 'st_fin_payable',
                                                       '上市公司资产负债表 - 应付短期融资款'],
    ('payables', 'q', 'E'):                           ['balance', 'payables', '上市公司资产负债表 - 应付款项'],
    ('hfs_assets', 'q', 'E'):                         ['balance', 'hfs_assets', '上市公司资产负债表 - 持有待售的资产'],
    ('hfs_sales', 'q', 'E'):                          ['balance', 'hfs_sales', '上市公司资产负债表 - 持有待售的负债'],
    ('cost_fin_assets', 'q', 'E'):                    ['balance', 'cost_fin_assets',
                                                       '上市公司资产负债表 - 以摊余成本计量的金融资产'],
    ('fair_value_fin_assets', 'q', 'E'):              ['balance', 'fair_value_fin_assets',
                                                       '上市公司资产负债表 - 以公允价值计量且其变动计入其他综合收益的金融资产'],
    ('cip_total', 'q', 'E'):                          ['balance', 'cip_total',
                                                       '上市公司资产负债表 - 在建工程(合计)(元)'],
    ('oth_pay_total', 'q', 'E'):                      ['balance', 'oth_pay_total',
                                                       '上市公司资产负债表 - 其他应付款(合计)(元)'],
    ('long_pay_total', 'q', 'E'):                     ['balance', 'long_pay_total',
                                                       '上市公司资产负债表 - 长期应付款(合计)(元)'],
    ('debt_invest', 'q', 'E'):                        ['balance', 'debt_invest', '上市公司资产负债表 - 债权投资(元)'],
    ('oth_debt_invest', 'q', 'E'):                    ['balance', 'oth_debt_invest',
                                                       '上市公司资产负债表 - 其他债权投资(元)'],
    ('oth_eq_invest', 'q', 'E'):                      ['balance', 'oth_eq_invest',
                                                       '上市公司资产负债表 - 其他权益工具投资(元)'],
    ('oth_illiq_fin_assets', 'q', 'E'):               ['balance', 'oth_illiq_fin_assets',
                                                       '上市公司资产负债表 - 其他非流动金融资产(元)'],
    ('oth_eq_ppbond', 'q', 'E'):                      ['balance', 'oth_eq_ppbond',
                                                       '上市公司资产负债表 - 其他权益工具:永续债(元)'],
    ('receiv_financing', 'q', 'E'):                   ['balance', 'receiv_financing',
                                                       '上市公司资产负债表 - 应收款项融资'],
    ('use_right_assets', 'q', 'E'):                   ['balance', 'use_right_assets',
                                                       '上市公司资产负债表 - 使用权资产'],
    ('lease_liab', 'q', 'E'):                         ['balance', 'lease_liab', '上市公司资产负债表 - 租赁负债'],
    ('contract_assets', 'q', 'E'):                    ['balance', 'contract_assets', '上市公司资产负债表 - 合同资产'],
    ('contract_liab', 'q', 'E'):                      ['balance', 'contract_liab', '上市公司资产负债表 - 合同负债'],
    ('accounts_receiv_bill', 'q', 'E'):               ['balance', 'accounts_receiv_bill',
                                                       '上市公司资产负债表 - 应收票据及应收账款'],
    ('accounts_pay', 'q', 'E'):                       ['balance', 'accounts_pay',
                                                       '上市公司资产负债表 - 应付票据及应付账款'],
    ('oth_rcv_total', 'q', 'E'):                      ['balance', 'oth_rcv_total',
                                                       '上市公司资产负债表 - 其他应收款(合计)（元）'],
    ('fix_assets_total', 'q', 'E'):                   ['balance', 'fix_assets_total',
                                                       '上市公司资产负债表 - 固定资产(合计)(元)'],
    ('net_profit', 'q', 'E'):                         ['cashflow', 'net_profit', '上市公司现金流量表 - 净利润'],
    ('finan_exp', 'q', 'E'):                          ['cashflow', 'finan_exp', '上市公司现金流量表 - 财务费用'],
    ('c_fr_sale_sg', 'q', 'E'):                       ['cashflow', 'c_fr_sale_sg',
                                                       '上市公司现金流量表 - 销售商品、提供劳务收到的现金'],
    ('recp_tax_rends', 'q', 'E'):                     ['cashflow', 'recp_tax_rends',
                                                       '上市公司现金流量表 - 收到的税费返还'],
    ('n_depos_incr_fi', 'q', 'E'):                    ['cashflow', 'n_depos_incr_fi',
                                                       '上市公司现金流量表 - 客户存款和同业存放款项净增加额'],
    ('n_incr_loans_cb', 'q', 'E'):                    ['cashflow', 'n_incr_loans_cb',
                                                       '上市公司现金流量表 - 向中央银行借款净增加额'],
    ('n_inc_borr_oth_fi', 'q', 'E'):                  ['cashflow', 'n_inc_borr_oth_fi',
                                                       '上市公司现金流量表 - 向其他金融机构拆入资金净增加额'],
    ('prem_fr_orig_contr', 'q', 'E'):                 ['cashflow', 'prem_fr_orig_contr',
                                                       '上市公司现金流量表 - 收到原保险合同保费取得的现金'],
    ('n_incr_insured_dep', 'q', 'E'):                 ['cashflow', 'n_incr_insured_dep',
                                                       '上市公司现金流量表 - 保户储金净增加额'],
    ('n_reinsur_prem', 'q', 'E'):                     ['cashflow', 'n_reinsur_prem',
                                                       '上市公司现金流量表 - 收到再保业务现金净额'],
    ('n_incr_disp_tfa', 'q', 'E'):                    ['cashflow', 'n_incr_disp_tfa',
                                                       '上市公司现金流量表 - 处置交易性金融资产净增加额'],
    ('ifc_cash_incr', 'q', 'E'):                      ['cashflow', 'ifc_cash_incr',
                                                       '上市公司现金流量表 - 收取利息和手续费净增加额'],
    ('n_incr_disp_faas', 'q', 'E'):                   ['cashflow', 'n_incr_disp_faas',
                                                       '上市公司现金流量表 - 处置可供出售金融资产净增加额'],
    ('n_incr_loans_oth_bank', 'q', 'E'):              ['cashflow', 'n_incr_loans_oth_bank',
                                                       '上市公司现金流量表 - 拆入资金净增加额'],
    ('n_cap_incr_repur', 'q', 'E'):                   ['cashflow', 'n_cap_incr_repur',
                                                       '上市公司现金流量表 - 回购业务资金净增加额'],
    ('c_fr_oth_operate_a', 'q', 'E'):                 ['cashflow', 'c_fr_oth_operate_a',
                                                       '上市公司现金流量表 - 收到其他与经营活动有关的现金'],
    ('c_inf_fr_operate_a', 'q', 'E'):                 ['cashflow', 'c_inf_fr_operate_a',
                                                       '上市公司现金流量表 - 经营活动现金流入小计'],
    ('c_paid_goods_s', 'q', 'E'):                     ['cashflow', 'c_paid_goods_s',
                                                       '上市公司现金流量表 - 购买商品、接受劳务支付的现金'],
    ('c_paid_to_for_empl', 'q', 'E'):                 ['cashflow', 'c_paid_to_for_empl',
                                                       '上市公司现金流量表 - 支付给职工以及为职工支付的现金'],
    ('c_paid_for_taxes', 'q', 'E'):                   ['cashflow', 'c_paid_for_taxes',
                                                       '上市公司现金流量表 - 支付的各项税费'],
    ('n_incr_clt_loan_adv', 'q', 'E'):                ['cashflow', 'n_incr_clt_loan_adv',
                                                       '上市公司现金流量表 - 客户贷款及垫款净增加额'],
    ('n_incr_dep_cbob', 'q', 'E'):                    ['cashflow', 'n_incr_dep_cbob',
                                                       '上市公司现金流量表 - 存放央行和同业款项净增加额'],
    ('c_pay_claims_orig_inco', 'q', 'E'):             ['cashflow', 'c_pay_claims_orig_inco',
                                                       '上市公司现金流量表 - 支付原保险合同赔付款项的现金'],
    ('pay_handling_chrg', 'q', 'E'):                  ['cashflow', 'pay_handling_chrg',
                                                       '上市公司现金流量表 - 支付手续费的现金'],
    ('pay_comm_insur_plcy', 'q', 'E'):                ['cashflow', 'pay_comm_insur_plcy',
                                                       '上市公司现金流量表 - 支付保单红利的现金'],
    ('oth_cash_pay_oper_act', 'q', 'E'):              ['cashflow', 'oth_cash_pay_oper_act',
                                                       '上市公司现金流量表 - 支付其他与经营活动有关的现金'],
    ('st_cash_out_act', 'q', 'E'):                    ['cashflow', 'st_cash_out_act',
                                                       '上市公司现金流量表 - 经营活动现金流出小计'],
    ('n_cashflow_act', 'q', 'E'):                     ['cashflow', 'n_cashflow_act',
                                                       '上市公司现金流量表 - 经营活动产生的现金流量净额'],
    ('oth_recp_ral_inv_act', 'q', 'E'):               ['cashflow', 'oth_recp_ral_inv_act',
                                                       '上市公司现金流量表 - 收到其他与投资活动有关的现金'],
    ('c_disp_withdrwl_invest', 'q', 'E'):             ['cashflow', 'c_disp_withdrwl_invest',
                                                       '上市公司现金流量表 - 收回投资收到的现金'],
    ('c_recp_return_invest', 'q', 'E'):               ['cashflow', 'c_recp_return_invest',
                                                       '上市公司现金流量表 - 取得投资收益收到的现金'],
    ('n_recp_disp_fiolta', 'q', 'E'):                 ['cashflow', 'n_recp_disp_fiolta',
                                                       '上市公司现金流量表 - 处置固定资产、无形资产和其他长期资产收回的现金净额'],
    ('n_recp_disp_sobu', 'q', 'E'):                   ['cashflow', 'n_recp_disp_sobu',
                                                       '上市公司现金流量表 - 处置子公司及其他营业单位收到的现金净额'],
    ('stot_inflows_inv_act', 'q', 'E'):               ['cashflow', 'stot_inflows_inv_act',
                                                       '上市公司现金流量表 - 投资活动现金流入小计'],
    ('c_pay_acq_const_fiolta', 'q', 'E'):             ['cashflow', 'c_pay_acq_const_fiolta',
                                                       '上市公司现金流量表 - 购建固定资产、无形资产和其他长期资产支付的现金'],
    ('c_paid_invest', 'q', 'E'):                      ['cashflow', 'c_paid_invest',
                                                       '上市公司现金流量表 - 投资支付的现金'],
    ('n_disp_subs_oth_biz', 'q', 'E'):                ['cashflow', 'n_disp_subs_oth_biz',
                                                       '上市公司现金流量表 - 取得子公司及其他营业单位支付的现金净额'],
    ('oth_pay_ral_inv_act', 'q', 'E'):                ['cashflow', 'oth_pay_ral_inv_act',
                                                       '上市公司现金流量表 - 支付其他与投资活动有关的现金'],
    ('n_incr_pledge_loan', 'q', 'E'):                 ['cashflow', 'n_incr_pledge_loan',
                                                       '上市公司现金流量表 - 质押贷款净增加额'],
    ('stot_out_inv_act', 'q', 'E'):                   ['cashflow', 'stot_out_inv_act',
                                                       '上市公司现金流量表 - 投资活动现金流出小计'],
    ('n_cashflow_inv_act', 'q', 'E'):                 ['cashflow', 'n_cashflow_inv_act',
                                                       '上市公司现金流量表 - 投资活动产生的现金流量净额'],
    ('c_recp_borrow', 'q', 'E'):                      ['cashflow', 'c_recp_borrow',
                                                       '上市公司现金流量表 - 取得借款收到的现金'],
    ('proc_issue_bonds', 'q', 'E'):                   ['cashflow', 'proc_issue_bonds',
                                                       '上市公司现金流量表 - 发行债券收到的现金'],
    ('oth_cash_recp_ral_fnc_act', 'q', 'E'):          ['cashflow', 'oth_cash_recp_ral_fnc_act',
                                                       '上市公司现金流量表 - 收到其他与筹资活动有关的现金'],
    ('stot_cash_in_fnc_act', 'q', 'E'):               ['cashflow', 'stot_cash_in_fnc_act',
                                                       '上市公司现金流量表 - 筹资活动现金流入小计'],
    ('free_cashflow', 'q', 'E'):                      ['cashflow', 'free_cashflow',
                                                       '上市公司现金流量表 - 企业自由现金流量'],
    ('c_prepay_amt_borr', 'q', 'E'):                  ['cashflow', 'c_prepay_amt_borr',
                                                       '上市公司现金流量表 - 偿还债务支付的现金'],
    ('c_pay_dist_dpcp_int_exp', 'q', 'E'):            ['cashflow', 'c_pay_dist_dpcp_int_exp',
                                                       '上市公司现金流量表 - 分配股利、利润或偿付利息支付的现金'],
    ('incl_dvd_profit_paid_sc_ms', 'q', 'E'):         ['cashflow', 'incl_dvd_profit_paid_sc_ms',
                                                       '上市公司现金流量表 - 其中:子公司支付给少数股东的股利、利润'],
    ('oth_cashpay_ral_fnc_act', 'q', 'E'):            ['cashflow', 'oth_cashpay_ral_fnc_act',
                                                       '上市公司现金流量表 - 支付其他与筹资活动有关的现金'],
    ('stot_cashout_fnc_act', 'q', 'E'):               ['cashflow', 'stot_cashout_fnc_act',
                                                       '上市公司现金流量表 - 筹资活动现金流出小计'],
    ('n_cash_flows_fnc_act', 'q', 'E'):               ['cashflow', 'n_cash_flows_fnc_act',
                                                       '上市公司现金流量表 - 筹资活动产生的现金流量净额'],
    ('eff_fx_flu_cash', 'q', 'E'):                    ['cashflow', 'eff_fx_flu_cash',
                                                       '上市公司现金流量表 - 汇率变动对现金的影响'],
    ('n_incr_cash_cash_equ', 'q', 'E'):               ['cashflow', 'n_incr_cash_cash_equ',
                                                       '上市公司现金流量表 - 现金及现金等价物净增加额'],
    ('c_cash_equ_beg_period', 'q', 'E'):              ['cashflow', 'c_cash_equ_beg_period',
                                                       '上市公司现金流量表 - 期初现金及现金等价物余额'],
    ('c_cash_equ_end_period', 'q', 'E'):              ['cashflow', 'c_cash_equ_end_period',
                                                       '上市公司现金流量表 - 期末现金及现金等价物余额'],
    ('c_recp_cap_contrib', 'q', 'E'):                 ['cashflow', 'c_recp_cap_contrib',
                                                       '上市公司现金流量表 - 吸收投资收到的现金'],
    ('incl_cash_rec_saims', 'q', 'E'):                ['cashflow', 'incl_cash_rec_saims',
                                                       '上市公司现金流量表 - 其中:子公司吸收少数股东投资收到的现金'],
    ('uncon_invest_loss', 'q', 'E'):                  ['cashflow', 'uncon_invest_loss',
                                                       '上市公司现金流量表 - 未确认投资损失'],
    ('prov_depr_assets', 'q', 'E'):                   ['cashflow', 'prov_depr_assets',
                                                       '上市公司现金流量表 - 加:资产减值准备'],
    ('depr_fa_coga_dpba', 'q', 'E'):                  ['cashflow', 'depr_fa_coga_dpba',
                                                       '上市公司现金流量表 - 固定资产折旧、油气资产折耗、生产性生物资产折旧'],
    ('amort_intang_assets', 'q', 'E'):                ['cashflow', 'amort_intang_assets',
                                                       '上市公司现金流量表 - 无形资产摊销'],
    ('lt_amort_deferred_exp', 'q', 'E'):              ['cashflow', 'lt_amort_deferred_exp',
                                                       '上市公司现金流量表 - 长期待摊费用摊销'],
    ('decr_deferred_exp', 'q', 'E'):                  ['cashflow', 'decr_deferred_exp',
                                                       '上市公司现金流量表 - 待摊费用减少'],
    ('incr_acc_exp', 'q', 'E'):                       ['cashflow', 'incr_acc_exp', '上市公司现金流量表 - 预提费用增加'],
    ('loss_disp_fiolta', 'q', 'E'):                   ['cashflow', 'loss_disp_fiolta',
                                                       '上市公司现金流量表 - 处置固定、无形资产和其他长期资产的损失'],
    ('loss_scr_fa', 'q', 'E'):                        ['cashflow', 'loss_scr_fa',
                                                       '上市公司现金流量表 - 固定资产报废损失'],
    ('loss_fv_chg', 'q', 'E'):                        ['cashflow', 'loss_fv_chg',
                                                       '上市公司现金流量表 - 公允价值变动损失'],
    ('invest_loss', 'q', 'E'):                        ['cashflow', 'invest_loss', '上市公司现金流量表 - 投资损失'],
    ('decr_def_inc_tax_assets', 'q', 'E'):            ['cashflow', 'decr_def_inc_tax_assets',
                                                       '上市公司现金流量表 - 递延所得税资产减少'],
    ('incr_def_inc_tax_liab', 'q', 'E'):              ['cashflow', 'incr_def_inc_tax_liab',
                                                       '上市公司现金流量表 - 递延所得税负债增加'],
    ('decr_inventories', 'q', 'E'):                   ['cashflow', 'decr_inventories',
                                                       '上市公司现金流量表 - 存货的减少'],
    ('decr_oper_payable', 'q', 'E'):                  ['cashflow', 'decr_oper_payable',
                                                       '上市公司现金流量表 - 经营性应收项目的减少'],
    ('incr_oper_payable', 'q', 'E'):                  ['cashflow', 'incr_oper_payable',
                                                       '上市公司现金流量表 - 经营性应付项目的增加'],
    ('others', 'q', 'E'):                             ['cashflow', 'others', '上市公司现金流量表 - 其他'],
    ('im_net_cashflow_oper_act', 'q', 'E'):           ['cashflow', 'im_net_cashflow_oper_act',
                                                       '上市公司现金流量表 - 经营活动产生的现金流量净额(间接法)'],
    ('conv_debt_into_cap', 'q', 'E'):                 ['cashflow', 'conv_debt_into_cap',
                                                       '上市公司现金流量表 - 债务转为资本'],
    ('conv_copbonds_due_within_1y', 'q', 'E'):        ['cashflow', 'conv_copbonds_due_within_1y',
                                                       '上市公司现金流量表 - 一年内到期的可转换公司债券'],
    ('fa_fnc_leases', 'q', 'E'):                      ['cashflow', 'fa_fnc_leases',
                                                       '上市公司现金流量表 - 融资租入固定资产'],
    ('im_n_incr_cash_equ', 'q', 'E'):                 ['cashflow', 'im_n_incr_cash_equ',
                                                       '上市公司现金流量表 - 现金及现金等价物净增加额(间接法)'],
    ('net_dism_capital_add', 'q', 'E'):               ['cashflow', 'net_dism_capital_add',
                                                       '上市公司现金流量表 - 拆出资金净增加额'],
    ('net_cash_rece_sec', 'q', 'E'):                  ['cashflow', 'net_cash_rece_sec',
                                                       '上市公司现金流量表 - 代理买卖证券收到的现金净额(元)'],
    ('cashflow_credit_impa_loss', 'q', 'E'):          ['cashflow', 'credit_impa_loss',
                                                       '上市公司现金流量表 - 信用减值损失'],
    ('use_right_asset_dep', 'q', 'E'):                ['cashflow', 'use_right_asset_dep',
                                                       '上市公司现金流量表 - 使用权资产折旧'],
    ('oth_loss_asset', 'q', 'E'):                     ['cashflow', 'oth_loss_asset',
                                                       '上市公司现金流量表 - 其他资产减值损失'],
    ('end_bal_cash', 'q', 'E'):                       ['cashflow', 'end_bal_cash',
                                                       '上市公司现金流量表 - 现金的期末余额'],
    ('beg_bal_cash', 'q', 'E'):                       ['cashflow', 'beg_bal_cash',
                                                       '上市公司现金流量表 - 减:现金的期初余额'],
    ('end_bal_cash_equ', 'q', 'E'):                   ['cashflow', 'end_bal_cash_equ',
                                                       '上市公司现金流量表 - 加:现金等价物的期末余额'],
    ('beg_bal_cash_equ', 'q', 'E'):                   ['cashflow', 'beg_bal_cash_equ',
                                                       '上市公司现金流量表 - 减:现金等价物的期初余额'],
    ('express_revenue', 'q', 'E'):                    ['express', 'revenue', '上市公司业绩快报 - 营业收入(元)'],
    ('express_operate_profit', 'q', 'E'):             ['express', 'operate_profit', '上市公司业绩快报 - 营业利润(元)'],
    ('express_total_profit', 'q', 'E'):               ['express', 'total_profit', '上市公司业绩快报 - 利润总额(元)'],
    ('express_n_income', 'q', 'E'):                   ['express', 'n_income', '上市公司业绩快报 - 净利润(元)'],
    ('express_total_assets', 'q', 'E'):               ['express', 'total_assets', '上市公司业绩快报 - 总资产(元)'],
    ('express_total_hldr_eqy_exc_min_int', 'q', 'E'): ['express', 'total_hldr_eqy_exc_min_int',
                                                       '上市公司业绩快报 - 股东权益合计(不含少数股东权益)(元)'],
    ('express_diluted_eps', 'q', 'E'):                ['express', 'diluted_eps',
                                                       '上市公司业绩快报 - 每股收益(摊薄)(元)'],
    ('diluted_roe', 'q', 'E'):                        ['express', 'diluted_roe',
                                                       '上市公司业绩快报 - 净资产收益率(摊薄)(%)'],
    ('yoy_net_profit', 'q', 'E'):                     ['express', 'yoy_net_profit',
                                                       '上市公司业绩快报 - 去年同期修正后净利润'],
    ('bps', 'q', 'E'):                                ['express', 'bps', '上市公司业绩快报 - 每股净资产'],
    ('yoy_sales', 'q', 'E'):                          ['express', 'yoy_sales',
                                                       '上市公司业绩快报 - 同比增长率:营业收入'],
    ('yoy_op', 'q', 'E'):                             ['express', 'yoy_op', '上市公司业绩快报 - 同比增长率:营业利润'],
    ('yoy_tp', 'q', 'E'):                             ['express', 'yoy_tp', '上市公司业绩快报 - 同比增长率:利润总额'],
    ('yoy_dedu_np', 'q', 'E'):                        ['express', 'yoy_dedu_np',
                                                       '上市公司业绩快报 - 同比增长率:归属母公司股东的净利润'],
    ('yoy_eps', 'q', 'E'):                            ['express', 'yoy_eps',
                                                       '上市公司业绩快报 - 同比增长率:基本每股收益'],
    ('yoy_roe', 'q', 'E'):                            ['express', 'yoy_roe',
                                                       '上市公司业绩快报 - 同比增减:加权平均净资产收益率'],
    ('growth_assets', 'q', 'E'):                      ['express', 'growth_assets',
                                                       '上市公司业绩快报 - 比年初增长率:总资产'],
    ('yoy_equity', 'q', 'E'):                         ['express', 'yoy_equity',
                                                       '上市公司业绩快报 - 比年初增长率:归属母公司的股东权益'],
    ('growth_bps', 'q', 'E'):                         ['express', 'growth_bps',
                                                       '上市公司业绩快报 - 比年初增长率:归属于母公司股东的每股净资产'],
    ('or_last_year', 'q', 'E'):                       ['express', 'or_last_year',
                                                       '上市公司业绩快报 - 去年同期营业收入'],
    ('op_last_year', 'q', 'E'):                       ['express', 'op_last_year',
                                                       '上市公司业绩快报 - 去年同期营业利润'],
    ('tp_last_year', 'q', 'E'):                       ['express', 'tp_last_year',
                                                       '上市公司业绩快报 - 去年同期利润总额'],
    ('np_last_year', 'q', 'E'):                       ['express', 'np_last_year', '上市公司业绩快报 - 去年同期净利润'],
    ('eps_last_year', 'q', 'E'):                      ['express', 'eps_last_year',
                                                       '上市公司业绩快报 - 去年同期每股收益'],
    ('open_net_assets', 'q', 'E'):                    ['express', 'open_net_assets', '上市公司业绩快报 - 期初净资产'],
    ('open_bps', 'q', 'E'):                           ['express', 'open_bps', '上市公司业绩快报 - 期初每股净资产'],
    ('perf_summary', 'q', 'E'):                       ['express', 'perf_summary', '上市公司业绩快报 - 业绩简要说明'],
    ('eps', 'q', 'E'):                                ['financial', 'eps', '上市公司财务指标 - 基本每股收益'],
    ('dt_eps', 'q', 'E'):                             ['financial', 'dt_eps', '上市公司财务指标 - 稀释每股收益'],
    ('total_revenue_ps', 'q', 'E'):                   ['financial', 'total_revenue_ps',
                                                       '上市公司财务指标 - 每股营业总收入'],
    ('revenue_ps', 'q', 'E'):                         ['financial', 'revenue_ps', '上市公司财务指标 - 每股营业收入'],
    ('capital_rese_ps', 'q', 'E'):                    ['financial', 'capital_rese_ps',
                                                       '上市公司财务指标 - 每股资本公积'],
    ('surplus_rese_ps', 'q', 'E'):                    ['financial', 'surplus_rese_ps',
                                                       '上市公司财务指标 - 每股盈余公积'],
    ('undist_profit_ps', 'q', 'E'):                   ['financial', 'undist_profit_ps',
                                                       '上市公司财务指标 - 每股未分配利润'],
    ('extra_item', 'q', 'E'):                         ['financial', 'extra_item', '上市公司财务指标 - 非经常性损益'],
    ('profit_dedt', 'q', 'E'):                        ['financial', 'profit_dedt',
                                                       '上市公司财务指标 - 扣除非经常性损益后的净利润（扣非净利润）'],
    ('gross_margin', 'q', 'E'):                       ['financial', 'gross_margin', '上市公司财务指标 - 毛利'],
    ('current_ratio', 'q', 'E'):                      ['financial', 'current_ratio', '上市公司财务指标 - 流动比率'],
    ('quick_ratio', 'q', 'E'):                        ['financial', 'quick_ratio', '上市公司财务指标 - 速动比率'],
    ('cash_ratio', 'q', 'E'):                         ['financial', 'cash_ratio', '上市公司财务指标 - 保守速动比率'],
    ('invturn_days', 'q', 'E'):                       ['financial', 'invturn_days', '上市公司财务指标 - 存货周转天数'],
    ('arturn_days', 'q', 'E'):                        ['financial', 'arturn_days',
                                                       '上市公司财务指标 - 应收账款周转天数'],
    ('inv_turn', 'q', 'E'):                           ['financial', 'inv_turn', '上市公司财务指标 - 存货周转率'],
    ('ar_turn', 'q', 'E'):                            ['financial', 'ar_turn', '上市公司财务指标 - 应收账款周转率'],
    ('ca_turn', 'q', 'E'):                            ['financial', 'ca_turn', '上市公司财务指标 - 流动资产周转率'],
    ('fa_turn', 'q', 'E'):                            ['financial', 'fa_turn', '上市公司财务指标 - 固定资产周转率'],
    ('assets_turn', 'q', 'E'):                        ['financial', 'assets_turn', '上市公司财务指标 - 总资产周转率'],
    ('op_income', 'q', 'E'):                          ['financial', 'op_income', '上市公司财务指标 - 经营活动净收益'],
    ('valuechange_income', 'q', 'E'):                 ['financial', 'valuechange_income',
                                                       '上市公司财务指标 - 价值变动净收益'],
    ('interst_income', 'q', 'E'):                     ['financial', 'interst_income', '上市公司财务指标 - 利息费用'],
    ('daa', 'q', 'E'):                                ['financial', 'daa', '上市公司财务指标 - 折旧与摊销'],
    ('ebit', 'q', 'E'):                               ['financial', 'ebit', '上市公司财务指标 - 息税前利润'],
    ('ebitda', 'q', 'E'):                             ['financial', 'ebitda', '上市公司财务指标 - 息税折旧摊销前利润'],
    ('fcff', 'q', 'E'):                               ['financial', 'fcff', '上市公司财务指标 - 企业自由现金流量'],
    ('fcfe', 'q', 'E'):                               ['financial', 'fcfe', '上市公司财务指标 - 股权自由现金流量'],
    ('current_exint', 'q', 'E'):                      ['financial', 'current_exint', '上市公司财务指标 - 无息流动负债'],
    ('noncurrent_exint', 'q', 'E'):                   ['financial', 'noncurrent_exint',
                                                       '上市公司财务指标 - 无息非流动负债'],
    ('interestdebt', 'q', 'E'):                       ['financial', 'interestdebt', '上市公司财务指标 - 带息债务'],
    ('netdebt', 'q', 'E'):                            ['financial', 'netdebt', '上市公司财务指标 - 净债务'],
    ('tangible_asset', 'q', 'E'):                     ['financial', 'tangible_asset', '上市公司财务指标 - 有形资产'],
    ('working_capital', 'q', 'E'):                    ['financial', 'working_capital', '上市公司财务指标 - 营运资金'],
    ('networking_capital', 'q', 'E'):                 ['financial', 'networking_capital',
                                                       '上市公司财务指标 - 营运流动资本'],
    ('invest_capital', 'q', 'E'):                     ['financial', 'invest_capital',
                                                       '上市公司财务指标 - 全部投入资本'],
    ('retained_earnings', 'q', 'E'):                  ['financial', 'retained_earnings', '上市公司财务指标 - 留存收益'],
    ('diluted2_eps', 'q', 'E'):                       ['financial', 'diluted2_eps',
                                                       '上市公司财务指标 - 期末摊薄每股收益'],
    ('express_bps', 'q', 'E'):                        ['financial', 'bps', '上市公司财务指标 - 每股净资产'],
    ('ocfps', 'q', 'E'):                              ['financial', 'ocfps',
                                                       '上市公司财务指标 - 每股经营活动产生的现金流量净额'],
    ('retainedps', 'q', 'E'):                         ['financial', 'retainedps', '上市公司财务指标 - 每股留存收益'],
    ('cfps', 'q', 'E'):                               ['financial', 'cfps', '上市公司财务指标 - 每股现金流量净额'],
    ('ebit_ps', 'q', 'E'):                            ['financial', 'ebit_ps', '上市公司财务指标 - 每股息税前利润'],
    ('fcff_ps', 'q', 'E'):                            ['financial', 'fcff_ps',
                                                       '上市公司财务指标 - 每股企业自由现金流量'],
    ('fcfe_ps', 'q', 'E'):                            ['financial', 'fcfe_ps',
                                                       '上市公司财务指标 - 每股股东自由现金流量'],
    ('netprofit_margin', 'q', 'E'):                   ['financial', 'netprofit_margin',
                                                       '上市公司财务指标 - 销售净利率'],
    ('grossprofit_margin', 'q', 'E'):                 ['financial', 'grossprofit_margin',
                                                       '上市公司财务指标 - 销售毛利率'],
    ('cogs_of_sales', 'q', 'E'):                      ['financial', 'cogs_of_sales', '上市公司财务指标 - 销售成本率'],
    ('expense_of_sales', 'q', 'E'):                   ['financial', 'expense_of_sales',
                                                       '上市公司财务指标 - 销售期间费用率'],
    ('profit_to_gr', 'q', 'E'):                       ['financial', 'profit_to_gr',
                                                       '上市公司财务指标 - 净利润/营业总收入'],
    ('saleexp_to_gr', 'q', 'E'):                      ['financial', 'saleexp_to_gr',
                                                       '上市公司财务指标 - 销售费用/营业总收入'],
    ('adminexp_of_gr', 'q', 'E'):                     ['financial', 'adminexp_of_gr',
                                                       '上市公司财务指标 - 管理费用/营业总收入'],
    ('finaexp_of_gr', 'q', 'E'):                      ['financial', 'finaexp_of_gr',
                                                       '上市公司财务指标 - 财务费用/营业总收入'],
    ('impai_ttm', 'q', 'E'):                          ['financial', 'impai_ttm',
                                                       '上市公司财务指标 - 资产减值损失/营业总收入'],
    ('gc_of_gr', 'q', 'E'):                           ['financial', 'gc_of_gr',
                                                       '上市公司财务指标 - 营业总成本/营业总收入'],
    ('op_of_gr', 'q', 'E'):                           ['financial', 'op_of_gr',
                                                       '上市公司财务指标 - 营业利润/营业总收入'],
    ('ebit_of_gr', 'q', 'E'):                         ['financial', 'ebit_of_gr',
                                                       '上市公司财务指标 - 息税前利润/营业总收入'],
    ('roe', 'q', 'E'):                                ['financial', 'roe', '上市公司财务指标 - 净资产收益率'],
    ('roe_waa', 'q', 'E'):                            ['financial', 'roe_waa',
                                                       '上市公司财务指标 - 加权平均净资产收益率'],
    ('roe_dt', 'q', 'E'):                             ['financial', 'roe_dt',
                                                       '上市公司财务指标 - 净资产收益率(扣除非经常损益)'],
    ('roa', 'q', 'E'):                                ['financial', 'roa', '上市公司财务指标 - 总资产报酬率'],
    ('npta', 'q', 'E'):                               ['financial', 'npta', '上市公司财务指标 - 总资产净利润'],
    ('roic', 'q', 'E'):                               ['financial', 'roic', '上市公司财务指标 - 投入资本回报率'],
    ('roe_yearly', 'q', 'E'):                         ['financial', 'roe_yearly',
                                                       '上市公司财务指标 - 年化净资产收益率'],
    ('roa2_yearly', 'q', 'E'):                        ['financial', 'roa2_yearly',
                                                       '上市公司财务指标 - 年化总资产报酬率'],
    ('roe_avg', 'q', 'E'):                            ['financial', 'roe_avg',
                                                       '上市公司财务指标 - 平均净资产收益率(增发条件)'],
    ('opincome_of_ebt', 'q', 'E'):                    ['financial', 'opincome_of_ebt',
                                                       '上市公司财务指标 - 经营活动净收益/利润总额'],
    ('investincome_of_ebt', 'q', 'E'):                ['financial', 'investincome_of_ebt',
                                                       '上市公司财务指标 - 价值变动净收益/利润总额'],
    ('n_op_profit_of_ebt', 'q', 'E'):                 ['financial', 'n_op_profit_of_ebt',
                                                       '上市公司财务指标 - 营业外收支净额/利润总额'],
    ('tax_to_ebt', 'q', 'E'):                         ['financial', 'tax_to_ebt', '上市公司财务指标 - 所得税/利润总额'],
    ('dtprofit_to_profit', 'q', 'E'):                 ['financial', 'dtprofit_to_profit',
                                                       '上市公司财务指标 - 扣除非经常损益后的净利润/净利润'],
    ('salescash_to_or', 'q', 'E'):                    ['financial', 'salescash_to_or',
                                                       '上市公司财务指标 - 销售商品提供劳务收到的现金/营业收入'],
    ('ocf_to_or', 'q', 'E'):                          ['financial', 'ocf_to_or',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额/营业收入'],
    ('ocf_to_opincome', 'q', 'E'):                    ['financial', 'ocf_to_opincome',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额/经营活动净收益'],
    ('capitalized_to_da', 'q', 'E'):                  ['financial', 'capitalized_to_da',
                                                       '上市公司财务指标 - 资本支出/折旧和摊销'],
    ('debt_to_assets', 'q', 'E'):                     ['financial', 'debt_to_assets', '上市公司财务指标 - 资产负债率'],
    ('assets_to_eqt', 'q', 'E'):                      ['financial', 'assets_to_eqt', '上市公司财务指标 - 权益乘数'],
    ('dp_assets_to_eqt', 'q', 'E'):                   ['financial', 'dp_assets_to_eqt',
                                                       '上市公司财务指标 - 权益乘数(杜邦分析)'],
    ('ca_to_assets', 'q', 'E'):                       ['financial', 'ca_to_assets',
                                                       '上市公司财务指标 - 流动资产/总资产'],
    ('nca_to_assets', 'q', 'E'):                      ['financial', 'nca_to_assets',
                                                       '上市公司财务指标 - 非流动资产/总资产'],
    ('tbassets_to_totalassets', 'q', 'E'):            ['financial', 'tbassets_to_totalassets',
                                                       '上市公司财务指标 - 有形资产/总资产'],
    ('int_to_talcap', 'q', 'E'):                      ['financial', 'int_to_talcap',
                                                       '上市公司财务指标 - 带息债务/全部投入资本'],
    ('eqt_to_talcapital', 'q', 'E'):                  ['financial', 'eqt_to_talcapital',
                                                       '上市公司财务指标 - 归属于母公司的股东权益/全部投入资本'],
    ('currentdebt_to_debt', 'q', 'E'):                ['financial', 'currentdebt_to_debt',
                                                       '上市公司财务指标 - 流动负债/负债合计'],
    ('longdeb_to_debt', 'q', 'E'):                    ['financial', 'longdeb_to_debt',
                                                       '上市公司财务指标 - 非流动负债/负债合计'],
    ('ocf_to_shortdebt', 'q', 'E'):                   ['financial', 'ocf_to_shortdebt',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额/流动负债'],
    ('debt_to_eqt', 'q', 'E'):                        ['financial', 'debt_to_eqt', '上市公司财务指标 - 产权比率'],
    ('eqt_to_debt', 'q', 'E'):                        ['financial', 'eqt_to_debt',
                                                       '上市公司财务指标 - 归属于母公司的股东权益/负债合计'],
    ('eqt_to_interestdebt', 'q', 'E'):                ['financial', 'eqt_to_interestdebt',
                                                       '上市公司财务指标 - 归属于母公司的股东权益/带息债务'],
    ('tangibleasset_to_debt', 'q', 'E'):              ['financial', 'tangibleasset_to_debt',
                                                       '上市公司财务指标 - 有形资产/负债合计'],
    ('tangasset_to_intdebt', 'q', 'E'):               ['financial', 'tangasset_to_intdebt',
                                                       '上市公司财务指标 - 有形资产/带息债务'],
    ('tangibleasset_to_netdebt', 'q', 'E'):           ['financial', 'tangibleasset_to_netdebt',
                                                       '上市公司财务指标 - 有形资产/净债务'],
    ('ocf_to_debt', 'q', 'E'):                        ['financial', 'ocf_to_debt',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额/负债合计'],
    ('ocf_to_interestdebt', 'q', 'E'):                ['financial', 'ocf_to_interestdebt',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额/带息债务'],
    ('ocf_to_netdebt', 'q', 'E'):                     ['financial', 'ocf_to_netdebt',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额/净债务'],
    ('ebit_to_interest', 'q', 'E'):                   ['financial', 'ebit_to_interest',
                                                       '上市公司财务指标 - 已获利息倍数(EBIT/利息费用)'],
    ('longdebt_to_workingcapital', 'q', 'E'):         ['financial', 'longdebt_to_workingcapital',
                                                       '上市公司财务指标 - 长期债务与营运资金比率'],
    ('ebitda_to_debt', 'q', 'E'):                     ['financial', 'ebitda_to_debt',
                                                       '上市公司财务指标 - 息税折旧摊销前利润/负债合计'],
    ('turn_days', 'q', 'E'):                          ['financial', 'turn_days', '上市公司财务指标 - 营业周期'],
    ('roa_yearly', 'q', 'E'):                         ['financial', 'roa_yearly',
                                                       '上市公司财务指标 - 年化总资产净利率'],
    ('roa_dp', 'q', 'E'):                             ['financial', 'roa_dp',
                                                       '上市公司财务指标 - 总资产净利率(杜邦分析)'],
    ('fixed_assets', 'q', 'E'):                       ['financial', 'fixed_assets', '上市公司财务指标 - 固定资产合计'],
    ('profit_prefin_exp', 'q', 'E'):                  ['financial', 'profit_prefin_exp',
                                                       '上市公司财务指标 - 扣除财务费用前营业利润'],
    ('non_op_profit', 'q', 'E'):                      ['financial', 'non_op_profit', '上市公司财务指标 - 非营业利润'],
    ('op_to_ebt', 'q', 'E'):                          ['financial', 'op_to_ebt',
                                                       '上市公司财务指标 - 营业利润／利润总额'],
    ('nop_to_ebt', 'q', 'E'):                         ['financial', 'nop_to_ebt',
                                                       '上市公司财务指标 - 非营业利润／利润总额'],
    ('ocf_to_profit', 'q', 'E'):                      ['financial', 'ocf_to_profit',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额／营业利润'],
    ('cash_to_liqdebt', 'q', 'E'):                    ['financial', 'cash_to_liqdebt',
                                                       '上市公司财务指标 - 货币资金／流动负债'],
    ('cash_to_liqdebt_withinterest', 'q', 'E'):       ['financial', 'cash_to_liqdebt_withinterest',
                                                       '上市公司财务指标 - 货币资金／带息流动负债'],
    ('op_to_liqdebt', 'q', 'E'):                      ['financial', 'op_to_liqdebt',
                                                       '上市公司财务指标 - 营业利润／流动负债'],
    ('op_to_debt', 'q', 'E'):                         ['financial', 'op_to_debt',
                                                       '上市公司财务指标 - 营业利润／负债合计'],
    ('roic_yearly', 'q', 'E'):                        ['financial', 'roic_yearly',
                                                       '上市公司财务指标 - 年化投入资本回报率'],
    ('total_fa_trun', 'q', 'E'):                      ['financial', 'total_fa_trun',
                                                       '上市公司财务指标 - 固定资产合计周转率'],
    ('profit_to_op', 'q', 'E'):                       ['financial', 'profit_to_op',
                                                       '上市公司财务指标 - 利润总额／营业收入'],
    ('q_opincome', 'q', 'E'):                         ['financial', 'q_opincome',
                                                       '上市公司财务指标 - 经营活动单季度净收益'],
    ('q_investincome', 'q', 'E'):                     ['financial', 'q_investincome',
                                                       '上市公司财务指标 - 价值变动单季度净收益'],
    ('q_dtprofit', 'q', 'E'):                         ['financial', 'q_dtprofit',
                                                       '上市公司财务指标 - 扣除非经常损益后的单季度净利润'],
    ('q_eps', 'q', 'E'):                              ['financial', 'q_eps', '上市公司财务指标 - 每股收益(单季度)'],
    ('q_netprofit_margin', 'q', 'E'):                 ['financial', 'q_netprofit_margin',
                                                       '上市公司财务指标 - 销售净利率(单季度)'],
    ('q_gsprofit_margin', 'q', 'E'):                  ['financial', 'q_gsprofit_margin',
                                                       '上市公司财务指标 - 销售毛利率(单季度)'],
    ('q_exp_to_sales', 'q', 'E'):                     ['financial', 'q_exp_to_sales',
                                                       '上市公司财务指标 - 销售期间费用率(单季度)'],
    ('q_profit_to_gr', 'q', 'E'):                     ['financial', 'q_profit_to_gr',
                                                       '上市公司财务指标 - 净利润／营业总收入(单季度)'],
    ('q_saleexp_to_gr', 'q', 'E'):                    ['financial', 'q_saleexp_to_gr',
                                                       '上市公司财务指标 - 销售费用／营业总收入 (单季度)'],
    ('q_adminexp_to_gr', 'q', 'E'):                   ['financial', 'q_adminexp_to_gr',
                                                       '上市公司财务指标 - 管理费用／营业总收入 (单季度)'],
    ('q_finaexp_to_gr', 'q', 'E'):                    ['financial', 'q_finaexp_to_gr',
                                                       '上市公司财务指标 - 财务费用／营业总收入 (单季度)'],
    ('q_impair_to_gr_ttm', 'q', 'E'):                 ['financial', 'q_impair_to_gr_ttm',
                                                       '上市公司财务指标 - 资产减值损失／营业总收入(单季度)'],
    ('q_gc_to_gr', 'q', 'E'):                         ['financial', 'q_gc_to_gr',
                                                       '上市公司财务指标 - 营业总成本／营业总收入 (单季度)'],
    ('q_op_to_gr', 'q', 'E'):                         ['financial', 'q_op_to_gr',
                                                       '上市公司财务指标 - 营业利润／营业总收入(单季度)'],
    ('q_roe', 'q', 'E'):                              ['financial', 'q_roe', '上市公司财务指标 - 净资产收益率(单季度)'],
    ('q_dt_roe', 'q', 'E'):                           ['financial', 'q_dt_roe',
                                                       '上市公司财务指标 - 净资产单季度收益率(扣除非经常损益)'],
    ('q_npta', 'q', 'E'):                             ['financial', 'q_npta',
                                                       '上市公司财务指标 - 总资产净利润(单季度)'],
    ('q_opincome_to_ebt', 'q', 'E'):                  ['financial', 'q_opincome_to_ebt',
                                                       '上市公司财务指标 - 经营活动净收益／利润总额(单季度)'],
    ('q_investincome_to_ebt', 'q', 'E'):              ['financial', 'q_investincome_to_ebt',
                                                       '上市公司财务指标 - 价值变动净收益／利润总额(单季度)'],
    ('q_dtprofit_to_profit', 'q', 'E'):               ['financial', 'q_dtprofit_to_profit',
                                                       '上市公司财务指标 - 扣除非经常损益后的净利润／净利润(单季度)'],
    ('q_salescash_to_or', 'q', 'E'):                  ['financial', 'q_salescash_to_or',
                                                       '上市公司财务指标 - 销售商品提供劳务收到的现金／营业收入(单季度)'],
    ('q_ocf_to_sales', 'q', 'E'):                     ['financial', 'q_ocf_to_sales',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额／营业收入(单季度)'],
    ('q_ocf_to_or', 'q', 'E'):                        ['financial', 'q_ocf_to_or',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额／经营活动净收益(单季度)'],
    ('basic_eps_yoy', 'q', 'E'):                      ['financial', 'basic_eps_yoy',
                                                       '上市公司财务指标 - 基本每股收益同比增长率(%)'],
    ('dt_eps_yoy', 'q', 'E'):                         ['financial', 'dt_eps_yoy',
                                                       '上市公司财务指标 - 稀释每股收益同比增长率(%)'],
    ('cfps_yoy', 'q', 'E'):                           ['financial', 'cfps_yoy',
                                                       '上市公司财务指标 - 每股经营活动产生的现金流量净额同比增长率(%)'],
    ('op_yoy', 'q', 'E'):                             ['financial', 'op_yoy',
                                                       '上市公司财务指标 - 营业利润同比增长率(%)'],
    ('ebt_yoy', 'q', 'E'):                            ['financial', 'ebt_yoy',
                                                       '上市公司财务指标 - 利润总额同比增长率(%)'],
    ('netprofit_yoy', 'q', 'E'):                      ['financial', 'netprofit_yoy',
                                                       '上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)'],
    ('dt_netprofit_yoy', 'q', 'E'):                   ['financial', 'dt_netprofit_yoy',
                                                       '上市公司财务指标 - 归属母公司股东的净利润-扣除非经常损益同比增长率(%)'],
    ('ocf_yoy', 'q', 'E'):                            ['financial', 'ocf_yoy',
                                                       '上市公司财务指标 - 经营活动产生的现金流量净额同比增长率(%)'],
    ('roe_yoy', 'q', 'E'):                            ['financial', 'roe_yoy',
                                                       '上市公司财务指标 - 净资产收益率(摊薄)同比增长率(%)'],
    ('bps_yoy', 'q', 'E'):                            ['financial', 'bps_yoy',
                                                       '上市公司财务指标 - 每股净资产相对年初增长率(%)'],
    ('assets_yoy', 'q', 'E'):                         ['financial', 'assets_yoy',
                                                       '上市公司财务指标 - 资产总计相对年初增长率(%)'],
    ('eqt_yoy', 'q', 'E'):                            ['financial', 'eqt_yoy',
                                                       '上市公司财务指标 - 归属母公司的股东权益相对年初增长率(%)'],
    ('tr_yoy', 'q', 'E'):                             ['financial', 'tr_yoy',
                                                       '上市公司财务指标 - 营业总收入同比增长率(%)'],
    ('or_yoy', 'q', 'E'):                             ['financial', 'or_yoy',
                                                       '上市公司财务指标 - 营业收入同比增长率(%)'],
    ('q_gr_yoy', 'q', 'E'):                           ['financial', 'q_gr_yoy',
                                                       '上市公司财务指标 - 营业总收入同比增长率(%)(单季度)'],
    ('q_gr_qoq', 'q', 'E'):                           ['financial', 'q_gr_qoq',
                                                       '上市公司财务指标 - 营业总收入环比增长率(%)(单季度)'],
    ('q_sales_yoy', 'q', 'E'):                        ['financial', 'q_sales_yoy',
                                                       '上市公司财务指标 - 营业收入同比增长率(%)(单季度)'],
    ('q_sales_qoq', 'q', 'E'):                        ['financial', 'q_sales_qoq',
                                                       '上市公司财务指标 - 营业收入环比增长率(%)(单季度)'],
    ('q_op_yoy', 'q', 'E'):                           ['financial', 'q_op_yoy',
                                                       '上市公司财务指标 - 营业利润同比增长率(%)(单季度)'],
    ('q_op_qoq', 'q', 'E'):                           ['financial', 'q_op_qoq',
                                                       '上市公司财务指标 - 营业利润环比增长率(%)(单季度)'],
    ('q_profit_yoy', 'q', 'E'):                       ['financial', 'q_profit_yoy',
                                                       '上市公司财务指标 - 净利润同比增长率(%)(单季度)'],
    ('q_profit_qoq', 'q', 'E'):                       ['financial', 'q_profit_qoq',
                                                       '上市公司财务指标 - 净利润环比增长率(%)(单季度)'],
    ('q_netprofit_yoy', 'q', 'E'):                    ['financial', 'q_netprofit_yoy',
                                                       '上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)(单季度)'],
    ('q_netprofit_qoq', 'q', 'E'):                    ['financial', 'q_netprofit_qoq',
                                                       '上市公司财务指标 - 归属母公司股东的净利润环比增长率(%)(单季度)'],
    ('equity_yoy', 'q', 'E'):                         ['financial', 'equity_yoy',
                                                       '上市公司财务指标 - 净资产同比增长率'],
    ('rd_exp', 'q', 'E'):                             ['financial', 'rd_exp', '上市公司财务指标 - 研发费用'],
    ('rzye', 'd', 'Any'):                             ['margin', 'rzye', '融资融券交易汇总 - 融资余额(元)'],
    ('rzmre', 'd', 'Any'):                            ['margin', 'rzmre', '融资融券交易汇总 - 融资买入额(元)'],
    ('rzche', 'd', 'Any'):                            ['margin', 'rzche', '融资融券交易汇总 - 融资偿还额(元)'],
    ('rqye', 'd', 'Any'):                             ['margin', 'rqye', '融资融券交易汇总 - 融券余额(元)'],
    ('rqmcl', 'd', 'Any'):                            ['margin', 'rqmcl', '融资融券交易汇总 - 融券卖出量(股,份,手)'],
    ('rzrqye', 'd', 'Any'):                           ['margin', 'rzrqye', '融资融券交易汇总 - 融资融券余额(元)'],
    ('rqyl', 'd', 'Any'):                             ['margin', 'rqyl', '融资融券交易汇总 - 融券余量(股,份,手)'],
    ('close', 'd', 'Any'):                            ['top_list', 'close', '融资融券交易明细 - 收盘价'],
    ('pct_change', 'd', 'Any'):                       ['top_list', 'pct_change', '融资融券交易明细 - 涨跌幅'],
    ('turnover_rate', 'd', 'Any'):                    ['top_list', 'turnover_rate', '融资融券交易明细 - 换手率'],
    ('amount', 'd', 'Any'):                           ['top_list', 'amount', '融资融券交易明细 - 总成交额'],
    ('l_sell', 'd', 'Any'):                           ['top_list', 'l_sell', '融资融券交易明细 - 龙虎榜卖出额'],
    ('l_buy', 'd', 'Any'):                            ['top_list', 'l_buy', '融资融券交易明细 - 龙虎榜买入额'],
    ('l_amount', 'd', 'Any'):                         ['top_list', 'l_amount', '融资融券交易明细 - 龙虎榜成交额'],
    ('net_amount', 'd', 'Any'):                       ['top_list', 'net_amount', '融资融券交易明细 - 龙虎榜净买入额'],
    ('net_rate', 'd', 'Any'):                         ['top_list', 'net_rate', '融资融券交易明细 - 龙虎榜净买额占比'],
    ('amount_rate', 'd', 'Any'):                      ['top_list', 'amount_rate',
                                                       '融资融券交易明细 - 龙虎榜成交额占比'],
    ('float_values', 'd', 'Any'):                     ['top_list', 'float_values', '融资融券交易明细 - 当日流通市值'],
    ('reason', 'd', 'Any'):                           ['top_list', 'reason', '融资融券交易明细 - 上榜理由'],
    ('total_mv', 'd', 'IDX'):                         ['index_indicator', 'total_mv', '指数技术指标 - 当日总市值（元）'],
    ('float_mv', 'd', 'IDX'):                         ['index_indicator', 'float_mv',
                                                       '指数技术指标 - 当日流通市值（元）'],
    ('total_share     float', 'd', 'IDX'):            ['index_indicator', 'total_share     float',
                                                       '指数技术指标 - 当日总股本（股）'],
    ('float_share', 'd', 'IDX'):                      ['index_indicator', 'float_share',
                                                       '指数技术指标 - 当日流通股本（股）'],
    ('free_share', 'd', 'IDX'):                       ['index_indicator', 'free_share',
                                                       '指数技术指标 - 当日自由流通股本（股）'],
    ('turnover_rate', 'd', 'IDX'):                    ['index_indicator', 'turnover_rate', '指数技术指标 - 换手率'],
    ('turnover_rate_f', 'd', 'IDX'):                  ['index_indicator', 'turnover_rate_f',
                                                       '指数技术指标 - 换手率(基于自由流通股本)'],
    ('pe', 'd', 'IDX'):                               ['index_indicator', 'pe', '指数技术指标 - 市盈率'],
    ('pe_ttm', 'd', 'IDX'):                           ['index_indicator', 'pe_ttm', '指数技术指标 - 市盈率TTM'],
    ('pb', 'd', 'IDX'):                               ['index_indicator', 'pb', '指数技术指标 - 市净率'],
    ('turnover_rate', 'd', 'E'):                      ['stock_indicator', 'turnover_rate', '股票技术指标 - 换手率（%）'],
    ('turnover_rate_f', 'd', 'E'):                    ['stock_indicator', 'turnover_rate_f',
                                                       '股票技术指标 - 换手率（自由流通股）'],
    ('volume_ratio', 'd', 'E'):                       ['stock_indicator', 'volume_ratio', '股票技术指标 - 量比'],
    ('pe', 'd', 'E'):                                 ['stock_indicator', 'pe',
                                                       '股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）'],
    ('pe_ttm', 'd', 'E'):                             ['stock_indicator', 'pe_ttm',
                                                       '股票技术指标 - 市盈率（TTM，亏损的PE为空）'],
    ('pb', 'd', 'E'):                                 ['stock_indicator', 'pb', '股票技术指标 - 市净率（总市值/净资产）'],
    ('ps', 'd', 'E'):                                 ['stock_indicator', 'ps', '股票技术指标 - 市销率'],
    ('ps_ttm', 'd', 'E'):                             ['stock_indicator', 'ps_ttm', '股票技术指标 - 市销率（TTM）'],
    ('dv_ratio', 'd', 'E'):                           ['stock_indicator', 'dv_ratio', '股票技术指标 - 股息率 （%）'],
    ('dv_ttm', 'd', 'E'):                             ['stock_indicator', 'dv_ttm', '股票技术指标 - 股息率（TTM）（%）'],
    ('total_share', 'd', 'E'):                        ['stock_indicator', 'total_share',
                                                       '股票技术指标 - 总股本 （万股）'],
    ('float_share', 'd', 'E'):                        ['stock_indicator', 'float_share',
                                                       '股票技术指标 - 流通股本 （万股）'],
    ('free_share', 'd', 'E'):                         ['stock_indicator', 'free_share',
                                                       '股票技术指标 - 自由流通股本 （万）'],
    ('total_mv', 'd', 'E'):                           ['stock_indicator', 'total_mv', '股票技术指标 - 总市值 （万元）'],
    ('circ_mv', 'd', 'E'):                            ['stock_indicator', 'circ_mv', '股票技术指标 - 流通市值（万元）'],
    ('vol_ratio', 'd', 'E'):                          ['stock_indicator2', 'vol_ratio', '股票技术指标 - 量比'],
    ('turn_over', 'd', 'E'):                          ['stock_indicator2', 'turn_over', '股票技术指标 - 换手率'],
    ('swing', 'd', 'E'):                              ['stock_indicator2', 'swing', '股票技术指标 - 振幅'],
    ('selling', 'd', 'E'):                            ['stock_indicator2', 'selling', '股票技术指标 - 内盘（主动卖，手）'],
    ('buying', 'd', 'E'):                             ['stock_indicator2', 'buying', '股票技术指标 - 外盘（主动买， 手）'],
    ('total_share_b', 'd', 'E'):                      ['stock_indicator2', 'total_share', '股票技术指标 - 总股本(亿)'],
    ('float_share_b', 'd', 'E'):                      ['stock_indicator2', 'float_share',
                                                       '股票技术指标 - 流通股本(亿)'],
    ('pe_2', 'd', 'E'):                               ['stock_indicator2', 'pe', '股票技术指标 - 动态市盈率'],
    ('industry', 'd', 'E'):                           ['stock_indicator2', 'industry', '股票技术指标 - 所属行业'],
    ('area', 'd', 'E'):                               ['stock_indicator2', 'area', '股票技术指标 - 所属地域'],
    ('float_mv_2', 'd', 'E'):                         ['stock_indicator2', 'float_mv', '股票技术指标 - 流通市值'],
    ('total_mv_2', 'd', 'E'):                         ['stock_indicator2', 'total_mv', '股票技术指标 - 总市值'],
    ('avg_price', 'd', 'E'):                          ['stock_indicator2', 'avg_price', '股票技术指标 - 平均价'],
    ('strength', 'd', 'E'):                           ['stock_indicator2', 'strength', '股票技术指标 - 强弱度(%)'],
    ('activity', 'd', 'E'):                           ['stock_indicator2', 'activity', '股票技术指标 - 活跃度(%)'],
    ('avg_turnover', 'd', 'E'):                       ['stock_indicator2', 'avg_turnover', '股票技术指标 - 笔换手'],
    ('attack', 'd', 'E'):                             ['stock_indicator2', 'attack', '股票技术指标 - 攻击波(%)'],
    ('interval_3', 'd', 'E'):                         ['stock_indicator2', 'interval_3', '股票技术指标 - 近3月涨幅'],
    ('interval_6', 'd', 'E'):                         ['stock_indicator2', 'interval_6', '股票技术指标 - 近6月涨幅'],
}
# Table_masters，用于存储表的基本信息
TABLE_MASTER_COLUMNS = [
    'schema',  # 数据表schema
    'desc',   # 数据表描述
    'table_usage',   # 数据表用途
    'asset_type',   # 资产类型
    'freq',   # 数据频率
    'tushare',   # 从tushare获取数据时使用的api名
    'fill_arg_name',  # 从tushare获取数据时使用的api参数名
    'fill_arg_type',   # 从tushare获取数据时使用的api参数类型
    'arg_rng',   # 从tushare获取数据时使用的api参数取值范围
    'arg_allowed_code_suffix',   # 从tushare获取数据时使用的api参数允许的股票代码后缀
    'arg_allow_start_end',  # 从tushare获取数据时使用的api参数允许的start_date和end_date
    'start_end_chunk_size',   # 从tushare获取数据时使用的api参数start_date和end_date的最大时间跨度
    # 'eastmoney',   # 从eastmoney获取数据时使用的api名
    # 'fill_arg_name',   # 从eastmoney获取数据时使用的api参数名
    # 'fill_arg_type',   # 从eastmoney获取数据时使用的api参数类型
    # 'arg_rng',  # 从eastmoney获取数据时使用的api参数取值范围
]
TABLE_MASTERS = {

    'sys_op_live_accounts':
        ['sys_op_live_accounts', '实盘运行基本信息主记录表', 'sys', '', '', '', '', '', '', '', '', ''],

    'sys_op_positions':
        ['sys_op_positions', '实盘运行持仓记录', 'sys', '', '', '', '', '', '', '', '', ''],

    'sys_op_trade_orders':
        ['sys_op_trade_orders', '实盘运行交易订单记录表', 'sys', '', '', '', '', '', '', '', '', ''],

    'sys_op_trade_results':
        ['sys_op_trade_results', '实盘运行交易结果记录表', 'sys', '', '', '', '', '', '', '', '', ''],

    'trade_calendar':
        ['trade_calendar', '交易日历', 'cal', 'none', 'none', 'trade_calendar', 'exchange', 'list',
         'SSE,SZSE,BSE,CFFEX,SHFE,CZCE,DCE,INE,XHKG', '', '', ''],

    'stock_basic':
        ['stock_basic', '股票基本信息', 'basics', 'E', 'none', 'stock_basic', 'exchange', 'list', 'SSE,SZSE,BSE', '',
         '',
         ''],

    'stock_names':
        ['name_changes', '股票名称变更', 'events', 'E', 'none', 'name_change', 'ts_code', 'table_index', 'stock_basic',
         '', 'Y', ''],

    'stock_company':
        ['stock_company', '上市公司基本信息', 'basics', 'E', 'none', 'stock_company', 'exchange', 'list',
         'SSE, SZSE, BSE',
         '', '', ''],

    'stk_managers':
        ['stk_managers', '上市公司管理层', 'events', 'E', 'd', 'stk_managers', 'ann_date', 'datetime', '19901211',
         '', '', ''],

    'new_share':
        ['new_share', 'IPO新股列表', 'events', 'E', 'd', 'new_share', 'none', 'none', 'none',
         '', 'Y', '200'],

    'index_basic':
        ['index_basic', '指数基本信息', 'basics', 'IDX', 'none', 'index_basic', 'market', 'list',
         'SSE,MSCI,CSI,SZSE,CICC,SW,OTH', '', '', ''],

    'fund_basic':
        ['fund_basic', '基金基本信息', 'basics', 'FD', 'none', 'fund_basic', 'market', 'list', 'E,O', '', '', ''],

    'future_basic':
        ['future_basic', '期货基本信息', 'basics', 'FT', 'none', 'future_basic', 'exchange', 'list',
         'CFFEX,DCE,CZCE,SHFE,INE', '', '', ''],

    'opt_basic':
        ['opt_basic', '期权基本信息', 'basics', 'OPT', 'none', 'options_basic', 'exchange', 'list',
         'SSE,SZSE,CFFEX,DCE,CZCE,SHFE', '', '', ''],

    'stock_1min':
        ['min_bars', '股票分钟K线行情', 'mins', 'E', '1min', 'mins1', 'ts_code', 'table_index', 'stock_basic', '', 'y',
         '30'],

    'stock_5min':
        ['min_bars', '股票5分钟K线行情', 'mins', 'E', '5min', 'mins5', 'ts_code', 'table_index', 'stock_basic', '', 'y',
         '90'],

    'stock_15min':
        ['min_bars', '股票15分钟K线行情', 'mins', 'E', '15min', 'mins15', 'ts_code', 'table_index', 'stock_basic', '',
         'y', '180'],

    'stock_30min':
        ['min_bars', '股票30分钟K线行情', 'mins', 'E', '30min', 'mins30', 'ts_code', 'table_index', 'stock_basic', '',
         'y', '360'],

    'stock_hourly':
        ['min_bars', '股票60分钟K线行情', 'mins', 'E', 'h', 'mins60', 'ts_code', 'table_index', 'stock_basic', '',
         'y', '360'],

    'stock_daily':
        ['bars', '股票日线行情', 'data', 'E', 'd', 'daily', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'stock_weekly':
        ['bars', '股票周线行情', 'data', 'E', 'w', 'weekly', 'trade_date', 'trade_date', '19901221', '', '', ''],

    'stock_monthly':
        ['bars', '股票月线行情', 'data', 'E', 'm', 'monthly', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'index_1min':
        ['min_bars', '指数分钟K线行情', 'mins', 'IDX', '1min', 'mins1', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ',
         'y', '30'],

    'index_5min':
        ['min_bars', '指数5分钟K线行情', 'mins', 'IDX', '5min', 'mins5', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ',
         'y', '90'],

    'index_15min':
        ['min_bars', '指数15分钟K线行情', 'mins', 'IDX', '15min', 'mins15', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ', 'y', '180'],

    'index_30min':
        ['min_bars', '指数30分钟K线行情', 'mins', 'IDX', '30min', 'mins30', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ', 'y', '360'],

    'index_hourly':
        ['min_bars', '指数60分钟K线行情', 'mins', 'IDX', 'h', 'mins60', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ', 'y', '360'],

    'index_daily':
        ['bars', '指数日线行情', 'data', 'IDX', 'd', 'index_daily', 'ts_code', 'table_index', 'index_basic',
         'SH,CSI,SZ',
         'y', ''],

    'index_weekly':
        ['bars', '指数周线行情', 'data', 'IDX', 'w', 'index_weekly', 'trade_date', 'trade_date', '19910705', '', '',
         ''],

    'index_monthly':
        ['bars', '指数月度行情', 'data', 'IDX', 'm', 'index_monthly', 'trade_date', 'trade_date', '19910731', '', '',
         ''],

    'fund_1min':
        ['min_bars', '场内基金分钟K线行情', 'mins', 'FD', '1min', 'mins1', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ',
         'y', '30'],

    'fund_5min':
        ['min_bars', '场内基金5分钟K线行情', 'mins', 'FD', '5min', 'mins5', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ',
         'y', '90'],

    'fund_15min':
        ['min_bars', '场内基金15分钟K线行情', 'mins', 'FD', '15min', 'mins15', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ', 'y', '180'],

    'fund_30min':
        ['min_bars', '场内基金30分钟K线行情', 'mins', 'FD', '30min', 'mins30', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ', 'y', '360'],

    'fund_hourly':
        ['min_bars', '场内基金60分钟K线行情', 'mins', 'FD', 'h', 'mins60', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ', 'y', '360'],

    'fund_daily':
        ['bars', '场内基金每日行情', 'data', 'FD', 'd', 'fund_daily', 'trade_date', 'trade_date', '19980417', '', '',
         ''],

    'fund_nav':
        ['fund_nav', '场外基金每日净值', 'data', 'FD', 'd', 'fund_net_value', 'nav_date', 'datetime', '20000107', '',
         '', ''],

    'fund_share':
        ['fund_share', '基金份额', 'events', 'FD', 'none', 'fund_share', 'ts_code', 'table_index', 'fund_basic', '', '',
         ''],

    'fund_manager':
        ['fund_manager', '基金经理', 'events', 'FD', 'none', 'fund_manager', 'ts_code', 'table_index', 'fund_basic',
         'OF, SZ, SH', '', ''],

    'future_1min':
        ['future_mins', '期货分钟K线行情', 'mins', 'FT', '1min', 'ft_mins1', 'ts_code', 'table_index', 'future_basic',
         '', 'y', '30'],

    'future_5min':
        ['future_mins', '期货5分钟K线行情', 'mins', 'FT', '5min', 'ft_mins5', 'ts_code', 'table_index', 'future_basic',
         '', 'y', '90'],

    'future_15min':
        ['future_mins', '期货15分钟K线行情', 'mins', 'FT', '15min', 'ft_mins15', 'ts_code', 'table_index',
         'future_basic',
         '', 'y', '180'],

    'future_30min':
        ['future_mins', '期货30分钟K线行情', 'mins', 'FT', '30min', 'ft_mins30', 'ts_code', 'table_index',
         'future_basic',
         '', 'y', '360'],

    'future_hourly':
        ['future_mins', '期货60分钟K线行情', 'mins', 'FT', 'h', 'ft_mins60', 'ts_code', 'table_index', 'future_basic',
         '', 'y', '360'],

    'future_daily':
        ['future_daily', '期货每日行情', 'data', 'FT', 'd', 'future_daily', 'trade_date', 'datetime', '19950417', '',
         '', ''],

    'options_1min':
        ['min_bars', '期权分钟K线行情', 'mins', 'OPT', '1min', 'mins1', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '30'],

    'options_5min':
        ['min_bars', '期权5分钟K线行情', 'mins', 'OPT', '5min', 'mins5', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '90'],

    'options_15min':
        ['min_bars', '期权15分钟K线行情', 'mins', 'OPT', '15min', 'mins15', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '180'],

    'options_30min':
        ['min_bars', '期权30分钟K线行情', 'mins', 'OPT', '30min', 'mins30', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '360'],

    'options_hourly':
        ['min_bars', '期权60分钟K线行情', 'mins', 'OPT', 'h', 'mins60', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '360'],

    'options_daily':
        ['options_daily', '期权每日行情', 'data', 'OPT', 'd', 'options_daily', 'trade_date', 'datetime', '20150209', '',
         '', ''],

    'stock_adj_factor':
        ['adj_factors', '股票价格复权系数', 'adj', 'E', 'd', 'adj_factors', 'trade_date', 'trade_date', '19901219', '',
         '', ''],

    'fund_adj_factor':
        ['adj_factors', '基金价格复权系数', 'adj', 'FD', 'd', 'fund_adj', 'trade_date', 'trade_date', '19980407', '',
         '',
         ''],

    'stock_indicator':
        ['stock_indicator', '股票技术指标', 'data', 'E', 'd', 'daily_basic', 'trade_date', 'trade_date', '19990101', '',
         '', ''],

    'stock_indicator2':
        ['stock_indicator2', '股票技术指标备用表', 'data', 'E', 'd', 'daily_basic2', 'trade_date', 'trade_date',
         '19990101', '', '', ''],

    'index_indicator':
        ['index_indicator', '指数关键指标', 'data', 'IDX', 'd', 'index_daily_basic', 'trade_date', 'datetime',
         '20040102', '', '', ''],

    'index_weight':
        ['index_weight', '指数成分', 'comp', 'IDX', 'd', 'composite', 'trade_date', 'datetime', '20050408', '', '', ''],

    'income':
        ['income', '上市公司利润表', 'report', 'E', 'q', 'income', 'ts_code', 'table_index', 'stock_basic', '', 'Y',
         ''],

    'balance':
        ['balance', '上市公司资产负债表', 'report', 'E', 'q', 'balance', 'ts_code', 'table_index', 'stock_basic', '',
         'Y',
         ''],

    'cashflow':
        ['cashflow', '上市公司现金流量表', 'report', 'E', 'q', 'cashflow', 'ts_code', 'table_index', 'stock_basic', '',
         'Y', ''],

    'financial':
        ['financial', '上市公司财务指标', 'report', 'E', 'q', 'indicators', 'ts_code', 'table_index', 'stock_basic', '',
         'Y', ''],

    'forecast':
        ['forecast', '上市公司财报预测', 'report', 'E', 'q', 'forecast', 'ts_code', 'table_index', 'stock_basic', '',
         'Y',
         ''],

    'express':
        ['express', '上市公司财报快报', 'report', 'E', 'q', 'express', 'ts_code', 'table_index', 'stock_basic', '', 'Y',
         ''],

    'shibor':
        ['shibor', '上海银行间行业拆放利率(SHIBOR)', 'data', 'none', 'd', 'shibor', 'date', 'trade_date', '20000101',
         '',
         'Y', ''],

    'libor':
        ['libor', '伦敦银行间行业拆放利率(LIBOR)', 'data', 'none', 'd', 'libor', 'date', 'trade_date', '20000101', '',
         'Y', ''],

    'hibor':
        ['hibor', '香港银行间行业拆放利率(HIBOR)', 'data', 'none', 'd', 'hibor', 'date', 'trade_date', '20000101', '',
         'Y', ''],

}
# Table schema，定义所有数据表的列名、数据类型、限制、主键以及注释，用于定义数据表的结构
TABLE_SCHEMA = {

    # TODO: 在live_account_master表中增加运行基本设置的字段如交易柜台连接设置、log设置、交易时间段设置、用户权限设置等，动态修改
    'sys_op_live_accounts':  # 交易账户表
        {'columns':    ['account_id', 'user_name', 'created_time', 'cash_amount', 'available_cash', 'total_invest'],
         'dtypes':     ['int', 'varchar(20)', 'datetime', 'double', 'double', 'double'],
         'remarks':    ['运行账号ID', '用户名', '创建时间', '现金总额', '可用现金总额', '总投资额'],
         'prime_keys': [0],
         },

    'sys_op_positions':  # 持仓表
        {'columns':    ['pos_id', 'account_id', 'symbol', 'position', 'qty', 'available_qty', 'cost'],
         'dtypes':     ['int', 'int', 'varchar(20)', 'varchar(5)', 'double', 'double', 'double'],
         'remarks':    ['持仓ID', '运行账号ID', '资产代码', '持仓类型(多long/空short)', '持仓数量', '可用数量',
                        '持仓成本'],
         'prime_keys': [0],
         },

    'sys_op_trade_orders':  # 交易订单表
        {'columns':    ['order_id', 'pos_id', 'direction', 'order_type', 'qty', 'price',
                        'submitted_time', 'status'],
         'dtypes':     ['int', 'int', 'varchar(10)', 'varchar(8)', 'double', 'double',
                        'datetime', 'varchar(15)'],
         'remarks':    ['交易订单ID', '持仓ID', '交易方向(买Buy/卖Sell)', '委托类型(市价单/限价单)', '委托数量',
                        '委托报价',
                        '委托时间', '状态(提交submitted/部分成交partial-filled/全部成交filled/取消canceled)'],
         'prime_keys': [0]
         },

    'sys_op_trade_results':  # 交易结果表
        {'columns':    ['result_id', 'order_id', 'filled_qty', 'price', 'transaction_fee', 'execution_time',
                        'canceled_qty', 'delivery_amount', 'delivery_status'],
         'dtypes':     ['int', 'int', 'double', 'double', 'double', 'datetime',
                        'double', 'double', 'varchar(2)'],
         'remarks':    ['交易结果ID', '交易订单ID', '成交数量', '成交价格', '交易费用', '成交时间',
                        '取消交易数量', '交割数量(现金或证券)', '交割状态{ND, DL}'],
         'prime_keys': [0],
         },

    'trade_calendar':
        {'columns':    ['exchange', 'cal_date', 'is_open', 'pretrade_date'],
         'dtypes':     ['varchar(9)', 'date', 'tinyint', 'date'],
         'remarks':    ['交易所', '日期', '是否交易', '上一交易日'],
         'prime_keys': [0, 1]
         },

    'stock_basic':
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

    'name_changes':
        {'columns':    ['ts_code', 'start_date', 'name', 'end_date', 'ann_date', 'change_reason'],
         'dtypes':     ['varchar(9)', 'date', 'varchar(8)', 'date', 'date', 'varchar(10)'],
         'remarks':    ['证券代码', '开始日期', '证券名称', '结束日期', '公告日期', '变更原因'],
         'prime_keys': [0, 1]
         },

    'stock_company':
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

    'stk_managers':
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

    'new_share':
        {'columns':    ['ts_code', 'sub_code', 'name', 'ipo_date', 'issue_date',
                        'amount', 'market_amount', 'price', 'pe', 'limit_amount',
                        'funds', 'ballot'],
         'dtypes':     ['varchar(20)', 'varchar(20)', 'varchar(50)', 'date', 'date',
                        'float', 'float', 'float', 'float', 'float',
                        'float', 'float'],
         'remarks':    ['TS股票代码', '申购代码', '名称', '上网发行日期', '上市日期',
                        '发行总量（万股）', '上网发行总量（万股）', '发行价格', '市盈率', '个人申购上限（万股）',
                        '募集资金（亿元）', '中签率'],
         'prime_keys': [0, 1]
         },

    'index_basic':
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

    'fund_basic':
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

    'future_basic':
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

    'opt_basic':
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

    'bars':
        {'columns':    ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change',
                        'pct_chg', 'vol', 'amount'],
         'dtypes':     ['varchar(20)', 'date', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float', 'double', 'double'],
         'remarks':    ['证券代码', '交易日期', '开盘价', '最高价', '最低价', '收盘价', '昨收价', '涨跌额',
                        '涨跌幅', '成交量(手)', '成交额(千元)'],
         'prime_keys': [0, 1]
         },

    'min_bars':
        {'columns':    ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount'],
         'dtypes':     ['varchar(20)', 'datetime', 'float', 'float', 'float', 'float', 'double',
                        'double'],
         'remarks':    ['证券代码', '交易日期时间', '开盘价', '最高价', '最低价', '收盘价', '成交量(股)',
                        '成交额(元)'],
         'prime_keys': [0, 1]
         },

    'adj_factors':
        {'columns':    ['ts_code', 'trade_date', 'adj_factor'],
         'dtypes':     ['varchar(9)', 'date', 'double'],
         'remarks':    ['证券代码', '交易日期', '复权因子'],
         'prime_keys': [0, 1]
         },

    'fund_nav':
        {'columns':    ['ts_code', 'nav_date', 'ann_date', 'unit_nav', 'accum_nav', 'accum_div',
                        'net_asset', 'total_netasset', 'adj_nav', 'update_flag'],
         'dtypes':     ['varchar(24)', 'date', 'date', 'float', 'float', 'float', 'double', 'double',
                        'float', 'varchar(2)'],
         'remarks':    ['TS代码', '净值日期', '公告日期', '单位净值', '累计净值', '累计分红', '资产净值',
                        '合计资产净值', '复权单位净值', '更新标记'],
         'prime_keys': [0, 1]
         },

    'fund_share':
        {'columns':    ['ts_code', 'trade_date', 'fd_share'],
         'dtypes':     ['varchar(20)', 'date', 'float'],
         'remarks':    ['证券代码', '变动日期，格式YYYYMMDD', '基金份额(万)'],
         'prime_keys': [0, 1]
         },

    'fund_manager':
        {'columns':    ['ts_code', 'ann_date', 'name', 'gender', 'birth_year', 'edu', 'nationality',
                        'begin_date', 'end_date', 'resume'],
         'dtypes':     ['varchar(20)', 'date', 'varchar(20)', 'varchar(2)', 'varchar(12)',
                        'varchar(30)', 'varchar(4)', 'date', 'date', 'text'],
         'remarks':    ['证券代码', '公告日期', '基金经理姓名', '性别', '出生年份', '学历', '国籍', '任职日期',
                        '离任日期', '简历'],
         'prime_keys': [0, 1]
         },

    'future_daily':
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

    'future_mins':
        {'columns':    ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount', 'oi'],
         'dtypes':     ['varchar(20)', 'datetime', 'float', 'float', 'float', 'float', 'double',
                        'double', 'double'],
         'remarks':    ['证券代码', '交易日期时间', '开盘价', '最高价', '最低价', '收盘价', '成交量(手)',
                        '成交金额(元)', '持仓量(手)'],
         'prime_keys': [0, 1]
         },

    'options_daily':
        {'columns':    ['ts_code', 'trade_date', 'exchange', 'pre_settle', 'pre_close', 'open', 'high',
                        'low', 'close', 'settle', 'vol', 'amount', 'oi'],
         'dtypes':     ['varchar(20)', 'date', 'varchar(8)', 'float', 'float', 'float', 'float',
                        'float', 'float', 'float', 'double', 'double', 'double'],
         'remarks':    ['证券代码', '交易日期', '交易市场', '昨结算价', '昨收盘价', '开盘价', '最高价', '最低价',
                        '收盘价', '结算价', '成交量(手)', '成交金额(万元)', '持仓量(手)'],
         'prime_keys': [0, 1]
         },

    'stock_indicator':
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

    'stock_indicator2':
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

    'index_indicator':
        {'columns':    ['ts_code', 'trade_date', 'total_mv', 'float_mv', 'total_share', 'float_share',
                        'free_share', 'turnover_rate', 'turnover_rate_f', 'pe', 'pe_ttm', 'pb'],
         'dtypes':     ['varchar(9)', 'date', 'double', 'double', 'double', 'double', 'double', 'float',
                        'float', 'float', 'float', 'float'],
         'remarks':    ['证券代码', '交易日期', '当日总市值(元)', '当日流通市值(元)', '当日总股本(股)',
                        '当日流通股本(股)', '当日自由流通股本(股)', '换手率', '换手率(基于自由流通股本)',
                        '市盈率', '市盈率TTM', '市净率'],
         'prime_keys': [0, 1]
         },

    'index_weight':
        {'columns':    ['index_code', 'trade_date', 'con_code', 'weight'],
         'dtypes':     ['varchar(24)', 'date', 'varchar(20)', 'float'],
         'remarks':    ['指数代码', '交易日期', '成分代码', '权重(%)'],
         'prime_keys': [0, 1, 2]
         },

    'income':
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

    'balance':
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

    'cashflow':
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

    'financial':
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

    'forecast':
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

    'express':
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

    'shibor':
        {'columns':    ['date', 'on', '1w', '2w', '1m', '3m', '6m', '9m', '1y'],
         'dtypes':     ['date', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float'],
         'remarks':    ['日期', '隔夜', '1周', '2周', '1个月', '3个月', '6个月', '9个月', '1年'],
         'prime_keys': [0]
         },

    'libor':
        {'columns':    ['date', 'curr_type', 'on', '1w', '1m', '2m', '3m', '6m', '12m'],
         'dtypes':     ['date', 'varchar(9)', 'float', 'float', 'float', 'float', 'float', 'float',
                        'float'],
         'remarks':    ['日期', '货币', '隔夜', '1周', '1个月', '2个月', '3个月', '6个月', '12个月'],
         'prime_keys': [0, 1]
         },

    'hibor':
        {'columns':    ['date', 'on', '1w', '2w', '1m', '2m', '3m', '6m', '12m'],
         'dtypes':     ['date', 'float', 'float', 'float', 'float', 'float', 'float', 'float', 'float'],
         'remarks':    ['日期', '隔夜', '1周', '2周', '1个月', '2个月', '3个月', '6个月', '12个月'],
         'prime_keys': [0]
         }

}


class DataConflictWarning(Warning):
    """ Warning Type: Data conflict detected"""
    pass


class MissingDataWarning(Warning):
    """ Warning Type: Local Data Missing"""
    pass


# noinspection SqlDialectInspection #,PyTypeChecker,PyPackageRequirements
class DataSource:
    """ DataSource 对象管理存储在本地的历史数据文件或数据库.

    通过DataSource对象，History模块可以容易地从本地存储的数据中读取并组装所需要的历史数据
    并确保历史数据符合HistoryPanel的要求。
    所有的历史数据必须首先从网络数据提供商处下载下来并存储在本地文件或数据库中，DataSource
    对象会检查数据的格式，确保格式正确并删除重复的数据。
    下载下来的历史数据可以存储成不同的格式，但是不管任何存储格式，所有数据表的结构都是一样
    的，而且都是与Pandas的DataFrame兼容的数据表格式。目前兼容的文件存储格式包括csv, hdf,
    fth(feather)，兼容的数据库包括mysql和MariaDB。
    如果HistoryPanel所要求的数据未存放在本地，DataSource对象不会主动下载缺失的数据，仅会
    返回空DataFrame。
    DataSource对象可以按要求定期刷新或从Provider拉取数据，也可以手动操作

    Attributes
    ----------

    Methods
    -------
    overview(print_out=True)
        以表格形式列出所有数据表的当前数据状态
    read_table_data(self, table, shares=None, start=None, end=None)
        从本地数据表中读取数据并返回DataFrame，不修改数据格式
    export_table_data(self, table, shares=None, start=None, end=None)
        NotImplemented 将数据表中的数据读取出来之后导出到一个文件中，便于用户使用过程中小
        规模转移数据
    get_history_data(self, shares, htypes, start, end, freq, asset_type='any', adj='none')
        根据给出的参数从不同的本地数据表中获取数据，并打包成一系列的DataFrame，以便组装成
        HistoryPanel对象。
    get_index_weights(self, index, start=None, end=None, shares=None)
        从本地数据仓库中获取一个指数的成分权重
    refill_local_source(self, tables=None, dtypes=None, freqs=None, asset_types=None,...)
        批量补充本地数据，手动或自动运行补充本地数据库

    """

    def __init__(self,
                 source_type: str = 'file',
                 file_type: str = 'csv',
                 file_loc: str = 'data/',
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = None,
                 password: str = None,
                 db_name: str = 'qt_db'):
        """ 创建一个DataSource 对象

        创建对象时确定本地数据存储方式，确定文件存储位置、文件类型，或者建立数据库的连接

        Parameters
        ----------
        source_type: str, Default: file
            数据源类型:
            - db/database: 数据存储在mysql数据库中
            - file: 数据存储在本地文件中
        file_type: str, {'csv', 'hdf', 'hdf5', 'feather', 'fth'}, Default: csv
            如果数据源为file时，数据文件类型：
            - csv: 简单的纯文本文件格式，可以用Excel打开，但是占用空间大，读取速度慢
            - hdf/hdf5: 基于pytables的数据表文件，速度较快，需要安装pytables
            - feather/fth: 轻量级数据文件，速度较快，占用空间小，需要安装pyarrow
        file_loc: str, Default: data/
            用于存储本地数据文件的路径
        host: str, default: localhost
            如果数据源为database时，数据库的host
        port: int, Default: 3306
            如果数据源为database时，数据库的port，默认3306
        user: str, Default: None
            如果数据源为database时，数据库的user name
        password: str, Default: None
            如果数据源为database时，数据库的passwrod
        db_name: str, Default: 'qt_db'
            如果数据源为database时，数据库的名称，默认值qt_db

        Raises
        ------
        ImportError
            部分文件格式以及数据类型需要optional dependency，如果缺乏这些package时，会提示安装
        SystemError
            数据类型为file时，在本地创建数据文件夹失败时会抛出该异常

        Returns
        -------
        None
        """
        if not isinstance(source_type, str):
            raise TypeError(f'source type should be a string, got {type(source_type)} instead.')
        if source_type.lower() not in ['file', 'database', 'db']:
            raise ValueError(f'invalid source_type')
        self._table_list = set()

        if source_type.lower() in ['db', 'database']:
            # optional packages to be imported
            try:
                import pymysql
            except ImportError:
                raise ImportError(f'Missing dependency \'pymysql\' for datasource type '
                                  f'\'database\'. Use pip or conda to install pymysql.')
            # set up connection to the data base
            if not isinstance(port, int):
                raise TypeError(f'port should be of type int')
            if user is None:
                raise ValueError(f'Missing user name for database connection')
            if password is None:
                raise ValueError(f'Missing password for database connection')
            # try to create pymysql connections
            try:
                self.source_type = 'db'
                con = pymysql.connect(host=host,
                                      port=port,
                                      user=user,
                                      password=password)
                # 检查db是否存在，当db不存在时创建新的db
                cursor = con.cursor()
                sql = f"CREATE DATABASE IF NOT EXISTS {db_name}"
                cursor.execute(sql)
                con.commit()
                sql = f"USE {db_name}"
                cursor.execute(sql)
                con.commit()
                con.close()
                # create mysql database connection info
                self.connection_type = f'db:mysql://{host}@{port}/{db_name}'
                self.host = host
                self.port = port
                self.db_name = db_name
                self.file_type = None
                self.file_path = None
                self.__user__ = user
                self.__password__ = password

            except Exception as e:
                warnings.warn(f'{str(e)}, Can not set data source type to "db",'
                              f' will fall back to default type', RuntimeWarning)
                source_type = 'file'
                file_type = 'csv'

        if source_type.lower() == 'file':
            # set up file type and file location
            if not isinstance(file_type, str):
                raise TypeError(f'file type should be a string, got {type(file_type)} instead!')
            file_type = file_type.lower()
            if file_type not in AVAILABLE_DATA_FILE_TYPES:
                raise KeyError(f'file type not recognized, supported file types are csv / hdf / feather')
            if file_type in ['hdf']:
                try:
                    import tables
                except ImportError:
                    raise ImportError(f'Missing optional dependency \'pytables\' for datasource file type '
                                      f'\'hdf5\'. Use pip or conda to install pytables')
                file_type = 'hdf'
            if file_type in ['feather', 'fth']:
                try:
                    import pyarrow
                except ImportError:
                    raise ImportError(f'Missing optional dependency \'pyarrow\' for datasource file type '
                                      f'\'feather\'. Use pip or conda to install pyarrow')
                file_type = 'fth'
            from qteasy import QT_ROOT_PATH
            self.file_path = path.join(QT_ROOT_PATH, file_loc)
            try:
                os.makedirs(self.file_path, exist_ok=True)  # 确保数据dir不存在时创建一个
            except Exception:
                raise SystemError(f'Failed creating data directory \'{file_loc}\' in qt root path, '
                                  f'please check your input.')
            self.source_type = 'file'
            self.file_type = file_type
            self.file_loc = file_loc
            self.connection_type = f'file://{file_type}@qt_root/{file_loc}'
            self.host = None
            self.port = None
            self.db_name = None
            self.__user__ = None
            self.__password__ = None

    @property
    def tables(self):
        """ 所有已经建立的tables的清单"""
        return list(self._table_list)

    def __repr__(self):
        if self.source_type == 'db':
            return f'DataSource(\'db\', \'{self.host}\', {self.port})'
        elif self.source_type == 'file':
            return f'DataSource(\'file\', \'{self.file_type}\', \'{self.file_loc}\')'
        else:
            return

    def __str__(self):
        return self.connection_type

    def info(self):
        """ 格式化打印database对象的各种主要信息

        Returns
        -------
        """
        raise NotImplementedError

    def overview(self, tables=None, print_out=True, include_sys_tables=False):
        """ 以表格形式列出所有数据表的当前数据状态

        Parameters
        ----------
        tables: str or list of str, Default None
            指定要列出的数据表，如果为None则列出所有数据表
        print_out: bool, Default True
            是否打印数据表总揽
        include_sys_tables: bool, Default False
            是否包含系统表

        Returns
        -------
        pd.DataFrame, 包含所有数据表的数据状态
        """

        all_tables = get_table_master()
        if not include_sys_tables:
            all_tables = all_tables[all_tables['table_usage'] != 'sys']
        all_table_names = all_tables.index
        if tables is not None:
            if isinstance(tables, str):
                tables = str_to_list(tables)
            if not isinstance(tables, list):
                raise TypeError(f'tables should be a list of str, got {type(tables)} instead!')
            all_table_names = [table_name for table_name in all_table_names if table_name in tables]

        all_info = []
        print('Analyzing local data source tables... depending on size of tables, it may take a few minutes')
        total_table_count = len(all_table_names)
        from .utilfuncs import progress_bar
        completed_reading_count = 0
        for table_name in all_table_names:
            progress_bar(completed_reading_count, total_table_count, comments=f'Analyzing table: <{table_name}>')
            all_info.append(self.get_table_info(table_name, verbose=False, print_info=False, human=True))
            completed_reading_count += 1
        progress_bar(completed_reading_count, total_table_count, comments=f'Analyzing completed!')
        all_info = pd.DataFrame(all_info, columns=['table', 'has_data', 'size', 'records',
                                                   'pk1', 'records1', 'min1', 'max1',
                                                   'pk2', 'records2', 'min2', 'max2'])
        all_info.index = all_info['table']
        all_info.drop(columns=['table'], inplace=True)
        if print_out:
            info_to_print = all_info.loc[all_info.has_data == True][['has_data', 'size', 'records', 'min2', 'max2']]
            print(f'\n{self}\nFollowing tables contain local data, to view complete list, print returned DataFrame')
            print(info_to_print.to_string(columns=['has_data',
                                                   'size',
                                                   'records',
                                                   'min2',
                                                   'max2'],
                                          header=['Has_data',
                                                  'Size_on_disk',
                                                  'Record_count',
                                                  'Record_start',
                                                  'Record_end'],
                                          justify='center'
                                          )
                  )
        return all_info

    # 文件操作层函数，只操作文件，不修改数据
    def get_file_path_name(self, file_name):
        """获取完整文件路径名"""
        if self.source_type == 'db':
            raise RuntimeError('can not check file system while source type is "db"')
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        file_name = file_name + '.' + self.file_type
        file_path_name = path.join(self.file_path, file_name)
        return file_path_name

    def file_exists(self, file_name):
        """ 检查文件是否已存在

        Parameters
        ----------
        file_name: 需要检查的文件名(不含扩展名)
        Returns
        -------
        Boolean: 文件存在时返回真，否则返回假
        """
        file_path_name = self.get_file_path_name(file_name)
        return path.exists(file_path_name)

    def write_file(self, df, file_name):
        """ 将df写入本地文件

        Parameters
        ----------
        df: 待写入文件的DataFrame
        file_name: 本地文件名(不含扩展名)
        Returns
        -------
        str: file_name 如果数据保存成功，返回完整文件路径名称
        """
        file_path_name = self.get_file_path_name(file_name)
        if self.file_type == 'csv':
            df.to_csv(file_path_name)
        elif self.file_type == 'fth':
            df.reset_index().to_feather(file_path_name)
        elif self.file_type == 'hdf':
            df.to_hdf(file_path_name, key='df')
        else:  # for some unexpected cases
            raise TypeError(f'Invalid file type: {self.file_type}')
        return len(df)

    def read_file(self, file_name, primary_key, pk_dtypes, share_like_pk=None,
                  shares=None, date_like_pk=None, start=None, end=None, chunk_size=50000):
        """ 从文件中读取DataFrame，当文件类型为csv时，支持分块读取且完成数据筛选

        Parameters
        ----------
        file_name: str
            文件名
        primary_key: list of str
            用于生成primary_key index 的主键
        pk_dtypes: list of str
            primary_key的数据类型
        share_like_pk: str
            用于按值筛选数据的主键
        shares: list of str
            用于筛选数据的主键的值
        date_like_pk: str
            用于按日期筛选数据的主键
        start: datetime-like
            用于按日期筛选数据的起始日期
        end: datetime-like
            用于按日期筛选数据的结束日期
        chunk_size: int
            分块读取csv大文件时的分块大小

        Returns
        -------
        DataFrame：从文件中读取的DataFrame，如果数据有主键，将主键设置为df的index
        """

        # TODO: 这里对所有读取的文件都进行筛选，需要考虑是否在read_table_data还需要筛选？
        #  也就是说，在read_table_data级别筛选数据还是在read_file/read_database级别
        #  筛选数据？
        file_path_name = self.get_file_path_name(file_name)
        if not self.file_exists(file_name):
            # 如果文件不存在，则返回空的DataFrame
            return pd.DataFrame()
        if date_like_pk is not None:
            start = pd.to_datetime(start).strftime('%Y-%m-%d')
            end = pd.to_datetime(end).strftime('%Y-%m-%d')

        if self.file_type == 'csv':
            # 这里针对csv文件进行了优化，通过分块读取文件，避免当文件过大时导致读取异常
            df_reader = pd.read_csv(file_path_name, chunksize=chunk_size)  # TODO: add try to escape file reading errors
            df_picker = (chunk for chunk in df_reader)
            if (share_like_pk is not None) and (date_like_pk is not None):
                df_picker = (chunk.loc[(chunk[share_like_pk].isin(shares)) &
                                       (chunk[date_like_pk] >= start) &
                                       (chunk[date_like_pk] <= end)] for chunk in df_reader)
            elif (share_like_pk is None) and (date_like_pk is not None):
                df_picker = (chunk.loc[(chunk[date_like_pk] >= start) &
                                       (chunk[date_like_pk] <= end)] for chunk in df_reader)
            elif (share_like_pk is not None) and (date_like_pk is None):
                df_picker = (chunk.loc[(chunk[share_like_pk].isin(shares))] for chunk in df_reader)
            df = pd.concat(df_picker)
            set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtypes)

            return df

        if self.file_type == 'hdf':
            # TODO: hdf5/feather的大文件读取尚未优化
            df = pd.read_hdf(file_path_name, 'df')  # TODO: add try to escape file reading errors
            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtypes)
        elif self.file_type == 'fth':
            # TODO: feather大文件读取尚未优化
            df = pd.read_feather(file_path_name)  # TODO: add try to escape file reading errors
        else:  # for some unexpected cases
            raise TypeError(f'Invalid file type: {self.file_type}')

        try:
            # 如果self.file_type 为 hdf/fth，那么需要筛选数据
            if (share_like_pk is not None) and (date_like_pk is not None):
                df = df.loc[(df[share_like_pk].isin(shares)) &
                            (df[date_like_pk] >= start) &
                            (df[date_like_pk] <= end)]
            elif (share_like_pk is None) and (date_like_pk is not None):
                df = df.loc[(df[date_like_pk] >= start) &
                            (df[date_like_pk] <= end)]
            elif (share_like_pk is not None) and (date_like_pk is None):
                df = df.loc[(df[share_like_pk].isin(shares))]
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f'{e}')

        set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtypes)
        return df

    def get_file_table_coverage(self, table, column, primary_key, pk_dtypes, min_max_only):
        """ 检查数据表文件关键列的内容，去重后返回该列的内容清单

        Parameters
        ----------
        table: str
            数据表名
        column: str
            关键列名
        primary_key: list of str
            数据表的主键名称列表
        pk_dtypes: list of str
            数据表的主键数据类型列表
        min_max_only: bool
            为True时仅输出最小、最大以及总数量，False输出完整列表

        Returns
        -------
        list of str
            数据表中存储的数据关键列的清单
        """
        if not self.file_exists(table):
            return list()
        df = self.read_file(table, primary_key, pk_dtypes)
        if df.empty:
            return list()
        if column in list(df.index.names):
            extracted_val = df.index.get_level_values(column).unique()
        else:
            extracted_val = df[column].unique()
        if isinstance(extracted_val[0], pd.Timestamp):
            extracted_val = extracted_val.strftime('%Y%m%d')

        res = list()
        if min_max_only:
            res.append(extracted_val.min())
            res.append(extracted_val.max())
            res.append(len(extracted_val))
        else:
            res.extend(extracted_val)

        return list(res)

    def drop_file(self, file_name):
        """ 删除本地文件

        Parameters
        ----------
        file_name: str
            将被删除的文件名

        Returns
        -------
        None
        """
        import os
        if self.file_exists(file_name):
            file_path_name = os.path.join(self.file_path, file_name + '.' + self.file_type)
            os.remove(file_path_name)

    def get_file_size(self, file_name):
        """ 获取文件大小，输出

        Parameters
        ----------
        file_name:  str 文件名
        Returns
        -------
            str representing file size
        """
        import os
        file_path_name = self.get_file_path_name(file_name)
        try:
            file_size = os.path.getsize(file_path_name)
            return file_size
        except FileNotFoundError:
            return -1
        except Exception as e:
            raise RuntimeError(f'{e}, unknown error encountered.')

    def get_file_rows(self, file_name):
        """获取csv、hdf、fether文件中数据的行数"""
        file_path_name = self.get_file_path_name(file_name)
        if self.file_type == 'csv':
            with open(file_path_name, 'r') as fp:
                line_count = None
                for line_count, line in enumerate(fp):
                    pass
                return line_count
        elif self.file_type == 'hdf':
            df = pd.read_hdf(file_path_name, 'df')
            return len(df)
        elif self.file_type == 'fth':
            df = pd.read_feather(file_path_name)
            return len(df)

    # 数据库操作层函数，只操作具体的数据表，不操作数据
    def read_database(self, db_table, share_like_pk=None, shares=None, date_like_pk=None, start=None, end=None):
        """ 从一张数据库表中读取数据，读取时根据share(ts_code)和dates筛选
            具体筛选的字段通过share_like_pk和date_like_pk两个字段给出

        Parameters
        ----------
        db_table: str
            需要读取数据的数据表
        share_like_pk: str
            用于筛选证券代码的字段名，不同的表中字段名可能不同，用这个字段筛选不同的证券、如股票、基金、指数等
            当这个参数给出时，必须给出shares参数
        shares: str,
            如果给出shares，则按照"WHERE share_like_pk IN shares"筛选
        date_like_pk: str
            用于筛选日期的主键字段名，不同的表中字段名可能不同，用这个字段筛选需要的记录的时间段
            当这个参数给出时，必须给出start和end参数
        start: datetime like,
            如果给出start同时又给出end，按照"WHERE date_like_pk BETWEEN start AND end"的条件筛选
        end: datetime like,
            当没有给出start时，单独给出end无效

        Returns
        -------
            DataFrame，从数据库中读取的DataFrame
        """
        if not self.db_table_exists(db_table):
            return pd.DataFrame()
        ts_code_filter = ''
        has_ts_code_filter = False
        date_filter = ''
        has_date_filter = False
        if shares is not None:
            has_ts_code_filter = True
            share_count = len(shares)
            if share_count > 1:
                ts_code_filter = f'{share_like_pk} in {tuple(shares)}'
            else:
                ts_code_filter = f'{share_like_pk} = "{shares[0]}"'
        if (start is not None) and (end is not None):
            # assert start and end are date-like
            has_date_filter = True
            date_filter = f'{date_like_pk} BETWEEN "{start}" AND "{end}"'

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        sql = f'SELECT * ' \
              f'FROM {db_table}\n'
        if not (has_ts_code_filter or has_date_filter):
            # No WHERE clause
            pass
        elif has_ts_code_filter and has_date_filter:
            # both WHERE clause for ts_code and date
            sql += f'WHERE {ts_code_filter}' \
                   f' AND {date_filter}\n'
        elif has_ts_code_filter and not has_date_filter:
            # only one WHERE clause for ts_code
            sql += f'WHERE {ts_code_filter}\n'
        elif not has_ts_code_filter and has_date_filter:
            # only one WHERE clause for date
            sql += f'WHERE {date_filter}'
        sql += ''
        try:
            df = pd.read_sql_query(sql, con=con)
            return df
        except Exception as e:
            raise RuntimeError(f'{e}, error in reading data from database with sql:\n"{sql}"')
        finally:
            con.close()

    def write_database(self, df, db_table):
        """ 将DataFrame中的数据添加到数据库表末尾，如果表不存在，则
        新建一张数据库表，并设置primary_key（如果给出）

        假定df的列与db_table的schema相同且顺序也相同

        Parameter
        ---------
        df: pd.DataFrame
            需要添加的DataFrame
        db_table: str
            需要添加数据的数据库表

        Returns
        -------
        int: 返回写入的记录数

        Note
        ----
        调用update_database()执行任务，设置参数ignore_duplicate=True
        """

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        # if table does not exist, create a new table without primary key info
        if not self.db_table_exists(db_table):
            dtype_mapping = {'object': 'varchar(255)',
                             'datetime64[ns]': 'datetime',
                             'int64': 'int',
                             'float32': 'float',
                             'float64': 'double',
                             }
            columns = df.columns
            dtypes = df.dtypes.tolist()
            dtypes = [dtype_mapping.get(str(dtype.name), 'varchar(255)') for dtype in dtypes]

            sql = f"CREATE TABLE IF NOT EXISTS `{db_table}` (\n"
            fields = []
            for col, dtype in zip(columns, dtypes):
                fields.append(f"`{col}` {dtype}\n")
            sql += f"{', '.join(fields)});"
            try:
                cursor = con.cursor()
                cursor.execute(sql)
                con.commit()
            except Exception as e:
                con.rollback()
                raise RuntimeError(f'db table {db_table} does not exist and can not be created:\n'
                                   f'Exception:\n{e}\n'
                                   f'SQL:\n{sql}')

        tbl_columns = tuple(self.get_db_table_schema(db_table).keys())
        if (len(df.columns) != len(tbl_columns)) or (any(i_d != i_t for i_d, i_t in zip(df.columns, tbl_columns))):
            raise KeyError(f'df columns {df.columns.to_list()} does not fit table schema {list(tbl_columns)}')
        df = df.where(pd.notna(df), None)
        df_tuple = tuple(df.itertuples(index=False, name=None))
        sql = f"INSERT IGNORE INTO "
        sql += f"`{db_table}` ("
        for col in tbl_columns[:-1]:
            sql += f"`{col}`, "
        sql += f"`{tbl_columns[-1]}`)\nVALUES\n("
        for val in tbl_columns[:-1]:
            sql += "%s, "
        sql += "%s)\n"
        try:
            cursor = con.cursor()
            rows_affected = cursor.executemany(sql, df_tuple)
            con.commit()
            return rows_affected
        except Exception as e:
            con.rollback()
            raise RuntimeError(f'Error during inserting data to table {db_table} with following sql:\n'
                               f'Exception:\n{e}\n'
                               f'SQL:\n{sql} \nwith parameters (first 10 shown):\n{df_tuple[:10]}')
        finally:
            con.close()

    def update_database(self, df, db_table, primary_key):
        """ 用DataFrame中的数据更新数据表中的数据记录

        假定df的列与db_table的列相同且顺序也相同
        在插入数据之前，必须确保表的primary_key已经正确设定
        如果写入记录的键值存在冲突时，更新数据库中的记录

        Parameters
        ----------
        df: pd.DataFrame
            用于更新数据表的数据DataFrame
        db_table: str
            需要更新的数据表
        primary_key: tuple
            数据表的primary_key，必须定义在数据表中，如果数据库表没有primary_key，将append所有数据

        Returns
        -------
        int: rows affected
        """
        tbl_columns = tuple(self.get_db_table_schema(db_table).keys())
        update_cols = [item for item in tbl_columns if item not in primary_key]
        if (len(df.columns) != len(tbl_columns)) or (any(i_d != i_t for i_d, i_t in zip(df.columns, tbl_columns))):
            raise KeyError(f'df columns {df.columns.to_list()} does not fit table schema {list(tbl_columns)}')
        df = df.where(pd.notna(df), None)
        df_tuple = tuple(df.itertuples(index=False, name=None))
        sql = f"INSERT INTO "
        sql += f"`{db_table}` ("
        for col in tbl_columns[:-1]:
            sql += f"`{col}`, "
        sql += f"`{tbl_columns[-1]}`)\nVALUES\n("
        for val in tbl_columns[:-1]:
            sql += "%s, "
        sql += "%s)\n" \
               "ON DUPLICATE KEY UPDATE\n"
        for col in update_cols[:-1]:
            sql += f"`{col}`=VALUES(`{col}`),\n"
        sql += f"`{update_cols[-1]}`=VALUES(`{update_cols[-1]}`)"
        try:
            import pymysql
            con = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.__user__,
                    password=self.__password__,
                    db=self.db_name,
            )
            cursor = con.cursor()
            rows_affected = cursor.executemany(sql, df_tuple)
            con.commit()
            return rows_affected
        except Exception as e:
            con.rollback()
            raise RuntimeError(f'Error during inserting data to table {db_table} with following sql:\n'
                               f'Exception:\n{e}\n'
                               f'SQL:\n{sql} \nwith parameters (first 10 shown):\n{df_tuple[:10]}')
        finally:
            con.close()

    def get_db_table_coverage(self, db_table, column):
        """ 检查数据库表关键列的内容，去重后返回该列的内容清单

        Parameters
        ----------
        db_table: str
            数据表名
        column: str
            数据表的字段名

        Returns
        -------
        """
        import datetime
        if not self.db_table_exists(db_table):
            return list()
        sql = f'SELECT DISTINCT `{column}`' \
              f'FROM `{db_table}`' \
              f'ORDER BY `{column}`'
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        try:
            cursor.execute(sql)
            con.commit()
            res = [item[0] for item in cursor.fetchall()]
            if isinstance(res[0], datetime.datetime):
                res = list(pd.to_datetime(res).strftime('%Y%m%d'))
            return res
        except Exception as e:
            con.rollback()
            raise RuntimeError(f'Exception:\n{e}\n'
                               f'Error during querying data from db_table {db_table} with following sql:\n'
                               f'SQL:\n{sql} \n')
        finally:
            con.close()

    def get_db_table_minmax(self, db_table, column, with_count=False):
        """ 检查数据库表关键列的内容，获取最小值和最大值和总数量

        Parameters
        ----------
        db_table: str
            数据表名
        column: str
            数据表的字段名
        with_count: bool, default False
            是否返回关键列值的数量，可能非常耗时

        Returns
        -------
        list: [min, max, count]
        """
        import datetime
        if not self.db_table_exists(db_table):
            return list()
        if with_count:
            add_sql = f', COUNT(DISTINCT(`{column}`))'
        else:
            add_sql = ''
        sql = f'SELECT MIN(`{column}`), MAX(`{column}`){add_sql} '
        sql += f'FROM `{db_table}`'
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        try:
            cursor.execute(sql)
            con.commit()

            res = list(cursor.fetchall()[0])
            if isinstance(res[0], datetime.datetime):
                res = list(pd.to_datetime(res).strftime('%Y%m%d'))
            return res
        except Exception as e:
            con.rollback()
            raise RuntimeError(f'Exception:\n{e}\n'
                               f'Error during querying data from db_table {db_table} with following sql:\n'
                               f'SQL:\n{sql} \n')
        finally:
            con.close()

    def db_table_exists(self, db_table):
        """ 检查数据库中是否存在db_table这张表

        Parameters
        ----------
        db_table: str
            数据表名

        Returns
        -------
        bool
        """
        if self.source_type == 'file':
            raise RuntimeError('can not connect to database while source type is "file"')
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = f"SHOW TABLES LIKE '{db_table}'"
        try:
            cursor.execute(sql)
            con.commit()
            res = cursor.fetchall()
            return len(res) > 0
        except Exception as e:
            raise RuntimeError(f'Exception:\n{e}\n'
                               f'Error during querying data from db_table {db_table} with following sql:\n'
                               f'SQL:\n{sql} \n')
        finally:
            con.close()

    def new_db_table(self, db_table, columns, dtypes, primary_key, auto_increment_id=False):
        """ 在数据库中新建一个数据表(如果该表不存在)，并且确保数据表的schema与设置相同,
            并创建正确的index

        Parameters
        ----------
        db_table: str
            数据表名
        columns: list of str
            数据表的所有字段名
        dtypes: list of str {'varchar', 'float', 'int', 'datetime', 'text'}
            数据表所有字段的数据类型
        primary_key: list of str
            数据表的所有primary_key
        auto_increment_id: bool, Default: False
            是否使用自增主键

        Returns
        -------
        None
        """
        if self.source_type != 'db':
            raise TypeError(f'Datasource is not connected to a database')

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = f"CREATE TABLE IF NOT EXISTS `{db_table}` (\n"
        for col_name, dtype in zip(columns, dtypes):
            sql += f"`{col_name}` {dtype}"
            if col_name in primary_key:
                sql += " NOT NULL"
                sql += " AUTO_INCREMENT,\n" if auto_increment_id else ",\n"
            else:
                sql += " DEFAULT NULL,\n"
        # 如果有primary key则添加primary key
        if primary_key is not None:
            sql += f"PRIMARY KEY (`{'`, `'.join(primary_key)}`)"
            # 如果primary key多于一个，则创建KEY INDEX
            if len(primary_key) > 1:
                sql += ",\nKEY (`" + '`),\nKEY (`'.join(primary_key[1:]) + "`)"
        sql += '\n);'
        try:
            cursor.execute(sql)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

    def get_db_table_schema(self, db_table):
        """ 获取数据库表的列名称和数据类型

        Parameters
        ----------
        db_table: str
            需要获取列名的数据库表

        Returns
        -------
            dict: 一个包含列名和数据类型的Dict: {column1: dtype1, column2: dtype2, ...}
        """

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()

        sql = f"SELECT COLUMN_NAME, DATA_TYPE " \
              f"FROM INFORMATION_SCHEMA.COLUMNS " \
              f"WHERE TABLE_SCHEMA = Database() " \
              f"AND table_name = '{db_table}'" \
              f"ORDER BY ordinal_position;"
        try:
            cursor.execute(sql)
            con.commit()
            results = cursor.fetchall()
            # 为了方便，将cur_columns和new_columns分别包装成一个字典
            columns = {}
            for col, typ in results:
                columns[col] = typ
            return columns
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

    def drop_db_table(self, db_table):
        """ 修改优化db_table的schema，建立index，从而提升数据库的查询速度提升效能

        Parameters
        ----------
        db_table: str
            数据表名

        Returns
        -------
        None
        """
        if self.source_type != 'db':
            raise TypeError(f'Datasource is not connected to a database')
        if not isinstance(db_table, str):
            raise TypeError(f'db_table name should be a string, got {type(db_table)} instead')

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = f"DROP TABLE IF EXISTS {db_table};"
        try:
            cursor.execute(sql)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

    def get_db_table_size(self, db_table):
        """ 获取数据库表的占用磁盘空间

        Parameters
        ----------
        db_table: str
            数据库表名称

        Returns
        -------
        rows: int
        """
        if not self.db_table_exists(db_table):
            return -1

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = "SELECT table_rows, data_length + index_length " \
              "FROM INFORMATION_SCHEMA.tables " \
              "WHERE table_schema = %s " \
              "AND table_name = %s;"
        try:
            cursor.execute(sql, (self.db_name, db_table))
            con.commit()
            rows, size = cursor.fetchall()[0]
            return rows, size
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

    # ==============
    # (逻辑)数据表操作层函数，只在逻辑表层面读取或写入数据，调用文件操作函数或数据库函数存储数据
    def table_data_exists(self, table):
        """ 逻辑层函数，判断数据表是否存在

        Parameters
        ----------
        table: 数据表名称

        Returns
        -------
        bool: True if table exists, False otherwise
        """
        if self.source_type == 'db':
            return self.db_table_exists(db_table=table)
        elif self.source_type == 'file':
            return self.file_exists(table)
        else:
            raise KeyError(f'invalid source_type: {self.source_type}')

    def read_table_data(self, table, shares=None, start=None, end=None):
        """ 从本地数据表中读取数据并返回DataFrame，不修改数据格式

        在读取数据表时读取所有的列，但是返回值筛选ts_code以及trade_date between start 和 end

        Parameters
        ----------
        table: str
            数据表名称
        shares: list，
            ts_code筛选条件，为空时给出所有记录
        start: str，
            YYYYMMDD格式日期，为空时不筛选
        end: str，
            YYYYMMDD格式日期，当start不为空时有效，筛选日期范围

        Returns
        -------
        pd.DataFrame 返回数据表中的数据

        """

        # TODO: 历史数据表的规模较大，如果数据存储在数据库中，读取和存储时
        #  没有问题，但是如果数据存储在文件中，需要优化存储和读取过程
        #  ，以便提高效率。目前优化了csv文件的读取，通过分块读取提高
        #  csv文件的读取效率，其他文件系统的读取还需要进一步优化
        if not isinstance(table, str):
            raise TypeError(f'table name should be a string, got {type(table)} instead.')
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name: {table}.')

        if shares is not None:
            assert isinstance(shares, (str, list))
            if isinstance(shares, str):
                shares = str_to_list(shares)

        if (start is not None) and (end is not None):
            start = regulate_date_format(start)
            end = regulate_date_format(end)
            assert pd.to_datetime(start) <= pd.to_datetime(end)

        columns, dtypes, primary_key, pk_dtypes = get_built_in_table_schema(table)
        # 识别primary key中的证券代码列名和日期类型列名，确认是否需要筛选证券代码及日期
        share_like_pk = None
        date_like_pk = None
        if shares is not None:
            try:
                varchar_like_dtype = [item for item in pk_dtypes if item[:7] == 'varchar'][0]
                share_like_pk = primary_key[pk_dtypes.index(varchar_like_dtype)]
            except:
                warnings.warn(f'can not find share-like primary key in the table {table}!\n'
                              f'passed argument shares will be ignored!', RuntimeWarning)
        # 识别Primary key中的，并确认是否需要筛选日期型pk
        if (start is not None) and (end is not None):
            try:
                date_like_dtype = [item for item in pk_dtypes if item in ['date', 'datetime']][0]
                date_like_pk = primary_key[pk_dtypes.index(date_like_dtype)]
            except Exception as e:
                warnings.warn(f'{e}\ncan not find date-like primary key in the table {table}!\n'
                              f'passed start({start}) and end({end}) arguments will be ignored!', RuntimeWarning)

        if self.source_type == 'file':
            # 读取table数据, 从本地文件中读取的DataFrame已经设置好了primary_key index
            # 但是并未按shares和start/end进行筛选，需要手动筛选
            df = self.read_file(file_name=table,
                                primary_key=primary_key,
                                pk_dtypes=pk_dtypes,
                                share_like_pk=share_like_pk,
                                shares=shares,
                                date_like_pk=date_like_pk,
                                start=start,
                                end=end)
            if df.empty:
                return df
            if share_like_pk is not None:
                df = df.loc[df.index.isin(shares, level=share_like_pk)]
            if date_like_pk is not None:
                # 两种方法实现筛选，分别是df.query 以及 df.index.get_level_values()
                # 第一种方法， df.query
                # df = df.query(f"{date_like_pk} >= {start} and {date_like_pk} <= {end}")
                # 第二种方法：df.index.get_level_values()
                m1 = df.index.get_level_values(date_like_pk) >= start
                m2 = df.index.get_level_values(date_like_pk) <= end
                df = df[m1 & m2]
        elif self.source_type == 'db':
            # 读取数据库表，从数据库表中读取的DataFrame并未设置primary_key index，因此
            # 需要手动设置index，但是读取的数据已经按shares/start/end筛选，无需手动筛选
            if not self.db_table_exists(db_table=table):
                # 如果数据库中不存在该表，则创建表
                self.new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            if share_like_pk is None:
                shares = None
            if date_like_pk is None:
                start = None
                end = None
            df = self.read_database(db_table=table,
                                    share_like_pk=share_like_pk,
                                    shares=shares,
                                    date_like_pk=date_like_pk,
                                    start=start,
                                    end=end)
            if df.empty:
                return df
            set_primary_key_index(df, primary_key, pk_dtypes)
        else:  # for unexpected cases:
            raise TypeError(f'Invalid value DataSource.source_type: {self.source_type}')

        return df

    def export_table_data(self, table, file_name=None, file_path=None, shares=None, start=None, end=None):
        """ 将数据表中的数据读取出来之后导出到一个文件中，便于用户使用过程中小规模转移数据或察看数据

        使用这个函数时，用户可以不用理会数据源的类型，只需要指定数据表名称，以及筛选条件即可
        导出的数据会被保存为csv文件，用户可以自行指定文件名以及文件存储路径，如果不指定文件名，
        则默认使用数据表名称作为文件名，如果不指定文件存储路径，则默认使用当前工作目录作为
        文件存储路径

        Parameters
        ----------
        table: str
            数据表名称
        file_name: str, optional
            导出的文件名，如果不指定，则默认使用数据表名称作为文件名
        file_path: str, optional
            导出的文件存储路径，如果不指定，则默认使用当前工作目录作为文件存储路径
        shares: list of str, optional
            ts_code筛选条件，为空时给出所有记录
        start: DateTime like, optional
            YYYYMMDD格式日期，为空时不筛选
        end: Datetime like，optional
            YYYYMMDD格式日期，当start不为空时有效，筛选日期范围

        Returns
        -------
        file_path_name: str
            导出的文件的完整路径
        """
        # 如果table不合法，则抛出异常
        table_master = self.get_table_master()
        non_sys_tables = table_master[table_master['table_usage'] != 'sys'].index.to_list()
        if table not in non_sys_tables:
            raise ValueError(f'Invalid table name: {table}!')

        # 检查file_name是否合法
        if file_name is None:
            file_name = table
        if file_path is None:
            file_path = os.getcwd()
        # 检查file_path_name是否存在，如果已经存在，则抛出异常
        file_path_name = path.join(file_path, file_name)
        if os.path.exists(file_path_name):
            raise FileExistsError(f'File {file_path_name} already exists!')

        # 读取table数据
        df = self.read_table_data(table=table, shares=shares, start=start, end=end)
        # 将数据写入文件
        try:
            df.to_csv(file_path_name)
        except Exception as e:
            raise RuntimeError(f'{e}, Failed to export table {table} to file {file_path_name}!')

        return file_path_name

    def write_table_data(self, df, table, on_duplicate='ignore'):
        """ 将df中的数据写入本地数据表(本地文件或数据库)

        如果本地数据表不存在则新建数据表，如果本地数据表已经存在，则将df数据添加在本地表中
        如果添加的数据主键与已有的数据相同，处理方式由on_duplicate参数确定

        Parameters
        ----------
        df: pd.DataFrame
            一个数据表，数据表的列名应该与本地数据表定义一致
        table: str
            本地数据表名，
        on_duplicate: str
            重复数据处理方式(仅当mode==db的时候有效)
            -ignore: 默认方式，将全部数据写入数据库表的末尾
            -update: 将数据写入数据库表中，如果遇到重复的pk则修改表中的内容

        Returns
        -------
        int: 写入的数据条数

        Notes
        -----
        注意！！不应直接使用该函数将数据写入本地数据库，因为写入的数据不会被检查
        请使用update_table_data()来更新或写入数据到本地
        """

        assert isinstance(df, pd.DataFrame)
        if not isinstance(table, str):
            raise TypeError(f'table name should be a string, got {type(table)} instead.')
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name.')
        columns, dtypes, primary_key, pk_dtype = get_built_in_table_schema(table)
        rows_affected = 0
        if self.source_type == 'file':
            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            rows_affected = self.write_file(df, file_name=table)
        elif self.source_type == 'db':
            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            if not self.db_table_exists(table):
                self.new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            if on_duplicate == 'ignore':
                rows_affected = self.write_database(df, db_table=table)
            elif on_duplicate == 'update':
                rows_affected = self.update_database(df, db_table=table, primary_key=primary_key)
            else:  # for unexpected cases
                raise KeyError(f'Invalid process mode on duplication: {on_duplicate}')
        self._table_list.add(table)
        return rows_affected

    def fetch_history_table_data(self, table, channel='tushare', df=None, f_name=None, **kwargs):
        """从网络获取本地数据表的历史数据，并进行内容写入前的预处理：

        数据预处理包含以下步骤：
        1，根据channel确定数据源，根据table名下载相应的数据表
        2，处理获取的df的格式，确保为只含简单range-index的格式

        Parameters
        ----------
        table: str,
            数据表名，必须是database中定义的数据表
        channel: str, optional
            str: 数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
            - 'df'      : 通过参数传递一个df，该df的columns必须与table的定义相同
            - 'csv'     : 通过本地csv文件导入数据，此时必须给出f_name参数
            - 'excel'   : 通过一个Excel文件导入数据，此时必须给出f_name参数
            - 'tushare' : 从Tushare API获取金融数据，请自行申请相应权限和积分
            - 'other'   : NotImplemented 其他金融数据API，尚未开发
        df: pd.DataFrame
            通过传递一个DataFrame获取数据, 如果数据获取渠道为"df"，则必须给出此参数
        f_name: str 通过本地csv文件或excel文件获取数据
            如果数据获取方式为"csv"或者"excel"时，必须给出此参数，表示文件的路径
        **kwargs:
            用于下载金融数据的函数参数，或者读取本地csv文件的函数参数

        Returns
        -------
        pd.DataFrame:
            下载后并处理完毕的数据，DataFrame形式，仅含简单range-index格式
        """

        # 目前仅支持从tushare获取数据，未来可能增加新的API
        from .tsfuncs import acquire_data
        if not isinstance(table, str):
            raise TypeError(f'table name should be a string, got {type(table)} instead.')
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name {table}')
        if not isinstance(channel, str):
            raise TypeError(f'channel should be a string, got {type(channel)} instead.')
        if channel not in AVAILABLE_CHANNELS:
            raise KeyError(f'Invalid channel name {channel}')

        column, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
        # 从指定的channel获取数据
        if channel == 'df':
            # 通过参数传递的DF获取数据
            if df is None:
                raise ValueError(f'a DataFrame must be given while channel == "df"')
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f'local df should be a DataFrame, got {type(df)} instead.')
            dnld_data = df
        elif channel == 'csv':
            # 读取本地csv数据文件获取数据
            if f_name is None:
                raise ValueError(f'a file path and name must be given while channel == "csv"')
            if not isinstance(f_name, str):
                raise TypeError(f'file name should be a string, got {type(df)} instead.')
            dnld_data = pd.read_csv(f_name, **kwargs)
        elif channel == 'excel':
            # 读取本地Excel文件获取数据
            assert f_name is not None, f'a file path and name must be given while channel == "excel"'
            assert isinstance(f_name, str), \
                f'file name should be a string, got {type(df)} instead.'
            raise NotImplementedError
        elif channel == 'tushare':
            # 通过tushare的API下载数据
            api_name = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('tushare')]
            try:
                dnld_data = acquire_data(api_name, **kwargs)
            except Exception as e:
                raise Exception(f'data {table} can not be acquired from tushare\n{e}')
        else:
            raise NotImplementedError
        res = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
        return res

    def fetch_realtime_price_data(self, table, channel, symbols):
        """ 获取分钟级实时股票价格数据，并进行内容写入前的预处理, 目前只支持下面的数据表获取实时分钟数据：
        stock_1min/stock_5min/stock_15min/stock_30min/stock_hourly

        Parameters
        ----------
        table: str,
            数据表名，必须是database中定义的数据表
        channel: str,
            数据获取渠道，金融数据API，支持以下选项:
            - 'eastmoney': 通过东方财富网的API获取数据
            - 'tushare':   从Tushare API获取金融数据，请自行申请相应权限和积分
            - 'other':     NotImplemented 其他金融数据API，尚未开发
        symbols: str or list of str
            用于下载金融数据的函数参数，需要输入完整的ts_code，表示股票代码

        Returns
        -------
        pd.DataFrame:
            下载后并处理完毕的数据，DataFrame形式，仅含简单range-index格式
            columns: ts_code, trade_time, open, high, low, close, vol, amount
        """
        # 目前支持从tushare和eastmoney获取数据，未来可能增加新的API
        if not isinstance(table, str):
            raise TypeError(f'table name should be a string, got {type(table)} instead.')
        if table not in ['stock_1min', 'stock_5min', 'stock_15min', 'stock_30min', 'stock_hourly']:
            raise KeyError(f'realtime minute data is not available for table {table}')

        table_freq_map = {
            '1min':  '1MIN',
            '5min':  '5MIN',
            '15min': '15MIN',
            '30min': '30MIN',
            'h':     '60MIN',
        }

        table_freq = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('freq')]
        realtime_data_freq = table_freq_map[table_freq]
        # 从指定的channel获取数据
        if channel == 'tushare':
            # tushare 要求symbols以逗号分隔字符串形式给出
            if isinstance(symbols, list):
                symbols = ','.join(symbols)
            from .tsfuncs import acquire_data as acquire_data_from_ts
            # 通过tushare的API下载数据
            api_name = 'realtime_min'
            if symbols is None:
                raise ValueError(f'ts_code must be given while channel == "tushare"')
            try:
                dnld_data = acquire_data_from_ts(api_name, ts_code=symbols, freq=realtime_data_freq)
            except Exception as e:
                raise Exception(f'data {table} can not be acquired from tushare\n{e}')

            # 从下载的数据中提取出需要的列
            dnld_data = dnld_data[['code', 'time', 'open', 'high', 'low', 'close', 'volume', 'amount']]
            dnld_data = dnld_data.rename(columns={
                'code':   'ts_code',
                'time':   'trade_time',
                'volume': 'vol',
            })

            return dnld_data
        # 通过东方财富网的API下载数据
        elif channel == 'eastmoney':
            from .emfuncs import acquire_data as acquire_data_from_em
            if isinstance(symbols, str):
                # 此时symbols应该以字符串列表的形式给出
                symbols = str_to_list(symbols)
            result_data = pd.DataFrame(
                    columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount'],
            )
            table_freq_map = {
                '1min':  1,
                '5min':  5,
                '15min': 15,
                '30min': 30,
                'h':     60,
            }
            current_time = pd.to_datetime('today')
            # begin time is freq minutes before current time
            begin_time = current_time.strftime('%Y%m%d')
            for symbol in symbols:
                code = symbol.split('.')[0]
                dnld_data = acquire_data_from_em(
                        api_name='get_k_history',
                        code=code,
                        beg=begin_time,
                        klt=table_freq_map[table_freq],
                        fqt=0,  # 获取不复权数据
                )
                # 仅保留dnld_data的最后一行，并添加ts_code列，值为symbol
                dnld_data = dnld_data.iloc[-1:, :]
                dnld_data['ts_code'] = symbol
                # 将dnld_data合并到result_data的最后一行 # TODO: 检查是否需要ignore_index参数？此时index信息会丢失

                result_data = pd.concat([result_data, dnld_data], axis=0, ignore_index=True)

            return result_data
        else:
            raise NotImplementedError

    def update_table_data(self, table, df, merge_type='update'):
        """ 检查输入的df，去掉不符合要求的列或行后，将数据合并到table中，包括以下步骤：

            1，检查下载后的数据表的列名是否与数据表的定义相同，删除多余的列
            2，如果datasource type是"db"，删除下载数据中与本地数据重复的部分，仅保留新增数据
            3，如果datasource type是"file"，将下载的数据与本地数据合并并去重
            返回处理完毕的dataFrame

        Parameters
        ----------
        table: str,
            数据表名，必须是database中定义的数据表
        merge_type: str
            指定如何合并下载数据和本地数据：
            - 'update': 默认值，如果下载数据与本地数据重复，用下载数据替代本地数据
            - 'ignore' : 如果下载数据与本地数据重复，忽略重复部分
        df: pd.DataFrame
            通过传递一个DataFrame获取数据
            如果数据获取渠道为"df"，则必须给出此参数

        Returns
        -------
        int, 写入数据表中的数据的行数
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f'df should be a dataframe, got {type(df)} instead')
        if not isinstance(merge_type, str):
            raise TypeError(f'merge type should be a string, got {type(merge_type)} instead.')
        if merge_type not in ['ignore', 'update']:
            raise KeyError(f'Invalid merge type, should be either "ignore" or "update"')

        dnld_data = df
        if dnld_data.empty:
            return 0

        table_columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
        dnld_data = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
        dnld_columns = dnld_data.columns.to_list()
        # 如果table中的相当部分(25%)不能从df中找到，判断df与table完全不匹配，报错
        # 否则判断df基本与table匹配，根据Constraints，添加缺少的列(通常为NULL列)
        missing_columns = [col for col in table_columns if col not in dnld_columns]
        if len(missing_columns) >= (len(table_columns) * 0.25):
            raise ValueError(f'there are too many missing columns in downloaded df, can not merge to local table:'
                             f'table_columns:\n{[table_columns]}\n'
                             f'downloaded:\n{[dnld_columns]}')
        else:
            pass  # 在后面调整列顺序时会同时添加缺的列并调整顺序
        # 删除数据中过多的列，不允许出现缺少列
        columns_to_drop = [col for col in dnld_columns if col not in table_columns]
        if len(columns_to_drop) > 0:
            dnld_data.drop(columns=columns_to_drop, inplace=True)
        # 确保df与table的column顺序一致
        if len(missing_columns) > 0 or any(item_d != item_t for item_d, item_t in zip(dnld_columns, table_columns)):
            dnld_data = dnld_data.reindex(columns=table_columns, copy=False)
        if self.source_type == 'file':
            # 如果source_type == 'file'，需要将下载的数据与本地数据合并，本地数据必须全部下载，
            # 数据量大后非常费时
            # 因此本地文件系统承载的数据量非常有限
            local_data = self.read_table_data(table)
            set_primary_key_index(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
            # 根据merge_type处理重叠部分：
            if merge_type == 'ignore':
                # 丢弃下载数据中的重叠部分
                dnld_data = dnld_data[~dnld_data.index.isin(local_data.index)]
            elif merge_type == 'update':  # 用下载数据中的重叠部分覆盖本地数据，下载数据不变，丢弃本地数据中的重叠部分(仅用于本地文件保存的情况)
                local_data = local_data[~local_data.index.isin(dnld_data.index)]
            else:  # for unexpected cases
                raise KeyError(f'Invalid merge type, got "{merge_type}"')
            rows_affected = self.write_table_data(pd.concat([local_data, dnld_data]), table=table)
        elif self.source_type == 'db':
            # 如果source_type == 'db'，不需要合并数据，当merge_type == 'update'时，甚至不需要下载
            # 本地数据
            if merge_type == 'ignore':
                dnld_data_range = get_primary_key_range(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
                local_data = self.read_table_data(table, **dnld_data_range)
                set_primary_key_index(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
                dnld_data = dnld_data[~dnld_data.index.isin(local_data.index)]
            dnld_data = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
            rows_affected = self.write_table_data(df=dnld_data, table=table, on_duplicate=merge_type)
        else:  # unexpected case
            raise KeyError(f'invalid data source type')

        return rows_affected

    def drop_table_data(self, table):
        """ 删除本地存储的数据表(操作不可撤销，谨慎使用)

        Parameters
        ----------
        table: str,
            本地数据表的名称

        Returns
        -------
        None
        """
        if self.source_type == 'db':
            self.drop_db_table(db_table=table)
        elif self.source_type == 'file':
            self.drop_file(file_name=table)
        self._table_list.difference_update([table])
        return None

    def get_table_data_coverage(self, table, column, min_max_only=False):
        """ 获取本地数据表内容的覆盖范围，取出数据表的"column"列中的去重值并返回

        Parameters
        ----------
        table: str,
            数据表的名称
        column: str or list of str
            需要去重并返回的数据列
        min_max_only: bool, default False
            为True时不需要返回整个数据列，仅返回最大值和最小值
            如果仅返回最大值和和最小值，返回值为一个包含两个元素的列表，
            第一个元素是最小值，第二个是最大值，第三个是总数量

        Returns
        -------
        List, 代表数据覆盖范围的列表

        Examples
        --------
        >>> import qteasy
        >>> qteasy.QT_DATA_SOURCE.get_table_data_coverage('stock_daily', 'ts_code')
        Out:
        ['000001.SZ',
         '000002.SZ',
         '000003.SZ',
         '000004.SZ',
         '000005.SZ',
         '000006.SZ',
         ...,
         '002407.SZ',
         '002408.SZ',
         '002409.SZ',
         '002410.SZ',
         '002411.SZ',
         ...]
        >>> import qteasy as qt
        >>> qt.QT_DATA_SOURCE.get_table_data_coverage('stock_daily', 'ts_code', min_max_only=True)
        Out:
        ['000001.SZ', '873593.BJ']
        """
        if self.source_type == 'db':
            if min_max_only:
                return self.get_db_table_minmax(table, column)
            else:
                return self.get_db_table_coverage(table, column)
        elif self.source_type == 'file':
            columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
            return self.get_file_table_coverage(table, column, primary_keys, pk_dtypes, min_max_only)
        else:
            raise TypeError(f'Invalid source type: {self.source_type}')

    def get_data_table_size(self, table, human=True, string_form=True):
        """ 获取数据表占用磁盘空间的大小

        Parameters
        ----------
        table: str
            数据表名称
        human: bool, default True
            True时显示容易阅读的形式，如1.5MB而不是1590868， False时返回字节数
        string_form: bool, default True
            True时以字符串形式返回结果，便于打印

        Returns
        -------
        tuple (size, rows): tuple of int or str:

        """
        if self.source_type == 'file':
            size = self.get_file_size(table)
            rows = self.get_file_rows(table)
            # rows = 'unknown'
        elif self.source_type == 'db':
            rows, size = self.get_db_table_size(table)
        else:
            raise RuntimeError(f'unknown source type: {self.source_type}')
        if size == -1:
            return 0, 0
        if not string_form:
            return size, rows
        if human:
            return f'{human_file_size(size)}', f'{human_units(rows)}'
        else:
            return f'{size}', f'{rows}'

    def get_table_info(self, table, verbose=True, print_info=True, human=True):
        """ 获取并打印数据表的相关信息，包括数据表是否已有数据，数据量大小，占用磁盘空间、数据覆盖范围，
            以及数据下载方法

        Parameters:
        -----------
        table: str
            数据表名称
        verbose: bool, Default: True
            是否显示更多信息，如是，显示表结构等信息
        print_info: bool, Default: True
            是否打印输出所有结果
        human: bool, Default: True
            是否给出容易阅读的字符串形式

        Returns
        -------
        一个tuple，包含数据表的结构化信息：
            (table name:    数据表名称
             table_exists:  bool，数据表是否存在
             table_size:    int/str，数据表占用磁盘空间，human 为True时返回容易阅读的字符串
             table_rows:    int/str，数据表的行数，human 为True时返回容易阅读的字符串
             primary_key1:  str，数据表第一个主键名称
             pk_count1:     int，数据表第一个主键记录数量
             pk_min1:       obj，数据表主键1起始记录
             pk_max1:       obj，数据表主键2最终记录
             primary_key2:  str，数据表第二个主键名称
             pk_count2:     int，数据表第二个主键记录
             pk_min2:       obj，数据表主键2起始记录
             pk_max2:       obj，数据表主键2最终记录)
        """
        pk1 = None
        pk_records1 = None
        pk_min1 = None
        pk_max1 = None
        pk2 = None
        pk_records2 = None
        pk_min2 = None
        pk_max2 = None
        if not isinstance(table, str):
            raise TypeError(f'table should be name of a table, got {type(table)} instead')
        if not table.lower() in TABLE_MASTERS:
            raise ValueError(f'in valid table name: {table}')

        columns, dtypes, remarks, primary_keys, pk_dtypes = get_built_in_table_schema(table,
                                                                                      with_remark=True,
                                                                                      with_primary_keys=True)
        critical_key = TABLE_MASTERS[table][6]
        table_schema = pd.DataFrame({'columns': columns,
                                     'dtypes':  dtypes,
                                     'remarks': remarks})
        table_exists = self.table_data_exists(table)
        if print_info:
            if table_exists:
                table_size, table_rows = self.get_data_table_size(table, human=human)
            else:
                table_size, table_rows = '0 MB', '0'
            print(f'<{table}>, {table_size}/{table_rows} records on disc\n'
                  f'primary keys: \n'
                  f'-----------------------------------')
        else:
            if table_exists:
                table_size, table_rows = self.get_data_table_size(table, string_form=human, human=human)
            else:
                table_size, table_rows = 0, 0
        pk_count = 0
        for pk in primary_keys:
            pk_min_max_count = self.get_table_data_coverage(table, pk, min_max_only=True)
            pk_count += 1
            critical = ''
            record_count = 'unknown'
            if len(pk_min_max_count) == 3:
                record_count = pk_min_max_count[2]
            if len(pk_min_max_count) == 0:
                pk_min_max_count = ['N/A', 'N/A']
            if print_info:
                if pk == critical_key:
                    critical = "       *<CRITICAL>*"
                print(f'{pk_count}:  {pk}:{critical}\n'
                      f'    <{record_count}> entries\n'
                      f'    starts:'
                      f' {pk_min_max_count[0]}, end: {pk_min_max_count[1]}')
            if pk_count == 1:
                pk1 = pk
                pk_records1 = record_count
                pk_min1 = pk_min_max_count[0]
                pk_max1 = pk_min_max_count[1]
            elif pk_count == 2:
                pk2 = pk
                pk_records2 = record_count
                pk_min2 = pk_min_max_count[0]
                pk_max2 = pk_min_max_count[1]
            else:
                pass
        if verbose and print_info:
            print(f'\ncolumns of table:\n'
                  f'------------------------------------\n'
                  f'{table_schema}\n')
        return (table,
                table_exists,
                table_size,
                table_rows,
                pk1,
                pk_records1,
                pk_min1,
                pk_max1,
                pk2,
                pk_records2,
                pk_min2,
                pk_max2
                )

    # ==============
    # 系统操作表操作函数，专门用于操作sys_operations表，记录系统操作信息，数据格式简化
    # ==============
    def get_sys_table_last_id(self, table):
        """ 从已有的table中获取最后一个id

        Parameters
        ----------
        table: str
            数据表名称

        Returns
        -------
        last_id: int 当前使用的最后一个ID（自增ID）
        """

        ensure_sys_table(table)
        # 如果是文件系统，在可行的情况下，直接从文件系统中获取最后一个id，否则读取文件数据后获取id
        if self.source_type == 'file':
            df = self.read_sys_table_data(table)
            if df is None:
                return 0
            # if df.empty:
            #     return 0
            return df.index.max()
        # 如果是数据库系统，直接获取最后一个id
        elif self.source_type == 'db':
            if not self.db_table_exists(table):
                columns, dtypes, prime_keys, pk_dtypes = get_built_in_table_schema(table)
                self.new_db_table(table,
                                  columns=columns,
                                  dtypes=dtypes,
                                  primary_key=prime_keys,
                                  auto_increment_id=True)
                return 0

            import pymysql
            con = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.__user__,
                    password=self.__password__,
                    db=self.db_name,
            )
            cursor = con.cursor()
            db_name = self.db_name
            sql = f"SELECT AUTO_INCREMENT\n" \
                  f"FROM information_schema.TABLES\n" \
                  f"WHERE `TABLE_SCHEMA` = %s\n" \
                  f"AND `TABLE_NAME` = %s;"

            try:
                cursor.execute(sql, (db_name, table))
                con.commit()
                res = cursor.fetchall()
                return res[0][0] - 1
            except Exception as e:
                raise RuntimeError(
                    f'{e}, An error occurred when getting last record_id for table {table} with SQL:\n{sql}')
            finally:
                con.close()

        else:  # for other unexpected cases
            pass
        pass

    def read_sys_table_data(self, table, record_id=None, **kwargs):
        """读取系统操作表的数据，包括读取所有记录，以及根据给定的条件读取记录

        每次读取的数据都以行为单位，必须读取整行数据，不允许读取个别列，
        如果给出id，只返回id行记录（dict），如果不给出id，返回所有记录（DataFrame）

        Parameters
        ----------
        table: str
            需要读取的数据表名称
        record_id: int, Default: None
            如果给出id，只返回id行记录
        kwargs: dict
            筛选数据的条件，包括用作筛选条件的字典如: account_id = 123

        Returns
        -------
        data: dict
            当给出record_id时，读取的数据为dict，包括数据表的结构化信息以及数据表中的记录
        pd.DataFrame:
            当不给出record_id时，读取的数据为DataFrame，包括数据表的结构化信息以及数据表中的记录
        None:
            当输入的id或筛选条件没有匹配项时
        """

        # 检查record_id是否合法
        if record_id is not None and record_id <= 0:
            return None

        ensure_sys_table(table)

        # 检查kwargs中是否有不可用的字段
        columns, dtypes, p_keys, pk_dtypes = get_built_in_table_schema(table)
        if any(k not in columns for k in kwargs):
            raise KeyError(f'kwargs not valid: {[k for k in kwargs if k not in columns]}')

        id_column = p_keys[0] if (len(p_keys) == 1) and (record_id is not None) else None
        id_values = [record_id] if record_id else None

        # 读取数据，如果给出id，则只读取一条数据，否则读取所有数据
        if self.source_type == 'db':
            res_df = self.read_database(table, share_like_pk=id_column, shares=id_values)
            if res_df.empty:
                return None
            set_primary_key_index(res_df, primary_key=p_keys, pk_dtypes=pk_dtypes)
        elif self.source_type == 'file':
            res_df = self.read_file(table, p_keys, pk_dtypes, share_like_pk=id_column, shares=id_values)
        else:  # for other unexpected cases
            res_df = pd.DataFrame()

        if res_df.empty:
            return None

        # 筛选数据
        for k, v in kwargs.items():
            res_df = res_df.loc[res_df[k] == v]

        if record_id is not None:
            return res_df.loc[record_id].to_dict()
        else:
            return res_df if not res_df.empty else None

    def update_sys_table_data(self, table, record_id, **data):
        """ 更新系统操作表的数据，根据指定的id更新数据，更新的内容由kwargs给出。

        每次只能更新一条数据，数据以dict形式给出
        可以更新一个或多个字段，如果给出的字段不存在，则抛出异，id不可更新。
        id必须存在，否则抛出异常

        Parameters
        ----------
        table: str
            需要更新的数据表名称
        record_id: int
            需要更新的数据的id
        data: dict
            需要更新的数据，包括需要更新的字段如: account_id = 123

        Returns
        -------
        id: int
            更新的记录ID

        Raises
        ------
        KeyError: 当给出的id不存在或为None时
        KeyError: 当给出的字段不存在时
        """

        ensure_sys_table(table)
        # TODO: 为了提高开发速度，使用self.update_table_data()，后续需要重构代码
        #  用下面的思路重构代码，提高运行效率
        """
        # 检察数据，如果**kwargs中有不可用的字段，则抛出异常，如果kwargs为空，则返回None

        # 判断id是否存在范围内，如果id超出范围，则抛出异常

        # 写入数据，如果是文件系统，读取文件，更新数据，然后写入文件，如果是数据库，直接用SQL更新数据库
        if self.source_type == 'file':
            pass
        elif self.source_type == 'db':
            pass
        else: # for other unexpected cases
            pass
        pass
        """

        # 将data构造为一个df，然后调用self.update_table_data()
        table_data = self.read_sys_table_data(table, record_id=record_id)
        if table_data is None:
            raise KeyError(f'record_id({record_id}) not found in table {table}')

        # 当data中有不可用的字段时，会抛出异常
        columns, dtypes, p_keys, pk_dtypes = get_built_in_table_schema(table)
        data_columns = [col for col in columns if col not in p_keys]
        if any(k not in data_columns for k in data.keys()):
            raise KeyError(f'kwargs not valid: {[k for k in data.keys() if k not in data_columns]}')

        # 更新original_data
        table_data.update(data)

        df_data = pd.DataFrame(table_data, index=[record_id])
        df_data.index.name = p_keys[0]
        self.update_table_data(table, df_data, merge_type='update')
        return record_id

    def insert_sys_table_data(self, table, **data):
        """ 插入系统操作表的数据

        一次插入一条记录，数据以dict形式给出
        不需要给出数据的ID，因为ID会自动生成
        如果给出的数据字段不完整，则抛出异常
        如果给出的数据中有不可用的字段，则抛出异常

        Parameters
        ----------
        table: str
            需要更新的数据表名称
        data: dict
            需要更新或插入的数据，数据的key必须与数据库表的字段相同，否则会抛出异常

        Returns
        -------
        record_id: int
            更新的记录ID

        Raises
        ------
        KeyError: 当给出的字段不完整或者有不可用的字段时
        """

        ensure_sys_table(table)
        # TODO: 为了缩短开发时间，先暂时调用self.update_table_data()，后续需要重构
        #  按照下面的思路重构简化代码：
        """
        # 检察数据，如果data中有不可用的字段，则抛出异常，如果data为空，则返回None
        if not isinstance(data, dict):
            raise TypeError(f'Input data must be a dict, but got {type(data)}')
        if not data:
            return None

        columns, dtypes, p_keys, pk_dtypes = get_built_in_table_schema(table)
        values = list(data.values())
        # 检查data的key是否与column完全一致，如果不一致，则抛出异常
        if list(data.keys() != columns):
            raise KeyError(f'Input data keys must be the same as the table columns, '
                           f'got {list(data.keys())} vs {columns}')

        # 写入数据，如果是文件系统，对可行的文件类型直接写入文件，否则读取文件，插入数据后再写入文件，如果是数据库，直接用SQL更新数据库
        if self.source_type == 'file':
            # 获取最后一个ID，然后+1，作为新的ID(仅当source_type==file时，数据库可以自动生成ID)
            last_id = self.get_last_id(table)
            new_id = last_id + 1 if last_id is not None else 1
            pass
        elif self.source_type == 'db':
            # 使用SQL插入一条数据到数据库
            db_table = table
            if not self.db_table_exists(db_table=table):
                # 如果数据库中不存在该表，则创建表
                self.new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            # 生成sql语句
            sql = f"INSERT INTO `{db_table}` ("
            for col in columns[:-1]:
                sql += f"`{col}`, "
            sql += f"`{columns[-1]}`)\nVALUES\n("
            for val in values[:-1]:
                sql += f"{val}, "
            sql += f"{values[-1]})\n"
            try:
                self.conn.execute(sql)
                self.conn.commit()
            except Exception as e:
                raise RuntimeError(f'{e}, An error occurred when insert data into table {table} with sql:\n{sql}')
        else:  # for other unexpected cases
            pass
        last_id = self.get_last_id(table)
        return last_id
        """

        # 将data构造为一个df，然后调用self.update_table_data()
        last_id = self.get_sys_table_last_id(table)
        record_id = last_id + 1 if last_id is not None else 1
        columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
        data_columns = [col for col in columns if col not in primary_keys]
        # 检查data的key是否与data_column完全一致，如果不一致，则抛出异常
        if any(k not in data_columns for k in data.keys()) or any(k not in data.keys() for k in data_columns):
            raise KeyError(f'Input data keys must be the same as the table data columns, '
                           f'got {list(data.keys())} vs {data_columns}')
        df = pd.DataFrame(data, index=[record_id], columns=data.keys())
        df = df.reindex(columns=columns)
        df.index.name = primary_keys[0]

        # 插入数据
        self.update_table_data(table, df, merge_type='update')
        # TODO: 这里为什么要用'ignore'而不是'update'? 现在改为'update'，
        #  test_database和test_trading测试都能通过，后续完整测试
        return record_id

    # ==============
    # 顶层函数，包括用于组合HistoryPanel的数据获取接口函数，以及自动或手动下载本地数据的操作函数
    # ==============
    def get_history_data(self, shares=None, symbols=None, htypes=None, freq='d', start=None, end=None, row_count=100,
                         asset_type='any', adj='none'):
        """ 根据给出的参数从不同的本地数据表中获取数据，并打包成一系列的DataFrame，以便组装成
            HistoryPanel对象。

        Parameters
        ----------
        shares: str or list of str
            等同于新的symbols参数，为了兼容旧的代码，保留此参数
            需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
             - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
        symbols: str or list of str
            需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
             - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
        htypes: str or list of str
            需要获取的历史数据类型集合，可以是以逗号分隔的数据类型字符串或者数据类型字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     'open, high, low, close'
             - list:    ['open', 'high', 'low', 'close']
        freq: str
            获取的历史数据的频率，包括以下选项：
             - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
             - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
             如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
        start: str, optional
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
        end: str, optional
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
        row_count: int, optional, default 10
            获取的历史数据的行数，如果指定了start和end，则忽略此参数
        asset_type: str or list of str
            限定获取的数据中包含的资产种类，包含以下选项或下面选项的组合，合法的组合方式包括
            逗号分隔字符串或字符串列表，例如: 'E, IDX' 和 ['E', 'IDX']都是合法输入
             - any: 可以获取任意资产类型的证券数据(默认值)
             - E:   只获取股票类型证券的数据
             - IDX: 只获取指数类型证券的数据
             - FT:  只获取期货类型证券的数据
             - FD:  只获取基金类型证券的数据
        adj: str
            对于某些数据，可以获取复权数据，需要通过复权因子计算，复权选项包括：
             - none / n: 不复权(默认值)
             - back / b: 后复权
             - forward / fw / f: 前复权

        Returns
        -------
        Dict of DataFrame: {htype: DataFrame[shares]}
            一个标准的DataFrame-Dict，满足stack_dataframes()函数的输入要求，以便组装成
            HistoryPanel对象
        """
        if symbols is not None:
            shares = symbols
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
        if isinstance(shares, str):
            shares = str_to_list(shares)
        if isinstance(asset_type, str):
            if asset_type.lower() == 'any':
                from qteasy.utilfuncs import AVAILABLE_ASSET_TYPES
                asset_type = AVAILABLE_ASSET_TYPES
            else:
                asset_type = str_to_list(asset_type)

        # 根据资产类型、数据类型和频率找到应该下载数据的目标数据表，以及目标列
        table_master = get_table_master()
        # 设置soft_freq = True以通过抖动频率查找频率不同但类型相同的数据表
        tables_to_read = htype_to_table_col(
                htypes=htypes,
                freq=freq,
                asset_type=asset_type,
                soft_freq=True
        )
        table_data_acquired = {}
        table_data_columns = {}
        if (start is not None) or (end is not None):
            # 如果指定了start或end，则忽略row_count参数, 但是如果row_count为None，则默认为-1, 读取所有数据
            row_count = 0 if row_count is not None else -1
        # 逐个读取相关数据表，删除名称与数据类型不同的，保存到一个字典中，这个字典的健为表名，值为读取的DataFrame
        for tbl, columns in tables_to_read.items():
            df = self.read_table_data(tbl, shares=shares, start=start, end=end)
            if not df.empty:
                cols_to_drop = [col for col in df.columns if col not in columns]
                df.drop(columns=cols_to_drop, inplace=True)
                if row_count > 0:
                    # 读取每一个ts_code的最后row_count行数据
                    df = df.groupby('ts_code').tail(row_count)
            table_data_acquired[tbl] = df
            table_data_columns[tbl] = df.columns
        # 从读取的数据表中提取数据，生成单个数据类型的dataframe，并把各个dataframe合并起来
        # 在df_by_htypes中预先存储了多个空DataFrame，用于逐个合并相关的历史数据
        df_by_htypes = {k: v for k, v in zip(htypes, [pd.DataFrame()] * len(htypes))}
        for htyp in htypes:
            for tbl in tables_to_read:
                if htyp in table_data_columns[tbl]:
                    df = table_data_acquired[tbl]
                    # 从本地读取的DF中的数据是按multi_index的形式stack起来的，因此需要unstack，成为多列、单index的数据
                    if not df.empty:
                        htyp_series = df[htyp]
                        new_df = htyp_series.unstack(level=0)
                        old_df = df_by_htypes[htyp]
                        # 使用两种方法实现df的合并，分别是merge()和join()
                        # df_by_htypes[htyp] = old_df.merge(new_df,
                        #                                   how='outer',
                        #                                   left_index=True,
                        #                                   right_index=True,
                        #                                   suffixes=('', '_y'))
                        df_by_htypes[htyp] = old_df.join(new_df,
                                                         how='outer',
                                                         rsuffix='_y')

        # 如果在历史数据合并后发现列名称冲突，发出警告信息，并删除后添加的列
        conflict_cols = ''
        for htyp in htypes:
            df_columns = df_by_htypes[htyp].columns.to_list()
            col_with_suffix = [col for col in df_columns if col[-2:] == '_y']
            if len(col_with_suffix) > 0:
                df_by_htypes[htyp].drop(columns=col_with_suffix, inplace=True)
                conflict_cols += f'd-type {htyp} conflicts in {list(set(col[:-2] for col in col_with_suffix))};\n'
        if conflict_cols != '':
            warnings.warn(f'\nConflict data encountered, some types of data are loaded from multiple tables, '
                          f'conflicting data might be discarded:\n'
                          f'{conflict_cols}', DataConflictWarning)
        # 如果提取的数据全部为空DF，说明DataSource可能数据不足，报错并建议
        if all(df.empty for df in df_by_htypes.values()):
            raise RuntimeError(f'Empty data extracted from DataSource {self.connection_type} with parameters:\n'
                               f'shares: {shares}\n'
                               f'htypes: {htypes}\n'
                               f'start/end/freq: {start}/{end}/"{freq}"\n'
                               f'asset_type/adj: {asset_type} / {adj}\n'
                               f'To check data availability, use one of the following:\n'
                               f'Availability of all tables:     qt.get_table_overview()，or\n'
                               f'Availability of <table_name>:   qt.get_table_info(\'table_name\')\n'
                               f'To fill datasource:             qt.refill_data_source(tables=\'table_name\', '
                               f'start=\'YYYYMMDD\', end=\'YYYYMMDD\', **kwargs)')
        # 如果需要复权数据，计算复权价格
        adj_factors = {}
        if adj.lower() not in ['none', 'n']:
            # 下载复权因子
            adj_tables_to_read = table_master.loc[(table_master.table_usage == 'adj') &
                                                  table_master.asset_type.isin(asset_type)].index.to_list()
            for tbl in adj_tables_to_read:
                adj_df = self.read_table_data(tbl, shares=shares, start=start, end=end)
                if not adj_df.empty:
                    adj_df = adj_df['adj_factor'].unstack(level=0)
                adj_factors[tbl] = adj_df
            # 如果adj table不为空但无法读取adj因子，则报错
            if adj_tables_to_read and (not adj_factors):
                raise ValueError(f'Failed reading price adjust factor data. call "qt.get_table_info()" to '
                                 f'check local source data availability')

        if adj_factors:
            # 根据复权因子更新所有可复权数据
            prices_to_adjust = [item for item in htypes if item in ADJUSTABLE_PRICE_TYPES]
            for htyp in prices_to_adjust:
                price_df = df_by_htypes[htyp]
                all_ts_codes = price_df.columns
                combined_factors = 1.0
                # 后复权价 = 当日最新价 × 当日复权因子
                for af in adj_factors:
                    combined_factors *= adj_factors[af].reindex(columns=all_ts_codes, index=price_df.index).fillna(1.0)
                # 得到合并后的复权因子，如果数据的频率为日级(包括周、月)，直接相乘即可
                #  但如果数据的频率是分钟级，则需要将复权因子也扩展到分钟级，才能相乘
                if freq in ['min', '1min', '5min', '15min', '30min', 'h']:
                    expanded_factors = combined_factors.reindex(price_df.index.date)
                    expanded_factors.index = price_df.index
                    price_df *= expanded_factors
                else:
                    price_df *= combined_factors
                # 前复权价 = 当日复权价 ÷ 最新复权因子
                if adj.lower() in ['forward', 'fw', 'f'] and len(combined_factors) > 1:
                    price_df /= combined_factors.iloc[-1]

        # 最后整理数据，确保每一个htype的数据框的columns与shares相同
        for htyp, df in df_by_htypes.items():
            df_by_htypes[htyp] = df.reindex(columns=shares)
        # print(f'[DEBUG]: in database.py get_history_data() got db_by_htypes:\n{df_by_htypes}')
        return df_by_htypes

    def get_index_weights(self, index, start=None, end=None, shares=None):
        """ 从本地数据仓库中获取一个指数的成分权重

        Parameters
        ----------
        index: [str, list]
            需要获取成分的指数代码，可以包含多个指数，每个指数
        start: str
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
        end: str
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
        shares: [str, list]
            需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
             - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']

        Returns
        -------
        Dict 一个标准的DataFrame-Dict，满足stack_dataframes()函数的输入要求，以便组装成
            HistoryPanel对象
        """
        if isinstance(index, str):
            index = str_to_list(index)
        if isinstance(shares, str):
            shares = str_to_list(shares)
        # 读取时间内的权重数据
        weight_data = self.read_table_data('index_weight', shares=index, start=start, end=end)
        if not weight_data.empty:
            weight_data = weight_data.unstack()
        else:
            # return empty dict
            return {}
        weight_data.columns = weight_data.columns.get_level_values(1)
        all_shares = weight_data.columns
        df_by_index = {}
        index_names = []
        columns_to_drop = []
        indices_found = weight_data.index.get_level_values(0)
        # 整理读取数据的结构，删除不需要的股票， 添加额外的股票，整理顺序
        if shares is not None:
            if isinstance(shares, str):
                shares = str_to_list(shares)
            columns_to_drop = [item for item in all_shares if item not in shares]
        for idx in index:
            if idx in indices_found:
                weight_df = weight_data.loc[idx]
            else:
                weight_df = pd.DataFrame(columns=all_shares)
            index_names.append(idx)
            if shares is not None:
                weight_df.drop(columns=columns_to_drop, inplace=True)
                weight_df = weight_df.reindex(columns=shares)
            df_by_index['wt-' + idx] = weight_df
        return df_by_index

    def refill_local_source(self, tables=None, dtypes=None, freqs=None, asset_types=None, start_date=None,
                            end_date=None, symbols=None, merge_type='update', reversed_par_seq=False, parallel=True,
                            process_count=None, chunk_size=100, refresh_trade_calendar=False, log=False):
        """ 批量下载历史数据并保存到本地数据仓库

        Parameters
        ----------
        tables: str or list of str
            需要补充的本地数据表，可以同时给出多个table的名称，逗号分隔字符串和字符串列表都合法：
            例如，下面两种方式都合法且相同：
                table='stock_indicator, stock_daily, income, stock_adj_factor'
                table=['stock_indicator', 'stock_daily', 'income', 'stock_adj_factor']
            除了直接给出表名称以外，还可以通过表类型指明多个表，可以同时输入多个类型的表：
                - 'all'     : 所有的表
                - 'cal'     : 交易日历表
                - 'basics'  : 所有的基础信息表
                - 'adj'     : 所有的复权因子表
                - 'data'    : 所有的历史数据表
                - 'events'  : 所有的历史事件表(如股票更名、更换基金经理、基金份额变动等)
                - 'report'  : 财务报表
                - 'comp'    : 指数成分表
        dtypes: str or list of str
            通过指定dtypes来确定需要更新的表单，只要包含指定的dtype的数据表都会被选中
            如果给出了tables，则dtypes参数会被忽略
        freqs: str or list of str
            通过指定tables或dtypes来确定需要更新的表单时，指定freqs可以限定表单的范围
            如果tables != all时，给出freq会排除掉freq与之不符的数据表
        asset_types: str or list of str
            通过指定tables或dtypes来确定需要更新的表单时，指定asset_types可以限定表单的范围
            如果tables != all时，给出asset_type会排除掉与之不符的数据表
        start_date: str YYYYMMDD
            限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
        end_date: str YYYYMMDD
            限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
        symbols: str or list of str
            限定下载数据的证券代码范围，代码不需要给出类型后缀，只需要给出数字代码即可。
            可以多种形式确定范围，以下输入均为合法输入：
            - '000001'
                没有指定asset_types时，000001.SZ, 000001.SH ... 等所有代码都会被选中下载
                如果指定asset_types，只有符合类型的证券数据会被下载
            - '000001, 000002, 000003'
            - ['000001', '000002', '000003']
                两种写法等效，列表中列举出的证券数据会被下载
            - '000001:000300'
                从'000001'开始到'000300'之间的所有证券数据都会被下载
        merge_type: str, Default update
            数据混合方式，当获取的数据与本地数据的key重复时，如何处理重复的数据：
            - 'update' 默认值，下载并更新本地数据的重复部分，使用下载的数据覆盖本地数据
            - 'ignore' 不覆盖本地的数据，在将数据复制到本地时，先去掉本地已经存在的数据，会导致速度降低
        reversed_par_seq: Bool, Default False
            是否逆序参数下载数据， 默认False
            - True:  逆序参数下载数据
            - False: 顺序参数下载数据
        parallel: Bool, Default True
            是否启用多线程下载数据
            - True:  启用多线程下载数据
            - False: 禁用多线程下载
        process_count: int
            启用多线程下载时，同时开启的线程数，默认值为设备的CPU核心数
        chunk_size: int
            保存数据到本地时，为了减少文件/数据库读取次数，将下载的数据累计一定数量后
            再批量保存到本地，chunk_size即批量，默认值100
        refresh_trade_calendar: Bool, Default True
            是否刷新交易日历，默认True
        log: Bool, Default False
            是否记录数据下载日志

        Returns
        -------
        None

        """

        from .tsfuncs import acquire_data
        # 1 参数合法性检查
        if (tables is None) and (dtypes is None):
            raise KeyError(f'tables and dtypes can not both be None.')
        if tables is None:
            tables = []
        if dtypes is None:
            dtypes = []
        valid_table_values = list(TABLE_MASTERS.keys()) + TABLE_USAGES + ['all']
        if not isinstance(tables, (str, list)):
            raise TypeError(f'tables should be a list or a string, got {type(tables)} instead.')
        if isinstance(tables, str):
            tables = str_to_list(tables)
        if not all(item.lower() in valid_table_values for item in tables):
            raise KeyError(f'some items in tables list are not valid: '
                           f'{[item for item in tables if item not in valid_table_values]}')
        if not isinstance(dtypes, (str, list)):
            raise TypeError(f'dtypes should be a list of a string, got {type(dtypes)} instead.')
        if isinstance(dtypes, str):
            dtypes = str_to_list(dtypes)

        code_start = None
        code_end = None
        if symbols is not None:
            if not isinstance(symbols, (str, list)):
                raise TypeError(f'code_range should be a string or list, got {type(symbols)} instead.')
            if isinstance(symbols, str):
                if len(str_to_list(symbols, ':')) == 2:
                    code_start, code_end = str_to_list(symbols, ':')
                    symbols = None
                else:
                    symbols = str_to_list(symbols, ',')

        # 2 生成需要处理的数据表清单 tables
        table_master = get_table_master()
        tables_to_refill = set()
        tables = [item.lower() for item in tables]
        if 'all' in tables:
            tables_to_refill.update(TABLE_MASTERS)
        else:
            for item in tables:
                if item in TABLE_MASTERS:
                    tables_to_refill.add(item)
                elif item in TABLE_USAGES:
                    tables_to_refill.update(
                            table_master.loc[table_master.table_usage == item.lower()].index.to_list()
                    )
            for item in dtypes:
                for tbl, schema in table_master.schema.iteritems():
                    if item.lower() in TABLE_SCHEMA[schema]['columns']:
                        tables_to_refill.add(tbl)

            if freqs is not None:
                tables_to_keep = set()
                for freq in str_to_list(freqs):
                    tables_to_keep.update(
                            table_master.loc[table_master.freq == freq.lower()].index.to_list()
                    )
                tables_to_refill.intersection_update(
                        tables_to_keep
                )
            if asset_types is not None:
                tables_to_keep = set()
                for a_type in str_to_list(asset_types):
                    tables_to_keep.update(
                            table_master.loc[table_master.asset_type == a_type.upper()].index.to_list()
                    )
                tables_to_refill.intersection_update(
                        tables_to_keep
                )

            dependent_tables = set()
            for table in tables_to_refill:
                cur_table = table_master.loc[table]
                fill_type = cur_table.fill_arg_type
                if fill_type == 'trade_date' and refresh_trade_calendar:
                    dependent_tables.add('trade_calendar')
                elif fill_type == 'table_index':
                    dependent_tables.add(cur_table.arg_rng)
            tables_to_refill.update(dependent_tables)
            # 为了避免parallel读取失败，需要确保tables_to_refill中包含trade_calendar表：
            if 'trade_calendar' not in tables_to_refill:
                if refresh_trade_calendar:
                    tables_to_refill.add('trade_calendar')
                else:
                    # 检查trade_calendar中是否已有数据，且最新日期是否足以覆盖今天，如果没有数据或数据不足，也需要添加该表
                    latest_calendar_date = self.get_table_info('trade_calendar', print_info=False)[11]
                    if latest_calendar_date == 'N/A':
                        tables_to_refill.add('trade_calendar')
                    elif pd.to_datetime('today') >= pd.to_datetime(latest_calendar_date):
                        tables_to_refill.add('trade_calendar')

        # 开始逐个下载清单中的表数据
        table_count = 0
        import time
        for table in table_master.index:
            # 逐个下载数据并写入本地数据表中
            if table not in tables_to_refill:
                continue
            table_count += 1
            cur_table_info = table_master.loc[table]
            # 3 生成数据下载参数序列
            arg_name = cur_table_info.fill_arg_name
            fill_type = cur_table_info.fill_arg_type
            freq = cur_table_info.freq

            # 开始生成所有的参数，参数的生成取决于fill_arg_type
            if (start_date is None) and (fill_type in ['datetime', 'trade_date']):
                start = cur_table_info.arg_rng
            else:
                start = start_date
            if start is not None:
                start = pd.to_datetime(start).strftime('%Y%m%d')
            if end_date is None:
                end = 'today'
            else:
                end = end_date
            end = pd.to_datetime(end).strftime('%Y%m%d')
            allow_start_end = (cur_table_info.arg_allow_start_end.lower() == 'y')
            start_end_chunk_size = 0
            if cur_table_info.start_end_chunk_size != '':
                start_end_chunk_size = int(cur_table_info.start_end_chunk_size)
            additional_args = {}
            chunked_additional_args = []
            start_end_chunk_multiplier = 1
            if allow_start_end:
                additional_args = {'start': start, 'end': end}
            if start_end_chunk_size > 0:
                start_end_chunk_lbounds = list(pd.date_range(start=start,
                                                             end=end,
                                                             freq=f'{start_end_chunk_size}d'
                                                             ).strftime('%Y%m%d'))
                start_end_chunk_rbounds = start_end_chunk_lbounds[1:]
                # 取到的日线或更低频率数据是包括右边界的，去掉右边界可以得到更精确的结果
                # 但是这样做可能没有意义
                if freq.upper() in ['D', 'W', 'M']:
                    prev_day = pd.Timedelta(1, 'd')
                    start_end_chunk_rbounds = pd.to_datetime(start_end_chunk_lbounds[1:]) - prev_day
                    start_end_chunk_rbounds = list(start_end_chunk_rbounds.strftime('%Y%m%d'))

                start_end_chunk_rbounds.append(end)
                chunked_additional_args = [{'start': s, 'end': e} for s, e in
                                           zip(start_end_chunk_lbounds, start_end_chunk_rbounds)]
                start_end_chunk_multiplier = len(chunked_additional_args)

            if fill_type in ['datetime', 'trade_date']:
                # 根据start_date和end_date生成数据获取区间
                additional_args = {}  # 使用日期作为关键参数，不再需要additional_args
                arg_coverage = pd.date_range(start=start, end=end, freq=freq)
                if fill_type == 'trade_date':
                    if freq.lower() in ['m', 'w', 'w-Fri']:
                        # 当生成的日期不连续时，或要求生成交易日序列时，需要找到最近的交易日
                        arg_coverage = map(nearest_market_trade_day, arg_coverage)
                    if freq == 'd':
                        arg_coverage = (date for date in arg_coverage if is_market_trade_day(date))
                arg_coverage = list(pd.to_datetime(list(arg_coverage)).strftime('%Y%m%d'))
            elif fill_type == 'list':
                arg_coverage = str_to_list(cur_table_info.arg_rng)
            elif fill_type == 'table_index':
                suffix = str_to_list(cur_table_info.arg_allowed_code_suffix)
                source_table = self.read_table_data(cur_table_info.arg_rng)
                arg_coverage = source_table.index.to_list()
                if code_start is not None:
                    arg_coverage = [code for code in arg_coverage if (code_start <= code.split('.')[0] <= code_end)]
                if symbols is not None:
                    arg_coverage = [code for code in arg_coverage if code.split('.')[0] in symbols]
                if suffix:
                    arg_coverage = [code for code in arg_coverage if code.split('.')[1] in suffix]
            else:
                arg_coverage = []

            # 处理数据下载参数序列，剔除已经存在的数据key
            if self.table_data_exists(table) and merge_type.lower() == 'ignore':
                # 当数据已经存在，且合并模式为"忽略新数据"时，从计划下载的数据范围中剔除已经存在的部分
                already_existed = self.get_table_data_coverage(table, arg_name)
                arg_coverage = [arg for arg in arg_coverage if arg not in already_existed]

            # 生成所有的参数, 开始循环下载并更新数据
            if reversed_par_seq:
                arg_coverage.reverse()
            if chunked_additional_args:
                import itertools
                all_kwargs = ({arg_name: val, **add_arg} for val, add_arg in
                              itertools.product(arg_coverage, chunked_additional_args))
            else:
                all_kwargs = ({arg_name: val, **additional_args} for val in arg_coverage)

            completed = 0
            total = len(list(arg_coverage)) * start_end_chunk_multiplier
            total_written = 0
            st = time.time()
            dnld_data = pd.DataFrame()
            time_elapsed = 0
            rows_affected = 0
            try:
                # 清单中的第一张表不使用parallel下载
                if parallel and table_count != 1:
                    with ProcessPoolExecutor(max_workers=process_count) as proc_pool:
                        # 这里如果直接使用fetch_history_table_data会导致程序无法运行，原因不明，目前只能默认通过tushare接口获取数据
                        #  通过TABLE_MASTERS获取tushare接口名称，并通过acquire_data直接通过tushare的API获取数据
                        api_name = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('tushare')]
                        futures = {proc_pool.submit(acquire_data, api_name, **kw): kw
                                   for kw in all_kwargs}
                        for f in as_completed(futures):
                            df = f.result()
                            cur_kwargs = futures[f]
                            completed += 1
                            if completed % chunk_size:
                                dnld_data = pd.concat([dnld_data, df])
                            else:
                                dnld_data = pd.concat([dnld_data, df])
                                rows_affected = self.update_table_data(table, dnld_data)
                                dnld_data = pd.DataFrame()
                            total_written += rows_affected
                            time_elapsed = time.time() - st
                            time_remain = sec_to_duration((total - completed) * time_elapsed / completed,
                                                          estimation=True, short_form=False)
                            progress_bar(completed, total, f'<{table}:{list(cur_kwargs.values())[0]}>'
                                                           f'{total_written}wrtn/{time_remain}left')

                        total_written += self.update_table_data(table, dnld_data)
                else:
                    for kwargs in all_kwargs:
                        df = self.fetch_history_table_data(table, **kwargs)
                        completed += 1
                        if completed % chunk_size:
                            dnld_data = pd.concat([dnld_data, df])
                        else:
                            dnld_data = pd.concat([dnld_data, df])
                            rows_affected = self.update_table_data(table, dnld_data)
                            dnld_data = pd.DataFrame()
                        total_written += rows_affected
                        time_elapsed = time.time() - st
                        time_remain = sec_to_duration(
                                (total - completed) * time_elapsed / completed,
                                estimation=True,
                                short_form=False
                        )
                        progress_bar(completed, total, f'<{table}:{list(kwargs.values())[0]}>'
                                                       f'{total_written}wrtn/{time_remain}left')
                    total_written += self.update_table_data(table, dnld_data)
                strftime_elapsed = sec_to_duration(
                        time_elapsed,
                        estimation=True,
                        short_form=True
                )
                if len(arg_coverage) > 1:
                    progress_bar(total, total, f'<{table}:{arg_coverage[0]}-{arg_coverage[-1]}>'
                                               f'{total_written}wrtn in {strftime_elapsed}\n')
                else:
                    progress_bar(total, total, f'[{table}:None>'
                                               f'{total_written}wrtn in {strftime_elapsed}\n')
            except Exception as e:
                total_written += self.update_table_data(table, dnld_data)
                warnings.warn(f'\n{e.__class__}:{str(e)} \ndownload process interrupted at [{table}]:'
                              f'<{arg_coverage[0]}>-<{arg_coverage[completed - 1]}>\n'
                              f'{total_written} rows downloaded, will proceed with next table!')
                # progress_bar(completed, total, f'[Interrupted! {table}] <{arg_coverage[0]} to {arg_coverage[-1]}>:'
                #                                f'{total_written} written in {sec_to_duration(time_elapsed)}\n')

    def get_all_basic_table_data(self, refresh_cache=False, raise_error=True):
        """ 一个快速获取所有basic数据表的函数，通常情况缓存处理以加快速度
        如果设置refresh_cache为True，则清空缓存并重新下载数据

        Parameters
        ----------
        refresh_cache: Bool, Default False
            如果为True，则清空缓存并重新下载数据
        raise_error: Bool, Default True
            如果为True，则在数据表为空时抛出ValueError

        Returns
        -------
        DataFrame
        """

        if refresh_cache:
            self._get_all_basic_table_data.cache_clear()
        return self._get_all_basic_table_data(raise_error=raise_error)

    @lru_cache(maxsize=1)
    def _get_all_basic_table_data(self, raise_error=True):
        """ 获取所有basic数据表

        Parameters
        ----------
        raise_error: Bool, Default True
            如果为True，则在数据表为空时抛出ValueError

        Returns
        -------
        tuple of DataFrames:
        df_s: stock_basic
        df_i: index_basic
        df_f: fund_basic
        df_ft: future_basic
        df_o: opt_basic

        Raises
        ------
        ValueError
            如果任意一个数据表为空，则抛出ValueError
        """
        df_s = self.read_table_data('stock_basic')
        if df_s.empty and raise_error:
            raise ValueError('stock_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="stock_basic")"')
        df_i = self.read_table_data('index_basic')
        if df_i.empty and raise_error:
            raise ValueError('index_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="index_basic")"')
        df_f = self.read_table_data('fund_basic')
        if df_f.empty and raise_error:
            raise ValueError('fund_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="fund_basic")"')
        df_ft = self.read_table_data('future_basic')
        if df_ft.empty and raise_error:
            raise ValueError('future_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="future_basic")"')
        df_o = self.read_table_data('opt_basic')
        if df_o.empty and raise_error:
            raise ValueError('opt_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="opt_basic")"')
        return df_s, df_i, df_f, df_ft, df_o

    def reconnect(self):
        """ 当数据库超时或其他原因丢失连接时，Ping数据库检查状态，
            如果可行的话，重新连接数据库

        Returns
        -------
        True: 连接成功
        False: 连接失败
        """
        if self.source_type != 'db':
            return True
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        try:
            con.ping(reconnect=True)
            con.ping()  # check if connection is still alive
            return True
        except Exception as e:
            print(f'{e} on {self.connection_type}, please check your connection')
            return False
        finally:
            con.close()


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
        raise TypeError(f'df should be a pandas DataFrame, got {type(df)} instead')
    if df.empty:
        return df
    if not isinstance(primary_key, list):
        raise TypeError(f'primary key should be a list, got {type(primary_key)} instead')
    all_columns = df.columns
    if not all(item in all_columns for item in primary_key):
        raise KeyError(f'primary key contains invalid value: '
                       f'{[item for item in primary_key if item not in all_columns]}')

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
        raise ValueError(f'wrong input!')
    df.drop(columns=primary_key, inplace=True)

    return None


def _resample_data(hist_data, target_freq,
                   method='last',
                   b_days_only=True,
                   trade_time_only=True,
                   forced_start=None,
                   forced_end=None,
                   **kwargs):
    """ 降低获取数据的频率，通过插值的方式将高频数据降频合并为低频数据，使历史数据的时间频率
    符合target_freq

    Parameters
    ----------
    hist_data: pd.DataFrame
        历史数据，是一个index为日期/时间的DataFrame
    target_freq: str
        历史数据的目标频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
         如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
    method: str
        调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
        数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
        降频可用的methods有：
        - 'last'/'close': 使用合并区间的最后一个值
        - 'first'/'open': 使用合并区间的第一个值
        - 'max'/'high': 使用合并区间的最大值作为合并值
        - 'min'/'low': 使用合并区间的最小值作为合并值
        - 'mean'/'average': 使用合并区间的平均值作为合并值
        - 'sum/total': 使用合并区间的总和作为合并值

        数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
        升频可用的methods有：
        - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN
        - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN
        - 'nan': 使用NaN值填充缺失数据
        - 'zero': 使用0值填充缺失数据
    b_days_only: bool 默认True
        是否强制转换自然日频率为工作日，即：
        'D' -> 'B'
        'W' -> 'W-FRI'
        'M' -> 'BM'
    trade_time_only: bool, 默认True
        为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
    forced_start: str, Datetime like, 默认None
        强制开始日期，如果为None，则使用hist_data的第一天为开始日期
    forced_start: str, Datetime like, 默认None
        强制结束日期，如果为None，则使用hist_data的最后一天为结束日期
    **kwargs:
        用于生成trade_time_index的参数，包括：
        include_start:   日期时间序列是否包含开始日期/时间
        include_end:     日期时间序列是否包含结束日期/时间
        start_am:        早晨交易时段的开始时间
        end_am:          早晨交易时段的结束时间
        include_start_am:早晨交易时段是否包括开始时间
        include_end_am:  早晨交易时段是否包括结束时间
        start_pm:        下午交易时段的开始时间
        end_pm:          下午交易时段的结束时间
        include_start_pm 下午交易时段是否包含开始时间
        include_end_pm   下午交易时段是否包含结束时间

    Returns
    -------
    DataFrame:
    一个重新设定index并填充好数据的历史数据DataFrame

    Examples
    --------
    例如，合并下列数据(每一个tuple合并为一个数值，?表示合并后的数值）
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(?), (?), (?)]
    数据合并方法:
    - 'last'/'close': 使用合并区间的最后一个值。如：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
    - 'first'/'open': 使用合并区间的第一个值。如：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
    - 'max'/'high': 使用合并区间的最大值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
    - 'min'/'low': 使用合并区间的最小值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
    - 'avg'/'mean': 使用合并区间的平均值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]
    - 'sum'/'total': 使用合并区间的平均值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]

    例如，填充下列数据(?表示插入的数据）
        [1, 2, 3] 填充后变为: [?, 1, ?, 2, ?, 3, ?]
    缺失数据的填充方法如下:
    - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN。如：
        [1, 2, 3] 填充后变为: [NaN, 1, 1, 2, 2, 3, 3]
    - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN。如：
        [1, 2, 3] 填充后变为: [1, 1, 2, 2, 3, 3, NaN]
    - 'nan': 使用NaN值填充缺失数据：
        [1, 2, 3] 填充后变为: [NaN, 1, NaN, 2, NaN, 3, NaN]
    - 'zero': 使用0值填充缺失数据：
        [1, 2, 3] 填充后变为: [0, 1, 0, 2, 0, 3, 0]
    """

    if not isinstance(target_freq, str):
        raise TypeError
    target_freq = target_freq.upper()
    # 如果hist_data为空，直接返回
    if hist_data.empty:
        return hist_data
    if b_days_only:
        if target_freq in ['W', 'W-SUN']:
            target_freq = 'W-FRI'
        elif target_freq == 'M':
            target_freq = 'BM'
    # 如果hist_data的freq与target_freq一致，也可以直接返回
    # TODO: 这里有bug：强制start/end的情形需要排除
    if hist_data.index.freqstr == target_freq:
        return hist_data
    # 如果hist_data的freq为None，可以infer freq
    if hist_data.index.inferred_freq == target_freq:
        return hist_data
    resampled = hist_data.resample(target_freq)
    if method in ['last', 'close']:
        resampled = resampled.last()
    elif method in ['first', 'open']:
        resampled = resampled.first()
    elif method in ['max', 'high']:
        resampled = resampled.max()
    elif method in ['min', 'low']:
        resampled = resampled.min()
    elif method in ['avg', 'mean']:
        resampled = resampled.mean()
    elif method in ['sum', 'total']:
        resampled = resampled.sum()
    elif method == 'ffill':
        resampled = resampled.ffill()
    elif method == 'bfill':
        resampled = resampled.bfill()
    elif method in ['nan', 'none']:
        resampled = resampled.first()
    elif method == 'zero':
        resampled = resampled.first().fillna(0)
    else:
        # for unexpected cases
        raise ValueError(f'resample method {method} can not be recognized.')

    # 完成resample频率切换后，根据设置去除非工作日或非交易时段的数据
    # 并填充空数据
    resampled_index = resampled.index
    if forced_start is None:
        start = resampled_index[0]
    else:
        start = pd.to_datetime(forced_start)
    if forced_end is None:
        end = resampled_index[-1]
    else:
        end = pd.to_datetime(forced_end)

    # 如果要求强制转换自然日频率为工作日频率
    # 原来的版本在resample之前就强制转换自然日到工作日，但是测试发现，pd的resample有一个bug：
    # 这个bug会导致method为last时，最后一个工作日的数据取自周日，而不是周五
    # 在实际测试中发现，如果将2020-01-01到2020-01-10之间的Hourly数据汇总到工作日时
    # 2020-01-03是周五，汇总时本来应该将2020-01-03 23:00:00的数据作为当天的数据
    # 但是实际上2020-01-05 23:00:00 的数据被错误地放置到了周五，也就是周日的数据被放到
    # 了周五，这样可能会导致错误的结果
    # 因此解决方案是，仍然按照'D'频率来resample，然后再通过reindex将非交易日的数据去除
    # 不过仅对freq为'D'的频率如此操作
    if b_days_only:
        if target_freq == 'D':
            target_freq = 'B'

    # 如果要求去掉非交易时段的数据
    from qteasy.trading_util import _trade_time_index
    if trade_time_only:
        expanded_index = _trade_time_index(
                start=start,
                end=end,
                freq=target_freq,
                trade_days_only=b_days_only,
                **kwargs
        )
    else:
        expanded_index = pd.date_range(start=start, end=end, freq=target_freq)
    resampled = resampled.reindex(index=expanded_index)
    # 如果在数据开始或末尾增加了空数据（因为forced start/forced end），需要根据情况填充
    if (expanded_index[-1] > resampled_index[-1]) or (expanded_index[0] < resampled_index[0]):
        if method == 'ffill':
            resampled.ffill(inplace=True)
        elif method == 'bfill':
            resampled.bfill(inplace=True)
        elif method == 'zero':
            resampled.fillna(0, inplace=True)

    return resampled


# noinspection PyUnresolvedReferences
def set_primary_key_frame(df, primary_key, pk_dtypes):
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
        raise TypeError(f'df should be a pandas DataFrame, got {type(df)} instead')
    if df.empty:
        return df
    if not isinstance(primary_key, list):
        raise TypeError(f'primary key should be a list, got {type(primary_key)} instead')
    if not isinstance(pk_dtypes, list):
        raise TypeError(f'primary key should be a list, got {type(primary_key)} instead')
    # TODO: 增加检查：primary_key中的元素是否在df.column中存，
    #  如果不存在，df必须有index，且index.name必须存在且与primary_key中的元素一致
    #  否则报错

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


def set_datetime_format_frame(df, primary_key, pk_dtypes):
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
    # 设置正确的时间日期格式(找到pk_dtype中是否有"date"或"TimeStamp"类型，将相应的列设置为TimeStamp
    if ("date" in pk_dtypes) or ("TimeStamp" in pk_dtypes):
        # 需要设置正确的时间日期格式：
        # 有时候pk会包含多列，可能有多个时间日期，因此需要逐个设置
        for pk_item, dtype in zip(primary_key, pk_dtypes):
            if dtype in ['date', 'TimeStamp']:
                df[pk_item] = pd.to_datetime(df[pk_item])
    return None


def get_primary_key_range(df, primary_key, pk_dtypes):
    """ 给定一个dataframe，给出这个df表的主键的范围，用于下载数据时用作传入参数
        如果主键类型为string，则给出一个list，包含所有的元素
        如果主键类型为date，则给出上下界

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list
        以列表形式给出的primary_key列名
    pk_dtypes: list
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


def htype_to_table_col(htypes, freq='d', asset_type='E', method='permute', soft_freq=False):
    """ 根据输入的字符串htypes\freq\asset_type,查找包含该data_type的数据表以及column
        仅支持精确匹配。无法精确匹配数据表时，报错

    Parameters
    ----------
    htypes: str or list of str
        需要查找的的数据类型，该数据类型必须能在data_table_map中找到，包括所有内置数据类型，
        也包括自定义数据类型（自定义数据类型必须事先添加到data_table_map中），
        否则会被忽略
        当输入类型为str时，可以接受逗号分隔的字符串表示多个不同的data type
        如下面两种输入等效：
        'close, open, high' == ['close', 'open', 'high']
    freq: str or list of str default 'd'
        所需数据的频率，数据频率必须符合标准频率定义，即包含以下关键字：
        min / hour / H / d / w / M / Q / Y
        同时支持含数字或附加信息的频率如：
        5min / 2d / W-Fri
        如果输入的频率在data_table_map中无法找到，则根据soft_freq的值采取不同处理方式：
        - 如果soft_freq == True:
            在已有的data_table_map中查找最接近的freq并输出
        - 如果soft_freq == False:
            该项被忽略
    asset_type: (str, list) default 'E'
        所需数据的资产类型。该资产类型必须能在data_table_map中找到，
        否则会被忽略
        输入逗号分隔的多个asset_type等效于多个asset_type的list
    method: str
        决定htype和asset_type数据的匹配方式以及输出的数据表数量：
        - 'exact': 完全匹配，针对输入的每一个参数匹配一张数据表
          输出的数据列数量与htype/freq/asset_type的最大数量相同，
          如果输入的数据中freq与asset_type数量不足时，自动补足
          如果输入的数据中freq与asset_type数量太多时，自动忽略
          当输入的htype或asset_type中有一个或多个无法在data_table_map中找到匹配项时，该项会被忽略
        举例：
            输入为:
                ['close', 'pe'], ['d', 'd'], ['E', 'IDX'] 时，
            输出为:
                {'stock_daily':     ['close'],
                 'index_indicator': ['pe']}

        - 'permute': 排列组合，针对输入数据的排列组合输出匹配的数据表
          输出的数据列数量与htype/freq/asset_type的数量乘积相同，但同一张表中的数据列会
          被合并
          当某一个htype或asset_type的组合无法在data_table_map中找到时，忽略该组合
        举例：
            输入为:
                ['close', 'pe', 'open'], ['d'], ['E', 'IDX']时，
            输出为:
                {'stock_daily':     ['close', 'open'],
                 'index_daily':     ['close', 'open'],
                 'stock_indicator': ['pe'],
                 'index_indicator': ['pe']}
    soft_freq: bool, default False
        决定freq的匹配方式：
        - True: 允许不完全匹配输入的freq，优先查找更高且能够等分匹配的频率，
          失败时查找更低的频率，如果都失败，则输出None(当method为'exact'时)，
          或被忽略(当method为'permute'时)
        - False:不允许不完全匹配的freq，当输入的freq无法匹配时输出None(当method为'exact'时)

    Returns
    -------
    matched_tables: dict
    key为需要的数据所在数据表，value为该数据表中的数据列:
    {tables: columns}

    TODO: 未来可以考虑增加对freq的soft匹配，即允许不完全匹配输入的freq，优先查找更高且能够等分匹配的频率，
     失败时查找更低的频率，如果都失败，则输出None(当method为'exact'时)，
     或被忽略(当method为'permute'时)

    TODO: 下面Example中的输出结果需要更新
    Examples
    --------
    >>> htype_to_table_col('close, open, high', freq='d', asset_type='E', method='exact')
    {'stock_daily': ['close', 'open', 'high']}
    >>> htype_to_table_col('close, open, high', freq='d, m', asset_type='E', method='exact')
    {'stock_daily': ['close', 'high'], 'stock_monthly': ['open']}
    >>> htype_to_table_col('close, open, high', freq='d, m', asset_type='E, IDX', method='exact')
    {'index_monthly': ['open'], 'stock_daily': ['close', 'high']}
    >>> htype_to_table_col('close, open, high', freq='d, m', asset_type='E, IDX', method='permute')
    {'stock_daily': ['close', 'open', 'high'],
     'stock_monthly': ['close', 'open', 'high'],
     'index_daily': ['close', 'open', 'high'],
     'index_monthly': ['close', 'open', 'high']}
    """
    if isinstance(htypes, str):
        htypes = str_to_list(htypes)
    if isinstance(freq, str):
        freq = str_to_list(freq)
    if isinstance(asset_type, str):
        if asset_type.lower() == 'any':
            from .utilfuncs import AVAILABLE_ASSET_TYPES
            asset_type = AVAILABLE_ASSET_TYPES
        else:
            asset_type = str_to_list(asset_type)

    # 根据资产类型、数据类型和频率找到应该下载数据的目标数据表

    # 并开始从dtype_map中查找内容,
    # - exact模式下使用reindex确保找足数量，按照输入组合的数量查找，找不到的输出NaN
    # - permute模式下将dtype/freq/atype排列组合后查找所有可能的数据表，找不到的输出NaN
    dtype_map = get_dtype_map()
    if method.lower() == 'exact':
        # 一一对应方式，仅严格按照输入数据的数量一一列举数据表名称：
        idx_count = max(len(htypes), len(freq), len(asset_type))
        freq_padder = freq[0] if len(freq) == 1 else 'd'
        asset_padder = asset_type[0] if len(asset_type) == 1 else 'E'
        htypes = input_to_list(htypes, idx_count, padder=htypes[-1])
        freq = input_to_list(freq, idx_count, padder=freq_padder)
        asset_type = input_to_list(asset_type, idx_count, padder=asset_padder)
        dtype_idx = [(h, f, a) for h, f, a in zip(htypes, freq, asset_type)]

    elif method.lower() == 'permute':
        import itertools
        dtype_idx = list(itertools.product(htypes, freq, asset_type))

    else:  # for some unexpected cases
        raise KeyError(f'invalid method {method}')

    # 查找内容
    found_dtypes = dtype_map.reindex(index=dtype_idx)

    # 检查找到的数据中是否有NaN值，即未精确匹配到的值，确认是由于dtype/atype不对还是freq不对造成的
    # 如果是freq不对造成的，则需要抖动freq后重新匹配
    not_matched = found_dtypes.isna().all(axis=1)
    all_found = ~not_matched.any()  # 如果没有任何组合未找到，等价于全部组合都找到了
    # 在soft_freq模式下，进一步确认无法找到数据的原因，如果因为freq不匹配，则抖动freq后重新查找
    rematched_tables = {}
    if (not all_found) and soft_freq:
        # 有部分htype/freq/type组合没有找到结果，这部分index需要调整
        unmatched_index = found_dtypes.loc[not_matched].index
        unmatched_dtypes = [item[0] for item in unmatched_index]
        unmatched_freqs = [item[1] for item in unmatched_index]
        unmatched_atypes = [item[2] for item in unmatched_index]
        map_index = dtype_map.index
        all_dtypes = map_index.get_level_values(0)
        all_freqs = map_index.get_level_values(1)
        all_atypes = map_index.get_level_values(2)

        rematched_dtype_index = []
        for dt, fr, at in zip(unmatched_dtypes, unmatched_freqs, unmatched_atypes):
            try:
                rematched_dtype_loc = all_dtypes.get_loc(dt)
                rematched_atype_loc = all_atypes.get_loc(at)
            except KeyError:
                # 如果产生Exception，说明dt或at无法精确匹配
                # 此时应该保留全NaN输出
                continue
                # raise KeyError(f'dtype ({dt}) or asset_type ({at}) can not be found in dtype map')
            # 否则就是freq无法精确匹配，此时需要抖动freq
            '''
            原本使用下面的方法获取同时满足两个条件的freq的集合
            available_freq_list = all_freqs[rematched_dtype_loc & rematched_atype_loc]
            available_freq_list = list(set(available_freq_list))
            但是rematched_dtype_loc和rematched_atype_loc有时候类型不同，因此无法直接&
            例如，当dt = invest_income 时，rematched_dtype_loc返回值为一个数字209，
            而当at = E 时，rematched_atype_loc返回值为一个bool series
            两者无法直接进行 & 运算，因此会导致错误结果
            因此直接使用集合交集运算
            '''
            dtype_freq_list = set(all_freqs[rematched_dtype_loc])
            atype_freq_list = set(all_freqs[rematched_atype_loc])
            available_freq_list = list(dtype_freq_list.intersection(atype_freq_list))

            # 当无法找到available freq list时，跳过这一步
            if len(available_freq_list) == 0:
                continue

            dithered_freq = freq_dither(fr, available_freq_list)
            # 将抖动后生成的新的dtype ID保存下来
            rematched_dtype_index.append((dt, dithered_freq.lower(), at))

        # 抖动freq后生成的index中可能有重复项，需要去掉重复项
        rematched_dtype_index_unduplicated = list(set(rematched_dtype_index))
        # 通过去重后的index筛选出所需的dtypes
        rematched_dtypes = dtype_map.reindex(index=rematched_dtype_index_unduplicated)
        # 合并成组后生成dict
        group = rematched_dtypes.groupby(['table_name'])
        rematched_tables = group['column'].apply(list).to_dict()

    # 从found_dtypes中提取数据并整理为dict
    group = found_dtypes.groupby(['table_name'])
    matched_tables = group['column'].apply(list).to_dict()

    if soft_freq:
        # 将找到的dtypes与重新匹配的dtypes合并
        matched_tables.update(rematched_tables)
    return matched_tables


# noinspection PyTypeChecker
@lru_cache(maxsize=16)
def get_built_in_table_schema(table, with_remark=False, with_primary_keys=True):
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
        raise TypeError(f'table name should be a string, got {type(table)} instead')
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


@lru_cache(maxsize=1)
def get_dtype_map():
    """ 获取所有内置数据类型的清单

    Returns
    -------
    """
    dtype_map = pd.DataFrame(DATA_TABLE_MAP).T
    dtype_map.columns = DATA_TABLE_MAP_COLUMNS
    dtype_map.index.names = DATA_TABLE_MAP_INDEX_NAMES
    return dtype_map


@lru_cache(maxsize=1)
def get_table_map():
    """ 获取所有内置数据表的清单，to be deprecated

    Returns
    -------
    pd.DataFrame
    数据表清单
    """
    warnings.warn('get_table_map() is deprecated, use get_table_master() instead', DeprecationWarning)
    table_map = pd.DataFrame(TABLE_MASTERS).T
    table_map.columns = TABLE_MASTER_COLUMNS
    return table_map


@lru_cache(maxsize=1)
def get_table_master():
    """ 获取所有内置数据表的清单

    Returns
    -------
    table_masters: pd.DataFrame
    数据表清单, 包含以下字段:
    """
    table_master = pd.DataFrame(TABLE_MASTERS).T
    table_master.columns = TABLE_MASTER_COLUMNS
    return table_master


def find_history_data(s, match_description=False, fuzzy=False, freq=None, asset_type=None, match_threshold=0.85):
    """ 根据输入的字符串，查找或匹配历史数据类型,并且显示该历史数据的详细信息。支持模糊查找、支持通配符、支持通过英文字符或中文
    查找匹配的历史数据类型。

    Parameters
    ----------
    s: str
        一个字符串，用于查找或匹配历史数据类型
    match_description: bool, Default: False
        是否模糊匹配数据描述，如果给出的字符串中含有非Ascii字符，会自动转为True
         - False: 仅匹配数据名称
         - True:  同时匹配数据描述
    fuzzy: bool, Default: False
        是否模糊匹配数据名称，如果给出的字符串中含有非Ascii字符或通配符*/?，会自动转为True
         - False: 精确匹配数据名称
         - True:  模糊匹配数据名称或数据描述
    freq: str, Default: None
        数据频率，如果提供，则只匹配该频率的数据
        可以输入单个频率，也可以输入逗号分隔的多个频率
    asset_type: str, Default: None
        证券类型，如果提供，则只匹配该证券类型的数据
        可以输入单个证券类型，也可以输入逗号分隔的多个证券类型
    match_threshold: float, default 0.85
        匹配度阈值，匹配度超过该阈值的项目会被判断为匹配

    Returns
    -------
    data_id: list
        匹配到的数据类型的data_id，可以用于qt.get_history_data()下载数据

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.find_history_data('pe')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
               freq asset             table                            desc
    data_id
    initial_pe    d     E         new_share                  新股上市信息 - 发行市盈率
    pe            d   IDX   index_indicator                    指数技术指标 - 市盈率
    pe            d     E   stock_indicator  股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）
    pe_2          d     E  stock_indicator2                  股票技术指标 - 动态市盈率
    ========================================================================

    >>> qt.find_history_data('ep*')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
                  freq asset      table                 desc
    data_id
    eps_last_year    q     E    express  上市公司业绩快报 - 去年同期每股收益
    eps              q     E  financial    上市公司财务指标 - 基本每股收益
    ========================================================================

    >>> qt.find_history_data('每股收益')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
                    freq asset      table                 desc
    data_id
    basic_eps              q     E     income           上市公司利润表 - 基本每股收益
    diluted_eps            q     E     income           上市公司利润表 - 稀释每股收益
    express_diluted_eps    q     E    express     上市公司业绩快报 - 每股收益(摊薄)(元)
    yoy_eps                q     E    express    上市公司业绩快报 - 同比增长率:基本每股收益
    eps_last_year          q     E    express        上市公司业绩快报 - 去年同期每股收益
    eps                    q     E  financial          上市公司财务指标 - 基本每股收益
    dt_eps                 q     E  financial          上市公司财务指标 - 稀释每股收益
    diluted2_eps           q     E  financial        上市公司财务指标 - 期末摊薄每股收益
    q_eps                  q     E  financial       上市公司财务指标 - 每股收益(单季度)
    basic_eps_yoy          q     E  financial  上市公司财务指标 - 基本每股收益同比增长率(%)
    dt_eps_yoy             q     E  financial  上市公司财务指标 - 稀释每股收益同比增长率(%)
    ========================================================================

    Raises
    ------
    TypeError: 输入的s不是字符串，或者freq/asset_type不是字符串或列表
    """

    if not isinstance(s, str):
        raise TypeError(f'input should be a string, got {type(s)} instead.')
    # 判断输入是否ascii编码，如果是，匹配数据名称，否则，匹配数据描述
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        # is_ascii = False, 此时强制匹配description, 并且fuzzy匹配
        match_description = True
        fuzzy = True
    if match_description:
        fuzzy = True
    if ('?' in s) or ('*' in s):
        fuzzy = True  # 给出通配符时强制fuzzy匹配

    data_table_map = get_dtype_map()
    data_table_map['freq'] = data_table_map.index.get_level_values(level=1)
    data_table_map['asset_type'] = data_table_map.index.get_level_values(level=2)

    if freq is not None:
        if isinstance(freq, str):
            freq = str_to_list(freq)
        if not isinstance(freq, list):
            raise TypeError(f'freq should be a string or a list, got {type(freq)} instead')
        data_table_map = data_table_map.loc[data_table_map['freq'].isin(freq)]
    if asset_type is not None:
        if isinstance(asset_type, str):
            asset_type = str_to_list(asset_type)
        if not isinstance(asset_type, list):
            raise TypeError(f'asset_type should be a string or a list, got {type(asset_type)} instead')
        data_table_map = data_table_map.loc[data_table_map['asset_type'].isin(asset_type)]

    data_table_map['n_matched'] = 0  # name列的匹配度，模糊匹配的情况下，匹配度为0～1之间的数字
    data_table_map['d_matched'] = 0  # description列的匹配度，模糊匹配的情况下，匹配度为0～1之间的数字

    if (not fuzzy) and (not match_description):
        data_table_map['n_matched'] = data_table_map['column'] == s
        data_table_map['n_matched'] = data_table_map['n_matched'].astype('int')
    else:
        if match_description:
            where_to_look = ['column', 'description']
            match_how = [_lev_ratio, _partial_lev_ratio]
            result_columns = ['n_matched', 'd_matched']
        elif fuzzy:
            where_to_look = ['column']
            match_how = [_partial_lev_ratio]
            result_columns = ['n_matched']
        else:
            where_to_look = ['column']
            match_how = [_lev_ratio]
            result_columns = ['n_matched']

        for where, how, res in zip(where_to_look, match_how, result_columns):
            if ('?' in s) or ('*' in s):
                matched = _wildcard_match(s, data_table_map[where])
                match_values = [1 if item in matched else 0 for item in data_table_map[where]]
            else:
                match_values = list(map(how, [s] * len(data_table_map[where]), data_table_map[where]))
            data_table_map[res] = match_values

    data_table_map['matched'] = data_table_map['n_matched'] + data_table_map['d_matched']
    data_table_map = data_table_map.loc[data_table_map['matched'] >= match_threshold]
    data_table_map.drop(columns=['n_matched', 'd_matched', 'matched'], inplace=True)
    data_table_map.index = data_table_map.index.get_level_values(level=0)
    data_table_map.index.name = 'data_id'
    print(f'matched following history data, \n'
          f'use "qt.get_history_data()" to load these historical data by its data_id:\n'
          f'------------------------------------------------------------------------')
    print(
            data_table_map.to_string(
                    columns=['freq',
                             'asset_type',
                             'table_name',
                             'description'],
                    header=['freq',
                            'asset',
                            'table',
                            'desc'],
            )
    )
    print(f'========================================================================')
    return list(data_table_map.index)


def ensure_sys_table(table):
    """ 检察table是不是sys表

    Parameters
    ----------
    table:

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
        raise TypeError(f'table name should be a string, got {type(table)} instead.')
    try:
        table_usage = TABLE_MASTERS[table][2]
        if not table_usage == 'sys':
            raise TypeError(f'Table {table}<{table_usage}> is not subjected to sys use')
    except KeyError as e:
        raise KeyError(f'"{e}" is not a valid table name')
    except Exception as e:
        raise RuntimeError(f'{e}: An error occurred when checking table usage')
