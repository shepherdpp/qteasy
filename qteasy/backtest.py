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

from qteasy.finance import CashPlan

from qteasy.utilfuncs import (
    str_to_list,
    FunctionTimer,
)

from qteasy.qt_operator import (
    Operator,
    SIGNAL_TYPE_ID,
)

from qteasy.evaluate import (
    evaluate,
)

from qteasy.finance import (
    apply_execution_slippage,
    get_selling_result,
    get_purchase_result,
)

from qteasy.visual import (
    _plot_loop_result,
    _loop_report_str,
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
        slippage: float, 交易成本：交易滑点
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
        # DEBUG
        # print(f'cash inflation applied: {cash_inflation:.4f}, new own_cash: {own_cash:.2f},
        # new available_cash: {available_cash:.2f}')

    # print(f'\ncalculating trade results for day {day_num}, signal_type: {signal_type}, op_signal: {op_signal}')
    # if day_num == 1781:
    #     import pdb; pdb.set_trace()
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
            moq_sell=moq_sell,
            cash_delivery_period=cash_delivery_period,
    )
    # DEBUG
    # print(f'calculated trade results'
    #       f'own_cash: {own_cash:.5f}, own_amounts: {own_amounts.round(6)}, \n'
    #       f'available_cash: {available_cash:.5f}, available_amounts: {available_amounts.round(6)}\n'
    #       f'trade results - cash_gained: {cash_gained.sum():.5f}, cash_spent: {cash_spent.sum():.5f}, '
    #       f'amount_purchased: {amount_purchased.sum():.5f}, amount_sold: {amount_sold.sum():.5f}, '
    #       f'fees: {fees.sum():.5f}')

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
    # DEBUG
    # print(f'\nprocessing delivery for day {day_num}, is_delivery_day: {is_delivery_day}\n'
    #       f'cash delivery queue: {cash_delivery_queue.round(6)}, stock delivery queue: '
    #       f'{stock_delivery_queue.round(6)}\n delivered_cash: {delivered_cash:.2f}, '
    #       f'delivered_stocks: {delivered_stocks}')

    # 4, 更新持有现金和可用现金
    next_own_cash = np.round(own_cash + cash_gained.sum() + cash_spent.sum(), 3)
    next_available_cash = np.round(available_cash + delivered_cash + cash_spent.sum(), 3)
    # DEBUG
    # print(f'updating cash for day {day_num}, \n'
    #       f'own_cash: {own_cash:.2f} + cash_gained: {cash_gained.sum():.2f} + cash_spent: '
    #       f'{cash_spent.sum():.2f} = next_own_cash: {next_own_cash:.2f}\n'
    #       f'available_cash: {available_cash:.2f} + delivered_cash: {delivered_cash:.2f} + cash_spent: '
    #       f'{cash_spent.sum():.2f} = next_available_cash: {next_available_cash:.2f}')
    # 更新持有资产和可用资产
    next_own_amounts = np.round(own_amounts + amount_purchased + amount_sold, 3)
    next_available_amounts = np.round(available_amounts + delivered_stocks + amount_sold, 3)
    # DEBUG
    # print(f'updating amounts for day {day_num}, \n'
    #       f'own_amounts: {own_amounts.round(6)} + amount_purchased: {amount_purchased} + amount_sold: '
    #       f'{amount_sold} = next_own_amounts: {next_own_amounts.round(6)}\n'
    #       f'available_amounts: {available_amounts.round(6)} + delivered_stocks: {delivered_stocks} + amount_sold: '
    #       f'{amount_sold} = next_available_amounts: {next_available_amounts.round(6)}')

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


@njit(cache=True, nogil=True)
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
        cash_delivery_period: int,
) -> tuple[ndarray, ndarray, ndarray, ndarray, ndarray]:
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
        buy_rate: float, 交易成本：固定买入费率
        sell_rate: float, 交易成本：固定卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slippage: float, 交易成本：滑点
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
        # DEBUG
        # print(f'parsed PT signals, trimmed_op_signal: {trimmed_op_signal.round(3)}, \n'
        #       f'cash_to_spend: {cash_to_spend.round(2)}, amounts_to_sell: {amounts_to_sell.round(2)}')

    elif signal_type == 1:  # PS信号
        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=op_signal,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=allow_sell_short
        )
        # 如果是全零信号，则直接返回空结果
        if np.allclose(cash_to_spend, 0.) and np.allclose(amounts_to_sell, 0.):
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
        if np.allclose(cash_to_spend, 0.) and np.allclose(amounts_to_sell, 0.):
            return (empty_array,
                    empty_array,
                    empty_array,
                    empty_array,
                    empty_array)

    else:
        raise ValueError('Invalid signal_type')
    # # 这里还需要考虑交易价格为NaN的情况，如果价格为NaN，则不进行交易，直接将交易计划中的买入金额和卖出数量调整为0
    # cash_to_spend = np.where(np.isnan(prices), 0, cash_to_spend)
    # amounts_to_sell = np.where(np.isnan(prices), 0, amounts_to_sell)

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

    # DEBUG
    # print(f'Processed signals, calculated and adjusted'
    #       f'\ncash_to_spend: {cash_to_spend.round(2)}, \namounts_to_sell: {amounts_to_sell.round(2)}')
    # 4，批量提交股份卖出计划，计算实际卖出份额和交易费用
    amount_sold, cash_gained, fee_selling = get_selling_result(
            prices=prices,
            a_to_sell=amounts_to_sell,
            moq=moq_sell,
            cost_params=cost_params,
    )
    # DEBUG
    # print(f'calculated amount sell result:\n'
    #       f'amount sold: {amount_sold.round(2)}\n'
    #       f'cash gained: {cash_gained.round(2)}')

    if np.allclose(cash_to_spend, 0.0, atol=0.001):
        # 如果所有买入计划绝对值都小于1分钱，则直接跳过后续的计算
        return cash_gained, empty_array, empty_array, amount_sold, fee_selling

    # 5，根据可用现金数量或多空持仓限额调整买入计划

    # 如果不允许卖空交易，则根据可用现金调整买入计划，确保买入总金额不超过可用现金。
    # 此时自动保证交易后的持仓比例在0～1之间。
    if not allow_sell_short:
        # 对于 PT 信号，在现金交割周期为 0 时，可以在同一回测步中复用本期卖出获得的现金，
        # 从而更好地贴合“目标仓位一次性调仓”的语义；对于 PS / VS 信号，始终仅使用期初可用现金。
        if signal_type == 0 and cash_delivery_period == 0:
            effective_available_cash = available_cash + cash_gained.sum()
        else:
            effective_available_cash = available_cash
        # 忽略cash_to_spend中的空头买入部分（不允许卖空时无意义）
        cash_to_spend = np.where(cash_to_spend > 0.001, cash_to_spend, 0)
        # DEBUG
        # print(f'cash_to_spend adjusted, {cash_to_spend.round(6)} = np.where(cash_to_spend > 0.001,
        # cash_to_spend, 0)\n')
        # 确保总现金买入金额不超过有效可用现金，如果超过则按比例调降
        if cash_to_spend.sum() > effective_available_cash:
            cash_to_spend *= effective_available_cash / cash_to_spend.sum()
            # DEBUG
            # print(f'cash_to_spend adjusted by available_cash, cash_to_spend: {cash_to_spend.round(6)}, *= '
            #       f'available_cash: {available_cash:.2f} / cash_to_spend.sum(): {cash_to_spend.sum():.2f}\n')

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
    # DEBUG
    # print(f'calculated purchase result: \namount_purchased: {amount_purchased.round(2)}'
    #       f'cash_spent: {cash_spent}')

    # 4, 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = fee_buying + fee_selling
    apply_execution_slippage(
            prices, amount_purchased, amount_sold, cash_spent, cash_gained, fee, cost_params[4],
    )
    # DEBUG
    # print(f'finished calculation: \n'
    #       f'cash_gained: {cash_gained.round(2)}\n'
    #       f'amount_sold: {amount_sold.round(2)}\n'
    #       f'amount_purchased: {amount_purchased.round(2)}'
    #       f'cash_spent: {cash_spent}\n'
    #       f'fee: {fee.round(2)}\n')

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

    此处需要非常注意区分：股现交割的时机是发生在交易完成前还是交易完成后，因为两种时机意味着
     交割判断是不同的。如果交割发生在交易完成前，那么在“换日”判断基于上一次交易是否与本次交易日期一
     致，如果不一致实际上处理的是前一日的交易结果，此时应该直接进行交割换日。
     但是如果在交易后执行交割，则“换日”判断基于下一次交易是否与本次交易日期一致，将本次交易结果加入
     交割队列后，当下一次交易换日时，才会进行交割换日。
     上述两种交割处理不同，在目前的实现中，交割发生在交易完成后，因此“换日”判断基于下一次交易是否
     与本次交易日期一致。应该按照交易后交割形式实现。

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

    if cash_delivery_period == 0:
        cash_delivered = new_cash
    else:
        # 计算交割队列的起始位置，将新增现金加入交割队列起始位置
        cash_in_pos = day_num % cash_delivery_period
        cash_delivery_queue[cash_in_pos] += new_cash
        if is_new_day:
            # 如果下次交易是新的一天，查找现金交割位置执行交割，
            cash_delivery_pos = (day_num + 1) % cash_delivery_period
            cash_delivered = cash_delivery_queue[cash_delivery_pos]
            cash_delivery_queue[cash_delivery_pos] = 0.0
        else:
            cash_delivered = 0.0

    if stock_delivery_period == 0:
        stocks_delivered = new_stocks.copy()
    else:
        # 计算交割队列起始位置，将新增股票加入交割队列起始位置
        stock_in_pos = day_num % stock_delivery_period
        stock_delivery_queue[stock_in_pos, :] += new_stocks
        if is_new_day:
            # 如果下次交易是新的一天，查找股票交割位置执行交割，
            stock_delivery_pos = (day_num + 1) % stock_delivery_period
            stocks_delivered = stock_delivery_queue[stock_delivery_pos, :].copy()
            stock_delivery_queue[stock_delivery_pos, :] = np.zeros(shape=(share_count,), dtype='float')
        else:
            stocks_delivered = np.zeros(shape=(share_count,), dtype='float')

    return cash_delivered, stocks_delivered


# @njit(nogil=True, cache=True)
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
        slippage: float, 交易成本：滑点
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
        (own_cashes[i + 1],
         available_cashes[i + 1],
         own_amounts_array[i + 1],
         available_amounts_array[i + 1],
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


@njit(nogil=True, cache=True)
def backtest_flash_steps(
        signal_types: np.ndarray,
        op_signals: np.ndarray,
        cash_investment_array: np.ndarray,
        cash_inflation_array: np.ndarray,
        delivery_day_indicators: np.ndarray,
        trade_prices: np.ndarray,
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
) -> tuple[Union[float, Any], Union[ndarray[Any, dtype[Any]], Any]]:
    """相比backtest_batch_steps()函数，以更快的速度批量处理多次交易的回测计算

    该函数省略所有中间计算变量的存储，仅保存最终结果，同时省略与最终结果无关的数据存储，
    从而提升计算速度、节省内存开销。

    输入数据与backtest_batch_steps()函数相似，但是不包含用于记录现金、持股变动以及
    交易记录和交易费用的整个数组。这些数据在函数内部仅仅作为中间变量，存储每一轮回测过
    程的期初结果和期末结果，在完成全部交易信号的回测计算后，输出最后一轮回测的期末结果。

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
    trade_prices: np.ndarray
        交易价格清单，记录每一个运行交易记录时间戳中的各个资产的交易价格
    cost_params: np.ndarray
        交易成本参数，包括买入费率、卖出费率、最低买入费用、最低卖出费用、交易滑点
        buy_rate: float, 交易成本：固定买入费率
        sell_rate: float, 交易成本：固定卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slippage: float, 交易成本：滑点
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
    tuple(float, np.ndarray),
    交易的结果保存在最终的计算结果中
        closing_cash: 回测结束后最终持有现金清单
        closing_amounts: 回测结束后最终持有资产清单

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
    opening_cash = 0.0
    opening_available_cash = 0.0
    opening_amounts = np.zeros(shape=(share_count,), dtype='float')
    opening_available_amounts = np.zeros(shape=(share_count,), dtype='float')

    closing_cash = 0.0
    closing_amounts = np.zeros(shape=(share_count,), dtype='float')

    # 开始循环处理op_signal中的每一条交易信号，获取其signal_type，执行下列步骤：
    for i in range(signal_count):
        # 如果当期有现金投资，则更新持有现金和可用现金
        cash_investment = cash_investment_array[i]
        if cash_investment > 0:
            opening_cash += cash_investment
            opening_available_cash += cash_investment

        is_delivery_day = bool(delivery_day_indicators[i])

        # 调用backtest_step函数，计算本次交易的现金变动、持仓变动和交易费用
        (closing_cash,
         closing_available_cash,
         closing_amounts,
         closing_available_amounts,
         _,
         _,
         cash_delivery_queue,
         stock_delivery_queue) = backtest_step(
                signal_type=signal_types[i],
                op_signal=op_signals[i],
                cash_inflation=cash_inflation_array[i],
                is_delivery_day=is_delivery_day,
                day_num=day_nums[i],
                own_cash=opening_cash,
                own_amounts=opening_amounts,
                available_cash=opening_available_cash,
                available_amounts=opening_available_amounts,
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

        opening_cash = closing_cash
        opening_available_cash = closing_available_cash
        opening_amounts = closing_amounts
        opening_available_amounts = closing_available_amounts

    # 完成全部交易信号的处理后，输出最终的持有现金清单、持有资产清单和交易费用清单
    return closing_cash, closing_amounts


def generate_cash_invest_and_delivery_arrays(invest_cash_plan: CashPlan,
                                             group_merge_type: str,
                                             timing_table: pd.DataFrame) -> (tuple[np.ndarray, np.ndarray, np.ndarray]):
    """ 获取现金投资和通胀率相关参数，生成投资和通胀率数组

    Parameters
    ----------
    invest_cash_plan: CashPlan
        现金投资计划
    group_merge_type: str
        投资策略组合并类型。如果该类型为'NONE'，则表示不进行组合并操作,则交易信号的
        数量可能会大于timing_table的长度，否则交易信号的数量与timing_table的长度
        相同
    timing_table: pd.DataFrame
        操作日时间索引, 用于生成对应长度的数组

    Returns
    -------
    cash_investment_array: np.ndarray
        现金投资数组
    inflation_rate_array: np.ndarray
        通胀率数组
    delivery_day_indicators: np.ndarray
        交割日指示数组, 非交割日为0，交割日为1
    """
    if group_merge_type.upper() == 'NONE':
        signal_length = int(timing_table.sum().sum())
        cash_plan_index = timing_table.index.repeat(timing_table.sum(axis=1).values)
    else:
        signal_length = len(timing_table)
        cash_plan_index = timing_table.index

    # 生成包含现金投资和现金通胀率数组的DataFrame
    cash_plan_df = pd.DataFrame(
            {'investment':     np.zeros(shape=(signal_length,), dtype=float),
             'inflation_rate': np.ones(shape=(signal_length,), dtype=float)},
            index=cash_plan_index,
    )
    investment_positions = np.searchsorted(cash_plan_index, invest_cash_plan.plan.index, side='left')
    for pos, amount in zip(investment_positions, invest_cash_plan.amounts):
        if pos < len(cash_plan_df):
            cash_plan_df.iat[pos, 0] += amount  # 累加投资金额

    inflation_rate = invest_cash_plan.ir
    day_diffs = (cash_plan_df.index - cash_plan_df.index[0]).days
    cash_plan_df['inflation_rate'] += inflation_rate * day_diffs / 365  # 年化通胀率转换为日化通胀率
    cash_investment_array = cash_plan_df['investment'].to_numpy()
    cash_inflation_array = cash_plan_df['inflation_rate'].to_numpy()
    cash_inflation_array = cash_inflation_array / np.roll(cash_inflation_array, 1)
    cash_inflation_array[0] = 1.0  # 第一天的通胀率设为1.0

    day_changes = np.diff(day_diffs.values, append=day_diffs.values[-1] + 1)  # 计算相邻日期的差值，最后一个日期后面添加一个新日期以确保最后一天的变化被记录
    day_changes[day_changes.nonzero()] = 1  # 将非零差值设为1，表示天数变化
    return cash_investment_array, cash_inflation_array, day_changes


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
                 cash_plan: CashPlan,
                 cash_investment_array: np.ndarray,
                 cash_inflation_array: np.ndarray,
                 delivery_day_indicators: np.ndarray,
                 cost_params: np.ndarray,  # 交易成本参数
                 signal_parsing_params: dict,  # 交易信号解析参数
                 trading_moq_params: dict,  # 交易最小单位参数
                 trading_delivery_params: dict,  # 交易交割参数
                 trade_price_data: np.ndarray,  # 交易价格数据
                 benchmark_data: Optional[Union[pd.DataFrame, pd.Series]] = None,
                 evaluate_price_data: Optional[pd.DataFrame] = None,
                 enable_tracing: bool = False,
                 logger: Optional[logging.Logger] = None):
        """ 初始化Backtester对象，设置operator对象和回测参数，初始化回测结果存储表格

        Parameters
        ----------
        op: Operator
            交易操作对象，包含交易信号生成和交易执行的逻辑
        shares: list[str]
            交易标的列表，包含所有交易标的的代码
        cash_plan: CashPlan,
            现金投资计划
        benchmark_data: pd.DataFrame or pd.Series
            用于评价回测结果的业绩基准价格，频率为日频，每日收盘价，其索引为回测开始日到结束日的所有交易日日期，列名为benchmark
        evaluate_price_data: pd.DataFrame, optional
            用于评价回测结果的日频收盘价数据，索引为交易日15:00:00，列为资产代码
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
            slippage: float, 交易成本：滑点
        signal_parsing_params: dict
            交易信号解析参数字典，包含解析交易信号所需的所有参数，通常是parse_signal_parsing_params()函数的输出
        trading_moq_params: dict
            交易最小单位参数字典，包含交易最小单位相关的所有参数，通常是parse_trading_moq_params()函数的输出
        trading_delivery_params: dict
            交易交割参数字典，包含交易交割相关的所有参数，通常是parse_trading_delivery_params()函数的输出
        trade_price_data: np.ndarray
            交易价格数据，记录每一个运行交易记录时间戳中的各个资产的交易价格
        enable_tracing: bool, optional, default=False
            是否启用回测过程的性能追踪功能，默认值为False
        logger: Optional[logging.Logger]
            可选的日志记录器对象，用于记录回测过程中的日志信息
        """

        # 参数基础校验
        assert isinstance(op, Operator), "op must be an instance of Operator"
        if isinstance(shares, str):
            shares = str_to_list(shares)
        assert isinstance(shares, list) and all(isinstance(s, str) for s in shares), "shares must be a list of strings"

        # benchmark 必须是一个pd.Series，如果是DataFrame，则转换为Series
        if isinstance(benchmark_data, pd.DataFrame):
            if benchmark_data.shape[1] != 1:
                raise ValueError("benchmark_data DataFrame must have only one column")
            benchmark_data = benchmark_data.iloc[:, 0]
        if benchmark_data is not None and not isinstance(benchmark_data, pd.Series):
            raise TypeError("benchmark_data must be a pandas Series or DataFrame with one column")

        # 参数一致性校验
        n_signals = op.get_signal_count()
        share_count = len(shares)
        arrays_to_check = [
            ("cash_investment_array", cash_investment_array, (n_signals,)),
            ("cash_inflation_array", cash_inflation_array, (n_signals,)),
            ("delivery_day_indicators", delivery_day_indicators, (n_signals,)),
            ("trade_price_data", trade_price_data, (n_signals, share_count))
        ]
        for name, arr, shape in arrays_to_check:
            if not isinstance(arr, np.ndarray):
                raise TypeError(f"{name} must be a numpy array")
            if arr.shape != shape:
                raise ValueError(f"{name} should have shape {shape}, but got {arr.shape}")

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
        self.share_count = len(self.shares)

        # 3.1 现金和股票持仓历史记录表
        shape_assets = (self.n_signals + 1, self.share_count)
        shape_cashes = (self.n_signals + 1,)
        self.own_cashes = np.zeros(shape=shape_cashes, dtype=float)
        self.own_amounts_array = np.zeros(shape=shape_assets, dtype=float)
        self.available_cashes = np.zeros(shape=shape_cashes, dtype=float)
        self.available_amounts_array = np.zeros(shape=shape_assets, dtype=float)

        # 3.2 交易过程数据记录表，包括交易记录、交易成本等
        shape_signals = (self.n_signals, self.share_count)
        self.trade_records_array = np.zeros(shape_signals, dtype=float)  # 记录每次交易的买卖数量
        self.trade_cost_array = np.zeros(shape_signals, dtype=float)  # 记录每次交易的交易成本
        self.trade_price_array = np.zeros(shape_signals, dtype=float)  # 记录每次交易的成交价格，未成交为0，dynamic数据类型的operator需要用到

        # 4, 回测交易最终结果：评价指标、交易日志和交易汇总记录
        self.backtest_result: dict = {}
        self.trade_log_df: Optional[pd.DataFrame] = None
        self.summary_df: Optional[pd.DataFrame] = None
        self.trace_df: Optional[pd.DataFrame] = None

        # 5, 其他相关属性（需要增加数据匹配性校验）
        self.cash_plan = cash_plan
        self.benchmark_data = benchmark_data
        self.evaluate_price_data = evaluate_price_data
        self.enable_tracing = enable_tracing

        if logger is not None:
            logger.info('Start backtest operator...')

    def run(self) -> 'Backtester':
        """ 执行回测计算，生成回测结果数据并存入对象属性中"""
        self.op.set_shares(self.shares)

        if self.enable_tracing:
            self.op.enable_tracing()
        else:
            self.op.disable_tracing()

        # 1，如果operator的交易信号不依赖于回测数据，调用函数backtest_operator_independently()处理回测信号
        if not self.op.check_dynamic_data():
            if self.logger is not None:
                self.logger.info('Backtest operator with only static data...')
            signals = self._backtest_static_operator()
        # 2，如果operator的交易信号依赖于回测数据，调用函数backtest_operator_dependently()处理回测信号
        else:
            if self.logger is not None:
                self.logger.info('Backtest operator with dynamic data dependence...')
            signals = self._backtest_dynamic_operator()

        self.op_signals = signals
        if self.logger is not None:
            self.logger.info('Backtest completed.')

        return self

    def clear_backtest_buffers(self):
        """ 清除回测结果缓存数据，将回测结果数据重置为空数组，以便重新进行回测计算

        Returns
        -------
        None
        """
        self.op_signals = None
        self.own_cashes.fill(0.0)
        self.own_amounts_array.fill(0.0)
        self.available_cashes.fill(0.0)
        self.available_amounts_array.fill(0.0)
        self.trade_records_array.fill(0.0)
        self.trade_cost_array.fill(0.0)
        self.backtest_result.clear()
        self.trade_log_df = None
        self.summary_df = None

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

        # TODO: 实现交易过程动态数据的获取

        # 1，读取初始持仓和现金数据，更新operator中的依赖性历史数据
        signals = np.zeros((self.op.get_signal_count(), self.share_count), dtype=float)

        # 为 Operator 注入完整的交易过程数据源与时间索引，供策略通过 get_data('proc.xxx', ...) 访问。
        # 注意：这里不改变原有 dynamic data buffer 机制，仅额外提供 process data 视图。
        try:
            self.op._process_time_index = self.op.op_signal_index.get_level_values(0).to_numpy()
        except Exception:
            self.op._process_time_index = None
        if hasattr(self.op, "_process_data_sources"):
            self.op._process_data_sources = {
                "own_cashes": self.own_cashes,
                "available_cashes": self.available_cashes,
                "own_amounts": self.own_amounts_array,
                "available_amounts": self.available_amounts_array,
                "trade_records": self.trade_records_array,
                "trade_costs": self.trade_cost_array,
                # 使用实际成交价格作为交易价格过程数据
                "trade_prices": self.trade_price_array,
                # 使用交易模拟价格作为估值价格，用于 position_value / total_value 一类派生量
                "price_data": self.trade_price_data,
            }

        self.op.prepare_dynamic_data_buffer(
                trade_records=self.trade_records_array,  # 成交量
                trade_prices=self.trade_price_array,  # 成交价格
                own_cashes=self.own_cashes,  # 持有现金
                available_cashes=self.available_cashes,
                holding_positions=self.own_amounts_array,
                available_positions=self.available_amounts_array,
        )

        cash_delivery_queue, stock_delivery_queue = initialize_backtest_delivery_queue(
                share_count=self.share_count,
                **self.trading_delivery_params,
        )
        day_nums = self.delivery_day_indicators.cumsum()

        timer = FunctionTimer()
        bt_step = 0
        # 循环执行下面步骤，直至完整生成回测结果清单
        for i in range(len(self.op.group_timing_table)):

            # 1，调用operator.run_strategy()生成当前交易信号，注意同一时刻可能会有多组信号生成
            # print(f'running / backtest step {i+1}/{bt_step + 1}...')
            for result in timer.time_function('op_run', self.op.run_strategy, step_index=i):
                # print(f'got result from op.run_strategy: {result}')
                stype, s_index, signal = result

                # 2，开始回测，判断是否有资金投入，如果有，更新持有现金和可用现金
                cash_investment = self.cash_investment_array[bt_step]
                if cash_investment > 0:
                    self.own_cashes[bt_step] += cash_investment
                    self.available_cashes[bt_step] += cash_investment

                signal_type = SIGNAL_TYPE_ID[stype]
                is_delivery_day = bool(self.delivery_day_indicators[bt_step])
                signals[bt_step, :] = signal

                # 3，调用backtest_step()回测当前交易信号的结果，生成当前交易回测结果
                (
                    self.own_cashes[bt_step + 1],
                    self.available_cashes[bt_step + 1],
                    self.own_amounts_array[bt_step + 1],
                    self.available_amounts_array[bt_step + 1],
                    self.trade_records_array[bt_step],
                    self.trade_cost_array[bt_step],
                    cash_delivery_queue,
                    stock_delivery_queue,
                ) = timer.time_function(
                        'backtest',
                        backtest_step,
                        signal_type=signal_type,
                        op_signal=signal,
                        cash_inflation=self.cash_inflation_array[bt_step],
                        is_delivery_day=is_delivery_day,
                        day_num=day_nums[bt_step],
                        own_cash=self.own_cashes[bt_step],
                        own_amounts=self.own_amounts_array[bt_step, :],
                        available_cash=self.available_cashes[bt_step],
                        available_amounts=self.available_amounts_array[bt_step, :],
                        trade_prices=self.trade_price_data[bt_step, :],
                        cost_params=self.cost_params,
                        cash_delivery_queue=cash_delivery_queue,
                        stock_delivery_queue=stock_delivery_queue,
                        share_count=self.share_count,
                        **self.signal_parsing_params,
                        **self.trading_moq_params,
                        **self.trading_delivery_params,
                )
                bt_step += 1

                # # 4，更新operator中的依赖性历史数据，主要是trade_prices_array数据（成交价格数据，因为这个价格需要计算出来）
                self.trade_price_array[:] = np.abs(np.sign(self.trade_records_array)) * self.trade_price_data

        time = timer.get_stats()
        self.op_run_time = time['op_run']
        self.backtest_run_time = time['backtest']

        # 5，返回signals，因为完整的回测结果清单已经保存在作为参数传入的几个数组中
        return signals

    # 生成回测结果的各种评价指标，直接快速计算返回回测的各项结果指标
    def trade_result_final_value(self):
        """ 直接快速计算返回回测的终值结果"""
        final_value = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]
        return final_value[-1]

    def trade_result_volatility(self):
        """ 直接快速计算返回回测的波动率结果"""
        value_history = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]
        rolled_value_history = np.roll(value_history, 1)
        returns = (value_history - rolled_value_history) / rolled_value_history
        returns[0] = 0.0  # 第一天的收益率设为0.0
        volatility = returns.std() * np.sqrt(252)
        return volatility

    def trade_result_max_drawdown(self):
        """ 直接快速计算返回回测的最大回撤结果"""
        value_history = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]
        rolling_max = np.maximum.accumulate(value_history)
        drawdown = (value_history - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        return max_drawdown

    # 生成更加结构化的DataFrame型交易结果数据，以便用于结果的评价及后续处理，
    def trade_result_df(self) -> pd.DataFrame:
        """ 根据回测结果生成资产价值记录，输出内容为DataFrame格式

        Returns
        -------
        value_history: pd.DataFrame
            交易模拟结果数据
        """
        if self.evaluate_price_data is None:
            value_history = pd.DataFrame(self.own_amounts_array[1:],
                                         index=self.op.op_signal_index.get_level_values(0),
                                         columns=self.shares)
            value_history['cash'] = self.own_cashes[1:]
            value_history['value'] = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]
            value_history['fee'] = self.trade_cost_array.sum(axis=1)
            value_history = value_history.groupby(value_history.index).last()
            return value_history

        daily_index = self.evaluate_price_data.index
        step_times = pd.to_datetime(self.op.op_signal_index.get_level_values(0))

        step_times_values = step_times.to_numpy()
        daily_values_ts = daily_index.to_numpy()
        # 对于第一个交易信号之前的日期，使用初始持仓（索引0）；
        # 对于两个交易信号之间的日期，使用最近一次交易后的持仓；
        # 对于最后一个交易信号之后的日期，使用最后一次交易后的持仓。
        pos_idx = np.searchsorted(step_times_values, daily_values_ts, side='right')
        pos_idx = np.clip(pos_idx, 0, self.own_amounts_array.shape[0] - 1)

        daily_positions = self.own_amounts_array[pos_idx, :]
        daily_cash = self.own_cashes[pos_idx]

        # 将每一步交易费用按“日期”聚合为“每日总费用”，再与日频索引按日期对齐
        step_dates = step_times.normalize()
        step_fee = self.trade_cost_array.sum(axis=1)
        fee_by_date = pd.Series(step_fee, index=step_dates).groupby(level=0).sum()
        daily_dates = daily_index.normalize()
        daily_fee = fee_by_date.reindex(daily_dates).fillna(0.0)

        # 使用评价用日频收盘价构造日频价格序列
        daily_prices = self.evaluate_price_data.reindex(daily_index).reindex(columns=self.shares)
        price_array = np.nan_to_num(daily_prices.values, nan=0.0)
        daily_values = (price_array * daily_positions).sum(axis=1) + daily_cash

        # 一次性拼接持仓列与价格列，避免逐列插入导致 DataFrame 碎片化
        positions_df = pd.DataFrame(daily_positions, index=daily_index, columns=self.shares)
        price_df = daily_prices.reindex(columns=self.shares).rename(columns=lambda c: 'p-' + c)
        value_history = pd.concat([positions_df, price_df], axis=1)
        value_history['cash'] = daily_cash
        value_history['value'] = daily_values
        value_history['fee'] = daily_fee.values

        return value_history

    def trace_result_df(self) -> Optional[DataFrame]:
        """ 根据回测结果生成交易过程记录，输出内容为DataFrame格式

        trace 行与 op_signal_index 的对齐由 Operator 在写入时保证（update_trace_step 使用
        全局 signal 行号），此处仅按策略 concat 后设置 index 为 op_signal_index。

        Returns
        -------
        trade_trace: pd.DataFrame
            交易模拟过程数据
        """
        if not self.enable_tracing:
            return self.trace_df
        op_signal_index = self.op.op_signal_index
        trace_dfs = [s.get_trace_data() for s in self.op.strategies]
        if not trace_dfs:
            self.trace_df = pd.DataFrame(index=op_signal_index)
            return self.trace_df
        trade_trace = pd.concat(trace_dfs, axis=1)
        trade_trace.index = op_signal_index
        self.trace_df = trade_trace
        return self.trace_df

    def evaluate_result(self, indicators: str) -> dict:
        """生成交易结果的评价报告，保存在self.evaluate_result属性中

        Parameters
        ----------
        indicators: str
            回测结果评价指标，详情参见qteasy.evaluate.evaluate()函数

        Returns
        -------
        """
        self.backtest_result.update(
                evaluate(
                        looped_values=self.trade_result_df(),
                        hist_benchmark=self.benchmark_data,
                        cash_plan=self.cash_plan,
                        indicators=indicators,
                )
        )

        self.backtest_result['op_run_time'] = self.op_run_time
        self.backtest_result['loop_run_time'] = self.backtest_run_time

        return self.backtest_result

    # 生成回测结果的明细报告，包括纯文本形式的报告和图表形式的报告
    def report_result(self,
                      trade_log: str = None,
                      trade_summary: str = None) -> str:
        """ 生成回测结果的明细报告，报告为纯文本格式，可以使用print命令打印

        Parameters
        ----------
        trade_log: str, optional
            交易日志文件的存储路径，默认值为None，如果给出该路径，则在报告中打印交易日志的存储路径
        trade_summary: str, optional
            交易汇总记录文件的存储路径，默认值为None，如果给出，则在报告中打印交易汇总记录的存储路径

        Returns
        -------
        report_str: str
            以打印格式排版的回测结果报告
        """
        if self.backtest_result.get('complete_values') is not None:
            self.backtest_result['report'] = _loop_report_str(
                    loop_results=self.backtest_result,
            )
            return self.backtest_result['report']
        else:
            return 'Complete evaluation of backtest result is not created!'

    def plot_result(self, plot_title: str,
                    show_positions: bool,
                    buy_sell_markers: bool) -> None:
        """ 以图表形式生成交易结果

        Parameters
        ----------
        plot_title: str
            图表的标题名称
        show_positions: bool
            是否显示持股仓位区间信息，如果设置为True，则在收益率曲线图上
            以红色/绿色条带显示区间的持仓类型（绿色表示持多仓，红色表示持
            空仓）颜色越深持仓比例越高
        buy_sell_markers: bool
            是否在收益率曲线图上显示买卖点，如果设置为True，则在收益率曲
            线图上以红绿色小箭头标示出买卖点

        Returns
        -------
        None
        """
        if self.backtest_result.get('complete_values') is not None:
            _plot_loop_result(
                    loop_results=self.backtest_result,
                    plot_title=plot_title,
                    show_positions=show_positions,
                    buy_sell_markers=buy_sell_markers,
            )
        else:
            err = RuntimeError('Complete evaluation of backtest result is not created!')
            raise err

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
            以上信息以DataFrame形式保存，行索引为多级索引，第一/二层为时间/策略组索引，第三层为上述8个数据类别。
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
        op_signal_index = self.op.op_signal_index
        trade_signal_df = pd.DataFrame(self.op_signals,
                                       index=op_signal_index,
                                       columns=self.shares)
        trade_price_df = pd.DataFrame(np.round(self.trade_price_data, 3),
                                      index=op_signal_index,
                                      columns=self.shares)
        own_amounts_df = pd.DataFrame(np.round(self.own_amounts_array[1:], 3),
                                      index=op_signal_index,
                                      columns=self.shares)
        available_amounts_df = pd.DataFrame(np.round(self.available_amounts_array[1:], 3),
                                            index=op_signal_index,
                                            columns=self.shares)
        trade_records_df = pd.DataFrame(np.round(self.trade_records_array, 3),
                                        index=op_signal_index,
                                        columns=self.shares)
        trade_cost_df = pd.DataFrame(np.round(self.trade_cost_array, 3),
                                     index=op_signal_index,
                                     columns=self.shares)
        cash_changed_df = pd.DataFrame(np.round(-trade_price_df * trade_records_df - self.trade_cost_array, 3),
                                       index=op_signal_index,
                                       columns=self.shares)
        amounts_value_df = pd.DataFrame(np.round(trade_price_df * self.own_amounts_array[1:], 3),
                                        index=op_signal_index,
                                        columns=self.shares)

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
        combined_data = combined_data.reorder_levels([1, 2, 0]).sort_index(level=0)

        # 生成 trade log 详细表的每期汇总数据部分（当期现金投入、期末持有现金、期末可用现金、期末总价值）
        add_investments = pd.Series(self.cash_investment_array,
                                    index=op_signal_index,
                                    name='add. invest')
        own_cash_series = pd.Series(np.round(self.own_cashes[1:], 3),
                                    index=op_signal_index,
                                    name='own cash')
        available_cash_series = pd.Series(np.round(self.available_cashes[1:], 3),
                                          index=op_signal_index,
                                          name='available cash')
        total_values = (self.trade_price_data * self.own_amounts_array[1:]).sum(axis=1) + self.own_cashes[1:]

        total_value_series = pd.Series(np.round(total_values, 3),
                                       index=op_signal_index,
                                       name='value')

        summary_data = [add_investments, own_cash_series, available_cash_series, total_value_series]

        if self.enable_tracing:
            trace_df = self.trace_result_df()
            if trace_df is not None:
                summary_data.append(trace_df)

        self.summary_df = pd.concat(
                objs=summary_data,
                axis=1,
        )
        self.summary_df = self.summary_df.assign(summary='7, summary').set_index('summary', append=True)
        self.summary_df.index.names = [None, None, None]
        # 上面将summary_df的索引变为多级索引，第三层为'7, summary'，与combined_data的第三层索引对应，以便join
        self.trade_log_df = self.summary_df.join(combined_data, how='outer', sort=False)

        if save_to_file_path is not None:
            self.trade_log_df.to_csv(save_to_file_path, encoding='utf-8')
            if self.logger:
                self.logger.info(f'trade log saved to {save_to_file_path}')

        self.backtest_result['trade_log'] = save_to_file_path  #

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
            raise KeyError(
                    f'some shares ({missing_share}) are not in trade_log_df columns, cannot create trade summary!')
        # 处理share_names
        if share_names is None:
            share_names = ['N/A' for _ in self.shares]

        share_logs = []
        # trade_log_df_no_duplicate = self.trade_log_df[~self.trade_log_df.index.duplicated(keep='last')]
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
        self.summary_df.index = self.summary_df.index.droplevel(-1)  # 去掉index中的’7, summary‘层级以便join
        self.summary_df = self.summary_df.join(op_log_shares_abs, how='right', sort=True)

        if save_to_file_path is not None:
            self.summary_df.to_csv(save_to_file_path, encoding='utf-8')
            if self.logger is not None:
                self.logger.info(f'trade summary saved to {save_to_file_path}')

        self.backtest_result['trade_summary'] = save_to_file_path  #

        return self.summary_df

    def save_complete_values(self, save_to_file_path: Optional[str] = None) -> Optional[str]:
        """ 将 complete_values 保存为 CSV 文件（当 trade_log=True 时由 qt_operator 调用）

        Parameters
        ----------
        save_to_file_path: str, optional
            保存路径，若为 None 则不写入

        Returns
        -------
        str or None
            成功时返回保存路径，否则返回 None
        """
        cv = self.backtest_result.get('complete_values')
        if save_to_file_path is None or cv is None or (isinstance(cv, pd.DataFrame) and cv.empty):
            if self.logger:
                self.logger.debug(
                    'save_complete_values skipped: path=%s, complete_values present=%s',
                    save_to_file_path,
                    cv is not None and (not isinstance(cv, pd.DataFrame) or not cv.empty),
                )
            return None
        cv.to_csv(save_to_file_path, encoding='utf-8')
        self.backtest_result['complete_values_file'] = save_to_file_path
        if self.logger:
            self.logger.info(f'complete values (value curve) saved to {save_to_file_path}')
        return save_to_file_path
