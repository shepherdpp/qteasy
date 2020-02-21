# coding=utf-8

import pandas as pd
import numpy as np
import numba
import datetime
from abc import abstractmethod, ABCMeta
import itertools
from qteasy.history import History


# TODO: 简化类的定义，删除不必要的类，将类的方法改成函数
# TODO: 将文件内的类或函数分组，分别放到不同的文件中去，如Loop、Optimizer等

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

    def __init__(self, mode=RUN_MODE_BACKLOOP, rate_fee=0.003, rate_slipery=0, rate_impact=0, moq=100):
        """初始化所有的环境变量和环境常量"""

        # 环境变量
        # ============
        self.mode = mode
        self.rate = Rate(rate_fee, rate_slipery, rate_impact)
        self.moq = moq  # 交易最小批量，设置为0表示可以买卖分数股
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
        self.opti_method = 'standard'

        pass

    def __str__(self):
        out_str = []
        out_str.append('qteasy running information:')
        out_str.append('===========================')
        return ''.join(out_str)


class Rate:

    def __init__(self, fee:float=0.003, slipery:float=0, impact:float=0):
        self.fee = fee
        self.slipery = slipery
        self.impact = impact

    def __str__(self):
        """设置Rate对象的打印形式"""
        return f'<rate: fee:{self.fee}, slipery:{self.slipery}, impact:{self.impact}>'

    def __repr__(self):
        """设置Rate对象"""
        return f'Rate({self.fee}, {self.slipery}, {self.impact})'

    def __call__(self, amount:np.ndarray):
        """直接调用对象，计算交易费率"""
        return self.fee + self.slipery + self.impact * amount

    def __getitem__(self, item:str)->float:
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
        raise NotImplementedError


#TODO: 使用Numba加速_loop_step()函数
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
        :type rate_slipery: float
        :type rate_fee: float
        :type moq: float
        :type rate_impact: float

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
                                                   rate = rate, moq=moq)
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
            share_prices = []
            complete_value.plot(grid=True, figsize=(15, 7), legend=True,
                                secondary_y=shares)
        else:  # 否则，仅显示总资产的历史变化情况
            complete_value.plot(grid=True, figsize=(15, 7), legend=True)
    return value_history


def run(operator, context, how=0, output_count=50,
        keep_largest_perf=True, hist=None, *args, **kwargs):
    """开始优化，Optimizer类的主要动作调用入口函数

       根据所需要优化的参数空间类型不同，所选择的优化算法不同，调用不同的优化函数完成优化并返回输出结果

    输入：

        参数 how:int，参数评价方法
        参数 output_count: int，优化器输出的结果数量
        参数 keep_largest_perf: bool，True表示寻找评价得分最高的参数，False表示寻找评价得分最低的参数
        其他参数
    输出：=====
        暂无，需完善
    """
    # 确认所有的基本参数设置正确，否则打印错误信息，中止优化

    # 分析op对象，确定最大化的优化参数空间

    # 如果明确指定了参数空间：
    # 将给定的参数空间与最大化优化参数空间比较，对不需要优化的参数进行空间纬度压缩
    # 否则：
    # 使用最大化优化参数空间进行优化

    # 判断所选择的优化算法是否适用于参数空间，如否，打印错误信息并中止优化

    # 根据基本参数设置基本变量，如历史数据、op对象、lpr对象等
    shares = context.shares
    if hist is None:
        start = context.opt_period_start
        end = context.opt_period_end
        freq = context.opt_period_freq
        hist = context.history.extract(shares, price_type='close',
                                    start=start, end=end,
                                    interval=freq)
    else:  # TODO, operator start shall be improved!!
        assert type(hist) is pd.DataFrame, 'historical price DataFrame shall be passed as parameter!'
        start = hist.index[0]
        end = hist.index[-1]
        freq = 'd'

    # 以下是调试用代码
    print('shares involved in optimization:', shares)
    print('Historical period of optimization starts:', start)
    print('Historical period of optimization endd:', end)
    print('Historical data frequency:', freq)
    print('Starts optimization')

    # 根据所选择的优化算法进行优化并输出结果
    # 优化方法可以做成一个简单工厂模式，此段代码应该重构并简化
    if how == 0:  # 穷举法

        pars, perfs = _search_exhaustive(hist=hist, op=operator,
                                               output_count=output_count, keep_largest_perf=keep_largest_perf,
                                               *args, **kwargs)
    elif how == 1:  # Montecarlo蒙特卡洛方法

        pars, perfs = _search_MonteCarlo(hist=hist, op=op,
                                               output_count=output_count, keep_largest_perf=keep_largest_perf,
                                               *args, **kwargs)
    elif how == 2:  # 递进步长法

        pars, perfs = _search_Incremental(hist=hist, op=op,
                                                output_count=output_count, keep_largest_perf=keep_largest_perf,
                                                *args, **kwargs)
    elif how == 3:  # 遗传算法
        pass
    pass


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
        op.set_opt_par(par)  # 设置Operator子对象的当前择时Timing参数
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


def _search_MonteCarlo(hist, op, output_count, keep_largest_perf, point_count=50):
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
        op.set_opt_par(par)  # 设置timing参数
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


def _search_Incremental(hist, op, output_count, keep_largest_perf, init_step=16,
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
    spaces = []  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
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
                op.set_opt_par(par)  # 设置择时参数
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
    pool = ResultPool()
    return pool.pars, pool.perfs


def _eval_alpha(looped_val):
    return perf


def _eval_sharp(looped_val):
    return perf


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

# TODO: 以下函数可以放到一个模块中，称为utilfuncs==================
@numba.jit(nopython=True, target='cpu', parallel=True)
def ema(arr, span: int = None, alpha: float = None):
    """基于numpy的高速指数移动平均值计算.

    input：
        :param arr: 1-D ndarray, 输入数据，一维矩阵
        :param span: int, optional, 1 < span, 跨度
        :param alpha: float, optional, 0 < alpha < 1, 数据衰减系数
    output：=====
        :return: 1-D ndarray; 输入数据的指数平滑移动平均值
    """
    if alpha is None:
        alpha = 2 / (span + 1.0)
    alpha_rev = 1 - alpha
    n = arr.shape[0]
    pows = alpha_rev ** (np.arange(n + 1))
    scale_arr = 1 / pows[:-1]
    offset = arr[0] * pows[1:]
    pw0 = alpha * alpha_rev ** (n - 1)
    mult = arr * pw0 * scale_arr
    cumsums = mult.cumsum()
    return offset + cumsums * scale_arr[::-1]


@numba.jit(nopython=True)
def ma(arr, window: int):
    """Fast moving average calculation based on NumPy
       基于numpy的高速移动平均值计算

    input：
        :param window: type: int, 1 < window, 时间滑动窗口
        :param arr: type: object np.ndarray: 输入数据，一维矩阵
    return：
        :return: ndarray, 完成计算的移动平均序列
    """
    arr_ = arr.cumsum()
    arr_r = np.roll(arr_, window)
    arr_r[:window - 1] = np.nan
    arr_r[window - 1] = 0
    return (arr_ - arr_r) / window

# TODO: utilfuncs 结束

#TODO： 以下类放入Strategy和Operator模块中
class Strategy:
    """量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的择时类调用"""
    __mataclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'strategy type'
    _stg_name = 'strategy name'
    _stg_text = 'intro text of strategy'
    _par_count = 0
    _par_types = []
    _par_bounds_or_enums = []

    @property
    def stg_type(self):
        return self._stg_type

    @property
    def stg_name(self):
        return self._stg_name

    @property
    def stg_text(self):
        return self._stg_text

    @property
    def par_count(self):
        return self._par_count

    @property
    def par_types(self):
        return self._par_types

    @property
    def par_boes(self):
        return self._par_bounds_or_enums

    @property
    def opt_tag(self):
        return self._opt_tag

    @property
    def pars(self):
        return self._pars

    # 以下是所有Strategy对象的共有方法
    def __init__(self, pars=None, opt_tag=0):
        # 对象属性：
        self._pars = pars
        self._opt_tag = opt_tag

    def info(self):
        # 打印所有相关信息和主要属性
        print('Type of Strategy:', self.stg_type)
        print('Information of the strategy:\n', self.stg_name, self.stg_text)
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_boes)
        if self._pars is not None:
            print('Parameter Loaded：', type(self._pars), self._pars)
        else:
            print('Parameter NOT loaded!')
        pass

    def set_pars(self, pars):
        self._pars = pars
        return pars

    def set_opt_tag(self, opt_tag):
        self._opt_tag = opt_tag
        return opt_tag

    def set_par_boes(self, par_boes):
        self._par_bounds_or_enums = par_boes
        return par_boes

    @abstractmethod
    def generate(self, hist_price):
        """策略类的基本抽象方法，接受输入参数并输出操作清单"""
        pass


class Timing(Strategy):
    """择时策略的抽象基类，所有择时策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的择时类调用"""
    __mataclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'timing'

    ###################
    # 以下是本类型strategy对象的公共方法和抽象方法

    @abstractmethod
    def _generate_one(self, hist_price, params):
        """抽象方法，在具体类中需要重写，是整个类的择时信号基本生成方法，针对单个个股的价格序列生成多空状态信号"""
        pass

    def generate(self, hist_price):
        """基于_generate_one方法生成整个股票价格序列集合的多空状态矩阵.

        本方法基于numpy的ndarray计算
        输入：   hist_extract：DataFrame，历史价格数据，需要被转化为ndarray
        输出：=====
        """
        assert isinstance(hist_price, np.ndarray), 'Type Error: input should be Ndarray'
        pars = self._pars

        # assert pars.keys() = hist_extract.columns
        if type(pars) is dict:
            # 调用_generate_one方法计算单个个股的多空状态，并组合起来
            # print('input Pars is dict type, different parameters shall be mapped within data')
            par_list = list(pars.values())
            # print('values of pars are listed:', par_list)
            res = np.array(list(map(self._generate_one, hist_price.T, par_list))).T
        else:
            # 当参数不是字典状态时，直接使用pars作为参数
            res = np.apply_along_axis(self._generate_one, 0, hist_price, pars)

        # 将完成的数据组合成DataFrame
        # print('generate result of np timing generate', res)
        return res


class TimingSimple(Timing):
    """简单择时策略，返回整个历史周期上的恒定多头状态"""
    __stg_name = 'SIMPLE TIMING STRATEGY'
    __stg_text = 'Simple Timing strategy, return constant long position on the whole history'

    def _generate_one(self, hist_price, params):
        return hist_price.clip(1, 1)


class TimingCrossline(Timing):
    """crossline择时策略类，利用长短均线的交叉确定多空状态

        crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型

    """
    # 重写策略参数相关信息
    _par_count = 4
    _par_types = ['discr', 'discr', 'conti', 'enum']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250), ('buy', 'sell')]
    _stg_name = 'CROSSLINE STRATEGY'
    _stg_text = 'Moving average crossline strategy, determin long/short position according to the cross point of long and short term moving average prices'

    def _generate_one(self, hist_price, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 计算均线前排除所有的无效值，无效值前后价格处理为连续价格，返回时使用pd.Series重新填充日期序列恢复
        # 去掉的无效值
        # print 'Generating Crossline Long short Mask with parameters', params
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]  # 仅针对非nan值计算，忽略股票停牌时期
        # 计算长短均线之间的距离
        diff = ma(h_, l) - ma(h_, s)
        # TODO: 可以改成np.digitize()来完成，效率更高 -- 测试结果表明np.digitize速度甚至稍慢于两个where
        cat[drop] = np.where(diff < -m, 1, np.where(diff >= m, -1, 0))
        # TODO: 处理hesitate参数 &&&未完成代码&&&
        if hesitate == 'buy':
            pass
        elif hesitate == 'sell':
            pass
        else:
            pass
        # 重新恢复nan值可以使用pd.Series也可以使用pd.reindex，可以测试哪一个速度更快，选择速度更快的一个
        return cat  # 返回时填充日期序列恢复无效值


class TimingMACD(Timing):
    """MACD择时策略类，继承自Timing类，重写_generate方法'

    运用MACD均线策略，在hist_price Series对象上生成交易信号
    注意！！！
    由于MACD使用指数移动均线，由于此种均线的计算特性，在历史数据集的前max(sRange, lRange, mRange)
    个工作日上生成的数据不可用
    例如，max(sRange, lRange, mRange) = max(72,120,133) = 133个工作日内产生的买卖点不正确"""
    _par_count = 3
    _par_types = ['discr', 'discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250)]
    _stg_name = 'MACD STRATEGY'
    _stg_text = 'MACD strategy, determin long/short position according to differences of exponential weighted moving average prices'

    def _generate_one(self, hist_price, params):
        """生成单只个股的择时多空信号.

        输入:
            idx: 指定的参考指数历史数据
            sRange, 短均线参数，短均线的指数移动平均计算窗口宽度，单位为日
            lRange, 长均线参数，长均线的指数移动平均计算窗口宽度，单位为日
            dRange, DIFF的指数移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """

        s, l, m = params
        # print 'Generating MACD Long short Mask with parameters', params
        # h_ = hist_price.dropna() # 仅针对非nan值计算，忽略股票停牌时期
        cut = max(s, l) + m
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]

        # 计算指数的指数移动平均价格
        DIFF = ema(h_, s) - ema(h_, l)
        DEA = ema(DIFF, m)
        MACD = 2 * (DIFF - DEA)

        # 生成MACD多空判断：
        # 1， MACD柱状线为正，多头状态，为负空头状态：由于MACD = DIFF - DEA
        cat[drop] = np.where(MACD > 0, 1, 0)
        cat[0:cut] = np.nan
        return cat


class TimingDMA(Timing):
    """DMA择时策略，继承自Timing类，重写_generate方法"""
    _par_count = 3
    _par_types = ['discr', 'discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250)]
    _stg_name = 'quick-DMA STRATEGY'
    _stg_text = 'numpy based DMA strategy, determin long/short position according to differences of moving average prices'

    def _generate_one(self, hist_price, params):
        # 使用基于numpy的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick DMA Long short Mask with parameters', params
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]
        # 计算指数的移动平均价格
        DMA = ma(h_, s) - ma(h_, l)
        AMA = DMA.copy()
        AMA[~np.isnan(DMA)] = ma(DMA[~np.isnan(DMA)], d)
        # print('qDMA generated DMA and AMA signal:', DMA.size, DMA, '\n', AMA.size, AMA)
        # 生成DMA多空判断：
        # 1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        # 2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        # 3， DMA与股价发生背离时的交叉信号，可信度较高
        cat[drop] = np.where(DMA > AMA, 1, 0)
        # print('qDMA generate category data with as type', cat.size, cat)
        return cat


class TimingTRIX(Timing):
    """TRIX择时策略，继承自Timing类，重写__generate方法"""
    # 运用TRIX均线策略，在idx历史序列上生成交易信号
    # 注意！！！
    # 由于TRIX使用指数移动均线，由于此种均线的计算特性，在历史数据集的前sRange + mRange个工作日上生成的数据不可用
    # 例如，sRange + mRange = 157时，前157个工作日内产生的买卖点不正确，应忽略
    _par_count = 2
    _par_types = ['discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250)]
    _stg_name = 'TRIX STRATEGY'
    _stg_text = 'TRIX strategy, determin long/short position according to triple exponential weighted moving average prices'

    def _generate_one(self, hist_price, params):
        """# 参数:
        # idx: 指定的参考指数历史数据
        # sRange, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        # dRange, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """
        s, m = params
        cut = s + m
        # print 'Generating TRIX Long short Mask with parameters', params
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]

        # 计算指数的指数移动平均价格
        TR = ema(ema(ema(h_, s), s), s)
        TRIX = (TR - np.roll(TR, 1)) / np.roll(TR, 1) * 100
        MATRIX = ma(TRIX, m)

        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = -1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 1
        cat[drop] = np.where(TRIX > MATRIX, 1, 0)
        cat[0: cut] = np.nan
        return cat  # 返回时填充日期序列恢复nan值


class Selecting(Strategy):
    """选股策略类的抽象基类，所有选股策略类都继承该类"""
    __metaclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'selecting'

    #######################
    # Selecting 类的自有方法和抽象方法

    @abstractmethod
    def _select(self, shares, date, pct):
        # Selecting 类的选股抽象方法，在不同的具体选股类中应用不同的选股方法，实现不同的选股策略
        # 返回值：代表一个周期内股票选择权重的ndarray，1Darray
        pass

    def __to_trade_day(self, date):
        # 如果给定日期是交易日，则返回该日期，否则返回该日期的后一个交易日
        # 有可能传入的date参数带有时间部分，无法与交易日清单中的纯日期比较，因此需要转化为纯日期
        # 使用astype将带有时间的datetime64格式转化为纯日期的datetime64
        if self.__trade_cal.loc[date.astype('<M8[D]')] == 1:
            return date
        else:
            while self.__trade_cal.loc[date.astype('<M8[D]')] != 1:
                date = date + np.timedelta64(1, 'D')
            return date

    def __to_prev_trade_day(self, date):
        # 韩惠给定日期的前一个交易日
        # 使用astype将带有时间的datetime64格式转化为纯日期的datetime64
        date = date - np.timedelta64(1, 'D')
        while self.__trade_cal.loc[date.astype('<M8[D]')] != 1:
            date = date - np.timedelta64(1, 'D')
        return date

    def _seg_periods(self, dates, freq):
        # 对输入的价格序列数据进行分段，Selection类会对每个分段应用不同的股票组合
        # 对输入的价格序列日期进行分析，生成每个历史分段的起止日期所在行号，并返回行号和分段长度（数据行数）
        # 输入：
        # dates ndarray，日期序列，
        # freq：str 分段频率，取值为‘Q'：季度， ’Y'，年度； ‘M'，月度
        # 输出：=====
        # seg_pos: 每一个历史分段的开始日期;
        # seg_lens：每一个历史分段中含有的历史数据数量，
        # en(seg_lens): 分段的数量
        # 生成历史区间内的时间序列，序列间隔为选股间隔，每个时间点代表一个选股区间的开始时间
        bnds = pd.date_range(start=dates[0], end=dates[-1], freq=freq).values
        # 写入第一个选股区间分隔位——0
        seg_pos = np.zeros(shape=(len(bnds) + 2), dtype='int')
        seg_pos[1:-1] = np.searchsorted(dates, bnds)
        # 最后一个分隔位等于历史区间的总长度
        seg_pos[-1] = len(dates) - 1
        # print('Results check, selecting - segment creation, segments:', seg_pos)
        # 计算每个分段的长度
        seg_lens = (seg_pos - np.roll(seg_pos, 1))[1:]
        return seg_pos, seg_lens, len(seg_pos) - 1

    def generate(self, hist_price, dates, shares):
        """
        生成历史价格序列的选股组合信号：将历史数据分成若干连续片段，在每一个片段中应用某种规则建立投资组合
        建立的投资组合形成选股组合蒙版，每行向量对应所有股票在当前时间点在整个投资组合中所占的比例
        输入：
        hist_price：历史数据, DataFrame
        输出：=====sel_mask：选股蒙版，是一个与输入历史数据尺寸相同的ndarray，dtype为浮点数，取值范围在0～1之间
         矩阵中的取值代表股票在投资组合中所占的比例，0表示投资组合中没有该股票，1表示该股票占比100%
        获取参数

        :param hist_price: type: np.ndarray, 历史数据
        :param dates:
        :param shares:
        :return:
        """

        freq = self._pars[0]
        poq = self._pars[1]
        # 获取完整的历史日期序列，并按照选股频率生成分段标记位，完整历史日期序列从参数获得，股票列表也从参数获得
        # dates = hist_price.index.values
        # print('SPEED TEST Selection module, Time of segmenting history')
        # %time self._seg_periods(dates, freq)
        assert isinstance(hist_price, np.ndarray), 'Type Error: input historical data should be ndarray'
        seg_pos, seg_lens, seg_count = self._seg_periods(dates, freq)
        # shares = hist_price.columns
        # 一个空的list对象用于存储生成的选股蒙版
        sel_mask = np.zeros(shape=(len(dates), len(shares)), order='C')
        seg_start = 0

        for sp, sl in zip(seg_pos, seg_lens):  # 针对每一个选股分段区间内生成股票在投资组合中所占的比例
            # share_sel向量代表当前区间内的投资组合比例
            share_sel = self._select(shares, dates[sp], poq)
            seg_end = seg_start + sl
            # 填充相同的投资组合到当前区间内的所有交易时间点
            sel_mask[seg_start:seg_end + 1, :] = share_sel
            seg_start = seg_end
        # 将所有分段组合成完整的ndarray
        # print('SPEED TEST selection module, time of concatenating segments')
        return sel_mask


class SelectingTrend(Selecting):
    """趋势选股策略，继承自选股策略类"""
    _stg_name = 'TREND SELECTING'
    _stg_text = 'Selecting share according to detected trends'

    def _select(self, shares, date, pct):
        # 所有股票全部被选中，权值（投资比例）平均分配
        return [1. / len(shares)] * len(shares)

    pass


class SelectingSimple(Selecting):
    """基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配"""
    _stg_name = 'SIMPLE SELECTING'
    _stg_text = 'Selecting all share and distribute weights evenly'

    def _select(self, shares, date, pct):
        # 所有股票全部被选中，投资比例平均分配
        return [1. / len(shares)] * len(shares)


class SelectingRandom(Selecting):
    """基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配"""
    _stg_name = 'RANDOM SELECTING'
    _stg_text = 'Selecting share Randomly and distribute weights evenly'

    def _select(self, shares, date, par):
        if par < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size=len(shares), p=[par, 1 - par])
        else:  # par >= 1 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(len(shares), size=(int(par)), replace=False)
            chosen = np.zeros(len(shares))
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum()  # 投资比例平均分配


class SelectingRanking(Selecting):
    """
    普遍适用的选股策略：根据事先定义的排序表（Ranking table）来选择股票，根据不同的参数可以自定义多种不同的选股方式
    相关选股参数保存为对象属性，在Further_initialization过程中初始化, 包括：
        self.__ranking_table: 排序表，策略核心。在一张表中列出所有股票在不同历史时期的评分值，根据评分值的排序确定投资组合中的股票
        self.__largest_win: 布尔变量，为True时优先选择分值最高的股票，否则优先选择分值最低的股票
        self.__distribution: str变量，指定如何确定中选股票在投资组合中的比例：
            'even': 均匀分配，所有中选股票比例相同
            'linear': 线性分配，中选股票在组合中的占比呈等差数列，排名最高者比最低者比例高约200%
            'proportion': 比例分配，中选股票在组合中的占比与其分值成正比
        self.__drop_threshold: 弃置阈值，当分值低于（或高于）该阈值时将股票从组合中剔除'''
    """
    _stg_name = 'RANKING SELECTING'
    _stg_text = 'Selecting shares according to the so called ranking table, distribute weights in multiple ways'
    _par_count = 3  # 比普通selecting多一个ranking_table参数，opt类型为enum（自然）
    _par_types = ['enum', 'conti', 'enum']
    _par_bounds_or_enums = [('M', 'Q', 'S', 'Y'), (0, 1), ()]  # 四种分组单元分别为 'month', 'quarter', 'semi', 'year'

    # TODO: 因为Strategy主类代码重构，ranking table的代码结构也应该相应修改，待修改
    # 重写参数设置方法，把增加的策略参数包含在内
    def set_param(self, freq=None, pct_or_qty=None, ranking_table=None, largest_win=True, distribution='even',
                  drop_threshold=None):
        if freq is None:
            self.__freq = 'Q'
        else:
            self.__freq = freq
        if pct_or_qty is None:
            self.__pct_or_qty = 0.5
        else:
            self.__pct_or_qty = pct_or_qty
        self.__ranking_table = ranking_table
        self.__largest_win = largest_win
        self.__distribution = distribution
        self.__drop_threshold = drop_threshold
        pass

    # 重写信息打印方法，增加新增的策略参数
    def info(self):
        # 打印所有相关信息和主要属性
        print('Here\'s information of the Selecting strategy:', self.StgName, self.StgText, sep='\n')
        print('key parameters: frequency and selection percent or quantity', self.__freq,
              self.__pct_or_qty,
              sep='\n')
        if not self.__ranking_table is None:
            print('Other key parameters: \n', 'ranking table, largest win, distribution, drop threshold \n',
                  type(self.__ranking_table), self.__largest_win, self.__distribution, self.__drop_threshold,
                  sep=',')
        else:
            print('Other key parameters: \n', 'ranking table, largest win, distribution, drop threshold \n',
                  'Ranking Table None', self.__largest_win, self.__distribution, self.__drop_threshold,
                  sep=',')

    def _select(self, shares, date, par):
        """# 根据事先定义的排序表根据不同的方法选择一定数量的股票
    # 输入：
        # shares：列表，包含了所有备选投资产品的代码
        # date：选股日期，选股操作发生的日期
        # par：选股参数，选股百分比或选股数量
    # 输出：=====
        # chosen：浮点型向量，元素数量与shares中的相同，每个元素代表对应的投资产品在投资组合中占的比例"""
        share_count = len(shares)
        if par < 1:
            # par 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            par = int(len(shares) * par)
        else:  # par 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            par = int(par)
        if not self.__ranking_table is None:  # 排序表不能为空，否则无法进行
            # 排序表的列名为每一列数据的可用日期，也就是说该列数据只在该日期以后可用，获取可用日期
            r_table_dates = self.__ranking_table.columns
            # 根据选股日期选择最为接近的数据可用日期，用于确定使用哪一列数据执行选股操作
            i = r_table_dates.searchsorted(date)
            indices = self.__ranking_table[r_table_dates[i]]  # 定位到i列数据
            # 排序表的行索引为所有投资产品的代码，提取出shares列表中股票的分值，并压缩维度到1维
            indices = indices.loc[shares].values.squeeze()
            nan_count = np.isnan(indices).astype('int').sum()  # 清点数据，获取nan值的数量
            if self.__largest_win:
                # 选择分数最高的部分个股，由于np排序时会把NaN值与最大值排到一起，因此需要去掉所有NaN值
                pos = max(share_count - par - nan_count, 0)
            else:  # 选择分数最低的部分个股
                pos = par
            # 对数据进行排序，并把排位靠前者的序号存储在arg_found中
            if self.__distribution == 'even':
                # 仅当投资比例为均匀分配时，才可以使用速度更快的argpartition方法进行粗略排序
                arg_found = indices.argpartition(pos)[pos:]
            else:  # 如果采用其他投资比例分配方式时，必须使用较慢的全排序
                arg_found = indices.argsort()[pos:]
            # nan值数据的序号存储在arg_nan中
            arg_nan = np.where(np.isnan(indices))[0]
            # 使用集合操作从arg_found中剔除arg_nan，使用assume_unique参数可以提高效率
            args = np.setdiff1d(arg_found, arg_nan, assume_unique=True)
            # 构造输出向量，初始值为全0
            chosen = np.zeros_like(indices)
            # 根据投资组合比例分配方式，确定被选中产品的占比
            # Linear：根据分值排序线性分配，分值最高者占比约为分值最低者占比的三倍，其余居中者的比例按序呈等差数列
            if self.__distribution == 'linear':
                dist = np.arange(1, 3, 2. / len(args))  # 生成一个线性序列，最大值为最小值的约三倍
                chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
            # proportion：比例分配，占比与分值成正比，分值最低者获得一个基础比例，其余股票的比例与其分值成正比
            elif self.__distribution == 'proportion':
                dist = indices[args]
                d = dist.max() - dist.min()
                if self.__largest_win:
                    dist = dist - dist.min() + d / 10.
                else:
                    dist = dist.max() - dist + d / 10.
                chosen[args] = dist / dist.sum()
            # even：均匀分配，所有中选股票在组合中占比相同
            else:  # self.__distribution == 'even'
                chosen[args] = 1. / len(args)
            return chosen
        else:
            # 排序表不存在，返回包含所有股票平均分配比例的投资组合
            return [1. / len(shares)] * len(shares)
        pass

    def ranking_table(self, r_table=None):
        # 给ranking_table属性赋值，或者打印当前ranking_table的信息
        if r_table is None:  # 打印当前ranking_table的信息
            if self.__ranking_table is None:
                print('ranking table does not exist!')
                print('ranking table must be created before ranking based selection')
            else:
                print('ranking table information', self.__ranking_table.info())
        else:  # 将传入的数据赋值给对象的ranking_table属性
            self.__ranking_table = r_table


class Ricon(Strategy):
    """风险控制抽象类，所有风险控制策略均继承该类"""
    '''该策略仅仅生成卖出信号，无买入信号，因此作为止损点控制策略，仅与其他策略配合使用'''
    __metaclass__ = ABCMeta
    _stg_type = 'RiCon'

    @abstractmethod
    def generate(self, hist_price):
        pass


class RiconNone(Ricon):
    """无风险控制策略，不对任何风险进行控制"""
    _stg_name = 'NONE'
    _stg_text = 'Do not take any risk control activity'

    def generate(self, hist_price):
        return np.zeros_like(hist_price)


class RiconUrgent(Ricon):
    """urgent风控类，继承自Ricon类，重写_generate_ricon方法"""
    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号
    _par_count = 2
    _par_types = ['discr', 'conti']
    _par_bounds_or_enums = [(1, 40), (-0.5, 0.5)]
    _stg_name = 'URGENT'
    _stg_text = 'Generate selling signal when N-day drop rate reaches target'

    def generate(self, hist_price):
        """
        # 根据N日内下跌百分比确定的卖出信号，让N日内下跌百分比达到pct时产生卖出信号

        input =====
            :type hist_price: tuple like (N, pct): type N: int, Type pct: float
                输入参数对，当股价在N天内下跌百分比达到pct时，产生卖出信号
        return ====
            :rtype: object np.ndarray: 包含紧急卖出信号的ndarray
        """
        assert self._pars is not None, 'Parameter of Risk Control-Urgent should be a pair of numbers like (N, ' \
                                       'pct)\nN as days, pct as percent drop '
        assert isinstance(hist_price, np.ndarray), 'Type Error: input historical data should be ndarray'
        day, drop = self._pars

        diff = (hist_price - np.roll(hist_price, day)) / hist_price
        return np.where(diff < drop, -1, 0)


def _mask_to_signal(lst):
    """将持仓蒙板转化为交易信号.

    转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
    则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
    生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
        signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
            现金总额不足，则按比例调降买入比率，直到用尽现金。
        signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
        signal = 0时，表示不进行任何操作

    输入：
        参数 lst，ndarray，持仓蒙板
    输出：=====
        op，ndarray，交易信号矩阵
    """

    # 比较本期交易时间点和上期之间的持仓比率差额，差额大于0者可以直接作为补仓买入信号，如上期为0.35，
    # 本期0.7，买入信号为0.35，即使用总资金的35%买入该股，加仓到70%
    op = (lst - np.roll(lst, 1))
    # 差额小于0者需要计算差额与上期持仓数之比，作为卖出信号的强度，如上期为0.7，本期为0.35，差额为-0.35，则卖出信号强度
    # 为 (0.7 - 0.35) / 0.35 = 0.5即卖出50%的持仓数额，从70%仓位减仓到35%
    op = np.where(op < 0, (op / np.roll(lst, 1)), op)
    # 补齐因为计算差额导致的第一行数据为NaN值的问题
    op[0] = lst[0]
    return op


def _legalize(lst):
    """交易信号合法化，整理生成的交易信号，使交易信号符合规则.

    根据历史数据产生的交易信号不一定完全符合实际的交易规则，在必要时需要对交易信号进行
    修改，以确保最终的交易信号符合交易规则，这里的交易规则仅包含与交易时间相关的规则如T+1规则等，与交易
    成本或交易量相关的规则如费率、MOQ等都在回测模块中考虑"""

    # 最基本的操作规则是不允许出现大于1或者小于-1的交易信号
    return lst.clip(-1, 1)


def _timing_blend_change(ser: np.ndarray):
    """
    this method is based on Numpy thus is faster than the other two

    :type ser: object np.ndarray
    """
    if ser[0] > 0:
        state = 1
    else:
        state = 0
    res = np.zeros_like(ser)
    prev = ser[0]
    for u, v in np.nditer([res, ser], op_flags=['readwrite']):
        if v < prev:
            state = 0
        elif v > prev:
            state = 1
        u[...] = state
        prev = v
    return res


def _blend(n1, n2, op):
    """混合操作符函数，使用加法和乘法处理与和或的问题,可以研究逻辑运算和加法运算哪一个更快，使用更快的一个

    input:
        :param n1: np.ndarray: 第一个输入矩阵
        :param n2: np.ndarray: 第二个输入矩阵
        :param op: np.ndarray: 运算符
    return:
        :return: np.ndarray

    """
    if op == 'or':
        return n1 + n2
    elif op == 'and':
        return n1 * n2


def unify(arr):
    """
    unify each row of input array so that the sum of all elements in one row is 1, and each element remains
    its original ratio to the sum
    调整输入矩阵每一行的元素，使得所有元素等比例缩小（或放大）后的和为1

    example:
    unify([[3.0, 2.0, 5.0], [2.0, 3.0, 5.0]])
    =
    [[0.3, 0.2, 0.5], [0.2, 0.3, 0.5]]

    :param arr: type: np.ndarray
    :return: ndarray
    """
    assert isinstance(arr, np.ndarray), 'Input should be ndarray!'
    s = arr.sum(1)
    shape = (s.shape[0], 1)
    return arr / s.reshape(shape)


class Operator:
    """交易操作生成类，通过简单工厂模式创建择时属性类和选股属性类，并根据这两个属性类的结果生成交易清单

    交易操作生成类包含若干个选股对象组件，若干个择时对象组件，以及若干个风险控制组件，所有这些组件对象都能
    在同一组历史数据对象上进行相应的选股操作、择时操作并进行风控分析。不同的选股或择时对象工具独立地在历史数据
    对象上生成选股蒙版或多空蒙版，这些独立的选股蒙版及多空蒙版又由不同的方式混合起来（通过交易操作对象的蒙版
    混合属性确定，其中选股蒙版混合属性是一个逻辑表达式，根据这个逻辑表达式用户可以确定所有的蒙版的混合方式，
    例如“0 or （ 1 and （ 2 and 3 ） or 4 ）”；多空信号的生成方式是三个生成选项之一）。生成一个
    综合应用所有择时选股风控策略在目标历史数据上后生成的一个交易信号记录，交易信号经过合法性修改后成为
    一个最终输出的合法交易记录（信号）

    """

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表
    def __init__(self, selecting_types=['simple'],
                 timing_types=['simple'],
                 ricon_types=['none']):
        # 根据输入的参数生成择时具体类:
        # 择时类的混合方式有：
        # pos-N：只有当大于等于N个策略看多时，输出为看多，否则为看空
        # chg-N：在某一个多空状态下，当第N个反转信号出现时，反转状态
        # cumulate：没有绝对的多空状态，给每个策略分配同样的权重，当所有策略看多时输出100%看多，否则
        # 输出的看多比例与看多的策略的权重之和相同，当多空状态发生变化时会生成相应仓位的交易信号
        # 对象属性：
        # 交易信号通用属性：
        self.__Tp0 = False  # 是否允许T+0交易，True时允许T+0交易，否则不允许
        # 交易策略属性：
        # 对象的timings属性和timing_types属性都是列表，包含若干策略而不是一个策略
        self.__timing_types = []
        self.__timing = []
        self.__timing_blender = 'pos-1'  # 默认的择时策略混合方式
        # print timing_types
        for timing_type in timing_types:
            # print timing_type.lower()
            # 通过字符串比较确认timing_type的输入参数来生成不同的具体择时策略对象，使用.lower()转化为全小写字母
            self.__timing_types.append(timing_type)
            if timing_type.lower() == 'cross_line':
                self.__timing.append(TimingCrossline())
            elif timing_type.lower() == 'macd':
                self.__timing.append(TimingMACD())
            elif timing_type.lower() == 'dma':
                self.__timing.append(TimingDMA())
            elif timing_type.lower() == 'trix':
                self.__timing.append(TimingTRIX())
            else:  # 默认情况下使用simple策略
                self.__timing.append(TimingSimple())
                self.__timing_types.pop()
                self.__timing_types.append('simple')
                # print timing_type
        # 根据输入参数创建不同的具体选股策略对象。selecting_types及selectings属性与择时策略对象属性相似
        # 都是列表，包含若干相互独立的选股策略（至少一个）
        self.__selecting_type = []
        self.__selecting = []
        # 选股策略的混合方式使用以下字符串描述。简单来说，每个选股策略都独立地生成一个选股蒙版，每个蒙版与其他的
        # 蒙版的混合方式要么是OR（+）要么是AND（*），最终混合的结果取决于这些蒙版的混合方法和混合顺序而多个蒙版
        # 的混合方式就可以用一个类似于四则运算表达式的方式来描述，例如“（ 0 + 1 ） * （ 2 + 3 * 4 ）”
        # 在操作生成模块中，有一个表达式解析器，通过解析四则运算表达式来解算selecting_blender_string，并将混
        # 合的步骤以前缀表达式的方式存储在selecting_blender中，在混合时按照前缀表达式的描述混合所有蒙版。注意
        # 表达式中的数字代表selectings列表中各个策略的索引值
        cur_type = 0
        self.__selecting_blender_string = ''
        for selecting_type in selecting_types:
            self.__selecting_type.append(selecting_type)
            if cur_type == 0:
                self.__selecting_blender_string += str(cur_type)
            else:
                self.__selecting_blender_string += ' or ' + str(cur_type)
            cur_type += 1
            if selecting_type.lower() == 'trend':
                self.__selecting.append(SelectingTrend())
            elif selecting_type.lower() == 'random':
                self.__selecting.append(SelectingRandom())
            elif selecting_type.lower() == 'ranking':
                self.__selecting.append(SelectingRanking())
            else:
                self.__selecting.append(SelectingSimple())
                self.__selecting_type.pop()
                self.__selecting_type.append('simple')
            # create selecting blender by selecting blender string
            self.__selecting_blender = self._exp_to_blender

        # 根据输入参数生成不同的风险控制策略对象
        self.__ricon_type = []
        self.__ricon = []
        self.__ricon_blender = 'add'
        for ricon_type in ricon_types:
            self.__ricon_type.append(ricon_type)
            if ricon_type.lower() == 'none':
                self.__ricon.append(RiconNone())
            elif ricon_type.lower() == 'urgent':
                self.__ricon.append(RiconUrgent())
            else:
                self.__ricon.append(RiconNone())
                self.__ricon_type.append('none')

    @property
    def timing(self):
        return self.__timing

    @property
    def selecting(self):
        return self.__selecting

    @property
    def ricon(self):
        return self.__ricon

    @property
    def strategies(self):
        stg = []
        stg.extend(self.timing)
        stg.extend(self.selecting)
        stg.extend(self.ricon)
        return stg

    # Operation对象有两类属性需要设置：blender混合器属性、Parameters策略参数或属性
    # 这些属性参数的设置需要在OP模块设置一个统一的设置入口，同时，为了实现与Optimizer模块之间的接口
    # 还需要创建两个Opti接口函数，一个用来根据的值创建合适的Space初始化参数，另一个用于接受opt
    # 模块传递过来的参数，分配到合适的策略中去

    def set_blender(self, blender_type, *args, **kwargs):
        # 统一的blender混合器属性设置入口
        if type(blender_type) == str:
            if blender_type.lower() == 'selecting':
                self.__set_selecting_blender(*args, **kwargs)
            elif blender_type.lower() == 'timing':
                self.__set_timing_blender(*args, **kwargs)
            elif blender_type.lower() == 'ricon':
                self.__set_ricon_blender(*args, **kwargs)
            else:
                print('wrong input!')
                pass
        else:
            print('blender_type should be a string')
        pass

    def set_parameter(self, stg_id, pars=None, opt_tag=None, par_boes=None):
        """# 统一的策略参数设置入口，stg_id标识接受参数的具体成员策略
        # stg_id的格式为'x-n'，其中x为's/t/r'中的一个字母，n为一个整数"""
        if type(stg_id) == str:
            l = stg_id.split('-')
            stg = l[0]
            num = int(l[1])
            if stg.lower() == 's':
                strategy = self.selecting[num]
            elif stg.lower() == 't':
                strategy = self.timing[num]
            elif stg.lower() == 'r':
                strategy = self.ricon[num]
            else:
                print('wrong input!')
                return
            if pars is not None:
                strategy.set_pars(pars)
            if opt_tag is not None:
                strategy.set_opt_tag(opt_tag)
            if par_boes is not None:
                strategy.set_par_boes(par_boes)
        else:
            print('blender_type should be a string')
        pass

    def set_opt_par(self, opt_par):
        # 将输入的opt参数切片后传入stg的参数中
        s = 0
        k = 0
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass
            elif stg.opt_tag == 1:
                k += stg.par_count
                stg.set_pars(opt_par[s:k])
                s = k
            elif stg.opt_tag == 2:
                k += 1
                stg.set_pars(opt_par[s:k])
                s = k

    def get_opt_space_par(self):
        ranges = []
        types = []
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass  # 策略优化方案关闭
            elif stg.opt_tag == 1:
                ranges.extend(stg.par_boes)
                types.extend(stg.par_types)
            elif stg.opt_tag == 2:
                ranges.append(stg.par_boes)
                types.extend(['enum'])
        return ranges, types
        pass

    # =================================================
    # 下面是Operation模块的公有方法：
    def info(self):
        """# 打印出当前交易操作对象的信息，包括选股、择时策略的类型，策略混合方法、风险控制策略类型等等信息
        # 如果策略包含更多的信息，还会打印出策略的一些具体信息，如选股策略的信息等
        # 在这里调用了私有属性对象的私有属性，不应该直接调用，应该通过私有属性的公有方法打印相关信息
        # 首先打印Operation木块本身的信息"""
        print('OPERATION MODULE INFO:')
        print('=' * 25)
        print('Information of the Module')
        print('=' * 25)
        # 打印各个子模块的信息：
        # 首先打印Selecting模块的信息
        print('Total count of Selecting strategies:', len(self.__selecting))
        print('the blend type of selecting strategies is', self.__selecting_blender_string)
        print('Parameters of Selecting Strategies:')
        for sel in self.selecting:
            sel.info()
        print('#' * 25)

        # 接着打印 timing模块的信息
        print('Total count of timing strategies:', len(self.__timing))
        print('The blend type of timing strategies is', self.__timing_blender)
        print('Parameters of timing Strategies:')
        for tmg in self.timing:
            tmg.info()
        print('#' * 25)

        # 最后打印Ricon模块的信息
        print('Total count of Risk Control strategies:', len(self.__ricon))
        print('The blend type of Risk Control strategies is', self.__ricon_blender)
        for ric in self.ricon:
            ric.info()
        print('#' * 25)

    def create(self, hist_extract):
        """# 操作信号生成方法，在输入的历史数据上分别应用选股策略、择时策略和风险控制策略，生成初步交易信号后，
        # 对信号进行合法性处理，最终生成合法交易信号
        # 输入：
            # hist_extract：从数据仓库中导出的历史数据，包含多只股票在一定时期内特定频率的一组或多组数据
        # 输出：=====
            # lst：使用对象的策略在历史数据期间的一个子集上产生的所有合法交易信号，该信号可以输出到回测
            # 模块进行回测和评价分析，也可以输出到实盘操作模块触发交易操作
        #print( 'Time measurement: selection_mask creation')
        # 第一步，在历史数据上分别使用选股策略独立产生若干选股蒙板（sel_mask）
        # 选股策略的所有参数都通过对象属性设置，因此在这里不需要传递任何参数"""
        sel_masks = []
        assert type(hist_extract) is pd.DataFrame, 'Type Error: the extracted historical data is a Pandas DataFrame'
        shares = hist_extract.columns
        date_list = hist_extract.index
        h_v = hist_extract.values
        for sel in self.__selecting:  # 依次使用选股策略队列中的所有策略逐个生成选股蒙板
            # print('SPEED test OP create, Time of sel_mask creation')
            sel_masks.append(sel.generate(h_v, date_list, shares))  # 生成的选股蒙板添加到选股蒙板队列中
        # print('SPEED test OP create, Time of sel_mask blending')
        # %time (self.__selecting_blend(sel_masks))
        sel_mask = self.__selecting_blend(sel_masks)  # 根据蒙板混合前缀表达式混合所有蒙板
        # sel_mask.any(0) 生成一个行向量，每个元素对应sel_mask中的一列，如果某列全部为零，该元素为0，
        # 乘以hist_extract后，会把它对应列清零，因此不参与后续计算，降低了择时和风控计算的开销
        selected_shares = sel_mask.any(0)
        hist_selected = hist_extract * selected_shares
        # print ('Time measurement: ls_mask creation')
        # 第二步，使用择时策略在历史数据上独立产生若干多空蒙板(ls_mask)
        ls_masks = []
        for tmg in self.__timing:  # 依次使用择时策略队列中的所有策略逐个生成多空蒙板
            # 生成多空蒙板时忽略在整个历史考察期内从未被选中过的股票：
            # print('SPEED test OP create, Time of ls_mask creation')
            ls_masks.append(tmg.generate(h_v))
            # print(tmg.generate(h_v))
            # print('ls mask created: ', tmg.generate(hist_selected).iloc[980:1000])
        # print('SPEED test OP create, Time of ls_mask blending')
        # %time self.__timing_blend(ls_masks)
        ls_mask = self.__timing_blend(ls_masks)  # 混合所有多空蒙板生成最终的多空蒙板
        # print( '\n long/short mask: \n', ls_mask)
        # print 'Time measurement: risk-control_mask creation'
        # 第三步，风险控制交易信号矩阵生成（简称风控矩阵）
        ricon_mats = []
        for ricon in self.__ricon:  # 依次使用风控策略队列中的所有策略生成风险控制矩阵
            # print('SPEED test OP create, Time of ricon_mask creation')
            ricon_mats.append(ricon.generate(h_v))  # 所有风控矩阵添加到风控矩阵队列
        # print('SPEED test OP create, Time of ricon_mask blending')
        # %time self.__ricon_blend(ricon_mats)
        ricon_mat = self.__ricon_blend(ricon_mats)  # 混合所有风控矩阵后得到最终的风控策略
        # print ('risk control matrix \n', ricon_mat[980:1000])
        # print (ricon_mat)
        # print ('sel_mask * ls_mask: ', (ls_mask * sel_mask))
        # 使用mask_to_signal方法将多空蒙板及选股蒙板的乘积（持仓蒙板）转化为交易信号，再加上风控交易信号矩阵，并对交易信号进行合法化
        # print('SPEED test OP create, Time of operation mask creation')
        # %time self._legalize(self._mask_to_signal(ls_mask * sel_mask) + (ricon_mat))
        op_mat = _legalize(_mask_to_signal(ls_mask * sel_mask) + ricon_mat)
        # print('SPEED test OP create, Time of converting op matrix into DataFrame')
        # pd.DataFrame(op_mat, index = date_list, columns = shares)
        lst = pd.DataFrame(op_mat, index=date_list, columns=shares)
        # print ('operation matrix: ', '\n', lst.loc[lst.any(axis = 1)]['2007-01-15': '2007-03-01'])
        # return lst[lst.any(1)]
        # 消除完全相同的行和数字全为0的行
        lst_out = lst[lst.any(1)]
        keep = (lst_out - lst_out.shift(1)).any(1)
        return lst_out[keep]

        ################################################################

    # 下面是Operation模块的私有方法

    def __set_timing_blender(self, timing_blender):
        """设置择时策略混合方式，混合方式包括pos-N,chg-N，以及cumulate三种

        输入：
            参数 timing_blender，str，合法的输入包括：
                'chg-N': N为正整数，取值区间为1到len(timing)的值，表示多空状态在第N次信号反转时反转
                'pos-N': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                'cumulate': 在每个策略发生反转时都会产生交易信号，但是信号强度为1/len(timing)
        输出：=====
            无
        """
        self.__timing_blender = timing_blender

    def __set_selecting_blender(self, selecting_blender_expression):
        # 设置选股策略的混合方式，混合方式通过选股策略混合表达式来表示
        # 给选股策略混合表达式赋值后，直接解析表达式，将选股策略混合表达式的前缀表达式存入选股策略混合器
        if not type(selecting_blender_expression) is str:  # 如果输入不是str类型
            self.__selecting_blender = self._exp_to_blender
            self.__selecting_blender_string = '0'
        else:
            self.__selecting_blender = self._exp_to_blender
            self.__selecting_blender_string = selecting_blender_expression

    def __set_ricon_blender(self, ricon_blender):
        self.__ricon_blender = ricon_blender

    def __timing_blend(self, ls_masks):
        """# 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板
        # input：=====
            :type: ls_masks：object ndarray, 多空蒙板列表，包含至少一个多空蒙板
        # return：=====
            :rtype: object: 一个混合后的多空蒙板
        """
        blndr = self.__timing_blender  # 从对象的属性中读取择时混合参数
        assert type(blndr) is str, 'Parmameter Type Error: the timing blender should be a text string!'
        # print 'timing blender is:', blndr
        l_m = 0
        for msk in ls_masks:  # 计算所有多空模版的和
            l_m += msk
        if blndr[0:3] == 'chg':  # 出现N个状态变化信号时状态变化
            # TODO: ！！本混合方法暂未完成！！
            # chg-N方式下，持仓仅有两个位置，1或0，持仓位置与各个蒙板的状态变化有关，如果当前状态为空头，只要有N个或更多
            # 蒙板空转多，则结果转换为多头，反之亦然。这种方式与pos-N的区别在于，pos-N在多转空时往往滞后，因为要满足剩余
            # 的空头数量小于N后才会转空头，而chg-N则不然。例如，三个组合策略下pos-1要等至少两个策略多转空后才会转空，而
            # chg-1只要有一个策略多转空后，就会立即转空
            # 已经实现的chg-1方法由pandas实现，效率很低
            # print 'the first long/short mask is\n', ls_masks[-1]
            assert isinstance(l_m, np.ndarray), 'TypeError: the long short position mask should be an ndArray'
            return np.apply_along_axis(_timing_blend_change, 1, l_m)
        else:  # 另外两种混合方式都需要用到蒙板累加，因此一同处理
            l_count = len(ls_masks)
            # print 'the first long/short mask is\n', ls_masks[-1]
            if blndr == 'cumulate':
                # cumulate方式下，持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，只有所有蒙板均看空时，最终结果才看空
                # 所有蒙板的权重相同，因此，如果一共五个蒙板三个看多两个看空时，持仓为60%
                # print 'long short masks are merged by', blndr, 'result as\n', l_m / l_count
                return l_m / l_count
            elif blndr[0:3] == 'pos':
                # pos-N方式下，持仓同样取决于看多的蒙板的数量，但是持仓只能为1或0，只有满足N个或更多蒙板看多时，最终结果
                # 看多，否则看空，如pos-2方式下，至少两个蒙板看多则最终看多，否则看空
                # print 'timing blender mode: ', blndr
                n = int(blndr[-1])
                # print 'long short masks are merged by', blndr, 'result as\n', l_m.clip(n - 1, n) - (n - 1)
                return l_m.clip(n - 1, n) - (n - 1)
            else:
                print('Blender text not recognized!')
        pass

    def __selecting_blend(self, sel_masks):
        #
        exp = self.__selecting_blender[:]
        # print('expression in operation module', exp)
        s = []
        while exp:  # previously: while exp != []
            if exp[-1].isdigit():
                s.append(sel_masks[int(exp.pop())])
            else:
                s.append(_blend(s.pop(), s.pop(), exp.pop()))
        return unify(s[0])

    def __ricon_blend(self, ricon_mats):
        if self.__ricon_blender == 'add':
            r_m = ricon_mats.pop()
            while ricon_mats:  # previously while ricon_mats != []
                r_m += ricon_mats.pop()
            return r_m

    @property
    def _exp_to_blender(self):
        """# 选股策略混合表达式解析程序，将通常的中缀表达式解析为前缀运算队列，从而便于混合程序直接调用
        # 系统接受的合法表达式为包含 '*' 与 '+' 的中缀表达式，符合人类的思维习惯，使用括号来实现强制
        # 优先计算，如 '0 + (1 + 2) * 3'; 表达式中的数字0～3代表选股策略列表中的不同策略的索引号
        # 上述表达式虽然便于人类理解，但是不利于快速计算，因此需要转化为前缀表达式，其优势是没有括号
        # 按照顺序读取并直接计算，便于程序的运行。为了节省系统运行开销，在给出混合表达式的时候直接将它
        # 转化为前缀表达式的形式并直接存储在blender列表中，在混合时直接调用并计算即可
        # input： =====
            no input parameter
        # return：===== s2: 前缀表达式
            :rtype: list: 前缀表达式
        """
        prio = {'or': 0,
                'and': 1}
        # 定义两个队列作为操作堆栈
        s1 = []  # 运算符栈
        s2 = []  # 结果栈
        # 读取字符串并读取字符串中的各个元素（操作数和操作符），当前使用str对象的split()方法进行，要
        # 求字符串中个元素之间用空格或其他符号分割，应该考虑写一个self.__split()方法，不依赖空格对
        # 字符串进行分割
        # exp_list = self.__selecting_blender_string.split()
        exp_list = list(self.__selecting_blender_string)
        # 开始循环读取所有操作元素
        while exp_list:
            s = exp_list.pop()
            # 从右至左逐个读取表达式中的元素（数字或操作符）
            # 并按照以下算法处理
            if s.isdigit():
                # 1，如果元素是数字则压入结果栈
                s2.append(s)

            elif s == ')':
                # 2，如果元素是反括号则压入运算符栈
                s1.append(s)
            elif s == '(':
                # 3，扫描到（时，依次弹出所有运算符直到遇到），并把该）弹出
                while s1[-1] != ')':
                    s2.append(s1.pop())
                s1.pop()
            elif s in prio.keys():
                # 4，扫描到运算符时：
                if s1 == [] or s1[-1] == ')' or prio[s] >= prio[s1[-1]]:
                    # 如果这三种情况则直接入栈
                    s1.append(s)
                else:
                    # 否则就弹出s1中的符号压入s2，并将元素放回队列
                    s2.append(s1.pop())
                    exp_list.append(s)
        while s1:
            s2.append(s1.pop())
        s2.reverse()  # 表达式解析完成，生成前缀表达式
        return s2
