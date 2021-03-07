# coding=utf-8
# finance.py

# ======================================
# This file contains classes that are
# related to investment financial figures
# such as operation cost (Cost class) and
# investment plans (CashPlan class) as
# well more related functions.
# ======================================

import numpy as np
import pandas as pd
from numba import jit, int64, float64
from collections import Iterable


class Cost:
    """ 交易成本类，用于在回测过程中对交易成本进行估算

    交易成本的估算依赖三种类型的成本：
    1， fix：type：float，固定费用，在交易过程中产生的固定现金费用，与交易金额和交易量无关： 固定费用 = 固定费用
    2， fee：type：float，交易费率，或者叫一阶费率，交易过程中的固定费率，交易费用 = 交易金额 * 交易费率
    3， slipage：type：float，交易滑点，或者叫二阶费率。
        用于模拟交易过程中由于交易延迟或买卖冲击形成的交易成本，滑点绿表现为一个关于交易量的函数, 交易
        滑点成本等于该滑点率乘以交易金额： 滑点成本 = f(交易金额） * 交易成本
    """

    def __init__(self,
                 buy_fix: float = 0.0,
                 sell_fix: float = 0.0,
                 buy_rate: float = 0.003,
                 sell_rate: float = 0.001,
                 buy_min: float = 5.0,
                 sell_min: float = 0.0,
                 slipage: float = 0.0):
        self.buy_fix = float(buy_fix)
        self.sell_fix = float(sell_fix)
        self.buy_rate = float(buy_rate)
        self.sell_rate = float(sell_rate)
        self.buy_min = float(buy_min)
        self.sell_min = float(sell_min)
        self.slipage = float(slipage)

    def __str__(self):
        """设置Rate对象的打印形式"""
        return f'<Buying: {self.buy_fix}, rate:{self.buy_rate}, slipage:{self.slipage}\n' \
               f'Selling: {self.sell_fix}, rate:{self.sell_rate}>'

    def __repr__(self):
        """设置Rate对象"""
        return f'Rate({self.fix}, {self.fee}, {self.slipage})'

    # TODO: Rate对象的调用结果应该返回交易费用而不是交易费率，否则固定费率就没有意义了(交易固定费用在回测中计算较为复杂)
    def __call__(self,
                 trade_values: np.ndarray,
                 is_buying: bool = True,
                 fixed_fees: bool = False) -> float:
        """直接调用对象，计算交易费率或交易费用

        采用两种模式计算：
            当fixed_fees为True时，采用固定费用模式计算，返回值为包含滑点的交易成本列表，
            当fixed_fees为False时，采用固定费率模式计算，返回值为包含滑点的交易成本率列表

        :param trade_values: ndarray: 总交易金额清单
        :param is_buying: bool: 当前是否计算买入费用或费率
        :param fixed_fees: bool: 当前是否采用固定费用模式计算
        :return:
        np.ndarray,
        """
        bf = self.buy_fix
        sf = self.sell_fix
        br = self.buy_rate
        sr = self.sell_rate
        bm = self.buy_min
        sm = self.sell_min
        slp = self.slipage
        return _calculate_fee(trade_values.astype('float'),
                              fixed_fees,
                              is_buying,
                              bf, sf, br, sr, bm, sm, slp)

    def __getitem__(self, item: str) -> float:
        """通过字符串获取Rate对象的某个组份（费率、滑点或冲击率）"""
        assert isinstance(item, str), 'TypeError, item should be a string in ' \
                                      '[\'buy_fix\', \'sell_fix\', \'buy_rate\', \'sell_rate\',' \
                                      ' \'buy_min\', \'sell_min\',\'slipage\']'
        if item == 'buy_fix':
            return self.buy_fix
        elif item == 'sell_fix':
            return self.sell_fix
        elif item == 'buy_rate':
            return self.buy_rate
        elif item == 'sell_rate':
            return self.sell_rate
        elif item == 'buy_min':
            return self.buy_min
        elif item == 'sell_min':
            return self.sell_min
        elif item == 'slipage':
            return self.slipage
        else:
            raise TypeError

    # @numba.njit
    def get_selling_result(self, prices: np.ndarray, op: np.ndarray, amounts: np.ndarray, moq: float = 0):
        """计算出售投资产品的要素


        :param prices: 投资产品的价格
        :param op: 交易信号
        :param amounts: 持有投资产品的份额
        :param moq: 卖出股票的最小交易单位

        :return:
        a_sold:
        fee:
        cash_gained: float
        fee: float
        """
        if moq == 0:
            a_sold = np.sign(prices) * np.where(op < 0, amounts * op, 0)
        else:
            a_sold = np.sign(prices) * np.where(op < 0, amounts * op // moq * moq, 0)
        sold_values = a_sold * prices
        if self.sell_fix == 0:  # 固定交易费用为0，按照交易费率模式计算
            rates = self.__call__(trade_values=amounts * prices, is_buying=False, fixed_fees=False)
            cash_gained = (-1 * sold_values * (1 - rates)).sum()
            fee = (sold_values * rates).sum()
        else:
            fixed_fees = self.__call__(trade_values=amounts * prices, is_buying=False, fixed_fees=True)
            fee = -np.where(a_sold, fixed_fees, 0).sum()
            cash_gained = - sold_values.sum() + fee
        return a_sold, cash_gained, fee

    # @numba.njit
    def get_purchase_result(self, prices: np.ndarray, op: np.ndarray, pur_values: [np.ndarray, float], moq: float):
        """获得购买资产时的要素

        :param prices: ndarray, 投资组合中每只股票的当前单价
        :param op: ndarray, 操作矩阵，针对投资组合中的每只股票的买卖操作，>0代表买入或平空仓,<0代表卖出或平多仓，绝对值表示买卖比例
        :param pur_values: ndarray, 买入金额，可用于买入股票或资产的计划金额
        :param moq: float, 最小交易单位
        :return:
        a_purchased: 一个ndarray, 代表所有股票分别买入的份额或数量
        cash_spent: float，花费的总金额，包括费用在内
        fee: 花费的费用，购买成本，包括佣金和滑点等投资成本
        """
        if self.buy_fix == 0.:
            # 固定费用为0，按照费率模式计算
            rates = self.__call__(trade_values=pur_values, is_buying=True, fixed_fees=False)
            # debug
            # print(f'purchase rate is {rates}')
            # 费率模式下，计算综合费率（包含滑点）
            if moq == 0:  # moq为0，买入份额数为任意分数份额
                a_purchased = np.where(prices,
                                       np.where(op > 0,
                                                pur_values / (prices * (1 + rates)),
                                                0),
                                       0)
            else:  # moq不为零，买入份额必须是moq的倍数
                a_purchased = np.where(prices,
                                       np.where(op > 0,
                                                pur_values // (prices * moq * (1 + rates)) * moq,
                                                0),
                                       0)
            cash_spent = np.where(a_purchased, -1 * a_purchased * prices * (1 + rates), 0)
            fee = -(cash_spent * rates / (1 + rates)).sum()
        elif self.buy_fix:
            # 固定费用不为0，按照固定费用模式计算费用，忽略费率并且忽略最小费用，只计算买入金额大于固定费用的份额
            fixed_fees = self.__call__(trade_values=pur_values, is_buying=True, fixed_fees=True)
            if moq == 0:
                a_purchased = np.fmax(np.where(prices,
                                               np.where(op > 0,
                                                        (pur_values - fixed_fees) / prices,
                                                        0),
                                               0),
                                      0)
            else:
                a_purchased = np.fmax(np.where(prices,
                                               np.where(op > 0,
                                                        (pur_values - fixed_fees) // (prices * moq) * moq,
                                                        0),
                                               0),
                                      0)
            cash_spent = np.where(a_purchased, -1 * a_purchased * prices - fixed_fees, 0)
            fee = np.where(a_purchased, fixed_fees, 0).sum()
        return a_purchased, cash_spent.sum(), fee


@jit(float64[:](float64[:], int64, int64, float64, float64, float64, float64, float64, float64, float64), nopython=True)
def _calculate_fee(trade_values, fixed_fees, is_buying, bf, sf, br, sr, bm, sm, slp):
    """calculate the transaction fee given all parameters

    """
    if fixed_fees:  # 采用固定费用模式计算
        if is_buying:
            return bf + slp * trade_values ** 2
        else:
            return sf + slp * trade_values ** 2
    else:  # 采用固定费率模式计算
        if is_buying:
            if bm == 0.:
                return br + slp * trade_values
            else:
                min_rate = bm / (trade_values - bm)
                return np.fmax(br, min_rate) + slp * trade_values
        else:
            if sm == 0.:
                return sr + slp * trade_values
            else:
                min_rate = sm / trade_values
                return np.fmax(sr, min_rate) + slp * trade_values


# TODO: 在qteasy中所使用的所有时间日期格式统一使用pd.TimeStamp格式
class CashPlan:
    """ 现金计划类，在策略回测的过程中用来模拟固定日期的现金投资额

    投资计划对象包含一组带时间戳的投资金额数据，用于模拟在固定时间的现金投入，可以实现对一次性现金投入和资金定投的模拟
    """

    def __init__(self, dates: [list, str], amounts: [list, str, int, float], interest_rate: float = 0.0):
        """

        :param dates:
        :param amounts:
        :param interest_rate: float
        """
        if isinstance(amounts, (int, float)):
            amounts = [amounts]
        assert isinstance(amounts,(list, np.ndarray)), \
            f'TypeError: amounts should be a list of numbers, got {type(amounts)} instead'
        if isinstance(amounts, list):
            assert all([isinstance(amount, (int, float, np.int64, np.float64)) for amount in amounts]), \
                f'TypeError: amount should be number format, got {type(amount)} instead'
            assert all([amount > 0 for amount in amounts]), f'InputError: Investment amount should be larger than 0'
        assert isinstance(dates, Iterable), f"Expect Iterable input dates, got {type(dates)} instead!"

        if isinstance(dates, str):
            dates = dates.replace(' ', '')
            dates = dates.split(',')
        try:
            dates = list(map(pd.to_datetime, dates))
        except:
            raise KeyError(f'some of the input strings can not be converted to date time format!')

        assert len(amounts) == len(dates), \
            f'InputError: number of amounts should be equal to that of dates, can\'t match {len(amounts)} amounts in' \
            f' to {len(dates)} days.'

        self._cash_plan = pd.DataFrame(amounts, index=dates, columns=['amount']).sort_index()
        assert isinstance(interest_rate, float), \
            f'TypeError, interest rate should be a float number, got {type(interest_rate)}'
        assert 0. <= interest_rate <= 1., \
            f'InputError, interest rate should be between 0 and 100%, got {interest_rate:.2%}'
        self._ir = interest_rate

    @property
    def first_day(self):
        """ 返回投资第一天的日期

        :return: pd.Timestamp
        """
        return self.dates[0]

    @property
    def last_day(self):
        """ 返回投资期最后一天的日期

        :return: pd.Timestamp
        """
        return self.dates[-1]

    @property
    def period(self):
        """ 返回第一次投资到最后一次投资之间的时长，单位为天

        :return: int
        """
        return (self.last_day - self.first_day).days

    @property
    def investment_count(self):
        """ 返回在整个投资计划期间的投资次数

        :return: int
        """
        return len(self.dates)

    @property
    def dates(self):
        """ 返回整个投资计划期间的所有投资日期，按从先到后排列

        :return: list[pandas.Timestamp]
        """
        return list(self.plan.index)

    @property
    def amounts(self):
        """ 返回整个投资计划期间的所有投资额列表，按从先到后排列

        :return: list[float]
        """
        return list(self.plan.amount)

    @property
    def total(self):
        """ 返回整个投资计划期间的投资额总和，不考虑利率

        :return: float
        """
        return self.plan.amount.sum()

    @property
    def ir(self):
        """ 无风险利率，年化利率

        :return: float
        """
        return self._ir

    @ir.setter
    def ir(self, ir: float):
        """ 设置无风险利率

        :param ir: float, 无风险利率
        :return:
        """
        assert isinstance(ir, float), f'The interest rate should be a float number, not {type(ir)}'
        assert 0. < ir < 1., f'Interest rate should be between 0 and 1'
        self._ir = ir

    @property
    def closing_value(self):
        """ 计算所有投资额按照无风险利率到最后一个投资额的终值

        :return: float
        """
        if self.ir == 0:
            return self.total
        else:
            df = self.plan.copy()
            df['days'] = (df.index[-1] - df.index).days
            df['fv'] = df.amount * (1 + self.ir) ** (df.days / 365.)
            return df.fv.sum()

    @property
    def opening_value(self):
        """ 计算所有投资额按照无风险利率在第一个投资日的现值

        :return: float
        """
        if self.ir == 0:
            return self.total
        else:
            df = self.plan.copy()
            df['days'] = (df.index - df.index[0]).days
            df['pv'] = df.amount / (1 + self.ir) ** (df.days / 365.)
            return df.pv.sum()

    @property
    def plan(self):
        """ 返回整个投资区间的投资计划，形式为DataFrame

        :return: pandas.DataFrame
        """
        return self._cash_plan

    def to_dict(self, keys: [list, np.ndarray] = None):
        """ 返回整个投资区间的投资计划，形式为字典。默认key为日期，如果明确给出keys，则使用参数keys

        :return: dict
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

        :return: None
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
        """ 两个CashPlan对象相加，得到一个新的CashPlan对象，这个对象包含两个CashPlan对象的投资计划的并集，如果两个投资计划的时间
            相同，则新的CashPlan的投资计划每个投资日的投资额是两个投资计划的和

            CashPlan对象与一个int或float对象相加，得到的新的CashPlan对象的每笔投资都增加int或float数额

        :param other: (int, float, CashPlan): 另一个对象，根据对象类型不同行为不同
        :return:
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

        :param other:
        :return:
        """
        return self.__add__(other)

    def __mul__(self, other):
        """CashPlan乘以一个int或float返回一个新的CashPlan，它的投资数量和投资日期与CashPlan对象相同，每次投资额增加int或float倍

        :param other: (int, float):
        :return:
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

        :param other:
        :return:
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
        """

        :return:
        """
        return self.__str__()

    def __str__(self):
        """ 打印cash plan

        :return:
        """
        return self._cash_plan.__str__()

    def __getitem__(self, item):
        """

        :param item:
        :return:
        """
        return self.plan[item]


# TODO: 实现多种方式的定投计划，可定制周期、频率、总金额、单次金额等简单功能，同时还应支持递增累进式定投、按照公式定投等高级功能
def distribute_investment(amount: float,
                          start: str,
                          end: str,
                          periods: int,
                          freq: str) -> CashPlan:
    """ 将投资额拆分成一系列定投金额，并生成一个CashPlan对象

    :param amount:
    :param start:
    :param end:
    :param periods:
    :param freq:
    :return:
    """

