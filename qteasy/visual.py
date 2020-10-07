# coding=utf-8
# visual.py

# ======================================
# This file contains components for the qt
# to establish visual outputs of price data
# loop result and strategy optimization
# results as well
# ======================================

import mplfinance as mpf
import pandas as pd
import datetime
from .tsfuncs import get_bar, name_change


def candle(stock, start=None, end=None, asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
    mc = mpf.make_marketcolors(up='r', down='g',
                               volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    if not no_visual:
        mpf.plot(daily,
                 title=share_name,
                 volume=True,
                 type='candle',
                 style=s,
                 figsize=figsize,
                 mav=mav,
                 figscale=0.5)


def ohlc(stock, start=None, end=None, asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
    mc = mpf.make_marketcolors(up='r', down='g',
                               volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    if not no_visual:
        mpf.plot(daily,
                 title=share_name,
                 volume=True,
                 type='ohlc',
                 style=s,
                 figsize=figsize,
                 mav=mav,
                 figscale=0.5)


def renko(stock, start=None, end=None, asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
    mc = mpf.make_marketcolors(up='r', down='g',
                               volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    if not no_visual:
        mpf.plot(daily,
                 title=share_name,
                 volume=True,
                 type='renko',
                 style=s,
                 figsize=figsize,
                 mav=mav,
                 figscale=0.5)


def _prepare_mpf_data(stock, start=None, end=None, asset_type='E'):
    today = datetime.datetime.today()
    if end is None:
        end = today.strftime('%Y-%m-%d')
    if start is None:
        try:
            start = (pd.Timestamp(end) - pd.Timedelta(30, 'd')).strftime('%Y-%m-%d')
        except:
            start = today - pd.Timedelta(30, 'd')

    data = get_bar(shares=stock, start=start, end=end, asset_type=asset_type)
    if asset_type == 'E':
        share_basic = name_change(ts_code=stock, fields='ts_code,name,start_date,end_date,change_reason')
        if share_basic.empty:
            raise ValueError(f'stock {stock} can not be found or does not exist!')
        share_name = stock + ' - ' + share_basic.name[0]
        # debug
        # print(share_basic.head())
    else:
        share_name = stock + ' - ' + asset_type
    # data.info()
    daily = data[['open', 'high', 'low', 'close', 'vol']]
    daily.columns = ['open', 'high', 'low', 'close', 'volume']
    daily.index = data['trade_date']
    daily = daily.rename(index=pd.Timestamp).sort_index()
    # print(daily.head())
    # manipulating of mpf:
    return daily, share_name