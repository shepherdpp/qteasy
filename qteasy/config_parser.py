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


def parse_optimization_start_end_dates(config) -> tuple[str, str, str, str]:
    """ Parse optimization and validation start and end date from config settings."""

    opt_start = config.get('opti_start')
    opt_end = config.get('opti_end')
    val_start = config.get('test_start')
    val_end = config.get('test_end')

    if opt_end is None:
        opt_end = regulate_date_format(pd.Timestamp.today() - pd.DateOffset(months=6), force_format='date')
    else:
        opt_end = regulate_date_format(opt_end, force_format='date')

    if opt_start is None:  # start is end - 1 year
        opt_start = regulate_date_format(pd.Timestamp(opt_end) - pd.DateOffset(years=1), force_format='date')
    else:
        opt_start = regulate_date_format(opt_start, force_format='date')

    if val_end is None:
        val_end = regulate_date_format(pd.Timestamp.today(), force_format='date')
    else:
        val_end = regulate_date_format(val_end, force_format='date')

    if val_start is None:  # start is end - 6 months
        val_start = regulate_date_format(pd.Timestamp(val_end) - pd.DateOffset(months=6), force_format='date')
    else:
        val_start = regulate_date_format(val_start, force_format='date')

    if pd.to_datetime(opt_start) >= pd.to_datetime(opt_end):
        raise ValueError(f'opt_start {opt_start} should be earlier than opt_end {opt_end}')
    if pd.to_datetime(val_start) >= pd.to_datetime(val_end):
        raise ValueError(f'val_start {val_start} should be earlier than val_end {val_end}')

    return opt_start, opt_end, val_start, val_end


def parse_optimization_cash_plan(config: Union[dict, ConfigDict]) -> tuple[CashPlan, CashPlan]:
    """Parse optimization and validation cash plans from config settings."""
    opt_start, opt_end, val_start, val_end = parse_optimization_start_end_dates(config=config)

    # optimization cash plan
    if config['opti_cash_dates'] is None:
        opt_cash_plan = CashPlan(opt_start,
                                 config['opti_cash_amounts'][0],
                                 config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['opti_cash_dates'])
        opt_cash_plan = CashPlan(dates=cash_dates,
                                 amounts=config['opti_cash_amounts'],
                                 interest_rate=config['riskfree_ir'])
        opt_first_cash_date = regulate_date_format(opt_cash_plan.first_day)
        if pd.to_datetime(opt_start) != pd.to_datetime(opt_first_cash_date):
            err = RuntimeError(f'first cash investment date {opt_first_cash_date} must be equal to '
                               f'opt_start date {opt_start} in optimization mode! \n'
                               f'Make adjustment in following config settings:\n'
                               f'- config["opt_start"] current setting: ({config["opti_start"]})\n'
                               f'- config["opt_cash_dates"] current setting: ({config["opti_cash_dates"]})\n')
            raise err

    # validation cash plan
    if config['test_cash_dates'] is None:
        val_cash_plan = CashPlan(val_start,
                                 config['test_cash_amounts'][0],
                                 config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['test_cash_dates'])
        val_cash_plan = CashPlan(dates=cash_dates,
                                 amounts=config['test_cash_amounts'],
                                 interest_rate=config['riskfree_ir'])
        val_first_cash_date = regulate_date_format(val_cash_plan.first_day)
        if pd.to_datetime(val_start) != pd.to_datetime(val_first_cash_date):
            err = RuntimeError(f'first cash investment date {val_first_cash_date} must be equal to '
                               f'test_start date {val_start} in validation mode! \n'
                               f'Make adjustment in following config settings:\n'
                               f'- config["test_start"] current setting: ({config["test_start"]})\n'
                               f'- config["val_cash_dates"] current setting: ({config["test_cash_dates"]})\n')
            raise err

    return opt_cash_plan, val_cash_plan


def parse_backtest_start_end_dates(config) -> tuple[str, str]:
    """Parse backtest investment start and end date from config settings."""

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
        return CashPlan(
                invest_start,
                config['invest_cash_amounts'][0],
                config['riskfree_ir'],
        )
    else:
        cash_dates = str_to_list(config['invest_cash_dates'])
        invest_cash_plan = CashPlan(
                dates=cash_dates,
                amounts=config['invest_cash_amounts'],
                interest_rate=config['riskfree_ir'],
        )
        first_invest_date = regulate_date_format(invest_cash_plan.first_day)
        if pd.to_datetime(first_invest_date) != pd.to_datetime(invest_start):
            err = RuntimeError(f'ConfigError, first cash investment date {first_invest_date} must be equal to '
                               f'backtest_start date {invest_start} in backtest mode! \n'
                               f'Make adjustment in following config settings:\n'
                               f'- config["invest_start"] current setting: ({config["invest_start"]})\n'
                               f'- config["invest_cash_dates"] current setting: ({config["invest_cash_dates"]})\n')
            raise err

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
        'buy_rate':  config['cost_rate_buy'],
        'sell_rate': config['cost_rate_sell'],
        'buy_min':   config['cost_min_buy'],
        'sell_min':  config['cost_min_sell'],
        'slippage':  config['cost_slippage'],
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


def parse_cash_invest_and_delivery_arrays(config: dict,
                                          op_schedule: pd.Index) -> (tuple[np.ndarray, np.ndarray, np.ndarray]):
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
            {'investment':     np.zeros_like(op_schedule, dtype=float),
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
    cash_inflation_array = cash_inflation_array / np.roll(cash_inflation_array, 1)
    cash_inflation_array[0] = 1.0  # 第一天的通胀率设为1.0

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
        'pt_buy_threshold':  config['PT_buy_threshold'],
        'pt_sell_threshold': config['PT_sell_threshold'],
        'long_pos_limit':    config['long_position_limit'],
        'short_pos_limit':   config['short_position_limit'],
        'allow_sell_short':  config['allow_sell_short'],
    }
    # raise if parameters are out of range or with wrong types
    if not (isinstance(signal_parsing_params['pt_buy_threshold'], (float, int)) and
            0 <= signal_parsing_params['pt_buy_threshold'] < 1):
        raise ValueError('PT_buy_threshold should be a float number between 0 and 1')
    if not (isinstance(signal_parsing_params['pt_sell_threshold'], (float, int)) and
            0 <= signal_parsing_params['pt_sell_threshold'] < 1):
        raise ValueError('PT_sell_threshold should be a float number between 0 and 1')
    if not (isinstance(signal_parsing_params['long_pos_limit'], (float, int)) and
            signal_parsing_params['long_pos_limit'] > 0):
        raise ValueError('long_position_limit should be a positive float number')
    if not (isinstance(signal_parsing_params['short_pos_limit'], (float, int)) and
            signal_parsing_params['short_pos_limit'] < 0):
        raise ValueError('short_position_limit should be a negative float number')
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
        'moq_buy':  config['trade_batch_size'],
        'moq_sell': config['sell_batch_size'],
    }
    # raise if parameters are out of range or with wrong types
    if not (isinstance(trading_moq_params['moq_buy'], (float, int)) and trading_moq_params['moq_buy'] >= 0):
        raise ValueError('moq_buy should be a positive float number or zero')
    if not (isinstance(trading_moq_params['moq_sell'], (float, int)) and trading_moq_params['moq_sell'] >= 0):
        raise ValueError('moq_sell should be a positive float number or zero')

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
        'cash_delivery_period':  config['cash_delivery_period'],
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


def parse_market_trade_time_params(config) -> dict:
    """解析市场交易时间相关的配置参数:

    market_open_time_am/pm: str,
        市场开盘时间
    market_close_time_am/pm: str,
        市场收盘时间

    Parameters
    ----------
    config: dict
        配置参数字典

    Returns
    -------
    market_trade_time_params: dict
        市场交易时间相关的参数字典
    """
    market_trade_time_params = {
        'market_open_time_am':  config['market_open_time_am'],
        'market_close_time_am': config['market_close_time_am'],
        'market_open_time_pm':  config['market_open_time_pm'],
        'market_close_time_pm': config['market_close_time_pm'],
    }
    # raise if parameters are out of range or with wrong types
    if not isinstance(market_trade_time_params['market_open_time_am'], str):
        raise ValueError('market_open_time should be a string in format "HH:MM:SS"')
    if not isinstance(market_trade_time_params['market_close_time_am'], str):
        raise ValueError('market_close_time should be a string in format "HH:MM:SS"')
    # raise if parameters are out of range or with wrong types
    if not isinstance(market_trade_time_params['market_open_time_pm'], str):
        raise ValueError('market_open_time should be a string in format "HH:MM:SS"')
    if not isinstance(market_trade_time_params['market_close_time_pm'], str):
        raise ValueError('market_close_time should be a string in format "HH:MM:SS"')

    # raise if parameters can not be properly converted to time
    try:
        pd.to_datetime(market_trade_time_params['market_open_time_am'], format='%H:%M:%S').time()
        pd.to_datetime(market_trade_time_params['market_close_time_am'], format='%H:%M:%S').time()
        pd.to_datetime(market_trade_time_params['market_open_time_pm'], format='%H:%M:%S').time()
        pd.to_datetime(market_trade_time_params['market_close_time_pm'], format='%H:%M:%S').time()
    except Exception as e:
        raise ValueError('market trade time parameters should be strings in format "HH:MM:SS"') from e

    return market_trade_time_params
