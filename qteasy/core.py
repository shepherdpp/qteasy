# coding=utf-8

import pandas as pd
import numpy as np
import datetime
import itertools
from qteasy.utilfuncs import *


class Log:
    def __init__(self):
        """

        """
        raise NotImplementedError


class Context:
    """QT Easy量化交易系统的上下文对象，保存所有相关环境变量及(伪)常量

    包含的常量：
    ========
        RUN_MODE_LIVE = 0
        RUN_MODE_BACKLOOP = 1
        RUN_MODE_OPTIMIZE = 2

    包含的变量：
    ========
        mode，运行模式
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
                 rate_impact: float = 0,
                 moq: int = 100,
                 init_cash: float = 10000,
                 visual: bool = False,
                 reference_visual: bool = False,
                 reference: list = list()):
        """初始化所有的环境变量和环境常量

        input:
            :param mode:
            :param rate_fee:
            :param rate_slipery:
            :param rate_impact:
            :param moq:
            :param init_cash:
            :param visual:
            :param reference_visual:
            :param reference:
        """

        self.mode = mode
        self.rate = Rate(rate_fee, rate_slipery, rate_impact)
        self.moq = moq  # 交易最小批量，设置为0表示可以买卖分数股
        self.init_cash = init_cash
        today = datetime.datetime.today().date()
        self.shares = []  # 优化参数所针对的投资产品
        self.opt_period_start = today - datetime.timedelta(3650)  # 优化历史区间开始日
        self.opt_period_end = today - datetime.timedelta(365)  # 优化历史区间结束日
        self.opt_period_freq = 'd'  # 优化历史区间采样频率
        self.loop_period_start = today - datetime.timedelta(3650)  # 测试区间开始日
        self.loop_period_end = today  # 测试区间结束日（测试区间的采样频率与优化区间相同）
        self.t_func_type = 1  # 'single'
        self.t_func = 'FV'  # 评价函数
        self.compound_method_expr = '( FV + Sharp )'  # 复合评价函数表达式，使用表达式解析模块解析并计算
        self.cycle_convolution_type = 'average'  # 当使用重叠区间优化参数时，各个区间评价函数值的组合方法
        self.opti_method = Context.OPTI_EXHAUSTIVE
        self.output_count = 50
        self.keep_largest_perf = True
        self.history_data_types = ['close']
        self.history_data = None
        self.visual = visual
        self.reference_visual = reference_visual

    def __str__(self):
        out_str = list()
        out_str.append('qteasy running information:')
        out_str.append('===========================')
        return ''.join(out_str)


class Rate:
    def __init__(self, fee: float = 0.003, slipery: float = 0, impact: float = 0):
        self.fee = fee
        self.slipery = slipery
        self.impact = impact

    def __str__(self):
        """设置Rate对象的打印形式"""
        return f'<rate: fee:{self.fee}, slipery:{self.slipery}, impact:{self.impact}>'

    def __repr__(self):
        """设置Rate对象"""
        return f'Rate({self.fee}, {self.slipery}, {self.impact})'

    def __call__(self, amount: np.ndarray):
        """直接调用对象，计算交易费率"""
        return self.fee + self.slipery + self.impact * amount

    def __getitem__(self, item: str) -> float:
        """通过字符串获取Rate对象的某个组份（费率、滑点或冲击率）"""
        assert isinstance(item, str), 'TypeError, item should be a string in [\'fee\', \'slipery\', \'impact\']'
        if item == 'fee':
            return self.fee
        elif item == 'slipery':
            return self.fee
        elif item == 'impact':
            return self.impact
        else:
            raise TypeError


# TODO: 使用Numba加速_loop_step()函数
def _loop_step(pre_cash, pre_amounts, op, prices, rate, moq):
    """ 对单次交易进行处理，采用向量化计算以提升效率

    input：=====
        param pre_cash, np.ndarray：本次交易开始前账户现金余额
        param pre_amounts, np.ndarray：list，交易开始前各个股票账户中的股份余额
        param op, np.ndarray：本次交易的个股交易清单
        param prices：np.ndarray，本次交易发生时各个股票的价格
        param rate：object Rate() 买入成本——待改进，应根据三个成本费率动态估算
        param moq：float: 投资产品最小交易单位

    return：=====元组，包含四个元素
        cash：交易后账户现金余额
        amounts：交易后每个个股账户中的股份余额
        fee：本次交易总费用
        value：本次交易后资产总额（按照交易后现金及股份余额以及交易时的价格计算）
    """
    # 计算交易前现金及股票余额在当前价格下的资产总额
    pre_value = pre_cash + (pre_amounts * prices).sum()
    # 计算按照交易清单出售资产后的资产余额以及获得的现金
    '''在这里出售的amount被使用np.rint()函数转化为int型，这里应该增加判断，如果MOQ不要求出售
    的投资产品份额为整数，可以省去rint处理'''
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


def _get_complete_hist(values, h_list, with_price=False):
    """完成历史交易回测后，填充完整的历史资产总价值清单

    输入：=====
        参数 values：完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
        参数 history_list：完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
        参数 with_price：Bool，True时在返回的清单中包含历史价格，否则仅返回资产总价值
    输出：=====
        values，pandas.Series 或 pandas.DataFrame：重新填充的完整历史交易日资产总价值清单
    """
    # 获取价格清单中的投资产品列表
    shares = h_list.columns
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    values = values.reindex(h_list.index, method='ffill').fillna(0)
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象
    values = (h_list * values[shares]).sum(axis=1) + values['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        values = pd.DataFrame(values.values, index=h_list.index, columns=['values'])
        values[shares] = h_list[shares]
    return values


def apply_loop(op_list, history_list, visual=False, price_visual=False,
               init_cash=100000, rate=None, moq=100):
    """使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
        现金额及费用，输出的结果可选

    input：=====
        :type init_cash: float: 初始资金额
        :type price_visual: Bool: 选择是否在图表输出时同时输出相关资产价格变化，visual为False时无效
        :type history_list: object pd.DataFrame: 完整历史价格清单，数据的频率由freq参数决定
        :type visual: Bool: 可选参数，默认False，仅在有交易行为的时间点上计算持仓、现金及费用，
                            为True时将数据填充到整个历史区间，并用图表输出
        :type op_list: object pd.DataFrame: 标准格式交易清单，描述一段时间内的交易详情，每次交易一行数据
        :type rate: float Rate: 交易成本率对象，包含交易费、滑点及冲击成本
        :type moq: float：每次交易的最小份额

    output：=====
        Value_history：包含交易结果及资产总额的历史清单

    """
    assert not op_list.empty, 'InputError: The Operation list should not be Empty'
    assert rate is not None, 'TyepError: rate should not be None type'
    # 将交易清单和与之对应的价格清单转化为ndarray，确保内存存储方式为Fortune，
    # 以实现高速逐行循环批量操作
    # 根据最新的研究实验，在python3.6的环境下，nditer的速度显著地慢于普通的for-loop
    # 因此改回for-loop执行，知道找到更好的向量化执行方法
    op = op_list.values
    price = history_list.fillna(0).loc[op_list.index].values
    op_count = op.shape[0]  # 获取行数
    # 初始化计算结果列表
    cash = init_cash  # 持有现金总额，初始化为初始现金总额
    amounts = [0] * len(history_list.columns)  # 投资组合中各个资产的持有数量，初始值为全0向量
    cashes = []  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
    fees = []  # 交易费用，记录每个操作时点产生的交易费用
    values = []  # 资产总价值，记录每个操作时点的资产和现金价值总和
    amounts_matrix = []
    # 只有当交易的资产数量大于1时，才需要向量化逐行循环，否则使用默认的ndarray循环
    for i in range(op_count):
        # it = np.nditer([op, price], flags = ['external_loop'], order = 'C')
        if len(history_list.columns) > 1:
            # ndarray的内存存储方式和external loop的循环顺序不一致时，会产生逐行循环的效果，实现向量化计算

            cash, amounts, fee, value = _loop_step(pre_cash=cash,
                                                   pre_amounts=amounts,
                                                   op=op[i, :],
                                                   prices=price[i, :],
                                                   rate=rate, moq=moq)
        else:
            # it = np.nditer([op, price])
            # 将每一行交易信号代码和每一行价格使用迭代器送入_loop_step()函数计算结果
            cash, amounts, fee, value = _loop_step(pre_cash=cash,
                                                   pre_amounts=amounts,
                                                   op=op[i], prices=price[i],
                                                   rate=rate,
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
        complete_value = _get_complete_hist(values=value_history,
                                            h_list=history_list,
                                            with_price=price_visual)
        # 输出相关资产价格
        if price_visual:  # 当Price_Visual参数为True时同时显示所有的成分股票的历史价格
            shares = history_list.columns
            share_prices = list()
            complete_value.plot(grid=True, figsize=(15, 7), legend=True,
                                secondary_y=shares)
        else:  # 否则，仅显示总资产的历史变化情况
            complete_value.plot(grid=True, figsize=(15, 7), legend=True)
    return value_history


def run(operator, context, mode: int = None, history_data: pd.DataFrame = None, *args, **kwargs):
    """开始运行，qteasy模块的主要入口函数

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
            输出回测日志
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

        param operator: Operator()，策略执行器对象
        param context: Context()，策略执行环境的上下文对象
        param mode: int, default to None，qteasy运行模式，如果给出则override context中的mode参数
        param history_data: pd.DataFrame, default to None, 参与执行所需的历史数据，如果给出则overidecontext 中的hist参数
        other params
    return：=====
        type: Log()，运行日志记录，txt 或 pd.DataFrame
    """

    shares = context.shares
    if mode is None:
        exe_mode = context.mode
    else:
        exe_mode = mode
    # hist data can be overwritten by passing history_data: pd.DataFrame
    if history_data is None:
        hist = context.history.extract(shares, price_type='close',
                                       start=start, end=end,
                                       interval=freq)
    else:
        assert type(history_data) is pd.DataFrame, 'historical price DataFrame shall be passed as parameter!'
        hist = history_data

    # ========
    if exe_mode == 0:
        """进入实时信号生成模式："""
        raise NotImplementedError

    elif exe_mode == 1:
        """进入回测模式："""
        op_list = operator.create(hist_extract=hist)
        looped_values = apply_loop(op_list, hist.fillna(0),
                                   init_cash=context.init_cash,
                                   moq=0, visual=True, rate=context.rate,
                                   price_visual=True)
        ret = looped_values.value[-1] / looped_values.value[0]
        years = (looped_values.index[-1] - looped_values.index[0]).days / 365.
        print('\nTotal investment years:', np.round(years, 1), np.round(ret * 100 - 100, 3), '%, final value:',
              np.round(ret * context.init_cash, 2))
        print('Average Yearly return rate: ', np.round((ret ** (1 / years) - 1) * 100, 3), '%')

    elif exe_mode == 2:
        """进入优化模式："""
        how = context.opti_method
        if how == 0:
            """穷举法"""
            pars, perfs = _search_exhaustive(hist=hist, op=operator,
                                             output_count = context.output_count,
                                             keep_largest_perf=context. keep_largest_perf,
                                             *args, **kwargs)
        elif how == 1:
            """Montecarlo蒙特卡洛方法"""
            pars, perfs = _search_montecarlo(hist=hist, op=op,
                                             output_count=context.output_count,
                                             keep_largest_perf=context.keep_largest_perf,
                                             *args, **kwargs)
        elif how == 2:  #
            """递进步长法"""
            pars, perfs = _search_incremental(hist=hist, op=op,
                                              output_count=context.output_count,
                                              keep_largest_perf=context.keep_largest_perf,
                                              *args, **kwargs)
        elif how == 3:
            """遗传算法"""
            raise NotImplementedError


def _search_exhaustive(hist, op, output_count, keep_largest_perf, step_size=1):
    """ 最优参数搜索算法1: 穷举法或间隔搜索法

        逐个遍历整个参数空间（仅当空间为离散空间时）的所有点并逐一测试，或者使用某个固定的
        “间隔”从空间中逐个取出所有的点（不管离散空间还是连续空间均适用）并逐一测试，
        寻找使得评价函数的值最大的一组或多组参数

    输入：
        参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        参数 op，object，交易信号生成器对象
        参数 lpr，object，交易信号回测器对象
        参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
        参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
        参数 step_size，int或list，搜索参数，搜索步长，在参数空间中提取参数的间隔，如果是int型，则在空间的每一个轴上
            取同样的步长，如果是list型，则取list中的数字分别作为每个轴的步长
    输出：=====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
    """

    pool = ResultPool(output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par()
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
        op._set_opt_par(par)  # 设置Operator子对象的当前择时Timing参数
        # 调试代码
        # print('Optimization, created par for op:', par)
        # 使用Operator.create()生成交易清单，并传入Looper.apply_loop()生成模拟交易记录
        looped_val = apply_loop(op_list=op.create(hist),
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

输入：
    参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
    参数 op，object，交易信号生成器对象
    参数 lpr，object，交易信号回测器对象
    参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
    参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
    参数 point_count，int或list，搜索参数，提取数量，如果是int型，则在空间的每一个轴上
        取同样多的随机值，如果是list型，则取list中的数字分别作为每个轴随机值提取数量目标
输出：=====tuple对象，包含两个变量
    pool.pars 作为结果输出的参数组
    pool.perfs 输出的参数组的评价分数
"""
    pool = ResultPool(output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par()
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
        op._set_opt_par(par)  # 设置timing参数
        # 生成交易清单并进行模拟交易生成交易记录
        looped_val = apply_loop(op_list=op.create(hist),
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

输入：
    参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
    参数 op，object，交易信号生成器对象
    参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
    参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
    参数 init_step，int，初始步长，默认值为16
    参数 inc_step，float，递进系数，每次重新搜索时，新的步长缩小的倍数
    参数 min_step，int，终止步长，当搜索步长最小达到min_step时停止搜索
输出：=====tuple对象，包含两个变量
    pool.pars 作为结果输出的参数组
    pool.perfs 输出的参数组的评价分数

"""
    pool = ResultPool(output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par()
    spaces = list()  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
    spaces.append(Space(s_range, s_type))  # 将整个空间作为第一个子空间对象存储起来
    step_size = init_step  # 设定初始搜索步长
    # 调试代码
    print('Result pool has been created, capacity of result pool: ', pool.capacity)
    print('Searching Space has been created: ', spaces)
    print('Searching Starts...')

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
                op._set_opt_par(par)  # 设置择时参数
                # 声称交易清淡病进行模拟交易生成交易记录
                looped_val = apply_loop(op_list=op.create(hist),
                                        history_list=hist, init_cash=100000,
                                        visual=False, price_visual=False)
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

输入：
参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
参数 op，object，交易信号生成器对象
参数 lpr，object，交易信号回测器对象
参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
输出：=====tuple对象，包含两个变量
pool.pars 作为结果输出的参数组
pool.perfs 输出的参数组的评价分数

"""
    raise NotImplementedError


def _eval_alpha(looped_val):
    raise NotImplementedError


def _eval_sharp(looped_val):
    raise NotImplementedError


def _eval_roi(looped_val):
    """评价函数 RoI 收益率'

'投资模拟期间资产投资年化收益率

输入：
参数 looped_val，ndarray，回测器生成输出的交易模拟记录
输出：=====
perf：float，应用该评价方法对回测模拟结果的评价分数

"""
    return perf


def _eval_FV(looped_val):
    """评价函数 Future Value 终值评价

'投资模拟期最后一个交易日的资产总值

输入：
参数 looped_val，ndarray，回测器生成输出的交易模拟记录
输出：=====
perf：float，应用该评价方法对回测模拟结果的评价分数

"""
    if not looped_val.empty:
        # 调试代码
        # print looped_val.head()
        perf = looped_val['value'][-1]
        return perf
    else:
        return -np.inf


def _eval(looped_val, method):
    """评价函数，对回测器生成的交易模拟记录进行评价，包含不同的评价方法。

输入：
参数 looped_val，ndarray，回测器生成输出的交易模拟记录
参数 method，int，交易记录评价方法
输出：=====
调用不同评价函数的返回值
"""
    if method.upper() == 'FV':
        return _eval_FV(looped_val)
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

'最初的算法是在每次新元素入池的时候都进行排序并去掉最差结果，这样要求每次都在结果池深度范围内进行排序'
'第一步的改进是记录结果池中最差结果，新元素入池之前与最差结果比较，只有优于最差结果的才入池，避免了部分情况下的排序'
'新算法在结果入池的循环内函数中避免了耗时的排序算法，将排序和修剪不合格数据的工作放到单独的cut函数中进行，这样只进行一次排序'
'新算法将一百万次1000深度级别的排序简化为一次百万级别排序，实测能提速一半左右'
'即使在结果池很小，总数据量很大的情况下，循环排序的速度也慢于单次排序修剪"""

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

输入：
    参数 item，object，需要放入结果池的参数对象
    参数 perf，float，放入结果池的参数评价分数
输出：=====
    无
"""
        self.__pool.append(item)  # 新元素入池
        self.__perfs.append(perf)  # 新元素评价分记录

    def cut(self, keep_largest=True):
        """将pool内的结果排序并剪切到capacity要求的大小

直接对self对象进行操作，排序并删除不需要的结果

输入：
    参数 keep_largest， bool，True保留评价分数最高的结果，False保留评价分数最低的结果
输出：=====
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

    def __init__(self, pars, types=[]):
        """参数空间对象初始化，根据输入的参数生成一个空间

        输入：
            参数 pars，int、float或list,需要建立参数空间的初始信息，通常为一个数值轴的上下界，如果给出了types，按照
                types中的类型字符串创建不同的轴，如果没有给出types，系统根据不同的输入类型动态生成的空间类型分别如下：
                    pars为float，自动生成上下界为(0, pars)的浮点型数值轴，
                    pars为int，自动生成上下界为(0, pars)的整形数值轴
                    pars为list，根据list的元素种类和数量生成不同类型轴：
                        list元素只有两个且元素类型为int或float：生成上下界为(pars[0], pars[1])的浮点型数值
                        轴或整形数值轴
                        list元素不是两个，或list元素类型不是int或float：生成枚举轴，轴的元素包含par中的元素
            参数 types，list，默认为空，生成的空间每个轴的类型，如果给出types，应该包含每个轴的类型字符串：
                'discr': 生成整数型轴
                'conti': 生成浮点数值轴
                'enum': 生成枚举轴
        输出：=====
            无
        """
        self.__axes = []
        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        pars = list(pars)
        par_dim = len(pars)
        types = self.__input_to_list(types, par_dim, [None])
        # 调试代码：
        # print('par dim:', par_dim)
        # print('pars and types:', pars, types)
        # 逐一生成Axis对象并放入axes列表中
        for i in range(par_dim):
            # print('appending', i+1, '-th par', pars[i],'in type:', types[i])
            self.__axes.append(Axis(pars[i], types[i]))

    @property
    def dim(self):  # 空间的维度
        return len(self.__axes)

    @property
    def types(self):  # List of types of axis of the space
        types = []
        if self.dim > 0:
            for i in range(self.dim):
                types.append(self.__axes[i].axis_type)
        return types

    @property
    def boes(self):  # List of bounds of axis of the space
        boes = []
        if self.dim > 0:
            for i in range(self.dim):
                boes.append(self.__axes[i].axis_boe)
        return boes

    @property
    def shape(self):
        # 输出空间的维度大小，输出形式为元组，每个元素代表对应维度的元素个数
        s = []
        for axis in self.__axes:
            s.append(axis.count)
        return tuple(s)

    @property
    def size(self):
        """输出空间的尺度，输出每个维度的跨度之乘积"""
        s = []
        for axis in self.__axes:
            s.append(axis.size)
        return np.product(s)

    # Methods:
    def __input_to_list(self, pars, dim, padder):
        """将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

        输入：
            参数 pars，需要转化为list对象的输出对象
            参数 dim，需要生成的目标list的元素数量
            参数 padder，当元素数量不足的时候用来补充的元素
        输出：=====
            pars, list 转化好的元素清单
        """
        if (type(pars) == str) or (type(pars) == int):  # 处理字符串类型的输入
            # print 'type of types', type(pars)
            pars = [pars] * dim
        else:
            pars = list(pars)  # 正常处理，输入转化为列表类型
        par_dim = len(pars)
        # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
        if par_dim < dim: pars.extend(padder * (dim - par_dim))
        return pars

    def info(self):
        """打印空间的各项信息"""
        if self.dim > 0:
            print('Space is not empty!')
            print('dimension:', self.dim)
            print('types:', self.types)
            print('the bounds or enums of space', self.boes)
            print('shape of space:', self.shape)
            print('size of space:', self.size)
        else:
            print('Space is empty!')

    def extract(self, interval_or_qty=1, how='interval'):
        """从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        输入
            参数 interval_or_qty，int。从空间中每个轴上需要提取数据的步长或坐标数量
            参数 how, str, 有两个合法参数：
                'interval',以间隔步长的方式提取坐标，这时候interval_or_qty代表步长
                'rand', 以随机方式提取坐标，这时候interval_or_qty代表提取数量
        输出，tuple，包含两个数据
            iter，迭代器数据，打包好的所有需要被提取的点的集合
            total，int，迭代器输出的点的数量
        """
        interval_or_qty = self.__input_to_list(pars=interval_or_qty,
                                               dim=self.dim,
                                               padder=[1])
        axis_ranges = []
        i = 0
        total = 1
        for axis in self.__axes:  # 分别从各个Axis中提取相应的坐标
            axis_ranges.append(axis.extract(interval_or_qty[i], how))
            total *= len(axis_ranges[i])
            i += 1
        if how == 'interval':
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how == 'rand':
            return itertools.zip_longest(*axis_ranges), interval_or_qty  # 使用迭代器工具将所有点组合打包为点集

    def from_point(self, point, distance, ignore_enums=True):
        """在已知空间中以一个点为中心点生成一个字空间

        输入：
            参数 point，object，已知参数空间中的一个参数点
            参数 distance， int或float，需要生成的新的子空间的数轴半径
            参数 ignore_enums，bool，True忽略enum型轴，生成的子空间包含枚举型轴的全部元素，False生成的子空间
                包含enum轴的部分元素
        输出：=====

        """
        if ignore_enums == True: pass
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

    def expand(self, bounds_or_enum, typ=None):
        # expand one more dimension of the space
        pass

    def squeez(self):
        # reduce one dimension of the space
        pass


class Axis:
    """数轴对象，空间对象的一个组成部分，代表空间对象的一个维度"""

    def __init__(self, bounds_or_enum, typ=None):
        import numpy as np
        self.__type = None  # 数轴类型
        self.__lbound = None  # 空间在数轴上的下界
        self.__ubound = None  # 空间在数轴上的上届
        self.__enum_val = None  # 当数轴类型为“枚举”型时，储存改数轴上所有可用值
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
            return self.__new_enumerate_axis(boe)
        elif typ == 'discr':  # 创建一个离散型数轴
            if length == 1:
                self.__new_discrete_axis(0, boe[0])
            else:
                self.__new_discrete_axis(boe[0], boe[1])
        else:  # 创建一个连续型数轴
            if length == 1:
                self.__new_continuous_axis(0, boe[0])
            else:
                self.__new_continuous_axis(boe[0], boe[1])

    @property
    def count(self):  # 输出数轴中元素的个数，若数轴为连续型，输出为inf
        self_type = self.__type
        if self_type == 'conti':
            return np.inf
        elif self_type == 'discr':
            return self.__ubound - self.__lbound
        else:
            return len(self.__enum_val)

    @property
    def size(self):  # 输出数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界
        self_type = self.__type
        if self_type == 'conti':
            return self.__ubound - self.__lbound
        else:
            return self.count

    @property
    def axis_type(self):
        return self.__type

    @property
    def axis_boe(self):
        if self.__type == 'enum':
            return tuple(self.__enum_val)
        else:
            return self.__lbound, self.__ubound

    def extract(self, interval_or_qty=1, how='interval'):
        if how == 'interval':
            if self.axis_type == 'enum':
                return self.__extract_enum_interval(interval_or_qty)
            else:
                return self.__extract_bounding_interval(interval_or_qty)
        else:
            if self.axis_type == 'enum':
                return self.__extract_enum_random(interval_or_qty)
            else:
                return self.__extract_bounding_random(interval_or_qty)

    def __set_bounds(self, lbound, ubound):
        self.__lbound = lbound
        self.__ubound = ubound
        self.__enum = None

    def __set_enum_val(self, enum):
        self.__lbound = None
        self.__ubound = None
        self.__enum_val = np.array(enum, subok=True)

    def __new_discrete_axis(self, lbound, ubound):
        self.__type = 'discr'
        self.__set_bounds(int(lbound), int(ubound))

    def __new_continuous_axis(self, lbound, ubound):
        self.__type = 'conti'
        self.__set_bounds(float(lbound), float(ubound))

    def __new_enumerate_axis(self, enum):
        self.__type = 'enum'
        self.__set_enum_val(enum)

    def __extract_bounding_interval(self, interval):
        return np.arange(self.__lbound, self.__ubound, interval)

    def __extract_bounding_random(self, qty):
        if self.__type == 'discr':
            result = np.random.randint(self.__lbound, self.__ubound + 1, size=qty)
        else:
            result = self.__lbound + np.random.random(size=qty) * (self.__ubound - self.__lbound)
        return result

    def __extract_enum_interval(self, interval):
        count = self.count
        return self.__enum_val[np.arange(0, count, interval)]

    def __extract_enum_random(self, qty):
        count = self.count
        return self.__enum_val[np.random.choice(count, size=qty)]
