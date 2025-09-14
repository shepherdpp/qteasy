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

import re
import pandas as pd
from warnings import warn

from typing import List, Dict, Any, Union

from qteasy.configure import ConfigDict
from qteasy.utilfuncs import next_market_trade_day, regulate_date_format, str_to_list
from qteasy.finance import CashPlan


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
        invest_start = regulate_date_format(invest_cash_plan.first_day)

        if pd.to_datetime(invest_start) != pd.to_datetime(config['invest_start']):
            msg = (f'first cash investment on {invest_start} differ from invest_start {config["invest_start"]},'
                   f' first cash date will be used!')
            raise RuntimeError(msg)

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

