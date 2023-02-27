# coding=utf-8
# ======================================
# File:     live_trade.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-02-20
# Desc:
#   functions that generates, submits
# operation signals and processes
# their results in live trade mode.
# ======================================

import asyncio


async def process_trade_signal(signal):
    # 将交易信号提交给交易平台或用户以获取交易结果
    trade_results = await submit_signal(signal)
    # 更新交易信号状态并更新TUI
    update_signal_status(signal_id=signal['signal_id'], status=trade_results['status'])
    output_trade_signal()
    # 更新账户的持仓
    update_account_position(account_id=signal['account_id'], position=trade_results['position'])
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
        signal = parse_trade_signal(signal)
        # 检查账户的可用资金是否充足
        if not check_account_availability():
            continue
        # 检查账户的持仓是否允许下单
        if not check_position_availability():
            continue
        # 将交易信号写入数据库
        signal_id = record_trade_signal(signal)
        # 读取交易信号并将其显示在界面上
        display_trade_signal(read_trade_signal(signal_id=signal_id))
        # 提交交易信号并等待结果
        asyncio.create_task(process_trade_signal(signal))
        # 继续生成后续交易信号
        await asyncio.sleep(1)


asyncio.run(live_trade_signals())


# all functions for live trade

def generate_signal():
    """ 从Operator对象中生成qt交易信号

    Returns
    -------
    signal: ndarray
        交易信号
    """
    pass


def parse_trade_signal(signal, config):
    """ 根据signal_type的值，将operator生成的qt交易信号解析为标准的交易信号，包括


    Parameters
    ----------
    signal: np.ndarray
        交易信号
    config: dict
        交易信号的配置

    Returns
    -------
    tuple of dict:
    ({
        symbol:
        position:
        direction:
        order_type:
        qty:
        price:
        submitted_time:
        status:
    }, ...)
    """

    trade_signal = {
        'symbol': None,
        'position': None,
        'direction': None,
        'order_type': None,
        'qty': None,
        'price': None,
        'submitted_time': None,
        'status': 'submitted',
    }
    pass


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


def update_account(account_id, trade_results):
    """ 更新账户信息

    通用接口，用于更新账户的所有信息，除了账户的持仓和可用资金
    以外，还包括账户的其他状态变量

    Parameters
    ----------
    account_id: int
        账户的id
    trade_results: dict
        交易结果

    Returns
    -------
    None
    """
    pass


def update_account_balance(account_id, balance_change):
    """ 更新账户的可用资金

    Parameters
    ----------
    account_id: int
        账户的id
    balance_change: float
        可用资金的变化量

    Returns
    -------
    None
    """
    pass


def update_account_available_amount(account_id, amount_change):
    """ 更新账户的可用资金

    Parameters
    ----------
    account_id: int
        账户的id
    amount_change: float
        可用资金的变化量

    Returns
    -------
    None
    """
    pass


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
    if position['position'] != planned_pos:
        return 0.0
    available_qty = position['available_qty']
    if available_qty == 0:
        return 0.0
    if available_qty >= planned_qty:
        return 1.0
    return available_qty / planned_qty


def update_position(account_id, position_id, trade_results):
    """ 更新账户的持仓

    Parameters
    ----------
    account_id: int
        账户的id
    position_id: int
        持仓的id
    trade_results: dict
        交易结果

    Returns
    -------
    None
    """
    pass


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

    data_source.insert_sys_table_data('sys_op_trade_results', trade_results)

    # 如果canceled quantity大于0，则说明交易信号已经被取消
    if trade_results['canceled_qty'] > 0:
        trade_signal['status'] = trade_signal['status'] + 'canceled'
        # 计算需要revert的可用现金数量及计划交易数量
        planned_symbol = trade_signal['symbol']
        planned_qty = trade_signal['qty']
        planned_price = trade_signal['price']
        planned_amount = planned_qty * planned_price

        return

    # 如果filled quantity大于0，但小于交易信号委托数量，则说明交易信号部分执行
    elif (trade_results['filled_qty'] > 0) and (trade_results['filled_qty'] < trade_signal['qty']):
        trade_signal['status'] = trade_signal['status'] + 'partially_filled'

    # 如果filled quantity等于交易信号委托数量，则说明交易信号全部执行
    elif trade_results['filled_qty'] == trade_signal['qty']:
        trade_signal['status'] = trade_signal['status'] + 'filled'

    else:  # 其他情况报错
        raise RuntimeError(f'Unexpected trade results: {trade_results}')

    # 计算需要更新的现金、可用现金数量及持仓数量、可用持仓数量 TODO: 以下代码由Copilot生成，需要进一步调整
    # 如果是多头买进或空头卖出，则需要更新现金、可用现金数量
    if (trade_signal['position'] == 'long') and (trade_signal['side'] == 'buy' or trade_signal['side'] == 'cover'):
        cash_change = - trade_results['filled_qty'] * trade_results['filled_price'] - trade_results['transaction_fee']
        available_cash_change = cash_change
        position_change = trade_results['filled_qty']
        available_position_change = position_change
    # 如果是多头卖出或空头买进，则需要更新持仓、可用持仓数量
    elif (trade_signal['position'] == 'long') and (trade_signal['side'] == 'sell' or trade_signal['side'] == 'short'):
        cash_change = trade_results['filled_qty'] * trade_results['filled_price'] - trade_results['transaction_fee']
        available_cash_change = cash_change
        position_change = - trade_results['filled_qty']
        available_position_change = position_change
    # 如果是空头买进或多头卖出，则需要更新现金、可用现金数量
    elif (trade_signal['position'] == 'short') and (trade_signal['side'] == 'buy' or trade_signal['side'] == 'cover'):
        cash_change = trade_results['filled_qty'] * trade_results['filled_price'] - trade_results['transaction_fee']
        available_cash_change = cash_change
        position_change = - trade_results['filled_qty']
        available_position_change = position_change
    # 如果是空头卖出或多头买进，则需要更新持仓、可用持仓数量
    elif (trade_signal['position'] == 'short') and (trade_signal['side'] == 'sell' or trade_signal['side'] == 'short'):
        cash_change = - trade_results['filled_qty'] * trade_results['filled_price'] - trade_results['transaction_fee']
        available_cash_change = cash_change
        position_change = trade_results['filled_qty']
        available_position_change = position_change
    else:
        raise RuntimeError(f'Unexpected trade signal: {trade_signal}')
    # 更新account和position的变化
    account_id = trade_signal['account_id']
    position_id = trade_signal['position_id']
    update_account_balance(account_id, cash_change)
    update_account_available_amount(account_id, available_cash_change)
    update_position_amount(position_id, position_change)
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


def output_trade_signal():
    """ 将交易信号输出到终端或TUI

    Returns
    -------
    signal_id: int
        交易信号的id
    """
    pass


def submit_signal(signal):
    """ 将交易信号提交给交易平台或用户以等待交易结果

    交易结果可以来自用户输入，也可以来自交易平台的返回

    Parameters
    ----------
    signal: dict
        交易信号

    Returns
    -------
    trade_results: dict
        交易结果
    """
    return get_trade_result(signal)


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


def write_trade_result(trade_results):
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
    pass


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
    pass


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

