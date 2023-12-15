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
import numpy as np
import time

from qteasy import QT_CONFIG

CASH_DECIMAL_PLACES = QT_CONFIG['cash_decimal_places']
AMOUNT_DECIMAL_PLACES = QT_CONFIG['amount_decimal_places']


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
        self.is_registered = False

        self.order_queue = Queue()
        self.result_queue = Queue()
        self.broker_messages = Queue()

    def register(self, debug=False, **kwargs):
        """ register由broker的trader对象发起，作用是设置broker的状态为is_registered
        将broker连接到正确的交易平台，注册交易信息，输入账号、密码等完成登录

        只有is_registered == True时，broker才能够运行

        Parameters
        ----------
        debug: bool, default: False
            是否进入debug mode
        kwargs:

        Return
        ------
        None
        """
        # TODO: implement this function
        self.is_registered = True
        self.debug = debug

    def run(self):
        """ Broker的主循环，从order_queue中获取交易订单并处理，获得交易结果并放入result_queue中
        order_queue中的每一个交易订单都由get_result函数来处理并获取交易结果，get_result函数
        的执行过程是IO intensive的，因此需要使用ThreadPoolExecutor来并行处理交易订单
        """
        if not self.is_registered:
            raise RuntimeError(f'broker is not registered!')
        if self.debug:
            self.post_message(f'is running...')
        self.status = 'init'
        try:
            while self.status != 'stopped':
                time.sleep(0.05)
                # 如果Broker处于暂停状态，则不处理交易订单
                if self.status == 'paused':
                    continue
                # 如果order_queue为空，则不处理交易订单
                if self.order_queue.empty():
                    continue

                # 使用ThreadPoolExecutor并行调用get_result函数处理交易订单，将结果put到result_queue中
                # TODO: Broker的结构需改进。self.get_result()函数应该从始至终只处理一个订单，并且在处理订单的
                #  过程中可以多次返回结果，将结果放入一个内部result_queue中，直到订单处理完成，或者订单被取消，
                #  或者订单处理失败，此时才返回None。
                #  Broker的主循环从内部result_queue中获取结果，添加必要的信息之后，将结果放入result_queue中。
                #  Broker的主循环从order_queue中获取订单，为每一个订单在一个单独的thread中调用self.get_result()。
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    while not self.order_queue.empty():
                        # TODO: 此处改进，只有order_queue中的订单被Broker读取后，才修改订单的状态为'submitted'，之前状态为'created'
                        order = self.order_queue.get()
                        if self.debug:
                            self.post_message(f'is running, '
                                              f'got order(ID) {order["order_id"]} from order queue'
                                              f'({self.order_queue.unfinished_tasks} orders left in the queue)...')
                        futures.append(executor.submit(self.get_result, order))
                        self.order_queue.task_done()
                    # 获取交易结果并将其放入result_queue中
                    for future in as_completed(futures):
                        results = future.result()
                        if self.debug:
                            self.post_message(f'is running, got result {results} '
                                              f'and put to result queue...')
                        for result in results:
                            self.result_queue.put(result)
            else:
                # 如果Broker正常退出，处理尚未完成的交易订单
                if self.debug:
                    self.post_message(f'is stopped, will process unfinished orders...')
                while not self.order_queue.empty():
                    order = self.order_queue.get()
                    # TODO: 如果Broker正常退出，应该将未完成的交易订单返回给用户，并提示用户后取消订单
                    self.result_queue.put(self.get_result(order))
                    self.order_queue.task_done()
        except KeyboardInterrupt:
            # 如果Broker被用户强制退出，处理尚未完成的交易订单
            if self.debug:
                self.post_message('is stopped by user, will stop broker and process unfinished orders...')
            self.status = 'stopped'
            while not self.order_queue.empty():
                order = self.order_queue.get()
                # TODO: 如果Broker被用户强制退出，应该将未完成的交易订单返回给用户，并提示用户后取消订单
                self.result_queue.put(self.get_result(order))
                self.order_queue.task_done()
        except Exception as e:
            # 如果Broker出现异常，处理尚未完成的交易订单
            if self.debug:
                self.post_message(f'is stopped by exception: {e}, will stop broker and process unfinished orders...')
                import traceback
                traceback.print_exc()
            self.status = 'stopped'
            raise e
        return

    def post_message(self, message: str, new_line=True):
        """ 将消息放入消息队列
        """
        if self.debug:
            message = f'[DEBUG]-{message}'
        message = f'[{self.broker_name}]: {message}'
        if not new_line:
            message += '_R'
        self.broker_messages.put(message)

    def get_result(self, order):
        """ 交易所处理交易订单并获取交易结果

        Parameters:
        -----------
        order: dict 交易订单dict，详细信息如下:
            {'order_id': 订单ID,
             'pos_id': position ID,
             'direction',
             'order_type',
             'qty',
             'price',
             'submitted_time',
             'status'}

        Returns:
        --------
        raw_trade_result: dict, 初步交易结果dict,详细信息如下：
            {'order_id',
             'filled_qty',
             'price',
             'transaction_fee',
             'execution_time',
             'canceled_qty',
             'delivery_amount',
             'delivery_status'
             }
        """

        if self.debug:
            self.post_message(f'get_result():\nsubmit order components of order(ID) {order["order_id"]}:\n'
                              f'quantity:{order["qty"]}\norder_price={order["price"]}\n'
                              f'order_direction={order["direction"]}\n')
        pos_id = order['pos_id']
        from qteasy.trade_recording import get_position_by_id
        from qteasy import QT_DATA_SOURCE
        symbol = get_position_by_id(pos_id=pos_id, data_source=QT_DATA_SOURCE)['symbol']
        trade_results = self.transaction_result(
                symbol=symbol,
                order_qty=order['qty'],
                order_price=order['price'],
                direction=order['direction'],
        )
        raw_trade_results = []
        for trade_result in trade_results:
            result_type, qty, filled_price, fee = trade_result

            if not isinstance(result_type, str):
                raise TypeError(f'result_type should be str, but got {type(result_type)}')
            if result_type not in ['filled', 'partial-filled', 'canceled']:
                raise ValueError(f'result_type should be one of ["filled", "canceled"], but got {result_type}')
            if not isinstance(qty, (int, float)):
                raise TypeError(f'qty should be int or float, but got {type(qty)}')
            if qty <= 0:
                raise ValueError(f'qty should be greater than 0, but got {qty}')
            if qty > order['qty']:
                raise ValueError(f'qty should be less than or equal to order["qty"], but got {qty}')
            if not isinstance(filled_price, (int, float)):
                raise TypeError(f'filled_price should be int or float, but got {type(filled_price)}')
            if filled_price < 0:
                raise ValueError(f'filled_price should be greater than 0, but got {filled_price}')
            if result_type == 'canceled' and filled_price != 0:
                raise ValueError(f'filled_price should be 0 when result_type is "canceled", but got {filled_price}')
            if not isinstance(fee, (int, float)):
                raise TypeError(f'fee should be int or float, but got {type(fee)}')
            if fee < 0:
                raise ValueError(f'fee should be greater than 0, but got {fee}')

            # 确认数据格式正确后，将数据圆整到合适的精度，并组装为raw_trade_result
            if self.debug:
                self.post_message(f'method: get_result(): got transaction result for order(ID) {order["order_id"]}\n'
                                  f'result_type={result_type}, \nqty={qty}, \n'
                                  f'filled_price={filled_price}, \nfee={fee}')
            # 圆整qty、filled_qty和fee
            qty = round(qty, AMOUNT_DECIMAL_PLACES)
            filled_price = round(filled_price, CASH_DECIMAL_PLACES)
            transaction_fee = round(fee, CASH_DECIMAL_PLACES)

            filled_qty = 0
            canceled_qty = 0
            if result_type in ['filled', 'partial-filled']:
                filled_qty = qty
            elif result_type == 'canceled':
                canceled_qty = qty
            else:
                raise ValueError(f'Unknown result_type: {result_type}, should be one of ["filled", "canceled"]')

            current_datetime = pd.to_datetime('today')
            raw_trade_result = {
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
                self.post_message(f'method get_result(): created raw trade result for order(ID) {order["order_id"]}:\n'
                                  f'{raw_trade_result}')

            raw_trade_results.append(raw_trade_result)

        return raw_trade_results

    @abstractmethod
    def transaction_result(self, symbol, order_qty, order_price, direction):
        """ 交易所处理交易订单并获取交易结果, 抽象方法，需要由用户在子类中实现

        Parameters:
        -----------
        symbol: str
            交易标的股票代码
        order_qty: float
            挂单数量
        order_price: float
            交易报价
        direction: str
            交易订单方向，'buy' 或者 'sell'

        Returns:
        --------
        tuple of tuples: ((result_type, qty, price, fee), (...), ...)
            result_type: str 交易结果类型:
                'filled' - 成交,
                'partial_filled' - 部分成交,
                'canceled' - 取消
                'failed' - 失败
            qty: float
                成交/取消数量，这个数字应该小于等于order_qty，且大于等于0
            price: float
                成交价格, 如果是取消交易，价格为0或任意数字
            fee: float
                交易费用，交易费用应该大于等于0

        Notes:
        ------
        1. 如果交易所返回的交易结果是部分成交，返回部分成交的结果
        2. 如果交易所返回的交易结果是分批成交，返回所有成交的结果
        3. 如果交易所返回的交易结果是取消，返回取消的结果
        4. 如果交易所返回的交易结果是失败，返回失败的结果

        Examples:
        ---------
        >>> broker = Broker()
        >>> # 交易所返回完全成交结果
        >>> broker.transaction_result(100, 10, 'buy')
        (('filled', 100, 10, 5),)
        >>> # 交易所返回部分成交结果
        >>> broker.transaction_result(100, 10, 'buy')
        (('partial_filled', 50, 10, 5),)
        >>> # 交易所返回分批成交结果
        >>> broker.transaction_result(200, 10, 'buy')
        (('partial_filled', 100, 10, 5), ('filled', 100, 10, 5))
        >>> # 交易所返回取消结果
        >>> broker.transaction_result(100, 10, 'buy')
        (('canceled', 100, 0, 0),)
        >>> # 交易所返回失败结果
        >>> broker.transaction_result(100, 10, 'buy')
        (('failed', 0, 0, 0),)
        """
        pass


class SimpleBroker(Broker):
    """ SimpleBroker接到交易订单后，立即返回交易结果
    交易结果总是完全成交，根据moq调整交易批量，根据设定的交易费率计算交易费用，滑点是按照百分比计算的

    Parameters
    ----------
    """

    def __init__(self):
        super(SimpleBroker, self).__init__()
        self.broker_name = 'SimpleBroker'

    def transaction_result(self, symbol, order_qty, order_price, direction):
        """ 订单立即成交

        Parameters:
        ----------
        symbol: str
            挂单交易标的股票代码
        order_qty: float
            挂单数量
        order_price: float
            挂单报价
        direction: str
            交易订单方向，'buy' 或者 'sell'

        Returns:
        --------
        tuple of tuples: ((result_type, qty, price, fee), (...), ...)
            result_type: str 交易结果类型:
                'filled' - 成交,
                'partial_filled' - 部分成交,
                'canceled' - 取消
                'failed' - 失败
            qty: float
                成交/取消数量，这个数字应该小于等于order_qty，且大于等于0
            price: float
                成交价格, 如果是取消交易，价格为0或任意数字
            fee: float
                交易费用，交易费用应该大于等于0
        """
        qty = order_qty
        price = order_price
        fee: float = 5.
        return 'filled', qty, price, fee


class SimulatorBroker(Broker):
    """ QT 默认的模拟交易所，该交易所模拟真实的交易情况，从qt_config中读取交易费率、滑点等参数

    根据这些参数尽可能真实地模拟成交结果，特点如下：

    - 在收到交易订单后，检查当前价格，如果价格低于叫买价，以实际价格买入，如果价格高于叫卖价，以实际价格卖出 - TODO: to be implemented
    - 交易费率根据qt_config中的设置计算，包括固定费率、最低费用、滑点等
    - 股票涨停时大概率买入交易失败，跌停时大概率卖出交易失败 - TODO: to be implemented
    """

    def __init__(self,
                 fee_rate_buy=0.0003,
                 fee_rate_sell=0.0001,
                 fee_min_buy=0.0,
                 fee_min_sell=0.0,
                 fee_fix_buy=0.0,
                 fee_fix_sell=0.0,
                 slipage=0.0,
                 moq_buy=0.0,
                 moq_sell=0.0,
                 delay=1.0,
                 price_deviation=0.0,
                 probabilities=(0.9, 0.08, 0.02)):
        """ 生成一个Broker对象

        Parameters
        ----------
        fee_rate_buy: float,
            买入操作的交易费率
        fee_rate_sell: float,
            卖出操作的交易费率
        fee_min_buy: float, default 0.0
            买入操作的最低交易费用
        fee_min_sell: float, default 0.0
            卖出操作的最低交易费用
        fee_fix_buy: float, default 0.0
            买入操作的固定交易费用，如果不为0，则忽略交易费率和最低费用
        fee_fix_sell: float, default 0.0
            卖出操作的固定交易费用，如果不为0，则忽略交易费率和最低费用
        slipage: float, default 0.0
            交易滑点, 当交易数量很大时，交易费用会被放大 slipage * (qty / 100) ** 2 倍
        moq_buy: float, default 0.0
            买入操作最小数量
        moq_sell: float, default 0.0
            卖出操作最小数量
        delay: float, default 1.0
            模拟交易延迟，单位为秒
        price_deviation: float, default 0.0
            模拟成交价格允许误差值。例如，当前价格100元，误差值为0.01，即允许价格误差为100*0.01 = 1元
            此时买入报价大于100-1元即可成交
            卖出报价小于100+1元即可成交
        probabilities: tuple of 3 floats, default (0.90, 0.08, 0.02)
            模拟完全成交、部分成交和未成交三种情况出现的概率

        """
        super(SimulatorBroker, self).__init__()
        self.broker_name = 'SimulatorBroker'
        self.fee_rate_buy = fee_rate_buy
        self.fee_rate_sell = fee_rate_sell
        self.fee_min_buy = fee_min_buy
        self.fee_min_sell = fee_min_sell
        self.fee_fix_buy = fee_fix_buy
        self.fee_fix_sell = fee_fix_sell
        self.slipage = slipage
        self.moq_buy = moq_buy
        self.moq_sell = moq_sell
        self.delay = delay
        self.price_deviation = price_deviation
        self.probabilities = probabilities

    def transaction_result(self, symbol, order_qty, order_price, direction):
        """ 读取实时价格模拟成交


        Parameters:
        -----------
        symbol: str
            交易标的股票代码
        order_qty: float
            挂单数量
        order_price: float
            交易报价
        direction: str
            交易订单方向，'buy' 或者 'sell'

        Returns:
        --------
        tuple of tuples: ((result_type, qty, price, fee), (...), ...)
            result_type: str 交易结果类型:
                'filled' - 成交,
                'partial_filled' - 部分成交,
                'canceled' - 取消
                'failed' - 失败
            qty: float
                成交/取消数量，这个数字应该小于等于order_qty，且大于等于0
            price: float
                成交价格, 如果是取消交易，价格为0或任意数字
            fee: float
                交易费用，交易费用应该大于等于0
        """

        remain_qty = order_qty
        order_results = []

        while remain_qty > 0.001:

            # 获取当前实时价格 TODO: 如果当前价格无法成交，是否应该持续等待价格变化可以成交或者broker关闭为止？
            from .emfuncs import stock_live_kline_price
            live_prices = stock_live_kline_price(symbol, freq='D', verbose=True, parallel=False)
            if not live_prices.empty:
                live_prices['close'] = live_prices['close'].astype('float')
                change = (live_prices['close'] / live_prices['pre_close'] - 1).iloc[-1]
                live_price = live_prices.close.iloc[-1]
                price_deviation = live_price * self.price_deviation
            else:
                raise ValueError(f'live price of symbol {symbol} can not be acquired at the moment...')

            # 如果当前价高于挂卖价(允许误差由price_deviation控制)，大概率成交或部分成交
            if (live_price >= order_price - price_deviation) and (direction == 'sell'):
                result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=self.probabilities)
                # 如果change非常接近-10%(跌停)，则非常大概率canceled
                if abs(change + 0.1) <= 0.001:
                    self.post_message(f'order will be probably canceled because -10% sell-limit')
                    result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=(0.01, 0.01, 0.98))
            # 如果当前价低于挂买价(允许误差由price_deviation控制), 大概率成交或部分成交
            elif (live_price <= order_price + price_deviation) and (direction == 'buy'):
                result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=self.probabilities)
                # 如果change非常接近+10%(涨停)，则非常大概率canceled
                if abs(change - 0.1) <= 0.001:
                    self.post_message(f'order will be probably canceled because +10% buy-limit')
                    result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=(0.01, 0.01, 0.98))

            else:
                # 无法成交
                self.post_message('quoted price does not meet current price, order will be canceled')
                result_type = 'canceled'

            if result_type in ['filled', 'partial-filled']:
                filled_proportion = 1
                if result_type == 'partial-filled':
                    filled_proportion = np.random.choice([0.25, 0.5, 0.75], p=[0.3, 0.5, 0.2])  # 模拟交易所的部分成交
                qty = remain_qty * filled_proportion
                if self.moq_buy > 0:
                    qty = np.trunc(qty / self.moq_buy) * self.moq_buy
                    if (qty < self.moq_buy) and (remain_qty > self.moq_buy):
                        qty = self.moq_buy # 如果成交数量小于moq，但是剩余数量大于moq，那么成交数量就是moq
                    elif (qty < self.moq_buy) and (remain_qty <= self.moq_buy):
                        qty = remain_qty # 如果成交数量小于moq，且剩余数量也小于moq，那么成交数量就是剩余数量
                        result_type = 'filled'
                if direction == 'buy':
                    order_price = live_price
                    transaction_fee = \
                        max(qty * order_price * self.fee_rate_buy, self.fee_min_buy) \
                            if self.fee_fix_buy == 0 \
                            else self.fee_fix_buy
                elif direction == 'sell':
                    order_price = live_price
                    transaction_fee = \
                        max(qty * order_price * self.fee_rate_sell, self.fee_min_sell) \
                            if self.fee_fix_sell == 0 \
                            else self.fee_min_sell
                else:
                    raise RuntimeError(f'invalid direction: {direction}')
                # 模拟交易滑点, 交易数量越大，对交易费用产生的影响越大
                if self.slipage > 0:
                    transaction_fee *= (1 + self.slipage * (qty / 100) ** 2)

            else:  # result_type == 'canceled'
                transaction_fee = 0
                order_price = 0
                qty = remain_qty

            remain_qty -= qty
            order_results.append((result_type, qty, order_price, transaction_fee))

        return tuple(order_results)


class NotImplementedBroker(Broker):
    """ NotImplementedBroker raises NotImplementedError when __init__() is called
    """

    def __init__(self):
        super(NotImplementedBroker, self).__init__()
        raise NotImplementedError('NotImplementedBroker is not implemented yet')

    def transaction_result(self, symbol, order_qty, order_price, direction):
        pass


def get_broker(name: str = 'simulator', params=None):
    """ get broker object by broker name

    Parameters
    ----------
    name:str default: simulator
        the broker name
    params: dict or None
        the parameters of broker

    Return
    ------
    Broker
    """
    all_brokers = {
        'random':    SimulatorBroker,
        'simple':    SimpleBroker,
        'manual':    NotImplementedBroker,
        'simulator': SimulatorBroker,
    }
    names_to_be_deprecated = {'random': 'simulator'}

    if not isinstance(name, str):
        raise TypeError(f'name must be a string, got {type(name)}')

    if name in names_to_be_deprecated:
        import warnings
        warnings.warn(f'the broker {name} will be deprecated in next version, '
                      f'use {names_to_be_deprecated[name]} instead')
    broker_func = all_brokers.get(name, SimulatorBroker)
    if params is not None:
        return broker_func(**params)
    return broker_func()
