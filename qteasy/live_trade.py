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


def pars_trade_signal(signal, sig_type):
    """ 根据signal_type的值，将operator生成的qt交易信号解析为包含标准的交易信号，包括


    Parameters
    ----------
    signal: np.ndarray
    sig_type:

    Returns
    -------
    tuple of dict:
    ({
        symbol:
        position:
        direction:
        qty:
        price:
    }, ...)
    """

    pass


def check_account_availability(account_id):
    """ 检查账户的可用资金是否充足

    Parameters
    ----------
    account_id: int
        账户的id

    Returns
    -------
    bool:
        True if account has enough available funds
    """
    pass


def update_account(account_id, trade_results):
    """ 更新账户的可用资金

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


def check_position_availability(account_id, position_id):
    """ 检查账户的持仓是否允许下单

    Parameters
    ----------
    account_id: int
        账户的id
    position_id: int
        持仓的id

    Returns
    -------
    bool:
        True if account has enough available positions
    """
    pass


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
    pass


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
    pass


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
    pass


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

