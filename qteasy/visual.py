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
from .utilfuncs import time_str_format


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


def plot_loop_result(result, msg: dict):
    """plot the loop results in a fancy way that displays all infomration more clearly"""
    # prepare result dataframe
    if not isinstance(result, pd.DataFrame):
        raise TypeError('')
    if result.empty:
        raise ValueError()
    # TODO: needs to find out all the stock holding columns,
    # TODO: and calculate change according to the change of all
    # TODO: stocks
    result_columns = result.columns
    fixed_column_items = ['fee', 'cash', 'value', 'reference']
    stock_holdings = [item for
                      item in
                      result_columns if
                      item not in fixed_column_items and
                      item[-2:] != '_p']
    change = (result[stock_holdings] - result[stock_holdings].shift(1)).sum(1)
    start_point = result['value'].iloc[0]
    adjust_factor = result['value'].iloc[0] / result['reference'].iloc[0]
    reference = result['reference'] * adjust_factor
    ret = result['value'] - result['value'].shift(1)
    return_rate = (result.value - start_point) / start_point * 100
    ref_rate = (reference - start_point) / start_point * 100

    # process plot figure and axes formatting
    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    CHART_WIDTH = 0.88

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle('Back Testing Result - reference: 000300.SH')

    fig.text(0.05, 0.93, f'periods: {msg["years"]} years, '
                         f'from: {msg["loop_start"].date()} to {msg["loop_end"].date()}   ... '
                         f'time consumed:   signal creation: {time_str_format(msg["run_time_p"])};'
                         f'  back test:{time_str_format(msg["run_time_l"])}')
    fig.text(0.05, 0.90, f'operation summary: {msg["oper_count"].values.sum()}     Total operation fee:'
                         f'¥{msg["total_fee"]:13,.2f}     '
                         f'total investment amount: ¥{msg["total_invest"]:13,.2f}    '
                         f'final value:  ¥{msg["final_value"]:13,.2f}')
    fig.text(0.05, 0.87, f'Total return: {msg["rtn"] * 100:.3f}%    '
                         f'Avg annual return: {((msg["rtn"] + 1) ** (1 / msg["years"]) - 1) * 100: .3f}%    '
                         f'ref return: {msg["ref_rtn"] * 100:.3f}%    '
                         f'Avg annual ref return: {msg["ref_annual_rtn"] * 100:.3f}%')
    ax1.set_position([0.05, 0.41, CHART_WIDTH, 0.40])
    ax1.plot(result.index, ref_rate, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='reference')
    ax1.plot(result.index, return_rate, linestyle='-',
             color=(0.8, 0.2, 0.0), alpha=0.85, label='return')
    ax1.set_ylabel('Total return rate')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.fill_between(result.index, 0, ref_rate,
                     where=ref_rate >= 0,
                     facecolor=(0.4, 0.6, 0.2), alpha=0.35)
    ax1.fill_between(result.index, 0, ref_rate,
                     where=ref_rate < 0,
                     facecolor=(0.8, 0.2, 0.0), alpha=0.35)
    ax1.yaxis.tick_right()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax1.axvspan(pd.Timestamp('20150101'), pd.Timestamp('20170702'), facecolor='0.15', alpha=0.15)
    ax1.legend()

    ax2.set_position([0.05, 0.23, CHART_WIDTH, 0.18])
    ax2.plot(result.index, change)
    ax2.set_ylabel('Amount bought / sold')
    ax2.set_xlabel(None)
    ax2.yaxis.tick_right()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.grid(True)

    ax3.set_position([0.05, 0.05, CHART_WIDTH, 0.18])
    ax3.bar(result.index, ret)
    ax3.set_ylabel('Daily return')
    ax3.set_xlabel('date')
    ax3.yaxis.tick_right()
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['bottom'].set_visible(False)
    ax3.spines['left'].set_visible(False)
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