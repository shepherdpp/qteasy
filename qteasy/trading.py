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

from qteasy.database import DataSource


# TODO: 创建一个模块级变量，用于存储交易信号的数据源，所有的交易信号都从这个数据源中读取
#  避免交易信号从不同的数据源中获取，导致交易信号的不一致性
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
    submitted_qty = 0
    for sym, pos, d, qty in zip(symbols, positions, directions, quantities):
        pos_id = get_or_create_position(
            account_id=account_id,
            symbol=sym,
            position_type=pos,
        )
        # 如果是卖出信号，检查是否有足够的可用持仓，如果可用持仓不足，降低交易数量
        if d == 'sell':
            qty = check_position_availability(account_id=account_id, symbol=sym, qty=qty)

        # 生成交易信号dict
        trade_signal = {
            'account_id': account_id,
            'pos_id': pos_id,
            'direction': d,
            'order_type': order_type,
            'qty': qty,
            'price': get_price(),
            'submitted_time': None,
            'status': 'created',
        }
        record_trade_signal(trade_signal)
        # 逐一提交交易信号
        if submit_signal(trade_signal) is not None:

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
    """ 根据signal_type的值，将operator生成的qt交易信号解析为标准的交易信号，包括
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
    tuple, (symbols, positions, directions, quantities)
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
    symbols, positions, directions, quantities = itemize_trade_signals(
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


def itemize_trade_signals(shares,
                          cash_to_spend,
                          amounts_to_sell,
                          prices,
                          available_cash,
                          available_amounts,
                          allow_sell_short=False):
    """ 逐个计算每一只资产的买入和卖出的数量，将parse_pt/ps/vs_signal函数计算出的交易信号逐项拆分
    成为交易信号的各个元素，以便于后续生成交易信号

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
    tuple: (symbols, positions, directions, quantities)
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

    return symbols, positions, directions, quantities


# 7 foundational functions for account and position management
def new_account(user_name, cash_amount, data_source=None, **account_data):
    """ 创建一个新的账户

    Parameters
    ----------
    user_name: str
        用户名
    cash_amount: float
        账户的初始资金
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    account_data: dict
        账户的其他信息

    Returns
    -------
    int: 账户的id
    """
    # 输入数据检查在这里进行
    if cash_amount <= 0:
        raise ValueError('cash_amount must be positive!')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    account_id = data_source.insert_sys_table_data(
        'sys_op_live_accounts',
        user_name=user_name,
        created_time=pd.to_datetime('now'),
        cash_amount=cash_amount,
        available_cash=cash_amount,
        **account_data,
    )
    return account_id


def get_account(account_id, data_source=None):
    """ 根据account_id获取账户的信息

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    dict: 账户的信息
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    account = data_source.read_sys_table_data('sys_op_live_accounts', record_id=account_id)
    if account is None:
        raise RuntimeError('Account not found!')
    return account


def update_account(account_id, data_source=None, **account_data):
    """ 更新账户信息

    通用接口，用于更新账户的所有信息，除了账户的持仓和可用资金
    以外，还包括账户的其他状态变量

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    account_data: dict
        交易结果

    Returns
    -------
    None
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    data_source.update_sys_table_data('sys_op_live_accounts', record_id=account_id, **account_data)


def update_account_balance(account_id, data_source=None, **cash_change):
    """ 更新账户的资金总额和可用资金, 为了避免误操作，仅允许修改现金总额和可用现金，其他字段不可修改

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    cash_change: dict, optional {'cash_amount_change': float, 'available_cash_change': float}
        可用资金的变化，其余字段不可用此函数修改

    Returns
    -------
    None
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    account_data = data_source.read_sys_table_data('sys_op_live_accounts', record_id=account_id)
    if account_data is None:
        raise RuntimeError('Account not found!')

    cash_amount_change = cash_change.get('cash_amount_change', 0.0)
    if not isinstance(cash_amount_change, (int, float)):
        raise TypeError(f'cash_amount_change must be a number, got {type(cash_amount_change)} instead')
    cash_amount = account_data['cash_amount'] + cash_amount_change

    available_cash_change = cash_change.get('available_cash_change', 0.0)
    if not isinstance(available_cash_change, (int, float)):
        raise TypeError(f'available_cash_change must be a number, got {type(available_cash_change)} instead')
    available_cash = account_data['available_cash'] + available_cash_change

    # 如果可用现金超过现金总额，则报错
    if available_cash > cash_amount:
        raise RuntimeError(f'available_cash ({available_cash}) cannot be greater than cash_amount ({cash_amount})')
    # 如果可用现金小于0，则报错
    if available_cash < 0:
        raise RuntimeError(f'available_cash ({available_cash}) cannot be less than 0!')
    # 如果现金总额小于0，则报错
    if cash_amount < 0:
        raise RuntimeError(f'cash_amount cannot be less than 0!')

    # 更新账户的资金总额和可用资金
    data_source.update_sys_table_data(
            'sys_op_live_accounts',
            record_id=account_id,
            cash_amount=cash_amount,
            available_cash=available_cash
    )


def get_position_by_id(pos_id, data_source=None):
    """ 通过pos_id获取持仓的信息

    Parameters
    ----------
    pos_id: int
        持仓的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    dict: 持仓的信息
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    position = data_source.read_sys_table_data('sys_op_positions', record_id=pos_id)
    if position is None:
        raise RuntimeError('Position not found!')
    return position


def get_position_ids(account_id, symbol=None, position_type=None, data_source=None):
    """ 根据symbol和position_type获取账户的持仓id, 如果没有持仓，则返回空列表, 如果有多个持仓，则返回所有持仓的id

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str, optional
        交易标的的代码
    position_type: str, optional, {'long', 'short'}
        持仓类型, 'long' 表示多头持仓, 'short' 表示空头持仓
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    position_ids: list of int: 持仓的id列表
    None: 如果没有持仓, 则返回None
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 获取账户的持仓
    position_filter = {'account_id': account_id}
    if symbol is not None:
        position_filter['symbol'] = str(symbol)
    if position_type is not None:
        position_filter['position'] = str(position_type)

    try:
        position = data_source.read_sys_table_data(
                table='sys_op_positions',
                record_id=None,
                **position_filter,
        )
    except Exception as e:
        print(f'Error occurred: {e}')
        return None
    if position is None:
        return
    return position.index.tolist()


def get_or_create_position(account_id: int, symbol: str, position_type: str, data_source: DataSource=None):
    """ 获取账户的持仓, 如果持仓不存在，则创建一条新的持仓记录

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str
        交易标的的代码
    position_type: str, {'long', 'short'}
        持仓类型, 'long'表示多头持仓, 'short'表示空头持仓
    data_source: DataSource, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    dict: 如果symbol和position匹配的持仓记录已存在，则直接返回该记录的dict形式
    int: 如果匹配的持仓记录不存在，则创建一条新的空持仓记录，并返回新持仓记录的id
    """

    from qteasy import DataSource, QT_DATA_SOURCE
    if data_source is None:
        data_source = QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 检查account_id是否存在，如果不存在，则报错，否则创建的持仓记录将无法关联到账户
    account = get_account(account_id, data_source=data_source)
    if account is None:
        raise RuntimeError(f'account_id {account_id} not found!')

    if not isinstance(symbol, str):
        raise TypeError(f'symbol must be a str, got {type(symbol)} instead')
    if not isinstance(position_type, str):
        raise TypeError(f'position_type must be a str, got {type(position_type)} instead')
    if position_type not in ('long', 'short'):
        raise ValueError(f'position_type must be "long" or "short", got {position_type} instead')

    position = data_source.read_sys_table_data(
            table='sys_op_positions',
            record_id=None,
            account_id=account_id,
            symbol=symbol,
            position=position_type
    )
    if position is None:
        return data_source.insert_sys_table_data(
                table='sys_op_positions',
                account_id=account_id,
                symbol=symbol,
                position=position_type,
                qty=0,
                available_qty=0
        )
    # position已存，此时position中只能有一条记录，否则说明记录重复，报错
    if len(position) > 1:
        raise RuntimeError(f'position record is duplicated, got {len(position)} records: \n{position}')
    return position.iloc[0].to_dict()


def update_position(position_id, data_source=None, **position_data):
    """ 更新账户的持仓，包括持仓的数量和可用数量，account_id, position和symbol不可修改

    Parameters
    ----------
    position_id: int
        持仓的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    position_data: dict, optional, {'qty_change': int, 'available_qty_change': int}
        持仓的数据，只能修改qty, available_qty两类数据中的任意一个或多个

    Returns
    -------
    None
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 从数据库中读取持仓数据，修改后再写入数据库
    position = data_source.read_sys_table_data('sys_op_positions', record_id=position_id)
    if position is None:
        raise RuntimeError(f'position_id {position_id} not found!')

    qty_change = position_data.get('qty_change', 0.0)
    if not isinstance(qty_change, (int, float)):
        raise TypeError(f'qty_change must be a int or float, got {type(qty_change)} instead')
    position['qty'] += qty_change

    available_qty_change = position_data.get('available_qty_change', 0.0)
    if not isinstance(available_qty_change, (int, float)):
        raise TypeError(f'available_qty_change must be a int or float, got {type(available_qty_change)} instead')
    position['available_qty'] += available_qty_change

    # 如果可用数量超过持仓数量，则报错
    if position['available_qty'] > position['qty']:
        raise RuntimeError(f'available_qty ({position["available_qty"]}) cannot be greater than '
                           f'qty ({position["qty"]})')
    # 如果可用数量小于0，则报错
    if position['available_qty'] < 0:
        raise RuntimeError(f'available_qty ({position["available_qty"]}) cannot be less than 0!')
    # 如果持仓数量小于0，则报错
    if position['qty'] < 0:
        raise RuntimeError(f'qty ({position["qty"]}) cannot be less than 0!')

    data_source.update_sys_table_data('sys_op_positions', record_id=position_id, **position)


def get_account_positions(account_id, data_source=None):
    """ 根据account_id获取账户的所有持仓

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    pandas.DataFrame or None: 账户的所有持仓
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    positions = data_source.read_sys_table_data(
            'sys_op_positions',
            record_id=None,
            account_id=account_id,
    )
    return positions


# Four 2nd foundational functions for account and position availability check
def get_account_cash_availabilities(account_id, data_source=None):
    """ 根据账户id获取账户的可用资金和资金总额
    返回一个tuple，第一个元素是账户的可用资金，第二个元素是账户的资金总额

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    cash_availabilities: tuple, (float, float)
        账户的可用资金和资金总额
    """

    account = get_account(account_id=account_id, data_source=data_source)
    return account['available_cash'], account['cash_amount']


def get_account_position_availabilities(account_id, shares, data_source=None):
    """ 根据account_id读取账户的持仓，筛选出与shares相同的symbol的持仓，返回两个ndarray，分别为
    每一个share对应的持仓的数量和可用数量

    Parameters
    ----------
    account_id: int
        账户的id
    shares: list of str
        需要输出的持仓的symbol列表
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    tuple of two numpy.ndarray: 每一个share对应的持仓的数量和可用数量
    """

    # 根据account_id读取账户的全部持仓
    positions = get_account_positions(account_id=account_id, data_source=data_source)

    if positions.empty:
        return np.zeros(len(shares)), np.zeros(len(shares))

    own_amounts = []
    available_amounts = []
    for share in shares:
        # 检查symbol为share的持仓是否存在
        position = positions[(positions['symbol'] == share) & (positions['qty'] > 0)]
        if position.empty:
            own_amounts.append(0.0)
            available_amounts.append(0.0)
            continue
        # 如果存在多头持仓，则将多头持仓的数量和可用数量放入列表
        if position['position'] == 'long':
            own_amounts.append(position['qty'].values[0])
            available_amounts.append(position['available_qty'].values[0])
            continue
        # 如果存在空头持仓，则将空头持仓的数量和可用数量乘以-1并放入列表
        if position['position'] == 'short':
            own_amounts.append(-position['qty'].values[0])
            available_amounts.append(-position['available_qty'].values[0])
            continue
    # 如果列表长度与shares长度不相等，则报错
    if len(own_amounts) != len(shares):
        raise RuntimeError(f'own_amounts length ({len(own_amounts)}) is not equal to shares length ({len(shares)})')
    if len(available_amounts) != len(shares):
        raise RuntimeError(f'available_amounts length ({len(available_amounts)}) is not equal to '
                           f'shares length ({len(shares)})')
    # 将列表转换为ndarray并返回
    return np.array(own_amounts), np.array(available_amounts)


def check_account_availability(account_id, requested_amount, data_source=None):
    """ 检查账户的可用资金是否充足

    Parameters
    ----------
    account_id: int
        账户的id
    requested_amount: float or np.float64 or np.ndarray
        交易所需的资金
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    float: 可用资金相对于交易所需资金的比例，如果可用资金大于交易所需资金，则返回1.0

    Raises
    ------
    RuntimeError: 如果requested_amount小于0
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    if requested_amount == 0:
        return 1.0
    if requested_amount < 0:
        raise RuntimeError(f'requested_amount ({requested_amount}) cannot be less than 0!')
    account = get_account(account_id, data_source=data_source)
    available_cash = account['available_cash']
    if available_cash == 0:
        return 0.0
    if available_cash >= requested_amount:
        return 1.0
    return available_cash / requested_amount


def check_position_availability(account_id, symbol, position, planned_qty, data_source=None):
    """ 检查账户的持仓是否允许下单

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str
        交易标的的代码
    position: str, {'long', 'short'}
        计划交易的持仓类型, long为多头仓位，short为空头仓位
    planned_qty: float
        计划交易数量
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    float: 可用于交易的资产相对于计划交易数量的比例，如果可用资产大于计划交易数量，则返回1.0

    Raises
    ------
    RuntimeError: 如果计划交易数量为0，则报错
    RuntimeError: 如果计划交易数量小于0，则报错
    TypeError: 如果data_source不是DataSource实例，则报错
    RuntimeError: 如果持仓不存在，则报错
    RuntimeError: 如果持仓类型不匹配，则报错
    """

    if planned_qty == 0:
        return 1.0
    if planned_qty < 0:
        raise RuntimeError(f'planned_qty ({planned_qty}) cannot be less than 0!')
    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    position_read = get_or_create_position(account_id, symbol, position, data_source=data_source)
    if position_read is None:
        raise RuntimeError('Position not found!')
    if position_read['position'] != position:  # 根据持仓类型新建或读取数据，类型应该匹配
        raise RuntimeError(f'Position type not match: "{position_read["position"]}" != "{position}"')
    available_qty = position_read['available_qty']
    if available_qty == 0:
        return 0.0
    if available_qty >= planned_qty:
        return 1.0
    return available_qty / planned_qty


# 4 foundational functions for trade signal
def record_trade_signal(signal, data_source=None):
    """ 将交易信号写入数据库

    Parameters
    ----------
    signal: dict
        标准形式的交易信号
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    signal_id: int
    写入数据库的交易信号的id
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 检查交易信号的格式和数据合法性
    if not isinstance(signal, dict):
        raise TypeError(f'signal must be a dict, got {type(signal)} instead')
    if not isinstance(signal['pos_id'], int):
        raise TypeError(f'signal["pos_id"] must be an int, got {type(signal["pos_id"])} instead')
    if not isinstance(signal['direction'], str):
        raise TypeError(f'signal["direction"] must be a str, got {type(signal["direction"])} instead')
    if not isinstance(signal['order_type'], str):
        raise TypeError(f'signal["order_type"] must be a str, got {type(signal["order_type"])} instead')
    if not isinstance(signal['qty'], (float, int)):
        raise TypeError(f'signal["qty"] must be a float, got {type(signal["qty"])} instead')
    if not isinstance(signal['price'], (float, int)):
        raise TypeError(f'signal["price"] must be a float, got {type(signal["price"])} instead')
    if signal['qty'] <= 0:
        raise RuntimeError(f'signal["qty"] ({signal["qty"]}) must be greater than 0!')
    if signal['price'] <= 0:
        raise RuntimeError(f'signal["price"] ({signal["price"]}) must be greater than 0!')

    return data_source.insert_sys_table_data('sys_op_trade_signals', **signal)


def read_trade_signal(signal_id, data_source=None):
    """ 根据signal_id从数据库中读取交易信号

    Parameters
    ----------
    signal_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    signal: dict
        交易信号
    """
    if not isinstance(signal_id, int):
        raise TypeError(f'signal_id must be an int, got {type(signal_id)} instead')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    return data_source.read_sys_table_data('sys_op_trade_signals', record_id=signal_id)


def update_trade_signal(signal_id, data_source=None, status=None, raise_if_status_wrong=False):
    """ 更新数据库中trade_signal的状态或其他信，这里只操作trade_signal，不处理交易结果

    trade_signal的所有字段中，可以更新字段只有status。
    status的更新遵循下列规律：
    1. 如果status为 'created'，则可以更新为 'submitted';
    2. 如果status为 'submitted'，则可以更新为 'canceled', 'partial-filled' 或 'filled';
    3. 如果status为 'partial-filled'，则可以更新为 'canceled' 或 'filled';
    4. 如果status为 'canceled' 或 'filled'，则不可以再更新.

    Parameters
    ----------
    signal_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    status: str, optional
        交易信号的状态, 默认为None, 表示不更新状态
    raise_if_status_wrong: bool, default False
        如果status不符合规则，则抛出RuntimeError, 默认为False, 表示不抛出异常

    Returns
    -------
    signal_id: int, 如果更新成功，返回更新后的交易信号的id
    None, 如果更新失败，返回None

    Raises
    ------
    TypeError
        如果data_source不是DataSource的实例，则抛出TypeError
    RuntimeError
        如果trade_signal读取失败，则抛出RuntimeError
        如果status不符合规则，则抛出RuntimeError
    """

    if status is None:
        return None

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    trade_signal = data_source.read_sys_table_data('sys_op_trade_signals', record_id=signal_id)

    # 如果trade_signal读取失败，则报错
    if trade_signal is None:
        raise RuntimeError(f'Trade signal (signal_id = {signal_id}) not found!')

    # 如果trade_signal的状态为 'created'，则可以更新为 'submitted'
    if trade_signal['status'] == 'created' and status == 'submitted':
        return data_source.update_sys_table_data('sys_op_trade_signals', signal_id, status=status)
    # 如果trade_signal的状态为 'submitted'，则可以更新为 'canceled', 'partial-filled' 或 'filled'
    if trade_signal['status'] == 'submitted' and status in ['canceled', 'partial-filled', 'filled']:
        return data_source.update_sys_table_data('sys_op_trade_signals', signal_id, status=status)
    # 如果trade_signal的状态为 'partial-filled'，则可以更新为 'canceled' 或 'filled'
    if trade_signal['status'] == 'partial-filled' and status in ['canceled', 'filled']:
        return data_source.update_sys_table_data('sys_op_trade_signals', signal_id, status=status)

    if raise_if_status_wrong:
        raise RuntimeError(f'Wrong status update: {trade_signal["status"]} -> {status}')

    return


def query_trade_signals(account_id,
                        symbol=None,
                        position=None,
                        direction=None,
                        order_type=None,
                        status=None,
                        data_source=None):
    """ 根据symbol、direction、status 从数据库中查询交易信号并批量返回结果

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str, optional
        交易标的
    position: str, optional, {'long', 'short'}
        交易方向, 默认为None, 表示不限制, 'long' 表示多头, 'short' 表示空头
    direction: str, optional, {'buy', 'sell'}
        交易方向, 默认为None, 表示不限制, 'buy' 表示买入, 'sell' 表示卖出
    order_type: str, optional, {'market', 'limit', 'stop', 'stop_limit'}
        交易类型, 默认为None, 表示不限制, 'market' 表示市价单, 'limit' 表示限价单, 'stop' 表示止损单, 'stop_limit' 表示止损限价单
    status: str, optional, {'created', 'submitted', 'canceled', 'partial-filled', 'filled'}
        交易信号状态
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    signals: list
        交易信号列表
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 从数据库中读取position的id
    pos_ids = get_position_ids(account_id, symbol, position, data_source=data_source)
    if pos_ids is None:
        return None

    data_filter = {}
    if direction is not None:
        data_filter['direction'] = direction
    if order_type is not None:
        data_filter['order_type'] = order_type
    if status is not None:
        data_filter['status'] = status

    res = []
    for pos_id in pos_ids:
        res.append(
                data_source.read_sys_table_data(
                        'sys_op_trade_signals',
                        pos_id=pos_id,
                        **data_filter,
                )
        )
    if all(r is None for r in res):
        return None
    return pd.concat(res)


# 2 2nd level functions for trade signal
def read_trade_signal_detail(signal_id, data_source=None):
    """ 从数据库中读取交易信号的详细信息，包括从关联表中读取symbol和position的信息

    Parameters
    ----------
    signal_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    trade_signal_detail: dict
        包含symbol和position信息的交易信号明细
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    trade_signal_detail = read_trade_signal(signal_id, data_source=data_source)
    if trade_signal_detail is None:
        return None
    pos_id = trade_signal_detail['pos_id']
    position = get_position_by_id(pos_id, data_source=data_source)
    if position is None:
        raise RuntimeError(f'Position (position_id = {pos_id}) not found!')
    # 从关联表中读取symbol和position的信，添加到trade_signal_detail中
    trade_signal_detail['symbol'] = position['symbol']
    trade_signal_detail['position'] = position['position']
    return trade_signal_detail


def output_trade_signal():
    """ 将交易信号输出到终端或TUI

    Returns
    -------
    signal_id: int
        交易信号的id
    """
    pass


def submit_signal(signal_id, data_source=None):
    """ 将交易信号提交给交易平台或用户以等待交易结果

    只有刚刚创建的交易信号（status == 'created'）才能提交，否则不需要再次提交
    在提交交易信号以前，对于买入信号，会检查账户的现金是否足够，如果不足，则会按比例调整交易信号的委托数量
    对于卖出信号，会检查账户的持仓是否足够，如果不足，则会按比例调整交易信号的委托数量
    交易信号提交后，会将交易信号的状态设置为submitted，同时将交易信号保存到数据库中
    - 只有使用submit_signal才能将信号保存到数据库中，同时调整相应的账户和持仓信息

    Parameters
    ----------
    signal_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    int, 交易信号的id
    """

    # 读取交易信号
    trade_signal = read_trade_signal(signal_id, data_source=data_source)

    # 如果交易信号的状态不为created，则说明交易信号已经提交过，不需要再次提交
    if trade_signal['status'] != 'created':
        return None

    # 如果交易方向为buy，则需要检查账户的现金是否足够 TODO: position为short时做法不同，需要进一步调整
    if trade_signal['direction'] == 'buy':
        account_id = trade_signal['account_id']
        account = get_account(account_id, data_source=data_source)
        # 如果账户的现金不足，则按比例调整交易信号的委托数量
        if account['available_cash'] < trade_signal['qty'] * trade_signal['price']:
            proportion = (trade_signal['qty'] * trade_signal['price']) / account['available_cash']
            trade_signal['qty'] = trade_signal['qty'] * proportion
        else:
            pass
        # 调整账户的可用现金余额, 并更新到数据表中
        available_cash_change = -trade_signal['qty'] * trade_signal['price']
        update_account(account_id, data_source=data_source, available_cash_change=available_cash_change)

    # 如果交易方向为sell，则需要检查账户的持仓是否足够 TODO: position为short时做法不一样，需要考虑
    elif trade_signal['direction'] == 'sell':
        position_id = trade_signal['pos_id']
        position = get_position_by_id(position_id, data_source=data_source)
        # 如果账户的持仓不足，则最多只能卖出账户的持仓数量
        if position['available_qty'] < trade_signal['qty']:
            trade_signal['qty'] = position['available_qty']
        else:
            pass
        # 调整账户的可用持仓余额，并更新到数据表中
        available_qty_change = -trade_signal['qty']
        update_position(position_id, available_qty_change=available_qty_change)

    # 将signal的status改为"submitted"，并将trade_signal写入数据库
    trade_signal['status'] = 'submitted'
    signal_id = update_trade_signal(signal_id=signal_id, data_source=data_source, status='submitted')
    # 检查交易信号

    return signal_id


# foundational functions for trade result
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
    return data_source.read_sys_table_data('sys_op_trade_results', record_id=result_id)


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

