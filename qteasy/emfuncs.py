# coding=utf-8
# ======================================
# File:     emfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-11-01
# Desc:
#   Interfaces to eastmoney data
# functions and api, as the default
# api in qteasy, emfuncs provides basic
# functions to acquire price k-lines.
# ======================================

from urllib.parse import urlencode
import pandas as pd
import requests

from concurrent.futures import as_completed, ThreadPoolExecutor

from .utilfuncs import str_to_list


# eastmoney interface function, call this function to extract data
def acquire_data(api_name, **kwargs):
    """ eastmoney接口函数，根据根据table的内容调用相应的eastmoney API下载数据，并以DataFrame的形式返回数据"""
    func = globals()[api_name]
    res = func(**kwargs)
    return res


def gen_eastmoney_code(rawcode: str) -> str:
    """
    生成东方财富专用的secid: 1.000001 0.399001等

    沪市股票以1开头，深市及北交所股票以0开头
    如果rawcode中未指明市场，则根据六位数的第一位判断，当第一位是6是判定未沪市，否则判定为深市
    此时默认所有代码都为股票，即000001会被判定为0.000001(平安银行）而不是1.000001（上证指数)
    只有给出后缀时，才根据市场判定正确的secid

    Parameters
    ----------
    rawcode：str
        6 位股票代码按东方财富格式生成的字符串

    Returns
    -------
    secid: str
        东方财富证券代码

    Examples
    --------
    >>> gen_eastmoney_code('000001')
    0.000001
    >>> gen_eastmoney_code('000001.SZ')
    0.000001
    >>> gen_eastmoney_code('000001.SH')
    1.000001
    """

    rawcode = rawcode.split('.')
    if len(rawcode) == 1:
        rawcode = rawcode[0]
        if rawcode[0] != '6':
            return f'0.{rawcode}'
        return f'1.{rawcode}'
    if len(rawcode) == 2:
        market = rawcode[1]
        rawcode = rawcode[0]
        if market in ['SZ', 'BJ']:
            return f'0.{rawcode}'
        elif market == 'SH':
            return f'1.{rawcode}'


def get_k_history(code: str, beg: str = '16000101', end: str = '20500101', klt: int = 1, fqt: int = 1, verbose=False) -> pd.DataFrame:
    """ 功能获取k线数据

    Parameters
    ----------
    code: str
        6 位股票代码
    beg: str, default '16000101'
        开始日期 例如 20200101
    end: str, default '20500101'
        结束日期 例如 20200201
    klt: int , default 1
        k线间距 默认为 101 即日k
        klt:1 1 分钟
        klt:5 5 分钟
        klt:101 日
        klt:102 周
    fqt: str, default 1
        复权方式
        不复权 : 0
        前复权 : 1
        后复权 : 2
    verbose: bool, default False
        是否返回更多信息（名称，昨日收盘价）

    Return
    ------
    DateFrame : 包含股票k线数据，包含以下字段
        trade_time: str, 日期
        name: str, 股票名称，仅当verbose=True时返回
        pre_close: float, 昨日收盘价，仅当verbose=True时返回
        open: float, 开盘价
        close: float, 收盘价
        high: float, 最高价
        low: float, 最低价
        vol: float, 成交量
        amount: float, 成交额
    未读取到数据时返回空DataFrame
    """

    EastmoneyKlines = {
        'f51': 'trade_time',
        'f52': 'open',
        'f53': 'close',
        'f54': 'high',
        'f55': 'low',
        'f56': 'vol',
        'f57': 'amount',
    }
    EastmoneyHeaders = {

        'User-Agent':      'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
        'Accept':          '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer':         'http://quote.eastmoney.com/center/gridlist.html',
    }
    fields = list(EastmoneyKlines.keys())
    columns = list(EastmoneyKlines.values())
    fields2 = ",".join(fields)
    secid = gen_eastmoney_code(code)
    params = (
        ('fields1', 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13'),
        ('fields2', fields2),
        ('beg', beg),
        ('end', end),
        ('rtntype', '6'),
        ('secid', secid),
        ('klt', f'{klt}'),
        ('fqt', f'{fqt}'),
    )
    base_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    # base_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    url = base_url + '?' + urlencode(params)
    try:
        json_response = requests.get(
                url, headers=EastmoneyHeaders).json()
    except:
        return pd.DataFrame()
    data = json_response['data']
    if data is None:
        return pd.DataFrame()
    klines = data['klines']
    rows = []
    for _kline in klines:
        kline = _kline.split(',')
        rows.append(kline)
    df = pd.DataFrame(rows, columns=columns)
    if verbose:
        df['name'] = data['name']
        df['pre_close'] = data['prePrice']
    return df


def stock_daily(symbols, start, end):
    """ 获取股票日线数据
    Parameters
    ----------
    symbols : list
        股票代码列表
    start : str
        开始日期
    end : str
        结束日期
    Returns
    -------
    DataFrame
        包含股票日线数据
    """
    data = []
    for symbol in symbols:
        code = symbol.split('.')[0]
        df = get_k_history(code, start, end, klt=101)
        df['symbol'] = symbol
        data.append(df)
    return pd.concat(data)


def stock_mins(symbols, start, end, freq='1min'):
    """ 获取股票分钟线数据
    Parameters
    ----------
    symbols : list
        股票代码列表
    start : str
        开始日期
    end : str
        结束日期
    freq : str, optional, default '1min'
        频率，支持'1min', '5min', '15min', '30min', '60min'
    Returns
    -------
    DataFrame
        包含股票1分钟线数据
    """
    data = []
    freq_map = {
        '1min': 1,
        '5min': 5,
        '15min': 15,
        '30min': 30,
        '60min': 60,
    }
    for symbol in symbols:
        code = symbol.split('.')[0]
        df = get_k_history(code, start, end, klt=1)
        df['symbol'] = symbol
        data.append(df)
    return pd.concat(data)


def stock_live_kline_price(symbols, freq='D', verbose=False, parallel=True, timezone='local'):
    """ 获取股票当前最新日线数据，数据实时更新
    Parameters
    ----------
    symbols : str or list of str
        股票代码
    freq : str
        数据更新频率，目前仅支持日线数据
    verbose : bool, default False
        是否返回更多信息（名称，昨日收盘价）
    parallel : bool, default True
        是否使用多进程加速数据获取
    timezone : str, default 'local'
        时区，默认值为'local'，即本地时区, 也可以设置为'Asia/Shanghai'等以强制转换时区

    Returns
    -------
    DataFrame
        包含股票日线数据, 包含以下字段
        datetime: str, 日期
        symbol: str, 股票代码
        open: float, 开盘价
        close: float, 收盘价
        high: float, 最高价
        low: float, 最低价
        vol: float, 成交量
        amount: float, 成交额
    """
    data = []
    if isinstance(symbols, str):
        symbols = str_to_list(symbols)
    if timezone == 'local':
        today = pd.Timestamp.today().strftime('%Y%m%d')
    else:
        today = pd.Timestamp.today(tz=timezone).strftime('%Y%m%d')
    klt = 101  # k line type, 101 for daily
    if freq.upper() == 'W':
        klt = 102
    if freq.upper() == 'M':
        klt = 103
    # 使用ProcessPoolExecutor, as_completed加速数据获取，当parallel=False时，不使用多进程
    if parallel:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(get_k_history, code=symbol, beg=today, klt=klt, verbose=verbose): symbol
                for symbol
                in symbols
            }
            for future in as_completed(futures):
                try:
                    df = future.result(timeout=2)
                    symbol = futures[future]
                except TimeoutError:
                    continue
                except Exception as exc:
                    print(f'{exc} generated an exception: {exc}')
                else:
                    if df.empty:
                        continue
                    df['symbol'] = symbol
                    data.append(df.iloc[-1:, :])
    else:  # parallel == False, 不使用多进程
        for symbol in symbols:
            df = get_k_history(symbol, beg=today, klt=klt, verbose=verbose)
            if df.empty:
                continue
            df['symbol'] = symbol
            data.append(df.iloc[-1:, :])
    try:
        data = pd.concat(data)
    except:
        return pd.DataFrame()  # 返回空DataFrame
    if verbose:
        data = data.reindex(
                columns=['trade_time', 'symbol', 'name', 'pre_close', 'open', 'close', 'high', 'low', 'vol', 'amount']
        )
    else:
        data = data.reindex(
                columns=['trade_time', 'symbol', 'open', 'close', 'high', 'low', 'vol', 'amount']
        )
    data.set_index('trade_time', inplace=True)
    return data
