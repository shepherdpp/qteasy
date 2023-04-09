# coding=utf-8
# ======================================
# File:     trader.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-08
# Desc:
#   class TaskScheduler for trader to
# schedule trading tasks according to trade
# calendars and strategy rules, generate
# trading orders and submit to class Broker
# ======================================

import time
import pandas as pd

from queue import Queue
from functools import lru_cache

from qteasy import Operator


TIME_ZONE = 'Asia/Shanghai'
MARKET_CLOSE_DAY_LOOP_INTERVAL = 60  # seconds
MARKET_OPEN_DAY_LOOP_INTERVAL = 1  # seconds


class TaskScheduler(object):
    """ TaskScheduler是交易系统的核心，它负责调度交易任务，根据交易日历和策略规则生成交易订单并提交给Broker

    TaskScheduler的核心包括：
        一个task_queue，它是一个FIFO队列，任何需要执行的任务都需要被添加到队列中才会执行，执行完成后从队列中删除。
        一个task_daily_agenda，它是list of tuples, 每个tuple包含一个交易时间和一项任务，例如
        (datetime.time(9, 30), 'open_market')，表示在每天的9:30开市
    TaskScheduler的main loop定期检查task_queue中的任务，如果有任务到达，就执行任务，否则等待下一个任务到达。
    如果在交易日中，TaskScheduler会定时将task_daily_agenda中的任务添加到task_queue中。
    如果不是交易日，TaskScheduler会打印当前状态，并等待下一个交易日。

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
    init_task_daily_agenda()
        初始化每天的任务日程
    start()
        启动交易系统
    stop()
        停止交易系统
    sleep()
        休眠交易系统
    wakeup()
        唤醒交易系统
    pause()
        暂停交易系统
    resume()
        恢复交易系统
    """

    def __init__(self, account_id, operator, broker, config):
        """ 初始化TaskScheduler

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
        """
        self.account_id = account_id
        self._broker = broker
        self._operator = operator
        self._config = config

        self.task_queue = Queue()
        self.task_daily_agenda = []

        self.is_market_open = False
        self.is_trade_day = False
        self.status = 'stopped'

        self._read_account_info(account_id)

    def run(self):
        """ 交易系统的main loop """
        while True:
            self._check_trade_day()
            sleep_interval = MARKET_CLOSE_DAY_LOOP_INTERVAL if not self.is_trade_day else MARKET_OPEN_DAY_LOOP_INTERVAL
            # 只有当交易系统处于'running'状态时，才会执行任务
            if self.status != 'running':
                time.sleep(1)
                continue
            # 如果交易日，检查任务队列，如果有任务，执行任务，否则添加任务到任务队列
            if not self.task_queue.empty():
                # 如果任务队列不为空，执行任务
                task = self.task_queue.get()
                self._run_task(task)
                self.task_queue.task_done()
                if self.status == 'stopped':
                    break
                else:
                    continue

            # 非交易日会执行任务，但是不会从任务日程中添加任务到任务队列，sleep后继续循环
            if not self.is_trade_day:
                print('Today is not a trade day, sleep for a while...')
                time.sleep(sleep_interval)
                continue

            # 从任务日程中添加任务到任务队列，sleep后继续循环
            current_time = pd.to_datetime('now', utc=True).tz_convert(TIMEZONE).time()
            self._add_task_from_agenda(current_time)
            time.sleep(sleep_interval)

    def _start(self):
        """ 启动交易系统 """
        self.status = 'running'

    def _stop(self):
        """ 停止交易系统 """
        self.status = 'stopped'

    def _sleep(self):
        """ 休眠交易系统 """
        self.status = 'sleeping'

    def _wakeup(self):
        """ 唤醒交易系统 """
        self.status = 'running'

    def _pause(self):
        """ 暂停交易系统 """
        self.status = 'paused'

    def _resume(self):
        """ 恢复交易系统 """
        self.status = 'running'

    def _run_strategy(self, strategy_ids=None):
        """ 运行交易策略，生成交易信号，解析信号为交易订单，并将交易订单发送给交易所

        Parameters
        ----------
        strategy_ids: tuple of int
            交易策略ID列表
        """
        if not self.is_market_open:
            return
        # TODO: set up operator, run operator strategies, and get signals
        self._operator.create_signal()

    def _pre_open(self):
        """ 开市前 """
        self._initialize_agenda(operator, config)

    def _market_open(self):
        """ 开市 """
        self.is_market_open = True

    def _market_close(self):
        """ 收市 """
        self.is_market_open = False

    def _run_task(self, task, **kwargs):
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

        if task not in AVAILABLE_TASKS.keys():
            raise ValueError(f'Invalid task name: {task}')

        task_func = AVAILABLE_TASKS[task]
        task_func(self, **kwargs)

    def _check_trade_day(self):
        """ 检查当前日期是否是交易日 """
        current_date = pd.to_datetime('now', utc=True).tz_convert(TIMEZONE).date()
        from qteasy.utilfuncs import is_market_trade_day
        self.is_trade_day = is_market_trade_day(current_date, self._config['market'])

    def _add_task_to_queue(self, task):
        """ 添加任务到任务队列

        Parameters
        ----------
        task: str
            任务名称
        """
        self.task_queue.put(task)

    def _add_task_from_agenda(self, current_time):
        """ 根据当前时间从任务日程中添加任务到任务队列，只有到时间时才添加任务

        Parameters
        ----------
        current_time: datetime.time
            当前时间, 只有任务计划时间小于等于当前时间时才添加任务
        """
        # 对比当前时间和任务日程中的任务时间，如果任务时间小于等于当前时间，添加任务到任务队列
        for task_time, task in self.task_daily_agenda:
            if task_time <= current_time:
                self._add_task_to_queue(task)

    def _initialize_agenda(self, operator, config):
        """ 初始化交易日的任务日程 """
        from qteasy.trading_util import create_daily_task_agenda
        self.task_daily_agenda = create_daily_task_agenda(operator, config)

    def _read_account_info(self, account_id):
        """ 读取账户信息

        Parameters
        ----------
        account_id: int
            账户ID
        """
        pass

    AVAILABLE_TASKS = {
        'pre_open':     _pre_open,
        'open_market':  _market_open,
        'close_market': _market_close,
        'post_close':   _post_close,
        'run_strategy': _run_strategy,
        'start':        _start,
        'stop':         _stop,
        'sleep':        _sleep,
        'wakeup':       _wakeup,
        'pause':        _pause,
        'resume':       _resume,
    }
