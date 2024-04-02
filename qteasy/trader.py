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

import shlex
import os
import shutil
import sys
import time
import argparse
import logging
from cmd import Cmd
from queue import Queue
from threading import Timer

import numpy as np
import pandas as pd
import rich

import qteasy
from qteasy import ConfigDict, DataSource, Operator
from qteasy.broker import Broker
from qteasy.core import check_and_prepare_live_trade_data
from qteasy.trade_recording import get_account, get_account_position_availabilities, get_account_position_details
from qteasy.trade_recording import get_account_cash_availabilities, query_trade_orders, record_trade_order
from qteasy.trade_recording import get_or_create_position, new_account, update_position
from qteasy.trading_util import cancel_order, create_daily_task_schedule, get_position_by_id
from qteasy.trading_util import get_last_trade_result_summary, get_symbol_names, process_account_delivery
from qteasy.trading_util import parse_trade_signal, process_trade_result, submit_order
from qteasy.utilfuncs import TIME_FREQ_LEVELS, adjust_string_length, parse_freq_string, sec_to_duration, str_to_list
from qteasy.utilfuncs import get_current_tz_datetime

UNIT_TO_TABLE = {
    'h':     'stock_hourly',
    '30min': 'stock_30min',
    '15min': 'stock_15min',
    '5min':  'stock_5min',
    '1min':  'stock_1min',
    'min':   'stock_1min',
}


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
    - watch: 添加或删除股票到监视列表
    - buy: 手动创建买入订单
    - sell: 手动创建卖出订单
    - change: 手动修改交易系统的资金和持仓
    - positions: 查看账户持仓
    - orders: 查看账户订单
    - history: 查看账户历史交易记录
    - overview: 查看账户概览
    - config: 查看或修改qt_config配置信息
    - dashboard: 退出shell，进入dashboard模式
    - strategies: 查看策略信息，或者修改策略参数
    - schedule: 查看交易日程
    - help: 查看帮助信息
    - run: 手动运行交易策略，此功能仅在debug模式下可用

    qteasy Shell的命令支持参数解析，用户可以通过命令行参数来调整命令的行为，要查看所有命令的帮助，
    可以使用命令 "help" 或者 "?"，要查看某个命令的帮助，可以使用命令 "help <command>" 或者
    命令的-h参数，如<command -h>。

    在Shell运行过程中按下 ctrl + c 进入状态选单，用户可以选择进入dashboard模式或者退出shell

    """
    intro = 'Welcome to the trader shell interactive mode. Type help or ? to list commands.\n' \
            'Type "bye" to stop trader and exit shell.\n' \
            'Type "dashboard" to leave interactive mode and enter dashboard.\n' \
            'Type "help <command>" to get help for more commands.\n'
    prompt = '(QTEASY) '

    argparser_properties = {
        'status':     dict(prog='status', description='Show trader status',
                           usage='status [-h]', ),
        'pause':      dict(prog='pause', description='Pause trader',
                           usage='pause [-h]',
                           epilog='When trader is paused, strategies will not be executed, '
                                  'orders will not be submitted, submitted orders will be '
                                  'suspended until trader is resumed'),
        'resume':     dict(prog='resume', description='Resume trader',
                           usage='resume [-h]', ),
        'bye':        dict(prog='bye', description='Stop trader and exit shell',
                           usage='bye [-h]',
                           epilog='You can also exit shell using command "exit" or "stop"'),
        'exit':       dict(prog='exit', description='Stop trader and exit shell',
                           usage='exit [-h]',
                           epilog='You can also exit shell using command "bye" or "stop"'),
        'stop':       dict(prog='stop', description='Stop trader and exit shell',
                           usage='stop [-h]',
                           epilog='You can also exit shell using command "exit" or "bye"'),
        'info':       dict(prog='info', description='Get trader info, same as overview',
                           usage='info [-h] [--detail] [--system]',
                           epilog='Get trader info, including basic information of current '
                                  'account, and current cash and positions'),
        'pool':       dict(prog='pool', description='Show details of asset pool',
                           usage='pool [-h]'),
        'watch':      dict(prog='watch', description='Add or remove stock symbols to watch list',
                           usage='watch [SYMBOL [SYMBOL ...]] [-h] [--position] [--remove '
                                 '[REMOVE [REMOVE ...]]] [--clear]'),
        'buy':        dict(prog='buy', description='Manually create buy-in order',
                           usage='buy AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] '
                                 '[--force]',
                           epilog='the order will be submitted to broker and will be executed'
                                  ' according to broker rules, Currently only market price '
                                  'orders can be submitted, and the orders might not be executed '
                                  'immediately if market is not open'),
        'sell':       dict(prog='sell', description='Manually create sell-out order',
                           usage='sell AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] '
                                 '[--force]',
                           epilog='the order will be submitted to broker and will be executed'
                                  ' according to broker rules, Currently only market price '
                                  'orders can be submitted, and the orders might not be executed '
                                  'immediately if market is not open'),
        'positions':  dict(prog='positions', description='Get account positions',
                           usage='positions [-h]',
                           epilog='Print out holding quantities and available quantities '
                                  'of all positions'),
        'overview':   dict(prog='overview', description='Get trader overview, same as info',
                           usage='overview [-h] [--detail] [--system]',
                           epilog='Get trader info, including basic information of current '
                                  'account, and current cash and positions'),
        'config':     dict(prog='config', description='Show or change qteasy configurations',
                           usage='config [KEYS [KEYS ...]] [-h] [--level LEVEL] [--detail] [--set SET]'),
        'history':    dict(prog='history', description='List trade history of a stock',
                           usage='history [SYMBOL] [-h]',
                           epilog='List all trade history of one particular stock, displaying '
                                  'every buy-in and sell-out in a table format. '
                                  'symbol like 000651 is accepted.'),
        'orders':     dict(prog='orders', description='Get account orders',
                           usage='usage: orders [SYMBOL [SYMBOL ...]] [-h] '
                                 '[--status {filled,f,canceled,c,partial-filled,p}] '
                                 '[--time {today,t,yesterday,y,3day,3,week,w,month,m,all,a}] '
                                 '[--type {buy,sell,b,s,all,a}] '
                                 '[--side {long,short,l,s,all,a}]'),
        'change':     dict(prog='change', description='Change account cash and positions',
                           usage='change [SYMBOL] [-h] [--amount AMOUNT] [--price PRICE] '
                                 '[--side {l,long,s,short}] [--cash CASH]',
                           epilog='Change cash or positions or both. nothing will be changed '
                                  'if amount or cash is not given, price is used to calculate '
                                  'new cost, if not given, current price will be used'),
        'dashboard':  dict(prog='', description='Exit shell and enter dashboard',
                           usage='dashboard [-h] [--rewind REWIND]',
                           epilog='Exit shell and enter dashboard mode, where trading logs '
                                  'are displayed in real time, provide an integer to rewind '
                                  'previous rows of logs, default 50 rows'),
        'strategies': dict(prog='', description='Show or change strategy parameters',
                           usage='strategies [STRATEGY [STRATEGY ...]] [-h] [--detail] '
                                 '[--set-par [SET_VAL [SET_VAL ...]]] [--blender BLENDER] '
                                 '[--timing TIMING]'),
        'schedule':   dict(prog='', description='Show trade agenda',
                           usage='schedule [-h]'),
        'run':        dict(prog='', description='Run strategies manually',
                           usage='run [STRATEGY [STRATEGY ...]] [-h] '
                                 '[--task {none,stop,sleep,pause,process_result,'
                                 'pre_open,open_market,close_market,acquire_live_price}] '
                                 '[--args [ARGS [ARGS ...]]]'),
    }

    command_arguments = {
        'status':     [],
        'pause':      [],
        'resume':     [],
        'bye':        [],
        'exit':       [],
        'stop':       [],
        'info':       [('--detail', '-d'),
                       ('--system', '-s')],
        'pool':       [],
        'watch':      [('symbols',),
                       ('--position', '--positions', '-pos', '-p'),
                       ('--remove', '-r'),
                       ('--clear', '-c')],
        'buy':        [('amount',),
                       ('symbol',),
                       ('--price', '-p'),
                       ('--side', '-s'),
                       ('--force', '-f')],
        'sell':       [('amount',),
                       ('symbol',),
                       ('--price', '-p'),
                       ('--side', '-s'),
                       ('--force', '-f')],
        'positions':  [],
        'overview':   [('--detail', '-d'),
                       ('--system', '-s')],
        'config':     [('keys',),
                       ('--level', '-l'),
                       ('--detail', '-d'),
                       ('--set', '-s')],
        'history':    [('symbol',)],
        'orders':     [('symbols',),
                       ('--status', '-s'),
                       ('--time', '-t'),
                       ('--type', '-y'),
                       ('--side', '-d')],
        'change':     [('symbol',),
                       ('--amount', '-a'),
                       ('--price', '-p'),
                       ('--side', '-s'),
                       ('--cash', '-c')],
        'dashboard':  [('--rewind', '-r'),
                       ],
        'strategies': [('strategy',),
                       ('--detail', '-d'),
                       ('--set-par', '--set', '-s'),
                       ('--blender', '-b'),
                       ('--timing', '-t')],
        'schedule':   [],
        'run':        [('strategy',),
                       ('--task', '-t'),
                       ('--args', '-a')],
    }

    command_arg_properties = {
        'status':     [],
        'pause':      [],
        'resume':     [],
        'bye':        [],
        'exit':       [],
        'stop':       [],
        'info':       [{'action': 'store_true',
                        'help':   'show detailed account info'},
                       {'action': 'store_true',
                        'help':   'show system info'}],
        'pool':       [],
        'watch':      [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'stock symbols to add to watch list'},
                       {'action': 'store_true',
                        'dest':   'position',
                        'help':   'add 5 stocks from position list to watch list'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'remove stock symbols from watch list'},
                       {'action': 'store_true',
                        'help':   'clear watch list'}],
        'buy':        [{'action': 'store',
                        'type':   float,
                        'help':   'amount of shares to buy'},
                       {'action': 'store',
                        'help':   'stock symbol to buy'},
                       {'action':  'store',
                        'type':    float,
                        'default': 0.0,  # default to market price
                        'help':    'price to buy at'},
                       {'action':  'store',
                        'default': 'long',
                        'choices': ['long', 'short'],
                        'help':    'order position side, default long'},
                       {'action': 'store_true',
                        'help':   'force buy regardless of current prices (NOT IMPLEMENTED YET)'}],
        'sell':       [{'action': 'store',
                        'type':   float,
                        'help':   'amount of shares to sell'},
                       {'action': 'store',
                        'help':   'stock symbol to sell'},
                       {'action':  'store',
                        'type':    float,
                        'default': 0.0,  # default to market price
                        'help':    'price to sell at'},
                       {'action':  'store',
                        'default': 'long',
                        'choices': ['long', 'short'],
                        'help':    'order position side, default long'},
                       {'action': 'store_true',
                        'help':   'force sell regardless of current prices'}],
        'positions':  [],
        'overview':   [{'action': 'store_true',
                        'help':   'show detailed account info'},
                       {'action': 'store_true',
                        'help':   'show system info'}],
        'config':     [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'config keys to show or change'},
                       {'action':  'count',
                        'default': 2,
                        'help':    'config level to show or change'},
                       {'action': 'store_true',
                        'help':   'show detailed config info'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'config values to set or change for keys'}],
        'history':    [{'action':  'store',
                        'nargs':   '?',  # nargs='?' will require at most one argument
                        'default': 'all',
                        'type':    str,
                        'help':    'stock symbol to show history for, if not given, show history for all'}],
        'orders':     [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'stock symbol to show orders for'},
                       {'action':  'store',
                        'default': 'all',
                        'choices': ['filled', 'f', 'canceled', 'c', 'partial-filled', 'p'],
                        'help':    'order status to show'},
                       {'action':  'store',
                        'default': 'today',
                        'choices': ['today', 't', 'yesterday', 'y', '3day', '3', 'week', 'w',
                                    'month', 'm', 'all', 'a'],
                        'help':    'order time to show'},
                       {'action':  'store',
                        'default': 'all',
                        'choices': ['buy', 'sell', 'b', 's', 'all', 'a'],
                        'help':    'order type to show'},
                       {'action':  'store',
                        'default': 'all',
                        'choices': ['long', 'short', 'l', 's', 'all', 'a'],
                        'help':    'order side to show'}],
        'change':     [{'action':  'store',
                        'nargs':   '?',  # one or zero (default value) argument is allowed
                        'default': '',
                        'help':    'symbol to change position for'},
                       {'action':  'store',
                        'default': 0,
                        'type':    float,
                        'help':    'amount of shares to change'},
                       {'action':  'store',
                        'default': 0.0,  # default to market price
                        'type':    float,
                        'help':    'price to change position at'},
                       {'action':  'store',
                        'default': 'long',
                        'choices': ['l', 'long', 's', 'short'],
                        'help':    'side of the position to change'},
                       {'action':  'store',
                        'default': 0.0,  # default not to change cash
                        'type':    float,
                        'help':    'amount of cash to change for current account'}],
        'dashboard':  [{'action':  'store',
                        'type':    int,
                        'default': 50,
                        'help':    'rewind previous rows of logs, default to 50'}],
        'strategies': [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',  # nargs='+' will require at least one argument
                        'help':   'strategy to show or change parameters for'},
                       {'action': 'store_true',
                        'help':   'show detailed strategy info'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'dest':   'set_val',
                        'help':   'set parameters for strategy'},
                       {'action':  'store',
                        'default': '',
                        'type':    str,
                        'help':    'set blender for strategies'},
                       {'action':  'store',
                        'default': '',
                        'help':    'The strategy run timing of the strategies whose blender is set'}],
        'schedule':   [],
        'run':        [{'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'strategies to run'},
                       {'action':  'store',
                        'default': '',
                        'choices': ['none', 'stop', 'sleep', 'pause', 'resume',
                                    'run_strategy', 'process_result', 'pre_open',
                                    'open_market', 'close_market', 'acquire_live_price'],
                        'help':    'task to run'},
                       {'action': 'append',  # TODO: for python version >= 3.8, use action='extend' instead
                        'nargs':  '*',
                        'help':   'arguments for the task to run'}],
    }

    def __init__(self, trader):
        super().__init__(completekey='tab')
        self._trader = trader
        self._timezone = trader.time_zone
        self._status = None
        self._watch_list = ['000001.SH']  # default watched price is SH index
        self._watched_prices = ' == Realtime prices can be displayed here. ' \
                               'Use "watch" command to add stocks to watch list. =='  # watched prices string

        self.argparsers = {}

        self.init_arg_parsers()

    @property
    def trader(self):
        return self._trader

    @property
    def status(self):
        return self._status

    @property
    def watch_list(self):
        return self._watch_list

    def update_watched_prices(self):
        """ 根据watch list返回清单中股票的信息：代码、名称、当前价格、涨跌幅
        """
        if self._watch_list:
            from qteasy.emfuncs import stock_live_kline_price
            symbols = self._watch_list
            live_prices = stock_live_kline_price(symbols, freq='D', verbose=True, parallel=False)
            if not live_prices.empty:
                live_prices.close = live_prices.close.astype(float)
                live_prices['change'] = live_prices['close'] / live_prices['pre_close'] - 1
                live_prices.set_index('symbol', inplace=True)

                if self.trader.debug:
                    self.trader.send_message('live prices acquired to update watched prices!')
            else:

                if self.trader.debug:
                    self.trader.send_message('Failed to acquire live prices to update watch price string!')
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

    # ----- command arg parsers -----
    def init_arg_parsers(self):
        """ 初始化命令参数解析器
        """
        if self.argparsers:
            return

        # create instances of argparsers for each command
        for command in self.argparser_properties:
            self.argparsers[command] = argparse.ArgumentParser(
                    **self.argparser_properties[command],
            )

        # add arguments to each argparser
        for command in self.argparsers:
            args = self.command_arguments[command]
            arg_properties = self.command_arg_properties[command]
            if not args:
                continue
            for arg, arg_property in zip(args, arg_properties):
                try:
                    self.argparsers[command].add_argument(*arg, **arg_property)
                except:
                    raise RuntimeError(f'Error: failed to add argument {arg} to parser for command {command}\n'
                                       f'pars: {arg_property}')

    def parse_args(self, command, args=None):
        """ 解析命令行参数

        Parameters
        ----------
        command: str
            需要解析参数的命令
        args: str
            需要被解析的参数

        Returns
        -------
        args: Namespace
            解析后的参数，一个Namespace对象
        """
        if command not in self.argparsers:
            raise ValueError(f'Command {command} not found in argparsers')
        arg_parser = self.argparsers[command]
        try:
            args = arg_parser.parse_args(shlex.split(args))
        except argparse.ArgumentError as e:  # wrong argument, this should work for python >= 3.11
            print(f'{e}')
            return None
        except SystemExit:  # wrong argument, this should work for python < 3.10
            # print(f'Wrong argument, use "help {command}" to see more info')
            return None

        return args

    def check_buy_sell_args(self, args, type):
        """ 检查买卖参数是否合法

        Parameters
        ----------
        args: Namespace
            命令行参数对象
        type: str
            买卖类型，'buy' 或 'sell'

        Returns
        -------
        bool
            参数是否合法
        """

        import rich

        qty = args.amount
        symbol = args.symbol.upper()
        price = args.price

        # check if qty and price are legal
        if qty <= 0:
            rich.print("[bold red]Qty can not be less or equal to 0[/bold red]")
            return False
        if price < 0:
            rich.print("[bold red]Price can not be less than 0[/bold red]")
            return False

        # check if qty meets the moq
        if type == 'buy':
            moq = self.trader.get_config('trade_batch_size')['trade_batch_size']
        else:
            moq = self.trader.get_config('sell_batch_size')['sell_batch_size']

        if moq != 0 and qty % moq != 0:
            rich.print(f'[bold red]Qty should be a multiple of the minimum order quantity ({moq})[/bold red]')
            return False

        # check if symbol is legal
        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like
        if not is_complete_cn_stock_symbol_like(symbol):
            print(f'Wrong symbol is given: {symbol}, please input full symbol code like "000651.SZ"')
            return False

        # if price == 0, use live price
        if price == 0:
            if self.trader.live_price is None:
                rich.print(f'[bold red]No live price data available, price should be given![/bold red')
                return False
            try:
                args.price = self.trader.live_price[symbol]
            except KeyError:
                rich.print(f'[bold red]No live price data for {symbol} available, price should be given![/bold red')
                return False

        # the symbol must be in the pool
        if symbol not in self.trader.asset_pool:
            rich.print(f'[bold red]{symbol} is not in the asset pool, can not be bought![/bold red')
            return False

        return True

    # ----- basic commands -----
    def do_status(self, arg):
        """usage: status [-h]

        Show trader status

        optional arguments:
          -h, --help  show this help message and exit

        Examples:
        ---------
        to show trader status:
        (QTEASY) status
        """

        import rich
        args = self.parse_args('status', arg)
        if not args:
            return False

        rich.print(f'current trader status: {self.trader.status} \n'
                   f'current broker name: {self.trader.broker.broker_name} \n'
                   f'current broker status: {self.trader.broker.status} \n'
                   f'current day is trade day: {self.trader.is_trade_day} \n')

    def do_pause(self, arg):
        """usage: pause [-h]

        Pause trader

        optional arguments:
          -h, --help  show this help message and exit

        When trader is paused, strategies will not be executed, orders will not be
        submitted, submitted orders will be suspended until trader is resumed

        Examples:
        ---------
        to pause trader:
        (QTEASY) pause
        """
        args = self.parse_args('pause', arg)
        if not args:
            return False
        self.trader.add_task('pause')
        sys.stdout.write(f'Pausing trader... use command status to check current status\n')

    def do_resume(self, arg):
        """usage: resume [-h]

        Resume trader

        optional arguments:
          -h, --help  show this help message and exit

        Examples:
        ---------
        to resume trader:
        (QTEASY) resume
        """
        args = self.parse_args('resume', arg)
        if not args:
            return False
        self.trader.add_task('resume')
        sys.stdout.write(f'Resuming trader...\n')

    def do_bye(self, arg):
        """usage: bye [-h]

        Stop trader and exit shell

        optional arguments:
          -h, --help  show this help message and exit

        You can also exit shell using command "exit" or "stop"

        Examples:
        ---------
        to stop trader and exit shell:
        (QTEASY) bye
        """
        args = self.parse_args('bye', arg)
        if not args:
            return False
        print(f'canceling all unfinished orders')
        self.trader.add_task('post_close')
        print(f'stopping trader...')
        self.trader.add_task('stop')
        self._status = 'stopped'
        return True

    def do_exit(self, arg):
        """usage: exit [-h]

        Stop trader and exit shell

        optional arguments:
          -h, --help  show this help message and exit

        You can also exit shell using command "bye" or "stop"

        Examples:
        ---------
        to stop trader and exit shell:
        (QTEASY) exit
        """
        return self.do_bye(arg)

    def do_stop(self, arg):
        """usage: stop [-h]

        Stop trader and exit shell

        optional arguments:
          -h, --help  show this help message and exit

        You can also exit shell using command "exit" or "bye"

        Examples:
        ---------
        to stop trader and exit shell:
        (QTEASY) stop
        """
        return self.do_bye(arg)

    def do_info(self, arg):
        """usage: info [-h] [--detail] [--system]

        Get trader info, same as overview

        optional arguments:
          -h, --help    show this help message and exit
          --detail, -d  show detailed account info
          --system, -s  show system info

        Get trader info, including basic information of current account, and
        current cash and positions.

        Examples:
        ---------
        to get trader info:
        (QTEASY) info
        to get detailed trader info:
        (QTEASY) info --detail
        """
        return self.do_overview(arg)

    def do_pool(self, arg):
        """print information of the asset pool

        Print detailed information of all stocks in the asset pool, including
        stock symbol, name, company name, industry, listed date, etc.

        """

        args = self.parse_args('pool', arg)
        if not args:
            return False

        return self.trader.asset_pool_detail()

    def do_watch(self, arguments):
        """usage: watch [SYMBOL [SYMBOL ...]] [-h] [--position] [--remove [REMOVE [REMOVE ...]]] [--clear]

        Add or remove stock symbols to watch list

        positional arguments:
          symbols               stock symbols to add to watch list

        optional arguments:
          -h, --help            show this help message and exit
          --position, --positions, -pos, -p
                                add 5 stocks from position list to watch list
          --remove [REMOVE [REMOVE ...]], -r [REMOVE [REMOVE ...]]
                                remove stock symbols from watch list
          --clear, -c           clear watch list

        Examples:
        ---------
        to view current watch list
        (QTEASY) watch
        to add stock symbols to watch list:
        (QTEASY) watch 000651.SZ 600036.SH 000550.SZ
        to add 5 stocks from position list to watch list:
        (QTEASY) watch --position
        to remove stock symbols from watch list:
        (QTEASY) watch -r 000651.SZ 600036.SH
        to clear watch list:
        (QTEASY) watch -c
        """

        import rich
        args = self.parse_args('watch', arguments)
        if not args:
            return False

        # TODO: for python version >= 3.8, list args are extended then flatten nested list is not needed
        if args.symbols is None:
            args.symbols = []
        else:
            args.symbols = [symbol.upper() for symbol_list in args.symbols for symbol in symbol_list]

        if args.remove is None:
            args.remove = []
        else:
            args.remove = [symbol.upper() for symbol_list in args.remove for symbol in symbol_list]

        from .utilfuncs import is_complete_cn_stock_symbol_like

        illegal_symbols = []
        for symbol in args.symbols:
            if not is_complete_cn_stock_symbol_like(symbol):
                illegal_symbols.append(symbol)
                continue

            # 添加symbols到watch list，除非该代码已在watch list中
            if symbol not in self._watch_list:
                self._watch_list.append(symbol)
            # 检查watch_list中代码个数是否超过5个，如果超过，删除最早添加的代码
            if len(self._watch_list) > 5:
                self._watch_list.pop(0)

        # 如果arg.position == True，则将当前持仓量最大的股票代码添加到watch list
        if args.position:
            pos = self._trader.account_position_info
            if pos.empty:
                print('No holding position at the moment.')
            top_5_pos = pos.sort_values(by='market_value', ascending=False).head(5)
            top_5_pos = top_5_pos.index.tolist()
            self._watch_list = top_5_pos

        # 如果arg.remove不为空，则将remove中的股票代码从watch list中删除
        symbols_not_found = []
        if args.remove:
            for symbol in args.remove:
                print(f'is removing symbol {symbol} from watch list {self._watch_list}')
                if symbol in self._watch_list:
                    self._watch_list.remove(symbol)
                else:
                    symbols_not_found.append(symbol)

        # 如果arg.clear == True，则清空watch list
        if args.clear:
            self._watch_list = []

        rich.print(f'current watch list: {self._watch_list}')
        if illegal_symbols:
            rich.print(f'Illegal symbols in arguments: {illegal_symbols}, input symbols in the form like "000651.SZ"')
        if symbols_not_found:
            rich.print(f'Symbols can not be removed from watch list because they are not there: {symbols_not_found}')

    def do_buy(self, arg):
        """usage: buy AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] [--force]

        Manually create buy-in order

        positional arguments:
          amount                amount of shares to buy
          symbol                stock symbol to buy

        optional arguments:
          -h, --help            show this help message and exit
          --price PRICE, -p PRICE
                                price to buy at
          --side {long,short}, -s {long,short}
                                order position side, default long
          --force, -f           force buy regardless of current prices (NOT IMPLEMENTED YET)

        the order will be submitted to broker and will be executed according to broker
        rules, Currently only market price orders can be submitted, and the orders might
        not be executed immediately if market is not open

        Examples:
        ---------
        to buy 100 shares of 000651.SH at price 32.5
        (QTEASY) buy 100 000651.Sh -p 32.5
        to buy short 100 shares of 000651 at price 30.0
        (QTEASY) buy 100 000651.SH -p 30.0 -s short
        """

        args = self.parse_args('buy', arg)
        if not args:
            return False

        if not self.check_buy_sell_args(args, 'buy'):
            return False

        account_id = self.trader.account_id
        datasource = self.trader.datasource
        broker = self.trader.broker

        qty = args.amount
        symbol = args.symbol.upper()
        price = args.price
        position = args.side

        # start to add order
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

        # 检查

        order_id = record_trade_order(trade_order, data_source=datasource)

        # 提交交易订单
        if submit_order(order_id=order_id, data_source=datasource) is not None:
            trade_order['order_id'] = order_id
            broker.order_queue.put(trade_order)
            print(f'Order <{order_id}> has been submitted to broker: '
                  f'{trade_order["direction"]} {trade_order["qty"]:.1f} of {symbol} '
                  f'at price {trade_order["price"]:.2f}')

            if not self.trader.is_market_open:
                print(f'Market is not open, order might not be executed immediately')

    def do_sell(self, arg):
        """usage: sell AMOUNT SYMBOL [-h] [--price PRICE] [--side {long,short}] [--force]

        Manually submit buy-in order

        positional arguments:
          amount                amount of shares to sell
          symbol                stock symbol to sell

        optional arguments:
          -h, --help            show this help message and exit
          --price PRICE, -p PRICE
                                price to sell at
          --side {long,short}, -s {long,short}
                                order position side, default long
          --force, -f           force sell regardless of current prices (NOT IMPLEMENTED YET)

        the order will be submitted to broker and will be executed according to broker
        rules, Currently only market price orders can be submitted, and the orders might
        not be executed immediately if market is not open

        Examples:
        ---------
        to sell 100 shares of 000651.SH at price 32.5
        (QTEASY) sell 100 000651.Sh -p 32.5
        to sell short 100 shares of 000651 at price 30.0
        (QTEASY) sell 100 000651.SH -p 30.0 -s short
        """

        args = self.parse_args('sell', arg)
        if not args:
            return False

        if not self.check_buy_sell_args(args, 'sell'):
            return False

        account_id = self.trader.account_id
        datasource = self.trader.datasource
        broker = self.trader.broker

        qty = args.amount
        symbol = args.symbol.upper()
        price = args.price
        position = args.side

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
            print(f'Order <{order_id}> has been submitted to broker: '
                  f'{trade_order["direction"]} {trade_order["qty"]:.1f} of {symbol} '
                  f'at price {trade_order["price"]:.2f}')

            if not self.trader.is_market_open:
                print(f'Market is not open, order might not be executed immediately')

    def do_positions(self, arg):
        """usage: positions [-h]

        Get account positions

        optional arguments:
          -h, --help  show this help message and exit

        Print out holding quantities and available quantities of all positions

        Examples:
        ---------
        to get account positions:
        (QTEASY) positions
        """

        args = self.parse_args('positions', arg)
        if not args:
            return False

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
        rich.print(f'{pos_header_string}\n{earning_pos_string}\n{losing_pos_string}\n{nan_profit_pos_string}')

    def do_overview(self, arg):
        """usage: overview [-h] [--detail] [--system]

        Get trader overview, same as info

        optional arguments:
          -h, --help    show this help message and exit
          --detail, -d  show detailed account info
          --system, -s  show system info Get trader overview, same as info

        Get trader overview, including basic information of current account, and
        current cash and positions.

        Examples:
        ---------
        to get trader overview:
        (QTEASY) overview
        to get detailed trader overview:
        (QTEASY) overview --detail
        """
        args = self.parse_args('overview', arg)
        if not args:
            return False

        self.trader.info(detail=args.detail, system=args.system)

        if args.detail:
            return self.do_positions(arg='')

    def do_config(self, arg):
        """usage: config [KEYS [kEYS ...]] [-h] [--level] [--detail] [--set [SET [SET ...]]]

        Show or change qteasy configurations

        positional arguments:
          keys                  config keys to show or change

        optional arguments:
          -h, --help            show this help message and exit
          --level, -l           config level to show or change, default to level 2
          --detail, -d          show detailed config info
          --set [SET [SET ...]], -s [SET [SET ...]]
                                config values to set or change for key, a key must be given to set value

        Display current qt configurations to designated level, if level is not given, display
        until level 2.
        if configure key is given and value is not given, display current value, default value
        and explanation of the configure key.
        if configure key and a value is given, change the configure key to the given value.

        Examples:
        ---------
        to show all configures:
        (QTEASY) config
        to show configures until level 3:
        (QTEASY) config -lll
        to show value of configure key "key1":
        (QTEASY) config key1
        to change value of configure key "key1" to "value1":
        (QTEASY) config key1 -s value1
        """

        args = self.parse_args('config', arg)
        if not args:
            return False

        from qteasy._arg_validators import _vkwargs_to_text
        import rich
        import shutil

        # get terminal width and set print width to 75% of terminal width
        column_width, _ = shutil.get_terminal_size()
        column_width = int(column_width * 0.75) if column_width > 120 else column_width

        keys = [str(key) for key_list in args.keys for key in key_list] if args.keys else []
        set_values = [str(value) for value_list in args.set for value in value_list] if args.set else []
        level = args.level
        verbose = args.detail

        get_config = self.trader.get_config
        if not keys:  # no keys given, show all configures
            configs = get_config()
            rich.print(_vkwargs_to_text(configs,
                                        level=level,
                                        info=True,
                                        verbose=verbose,
                                        width=column_width)
                       )
        # if keys are given and set_values are not given, show configure values
        elif keys and not set_values:
            configs = {key: get_config(key)[key] for key in keys}
            rich.print(_vkwargs_to_text(configs,
                                        level='all',
                                        info=True,
                                        verbose=verbose,
                                        width=column_width)
                       )
        # if keys are given and set_values are also given, set configure values
        elif keys and set_values:
            if len(keys) != len(set_values):
                rich.print(f'[bold red]Number of keys and values do not match: {len(keys)} keys and '
                           f'{len(set_values)} values[/bold red]')
                return False

            # update configure values one by one
            for key, value in zip(keys, set_values):
                try:
                    self.trader.update_config(key, value)
                    rich.print(f'[bold green]configure key "{key}" has been changed to "{value}".[bold green]')
                except:
                    rich.print(f'[bold red]configure key "{key}" can not be changed to "{value}".[/bold red]')
                    continue

    def do_history(self, arg):
        """usage: history [SYMBOL] [-h]

        List trade history of a stock

        positional arguments:
          symbol      stock symbol to show history for, if not given, show history for all

        optional arguments:
          -h, --help  show this help message and exit

        List all trade history of one particular stock, displaying every buy-in and
        sell-out in a table format. symbol like 000651 is accepted.

        Examples:
        ---------
        to show trade history of stock 000001:
        (QTEASY) history 000001
        to show trade history of all stocks:
        (QTEASY) history
        """

        args = self.parse_args('history', arg)
        if not args:
            return False

        history = self._trader.history_orders()

        if history.empty:
            print('No trade history found.')
            return

        symbol = args.symbol.upper()

        if symbol != 'ALL':
            from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
            if is_complete_cn_stock_symbol_like(symbol):
                history = history[history['symbol'] == symbol]
                # select orders by order symbol arguments like '000001'
            elif is_cn_stock_symbol_like(symbol):
                possible_complete_symbols = [symbol + '.SH', symbol + '.SZ', symbol + '.BJ']
                history = history[history['symbol'].isin(possible_complete_symbols)]
            else:
                # if argument is not a symbol, use the first available symbol in order details
                print(f'Wrong symbol is given: {symbol}, please input full symbol code like "000651" or "000651.SZ"')
                return False

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
        #  for earning rate
        #  Error will be raised if execution_time is NaT. will print out normal format in this case
        if np.any(pd.isna(history.execution_time)):
            history.execution_time = history.execution_time.fillna(pd.to_datetime('1970-01-01'))

        rich.print(
                history.to_string(
                        columns=['execution_time', 'symbol', 'direction', 'filled_qty', 'price_filled',
                                 'transaction_fee', 'cum_qty', 'value', 'share_cost', 'earnings', 'earning_rate',
                                 'name'],
                        header=['time', 'symbol', 'oper', 'qty', 'price',
                                'trade_fee', 'holdings', 'holding value', 'cost', 'earnings', 'earning_rate',
                                'name'],
                        formatters={
                            'execution_time':  lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x)),
                            'name':            '{:8s}'.format,
                            'operation':       '{:s}'.format,
                            'filled_qty':      '{:,.2f}'.format,
                            'price_filled':    '¥{:,.2f}'.format,
                            'transaction_fee': '¥{:,.2f}'.format,
                            'cum_qty':         '{:,.2f}'.format,
                            'value':           '¥{:,.2f}'.format,
                            'share_cost':      '¥{:,.2f}'.format,
                            'earnings':        '¥{:,.2f}'.format,
                            'earning_rate':    '{:.3%}'.format,
                        },
                        col_space={
                            'name':         8,
                            'price_filled': 10,
                            'value':        12,
                            'share_cost':   10,
                            'earnings':     12,
                        },
                        justify='right',
                        index=False,
                )
        )

    def do_orders(self, arg):
        """ usage: orders [SYMBOL [SYMBOL ...]] [-h] [--status {filled,f,canceled,c,partial-filled,p}]
                [--time {today,t,yesterday,y,3day,3,week,w,month,m,all,a}]
                [--type {buy,sell,b,s,all,a}] [--side {long,short,l,s,all,a}]

        Get account orders

        positional arguments:
          symbol                stock symbol to show orders for

        optional arguments:
          -h, --help            show this help message and exit
          --status {filled,f,canceled,c,partial-filled,p}, -s {filled,f,canceled,c,partial-filled,p}
                                order status to show
          --time {today,t,yesterday,y,3day,3,week,w,month,m,all,a}, -t {today,t,yesterday,y,3day,3,week,w,month,m,all,a}
                                order time to show
          --type {buy,sell,b,s,all,a}, -y {buy,sell,b,s,all,a}
                                order type to show
          --side {long,short,l,s,all,a}, -d {long,short,l,s,all,a}
                                order side to show

        Examples:
        ---------
        to get today's orders:
        (QTEASY) orders
        to get yesterday's orders:
        (QTEASY) orders -t yesterday
        to get orders of stock 000001:
        (QTEASY) orders 000001
        to get filled orders of stock 000001:
        (QTEASY) orders 000001 -s filled
        to get filled buy orders of stock 000001:
        (QTEASY) orders 000001 -s filled -y buy
        """

        args = self.parse_args('orders', arg)
        if not args:
            return False

        symbols = [symbol for symbol_list in args.symbols for symbol in symbol_list] if args.symbols else []
        status = args.status
        order_time = args.time
        order_type = args.type
        side = args.side

        order_details = self._trader.history_orders()

        # filter orders by arguments

        # select orders by time range arguments like 'last_hour', 'today', '3day', 'week', 'month'
        end = self.trader.get_current_tz_datetime()  # 产生本地时区时间
        if order_time in ['last_hour', 'l']:
            start = pd.to_datetime(end) - pd.Timedelta(hours=1)
        elif order_time in ['today', 't']:
            start = pd.to_datetime(end) - pd.Timedelta(days=1)
            start = start.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['yesterday', 'y']:
            yesterday = pd.to_datetime(end) - pd.Timedelta(days=1)
            start = yesterday.strftime("%Y-%m-%d 00:00:00")
            end = yesterday.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['3day', '3']:
            start = pd.to_datetime(end) - pd.Timedelta(days=3)
            start = start.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['week', 'w']:
            start = pd.to_datetime(end) - pd.Timedelta(days=7)
            start = start.strftime("%Y-%m-%d 23:59:59")
        elif order_time in ['month', 'm']:
            start = pd.to_datetime(end) - pd.Timedelta(days=30)
            start = start.strftime("%Y-%m-%d 23:59:59")
        else:
            start = pd.to_datetime(end) - pd.Timedelta(days=1)
            start = start.strftime("%Y-%m-%d 23:59:59")

        # select orders by time range
        order_details = order_details[(order_details['submitted_time'] >= start) &
                                      (order_details['submitted_time'] <= end)]

        # select orders by status arguments like 'filled', 'canceled', 'partial-filled'
        if status in ['filled', 'f']:
            order_details = order_details[order_details['status'] == 'filled']
        elif status in ['canceled', 'c']:
            order_details = order_details[order_details['status'] == 'canceled']
        elif status in ['partial-filled', 'p']:
            order_details = order_details[order_details['status'] == 'partial-filled']
        else:  # default to show all statuses
            pass

        # select orders by order side arguments like 'long', 'short'
        if side in ['long', 'l']:
            order_details = order_details[order_details['position'] == 'long']
        elif side in ['short', 's']:
            order_details = order_details[order_details['position'] == 'short']
        else:  # default to show all sides
            pass

        # select orders by order side arguments like 'buy', 'sell'
        if order_type in ['buy', 'b']:
            order_details = order_details[order_details['direction'] == 'buy']
        elif order_type in ['sell', 's']:
            order_details = order_details[order_details['direction'] == 'sell']
        else:  # default to show all directions
            pass

            # select orders by order symbol arguments like '000001.SZ'

        # normalize symbols to upper case and with suffix codes
        if symbols:
            symbols = [symbol.upper() for symbol in symbols]

        for symbol in symbols:
            from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like
            if is_complete_cn_stock_symbol_like(symbol.upper()):
                order_details = order_details[order_details['symbol'] == symbol.upper()]
            # select orders by order symbol arguments like '000001'
            elif is_cn_stock_symbol_like(symbol):
                possible_complete_symbols = [symbol + '.SH', symbol + '.SZ', symbol + '.BJ']
                order_details = order_details[order_details['symbol'].isin(possible_complete_symbols)]
            else:
                print(f'"{symbol}" invalid: Please input a valid symbol to get order details.')
                return False

        if order_details.empty:
            rich.print(f'No orders found with argument ({args}). try other arguments.')
        else:
            symbols = order_details['symbol'].tolist()
            names = get_symbol_names(datasource=self.trader.datasource, symbols=symbols)
            order_details['name'] = names
            # if NaT in order_details, then strftime will not work, will print out original form of order_details
            if np.any(pd.isna(order_details.execution_time)) or np.any(pd.isna(order_details.submitted_time)):
                print(order_details)
            else:
                rich.print(order_details.to_string(
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
                                    'execution_time': lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x)),
                                    'submitted_time': lambda x: "{:%b%d %H:%M:%S}".format(pd.to_datetime(x))
                                    },
                        col_space={
                            'price_quoted': 10,
                            'price_filled': 10,
                            'filled_qty':   10,
                            'canceled_qty': 10,
                        },
                        justify='right',
                ))

    def do_change(self, arg):
        """usage: change [SYMBOL] [-h] [--amount AMOUNT] [--price PRICE] [--side {l,long,s,short}]
                [--cash CASH]

        Change account cash and positions

        positional arguments:
          symbol                symbol to change position for

        optional arguments:
          -h, --help            show this help message and exit
          --amount AMOUNT, -a AMOUNT
                                amount of shares to change
          --price PRICE, -p PRICE
                                price to change position at
          --side {l,long,s,short}, -s {l,long,s,short}
                                side of the position to change
          --cash CASH, -c CASH  amount of cash to change for current account

           Change trader cash and positions

        Change cash or positions or both. nothing will be changed if amount or cash is not given,
        price is used to calculate new cost, if not given, current price will be used

        Usage:
        ------
        change symbol [--amount | -a AMOUNT] [--price | -p PRICE] [--side | -s l LONG | s SHORT] [--cash | -c amount]

        Examples:
        ---------
        to change cash to increase 1000:
        (QTEASY) change --cash 1000
        to change cash to decrease 1000:
        (QTEASY) change --cash -1000
        to change position of 000651.SH to increase 100 shares:
        (QTEASY) change 000651.SH --amount 100
        to change position of 000651.SH to increase 100 shares at price 32.5:
        (QTEASY) change 000651.SH --amount 100 --price 32.5
        to change short side of position of 000651.SH to increase 100 shares at price 32.5:
        (QTEASY) change 000651.SH --amount 100 --price 32.5 --side short
        """

        args = self.parse_args('change', arg)
        if not args:
            return False

        from qteasy.utilfuncs import is_complete_cn_stock_symbol_like, is_cn_stock_symbol_like

        symbol = args.symbol.upper()
        qty = args.amount
        price = args.price
        side = args.side
        cash_amount = args.cash

        # either qty or cash amount should be given
        if qty == 0 and cash_amount == 0:
            print('Please input one of position amount or cash to change.')
            return False

        # check the format of symbol
        if is_cn_stock_symbol_like(symbol):
            # check if input matches one of symbols in trader asset pool
            asset_pool = self.trader.asset_pool
            asset_pool_striped = [symbol.split('.')[0] for symbol in asset_pool]
            if symbol not in asset_pool_striped:
                print(f'symbol {symbol} not in trader asset pool, please check your input.')
                return False
            symbol = asset_pool[asset_pool_striped.index(symbol)]

        if symbol != '' and not is_complete_cn_stock_symbol_like(symbol):
            print(f'"{symbol}" invalid: Please input a valid symbol to change position holdings.')
            return False

        # get current price if price is not given
        if price == 0:
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
            price = current_price

        if qty != 0:
            if side in ['s', 'short']:
                side = 'short'
            if side in ['l', 'long']:
                side = 'long'
            self._trader.manual_change_position(
                    symbol=symbol,
                    quantity=qty,
                    price=price,
                    side=side,
            )

        if cash_amount != 0:
            # change cash
            self.trader.manual_change_cash(amount=cash_amount)

    def do_dashboard(self, arg):
        """usage: dashboard [-h] [--rewind REWIND]

        Exit shell and enter dashboard

        optional arguments:
          -h, --help    show this help message and exit
          --rewind REWIND, -r REWIND
                        number of lines to rewind  (default: 50)

        Examples:
        ---------
        to enter dashboard mode:
        (QTEASY) dashboard
        to enter dashboard mode and rewind 100 lines:
        (QTEASY) dashboard -r 100
        """

        args = self.parse_args('dashboard', arg)
        if not args:
            return False
        if args.rewind < 0 or args.rewind > 999:
            print('can not rewind more than 999 lines or less than 0 lines. please check your input.')
            return False

        import os
        # check os type of current system, and then clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        self._status = 'dashboard'
        print('\nWelcome to TraderShell! currently in dashboard mode, live status will be displayed here.\n'
              'You can not input commands in this mode, if you want to enter interactive mode, please'
              'press "Ctrl+C" to exit dashboard mode and select from prompted options.\n')
        # read all system logs and display them on the screen
        lines = self.trader.read_sys_log(row_count=args.rewind)
        rich.print(''.join(lines))
        return True

    def do_strategies(self, arg: str):
        """usage: strategies [STRATEGY [STRATEGY ...]] [-h] [--detail] [--set-par [SET_VAL [SET_VAL ...]]]
                [--blender BLENDER] [--timing TIMING]

        Show or change strategy parameters

        positional arguments:
          strategy              strategy to show or change parameters for

        optional arguments:
          -h, --help            show this help message and exit
          --detail, -d          show detailed strategy info
          --set-par [SET_PAR [SET_PAR ...]], --set [SET_PAR [SET_PAR ...]], -s [SET_PAR [SET_PAR ...]]
                                set parameters for strategy
          --blender BLENDER, -b BLENDER
                                set blender for strategies, not implemented yet
          --timing TIMING, -t TIMING
                                The strategy run timing of the strategies whose
                                blender is set, not implemented yet

        Examples:
        ---------
        to display strategies information:
        (QTEASY): strategies
        to display strategies information in detail:
        (QTEASY): strategies --detail
        to set parameters (1, 2, 3) for strategy "stg":
        (QTEASY): strategies stg --set-par 1 2 3
        to set parameters (1, 2, 3) and (4, 5) for strategies "stg1" and "stg2" respectively:
        (QTEASY): strategies stg1 stg2 -s 1 2 3 -s 4 5
        to set blender of strategies:
        (QTEASY): strategies --blender <blender> (not implemented yet)
        """

        args = self.parse_args('strategies', arg)
        if not args:
            return False

        strategies = [stg for stg_list in args.strategy for stg in stg_list] if args.strategy else []
        detail = args.detail
        set_val = [tuple(val_list) for val_list in args.set_val] if args.set_val else []
        timing = args.timing
        blender = args.blender

        if not strategies and not blender:
            # if strategies are not given then display information of operator
            self.trader.operator.info(verbose=detail)
            return

        elif strategies and not set_val:
            # if strategies are given without set values

            strategy_ids = self.trader.operator.strategy_ids
            # check if strategies are all valid strategy ids
            if any(stg not in strategy_ids for stg in strategies):
                wrong_stg = [stg not in strategy_ids for stg in strategies]
                print(f'Strategies ({wrong_stg}) are not valid strategy ids, please check your input!')
                return False
            # show strategy info one by one
            for stg in strategies:
                self.trader.operator[stg].info(verbose=detail)
            return

        elif strategies and set_val:
            # set the parameters of each strategy

            # count of strategies should match that of set_val
            if len(strategies) != len(set_val):
                print(f'Number of strategies({len(strategies)}) must match set_val({len(set_val)})')
                return False

            for stg, val in zip(strategies, set_val):
                try:
                    # correct par type before setting
                    op = self.trader.operator
                    op.set_parameter(stg_id=stg, pars=val)
                    print(f'Parameter {val} has been set to strategy {stg}.')
                except Exception as e:
                    print(f'Can not set {val} to {stg}, Error: {e}')
                    if self.trader.debug:
                        import traceback
                        traceback.print_exc()
                    return False

        elif timing and blender:
            try:
                self.trader.operator.set_blender(blender=blender, run_timing=timing)
                print(f'Blender {blender} has been set to run timing {timing}')
            except Exception as e:
                print(f'Can not set {blender} to {timing}, Error: {e}')
                if self.trader.debug:
                    import traceback
                    traceback.print_exc()
                return False

    def do_schedule(self, arg):
        """ usage: schedule [-h]

        Show trade agenda

        optional arguments:
          -h, --help  show this help message and exit

        Examples:
        ---------
        to display current strategy task schedule:
        (QTEASY): schedule
        """

        args = self.parse_args('schedule', arg)
        if not args:
            return False

        print(f'Execution Schedule:')
        self.trader.show_schedule()

    def do_run(self, arg):
        """usage: run [STRATEGY [STRATEGY ...]] [-h]
                [--task {none,stop,sleep,pause,run_strategy,process_result,pre_open,open_market,close_market,
                acquire_live_price}]
                [--args [ARGS [ARGS ...]]]

        Run strategies manually

        positional arguments:
          strategy              strategies to run

        optional arguments:
          -h, --help            show this help message and exit
          --task {none,stop,sleep,pause,run_strategy,process_result,pre_open,open_market,close_market,
          acquire_live_price}, -t {none,stop,sleep,pause,run_strategy,process_result,pre_open,open_market,
          close_market,acquire_live_price}
                                task to run
          --args [ARGS [ARGS ...]], -a [ARGS [ARGS ...]]
                                arguments for the task to run

        Examples:
        ---------
        to run strategy "stg1":
        (QTEASY): run stg1
        to run strategy "stg1" and "stg2":
        (QTEASY): run stg1 stg2
        to run task "task1":
        (QTEASY): run --task task1
        to run task "task1" with arguments "arg1" and "arg2":
        (QTEASY): run --task task1 --args arg1 arg2

        """

        if not self.trader.debug:
            print('Running strategy manually is only available in DEBUG mode')
            return False

        args = self.parse_args('run', arg)
        if not args:
            return False

        strategies = [stg for stg_list in args.strategy for stg in stg_list] if args.strategy else []
        task = args.task
        task_args = [t_arg for arg_list in args.args for t_arg in arg_list] if args.args else []

        if not strategies and not task:
            print('Please input a valid strategy id or task name.')
            return False

        elif strategies:  # run strategies
            all_strategy_ids = self.trader.operator.strategy_ids
            if not all([strategy in all_strategy_ids for strategy in strategies]):
                invalid_stg = [stg for stg in strategies if stg not in all_strategy_ids]
                print(f'Invalid strategy id: {invalid_stg}, use "strategies" to view all valid strategy ids.')
                return False

            current_trader_status = self.trader.status
            current_broker_status = self.trader.broker.status

            self.trader.status = 'running'
            self.trader.broker.status = 'running'

            try:
                self.trader.run_task('run_strategy', strategies, run_in_main_thread=True)
            except Exception as e:
                import traceback
                print(f'Error in running strategy: {e}')
                print(traceback.format_exc())
                return

            self.trader.status = current_trader_status
            self.trader.broker.status = current_broker_status
        else:  # run tasks
            if task not in ['stop', 'sleep', 'pause', 'process_result', 'pre_open']:
                print(f'Invalid task name: {task}, please input a valid task name.')
                return False
            try:
                task_args = tuple(task_args)
                self.trader.run_task(task, *task_args, run_in_main_thread=True)
            except Exception as e:
                import traceback
                print(f'Error in running task: {e}')
                print(traceback.format_exc())
                return False

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
                            rich.print(message, end='\r')
                            if next_normal_message:
                                rich.print(message)
                        else:
                            # 在前一条信息为覆盖型信息时，在信息前插入"\n"使常规信息在下一行显示
                            if prev_message[-2:] == '_R':
                                print('\n', end='')
                            message = adjust_string_length(message,
                                                           text_width - 2,
                                                           hans_aware=True,
                                                           format_tags=True)
                            rich.print(message)
                        prev_message = message
                    # check if live price refresh timer is up, if yes, refresh live prices
                    live_price_refresh_timer += 0.05
                    if live_price_refresh_timer > watched_price_refresh_interval:
                        # 在一个新的进程中读取实时价格, 收盘后不获取
                        if self.trader.is_market_open:
                            from threading import Thread
                            t = Thread(target=self.update_watched_prices, daemon=True)
                            t.start()
                            if self.trader.debug:
                                self.trader.send_message(f'Acquiring watched prices in a new thread<{t.name}>')
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
                # TODO: 上面这种5秒定时的方式有问题，如果用户五秒后再次按下Ctrl+C，会导致Shell异常退出
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

        self.live_sys_logger = None

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

    @property
    def config(self):
        return self._config

    @property
    def _log_file_name(self):
        """ 返回视盘交易和系统记录文件的文件名

        Returns
        -------
        file_name: str
            文件名不含扩展名，系统记录文件扩展名为.lo，交易记录文件扩展名为.csv
        """
        account = get_account(self.account_id, data_source=self._datasource)
        account_name = account['user_name']
        return f'live_log_{self.account_id}_{account_name}'

    @property
    def sys_log_file_path_name(self):
        """ 返回实盘系统记录文件的路径和文件名，文件路径为QT_SYS_LOG_PATH

        Returns
        -------
        file_path_name: str
            完整的系统记录文件路径和文件名，含扩展名.log
        """

        from qteasy import QT_SYS_LOG_PATH
        sys_log_file_name = self._log_file_name + '.log'
        log_file_path_name = os.path.join(QT_SYS_LOG_PATH, sys_log_file_name)
        return log_file_path_name

    @property
    def trade_log_file_path_name(self):
        """ 返回实盘交易记录文件的路径和文件名，文件路径为QT_TRADE_LOG_PATH

        Returns
        -------
        file_path_name: str
            完整的系统记录文件路径和文件名，含扩展名.csv
        """

        from qteasy import QT_TRADE_LOG_PATH
        trade_log_file_name = self._log_file_name + '.csv'
        log_file_path_name = os.path.join(QT_TRADE_LOG_PATH, trade_log_file_name)
        return log_file_path_name

    @property
    def trade_log_file_is_valid(self):
        """ 返回交易记录文件是否存在

        同时检查交易记录文件格式是否正确，header内容是否与self.trade_log_file_header一致
        """

        log_file_path_name = self.trade_log_file_path_name

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

    def sys_log_file_exists(self):
        """ 返回系统记录文件是否存在 """
        return os.path.exists(self.sys_log_file_path_name)

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

        schedule_string = schedule.to_string()
        schedule_string = schedule_string.replace('[', '<')
        schedule_string = schedule_string.replace(']', '>')
        rich.print(schedule_string)

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

        # 初始化交易记录文件
        self.init_trade_log_file()
        # 初始化系统logger
        self.init_system_logger()

        # 初始化trader的状态，初始化任务计划
        self.status = 'sleeping'
        self._check_trade_day()
        self._initialize_schedule()
        self.send_message(f'Trader is started, running with account_id: {self.account_id}\n'
                          f' = Started on date / time: '
                          f'{self.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")}\n'
                          f' = current day is trade day: {self.is_trade_day}\n'
                          f' = running agenda (first 5 tasks): {self.task_daily_schedule[:5]}')

        market_open_day_loop_interval = 0.05
        market_close_day_loop_interval = 1
        current_date_time = self.get_current_tz_datetime()  # 产生当地时间
        current_date = current_date_time.date()

        # 在try-block中开始主循环，以抓取KeyboardInterrupt
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
                self.send_message(f'Trader is stopped.\n'
                                  f'{"=" * 20}\n')
        except KeyboardInterrupt:
            self.send_message('KeyboardInterrupt, stopping trader...')
            self.run_task('stop')
        except Exception as e:
            self.send_message(f'error occurred when running trader, error: {e}')
            if self.debug:
                import traceback
                traceback.print_exc()
        return

    def info(self, verbose=False, detail=False, system=False, width=80):
        """ 打印账户的概览，包括账户基本信息，持有现金和持仓信息

        Parameters:
        -----------
        verbose: bool, default False
            是否打印详细信息(账户信息、交易状态信息等), to be deprecated, use detail instead
        detail: bool, default False
            是否打印详细信息(账户持仓、账户现金等)，如否，则只打印账户持仓等基本信息
        system: bool, default False
            是否打印系统信息
        width: int, default 80
            打印信息的宽度

        Returns:
        --------
        None
        """

        detail = detail or verbose

        if verbose:
            import warnings
            warnings.warn('verbose argument is deprecated, use detail instead', DeprecationWarning)

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
        if system:
            # System Info
            rich.print(f'{" System Info ":=^{width}}')
            rich.print(f'{"python":<{semi_width - 20}}{sys.version}')
            rich.print(f'{"qteasy":<{semi_width - 20}}{qteasy.__version__}')
            import tushare
            rich.print(f'{"tushare":<{semi_width - 20}}{tushare.__version__}')
            try:
                import talib
                rich.print(f'{"ta-lib":<{semi_width - 20}}{talib.__version__}')
            except ImportError:
                rich.print(f'{"ta-lib":<{semi_width - 20}}not installed')
            rich.print(f'{"Local DataSource":<{semi_width - 20}}{self.datasource}')
            rich.print(f'{"System log file path":<{semi_width - 20}}'
                       f'{self.get_config("sys_log_file_path")["sys_log_file_path"]}')
            rich.print(f'{"Trade log file path":<{semi_width - 20}}'
                       f'{self.get_config("trade_log_file_path")["trade_log_file_path"]}')
        if detail:
            # Account information
            rich.print(f'{" Account Overview ":=^{width}}')
            rich.print(f'{"Account ID":<{semi_width - 20}}{self.account_id}')
            rich.print(f'{"User Name":<{semi_width - 20}}{self.account["user_name"]}')
            rich.print(f'{"Created on":<{semi_width - 20}}{self.account["created_time"]}')
            rich.print(f'{"Started on":<{semi_width - 20}}{self.init_datetime}')
            rich.print(f'{"Time zone":<{semi_width - 20}}{self.get_config("time_zone")["time_zone"]}')
            # Status and Settings
            rich.print(f'{" Status and Settings ":=^{width}}')
            rich.print(f'{"Trader Stats":<{semi_width - 20}}{self.status}')
            rich.print(f'{"Broker Status":<{semi_width - 20}}{self.broker.broker_name} / {self.broker.status}')
            rich.print(f'{"Live price update freq":<{semi_width - 20}}'
                       f'{self.get_config("live_price_acquire_freq")["live_price_acquire_freq"]}')
            rich.print(f'{"Strategy":<{semi_width - 20}}{self.operator.strategies}')
            rich.print(f'{"Strategy run frequency":<{semi_width - 20}}{self.operator.op_data_freq}')
            rich.print(f'{"Trade batch size(buy/sell)":<{semi_width - 20}}'
                       f'{self.get_config("trade_batch_size")["trade_batch_size"]} '
                       f'/ {self.get_config("sell_batch_size")["sell_batch_size"]}')
            rich.print(f'{"Delivery Rule (cash/asset)":<{semi_width - 20}}'
                       f'{self.get_config("cash_delivery_period")["cash_delivery_period"]} day / '
                       f'{self.get_config("stock_delivery_period")["stock_delivery_period"]} day')
            buy_fix = float(self.get_config('cost_fixed_buy')['cost_fixed_buy'])
            sell_fix = float(self.get_config('cost_fixed_sell')['cost_fixed_sell'])
            buy_rate = float(self.get_config('cost_rate_buy')['cost_rate_buy'])
            sell_rate = float(self.get_config('cost_rate_sell')['cost_rate_sell'])
            buy_min = float(self.get_config('cost_min_buy')['cost_min_buy'])
            sell_min = float(self.get_config('cost_min_sell')['cost_min_sell'])
            if (buy_fix > 0) or (sell_fix > 0):
                rich.print(f'{"Trade cost - fixed (B/S)":<{semi_width - 20}}¥ {buy_fix:.3f} / ¥ {sell_fix:.3f}')
            if (buy_rate > 0) or (sell_rate > 0):
                rich.print(f'{"Trade cost - rate (B/S)":<{semi_width - 20}}{buy_rate:.3%} / {sell_rate:.3%}')
            if (buy_min > 0) or (sell_min > 0):
                rich.print(f'{"Trade cost - minimum (B/S)":<{semi_width - 20}}¥ {buy_min:.3f} / ¥ {sell_min:.3f}')
            rich.print(f'{"Market time (open/close)":<{semi_width - 20}}'
                       f'{self.get_config("market_open_time_am")["market_open_time_am"]} / '
                       f'{self.get_config("market_close_time_pm")["market_close_time_pm"]}')
        # Investment Return
        print(f'{" Returns ":=^{semi_width}}')
        rich.print(f'{"Benchmark":<{semi_width - 20}}¥ '
                   f'{self.get_config("benchmark_asset")["benchmark_asset"]}')
        rich.print(f'{"Total Investment":<{semi_width - 20}}¥ {total_investment:,.2f}')
        if total_value >= total_investment:
            rich.print(f'{"Total Value":<{semi_width - 20}}¥[bold red] {total_value:,.2f}[/bold red]')
            rich.print(f'{"Total Return of Investment":<{semi_width - 20}}'
                       f'¥[bold red] {total_return_of_investment:,.2f}[/bold red]\n'
                       f'{"Total ROI Rate":<{semi_width - 20}}  [bold red]{total_roi_rate:.2%}[/bold red]')
        else:
            rich.print(f'{"Total Value":<{semi_width - 20}}¥[bold green] {total_value:,.2f}[/bold green]')
            rich.print(f'{"Total Return of Investment":<{semi_width - 20}}'
                       f'¥[bold green] {total_return_of_investment:,.2f}[/bold green]\n'
                       f'{"Total ROI Rate":<{semi_width - 20}}  [bold green]{total_roi_rate:.2%}[/bold green]')
        print(f'{" Cash ":=^{semi_width}}')
        rich.print(f'{"Cash Percent":<{semi_width - 20}}  {own_cash / total_value:.2%} ')
        rich.print(f'{"Total Cash":<{semi_width - 20}}¥ {own_cash:,.2f} ')
        rich.print(f'{"Available Cash":<{semi_width - 20}}¥ {available_cash:,.2f}')
        print(f'{" Stock Value ":=^{semi_width}}')
        rich.print(f'{"Stock Percent":<{semi_width - 20}}  {position_level:.2%}')
        if total_profit >= 0:
            rich.print(f'{"Total Stock Value":<{semi_width - 20}}¥[bold red] {total_market_value:,.2f}[/bold red]')
            rich.print(f'{"Total Stock Profit":<{semi_width - 20}}¥[bold red] {total_profit:,.2f}[/bold red]')
            rich.print(f'{"Stock Profit Ratio":<{semi_width - 20}}  [bold red]{total_profit_ratio:.2%}[/bold red]')
        else:
            rich.print(f'{"Total Stock Value":<{semi_width - 20}}¥[bold green] {total_market_value:,.2f}[/bold green]')
            rich.print(f'{"Total Stock Profit":<{semi_width - 20}}¥[bold green] {total_profit:,.2f}[/bold green]')
            rich.print(f'{"Total Profit Ratio":<{semi_width - 20}}  [bold green]{total_profit_ratio:.2%}[/bold green]')
        asset_in_pool = len(self.asset_pool)
        asset_pool_string = adjust_string_length(
                s=' '.join(self.asset_pool),
                n=width - 2,
        )
        if detail:
            print(f'{" Investment ":=^{width}}')
            rich.print(f'Current Investment Type:        {self.asset_type}')
            rich.print(f'Current Investment Pool:        {asset_in_pool} stocks, Use "pool" command to view details.\n'
                       f'=={asset_pool_string}\n')

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

        根据当前状态和消息类型，在添加到消息队列的同时，执行不同的操作：
        - 如果是覆盖型信息，在信息文字后添加_R，表示不换行，覆盖型信息不记入log文件，其他信息全部记入log文件
        - 如果是debug状态，添加<DEBUG>标签在信息头部

        Parameters
        ----------
        message: str
            消息内容
        new_line: bool, default True
            是否在消息后添加换行符
        """

        if self.live_sys_logger is None:
            logger_live = self.new_sys_logger()
        else:
            logger_live = self.live_sys_logger

        account_id = self.account_id

        time_string = self.get_current_tz_datetime().strftime("%b%d %H:%M:%S")  # 本地时间
        if self.time_zone != 'local':
            tz = f"({self.time_zone.split('/')[-1]})"
        else:
            tz = ''

        # 在message前添加时间、状态等信息
        normal_message = True
        message = f'<{time_string}{tz}>{self.status}: {message}'
        if not new_line:
            message += '_R'
            normal_message = False
        if self.debug:
            message = f'<DEBUG>{message}'

        # 处理消息，区分不同情况，需要打印、发送消息且写入log文件
        self.message_queue.put(message)
        if normal_message:
            # 如果不是覆盖型信息，同时写入log文件
            logger_live.info(message)

        if self.debug and normal_message:
            # 如果在debug模式下同时打印非覆盖型信息，确保interactive模式下也能看到debug信息
            text_width = int(shutil.get_terminal_size().columns)
            print(f'{message: <{text_width - 2}}')

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
        # correct the data types of some columns
        order_result_details['submitted_time'] = pd.to_datetime(order_result_details['submitted_time'])
        order_result_details['execution_time'] = pd.to_datetime(order_result_details['execution_time'])
        return order_result_details

    def asset_pool_detail(self):
        """ 显示asset_pool的详细信息"""
        # get all symbols from asset pool, display their master info
        asset_pool = self.asset_pool
        stock_basic = self.datasource.read_table_data(table='stock_basic')
        if stock_basic.empty:
            print(f'No stock basic data found in the datasource, acquire data with '
                  f'"qt.refill_data_source(tables="stock_basic")"')
            return
        print(stock_basic.reindex(index=asset_pool))

    def new_sys_logger(self) -> logging.Logger:
        """ 返回一个系统logger

        Returns
        -------
        logger: logging.Logger
            系统信息logger
        """

        live_handler = logging.FileHandler(
                filename=self.sys_log_file_path_name,
                mode='a',
                encoding='utf-8',
                delay=False,
        )
        logger_live = logging.getLogger('live')
        logger_live.addHandler(live_handler)
        logger_live.setLevel(logging.INFO)
        logger_live.propagate = False

        return logger_live

    def init_system_logger(self) -> None:
        """ 检查系统logger属性是否已经设置，或者log文件存在，如果没有，则初始化系统logger属性

        Returns
        -------
        None
        """
        if not self.sys_log_file_exists():
            self.live_sys_logger = None
        if self.live_sys_logger is None:
            self.live_sys_logger = self.new_sys_logger()

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
        log_file_path_name = self.trade_log_file_path_name

        if os.path.exists(log_file_path_name):
            os.remove(log_file_path_name)

        with open(log_file_path_name, mode='w', encoding='utf-8') as f:
            writer = csv.writer(f)
            row = self.trade_log_file_headers
            writer.writerow(row)

        return log_file_path_name

    def write_log_file(self, **log_content: dict):
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
        with open(self.trade_log_file_path_name, mode='a', encoding='utf-8') as f:
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
            df = pd.read_csv(self.trade_log_file_path_name)
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

        log_file_path = self.sys_log_file_path_name
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
                    self.send_message(f'<NEW ORDER {order_id}>: <{name} - {sym}> [bold red]{d}-{pos} '
                                      f'{qty} shares @ {price}[/bold red]')
                else:  # green for sell
                    self.send_message(f'<NEW ORDER {order_id}>: <{name} - {sym}> [bold green]{d}-{pos} '
                                      f'{qty} shares @ {price}[/bold green]')
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
        # 生成交易结果后，逐个检查交易结果并记录到trade_log文件并推送到信息队列（记录到system_log中）
        if result_id is not None:
            # 获取交易结果和订单信息
            result_detail = read_trade_result_by_id(result_id, data_source=self._datasource)
            order_id = result_detail['order_id']
            order_detail = read_trade_order_detail(order_id, data_source=self._datasource)
            pos, d, sym = order_detail['position'], order_detail['direction'], order_detail['symbol']
            status = order_detail['status']

            filled_qty = result_detail['filled_qty']
            filled_price = result_detail['price']
            trade_cost = result_detail['transaction_fee']

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
            symbol = position['symbol']
            # 读取持有现金
            account = get_account(self.account_id, data_source=self._datasource)
            post_cash_amount = account['cash_amount']
            post_available_cash = account['available_cash']
            name = get_symbol_names(datasource=self.datasource, symbols=symbol)[0]
            trade_log = {
                'reason':                'order',
                'order_id':              order_id,
                'position_id':           pos_id,
                'symbol':                symbol,
                'name':                  name,
                'position_type':         position['position'],
                'direction':             order_detail['direction'],
                'trade_qty':             filled_qty,
                'price':                 filled_price,
                'trade_cost':            trade_cost,
                'qty_change':            post_qty - pre_qty,
                'qty':                   post_qty,
                'available_qty_change':  post_available - pre_available,
                'available_qty':         post_available,
                'cost_change':           post_cost - pre_cost,
                'holding_cost':          post_cost,
                'cash_change':           post_cash_amount - pre_cash_amount,
                'cash':                  post_cash_amount,
                'available_cash_change': post_available_cash - pre_available_cash,
                'available_cash':        post_available_cash,
            }
            self.write_log_file(**trade_log)
            # 生成system_log
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

        # 检查账户中的成交结果，完成全部交易结果的交割
        delivery_result = process_account_delivery(
                account_id=self.account_id,
                data_source=self._datasource,
                config=self._config,
        )

        # 生成交割结果信息推送到信息队列
        for res in delivery_result:
            order_id = res['order_id']
            if res['account_id']:  # 发生了现金交割，更新了账户现金的可用数量
                pos = get_position_by_id(pos_id=res['pos_id'], data_source=self.datasource)
                symbol = pos['symbol']
                pos_type = pos['position']
                account = get_account(account_id=self.account_id, data_source=self.datasource)
                account_name = account['user_name']
                prev_amount = res['prev_amount']
                updated_amount = res['updated_amount']
                color_tag = 'bold red' if prev_amount > updated_amount else 'bold green'
                # 生成trade_log并写入文件
                trade_log = {
                    'reason':                'delivery',
                    'order_id':              order_id,
                    'position_id':           res['pos_id'],
                    'symbol':                symbol,
                    'position_type':         pos_type,
                    'name':                  get_symbol_names(datasource=self.datasource, symbols=pos['symbol'])[0],
                    'available_cash_change': updated_amount - prev_amount,
                    'available_cash':        updated_amount
                }
                self.write_log_file(**trade_log)
                # 发送system log信息
                self.send_message(f'<DELIVERED {order_id}>: <{account_name}-{self.account_id}> available cash:'
                                  f'[{color_tag}]¥{prev_amount}->¥{updated_amount}[/{color_tag}]')

            elif res['pos_id']:  # 发生了股票/资产交割，更新了资产股票的可用持仓数量
                pos = get_position_by_id(pos_id=res['pos_id'], data_source=self.datasource)
                symbol = pos['symbol']
                pos_type = pos['position']
                prev_qty = res['prev_qty']
                updated_qty = res['updated_qty']
                print(f'got result {res}')
                color_tag = 'bold red' if prev_qty > updated_qty else 'bold green'

                name = get_symbol_names(self.datasource, symbols=symbol)
                # 生成trade_log并写入文件
                trade_log = {
                    'reason':               'delivery',
                    'order_id':             order_id,
                    'position_id':          res['pos_id'],
                    'symbol':               symbol,
                    'position_type':        pos_type,
                    'name':                 get_symbol_names(datasource=self.datasource, symbols=pos['symbol'])[0],
                    'available_qty_change': updated_qty - prev_qty,
                    'available_qty':        updated_qty,
                }
                self.write_log_file(**trade_log)
                # 发送system log信息
                self.send_message(f'<DELIVERED {order_id}>: <{name}-{symbol}@{pos_type} side> available qty:'
                                  f'[{color_tag}]{prev_qty}->{updated_qty} [/{color_tag}]')

        # 获取当日实时价格
        self._update_live_price()

    def _post_close(self):
        """ 所有收盘后应该完成的任务

        1，处理当日未完成的交易信号，生成取消订单，并记录订单取消结果
        2，处理当日已成交的订单结果的交割，记录交割结果
        3，生成消息发送到消息队列
        """
        if self.debug:
            self.send_message('running task post_close')

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
            self.send_message(f'canceled unfilled orders')

        # 检查今日成交结果，完成交易结果的交割

        self.send_message('processed trade delivery')

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

    def manual_change_cash(self, amount):
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
        cash_amount, available_cash, total_invest = get_account_cash_availabilities(
                account_id=self.account_id,
                data_source=self.datasource
        )
        # 在trade_log中记录现金变动
        log_content = {
            'cash_change':           amount,
            'cash':                  cash_amount,
            'available_cash_change': amount,
            'available_cash':        available_cash,
            'reason':                'manual_change'
        }
        self.write_log_file(**log_content)
        # 发送消息通知现金变动并记录system log
        self.send_message(f'Cash amount changed to {self.account_cash}')

        return

    def manual_change_position(self, symbol, quantity, price, side=None):
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
            if self.debug:
                print('Position to be modified does not exist, new position is created!')
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
                    print(f'Can not modify position {symbol}@ {side} while {symbol}@ {position["position"]}'
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
        if self.debug:
            self.send_message(f'Changing position {position_id} {position["symbol"]}/{position["position"]} '
                              f'from {position["qty"]} to {position["qty"] + quantity}')
        # 如果减少持仓，则可用持仓数量必须足够，否则退出
        if quantity < 0 and position['available_qty'] < -quantity:
            print(f'Not enough position to decrease, available: {position["available_qty"]}, skipping operation')
            return
        prev_cost = position['cost']
        current_total_cost = prev_cost * position['qty']
        additional_cost = np.round(price * float(quantity), 2)
        new_average_cost = np.round((current_total_cost + additional_cost) / (position['qty'] + quantity), 2)
        if np.isnan(new_average_cost):
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
        # 在trade_log中记录持仓变动
        position = get_position_by_id(
                pos_id=position_id,
                data_source=self.datasource,
        )
        name = get_symbol_names(self.datasource, symbols=symbol)[0]
        log_content = {
            'reason':               'manual',
            'position_id':          position_id,
            'symbol':               position['symbol'],
            'position_type':        position['position'],  # 'long' or 'short'
            'name':                 name,
            'qty_change':           quantity,
            'qty':                  position["qty"],
            'available_qty_change': quantity,
            'available_qty':        position["available_qty"],
            'cost_change':          position['cost'] - prev_cost,
            'holding_cost':         position['cost'],
        }
        self.write_log_file(**log_content)
        # 发送消息通知持仓变动并记录system log
        self.send_message(f'Position {position["symbol"]}/{position["position"]} '
                          f'changed to {position["qty"] + quantity}')

        return

    def _update_live_price(self):
        """获取实时数据，并将实时数据更新到self.live_price中，此函数可能出现Timeout或运行失败"""
        if self.debug:
            self.send_message(f'Acquiring live price data')
        from qteasy.emfuncs import stock_live_kline_price
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
            "probabilities":   (0.9, 0.08, 0.02),
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