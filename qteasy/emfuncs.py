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

from qteasy.utilfuncs import str_to_list

east_money_freq_map = {
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

# eastmoney interface function, call this function to extract data
def acquire_data(api_name, **kwargs):
    """ eastmoney接口函数，根据根据table的内容调用相应的eastmoney API下载数据，并以DataFrame的形式返回数据"""
    func = globals()[api_name]
    res = func(**kwargs)
    return res


def _gen_eastmoney_code(rawcode: str) -> str:
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
    >>> _gen_eastmoney_code('000001')
    0.000001
    >>> _gen_eastmoney_code('000001.SZ')
    0.000001
    >>> _gen_eastmoney_code('000001.SH')
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
    secid = _gen_eastmoney_code(code)
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


def _stock_bars(qt_code, start, end, freq) -> pd.DataFrame:
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
    code = _gen_eastmoney_code(qt_code)
    klt = east_money_freq_map.get(freq, 101)
    df = _get_k_history(code, start, end, klt=klt)
    df['symbol'] = qt_code

    return df


def stock_daily(qt_code, start, end):
    """ 获取单支股票的日K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='d')


def stock_1min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的1分钟K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='1min')


def stock_5min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的5分钟K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='5min')


def stock_15min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的15分钟K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='15min')


def stock_30min(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的30分钟K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='30min')


def stock_hourly(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的小时K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='h')


def stock_weekly(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的周K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='w')


def stock_monthly(qt_code, start, end) -> pd.DataFrame:
    """ 获取单支股票的周K线数据
    """
    return _stock_bars(qt_code=qt_code, start=start, end=end, freq='m')


def real_time_klines(qt_code, date, freq='d'):
    """ 获取股票当前最新日线数据，数据实时更新
    Parameters
    ----------
    qt_code : str or list of str
        股票代码
    date: Datetime like
        需要获取的实时K线的日期，获取当天开盘到收盘/当前时间的所有K线
    freq : str
        数据频率，支持分钟到日频数据，频率最低为日频，周频/月频不支持

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
    symbol = _gen_eastmoney_code(qt_code)

    klt = east_money_freq_map.get(freq, 101)
    if klt > 101:
        raise ValueError(f'Can not get real time K line with freq: {freq}')

    df = _get_k_history(symbol, beg=date, klt=klt, verbose=True)
    df['symbol'] = symbol
    data = df.iloc[-1:, :]

    return data


def real_time_quote(symbols, verbose=False, parallel=True, timezone='local') -> pd.DataFrame:
    """ 获取股票实时盘口交易详情，包括日期时间、现价、竞买竞卖价格、成交价格、成交量、以及委买委卖1～5档数据
    """

