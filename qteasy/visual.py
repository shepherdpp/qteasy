# coding=utf-8
# -*- coding: utf-8 -*-
# visual.py

# =====================================4
# This file contains components for the qt
# to establish visual outputs of price data
# loop result and strategy optimization
# results as well
# ======================================

import mplfinance as mpf
from mplfinance.original_flavor import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

import pandas as pd
import numpy as np

from .history import get_history_panel
from .tsfuncs import stock_basic, fund_basic, future_basic, index_basic
from .utilfuncs import time_str_format, list_to_str_format
from .tafuncs import macd, dema, rsi, bbands, ma

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

ValidAddPlots = ['macd',
                 'dma',
                 'trix']
title_font = {'fontname': 'pingfang HK',
              'size':     '16',
              'color':    'black',
              'weight':   'bold',
              'va':       'bottom',
              'ha':       'center'}
large_red_font = {'fontname': 'Arial',
                  'size':     '24',
                  'color':    'red',
                  'weight':   'bold',
                  'va':       'bottom'}
large_green_font = {'fontname': 'Arial',
                    'size':     '24',
                    'color':    'green',
                    'weight':   'bold',
                    'va':       'bottom'}
small_red_font = {'fontname': 'Arial',
                  'size':     '12',
                  'color':    'red',
                  'weight':   'bold',
                  'va':       'bottom'}
small_green_font = {'fontname': 'Arial',
                    'size':     '12',
                    'color':    'green',
                    'weight':   'bold',
                    'va':       'bottom'}
normal_label_font = {'fontname': 'pingfang HK',
                     'size':     '12',
                     'color':    'black',
                     'weight':   'normal',
                     'va':       'bottom',
                     'ha':       'right'}
normal_font = {'fontname': 'Arial',
               'size':     '12',
               'color':    'black',
               'weight':   'normal',
               'va':       'bottom',
               'ha':       'left'}


# 动态交互式蜡烛图类
class InterCandle:
    def __init__(self, data, stock_name, style, idx_start=0, idx_range=100):
        self.pressed = False
        self.xpress = None

        # 初始化交互式K线图对象，历史数据作为唯一的参数用于初始化对象
        self.data = data
        self.style = style
        self.stock_name = stock_name
        # 设置初始化的K线图显示区间起点为0，即显示第0到第99个交易日的数据（前100个数据）
        self.idx_start = idx_start
        self.idx_range = idx_range
        # 设置ax1图表中显示的均线类型
        self.avg_type = 'ma'
        self.indicator = 'macd'

        self.cur_xlim = None

        # 初始化figure对象，在figure上建立三个Axes对象并分别设置好它们的位置和基本属性
        self.fig = mpf.figure(style=style, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
        fig = self.fig
        self.ax1 = fig.add_axes([0.08, 0.25, 0.88, 0.60])
        self.ax1.set_xbound(0, 100)
        # self.ax1.set_xticklabels(data.index)
        self.ax2 = fig.add_axes([0.08, 0.15, 0.88, 0.10], sharex=self.ax1)
        self.ax2.set_ylabel('volume')
        self.ax3 = fig.add_axes([0.08, 0.05, 0.88, 0.10], sharex=self.ax1)
        self.ax3.set_ylabel('macd')
        # 初始化figure对象，在figure上预先放置文本并设置格式，文本内容根据需要显示的数据实时更新
        self.t1 = fig.text(0.50, 0.94, f'{self.stock_name}', **title_font)
        self.t2 = fig.text(0.12, 0.90, '开/收: ', **normal_label_font)
        self.t3 = fig.text(0.14, 0.89, f'', **large_red_font)
        self.t4 = fig.text(0.14, 0.86, f'', **small_red_font)
        self.t5 = fig.text(0.22, 0.86, f'', **small_red_font)
        self.t6 = fig.text(0.12, 0.86, f'', **normal_label_font)
        self.t7 = fig.text(0.40, 0.90, '高: ', **normal_label_font)
        self.t8 = fig.text(0.40, 0.90, f'', **small_red_font)
        self.t9 = fig.text(0.40, 0.86, '低: ', **normal_label_font)
        self.t10 = fig.text(0.40, 0.86, f'', **small_green_font)
        self.t11 = fig.text(0.55, 0.90, '量(万手): ', **normal_label_font)
        self.t12 = fig.text(0.55, 0.90, f'', **normal_font)
        self.t13 = fig.text(0.55, 0.86, '额(亿元): ', **normal_label_font)
        self.t14 = fig.text(0.55, 0.86, f'', **normal_font)
        self.t15 = fig.text(0.70, 0.90, '涨停: ', **normal_label_font)
        self.t16 = fig.text(0.70, 0.90, f'', **small_red_font)
        self.t17 = fig.text(0.70, 0.86, '跌停: ', **normal_label_font)
        self.t18 = fig.text(0.70, 0.86, f'', **small_green_font)
        self.t19 = fig.text(0.85, 0.90, '均价: ', **normal_label_font)
        self.t20 = fig.text(0.85, 0.90, f'', **normal_font)
        self.t21 = fig.text(0.85, 0.86, '昨收: ', **normal_label_font)
        self.t22 = fig.text(0.85, 0.86, f'', **normal_font)

        plot_data = self.data
        data_len = len(plot_data)

        # 绘制图表:
        # 绘制K线图
        self.lines, self.polys = candlestick2_ohlc(self.ax1,
                                                   plot_data.open,
                                                   plot_data.high,
                                                   plot_data.low,
                                                   plot_data.close, width=0.6, colorup='r', colordown='g')
        # 区分红色和绿色K线，分别绘制红色和绿色的交易量柱子
        volume_up = np.where(plot_data.open > plot_data.close, plot_data.volume, 0)
        volume_down = np.where(plot_data.open <= plot_data.close, plot_data.volume, 0)
        self.vup = self.ax2.bar(np.arange(data_len),
                                volume_up, width=0.8, color='r')
        self.vdn = self.ax2.bar(np.arange(data_len),
                                volume_down, width=0.8, color='g')

        # 生成移动均线，并绘制四条移动均线
        self.ma1, self.ma2, self.ma3, self.ma4 = self.ax1.plot(np.arange(data_len),
                                                               plot_data[['MA5', 'MA10', 'MA20', 'MA60']])
        # 生成布林带线，并绘制三条布林带线，初始状态下，设置布林带线不可见
        self.bbu, self.bbm, self.bbl = self.ax1.plot(np.arange(data_len),
                                                     plot_data[['bb-u', 'bb-m', 'bb-l']])
        self.bbu.set_visible(False)
        self.bbm.set_visible(False)
        self.bbl.set_visible(False)
        # 生成macd线和柱，初始状态下，MACD线可见
        self.macd_m, self.macd_s = self.ax3.plot(np.arange(data_len), plot_data[['macd-m', 'macd-s']])
        # MACD线的红绿两色柱子需要分别生成并绘制
        macd_bar_r = np.where(plot_data['macd-h'] > 0, plot_data['macd-h'], 0)
        macd_bar_g = np.where(plot_data['macd-h'] <= 0, plot_data['macd-h'], 0)
        self.macd_rbars = self.ax3.bar(np.arange(data_len), macd_bar_r, color='r')
        self.macd_gbars = self.ax3.bar(np.arange(data_len), macd_bar_g, color='g')
        # 生成rsi线和上下界，并设置RSI线不可见
        self.rsi_up, = self.ax3.plot(np.arange(data_len), [75] * len(plot_data), color=(0.75, 0.5, 0.5))
        self.rsi_dn, = self.ax3.plot(np.arange(data_len), [30] * len(plot_data), color=(0.5, 0.75, 0.5))
        self.rsi, = self.ax3.plot(np.arange(data_len), plot_data['rsi'])
        self.rsi_up.set_visible(False)
        self.rsi_dn.set_visible(False)
        self.rsi.set_visible(False)
        # 生成dema线，并设置DEMA线不可见
        self.dema, = self.ax3.plot(np.arange(data_len), plot_data['dema'])
        self.dema.set_visible(False)

        # 设置三张图表的显示界限

        fig.canvas.mpl_connect('button_press_event', self.on_press)
        fig.canvas.mpl_connect('button_release_event', self.on_release)
        fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        fig.canvas.mpl_connect('scroll_event', self.on_scroll)

    def refresh_plot(self, idx_start, idx_range):
        """ 根据最新的参数，重新绘制整个图表
        """
        ap = []
        # 添加K线图重叠均线，根据均线类型添加移动均线或布林带线
        plot_data = self.data.iloc[idx_start:idx_start + idx_range - 1]
        if self.avg_type == 'ma':
            ap.append(mpf.make_addplot(plot_data[['MA5', 'MA10', 'MA20', 'MA60']], ax=self.ax1))
        elif self.avg_type == 'bb':
            ap.append(mpf.make_addplot(plot_data[['bb-u', 'bb-m', 'bb-l']], ax=self.ax1))
        else:
            pass  # 不添加任何均线
        # 添加指标，根据指标类型添加MACD或RSI或DEMA
        if self.indicator == 'macd':
            ap.append(mpf.make_addplot(plot_data[['macd-m', 'macd-s']], ylabel='macd', ax=self.ax3))
            bar_r = np.where(plot_data['macd-h'] > 0, plot_data['macd-h'], 0)
            bar_g = np.where(plot_data['macd-h'] <= 0, plot_data['macd-h'], 0)
            ap.append(mpf.make_addplot(bar_r, type='bar', color='red', ax=self.ax3))
            ap.append(mpf.make_addplot(bar_g, type='bar', color='green', ax=self.ax3))
            self.ax3.set_ylabel('macd')
        elif self.indicator == 'rsi':
            ap.append(mpf.make_addplot([75] * len(plot_data), color=(0.75, 0.6, 0.6), ax=self.ax3))
            ap.append(mpf.make_addplot([30] * len(plot_data), color=(0.6, 0.75, 0.6), ax=self.ax3))
            ap.append(mpf.make_addplot(plot_data['rsi'], ylabel='rsi', ax=self.ax3))
            self.ax3.set_ylabel('rsi')
        else:  # indicator == 'dema'
            ap.append(mpf.make_addplot(plot_data['dema'], ylabel='dema', ax=self.ax3))
            self.ax3.set_ylabel('dema')
        # 绘制图表
        mpf.plot(plot_data,
                 ax=self.ax1,
                 volume=self.ax2,
                 addplot=ap,
                 type='candle',
                 style=self.style,
                 datetime_format='%Y-%m',
                 xrotation=0)
        plt.show()

    def refresh_texts(self, display_data):
        """ 更新K线图上的价格文本
        """
        # display_data是一个交易日内的所有数据，将这些数据分别填入figure对象上的文本中
        self.t3.set_text(f'{display_data["open"]:.3f} / {display_data["close"]:.3f}')
        self.t4.set_text(f'{display_data["change"]:.3f}')
        self.t5.set_text(f'[{display_data["pct_change"]:.3f}%]')
        self.t6.set_text(f'{display_data.name.date()}')
        self.t8.set_text(f'{display_data["high"]:.3f}')
        self.t10.set_text(f'{display_data["low"]:.3f}')
        self.t12.set_text(f'{display_data["volume"] / 10000:.3f}')
        self.t14.set_text(f'{display_data["value"]:.3f}')
        self.t16.set_text(f'{display_data["upper_lim"]:.3f}')
        self.t18.set_text(f'{display_data["lower_lim"]:.3f}')
        self.t20.set_text(f'{display_data["average"]:.3f}')
        self.t22.set_text(f'{display_data["last_close"]:.3f}')
        # 根据本交易日的价格变动值确定开盘价、收盘价的显示颜色
        if display_data['change'] > 0:  # 如果今日变动额大于0，即今天价格高于昨天，今天价格显示为红色
            close_number_color = 'red'
        elif display_data['change'] < 0:  # 如果今日变动额小于0，即今天价格低于昨天，今天价格显示为绿色
            close_number_color = 'green'
        else:
            close_number_color = 'black'
        self.t3.set_color(close_number_color)
        self.t4.set_color(close_number_color)
        self.t5.set_color(close_number_color)
        plt.show()

    def on_press(self, event):
        # 如果点击范围不在ax1或ax3范围内则退出
        if not (event.inaxes == self.ax1 or event.inaxes == self.ax3):
            return
        if event.button != 1:
            return
        self.pressed = True
        self.xpress = event.xdata
        self.cur_xlim = self.ax1.get_xlim()
        print(f'cur_xlim is {self.cur_xlim}')

        # 当当前鼠标点击模式为双击时，继续检查更新K线图
        if event.dblclick == 1:
            # 当点击位置在ax1中时，切换当前ma类型, 在ma、bb、none之间循环
            if event.inaxes == self.ax1:
                if self.avg_type == 'ma':
                    self.avg_type = 'bb'
                elif self.avg_type == 'bb':
                    self.avg_type = 'none'
                else:
                    self.avg_type = 'ma'
                # 更新K线图
            # 当点击位置在ax3范围内时，切换当前indicator类型，在macd/dma/rsi/kdj之间循环
            else:  # event.inaxes == self.ax3
                if self.indicator == 'macd':
                    self.indicator = 'dma'
                elif self.indicator == 'dma':
                    self.indicator = 'rsi'
                else:
                    self.indicator = 'macd'
            # 更新K线图
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.refresh_plot(self.idx_start, self.idx_range)

    def on_release(self, event):
        """当释放鼠标按键时，更新新的K线起点"""
        self.pressed = False
        if self.xpress is None:
            return
        dx = int(event.xdata - self.xpress)
        self.idx_start -= dx
        if self.idx_start <= 0:
            self.idx_start = 0
        if self.idx_start >= len(self.data) - 100:
            self.idx_start = len(self.data) - 100

    def on_motion(self, event):
        """当鼠标移动时，如果鼠标已经按下，计算鼠标水平移动距离，并根据水平距离计算K线平移距离"""
        if not self.pressed:
            return
        if not event.inaxes == self.ax1:
            return
        # 计算鼠标的水平移动距离
        dx = int(event.xdata - self.xpress)
        new_start = self.idx_start - dx
        # 设定平移的左右界限，如果平移后超出界限，则不再平移
        if new_start <= 0:
            new_start = 0
        if new_start >= len(self.data) - 100:
            new_start = len(self.data) - 100
        # 根据水平距离重新绘制K线图
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.refresh_texts(self.data.iloc[new_start])
        self.refresh_plot(new_start, self.idx_range)

    def on_scroll(self, event):
        """当鼠标滚轮滚动时，更新K线图的显示范围"""
        if event.inaxes != self.ax1:
            return
        # 确认是否是正确的滚轮滚动
        if event.button == 'down':
            # 缩小20%显示范围
            scale_factor = 0.8
        elif event.button == 'up':
            # 放大20%显示范围
            scale_factor = 1.2
        else:
            # 特殊情况处理
            scale_factor = 1
            print(event.button)
        # 更新K线图显示范围
        self.idx_range = int(self.idx_range * scale_factor)
        # 确认显示范围是否超出允许范围：最小30、最大不超过当前起点到终点的距离
        data_length = len(self.data)
        if self.idx_range >= data_length - self.idx_start:
            self.idx_range = data_length - self.idx_start
        if self.idx_range <= 30:
            self.idx_range = 30
        # 更新K线图
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.refresh_texts(self.data.iloc[self.idx_start])
        self.refresh_plot(self.idx_start, self.idx_range)


# TODO: simplify and merge these three functions
def candle(stock=None, start=None, end=None, stock_data=None, share_name=None, asset_type='E',
           no_visual=False, **kwargs):
    """plot stock data or extracted data in candle form"""
    return mpf_plot(stock_data=stock_data, share_name=share_name, stock=stock, start=start,
                    end=end, asset_type=asset_type, plot_type='candle', no_visual=no_visual,
                    **kwargs)


def ohlc(stock=None, start=None, end=None, stock_data=None, share_name=None, asset_type='E',
         no_visual=False, **kwargs):
    """plot stock data or extracted data in ohlc form"""
    return mpf_plot(stock_data=stock_data, share_name=share_name, stock=stock, start=start,
                    end=end, asset_type=asset_type, plot_type='ohlc', no_visual=no_visual,
                    **kwargs)


def renko(stock=None, start=None, end=None, stock_data=None, share_name=None, asset_type='E',
          no_visual=False, **kwargs):
    """plot stock data or extracted data in renko form"""
    return mpf_plot(stock_data=stock_data, share_name=share_name, stock=stock, start=start,
                    end=end, asset_type=asset_type, plot_type='renko', no_visual=no_visual,
                    **kwargs)


def mpf_plot(stock_data=None, share_name=None, stock=None, start=None, end=None,
             asset_type='E', plot_type=None, no_visual=False, mav=None, indicator=None,
             indicator_par=None, **kwargs):
    """plot stock data or extracted data in renko form
    """
    assert plot_type is not None
    if end is None:
        now = pd.to_datetime('now') + pd.Timedelta(8, 'h')
        if now.hour >= 23:
            end = pd.to_datetime('today')
        else:
            end = pd.to_datetime('today') - pd.Timedelta(1, 'd')
    if start is None:
        start = end - pd.Timedelta(60, 'd')
    if mav is None:
        mav = [5, 10, 20, 60]
    end = pd.to_datetime(end)
    start = pd.to_datetime(start)
    if stock_data is None:
        assert stock is not None
        if 'adj' in kwargs:
            adj = kwargs['adj']
        else:
            adj = 'none'
        # 准备股票数据，为了实现动态图表，应该获取一只股票在全历史周期内的所有价格数据，并且在全周期上计算
        # 所需的均线以及指标数据，显示的时候只显示其中一部分即可，并且可以使用鼠标缩放平移
        # 因此_prepare_mpf_data()函数应该返回一个包含所有历史价格以及相关指标的DataFrame
        daily, share_name = _get_mpf_data(stock=stock,
                                          asset_type=asset_type,
                                          adj=adj,
                                          mav=mav,
                                          indicator=indicator,
                                          indicator_par=indicator_par)
        has_volume = True
    else:
        assert isinstance(stock_data, pd.DataFrame)
        assert all(col in stock_data.columns for col in ['open', 'high', 'low', 'close'])
        daily = stock_data
        has_volume = 'volume' in stock_data.columns
        if share_name is None:
            share_name = 'stock'

    daily = _add_indicators(daily, mav=mav)

    my_color = mpf.make_marketcolors(up='r',
                                     down='g',
                                     edge='inherit',
                                     wick='inherit',
                                     volume='inherit')
    my_style = mpf.make_mpf_style(marketcolors=my_color,
                                  figcolor='(0.82, 0.83, 0.85)',
                                  gridcolor='(0.82, 0.83, 0.85)')
    if not no_visual:
        idx_start = np.searchsorted(daily.index, start)
        idx_range = np.searchsorted(daily.index, end) - idx_start
        my_candle = InterCandle(data=daily, stock_name=share_name, style=my_style,
                                idx_start=idx_start, idx_range=idx_range)
        my_candle.refresh_texts(daily.iloc[idx_start + idx_range - 1])
        my_candle.refresh_plot(idx_start, idx_range)
    return daily


def _get_mpf_data(stock, asset_type='E', adj='none', freq='d', mav=None, indicator=None, indicator_par=None):
    """ 返回一只股票在全部历史区间上的价格数据，生成一个pd.DataFrame. 包含open, high, low, close, volume 五组数据
        并返回股票的名称。

    :param stock: 股票代码
    :param asset_type: 资产类型，E——股票，F——期货，FD——基金，I——指数
    :param adj: 是否复权，none——不复权，hfq——后复权，qfq——前复权
    :param freq: 价格周期，d——日K线，5min——五分钟k线
    :param mav: 移动平均线，一个tuple，包含数个integer，代表均线周期
    :param indicator: str，指标，如MACD等
    :param indicator_par:
    :return:
        tuple：(pd.DataFrame, share_name)
    """
    # 首先获取股票的上市日期，并获取从上市日期开始到现在的所有历史数据
    name_of = {'E':  'Stock 股票',
               'I':  'Index 指数',
               'F':  'Futures 期货',
               'FD': 'Fund 基金'}
    if asset_type == 'E':
        basic_info = stock_basic(fields='ts_code,symbol,name,fullname,area,industry,list_date')
    elif asset_type == 'I':
        # 获取指数的基本信息
        basic_info = index_basic()
    elif asset_type == 'F':
        # 获取期货的基本信息
        basic_info = future_basic()
    elif asset_type == 'FD':
        # 获取基金的基本信息
        basic_info = fund_basic()
    else:
        raise KeyError(f'Wrong asset type: [{asset_type}]')
    this_stock = basic_info.loc[basic_info.ts_code == stock]
    if this_stock.empty:
        raise KeyError(f'Can not find historical data for asset {stock} of type {asset_type}!')
    # 设置历史数据获取区间的开始日期为股票上市第一天
    start_date = pd.to_datetime(this_stock.list_date.values[0]).strftime('%Y-%m-%d')
    # 设置历史数据获取最后一天，只有现在的时间在23:00以后时才设置为今天，否则就设置为昨天
    # now获取的日期时间是格林尼治标准时间，计算中国的时间需要加8小时（中国在东八区）
    now = pd.to_datetime('now') + pd.Timedelta(8, 'h')
    if now.hour >= 23 and now.weekday() < 5:
        end = pd.to_datetime('today')
    else:
        end = pd.to_datetime('today') - pd.Timedelta(now.weekday() - 4, 'd')
    end_date = end.strftime('%Y-%m-%d')
    name = this_stock.name.values[0]
    # fullname = this_stock.fullname.values[0]
    # 读取该股票从上市第一天到今天的全部历史数据，包括ohlc和volume数据
    data = get_history_panel(start=start_date, end=end_date, freq=freq, shares=stock,
                             htypes='close,high,low,open,vol', asset_type=asset_type,
                             adj=adj, chanel='local', parallel=10).to_dataframe(share=stock)
    # 返回股票的名称和全称
    share_name = stock + ' - ' + name + ' [' + name_of[asset_type] + '] '
    data.rename({'vol': 'volume'}, axis='columns', inplace=True)

    return data, share_name


def _add_indicators(data, mav=None, bb_par=None, macd_par=None, rsi_par=None, dema_par=None):
    """ data是一只股票的历史K线数据，包括O/H/L/C/V五组数据或者O/H/L/C四组数据
        并根据这些数据生成以下数据，加入到data中：

        - Moving Average
        - change and percent change
        - average
        - last close
        - Bband
        - macd
        - kdj
        - dma
        - rsi

    :param data:
    :return: pd.DataFrame
    """
    if mav is None:
        mav = (5, 10, 20)
    # 其他indicator的parameter使用默认值
    if dema_par is None:
        dema_par = (30,)
    if macd_par is None:
        macd_par = (9, 12, 26)
    if rsi_par is None:
        rsi_par = (14,)
    if bb_par is None:
        bb_par = (20, 2, 2, 0)
    # 在DataFrame中增加均线信息：
    assert isinstance(mav, (list, tuple))
    assert all(isinstance(item, int) for item in mav)
    for value in mav:
        data['MA' + str(value)] = ma(data.close, timeperiod=value)  # 以后还可以加上不同的ma_type
    data['change'] = np.round(data['close'] - data['close'].shift(1), 3)
    data['pct_change'] = np.round(data['change'] / data['close'] * 100, 2)
    data['value'] = np.round(data['close'] * data['volume'] / 1000000, 2)
    data['upper_lim'] = np.round(data['close'] * 1.1, 3)
    data['lower_lim'] = np.round(data['close'] * 0.9, 3)
    data['last_close'] = data['close'].shift(1)
    data['average'] = data[['open', 'close', 'high', 'low']].mean(axis=1)
    data['volrate'] = data['volume']
    # 添加不同的indicator
    data['dema'] = dema(data.close, *dema_par)
    data['macd-m'], data['macd-s'], data['macd-h'] = macd(data.close, *macd_par)
    data['rsi'] = rsi(data.close, *rsi_par)
    data['bb-u'], data['bb-m'], data['bb-l'] = bbands(data.close, *bb_par)

    return data


def _plot_loop_result(loop_results: dict, config):
    """plot the loop results in a fancy way that displays all information more clearly"""
    # prepare looped_values dataframe
    if not isinstance(loop_results, dict):
        raise TypeError('')
    looped_values = loop_results['complete_values']
    if looped_values.empty:
        raise ValueError(f'No meaningful operation list is created in current period thus back looping is skipped!')
    # register matplotlib converters is requested in future matplotlib versions
    register_matplotlib_converters()
    # 计算在整个投资回测区间内每天的持股数量，通过持股数量的变化来推出买卖点
    result_columns = looped_values.columns
    fixed_column_items = ['fee', 'cash', 'value', 'reference', 'ref', 'ret']
    stock_holdings = [item for
                      item in
                      result_columns if
                      item not in fixed_column_items and
                      item[-2:] != '_p']
    # 为了确保回测结果和参考价格在同一个水平线上比较，需要将他们的起点"重合"在一起，否则
    # 就会出现两者无法比较的情况。
    # 例如，当参考价格为HS300指数，而回测时的初始资金额为100000时，回测结果的金额通常在
    # 100000以上，而HS300指数的价格仅仅在2000～5000之间波动，这就导致在同一个图表上
    # plot两个指标时，只能看到回测结果，而HS300指数则被压缩成了一条直线，无法对比
    # 解决办法时同时显示两者的相对收益率，两条线的起点都是0，就能很好地解决上述问题。

    # 持股数量变动量，当持股数量发生变动时，判断产生买卖行为
    change = (looped_values[stock_holdings] - looped_values[stock_holdings].shift(1)).sum(1)
    # 计算回测记录第一天的回测结果和参考指数价格，以此计算后续的收益率曲线
    start_point = looped_values['value'].iloc[0]
    ref_start = looped_values['reference'].iloc[0]
    # 计算回测结果的每日回报率
    ret = looped_values['value'] - looped_values['value'].shift(1)
    # 计算每日的持仓仓位
    position = 1 - (looped_values['cash'] / looped_values['value'])
    # 回测结果和参考指数的总体回报率曲线
    return_rate = (looped_values.value - start_point) / start_point * 100
    ref_rate = (looped_values.reference - ref_start) / ref_start * 100

    # process plot figure and axes formatting
    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    weekdays = mdates.WeekdayLocator()  # every weekday
    years_fmt = mdates.DateFormatter('%Y')
    month_fmt_none = mdates.DateFormatter('')
    month_fmt_l = mdates.DateFormatter('%y/%m')
    month_fmt_s = mdates.DateFormatter('%m')

    chart_width = 0.88
    # 显示投资回报评价信息
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    if isinstance(config.asset_pool, str):
        title_asset_pool = config.asset_pool
    else:
        if len(config.asset_pool) > 3:
            title_asset_pool = list_to_str_format(config.asset_pool[:3]) + '...'
        else:
            title_asset_pool = list_to_str_format(config.asset_pool)
    fig.suptitle(f'Back Testing Result {title_asset_pool} - benchmark: {config.reference_asset}',
                 fontsize=14,
                 fontweight=10)
    # 投资回测结果的评价指标全部被打印在图表上，所有的指标按照表格形式打印
    # 为了实现表格效果，指标的标签和值分成两列打印，每一列的打印位置相同
    fig.text(0.07, 0.93, f'periods: {loop_results["years"]} years, '
                         f'from: {loop_results["loop_start"].date()} to {loop_results["loop_end"].date()}'
                         f'time consumed:   signal creation: {time_str_format(loop_results["op_run_time"])};'
                         f'  back test:{time_str_format(loop_results["loop_run_time"])}')
    fig.text(0.21, 0.82, f'Operation summary:\n\n'
                         f'Total op fee:\n'
                         f'total investment:\n'
                         f'final value:', ha='right')
    fig.text(0.23, 0.82, f'{loop_results["oper_count"].buy.sum()}     buys \n'
                         f'{loop_results["oper_count"].sell.sum()}     sells\n'
                         f'¥{loop_results["total_fee"]:13,.2f}\n'
                         f'¥{loop_results["total_invest"]:13,.2f}\n'
                         f'¥{loop_results["final_value"]:13,.2f}')
    fig.text(0.50, 0.82, f'Total return:\n'
                         f'Avg annual return:\n'
                         f'ref return:\n'
                         f'Avg annual ref return:\n'
                         f'Max drawdown:', ha='right')
    fig.text(0.52, 0.82, f'{loop_results["rtn"] * 100:.2f}%    \n'
                         f'{loop_results["annual_rtn"] * 100: .2f}%    \n'
                         f'{loop_results["ref_rtn"] * 100:.2f}%    \n'
                         f'{loop_results["ref_annual_rtn"] * 100:.2f}%\n'
                         f'{loop_results["mdd"] * 100:.3f}%'
                         f' on {loop_results["valley_date"]}')
    fig.text(0.82, 0.82, f'alpha:\n'
                         f'Beta:\n'
                         f'Sharp ratio:\n'
                         f'Info ratio:\n'
                         f'250-day volatility:', ha='right')
    fig.text(0.84, 0.82, f'{loop_results["alpha"]:.3f}  \n'
                         f'{loop_results["beta"]:.3f}  \n'
                         f'{loop_results["sharp"]:.3f}  \n'
                         f'{loop_results["info"]:.3f}  \n'
                         f'{loop_results["volatility"]:.3f}')

    ax1.set_position([0.05, 0.41, chart_width, 0.40])
    # 绘制参考数据的收益率曲线图
    ax1.plot(looped_values.index, ref_rate, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='Reference')

    # 绘制回测结果的收益率曲线图
    ax1.plot(looped_values.index, return_rate, linestyle='-',
             color=(0.8, 0.2, 0.0), alpha=0.85, label='Return')
    ax1.set_ylabel('Total return rate')
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    # 填充参考收益率的正负区间，绿色填充正收益率，红色填充负收益率
    ax1.fill_between(looped_values.index, 0, ref_rate,
                     where=ref_rate >= 0,
                     facecolor=(0.4, 0.6, 0.2), alpha=0.35)
    ax1.fill_between(looped_values.index, 0, ref_rate,
                     where=ref_rate < 0,
                     facecolor=(0.8, 0.2, 0.0), alpha=0.35)

    # 显示持股仓位区间（效果是在回测区间上用绿色带表示多头仓位，红色表示空头仓位，颜色越深仓位越高）
    # 查找每次买进和卖出的时间点并将他们存储在一个列表中，用于标记买卖时机
    if config.show_positions:
        position_bounds = [looped_values.index[0]]
        position_bounds.extend(looped_values.loc[change != 0].index)
        position_bounds.append(looped_values.index[-1])
        for first, second, long_short in zip(position_bounds[:-2], position_bounds[1:],
                                             position.loc[position_bounds[:-2]]):
            # 分别使用绿色、红色填充交易回测历史中的多头和空头区间
            if long_short > 0:
                # 用不同深浅的绿色填充多头区间
                if long_short > 1:
                    long_short = 1
                ax1.axvspan(first, second,
                            facecolor=((1 - 0.6 * long_short), (1 - 0.4 * long_short), (1 - 0.8 * long_short)),
                            alpha=0.2)
            else:
                # 用不同深浅的红色填充空头区间
                ax1.axvspan(first, second,
                            facecolor=((1 - 0.2 * long_short), (1 - 0.8 * long_short), (1 - long_short)),
                            alpha=0.2)

    # 显示买卖时机的另一种方法，使用buy / sell 来存储买卖点
    # buy_point是当持股数量增加时为买点，sell_points是当持股数量下降时
    # 在买卖点当天写入的数据是参考数值，这是为了使用散点图画出买卖点的位置
    # 绘制买卖点散点图(效果是在ref线上使用红绿箭头标识买卖点)
    if config.buy_sell_points:
        buy_points = np.where(change > 0, ref_rate, np.nan)
        sell_points = np.where(change < 0, ref_rate, np.nan)
        ax1.scatter(looped_values.index, buy_points, color='green',
                    label='Buy', marker='^', alpha=0.9)
        ax1.scatter(looped_values.index, sell_points, color='red',
                    label='Sell', marker='v', alpha=0.9)

    # put arrow on where max draw down is
    ax1.annotate("Max Drawdown",
                 xy=(loop_results["valley_date"], return_rate[loop_results["valley_date"]]),
                 xycoords='data',
                 xytext=(loop_results["peak_date"], return_rate[loop_results["peak_date"]]),
                 textcoords='data',
                 arrowprops=dict(width=3, headwidth=5, facecolor='black', shrink=0.),
                 ha='right',
                 va='bottom')
    ax1.legend()

    ax2.set_position([0.05, 0.23, chart_width, 0.18])
    ax2.plot(looped_values.index, position)
    ax2.set_ylabel('Amount bought / sold')
    ax2.set_xlabel(None)

    ax3.set_position([0.05, 0.05, chart_width, 0.18])
    ax3.bar(looped_values.index, ret)
    ax3.set_ylabel('Daily return')
    ax3.set_xlabel('date')

    # 设置所有图表的基本格式:
    for ax in [ax1, ax2, ax3]:
        ax.yaxis.tick_right()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.grid(True)

    # format the ticks
    # major tick on year if span > 3 years, else on month
    if loop_results['years'] > 4:
        major_locator = years
        major_formatter = years_fmt
        minor_locator = months
        minor_formatter = month_fmt_none
    elif loop_results['years'] > 2:
        major_locator = years
        major_formatter = years_fmt
        minor_locator = months
        minor_formatter = month_fmt_s
    else:
        major_locator = months
        major_formatter = month_fmt_l
        minor_locator = weekdays
        minor_formatter = month_fmt_none

    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_locator(major_locator)
        ax.xaxis.set_major_formatter(major_formatter)
        ax.xaxis.set_minor_locator(minor_locator)
        ax.xaxis.set_minor_formatter(minor_formatter)

    plt.show()


# TODO: like _print_test_result, take the evaluate results on both opti and test hist data
# TODO: and commit comparison base on these two data sets
def _plot_test_result(opti_eval_res: list,
                      test_eval_res: list = None,
                      config=None):
    """ plot test result of optimization results

    :param test_eval_res:
        :type test_eval_res: list

    :param opti_eval_res:
        :type opti_eval_res: list

    :param config:
    :return:
    """
    # 以下评价指标是可以用来比较优化数据集和测试数据集的表现的，只有以下几个评价指标可以使用子图表显示
    plot_compariables = ['annual_rtn',
                         'mdd',
                         'volatility',
                         'beta',
                         'sharp',
                         'alpha',
                         'info']
    if test_eval_res is None:
        test_eval_res = []
    # 从opti和test评价结果列表中取出完整的回测曲线
    result_count = len(test_eval_res)
    valid_opti_eval_res = [item for item in opti_eval_res if not item['complete_values'].empty]
    valid_test_eval_res = [item for item in test_eval_res if not item['complete_values'].empty]
    opti_complete_value_results = [result['complete_values'] for result in valid_opti_eval_res]
    test_complete_value_results = [result['complete_values'] for result in valid_test_eval_res]
    first_opti_looped_values = opti_complete_value_results[0]
    first_test_looped_values = test_complete_value_results[0]
    opti_reference = first_opti_looped_values.reference
    test_reference = first_test_looped_values.reference
    complete_reference = opti_reference.reindex(opti_reference.index.union(test_reference.index))
    complete_reference.loc[np.isnan(complete_reference)] = test_reference
    # matplotlib 所需固定操作
    register_matplotlib_converters()
    CHART_WIDTH = 0.9
    # 计算在生成的评价指标清单中，有多少个可以进行优化-测试对比的评价指标，根据评价指标的数量生成多少个子图表
    compariable_indicators = [i for i in valid_opti_eval_res[0].keys() if i in plot_compariables]
    compariable_indicator_count = len(compariable_indicators)

    # 显示投资回报评价信息
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle(f'Optimization Test Results - {result_count} sets of strategy parameters', fontsize=14, fontweight=10)

    # 投资回测结果的评价指标全部被打印在图表上，所有的指标按照表格形式打印
    # 为了实现表格效果，指标的标签和值分成两列打印，每一列的打印位置相同
    fig.text(0.07, 0.91, f'opti periods: {valid_opti_eval_res[0]["years"]:.1f} years, '
                         f'from: {valid_opti_eval_res[0]["loop_start"].date()} to '
                         f'{valid_opti_eval_res[0]["loop_end"].date()}  '
                         f'time consumed:'
                         f'  signal creation: {time_str_format(valid_opti_eval_res[0]["op_run_time"])};'
                         f'  back test:{time_str_format(valid_opti_eval_res[0]["loop_run_time"])}\n'
                         f'test periods: {valid_test_eval_res[0]["years"]:.1f} years, '
                         f'from: {valid_test_eval_res[0]["loop_start"].date()} to '
                         f'{valid_test_eval_res[0]["loop_end"].date()}  '
                         f'time consumed:'
                         f'  signal creation: {time_str_format(valid_test_eval_res[0]["op_run_time"])};'
                         f'  back test:{time_str_format(valid_test_eval_res[0]["loop_run_time"])}')

    # 确定参考数据在起始日的数据，以便计算参考数据在整个历史区间内的原因
    ref_start_value = complete_reference.iloc[0]
    reference = (complete_reference - ref_start_value) / ref_start_value * 100
    compariable_plots = []

    # 根据数据对比表的数量不同，生成不同数量的并安排对比表的位置和排列方式
    if compariable_indicator_count == 0:
        # 没有子图表时，历史曲线图占据整个图幅
        ax1.set_position([0.05, 0.05, CHART_WIDTH, 0.8])
    else:
        # 有子图表时，历史曲线图占据大约一半的图幅，其余对比图放置在历史曲线图的下方
        ax1.set_position([0.05, 0.51, CHART_WIDTH, 0.39])
        if compariable_indicator_count == 1:
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 2 - 0.1, 0.40]))
        elif compariable_indicator_count == 2:
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 2 - 0.1, 0.40]))
            compariable_plots.append(fig.add_axes([0.550, 0.05, CHART_WIDTH / 2 - 0.1, 0.40]))
        elif compariable_indicator_count == 3:
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 3 - 0.06, 0.40]))
            compariable_plots.append(fig.add_axes([0.365, 0.05, CHART_WIDTH / 3 - 0.06, 0.40]))
            compariable_plots.append(fig.add_axes([0.680, 0.05, CHART_WIDTH / 3 - 0.06, 0.40]))
        elif compariable_indicator_count == 4:  # 4 plots in one row
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 4 - 0.05, 0.40]))
            compariable_plots.append(fig.add_axes([0.285, 0.05, CHART_WIDTH / 4 - 0.05, 0.40]))
            compariable_plots.append(fig.add_axes([0.521, 0.05, CHART_WIDTH / 4 - 0.05, 0.40]))
            compariable_plots.append(fig.add_axes([0.757, 0.05, CHART_WIDTH / 4 - 0.05, 0.40]))
        elif compariable_indicator_count == 5:  # two rows, 3 and 2 plots each row respectively
            compariable_plots.append(fig.add_axes([0.050, 0.28, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.365, 0.28, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.680, 0.28, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.365, 0.05, CHART_WIDTH / 3 - 0.06, 0.18]))
        elif compariable_indicator_count == 6:
            compariable_plots.append(fig.add_axes([0.050, 0.28, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.368, 0.28, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.686, 0.28, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.368, 0.05, CHART_WIDTH / 3 - 0.06, 0.18]))
            compariable_plots.append(fig.add_axes([0.686, 0.05, CHART_WIDTH / 3 - 0.06, 0.18]))
        elif compariable_indicator_count == 7:
            compariable_plots.append(fig.add_axes([0.050, 0.28, CHART_WIDTH / 4 - 0.05, 0.18]))
            compariable_plots.append(fig.add_axes([0.285, 0.28, CHART_WIDTH / 4 - 0.05, 0.18]))
            compariable_plots.append(fig.add_axes([0.521, 0.28, CHART_WIDTH / 4 - 0.05, 0.18]))
            compariable_plots.append(fig.add_axes([0.757, 0.28, CHART_WIDTH / 4 - 0.05, 0.18]))
            compariable_plots.append(fig.add_axes([0.050, 0.05, CHART_WIDTH / 4 - 0.05, 0.18]))
            compariable_plots.append(fig.add_axes([0.285, 0.05, CHART_WIDTH / 4 - 0.05, 0.18]))
            compariable_plots.append(fig.add_axes([0.521, 0.05, CHART_WIDTH / 4 - 0.05, 0.18]))

    # 绘制历史回测曲线图，包括参考数据、优化数据以及回测数据
    ax1.plot(complete_reference.index, reference, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='reference')
    # 填充参考收益率的正负区间，绿色填充正收益率，红色填充负收益率
    ax1.fill_between(complete_reference.index, 0, reference,
                     where=reference >= 0,
                     facecolor=(0.4, 0.6, 0.2), alpha=0.35)
    ax1.fill_between(complete_reference.index, 0, reference,
                     where=reference < 0,
                     facecolor=(0.8, 0.2, 0.0), alpha=0.35)
    # 逐个绘制所有的opti区间和test区间收益率曲线
    for cres in opti_complete_value_results:
        if not cres.empty:
            start_value = cres.value.iloc[0]
            values = (cres.value - start_value) / start_value * 100
            ax1.plot(first_opti_looped_values.index, values, linestyle='-',
                     color=(0.8, 0.2, 0.0), alpha=0.85, label='return')
    for cres in test_complete_value_results:
        if not cres.empty:
            start_value = cres.value.iloc[0]
            values = (cres.value - start_value) / start_value * 100
            ax1.plot(first_test_looped_values.index, values, linestyle='-',
                     color=(0.2, 0.6, 0.2), alpha=0.85, label='return')
    # 设置历史曲线图表的绘制格式
    ax1.set_ylabel('Total return rate')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.yaxis.tick_right()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)

    # 生成两个DataFrame，分别包含需要显示的对比数据，便于计算它们的统计值并绘制图表
    opti_indicator_df = pd.DataFrame([{key: result[key]
                                       for key in compariable_indicators}
                                      for result in valid_opti_eval_res],
                                     index=[result['par'] for result in valid_opti_eval_res])
    test_indicator_df = pd.DataFrame([{key: result[key]
                                       for key in compariable_indicators}
                                      for result in valid_test_eval_res],
                                     index=[result['par'] for result in valid_test_eval_res])

    # 开始使用循环的方式逐个生成对比图表
    if compariable_indicator_count > 0:
        for ax, name in zip(compariable_plots, compariable_indicators):
            # 设置每一个对比图表的基本显示格式
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_ylabel(f'{name}')
            ax.yaxis.tick_right()
            # 根据config中设置的参数，选择生成三种不同类型的图表之一
            p_type = config.indicator_plot_type
            # 在图表中应该舍去np.inf值，暂时将inf作为na值处理，因此可以使用dropna()去除inf值
            with pd.option_context('mode.use_inf_as_na', True):
                opti_label = f'opti:{opti_indicator_df[name].mean():.2f}±{opti_indicator_df[name].std():.2f}'
                test_label = f'test:{test_indicator_df[name].mean():.2f}±{test_indicator_df[name].std():.2f}'
                if p_type == 0 or p_type == 'errorbar':
                    max_v = opti_indicator_df[name].max()
                    min_v = opti_indicator_df[name].min()
                    mean = opti_indicator_df[name].mean()
                    std = opti_indicator_df[name].std()
                    ax.errorbar(1, mean, std, fmt='ok', lw=3)
                    ax.errorbar(1, mean, np.array(mean - min_v, max_v - mean).T, fmt='.k', ecolor='red', lw=1,
                                label=opti_label)
                    max_v = test_indicator_df[name].max()
                    min_v = test_indicator_df[name].min()
                    mean = test_indicator_df[name].mean()
                    std = test_indicator_df[name].std()
                    ax.errorbar(2, mean, std, fmt='ok', lw=3)
                    ax.errorbar(2, mean, np.array(mean - min_v, max_v - mean).T, fmt='.k', ecolor='green', lw=1,
                                label=test_label)
                    ax.set_xlim(0, 3)
                    labels = ['opti', 'test']
                    ax.set_xticks(np.arange(1, len(labels) + 1))
                    ax.set_xticklabels(labels)
                    ax.set_xlim(0.25, len(labels) + 0.75)
                    ax.legend()
                elif p_type == 1 or p_type == 'scatter':
                    ax.scatter(opti_indicator_df[name].fillna(np.nan),
                               test_indicator_df[name].fillna(np.nan),
                               label=name, marker='^', alpha=0.9)
                    ax.set_title(opti_label)
                    ax.set_ylabel(test_label)
                    ax.legend()
                elif p_type == 2 or p_type == 'histo':
                    ax.hist(opti_indicator_df[name].fillna(np.nan), bins=15, alpha=0.5,
                            label=opti_label)
                    ax.hist(test_indicator_df[name].fillna(np.nan), bins=15, alpha=0.5,
                            label=test_label)
                    ax.legend()
                elif p_type == 3 or p_type == 'violin':
                    data_df = pd.DataFrame(np.array([opti_indicator_df[name].fillna(np.nan),
                                                     test_indicator_df[name].fillna(np.nan)]).T,
                                           columns=[opti_label, test_label])
                    ax.violinplot(data_df)
                    labels = ['opti', 'test']
                    ax.set_xticks(np.arange(1, len(labels) + 1))
                    ax.set_xticklabels(labels)
                    ax.set_xlim(0.25, len(labels) + 0.75)
                    ax.legend()
                else:
                    data_df = pd.DataFrame(np.array([opti_indicator_df[name].fillna(np.nan),
                                                     test_indicator_df[name].fillna(np.nan)]).T,
                                           columns=[opti_label, test_label])
                    ax.boxplot(data_df)
                    labels = ['opti', 'test']
                    ax.set_xticks(np.arange(1, len(labels) + 1))
                    ax.set_xticklabels(labels)
                    ax.set_xlim(0.25, len(labels) + 0.75)
                    ax.legend()

    plt.show()


def _print_operation_signal(op_list, run_time_prepare_data=0, operator=None, history_data=None):
    """打印实时信号生成模式的运行结果
    """
    print(f'\n'
          f'      ====================================\n'
          f'      |                                  |\n'
          f'      |       OPERATION SIGNALS          |\n'
          f'      |                                  |\n'
          f'      ====================================\n')
    print(f'Operation list is created based on following strategy:\n{operator.strategies}\n'
          f'{operator.info()}')
    print(f'Operation list is created on history data: \n'
          f'starts:     {history_data.hdates[0]}\n'
          f'end:        {history_data.hdates[-1]}')
    print(f'time consumption for operate signal creation: {time_str_format(run_time_prepare_data)}\n')
    print(f'Operation signals are generated on {op_list.index[0]}\nends on {op_list.index[-1]}\n'
          f'Total signals generated: {len(op_list.index)}.')
    print(f'Operation signal for shares on {op_list.index[-1].date()}\n'
          f'Last three operation signals:\n'
          f'{op_list.tail(3)}\n')
    print(f'---------Current Operation Instructions------------\n')
    for share, signal in op_list.iloc[-1].iteritems():
        print(f'------share {share}-----------:')
        if signal > 0:
            print(f'Buy in with {signal * 100}% of total investment value!')
        elif signal < 0:
            print(f'Sell out {-signal * 100}% of current on holding stock!')
    print(f'\n      ===========END OF REPORT=============\n')


def _print_loop_result(loop_results=None, columns=None, headers=None, formatter=None):
    """ 格式化打印输出单次回测的结果，根据columns、headers、formatter等参数选择性输出result中的结果
        确保输出的格式美观一致

    :param loop_results:
    :param columns:
    :param headers:
    :param formatter:
    :return:
    """
    if loop_results is None:
        return
    looped_values = loop_results['complete_values']
    worst_drawdowns = loop_results['worst_drawdowns']
    print(f'\n     ==================================== \n'
          f'     |                                  |\n'
          f'     |       BACK TESTING RESULT        |\n'
          f'     |                                  |\n'
          f'     ====================================')
    print(f'\nqteasy running mode: 1 - History back testing\n'
          f'time consumption for operate signal creation: {time_str_format(loop_results["op_run_time"])}\n'
          f'time consumption for operation back looping:  {time_str_format(loop_results["loop_run_time"])}\n')
    print(f'investment starts on      {looped_values.index[0]}\n'
          f'ends on                   {looped_values.index[-1]}\n'
          f'Total looped periods:     {loop_results["years"]:.1f} years.')
    print(f'-----------operation summary:-----------\n '
          f'{loop_results["oper_count"]}\n'
          f'Total operation fee:     ¥{loop_results["total_fee"]:12,.2f}')
    print(f'total investment amount: ¥{loop_results["total_invest"]:12,.2f}\n'
          f'final value:              ¥{loop_results["final_value"]:12,.2f}')
    print(f'Total return:             {loop_results["rtn"]:13.2%} \n'
          f'Avg Yearly return:        {loop_results["annual_rtn"]:13.2%}')
    print(f'Reference return:         {loop_results["ref_rtn"]:13.2%} \n'
          f'Reference Yearly return:  {loop_results["ref_annual_rtn"]:13.2%}')
    print(f'------strategy loop_results indicators------ \n'
          f'alpha:                    {loop_results["alpha"]:13.3f}\n'
          f'Beta:                     {loop_results["beta"]:13.3f}\n'
          f'Sharp ratio:              {loop_results["sharp"]:13.3f}\n'
          f'Info ratio:               {loop_results["info"]:13.3f}\n'
          f'250 day volatility:       {loop_results["volatility"]:13.3f}\n'
          f'Max drawdown:             {loop_results["mdd"]:13.2%} \n'
          f'    peak / valley:        {loop_results["peak_date"].date()} / {loop_results["valley_date"].date()}\n'
          f'    recovered on:         {loop_results["recover_date"].date()}\n'
          f'Worst 5 drawdonws:        \n')
    print(worst_drawdowns.to_string(formatters={'drawdown': '{:.2%}'.format}))
    print(f'\n===========END OF REPORT=============\n')


# TODO: like _plot_test_result, take the evaluate results on both opti and test hist data
# TODO: and commit comparison base on these two data sets
def _print_test_result(result, config=None, columns=None, headers=None, formatter=None):
    """ 以表格形式格式化输出批量数据结果，输出结果的格式和内容由columns，headers，formatter等参数控制，
        输入的数据包括多组同样结构的数据，输出时可以选择以统计结果的形式输出或者以表格形式输出，也可以同时
        以统计结果和表格的形式输出

    :param result:
    :param columns:
    :param headers:
    :param formatter:
    :return:
    """
    result = pd.DataFrame(result)
    first_res = result.iloc[0]
    ref_rtn, ref_annual_rtn = first_res['ref_rtn'], first_res['ref_annual_rtn']
    print(f'\n'
          f'==================================== \n'
          f'|                                  |\n'
          f'|       OPTIMIZATION RESULT        |\n'
          f'|                                  |\n'
          f'====================================')
    print(f'\nqteasy running mode: 2 - Strategy Parameter Optimization\n')
    print(f'investment starts on {first_res["loop_start"]}\nends on {first_res["loop_end"]}\n'
          f'Total looped periods: {result.years[0]:.1f} years.')
    print(f'total investment amount: ¥{result.total_invest[0]:13,.2f}')
    print(f'Reference index type is {config.reference_asset} at {config.ref_asset_type}\n'
          f'Total reference return: {ref_rtn :.2%} \n'
          f'Average Yearly reference return rate: {ref_annual_rtn:.2%}')
    print(f'statistical analysis of optimal strategy messages indicators: \n'
          f'total return:        {result.rtn.mean():.2%} ±'
          f' {result.rtn.std():.2%}\n'
          f'annual return:       {result.annual_rtn.mean():.2%} ±'
          f' {result.annual_rtn.std():.2%}\n'
          f'alpha:               {result.alpha.mean():.3f} ± {result.alpha.std():.3f}\n'
          f'Beta:                {result.beta.mean():.3f} ± {result.beta.std():.3f}\n'
          f'Sharp ratio:         {result.sharp.mean():.3f} ± {result.sharp.std():.3f}\n'
          f'Info ratio:          {result["info"].mean():.3f} ± {result["info"].std():.3f}\n'
          f'250 day volatility:  {result.volatility.mean():.3f} ± {result.volatility.std():.3f}\n'
          f'other messages indicators are listed in below table\n')
    # result.sort_values(by='final_value', ascending=False, inplace=True)
    print(result.to_string(columns=["par",
                                    "sell_count",
                                    "buy_count",
                                    "total_fee",
                                    "final_value",
                                    "rtn",
                                    "ref_rtn",
                                    "mdd"],
                           header=["Strategy items",
                                   "Sell-outs",
                                   "Buy-ins",
                                   "Total fee",
                                   "Final value",
                                   "ROI",
                                   "Reference return",
                                   "MDD"],
                           formatters={'total_fee':   '{:,.2f}'.format,
                                       'final_value': '{:,.2f}'.format,
                                       'rtn':         '{:.1%}'.format,
                                       'mdd':         '{:.1%}'.format,
                                       'ref_rtn':     '{:.1%}'.format,
                                       'sell_count':  '{:.1f}'.format,
                                       'buy_count':   '{:.1f}'.format},
                           justify='center'))
    print(f'\n===========END OF REPORT=============\n')