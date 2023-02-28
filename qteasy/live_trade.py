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
    return trade_signal


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
    import qteasy.QT_DATA_SOURCE as data_source
    data_source.update_sys_table_data('sys_op_live_accounts', id=account_id, **trade_results)


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
    trade_position = trade_signal['position']
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

