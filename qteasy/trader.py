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
from threading import Thread
from queue import Queue
from functools import lru_cache

import pandas as pd

from qteasy import Operator, DataSource
from qteasy.utilfuncs import str_to_list
from qteasy.broker import Broker, QuickBroker
from qteasy.trade_recording import get_account, get_account_positions, get_account_position_details
from qteasy.trade_recording import get_account_cash_availabilities, get_position_ids, query_trade_orders
from qteasy.trade_recording import read_trade_order_detail, read_trade_results_by_order_id
from qteasy.trading_util import parse_trade_signal, submit_order, record_trade_order, process_trade_result
from qteasy.trading_util import process_trade_delivery, create_daily_task_agenda

# TODO: 交易系统的配置信息，从QT_CONFIG中读取
TIME_ZONE = 'Asia/Shanghai'

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

        default_config = {
            'market_open_time_am':  '09:30:00',
            'market_close_time_pm': '15:30:00',
            'market_open_time_pm':  '13:00:00',
            'market_close_time_am': '11:30:00',
            'exchange':             'SSE',
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
            'asset_pool':           None,
            'market_close_day_loop_interval': 0,
            'market_open_day_loop_interval': 0,
            'strategy_open_close_timing_offset': 1,  # minutes, 策略在开盘和收盘运行时的偏移量
        }

        self.account_id = account_id
        self._broker = broker
        self._operator = operator
        self._config = default_config
        self._config.update(config)
        self._datasource = datasource
        self._asset_pool = str_to_list(self._config['asset_pool'])

        self.task_queue = Queue()
        self.message_queue = Queue()

        self.task_daily_agenda = []

        self.is_trade_day = False
        self.status = 'stopped'

        self.account = get_account(self.account_id, self._datasource)

        self.debug = debug

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
    def account_overview(self):
        """ 账户的概览，包括账户的现金和持仓 """
        return {
            'cash': self.account_cash,
            'positions': self.account_positions
        }

    @property
    def account_cash(self):
        """ 账户的现金, 包括持有现金和可用现金 """
        from qteasy.trade_recording import get_account_cash_availabilities
        return get_account_cash_availabilities(self.account_id, data_source=self._datasource)

    @property
    def account_positions(self):
        """ 账户的持仓，一个tuple,包含两个ndarray，包括每种股票的持有数量和可用数量 """
        from qteasy.trade_recording import get_account_position_availabilities
        shares = self.asset_pool

        positions = get_account_position_details(
                self.account_id,
                shares=shares,
                data_source=self._datasource
        )
        return positions

    @property
    def history_orders(self):
        """ 账户的历史订单 """
        from qteasy.trade_recording import query_trade_orders
        return query_trade_orders(self.account_id, data_source=self._datasource)

    def trade_results(self):
        """ 账户的交易结果 """
        from qteasy.trade_recording import read_trade_results_by_order_id
        from qteasy.trade_recording import query_trade_orders
        order_ids = query_trade_orders(
                self.account_id,
                status='filled',
                data_source=self._datasource
        ).order_id.values
        return list(map(read_trade_results_by_order_id, order_ids))

    def run(self):
        """ 交易系统的main loop：

        1，检查task_queue中是否有任务，如果有任务，则提取任务，根据当前status确定是否执行任务，如果可以执行，则执行任务，否则忽略任务
        2，如果当前是交易日，检查当前时间是否在task_daily_agenda中，如果在，则将任务添加到task_queue中
        3，如果当前是交易日，检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
        """
        self._check_trade_day()
        self._initialize_agenda()
        self.status = 'running'
        self.post_message(f'Trader is running with account_id: {self.account_id}')
        market_open_day_loop_interval = self._config['market_open_day_loop_interval']
        market_close_day_loop_interval = self._config['market_close_day_loop_interval']
        while self.status != 'stopped':
            self._check_trade_day()
            sleep_interval = market_close_day_loop_interval if not self.is_trade_day else market_open_day_loop_interval
            # 检查任务队列，如果有任务，执行任务，否则添加任务到任务队列
            if not self.task_queue.empty():
                # 如果任务队列不为空，执行任务
                white_listed_tasks = self.TASK_WHITELIST[self.status]
                task = self.task_queue.get()
                self.post_message(f'task queue is not empty, taking next task from queue: {task}')
                if task not in white_listed_tasks:
                    message = f'task: {task} cannot be executed in current status: {self.status}'
                    self.post_message(message)
                    self.task_queue.task_done()
                    continue
                self.run_task(task)
                self.task_queue.task_done()
                continue

            # 从任务日程中添加任务到任务队列
            current_time = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).time()
            self._add_task_from_agenda(current_time)

            # 检查broker的result_queue中是否有交易结果，如果有，则添加"process_result"任务到task_queue中
            if not self.broker.result_queue.empty():
                result = self.broker.result_queue.get()
                self.add_task('process_result', result=result)

            time.sleep(sleep_interval)

    def post_message(self, message):
        """ 发送消息到消息队列, 在消息前添加必要的信息如日期、时间等

        Parameters
        ----------
        message: str
            消息内容
        """
        if not isinstance(message, str):
            raise TypeError('message should be a str')
        time_string = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).strftime('%Y-%m-%d %H:%M:%S')
        message = f'[{time_string}]-{self.status}: {message}'
        if self.debug:
            print(message)
        self.message_queue.put(message)

    def add_task(self, task, **kwargs):
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
        if not isinstance(kwargs, dict):
            raise TypeError('kwargs should be a dict')

        if task not in self.AVAILABLE_TASKS:
            raise ValueError('task {} is not available'.format(task))

        if kwargs:
            task = (task, kwargs)
        self.post_message(f'adding task: {task}')
        self._add_task_to_queue(task)

    # definition of tasks
    def _start(self):
        """ 启动交易系统 """
        self.post_message('starting Trader')
        self.status = 'running'

    def _stop(self):
        """ 停止交易系统 """
        self.post_message('stopping Trader')
        self.status = 'stopped'

    def _sleep(self):
        """ 休眠交易系统 """
        self.post_message('Putting Trader to sleep')
        self.status = 'sleeping'

    def _wakeup(self):
        """ 唤醒交易系统 """
        self.post_message('Waking up Trader')
        self.status = 'running'

    def _pause(self):
        """ 暂停交易系统 """
        self.post_message('Pausing Trader')
        self.status = 'paused'

    def _resume(self):
        """ 恢复交易系统 """
        self.post_message('Resuming Trader')
        self.status = 'running'

    def _run_strategy(self, strategy_ids=None):
        """ 运行交易策略

        1，读取实时数据，设置operator的数据分配
        2，根据strtegy_id设定operator的运行模式，生成交易信号
        3，解析信号为交易订单，并将交易订单发送到交易所的订单队列
        4，将交易订单的ID保存到数据库，更新账户和持仓信息
        5，生成交易订单状态信息推送到信息队列

        Parameters
        ----------
        strategy_ids: tuple of int
            交易策略ID列表
        """
        if not self.is_market_open:
            return

        operator = self._operator
        signal_type = operator.signal_type
        shares = self.asset_pool
        prices = get_current_prices()  # 获取实时价格 TODO: implement get_current_prices
        own_amounts = self.account_positions
        own_cash = self.account_cash
        config = self._config
        # 读取实时数据,设置operator的数据分配,创建trade_data
        hist_op, hist_ref, invest_cash_plan = check_and_prepare_real_time_data(operator, config)
        self.post_message(f'read real time data and set operator data allocation')

        if operator.op_type == 'batch':
            raise KeyError(f'Operator can not work in live mode when its operation type is "batch", set '
                           f'"Operator.op_type = \'step\'"')
        else:
            op_signal = operator.create_signal(
                    trade_data=trade_data,
                    sample_idx=-1,
                    price_type_idx=0
            )  # 生成交易清单
            self.post_message(f'ran strategy and created signal: {op_signal}')

        # 解析交易信号
        symbols, positions, directions, quantities = parse_trade_signal(
                signals=op_signal,
                signal_type=signal_type,
                shares=shares,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                config=config
        )
        submitted_qty = 0
        for sym, pos, d, qty in zip(symbols, positions, directions, quantities):
            pos_id = get_position_ids(account_id=account_id,
                                      symbol=sym,
                                      position_type=pos,
                                      data_source=data_source)

            # 生成交易订单dict
            trade_order = {
                'pos_id':         pos_id,
                'direction':      d,
                'order_type':     order_type,
                'qty':            qty,
                'price':          get_price(),
                'submitted_time': None,
                'status':         'created',
            }
            order_id = record_trade_order(trade_order, data_source=self._datasource)
            # 逐一提交交易信号
            if submit_order(order_id=order_id, data_source=self._datasource) is not None:
                self._broker.order_queue.put(trade_order)
                self.post_message(f'submitted order to broker: {trade_order}')
                # 记录已提交的交易数量
                submitted_qty += qty

        return submitted_qty

    def _process_result(self, result):
        """ 从result_queue中读取并处理交易结果

        1，处理交易结果，更新账户和持仓信息
        2，处理交易结果的交割，记录交割结果（未达到交割条件的交易结果不会被处理）
        4，生成交易结果信息推送到信息队列
        """
        process_trade_result(result, data_source=self._datasource)
        self.post_message(f'processed trade result: {result}')
        process_trade_delivery(
                account_id=self.account_id,
                data_source=self._datasource,
                config=self._config,
        )

    def _pre_open(self):
        """ 开市前, 生成交易日的任务计划，生成消息发送到消息队列"""
        self._initialize_agenda()
        self.post_message('initialized daily task agenda')

    def _post_close(self):
        """ 收市后例行操作：

        1，处理当日未完成的交易信号，生成取消订单，并记录订单取消结果
        2，处理当日已成交的订单结果的交割，记录交割结果
        3，生成消息发送到消息队列
        """
        # 检查task_queue中是否有任务，如果有，全部都是未处理的交易信号，生成取消订单
        if not self.task_queue.empty():
            self.post_message('processing unprocessed signals')
            while not self.task_queue.empty():
                task = self.task_queue.get()
                self.run_task(task)  # TODO: 这里需要修改，生成取消订单
                self.task_queue.task_done()
        # 检查今日成交订单，确认是否有"部分成交"以及"已提交"的订单，如果有，生成取消订单，取消尚未成交的部分
        self.post_message('processing partially filled orders')
        partially_filled_orders = query_trade_orders(
                account_id=self.account_id,
                status='partially-filled',
                data_source=self._datasource,
        )
        unfilled_orders = query_trade_orders(
                account_id=self.account_id,
                status='submitted',
                data_source=self._datasource,
        )
        orders_to_be_canceled = partially_filled_orders + unfilled_orders
        if order in orders_to_be_canceled:
            # 部分成交订单不为空，需要生成一条新的交易记录，用于取消订单中的未成交部分，并记录订单结果
            order_id = order['order_id']
            order_details = read_trade_order_detail(order_id=order_id, data_source=self._datasource)
            order_results = read_trade_results_by_order_id(order_id=order_id, data_source=self._datasource)
            total_filled_qty = order_results['filled_qty'].sum()
            already_canceled_qty = order_results['canceled_qty'].sum()
            if already_canceled_qty > 0:
                raise RuntimeError(f'order status wrong: canceled qty should be 0 unless order is canceled!')
            remaining_qty = order_details['qty'] - total_filled_qty
            if remaining_qty <= 0:
                raise RuntimeError(f'order status wrong: remaining qty should be larger than '
                                   f'when order is partially filled')
            result_of_cancel = {
                'order_id': order['order_id'],
                'filled_qty': total_filled_qty,
                'price': order_details['price'],
                'transaction_fee': 0.,
                'canceled_qty': remaining_qty,
                'delivery_amount': 0,
                'delivery_status': 'ND',
            }
            process_trade_result(
                    raw_trade_result=result_of_cancel,
                    data_source=self._datasource,
                    config=self._config
            )
            self.post_message(f'processed trade result: {result_of_cancel}')
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
        self.is_market_open = True
        self.post_message('market is open')
        Thread(target=self.broker.run).start()

    def _market_close(self):
        """ 收市时操作：

        1，停止broker的主循环，将broker的status设置为stopped
        2，生成消息发送到消息队列
        """
        self.is_market_open = False
        self.post_message('market is closed')
        self.broker.status = 'stopped'

    def run_task(self, task, **kwargs):
        """ 运行任务

        Parameters
        ----------
        task: str
            任务名称
        **kwargs: dict
            任务参数
        """

        if task is None:
            return
        if not isinstance(task, str):
            raise ValueError(f'task must be a string, got {type(task)} instead.')

        if task not in self.AVAILABLE_TASKS.keys():
            raise ValueError(f'Invalid task name: {task}')

        task_func = self.AVAILABLE_TASKS[task]
        self.post_message(f'will run task: {task} with kwargs: {kwargs} in function: {task_func.__name__}')
        if kwargs:
            task_func(self, **kwargs)
        else:
            task_func(self)

    def _check_trade_day(self):
        """ 检查当前日期是否是交易日 """
        current_date = pd.to_datetime('now', utc=True).tz_convert(TIME_ZONE).date()
        from qteasy.utilfuncs import is_market_trade_day
        self.is_trade_day = is_market_trade_day(current_date, self._config['exchange'])

    def _add_task_to_queue(self, task):
        """ 添加任务到任务队列

        Parameters
        ----------
        task: str
            任务名称
        """
        self.post_message(f'putting task {task} into task queue')
        self.task_queue.put(task)

    def _add_task_from_agenda(self, current_time):
        """ 根据当前时间从任务日程中添加任务到任务队列，只有到时间时才添加任务

        Parameters
        ----------
        current_time: datetime.time
            当前时间, 只有任务计划时间小于等于当前时间时才添加任务
        """
        # 对比当前时间和任务日程中的任务时间，如果任务时间小于等于当前时间，添加任务到任务队列
        for task_tuple in self.task_daily_agenda:
            task_time = task_tuple[0]
            task_time = pd.to_datetime(task_time, utc=True).tz_convert(TIME_ZONE).time()
            if task_time <= current_time:
                if len(task_tuple) > 2:
                    task = task_tuple[1, 2]
                else:
                    task = task_tuple[1]
                self.post_message(f'current time {current_time} >= task time {task_time} adding task: {task} from agenda')
                self._add_task_to_queue(task)

    def _initialize_agenda(self):
        """ 初始化交易日的任务日程 """
        # 如果不是交易日，直接返回
        if not self.is_trade_day:
            return
        if self.task_daily_agenda is not None:
            # 如果任务日程已经初始化，直接返回
            return
        self.task_daily_agenda = create_daily_task_agenda(
                self.operator,
                self._config
        )

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
    }

    TASK_WHITELIST = {
        'stopped':     ['start'],
        'running':     ['stop', 'sleep', 'pause', 'run_strategy', 'process_result', 'pre_open',
                        'post_close', 'open_market', 'close_market'],
        'sleeping':    ['wakeup', 'stop'],
        'paused':      ['resume', 'stop'],
    }

