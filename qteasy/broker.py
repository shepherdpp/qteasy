# coding=utf-8
# ======================================
# File:     broker.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-09
# Desc:
#   class Broker for trader to submit
# trading orders and get trading results
# Broker classes are supposed to be
# inherited from Broker, representing
# different trading platforms or brokers
# ======================================

from queue import Queue
from abc import abstractmethod, ABCMeta
from concurrent.futures import ThreadPoolExecutor

import pandas as pd


class Broker(object):
    """ Broker是交易所的抽象，它接受交易订单并返回交易结果

    BaseBroker定义了Broker的基本接口，所有的Broker都必须继承自BaseBroker，
    以实现不同交易所的接口

    Attributes:
    -----------
    order_queue: Queue
        交易订单队列，每个交易订单都是一个list，包含多个交易订单
    result_queue: Queue
        交易结果队列，每个交易结果都是一个list，包含多个交易结果
    status: str
        Broker的状态，可以是 'init', 'running', 'stopped', 'paused'
        - init: Broker刚刚创建，还没有开始运行
        - running: Broker正在运行, 接受交易订单并返回交易结果
        - stopped: Broker已经停止运行, 停止所有操作，未完成的订单将被丢弃，并退出主循环
        - paused: Broker暂停运行，未完成的订单将被暂停，可以接受交易订单，但不会返回交易结果

    Methods:
    --------
    run()
        Broker的主循环，从order_queue中获取交易订单并处理，获得交易结果并放入result_queue中
    get_result(order): abstract method
        交易所处理交易订单并获取交易结果,在子类中必须实现这个方法
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.broker_name = 'BaseBroker'
        self.user_name = ''
        self.password = ''
        self.token = ''
        self.status = 'init'  # init, running, stopped, paused

        self.order_queue = Queue()
        self.result_queue = Queue()

    def run(self):
        """ Broker的主循环，从order_queue中获取交易订单并处理，获得交易结果并放入result_queue中
        order_queue中的每一个交易订单都由get_result函数来处理并获取交易结果，get_result函数
        的执行过程是IO intensive的，因此需要使用ThreadPoolExecutor来并行处理交易订单
        """
        try:
            while self.status != 'stopped':
                # 如果Broker处于暂停状态，则不处理交易订单
                if self.status == 'paused':
                    continue
                # 如果order_queue为空，则不处理交易订单
                if self.order_queue.empty():
                    continue
                # 使用ThreadPoolExecutor并行调用get_result函数处理交易订单，将结果put到result_queue中
                with ThreadPoolExecutor(max_workers=10) as executor:
                    while not self.order_queue.empty():
                        # debug
                        print(f'Broker {self.broker_name} is running, got order from order queue, taking order...')
                        order = self.order_queue.get()
                        # debug
                        print(f'Broker {self.broker_name} is running, will submit order {order} to get result...')
                        executor.submit(self.get_result, order)
                        self.order_queue.task_done()
                    # 获取交易结果并将其放入result_queue中
                for future in executor.as_completed():
                    self.result_queue.put(future.result())
            else:
                # 如果Broker正常退出，处理尚未完成的交易订单
                # TODO: 完善下面的代码，下面代码由Github Copilot自动生成，但是还不完善
                while not self.order_queue.empty():
                    order = self.order_queue.get()
                    self.result_queue.put(self.get_result(order))
                    self.order_queue.task_done()
        except KeyboardInterrupt:
            # 如果Broker被用户强制退出，处理尚未完成的交易订单
            # TODO: 完善下面的代码，下面代码由Github Copilot自动生成，但是还不完善
            self.status = 'stopped'
            while not self.order_queue.empty():
                order = self.order_queue.get()
                self.result_queue.put(self.get_result(order))
                self.order_queue.task_done()

    @abstractmethod
    def get_result(self, order):
        """ 交易所处理交易订单并获取交易结果

        抽象方法，必须在子类中实现

        Parameters:
        -----------
        order: dict
            交易订单dict的key包括 ['order_id', 'pos_id', 'direction', 'order_type', 'qty', 'price',
                     'submitted_time', 'status']

        Returns:
        --------
        result: dict
            交易结果dict的key包括 ['order_id', 'filled_qty', 'price', 'transaction_fee', 'execution_time',
                        'canceled_qty', 'delivery_amount', 'delivery_status'
        """
        pass


class QuickBroker(Broker):
    """ QuickBroker接到交易订单后，立即返回交易结果，且结果永远是全部成交

    交易费用根据交易方向和交易价格计算，滑点是按照百分比计算的，比如0.01表示1%
    """
    def __init__(self, fee_rate_buy=0.0001, fee_rate_sell=0.0003):
        super(QuickBroker, self).__init__()
        self.broker_name = 'QuickBroker'
        self.fee_rate_buy = fee_rate_buy
        self.fee_rate_sell = fee_rate_sell

    def get_result(self, order):
        """ 订单立即全部成交 """
        from time import sleep
        from random import random
        from qteasy.trading_util import TIMEZONE
        # debug
        print(f'QuickBroker: get_result: got order: \n{order}')
        qty = order['qty']
        price = order['price']
        if order['direction'] == 'buy':
            transaction_fee = qty * price * self.fee_rate_buy
        elif order['direction'] == 'sell':
            transaction_fee = qty * price * self.fee_rate_sell
        else:
            raise RuntimeError('invalid direction: {}'.format(order['direction']))
        result = {
            'order_id': order['order_id'],
            'filled_qty': qty,
            'price': price,
            'transaction_fee': transaction_fee,
            'execution_time': pd.to_datetime('now').tz_convert(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'),
            'canceled_qty': 0,
            'delivery_amount': 0,
            'delivery_status': 'ND',
        }
        # debug
        print(f'QuickBroker: get_result: return result: \n{result}')
        sleep(random() * 5)  # 模拟交易所处理订单的时间,最长5，平均2.5秒
        return result
