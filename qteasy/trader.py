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

import pandas as pd
import numpy as np
import shutil

from threading import Timer
from queue import Queue
from cmd import Cmd
from rich import print as rprint

import qteasy
from qteasy import Operator, DataSource, ConfigDict
from qteasy.core import check_and_prepare_live_trade_data
from qteasy.utilfuncs import str_to_list, TIME_FREQ_LEVELS, parse_freq_string, sec_to_duration, adjust_string_length
from qteasy.utilfuncs import get_current_tz_datetime
from qteasy.broker import Broker
from qteasy.trade_recording import get_account, get_account_position_details, get_account_position_availabilities
from qteasy.trade_recording import get_account_cash_availabilities, query_trade_orders, record_trade_order
from qteasy.trade_recording import new_account, get_or_create_position, update_position, read_trade_order_detail
from qteasy.trade_recording import get_position_by_id
from qteasy.trading_util import parse_trade_signal, submit_order, process_trade_result
from qteasy.trading_util import process_account_delivery, create_daily_task_schedule, cancel_order
from qteasy.trading_util import get_last_trade_result_summary, get_symbol_names

UNIT_TO_TABLE = {
            'h':     'stock_hourly',
            '30min': 'stock_30min',
            '15min': 'stock_15min',
            '5min':  'stock_5min',
            '1min':  'stock_1min',
            'min':   'stock_1min',
        }


def parse_shell_argument(arg: str = None, default=None, command_name=None) -> list:
    """ 解析输入的参数, 返回解析后的参数列表，

    解析输入参数，所有的输入参数都是字符串，包括命令后的所有字符
    首先删除多余的空格，将字符串全部转化为小写，再将字符串以空格分割成参数列表。如果输入是空字符串，转化为空列表。
    参数列表中所有参数的类型都是字符串，在调用时各自转换为相应的类型

    Parameters:
    -----------
    arg: str
        输入的参数
    default: str, default None
        如果输入参数为空，返回的默认值

    Returns:
    --------
    args: list
        解析后的参数
    """
    # TODO: should return:
    #  a dict that contains values of all arguments, such as:
    #  {'arg1': (value),
    #   'arg2': value2}
    #  maybe should use parser to parse arguments, arguments defined in each command
    if arg is None:
        return [] if default is None else [default]
    arg = arg.lower().strip()  # 将字符串全部转化为小写并删除首尾空格
    while '  ' in arg:
        arg = arg.replace('  ', ' ')  # 删除字符间多余的空格
    if arg == '':
        return [] if default is None else [default]
    args = arg.split(' ')
    # 当用户仍然使用原来的parameter格式时（不带"-"），打印DeprecatedWarning
    if any(arg[0] != '-' for arg in args):
        # update args, add "-" in short args and "--" in long args
        new_args = []
        example_arg = ''
        for arg in args:
            if len(arg) == 1 and (not arg.isdigit()):
                new_args.append("-" + arg)
                example_arg = "-" + arg
            elif all(char.isdigit() for char in arg[:2]):  # do nothing for parameters started with at least two digits
                new_args.append(arg)
            elif arg[0] == '-':  # do nothing if arg starts with '-' or '--' already
                new_args.append(arg)
            else:
                new_args.append("--" + arg)
                example_arg = "--" + arg

        if example_arg:
            from rich import print as rprint
            rprint(f'[bold red]FutureWarning[/bold red]: plain style parameters will be deprecated in future versions, '
                   f'use "{command_name} {example_arg}" instead\n')

        args = new_args

    return args


class TraderShell(Cmd):
    """ 基于Cmd的交互式shell，用于实盘交易模式与用户交互

    提供了基本操作命令，包括：
    - status: 查看交易系统状态
    - pause: 暂停交易系统
    - resume: 恢复交易系统
    - bye: 停止交易系统并退出shell
    - exit: 停止交易系统并退出shell
    - stop: 停止交易系统并退出shell
    - info: 查看交易系统信息
    - change: 手动修改交易系统的资金和持仓
    - positions: 查看账户持仓
    - orders: 查看账户订单
    - history: 查看账户历史交易记录
    - overview: 查看账户概览
    - config: 查看或修改qt_config配置信息
    - dashboard: 退出shell，进入dashboard模式
    - strategies: 查看策略信息，或者修改策略参数
    - agenda: 查看交易日程
    - help: 查看帮助信息
    - run: 手动运行交易策略，此功能仅在debug模式下可用

    在Shell运行过程中按下 ctrl + c 进入状态选单，用户可以选择进入dashboard模式或者退出shell

    """
    intro = 'Welcome to the trader shell interactive mode. Type help or ? to list commands.\n' \
            'Type "bye" to stop trader and exit shell.\n' \
            'Type "dashboard" to leave interactive mode and enter dashboard.\n' \
            'Type "help <command>" to get help for more commands.\n'
    prompt = '(QTEASY) '

    def __init__(self, trader):
        super().__init__(completekey='tab')
        self._trader = trader
        self._timezone = trader.time_zone
        self._status = None
        self._watch_list = ['000001.SH']  # default watched price is SH index
        self._watched_prices = ' == Realtime prices can be displayed here. ' \
                               'Use "watch" command to add stocks to watch list. =='  # watched prices string

    @property
    def trader(self):
        return self._trader

    @property
    def status(self):
        return self._status

    def watch_list(self):
        return self._watch_list

    def update_watched_prices(self):
        """ 根据watch list返回清单中股票的信息：代码、名称、当前价格、涨跌幅
        """
        if self._watch_list:
            from .emfuncs import stock_live_kline_price
            symbols = self._watch_list
            live_prices = stock_live_kline_price(symbols, freq='D', verbose=True, parallel=False)
            if not live_prices.empty:
                live_prices.close = live_prices.close.astype(float)
                live_prices['change'] = live_prices['close'] / live_prices['pre_close'] - 1
                live_prices.set_index('symbol', inplace=True)

            #     # if self.trader.debug:
            #     #     self.trader.send_message('live prices acquired to update watched prices!')
            # else:
            #
            #     if self.trader.debug:
            #         self.trader.send_message('Failed to acquire live prices to update watch price string!')

            watched_prices = ''
            for symbol in symbols:
                if symbol in live_prices.index:
                    change = live_prices.loc[symbol, 'change']
                    watched_prices_seg = f' ={symbol[:-3]}{live_prices.loc[symbol, "name"]}/' \
                                         f'{live_prices.loc[symbol, "close"]:.2f}/' \
                                         f'{live_prices.loc[symbol, "change"]:+.2%}'
                    if change > 0:
                        watched_prices += ('[bold red]' + watched_prices_seg + '[/bold red]')
                    elif change < 0:
                        watched_prices += ('[bold green]' + watched_prices_seg + '[/bold green]')
                    else:
                        watched_prices += watched_prices_seg

                else:
                    watched_prices += f' ={symbol[:-3]}/--/---'
            self._watched_prices = watched_prices
        else:
            self._watched_prices = ' == Realtime prices can be displayed here. ' \
                                   'Use "watch" command to add stocks to watch list. =='
        return

    # ----- basic commands -----
    # TODO: add escape warning when realtime data acquiring is not available
    def do_status(self, arg):
        """ Show trader status

        Usage:
        ------
        status
        """

        from rich import print as rprint
        if arg:
            rprint(f'status command does not accept arguments\n')
        rprint(f'current trader status: {self.trader.status} \n'
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
        if arg:
            sys.stdout.write(f'pause command does not accept arguments\n')
            return False
        self.trader.add_task('pause')
        sys.stdout.write(f'Pausing trader...\n')

    def do_resume(self, arg):
        """ Resume trader

        When trader is resumed, strategies will be executed, orders will be submitted,
        suspended orders will be resumed

        Usage:
        ------
        resume
        """
        if arg:
            sys.stdout.write(f'resume command does not accept arguments\n')
            return False
        self.trader.add_task('resume')
        sys.stdout.write(f'Resuming trader...\n')

    def do_bye(self, arg):
        """ Stop trader and exit shell

        When trader is stopped, strategies will not be executed, orders will not be submitted,
        submitted orders will be suspended until trader is resumed

        Usage:
        ------
        bye

        Aliases:
        --------
        exit, stop
        """
        if arg:
            sys.stdout.write(f'bye command does not accept arguments\n')
            return False
        print(f'canceling all unfinished orders')
        self.trader.add_task('post_close')
        print(f'stopping trader...')
        self.trader.add_task('stop')
        self._status = 'stopped'
        return True

    def do_exit(self, arg):
        """ Stop trader and exit shell

        When trader is stopped, strategies will not be executed, orders will not be submitted,
        submitted orders will be suspended until trader is resumed

        Usage:
        ------
        exit

        Aliases:
        --------
        bye, stop
        """
        self.do_bye(arg)
        return True

    def do_stop(self, arg):
        """ Stop trader and exit shell

        When trader is stopped, strategies will not be executed, orders will not be submitted,
        submitted orders will be suspended until trader is resumed

        Usage:
        ------
        stop

        Aliases:
        --------
        bye, exit
        """
        self.do_bye(arg)
        return True

    def do_info(self, arg):
        """ Get trader info, same as overview

        Get trader info, including basic information of current account, and
        current cash and positions.

        Usage:
        ------
        info [--detail｜-d]
        """
        self.do_overview(arg)

    def do_pool(self, arg):
        """ print information of the asset pool

        Print detailed information of all stocks in the asset pool, including
        stock symbol, name, company name, industry, listed date, etc.

        """
        # TODO: implement this function
        return

    def do_watch(self, arg):
        """ Add or remove stock symbols to watch list

        Usage:
        ------
        watch [SYMBOL [SYMBOL ...]] [--position|--positions|-pos|-p]

        symbol:     Add symbols explicitly to watch list:
        position:   Add 5 symbols from position list to watch list:
        watch
        """

        from rich import print as rprint
        args = parse_shell_argument(arg, command_name='watch')
        if not args:
            sys.stdout.write(f'Current watch list: {self._watch_list}\n'
                             f'input symbols to add to watch list, like 000651.SZ\n')
            return False
        if args:
            arg_count = len(args)
            if arg_count > 5:
                args = args[:5]
        from .utilfuncs import TS_CODE_IDENTIFIER_CN_STOCK
        import re
        for arg in args:
            # 如果arg=='--position' 或者 '--positions'，则将当前持仓量最大的股票代码添加到watch list
            if arg in ['--position', '--positions', '-pos', '-p']:
                pos = self._trader.account_position_info
                if pos.empty:
                    print('No holding position at the moment.')
                    continue
                top_5_pos = pos.sort_values(by='market_value', ascending=False).head(5)
                top_5_pos = top_5_pos.index.tolist()
                self._watch_list = top_5_pos
                continue
            # 检查arg是否股票代码，如果是，添加到watch list，除非该代码已在watch list中
            if re.match(TS_CODE_IDENTIFIER_CN_STOCK, arg.upper()):
                if arg not in self._watch_list:
                    self._watch_list.append(arg.upper())
                # 检查watch_list中代码个数是否超过5个，如果超过，删除最早添加的代码
                if len(self._watch_list) > 5:
                    self._watch_list.pop(0)
        rprint(f'current watch list: {self._watch_list}')

    def do_buy(self, arg):
        """ Manually create buy-in order: buy AMOUNT shares of SYMBOL with PRICE
        the order will be submitted to broker and will be executed according to broker rules

        --long / --short indicates position to buy, default long
        --force indicates force buy regardless of current prices # TODO: to be implemented

        Usage:
        ------
        buy AMOUNT SYMBOL PRICE [--long|-l|--short|-s] [--force|-f]

        Notes:
        ------
        Currently only market price orders can be submitted

        Examples:
        ---------
        # buy in 100 shares of 000651.SH at price 32.5
        buy 100 000651.SH 32.5
        # buy short 100 shares of 000651.SH at price 30.0
        buy 100 000651.SH 30.0 --short
        """
        account_id = self.trader.account_id
        datasource = self.trader.datasource
        broker = self.trader.broker
        args = parse_shell_argument(arg)
        if len(args) < 3:
            print(f'Not enough argument, Command buy takes at least 3 positional arguments: AMOUNT SYMBOL and PRICE. '
                  f'use "help buy" to see more info')
            return
        try:
            qty = float(args[0])
            symbol = args[1].upper()
            price = float(args[2])
            position = 'long'
        except:
            print(f'Wrong format for positional argument AMOUNT or PRICE, please check your input. '
                  f'use "help buy" to see more info')
            return
        if len(args) >= 4:
            if args[3] not in ['--long', '-l', '--short', '-s']:
                print(f'Wrong argument: {args[3]}, use "help buy" to see more info')
                return
            if args[3] in ['--short', '-s']:
                position = 'short'
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like
        if not is_complete_cn_stock_symbol_like(symbol):
            print(f'Wrong symbol is given: {symbol}, please check your input!')
            return
        if qty <= 0 or price <= 0:
            print(f'Qty or price can not be less or equal to 0, please check your input!')
        pos_id = get_or_create_position(account_id=account_id,
                                        symbol=symbol,
                                        position_type=position,
                                        data_source=datasource)

        # 生成交易订单dict
        trade_order = {
            'pos_id':         pos_id,
            'direction':      'buy',
            'order_type':     'market',  # 'limit' or 'market'
            'qty':            qty,
            'price':          price,
            'submitted_time': None,
            'status':         'created',
        }

        order_id = record_trade_order(trade_order, data_source=datasource)
        # 逐一提交交易信号
        if submit_order(order_id=order_id, data_source=datasource) is not None:
            trade_order['order_id'] = order_id
            broker.order_queue.put(trade_order)
        pass

    def do_sell(self, arg):
        """ Manually create sell-out order: sell AMOUNT shares of SYMBOL with PRICE
        the order will be submitted to broker and will be executed according to broker rules

        --long / --short indicates position to buy, default long
        --force indicates force buy regardless of current prices # TODO: to be implemented

        Usage:
        ------
        sell AMOUNT SYMBOL PRICE [--long|-l|--short|-s] [--force|-f]

        Notes:
        ------
        Currently only market price orders can be submitted

        Examples:
        ---------
        # sell out 100 shares of 000651.SH at price 32.5
        sell 100 000651.Sh 32.5
        # sell short 100 shares of 000651 at price 30.0
        sell 100 000651.SH 30.0 --short
        """
        account_id = self.trader.account_id
        datasource = self.trader.datasource
        broker = self.trader.broker
        args = parse_shell_argument(arg)
        if len(args) < 3:
            print(f'Not enough argument, Command buy takes at least 3 positional arguments: AMOUNT SYMBOL and PRICE. '
                  f'use "help buy" to see more info')
            return
        try:
            qty = float(args[0])
            symbol = args[1].upper()
            price = float(args[2])
            position = 'long'
        except:
            print(f'Wrong format for positional argument AMOUNT or PRICE, please check your input. '
                  f'use "help buy" to see more info')
            return
        if len(args) >= 4:
            if args[3] not in ['--long', '-l', '--short', '-s']:
                print(f'Wrong argument: {args[3]}, use "help buy" to see more info')
                return
            if args[3] in ['--short', '-s']:
                position = 'short'
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like
        if not is_complete_cn_stock_symbol_like(symbol):
            print(f'Wrong symbol is given: {symbol}, please check your input!')
            return
        if qty <= 0 or price <= 0:
            print(f'Qty or price can not be less or equal to 0, please check your input!')
        pos_id = get_or_create_position(account_id=account_id,
                                        symbol=symbol,
                                        position_type=position,
                                        data_source=datasource)

        # 生成交易订单dict
        trade_order = {
            'pos_id':         pos_id,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            qty,
            'price':          price,
            'submitted_time': None,
            'status':         'created',
        }

        order_id = record_trade_order(trade_order, data_source=datasource)
        # 逐一提交交易信号
        if submit_order(order_id=order_id, data_source=datasource) is not None:
            trade_order['order_id'] = order_id
            broker.order_queue.put(trade_order)
        pass

    def do_positions(self, arg):
        """ Get account positions

        Get account positions, including all positions and available positions

        Usage:
        ------
        positions
        """

        if arg:
            sys.stdout.write(f'positions command does not accept arguments\n')
            return False
        from rich import print as rprint
        print(f'current positions: \n')
        pos = self._trader.account_position_info
        if pos.empty:
            print('No holding position at the moment.')
        pos_string = pos.to_string(
                columns=['qty', 'available_qty', 'cost', 'current_price',
                         'market_value', 'profit', 'profit_ratio', 'name'],
                header=['qty', 'available', 'cost', 'price', 'market_value', 'profit', 'profit_ratio', 'name'],
                col_space={
                    'name':          8,
                    'qty':           10,
                    'available_qty': 10,
                    'cost':          12,
                    'current_price': 10,
                    'market_value':  14,
                    'profit':        14,
                    'profit_ratio':  14,
                },
                justify='right',
        )
        pos_header_string = pos_string.split('\n')[0]
        earning_pos = pos[pos['profit'] >= 0].sort_values(by='profit', ascending=False)
        losing_pos = pos[pos['profit'] < 0].sort_values(by='profit', ascending=False)
        nan_profit_pos = pos[pos['profit'].isna()]
        if not earning_pos.empty:
            earning_pos_string = earning_pos.to_string(
                    columns=['qty', 'available_qty', 'cost', 'current_price',
                             'market_value', 'profit', 'profit_ratio', 'name'],
                    header=None,
                    index_names=False,
                    formatters={'name':          '{:8s}'.format,
                                'qty':           '{:,.2f}'.format,
                                'available_qty': '{:,.2f}'.format,
                                'cost':          '¥{:,.2f}'.format,
                                'current_price': '[bold red]¥{:,.2f}'.format,
                                'market_value':  '¥{:,.2f}'.format,
                                'profit':        '¥{:,.2f}'.format,
                                'profit_ratio':  '{:.2%}[/bold red]'.format},
                    col_space={
                        'name':          8,
                        'qty':           10,
                        'available_qty': 10,
                        'cost':          12,
                        'current_price': 20,
                        'market_value':  14,
                        'profit':        14,
                        'profit_ratio':  14,
                    },
                    justify='right',
            )
        else:
            earning_pos_string = ''
        if not losing_pos.empty:
            losing_pos_string = losing_pos.to_string(
                    columns=['qty', 'available_qty', 'cost', 'current_price',
                                'market_value', 'profit', 'profit_ratio', 'name'],
                    header=None,
                    index_names=False,
                    formatters={'name':          '{:8s}'.format,
                                'qty':           '{:,.2f}'.format,
                                'available_qty': '{:,.2f}'.format,
                                'cost':          '¥{:,.2f}'.format,
                                'current_price': '[bold green]¥{:,.2f}'.format,
                                'market_value':  '¥{:,.2f}'.format,
                                'profit':        '¥{:,.2f}'.format,
                                'profit_ratio':  '{:.2%}[/bold green]'.format},
                    col_space={
                        'name':          8,
                        'qty':           10,
                        'available_qty': 10,
                        'cost':          12,
                        'current_price': 22,
                        'market_value':  14,
                        'profit':        14,
                        'profit_ratio':  12,
                    },
                    justify='right',
            )
        else:
            losing_pos_string = ''
        if not nan_profit_pos.empty:
            nan_profit_pos_string = nan_profit_pos.to_string(
                    columns=['qty', 'available_qty', 'cost', 'current_price',
                                'market_value', 'profit', 'profit_ratio', 'name'],
                    header=None,
                    index_names=False,
                    formatters={'name':          '{:8s}'.format,
                                'qty':           '{:,.2f}'.format,
                                'available_qty': '{:,.2f}'.format,
                                'cost':          '¥{:,.2f}'.format,
                                'current_price': '¥{:,.2f}'.format,
                                'market_value':  '¥{:,.2f}'.format,
                                'profit':        '¥{:,.2f}'.format,
                                'profit_ratio':  '{:.2%}'.format},
                    col_space={
                        'name':          8,
                        'qty':           10,
                        'available_qty': 10,
                        'cost':          12,
                        'current_price': 22,
                        'market_value':  14,
                        'profit':        14,
                        'profit_ratio':  14,
                    },
                    justify='right',
            )
        else:
            nan_profit_pos_string = ''
        rprint(f'{pos_header_string}\n{earning_pos_string}\n{losing_pos_string}\n{nan_profit_pos_string}')

    def do_overview(self, arg):
        """ Get trader overview, same as info

        Get trader overview, including basic information of current account, and
        current cash and positions.

        Usage:
        ------
        overview [--detail|-d]
        """
        detail = False
        args = parse_shell_argument(arg, command_name='overview')
        if args:
            if args[0] in ['--detail', '-d']:
                detail = True
            else:
                print('argument not valid, input "detail" or "d" to get detailed info')
        self._trader.info(verbose=detail)
        if detail:
            self.do_positions(arg=None)

    def do_config(self, arg):
        """ Show or change qteasy configurations

        Display current qt configurations to designated level, if level is not given, display
        until level 2.
        if configure key is given and value is not given, display current value, default value
        and explanation of the configure key.
        if configure key and a value is given, change the configure key to the given value.

        Usage:
        ------
        config [[level]|[key]] [value]

        Examples:
        ---------
        config 3
        - display all qt configurations to level 3
        config mode
        - display current value, default value and explanation of configure key 'mode'
        config mode 2
        - change configure key 'mode' to value 2
        """

        from qteasy._arg_validators import _vkwargs_to_text
        from rich import print as rprint
        import shutil
        column_width, _ = shutil.get_terminal_size()
        column_width = int(column_width * 0.75) if column_width > 120 else column_width
        args = parse_shell_argument(arg, command_name='config')
        if len(args) == 0:
            config = self.trader.get_config()
            rprint(_vkwargs_to_text(config,
                                    level=[0],
                                    info=True,
                                    verbose=False,
                                    width=column_width)
                   )
        elif len(args) == 1:
            if args[0].isdigit():  # arg is level
                config = self.trader.get_config()
                level = int(args[0])
                rprint(_vkwargs_to_text(config,
                                        level=list(range(0, level + 1)),
                                        info=True,
                                        verbose=False,
                                        width=column_width)
                       )
            else:  # arg is key
                config = self.trader.get_config(args[0])
                key = args[0]
                value = config[key]
                if value is None:
                    print(f'configure key "{key}" not found.')
                    return
                rprint(_vkwargs_to_text(config,
                                        level='all',
                                        info=True,
                                        verbose=True,
                                        width=column_width)
                       )
        elif len(args) == 2:
            key = args[0]
            value = args[1]
            try:
                result = self.trader.update_config(key, value)
                if result:
                    rprint(f'configure key "{key}" has been changed to "{value}".')
                else:
                    rprint(f'configure key "{key}" can not be changed to "{value}".')
            except Exception as e:
                print(f'Error: {e}')
                if self.trader.debug:
                    import traceback
                    traceback.print_exc()
            return
        else:
            rprint(f'config command does not accept more than 2 arguments\n')
            return

    def do_history(self, arg):
        """ List trade history of a stock

        List all trade history of one particular stock, displaying every buy-in and sell-out
        in a table format. a symbol is required.

        Usage:
        ------
        history [symbol]
        """

        from rich import print as rprint
        args = parse_shell_argument(arg, command_name='history')
        history = self._trader.history_orders()

        if history.empty:
            print('No trade history found.')
            return

        for argument in args:
            from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
            if is_complete_cn_stock_symbol_like(argument.upper()):
                history = history[history['symbol'] == argument.upper()]
                # select orders by order symbol arguments like '000001'
            elif is_cn_stock_symbol_like(argument):
                possible_complete_symbols = [argument + '.SH', argument + '.SZ', argument + '.BJ']
                history = history[history['symbol'].isin(possible_complete_symbols)]
            else:
                # if argument is not a symbol, use the first available symbol in order details
                history = history[history['symbol'] == history['symbol'].iloc[0]]

        # remove rows whose value in column 'filled_qty' is 0, and sort by 'filled_time'
        history = history[history['filled_qty'] != 0]
        history.sort_values(by='execution_time', inplace=True)
        # change the quantity to negative if it is a sell-out
        history['filled_qty'] = np.where(history['direction'] == 'sell',
                                         -history['filled_qty'],
                                         history['filled_qty'])
        # calculate rows: cum_qty, trade_cost, cum_cost, value, share_cost, earnings, and earning rate
        history['cum_qty'] = history.groupby('symbol')['filled_qty'].cumsum()
        history['trade_cost'] = history['filled_qty'] * history['price_filled'] + history['transaction_fee']
        history['cum_cost'] = history.groupby('symbol')['trade_cost'].cumsum()
        history['value'] = history['cum_qty'] * history['price_filled']
        history['share_cost'] = history['cum_cost'] / history['cum_qty']
        history['earnings'] = history['value'] - history['cum_cost']
        history['earning_rate'] = history['earnings'] / history['cum_cost']
        # add row: name
        all_names = get_symbol_names(datasource=self.trader.datasource, symbols=history['symbol'].tolist())
        history['name'] = [adjust_string_length(name, 8, hans_aware=True, padding='left') for name in all_names]

        # display history with to_string method with 2 digits precision for all numbers and 3 digits percentage
        # for earning rate
        # Error will be raised if execution_time is NaT. will print out normal format in this case
        if np.any(pd.isna(history.execution_time)):
            history.execution_time = history.execution_time.fillna(pd.to_datetime('1970-01-01'))
        # else:
        # print(history)
        rprint(
                history.to_string(
                        columns=['execution_time', 'symbol', 'direction', 'filled_qty', 'price_filled',
                                 'transaction_fee', 'cum_qty', 'value', 'share_cost', 'earnings', 'earning_rate',
                                 'name'],
                        header=['time', 'symbol', 'oper', 'qty', 'price',
                                'trade_fee', 'holdings', 'holding value', 'cost', 'earnings', 'earning_rate',
                                'name'],
                        formatters={
                            'execution_time': lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x, unit="D")),
                            'name':         '{:8s}'.format,
                            'operation':    '{:s}'.format,
                            'filled_qty':   '{:,.2f}'.format,
                            'price_filled': '¥{:,.2f}'.format,
                            'transaction_fee': '¥{:,.2f}'.format,
                            'cum_qty':      '{:,.2f}'.format,
                            'value':        '¥{:,.2f}'.format,
                            'share_cost':   '¥{:,.2f}'.format,
                            'earnings':     '¥{:,.2f}'.format,
                            'earning_rate': '{:.3%}'.format,
                        },
                        col_space={
                            'name': 8,
                            'price_filled': 10,
                            'value': 12,
                            'share_cost': 10,
                            'earnings': 12,
                        },
                        justify='right',
                        index=False,
                )
        )

    def do_orders(self, arg):
        """ Get trader orders

        Get trader orders, use arg to specify orders to get, default is today's orders

        Usage:
        ------
        orders --today|-t [--filled|-f] [--canceled|-c] [--partial-filled|-p] [--last_hour|-l|-h] [--yesterday|-y]
        [--3day|-3] [--week|-w] [--month|-m] [--buy|-b] [--sell|-s] [--long|-lg] [--short|-sh] [symbol like '000001.SZ']

        Examples:
        ---------
        (QTEASY): orders
        - display all orders of today
        (QTEASY): orders 000001
        - display all orders of stock 000001
        (QTEASY): orders --filled --today 000001
        - display all filled orders of stock 000001 executed today
        """

        from rich import print as rprint
        args = parse_shell_argument(arg, default='--today', command_name='orders')
        order_details = self._trader.history_orders()

        for argument in args:
            from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
            # select orders by time range arguments like 'last_hour', 'today', '3day', 'week', 'month'
            if argument in ['--last_hour', '-l', '-h', '--today', '-t', '--yesterday', '-y',
                            '--3day', '-3', '--week', '-w', '--month', '-m']:
                # create order time ranges
                end = self.trader.get_current_tz_datetime()  # 产生本地时区时间
                if argument in ['--last_hour', '-l']:
                    start = pd.to_datetime(end) - pd.Timedelta(hours=1)
                elif argument in ['--today', '-t']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=1)
                    start = start.strftime("%Y-%m-%d 23:59:59")
                elif argument in ['--yesterday', '-y']:
                    yesterday = pd.to_datetime(end) - pd.Timedelta(days=1)
                    start = yesterday.strftime("%Y-%m-%d 00:00:00")
                    end = yesterday.strftime("%Y-%m-%d 23:59:59")
                elif argument in ['--3day', '-3']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=3)
                    start = start.strftime("%Y-%m-%d 23:59:59")
                elif argument in ['--week', '-w']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=7)
                    start = start.strftime("%Y-%m-%d 23:59:59")
                elif argument in ['--month', '-m']:
                    start = pd.to_datetime(end) - pd.Timedelta(days=30)
                    start = start.strftime("%Y-%m-%d 23:59:59")
                else:
                    start = pd.to_datetime(end) - pd.Timedelta(days=1)
                    start = start.strftime("%Y-%m-%d 23:59:59")

                # select orders by time range
                order_details = order_details[(order_details['submitted_time'] >= start) &
                                              (order_details['submitted_time'] <= end)]
            # select orders by status arguments like 'filled', 'canceled', 'partial-filled'
            elif argument in ['--filled', '-f', '--canceled', '-c', '--partial-filled', '-p']:
                if argument in ['--filled', '-f']:
                    order_details = order_details[order_details['status'] == 'filled']
                elif argument in ['--canceled', '-c']:
                    order_details = order_details[order_details['status'] == 'canceled']
                elif argument in ['--partial-filled', '-p']:
                    order_details = order_details[order_details['status'] == 'partial-filled']
            # select orders by order side arguments like 'long', 'short'
            elif argument in ['--long', '-lg', '--short', '-sh']:
                if argument in ['--long', '-lg']:
                    order_details = order_details[order_details['position'] == 'long']
                elif argument in ['--short', '-sh']:
                    order_details = order_details[order_details['position'] == 'short']
            # select orders by order side arguments like 'buy', 'sell'
            elif argument in ['--buy', '-b', '--sell', '-s']:
                if argument in ['--buy', '-b']:
                    order_details = order_details[order_details['direction'] == 'buy']
                elif argument in ['--sell', '-s']:
                    order_details = order_details[order_details['direction'] == 'sell']
            # select orders by order symbol arguments like '000001.SZ'
            elif is_complete_cn_stock_symbol_like(argument.upper()):
                order_details = order_details[order_details['symbol'] == argument.upper()]
            # select orders by order symbol arguments like '000001'
            elif is_cn_stock_symbol_like(argument):
                possible_complete_symbols = [argument + '.SH', argument + '.SZ', argument + '.BJ']
                order_details = order_details[order_details['symbol'].isin(possible_complete_symbols)]
            else:
                print(f'"{argument}" invalid: Please input a valid symbol to get order details.')
                return

        if order_details.empty:
            rprint(f'No orders found with argument ({args}). try other arguments.')
        else:
            symbols = order_details['symbol'].tolist()
            names = get_symbol_names(datasource=self.trader.datasource, symbols=symbols)
            order_details['name'] = names
            # if NaT in order_details, then strftime will not work, will print out original form of order_details
            if np.any(pd.isna(order_details.execution_time)) or np.any(pd.isna(order_details.submitted_time)):
                print(order_details)
            else:
                rprint(order_details.to_string(
                        index=False,
                        columns=['execution_time', 'symbol', 'position', 'direction', 'qty', 'price_quoted',
                                 'submitted_time', 'status', 'price_filled', 'filled_qty', 'canceled_qty',
                                 'delivery_status', 'name'],
                        header=['time', 'symbol', 'pos', 'buy/sell', 'qty', 'price',
                                'submitted', 'status', 'fill_price', 'fill_qty', 'canceled',
                                'delivery', 'name'],
                        formatters={'name':           '{:s}'.format,
                                    'qty':            '{:,.2f}'.format,
                                    'price_quoted':   '¥{:,.2f}'.format,
                                    'price_filled':   '¥{:,.2f}'.format,
                                    'filled_qty':     '{:,.2f}'.format,
                                    'canceled_qty':   '{:,.2f}'.format,
                                    'execution_time': lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x, unit="D")),
                                    'submitted_time': lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x, unit="D"))
                                    },
                        col_space={
                            'price_quoted': 10,
                            'price_filled': 10,
                            'filled_qty': 10,
                            'canceled_qty': 10,
                        },
                        justify='right',
                ))

    def do_change(self, arg):
        """ Change trader cash and positions
        to change cash, amount must be given
        to change a position, amount and symbol must be given, price is used to update cost,
        if not given, current price will be used, side is used to specify long or short side,
        if not given, long side will be used

        Usage:
        ------
        change symbol amount price [--long|-l|--short|-s]
        change [--cash|-c amount]

        Examples:
        ---------
        change 000001.SZ 1000 10.5:
            add 1000 shares of 000001.SZ to trader account with price 10.5 on long side (default)
        change --cash/-c 1000000:
            add 1000000 cash to trader account
        """

        args = parse_shell_argument(arg, command_name='change')
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like, is_number_like

        if not args:
            print('Please input valid arguments.')
            return

        if args[0] in ['--cash', '-c']:
            # change cash
            if len(args) < 2:
                print('Please input cash value to increase (+) or to decrease (-).')
                return
            try:
                amount = float(args[1])
            except ValueError:
                print('Please input cash value to increase (+) or to decrease (-).')
                return

            self.trader._change_cash(amount)
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
            last_available_data = self.trader.datasource.get_history_data(
                    shares=[symbol],
                    htypes='close',
                    asset_type=self.trader.asset_type,
                    freq=freq,
                    row_count=10,
            )
            current_price = last_available_data['close'][symbol][-1]
        except Exception as e:
            print(f'Error: {e}, latest available data can not be downloaded. 10.00 will be used as current price.')
            import traceback
            traceback.print_exc()
            current_price = 10.00
        if len(args) == 2:
            # 只给出两个参数，默认使用最新价格、side为已有的非零持仓
            price = current_price
            side = None
        elif (len(args) == 3) and (args[2] in ['--long', '--short', '-l', '-s']):
            # 只给出side参数，默认使用最新价格
            price = current_price
            side = 'long' if args[2] in ['--long', '-l'] else 'short'
        elif (len(args) == 3) and (is_number_like(args[2])):
            # 只给出price参数，默认使用已有的非零持仓side
            price = float(args[2])
            side = None
        elif (len(args) == 4) and (is_number_like(args[2])) and (args[3] in ['--long', '--short', '-l', '-s']):
            # 既给出了价格，又给出了side
            price = float(args[2])
            side = 'long' if args[3] in ['--long', '-l'] else 'short'
        elif (len(args) == 4) and (is_number_like(args[3])) and (args[2] in ['--long', '--short', '-l', '-s']):
            # 既给出了价格，又给出了side
            price = float(args[3])
            side = 'long' if args[2] in ['--long', '-l'] else 'short'
        else:  # not a valid input
            print(f'{args} is not a valid input, Please input valid arguments.')
            return

        self._trader._change_position(
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
        if arg:
            print('dashboard command does not accept arguments.')
            return False
        if not self.trader.debug:
            import os
            # check os type of current system, and then clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
        self._status = 'dashboard'
        print('\nWelcome to TraderShell! currently in dashboard mode, live status will be displayed here.\n'
              'You can not input commands in this mode, if you want to enter interactive mode, please'
              'press "Ctrl+C" to exit dashboard mode and select from prompted options.\n')
        return True

    def do_strategies(self, arg: str):
        """ Show strategies information or set parameters for a strategy

        Usage:
        ------
        strategies [--detail|-d] [--set-par|-s strategy_id pars]

        Examples:
        ---------
        to display strategies information:
        (QTEASY): strategies
        to display strategies information in detail:
        (QTEASY): strategies --detail
        to set parameters for strategy "stg":
        (QTEASY): strategies --set-par stg (1, 2, 3)
        to set blender of strategies:
        (QTEASY): strategies --blender <blender> (not implemented yet)

        """
        # TODO: to change blender of strategies, use strategies blender|b <blender>
        args = parse_shell_argument(arg, command_name='strategies')
        if not args:
            self.trader.operator.info()
        elif args[0] in ['-d', '--detail']:
            self.trader.operator.info(verbose=True)
        elif args[0] in ['-s', '--set-par']:
            if len(args) < 3:
                print('To set up variable parameter of a strategy, input a valid strategy id and a parameter:\n'
                      'For Example, to set (1, 2, 3) as the parameter of strategy "custom", use:\n'
                      '(QTEASY): strategies -s custom (1, 2, 3)')
                return
            strategy_id = args[1]
            pars = args[2:]
            try:
                new_pars = eval(','.join(pars))
            except Exception as e:
                print(f'Invalid parameter ({",".join(pars)})! Error: {e}')
                if self.trader.debug:
                    import traceback
                    traceback.print_exc()
                return
            if not isinstance(new_pars, tuple):
                print(f'Invalid parameter ({new_pars})! Parameter should be a tuple')
            if not isinstance(new_pars, tuple):
                print(f'Invalid parameter ({new_pars})! Please input a valid parameter.')
                return
            try:
                self.trader.operator.set_parameter(stg_id=strategy_id, pars=new_pars)
            except Exception as e:
                print(f'Can not set {new_pars} to {strategy_id}, Error: {e}')
                self.trader.operator.info()
                if self.trader.debug:
                    import traceback
                    traceback.print_exc()
                return
            print(f'Parameter {new_pars} has been set to strategy {strategy_id}.')
            self.trader.operator.info()
        elif args[0] in ['-b', '--blender']:
            print(f'Not implemented yet.')

    def do_schedule(self, arg):
        """ Show current strategy task schedule

        Usage:
        ------
        schedule
        """
        if arg:
            print('schedule command does not accept arguments.')
            return
        print(f'Execution Schedule:')
        self.trader.show_schedule()

    def do_run(self, arg: str):
        """ To force run a strategy or a task in current setup, only available in DEBUG mode.
        strategy id can be found in strategies command.

        Usage:
        ------
        run stg1 [stg2] [stg3] ...
        run --task|-t task_name [[arg1] [arg2] ...]
        """
        if not self.trader.debug:
            print('Running strategy manually is only available in DEBUG mode')
            return
        argument = str_to_list(arg, sep_char=' ')
        if not isinstance(argument, list):
            print('Invalid argument, use "strategies" to view all strategy ids.\n'
                  'Use: run stg1 [stg2] [stg3] ... to run one or more strategies')
            return
        if not argument:
            print('A valid strategy id must be given, use "strategies" to view all ids.\n'
                  'Use: run stg1 [stg2] [stg3] ... to run one or more strategies')
            return
        if not argument[0] in ['--task', '-t']:  # run strategies
            all_strategy_ids = self.trader.operator.strategy_ids
            if not all([strategy in all_strategy_ids for strategy in argument]):
                invalid_stg = [stg for stg in argument if stg not in all_strategy_ids]
                print(f'Invalid strategy id: {invalid_stg}, use "strategies" to view all valid strategy ids.')
                return

            current_trader_status = self.trader.status
            current_broker_status = self.trader.broker.status

            self.trader.status = 'running'
            self.trader.broker.status = 'running'

            try:
                self.trader.run_task('run_strategy', argument, run_in_main_thread=True)
            except Exception as e:
                import traceback
                print(f'Error in running strategy: {e}')
                print(traceback.format_exc())

            self.trader.status = current_trader_status
            self.trader.broker.status = current_broker_status
        else:  # run tasks
            if len(argument) == 1:
                print('Please input a valid task name.')
                return
            task_name = argument[1]
            try:
                self.trader.run_task(task_name, run_in_main_thread=True)
            except Exception as e:
                import traceback
                print(f'Error in running task: {e}')
                print(traceback.format_exc())

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

        prev_message = ''
        live_price_refresh_timer = 0
        while True:
            # enter shell loop
            try:
                if self.status == 'stopped':
                    # if trader is stopped, shell will exit
                    break
                if self.status == 'dashboard':
                    # check trader message queue and display messages
                    watched_price_refresh_interval = self.trader.get_config(
                            'watched_price_refresh_interval')['watched_price_refresh_interval']
                    if not self._trader.message_queue.empty():
                        text_width = int(shutil.get_terminal_size().columns)
                        # adjust message length
                        message = self._trader.message_queue.get()
                        if message[-2:] == '_R':
                            # 如果读取到覆盖型信息，则逐次读取所有的覆盖型信息，并显示最后一条和下一条常规信息
                            next_normal_message = None
                            while True:
                                if self._trader.message_queue.empty():
                                    break
                                next_message = self._trader.message_queue.get()
                                if message[-2:] != '_R':
                                    next_normal_message = next_message
                                    break
                                message = next_message

                            message = message[:-2] + ' ' + self._watched_prices
                            message = adjust_string_length(message,
                                                           text_width - 2,
                                                           hans_aware=True,
                                                           format_tags=True)
                            message = f'{message: <{text_width - 2}}'
                            rprint(message, end='\r')
                            if next_normal_message:
                                rprint(message)
                        else:
                            # 在前一条信息为覆盖型信息时，在信息前插入"\n"使常规信息在下一行显示
                            if prev_message[-2:] == '_R':
                                print('\n', end='')
                            message = adjust_string_length(message,
                                                           text_width - 2,
                                                           hans_aware=True,
                                                           format_tags=True)
                            rprint(message)
                        prev_message = message
                    # check if live price refresh timer is up, if yes, refresh live prices
                    live_price_refresh_timer += 0.05
                    if live_price_refresh_timer > watched_price_refresh_interval:
                        # 在一个新的进程中读取实时价格, 收盘后不获取
                        if self.trader.is_market_open:
                            from threading import Thread
                            t = Thread(target=self.update_watched_prices, daemon=True)
                            t.start()
                            # if self.trader.debug:
                                # self.trader.send_message(f'Acquiring watched prices in a new thread<{t.name}>')
                        live_price_refresh_timer = 0
                elif self.status == 'command':
                    # get user command input and do commands
                    sys.stdout.write('will enter interactive mode.\n')
                    if not self.trader.debug:
                        import os
                        # check os type of current system, and then clear screen
                        os.system('cls' if os.name == 'nt' else 'clear')
                    # check if data source is connected here, if not, reconnect before entering interactive mode
                    self.trader.datasource.reconnect()
                    self.trader.datasource.reconnect()
                    self.cmdloop()
                else:
                    sys.stdout.write('status error, shell will exit, trader and broker will be shut down\n')
                    self.do_bye('')
                time.sleep(0.05)
            except KeyboardInterrupt:
                # ask user if he/she wants to: [1], command mode; [2], stop trader; [3 or other], resume dashboard mode
                t = Timer(5, lambda: print(
                        "\nNo input in 5 seconds, press Enter to continue current mode. "))
                t.start()
                option = input('\nCurrent mode interrupted, Input 1 or 2 or 3 for below options: \n'
                               '[1], Enter command mode; \n'
                               '[2], Enter dashboard mode. \n'
                               '[3], Exit and stop the trader; \n'
                               'please input your choice: ')
                if option == '1':
                    self._status = 'command'
                elif option == '2':
                    self.do_dashboard('')
                elif option == '3':
                    self.do_bye('')
                else:
                    continue
                t.cancel()
                continue
            # looks like finally block is better than except block here
            except Exception as e:
                self.stdout.write(f'Unexpected Error: {e}\n')
                import traceback
                traceback.print_exc()
                self.do_bye('')

        sys.stdout.write('Thank you for using qteasy!\n')
        self.do_bye('')


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
        # default_config = ConfigDict(
        #         {
        #                 'exchange':                         'SSE',
        #                 'market_close_day_loop_interval':   0,
        #                 'market_open_day_loop_interval':    0,
        #         }
        # )

        self.account_id = account_id
        self._broker = broker
        self._operator = operator
        self._config = ConfigDict()
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

        self.task_daily_schedule = []
        self.time_zone = config['time_zone']
        self.init_datetime = self.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")

        self.is_trade_day = False
        self.is_market_open = False
        self._status = 'stopped'
        self._prev_status = None

        self.live_price_channel = self._config['live_price_acquire_channel']
        self.live_price_freq = self._config['live_price_acquire_freq']
        self.live_price = None  # 用于存储本交易日最新的实时价格，用于跟踪最新价格、计算市值盈亏等

        self.account = get_account(self.account_id, data_source=self._datasource)

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
    def account_positions(self):
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
    def non_zero_positions(self):
        """ 账户当前的持仓，一个tuple，当前持有非零的股票仓位symbol，持有数量和可用数量 """
        positions = self.account_positions
        return positions.loc[positions['qty'] != 0]

    @property
    def account_position_info(self):
        """ 账户当前的持仓，一个tuple，当前持有的股票仓位symbol，名称，持有数量、可用数量，以及当前价格、成本和市值 """
        positions = self.account_positions

        # 获取每个symbol的最新价格，在交易日从self.live_price中获取，非交易日从datasource中获取，或者使用全nan填充，
        if self.live_price is None:
            today = self.get_current_tz_datetime()
            try:
                current_prices = self._datasource.get_history_data(
                        shares=positions.index.tolist(),
                        htypes='close',
                        asset_type='E',
                        freq=self.operator.op_data_freq,
                        start=today - pd.Timedelta(days=7),
                        end=today,
                )['close'].iloc[-1]
            except Exception as e:
                if self.debug:
                    self.send_message(f'Error in getting current prices: {e}')
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
    def datasource(self):
        return self._datasource

    # ================== methods ==================
    def get_current_tz_datetime(self):
        """ 根据当前时区获取当前时间，如果指定时区等于当前时区，将当前时区设置为local，返回当前时间"""

        tz_time = get_current_tz_datetime(self.time_zone)
        # if tz_time is very close to local time, then set time_zone to local and return local time
        if abs(tz_time - pd.to_datetime('today')) < pd.Timedelta(seconds=1):
            self.time_zone = 'local'
        # else return tz_time
        return tz_time

    def get_config(self, key=None):
        """ 返回交易系统的配置信息 如果给出了key，返回一个仅包含key:value的dict，否则返回完整的config字典"""
        if key is not None:
            return {key: self._config.get(key)}
        else:
            return self._config

    def update_config(self, key=None, value=None):
        """ 更新交易系统的配置信息 """
        if key not in self._config:
            return None
        from qteasy._arg_validators import _update_config_kwargs
        new_kwarg = {key: value}
        _update_config_kwargs(self._config, new_kwarg, raise_if_key_not_existed=True)
        return self._config[key]

    def show_schedule(self):
        """ 显示当前的任务日程 """
        schedule = pd.DataFrame(
                self.task_daily_schedule,
                columns=['datetime', 'task', 'parameters'],
        )
        schedule.set_index(keys='datetime', inplace=True)
        from rich import print as rprint
        schedule_string = schedule.to_string()
        schedule_string = schedule_string.replace('[', '<')
        schedule_string = schedule_string.replace(']', '>')
        rprint(schedule_string)

    def register_broker(self, debug=False, **kwargs):
        """ 注册broker，以便实现登录等处理
        """
        self.broker.register(debug=debug, **kwargs)

    def run(self):
        """ 交易系统的main loop：

        1，检查task_queue中是否有任务，如果有任务，则提取任务，根据当前status确定是否执行任务，如果可以执行，则执行任务，否则忽略任务
        2，如果当前是交易日，检查当前时间是否在task_daily_agenda中，如果在，则将任务添加到task_queue中
        3，如果当前是交易日，检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
        """
        self.status = 'sleeping'
        self._check_trade_day()
        self._initialize_schedule()
        self.send_message(f'Trader is running with account_id: {self.account_id}\n'
                          f'Started on date / time: '
                          f'{self.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")}\n'
                          f'current day is trade day: {self.is_trade_day}\n'
                          f'running agenda: {self.task_daily_schedule}')
        market_open_day_loop_interval = 0.05
        market_close_day_loop_interval = 1
        current_date_time = self.get_current_tz_datetime()  # 产生当地时间
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
                            self.send_message(f'tuple task: {task} is taken from task queue, task[0]: {task[0]}'
                                              f'task[1]: {task[1]}')
                        task_name = task[0]
                        args = task[1]
                    else:
                        task_name = task
                        args = None
                    if self.debug:
                        self.send_message(f'task queue is not empty, taking next task from queue: {task_name}')
                    if task_name not in white_listed_tasks:
                        if self.debug:
                            self.send_message(f'task: {task} cannot be executed in current status: {self.status}')
                        self.task_queue.task_done()
                        continue
                    try:
                        if args:
                            self.run_task(task_name, args)
                        else:
                            self.run_task(task_name)
                    except Exception as e:
                        self.send_message(f'error occurred when executing task: {task_name}, error: {e}')
                        if self.debug:
                            import traceback
                            traceback.print_exc()
                    self.task_queue.task_done()

                # 如果没有暂停，从任务日程中添加任务到任务队列
                current_date_time = self.get_current_tz_datetime()  # 产生本地时间
                current_time = current_date_time.time()
                current_date = current_date_time.date()
                if self.status != 'paused':
                    self._add_task_from_agenda(current_time)
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
                self.send_message('Trader completed and exited.')
        except KeyboardInterrupt:
            self.send_message('KeyboardInterrupt, stopping trader...')
            self.run_task('stop')
        except Exception as e:
            self.send_message(f'error occurred when running trader, error: {e}')
            if self.debug:
                import traceback
                traceback.print_exc()
        return

    def info(self, verbose=False, width=80):
        """ 打印账户的概览，包括账户基本信息，持有现金和持仓信息

        Parameters:
        -----------
        verbose: bool, default False
            是否打印详细信息(系统信息、账户信息、交易状态信息等)，如否，则只打印账户持仓等基本信息
        width: int, default 80
            打印信息的宽度

        Returns:
        --------
        None
        """

        from rich import print as rprint

        semi_width = int(width * 0.75)
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
        if verbose:
            # System Info
            rprint(f'{" System Info ":=^{width}}')
            rprint(f'{"python":<{semi_width - 20}}{sys.version}')
            rprint(f'{"qteasy":<{semi_width - 20}}{qteasy.__version__}')
            import tushare
            rprint(f'{"tushare":<{semi_width - 20}}{tushare.__version__}')
            try:
                import talib
                rprint(f'{"ta-lib":<{semi_width - 20}}{talib.__version__}')
            except ImportError:
                rprint(f'{"ta-lib":<{semi_width - 20}}not installed')
            rprint(f'{"Local DataSource":<{semi_width - 20}}{self.datasource}')
            rprint(f'{"System log file path":<{semi_width - 20}}'
                   f'{self.get_config("sys_log_file_path")["sys_log_file_path"]}')
            rprint(f'{"Trade log file path":<{semi_width - 20}}'
                   f'{self.get_config("trade_log_file_path")["trade_log_file_path"]}')
            # Account information
            rprint(f'{" Account Overview ":=^{width}}')
            rprint(f'{"Account ID":<{semi_width - 20}}{self.account_id}')
            rprint(f'{"User Name":<{semi_width - 20}}{self.account["user_name"]}')
            rprint(f'{"Created on":<{semi_width - 20}}{self.account["created_time"]}')
            rprint(f'{"Started on":<{semi_width - 20}}{self.init_datetime}')
            rprint(f'{"Time zone":<{semi_width - 20}}{self.get_config("time_zone")["time_zone"]}')
            # Status and Settings
            rprint(f'{" Status and Settings ":=^{width}}')
            rprint(f'{"Trader Stats":<{semi_width - 20}}{self.status}')
            rprint(f'{"Broker Status":<{semi_width - 20}}{self.broker.broker_name} / {self.broker.status}')
            rprint(f'{"Live price update freq":<{semi_width - 20}}'
                   f'{self.get_config("live_price_acquire_freq")["live_price_acquire_freq"]}')
            rprint(f'{"Strategy":<{semi_width - 20}}{self.operator.strategies}')
            rprint(f'{"Strategy run frequency":<{semi_width - 20}}{self.operator.op_data_freq}')
            rprint(f'{"Trade batch size(buy/sell)":<{semi_width - 20}}'
                   f'{self.get_config("trade_batch_size")["trade_batch_size"]} '
                   f'/ {self.get_config("sell_batch_size")["sell_batch_size"]}')
            rprint(f'{"Delivery Rule (cash/asset)":<{semi_width - 20}}'
                   f'{self.get_config("cash_delivery_period")["cash_delivery_period"]} day / '
                   f'{self.get_config("stock_delivery_period")["stock_delivery_period"]} day')
            buy_fix = float(self.get_config('cost_fixed_buy')['cost_fixed_buy'])
            sell_fix = float(self.get_config('cost_fixed_sell')['cost_fixed_sell'])
            buy_rate = float(self.get_config('cost_rate_buy')['cost_rate_buy'])
            sell_rate = float(self.get_config('cost_rate_sell')['cost_rate_sell'])
            buy_min = float(self.get_config('cost_min_buy')['cost_min_buy'])
            sell_min = float(self.get_config('cost_min_sell')['cost_min_sell'])
            if (buy_fix > 0) or (sell_fix > 0):
                rprint(f'{"Trade cost - fixed (B/S)":<{semi_width - 20}}¥ {buy_fix:.3f} / ¥ {sell_fix:.3f}')
            if (buy_rate > 0) or (sell_rate > 0):
                rprint(f'{"Trade cost - rate (B/S)":<{semi_width - 20}}{buy_rate:.3%} / {sell_rate:.3%}')
            if (buy_min > 0) or (sell_min > 0):
                rprint(f'{"Trade cost - minimum (B/S)":<{semi_width - 20}}¥ {buy_min:.3f} / ¥ {sell_min:.3f}')
            rprint(f'{"Market time (open/close)":<{semi_width - 20}}'
                   f'{self.get_config("market_open_time_am")["market_open_time_am"]} / '
                   f'{self.get_config("market_close_time_pm")["market_close_time_pm"]}')
        # Investment Return
        print(f'{" Returns ":=^{semi_width}}')
        rprint(f'{"Benchmark":<{semi_width - 20}}¥ '
               f'{self.get_config("benchmark_asset")["benchmark_asset"]}')
        rprint(f'{"Total Investment":<{semi_width - 20}}¥ {total_investment:,.2f}')
        if total_value >= total_investment:
            rprint(f'{"Total Value":<{semi_width - 20}}¥[bold red] {total_value:,.2f}[/bold red]')
            rprint(f'{"Total Return of Investment":<{semi_width - 20}}'
                   f'¥[bold red] {total_return_of_investment:,.2f}[/bold red]\n'
                   f'{"Total ROI Rate":<{semi_width - 20}}  [bold red]{total_roi_rate:.2%}[/bold red]')
        else:
            rprint(f'{"Total Value":<{semi_width - 20}}¥[bold green] {total_value:,.2f}[/bold green]')
            rprint(f'{"Total Return of Investment":<{semi_width - 20}}'
                   f'¥[bold green] {total_return_of_investment:,.2f}[/bold green]\n'
                   f'{"Total ROI Rate":<{semi_width - 20}}  [bold green]{total_roi_rate:.2%}[/bold green]')
        print(f'{" Cash ":=^{semi_width}}')
        rprint(f'{"Cash Percent":<{semi_width - 20}}  {own_cash / total_value:.2%} ')
        rprint(f'{"Total Cash":<{semi_width - 20}}¥ {own_cash:,.2f} ')
        rprint(f'{"Available Cash":<{semi_width - 20}}¥ {available_cash:,.2f}')
        print(f'{" Stock Value ":=^{semi_width}}')
        rprint(f'{"Stock Percent":<{semi_width - 20}}  {position_level:.2%}')
        if total_profit >= 0:
            rprint(f'{"Total Stock Value":<{semi_width - 20}}¥[bold red] {total_market_value:,.2f}[/bold red]')
            rprint(f'{"Total Stock Profit":<{semi_width - 20}}¥[bold red] {total_profit:,.2f}[/bold red]')
            rprint(f'{"Stock Profit Ratio":<{semi_width - 20}}  [bold red]{total_profit_ratio:.2%}[/bold red]')
        else:
            rprint(f'{"Total Stock Value":<{semi_width - 20}}¥[bold green] {total_market_value:,.2f}[/bold green]')
            rprint(f'{"Total Stock Profit":<{semi_width - 20}}¥[bold green] {total_profit:,.2f}[/bold green]')
            rprint(f'{"Total Profit Ratio":<{semi_width - 20}}  [bold green]{total_profit_ratio:.2%}[/bold green]')
        asset_in_pool= len(self.asset_pool)
        asset_pool_string = adjust_string_length(
                s=' '.join(self.asset_pool),
                n=width - 2,
        )
        if verbose:
            print(f'{" Investment ":=^{width}}')
            rprint(f'Current Investment Type:        {self.asset_type}')
            rprint(f'Current Investment Pool:        {asset_in_pool} stocks, Use "pool" command to view details.\n'
                   f'=={asset_pool_string}\n')
        return None

    def trade_results(self, status='filled'):
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

    def send_message(self, message: str, new_line=True):
        """ 发送消息到消息队列, 在消息前添加必要的信息如日期、时间等

        Parameters
        ----------
        message: str
            消息内容
        new_line: bool, default True
            是否在消息后添加换行符
        """
        time_string = self.get_current_tz_datetime().strftime("%b%d %H:%M:%S")  # 本地时间
        if self.time_zone != 'local':
            tz = f"({self.time_zone.split('/')[-1]})"
        else:
            tz = ''
        message = f'<{time_string}{tz}>{self.status}: {message}'
        if not new_line:
            message += '_R'
        if self.debug:
            message = f'<DEBUG>{message}'
        if self.debug and (message[-2:] != '_R'):
            text_width = int(shutil.get_terminal_size().columns)
            print(f'{message: <{text_width - 2}}')  # 如果在debug模式下且不是覆盖型信息，直接打印
        else:
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

        if kwargs:
            task = (task, kwargs)
        if self.debug:
            self.send_message(f'adding task: {task}')
        self._add_task_to_queue(task)

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
        return order_result_details

    # ============ definition of tasks ================
    def _start(self):
        """ 启动交易系统 """
        self.send_message('starting Trader')
        self.status = 'sleeping'

    def _stop(self):
        """ 停止交易系统 """
        self.send_message('stopping Trader, the broker will be stopped as well...')
        self._broker.status = 'stopped'
        self.status = 'stopped'

    def _sleep(self):
        """ 休眠交易系统 """
        self.send_message('[bold red]Putting Trader to sleep[/bold red]')
        self.status = 'sleeping'
        self.broker.status = 'paused'

    def _wakeup(self):
        """ 唤醒交易系统 """
        self.status = 'running'
        self.broker.status = 'running'
        self.send_message('[bold red]Trader is awake, broker is running[/bold red]')

    def _pause(self):
        """ 暂停交易系统 """
        self.status = 'paused'
        self.send_message('[bold red]Trader is Paused, broker is still running[/bold red]')

    def _resume(self):
        """ 恢复交易系统 """
        self.status = self.prev_status
        self.send_message(f'[bold red]Trader is resumed to previous status({self.status})[/bold red]')

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

        # TODO: 这里应该可以允许用户输入blender，从而灵活地测试不同交易策略的组合和混合方式
        if self.debug:
            self.send_message(f'running task run strategy: {strategy_ids}')
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
        if self.debug:
            self.send_message(f'getting live price data for strategy run...')
        # # 将类似于'2H'或'15min'的时间频率转化为两个变量：duration和unit (duration=2, unit='H')/ (duration=15, unit='min')
        duration, unit, _ = parse_freq_string(max_strategy_freq, std_freq_only=False)
        if (unit.lower() in ['min', '5min', '10min', '15min', '30min', 'h']) and self.is_trade_day:
            # 如果strategy_run的运行频率为分钟或小时，则调用fetch_realtime_price_data方法获取分钟级别的实时数据
            table_to_update = UNIT_TO_TABLE[unit.lower()]
            real_time_data = self._datasource.fetch_realtime_price_data(
                    table=table_to_update,
                    channel=config['live_price_acquire_channel'],
                    symbols=self.asset_pool,
            )

            # 将real_time_data写入DataSource
            # 在real_time_data中数据的trade_time列中增加日期并写入DataSource，但是只在交易日这么做，否则会出现日期错误
            real_time_data['trade_time'] = real_time_data['trade_time'].apply(
                    lambda x: pd.to_datetime(x)
            )
            # 将实时数据写入数据库 (仅在交易日这么做)
            rows_written = self._datasource.update_table_data(
                    table=table_to_update,
                    df=real_time_data,
                    merge_type='update',
            )

        # 如果strategy_run的运行频率大于等于D，则不下载实时数据，使用datasource中的历史数据
        else:
            pass
        # 读取最新数据,设置operator的数据分配,创建trade_data
        if self.debug:
            self.send_message(f'preparing trade data...')
        hist_op, hist_ref = check_and_prepare_live_trade_data(
                operator=operator,
                config=config,
                datasource=self._datasource,
                live_prices=self.live_price,
        )
        if self.debug:
            self.send_message(f'read real time data and set operator data allocation')
        operator.assign_hist_data(
                hist_data=hist_op,
                reference_data=hist_ref,
                live_mode=True,
                live_running_stgs=strategy_ids
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
        if self.debug:
            self.send_message(f'Generating trade data from position availabilities...')
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
        if self.debug:
            self.send_message(f'ran strategy and created signal: {op_signal}')

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
        if self.debug:
            self.send_message(f'generated trade signals:\n'
                              f'symbols: {symbols}\n'
                              f'positions: {positions}\n'
                              f'directions: {directions}\n'
                              f'quantities: {quantities}\n'
                              f'current_prices: {quoted_prices}\n')
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
                # format the message depending on buy/sell orders
                if d == 'buy':  # red for buy
                    self.send_message(f'<NEW ORDER {order_id}>: <{name}-{sym}> [bold red]{d}-{pos} '
                                      f'{qty} shares @ ¥{price}[/bold red]')
                else:  # green for sell
                    self.send_message(f'<NEW ORDER {order_id}>: <{name}-{sym}> [bold green]{d}-{pos} '
                                      f'{qty} shares @ ¥{price}[/bold green]')
                # 记录已提交的交易数量
                submitted_qty += 1

        self.send_message(f'<RAN STRATEGY {tuple(strategy_ids)}>: {submitted_qty} orders submitted in total.')

        return submitted_qty

    def _process_result(self, result):
        """ 从result_queue中读取并处理交易结果

        1，处理交易结果，更新账户和持仓信息
        2，处理交易结果的交割，记录交割结果（未达到交割条件的交易结果不会被处理）
        4，生成交易结果信息推送到信息队列
        """

        if self.debug:
            self.send_message(f'running task process_result, got result: \n{result}')

        from qteasy.trade_recording import read_trade_result_by_id, read_trade_order_detail, get_position_by_id
        from qteasy.trade_recording import get_account
        # 读取交易处理以前的账户信息和持仓信息
        order_id = result['order_id']
        order_detail = read_trade_order_detail(order_id, data_source=self._datasource)
        # 读取持仓信息
        pos_id = order_detail['pos_id']
        position = get_position_by_id(pos_id, data_source=self._datasource)
        pre_qty, pre_available, pre_cost = position['qty'], position['available_qty'], position['cost']
        # 读取持有现金
        account = get_account(self.account_id, data_source=self._datasource)
        pre_cash_amount = account['cash_amount']
        pre_available_cash = account['available_cash']

        # 交易结果处理, 更新账户和持仓信息, 如果交易结果导致错误，不会更新账户和持仓信息
        try:
            result_id = process_trade_result(result, data_source=self._datasource)
        except Exception as e:
            self.send_message(f'{e} Error occurred during processing trade result, result will be ignored')
            if self.debug:
                import traceback
                traceback.print_exc()
            return
        if result_id is not None:
            result_detail = read_trade_result_by_id(result_id, data_source=self._datasource)
            order_id = result_detail['order_id']
            order_detail = read_trade_order_detail(order_id, data_source=self._datasource)
            pos, d, sym = order_detail['position'], order_detail['direction'], order_detail['symbol']
            status = order_detail['status']
            filled_qty, filled_price = result_detail['filled_qty'], result_detail['price']
            # send message to indicate execution of order
            self.send_message(f'<ORDER EXECUTED {order_id}>: '
                              f'{d}-{pos} of {sym}: {status} with {filled_qty} @ {filled_price}')
            # send message to indicate change of positions / cashes
            # 读取交易处理以后的账户信息和持仓信息
            order_id = result['order_id']
            order_detail = read_trade_order_detail(order_id, data_source=self._datasource)
            # 读取持仓信息
            pos_id = order_detail['pos_id']
            position = get_position_by_id(pos_id, data_source=self._datasource)
            post_qty, post_available, post_cost = position['qty'], position['available_qty'], position['cost']
            # 读取持有现金
            account = get_account(self.account_id, data_source=self._datasource)
            post_cash_amount = account['cash_amount']
            post_available_cash = account['available_cash']
            if pre_qty != post_qty:
                self.send_message(f'<RESULT>: {sym}({pos}): '
                                  f'own {pre_qty:.2f}->{post_qty:.2f}; '
                                  f'available {pre_available:.2f}->{post_available:.2f}; '
                                  f'cost: {pre_cost:.2f}->{post_cost:.2f}')
            if pre_cash_amount != post_cash_amount:
                self.send_message(f'<RESULT>: account cash changed: '
                                  f'cash: ¥{pre_cash_amount:,.2f}->¥{post_cash_amount:,.2f}'
                                  f'available: ¥{pre_available_cash:,.2f}->¥{post_available_cash:,.2f}')

    def _pre_open(self):
        """ pre_open处理所有应该在开盘前完成的任务，包括运行中断后重新开始trader所需的初始化任务：

        - 确保data_source重新连接,
        - 扫描数据源，下载缺失的数据
        - 处理订单的交割
        - 获取当日实时价格
        """
        datasource = self._datasource
        config = self._config
        operator = self._operator

        datasource.reconnect()
        datasource.reconnect()

        datasource.get_all_basic_table_data(
                refresh_cache=True,
        )
        self.send_message(f'data source reconnected...')

        # 扫描数据源，下载缺失的日频或以上数据

        refill_missing_datasource_data(
                operator=operator,
                trader=self,
                config=config,
                datasource=datasource,
        )
        self.send_message(f'missing data acquired!')

        # 检查账户重的成交结果，完成全部交易结果的交割
        delivery_result = process_account_delivery(
                account_id=self.account_id,
                data_source=self._datasource,
                config=self._config
        )
        for res in delivery_result:
            order_id = delivery_result['order_id']
            if res['pos_id']:  # 发生了股票/资产交割，更新了资产股票的可用持仓数量
                pos = get_position_by_id(pos_id=res['pos_id'], data_source=self.datasource)
                symbol = pos['symbol']
                pos_type = pos['position']
                prev_qty = delivery_result['prev_qty']
                updated_qty = delivery_result['updated_qty']
                color_tag = 'bold red' if prev_qty > updated_qty else 'bold green'

                name = get_symbol_names(self.datasource, symbols=symbol)
                self.send_message(f'<DELIVERED {order_id}>: <{name}-{symbol}@{pos_type} side> available qty:'
                                  f'[{color_tag}]{prev_qty}->{updated_qty} [/{color_tag}]')

            if res['account_id']:  # 发生了现金交割，更新了账户现金的可用数量
                account = get_account(account_id=self.account_id, data_source=self.datasource)
                account_name = account['user_name']
                prev_amount = delivery_result['prev_amount']
                updated_amount = delivery_result['updated_amount']
                color_tag = 'bold red' if prev_amount > updated_amount else 'bold green'

                self.send_message(f'<DELIVERED {order_id}>: <{account_name}-{self.account_id}> available cash:'
                                  f'[{color_tag}]¥{prev_amount}->¥{updated_amount}[/{color_tag}]')

        # 获取当日实时价格
        self._update_live_price()

    def _post_close(self):
        """ 所有收盘后应该完成的任务

        1，处理当日未完成的交易信号，生成取消订单，并记录订单取消结果
        2，处理当日已成交的订单结果的交割，记录交割结果
        3，生成消息发送到消息队列
        """
        self.send_message('Processing post_close activities...')

        if self.is_market_open:
            if self.debug:
                self.send_message('market is still open, post_close can not be executed during open time!')
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
            self.send_message(f'partially filled orders found, they are to be canceled: \n{orders_to_be_canceled}')
        for order_id in orders_to_be_canceled.index:
            # 部分成交订单不为空，需要生成一条新的交易记录，用于取消订单中的未成交部分，并记录订单结果
            # TODO: here "submitted" orders can not be canceled, need to be fixed
            cancel_order(order_id=order_id, data_source=self._datasource)
            order_details = read_trade_order_detail(order_id, data_source=self._datasource)
            sym = order_details['symbol']
            name = get_symbol_names(self._datasource, [sym])[0]
            d = order_details['direction']
            pos = order_details['position']
            qty = order_details['qty']
            price = order_details['price']
            self.send_message(f'<CANCELED ORDER {order_id}>: <{name}-{sym}> {d}-{pos} '
                                      f'{qty} shares @ ¥{price}')

    def _change_date(self):
        """ 改变日期，在日期改变（午夜）前执行的操作，包括：

        - 处理前一日交易的交割
        - 处理前一日获取的实时数据、并准备下一日的实时数据
        - 检查下一日是否是交易日，并更新相关的运行参数
        - 重新生成agenda
        - 生成消息发送到消息队列
        """
        raise NotImplementedError

    def _market_open(self):
        """ 开市时操作：

        1，启动broker的主循环，将broker的status设置为running
        2，生成消息发送到消息队列
        """
        if self.debug:
            self.send_message('running task: market open')
        self.is_market_open = True
        self.run_task('wakeup')
        self.send_message('market is open, trader is running, broker is running')

    def _market_close(self):
        """ 收市时操作：

        1，停止broker的主循环，将broker的status设置为stopped
        2，生成消息发送到消息队列
        """
        if self.debug:
            self.send_message('running task: market close')
        self.is_market_open = False
        self.run_task('sleep')
        self.send_message('market is closed, trader is slept, broker is paused')

    def _refill(self, tables, freq):
        """ 补充数据库内的历史数据 """
        if self.debug:
            self.send_message('running task: refill, this task will be done only during sleeping')
        # 更新数据源中的数据，不同频率的数据表可以不同时机更新，每次更新时仅更新当天或最近一个freq的数据
        # 例如，freq为H或min的数据，更新当天的数据，freq为W的数据，更新最近一周
        # 在arg中必须给出freq以及tables两个参数，tables参数直接传入refill_local_source函数
        # freq被用于计算start_date和end_date
        end_date = self.get_current_tz_datetime().date()
        if freq == 'D':
            start_date = end_date
        elif freq == 'W':
            start_date = end_date - pd.Timedelta(days=7)
        elif freq == 'M':
            start_date = end_date - pd.Timedelta(days=30)
        else:
            raise ValueError(f'invalid freq: {freq}')
        self._datasource.refill_local_source(
                tables=tables,
                start_date=start_date,
                end_date=end_date,
                merge_type='update',
        )

    # ================ task operations =================
    def run_task(self, task, *args, run_in_main_thread=False):
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
            raise ValueError(f'task must be a string, got {type(task)} instead.')

        if task not in available_tasks.keys():
            raise ValueError(f'Invalid task name: {task}')

        task_func = available_tasks[task]

        new_thread_tasks = ['acquire_live_price', 'run_strategy', 'process_result']
        if (not run_in_main_thread) and (task in new_thread_tasks):
            from threading import Thread
            if args:
                t = Thread(target=task_func, args=args, daemon=True)
            else:
                t = Thread(target=task_func, daemon=True)
            if self.debug:
                self.send_message(f'will run task: {task} with args: {args} in a new Thread {t.name}')
            t.start()
        else:
            if args:
                task_func(*args)
            else:
                task_func()

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
            # current_date = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).date()  # 产生世界时UTC时间
            current_date = self.get_current_tz_datetime().date()  # 产生本地时间
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
            self.send_message(f'putting task {task} into task queue')
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
            # current_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).time()  # 产生UTC时间
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
                if self.debug:
                    self.send_message(f'adding task: {task_tuple} from agenda')
                if len(task_tuple) == 3:
                    task = task_tuple[1:3]
                elif len(task_tuple) == 2:
                    task = task[1]
                else:
                    raise ValueError(f'Invalid task tuple: No task found in {task_tuple}')

                if self.debug:
                    self.send_message(f'current time {current_time} >= task time {task_time}, '
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
            self.send_message(f'Next task:({next_task[1]}) in '
                              f'{sec_to_duration(count_down_to_next_task, estimation=True)}',
                              new_line=False)

    def _initialize_schedule(self, current_time=None):
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
        if self.debug:
            self.send_message('initializing agenda...\r')
        # 如果不是交易日，直接返回
        if not self.is_trade_day:
            if self.debug:
                self.send_message('not a trade day, no need to initialize agenda')
            return
        if self.task_daily_schedule:
            # 如果任务日程非空列表，直接返回
            if self.debug:
                self.send_message('task agenda is not empty, no need to initialize agenda')
            return
        self.task_daily_schedule = create_daily_task_schedule(
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
                self.send_message('before market morning open, keeping all tasks')
        elif moa < current_time < mca:
            # market open time, remove all task before current time except pre_open
            if self.debug:
                self.send_message('market open, removing all tasks before current time except pre_open and open_market')
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'open_market'])]
        elif mca < current_time < moc:
            # before market afternoon open, remove all task before current time except pre_open, open_market and sleep
            if self.debug:
                self.send_message('before market afternoon open, removing all tasks before current time '
                                  'except pre_open, open_market and sleep')
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'open_market',
                                                     'sleep'])]
        elif moc < current_time < mcc:
            # market afternoon open, remove all task before current time except pre_open, open_market, sleep, and wakeup
            if self.debug:
                self.send_message('market afternoon open, removing all tasks before current time '
                                  'except pre_open, open_market, sleep and wakeup')
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'open_market',
                                                     'sleep',
                                                     'wakeup'])]
        elif mcc < current_time:
            # after market close, remove all task before current time except pre_open and post_close
            if self.debug:
                self.send_message('market closed, removing all tasks before current time except post_close')
            self.task_daily_schedule = [task for task in self.task_daily_schedule if
                                        (pd.to_datetime(task[0]).time() >= current_time) or
                                        (task[1] in ['pre_open',
                                                     'post_close'])]
        else:
            raise ValueError(f'Invalid current time: {current_time}')

    def _change_cash(self, amount):
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
        self.send_message(f'Cash amount changed to {self.account_cash}')
        return

    def _change_position(self, symbol, quantity, price, side=None):
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
                        account_id=self.account_id,
                        symbol=symbol,
                        position_type=side,
                        data_source=self.datasource,
                )
        position = get_position_by_id(
                pos_id=position_id,
                data_source=self.datasource,
        )
        if self.debug:
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
        return

    def _update_live_price(self):
        """获取实时数据，并将实时数据更新到self.live_price中，此函数可能出现Timeout或运行失败"""
        if self.debug:
            self.send_message(f'Acquiring live price data')
        from .emfuncs import stock_live_kline_price
        try:
            real_time_data = stock_live_kline_price(symbols=self.asset_pool)
        except Exception as e:
            if self.debug:
                import traceback
                self.send_message(f'Error in acquiring live prices: {e}')
                traceback.print_exc()
            return None
        if real_time_data.empty:
            # empty data downloaded
            if self.debug:
                self.send_message(f'Something wrong, failed to download live price data.')
            return
        real_time_data.set_index('symbol', inplace=True)
        # 将real_time_data 赋值给self.live_price
        self.live_price = real_time_data
        if self.debug:
            self.send_message(f'acquired live price data, live prices updated!')
        return

    TASK_WHITELIST = {
        'stopped':  ['start'],
        'running':  ['stop', 'sleep', 'pause', 'run_strategy', 'process_result', 'pre_open',
                     'open_market', 'close_market', 'acquire_live_price'],
        'sleeping': ['wakeup', 'stop', 'pause', 'pre_open',
                     'process_result',  # 如果交易结果已经产生，哪怕处理时Trader已经处于sleeping状态，也应该处理完所有结果
                     'open_market', 'post_close', 'refill'],
        'paused':   ['resume', 'stop'],
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
        交易账户ID, 如果ID小于0或者未给出，则需要新建一个账户
    user_name: str, optional
        交易账户用户名，如果未给出账户ID或为空，则需要新建一个账户，此时必须给出用户名
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
    if (account_id is None) or (account_id < 0):
        if (user_name is None) or (user_name == ''):
            raise ValueError('if account_id is None, user_name must be given.')
        account_id = new_account(
                user_name=user_name,
                cash_amount=init_cash,
                data_source=datasource,
        )
    try:
        _ = get_account(account_id, data_source=datasource)
    except Exception as e:
        raise ValueError(f'{e}\naccount {account_id} does not exist. choose a valid account or create a new one.')

    # now we know that account_id is valid

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
                        'qty_change':           abs(amount),
                        'available_qty_change': abs(amount),
                    }
            )

    # if account is ready then create trader and broker
    broker_type = config['live_trade_broker_type']
    broker_params = config['live_trade_broker_params']
    if (broker_type == 'simulator') and (broker_params is None):
        broker_params = {
            "fee_rate_buy": config['cost_rate_buy'],
            "fee_rate_sell": config['cost_rate_sell'],
            "fee_min_buy": config['cost_min_buy'],
            "fee_min_sell": config['cost_min_sell'],
            "fee_fix_buy": config['cost_fixed_buy'],
            "fee_fix_sell": config['cost_fixed_sell'],
            "slipage": config['cost_slippage'],
            "moq_buy": config['trade_batch_size'],
            "moq_sell": config['sell_batch_size'],
            "delay": 1.0,
            "price_deviation": 0.001,
            "probabilities": (0.9, 0.08, 0.02),
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

    TraderShell(trader).run()


def refill_missing_datasource_data(operator, trader, config, datasource):
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
    from qteasy.database import htype_to_table_col
    op_data_types = operator.op_data_types
    op_data_freq = operator.op_data_freq
    related_tables = htype_to_table_col(
            htypes=op_data_types,
            freq=op_data_freq,
            asset_type=config['asset_type'],

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

        datasource.refill_local_source(
                tables='index_daily',
                dtypes=op_data_types,
                freqs=op_data_freq,
                asset_types=asset_types,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.to_pydatetime().strftime('%Y%m%d'),
                symbols=symbol_list,
                parallel=True,
                refresh_trade_calendar=True,
        )

    return
