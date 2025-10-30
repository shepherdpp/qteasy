# coding=utf-8
# ======================================
# File:     backtest.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-03-12
# Desc:
#   Functions used for backtesting and
# evaluation of trade results
# ======================================

import os
import pandas as pd
import numpy as np
from numba import njit  # try taichi, which might be even faster
from typing import Any, Union

from numpy import bool_, dtype, ndarray

import qteasy
from qteasy.history import HistoryPanel
from qteasy.qt_operator import Operator

from qteasy.finance import (
    get_selling_result,
    get_purchase_result,
)

from qteasy.trading_util import (
    parse_pt_signals,
    parse_ps_signals,
    parse_vs_signals,
    trim_pt_type_signals,
)


@njit(nogil=True, cache=True)
def backtest_step(
        signal_type: Union[int, np.int32, np.int64, np.ndarray],
        op_signal: np.ndarray,
        cash_inflation: np.ndarray,
        is_delivery_day: bool,
        day_num: Union[int, np.int32, np.int64, np.ndarray],
        own_cash: np.ndarray,
        own_amounts: np.ndarray,
        available_cash: np.ndarray,
        available_amounts: np.ndarray,
        trade_prices: np.ndarray,
        cost_params: np.ndarray,
        pt_buy_threshold: float,
        pt_sell_threshold: float,
        long_pos_limit: float,
        short_pos_limit: float,
        allow_sell_short: bool,
        moq_buy: float,
        moq_sell: float,
        cash_delivery_queue: np.ndarray,
        stock_delivery_queue: np.ndarray,
        cash_delivery_period: int,
        stock_delivery_period: int,
        share_count: int,
):
    """ 完成一次完整的单步骤回测计算，包括下面三个步骤：
    1，检查现金增值比例，如果大于0，则更新持有现金和可用现金
    2，调用calculate_trade_results()函数计算本次交易结果
    3，处理现金变动和持仓变动的交割，更新持有现金和可用现金，更新持有资产和可用资产
    更新账户现金和持仓余额后，返回交易后的各项数据和交割队列

    Parameters
    ----------
    signal_type: int
        信号类型:
            0 - PT signal
            1 - PS signal
            2 - VS signal
    op_signal: np.ndarray
        本次交易的个股交易信号
    cash_inflation: float
        现金增值比例
    is_delivery_day: bool
        是否为新的交割日，用于确定是否需要更新交割队列
    day_num: int
        当前的天数，用于确定交割队列中的交割位置
    own_cash: float
        本次交易开始前持有的现金余额（包括交割中的现金）
    own_amounts: np.ndarray
        本次交易开始前持有的资产份额（包括交割中的资产份额）
    available_cash: float
        本次交易开始前账户可用现金余额（交割中的现金不计入余额）
    available_amounts: np.ndarray:
        交易开始前各个股票的可用数量余额（交割中的股票不计入余额）
    trade_prices: np.ndarray
        本次交易发生时各个股票的交易价格
    cost_params: np.ndarray
        交易成本参数，包括买入费率、卖出费率、最低买入费用、最低卖出费用、交易滑点
        buy_rate: float, 交易成本：买入费率
        sell_rate: float, 交易成本：卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slipage: float, 交易成本：交易滑点
    pt_buy_threshold: float
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    pt_sell_threshold: float
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    long_pos_limit: float
        允许建立的多头总仓位与净资产的比值，默认值1.0，表示最多允许建立100%多头仓位
    short_pos_limit: float
        允许建立的空头总仓位与净资产的比值，默认值-1.0，表示最多允许建立100%空头仓位
    allow_sell_short: bool
        True:   允许买空卖空
        False:  只允许买入多头仓位
    moq_buy: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍
    moq_sell: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍
    cash_delivery_queue: np.ndarray
        现金交割队列
    stock_delivery_queue: np.ndarray
        股票交割队列
    cash_delivery_period: int
        现金交割周期
    stock_delivery_period: int
        股票交割周期
    share_count: int
        交易的股票数量

    Returns
    -------
    tuple: (next_own_cash, next_available_cash, next_own_amounts, next_available_amounts,
            current_trade_records, current_trade_cost, cash_delivery_queue, stock_delivery_queue)
        next_own_cash: float
            本次交易结束后持有的现金余额（包括交割中的现金）
        next_available_cash: float
            本次交易结束后账户可用现金余额（交割中的现金不计入余额）
        next_own_amounts: np.ndarray
            本次交易结束后持有的资产份额（包括交割中的资产份额）
        next_available_amounts: np.ndarray
            交易结束后各个股票的可用数量余额（交割中的股票不计入余额）
        current_trade_records: np.ndarray
            本次交易的交易记录
        current_trade_cost: np.ndarray
            本次交易的交易费用
        cash_delivery_queue: np.ndarray
            更新后的现金交割队列
        stock_delivery_queue: np.ndarray
            更新后的股票交割队列
    """

    # 1，如果现金增值比例大于0，则更新持有现金和可用现金
    if cash_inflation > 1.:
        own_cash *= cash_inflation
        available_cash *= cash_inflation
        # DEBUG:
        # print(f'- cash inflation applied: {cash_inflation}, new own_cash = {own_cash}\n')

    # 2，调用backtest_step函数，计算本次交易的现金变动、持仓变动和交易费用
    cash_gained, cash_spent, amount_purchased, amount_sold, fees = calculate_trade_results(
            signal_type=signal_type,
            own_cash=own_cash,
            own_amounts=own_amounts,
            available_cash=available_cash,
            available_amounts=available_amounts,
            op_signal=op_signal,
            prices=trade_prices,
            cost_params=cost_params,
            pt_buy_threshold=pt_buy_threshold,
            pt_sell_threshold=pt_sell_threshold,
            long_pos_limit=long_pos_limit,
            short_pos_limit=short_pos_limit,
            allow_sell_short=allow_sell_short,
            moq_buy=moq_buy,
            moq_sell=moq_sell
    )
    # DEBUG:
    # print(f'- Calculated trade results for the end of step: \n'
    #       f'  cash_gained = {cash_gained}, cash_spent = {cash_spent}\n'
    #       f'  amount_purchased = {amount_purchased}, amount_sold = {amount_sold}\n'
    #       f'  fees = {fees}\n')

    # 3，处理现金变动和持仓变动的交割，输出交割数据
    new_cash = cash_gained.sum()
    delivered_cash, delivered_stocks = process_backtest_delivery(
            cash_delivery_queue=cash_delivery_queue,
            stock_delivery_queue=stock_delivery_queue,
            is_new_day=is_delivery_day,
            day_num=day_num,
            new_cash=new_cash,
            new_stocks=amount_purchased,
            cash_delivery_period=cash_delivery_period,
            stock_delivery_period=stock_delivery_period,
            share_count=share_count,
    )
    # DEBUG:
    # print(f'- processed delivery at end of step: \n'
    #       f'  delivered_cash = {delivered_cash}, delivered_stocks = {delivered_stocks}, \n'
    #       f'  cash_delivery_queue = {cash_delivery_queue}, \n'
    #       f'  stock_delivery_queue = {stock_delivery_queue}, \n')

    # 4, 更新持有现金和可用现金
    next_own_cash = own_cash + cash_gained.sum() + cash_spent.sum()
    next_available_cash = available_cash + delivered_cash + cash_spent.sum()
    # 更新持有资产和可用资产
    next_own_amounts = own_amounts + amount_purchased + amount_sold
    next_available_amounts = available_amounts + delivered_stocks + amount_sold

    # DEBUG:
    # print(f'- updated holdings at end of step: \n'
    #       f'  next_own_cash({next_own_cash}) = own_cash({own_cash}) + cash_gained({cash_gained.sum()}) + '
    #       f'cash_spent({cash_spent.sum()})\n'
    #       f'  next_available_cash({next_available_cash}) = available_cash({available_cash}) + '
    #       f'delivered_cash({delivered_cash}) + cash_spent({cash_spent.sum()})\n'
    #       f'  next_own_amounts({next_own_amounts}) = own_amounts({own_amounts}) + '
    #       f'amount_purchased({amount_purchased}) + amount_sold({amount_sold})\n'
    #       f'  next_available_amounts({next_available_amounts}) = available_amounts({available_amounts}) + '
    #       f'delivered_stocks({delivered_stocks}) + amount_sold({amount_sold})\n')

    # 5, 记录交易记录和交易费用
    current_trade_records = amount_purchased + amount_sold
    current_trade_cost = fees

    return (
        next_own_cash,
        next_available_cash,
        next_own_amounts,
        next_available_amounts,
        current_trade_records,
        current_trade_cost,
        cash_delivery_queue,
        stock_delivery_queue,
    )


@njit()
def calculate_trade_results(
        signal_type: Union[int, np.int32, np.int64, np.ndarray],
        own_cash: Union[float, np.float64, np.ndarray],
        own_amounts: np.ndarray,
        available_cash: Union[float, np.float64, np.ndarray],
        available_amounts: np.ndarray,
        op_signal: np.ndarray,
        prices: np.ndarray,
        cost_params: np.ndarray,
        pt_buy_threshold: float,
        pt_sell_threshold: float,
        long_pos_limit: float,
        short_pos_limit: float,
        allow_sell_short: bool,
        moq_buy: float,
        moq_sell: float,
) -> Union[tuple[ndarray, ndarray, ndarray, ndarray, ndarray],
           tuple[ndarray, ndarray, ndarray, ndarray, ndarray[Any, dtype[bool_]]]]:
    """ 该函数用于批量计算股票交易结果，根据交易信号、价格和持仓情况，结合交易
    成本和仓位限制，计算出每只股票的买入卖出数量、现金变动及交易费用。支持多种
    交易信号类型（PT、PS、VS）和做空机制，并通过Numba加速计算。

    Parameters
    ----------
    signal_type: int
        信号类型:
            0 - PT signal
            1 - PS signal
            2 - VS signal
    own_cash: float
        本次交易开始前持有的现金余额（包括交割中的现金）
    own_amounts: np.ndarray
        本次交易开始前持有的资产份额（包括交割中的资产份额）
    available_cash: np.ndarray
        本次交易开始前账户可用现金余额（交割中的现金不计入余额）
    available_amounts: np.ndarray:
        交易开始前各个股票的可用数量余额（交割中的股票不计入余额）
    op_signal: np.ndarray
        本次交易的个股交易信号
    prices: np.ndarray，
        本次交易发生时各个股票的交易价格
    cost_params: np.ndarray
        交易成本参数，包括固定买入费用、固定卖出费用、买入费率、卖出费率、最低买入费用、最低卖出费用
        buy_fix: float, 交易成本：固定买入费用
        sell_fix: float, 交易成本：固定卖出费用
        buy_rate: float, 交易成本：固定买入费率
        sell_rate: float, 交易成本：固定卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slipage: float, 交易成本：滑点
    pt_buy_threshold: object Cost
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    pt_sell_threshold: object Cost
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    long_pos_limit: float
        允许建立的多头总仓位与净资产的比值，默认值1.0，表示最多允许建立100%多头仓位
    short_pos_limit: float
        允许建立的空头总仓位与净资产的比值，默认值-1.0，表示最多允许建立100%空头仓位
    allow_sell_short: bool
        True:   允许买空卖空
        False:  默认值，只允许买入多头仓位
    moq_buy: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍
    moq_sell: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

    Returns
    -------
    tuple: (cash_gained, cash_spent, amounts_purchased, amounts_sold, fee)
        cash_gained:        ndarray, 本批次交易中获得的现金增加额
        cash_spent:         ndarray, 本批次交易中共花费的现金总额
        amounts_purchased:  ndarray, 交易后每个个股账户中的股份增加数量
        amounts_sold:       ndarray, 交易后每个个股账户中的股份减少数量
        fee:                ndarray, 本次交易每个个股的交易费用，包括卖出的费用和买入的费用
    """
    # 1,计算期初资产总额：交易前现金及股票余额在当前价格下的资产总额
    pre_values = own_amounts * prices
    total_value = own_cash + pre_values.sum()
    empty_array = np.zeros_like(op_signal)

    # 2,制定交易计划，生成计划买入金额和计划卖出数量
    if signal_type == 0:  # PT信号
        # 限定PT信号在多空持仓限额范围内，这样就不需要在后续处理交易指令时调整交易数量了
        trimmed_op_signal = trim_pt_type_signals(
                op_signals=op_signal,
                long_pos_limit=long_pos_limit,
                short_pos_limit=short_pos_limit,
        )
        cash_to_spend, amounts_to_sell = parse_pt_signals(
                signals=trimmed_op_signal,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                pt_buy_threshold=pt_buy_threshold,
                pt_sell_threshold=pt_sell_threshold,
                allow_sell_short=allow_sell_short
        )

    elif signal_type == 1:  # PS信号
        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=op_signal,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=allow_sell_short
        )
        # 如果是全零信号，则直接返回空结果
        if np.all(cash_to_spend == 0) and np.all(amounts_to_sell == 0):
            return (empty_array,
                    empty_array,
                    empty_array,
                    empty_array,
                    empty_array)

    elif signal_type == 2:  # VS信号
        cash_to_spend, amounts_to_sell = parse_vs_signals(
                signals=op_signal,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=allow_sell_short,
                cost_params=cost_params,
        )
        # 如果是全零信号，则直接返回空结果
        if np.all(cash_to_spend == 0) and np.all(amounts_to_sell == 0):
            return (empty_array,
                    empty_array,
                    empty_array,
                    empty_array,
                    empty_array)

    else:
        raise ValueError('Invalid signal_type')

    # 3, 根据可用股票数量或多空持仓限额调整卖出计划。

    # 如果不允许卖空交易，则根据可用股份数量调整卖出计划，确保卖出数量不超过可用数量，
    # 此时忽略long_pos_limit与short_pos_limit，因为pos_limit被可用金额自动限制在0～1之间
    if not allow_sell_short:
        amounts_to_sell = - np.fmin(-amounts_to_sell, available_amounts)
    else:  # 如果允许卖空交易，则检查卖出计划是否超过own_amounts，将超过的部分转化为相应的空头/多头买入
        excesive_long_amounts_to_sell = np.where(
                (amounts_to_sell < 0) & (own_amounts + amounts_to_sell < 0),
                own_amounts + amounts_to_sell,
                0
        )
        cash_to_spend += excesive_long_amounts_to_sell * prices
        excesive_short_amounts_to_sell = np.where(
                (amounts_to_sell > 0) & (own_amounts + amounts_to_sell > 0),
                own_amounts + amounts_to_sell,
                0
        )
        cash_to_spend += excesive_short_amounts_to_sell * prices
        amounts_to_sell -= excesive_long_amounts_to_sell + excesive_short_amounts_to_sell

    # 4，批量提交股份卖出计划，计算实际卖出份额和交易费用
    amount_sold, cash_gained, fee_selling = get_selling_result(
            prices=prices,
            a_to_sell=amounts_to_sell,
            moq=moq_sell,
            cost_params=cost_params,
    )

    if np.all(np.abs(cash_to_spend) < 0.001):
        # 如果所有买入计划绝对值都小于1分钱，则直接跳过后续的计算
        return cash_gained, empty_array, empty_array, amount_sold, fee_selling

    # 5，根据可用现金数量或多空持仓限额调整买入计划

    # 如果不允许卖空交易，则根据可用现金调整买入计划，确保买入总金额不超过可用现金
    # 此时自动保证交易后的持仓比例在0～1之间
    if not allow_sell_short:
        # 忽略cash_to_spend中的空头买入部分（不允许卖空时无意义）
        cash_to_spend = np.where(cash_to_spend > 0.001, cash_to_spend, 0)
        # 确保总现金买入金额不超过可用现金，如果超过则按比例调降
        if cash_to_spend.sum() > available_cash:
            cash_to_spend *= available_cash / cash_to_spend.sum()

    elif signal_type >= 1:
        # 调整买入金额，确保产生的仓位不会超过long_pos_limit和short_pos_limit
        # 因为signal_type != 0，因此调整的比例以买入金额为准
        next_own_amounts = own_amounts + amount_sold
        long_cash_to_spend = np.where(cash_to_spend > 0.001, cash_to_spend, 0)
        total_long_cash_to_spend = long_cash_to_spend.sum()
        max_long_pos_to_buy = long_pos_limit * total_value - np.where(
                cash_to_spend > 0.001, next_own_amounts * prices, 0).sum()

        short_cash_to_spend = np.where(cash_to_spend < -0.001, cash_to_spend, 0)
        total_short_cash_to_spend = short_cash_to_spend.sum()
        max_short_pos_to_buy = short_pos_limit * total_value - np.where(
                cash_to_spend < -0.001, next_own_amounts * prices, 0).sum()

        if total_long_cash_to_spend > max_long_pos_to_buy:
            # 如果计划买入多头现金超过允许买入最大金额，按比例降低分配给每个拟买入多头资产的现金
            long_cash_to_spend *= max_long_pos_to_buy / total_long_cash_to_spend

        if total_short_cash_to_spend < max_short_pos_to_buy:
            # 如果计划买入空头现金超过允许买入最大金额，按比例调降拟买入空头资产的现金
            short_cash_to_spend *= max_short_pos_to_buy / total_short_cash_to_spend

        cash_to_spend = long_cash_to_spend + short_cash_to_spend
    else:
        # 对于signal_type == 0，在生成买入数量前，仓位信号已经被限制在
        # long_pos_limit和short_pos_limit之间了，因此不需要再调整
        pass

    # 批量提交股份买入计划，计算实际买入的股票份额和交易费用dflasjdf
    # 由于已经提前确认过现金总额，因此不存在买入总金额超过持有现金的情况
    amount_purchased, cash_spent, fee_buying = get_purchase_result(
            prices=prices,
            cash_to_spend=cash_to_spend,
            moq=moq_buy,
            cost_params=cost_params,
    )

    # 4, 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = fee_buying + fee_selling

    return cash_gained, cash_spent, amount_purchased, amount_sold, fee


@njit()  # 使用numba加速反而更慢，可能是因为函数体太简单，编译和调用开销大于计算开销
def initialize_backtest_delivery_queue(cash_delivery_period: int,
                                       stock_delivery_period: int,
                                       share_count: int):
    """ 初始化回测现金和股票交割队列，因为回测是批量进行的，因此需要通过交割队列进行快速交割计算

    Parameters
    ----------
    cash_delivery_period: int
        现金交割周期
    stock_delivery_period: int
        股票交割周期
    share_count: int
        股票数量

    Returns
    -------
    cash_delivery_queue: np.ndarray
        现金交割队列
    stock_delivery_queue: np.ndarray
        股票交割队列
    """

    cash_delivery_queue = np.zeros(shape=(cash_delivery_period + 1,), dtype='float')

    stock_delivery_queue = np.zeros(shape=(stock_delivery_period + 1, share_count), dtype='float')

    return cash_delivery_queue, stock_delivery_queue


@njit(nogil=True, cache=True)  # 使用numba加速反而更慢，可能是因为函数体太简单，编译和调用开销大于计算开销
def process_backtest_delivery(cash_delivery_queue: np.ndarray,
                              stock_delivery_queue: np.ndarray,
                              is_new_day: bool,
                              day_num: int,
                              new_cash: float,
                              new_stocks: np.ndarray,
                              cash_delivery_period: int,
                              stock_delivery_period: int,
                              share_count: int) -> tuple[Any, np.ndarray]:
    """ 处理回测现金和股票交割队列，计算达到交割期的现金和股票，并更新可用现金和可用股票

    Parameters
    ----------
    cash_delivery_queue: np.ndarray
        现金交割队列
    stock_delivery_queue: np.ndarray
        股票交割队列
    is_new_day: bool
        是否为新的一天，用于判断是否需要更新交割队列
    day_num: int
        当前的天数，用于确定交割队列中的交割位置
    new_cash: float
        新增的现金，用于加入交割队列
    new_stocks: np.ndarray
        新增的股票，用于加入交割队列
    cash_delivery_period: int
        现金交割周期
    stock_delivery_period: int
        股票交割周期
    share_count: int
        股票数量

    Returns
    -------
    cash_delivery_queue: np.ndarray
        更新后的现金交割队列
    stock_delivery_queue: np.ndarray
        更新后的股票交割队列
    cash_delivered: float
        达到交割期的现金
    stocks_delivered: np.ndarray
        达到交割期的股票数量
    """

    # % 计算速度非常快，不需要区分is_new_day
    cash_in_pos = day_num % (cash_delivery_period + 1)
    stock_in_pos = day_num % (stock_delivery_period + 1)
    cash_delivery_pos = (day_num + 1) % (cash_delivery_period + 1)
    stock_delivery_pos = (day_num + 1) % (stock_delivery_period + 1)

    # if is_new_day:
    #     cash_delivery_queue[cash_in_pos] = new_cash
    #     stock_delivery_queue[stock_in_pos, :] = new_stocks
    # else:
    #     cash_delivery_queue[cash_in_pos] += new_cash
    #     stock_delivery_queue[stock_in_pos, :] += new_stocks

    if is_new_day or cash_delivery_period == 0:
        cash_delivery_queue[cash_in_pos] = new_cash
        cash_delivered = cash_delivery_queue[cash_delivery_pos]
    else:
        cash_delivery_queue[cash_in_pos] += new_cash
        cash_delivered = 0.0

    if is_new_day or stock_delivery_period == 0:
        stock_delivery_queue[stock_in_pos, :] = new_stocks
        stocks_delivered = stock_delivery_queue[stock_delivery_pos, :].copy()
    else:
        stock_delivery_queue[stock_in_pos, :] += new_stocks
        stocks_delivered = np.zeros(shape=(share_count,), dtype='float')

    return cash_delivered, stocks_delivered


@njit(nogil=True, cache=True)
def backtest_batch_steps(
        signal_types: np.ndarray,
        op_signals: np.ndarray,
        cash_investment_array: np.ndarray,
        cash_inflation_array: np.ndarray,
        delivery_day_indicators: np.ndarray,
        own_cashes: np.ndarray,
        own_amounts_array: np.ndarray,
        available_cashes: np.ndarray,
        available_amounts_array: np.ndarray,
        trade_prices: np.ndarray,
        trade_records_array: np.ndarray,
        trade_cost_array: np.ndarray,
        cost_params: np.ndarray,
        pt_buy_threshold: float,
        pt_sell_threshold: float,
        long_pos_limit: float,
        short_pos_limit: float,
        allow_sell_short: bool,
        moq_buy: float,
        moq_sell: float,
        cash_delivery_period: int,
        stock_delivery_period: int,
) -> None:
    """批量处理多次交易的回测计算

    输入数据为整个交易过程的交易信号、交易价格、初始持仓和现金等完整的持仓表，
    循环调用backtest_step()函数，同时处理现金和持仓的交割，完成整个交易清单的回测计算

    Parameters
    ----------
    signal_types: np.ndarray[int]
        信号类型数组，所有交易信号的类型代码
    op_signals: np.ndarray[float]
        交易信号数组，所有交易信号
    cash_investment_array: np.ndarray
        现金投资数组，记录每一个交易信号日的现金投资金额
    cash_inflation_array: np.ndarray
        现金增值数组，记录每一个交易信号日相对前一个交易信号日的现金增值幅度
    delivery_day_indicators: np.ndarray
        交割日指标数组，记录每一个交易信号日是否为新的交割日
    own_cashes: np.ndarray
        持有现金清单，完整记录整个回测过程中的持有现金
    own_amounts_array: np.ndarray
        持有资产清单，完整记录整个回测过程中的持有资产
    available_cashes: np.ndarray
        可用现金清单，完整记录整个回测过程中的可用现金
    available_amounts_array: np.ndarray
        可用资产清单，完整记录整个回测过程中的可用资产
    trade_prices: np.ndarray
        交易价格清单，记录每一个运行交易记录时间戳中的各个资产的交易价格
    trade_records_array: np.ndarray
        交易记录清单，完整记录整个回测过程中每只股票的买卖数量记录
    trade_cost_array: np.ndarray
        交易成本清单，完整记录整个回测过程中的交易成本
    cost_params: np.ndarray
        交易成本参数，包括买入费率、卖出费率、最低买入费用、最低卖出费用、交易滑点
        buy_rate: float, 交易成本：固定买入费率
        sell_rate: float, 交易成本：固定卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slipage: float, 交易成本：滑点
    pt_buy_threshold: float
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    pt_sell_threshold: float
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    long_pos_limit: float
        允许建立的多头总仓位与净资产的比值，默认值1.0，表示最多允许建立100%多头仓位
    short_pos_limit: float
        允许建立的空头总仓位与净资产的比值，默认值-1.0，表示最多允许建立100%空头仓位
    allow_sell_short: bool
        True:   允许买空卖空
        False:  默认值，只允许买入多头仓位
    moq_buy: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍
    moq_sell: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍
    cash_delivery_period: int
        现金交割周期
    stock_delivery_period: int
        股票交割周期

    Returns
    -------
    None,
    交易的结果会被填充到传入的数组中
        own_cashes: 最终持有现金清单，完整记录整个回测过程中的持有现金变动情况
        available_cashes: 可用现金清单，完整记录整个回测过程中的可用现金变动情况
        own_amounts_array: 最终持有资产清单，完整记录整个回测过程中的持有资产变动情况
        available_amounts_array: 可用资产清单，完整记录整个回测过程中的可用资产变动情况
        trade_records_array: 交易记录清单，完整记录整个回测过程中的每只股票的买卖数量记录
        trade_cost_array: 交易费用清单，完整记录整个回测过程中的交易费用

    """

    signal_count = op_signals.shape[0]
    share_count = op_signals.shape[1]
    # print(f'backtest started, total {signal_count} steps to process, got {share_count} shares in total\n'
    #       f'initial prices, cashes and stocks: \n'
    #       f'trade prices = \n{trade_prices}\n'
    #       f'own_cash = \n{own_cashes}\nown_amounts = \n{own_amounts_array} \n')

    cash_delivery_queue, stock_delivery_queue = initialize_backtest_delivery_queue(
            cash_delivery_period=cash_delivery_period,
            stock_delivery_period=stock_delivery_period,
            share_count=share_count,
    )
    day_nums = delivery_day_indicators.cumsum().astype('int')

    # 开始循环处理op_signal中的每一条交易信号，获取其signal_type，执行下列步骤：
    for i in range(signal_count):

        # print(f'Processing step {i}/{signal_count}, signal_type = {signal_types[i]}, '
        #       f'op_signal = {op_signals[i]}\n'
        #       f'trade_prices = {trade_prices[i]}\n')

        cash_investment = cash_investment_array[i]
        if cash_investment > 0:
            own_cashes[i] += cash_investment
            available_cashes[i] += cash_investment
            # DEBUG:
            # print(f'- cash investment added: {cash_investment}, new own_cash = {own_cashes[i]},'
            #       f' new available_cash = {available_cashes[i]}\n')

        is_delivery_day = bool(delivery_day_indicators[i])

        (own_cashes[i+1],
         available_cashes[i+1],
         own_amounts_array[i+1],
         available_amounts_array[i+1],
         trade_records_array[i],
         trade_cost_array[i],
         cash_delivery_queue,
         stock_delivery_queue) = backtest_step(
            signal_type=signal_types[i],
            op_signal=op_signals[i],
            cash_inflation=cash_inflation_array[i],
            is_delivery_day=is_delivery_day,
            day_num=day_nums[i],
            own_cash=own_cashes[i],
            own_amounts=own_amounts_array[i],
            available_cash=available_cashes[i],
            available_amounts=available_amounts_array[i],
            trade_prices=trade_prices[i],
            cost_params=cost_params,
            pt_buy_threshold=pt_buy_threshold,
            pt_sell_threshold=pt_sell_threshold,
            long_pos_limit=long_pos_limit,
            short_pos_limit=short_pos_limit,
            allow_sell_short=allow_sell_short,
            moq_buy=moq_buy,
            moq_sell=moq_sell,
            cash_delivery_queue=cash_delivery_queue,
            stock_delivery_queue=stock_delivery_queue,
            cash_delivery_period=cash_delivery_period,
            stock_delivery_period=stock_delivery_period,
            share_count=share_count,
        )

    # 完成全部交易信号的处理后，输出最终的持有现金清单、持有资产清单和交易费用清单
    return None


def _get_complete_hist(looped_value: pd.DataFrame,
                       h_list: HistoryPanel,
                       benchmark_list: pd.DataFrame,
                       with_price: bool = False) -> pd.DataFrame:
    """完成历史交易回测后，填充完整的历史资产总价值清单，
        同时在回测清单中填入参考价格数据，参考价格数据用于数据可视化对比，参考数据的来源为Config.benchmark_asset

    Parameters
    ----------
    looped_value: pd.DataFrame
        完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
    h_list: pd.DataFrame
        完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
    benchmark_list: pd.DataFrame
        参考资产的历史价格清单，参考资产用于收益率的可视化对比，同时用于计算alpha、sharp等指标
    with_price: boolean, default False
        True时在返回的清单中包含历史价格，否则仅返回资产总价值

    Returns
    -------
    looped_value: pd.DataFrame:
    重新填充的完整历史交易日资产总价值清单，包含以下列：
    - [share-x]:        多列，每种投资产品的持有份额数量
    - cash:             期末现金金额
    - fee:              当期交易费用（交易成本）
    - value:            当期资产总额（现金总额 + 所有在手投资产品的价值总额）
    """
    # 获取价格清单中的投资产品列表
    shares = h_list.shares  # 获取资产清单
    try:
        start_date = looped_value.index[0]  # 开始日期
    except:
        raise IndexError('index 0 is out of bounds for axis 0 with size 0')
    looped_history = h_list.segment(start_date)  # 回测历史数据区间 = [开始日期:]
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    hdates = looped_history.hdates
    purchased_shares = looped_value[shares].reindex(hdates, method='ffill').fillna(0)
    cashes = looped_value['cash'].reindex(hdates, method='ffill').fillna(0)
    fees = looped_value['fee'].reindex(hdates).fillna(0)
    looped_value = looped_value.reindex(hdates)
    # 这里采用了一种看上去貌似比较奇怪的处理方式：
    # 先为cashes、purchased_shares两个变量赋值，
    # 然后再将上述两个变量赋值给looped_values的列中
    # 这样看上去好像多此一举，为什么不能直接赋值，然而
    # 经过测试，如果直接用下面的代码直接赋值，将无法起到
    # 填充值的作用：
    # looped_value.cash = looped_value.cash.reindex(dates, method='ffill')
    looped_value[shares] = purchased_shares
    looped_value.cash = cashes
    looped_value.fee = looped_value['fee'].reindex(hdates).fillna(0)
    looped_value['reference'] = benchmark_list.reindex(hdates).fillna(0)
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象，如果looped_history历史价格中包含多种价格，使用最后一种
    decisive_prices = looped_history[-1].squeeze(axis=2).T
    looped_value['value'] = (decisive_prices * looped_value[shares]).sum(axis=1) + looped_value['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        share_price_column_names = [name + '_p' for name in shares]
        looped_value[share_price_column_names] = looped_history[shares]
    return looped_value


def process_loop_results(operator,
                         loop_results=None,
                         op_log_matrix=None,
                         op_summary_matrix=None,
                         op_list_bt_indices=None,
                         trade_log=False,
                         bt_price_priority_ohlc: str = 'OHLC'):
    """ 接受apply_loop函数传回的计算结果，生成DataFrame型交易模拟结果数据，保存交易记录，并返回结果供下一步处理

    Parameters
    ----------
    operator: Operator
        交易操作对象
    loop_results: tuple, optional
        apply_loop函数返回的计算结果
    op_log_matrix: np.ndarray, optional
        交易记录矩阵，记录了模拟交易过程中每一笔交易的详细信息
    op_summary_matrix: np.ndarray, optional
        交易汇总矩阵，记录了模拟交易过程中每一笔交易的汇总信息
    op_list_bt_indices: list, optional
        交易记录矩阵中的交易日期索引
    trade_log: bool, optional, default False
        是否保存交易记录，默认为False
    bt_price_priority_ohlc: str, optional, default 'OHLC'
        交易记录中的价格优先级，可选'OHLC'、'HLOC'、'LOCH'、'LCOH'、'COHL'、'COLH'

    Returns
    -------
    value_history: pd.DataFrame
        交易模拟结果数据
    """
    from qteasy import logger_core
    amounts_matrix, cashes, fees, values = loop_results
    shares = operator.op_list_shares
    complete_loop_dates = operator.op_list_hdates
    looped_dates = [complete_loop_dates[item] for item in op_list_bt_indices]

    price_types_in_priority = operator.get_bt_price_types_in_priority(priority=bt_price_priority_ohlc)

    # 将向量化计算结果转化回DataFrame格式
    value_history = pd.DataFrame(amounts_matrix, index=looped_dates,
                                 columns=shares)
    # 填充标量计算结果
    value_history['cash'] = cashes
    value_history['fee'] = fees
    value_history['value'] = values

    # 生成trade_log，index为MultiIndex，因为每天的交易可能有多种价格
    if trade_log:
        from .core import get_basic_info
        # create complete trading log
        logger_core.info(f'generating complete trading log ...')
        op_log_index = pd.MultiIndex.from_product(
                [looped_dates,
                 price_types_in_priority,
                 ['0, trade signal',
                  '1, price',
                  '2, traded amounts',
                  '3, cash changed',
                  '4, trade cost',
                  '5, own amounts',
                  '6, available amounts',
                  '7, summary']],
                names=('date', 'trade_on', 'item')
        )
        op_sum_index = pd.MultiIndex.from_product(
                [looped_dates,
                 price_types_in_priority,
                 ['7, summary']],
                names=('date', 'trade_on', 'item')
        )
        op_log_columns = [str(s) for s in shares]
        op_log_df = pd.DataFrame(op_log_matrix, index=op_log_index, columns=op_log_columns)
        op_summary_df = pd.DataFrame(op_summary_matrix,
                                     index=['add. invest', 'own cash', 'available cash', 'value'],
                                     columns=op_sum_index).T
        log_file_path_name = os.path.join(qteasy.QT_TRADE_LOG_PATH, 'trade_log.csv')
        op_summary_df.join(op_log_df, how='right', sort=False).to_csv(log_file_path_name, encoding='utf-8')

        # 生成 trade log 摘要表 (a more concise and human-readable format of trading log
        # create share trading logs:
        logger_core.info(f'generating abstract trading log ...')
        share_logs = []
        for share in op_log_columns:
            share_df = op_log_df[share].unstack()
            share_df = share_df[share_df['2, traded amounts'] != 0]
            share_df['code'] = share
            try:
                share_name = get_basic_info(share, printout=False)['name']
            except Exception as e:
                share_name = 'unknown'
            share_df['name'] = share_name
            share_logs.append(share_df)

        re_columns = ['code',
                      'name',
                      '0, trade signal',
                      '1, price',
                      '2, traded amounts',
                      '3, cash changed',
                      '4, trade cost',
                      '5, own amounts',
                      '6, available amounts',
                      '7, summary']
        op_log_shares_abs = pd.concat(share_logs).reindex(columns=re_columns)
        record_file_path_name = os.path.join(qteasy.QT_TRADE_LOG_PATH, 'trade_records.csv')
        # TODO: 可以增加一个config属性来控制交易摘要表的生成规则：
        #  如果how == 'left' 保留无交易日期的记录
        #  如果how == 'right', 不显示无交易日期的记录
        op_summary_df.join(op_log_shares_abs, how='right', sort=True).to_csv(record_file_path_name, encoding='utf-8')

    return value_history
