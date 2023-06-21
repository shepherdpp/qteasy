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

import time
import sys
from typing import Any, Callable, List, Union

import pandas as pd
import numpy as np

from threading import Thread
from queue import Queue
from cmd import Cmd

import qteasy
from qteasy import Operator, DataSource, ConfigDict
from qteasy.core import check_and_prepare_live_trade_data
from qteasy.utilfuncs import str_to_list, TIME_FREQ_LEVELS, parse_freq_string, sec_to_duration
from qteasy.broker import Broker, RandomBroker
from qteasy.trade_recording import get_account, get_account_position_details, get_account_position_availabilities
from qteasy.trade_recording import get_account_cash_availabilities, get_position_ids, query_trade_orders
from qteasy.trade_recording import new_account, get_or_create_position, update_position
from qteasy.trading_util import parse_trade_signal, submit_order, record_trade_order, process_trade_result
from qteasy.trading_util import process_trade_delivery, create_daily_task_agenda, cancel_order
from qteasy.trading_util import get_last_trade_result_summary

# TODO: 交易系统的配置信息，从QT_CONFIG中读取
TIME_ZONE = 'Asia/Shanghai'
# TIME_ZONE = 'UTC'


class TraderShell(Cmd):
    """

    """
    intro = 'Welcome to the trader shell interactive mode. Type help or ? to list commands.\n' \
            'Type "bye" to stop trader and exit shell.\n' \
            'Type "dashboard" to leave interactive mode and enter dashboard.\n' \
            'Type "help <command>" to get help for more commands.\n'
    prompt = '(QTEASY) '
    use_rawinput = False

    def __init__(self, trader):
        super().__init__()
        self._trader = trader
        self._status = None

    @property
    def trader(self):
        return self._trader

    @property
    def status(self):
        return self._status

    # ----- basic commands -----
    def do_status(self, arg):
        """ Show trader status

        Usage:
        ------
        status
        """
        sys.stdout.write(f'current trader status: {self.trader.status} \n'
                         f'current broker name: {self.trader.broker.broker_name} \n'
                         f'current broker status: {self.trader.broker.status} \n'
                         f'current day is trade day: {self.trader.is_trade_day} \n')

    def do_pause(self, arg):
        """ Pause trader

        When trader is paused, strategies will not be executed, orders will not be submitted,
        submitted orders will be suspended until trader is resumed

        Usage:
        ------
        pause
        """
        self.trader.add_task('pause')
        sys.stdout.write(f'current trader status: {self.trader.status} \n')

    def do_resume(self, arg):
        """ Resume trader

        When trader is resumed, strategies will be executed, orders will be submitted,
        suspended orders will be resumed

        Usage:
        ------
        resume
        """
        self.trader.add_task('resume')
        sys.stdout.write(f'current trader status: {self.trader.status} \n')

    def do_bye(self, arg):
        """ Stop trader and exit shell

        When trader is stopped, strategies will not be executed, orders will not be submitted,
        submitted orders will be suspended until trader is resumed

        Usage:
        ------
        bye
        """
        self.trader.add_task('stop')
        self._status = 'stopped'
        return True

    def do_info(self, arg):
        """ Get trader info, same as overview

        Get trader info, including basic information of current account, and
        current cash and positions.

        Usage:
        ------
        info [detail]
        """
        sys.stdout.write(f'current trader status: {self.trader.status} \n')
        self.trader.info()

    def do_positions(self, arg):
        """ Get account positions

        Get account positions, including all positions and available positions

        Usage:
        ------
        positions
        """
        print(self._trader.account_positions)
        # TODO: 打印持仓的股票名称，显示持仓收益情况

    def do_overview(self, arg):
        """ Get trader overview, same as info

        Get trader overview, including basic information of current account, and
        current cash and positions.

        Usage:
        ------
        overview [detail]
        """
        detail = False
        if arg is not None:
            if arg in ['detail', 'd']:
                detail = True
            else:
                print('argument not valid, input "detail" or "d" to get detailed info')
        self._trader.info(detail)
        # TODO: 打印持仓的股票名称，显示持仓收益情况，显示总投资金额和总收益率

    def do_history(self, arg):
        """ Get trader history

        Get trader history, including all orders, all trades, all cash and positions.

        Usage:
        ------
        history [orders] [cash] [positions] [today] [3day] [week] [month] [year] [details]
        """
        if arg is None or arg == '':
            arg = 'today'
        if not isinstance(arg, str):
            print('Please input a valid argument.')
            return
        print(f'{self} running history with arg: {arg}')

        if 'orders' in arg:
            print(self._trader.history_orders)
        if 'cash' in arg:
            print(self._trader.history_cashes)

    def do_orders(self, arg):
        """ Get trader orders

        Get trader orders, use arg to specify orders to get, default is today's orders

        Usage:
        ------
        orders [(F)filled] [(C)canceled] [(P)partial-filled] [(L)last_hour] [(T)today]
        [(3)3day] [(W)week] [(M)month] [(B)buy] [(S)sell] [symbols like '000001.SZ']
        """
        if arg is None or arg == '':
            arg = 'today'
        args = arg.split(' ')
        order_details = self._trader.history_orders()

        for argument in args:
            from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
            # select orders by time range arguments like 'last_hour', 'today', '3day', 'week', 'month'
            if argument in ['last_hour', 'l', 'today', 't', '3day', '3', 'week', 'w', 'month', 'm']:
                # create order time ranges
                end = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")
                if argument in ['last_hour', 'l']:
                    start = pd.to_datetime(end) - pd.Timedelta(hours=1)
                elif argument in ['today', 't']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=1)
                    start = start.strftime("%Y-%m-%d 00:00:00")
                elif argument in ['3day', '3']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=3)
                elif argument in ['week', 'w']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=7)
                elif argument in ['month', 'm']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=30)
                else:
                    start = pd.to_datetime(end) - pd.Timedelta(hours=1)
                # select orders by time range
                order_details = order_details[(order_details['submitted_time'] >= start) &
                                                (order_details['submitted_time'] <= end)]
            # select orders by status arguments like 'filled', 'canceled', 'partial-filled'
            elif argument in ['filled', 'f', 'canceled', 'c', 'partial-filled', 'p']:
                if argument in ['filled', 'f']:
                    order_details = order_details[order_details['status'] == 'filled']
                elif argument in ['canceled', 'c']:
                    order_details = order_details[order_details['status'] == 'canceled']
                elif argument in ['partial-filled', 'p']:
                    order_details = order_details[order_details['status'] == 'partial-filled']
            # select orders by order side arguments like 'long', 'short'
            elif argument in ['long', 'short']:
                if argument in ['long']:
                    order_details = order_details[order_details['position'] == 'long']
                elif argument in ['short']:
                    order_details = order_details[order_details['position'] == 'short']
            # select orders by order side arguments like 'buy', 'sell'
            elif argument in ['buy', 'b', 'sell', 's']:
                if argument in ['buy', 'b']:
                    order_details = order_details[order_details['direction'] == 'buy']
                elif argument in ['sell', 's']:
                    order_details = order_details[order_details['direction'] == 'sell']
            # select orders by order symbol arguments like '000001.SZ'
            elif is_complete_cn_stock_symbol_like(argument.upper()):
                order_details = order_details[order_details['symbol'] == argument.upper()]
            # select orders by order symbol arguments like '000001'
            elif is_cn_stock_symbol_like(argument):
                possible_complete_symbols = [argument+'.SH', argument+'.SZ', argument+'.BJ']
                order_details = order_details[order_details['symbol'].isin(possible_complete_symbols)]
            else:
                pass

        print(order_details.to_string(index=False))

    def do_change(self, arg):
        """ Change trader cash and positions
        to change cash, amount must be given
        to change a position, amount and symbol must be given, price is used to update cost,
        if not given, current price will be used, side is used to specify long or short side,
        if not given, long side will be used

        Usage:
        ------
        change cash/c <amount>
        change <symbol> <amount> [price] [long/l/short/s]

        Examples:
        ---------
        change cash/c 1000000:
            add 1000000 cash to trader account
        change 000001.SZ 1000 10.5:
            add 1000 shares of 000001.SZ to trader account with price 10.5 on long side (default)
        """
        print(f'{self} running change with arg: {arg}')
        args = arg.split(' ')
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like, is_number_like

        if args[0] in ['cash', 'c']:
            # change cash
            if len(args) < 2:
                print('Please input cash value to increase (+) or to decrease (-).')
                return
            try:
                amount = float(args[1])
            except ValueError:
                print('Please input cash value to increase (+) or to decrease (-).')
                return

            self.trader.change_cash(amount)
            return

        symbol = None
        if is_cn_stock_symbol_like(args[0].upper()):
            # check if input matches one of symbols in trader asset pool
            asset_pool = self.trader.asset_pool
            asset_pool_striped = [symbol.split('.')[0] for symbol in asset_pool]
            if args[0] not in asset_pool_striped:
                print(f'symbol {args[0]} not in trader asset pool, please check your input.')
                return
            symbol = asset_pool[asset_pool_striped.index(args[0])]

        if is_complete_cn_stock_symbol_like(args[0].upper()):
            symbol = args[0].upper()

        if symbol is None:
            print(f'"{args[0]}" invalid: Please input a valid symbol to change position holdings.')
            return

        if len(args) < 2:
            print('Please input valid arguments.')
            return

        # change positions: amount and symbol must be given, minus sign decrease. price is used to update cost,
        # if not given, current price will be used, side is used to specify long or short side, if not given,
        # current none-zero side will be used, if both sides are zero, long side will be used. if none-zero side
        # existed, the other side can not be changed.
        volume = float(args[1])
        try:
            freq = self.trader.operator.op_data_freq
            end = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE)
            start = end - pd.Timedelta(100, freq)
            last_available_data = self.trader.datasource.get_history_data(
                        shares=[symbol],
                        htypes='close',
                        asset_type=self.trader.asset_type,
                        start=start,
                        end=end,
                        freq=freq,
            )
            current_price = last_available_data['close'][symbol][-1]
        except Exception as e:
            print(f'Error: {e}, latest available data can not be donwloaded. 10.00 will be used as current price.')
            import traceback
            traceback.print_exc()
            current_price = 10.00
        if len(args) == 2:
            # 只给出两个参数，默认使用最新价格、side为已有的非零持仓
            price = current_price
            side = None
        elif (len(args) == 3) and (args[2] in ['long', 'short', 'l', 's']):
            # 只给出side参数，默认使用最新价格
            price = current_price
            side = 'long' if args[2] in ['long', 'l'] else 'short'
        elif (len(args) == 3) and (is_number_like(args[2])):
            # 只给出price参数，默认使用已有的非零持仓side
            price = float(args[2])
            side = None
        elif (len(args) == 4) and (is_number_like(args[2])) and (args[3] in ['long', 'short', 'l', 's']):
            # 既给出了价格，又给出了side
            price = float(args[2])
            side = 'long' if args[3] in ['long', 'l'] else 'short'
        elif (len(args) == 4) and (is_number_like(args[3])) and (args[2] in ['long', 'short', 'l', 's']):
            # 既给出了价格，又给出了side
            price = float(args[3])
            side = 'long' if args[2] in ['long', 'l'] else 'short'
        else:  # not a valid input
            print(f'{args} is not a valid input, Please input valid arguments.')
            return

        self._trader.change_position(
            symbol=symbol,
            quantity=volume,
            price=price,
            side=side,
        )

    def do_dashboard(self, arg):
        """ Enter dashboard mode, live status will be displayed

        Usage:
        ------
        dashboard
        """
        import os
        # check os type of current system, and then clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        self._status = 'dashboard'
        print('\nWelcome to TraderShell! currently in dashboard mode, live status will be displayed here.\n'
              'You can not input commands in this mode, if you want to enter interactive mode, please'
              'press "Ctrl+C" to exit dashboard mode and select from prompted options.\n')
        return True

    def do_strategies(self, arg):
        """ Show strategies

        Usage:
        ------
        strategies
        """
        print(f'All running strategies -- {self.trader.operator.strategies}')

    def do_agenda(self, arg):
        """ Show current strategy task agenda

        Usage:
        ------
        plan
        """
        print(f'Execution Agenda -- {self.trader.task_daily_agenda}')

    def do_run(self, arg):
        """ To run a strategy in current setup, only available in DEBUG mode.
        strategy id can be found in strategies command.

        Usage:
        ------
        run [strategy id]
        """
        if not self.trader.debug:
            print('Running strategy manually is only available in DEBUG mode')
            return
        strategies = arg
        if isinstance(strategies, str):
            strategies = str_to_list(arg)
        if not isinstance(strategies, list):
            print('Please input a valid strategy id, use "strategies" to view all ids.')
            return
        if not strategies:
            print('Please input a valid strategy id, use "strategies" to view all ids.')
            return
        all_strategy_ids = self.trader.operator.strategy_ids
        if not all([strategy in all_strategy_ids for strategy in strategies]):
            print('Please input a valid strategy id, use "strategies" to view all ids.')
            return

        current_trader_status = self.trader.status
        current_broker_status = self.trader.broker.status

        self.trader.status = 'running'
        self.trader.broker.status = 'running'
        print(f'[DEBUG] running strategy: {strategies}')

        try:
            self.trader.run_task('run_strategy', strategies)
        except Exception as e:
            import traceback
            print(f'Error in running strategy: {e}')
            print(traceback.format_exc())

        import time
        time.sleep(10)
        self.trader.status = current_trader_status
        self.trader.broker.status = current_broker_status

    # ----- overridden methods -----
    def precmd(self, line: str) -> str:
        """ Make all commands case-insensitive,
            remove trailing spaces,
            remove commas between arguments,
            and remove redundant spaces between words
        """
        line = line.lower()
        line = line.strip()
        line = line.replace(',', ' ')
        line = ' '.join(line.split())
        return line

    def run(self):
        from threading import Thread

        self.do_dashboard('')
        Thread(target=self.trader.run).start()
        Thread(target=self.trader.broker.run).start()

        while self.status != 'stopped':
            # it looks to me that while loop should be within the try block
            # but it is not, because if it is, the KeyboardInterrupt will not be caught
            # and the shell will not be able to exit.
            # but sometimes the KeyboardInterrupt will not be caught when the program is running
            # exactly on the line of try, and will cause the program to fail.
            try:
                if self.status == 'dashboard':
                    # check trader message queue and display messages
                    if not self._trader.message_queue.empty():
                        message = self._trader.message_queue.get()
                        if message[-2:] == '_R':
                            print(message[:-2], end='\r')
                        else:
                            print(message)
    
                elif self.status == 'command':
                    # get user command input and do commands
                    sys.stdout.write('will enter interactive mode.\n')
                    # check if data source is connected here, if not, reconnect
                    # if not self.trader.datasource.connected:
                    #     self.trader.datasource.reconnect()
                    self.cmdloop()
                else:
                    sys.stdout.write('status error, shell will exit, trader and broker will be shut down\n')
                    self.do_bye('')
            except KeyboardInterrupt:
                # ask user if he/she wants to: [1], command mode; [2], stop trader; [3 or other], resume dashboard mode
                option = input('\nWhat would you like? input number to select from below options: \n'
                               '[1], Enter command mode; \n'
                               '[2], Exit and stop the trader; \n'
                               '[3], Enter dashboard mode. \n'
                               'please input your choice: ')
                if option == '1':
                    self._status = 'command'
                elif option == '2':
                    self.do_bye('')
                else:
                    self.do_dashboard('')
            except Exception as e:
                self.stdout.write(f'Unexpected Error: {e}\n')
                import traceback
                traceback.print_exc()
                self.do_bye('')

        sys.stdout.write('Thank you for using qteasy!\n')


class Trader(object):
    """ Trader是交易系统的核心，它负责调度交易任务，根据交易日历和策略规则生成交易订单并提交给Broker

    Trader的核心包括：
        一个task_queue，它是一个FIFO队列，任何需要执行的任务都需要被添加到队列中才会执行，执行完成后从队列中删除。
        一个task_daily_agenda，它是list of tuples, 每个tuple包含一个交易时间和一项任务，例如
        (datetime.time(9, 30), 'open_market')，表示在每天的9:30开市
    Trader的main loop定期检查task_queue中的任务，如果有任务到达，就执行任务，否则等待下一个任务到达。
    如果在交易日中，Trader会定时将task_daily_agenda中的任务添加到task_queue中。
    如果不是交易日，Trader会打印当前状态，并等待下一个交易日。

    Attributes:
    -----------
    account_id: int
        账户ID
    broker: Broker
        交易所对象，接受交易订单并返回交易结果
    task_queue: list of tuples
        任务队列，每个任务是一个tuple，包含任务的执行时间和任务的名称
    task_daily_agenda: list of tuples
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
        if not isinstance(account_id, int):
            raise TypeError(f'account_id must be int, got {type(account_id)} instead')
        if not isinstance(operator, Operator):
            raise TypeError(f'operator must be Operator, got {type(operator)} instead')
        if not isinstance(broker, Broker):
            raise TypeError(f'broker must be Broker, got {type(broker)} instead')
        if not isinstance(config, dict):
            raise TypeError(f'config must be dict, got {type(config)} instead')
        if not isinstance(datasource, DataSource):
            raise TypeError(f'datasource must be DataSource, got {type(datasource)} instead')

        # TODO: 确定所有的config都在QT_CONFIG中后，default_config就不再需要了
        default_config = ConfigDict(
                {
                        'market_open_time_am':              '09:30:00',
                        'market_close_time_pm':             '15:30:00',
                        'market_open_time_pm':              '13:00:00',
                        'market_close_time_am':             '11:30:00',
                        'exchange':                         'SSE',
                        'cash_delivery_period':             0,
                        'stock_delivery_period':            0,
                        'asset_pool':                       None,
                        'market_close_day_loop_interval':   0,
                        'market_open_day_loop_interval':    0,
                        'strategy_open_close_timing_offset': 1,  # minutes, 策略在开盘和收盘运行时的偏移量
                }
        )

        self.account_id = account_id
        self._broker = broker
        self._operator = operator
        self._config = default_config
        self._config.update(qteasy.QT_CONFIG.copy())
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

        self.task_daily_agenda = []
        """任务日程是动态的，当agenda的时间晚于当前时间时，触发任务，同时将该任务从agenda中删除。第二天0:00重新生成新的agenda。
         在第一次生成agenda时，需要判断当前时间，并把已经过期的task删除，才能确保正常运行，同时添加pre_open任务确保pre_open总会被执行

        现在采用动态agenda方式设计的原因是，如果采用静态agenda，在交易mainloop中可能重复执行任务或者漏掉任务。"""

        self.is_trade_day = False
        self._status = 'stopped'
        self._prev_status = None

        self.account = get_account(self.account_id, self._datasource)

        self.debug = debug

    # ================== properties ==================
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in ['running', 'sleeping', 'paused', 'stopped']:
            raise ValueError(f'invalid status: {value}')
        self._prev_status = self._status
        self._status = value

    @property
    def prev_status(self):
        return self._prev_status

    @property
    def operator(self):
        return self._operator

    @property
    def broker(self):
        return self._broker

    @property
    def asset_pool(self):
        """ 账户的资产池，一个list，包含所有允许投资的股票代码 """
        return self._asset_pool

    @property
    def asset_type(self):
        """ 账户的资产类型，一个str，包含所有允许投资的资产类型 """
        return self._asset_type

    @property
    def account_cash(self):
        """ 账户的现金, 包括持有现金和可用现金 """
        return get_account_cash_availabilities(self.account_id, data_source=self._datasource)

    @property
    def account_positions(self):
        """ 账户的持仓，一个tuple,包含两个ndarray，包括每种股票的持有数量和可用数量 """
        shares = self.asset_pool

        positions = get_account_position_details(
                self.account_id,
                shares=shares,
                data_source=self._datasource
        )
        return positions.T

    @property
    def non_zero_positions(self):
        """ 账户当前的持仓，一个tuple，当前持有非零的股票仓位symbol，持有数量和可用数量 """
        positions = self.account_positions
        return positions.loc[positions['qty'] != 0]

    @property
    def datasource(self):
        return self._datasource

    # ================== methods ==================
    def run(self):
        """ 交易系统的main loop：

        1，检查task_queue中是否有任务，如果有任务，则提取任务，根据当前status确定是否执行任务，如果可以执行，则执行任务，否则忽略任务
        2，如果当前是交易日，检查当前时间是否在task_daily_agenda中，如果在，则将任务添加到task_queue中
        3，如果当前是交易日，检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
        """
        self.status = 'sleeping'
        self._check_trade_day()
        self._initialize_agenda()
        self.post_message(f'Trader is running with account_id: {self.account_id}\n'
                          f'Initialized on date / time: '
                          f'{pd.to_datetime("now", utc=True).tz_convert(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S")}\n'
                          f'current day is trade day: {self.is_trade_day}\n'
                          f'running agenda: {self.task_daily_agenda}')
        # market_open_day_loop_interval = self._config['market_open_day_loop_interval']
        # market_close_day_loop_interval = self._config['market_close_day_loop_interval']
        market_open_day_loop_interval = 1
        market_close_day_loop_interval = 1
        current_date_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE)
        current_date = current_date_time.date()
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
                        if self.debug:
                            self.post_message(f'tuple task: {task} is taken from task queue, task[0]: {task[0]}'
                                              f'task[1]: {task[1]}')
                        task_name = task[0]
                        args = task[1]
                    else:
                        task_name = task
                        args = None
                    if self.debug:
                        self.post_message(f'task queue is not empty, taking next task from queue: {task_name}')
                    if task_name not in white_listed_tasks:
                        if self.debug:
                            self.post_message(f'task: {task} cannot be executed in current status: {self.status}')
                        self.task_queue.task_done()
                        continue
                    try:
                        if args:
                            self.run_task(task_name, args)
                        else:
                            self.run_task(task_name)
                    except Exception as e:
                        self.post_message(f'error occurred when executing task: {task_name}, error: {e}')
                        if self.debug:
                            import traceback
                            traceback.print_exc()
                    self.task_queue.task_done()

                # 如果没有暂停，从任务日程中添加任务到任务队列
                current_date_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE)
                current_time = current_date_time.time()
                current_date = current_date_time.date()
                if self.status != 'paused':
                    self._add_task_from_agenda(current_time)
                # 如果日期变化，检查是否是交易日，如果是交易日，更新日程
                if current_date != pre_date:
                    self._check_trade_day()
                    self._initialize_agenda(current_time)

                # 检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
                if not self.broker.result_queue.empty():
                    result = self.broker.result_queue.get()
                    self.post_message(f'got new result from broker for order {result["order_id"]}, '
                                      f'adding process_result task to queue')
                    self.add_task('process_result', result)

                time.sleep(sleep_interval)
            else:
                # process trader when trader is normally stopped
                self.post_message('Trader completed and exited.')
        except KeyboardInterrupt:
            self.post_message('KeyboardInterrupt, stopping trader')
            self.run_task('stop')
        except Exception as e:
            self.post_message(f'error occurred when running trader, error: {e}')
            if self.debug:
                import traceback
                traceback.print_exc()

    def history_cashes(self, start_date=None, end_date=None):
        """ 账户的历史现金流水 """
        # TODO: implement this function
        from qteasy.trade_recording import query_cash_flows
        return query_cash_flows(self.account_id, start_date, end_date, data_source=self._datasource)

    def history_positions(self, start_date=None, end_date=None):
        """ 账户的历史持仓 """
        # TODO: implement this function
        from qteasy.trade_recording import query_positions
        return query_positions(self.account_id, start_date, end_date, data_source=self._datasource)

    def info(self, detail=False):
        """ 打印账户的概览，包括账户基本信息，持有现金和持仓信息

        Parameters:
        -----------
        detail: bool, default False
            是否打印持仓的详细信息

        Returns:
        --------
        None
        """
        print('Account Overview:')
        print('-----------------')
        print(f'Account ID: {self.account_id}')
        print(f'User Name: {self.account["user_name"]}')
        print(f'Created on: {self.account["created_time"]}')
        if detail:
            print(f'Own Cash/Available: {self.account_cash[0]} / {self.account_cash[1]}')
            print(f'Own / Available Positions: \n{self.non_zero_positions}')
        return None

    def trade_results(self, status='filled'):
        """ 账户的交易结果 """
        from qteasy.trade_recording import read_trade_results_by_order_id
        from qteasy.trade_recording import query_trade_orders
        trade_orders = query_trade_orders(
                self.account_id,
                status=status,
                data_source=self._datasource
        )
        order_ids = trade_orders.index.values
        return read_trade_results_by_order_id(order_id=order_ids, data_source=self._datasource)

    def post_message(self, message, new_line=True):
        """ 发送消息到消息队列, 在消息前添加必要的信息如日期、时间等

        Parameters
        ----------
        message: str
            消息内容
        new_line: bool, default True
            是否在消息后添加换行符
        """
        if not isinstance(message, str):
            raise TypeError('message should be a str')
        time_string = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).strftime('%Y-%m-%d %H:%M:%S')
        message = f'[{time_string}]-{self.status}: {message}'
        if not new_line:
            message += '_R'
        if self.debug:
            message = f'[DEBUG]-{message}'
        self.message_queue.put(message)

    def add_task(self, task, kwargs=None):
        """ 添加任务到任务队列

        Parameters
        ----------
        task: str
            任务名称
        **kwargs: dict
            任务参数
        """
        if not isinstance(task, str):
            raise TypeError('task should be a str')
        if kwargs and (not isinstance(kwargs, dict)):
            raise TypeError('kwargs should be a dict')

        if task not in self.AVAILABLE_TASKS:
            raise ValueError('task {} is not available'.format(task))

        if kwargs:
            task = (task, kwargs)
        self.post_message(f'adding task: {task}')
        self._add_task_to_queue(task)

    def _process_result(self, result):
        """ 从result_queue中读取并处理交易结果

        1，处理交易结果，更新账户和持仓信息
        2，处理交易结果的交割，记录交割结果（未达到交割条件的交易结果不会被处理）
        4，生成交易结果信息推送到信息队列
        """
        if self.debug:
            self.post_message('running task process_result')
        if self.debug:
            self.post_message(f'process_result: got result: \n{result}')
        process_trade_result(result, data_source=self._datasource)
        self.post_message(f'processed trade result: \n{result}')
        process_trade_delivery(
                account_id=self.account_id,
                data_source=self._datasource,
                config=self._config,
        )

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
            - qty: int, 订单数量
            - price: float, 订单价格
            - submitted_time: datetime, 订单提交时间
            - status: str, 订单状态，filled/canceled/partial-filled
            - price_filled: float, 成交价格
            - filled_qty: int, 成交数量
            - canceled_qty: int, 撤单数量
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
                           'price_filled', 'filled_qty', 'canceled_qty', 'execution_time',
                           'delivery_status'],
        )
        return order_result_details

    # ============ definition of tasks ================
    def _start(self):
        """ 启动交易系统 """
        self.post_message('starting Trader')
        self.status = 'sleeping'

    def _stop(self):
        """ 停止交易系统 """
        self.post_message('stopping Trader, the broker will be stopped as well')
        self._broker.status = 'stopped'
        self.status = 'stopped'

    def _sleep(self):
        """ 休眠交易系统 """
        self.post_message('Putting Trader to sleep')
        self.status = 'sleeping'
        self.broker.status = 'paused'

    def _wakeup(self):
        """ 唤醒交易系统 """
        self.status = 'running'
        self.broker.status = 'running'
        self.post_message('Trader is awake, broker is running')

    def _pause(self):
        """ 暂停交易系统 """
        self.status = 'paused'
        self.post_message('Trader is Paused, broker is still running')

    def _resume(self):
        """ 恢复交易系统 """
        self.status = self.prev_status
        self.post_message(f'Trader is resumed to previous status({self.status})')

    def _run_strategy(self, strategy_ids=None):
        """ 运行交易策略

        1，读取实时数据，设置operator的数据分配
        2，根据strtegy_id设定operator的运行模式，生成交易信号
        3，解析信号为交易订单，并将交易订单发送到交易所的订单队列
        4，将交易订单的ID保存到数据库，更新账户和持仓信息
        5，生成交易订单状态信息推送到信息队列

        Parameters
        ----------
        strategy_ids: list of str
            交易策略ID列表
        """
        if self.debug:
            self.post_message(f'running task run strategy: {strategy_ids}')
        operator = self._operator
        signal_type = operator.signal_type
        shares = self.asset_pool
        own_amounts = self.account_positions['qty']
        own_cash = self.account_cash[0]
        config = self._config

        # 下载最小所需实时历史数据
        # 在run_strategy过程中，可以假定需要下载的数据为最小所需数据，即只需要下载最近一个周期内的交易数据
        # 数据下载区间结束时间是现在，数据下载周期为所有策略中最大运行周期（最低频率），开始时间是结束时间减去周期
        data_end_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE)
        max_strategy_freq = 'T'
        for strategy_id in strategy_ids:
            strategy = operator[strategy_id]
            freq = strategy.strategy_run_freq.upper()
            if TIME_FREQ_LEVELS[freq] < TIME_FREQ_LEVELS[max_strategy_freq]:
                max_strategy_freq = freq
        # 将类似于'2H'或'15min'的时间频率转化为两个变量：duration和unit (duration=2, unit='H')/ (duration=15, unit='min')
        duration, unit, _ = parse_freq_string(max_strategy_freq, std_freq_only=True)
        data_start_time = data_end_time + pd.Timedelta(duration, unit)
        # 由于在每次strategy_run的时候仅下载最近一个周期的数据，因此在live_trade开始前都需要下载足够多的数据（至少是window_length）
        # TODO: 目前在这里获取最新股票数据的实现方式还有很多问题，需要解决：
        #  2，需要解决parallel读取的问题，在目前的测试中，parallel读取会导致数据读取失败
        if self.debug:
            self.post_message(f'downloading data from {data_start_time} to {data_end_time}')
        self._datasource.refill_local_source(
                dtypes=operator.op_data_types,
                freqs=operator.op_data_freq,
                asset_types='E',
                start_date=data_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_date=data_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                symbols=self.asset_pool,
                parallel=False,
                refresh_trade_calendar=False
        )
        # 读取实时数据,设置operator的数据分配,创建trade_data
        hist_op, hist_ref, invest_cash_plan = check_and_prepare_live_trade_data(
                operator=operator,
                config=config,
                datasource=self._datasource,
        )
        if self.debug:
            self.post_message(f'read real time data and set operator data allocation')
        operator.assign_hist_data(hist_data=hist_op, cash_plan=invest_cash_plan, reference_data=hist_ref,
                                  live_mode=True, live_running_stgs=strategy_ids)

        # 生成N行5列的交易相关数据，包括当前持仓、可用持仓、当前价格、最近成交量、最近成交价格
        trade_data = np.zeros(shape=(len(shares), 5))
        position_availabilities = get_account_position_availabilities(
                account_id=self.account_id,
                shares=shares,
                data_source=self._datasource,
        )
        # 当前价格是hist_op的最后一行  # TODO: 需要根据strategy_timing获取价格的类型（如open价格或close价格）
        timing_type = operator[strategy_ids[0]].strategy_timing
        current_prices = hist_op[timing_type, :, -1].squeeze()
        last_trade_result_summary = get_last_trade_result_summary(
                account_id=self.account_id,
                shares=shares,
                data_source=self._datasource,
        )
        if self.debug:
            self.post_message(f'generating trade data from position availabilities, current prices and last trade:\n'
                              f'position_availabilities: \n{position_availabilities}\n'
                              f'current_prices: {current_prices}\n'
                              f'last_trade_result_summary: \n{last_trade_result_summary}')
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
                    sample_idx=1,
                    price_type_idx=0
            )  # 生成交易清单
        if self.debug:
            self.post_message(f'ran strategy and created signal: {op_signal}')

        # 解析交易信号
        symbols, positions, directions, quantities, quoted_prices = parse_trade_signal(
                signals=op_signal,
                signal_type=signal_type,
                shares=shares,
                prices=current_prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                config=config
        )
        submitted_qty = 0
        if self.debug:
            self.post_message(f'generated trade signals:\n'
                              f'symbols: {symbols}\n'
                              f'positions: {positions}\n'
                              f'directions: {directions}\n'
                              f'quantities: {quantities}\n'
                              f'current_prices: {quoted_prices}\n')
        for sym, pos, d, qty, price in zip(symbols, positions, directions, quantities, quoted_prices):
            pos_id = get_or_create_position(account_id=self.account_id,
                                              symbol=sym,
                                              position_type=pos,
                                              data_source=self._datasource)

            # 生成交易订单dict
            trade_order = {
                'pos_id':         pos_id,
                'direction':      d,
                'order_type':     'market',  # TODO: order type is to be properly defined
                'qty':            qty,
                'price':          price,
                'submitted_time': None,
                'status':         'created',
            }

            order_id = record_trade_order(trade_order, data_source=self._datasource)
            # 逐一提交交易信号
            if submit_order(order_id=order_id, data_source=self._datasource) is not None:
                trade_order['order_id'] = order_id
                self._broker.order_queue.put(trade_order)
                self.post_message(f'Submitted order to broker: {trade_order}')
                # 记录已提交的交易数量
                submitted_qty += qty

        return submitted_qty

    def _pre_open(self):
        """ 开市前, 确保data_source重新连接"""
        for retry in range(3):
            if self._datasource.reconnect():
                break
            else:
                self._datasource.reconnect()
        # test if data source is connected
        self._datasource.reconnect()
        self._datasource.get_all_basic_table_data(
                refresh_cache=True,
        )
        self.post_message(f'data source reconnected, connection status: {self._datasource.con.db}')

    def _post_close(self):
        """ 收市后例行操作：

        1，处理当日未完成的交易信号，生成取消订单，并记录订单取消结果
        2，处理当日已成交的订单结果的交割，记录交割结果
        3，生成消息发送到消息队列
        """
        if self.debug:
            self.post_message('running task post_close')

        # 检查order_queue中是否有任务，如果有，全部都是未处理的交易信号，生成取消订单
        order_queue = self.broker.order_queue
        if not order_queue.empty():
            self.post_message('unprocessed orders found, these orders will be canceled')
            while not order_queue.empty():
                order = order_queue.get()
                order_id = order['order_id']
                cancel_order(order_id, data_source=self._datasource)  # 生成订单取消记录，并记录到数据库
                self.post_message(f'canceled unprocessed order: {order_id}')
                order_queue.task_done()
        # 检查今日成交订单，确认是否有"部分成交"以及"未成交"的订单，如果有，生成取消订单，取消尚未成交的部分
        partially_filled_orders = query_trade_orders(
                account_id=self.account_id,
                status='partial-filled',
                data_source=self._datasource,
        )
        unfilled_orders = query_trade_orders(
                account_id=self.account_id,
                status='submitted',
                data_source=self._datasource,
        )
        orders_to_be_canceled = pd.concat([partially_filled_orders, unfilled_orders])
        if self.debug:
            self.post_message(f'partially filled orders found, they are to be canceled: \n{orders_to_be_canceled}')
        for order_id in orders_to_be_canceled.index:
            # 部分成交订单不为空，需要生成一条新的交易记录，用于取消订单中的未成交部分，并记录订单结果
            self.post_message('partially filled orders found, unfilled part will be canceled')
            cancel_order(order_id=order_id, data_source=self._datasource)
            self.post_message(f'canceled unfilled order: {order_id}')

        # 检查今日成交结果，完成交易结果的交割
        process_trade_delivery(
                account_id=self.account_id,
                data_source=self._datasource,
                config=self._config
        )
        self.post_message('processed trade delivery')

    def _market_open(self):
        """ 开市时操作：

        1，启动broker的主循环，将broker的status设置为running
        2，生成消息发送到消息队列
        """
        if self.debug:
            self.post_message('running task: market open')
        self.is_market_open = True
        self.run_task('wakeup')
        self.post_message('market is open, trader is running, broker is running')

    def _market_close(self):
        """ 收市时操作：

        1，停止broker的主循环，将broker的status设置为stopped
        2，生成消息发送到消息队列
        """
        if self.debug:
            self.post_message('running task: market close')
        self.is_market_open = False
        self.run_task('sleep')
        self.post_message('market is closed, trader is slept, broker is paused')

    def _refill(self, tables, freq):
        """ 补充数据库内的历史数据 """
        # TODO： implement this function
        if self.debug:
            self.post_message('running task: refill, this task will be done only during sleeping')
        # 更新数据源中的数据，不同频率的数据表可以不同时机更新，每次更新时仅更新当天或最近一个freq的数据
        # 例如，freq为H或min的数据，更新当天的数据，freq为W的数据，更新最近一周
        # 在arg中必须给出freq以及tables两个参数，tables参数直接传入refill_local_source函数
        # freq被用于计算start_date和end_date
        end_date = datetime.now().date()
        if freq == 'D':
            start_date = end_date
        elif freq == 'W':
            start_date = end_date - timedelta(days=7)
        elif freq == 'M':
            start_date = end_date - timedelta(days=30)
        else:
            raise ValueError(f'invalid freq: {freq}')
        self._datasource.refill_local_source(
                tables=tables,
                start_date=start_date,
                end_date=end_date,
                merge_type='update',
        )

    # ================ task operations =================
    def run_task(self, task, *args):
        """ 运行任务

        Parameters
        ----------
        task: str
            任务名称
        *args: tuple
            任务参数
        """

        if task is None:
            return
        if not isinstance(task, str):
            raise ValueError(f'task must be a string, got {type(task)} instead.')

        if task not in self.AVAILABLE_TASKS.keys():
            raise ValueError(f'Invalid task name: {task}')

        task_func: Union[Union[Callable, None], Any] = self.AVAILABLE_TASKS[task]
        if self.debug:
            self.post_message(f'will run task: {task} with args: {args} in function: {task_func.__name__}')
        if args:
            task_func(self, *args)
        else:
            task_func(self)

    # =============== internal methods =================

    def _check_trade_day(self, current_date=None):
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
            current_date = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).date()
        from qteasy.utilfuncs import is_market_trade_day
        # exchange = self._config['exchange']  # TODO: should we add exchange to config?
        exchange = 'SSE'
        self.is_trade_day = is_market_trade_day(current_date, exchange)

    def _add_task_to_queue(self, task):
        """ 添加任务到任务队列

        Parameters
        ----------
        task: str
            任务名称
        """
        if self.debug:
            self.post_message(f'putting task {task} into task queue')
        self.task_queue.put(task)

    def _add_task_from_agenda(self, current_time=None):
        """ 根据当前时间从任务日程中添加任务到任务队列，只有到时间时才添加任务

        Parameters
        ----------
        current_time: datetime.time, optional
            当前时间, 只有任务计划时间小于等于当前时间时才添加任务
            如果current_time为None，则使用当前系统时间，给出current_time的目的是为了方便测试
        """
        if current_time is None:
            current_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).time()
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
        for idx, task in enumerate(self.task_daily_agenda):
            task_time = pd.to_datetime(task[0], utc=True).time()
            # 当task_time小于等于current_time时，添加task，同时删除该task
            if task_time <= current_time:
                task_tuple = self.task_daily_agenda.pop(idx)
                if self.debug:
                    self.post_message(f'adding task: {task_tuple} from agenda')
                if len(task_tuple) == 3:
                    task = task_tuple[1:3]
                elif len(task_tuple) == 2:
                    task = task[1]
                else:
                    raise ValueError(f'Invalid task tuple: No task found in {task_tuple}')

                if self.debug:
                    self.post_message(f'current time {current_time} >= task time {task_time}, '
                                  f'adding task: {task} from agenda')
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
            self.post_message(f'will execute next task:({next_task}) in '
                              f'{sec_to_duration(count_down_to_next_task, estimation=True)}',
                              new_line=False)

    def _initialize_agenda(self, current_time=None):
        """ 初始化交易日的任务日程, 在任务清单中添加以下任务：
        1. 每日固定事件如开盘、收盘、交割等
        2. 每日需要定时执行的交易策略
        3. 需要定期下载的历史数据（这部分信息需要在QT_CONFIG中定义）

        Parameters
        ----------
        current_time: datetime.time, optional
            当前时间, 生成任务计划后，需要将当天已经过期的任务删除，即计划时间早于current_time的任务
            如果current_time为None，则使用当前系统时间，给出current_time的目的是为了方便测试
        """
        # if current_time is None then use current system time
        if current_time is None:
            current_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).time()
        if self.debug:
            self.post_message('initializing agenda')
        # 如果不是交易日，直接返回
        if not self.is_trade_day:
            if self.debug:
                self.post_message('not a trade day, no need to initialize agenda')
            return
        if self.task_daily_agenda:
            # 如果任务日程非空列表，直接返回
            if self.debug:
                self.post_message('task agenda is not empty, no need to initialize agenda')
            return
        self.task_daily_agenda = create_daily_task_agenda(
                self.operator,
                self._config
        )
        # 根据当前时间删除过期的任务
        moa = pd.to_datetime(self._config['market_open_time_am']).time()
        mca = pd.to_datetime(self._config['market_close_time_am']).time()
        moc = pd.to_datetime(self._config['market_open_time_pm']).time()
        mcc = pd.to_datetime(self._config['market_close_time_pm']).time()
        if current_time < moa:
            # before market morning open, keep all tasks
            if self.debug:
                self.post_message('before market morning open, keeping all tasks')
        elif moa < current_time < mca:
            # market open time, remove all task before current time except pre_open
            if self.debug:
                self.post_message('market open, removing all tasks before current time except pre_open and open_market')
            self.task_daily_agenda = [task for task in self.task_daily_agenda if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                      (task[1] in ['pre_open', 'open_market'])]
        elif mca < current_time < moc:
            # before market afternoon open, remove all task before current time except pre_open, open_market and sleep
            if self.debug:
                self.post_message('before market afternoon open, removing all tasks before current time '
                                  'except pre_open, open_market and sleep')
            self.task_daily_agenda = [task for task in self.task_daily_agenda if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                          (task[1] in ['pre_open', 'open_market', 'sleep'])]
        elif moc < current_time < mcc:
            # market afternoon open, remove all task before current time except pre_open, open_market, sleep, and wakeup
            if self.debug:
                self.post_message('market afternoon open, removing all tasks before current time '
                                  'except pre_open, open_market, sleep and wakeup')
            self.task_daily_agenda = [task for task in self.task_daily_agenda if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                          (task[1] in ['pre_open', 'open_market'])]
        elif mcc < current_time:
            # after market close, remove all task before current time except post_close
            if self.debug:
                self.post_message('market closed, removing all tasks before current time except post_close')
            self.task_daily_agenda = [task for task in self.task_daily_agenda if
                                      (pd.to_datetime(task[0]).time() >= current_time) or (task[1] == 'post_close')]
        else:
            raise ValueError(f'Invalid current time: {current_time}')

    def change_cash(self, amount):
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

        cash_amount, available_cash = get_account_cash_availabilities(
                account_id=self.account_id,
                data_source=self.datasource
        )
        if amount < -available_cash:
            print(f'Not enough cash to decrease, available cash: {available_cash}, change amount: {amount}')
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
        print(f'Cash amount changed to {self.account_cash}')
        return

    def change_position(self, symbol, quantity, price, side=None):
        """ 手动修改仓位，查找指定标的和方向的仓位，增加或减少其持仓数量，同时根据新的持仓数量和价格计算新的持仓成本

        修改后持仓的数量 = 原持仓数量 + quantity
        如果找不到指定标的和方向的仓位，则创建一个新的仓位
        如果不指定方向，则查找当前持有的非零仓位，使用持有仓位的方向，如果没有持有非零仓位，则默认为'long'方向
        如果已经持有的非零仓位和指定的方向不一致，则忽略该操作
        如果quantity为负且绝对值大于可用数量，则忽略该操作

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
                    print(f'Position {position_id} is not empty, cannot change side')
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
                        account_id=self.trader.account_id,
                        symbol=symbol,
                        position_type=side,
                        data_source=self.datasource,
                )
        position = get_position_by_id(
                pos_id=position_id,
                data_source=self.datasource,
        )
        print(f'Changing position {position_id} {position["symbol"]}/{position["position"]} '
              f'from {position["qty"]} to {position["qty"] + quantity}')
        # 如果减少持仓，则可用持仓数量必须足够，否则退出
        if quantity < 0 and position['available_qty'] < -quantity:
            print(f'Not enough position to decrease, available position: {position["available_qty"]}')
            return
        current_total_cost = position['cost'] * position['qty']
        additional_cost = np.round(price * float(quantity), 2)
        new_average_cost = np.round((current_total_cost + additional_cost) / (position['qty'] + quantity), 2)
        if np.isinf(new_average_cost):
            new_average_cost = 0
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
        print(f'[DEBUG] position {position_id} changed with data: {position_data}')
        return

    AVAILABLE_TASKS = {
        'pre_open':         _pre_open,
        'open_market':      _market_open,
        'close_market':     _market_close,
        'post_close':       _post_close,
        'run_strategy':     _run_strategy,
        'process_result':   _process_result,
        'start':            _start,
        'stop':             _stop,
        'sleep':            _sleep,
        'wakeup':           _wakeup,
        'pause':            _pause,
        'resume':           _resume,
        'refill':           _refill,
    }

    TASK_WHITELIST = {
        'stopped':     ['start'],
        'running':     ['stop', 'sleep', 'pause', 'run_strategy', 'process_result', 'pre_open',
                        'open_market', 'close_market'],
        'sleeping':    ['wakeup', 'stop', 'pause', 'pre_open', 'open_market', 'post_close', 'refill'],
        'paused':      ['resume', 'stop'],
    }


def start_trader(
        operator,
        account_id=None,
        user_name=None,
        init_cash=None,
        init_holdings=None,
        datasource=None,
        config=None,
        debug=False,
):
    """ 启动交易。根据配置信息生成Trader对象，并启动TraderShell

    Parameters
    ----------
    operator: Operator
        交易员 object
    account_id: str, optional
        交易账户ID
    user_name: str, optional
        交易账户用户名，如果未给出账户ID，则需要新建一个账户，此时必须给出用户名
    init_cash: float, optional
        初始资金，只有创建新账户时有效
    init_holdings: dict of {str: int}, optional
        初始持仓股票代码和数量的字典{'symbol': amount}，只有创建新账户时有效
    datasource: DataSource, optional
        数据源 object
    config: dict, optional
        配置信息字典
    debug: bool, optional
        是否进入debug模式

    Returns
    -------
    None
    """
    if not isinstance(operator, Operator):
        raise ValueError(f'operator must be an Operator object, got {type(operator)} instead.')

    # if account_id is None then create a new account
    if account_id is None:
        if user_name is None:
            raise ValueError('if account_id is None, user_name must be given.')
        account_id = new_account(
                user_name=user_name,
                cash_amount=init_cash,
                data_source=datasource,
        )
        # if init_holdings is not None then add holdings to account
        if init_holdings is not None:
            if not isinstance(init_holdings, dict):
                raise ValueError(f'init_holdings must be a dict, got {type(init_holdings)} instead.')
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
                            'qty_change': abs(amount),
                            'available_qty_change': abs(amount),
                        }
                )
    try:
        _ = get_account(account_id, datasource)
    except Exception as e:
        raise ValueError(f'{e}\naccount {account_id} does not exist.')

    # if account is ready then create trader and broker
    broker = RandomBroker(
            fee_rate_buy=0.0001,
            fee_rate_sell=0.0003,
    )
    trader = Trader(
            account_id=account_id,
            operator=operator,
            broker=broker,
            config=config,
            datasource=datasource,
            debug=debug,
    )
    trader.broker.debug = debug
    # refill data source, start date is window length before today
    end_date = pd.to_datetime('today')
    start_date = end_date - pd.Timedelta(days=operator.max_window_length * 2)
    datasource.refill_local_source(
            tables='index_daily',
            dtypes=operator.op_data_types,
            freqs=operator.op_data_freq,
            asset_types='E, IDX',  # only support equities for now
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.to_pydatetime().strftime('%Y%m%d'),
            symbols=config['asset_pool'].extend(['000300.SH', '000905.SH', '000001.SH', '399001.SZ', '399006.SZ']),
            parallel=True,
            refresh_trade_calendar=True,
    )

    TraderShell(trader).run()
