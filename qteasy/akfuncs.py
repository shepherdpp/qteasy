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


def _code_to_ts_code(code: str) -> str:
    """将 6 位证券代码推断为 qteasy ts_code。"""
    code = str(code).strip().zfill(6)
    if code.startswith(('4', '8')):
        return f'{code}.BJ'
    if code.startswith('6'):
        return f'{code}.SH'
    if code.startswith(('0', '3')):
        return f'{code}.SZ'
    return f'{code}.SZ'


def _to_sina_symbol(qt_code: str) -> str:
    """将 qteasy 代码转换为新浪 daily 接口 symbol（如 sh600000）。"""
    sym = _extract_symbol(qt_code)
    if not sym:
        return ''
    if isinstance(qt_code, str) and qt_code.upper().endswith('.SH'):
        return f'sh{sym}'
    if isinstance(qt_code, str) and qt_code.upper().endswith('.BJ'):
        return f'bj{sym}'
    return f'sz{sym}'


def _market_tag_from_qt_code(qt_code: str) -> str:
    """东财个股资金流 market 参数：sh / sz。"""
    if isinstance(qt_code, str) and qt_code.upper().endswith('.SH'):
        return 'sh'
    if isinstance(qt_code, str) and qt_code.upper().endswith('.BJ'):
        return 'bj'
    return 'sz'


def _filter_frame_by_date(
        df: pd.DataFrame,
        date_col: str,
        start: str,
        end: str,
) -> pd.DataFrame:
    """按 YYYYMMDD 区间过滤含日期列的 DataFrame。"""
    if df is None or df.empty:
        return df
    out = df.copy()
    out['_dt'] = pd.to_datetime(out[date_col], errors='coerce')
    start_dt = pd.to_datetime(_normalize_date_text(start), errors='coerce')
    end_dt = pd.to_datetime(_normalize_date_text(end), errors='coerce')
    if pd.notna(start_dt):
        out = out[out['_dt'] >= start_dt]
    if pd.notna(end_dt):
        out = out[out['_dt'] <= end_dt]
    return out.drop(columns=['_dt'], errors='ignore')


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


def _normalize_adj_frame(raw_df: pd.DataFrame, qt_code: str) -> pd.DataFrame:
    """将 akshare 复权因子数据规整为 adj_factors schema。"""
    empty = pd.DataFrame(columns=['ts_code', 'trade_date', 'adj_factor'])
    if raw_df is None or raw_df.empty:
        return empty
    df = raw_df.copy()
    trade_date = _pick_col(df, ['date', '日期', 'trade_date'])
    factor = _normalize_numeric_series(_pick_col(df, ['qfq_factor', '前复权因子', 'adj_factor', 'factor']))
    out = pd.DataFrame({
        'ts_code': qt_code,
        'trade_date': pd.to_datetime(trade_date, errors='coerce').dt.strftime('%Y%m%d'),
        'adj_factor': factor,
    })
    out = out.dropna(subset=['trade_date', 'adj_factor']).reset_index(drop=True)
    return out.reindex(columns=['ts_code', 'trade_date', 'adj_factor'])


def _normalize_trade_calendar(raw_dates: pd.Series, exchange: str) -> pd.DataFrame:
    """将交易日列表展开为 trade_calendar schema。"""
    if raw_dates is None or len(raw_dates) == 0:
        return pd.DataFrame(columns=['cal_date', 'exchange', 'is_open', 'pretrade_date'])
    dates = pd.to_datetime(raw_dates, errors='coerce').dropna().sort_values().unique()
    records = []
    for idx, dt in enumerate(dates):
        cal = pd.Timestamp(dt).strftime('%Y%m%d')
        pre = pd.Timestamp(dates[idx - 1]).strftime('%Y%m%d') if idx > 0 else None
        records.append({
            'cal_date': cal,
            'exchange': exchange,
            'is_open': 1,
            'pretrade_date': pre,
        })
    return pd.DataFrame(records)


def _normalize_stock_basic(raw_df: pd.DataFrame, exchange: str = '') -> pd.DataFrame:
    """将 akshare 股票列表规整为 stock_basic schema（缺列填空）。"""
    cols = [
        'ts_code', 'symbol', 'name', 'area', 'industry', 'fullname',
        'enname', 'cnspell', 'market', 'exchange', 'curr_type', 'list_status',
        'list_date', 'delist_date', 'is_hs',
    ]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=cols)
    df = raw_df.copy()
    code = _pick_col(df, ['code', '代码', '证券代码', 'symbol']).astype(str).str.zfill(6)
    name = _pick_col(df, ['name', '名称', '股票名称']).fillna('').astype(str)
    ts_codes = code.map(_code_to_ts_code)
    out = pd.DataFrame({
        'ts_code': ts_codes,
        'symbol': code,
        'name': name,
        'area': '',
        'industry': '',
        'fullname': name,
        'enname': '',
        'cnspell': '',
        'market': '',
        'exchange': ts_codes.str.split('.').str[-1].map({'SH': 'SSE', 'SZ': 'SZSE', 'BJ': 'BSE'}),
        'curr_type': 'CNY',
        'list_status': 'L',
        'list_date': None,
        'delist_date': None,
        'is_hs': '',
    })
    if exchange:
        ex = exchange.upper()
        if ex in ('SSE', 'SH'):
            out = out[out['ts_code'].str.endswith('.SH')]
        elif ex in ('SZSE', 'SZ'):
            out = out[out['ts_code'].str.endswith('.SZ')]
        elif ex in ('BSE', 'BJ'):
            out = out[out['ts_code'].str.endswith('.BJ')]
    return out.reindex(columns=cols)


def _normalize_index_basic(raw_df: pd.DataFrame) -> pd.DataFrame:
    """将 akshare 指数列表规整为 index_basic schema。"""
    cols = [
        'ts_code', 'name', 'fullname', 'market', 'publisher', 'category',
        'base_date', 'base_point', 'list_date', 'weight_rule', 'desc', 'exp_date',
    ]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=cols)
    df = raw_df.copy()
    code = _pick_col(df, ['index_code', '代码', 'code', 'symbol']).astype(str).str.zfill(6)
    name = _pick_col(df, ['display_name', '名称', 'name', '指数名称']).fillna('').astype(str)
    ts_codes = code.map(_code_to_ts_code)
    return pd.DataFrame({
        'ts_code': ts_codes,
        'name': name,
        'fullname': name,
        'market': '',
        'publisher': '',
        'category': '',
        'base_date': None,
        'base_point': None,
        'list_date': None,
        'weight_rule': '',
        'desc': '',
        'exp_date': None,
    }).reindex(columns=cols)


def _normalize_fund_basic(raw_df: pd.DataFrame) -> pd.DataFrame:
    """将 akshare ETF 现货列表规整为 fund_basic schema。"""
    cols = [
        'ts_code', 'name', 'management', 'custodian', 'fund_type', 'found_date',
        'due_date', 'list_date', 'issue_date', 'delist_date', 'issue_amount',
        'm_fee', 'c_fee', 'duration_year', 'p_value', 'min_amount', 'exp_return',
        'benchmark', 'status', 'invest_type', 'type', 'trustee', 'purc_startdate',
        'redm_startdate', 'market',
    ]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=cols)
    df = raw_df.copy()
    code = _pick_col(df, ['代码', '基金代码', 'code']).astype(str).str.zfill(6)
    name = _pick_col(df, ['名称', '基金简称', 'name']).fillna('').astype(str)
    ts_codes = code.map(lambda c: f'{c}.SH' if c.startswith('5') else f'{c}.SZ')
    return pd.DataFrame({
        'ts_code': ts_codes,
        'name': name,
        'management': '',
        'custodian': '',
        'fund_type': '',
        'found_date': None,
        'due_date': None,
        'list_date': None,
        'issue_date': None,
        'delist_date': None,
        'issue_amount': None,
        'm_fee': None,
        'c_fee': None,
        'duration_year': None,
        'p_value': None,
        'min_amount': None,
        'exp_return': None,
        'benchmark': '',
        'status': 'L',
        'invest_type': '',
        'type': '',
        'trustee': '',
        'purc_startdate': None,
        'redm_startdate': None,
        'market': 'E',
    }).reindex(columns=cols)


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


def _fetch_fund_hist(qt_code: str, start: str, end: str, period: str) -> pd.DataFrame:
    """拉取场内基金日周月线并标准化。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.fund_etf_hist_em(
        symbol=symbol,
        period=period,
        start_date=_normalize_date_text(start),
        end_date=_normalize_date_text(end),
        adjust='qfq',
    )
    return _normalize_daily_frame(raw, qt_code)


def _fetch_stock_min(qt_code: str, start: str, end: str, period: str) -> pd.DataFrame:
    """拉取股票分钟线并标准化。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.stock_zh_a_hist_min_em(
        symbol=symbol,
        period=period,
        start_date=_to_ak_min_datetime(start, True),
        end_date=_to_ak_min_datetime(end, False),
        adjust='',
    )
    return _normalize_min_frame(raw, qt_code)


def _fetch_fund_min(qt_code: str, start: str, end: str, period: str) -> pd.DataFrame:
    """拉取场内基金分钟线并标准化。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.fund_etf_hist_em(
        symbol=symbol,
        period=period,
        start_date=_to_ak_min_datetime(start, True),
        end_date=_to_ak_min_datetime(end, False),
        adjust='',
    )
    return _normalize_min_frame(raw, qt_code)


def trade_cal(exchange: str = 'SSE', start: str = None, end: str = None, is_open: int = None):
    """获取交易日历（基于新浪交易日列表，按交易所复制行）。"""
    raw = ak.tool_trade_date_hist_sina()
    date_col = _pick_col(raw, ['trade_date', '日期'])
    out = _normalize_trade_calendar(date_col, exchange=exchange or 'SSE')
    if start:
        out = out[out['cal_date'] >= _normalize_date_text(start)]
    if end:
        out = out[out['cal_date'] <= _normalize_date_text(end)]
    if is_open is not None and int(is_open) == 0:
        return pd.DataFrame(columns=out.columns)
    return out.reset_index(drop=True)


def stock_basic(exchange: str = None):
    """获取 A 股股票基本信息。"""
    raw = ak.stock_info_a_code_name()
    return _normalize_stock_basic(raw, exchange=exchange or '')


def index_basic(exchange: str = 'ALL'):
    """获取指数基本信息。"""
    raw = ak.index_stock_info()
    out = _normalize_index_basic(raw)
    if exchange and str(exchange).upper() not in ('ALL', 'NONE', ''):
        suffix = {'SSE': '.SH', 'SZSE': '.SZ'}.get(str(exchange).upper(), '')
        if suffix:
            out = out[out['ts_code'].str.endswith(suffix)]
    return out.reset_index(drop=True)


def fund_basic(market: str = 'ALL'):
    """获取场内 ETF 基金基本信息。"""
    raw = ak.fund_etf_spot_em()
    out = _normalize_fund_basic(raw)
    if market and str(market).upper() not in ('ALL', 'E,O', 'NONE', ''):
        if str(market).upper() == 'E':
            out = out[out['market'] == 'E']
    return out.reset_index(drop=True)


def stock_adj_factor(qt_code, start, end):
    """获取股票前复权因子。"""
    sina_sym = _to_sina_symbol(qt_code)
    if not sina_sym:
        return pd.DataFrame(columns=['ts_code', 'trade_date', 'adj_factor'])
    raw = ak.stock_zh_a_daily(
        symbol=sina_sym,
        start_date=_normalize_date_text(start),
        end_date=_normalize_date_text(end),
        adjust='qfq-factor',
    )
    return _normalize_adj_frame(raw, qt_code)


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
    return _fetch_stock_min(qt_code=qt_code, start=start, end=end, period='1')


def stock_5min(qt_code, start, end):
    """获取股票 5 分钟线数据。"""
    return _fetch_stock_min(qt_code=qt_code, start=start, end=end, period='5')


def stock_15min(qt_code, start, end):
    """获取股票 15 分钟线数据。"""
    return _fetch_stock_min(qt_code=qt_code, start=start, end=end, period='15')


def stock_30min(qt_code, start, end):
    """获取股票 30 分钟线数据。"""
    return _fetch_stock_min(qt_code=qt_code, start=start, end=end, period='30')


def stock_hourly(qt_code, start, end):
    """获取股票 60 分钟线数据。"""
    return _fetch_stock_min(qt_code=qt_code, start=start, end=end, period='60')


def index_daily(qt_code, start, end):
    """获取指数日线数据"""
    return _fetch_index_hist(qt_code=qt_code, start=start, end=end, period='daily')


def index_weekly(qt_code, start, end):
    """获取指数周线数据"""
    return _fetch_index_hist(qt_code=qt_code, start=start, end=end, period='weekly')


def index_monthly(qt_code, start, end):
    """获取指数月线数据"""
    return _fetch_index_hist(qt_code=qt_code, start=start, end=end, period='monthly')


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


def fund_weekly(qt_code, start, end):
    """获取场内基金周线数据。"""
    return _fetch_fund_hist(qt_code=qt_code, start=start, end=end, period='weekly')


def fund_monthly(qt_code, start, end):
    """获取场内基金月线数据。"""
    return _fetch_fund_hist(qt_code=qt_code, start=start, end=end, period='monthly')


def fund_1min(qt_code, start, end):
    """获取场内基金 1 分钟线数据。"""
    return _fetch_fund_min(qt_code=qt_code, start=start, end=end, period='1')


def stock_suspend(trade_date=None, start=None, end=None, suspend_type=None):
    """获取停复牌信息（按交易日拉取）。"""
    date_text = _normalize_date_text(trade_date or start)
    if not date_text:
        return pd.DataFrame(columns=['ts_code', 'trade_date', 'suspend_timing', 'suspend_type'])
    raw = ak.stock_tfp_em(date=date_text)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=['ts_code', 'trade_date', 'suspend_timing', 'suspend_type'])
    df = raw.copy()
    code = _pick_col(df, ['代码', 'code', 'symbol']).astype(str).str.zfill(6)
    suspend_type_col = _pick_col(df, ['停牌类型', 'suspend_type', '类型']).fillna('S')
    timing = _pick_col(df, ['停牌时间', 'suspend_timing', '时间段']).fillna('')
    return pd.DataFrame({
        'ts_code': code.map(_code_to_ts_code),
        'trade_date': date_text,
        'suspend_timing': timing.astype(str),
        'suspend_type': suspend_type_col.astype(str).str[:2],
    })


def money_flow(qt_code, start, end):
    """获取个股资金流向。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.stock_individual_fund_flow(stock=symbol, market=_market_tag_from_qt_code(qt_code))
    if raw is None or raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    trade_date = pd.to_datetime(_pick_col(df, ['日期', 'trade_date']), errors='coerce')
    df['trade_date'] = trade_date.dt.strftime('%Y%m%d')
    df['ts_code'] = qt_code
    col_map = {
        'buy_sm_vol': ['小单买入量', 'buy_sm_vol'],
        'buy_sm_amount': ['小单买入额', 'buy_sm_amount'],
        'sell_sm_vol': ['小单卖出量', 'sell_sm_vol'],
        'sell_sm_amount': ['小单卖出额', 'sell_sm_amount'],
        'buy_md_vol': ['中单买入量', 'buy_md_vol'],
        'buy_md_amount': ['中单买入额', 'buy_md_amount'],
        'sell_md_vol': ['中单卖出量', 'sell_md_vol'],
        'sell_md_amount': ['中单卖出额', 'sell_md_amount'],
        'buy_lg_vol': ['大单买入量', 'buy_lg_vol'],
        'buy_lg_amount': ['大单买入额', 'buy_lg_amount'],
        'sell_lg_vol': ['大单卖出量', 'sell_lg_vol'],
        'sell_lg_amount': ['大单卖出额', 'sell_lg_amount'],
        'buy_elg_vol': ['特大单买入量', 'buy_elg_vol'],
        'buy_elg_amount': ['特大单买入额', 'buy_elg_amount'],
        'sell_elg_vol': ['特大单卖出量', 'sell_elg_vol'],
        'sell_elg_amount': ['特大单卖出额', 'sell_elg_amount'],
        'net_mf_vol': ['净流入量', 'net_mf_vol'],
        'net_mf_amount': ['净流入额', 'net_mf_amount'],
    }
    out = {'ts_code': df['ts_code'], 'trade_date': df['trade_date']}
    for target, candidates in col_map.items():
        out[target] = _normalize_numeric_series(_pick_col(df, candidates))
    result = pd.DataFrame(out)
    result = _filter_frame_by_date(result, 'trade_date', start, end)
    return result.reindex(columns=[
        'ts_code', 'trade_date', 'buy_sm_vol', 'buy_sm_amount', 'sell_sm_vol', 'sell_sm_amount',
        'buy_md_vol', 'buy_md_amount', 'sell_md_vol', 'sell_md_amount', 'buy_lg_vol', 'buy_lg_amount',
        'sell_lg_vol', 'sell_lg_amount', 'buy_elg_vol', 'buy_elg_amount', 'sell_elg_vol',
        'sell_elg_amount', 'net_mf_vol', 'net_mf_amount',
    ])


def dividend(qt_code, start=None, end=None):
    """获取个股分红历史。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    raw = ak.stock_history_dividend_detail(symbol=symbol, indicator='分红')
    if raw is None or raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    return pd.DataFrame({
        'ts_code': qt_code,
        'end_date': pd.to_datetime(_pick_col(df, ['分红年度', 'end_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'div_proc': _pick_col(df, ['实施进度', 'div_proc']).fillna('').astype(str),
        'ann_date': pd.to_datetime(_pick_col(df, ['公告日期', 'ann_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'stk_div': _normalize_numeric_series(_pick_col(df, ['每股送转', 'stk_div'])),
        'stk_bo_rate': _normalize_numeric_series(_pick_col(df, ['每股送股', 'stk_bo_rate'])),
        'stk_co_rate': _normalize_numeric_series(_pick_col(df, ['每股转增', 'stk_co_rate'])),
        'cash_div': _normalize_numeric_series(_pick_col(df, ['每股分红', 'cash_div'])),
        'cash_div_tax': _normalize_numeric_series(_pick_col(df, ['每股分红税后', 'cash_div_tax'])),
        'record_date': pd.to_datetime(_pick_col(df, ['股权登记日', 'record_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'ex_date': pd.to_datetime(_pick_col(df, ['除权除息日', 'ex_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'pay_date': pd.to_datetime(_pick_col(df, ['派息日', 'pay_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'div_listdate': '',
        'imp_ann_date': '',
        'base_date': '',
        'base_share': None,
    })


def new_share(qt_code, start=None, end=None):
    """获取 IPO 信息（按股票代码）。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    try:
        raw = ak.stock_ipo_info(stock=symbol)
    except Exception:
        return pd.DataFrame()
    if raw is None or raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    return pd.DataFrame({
        'ts_code': qt_code,
        'sub_code': _pick_col(df, ['申购代码', 'sub_code']).astype(str),
        'name': _pick_col(df, ['名称', 'name']).astype(str),
        'ipo_date': pd.to_datetime(_pick_col(df, ['申购日期', 'ipo_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'issue_date': pd.to_datetime(_pick_col(df, ['上市日期', 'issue_date']), errors='coerce').dt.strftime('%Y%m%d'),
        'amount': _normalize_numeric_series(_pick_col(df, ['发行总数', 'amount'])),
        'market_amount': _normalize_numeric_series(_pick_col(df, ['网上发行', 'market_amount'])),
        'price': _normalize_numeric_series(_pick_col(df, ['发行价格', 'price'])),
        'pe': _normalize_numeric_series(_pick_col(df, ['市盈率', 'pe'])),
        'limit_amount': _normalize_numeric_series(_pick_col(df, ['申购上限', 'limit_amount'])),
        'funds': _normalize_numeric_series(_pick_col(df, ['募集资金', 'funds'])),
        'ballot': _normalize_numeric_series(_pick_col(df, ['中签率', 'ballot'])),
    })


def stock_company(qt_code, start=None, end=None):
    """获取上市公司基本信息。"""
    symbol = _extract_symbol(qt_code)
    if not symbol:
        return pd.DataFrame()
    try:
        raw = ak.stock_profile_cninfo(symbol=symbol)
    except Exception:
        return pd.DataFrame()
    if raw is None or raw.empty:
        return pd.DataFrame()
    item = _pick_col(raw, ['item', '项目', '字段'])
    value = _pick_col(raw, ['value', '内容', '值'])
    info = dict(zip(item.astype(str), value.astype(str)))
    exchange = 'SSE' if qt_code.endswith('.SH') else ('SZSE' if qt_code.endswith('.SZ') else 'BSE')
    return pd.DataFrame([{
        'ts_code': qt_code,
        'exchange': exchange,
        'chairman': info.get('法人代表', info.get('董事长', '')),
        'manager': info.get('总经理', ''),
        'secretary': info.get('董秘', ''),
        'reg_capital': _normalize_numeric_series(pd.Series([info.get('注册资本', None)])).iloc[0],
        'setup_date': info.get('成立日期', ''),
        'province': info.get('省份', ''),
        'city': info.get('城市', ''),
        'introduction': info.get('公司简介', info.get('公司介绍', '')),
        'website': info.get('公司网址', ''),
        'email': info.get('电子邮箱', ''),
        'office': info.get('办公地址', ''),
        'employees': None,
        'main_business': info.get('主营业务', ''),
        'business_scope': info.get('经营范围', ''),
    }])


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
