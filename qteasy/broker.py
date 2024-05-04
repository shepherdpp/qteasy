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

import numpy as np
import time

import pandas as pd

from qteasy import QT_CONFIG
from qteasy.utilfuncs import get_current_timezone_datetime

CASH_DECIMAL_PLACES = QT_CONFIG['cash_decimal_places']
AMOUNT_DECIMAL_PLACES = QT_CONFIG['amount_decimal_places']


def _verify_trade_result(trade_result, order_qty):
    """ 检查result，确认是否符合基本要求:
    包括trade_result各个组份的类型是否正确、数据是否超过范围

    Parameters:
    -----------
    trade_result: tuple: (result_type, qty, filled_price, fee)
        result_type: str
        qty: float
        filled_price: float
        fee: float
    order_qty: float
        订单的报价数量
    """
    result_type, qty, filled_price, fee = trade_result

    if not isinstance(result_type, str):
        raise TypeError(f'result_type should be str, but got {type(result_type)}')
    if result_type not in ['filled', 'partial-filled', 'canceled']:
        raise ValueError(f'result_type should be one of ["filled", "canceled"], but got {result_type}')
    if not isinstance(qty, (int, float)):
        raise TypeError(f'qty should be int or float, but got {type(qty)}')
    if qty <= 0:
        raise ValueError(f'qty should be greater than 0, but got {qty}')
    if qty > order_qty:
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

    return True


class Broker(object):
    """ Broker是交易所的抽象，它处理账户信息、接受交易订单、处理交易订单、记录并返回交易结果

    Broker类包含与data_source的连接，可以读取并记录交易结果，在本地记录更新账户信息、持仓信息、交易历史等

    Attributes:
    -----------
    broker_name: str
        交易所的名称

    Methods:
    --------
    register(debug=False, **kwargs):
        交易所的初始化程序，用于模拟交易所对象与交易所建立连接，登录账号，获取token，读取并同步最新信息等任务
    log_out_broker():
        交易所的关闭程序，用于模拟交易所对象与交易所断开连接，退出账号，清除token等任务
    pause_broker():
        暂停交易所，暂停交易所的交易活动
    resume_broker():
        恢复交易所，恢复交易所的交易活动
    check_status():
        检查交易所的状态，如 'running'(交易中)、'stopped'(停止)、'paused'(暂停/休市)等
    submit_order(order):
        向交易所发出指令，提交交易订单，等待交易所返回交易结果
    cancel_order(order_id):
        取消交易订单，发出指令取消已经提交的交易订单
    transfer_in(amount):
        向交易所转入资金，将资金从银行账户转入交易所账户
    transfer_out(amount):
        从交易所转出资金，将资金从交易所账户转出到银行账户
    check_order(order_id):
        查询交易订单的状态，返回交易订单的执行状态
    check_orders():
        查询账户交易订单，返回账户交易订单信息，包括未成交订单、已成交订单等
    check_balance():
        查询账户余额，返回账户余额信息，包括现金、可用现金、保证金、可用保证金等
    check_positions():
        查询账户持仓，返回账户持仓信息，包括股票持仓、期货持仓等
    check_history():
        查询成交历史，包括成交订单，时间、数量、交易费用等

    """
    __metaclass__ = ABCMeta

    # TODO: for v1.2:
    #  重构Broker类，使Broker基类提供通用的接口，如log_in, log_out, run, transaction等
    #  并将具体的交易所实现放在子类中，如SimulatorBroker, SimpleBroker等
    #  重构后的Broker类应该是一个抽象类，不能直接实例化，只能通过子类实例化
    #  重构后的Broker类提供的接口可以通用于模拟交易所和真实交易所，同时所有的接口以真实交易所的接口
    #  为标准，模拟交易所的接口应该尽量与真实交易所的接口保持一致
    def __init__(self, data_source=None):
        """ 生成一个Broker对象

        """
        # override this function if necessary
        self._data_source = data_source
        self.broker_name = 'BaseBroker'
        self.account_id = None
        self.user_name = ''
        self.password = ''
        self.token = ''
        self.status = 'init'  # init, running, stopped, paused
        self.debug = False
        self.is_registered = False

        self.time_zone = 'local'
        self.init_time = get_current_timezone_datetime(self.time_zone).strftime('%Y-%m-%d %H:%M:%S')

        self.order_queue = Queue()
        self.result_queue = Queue()
        self.broker_messages = Queue()

    def register(self, debug=False, **kwargs) -> bool:
        """ Broker对象在开始运行前的注册过程，作用是设置broker的状态为is_registered
        Override这个函数，以添加更多处理

        只有is_registered == True时，broker才能够运行

        Parameters
        ----------
        debug: bool, default: False
            是否进入debug mode
        kwargs:

        Return
        ------
        is_registered: bool
            是否注册成功
        """
        # override this function if necessary
        self.is_registered = True
        self.debug = debug

        return self.is_registered

    def log_out_broker(self) -> None:
        """ 退出登录Broker，在关闭前的处理过程。
        """
        # override this function if necessary
        pass

    def submit_order(self, order) -> int:
        """ 将交易订单提交至broker，需要提供symbol，多空类型，交易方向，交易数量/金额，交易报价，订单类型等信息
        订单执行的结果需要通过check_order()来查询

        Parameters
        ----------
        order: dict
            交易订单dict，详细信息如下:
            {'order_id': 订单ID,
             'pos_id': position ID,
             'direction',
             'order_type',
             'qty',
             'price',
             'submitted_time',
             'status'}

        Returns
        -------
        order_id: int
            交易订单ID
        """
        pass

    def cancel_order(self, order_id) -> None:
        """ 取消已经提交的交易订单，如果订单已经执行，则无法取消，订单取消的结果需要通过check_order()来确认
        """
        pass

    def check_order(self, order_id) -> dict:
        """ 查询交易订单的状态，返回交易订单的执行状态

        Parameters
        ----------
        order_id: int
            交易订单ID

        Returns
        -------
        order_status: dict
            交易订单的状态，包括订单ID，订单状态，订单数量，订单价格，订单类型，订单提交时间等
        """
        pass

    def check_orders(self) -> pd.DataFrame:
        """ 查询账户交易订单，返回账户交易订单信息，包括未成交订单、已成交订单等

        Returns
        -------
        orders: pd.DataFrame
            账户交易订单信息，包括订单ID，订单状态，订单数量，订单价格，订单类型，订单提交时间等
        """
        pass

    def transfer_in(self, amount) -> None:
        """ 向交易所转入资金，将资金从银行账户转入交易所账户，转入的结果需要通过check_balance()来确认
        """
        pass

    def transfer_out(self, amount) -> None:
        """ 从交易所转出资金，将资金从交易所账户转出到银行账户，转出的结果需要通过check_balance()来确认
        """
        pass

    def check_balance(self) -> dict:
        """ 查询账户余额，返回账户余额信息，包括现金、可用现金、保证金、可用保证金等

        Returns
        -------
        balance: dict
            账户余额信息
        """
        pass

    def check_positions(self) -> pd.DataFrame:
        """ 查询账户持仓，返回账户持仓信息，包括股票持仓、期货持仓等

        Returns
        -------
        positions: pd.DataFrame
            账户持仓信息, 包括持有资产的代码、数量，可用数量，持仓成本等信息
        """
        pass

    def check_history(self) -> pd.DataFrame:
        """ 查询成交历史，包括成交订单，时间、数量、交易费用等

        Returns
        -------
        history: pd.DataFrame
            成交历史信息，包括成交订单的时间、数量、交易费用等
        """
        pass


class SimulatorBroker(Broker):
    """ QT 实盘运行模拟交易所，接受交易订单后，读取实际价格数据，根据订单类型、价格数据以及设置的交易费率参数模拟成交结果

    - 在收到交易订单后，根据订单类型和当前价格确认成交类型：
        - 如果订单类型是市价单：以当前价成交
        - 如果订单类型是限价单：若当前格低于叫买价，以当前价买入，若当前价高于叫卖价，以当前价卖出
    - 股票涨停时大概率买入交易失败，跌停时大概率卖出交易失败
    - 交易费率根据参数中的设置计算，包括固定费率、最低费用、滑点等
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
                 probabilities=(0.9, 0.08, 0.02),
                 data_source=None):
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

        self._data_source = data_source
        self.broker_name = 'BaseBroker'
        self.user_name = ''
        self.password = ''
        self.token = ''
        self.status = 'init'  # init, running, stopped, paused
        self.debug = False
        self.is_registered = False

        self.time_zone = 'local'
        self.init_time = get_current_timezone_datetime(self.time_zone).strftime('%Y-%m-%d %H:%M:%S')

        self.order_queue = Queue()
        self.result_queue = Queue()
        self.broker_messages = Queue()

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

    @property
    def data_source(self):
        return self._data_source

    def run(self):
        """ Broker的主循环，从order_queue中获取交易订单并处理，获得交易结果并放入result_queue中
        order_queue中的每一个交易订单都由transaction函数来处理并获取交易结果，transaction函数是
        一个Generator，可以分批返回交易结果，直至订单处理完毕或出现错误。每一个transaction都会在单
        独的线程中运行
        """
        from threading import Thread
        if not self.is_registered:
            raise RuntimeError(f'broker is not registered!')
        if self.debug:
            self.send_message(f'is running...')
        self.status = 'init'
        while True:
            try:
                time.sleep(0.05)
                if self.status == 'stopped':
                    # 如果Broker正常退出，处理尚未提取的交易订单，这些订单将不会被处理，会提示用户取消订单
                    print(f'Stopping un-processed orders in broker...')
                    un_processed_orders = []
                    while not self.order_queue.empty():
                        un_processed_orders.append(self.order_queue.get())
                        self.order_queue.task_done()

                    if len(un_processed_orders) > 0:
                        print(f'Un-processed orders: {un_processed_orders}')

                    # 交易所关闭后的处理程序
                    self.log_out_broker()
                    print(f'Broker is stopped')
                    break

                # 如果Broker处于暂停状态，则不处理交易订单
                if self.status == 'paused':
                    continue

                # 如果order_queue为空，则不处理交易订单
                if self.order_queue.empty():
                    continue

                # order_queue不为空，提取交易订单，在一个单独的thread中调用self._get_result()处理交易订单
                order = self.order_queue.get()  # order is a dict, should be packed in a tuple
                t = Thread(target=self._get_result, args=(order, ), daemon=True)
                t.start()

            except KeyboardInterrupt:
                # 如果Broker被用户强制退出，处理尚未完成的交易订单
                if self.debug:
                    self.send_message('Broker will be stopped by user.')
                self.status = 'stopped'
                continue
            except Exception as e:
                # 如果Broker出现异常，打印异常信息，并继续运行
                self.send_message(f'Runtime exception: {e}, please check system log for details')
                if self.debug:
                    import traceback
                    traceback.print_exc()
                continue

        return

    def send_message(self, message: str, new_line=True):
        """ 将消息放入broker的消息队列
        """
        if self.debug:
            message = f'[DEBUG]-{message}'
        message = f'[{self.broker_name}]: {message}'
        if not new_line:
            message += '_R'
        self.broker_messages.put(message)

    def parse_order(self, order):
        """ 解析交易订单，提取其关键信息，并将order的状态改为"submitted"

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
        order info: tuple(symbol, qty, price, direction, position)
        symbol:
        qty:
        price:
        direction:
        position:
        """

        if self.debug:
            self.send_message(f'_parse_order():\nsubmit order components of order(ID) {order["order_id"]}:\n'
                              f'quantity:{order["qty"]}\norder_price={order["price"]}\n'
                              f'order_direction={order["direction"]}\n')
        pos_id = order['pos_id']
        from qteasy.trade_recording import get_position_by_id
        try:
            position = get_position_by_id(pos_id=pos_id, data_source=self.data_source)
        except RuntimeError as e:
            raise RuntimeError(e)
        symbol = position['symbol']
        position = position['position']
        qty = order['qty']
        price = order['price']
        direction = order['direction']
        order_type = order['order_type']
        return order_type, symbol, qty, price, direction, position

    def _get_result(self, order):
        """ 解析订单信息，将关键信息提交给transaction，获取交易结果后，解析交易结果，将结果放入result_queue

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

        order_type, symbol, qty, price, direction, position = self.parse_order(order)
        for trade_result in self.transaction(
                order_type=order_type,
                symbol=symbol,
                order_qty=qty,
                order_price=price,
                direction=direction,
                position=position
        ):
            result_type, qty, filled_price, fee = trade_result
            _verify_trade_result(trade_result, qty)

            # 确认数据格式正确后，将数据圆整到合适的精度，并组装为raw_trade_result
            if self.debug:
                self.send_message(f'method: _get_result(): got transaction result for order(ID) {order["order_id"]}\n'
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

            current_datetime = get_current_timezone_datetime(self.time_zone)
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

            # 将trade_result放入result_queue
            if self.debug:
                self.send_message(f'method _get_result(): created raw trade result for order(ID) {order["order_id"]}:\n'

                                  f'{raw_trade_result}')
            self.result_queue.put(raw_trade_result)

        # 全部订单处理完毕或发生错误后结束
        return

    def transaction(self, symbol, order_qty, order_price, direction, position='long', order_type='market'):
        """ 读取实时价格模拟成交结果
        """

        total_filled = 0

        while True:

            import time

            if total_filled >= order_qty:  # 订单完全成交，退出
                break

            if self.status == 'stopped':  # 当broker停止时，退出
                break

            if self.status == 'paused':  # 当broker暂停时，稍后重试
                continue

            # 获取当前实时价格
            retry = 10  # 重试次数为10次（秒）
            from .emfuncs import real_time_klines
            live_prices = real_time_klines(symbol, freq='D', verbose=True, parallel=False)
            if not live_prices.empty:
                live_prices['close'] = live_prices['close'].astype('float')
                change = (live_prices['close'] / live_prices['pre_close'] - 1).iloc[-1]
                live_price = live_prices.close.iloc[-1]
                price_deviation = live_price * self.price_deviation
            else:  # 实时价格获取不成功，稍后重试
                self.send_message(f'live price of {symbol} can not be acquired at the moment, '
                                  f'order will not be processed, retries left: {retry}')
                retry -= 1
                live_price = 0
                change = 0
                price_deviation = 0
                if retry > 0:
                    time.sleep(1)  # 延迟1秒重试
                    continue
            # 重试超过max_retry，直接cancel订单
            if retry <= 0:
                self.send_message(f'order will be canceled because max retries exceeded')
                result_type = 'canceled'
            # 如果当前价高于挂卖价(允许误差由price_deviation控制)，大概率成交或部分成交
            elif (live_price >= order_price - price_deviation) and (direction == 'sell'):
                result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=self.probabilities)
                # 如果change非常接近-10%(跌停)，则非常大概率canceled
                if abs(change + 0.1) <= 0.001:
                    self.send_message(f'order will be probably canceled because -10% sell-limit')
                    result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=(0.01, 0.01, 0.98))
            # 如果当前价低于挂买价(允许误差由price_deviation控制), 大概率成交或部分成交
            elif (live_price <= order_price + price_deviation) and (direction == 'buy'):
                result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=self.probabilities)
                # 如果change非常接近+10%(涨停)，则非常大概率canceled
                if abs(change - 0.1) <= 0.001:
                    self.send_message(f'order will be probably canceled because +10% buy-limit')
                    result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=(0.01, 0.01, 0.98))
            # 如果挂单类型为市价单且不受张跌停限制, 大概率成交或部分成交
            elif (order_type == 'market') and (-0.098 < change < 0.098):
                # 市价单，只要不涨停跌停即可市价成交
                result_type = np.random.choice(['filled', 'partial-filled', 'canceled'], p=self.probabilities)
            # 所有条件均不满足，稍后重试
            else:
                if self.debug:
                    self.send_message(f'current price does not satisfy quoted, retries left: {retry}')
                retry -= 1
                time.sleep(1)  # 延迟1秒重试
                continue

            # 成交类型为成交或部分成交，计算成交数量及交易费用
            if result_type in ['filled', 'partial-filled']:
                # 部分成交及全部成交，计算成交数量
                filled_proportion = 1
                if result_type == 'partial-filled':
                    filled_proportion = np.random.choice([0.25, 0.5, 0.75], p=[0.3, 0.5, 0.2])  # 模拟交易所的部分成交
                remain_qty = order_qty - total_filled
                qty = remain_qty * filled_proportion
                if self.moq_buy > 0:
                    qty = np.trunc(qty / self.moq_buy) * self.moq_buy
                    if (qty < self.moq_buy) and (remain_qty > self.moq_buy):
                        qty = self.moq_buy  # 如果成交数量小于moq，但是剩余数量大于moq，那么成交数量就是moq
                    elif (qty < self.moq_buy) and (remain_qty <= self.moq_buy):
                        qty = remain_qty  # 如果成交数量小于moq，且剩余数量也小于moq，那么成交数量就是剩余数量
                        result_type = 'filled'
                # 如果确认成交，成交价格为当前价格
                order_price = live_price
                # 计算交易费用，根据买入/卖出费率计算
                if direction == 'buy':
                    transaction_fee = \
                        max(qty * order_price * self.fee_rate_buy, self.fee_min_buy) \
                            if self.fee_fix_buy == 0 \
                            else self.fee_fix_buy
                elif direction == 'sell':
                    transaction_fee = \
                        max(qty * order_price * self.fee_rate_sell, self.fee_min_sell) \
                            if self.fee_fix_sell == 0 \
                            else self.fee_min_sell
                else:
                    raise RuntimeError(f'invalid direction: {direction}')
                # 模拟交易滑点, 交易数量越大，对交易费用产生的影响越大
                if self.slipage > 0:
                    transaction_fee *= (1 + self.slipage * (qty / 100) ** 2)

            # 成交类型为取消，成交数量为0，成交价格为0，交易费用为0
            elif result_type in ['canceled']:  # result_type == 'canceled'
                transaction_fee = 0
                order_price = 0
                qty = order_qty - total_filled
            # 不能成交，稍后重试
            else:
                time.sleep(1)  # 延迟1秒重试
                continue

            order_result = (result_type, qty, order_price, transaction_fee)
            yield order_result

            total_filled += qty


class BacktestBroker(Broker):
    """ BacktestBroker is a broker for backtesting trading strategies"""

    def __init__(self):
        super(BacktestBroker, self).__init__()
        self.broker_name = 'BacktestBroker'


class ManualBroker(Broker):
    """ ManualBroker is a broker for manual trading"""

    def __init__(self, data_source=None):
        super(ManualBroker, self).__init__()
        self._data_source = data_source
        self.broker_name = 'ManualBroker'


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
        'manual':    ManualBroker,
        'backtest':  BacktestBroker,
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