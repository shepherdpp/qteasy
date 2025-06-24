# coding=utf-8
# ======================================
# File:     sinafuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-06-24
# Desc:
#   Interfaces to sina finance data
# functions and api, as the default
# api in qteasy, sinafuncs provides basic
# functions to acquire price k-lines.
# ======================================

import time
import datetime
import pandas as pd
import numpy as np
import requests
from urllib.parse import urlencode

from qteasy.utilfuncs import (
    prev_market_trade_day, retry,
    format_str_to_float,
)

ERRORS_TO_CHECK_ON_RETRY = Exception

sina_finance_freq_map = {
    '1min':  1,
    '5min':  5,
    '15min': 15,
    '30min': 30,
    '60min': 60,
    'h':     60,
    'd':     101,
    'w':     102,
    'm':     103,
}

dc_cookies = {
    "qgqp_b_id":  "cf8b058a05d005ca7fb2afc14957f250",
    "st_si":      "72907886672492",
    "st_asi":     "delete",
    "HAList":     "ty-1-688720-N%u827E%u68EE%2Cty-0-873122-%u4E2D%u7EBA%u6807",
    "st_pvi":     "02194384728897",
    "st_sp":      "2023-12-06%2016%3A05%3A53",
    "st_inirUrl": "https%3A%2F%2Fquote.eastmoney.com%2Fcenter%2Fgridlist.html",
    "st_sn":      "11",
    "st_psi":     "20231206170058129-113200313000-8845421016"
}

dc_headers = {
    "Connection":      "keep-alive",
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
    "Accept":          "*/*",
    "Sec-Fetch-Site":  "same-site",
    "Sec-Fetch-Mode":  "no-cors",
    "Sec-Fetch-Dest":  "script",
    "Referer":         "https://quote.eastmoney.com/kcb/688720.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

LIVE_QUOTE_COLS = ['NAME', 'OPEN', 'PRE_CLOSE', 'PRICE', 'HIGH', 'LOW', 'BID', 'ASK', 'VOLUME', 'AMOUNT', 'B1_V',
                   'B1_P',
                   'B2_V', 'B2_P', 'B3_V', 'B3_P', 'B4_V', 'B4_P', 'B5_V', 'B5_P', 'A1_V', 'A1_P', 'A2_V', 'A2_P',
                   'A3_V', 'A3_P', 'A4_V', 'A4_P', 'A5_V', 'A5_P', 'DATE', 'TIME', 'TS_CODE']

LIVE_QUOTE_COLS_REINDEX = ['NAME', 'TS_CODE', 'DATE', 'TIME', 'OPEN', 'PRE_CLOSE', 'PRICE', 'HIGH', 'LOW', 'BID', 'ASK',
                           'VOLUME', 'AMOUNT', 'B1_V', 'B1_P',
                           'B2_V', 'B2_P', 'B3_V', 'B3_P', 'B4_V', 'B4_P', 'B5_V', 'B5_P', 'A1_V', 'A1_P', 'A2_V',
                           'A2_P',
                           'A3_V', 'A3_P', 'A4_V', 'A4_P', 'A5_V', 'A5_P']


# eastmoney interface function, call this function to extract data
def acquire_data(api_name, **kwargs):
    """ eastmoney接口函数，根据根据table的内容调用相应的eastmoney API下载数据，并以DataFrame的形式返回数据"""

    if 'retry_count' in kwargs:
        data_download_retry_count = kwargs.pop('retry_count')
    else:
        data_download_retry_count = 3

    if 'retry_wait' in kwargs:
        data_download_retry_wait = kwargs.pop('retry_wait')
    else:
        data_download_retry_wait = 0.01

    if 'retry_backoff' in kwargs:
        data_download_retry_backoff = kwargs.pop('retry_backoff')
    else:
        data_download_retry_backoff = 2

    retry_decorator = retry(
            exception_to_check=ERRORS_TO_CHECK_ON_RETRY,
            mute=True,
            tries=data_download_retry_count,
            delay=data_download_retry_wait,
            backoff=data_download_retry_backoff,
    )
    try:
        func = globals()[api_name]
    except KeyError:
        raise KeyError(f'undefined API {api_name} for eastmoney')
    decorated_func = retry_decorator(func)

    res = decorated_func(**kwargs)
    return res


def _format_em_str(x):
    return float(x / 100) if x != "-" else 0


def _format_em_date_str(date_str):
    return date_str.replace("-", "")


def _timestamp_to_time(time_stamp, form_date="%Y-%m-%d %H:%M:%S"):
    time_stamp = int(str(time_stamp)[0:10])
    date_array = datetime.datetime.fromtimestamp(time_stamp)
    other_style_time = date_array.strftime(form_date)
    return str(other_style_time)


def _gen_sina_code(rawcode: str) -> str:
    """
    生成东方财富专用的secid: 1.000001 0.399001等

    沪市股票/指数/ETF以1开头，深市及北交所股票/指数/ETF以0开头
    如果rawcode中未指明市场，则根据六位数的第一位判断，当第一位是6是判定为沪市，否则判定为深市
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
    >>> _gen_sina_code('000001')
    0.000001
    >>> _gen_sina_code('000001.SZ')
    0.000001
    >>> _gen_sina_code('000001.SH')
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


def _get_k_history(code: str, beg: str = '16000101', end: str = '20500101',
                   klt: int = 1, fqt: int = 1, verbose=False) -> pd.DataFrame:
    """ 功能获取k线数据

    Parameters
    ----------
    code: str
        6 位股票代码或带市场标识的qt_code
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
        # 'f50': 'unknown',
        'f51': 'trade_time',
        'f52': 'open',
        'f53': 'close',
        'f54': 'high',
        'f55': 'low',
        'f56': 'vol',
        'f57': 'amount',
        'f58': 'range',
        'f59': 'pct_chg',
        'f60': 'change',
        'f61': 'turnover',
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
    secid = _gen_sina_code(code)
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
        df['pre_close'] = np.NaN
    for col in ['open', 'high', 'low', 'close', 'vol', 'amount', 'change', 'pct_chg', 'range', 'turnover']:
        df[col] = df[col].apply(format_str_to_float)  # 将数据转化为float格式
    if klt >= 101:
        df['pre_close'] = df.close - df.change  # k线的昨收价是收盘价减去涨跌额，但仅限于日频或更低的K线
    # vol的单位为“手”，amount的单位为“元”
    return df


def _get_rt_quote(code: str) -> pd.DataFrame:
    """ codes from tushare, get real time quote data from eastmoney"""

    url = "https://push2.eastmoney.com/api/qt/stock/get"
    symbol = _gen_sina_code(code)
    # print(symbol)
    params = {
        "invt":   "2",
        "fltt":   "1",
        # "cb": "jQuery35108939078769986013_1701853424476",
        "fields": "f58,f734,f107,f57,f43,f59,f169,f301,f60,f170,f152,f177,f111,f46,f44,f45,f47,f260,f48,f261,f279,f277,f278,f288,f19,f17,f531,f15,f13,f11,f20,f18,f16,f14,f12,f39,f37,f35,f33,f31,f40,f38,f36,f34,f32,f211,f212,f213,f214,f215,f210,f209,f208,f207,f206,f161,f49,f171,f50,f86,f84,f85,f168,f108,f116,f167,f164,f162,f163,f92,f71,f117,f292,f51,f52,f191,f192,f262,f294,f295,f748,f747",
        "secid":  f"0.{symbol}",
        "ut":     "fa5fd1943c7b386f172d6893dbfba10b",
        "wbp2u":  "|0|0|0|web",
        "_":      str(int(time.time() * 1000))
    }

    # print(params["secid"])
    response = requests.get(url, headers=dc_cookies, cookies=dc_headers, params=params)
    data_info = response.json()["data"]
    if not data_info:
        return pd.DataFrame()
    name = data_info["f58"]
    open = data_info["f46"]  # / 100
    high = data_info["f44"]  # / 100
    pre_close = data_info["f60"]  # / 100
    low = data_info["f45"]  # / 100
    price = data_info["f43"]  # / 100 if data_info["f43"] != "-" else ""
    b5_v = format_str_to_float(data_info["f12"])
    b5_p = data_info["f11"]  # / 100 if data_info["f11"] != "-" else ""
    b4_v = format_str_to_float(data_info["f14"])
    b4_p = data_info["f13"]  # / 100 if data_info["f13"] != "-" else ""
    b3_v = format_str_to_float(data_info["f16"])
    b3_p = data_info["f15"]  # / 100 if data_info["f15"] != "-" else ""
    b2_v = format_str_to_float(data_info["f18"])
    b2_p = data_info["f17"]  # / 100 if data_info["f17"] != "-" else ""
    b1_v = format_str_to_float(data_info["f20"])
    b1_p = data_info["f19"]  # / 100 if data_info["f19"] != "-" else ""
    a5_v = format_str_to_float(data_info["f32"])
    a5_p = data_info["f31"]  # / 100 if data_info["f31"] != "-" else ""
    a4_v = format_str_to_float(data_info["f34"])
    a4_p = data_info["f33"]  # / 100 if data_info["f33"] != "-" else ""
    a3_v = format_str_to_float(data_info["f36"])
    a3_p = data_info["f35"]  # / 100 if data_info["f35"] != "-" else ""
    a2_v = format_str_to_float(data_info["f38"])
    a2_p = data_info["f37"]  # / 100 if data_info["f38"] != "-" else ""
    a1_v = format_str_to_float(data_info["f40"])
    a1_p = data_info["f39"]  # / 100 if data_info["f39"] != "-" else ""
    date_time = _timestamp_to_time(data_info["f86"])
    date = date_time[0:10]
    times = date_time[10:]
    volume = format_str_to_float(data_info["f47"])
    amount = format_str_to_float(data_info["f48"])
    bid = format_str_to_float(data_info["f19"])
    ask = format_str_to_float(data_info["f39"])
    code = symbol
    data_list = [[name, open, pre_close, price, high, low, bid, ask, volume, amount,
                  b1_v, b1_p, b2_v, b2_p, b3_v, b3_p, b4_v, b4_p, b5_v, b5_p,
                  a1_v, a1_p, a2_v, a2_p, a3_v, a3_p, a4_v, a4_p, a5_v, a5_p, date, times, code]]
    df = pd.DataFrame(data_list, columns=LIVE_QUOTE_COLS)
    df["DATE"] = df["DATE"].apply(_format_em_date_str())
    df["ASK"] = df["ASK"].apply(_format_em_str)
    df["OPEN"] = df["OPEN"].apply(_format_em_str)
    df["HIGH"] = df["HIGH"].apply(_format_em_str)
    df["LOW"] = df["LOW"].apply(_format_em_str)
    df["PRE_CLOSE"] = df["PRE_CLOSE"].apply(_format_em_str)
    df["BID"] = df["BID"].apply(_format_em_str)
    df["A1_P"] = df["A1_P"].apply(_format_em_str)
    df["A2_P"] = df["A2_P"].apply(_format_em_str)
    df["A3_P"] = df["A3_P"].apply(_format_em_str)
    df["A4_P"] = df["A4_P"].apply(_format_em_str)
    df["A5_P"] = df["A5_P"].apply(_format_em_str)
    df["PRICE"] = df["PRICE"].apply(_format_em_str)
    df["B1_P"] = df["B1_P"].apply(_format_em_str)
    df["B2_P"] = df["B2_P"].apply(_format_em_str)
    df["B3_P"] = df["B3_P"].apply(_format_em_str)
    df["B4_P"] = df["B4_P"].apply(_format_em_str)
    df["B5_P"] = df["B5_P"].apply(_format_em_str)
    new_order = LIVE_QUOTE_COLS_REINDEX
    df = df[new_order]
    return df


def _stock_bars(qt_code, start, end=None, freq=None) -> pd.DataFrame:
    """ 获取单支股票的日K线数据
    Parameters
    ----------
    qt_code: str
        股票代码，可以是qt_code或者纯symbol
    start: str
        开始日期
    end: str
        结束日期
    freq:
        K线频率，可以是1min～W之间的各个频率, 如果输入不合法，默认’d'

    Returns
    -------
    DataFrame
        包含单支股票的K线数据，频率可选
    """
    klt = sina_finance_freq_map.get(freq, 101)
    df = _get_k_history(code=qt_code, beg=start, end=end, klt=klt, verbose=True)
    df['ts_code'] = qt_code
    # 重新计算pct_chg，因为原始数据的精度不够四位小数
    if not df.empty:
        df['pct_chg'] = np.round((df['close'] - df['pre_close']) / df['pre_close'] * 100, 4)
    df = df.reindex(columns=['ts_code', 'name', 'trade_time', 'open', 'high', 'low', 'close',
                             'pre_close', 'change', 'pct_chg', 'vol', 'amount'])
    if klt >= 101:
        df.columns = ['ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
                      'pre_close', 'change', 'pct_chg', 'vol', 'amount']
    return df


# 以下是不同频率K线对外接口，接口数据符合datasource的数据格式，可用于股票E、指数IDX、基金FD的K线获取
def stock_daily(qt_code, start, end):
    """ 获取单支股票的日K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='d')
    res['amount'] = np.round(res['amount'] / 1000, 3)  # 东方财富的amount单位是元，转换为千元，保留3位小数
    res = res.reindex(columns=['ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
                               'pre_close', 'change', 'pct_chg', 'vol', 'amount'])

    return res


def stock_1min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的1分钟K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='1min')
    res = res.reindex(columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close',
                               'vol', 'amount'])
    res['vol'] = res['vol'] * 100  # 东方财富的vol单位是手，转换为股
    return res


def stock_5min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的5分钟K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='5min')
    res = res.reindex(columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close',
                               'vol', 'amount'])
    res['vol'] = res['vol'] * 100  # 东方财富的vol单位是手，转换为股
    return res


def stock_15min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的15分钟K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='15min')
    res = res.reindex(columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close',
                               'vol', 'amount'])
    res['vol'] = res['vol'] * 100  # 东方财富的vol单位是手，转换为股
    return res


def stock_30min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的30分钟K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='30min')
    res = res.reindex(columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close',
                               'vol', 'amount'])
    res['vol'] = res['vol'] * 100  # 东方财富的vol单位是手，转换为股
    return res


def stock_hourly(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的小时K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='h')
    res = res.reindex(columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close',
                               'vol', 'amount'])
    res['vol'] = res['vol'] * 100  # 东方财富的vol单位是手，转换为股
    return res


def stock_weekly(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的周K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='w')
    res['amount'] = np.round(res['amount'] / 1000, 3)  # 东方财富的amount单位是元，转换为千元，保留3位小数
    res = res.reindex(columns=['ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
                               'pre_close', 'change', 'pct_chg', 'vol', 'amount'])

    return res


def stock_monthly(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的周K线数据
    """
    res = _stock_bars(qt_code=qt_code, start=start, end=end, freq='m')
    res['amount'] = np.round(res['amount'] / 1000, 3)  # 东方财富的amount单位是元，转换为千元，保留3位小数
    res = res.reindex(columns=['ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
                               'pre_close', 'change', 'pct_chg', 'vol', 'amount'])

    return res


# TODO: 这个函数是用于以前的trader/broker的接口，为了确保兼容性，仍然保留，但未来应该调整为使用新的接口
#  这个函数最大的问题是，它返回的最后一根K线数据往往是不完整的，例如在交易时间内，返回的当天最后一根日K线数据
#  只能体现截止到当前时间的价格和交易量。例如
#  2025年2月17日交易日，假如在早上十一点获取当天的日K线，将得到当天的正确开盘价，但是最高价、最低价和收盘价都
#  仅仅是当天截止11点的最新价格，而不是当天的最终价格。而且交易量和交易额数据也不完整。
#  如果将此数据存入数据库，将会导致数据不准确，因此在使用此函数时，需要注意这个问题。
def real_time_klines(qt_code: str, date: str = 'today', freq: str = 'd') -> pd.DataFrame:
    """ 获取股票date日最新K线数据，数据实时更新,不管K线频率如何，总是返回当天最后一根可用K线数据

    Parameters
    ----------
    qt_code : str
        一支股票的代码
    date: Datetime like, optional, default: 'today'
        需要获取的实时K线的日期，获取当天开盘到收盘/当前时间的所有K线
    freq : str
        数据频率，支持分钟到日频数据，频率最低为日频，周频/月频不支持
        当数据频率为分钟数据时，返回当天的最后一根分钟K线数据

    Returns
    -------
    DataFrame
        包含股票日线数据, 包含以下字段
        datetime: str, 日期
        symbol: str, 股票代码
        name: str, 股票名称
        pre_close: float, 昨日收盘价
        open: float, 开盘价
        close: float, 收盘价
        high: float, 最高价
        low: float, 最低价
        vol: float, 成交量
        amount: float, 成交额
    """

    date = pd.to_datetime(date).strftime('%Y%m%d')
    second_day = pd.Timestamp(date) + pd.Timedelta(days=1)
    second_day = second_day.strftime('%Y%m%d')
    # 为了确保当freq=d时也能返回昨天的数据，需要从上一个交易日开始获取数据
    prev_day = prev_market_trade_day(date).strftime('%Y%m%d')

    df = _stock_bars(qt_code, start=prev_day, end=second_day, freq=freq)

    df['symbol'] = qt_code
    if freq in ['1min', '5min', '15min', '30min', '60min', 'h']:
        df.index = pd.to_datetime(df['trade_time'])
        df['vol'] = df['vol'] * 100  # 东方财富的vol单位是手，转换为股
    else:
        df.index = pd.to_datetime(df['trade_date'])
        df['amount'] = np.round(df['amount'] / 1000, 3)  # 东方财富的amount单位是元，转换为千元，保留3位小数

    df = df.reindex(columns=['symbol', 'name', 'pre_close', 'open', 'close', 'high', 'low', 'vol', 'amount'])

    data = df.loc[pd.to_datetime(prev_day):pd.to_datetime(second_day), :]

    return data


def real_time_quote(qt_code) -> pd.DataFrame:
    """ 获取股票实时盘口交易详情，包括日期时间、现价、竞买竞卖价格、成交价格、成交量、以及委买委卖1～5档数据
    """
    return _get_rt_quote(code=qt_code)