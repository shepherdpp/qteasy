# coding=utf-8
# core.py

# ======================================
# This file contains core functions and
# core Classes. Such as looping and
# optimizations, Configs and Spaces, etc.
# 2021 Chinese New Year update ^_^
# Happy New Year and prosperous in 2021!!
# ======================================

import pandas as pd
import numpy as np
import time
import math
import logging
from warnings import warn

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

from .history import get_history_panel, HistoryPanel, stack_dataframes
from .utilfuncs import time_str_format, progress_bar, str_to_list, regulate_date_format
from .utilfuncs import is_market_trade_day, next_market_trade_day, prev_market_trade_day, weekday_name
from .space import Space, ResultPool
from .finance import Cost, CashPlan
from .operator import Operator
from .visual import _plot_loop_result, _print_loop_result, _print_test_result, \
    _print_operation_signal, _plot_test_result
from .evaluate import evaluate, performance_statistics
from ._arg_validators import _validate_key_and_value
from .tsfuncs import stock_basic

from ._arg_validators import QT_CONFIG, _vkwargs_to_text

AVAILABLE_EVALUATION_INDICATORS = []
AVAILABLE_SHARE_INDUSTRIES = ['银行', '全国地产', '互联网', '环境保护', '区域地产',
                              '酒店餐饮', '运输设备', '综合类', '建筑工程', '玻璃',
                              '家用电器', '文教休闲', '其他商业', '元器件', 'IT设备',
                              '其他建材', '汽车服务', '火力发电', '医药商业', '汽车配件',
                              '广告包装', '轻工机械', '新型电力', '多元金融', '饲料',
                              '电气设备', '房产服务', '石油加工', '铅锌', '农业综合',
                              '批发业', '通信设备', '旅游景点', '港口', '机场',
                              '石油贸易', '空运', '医疗保健', '商贸代理', '化学制药',
                              '影视音像', '工程机械', '软件服务', '证券', '化纤', '水泥',
                              '生物制药', '专用机械', '供气供热', '农药化肥', '机床制造',
                              '百货', '中成药', '路桥', '造纸', '食品', '黄金',
                              '化工原料', '矿物制品', '水运', '日用化工', '机械基件',
                              '汽车整车', '煤炭开采', '铁路', '染料涂料', '白酒', '林业',
                              '水务', '水力发电', '旅游服务', '纺织', '铝', '保险',
                              '园区开发', '小金属', '铜', '普钢', '航空', '特种钢',
                              '种植业', '出版业', '焦炭加工', '啤酒', '公路', '超市连锁',
                              '钢加工', '渔业', '农用机械', '软饮料', '化工机械', '塑料',
                              '红黄酒', '橡胶', '家居用品', '摩托车', '电器仪表', '服饰',
                              '仓储物流', '纺织机械', '电器连锁', '装修装饰', '半导体',
                              '电信运营', '石油开采', '乳制品', '商品城', '公共交通',
                              '陶瓷', '船舶']
AVAILABLE_SHARE_AREA = ['深圳', '北京', '吉林', '江苏', '辽宁', '广东',
                        '安徽', '四川', '浙江', '湖南', '河北', '新疆',
                        '山东', '河南', '山西', '江西', '青海', '湖北',
                        '内蒙', '海南', '重庆', '陕西', '福建', '广西',
                        '天津', '云南', '贵州', '甘肃', '宁夏', '黑龙江',
                        '上海', '西藏']
AVAILABLE_SHARE_MARKET = ['主板', '中小板', '创业板', '科创板', 'CDR']
AVAILABLE_SHARE_EXCHANGES = ['SZSE', 'SSE']


# TODO: 使用logging模块来管理logs
class Log:
    """ 数据记录类，策略选股、择时、风险控制、交易信号生成、回测等过程中的记录的基类

    记录各个主要过程中的详细信息，并写入内存
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


# TODO: Usability improvements:
# TODO: 1: 增加PREDICT模式，完善predict模式所需的参数，完善其他优化算法的参数
# TODO: 完善config字典的信息属性，使得用户可以快速了解当前配置
# TODO: Config应该有一个保存功能，或至少有一个"read_last"功能，以便用户长期保存常用的上下文参数变量
# TODO: 使用C实现回测的关键功能，并用python接口调用，以实现速度的提升，或者使用numba实现加速
def _loop_step(pre_cash: float,
               pre_amounts: np.ndarray,
               op: np.ndarray,
               prices: np.ndarray,
               rate: Cost,
               moq_buy: float = 100,
               moq_sell: float = 1,
               print_log: bool = False,
               share_names: list = None) -> tuple:
    """ 对单次交易进行处理，采用向量化计算以提升效率

    input：=====
        :param pre_cash,
            :type pre_cash: np.ndarray
            本次交易开始前账户现金余额

        :param pre_amounts,
            :type pre_amounts: np.ndarray:
            交易开始前各个股票账户中的股份余额

        :param op,
            :type op: np.ndarray
            本次交易的个股交易清单

        :param prices：
            :type prices: np.ndarray，
            本次交易发生时各个股票的价格

        :param rate：
            :type rate: object Cost
            交易成本率对象

        :param moq_buy：
            :type moq_buy: float:
            投资产品最买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

        :param moq_sell：
            :type moq_sell: float:
            投资产品最买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

        :param print_log：
            :type print_log: bool:
            是否在回测过程中打印交易记录，临时解决方案，会导致效率降低。以后会被logs代替

        :param share_names：
            :type share_names: list:
            以list的形式存储的股票名称，share_names列表的元素数量与股票的数量相同

    return：===== tuple，包含四个元素
        cash：       交易后账户现金余额
        amounts：    交易后每个个股账户中的股份余额
        fee：        本次交易总费用
        value：      本次交易后资产总额（按照交易后现金及股份余额以及交易时的价格计算）
    """
    # 计算交易前现金及股票余额在当前价格下的资产总额
    pre_value = pre_cash + (pre_amounts * prices).sum()
    if print_log:
        # asset_array = np.array([pre_amounts, prices])
        print(f'本期期初总资产:{pre_value:.2f}，其中包括: \n'
              f'期初现金:      {pre_cash:.2f}, 资产总价值: {pre_value - pre_cash:.2f}\n'
              f'期初持有资产:  {np.around(pre_amounts, 2)}\n'
              f'本期资产价格:  {np.around(prices, 2)}\n'
              f'本期交易信号:  {op}')
    # 计算按照交易清单出售资产后的资产余额以及获得的现金
    # 根据出售持有资产的份额数量计算获取的现金
    amount_sold, cash_gained, fee_selling = rate.get_selling_result(prices=prices,
                                                                    op=op,
                                                                    amounts=pre_amounts,
                                                                    moq=moq_sell)
    if print_log:
        # 当没有给出share_dict，同时需要输出print_log的时候，生成一个临时share_dict
        if share_names is None:
            share_names = np.arange(len(op))
        item_sold = np.where(op < 0)[0]
        if len(item_sold) > 0:
            for i in item_sold:
                if prices[i] != 0:
                    print(f' - 资产:\'{share_names[i]}\' - 以本期价格 {np.round(prices[i], 2)} '
                          f'出售 {np.round(-amount_sold[i], 2)} 份')
                else:
                    print(f' - 资产:\'{share_names[i]}\' - 本期停牌, 价格为 {np.round(prices[i], 2)} '
                          f'暂停交易，出售 {0.0} 份')
            print(f'获得现金 {cash_gained:.2f} 并产生交易费用 {fee_selling:.2f}, '
                  f'交易后现金余额: {(pre_cash + cash_gained):.3f}')
        else:
            print(f'本期未出售任何资产,交易后现金余额与资产总量不变')
    # 本期出售资产后现金余额 = 期初现金余额 + 出售资产获得现金总额
    cash = pre_cash + cash_gained
    # 初步估算按照交易清单买入资产所需要的现金，如果超过持有现金，则按比例降低买入金额
    pur_values = pre_value * op.clip(0)  # 使用clip来代替np.where，速度更快,且op.clip(1)比np.clip(op, 0, 1)快很多
    if print_log and pur_values.sum() > 0:
        print(f'本期计划买入资产动用资金: {pur_values.sum():.2f}')
    if pur_values.sum() > cash:
        # 估算买入资产所需现金超过持有现金
        pur_values = pur_values / pur_values.sum() * cash
        if print_log:
            print(f'由于持有现金不足，调整动用资金数量为: {pur_values.sum():.2f}')
            # 按比例降低分配给每个拟买入资产的现金额度
    # 计算购入每项资产实际花费的现金以及实际买入资产数量，如果MOQ不为0，则需要取整并修改实际花费现金额
    amount_purchased, cash_spent, fee_buying = rate.get_purchase_result(prices=prices,
                                                                        op=op,
                                                                        cash_to_be_spent=pur_values,
                                                                        moq=moq_buy)
    if print_log:
        # 当没有给出share_dict，同时需要输出print_log的时候，生成一个临时share_dict
        if share_names is None:
            share_names = np.arange(len(op))
        item_purchased = np.where(op > 0)[0]
        if len(item_purchased) > 0:
            for i in item_purchased:
                print(f' - 资产:\'{share_names[i]}\' - 以本期价格 {np.round(prices[i], 2)}'
                      f' 买入 {np.round(amount_purchased[i], 2)} 份')
            print(f'实际花费现金 {-cash_spent:.2f} 并产生交易费用: {fee_buying:.2f}')
        else:
            print(f'本期未购买任何资产,交易后现金余额与资产总量不变')
    # 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = fee_buying + fee_selling
    # 持有资产总额 = 期初资产余额 + 本期买入资产总额 + 本期卖出资产总额（负值）
    amounts = pre_amounts + amount_purchased + amount_sold
    # 期末现金余额 = 本期出售资产后余额 + 本期购入资产花费现金总额（负值）
    cash += cash_spent.sum()
    # 期末资产总价值 = 期末资产总额 * 本期资产单价 + 期末现金余额
    value = (amounts * prices).sum() + cash
    if print_log:
        print(f'期末现金: {cash:.2f}, 期末总资产: {value:.2f}\n')
    return cash, amounts, fee, value


def _get_complete_hist(looped_value: pd.DataFrame,
                       h_list: pd.DataFrame,
                       ref_list: pd.DataFrame,
                       with_price: bool = False) -> pd.DataFrame:
    """完成历史交易回测后，填充完整的历史资产总价值清单，
        同时在回测清单中填入参考价格数据，参考价格数据用于数据可视化对比，参考数据的来源为Config.reference_asset

    input:=====
        :param looped_value:
            :type looped_value: pd.DataFrame
            完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录

        :param h_list:
            :type h_list: pd.DataFrame
            完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格

        :param ref_list:
            :type ref_list: pd.DataFrame
            参考资产的历史价格清单，参考资产用于收益率的可视化对比，同时用于计算alpha、sharp等指标

        :param with_price:
            :type with_price: boolean
            True时在返回的清单中包含历史价格，否则仅返回资产总价值

    return: =====
        pandas.DataFrame:
        重新填充的完整历史交易日资产总价值清单
    """
    # 获取价格清单中的投资产品列表
    shares = h_list.columns  # 获取资产清单
    start_date = looped_value.index[0]  # 开始日期
    looped_history = h_list.loc[start_date:]  # 回测历史数据区间 = [开始日期:]
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    purchased_shares = looped_value[shares].reindex(looped_history.index, method='ffill').fillna(0)
    cashes = looped_value['cash'].reindex(looped_history.index, method='ffill').fillna(0)
    fees = looped_value['fee'].reindex(looped_history.index).fillna(0)
    looped_value = looped_value.reindex(looped_history.index)
    # 这里采用了一种看上去貌似比较奇怪的处理方式：
    # 先为cashes、purchased_shares两个变量赋值，
    # 然后再将上述两个变量赋值给looped_values的列中
    # 这样看上去好像多此一举，为什么不能直接赋值，然而
    # 经过测试，如果直接用下面的代码直接赋值，将无法起到
    # 填充值的作用：
    # looped_value.cash = looped_value.cash.reindex(dates, method='ffill')
    looped_value[shares] = purchased_shares
    looped_value.cash = cashes
    looped_value.fee = looped_value['fee'].reindex(looped_history.index).fillna(0)
    looped_value['reference'] = ref_list.reindex(looped_history.index).fillna(0)
    # print(f'extended looped value according to looped history: \n{looped_value.info()}')
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象
    looped_value['value'] = (looped_history * looped_value[shares]).sum(axis=1) + looped_value['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        share_price_column_names = [name + '_p' for name in shares]
        looped_value[share_price_column_names] = looped_history[shares]
    # print(looped_value.tail(10))
    return looped_value


def _merge_invest_dates(op_list: pd.DataFrame, invest: CashPlan) -> pd.DataFrame:
    """将完成的交易信号清单与现金投资计划合并：
        检查现金投资计划中的日期是否都存在于交易信号清单op_list中，如果op_list中没有相应日期时，当交易信号清单中没有相应日期时，添加空交易
        信号，以便使op_list中存在相应的日期。

        注意，在目前的设计中，要求invest中的所有投资日期都为交易日（意思是说，投资日期当天资产价格不为np.nan）
        否则，将会导致回测失败（回测当天取到np.nan作为价格，引起总资产计算失败，引起连锁反应所有的输出结果均为np.nan。

        需要在CashPlan投资计划类中增加合法性判断

    :param op_list: 交易信号清单，一个DataFrame。index为Timestamp类型
    :param invest: CashPlan对象，投资日期和投资金额
    :return:
    """
    if not isinstance(op_list, pd.DataFrame):
        raise TypeError(f'operation list should be a pandas DataFrame, got {type(op_list)} instead')
    if not isinstance(invest, CashPlan):
        raise TypeError(f'invest plan should be a qteasy CashPlan, got {type(invest)} instead')
    for date in invest.dates:
        try:
            op_list.loc[date]
        except:
            op_list.loc[date] = 0
    op_list.sort_index(inplace=True)
    return op_list


# TODO: 并将过程和信息输出到log文件或log信息中，返回log信息
# TODO: 使用C实现回测核心功能，并用python接口调用，以实现效率的提升，或者使用numba实现加速
# TODO: 增加功能：上一次信号执行结果确认：
# TODO:         1, 如果上一次信号执行后有余量未完成，需要叠加到本次完成
# TODO:         2, 如果上次信号执行后本次无需执行（如完全相同的卖出信号，无需重复执行）则跳过本次执行

def apply_loop(op_list: pd.DataFrame,
               history_list: pd.DataFrame,
               cash_plan: CashPlan = None,
               cost_rate: Cost = None,
               moq_buy: float = 100.,
               moq_sell: float = 1,
               inflation_rate: float = 0.03,
               print_log: bool = False) -> pd.DataFrame:
    """使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
        现金额及费用，输出的结果可选

    input：=====
        :param cash_plan: float: 初始资金额，未来将被替换为CashPlan对象
        :param history_list: object pd.DataFrame: 完整历史价格清单，数据的频率由freq参数决定
        :param op_list: object pd.DataFrame: 标准格式交易清单，描述一段时间内的交易详情，每次交易一行数据
        :param cost_rate: float Rate: 交易成本率对象，包含交易费、滑点及冲击成本
        :param moq_buy: float：每次交易买进的最小份额单位
        :param moq_sell: float: 每次交易卖出的最小份额单位
        :param inflation_rate: float, 现金的时间价值率，如果>0，则现金的价值随时间增长，增长率为inflation_rate
        :param print_log: bool: 设置为True将打印回测详细日志

    output：=====
        Value_history: pandas.DataFrame: 包含交易结果及资产总额的历史清单

    """
    assert not op_list.empty, 'InputError: The Operation list should not be Empty'
    assert cost_rate is not None, 'TypeError: cost_rate should not be None type'
    assert cash_plan is not None, 'ValueError: cash plan should not be None type'
    if moq_buy == 0:
        assert moq_sell == 0, f'ValueError, if moq buy is 0, then moq_sell should also be 0, got {moq_sell}'
    if (moq_buy != 0) and (moq_sell != 0):
        assert moq_buy % moq_sell == 0, \
            f'ValueError, the sell moq should be divisible by moq_buy, or there will be mistake'

    # 根据最新的研究实验，在python3.6的环境下，nditer的速度显著地慢于普通的for-loop
    # 因此改回for-loop执行，直到找到更好的向量化执行方法
    # 提取交易清单中的所有数据，生成np.ndarray，即所有的交易信号
    op_list = _merge_invest_dates(op_list, cash_plan)
    op = op_list.values
    shares = op_list.columns
    share_dict = {k: v for k, v in zip(range(len(shares)), shares)}
    # 从价格清单中提取出与交易清单的日期相对应日期的所有数据
    # TODO: FutureWarning:
    # TODO: Passing list-likes to .loc or [] with any missing label will raise
    # TODO: KeyError in the future, you can use .reindex() as an alternative.
    # 为防止回测价格数据中存在Nan值，需要首先将Nan值替换成0，否则将造成错误值并一直传递到回测历史最后一天
    price = history_list.fillna(0).loc[op_list.index].values
    # 以下测试代码，将Nan值替换成前一个有效交易日的价格，这样有助于计算某只股票停牌日的实际资产，但是将造成
    # 股票停牌日的买卖错误信号，因此下面的算法将会导致错误结果
    # price = history_list.fillna(method='ffill').fillna(0).loc[op_list.index].values
    looped_dates = list(op_list.index)
    # 如果inflation_rate > 0 则还需要计算所有有交易信号的日期相对前一个交易信号日的现金增长比率，这个比率与两个交易信号日之间的时间差有关
    if inflation_rate > 0:
        # print(f'looped dates are like: {looped_dates}')
        days_timedelta = looped_dates - np.roll(looped_dates, 1)
        # print(f'days differences between two operations dates are {days_timedelta}')
        days_difference = np.zeros_like(looped_dates, dtype='int')
        for i in range(1, len(looped_dates)):
            days_difference[i] = days_timedelta[i].days
        inflation_factors = 1 + days_difference * inflation_rate / 250
    op_count = op.shape[0]  # 获取行数
    # 获取每一个资金投入日在历史时间序列中的位置
    investment_date_pos = np.searchsorted(looped_dates, cash_plan.dates)
    invest_dict = cash_plan.to_dict(investment_date_pos)
    # 初始化计算结果列表
    cash = 0  # 持有现金总额，期初现金总额总是0，在回测过程中到现金投入日时再加入现金
    amounts = [0] * len(history_list.columns)  # 投资组合中各个资产的持有数量，初始值为全0向量
    cashes = []  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
    fees = []  # 交易费用，记录每个操作时点产生的交易费用
    values = []  # 资产总价值，记录每个操作时点的资产和现金价值总和
    amounts_matrix = []
    date_print_format = '%Y/%m/%d'
    # TODO: use Numba to optimize the efficiency of the looping process
    for i in range(op_count):  # 对每一行历史交易信号开始回测
        if print_log:
            print(f'交易日期:{looped_dates[i].strftime(date_print_format)}, '
                  f'{weekday_name(looped_dates[i].date().weekday())}')
        if inflation_rate > 0:  # 现金的价值随时间增长，需要依次乘以inflation 因子，且只有持有现金增值，新增的现金不增值
            cash *= inflation_factors[i]
            if print_log:
                print(f'考虑现金增值, 上期现金: {(cash / inflation_factors[i]):.2f}, 经过{days_difference[i]}天后'
                      f'现金增值到{cash:.2f}')
        if i in investment_date_pos:
            # 如果在交易当天有资金投入，则将投入的资金加入可用资金池中
            cash += invest_dict[i]
            if print_log:
                print(f'本期新增投入现金, 本期现金: {(cash - invest_dict[i]):.2f}, 追加投资后现金增加到{cash:.2f}')
        # 调用loop_step()函数，计算下一期剩余资金、资产组合的持有份额、交易成本和下期资产总额
        cash, amounts, fee, value = _loop_step(pre_cash=cash,
                                               pre_amounts=amounts,
                                               op=op[i],
                                               prices=price[i],
                                               rate=cost_rate,
                                               moq_buy=moq_buy,
                                               moq_sell=moq_sell,
                                               print_log=print_log,
                                               share_names=shares)
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
    return value_history


def get_current_holdings() -> tuple:
    """ 获取当前持有的产品在手数量

    :return: tuple:
    """
    raise NotImplementedError


def get_stock_pool(date: str = '1970-01-01', **kwargs) -> list:
    """根据输入的参数筛选出合适的初始股票清单

        可以通过以下参数筛选股票, 每一个筛选条件都可以是str或者包含str的list，也可以为逗号分隔的str，只有符合要求的股票才会被筛选出来
            date:       根据上市日期选择，在改日期以前上市的股票将会被剔除：
            index:      根据指数筛选，不含在指定的指数内的股票将会被剔除
            industry:   公司所处行业，只有列举出来的行业会被选中
            area:       公司所处省份，只有列举出来的省份的股票才会被选中
            market:     市场，分为主板、创业板等
            exchange:   交易所，包括上海证券交易所和深圳股票交易所

    input:
    :param date:
    return:
    a list that contains ts_codes of all selected shares

    """
    try:
        date = pd.to_datetime(date)
    except:
        date = pd.to_datetime('1970-01-01')
    # validate all input args:
    if not all(arg in ['index', 'industry', 'area', 'market', 'exchange'] for arg in kwargs.keys()):
        raise KeyError()
    if not all(isinstance(val, (str, list)) for val in kwargs.values()):
        raise KeyError()

    #
    share_basics = stock_basic(fields='ts_code,symbol,name,area,industry,market,list_date,exchange')
    share_basics['list_date'] = pd.to_datetime(share_basics.list_date)
    share_basics = share_basics.loc[share_basics.list_date >= date]

    for column, targets in zip(kwargs.keys(), kwargs.values()):
        if column == 'index':
            pass
        if isinstance(targets, str):
            targets = str_to_list(targets)
        if not all(isinstance(target, str) for target in targets):
            raise KeyError(f'the list should contain only strings')
        share_basics = share_basics.loc[share_basics[column].isin(targets)]

    return list(share_basics['ts_code'].values)


# TODO: 在这个函数中对config的各项参数进行检查和处理，将对各个日期的检查和更新（如交易日调整等）放在这里，直接调整
# TODO: config参数，使所有参数直接可用。并发出warning，不要在后续的使用过程中调整参数
def is_ready(**kwargs):
    """ 检查QT_CONFIG以及Operator对象，确认qt.run()是否具备基本运行条件

    :param kwargs:
    :return:
    """
    # 检查各个cash_amounts与各个cash_dates是否能生成正确的CashPlan对象

    # 检查invest(loop)、opti、test等几个start与end日期是否冲突

    # 检查invest(loop)、opti、test等几个cash_dates是否冲突


    return True


def info(**kwargs):
    """ qteasy 模块的帮助信息入口函数

    :param kwargs:
    :return:
    """
    raise NotImplementedError


def help(**kwargs):
    """ qteasy 模块的帮助信息入口函数

    :param kwargs:
    :return:
    """
    raise NotImplementedError


def configure(**kwargs):
    """ 配置qteasy的运行参数QT_CONFIG

    :param kwargs:
    :return:
    """
    for key in kwargs.keys():
        value = kwargs[key]
        _validate_key_and_value(key, value)
        QT_CONFIG.__setattr__(key, value)


def configuration(mode=None, type=None, opti_method=None, level=0, info=False, verbose=False):
    """ 显示qt当前的环境变量，

    :param mode:
    :param type:
    :param opti_method
    :param level:
    :param info:
    :param verbose:
    :return:
    """
    AVAILABLE_TYPES = ['system',
                       'cost',
                       ]
    if mode is None:
        mode = QT_CONFIG.mode
    kwargs = list()
    if mode == 'all':
        kwargs = ['mode',
                  'trade_batch_size',
                  'riskfree_ir',
                  'visual',
                  'log',
                  'asset_pool',
                  'asset_type',
                  'invest_start',
                  'invest_end',
                  'cost_fixed_buy',
                  'cost_fixed_sell',
                  'cost_rate_buy',
                  'cost_rate_sell',
                  'cost_slippage',
                  'invest_cash_amounts',
                  'invest_cash_dates',
                  'reference_asset',
                  'ref_asset_type',
                  'ref_asset_dtype',
                  'opti_start',
                  'opti_end',
                  'opti_cash_amounts',
                  'opti_cash_dates',
                  'test_start',
                  'test_end',
                  'test_cash_amounts',
                  'test_cash_dates',
                  'opti_method']
    elif mode == 0:
        kwargs = ['mode',
                  'asset_pool',
                  'asset_type',
                  'reference_asset',
                  'ref_asset_type',
                  'ref_asset_dtype']
    elif mode == 1:
        kwargs = ['mode',
                  'trade_batch_size',
                  'riskfree_ir',
                  'visual',
                  'log',
                  'asset_pool',
                  'asset_type',
                  'invest_start',
                  'invest_end',
                  'cost_fixed_buy',
                  'cost_fixed_sell',
                  'invest_cash_amounts',
                  'invest_cash_dates',
                  'reference_asset',
                  'ref_asset_type',
                  'ref_asset_dtype']
    elif mode == 2:
        kwargs = ['mode',
                  'trade_batch_size',
                  'riskfree_ir',
                  'visual',
                  'log',
                  'asset_pool',
                  'asset_type',
                  'opti_start',
                  'opti_end',
                  'opti_cash_amounts',
                  'opti_cash_dates',
                  'test_start',
                  'test_end',
                  'opti_method']
    else:
        raise KeyError(f'mode ({mode}) is not valid!')
    print(_vkwargs_to_text(kwargs=kwargs, level=level, info=info, verbose=verbose))


# TODO: 提高prepare_hist_data的容错度，当用户输入的回测开始日期和资金投资日期等
# TODO: 不匹配时，应根据优先级调整合理后继续完成回测或优化，而不是报错后停止运行
def check_and_prepare_hist_data(operator, config):
    """ 根据config参数字典中的参数，下载或读取所需的历史数据以及相关的投资资金计划

    :param: operator: Operator对象，
    :param: config, dict 参数字典
    :return:
        hist_op:
        hist_loop:
        hist_opti:
        hist_test:
        hist_opti_loop:
        hist_test_loop:

    """
    run_mode = config.mode
    # 如果run_mode=0，选取足够的历史数据生成迄今为止上一个交易日或本个交易日（如果运行时间在17:00以后）
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    # 根据不同的运行模式，设定不同的运行历史数据起止日期
    # 投资回测区间的开始日期根据invest_start和invest_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config.invest_cash_dates is None:
        invest_start = next_market_trade_day(config.invest_start).strftime('%Y%m%d')
        invest_cash_plan = CashPlan(invest_start,
                                    config.invest_cash_amounts[0],
                                    config.riskfree_ir)
    else:
        cash_dates = str_to_list(config.invest_cash_dates)
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        invest_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                    amounts=config.invest_cash_amounts,
                                    interest_rate=config.riskfree_ir)
        invest_start = regulate_date_format(invest_cash_plan.first_day)
        if pd.to_datetime(invest_start) != pd.to_datetime(config.invest_start):
            warn(f'first cash investment on {invest_start} differ from invest_start {config.invest_start}, first cash'
                 f' date will be used!',
                 RuntimeWarning)
    # 按照同样的逻辑设置优化区间和测试区间的起止日期

    # 优化区间开始日期根据opti_start和opti_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config.opti_cash_dates is None:
        opti_start = next_market_trade_day(config.opti_start).strftime('%Y%m%d')
        opti_cash_plan = CashPlan(opti_start,
                                  config.opti_cash_amounts[0],
                                  config.riskfree_ir)
    else:
        cash_dates = str_to_list(config.opti_cash_dates)
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        opti_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                  amounts=config.opti_cash_amounts,
                                  interest_rate=config.riskfree_ir)
        opti_start = regulate_date_format(opti_cash_plan.first_day)
        if pd.to_datetime(opti_start) != pd.to_datetime(config.opti_start):
            warn(f'first cash investment on {opti_start} differ from invest_start {config.opti_start}, first cash'
                 f' date will be used!',
                 RuntimeWarning)
        # TODO: 此处应该检查opti_start是否在config.opti_start与config.opti_end之间，否则raise

    # 测试区间开始日期根据opti_start和opti_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config.test_cash_dates is None:
        test_start = next_market_trade_day(config.test_start).strftime('%Y%m%d')
        test_cash_plan = CashPlan(test_start,
                                  config.test_cash_amounts[0],
                                  config.riskfree_ir)
    else:
        cash_dates = str_to_list(config.test_cash_dates)
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        test_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                  amounts=config.test_cash_amounts,
                                  interest_rate=config.riskfree_ir)
        test_start = regulate_date_format(test_cash_plan.first_day)
        if pd.to_datetime(test_start) != pd.to_datetime(config.test_start):
            warn(f'first cash investment on {test_start} differ from invest_start {config.test_start}, first cash'
                 f' date will be used!',
                 RuntimeWarning)
        # TODO: 此处应该检查test_start是否在config.test_start与config.test_end之间，否则raise
    # 设定投资结束日期
    if run_mode == 0:
        if is_market_trade_day(current_date) and current_time.hour > 21:  # 交易日22:00以后
            invest_end = regulate_date_format(current_date)
        else:  # 交易日17:00以前，查询到前一个交易日
            invest_end = regulate_date_format(prev_market_trade_day(current_date))
    else:
        invest_end = config.invest_end
    # 设置优化区间和测试区间的结束日期
    opti_end = config.opti_end
    test_end = config.test_end
    window_length = operator.max_window_length
    hist_op = get_history_panel(start=regulate_date_format(pd.to_datetime(invest_start) -
                                                           pd.Timedelta(int(window_length * 1.6), 'd')),
                                end=invest_end,
                                shares=config.asset_pool,
                                htypes=operator.op_data_types,
                                freq=operator.op_data_freq,
                                asset_type=config.asset_type,
                                chanel=config.hist_data_channel,
                                parallel=config.hist_dnld_parallel,
                                delay=config.hist_dnld_delay,
                                delay_every=config.hist_dnld_delay_evy,
                                progress=config.hist_dnld_prog_bar) if run_mode <= 1 else HistoryPanel()
    # 生成用于数据回测的历史数据，格式为pd.DataFrame，仅有一个价格数据用于计算交易价格
    hist_loop = hist_op.to_dataframe(htype='close')
    # fill np.inf in hist_loop to prevent from result in nan in value
    inf_locs = np.where(np.isinf(hist_loop))
    for row, col in zip(inf_locs[0], inf_locs[1]):
        hist_loop.iloc[row, col] = 0

    # 生成用于策略优化训练的训练历史数据集合
    hist_opti = get_history_panel(start=regulate_date_format(pd.to_datetime(opti_start) -
                                                             pd.Timedelta(int(window_length * 1.6), 'd')),
                                  end=opti_end,
                                  shares=config.asset_pool,
                                  htypes=operator.op_data_types,
                                  freq=operator.op_data_freq,
                                  asset_type=config.asset_type,
                                  chanel=config.hist_data_channel,
                                  parallel=config.hist_dnld_parallel,
                                  delay=config.hist_dnld_delay,
                                  delay_every=config.hist_dnld_delay_evy,
                                  progress=config.hist_dnld_prog_bar) if run_mode == 2 else HistoryPanel()
    # 生成用于优化策略测试的测试历史数据集合
    hist_test = get_history_panel(start=regulate_date_format(pd.to_datetime(test_start) -
                                                             pd.Timedelta(int(window_length * 1.6), 'd')),
                                  end=test_end,
                                  shares=config.asset_pool,
                                  htypes=operator.op_data_types,
                                  freq=operator.op_data_freq,
                                  asset_type=config.asset_type,
                                  chanel=config.hist_data_channel,
                                  parallel=config.hist_dnld_parallel,
                                  delay=config.hist_dnld_delay,
                                  delay_every=config.hist_dnld_delay_evy,
                                  progress=config.hist_dnld_prog_bar) if run_mode == 2 else HistoryPanel()

    hist_test_loop = hist_test.to_dataframe(htype='close')
    inf_locs = np.where(np.isinf(hist_test_loop))
    for row, col in zip(inf_locs[0], inf_locs[1]):
        hist_test_loop.iloc[row, col] = 0

    # 生成参考历史数据，作为参考用于回测结果的评价
    # 评价数据的历史区间应该覆盖invest/opti/test的数据区间
    all_starts = [pd.to_datetime(date_str) for date_str in [invest_start, opti_start, test_start]]
    all_ends = [pd.to_datetime(date_str) for date_str in [invest_end, opti_end, test_end]]
    refer_hist_start = regulate_date_format(min(all_starts))
    refer_hist_end = regulate_date_format(max(all_ends))
    hist_reference = (get_history_panel(start=refer_hist_start,
                                        end=refer_hist_end,
                                        shares=config.reference_asset,
                                        htypes=config.ref_asset_dtype,
                                        freq=operator.op_data_freq,
                                        asset_type=config.ref_asset_type,
                                        chanel=config.hist_data_channel,
                                        parallel=config.hist_dnld_parallel,
                                        delay=config.hist_dnld_delay,
                                        delay_every=config.hist_dnld_delay_evy,
                                        progress=config.hist_dnld_prog_bar)
                      ).to_dataframe(htype='close')

    return hist_op, hist_loop, hist_opti, hist_test, hist_test_loop, hist_reference, \
           invest_cash_plan, opti_cash_plan, test_cash_plan


def run(operator, **kwargs):
    """开始运行，qteasy模块的主要入口函数

        接受operator执行器对象作为主要的运行组件，根据输入的运行模式确定运行的方式和结果
        根据QT_CONFIG环境变量中的设置和运行模式（mode）进行不同的操作：
        mode == 0:
            进入实时信号生成模式：
            根据Config实时策略运行所需的历史数据，根据历史数据实时生成操作信号
            策略参数不能为空

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

        mode == 1:
            回测模式：
            根据Config规定的回测区间，使用History模块联机读取或从本地读取覆盖整个回测区间的历史数据
            生成投资资金模型，模拟在回测区间内使用投资资金模型进行模拟交易的结果
            输出对结果的评价（使用多维度的评价方法）
            输出回测日志·
            投资资金模型不能为空，策略参数不能为空

            根据执行器历史数据hist_op，应用operator执行器对象中定义的投资策略生成一张投资产品头寸及仓位建议表。
            这张表的每一行内的数据代表在这个历史时点上，投资策略建议对每一个投资产品应该持有的仓位。每一个历史时点的数据都是根据这个历史时点的
            相对历史数据计算出来的。这张投资仓位建议表的历史区间受Config上下文对象的"loop_period_start, loop_period_end, loop_period_freq"
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

        mode == 2:
            策略优化模式：
            根据Config规定的优化区间和回测区间，使用History模块联机读取或本地读取覆盖整个区间的历史数据
            生成待优化策略的参数空间，并生成投资资金模型
            使用指定的优化方法在优化区间内查找投资资金模型的全局最优或局部最优参数组合集合
            使用在优化区间内搜索到的全局最优策略参数在回测区间上进行多次回测并再次记录结果
            输出最优参数集合在优化区间和回测区间上的评价结果
            输出优化及回测日志
            投资资金模型不能为空，策略参数可以为空

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
                    1，Grid_searching                        网格搜索法：

                        网格法是最简单和直接的参数优化方法，在已经定义好的参数空间中，按照一定的间隔均匀地从向量空间中取出一系列的点，
                        逐个在优化空间中生成交易信号并进行回测，把所有的参数组合都测试完毕后，根据目标函数的值选择排名靠前的参数组合即可。

                        网格法能确保找到参数空间中的全剧最优参数，不过必须逐一测试所有可能的参数点，因此计算量相当大。同时，网格法只
                        适用于非连续的参数空间，对于连续空间，仍然可以使用网格法，但无法真正"穷尽"所有的参数组合

                        关于网格法的具体参数和输出，参见self._search_grid()函数的docstring

                    2，Montecarlo_searching                  蒙特卡洛法

                        蒙特卡洛法与网格法类似，也需要检查并测试参数空间中的大量参数组合。不过在蒙特卡洛法中，参数组合是从参数空间中随机
                        选出的，而且在参数空间中均匀分布。与网格法相比，蒙特卡洛方法不仅更适合于连续参数空间、通常情况下也有更好的性能。

                        关于蒙特卡洛方法的参数和输出，参见self._search_montecarlo()函数的docstring

                    3，Incremental_steped_searching          递进搜索法

                        递进步长法的基本思想是对参数空间进行多轮递进式的搜索，每一轮搜索方法与蒙特卡洛法相同但是每一轮搜索后都将搜索
                        范围缩小到更希望产生全局最优的子空间中，并在这个较小的子空间中继续使用蒙特卡洛法进行搜索，直到该子空间太小、
                        或搜索轮数大于设定值为止。

                        使用这种技术，在一个250*250*250的空间中，能够把搜索量从15,000,000降低到10,000左右,缩减到原来的1/1500，
                        却不太会影响最终搜索的效果。

                        关于递进步长法的参数和输出，参见self._search_incremental()函数的docstring

                    4，Genetic_Algorithm                     遗传算法

                        遗传算法适用于"超大"参数空间的参数寻优。对于有二到三个参数的策略来说，使用蒙特卡洛或网格法是可以承受的选择，
                        如果参数数量增加到4到5个，递进步长法可以帮助降低计算量，然而如果参数有数百个，而且每一个都有无限取值范围的时
                        候，任何一种基于网格的方法都没有应用的意义了。如果目标函数在参数空间中是连续且可微的，可以使用基于梯度的方法，
                        但如果目标函数不可微分，GA方法提供了一个在可以承受的时间内找到全局最优或局部最优的方法。

                        GA方法受生物进化论的启发，通过模拟生物在自然选择下的基因进化过程，在复杂的超大参数空间中搜索全局最优或局部最
                        优参数。GA的基本做法是模拟一个足够大的"生物"种群在自然环境中的演化，这些生物的"基因"是参数空间中的一个点，
                        在演化过程中，种群中的每一个个体会发生变异、也会通过杂交来改变或保留自己的"基因"，并把变异或杂交后的基因传递到
                        下一代。在每一代的种群中，优化器会计算每一个个体的目标函数并根据目标函数的大小确定每一个个体的生存几率和生殖几
                        率。由于表现较差的基因生存和生殖几率较低，因此经过数万乃至数十万带的迭代后，种群中的优秀基因会保留并演化出更
                        加优秀的基因，最终可能演化出全局最优或至少局部最优的基因。

                        关于遗传算法的详细参数和输出，参见self._search_ga()函数的docstring

                    5, Gradient Descendent Algorithm        梯度下降算法

                        梯度下降算法

                2，有监督方法类：这一类方法依赖于历史数据上的（有用的）先验信息：比如过去一个区间上的已知交易信号、或者价格变化信息。然后通过
                优化方法寻找历史数据和有用的先验信息之间的联系（目标联系）。这一类优化方法的假设是，如果这些通过历史数据直接获取先验信息的
                联系在未来仍然有效，那么我们就可能在未来同样根据这些联系，利用已知的数据推断出对我们有用的信息。
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
        Config.mode == 3 or mode == 3:
            进入评价模式（技术冻结后暂停开发此功能）
            评价模式的思想是使用随机生成的模拟历史数据对策略进行评价。由于可以使用大量随机历史数据序列进行评价，因此可以得到策略的统计学
            表现
    input：

        :param operator:
            :type Operator
            策略执行器对象

        :param **kwargs:
            可用的kwargs包括：


    return:
        1, 在signal模式或模式0下,返回: op_list
        2, 在back_test模式或模式1下, 返回: loop_result
        3, 在optimization模式或模式2下: 返回一个list，包含所有优化后的策略参数
    """
    import time
    # import pdb
    # pdb.set_trace()
    optimization_methods = {0: _search_grid,
                            1: _search_montecarlo,
                            2: _search_incremental,
                            3: _search_ga,
                            4: _search_gradient,
                            5: _search_particles
                            }
    # 如果函数调用时用户给出了关键字参数(**kwargs），则首先处理关键字参数，将所有的关键字参数赋值给QT_CONFIG变量，用于运行参数配置
    configure(**kwargs)
    config = QT_CONFIG

    # 赋值给参考数据和运行模式
    reference_data_type = config.reference_asset
    run_mode = config.mode
    """
    用于交易信号生成、数据回测、策略优化、结果测试以及结果评价参考的历史数据:
    hist_op:            信号生成数据，根据策略的运行方式，信号生成数据可能包含量价数据、基本面数据、指数、财务指标等等
    hist_loop:          回测价格数据，用于在backtest模式下对生成的信号进行测试，仅包含买卖价格数据（定价回测）
    hist_opti:          策略优化数据，数据的类型与信号生成数据一样，但是取自专门的独立区间用于策略的参数优化
    hist_opti_loop:     优化回测价格，用于在optimization模式下在策略优化区间上回测交易结果，目前这组数据并未提前生成，
                        而是在optimize的时候生成，实际上应该提前生成
    hist_test:          策略检验数据，数据的类型与信号生成数据一样，同样取自专门的独立区间用于策略参数的性能检测
    hist_test_loop:     检验回测价格，用于在optimization模式下在策略检验区间上回测交易结果
    hist_reference:     评价参考价格，用于评价回测结果，大部分用于评价回测结果的alpha表现（取出无风险回报之后的表现）
                        相关的指标都需要用到参考价格;
    invest_cash_plan:
    opti_cash_plan:
    test_cssh_plan:
    """
    # 统一生成回测、优化、测试所需要的信号生成数据、回测数据以及投资金额数据（投资金额数据已调整为交易日）
    (hist_op,
     hist_loop,
     hist_opti,
     hist_test,
     hist_test_loop,
     hist_reference,
     invest_cash_plan,
     opti_cash_plan,
     test_cash_plan) = check_and_prepare_hist_data(operator, config)

    if run_mode == 0 or run_mode == 'signal':
        # 进入实时信号生成模式：
        # 在生成交易信号之前分配历史数据，将正确的历史数据分配给不同的交易策略
        operator.prepare_data(hist_data=hist_op, cash_plan=invest_cash_plan)
        st = time.time()  # 记录交易信号生成耗时
        op_list = operator.create_signal(hist_data=hist_op)  # 生成交易清单
        et = time.time()
        run_time_prepare_data = (et - st)
        _print_operation_signal(op_list=op_list,
                                run_time_prepare_data=run_time_prepare_data,
                                operator=operator,
                                history_data=hist_op)
        return op_list

    elif run_mode == 1 or run_mode == 'back_test':
        # 进入回测模式

        operator.prepare_data(hist_data=hist_op, cash_plan=invest_cash_plan)  # 在生成交易信号之前准备历史数据

        # 生成交易清单，对交易清单进行回测，对回测的结果进行基本评价
        loop_result = _evaluate_one_parameter(par=None,
                                              op=operator,
                                              op_history_data=hist_op,
                                              loop_history_data=hist_loop,
                                              reference_history_data=hist_reference,
                                              reference_history_data_type=reference_data_type,
                                              config=config,
                                              stage='loop')
        if config.visual:
            # 图表输出投资回报历史曲线
            _plot_loop_result(loop_result, config)
        else:
            # 格式化输出回测结果
            _print_loop_result(loop_result, config)

        return loop_result

    elif run_mode == 2 or run_mode == 'optimization':
        how = config.opti_method
        assert operator.opt_space_par[0] == [], \
            f'ConfigError, none of the strategy parameters is adjustable, set opt_tag to be 1 or 2 to ' \
            f'activate optimization in mode 2, and make sure strategy has adjustable parameters'
        operator.prepare_data(hist_data=hist_opti, cash_plan=opti_cash_plan)  # 在生成交易信号之前准备历史数据
        # 使用how确定优化方法并生成优化后的参数和性能数据
        pars, perfs = optimization_methods[how](hist=hist_opti,
                                                ref_hist=hist_reference,
                                                ref_type=reference_data_type,
                                                op=operator,
                                                config=config)
        # 输出策略优化的评价结果，该结果包含在result_pool的extra额外信息属性中
        hist_opti_loop = hist_opti.to_dataframe(htype='close').fillna(0)
        result_pool = _evaluate_all_parameters(par_generator=pars,
                                               total=config.opti_output_count,
                                               op=operator,
                                               op_history_data=hist_opti,
                                               loop_history_data=hist_opti_loop,
                                               reference_history_data=hist_reference,
                                               reference_history_data_type=reference_data_type,
                                               config=config,
                                               stage='test-o')
        # 评价回测结果——计算参考数据收益率以及平均年化收益率
        opti_eval_res = result_pool.extra
        if config.visual:
            pass
            # _plot_test_result(opti_eval_res, config=config)
        else:
            _print_test_result(opti_eval_res, config=config)

        # 完成策略参数的寻优，在测试数据集上检验寻优的结果
        operator.prepare_data(hist_data=hist_test, cash_plan=test_cash_plan)
        if config.test_type in ['single', 'multiple']:
            result_pool = _evaluate_all_parameters(par_generator=pars,
                                                   total=config.opti_output_count,
                                                   op=operator,
                                                   op_history_data=hist_test,
                                                   loop_history_data=hist_test_loop,
                                                   reference_history_data=hist_reference,
                                                   reference_history_data_type=reference_data_type,
                                                   config=config,
                                                   stage='test-t')

            # 评价回测结果——计算参考数据收益率以及平均年化收益率
            test_eval_res = result_pool.extra
            if config.visual:
                _plot_test_result(test_eval_res=test_eval_res, opti_eval_res=opti_eval_res, config=config)
            else:
                _print_test_result(test_eval_res, config)
        elif config.test_type == 'montecarlo':
            for i in range(config.test_cycle_count):
                # 临时生成用于测试的模拟数据，将模拟数据传送到operator中，使用operator中的新历史数据
                # 重新生成交易信号，并在模拟的历史数据上进行回测
                mock_hist = _create_mock_data(hist_test)
                operator.prepare_data(hist_data=mock_hist,
                                      cash_plan=CashPlan(config.test_cash_dates, config.test_cash_amounts))
                mock_hist_loop = mock_hist.to_dataframe(htype='close')
                result_pool = _evaluate_all_parameters(par_generator=pars,
                                                       total=config.opti_output_count,
                                                       op=operator,
                                                       op_history_data=mock_hist,
                                                       loop_history_data=mock_hist_loop,
                                                       reference_history_data=mock_hist_loop,
                                                       reference_history_data_type=reference_data_type,
                                                       config=config,
                                                       stage='test-t')

                # 评价回测结果——计算参考数据收益率以及平均年化收益率
                test_eval_res = result_pool.extra
                if config.visual:
                    pass
                else:
                    _print_test_result(test_eval_res, config)

        return pars


def _evaluate_all_parameters(par_generator,
                             total,
                             op: Operator,
                             op_history_data: HistoryPanel,
                             loop_history_data: pd.DataFrame,
                             reference_history_data,
                             reference_history_data_type,
                             config,
                             stage='optimize') -> ResultPool:
    """ 接受一个策略参数生成器对象，批量生成策略参数，反复调用_evaluate_one_parameter()函数，使用所有生成的策略参数
        生成历史区间上的交易策略和回测结果，将得到的回测结果全部放入一个结果池对象，并根据策略筛选方法筛选出符合要求的回测
        结果，并返回筛选后的结果。

        根据config中的配置参数，这里可以选择进行并行计算以充分利用多核处理器的全部算力以缩短运行时间。

    input:
        :param par_generator: Generator ->
            一个迭代器对象，生成所有需要迭代测试的策略参数

        :param op: qt.Operator ->
            一个operator对象，包含多个投资策略，用于根据交易策略以及策略的配置参数生成交易信号

        :param op_history_data:  qt.HistoryPanel ->
            用于生成operation List的历史数据。根据operator中的策略种类不同，需要的历史数据类型也不同，该组
            历史数据是一个HistoryPanel对象，包含适合于交易信号创建的所有投资品种所有相关数据类型的数据。如交易
            价格数据（如果策略通过交易价格生成交易信号）、财务报表数据（如果策略通过财务报表生成交易信号）等等

        :param loop_history_data: pd.DataFrame ->
            用于进行回测的历史数据，该数据历史区间与前面的数据相同，但是仅包含回测所需要的价格信息，通常为收盘价
            （假设交易价格为收盘价）

        :param reference_history_data: pd.DataFrame ->
            用于回测结果评价的参考历史数据，历史区间与回测历史数据相同，但是通常是能代表整个市场整体波动的金融资
            产的价格，例如沪深300指数的价格。

        :param reference_history_data_type: str ->
            用于回测结果评价的参考历史数据种类，通常为收盘价close

        :param config: Config ->
            参数配置对象，用于保存相关配置，在所有的参数配置中，其作用的有下面N种：
                1, config.opti_output_count:
                    优化结果数量
                2, config.parallel:
                    并行计算选项，True时进行多进程并行计算，False时进行单进程计算

        :param stage:
            :type stage: str
            该参数直接传递至_evaluate_one_parameter()函数中，其含义和作用参见其docstring
    :return:
        pool，一个Pool对象，包含经过筛选后的所有策略参数以及它们的性能表现

    """
    pool = ResultPool(config.opti_output_count)  # 用于存储中间结果或最终结果的参数池对象
    i = 0
    best_so_far = 0
    opti_target = config.optimize_target
    # 启用多进程计算方式利用所有的CPU核心计算
    if config.parallel:
        # 启用并行计算
        proc_pool = ProcessPoolExecutor()
        futures = {proc_pool.submit(_evaluate_one_parameter,
                                    par,
                                    op,
                                    op_history_data,
                                    loop_history_data,
                                    reference_history_data,
                                    reference_history_data_type,
                                    config,
                                    stage): par for par in
                   par_generator}
        for f in as_completed(futures):
            eval_dict = f.result()
            target_value = eval_dict[opti_target]
            pool.in_pool(item=futures[f], perf=target_value, extra=eval_dict)
            i += 1
            if target_value > best_so_far:
                best_so_far = target_value
            if i % 10 == 0:
                progress_bar(i, total, comments=f'best performance: {best_so_far:.3f}')
    # 禁用多进程计算方式，使用单进程计算
    else:
        for par in par_generator:
            perf = _evaluate_one_parameter(par=par,
                                           op=op,
                                           op_history_data=op_history_data,
                                           loop_history_data=loop_history_data,
                                           reference_history_data=reference_history_data,
                                           reference_history_data_type=reference_history_data_type,
                                           config=config,
                                           stage=stage)
            target_value = perf[opti_target]
            pool.in_pool(item=par, perf=target_value, extra=perf)
            i += 1
            if target_value > best_so_far:
                best_so_far = target_value
            if i % 10 == 0:
                progress_bar(i, total, comments=f'best performance: {best_so_far:.3f}')
    # 将当前参数以及评价结果成对压入参数池中，并返回所有成对参数和评价结果
    progress_bar(i, i)

    return pool


def _evaluate_one_parameter(par: tuple,
                            op: Operator,
                            op_history_data: HistoryPanel,
                            loop_history_data: [pd.DataFrame, pd.Series],
                            reference_history_data,
                            reference_history_data_type,
                            config,
                            stage='optimize') -> dict:
    """ 基于op中的交易策略，在给定策略参数par的条件下，计算交易策略在一段历史数据上的交易信号，并对交易信号的交易
        结果进行回测，对回测结果数据进行评价，并给出评价结果。
        本函数是一个方便的包裹函数，包裹了交易信号生成、交易信号回测以及回测结果评价结果的打包过程，同时，根据QT基
        本配置的不同，可以在交易信号回测的过程中进行多重回测，即将一段历史区间分成几个子区间，在每一个子区间上分别
        回测后返回多次回测的综合结果。

    input:
        :param par: tuple
            输入的策略参数组合，这些参数必须与operator运行器对象中的交易策略相匹配，且符合op对象中每个交易策
            略的优化标记设置，关于交易策略的优化标记如何影响参数导入，参见qt.operator.set_opt_par()的
            docstring

        :param op: qt.Operator
            一个operator对象，包含多个投资策略，用于根据交易策略以及策略的配置参数生成交易信号

        :param op_history_data: qt.HistoryPanel
            用于生成operation List的历史数据。根据operator中的策略种类不同，需要的历史数据类型也不同，该组
            历史数据是一个HistoryPanel对象，包含适合于交易信号创建的所有投资品种所有相关数据类型的数据。如交易
            价格数据（如果策略通过交易价格生成交易信号）、财务报表数据（如果策略通过财务报表生成交易信号）等等

        :param loop_history_data: pd.DataFrame
            用于进行回测的历史数据，该数据历史区间与前面的数据相同，但是仅包含回测所需要的价格信息，通常为收盘价
            （假设交易价格为收盘价）

        :param reference_history_data: pd.DataFrame
            用于回测结果评价的参考历史数据，历史区间与回测历史数据相同，但是通常是能代表整个市场整体波动的金融资
            产的价格，例如沪深300指数的价格。

        :param reference_history_data_type: str
            用于回测结果评价的参考历史数据种类，通常为收盘价close

        :param config: Config:
            参数配置对象，用于保存相关配置，在所有的参数配置中，其作用的有下面N种：
                1, config.opti_type/test_type:
                    优化或测试模式，决定如何利用回测区间
                    single:     在整个回测区间上进行一次回测
                    multiple:   将回测区间分割为多个子区间并分别回测
                    montecarlo: 根据回测区间的数据生成模拟数据进行回测（仅在test模式下）
                2, config.optimize_target/test_indicators:
                    优化目标函数（优化模式下）或评价指标（测试模式下）
                    在优化模式下，使用特定的优化目标函数来确定表现最好的策略参数
                    在测试模式下，对策略的回测结果进行多重评价并输出评价结果
                3, config.opti_cash_amounts/test_cash_amounts:
                    优化/测试投资金额
                    在多区间回测情况下，投资金额会被调整，初始投资日期会等于每一个回测子区间的第一天
                4, config.opti_sub_periods/test_sub_periods:
                    优化/测试区间数量
                    在多区间回测情况下，在整个回测区间中间隔均匀地取出多个区间，在每个区间上分别回测
                    每个区间的长度相同，但是起止点不同。每个起点之间的间隔与子区间的长度和数量同时相关，
                    确保每个区间的起点是均匀分布的，同时所有的子区间正好覆盖整个回测区间。
                5, config.opti_sub_prd_length/test_sub_prd_length:
                    优化/测试子区间长度
                    该数值是一个相对长度，取值在0～1之间，代表每个子区间的长度相对于整个区间的比例，
                    例如，0.5代表每个子区间的长度是整个区间的一半

        :param stage: str:
            运行标记，代表不同的运行阶段控制运行过程的不同处理方式，包含三种不同的选项
                1, 'loop':      运行模式为回测模式，在这种模式下：
                                使用投资区间回测投资计划
                                使用config.print_backtest_log来确定是否打印回测结果
                2, 'optimize':  运行模式为优化模式，在这种模式下：
                                使用优化区间回测投资计划
                                回测区间利用方式使用opti_type的设置值
                                回测区间分段数量和间隔使用opti_sub_periods
                3, 'test-o':    运行模式为测试模式-opti区间，以便在opti区间上进行一次与test区间完全相同的测试以比较结果
                                使用优化区间回测投资计划
                                回测区间利用方式使用test_type的设置值
                                回测区间分段数量和间隔使用test_sub_periods
                4, 'test-t':    运行模式为测试模式-test区间
                                使用测试区间回测投资计划
                                回测区间利用方式使用test_type的设置值
                                回测区间分段数量和间隔使用test_sub_periods
    :return:
        dict:
        一个dict对象，存储该策略在使用par作为参数时的性能表现评分以及一些其他运行信息，允许对性能
        表现进行多重指标评价，dict的指标类型为dict的键，评价结果为结果分值，dict不能为空，至少包含以下值：
            'complete_value': 完整的回测结果清单，无结果时为None
            'op_run_time':    交易清单生成耗时
            'loop_run_time':  回测耗时
            'final_value':    回测结果终值（默认评价指标）
        除了上述必须存在的项目以外，返回的res_dict还可以包含任意evaluation模块可以输出的评价值，例如：
            {'final_value': 34567,
             'sharp':       0.123}
        如果当前的策略不能生成有效的交易操作清单时，直接返回默认结果，其终值为负无穷大：
            {'complete_values':  None,
             'op_run_time':     0.0354675,
             'loop_run_time':   None,
             'final_value':     np.NINF}

    """
    res_dict = {'par':             None,
                'complete_values': None,
                'op_run_time':     0,
                'loop_run_time':   0,
                'final_value':     None}

    assert stage in ['loop', 'optimize', 'test-o', 'test-t']
    if par is not None:  # 如果给出了策略参数，则更新策略参数，否则沿用原有的策略参数
        op.set_opt_par(par)
        res_dict['par'] = par
    # 生成交易清单并进行模拟交易生成交易记录
    st = time.time()
    op_list = op.create_signal(op_history_data)
    et = time.time()
    op_run_time = et - st
    res_dict['op_run_time'] = op_run_time
    riskfree_ir = config.riskfree_ir
    if op_list.empty:  # 如果策略无法产生有意义的操作清单，则直接返回基本信息
        res_dict['final_value'] = np.NINF
        return res_dict
    # 根据stage的值选择使用投资金额种类以及运行类型（单区间运行或多区间运行）及区间参数及回测参数
    if stage == 'loop':
        invest_cash_amounts = config.invest_cash_amounts
        invest_cash_dates = pd.to_datetime(config.invest_start) if \
            config.invest_cash_dates is None \
            else pd.to_datetime(config.invest_cash_dates)
        period_util_type = 'single'
        indicators = 'years,fv,return,mdd,v,ref,alpha,beta,sharp,info'
        print_backtest_log = config.print_backtest_log  # 回测参数print_backtest_log只有在回测模式下才有用
    elif stage == 'optimize':
        invest_cash_amounts = config.opti_cash_amounts[0]
        # TODO: only works when config.opti_cash_dates is a string, if it is a list, it will not work
        invest_cash_dates = pd.to_datetime(config.opti_start) if \
            config.opti_cash_dates is None \
            else pd.to_datetime(config.opti_cash_dates)
        period_util_type = config.opti_type
        period_count = config.opti_sub_periods
        period_length = config.opti_sub_prd_length
        indicators = config.optimize_target
        print_backtest_log = False
    elif stage == 'test-o':
        invest_cash_amounts = config.test_cash_amounts[0]
        # TODO: only works when config.opti_cash_dates is a string, if it is a list, it will not work
        invest_cash_dates = pd.to_datetime(config.opti_start) if \
            config.opti_cash_dates is None \
            else pd.to_datetime(config.opti_cash_dates)
        period_util_type = config.test_type
        period_count = config.test_sub_periods
        period_length = config.test_sub_prd_length
        indicators = config.test_indicators
        print_backtest_log = False
    else:  # stage == 'test-t':
        invest_cash_amounts = config.test_cash_amounts[0]
        # TODO: only works when config.opti_cash_dates is a string, if it is a list, it will not work
        invest_cash_dates = pd.to_datetime(config.test_start) if \
            config.test_cash_dates is None \
            else pd.to_datetime(config.test_cash_dates)
        period_util_type = config.test_type
        period_count = config.test_sub_periods
        period_length = config.test_sub_prd_length
        indicators = config.test_indicators
        print_backtest_log = False
    # create list of start and end dates
    # in this case, user-defined invest_cash_dates will be disabled, each start dates will be
    # used as the investment date for each sub-periods
    invest_cash_dates = next_market_trade_day(invest_cash_dates)
    start_dates = []
    end_dates = []
    if period_util_type == 'single' or period_util_type == 'montecarlo':
        start_dates.append(invest_cash_dates)
        # start_dates.append(loop_history_data.index[0])
        end_dates.append(loop_history_data.index[-1])
    elif period_util_type == 'multiple':
        first_history_date = invest_cash_dates
        # first_history_date = loop_history_data.index[0]
        last_history_date = loop_history_data.index[-1]
        history_range = last_history_date - first_history_date
        sub_hist_range = history_range * period_length
        sub_hist_interval = (1 - period_length) * history_range / period_count
        for i in range(period_count):
            start_date = first_history_date + i * sub_hist_interval
            start_dates.append(start_date)
            end_dates.append(start_date + sub_hist_range)
    else:
        raise KeyError(f'Not recognized optimization type: {config.opti_type}')
    # loop over all pairs of start and end dates, get the results separately and output average
    perf_list = []
    st = time.time()
    for start, end in zip(start_dates, end_dates):
        op_list_seg = op_list[start:end].copy()
        history_list_seg = loop_history_data[start:end].copy()
        if stage != 'loop':
            invest_cash_dates = history_list_seg.index[0]
        cash_plan = CashPlan(invest_cash_dates.strftime('%Y%m%d'),
                             invest_cash_amounts,
                             riskfree_ir)
        trade_cost = Cost(config.cost_fixed_buy,
                          config.cost_fixed_sell,
                          config.cost_rate_buy,
                          config.cost_rate_sell,
                          config.cost_min_buy,
                          config.cost_min_sell,
                          config.cost_slippage)
        looped_val = apply_loop(op_list=op_list_seg,
                                history_list=history_list_seg,
                                cash_plan=cash_plan,
                                cost_rate=trade_cost,
                                moq_buy=config.trade_batch_size,
                                moq_sell=config.sell_batch_size,
                                print_log=print_backtest_log)
        complete_values = _get_complete_hist(looped_value=looped_val,
                                             h_list=history_list_seg,
                                             ref_list=reference_history_data,
                                             with_price=False)
        perf = evaluate(op_list=op_list_seg,
                        looped_values=complete_values,
                        hist_reference=reference_history_data,
                        reference_data=reference_history_data_type,
                        cash_plan=cash_plan,
                        indicators=indicators)
        perf_list.append(perf)
    perf = performance_statistics(perf_list)
    et = time.time()
    loop_run_time = et - st
    res_dict.update(perf)
    res_dict['loop_run_time'] = loop_run_time
    return res_dict


# TODO: 这个函数有潜在大量运行的可能，需要使用Numba加速
def _create_mock_data(history_data: HistoryPanel) -> HistoryPanel:
    """ 根据输入的历史数据的统计特征，随机生成多组具备同样统计特征的随机序列，用于进行策略收益的蒙特卡洛模拟

        目前仅支持OHLC数据以及VOLUME数据的随机生成，其余种类的数据需要继续研究
        为了确保生成的数据留有足够的前置数据窗口，生成的伪数据包含两段，第一段长度与最大前置窗口长度相同，这一段
        为真实历史数据，第二段才是随机生成的模拟数据
        同时，生成的数据仍然满足OHLC的关系，同时所有的数据在统计上与参考数据是一致的，也就是说，随机生成的数据
        不仅仅满足K线图的形态要求，其各个参数的均值、标准差与参考数据一致。

    :param history_data:
        :type history_data: HistoryPanel
        模拟数据的参考源

    :return:
        HistoryPanel
    """

    assert isinstance(history_data, HistoryPanel)
    data_types = history_data.htypes
    # volume数据的生成还需要继续研究
    assert any(data_type in ['close', 'open', 'high', 'low', 'volume'] for data_type in data_types), \
        f'the data type {data_types} does not fit'
    has_volume = any(data_type in ['volume'] for data_type in data_types)
    # 按照细粒度方法同时生成OHLC数据
    # 针对每一个share生成OHLC数据
    # 先考虑生成正确的信息，以后再考虑优化
    dfs_for_share = []
    for share in history_data.shares:
        share_df = history_data.to_dataframe(share=share)
        share_df['close_chg'] = share_df.close / share_df.close.shift(1)
        mean = share_df.close_chg.mean()
        std = share_df.close_chg.std()
        mock_col = np.random.randn(len(history_data.hdates) * 5) * std * 5 + mean
        mock_col = 1 + 0.09 * (mock_col - 1)
        mock_col[0] = share_df.close.iloc[0]
        mock_col = np.cumprod(mock_col)
        mock = mock_col.reshape(len(history_data.hdates), 5)
        mock_df = pd.DataFrame(index=history_data.hdates)
        mock_df['open'] = mock[:, 0]
        mock_df['high'] = np.max(mock, axis=1)
        mock_df['low'] = np.min(mock, axis=1)
        mock_df['close'] = mock[:, 4]
        if has_volume:
            mock_df['volume'] = share_df.volume
        dfs_for_share.append(mock_df.copy())

    # 生成一个HistoryPanel对象，每一层一个个股
    mock_data = stack_dataframes(dfs_for_share,
                                 stack_along='shares',
                                 shares=history_data.shares)
    return mock_data


def _search_grid(hist, ref_hist, ref_type, op, config):
    """ 最优参数搜索算法1: 网格搜索法

        在整个参数空间中建立一张间距固定的"网格"，搜索网格的所有交点所在的空间点，
        根据该点的参数生成操作信号、回测后寻找表现最佳的一组或多组参数
        与该算法相关的设置选项有：
            grid_size:  网格大小，float/int/list/tuple 当参数为数字时，生成空间所有方向
                        上都均匀分布的网格；当参数为list或tuple时，可以在空间的不同方向
                        上生成不同间隔大小的网格。list或tuple的维度须与空间的维度一致

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param config, object, 用于存储优化参数的上下文对象
    return: =====tuple对象，包含两个变量
        items 作为结果输出的参数组
        perfs 输出的参数组的评价分数
    """
    s_range, s_type = op.opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间

    # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
    par_generator, total = space.extract(config.opti_grid_size)
    history_list = hist.to_dataframe(htype='close').fillna(0)
    st = time.time()
    pool = _evaluate_all_parameters(par_generator=par_generator,
                                    total=total,
                                    op=op,
                                    op_history_data=hist,
                                    loop_history_data=history_list,
                                    reference_history_data=ref_hist,
                                    reference_history_data_type=ref_type,
                                    config=config,
                                    stage='optimize')
    pool.cut(config.maximize_target)
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st)}')
    return pool.items, pool.perfs


def _search_montecarlo(hist, ref_hist, ref_type, op, config):
    """ 最优参数搜索算法2: 蒙特卡洛法

        从待搜索空间中随机抽取大量的均匀分布的参数点并逐个测试，寻找评价函数值最优的多个参数组合
        与该算法相关的设置选项有：
            sample_size:采样点数量，int 由于采样点的分布是随机的，因此采样点越多，越有可能
                        接近全局最优值

    input:
        :param hist: object，历史数据，优化器的整个优化过程在历史数据上完成
        :param ref_hist:
        :param ref_type:
        :param op: object，交易信号生成器对象
        :param config: object 用于存储相关参数的上下文对象
    return: =====tuple对象，包含两个变量
        pool.items 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
"""
    # s_range, s_type = op.opt_space_par
    space = Space(*op.opt_space_par)  # 生成参数空间
    # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与网格法一致
    par_generator, total = space.extract(config.opti_sample_count, how='rand')
    history_list = hist.to_dataframe(htype='close').fillna(0)
    st = time.time()
    pool = _evaluate_all_parameters(par_generator=par_generator,
                                    total=total,
                                    op=op,
                                    op_history_data=hist,
                                    loop_history_data=history_list,
                                    reference_history_data=ref_hist,
                                    reference_history_data_type=ref_type,
                                    config=config,
                                    stage='optimize')
    pool.cut(config.maximize_target)
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st, short_form=True)}')
    return pool.items, pool.perfs


def _search_incremental(hist, ref_hist, ref_type, op, config):
    """ 最优参数搜索算法3: 增量递进搜索法

        该算法是蒙特卡洛算法的一种改进。整个算法运行多轮蒙特卡洛算法，但是每一轮搜索的空间大小都更小，
        而且每一轮搜索都（大概率）更接近全局最优解。
        该算法的第一轮搜索就是标准的蒙特卡洛算法，在整个参数空间中随机取出一定数量的参数组合，使用这
        些参数分别进行信号回测。第一轮搜索结束后，在第一轮的全部结果中择优选出一定比例的最佳参数，以
        这些最佳参数为中心点，构建一批子空间，这些子空间的总体积比起最初的参数空间小的多，但是大概率
        容纳了最初参数空间的全局最优解。
        接着，程序继续在新生成的子空间中取出同样多的参数组合，并同样选出最佳参数组合，以新的最优解为
        中心创建下一轮的参数空间，其总体积再次缩小。
        如上所诉反复运行程序，每一轮需要搜索的子空间的体积越来越小，找到全局最优的概率也越来越大，直到
        参数空间的体积小于一个固定值，或者循环的次数超过最大次数，循环停止，输出当前轮的最佳参数组合。

        与该算法相关的设置选项有：
            r_sample_size:      采样点数量，int 每一轮搜索中采样点的数量
            reduce_ratio:       择优比例，float, 大于零小于1的浮点数，次轮搜索参数空间大小与本轮
                                空间大小的比例，同时也是参数组的择优比例，例如0。2代表每次搜索的
                                参数中最佳的20%会被用于创建下一轮的子空间邻域，同时下一轮的子空间
                                体积为本轮空间体积的20%
            max_rounds:         最大轮数，int，循环次数达到该值时结束循环
            min_volume:         最小体积，float，当参数空间的体积（Volume）小于该值时停止循环

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param config, object, 用于存储交易相关参数的上下文对象
    return: =====tuple对象，包含两个变量
        pool.items 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

"""
    sample_count = config.opti_r_sample_count
    min_volume = config.opti_min_volume
    max_rounds = config.opti_max_rounds
    reduce_ratio = config.opti_reduce_ratio
    parallel = config.parallel
    s_range, s_type = op.opt_space_par
    spaces = list()  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
    base_space = Space(s_range, s_type)
    base_volume = base_space.volume
    base_dimension = base_space.dim
    # 每一轮参数寻优后需要保留的参数组的数量
    reduced_sample_count = int(sample_count * reduce_ratio)
    pool = ResultPool(reduced_sample_count)  # 用于存储中间结果或最终结果的参数池对象

    spaces.append(base_space)  # 将整个空间作为第一个子空间对象存储起来
    space_count_in_round = 1  # 本轮运行子空间的数量
    current_round = 1  # 当前运行轮次
    current_volume = base_space.volume  # 当前运行轮次子空间的总体积
    history_list = hist.to_dataframe(htype='close').fillna(0)  # 准备历史数据
    """
    估算运行的总回合数量，由于每一轮运行的回合数都是大致固定的（随着空间大小取整会有波动）
    因此总的运行回合数就等于轮数乘以每一轮的回合数。关键是计算轮数
    由于轮数的多少取决于两个变量，一个是最大轮次数，另一个是下一轮产生的子空间总和体积是否
    小于最小体积阈值，因此，推算过程如下：
    设初始空间体积为Vi，最小空间体积为Vmin，每一轮的缩小率为rr，最大计算轮数为Rmax
    且第k轮的空间体积为Vk，则有：
                          Vk = Vi * rr ** k
          停止条件1：      Vk = Vi * rr ** k < Vmin
          停止条件2:      k >= Rmax
       根据停止条件1：    rr ** k < Vmin / Vi
                       k > log(Vmin / Vi) / log(rr)
           因此，当：    k > min(Rmax, log(Vmin / Vi) / log(rr))
    """
    round_count = min(max_rounds, (math.log(min_volume / base_volume) / math.log(reduce_ratio)))
    total_calc_rounds = int(round_count * sample_count)
    i = 0
    st = time.time()
    # 从当前space开始搜索，当subspace的体积小于min_volume或循环次数达到max_rounds时停止循环
    while current_volume >= min_volume and current_round < max_rounds:
        # 在每一轮循环中，spaces列表存储该轮所有的空间或子空间
        while spaces:
            space = spaces.pop()
            # 逐个弹出子空间列表中的子空间，随机选择参数，生成参数生成器generator
            # 生成的所有参数及评价结果压入pool结果池，每一轮所有空间遍历完成后再排序择优
            par_generator, total = space.extract(sample_count // space_count_in_round, how='rand')
            # TODO: progress bar does not work properly, try to find a way to get progress bar working
            pool = pool + _evaluate_all_parameters(par_generator=par_generator,
                                                   total=total,
                                                   op=op,
                                                   op_history_data=hist,
                                                   loop_history_data=history_list,
                                                   reference_history_data=ref_hist,
                                                   reference_history_data_type=ref_type,
                                                   config=config,
                                                   stage='optimize')
        # 本轮所有结果都进入结果池，根据择优方向选择最优结果保留，剪除其余结果
        pool.cut(config.maximize_target)
        """
        为了生成新的子空间，计算下一轮子空间的半径大小
        为确保下一轮的子空间总体积与本轮子空间总体积的比值是reduce_ratio，需要根据空间的体积公式设置正确
        的缩小比例。这个比例与空间的维数和子空间的数量有关
        例如：
        若 reduce_ratio(rr)=0.5，设初始空间体积为Vi,边长为Si，第k轮空间体积为Vk，子空间数量为m，
              每个子空间的体积为V，Size为S，空间的维数为d,则有：
              Si ** d * (rr ** k) = Vi * (rr ** k) = Vk =  V * m = S ** d * m
              于是：
              S ** d * m = Si ** d * (rr ** k)
              (S/Si) ** d = (rr ** k) / m
              S/Si = ((rr ** k) / m) ** (1/d)
        根据上述结果，第k轮的子空间直径S可以由原始空间的半径Si得到：
              S = Si * ((rr ** k) / m) ** (1/d)
              distance = S / 2
        """
        size_reduce_ratio = ((reduce_ratio ** current_round) / reduced_sample_count) ** (1 / base_dimension)
        reduced_size = tuple(np.array(base_space.size) * size_reduce_ratio / 2)
        # 完成一轮搜索后，检查pool中留存的所有点，并生成由所有点的邻域组成的子空间集合
        current_volume = 0
        for point in pool.items:
            subspace = base_space.from_point(point=point, distance=reduced_size)
            spaces.append(subspace)
            current_volume += subspace.volume
        current_round += 1
        space_count_in_round = len(spaces)
        progress_bar(i, total_calc_rounds, f'start next round with {space_count_in_round} spaces')
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st)}')
    return pool.items, pool.perfs


def _search_ga(hist, ref_hist, ref_type, op, config):
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
        :param hist
            :type hist: object，历史数据，优化器的整个优化过程在历史数据上完成

        :param ref_hist
            :type ref_hist:

        :param ref_type
            :type ref_type:

        :param op
            :type op: object，交易信号生成器对象

        :param config
            :type config: ConfigDict

    return: =====tuple对象，包含两个变量
        pool.items 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

    """
    raise NotImplementedError


def _search_gradient(hist, ref_hist, ref_type, op, config):
    """ 最优参数搜索算法5：梯度下降法
    在参数空间中寻找优化结果变优最快的方向，始终保持向最优方向前进（采用自适应步长）一直到结果不再改变或达到
    最大步数为止，输出结果为最后N步的结果

    :input
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param ref_hist:
        :param ref_type:
        :param op，object，交易信号生成器对象
        :param config, object, 用于存储交易相关参数配置对象
    :return:
    """
    raise NotImplementedError


def _search_particles(hist, ref_hist, ref_type, op, config):
    """ 粒子群算法，与梯度下降相似，不过同时有N个粒子同时向山坡下滚动，输出结果为所有N个球的最后一步结果

    :input
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param ref_hist:
        :param ref_type:
        :param op，object，交易信号生成器对象
        :param config, object, 用于存储交易相关参数配置对象
    :return:
    """