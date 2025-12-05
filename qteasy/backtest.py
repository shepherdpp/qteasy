# coding=utf-8
# ======================================
# File:     backtest.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-03-12
# Desc:
#   Functions used for backtesting.
# ======================================

import logging
import time
import pandas as pd
import numpy as np
from numba import njit
from typing import Any, Union, Optional

from numpy import bool_, dtype, ndarray
from pandas import DataFrame

from qteasy.utilfuncs import str_to_list

from qteasy.qt_operator import (
    Operator,
    SIGNAL_TYPE_ID,
)

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

    # 4, 更新持有现金和可用现金
    next_own_cash = own_cash + cash_gained.sum() + cash_spent.sum()
    next_available_cash = available_cash + delivered_cash + cash_spent.sum()
    # 更新持有资产和可用资产
    next_own_amounts = own_amounts + amount_purchased + amount_sold
    next_available_amounts = available_amounts + delivered_stocks + amount_sold

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
        trade_records_array: 交易记录清单，完整记录整个回测过程中的每只股票的买卖数量变动记录
        trade_cost_array: 交易费用清单，完整记录整个回测过程中的交易费用

    """

    signal_count = op_signals.shape[0]
    share_count = op_signals.shape[1]
    # 初始化现金和股票交割队列以及交割日计数器
    cash_delivery_queue, stock_delivery_queue = initialize_backtest_delivery_queue(
            cash_delivery_period=cash_delivery_period,
            stock_delivery_period=stock_delivery_period,
            share_count=share_count,
    )
    day_nums = delivery_day_indicators.cumsum().astype('int')

    # 开始循环处理op_signal中的每一条交易信号，获取其signal_type，执行下列步骤：
    for i in range(signal_count):
        # 如果当期有现金投资，则更新持有现金和可用现金
        cash_investment = cash_investment_array[i]
        if cash_investment > 0:
            own_cashes[i] += cash_investment
            available_cashes[i] += cash_investment

        is_delivery_day = bool(delivery_day_indicators[i])

        # 调用backtest_step函数，计算本次交易的现金变动、持仓变动和交易费用
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


# 定义一个Backtester类，该类包含一个operator对象，同时包含与operator回测相关的所有属性，同时提供回测结果的生成方法
class Backtester:
    """ Backtester类用于对operator对象进行回测操作。
    本类的属性包括回测计算中所需的所有参数，包括回测过程中产生的结果数据，这些结果数据以ndarray的形式
    在对象的生命周期内长期保存，并可以反复刷新。

    这个类只有在operator对象被创建之后才能被实例化，因为Backtester类需要依赖operator对象来生成交易
    信号和执行交易。典型用法如下：
    ```
        operator = Operator( ... )  # 创建Operator对象
        backtested = Operator.backtest( signal_count=100, share_count=10, **kwargs)  # 创建Backtester对象
        # get backtest raw results:
        backtested.cash_investment_array
        backtested.own_cashes
        ...
        # get backtest results as DataFrame:
        result_df = backtested.value_records()
        trade_log_df = backtested.trade_logs()
        trade_summary_df = backtested.trade_summary()
    ```

    Attributes
    ----------
    op: Operator
        交易操作对象，包含交易信号生成和交易执行的逻辑

    """

    def __init__(self,
                 op: Operator,
                 shares: list[str],
                 cash_investment_array: np.ndarray,
                 cash_inflation_array: np.ndarray,
                 delivery_day_indicators: np.ndarray,
                 cost_params: np.ndarray,  # 交易成本参数
                 signal_parsing_params: dict,  # 交易信号解析参数
                 trading_moq_params: dict,  # 交易最小单位参数
                 trading_delivery_params: dict,  # 交易交割参数
                 trade_price_data: np.ndarray,  # 交易价格数据
                 logger: Optional[logging.Logger] = None):
        """ 初始化Backtester对象，设置operator对象和回测参数，初始化回测结果存储表格

        Parameters
        ----------
        op: Operator
            交易操作对象，包含交易信号生成和交易执行的逻辑
        shares: list[str]
            交易标的列表，包含所有交易标的的代码
        cash_investment_array: np.ndarray
            现金投资数组，记录每一个交易信号日的现金投资金额
        cash_inflation_array: np.ndarray
            现金增值数组，记录每一个交易信号日相对前一个交易信号日的现金增值幅度
        delivery_day_indicators: np.ndarray
            交割日指标数组，记录每一个交易信号日是否为新的交割日
        cost_params: np.ndarray
            交易成本参数，包括买入费率、卖出费率、最低买入费用、最低卖出费用、交易滑点
            buy_rate: float, 交易成本：固定买入费率
            sell_rate: float, 交易成本：固定卖出费率
            buy_min: float, 交易成本：最低买入费用
            sell_min: float, 交易成本：最低卖出费用
            slipage: float, 交易成本：滑点
        signal_parsing_params: dict
            交易信号解析参数字典，包含解析交易信号所需的所有参数，通常是parse_signal_parsing_params()函数的输出
        trading_moq_params: dict
            交易最小单位参数字典，包含交易最小单位相关的所有参数，通常是parse_trading_moq_params()函数的输出
        trading_delivery_params: dict
            交易交割参数字典，包含交易交割相关的所有参数，通常是parse_trading_delivery_params()函数的输出
        trade_price_data: np.ndarray
            交易价格数据，记录每一个运行交易记录时间戳中的各个资产的交易价格
        logger: Optional[logging.Logger]
            可选的日志记录器对象，用于记录回测过程中的日志信息
        """

        # 参数基础校验
        assert isinstance(op, Operator), "op must be an instance of Operator"
        if isinstance(shares, str):
            shares = str_to_list(shares)
        assert isinstance(shares, list) and all(isinstance(s, str) for s in shares), "shares must be a list of strings"

        self.op = op
        self.op_signals: Optional[np.ndarray] = None  # 回测生成的交易信号表格，实际上在op内也可以存储
        self.shares = shares
        self.cash_investment_array = cash_investment_array
        self.cash_inflation_array = cash_inflation_array
        self.delivery_day_indicators = delivery_day_indicators
        self.cost_params = cost_params
        self.signal_parsing_params = signal_parsing_params
        self.trading_moq_params = trading_moq_params
        self.trading_delivery_params = trading_delivery_params
        self.trade_price_data = trade_price_data
        self.logger = logger

        self.op_run_time = 0.0  # operator运行时间，单位秒
        self.backtest_run_time = 0.0  # 回测运行时间，单位秒

        # 1，检查operator对象是否已经准备好，否则raise error, TOOD: 是否有必要？
        # op.is_ready(raise_error=True)
        if logger is not None:
            logger.info('Start backtest operator...')

        # 2，从operator对象读取交易运行计划和时间表，获取交易信号长度，生成用于存储交易信号和持仓数据的表格
        self.op_schedule = op.group_timing_table.index
        self.n_signals = op.get_signal_count()
        self.share_count = len(shares)

        # 参数一致性校验
        arrays_to_check = [
            ("cash_investment_array", self.cash_investment_array, (self.n_signals,)),
            ("cash_inflation_array", self.cash_inflation_array, (self.n_signals,)),
            ("delivery_day_indicators", self.delivery_day_indicators, (self.n_signals,)),
            ("trade_price_data", self.trade_price_data, (self.n_signals, self.share_count))
        ]
        for name, arr, shape in arrays_to_check:
            if not isinstance(arr, np.ndarray):
                raise TypeError(f"{name} must be a numpy array")
            if arr.shape != shape:
                raise ValueError(f"{name} should have shape {shape}, but got {arr.shape}")

        # 3.1 现金和股票持仓历史记录表
        shape_assets = (self.n_signals + 1, self.share_count)
        shape_cashes = (self.n_signals + 1,)
        self.own_cashes = np.zeros(shape=shape_cashes, dtype=float)
        self.own_amounts_array = np.zeros(shape=shape_assets, dtype=float)
        self.available_cashes = np.zeros(shape=shape_cashes, dtype=float)
        self.available_amounts_array = np.zeros(shape=shape_assets, dtype=float)

        # 3.2 交易过程数据记录表，包括交易记录、交易成本等
        shape_signals = (self.n_signals, self.share_count)
        self.trade_records_array = np.zeros(shape_signals, dtype=float)
        self.trade_cost_array = np.zeros(shape_signals, dtype=float)

        # 4, 交易日志和交易汇总记录
        self.trade_log_df: Optional[pd.DataFrame] = None
        self.summary_df: Optional[pd.DataFrame] = None

    def run(self) -> 'Backtester':
        """ 执行回测计算，生成回测结果数据并存入对象属性中"""

        # 4，如果operator的交易信号不依赖于回测数据，调用函数backtest_operator_independently()处理回测信号
        if self.op.check_dynamic_data():
            if self.logger is not None:
                self.logger.info('Backtest operator with dynamic data dependence...')
            signals = self._backtest_static_operator()
        # 5，如果operator的交易信号依赖于回测数据，调用函数backtest_operator_dependently()处理回测信号
        else:
            if self.logger is not None:
                self.logger.info('Backtest operator without dynamic data dependence...')
            signals = self._backtest_dynamic_operator()

        self.op_signals = signals
        if self.logger is not None:
            self.logger.info('Backtest completed.')

        return self

    def _backtest_static_operator(self) -> np.ndarray:
        """处理operator的交易信号仅包含静态数据类型（不依赖交易结果的数据）的情况:

        """
        # 1，调用operator.run()生成完整的交易信号清单，并计算保存运行时间
        stypes = np.zeros(self.op.get_signal_count(), dtype=int)
        s_indices = np.zeros(self.op.get_signal_count(), dtype=int)
        signals = np.zeros((self.op.get_signal_count(), self.share_count), dtype=float)
        signal_index = 0

        st = time.time()
        for stype, s_index, signal in self.op.run_strategies(steps=range(len(self.op.group_timing_table))):
            stypes[signal_index] = SIGNAL_TYPE_ID[stype]
            s_indices[signal_index] = s_index
            signals[signal_index, :] = signal
            signal_index += 1
        et = time.time()
        self.op_run_time = et - st

        # 2，调用backtest_batch_steps()进行回测，填充回测结果清单
        st = time.time()
        backtest_batch_steps(
                signal_types=stypes,
                op_signals=signals,
                cash_investment_array=self.cash_investment_array,
                cash_inflation_array=self.cash_inflation_array,
                delivery_day_indicators=self.delivery_day_indicators,
                own_cashes=self.own_cashes,
                available_cashes=self.available_cashes,
                own_amounts_array=self.own_amounts_array,
                available_amounts_array=self.available_amounts_array,
                trade_prices=self.trade_price_data,
                trade_records_array=self.trade_records_array,
                trade_cost_array=self.trade_cost_array,
                cost_params=self.cost_params,
                **self.signal_parsing_params,
                **self.trading_moq_params,
                **self.trading_delivery_params,
        )
        et = time.time()
        self.backtest_run_time = et - st

        return signals

    def _backtest_dynamic_operator(self) -> np.ndarray:
        """处理operator的交易信号包含动态数据类型(依赖交易结果的数据类型)的情况:

        根据输入参数逐步调用operator.run()生成交易信号清单，然后调用backtest_batch_steps()进行回测"""

        # 1，读取初始持仓和现金数据，更新operator中的依赖性历史数据
        initial_trade_records = self.trade_records_array[0, :].copy()
        initial_trade_costs = self.trade_cost_array[0, :].copy()
        initial_trade_prices = self.trade_price_data[0, :].copy()
        signals = np.zeros((self.op.get_signal_count(), self.share_count), dtype=float)

        self.op.prepare_dynamic_data_buffer(
                trade_records=initial_trade_records,
                trade_costs=initial_trade_costs,
                trade_prices=initial_trade_prices,
        )

        cash_delivery_queue, stock_delivery_queue = initialize_backtest_delivery_queue(
                share_count=self.share_count,
                **self.trading_delivery_params,
        )
        day_nums = self.delivery_day_indicators.cumsum()

        st = time.time()
        # 循环执行下面步骤，直至完整生成回测结果清单
        for i in range(self.op.get_signal_count()):

            # 1，判断是否有资金投入，如果有，更新持有现金和可用现金
            cash_investment = self.cash_investment_array[i]
            if cash_investment > 0:
                self.own_cashes[i] += cash_investment
                self.available_cashes[i] += cash_investment

            # 2，调用operator.run_strategy()生成当前交易信号
            stype, s_index, signal = tuple(self.op.run_strategy(step_index=i))[0]
            is_delivery_day = bool(self.delivery_day_indicators[i])
            signals[i, :] = signal

            # 3，调用backtest_step()回测当前交易信号的结果，生成当前交易回测结果
            (
                self.own_cashes[i + 1],
                self.available_cashes[i + 1],
                self.own_amounts_array[i + 1],
                self.available_amounts_array[i + 1],
                self.trade_records_array[i],
                self.trade_cost_array[i],
                cash_delivery_queue,
                stock_delivery_queue,
            ) = backtest_step(
                    signal_type=stype,
                    op_signal=signal,
                    cash_inflation=self.cash_inflation_array[i],
                    is_delivery_day=is_delivery_day,
                    day_num=day_nums[i],
                    own_cash=self.own_cashes[i],
                    own_amounts=self.own_amounts_array[i, :],
                    available_cash=self.available_cashes[i],
                    available_amounts=self.available_amounts_array[i, :],
                    trade_prices=self.trade_price_data[i, :],
                    cost_params=self.cost_params,
                    **self.signal_parsing_params,
                    **self.trading_moq_params,
                    **self.trading_delivery_params,
            )

            # 4，更新operator中的依赖性历史数据
            self.op.prepare_dynamic_data_buffer(
                    trade_records=self.trade_records_array[i],
                    trade_costs=self.trade_cost_array[i],
                    trade_prices=self.trade_price_data[i],
            )

        et = time.time()
        self.op_run_time = et - st
        self.backtest_run_time = et - st

        # 5，返回signals，因为完整的回测结果清单已经保存在作为参数传入的几个数组中
        return signals

    # 生成更加易于阅读的DataFrame型交易结果数据，以便用于结果的评价及后续处理，

    def trade_result_df(self) -> pd.DataFrame:
        """ 根据回测结果生成资产价值记录，输出内容为DataFrame格式

        Returns
        -------
        value_history: pd.DataFrame
            交易模拟结果数据
        """
        value_history = pd.DataFrame(self.own_amounts_array[1:],
                                     index=self.op_schedule,
                                     columns=self.shares)
        # 填充标量计算结果
        value_history['cash'] = self.own_cashes[1:]
        value_history['value'] = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]
        value_history['fee'] = self.trade_cost_array.sum(axis=1)

        return value_history

    # 根据回测结果生成交易日志，包含更加完整的交易记录，输出内容为DataFrame格式，并且可以保存为csv文件
    def generate_trade_logs(
            self,
            save_to_file_path: Union[str, None] = None,
    ) -> DataFrame:
        """ 根据回测结果生成交易日志，交易日志是一份完整的交易记录文件，包含每一个交易期间的下列信息：
            每一个交易期间包含8行数据，分别为：
                '0, trade signal', 每一支股票的当期交易信号
                '1, price', 每一支股票的当期交易价格
                '2, traded amounts', 每一支股票的当期交易数量，如果没有交易则为0
                '3, cash changed', 每一支股票的当期现金变动金额，买入为负数，卖出为正数
                '4, trade cost', 每一支股票的当期交易费用
                '5, own amounts', 每一支股票的当期末持有数量
                '6, available amounts', 每一支股票的当期末可用数量
                '7, summary', 当期每一支股票的持仓价值，同时包含汇总数据：当期末持有现金、可用现金、总资产价值
            交易日志文件可以被保存为csv格式，文件名为'trade_log.csv'

        Parameters
        ----------
        save_to_file_path: str, optional
            如果提供了文件路径，则将交易日志保存为CSV文件，默认值为None

        Returns
        -------
        trade_log: pd.DataFrame
            交易模拟结果数据
        """
        if self.logger:
            # create share trading logs:
            self.logger.info(f'generating detailed trading log ...')
        if self.share_count == 0:
            raise ValueError('shares list is empty, cannot create trade logs!')

        # 生成 trade log 详细表的股票持仓变化详情部分 （每支股票每期的交易信号、价格、交易数量、交易费用、期末持有数量、期末可用数量、持仓价值等）
        trade_signal_df = pd.DataFrame(self.op_signals, index=self.op_schedule, columns=self.shares)
        trade_price_df = pd.DataFrame(self.trade_price_data, index=self.op_schedule, columns=self.shares)
        own_amounts_df = pd.DataFrame(self.own_amounts_array[1:], index=self.op_schedule, columns=self.shares)
        available_amounts_df = pd.DataFrame(self.available_amounts_array[1:], index=self.op_schedule, columns=self.shares)
        trade_records_df = pd.DataFrame(self.trade_records_array, index=self.op_schedule, columns=self.shares)
        trade_cost_df = pd.DataFrame(self.trade_cost_array, index=self.op_schedule, columns=self.shares)
        cash_changed_df = pd.DataFrame(-trade_price_df * trade_records_df - self.trade_cost_array, index=self.op_schedule, columns=self.shares)
        amounts_value_df = pd.DataFrame(trade_price_df * self.own_amounts_array[1:], index=self.op_schedule, columns=self.shares)

        combined_data = pd.concat(
                objs=[trade_signal_df,
                      trade_price_df,
                      trade_records_df,
                      cash_changed_df,
                      trade_cost_df,
                      own_amounts_df,
                      available_amounts_df,
                      amounts_value_df, ],
                keys=['0, trade signal',
                      '1, price',
                      '2, traded amounts',
                      '3, cash changed',
                      '4, trade cost',
                      '5, own amounts',
                      '6, available amounts',
                      '7, summary'],
        )
        combined_data = combined_data.reorder_levels([1, 0]).sort_index(level=0)

        # 生成 trade log 详细表的每期汇总数据部分（当期现金投入、期末持有现金、期末可用现金、期末总价值）
        add_investments = pd.Series(self.cash_investment_array, index=self.op_schedule, name='add. invest')
        own_cash_series = pd.Series(self.own_cashes[1:], index=self.op_schedule, name='own cash')
        available_cash_series = pd.Series(self.available_cashes[1:], index=self.op_schedule, name='available cash')
        total_values = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]

        total_value_series = pd.Series(total_values, index=self.op_schedule, name='value')

        self.summary_df = pd.concat(
                objs=[add_investments,
                      own_cash_series,
                      available_cash_series,
                      total_value_series],
                axis=1,
        )
        summary_index = pd.MultiIndex.from_product(
                [self.summary_df.index,
                    ['7, summary']],
        )
        self.summary_df.index = summary_index
        self.trade_log_df = self.summary_df.join(combined_data, how='outer', sort=False)

        if save_to_file_path is not None:
            self.trade_log_df.to_csv(save_to_file_path, encoding='utf-8')
            if self.logger:
                self.logger.info(f'trade log saved to {save_to_file_path}')

        return self.trade_log_df

    # 根据回测结果生成交易汇总表，输出内容为DataFrame格式，并且可以保存为csv文件
    def generate_trade_summary(
            self,
            share_names: Union[list[str], None] = None,
            save_to_file_path: Union[str, None] = None,
    ) -> pd.DataFrame:
        """ 生成 trade summary 交易摘要表 (一个更加紧凑的交易汇总表，包含每次交易的关键信息，
        以一种更加易于人类阅读的方式呈现，并过滤掉无交易的记录)，函数的输入trade_log_df是函数
        generate_trade_logs()的返回值。

        Parameters
        ----------
        share_names: list[str], optional
            交易标的名称列表, 如果为None，则使用“N/A”作为名称
        save_to_file_path: str, optional
            如果提供了文件路径，则将交易摘要表保存为CSV文件，默认值为None，不保存文件
        """

        if self.logger is not None:
            # create share trading logs:
            self.logger.info(f'generating abstract trading log ...')
        if self.share_count == 0:
            raise ValueError('shares list is empty, cannot create trade summary!')
        if any(share not in self.trade_log_df.columns for share in self.shares):
            missing_share = [share for share in self.shares if share not in self.trade_log_df.columns]
            raise KeyError(f'some shares ({missing_share}) are not in trade_log_df columns, cannot create trade summary!')
        # 处理share_names
        if share_names is None:
            share_names = ['N/A' for _ in self.shares]

        share_logs = []
        for share, share_name in zip(self.shares, share_names):
            share_df = self.trade_log_df[share].unstack()
            share_df = share_df[share_df['2, traded amounts'] != 0]
            share_df['code'] = share
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
        self.summary_df.index = self.summary_df.index.levels[0]
        self.summary_df = self.summary_df.join(op_log_shares_abs, how='right', sort=True)

        if save_to_file_path is not None:
            self.summary_df.to_csv(save_to_file_path, encoding='utf-8')
            if self.logger is not None:
                self.logger.info(f'trade summary saved to {save_to_file_path}')

        return self.summary_df
