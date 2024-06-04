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
from warnings import warn

import datetime

import qteasy
from .history import get_history_panel, HistoryPanel
from .utilfuncs import str_to_list, regulate_date_format, match_ts_code
from .utilfuncs import next_market_trade_day
from .utilfuncs import AVAILABLE_ASSET_TYPES, _partial_lev_ratio
from .finance import CashPlan
from .qt_operator import Operator
from .visual import _plot_loop_result, _loop_report_str, _print_test_result
from .visual import _plot_test_result
from ._arg_validators import _update_config_kwargs, ConfigDict
from ._arg_validators import QT_CONFIG, _vkwargs_to_text
from .optimization import _evaluate_all_parameters, _evaluate_one_parameter


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
    try:
        date = pd.to_datetime(date)
    except:
        date = pd.to_datetime('today')
    # validate all input args:
    if not all(arg.lower() in ['index', 'industry', 'area', 'market', 'exchange'] for arg in kwargs.keys()):
        raise KeyError()
    if not all(isinstance(val, (str, list)) for val in kwargs.values()):
        raise KeyError()

    ds = qteasy.QT_DATA_SOURCE
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
    """ 等同于get_stock_info()
        根据输入的信息，查找股票、基金、指数或期货、期权的基本信息

    Parameters
    ----------
    code_or_name:
        证券代码或名称，
        如果是证券代码，可以含后缀也可以不含后缀，含后缀时精确查找、不含后缀时全局匹配
        如果是证券名称，可以包含通配符模糊查找，也可以通过名称模糊查找
        如果精确匹配到一个证券代码，返回一个字典，包含该证券代码的相关信息
    asset_types: 默认None
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
    dict
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
    matched_codes = match_ts_code(code_or_name, asset_types=asset_types, match_full_name=match_full_name)

    ds = qteasy.QT_DATA_SOURCE
    df_s, df_i, df_f, df_ft, df_o = ds.get_all_basic_table_data()
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
    code_or_name:
        证券代码或名称，
        如果是证券代码，可以含后缀也可以不含后缀，含后缀时精确查找、不含后缀时全局匹配
        如果是证券名称，可以包含通配符模糊查找，也可以通过名称模糊查找
        如果精确匹配到一个证券代码，返回一个字典，包含该证券代码的相关信息
    asset_types:
        证券类型，接受列表或逗号分隔字符串，包含认可的资产类型：
        - E     股票
        - IDX   指数
        - FD    基金
        - FT    期货
        - OPT   期权
    match_full_name: bool
        是否匹配股票或基金的全名，默认否，如果匹配全名，耗时更长
    printout: bool
        如果为True，打印匹配到的结果
    verbose: bool
        当匹配到的证券太多时（多于五个），是否显示完整的信息
        - False 默认值，只显示匹配度最高的内容
        - True  显示所有匹配到的内容

    Returns
    -------
    dict
        当仅找到一个匹配是，返回一个dict，包含找到的基本信息，根据不同的证券类型，找到的信息不同：
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


def get_table_info(table_name, data_source=None, verbose=True):
    """ 获取并打印数据源中一张数据表的信息，包括数据量、占用磁盘空间、主键名称、内容
        以及数据列的名称、数据类型及说明

    Parameters:
    -----------
    table_name: str
        需要查询的数据表名称
    data_source: DataSource
        需要获取数据表信息的数据源，默认None，此时获取QT_DATA_SOURCE的信息
    verbose: bool, Default: True，
        是否打印完整数据列名称及类型清单

    Returns
    -------
    一个tuple，包含数据表的结构化信息：
        (table name:    str, 数据表名称
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
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE
    if not isinstance(data_source, qteasy.DataSource):
        raise TypeError(f'data_source should be a DataSource, got {type(data_source)} instead.')
    return data_source.get_table_info(table=table_name, verbose=verbose)


def get_table_overview(data_source=None, tables=None, include_sys_tables=False) -> None:
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
    None

    Notes
    -----
    用法示例参见get_data_overview()
    """

    from .database import DataSource
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'A DataSource object must be passed, got {type(data_source)} instead.')

    data_source.overview(tables=tables, include_sys_tables=include_sys_tables)


def get_data_overview(data_source=None, tables=None, include_sys_tables=False) -> None:
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
    None

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


def refill_data_source(*, data_source=None, **kwargs) -> None:
    """ 填充数据数据源

    Parameters
    ----------
    data_source: DataSource, Default None
        需要填充数据的DataSource, 如果为None，则填充数据源到QT_DATA_SOURCE
    **kwargs:
     tables: str or list of str, default: None
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
     dtypes: str or list of str, default: None
         通过指定dtypes来确定需要更新的表单，只要包含指定的dtype的数据表都会被选中
         如果给出了tables，则dtypes参数会被忽略
     freqs: str, default: None
         通过指定tables或dtypes来确定需要更新的表单时，指定freqs可以限定表单的范围
         如果tables != all时，给出freq会排除掉freq与之不符的数据表
     asset_types: Str of List of Str, default: None
         通过指定tables或dtypes来确定需要更新的表单时，指定asset_types可以限定表单的范围
         如果tables != all时，给出asset_type会排除掉与之不符的数据表
     start_date: DateTime Like, default: None
         限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
     end_date: DateTime Like, default: None
         限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
     list_arg_filter: str or list of str, default: None  **注意，不是所有情况下该参数都有效**
         限定下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
         参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。
         如果filter_arg为None，则下载所有数据。
         例如，下载stock_basic表数据时，下载以下输入均为合法输入：
         - 'SZSE'
             仅下载深圳交易所的股票数据
         - ['SSE', 'SZSE']
         - 'SSE, SZSE'
             上面两种写法等效，下载上海和深圳交易所的股票数据
     symbols: str or list of str, default: None  **注意，不是所有情况下该参数都有效**
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
     merge_type: str, default: 'ignore'
         数据混合方式，当获取的数据与本地数据的key重复时，如何处理重复的数据：
         - 'ignore' 默认值，不下载重复的数据
         - 'update' 下载并更新本地数据的重复部分
     reversed_par_seq: Bool, default: False
         是否逆序参数下载数据， 默认False
         - True:  逆序参数下载数据
         - False: 顺序参数下载数据
     parallel: Bool, default: True
         是否启用多线程下载数据，默认True
         - True:  启用多线程下载数据
         - False: 禁用多线程下载
     process_count: int, default: None
         启用多线程下载时，同时开启的线程数，默认值为设备的CPU核心数
     chunk_size: int, default: 100
         保存数据到本地时，为了减少文件/数据库读取次数，将下载的数据累计一定数量后
         再批量保存到本地，chunk_size即批量，默认值100

    Returns
    -------
    None

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.refill_data_source(tables='stock_basic')

    """
    from .database import DataSource
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'A DataSource object must be passed, got {type(data_source)} instead.')
    print(f'Filling data source {data_source} ...')
    hist_dnld_delay = None
    hist_dnld_delay_evy = None
    if 'download_batch_size' not in kwargs:
        hist_dnld_delay = QT_CONFIG.hist_dnld_delay
    if 'download_batch_interval' not in kwargs:
        hist_dnld_delay_evy = QT_CONFIG.hist_dnld_delay_evy

    data_source.refill_local_source(
            download_batch_size=hist_dnld_delay_evy,
            download_batch_interval=hist_dnld_delay,
            **kwargs,
    )


def get_history_data(htypes,
                     shares=None,
                     symbols=None,
                     start=None,
                     end=None,
                     freq=None,
                     rows=10,
                     asset_type=None,
                     adj=None,
                     as_data_frame=None,
                     group_by=None,
                     **kwargs):
    """ 从本地DataSource（数据库/csv/hdf/fth）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

    Parameters
    ----------
    htypes: [str, list]
        需要获取的历史数据类型集合，可以是以逗号分隔的数据类型字符串或者数据类型字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     'open, high, low, close'
         - list:    ['open', 'high', 'low', 'close']
        特殊htypes的处理，以下特殊htypes将被特殊处理，返回特定的数，详见示例
         - wt-000300.SH:
            指数权重数据，如果htype是一个wt开头的复合体，则获取该指数的股票权重数据
            获取的数据的htypes同样为wt-000300.SH型
         - close-000300.SH:
            给出一个htype和ts_code的复合体，且shares为None时，返回不含任何share
            的参考数据
    shares: [str, list] 等同于symbols
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
         - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
    symbols: [str, list] 等同于shares
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
        - str:     '000001, 000002, 000004, 000005'
        - list:    ['000001', '000002', '000004', '000005']
    start: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
    end: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
    rows: int, default: 10
        获取的历史数据的行数，如果指定了start和end，则忽略此参数，且获取的数据的时间范围为[start, end]
        如果未指定start和end，则获取数据表中最近的rows条数据，使用row来获取数据时，速度比使用日期慢得多
    freq: str
        获取的历史数据的频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
    asset_type: str, list
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
    as_data_frame: bool, Default: False
        是否返回DataFrame对象，True时返回HistoryPanel对象
    group_by: str, 默认'shares'
        如果返回DataFrame对象，设置dataframe的分组策略
        - 'shares' / 'share' / 's': 每一个share组合为一个dataframe
        - 'htypes' / 'htype' / 'h': 每一个htype组合为一个dataframe
    **kwargs:
        用于生成trade_time_index的参数，包括：
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
    HistoryPanel:
        如果设置as_data_frame为False，则返回一个HistoryPanel对象
    Dict of DataFrame:
        如果设置as_data_frame为True，则返回一个Dict，其值为多个DataFrames

    Examples
    --------
    >>> import qteasy as qt
    # 给出历史数据类型和证券代码，起止时间，可以获取该时间段内该股票的历史数据
    >>> qt.get_history_data(htypes='open, high, low, close, vol', shares='000001.SZ', start='20191225', end='20200110')
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

    >>> # 除了股票的价格数据以外，也可以获取基金、指数的价格数据，如下面的代码获取000300.SH的指数价格数
    >>> qt.get_history_data(htypes='close', shares='000300.SH', start='20191225', end='20200105')
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
    # 以及基金的净值数据
    >>> qt.get_history_data(htypes='unit_nav, accum_nav', shares='000001.OF', start='20191225', end='20200105')
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
    >>> qt.get_history_data(htypes='close, pe, pb', shares='000001.SZ', start='20191225', end='20200105')
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
    # 可以同时混合获取多只股票、指数、多种数据类型的数据，如果某些数据类型缺失，会用NaN填充，注意000001.SZ是股票平安银行，000001.SH是上证指数
    >>> qt.get_history_data(htypes='close, pe, pb, total_mv, eps', shares='000001.SZ, 000001.SH', start='20191225', end='20200105')
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
    >>> qt.get_history_data(htypes='open, high, low, close', shares='000001.SZ', start='20191229', end='20200106', freq='H', adj='b', asset_type='E')
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
    >>> qt.get_history_data(htypes='open, high, low, close, vol', shares='000001.SZ', start='20191225', end='20200105', b_days_only=False)
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
    >>> qt.get_history_data(htypes='wt-000300.SH', shares='000001.SZ, 000002.SZ', start='20191225', end='20200105')
    {'000001.SZ':
                wt-000300.SH
    2020-01-02        1.1714
    2020-01-03        1.1714,
    '000002.SZ':
                wt-000300.SH
    2020-01-02        1.3595
    2020-01-03        1.3595
    }

    """

    if htypes is None:
        raise ValueError(f'htype should not be None')
    if symbols is not None and shares is None:
        shares = symbols
    if shares is None:
        shares = qteasy.QT_CONFIG.asset_pool

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

    if freq is None:
        freq = 'd'

    if asset_type is None:
        asset_type = 'any'

    if adj is None:
        adj = 'n'

    if as_data_frame is None:
        as_data_frame = True

    if group_by is None:
        group_by = 'shares'
    if group_by in ['shares', 'share', 's']:
        group_by = 'shares'
    elif group_by in ['htypes', 'htype', 'h']:
        group_by = 'htypes'
    hp = get_history_panel(htypes=htypes, shares=shares, start=start, end=end, freq=freq, asset_type=asset_type,
                           symbols=symbols, rows=rows, adj=adj, **kwargs)

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


def configure(config=None, reset=False, only_built_in_keys=True, **kwargs) -> None:
    """ 配置qteasy的运行参数QT_CONFIG

    Parameters
    ----------
    config: ConfigDict 对象
        需要设置或调整参数的config对象，默认为None，此时直接对QT_CONFIG对象设置参数
    reset: bool
        默认值为False，为True时忽略传入的kwargs，将所有的参数设置为默认值
    only_built_in_keys: bool
        默认值False，如果为True，仅允许传入内部参数，False时允许传入任意参数
    **kwargs:
        需要设置的所有参数

    Returns
    -------
    None

    Notes
    -----
    使用get_config()或configuration()查看当前的QT_CONFIG参数

    Examples
    --------
    >>> configure(reset=True)  # 将QT_CONFIG参数设置为默认值
    >>> configure(invest_cash_amounts=[10000, 20000, 30000], invest_cash_dates=['2018-01-01', '2018-02-01', '2018-03-01'])
    >>> get_config('invest_cash_amounts, invest_cash_dates')
    No. Config-Key            Cur Val                       Default val
    -------------------------------------------------------------------
    1   invest_cash_amounts   [10000, 20000, 30000]         <[100000.0]>
    2   invest_cash_dates     ['2018-01-01', '2018-02-01'...<None>

    """
    if config is None:
        set_cfg = QT_CONFIG
    else:
        assert isinstance(config, ConfigDict), TypeError(f'config should be a ConfigDict, got {type(config)}')
        set_cfg = config
    if not reset:
        _update_config_kwargs(set_cfg, kwargs, raise_if_key_not_existed=only_built_in_keys)
    else:
        from qteasy._arg_validators import _valid_qt_kwargs
        default_kwargs = {k: v['Default'] for k, v in zip(_valid_qt_kwargs().keys(),
                                                          _valid_qt_kwargs().values())}
        _update_config_kwargs(set_cfg, default_kwargs, raise_if_key_not_existed=True)


def set_config(config=None, reset=False, only_built_in_keys=True, **kwargs) -> None:
    """ 配置qteasy的运行参数QT_CONFIG，等同于configure()

    Parameters
    ----------
    config: ConfigDict 对象
        需要设置或调整参数的config对象，默认为None，此时直接对QT_CONFIG对象设置参数
    reset: bool
        默认值为False，为True时忽略传入的kwargs，将所有的参数设置为默认值
    only_built_in_keys: bool
        默认值False，如果为True，仅允许传入内部参数，False时允许传入任意参数
    **kwargs:
        需要设置的所有参数

    Returns
    -------
    None

    Examples
    --------
    参见 configure()
    """

    return configure(config=config, reset=reset, only_built_in_keys=only_built_in_keys, **kwargs)


def configuration(config_key=None, level=0, up_to=0, default=True, verbose=False) -> None:
    """ 显示qt当前的配置变量，

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Notes
    -----
    使用示例参见get_config()
    """
    assert isinstance(level, int) and (0 <= level <= 5), f'InputError, level should be an integer, got {type(level)}'
    assert isinstance(up_to, int) and (0 <= up_to <= 5), f'InputError, up_to level should be an integer, ' \
                                                         f'got {type(up_to)}'
    if up_to <= level:
        up_to = level
    if up_to == level:
        level = level
    else:
        level = list(range(level, up_to + 1))

    if config_key is None:
        kwargs = QT_CONFIG
    else:
        if isinstance(config_key, str):
            config_key = str_to_list(config_key)
        if not isinstance(config_key, list):
            raise TypeError(f'config_key should be a string or list of strings, got {type(config_key)}')
        assert all(isinstance(item, str) for item in config_key)
        kwargs = {key: QT_CONFIG[key] for key in config_key}
        level = [0, 1, 2, 3, 4, 5]
    print(_vkwargs_to_text(kwargs=kwargs, level=level, info=default, verbose=verbose))


def get_configurations(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，与get_config / configuration 相同

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Examples
    --------
    使用示例参见get_config()
    """

    return configuration(config_key=config_key, level=level, up_to=up_to, default=default, verbose=verbose)


def get_config(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，与get_config / configuration 相同

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Examples
    --------
    >>> get_config('local_data_source')
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   local_data_source     database       <file>

    >>> get_config('local_data_source, local_data_file_type, local_data_file_path')
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   local_data_source     database       <file>
    2   local_data_file_type  csv            <csv>
    3   local_data_file_path  data/          <data/>

    >>> get_config(level=0, up_to=2)
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   mode                  1              <1>
    2   time_zone             Asia/Shanghai  <Asia/Shanghai>
    3   asset_pool            000300.SH      <000300.SH>
    4   asset_type            IDX            <IDX>
    5   live_trade_account_id None           <None>
    6   live_trade_account    None           <None>
    7   live_trade_debug_mode False          <False>
    8   live_trade_init_cash  1000000.0      <1000000.0>
    ... (more rows)

    >>> get_config(level=0, up_to=1, verbose=True)
    No. Config-Key            Cur Val        Default val
          Description
    ----------------------------------------------------
    1   mode                  1              <1>
          qteasy 的运行模式:
          0: 实盘运行模式
          1: 回测-评价模式
          2: 策略优化模式
          3: 统计预测模式
    2   time_zone             Asia/Shanghai  <Asia/Shanghai>
          回测时的时区，可以是任意时区，例如：
          Asia/Shanghai
          Asia/Hong_Kong
          US/Eastern
          US/Pacific
          Europe/London
          Europe/Paris
          Australia/Sydney
          Australia/Melbourne
          Pacific/Auckland
          Pacific/Chatham
          etc.
    3   asset_pool            000300.SH      <000300.SH>
          可用投资产品池，投资组合基于池中的产品创建
    4   asset_type            IDX            <IDX>
          投资产品的资产类型，包括：
          IDX  : 指数
          E    : 股票
          FT   : 期货
          FD   : 基金
    """

    return configuration(config_key=config_key, level=level, up_to=up_to, default=default, verbose=verbose)


def _check_config_file_name(file_name, allow_default_name=False):
    """ 检查配置文件名是否合法，如果合法或可以转化为合法，返回合法文件名，否则raise

    parameters
    ----------
    file_name: str
        配置文件名，可以是一个文件名，也可以是不带后缀的文件名，不可以是一个路径
    allow_default_name: bool
        是否允许使用默认的配置文件名qteasy.cfg
    """

    if file_name is None:
        file_name = 'saved_config.cfg'
    if not isinstance(file_name, str):
        raise TypeError(f'file_name should be a string, got {type(file_name)} instead.')
    import re
    if re.match(r'[a-zA-Z_]\w+$', file_name):
        file_name = file_name + '.cfg'  # add .cfg suffix if not given
    if not re.match(r'[a-zA-Z_]\w+\.cfg$', file_name):
        raise ValueError(f'invalid file name given: {file_name}')
    if (file_name == 'qteasy.cfg') and (not allow_default_name):
        # TODO: 实现配置变量写入qteasy.cfg初始配置文件的功能
        raise NotImplementedError(f'"qteasy.cfg" is not an allowed file name, functionality not '
                                  f'implemented yet, please use another file name.')
    return file_name


def save_config(*, config=None, file_name=None, overwrite=True, initial_config=False) -> str:
    """ 将config保存为一个文件
    尚未实现的功能：如果initial_config为True，则将配置更新到初始化配置文件qteasy.cfg中()

    Parameters
    ----------
    config: ConfigDict or dict, Default: None
        一个config对象或者包含配配置变量的dict，如果为None，则保存qt.QT_CONFIG
    file_name: str, Default: None
        文件名，如果为None，文件名为"saved_config.cfg"
    overwrite: bool, Default: True
        默认True，覆盖重名文件，如果为False，当保存的文件已存在时，将报错
    initial_config: bool, Default: False ** FUNCTIONALITY NOT IMPLEMENTED **
        保配置变量到初始配置文件 qteasy.cfg 中，如果qteasy.cfg中已经存在部配置变量了，则覆盖相配置变量
        TODO: 实现将配置变量写入qteasy.cfg初始配置文件的功能
         由于目前使用pickle写入对象为二进制文件，而qteasy.cfg是文本文件，所以需要实现一个新的写入方式

    Returns
    -------
    file_name: str
        保存的文件名
    """

    from qteasy import logger_core
    from qteasy import QT_ROOT_PATH
    import pickle
    import os

    if config is None:
        config = QT_CONFIG
    if not isinstance(config, (ConfigDict, dict)):
        raise TypeError(f'config should be a ConfigDict or a dict, got {type(config)} instead.')

    file_name = _check_config_file_name(file_name=file_name, allow_default_name=initial_config)

    config_path = os.path.join(QT_ROOT_PATH, '../config/')
    if not os.path.exists(config_path):
        os.makedirs(config_path, exist_ok=False)
    if overwrite:
        open_method = 'wb'  # overwrite the file
    else:
        open_method = 'xb'  # raise if file already existed
    with open(os.path.join(config_path, file_name), open_method) as f:
        try:
            pickle.dump(config, f, pickle.HIGHEST_PROTOCOL)
            logger_core.info(f'config file content written to: {f.name}')
            return f.name
        except Exception as e:
            logger_core.warning(f'{e}, error during writing config to local file.')
            return ""


def load_config(*, config=None, file_name=None) -> dict:
    """ 从文件file_name中读取相应的config参数，写入到config中，如果config为
        None，则保存参数到QT_CONFIG中

    Parameters
    ----------
    config: ConfigDict 对象
        一个config对象，默认None，如果不为None且为一个ConfigDict对象，则将读取的配置参数写入到config中
    file_name: str
        文件名，默认None，如果为None，文件名为saved_config.cfg

    Returns
    -------
    config: dict
        读取的配置参数

    Raises
    ------
    FileNotFoundError
        如果给定文件不存在，则报错。如果没有给定文件名，则当config/saved_config.cfg不存在时，报错
    """
    from qteasy import logger_core
    from qteasy import QT_ROOT_PATH
    import pickle

    file_name = _check_config_file_name(file_name=file_name, allow_default_name=False)

    config_path = os.path.join(QT_ROOT_PATH, '../config/')
    try:
        with open(os.path.join(config_path, file_name), 'rb') as f:
            saved_config = pickle.load(f)
            logger_core.info(f'read configuration file: {f.name}')
    except FileNotFoundError as e:
        msg = f'{e}\nConfiguration file {file_name} not found! nothing will be read.'
        logger_core.warning(msg)
        saved_config = {}

    if config is not None:
        if not isinstance(config, ConfigDict):
            msg = f'config should be a ConfigDict, got {type(config)} instead.'
            raise TypeError(msg)
        configure(config=config,
                  only_built_in_keys=False,
                  **saved_config)

    return saved_config


def view_config_files(details=False) -> None:
    """ 查看已经保存的配置文件，并显示其主要内容

    Parameters
    ----------
    details: bool, Default: False
        是否显示配置文件的详细内容

    Returns
    -------
    None

    Notes
    -----
    该函数只显示config文件夹下的配置文件，不显示qteasy.cfg中的配置
    """

    # TODO: add unittests
    # 1. list all files in config folder
    # 2. read each file and display its content if details is True
    # 3. display only file names if details is False

    from qteasy import QT_ROOT_PATH
    import pickle

    config_path = os.path.join(QT_ROOT_PATH, '../config/')

    files = os.listdir(config_path)
    files = [f for f in files if f.endswith('.cfg')]

    if len(files) == 0:
        print('No config files found in config folder.')

    if details:
        for file in files:
            with open(os.path.join(config_path, file), 'rb') as f:
                config = pickle.load(f)
            print(f'File: {file}')
            print(config)

    else:
        print('Config files found in config folder:')
        for file in files:
            print(file)


def reset_config(config=None):
    """ 重设config对象，将所有的参数都设置为默认值
        如果config为None，则重设qt.QT_CONFIG

    Parameters
    ----------
    config: ConfigDict
        需要重设的config对象

    Returns
    -------
    None

    Notes
    -----
    等同于调用configure(config, reset=True)
    """
    from qteasy import logger_core
    if config is None:
        config = QT_CONFIG
    if not isinstance(config, ConfigDict):
        raise TypeError(f'config should be a ConfigDict, got {type(config)} instead.')
    logger_core.info(f'{config} is now reset to default values.')
    configure(config, reset=True)


def live_trade_accounts() -> pd.DataFrame:
    """ 获取当前所有实盘交易账户的详细信息

    Returns
    -------
    all_accounts: pd.DataFrame
        包含所有实盘交易账户信息的DataFrame
    """
    from qteasy.trade_recording import get_all_accounts
    return get_all_accounts(qteasy.QT_DATA_SOURCE)


# TODO: Bug检查：
#   在使用AlphaSel策略，如下设置参数时，会产生数据长度不足错误：
#   strategy_run_freq='m',
#   data_freq='m',
#   window_length=6,
def check_and_prepare_hist_data(oper, config, datasource=None):
    """ 根据config参数字典中的参数，下载或读取所需的历史数据以及相关的投资资金计划

    Parameters
    ----------
    oper: Operator，
        需要设置数据的Operator对象
    config: ConfigDict
        用于设置Operator对象的环境参数变量
    datasource: DataSource
        用于下载数据的DataSource对象

    Returns
    -------
    hist_op: HistoryPanel,
        用于回测模式下投资策略生成的历史数据区间，包含多只股票的多种历史数据
    hist_ref: HistoryPanel,
        用于回测模式下投资策略生成的历史参考数据
    back_trade_prices: HistoryPanel,
        用于回测模式投资策略回测的交易价格数据
    hist_opti: HistoryPanel,
        用于优化模式下生成投资策略的历史数据，包含股票的历史数，时间上涵盖优化与测试区间
    hist_opti_ref: HistoryPanel,
        用于优化模式下生成投资策略的参考数据，包含所有股票、涵盖优化与测试区间
    opti_trade_prices: pd.DataFrame,
        用于策略优化模式下投资策略优化结果的回测，作为独立检验数据
    hist_benchmark: pd.DataFrame,
        用于评价回测结果的同期基准收益曲线，一般为股票指数如HS300指数同期收益曲线
    invest_cash_plan: CashPlan,
        用于回测模式的资金投入计划
    opti_cash_plan: CashPlan,
        用于优化模式下，策略优化区间的资金投入计划
    test_cash_plan: CashPlan,
        用于优化模式下，策略测试区间的资金投入计划
    """
    run_mode = config['mode']
    # 如果run_mode=0，设置历史数据的开始日期为window length，结束日期为当前日期
    current_datetime = datetime.datetime.now()
    # 根据不同的运行模式，设定不同的运行历史数据起止日期
    # 投资回测区间的开始日期根据invest_start和invest_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['invest_cash_dates'] is None:
        invest_start = next_market_trade_day(config['invest_start']).strftime('%Y%m%d')
        invest_cash_plan = CashPlan(invest_start,
                                    config['invest_cash_amounts'][0],
                                    config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['invest_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        invest_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                    amounts=config['invest_cash_amounts'],
                                    interest_rate=config['riskfree_ir'])
        invest_start = regulate_date_format(invest_cash_plan.first_day)
        if pd.to_datetime(invest_start) != pd.to_datetime(config['invest_start']):
            warn(
                f'first cash investment on {invest_start} differ from invest_start {config["invest_start"]}, first cash'
                f' date will be used!',
                RuntimeWarning)
    # 按照同样的逻辑设置优化区间和测试区间的起止日期
    # 优化区间开始日期根据opti_start和opti_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['opti_cash_dates'] is None:
        opti_start = next_market_trade_day(config['opti_start']).strftime('%Y%m%d')
        opti_cash_plan = CashPlan(opti_start,
                                  config['opti_cash_amounts'][0],
                                  config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['opti_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        opti_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                  amounts=config['opti_cash_amounts'],
                                  interest_rate=config['riskfree_ir'])
        opti_start = regulate_date_format(opti_cash_plan.first_day)
        if pd.to_datetime(opti_start) != pd.to_datetime(config['opti_start']):
            warn(f'first cash investment on {opti_start} differ from invest_start {config["opti_start"]}, first cash'
                 f' date will be used!',
                 RuntimeWarning)

    # 测试区间开始日期根据opti_start和opti_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['test_cash_dates'] is None:
        test_start = next_market_trade_day(config['test_start']).strftime('%Y%m%d')
        test_cash_plan = CashPlan(
                test_start,
                config['test_cash_amounts'][0],
                config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['test_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        test_cash_plan = CashPlan(
                dates=adjusted_cash_dates,
                amounts=config['test_cash_amounts'],
                interest_rate=config['riskfree_ir'])
        test_start = regulate_date_format(test_cash_plan.first_day)
        if pd.to_datetime(test_start) != pd.to_datetime(config['test_start']):
            warn(f'first cash investment on {test_start} differ from invest_start {config["test_start"]}, first cash'
                 f' date will be used!',
                 RuntimeWarning)

    # 设置历史数据前置偏移，以便有足够的历史数据用于生成最初的信号
    window_length = oper.max_window_length
    window_offset_freq = oper.op_data_freq
    if isinstance(window_offset_freq, list):
        raise NotImplementedError(f'There are more than one data frequencies in operator ({window_offset_freq}), '
                                  f'multiple data frequency in one operator is currently not supported')
    if window_offset_freq.lower() not in ['d', 'w', 'm', 'q', 'y']:
        from qteasy.utilfuncs import parse_freq_string
        duration, base_unit, _ = parse_freq_string(window_offset_freq, std_freq_only=True)
        # print(f'[DEBUG]: in core.py function check_and_prepare_hist_data(), '
        #       f'window_offset_freq is {window_offset_freq}\n'
        #       f'it should be converted to {duration} {base_unit}, '
        #       f'and window_length and window_offset_freq should be \n'
        #       f'adjusted accordingly: \n'
        #       f'window_length: {window_length} -> {window_length * duration * 3}\n'
        #       f'window_offset_freq: {window_offset_freq} -> {base_unit}')
        window_length *= duration * 10  # 临时处理措施，由于交易时段不连续，仅仅前推一个周期可能会导致数据不足
        window_offset_freq = base_unit
    window_offset = pd.Timedelta(int(window_length * 1.6), window_offset_freq)

    # 设定投资结束日期
    if run_mode == 0:
        # 实时模式下，设置结束日期为现在，并下载最新的数据（下载的数据仅包含最小所需）
        invest_end = regulate_date_format(current_datetime)
        # 开始日期时间为现在往前推window_offset
        invest_start = regulate_date_format(current_datetime - window_offset)
    else:
        invest_end = config['invest_end']
        invest_start = regulate_date_format(pd.to_datetime(invest_start) - window_offset)

    # debug
    # 检查invest_start是否正确地被前溯了window_offset
    # print(f'[DEBUG]: in core.py function check_and_prepare_hist_data(), extracting data from window_length earlier '
    #       f'than invest_start: \n'
    #       f'current run mode: {run_mode}\n'
    #       f'current_date = {current_datetime}\n'
    #       f'window_offset = {window_offset}\n'
    #       f'invest_start = {invest_start}\n'
    #       f'invest_end = {invest_end}\n')
    # 设置优化区间和测试区间的结束日期
    opti_end = config['opti_end']
    test_end = config['test_end']

    # 优化/测试数据是合并读取的，因此设置一个统一的开始/结束日期：
    # 寻优开始日期为优化开始和测试开始日期中较早者，寻优结束日期为优化结束和测试结束日期中较晚者
    opti_test_start = opti_start if pd.to_datetime(opti_start) < pd.to_datetime(test_start) else test_start
    opti_test_end = opti_end if pd.to_datetime(opti_end) > pd.to_datetime(test_end) else test_end

    # 合并生成交易信号和回测所需历史数据，数据类型包括交易信号数据和回测价格数据
    hist_op = get_history_panel(
            htypes=oper.all_price_and_data_types,
            shares=config['asset_pool'],
            start=invest_start,
            end=invest_end,
            freq=oper.op_data_freq,
            asset_type=config['asset_type'],
            adj=config['backtest_price_adj'] if run_mode > 0 else 'none',
            data_source=datasource,
    ) if run_mode <= 1 else HistoryPanel()  # TODO: 当share较多时，运行速度非常慢，需要优化
    # 解析参考数据类型，获取参考数据
    hist_ref = get_history_panel(
            htypes=oper.op_ref_types,
            shares=None,
            start=regulate_date_format(pd.to_datetime(invest_start) - window_offset),  # TODO: 已经offset过了，为什么还要offset？
            end=invest_end,
            freq=oper.op_data_freq,
            asset_type='IDX',
            adj='none',
            data_source=datasource,
    ) if run_mode <= 1 else HistoryPanel()
    # 生成用于数据回测的历史数据，格式为HistoryPanel，包含用于计算交易结果的所有历史价格种类
    bt_price_types = oper.strategy_timings
    back_trade_prices = hist_op.slice(htypes=bt_price_types)
    # fill np.inf in back_trade_prices to prevent from result in nan in value
    back_trade_prices.fillinf(0)

    # 生成用于策略优化训练的训练和测试历史数据集合和回测价格类型集合
    hist_opti = get_history_panel(
            htypes=oper.all_price_and_data_types,
            shares=config['asset_pool'],
            start=regulate_date_format(pd.to_datetime(opti_test_start) - window_offset),
            end=opti_test_end,
            freq=oper.op_data_freq,
            asset_type=config['asset_type'],
            adj=config['backtest_price_adj'],
            data_source=datasource,
    ) if run_mode == 2 else HistoryPanel()

    # 生成用于优化策略测试的测试历史数据集合
    hist_opti_ref = get_history_panel(
            htypes=oper.op_ref_types,
            shares=None,
            start=regulate_date_format(pd.to_datetime(opti_test_start) - window_offset),
            end=opti_test_end,
            freq=oper.op_data_freq,
            asset_type=config['asset_type'],
            adj=config['backtest_price_adj'],
            data_source=datasource,
    ) if run_mode == 2 else HistoryPanel()

    opti_trade_prices = hist_opti.slice(htypes=bt_price_types)
    opti_trade_prices.fillinf(0)

    # 生成参考历史数据，作为参考用于回测结果的评价
    # 评价数据的历史区间应该覆盖invest/opti/test的数据区间
    all_starts = [pd.to_datetime(date_str) for date_str in [invest_start, opti_start, test_start]]
    all_ends = [pd.to_datetime(date_str) for date_str in [invest_end, opti_end, test_end]]
    benchmark_start = regulate_date_format(min(all_starts))
    benchmark_end = regulate_date_format(max(all_ends))

    hist_benchmark = get_history_panel(
            htypes=config['benchmark_dtype'],
            shares=config['benchmark_asset'],
            start=benchmark_start,
            end=benchmark_end,
            freq=oper.op_data_freq,
            asset_type=config['benchmark_asset_type'],
            adj=config['backtest_price_adj'],
            data_source=datasource,
    ).slice_to_dataframe(htype=config['benchmark_dtype'])

    return hist_op, hist_ref, back_trade_prices, hist_opti, hist_opti_ref, opti_trade_prices, hist_benchmark, \
        invest_cash_plan, opti_cash_plan, test_cash_plan


def reconnect_ds(data_source=None):  # deprecated
    """ （当数据库连接超时时）重新连接到data source，如果不指定具体的data_source，则重新连接默认数据源

    Parameters
    ----------
    data_source:
        需要重新连接的datasource对象

    Returns
    -------
    """
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE

    if not isinstance(data_source, qteasy.DataSource):
        raise TypeError(f'data source not recognized!')

    # reconnect twice to make sure the connection is established
    data_source.reconnect()
    data_source.reconnect()


def check_and_prepare_live_trade_data(operator, config, datasource=None, live_prices=None):
    """ 在run_mode == 0的情况下准备相应的历史数据

    Parameters
    ----------
    operator: Operator
        需要设置数据的Operator对象
    config: ConfigDict
        用于设置Operator对象的环境参数变量
    datasource: DataSource
        用于下载数据的DataSource对象
    live_prices: pd.DataFrame, optional
        用于实盘交易的最新价格数据，如果不提供，则从datasource中下载获取

    Returns
    -------
    hist_op: HistoryPanel
        用于回测的历史数据，包含用于计算交易结果的所有历史价格种类
    hist_ref: HistoryPanel
        用于回测的历史参考数据，包含用于计算交易结果的所有历史参考数据
    """

    run_mode = config['mode']
    if run_mode != 0:
        raise ValueError(f'run_mode should be 0, but {run_mode} is given!')
    # 合并生成交易信号和回测所需历史数据，数据类型包括交易信号数据和回测价格数据
    hist_op = get_history_panel(
            htypes=operator.all_price_and_data_types,
            shares=config['asset_pool'],
            rows=operator.max_window_length,
            freq=operator.op_data_freq,
            asset_type=config['asset_type'],
            adj='none',
            data_source=datasource,
    )  # TODO: this function get_history_panel() is extremely slow, need to be optimized

    # 解析参考数据类型，获取参考数据
    hist_ref = get_history_panel(
            htypes=operator.op_ref_types,
            shares=None,
            rows=operator.max_window_length,
            freq=operator.op_data_freq,
            asset_type=config['asset_type'],
            adj='none',
            data_source=datasource,
    )
    if any(
            (stg.strategy_run_freq.upper() in ['D', 'W', 'M']) and
            stg.use_latest_data_cycle
            for stg
            in operator.strategies
    ):  # 如果有任何一个策略需要估算当前周期的数据
        # 从hist_op的index中找到日期序列，最后一个日期是prev_cycle_end, 根据日期序列计算本cycle的开始和结束日期
        prev_cycle_date = hist_op.hdates[-1]

        latest_cycle_date = next_market_trade_day(
                prev_cycle_date,
                nearest_only=False,
        )

        extended_op_values = np.zeros(shape=(hist_op.shape[0], 1, hist_op.shape[2]))
        extended_ref_values = np.zeros(shape=(hist_ref.shape[0], 1, hist_ref.shape[2]))
        # 如果需要估算当前的除open/high/low/close/volume以外的其他数据：
        # 直接沿用上一周期的数据
        # 将hist_op和ref最后一行的数据复制到extended_op_values和extended_ref_values中,作为默认值
        extended_op_values[:, 0, :] = hist_op.values[:, -1, :]
        if not hist_ref.is_empty:
            extended_ref_values[:, 0, :] = hist_ref.values[:, -1, :]

        # 如果没有给出live_prices，则使用eastmoney的stock_live_kline_price获取当前周期的最新数据
        if live_prices is None:
            from qteasy.emfuncs import stock_live_kline_price
            live_kline_prices = stock_live_kline_price(
                    symbols=hist_op.shares,
                    freq=operator.op_data_freq,
            )
            live_kline_prices.set_index('symbol', inplace=True)
        else:
            live_kline_prices = live_prices
        # 将live_kline_prices中的数据填充到extended_op_values和extended_ref_values中
        live_kline_prices = live_kline_prices.reindex(index=hist_op.shares)
        for i, htype in enumerate(hist_op.htypes):
            if htype in live_kline_prices.columns:
                extended_op_values[:, 0, i] = live_kline_prices[htype].values

        # 将extended_hist_op和extended_hist_ref添加到hist_op和hist_ref中
        extended_hist_op = HistoryPanel(
                values=extended_op_values,
                levels=hist_op.shares,
                rows=[latest_cycle_date],
                columns=hist_op.htypes,
        )
        hist_op = hist_op.join(extended_hist_op, same_shares=True, same_htypes=True)
        if not hist_ref.is_empty:
            extended_hist_ref = HistoryPanel(
                    values=extended_ref_values,
                    levels=hist_ref.shares,
                    rows=[latest_cycle_date],
                    columns=hist_ref.htypes,
            )
            hist_ref = hist_ref.join(extended_hist_ref, same_shares=True, same_htypes=True)

    return hist_op, hist_ref


def check_and_prepare_backtest_data(operator, config, datasource=None):
    """ 在run_mode == 1的回测模式情况下准备相应的历史数据

    Returns
    -------
    """
    (hist_op,
     hist_ref,
     back_trade_prices,
     hist_opti,
     hist_opti_ref,
     opti_trade_prices,
     hist_benchmark,
     invest_cash_plan,
     opti_cash_plan,
     test_cash_plan
     ) = check_and_prepare_hist_data(operator, config, datasource)

    return hist_op, hist_ref, back_trade_prices, hist_benchmark, invest_cash_plan


def check_and_prepare_optimize_data(operator, config, datasource=None):
    """ 在run_mode == 2的策略优化模式情况下准备相应的历史数据

    Parameters
    ----------
    operator: qteasy.Operator
        运算器对象
    config: qteasy.Config
        配置对象
    datasource: qteasy.DataSource
        数据源对象

    Returns
    -------
    """
    (hist_op,
     hist_ref,
     back_trade_prices,
     hist_opti,
     hist_opti_ref,
     opti_trade_prices,
     hist_benchmark,
     invest_cash_plan,
     opti_cash_plan,
     test_cash_plan
     ) = check_and_prepare_hist_data(operator, config, datasource)

    return hist_opti, hist_opti_ref, opti_trade_prices, hist_benchmark, opti_cash_plan, test_cash_plan


# noinspection PyTypeChecker
def run(operator, **kwargs):
    """ `qteasy`模块的主要入口函数

    接受`operator`执行器对象作为主要的运行组件，根据输入的运行模式确定运行的方式和结果
    根据QT_CONFIG配置变量中的设置和运行模式（mode）进行不同的操作：

    mode == 0, live trade mode, 实盘交易模式：
        一旦启动此模式，就会在terminal中启动一个单独的线程在后台运行，运行的时机也是跟真实的股票市场一致的，股票市场收市的时
        候不运行，交易日早上9点15分唤醒系统开始拉取实时股价，9点半开始运行交易策略，交易策略的运行时机和运行频率在策略的属性中
        设置。如果策略运行的结果产生交易信号，则根据交易信号模拟挂单，挂单成交后修改响应账户资金和股票持仓，交易费用按照设置中
        的费率扣除。如果资金不足或持仓不足会导致交易失败，当天买入的股票同真实市场一样T+1交割，第二个交易日开始前交割完毕。

        `Qteasy`的实盘运行有一个“账户”的概念，就跟您在股票交易市场开户一样，一个账户可以有自己的持有资金，股票持仓，单独
        计算盈亏。运行过程中您可以随时终止程序，这时所有的交易记录都会保存下来，下次重新启动时，只要引用上一次运行使用的
        账户ID（account ID）就可以从上次中断的地方继续运行了，因此启动时需要指定账户，如果不想继续上次的账户，可以新开一个账户运行。

    mode == 1, backtest mode, 回测模式，根据历史数据生成交易信号，执行交易：
        根据Config规定的回测区间，使用History模块联机读取或从本地读取覆盖整个回测区间的历史数据
        生成投资资金模型，模拟在回测区间内使用投资资金模型进行模拟交易的结果
        输出对结果的评价（使用多维度的评价方法）
        输出回测日志·
        投资资金模型不能为空，策略参数不能为空

        根据执行器历史数据hist_op，应用operator执行器对象中定义的投资策略生成一张投资产品头寸及仓位建议表。
        这张表的每一行内的数据代表在这个历史时点上，投资策略建议对每一个投资产品应该持有的仓位。每一个历史时点的数据都是根据这个历史时点的
        相对历史数据计算出来的。这张投资仓位建议表的历史区间受Config上下文对象的"loop_period_start, loop_period_end, loop_period_freq"
        等参数确定。
        同时，这张投资仓位建议表是由operator执行器对象在hist_op策略生成历史数据上生成的。hist_op历史数据包含所有用于生成策略运行结果的信息
        包括足够的数据密度、足够的前置历史区间以及足够的历史数据类型（如不同价格种类、不同财报指标种类等）
        operator执行器对象接受输入的hist_op数据后，在数据集合上反复循环运行，从历史数据中逐一提取出一个个历史片段，根据这个片段生成一个投资组合
        建议，然后把所有生成的投资组合建议组合起来形成完整的投资组合建议表。

        投资组合建议表生成后，系统在整个投资组合建议区间上比较前后两个历史时点上的建议持仓份额，当发生建议持仓份额变动时，根据投资产品的类型
        生成投资交易信号，包括交易方向、交易产品和交易量。形成历史交易信号表。

        历史交易信号表生成后，系统在相应的历史区间中创建hist_loop回测历史数据表，回测历史数据表包含对回测操作来说必要的历史数据如股价等，然后
        在hist_loop的历史数据区间上对每一个投资交易信号进行模拟交易，并且逐个生成每个交易品种的实际成交量、成交价格、交易费用（通过Rate类估算）
        以及交易前后的持有资产数量和持有现金数量的变化，以及总资产的变化。形成一张交易结果清单。交易模拟过程中的现金投入过程通过CashPlan对象来
        模拟。

        因为交易结果清单是根据有交易信号的历史交易日上计算的，因此并不完整。根据完整的历史数据，系统可以将数据补充完整并得到整个历史区间的
        每日甚至更高频率的投资持仓及总资产变化表。完成这张表后，系统将在这张总资产变化表上执行完整的回测结果分析，分析的内容包括：
            1，total_investment                      总投资
            2，total_final_value                     投资期末总资产
            3，loop_length                           投资模拟区间长度
            4，total_earning                         总盈亏
            5，total_transaction_cost                总交易成本
            6，total_open                            总开仓次数
            7，total_close                           总平仓次数
            8，total_return_rate                     总收益率
            9，annual_return_rate                    总年化收益率
            10，reference_return                     基准产品总收益
            11，reference_return_rate                基准产品总收益率
            12，reference_annual_return_rate         基准产品年化收益率
            13，max_retreat                          投资期最大回测率
            14，Karma_rate                           卡玛比率
            15，Sharp_rate                           夏普率
            16，win_rate                             胜率

        上述所有评价结果和历史区间数据能够以可视化的方式输出到图表中。同时回测的结果数据和回测区间的每一次模拟交易记录也可以被记录到log对象中
        保存在磁盘上供未来调用

    mode == 2, optimization mode, 优化模式，使用一段历史数据区间内的数据来寻找最优的策略参数组合，然后在另一段历史数据区间内进行回测，评价:
        策略优化模式：
        根据Config规定的优化区间和回测区间，使用History模块联机读取或本地读取覆盖整个区间的历史数据
        生成待优化策略的参数空间，并生成投资资金模型
        使用指定的优化方法在优化区间内查找投资资金模型的全局最优或局部最优参数组合集合
        使用在优化区间内搜索到的全局最优策略参数在回测区间上进行多次回测并再次记录结果
        输出最优参数集合在优化区间和回测区间上的评价结果
        输出优化及回测日志
        投资资金模型不能为空，策略参数可以为空

        优化模式的目的是寻找能让策略的运行效果最佳的参数或参数组合。
        寻找能使策略的运行效果最佳的参数组合并不是一件容易的事，因为我们通常认为运行效果最佳的策略是能在"未来"实现最大收益的策略。但是，鉴于
        实际上要去预测未来是不可能的，因此我们能采取的优化方法几乎都是以历史数据——也就是过去的经验——为基础的，并且期望通过过去的历史经验
        达到某种程度上"预测未来"的效果。

        策略优化模式或策略优化器的工作方法就基于这个思想，如果某个或某组参数使得某个策略的在过去足够长或者足够有代表性的历史区间内表现良好，
        那么很有可能它也能在有限的未来不大会表现太差。因此策略优化模式的着眼点完全在于历史数据——所有的操作都是通过解读历史数据，或者策略在历史数据
        上的表现来评判一个策略的优劣的，至于如何找到对策略的未来表现有更大联系的历史数据或表现形式，则是策略设计者的责任。策略优化器仅仅
        确保找出的参数组合在过去有很好的表现，而对于未来无能为力。

        优化器的工作基础在于历史数据。它的工作方法从根本上来讲，是通过检验不同的参数在同一组历史区间上的表现来评判参数的优劣的。优化器的
        工作方法可以大体上分为以下两类：

        1，无监督方法类：这一类方法不需要事先知道"最优"或先验信息，从未知开始搜寻最佳参数。这类方法需要大量生成不同的参数组合，并且
        在同一个历史区间上反复回测，通过比较回测的结果而找到最优或较优的参数。这一类优化方法的假设是，如果这一组参数在过去取得了良好的
        投资结果，那么很可能在未来也不会太差。
        这一类方法包括：
            1，Grid_searching                        网格搜索法：

                网格法是最简单和直接的参数优化方法，在已经定义好的参数空间中，按照一定的间隔均匀地从向量空间中取出一系列的点，
                逐个在优化空间中生成交易信号并进行回测，把所有的参数组合都测试完毕后，根据目标函数的值选择排名靠前的参数组合即可。

                网格法能确保找到参数空间中的全剧最优参数，不过必须逐一测试所有可能的参数点，因此计算量相当大。同时，网格法只
                适用于非连续的参数空间，对于连续空间，仍然可以使用网格法，但无法真正"穷尽"所有的参数组合

                关于网格法的具体参数和输出，参见self._search_grid()函数的docstring

            2，Montecarlo_searching                  蒙特卡洛法

                蒙特卡洛法与网格法类似，也需要检查并测试参数空间中的大量参数组合。不过在蒙特卡洛法中，参数组合是从参数空间中随机
                选出的，而且在参数空间中均匀分布。与网格法相比，蒙特卡洛方法不仅更适合于连续参数空间、通常情况下也有更好的性能。

                关于蒙特卡洛方法的参数和输出，参见self._search_montecarlo()函数的docstring

                3，Incremental_step_searching            递进搜索法

                递进步长法的基本思想是对参数空间进行多轮递进式的搜索，每一轮搜索方法与蒙特卡洛法相同但是每一轮搜索后都将搜索
                范围缩小到更希望产生全局最优的子空间中，并在这个较小的子空间中继续使用蒙特卡洛法进行搜索，直到该子空间太小、
                或搜索轮数大于设定值为止。

                使用这种技术，在一个250*250*250的空间中，能够把搜索量从15,000,000降低到10,000左右,缩减到原来的1/1500，
                却不太会影响最终搜索的效果。

                关于递进步长法的参数和输出，参见self._search_incremental()函数的docstring

            4，Genetic_Algorithm                     遗传算法 （尚未实现）

                遗传算法适用于"超大"参数空间的参数寻优。对于有二到三个参数的策略来说，使用蒙特卡洛或网格法是可以承受的选择，
                如果参数数量增加到4到5个，递进步长法可以帮助降低计算量，然而如果参数有数百个，而且每一个都有无限取值范围的时
                候，任何一种基于网格的方法都没有应用的意义了。如果目标函数在参数空间中是连续且可微的，可以使用基于梯度的方法，
                但如果目标函数不可微分，GA方法提供了一个在可以承受的时间内找到全局最优或局部最优的方法。

                GA方法受生物进化论的启发，通过模拟生物在自然选择下的基因进化过程，在复杂的超大参数空间中搜索全局最优或局部最
                优参数。GA的基本做法是模拟一个足够大的"生物"种群在自然环境中的演化，这些生物的"基因"是参数空间中的一个点，
                在演化过程中，种群中的每一个个体会发生变异、也会通过杂交来改变或保留自己的"基因"，并把变异或杂交后的基因传递到
                下一代。在每一代的种群中，优化器会计算每一个个体的目标函数并根据目标函数的大小确定每一个个体的生存几率和生殖几
                率。由于表现较差的基因生存和生殖几率较低，因此经过数万乃至数十万带的迭代后，种群中的优秀基因会保留并演化出更
                加优秀的基因，最终可能演化出全局最优或至少局部最优的基因。

                关于遗传算法的详细参数和输出，参见self._search_ga()函数的docstring

            5, Gradient Descendent Algorithm        梯度下降算法 （尚未实现）

                梯度下降算法

        2，有监督方法类：这一类方法依赖于历史数据上的（有用的）先验信息：比如过去一个区间上的已知交易信号、或者价格变化信息。然后通过
        优化方法寻找历史数据和有用的先验信息之间的联系（目标联系）。这一类优化方法的假设是，如果这些通过历史数据直接获取先验信息的
        联系在未来仍然有效，那么我们就可能在未来同样根据这些联系，利用已知的数据推断出对我们有用的信息。
        这一类方法包括：
            1，ANN_based_methods                     基于人工神经网络的有监督方法（尚未实现）
            2，SVM                                   支持向量机类方法（尚未实现）
            3，KNN                                   基于KNN的方法（尚未实现）

        为了实现上面的方法，优化器需要两组历史数据，分别对应两个不同的历史区间，一个是优化区间，另一个是回测区间。在优化的第一阶段，优化器
        在优化区间上生成交易信号，或建立目标联系，并且在优化区间上找到一个或若干个表现最优的参数组合或目标联系，接下来，在优化的第二阶段，
        优化器在回测区间上对寻找到的最优参数组合或目标联系进行测试，在回测区间生成对所有中选参数的“独立”表现评价。通常，可以选择优化区间较
        长且较早，而回测区间较晚而较短，这样可以模拟根据过去的信息建立的策略在未来的表现。

        优化器的优化过程首先开始于一个明确定义的参数"空间"。参数空间在系统中定义为一个Space对象。如果把策略的参数用向量表示，空间就是所有可能
        的参数组合形成的向量空间。对于无监督类方法来说，参数空间容纳的向量就是交易信号本身或参数本身。而对于有监督算法，参数空间是将历史数据
        映射到先验数据的一个特定映射函数的参数空间，例如，在ANN方法中，参数空间就是神经网络所有神经元连接权值的可能取值空间。优化器的工作本质
        就是在这个参数空间中寻找全局最优解或局部最优解。因此理论上所有的数值优化方法都可以用于优化器。

        优化器的另一个重要方面是目标函数。根据目标函数，我们可以对优化参数空间中的每一个点计算出一个目标函数值，并根据这个函数值的大小来评判
        参数的优劣。因此，目标函数的输出应该是一个实数。对于无监督方法，目标函数与参数策略的回测结果息息相关，最直接的目标函数就是投资终值，
        当初始投资额相同的时候，我们可以简单地认为终值越高，则参数的表现越好。但目标函数可不仅仅是终值一项，年化收益率或收益率、夏普率等等
        常见的评价指标都可以用来做目标函数，甚至目标函数可以用复合指标，如综合考虑收益率、交易成本、最大回撤等指标的一个复合指标，只要目标函数
        的输出是一个实数，就能被用作目标函数。而对于有监督方法，目标函数表征的是从历史数据到先验信息的映射能力，通常用实际输出与先验信息之间
        的差值的函数来表示。在机器学习和数值优化领域，有多种函数可选，例如MSE函数，CrossEntropy等等。
    Config.mode == 3 or mode == 3:
        进入评价模式（技术冻结后暂停开发此功能）
        评价模式的思想是使用随机生成的模拟历史数据对策略进行评价。由于可以使用大量随机历史数据序列进行评价，因此可以得到策略的统计学
        表现

    Parameters
    ----------
    operator : Operator
        策略执行器对象
    **kwargs:
        可用的kwargs包括所有合法的qteasy配置参数，参见qteasy文档

    Returns
    -------
        1, 在live_trade模式或模式0下，进入实盘交易Shell
        2, 在back_test模式或模式1下, 返回: loop_result
        3, 在optimization模式或模式2下: 返回一个list，包含所有优化后的策略参数
    """

    try:
        # 如果operator尚未准备好,is_ready()会检查汇总所有问题点并raise
        operator.is_ready()
    except Exception as e:
        raise ValueError(f'operator object is not ready for running, please check following info:\n'
                         f'{e}')
    from .optimization import _search_ga, _search_aco, _search_pso, _search_grid, _search_gradient
    from .optimization import _search_montecarlo, _search_incremental, _create_mock_data
    optimization_methods = {0: _search_grid,
                            1: _search_montecarlo,
                            2: _search_incremental,
                            3: _search_ga,
                            4: _search_gradient,
                            5: _search_pso,
                            6: _search_aco
                            }
    # 如果函数调用时用户给出了关键字参数(**kwargs），将关键字参数赋值给一个临时配置参数对象，
    # 覆盖QT_CONFIG的设置，但是仅本次运行有效
    config = ConfigDict(**QT_CONFIG)
    configure(config=config, **kwargs)

    # 赋值给参考数据和运行模式
    benchmark_data_type = config['benchmark_asset']
    run_mode = config['mode']

    if run_mode == 0 or run_mode == 'live':
        # 进入实时信号生成模式:
        from qteasy.trader import start_trader_ui
        from qteasy import QT_DATA_SOURCE
        # 实盘运行模式📄支持asset_type = 'E'的情况，因此需要检查并排除其他情况
        if config['asset_type'] != 'E':
            msg = f'Only stock market is supported for live trade mode, got {config["asset_type"]} instead\n' \
                  f'please set asset_type="E" with: qt.configure(asset_type="E")'
            raise ValueError(msg)
        start_trader_ui(
                operator=operator,
                account_id=config['live_trade_account_id'],
                user_name=config['live_trade_account_name'],
                init_cash=config['live_trade_init_cash'],
                init_holdings=config['live_trade_init_holdings'],
                config=config,
                datasource=QT_DATA_SOURCE,
                debug=config['live_trade_debug_mode'],
        )

    elif run_mode == 1 or run_mode == 'back_test':
        # 进入回测模式，生成历史交易清单，使用真实历史价格回测策略的性能
        (hist_op,
         hist_ref,
         back_trade_prices,
         hist_benchmark,
         invest_cash_plan
         ) = check_and_prepare_backtest_data(
                operator=operator,
                config=config
        )
        # 在生成交易信号之前准备历史数据
        operator.assign_hist_data(
                hist_data=hist_op,
                reference_data=hist_ref,
                cash_plan=invest_cash_plan,
        )

        # 生成交易清单，对交易清单进行回测，对回测的结果进行基本评价
        loop_result = _evaluate_one_parameter(
                par=None,
                op=operator,
                trade_price_list=back_trade_prices,
                benchmark_history_data=hist_benchmark,
                benchmark_history_data_type=benchmark_data_type,
                config=config,
                stage='loop'
        )
        if config['report']:
            # 格式化输出回测结果
            report = _loop_report_str(loop_result, config)
            print(report)
            loop_result['report'] = report
        if config['visual']:
            # 图表输出投资回报历史曲线
            _plot_loop_result(loop_result, config)

        return loop_result

    elif run_mode == 2 or run_mode == 'optimization':
        # 进入优化模式，使用真实历史数据或模拟历史数据反复测试策略，寻找并测试最佳参数

        # 判断operator对象的策略中是否有可优化的参数，即优化标记opt_tag设置为1，且参数数量不为0
        assert operator.opt_space_par[0] != [], \
            f'ConfigError, none of the strategy parameters is adjustable, set opt_tag to be 1 or 2 to ' \
            f'activate optimization in mode 2, and make sure strategy has adjustable parameters'
        (hist_opti,
         hist_opti_ref,
         opti_trade_prices,
         hist_benchmark,
         opti_cash_plan,
         test_cash_plan
         ) = check_and_prepare_optimize_data(
                operator=operator,
                config=config
        )
        operator.assign_hist_data(
                hist_data=hist_opti,
                cash_plan=opti_cash_plan,
                reference_data=hist_opti_ref,
        )
        # 使用how确定优化方法并生成优化后的参数和性能数据
        how = config['opti_method']

        # 检查numpy的版本和优化算法，当numpy版本高于1.21,优化算法为2-incremental时，使用多进程计算反而会导致效率降低（原因尚待调查）
        # TODO: 临时解决办法：
        #  1, 当numpy版本高于1.22且算法为2-incremental时，强制禁用多进程计算，并打印warning信息
        np_version = np.__version__
        if np_version >= '1.22' and how == 2:
            import warnings
            config['parallel'] = False if config['parallel'] else config['parallel']
            msg = f'Performance Warning: the optimization algorithm 2-incremental is much slower than ' \
                  f'expected when numpy version is higher than 1.21 in parallel computing mode, ' \
                  f'the parallel computing is disabled to avoid performance degradation.'
            warnings.warn(msg, RuntimeWarning)

        # 开始优化
        optimal_pars, perfs = optimization_methods[how](
                hist=hist_opti,
                benchmark=hist_benchmark,
                benchmark_type=benchmark_data_type,
                op=operator,
                config=config
        )

        # 输出策略优化的评价结果，该结果包含在result_pool的extra额外信息属性中
        hist_opti_loop = hist_opti.fillna(0)
        result_pool = _evaluate_all_parameters(
                par_generator=optimal_pars,
                total=config['opti_output_count'],
                op=operator,
                trade_price_list=hist_opti_loop,
                benchmark_history_data=hist_benchmark,
                benchmark_history_data_type=benchmark_data_type,
                config=config,
                stage='test-o'
        )
        # 评价回测结果——计算参考数据收益率以及平均年化收益率
        opti_eval_res = result_pool.extra
        if config['report']:
            _print_test_result(opti_eval_res, config=config)
        if config['visual']:
            pass
            # _plot_test_result(opti_eval_res, config=config)

        # 完成策略参数的寻优，在测试数据集上检验寻优的结果，此时operator的交易数据已经分配好，无需再次分配
        if config['test_type'] in ['single', 'multiple']:
            result_pool = _evaluate_all_parameters(
                    par_generator=optimal_pars,
                    total=config['opti_output_count'],
                    op=operator,
                    trade_price_list=opti_trade_prices,
                    benchmark_history_data=hist_benchmark,
                    benchmark_history_data_type=benchmark_data_type,
                    config=config,
                    stage='test-t'
            )

            # 评价回测结果——计算参考数据收益率以及平均年化收益率
            test_eval_res = result_pool.extra
            if config['report']:
                _print_test_result(test_eval_res, config)
            if config['visual']:
                _plot_test_result(test_eval_res=test_eval_res, opti_eval_res=opti_eval_res, config=config)

        # TODO: Montecarlo模拟测试是否有必要存在？ v1.1版本后是否应该删除？
        elif config['test_type'] == 'montecarlo':
            for i in range(config['test_cycle_count']):
                # 临时生成用于测试的模拟数据，将模拟数据传送到operator中，使用operator中的新历史数据
                # 重新生成交易信号，并在模拟的历史数据上进行回测
                mock_hist = _create_mock_data(hist_opti)
                print(f'config.test_cash_dates is {config["test_cash_dates"]}')
                operator.assign_hist_data(
                        hist_data=mock_hist,
                        cash_plan=test_cash_plan,
                )
                mock_hist_loop = mock_hist.slice_to_dataframe(htype='close')
                result_pool = _evaluate_all_parameters(
                        par_generator=optimal_pars,
                        total=config['opti_output_count'],
                        op=operator,
                        trade_price_list=mock_hist,
                        benchmark_history_data=mock_hist_loop,
                        benchmark_history_data_type=benchmark_data_type,
                        config=config,
                        stage='test-t'
                )

                # 评价回测结果——计算参考数据收益率以及平均年化收益率
                test_eval_res = result_pool.extra
                if config['report']:
                    # TODO: 应该有一个专门的函数print_montecarlo_test_report
                    _print_test_result(test_eval_res, config)
                if config['visual']:  # 如果config.visual == True
                    # TODO: 应该有一个专门的函数plot_montecarlo_test_result
                    pass

        return optimal_pars
