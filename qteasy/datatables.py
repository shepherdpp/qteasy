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


AVAILABLE_DATA_FILE_TYPES = ['csv', 'hdf', 'hdf5', 'feather', 'fth']
AVAILABLE_CHANNELS = ['df', 'csv', 'excel', 'tushare']
ADJUSTABLE_PRICE_TYPES = ['open', 'high', 'low', 'close']
TABLE_USAGES = ['sys', 'cal', 'basics', 'data', 'adj', 'events', 'comp', 'report', 'mins', 'reference']

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
                            ?min - 分钟数据
                            d - 日数据
                            w - 周数据
                            m - 月数据
                            q - 季度数据

asset_type(key):            数据对应的金融资产类型:
                            E - 股票
                            IDX - 指数
                            FT - 期货
                            FD - 基金
                            OPT - 期权
                            THS - 同花顺指数
                            SW - 申万行业指数
                            
table_name:                 历史数据所在的表的名称

column:                     历史数据在表中的列名称

description:                历史数据的详细描述，可以用于列搜索
---------------------------------------------------------------------------------------------------------

2, TABLE_MASTER

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
                            'none'表示无频率

6, tushare:                 对应的tushare API函数名, 参见tsfuncs.py中的定义

7, fill_arg_name:           从tushare下载数据时的关键参数，使用该关键参数来分多次下载完整的数据
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

8, fill_arg_type:           关键参数的数据类型，可以为list、table_index、datetime、trade_date，含义分别为：
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

9, arg_rng:                 关键参数的取值范围，
                            -   如果数据类型为datetime或trade_date，是一个起始日期，表示取值范围从该日期到今日之间
                            -   如果数据类型为table_index，取值范围是一张表，如stock_basic，表示数据从stock_basic的
                                索引中取值
                            -   如果数据类型为list，则直接给出取值范围，如"SSE,SZSE"表示可以取值SSE以及SZSE。

10, arg_allowed_code_suffix:
                            table_index类型取值范围的限制值，限制只有特定后缀的证券代码才会被用作参数下载数据。
                            例如，取值"SH,SZ"表示只有以SH、SZ结尾的证券代码才会被用作参数从tushare下载数据。

11, arg_allow_start_end:    使用table_index类型参数时，是否同时允许传入开始结束日期作为参数。如果设置为"Y"，则会在使用
                            table_index中的代码作为参数下载数据时，同时传入开始和结束日期作为附加参数，否则仅传入代码

12, start_end_chunk_size:   传入开始结束日期作为附加参数时，是否分块下载。可以设置一个正整数或空字符串如"300"。如果设置了
                            一个正整数字符串，表示一个天数，并将开始结束日期之间的数据分块下载，每个块中数据的时间跨度不超
                            过这个天数。
                            例如，设置该参数为100，则每个分块内的时间跨度不超过100天
                    
13, akshare:                对应的akshare API函数名

14, ak_fill_arg_name:       从akshare下载数据时的关键参数，使用该关键参数来分多次下载完整的数据
                            与tushare的fill_arg_name相同
                            
15, ak_fill_arg_type:       与tushare的fill_arg_type相同, 用于akshare API

16, ak_arg_rng:             与tushare的arg_rng相同, 用于akshare API
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
    'schema',  # 1, 数据表schema
    'desc',  # 2, 数据表描述
    'table_usage',  # 3, 数据表用途
    'asset_type',  # 4, 资产类型
    'freq',  # 5, 数据频率
    'tushare',  # 6, 从tushare获取数据时使用的api名
    'fill_arg_name',  # 7, 从tushare获取数据时使用的api参数名
    'fill_arg_type',  # 8, 从tushare获取数据时使用的api参数类型
    'arg_rng',  # 9, 从tushare获取数据时使用的api参数取值范围
    'arg_allowed_code_suffix',  # 10, 从tushare获取数据时使用的api参数允许的股票代码后缀
    'arg_allow_start_end',  # 11, 从tushare获取数据时使用的api参数是否允许start_date和end_date
    'start_end_chunk_size',  # 12, 从tushare获取数据时使用的api参数start_date和end_date时的分段大小
    'akshare',   # 13, 从akshare获取数据时使用的api名
    'ak_fill_arg_name',   # 14, 从akshare获取数据时使用的api参数名
    'ak_fill_arg_type',   # 15, 从akshare获取数据时使用的api参数类型
    'ak_arg_rng',  # 16, 从eastmoney获取数据时使用的api参数取值范围
]
TABLE_MASTERS = {

    'sys_op_live_accounts':
        ['sys_op_live_accounts', '实盘运行基本信息主记录表', 'sys', '', '', '', '', '', '', '', '', '', '', '', '', ''],

    'sys_op_positions':
        ['sys_op_positions', '实盘运行持仓记录', 'sys', '', '', '', '', '', '', '', '', '', '', '', '', ''],

    'sys_op_trade_orders':
        ['sys_op_trade_orders', '实盘运行交易订单记录表', 'sys', '', '', '', '', '', '', '', '', '', '', '', '', ''],

    'sys_op_trade_results':
        ['sys_op_trade_results', '实盘运行交易结果记录表', 'sys', '', '', '', '', '', '', '', '', '', '', '', '', ''],

    'trade_calendar':
        ['trade_calendar', '交易日历', 'cal', 'none', 'none', 'trade_calendar', 'exchange', 'list',
         'SSE,SZSE,BSE,CFFEX,SHFE,CZCE,DCE,INE,XHKG', '', '', '', '', '', '', ''],

    'stock_basic':
        ['stock_basic', '股票基本信息', 'basics', 'E', 'none', 'stock_basic', 'exchange', 'list', 'SSE,SZSE,BSE', '',
         '',
         '', '', '', '', ''],

    'stock_names':
        ['name_changes', '股票名称变更', 'events', 'E', 'none', 'name_change', 'ts_code', 'table_index', 'stock_basic',
         '', 'Y', '', '', '', '', ''],

    'stock_company':
        ['stock_company', '上市公司基本信息', 'basics', 'E', 'none', 'stock_company', 'exchange', 'list',
         'SSE, SZSE, BSE',
         '', '', '', '', '', '', ''],

    'stk_managers':
        ['stk_managers', '上市公司管理层', 'events', 'E', 'd', 'stk_managers', 'ann_date', 'datetime', '19901211',
         '', '', '', '', '', '', ''],

    'new_share':
        ['new_share', 'IPO新股列表', 'events', 'E', 'd', 'new_share', 'none', 'none', 'none',
         '', 'Y', '200', '', '', '', ''],

    'money_flow':  # New, 个股资金流向!
        ['money_flow', '资金流向', 'data', 'E', 'd', 'moneyflow', 'trade_date', 'trade_date', '20100101', '', '', '',
         '', '', '', ''],

    'stock_limit':  # New, 涨跌停价格!
        ['stock_limit', '涨跌停价格', 'data', 'E,FD', 'd', 'stk_limit', 'trade_date', 'trade_date', '20100101', '', '', '',
         '', '', '', ''],

    'stock_suspend':  # New, 停复牌信息!
        ['stock_suspend', '停复牌信息', 'events', 'E', 'd', 'suspend_d', 'trade_date', 'trade_date', '20100101', '', '',
         '', '', '', '', ''],

    'HS_money_flow':  # New, 沪深股通资金流向!
        ['HS_money_flow', '沪深股通资金流向', 'reference', 'none', 'd', 'moneyflow_hsgt', 'trade_date', 'trade_date',
         '20100101', '', '', '', '', '', '', ''],

    'HS_top10_stock':  # New, 沪深股通十大成交股!
        ['HS_top10_stock', '沪深股通十大成交股东', 'events', 'E', 'd', 'hsgt_top10', 'trade_date', 'trade_date',
         '20100101', '', '', '', '', '', '', ''],

    'HK_top10_stock':  # New, 港股通十大成交股!
        ['HK_top10_stock', '港股通十大成交股东', 'events', 'E', 'd', 'ggt_top10', 'trade_date', 'trade_date',
         '20100101', '', '', '', '', '', '', ''],

    'index_basic':
        ['index_basic', '指数基本信息', 'basics', 'IDX', 'none', 'index_basic', 'market', 'list',
         'SSE,MSCI,CSI,SZSE,CICC,SW,OTH', '', '', '', '', '', '', ''],

    'fund_basic':
        ['fund_basic', '基金基本信息', 'basics', 'FD', 'none', 'fund_basic', 'market', 'list', 'E,O', '', '', '', '', '', '', ''],

    'future_basic':
        ['future_basic', '期货基本信息', 'basics', 'FT', 'none', 'future_basic', 'exchange', 'list',
         'CFFEX,DCE,CZCE,SHFE,INE', '', '', '', '', '', '', ''],

    'opt_basic':
        ['opt_basic', '期权基本信息', 'basics', 'OPT', 'none', 'options_basic', 'exchange', 'list',
         'SSE,SZSE,CFFEX,DCE,CZCE,SHFE', '', '', '', '', '', '', ''],

    'ths_index_basic':  # New, 同花顺指数基本信息
        ['ths_index_basic', '同花顺指数基本信息', 'basic', 'THS', 'none', 'ths_index', 'exchange', 'list',
         'A, HK, US', '', '', '', '', '', '', ''],

    'sw_industry_basic':  # New, 申万行业分类
        ['sw_industry_basic', '申万行业分类', 'basic', 'IDX', 'none', 'industry_sw', 'src', 'list', 'sw2014, sw2021',
         '', '', '', '', '', '', ''],

    'stock_1min':
        ['min_bars', '股票分钟K线行情', 'mins', 'E', '1min', 'mins1', 'ts_code', 'table_index', 'stock_basic', '', 'y',
         '30', '', '', '', ''],

    'stock_5min':
        ['min_bars', '股票5分钟K线行情', 'mins', 'E', '5min', 'mins5', 'ts_code', 'table_index', 'stock_basic', '', 'y',
         '90', '', '', '', ''],

    'stock_15min':
        ['min_bars', '股票15分钟K线行情', 'mins', 'E', '15min', 'mins15', 'ts_code', 'table_index', 'stock_basic', '',
         'y', '180', '', '', '', ''],

    'stock_30min':
        ['min_bars', '股票30分钟K线行情', 'mins', 'E', '30min', 'mins30', 'ts_code', 'table_index', 'stock_basic', '',
         'y', '360', '', '', '', ''],

    'stock_hourly':
        ['min_bars', '股票60分钟K线行情', 'mins', 'E', 'h', 'mins60', 'ts_code', 'table_index', 'stock_basic', '',
         'y', '360', '', '', '', ''],

    'stock_daily':
        ['bars', '股票日线行情', 'data', 'E', 'd', 'daily', 'trade_date', 'trade_date', '19901211', '', '', '', '', '', '', ''],

    'stock_weekly':
        ['bars', '股票周线行情', 'data', 'E', 'w', 'weekly', 'trade_date', 'trade_date', '19901221', '', '', '', '', '', '', ''],

    'stock_monthly':
        ['bars', '股票月线行情', 'data', 'E', 'm', 'monthly', 'trade_date', 'trade_date', '19901211', '', '', '', '', '', '', ''],

    'index_1min':
        ['min_bars', '指数分钟K线行情', 'mins', 'IDX', '1min', 'mins1', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ',
         'y', '30', '', '', '', ''],

    'index_5min':
        ['min_bars', '指数5分钟K线行情', 'mins', 'IDX', '5min', 'mins5', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ',
         'y', '90', '', '', '', ''],

    'index_15min':
        ['min_bars', '指数15分钟K线行情', 'mins', 'IDX', '15min', 'mins15', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ', 'y', '180', '', '', '', ''],

    'index_30min':
        ['min_bars', '指数30分钟K线行情', 'mins', 'IDX', '30min', 'mins30', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ', 'y', '360', '', '', '', ''],

    'index_hourly':
        ['min_bars', '指数60分钟K线行情', 'mins', 'IDX', 'h', 'mins60', 'ts_code', 'table_index', 'index_basic',
         'SH,SZ', 'y', '360', '', '', '', ''],

    'index_daily':
        ['bars', '指数日线行情', 'data', 'IDX', 'd', 'index_daily', 'ts_code', 'table_index', 'index_basic',
         'SH,CSI,SZ', 'y', '', '', '', '', ''],

    'index_weekly':
        ['bars', '指数周线行情', 'data', 'IDX', 'w', 'index_weekly', 'trade_date', 'trade_date', '19910705', '', '',
         '', '', '', '', ''],

    'index_monthly':
        ['bars', '指数月度行情', 'data', 'IDX', 'm', 'index_monthly', 'trade_date', 'trade_date', '19910731', '', '',
         '', '', '', '', ''],

    'ths_index_daily':  # New, 同花顺行业指数日线行情!
        ['ths_index_daily', '同花顺行业指数日线行情', 'data', 'THS', 'd', 'ths_daily', 'trade_date', 'trade_date',
         '20100101', '', '', '', '', '', '', ''],

    'ths_index_weight':  # New, 同花顺行业指数成分股权重!
        ['ths_index_weight', '同花顺行业指数成分股权重', 'comp', 'THS', 'd', 'ths_member', 'ts_code', 'table_index',
         'ths_index_basic', '', '', '', '', '', '', ''],

    'ci_index_daily':  # New, 中信指数日线行情!
        ['ci_index_daily', '中证指数日线行情', 'reference', 'none', 'd', 'ci_daily', 'trade_date', 'trade_date',
         '19901211', '', '', '', '', '', '', ''],

    'sw_index_daily':  # New, 申万指数日线行情!
        ['sw_index_daily', '申万指数日线行情', 'reference', 'none', 'd', 'sw_daily', 'trade_date', 'trade_date',
         '19901211', '', '', '', '', '', '', ''],

    'global_index_daily':  # New, 全球指数日线行情!
        ['global_index_daily', '全球指数日线行情', 'reference', 'none', 'd', 'index_global', 'trade_date', 'trade_date',
         '19901211', '', '', '', '', '', '', ''],

    'fund_1min':
        ['min_bars', '场内基金分钟K线行情', 'mins', 'FD', '1min', 'mins1', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ',
         'y', '30', '', '', '', ''],

    'fund_5min':
        ['min_bars', '场内基金5分钟K线行情', 'mins', 'FD', '5min', 'mins5', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ',
         'y', '90', '', '', '', ''],

    'fund_15min':
        ['min_bars', '场内基金15分钟K线行情', 'mins', 'FD', '15min', 'mins15', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ', 'y', '180', '', '', '', ''],

    'fund_30min':
        ['min_bars', '场内基金30分钟K线行情', 'mins', 'FD', '30min', 'mins30', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ', 'y', '360', '', '', '', ''],

    'fund_hourly':
        ['min_bars', '场内基金60分钟K线行情', 'mins', 'FD', 'h', 'mins60', 'ts_code', 'table_index', 'fund_basic',
         'SH,SZ', 'y', '360', '', '', '', ''],

    'fund_daily':
        ['bars', '场内基金每日行情', 'data', 'FD', 'd', 'fund_daily', 'trade_date', 'trade_date', '19980417', '', '',
         '', '', '', '', ''],

    'fund_nav':
        ['fund_nav', '场外基金每日净值', 'data', 'FD', 'd', 'fund_net_value', 'nav_date', 'datetime', '20000107', '',
         '', '', '', '', '', ''],

    'fund_share':
        ['fund_share', '基金份额', 'events', 'FD', 'none', 'fund_share', 'ts_code', 'table_index', 'fund_basic', '', '',
         '', '', '', '', ''],

    'fund_manager':
        ['fund_manager', '基金经理', 'events', 'FD', 'none', 'fund_manager', 'ts_code', 'table_index', 'fund_basic',
         'OF, SZ, SH', '', '', '', '', '', ''],

    'future_mapping':  # New, 期货合约映射表!
        ['future_mapping', '期货合约映射表', 'data', 'FT', 'none', 'fut_mapping', 'trade_date', 'trade_date', '19901219',
         '', '', '', '', '', '', ''],

    'future_1min':
        ['future_mins', '期货分钟K线行情', 'mins', 'FT', '1min', 'ft_mins1', 'ts_code', 'table_index', 'future_basic',
         '', 'y', '30', '', '', '', ''],

    'future_5min':
        ['future_mins', '期货5分钟K线行情', 'mins', 'FT', '5min', 'ft_mins5', 'ts_code', 'table_index', 'future_basic',
         '', 'y', '90', '', '', '', ''],

    'future_15min':
        ['future_mins', '期货15分钟K线行情', 'mins', 'FT', '15min', 'ft_mins15', 'ts_code', 'table_index',
         'future_basic',
         '', 'y', '180', '', '', '', ''],

    'future_30min':
        ['future_mins', '期货30分钟K线行情', 'mins', 'FT', '30min', 'ft_mins30', 'ts_code', 'table_index',
         'future_basic',
         '', 'y', '360', '', '', '', ''],

    'future_hourly':
        ['future_mins', '期货60分钟K线行情', 'mins', 'FT', 'h', 'ft_mins60', 'ts_code', 'table_index', 'future_basic',
         '', 'y', '360', '', '', '', ''],

    'future_daily':
        ['future_daily', '期货每日行情', 'data', 'FT', 'd', 'future_daily', 'trade_date', 'trade_date', '19950417', '',
         '', '', '', '', '', ''],

    'future_weekly':  # New, 期货周线行情!
        ['future_daily', '期货周线行情', 'data', 'FT', 'w', 'future_weekly', 'trade_date', 'trade_date', '19950417', '',
         '', '', '', '', '', ''],

    'future_monthly':  # New, 期货月线行情!
        ['future_daily', '期货月线行情', 'data', 'FT', 'm', 'future_monthly', 'trade_date', 'trade_date', '19950417', '',
         '', '', '', '', '', ''],

    'options_1min':
        ['min_bars', '期权分钟K线行情', 'mins', 'OPT', '1min', 'mins1', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '30', '', '', '', ''],

    'options_5min':
        ['min_bars', '期权5分钟K线行情', 'mins', 'OPT', '5min', 'mins5', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '90', '', '', '', ''],

    'options_15min':
        ['min_bars', '期权15分钟K线行情', 'mins', 'OPT', '15min', 'mins15', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '180', '', '', '', ''],

    'options_30min':
        ['min_bars', '期权30分钟K线行情', 'mins', 'OPT', '30min', 'mins30', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '360', '', '', '', ''],

    'options_hourly':
        ['min_bars', '期权60分钟K线行情', 'mins', 'OPT', 'h', 'mins60', 'ts_code', 'table_index', 'opt_basic',
         '', 'y', '360', '', '', '', ''],

    'options_daily':
        ['options_daily', '期权每日行情', 'data', 'OPT', 'd', 'options_daily', 'trade_date', 'trade_date', '20150209', '',
         '', '', '', '', '', ''],

    'stock_adj_factor':
        ['adj_factors', '股票价格复权系数', 'adj', 'E', 'd', 'adj_factors', 'trade_date', 'trade_date', '19901219', '',
         '', '', '', '', '', ''],

    'fund_adj_factor':
        ['adj_factors', '基金价格复权系数', 'adj', 'FD', 'd', 'fund_adj', 'trade_date', 'trade_date', '19980407', '',
         '',
         '', '', '', '', ''],

    'stock_indicator':
        ['stock_indicator', '股票技术指标', 'data', 'E', 'd', 'daily_basic', 'trade_date', 'trade_date', '19990101', '',
         '', '', '', '', '', ''],

    'stock_indicator2':
        ['stock_indicator2', '股票技术指标备用表', 'data', 'E', 'd', 'daily_basic2', 'trade_date', 'trade_date',
         '19990101', '', '', '', '', '', '', ''],

    'index_indicator':
        ['index_indicator', '指数关键指标', 'data', 'IDX', 'd', 'index_daily_basic', 'trade_date', 'trade_date',
         '20040102', '', '', '', '', '', '', ''],

    'index_weight':
        ['index_weight', '指数成分', 'comp', 'IDX', 'd', 'composite', 'trade_date', 'datetime', '20050408', '', '', '',
         '', '', '', ''],

    'income':
        ['income', '上市公司利润表', 'report', 'E', 'q', 'income', 'ts_code', 'table_index', 'stock_basic', '', 'Y',
         '', '', '', '', ''],

    'balance':
        ['balance', '上市公司资产负债表', 'report', 'E', 'q', 'balance', 'ts_code', 'table_index', 'stock_basic', '',
         'Y',
         '', '', '', '', ''],

    'cashflow':
        ['cashflow', '上市公司现金流量表', 'report', 'E', 'q', 'cashflow', 'ts_code', 'table_index', 'stock_basic', '',
         'Y', '', '', '', '', ''],

    'financial':
        ['financial', '上市公司财务指标', 'report', 'E', 'q', 'indicators', 'ts_code', 'table_index', 'stock_basic', '',
         'Y', '', '', '', '', ''],

    'forecast':
        ['forecast', '上市公司财报预测', 'report', 'E', 'q', 'forecast', 'ts_code', 'table_index', 'stock_basic', '',
         'Y',
         '', '', '', '', ''],

    'express':
        ['express', '上市公司财报快报', 'report', 'E', 'q', 'express', 'ts_code', 'table_index', 'stock_basic', '', 'Y',
         '', '', '', '', ''],

    'dividend':  # New, 分红送股!
        ['dividend', '分红送股', 'events', 'E', 'd', 'dividend', 'ts_code', 'table_index', 'stock_basic', '', '', '',
         '', '', '', ''],

    'top_list':  # New, 龙虎榜交易明细!
        ['top_list', '龙虎榜交易明细', 'events', 'E', 'd', 'top_list', 'trade_date', 'trade_date', '20050101', '', '', '',
         '', '', '', ''],

    'top_inst':  # New, 龙虎榜机构交易明细!
        ['top_inst', '龙虎榜机构交易明细', 'events', 'E', 'd', 'top_inst', 'trade_date', 'trade_date', '19901211', '', '', '',
         '', '', '', ''],

    'sw_industry_detail':  # New, 申万行业分类明细(成分股)!
        ['sw_industry_detail', '申万行业分类明细', 'comp', 'IDX', 'none', 'index_member_all', 'ts_code', 'table_index',
         'stock_basic', '', '', '', '', '', '', ''],

    'block_trade':  # New, 大宗交易!
        ['block_trade', '大宗交易', 'events', 'E', 'd', 'block_trade', 'trade_date', 'trade_date', '20100101', '', '', '',
         '', '', '', ''],

    'stock_holder_trade':  # New, 股东交易（股东增减持）!
        ['stock_holder_trade', '股东交易', 'events', 'E', 'd', 'stk_holdertrade', 'trade_date', 'trade_date', '20100101',
         '', '', '', '', '', '', ''],

    'margin':  # New, 融资融券交易概况!
        ['margin', '融资融券交易概况', 'reference', 'none', 'd', 'margin', 'exchange_id', 'list', 'SSE,SZSE,BSE', '', '',
         '', '', '', '', ''],

    'margin_detail':  # New, 融资融券交易明！
        ['margin_detail', '融资融券交易明细', 'events', 'E', 'd', 'margin_detail', 'trade_date', 'trade_date', '20190910',
         '', '', '', '', '', '', ''],

    'shibor':
        ['shibor', '上海银行间行业拆放利率(SHIBOR)', 'reference', 'none', 'd', 'shibor', 'date', 'datetime', '20000101',
         '',
         '', '', '', '', '', ''],

    'libor':
        ['libor', '伦敦银行间行业拆放利率(LIBOR)', 'reference', 'none', 'd', 'libor', 'date', 'datetime', '20000101', '',
         '', '', '', '', '', ''],

    'hibor':
        ['hibor', '香港银行间行业拆放利率(HIBOR)', 'reference', 'none', 'd', 'hibor', 'date', 'datetime', '20000101', '',
         '', '', '', '', '', ''],

    'wz_index':  # New, 温州民间借贷指数!
        ['wz_index', '温州民间借贷指数', 'reference', 'none', 'd', 'wz_index', 'date', 'datetime', '20121207', '', '', '',
         '', '', '', ''],

    'gz_index':  # New, 广州民间借贷指数!
        ['gz_index', '广州民间借贷指数', 'reference', 'none', 'd', 'gz_index', 'date', 'datetime', '19901211', '', '', '',
         '', '', '', ''],

    'cn_gdp':  # New, 国内生产总值季度数据!
        ['cn_gdp', '国内生产总值年度数据', 'reference', 'none', 'q', 'cn_gdp', '', '', '',
         '', '', '', '', '', '', ''],

    'cn_cpi':  # New, 居民消费价格指数月度数据!
        ['cn_cpi', '居民消费价格指数月度数据', 'reference', 'none', 'm', 'cn_cpi', '', '', '', '',
         '', '', '', '', '', ''],

    'cn_ppi':  # New, 工业品出厂价格指数月度数据!
        ['cn_ppi', '工业品出厂价格指数月度数据', 'reference', 'none', 'm', 'cn_ppi', '', '', '', '',
         '', '', '', '', '', ''],

    'cn_money':  # New, 中国货币供应量!
        ['cn_money', '中国货币供应量', 'reference', 'none', 'm', 'cn_m', '', '', '', '',
         '', '', '', '', '', ''],

    'cn_sf':  # New, 中国社会融资规模月度数据!
        ['cn_sf', '中国社会融资规模月度数据', 'reference', 'none', 'm', 'sf_month', '', '', '',
         '', '', '', '', '', '', ''],

    'cn_pmi':  # New, 采购经理人指数月度数据!
        ['cn_pmi', '采购经理人指数月度数据', 'reference', 'none', 'm', 'cn_pmi', '', '', '',
         '', '', '', '', '', '', ''],

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
        {'columns':    ['exchange', 'cal_date', 'is_open', 'pretrade_date'],
         'dtypes':     ['varchar(9)', 'date', 'tinyint', 'date'],
         'remarks':    ['交易所', '日期', '是否交易', '上一交易日'],
         'prime_keys': [0, 1]
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

    'name_changes':  # 股票名称变更表
        {'columns':    ['ts_code', 'start_date', 'name', 'end_date', 'ann_date', 'change_reason'],
         'dtypes':     ['varchar(9)', 'date', 'varchar(8)', 'date', 'date', 'varchar(10)'],
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

    'stk_managers':  # 上市公司管理层表
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
         'prime_keys':  [0, 1]
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
         'remarks':     ["TS代码", "交易日期", "小单买入量（手）", "小单买入金额（万元）", "小单卖出量（手）", "小单卖出金额（万元）",
                         "中单买入量（手）", "中单买入金额（万元）", "中单卖出量（手）", "中单卖出金额（万元）", "大单买入量（手）", "大单买入金额（万元）",
                         "大单卖出量（手）", "大单卖出金额（万元）", "特大单买入量（手）", "特大单买入金额（万元）", "特大单卖出量（手）",
                         "特大单卖出金额（万元）", "净流入量（手）", "净流入额（万元）"],
         'prime_keys':  [0, 1]
         },

    'stock_limit':  # New, 涨跌停价格!
        {'columns':     ["trade_date", "ts_code", "pre_close", "up_limit", "down_limit"],
         'dtypes':      ["date", "varchar(10)", "float", "float", "float"],
         'remarks':     ["交易日期", "TS股票代码", "昨日收盘价", "涨停价", "跌停价"],
         'prime_keys':  [0, 1]
         },

    'stock_suspend':  # New, 停复牌信息!
        {'columns':     ["ts_code", "trade_date", "suspend_timing", "suspend_type"],
         'dtypes':      ["varchar(10)", "date", "varchar(15)", "varchar(2)"],
         'remarks':     ["TS代码", "停复牌日期", "日内停牌时间段", "停复牌类型：S-停牌，R-复牌"],
         'prime_keys':  [0, 1]
         },

    'HS_money_flow':  # New, 沪深股通资金流向!
        {'columns':     ["trade_date", "ggt_ss", "ggt_sz", "hgt", "sgt", "north_money",
                         "south_money"],
         'dtypes':      ["date", "float", "float", "float", "float", "float",
                         "float"],
         'remarks':     ["交易日期", "港股通（上海）", "港股通（深圳）", "沪股通（百万元）", "深股通（百万元）", "北向资金（百万元）",
                         "南向资金（百万元）"],
         'prime_keys':  [0]
         },

    'HS_top10_stock':  # New, 沪深股通十大成交股!
        {'columns':     ["trade_date", "ts_code", "name", "close", "change", "rank", "market_type", "amount",
                         "net_amount", "buy", "sell"],
         'dtypes':      ["date", "varchar(10)", "varchar(10)", "float", "float", "int", "str", "float",
                         "float", "float", "float"],
         'remarks':     ["交易日期", "股票代码", "股票名称", "收盘价", "涨跌额", "资金排名", "市场类型（1：沪市 3：深市）", "成交金额（元）",
                         "净成交金额（元）", "买入金额（元）", "卖出金额（元）"],
         'prime_keys':  [0, 1]
         },

    'HK_top10_stock':  # New, 港股通十大成交股!
        {'columns':     ["trade_date", "ts_code", "name", "close", "p_change", "rank", "market_type",
                         "amount", "net_amount", "sh_amount", "sh_net_amount", "sh_buy", "sh_sell",
                         "sz_amount", "sz_net_amount", "sz_buy", "sz_sell"],
         'dtypes':      ["date", "varchar(10)", "varchar(10)", "float", "float", "varchar(10)", "varchar(4)",
                         "float", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float"],
         'remarks':     ["交易日期", "股票代码", "股票名称", "收盘价", "涨跌幅", "资金排名", "市场类型 2：港股通（沪） 4：港股通（深）",
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
         'dtypes':      ["varchar(14)", "varchar(10)", "varchar(6)", "varchar(6)", "varchar(10)",
                         "varchar(4)", "varchar(4)"],
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

    'adj_factors':  # 复权因子表
        {'columns':    ['ts_code', 'trade_date', 'adj_factor'],
         'dtypes':     ['varchar(9)', 'date', 'double'],
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
        {'columns':     ["ts_code", "code", "name", "weight", "in_date", "out_date", "is_new"],
         'dtypes':      ["str", "str", "str", "float", "str", "str", "str"],
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
         'remarks':    ['TS代码', '净值日期', '公告日期', '单位净值', '累计净值', '累计分红', '资产净值',
                        '合计资产净值', '复权单位净值', '更新标记'],
         'prime_keys': [0, 1]
         },

    'fund_share':  # 基金份额表
        {'columns':    ['ts_code', 'trade_date', 'fd_share'],
         'dtypes':     ['varchar(20)', 'date', 'float'],
         'remarks':    ['证券代码', '变动日期，格式YYYYMMDD', '基金份额(万)'],
         'prime_keys': [0, 1]
         },

    'fund_manager':  # 基金经理表
        {'columns':    ['ts_code', 'ann_date', 'name', 'gender', 'birth_year', 'edu', 'nationality',
                        'begin_date', 'end_date', 'resume'],
         'dtypes':     ['varchar(20)', 'date', 'varchar(20)', 'varchar(2)', 'varchar(12)',
                        'varchar(30)', 'varchar(4)', 'date', 'date', 'text'],
         'remarks':    ['证券代码', '公告日期', '基金经理姓名', '性别', '出生年份', '学历', '国籍', '任职日期',
                        '离任日期', '简历'],
         'prime_keys': [0, 1]
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
        {'columns':     ["ts_code", "end_date", "ann_date", "div_proc", "stk_div", "stk_bo_rate", "stk_co_rate",
                         "cash_div", "cash_div_tax", "record_date", "ex_date", "pay_date", "div_listdate",
                         "imp_ann_date", "base_date", "base_share"],
         'dtypes':      ["varchar(14)", "date", "date", "varchar(10)", "float", "float", "float",
                         "float", "float", "date", "date", "date", "date",
                         "date", "date", "float"],
         'remarks':     ["TS代码", "分红年度", "预案公告日", "实施进度", "每股送转", "每股送股比例", "每股转增比例",
                         "每股分红（税后）", "每股分红（税前）", "股权登记日", "除权除息日", "派息日", "红股上市日",
                         "实施公告日", "基准日", "基准股本（万）"],
         'prime_keys':  [0, 2]
         },

    'top_list':  # New, 龙虎榜交易明细!
        {'columns':     ["trade_date", "ts_code", "name", "close", "pct_change", "turnover_rate", "amount", "l_sell",
                         "l_buy", "l_amount", "net_amount", "net_rate", "amount_rate",
                         "float_values", "reason"],
         'dtypes':      ["date", "varchar(14)", "varchar(10)", "float", "float", "float", "float", "float",
                         "float", "float", "float", "float", "float",
                         "float", "text"],
         'remarks':     ["交易日期", "TS代码", "名称", "收盘价", "涨跌幅", "换手率", "总成交额", "龙虎榜卖出额",
                         "龙虎榜买入额", "龙虎榜成交额", "龙虎榜净买入额", "龙虎榜净买额占比", "龙虎榜成交额占比",
                         "当日流通市值", "上榜理由"],
         'prime_keys':  [0, 1]
         },

    'top_inst':  # New, 龙虎榜机构交易明细!
        {'columns':     ["trade_date", "ts_code", "exalter", "side", "buy",
                         "buy_rate", "sell", "sell_rate", "net_buy", "reason"],
         'dtypes':      ["date", "varchar(14)", "text", "varchar(2)", "float",
                         "float", "float", "float", "float", "text"],
         'remarks':     ["交易日期", "TS代码", "营业部名称", "买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名",
                         "买入额（元）", "买入占总成交比例", "卖出额（元）", "卖出占总成交比例", "净成交额（元）", "上榜理由"],
         'prime_keys':  [0, 1]
         },

    'sw_industry_detail':  # New, 申万行业分类明细(成分股)!
        {'columns':     ["l1_code", "l1_name", "l2_code", "l2_name", "l3_code", "l3_name",
                         "ts_code", "name", "in_date", "out_date", "is_new"],
         'dtypes':      ["varchar(14)", "varchar(10)", "varchar(14)", "varchar(10)", "varchar(14)", "varchar(10)",
                         "varchar(14)", "varchar(14)", "date", "date", "varchar(2)"],
         'remarks':     ["一级行业代码", "一级行业名称", "二级行业代码", "二级行业名称", "三级行业代码", "三级行业名称",
                         "成分股票代码", "成分股票名称", "纳入日期", "剔除日期", "是否最新Y是N否"],
         'prime_keys':  [0]
         },

    'block_trade':  # New, 大宗交易!
        {'columns':     ["ts_code", "trade_date", "price", "vol", "amount", "buyer", "seller"],
         'dtypes':      ["varchar(14)", "date", "float", "float", "float", "text", "text"],
         'remarks':     ["TS代码", "交易日历", "成交价", "成交量（万股）", "成交金额", "买方营业部", "卖方营业部"],
         'prime_keys':  [0, 1]
         },

    'stock_holder_trade':  # New, 股东交易（股东增减持）!
        {'columns':     ["ts_code", "ann_date", "holder_name", "holder_type", "in_de", "change_vol",
                         "change_ratio", "after_share", "after_ratio", "avg_price", "total_share", "begin_date",
                         "close_date"],
         'dtypes':      ["varchar(14)", "date", "text", "varchar(2)", "varchar(4)", "float",
                         "float", "float", "float", "float", "float", "date",
                         "date"],
         'remarks':     ["TS代码", "公告日期", "股东名称", "股东类型G高管P个人C公司", "类型IN增持DE减持", "变动数量",
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
        {'columns':     ["trade_date", "ts_code", "rzye", "rqye", "rzmre", "rqyl",
                         "rzche", "rqchl", "rqmcl", "rzrqye"],
         'dtypes':      ["date", "varchar(14)", "float", "float", "float", "float",
                         "float", "float", "float", "float"],
         'remarks':     ["交易日期", "TS股票代码", "融资余额(元)", "融券余额(元)", "融资买入额(元)", "融券余量（股）",
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
         'dtypes':      ["date", "float", "float", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["季度", "GDP累计值（亿元）", "当季同比增速（%）", "第一产业累计值（亿元）", "第一产业同比增速（%）",
                         "第二产业累计值（亿元）", "第二产业同比增速（%）", "第三产业累计值（亿元）", "第三产业同比增速（%）"],
         'prime_keys':  [0]
         },

    'cn_cpi':  # New, 居民消费价格指数月度数据!
        {'columns':     ["month", "nt_val", "nt_yoy", "nt_mom", "nt_accu", "town_val", "town_yoy",
                         "town_mom", "town_accu", "cnt_val", "cnt_yoy", "cnt_mom", "cnt_accu"],
         'dtypes':      ["date", "float", "float", "float", "float", "float", "float",
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
         'dtypes':      ["date", "float", "float", "float", "float", "float",
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
         'dtypes':      ["date", "float", "float", "float", "float", "float", "float", "float", "float", "float"],
         'remarks':     ["月份YYYYMM", "M0（亿元）", "M0同比（%）", "M0环比（%）", "M1（亿元）", "M1同比（%）", "M1环比（%）",
                         "M2（亿元）", "M2同比（%）", "M2环比（%）"],
         'prime_keys':  [0]
         },

    'cn_sf':  # New, 中国社会融资规模月度数据!
        {'columns':     ["month", "inc_month", "inc_cumval", "stk_endval"],
         'dtypes':      ["date", "float", "float", "float"],
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
         'dtypes':      ["date", "float", "float", "float", "float", "float", "float", "float", "float", "float",
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


class DataConflictWarning(Warning):
    """ Warning Type: Data conflict detected"""
    pass


class MissingDataWarning(Warning):
    """ Warning Type: Local Data Missing"""
    pass

