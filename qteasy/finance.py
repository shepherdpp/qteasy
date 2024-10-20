# coding=utf-8
# ======================================
# File:     finance.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-09-30
# Desc:
#   Back-test trade cost calculation and
#   Cash investment simulation functions.
# ======================================

import numpy as np
import pandas as pd
from numba import njit

from qteasy.utilfuncs import ALL_COST_PARAMETERS


def validate_cost_dict(cost: dict) -> None:
    """ 检查成本参数是否合法

    Parameters
    ----------
    cost: dict
        一个包含成本参数的字典

    Returns
    -------
    None

    Raises
    ------
    TypeError
        如果cost不是一个字典
    KeyError
        如果cost中包含非法的成本参数
    """
    if not isinstance(cost, dict):
        msg = f'Cost should be a dict, got {type(cost)} instead'
        raise TypeError(msg)
    if any(k not in ALL_COST_PARAMETERS for k in cost.keys()):
        invalid_keys = [k for k in cost.keys() if k not in ALL_COST_PARAMETERS]
        raise KeyError(f'Invalid cost parameters: {invalid_keys}')
    return None


def set_cost(**kwargs):
    """ 新建一个cost字典

    交易成本的估算依赖四种类型的成本：
    1,  fixed_fee：固定费用，在交易过程中产生的固定现金费用，与交易金额和交易量无关，买入与卖出固定费用可以不同
        固定费用类型与固定费率或最低费用不能同时存在，当固定费用不为0时，直接使用固定费用作为交易费用，忽略其他参数
        交易费用 = 固定费用
    2,  rate：type：float，交易费率，交易过程中的固定费率，与交易金额成正比，买入与卖出的交易费率可以不同
        交易费用 = 交易金额 * 交易费率
    3,  min_fee: float，最低交易费用，当设置了交易费率时，按照交易费率计算费用，但如果按照交易费率算出的费用低于
        最低费用，则使用最低费用。例如：
            卖出100股股票，假设每股价格10元，交易费率为千分之一，最低费用为5元，则
            根据费率计算出交易费用为1元，但由于最低费用为5元，因而交易费用为5元
    4,  slipage：type：float，交易滑点，或者叫二阶费率。
        用于模拟交易过程中由于交易延迟或买卖冲击形成的交易成本，滑点绿表现为一个关于交易量的函数, 交易
        滑点成本等于该滑点率乘以交易金额： 滑点成本 = f(交易金额） * 交易成本

    Parameters
    ----------
    kwargs: dict
        可用的成本参数包括：
        - buy_fix: float, 固定买入费用，如果设置了固定费用，则费率和最低费用会被忽略
        - sell_fix: float, 固定卖出费用，如果设置了固定费用，则费率和最低费用会被忽略
        - buy_rate: float, 买入费率，实际买入费用等于买入金额乘以费率
        - sell_rate: float, 卖出费率，实际卖出费用等于卖出金额乘以费率
        - buy_min: float, 最低买入费用，当按费率计算的费用小于该费用时，按最低费用计算
        - sell_min: float, 最低卖出费用，当按费率计算的费用小于该费用时，按最低费用计算
        - slipage: float, 滑点，用于估算交易价格损失，金额为滑点乘以交易金额

    Returns
    -------
    cost : dict of float, cost parameters

    """
    cost = dict(buy_fix=0.0,
                sell_fix=0.0,
                buy_rate=0.003,
                sell_rate=0.001,
                buy_min=5.0,
                sell_min=0.0,
                slipage=0.0)

    update_cost(cost, **kwargs)
    return cost


def update_cost(c: dict, **kwargs):
    """ 更新cost字典中各个值

    Parameters
    ----------
    c: dict
        一个包含成本参数的字典
    kwargs: dict
        可用的成本参数包括：
        - buy_fix: float, 固定买入费用，如果设置了固定费用，则费率和最低费用会被忽略
        - sell_fix: float, 固定卖出费用，如果设置了固定费用，则费率和最低费用会被忽略
        - buy_rate: float, 买入费率，实际买入费用等于买入金额乘以费率
        - sell_rate: float, 卖出费率，实际卖出费用等于卖出金额乘以费率
        - buy_min: float, 最低买入费用，当按费率计算的费用小于该费用时，按最低费用计算
        - sell_min: float, 最低卖出费用，当按费率计算的费用小于该费用时，按最低费用计算
        - slipage: float, 滑点，用于估算交易价格损失，金额为滑点乘以交易金额

    Returns
    -------
    c: dict, 更新后的成本参数
    """
    validate_cost_dict(c)
    for k, v in kwargs.items():
        if k not in ALL_COST_PARAMETERS:
            continue
        # TODO: 此处应该validate输入值
        c[k] = v

    return c


def get_cost_pamams(c: dict) -> np.ndarray:
    """ 返回成本参数

    Parameters
    ----------
    c: dict
        一个包含成本参数的字典

    Returns
    -------
    np.ndarray
        一个包含成本参数的ndarray，包括以下参数：
        fee_params[0]: buy_fix: float:
            买入固定费用
        fee_params[1]: sell_fix: float:
            卖出固定费用
        fee_params[2]: buy_rate: float:
            买入费率
        fee_params[3]: sell_rate: float:
            卖出费率
        fee_params[4]: buy_min: float:
            买入最低费用
        fee_params[5]: sell_min: float:
            卖出最低费用
        fee_params[6]: slipage: float:
            滑点
    """
    validate_cost_dict(c)
    return np.array([c['buy_fix'],
                     c['sell_fix'],
                     c['buy_rate'],
                     c['sell_rate'],
                     c['buy_min'],
                     c['sell_min'],
                     c['slipage']])


@njit
def calculate_fees(trade_values: np.ndarray, cost_params: np.ndarray, is_buying: bool = True,
                   fixed_fees: bool = False) -> np.ndarray:
    """直接调用对象，计算交易费率或交易费用

    采用两种模式计算：
        当fixed_fees为True时，采用固定费用模式计算，返回值为包含滑点的交易成本列表，
        当fixed_fees为False时，采用固定费率模式计算，返回值为包含滑点的交易成本率列表

    Parameters
    ----------
    trade_values: ndarray:
        总交易金额清单，每一种股票的交易金额
    cost_params: np.ndarray:
        交易费用参数，一个ndarray，包括以下参数：
        fee_params[0]: buy_fix: float:
            买入固定费用
        fee_params[1]: sell_fix: float:
            卖出固定费用
        fee_params[2]: buy_rate: float:
            买入费率
        fee_params[3]: sell_rate: float:
            卖出费率
        fee_params[4]: buy_min: float:
            买入最低费用
        fee_params[5]: sell_min: float:
            卖出最低费用
        fee_params[6]: slipage: float:
            滑点
    is_buying: bool, optional, default: True:
        当前是否计算买入费用或费率, 默认True
    fixed_fees: bool, optional, default: False:
        当前是否采用固定费用模式计算, 默认False

    Returns
    -------
    np.ndarray:
        一个ndarray，每种股票的交易费用
    """
    if is_buying is None:
        is_buying = True
    if fixed_fees is None:
        fixed_fees = False

    # TODO: 重写slipage的计算公式，使得slipage是一个交易费用的乘数，该乘数 = slipage * (qty / 100) ** 2
    if fixed_fees:  # 采用固定费用模式计算, 返回固定费用及滑点成本，返回的是费用而不是费率
        if is_buying:
            # buy_fix + slipage * trade_values ** 2
            return cost_params[0] + cost_params[6] * trade_values ** 2
        else:
            # sell_fix + slipage * trade_values ** 2
            return cost_params[1] + cost_params[6] * trade_values ** 2
    else:  # 采用固定费率模式计算, 返回费率而不是费用
        if is_buying:
            if cost_params[4] == 0.:  # if buy_min == 0
                # return buy_rate + slipage * trade_values
                return cost_params[2] + cost_params[6] * trade_values
            else:
                # min_rate = buy_min / (trade_values - buy_min)
                min_rate = cost_params[4] / (trade_values - cost_params[4])
                # return max(buy_rate, min_rate) + slipage * trade_values
                return np.fmax(cost_params[2], min_rate) + cost_params[6] * trade_values
        else:
            if cost_params[5] == 0.:  # if sell_min == 0
                # return sell_rate - slipage * trade_values
                return cost_params[3] - cost_params[6] * trade_values
            else:
                # min_rate = - sell_min / trade_values
                min_rate = - cost_params[5] / trade_values
                # 当trade_values中有0值时，将产生inf，且传递到caller后会导致问题，因此需要清零
                min_rate[np.isinf(min_rate)] = 0
                # return max(sell_rate, min_rate) - slipage * trade_values
                return np.fmax(cost_params[3], min_rate) + cost_params[6] * trade_values


@njit
def get_selling_result(prices: np.ndarray,
                       a_to_sell: np.ndarray,
                       moq,
                       cost_params: np.ndarray,
                       ) -> (np.ndarray, np.ndarray, np.ndarray):
    """计算出售投资产品的要素

    Parameters
    ----------
    prices: ndarray, 投资产品的价格
    a_to_sell: ndarray, 计划卖出数量，其形式为计划卖出的股票的数量，通常为负，且其绝对值通常小于等于可出售的数量
    moq: float, 卖出股票的最小交易单位
    cost_params: np.ndarray, 交易费用参数，包括以下参数：
        - buy_fix: float, 买入固定费用
        - sell_fix: float, 卖出固定费用
        - buy_rate: float, 买入费率
        - sell_rate: float, 卖出费率
        - buy_min: float, 买入最低费用
        - sell_min: float, 卖出最低费用
        - slipage: float, 滑点

    Returns
    -------
    tuple: (a_sold, cash_gained, fee)
     - a_sold: ndarray          实际出售的资产份额
     - cash_gained: ndarray     扣除手续费后获得的现金
     - fee: ndarray             扣除的手续费
    """
    if moq == 0:
        a_sold = a_to_sell
    else:
        a_sold = np.trunc(a_to_sell / moq) * moq
    sold_values = a_sold * prices
    sell_fix = cost_params[1]
    if sell_fix == 0:  # 固定交易费用为0，按照交易费率模式计算
        rates = calculate_fees(trade_values=sold_values, cost_params=cost_params, is_buying=False, fixed_fees=False)
        cash_gained = (-1 * sold_values * (1 - rates))
        fees = -(sold_values * rates)
    else:  # 固定交易费用不为0时，按照固定费率收取费用——直接从交易获得的现金中扣除
        fixed_fees = calculate_fees(trade_values=sold_values, cost_params=cost_params, is_buying=False, fixed_fees=True)
        fees = np.where(a_sold, fixed_fees, 0)
        cash_gained = - sold_values - fees
    return a_sold, cash_gained, fees


@njit
def get_purchase_result(prices: np.ndarray,
                        cash_to_spend: np.ndarray,
                        moq,
                        cost_params: np.ndarray,
                        ) -> (np.ndarray, np.ndarray, np.ndarray):
    """获得购买资产时的要素

    Parameters
    ----------
    prices: ndarray, 投资组合中每只股票的当前单价
    cash_to_spend: ndarray, 买入金额，可用于买入股票或资产的计划金额
    moq: float, 最小交易单位
    cost_params: np.ndarray, 交易费用参数，包括以下参数：
        - buy_fix: float, 买入固定费用
        - sell_fix: float, 卖出固定费用
        - buy_rate: float, 买入费率
        - sell_rate: float, 卖出费率
        - buy_min: float, 买入最低费用
        - sell_min: float, 卖出最低费用
        - slipage: float, 滑点

    Returns
    -------
    tuple: (a_to_purchase, cash_spent, fee)
    a_to_purchase: ndarray,  代表所有股票分别买入的份额或数量
    cash_spent: ndarray,     花费的总金额，包括购买成本在内
    fee: ndarray,            花费的费用，购买成本，包括佣金和滑点等投资成本
    """

    buy_fix = cost_params[0]
    buy_min = cost_params[4]
    if buy_fix == 0.:
        # 固定费用为0，估算购买一定金额股票的交易费率，考虑最小费用，将绝对值小于buy_min的金额置0
        # （因为在"allow_sell_short"模式下，cash_to_spend可能会小于零，代表买入负持仓）
        cash_to_spend = np.where(np.abs(cash_to_spend) < buy_min, 0, cash_to_spend)
        rates = calculate_fees(trade_values=cash_to_spend, cost_params=cost_params, is_buying=True, fixed_fees=False)
        # 根据moq计算实际购买份额，当价格为0的时候买入份额为0
        if moq == 0:  # moq为0，实际买入份额与期望买入份额相同
            a_purchased = np.where(prices,
                                   cash_to_spend / (prices * (1 + rates)),
                                   0.)
        else:  # moq不为零，实际买入份额必须是moq的倍数，因此实际买入份额通常小于期望买入份额
            a_purchased = np.where(prices,
                                   np.trunc(cash_to_spend / (prices * moq * (1 + rates))) * moq,
                                   0.)
        # 根据交易量计算交易费用，考虑最低费用的因素，当费用低于最低费用时，使用最低费用
        fees = np.where(a_purchased, np.fmax(a_purchased * prices * rates, buy_min), 0.)
        purchased_values = a_purchased * prices + fees
        cash_spent = np.where(a_purchased, -1 * purchased_values, 0.)
    else:  # self.buy_fix
        # 固定费用不为0，按照固定费用模式计算费用，忽略费率并且忽略最小费用，将绝对值小于buy_fix的金额置0
        # （因为在"allow_sell_short"模式下，cash_to_spend可能会小于零，代表买入负持仓）
        cash_to_spend = np.where(np.abs(cash_to_spend) < buy_fix, 0, cash_to_spend)
        fixed_fees = calculate_fees(trade_values=cash_to_spend, cost_params=cost_params, is_buying=True, fixed_fees=True)
        if moq == 0.:
            a_purchased = np.fmax(np.where(prices,
                                           (cash_to_spend - fixed_fees) / prices,
                                           0.),
                                  0.)
        else:
            a_purchased = np.fmax(np.where(prices,
                                           np.trunc((cash_to_spend - fixed_fees) / (prices * moq)) * moq,
                                           0.),
                                  0.)
        cash_spent = np.where(a_purchased, -1 * a_purchased * prices - fixed_fees, 0.)
        fees = np.where(a_purchased, fixed_fees, 0.)
    return a_purchased, cash_spent, fees


class CashPlan:
    """ 现金计划类，在策略回测的过程中用来模拟固定日期的现金投资额

    投资计划对象包含一组带时间戳的投资金额数据，用于模拟在固定时间的现金投入，可以实现对一次性现金投入和资金定投的模拟

    Properties:
    -----------
    first_date: str, 第一笔投资的日期
    last_date: str, 最后一笔投资的日期
    periods: int, 投资的总期数
    investment_amounts: list, 投资的金额列表
    dates: list, 投资的日期列表
    amounts: list, 投资的金额列表
    total: float, 投资的总金额
    ir: float, 投资的年化收益率
    closing_value: float, 投资的最终价值
    opening_value: float, 投资的初始价值

    Methods
    -------
    info()
        打印投资计划的基本信息
    reset_dates(dates: [list, str])
        重置投资计划的日期
    plan()
        返回投资计划的时间序列数据
    to_dict(key: str = 'cash_plan')
        返回投资计划的字典数据

    Operators
    ---------
    __add__(other)
        投资计划的加法运算，两个投资计划相加得到投资计划的并集
    __mul__(other)
        投资计划的乘法运算，投资计划乘以一个整数得到倍增的投资计划
    __rmul__(other)
        投资计划的乘法运算，一个整数乘以投资计划得到延长的投资计划，一个浮点数乘以投资计划得到倍增的投资计划

    Examples
    --------
    >>> plan1 = CashPlan(dates='2020-01-01', amounts=10000)
    >>> plan1.info()
    <class 'qteasy.finance.CashPlan'>
    Investment is one-off amount of ¥10,000.00 on 2020-01-01
    Interest rate: 0.00%, equivalent final value: ¥10,000.00:
                amount
    2020-01-01   10000

    >>> plan2 = CashPlan(dates=['2020-01-01', '2020-02-01'], amounts=[10000, 20000])
    >>> plan2.info()
    <class 'qteasy.finance.CashPlan'>
    Investment is two times of ¥10,000.00 on 2020-01-01 and ¥20,000.00 on 2020-02-01
    Interest rate: 0.00%, equivalent final value: ¥30,000.00:
                amount
    2020-01-01   10000
    2020-02-01   20000

    >>> plan
    CashPlan(['20200101'], [10000], 0.0)
    >>> plan2
    CashPlan(['20200101', '20200201'], [10000, 20000], 0.0)
    >>> plan + plan2
    CashPlan(['20200101', '20200201'], [20000, 20000], 0.0)

    >>> plan2 + 10000
    CashPlan(['20200101', '20200201'], [20000, 30000], 0.0)
    >>> plan2 * 2
    CashPlan(['20200101', '20200201'], [20000, 40000], 0.0)
    >>> 2 * plan2
    CashPlan(['20200101', '20200201', '20200304', '20200404'], [10000, 20000, 10000, 20000], 0.0)
    """

    def __init__(self, dates, amounts: (int, float, [int], [float]), interest_rate: float = 0.0):
        """ 初始化投资计划

        Parameters
        ----------
        dates: str, datetime, list of str or list of datetime
            投资的日期，可以是一个日期字符串，也可以是一个日期字符串列表
        amounts: int, float, list of int or float
            投资的金额，可以是一个数字，也可以是一个数字列表
        interest_rate: float, Default 0.0
            投资的年化收益率，用于计算投资的最终价值

        Examples
        --------
        >>> plan = CashPlan(dates='2020-01-01', amounts=10000)
        >>> plan
        CashPlan(['20200101'], [10000], 0.0)
        >>> plan = CashPlan(dates=['2020-01-01', '2020-02-01'], amounts=[10000, 20000])
        >>> plan
        CashPlan(['20200101', '20200201'], [10000, 20000], 0.0)
        """

        if isinstance(amounts, (int, float)):
            amounts = [amounts]
        if not isinstance(amounts, (list, np.ndarray)):
            msg = f'Amounts should be a list of numbers, got {type(amounts)} instead'
            raise TypeError(msg)
        if isinstance(amounts, list):

            if not all([isinstance(amount, (int, float, np.int64, np.float64)) for amount in amounts]):
                msg = f'Amount should be number format, got unresolved format in amounts!'
                raise TypeError(msg)
            if not all([amount > 0 for amount in amounts]):
                msg = f'Investment amount should be larger than 0'
                raise ValueError(msg)

        if isinstance(dates, str):
            dates = dates.replace(' ', '')
            dates = dates.split(',')
        try:
            dates = list(map(pd.to_datetime, dates))
        except Exception as e:
            raise KeyError(f'{e}, some of the input strings can not be converted to date time format!')

        if not len(amounts) == len(dates):
            msg = f'Count of amounts should be equal to that of dates, can\'t match ' \
                  f'{len(amounts)} amounts into {len(dates)} days.'
            raise ValueError(msg)

        self._cash_plan = pd.DataFrame(amounts, index=dates, columns=['amount']).sort_index()
        if not isinstance(interest_rate, float):
            msg = f'Interest rate should be a float number, got {type(interest_rate)}'
            raise TypeError(msg)
        if not 0. <= interest_rate <= 1.:  # 0 <= interest_rate <= 1
            msg = f'InputError, interest rate should be between 0 and 100%, got {interest_rate:.2%}'
            raise ValueError(msg)
        self._ir = interest_rate

    @property
    def first_day(self):
        """ 返回投资第一天的日期

        Returns
        -------
        pd.Timestamp

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'], amounts=[10000, 10000, 15000])
        >>> plan.first_day
        Timestamp('2020-01-01 00:00:00')
        """
        if self.dates:
            return self.dates[0]
        else:
            return

    @property
    def last_day(self):
        """ 返回投资期最后一天的日期

        Returns
        -------
        pd.Timestamp

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'], amounts=[10000, 10000, 15000])
        >>> plan.last_day
        Timestamp('2021-01-01 00:00:00')
        """
        if self.dates:
            return self.dates[-1]
        else:
            return

    @property
    def period(self):
        """ 返回第一次投资到最后一次投资之间的时长，单位为天

        Returns
        -------
        int

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan.period
        366
        """
        if self.dates:
            return (self.last_day - self.first_day).days
        else:
            return 0

    @property
    def investment_count(self):
        """ 返回在整个投资计划期间的投资次数

        Returns
        -------
        int

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan.investment_count
        2
        """
        return len(self.dates)

    @property
    def dates(self):
        """ 返回整个投资计划期间的所有投资日期，按从先到后排列

        Returns
        -------
        list of pd.Timestamp

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'], amounts=[10000, 10000, 15000])
        >>> plan.dates
        [Timestamp('2020-01-01 00:00:00'),
         Timestamp('2020-06-01 00:00:00'),
         Timestamp('2021-01-01 00:00:00')]
        """
        return list(self.plan.index)

    @property
    def amounts(self):
        """ 返回整个投资计划期间的所有投资额列表，按从先到后排列

        Returns
        -------
        list of float

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'], amounts=[10000, 10000, 15000])
        >>> plan.amounts
        [10000.0, 15000.0, 10000.0]
        """
        return list(self.plan.amount)

    @property
    def total(self):
        """ 返回整个投资计划期间的投资额总和，不考虑利率

        Returns
        -------
        float, 所有投资金额的简单相加

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'], amounts=[10000, 10000, 15000])
        >>> plan.total
        35000.0
        """
        return self.plan.amount.sum()

    @property
    def ir(self):
        """ 无风险利率，年化利率

        Returns
        -------
        float
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'],
        ... amounts=[10000, 10000, 15000],
        ... interest_rate=0.03)
        >>> plan
        CashPlan(['20200101', '20200601', '20210101'], [10000, 15000, 10000], 0.03)
        >>> plan.ir
        0.03
        """
        return self._ir

    @ir.setter
    def ir(self, ir: float):
        """ 设置无风险利率 """
        assert isinstance(ir, float), f'The interest rate should be a float number, not {type(ir)}'
        assert 0. < ir < 1., f'Interest rate should be between 0 and 1'
        self._ir = ir

    @property
    def closing_value(self):
        """ 计算所有投资额按照无风险利率到最后一笔投资当天的终值

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'],
        ... amounts=[10000, 10000, 15000],
        ... interest_rate=0.03)
        >>> plan.closing_value
        35563.06
        """
        if self.ir == 0:
            return self.total
        else:
            df = self.plan.copy()
            df['days'] = (df.index[-1] - df.index).days
            df['fv'] = df.amount * (1 + self.ir) ** (df.days / 365.)
            return np.round(df.fv.sum(), 2)

    @property
    def opening_value(self):
        """ 计算所有投资额按照无风险利率在第一个投资日的现值

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101', '20200601'],
        ... amounts=[10000, 10000, 15000],
        ... interest_rate=0.03)
        >>> plan.opening_value
        34524.44
        """
        if self.ir == 0:
            return self.total
        else:
            df = self.plan.copy()
            df['days'] = (df.index - df.index[0]).days
            df['pv'] = df.amount / (1 + self.ir) ** (df.days / 365.)
            return np.round(df.pv.sum(), 2)

    @property
    def plan(self):
        """ 返回整个投资区间的投资计划

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan.plan
                    amount
        2020-01-01   10000
        2021-01-01   10000
        """

        return self._cash_plan

    def reset_dates(self, dates):
        """ 重设投资日期，dates必须为一个可迭代的日期时间序列，数量与CashPlan的投资
            期数相同，且可转换为datetime对象

        Parameters
        ----------
        dates: iterables
            一个可迭代的时间日期序列

        Returns
        -------
        None

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan
        CashPlan(['20200101', '20210101'], [10000, 10000], 0.0)
        >>> plan.reset_dates(['20200101', '20200601'])
        >>> plan
        CashPlan(['20200101', '20200601'], [10000, 10000], 0.0)
        """
        try:
            idx = pd.Index(dates, dtype='datetime64[ns]')
            self.plan.index = idx
        except Exception as e:
            print(f'{e}, ')

    def to_dict(self, keys: [list, tuple, np.ndarray] = None):
        """ 返回整个投资区间的投资计划，形式为字典。默认key为日期，如果明确给出keys，则使用参数keys

        Parameters
        ----------
        keys: iterables
            用于替代投资计划日期的可迭代对象

        Returns
        -------
        dict

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan
        CashPlan(['20200101', '20210101'], [10000, 10000], 0.0)
        >>> plan.to_dict()
        {Timestamp('2020-01-01 00:00:00'): 10000,
         Timestamp('2021-01-01 00:00:00'): 10000}
        >>> plan.to_dict(['1st invest', '2nd invest'])
        {'1st invest': 10000, '2nd invest': 10000}
        """

        if keys is None:
            return dict(self.plan.amount)
        else:
            # assert isinstance(keys, list), f'TypeError, keys should be list, got {type(keys)} instead.'
            assert len(keys) == len(self.amounts), \
                f'InputError, count of elements in keys should be same as that of investment amounts, expect ' \
                f'{len(self.amounts)}, got {len(keys)}'
            return dict(zip(keys, self.amounts))

    def info(self):
        """ 打印投资计划的所有信息

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan.info()
        <class 'qteasy.finance.CashPlan'>
        Investment contains multiple entries
        Investment Period from 2020-01-01 to 2021-01-01, lasting 366 days
        Total investment count: 2 entries, total invested amount: ¥20,000.00
        Interest rate: 0.00%, equivalent final value: ¥20,000.00:
                    amount
        2020-01-01   10000
        2021-01-01   10000
        memory usage: 136 bytes
        """
        import sys
        print(f'\n{type(self)}')
        if self.investment_count > 1:
            print('Investment contains multiple entries')
            print(f'Investment Period from {self.first_day.date()} to {self.last_day.date()}, '
                  f'lasting {self.period} days')
            print(f'Total investment count: {self.investment_count} entries, total invested amount: ¥{self.total:,.2f}')
            print(f'Interest rate: {self.ir:.2%}, equivalent final value: ¥{self.closing_value:,.2f}:')
        else:
            print(f'Investment is one-off amount of ¥{self.total:,.2f} on {self.first_day.date()}')
            print(f'Interest rate: {self.ir:.2%}, equivalent final value: ¥{self.closing_value:,.2f}:')
        print(self.plan)
        print(f'memory usage: {sys.getsizeof(self.plan)} bytes\n')

    def __add__(self, other):
        """ 将CashPlan与另一个对象相加

        两个CashPlan对象相加，得到一个金额合并后的的CashPlan对象
        CashPlan对象与一个int或float对象相加，得到的新的CashPlan对象的每笔投资都增加int或float数额

        Parameters
        ----------
        other: (int, float, CashPlan): 另一个对象，根据对象类型不同行为不同

        Returns
        -------
        cashplan

        Examples
        --------
        >>> plan1 = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan2 = CashPlan(dates=['20200601', '20210101'], amounts=[10000, 10000])
        >>> plan1 + 10000
        CashPlan(['20200101', '20210101'], [20000, 20000], 0.0)
        >>> plan1 + plan2
        CashPlan(['20200101', '20200601', '20210101'], [10000.0, 10000.0, 20000.0], 0.0)
        """

        if isinstance(other, (int, float)):
            # 当other是一个数字时，在新的CashPlan的每个投资日期的投资额上加上other元
            min_amount = np.min(self.amounts)
            assert other > -min_amount, \
                f'ValueError, the amount will cause illegal invest value in plan, {min_amount} - {other}'
            new_amounts = np.array(self.amounts) + other
            return CashPlan(self.dates, new_amounts, self.ir)
        elif isinstance(other, CashPlan):
            plan1 = self._cash_plan
            plan2 = other._cash_plan
            index_combo = list(plan1.index)
            index_combo.extend(list(plan2.index))
            index_combo = list(set(index_combo))  # 新的CashPlan的投资日期集合是两个CashPlan的并集
            plan1 = plan1.reindex(index_combo).fillna(0)  # 填充Nan值避免相加后产生Nan值
            plan2 = plan2.reindex(index_combo).fillna(0)
            plan = (plan1 + plan2).sort_index()
            if self.ir == 0:
                new_ir = other.ir
            else:
                new_ir = self.ir
            return CashPlan(list(plan.index), list(plan.amount), new_ir)
        else:
            raise TypeError(f'Only CashPlan and numbers are supported, got {type(other)}')

    def __radd__(self, other):
        """ 另一个对象other + CashPlan的结果与CashPlan + other相同， 即：
            other + CashPlan == CashPlan + other

        Parameters
        ----------
        other: (int, float, CashPlan): 另一个对象，根据对象类型不同行为不同

        Returns
        -------
        CashPlan: 新的CashPlan对象

        Examples
        --------
        >>> plan1 = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan2 = CashPlan(dates=['20200601', '20210101'], amounts=[10000, 10000])
        >>> 10000 + plan1
        CashPlan(['20200101', '20210101'], [20000, 20000], 0.0)
        >>> plan1 + plan2
        CashPlan(['20200101', '20200601', '20210101'], [10000.0, 10000.0, 20000.0], 0.0)
        """
        return self.__add__(other)

    def __mul__(self, other):
        """CashPlan乘以一个int或float返回一个新的CashPlan，它的投资数量和投资日期与CashPlan对象相同，每次投资额增加int或float倍

        Parameters
        ----------
        other: (int, float), 倍增一个cashplan的倍数

        Returns
        -------
        CashPlan: 新的CashPlan对象

        Examples
        --------
        >>> plan1 = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan1 * 2
        CashPlan(['20200101', '20210101'], [20000, 20000], 0.0)
        >>> plan1 * 0.5
        CashPlan(['20200101', '20210101'], [5000.0, 5000.0], 0.0)
        """
        assert isinstance(other, (int, float))
        assert other >= 0
        new_dates = list(self.dates)
        new_amounts = list(np.array(self.amounts) * other)
        return CashPlan(new_dates, new_amounts, self.ir)

    def __rmul__(self, other):
        """ other 乘以一个CashPlan的结果是一个新的CashPlan，结果取决于other的类型：

        other 为 int时，新的CashPlan的投资次数重复int次，投资额不变，投资日期按照相同的频率顺延，如果CashPlan只有一个投资日期时
            频率为一年
        other 为 float时，other * CashPlan == CashPlan * other

        Parameters
        ----------
        other: (int, float), 倍增或延长一个cashplan的倍数或次数

        Returns
        -------
        CashPlan: 新的CashPlan对象

        Examples
        --------
        >>> plan1 = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> 2 * plan1
        CashPlan(['20200101', '20210101', '20220103', '20230104'], [10000, 10000, 10000, 10000], 0.0)
        >>> 2.5 * plan1
        CashPlan(['20200101', '20210101'], [25000.0, 25000.0], 0.0)
        """
        assert isinstance(other, (int, float))
        if isinstance(other, int):
            assert other > 1
            one_day = pd.Timedelta(1, 'd')
            one_month = pd.Timedelta(31, 'd')
            one_quarter = pd.Timedelta(93, 'd')
            one_year = pd.Timedelta(365, 'd')
            if self.investment_count == 1:  # 如果只有一次投资，则以一年为间隔
                new_dates = [self.first_day + one_year * i for i in range(other)]
                return CashPlan(new_dates, self.amounts * other, self.ir)
            else:  # 如果有两次或以上投资，则计算首末两次投资之间的间隔，以此为依据计算未来投资间隔
                if self.investment_count == 2:  # 当只有两次投资时，新增投资的间距与频率与两次投资的间隔相同
                    time_offset = pd.Timedelta(self.period * 2, 'd')
                else:  # 当投资次数多于两次时，整个投资作为一个单元，未来新增投资为重复每个单元的投资。单元的跨度可以为月、季度及年
                    if self.period <= 28:
                        time_offset = one_month
                    elif self.period <= 90:
                        time_offset = one_quarter
                    elif self.period <= 365:
                        time_offset = one_year
                    else:
                        time_offset = one_year * (self.period // 365 + 1)
                # 获取投资间隔后，循环生成所有的投资日期
                original_dates = self.dates
                new_dates = self.dates
                for i in range(other - 1):
                    new_dates.extend([date + time_offset * (i + 1) + one_day for date in original_dates])
                return CashPlan(new_dates, self.amounts * other, self.ir)

        else:  # 当other是浮点数时，返回CashPlan * other 的结果
            return self.__mul__(other)

    def __repr__(self):
        """ 打印cash plan

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan
        CashPlan(['20200101', '20210101'], [10000, 10000], 0.0)
        """
        dates = self.plan.index.strftime('%Y%m%d').to_list()
        return f'CashPlan({dates}, {self.amounts}, {self.ir})'

    def __str__(self):
        """ 打印cash plan

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> print(plan)
        CashPlan(['20200101', '20210101'], [10000, 10000], 0.0)
        """
        return self._cash_plan.__str__()

    def __getitem__(self, item):
        """ 获取cash plan中某一天的投资金额

        Parameters
        ----------
        item: (int, datetimelike), 用于索引cash plan的索引器

        Returns
        -------
        dict, cash plan中的一个部分

        Examples
        --------
        >>> plan = CashPlan(dates=['20200101', '20210101'], amounts=[10000, 10000])
        >>> plan[0]
        {'amount': 10000}
        >>> plan['20200101']
        {'amount': 10000}
        >>> plan['2020-01-01']
        {'amount': 10000}
        """
        if isinstance(item, int):
            return self.plan.iloc[item].to_dict()
        else:
            return self.plan.loc[item].to_dict()


# TODO: 实现多种方式的定投计划，可定制周期、频率、总金额、单次金额等简单功能，同时还应支持递增累进式定投、按照公式定投等高级功能
def distribute_investment(amount: float,
                          start: str,
                          end: str,
                          periods: int,
                          freq: str) -> CashPlan:
    """ 将投资额拆分成一系列定投金额，并生成一个CashPlan对象

    Parameters
    ----------
    amount:
    start:
    end:
    periods:
    freq:

    Returns
    -------
    cashplan:
    """
    raise NotImplementedError
