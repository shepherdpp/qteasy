# coding=utf-8
# ======================================
# File:     trading.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-02-20
# Desc:
#   functions related to live-trading,
# including scheduling, data-acquisition
# signal-to-ordering, and result
# processing.
# ======================================

import asyncio

import pandas as pd
import numpy as np

from qteasy.database import DataSource
from qteasy import logger_core as logger

from qteasy.trade_recording import read_trade_order, get_position_by_id, get_account, update_trade_order
from qteasy.trade_recording import read_trade_order_detail, read_trade_results_by_delivery_status, write_trade_result
from qteasy.trade_recording import read_trade_results_by_order_id, get_account_cash_availabilities
from qteasy.trade_recording import update_account_balance, update_position, update_trade_result

# TODO: add TIMEZONE to qt config arguments
TIMEZONE = 'Asia/Shanghai'


# TODO: 创建一个模块级变量，用于存储交易信号的数据源，所有的交易信号都从这个数据源中读取
#  避免交易信号从不同的数据源中获取，导致交易信号的不一致性
async def process_trade_signal(signal):
    # 将交易信号提交给交易平台或用户以获取交易结果
    raw_trade_results = await generate_trade_result(order_id, account_id=1)
    # 处理交易结果
    process_trade_result(raw_trade_result=raw_trade_results, config=config)


async def live_trade_signals():
    while True:
        # 检查交易策略的运行状态：
        # 当有交易策略处于"运行"状态时，生成交易信号
        signals = generate_signal()
        # 解析交易信号，将其转换为标准的交易信号
        order_elements = parse_trade_signal(
                signals=signals,
                signal_type=signal_type,
                shares=shares,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                config=config,
        )

        order_ids = save_parsed_trade_orders(
                account_id=account_id,
                **order_elements,
        )
        # 提交交易信号并等待结果
        for order_id in order_ids:
            asyncio.create_task(submit_order(order_id))
        # 继续生成后续交易信号
        await asyncio.sleep(1)


def live_trade():
    asyncio.run(live_trade_signals())


# all functions for live trade

def generate_signal(operator, signal_type, shares, prices, own_amounts, own_cash, config):
    """ 从Operator对象中生成qt交易信号

    Parameters
    ----------
    operator: Operator
        交易策略的Operator对象
    signal_type: str, {'PT', 'PS', 'VS'}
        交易信号类型
    shares: list of str
        股票代码
    prices: np.ndarray
        股票价格
    own_amounts: np.ndarray
        股票持仓数量, 与shares对应, 顺序一致, 无持仓的股票数量为0, 负数表示空头持仓
    own_cash: float
        账户可用资金
    config: dict
        交易信号的配置

    Returns
    -------
    int, 提交的交易信号的数量
    """
    # 从Operator对象中读取交易信号
    op_signal = operator.create_signal()
    # 解析交易信号
    symbols, positions, directions, quantities = parse_trade_signal(
        signals=op_signal,
        signal_type=signal_type,
        shares=shares,
        prices=prices,
        own_amounts=own_amounts,
        own_cash=own_cash,
        config=config
    )
    submitted_qty = 0
    for sym, pos, d, qty in zip(symbols, positions, directions, quantities):
        pos_id = get_position_ids(account_id=account_id,
                                  symbol=sym,
                                  position_type=pos,
                                  data_source=data_source)

        # 生成交易信号dict
        trade_signal = {
            'pos_id': pos_id,
            'direction': d,
            'order_type': order_type,
            'qty': qty,
            'price': get_price(),
            'submitted_time': None,
            'status': 'created',
        }
        record_trade_order(trade_signal)
        # 逐一提交交易信号
        if submit_order(trade_signal) is not None:

            # 记录已提交的交易数量
            submitted_qty += qty

    return submitted_qty


# Work functions for live trade
def parse_trade_signal(signals,
                       signal_type,
                       shares,
                       prices,
                       own_amounts,
                       own_cash,
                       available_amounts=None,
                       available_cash=None,
                       config=None):
    """ 根据signal_type的值，将operator生成的qt交易信号解析为标准的交易订单元素，包括
    资产代码、头寸类型、交易方向、交易数量等, 不检查账户的可用资金和持仓数量

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    signal_type: str, {'PT', 'PS', 'VS'}
        交易信号类型
    shares: list of str
        股票代码
    prices: np.ndarray
        股票价格
    own_amounts: np.ndarray
        股票持仓数量, 与shares对应, 顺序一致, 无持仓的股票数量为0, 负数表示空头持仓
    own_cash: float
        账户可用资金总额
    available_amounts: np.ndarray
        股票可用持仓数量, 与shares对应, 顺序一致, 无持仓的股票数量为0, 负数表示空头持仓
    available_cash: float
        账户可用资金总额
    config: dict
        交易信号的配置

    Returns
    -------
    order_elements: tuple, (symbols, positions, directions, quantities)
        symbols: list of str, 交易信号对应的股票代码
        positions: list of str, 交易信号对应的持仓类型
        directions: list of str, 交易信号对应的交易方向
        quantities: list of float, 交易信号对应的交易数量
    """

    # 处理optional参数:
    # 如果没有提供可用资金和持仓数量，使用当前的资金和持仓数量
    if available_amounts is None:
        available_amounts = own_amounts
    if available_cash is None:
        available_cash = own_cash
    # 如果没有提供交易信号的配置，使用QT_CONFIG中的默认配置
    if config is None:
        from qteasy import QT_CONFIG
        config = {
            'pt_buy_threshold': QT_CONFIG['pt_buy_threshold'],
            'pt_sell_threshold': QT_CONFIG['pt_sell_threshold'],
            'allow_sell_short': QT_CONFIG['allow_sell_short'],
        }

    # PT交易信号和PS/VS交易信号需要分开解析
    if signal_type.lower() == 'pt':
        cash_to_spend, amounts_to_sell = parse_pt_signals(
            signals=signals,
            prices=prices,
            own_amounts=own_amounts,
            own_cash=own_cash,
            pt_buy_threshold=config['pt_buy_threshold'],
            pt_sell_threshold=config['pt_sell_threshold'],
            allow_sell_short=config['allow_sell_short']
        )
    # 解析PT交易信号：
    # 读取当前的所有持仓，与signal比较，根据差值确定计划买进和卖出的数量
    # 解析PS/VS交易信号
    # 直接根据交易信号确定计划买进和卖出的数量
    elif signal_type.lower() == 'ps':
        cash_to_spend, amounts_to_sell = parse_ps_signals(
            signals=signals,
            prices=prices,
            own_amounts=own_amounts,
            own_cash=own_cash,
            allow_sell_short=config['allow_sell_short']
        )
    elif signal_type.lower() == 'vs':
        cash_to_spend, amounts_to_sell = parse_vs_signals(
            signals=signals,
            prices=prices,
            own_amounts=own_amounts,
            allow_sell_short=config['allow_sell_short']
        )
    else:
        raise ValueError('Unknown signal type: {}'.format(signal_type))

    # 将计划买进金额和计划卖出数量四舍五入到小数点后3位  # TODO: 可以考虑增加一个qt参数，用于控制小数点后的位数
    cash_to_spend = np.round(cash_to_spend, 3)
    amounts_to_sell = np.round(amounts_to_sell, 3)

    # 确认总现金是否足够执行交易，如果不足，则将计划买入金额调整为可用的最大值，可用持仓检查可以分别进行
    total_cash_to_spend = np.sum(cash_to_spend)  # 计划买进的总金额 TODO: 仅对多头持仓有效，空头买入需要另外处理
    if total_cash_to_spend > own_cash:
        # 将计划买入的金额调整为可用的最大值
        cash_to_spend = cash_to_spend * own_cash / total_cash_to_spend

    # 将计算出的买入和卖出的数量转换为交易信号
    symbols, positions, directions, quantities = signal_to_order_elements(
        shares=shares,
        cash_to_spend=cash_to_spend,
        amounts_to_sell=amounts_to_sell,
        prices=prices,
        available_cash=available_cash,
        available_amounts=available_amounts,
        allow_sell_short=config['allow_sell_short']
    )
    return symbols, positions, directions, quantities


# TODO: 将parse_pt/ps/vs_signals函数作为通用函数，在core.py的loopstep中直接引用这三个函数的返回值
#  从而消除重复的代码
# TODO: 考虑修改多空买卖信号的表示方式：当前的表示方式为：
#  1. 多头买入信号：正数cash_to_spend
#  2. 空头买入信号：负数cash_to_spend
#  3. 多头卖出信号：负数amounts_to_sell，负数表示空头，与直觉相反
#  4. 空头卖出信号：正数amounts_to_sell，正数表示多头，与直觉相反
#  但是这种表示方式不够直观
#  可以考虑将多头买入信号和空头卖出信号的表示方式统一为：
#  1. 多头买入信号：正数cash_to_spend
#  2. 空头买入信号：负数cash_to_spend
#  3. 多头卖出信号：正数amounts_to_sell
#  4. 空头卖出信号：负数amounts_to_sell
#  上述表示方法用cash表示买入，amounts表示卖出，且正数表示多头，负数表示空头，与直觉相符
#  但是这样需要修改core.py中的代码，需要修改backtest的部分代码，需要详细测试
def parse_pt_signals(signals,
                     prices,
                     own_amounts,
                     own_cash,
                     pt_buy_threshold,
                     pt_sell_threshold,
                     allow_sell_short):
    """ 解析PT类型的交易信号

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    prices: np.ndarray
        各个资产的价格
    own_amounts: np.ndarray
        各个资产的持仓数量
    own_cash: float
        账户的现金
    pt_buy_threshold: float
        PT买入的阈值
    pt_sell_threshold: float
        PT卖出的阈值
    allow_sell_short: bool
        是否允许卖空

    Returns
    -------
    tuple: (cash_to_spend, amounts_to_sell)
        cash_to_spend: np.ndarray, 买入资产的现金
        amounts_to_sell: np.ndarray, 卖出资产的数量
    """

    # 计算当前总资产
    total_value = np.sum(prices * own_amounts) + own_cash

    ptbt = pt_buy_threshold
    ptst = -pt_sell_threshold
    # 计算当前持有头寸的持仓占比，与交易信号相比较，计算持仓差异
    previous_pos = own_amounts * prices / total_value
    position_diff = signals - previous_pos
    # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
    # 当持有份额大于零时，平多仓：卖出数量 = 仓位差 * 持仓份额，此时持仓份额需大于零
    amounts_to_sell = np.where((position_diff < ptst) & (own_amounts > 0),
                               position_diff / previous_pos * own_amounts,
                               0.)
    # 当持有份额不小于0时，开多仓：买入金额 = 仓位差 * 当前总资产，此时不能持有空头头寸
    cash_to_spend = np.where((position_diff > ptbt) & (own_amounts >= 0),
                             position_diff * total_value,
                             0.)
    # 当允许买空卖空操作时，需要考虑持有股票时卖出或买入，即开多仓和平多仓，以及开空仓和平空仓
    if allow_sell_short:

        # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 仓位差 * 当前总资产，此时持有份额为0
        cash_to_spend += np.where((position_diff < ptst) & (own_amounts <= 0),
                                  position_diff * total_value,
                                  0.)
        # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 仓位差 * 当前持有空头份额
        amounts_to_sell += np.where((position_diff > ptbt) & (own_amounts < 0),
                                    position_diff / previous_pos * own_amounts,
                                    0.)

    return cash_to_spend, amounts_to_sell


def parse_ps_signals(signals, prices, own_amounts, own_cash, allow_sell_short):
    """ 解析PS类型的交易信号

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    prices: np.ndarray
        当前资产的价格
    own_amounts: np.ndarray
        当前持有的资产份额
    own_cash: float
        当前持有的现金
    allow_sell_short: bool
        是否允许卖空

    Returns
    -------
    tuple: (cash_to_spend, amounts_to_sell)
        cash_to_spend: np.ndarray, 买入资产的现金
        amounts_to_sell: np.ndarray, 卖出资产的数量
    """

    # 计算当前总资产
    total_value = np.sum(prices * own_amounts) + own_cash

    # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
    # 当持有份额大于零时，平多仓：卖出数量 =交易信号 * 持仓份额，此时持仓份额需大于零
    amounts_to_sell = np.where((signals < 0) & (own_amounts > 0), signals * own_amounts, 0.)
    # 当持有份额不小于0时，开多仓：买入金额 =交易信号 * 当前总资产，此时不能持有空头头寸
    cash_to_spend = np.where((signals > 0) & (own_amounts >= 0), signals * total_value, 0.)

    # 当允许买空卖空时，允许开启空头头寸：
    if allow_sell_short:

        # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 交易信号 * 当前总资产
        cash_to_spend += np.where((signals < 0) & (own_amounts <= 0), signals * total_value, 0.)
        # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 交易信号 * 当前持有空头份额
        amounts_to_sell -= np.where((signals > 0) & (own_amounts < 0), signals * own_amounts, 0.)

    return cash_to_spend, amounts_to_sell


def parse_vs_signals(signals, prices, own_amounts, allow_sell_short):
    """ 解析VS类型的交易信号

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    prices: np.ndarray
        当前资产的价格
    own_amounts: np.ndarray
        当前持有的资产的数量
    allow_sell_short: bool
        是否允许卖空

    Returns
    -------
    tuple: (cash_to_spend, amounts_to_sell)
    - symbols: list of str, 产生交易信号的资产代码
    - positions: list of str, 产生交易信号的各各资产的头寸类型('long', 'short')
    - directions: list of str, 产生的交易信号的交易方向('buy', 'sell')
    - quantities: list of float, 所有交易信号的交易数量
    """

    # 计算各个资产的计划买入金额和计划卖出数量
    # 当持有份额大于零时，平多仓：卖出数量 = 信号数量，此时持仓份额需大于零
    amounts_to_sell = np.where((signals < 0) & (own_amounts > 0), signals, 0.)
    # 当持有份额不小于0时，开多仓：买入金额 = 信号数量 * 资产价格，此时不能持有空头头寸，必须为空仓或多仓
    cash_to_spend = np.where((signals > 0) & (own_amounts >= 0), signals * prices, 0.)

    # 当允许买空卖空时，允许开启空头头寸：
    if allow_sell_short:
        # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 信号数量 * 资产价格
        cash_to_spend += np.where((signals < 0) & (own_amounts <= 0), signals * prices, 0.)
        # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 交易信号 * 当前持有空头份额
        amounts_to_sell -= np.where((signals > 0) & (own_amounts < 0), -signals, 0.)

    return cash_to_spend, amounts_to_sell


def signal_to_order_elements(shares,
                             cash_to_spend,
                             amounts_to_sell,
                             prices,
                             available_cash,
                             available_amounts,
                             allow_sell_short=False):
    """ 逐个计算每一只资产的买入和卖出的数量，将parse_pt/ps/vs_signal函数计算出的交易信号逐项转化为
    交易订单 trade_orders

    在生成交易信号时，需要考虑可用现金的总量以及可用资产的总量
    如果可用现金不足买入所有的股票，则将买入金额按照比例分配给各个股票
    如果可用资产不足计划卖出数量，则降低卖出的数量，同时在允许卖空的情况下，增加对应的空头买入信号

    Parameters
    ----------
    shares: list of str
        各个资产的代码
    cash_to_spend: np.ndarray
        各个资产的买入金额
    amounts_to_sell: np.ndarray
        各个资产的卖出数量
    prices: np.ndarray
        各个资产的价格
    available_cash: float
        可用现金
    available_amounts: np.ndarray
        可用资产的数量
    allow_sell_short: bool, default False
        是否允许卖空，如果允许，当可用资产不足时，会增加空头买入信号

    Returns
    -------
    order_elements: tuple, (symbols, positions, directions, quantities)
    - symbols: list of str, 产生交易信号的资产代码
    - positions: list of str, 产生交易信号的各各资产的头寸类型('long', 'short')
    - directions: list of str, 产生的交易信号的交易方向('buy', 'sell')
    - quantities: list of float, 所有交易信号的交易数量
    """
    # 计算总的买入金额，调整买入金额，使得买入金额不超过可用现金
    total_cash_to_spend = np.sum(cash_to_spend)
    if total_cash_to_spend > available_cash:
        cash_to_spend = cash_to_spend * available_cash / total_cash_to_spend

    # 逐个计算每一只资产的买入和卖出的数量
    symbols = []
    positions = []
    directions = []
    quantities = []

    for i, sym in enumerate(shares):
        # 计算多头买入的数量
        if cash_to_spend[i] > 0.001:
            # 计算买入的数量
            quantity = cash_to_spend[i] / prices[i]
            symbols.append(sym)
            positions.append('long')
            directions.append('buy')
            quantities.append(quantity)
        # 计算空头买入的数量
        if (cash_to_spend[i] < -0.001) and allow_sell_short:
            # 计算买入的数量
            quantity = -cash_to_spend[i] / prices[i]
            symbols.append(sym)
            positions.append('short')
            directions.append('buy')
            quantities.append(quantity)
        # 计算多头卖出的数量
        if amounts_to_sell[i] < -0.001:
            # 计算卖出的数量，如果可用资产不足，则降低卖出的数量，并增加相反头寸的买入数量，买入剩余的数量
            if amounts_to_sell[i] < -available_amounts[i]:
                # 计算卖出的数量
                quantity = available_amounts[i]
                symbols.append(sym)
                positions.append('long')
                directions.append('sell')
                quantities.append(quantity)
                # 如果allow_sell_short，增加反向头寸的买入信号
                if allow_sell_short:
                    quantity = - amounts_to_sell[i] - available_amounts[i]
                    symbols.append(sym)
                    positions.append('short')
                    directions.append('buy')
                    quantities.append(quantity)
            else:
                # 计算卖出的数量，如果可用资产足够，则直接卖出
                quantity = -amounts_to_sell[i]
                symbols.append(sym)
                positions.append('long')
                directions.append('sell')
                quantities.append(quantity)
        # 计算空头卖出的数量
        if (amounts_to_sell[i] > 0.001) and allow_sell_short:
            # 计算卖出的数量，如果可用资产不足，则降低卖出的数量，并增加相反头寸的买入数量，买入剩余的数量
            if amounts_to_sell[i] > available_amounts[i]:
                # 计算卖出的数量
                quantity = - available_amounts[i]
                symbols.append(sym)
                positions.append('short')
                directions.append('sell')
                quantities.append(quantity)
                # 增加反向头寸的买入信号
                quantity = amounts_to_sell[i] + available_amounts[i]
                symbols.append(sym)
                positions.append('long')
                directions.append('buy')
                quantities.append(quantity)
            else:
                # 计算卖出的数量，如果可用资产足够，则直接卖出
                quantity = amounts_to_sell[i]
                symbols.append(sym)
                positions.append('short')
                directions.append('sell')
                quantities.append(quantity)

    order_elements = (symbols, positions, directions, quantities)
    return order_elements


def output_trade_order():
    """ 将交易信号输出到终端或TUI

    Returns
    -------
    order_id: int
        交易信号的id
    """
    pass


def submit_order(order_id, data_source=None):
    """ 将交易订单提交给交易平台或用户以等待交易结果，同时更新账户和持仓信息

    只有刚刚创建的交易信号（status == 'created'）才能提交，否则不需要再次提交
    在提交交易信号以前，对于买入信号，会检查账户的现金是否足够，如果不足，则会按比例调整交易信号的委托数量
    对于卖出信号，会检查账户的持仓是否足够，如果不足，则会按比例调整交易信号的委托数量
    交易信号提交后，会将交易信号的状态设置为submitted，同时将交易信号保存到数据库中
    - 只有使用submit_signal才能将信号保存到数据库中，同时调整相应的账户和持仓信息

    Parameters
    ----------
    order_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    int, 交易信号的id

    Raises
    ------
    RuntimeError
        如果交易信号的状态不为created，则说明交易信号已经提交过，不需要再次提交
    """

    # 读取交易信号
    trade_order = read_trade_order(order_id, data_source=data_source)

    # 如果交易信号的状态不为created，则说明交易信号已经提交过，不需要再次提交
    if trade_order['status'] != 'created':
        return None

    # 实际上在parse_trade_signal的时候就已经检查过总买入数量与可用现金之间的关系了，这里不再检察
    # 如果交易方向为buy，则需要检查账户的现金是否足够 TODO: position为short时做法不同，需要进一步调整
    position_id = trade_order['pos_id']
    position = get_position_by_id(position_id, data_source=data_source)
    if trade_order['direction'] == 'buy':
        account_id = position['account_id']
        account = get_account(account_id, data_source=data_source)
        # 如果账户的现金不足，则输出警告信息
        if account['available_cash'] < trade_order['qty'] * trade_order['price']:
            logger.warning(f'Available cash {account["available_cash"]} is not enough for trade order: \n'
                           f'{trade_order}'
                           f'trade order might not be executed!')

    # 如果交易方向为sell，则需要检查账户的持仓是否足够 TODO: position为short时做法不一样，需要考虑
    elif trade_order['direction'] == 'sell':
        # 如果账户的持仓不足，则输出警告信息
        if position['available_qty'] < trade_order['qty']:
            logger.warning(f'Available quantity {position["available_qty"]} is not enough for trade order: \n'
                           f'{trade_order}'
                           f'trade order might not be executed!')

    # 将signal的status改为"submitted"，并将trade_signal写入数据库
    order_id = update_trade_order(order_id=order_id, data_source=data_source, status='submitted')
    # 检查交易信号

    return order_id


def process_trade_delivery(account_id, data_source=None, config=None):
    """ 处理account_id账户中所有持仓和现金的交割

    从交易历史中读取尚未交割的现金和持仓，根据config中的设置值 'cash_delivery_period' 和
    'stock_delivery_period' 执行交割，将完成交割的现金和持仓数量更新到现金和持仓的available
    中，并将已完成交割的交易结果的交割状态更新为"DL"

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    config: dict, optional
        配置参数, 默认为None, 表示使用默认的配置参数

    Returns
    -------
    None
    """

    if not isinstance(account_id, (int, np.int64)):
        raise TypeError('account_id must be an int')
    if config is None:
        config = {
            'cash_delivery_period': 0,
            'stock_delivery_period': 0,
        }
    if not isinstance(config, dict):
        raise TypeError('config must be a dict')

    undelivered_results = read_trade_results_by_delivery_status('ND', data_source=data_source)
    if undelivered_results is None:
        return
    # 循环处理每一条未交割的交易结果：
    for result_id, result in undelivered_results.iterrows():
        # 读取交易结果的signal_detail，如果account_id不匹配，则跳过，如果signal_detail不存在，则报错
        order_detail = read_trade_order_detail(result.order_id, data_source=data_source)
        if order_detail is None:
            raise RuntimeError(f'No order_detail found for order_id {result.order_id}')
        if order_detail['account_id'] != account_id:
            continue
        # 读取交易方向，根据方向判断需要交割现金还是持仓，并分别读取现金/持仓的交割期
        direction = order_detail['direction']
        if direction == 'buy':
            delivery_period = config['stock_delivery_period']
        elif direction == 'sell':
            delivery_period = config['cash_delivery_period']
        else:
            raise ValueError(f'Invalid direction: {direction}')
        # 读取交易结果的execution_time，如果execution_time与现在的日期差小于交割期，则跳过
        execution_date = pd.to_datetime(result.execution_time).date()
        current_date = pd.to_datetime('now', utc=True).tz_convert(TIMEZONE).date()
        day_diff = (current_date - execution_date).days
        if day_diff < delivery_period:
            continue
        # 执行交割，更新现金/持仓的available，更新交易结果的delivery_status
        if direction == 'buy':
            position_id = order_detail['pos_id']
            update_position(
                    position_id=position_id,
                    data_source=data_source,
                    available_qty_change=result.delivery_amount,
            )
        elif direction == 'sell':
            account_id = order_detail['account_id']
            update_account_balance(
                    account_id=account_id,
                    data_source=data_source,
                    available_cash_change=result.delivery_amount,
            )
        else:
            raise ValueError(f'Invalid direction: {direction}')
        update_trade_result(
                result_id=result_id,
                data_source=data_source,
                delivery_status='DL',
        )


def process_trade_result(raw_trade_result, data_source=None, config=None):
    """ 处理交易结果: 更新交易委托的状态，更新账户的持仓，更新持有现金金额

    交易结果一旦生成，其内容就不会再改变，因此不需要更新交易结果，只需要根据交易结果
    更新相应交易信号（委托）的状态，更新账户的持仓，更新账户的现金余额

    Parameters
    ----------
    raw_trade_result: dict
        原始交易结果, 与正式交易结果的区别在于，原始交易结果不包含execution_time字段
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    config: dict, optional
        配置参数, 默认为None, 表示使用默认的配置参数

    Returns
    -------
    None
    """

    if not isinstance(raw_trade_result, dict):
        raise TypeError(f'raw_trade_result must be a dict, got {type(raw_trade_result)} instead')

    order_id = raw_trade_result['order_id']
    order_detail = read_trade_order_detail(order_id, data_source=data_source)

    # 确认交易信号的状态不为 'created'. 'filled' or 'canceled'，如果是，则抛出异常
    if order_detail['status'] in ['created', 'filled', 'canceled']:
        raise RuntimeError(f'signal {order_id} has already been filled or canceled')
    # 交割历史交易结果
    if config is None:
        import qteasy as qt
        config = qt.QT_CONFIG
    if not isinstance(config, dict):
        raise TypeError('config must be a dict')
    process_trade_delivery(account_id=order_detail['account_id'], data_source=data_source, config=config)

    # 读取交易信号的历史交易记录，计算尚未成交的数量：remaining_qty
    trade_results = read_trade_results_by_order_id(order_id, data_source=data_source)
    filled_qty = trade_results['filled_qty'].sum() if trade_results is not None else 0
    remaining_qty = order_detail['qty'] - filled_qty
    if not isinstance(remaining_qty, (int, float, np.int64, np.float64)):
        import pdb; pdb.set_trace()
        raise RuntimeError(f'qty {order_detail["qty"]} is not an integer')
    # 如果交易结果中的cancel_qty大于0，则将交易信号的状态设置为'canceled'，同时确认cancel_qty等于remaining_qty
    if raw_trade_result['canceled_qty'] > 0:
        if raw_trade_result['canceled_qty'] != remaining_qty:
            raise RuntimeError(f'canceled_qty {raw_trade_result["canceled_qty"]} '
                               f'does not match remaining_qty {remaining_qty}')
        order_detail['status'] = 'canceled'
    # 如果交易结果中的canceled_qty等于0，则检查filled_qty的数量是大于remaining_qty，如果大于，则抛出异常
    else:
        if raw_trade_result['filled_qty'] > remaining_qty:
            raise RuntimeError(f'filled_qty {raw_trade_result["filled_qty"]} '
                               f'is greater than remaining_qty {remaining_qty}')

        # 如果filled_qty等于remaining_qty，则将交易信号的状态设置为'filled'
        elif raw_trade_result['filled_qty'] == remaining_qty:
            order_detail['status'] = 'filled'

        # 如果filled_qty小于remaining_qty，则将交易信号的状态设置为'partially_filled'
        elif raw_trade_result['filled_qty'] < remaining_qty:
            order_detail['status'] = 'partial-filled'

    # 计算交易后持仓数量的变化 position_change 和现金的变化值 cash_change
    position_change = raw_trade_result['filled_qty']
    if order_detail['direction'] == 'sell':
        cash_change = raw_trade_result['filled_qty'] * raw_trade_result['price'] - raw_trade_result['transaction_fee']
    elif order_detail['direction'] == 'buy':
        cash_change = - raw_trade_result['filled_qty'] * raw_trade_result['price'] - raw_trade_result['transaction_fee']

    # 如果position_change小于available_position_amount，则抛出异常
    available_qty = get_position_by_id(order_detail['pos_id'], data_source=data_source)['available_qty']
    if available_qty + position_change < 0:
        raise RuntimeError(f'position_change {position_change} is greater than '
                           f'available position amount {available_qty}')

    # 如果cash_change小于available_cash，则抛出异常
    available_cash = get_account_cash_availabilities(order_detail['account_id'], data_source=data_source)[1]
    if available_cash + cash_change < 0:
        raise RuntimeError(f'cash_change {cash_change} is greater than '
                           f'available cash {available_cash}')

    # 计算并生成交易结果的交割数量和交割状，如果是买入信号，交割数量为position_change，如果是卖出信号，交割数量为cash_change
    if order_detail['direction'] == 'buy':
        raw_trade_result['delivery_amount'] = position_change
    elif order_detail['direction'] == 'sell':
        raw_trade_result['delivery_amount'] = cash_change
    else:
        raise ValueError(f'direction must be buy or sell, got {order_detail["direction"]} instead')
    raw_trade_result['delivery_status'] = 'ND'
    # 生成交易结果的execution_time字段，保存交易结果
    execution_time = pd.to_datetime('now', utc=True).tz_convert(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    raw_trade_result['execution_time'] = execution_time
    write_trade_result(raw_trade_result, data_source=data_source)

    # 更新账户的持仓和现金余额:

    # 如果direction为buy，则同时更新cash_amount和available_cash，如果direction为sell，则只更新cash_amount
    if order_detail['direction'] == 'buy':
        update_account_balance(
                account_id=order_detail['account_id'],
                data_source=data_source,
                cash_amount_change=cash_change,
                available_cash_change=cash_change,
        )
        update_position(
                position_id=order_detail['pos_id'],
                data_source=data_source,
                qty_change=position_change,
        )
    # 如果direction为sell，则同时更新qty和available_qty，如果direction为buy，则只更新qty
    elif order_detail['direction'] == 'sell':
        update_account_balance(
                account_id=order_detail['account_id'],
                data_source=data_source,
                cash_amount_change=cash_change,
        )
        update_position(
                position_id=order_detail['pos_id'],
                data_source=data_source,
                qty_change=-position_change,
                available_qty_change=-position_change,
        )
    else:
        raise RuntimeError(f'invalid direction {order_detail["direction"]}')
    # 更新交易信号的状态
    update_trade_order(order_id, data_source=data_source, status=order_detail['status'])


def output_account_position(account_id, position_id):
    """ 将账户的持仓输出到终端或TUI

    Parameters
    ----------
    account_id: int
        账户的id
    position_id: int
        持仓的id

    Returns
    -------
    None
    """
    pass


def generate_trade_result(order_id, account_id):
    """ 生成交易结果

    Parameters
    ----------
    order_id: int
        交易信号的id
    account_id: int
        账户的id

    Returns
    -------
    trade_results: dict
        交易结果
    """
    pass

