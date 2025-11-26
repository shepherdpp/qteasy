# coding=utf-8
# ======================================
# File:     config_parser.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-09-09
# Desc:
#   Functions used to parse specific
# useful information from qteasy config
# settings.
# ======================================

import pandas as pd
import numpy as np

from typing import Any, Union
from warnings import warn

from qteasy import QT_DATA_SOURCE
from qteasy.configure import ConfigDict
from qteasy.utilfuncs import next_market_trade_day, regulate_date_format, str_to_list
from qteasy.finance import CashPlan
from qteasy.history import get_history_data_packages, get_history_panel


def parse_backtest_start_end_dates(config) -> tuple[str, str]:
    """Parse investment start and end date from config settings."""

    invest_start = config.get('invest_start')
    invest_end = config.get('invest_end')

    if invest_end is None:
        invest_end = regulate_date_format(pd.Timestamp.today(), force_format='date')
    else:
        invest_end = regulate_date_format(invest_end, force_format='date')

    if invest_start is None:  # start is end - 1 year
        invest_start = regulate_date_format(pd.Timestamp(invest_end) - pd.DateOffset(years=1), force_format='date')
    else:
        invest_start = regulate_date_format(invest_start, force_format='date')

    if pd.to_datetime(invest_start) >= pd.to_datetime(invest_end):
        raise ValueError(f'invest_start {invest_start} should be earlier than invest_end {invest_end}')

    return invest_start, invest_end


def parse_backtest_cash_plan(config: Union[dict, ConfigDict]) -> CashPlan:
    """Parse investment cash plan from config settings."""
    # 投资回测区间的开始日期根据invest_start和invest_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    invest_start, invest_end = parse_backtest_start_end_dates(config=config)

    if config['invest_cash_dates'] is None:
        invest_start = next_market_trade_day(invest_start).strftime('%Y%m%d')
        return CashPlan(invest_start,
                                    config['invest_cash_amounts'][0],
                                    config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['invest_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        invest_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                    amounts=config['invest_cash_amounts'],
                                    interest_rate=config['riskfree_ir'])
        invest_start = regulate_date_format(invest_cash_plan.first_day)
        if pd.to_datetime(invest_start) != pd.to_datetime(config['invest_start']):
            warn(
                f'first cash investment on {invest_start} differ from invest_start {config["invest_start"]}, first cash'
                f' date will be used!',
                RuntimeWarning)

        return invest_cash_plan


def parse_trade_cost_params(config) -> dict:
    """解析交易成本相关的配置参数:
        buy_rate: float, 交易成本：固定买入费率
        sell_rate: float, 交易成本：固定卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slipage: float, 交易成本：滑点

    Returns
    -------
    trade_cost_params: dict
        交易成本相关的参数字典
    """
    cost_params = {
        'buy_rate': config['cost_rate_buy'],
        'sell_rate': config['cost_rate_sell'],
        'buy_min': config['cost_min_buy'],
        'sell_min': config['cost_min_sell'],
        'slippage': config['cost_slippage'],
    }
    # raise if parameters are out of range or with wrong types
    if not (isinstance(cost_params['buy_rate'], (float, int)) and 0 <= cost_params['buy_rate'] < 1):
        raise ValueError('cost_rate_buy should be a float number between 0 and 1')
    if not (isinstance(cost_params['sell_rate'], (float, int)) and 0 <= cost_params['sell_rate'] < 1):
        raise ValueError('cost_rate_sell should be a float number between 0 and 1')
    if not (isinstance(cost_params['buy_min'], (float, int)) and cost_params['buy_min'] >= 0):
        raise ValueError('cost_min_buy should be a non-negative float number')
    if not (isinstance(cost_params['sell_min'], (float, int)) and cost_params['sell_min'] >= 0):
        raise ValueError('cost_min_sell should be a non-negative float number')
    if not (isinstance(cost_params['slippage'], (float, int)) and 0 <= cost_params['slippage'] < 1):
        raise ValueError('cost_slipage should be a float number between 0 and 1')

    return cost_params


def parse_cash_invest_and_delivery_arrays(config: dict, op_schedule: pd.Index) -> (
        tuple[np.ndarray, np.ndarray, np.ndarray]):
    """ 获取现金投资和通胀率相关参数，生成投资和通胀率数组

    Parameters
    ----------
    config: dict
        配置参数字典
    op_schedule: pd.Index
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

    invest_cash_plan = parse_backtest_cash_plan(config)
    # 生成包含现金投资和现金通胀率数组的DataFrame
    cash_plan_df = pd.DataFrame(
            {'investment': np.zeros_like(op_schedule, dtype=float),
             'inflation_rate': np.ones_like(op_schedule, dtype=float)},
            index=op_schedule,
    )
    investment_positions = np.searchsorted(op_schedule.values, invest_cash_plan.plan.index, side='left')
    for pos, amount in zip(investment_positions, invest_cash_plan.amounts):
        if pos < len(cash_plan_df):
            cash_plan_df.iat[pos, 0] += amount  # 累加投资金额

    inflation_rate = invest_cash_plan.ir
    day_diffs = (cash_plan_df.index - cash_plan_df.index[0]).days
    cash_plan_df['inflation_rate'] += inflation_rate * day_diffs / 365  # 年化通胀率转换为日化通胀率
    cash_investment_array = cash_plan_df['investment'].to_numpy()
    cash_inflation_array = cash_plan_df['inflation_rate'].to_numpy()

    day_changes = np.diff(day_diffs.values, prepend=-1)
    day_changes[day_changes.nonzero()] = 1  # 将非零差值设为1，表示天数变化

    return cash_investment_array, cash_inflation_array, day_changes


def parse_signal_parsing_params(config) -> dict:
    """解析信号处理相关的配置参数:

    pt_buy_threshold: float,
        PT信号处理参数：买入信号触发阈值
    pt_sell_threshold: float,
        PT信号处理参数：卖出信号触发阈值
    long_pos_limit: float, > 0
        多头持仓比例上限
    short_pos_limit: float, < 0
        空头持仓比例上限
    allow_sell_short: bool,
        是否允许卖空操作

    Parameters
    ----------
    config: dict
        配置参数字典

    Returns
    -------
    signal_parsing_params: dict
        信号处理相关的参数字典
    """
    signal_parsing_params = {
        'pt_buy_threshold': config['PT_buy_threshold'],
        'pt_sell_threshold': config['PT_sell_threshold'],
        'long_pos_limit': config['long_position_limit'],
        'short_pos_limit': config['short_position_limit'],
        'allow_sell_short': config['allow_sell_short'],
    }
    # raise if parameters are out of range or with wrong types
    if not (isinstance(signal_parsing_params['pt_buy_threshold'], (float, int)) and
            0 <= signal_parsing_params['pt_buy_threshold'] < 1):
        raise ValueError('pt_buy_threshold should be a float number between 0 and 1')
    if not (isinstance(signal_parsing_params['pt_sell_threshold'], (float, int)) and
            0 <= signal_parsing_params['pt_sell_threshold'] < 1):
        raise ValueError('pt_sell_threshold should be a float number between 0 and 1')
    if not (isinstance(signal_parsing_params['long_pos_limit'], (float, int)) and
            signal_parsing_params['long_pos_limit'] > 0):
        raise ValueError('long_pos_limit should be a positive float number')
    if not (isinstance(signal_parsing_params['short_pos_limit'], (float, int)) and
            signal_parsing_params['short_pos_limit'] < 0):
        raise ValueError('short_pos_limit should be a negative float number')
    if not isinstance(signal_parsing_params['allow_sell_short'], bool):
        raise ValueError('allow_sell_short should be a boolean value')

    return signal_parsing_params


def parse_trading_moq_params(config) -> dict:
    """解析交易最小单位相关的配置参数:

    moq_buy: float,
        交易最小买入单位
    moq_sell: float,
        交易最小卖出单位

    Parameters
    ----------
    config: dict
        配置参数字典

    Returns
    -------
    trading_moq_params: dict
        交易最小单位相关的参数字典
    """
    trading_moq_params = {
        'moq_buy': config['trade_batch_size'],
        'moq_sell': config['sell_batch_size'],
    }
    # raise if parameters are out of range or with wrong types
    if not (isinstance(trading_moq_params['moq_buy'], (float, int)) and trading_moq_params['moq_buy'] >= 0):
        raise ValueError('moq_buy should be a positive float number')
    if not (isinstance(trading_moq_params['moq_sell'], (float, int)) and trading_moq_params['moq_sell'] >= 0):
        raise ValueError('moq_sell should be a positive float number')

    return trading_moq_params


def parse_trading_delivery_params(config) -> dict:
    """解析交易交割相关的配置参数:

    cash_delivery_period: int,
        现金交割周期（交易日）
    stock_delivery_period: int,
        股票交割周期（交易日）

    Parameters
    ----------
    config: dict
        配置参数字典

    Returns
    -------
    trading_delivery_params: dict
        交易交割相关的参数字典
    """
    trading_delivery_params = {
        'cash_delivery_period': config['cash_delivery_period'],
        'stock_delivery_period': config['stock_delivery_period'],
    }
    # raise if parameters are out of range or with wrong types
    if not (isinstance(trading_delivery_params['cash_delivery_period'], int) and
            trading_delivery_params['cash_delivery_period'] >= 0):
        raise ValueError('cash_delivery_period should be a non-negative integer')
    if not (isinstance(trading_delivery_params['stock_delivery_period'], int) and
            trading_delivery_params['stock_delivery_period'] >= 0):
        raise ValueError('stock_delivery_period should be a non-negative integer')

    return trading_delivery_params
