# coding=utf-8
# ======================================
# File:     data_channels.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-10-09
# Desc:
#   Definition of interface to
# acquire or download historical data
# that can be stored in the datasource
# from different channels such as
# tushare, yahoo finance, akshare, etc.
# ======================================
import numpy as np
import pandas as pd
import time

from functools import lru_cache

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from .utilfuncs import (
    str_to_list,
    list_truncate,
    list_to_str_format,
    get_current_timezone_datetime,
)

"""
这个模块提供一个统一数据下载api：
data_channels.download_data(
    channel=channel,
    table=table_name,
    shares=shares,
    start_date=start_date,
    end_date=end_date,
    columns=columns,
    kwargs=kwargs,
)
其中table_name为数据表名，shares为股票代码，start_date和end_date为开始和
结束日期，columns为需要的列名，kwargs为其他参数。
这个api会根据channel的不同，找到不同数据源的下载api，然后调用这个api下载数据，
下载的数据将会被去重以后保存到一个DataFrame中，并返回。

数据的column整理不在这个模块中进行，而是在database模块中进行。这里只进行row方
向的去重处理

针对不同的数据源，本模块定义不同的数据表和下载api的对照表以及参数表，根据
这些表，将采用优化的方式下载数据。

优化方式包括：
1，数据量拆分，对于数据量较大的数据，可以将数据拆分成多组小数据，分批下载，拆分的方式依据对照表。
2，并行下载，拆分后的数据可以并行下载，加快下载速度。
3，数据缓存组装，对于大量数据，进行优化组装，提高速度

"""


# =====================
# data_channel模块主要API的解析函数，根据channel解析正确的API以执行
# =====================
def _fetch_table_data_from_tushare(table, **kwargs):
    """使用kwargs参数，从tushare获取一次金融数据

    Parameters
    ----------
    table: str,
        数据表名，必须是API_MAP中定义的数据表
    **kwargs:
        用于下载金融数据的函数参数

    Returns
    -------
    pd.DataFrame:
        下载后的数据
    """

    from .tsfuncs import acquire_data
    dnld_data = acquire_data(TUSHARE_API_MAP[table][API_MAP_COLUMNS.index('api')], **kwargs)

    return dnld_data


def _fetch_table_data_from_akshare(table, **kwargs):
    """ 使用kwargs参数，从akshare获取一次金融数据

    Parameters
    ----------
    table: str,
        数据表名，必须是API_MAP中定义的数据表
    **kwargs:
        用于下载金融数据的函数参数

    Returns
    -------
    pd.DataFrame:
        下载后的数据
    """
    from .akfuncs import acquire_data
    dnld_data = acquire_data(AKSHARE_API_MAP[table][API_MAP_COLUMNS.index('api')], **kwargs)

    return dnld_data


def _fetch_table_data_from_eastmoney(table, **kwargs):
    """ 使用kwargs参数，从东方财富网获取一次金融数据

    Parameters
    ----------
    table: str,
        数据表名，必须是API_MAP中定义的数据表
    **kwargs:
        用于下载金融数据的函数参数

    Returns
    -------
    pd.DataFrame:
        下载后的数据
    """
    from .emfuncs import acquire_data
    dnld_data = acquire_data(EASTMONEY_API_MAP[table][API_MAP_COLUMNS.index('api')], **kwargs)

    return dnld_data


def _fetch_table_data_from_sina(table, **kwargs):
    """ 使用kwargs参数，从新浪财经获取一次金融数据

    Parameters
    ----------
    table: str,
        数据表名，必须是API_MAP中定义的数据表
    **kwargs:
        用于下载金融数据的函数参数

    Returns
    -------
    pd.DataFrame:
        下载后的数据
    """
    from .sinafuncs import acquire_data
    dnld_data = acquire_data(SINA_API_MAP[table][API_MAP_COLUMNS.index('api')], **kwargs)

    return dnld_data


def _fetch_realtime_kline_from_tushare(qt_code, date, freq):
    """ 从tushare获取实时K线数据"""
    from .tsfuncs import acquire_data
    api_name = TUSHARE_REALTIME_API_MAP['realtime_bars'][API_MAP_COLUMNS.index('api')]
    dnld_data = acquire_data(api_name, **{'ts_code': qt_code, 'freq': freq})

    return dnld_data


def _fetch_realtime_kline_from_akshare(qt_code, date, freq):
    """ 从akshare获取实时K线数据"""
    from .akfuncs import acquire_data
    api_name = AKSHARE_REALTIME_API_MAP['realtime_bars'][API_MAP_COLUMNS.index('api')]
    dnld_data = acquire_data(api_name, **{'qt_code': qt_code, 'date': date, 'freq': freq})

    return dnld_data


def _fetch_realtime_kline_from_eastmoney(qt_code, date, freq):
    """ 从eastmoney获取实时K线数据"""
    from .emfuncs import acquire_data
    api_name = EASTMONEY_REALTIME_API_MAP['realtime_bars'][API_MAP_COLUMNS.index('api')]
    dnld_data = acquire_data(api_name, **{'qt_code': qt_code, 'date': date, 'freq': freq})

    return dnld_data


def _fetch_realtime_kline_from_sina(qt_code, date, freq):
    """ 从新浪财经获取实时K线数据"""
    from .sinafuncs import acquire_data
    api_name = SINA_REALTIME_API_MAP['realtime_bars'][API_MAP_COLUMNS.index('api')]
    dnld_data = acquire_data(api_name, **{'qt_code': qt_code, 'date': date, 'freq': freq})

    return dnld_data


def _get_fetch_table_func(channel: str):
    """ 获取数据下载函数

    Parameters
    ----------
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据

    Returns
    -------
    function:
        数据下载函数
    """
    if channel == 'tushare':
        return _fetch_table_data_from_tushare
    elif channel == 'akshare':
        return _fetch_table_data_from_akshare
    elif channel in ['emoney', 'eastmoney']:
        return _fetch_table_data_from_eastmoney
    elif channel == 'sina':
        return _fetch_table_data_from_sina
    else:
        raise NotImplementedError(f'channel {channel} is not supported')


def _get_realtime_kline_func(channel: str):
    """ 获取实时K线下载函数"""
    if channel == 'tushare':
        return _fetch_realtime_kline_from_tushare
    elif channel == 'akshare':
        return _fetch_realtime_kline_from_akshare
    elif channel in ['emoney', 'eastmoney']:
        return _fetch_realtime_kline_from_eastmoney
    elif channel == 'sina':
        return _fetch_realtime_kline_from_sina
    else:
        raise NotImplementedError(f'channel {channel} is not supported')


# =====================
# data_channel模块的主要API，分别用于从不同的渠道获取数据表数据以及实时价格数据（实时数据仅包含实时价格数据，且格式统一）
# =====================
def parse_data_fetch_args(table, channel, symbols, start_date, end_date, list_arg_filter, reversed_par_seq) -> dict:
    """ 解析数据获取API的参数，生成下载数据的参数序列

    本函数为data_channel的主API进行参数解析，用户在获取数据时，一般仅会指定需要获取的数据
    类型、频率、开始和结束日期，以及可能的筛选参数，如股票代码、交易所等。Data_channel会将
    这些参数解析成一组参数序列，用于调用数据获取API。

    Parameters
    ----------
    table: str,
        数据表名，必须是database中定义的数据表
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据
    start_date: str, optional
        数据下载的开始日期
    end_date: str, optional
        数据下载的结束日期
    list_arg_filter: str or list of str, optional
        用于下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
        参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。
        如果filter_arg为None，则下载所有数据。
        例如，下载stock_basic表数据时，下载以下输入均为合法输入：
        - 'SZSE'
            仅下载深圳交易所的股票数据
        - ['SSE', 'SZSE']
        - 'SSE, SZSE'
            上面两种写法等效，下载上海和深圳交易所的股票数据
    symbols: str or list of str, optional
        用于下载数据的股票代码，如果给出了symbols，只有这些股
        票代码的数据会被下载
    reversed_par_seq: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    dict:
        用于下载数据的参数序列
    """

    if channel == 'tushare':
        API_MAP = TUSHARE_API_MAP
    elif channel == 'akshare':
        API_MAP = AKSHARE_API_MAP
    elif channel == 'eastmoney':
        API_MAP = EASTMONEY_API_MAP
    else:
        raise NotImplementedError(f'channel {channel} is not supported')

    if table not in API_MAP:
        return {}

    # get all tables in the API mapping
    arg_name = API_MAP[table][1]
    arg_type = API_MAP[table][2]
    arg_range = API_MAP[table][3]
    allowed_code_suffix = API_MAP[table][4]
    additional_start_end = API_MAP[table][5]
    start_end_chunk_size = API_MAP[table][6]

    if isinstance(symbols, list):
        symbols = list_to_str_format(symbols)

    # parse the filling args and pick the first filling arg value from the range

    if arg_name == 'none':
        arg_name = None

    if arg_type == 'list':
        arg_values = _parse_list_args(arg_range, list_arg_filter, reversed_par_seq)
    elif arg_type == 'datetime':
        from .datatables import TABLE_MASTERS
        freq = TABLE_MASTERS[table][4]
        arg_values = _parse_datetime_args(arg_range, start_date, end_date, freq, reversed_par_seq)
    elif arg_type == 'trade_date':
        from .datatables import TABLE_MASTERS
        freq = TABLE_MASTERS[table][4]
        arg_values = _parse_trade_date_args(arg_range, start_date, end_date, freq, 'SSE', reversed_par_seq)
    elif arg_type == 'hk_trade_date':
        raise NotImplementedError('hk_trade_date is not implemented')
    elif arg_type == 'us_trade_date':
        raise NotImplementedError('us_trade_date is not implemented')
    elif arg_type == 'quarter':
        arg_values = _parse_quarter_args(arg_range, start_date, end_date, reversed_par_seq)
    elif arg_type == 'month':
        arg_values = _parse_month_args(arg_range, start_date, end_date, reversed_par_seq)
    elif arg_type == 'table_index':
        arg_values = _parse_table_index_args(arg_range, symbols, allowed_code_suffix, reversed_par_seq)
    elif arg_type == 'none':
        arg_values = []
    else:
        raise ValueError('unexpected arg type:', arg_type)

    # build the args dict
    if (arg_name is None) and (additional_start_end.lower() != 'y'):
        kwargs = {}
    elif (arg_name is None) and (additional_start_end.lower() == 'y'):
        additional_args = _parse_additional_time_args(start_end_chunk_size, start_date, end_date)
        kwargs = ({**add_arg} for add_arg in additional_args)
    elif additional_start_end.lower() != 'y':
        # only standard args
        kwargs = ({arg_name: val} for val in arg_values)
    elif additional_start_end.lower() == 'y':
        # build additional start/end args
        additional_args = _parse_additional_time_args(start_end_chunk_size, start_date, end_date)
        import itertools
        kwargs = ({arg_name: val, **add_arg} for val, add_arg in
                  itertools.product(arg_values, additional_args))
    else:
        raise ValueError('unexpected additional_start_end:', additional_start_end)

    return kwargs


def fetch_batched_table_data(
        *,
        table: str,
        channel: str,
        arg_list: any,
        parallel: bool = True,
        process_count: int = None,
        logger: any = None,
        download_batch_size: int = 0,
        download_batch_interval: int = 0.,
) -> pd.DataFrame:
    """ 一个Generator，顺序循环批量获取同一张数据表的数据，支持并行下载并逐个返回数据

    Parameters
    ----------
    table: str,
        数据表名，必须是database中定义的数据表
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据
    arg_list: iterable
        用于下载数据的函数参数
    parallel: bool, default True
        是否并行下载数据
    process_count: int, default None
        并行下载数据时，使用的进程数, 默认为None，表示使用cpu_count()个进程
    logger: logger
        用于记录下载数据的日志
    download_batch_size: int
        为降低网络请求的频率，在暂停之前连续网络请求的次数，单位为次，如果设置为0，则不暂停
    download_batch_interval: float
        为降低网络请求的频率，连续网络请求一定次数后，暂停的时间，单位为秒

    Yields
    -------
    dict: {'kwargs': kwargs, 'data': pd.DataFrame}
        下载的数据，包含参数和数据
    """

    fetch_table_data = _get_fetch_table_func(channel)

    # 如果当总下载量小于batch_size时，就不用暂停了(为了实现truncate，必须把arg_list转化为list)
    if not isinstance(arg_list, list):
        arg_list = list(arg_list)
    if len(arg_list) < download_batch_size:
        download_batch_interval = 0

    completed = 0
    if not parallel:
        for kwargs in arg_list:
            completed += 1
            df = fetch_table_data(table, **kwargs)
            if (download_batch_interval != 0) and (completed % download_batch_size == 0):
                time.sleep(download_batch_interval)
            # logger.info(f'[{table}:{kwargs}] {len(df)} rows downloaded')
            yield {'kwargs': kwargs, 'data': df}

    else:  # parallel
        # 使用ThreadPoolExecutor循环下载数据
        with ThreadPoolExecutor(max_workers=process_count) as worker:
            # 在parallel模式下，下载线程的提交和返回是分开进行的，为了实现分批下载，必须分批提交，提交一批
            # 数据后，等待结果返回，再提交下一批，因此，需要将arg_list分段，提交完一个batch之后，返回结果，
            # 再暂停，暂停后再继续提交
            submitted = 0
            # 将arg_list分段，每次下载batch_size个数据
            if download_batch_size == 0:
                arg_list_chunks = [arg_list]
            else:
                arg_list_chunks = list_truncate(arg_list, download_batch_size, as_list=False)

            for arg_sub_list in arg_list_chunks:
                futures = {}
                for kw in arg_sub_list:
                    futures.update({worker.submit(fetch_table_data, table, **kw): kw})
                    submitted += 1
                for f in as_completed(futures):
                    kwargs = futures[f]
                    completed += 1
                    yield {'kwargs': kwargs, 'data': f.result()}

                if download_batch_interval != 0:
                    time.sleep(download_batch_interval)


def fetch_real_time_klines(
        *,
        channel: str,
        qt_codes: str or [str],
        freq: str = 'd',
        parallel: bool = True,
        time_zone: str = 'local',
        verbose: bool = True,
        matured_kline_only: bool = False,
        logger: any = None,
) -> pd.DataFrame:
    """ 从 channels 调用实时K线接口获取当天的最新实时K线数据，K线频率最低为‘d'，最高为'1min'
    获取的数据仅包括当天的数据，如果当天不是交易日，返回空数据框。

    Parameters
    ----------
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据
    qt_codes: str or [str],
        股票代码
    freq: str,
        数据频率，支持以下频率：
        - 'd': 如果
        - 'h':
        - '30min':
        - '15min':
        - '5min':
        - '1min':
    parallel: bool, optional, default True
        是否并行获取数据，默认True
    time_zone: str, optional
        时区，默认local即系统当地时区，可以指定特定的时区以获取不同时区市场的实时价格
    verbose: bool, optional, default False
        如果为True，给出更多的数据，否则返回简化的数据：
        - verbose = True: 'trade_time, symbol, name, pre_close, open, close, high, low, vol, amount'
        - verbose = False: 'trade_time, symbol, open, close, high, low, vol, amount'
    matured_kline_only: bool, default False
        是否只返回已经成熟的(也就是完整的上一个)K线数据，如果为True，则只返回已经成熟的K线数据，即已经完整的上一根K线数据
        如果为False，则返回最新的K线数据，哪怕这根K线数据并未完整
    logger: logger
        用于记录下载数据的日志

    Returns
    -------
    pd.DataFrame
    """

    fetch_realtime_kline = _get_realtime_kline_func(channel)

    data = []
    if isinstance(qt_codes, str):
        qt_codes = str_to_list(qt_codes)

    # 获取当前时间以及当天日期
    current_time = get_current_timezone_datetime(time_zone)
    today =current_time.strftime('%Y%m%d')

    # 使用ProcessPoolExecutor, as_completed加速数据获取，当parallel=False时，不使用多进程
    if parallel:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(fetch_realtime_kline, qt_code=symbol, date=today, freq=freq): symbol
                for symbol
                in qt_codes
            }
            for future in as_completed(futures):
                try:
                    df = future.result(timeout=2)
                    symbol = futures[future]
                except TimeoutError:
                    continue
                except Exception as exc:
                    print(f'Encountered an exception: {exc}')
                    if '权限' in str(exc):
                        continue
                    elif 'not_implemented' in str(exc):
                        continue
                    else:
                        raise exc
                else:
                    if df.empty:
                        continue
                    df['ts_code'] = symbol
                    # 根据当前时间确定哪个是matured kline，而不是直接取最后一个，因为最后一个可能是不完整的
                    if matured_kline_only:
                        last_matured_index = np.searchsorted(df.index, current_time, side='right') - 1
                        k_line = df.iloc[last_matured_index:last_matured_index + 1, :]
                    else:  # 否则就直接取最后一个，不管是否完整
                        k_line = df.iloc[-1:, :]
                    data.append(k_line)
    else:  # parallel == False, 不使用多进程
        for symbol in qt_codes:
            df = fetch_realtime_kline(qt_code=symbol, date=today, freq=freq)
            if df.empty:
                continue
            df['ts_code'] = symbol
            # 根据当前时间确定哪个是matured kline，而不是直接取最后一个，因为最后一个可能是不完整的
            if matured_kline_only:
                last_matured_index = np.searchsorted(df.index, current_time, side='right') - 1
                k_line = df.iloc[last_matured_index:last_matured_index + 1, :]
            else:  # 否则就直接取最后一个，不管是否完整
                k_line = df.iloc[-1:, :]
            data.append(k_line)
    try:
        data = pd.concat(data)
    except:
        return pd.DataFrame()  # 返回空DataFrame

    data = scrub_realtime_klines(data, verbose=verbose)

    return data


def fetch_real_time_quotes(
        *,
        channel: str,
        shares: str or [str],
        parallel: bool = True,
        logger: any = None,
) -> pd.DataFrame:
    """ 从 channels 调用实时盘口API获取实时盘口数据，包括实时价格、成交数据、五档委买委卖数据等。

    Parameters
    ----------
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据
    shares: str or [str],
        股票代码
    parallel: bool, optional, default True
        是否并行获取数据，默认True
    logger: logger
        用于记录下载数据的日志

    Returns
    -------
    pd.DataFrame
    """
    raise NotImplementedError


def scrub_table_data(data: pd.DataFrame, table: str) -> pd.DataFrame:
    """ 清洗数据，确保数据data的字段和数据类型符合数据表table的定义

    Parameters
    ----------
    data: pd.DataFrame,
        下载的数据
    table: str,
        数据表名，必须是API_MAP中定义的数据表

    Returns
    -------
    pd.DataFrame:
        清洗后的数据
    """
    # TODO: this function is now not utilized; data scrubbing is done in datasource
    #  but later data scrubbing shoule be done here, and datasource only does basic checks
    #  following works should be done:
    #  1, make sure data column numbers match table schema
    #  2, remove all NaN data rows
    #  3, reindex data column names
    #  4, make DataFrame index according to table prime keys and remove duplicate indexes
    #  5, check data types, make sure all data types fit table schema
    #  6, cut off strings that exceeds varchar limit
    raise NotImplementedError


def scrub_realtime_quote_data(raw_data, verbose) -> pd.DataFrame:
    """ 清洗数据，去除不一致及错误数据，并使数据符合realtime_quote的数据格式"""
    raise NotImplementedError


def scrub_realtime_klines(raw_data, verbose) -> pd.DataFrame:
    """ 清洗数据，去除不一致及错误的数据，并使数据符合实时K线图的数据格式"""

    if "trade_time" not in raw_data.columns:
        # trade_time 在 index 中，将它移到frame中
        assert raw_data.index.name in ['trade_time', 'trade_date'], AssertionError('trade_time should be in index')
        raw_data['trade_time'] = raw_data.index
    # 重新整理数据列名称
    if verbose:
        target_columns = ['trade_time', 'ts_code', 'name', 'pre_close', 'open', 'close',
                          'high', 'low', 'vol', 'amount']

    else:

        target_columns = ['trade_time', 'ts_code', 'open', 'close', 'high', 'low', 'vol', 'amount']

    data = raw_data.reindex(
            columns=target_columns
    )
    # set index
    data.set_index('trade_time', inplace=True)

    return data


# ======================================
# 一系列函数数据获取原子函数，针对不同的API主参数类型，生成下载数据的参数序列
# ======================================
def _parse_list_args(arg_range: str or [str], list_arg_filter: str or [str] = None, reversed_par_seq: bool = False):
    """ 解析list类型的参数，生成下载数据的参数序列

    Parameters
    ----------
    arg_range: str or list of str,
        用于下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
        参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。
    list_arg_filter: str or list of str, optional
        用于下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
        参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。
        如果filter_arg为None，则下载所有数据。
        例如，下载stock_basic表数据时，下载以下输入均为合法输入：
        - 'SZSE'
            仅下载深圳交易所的股票数据
        - ['SSE', 'SZSE']
        - 'SSE, SZSE'
            上面两种写法等效，下载上海和深圳交易所的股票数据
    reversed_par_seq: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list generator:
        用于下载数据的参数序列
    """
    if isinstance(arg_range, str):
        arg_range = str_to_list(arg_range)

    if reversed_par_seq:
        arg_range = arg_range[::-1]

    if list_arg_filter is None:
        return (item for item in arg_range)

    if (isinstance(list_arg_filter, str)) and ":" not in list_arg_filter:
        # 如果list_arg_filter是字符串，且不包含":"，则将其转换为列表
        list_arg_filter = str_to_list(list_arg_filter)

    if isinstance(list_arg_filter, str):
        # 如果list_arg_filter是字符串，且包含":"，则将其转换为上下限
        list_arg_bounds = list_arg_filter.split(':')
        list_idx_lower = arg_range.index(list_arg_bounds[0])
        list_idx_upper = arg_range.index(list_arg_bounds[1])
        if list_idx_lower > list_idx_upper:
            # reverse the lower and upper index if lower is larger than upper
            list_idx_lower, list_idx_upper = list_idx_upper, list_idx_lower
        # 确认上下限的位置
        return (item for item in arg_range[list_idx_lower:list_idx_upper + 1])

    return (item for item in arg_range if item in list_arg_filter)


def _parse_datetime_args(arg_range: str, start_date: str, end_date: str,
                         freq: str = 'd', reversed_par_seq: bool = False):
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    arg_range: str,
        表示数据的时间范围的起始日期，如'20210101'表示从2021年1月1日开始
    start_date: str, YYYYMMDD
        数据下载的开始日期
    end_date: str, YYYYMMDD
        数据下载的结束日期
    freq: str, optional
        数据下载的频率，支持以下选项：
        - 'd':  日频率
        - 'w':  周频率
        - 'm':  月频率
    reversed_par_seq: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list:
        用于下载数据的参数序列
    """

    start_date, end_date = _ensure_date_sequence(arg_range, start_date, end_date)

    if freq is None:
        freq = 'd'
    if freq.lower() == 'w':
        freq = 'w-Fri'
    if freq.lower() == 'm':
        freq = 'ME'

    res = pd.date_range(start_date, end_date, freq=freq).strftime('%Y%m%d').to_list()

    if reversed_par_seq:
        return res[::-1]
    else:
        return res


def _parse_trade_date_args(arg_range: str, start_date: str, end_date: str,
                           freq: str = 'd', market: str = 'SSE', reversed_par_seq: bool = False):
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期
    freq: str, optional
        数据下载的频率，支持以下选项：
        - 'd':  日频率
        - 'w':  周频率
        - 'm':  月频率
    market: str, optional
        交易市场，支持数据表Trade_calendar中定义的交易市场
    reversed_par_seq: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list:
        用于下载数据的参数序列
    """

    from .utilfuncs import is_market_trade_day, nearest_market_trade_day
    full_dates = _parse_datetime_args(arg_range, start_date, end_date, freq, reversed_par_seq)

    if freq is None:
        freq = 'd'
    # 如果频率是月或周，分别查找所有日期的nearest_trade_day并删除重复日期
    if freq.lower() in ['w', 'm']:
        trade_dates = list(map(nearest_market_trade_day, full_dates))
        trade_dates = list(set(trade_dates))
        trade_dates.sort(reverse=reversed_par_seq)
        trade_dates = [date.strftime('%Y%m%d') for date in trade_dates]
    else:
        # 如果频率是日，删除所有非交易日
        trade_dates = [date for date in full_dates if is_market_trade_day(date, market)]

    return trade_dates


def _parse_table_index_args(arg_range: str, symbols: str, allowed_code_suffix: str = None,
                            reversed_par_seq: bool = False):
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    arg_range: str,
        数据表名，定义为basics的数据表，包含股票代码等基本信息
    symbols: str or list of str,
        用于下载数据的股票代码，如果给出了symbols，只有这些股票代码的数据会被下载
    allowed_code_suffix: str, optional
        用于下载数据的股票代码后缀，如果给出了allowed_code_suffix，只有这些股票代码的数据会被下载
    reversed_par_seq: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list:
        用于下载数据的参数序列
    """

    from qteasy import QT_DATA_SOURCE

    df_s, df_i, df_f, df_ft, df_o, df_ths = QT_DATA_SOURCE.get_all_basic_table_data()

    table_name = arg_range

    if table_name == 'stock_basic':
        all_args = df_s.index.to_list()
    elif table_name == 'index_basic':
        all_args = df_i.index.to_list()
    elif table_name == 'fund_basic':
        all_args = df_f.index.to_list()
    elif table_name == 'future_basic':
        all_args = df_ft.index.to_list()
    elif table_name == 'opt_basic':
        all_args = df_o.index.to_list()
    elif table_name == 'ths_index_basic':
        all_args = df_ths.index.to_list()
    else:
        raise ValueError(f'unknown table name {table_name}')

    if symbols is not None:  # assert symbols is a str, 进行第一次筛选
        # 冒号分隔的字符串，表示股票代码的上下限
        if ':' in symbols:
            symbols = symbols.split(':')
            lower = symbols[0].split('.')[0]
            upper = symbols[1].split('.')[0]
            if lower > upper:
                lower, upper = upper, lower
            all_args = [arg for arg in all_args if (lower <= arg.split('.')[0] <= upper)]

        else:
            symbols = str_to_list(symbols)
            all_args = [arg for arg in all_args if arg in symbols]

    if allowed_code_suffix:  # assert allowed_code_suffix is a str, 进行第二次筛选
        suffix = str_to_list(allowed_code_suffix)
        all_args = [arg for arg in all_args if arg[-2:] in suffix]

    if reversed_par_seq:
        all_args = all_args[::-1]

    return all_args


def _parse_quarter_args(arg_range: str, start_date: str, end_date: str, reversed_par_seq: bool = False) -> list:
    """ 根据开始和结束日期，生成数据获取的参数序列，类似2022Q1等

    Parameters
    ----------
    arg_range: str,
        可以下载的最早数据的季度标识，如1976Q1标识1976年第一季度
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    start_date, end_date = _ensure_date_sequence(arg_range, start_date, end_date)

    # calculate absolute quarter number
    start_quarter = _convert_date_to_absolute_quarter(start_date)
    end_quarter = _convert_date_to_absolute_quarter(end_date)

    # convert year and quarter to string
    quarter_list = list(range(start_quarter, end_quarter + 1))
    quarter_list = [_convert_absolute_quarter_to_quarter_str(q) for q in quarter_list]

    if reversed_par_seq:
        return quarter_list[::-1]

    return quarter_list


def _get_year_and_quarter(date) -> tuple:
    """ convert date like 2020-01-01 to year and quarter like 2020, 1"""
    return date.year, (date.month - 1) // 3 + 1


def _get_year_and_month(date) -> tuple:
    """ convert date like 2020-03-01 to year and month like 2020, 3"""
    return date.year, date.month


def _convert_date_to_absolute_quarter(date) -> int:
    """ convert date like 2020-01-01 to absolute quarter number like 2020*4+1"""
    year, quarter = _get_year_and_quarter(date)
    return year * 4 + quarter


def _convert_quarter_str_to_absolute_quarter(quarter: str) -> int:
    """ converte quarter str like 2020Q1 to absolute quarter number like 2020*4+1"""
    year, quarter = quarter.split('Q')
    return int(year) * 4 + int(quarter)


def _convert_date_to_absolute_month(date) -> int:
    """ convert date like 2020-03-01 to absolute month number like 2020*12+3"""
    year, month = _get_year_and_month(date)
    return year * 12 + month


def _convert_month_str_to_absolute_month(date: str) -> int:
    """ convert month str like 202003 to absolute month like 2020*12+3"""
    year, month = date[:4], date[4:]
    return int(year) * 12 + int(month)


def _convert_absolute_quarter_to_quarter_str(quarter_num) -> str:
    """ convert absolute quarter number like 2020*4+1 to quarter like 2020Q1"""
    year, quarter = quarter_num // 4, quarter_num % 4
    if quarter == 0:
        year = year - 1
        quarter = 4
    return f'{year}Q{quarter}'


def _convert_absolute_month_to_month_str(month_num) -> str:
    """ convert absolute month number like 2020*12+3 to month like 202003"""
    year, month = month_num // 12, month_num % 12
    if month == 0:
        year = year - 1
        month = 12
    return f'{year}{month:02d}'


def _parse_month_args(arg_range: str, start_date: str, end_date: str, reversed_par_seq: bool = False) -> list:
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    arg_range: str,
        数据下载的开始日期
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期
    reversed_par_seq: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    start_date, end_date = _ensure_date_sequence(arg_range, start_date, end_date)

    # calculate absolute month number
    start_month = _convert_date_to_absolute_month(start_date)
    end_month = _convert_date_to_absolute_month(end_date)

    # complete list with all months
    month_list = list(range(start_month, end_month + 1))

    # convert year and month to string
    month_list = [_convert_absolute_month_to_month_str(month) for month in month_list]

    if reversed_par_seq:
        return month_list[::-1]

    return month_list


def _parse_additional_time_args(chunk_size, start_date, end_date) -> list:
    """ 生成附加的开始/结束日期参数。对于分钟类型的数据表，按照qt_code生成参数序列
    还有可能无法完整下载所有数据，因此需要增加start/end限制参数，限制每次下载的数据量
    确保数据下载的完整性。

    Parameters
    ----------
    chunk_size: str,
        分批下载数据时，每一批数据包含的数据量，单位为天，表示每次下载多少天的数据
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期

    Returns
    -------
    list: [{'start': date, 'end': date}, ...]
        用于下载数据的额外参数序列，在主参数序列的基础上，增加了start和end参数
    """

    start_date, end_date = _ensure_date_sequence('19700101', start_date, end_date)

    if chunk_size is None:
        return [{'start': start_date.strftime('%Y%m%d'), 'end': end_date.strftime('%Y%m%d')}]
    try:
        chunk_size = int(chunk_size)
    except ValueError:
        chunk_size = 0

    if chunk_size <= 0:
        return [{'start': start_date.strftime('%Y%m%d'), 'end': end_date.strftime('%Y%m%d')}]  # return the whole period

    start_end_chunk_lbounds = list(pd.date_range(start=start_date,
                                                 end=end_date,
                                                 freq=f'{chunk_size}d'
                                                 ).strftime('%Y%m%d'))
    start_end_chunk_rbounds = start_end_chunk_lbounds[1:]

    start_end_chunk_rbounds.append(end_date.strftime('%Y%m%d'))
    chunked_additional_args = [{'start': s, 'end': e} for s, e in
                               zip(start_end_chunk_lbounds, start_end_chunk_rbounds)]

    return chunked_additional_args


def _ensure_date_sequence(first_date, start_date, end_date) -> tuple:
    """ 确保开始和结束日期在first_date之后，如果不是，则交换开始和结束日期

    Parameters
    ----------
    first_date: str,
        数据表中的最早日期
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期

    Returns
    -------
    tuple: start_date, end_date
        确保开始和结束日期在first_date之后的开始和结束日期
    """

    first_date = pd.to_datetime(first_date)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if start_date < first_date:
        start_date = first_date
    if end_date < first_date:
        end_date = first_date
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date


def get_dependent_table(table: str, channel: str) -> str or None:
    """ 获取数据表的依赖表. 依赖表是指在获取某个数据表之前，需要先获取的数据表

    依赖表主要包括在api_map中定义的fill_arg_type为'table_index'的数据表，如stock_basic表

    Parameters
    ----------
    table: str,
        数据表名，必须是database中定义的数据表
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据

    Returns
    -------
    str:
        数据表的依赖表名称

    Notes
    -----
    如果数据表不存在或者无法找到依赖表，则返回None
    """

    api_map = get_api_map(channel=channel)

    if table not in api_map.index:
        return None

    cur_table = api_map.loc[table]
    fill_type = cur_table.fill_arg_type
    if fill_type == 'trade_date':
        return 'trade_calendar'
    elif fill_type == 'table_index':
        return cur_table.arg_rng


@lru_cache(maxsize=4)
def get_api_map(channel: str) -> pd.DataFrame:
    """ 获取指定金融数据API的MAP表

    Parameters
    ----------
    channel: str,
        数据获取渠道，金融数据API，支持以下选项:
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'eastmoney'   : 从东方财富网获取金融数据

    Returns
    -------
    pd.DataFrame
        根据channel返回对应的API MAP表，DataFrame格式
    """

    if channel == 'tushare':
        API_MAP = TUSHARE_API_MAP
        MAP_COLUMNS = API_MAP_COLUMNS
    elif channel == 'akshare':
        API_MAP = AKSHARE_API_MAP
        MAP_COLUMNS = API_MAP_COLUMNS
    elif channel == 'eastmoney':
        API_MAP = EASTMONEY_API_MAP
        MAP_COLUMNS = API_MAP_COLUMNS
    else:
        raise NotImplementedError(f'channel {channel} is not supported')

    api_map = pd.DataFrame(API_MAP).T
    api_map.columns = MAP_COLUMNS

    return api_map


"""
TUSHARE API MAP表column的定义：
1, api:                     对应的tushare API函数名, 参见tsfuncs.py中的定义

2, fill_arg_name:           从tushare下载数据时的关键参数，使用该关键参数来分多次下载完整的数据
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

3, fill_arg_type:           关键参数的数据类型，可以为list、table_index、datetime、trade_date，含义分别为：
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

4, arg_rng:                 关键参数的取值范围，
                            -   如果数据类型为datetime或trade_date，是一个起始日期，表示取值范围从该日期到今日之间
                            -   如果数据类型为table_index，取值范围是一张表，如stock_basic，表示数据从stock_basic的
                                索引中取值
                            -   如果数据类型为list，则直接给出取值范围，如"SSE,SZSE"表示可以取值SSE以及SZSE。

5, arg_allowed_code_suffix:
                            table_index类型取值范围的限制值，限制只有特定后缀的证券代码才会被用作参数下载数据。
                            例如，取值"SH,SZ"表示只有以SH、SZ结尾的证券代码才会被用作参数从tushare下载数据。

6, arg_allow_start_end:     使用table_index类型参数时，是否同时允许传入开始结束日期作为参数。如果设置为"Y"，则会在使用
                            table_index中的代码作为参数下载数据时，同时传入开始和结束日期作为附加参数，否则仅传入代码

7, start_end_chunk_size:    传入开始结束日期作为附加参数时，是否分块下载。可以设置一个正整数或空字符串如"300"。如果设置了
                            一个正整数字符串，表示一个天数，并将开始结束日期之间的数据分块下载，每个块中数据的时间跨度不超
                            过这个天数。
                            例如，设置该参数为100，则每个分块内的时间跨度不超过100天
"""

API_MAP_COLUMNS = [
    'api',  # 1, 从channel获取数据时使用的api名
    'fill_arg_name',  # 2, 获取数据时使用的api参数名
    'fill_arg_type',  # 3, 从获取数据时使用的api参数类型
    'arg_rng',  # 4, 获取数据时使用的api参数取值范围
    'allowed_code_suffix',  # 5, 获取数据时使用的api参数允许的股票代码后缀
    'allow_start_end',  # 6, 获取数据时使用的api参数需要的额外参数类型
    'start_end_chunk_size',  # 7, 从tushare获取数据时使用的api参数start_date和end_date时的分段大小
    # TODO: 修改column6/column7 for minor upgrades of version 1.4：
    #  将6改为"table_row_limiter”,含义是限制同时下载的数据行方法，取值包括：
    #  -   '':   没有额外的参数用于限制下载数据的行数
    #  -   'Y':  使用开始结束日期作为参数，限制下载数据的行数
    #  -   'C':  使用limit/offset作为参数，直接限制下载数据的行数
    #  -   'other':  其他方法，如使用日期作为参数，但不限制下载数据的行数
    #  将7改为“table_row_limiter_args”，含义是限制下载数据行数的参数，取值包括：
    #  -   当table_row_limiter为''时，table_row_limiter_args为''
    #  -   当table_row_limiter为'Y'时，table_row_limiter_args为起止日期之间的天数，如200代表最多下载200天的数据
    #  -   当table_row_limiter为'C'时，table_row_limiter_args为limit/offset的值，如100代表每次下载100行数据
]

TUSHARE_API_MAP = {
    'trade_calendar':
        ['trade_cal', 'exchange', 'list', 'SSE, SZSE, CFFEX, SHFE, CZCE, DCE, INE', '', '', ''],

    # 'hk_trade_calendar':  # tsfuncs
    #     ['hk_tradecal', 'none', 'none', 'none', '', 'C', '2000'],

    # 'us_trade_calendar':  # tsfuncs
    #     ['us_tradecal', 'none', 'none', 'none', '', 'C', '6000'],

    'stock_basic':
        ['stock_basic', 'exchange', 'list', 'SSE,SZSE,BSE', '', '', '', ],

    # 'hk_stock_basic':  # tsfuncs
    #     ['hk_stock_basic', 'none', 'none', 'none', '', '', ''],
    #
    # 'us_stock_basic':  # tsfuncs
    #     ['us_stock_basic', 'none', 'none', 'none', '', 'C', '6000'],

    'stock_names':
        ['namechange', 'ts_code', 'table_index', 'stock_basic', '', 'Y', '300'],

    'stock_company':
        ['stock_company', 'exchange', 'list', 'SSE, SZSE, BSE', '', '', ''],

    'stk_managers':
        ['stk_managers', 'ann_date', 'datetime', '19901211', '', '', ''],

    'new_share':
        ['new_share', 'none', 'none', 'none', '', 'Y', '200'],

    'money_flow':
        ['moneyflow', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'stock_limit':
        ['stk_limit', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'stock_suspend':
        ['suspend_d', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'hs_money_flow':
        ['moneyflow_hsgt', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'hs_top10_stock':
        ['hsgt_top10', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'hk_top10_stock':
        ['ggt_top10', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'index_basic':
        ['index_basic', 'market', 'list', 'SSE,MSCI,CSI,SZSE,CICC,SW,OTH', '', '', ''],

    'fund_basic':
        ['fund_basic', 'market', 'list', 'E,O', '', '', ''],

    'future_basic':
        ['future_basic', 'exchange', 'list', 'CFFEX,DCE,CZCE,SHFE,INE', '', '', ''],

    'opt_basic':
        ['options_basic', 'exchange', 'list', 'SSE,SZSE,CFFEX,DCE,CZCE,SHFE', '', '', ''],

    'ths_index_basic':
        ['ths_index', 'exchange', 'list', 'A, HK, US', '', '', ''],

    'sw_industry_basic':
        ['index_classify', 'src', 'list', 'sw2014, sw2021', '', '', ''],

    'stock_1min':
        ['mins1', 'ts_code', 'table_index', 'stock_basic', '', 'y', '30'],

    'stock_5min':
        ['mins5', 'ts_code', 'table_index', 'stock_basic', '', 'y', '90'],

    'stock_15min':
        ['mins15', 'ts_code', 'table_index', 'stock_basic', '', 'y', '180'],

    'stock_30min':
        ['mins30', 'ts_code', 'table_index', 'stock_basic', '', 'y', '360'],

    'stock_hourly':
        ['mins60', 'ts_code', 'table_index', 'stock_basic', '', 'y', '360'],

    'stock_daily':
        ['daily', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'stock_weekly':
        ['weekly', 'trade_date', 'trade_date', '19901221', '', '', ''],

    'stock_monthly':
        ['monthly', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'hk_stock_daily':
        ['hk_daily', 'trade_date', 'hk_trade_date', '19901211', '', '', ''],

    'us_stock_daily':
        ['us_daily', 'trade_date', 'us_trade_date', '19601211', '', '', ''],

    'index_1min':
        ['mins1', 'ts_code', 'table_index', 'index_basic', 'SH,SZ', 'y', '30'],

    'index_5min':
        ['mins5', 'ts_code', 'table_index', 'index_basic', 'SH,SZ', 'y', '90'],

    'index_15min':
        ['mins15', 'ts_code', 'table_index', 'index_basic', 'SH,SZ', 'y', '180'],

    'index_30min':
        ['mins30', 'ts_code', 'table_index', 'index_basic', 'SH,SZ', 'y', '360'],

    'index_hourly':
        ['mins60', 'ts_code', 'table_index', 'index_basic', 'SH,SZ', 'y', '360'],

    'index_daily':
        ['index_daily', 'ts_code', 'table_index', 'index_basic', 'SH,CSI,SZ', 'y', ''],

    'index_weekly':
        ['index_weekly', 'trade_date', 'trade_date', '19910705', '', '', ''],

    'index_monthly':
        ['index_monthly', 'trade_date', 'trade_date', '19910731', '', '', ''],

    'ths_index_daily':
        ['ths_daily', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'ths_index_weight':
        ['ths_member', 'ts_code', 'table_index', 'ths_index_basic', '', '', ''],

    'ci_index_daily':
        ['ci_daily', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'sw_index_daily':
        ['sw_daily', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'global_index_daily':
        ['index_global', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'fund_1min':
        ['mins1', 'ts_code', 'table_index', 'fund_basic', 'SH,SZ', 'y', '30'],

    'fund_5min':
        ['mins5', 'ts_code', 'table_index', 'fund_basic', 'SH,SZ', 'y', '90'],

    'fund_15min':
        ['mins15', 'ts_code', 'table_index', 'fund_basic', 'SH,SZ', 'y', '180'],

    'fund_30min':
        ['mins30', 'ts_code', 'table_index', 'fund_basic', 'SH,SZ', 'y', '360'],

    'fund_hourly':
        ['mins60', 'ts_code', 'table_index', 'fund_basic', 'SH,SZ', 'y', '360'],

    'fund_daily':
        ['fund_daily', 'trade_date', 'trade_date', '19980417', '', '', ''],

    'fund_nav':
        ['fund_net_value', 'nav_date', 'datetime', '20000107', '', '', ''],

    'fund_share':
        ['fund_share', 'ts_code', 'table_index', 'fund_basic', '', '', ''],

    'fund_manager':
        ['fund_manager', 'ts_code', 'table_index', 'fund_basic', 'OF, SZ, SH', '', ''],

    'future_mapping':
        ['fut_mapping', 'trade_date', 'trade_date', '19901219', '', '', ''],

    'future_1min':  # future_xmin 表应该通过trade_time(start/end)来切表索引，而不是通过table_index
        ['ft_mins1', 'ts_code', 'table_index', 'future_basic', '', 'y', '30'],

    'future_5min':
        ['ft_mins5', 'ts_code', 'table_index', 'future_basic', '', 'y', '90'],

    'future_15min':
        ['ft_mins15', 'ts_code', 'table_index', 'future_basic', '', 'y', '180'],

    'future_30min':
        ['ft_mins30', 'ts_code', 'table_index', 'future_basic', '', 'y', '360'],

    'future_hourly':
        ['ft_mins60', 'ts_code', 'table_index', 'future_basic', '', 'y', '360'],

    'future_daily':
        ['future_daily', 'trade_date', 'trade_date', '19950417', '', '', ''],

    'future_weekly':
        ['fut_weekly', 'trade_date', 'trade_date', '19950417', '', '', ''],

    'future_monthly':
        ['fut_monthly', 'trade_date', 'trade_date', '19950417', '', '', ''],

    'options_1min':  # options_xmin 表应该通过trade_time(start/end)来切表索引，而不是通过table_index
        ['mins1', 'ts_code', 'table_index', 'opt_basic', '', 'y', '30'],

    'options_5min':
        ['mins5', 'ts_code', 'table_index', 'opt_basic', '', 'y', '90'],

    'options_15min':
        ['mins15', 'ts_code', 'table_index', 'opt_basic', '', 'y', '180'],

    'options_30min':
        ['mins30', 'ts_code', 'table_index', 'opt_basic', '', 'y', '360'],

    'options_hourly':
        ['mins60', 'ts_code', 'table_index', 'opt_basic', '', 'y', '360'],

    'options_daily':
        ['options_daily', 'trade_date', 'trade_date', '20150209', '', '', ''],

    'stock_adj_factor':
        ['adj_factors', 'trade_date', 'trade_date', '19901219', '', '', ''],

    'fund_adj_factor':
        ['fund_adj', 'trade_date', 'trade_date', '19980407', '', '', ''],

    'stock_indicator':
        ['daily_basic', 'trade_date', 'trade_date', '19990101', '', '', ''],

    'stock_indicator2':
        ['bak_daily', 'trade_date', 'trade_date', '19990101', '', '', ''],

    'hk_stock_indicator':  # tsfuncs
        ['hk_indicators', 'trade_date', 'hk_trade_date', '19900101', '', '', ''],

    'us_stock_indicator':  # tsfuncs
        ['us_indicators', 'trade_date', 'us_trade_date', '19600101', '', '', ''],

    'index_indicator':
        ['index_dailybasic', 'trade_date', 'trade_date', '20040102', '', '', ''],

    'index_weight':
        ['composite', 'trade_date', 'datetime', '20050408', '', '', ''],

    'income':
        ['income', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

    'balance':
        ['balance', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

    'cashflow':
        ['cashflow', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

    'financial':
        ['indicators', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

    'forecast':
        ['forecast', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

    'express':
        ['express', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

    'dividend':
        ['dividend', 'ts_code', 'table_index', 'stock_basic', '', '', ''],

    'top_list':
        ['top_list', 'trade_date', 'trade_date', '20050101', '', '', ''],

    'top_inst':
        ['top_inst', 'trade_date', 'trade_date', '19901211', '', '', ''],

    'sw_industry_detail':
        ['index_member_all', 'l1_code', 'list',
         '801010.SI, 801020.SI, 801030.SI, 801040.SI, 801050.SI, 801080.SI, '
         '801110.SI, 801120.SI, 801130.SI, 801140.SI, 801150.SI, 801160.SI, '
         '801170.SI, 801180.SI, 801200.SI, 801210.SI, 801230.SI, 801710.SI, '
         '801720.SI, 801730.SI, 801740.SI, 801750.SI, 801760.SI, 801770.SI, '
         '801780.SI, 801790.SI, 801880.SI, 801890.SI, 801950.SI, 801960.SI, '
         '801970.SI, 801980.SI',
         '', '', ''],

    'block_trade':
        ['block_trade', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'stock_holder_trade':
        ['stk_holdertrade', 'ann_date', 'datetime', '20100101', '', '', ''],

    'margin':
        ['margin', 'exchange_id', 'list', 'SSE,SZSE,BSE', '', '', ''],

    'margin_detail':
        ['margin_detail', 'trade_date', 'trade_date', '20190910', '', '', ''],

    'shibor':
        ['shibor', 'none', 'none', '', '', 'Y', '365'],

    'libor':
        ['libor', 'none', 'none', '', '', 'Y', '365'],

    'hibor':
        ['hibor', 'none', 'none', '', '', 'Y', '365'],

    'wz_index':
        ['wz_index', 'none', 'none', '', '', 'Y', '365'],

    'gz_index':
        ['gz_index', 'none', 'none', '', '', 'Y', '365'],

    'cn_gdp':
        ['cn_gdp', 'start', 'quarter', '1976Q4', '', '', ''],

    'cn_cpi':
        ['cn_cpi', 'start', 'month', '19760101', '', '', ''],

    'cn_ppi':
        ['cn_ppi', 'start', 'month', '19760101', '', '', ''],

    'cn_money':
        ['cn_money', 'start', 'month', '19760101', '', '', ''],

    'cn_sf':
        ['cn_sf', 'start', 'month', '19760101', '', '', ''],

    'cn_pmi':
        ['cn_pmi', 'start', 'month', '19760101', '', '', ''],
}

TUSHARE_REALTIME_API_MAP = {
    'realtime_bars':  # 实时行情数据
        ['realtime_min', 'ts_code', 'list', 'none', '', 'N', '', ''],
    'realtime_quotes':
        ['realtime_quote', 'ts_code', 'list', 'none', '', 'N', '', '']
}

AKSHARE_API_MAP = {

}

AKSHARE_REALTIME_API_MAP = {
    'realtime_bars':  # 实时行情数据
        ['not_implemented', 'symbols', 'list', 'none', '', 'N', '', ''],

    'realtime_quotes':
        ['not_implemented', 'symbols', 'list', 'none', '', 'N', '', '']
}

EASTMONEY_API_MAP = {  # 从EastMoney的数据API不区分asset_type，只要给出qt_code即可，因此index和stock共用API
    'stock_daily':
        ['stock_daily', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '30'],

    'stock_1min':
        ['stock_1min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '1'],

    'stock_5min':
        ['stock_5min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_15min':
        ['stock_15min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_30min':
        ['stock_30min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_hourly':
        ['stock_hourly', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_weekly':
        ['stock_weekly', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '100'],

    'stock_monthly':
        ['stock_monthly', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '300'],

    'index_daily':
        ['stock_daily', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '30'],

    'index_1min':
        ['stock_1min', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '1'],

    'index_5min':
        ['stock_5min', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '10'],

    'index_15min':
        ['stock_15min', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '10'],

    'index_30min':
        ['stock_30min', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '10'],

    'index_hourly':
        ['stock_hourly', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '10'],

    'index_weekly':
        ['stock_weekly', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '100'],

    'index_monthly':
        ['stock_monthly', 'qt_code', 'table_index', 'index_basic', 'SH,SZ', 'Y', '300'],

    'fund_daily':
        ['stock_daily', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '30'],

    'fund_1min':
        ['stock_1min', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '1'],

    'fund_5min':
        ['stock_5min', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '10'],

    'fund_15min':
        ['stock_15min', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '10'],

    'fund_30min':
        ['stock_30min', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '10'],

    'fund_hourly':
        ['stock_hourly', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '10'],

    'fund_weekly':
        ['stock_weekly', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '100'],

    'fund_monthly':
        ['stock_monthly', 'qt_code', 'table_index', 'fund_basic', 'SH,SZ', 'Y', '300'],

}

EASTMONEY_REALTIME_API_MAP = {
    'realtime_bars':  # 实时K线行情数据
        ['real_time_klines', 'qt_code', 'list', 'none', '', 'N', '', ''],

    'realtime_quotes':  # 实时报价数据
        ['real_time_quote', 'qt_code', 'list', 'none', '', 'N', '', '']
}

SINA_API_MAP = {
    'stock_daily':
        ['stock_daily', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '30'],

    'stock_1min':
        ['stock_1min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '1'],

    'stock_5min':
        ['stock_5min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_15min':
        ['stock_15min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_30min':
        ['stock_30min', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    'stock_hourly':
        ['stock_hourly', 'qt_code', 'table_index', 'stock_basic', '', 'Y', '10'],

    # SINA does not provide weekly/monthly data
}

SINA_REALTIME_API_MAP = {
    'realtime_bars':  # 实时K线行情数据
        ['realtime_klines', 'qt_code', 'list', 'none', '', 'N', '', ''],

    'realtime_quotes':  # 实时报价数据
        ['realtime_quote', 'qt_code', 'list', 'none', '', 'N', '', '']
}