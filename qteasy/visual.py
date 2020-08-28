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
from .history import get_bar, stock_basic, name_change


def ohlc(stock, start, end=None, asset_type='E', type='candle', figsize=(10, 5), mav=(5, 10, 20, 30)):
    if end is None:
        today = datetime.datetime.today()
        end = today.strftime('dddd-mm-dd')
    data = get_bar(shares=stock, start=start, end=end, asset_type=asset_type)
    share_basic = name_change(ts_code=stock, fields='ts_code,name,start_date,end_date,change_reason')
    share_name = stock + ' - ' + share_basic.name[0]
    print(share_basic.head())
    # data.info()
    daily = data[['open', 'high', 'low', 'close', 'vol']]
    daily.columns=['open', 'high', 'low', 'close', 'volume']
    daily.index = data['trade_date']
    daily = daily.rename(index=pd.Timestamp).sort_index()
    # print(daily.head())
    # manipulating of mpf:
    mc = mpf.make_marketcolors(up='r', down='g',
                               volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    mpf.plot(daily,
             title=share_name,
             volume=True,
             type=type,
             style=s,
             figsize=figsize,
             mav=mav,
             figscale=0.5)
