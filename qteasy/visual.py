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
import matplotlib.ticker as mtick

import pandas as pd
import numpy as np
from pandas.plotting import register_matplotlib_converters
import datetime
from .tsfuncs import get_bar, name_change
from .utilfuncs import time_str_format


# TODO: simplify and merge these three functions
def candle(stock=None, start=None, end=None, stock_data=None, share_name=None,
           asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    """plot stock data or extracted data in candle form"""
    return mpf_plot(stock_data=stock_data, share_name=share_name, stock=stock, start=start,
                    end=end, asset_type=asset_type, plot_type='candle',
                    no_visual=no_visual, figsize=figsize, mav=mav)


def ohlc(stock=None, start=None, end=None, stock_data=None, share_name=None,
         asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    """plot stock data or extracted data in ohlc form"""
    return mpf_plot(stock_data=stock_data, share_name=share_name, stock=stock, start=start,
                    end=end, asset_type=asset_type, plot_type='ohlc',
                    no_visual=no_visual, figsize=figsize, mav=mav)


def renko(stock=None, start=None, end=None, stock_data=None, share_name=None,
          asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    """plot stock data or extracted data in renko form"""
    return mpf_plot(stock_data=stock_data, share_name=share_name, stock=stock, start=start,
                    end=end, asset_type=asset_type, plot_type='renko',
                    no_visual=no_visual, figsize=figsize, mav=mav)


def mpf_plot(stock_data=None, share_name=None, stock=None, start=None, end=None,
             asset_type='E', plot_type=None, no_visual=False, **kwargs):
    """plot stock data or extracted data in renko form
    """
    assert plot_type is not None
    if stock_data is None:
        assert stock is not None
        daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
        has_volume = True
    else:
        assert isinstance(stock_data, pd.DataFrame)
        assert all(col in ['open', 'high', 'low', 'close', 'volume'] for col in stock_data.columns)
        daily = stock_data
        has_volume = any(col in ['volume'] for col in stock_data.columns)
        if share_name is None:
            share_name = 'stock'
    mc = mpf.make_marketcolors(up='r', down='g',
                               volume='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    if not no_visual:
        mpf.plot(daily,
                 title=share_name,
                 volume=has_volume,
                 type=plot_type,
                 style=s,
                 figscale=0.5,
                 **kwargs)
    return daily


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
    else:
        share_name = stock + ' - ' + asset_type
    # data.info()
    daily = data[['open', 'high', 'low', 'close', 'vol']]
    daily.columns = ['open', 'high', 'low', 'close', 'volume']
    daily.index = data['trade_date']
    daily = daily.rename(index=pd.Timestamp).sort_index()
    # manipulating of mpf:
    return daily, share_name


def _plot_loop_result(loop_results: dict, config):
    """plot the loop results in a fancy way that displays all information more clearly"""
    # prepare looped_values dataframe
    if not isinstance(loop_results, dict):
        raise TypeError('')
    looped_values = loop_results['complete_values']
    if looped_values.empty:
        raise ValueError()
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
    years_fmt = mdates.DateFormatter('%Y')

    chart_width = 0.88
    # 显示投资回报评价信息
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle('Back Testing Result - reference: 000300.SH', fontsize=14, fontweight=10)
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
                         f' on {loop_results["low_date"]}')
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
    # ax1.annotate("max_drawdown",
    #              xy=(loop_results["max_date"], return_rate[loop_results["low_date"]]),
    #              xytext=(0.7, 0.0),
    #              textcoords='axes fraction',
    #              arrowprops=dict(facecolor='black', shrink=0.3),
    #              horizontalalignment='right',
    #              verticalalignment='top')
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


# TODO: like _print_test_result, take the evaluate results on both opti and test hist data
# TODO: and commit comparison base on these two data sets
def _plot_test_result(opti_eval_res: list,
                      test_eval_res: list = None,
                      config = None):
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
    opti_complete_value_results = [result['complete_values'] for result in opti_eval_res]
    test_complete_value_results = [result['complete_values'] for result in test_eval_res]
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
    compariable_indicators = [i for i in opti_eval_res[0].keys() if i in plot_compariables]
    compariable_indicator_count = len(compariable_indicators)

    # 显示投资回报评价信息
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle(f'Optimization Test Results - {result_count} sets of strategy parameters', fontsize=14, fontweight=10)

    # 投资回测结果的评价指标全部被打印在图表上，所有的指标按照表格形式打印
    # 为了实现表格效果，指标的标签和值分成两列打印，每一列的打印位置相同
    fig.text(0.07, 0.91, f'opti periods: {opti_eval_res[0]["years"]} years, '
                         f'from: {opti_eval_res[0]["loop_start"].date()} to '
                         f'{opti_eval_res[0]["loop_end"].date()}  '
                         f'time consumed:   signal creation: {time_str_format(opti_eval_res[0]["op_run_time"])};'
                         f'  back test:{time_str_format(opti_eval_res[0]["loop_run_time"])}\n'
                         f'test periods: {test_eval_res[0]["years"]} years, '
                         f'from: {test_eval_res[0]["loop_start"].date()} to '
                         f'{test_eval_res[0]["loop_end"].date()}  '
                         f'time consumed:   signal creation: {time_str_format(test_eval_res[0]["op_run_time"])};'
                         f'  back test:{time_str_format(test_eval_res[0]["loop_run_time"])}')

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
        start_value = cres.value.iloc[0]
        values = (cres.value - start_value) / start_value * 100
        ax1.plot(first_opti_looped_values.index, values, linestyle='-',
                 color=(0.8, 0.2, 0.0), alpha=0.85, label='return')
    for cres in test_complete_value_results:
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
                                      for result in opti_eval_res],
                                     index=[result['par'] for result in opti_eval_res])
    test_indicator_df = pd.DataFrame([{key: result[key]
                                       for key in compariable_indicators}
                                      for result in test_eval_res],
                                     index=[result['par'] for result in test_eval_res])

    # 开始使用循环的方式逐个生成对比图表
    if compariable_indicator_count > 0:
        # TODO: BUG: 当输入的数据中含有inf时，会无法生成某些图表（如histo），因此需要排除此类情况
        for ax, name in zip(compariable_plots, compariable_indicators):
            # 设置每一个对比图表的基本显示格式
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_ylabel(f'{name}')
            ax.yaxis.tick_right()
            # 根据config中设置的参数，选择生成三种不同类型的图表之一。
            p_type = config.indicator_plot_type
            if p_type == 0 or p_type == 'errorbar':
                max_v = opti_indicator_df[name].max()
                min_v = opti_indicator_df[name].min()
                mean = opti_indicator_df[name].mean()
                std = opti_indicator_df[name].std()
                ax.errorbar(1, mean, std, fmt='ok', lw=3)
                ax.errorbar(1, mean, np.array(mean - min_v, max_v - mean).T, fmt='.k', ecolor='red', lw=1,
                            label=f'opti:{opti_indicator_df[name].mean():.2f}±{opti_indicator_df[name].std():.2f}')
                max_v = test_indicator_df[name].max()
                min_v = test_indicator_df[name].min()
                mean = test_indicator_df[name].mean()
                std = test_indicator_df[name].std()
                ax.errorbar(2, mean, std, fmt='ok', lw=3)
                ax.errorbar(2, mean, np.array(mean - min_v, max_v - mean).T, fmt='.k', ecolor='green', lw=1,
                            label=f'test:{test_indicator_df[name].mean():.2f}±{test_indicator_df[name].std():.2f}')
                ax.set_xlim(0, 3)
                labels = ['opti', 'test']
                ax.set_xticks(np.arange(1, len(labels) + 1))
                ax.set_xticklabels(labels)
                ax.set_xlim(0.25, len(labels) + 0.75)
            elif p_type == 1 or p_type == 'scatter':
                ax.scatter(opti_indicator_df[name],
                           test_indicator_df[name],
                           label=name, marker='^', alpha=0.9)
                ax.set_xlabel('opti')
                ax.set_ylabel('test')
                ax.legend()
            elif p_type == 2 or p_type == 'histo':
                ax.hist(opti_indicator_df[name], bins=15, alpha=0.5,
                        label=f'opti:{opti_indicator_df[name].mean():.2f}±{opti_indicator_df[name].std():.2f}')
                ax.hist(test_indicator_df[name], bins=15, alpha=0.5,
                        label=f'test:{test_indicator_df[name].mean():.2f}±{test_indicator_df[name].std():.2f}')
                ax.legend()
            elif p_type == 3 or p_type == 'violin':
                data_df = pd.DataFrame(np.array([opti_indicator_df[name], test_indicator_df[name]]).T,
                                       columns=['opti', 'test'])
                ax.violinplot(data_df)
                labels = ['opti', 'test']
                ax.set_xticks(np.arange(1, len(labels) + 1))
                ax.set_xticklabels(labels)
                ax.set_xlim(0.25, len(labels) + 0.75)
            else:
                data_df = pd.DataFrame(np.array([opti_indicator_df[name], test_indicator_df[name]]).T,
                                       columns=['opti', 'test'])
                ax.boxplot(data_df)
                labels = ['opti', 'test']
                ax.set_xticks(np.arange(1, len(labels) + 1))
                ax.set_xticklabels(labels)
                ax.set_xlim(0.25, len(labels) + 0.75)

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
    looped_values = loop_results['complete_values']
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
          f'final value:             ¥{loop_results["final_value"]:12,.2f}')
    print(f'Total return:             {loop_results["rtn"] * 100:12.2f}% \n'
          f'Avg Yearly return:        {loop_results["annual_rtn"] * 100:12.2f}%')
    print(f'Reference return:         {loop_results["ref_rtn"] * 100:12.2f}% \n'
          f'Reference Yearly return:  {loop_results["ref_annual_rtn"] * 100:12.2f}%')
    print(f'------strategy loop_results indicators------ \n'
          f'alpha:                    {loop_results["alpha"]:13.3f}\n'
          f'Beta:                     {loop_results["beta"]:13.3f}\n'
          f'Sharp ratio:              {loop_results["sharp"]:13.3f}\n'
          f'Info ratio:               {loop_results["info"]:13.3f}\n'
          f'250 day volatility:       {loop_results["volatility"]:13.3f}\n'
          f'Max drawdown:             {loop_results["mdd"] * 100:13.3f}% '
          f'from {loop_results["max_date"].date()} to {loop_results["low_date"].date()}')
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
          f'Total reference return: {ref_rtn * 100:.3f}% \n'
          f'Average Yearly reference return rate: {ref_annual_rtn * 100:.3f}%')
    print(f'statistical analysis of optimal strategy messages indicators: \n'
          f'total return:        {result.rtn.mean() * 100:.3f}% ±'
          f' {result.rtn.std() * 100:.3f}%\n'
          f'annual return:       {result.annual_rtn.mean() * 100:.3f}% ±'
          f' {result.annual_rtn.std() * 100:.3f}%\n'
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
                                       'final_value':  '{:,.2f}'.format,
                                       'rtn':         '{:.1%}'.format,
                                       'mdd':         '{:.1%}'.format,
                                       'ref_rtn':     '{:.1%}'.format,
                                       'sell_count':  '{:.1f}'.format,
                                       'buy_count':   '{:.1f}'.format},
                           justify='center'))
    print(f'\n===========END OF REPORT=============\n')
