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


from abc import abstractmethod, ABCMeta

from qteasy.trader import TaskScheduler


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

