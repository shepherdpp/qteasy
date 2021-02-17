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
from pandas.plotting import register_matplotlib_converters
import datetime
from .tsfuncs import get_bar, name_change
from .utilfuncs import time_str_format


# TODO: simplify and merge these three functions
def candle(stock_data=None, share_name=None, stock=None, start=None, end=None,
           asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    if stock_data is None:
        assert stock is not None
        daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
    else:
        assert type(stock_data) == pd.DataFrame
        assert all(col in ['open', 'high', 'low', 'close', 'volume'] for col in stock_data.columns)
        daily = stock_data
        if share_name is None:
            share_name = 'stock'
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
    return daily


def ohlc(stock_data=None, share_name=None, stock=None, start=None, end=None,
         asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    if stock_data is None:
        assert stock is not None
        daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
    else:
        assert isinstance(stock_data, pd.DataFrame)
        assert all(col in ['open', 'high', 'low', 'close', 'volume'] for col in stock_data.columns)
        daily = stock_data
        if share_name is None:
            share_name = 'stock'
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
    return daily


def renko(stock_data=None, share_name=None, stock=None, start=None, end=None,
          asset_type='E', figsize=(10, 5), mav=(5, 10, 20, 30), no_visual=False):
    if stock_data is None:
        assert stock is not None
        daily, share_name = _prepare_mpf_data(stock=stock, start=start, end=end, asset_type=asset_type)
    else:
        assert isinstance(stock_data, pd.DataFrame)
        assert all(col in ['open', 'high', 'low', 'close', 'volume'] for col in stock_data.columns)
        daily = stock_data
        if share_name is None:
            share_name = 'stock'
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


def _plot_loop_result(result, msg: dict):
    """plot the loop results in a fancy way that displays all information more clearly"""
    # prepare result dataframe
    if not isinstance(result, pd.DataFrame):
        raise TypeError('')
    if result.empty:
        raise ValueError()
    # debug
    # print(f'in visual function, got msg max date and low_date: \n'
    #       f'msg["max_date"]:  {msg["max_date"]}\n'
    #       f'msg["low_date"]:  {msg["low_date"]}')
    register_matplotlib_converters()
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
    position = 1 - (result['cash'] / result['value'])
    return_rate = (result.value - start_point) / start_point * 100
    ref_rate = (reference - start_point) / start_point * 100
    position_bounds = [result.index[0]]
    position_bounds.extend(result.loc[change != 0].index)
    position_bounds.append(result.index[-1])

    # process plot figure and axes formatting
    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    CHART_WIDTH = 0.88
    # 显示投资回报评价信息
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), facecolor=(0.82, 0.83, 0.85))
    fig.suptitle('Back Testing Result - reference: 000300.SH', fontsize=14, fontweight=10)
    # output all evaluate result in table form (values and labels are printed separately)
    fig.text(0.07, 0.93, f'periods: {msg["years"]} years, '
                         f'from: {msg["loop_start"].date()} to {msg["loop_end"].date()}'
                         f'time consumed:   signal creation: {time_str_format(msg["run_time_p"])};'
                         f'  back test:{time_str_format(msg["run_time_l"])}')
    fig.text(0.21, 0.82, f'Operation summary:\n\n'
                         f'Total op fee:\n'
                         f'total investment:\n'
                         f'final value:', ha='right')
    fig.text(0.23, 0.82, f'{msg["oper_count"].buy.sum()}     buys \n'
                         f'{msg["oper_count"].sell.sum()}     sells\n'
                         f'¥{msg["total_fee"]:13,.2f}\n'
                         f'¥{msg["total_invest"]:13,.2f}\n'
                         f'¥{msg["final_value"]:13,.2f}')
    fig.text(0.50, 0.82, f'Total return:\n'
                         f'Avg annual return:\n'
                         f'ref return:\n'
                         f'Avg annual ref return:\n'
                         f'Max drawdown:', ha='right')
    fig.text(0.52, 0.82, f'{msg["rtn"] * 100:.2f}%    \n'
                         f'{msg["annual_rtn"] * 100: .2f}%    \n'
                         f'{msg["ref_rtn"] * 100:.2f}%    \n'
                         f'{msg["ref_annual_rtn"] * 100:.2f}%\n'
                         f'{msg["mdd"] * 100:.3f}%'
                         f' on {msg["low_date"].date()}')
    fig.text(0.82, 0.82, f'alpha:\n'
                         f'Beta:\n'
                         f'Sharp ratio:\n'
                         f'Info ratio:\n'
                         f'250-day volatility:', ha='right')
    fig.text(0.84, 0.82, f'{msg["alpha"]:.3f}  \n'
                         f'{msg["beta"]:.3f}  \n'
                         f'{msg["sharp"]:.3f}  \n'
                         f'{msg["info"]:.3f}  \n'
                         f'{msg["volatility"]:.3f}')

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

    # 显示持股仓位区间
    # TODO: 使用箭头标记买入和卖出点：位于参考线下方的绿色箭头代表买入，位于参考线上方的红色箭头代表卖出
    for first, second, long_short in zip(position_bounds[:-2], position_bounds[1:], position.loc[position_bounds[:-2]]):
        # fill long/short strips with grey
        # ax1.axvspan(first, second, facecolor=str(1 - color), alpha=0.2)
        # fill long/short strips with green/red colors
        if long_short > 0:
            # fill green strips if position is long
            ax1.axvspan(first, second,
                        facecolor=((1 - 0.6 * long_short), (1 - 0.4 * long_short), (1 - 0.8 * long_short)),
                        alpha=0.2)
        else:
            # fill red strips if position is short
            ax1.axvspan(first, second,
                        facecolor=((1 - 0.2 * long_short), (1 - 0.8 * long_short), (1 - long_short)),
                        alpha=0.2)
    ax1.annotate("max_drawdown",
                 xy=(msg["max_date"], return_rate[msg["low_date"]]),
                 xytext=(0.7, 0.0),
                 textcoords='axes fraction',
                 arrowprops=dict(facecolor='black', shrink=0.3),
                 horizontalalignment='right',
                 verticalalignment='top')
    ax1.legend()

    ax2.set_position([0.05, 0.23, CHART_WIDTH, 0.18])
    ax2.plot(result.index, position)
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


def _plot_opti_result():
    """ plot optimization results

    :return:
    """
    raise NotImplementedError


# TODO: like _print_test_result, take the evaluate results on both opti and test hist data
# TODO: and commit comparison base on these two data sets
def _plot_test_result(test_eval_res: pd.DataFrame,
                      opti_eval_res: pd.DataFrame,
                      test_loop_lists: list,
                      opti_loop_lists: list,
                      config):
    """ plot test result of optimization results

    :param test_eval_res:
    :param opti_eval_res:
    :param test_loop_lists:
    :param opti_loop_lists:
    :param config:
    :return:
    """
    raise NotImplementedError


def _print_operation_signal(run_time_prepare_data, op_list):
    """打印实时信号生成模式的运行结果
    """
    print(f'====================================\n'
          f'|                                  |\n'
          f'|       OPERATION SIGNALS          |\n'
          f'|                                  |\n'
          f'====================================\n')
    print(f'time consumption for operate signal creation: {time_str_format(run_time_prepare_data)}\n')
    print(f'Operation signals are generated on {op_list.index[0]}\nends on {op_list.index[-1]}\n'
          f'Total signals generated: {len(op_list.index)}.')
    print(f'Operation signal for shares on {op_list.index[-1].date()}')
    for share, signal in op_list.iloc[-1].iteritems():
        print(f'share {share}:')
        if signal > 0:
            print(f'Buy in with {signal * 100}% of total investment value!')
        elif signal < 0:
            print(f'Sell out {-signal * 100}% of current on holding stock!')
    print(f'\n===========END OF REPORT=============\n')


def _print_loop_result(result, messages=None, columns=None, headers=None, formatter=None):
    """ 格式化打印输出单次回测的结果，根据columns、headers、formatter等参数选择性输出result中的结果
        确保输出的格式美观一致

    :param result:
    :param messages:
    :param columns:
    :param headers:
    :param formatter:
    :return:
    """
    print(f'==================================== \n'
          f'|                                  |\n'
          f'|       BACK TESTING RESULT        |\n'
          f'|                                  |\n'
          f'====================================')
    print(f'\nqteasy running mode: 1 - History back testing\n'
          f'time consumption for operate signal creation: {time_str_format(messages["run_time_p"])}\n'
          f'time consumption for operation back looping:  {time_str_format(messages["run_time_l"])}\n')
    print(f'investment starts on      {result.index[0]}\n'
          f'ends on                   {result.index[-1]}\n'
          f'Total looped periods:     {messages["years"]:.1f} years.')
    print(f'-----------operation summary:-----------\n '
          f'{messages["oper_count"]}\n'
          f'Total operation fee:     ¥{messages["total_fee"]:12,.2f}')
    print(f'total investment amount: ¥{messages["total_invest"]:12,.2f}\n'
          f'final value:             ¥{messages["final_value"]:12,.2f}')
    print(f'Total return:             {messages["rtn"] * 100:12.2f}% \n'
          f'Avg Yearly return:        {messages["annual_rtn"] * 100:12.2f}%')
    print(f'Reference return:         {messages["ref_rtn"] * 100:12.2f}% \n'
          f'Reference Yearly return:  {messages["ref_annual_rtn"] * 100:12.2f}%')
    print(f'------strategy messages indicators------ \n'
          f'alpha:                    {messages["alpha"]:13.3f}\n'
          f'Beta:                     {messages["beta"]:13.3f}\n'
          f'Sharp ratio:              {messages["sharp"]:13.3f}\n'
          f'Info ratio:               {messages["info"]:13.3f}\n'
          f'250 day volatility:       {messages["volatility"]:13.3f}\n'
          f'Max drawdown:             {messages["mdd"] * 100:13.3f}% '
          f'from {messages["max_date"].date()} to {messages["low_date"].date()}')
    print(f'\n===========END OF REPORT=============\n')


# TODO: like _plot_test_result, take the evaluate results on both opti and test hist data
# TODO: and commit comparison base on these two data sets
def _print_test_result(result, messages=None, config=None, columns=None, headers=None, formatter=None):
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

    ref_rtn, ref_annual_rtn = messages['ref_rtn'], messages['ref_annual_rtn']
    print(f'==================================== \n'
          f'|                                  |\n'
          f'|       OPTIMIZATION RESULT        |\n'
          f'|                                  |\n'
          f'====================================')
    print(f'\nqteasy running mode: 2 - Strategy Parameter Optimization\n')
    print(f'investment starts on {messages["loop_start"]}\nends on {messages["loop_end"]}\n'
          f'Total looped periods: {result.years[0]:.1f} years.')
    print(f'total investment amount: ¥{result.total_invest[0]:13,.2f}')
    print(f'Reference index type is {config.reference_asset} at {config.ref_asset_type}\n'
          f'Total reference return: {ref_rtn * 100:.3f}% \n'
          f'Average Yearly reference return rate: {ref_annual_rtn * 100:.3f}%')
    print(f'statistical analysis of optimal strategy messages indicators: \n'
          f'total return:        {result.total_return.mean() * 100:.3f}% ±'
          f' {result.total_return.std() * 100:.3f}%\n'
          f'annual return:       {result.annual_return.mean() * 100:.3f}% ±'
          f' {result.annual_return.std() * 100:.3f}%\n'
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
                                    "total_return",
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
                                       'total_return': '{:.1%}'.format,
                                       'mdd':          '{:.1%}'.format,
                                       'ref_rtn':      '{:.1%}'.format,
                                       'sell_count':   '{:.1f}'.format,
                                       'buy_count':    '{:.1f}'.format},
                           justify='center'))
    print(f'\n===========END OF REPORT=============\n')


def _print_opti_result(pars, perfs, config=None, columns=None, headers=None, formatter=None):
    """

    :param result:
    :param messages:
    :param config:
    :param columns:
    :param headers:
    :param formatter:
    :return:
    """
    print(f'====================================\n'
          f'|                                  |\n'
          f'|       OPTIMIZATION RESULT        |\n'
          f'|                                  |\n'
          f'====================================\n')
    print(f'Searching finished, {len(perfs)} best results are generated')
    print(f'The best parameter performs {perfs[-1]/perfs[0]:.3f} times better than the least performing result:\n'
          f'=======================OPTIMIZATION RESULTS===========================\n'
          f'                    parameter                     |    performance    \n'
          f'--------------------------------------------------|-------------------')
    for par, perf in zip(pars, perfs):
        print(f'{par}{" " * (50 - len(str(par)))}|  {perf:.3f}')
    # print(f'best result: {perfs[-1]:.3f} obtained at parameter: \n{items[-1]}')
    # print(f'least result: {perfs[0]:.3f} obtained at parameter: \n{items[0]}')
    print(f'===============VALIDATION OF OPTIMIZATION RESULTS==================')