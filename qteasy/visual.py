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
from .history import get_bar


def ohlc(stock, start, end, style='yahoo', type='candle', figsize=(18, 10), mav=(5, 10, 20, 30)):
    data = get_bar(shares=stock, start=start, end=end)
    # data.info()
    daily = data[['open', 'high', 'low', 'close', 'vol']]
    daily.columns=['open', 'high', 'low', 'close', 'volume']
    daily.index = data['trade_date']
    daily = daily.rename(index=pd.Timestamp).sort_index()
    # print(daily.head())
    mpf.plot(daily, volume=True, type=type, style=style, figsize=figsize, mav=mav)
