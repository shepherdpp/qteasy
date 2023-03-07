# coding=utf-8
# ======================================
# File:     trading.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-02-20
# Desc:
#   functions that generates, submits
# operation signals and processes
# their results in live trade mode.
# ======================================

import asyncio

import pandas as pd
import numpy as np


async def process_trade_signal(signal):
    # 将交易信号提交给交易平台或用户以获取交易结果
    trade_results = await submit_signal(signal)
    # 更新交易信号状态并更新TUI
    update_signal_status(signal_id=signal['signal_id'], status=trade_results['status'])
    output_trade_signal()
    # 更新账户的持仓
    update_account_position(account_id=signal['account_id'], position=trade_results['position_type'])
    # 更新账户的可用资金
    update_account(account_id=signal['account_id'], trade_results=trade_results)
    # 刷新TUI
    output_account_position()


async def live_trade_signals():
    while True:
        # 检查交易策略的运行状态：
        # 当有交易策略处于"运行"状态时，生成交易信号
        signal = generate_signal()
        # 解析交易信号，将其转换为标准的交易信号
        signal = parse_trade_signal(signal, config)
        # 检查账户的可用资金是否充足
        if not check_account_availability(account_id=signal['account_id']):
            continue
        # 检查账户的持仓是否允许下单
        if not check_position_availability(account_id=signal['account_id']):
            continue
        # 将交易信号写入数据库
        signal_id = record_trade_signal(signal)
        # 读取交易信号并将其显示在界面上
        display_trade_signal(read_trade_signal(signal_id=signal_id))
        # 提交交易信号并等待结果
        asyncio.create_task(process_trade_signal(signal))
        # 继续生成后续交易信号
        await asyncio.sleep(1)

#
# asyncio.run(live_trade_signals())


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
    # 产生计划买进和卖出数量后，逐一生成交易信号：
    # 检查所有持仓，获取已有持仓的id，如果没有持仓，需要创建一个新的持仓获得持仓id
    # 生成交易信号
    submitted_qty = 0
    for sym, pos, d, qty in zip(symbols, positions, directions, quantities):
        pos_id = get_or_create_position(
            account_id=account_id,
            symbol=sym,
            position_type=pos,
        )
        trade_signal = {
            'account_id': account_id,
            'pos_id': pos_id,
            'direction': d,
            'order_type': order_type,
            'qty': qty,
            'price': get_price(),
            'submitted_time': pd.to_datetime('now'),
            'status': 'created',
        }
        # 逐一提交交易信号
        if submit_signal(trade_signal) is not None:

            # 记录已提交的交易数量
            submitted_qty += qty

    return submitted_qty


def parse_trade_signal(signals, signal_type, shares, prices, own_amounts, own_cash, config):
    """ 根据signal_type的值，将operator生成的qt交易信号解析为标准的交易信号，包括
    资产代码、头寸类型、交易方向、交易数量等

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
        账户可用资金
    config: dict
        交易信号的配置

    Returns
    -------
    tuple, (symbols, positions, directions, quantities)
        symbols: list, 交易信号对应的股票代码
        positions: list, 交易信号对应的持仓类型
        directions: list, 交易信号对应的交易方向
        quantities: list, 交易信号对应的交易数量
    """

    # 读取signal的值，根据signal_type确定如何解析交易信号

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

    # 将计算出的买入和卖出的数量转换为交易信号
    symbols, positions, directions, quantities = itemize_trade_signals(
        shares=shares,
        cash_to_spend=cash_to_spend,
        amounts_to_sell=amounts_to_sell,
        prices=prices
    )
    return symbols, positions, directions, quantities


# TODO: 将parse_pt/ps/vs_signals函数作为通用函数，在core.py中直接引用这三个函数的返回值
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


def itemize_trade_signals(shares, cash_to_spend, amounts_to_sell, prices):
    """ 逐个计算每一只资产的买入和卖出的数量，将parse_pt/ps/vs_signal函数计算出的交易信号逐项拆分
    成为交易信号的各个元素，以便于后续生成交易信号

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

    Returns
    -------
    tuple: (symbols, positions, directions, quantities)
    - symbols: list of str, 产生交易信号的资产代码
    - positions: list of str, 产生交易信号的各各资产的头寸类型('long', 'short')
    - directions: list of str, 产生的交易信号的交易方向('buy', 'sell')
    - quantities: list of float, 所有交易信号的交易数量
    """
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
        if cash_to_spend[i] < -0.001:
            # 计算买入的数量
            quantity = -cash_to_spend[i] / prices[i]
            symbols.append(sym)
            positions.append('short')
            directions.append('buy')
            quantities.append(quantity)
        # 计算多头卖出的数量
        if amounts_to_sell[i] < -0.001:
            # 计算卖出的数量
            quantity = -amounts_to_sell[i]
            symbols.append(sym)
            positions.append('long')
            directions.append('sell')
            quantities.append(quantity)
        # 计算空头卖出的数量
        if amounts_to_sell[i] > 0.001:
            # 计算卖出的数量
            quantity = amounts_to_sell[i]
            symbols.append(sym)
            positions.append('short')
            directions.append('sell')
            quantities.append(quantity)

    return symbols, positions, directions, quantities


def new_account(user_name, cash_amount, **account_data):
    """ 创建一个新的账户

    Parameters
    ----------
    user_name: str
        用户名
    cash_amount: float
        账户的初始资金
    account_data: dict
        账户的其他信息

    Returns
    -------
    int: 账户的id
    """
    import qteasy.QT_DATA_SOURCE as data_source
    account_id = data_source.write_sys_table_data(
        'sys_op_live_accounts',
        user_name=user_name,
        created_time=pd.to_datetime('now'),
        cash_amount=cash_amount,
        **account_data,
    )
    return account_id


def check_account_availability(account_id, requested_amount):
    """ 检查账户的可用资金是否充足

    Parameters
    ----------
    account_id: int
        账户的id
    requested_amount: float
        交易所需的资金

    Returns
    -------
    float: 可用资金相对于交易所需资金的比例，如果可用资金大于交易所需资金，则返回1.0
    """

    import qteasy.QT_DATA_SOURCE as data_source
    account = data_source.read_sys_table_data('sys_op_live_accounts', id=account_id)
    if account is None:
        raise RuntimeError('Account not found!')
    available_amount = account['available_amount']
    if available_amount == 0:
        return 0.0
    if available_amount >= requested_amount:
        return 1.0
    return available_amount / requested_amount


def update_account(account_id, **account_data):
    """ 更新账户信息

    通用接口，用于更新账户的所有信息，除了账户的持仓和可用资金
    以外，还包括账户的其他状态变量

    Parameters
    ----------
    account_id: int
        账户的id
    account_data: dict
        交易结果

    Returns
    -------
    None
    """
    import qteasy.QT_DATA_SOURCE as data_source
    data_source.update_sys_table_data('sys_op_live_accounts', id=account_id, **account_data)


def update_account_balance(account_id, **cash_change):
    """ 更新账户的资金总额和可用资金

    Parameters
    ----------
    account_id: int
        账户的id
    cash_change: dict, optional {'cash_amount_change': float, 'available_cash_change': float}
        可用资金的变化，其余字段不可用此函数修改

    Returns
    -------
    None
    """
    import qteasy.QT_DATA_SOURCE as data_source

    account_data = data_source.read_sys_table_data('sys_op_live_accounts', id=account_id)
    cash_amount = account_data['cash_amount_change']
    available_cash = account_data['available_cash_change']
    if 'cash_amount_change' in cash_change:
        cash_amount += cash_change['cash_amount_change']
    if 'available_cash_change' in cash_change:
        available_cash += cash_change['available_cash_change']

    # 更新账户的资金总额和可用资金
    data_source.update_sys_table_data(
            'sys_op_live_accounts',
            id=account_id,
            cash_amount=cash_amount,
            available_cash=available_cash
    )


def get_or_create_position(account_id, symbol, position_type):
    """ 获取账户的持仓, 如果持仓不存在，则创建一条新的持仓记录

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str
        交易标的
    position_type: str, {'long', 'short'}
        持仓类型

    Returns
    -------
    dict: 持仓记录
    int: 如果持仓记录不存在，则创建一条新的空持仓记录，并返回新持仓记录的id
    """
    import qteasy.QT_DATA_SOURCE as data_source
    position = data_source.read_sys_table_data(
            'sys_op_live_positions',
            id=None,
            account_id=account_id,
            symbol=symbol,
            position=position_type
    )
    if position.empty:
        return data_source.insert_sys_table_data(
                'sys_op_live_positions',
                account_id=account_id,
                symbol=symbol,
                position=position_type,
                qty=0,
                avg_price=0
        )
    return position['id']


def get_account_positions(account_id):
    """ 获取账户的所有持仓

    Parameters
    ----------
    account_id: int
        账户的id

    Returns
    -------
    pandas.DataFrame or None: 账户的所有持仓
    """
    import qteasy.QT_DATA_SOURCE as data_source
    positions = data_source.read_sys_table_data(
            'sys_op_live_positions',
            id=None,
            account_id=account_id,
    )
    return positions


def check_position_availability(account_id, planned_qty, planned_pos):
    """ 检查账户的持仓是否允许下单

    Parameters
    ----------
    account_id: int
        账户的id
    planned_qty: int
        计划交易数量
    planned_pos: str
        计划交易的持仓

    Returns
    -------
    float: 可用于交易的资产相对于计划交易数量的比例，如果可用资产大于计划交易数量，则返回1.0
    """

    import qteasy.QT_DATA_SOURCE as data_source
    position = data_source.read_sys_table_data('sys_op_live_positions', id=None, account_id=account_id)
    if position is None:
        raise RuntimeError('Position not found!')
    if position['position_type'] != planned_pos:
        return 0.0
    available_qty = position['available_qty']
    if available_qty == 0:
        return 0.0
    if available_qty >= planned_qty:
        return 1.0
    return available_qty / planned_qty


def update_position(position_id, **position_data):
    """ 更新账户的持仓，包括持仓的数量和可用数量，account_id, position和symbol不可修改

    Parameters
    ----------
    position_id: int
        持仓的id
    position_data: dict, optional, {'qty_change': int, 'available_qty_change': int}
        持仓的数据，只能修改qty, available_qty两类数据中的任意一个或多个

    Returns
    -------
    None
    """
    import qteasy.QT_DATA_SOURCE as data_source
    # 从数据库中读取持仓数据，修改后再写入数据库
    position = data_source.read_sys_table_data('sys_op_live_positions', id=position_id)
    if qty_change in position_data:
        position['qty'] += position_data['qty_change']
    if available_qty_change in position_data:
        position['available_qty'] += position_data['available_qty_change']

    data_source.update_sys_table_data('sys_op_live_positions', id=position_id, **position)


def record_trade_signal(signal):
    """ 将交易信号写入数据库

    Parameters
    ----------
    signal: dict
        标准形式的交易信号

    Returns
    -------
    signal_id: int
    写入数据库的交易信号的id
    """
    import qteasy.QT_DATA_SOURCE as data_source
    return data_source.insert_sys_table_data('sys_op_trade_signals', signal)


def update_trade_signal(signal_id, trade_results):
    """ 将交易结果更新到数据库中的交易信号

    Parameters
    ----------
    signal_id: int
        交易信号的id
    trade_results: dict
        交易结果

    Returns
    -------
    None
    """
    import qteasy.QT_DATA_SOURCE as data_source
    trade_signal = data_source.read_sys_table_data('sys_op_trade_signals', id=signal_id)

    if trade_signal is None:
        raise RuntimeError(f'Trade signal (signal_id = {signal_id}) not found!')

    # 如果canceled quantity大于0，则说明交易信号已经被取消
    if trade_results['canceled_qty'] > 0:
        trade_signal['status'] = 'canceled'
        # 计算需要revert的可用现金数量及计划交易数量
        planned_symbol = trade_signal['symbol']
        planned_qty = trade_signal['qty']
        planned_price = trade_signal['price']
        planned_amount = planned_qty * planned_price

        return

    # 如果filled quantity大于0，但小于交易信号委托数量，则说明交易信号部分执行
    elif (trade_results['filled_qty'] > 0) and (trade_results['filled_qty'] < trade_signal['qty']):
        trade_signal['status'] = 'partial'

    # 如果filled quantity等于交易信号委托数量，则说明交易信号全部执行
    elif trade_results['filled_qty'] == trade_signal['qty']:
        trade_signal['status'] = 'filled'

    else:  # 其他情况报错
        raise RuntimeError(f'Unexpected trade results: {trade_results}')

    # 计算需要更新的现金、可用现金数量及持仓数量、可用持仓数量 TODO: 以下代码由Copilot生成，需要进一步调整
    trade_position = trade_signal['position_type']
    trade_symbol = trade_signal['symbol']
    filled_qty = trade_results['filled_qty']
    filled_price = trade_results['price']
    transaction_fee = trade_results['transaction_fee']
    cash_change = 0.0
    position_change = 0.0
    # 如果是买入股票，则现金会减少，持仓会增加
    # 新增的持仓进入交割清单，等待交割
    if trade_signal['direction'] == 'buy':
        cash_change = - filled_qty * filled_price - transaction_fee
        position_change = trade_results['filled_qty']
    # 如果是卖出股票，则现金会增加，持仓会减少
    # 卖出的持仓进入交割清单，等待交割
    elif trade_signal['direction'] == 'sell':
        cash_change = filled_qty * filled_price - transaction_fee
        position_change = - trade_results['filled_qty']

    # 更新account和position的变化
    account_id = trade_signal['account_id']
    position_id = trade_signal['pos_id']

    # TODO: 需要引入delivery list机制，以便在交割清单中记录交易信号的交割过程
    update_account_balance(
            account_id=account_id,
            cash_amount_change=cash_change,
            position_amount_change=position_change
    )
    update_position(
            position_id=position_id,
            qty_change=position_change,
            available_qty_change=position_change
    )

    data_source.insert_sys_table_data('sys_op_trade_results', trade_results)
    return


def read_trade_signal(signal_id):
    """ 从数据库中读取交易信号

    Parameters
    ----------
    signal_id: int
        交易信号的id

    Returns
    -------
    signal: dict
        交易信号
    """
    import qteasy.QT_DATA_SOURCE as data_source
    return data_source.read_sys_table_data('sys_op_trade_signals', id=signal_id)


def query_trade_signal(account_id, symbol, direction, status):
    """ 从数据库中查询交易信号

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str
        交易标的
    direction: str
        交易方向
    status: str
        交易信号状态

    Returns
    -------
    signals: list
        交易信号列表
    """
    import qteasy.QT_DATA_SOURCE as data_source
    return data_source.read_sys_table_data(
        'sys_op_trade_signals',
        account_id=account_id,
        symbol=symbol,
        direction=direction,
        status=status
    )


def output_trade_signal():
    """ 将交易信号输出到终端或TUI

    Returns
    -------
    signal_id: int
        交易信号的id
    """
    pass


def submit_signal(trade_signal):
    """ 将交易信号提交给交易平台或用户以等待交易结果

    交易结果可以来自用户输入，也可以来自交易平台的返回，在这个函数中不等待交易结果，而是将交易信号写入数据库，然后返回交易信号的id

    Parameters
    ----------
    trade_signal: dict
        标准格式交易信号

    Returns
    -------
    int, 交易信号的id
    """
    # 如果交易信号的状态不为created，则说明交易信号已经提交过，不需要再次提交
    if not trade_signal['status'] == 'created':
        return None

    # 如果交易方向为buy，则需要检查账户的现金是否足够 TODO: position为short时做法不同，需要进一步调整
    if trade_signal['direction'] == 'buy':
        account_id = trade_signal['account_id']
        account = read_account(account_id)
        # 如果账户的现金不足，则按比例调整交易信号的委托数量
        if account['available_cash'] < trade_signal['qty'] * trade_signal['price']:
            proportion = (trade_signal['qty'] * trade_signal['price']) / account['available_cash']
            trade_signal['qty'] = trade_signal['qty'] * proportion
        else:
            pass
        # 调整账户的可用现金余额, 并更新到数据表中
        account['available_cash'] = account['available_cash'] - trade_signal['qty'] * trade_signal['price']
        update_account(account_id, available_cash=account['available_cash'])

    # 如果交易方向为sell，则需要检查账户的持仓是否足够 TODO: position为short时做法不一样，需要考虑
    elif trade_signal['direction'] == 'sell':
        position_id = trade_signal['pos_id']
        position = read_position(position_id)
        # 如果账户的持仓不足，则最多只能卖出账户的持仓数量
        if position['available_qty'] < trade_signal['qty']:
            trade_signal['qty'] = position['available_qty']
        else:
            pass
        # 调整账户的可用持仓余额，并更新到数据表中
        position['available_qty'] = position['available_qty'] - trade_signal['qty']
        update_position(position_id, available_qty=position['available_qty'])

    # 将signal的status改为"submitted"，并将trade_signal写入数据库
    trade_signal['status'] = 'submitted'
    signal_id = record_trade_signal(trade_signal)
    # 检查交易信号

    return signal_id


def generate_trade_result(signal_id, account_id):
    """ 生成交易结果

    Parameters
    ----------
    signal_id: int
        交易信号的id
    account_id: int
        账户的id

    Returns
    -------
    trade_results: dict
        交易结果
    """
    pass


def record_trade_result(trade_results):
    """ 将交易结果写入数据库

    Parameters
    ----------
    trade_results: dict
        交易结果

    Returns
    -------
    result_id: int
        交易结果的id
    """
    import qteasy.QT_DATA_SOURCE as data_source
    return data_source.write_sys_table_data('sys_op_trade_results', trade_results)


def read_trade_result(result_id):
    """ 从数据库中读取交易结果

    Parameters
    ----------
    result_id: int
        交易结果的id

    Returns
    -------
    trade_results: dict
        交易结果
    """
    import qteasy.QT_DATA_SOURCE as data_source
    return data_source.read_sys_table_data('sys_op_trade_results', id=result_id)


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

