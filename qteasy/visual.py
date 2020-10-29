# coding=utf-8
# visual.py

# ======================================
# This file contains components for the qt
# to establish visual outputs of price data
# loop result and strategy optimization
# results as well
# ======================================

import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np

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
        share_basic = name_change(shares=stock, fields='ts_code,name,start_date,end_date,change_reason')
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


def plot_loop_result(result, **kwargs):
    """plot the loop results in a fancy way that displays all infomration more clearly"""
    # prepare result dataframe
    if not isinstance(result, pd.DataFrame):
        raise TypeError('')
    if result.empty:
        raise ValueError()

    result['change'] = result['000300.SH'] - result['000300.SH'].shift(1)
    start_point = result['value'].iloc[0]
    adjust_factor = result['value'].iloc[0] / result['000300.SH_p'].iloc[0]
    result['000300.SH_p'] = result['000300.SH_p'] * adjust_factor
    result['return'] = result['value'] - result['value'].shift(1)
    result['return_rate'] = (result.value - start_point) / start_point
    result['ref_rate'] = (result['000300.SH_p'] - start_point) / start_point

    # process plot figure and axes formatting
    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8))
    fig.suptitle('Back Testing Result - reference: 000300.SH')
    ax1.set_position([0.1, 0.55, 0.85, 0.45])
    ax1.plot(result.index, result['ref_rate'], linestyle='-', color=(0.2, 0.2, 0.7), alpha=0.5, label='ref_return')
    ax1.plot(result.index, result['return_rate'], color=(0.7, 0.2, 0.2), alpha=0.6, label='return')
    ax1.set_ylabel('annual return')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.fill_between(result.index, 0, result['ref_rate'],
                     where=result['ref_rate'] >= 0,
                     facecolor=(0.2, 0.6, 0.2), alpha=0.35)
    ax1.fill_between(result.index, 0, result['ref_rate'],
                     where=result['ref_rate'] < 0,
                     facecolor=(0.6, 0.2, 0.2), alpha=0.35)
    ax1.legend()

    ax2.set_position([0.1, 0.275, 0.85, 0.207])
    ax2.plot(result.index, result['change'])
    ax2.set_ylabel('amount bought / sold')
    ax2.set_xlabel(None)
    ax2.grid(True)

    ax3.set_position([0.1, 0.1, 0.85, 0.207])
    ax3.bar(result.index, result['return'])
    ax3.set_ylabel('daily return')
    ax3.set_xlabel('date')
    ax3.grid(True)

    # format the ticks
    ax1.xaxis.set_major_locator(years)
    ax1.xaxis.set_major_formatter(years_fmt)
    ax1.xaxis.set_minor_locator(months)

    ax2.xaxis.set_major_locator(years)
    ax2.xaxis.set_major_formatter(years_fmt)
    ax2.xaxis.set_minor_locator(months)

    ax3.xaxis.set_major_locator(years)
    ax3.xaxis.set_major_formatter(years_fmt)
    ax3.xaxis.set_minor_locator(months)

    plt.show()