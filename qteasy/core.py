# coding=utf-8
# core.py

import pandas as pd
import numpy as np
import datetime
import itertools
from qteasy.utilfuncs import *
from .history import HistoryPanel


class Log:
    """ 数据记录类，策略选股、择时、风险控制、交易信号生成、回测等过程中的记录的基类


    """

    def __init__(self):
        """

        """
        self.record = None
        raise NotImplementedError

    def write_record(self, *args):
        """

        :param args:
        :return:
        """

        raise NotImplementedError


class Context:
    """QT Easy量化交易系统的上下文对象，保存所有相关环境变量及(伪)常量

    所有系统执行相关的变量都存储在Context对象中，在调用core模块中的主要公有方法时，应该引用Context对象以提供所有的环境变量。

    包含的常量：
    ========
        RUN_MODE_LIVE = 0
        RUN_MODE_BACKLOOP = 1
        RUN_MODE_OPTIMIZE = 2

    包含的变量：
    ========
        运行模式变量：
            mode，运行模式，包括实盘模式、回测模式和优化模式三种方式
        实盘模式相关变量：

        回测费率变量：

        回测历史区间变量：

        优化模式变量：

        优化区间变量：

        优化目标函数变量：
    """
    # 环境常量
    # ============
    RUN_MODE_LIVE = 0
    RUN_MODE_BACKLOOP = 1
    RUN_MODE_OPTIMIZE = 2

    OPTI_EXHAUSTIVE = 0
    OPTI_MONTECARLO = 1
    OPTI_INCREMENTAL = 2
    OPTI_GA = 3

    def __init__(self,
                 mode: int = RUN_MODE_BACKLOOP,
                 rate_fee: float = 0.003,
                 rate_slipery: float = 0,
                 moq: int = 100,
                 investment_amounts: list = None,
                 investment_dates: list = None,
                 riskfree_interest_rate: float = 0.035,
                 visual: bool = False,
                 reference_visual: bool = False,
                 reference_data: str = None):
        """初始化所有的环境变量和环境常量

        input:
            :param mode:
            :param rate_fee:
            :param rate_slipery:
            :param moq:
            :param init_cash:
            :param visual:
            :param reference_visual:
            :param reference_data:
        """

        self.mode = mode
        self.rate = Rate(0, rate_fee, rate_slipery)
        self.moq = moq  # 最小交易批量，设置为0表示可以买卖分数股
        assert investment_dates is not None, \
            f'InputError, investment dates should be given, got {type(investment_dates)}'
        self.cash_plan = CashPlan(dates=investment_dates,
                                  amounts=investment_amounts,
                                  interest_rate=riskfree_interest_rate)  # 回测初始现金金额
        # TODO： 将整数形式的初始现金金额修改为投资现金对象CashPlan
        today = datetime.datetime.today().date()
        self.share_pool = []  # 优化参数所针对的投资产品
        self.opt_period_start = today - datetime.timedelta(3650)  # 默认优化历史区间开始日是十年前
        self.opt_period_end = today - datetime.timedelta(365)  # 优化历史区间结束日
        self.opt_period_freq = 'd'  # 优化历史区间采样频率
        self.loop_period_start = today - datetime.timedelta(3650)  # 测试区间开始日
        self.loop_period_end = today  # 测试区间结束日（测试区间的采样频率与优化区间相同）
        self.loop_period_freq = 'd'
        self.loop_hist_data_type = 'close'
        self.t_func_type = 1  # 'single'
        self.t_func = 'FV'  # 评价函数
        self.compound_method_expr = '( FV + Sharp )'  # 复合评价函数表达式，使用表达式解析模块解析并计算
        self.opti_method = Context.OPTI_EXHAUSTIVE
        self.output_count = 50
        self.keep_largest_perf = True
        self.history_data_types = ['close']
        self.history_data = None
        self.visual = visual
        self.reference_visual = reference_visual
        self.reference_data = reference_data

    def __str__(self):
        """定义Context类的打印样式"""
        out_str = list()
        out_str.append('qteasy running information:')
        out_str.append('===========================')
        return ''.join(out_str)


# TODO: 对Rate对象进行改进，实现以下功能：1，最低费率，2，卖出和买入费率不同，3，固定费用，4，与交易量相关的一阶费率，
# TODO: 5，与交易量相关的二阶费率
class Rate:
    """ 交易费率类，用于在回测过程中对交易成本进行估算

    交易成本的估算依赖三个参数：
    1， fix：type：float，固定费率，在交易过程中产生的固定现金费用，与交易金额和交易量无关： 固定费用 = 固定费用
    2， fee：type：float，交易费率，交易过程中的固定费率，交易费用 = 交易金额 * 交易费率
    3， slipage：type：float，交易滑点，用于模拟交易过程中由于交易延迟或买卖冲击形成的交易成本，滑点绿表现为一个关于交易量的函数, 交易
        滑点成本等于该滑点率乘以交易金额： 滑点成本 = f(交易金额） * 交易成本
    """

    def __init__(self, fix: float = 0, fee: float = 0.003, slipage: float = 0):
        self.fix = fix
        self.fee = fee
        self.slipage = slipage

    def __str__(self):
        """设置Rate对象的打印形式"""
        return f'<fixed fee: {self.fix}, rate fee:{self.fee}, slipage:{self.slipage}>'

    def __repr__(self):
        """设置Rate对象"""
        return f'Rate({self.fix}, {self.fee}, {self.slipage})'

    # TODO: Rate对象的调用结果应该返回交易费用而不是交易费率，否则固定费率就没有意义了(交易固定费用在回测中计算较为复杂)
    def __call__(self, amount: np.ndarray):
        """直接调用对象，计算交易费率"""
        return self.fee + self.slipage * amount

    def __getitem__(self, item: str) -> float:
        """通过字符串获取Rate对象的某个组份（费率、滑点或冲击率）"""
        assert isinstance(item, str), 'TypeError, item should be a string in [\'fix\', \'fee\', \'slipage\']'
        if item == 'fix':
            return self.fix
        elif item == 'fee':
            return self.fee
        elif item == 'slipage':
            return self.fee
        else:
            raise TypeError


# TODO：在Cash类中增加现金投资的无风险利率，在apply_loop的时候，可以选择是否考虑现金的无风险利率，如果考虑时，现金按照无风险利率增长
# TODO: 在qteasy中所使用的所有时间日期格式统一使用np.datetime64格式
class CashPlan:
    """ 现金计划类，在策略回测的过程中用来模拟固定日期的现金投资额

    投资计划对象包含一组带时间戳的投资金额数据，用于模拟在固定时间的现金投入，可以实现对一次性现金投入和资金定投的模拟
    """

    def __init__(self, dates, amounts, interest_rate: float = 0.0):
        """

        :param dates:
        :param amounts:
        :param interest_rate: float
        """
        from collections import Iterable
        if isinstance(amounts, int) or isinstance(amounts, float):
            amounts = [amounts]
        assert isinstance(amounts, list), f'TypeError: amounts should be Iterable, got {type(amounts)} instead'
        for amount in amounts:
            assert isinstance(amount, float) or isinstance(amount, int), \
                f'TypeError: amount should be number format, got {type(amount)} instead'
            assert amount > 0, f'InputError: Investment amount should be larger than 0'
        assert isinstance(dates, Iterable)

        if isinstance(dates, str):
            dates = dates.replace(' ', '')
            dates = dates.split(',')
        try:
            dates = list(map(pd.to_datetime, dates))
        except:
            raise KeyError

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
        assert isinstance(ir, float)
        assert 0. < ir < 1.
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

    def to_dict(self, keys: list = None):
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
        """

        :param other:
        :return:
        """
        raise NotImplementedError

    def __mul__(self, other):
        """

        :param other:
        :return:
        """
        raise NotImplementedError

    def __repr__(self):
        """

        :return:
        """
        raise NotImplementedError

    def __str__(self):
        """

        :return:
        """
        return f'type(self)'

    def __getitem__(self, item):
        """

        :param item:
        :return:
        """
        return self.plan[item]


# TODO: 实现多种方式的定投计划，可定制周期、频率、总金额、单次金额等简单功能，同时还应支持递增累进式定投、按照公式定投等高级功能
def distribute_investment(amount, start, end, periods, freq):
    """ 将投资额拆分成一系列定投金额，并生成一个CashPlan对象

    :param amount:
    :param start:
    :param end:
    :param periods:
    :param freq:
    :return:
    """


# TODO: 使用Numba加速_loop_step()函数
def _loop_step(pre_cash, pre_amounts, op, prices, rate, moq):
    """ 对单次交易进行处理，采用向量化计算以提升效率

    input：=====
        param pre_cash, np.ndarray：本次交易开始前账户现金余额
        param pre_amounts, np.ndarray：list，交易开始前各个股票账户中的股份余额
        param op, np.ndarray：本次交易的个股交易清单
        param prices：np.ndarray，本次交易发生时各个股票的价格
        param rate：object Rate 交易成本率对象
        param moq：float: 投资产品最小交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

    return：===== tuple，包含四个元素
        cash：交易后账户现金余额
        amounts：交易后每个个股账户中的股份余额
        fee：本次交易总费用
        value：本次交易后资产总额（按照交易后现金及股份余额以及交易时的价格计算）
    """
    # 计算交易前现金及股票余额在当前价格下的资产总额
    pre_value = pre_cash + (pre_amounts * prices).sum()
    # 计算按照交易清单出售资产后的资产余额以及获得的现金
    # 如果MOQ不要求出售的投资产品份额为整数，可以省去rint处理
    if moq == 0:
        a_sold = np.where(prices != 0,
                          np.where(op < 0, pre_amounts * op, 0),
                          0)
    else:
        a_sold = np.where(prices != 0,
                          np.where(op < 0, np.rint(pre_amounts * op), 0),
                          0)
    rate_out = rate(a_sold * prices)
    cash_gained = np.where(a_sold < 0, -1 * a_sold * prices * (1 - rate_out), 0)
    # 本期出售资产后现金余额 = 期初现金余额 + 出售资产获得现金总额
    cash = pre_cash + cash_gained.sum()
    # 初步估算按照交易清单买入资产所需要的现金，如果超过持有现金，则按比例降低买入金额
    pur_values = pre_value * op.clip(0)  # 使用clip来代替np.where，速度更快,且op.clip(1)比np.clip(op, 0, 1)快很多
    if pur_values.sum() > cash:
        # 估算买入资产所需现金超过持有现金
        pur_values = pur_values / pre_value * cash
        # 按比例降低分配给每个拟买入资产的现金额度
    # 计算购入每项资产实际花费的现金以及实际买入资产数量，如果MOQ不为0，则需要取整并修改实际花费现金额
    rate_in = rate(pur_values)
    if moq == 0:  # MOQ为零时，可以购入的资产数量允许为小数
        a_purchased = np.where(prices != 0,
                               np.where(op > 0,
                                        pur_values / (prices * (1 + rate_in)), 0), 0)
    else:  # 否则，使用整除方式确保购入的资产数量为MOQ的整数倍，MOQ非整数时仍然成立
        a_purchased = np.where(prices != 0,
                               np.where(op > 0,
                                        pur_values // (prices * moq * (1 + rate_in)) * moq,
                                        0), 0)
    # 由于MOQ的存在，需要根据实际购入的资产数量确定花费的现金资产
    # 仅当a_purchased大于零时计算花费的现金额
    cash_spent = np.where(a_purchased > 0,
                          -1 * a_purchased * prices * (1 + rate_in), 0)

    # 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = np.where(op == 0, 0,
                   np.where(op > 0, -1 * cash_spent * rate_in,
                            cash_gained * rate_out)).sum()
    # 持有资产总额 = 期初资产余额 + 本期买入资产总额 + 本期卖出资产总额（负值）
    amounts = pre_amounts + a_purchased + a_sold
    # 期末现金余额 = 本期出售资产后余额 + 本期购入资产花费现金总额（负值）
    cash += cash_spent.sum()
    # 期末资产总价值 = 期末资产总额 * 本期资产单价 + 期末现金余额
    value = (amounts * prices).sum() + cash
    return cash, amounts, fee, value


def _get_complete_hist(looped_value, h_list, with_price=False):
    """完成历史交易回测后，填充完整的历史资产总价值清单

    input:=====
        :param values：完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
        :param h_list：完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
        :param with_price：Bool，True时在返回的清单中包含历史价格，否则仅返回资产总价值
    return: =====
        values，pandas.DataFrame：重新填充的完整历史交易日资产总价值清单
    """
    # 获取价格清单中的投资产品列表
    # print(f'looped values raw data info: {looped_value.info()}')
    shares = h_list.columns
    start_date = looped_value.index[0]
    looped_history = h_list.loc[start_date:]
    # print(f'looped history info: \n{looped_history.info()}')
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    purchased_shares = looped_value[shares].reindex(looped_history.index, method='ffill').fillna(0)
    cashes = looped_value['cash'].reindex(looped_history.index, method='ffill').fillna(0)
    fees = looped_value['fee'].reindex(looped_history.index).fillna(0)
    looped_value = looped_value.reindex(looped_history.index)
    looped_value[shares] = purchased_shares
    looped_value.fee = fees
    looped_value.cash = cashes
    # print(f'extended looped value according to looped history: \n{looped_value.info()}')
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象
    looped_value['value'] = (looped_history * looped_value[shares]).sum(axis=1) + looped_value['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        share_price_column_names = []
        for name in shares:
            share_price_column_names.append(name + '_p')
        looped_value[share_price_column_names] = looped_history[shares]
    return looped_value


# TODO：回测主入口函数需要增加现金计划、多种回测结果评价函数、回测过程log记录、回测结果可视化和回测结果参照标准
# TODO：增加一个参数，允许用户选择是否考虑现金的无风险利率增长
def apply_loop(op_list: pd.DataFrame,
               history_list: pd.DataFrame,
               visual: bool = False,
               price_visual: bool = False,
               cash_plan: CashPlan = None,
               cost_rate: Rate = None,
               moq: float = 100.):
    """使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
        现金额及费用，输出的结果可选

    input：=====
        :type cash_plan: float: 初始资金额，未来将被替换为CashPlan对象
        :type price_visual: Bool: 选择是否在图表输出时同时输出相关资产价格变化，visual为False时无效，未来将增加reference数据
        :type history_list: object pd.DataFrame: 完整历史价格清单，数据的频率由freq参数决定
        :type visual: Bool: 可选参数，默认False，仅在有交易行为的时间点上计算持仓、现金及费用，
                            为True时将数据填充到整个历史区间，并用图表输出
        :type op_list: object pd.DataFrame: 标准格式交易清单，描述一段时间内的交易详情，每次交易一行数据
        :type cost_rate: float Rate: 交易成本率对象，包含交易费、滑点及冲击成本
        :type moq: float：每次交易的最小份额

    output：=====
        Value_history：包含交易结果及资产总额的历史清单

    """
    assert not op_list.empty, 'InputError: The Operation list should not be Empty'
    assert cost_rate is not None, 'TyepError: cost_rate should not be None type'

    # 根据最新的研究实验，在python3.6的环境下，nditer的速度显著地慢于普通的for-loop
    # 因此改回for-loop执行，知道找到更好的向量化执行方法

    op = op_list.values
    price = history_list.fillna(0).loc[op_list.index].values
    looped_dates = list(op_list.index)
    if cash_plan is None:
        cash_plan = CashPlan(dates=looped_dates[0], amounts=100000, interest_rate=0)
    op_count = op.shape[0]  # 获取行数
    investment_date_pos = np.searchsorted(looped_dates, cash_plan.dates)
    invest_dict = cash_plan.to_dict(investment_date_pos)
    # print(f'investment date position calculated: {investment_date_pos}')
    # 初始化计算结果列表
    cash = 0  # 持有现金总额，初始化为初始现金总额
    amounts = [0] * len(history_list.columns)  # 投资组合中各个资产的持有数量，初始值为全0向量
    cashes = []  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
    fees = []  # 交易费用，记录每个操作时点产生的交易费用
    values = []  # 资产总价值，记录每个操作时点的资产和现金价值总和
    amounts_matrix = []
    for i in range(op_count):  # 对每一行历史交易信号开始回测
        if i in investment_date_pos:
            cash += invest_dict[i]
            # print(f'In loop process, on loop position {i} cash increased from {cash - invest_dict[i]} to {cash}')
        cash, amounts, fee, value = _loop_step(pre_cash=cash,
                                               pre_amounts=amounts,
                                               op=op[i], prices=price[i],
                                               rate=cost_rate,
                                               moq=moq)
        # 保存计算结果
        cashes.append(cash)
        fees.append(fee)
        values.append(value)
        amounts_matrix.append(amounts)
    # 将向量化计算结果转化回DataFrame格式
    value_history = pd.DataFrame(amounts_matrix, index=op_list.index,
                                 columns=op_list.columns)
    # 填充标量计算结果
    value_history['cash'] = cashes
    value_history['fee'] = fees
    value_history['value'] = values
    if visual:  # Visual参数为True时填充完整历史记录并
        complete_value = _get_complete_hist(looped_value=value_history,
                                            h_list=history_list,
                                            with_price=price_visual)
        # 输出相关资产价格
        if price_visual:  # 当Price_Visual参数为True时同时显示所有的成分股票的历史价格
            shares = history_list.columns
            complete_value.plot(grid=True, figsize=(15, 7), legend=True,
                                secondary_y=shares)
        else:  # 否则，仅显示总资产的历史变化情况
            complete_value.plot(grid=True, figsize=(15, 7), legend=True)
        return complete_value
    return value_history


def run(operator, context, mode: int = None, history_data: pd.DataFrame = None):
    """开始运行，qteasy模块的主要入口函数

        接受context上下文对象和operator执行器对象作为主要的运行组件，根据输入的运行模式确定运行的方式和结果
        根据context中的设置和运行模式（mode）进行不同的操作：
        context.mode == 0 or mode == 0:
            进入实时信号生成模式：
            根据context实时策略运行所需的历史数据，根据历史数据实时生成操作信号
            策略参数不能为空
        context.mode == 1 or mode == 1:
            进入回测模式：
            根据context规定的回测区间，使用History模块联机读取或从本地读取覆盖整个回测区间的历史数据
            生成投资资金模型，模拟在回测区间内使用投资资金模型进行模拟交易的结果
            输出对结果的评价（使用多维度的评价方法）
            输出回测日志·
            投资资金模型不能为空，策略参数不能为空
        context.mode == 2 or mode == 2:
            进入优化模式：
            根据context规定的优化区间和回测区间，使用History模块联机读取或本地读取覆盖整个区间的历史数据
            生成待优化策略的参数空间，并生成投资资金模型
            使用指定的优化方法在优化区间内查找投资资金模型的全局最优或局部最优参数组合集合
            使用在优化区间内搜索到的全局最优策略参数在回测区间上进行多次回测并再次记录结果
            输出最优参数集合在优化区间和回测区间上的评价结果
            输出优化及回测日志
            投资资金模型不能为空，策略参数可以为空
    input：

        :param operator: Operator()，策略执行器对象
        :param context: Context()，策略执行环境的上下文对象
        :param mode: int, default to None，qteasy运行模式，如果给出则override context中的mode参数
        :param history_data: pd.DataFrame, default to None, 参与执行所需的历史数据，如果给出则overidecontext 中的hist参数
        other params
    return：=====
        type: Log()，运行日志记录，txt 或 pd.DataFrame
    """
    import time
    # 从context 上下文对象中读取运行所需的参数：
    # 股票清单或投资产品清单
    shares = context.share_pool
    reference_data = context.reference_data
    # 如果没有显式给出运行模式，则按照context上下文对象中的运行模式运行，否则，适用mode参数中的模式
    if mode is None:
        run_mode = context.mode
    else:
        run_mode = mode
    # 如果没有显式给出 history_data 历史数据，则按照context上下文对象设定的回测、优化区间及频率参数建立历史数据，否则适用history_data 数据
    # TODO： 直接给出history_data是一个没有明确定义的操作：history_data被用于回测？还是优化？如何确保符合op的要求？详见下方hist_data_req
    # TODO： 对于策略生成、策略回测和策略优化有可能应用不同的历史数据，因此应该分别处理并生成不同的历史数据集，例如策略生成需要用到3D多类型数据 \
    # 而回测则只需要收盘价即可，数据频率也可能不同
    if history_data is None:
        # TODO：根据operation对象和context对象的参数生成不同的历史数据用于不同的用途：
        # 用于交易信号生成的历史数据
        hist_op = context.history.extract(shares, price_type='close',
                                          start=start, end=end,
                                          interval=freq)
        hist_loop = None  # 用于数据回测的历史数据
        hist_opti = None  # 用于策略优化的历史数据
        hist_reference = None
        # print('history data is None')
    else:
        # TODO: hist_data_req：这里的代码需要优化：正常工作中，历史数据不需要手工传入，应该可以根据需要策略的参数和context配置自动 \
        # TODO: 下载或者从数据库自动读取
        assert isinstance(history_data, HistoryPanel), \
            f'historical price should be HistoryPanel! got {type(history_data)}'
        hist_op = history_data
        hist_loop = history_data.to_dataframe(htype='close')
        hist_reference = history_data.to_dataframe(htype='close')
        # print('history data is not None')
    # ========
    # TODO: 紧迫任务：完成实时信号生成模式。根据输入的策略类型和参数自动读取并组装正确的历史数据
    # TODO: 利用历史数据生成交易信号，并且根据交易信号和当前持仓位置生成交易订单（输出交易订单的易读形式），并且将标准化格式的交易订单
    # TODO: 传递至实盘交易模块。
    if run_mode == 0:
        """进入实时信号生成模式：
        
            根据生成的执行器历史数据hist_op，应用operator对象中定义的投资策略生成当前的投资组合和各投资产品的头寸及仓位
            连接交易执行模块登陆交易平台，获取当前账号的交易平台上的实际持仓组合和持仓仓位
            将生成的投资组合和持有仓位与实际仓位比较，生成交易信号
            交易信号为一个tuple，包含以下组分信息：
             1，交易品种：str，需要交易的目标投资产品，可能为股票、基金、期货或其他，根据建立或设置的投资组合产品池确定
             2，交易位置：int，分别为多头头寸：1，或空头仓位： -1 （空头头寸只有在期货或期权交易时才会涉及到）
             3，交易方向：int，分别为开仓：1， 平仓：0 （股票和基金的交易只能开多头（买入）和平多头（卖出），基金可以开、平空头）
             4，交易类型：int，分为市价单：0，限价单：0
             5，交易价格：float，仅当交易类型为限价单时有效，市价单
             6，交易量：float，当交易方向为开仓（买入）时，交易量代表计划现金投入量，当交易方向为平仓（卖出）时，交易量代表卖出的产品份额
             
             上述交易信号被传入交易执行模块，连接券商服务器执行交易命令，执行成功后返回1，否则返回0
             若交易执行模块交易成功，返回实际成交的品种、位置、方向、价格及成交数量（交易量），另外还返回交易后的实际持仓数额，资金余额
             交易费用等信息
             
             以上信息被记录到log对象中，并最终存储在磁盘上
        """

    elif run_mode == 1:
        """进入回测模式：
        
            根据执行器历史数据hist_op，应用operator执行器对象中定义的投资策略生成一张投资产品头寸及仓位建议表。
            这张表的每一行内的数据代表在这个历史时点上，投资策略建议对每一个投资产品应该持有的仓位。每一个历史时点的数据都是根据这个历史时点的
            相对历史数据计算出来的。这张投资仓位建议表的历史区间受context上下文对象的"loop_period_start, loop_period_end, loop_period_freq"
            等参数确定。
            同时，这张投资仓位建议表是由operator执行器对象在hist_op策略生成历史数据上生成的。hist_op历史数据包含所有用于生成策略运行结果的信息
            包括足够的数据密度、足够的前置历史区间以及足够的历史数据类型（如不同价格种类、不同财报指标种类等）
            operator执行器对象接受输入的hist_op数据后，在数据集合上反复循环运行，从历史数据中逐一提取出一个个历史片段，根据这个片段生成一个投资组合
            建议，然后把所有生成的投资组合建议组合起来形成完整的投资组合建议表。
            
            投资组合建议表生成后，系统在整个投资组合建议区间上比较前后两个历史时点上的建议持仓份额，当发生建议持仓份额变动时，根据投资产品的类型
            生成投资交易信号，包括交易方向、交易产品和交易量。形成历史交易信号表。
            
            历史交易信号表生成后，系统在相应的历史区间中创建hist_loop回测历史数据表，回测历史数据表包含对回测操作来说必要的历史数据如股价等，然后
            在hist_loop的历史数据区间上对每一个投资交易信号进行模拟交易，并且逐个生成每个交易品种的实际成交量、成交价格、交易费用（通过Rate类估算）
            以及交易前后的持有资产数量和持有现金数量的变化，以及总资产的变化。形成一张交易结果清单。交易模拟过程中的现金投入过程通过CashPlan对象来
            模拟。
            
            因为交易结果清单是根据有交易信号的历史交易日上计算的，因此并不完整。根据完整的历史数据，系统可以将数据补充完整并得到整个历史区间的
            每日甚至更高频率的投资持仓及总资产变化表。完成这张表后，系统将在这张总资产变化表上执行完整的回测结果分析，分析的内容包括：
                1，total_investment                      总投资
                2，total_final_value                     投资期末总资产
                3，loop_length                           投资模拟区间长度
                4，total_earning                         总盈亏
                5，total_transaction_cost                总交易成本
                6，total_open                            总开仓次数
                7，total_close                           总平仓次数
                8，total_return_rate                     总收益率
                9，annual_return_rate                    总年化收益率
                10，reference_return                     基准产品总收益
                11，reference_return_rate                基准产品总收益率
                12，reference_annual_return_rate         基准产品年化收益率
                13，max_retreat                          投资期最大回测率
                14，Karma_rate                           卡玛比率
                15，Sharp_rate                           夏普率
                16，win_rage                             胜率
                
            上述所有评价结果和历史区间数据能够以可视化的方式输出到图表中。同时回测的结果数据和回测区间的每一次模拟交易记录也可以被记录到log对象中
            保存在磁盘上供未来调用
            
        """
        operator.prepare_data(hist_data=hist_op, cash_plan=context.cash_plan)
        st = time.clock()
        op_list = operator.create_signal(hist_data=hist_op)
        et = time.clock()
        run_time_prepare_data = (et - st) * 1000
        st = time.clock()
        looped_values = apply_loop(op_list,
                                   hist_loop.fillna(0),
                                   cash_plan=context.cash_plan,
                                   moq=0,
                                   visual=True,
                                   cost_rate=context.rate,
                                   price_visual=True)
        et = time.clock()
        run_time_loop_full = (et - st) * 1000
        # print('looped values result is: \n', looped_values)
        years, oper_count, total_invest, total_fee = _eval_operation(op_list=op_list,
                                                                     looped_value=looped_values,
                                                                     cash_plan=context.cash_plan)
        final_value = _eval_fv(looped_val=looped_values)
        ret = final_value / total_invest
        max_drawdown, low_date = _eval_max_drawdown(looped_values)
        volatility = _eval_volatility(looped_values, hist_loop)
        ref_rtn, ref_annual_rtn = _eval_benchmark(looped_values, hist_reference, reference_data)
        beta = _eval_beta(looped_values, hist_loop, hist_reference, reference_data)
        sharp = _eval_sharp(looped_values, hist_loop, total_invest, 0.035)
        alpha = _eval_alpha(looped_values, total_invest, hist_loop, hist_reference, reference_data)
        print(f'==================================== \n'
              f'           LOOPING RESULT\n'
              f'====================================')
        print(f'\ntime consumption for operate signal creation: {run_time_prepare_data:.3f} ms\n'
              f'time consumption for operation back looping: {run_time_loop_full:.3f} ms\n')
        print(f'investment starts on {looped_values.index[0]}\nends on {looped_values.index[-1]}\n'
              f'Total looped periods: {years} years.')
        print(f'operation summary:\n {oper_count}\nTotal operation fee:     ¥{total_fee:11,.2f}')
        print(f'total investment amount: ¥{total_invest:11,.2f}\n'
              f'final value:             ¥{final_value:11,.2f}')
        print(f'Total return: {ret * 100:.3f}% \nAverage Yearly return rate: {(ret ** (1 / years) - 1) * 100: .3f}%')
        print(f'Total reference return: {ref_rtn * 100:.3f}% \n'
              f'Average Yearly reference return rate: {ref_annual_rtn * 100:.3f}%')
        print(f'strategy performance indicators: \n'
              f'alpha:               {alpha:.3f}\n'
              f'Beta:                {beta:.3f}\n'
              f'Sharp rate:          {sharp:.3f}\n'
              f'250 day volatility:  {volatility:.3f}\n'
              f'Max drawdown:        {max_drawdown * 100:.3f}% on {low_date}')

    elif run_mode == 2:
        """进入策略优化模式：
        
            优化模式的目的是寻找能让策略的运行效果最佳的参数或参数组合。
            寻找能使策略的运行效果最佳的参数组合并不是一件容易的事，因为我们通常认为运行效果最佳的策略是能在"未来"实现最大收益的策略。但是，鉴于
            实际上要去预测未来是不可能的，因此我们能采取的优化方法几乎都是以历史数据——也就是过去的经验——为基础的，并且期望通过过去的历史经验
            达到某种程度上"预测未来"的效果。
            
            策略优化模式或策略优化器的工作方法就基于这个思想，如果某个或某组参数使得某个策略的在过去足够长或者足够有代表性的历史区间内表现良好，
            那么很有可能它也能在有限的未来不大会表现太差。因此策略优化模式的着眼点完全在于历史数据——所有的操作都是通过解读历史数据，或者策略在历史数据
            上的表现来评判一个策略的优劣的，至于如何找到对策略的未来表现有更大联系的历史数据或表现形式，则是策略设计者的责任。策略优化器仅仅
            确保找出的参数组合在过去有很好的表现，而对于未来无能为力。
            
            优化器的工作基础在于历史数据。它的工作方法从根本上来讲，是通过检验不同的参数在同一组历史区间上的表现来评判参数的优劣的。优化器的
            工作方法可以大体上分为以下两类：
            
                1，无监督方法类：这一类方法不需要事先知道"最优"或先验信息，从未知开始搜寻最佳参数。这类方法需要大量生成不同的参数组合，并且
                在同一个历史区间上反复回测，通过比较回测的结果而找到最优或较优的参数。这一类优化方法的假设是，如果这一组参数在过去取得了良好的
                投资结果，那么很可能在未来也不会太差。
                这一类方法包括：
                    1，Exhaustive_searching                  穷举法：
                    2，Montecarlo_searching                  蒙特卡洛法
                    3，Incremental_steped_searching          步进搜索法
                    4，Genetic_Algorithm                     遗传算法
                
                2，有监督方法类：这一类方法依赖于历史数据上的（有用的）先验信息：比如过去一个区间上的已知交易信号、或者价格变化信息。然后通过
                优化方法寻找历史数据和有用的先验信息之间的联系（目标联系）。这一类优化方法的假设是，如果这些通过历史数据直接获取先验信息的联系在未来仍然
                有效，那么我们就可能在未来同样根据这些联系，利用已知的数据推断出对我们有用的信息。
                这一类方法包括：
                    1，ANN_based_methods                     基于人工神经网络的有监督方法
                    2，SVM                                   支持向量机类方法
                    3，KNN                                   基于KNN的方法
                    
            为了实现上面的方法，优化器需要两组历史数据，分别对应两个不同的历史区间，一个是优化区间，另一个是回测区间。在优化的第一阶段，优化器
            在优化区间上生成交易信号，或建立目标联系，并且在优化区间上找到一个或若干个表现最优的参数组合或目标联系，接下来，在优化的第二阶段，
            优化器在回测区间上对寻找到的最优参数组合或目标联系进行测试，在回测区间生成对所有中选参数的“独立”表现评价。通常，可以选择优化区间较
            长且较早，而回测区间较晚而较短，这样可以模拟根据过去的信息建立的策略在未来的表现。
            
            优化器的优化过程首先开始于一个明确定义的参数"空间"。参数空间在系统中定义为一个Space对象。如果把策略的参数用向量表示，空间就是所有可能
            的参数组合形成的向量空间。对于无监督类方法来说，参数空间容纳的向量就是交易信号本身或参数本身。而对于有监督算法，参数空间是将历史数据
            映射到先验数据的一个特定映射函数的参数空间，例如，在ANN方法中，参数空间就是神经网络所有神经元连接权值的可能取值空间。优化器的工作本质
            就是在这个参数空间中寻找全局最优解或局部最优解。因此理论上所有的数值优化方法都可以用于优化器。
            
            优化器的另一个重要方面是目标函数。根据目标函数，我们可以对优化参数空间中的每一个点计算出一个目标函数值，并根据这个函数值的大小来评判
            参数的优劣。因此，目标函数的输出应该是一个实数。对于无监督方法，目标函数与参数策略的回测结果息息相关，最直接的目标函数就是投资终值，
            当初始投资额相同的时候，我们可以简单地认为终值越高，则参数的表现越好。但目标函数可不仅仅是终值一项，年化收益率或收益率、夏普率等等
            常见的评价指标都可以用来做目标函数，甚至目标函数可以用复合指标，如综合考虑收益率、交易成本、最大回撤等指标的一个复合指标，只要目标函数
            的输出是一个实数，就能被用作目标函数。而对于有监督方法，目标函数表征的是从历史数据到先验信息的映射能力，通常用实际输出与先验信息之间
            的差值的函数来表示。在机器学习和数值优化领域，有多种函数可选，例如MSE函数，CrossEntropy等等。
        """
        how = context.opti_method
        if how == 0:
            """ Exhausetive Search 穷举法
            
                穷举法是最简单和直接的参数优化方法，在已经定义好的参数空间中，按照一定的间隔均匀地从向量空间中取出一系列的点，逐个在优化空间
                中生成交易信号并进行回测，把所有的参数组合都测试完毕后，根据目标函数的值选择排名靠前的参数组合即可。
                
                穷举法能确保找到参数空间中的全剧最优参数，不过必须逐一测试所有可能的参数点，因此计算量相当大。同时，穷举法只适用于非连续的参数
                空间，对于连续空间，仍然可以使用穷举法，但无法真正"穷尽"所有的参数组合
                
                关于穷举法的具体参数和输出，参见self._search_exhaustive()函数的docstring
            """
            pars, perfs = _search_exhaustive(hist=hist_op, op=operator,
                                             output_count=context.output_count,
                                             keep_largest_perf=context.keep_largest_perf)
        elif how == 1:
            """ Montecarlo蒙特卡洛方法
            
                蒙特卡洛法与穷举法类似，也需要检查并测试参数空间中的大量参数组合。不过在蒙特卡洛法中，参数组合是从参数空间中随机选出的，而且在
                参数空间中均匀分布。与穷举法相比，蒙特卡洛方法更适合于连续参数空间。
                
                关于蒙特卡洛方法的参数和输出，参见self._search_montecarlo()函数的docstring
            """
            pars, perfs = _search_montecarlo(hist=hist_op, op=operator,
                                             output_count=context.output_count,
                                             keep_largest_perf=context.keep_largest_perf)
        elif how == 2:  #
            """ Incremental Stepped Search 递进步长法
            
                递进步长法本质上与穷举法是一样的。不过规避了穷举法的计算量过大的缺点，大大降低了计算量，同时在对最优结果的搜索能力上并未作出太大
                牺牲。递进步长法的基本思想是对参数空间进行多轮递进式的搜索，第一次搜索时使用一个相对较大的搜索步长，由于搜索的步长较大（通常为8或
                16，或者更大）因此第一次搜索的计算量只有标准穷举法的1/16^3或更少。第一次搜索完毕后，选出结果最优的参数点，通常为50个到1000个之
                间，在这些参数点的"附件"进行第二轮搜索，此时搜索的步长只有第一次的1/2或1/3。虽然搜索步长减小，但是搜索的空间更小，因此计算量也
                不大。第二轮搜索完成后，继续减小搜索步长，同样对上一轮搜索中找到的最佳参数附近搜索。这样循环直到完成整个空间的搜索。
                
                使用这种技术，在一个250*250X250的空间中，能够把搜索量从15,000,000降低到28,000左右,缩减到原来的1/500。如果目标函数在参数空间
                中大体上是连续的情况下，使用ISS方法可以以五百分之一的计算量得到近似穷举法的搜索效果。
                
                关于递进步长法的参数和输出，参见self._search_incremental()函数的docstring
            """
            pars, perfs = _search_incremental(hist=hist_op, op=operator,
                                              output_count=context.output_count,
                                              keep_largest_perf=context.keep_largest_perf)
        elif how == 3:
            """ GA method遗传算法
            
                遗传算法适用于"超大"参数空间的参数寻优。对于有二到三个参数的策略来说，使用蒙特卡洛或穷举法是可以承受的选择，如果参数数量增加到4到
                5个，递进步长法可以帮助降低计算量，然而如果参数有数百个，而且每一个都有无限取值范围的时候，任何一种基于穷举的方法都没有应用的
                意义了。如果目标函数在参数空间中是连续且可微的，可以使用基于梯度的方法，但如果目标函数不可微分，GA方法提供了一个在可以承受的时间
                内找到全局最优或局部最优的方法。
                
                GA方法受生物进化论的启发，通过模拟生物在自然选择下的基因进化过程，在复杂的超大参数空间中搜索全局最优或局部最优参数。GA的基本做法
                是模拟一个足够大的"生物"种群在自然环境中的演化，这些生物的"基因"是参数空间中的一个点，在演化过程中，种群中的每一个个体会发生
                变异、也会通过杂交来改变或保留自己的"基因"，并把变异或杂交后的基因传递到下一代。在每一代的种群中，优化器会计算每一个个体的目标函数
                并根据目标函数的大小确定每一个个体的生存几率和生殖几率。由于表现较差的基因生存和生殖几率较低，因此经过数万乃至数十万带的迭代后，
                种群中的优秀基因会保留并演化出更加优秀的基因，最终可能演化出全局最优或至少局部最优的基因。
                
                关于遗传算法的详细参数和输出，参见self._search_ga()函数的docstring
            """
            raise NotImplementedError
        elif how == 4:
            """ ANN 人工神经网络
            
            """
            raise NotImplementedError
        elif how == 5:
            """ SVM 支持向量机方法
            
            """
            raise NotImplementedError
        optimization_log = Log()
        optimization_log.write_record(pars, perfs)


def _search_exhaustive(hist, op, output_count, keep_largest_perf, step_size=1):
    """ 最优参数搜索算法1: 穷举法或间隔搜索法

        逐个遍历整个参数空间（仅当空间为离散空间时）的所有点并逐一测试，或者使用某个固定的
        “间隔”从空间中逐个取出所有的点（不管离散空间还是连续空间均适用）并逐一测试，
        寻找使得评价函数的值最大的一组或多组参数

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param output_count，int，输出数量，优化器寻找的最佳参数的数量
        :param keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
        :param step_size，int或list，搜索参数，搜索步长，在参数空间中提取参数的间隔，如果是int型，则在空间的每一个轴上
            取同样的步长，如果是list型，则取list中的数字分别作为每个轴的步长
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
    """

    pool = ResultPool(output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间

    # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
    i = 0
    it, total = space.extract(step_size)
    # 调试代码
    print('Result pool has been created, capacity of result pool: ', pool.capacity)
    print('Searching Space has been created: ')
    space.info()
    print('Number of points to be checked: ', total)
    print('Searching Starts...')

    for par in it:
        op.set_opt_par(par)  # 设置Operator子对象的当前择时Timing参数
        # 调试代码
        # print('Optimization, created par for op:', par)
        # 使用Operator.create()生成交易清单，并传入Looper.apply_loop()生成模拟交易记录
        looped_val = apply_loop(op_list=op.create_signal(hist),
                                history_list=hist, init_cash=100000,
                                visual=False, price_visual=False)
        # 使用Optimizer的eval()函数对模拟交易记录进行评价并得到评价结果
        # 交易结果评价的方法由method参数指定，评价函数的输出为一个实数
        perf = _eval(looped_val, method='fv')
        # 将当前参数以及评价结果成对压入参数池中，并去掉最差的结果
        # 至于去掉的是评价函数最大值还是最小值，由keep_largest_perf参数确定
        # keep_largest_perf为True则去掉perf最小的参数组合，否则去掉最大的组合
        pool.in_pool(par, perf)
        # 调试代码
        i += 1.
        if i % 10 == 0:
            print('current result:', np.round(i / total * 100, 3), '%', end='\r')

            pool.cut(keep_largest_perf)
            print('Searching finished, best results:', pool.perfs)
            print('best parameters:', pool.pars)
            return pool.pars, pool.perfs


def _search_montecarlo(hist, op, output_count, keep_largest_perf, point_count=50):
    """ 最优参数搜索算法2: 蒙特卡洛法

        从待搜索空间中随机抽取大量的均匀分布的参数点并逐个测试，寻找评价函数值最优的多个参数组合
        随机抽取的参数点的数量为point_count, 输出结果的数量为output_count

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param output_count，int，输出数量，优化器寻找的最佳参数的数量
        :param keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
        :param point_count，int或list，搜索参数，提取数量，如果是int型，则在空间的每一个轴上
            取同样多的随机值，如果是list型，则取list中的数字分别作为每个轴随机值提取数量目标
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
"""
    pool = ResultPool(output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间
    # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与穷举法一致
    i = 0
    it, total = space.extract(point_count, how='rand')
    # 调试代码
    print('Result pool has been created, capacity of result pool: ', pool.capacity)
    print('Searching Space has been created: ')
    space.info()
    print('Number of points to be checked:', total)
    print('Searching Starts...')

    for par in it:
        op.set_opt_par(par)  # 设置timing参数
        # 生成交易清单并进行模拟交易生成交易记录
        looped_val = apply_loop(op_list=op.create_signal(hist),
                                history_list=hist, init_cash=100000,
                                visual=False, price_visual=False)
        # 使用评价函数计算该组参数模拟交易的评价值
        perf = _eval(looped_val, method='fv')
        # 将参数和评价值传入pool对象并过滤掉最差的结果
        pool.in_pool(par, perf)
        # 调试代码
        i += 1.0
        print('current result:', np.round(i / total * 100, 3), '%', end='\r')
        pool.cut(keep_largest_perf)
        print('Searching finished, best results:', pool.perfs)
        print('best parameters:', pool.pars)
        return pool.pars, pool.perfs


def _search_incremental(hist, op, output_count, keep_largest_perf, init_step=16,
                        inc_step=2, min_step=1):
    """ 最优参数搜索算法3: 递进搜索法

        该搜索方法的基础还是间隔搜索法，首先通过较大的搜索步长确定可能出现最优参数的区域，然后逐步
        缩小步长并在可能出现最优参数的区域进行“精细搜索”，最终锁定可能的最优参数
        与确定步长的搜索方法和蒙特卡洛方法相比，这种方法能够极大地提升搜索速度，缩短搜索时间，但是
        可能无法找到全局最优参数。同时，这种方法需要参数的评价函数值大致连续

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param output_count，int，输出数量，优化器寻找的最佳参数的数量
        :param keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
        :param init_step，int，初始步长，默认值为16
        :param inc_step，float，递进系数，每次重新搜索时，新的步长缩小的倍数
        :param min_step，int，终止步长，当搜索步长最小达到min_step时停止搜索
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

"""
    pool = ResultPool(output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par
    spaces = list()  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
    spaces.append(Space(s_range, s_type))  # 将整个空间作为第一个子空间对象存储起来
    step_size = init_step  # 设定初始搜索步长

    while step_size >= min_step:  # 从初始搜索步长开始搜索，一回合后缩短步长，直到步长小于min_step参数
        i = 0
        while len(spaces) > 0:
            space = spaces.pop()
            # 逐个弹出子空间列表中的子空间，用当前步长在其中搜索最佳参数，所有子空间的最佳参数全部进入pool并筛选最佳参数集合
            # 调试代码
            it, total = space.extract(step_size, how='interval')
            for par in it:
                # 以下所有函数都是循环内函数，需要进行提速优化
                # 以下所有函数在几种优化算法中是相同的，因此可以考虑简化
                op.set_opt_par(par)  # 设置择时参数``
                # 声称交易清淡病进行模拟交易生成交易记录
                looped_val = apply_loop(op_list=op.create_signal(hist),
                                        history_list=hist,
                                        init_cash=100000,
                                        visual=False,
                                        price_visual=False)
                # 使用评价函数计算参数模拟交易的评价值
                perf = _eval(looped_val, method='fv')
                pool.in_pool(par, perf)
                i += 1.
                print(
                    'current result:', np.round(i / (total * output_count) * 100, 5), '%', end='\r')
                pool.cut(keep_largest_perf)
                print('Completed one round, creating new space set')
                # 完成一轮搜索后，检查pool中留存的所有点，并生成由所有点的邻域组成的子空间集合
                for item in pool.pars:
                    spaces.append(space.from_point(point=item, distance=step_size))
                # 刷新搜索步长
                step_size = step_size // inc_step
                print('new spaces created, start next round with new step size', step_size)
            print('Searching finished, best results:', pool.perfs)
            print('best parameters:', pool.pars)
            return pool.pars, pool.perfs


def _search_ga(hist, op, lpr, output_count, keep_largest_perf):
    """ 最优参数搜索算法4: 遗传算法
    遗传算法适用于在超大的参数空间内搜索全局最优或近似全局最优解，而它的计算量又处于可接受的范围内

    遗传算法借鉴了生物的遗传迭代过程，首先在参数空间中随机选取一定数量的参数点，将这批参数点称为
    “种群”。随后在这一种群的基础上进行迭代计算。在每一次迭代（称为一次繁殖）前，根据种群中每个个体
    的评价函数值，确定每个个体生存或死亡的几率，规律是若个体的评价函数值越接近最优值，则其生存的几率
    越大，繁殖后代的几率也越大，反之则越小。确定生死及繁殖的几率后，根据生死几率选择一定数量的个体
    让其死亡，而从剩下的（幸存）的个体中根据繁殖几率挑选几率最高的个体进行杂交并繁殖下一代个体，
    同时在繁殖的过程中引入随机的基因变异生成新的个体。最终使种群的数量恢复到初始值。这样就完成
    一次种群的迭代。重复上面过程数千乃至数万代直到种群中出现希望得到的最优或近似最优解为止

    input：
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param lpr，object，交易信号回测器对象
        :param output_count，int，输出数量，优化器寻找的最佳参数的数量
        :param keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

"""
    raise NotImplementedError


def _eval_benchmark(looped_value, reference_value, reference_data):
    """ 参考标准年化收益率。具体计算方式为 （(参考标准最终指数 / 参考标准初始指数) ** 1 / 回测交易年数 - 1）

    :param looped_value:
    :param reference_value:
    :return:
    """
    first_day = looped_value.index[0]
    last_day = looped_value.index[-1]
    total_year = (last_day - first_day).days / 365
    rtn_data = reference_value[reference_data]
    rtn = (rtn_data[last_day] / rtn_data[first_day])
    return rtn, rtn ** (1 / total_year) - 1.


def _eval_alpha(looped_val, total_invest, hist_list, reference_value, reference_data):
    """ 回测结果评价函数：alpha率

    阿尔法。具体计算方式为 (策略年化收益 - 无风险收益) - beta × (参考标准年化收益 - 无风险收益)，
    这里的无风险收益指的是中国固定利率国债收益率曲线上10年期国债的年化到期收益率。
    :param looped_val:
    :param total_invest:
    :param reference_value:
    :param reference_data:
    :return:
    """
    first_day = looped_val.index[0]
    last_day = looped_val.index[-1]
    total_year = (last_day - first_day).days / 365
    final_value = _eval_fv(looped_val)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    reference_return, reference_yearly_return = _eval_benchmark(looped_val, reference_value, reference_data)
    beta = _eval_beta(looped_val, hist_list, reference_value, reference_data)
    return (strategy_return - 0.035) - beta * (reference_yearly_return - 0.035)


def _eval_beta(looped_value, hist_list, reference_value, reference_data):
    """ 贝塔。具体计算方法为 策略每日收益与参考标准每日收益的协方差 / 参考标准每日收益的方差 。

    :param reference_value:
    :param looped_value:
    :return:
    """
    assert isinstance(reference_value, pd.DataFrame)
    first_day = looped_value.index[0]
    last_day = looped_value.index[-1]
    ret = looped_value['value'] / looped_value['value'].shift(1)
    ret_dev = ret.std()
    ref = reference_value[reference_data]
    ref_ret = ref / ref.shift(1)
    looped_value['ref'] = ref_ret
    looped_value['ret'] = ret
    return looped_value.ref.cov(looped_value.ret) / ret_dev


def _eval_sharp(looped_val, hist_list, total_invest, riskfree_interest_rate):
    """ 夏普比率。表示每承受一单位总风险，会产生多少的超额报酬。

    具体计算方法为 (策略年化收益率 - 回测起始交易日的无风险利率) / 策略收益波动率 。

    :param looped_val:
    :return:
    """
    first_day = looped_val.index[0]
    last_day = looped_val.index[-1]
    total_year = (last_day - first_day).days / 365
    final_value = _eval_fv(looped_val)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    volatility = _eval_volatility(looped_val, hist_list)
    return (strategy_return - riskfree_interest_rate) / volatility


def _eval_volatility(looped_value, hist_list):
    """ 策略收益波动率。用来测量资产的风险性。具体计算方法为 策略每日收益的年化标准差 。

    :param looped_value:
    :parma hist_list:
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        ret = np.log(looped_value['value'] / looped_value['value'].shift(1))
        volatility = ret.rolling(250).std() * np.sqrt(250)
        return volatility[-1]
    else:
        return -np.inf


def _eval_info_ratio(looped_value):
    """ 信息比率。衡量超额风险带来的超额收益。具体计算方法为 (策略每日收益 - 参考标准每日收益)的年化均值 / 年化标准差 。

    :param looped_value:
    :return:
    """
    raise NotImplementedError


def _eval_max_drawdown(looped_value):
    """ 最大回撤。描述策略可能出现的最糟糕的情况。具体计算方法为 max(1 - 策略当日价值 / 当日之前虚拟账户最高价值)

    :param looped_value:
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        max_val = 0
        max_drawdown = 0
        max_drawdown_date = 0
        for date, value in looped_value.value.iteritems():
            if value > max_val:
                max_val = value
            drawdown = 1 - value / max_val
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_date = date
        return max_drawdown, max_drawdown_date
    else:
        return -np.inf


def _eval_fv(looped_val):
    """评价函数 Future Value 终值评价

'投资模拟期最后一个交易日的资产总值

input:
:param looped_val，ndarray，回测器生成输出的交易模拟记录
return: =====
perf：float，应用该评价方法对回测模拟结果的评价分数

"""
    if not looped_val.empty:
        # 调试代码
        # print looped_val.head()
        perf = looped_val['value'][-1]
        return perf
    else:
        return -np.inf


def _eval_operation(op_list, looped_value, cash_plan):
    """ 评价函数，统计操作过程中的基本信息:

    对回测过程进行统计，输出以下内容：
    1，总交易次数：买入操作次数、卖出操作次数
    2，总投资额
    3，总交易费用
    4，回测时间长度

    :param looped_value:
    :param cash_plan:
    :return:
    """
    total_year = np.round((looped_value.index[-1] - looped_value.index[0]).days / 365., 1)
    sell_counts = []
    buy_counts = []
    for share, ser in op_list.iteritems():
        sell_count = 0
        buy_count = 0
        current_pos = -1
        for i, value in ser.iteritems():
            if np.sign(value) != current_pos:
                current_pos = np.sign(value)
                if current_pos == 1:
                    buy_count += 1
                else:
                    sell_count += 1
        sell_counts.append(sell_count)
        buy_counts.append(buy_count)
    op_counts = pd.DataFrame(sell_counts, index=op_list.columns, columns=['sell'])
    op_counts['buy'] = buy_counts
    op_counts['total'] = op_counts.buy + op_counts.sell
    total_op_fee = looped_value.fee.sum()
    total_investment = cash_plan.total

    return total_year, op_counts, total_investment, total_op_fee


# TODO：eval()函数没必要写那么多个，可以根据需要统一到一个评价函数中
def _eval(looped_val, method: str = None):
    """评价函数，对回测器生成的交易模拟记录进行评价，包含不同的评价方法。

    input:
    :param looped_val，ndarray，回测器生成输出的交易模拟记录
    :param method，int，交易记录评价方法
    return: =====
    调用不同评价函数的返回值
"""
    if method.upper() == 'FV':
        return _eval_fv(looped_val)
    elif method.upper() == 'ROI':
        return _eval_roi(looped_val)
    elif method.upper() == 'SHARP':
        return _eval_sharp(looped_val)
    elif method.upper() == 'ALPHA':
        return _eval_alpha(looped_val)


def _space_around_centre(space, centre, radius, ignore_enums=True):
    """在给定的参数空间中指定一个参数点，并且创建一个以该点为中心且包含于给定参数空间的子空间"""
    '如果参数空间中包含枚举类型维度，可以予以忽略或其他操作'
    return space.from_point(point=centre, distance=radius, ignore_enums=ignore_enums)


class ResultPool:
    """结果池类，用于保存限定数量的中间结果，当压入的结果数量超过最大值时，去掉perf最差的结果.

    最初的算法是在每次新元素入池的时候都进行排序并去掉最差结果，这样要求每次都在结果池深度范围内进行排序'
    第一步的改进是记录结果池中最差结果，新元素入池之前与最差结果比较，只有优于最差结果的才入池，避免了部分情况下的排序'
    新算法在结果入池的循环内函数中避免了耗时的排序算法，将排序和修剪不合格数据的工作放到单独的cut函数中进行，这样只进行一次排序'
    新算法将一百万次1000深度级别的排序简化为一次百万级别排序，实测能提速一半左右'
    即使在结果池很小，总数据量很大的情况下，循环排序的速度也慢于单次排序修剪
    """

    # result pool operation:
    def __init__(self, capacity):
        """result pool stores all intermediate or final result of searching, the points"""
        self.__capacity = capacity  # 池中最多可以放入的结果数量
        self.__pool = []  # 用于存放中间结果
        self.__perfs = []  # 用于存放每个中间结果的评价分数，老算法仍然使用列表对象

    @property
    def pars(self):
        return self.__pool  # 只读属性，所有池中参数

    @property
    def perfs(self):
        return self.__perfs  # 只读属性，所有池中参数的评价分

    @property
    def capacity(self):
        return self.__capacity

    def in_pool(self, item, perf):
        """将新的结果压入池中

        input:
            :param item，object，需要放入结果池的参数对象
            :param perf，float，放入结果池的参数评价分数
        return: =====
            无
        """
        self.__pool.append(item)  # 新元素入池
        self.__perfs.append(perf)  # 新元素评价分记录

    def cut(self, keep_largest=True):
        """将pool内的结果排序并剪切到capacity要求的大小

        直接对self对象进行操作，排序并删除不需要的结果
        input:
            :param keep_largest， bool，True保留评价分数最高的结果，False保留评价分数最低的结果
        return: =====
            无
        """
        poo = self.__pool  # 所有池中元素
        per = self.__perfs  # 所有池中元素的评价分
        cap = self.__capacity
        if keep_largest:
            arr = np.array(per).argsort()[-cap:]
        else:
            arr = np.array(per).argsort()[:cap]
        poo2 = []
        per2 = []
        for i in arr:
            poo2.append(poo[i])
            per2.append(per[i])
        self.__pool = poo2
        self.__perfs = per2


def _input_to_list(pars, dim, pader):
    """将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

    input:
        :param pars，需要转化为list对象的输出对象
        :param dim，需要生成的目标list的元素数量
        :param pader，当元素数量不足的时候用来补充的元素
    return: =====
        pars, list 转化好的元素清单
    """
    if (type(pars) == str) or (type(pars) == int):  # 处理字符串类型的输入
        # print 'type of types', type(pars)
        pars = [pars] * dim
    else:
        pars = list(pars)  # 正常处理，输入转化为列表类型
    par_dim = len(pars)
    # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
    if par_dim < dim: pars.extend([pader] * (dim - par_dim))
    return pars


class Space:
    """定义一个参数空间，一个参数空间包含一个或多个Axis对象，存储在axes列表中

    参数空间类用于生成并管理一个参数空间，从参数空间中根据一定的要求提取出一系列的参数点并组装成迭代器供优化器调用
    参数空间包含一个或多个轴，每个轴代表参数空间的一个维度，从每个轴上取出一个数值作为参数空间中某个点的坐标，而这个坐标
    就代表空间中的一个参数组合
    参数空间支持三种不同的轴，整数轴、浮点轴，这两种都是数值型的轴，还有另一种枚举轴，包含不同对象的枚举，同样可以作为参数
    空间的一个维度独立存在，与数值轴的操作方式相同
    数值轴的定义方式为上下界定义，枚举轴的定义方式为枚举定义，数值轴的取值范围为上下界之间的合法数值，而枚举轴的取值为枚举
    列表中的值
    """

    def __init__(self, pars, par_types: list = None):
        """参数空间对象初始化，根据输入的参数生成一个空间

        input:
            :param pars，int、float或list,需要建立参数空间的初始信息，通常为一个数值轴的上下界，如果给出了types，按照
                types中的类型字符串创建不同的轴，如果没有给出types，系统根据不同的输入类型动态生成的空间类型分别如下：
                    pars为float，自动生成上下界为(0, pars)的浮点型数值轴，
                    pars为int，自动生成上下界为(0, pars)的整形数值轴
                    pars为list，根据list的元素种类和数量生成不同类型轴：
                        list元素只有两个且元素类型为int或float：生成上下界为(pars[0], pars[1])的浮点型数值
                        轴或整形数值轴
                        list元素不是两个，或list元素类型不是int或float：生成枚举轴，轴的元素包含par中的元素
            :param par_types，list，默认为空，生成的空间每个轴的类型，如果给出types，应该包含每个轴的类型字符串：
                'discr': 生成整数型轴
                'conti': 生成浮点数值轴
                'enum': 生成枚举轴
        return: =====
            无
        """
        self._axes = []
        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        pars = list(pars)
        par_dim = len(pars)
        if par_types is None:
            par_types = []
        par_types = _input_to_list(par_types, par_dim, [None])

        # 调试代码：
        # print('par dim:', par_dim)
        # print('pars and par_types:', pars, par_types)
        # 逐一生成Axis对象并放入axes列表中
        for i in range(par_dim):
            # print('appending', i+1, '-th par', pars[i],'in type:', par_types[i])
            self._axes.append(Axis(pars[i], par_types[i]))

    @property
    def dim(self):  # 空间的维度
        return len(self._axes)

    @property
    def types(self):
        """List of types of axis of the space"""
        types = []
        if self.dim > 0:
            for i in range(self.dim):
                types.append(self._axes[i].axis_type)
        return types

    @property
    def boes(self):
        """List of bounds of axis of the space"""
        boes = []
        if self.dim > 0:
            for i in range(self.dim):
                boes.append(self._axes[i].axis_boe)
        return boes

    @property
    def shape(self):
        """输出空间的维度大小，输出形式为元组，每个元素代表对应维度的元素个数"""
        s = []
        for axis in self._axes:
            s.append(axis.count)
        return tuple(s)

    @property
    def size(self):
        """输出空间的尺度，输出每个维度的跨度之乘积"""
        s = []
        for axis in self._axes:
            s.append(axis.size)
        return np.product(s)

    def info(self):
        """打印空间的各项信息"""
        if self.dim > 0:
            print(type(self))
            print('dimension:', self.dim)
            print('types:', self.types)
            print('the bounds or enums of space', self.boes)
            print('shape of space:', self.shape)
            print('size of space:', self.size)
        else:
            print('Space is empty!')

    def extract(self, interval_or_qty: int = 1, how: str = 'interval'):
        """从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        input:
            :param interval_or_qty: int。从空间中每个轴上需要提取数据的步长或坐标数量
            :param how, str, 有两个合法参数：
                'interval',以间隔步长的方式提取坐标，这时候interval_or_qty代表步长
                'rand', 以随机方式提取坐标，这时候interval_or_qty代表提取数量
        return: tuple，包含两个数据
            iter，迭代器数据，打包好的所有需要被提取的点的集合
            total，int，迭代器输出的点的数量
        """
        interval_or_qty_list = _input_to_list(pars=interval_or_qty,
                                              dim=self.dim,
                                              pader=[1])
        axis_ranges = []
        i = 0
        total = 1
        for axis in self._axes:  # 分别从各个Axis中提取相应的坐标
            axis_ranges.append(axis.extract(interval_or_qty_list[i], how))
            total *= len(axis_ranges[i])
            i += 1
        if how == 'interval':
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how == 'rand':
            return itertools.zip_longest(*axis_ranges), interval_or_qty  # 使用迭代器工具将所有点组合打包为点集

    def from_point(self, point, distance, ignore_enums=True):
        """在已知空间中以一个点为中心点生成一个字空间

        input:
            :param point，object，已知参数空间中的一个参数点
            :param distance， int或float，需要生成的新的子空间的数轴半径
            :param ignore_enums，bool，True忽略enum型轴，生成的子空间包含枚举型轴的全部元素，False生成的子空间
                包含enum轴的部分元素
        return: =====

        """
        if ignore_enums: pass
        assert self.dim > 0, 'original space should not be empty!'
        pars = []
        for i in range(self.dim):
            if self.types[i] != 'enum':
                space_lbound = self.boes[i][0]
                space_ubound = self.boes[i][1]
                lbound = max((point[i] - distance), space_lbound)
                ubound = min((point[i] + distance), space_ubound)
                pars.append((lbound, ubound))
            else:
                pars.append(self.boes[i])
        return Space(pars, self.types)


class Axis:
    """数轴对象，空间对象的一个组成部分，代表空间对象的一个维度


    """

    def __init__(self, bounds_or_enum, typ=None):
        self._axis_type = None  # 数轴类型
        self._lbound = None  # 离散型或连续型数轴下界
        self._ubound = None  # 离散型或连续型数轴上界
        self._enum_val = None  # 当数轴类型为“枚举”型时，储存改数轴上所有可用值
        # 将输入的上下界或枚举转化为列表，当输入类型为一个元素时，生成一个空列表并添加该元素
        boe = list(bounds_or_enum)
        length = len(boe)  # 列表元素个数
        # 调试代码
        # print('in Axis: boe recieved, and its length:', boe, length, 'type of boe:', typ)
        if typ is None:
            # 当typ为空时，需要根据输入数据的类型猜测typ
            if length <= 2:  # list长度小于等于2，根据数据类型取上下界，int产生离散，float产生连续
                if type(boe[0]) == int:
                    typ = 'discr'
                elif type(boe[0]) == float:
                    typ = 'conti'
                else:  # 输入数据类型不是数字时，处理为枚举类型
                    typ = 'enum'
            else:  # list长度为其余值时，全部处理为enum数据
                typ = 'enum'
        elif typ != 'enum' and typ != 'discr' and typ != 'conti':
            typ = 'enum'  # 当发现typ为异常字符串时，修改typ为enum类型
        # 调试代码
        # print('in Axis, after infering typ, the typ is:', typ)
        # 开始根据typ的值生成具体的Axis
        if typ == 'enum':  # 创建一个枚举数轴
            self._new_enumerate_axis(boe)
        elif typ == 'discr':  # 创建一个离散型数轴
            if length == 1:
                self._new_discrete_axis(0, boe[0])
            else:
                self._new_discrete_axis(boe[0], boe[1])
        else:  # 创建一个连续型数轴
            if length == 1:
                self._new_continuous_axis(0, boe[0])
            else:
                self._new_continuous_axis(boe[0], boe[1])

    @property
    def count(self):
        """输出数轴中元素的个数，若数轴为连续型，输出为inf"""
        self_type = self._axis_type
        if self_type == 'conti':
            return np.inf
        elif self_type == 'discr':
            return self._ubound - self._lbound
        else:
            return len(self._enum_val)

    @property
    def size(self):
        """输出数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界"""
        self_type = self._axis_type
        if self_type == 'conti':
            return self._ubound - self._lbound
        else:
            return self.count

    @property
    def axis_type(self):
        """返回数轴的类型"""
        return self._axis_type

    @property
    def axis_boe(self):
        """返回数轴的上下界或枚举"""
        if self._axis_type == 'enum':
            return tuple(self._enum_val)
        else:
            return self._lbound, self._ubound

    def extract(self, interval_or_qty=1, how='interval'):
        """从数轴中抽取数据，并返回一个iterator迭代器对象

        input:
            :param interval_or_qty: int 需要从数轴中抽取的数据总数或抽取间隔，当how=='interval'时，代表抽取间隔，否则代表总数
            :param how: str 抽取方法，'interval' 或 'rand'， 默认'interval'
        return:
            一个迭代器对象，包含所有抽取的数值
        """
        if how == 'interval':
            if self.axis_type == 'enum':
                return self._extract_enum_interval(interval_or_qty)
            else:
                return self._extract_bounding_interval(interval_or_qty)
        else:
            if self.axis_type == 'enum':
                return self._extract_enum_random(interval_or_qty)
            else:
                return self._extract_bounding_random(interval_or_qty)

    def _set_bounds(self, lbound, ubound):
        """设置数轴的上下界, 只适用于离散型或连续型数轴

        input:
            :param lbound int/float 数轴下界
            :param ubound int/float 数轴上界
        return:
            None
        """
        self._lbound = lbound
        self._ubound = ubound
        self.__enum = None

    def _set_enum_val(self, enum):
        """设置数轴的枚举值，适用于枚举型数轴

        input:
            :param enum: 数轴枚举值
        :return:
            None
        """
        self._lbound = None
        self._ubound = None
        self._enum_val = np.array(enum, subok=True)

    def _new_discrete_axis(self, lbound, ubound):
        """ 创建一个新的离散型数轴

        input:
            :param lbound: 数轴下界
            :param ubound: 数轴上界
        :return:
            None
        """
        self._axis_type = 'discr'
        self._set_bounds(int(lbound), int(ubound))

    def _new_continuous_axis(self, lbound, ubound):
        """ 创建一个新的连续型数轴

        input:
            :param lbound: 数轴下界
            :param ubound: 数轴上界
        :return:
            None
        """
        self._axis_type = 'conti'
        self._set_bounds(float(lbound), float(ubound))

    def _new_enumerate_axis(self, enum):
        """ 创建一个新的枚举型数轴

        input:
            :param enum: 数轴的枚举值
        :return:
        """
        self._axis_type = 'enum'
        self._set_enum_val(enum)

    def _extract_bounding_interval(self, interval):
        """ 按照间隔方式从离散或连续型数轴中提取值

        input:
            :param interval: 提取间隔
        :return:
            np.array 从数轴中提取出的值对象
        """
        return np.arange(self._lbound, self._ubound, interval)

    def _extract_bounding_random(self, qty: int):
        """ 按照随机方式从离散或连续型数轴中提取值

        input:
            :param qty: 提取的数据总量
        :return:
            np.array 从数轴中提取出的值对象
        """
        if self._axis_type == 'discr':
            result = np.random.randint(self._lbound, self._ubound + 1, size=qty)
        else:
            result = self._lbound + np.random.random(size=qty) * (self._ubound - self._lbound)
        return result

    def _extract_enum_interval(self, interval):
        """ 按照间隔方式从枚举型数轴中提取值

        input:
            :param interval: 提取间隔
        :return:
            list 从数轴中提取出的值对象
        """
        count = self.count
        return self._enum_val[np.arange(0, count, interval)]

    def _extract_enum_random(self, qty: int):
        """ 按照随机方式从枚举型数轴中提取值

        input:
            :param qty: 提取间隔
        :return:
            list 从数轴中提取出的值对象
        """
        count = self.count
        return self._enum_val[np.random.choice(count, size=qty)]
