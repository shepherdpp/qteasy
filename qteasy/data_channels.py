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


import pandas as pd

from .utilfuncs import str_to_list

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
import pandas as pd


def fetch_history_table_data(table, channel='tushare', **kwargs):
    """从网络获取本地数据表的历史数据，调用API的参数只能是一组数据

    1，根据table以及channel的不同，调用不同的数据API获取函数，获取数据
    2，数据API从模块中定义的各个MAP表中获取

    Parameters
    ----------
    table: str,
        数据表名，必须是API_MAP中定义的数据表
    channel: str, optional
        str: 数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'emoney'      : 从东方财富网获取金融数据
    **kwargs:
        用于下载金融数据的函数参数，或者读取本地csv文件的函数参数

    Returns
    -------
    pd.DataFrame:
        下载后并处理完毕的数据，DataFrame形式，仅含简单range-index格式
    """

    # 目前仅支持从tushare获取数据，未来可能增加新的API
    from .tsfuncs import acquire_data
    # 从指定的channel获取数据
    if channel == 'tushare':
        # 通过tushare的API下载数据
        api_name = TUSHARE_API_MAP[table][TUSHARE_API_MAP_COLUMNS.index('api')]
    elif channel == 'akshare':
        # 通过akshare的API下载数据
        api_name = AKSHARE_API_MAP[table][AKSHARE_API_MAP_COLUMNS.index('api')]
    elif channel == 'emoney':
        # 通过东方财富网的API下载数据
        api_name = EASTMONEY_API_MAP[table][EASTMONEY_API_MAP_COLUMNS.index('api')]
    else:
        raise NotImplementedError
    try:
        dnld_data = acquire_data(api_name, **kwargs)
    except Exception as e:
        raise Exception(f'{e}: data {table} can not be acquired from {channel}')

    return dnld_data


def fetch_batched_table_data(*, table, channel, arg_list, parallel, process_count, log,
                             chunk_size, download_batch_size, download_batch_interval) -> pd.DataFrame:
    """ 批量获取同一张数据表的数据，反复调用同一个API，但是传入一系列不同的参数

    Parameters
    ----------
    table: str,
        数据表名，必须是database中定义的数据表
    channel: str,
        数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'emoney'      : 从东方财富网获取金融数据
    arg_list: iterable
        用于下载数据的函数参数
    parallel: bool
        是否启用多线程下载数据
    process_count: int
        启用多线程下载时，同时开启的线程数，默认值为设备的CPU核心数
    """

    # 本函数解析arg_list中的参数，循环或者并行调用fetch_history_table_data函数获取
    # 数据，然后将数据合并成一个DataFrame返回
    raise NotImplementedError


def _parse_data_fetch_args(table, channel, symbols, start_date, end_date, freq, list_arg_filter, reversed_par_seq) -> dict:
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
        - 'emoney'      : 从东方财富网获取金融数据
    start_date: str, optional
        数据下载的开始日期
    end_date: str, optional
        数据下载的结束日期
    freq: str, optional
        数据下载的频率，支持以下选项(仅当数据类型为trade_time时)：
        - '1min':  1分钟频率
        - '5min':  5分钟频率
        - '15min': 15分钟频率
        - '30min': 30分钟频率
        - 'h':     1小时频率
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

    # get all tables in the API mapping
    arg_type = API_MAP[table][2]
    arg_range = API_MAP[table][3]

    # parse the filling args and pick the first filling arg value from the range

    arg_name = None

    if arg_type == 'list':
        arg_values = _parse_list_args(arg_range, list_arg_filter, reversed_par_seq)
    elif arg_type == 'datetime':
        arg_values = _parse_datetime_args(arg_range, start_date, end_date)
    elif arg_type == 'trade_date':
        arg_values = _parse_trade_date_args(arg_range, start_date, end_date)
    elif arg_type == 'trade_time':
        arg_values = _parse_trade_time_args(arg_range, start_date, end_date, freq)
    elif arg_type == 'quarter':
        arg_values = _parse_quarter_args(arg_range, start_date, end_date)
    elif arg_type == 'month':
        arg_values = _parse_month_args(arg_range, start_date, end_date)
    elif arg_type == 'table_index':
        arg_values = _parse_table_index_args(arg_range, symbols)
    else:
        raise ValueError('unexpected arg type:', arg_type)

    # build the args dict
    if arg_name is not None:
        kwargs = {arg_name: arg_values}
    else:
        kwargs = {}

    return kwargs

# ======================================
# 下面是一系列函数，针对不同的API主参数类型，生成下载数据的参数序列
# ======================================


def _parse_list_args(arg_range: str or [str], list_arg_filter: str or [str] = None, reversed: bool = False):
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
    reversed: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list generator:
        用于下载数据的参数序列
    """
    if isinstance(arg_range, str):
        arg_range = str_to_list(arg_range)

    if reversed:
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
        return (item for item in arg_range[list_idx_lower:list_idx_upper+1])

    return (item for item in arg_range if item in list_arg_filter)


def _parse_datetime_args(arg_range: str, start_date: str, end_date: str, reversed: bool = False):
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    arg_range: str,
        表示数据的时间范围的起始日期，如'20210101'表示从2021年1月1日开始
    start_date: str, YYYYMMDD
        数据下载的开始日期
    end_date: str, YYYYMMDD
        数据下载的结束日期
    reversed: bool, default False
        是否将参数序列反转，如果为True，则会将参数序列反转，用于下载数据时的优化

    Returns
    -------
    list:
        用于下载数据的参数序列
    """

    first_date = pd.to_datetime(arg_range)  # assert arg_range is a valid date
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if start_date < first_date:
        start_date = first_date

    if end_date < start_date:
        # reverse the start and end date if end date is earlier than start date
        start_date, end_date = end_date, start_date

    res = pd.date_range(start_date, end_date).strftime('%Y%m%d').to_list()

    if reversed:
        return res[::-1]
    else:
        return res


def _parse_trade_date_args(arg_range, start_date: str, end_date: str, reversed: bool = False):
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    raise NotImplementedError


def _parse_table_index_args(table_name, symbols):
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    table_name: str,
        数据表名，定义为basics的数据表，包含股票代码等基本信息
    symbols: str or list of str,
        用于下载数据的股票代码，如果给出了symbols，只有这些股票代码的数据会被下载

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    raise NotImplementedError


def _parse_quarter_args(arg_range, start_date, end_date) -> list:
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    raise NotImplementedError


def _parse_month_args(arg_range, start_date, end_date) -> list:
    """ 根据开始和结束日期，生成数据获取的参数序列

    Parameters
    ----------
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    raise NotImplementedError


def _parse_trade_time_args(arg_range, start_date, end_date, freq) -> list:
    """ 根据开始和结束日期，生成交易时间类型（分钟精度）数据获取的参数序列

    Parameters
    ----------
    start_date: str,
        数据下载的开始日期
    end_date: str,
        数据下载的结束日期
    freq: str,
        数据下载的频率，支持以下选项：
        - '1min':  1分钟频率
        - '5min':  5分钟频率
        - '15min': 15分钟频率
        - '30min': 30分钟频率
        - 'h':     1小时频率

    Returns
    -------
    list:
        用于下载数据的参数序列
    """
    raise NotImplementedError


def _parse_tables_to_fetch(tables, dtypes, freqs, asset_types, refresh_trade_calendar) -> set:
    """ 根据输入的参数，生成需要下载的数据表清单

    Parameters
    ----------
    tables: str or list of str,
        数据表名，必须是database中定义的数据表
    dtypes: str or list of str,
        数据表的数据类型，必须是database中定义的数据类型
    freqs: str or list of str,
        数据表的数据频率，必须是database中定义的数据频率
    asset_types: str or list of str,
        数据表的资产类型，必须是database中定义的资产类型
    refresh_trade_calendar: bool,
        是否更新trade_calendar表，如果为True，则会下载trade_calendar表的数据

    Returns
    -------
    set:
        需要下载的数据表清单
    """
    raise NotImplementedError


def fetch_realtime_price_data(channel, qt_code, **kwargs):
    """ 从网络数据提供商获取实时股票价格数据

    如果一个Channel提供了相应的实时数据获取API，这些API会被记录在MAP表中
    以'real_time'为key的数据列中，这些API会被调用以获取实时数据

    Parameters
    ----------
    channel: str,
        数据获取渠道，金融数据API，支持以下选项:
        - 'eastmoney': 通过东方财富网的API获取数据
        - 'tushare':   从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'other':     NotImplemented 其他金融数据API，尚未开发
    qt_code: str or list of str
        用于下载金融数据的函数参数，需要输入完整的ts_code，表示股票代码

    Returns
    -------
    pd.DataFrame:
        下载后并处理完毕的数据，DataFrame形式，仅含简单range-index格式
        columns: qt_code, trade_time, open, high, low, close, vol, amount
    """

    # TODO: 将该函数移动到别的文件中如datachannels.py
    #  这个函数的功能与DataSource的定义不符。
    #  在DataSource中应该有一个API专司数据的清洗，以便任何形式的数据都
    #  可以在清洗后被写入特定的数据表，而数据的获取则不应该放在DataSource中
    #  DataSource应该被设计为专精与数据的存储接口，而不是数据获取接口
    #  同样的道理适用于refill_local_source()函数

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
            err = ValueError(f'ts_code must be given while channel == "tushare"')
            raise err
        try:
            dnld_data = acquire_data_from_ts(api_name, ts_code=symbols, freq=realtime_data_freq)
        except Exception as e:
            raise Exception(f'data {table} can not be acquired from tushare\n{e}')

        # 从下载的数据中提取出需要的列
        dnld_data = dnld_data[['code', 'time', 'open', 'high', 'low', 'close', 'volume', 'amount']]
        dnld_data = dnld_data.rename(columns={ 'code':   'ts_code', 'time':   'trade_time', 'volume': 'vol',
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
        table_freq_map = { '1min':  1, '5min':  5, '15min': 15, '30min': 30, 'h':     60,
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


def fetch_tables(channel, *, tables=None, dtypes=None, freqs=None, asset_types=None, refresh_trade_calendar=False,
                 symbols=None, start_date=None, end_date=None, list_arg_filter=None, reversed_par_seq=False,
                 parallel=True, process_count=None, chunk_size=100, download_batch_size=0,
                 download_batch_interval=0, log=False) -> dict:
    """ 大批量下载多张数据表中的数据，并将下载的数据组装成pd.DataFrame，检查数据的完整性
    完成数据清洗并返回可以直接写入数据表中的数据。

    本函数逐个下载指定数据表中的数据，目的是大批量下载全部数据，因此仅支持时间分段下载，不允许
    指定单个证券代码下载数据。

    本函数会解析输入的参数，如果参数范围过大导致下载的数据超出数据提供商的限制，会根据数据MAP表
    中定义的规则将数据拆分成多组，分批下载。

    下载过程可以并行进行，也可以顺序进行，可以设置下载的并行线程数，也可以设置下载的批次大小和
    批次间隔时间。

    数据下载的过程可以记录到日志中，以便查看下载的进度和结果

    Parameters
    ----------
    channel: str,
        数据获取渠道，金融数据API，支持以下选项:
        - 'tushare'     : 从Tushare API获取金融数据，请自行申请相应权限和积分
        - 'akshare'     : 从AKshare API获取金融数据
        - 'emoney'      : 从东方财富网获取金融数据
    == 前面四个参数用于筛选需要下载的数据表，必须至少输入一个 ==
    tables: str or list of str, default: None
        数据表名，必须是database中定义的数据表，用于指定需要下载的数据表
    dtypes: str or list of str, default: None
        需要下载的数据类型，用于进一步筛选数据表，必须是database中定义的数据类型
    freqs: str or list of str, default: None
        需要下载的数据频率，用于进一步筛选数据表，必须是database中定义的数据频率
    asset_types: str or list of str, default: None
        需要下载的数据资产类型，用于进一步筛选数据表，必须是database中定义的资产类型

    == 第五个参数用于特别指定更新trade_calendar表 ==
    refresh_trade_calendar: Bool, Default False
        是否更新trade_calendar表，如果为True，则会下载trade_calendar表的数据

    == 后续几个参数用于下载数据的参数设置 ==
    start_date: str YYYYMMDD
        限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
    end_date: str YYYYMMDD
        限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
    list_arg_filter: str or list of str, default: None  **注意，不是所有情况下filter_arg参数都有效**
        限定下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
        参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。
        如果filter_arg为None，则下载所有数据。
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

    == 最后几个参数用于下载数据的设置 ==
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
    log: Bool, Default False
        是否记录数据下载日志

    Returns
    -------
    dict:
        返回一个字典，包含下载的数据DataFrame
    """

    # 1, 解析需要下载的数据表清单
    table_list = _parse_tables_to_fetch(tables, dtypes, freqs, asset_types, refresh_trade_calendar)

    result_data = {}
    # 2, 循环下载数据表，单独对每个数据表进行参数拆解
    for table in table_list:
        # 2.1, 解析下载数据的参数
        data_fetch_args = _parse_data_fetch_args(
                table=table,
                channel=channel,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                freq=freqs,
                list_arg_filter=list_arg_filter,
                reversed_par_seq=reversed_par_seq,
        )
        # 2.2, 批量下载数据
        dnld_data = fetch_batched_table_data(
                table=table,
                channel=channel,
                arg_list=data_fetch_args,
                parallel=parallel,
                process_count=process_count,
                log=log,
                chunk_size=chunk_size,
                download_batch_size=download_batch_size,
                download_batch_interval=download_batch_interval,
        )
        result_data[table] = dnld_data

    return result_data


TUSHARE_API_MAP_COLUMNS = [
    'api',  # 1, 从tushare获取数据时使用的api名
    'fill_arg_name',  # 2, 从tushare获取数据时使用的api参数名
    'fill_arg_type',  # 3, 从tushare获取数据时使用的api参数类型
    'arg_rng',  # 4, 从tushare获取数据时使用的api参数取值范围
    'arg_allowed_code_suffix',  # 5, 从tushare获取数据时使用的api参数允许的股票代码后缀
    'arg_allow_start_end',  # 6, 从tushare获取数据时使用的api参数是否允许start_date和end_date
    'start_end_chunk_size',  # 7, 从tushare获取数据时使用的api参数start_date和end_date时的分段大小
]

TUSHARE_API_MAP = {
    'real_time':  # 实时行情数据
        ['get_realtime_quotes', 'symbols', 'list', 'none', '', 'N', '', ''],

    'trade_calendar':
        ['trade_cal', 'exchange', 'list', 'SSE, SZSE, CFFEX, SHFE, CZCE, DCE, INE', '', 'N', '', ''],

    'stock_names':
        ['namechange', 'ts_code', 'table_index', 'stock_basic', '', 'Y', ''],

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

    'HS_money_flow':
        ['moneyflow_hsgt', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'HS_top10_stock':
        ['hsgt_top10', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'HK_top10_stock':
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
        ['future_weekly', 'trade_date', 'trade_date', '19950417', '', '', ''],

    'future_monthly':
        ['future_monthly', 'trade_date', 'trade_date', '19950417', '', '', ''],

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
        ['index_member_all', 'ts_code', 'table_index', 'stock_basic', '', '', ''],

    'block_trade':
        ['block_trade', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'stock_holder_trade':
        ['stk_holdertrade', 'trade_date', 'trade_date', '20100101', '', '', ''],

    'margin':
        ['margin', 'exchange_id', 'list', 'SSE,SZSE,BSE', '', '', ''],

    'margin_detail':
        ['margin_detail', 'trade_date', 'trade_date', '20190910', '', '', ''],

    'shibor':
        ['shibor', 'date', 'datetime', '20000101', '', '', ''],

    'libor':
        ['libor', 'date', 'datetime', '20000101', '', '', ''],

    'hibor':
        ['hibor', 'date', 'datetime', '20000101', '', '', ''],

    'wz_index':
        ['wz_index', 'none', '', '', '', '', ''],

    'gz_index':
        ['gz_index', 'none', '', '', '', '', ''],

    'cn_gdp':
        ['cn_gdp', 'start', 'quarter', '1976Q4', '', '', ''],

    'cn_cpi':
        ['cn_cpi', 'start', 'month', '197601', '', '', ''],

    'cn_ppi':
        ['cn_ppi', 'start', 'month', '197601', '', '', ''],

    'cn_money':
        ['cn_m', 'start', 'month', '197601', '', '', ''],

    'cn_sf':
        ['sf_month', 'start', 'month', '197601', '', '', ''],

    'cn_pmi':
        ['cn_pmi', 'start', 'month', '197601', '', '', ''],
}

AKSHARE_API_MAP_COLUMNS = [
    'api',  # 1, 从akshare获取数据时使用的api名
    'ak_fill_arg_name',  # 2, 从akshare获取数据时使用的api参数名
    'ak_fill_arg_type',  # 3, 从akshare获取数据时使用的api参数类型
    'ak_arg_rng',  # 4, 从akshare获取数据时使用的api参数取值范围
]

AKSHARE_API_MAP = {

}

EASTMONEY_API_MAP_COLUMNS = [
    'api',  # 1, 从东方财富网获取数据时使用的api名
    'em_fill_arg_name',  # 2, 从东方财富网获取数据时使用的api参数名
    'em_fill_arg_type',  # 3, 从东方财富网获取数据时使用的api参数类型
    'em_arg_rng',  # 4, 从东方财富网获取数据时使用的api参数取值范围
    'em_arg_allowed_code_suffix',  # 5, 从东方财富网获取数据时使用的api参数允许的股票代码后缀
]

EASTMONEY_API_MAP = {

}
