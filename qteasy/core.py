# coding=utf-8
# ======================================
# File:     core.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-16
# Desc:
#   Core functions and Classes of qteasy.
# ======================================
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from warnings import warn
from typing import Optional, Union, Iterable

import qteasy
from qteasy.configure import configure
from qteasy.qt_operator import Operator
from qteasy.database import DataSource

from qteasy.datatypes import (
    DataType, infer_data_types,
)

from qteasy.history import (
    get_history_panel,
)

from qteasy.utilfuncs import (
    str_to_list,
    match_ts_code,
    AVAILABLE_ASSET_TYPES,
    _partial_lev_ratio,
    TIME_FREQ_STRINGS,
    TIME_FREQ_LEVELS,
    parse_freq_string,
)

from qteasy._arg_validators import (
    QT_CONFIG,
    ConfigDict,
)


def filter_stocks(date: str = 'today', **kwargs) -> pd.DataFrame:
    """根据输入的参数筛选股票，并返回一个包含股票代码和相关信息的DataFrame

    Parameters
    ----------
    date: date-like str
        筛选股票的上市日期，在该日期以后上市的股票将会被剔除：
    kwargs: str or list of str
        可以通过以下参数筛选股票, 可以同时输入多个筛选条件，只有符合要求的股票才会被筛选出来
        - index:      根据指数筛选，不含在指定的指数内的股票将会被剔除
        - industry:   公司所处行业，只有列举出来的行业会被选中
        - area:       公司所处省份，只有列举出来的省份的股票才会被选中
        - market:     市场，分为主板、创业板等
        - exchange:   交易所，包括上海证券交易所和深圳股票交易所

    Returns
    -------
    DataFrame: 筛选出来的股票的基本信息

    Examples
    --------
    >>> # 筛选出2019年1月1日以后的上证300指数成分股
    >>> filter_stocks(date='2019-01-01', index='000300.SH')
           symbol   name area industry market  list_date exchange
    ts_code
    000001.SZ  000001   平安银行   深圳       银行     主板 1991-04-03     SZSE
    000002.SZ  000002    万科A   深圳     全国地产     主板 1991-01-29     SZSE
    000063.SZ  000063   中兴通讯   深圳     通信设备     主板 1997-11-18     SZSE
    000069.SZ  000069   华侨城A   深圳     全国地产     主板 1997-09-10     SZSE
    000100.SZ  000100  TCL科技   广东      元器件     主板 2004-01-30     SZSE
               ...    ...  ...      ...    ...        ...      ...
    600732.SH  600732   爱旭股份   上海     电气设备     主板 1996-08-16      SSE
    600754.SH  600754   锦江酒店   上海     酒店餐饮     主板 1996-10-11      SSE
    600875.SH  600875   东方电气   四川     电气设备     主板 1995-10-10      SSE
    601699.SH  601699   潞安环能   山西     煤炭开采     主板 2006-09-22      SSE
    688223.SH  688223   晶科能源   江西     电气设备    科创板 2022-01-26      SSE
    [440 rows x 7 columns]

    >>> # 筛选出2019年1月1日以后上市的上海银行业的股票
    >>> filter_stocks(date='2019-01-01', industry='银行', area='上海')
               name area industry market  list_date exchange
    ts_code
    600000.SH  浦发银行   上海       银行     主板 1999-11-10      SSE
    601229.SH  上海银行   上海       银行     主板 2016-11-16      SSE
    601328.SH  交通银行   上海       银行     主板 2007-05-15      SSE
    """
    from qteasy import QT_DATA_SOURCE
    try:
        date = pd.to_datetime(date)
    except:
        date = pd.to_datetime('today')
    # validate all input args:
    if not all(arg.lower() in ['index', 'industry', 'area', 'market', 'exchange'] for arg in kwargs.keys()):
        raise KeyError()
    if not all(isinstance(val, (str, list)) for val in kwargs.values()):
        raise KeyError()

    ds = QT_DATA_SOURCE
    # ts_code是dataframe的index
    share_basics = ds.read_table_data('stock_basic')
    if not share_basics.empty:
        share_basics = share_basics[['symbol', 'name', 'area', 'industry',
                                     'market', 'list_date', 'exchange']]
    else:
        raise ValueError('No stock basic data found, please download stock basic data, call '
                         '"qt.refill_data_source(tables="stock_basic")"')
    if share_basics is None or share_basics.empty:
        return pd.DataFrame()
    share_basics['list_date'] = pd.to_datetime(share_basics.list_date)
    none_matched = dict()
    # 找出targets中无法精确匹配的值，加入none_matched字典，随后尝试模糊匹配并打印模糊模糊匹配信息
    # print('looking for none matching arguments')
    for column, targets in kwargs.items():
        if column == 'index':
            continue
        if isinstance(targets, str):
            targets = str_to_list(targets)
            kwargs[column] = targets
        all_column_values = share_basics[column].unique().tolist()
        target_not_matched = [item for item in targets if item not in all_column_values]
        if len(target_not_matched) > 0:
            kwargs[column] = list(set(targets) - set(target_not_matched))
            match_dict = {}
            for t in target_not_matched:
                similarities = []
                for s in all_column_values:
                    if not isinstance(s, str):
                        similarities.append(0.0)
                        continue
                    try:
                        similarities.append(_partial_lev_ratio(s, t))
                    except Exception as e:
                        print(f'{e}, error during matching "{t}" and "{s}"')
                        raise e
                sim_array = np.array(similarities)
                best_matched = [all_column_values[i] for i in
                                np.where(sim_array >= 0.5)[0]
                                if
                                isinstance(all_column_values[i], str)]
                match_dict[t] = best_matched
                best_matched_str = '\" or \"'.join(best_matched)
                print(f'{t} will be excluded because an exact match is not found in "{column}", did you mean\n'
                      f'"{best_matched_str}"?')
            none_matched[column] = match_dict
        # 从清单中将none_matched移除
    for column, targets in kwargs.items():
        if column == 'index':
            # 查找date到今天之间的所有成分股, 如果date为today，则将date前推一个月
            end_date = pd.to_datetime('today')
            start_date = date - pd.Timedelta(50, 'd')
            index_comp = ds.read_table_data('index_weight',
                                            shares=targets,
                                            start=start_date.strftime("%Y%m%d"),
                                            end=end_date.strftime('%Y%m%d'))
            if index_comp.empty:
                return index_comp
            # share_basics.loc[a_list] is deprecated since pandas 1.0.0
            # return share_basics.loc[index_comp.index.get_level_values('con_code').unique().tolist()]
            return share_basics.reindex(index=index_comp.index.get_level_values('con_code').unique().tolist())
        if isinstance(targets, str):
            targets = str_to_list(targets)
        if len(targets) == 0:
            continue
        if not all(isinstance(target, str) for target in targets):
            raise KeyError(f'the list should contain only strings')
        share_basics = share_basics.loc[share_basics[column].isin(targets)]
    share_basics = share_basics.loc[share_basics.list_date <= date]
    if not share_basics.empty:
        return share_basics[['name', 'area', 'industry', 'market', 'list_date', 'exchange']]
    else:
        return share_basics


def filter_stock_codes(date: str = 'today', **kwargs) -> list:
    """根据输入的参数调用filter_stocks筛选股票，并返回股票代码的清单

    Parameters
    ----------
    date: date-like str
        筛选股票的上市日期，在该日期以后上市的股票将会被剔除：
    kwargs: str or list of str
        可以通过以下参数筛选股票, 可以同时输入多个筛选条件，只有符合要求的股票才会被筛选出来

    Returns
    -------
    list, 股票代码清单

    See Also
    --------
    filter_stocks()
    """
    share_basics = filter_stocks(date=date, **kwargs)
    return share_basics.index.to_list()


def get_basic_info(code_or_name: str, asset_types=None, match_full_name=False, printout=True, verbose=False):
    """ 等同于get_stock_info()，根据输入的信息，查找股票、基金、指数或期货、期权的基本信息

    Parameters
    ----------
    code_or_name: str
        证券代码或名称：
        - 如果是证券代码，可以含后缀也可以不含后缀，含后缀时精确查找、不含后缀时全局匹配
        - 如果是证券名称，可以包含通配符模糊查找，也可以通过名称模糊查找
        - 如果精确匹配到一个证券代码，返回一个字典，包含该证券代码的相关信息
    asset_types: str, list of str, optional
        证券类型，接受列表或逗号分隔字符串，包含认可的资产类型：
        - E     股票
        - IDX   指数
        - FD    基金
        - FT    期货
        - OPT   期权
    match_full_name: bool, default False
        是否匹配股票或基金的全名，默认否，如果匹配全名，耗时更长
    printout: bool, default True
        如果为True，打印匹配到的结果
    verbose: bool, default False
        当匹配到的证券太多时（多于五个），是否显示完整的信息
        - False 默认值，只显示匹配度最高的内容
        - True  显示所有匹配到的内容

    Returns
    -------
    stock_basic: dict
        当仅找到一个匹配时，返回一个dict，包含找到的基本信息，根据不同的证券类型，找到的信息不同：
        - 股票信息：公司名、地区、行业、全名、上市状态、上市日期
        - 指数信息：指数名、全名、发行人、种类、发行日期
        - 基金：   基金名、管理人、托管人、基金类型、发行日期、发行数量、投资类型、类型
        - 期货：   期货名称
        - 期权：   期权名称

    Examples
    --------
    >>> get_basic_info('000001.SZ')
    found 1 matches, matched codes are {'E': {'000001.SZ': '平安银行'}, 'count': 1}
    More information for asset type E:
    ------------------------------------------
    ts_code       000001.SZ
    name               平安银行
    area                 深圳
    industry             银行
    fullname     平安银行股份有限公司
    list_status           L
    list_date    1991-04-03
    -------------------------------------------

    >>> get_basic_info('000001')
    found 4 matches, matched codes are {'E': {'000001.SZ': '平安银行'}, 'IDX': {'000001.CZC': '农期指数', '000001.SH': '上证指数'}, 'FD': {'000001.OF': '华夏成长'}, 'count': 4}
    More information for asset type E:
    ------------------------------------------
    ts_code       000001.SZ
    name               平安银行
    area                 深圳
    industry             银行
    fullname     平安银行股份有限公司
    list_status           L
    list_date    1991-04-03
    -------------------------------------------
    More information for asset type IDX:
    ------------------------------------------
    ts_code   000001.CZC   000001.SH
    name            农期指数        上证指数
    fullname        农期指数      上证综合指数
    publisher    郑州商品交易所        中证公司
    category        商品指数        综合指数
    list_date       None  1991-07-15
    -------------------------------------------
    More information for asset type FD:
    ------------------------------------------
    ts_code        000001.OF
    name                华夏成长
    management          华夏基金
    custodian         中国建设银行
    fund_type            混合型
    issue_date    2001-11-28
    issue_amount     32.3683
    invest_type          成长型
    type              契约型开放式
    -------------------------------------------

    >>> get_basic_info('平安银行')
    found 4 matches, matched codes are {'E': {'000001.SZ': '平安银行', '600928.SH': '西安银行'}, 'IDX': {'802613.SI': '平安银行养老新兴投资指数'}, 'FD': {'700001.OF': '平安行业先锋'}, 'count': 4}
    More information for asset type E:
    ------------------------------------------
    ts_code       000001.SZ   600928.SH
    name               平安银行        西安银行
    area                 深圳          陕西
    industry             银行          银行
    fullname     平安银行股份有限公司  西安银行股份有限公司
    list_status           L           L
    list_date    1991-04-03  2019-03-01
    -------------------------------------------
    More information for asset type IDX:
    ------------------------------------------
    ts_code       802613.SI
    name       平安银行养老新兴投资指数
    fullname   平安银行养老新兴投资指数
    publisher          申万研究
    category           价值指数
    list_date    2017-01-03
    -------------------------------------------
    More information for asset type FD:
    ------------------------------------------
    ts_code        700001.OF
    name              平安行业先锋
    management          平安基金
    custodian           中国银行
    fund_type            混合型
    issue_date    2011-08-15
    issue_amount     31.9816
    invest_type          混合型
    type              契约型开放式
    -------------------------------------------

    >>> get_basic_info('贵州钢绳', match_full_name=False)
    No match found! To get better result, you can
    - pass "match_full_name=True" to match full names of stocks and funds

    >>> get_basic_info('贵州钢绳', match_full_name=True)
    found 1 matches, matched codes are {'E': {'600992.SH': '贵绳股份'}, 'count': 1}
    More information for asset type E:
    ------------------------------------------
    ts_code       600992.SH
    name               贵绳股份
    area                 贵州
    industry            钢加工
    fullname     贵州钢绳股份有限公司
    list_status           L
    list_date    2004-05-14
    -------------------------------------------
    """
    from qteasy import QT_DATA_SOURCE
    matched_codes = match_ts_code(code_or_name, asset_types=asset_types, match_full_name=match_full_name)

    ds = QT_DATA_SOURCE
    df_s, df_i, df_f, df_ft, df_o, df_ths = ds.get_all_basic_table_data()
    asset_type_basics = {k: v for k, v in zip(AVAILABLE_ASSET_TYPES, [df_s, df_i, df_ft, df_f, df_o])}

    matched_count = matched_codes['count']
    asset_best_matched = matched_codes
    asset_codes = []
    info_columns = {'E':
                        ['name', 'area', 'industry', 'fullname', 'list_status', 'list_date'],
                    'IDX':
                        ['name', 'fullname', 'publisher', 'category', 'list_date'],
                    'FD':
                        ['name', 'management', 'custodian', 'fund_type', 'issue_date', 'issue_amount', 'invest_type',
                         'type'],
                    'FT':
                        ['name'],
                    'OPT':
                        ['name']}

    if matched_count == 1 and not printout:
        # 返回唯一信息字典
        a_type = list(asset_best_matched.keys())[0]
        basics = asset_type_basics[a_type][info_columns[a_type]]
        return basics.loc[asset_codes[0]].to_dict()

    if (matched_count == 0) and (not match_full_name):
        print(f'No match found! To get better result, you can\n'
              f'- pass "match_full_name=True" to match full names of stocks and funds')
    elif (matched_count == 0) and (asset_types is not None):
        print(f'No match found! To get better result, you can\n'
              f'- pass "asset_type=None" to match all asset types')
    elif matched_count <= 5:
        print(f'found {matched_count} matches, matched codes are {matched_codes}')
    else:
        if verbose:
            print(f'found {matched_count} matches, matched codes are:\n{matched_codes}')
        else:
            asset_matched = {at: list(matched_codes[at].keys()) for at in matched_codes if at != 'count'}
            asset_best_matched = {}
            for a_type in matched_codes:
                if a_type == 'count':
                    continue
                if asset_matched[a_type]:
                    key = asset_matched[a_type][0]
                    asset_best_matched[a_type] = {key: matched_codes[a_type][key]}
            print(f'Too many matched codes {matched_count}, best matched are\n'
                  f'{asset_best_matched}\n'
                  f'To fine tune results, you can\n'
                  f'- pass "verbose=Ture" to view all matched assets\n'
                  f'- pass "asset_type=<asset_type>" to limit hit count')
    for a_type in asset_best_matched:
        if a_type == 'count':
            continue
        if asset_best_matched[a_type]:
            print(f'More information for asset type {a_type}:\n'
                  f'------------------------------------------')
            basics = asset_type_basics[a_type][info_columns[a_type]]
            asset_codes = list(asset_best_matched[a_type].keys())
            print(basics.loc[asset_codes].T)
            print('-------------------------------------------')


def get_stock_info(code_or_name: str, asset_types=None, match_full_name=False, printout=True, verbose=False):
    """ 等同于get_basic_info()
        根据输入的信息，查找股票、基金、指数或期货、期权的基本信息

    Parameters
    ----------
    code_or_name: str
        证券代码或名称，
        如果是证券代码，可以含后缀也可以不含后缀，含后缀时精确查找、不含后缀时全局匹配
        如果是证券名称，可以包含通配符模糊查找，也可以通过名称模糊查找
        如果精确匹配到一个证券代码，返回一个字典，包含该证券代码的相关信息
    asset_types: str or list of str, optional
        证券类型，接受列表或逗号分隔字符串，包含认可的资产类型：
        - E     股票
        - IDX   指数
        - FD    基金
        - FT    期货
        - OPT   期权
    match_full_name: bool, default False
        是否匹配股票或基金的全名，默认否，如果匹配全名，耗时更长
    printout: bool, default True
        如果为True，打印匹配到的结果
    verbose: bool, default False
        当匹配到的证券太多时（多于五个），是否显示完整的信息
        - False 默认值，只显示匹配度最高的内容
        - True  显示所有匹配到的内容

    Returns
    -------
    stock_info: dict
        当仅找到一个匹配时，返回一个dict，包含找到的基本信息，根据不同的证券类型，找到的信息不同：
        - 股票信息：公司名、地区、行业、全名、上市状态、上市日期
        - 指数信息：指数名、全名、发行人、种类、发行日期
        - 基金：   基金名、管理人、托管人、基金类型、发行日期、发行数量、投资类型、类型
        - 期货：   期货名称
        - 期权：   期权名称

    Notes
    -----
    用法示例参见：get_basic_info()

    """

    return get_basic_info(code_or_name=code_or_name,
                          asset_types=asset_types,
                          match_full_name=match_full_name,
                          printout=printout,
                          verbose=verbose)


def get_table_info(table_name, data_source=None, verbose=True) -> dict:
    """ 获取并打印数据源中一张数据表的信息，包括数据量、占用磁盘空间、主键名称、内容以及数据列的名称、数据类型及说明

    Parameters
    ----------
    table_name: str
        需要查询的数据表名称
    data_source: DataSource
        需要获取数据表信息的数据源，默认None，此时获取QT_DATA_SOURCE的信息
    verbose: bool, Default: True，
        是否打印完整数据列名称及类型清单

    Returns
    -------
    data_struct: dict
        数据表的结构化信息：
        {
            table name:    数据表名称
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
            pk_max2:       obj，数据表主键2最终记录
        }

    Examples
    --------
    >>> get_table_info('STOCK_BASIC')
    <stock_basic>, 1.5MB/5K records on disc
    primary keys:
    -----------------------------------
    1:  ts_code:
        <unknown> entries
        starts: 000001.SZ, end: 873527.BJ
    columns of table:
    ------------------------------------
            columns       dtypes remarks
    0       ts_code   varchar(9)    证券代码
    1        symbol   varchar(6)    股票代码
    2          name  varchar(20)    股票名称
    3          area  varchar(10)      地域
    4      industry  varchar(10)    所属行业
    5      fullname  varchar(50)    股票全称
    6        enname  varchar(80)    英文全称
    7       cnspell  varchar(40)    拼音缩写
    8        market   varchar(6)    市场类型
    9      exchange   varchar(6)   交易所代码
    10    curr_type   varchar(6)    交易货币
    11  list_status   varchar(4)    上市状态
    12    list_date         date    上市日期
    13  delist_date         date    退市日期
    14        is_hs   varchar(2)  是否沪深港通
    """
    from qteasy import QT_DATA_SOURCE
    if data_source is None:
        data_source = QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'data_source should be a DataSource, got {type(data_source)} instead.')
    return data_source.get_table_info(table=table_name, verbose=verbose)


def get_table_overview(data_source=None, tables=None, include_sys_tables=False) -> pd.DataFrame:
    """ 显示默认数据源或指定数据源的数据总览

    Parameters
    ----------
    data_source: Object
        一个data_source 对象,默认为None，如果为None，则显示默认数据源的overview
    tables: str or list of str, Default: None
        需要显示overview的数据表名称，如果为None，则显示所有数据表的overview
    include_sys_tables: bool, Default: False
        是否显示系统数据表的overview

    Returns
    -------
    pd.DataFrame

    Notes
    -----
    用法示例参见get_data_overview()
    """

    from .database import DataSource
    if data_source is None:
        from qteasy import QT_DATA_SOURCE
        data_source = QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'A DataSource object must be passed, got {type(data_source)} instead.')

    return data_source.overview(tables=tables, include_sys_tables=include_sys_tables)


def get_data_overview(data_source=None, tables=None, include_sys_tables=False) -> pd.DataFrame:
    """ 显示数据源的数据总览，等同于get_table_overview()

    获取的信息包括所有数据表的数据量、占用磁盘空间、主键名称、内容等

    Parameters
    ----------
    data_source: Object
        一个data_source 对象,默认为None，如果为None，则显示默认数据源的overview
    tables: str or list of str, Default: None
        需要显示overview的数据表名称，如果为None，则显示所有数据表的overview
    include_sys_tables: bool, Default: False
        是否显示系统数据表的overview

    Returns
    -------
    pd.DataFrame
    返回一个包含数据表的overview信息的DataFrame

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.get_data_overview()  # 获取当前默认数据源的数据总览
    Analyzing local data source tables... depending on size of tables, it may take a few minutes
    [########################################]62/62-100.0%  Analyzing completed!
    db:mysql://localhost@3306/ts_db
    Following tables contain local data, to view complete list, print returned DataFrame
                     Has_data Size_on_disk Record_count Record_start  Record_end
    table
    trade_calendar     True        2.5MB         73K     1990-10-12   2023-12-31
    stock_basic        True        1.5MB          5K           None         None
    stock_names        True        1.5MB         14K     1990-12-10   2023-07-17
    stock_company      True       18.5MB          3K           None         None
    stk_managers       True      150.4MB        126K     2020-01-01   2022-07-27
    index_basic        True        3.5MB         10K           None         None
    fund_basic         True        4.5MB         17K           None         None
    future_basic       True        1.5MB          7K           None         None
    opt_basic          True       15.5MB         44K           None         None
    stock_1min         True      42.83GB      273.0M       20220318     20230710
    stock_5min         True      34.33GB      233.2M       20090105     20230710
    stock_15min        True      14.45GB      141.2M       20090105     20230710
    stock_30min        True       7.78GB       77.1M       20090105     20230710
    stock_hourly       True       4.22GB       42.0M       20090105     20230710
    stock_daily        True       1.49GB       11.6M     1990-12-19   2023-07-17
    stock_weekly       True      231.9MB        2.6M     1990-12-21   2023-07-14
    stock_monthly      True       50.6MB        635K     1990-12-31   2023-06-30
    index_1min         True       4.25GB       27.6M       20220318     20230712
    index_5min         True       6.18GB       47.2M       20090105     20230712
    index_15min        True       2.61GB       26.1M       20090105     20230712
    index_30min        True      884.0MB       12.9M       20090105     20230712
    index_hourly       True      536.0MB        7.6M       20090105     20230712
    index_daily        True      309.0MB        3.7M     1990-12-19   2023-07-10
    index_weekly       True       61.6MB        674K     1991-07-05   2023-07-14
    index_monthly      True       13.5MB        158K     1991-07-31   2023-06-30
    fund_1min          True       5.46GB       55.8M       20220318     20230712
    fund_5min          True       3.68GB       12.3M       20220318     20230712
    fund_15min         True      835.9MB        3.9M       20220318     20230712
    fund_30min         True      385.7MB        1.9M       20220318     20230712
    fund_hourly        True      124.8MB        1.6M       20210104     20230629
    fund_daily         True      129.7MB        1.6M     1998-04-07   2023-07-10
    fund_nav           True      693.0MB       13.6M     2000-01-07   2023-07-07
    fund_share         True       72.7MB        1.4M     1998-03-27   2023-07-14
    fund_manager       True      109.7MB         37K     2000-02-22   2023-03-30
    future_hourly      True         32KB           0           None         None
    future_daily       True      190.8MB        2.0M     1995-04-17   2023-07-10
    options_hourly     True         32KB           0           None         None
    options_daily      True      436.0MB        4.6M     2015-02-09   2023-07-10
    stock_adj_factor   True      897.0MB       11.8M     1990-12-19   2023-07-12
    fund_adj_factor    True       74.6MB        1.8M     1998-04-07   2023-07-12
    stock_indicator    True       2.06GB       11.8M     1999-01-01   2023-07-17
    stock_indicator2   True      734.8MB        4.1M     2017-06-14   2023-07-10
    index_indicator    True        4.5MB         45K     2004-01-02   2023-07-10
    index_weight       True      748.0MB        8.7M     2005-04-08   2023-07-14
    income             True       59.7MB        213K     1990-12-31   2023-06-30
    balance            True       97.8MB        218K     1989-12-31   2023-06-30
    cashflow           True       69.7MB        181K     1998-12-31   2023-06-30
    financial          True      289.0MB        203K     1989-12-31   2023-06-30
    forecast           True       32.6MB         98K     1998-12-31   2024-03-31
    express            True        3.5MB         23K     2004-12-31   2023-06-30
    shibor             True         16KB         212           None         None
    """

    return get_table_overview(data_source=data_source, tables=tables, include_sys_tables=include_sys_tables)


def refill_data_source(tables, *, channel=None, data_source=None, dtypes=None, freqs=None, asset_types=None,
                       refresh_trade_calendar=False, refill_dependent_tables=True,
                       symbols=None, start_date=None, end_date=None, list_arg_filter=None, reversed_par_seq=False,
                       parallel=True, process_count=None, chunk_size=100, download_batch_size=0,
                       download_batch_interval=0, merge_type='update', log=False) -> None:
    """ 从网络数据提供商的API通道批量下载数据，清洗后填充数据到本地数据源中

    Parameters
    ----------
    tables: str or list of str,
        数据表名，必须是database中定义的数据表，用于指定需要下载的数据表
        可以给出数据表名称，如 'stock_daily, stock_weekly'
        也可以给出数据表的用途，如 'data, basic'
    data_source: DataSource, Default None
        需要填充数据的DataSource, 如果为None，则填充数据源到QT_DATA_SOURCE
    channel: str, optional, Default 'tushare'
        数据获取渠道，金融数据API，支持以下选项:

        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据
    tables: str or list of str, default: None
        数据表名，必须是database中定义的数据表，用于指定需要下载的数据表
    dtypes: str or list of str, default: None
        需要下载的数据类型，用于进一步筛选数据表，必须是database中定义的数据类型
    freqs: str or list of str, default: None
        需要下载的数据频率，用于进一步筛选数据表，必须是database中定义的数据频率
    asset_types: str or list of str, default: None
        需要下载的数据资产类型，用于进一步筛选数据表，必须是database中定义的资产类型
    refresh_trade_calendar: Bool, Default False
        是否更新trade_calendar表，如果为True，则会下载trade_calendar表的数据
    refill_dependent_tables: Bool, Default True, New in v1.4.3
        是否更新依赖表的数据，默认True，如果设置为False，则忽略依赖表，这样可能导致数据下载不成功
    start_date: str YYYYMMDD
        限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
    end_date: str YYYYMMDD
        限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
    list_arg_filter: str or list of str, default: None  **注意，不是所有情况下filter_arg参数都有效**
        限定下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
        参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。 如果filter_arg为None，则下载所有数据。
        例如，下载stock_basic表数据时，下载以下输入均为合法输入：
        - 'SZSE'
            仅下载深圳交易所的股票数据
        - ['SSE', 'SZSE']
        - 'SSE, SZSE'
            上面两种写法等效，下载上海和深圳交易所的股票数据
    symbols: str or list of str, default: None
        用于下载数据的股票代码，如果给出了symbols，只有这些股票代码的数据会被下载
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
    download_batch_size: int, default 0
        为了降低下载数据时的网络请求频率，可以在完成一批数据下载后，暂停一段时间再继续下载
        该参数指定了每次暂停之前最多可以下载的次数，该参数只有在parallel=False时有效
        如果为0，则不暂停，一次性下载所有数据
    download_batch_interval: int, default 0
        为了降低下载数据时的网络请求频率，可以在完成一批数据下载后，暂停一段时间再继续下载
        该参数指定了每次暂停的时间，单位为秒，该参数只有在parallel=False时有效
        如果<=0，则不暂停，立即开始下一批数据下载
    merge_type: str, Default 'update'
        数据写入数据源时的合并方式，支持以下选项：
        - 'update'  : 更新数据，如果数据已存在，则更新数据
        - 'ignore'  : 忽略数据，如果数据已存在，则丢弃下载的数据
    log: Bool, Default False
        是否记录数据下载日志

    Returns
    -------
    None

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.refill_data_source(tables='stock_basic')

    """

    # 0, 输入数据检查

    if data_source is None:
        from qteasy import QT_DATA_SOURCE
        data_source = QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'A DataSource object must be passed, got {type(data_source)} instead.')
    print(f'Filling data source {data_source} ...')
    if download_batch_interval is None:
        download_batch_interval = QT_CONFIG.hist_dnld_delay
    if download_batch_size is None:
        download_batch_size = QT_CONFIG.hist_dnld_delay_evy

    # 1, 解析需要下载的数据表清单
    if isinstance(tables, str):
        tables = str_to_list(tables)
    if isinstance(dtypes, str):
        dtypes = str_to_list(dtypes)
    if isinstance(freqs, str):
        freqs = str_to_list(freqs)
    if isinstance(asset_types, str):
        asset_types = str_to_list(asset_types)

    from .datatables import get_tables_by_name_or_usage
    from .data_channels import get_dependent_table

    if data_source is None:
        from qteasy import QT_DATA_SOURCE
        data_source = QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        err = TypeError(f'data source should be an instance of DataSource, got {type(data_source)} instead.')
        raise err

    if channel is None:
        channel = 'tushare'
    if not isinstance(channel, str):
        err = TypeError(f'channel should be a str, got {type(channel)} instead')
        raise err
    if channel not in ['tushare', 'akshare', 'eastmoney']:
        err = ValueError(f'channel should be one of "tushare", "akshare", and "eastmoney", got {channel} instead.')
        raise err

    table_list = get_tables_by_name_or_usage(
            tables=tables,
    )
    # 根据数据类型查找相应的数据表名称，并将这些数据表添加到下载清单中
    if dtypes or freqs or asset_types:
        data_types = infer_data_types(
                names=dtypes,
                freqs=freqs,
                asset_types=asset_types,
        )
        for dtype in data_types:
            table_list.update(dtype.data_table_names)

    # 下载部分数据表需要依赖其他表（通常是基础数据）的数据，这些依赖表的数据也需要下载，否则可能无法正确生成参数
    dependent_tables = set()
    if refill_dependent_tables:
        for table in table_list:
            dependent_table = get_dependent_table(table, channel=channel)
            if dependent_table is None:
                continue
            dependent_tables.add(dependent_table)
        table_list.update(dependent_tables)

    # 如果trade_calendar数据不足时，需要强制添加该表
    if not refresh_trade_calendar:
        # 检查trade_calendar中是否已有数据，且最新日期是否足以覆盖今天，如果没有数据或数据不足，也需要添加该表
        latest_calendar_date = data_source.get_table_info('trade_calendar', print_info=False)['pk_max1']
        try:
            latest_calendar_date = pd.to_datetime(latest_calendar_date)
            if pd.to_datetime('today') >= latest_calendar_date:
                refresh_trade_calendar = True
        except:
            refresh_trade_calendar = True

    # 整理下载表的顺序，这里需要确保依赖表位于下载清单的前面，否则当依赖表不存在时，会导致下载失败
    download_table_list = []
    if refresh_trade_calendar and ('trade_calendar' not in table_list):
        # 因为trade_calendar也有可能通过依赖表添加
        download_table_list.append('trade_calendar')
    if dependent_tables:
        download_table_list.extend([item for item in table_list if item in dependent_tables])
    download_table_list.extend([item for item in table_list if item not in dependent_tables])

    if parallel:
        print(f'into {len(table_list)} table(s) (parallely): {table_list}')
    else:
        print(f'into {len(table_list)} table(s) (sequentially): {table_list}')

    # 2, 循环下载数据表
    from .data_channels import parse_data_fetch_args, fetch_batched_table_data

    table_filled = 0
    total_rows_written = 0

    for table in table_list:
        # 2.1, 解析下载数据的参数
        arg_list = list(parse_data_fetch_args(
                table=table,
                channel=channel,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                list_arg_filter=list_arg_filter,
                reversed_par_seq=reversed_par_seq,
        ))

        if not arg_list:  # 意味着该数据表无法从该渠道下载
            print(f'<{table}> can\'t be fetched from channel:{channel}!')
            continue

        # 2.2, 批量下载数据
        completed = 0
        total = len(arg_list)
        total_written = 0
        df_concat_list = []
        interruption_error_string = ''

        with tqdm(total=total + 1, unit='task') as pbar:
            try:
                for res in fetch_batched_table_data(
                        table=table,
                        channel=channel,
                        arg_list=arg_list,
                        parallel=parallel,
                        process_count=process_count,
                        download_batch_size=download_batch_size,
                        download_batch_interval=download_batch_interval,
                ):
                    completed += 1
                    kwargs = tuple(res['kwargs'].values())
                    data = res['data'].dropna(axis=1, how='all')  # 删除全为空的列以便满足未来concat函数的要求，避免FutureWarning
                    if not data.empty:
                        df_concat_list.append(data)
                    if (completed % chunk_size == 0) and (len(df_concat_list) > 0):
                        # 将下载的数据写入数据源
                        rows_affected = data_source.update_table_data(
                                table=table,
                                df=pd.concat(df_concat_list, copy=False, ignore_index=True),
                                merge_type=merge_type,
                        )
                        df_concat_list = []
                        total_written += rows_affected
                    pbar.set_description(f'<{table}>{kwargs} {total_written} wrn')
                    pbar.update()

            except Exception as e:
                # 如果下载过程中出现错误，则跳过并不打断pbar的显示，并将已下载的数据写入数据源
                interruption_error_string = f' failed: {e}'
                continue

            finally:
                if df_concat_list:
                    # 将下载的数据写入数据源
                    rows_affected = data_source.update_table_data(
                            table=table,
                            df=pd.concat(df_concat_list, copy=False, ignore_index=True),
                            merge_type=merge_type,
                    )
                    total_written += rows_affected

                pbar.set_description(f'<{table}> {total_written} wrn{interruption_error_string}')
                pbar.update()
                table_filled += 1
                total_rows_written += total_written

    print(f'\nData refill completed! {total_rows_written} rows written into {table_filled}/{len(table_list)} table(s)!')

    return None


def transfer_data(source: DataSource,
                  target: DataSource,
                  tables=None,
                  parallel=True,
                  process_count=None,
                  chunk_size=100,
                  merge_type='update',
                  log=False):
    """ 将数据从一个数据源迁移到另一个数据源

    Parameters
    ----------
    source: DataSource
        数据迁移的来源数据源，必须是一个DataSource对象
    target: DataSource
        数据迁移的目标数据源，必须是一个DataSource对象
    tables: str or list of str, default: None
        需要迁移的数据表名称，如果为None，则迁移所有数据表
    parallel: Bool, Default True
        是否启用多线程迁移数据
        - True:  启用多线程迁移数据
        - False: 禁用多线程迁移数据
    process_count: int
        启用多线程迁移数据时，同时开启的线程数，默认值为设备的CPU核心数
    chunk_size: int
        保存数据到目标数据源时，为了减少文件/数据库读取次数，将迁移的数据累计一定数量后再批量保存到目标数据源，chunk_size即批量，默认值100
    merge_type: str, Default 'update'
        数据写入目标数据源时的合并方式，支持以下选项：
        - 'update'  : 更新数据，如果数据已存在，则更新数据
        - 'ignore'  : 忽略数据，如果数据已存在，则丢弃迁移的数据
    log: Bool, Default False
        是否记录数据迁移日志

    Returns
    -------
    None
    """
    if not isinstance(source, DataSource):
        raise TypeError(f'source should be a DataSource, got {type(source)} instead.')
    if not isinstance(target, DataSource):
        raise TypeError(f'target should be a DataSource, got {type(target)} instead.')

    # TODO: implement this function,
    #  当需要将大量数据从一个数据源迁移到另一个数据源时，这个函数将会非常有用。
    #  这个函数需要具备迁移大量数据的能力，同时需要提供进度条、需要分段迁移

    raise NotImplementedError


def get_history_data(htypes=None,
                     *,
                     htype_names=None,
                     data_types=None,
                     data_source=None,
                     shares=None,
                     symbols=None,
                     start=None,
                     end=None,
                     freq=None,
                     rows=None,
                     asset_type=None,
                     adj=None,
                     as_data_frame=None,
                     group_by=None,
                     **kwargs):
    """根据给定的标的、数据类型与频率，从本地数据源获取历史数据并组装为策略可直接使用的结构。

    可以通过 ``htype_names`` 或 ``data_types`` 指定需要的数据种类，并结合 ``shares`` /
    ``symbols``、时间区间与 ``freq`` 控制取数范围；根据 ``as_data_frame`` 与 ``group_by``
    的设置，函数返回 HistoryPanel 或按标的/数据类型分组的 DataFrame 字典。关于数据类型
    推断、频率转换和 trade_time_only 等高级用法，详见文档「历史数据获取 get_history_data」
    相关章节。

    Parameters
    ----------
    htype_names: [str] or str, optional
        需要获取的历史数据的名称集合，如果htypes为空，则系统将尝试通过根据历史数据名称和freq/asset_type参数创建
        所有可能的htypes。输入方式可以为str或list：
         - str:     'open, high, low, close'
         - list:    ['open', 'high', 'low', 'close']
    htypes: [DataType], optional, deprecated
        需要获取的历史数据的名称集合，如果htypes为空，则系统将尝试通过根据历史数据名称和freq/asset_type参数创建
        所有可能的htypes。输入方式可以为str或list：
    data_types: [DataType], optional
        需要获取的历史数据类型集合，必须是合法的数据类型对象。
        如果给出了本参数，htype_names会被忽略，否则根据htype_names参数创建可能的htypes
    data_source: DataSource, optional
        需要获取历史数据的数据源
    shares: str or list of str, optional
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
         - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
    symbols: str or list of str, optional
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
        - str:     '000001, 000002, 000004, 000005'
        - list:    ['000001', '000002', '000004', '000005']
    start: str, optional
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
    end: str, optional
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
    rows: int, default 10
        获取的历史数据的行数，如果指定了start和end，则忽略此参数，且获取的数据的时间范围为[start, end]
        如果未指定start和end，则获取数据表中最近的rows条数据，使用row来获取数据时，速度比使用日期慢得多
    freq: str, optional
        获取的历史数据的频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
    asset_type: str or list of str, optional
        限定获取的数据中包含的资产种类，包含以下选项或下面选项的组合，合法的组合方式包括
        逗号分隔字符串或字符串列表，例如: 'E, IDX' 和 ['E', 'IDX']都是合法输入
         - any: 可以获取任意资产类型的证券数据(默认值)
         - E:   只获取股票类型证券的数据
         - IDX: 只获取指数类型证券的数据
         - FT:  只获取期货类型证券的数据
         - FD:  只获取基金类型证券的数据
    adj: str, optional, deprecated
        Deprecated: 对于某些数据，可以获取复权数据，需要通过复权因子计算，复权选项包括：
         - none / n: 不复权(默认值)
         - back / b: 后复权
         - forward / fw / f: 前复权
         从下一个版本开始，adj参数将不再可用，请直接在htype中使用close:b等方式指定复权价格
    as_data_frame: bool, default True
        True 时返回 HistoryPanel 对象，False 时返回一个包含 DataFrame 对象的字典。
    group_by: str, default 'shares'
        如果返回DataFrame对象，设置dataframe的分组策略
        - 'shares' / 'share' / 's': 每一个share组合为一个dataframe
        - 'htypes' / 'htype' / 'h': 每一个htype组合为一个dataframe
    **kwargs
        用于生成 trade_time_index 的参数以及频率转换行为控制，包括：
        drop_nan: bool
            是否保留全NaN的行
        resample_method: str
            如果数据需要升频或降频时，调整频率的方法
            调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
            数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
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

            数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
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
        b_days_only: bool 默认True
            是否强制转换自然日频率为工作日，即：
            'D' -> 'B'
            'W' -> 'W-FRI'
            'M' -> 'BM'
        trade_time_only: bool, default True
            为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
        include_start: bool, default True
            日期时间序列是否包含开始日期/时间
        include_end: bool, default True
            日期时间序列是否包含结束日期/时间
        start_am:, str
            早晨交易时段的开始时间
        end_am:, str
            早晨交易时段的结束时间
        include_start_am: bool
            早晨交易时段是否包括开始时间
        include_end_am: bool
            早晨交易时段是否包括结束时间
        start_pm: str
            下午交易时段的开始时间
        end_pm: str
            下午交易时段的结束时间
        include_start_pm: bool
            下午交易时段是否包含开始时间
        include_end_pm: bool
            下午交易时段是否包含结束时间

    Returns
    -------
    HistoryPanel
        当 ``as_data_frame`` 为 False 时，返回包含所有请求数据的 HistoryPanel 对象。
    dict of pandas.DataFrame
        当 ``as_data_frame`` 为 True 时，返回按 ``group_by`` 分组的 DataFrame 字典。

    Examples
    --------
    >>> import qteasy as qt
    # 给出历史数据类型和证券代码，起止时间，可以获取该时间段内该股票的历史数据
    >>> qt.get_history_data(htype_names='open, high, low, close, vol', shares='000001.SZ', start='20191225', end='20200110')
    {'000001.SZ':
                 open   high    low  close         vol
    2019-12-25  16.45  16.56  16.24  16.30   414917.98
    2019-12-26  16.34  16.48  16.32  16.47   372033.86
    2019-12-27  16.53  16.93  16.43  16.63  1042574.72
    2019-12-30  16.46  16.63  16.10  16.57   976970.31
    2019-12-31  16.57  16.63  16.31  16.45   704442.25
    2020-01-02  16.65  16.95  16.55  16.87  1530231.87
    2020-01-03  16.94  17.31  16.92  17.18  1116194.81
    2020-01-06  17.01  17.34  16.91  17.07   862083.50
    2020-01-07  17.13  17.28  16.95  17.15   728607.56
    2020-01-08  17.00  17.05  16.63  16.66   847824.12
    2020-01-09  16.81  16.93  16.53  16.79  1031636.65
    2020-01-10  16.79  16.81  16.52  16.69   585548.45
    }

    >>> # 除了股票的价格数据以外，也可以获取基金、指数的价格数据，如下面的代码获取000300.SH的指数价格
    >>> qt.get_history_data(htype_names='close', shares='000300.SH', start='20191225', end='20200105')
    {'000300.SH':
                  close
    2019-12-25  3990.87
    2019-12-26  4025.99
    2019-12-27  4022.03
    2019-12-30  4081.63
    2019-12-31  4096.58
    2020-01-02  4152.24
    2020-01-03  4144.96
    }

    >>> # 以及基金的净值数据
    >>> qt.get_history_data(htype_names='unit_nav, accum_nav', shares='000001.OF', start='20191225', end='20200105')
    {'000001.OF':
                unit_nav  accum_nav
    2019-12-25     1.086      3.547
    2019-12-26     1.096      3.557
    2019-12-27     1.091      3.552
    2019-12-30     1.100      3.561
    2019-12-31     1.105      3.566
    2020-01-02     1.123      3.584
    2020-01-03     1.127      3.588
    }

    >>> # 不光价格数据，其他类型的数据也可以同时获取：
    >>> qt.get_history_data(htype_names='close, pe, pb', shares='000001.SZ', start='20191225', end='20200105')
    {'000001.SZ':
                close       pe      pb
    2019-12-25  16.30  12.7454  1.1798
    2019-12-26  16.47  12.8784  1.1921
    2019-12-27  16.63  13.0035  1.2036
    2019-12-30  16.57  12.9566  1.1993
    2019-12-31  16.45  12.8627  1.1906
    2020-01-02  16.87  13.1911  1.2210
    2020-01-03  17.18  13.4335  1.2434
    }

    >>> # 可以同时混合获取多只股票、指数、多种数据类型的数据，如果某些数据类型缺失，会用NaN填充，注意000001.SZ是股票平安银行，000001.SH是上证指数
    >>> qt.get_history_data(htype_names='close, pe, pb, total_mv, eps', shares='000001.SZ, 000001.SH', start='20191225', end='20200105')
    {'000001.SZ':
                close       pe      pb      total_mv   eps
    2019-12-25  16.30  12.7454  1.1798  3.163165e+07   NaN
    2019-12-26  16.47  12.8784  1.1921  3.196155e+07   NaN
    2019-12-27  16.63  13.0035  1.2036  3.227204e+07   NaN
    2019-12-30  16.57  12.9566  1.1993  3.215561e+07   NaN
    2019-12-31  16.45  12.8627  1.1906  3.192274e+07  1.54
    2020-01-02  16.87  13.1911  1.2210  3.273778e+07  1.54
    2020-01-03  17.18  13.4335  1.2434  3.333937e+07  1.54,
    '000001.SH':
                  close     pe    pb      total_mv  eps
    2019-12-25  2981.88  13.74  1.38  3.987686e+13  NaN
    2019-12-26  3007.35  13.85  1.39  4.020871e+13  NaN
    2019-12-27  3005.04  13.85  1.39  4.019086e+13  NaN
    2019-12-30  3040.02  14.00  1.40  4.064796e+13  NaN
    2019-12-31  3050.12  14.05  1.41  4.079249e+13  NaN
    2020-01-02  3085.20  14.22  1.42  4.128453e+13  NaN
    2020-01-03  3083.79  14.22  1.42  4.127933e+13  NaN
    }

    >>> # 通过设置freq参数，可以获取不同频率的K线数据，如设置freq='H'可以获取1小时频率的数据
    >>> qt.get_history_data(htype_names='open:b, high:b, low:b, close:b', shares='000001.SZ', start='20191229', end='20200106', freq='H', asset_type='E')
     {'000001.SZ':
                               open        high         low       close
    2019-12-30 10:00:00  1796.92174  1796.92174  1796.92174  1796.92174
    2019-12-30 11:00:00  1790.37160  1800.19681  1758.71259  1786.00484
    2019-12-30 14:00:00  1811.11371  1813.29709  1795.83005  1806.74695
    2019-12-30 15:00:00  1805.65526  1808.93033  1793.64667  1808.93033
    2019-12-31 10:00:00  1808.93033  1808.93033  1808.93033  1808.93033
    2019-12-31 11:00:00  1806.74695  1806.74695  1780.54639  1788.18822
    2019-12-31 14:00:00  1786.00484  1788.18822  1781.63808  1786.00484
    2019-12-31 15:00:00  1786.00484  1796.92174  1783.82146  1795.83005
    2020-01-02 10:00:00  1817.66385  1817.66385  1817.66385  1817.66385
    2020-01-02 11:00:00  1819.84723  1848.23117  1807.83864  1840.58934
    2020-01-02 14:00:00  1842.77272  1847.13948  1828.58075  1843.86441
    2020-01-02 15:00:00  1843.86441  1844.95610  1836.22258  1841.68103
    2020-01-03 10:00:00  1849.32286  1849.32286  1849.32286  1849.32286
    2020-01-03 11:00:00  1849.32286  1879.89018  1849.32286  1877.70680
    2020-01-03 14:00:00  1863.51483  1889.71539  1863.51483  1884.25694
    2020-01-03 15:00:00  1884.25694  1884.25694  1872.24835  1875.52342
    }

    >>> # 可以设置b_days_only参数来将价格填充到非交易日，形成完整的日期序列
    >>> qt.get_history_data(htype_names='open, high, low, close, vol', shares='000001.SZ', start='20191225', end='20200105', b_days_only=False)
    {'000001.SZ':
                  open   high    low  close         vol
     2019-12-25  16.45  16.56  16.24  16.30   414917.98
     2019-12-26  16.34  16.48  16.32  16.47   372033.86
     2019-12-27  16.53  16.93  16.43  16.63  1042574.72
     2019-12-28  16.53  16.93  16.43  16.63  1042574.72
     2019-12-29  16.53  16.93  16.43  16.63  1042574.72
     2019-12-30  16.46  16.63  16.10  16.57   976970.31
     2019-12-31  16.57  16.63  16.31  16.45   704442.25
     2020-01-01  16.57  16.63  16.31  16.45   704442.25
     2020-01-02  16.65  16.95  16.55  16.87  1530231.87
     2020-01-03  16.94  17.31  16.92  17.18  1116194.81
     2020-01-04  16.94  17.31  16.92  17.18  1116194.81
     2020-01-05  16.94  17.31  16.92  17.18  1116194.81
     }

    >>> # 使用特殊的htypes，可以获取特定的数据，如指数权重数据，下面的代码获取000001.SZ在HS300指数重的权重数据，单位为百分比
    >>> qt.get_history_data(htype_names='wt_id:000300.SH', shares='000001.SZ, 000002.SZ', start='20191225', end='20200105')
    {'000001.SZ':
                wt_idx:000300.SH
    2020-01-02        1.1714
    2020-01-03        1.1714,
    '000002.SZ':
                wt_idx:000300.SH
    2020-01-02        1.3595
    2020-01-03        1.3595
    }

    """

    # 检查数据合法性：
    if shares is None:
        shares = ''
    if htypes is None:
        htypes = ''

    if not isinstance(shares, (str, list)):
        raise TypeError(f'shares should be a string or list of strings, got {type(shares)}')
    if not isinstance(htypes, (str, list)):
        raise TypeError(f'htypes should be a string or list of strings, got {type(htypes)}')

    if isinstance(shares, str):
        shares = str_to_list(shares)
    if isinstance(shares, list):
        if not all(isinstance(item, str) for item in shares):
            raise TypeError(f'all items in shares list should be a string, got otherwise')

    # 如果给出了data_types参数，确认结果正确后，忽略htypes/htype_names参数
    if data_types is not None:
        if not isinstance(data_types, list) or not all(isinstance(dt, DataType) for dt in data_types):
            raise TypeError("data_types must be a list of DataType instances")
    else:
        # 仅当用户显式传入了非空 htypes 时才用它覆盖 htype_names（htypes 为 None 时已在前面被置为 ''，故用 truthy 判断以保持与 htype_names 等效）
        if htypes:
            warn("htypes parameter is deprecated, please use htype_names instead", DeprecationWarning)
            htype_names = htypes

        if htype_names is None:
            raise ValueError("Either data_types or htype_names must be provided")

        if isinstance(htype_names, str):
            htype_names = str_to_list(htype_names)
        if not all(isinstance(n, str) for n in htype_names):
            raise TypeError("All elements in htype_names must be strings")

        # check parameter freq
        if freq is None:
            freq = 'd'
        if not isinstance(freq, str):
            err = TypeError(f'freq should be a string, got {type(freq)} instead')
            raise err
        if freq.upper() not in TIME_FREQ_STRINGS:
            err = KeyError(f'invalid freq, valid freq should be anyone in {TIME_FREQ_STRINGS}')
            raise err
        freq = freq.lower()

        # check parameter asset_type:
        if asset_type is None:
            asset_type = 'any'
        if not isinstance(asset_type, (str, list)):
            err = TypeError(f'asset type should be a string, got {type(asset_type)} instead')
            raise err
        if isinstance(asset_type, str):
            asset_type = str_to_list(asset_type)
        if not all(isinstance(item, str) for item in asset_type):
            err = KeyError(f'not all items in asset type are strings')
            raise err
        if not all(item.upper() in ['ANY'] + AVAILABLE_ASSET_TYPES for item in asset_type):
            err = KeyError(f'invalid asset_type, asset types should be one or many in {AVAILABLE_ASSET_TYPES}')
            raise err
        # 显式 asset_type：用户未使用 any 关键字；否则视为“未显式指定”
        explicit_asset_type = not any(item.upper() == 'ANY' for item in asset_type)
        if any(item.upper() == 'ANY' for item in asset_type):
            asset_type = AVAILABLE_ASSET_TYPES
        asset_type = [item.upper() for item in asset_type]

        if adj is not None:
            msg = f'parameter adj is deprecated, please add adj suffixes for htype names instead\n' \
                  f'for example: use "close:b" for back-adjusted close prices'
            warn(msg, DeprecationWarning)
        else:
            adj = 'none'
        if not isinstance(adj, str):
            err = TypeError(f'adj type should be a string, got {type(adj)} instead')
            raise err
        if adj.upper() not in ['NONE', 'BACK', 'FORWARD', 'N', 'B', 'FW', 'F']:
            err = KeyError(f"invalid adj type ({adj}), which should be anyone of "
                           f"['NONE', 'BACK', 'FORWARD', 'N', 'B', 'FW', 'F']")
            raise err
        adj = adj.lower()
        PRICE_TYPES = ['open', 'close', 'high', 'low']
        if adj.upper() in ['F', 'FORWARD', 'FW']:
            htype_names = [f'{htype}|f' if htype in PRICE_TYPES else htype for htype in htype_names]
        elif adj.upper() in ['B', 'BACK']:
            htype_names = [f'{htype}|b' if htype in PRICE_TYPES else htype for htype in htype_names]
        else:
            htype_names = htype_names

        # 按名称解析 DataType，对 infer_data_types 的结果做二次筛选，保证每个 name 只有一个原生 freq/asset_type
        def _freq_level(freq_str: str) -> int:
            """将频率字符串转换为主频率，并返回其 level，用于频率高低比较。"""
            _, main_freq, _ = parse_freq_string(freq_str)
            key = main_freq if main_freq is not None else freq_str.upper()
            if key not in TIME_FREQ_LEVELS:
                err = KeyError(f'invalid freq string {freq_str}')
                raise err
            return TIME_FREQ_LEVELS[key]

        def _choose_best_freq(available_freqs, target_freq_str: str) -> str:
            """在可用原生频率中，为 target_freq 选择一个“最合适”的原生 freq。"""
            # 使用主频率进行比较
            _, target_main, _ = parse_freq_string(target_freq_str)
            if target_main is None:
                target_main = target_freq_str.upper()
            t_lvl = _freq_level(target_main)
            # 将可用频率映射到主频率集合
            norm_map = {}
            for f in available_freqs:
                _, main_f, _ = parse_freq_string(f)
                key = main_f if main_f is not None else f.upper()
                norm_map.setdefault(key, []).append(f)
            norm_freqs = list(norm_map.keys())
            if target_main in norm_freqs:
                return norm_map[target_main][0]
            higher = [nf for nf in norm_freqs if _freq_level(nf) < t_lvl]
            if higher:
                best_norm = max(higher, key=_freq_level)
                return norm_map[best_norm][0]
            lower = [nf for nf in norm_freqs if _freq_level(nf) > t_lvl]
            if lower:
                best_norm = min(lower, key=_freq_level)
                return norm_map[best_norm][0]
            # 理论上不会到达此处
            return available_freqs[0]

        def _collect_candidate_dtypes_from_names(names, target_freq_str: str, asset_types_arg: list[str]):
            """阶段 1：从 DATA_TYPE_MAP 中收集每个 name 的原生 DataType 候选集合。"""
            candidates = {n: [] for n in names}
            # 第一轮：使用 target_freq 直接匹配
            for n in names:
                try:
                    dts = infer_data_types(
                        names=[n],
                        freqs=[target_freq_str],
                        asset_types=asset_types_arg,
                        adj=None,
                        allow_ignore_freq=False,
                        allow_ignore_asset_type=False,
                    )
                except Exception:
                    dts = []
                if dts:
                    candidates[n].extend(dts)
            # 第二轮：对仍然没有候选的 name 使用更宽的频率集合重试，
            # 这里使用小写形式的频率字符串，以便与 DATA_TYPE_MAP 中的原生 freq 定义（如 'q','m','d','h'）对齐，
            # 并允许 freq / asset_type 忽略匹配，以便由 history 层负责升/降频与资产类型整合。
            broad_freqs = [f.lower() for f in TIME_FREQ_LEVELS.keys()]
            for n in names:
                if candidates[n]:
                    continue
                try:
                    dts = infer_data_types(
                        names=[n],
                        freqs=broad_freqs,
                        asset_types=asset_types_arg,
                        adj=None,
                        allow_ignore_freq=True,
                        allow_ignore_asset_type=True,
                    )
                except Exception:
                    dts = []
                if dts:
                    candidates[n].extend(dts)
            return candidates

        def _select_effective_dtypes(candidates_raw: dict, target_freq_str: str,
                                     asset_types_arg: list[str],
                                     explicit_asset_type: bool) -> list[DataType]:
            """阶段 2：对候选 DataType 做名称覆盖、频率唯一化与资产类型过滤。

            当 explicit_asset_type 为 False 时，不在此处对 asset_type 做任何裁剪，
            允许同一 name/freq 下存在多种资产类型的 DataType，一并交由 history 层处理。
            """
            missing_names = []
            effective_dtypes: list[DataType] = []
            # 名称逐一处理
            for name, dts in candidates_raw.items():
                if not dts:
                    missing_names.append(name)
                    continue
                # 按 dtype_id 去重
                dt_map = {}
                for dt in dts:
                    dt_map[dt.dtype_id] = dt
                dts_unique = list(dt_map.values())
                # 频率唯一化
                available_freqs = list({dt.freq for dt in dts_unique})
                try:
                    chosen_freq = _choose_best_freq(available_freqs, target_freq_str)
                except KeyError:
                    missing_names.append(name)
                    continue
                freq_filtered = [dt for dt in dts_unique if dt.freq == chosen_freq]
                if not freq_filtered:
                    missing_names.append(name)
                    continue
                # 资产类型过滤：
                # - 显式 asset_type 时按 asset_types_arg 过滤；
                # - 未显式指定时不过滤，允许多种资产类型并存，由下游根据 shares/type 决定实际取数。
                if explicit_asset_type:
                    # 用户给出了明确资产类型限制，此时 asset_types_arg 就是期望资产类型集合
                    filtered = [dt for dt in freq_filtered if dt.asset_type in asset_types_arg]
                    if not filtered:
                        missing_names.append(name)
                        continue
                    freq_filtered = filtered
                # 经过频率与资产类型处理后，至少应保留一个 DataType
                if not freq_filtered:
                    missing_names.append(name)
                    continue
                effective_dtypes.extend(freq_filtered)
            if missing_names:
                raise ValueError(
                    f"The following data type name(s) are not defined or could not be matched: {missing_names}. "
                    f"Check spelling or define them in DATA_TYPE_MAP."
                )
            return effective_dtypes

        # 收集候选 DataType 并根据 freq / asset_type 规则筛选
        asset_types_arg = asset_type
        candidates_raw = _collect_candidate_dtypes_from_names(htype_names, freq, asset_types_arg)
        data_types = _select_effective_dtypes(candidates_raw, freq, asset_types_arg, explicit_asset_type)

    if data_source is None:
        from qteasy import QT_DATA_SOURCE
        data_source = QT_DATA_SOURCE
    else:
        if not isinstance(data_source, DataSource):
            err = TypeError(f'data_source should be a data source object, got {type(data_source)} instead')
            raise err

    if symbols is not None and shares is None:
        shares = symbols
    if shares is None:
        shares = QT_CONFIG.asset_pool

    # check start and end parameters
    one_year = pd.Timedelta(365, 'd')
    one_week = pd.Timedelta(7, 'd')

    if (start is None) and (end is None) and (rows is None):
        end = pd.to_datetime('today').date()
        start = end - one_year
    elif (start is None) and (end is None):
        rows = int(rows)
    elif start is None:
        try:
            end = pd.to_datetime(end)
        except Exception:
            raise Exception(f'end date can not be converted to a datetime')
        start = end - one_year
        rows = None
    elif end is None:
        try:
            start = pd.to_datetime(start)
        except Exception:
            raise Exception(f'start date can not be converted to a datetime')
        end = start + one_year
        rows = None
    else:
        try:
            start = pd.to_datetime(start)
            end = pd.to_datetime(end)
        except Exception:
            raise Exception(f'start and end must be both datetime like')
        if end - start <= one_week:
            raise ValueError(f'End date should be at least one week after start date')
        rows = None
    # set start/end to be the correct datetime format

    if start is not None:
        try:
            start = pd.to_datetime(start)
            start = start.strftime('%Y%m%d')
        except Exception:
            raise Exception(f'Start date can not be converted to datetime format')
    if end is not None:
        try:
            end = pd.to_datetime(end)
            end = end.strftime('%Y%m%d')
        except Exception:
            raise Exception(f'End date can not be converted to datetime format')

    if as_data_frame is None:
        as_data_frame = True

    if group_by is None:
        group_by = 'shares'
    if group_by in ['shares', 'share', 's']:
        group_by = 'shares'
    elif group_by in ['htypes', 'htype', 'h']:
        group_by = 'htypes'

    hp = get_history_panel(
            data_types=data_types,
            data_source=data_source,
            shares=shares,
            start=start,
            end=end,
            freq=freq,
            rows=rows,
            **kwargs,
    )

    if as_data_frame:
        return hp.unstack(by=group_by)
    else:
        return hp


# TODO: 在这个函数中对config的各项参数进行检查和处理，将对各个日期的检查和更新（如交易日调整等）放在这里，直接调整
#  config参数，使所有参数直接可用。并发出warning，不要在后续的使用过程中调整参数
def is_ready(**kwargs):
    """ 检查QT_CONFIG以及Operator对象，确认qt.run()是否具备基本运行条件

    Parameters
    ----------
    kwargs:

    Returns
    -------
    """
    # 检查各个cash_amounts与各个cash_dates是否能生成正确的CashPlan对象

    # 检查invest(loop)、opti、test等几个start与end日期是否冲突

    # 检查invest(loop)、opti、test等几个cash_dates是否冲突

    return True


def info(**kwargs):
    """ qteasy 模块的帮助信息入口函数

    Parameters
    ----------
    kwargs:

    Returns
    -------
    """
    raise NotImplementedError


def help(**kwargs):
    """ qteasy 模块的帮助信息入口函数

    Parameters
    ----------
    kwargs:

    Returns
    -------
    """
    raise NotImplementedError


def live_trade_accounts() -> pd.DataFrame:
    """ 获取当前所有实盘交易账户的详细信息

    Returns
    -------
    all_accounts: pd.DataFrame
        包含所有实盘交易账户信息的DataFrame
    """
    from qteasy import QT_DATA_SOURCE
    from qteasy.trade_recording import get_all_accounts
    return get_all_accounts(QT_DATA_SOURCE)


# noinspection PyTypeChecker
def run(op: Operator, **kwargs) -> Union[dict, list]:
    """根据当前配置运行给定的 Operator，并进入回测、优化或实盘等不同工作模式。

    本函数是 qteasy 的统一入口：根据全局配置 ``QT_CONFIG['mode']``（可通过
    ``qt.configure(mode=...)`` 暂时覆盖），选择实盘模式、回测模式、优化模式等，
    自动准备所需数据源与日志对象并调用 ``Operator.run()`` 执行完整流程。各模式
    的详细行为与输出结构见文档「运行 qteasy 与工作模式」相关章节。

    Parameters
    ----------
    op : Operator
        已配置好策略与运行参数的 Operator 对象。
    **kwargs
        本次运行临时覆盖的配置项，键名需为合法的 qteasy 配置键，例如
        ``mode``、``asset_pool``、``invest_start``、``invest_end`` 等。

    Returns
    -------
    dict or list
        当 ``mode == 1``（回测模式）时通常返回包含回测结果的字典；
        当 ``mode == 2``（优化模式）时通常返回包含多组参数结果的列表；
        实盘模式与其他模式的具体返回结构详见 Operator.run() 与相关文档说明。

    Examples
    --------
    >>> import qteasy as qt
    >>> op = qt.Operator('dma')
    >>> qt.run(op, mode=1)  # 以回测模式运行
    """

    # 如果函数调用时用户给出了关键字参数(**kwargs），将关键字参数赋值给一个临时配置参数对象，
    # 覆盖QT_CONFIG的设置，但是仅本次运行有效
    config = ConfigDict(**QT_CONFIG)
    configure(config=config, **kwargs)

    return op.run(
            config=config,
            datasource=qteasy.QT_DATA_SOURCE,
            logger=qteasy.logger_core,
    )


def get_kline(
        shares,
        start: str = None,
        end: str = None,
        rows: int = None,
        freq: str = 'd',
        adj: str = None,
        asset_type: str = None,
        as_panel: bool = False,
        data_source=None,
        b_days_only: bool = None,
        trade_time_only: bool = None,
        **kwargs,
):
    """ 获取指定标的的标准 OHLCV K 线数据。

    本函数是基于 DataType / get_history_data 的高层封装，用于一行代码获取常见
    K 线价格数据，统一输出列名为 ``open, high, low, close, vol``，便于在 Notebook
    中进行快速数据探索与可视化。

    Parameters
    ----------
    shares : str or list of str
        需要获取 K 线数据的证券代码，可以是逗号分隔的字符串或字符串列表，例如：
        ``'000001.SZ,000002.SZ'`` 或 ``['000001.SZ', '000002.SZ']``。
    start : str, optional
        起始日期，格式 ``YYYYMMDD`` 或 ``YYYYMMDD HH:MM:SS``。与 ``end`` 一起
        指定时间区间；如给出，则 ``rows`` 参数被忽略。
    end : str, optional
        结束日期，格式同 ``start``。
    rows : int, optional
        需要获取的最近记录条数；仅在未指定 ``start`` 和 ``end`` 时生效。
    freq : str, default 'd'
        数据频率，默认为日线。可选值与 ``get_history_data`` 一致，如 ``'d'``、
        ``'w'``、``'m'``、``'h'`` 等。
    adj : str, optional
        复权方式，语义与 ``get_history_data`` 保持一致；推荐在 DataType 名称中使
        用 ``close|b`` 一类语法指定复权，本参数将在未来版本中移除。
    asset_type : str, optional
        资产类型过滤条件，如 ``'E'``（股票）、``'IDX'``（指数）等，具体含义与
        ``get_history_data`` 中的 ``asset_type`` 参数一致。
    as_panel : bool, default False
        - False: 返回单标的 DataFrame 或多标的 ``Dict[str, DataFrame]``；
        - True:  返回一个 ``HistoryPanel``，``htypes`` 固定为
          ``['open', 'high', 'low', 'close', 'vol']``。
    data_source : DataSource, optional
        历史数据源，不提供时使用全局默认 ``QT_DATA_SOURCE``。
    b_days_only : bool, optional
        是否将自然日频率转换为工作日，传递给 ``get_history_data``，语义一致。
    trade_time_only : bool, optional
        是否仅在交易时段生成时间索引，传递给 ``get_history_data``，语义一致。
    **kwargs :
        其他将透传给 ``get_history_data`` 的参数（如 ``drop_nan``、``resample_method``、
        交易时段参数等）。

    Returns
    -------
    pandas.DataFrame or Dict[str, pandas.DataFrame] or HistoryPanel
        - 当 ``as_panel=False`` 且 ``shares`` 为单个标的时，返回一个以时间为索引、
          列为 ``open, high, low, close, vol`` 的 DataFrame；
        - 当 ``as_panel=False`` 且 ``shares`` 为多个标的时，返回
          ``Dict[str, DataFrame]``，每只标的一张 K 线表；
        - 当 ``as_panel=True`` 时，返回一个 ``HistoryPanel``。

    """

    if isinstance(shares, str):
        # 允许逗号分隔的字符串形式
        share_list = [s.strip() for s in shares.split(',') if s.strip()]
    elif isinstance(shares, (list, tuple)):
        share_list = list(shares)
    else:
        raise TypeError(f'shares must be a string or a list of strings, got {type(shares)} instead')

    if not share_list:
        raise ValueError('shares can not be empty')

    # rows 与 start/end 的优先级：如给出 start/end，则忽略 rows
    if (start is not None) or (end is not None):
        rows_arg = None
    else:
        rows_arg = rows

    # 统一透传给底层 get_history_data
    gh_kwargs = dict(
        htype_names='open, high, low, close, volume',
        data_source=data_source,
        shares=','.join(share_list),
        start=start,
        end=end,
        freq=freq,
        rows=rows_arg,
        asset_type=asset_type,
        adj=adj,
    )
    if b_days_only is not None:
        gh_kwargs['b_days_only'] = b_days_only
    if trade_time_only is not None:
        gh_kwargs['trade_time_only'] = trade_time_only
    gh_kwargs.update(kwargs)

    if as_panel:
        # 直接返回 HistoryPanel，并将 'volume' 重命名为 'vol'
        hp = get_history_data(as_data_frame=False, **gh_kwargs)
        from qteasy.history import HistoryPanel  # 避免循环导入
        if isinstance(hp, HistoryPanel) and 'volume' in hp.htypes:
            new_htypes = ['vol' if h == 'volume' else h for h in hp.htypes]
            hp.re_label(htypes=new_htypes)
        return hp

    # 返回 dict[str, DataFrame]
    res = get_history_data(group_by='shares', **gh_kwargs)
    # 统一将列名 'volume' 重命名为 'vol'
    if isinstance(res, dict):
        for sh, df in res.items():
            if isinstance(df, pd.DataFrame) and 'volume' in df.columns:
                res[sh] = df.rename(columns={'volume': 'vol'})
        # 单标的时压缩为 DataFrame
        if len(share_list) == 1:
            return res[share_list[0]]
        return res

    # 理论上 group_by='shares' 应总是返回 dict，这里仅作兜底
    if isinstance(res, pd.DataFrame) and 'volume' in res.columns:
        return res.rename(columns={'volume': 'vol'})
    return res
