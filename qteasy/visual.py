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
    # 查找每次买进和卖出的时间点并将他们存储在一个列表中，用于标记买卖时机
    if config.show_positions:
        position_bounds = [looped_values.index[0]]
        position_bounds.extend(looped_values.loc[change != 0].index)
        position_bounds.append(looped_values.index[-1])

    # 显示买卖时机的另一种方法，使用buy / sell 来存储买卖点
    # buy_point是当持股数量增加时为买点，sell_points是当持股数量下降时
    # 在买卖点当天写入的数据是参考数值，这是为了使用散点图画出买卖点的位置
    if config.buy_sell_points:
        buy_points = np.where(change > 0, ref_rate, np.nan)
        sell_points = np.where(change < 0, ref_rate, np.nan)

    # process plot figure and axes formatting
    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    CHART_WIDTH = 0.88
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
                         f' on {loop_results["low_date"].date()}')
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

    ax1.set_position([0.05, 0.41, CHART_WIDTH, 0.40])
    # 绘制参考数据的收益率曲线图
    ax1.plot(looped_values.index, ref_rate, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='Reference')
    # 绘制回测结果的收益率曲线图
    ax1.plot(looped_values.index, return_rate, linestyle='-',
             color=(0.8, 0.2, 0.0), alpha=0.85, label='Return')
    # 绘制买卖点散点图(效果是在ref线上使用红绿箭头标识买卖点)
    if config.buy_sell_points:
        ax1.scatter(looped_values.index, buy_points, color='green',
                    label='Buy', marker='^', alpha=0.9)
        ax1.scatter(looped_values.index, sell_points, color='red',
                    label='Sell', marker='v', alpha=0.9)
    ax1.set_ylabel('Total return rate')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.fill_between(looped_values.index, 0, ref_rate,
                     where=ref_rate >= 0,
                     facecolor=(0.4, 0.6, 0.2), alpha=0.35)
    ax1.fill_between(looped_values.index, 0, ref_rate,
                     where=ref_rate < 0,
                     facecolor=(0.8, 0.2, 0.0), alpha=0.35)
    ax1.yaxis.tick_right()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)

    # 显示持股仓位区间（效果是在回测区间上用绿色带表示多头仓位，红色表示空头仓位，颜色越深仓位越高）
    if config.show_positions:
        for first, second, long_short in zip(position_bounds[:-2], position_bounds[1:], position.loc[position_bounds[:-2]]):
            # fill long/short strips with grey
            # ax1.axvspan(first, second, facecolor=str(1 - color), alpha=0.2)
            # fill long/short strips with green/red colors
            if long_short > 0:
                # fill green strips if position is long
                ax1.axvspan(first, second,
                            facecolor=((1 - 0.6 * long_short), (1 - 0.4 * long_short), (1 - 0.8 * long_short)),
                            alpha=0.2)
            else:# fill red strips if position is short
                ax1.axvspan(first, second,
                            facecolor=((1 - 0.2 * long_short), (1 - 0.8 * long_short), (1 - long_short)),
                            alpha=0.2)
    # put arrow on where max draw down is
    # ax1.annotate("max_drawdown",
    #              xy=(loop_results["max_date"], return_rate[loop_results["low_date"]]),
    #              xytext=(0.7, 0.0),
    #              textcoords='axes fraction',
    #              arrowprops=dict(facecolor='black', shrink=0.3),
    #              horizontalalignment='right',
    #              verticalalignment='top')
    ax1.legend()

    ax2.set_position([0.05, 0.23, CHART_WIDTH, 0.18])
    ax2.plot(looped_values.index, position)
    ax2.set_ylabel('Amount bought / sold')
    ax2.set_xlabel(None)
    ax2.yaxis.tick_right()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.grid(True)

    ax3.set_position([0.05, 0.05, CHART_WIDTH, 0.18])
    ax3.bar(looped_values.index, ret)
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


def _plot_opti_result(result_pool: list, config):
    """ plot optimization results

    :param result_pool
        :type result_pool: list, 一个包含了所有最优参数的评价指标的list。

    :return:
    """
    # prepare looped_values dataframe
    result_count = len(result_pool)
    complete_results = [result['complete_values'] for result in result_pool]
    looped_values = complete_results[0]
    # for complete_value in complete_results:
    #     print(complete_value.tail(100))
    if looped_values.empty:
        raise ValueError
    register_matplotlib_converters()
    CHART_WIDTH = 0.9
    # 显示投资回报评价信息
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle(f'Optimization Result - {result_count} results', fontsize=14, fontweight=10)
    # output all evaluate looped_values in table form (values and labels are printed separately)
    ref_start_value = looped_values.reference.iloc[0]
    reference = (looped_values.reference - ref_start_value) / ref_start_value * 100
    ax1.set_position([0.05, 0.35, CHART_WIDTH, 0.55])
    ax1.plot(looped_values.index, reference, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='reference')
    for cres in complete_results:
        start_value = cres.value.iloc[0]
        values = (cres.value - start_value) / start_value * 100
        ax1.plot(looped_values.index, values, linestyle='-',
                 color=(0.8, 0.2, 0.0), alpha=0.85, label='return')
    ax1.set_ylabel('Total return rate')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.yaxis.tick_right()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)

    # display information of rtn and annual_rtn, alpha
    indicator_df = pd.DataFrame([{'rtn':        result['rtn'],
                                  'annual_rtn': result['annual_rtn'],
                                  'alpha':      result['alpha']} for result in result_pool],
                                index=[result['par'] for result in result_pool])
    ax2.set_position([0.05, 0.05, CHART_WIDTH / 2 - 0.05, 0.25])
    maxes = indicator_df.max(axis=0)
    mins = indicator_df.min(axis=0)
    mean = indicator_df.mean(axis=0)
    std = indicator_df.std(axis=0)
    ax2.errorbar(np.arange(3), mean, std, fmt='ok', lw=3)
    ax2.errorbar(np.arange(3), mean, [mean - mins, maxes - mean], fmt='.k', ecolor='gray', lw=1)

    ax3.set_position([0.55, 0.05, CHART_WIDTH / 2 - 0.05, 0.25])
    ax3.hist(indicator_df['alpha'], bins=10)

    plt.show()


# TODO: like _print_test_result, take the evaluate results on both opti and test hist data
# TODO: and commit comparison base on these two data sets
def _plot_test_result(test_eval_res: list,
                      opti_eval_res: list,
                      config):
    """ plot test result of optimization results

    :param test_eval_res:
        :type test_eval_res: list

    :param opti_eval_res:
        :type opti_eval_res: list

    :param config:
    :return:
    """

    # prepare looped_values dataframe
    result_count = len(test_eval_res)
    opti_complete_value_results = [result['complete_values'] for result in opti_eval_res]
    test_complete_value_results = [result['complete_values'] for result in test_eval_res]
    first_opti_looped_values = opti_complete_value_results[0]
    first_test_looped_values = test_complete_value_results[0]
    # for complete_value in complete_results:
    #     print(complete_value.tail(100))
    if first_opti_looped_values.empty:
        raise ValueError
    if first_test_looped_values.empty:
        raise ValueError
    register_matplotlib_converters()
    CHART_WIDTH = 0.9
    # 显示投资回报评价信息
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle(f'Optimization Result - {result_count} results', fontsize=14, fontweight=10)
    # output all evaluate looped_values in table form (values and labels are printed separately)
    ref_start_value = first_test_looped_values.reference.iloc[0]
    reference = (first_test_looped_values.reference - ref_start_value) / ref_start_value * 100
    ax1.set_position([0.05, 0.35, CHART_WIDTH, 0.55])
    ax1.plot(first_test_looped_values.index, reference, linestyle='-',
             color=(0.4, 0.6, 0.8), alpha=0.85, label='reference')
    for cres in opti_complete_value_results:
        start_value = cres.value.iloc[0]
        values = (cres.value - start_value) / start_value * 100
        ax1.plot(first_opti_looped_values.index, values, linestyle='-',
                 color=(0.8, 0.2, 0.0), alpha=0.85, label='return')
    for cres in test_complete_value_results:
        start_value = cres.value.iloc[0]
        values = (cres.value - start_value) / start_value * 100
        ax1.plot(first_test_looped_values.index, values, linestyle='-',
                 color=(0.2, 0.8, 0.2), alpha=0.85, label='return')

    ax1.set_ylabel('Total return rate')
    ax1.grid(True)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.yaxis.tick_right()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)

    ax2.set_position([0.05, 0.05, CHART_WIDTH / 2 - 0.05, 0.25])

    ax3.set_position([0.55, 0.05, CHART_WIDTH / 2 - 0.05, 0.25])

    fig.show()


def _print_operation_signal(run_time_prepare_data, op_list):
    """打印实时信号生成模式的运行结果
    """
    print(f'\n      ====================================\n'
          f'      |                                  |\n'
          f'      |       OPERATION SIGNALS          |\n'
          f'      |                                  |\n'
          f'      ====================================\n')
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

    :param looped_values:
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
    :param messages:
    :param columns:
    :param headers:
    :param formatter:
    :return:
    """
    result = pd.DataFrame(result)
    first_res = result.iloc[0]
    ref_rtn, ref_annual_rtn = first_res['ref_rtn'], first_res['ref_annual_rtn']
    print(f'==================================== \n'
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
                           formatters={'total_fee':    '{:,.2f}'.format,
                                       'final_value':  '{:,.2f}'.format,
                                       'rtn':          '{:.1%}'.format,
                                       'mdd':          '{:.1%}'.format,
                                       'ref_rtn':      '{:.1%}'.format,
                                       'sell_count':   '{:.1f}'.format,
                                       'buy_count':    '{:.1f}'.format},
                           justify='center'))
    print(f'\n===========END OF REPORT=============\n')


# def _print_opti_result(pars, perfs, config=None, columns=None, headers=None, formatter=None):
#     """
#
#     :param result:
#     :param messages:
#     :param config:
#     :param columns:
#     :param headers:
#     :param formatter:
#     :return:
#     """
#     print(f'====================================\n'
#           f'|                                  |\n'
#           f'|       OPTIMIZATION RESULT        |\n'
#           f'|                                  |\n'
#           f'====================================\n')
#     print(f'Searching finished, {len(perfs)} best results are generated')
#     print(f'The best parameter performs {perfs[-1]/perfs[0]:.3f} times better than the least performing result:\n'
#           f'=======================OPTIMIZATION RESULTS===========================\n'
#           f'                    parameter                     |    performance    \n'
#           f'--------------------------------------------------|-------------------')
#     for par, perf in zip(pars, perfs):
#         print(f'{par}{" " * (50 - len(str(par)))}|  {perf:.3f}')
#     # print(f'best result: {perfs[-1]:.3f} obtained at parameter: \n{items[-1]}')
#     # print(f'least result: {perfs[0]:.3f} obtained at parameter: \n{items[0]}')
#     print(f'===============VALIDATION OF OPTIMIZATION RESULTS==================')