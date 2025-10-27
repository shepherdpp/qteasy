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

from qteasy import QT_DATA_SOURCE
from qteasy.configure import ConfigDict
from qteasy.utilfuncs import next_market_trade_day, regulate_date_format, str_to_list
from qteasy.finance import CashPlan
from qteasy.history import get_history_data_packages, get_history_panel


def parse_backtest_cash_plan(config: Union[dict, ConfigDict]) -> CashPlan:
    """Parse investment cash plan from config settings."""
    # 投资回测区间的开始日期根据invest_start和invest_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['invest_cash_dates'] is None:
        invest_start = next_market_trade_day(config['invest_start']).strftime('%Y%m%d')
        return CashPlan(invest_start,
                                    config['invest_cash_amounts'][0],
                                    config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['invest_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        invest_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                    amounts=config['invest_cash_amounts'],
                                    interest_rate=config['riskfree_ir'])

        return invest_cash_plan


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


def parse_backtest_data_package(config, dtypes) -> dict:
    """获取回测所需的数据包，数据类型由dtypes参数给出"""

    invest_start, invest_end = parse_backtest_start_end_dates(config=config)
    data_source = config.get('data_source', QT_DATA_SOURCE)
    # get data_package with another function in history module
    data_package = get_history_data_packages(
            data_types=dtypes,
            shares=config['asset_pool'],
            start=regulate_date_format(pd.to_datetime(invest_start) - pd.Timedelta(60, 'D')),
            end=invest_end,
            data_source=data_source,
    )

    return data_package


def parse_trade_cost_params(config) -> dict:
    """解析交易成本相关的配置参数:
        buy_fix: float, 交易成本：固定买入费用
        sell_fix: float, 交易成本：固定卖出费用
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
        'buy_rate': config.get('cost_rate_buy', 0.0),
        'sell_rate': config.get('cost_rate_sell', 0.0),
        'buy_min': config.get('cost_min_buy', 0.0),
        'sell_min': config.get('cost_min_sell', 0.0),
        'slipage': config.get('cost_slipage', 0.0),
    }
    return cost_params


def parse_cash_investment_and_inflation_arrays(config: dict, op_schedule: pd.Index) -> tuple[np.ndarray, np.ndarray]:
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
    """

    import pdb; pdb.set_trace()
    invest_cash_plan: CashPlan = parse_backtest_cash_plan(config)
    # 生成包含现金投资和现金通胀率数组的DataFrame
    cash_plan_df = pd.DataFrame(
            {'investment': np.zeros(len(op_schedule)),
             'inflation_rate': np.ones(len(op_schedule))},
            index=op_schedule,
    )
    investment_positions = np.searchsorted(op_schedule.values, invest_cash_plan.dates, side='left')
    for pos, amount in zip(investment_positions, invest_cash_plan.amounts):
        if pos < len(cash_plan_df):
            cash_plan_df.iat[pos, 0] += amount  # 累加投资金额

    inflation_rate = invest_cash_plan.ir
    op_schedule_dates = op_schedule.date()

    cash_investment_array = cash_plan_df['investment'].to_numpy()



def parse_delivery_day_indicators(config) -> np.ndarray:
    """解析交割日相关的配置参数

    Returns
    -------
    delivery_day_indicators: np.ndarray
        交割日相关的指标字典
    """
    raise NotImplementedError


def parse_cost_params(config) -> np.ndarray:
    """解析交易成本相关的配置参数

    Returns
    -------
    cost_params: np.ndarray
        交易成本相关的参数
    """
    raise NotImplementedError


def parse_signal_parsing_params(config) -> dict:
    """解析信号处理相关的配置参数

    Returns
    -------
    signal_parsing_params: dict
        信号处理相关的参数字典
    """
    raise NotImplementedError


def parse_trading_moq_params(config) -> dict:
    """解析交易最小单位相关的配置参数

    Returns
    -------
    trading_moq_params: dict
        交易最小单位相关的参数字典
    """
    raise NotImplementedError


def parse_trading_delivery_params(config) -> dict:
    """解析交易交割相关的配置参数

    Returns
    -------
    trading_delivery_params: dict
        交易交割相关的参数字典
    """
    raise NotImplementedError
