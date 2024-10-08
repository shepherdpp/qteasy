# coding=utf-8
# ======================================
# File:     backtest.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-03-12
# Desc:
#   Functions used for backtesting and
# evaluation of trade results
# ======================================

import os
import pandas as pd
import numpy as np
from numba import njit  # try taichi, which might be even faster

import qteasy
from qteasy.history import HistoryPanel
from qteasy.qt_operator import Operator

from qteasy.finance import (
    CashPlan,
    get_selling_result,
    get_purchase_result,
    get_cost_pamams,
)


@njit(nogil=True, cache=True)
def _loop_step(signal_type: int,
               own_cash: float,
               own_amounts: np.ndarray,
               available_cash: float,
               available_amounts: np.ndarray,
               op: np.ndarray,
               prices: np.ndarray,
               cost_params: np.ndarray,
               pt_buy_threshold: float,
               pt_sell_threshold: float,
               maximize_cash_usage: bool,
               long_pos_limit: float,
               short_pos_limit: float,
               allow_sell_short: bool,
               moq_buy: float,
               moq_sell: float) -> tuple:
    """ 对同一批交易进行处理，采用向量化计算以提升效率
        接受交易信号、交易价格以及期初可用现金和可用股票等输入，加上交易费率等信息计算交易后
        的现金和股票变动值、并计算交易费用

    Parameters
    ----------
    signal_type: int
        信号类型:
            0 - PT signal
            1 - PS signal
            2 - VS signal
    own_cash: float
        本次交易开始前持有的现金余额（包括交割中的现金）
    own_amounts: np.ndarray
        本次交易开始前持有的资产份额（包括交割中的资产份额）
    available_cash: np.ndarray
        本次交易开始前账户可用现金余额（交割中的现金不计入余额）
    available_amounts: np.ndarray:
        交易开始前各个股票的可用数量余额（交割中的股票不计入余额）
    op: np.ndarray
        本次交易的个股交易信号清单
    prices: np.ndarray，
        本次交易发生时各个股票的交易价格
    cost_params: np.ndarray
        交易成本参数，包括固定买入费用、固定卖出费用、买入费率、卖出费率、最低买入费用、最低卖出费用
        buy_fix: float, 交易成本：固定买入费用
        sell_fix: float, 交易成本：固定卖出费用
        buy_rate: float, 交易成本：固定买入费率
        sell_rate: float, 交易成本：固定卖出费率
        buy_min: float, 交易成本：最低买入费用
        sell_min: float, 交易成本：最低卖出费用
        slipage: float, 交易成本：滑点
    pt_buy_threshold: object Cost
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    pt_sell_threshold: object Cost
        当交易信号类型为PT时，用于计算买入/卖出信号的强度阈值
    maximize_cash_usage: object Cost
        True:   先卖后买模式
        False:  先买后卖模式
    long_pos_limit: float
        允许建立的多头总仓位与净资产的比值，默认值1.0，表示最多允许建立100%多头仓位
    short_pos_limit: float
        允许建立的空头总仓位与净资产的比值，默认值-1.0，表示最多允许建立100%空头仓位
    allow_sell_short: bool
        True:   允许买空卖空
        False:  默认值，只允许买入多头仓位
    moq_buy: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍
    moq_sell: float:
        投资产品最小买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

    Returns
    -------
    tuple: (cash_gained, cash_spent, amounts_purchased, amounts_sold, fee)
        cash_gained:        float, 本批次交易中获得的现金增加额
        cash_spent:         float, 本批次交易中共花费的现金总额
        amounts_purchased:  ndarray, 交易后每个个股账户中的股份增加数量
        amounts_sold:       ndarray, 交易后每个个股账户中的股份减少数量
        fee:                float, 本次交易总费用，包括卖出的费用和买入的费用
    """

    # 0, 当本期交易信号全为0，且信号类型为1或2时，退出计算，因为此时
    # 的买卖行为仅受交易信号控制，交易信号全为零代表不交易，但是如果交
    # 易信号为0时，代表持仓目标为0，此时有可能会有卖出交易，因此不能退
    # 出计算
    # if np.all(op == 0) and (signal_type > 0):
    #     # 返回0代表获得和花费的现金，返回全0向量代表买入和卖出的股票
    #     # 因为正好op全为0，因此返回op即可
    #     return np.zeros_like(op), np.zeros_like(op), np.zeros_like(op), np.zeros_like(op), np.zeros_like(op)

    # 1,计算期初资产总额：交易前现金及股票余额在当前价格下的资产总额
    pre_values = own_amounts * prices
    total_value = own_cash + pre_values.sum()

    # 2,制定交易计划，生成计划买入金额和计划卖出数量
    if signal_type == 0:
        # signal_type 为PT，比较当前持仓与计划持仓的差额，再生成买卖数量
        ptbt = pt_buy_threshold
        ptst = -pt_sell_threshold
        # 计算当前持仓与目标持仓之间的差额
        pre_position = pre_values / total_value
        position_diff = op - pre_position
        # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
        # 当持有份额大于零时，平多仓：卖出数量 = 仓位差 * 持仓份额，此时持仓份额需大于零
        amounts_to_sell = np.where((position_diff < ptst) & (own_amounts > 0),
                                   position_diff / pre_position * own_amounts,
                                   0.)
        # 当持有份额不小于0时，开多仓：买入金额 = 仓位差 * 当前总资产，此时不能持有空头头寸
        cash_to_spend = np.where((position_diff > ptbt) & (own_amounts >= 0),
                                 position_diff * total_value,
                                 0.)
        # 当允许买空卖空时，允许开启空头头寸：
        if allow_sell_short:

            # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 仓位差 * 当前总资产，此时持有份额为0
            cash_to_spend += np.where((position_diff < ptst) & (own_amounts <= 0),
                                      position_diff * total_value,
                                      0.)
            # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 仓位差 * 当前持有空头份额
            amounts_to_sell += np.where((position_diff > ptbt) & (own_amounts < 0),
                                        position_diff / pre_position * own_amounts,
                                        0.)

    elif signal_type == 1:
        # signal_type 为PS，根据目前的持仓比例和期初资产总额生成买卖数量
        # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
        # 当持有份额大于零时，平多仓：卖出数量 =交易信号 * 持仓份额，此时持仓份额需大于零
        amounts_to_sell = np.where((op < 0) & (own_amounts > 0), op * own_amounts, 0.)
        # 当持有份额不小于0时，开多仓：买入金额 =交易信号 * 当前总资产，此时不能持有空头头寸
        cash_to_spend = np.where((op > 0) & (own_amounts >= 0), op * total_value, 0.)

        # 当允许买空卖空时，允许开启空头头寸：
        if allow_sell_short:

            # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 交易信号 * 当前总资产
            cash_to_spend += np.where((op < 0) & (own_amounts <= 0), op * total_value, 0.)
            # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 交易信号 * 当前持有空头份额
            amounts_to_sell -= np.where((op > 0) & (own_amounts < 0), op * own_amounts, 0.)

    elif signal_type == 2:
        # signal_type 为VS，交易信号就是计划交易的股票数量，符号代表交易方向
        # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
        # 当持有份额大于零时，卖出多仓：卖出数量 = 信号数量，此时持仓份额需大于零
        amounts_to_sell = np.where((op < 0) & (own_amounts > 0), op, 0.)
        # 当持有份额不小于0时，买入多仓：买入金额 = 信号数量 * 资产价格，此时不能持有空头头寸，必须为空仓或多仓
        cash_to_spend = np.where((op > 0) & (own_amounts >= 0), op * prices, 0.)

        # 当允许买空卖空时，允许开启空头头寸：
        if allow_sell_short:
            # 当持有份额小于等于零且交易信号为负，买入空仓：买入空头金额 = 信号数量 * 资产价格
            cash_to_spend += np.where((op < 0) & (own_amounts <= 0), op * prices, 0.)
            # 当持有份额小于0（即持有空头头寸）且交易信号为正时，卖出空仓：卖出空头数量 = 交易信号 * 当前持有空头份额
            amounts_to_sell -= np.where((op > 0) & (own_amounts < 0), -op, 0.)

    else:
        raise ValueError('Invalid signal_type')

    # 3, 批量提交股份卖出计划，计算实际卖出份额与交易费用。

    # 如果不允许卖空交易，则需要更新股票卖出计划数量
    if not allow_sell_short:
        amounts_to_sell = - np.fmin(-amounts_to_sell, available_amounts)
    amount_sold, cash_gained, fee_selling = get_selling_result(
            prices=prices,
            a_to_sell=amounts_to_sell,
            moq=moq_sell,
            cost_params=cost_params,
    )

    if maximize_cash_usage:
        # 仅当现金交割期为0，且希望最大化利用同批交易产生的现金时，才调整现金余额
        # 现金余额 = 期初现金余额 + 本次出售资产获得现金总额
        available_cash += cash_gained.sum()

    # 调整处理cash_to_spend
    # 初步估算按照交易清单买入资产所需要的现金，如果超过持有现金，则按比例降低买入金额
    abs_cash_to_spend = np.abs(cash_to_spend)

    if np.all(abs_cash_to_spend < 0.01):
        # 如果所有买入计划绝对值都小于1分钱，则直接跳过后续的计算
        return cash_gained, np.zeros_like(op), np.zeros_like(op), amount_sold, fee_selling

    # 分别处理买入金额中的多头买入和空头买入部分，分别计算当前持有的多头和空头仓位
    pos_cash_to_spend = np.where(cash_to_spend > 0.01, cash_to_spend, 0)
    total_pos_cash_to_spend = pos_cash_to_spend.sum()
    neg_cash_to_spend = np.where(cash_to_spend < -0.01, cash_to_spend, 0)
    total_neg_cash_to_spend = neg_cash_to_spend.sum()
    next_own_amounts = own_amounts + amount_sold

    # 计算允许用于买入多头份额的最大金额
    current_long_pos = np.where(next_own_amounts > 0, next_own_amounts * prices, 0).sum() / total_value
    max_pos_cash_to_spend = (long_pos_limit - current_long_pos) * total_value

    if long_pos_limit <= 1.0:
        max_pos_cash_to_spend = min(max_pos_cash_to_spend, available_cash)

    if total_pos_cash_to_spend > max_pos_cash_to_spend:
        # 如果计划买入多头现金超过允许买入最大金额，按比例降低分配给每个拟买入多头资产的现金
        pos_cash_to_spend = pos_cash_to_spend / total_pos_cash_to_spend * max_pos_cash_to_spend

    if allow_sell_short:
        # 只有当allow_sell_short的时候才去考察允许持有的空头仓位限制
        current_short_pos = np.where(next_own_amounts < 0, next_own_amounts * prices, 0).sum() / total_value
        max_neg_cash_to_spend = (short_pos_limit - current_short_pos) * total_value

        if total_neg_cash_to_spend < max_neg_cash_to_spend:
            # 如果计划买入空头现金超过允许买入最大金额，按比例调降拟买入空头资产的现金
            neg_cash_to_spend = neg_cash_to_spend / total_neg_cash_to_spend * max_neg_cash_to_spend

    cash_to_spend = pos_cash_to_spend + neg_cash_to_spend

    # 批量提交股份买入计划，计算实际买入的股票份额和交易费用
    # 由于已经提前确认过现金总额，因此不存在买入总金额超过持有现金的情况
    amount_purchased, cash_spent, fee_buying = get_purchase_result(
            prices=prices,
            cash_to_spend=cash_to_spend,
            moq=moq_buy,
            cost_params=cost_params,
    )

    # 4, 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = fee_buying + fee_selling

    return cash_gained, cash_spent, amount_purchased, amount_sold, fee


def _get_complete_hist(looped_value: pd.DataFrame,
                       h_list: HistoryPanel,
                       benchmark_list: pd.DataFrame,
                       with_price: bool = False) -> pd.DataFrame:
    """完成历史交易回测后，填充完整的历史资产总价值清单，
        同时在回测清单中填入参考价格数据，参考价格数据用于数据可视化对比，参考数据的来源为Config.benchmark_asset

    Parameters
    ----------
    looped_value: pd.DataFrame
        完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
    h_list: pd.DataFrame
        完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
    benchmark_list: pd.DataFrame
        参考资产的历史价格清单，参考资产用于收益率的可视化对比，同时用于计算alpha、sharp等指标
    with_price: boolean, default False
        True时在返回的清单中包含历史价格，否则仅返回资产总价值

    Returns
    -------
    looped_value: pd.DataFrame:
    重新填充的完整历史交易日资产总价值清单，包含以下列：
    - [share-x]:        多列，每种投资产品的持有份额数量
    - cash:             期末现金金额
    - fee:              当期交易费用（交易成本）
    - value:            当期资产总额（现金总额 + 所有在手投资产品的价值总额）
    """
    # 获取价格清单中的投资产品列表
    shares = h_list.shares  # 获取资产清单
    try:
        start_date = looped_value.index[0]  # 开始日期
    except:
        raise IndexError('index 0 is out of bounds for axis 0 with size 0')
    looped_history = h_list.segment(start_date)  # 回测历史数据区间 = [开始日期:]
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    hdates = looped_history.hdates
    purchased_shares = looped_value[shares].reindex(hdates, method='ffill').fillna(0)
    cashes = looped_value['cash'].reindex(hdates, method='ffill').fillna(0)
    fees = looped_value['fee'].reindex(hdates).fillna(0)
    looped_value = looped_value.reindex(hdates)
    # 这里采用了一种看上去貌似比较奇怪的处理方式：
    # 先为cashes、purchased_shares两个变量赋值，
    # 然后再将上述两个变量赋值给looped_values的列中
    # 这样看上去好像多此一举，为什么不能直接赋值，然而
    # 经过测试，如果直接用下面的代码直接赋值，将无法起到
    # 填充值的作用：
    # looped_value.cash = looped_value.cash.reindex(dates, method='ffill')
    looped_value[shares] = purchased_shares
    looped_value.cash = cashes
    looped_value.fee = looped_value['fee'].reindex(hdates).fillna(0)
    looped_value['reference'] = benchmark_list.reindex(hdates).fillna(0)
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象，如果looped_history历史价格中包含多种价格，使用最后一种
    decisive_prices = looped_history[-1].squeeze(axis=2).T
    looped_value['value'] = (decisive_prices * looped_value[shares]).sum(axis=1) + looped_value['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        share_price_column_names = [name + '_p' for name in shares]
        looped_value[share_price_column_names] = looped_history[shares]
    return looped_value


def _merge_invest_dates(op_list: pd.DataFrame, invest: CashPlan) -> pd.DataFrame:
    """将完成的交易信号清单与现金投资计划合并：

    检查现金投资计划中的日期是否都存在于交易信号清单op_list中，如果op_list中没有相应日期时，当交易信号清单中没有相应日期时，添加空交易
    信号，以便使op_list中存在相应的日期。

    注意，在目前的设计中，要求invest中的所有投资日期都为交易日（意思是说，投资日期当天资产价格不为np.nan）
    否则，将会导致回测失败（回测当天取到np.nan作为价格，引起总资产计算失败，引起连锁反应所有的输出结果均为np.nan。

    需要在CashPlan投资计划类中增加合法性判断

    Parameters
    ----------
    op_list: pd.DataFrame
        交易信号清单，一个DataFrame。index为Timestamp类型
    invest: qt.CashPlan
        CashPlan对象，投资日期和投资金额
    Returns
    -------
    op_list: pd.DataFrame
        合并后的交易信号清单
    """
    if not isinstance(op_list, pd.DataFrame):
        raise TypeError(f'operation list should be a pandas DataFrame, got {type(op_list)} instead')
    if not isinstance(invest, CashPlan):
        raise TypeError(f'invest plan should be a qteasy CashPlan, got {type(invest)} instead')
    for date in invest.dates:
        try:
            op_list.loc[date]
        except Exception:
            op_list.loc[date] = 0
    op_list.sort_index(inplace=True)
    return op_list


# TODO: 删除operator作为传入参数，仅处理回测结果，将回测结果传出
#  函数后再处理为pandas.DataFrame，并在函数以外进行进一步的记录和处理，这里仅仅使用与回测相关
#  的参数
def apply_loop(operator: Operator,
               trade_price_list: HistoryPanel,
               start_idx: int = 0,
               end_idx: int = None,
               cash_plan: CashPlan = None,
               cost_rate: dict = None,
               moq_buy: float = 100.,
               moq_sell: float = 1.,
               inflation_rate: float = 0.03,
               pt_signal_timing: str = 'lazy',
               pt_buy_threshold: float = 0.1,
               pt_sell_threshold: float = 0.1,
               cash_delivery_period: int = 0,
               stock_delivery_period: int = 0,
               allow_sell_short: bool = False,
               long_pos_limit: float = 1.0,
               short_pos_limit: float = -1.0,
               max_cash_usage: bool = False,
               trade_log: bool = False,
               price_priority_list: list = None) -> tuple:
    """使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
        现金额及费用，输出的结果可选

    Parameters
    ----------
    operator: Operator
        用于生成交易信号(realtime模式)，预先生成的交易信号清单或清单相关信息也从中读取
    start_idx: int, Default: 0
        模拟交易从交易清单的该序号开始循环
    end_idx: int, Default: None
        模拟交易到交易清单的该序号为止
    trade_price_list: object HistoryPanel
        完整历史价格清单，数据的频率由freq参数决定
    cash_plan: CashPlan: Default: None
        资金投资计划，CashPlan对象
    cost_rate: dict: Default: None
        交易成本率，包含交易费、滑点及冲击成本
    moq_buy: float：Default: 100
        每次交易买进的最小份额单位
    moq_sell: float: Default: 1
        每次交易卖出的最小份额单位
    inflation_rate: float, Default: 0.03
        现金的时间价值率，如果>0，则现金的价值随时间增长，增长率为inflation_rate
    pt_signal_timing: str, {'lazy', 'eager', 'aggressive'}  # TODO: 增加参数值 'aggressive' 的alias 'eager'
        控制PT模式下交易信号产生的时机
    pt_buy_threshold: float, Default: 0.1
        PT买入信号阈值，只有当实际持仓与目标持仓的差值大于该阈值时，才会产生买入信号
    pt_sell_threshold: flaot, Default: 0.1
        PT卖出信号阈值，只有当实际持仓与目标持仓的差值小于该阈值时，才会产生卖出信号
    cash_delivery_period: int, Default: 0
        现金交割周期，默认值为0，单位为天。
    stock_delivery_period: int, Default: 0
        股票交割周期，默认值为0，单位为天。
    allow_sell_short: bool, Default: False
        是否允许卖空操作，如果不允许卖空，则卖出的数量不能超过持仓数量
    long_pos_limit: float, Default: 1.0
        允许持有的最大多头仓位比例
    short_pos_limit: flaot, Default: -1.0
        允许持有的最大空头仓位比例
    max_cash_usage: bool, Default: False
        是否最大化利用现金，如果为True，则在每次交易时，会将卖出股票的现金用于买入股票
    trade_log: bool: Default: False
        为True时，输出回测详细日志为csv格式的表格
    price_priority_list: list, Default: None
        各交易价格的执行顺序列表，列表中0～N数字代表operator中的各个交易价格的序号，各个交易价格
        将按照列表中的序号顺序执行

    Returns
    -------
    tuple: (loop_results, op_log_matrix, op_summary_matrix, op_list_bt_indices)
    - loop_results:        用于生成交易结果的数据，如持仓数量、交易费用、持有现金以及总资产
    - op_log_matrix:       用于生成详细交易记录的数据，包含每次交易的详细交易信息，如持仓、成交量、成交价格、现金变动、交易费用等等
    - op_summary_matrix:   用于生成详细交易记录的补充数据，包括投入资金量、资金变化量等
    - op_list_bt_indices:  交易清单中实际参加回测的行序号
    """
    if moq_buy == 0:
        assert moq_sell == 0, f'ValueError, if "trade_batch_size" is 0, then ' \
                              f'"sell_batch_size" should also be 0'
    if (moq_buy != 0) and (moq_sell != 0):
        assert moq_buy % moq_sell == 0, \
            f'ValueError, the sell moq should be divisible by moq_buy, or there will be mistake'
    signal_type = operator.signal_type_id
    op_type = operator.op_type

    # 获取交易信号的总行数、股票数量以及价格种类数量
    # 在这里，交易信号的价格种类数量与交易价格的价格种类数量必须一致，且顺序也必须一致
    op_list = None
    if operator.op_type == 'batch':

        op_list = operator.op_list

    looped_dates = operator.op_list_hdates
    share_count, op_count, price_type_count = operator.op_list_shape
    if end_idx is None:
        end_idx = op_count
    # 为防止回测价格数据中存在Nan值，需要首先将Nan值替换成0，否则将造成错误值并一直传递到回测历史最后一天
    price = trade_price_list.ffill(0).values
    # 获取每一个资金投入日在历史时间序列中的位置
    investment_date_pos = np.searchsorted(looped_dates, cash_plan.dates)
    invest_dict = cash_plan.to_dict(investment_date_pos)
    # 解析交易费率参数：
    cost_params = get_cost_pamams(cost_rate)
    # 确定是否属于PT+lazy的情形
    pt_and_lazy = (signal_type == 0) and (pt_signal_timing == 'lazy')

    # 检查信号清单，生成清单回测序号，生成需要跳过的交易信号的列表。这个列表有2维，分别代表每日/每回测价格信号是否可以跳过
    if operator.op_type == 'stepwise':
        # 在stepwise模式下，每一天都需要回，回测所有交易信号行
        skip_op_signal = np.zeros(shape=(op_count, price_type_count), dtype='bool')
    elif signal_type in [1, 2]:
        # 否则，在batch模式下，PS/VS模式下跳过没有信号的交易日, 并确保第一个回测日不为True
        skip_op_signal = np.all(op_list == 0, axis=0)
        skip_op_signal[start_idx, :] = False
    elif pt_and_lazy:
        # 或者，在batch模式下，PT模式下跳过信号没有发生变化的交易日，但确保第一个回测日不为True
        signal_diff = op_list - np.roll(op_list, 1, axis=1)
        skip_op_signal = np.all(signal_diff == 0, axis=0)
        skip_op_signal[start_idx, :] = False
    else:
        # 否则，在batch/PT/aggressive模式下，回测所有交易信号行
        skip_op_signal = np.zeros(shape=(op_count, price_type_count), dtype='bool')
    # 确定bt回测计算的范围
    op_list_bt_indices = np.array(range(start_idx, end_idx))
    # 如果inflation_rate > 0 则还需要计算所有有交易信号的日期相对前一个交易信号日的现金增长比率，这个比率与两个交易信号日之间的时间差有关
    inflation_factors = np.ones_like(op_list_bt_indices, dtype='float')
    additional_invest = 0.
    # 如果inflation_rate不为0，则需要计算每一个bt回测交易日相对上一日的现金增值幅度，用于计算现金增值
    if inflation_rate > 0:
        # TODO: 考虑把下面的计算numba化
        # 在不同的datafreq下，相差一个idx不一定代表相差一天，因此需要计算每个idx之间实际相差的天数
        bt_index_days = pd.to_datetime(looped_dates)[op_list_bt_indices]
        days_difference = np.array((bt_index_days - np.roll(bt_index_days, 1)).days)
        daily_ir = 1 + inflation_rate / 365.  # 由于这几计算的是两个日期之间的自然天数之差，因此日利率需要用ir/365计算
        inflation_factors = daily_ir ** days_difference
        inflation_factors[0] = 1.  # 使用np.roll计算后的第一个值是错误值，需要修正为1

    # 决定交易中是否最大化使用现金
    maximize_cash_usage = max_cash_usage and (cash_delivery_period == 0)
    # 保存trade_log_table数据：
    op_log_add_invest = []
    op_log_cash = []
    op_log_available_cash = []
    op_log_value = []
    op_log_matrix = []
    prev_date = 0

    if (op_type == 'batch') and (not trade_log):
        # batch模式下调用apply_loop_core函数:
        looped_day_indices = np.array(list(pd.to_datetime(pd.to_datetime(looped_dates).date).astype('int')))
        # 2, 将invset_dict处理为两个列表：invest_date_indices, invest_amount，因为invest_dict无法被Numba处理
        investment_date_pos = np.array(list(investment_date_pos))
        invest_amounts = np.array(list(invest_dict.values()))
        cashes, fees, values, amounts_matrix = apply_loop_core(share_count,
                                                               looped_day_indices,
                                                               inflation_factors,
                                                               investment_date_pos,
                                                               invest_amounts,
                                                               price,
                                                               op_list,
                                                               signal_type,
                                                               op_list_bt_indices,
                                                               skip_op_signal,
                                                               cost_params,
                                                               moq_buy,
                                                               moq_sell,
                                                               inflation_rate,
                                                               pt_buy_threshold,
                                                               pt_sell_threshold,
                                                               cash_delivery_period,
                                                               stock_delivery_period,
                                                               allow_sell_short,
                                                               long_pos_limit,
                                                               short_pos_limit,
                                                               maximize_cash_usage,
                                                               price_priority_list)
    else:
        # 初始化计算结果列表
        own_cash = 0.  # 持有现金总额，期初现金总额总是0，在回测过程中到现金投入日时再加入现金
        available_cash = 0.  # 每期可用现金总额
        own_amounts = np.zeros(shape=(share_count,))  # 投资组合中各个资产的持有数量，初始值为全0向量
        available_amounts = np.zeros(shape=(share_count,))  # 每期可用的资产数量
        cash_delivery_queue = []  # 用于模拟现金交割延迟期的定长队列
        stock_delivery_queue = []  # 用于模拟股票交割延迟期的定长队列
        cashes = []  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
        fees = []  # 交易费用，记录每个操作时点产生的交易费用
        values = []  # 资产总价值，记录每个操作时点的资产和现金价值总和
        amounts_matrix = []
        total_value = 0
        trade_data = np.zeros(shape=(share_count, 5))  # 交易汇总数据表，包含最近成交、交易价格、持仓数量、
        # 持有现金等数据的数组，用于stepwise信号生成
        recent_amounts_change = np.zeros(shape=(share_count,))  # 中间变量，保存最近的一次交易数量
        recent_trade_prices = np.zeros(shape=(share_count,))  # 中间变量，保存最近一次的成交价格
        result_count = 0  # 进行循环的次数
        # 在stepwise模式下pt_and_lazy情形需要跳过某些交易信号，需要用到prev_op
        prev_op = np.empty(shape=(share_count, price_type_count), dtype='float')
        prev_op[:, :] = np.nan
        for i in op_list_bt_indices:
            # 对每一回合历史交易信号开始回测，每一回合包含若干交易价格上所有股票的交易信号
            current_date = looped_dates[i].date()
            sub_total_fee = 0
            if inflation_rate > 0:
                # 现金的价值随时间增长，需要依次乘以inflation 因子，且只有持有现金增值，新增的现金不增值
                current_inflation_factor = inflation_factors[result_count]
                own_cash *= current_inflation_factor
                available_cash *= current_inflation_factor
            if i in investment_date_pos:
                # 如果在交易当天有资金投入，则将投入的资金加入可用资金池中
                additional_invest = invest_dict[i]
                own_cash += additional_invest
                available_cash += additional_invest
            for j in price_priority_list:
                # 交易前将交割队列中达到交割期的现金完成交割
                if ((prev_date != current_date) and
                    (len(cash_delivery_queue) == cash_delivery_period)) or \
                        (cash_delivery_period == 0):
                    if len(cash_delivery_queue) > 0:
                        cash_delivered = cash_delivery_queue.pop(0)
                        available_cash += cash_delivered
                # 交易前将交割队列中达到交割期的资产完成交割
                if ((prev_date != current_date) and
                    (len(stock_delivery_queue) == stock_delivery_period)) or \
                        (stock_delivery_period == 0):
                    if len(stock_delivery_queue) > 0:
                        stock_delivered = stock_delivery_queue.pop(0)
                        available_amounts += stock_delivered
                # 调用loop_step()函数，计算本轮交易的现金和股票变动值以及总交易费用
                current_prices = price[:, result_count, j]
                if op_type == 'stepwise':
                    # 在realtime模式下，准备trade_data并计算下一步的交易信号
                    trade_data[:, 0] = own_amounts
                    trade_data[:, 1] = available_amounts
                    trade_data[:, 2] = current_prices
                    trade_data[:, 3] = recent_amounts_change
                    trade_data[:, 4] = recent_trade_prices
                    current_op = operator.create_signal(
                            trade_data=trade_data,
                            sample_idx=i,
                            price_type_idx=j
                    )
                    if pt_and_lazy and np.all(prev_op[:, j] == current_op):
                        skip_op_signal[i, j] = True
                    prev_op[:, j] = current_op

                elif op_type == 'batch':
                    # 在batch模式下，直接从批量生成的交易信号清单中读取下一步交易信号
                    current_op = op_list[:, i, j]
                else:
                    # 其他不合法的op_type
                    raise TypeError(f'invalid op_type!')
                # 处理需要回测的交易信号，只有需要回测的信号才送入loop_step，否则直接生成五组全0结果
                if skip_op_signal[i, j]:
                    cash_gained = np.zeros_like(current_op)
                    cash_spent = np.zeros_like(current_op)
                    amount_purchased = np.zeros_like(current_op)
                    amount_sold = np.zeros_like(current_op)
                    fee = np.zeros_like(current_op)
                else:
                    cash_gained, cash_spent, amount_purchased, amount_sold, fee = _loop_step(
                            signal_type=signal_type,
                            own_cash=own_cash,
                            own_amounts=own_amounts,
                            available_cash=available_cash,
                            available_amounts=available_amounts,
                            op=current_op,
                            prices=current_prices,
                            cost_params=cost_params,
                            pt_buy_threshold=pt_buy_threshold,
                            pt_sell_threshold=pt_sell_threshold,
                            maximize_cash_usage=maximize_cash_usage,
                            allow_sell_short=allow_sell_short,
                            long_pos_limit=long_pos_limit,
                            short_pos_limit=short_pos_limit,
                            moq_buy=moq_buy,
                            moq_sell=moq_sell
                    )
                # 获得的现金进入交割队列，根据日期的变化确定是新增现金交割还是累加现金交割
                if (prev_date != current_date) or (cash_delivery_period == 0):
                    cash_delivery_queue.append(cash_gained.sum())
                else:
                    cash_delivery_queue[-1] += cash_gained.sum()

                # 获得的资产进入交割队列，根据日期的变化确定是新增资产交割还是累加资产交割
                if (prev_date != current_date) or (stock_delivery_period == 0):
                    stock_delivery_queue.append(amount_purchased)
                else:  # if prev_date == current_date
                    stock_delivery_queue[-1] += amount_purchased

                prev_date = current_date
                # 持有现金、持有股票用于计算本期的总价值
                available_cash += cash_spent.sum()
                available_amounts += amount_sold
                cash_changed = cash_gained + cash_spent
                own_cash = own_cash + cash_changed.sum()
                amount_changed = amount_sold + amount_purchased
                own_amounts = own_amounts + amount_changed
                total_stock_values = (own_amounts * current_prices)
                total_stock_value = total_stock_values.sum()
                total_value = total_stock_value + own_cash
                sub_total_fee += fee.sum()
                # 生成trade_log所需的数据，采用串列式表格排列：
                if trade_log:
                    rnd = np.round
                    op_log_matrix.append(rnd(current_op, 3))
                    op_log_matrix.append(rnd(current_prices, 3))
                    op_log_matrix.append(rnd(amount_changed, 3))
                    op_log_matrix.append(rnd(cash_changed, 3))
                    op_log_matrix.append(rnd(fee, 3))
                    op_log_matrix.append(rnd(own_amounts, 3))
                    op_log_matrix.append(rnd(available_amounts, 3))
                    op_log_matrix.append(rnd(total_stock_values, 3))
                    op_log_add_invest.append(rnd(additional_invest, 3))
                    additional_invest = 0.
                    op_log_cash.append(rnd(own_cash, 3))
                    op_log_available_cash.append(rnd(available_cash, 3))
                    op_log_value.append(rnd(total_value, 3))

            # 保存计算结果
            cashes.append(own_cash)
            fees.append(sub_total_fee)
            values.append(total_value)
            amounts_matrix.append(own_amounts)
            result_count += 1

    loop_results = (amounts_matrix, cashes, fees, values)
    op_summary_matrix = (op_log_add_invest, op_log_cash, op_log_available_cash, op_log_value)
    return loop_results, op_log_matrix, op_summary_matrix, op_list_bt_indices


@njit(nogil=True, cache=True)
def apply_loop_core(share_count: int,
                    looped_dates: np.ndarray,
                    inflation_factors: np.ndarray,
                    investment_date_pos: np.ndarray,
                    invest_amounts: np.ndarray,
                    price: np.ndarray,
                    op_list: np.ndarray,
                    signal_type: int,
                    op_list_bt_indices: np.ndarray,
                    skip_op_signal: np.ndarray,
                    cost_params: np.ndarray,
                    moq_buy: float,
                    moq_sell: float,
                    inflation_rate: float,
                    pt_buy_threshold: float,
                    pt_sell_threshold: float,
                    cash_delivery_period: int,
                    stock_delivery_period: int,
                    allow_sell_short: bool,
                    long_pos_limit: float,
                    short_pos_limit: float,
                    max_cash_usage: bool,
                    price_priority_list: list):
    """ apply_loop的核心function,不含任何numba不支持的元素，仅包含batch模式下，
        不需要生成trade_log的情形下运行核心循环的核心代码。
        在符合要求的情况下，这部分代码以njit方式加速运行，实现提速

    TODO: v1.1: 优化代码，去除代码中使用list来进行交割日期计算的部分，使用numpy数组来代替，提高代码效率
     避免产生numba warnings：
     NumbaPendingDeprecationWarning:
     Encountered the use of a type that is scheduled for deprecation: type 'reflected list'
     found for argument 'looped_dates' of function 'apply_loop_core'.
     For more information visit
     https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-reflection-for-list-and-set-types

    Parameters
    ----------
    share_count: int
        股票数量
    looped_dates: np.ndarray
        回测日期序列
    inflation_factors: np.ndarray
        通货膨胀因子序列
    investment_date_pos: np.ndarray
        投资日期在回测日期序列中的位置
    invest_amounts: np.ndarray
        投资金额序列
    price: np.ndarray
        价格序列
    op_list: np.ndarray
        交易信号序列
    signal_type: int
        交易信号类型
    op_list_bt_indices: np.ndarray
        交易信号序列的回测序列
    skip_op_signal: np.ndarray
        交易信号跳过序列
    cost_params: np.ndarray
        交易费率参数
    moq_buy: float
        最小买入量
    moq_sell: float
        最小卖出量
    inflation_rate: float
        通货膨胀率，用于计算无风险利率
    pt_buy_threshold: float
        PT买入阈值
    pt_sell_threshold: float
        PT卖出阈值
    cash_delivery_period: int
        现金交割周期
    stock_delivery_period: int
        股票交割周期
    allow_sell_short: bool
        是否允许卖空
    long_pos_limit: float
        最大多头仓位
    short_pos_limit: float
        最大空头仓位
    max_cash_usage: bool
        是否最大化利用现金
    price_priority_list: list
        价格优先级列表

    Returns
    -------
    """

    # 初始化计算结果列表
    own_cash = 0.  # 持有现金总额，期初现金总额总是0，在回测过程中到现金投入日时再加入现金
    available_cash = 0.  # 每期可用现金总额
    own_amounts = np.zeros(shape=(share_count,))  # 投资组合中各个资产的持有数量，初始值为全0向量
    available_amounts = np.zeros(shape=(share_count,))  # 每期可用的资产数量
    cash_delivery_queue = []  # 用于模拟现金交割延迟期的定长队列  # TODO: 使用numpy数组代替list
    stock_delivery_queue = []  # 用于模拟股票交割延迟期的定长队列  # TODO: 使用numpy数组代替list
    signal_count = len(op_list_bt_indices)
    cashes = np.empty(shape=(signal_count,))  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
    fees = np.empty(shape=(signal_count,))  # 交易费用，记录每个操作时点产生的交易费用
    values = np.empty(shape=(signal_count,))  # 资产总价值，记录每个操作时点的资产和现金价值总和
    amounts_matrix = np.empty(shape=(signal_count, share_count))
    total_value = 0
    prev_date = 0
    investment_count = 0  # 用于正确读取每笔投资金额的计数器
    result_count = 0  # 用于确保正确输出每笔交易结果的计数器

    for i in op_list_bt_indices:
        # 对每一回合历史交易信号开始回测，每一回合包含若干交易价格上所有股票的交易信号
        current_date = looped_dates[i]
        sub_total_fee = 0
        if inflation_rate > 0:
            # 现金的价值随时间增长，需要依次乘以inflation 因子，且只有持有现金增值，新增的现金不增值
            own_cash *= inflation_factors[result_count]
            available_cash *= inflation_factors[result_count]
        if i in investment_date_pos:
            # 如果在交易当天有资金投入，则将投入的资金加入可用资金池中
            additional_invest = invest_amounts[investment_count]
            own_cash += additional_invest
            available_cash += additional_invest
            investment_count += 1
        for j in price_priority_list:
            # 交易前将交割队列中达到交割期的现金完成交割
            if ((prev_date != current_date) and
                (len(cash_delivery_queue) == cash_delivery_period)) or \
                    (cash_delivery_period == 0):
                if len(cash_delivery_queue) > 0:
                    cash_delivered = cash_delivery_queue.pop(0)
                    available_cash += cash_delivered
            # 交易前将交割队列中达到交割期的资产完成交割
            if ((prev_date != current_date) and
                (len(stock_delivery_queue) == stock_delivery_period)) or \
                    (stock_delivery_period == 0):
                if len(stock_delivery_queue) > 0:
                    stock_delivered = stock_delivery_queue.pop(0)
                    available_amounts += stock_delivered
            # 调用loop_step()函数，计算本轮交易的现金和股票变动值以及总交易费用
            current_prices = price[:, result_count, j]
            current_op = op_list[:, i, j]
            if skip_op_signal[i, j]:
                cash_gained = np.zeros_like(current_op)
                cash_spent = np.zeros_like(current_op)
                amount_purchased = np.zeros_like(current_op)
                amount_sold = np.zeros_like(current_op)
                fee = np.zeros_like(current_op)
            else:
                maximize_cash_usage = max_cash_usage and cash_delivery_period == 0
                cash_gained, cash_spent, amount_purchased, amount_sold, fee = _loop_step(
                        signal_type=signal_type,
                        own_cash=own_cash,
                        own_amounts=own_amounts,
                        available_cash=available_cash,
                        available_amounts=available_amounts,
                        op=current_op,
                        prices=current_prices,
                        cost_params=cost_params,
                        pt_buy_threshold=pt_buy_threshold,
                        pt_sell_threshold=pt_sell_threshold,
                        maximize_cash_usage=maximize_cash_usage,
                        allow_sell_short=allow_sell_short,
                        long_pos_limit=long_pos_limit,
                        short_pos_limit=short_pos_limit,
                        moq_buy=moq_buy,
                        moq_sell=moq_sell
                )
            # 获得的现金进入交割队列，根据日期的变化确定是新增现金交割还是累加现金交割
            if (prev_date != current_date) or (cash_delivery_period == 0):
                cash_delivery_queue.append(cash_gained.sum())
            else:
                cash_delivery_queue[-1] += cash_gained.sum()

            # 获得的资产进入交割队列，根据日期的变化确定是新增资产交割还是累加资产交割
            if (prev_date != current_date) or (stock_delivery_period == 0):
                stock_delivery_queue.append(amount_purchased)
            else:  # if prev_date == current_date
                stock_delivery_queue[-1] += amount_purchased

            prev_date = current_date
            # 持有现金、持有股票用于计算本期的总价值
            available_cash += cash_spent.sum()
            available_amounts += amount_sold
            cash_changed = cash_gained + cash_spent
            own_cash = own_cash + cash_changed.sum()
            amount_changed = amount_sold + amount_purchased
            own_amounts = own_amounts + amount_changed
            total_stock_values = (own_amounts * current_prices)
            total_stock_value = total_stock_values.sum()
            total_value = total_stock_value + own_cash
            sub_total_fee += fee.sum()

        # 保存计算结果
        cashes[result_count] = own_cash
        fees[result_count] = sub_total_fee
        values[result_count] = total_value
        amounts_matrix[result_count, :] = own_amounts
        result_count += 1

    return cashes, fees, values, amounts_matrix


def process_loop_results(operator,
                         loop_results=None,
                         op_log_matrix=None,
                         op_summary_matrix=None,
                         op_list_bt_indices=None,
                         trade_log=False,
                         bt_price_priority_ohlc: str = 'OHLC'):
    """ 接受apply_loop函数传回的计算结果，生成DataFrame型交易模拟结果数据，保存交易记录，并返回结果供下一步处理

    Parameters
    ----------
    operator: Operator
        交易操作对象
    loop_results: tuple, optional
        apply_loop函数返回的计算结果
    op_log_matrix: np.ndarray, optional
        交易记录矩阵，记录了模拟交易过程中每一笔交易的详细信息
    op_summary_matrix: np.ndarray, optional
        交易汇总矩阵，记录了模拟交易过程中每一笔交易的汇总信息
    op_list_bt_indices: list, optional
        交易记录矩阵中的交易日期索引
    trade_log: bool, optional, default False
        是否保存交易记录，默认为False
    bt_price_priority_ohlc: str, optional, default 'OHLC'
        交易记录中的价格优先级，可选'OHLC'、'HLOC'、'LOCH'、'LCOH'、'COHL'、'COLH'

    Returns
    -------
    value_history: pd.DataFrame
        交易模拟结果数据
    """
    from qteasy import logger_core
    amounts_matrix, cashes, fees, values = loop_results
    shares = operator.op_list_shares
    complete_loop_dates = operator.op_list_hdates
    looped_dates = [complete_loop_dates[item] for item in op_list_bt_indices]

    price_types_in_priority = operator.get_bt_price_types_in_priority(priority=bt_price_priority_ohlc)

    # 将向量化计算结果转化回DataFrame格式
    value_history = pd.DataFrame(amounts_matrix, index=looped_dates,
                                 columns=shares)
    # 填充标量计算结果
    value_history['cash'] = cashes
    value_history['fee'] = fees
    value_history['value'] = values

    # 生成trade_log，index为MultiIndex，因为每天的交易可能有多种价格
    if trade_log:
        from .core import get_basic_info
        # create complete trading log
        logger_core.info(f'generating complete trading log ...')
        op_log_index = pd.MultiIndex.from_product(
                [looped_dates,
                 price_types_in_priority,
                 ['0, trade signal',
                  '1, price',
                  '2, traded amounts',
                  '3, cash changed',
                  '4, trade cost',
                  '5, own amounts',
                  '6, available amounts',
                  '7, summary']],
                names=('date', 'trade_on', 'item')
        )
        op_sum_index = pd.MultiIndex.from_product(
                [looped_dates,
                 price_types_in_priority,
                 ['7, summary']],
                names=('date', 'trade_on', 'item')
        )
        op_log_columns = [str(s) for s in shares]
        op_log_df = pd.DataFrame(op_log_matrix, index=op_log_index, columns=op_log_columns)
        op_summary_df = pd.DataFrame(op_summary_matrix,
                                     index=['add. invest', 'own cash', 'available cash', 'value'],
                                     columns=op_sum_index).T
        log_file_path_name = os.path.join(qteasy.QT_TRADE_LOG_PATH, 'trade_log.csv')
        op_summary_df.join(op_log_df, how='right', sort=False).to_csv(log_file_path_name, encoding='utf-8')

        # 生成 trade log 摘要表 (a more concise and human-readable format of trading log
        # create share trading logs:
        logger_core.info(f'generating abstract trading log ...')
        share_logs = []
        for share in op_log_columns:
            share_df = op_log_df[share].unstack()
            share_df = share_df[share_df['2, traded amounts'] != 0]
            share_df['code'] = share
            try:
                share_name = get_basic_info(share, printout=False)['name']
            except Exception as e:
                share_name = 'unknown'
            share_df['name'] = share_name
            share_logs.append(share_df)

        re_columns = ['code',
                      'name',
                      '0, trade signal',
                      '1, price',
                      '2, traded amounts',
                      '3, cash changed',
                      '4, trade cost',
                      '5, own amounts',
                      '6, available amounts',
                      '7, summary']
        op_log_shares_abs = pd.concat(share_logs).reindex(columns=re_columns)
        record_file_path_name = os.path.join(qteasy.QT_TRADE_LOG_PATH, 'trade_records.csv')
        # TODO: 可以增加一个config属性来控制交易摘要表的生成规则：
        #  如果how == 'left' 保留无交易日期的记录
        #  如果how == 'right', 不显示无交易日期的记录
        op_summary_df.join(op_log_shares_abs, how='right', sort=True).to_csv(record_file_path_name, encoding='utf-8')

    return value_history
