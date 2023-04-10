# coding=utf-8
# ======================================
# File:     broker.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-09
# Desc:
#   class BaseBroker for trader to submit
# trading orders and get trading results
# Broker classes are supposed to be
# inherited from BaseBroker, representing
# different trading platforms or brokers
# ======================================

from queue import Queue
from abc import abstractmethod, ABCMeta


class BaseBroker(object):
    """ Broker是交易所的抽象，它接受交易订单并返回交易结果

    BaseBroker定义了Broker的基本接口，所有的Broker都必须继承自BaseBroker，
    以实现不同交易所的接口
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.order_queue = Queue()
        self.result_queue = Queue()

    def submit_order(self, orders):
        self.order_queue.put(orders)

    def get_result(self):
        """ 交易所处理交易订单并获取交易结果 """
        pass


class QuickBroker(BaseBroker):
    """ QuickBroker接到交易订单后，立即返回交易结果，且结果永远是全部成交
    """
    def __init__(self):
        super(QuickBroker, self).__init__()

    def get_result(self):
        orders = self.order_queue.get()
        results = []
        for order in orders:
            results.append(self._quick_trade(order))
        self.result_queue.put(results)
        return results

    @staticmethod
    def _quick_trade(order):
        """ 交易所处理交易订单并获取交易结果 """
        return order