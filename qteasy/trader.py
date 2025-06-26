# coding=utf-8
# ======================================
# File:     trader.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-08
# Desc:
#   class Trader for trader to
# schedule trading tasks according to trade
# calendars and strategy rules, generate
# trading orders and submit to class Broker
# ======================================

import logging
import os
import sys
import time

import numpy as np
import pandas as pd

from queue import Queue
from rich.text import Text

from .__init__ import __version__ as qteasy_version
from .configure import ConfigDict, QT_CONFIG
from .database import DataSource
from .datatypes import get_tables_by_dtypes
from .qt_operator import Operator
from .broker import Broker
from .data_channels import fetch_real_time_klines
from .core import (
    check_and_prepare_live_trade_data,
    get_history_data,
    refill_data_source,
)

from .trade_recording import (
    get_account,
    get_account_position_availabilities,
    get_account_position_details,
    get_account_cash_availabilities,
    query_trade_orders,
    record_trade_order,
    get_or_create_position,
    new_account,
    update_position,
)

from .trading_util import (
    cancel_order,
    create_daily_task_schedule,
    get_position_by_id,
    get_last_trade_result_summary,
    get_symbol_names,
    process_account_delivery,
    parse_trade_signal,
    process_trade_result,
    submit_order,
    deliver_trade_result,
    calculate_cost_change,
    break_point_file_path_name,
    sys_log_file_path_name,
    trade_log_file_path_name,
)

from .utilfuncs import (
    TIME_FREQ_LEVELS,
    adjust_string_length,
    parse_freq_string,
    str_to_list,
    get_current_timezone_datetime,
)


UNIT_TO_TABLE = {
    'h':     'stock_hourly',
    '30min': 'stock_30min',
    '15min': 'stock_15min',
    '5min':  'stock_5min',
    '1min':  'stock_1min',
    'min':   'stock_1min',
}


class Trader(object):
    """ Trader是交易系统的核心，它负责调度交易任务，根据交易日历和策略规则生成交易订单并提交给Broker

    Trader的核心包括：
        一个task_daily_scheduler，它每天生成一个task列表和计划时间，在计划时间将任务加入task队列，任何需要
            执行的任务都需要被添加到队列中才会执行，执行完成后从队列中删除。
            Trader的main loop定期检查task_queue中的任务，如果有任务到达，就执行任务，否则等待下一个任务到达。
            如果在交易日中，Trader会定时将task_daily_agenda中的任务添加到task_queue中。
            如果不是交易日，Trader会打印当前状态，并等待下一个交易日。
        一个task_runner, 启动一个新的线程，运行指定的任务，等待任务返回结果

    Attributes:
    -----------
    account_id: int
        账户ID
    broker: Broker
        交易所对象，接受交易订单并返回交易结果
    task_queue: list of tuples
        任务队列，每个任务是一个tuple，包含任务的执行时间和任务的名称
    task_daily_schedule: list of tuples
        每天的任务日程，每个任务是一个tuple，包含任务的执行时间和任务的名称
    operator: Operator
        交易员对象，包含所有的交易策略，管理交易策略，控制策略的运行方式和合并方式
    config: dict
        交易系统的配置信息
    is_market_open: bool
        交易所是否开市
    is_trade_day: bool
        当前日期是否是交易日
    status: str
        交易系统的状态，包括'running', 'sleeping', 'paused', 'stopped'

    Methods
    -------
    run() -> None
        交易系统的main loop
    add_task(task) -> None
        添加任务到任务队列
    run_task(task) -> None
        执行任务
    """

    trade_log_file_headers = [
        'datetime',  # 0, 交易或变动发生时间
        'reason',  # 1, 交易或变动的原因: order / delivery / manual
        'order_id',  # 2, 如果是订单交易导致变动，记录订单ID
        'position_id',  # 3, 交易或变动发生的持仓ID
        'symbol',  # 4, 股票代码
        'name',  # 5, 股票名称
        'position_type',  # 6, 交易或变动发生的持仓类型，long / short
        'direction',  # 7, 交易方向，buy / sell
        'trade_qty',  # 8, 交易数量
        'price',  # 9, 成交价格
        'trade_cost',  # 10, 交易费用
        'qty_change',  # 11, 持仓变动数量
        'qty',  # 12, 变动后的持仓数量
        'available_qty_change',  # 13, 可用持仓变动数量
        'available_qty',  # 14, 变动后的可用持仓数量
        'cost_change',  # 15, 持仓成本变动
        'holding_cost',  # 16, 变动后的持仓成本
        'cash_change',  # 17, 现金变动
        'cash',  # 18, 变动后的现金
        'available_cash_change',  # 19, 可用现金变动
        'available_cash',  # 20, 变动后的可用现金
    ]

    def __init__(self, account_id, operator, broker, config, datasource, debug=False):
        """ 初始化Trader

        Parameters
        ----------
        account_id: int
            账户ID
        operator: Operator
            交易员对象，包含所有的交易策略，管理交易策略，控制策略的运行方式和合并方式
        broker: Broker
            交易所对象，接受交易订单并返回交易结果
        config: dict
            交易系统的配置信息
        datasource: DataSource
            数据源对象，从数据源获取数据
        debug: bool, default False
            是否打印debug信息
        """
        err = None
        if not isinstance(account_id, int):
            err = TypeError(f'account_id must be int, got {type(account_id)} instead')
        if not isinstance(operator, Operator):
            err = TypeError(f'operator must be Operator, got {type(operator)} instead')
        if not isinstance(broker, Broker):
            err = TypeError(f'broker must be Broker, got {type(broker)} instead')
        if not isinstance(config, dict):
            err = TypeError(f'config must be dict, got {type(config)} instead')
        if not isinstance(datasource, DataSource):
            err = TypeError(f'datasource must be DataSource, got {type(datasource)} instead')

        if err:
            raise err

        self.account_id = account_id
        self._broker = broker
        self._operator = operator
        self._config = ConfigDict()
        self._config.update(QT_CONFIG.copy())
        self._config.update(config)
        self._datasource = datasource
        asset_pool = self._config['asset_pool']
        asset_type = self._config['asset_type']
        if isinstance(asset_pool, str):
            asset_pool = str_to_list(asset_pool)
        self._asset_pool = asset_pool
        self._asset_type = asset_type

        self.task_queue = Queue()
        self.message_queue = Queue()

        self.task_daily_schedule = []
        self.time_zone = config['time_zone']
        self.init_datetime = self.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")

        self.next_task = ''
        self.count_down_to_next_task = 0

        self.is_trade_day = False
        self.is_market_open = False
        self._status = 'stopped'
        self._prev_status = None

        self.live_price_channel = self._config['live_price_acquire_channel']
        self.live_price_freq = self._config['live_price_acquire_freq']
        self.live_price = None  # 用于存储本交易日最新的实时价格，用于跟踪最新价格、计算市值盈亏等
        self.watched_price_refresh_interval = self._config['live_price_acquire_freq']
        self.watched_prices = None  # 用于存储被监视的股票的最新价格，用于监视价格变动
        benchmark_list = self._config['benchmark_asset']
        if isinstance(benchmark_list, str):
            benchmark_list = str_to_list(benchmark_list)
        self.watch_list = benchmark_list + self._asset_pool

        self.live_sys_logger = None

        self.account = get_account(self.account_id, data_source=self._datasource)

        self.debug = debug

    # ================== properties ==================
    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value) -> None:
        if value not in ['running', 'sleeping', 'paused', 'stopped']:
            err = ValueError(f'invalid status: {value}')
            raise err
        self._prev_status = self._status
        self._status = value

    @property
    def prev_status(self) -> str:
        return self._prev_status

    @property
    def operator(self) -> Operator:
        return self._operator

    @property
    def broker(self) -> Broker:
        return self._broker

    @property
    def asset_pool(self) -> list:
        """ 账户的资产池，一个list，包含所有允许投资的股票代码 """
        return self._asset_pool

    @property
    def asset_type(self) -> str:
        """ 账户的资产类型，一个str，包含所有允许投资的资产类型 """
        return self._asset_type

    @property
    def account_cash(self) -> tuple:
        """ 账户的现金, 包括持有现金和可用现金和总投资金额

        Returns
        -------
        cash_availabilities: tuple
            (cash_amount: float, 账户的可用资金
             available_cash: float, 账户的资金总额
             total_invest: float, 账户的总投资额
            )
        """
        return get_account_cash_availabilities(self.account_id, data_source=self._datasource)

    @property
    def account_positions(self) -> pd.DataFrame:
        """ 账户的持仓，一个tuple,包含两个ndarray，包括每种股票的持有数量和可用数量

        Returns
        -------
        positions: DataFrame, columns=['symbol', 'qty', 'available_qty'， 'cost']
            account持仓的symbol，qty, available_qty和cost, symbol与shares的顺序一致
        """
        shares = self.asset_pool

        positions = get_account_position_details(
                self.account_id,
                shares=shares,
                data_source=self._datasource
        )
        # 获取每个symbol的names
        positions = positions.T
        symbol_names = get_symbol_names(datasource=self._datasource, symbols=positions.index.tolist())
        positions['name'] = [adjust_string_length(name, 8, hans_aware=True, padding='left') for name in symbol_names]
        return positions

    @property
    def non_zero_positions(self) -> pd.DataFrame:
        """ 账户当前的持仓，一个tuple，当前持有非零的股票仓位symbol，持有数量和可用数量 """
        positions = self.account_positions
        return positions.loc[positions['qty'] != 0]

    @property
    def account_position_info(self) -> pd.DataFrame:
        """ 账户当前的持仓，一个DataFrame，当前持有的股票仓位symbol，名称，持有数量、可用数量，以及当前价格、成本和市值

        Returns
        -------
        positions: DataFrame, columns=['symbol', 'name', 'qty', 'available_qty', 'cost',
                                       'current_price', 'market_value', 'profit', 'profit_ratio']
            账户当前的持仓，一个DataFrame
        """
        positions = self.account_positions

        # 获取每个symbol的最新价格，在交易日从self.live_price中获取，非交易日从datasource中获取，或者使用全nan填充，
        if self.live_price is None:
            today = self.get_current_tz_datetime()
            start_date = (today - pd.Timedelta(days=7)).strftime('%Y%m%d')
            end_date = today.strftime('%Y%m%d')
            try:
                current_prices = get_history_data(
                        shares=positions.index.tolist(),
                        htypes='close',
                        asset_type='E',
                        freq=self.operator.op_data_freq,
                        start=start_date,
                        end=end_date,
                )['close'].iloc[-1]
            except Exception as e:
                self.send_message(f'Error in getting current prices: {e}', debug=True)
                current_prices = pd.Series(index=positions.index, data=np.nan)
        else:
            current_prices = self.live_price['close'].reindex(index=positions.index).astype('float')

        positions['name'] = positions['name'].fillna('')
        positions['current_price'] = current_prices
        positions['total_cost'] = positions['qty'] * positions['cost']
        positions['market_value'] = positions['qty'] * positions['current_price']
        positions['profit'] = positions['market_value'] - positions['total_cost']
        positions['profit_ratio'] = positions['profit'] / positions['total_cost']
        return positions.loc[positions['qty'] != 0]

    @property
    def datasource(self) -> DataSource:
        return self._datasource

    @property
    def config(self) -> dict:
        return self._config

    @property
    def trade_log_file_is_valid(self) -> bool:
        """ 返回交易记录文件是否存在

        同时检查交易记录文件格式是否正确，header内容是否与self.trade_log_file_header一致
        """

        log_file_path_name = trade_log_file_path_name(self.account_id, self.datasource)

        try:
            import csv
            with open(log_file_path_name, 'r') as f:
                # 读取文件第一行，确认与self.trade_log_file_header完全相同
                reader = csv.reader(f)
                read_header = next(reader)
                if read_header == self.trade_log_file_headers:
                    return True

                # 如果文件header不匹配，认为文件不存在
                return False

        except FileNotFoundError:
            return False

    @property
    def sys_log_file_exists(self) -> bool:
        """ 返回系统记录文件是否存在 """
        return os.path.exists(sys_log_file_path_name(self.account_id, self.datasource))

    @property
    def break_point_file_exists(self) -> bool:
        """ 返回交易设置文件是否存在 """
        return os.path.exists(break_point_file_path_name(self.account_id, self.datasource))

    # ================== methods ==================
    def get_current_tz_datetime(self) -> pd.Timestamp:
        """ 根据当前时区获取当前时间，如果指定时区等于当前时区，将当前时区设置为local，返回当前时间"""

        tz_time = get_current_timezone_datetime(self.time_zone)
        # if tz_time is very close to local time, then set time_zone to local and return local time
        if abs(tz_time - pd.to_datetime('today')) < pd.Timedelta(seconds=1):
            self.time_zone = 'local'
        # else return tz_time
        return tz_time

    def get_config(self, key=None) -> dict:
        """ 返回交易系统的配置信息 如果给出了key，返回一个仅包含key:value的dict，否则返回完整的config字典"""
        if key is not None:
            return {key: self._config.get(key)}
        else:
            return self._config

    def update_config(self, key=None, value=None) -> dict:
        """ 更新交易系统的配置信息 """
        if key not in self._config:
            return None
        from qteasy._arg_validators import _update_config_kwargs
        new_kwarg = {key: value}
        _update_config_kwargs(self._config, new_kwarg, raise_if_key_not_existed=True)
        return self._config[key]

    def get_schedule_string(self, rich_form=True) -> str:
        """ 返回当前的任务日程，以DataFrame.to_string()的形式返回

        Parameters
        ----------
        rich_form: bool, default True
            是否返回适合rich.print打印的字符串

        Returns
        -------
        schedule_string: str
            任务日程字符串
        """
        schedule = pd.DataFrame(
                self.task_daily_schedule,
                columns=['datetime', 'task', 'parameters'],
        )
        schedule.set_index(keys='datetime', inplace=True)

        if schedule.empty:
            return 'No tasks scheduled for today'

        schedule_string = schedule.to_string()
        if rich_form:
            schedule_string = schedule_string.replace('[', '<')
            schedule_string = schedule_string.replace(']', '>')

        return schedule_string

    def register_broker(self, debug=False, **kwargs) -> None:
        """ 注册broker，以便实现登录等处理
        """
        self.broker.register(debug=debug, **kwargs)

    def run(self) -> None:
        """ 交易系统的main loop：

        1，检查task_queue中是否有任务，如果有任务，则提取任务，根据当前status确定是否执行任务，如果可以执行，则执行任务，否则忽略任务
        2，如果当前是交易日，检查当前时间是否在task_daily_agenda中，如果在，则将任务添加到task_queue中
        3，如果当前是交易日，检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
        """

        self.run_task('start')

        market_open_day_loop_interval = 0.05
        market_close_day_loop_interval = 1
        current_date_time = self.get_current_tz_datetime()  # 产生当地时间
        current_date = current_date_time.date()

        # 在try-block中开始主循环，以抓取KeyboardInterrupt
        # TODO: 这里似乎应该重新思考trader和UI的关系，将trader和UI彻底分开：
        #  1，抓取 KeyboardInterrupt 似乎应该是UI的任务，trader应该专注于交易任务
        #  2，trader应该专注于交易任务，UI应该专注于交互任务，两者应该分开
        try:
            while self.status != 'stopped':
                pre_date = current_date
                sleep_interval = market_close_day_loop_interval if not \
                    self.is_trade_day else \
                    market_open_day_loop_interval
                # 检查任务队列，如果有任务，执行任务，否则添加任务到任务队列
                if not self.task_queue.empty():
                    # 如果任务队列不为空，执行任务
                    white_listed_tasks = self.TASK_WHITELIST[self.status]
                    task = self.task_queue.get()
                    if isinstance(task, tuple):
                        self.send_message(f'tuple task: {task} is taken from task queue, task[0]: {task[0]}'
                                          f'task[1]: {task[1]}', debug=True)
                        task_name = task[0]
                        args = task[1]
                    else:
                        task_name = task
                        args = None
                    self.send_message(f'task queue is not empty, taking next task from queue: {task_name}', debug=True)
                    if task_name not in white_listed_tasks:
                        self.send_message(f'task: {task} cannot be executed in current status: {self.status}', debug=True)
                        self.task_queue.task_done()
                        continue
                    try:
                        if args:
                            self.run_task(task_name, *args)
                        else:
                            self.run_task(task_name)
                    # error handling: (TODO: if there's connection problem, reconnect or hold the trader?)
                    except RuntimeError as e:
                        import traceback
                        self.send_message(f'Runtime Error occurred when executing task: {task_name}, error: {e}')
                        self.send_message(f'Traceback: \n{traceback.format_exc()}', debug=True)
                    except Exception as e:
                        import traceback
                        self.send_message(f'error occurred when executing task: {task_name}, error: {e}')
                        self.send_message(f'Traceback: \n{traceback.format_exc()}', debug=True)
                    self.task_queue.task_done()

                # 如果没有暂停，从任务日程中添加任务到任务队列
                current_date_time = self.get_current_tz_datetime()  # 产生本地时间
                current_time = current_date_time.time()
                current_date = current_date_time.date()
                if self.status != 'paused':
                    self._add_task_from_schedule(current_time)
                # 如果日期变化，检查是否是交易日，如果是交易日，更新日程
                # TODO: move these operations to a task "change_date"
                if current_date != pre_date:
                    self._check_trade_day()
                    self._initialize_schedule(current_time)

                # 检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
                if not self.broker.result_queue.empty():
                    result = self.broker.result_queue.get()
                    if self.broker.debug:
                        self.send_message(f'got new result from broker for order {result["order_id"]}, '
                                          f'adding process_result task to queue')
                    self.add_task('process_result', result)
                # 检查broker的message_queue中是否有消息，如果有，则处理消息，通常情况将消息添加到消息队列中
                if not self.broker.broker_messages.empty():
                    message = self.broker.broker_messages.get()
                    self.send_message(message)
                    self.broker.broker_messages.task_done()

                time.sleep(sleep_interval)
            else:
                # process trader when trader is normally stopped
                self.send_message(f'Trader is stopped.\n'
                                  f'{"=" * 20}\n')
        except KeyboardInterrupt:
            self.send_message('KeyboardInterrupt, stopping trader...')
            self.run_task('stop')
        except Exception as e:
            self.send_message(f'error occurred when running trader, error: {e}')
            import traceback
            self.send_message(f'Traceback: \n{traceback.format_exc()}', debug=True)
        return

    def info(self, verbose=False, detail=False, system=False) -> dict:
        """ 返回账户的概览信息，包括账户基本信息，持有现金和持仓信，所有信息打包成一个dict返回，供打印或者显示

        Parameters:
        -----------
        verbose: bool, default False
            是否生成详细信息(账户信息、交易状态信息等), to be deprecated, use detail instead
        detail: bool, default False
            是否生成详细信息(账户持仓、账户现金等)，如否，则只打印账户持仓等基本信息
        system: bool, default False
            是否生成系统信息，如否，则只生成账户信息

        Returns:
        --------
        info_str: dict
            账户的概览信息
        """

        detail = detail or verbose

        if verbose:
            import warnings
            warnings.warn('verbose argument is deprecated, use detail instead',
                          DeprecationWarning, stacklevel=2)

        position_info = self.account_position_info
        total_market_value = position_info['market_value'].sum()
        own_cash = self.account_cash[0]
        available_cash = self.account_cash[1]
        total_profit = position_info['profit'].sum()
        total_investment = self.account_cash[2]
        total_value = total_market_value + own_cash
        total_return_of_investment = total_value - total_investment
        total_roi_rate = total_return_of_investment / total_investment
        position_level = total_market_value / total_value
        total_profit_ratio = total_profit / total_market_value

        trader_info_dict = {}

        if system:
            # System Info
            trader_info_dict['python'] = sys.version
            trader_info_dict['qteasy'] = qteasy_version
            import tushare
            trader_info_dict['tushare'] = tushare.__version__
            try:
                from talib import __version__
            except ImportError:
                __version__ = 'not installed'

            trader_info_dict['ta-lib'] = 'not installed'
            trader_info_dict['Local DataSource'] = self.datasource
            trader_info_dict['System log file path'] = self.get_config("sys_log_file_path")["sys_log_file_path"]
            trader_info_dict['Trade log file path'] = self.get_config("trade_log_file_path")["trade_log_file_path"]

        if detail:
            # Account information
            trader_info_dict['Account ID'] = self.account_id
            trader_info_dict['User Name'] = self.account["user_name"]
            trader_info_dict['Created on'] = self.account["created_time"]
            trader_info_dict['Started on'] = self.init_datetime
            trader_info_dict['Time zone'] = self.get_config("time_zone")["time_zone"]

            # Status and Settings
            trader_info_dict['Trader Stats'] = self.status
            trader_info_dict['Broker Name'] = self.broker.broker_name
            trader_info_dict['Broker Status'] = self.broker.status
            trader_info_dict['Live price update freq'] = \
                self.get_config("live_price_acquire_freq")["live_price_acquire_freq"]
            trader_info_dict['Strategy'] = self.operator.strategies
            trader_info_dict['Strategy run frequency'] = self.operator.op_data_freq
            trader_info_dict['trade batch size'] = self.get_config("trade_batch_size")["trade_batch_size"]
            trader_info_dict['sell batch size'] = self.get_config("sell_batch_size")["sell_batch_size"]
            trader_info_dict['cash delivery period'] = self.get_config("cash_delivery_period")["cash_delivery_period"]
            trader_info_dict['stock delivery period'] = \
                self.get_config("stock_delivery_period")["stock_delivery_period"]
            trader_info_dict['buy_fix'] = float(self.get_config('cost_fixed_buy')['cost_fixed_buy'])
            trader_info_dict['sell_fix'] = float(self.get_config('cost_fixed_sell')['cost_fixed_sell'])
            trader_info_dict['buy_rate'] = float(self.get_config('cost_rate_buy')['cost_rate_buy'])
            trader_info_dict['sell_rate'] = float(self.get_config('cost_rate_sell')['cost_rate_sell'])
            trader_info_dict['buy_min'] = float(self.get_config('cost_min_buy')['cost_min_buy'])
            trader_info_dict['sell_min'] = float(self.get_config('cost_min_sell')['cost_min_sell'])
            trader_info_dict['market_open_am'] = self.get_config("market_open_time_am")["market_open_time_am"]
            trader_info_dict['market_close_pm'] = self.get_config("market_close_time_pm")["market_close_time_pm"]

        # Investment Return
        trader_info_dict['Benchmark'] = self.get_config("benchmark_asset")["benchmark_asset"]
        trader_info_dict['Total Investment'] = total_investment
        trader_info_dict['Total Value'] = total_value
        trader_info_dict['Total ROI'] = total_return_of_investment
        trader_info_dict['Total ROI Rate'] = total_roi_rate

        # Cash and Stock Info
        trader_info_dict['Cash Percent'] = own_cash / total_value
        trader_info_dict['Total Cash'] = own_cash
        trader_info_dict['Available Cash'] = available_cash

        trader_info_dict['Stock Percent'] = position_level
        trader_info_dict['Total Stock Value'] = total_market_value
        trader_info_dict['Total Stock Profit'] = total_profit
        trader_info_dict['Stock Profit Ratio'] = total_profit_ratio
        trader_info_dict['Asset Pool'] = self.asset_pool
        trader_info_dict['Asset Type'] = self.asset_type
        trader_info_dict['Asset in Pool'] = len(self.asset_pool)

        return trader_info_dict

    def trade_results(self, status='filled') -> pd.DataFrame:
        """ 返回账户的交易结果

        Parameters
        ----------
        status: str, default 'filled'
            交易结果的状态，包括'filled', 'cancelled', 'rejected', 'all'

        Returns
        -------
        trade_results: DataFrame
            交易结果
        """
        from qteasy.trade_recording import read_trade_results_by_order_id
        from qteasy.trade_recording import query_trade_orders
        trade_orders = query_trade_orders(
                self.account_id,
                status=status,
                data_source=self._datasource
        )
        order_ids = trade_orders.index.values
        return read_trade_results_by_order_id(order_id=order_ids, data_source=self._datasource)

    def send_message(self, message: (str, Text), debug=False) -> None:
        """ 发送消息到消息队列, 并根据情况对消息进行处理

        在处理消息时，执行下面：
        - 在消息前添加时间、状态等信息，并将消息记录到system log中
        - 如果debug=True，只有self.debug == True时才将消息推送到消息队列
        - 如果debug=False，总是将消息推送到消息队列

        Parameters
        ----------
        message: str, Text
            消息内容
        debug: bool, optional, default: False
            消息是否为debug类型，如果消息为debug类型，但当前不是debug模式时，消息会被阻断，不发送到消息队列
        """

        if self.live_sys_logger is None:
            self.init_system_logger()

        logger_live = self.live_sys_logger
        message_with_prefix = self.add_message_prefix(message, debug=debug)

        # 将添加消息头的消息写入log文件
        if debug:
            logger_live.debug(message_with_prefix)
        else:
            logger_live.info(message_with_prefix)

        # 如果debug 但 not self.debug，不发送消息到消息队列
        if debug and (not self.debug):
            return
        # 其他情况下，发送原始消息到消息队列
        self.message_queue.put(message)

    def add_message_prefix(self, message: str, debug=False) -> str:
        """ 在消息前添加时间、状态等信息

        Parameters
        ----------
        message: str
            消息内容
        debug: bool, optional, default: False
            是否在消息头中添加"<debug>"字样

        Returns
        -------
        message: str
            添加了时间、状态等信息的消息
        """

        time_string = self.get_current_tz_datetime().strftime("%b%d %H:%M:%S")  # 本地时间
        if self.time_zone != 'local':
            tz = f"({self.time_zone.split('/')[-1]})"
        else:
            tz = ''

        # 在message前添加时间、状态等信息
        message = f'<{time_string}{tz}>{self.status}: {message}'

        if debug:
            message = f'<DEBUG>{message}'

        return message

    def add_task(self, task, kwargs=None) -> None:
        """ 添加任务到任务队列

        Parameters
        ----------
        task: str
            任务名称
        kwargs: dict
            任务参数
        """
        if not isinstance(task, str):
            err = TypeError('task should be a str')
            raise err
        if kwargs and (not isinstance(kwargs, dict)):
            err = TypeError('kwargs should be a dict')
            raise err

        if kwargs:
            task = (task, (kwargs, ))
        self.send_message(f'adding task: {task}', debug=True)
        self._add_task_to_queue(task)

    def add_async_task(self, task, kwargs=None) -> None:
        """ 添加异步任务到任务队列，异步任务将以异步形式在主线程以外的子线程执行

        Parameters
        ----------
        task: str
            任务名称
        **kwargs: dict
            任务参数
        """
        raise NotImplementedError

    def history_orders(self, with_trade_results=True):
        """ 账户的历史订单详细信息

        Parameters
        ----------
        with_trade_results: bool, default False
            是否包含订单的成交结果

        Returns
        -------
        order_details: DataFrame:
            如果with_trade_results=False, 不包含成交结果信息：仅包含以下列
            - symbol: str, 交易标的股票代码
            - position: str, 交易标的的持仓方向，long/short
            - direction: str, 交易方向，buy/sell
            - order_type: str, 订单类型，market/limit
            - qty: int, 订单数量
            - price: float, 订单价格
            - submitted_time: datetime, 订单提交时间
            - status: str, 订单状态，filled/canceled

        order_result_details: DataFrame
            如果with_trade_results=True, 包含成交结果信息：包含以下列
            - symbol: str, 交易标的股票代码
            - position: str, 交易标的的持仓方向，long/short
            - direction: str, 交易方向，buy/sell
            - order_type: str, 订单类型，market/limit
            - qty: int, 订单申报数量
            - price: float, 订单申报价格
            - submitted_time: datetime, 订单提交时间
            - status: str, 订单状态，filled/canceled/partial-filled
            - price_filled: float, 成交价格
            - filled_qty: int, 成交数量
            - canceled_qty: int, 撤单数量
            - transaction_fee: float, 交易费用
            - execution_time: datetime, 成交时间
            - delivery_status: str, 交割状态，D/ND
        """
        from qteasy.trade_recording import query_trade_orders, get_account_positions, read_trade_results_by_order_id
        orders = query_trade_orders(self.account_id, data_source=self._datasource)
        positions = get_account_positions(self.account_id, data_source=self._datasource)
        order_details = orders.join(positions, on='pos_id', rsuffix='_p')
        order_details.drop(columns=['pos_id', 'account_id', 'qty_p', 'available_qty'], inplace=True)
        order_details = order_details.reindex(
                columns=['symbol', 'position', 'direction', 'order_type',
                         'qty', 'price',
                         'submitted_time', 'status']
        )
        if not with_trade_results:
            return order_details
        results = read_trade_results_by_order_id(orders.index.to_list(), data_source=self._datasource)
        order_result_details = order_details.join(results.set_index('order_id'), lsuffix='_quoted', rsuffix='_filled')
        order_result_details = order_result_details.reindex(
                columns=['symbol', 'position', 'direction', 'order_type',
                         'qty', 'price_quoted', 'submitted_time', 'status',
                         'price_filled', 'filled_qty', 'canceled_qty', 'transaction_fee', 'execution_time',
                         'delivery_status'],
        )
        # correct the data types of some columns
        order_result_details['submitted_time'] = pd.to_datetime(order_result_details['submitted_time'])
        order_result_details['execution_time'] = pd.to_datetime(order_result_details['execution_time'])
        return order_result_details

    def asset_pool_detail(self) -> pd.DataFrame:
        """ 返回asset_pool的详细信息，如果没有股票基本信息，则返回空DataFrame

        Returns
        -------
        asset_pool_detail: DataFrame
            asset_pool的详细信息
        """
        # get all symbols from asset pool, display their master info
        asset_pool = self.asset_pool
        stock_basic = self.datasource.read_table_data(table='stock_basic')
        if stock_basic.empty:
            # print(f'No stock basic data found in the datasource, acquire data with '
            #       f'"qt.refill_data_source(tables="stock_basic")"')
            # 打印是UI的任务，不是trader的任务
            return pd.DataFrame()
        return stock_basic.reindex(index=asset_pool)

    def manual_change_cash(self, amount) -> None:
        """ 手动修改现金，根据amount的正负号，增加或减少现金

        修改后持有现金/可用现金/总投资金额都会发生变化
        如果amount为负，且绝对值大于可用现金时，忽略该操作

        Parameters
        ----------
        amount: float
            现金

        Returns
        -------
        None
        """
        from qteasy.trade_recording import update_account_balance, get_account_cash_availabilities

        cash_amount, available_cash, total_invest = get_account_cash_availabilities(
                account_id=self.account_id,
                data_source=self.datasource
        )
        if amount < -available_cash:
            self.send_message(f'Not enough cash to decrease, available cash: {available_cash}, change amount: {amount}')
            return
        amount_change = {
            'cash_amount_change':      amount,
            'available_cash_change':   amount,
            'total_investment_change': amount,
        }
        update_account_balance(
                account_id=self.account_id,
                data_source=self.datasource,
                **amount_change
        )
        cash_amount, available_cash, total_invest = get_account_cash_availabilities(
                account_id=self.account_id,
                data_source=self.datasource
        )
        # 在trade_log中记录现金变动
        cash_change_detail = {
            'cash_change':           amount,
            'cash':                  cash_amount,
            'available_cash_change': amount,
            'available_cash':        available_cash,
        }
        self.log_manual_cash_change(cash_change_detail)

        return

    def manual_change_position(self, symbol, quantity, price, side=None) -> None:
        """ 手动修改仓位，查找指定标的和方向的仓位，增加或减少其持仓数量，同时根据新的持仓数量和价格计算新的持仓成本

        修改后持仓的数量 = 原持仓数量 + quantity
        如果找不到指定标的和方向的仓位，则创建一个新的仓位
        如果不指定方向，则查找当前持有的非零仓位，使用持有仓位的方向，如果没有持有非零仓位，则默认为'long'方向
        如果已经持有的非零仓位和指定的方向不一致，则忽略该操作，并打印提示
        如果quantity为负且绝对值大于可用数量，则忽略该操作，并打印提示

        Parameters
        ----------
        symbol: str
            交易标的代码
        quantity: float
            交易数量，正数表示买入，负数表示卖出
        price: float
            交易价格，用来计算新的持仓成本
        side: str, optional
            交易方向，'long' 表示买入，'short' 表示卖出, None表示取已有的不为0的仓位

        Returns
        -------
        None
        """

        from qteasy.trade_recording import get_or_create_position, get_position_by_id, update_position, get_position_ids
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like

        if not is_complete_cn_stock_symbol_like(symbol):
            self.send_message(f'Invalid symbol: {symbol}, please check your input.'
                              f'the symbol should include suffix like "SH"/"SZ", etc.')
            return

        position_ids = get_position_ids(
                account_id=self.account_id,
                symbol=symbol,
                data_source=self.datasource,
        )
        position_id = None
        if len(position_ids) == 0:
            # no position found, create a new one
            if side is None:
                side = 'long'
            position_id = get_or_create_position(
                    account_id=self.account_id,
                    symbol=symbol,
                    position_type=side,
                    data_source=self.datasource,
            )
            self.send_message('Position to be modified does not exist, new position is created!', debug=True)
        elif len(position_ids) == 1:
            # found one position, use it, if side is not consistent, create a new one on the other side
            position_id = position_ids[0]
            position = get_position_by_id(
                    pos_id=position_id,
                    data_source=self.datasource,
            )
            if side is None:
                side = position['position']
            if side != position['position']:
                if position['qty'] != 0:
                    self.send_message(f'Can not modify position {symbol}@ {side} while {symbol}@ {position["position"]}'
                                      f' still has {position["qty"]} shares, reduce it to 0 first!')
                    return
                else:
                    position_id = get_or_create_position(
                            account_id=self.account_id,
                            symbol=symbol,
                            position_type=side,
                            data_source=self.datasource,
                    )
        else:  # len(position_ids) > 1
            # more than one position found, find the one with none-zero side
            for pos_id in position_ids:
                position = get_position_by_id(
                        pos_id=pos_id,
                        data_source=self.datasource,
                )
                if position['qty'] != 0:
                    position_id = pos_id
                    break
            # in case both sides are zero, use the "side" one, unless "side" is "none-zero"
            if position_id is None:
                if side is None:
                    side = 'long'
                position_id = get_or_create_position(
                        account_id=self.account_id,
                        symbol=symbol,
                        position_type=side,
                        data_source=self.datasource,
                )
        position = get_position_by_id(
                pos_id=position_id,
                data_source=self.datasource,
        )
        self.send_message(f'Changing position {position_id} {position["symbol"]}/{position["position"]} '
                          f'from {position["qty"]} to {position["qty"] + quantity}', debug=True)
        # 如果减少持仓，则可用持仓数量必须足够，否则退出
        if quantity < 0 and position['available_qty'] < -quantity:
            self.send_message(f'Not enough position to decrease, '
                              f'available: {position["available_qty"]}, skipping operation')
            return

        # 计算持仓变动后的持仓成本
        cost_change, new_average_cost = calculate_cost_change(
                prev_qty=position['qty'],
                prev_unit_cost=position['cost'],
                qty_change=quantity,
                price=price,
                transaction_fee=0.0,
        )

        position_data = {
            'qty_change':           quantity,
            'available_qty_change': quantity,
            'cost':                 new_average_cost,
        }
        update_position(
                position_id=position_id,
                data_source=self.datasource,
                **position_data
        )
        position_change_detail = {
            'pos_id': position_id,
            'qty_change': quantity,
            'available_qty_change': quantity,
            'cost_change': cost_change,
        }
        # 在trade_log中记录持仓变动
        self.log_manual_qty_change(position_change_detail)

        return

    def update_watched_prices(self) -> pd.DataFrame:
        """ 根据watch list返回清单中股票的信息：代码、名称、当前价格、涨跌幅
        同时更新self.watched_prices
        """
        if self.watch_list:
            symbols = self.watch_list
            live_prices = fetch_real_time_klines(
                    channel=self.live_price_channel,
                    qt_codes=symbols,
                    freq='D',
                    verbose=True,
            )
            if not live_prices.empty:
                live_prices.close = live_prices.close.astype(float)
                live_prices['change'] = live_prices['close'] / live_prices['pre_close'] - 1
                live_prices.set_index('ts_code', inplace=True)
                # remove duplicated indices if any
                live_prices = live_prices[~live_prices.index.duplicated(keep='first')]

                self.send_message('live prices acquired to update watched prices!', debug=True)
            else:
                self.send_message('Failed to acquire live prices to update watch price string!', debug=True)

            self.watched_prices = live_prices

        return self.watched_prices

# ============= functions related to trade config and logging ====================

    def new_sys_logger(self) -> logging.Logger:
        """ 返回一个系统logger

        Returns
        -------
        logger: logging.Logger
            系统信息logger
        """

        live_handler = logging.FileHandler(
                filename=sys_log_file_path_name(self.account_id, self.datasource),
                mode='a',
                encoding='utf-8',
                delay=False,
        )
        logger_live = logging.getLogger('live')
        logger_live.addHandler(live_handler)
        logger_live.setLevel(logging.DEBUG)
        logger_live.propagate = False

        return logger_live

    def init_system_logger(self) -> None:
        """ 检查系统logger属性是否已经设置，或者log文件存在，如果没有，则初始化系统logger属性

        Returns
        -------
        None
        """
        if not self.sys_log_file_exists:
            self.live_sys_logger = None
        if self.live_sys_logger is None:
            self.live_sys_logger = self.new_sys_logger()

    def clear_sys_log(self) -> str:
        """ 清除system_log文件中的全部内容，并返回文件名

        Returns
        -------
        sys_log_file_name: str
        系统log文件名
        """
        raise NotImplementedError

    def init_trade_log_file(self) -> None:
        """ 检查交易log文件是否存在且合法，如果不存在或格式不合法，则刷新文件

        Returns
        -------
        None
        """

        if self.trade_log_file_is_valid:
            pass
        else:
            self.renew_trade_log_file()

    def renew_trade_log_file(self) -> str:
        """ 创建一个新的trade_log记录文件，写入文件header，清除文件内容

        Returns
        -------
        log_file_path_name: str
            交易记录文件的路径和文件名
        """
        import csv
        log_file_path_name = trade_log_file_path_name(self.account_id, self.datasource)

        if os.path.exists(log_file_path_name):
            os.remove(log_file_path_name)

        with open(log_file_path_name, mode='w', encoding='utf-8') as f:
            writer = csv.writer(f)
            row = self.trade_log_file_headers
            writer.writerow(row)

        return log_file_path_name

    def write_trade_log_file(self, **log_content: dict) -> None:
        """ 写入log到trade_log记录文件的最后一行

        log文件必须存在，否则会报错

        Parameters
        ----------
        log_content: dict
            log信息，包括日期、时间、log内容等

        Raises
        ------
        FileNotFoundError
            如果log文件不存在

        """
        if not self.trade_log_file_is_valid:
            raise FileNotFoundError('trade log file does not exist or is not valid')

        base_log_content = {
            k: v for k, v in
            zip(self.trade_log_file_headers,
                [None] * len(self.trade_log_file_headers))
        }
        # remove keys from log_content that are not in base_log_content
        log_content = {
            k: v for k, v in
            log_content.items() if
            k in base_log_content
        }
        # add datetime to log_content
        log_content['datetime'] = self.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")
        # update base_log_content with log_content
        base_log_content.update(log_content)

        # 调整各个数据的格式:
        for key in base_log_content:
            if key in ['qty_change', 'qty', 'available_qty_change', 'available_qty',
                       'cash_change', 'cash', 'available_cash_change', 'available_cash',
                       'cost_change', 'holding_cost', 'trade_cost', 'qty', 'trade_qty']:
                if base_log_content[key] is None:
                    continue
                base_log_content[key] = f'{base_log_content[key]:.3f}'

        import csv
        file_name = trade_log_file_path_name(self.account_id, self.datasource)
        with open(file_name, mode='a', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.trade_log_file_headers)
            # append log_content to the end of the file
            writer.writerow(base_log_content)

    def read_trade_log(self) -> pd.DataFrame:
        """ 读取trade_log记录文件的全部内容

        Returns
        -------
        trade_log: pd.DataFrame
        """
        if self.trade_log_file_is_valid:
            df = pd.read_csv(trade_log_file_path_name(self.account_id, self.datasource))
            return df
        else:
            return pd.DataFrame()

    def read_sys_log(self, row_count: int = None) -> list:
        """ 从系统log文件中读取文本信息，保存在一个列表中，如果指定row_count = N，则读取倒数N行

        Parameters
        ----------
        row_count: int, optional
        如果给出row_count，则只读取倒数row_count行文本，如果为None，读取所有文本

        Returns
        -------
        sys_logs: list of str
            逐行读取的系统log文本
        """

        log_file_path = sys_log_file_path_name(self.account_id, self.datasource)
        if not os.path.exists(log_file_path):
            return []
        with open(log_file_path, 'r') as f:
            # read last row_count lines from f
            lines = f.readlines()

            if row_count is None:
                row_count = len(lines)

            if row_count > 0:
                lines = lines[-row_count:]

        return lines

    def save_break_point(self) -> str:
        """ 保存工作断点

        Returns
        -------
        break_point_file_name: str
            断点文件路径
        """
        # TODO: 不用保存完整的config，只需要保存部分跟交易有关的信息即可
        #  在启动交易时导入的断点会覆盖start_up_settings中的参数
        break_point_data = dict()
        break_point_data['operator'] = self.operator
        break_point_data['config'] = self.config

        from .utilfuncs import write_binary_file

        break_point_file_name = break_point_file_path_name(self.account_id, self.datasource)
        try:
            break_point_file_name = write_binary_file(
                    file_path=os.path.dirname(break_point_file_name),
                    file_name=os.path.basename(break_point_file_name),
                    data=break_point_data,
            )
        except Exception as e:
            msg = f'{e}, error writing break point!'
            self.send_message(msg)

        return break_point_file_name

    def load_break_point(self) -> dict:
        """ 从断点文件中读取信息并载入相关属性

        :return:
        """
        from .utilfuncs import read_binary_file

        break_point_file_name = break_point_file_path_name(self.account_id, self.datasource)
        try:
            break_point_data = read_binary_file(
                    file_path=os.path.dirname(break_point_file_name),
                    file_name=os.path.basename(break_point_file_name),
            )
        except Exception as e:
            msg = f'{e}, break point does not exist or can not be loaded!'
            self.send_message(msg)
            return {}

        if not isinstance(break_point_data, dict):
            msg = f'Wrong data read from break point, the file might be corrupted, data will be ignored!'
            self.send_message(msg)
            return {}

        return break_point_data

    def submit_trade_order(self, symbol: str, position: str, direction: str,
                           order_type: str, qty: int, price: float) -> dict:
        """ 提交订单

        Parameters
        ----------
        symbol: str
            交易标的代码
        position: str
            交易标的的持仓方向，long/short
        direction: str
            交易方向，buy/sell
        order_type: str
            订单类型，market/limit
        qty: int
            订单数量
        price: float
            订单价格

        Returns
        -------
        trade_order: dict
            订单信息
        """
        if order_type is None:
            order_type = 'market'

        pos_id = get_or_create_position(account_id=self.account_id,
                                        symbol=symbol,
                                        position_type=position,
                                        data_source=self._datasource)

        # 生成交易订单dict
        trade_order = {
            'pos_id':         pos_id,
            'direction':      direction,
            'order_type':     order_type,  # TODO: order type is to be properly defined
            'qty':            qty,
            'price':          price,
            'submitted_time': None,
            'status':         'created',
        }

        order_id = record_trade_order(trade_order, data_source=self._datasource)
        # 提交交易订单
        if submit_order(order_id=order_id, data_source=self._datasource) is not None:
            trade_order['order_id'] = order_id

            return trade_order

        return {}

    def log_trade_result(self, full_trade_result) -> None:
        """ 根据返回的完整交易记录full_trade_result，生成交易记录
        trade_log和系统记录system_log，
        同时将交易记录记入log文件，将系统记录通过消息发送到trader

        Parameters
        ----------
        full_trade_result: dict
            一个字典，包含完整的交易结果信息，字典包含的内容与process_trade_result函数的返回值相同

        Returns
        -------
        None
        """
        # 获取交易结果和订单信息
        order_id = full_trade_result['order_id']
        pos, d, symbol = full_trade_result['position'], full_trade_result['direction'], full_trade_result['symbol']
        status = full_trade_result['order_status']

        filled_qty = full_trade_result['filled_qty']
        filled_price = full_trade_result['price']
        trade_cost = full_trade_result['transaction_fee']

        # TODO: 发现bug：
        #  如果一个订单分批完成，第一个结果应返回状态partial-filled，第二个结果返回状态filled
        #  但是在这里两个状态都会是partial-filled，需要查找原因并修改
        # send message to indicate execution of order
        self.send_message(f'<ORDER EXECUTED {order_id}>: '
                          f'{d}-{pos} of {symbol}: {status} with {filled_qty} @ {filled_price}')

        # 读取交易处理以后的账户信息和持仓信息
        pos_id = full_trade_result['pos_id']
        position = get_position_by_id(pos_id, data_source=self._datasource)
        qty, available_qty, cost = position['qty'], position['available_qty'], position['cost']
        # 读取持有现金
        account = get_account(self.account_id, data_source=self._datasource)
        cash_amount = account['cash_amount']
        available_cash = account['available_cash']
        name = get_symbol_names(datasource=self.datasource, symbols=symbol)[0]
        #
        qty_change = full_trade_result['qty_change']
        cash_amount_change = full_trade_result['cash_amount_change']
        trade_log = {
            'reason':                'order',
            'order_id':              order_id,
            'position_id':           pos_id,
            'symbol':                symbol,  # 股票代码
            'name':                  name,  # 股票名称
            'position_type':         pos,  # 'long'/'short'
            'direction':             d,  # 'buy'/'sell'
            'trade_qty':             filled_qty,  # 成交数量
            'price':                 filled_price,  # 成交价格
            'trade_cost':            trade_cost,  # 交易费用
            'qty_change':            qty_change,  #
            'qty':                   qty,
            'available_qty_change':  full_trade_result['available_qty_change'],
            'available_qty':         available_qty,
            'cost_change':           full_trade_result['cost_change'],
            'holding_cost':          cost,
            'cash_change':           cash_amount_change,
            'cash':                  cash_amount,
            'available_cash_change': full_trade_result['available_cash_change'],
            'available_cash':        available_cash,
        }
        self.write_trade_log_file(**trade_log)
        # 生成system_log 现金及持仓变动记录
        if qty_change != 0.:
            self.send_message(f'<RESULT RECORDED {order_id}>: position {symbol}({pos}) changed: '
                              f'own qyt: {qty - qty_change:.2f}->{qty:.2f}; '
                              f'available qyt: {available_qty - full_trade_result["available_qty_change"]:.2f}'
                              f'->{available_qty:.2f}; '
                              f'cost: {cost - full_trade_result["cost_change"]:.2f}->{cost:.2f}')
        if full_trade_result['cash_amount_change'] != 0:
            self.send_message(f'<RESULT LOGGED {order_id}>: account cash changed: '
                              f'cash: ¥{cash_amount - cash_amount_change:,.2f}->¥{cash_amount:,.2f}'
                              f'available: ¥{available_cash - full_trade_result["available_cash_change"]:,.2f}'
                              f'->¥{available_cash:,.2f}')

    def log_cash_delivery(self, delivery_result) -> None:
        """ 根据现金交割记录，生成详细trade_log和system_log
        并将trade_log和system_log记录到相应的文件或消息队列中

        Parameters
        ---------
        delivery_result: dict
            交割记录，一个字典，内容与deliver_trade_result函数的返回值一致
            {
                'order_id': int, 交割的订单的ID, 总是等于交易结果的order_id
                'account_id': int, 更新的账户ID，如果没有更新则为None
                'pos_id' : int, 更新的持仓ID，如果没有更新则为None
                'symbol': str, 更新的持仓代码，如果没有更新则为None
                'position': str, 更新的持仓方向，如果没有更新则为None
                'prev_qty': float, 更新前的资产可用持仓数量，如果没有更新则为None
                'updated_qty': float, 更新后的资产可用持仓数量，如果没有更新则为None
                'prev_amount': float, 更新前的账户可用现金余额，如果没有更新则为None
                'updated_amount': float, 更新后的账户可用现金余额，如果没有更新则为None
                'delivery_status': str, 更新后订单的交割状态，如果正常交割，则为'DL',否则为None
            }

        Returns
        -------
        None
        """
        if delivery_result['delivery_status'] is None:  # 如果未发生交割，则返回
            return
        order_id = delivery_result['order_id']
        if delivery_result['updated_amount'] is None:  # 如果交割结果不含现金，则返回
            return

        symbol = delivery_result['symbol']
        pos_type = delivery_result['position']
        account = get_account(account_id=self.account_id, data_source=self.datasource)
        account_name = account['user_name']
        prev_amount = delivery_result['prev_amount']
        updated_amount = delivery_result['updated_amount']
        color_tag = 'bold red' if prev_amount > updated_amount else 'bold green'
        # 生成trade_log并写入文件
        trade_log = {
            'reason':                'delivery',
            'order_id':              order_id,
            'position_id':           delivery_result['pos_id'],
            'symbol':                symbol,
            'position_type':         pos_type,
            'name':                  get_symbol_names(datasource=self.datasource, symbols=symbol)[0],
            'cash_change':           0.,
            'cash':                  account['cash_amount'],
            'available_cash_change': updated_amount - prev_amount,
            'available_cash':        updated_amount
        }
        self.write_trade_log_file(**trade_log)
        # 发送system log信息
        self.send_message(f'<RESULT DELIVERED {order_id}>: <{account_name}-{self.account_id}> available cash:'
                          f'[{color_tag}]¥{prev_amount:.3f}->¥{updated_amount:.3f}[/{color_tag}]')

    def log_qty_delivery(self, delivery_result) -> None:
        """ 根据股票持仓交割记录，生成详细的trade_log和system_log
        并将trade_log和system_log记录到相应的文件或消息队列中

        Parameters
        ---------
        delivery_result: dict
            交割记录，一个字典，内容与deliver_trade_result函数的返回值一致
            {
                'order_id': int, 交割的订单的ID, 总是等于交易结果的order_id
                'account_id': int, 更新的账户ID，如果没有更新则为None
                'pos_id' : int, 更新的持仓ID，如果没有更新则为None
                'symbol': str, 更新的持仓代码，如果没有更新则为None
                'position': str, 更新的持仓方向，如果没有更新则为None
                'prev_qty': float, 更新前的资产可用持仓数量，如果没有更新则为None
                'updated_qty': float, 更新后的资产可用持仓数量，如果没有更新则为None
                'prev_amount': float, 更新前的账户可用现金余额，如果没有更新则为None
                'updated_amount': float, 更新后的账户可用现金余额，如果没有更新则为None
                'delivery_status': str, 更新后订单的交割状态，如果正常交割，则为'DL',否则为None
            }

        Returns
        -------
        None
        """
        if delivery_result['delivery_status'] is None:  # 如果未发生交割，则返回
            return
        order_id = delivery_result['order_id']
        if delivery_result['updated_qty'] is None:  # 如果交割结果不含股票，则返回
            return

        pos = get_position_by_id(pos_id=delivery_result['pos_id'], data_source=self.datasource)
        symbol = pos['symbol']
        pos_type = pos['position']
        prev_qty = delivery_result['prev_qty']
        updated_qty = delivery_result['updated_qty']
        color_tag = 'bold red' if prev_qty > updated_qty else 'bold green'

        name = get_symbol_names(self.datasource, symbols=symbol)[0]
        # 生成trade_log并写入文件
        trade_log = {
            'reason':               'delivery',
            'order_id':             order_id,
            'position_id':          delivery_result['pos_id'],
            'symbol':               symbol,
            'position_type':        pos_type,
            'name':                 get_symbol_names(datasource=self.datasource, symbols=pos['symbol'])[0],
            'qty_change':           0.,
            'qty':                  pos['qty'],
            'available_qty_change': updated_qty - prev_qty,
            'available_qty':        updated_qty,
        }
        self.write_trade_log_file(**trade_log)
        # 发送system log信息
        self.send_message(f'<RESULT DELIVERED {order_id}>: <{name}-{symbol}@{pos_type} side> available qty:'
                          f'[{color_tag}]{prev_qty}->{updated_qty} [/{color_tag}]')

    def log_manual_cash_change(self, cash_change_detail) -> None:
        """ 当手动调整现金时，生成详细的trade_log和system_log
        并将trade_log和system_log记录到相应的文件或消息队列中

        Parameters
        ---------
        cash_change_detail: dict
            现金变动详情，包含：
            {
                'cash_change': float, 持有现金变动量
                'cash': float, 变动后持有现金总额
                'available_cash_change': float, 可用现金变动量
                'available_cash': float, 变动后可用现金总额
            }

        Returns
        -------
        None
        """
        if not isinstance(cash_change_detail, dict):
            raise TypeError(f'cash_change_detail should be a dict, got {type(cash_change_detail)} instead.')
        # 补充金额变动的额外信息
        cash_change_detail['reason'] = 'manual'
        self.write_trade_log_file(**cash_change_detail)
        # 发送消息通知现金变动并记录system log
        cash, available, investment = self.account_cash
        self.send_message(f'<MANUAL CHANGED CASH>: {cash:.2f}, '
                          f'available: {available:.2f}, '
                          f'total invest: {investment:.2f}')

    def log_manual_qty_change(self, qty_change_detail) -> None:
        """ 当手动调整持仓时，生成详细的trade_log和system_log
        并将trade_log和system_log记录到相应的文件或消息队列中

        Parameters
        ---------
        qty_change_detail: dict
            持仓变动详情，包含：
            {
                'pos_id': int, 发生变动的持仓ID
                'qty_change': float, 发生的持仓数量变动
                'available_qty_change': float, 发生的可用持仓变动量
                'cost_change': float, 发生的持仓成本变动量
            }

        Returns
        -------
        None
        """

        pos_id = qty_change_detail['pos_id']
        qty_change = qty_change_detail['qty_change']
        available_change = qty_change_detail['available_qty_change']
        cost_change = qty_change_detail['cost_change']
        # 在trade_log中记录持仓变动
        position = get_position_by_id(
                pos_id=pos_id,
                data_source=self.datasource,
        )
        symbol = position['symbol']
        qty = position['qty']
        available = position['available_qty']
        cost = position['cost']
        name = get_symbol_names(self.datasource, symbols=symbol)[0]
        log_content = {
            'reason':               'manual',
            'position_id':          pos_id,
            'symbol':               symbol,
            'position_type':        position['position'],  # 'long' or 'short'
            'name':                 name,
            'qty_change':           qty_change,
            'qty':                  qty,
            'available_qty_change': available_change,
            'available_qty':        available,
            'cost_change':          cost_change,
            'holding_cost':         cost,
        }
        self.write_trade_log_file(**log_content)
        # 发送消息通知持仓变动并记录system log
        self.send_message(f'<MANUAL CHANGED pos {symbol}/{position["position"]}>: '
                          f'qty: {qty - qty_change} -> {qty} '
                          f'available: {available - available_change} -> {available} '
                          f'cost: {cost - cost_change:.2f} -> {cost:.2f}')

    # ============ definition of tasks ================
    def _start(self) -> None:
        """ 启动交易系统 """
        self.send_message('Starting Trader...')

        # 初始化交易记录文件
        self.send_message(f'Initializing trade log file...')
        self.init_trade_log_file()
        # 初始化系统logger
        self.send_message(f'Initializing system logger...')
        self.init_system_logger()

        # 检查是否有断点，如果有，则载入断点
        self.send_message('Checking for break point...')
        break_point = self.load_break_point()

        if break_point:
            self.send_message('Break point loaded, resuming from break point...')
            operator = break_point.get('operator', None)
            if operator:
                self._operator = operator
                self.send_message('Loaded operator from break point!')

            # broker = break_point.get('broker', None)
            # if broker:
            #     self._broker = broker
            #     self.send_message('Loaded broker from break point!')

            config = break_point.get('config', None)
            if config:
                self._config.update(config)
                self.send_message('Loaded configurations from break point!')
        else:
            self.send_message('No break point found, will using default configurations...')

        # 初始化trader的状态，初始化任务计划
        self.status = 'sleeping'
        self.send_message('Checking trade day and initializing schedule...')
        self._check_trade_day()
        self._initialize_schedule()

        # 启动broker
        self.send_message(f'Trader is started, running with account_id: {self.account_id}\n'
                          f' = Started on date / time: '
                          f'{self.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")}\n'
                          f' = current day is trade day: {self.is_trade_day}\n'
                          f' = running agenda (first 5 tasks): {self.task_daily_schedule[:5]}')

    def _stop(self) -> None:
        """ 停止交易系统 """
        self.send_message('Saving Trading Data to break point...')
        break_point_file_name = self.save_break_point()
        self.send_message(f'Break point saved to {break_point_file_name}')
        self.send_message('Stopping Trader, the broker will be stopped as well...')
        self._broker.status = 'stopped'
        self.status = 'stopped'

    def _sleep(self) -> None:
        """ 休眠交易系统 """
        msg = Text('Putting Trader to sleep', style='bold red')
        self.send_message(message=msg)
        self.status = 'sleeping'
        self.broker.status = 'paused'

    def _wakeup(self) -> None:
        """ 唤醒交易系统 """
        self.status = 'running'
        self.broker.status = 'running'
        msg = Text('Trader is awake, broker is running', style='bold red')
        self.send_message(message=msg)

    def _pause(self) -> None:
        """ 暂停交易系统 """
        self.status = 'paused'
        msg = Text('Trader is Paused, broker is still running', style='bold red')
        self.send_message(message=msg)

    def _resume(self) -> None:
        """ 恢复交易系统 """
        self.status = self.prev_status
        msg = Text(f'Trader is resumed to previous status({self.status})', style='bold red')
        self.send_message(message=msg)

    def _run_strategy(self, *strategy_ids) -> int:
        """ 运行交易策略

        1，读取实时数据，设置operator的数据分配
        2，根据strtegy_ids设定operator的运行模式，生成交易信号
        3，解析信号为交易订单，并将交易订单发送到交易所的订单队列
        4，将交易订单的ID保存到数据库，更新账户和持仓信息
        5，生成交易订单状态信息推送到信息队列

        Parameters
        ----------
        strategy_ids: list of str
            交易策略ID列表

        Returns
        -------
        submitted_qty: int
            提交的交易订单数量
        """

        self.send_message(f'running task run strategy: {strategy_ids}', debug=True)
        operator = self._operator
        signal_type = operator.signal_type
        shares = self.asset_pool
        own_amounts = self.account_positions['qty']
        available_amounts = self.account_positions['available_qty']
        own_cash = self.account_cash[0]
        available_cash = self.account_cash[1]
        config = self._config
        # window_length = self._operator.max_window_length
        #
        # # 下载最小所需实时历史数据
        # data_end_time = self.get_current_tz_datetime()  # 产生本地时间
        max_strategy_freq = 'T'
        for strategy_id in strategy_ids:
            strategy = operator[strategy_id]
            freq = strategy.strategy_run_freq.upper()
            if TIME_FREQ_LEVELS[freq] < TIME_FREQ_LEVELS[max_strategy_freq]:
                max_strategy_freq = freq
        # 解析strategy_run的运行频率，根据频率确定是否下载实时数据
        self.send_message(f'getting live price data for strategy run...', debug=True)
        # # 将类似于'2H'或'15min'的时间频率转化为两个变量：duration和unit (duration=2, unit='H')/ (duration=15, unit='min')
        duration, unit, _ = parse_freq_string(max_strategy_freq, std_freq_only=False)
        if (unit.lower() in ['min', '5min', '15min', '30min', 'h']) and self.is_trade_day:
            # 如果strategy_run的运行频率为分钟或小时，则调用fetch_realtime_price_data方法获取分钟级别的实时价格
            # TODO: 实时价格不应该使用fetch_realtime_price_data方法，而应该使用fetch_realtime_quote方法
            table_to_update = UNIT_TO_TABLE[unit.lower()]
            # 这里不能将实时数据直接写入数据库，因为最新K线的数据可能尚不完整，只有上一个K线数据才是完整的
            real_time_data = fetch_real_time_klines(
                    freq=unit.lower(),
                    channel=self.live_price_channel,
                    qt_codes=self.asset_pool,
                    verbose=False,
                    matured_kline_only=True,  # 这里确保只获取成熟的K线数据
            )
            # 将real_time_data写入DataSource
            self.send_message(message=f'got real time data from channel {self.live_price_channel}:\n'
                                      f'{real_time_data.to_string()}\n'
                                      f'writing data to datasource: {self.datasource}...', debug=True)

            rows_written = self._datasource.update_table_data(
                    table=table_to_update,
                    df=real_time_data,
                    merge_type='update',
            )
            self.send_message(message=f'{rows_written} rows real-time price data written to'
                                      f'data source: {self.datasource}', debug=True)

        # 如果strategy_run的运行频率大于等于D，则不下载实时数据，使用datasource中的历史数据
        else:
            pass
        # 读取最新数据,设置operator的数据分配,创建trade_data
        self.send_message(f'preparing trade data...', debug=True)
        hist_op, hist_ref = check_and_prepare_live_trade_data(
                operator=operator,
                config=config,
                datasource=self._datasource,
                live_prices=self.live_price,
        )
        self.send_message(f'read real time data and set operator data allocation', debug=True)
        operator.assign_hist_data(
                hist_data=hist_op,
                reference_data=hist_ref,
                live_mode=True,
                live_running_stgs=list(strategy_ids)
        )

        # 生成N行5列的交易相关数据，包括当前持仓、可用持仓、当前价格、最近成交量、最近成交价格
        trade_data = np.zeros(shape=(len(shares), 5))
        position_availabilities = get_account_position_availabilities(
                account_id=self.account_id,
                shares=shares,
                data_source=self._datasource,
        )
        # 当前价格是hist_op的最后一行, 如果需要用latest_data_cycle，最新的实时数据已经包含在hist_op中了
        timing_type = operator[strategy_ids[0]].strategy_timing
        current_prices = hist_op[timing_type, :, -1].squeeze()
        if current_prices.ndim == 0:
            current_prices = np.array([current_prices])
        last_trade_result_summary = get_last_trade_result_summary(
                account_id=self.account_id,
                shares=shares,
                data_source=self._datasource,
        )
        self.send_message(f'Generating trade data from position availabilities...', debug=True)
        trade_data[:, 0] = position_availabilities[1]
        trade_data[:, 1] = position_availabilities[2]
        trade_data[:, 2] = current_prices
        trade_data[:, 3] = last_trade_result_summary[1]
        trade_data[:, 4] = last_trade_result_summary[2]

        if operator.op_type == 'batch':
            raise KeyError(f'Operator can not work in live mode when its operation type is "batch", set '
                           f'"Operator.op_type = "step"')
        else:
            op_signal = operator.create_signal(
                    trade_data=trade_data,
                    sample_idx=0,
                    price_type_idx=0
            )  # 生成交易清单
        self.send_message(f'ran strategy and created signal: {op_signal}', debug=True)

        # 解析交易信号
        symbols, positions, directions, quantities, quoted_prices, remarks = parse_trade_signal(
                signals=op_signal,
                signal_type=signal_type,
                shares=shares,
                prices=current_prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                available_amounts=available_amounts,  # 这里给出了available_amounts和available_cash，就不会产生超额交易订单
                available_cash=available_cash,
                config=config
        )
        names = get_symbol_names(self._datasource, symbols)
        submitted_qty = 0
        self.send_message(f'generated trade signals:\n'
                          f'symbols: {symbols}\n'
                          f'positions: {positions}\n'
                          f'directions: {directions}\n'
                          f'quantities: {quantities}\n'
                          f'current_prices: {quoted_prices}\n',
                          debug=True)
        for sym, name, pos, d, qty, price, remark in zip(
                symbols,
                names,
                positions,
                directions,
                quantities,
                quoted_prices,
                remarks,
        ):
            if remark:
                self.send_message(remark)
            if qty <= 0.001:
                continue

            trade_order = self.submit_trade_order(
                    symbol=sym,
                    position=pos,
                    direction=d,
                    order_type='market',
                    qty=qty,
                    price=price,
            )

            if trade_order:
                order_id = trade_order['order_id']
                self._broker.order_queue.put(trade_order)
                # format the message depending on buy/sell orders
                msg = Text(f'<NEW ORDER {order_id}>: <{name} - {sym}> ', style='bold')
                if d == 'buy':  # red for buy
                    msg.append(f'{d}-{pos} {qty} shares @ {price}', style='bold red')
                else:  # green for sell
                    msg.append(f'{d}-{pos} {qty} shares @ {price}', style='bold green')
                # 记录已提交的交易数量
                self.send_message(msg)
                submitted_qty += 1

        self.send_message(f'<RAN STRATEGY {tuple(strategy_ids)}>: {submitted_qty} orders submitted in total.')
        return submitted_qty

    def _process_result(self, result) -> None:
        """ 从result_queue中读取并处理交易结果

        1，处理交易结果，更新账户和持仓信息
        2，处理交易结果的交割，记录交割结果（未达到交割条件的交易结果不会被处理）
        3，生成交易结果信息推送到信息队列

        Parameters
        ----------
        result: dict
            交易结果

        Returns
        -------
        None
        """

        self.send_message(f'running task process_result, got result: \n{result}', debug=True)

        try:
            # 交易结果处理, 更新账户和持仓信息, 如果交易结果导致错误，不会更新账户和持仓信息
            trade_result = process_trade_result(result, data_source=self._datasource)
            result_id = trade_result['result_id']

        except Exception as e:
            self.send_message(f'{e} Error occurred during processing trade result, result will be ignored')
            import traceback
            self.send_message(f'Traceback: \n{traceback.format_exc()}', debug=True)
            return

        # 生成交易结果后，逐个检查交易结果并记录到trade_log文件并推送到信息队列（记录到system_log中）
        if result_id is None:
            return
        self.log_trade_result(full_trade_result=trade_result)

        # 执行交易结果的立即交割; 如果交割期为0，则立即交割结果，否则第二天开盘前集中交割
        deliver_result = deliver_trade_result(
                result_id=result_id,
                account_id=self.account_id,
                stock_delivery_period=self._config['stock_delivery_period'],
                cash_delivery_period=self._config['cash_delivery_period'],
                data_source=self._datasource,
        )

        # 记录交割结果到trade_log和system_log
        if deliver_result.get('delivery_status') != 'DL':
            return
        self.log_cash_delivery(delivery_result=deliver_result)
        self.log_qty_delivery(delivery_result=deliver_result)

    def _pre_open(self) -> None:
        """ pre_open处理所有应该在开盘前完成的任务，包括运行中断后重新开始trader所需的初始化任务：

        - 确保data_source重新连接,
        - 扫描数据源，下载缺失的数据
        - 处理订单的交割
        - 获取当日实时价格
        """

        self.send_message(f'Checking Trader and Broker connections...')
        datasource = self._datasource
        config = self._config
        operator = self._operator

        self.send_message(f'Reconnecting to datasource...')
        datasource.reconnect()

        self.send_message(f'Preparing historical financial data...')
        datasource.get_all_basic_table_data(
                refresh_cache=True,
                raise_error=False,
        )

        self.send_message(f'Preparing live trading data...')
        # 扫描数据源，下载缺失的日频或以上数据
        refill_missing_datasource_data(
                operator=operator,
                trader=self,
                config=config,
                datasource=datasource,
        )

        self.send_message(f'Looking for un-delivered trade results...')
        # 检查账户中的成交结果，完成全部交易结果的交割
        delivery_results = process_account_delivery(
                account_id=self.account_id,
                data_source=self._datasource,
                config=self._config,
        )

        # 生成交割结果信息推送到信息队列
        for res in delivery_results:
            if res.get('delivery_status') != 'DL':
                continue
            self.log_cash_delivery(res)
            self.log_qty_delivery(res)

        # 获取当日实时价格
        self._update_live_price()

    def _post_close(self) -> None:
        """ 所有收盘后应该完成的任务

        1，处理当日未完成的交易信号，生成取消订单，并记录订单取消结果
        2，处理当日已成交的订单结果的交割，记录交割结果
        3，生成消息发送到消息队列
        """
        self.send_message('running task post_close', debug=True)

        if self.is_market_open:
            self.send_message('market is still open, post_close can not be executed during open time!', debug=True)
            return

        # 检查order_queue中是否有任务，如果有，全部都是未处理的交易信号，生成取消订单
        order_queue = self.broker.order_queue
        # TODO: 已经submitted的订单如果已经有了成交结果，只是尚未记录的，则不应该取消，
        #   此处应该检查broker的result_queue，如果有结果，则推迟执行post_close，直到
        #   result_queue中的结果全部处理完毕，或者超过一定时间
        if not order_queue.empty():
            self.send_message('unprocessed orders found, these orders will be canceled')
            while not order_queue.empty():
                order = order_queue.get()
                order_id = order['order_id']
                cancel_order(order_id, data_source=self._datasource)  # 生成订单取消记录，并记录到数据库
                self.send_message(f'canceled unprocessed order: {order_id}')
                order_queue.task_done()
        # 检查今日成交订单，确认是否有"部分成交"的订单，如果有，生成取消订单，取消尚未成交的部分
        partially_filled_orders = query_trade_orders(
                account_id=self.account_id,
                status='partial-filled',
                data_source=self._datasource,
        )
        self.send_message(f'Looking for partial-filled orders... {len(partially_filled_orders)} found!')
        for order_id in partially_filled_orders.index:
            # 对于所有没有完全成交的订单，生成取消订单，取消剩余的部分
            cancel_order(order_id=order_id, data_source=self._datasource)
            self.send_message(f'Canceled remaining qty of partial-filled order: {order_id}')

        # 检查未提交订单，确认是否有"created"的订单，如果有，生成取消订单
        unsubmitted_orders = query_trade_orders(
                account_id=self.account_id,
                status='created',
                data_source=self._datasource,
        )
        self.send_message(f'Looking for Un-submitted orders... {len(unsubmitted_orders)} found!')

        for order_id in unsubmitted_orders.index:
            # 对于所有未成交的订单，生成取消订单
            cancel_order(order_id=order_id, data_source=self._datasource)
            self.send_message(f'Canceled un-submitted order: {order_id}')

        # 检查未成交订单，确认是否有"submitted"的订单，如果有，生成取消订单
        unfilled_orders = query_trade_orders(
                account_id=self.account_id,
                status='submitted',
                data_source=self._datasource,
        )
        self.send_message(f'Looking for Unfilled orders...{len(unfilled_orders)} found!')

        for order_id in unfilled_orders.index:
            # 对于所有未成交的订单，生成取消订单
            cancel_order(order_id=order_id, data_source=self._datasource)
            self.send_message(f'Canceled unfilled order: {order_id}')

    def _change_date(self) -> None:
        """ 改变日期，在日期改变（午夜）前执行的操作，包括：

        - 处理前一日交易的交割
        - 处理前一日获取的实时数据、并准备下一日的实时数据
        - 检查下一日是否是交易日，并更新相关的运行参数
        - 重新生成agenda
        - 生成消息发送到消息队列
        """
        raise NotImplementedError

    def _market_open(self) -> None:
        """ 开市时操作：

        1，启动broker的主循环，将broker的status设置为running
        2，生成消息发送到消息队列
        """
        self.send_message('running task: market open', debug=True)
        self.is_market_open = True
        self.run_task('wakeup')
        self.send_message('market is open, trader is running, broker is running')

    def _market_close(self) -> None:
        """ 收市时操作：

        1，停止broker的主循环，将broker的status设置为stopped
        2，生成消息发送到消息队列
        """
        self.send_message('running task: market close', debug=True)
        self.is_market_open = False
        self.run_task('sleep')
        self.send_message('market is closed, trader is slept, broker is paused')

    def _refill(self, tables: str, duration: int = 1, channel=None) -> None:
        """ 补充数据库内的历史数据
        通过tables指定需要更新的数据表名称

        Parameters
        ----------
        tables: str
            需要更新的数据表名称, 可以是单个表名，也可以是多个表名，用逗号分隔
        duration: str
            更新数据的周期，单位为天

        Returns
        -------
        None
        """
        self.send_message('running task: refill, this task will be done only during sleeping', debug=True)

        try:
            duration = int(duration)
        except Exception as e:
            self.send_message(f'Error occurred when trying to convert duration to integer: {e}'
                              f'Invalid duration: {duration}, will use default duration=1',
                              debug=True)
            duration = 1

        end_date = self.get_current_tz_datetime().date()
        start_date = end_date - pd.Timedelta(days=duration)
        if channel is None:
            channel = self.config['live_trade_data_refill_channel']
        else:
            channel = channel

        refill_data_batch_size = self.config['live_trade_data_refill_batch_size']
        refill_data_batch_interval = self.config['live_trade_data_refill_batch_interval']

        refill_data_source(
                tables=tables,
                channel=channel,
                start_date=start_date,
                end_date=end_date,
                refill_dependent_tables=False,
                data_source=self.datasource,
                refresh_trade_calendar=False,
                parallel=True,
                download_batch_size=refill_data_batch_size,
                download_batch_interval=refill_data_batch_interval,
        )

    # ================ task operations =================
    def run_task(self, task, *args, run_in_main_thread=False) -> None:
        """ 运行任务

        Parameters
        ----------
        task: str
            任务名称
        *args: tuple
            任务参数
        run_in_main_thread: bool, default False
            是否仅在主线程中运行任务
            如果设置为False，少数new_thread_tasks中的任务可以在新进程中运行
        """

        available_tasks = {
            'pre_open':           self._pre_open,
            'open_market':        self._market_open,
            'close_market':       self._market_close,
            'post_close':         self._post_close,
            'run_strategy':       self._run_strategy,
            'process_result':     self._process_result,
            'acquire_live_price': self._update_live_price,
            'change_date':        self._change_date,
            'start':              self._start,
            'stop':               self._stop,
            'sleep':              self._sleep,
            'wakeup':             self._wakeup,
            'pause':              self._pause,
            'resume':             self._resume,
            'refill':             self._refill,
        }

        if task is None:
            return
        if not isinstance(task, str):
            err = ValueError(f'task must be a string, got {type(task)} instead.')
            raise err

        if task not in available_tasks.keys():
            err = ValueError(f'Invalid task name: {task}')
            raise err

        task_func = available_tasks[task]

        new_thread_tasks = ['acquire_live_price', 'run_strategy']  # ‘proces_result’ was in the list before
        # TODO: 观察改进效果
        #  这里将'process_result'任务从new_thread_tasks中移除，因为process_result任务不能在单独的线程
        #  中运行，因为如果同时有多个交易结果需要处理，可能会导致多个数据被同时写入数据库，引起数据冲突导致
        #  数据结果不一致。这种不一致现在在一个订单分批同时成交时观察到了：当一个500股的买入订单分两批成交，
        #  第一批300股，第二批200股时，实际记录到数据库中的交易结果只有第二次成交记录，第一次成交记录丢失。
        #  从而引起数据混乱。现在修改后待观察是否还会出现这种情况。
        if (not run_in_main_thread) and (task in new_thread_tasks):
            from threading import Thread
            if args:
                t = Thread(target=task_func, args=args, daemon=True)
            else:
                t = Thread(target=task_func, daemon=True)
            self.send_message(f'will run task: {task} with args: {args} in a new Thread {t.name}', debug=True)
            t.start()
        else:
            self.send_message(f'running task: {task} with args: {args}', debug=True)
            if args:
                task_func(*args)
            else:
                task_func()

    def run_async_task(self, task, *args) -> None:
        """ 以异步方式执行任务

        Parameters
        ----------
        task: str
            任务名称
        *args: tuple
            任务参数
        """

        available_tasks = {
            'pre_open':           self._pre_open,
            'open_market':        self._market_open,
            'close_market':       self._market_close,
            'post_close':         self._post_close,
            'run_strategy':       self._run_strategy,
            'process_result':     self._process_result,
            'acquire_live_price': self._update_live_price,
            'change_date':        self._change_date,
            'start':              self._start,
            'stop':               self._stop,
            'sleep':              self._sleep,
            'wakeup':             self._wakeup,
            'pause':              self._pause,
            'resume':             self._resume,
            'refill':             self._refill,
        }

        if task is None:
            return
        if not isinstance(task, str):
            err = ValueError(f'task must be a string, got {type(task)} instead.')
            raise err

        if task not in available_tasks.keys():
            err = ValueError(f'Invalid task name: {task}')
            raise err

        task_func = available_tasks[task]

        async_tasks = ['acquire_live_price', 'run_strategy', 'process_result']

        if task not in async_tasks:
            err = ValueError(f'Invalid task name: {task}, only the following tasks can be run asynchronously: '
                             f'{async_tasks}')
            raise err

        from threading import Thread
        if args:
            t = Thread(target=task_func, args=args, daemon=True)
        else:
            t = Thread(target=task_func, daemon=True)
        self.send_message(f'will run task: {task} with args: {args} in a new Thread {t.name}', debug=True)
        t.start()

    # =============== internal methods =================

    def _check_trade_day(self, current_date=None) -> None:
        """ 检查当前日期是否是交易日

        Parameters
        ----------
        current_date: datetime.date, optional
            当前日期，默认为None，即当前日期为今天，指定日期用于测试

        Returns
        -------
        None
        """
        if current_date is None:
            current_date = self.get_current_tz_datetime().date()  # 产生本地时间
        from qteasy.utilfuncs import is_market_trade_day
        # exchange = self._config['exchange']  # TODO: should we add exchange to config?
        exchange = 'SSE'
        self.is_trade_day = is_market_trade_day(current_date, exchange)

    def _add_task_to_queue(self, task) -> None:
        """ 添加任务到任务队列

        Parameters
        ----------
        task: str
            任务名称
        """
        self.send_message(f'putting task {task} into task queue', debug=True)
        self.task_queue.put(task)

    def _add_task_from_schedule(self, current_time=None) -> None:
        """ 根据当前时间从任务日程中添加任务到任务队列，只有到时间时才添加任务

        Parameters
        ----------
        current_time: datetime.time, optional
            当前时间, 只有任务计划时间小于等于当前时间时才添加任务
            如果current_time为None，则使用当前系统时间，给出current_time的目的是为了方便测试
        """
        if current_time is None:
            current_time = self.get_current_tz_datetime().time()  # 产生本地时间
        task_added = False  # 是否添加了任务
        next_task = 'None'
        import datetime as dt
        convenience_date = dt.datetime(2000, 1, 1)
        current_datetime = dt.datetime.combine(convenience_date, current_time)
        end_of_the_day = dt.datetime.combine(convenience_date, dt.time(23, 59, 59))
        count_down_to_next_task = (end_of_the_day - current_datetime).total_seconds()  # 到下一个最近任务的倒计时，单位为秒
        if count_down_to_next_task <= 0:
            count_down_to_next_task = 1
        # 对比当前时间和任务日程中的任务时间，如果任务时间小于等于当前时间，添加任务到任务队列并删除该任务
        for idx, task in enumerate(self.task_daily_schedule):
            task_time = pd.to_datetime(task[0], utc=True).time()
            # 当task_time小于等于current_time时，添加task，同时删除该task
            if task_time <= current_time:
                task_tuple = self.task_daily_schedule.pop(idx)
                self.send_message(f'adding task: {task_tuple} from agenda', debug=True)
                if len(task_tuple) == 3:
                    task = task_tuple[1:3]
                elif len(task_tuple) == 2:
                    task = task[1]
                else:
                    err = ValueError(f'Invalid task tuple: No task found in {task_tuple}')
                    raise err

                self.send_message(f'current time {current_time} >= task time {task_time}, '
                                      f'adding task: {task} from agenda', debug=True)
                self._add_task_to_queue(task)
                task_added = True
            # 计算count_down_to_next_task秒数
            else:
                task_datetime = dt.datetime.combine(convenience_date, task_time)
                count_down_sec = (task_datetime - current_datetime).total_seconds()
                if count_down_sec < count_down_to_next_task:
                    count_down_to_next_task = count_down_sec
                    next_task = task
        if not task_added:
            self.next_task = next_task
            self.count_down_to_next_task = count_down_to_next_task

    def _initialize_schedule(self, current_time=None) -> None:
        """ 初始化交易日的任务日程, 在任务清单中添加以下任务：
        1. 每日固定事件如开盘、收盘、交割等
        2. 每日需要定时执行的交易策略
        3. 定时下载的实时数据

        Parameters
        ----------
        current_time: datetime.time, optional
            当前时间, 生成任务计划后，需要将当天已经过期的任务删除，即计划时间早于current_time的任务
            如果current_time为None，则使用当前系统时间，给出current_time的目的是为了方便测试
        """
        # if current_time is None then use current system time
        if current_time is None:
            # current_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).time()  # 产生UTC时间
            current_time = self.get_current_tz_datetime().time()  # 产生本地时间
        self.send_message('initializing agenda...', debug=True)
        # 如果不是交易日，直接返回
        # TODO: 不判断交易日，将交易日判断放到create_daily_task_schedule中进行
        # if not self.is_trade_day:
        #     self.send_message('not a trade day, no need to initialize agenda', debug=True)
        #     return
        if self.task_daily_schedule:
            # 如果任务日程非空列表，直接返回
            self.send_message('task agenda is not empty, no need to initialize agenda', debug=True)
            return

        self.task_daily_schedule = create_daily_task_schedule(
                operator=self.operator,
                config=self._config,
                is_trade_day=self.is_trade_day,
        )
        self.send_message(f'created complete daily schedule (to be further adjusted): {self.task_daily_schedule}',
                          debug=True)
        # 根据当前时间删除过期的任务
        moa = pd.to_datetime(self._config['market_open_time_am']).time()
        mca = pd.to_datetime(self._config['market_close_time_am']).time()
        moc = pd.to_datetime(self._config['market_open_time_pm']).time()
        mcc = pd.to_datetime(self._config['market_close_time_pm']).time()
        if current_time < moa:
            # before market morning open, keep all tasks
            self.send_message('before market morning open, keeping all tasks', debug=True)
        elif moa < current_time < mca:
            # market open time, remove all task before current time except pre_open
            self.send_message('market open, removing all tasks before current time except pre_open and open_market',
                              debug=True)
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'open_market'])]
        elif mca < current_time < moc:
            # before market afternoon open, remove all task before current time except pre_open, open_market and sleep
            self.send_message('before market afternoon open, removing all tasks before current time '
                              'except pre_open, open_market and sleep', debug=True)
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'open_market',
                                                     'close_market'])]
        elif moc < current_time < mcc:
            # market afternoon open, remove all task before current time except pre_open, open_market, sleep, and wakeup
            self.send_message('market afternoon open, removing all tasks before current time '
                              'except pre_open, open_market, sleep and wakeup', debug=True)
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'open_market',
                                                     'close_market'])]
        elif mcc < current_time:
            # after market close, remove all task before current time except pre_open and post_close
            self.send_message('market closed, removing all tasks before current time except '
                              'pre_open and post_close',
                              debug=True)
            # previously considered to add refill), but looks like it is not the best practice,
            # because this will result in multiple refill tasks if the user restart the trader
            # for many times after 16:00, this might not be the ideal case,
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'post_close',])]
        else:
            err = ValueError(f'Invalid current time: {current_time}')
            raise err

        self.send_message(f'adjusted daily schedule: {self.task_daily_schedule}', debug=True)

    def _update_live_price(self) -> None:
        """获取实时数据，并将实时数据更新到self.live_price中

        注：此函数并不将读取的数据写入datasource，且可能出现Timeout或运行失败"""
        self.send_message(f'Acquiring live price data', debug=True)
        real_time_data = fetch_real_time_klines(
                qt_codes=self.asset_pool,
                channel=self.live_price_channel,
                freq=self.operator.op_data_freq,
                verbose=False,
        )
        if real_time_data.empty:
            # empty data downloaded
            self.send_message(f'Something went wrong, failed to download live price data.', debug=True)
            return
        real_time_data.set_index('ts_code', inplace=True)
        # 将real_time_data 赋值给self.live_price
        self.live_price = real_time_data
        self.send_message(f'acquired live price data, live prices updated!', debug=True)
        return

    TASK_WHITELIST = {
        'stopped':  ['start'],
        'running':  ['stop', 'sleep', 'pause', 'run_strategy', 'process_result', 'pre_open',
                     'open_market', 'close_market', 'acquire_live_price'],
        'sleeping': ['wakeup', 'stop', 'pause', 'pre_open', 'close_market',
                     'process_result',  # 如果交易结果已经产生，哪怕处理时Trader已经处于sleeping状态，也应该处理完所有结果
                     'open_market', 'post_close', 'refill'],
        'paused':   ['resume', 'stop'],
    }


def start_trader_ui(
        operator: Operator,
        account_id: int = None,
        user_name: str = None,
        init_cash: float = None,
        init_holdings: dict = None,
        datasource: DataSource = None,
        config: dict = None,
        debug: bool = False,
) -> None:
    """ 启动交易。根据配置信息生成Trader对象，并启动TraderShell

    Parameters
    ----------
    operator: Operator
        交易员 object
    account_id: int, optional
        交易账户ID, 如果ID小于0或者未给出，则需要新建一个账户
    user_name: str, optional
        交易账户用户名，如果未给出账户ID或为空，则需要新建一个账户，此时必须给出用户名
    init_cash: float, optional
        初始资金，只有创建新账户时有效
    init_holdings: dict of {str: int}, optional
        初始持仓股票代码和数量的字典{'symbol': amount}，只有创建新账户时有效
    datasource: DataSource, optional
        数据源 object
    config: dict, optional, default None
        配置信息字典
    debug: bool, optional, default False
        是否进入debug模式

    Returns
    -------
    None
    """
    if not isinstance(operator, Operator):
        err = ValueError(f'operator must be an Operator object, got {type(operator)} instead.')
        raise err
    # if account_id is None then create a new account
    if (account_id is None) or (account_id < 0):
        if (user_name is None) or (user_name == ''):
            err = ValueError(f'Account_id is not given, Choose a valid account or create a new one:\n'
                             f'- to view all existing accounts, call: \'qt.live_trade_accounts()\'\n'
                             f'- to choose an existed account, set: \'live_trade_account_id=<ID>\'\n'
                             f'- to create a new account, set: \'live_trade_account_name="your_account_name"\'')
            raise err
        account_id = new_account(
                user_name=user_name,
                cash_amount=init_cash,
                data_source=datasource,
        )
    try:
        _ = get_account(account_id, data_source=datasource)
    except Exception as e:
        err = ValueError(f'{e}\nFailed to use account({account_id}), Choose a valid account or create a new one:\n'
                         f'- to choose an account, set: live_trade_account_id=<ID>\n'
                         f'- to create a new account, set: live_trade_account_name="your_account_name"')
        raise err

    # now we know that account_id is valid

    # if init_holdings is not None then add holdings to account
    if init_holdings is not None:
        if not isinstance(init_holdings, dict):
            err = ValueError(f'init_holdings must be a dict, got {type(init_holdings)} instead.')
            raise err
        for symbol, amount in init_holdings.items():
            pos_id = get_or_create_position(
                    account_id=account_id,
                    symbol=symbol,
                    position_type='long' if amount > 0 else 'short',
                    data_source=datasource,
            )
            update_position(
                    position_id=pos_id,
                    data_source=datasource,
                    **{
                        'qty_change':           abs(amount),
                        'available_qty_change': abs(amount),
                    }
            )

    # if account is ready then create trader and broker
    broker_type = config['live_trade_broker_type']
    broker_params = config['live_trade_broker_params']
    if (broker_type == 'simulator') and (broker_params is None):
        broker_params = {
            "fee_rate_buy":    config['cost_rate_buy'],
            "fee_rate_sell":   config['cost_rate_sell'],
            "fee_min_buy":     config['cost_min_buy'],
            "fee_min_sell":    config['cost_min_sell'],
            "fee_fix_buy":     config['cost_fixed_buy'],
            "fee_fix_sell":    config['cost_fixed_sell'],
            "slipage":         config['cost_slippage'],
            "moq_buy":         config['trade_batch_size'],
            "moq_sell":        config['sell_batch_size'],
            "delay":           1.0,
            "price_deviation": 0.001,
            # TODO: the probabilities should be a parameter passed in
            "probabilities":   (0.5, 0.45, 0.05),  # originally: (0.9, 0.08, 0.02)
        }

    from qteasy.broker import get_broker
    broker = get_broker(broker_type, broker_params)

    trader = Trader(
            account_id=account_id,
            operator=operator,
            broker=broker,
            config=config,
            datasource=datasource,
            debug=debug,
    )
    trader.register_broker(debug=trader.debug)

    # find out datasource availabilities, refill data source if table data not available
    refill_missing_datasource_data(
            operator=operator,
            trader=trader,
            config=config,
            datasource=datasource,
    )

    ui_type = config['live_trade_ui_type']
    if ui_type.lower() == 'cli':
        from .trader_cli import TraderShell
        TraderShell(trader).run()
    elif ui_type.lower() == 'tui':
        from .trader_tui import TraderApp
        TraderApp(trader).run()
    else:
        err= TypeError(f'Invalid ui type: ({ui_type})! use "cli" or "tui" instead.')
        raise err


def refill_missing_datasource_data(operator, trader, config, datasource) -> None:
    """ 针对日频或以上的数据，检查数据源中的数据可用性，下载缺失的数据到数据源

    在trader运行过程中，为了避免数据缺失，检查当前Datasource中的数据是否已经填充到最新日期，
    如果没有，则下载缺失的数据到数据源中，以便后续使用

    Parameters
    ----------
    operator: qt.Operator
        Operator交易员对象
    trader: Trader
        Trader交易对象
    config: qt.Config
        Config配置对象
    datasource: qt.Datasource
        Datasource数据源对象

    Returns
    -------
    None
    """

    # find out datasource availabilities, refill data source if table data not available
    op_data_types = operator.op_data_types
    op_data_freq = operator.op_data_freq
    asset_types = config['asset_type']
    if isinstance(asset_types, str):
        asset_types = str_to_list(asset_types)
    related_tables = get_tables_by_dtypes(
            dtypes=op_data_types,
            freqs=[op_data_freq],
            asset_types=asset_types,
    )
    related_tables = [table for table in related_tables]
    if len(related_tables) == 0:
        related_tables = ['stock_daily']
    elif len(related_tables) >= 1:
        pass
    table_availabilities = trader.datasource.overview(tables=related_tables, print_out=False)
    last_available_date = table_availabilities['max2'].max()
    try:
        last_available_date = pd.to_datetime(last_available_date)
    except:
        last_available_date = trader.get_current_tz_datetime() - pd.Timedelta(value=100, unit='d')
    from qteasy.utilfuncs import prev_market_trade_day
    today = trader.get_current_tz_datetime().strftime('%Y%m%d')
    last_trade_day = prev_market_trade_day(today) - pd.Timedelta(value=1, unit='d')
    if last_available_date < last_trade_day:
        # no need to refill if data is already filled up til yesterday

        if isinstance(config['asset_pool'], str):
            symbol_list = str_to_list(config['asset_pool'])
        else:
            symbol_list = config['asset_pool'].copy()  # to prevent from changing the config

        symbol_list.extend(['000300.SH', '000905.SH', '000001.SH', '399001.SZ', '399006.SZ'])
        asset_types = config['asset_type']
        if asset_types != 'IDX':
            # add index to make sure indices are downloaded
            asset_types += ', IDX'
        start_date = last_available_date
        end_date = trader.get_current_tz_datetime()

        refill_data_source(
                data_source=datasource,
                channel='tushare',
                tables=related_tables,
                dtypes=op_data_types,
                freqs=op_data_freq,
                asset_types=asset_types,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.to_pydatetime().strftime('%Y%m%d'),
                symbols=symbol_list,
                parallel=True,
                refresh_trade_calendar=False,
                refill_dependent_tables=False,
        )

    return None
