# coding=utf-8
# ======================================
# File:     visual.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-08-23
# Desc:
#   Functions for visual output and
#   effects.
# ======================================

import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

import pandas as pd
import numpy as np

import qteasy
from .history import get_history_panel
from .utilfuncs import sec_to_duration, list_to_str_format, match_ts_code, TIME_FREQ_STRINGS
from .tafuncs import macd, dema, rsi, bbands, ma

from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()

ValidCandlePlotIndicators = ['macd',
                             'dema',
                             'rsi']

ValidCandlePlotMATypes = ['ma',
                          'ema'
                          'bb',
                          'bbands']

ValidPlotTypes = ['candle', 'renko', 'ohlc', 'line']

title_font = {'fontname': 'pingfang HK',
              'size':     '16',
              'color':    'black',
              'weight':   'bold',
              'va':       'bottom',
              'ha':       'center'}
large_red_font = {'fontname': 'Arial',
                  'size':     '22',
                  'color':    'red',
                  'weight':   'bold',
                  'va':       'bottom'}
large_green_font = {'fontname': 'Arial',
                    'size':     '22',
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
    """ 一个动态交互式图表类，基于matplotlib和mplfinance实现

    在合适的backend显示时，支持以下鼠标及键盘交互操作：
    1, 鼠标点击K线图区域，左右拖放平移K线图
    2, 鼠标滚轮在K线图区域滚动，放大或缩小K线图的显示范围
    3, 鼠标双击K线图区域，切换不同的均线类型：移动平均及布林带线
    4, 鼠标在指标图区域双击，切换不同的指标类型：macd、rsi、dema等
    5, 按键盘左右键平移K线图
    6, 按键盘上下键放大或缩小K线图的显示范围
    7, 按键盘a键切换不同的指标类型

    """

    def __init__(self, data, title_info, plot_type, style, avg_type, indicator):
        """ 初始化动态图表对象，初始化属性

        Parameters
        ----------
        data: np.array
            需要显示的数据
        title_info: str
            需要显示的图表标题以及指标显示信息
        plot_type: str, {'candle', 'renko', 'ohlc', 'line'}
            K线图类型： candle 蜡烛图， ohlc: K线图，
        style: dict of table style
            一个图表style对象，确定K线图或蜡烛图的颜色风格
        avg_type: str, {'ma', 'bb', 'bbands'}
            均线类型： ma：移动平均线，bb / bbands：布林带线
        indicator: str, {'macd', 'rsi', 'dema'}
            指标类型：macd，rsi，dema
        """
        self.pressed = False
        self.xpress = None

        if not isinstance(data, pd.DataFrame):
            raise TypeError(f'data should be a DataFrame, got {type(data)} instead.')
        if not all(must_col in data.columns for must_col in ['open', 'close', 'high', 'low']):
            raise KeyError(f'data does not contain proper data - at least all columns in '
                           f'["open", "high", "low", "close"] should be in data')
        self.data = data
        if plot_type not in ValidPlotTypes:
            raise KeyError(f'Invalid plot type, plot type should be one of {ValidPlotTypes}')
        self.plot_type = plot_type
        self.style = style
        # title_info是一个用"/"分隔的字符串，包含以下信息：title, mav, bb_par, macd_par, rsi_par, dema_par
        self.plot_title, self.mav, self.bb_par, self.macd_par, self.rsi_par, self.dema_par = \
            tuple(title_info.split('/'))
        # 设置初始化的K线图显示区间起点为0，即显示第0到第99个交易日的数据（前100个数据）
        self.idx_start = 0
        self.idx_range = 100
        # 设置ax1图表中显示的均线类型
        self.avg_type = avg_type.lower()
        self.indicator = indicator.lower()

        self.cur_xlim = None

        # 初始化figure对象，在figure上建立三个Axes对象并分别设置好它们的位置和基本属性
        self.fig = mpf.figure(style=style, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
        fig = self.fig
        self.ax1 = fig.add_axes([0.08, 0.25, 0.86, 0.60])
        self.ax1.set_xbound(0, 100)
        # self.ax1.set_xticklabels(data.index)
        self.ax2 = fig.add_axes([0.08, 0.15, 0.86, 0.10], sharex=self.ax1)
        self.ax2.set_ylabel('This is not Volume')
        self.ax3 = fig.add_axes([0.08, 0.05, 0.86, 0.10], sharex=self.ax1)
        # 初始化figure对象，在figure上预先放置文本并设置格式，文本内容根据需要显示的数据实时更新
        self.t1 = fig.text(0.50, 0.94, f'{self.plot_title}', **title_font)
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

        fig.canvas.mpl_connect('button_press_event', self.on_press)
        fig.canvas.mpl_connect('button_release_event', self.on_release)
        fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def refresh_plot(self, idx_start, idx_range):
        """ 根据最新的参数，重新绘制整个图表
        """
        from qteasy import logger_core
        ap = []
        # 添加K线图重叠均线，根据均线类型添加移动均线或布林带线
        plot_data = self.data.iloc[idx_start:idx_start + idx_range]
        ylabel = 'Price'
        if self.avg_type == 'ma':
            ylabel = 'Price, MA:' + self.mav
            ma_to_plot = [col for col in plot_data.columns if col[:2] == 'MA']
            ap.append(mpf.make_addplot(plot_data[ma_to_plot],
                                       ax=self.ax1))
        elif self.avg_type in ['bb', 'bbands']:
            ylabel = f'Price, BBands:{self.bb_par}'
            ap.append(mpf.make_addplot(plot_data[['bb-u', 'bb-m', 'bb-l']],
                                       ax=self.ax1))
        else:
            pass  # 不添加任何均线
        # 添加指标，根据指标类型添加MACD或RSI或DEMA
        if self.indicator == 'macd':
            ap.append(mpf.make_addplot(plot_data[['macd-m', 'macd-s']],
                                       ylabel=f'macd: \n{self.macd_par}',
                                       ax=self.ax3))
            bar_r = np.where(plot_data['macd-h'] > 0, plot_data['macd-h'], 0)
            bar_g = np.where(plot_data['macd-h'] <= 0, plot_data['macd-h'], 0)
            ap.append(mpf.make_addplot(bar_r, type='bar', color='red', ax=self.ax3))
            ap.append(mpf.make_addplot(bar_g, type='bar', color='green', ax=self.ax3))
        elif self.indicator == 'rsi':
            ap.append(mpf.make_addplot([75] * len(plot_data), color=(0.75, 0.6, 0.6), ax=self.ax3))
            ap.append(mpf.make_addplot([30] * len(plot_data), color=(0.6, 0.75, 0.6), ax=self.ax3))
            ap.append(mpf.make_addplot(plot_data['rsi'],
                                       ylabel=f'rsi: \n{self.rsi_par}',
                                       ax=self.ax3))
        else:  # indicator == 'dema'
            ap.append(mpf.make_addplot(plot_data['dema'],
                                       ylabel=f'dema: \n{self.dema_par}',
                                       ax=self.ax3))
        # 绘制图表
        # 如果一次显示的内容过多（self.idx_range >= 350)则显示线图
        plot_type = self.plot_type
        if idx_range >= 350:
            plot_type = 'line'
        if not plot_data.empty:
            mpf.plot(plot_data,
                     ax=self.ax1,
                     volume=self.ax2,
                     ylabel=ylabel,
                     addplot=ap,
                     type=plot_type,
                     style=self.style,
                     datetime_format='%y/%m/%d',
                     xrotation=0)
            self.fig.show()
        else:
            logger_core.warning(f'plot data is empty, plot will not be refreshed!')

    def refresh_texts(self, display_data):
        """ 更新K线图上的价格文本
        """
        # display_data是一个交易日内的所有数据，将这些数据分别填入figure对象上的文本中
        self.t3.set_text(f'{display_data["open"]:.2f} / {display_data["close"]:.2f}')
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

    def on_press(self, event):
        # 如果点击范围不在ax1或ax3范围内则退出
        if not (event.inaxes == self.ax1 or event.inaxes == self.ax3):
            return
        if event.button != 1:
            return
        self.pressed = True
        self.xpress = event.xdata
        self.cur_xlim = self.ax1.get_xlim()
        print(f'key pressed! cur_xlim is {self.cur_xlim}')

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
            if event.inaxes == self.ax3:
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
        data_length = len(self.data)
        self.idx_start -= dx
        if self.idx_start <= 0:
            self.idx_start = 0
        if self.idx_start >= data_length - self.idx_range:
            self.idx_start = data_length - self.idx_range

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
        if new_start >= len(self.data) - self.idx_range:
            new_start = len(self.data) - self.idx_range
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

    # 键盘按下处理
    def on_key_press(self, event):
        data_length = len(self.data)
        if event.key == 'a':  # avg_type, 在ma,bb,none之间循环
            if self.avg_type == 'ma':
                self.avg_type = 'bb'
            elif self.avg_type == 'bb':
                self.avg_type = 'none'
            elif self.avg_type == 'none':
                self.avg_type = 'ma'
        elif event.key == 'up':  # 向上，看仔细1倍
            if self.idx_range > 60:
                self.idx_range = self.idx_range // 2
        elif event.key == 'down':  # 向下，看多1倍标的
            if self.idx_range <= 480:
                self.idx_range = self.idx_range * 2
        elif event.key == 'left':
            if self.idx_start > self.idx_range // 2:
                self.idx_start = self.idx_start - self.idx_range // 2
        elif event.key == 'right':
            if self.idx_start < data_length - self.idx_range // 2:
                self.idx_start = self.idx_start + self.idx_range // 2
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.refresh_texts(self.data.iloc[self.idx_start])
        self.refresh_plot(self.idx_start, self.idx_range)


def candle(stock=None, start=None, end=None, stock_data=None, asset_type=None, freq=None, plot_type='candle',
           interactive=True, data_source=None, **kwargs):
    """ 获取股票或证券的K线数据，并显示股票的K线图

    Parameters
    ----------
    stock: str,
        简化证券代码、完整证券代码或股票名称，根据该代码或名称匹配准确的证券代码
        如果给出股票名称，支持使用%、？等通配符、支持模糊查找
        如果匹配到多个证券代码，将打印出提示，并选择第一个匹配的证券代码输出图表
    start: str, datetime, TimeStamp
        K线图的起始日期
    end: str, datetime, TimeStamp
        K线图的终止日期
    stock_data: pd.DataFrame
        直接用于K线图的数据，如果给出stock_data，则忽略其他的参数,否则使用其他参数从dataSource读取数据
    freq: str
        K线图的时间频率，合法输入包括：
        - D/d: 日K线
        - W/w: 周K线
        - M/m: 月K线
        - XMin/Xmin: 分钟K线，接受1min/5min/15min/30min/60min等五种输入
    asset_type: str
        证券类型，包含：
        - E:    股票
        - IDX:  指数
        - FD:   基金
        - FT:   期货
        - OPT:  期权
    plot_type: str
        输出图表的类型，包括以下选项
        - candle:   显示蜡烛图
        - ohlc:     显示OHLC K线图
        - renko:    显示RENKO图
        - none:     只返回数据，不显示图表
    interactive: Bool
        是否输出可交互式图表
        （受matplotlib的backend限制，某些环境下交互式图表不可用，详情请参见
        https://matplotlib.org/stable/users/explain/backends.html）
    data_source: DataSource Object
        历史数据源，默认使用qt内置的数据源QT_DATA_SOURCE
        否则使用给定的DataSource
    kwargs:
        用于传递至K线图的更多参数，包括：
        - adj:          str, 复权参数： none，back，forward
        - mav:          list, 移动均线周期
        - avg_type:     str, 均线类型，包括ma，bbands
        - indicator:    str, 指标类型，包括macd，rsi，dema
        - bb_par:       tuple, 布林带线参数
        - macd_par:     tuple, MACD参数
        - rsi_par:      tuple, RSI指标参数
        - dema_par:     tuple, DEMA指标参数

    Returns
    -------
    pd.DataFrame
        包含相应股票数据的DataFrame

    See Also
    --------
    更多介绍参见QTEASY文档
    """
    from qteasy import logger_core
    no_visual = False
    if not isinstance(plot_type, str):
        raise TypeError(f'plot type should be a string, got {type(plot_type)} instead.')
    if plot_type.lower() in ['candle', 'cdl', 'c']:
        plot_type = 'candle'
    elif plot_type.lower() in ['ohlc', 'o']:
        plot_type = 'ohlc'
    elif plot_type.lower() in ['renko', 'r']:
        plot_type = 'renko'
    elif plot_type.lower() in ['line', 'l']:
        plot_type = 'line'
    elif plot_type.lower() in ['none', 'n']:
        plot_type = 'none'
        no_visual = True
    else:
        raise KeyError(f'Invalid plot type: {plot_type}')

    matched_codes = []
    if stock is not None:
        if not isinstance(stock, str):
            raise TypeError(f'stock should be a string, got {type(stock)} instead.')
        stock_part = len(stock.split('.'))
        if stock_part > 2:
            raise KeyError(f'invalid stock code or name {stock}, please check your input.')
        elif stock_part == 1:
            code_matched = match_ts_code(stock)
            match_count = code_matched['count']
            if match_count == 0:
                logger_core.warning(f'Can not find a matched ts_code with "{stock}", plotting will be canceled')
                return
            elif match_count >= 1:
                if asset_type is None:
                    matched_asset_types = []
                    for atype in code_matched:
                        if atype == 'count':
                            continue
                        if len(code_matched[atype]) >= 1:
                            matched_codes.extend(code_matched[atype])
                            matched_asset_types.append(atype)
                    asset_type = matched_asset_types[0]
                else:
                    if asset_type not in code_matched.keys():
                        logger_core.warning(f'can not find a matched ts_code with "{stock}" in asset type '
                                            f'"{asset_type}", plotting will be canceled')
                        return
                    matched_codes.extend(code_matched[asset_type])
            else:
                raise RuntimeError(f'Unknown Error: got code_matched: {code_matched}')
            if len(matched_codes) > 1:
                logger_core.info(f'More than one matching code is found with input ({stock}):\n'
                                    f'{code_matched}\n'
                                    f'\nonly the first will be used to plot.')
        elif stock_part == 2:
            matched_codes.append(stock)
        else:
            raise RuntimeError(f'Unknown Error, got invalid stock {stock}')
    if asset_type is None:
        asset_type = 'E'
    if len(matched_codes) == 0:
        stock = None
    else:
        stock = matched_codes[0]
    if not interactive:
        pass
    return _mpf_plot(stock_data=stock_data, stock=stock, start=start, end=end, freq=freq,
                     asset_type=asset_type, plot_type=plot_type, no_visual=no_visual, data_source=data_source,
                     **kwargs)


def _mpf_plot(stock_data=None, share_name=None, stock=None, start=None, end=None, freq=None,
              asset_type=None, plot_type=None, no_visual=False, mav=None, avg_type='ma', indicator=None,
              data_source=None, **kwargs):
    """plot stock data or extracted data in renko form
    """
    from qteasy import logger_core
    freq_info = '日K线'
    adj = 'none'
    adj_info = ''
    multiplier = 1
    if plot_type is None:
        plot_type = 'candle'
    if freq is None:
        freq = 'd'
    assert isinstance(freq, str), f'freq should be a string, got {type(freq)} instead.'
    assert freq.upper() in TIME_FREQ_STRINGS, f'freq should be a string in {TIME_FREQ_STRINGS}'
    if freq.upper() in ['W']:
        multiplier = 5
        freq_info = '周K线'
    elif freq.upper() in ['M']:
        multiplier = 30
        freq_info = '月K线'
    elif freq.upper() in ['H']:
        multiplier = 0.2
        freq_info = '小时K线'
    elif freq.upper() in ['MIN', '1MIN']:
        multiplier = 1 / 240
        freq_info = '分钟K线'
    elif freq.upper() in ['5MIN']:
        multiplier = 1 / 48
        freq_info = '5分钟K线'
    elif freq.upper() in ['15MIN']:
        multiplier = 1 / 16
        freq_info = '15分钟K线'
    elif freq.upper() in ['30MIN']:
        multiplier = 1 / 8
        freq_info = '30分钟K线'
    if end is None:
        now = pd.to_datetime('today')
        if now.hour >= 23:
            end = pd.to_datetime('today')
        else:
            end = pd.to_datetime('today') - pd.Timedelta(1, 'd')
    if start is None:
        start = end - pd.Timedelta(60 * multiplier, 'd')
    if mav is None:
        mav = [5, 10, 20, 60]
    end = pd.to_datetime(end)
    if freq.upper()[-3:] in ['MIN', 'H']:
        # 如果频率为分钟级别，则：
        # 设置end为当天的14:59:59，以确保频率为分钟时也能准确定位到当天15:00的最后一个交易时段
        end += pd.Timedelta(899.5, 'm')
    start = pd.to_datetime(start)
    # 当stock_data没有给出时，则从本地获取股票数据
    if stock_data is None:
        assert stock is not None
        if ('adj' in kwargs) and (asset_type.upper() in ['E', 'FD']):
            adj = kwargs['adj']
        try:
            daily, share_name = _get_mpf_data(data_source=data_source,
                                              stock=stock,
                                              asset_type=asset_type,
                                              freq=freq,
                                              adj=adj)
        except Exception as e:
            print(f'{e}')
            return
        if daily.empty:
            logger_core.warning(f'history data for {stock} can not be found!')
            return
    else:
        daily = stock_data
        if share_name is None:
            share_name = 'stock'

    if share_name[-1] == 'O':
        # 如果绘制场外基金的净值图，则设置图表类型为'line'，此时不会
        # 显示K线图，只显示曲线图, 同时，不显示移动均线
        share_name = share_name[:-1]
        plot_type = 'line'
        freq_info = '净值曲线'
        # mav = []
    if adj.lower() in ['n', 'none']:
        adj_info = '未复权'
    elif adj.lower() in ['b', 'back']:
        adj_info = '后复权'
    elif adj.lower() in ['f', 'fw', 'forward']:
        adj_info = '前复权'
    else:
        raise ValueError(f'Invalid adjust type: {adj}.')
    assert isinstance(daily, pd.DataFrame), f'stock data is not a DataFrame, got {type(daily)}'
    assert all(col in daily.columns for col in ['open', 'high', 'low', 'close']), \
        f"price data missing, can not find " \
        f"{[col for col in ['open', 'high', 'low', 'close'] if col not in daily.columns]}"
    # 如果给出或获取的数据没有volume列，则生成空数据列
    if 'volume' not in daily.columns:
        daily['volume'] = 0
    # 处理并生成indicator
    if indicator is None:
        indicator = 'macd'
    if indicator not in ValidCandlePlotIndicators + ValidCandlePlotMATypes:
        raise KeyError(f'Invalid indicator: ({indicator})')
    daily, parameters = _add_indicators(daily,
                                        mav=mav,
                                        **kwargs)

    my_color = mpf.make_marketcolors(up='r',
                                     down='g',
                                     edge='inherit',
                                     wick='inherit',
                                     volume='inherit')
    my_style = mpf.make_mpf_style(marketcolors=my_color,
                                  figcolor='(0.82, 0.83, 0.85)',
                                  gridcolor='(0.82, 0.83, 0.85)')
    # 设置plot title info
    plot_title_info = f'{share_name}-{freq_info}-{adj_info}/{parameters}'
    if not no_visual:
        idx_start = np.searchsorted(daily.index, start)
        idx_range = np.searchsorted(daily.index, end) - idx_start
        # 当end太靠后时，产生的range会越界，因此需要判断是否越界，如果越界则重设range
        if idx_range + idx_start >= len(daily.index):
            idx_range = len(daily.index) - idx_start - 1
        my_candle = InterCandle(data=daily,
                                title_info=plot_title_info,
                                plot_type=plot_type,
                                style=my_style,
                                avg_type=avg_type,
                                indicator=indicator)
        logger_core.info(f'Creating plot with data starts {idx_start} to {idx_start + idx_range}')
        my_candle.refresh_texts(daily.iloc[idx_start + idx_range])
        my_candle.refresh_plot(idx_start, idx_range + 1)
        # 如果需要动态图表，需要传入特别的参数以进入交互模式
        dynamic = False
        if dynamic:
            raise NotImplementedError
    return daily


def _get_mpf_data(stock, asset_type=None, adj='none', freq='d', data_source=None):
    """ 返回一只股票在全部历史区间上的价格数据，生成一个pd.DataFrame. 包含open, high, low, close, volume 五组数据
        并返回股票的名称。

    Parameters
    ----------
    stock: 股票代码
    asset_type: 资产类型，E——股票，F——期货，FD——基金，IDX——指数, OPT——期权
    adj: 是否复权，none——不复权，hfq——后复权，qfq——前复权
    freq: 价格周期，d——日K线，5min——五分钟k线
    data_source: 获取数据的数据源

    Returns
    -------
    tuple：(pd.DataFrame, share_name)
    """
    # 首先获取股票的上市日期，并获取从上市日期开始到现在的所有历史数据
    name_of = {'E':   'Stock 股票',
               'IDX': 'Index 指数',
               'FT':  'Futures 期货',
               'FD':  'Fund 基金',
               'OPT': 'Options 期权'}
    ds = qteasy.QT_DATA_SOURCE
    if asset_type.upper() == 'E':
        basic_info = ds.read_table_data('stock_basic')
    elif asset_type.upper() == 'IDX':
        # 获取指数的基本信息
        basic_info = ds.read_table_data('index_basic')
    elif asset_type.upper() == 'FT':
        # 获取期货的基本信息
        basic_info = ds.read_table_data('future_basic')
    elif asset_type.upper() == 'FD':
        # 获取基金的基本信息
        basic_info = ds.read_table_data('fund_basic')
    elif asset_type.upper() == 'OPT':
        # 获取基金的基本信息
        # basic_info = ds.read_table_data('opt_basic')
        raise NotImplementedError(f'Candle plot for asset type: "{asset_type}" is not supported at the moment')
    else:
        raise KeyError(f'Wrong asset type: "{asset_type}"')
    if basic_info.empty:
        raise ValueError(f'Can not load basic information for asset type: "{name_of[asset_type]}" from data source '
                         f'"{ds.connection_type}". \n'
                         f'use "datasource.refill_data_source(tables=\'basics\')" to download basic information')
    try:
        this_stock = basic_info.loc[stock]
    except Exception as e:
        raise ValueError(f'{e}, data not found for "{stock}" in asset type "{name_of[asset_type]}" '
                         f'from data source {ds.connection_type}, please check if asset type is correct.')

    if this_stock.empty:
        raise KeyError(f'Can not find historical data for asset "{stock}" of type "{name_of[asset_type]}" '
                       f'from data source "{ds.connection_type}"\n'
                       f'please check stock code')
    # 设置历史数据获取区间的开始日期为股票上市第一天
    l_date = this_stock.list_date
    if l_date is None:
        start_date = '2000-01-01'
    else:
        start_date = pd.to_datetime(l_date).strftime('%Y-%m-%d')
    # 设置历史数据获取最后一天，只有现在的时间在23:00以后时才设置为今天，否则就设置为昨天
    now = pd.to_datetime('today')
    if now.hour >= 23 and now.weekday() < 5:
        end = pd.to_datetime('today')
    else:
        end = pd.to_datetime('today') - pd.Timedelta(now.weekday() - 4, 'd')
    end_date = end.strftime('%Y-%m-%d')
    name = this_stock['name']
    if (asset_type.upper() == 'FD') and (this_stock['market'] == 'O'):
        if adj.lower() not in ('n', 'none'):
            htypes = 'adj_nav'
        else:
            htypes = 'accum_nav'
    else:
        htypes = 'close,high,low,open,vol'
    # fullname = this_stock.fullname.values[0]
    # 读取该股票从上市第一天到今天的全部历史数据，包括ohlc和volume数据
    data = get_history_panel(htypes=htypes, shares=stock, start=start_date, end=end_date, freq=freq,
                             asset_type=asset_type, adj=adj, data_source=data_source,
                             resample_method='none').slice_to_dataframe(share=stock)
    # 如果读取的是nav净值，将nav改为close，并填充open/high/low三列为NaN值
    is_out_fund = False
    if 'open' not in data.columns:
        data.columns = ['close']
        data['open'] = np.nan
        data['high'] = np.nan
        data['low'] = np.nan
        is_out_fund = True
    # 虽然比较罕见，但是存在这样的情况，当某日的交易量为0时，当天数据中open/high/low价格均为NaN，
    # 此时应该将open/high/low三者的价格设置为与close一致，否则无法显示K线图
    for col in ['open', 'high', 'low']:
        col_data = data[col]
        if np.isnan(col_data.values).any():
            col_data.loc[pd.isna(col_data)] = data.close

    # 返回股票的名称和全称
    share_name = stock + ' - ' + name + ' [' + name_of[asset_type] + '] '
    if is_out_fund:
        share_name += 'O'
    data.rename({'vol': 'volume'}, axis='columns', inplace=True)
    return data, share_name


def _add_indicators(data, mav=None, bb_par=None, macd_par=None, rsi_par=None, dema_par=None, **kwargs):
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

    Parameters
    ----------
    data : DataFrame
        一只股票的历史K线数据，包括O/H/L/C/V五组数据或者O/H/L/C四组数据

    Returns
    -------
    tuple: (data, parameter_string)
        (pd.DataFrame, str) 添加指标的价格数据表，所有指标的参数字符串，以"/"分隔
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
    # 在DataFrame中增加均线信息,并先删除已有的均线：
    assert isinstance(mav, (list, tuple))
    assert all(isinstance(item, int) for item in mav)
    mav_to_drop = [col for col in data.columns if col[:2] == 'MA']
    if len(mav_to_drop) > 0:
        data.drop(columns=mav_to_drop, inplace=True)
    # 排除close收盘价中的nan值：
    close = data.close.iloc[np.where(~np.isnan(data.close))]

    for value in mav:  # 需要处理数据中的nan值，否则会输出全nan值
        data['MA' + str(value)] = ma(close, timeperiod=value)  # 以后还可以加上不同的ma_type
    data['change'] = np.round(close - close.shift(1), 3)
    data['pct_change'] = np.round(data['change'] / close * 100, 2)
    data['value'] = np.round(data['close'] * data['volume'] / 1000000, 2)
    data['upper_lim'] = np.round(data['close'] * 1.1, 3)
    data['lower_lim'] = np.round(data['close'] * 0.9, 3)
    data['last_close'] = data['close'].shift(1)
    data['average'] = data[['open', 'close', 'high', 'low']].mean(axis=1)
    data['volrate'] = data['volume']
    # 添加不同的indicator
    data['dema'] = dema(close, *dema_par)
    data['macd-m'], data['macd-s'], data['macd-h'] = macd(close, *macd_par)
    data['rsi'] = rsi(close, *rsi_par)
    data['bb-u'], data['bb-m'], data['bb-l'] = bbands(close, *bb_par)

    parameter_string = f'{mav}/{bb_par}/{macd_par}/{rsi_par}/{dema_par}'

    return data, parameter_string


def _plot_loop_result(loop_results: dict, config):
    """ 以图表的形式输出回测结果。"""
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
    fixed_column_items = ['fee', 'cash', 'value', 'reference', 'ref', 'ret',
                          'invest', 'underwater', 'volatility', 'pct_change',
                          'beta', 'sharp', 'alpha']
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
    position = 1 - (looped_values['cash'] / looped_values['value'])
    beta = looped_values['beta']
    alpha = looped_values['alpha']
    volatility = looped_values['volatility']
    sharp = looped_values['sharp']
    underwater = looped_values['underwater']
    drawdowns = loop_results['worst_drawdowns']
    # 回测结果和参考指数的总体回报率曲线
    return_rate = (looped_values.value - start_point) / start_point * 100
    ref_rate = (looped_values.reference - ref_start) / ref_start * 100
    # 将benchmark的起始资产总额调整到与回测资金初始值一致，一遍生成可以比较的benchmark资金曲线
    # 这个资金曲线用于显示"以对数比例显示的资金变化曲线"图
    adjusted_bench_start = looped_values.reference / ref_start * start_point

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
    fig = plt.figure(figsize=(12, 15), facecolor=(0.82, 0.83, 0.85))
    ax1 = fig.add_axes([0.05, 0.67, chart_width, 0.20])
    ax2 = fig.add_axes([0.05, 0.57, chart_width, 0.08], sharex=ax1)
    ax3 = fig.add_axes([0.05, 0.49, chart_width, 0.06], sharex=ax1)
    ax4 = fig.add_axes([0.05, 0.41, chart_width, 0.06], sharex=ax1)
    ax5 = fig.add_axes([0.05, 0.33, chart_width, 0.06], sharex=ax1)
    ax6 = fig.add_axes([0.05, 0.25, chart_width, 0.06], sharex=ax1)
    ax7 = fig.add_axes([0.02, 0.04, 0.38, 0.16])
    ax8 = fig.add_axes([0.43, 0.04, 0.15, 0.16])
    ax9 = fig.add_axes([0.64, 0.04, 0.29, 0.16])
    if isinstance(config.asset_pool, str):
        title_asset_pool = config.asset_pool
    else:
        if len(config.asset_pool) > 3:
            title_asset_pool = list_to_str_format(config.asset_pool[:3]) + '...'
        else:
            title_asset_pool = list_to_str_format(config.asset_pool)
    fig.suptitle(f'Back Testing Result {title_asset_pool} - benchmark: {config.benchmark_asset}',
                 fontsize=14,
                 fontweight=10)
    # 投资回测结果的评价指标全部被打印在图表上，所有的指标按照表格形式打印
    # 为了实现表格效果，指标的标签和值分成两列打印，每一列的打印位置相同
    fig.text(0.07, 0.955, f'periods: {loop_results["years"]:3.1f} years, '
                          f'from: {loop_results["loop_start"].date()} to {loop_results["loop_end"].date()}       '
                          f'  time consumed:   signal creation: {sec_to_duration(loop_results["op_run_time"])};'
                          f'  back test:{sec_to_duration(loop_results["loop_run_time"])}')
    fig.text(0.21, 0.90, f'Operation summary:\n\n'
                         f'Total op fee:\n'
                         f'total investment:\n'
                         f'final value:', ha='right')
    fig.text(0.23, 0.90, f'{loop_results["oper_count"].buy.sum():.0f}     buys \n'
                         f'{loop_results["oper_count"].sell.sum():.0f}     sells\n'
                         f'¥{loop_results["total_fee"]:13,.2f}\n'
                         f'¥{loop_results["total_invest"]:13,.2f}\n'
                         f'¥{loop_results["final_value"]:13,.2f}')
    fig.text(0.50, 0.90, f'Cumulative return:\n'
                         f'Avg annual return:\n'
                         f'Benchmark return:\n'
                         f'Avg annual ref return:\n'
                         f'Max drawdown:', ha='right')
    fig.text(0.52, 0.90, f'{loop_results["rtn"]:3.2%}    \n'
                         f'{loop_results["annual_rtn"]:3.2%}    \n'
                         f'{loop_results["ref_rtn"]:3.2%}    \n'
                         f'{loop_results["ref_annual_rtn"]:3.2%}\n'
                         f'{loop_results["mdd"]:3.1%}'
                         f' on {loop_results["valley_date"].date()}')
    fig.text(0.82, 0.90, f'alpha:\n'
                         f'Beta:\n'
                         f'Sharp ratio:\n'
                         f'Info ratio:\n'
                         f'250-day volatility:', ha='right')
    fig.text(0.84, 0.90, f'{loop_results["alpha"]:.3f}  \n'
                         f'{loop_results["beta"]:.3f}  \n'
                         f'{loop_results["sharp"]:.3f}  \n'
                         f'{loop_results["info"]:.3f}  \n'
                         f'{loop_results["volatility"]:.3f}')

    # 绘制基准数据的收益率曲线图
    ax1.set_title('cum-return, benchmark and history operations')
    ax1.plot(looped_values.index, ref_rate, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='Benchmark')

    # 绘制回测结果的收益率曲线图
    ax1.plot(looped_values.index, return_rate, linestyle='-',
             color=(0.8, 0.2, 0.0), alpha=0.85, label='Return')
    ax1.set_ylabel('Cumulative Return')
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
                # 用不同深浅的绿色填充多头区间, 0 < long_short < 1
                if long_short > 1:
                    long_short = 1
                ax1.axvspan(first, second,
                            facecolor=((1 - 0.6 * long_short), (1 - 0.4 * long_short), (1 - 0.8 * long_short)),
                            alpha=0.2)
            else:
                # 用不同深浅的红色填充空头区间, -1 < long_short < 0
                if long_short < -1:
                    long_short = -1
                ax1.axvspan(first, second,
                            facecolor=((1 + 0.2 * long_short), (1 + 0.8 * long_short), (1 + long_short)),
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

    # 使用箭头标记最大回撤区间，箭头从最高起点开始，指向最低点，第二个箭头从最低点开始，指向恢复点
    ax1.annotate(f"{loop_results['peak_date'].date()}",
                 xy=(loop_results["valley_date"], return_rate[loop_results["valley_date"]]),
                 xycoords='data',
                 xytext=(loop_results["peak_date"], return_rate[loop_results["peak_date"]]),
                 textcoords='data',
                 arrowprops=dict(width=1, headwidth=3, facecolor='black', shrink=0.),
                 ha='right',
                 va='bottom')
    if pd.notna(loop_results["recover_date"]):
        ax1.annotate(f"-{loop_results['mdd']:.1%}\n{loop_results['valley_date'].date()}",
                     xy=(loop_results["recover_date"], return_rate[loop_results["recover_date"]]),
                     xycoords='data',
                     xytext=(loop_results["valley_date"], return_rate[loop_results["valley_date"]]),
                     textcoords='data',
                     arrowprops=dict(width=1, headwidth=3, facecolor='black', shrink=0.),
                     ha='right',
                     va='top')
    else:
        ax1.text(x=loop_results["valley_date"],
                 y=return_rate[loop_results["valley_date"]],
                 s=f"-{loop_results['mdd']:.1%}\nnot recovered",
                 ha='right',
                 va='top')
    ax1.legend()

    # 绘制参考数据的收益率曲线图
    ax2.set_title('Benchmark and Cumulative Return in Logarithm Scale')
    ax2.plot(looped_values.index, adjusted_bench_start, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='Benchmark')

    # 绘制回测结果的收益率曲线图
    ax2.plot(looped_values.index, looped_values.value, linestyle='-',
             color=(0.8, 0.2, 0.0), alpha=0.85, label='Cum Value')
    ax2.set_ylabel('Cumulative Return\n in logarithm scale')
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax2.set_yscale('log')
    ax2.legend()

    ax3.set_title('Return Values')
    ax3.bar(looped_values.index, ret)
    ax3.set_ylabel('Return')

    ax4.set_title('Portfolio Profitability Indicators - Sharp and Alpha')
    ax4.plot(looped_values.index, sharp, label='sharp')
    ax4.plot(looped_values.index, alpha, label='alpha')
    ax4.set_ylabel('Profitability')
    ax4.legend()

    ax5.set_title('Portfolio Risk Exposure - Volatility and Beta')
    ax5.plot(looped_values.index, beta, label='beta')
    ax5.plot(looped_values.index, volatility, label='volatility')
    ax5.set_ylabel('Risk Exposure')
    ax5.legend()

    # 绘制underwater图（drawdown可视化图表）
    ax6.set_title('Drawdown Analysis - 5 Worst Drawdowns in History')
    ax6.plot(underwater, label='underwater')
    ax6.set_ylabel('Max Drawdown')
    ax6.set_xlabel('date')
    ax6.set_ylim(-1, 0)
    ax6.fill_between(looped_values.index, 0, underwater,
                     where=underwater < 0,
                     facecolor=(0.8, 0.2, 0.0), alpha=0.35)
    dd_starts = drawdowns['peak_date'].values
    dd_ends = drawdowns['recover_date'].values
    dd_valley = drawdowns['valley_date'].values
    dd_value = drawdowns['drawdown'].values
    for start, end, valley, dd in zip(dd_starts, dd_ends, dd_valley, dd_value):
        if np.isnan(end):
            end = looped_values.index[-1]
        ax6.axvspan(start, end,
                    facecolor='grey',
                    alpha=0.3)
        if dd > -0.6:
            ax6.text(x=valley,
                     y=dd - 0.05,
                     s=f"-{dd:.1%}\n",
                     ha='center',
                     va='top')
        else:
            ax6.text(x=valley,
                     y=dd + 0.15,
                     s=f"-{dd:.1%}\n",
                     ha='center',
                     va='bottom')

    # 绘制收益率热力图
    monthly_return_df = loop_results['return_df'][['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
    return_years = monthly_return_df.index
    return_months = monthly_return_df.columns
    return_values = monthly_return_df.values
    c = ax7.imshow(return_values, cmap='RdYlGn')
    ax7.set_title('Monthly Return Heat Map')
    ax7.set_xticks(np.arange(len(return_months)))
    ax7.set_yticks(np.arange(len(return_years)))
    ax7.set_xticklabels(return_months, rotation=45)
    ax7.set_yticklabels(return_years)
    base_aspect_ratio = 0.72
    if len(return_years) <= 12:
        aspect_ratio = base_aspect_ratio
    else:
        aspect_ratio = base_aspect_ratio * 12 / len(return_years)
    ax7.set_aspect(aspect_ratio)
    ax7.grid(False)
    fig.colorbar(c, ax=ax7)

    # 绘制年度收益率柱状图
    y_cum = loop_results['return_df']['y-cum']
    y_count = len(return_years)
    pos_y_cum = np.where(y_cum >= 0, y_cum, 0)
    neg_y_cum = np.where(y_cum < 0, y_cum, 0)
    return_years = y_cum.index
    ax8.barh(np.arange(y_count), pos_y_cum, 1, align='center', facecolor='green', alpha=0.85)
    ax8.barh(np.arange(y_count), neg_y_cum, 1, align='center', facecolor='red', alpha=0.85)
    ax8.set_yticks(np.arange(y_count))
    ax8.set_ylim(y_count - 0.5, -0.5)
    ax8.set_yticklabels(list(return_years))
    ax8.set_title('Yearly Returns')
    ax8.grid(False)

    # 绘制月度收益率Histo直方图
    ax9.set_title('Monthly Return Histo')
    ax9.hist(monthly_return_df.values.flatten(), bins=18, alpha=0.5,
             label='monthly returns')
    ax9.grid(False)

    # 设置所有图表的基本格式:
    for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
        ax.yaxis.tick_right()
        ax.xaxis.set_ticklabels([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.grid(True)

    # 调整主图表的日期格式
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
    # 前五个主表的时间轴共享，因此只需要设置最下方表的时间轴即可
    ax6.xaxis.set_major_locator(major_locator)
    ax6.xaxis.set_major_formatter(major_formatter)
    ax6.xaxis.set_minor_locator(minor_locator)
    ax6.xaxis.set_minor_formatter(minor_formatter)
    # 隐藏除ax6以外的其他ax的ticklabel, 因为ax1到ax6共享xaxis，因此不能用：
    # ax1.xaxis.set_ticklabels([])
    for ax in [ax1, ax2, ax3, ax4, ax5]:
        plt.setp(ax.get_xticklabels(), visible=False)

    plt.show()


# TODO: like _print_test_result, take the evaluate results on both opti and test hist data
#  and commit comparison base on these two data sets
def _plot_test_result(opti_eval_res: list,
                      test_eval_res: list = None,
                      config=None):
    """ 输出优化后参数的测试结果

    Parameters
    ----------
    opti_eval_res : list
        优化后参数的测试结果
    test_eval_res : list optional
        测试结果
    config : dict optional
        配置参数

    Returns
    -------
    None
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
                         f'  signal creation: {sec_to_duration(valid_opti_eval_res[0]["op_run_time"])};'
                         f'  back test:{sec_to_duration(valid_opti_eval_res[0]["loop_run_time"])}\n'
                         f'test periods: {valid_test_eval_res[0]["years"]:.1f} years, '
                         f'from: {valid_test_eval_res[0]["loop_start"].date()} to '
                         f'{valid_test_eval_res[0]["loop_end"].date()}  '
                         f'time consumed:'
                         f'  signal creation: {sec_to_duration(valid_test_eval_res[0]["op_run_time"])};'
                         f'  back test:{sec_to_duration(valid_test_eval_res[0]["loop_run_time"])}')

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
                opti_v = opti_indicator_df[name].fillna(np.nan)
                test_v = test_indicator_df[name].fillna(np.nan)
                if p_type == 0 or p_type == 'errorbar':
                    max_v = np.nanmax(opti_v)
                    min_v = np.nanmin(opti_v)
                    mean = np.nanmean(opti_v)
                    std = np.nanstd(opti_v)
                    ax.errorbar(1, mean, std, fmt='ok', lw=3)
                    ax.errorbar(1, mean, np.array(mean - min_v, max_v - mean).T, fmt='.k', ecolor='red', lw=1,
                                label=opti_label)
                    max_v = np.nanmax(test_v)
                    min_v = np.nanmin(test_v)
                    mean = np.nanmean(test_v)
                    std = np.nanstd(test_v)
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
                    if not (all(pd.isna(opti_v)) and all(pd.isna(test_v))):
                        ax.scatter(opti_v, test_v,
                                   label=name, marker='^', alpha=0.9)
                    ax.set_title(opti_label)
                    ax.set_ylabel(test_label)
                    ax.legend()
                elif p_type == 2 or p_type == 'histo':
                    if not all(pd.isna(opti_v)):
                        ax.hist(opti_v, bins=15, alpha=0.5,
                                label=opti_label)
                    if not all(pd.isna(test_v)):
                        ax.hist(test_v, bins=15, alpha=0.5,
                                label=test_label)
                    ax.legend()
                elif p_type == 3 or p_type == 'violin':
                    if not (all(pd.isna(opti_v)) and all(pd.isna(test_v))):
                        data_df = pd.DataFrame(np.array([opti_v, test_v]).T,
                                               columns=[opti_label, test_label])
                    ax.violinplot(data_df)
                    labels = ['opti', 'test']
                    ax.set_xticks(np.arange(1, len(labels) + 1))
                    ax.set_xticklabels(labels)
                    ax.set_xlim(0.25, len(labels) + 0.75)
                    ax.legend()
                else:
                    if not (all(pd.isna(opti_v)) and all(pd.isna(test_v))):
                        data_df = pd.DataFrame(np.array([opti_v, test_v]).T,
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
    op_dates = operator.op_signal_hdate
    shares = operator.op_list_shares
    h_dates = history_data.hdates
    signal_type = operator.signal_type
    print(f'\n'
          f'      ====================================\n'
          f'      |                                  |\n'
          f'      |       OPERATION SIGNALS          |\n'
          f'      |                                  |\n'
          f'      ====================================\n')
    print(f'Operation list is created based on following strategy:\n{operator.strategies}\n'
          f'{operator.info()}')
    print(f'Operation list is created on history data: \n'
          f'starts:     {h_dates[0]}\n'
          f'end:        {h_dates[-1]}')
    print(f'time consumption for operate signal creation: {sec_to_duration(run_time_prepare_data)}\n')
    # print(f'Operation signals are generated on {op_dates[0]}\nends on {op_dates[-1]}\n'
    #       f'Total signals generated: {len(op_dates)}.')
    print(f'Operation signal for shares on {op_dates.date()}\n')
    print(f'---------Current Operation Instructions------------\n'
          f'         signal type: {operator.signal_type}\n'
          f'signals: \n{op_list}\n'
          f'Today\'s operation signal as following:\n')

    for share_idx in range(len(shares)):
        share = shares[share_idx]
        print(f'------share: {share}-----------:')
        signal = op_list
        for price_type_idx in range(operator.bt_price_type_count):
            # 根据信号类型解析信号含义
            current_signal = signal[price_type_idx]
            if signal_type == 'pt':  # 当信号类型为"PT"时，信号代表目标持仓仓位
                print(f'Hold {current_signal * 100}% of total investment value!')
            if signal_type == 'ps':  # 当信号类型为"PS"时，信号代表资产买入卖出比例
                if signal[price_type_idx] > 0:
                    print(f'Buy in with {current_signal * 100}% of total investment value!')
                elif signal[price_type_idx] < 0:
                    print(f'Sell out {-signal * 100}% of current on holding stock!')
            if signal_type == 'vs':  # 当信号类型为"PT"时，信号代表资产买入卖出数量
                if signal[price_type_idx] > 0:
                    print(f'Buy in with {current_signal} shares of total investment value!')
                elif signal[price_type_idx] < 0:
                    print(f'Sell out {-signal} shares of current on holding stock!')
    print(f'\n      ===========END OF REPORT=============\n')


def _print_loop_result(loop_results=None, columns=None, headers=None, formatter=None):
    """ 格式化打印输出单次回测的结果，根据columns、headers、formatter等参数选择性输出result中的结果
        确保输出的格式美观一致

    Parameters
    ----------
    loop_results: dict
        回测结果
    columns: list, optional, to be implemented
        输出的列名
    headers: list, optional, to be implemented
        输出的表头
    formatter: list, optional, to be implemented
        输出的格式化函数

    Returns
    -------
    None
    """
    if loop_results is None:
        return
    looped_values = loop_results['complete_values']
    print(f'\n'
          f'     ====================================\n'
          f'     |                                  |\n'
          f'     |       BACK TESTING RESULT        |\n'
          f'     |                                  |\n'
          f'     ====================================')
    print(f'\nqteasy running mode: 1 - History back testing\n'
          f'time consumption for operate signal creation: {sec_to_duration(loop_results["op_run_time"])}\n'
          f'time consumption for operation back looping:  {sec_to_duration(loop_results["loop_run_time"])}\n')
    print(f'investment starts on      {looped_values.index[0]}\n'
          f'ends on                   {looped_values.index[-1]}\n'
          f'Total looped periods:     {loop_results["years"]:.1f} years.')
    print(f'\n-------------operation summary:------------\n'
          f'Only non-empty shares are displayed, call \n'
          f'"loop_result["oper_count"]" for complete operation summary\n')
    op_summary = loop_results['oper_count']
    op_summary = op_summary.loc[op_summary['empty'] != 1.0]
    print(op_summary.to_string(columns=["sell",
                                        "buy",
                                        "total",
                                        "long",
                                        "short",
                                        "empty"],
                               header=["Sell Cnt",
                                       "Buy Cnt",
                                       "Total",
                                       "Long pct",
                                       "Short pct",
                                       "Empty pct"],
                               formatters={'sell':  '{:.0f}'.format,
                                           'buy':   '{:.0f}'.format,
                                           'total': '{:.0f}'.format,
                                           'long':  '{:.1%}'.format,
                                           'short': '{:.1%}'.format,
                                           'empty': '{:.1%}'.format},
                               justify='center',
                               max_rows=20), '\n')
    print(f'Total operation fee:     ¥{loop_results["total_fee"]:12,.2f}')
    print(f'total investment amount: ¥{loop_results["total_invest"]:12,.2f}\n'
          f'final value:              ¥{loop_results["final_value"]:12,.2f}')
    print(f'Total return:             {loop_results["rtn"]:13.2%} \n'
          f'Avg Yearly return:        {loop_results["annual_rtn"]:13.2%}\n'
          f'Skewness:                 {loop_results["skew"]:13.2f}\n'
          f'Kurtosis:                 {loop_results["kurtosis"]:13.2f}')
    print(f'Benchmark return:         {loop_results["ref_rtn"]:13.2%} \n'
          f'Benchmark Yearly return:  {loop_results["ref_annual_rtn"]:13.2%}')
    print(f'\n------strategy loop_results indicators------ \n'
          f'alpha:                    {loop_results["alpha"]:13.3f}\n'
          f'Beta:                     {loop_results["beta"]:13.3f}\n'
          f'Sharp ratio:              {loop_results["sharp"]:13.3f}\n'
          f'Info ratio:               {loop_results["info"]:13.3f}\n'
          f'250 day volatility:       {loop_results["volatility"]:13.3f}\n'
          f'Max drawdown:             {loop_results["mdd"]:13.2%} \n'
          f'    peak / valley:        {loop_results["peak_date"].date()} / {loop_results["valley_date"].date()}')
    if not pd.isna(loop_results['recover_date']):
        print(f'    recovered on:         {loop_results["recover_date"].date()}\n')
    else:
        print(f'    recovered on:         Not recovered!\n')
    print(f'===========END OF REPORT=============\n')


# TODO: like _plot_test_result, take the evaluate results on both opti and test hist data
#  and commit comparison base on these two data sets
def _print_test_result(result, config=None, columns=None, headers=None, formatter=None):
    """ 以表格形式格式化输出批量数据结果，输出结果的格式和内容由columns，headers，formatter等参数控制，
        输入的数据包括多组同样结构的数据，输出时可以选择以统计结果的形式输出或者以表格形式输出，也可以同时
        以统计结果和表格的形式输出

    Parameters
    ----------
    result: dict
        回测结果
    config: dict, optional
        输出的列名
    columns: list, optional, to be implemented
        输出的列名
    headers: list, optional, to be implemented
        输出的表头
    formatter: list, optional, to be implemented
        输出的格式化函数

    Returns
    -------
    None
    """
    result = pd.DataFrame(result)
    first_res = result.iloc[0]
    ref_rtn, ref_annual_rtn = first_res['ref_rtn'], first_res['ref_annual_rtn']
    if config is None:
        from qteasy import QT_CONFIG
        config = QT_CONFIG

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
    print(f'Reference index type is {config.benchmark_asset} at {config.benchmark_asset_type}\n'
          f'Total Benchmark rtn: {ref_rtn :.2%} \n'
          f'Average Yearly Benchmark rtn rate: {ref_annual_rtn:.2%}')
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
                                   "ttl-fee",
                                   "FV",
                                   "ROI",
                                   "Benchmark rtn",
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