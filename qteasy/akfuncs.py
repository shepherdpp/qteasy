# coding=utf-8
# ======================================
# File:     akfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-11
# Desc:
#   Interfaces to akshare data api.
# ======================================


import re
from datetime import datetime

import akshare as ak
import pandas as pd

from qteasy.__init__ import logger_core, QT_CONFIG
from qteasy.utilfuncs import retry

ERRORS_TO_CHECK_ON_RETRY = Exception

EXTRA_RETRY_API = [

]


# tsfuncs interface function, call this function to extract data
def acquire_data(api_name, **kwargs):
    """ DataSource模块的接口函数，根据根据table的内容调用相应的akshare API下载数据，并以DataFrame的形式返回数据"""
    data_download_retry_count = QT_CONFIG.hist_dnld_retry_cnt
    data_download_retry_wait = QT_CONFIG.hist_dnld_retry_wait
    data_download_retry_backoff = QT_CONFIG.hist_dnld_backoff

    if api_name in EXTRA_RETRY_API:
        data_download_retry_count += 3

    retry_decorator = retry(
            exception_to_check=ERRORS_TO_CHECK_ON_RETRY,
            mute=True,
            tries=data_download_retry_count,
            delay=data_download_retry_wait,
            backoff=data_download_retry_backoff,
            logger=logger_core,
    )
    func = globals()[api_name]
    decorated_func = retry_decorator(func)
    res = decorated_func(**kwargs)
    return res


def _extract_symbol(qt_code: str) -> str:
    """将 qteasy 代码转换为 akshare 代码。"""
    if not isinstance(qt_code, str):
        return ''
    return qt_code.split('.')[0].strip()


def _normalize_date_text(date_value: str) -> str:
    """将日期文本统一为 YYYYMMDD。"""
    if date_value is None:
        return ''
    return pd.to_datetime(str(date_value)).strftime('%Y%m%d')


def _normalize_numeric_series(series: pd.Series) -> pd.Series:
    """将字符串数字列安全转换为浮点数。"""
    return pd.to_numeric(
        series.astype(str).str.replace(',', '', regex=False),
        errors='coerce',
    )


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    """按候选列名顺序挑选第一列，未命中返回空列。"""
    for col in candidates:
        if col in df.columns:
            return df[col]
    return pd.Series([None] * len(df), index=df.index)


def _normalize_daily_frame(raw_df: pd.DataFrame, qt_code: str) -> pd.DataFrame:
    """将 akshare 日线数据规整为 qteasy bars schema。"""
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=[
            'ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
            'pre_close', 'change', 'pct_chg', 'vol', 'amount',
        ])
    df = raw_df.copy()
    trade_date = _pick_col(df, ['日期', 'trade_date', 'date', '时间'])
    open_col = _normalize_numeric_series(_pick_col(df, ['开盘', '开盘价', 'open']))
    high_col = _normalize_numeric_series(_pick_col(df, ['最高', '最高价', 'high']))
    low_col = _normalize_numeric_series(_pick_col(df, ['最低', '最低价', 'low']))
    close_col = _normalize_numeric_series(_pick_col(df, ['收盘', '收盘价', 'close']))
    vol_col = _normalize_numeric_series(_pick_col(df, ['成交量', 'vol', 'volume']))
    amount_col = _normalize_numeric_series(_pick_col(df, ['成交额', 'amount']))

    out = pd.DataFrame({
        'ts_code': qt_code,
        'name': _pick_col(df, ['名称', '股票名称', '基金简称', 'name']).fillna(''),
        'trade_date': pd.to_datetime(trade_date, errors='coerce').dt.strftime('%Y%m%d'),
        'open': open_col,
        'high': high_col,
        'low': low_col,
        'close': close_col,
        'vol': vol_col,
        'amount': amount_col,
    })
    out = out.dropna(subset=['trade_date', 'close']).reset_index(drop=True)
    if out.empty:
        return pd.DataFrame(columns=[
            'ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
            'pre_close', 'change', 'pct_chg', 'vol', 'amount',
        ])
    out['pre_close'] = out['close'].shift(1)
    out.loc[out.index[0], 'pre_close'] = out.loc[out.index[0], 'open']
    out['change'] = out['close'] - out['pre_close']
    out['pct_chg'] = (out['change'] / out['pre_close'].replace(0, pd.NA)) * 100
    out['pct_chg'] = out['pct_chg'].fillna(0.0)
    return out.reindex(columns=[
        'ts_code', 'name', 'trade_date', 'open', 'high', 'low', 'close',
        'pre_close', 'change', 'pct_chg', 'vol', 'amount',
    ])


def _normalize_min_frame(raw_df: pd.DataFrame, qt_code: str) -> pd.DataFrame:
    """将 akshare 分钟线数据规整为 qteasy min_bars schema。"""
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=[
            'ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount',
        ])
    df = raw_df.copy()
    trade_time = _pick_col(df, ['时间', 'trade_time', '日期', 'date'])
    out = pd.DataFrame({
        'ts_code': qt_code,
        'trade_time': pd.to_datetime(trade_time, errors='coerce').dt.strftime('%Y%m%d %H:%M:%S'),
        'open': _normalize_numeric_series(_pick_col(df, ['开盘', 'open'])),
        'high': _normalize_numeric_series(_pick_col(df, ['最高', 'high'])),
        'low': _normalize_numeric_series(_pick_col(df, ['最低', 'low'])),
        'close': _normalize_numeric_series(_pick_col(df, ['收盘', 'close'])),
        'vol': _normalize_numeric_series(_pick_col(df, ['成交量', 'vol', 'volume'])),
        'amount': _normalize_numeric_series(_pick_col(df, ['成交额', 'amount'])),
    })
    out = out.dropna(subset=['trade_time', 'close']).reset_index(drop=True)
    return out.reindex(columns=[
        'ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount',
    ])


def _to_ak_min_datetime(date_ymd: str, is_start: bool) -> str:
    """将 YYYYMMDD 转成 akshare 分钟接口需要的时间戳文本。"""
    ymd = _normalize_date_text(date_ymd)
    suffix = '09:00:00' if is_start else '23:59:59'
    return f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]} {suffix}'


def _fetch_stock_hist(qt_code: str, start: str, end: str, period: str) -> pd.DataFrame:
    """拉取股票日周月线并标准化。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=_normalize_date_text(start),
        end_date=_normalize_date_text(end),
        adjust='qfq',
    )
    return _normalize_daily_frame(raw, qt_code)


def _fetch_index_hist(qt_code: str, start: str, end: str, period: str) -> pd.DataFrame:
    """拉取指数日周月线并标准化。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.index_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=_normalize_date_text(start),
        end_date=_normalize_date_text(end),
    )
    return _normalize_daily_frame(raw, qt_code)


def stock_daily(qt_code, start, end):
    """获取股票日线数据"""
    return _fetch_stock_hist(qt_code=qt_code, start=start, end=end, period='daily')


def stock_weekly(qt_code, start, end):
    """获取股票周线数据"""
    return _fetch_stock_hist(qt_code=qt_code, start=start, end=end, period='weekly')


def stock_monthly(qt_code, start, end):
    """获取股票月线数据"""
    return _fetch_stock_hist(qt_code=qt_code, start=start, end=end, period='monthly')


def stock_1min(qt_code, start, end):
    """获取股票 1 分钟线数据。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.stock_zh_a_hist_min_em(
        symbol=symbol,
        period='1',
        start_date=_to_ak_min_datetime(start, True),
        end_date=_to_ak_min_datetime(end, False),
        adjust='',
    )
    return _normalize_min_frame(raw, qt_code)


def index_daily(qt_code, start, end):
    """获取指数日线数据"""
    return _fetch_index_hist(qt_code=qt_code, start=start, end=end, period='daily')


def index_weekly(qt_code, start, end):
    """获取指数周线数据"""
    return _fetch_index_hist(qt_code=qt_code, start=start, end=end, period='weekly')


def fund_daily(qt_code, start, end):
    """获取场内基金日线数据。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.fund_etf_hist_em(
        symbol=symbol,
        period='daily',
        start_date=_normalize_date_text(start),
        end_date=_normalize_date_text(end),
        adjust='qfq',
    )
    return _normalize_daily_frame(raw, qt_code)


def realtime_bars(qt_code, date='today', freq='d'):
    """获取实时K线数据"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    if date in (None, '', 'today'):
        date = datetime.now().strftime('%Y%m%d')
    freq_map = {
        '1min': '1',
        '5min': '5',
        '15min': '15',
        '30min': '30',
        'h': '60',
    }
    period = freq_map.get(str(freq).lower(), '1')
    raw = ak.stock_zh_a_hist_min_em(
        symbol=symbol,
        period=period,
        start_date=_to_ak_min_datetime(date, True),
        end_date=_to_ak_min_datetime(date, False),
        adjust='',
    )
    return _normalize_min_frame(raw, qt_code)


def realtime_quotes(qt_code):
    """获取实时行情数据"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.stock_zh_a_spot_em()
    if raw is None or raw.empty:
        return pd.DataFrame()
    code_col = _pick_col(raw, ['代码', '代码', 'symbol', '证券代码'])
    match = code_col.astype(str).str.zfill(6).str.contains(rf'^{re.escape(symbol)}$')
    data = raw[match].copy()
    if data.empty:
        return pd.DataFrame()
    return pd.DataFrame({
        'ts_code': [qt_code] * len(data),
        'name': _pick_col(data, ['名称', '股票名称', 'name']).fillna('').values,
        'price': _normalize_numeric_series(_pick_col(data, ['最新价', 'price'])).values,
        'open': _normalize_numeric_series(_pick_col(data, ['今开', '开盘', 'open'])).values,
        'high': _normalize_numeric_series(_pick_col(data, ['最高', 'high'])).values,
        'low': _normalize_numeric_series(_pick_col(data, ['最低', 'low'])).values,
        'vol': _normalize_numeric_series(_pick_col(data, ['成交量', 'vol', 'volume'])).values,
        'amount': _normalize_numeric_series(_pick_col(data, ['成交额', 'amount'])).values,
    })
