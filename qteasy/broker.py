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
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import time


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
        self.debug = False

        self.order_queue = Queue()
        self.result_queue = Queue()

    def run(self):
        """ Broker的主循环，从order_queue中获取交易订单并处理，获得交易结果并放入result_queue中
        order_queue中的每一个交易订单都由get_result函数来处理并获取交易结果，get_result函数
        的执行过程是IO intensive的，因此需要使用ThreadPoolExecutor来并行处理交易订单
        """
        if self.debug:
            print(f'[DEBUG]: Broker {self.broker_name} is running...')
        self.status = 'init'
        try:
            while self.status != 'stopped':
                time.sleep(1)
                # 如果Broker处于暂停状态，则不处理交易订单
                if self.status == 'paused':
                    continue
                # 如果order_queue为空，则不处理交易订单
                if self.order_queue.empty():
                    continue
                # 使用ThreadPoolExecutor并行调用get_result函数处理交易订单，将结果put到result_queue中
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    while not self.order_queue.empty():
                        if self.debug:
                            print(f'[DEBUG]: Broker {self.broker_name} is running, '
                                  f'got order from order queue, taking order from queue'
                                  f'({self.order_queue.unfinished_tasks} orders)...')
                        order = self.order_queue.get()
                        if self.debug:
                            print(f'[DEBUG]: Broker {self.broker_name} is running, will submit order {order} to get result...')
                        futures.append(executor.submit(self.get_result, order))
                        self.order_queue.task_done()
                    # 获取交易结果并将其放入result_queue中
                    for future in as_completed(futures):
                        result = future.result()
                        if self.debug:
                            print(f'[DEBUG]: Broker {self.broker_name} is running, got result {result} and put to result queue...')
                        self.result_queue.put(result)
            else:
                # 如果Broker正常退出，处理尚未完成的交易订单
                # TODO: 完善下面的代码，下面代码由Github Copilot自动生成，但是还不完善
                if self.debug:
                    print(f'[DEBUG]: Broker {self.broker_name} is stopped, will process unfinished orders...')
                while not self.order_queue.empty():
                    order = self.order_queue.get()
                    self.result_queue.put(self.get_result(order))
                    self.order_queue.task_done()
        except KeyboardInterrupt:
            # 如果Broker被用户强制退出，处理尚未完成的交易订单
            # TODO: 完善下面的代码，下面代码由Github Copilot自动生成，但是还不完善
            if self.debug:
                print('B[DEBUG]: roker is stopped by user, will stop broker and process unfinished orders...')
            self.status = 'stopped'
            while not self.order_queue.empty():
                order = self.order_queue.get()
                self.result_queue.put(self.get_result(order))
                self.order_queue.task_done()
        except Exception as e:
            # 如果Broker出现异常，处理尚未完成的交易订单
            if self.debug:
                print(f'[DEBUG]: Broker is stopped by exception{e}, will stop broker and process unfinished orders...')
                import traceback
                traceback.print_exc()
            self.status = 'stopped'
            raise e

    def get_result(self, order):
        """ 交易所处理交易订单并获取交易结果

        抽象方法，可以由用户在子类中实现，返回的信息包括filled_qty, transaction_fee, canceled_qty

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
        from time import sleep
        from random import random, choice
        from qteasy.trading_util import TIMEZONE
        if self.debug:
            print(f'[DEBUG]: Broker({self.broker_name}) method: get_result():\nsubmit order components:\n'
                  f'quantity:{order["qty"]}\norder_price={order["price"]}\norder_direction={order["direction"]}\n')
        result_type, qty, filled_price, fee = self.transaction_result(
                order_qty=order['qty'],
                order_price=order['price'],
                direction=order['direction'],
        )
        if self.debug:
            print(f'[DEBUG]: Broker({self.broker_name}) method: get_result(): got transaction result\n'
                  f'result_type={result_type}, \nqty={qty}, \nfilled_price={filled_price}, \nfee={fee}')
        # 圆整qty、filled_qty和fee # TODO: 这里的round函数小数位数应该是可配置的
        qty = round(qty, 2)
        filled_price = round(filled_price, 2)
        transaction_fee = round(fee, 2)

        filled_qty = 0
        canceled_qty = 0
        if result_type == 'filled':
            filled_qty = qty
        elif result_type == 'canceled':
            canceled_qty = qty
        else:
            raise ValueError(f'Unknown result_type: {result_type}, should be one of ["filled", "canceled"]')

        current_datetime = pd.to_datetime('now', utc=True).tz_convert(TIMEZONE)
        result = {
            'order_id':        order['order_id'],
            'filled_qty':      filled_qty,
            'price':           filled_price,
            'transaction_fee': transaction_fee,
            'execution_time':  current_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'canceled_qty':    canceled_qty,
            'delivery_amount': 0,
            'delivery_status': 'ND',
        }
        if self.debug:
            print(f'[DEBUG]: Broker({self.broker_name}) method get_result(): built up result:\n{result}')
        return result

    @abstractmethod
    def transaction_result(self, order_qty, order_price, direction):
        """ 交易所处理交易订单并获取交易结果, 抽象方法，需要由用户在子类中实现

        Parameters:
        -----------
        order_qty: float
            交易订单数量
        order_price: float
            交易订单价格
        direction: str
            交易订单方向，'buy' 或者 'sell'

        Returns:
        --------
        result_type: str
            交易结果类型，'filled' - 成交, 'canceled' - 取消
        qty: float
            成交/取消数量
        price: float
            成交价格, 如果是取消交易，价格为0或任意数字
        fee: float
            交易费用
        """
        pass


class SimpleBroker(Broker):
    """ SimpleBroker接到交易订单后，立即返回交易结果
    交易结果总是完全成交，交易费用固定为5元
    """

    def __init__(self):
        super(SimpleBroker, self).__init__()
        self.broker_name = 'SimpleBroker'

    def transaction_result(self, order_qty, order_price, direction):
        """ 订单立即成交

        Returns:
        --------
        result_type: str
            交易结果类型，'filled' - 成交
        qty: float
            成交数量
        price: float
            成交价格
        fee: float
            交易费用
        """
        qty = order_qty
        price = order_price
        fee: float = 5.
        return 'filled', qty, price, fee


class RandomBroker(Broker):
    """ RandomBroker接到交易订单后，随机等待一段时间再返回交易结果。交易结果随机，包含完全成交、部分成交和取消交易

    交易费用根据交易方向和交易价格计算，滑点是按照百分比计算的，比如0.01表示1%
    """

    def __init__(self, fee_rate_buy=0.0001, fee_rate_sell=0.0003):
        super(RandomBroker, self).__init__()
        self.broker_name = 'RandomBroker'
        self.fee_rate_buy = fee_rate_buy
        self.fee_rate_sell = fee_rate_sell

    def transaction_result(self, order_qty, order_price, direction):
        """ 订单随机成交

        Returns:
        --------
        result_type: str
            交易结果类型，'filled' - 成交, 'canceled' - 取消
        qty: float
            成交/取消数量
        price: float
            成交价格, 如果是取消交易，价格为0或任意数字
        fee: float
            交易费用
        """
        from time import sleep
        from random import random, choice
        from qteasy.trading_util import TIMEZONE
        result_type = choice(['filled', 'canceled'])
        trade_delay = random() * 5  # 模拟交易所处理订单的时间,最长5，平均2.5秒
        price_deviation = random() * 0.01  # 模拟交易所的滑点，最大1%，平均0.5%

        sleep(trade_delay)

        if result_type == 'filled':
            filled_proportion = choice([0.5, 0.75, 1.0])  # 模拟交易所的部分成交，最多成交1.0，最少成交0.5
            qty = order_qty * filled_proportion
            if direction == 'buy':
                order_price = order_price * (1 + price_deviation)
                transaction_fee = qty * order_price * self.fee_rate_buy
            elif direction == 'sell':
                order_price = order_price * (1 - price_deviation)
                transaction_fee = qty * order_price * self.fee_rate_sell
            else:
                raise RuntimeError('invalid direction: {}'.format(order['direction']))
        else: # result_type == 'canceled'
            transaction_fee = 0
            order_price = 0
            qty = order_qty

        return result_type, qty, order_price, transaction_fee
