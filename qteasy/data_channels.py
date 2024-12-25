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


# TODO: This function belongs to datachannels.py
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
    # TODO: 将该函数移动到别的文件中如datachannels.py
    #  这个函数的功能与DataSource的定义不符。
    #  在DataSource中应该有一个API专司数据的清洗，以便任何形式的数据都
    #  可以在清洗后被写入特定的数据表，而数据的获取则不应该放在DataSource中
    #  DataSource应该被设计为专精与数据的存储接口，而不是数据获取接口
    #  同样的道理适用于refill_local_source()函数

    # 目前仅支持从tushare获取数据，未来可能增加新的API
    from .tsfuncs import acquire_data
    if not isinstance(table, str):
        err = TypeError(f'table name should be a string, got {type(table)} instead.')
        raise err
    if table not in TABLE_MASTERS.keys():
        raise KeyError(f'Invalid table name {table}')
    if not isinstance(channel, str):
        err = TypeError(f'channel should be a string, got {type(channel)} instead.')
        raise err
    if channel not in AVAILABLE_CHANNELS:
        raise KeyError(f'Invalid channel name {channel}')

    column, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
    # 从指定的channel获取数据
    if channel == 'df':
        # 通过参数传递的DF获取数据
        if df is None:
            err = ValueError(f'a DataFrame must be given while channel == "df"')
            raise err
        if not isinstance(df, pd.DataFrame):
            err = TypeError(f'local df should be a DataFrame, got {type(df)} instead.')
            raise err
        dnld_data = df
    elif channel == 'csv':
        # 读取本地csv数据文件获取数据
        if f_name is None:
            err = ValueError(f'a file path and name must be given while channel == "csv"')
            raise err
        if not isinstance(f_name, str):
            err = TypeError(f'file name should be a string, got {type(df)} instead.')
            raise err
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
            raise Exception(f'{e}: data {table} can not be acquired from tushare')
    else:
        raise NotImplementedError
    res = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
    return res


# TODO: this function belongs to datachannels.py
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

    # TODO: 将该函数移动到别的文件中如datachannels.py
    #  这个函数的功能与DataSource的定义不符。
    #  在DataSource中应该有一个API专司数据的清洗，以便任何形式的数据都
    #  可以在清洗后被写入特定的数据表，而数据的获取则不应该放在DataSource中
    #  DataSource应该被设计为专精与数据的存储接口，而不是数据获取接口
    #  同样的道理适用于refill_local_source()函数

    # 目前支持从tushare和eastmoney获取数据，未来可能增加新的API
    if not isinstance(table, str):
        err = TypeError(f'table name should be a string, got {type(table)} instead.')
        raise err
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
            err = ValueError(f'ts_code must be given while channel == "tushare"')
            raise err
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


# TODO: This function belongs to DataChannel class, not DataSource
def refill_local_source(self, tables=None, dtypes=None, freqs=None, asset_types=None, start_date=None,
                        end_date=None, list_arg_filter=None, symbols=None, merge_type='update',
                        reversed_par_seq=False, parallel=True, process_count=None, chunk_size=100,
                        download_batch_size=0, download_batch_interval=0, refresh_trade_calendar=False,
                        log=False) -> None:
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
    download_batch_size: int, default 0
        为了降低下载数据时的网络请求频率，可以在完成一批数据下载后，暂停一段时间再继续下载
        该参数指定了每次暂停之前最多可以下载的次数，该参数只有在parallel=False时有效
        如果为0，则不暂停，一次性下载所有数据
    download_batch_interval: int, default 0
        为了降低下载数据时的网络请求频率，可以在完成一批数据下载后，暂停一段时间再继续下载
        该参数指定了每次暂停的时间，单位为秒，该参数只有在parallel=False时有效
        如果<=0，则不暂停，立即开始下一批数据下载
    refresh_trade_calendar: Bool, Default False
        是否强制刷新交易日历，如果为True，将下载最新的交易日历数据，如果为False，仅在交易日历数据不足时下载
    log: Bool, Default False
        是否记录数据下载日志

    Returns
    -------
    None

    """

    from .tsfuncs import acquire_data
    # 1 参数合法性检查 TODO: 参数检查在core.py中完成，这里只需要调用即可
    if (tables is None) and (dtypes is None):
        raise KeyError(f'tables and dtypes can not both be None.')
    if tables is None:
        tables = []
    if dtypes is None:
        dtypes = []
    valid_table_values = list(TABLE_MASTERS.keys()) + TABLE_USAGES + ['all']
    if not isinstance(tables, (str, list)):
        err = TypeError(f'tables should be a list or a string, got {type(tables)} instead.')
        raise err
    if isinstance(tables, str):
        tables = str_to_list(tables)
    if not all(item.lower() in valid_table_values for item in tables):
        raise KeyError(f'some items in tables list are not valid: '
                       f'{[item for item in tables if item not in valid_table_values]}')
    if not isinstance(dtypes, (str, list)):
        err = TypeError(f'dtypes should be a list of a string, got {type(dtypes)} instead.')
        raise err
    if isinstance(dtypes, str):
        dtypes = str_to_list(dtypes)

    if chunk_size <= 0:
        chunk_size = 100

    if download_batch_size <= 0:
        download_batch_size = 999999999999  # 一个很大的数，保证不会暂停下载

    if download_batch_interval <= 0:
        download_batch_interval = 0

    code_start = None
    code_end = None
    if symbols is not None:
        if not isinstance(symbols, (str, list)):
            err = TypeError(f'code_range should be a string or list, got {type(symbols)} instead.')
            raise err
        if isinstance(symbols, str):
            if len(str_to_list(symbols, ':')) == 2:
                code_start, code_end = str_to_list(symbols, ':')
                symbols = None
            else:
                symbols = str_to_list(symbols, ',')

    if list_arg_filter is not None:
        if not isinstance(list_arg_filter, (str, list)):
            err = TypeError(f'list_arg_filter should be a string or list, got {type(list_arg_filter)} instead.')
            raise err
        if isinstance(list_arg_filter, str):
            list_arg_filter = str_to_list(list_arg_filter, ',')

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
        for item in dtypes:  # 如果给出了dtypes，进一步筛选tables中的表，删除不需要的
            tables_to_keep = set()
            for tbl, schema in table_master.schema.items():  # iteritems()在pandas中已经被废弃
                if item.lower() in TABLE_SCHEMA[schema]['columns']:
                    tables_to_keep.add(tbl)
            tables_to_refill.intersection_update(
                    tables_to_keep
            )

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

        # 检查trade_calendar中是否有足够的数据，如果没有，需要包含trade_calendar表：
        if 'trade_calendar' not in tables_to_refill:
            if refresh_trade_calendar:
                tables_to_refill.add('trade_calendar')
            else:
                # 检查trade_calendar中是否已有数据，且最新日期是否足以覆盖本周，如果没有数据或数据不足，也需要添加该表
                latest_calendar_date = self.get_table_info('trade_calendar', print_info=False)['pk_max2']
                try:
                    latest_calendar_date = pd.to_datetime(latest_calendar_date)
                    present_week_day = pd.Timedelta(7, 'd') + pd.to_datetime('today')
                    if present_week_day >= pd.to_datetime(latest_calendar_date):
                        tables_to_refill.add('trade_calendar')
                except:
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
        # 生成start和end参数，如果需要的话
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
        # 生成其他参数，根据不同的fill_type生成不同的参数序列
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
            # 如果参数是一个列表，直接使用这个列表作为参数序列，除非给出了list_arg_filter
            arg_coverage = str_to_list(cur_table_info.arg_rng) if list_arg_filter is None else list_arg_filter
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
                with ThreadPoolExecutor(max_workers=process_count) as worker:
                    '''
                    这里如果直接使用fetch_history_table_data会导致程序无法运行，原因不明，目前只能默认通过tushare接口获取数据
                    通过TABLE_MASTERS获取tushare接口名称，并通过acquire_data直接通过tushare的API获取数据
                    '''
                    api_name = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('tushare')]
                    futures = {}
                    submitted = 0
                    for kw in all_kwargs:
                        futures.update({worker.submit(acquire_data, api_name, **kw): kw})
                        submitted += 1
                        if (download_batch_interval != 0) and (submitted % download_batch_size == 0):
                            progress_bar(submitted, total, f'<{table}>: Submitting tasks, '
                                                           f'Pausing for {download_batch_interval} sec...')
                            time.sleep(download_batch_interval)
                    # futures = {worker.submit(acquire_data, api_name, **kw): kw
                    #            for kw in all_kwargs}
                    progress_bar(0, total, f'<{table}>: estimating time left...')
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
                                                       f'{total_written}wrtn/{time_remain} left')

                    total_written += self.update_table_data(table, dnld_data)
            else:
                progress_bar(0, total, f'<{table}> estimating time left...')
                for kwargs in all_kwargs:
                    df = self.fetch_history_table_data(table, channel='tushare', **kwargs)
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

                    if (download_batch_interval != 0) and (completed % download_batch_size == 0):
                        progress_bar(completed, total, f'<{table}:{list(kwargs.values())[0]}>'
                                                       f'{total_written}wrtn/Pausing for '
                                                       f'{download_batch_interval} sec...')
                        time.sleep(download_batch_interval)
                    else:
                        progress_bar(completed, total, f'<{table}:{list(kwargs.values())[0]}>'
                                                       f'{total_written}wrtn/{time_remain} left')
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
            msg = f'\n{str(e)}: \ndownload process interrupted at [{table}]:' \
                          f'<{arg_coverage[0]}>-<{arg_coverage[completed - 1]}>\n' \
                          f'{total_written} rows downloaded, will proceed with next table!'
            warnings.warn(msg)


TUSHARE_API_PARAM_COLUMNS = {
    'api',  # 1, 从tushare获取数据时使用的api名
    'fill_arg_name',  # 2, 从tushare获取数据时使用的api参数名
    'fill_arg_type',  # 3, 从tushare获取数据时使用的api参数类型
    'arg_rng',  # 4, 从tushare获取数据时使用的api参数取值范围
    'arg_allowed_code_suffix',  # 5, 从tushare获取数据时使用的api参数允许的股票代码后缀
    'arg_allow_start_end',  # 6, 从tushare获取数据时使用的api参数是否允许start_date和end_date
    'start_end_chunk_size',  # 7, 从tushare获取数据时使用的api参数start_date和end_date时的分段大小
}

TUSHARE_API_PARAMS = {
    'trade_calender': ['trade_cal', 'exchange', 'list', 'SSE,SZSE,BSE,CFFEX,SHFE,CZCE,DCE,INE,XHKG', '', '', '',],
    'stock_basic': ['stock_basic', 'exchange', 'list', 'SSE,SZSE,BSE', '', '', '',]
}

AKSHARE_API_PARAM_COLUMNS = {
    'akshare',  # 13, 从akshare获取数据时使用的api名
    'ak_fill_arg_name',  # 14, 从akshare获取数据时使用的api参数名
    'ak_fill_arg_type',  # 15, 从akshare获取数据时使用的api参数类型
    'ak_arg_rng',  # 16, 从akshare获取数据时使用的api参数取值范围
}

AKSHARE_API_PARAMS = {

}

EASTMONEY_API_PARAM_COLUMNS = {
    'eastmoney',  # 8, 从东方财富网获取数据时使用的api名
    'em_fill_arg_name',  # 9, 从东方财富网获取数据时使用的api参数名
    'em_fill_arg_type',  # 10, 从东方财富网获取数据时使用的api参数类型
    'em_arg_rng',  # 11, 从东方财富网获取数据时使用的api参数取值范围
    'em_arg_allowed_code_suffix',  # 12, 从东方财富网获取数据时使用的api参数允许的股票代码后缀
}

EASTMONEY_API_PARAMS = {

}
