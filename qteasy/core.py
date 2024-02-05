# coding=utf-8
# ======================================
# File:     core.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-16
# Desc:
#   Core functions and Classes of qteasy.
# ======================================

import os
import pandas as pd
import numpy as np
import time
import math
from warnings import warn
from numba import njit

from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime

import qteasy
from .history import get_history_panel, HistoryPanel, stack_dataframes
from .utilfuncs import sec_to_duration, progress_bar, str_to_list, regulate_date_format, match_ts_code
from .utilfuncs import next_market_trade_day
from .utilfuncs import AVAILABLE_ASSET_TYPES, _partial_lev_ratio
from .space import Space, ResultPool
from .finance import CashPlan, get_selling_result, get_purchase_result, set_cost
from .qt_operator import Operator
from .visual import _plot_loop_result, _print_loop_result, _print_test_result
from .visual import _plot_test_result
from .evaluate import evaluate, performance_statistics
from ._arg_validators import _update_config_kwargs, ConfigDict

from ._arg_validators import QT_CONFIG, _vkwargs_to_text
#TODO: reduce the size of this file, split it into several files


@njit
def _loop_step(signal_type: int,
               own_cash: float,
               own_amounts: np.ndarray,
               available_cash: float,
               available_amounts: np.ndarray,
               op: np.ndarray,
               prices: np.ndarray,
               buy_fix: float,
               sell_fix: float,
               buy_rate: float,
               sell_rate: float,
               buy_min: float,
               sell_min: float,
               slipage: float,
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
    buy_fix: float
        交易成本：固定买入费用
    sell_fix: float
        交易成本：固定卖出费用
    buy_rate: float
        交易成本：固定买入费率
    sell_rate: float
        交易成本：固定卖出费率
    buy_min: float
        交易成本：最低买入费用
    sell_min: float
        交易成本：最低卖出费用
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

        :param moq_buy: float:
            投资产品最买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

        :param moq_sell: float:
            投资产品最买入交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

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
            buy_fix=buy_fix,
            sell_fix=sell_fix,
            buy_rate=buy_rate,
            sell_rate=sell_rate,
            buy_min=buy_min,
            sell_min=sell_min,
            slipage=slipage
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
            buy_fix=buy_fix,
            sell_fix=sell_fix,
            buy_rate=buy_rate,
            sell_rate=sell_rate,
            buy_min=buy_min,
            sell_min=sell_min,
            slipage=slipage
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
    buy_fix = cost_rate['buy_fix']
    sell_fix = cost_rate['sell_fix']
    buy_rate = cost_rate['buy_rate']
    sell_rate = cost_rate['sell_rate']
    buy_min = cost_rate['buy_min']
    sell_min = cost_rate['sell_min']
    slipage = cost_rate['slipage']
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
        looped_day_indices = list(pd.to_datetime(pd.to_datetime(looped_dates).date).astype('int'))
        # 2, 将invset_dict处理为两个列表：invest_date_indices, invest_amount，因为invest_dict无法被Numba处理
        investment_date_pos = list(investment_date_pos)
        invest_amounts = list(invest_dict.values())
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
                                                               buy_fix,
                                                               sell_fix,
                                                               buy_rate,
                                                               sell_rate,
                                                               buy_min,
                                                               sell_min,
                                                               slipage,
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
                            buy_fix=buy_fix,
                            sell_fix=sell_fix,
                            buy_rate=buy_rate,
                            sell_rate=sell_rate,
                            buy_min=buy_min,
                            sell_min=sell_min,
                            slipage=slipage,
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
                # debug
                # print(f'step {i} {op_type} looping result on {current_date}, total Value {total_value}::\n'
                #       f'op from calculation: {current_op}, prices: {current_prices}\n'
                #       f'cash change: {cash_changed}, own cash: {own_cash}\n'
                #       f'amount changed: {amount_changed}, '
                #       f'own amounts: {own_amounts}\n')

            # 保存计算结果
            cashes.append(own_cash)
            fees.append(sub_total_fee)
            values.append(total_value)
            amounts_matrix.append(own_amounts)
            result_count += 1

    loop_results = (amounts_matrix, cashes, fees, values)
    op_summary_matrix = (op_log_add_invest, op_log_cash, op_log_available_cash, op_log_value)
    return loop_results, op_log_matrix, op_summary_matrix, op_list_bt_indices


@njit
def apply_loop_core(share_count,
                    looped_dates,
                    inflation_factors,
                    investment_date_pos,
                    invest_amounts,
                    price,
                    op_list,
                    signal_type,
                    op_list_bt_indices,
                    skip_op_signal,
                    buy_fix: float,
                    sell_fix: float,
                    buy_rate: float,
                    sell_rate: float,
                    buy_min: float,
                    sell_min: float,
                    slipage: float,
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

    Returns
    -------
    """

    # 初始化计算结果列表
    own_cash = 0.  # 持有现金总额，期初现金总额总是0，在回测过程中到现金投入日时再加入现金
    available_cash = 0.  # 每期可用现金总额
    own_amounts = np.zeros(shape=(share_count,))  # 投资组合中各个资产的持有数量，初始值为全0向量
    available_amounts = np.zeros(shape=(share_count,))  # 每期可用的资产数量
    cash_delivery_queue = []  # 用于模拟现金交割延迟期的定长队列
    stock_delivery_queue = []  # 用于模拟股票交割延迟期的定长队列
    signal_count = len(op_list_bt_indices)
    cashes = np.empty(shape=(signal_count, ))  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
    fees = np.empty(shape=(signal_count, ))  # 交易费用，记录每个操作时点产生的交易费用
    values = np.empty(shape=(signal_count, ))  # 资产总价值，记录每个操作时点的资产和现金价值总和
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
                cash_gained, cash_spent, amount_purchased, amount_sold, fee = _loop_step(
                        signal_type=signal_type,
                        own_cash=own_cash,
                        own_amounts=own_amounts,
                        available_cash=available_cash,
                        available_amounts=available_amounts,
                        op=current_op,
                        prices=current_prices,
                        buy_fix=buy_fix,
                        sell_fix=sell_fix,
                        buy_rate=buy_rate,
                        sell_rate=sell_rate,
                        buy_min=buy_min,
                        sell_min=sell_min,
                        slipage=slipage,
                        pt_buy_threshold=pt_buy_threshold,
                        pt_sell_threshold=pt_sell_threshold,
                        maximize_cash_usage=max_cash_usage and cash_delivery_period == 0,
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
        log_file_path_name = qteasy.QT_TRADE_LOG_PATH + '/trade_log.csv'
        op_summary_df.join(op_log_df, how='right', sort=False).to_csv(log_file_path_name)
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
                # logger_core.warning(f'Error encountered getting share names\n{e}')
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
        record_file_path_name = qteasy.QT_TRADE_LOG_PATH + '/trade_records.csv'
        # TODO: 可以增加一个config属性来控制交易摘要表的生成规则：
        #  如果how == 'left' 保留无交易日期的记录
        #  如果how == 'right', 不显示无交易日期的记录
        op_summary_df.join(op_log_shares_abs, how='right', sort=True).to_csv(record_file_path_name)

    return value_history


def filter_stocks(date: str = 'today', **kwargs) -> pd.DataFrame:
    """根据输入的参数筛选股票，并返回一个包含股票代码和相关信息的DataFrame

    Parameters
    ----------
    date: date-like str
        筛选股票的上市日期，在该日期以后上市的股票将会被剔除：
    kwargs: str or list of str
        可以通过以下参数筛选股票, 可以同时输入多个筛选条件，只有符合要求的股票才会被筛选出来
        - index:      根据指数筛选，不含在指定的指数内的股票将会被剔除
        - industry:   公司所处行业，只有列举出来的行业会被选中
        - area:       公司所处省份，只有列举出来的省份的股票才会被选中
        - market:     市场，分为主板、创业板等
        - exchange:   交易所，包括上海证券交易所和深圳股票交易所

    Returns
    -------
    DataFrame: 筛选出来的股票的基本信息

    Examples
    --------
    >>> # 筛选出2019年1月1日以后的上证300指数成分股
    >>> filter_stocks(date='2019-01-01', index='000300.SH')
           symbol   name area industry market  list_date exchange
    ts_code
    000001.SZ  000001   平安银行   深圳       银行     主板 1991-04-03     SZSE
    000002.SZ  000002    万科A   深圳     全国地产     主板 1991-01-29     SZSE
    000063.SZ  000063   中兴通讯   深圳     通信设备     主板 1997-11-18     SZSE
    000069.SZ  000069   华侨城A   深圳     全国地产     主板 1997-09-10     SZSE
    000100.SZ  000100  TCL科技   广东      元器件     主板 2004-01-30     SZSE
               ...    ...  ...      ...    ...        ...      ...
    600732.SH  600732   爱旭股份   上海     电气设备     主板 1996-08-16      SSE
    600754.SH  600754   锦江酒店   上海     酒店餐饮     主板 1996-10-11      SSE
    600875.SH  600875   东方电气   四川     电气设备     主板 1995-10-10      SSE
    601699.SH  601699   潞安环能   山西     煤炭开采     主板 2006-09-22      SSE
    688223.SH  688223   晶科能源   江西     电气设备    科创板 2022-01-26      SSE
    [440 rows x 7 columns]

    >>> # 筛选出2019年1月1日以后上市的上海银行业的股票
    >>> filter_stocks(date='2019-01-01', industry='银行', area='上海')
               name area industry market  list_date exchange
    ts_code
    600000.SH  浦发银行   上海       银行     主板 1999-11-10      SSE
    601229.SH  上海银行   上海       银行     主板 2016-11-16      SSE
    601328.SH  交通银行   上海       银行     主板 2007-05-15      SSE
    """
    try:
        date = pd.to_datetime(date)
    except:
        date = pd.to_datetime('today')
    # validate all input args:
    if not all(arg.lower() in ['index', 'industry', 'area', 'market', 'exchange'] for arg in kwargs.keys()):
        raise KeyError()
    if not all(isinstance(val, (str, list)) for val in kwargs.values()):
        raise KeyError()

    ds = qteasy.QT_DATA_SOURCE
    # ts_code是dataframe的index
    share_basics = ds.read_table_data('stock_basic')[['symbol', 'name', 'area', 'industry',
                                                      'market', 'list_date', 'exchange']]
    if share_basics is None or share_basics.empty:
        return pd.DataFrame()
    share_basics['list_date'] = pd.to_datetime(share_basics.list_date)
    none_matched = dict()
    # 找出targets中无法精确匹配的值，加入none_matched字典，随后尝试模糊匹配并打印模糊模糊匹配信息
    # print('looking for none matching arguments')
    for column, targets in kwargs.items():
        if column == 'index':
            continue
        if isinstance(targets, str):
            targets = str_to_list(targets)
            kwargs[column] = targets
        all_column_values = share_basics[column].unique().tolist()
        target_not_matched = [item for item in targets if item not in all_column_values]
        if len(target_not_matched) > 0:
            kwargs[column] = list(set(targets) - set(target_not_matched))
            match_dict = {}
            for t in target_not_matched:
                similarities = []
                for s in all_column_values:
                    if not isinstance(s, str):
                        similarities.append(0.0)
                        continue
                    try:
                        similarities.append(_partial_lev_ratio(s, t))
                    except Exception as e:
                        print(f'{e}, error during matching "{t}" and "{s}"')
                        raise e
                sim_array = np.array(similarities)
                best_matched = [all_column_values[i] for i in
                                np.where(sim_array >= 0.5)[0]
                                if
                                isinstance(all_column_values[i], str)]
                match_dict[t] = best_matched
                best_matched_str = '\" or \"'.join(best_matched)
                print(f'{t} will be excluded because an exact match is not found in "{column}", did you mean\n'
                      f'"{best_matched_str}"?')
            none_matched[column] = match_dict
        # 从清单中将none_matched移除
    for column, targets in kwargs.items():
        if column == 'index':
            # 查找date到今天之间的所有成分股, 如果date为today，则将date前推一个月
            end_date = pd.to_datetime('today')
            start_date = date - pd.Timedelta(50, 'd')
            index_comp = ds.read_table_data('index_weight',
                                            shares=targets,
                                            start=start_date.strftime("%Y%m%d"),
                                            end=end_date.strftime('%Y%m%d'))
            if index_comp.empty:
                return index_comp
            # share_basics.loc[a_list] is deprecated since pandas 1.0.0
            # return share_basics.loc[index_comp.index.get_level_values('con_code').unique().tolist()]
            return share_basics.reindex(index=index_comp.index.get_level_values('con_code').unique().tolist())
        if isinstance(targets, str):
            targets = str_to_list(targets)
        if len(targets) == 0:
            continue
        if not all(isinstance(target, str) for target in targets):
            raise KeyError(f'the list should contain only strings')
        share_basics = share_basics.loc[share_basics[column].isin(targets)]
    share_basics = share_basics.loc[share_basics.list_date <= date]
    if not share_basics.empty:
        return share_basics[['name', 'area', 'industry', 'market', 'list_date', 'exchange']]
    else:
        return share_basics


def filter_stock_codes(date: str = 'today', **kwargs) -> list:
    """根据输入的参数调用filter_stocks筛选股票，并返回股票代码的清单

    Parameters
    ----------
    date: date-like str
        筛选股票的上市日期，在该日期以后上市的股票将会被剔除：
    kwargs: str or list of str
        可以通过以下参数筛选股票, 可以同时输入多个筛选条件，只有符合要求的股票才会被筛选出来

    Returns
    -------
    list, 股票代码清单

    See Also
    --------
    filter_stock()
    """
    share_basics = filter_stocks(date=date, **kwargs)
    return share_basics.index.to_list()


def get_basic_info(code_or_name: str, asset_types=None, match_full_name=False, printout=True, verbose=False):
    """ 等同于get_stock_info()
        根据输入的信息，查找股票、基金、指数或期货、期权的基本信息

    Parameters
    ----------
    code_or_name:
        证券代码或名称，
        如果是证券代码，可以含后缀也可以不含后缀，含后缀时精确查找、不含后缀时全局匹配
        如果是证券名称，可以包含通配符模糊查找，也可以通过名称模糊查找
        如果精确匹配到一个证券代码，返回一个字典，包含该证券代码的相关信息
    asset_types: 默认None
        证券类型，接受列表或逗号分隔字符串，包含认可的资产类型：
        - E     股票
        - IDX   指数
        - FD    基金
        - FT    期货
        - OPT   期权
    match_full_name: bool, default False
        是否匹配股票或基金的全名，默认否，如果匹配全名，耗时更长
    printout: bool, default True
        如果为True，打印匹配到的结果
    verbose: bool, default False
        当匹配到的证券太多时（多于五个），是否显示完整的信息
        - False 默认值，只显示匹配度最高的内容
        - True  显示所有匹配到的内容

    Returns
    -------
    dict
        当仅找到一个匹配时，返回一个dict，包含找到的基本信息，根据不同的证券类型，找到的信息不同：
        - 股票信息：公司名、地区、行业、全名、上市状态、上市日期
        - 指数信息：指数名、全名、发行人、种类、发行日期
        - 基金：   基金名、管理人、托管人、基金类型、发行日期、发行数量、投资类型、类型
        - 期货：   期货名称
        - 期权：   期权名称

    Examples
    --------
    >>> get_basic_info('000001.SZ')
    found 1 matches, matched codes are {'E': {'000001.SZ': '平安银行'}, 'count': 1}
    More information for asset type E:
    ------------------------------------------
    ts_code       000001.SZ
    name               平安银行
    area                 深圳
    industry             银行
    fullname     平安银行股份有限公司
    list_status           L
    list_date    1991-04-03
    -------------------------------------------

    >>> get_basic_info('000001')
    found 4 matches, matched codes are {'E': {'000001.SZ': '平安银行'}, 'IDX': {'000001.CZC': '农期指数', '000001.SH': '上证指数'}, 'FD': {'000001.OF': '华夏成长'}, 'count': 4}
    More information for asset type E:
    ------------------------------------------
    ts_code       000001.SZ
    name               平安银行
    area                 深圳
    industry             银行
    fullname     平安银行股份有限公司
    list_status           L
    list_date    1991-04-03
    -------------------------------------------
    More information for asset type IDX:
    ------------------------------------------
    ts_code   000001.CZC   000001.SH
    name            农期指数        上证指数
    fullname        农期指数      上证综合指数
    publisher    郑州商品交易所        中证公司
    category        商品指数        综合指数
    list_date       None  1991-07-15
    -------------------------------------------
    More information for asset type FD:
    ------------------------------------------
    ts_code        000001.OF
    name                华夏成长
    management          华夏基金
    custodian         中国建设银行
    fund_type            混合型
    issue_date    2001-11-28
    issue_amount     32.3683
    invest_type          成长型
    type              契约型开放式
    -------------------------------------------

    >>> get_basic_info('平安银行')
    found 4 matches, matched codes are {'E': {'000001.SZ': '平安银行', '600928.SH': '西安银行'}, 'IDX': {'802613.SI': '平安银行养老新兴投资指数'}, 'FD': {'700001.OF': '平安行业先锋'}, 'count': 4}
    More information for asset type E:
    ------------------------------------------
    ts_code       000001.SZ   600928.SH
    name               平安银行        西安银行
    area                 深圳          陕西
    industry             银行          银行
    fullname     平安银行股份有限公司  西安银行股份有限公司
    list_status           L           L
    list_date    1991-04-03  2019-03-01
    -------------------------------------------
    More information for asset type IDX:
    ------------------------------------------
    ts_code       802613.SI
    name       平安银行养老新兴投资指数
    fullname   平安银行养老新兴投资指数
    publisher          申万研究
    category           价值指数
    list_date    2017-01-03
    -------------------------------------------
    More information for asset type FD:
    ------------------------------------------
    ts_code        700001.OF
    name              平安行业先锋
    management          平安基金
    custodian           中国银行
    fund_type            混合型
    issue_date    2011-08-15
    issue_amount     31.9816
    invest_type          混合型
    type              契约型开放式
    -------------------------------------------

    >>> get_basic_info('贵州钢绳', match_full_name=False)
    No match found! To get better result, you can
    - pass "match_full_name=True" to match full names of stocks and funds

    >>> get_basic_info('贵州钢绳', match_full_name=True)
    found 1 matches, matched codes are {'E': {'600992.SH': '贵绳股份'}, 'count': 1}
    More information for asset type E:
    ------------------------------------------
    ts_code       600992.SH
    name               贵绳股份
    area                 贵州
    industry            钢加工
    fullname     贵州钢绳股份有限公司
    list_status           L
    list_date    2004-05-14
    -------------------------------------------
    """
    matched_codes = match_ts_code(code_or_name, asset_types=asset_types, match_full_name=match_full_name)

    ds = qteasy.QT_DATA_SOURCE
    df_s, df_i, df_f, df_ft, df_o = ds.get_all_basic_table_data()
    asset_type_basics = {k: v for k, v in zip(AVAILABLE_ASSET_TYPES, [df_s, df_i, df_ft, df_f, df_o])}

    matched_count = matched_codes['count']
    asset_best_matched = matched_codes
    asset_codes = []
    info_columns = {'E':
                        ['name', 'area', 'industry', 'fullname', 'list_status', 'list_date'],
                    'IDX':
                        ['name', 'fullname', 'publisher', 'category', 'list_date'],
                    'FD':
                        ['name', 'management', 'custodian', 'fund_type', 'issue_date', 'issue_amount', 'invest_type',
                         'type'],
                    'FT':
                        ['name'],
                    'OPT':
                        ['name']}

    if matched_count == 1 and not printout:
        # 返回唯一信息字典
        a_type = list(asset_best_matched.keys())[0]
        basics = asset_type_basics[a_type][info_columns[a_type]]
        return basics.loc[asset_codes[0]].to_dict()

    if (matched_count == 0) and (not match_full_name):
        print(f'No match found! To get better result, you can\n'
              f'- pass "match_full_name=True" to match full names of stocks and funds')
    elif (matched_count == 0) and (asset_types is not None):
        print(f'No match found! To get better result, you can\n'
              f'- pass "asset_type=None" to match all asset types')
    elif matched_count <= 5:
        print(f'found {matched_count} matches, matched codes are {matched_codes}')
    else:
        if verbose:
            print(f'found {matched_count} matches, matched codes are:\n{matched_codes}')
        else:
            asset_matched = {at: list(matched_codes[at].keys()) for at in matched_codes if at != 'count'}
            asset_best_matched = {}
            for a_type in matched_codes:
                if a_type == 'count':
                    continue
                if asset_matched[a_type]:
                    key = asset_matched[a_type][0]
                    asset_best_matched[a_type] = {key: matched_codes[a_type][key]}
            print(f'Too many matched codes {matched_count}, best matched are\n'
                  f'{asset_best_matched}\n'
                  f'To fine tune results, you can\n'
                  f'- pass "verbose=Ture" to view all matched assets\n'
                  f'- pass "asset_type=<asset_type>" to limit hit count')
    for a_type in asset_best_matched:
        if a_type == 'count':
            continue
        if asset_best_matched[a_type]:
            print(f'More information for asset type {a_type}:\n'
                  f'------------------------------------------')
            basics = asset_type_basics[a_type][info_columns[a_type]]
            asset_codes = list(asset_best_matched[a_type].keys())
            print(basics.loc[asset_codes].T)
            print('-------------------------------------------')


def get_stock_info(code_or_name: str, asset_types=None, match_full_name=False, printout=True, verbose=False):
    """ 等同于get_basic_info()
        根据输入的信息，查找股票、基金、指数或期货、期权的基本信息

    Parameters
    ----------
    code_or_name:
        证券代码或名称，
        如果是证券代码，可以含后缀也可以不含后缀，含后缀时精确查找、不含后缀时全局匹配
        如果是证券名称，可以包含通配符模糊查找，也可以通过名称模糊查找
        如果精确匹配到一个证券代码，返回一个字典，包含该证券代码的相关信息
    asset_types:
        证券类型，接受列表或逗号分隔字符串，包含认可的资产类型：
        - E     股票
        - IDX   指数
        - FD    基金
        - FT    期货
        - OPT   期权
    match_full_name: bool
        是否匹配股票或基金的全名，默认否，如果匹配全名，耗时更长
    printout: bool
        如果为True，打印匹配到的结果
    verbose: bool
        当匹配到的证券太多时（多于五个），是否显示完整的信息
        - False 默认值，只显示匹配度最高的内容
        - True  显示所有匹配到的内容

    Returns
    -------
    dict
        当仅找到一个匹配是，返回一个dict，包含找到的基本信息，根据不同的证券类型，找到的信息不同：
        - 股票信息：公司名、地区、行业、全名、上市状态、上市日期
        - 指数信息：指数名、全名、发行人、种类、发行日期
        - 基金：   基金名、管理人、托管人、基金类型、发行日期、发行数量、投资类型、类型
        - 期货：   期货名称
        - 期权：   期权名称

    Notes
    -----
    用法示例参见：get_basic_info()

    """

    return get_basic_info(code_or_name=code_or_name,
                          asset_types=asset_types,
                          match_full_name=match_full_name,
                          printout=printout,
                          verbose=verbose)


def get_table_info(table_name, data_source=None, verbose=True):
    """ 获取并打印数据源中一张数据表的信息，包括数据量、占用磁盘空间、主键名称、内容
        以及数据列的名称、数据类型及说明

    Parameters:
    -----------
    table_name: str
        需要查询的数据表名称
    data_source: DataSource
        需要获取数据表信息的数据源，默认None，此时获取QT_DATA_SOURCE的信息
    verbose: bool, Default: True，
        是否打印完整数据列名称及类型清单

    Returns
    -------
    一个tuple，包含数据表的结构化信息：
        (table name:    str, 数据表名称
         table_exists:  bool，数据表是否存在
         table_size:    int/str，数据表占用磁盘空间，human 为True时返回容易阅读的字符串
         table_rows:    int/str，数据表的行数，human 为True时返回容易阅读的字符串
         primary_key1:  str，数据表第一个主键名称
         pk_count1:     int，数据表第一个主键记录数量
         pk_min1:       obj，数据表主键1起始记录
         pk_max1:       obj，数据表主键2最终记录
         primary_key2:  str，数据表第二个主键名称
         pk_count2:     int，数据表第二个主键记录
         pk_min2:       obj，数据表主键2起始记录
         pk_max2:       obj，数据表主键2最终记录)

    Examples
    --------
    >>> get_table_info('STOCK_BASIC')

    Out:
    <stock_basic>, 1.5MB/5K records on disc
    primary keys:
    -----------------------------------
    1:  ts_code:
        <unknown> entries
        starts: 000001.SZ, end: 873527.BJ

    columns of table:
    ------------------------------------
            columns       dtypes remarks
    0       ts_code   varchar(9)    证券代码
    1        symbol   varchar(6)    股票代码
    2          name  varchar(20)    股票名称
    3          area  varchar(10)      地域
    4      industry  varchar(10)    所属行业
    5      fullname  varchar(50)    股票全称
    6        enname  varchar(80)    英文全称
    7       cnspell  varchar(40)    拼音缩写
    8        market   varchar(6)    市场类型
    9      exchange   varchar(6)   交易所代码
    10    curr_type   varchar(6)    交易货币
    11  list_status   varchar(4)    上市状态
    12    list_date         date    上市日期
    13  delist_date         date    退市日期
    14        is_hs   varchar(2)  是否沪深港通
    """
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE
    if not isinstance(data_source, qteasy.DataSource):
        raise TypeError(f'data_source should be a DataSource, got {type(data_source)} instead.')
    return data_source.get_table_info(table=table_name, verbose=verbose)


def get_table_overview(data_source=None, tables=None, include_sys_tables=False):
    """ 显示默认数据源或指定数据源的数据总览

    Parameters
    ----------
    data_source: Object
        一个data_source 对象,默认为None，如果为None，则显示默认数据源的overview
    tables: str or list of str, Default: None
        需要显示overview的数据表名称，如果为None，则显示所有数据表的overview
    include_sys_tables: bool, Default: False
        是否显示系统数据表的overview

    Returns
    -------
    None

    Notes
    -----
    用法示例参见get_data_overview()
    """

    from .database import DataSource
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'A DataSource object must be passed, got {type(data_source)} instead.')
    return data_source.overview(tables=tables, include_sys_tables=include_sys_tables)


def get_data_overview(data_source=None, tables=None, include_sys_tables=False):
    """ 显示数据源的数据总览，等同于get_table_overview()

    获取的信息包括所有数据表的数据量、占用磁盘空间、主键名称、内容等

    Parameters
    ----------
    data_source: Object
        一个data_source 对象,默认为None，如果为None，则显示默认数据源的overview
    tables: str or list of str, Default: None
        需要显示overview的数据表名称，如果为None，则显示所有数据表的overview
    include_sys_tables: bool, Default: False
        是否显示系统数据表的overview

    Returns
    -------
    None

    Examples
    --------
    >>> get_data_overview()  # 获取当前默认数据源的数据总览

    Out:

    Analyzing local data source tables... depending on size of tables, it may take a few minutes
    [########################################]62/62-100.0%  Analyzing completed!
    db:mysql://localhost@3306/ts_db
    Following tables contain local data, to view complete list, print returned DataFrame
                     Has_data Size_on_disk Record_count Record_start  Record_end
    table
    trade_calendar     True        2.5MB         73K     1990-10-12   2023-12-31
    stock_basic        True        1.5MB          5K           None         None
    stock_names        True        1.5MB         14K     1990-12-10   2023-07-17
    stock_company      True       18.5MB          3K           None         None
    stk_managers       True      150.4MB        126K     2020-01-01   2022-07-27
    index_basic        True        3.5MB         10K           None         None
    fund_basic         True        4.5MB         17K           None         None
    future_basic       True        1.5MB          7K           None         None
    opt_basic          True       15.5MB         44K           None         None
    stock_1min         True      42.83GB      273.0M       20220318     20230710
    stock_5min         True      34.33GB      233.2M       20090105     20230710
    stock_15min        True      14.45GB      141.2M       20090105     20230710
    stock_30min        True       7.78GB       77.1M       20090105     20230710
    stock_hourly       True       4.22GB       42.0M       20090105     20230710
    stock_daily        True       1.49GB       11.6M     1990-12-19   2023-07-17
    stock_weekly       True      231.9MB        2.6M     1990-12-21   2023-07-14
    stock_monthly      True       50.6MB        635K     1990-12-31   2023-06-30
    index_1min         True       4.25GB       27.6M       20220318     20230712
    index_5min         True       6.18GB       47.2M       20090105     20230712
    index_15min        True       2.61GB       26.1M       20090105     20230712
    index_30min        True      884.0MB       12.9M       20090105     20230712
    index_hourly       True      536.0MB        7.6M       20090105     20230712
    index_daily        True      309.0MB        3.7M     1990-12-19   2023-07-10
    index_weekly       True       61.6MB        674K     1991-07-05   2023-07-14
    index_monthly      True       13.5MB        158K     1991-07-31   2023-06-30
    fund_1min          True       5.46GB       55.8M       20220318     20230712
    fund_5min          True       3.68GB       12.3M       20220318     20230712
    fund_15min         True      835.9MB        3.9M       20220318     20230712
    fund_30min         True      385.7MB        1.9M       20220318     20230712
    fund_hourly        True      124.8MB        1.6M       20210104     20230629
    fund_daily         True      129.7MB        1.6M     1998-04-07   2023-07-10
    fund_nav           True      693.0MB       13.6M     2000-01-07   2023-07-07
    fund_share         True       72.7MB        1.4M     1998-03-27   2023-07-14
    fund_manager       True      109.7MB         37K     2000-02-22   2023-03-30
    future_hourly      True         32KB           0           None         None
    future_daily       True      190.8MB        2.0M     1995-04-17   2023-07-10
    options_hourly     True         32KB           0           None         None
    options_daily      True      436.0MB        4.6M     2015-02-09   2023-07-10
    stock_adj_factor   True      897.0MB       11.8M     1990-12-19   2023-07-12
    fund_adj_factor    True       74.6MB        1.8M     1998-04-07   2023-07-12
    stock_indicator    True       2.06GB       11.8M     1999-01-01   2023-07-17
    stock_indicator2   True      734.8MB        4.1M     2017-06-14   2023-07-10
    index_indicator    True        4.5MB         45K     2004-01-02   2023-07-10
    index_weight       True      748.0MB        8.7M     2005-04-08   2023-07-14
    income             True       59.7MB        213K     1990-12-31   2023-06-30
    balance            True       97.8MB        218K     1989-12-31   2023-06-30
    cashflow           True       69.7MB        181K     1998-12-31   2023-06-30
    financial          True      289.0MB        203K     1989-12-31   2023-06-30
    forecast           True       32.6MB         98K     1998-12-31   2024-03-31
    express            True        3.5MB         23K     2004-12-31   2023-06-30
    shibor             True         16KB         212           None         None
    """

    return get_table_overview(data_source=data_source, tables=tables, include_sys_tables=include_sys_tables)


def refill_data_source(data_source=None, **kwargs):
    """ 填充数据源

    Parameters
    ----------
    data_source: DataSource, Default None
        需要填充数据的DataSource, 如果为None，则填充数据源到QT_DATA_SOURCE
    **kwargs
        DataSource.refill_local_source()的数据下载参数：
        tables: str or list of str, default: None
            需要补充的本地数据表，可以同时给出多个table的名称，逗号分隔字符串和字符串列表都合法：
            例如，下面两种方式都合法且相同：
                table='stock_indicator, stock_daily, income, stock_adj_factor'
                table=['stock_indicator', 'stock_daily', 'income', 'stock_adj_factor']
            除了直接给出表名称以外，还可以通过表类型指明多个表，可以同时输入多个类型的表：
                - 'all'     : 所有的表
                - 'cal'     : 交易日历表
                - 'basics'  : 所有的基础信息表
                - 'adj'     : 所有的复权因子表
                - 'data'    : 所有的历史数据表
                - 'events'  : 所有的历史事件表(如股票更名、更换基金经理、基金份额变动等)
                - 'report'  : 财务报表
                - 'comp'    : 指数成分表
        dtypes: str or list of str, default: None
            通过指定dtypes来确定需要更新的表单，只要包含指定的dtype的数据表都会被选中
            如果给出了tables，则dtypes参数会被忽略
        freqs: str, default: None
            通过指定tables或dtypes来确定需要更新的表单时，指定freqs可以限定表单的范围
            如果tables != all时，给出freq会排除掉freq与之不符的数据表
        asset_types: Str of List of Str, default: None
            通过指定tables或dtypes来确定需要更新的表单时，指定asset_types可以限定表单的范围
            如果tables != all时，给出asset_type会排除掉与之不符的数据表
        start_date: DateTime Like, default: None
            限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
        end_date: DateTime Like, default: None
            限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
        code_range: str or list of str, default: None
            **注意，不是所有情况下code_range参数都有效
            限定下载数据的证券代码范围，代码不需要给出类型后缀，只需要给出数字代码即可。
            可以多种形式确定范围，以下输入均为合法输入：
            - '000001'
                没有指定asset_types时，000001.SZ, 000001.SH ... 等所有代码都会被选中下载
                如果指定asset_types，只有符合类型的证券数据会被下载
            - '000001, 000002, 000003'
            - ['000001', '000002', '000003']
                两种写法等效，列表中列举出的证券数据会被下载
            - '000001:000300'
                从'000001'开始到'000300'之间的所有证券数据都会被下载
        merge_type: str, default: 'ignore'
            数据混合方式，当获取的数据与本地数据的key重复时，如何处理重复的数据：
            - 'ignore' 默认值，不下载重复的数据
            - 'update' 下载并更新本地数据的重复部分
        reversed_par_seq: Bool, default: False
            是否逆序参数下载数据， 默认False
            - True:  逆序参数下载数据
            - False: 顺序参数下载数据
        parallel: Bool, default: True
            是否启用多线程下载数据，默认True
            - True:  启用多线程下载数据
            - False: 禁用多线程下载
        process_count: int, default: None
            启用多线程下载时，同时开启的线程数，默认值为设备的CPU核心数
        chunk_size: int, default: 100
            保存数据到本地时，为了减少文件/数据库读取次数，将下载的数据累计一定数量后
            再批量保存到本地，chunk_size即批量，默认值100

    Returns
    -------
    None

    """
    from .database import DataSource
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'A DataSource object must be passed, got {type(data_source)} instead.')
    print(f'Filling data source {data_source} ...')
    data_source.refill_local_source(**kwargs)


def get_history_data(htypes,
                     shares=None,
                     symbols=None,
                     start=None,
                     end=None,
                     freq=None,
                     rows=10,
                     asset_type=None,
                     adj=None,
                     as_data_frame=None,
                     group_by=None,
                     **kwargs):
    """ 从本地DataSource（数据库/csv/hdf/fth）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

    Parameters
    ----------
    htypes: [str, list]
        需要获取的历史数据类型集合，可以是以逗号分隔的数据类型字符串或者数据类型字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     'open, high, low, close'
         - list:    ['open', 'high', 'low', 'close']
        特殊htypes的处理：
        以下特殊htypes将被特殊处理"
         - wt-000300.SH:
            指数权重数据，如果htype是一个wt开头的复合体，则获取该指数的股票权重数据
            获取的数据的htypes同样为wt-000300.SH型
         - close-000300.SH:
            给出一个htype和ts_code的复合体，且shares为None时，返回不含任何share
            的参考数据
    shares: [str, list] 等同于symbols
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
         - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
    symbols: [str, list] 等同于shares
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
        - str:     '000001, 000002, 000004, 000005'
        - list:    ['000001', '000002', '000004', '000005']
    start: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
    end: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
    rows: int, default: 10
        获取的历史数据的行数，如果指定了start和end，则忽略此参数，且获取的数据的时间范围为[start, end]
        如果未指定start和end，则获取数据表中最近的rows条数据，使用row来获取数据时，速度比使用日期慢得多
    freq: str
        获取的历史数据的频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
    asset_type: str, list
        限定获取的数据中包含的资产种类，包含以下选项或下面选项的组合，合法的组合方式包括
        逗号分隔字符串或字符串列表，例如: 'E, IDX' 和 ['E', 'IDX']都是合法输入
         - any: 可以获取任意资产类型的证券数据(默认值)
         - E:   只获取股票类型证券的数据
         - IDX: 只获取指数类型证券的数据
         - FT:  只获取期货类型证券的数据
         - FD:  只获取基金类型证券的数据
    adj: str
        对于某些数据，可以获取复权数据，需要通过复权因子计算，复权选项包括：
         - none / n: 不复权(默认值)
         - back / b: 后复权
         - forward / fw / f: 前复权
    as_data_frame: bool, Default: False
        是否返回DataFrame对象，True时返回HistoryPanel对象
    group_by: str, 默认'shares'
        如果返回DataFrame对象，设置dataframe的分组策略
        - 'shares' / 'share' / 's': 每一个share组合为一个dataframe
        - 'htypes' / 'htype' / 'h': 每一个htype组合为一个dataframe
    **kwargs:
        用于生成trade_time_index的参数，包括：
        drop_nan: bool
            是否保留全NaN的行
        resample_method: str
            如果数据需要升频或降频时，调整频率的方法
            调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
            数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
            例如，合并下列数据(每一个tuple合并为一个数值，?表示合并后的数值）
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(?), (?), (?)]
            数据合并方法:
            - 'last'/'close': 使用合并区间的最后一个值。如：
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
            - 'first'/'open': 使用合并区间的第一个值。如：
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
            - 'max'/'high': 使用合并区间的最大值作为合并值：
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
            - 'min'/'low': 使用合并区间的最小值作为合并值：
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
            - 'avg'/'mean': 使用合并区间的平均值作为合并值：
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]
            - 'sum'/'total': 使用合并区间的平均值作为合并值：
                [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]

            数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
            例如，填充下列数据(?表示插入的数据）
                [1, 2, 3] 填充后变为: [?, 1, ?, 2, ?, 3, ?]
            缺失数据的填充方法如下:
            - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN。如：
                [1, 2, 3] 填充后变为: [NaN, 1, 1, 2, 2, 3, 3]
            - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN。如：
                [1, 2, 3] 填充后变为: [1, 1, 2, 2, 3, 3, NaN]
            - 'nan': 使用NaN值填充缺失数据：
                [1, 2, 3] 填充后变为: [NaN, 1, NaN, 2, NaN, 3, NaN]
            - 'zero': 使用0值填充缺失数据：
                [1, 2, 3] 填充后变为: [0, 1, 0, 2, 0, 3, 0]
        b_days_only: bool 默认True
            是否强制转换自然日频率为工作日，即：
            'D' -> 'B'
            'W' -> 'W-FRI'
            'M' -> 'BM'
        trade_time_only: bool, 默认True
            为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
        include_start:
            日期时间序列是否包含开始日期/时间
        include_end:
            日期时间序列是否包含结束日期/时间
        start_am:
            早晨交易时段的开始时间
        end_am:
            早晨交易时段的结束时间
        include_start_am:
            早晨交易时段是否包括开始时间
        include_end_am:
            早晨交易时段是否包括结束时间
        start_pm:
            下午交易时段的开始时间
        end_pm:
            下午交易时段的结束时间
        include_start_pm
            下午交易时段是否包含开始时间
        include_end_pm
            下午交易时段是否包含结束时间

    Returns
    -------
    HistoryPanel:
        如果设置as_data_frame为False，则返回一个HistoryPanel对象
    Dict of DataFrame:
        如果设置as_data_frame为True，则返回一个Dict，其值为多个DataFrames

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.get_history_data(htypes='open, high, low, close, vol', shares='000001.SZ', start='20191225', end='20200110')
    {'000001.SZ':
                  open   high    low  close         vol
     2019-12-25  16.45  16.56  16.24  16.30   414917.98
     2019-12-26  16.34  16.48  16.32  16.47   372033.86
     2019-12-27  16.53  16.93  16.43  16.63  1042574.72
     2019-12-30  16.46  16.63  16.10  16.57   976970.31
     2019-12-31  16.57  16.63  16.31  16.45   704442.25
     2020-01-02  16.65  16.95  16.55  16.87  1530231.87
     2020-01-03  16.94  17.31  16.92  17.18  1116194.81
     2020-01-06  17.01  17.34  16.91  17.07   862083.50
     2020-01-07  17.13  17.28  16.95  17.15   728607.56
     2020-01-08  17.00  17.05  16.63  16.66   847824.12
     2020-01-09  16.81  16.93  16.53  16.79  1031636.65
     2020-01-10  16.79  16.81  16.52  16.69   585548.45
     }
     # data can be extracted in different frequency, and also adjusted
     >>> qt.get_history_data(htypes='open, high, low, close', shares='000001.SZ', start='20191229', end='20200106', freq='H', adj='b', asset_type='E')
     {'000001.SZ':
                                open        high         low       close
     2019-12-30 10:00:00  1796.92174  1796.92174  1796.92174  1796.92174
     2019-12-30 11:00:00  1790.37160  1800.19681  1758.71259  1786.00484
     2019-12-30 14:00:00  1811.11371  1813.29709  1795.83005  1806.74695
     2019-12-30 15:00:00  1805.65526  1808.93033  1793.64667  1808.93033
     2019-12-31 10:00:00  1808.93033  1808.93033  1808.93033  1808.93033
     2019-12-31 11:00:00  1806.74695  1806.74695  1780.54639  1788.18822
     2019-12-31 14:00:00  1786.00484  1788.18822  1781.63808  1786.00484
     2019-12-31 15:00:00  1786.00484  1796.92174  1783.82146  1795.83005
     2020-01-02 10:00:00  1817.66385  1817.66385  1817.66385  1817.66385
     2020-01-02 11:00:00  1819.84723  1848.23117  1807.83864  1840.58934
     2020-01-02 14:00:00  1842.77272  1847.13948  1828.58075  1843.86441
     2020-01-02 15:00:00  1843.86441  1844.95610  1836.22258  1841.68103
     2020-01-03 10:00:00  1849.32286  1849.32286  1849.32286  1849.32286
     2020-01-03 11:00:00  1849.32286  1879.89018  1849.32286  1877.70680
     2020-01-03 14:00:00  1863.51483  1889.71539  1863.51483  1884.25694
     2020-01-03 15:00:00  1884.25694  1884.25694  1872.24835  1875.52342
     }
     # if you want data to be filled also in non-trading days
     >>> qt.get_history_data(htypes='open, high, low, close, vol', shares='000001.SZ', start='20191225', end='20200105', b_days_only=False)
    {'000001.SZ':
                  open   high    low  close         vol
     2019-12-25  16.45  16.56  16.24  16.30   414917.98
     2019-12-26  16.34  16.48  16.32  16.47   372033.86
     2019-12-27  16.53  16.93  16.43  16.63  1042574.72
     2019-12-28  16.53  16.93  16.43  16.63  1042574.72
     2019-12-29  16.53  16.93  16.43  16.63  1042574.72
     2019-12-30  16.46  16.63  16.10  16.57   976970.31
     2019-12-31  16.57  16.63  16.31  16.45   704442.25
     2020-01-01  16.57  16.63  16.31  16.45   704442.25
     2020-01-02  16.65  16.95  16.55  16.87  1530231.87
     2020-01-03  16.94  17.31  16.92  17.18  1116194.81
     2020-01-04  16.94  17.31  16.92  17.18  1116194.81
     2020-01-05  16.94  17.31  16.92  17.18  1116194.81}
    """

    if htypes is None:
        raise ValueError(f'htype should not be None')
    if symbols is not None and shares is None:
        shares = symbols
    if shares is None:
        shares = qteasy.QT_CONFIG.asset_pool

    one_year = pd.Timedelta(365, 'd')
    one_week = pd.Timedelta(7, 'd')

    if (start is None) and (end is None) and (rows is None):
        end = pd.to_datetime('today').date()
        start = end - one_year
    elif (start is None) and (end is None):
        rows = int(rows)
    elif start is None:
        try:
            end = pd.to_datetime(end)
        except Exception:
            raise Exception(f'end date can not be converted to a datetime')
        start = end - one_year
        rows = None
    elif end is None:
        try:
            start = pd.to_datetime(start)
        except Exception:
            raise Exception(f'start date can not be converted to a datetime')
        end = start + one_year
        rows = None
    else:
        try:
            start = pd.to_datetime(start)
            end = pd.to_datetime(end)
        except Exception:
            raise Exception(f'start and end must be both datetime like')
        if end - start <= one_week:
            raise ValueError(f'End date should be at least one week after start date')
        rows = None

    if freq is None:
        freq = 'd'

    if asset_type is None:
        asset_type = 'any'

    if adj is None:
        adj = 'n'

    if as_data_frame is None:
        as_data_frame = True

    if group_by is None:
        group_by = 'shares'
    if group_by in ['shares', 'share', 's']:
        group_by = 'shares'
    elif group_by in ['htypes', 'htype', 'h']:
        group_by = 'htypes'
    hp = get_history_panel(htypes=htypes, shares=shares, start=start, end=end, freq=freq, asset_type=asset_type,
                           symbols=symbols, rows=rows, adj=adj, **kwargs)

    if as_data_frame:
        return hp.unstack(by=group_by)
    else:
        return hp


# TODO: 在这个函数中对config的各项参数进行检查和处理，将对各个日期的检查和更新（如交易日调整等）放在这里，直接调整
#  config参数，使所有参数直接可用。并发出warning，不要在后续的使用过程中调整参数
def is_ready(**kwargs):
    """ 检查QT_CONFIG以及Operator对象，确认qt.run()是否具备基本运行条件

    Parameters
    ----------
    kwargs:

    Returns
    -------
    """
    # 检查各个cash_amounts与各个cash_dates是否能生成正确的CashPlan对象

    # 检查invest(loop)、opti、test等几个start与end日期是否冲突

    # 检查invest(loop)、opti、test等几个cash_dates是否冲突

    return True


def info(**kwargs):
    """ qteasy 模块的帮助信息入口函数

    Parameters
    ----------
    kwargs:

    Returns
    -------
    """
    raise NotImplementedError


def help(**kwargs):
    """ qteasy 模块的帮助信息入口函数

    Parameters
    ----------
    kwargs:

    Returns
    -------
    """
    raise NotImplementedError


def configure(config=None, reset=False, only_built_in_keys=True, **kwargs):
    """ 配置qteasy的运行参数QT_CONFIG

    Parameters
    ----------
    config: ConfigDict 对象
        需要设置或调整参数的config对象，默认为None，此时直接对QT_CONFIG对象设置参数
    reset: bool
        默认值为False，为True时忽略传入的kwargs，将所有的参数设置为默认值
    only_built_in_keys: bool
        默认值False，如果为True，仅允许传入内部参数，False时允许传入任意参数
    **kwargs:
        需要设置的所有参数

    Returns
    -------
    None

    Notes
    -----
    使用get_config()或configuration()查看当前的QT_CONFIG参数

    Examples
    --------
    >>> configure(reset=True)  # 将QT_CONFIG参数设置为默认值
    >>> configure(invest_cash_amounts=[10000, 20000, 30000], invest_cash_dates=['2018-01-01', '2018-02-01', '2018-03-01'])
    >>> get_config('invest_cash_amounts, invest_cash_dates')
    No. Config-Key            Cur Val                       Default val
    -------------------------------------------------------------------
    1   invest_cash_amounts   [10000, 20000, 30000]         <[100000.0]>
    2   invest_cash_dates     ['2018-01-01', '2018-02-01'...<None>

    """
    if config is None:
        set_config = QT_CONFIG
    else:
        assert isinstance(config, ConfigDict), TypeError(f'config should be a ConfigDict, got {type(config)}')
        set_config = config
    if not reset:
        _update_config_kwargs(set_config, kwargs, raise_if_key_not_existed=only_built_in_keys)
    else:
        from qteasy._arg_validators import _valid_qt_kwargs
        default_kwargs = {k: v['Default'] for k, v in zip(_valid_qt_kwargs().keys(),
                                                          _valid_qt_kwargs().values())}
        _update_config_kwargs(set_config, default_kwargs, raise_if_key_not_existed=True)


def set_config(config=None, reset=False, only_built_in_keys=True, **kwargs):
    """ 配置qteasy的运行参数QT_CONFIG，等同于configure()

    Parameters
    ----------
    config: ConfigDict 对象
        需要设置或调整参数的config对象，默认为None，此时直接对QT_CONFIG对象设置参数
    reset: bool
        默认值为False，为True时忽略传入的kwargs，将所有的参数设置为默认值
    only_built_in_keys: bool
        默认值False，如果为True，仅允许传入内部参数，False时允许传入任意参数
    **kwargs:
        需要设置的所有参数

    Returns
    -------
    None

    Examples
    --------
    参见 configure()
    """

    return configure(config=config, reset=reset, only_built_in_keys=only_built_in_keys, **kwargs)


def configuration(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Notes
    -----
    使用示例参见get_config()
    """
    assert isinstance(level, int) and (0 <= level <= 5), f'InputError, level should be an integer, got {type(level)}'
    assert isinstance(up_to, int) and (0 <= up_to <= 5), f'InputError, up_to level should be an integer, ' \
                                                         f'got {type(up_to)}'
    if up_to <= level:
        up_to = level
    if up_to == level:
        level = level
    else:
        level = list(range(level, up_to + 1))

    if config_key is None:
        kwargs = QT_CONFIG
    else:
        if isinstance(config_key, str):
            config_key = str_to_list(config_key)
        if not isinstance(config_key, list):
            raise TypeError(f'config_key should be a string or list of strings, got {type(config_key)}')
        assert all(isinstance(item, str) for item in config_key)
        kwargs = {key: QT_CONFIG[config_key] for key in config_key}
        level = [0, 1, 2, 3, 4, 5]
    print(_vkwargs_to_text(kwargs=kwargs, level=level, info=default, verbose=verbose))


def get_configurations(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，与get_config / configuration 相同

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Examples
    --------
    使用示例参见get_config()
    """

    return configuration(config_key=config_key, level=level, up_to=up_to, default=default, verbose=verbose)


def get_config(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，与get_config / configuration 相同

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Examples
    --------
    >>> get_config('local_data_source')
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   local_data_source     database       <file>

    >>> get_config('local_data_source, local_data_file_type, local_data_file_path')
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   local_data_source     database       <file>
    2   local_data_file_type  csv            <csv>
    3   local_data_file_path  data/          <data/>

    >>> get_config(level=0, up_to=2)
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   mode                  1              <1>
    2   time_zone             Asia/Shanghai  <Asia/Shanghai>
    3   asset_pool            000300.SH      <000300.SH>
    4   asset_type            IDX            <IDX>
    5   live_trade_account_id None           <None>
    6   live_trade_account    None           <None>
    7   live_trade_debug_mode False          <False>
    8   live_trade_init_cash  1000000.0      <1000000.0>
    ... (more rows)

    >>> get_config(level=0, up_to=1, verbose=True)
    No. Config-Key            Cur Val        Default val
          Description
    ----------------------------------------------------
    1   mode                  1              <1>
          qteasy 的运行模式:
          0: 实盘运行模式
          1: 回测-评价模式
          2: 策略优化模式
          3: 统计预测模式
    2   time_zone             Asia/Shanghai  <Asia/Shanghai>
          回测时的时区，可以是任意时区，例如：
          Asia/Shanghai
          Asia/Hong_Kong
          US/Eastern
          US/Pacific
          Europe/London
          Europe/Paris
          Australia/Sydney
          Australia/Melbourne
          Pacific/Auckland
          Pacific/Chatham
          etc.
    3   asset_pool            000300.SH      <000300.SH>
          可用投资产品池，投资组合基于池中的产品创建
    4   asset_type            IDX            <IDX>
          投资产品的资产类型，包括：
          IDX  : 指数
          E    : 股票
          FT   : 期货
          FD   : 基金
    """

    return configuration(config_key=config_key, level=level, up_to=up_to, default=default, verbose=verbose)


def _check_config_file_name(file_name, allow_default_name=False):
    """ 检查配置文件名是否合法，如果合法或可以转化为合法，返回合法文件名，否则raise

    parameters
    ----------
    file_name: str
        配置文件名，可以是一个文件名，也可以是不带后缀的文件名，不可以是一个路径
    allow_default_name: bool
        是否允许使用默认的配置文件名qteasy.cfg
    """

    if file_name is None:
        file_name = 'saved_config.cfg'
    if not isinstance(file_name, str):
        raise TypeError(f'file_name should be a string, got {type(file_name)} instead.')
    import re
    if re.match('[a-zA-Z_]\w+$', file_name):
        file_name = file_name + '.cfg'  # add .cfg suffix if not given
    if not re.match('[a-zA-Z_]\w+\.cfg$', file_name):
        raise ValueError(f'invalid file name given: {file_name}')
    if (file_name == 'qteasy.cfg') and (not allow_default_name):
        # TODO: 实现将环境变量写入qteasy.cfg初始配置文件的功能
        raise NotImplementedError(f'functionality not implemented yet, please use another file name.')
    return file_name


def save_config(config=None, file_name=None, overwrite=True, initial_config=False):
    """ 将config保存为一个文件
    TODO: 尚未实现的功能：如果initial_config为True，则将配置更新到初始化配置文件qteasy.cfg中()

    Parameters
    ----------
    config: ConfigDict or dict, Default: None
        一个config对象或者包含配置环境变量的dict，如果为None，则保存qt.QT_CONFIG
    file_name: str, Default: None
        文件名，如果为None，文件名为"saved_config.cfg"
    overwrite: bool, Default: True
        默认True，覆盖重名文件，如果为False，当保存的文件已存在时，将报错
    initial_config: bool, Default: False ** FUNCTIONALITY NOT IMPLEMENTED **
        保存环境变量到初始配置文件 qteasy.cfg 中，如果qteasy.cfg中已经存在部分环境变量了，则覆盖相关环境变量

    Returns
    -------
    None
    """

    from qteasy import logger_core
    from qteasy import QT_ROOT_PATH
    import pickle
    import os

    if config is None:
        config = QT_CONFIG
    if not isinstance(config, (ConfigDict, dict)):
        raise TypeError(f'config should be a ConfigDict or a dict, got {type(config)} instead.')

    file_name = _check_config_file_name(file_name=file_name, allow_default_name=initial_config)

    config_path = os.path.join(QT_ROOT_PATH, 'config/')
    if not os.path.exists(config_path):
        os.makedirs(config_path, exist_ok=False)
    if overwrite:
        open_method = 'wb'  # overwrite the file
    else:
        open_method = 'xb'  # raise if file already existed
    with open(os.path.join(config_path, file_name), open_method) as f:
        try:
            pickle.dump(config, f, pickle.HIGHEST_PROTOCOL)
            logger_core.info(f'config file content written to: {f.name}')
        except Exception as e:
            logger_core.warning(f'{e}, error during writing config to local file.')


def load_config(config=None, file_name=None):
    """ 从文件file_name中读取相应的config参数，写入到config中，如果config为
        None，则保存参数到QT_CONFIG中

    Parameters
    ----------
    config: ConfigDict 对象
        一个config对象，默认None，如果为None，则保存QT_CONFIG
    file_name: str
        文件名，默认None，如果为None，文件名为saved_config.cfg

    Returns
    -------
    None
    """
    from qteasy import logger_core
    from qteasy import QT_ROOT_PATH
    import pickle

    if config is None:
        config = QT_CONFIG
    if not isinstance(config, ConfigDict):
        raise TypeError(f'config should be a ConfigDict, got {type(config)} instead.')

    file_name = _check_config_file_name(file_name=file_name, allow_default_name=False)

    config_path = os.path.join(QT_ROOT_PATH, 'config/')
    try:
        with open(os.path.join(config_path, file_name), 'rb') as f:
            saved_config = pickle.load(f)
            logger_core.info(f'read configuration file: {f.name}')
    except FileNotFoundError as e:
        logger_core.warning(f'{e}\nError during loading configuration {file_name}! nothing will be read.')
        saved_config = {}

    configure(config=config,
              only_built_in_keys=False,
              **saved_config)


def view_config_files(details=False):
    """ 查看已经保存的配置文件，并显示其主要内容

    Parameters
    ----------
    details: bool, Default: False
        是否显示配置文件的详细内容

    Returns
    -------
    None

    Notes
    -----
    该函数只显示config文件夹下的配置文件，不显示qteasy.cfg中的配置
    """

    # TODO: Implement this function and add unittests
    raise NotImplementedError


def reset_config(config=None):
    """ 重设config对象，将所有的参数都设置为默认值
        如果config为None，则重设qt.QT_CONFIG

    Parameters
    ----------
    config: ConfigDict
        需要重设的config对象

    Returns
    -------
    None

    Notes
    -----
    等同于调用configure(config, reset=True)
    """
    from qteasy import logger_core
    if config is None:
        config = QT_CONFIG
    if not isinstance(config, ConfigDict):
        raise TypeError(f'config should be a ConfigDict, got {type(config)} instead.')
    logger_core.info(f'{config} is now reset to default values.')
    configure(config, reset=True)


# TODO: Bug检查：
#   在使用AlphaSel策略，如下设置参数时，会产生数据长度不足错误：
#   strategy_run_freq='m',
#   data_freq='m',
#   window_length=6,
def check_and_prepare_hist_data(oper, config, datasource=None):
    """ 根据config参数字典中的参数，下载或读取所需的历史数据以及相关的投资资金计划

    Parameters
    ----------
    oper: Operator，
        需要设置数据的Operator对象
    config: ConfigDict
        用于设置Operator对象的环境参数变量
    datasource: DataSource
        用于下载数据的DataSource对象

    Returns
    -------
    hist_op: HistoryPanel,
        用于回测模式下投资策略生成的历史数据区间，包含多只股票的多种历史数据
    hist_ref: HistoryPanel,
        用于回测模式下投资策略生成的历史参考数据
    back_trade_prices: HistoryPanel,
        用于回测模式投资策略回测的交易价格数据
    hist_opti: HistoryPanel,
        用于优化模式下生成投资策略的历史数据，包含股票的历史数，时间上涵盖优化与测试区间
    hist_opti_ref: HistoryPanel,
        用于优化模式下生成投资策略的参考数据，包含所有股票、涵盖优化与测试区间
    opti_trade_prices: pd.DataFrame,
        用于策略优化模式下投资策略优化结果的回测，作为独立检验数据
    hist_benchmark: pd.DataFrame,
        用于评价回测结果的同期基准收益曲线，一般为股票指数如HS300指数同期收益曲线
    invest_cash_plan: CashPlan,
        用于回测模式的资金投入计划
    opti_cash_plan: CashPlan,
        用于优化模式下，策略优化区间的资金投入计划
    test_cash_plan: CashPlan,
        用于优化模式下，策略测试区间的资金投入计划
    """
    run_mode = config['mode']
    # 如果run_mode=0，设置历史数据的开始日期为window length，结束日期为当前日期
    current_datetime = datetime.datetime.now()
    # 根据不同的运行模式，设定不同的运行历史数据起止日期
    # 投资回测区间的开始日期根据invest_start和invest_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['invest_cash_dates'] is None:
        invest_start = next_market_trade_day(config['invest_start']).strftime('%Y%m%d')
        invest_cash_plan = CashPlan(invest_start,
                                    config['invest_cash_amounts'][0],
                                    config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['invest_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        invest_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                    amounts=config['invest_cash_amounts'],
                                    interest_rate=config['riskfree_ir'])
        invest_start = regulate_date_format(invest_cash_plan.first_day)
        if pd.to_datetime(invest_start) != pd.to_datetime(config['invest_start']):
            warn(f'first cash investment on {invest_start} differ from invest_start {config["invest_start"]}, first cash'
                 f' date will be used!',
                 RuntimeWarning)
    # 按照同样的逻辑设置优化区间和测试区间的起止日期
    # 优化区间开始日期根据opti_start和opti_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['opti_cash_dates'] is None:
        opti_start = next_market_trade_day(config['opti_start']).strftime('%Y%m%d')
        opti_cash_plan = CashPlan(opti_start,
                                  config['opti_cash_amounts'][0],
                                  config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['opti_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        opti_cash_plan = CashPlan(dates=adjusted_cash_dates,
                                  amounts=config['opti_cash_amounts'],
                                  interest_rate=config['riskfree_ir'])
        opti_start = regulate_date_format(opti_cash_plan.first_day)
        if pd.to_datetime(opti_start) != pd.to_datetime(config['opti_start']):
            warn(f'first cash investment on {opti_start} differ from invest_start {config["opti_start"]}, first cash'
                 f' date will be used!',
                 RuntimeWarning)

    # 测试区间开始日期根据opti_start和opti_cash_dates两个参数确定，后一个参数非None时，覆盖前一个参数
    if config['test_cash_dates'] is None:
        test_start = next_market_trade_day(config['test_start']).strftime('%Y%m%d')
        test_cash_plan = CashPlan(
                test_start,
                config['test_cash_amounts'][0],
                config['riskfree_ir'])
    else:
        cash_dates = str_to_list(config['test_cash_dates'])
        adjusted_cash_dates = [next_market_trade_day(date) for date in cash_dates]
        test_cash_plan = CashPlan(
                dates=adjusted_cash_dates,
                amounts=config['test_cash_amounts'],
                interest_rate=config['riskfree_ir'])
        test_start = regulate_date_format(test_cash_plan.first_day)
        if pd.to_datetime(test_start) != pd.to_datetime(config['test_start']):
                warn(f'first cash investment on {test_start} differ from invest_start {config["test_start"]}, first cash'
                     f' date will be used!',
                     RuntimeWarning)

    # 设置历史数据前置偏移，以便有足够的历史数据用于生成最初的信号
    window_length = oper.max_window_length
    window_offset_freq = oper.op_data_freq
    if isinstance(window_offset_freq, list):
        raise NotImplementedError(f'There are more than one data frequencies in operator ({window_offset_freq}), '
                                  f'multiple data frequency in one operator is currently not supported')
    if window_offset_freq.lower() not in ['d', 'w', 'm', 'q', 'y']:
        from qteasy.utilfuncs import parse_freq_string
        duration, base_unit, _ = parse_freq_string(window_offset_freq, std_freq_only=True)
        # print(f'[DEBUG]: in core.py function check_and_prepare_hist_data(), '
        #       f'window_offset_freq is {window_offset_freq}\n'
        #       f'it should be converted to {duration} {base_unit}, '
        #       f'and window_length and window_offset_freq should be \n'
        #       f'adjusted accordingly: \n'
        #       f'window_length: {window_length} -> {window_length * duration * 3}\n'
        #       f'window_offset_freq: {window_offset_freq} -> {base_unit}')
        window_length *= duration * 10  # 临时处理措施，由于交易时段不连续，仅仅前推一个周期可能会导致数据不足
        window_offset_freq = base_unit
    window_offset = pd.Timedelta(int(window_length * 1.6), window_offset_freq)

    # 设定投资结束日期
    if run_mode == 0:
        # 实时模式下，设置结束日期为现在，并下载最新的数据（下载的数据仅包含最小所需）
        invest_end = regulate_date_format(current_datetime)
        # 开始日期时间为现在往前推window_offset
        invest_start = regulate_date_format(current_datetime - window_offset)
    else:
        invest_end = config['invest_end']
        invest_start = regulate_date_format(pd.to_datetime(invest_start) - window_offset)

    # debug
    # 检查invest_start是否正确地被前溯了window_offset
    # print(f'[DEBUG]: in core.py function check_and_prepare_hist_data(), extracting data from window_length earlier '
    #       f'than invest_start: \n'
    #       f'current run mode: {run_mode}\n'
    #       f'current_date = {current_datetime}\n'
    #       f'window_offset = {window_offset}\n'
    #       f'invest_start = {invest_start}\n'
    #       f'invest_end = {invest_end}\n')
    # 设置优化区间和测试区间的结束日期
    opti_end = config['opti_end']
    test_end = config['test_end']

    # 优化/测试数据是合并读取的，因此设置一个统一的开始/结束日期：
    # 寻优开始日期为优化开始和测试开始日期中较早者，寻优结束日期为优化结束和测试结束日期中较晚者
    opti_test_start = opti_start if pd.to_datetime(opti_start) < pd.to_datetime(test_start) else test_start
    opti_test_end = opti_end if pd.to_datetime(opti_end) > pd.to_datetime(test_end) else test_end

    # 合并生成交易信号和回测所需历史数据，数据类型包括交易信号数据和回测价格数据
    hist_op = get_history_panel(
            htypes=oper.all_price_and_data_types,
            shares=config['asset_pool'],
            start=invest_start,
            end=invest_end,
            freq=oper.op_data_freq,
            asset_type=config['asset_type'],
            adj=config['backtest_price_adj'] if run_mode > 0 else 'none',
            data_source=datasource,
    ) if run_mode <= 1 else HistoryPanel()  # TODO: 当share较多时，运行速度非常慢，需要优化
    # 解析参考数据类型，获取参考数据
    hist_ref = get_history_panel(
            htypes=oper.op_ref_types,
            shares=None,
            start=regulate_date_format(pd.to_datetime(invest_start) - window_offset),  # TODO: 已经offset过了，为什么还要offset？
            end=invest_end,
            freq=oper.op_data_freq,
            asset_type='IDX',
            adj='none',
            data_source=datasource,
    ) if run_mode <= 1 else HistoryPanel()
    # 生成用于数据回测的历史数据，格式为HistoryPanel，包含用于计算交易结果的所有历史价格种类
    bt_price_types = oper.strategy_timings
    back_trade_prices = hist_op.slice(htypes=bt_price_types)
    # fill np.inf in back_trade_prices to prevent from result in nan in value
    back_trade_prices.fillinf(0)

    # 生成用于策略优化训练的训练和测试历史数据集合和回测价格类型集合
    hist_opti = get_history_panel(
            htypes=oper.all_price_and_data_types,
            shares=config['asset_pool'],
            start=regulate_date_format(pd.to_datetime(opti_test_start) - window_offset),
            end=opti_test_end,
            freq=oper.op_data_freq,
            asset_type=config['asset_type'],
            adj=config['backtest_price_adj'],
            data_source=datasource,
    ) if run_mode == 2 else HistoryPanel()

    # 生成用于优化策略测试的测试历史数据集合
    hist_opti_ref = get_history_panel(
            htypes=oper.op_ref_types,
            shares=None,
            start=regulate_date_format(pd.to_datetime(opti_test_start) - window_offset),
            end=opti_test_end,
            freq=oper.op_data_freq,
            asset_type=config['asset_type'],
            adj=config['backtest_price_adj'],
            data_source=datasource,
    ) if run_mode == 2 else HistoryPanel()

    opti_trade_prices = hist_opti.slice(htypes=bt_price_types)
    opti_trade_prices.fillinf(0)

    # 生成参考历史数据，作为参考用于回测结果的评价
    # 评价数据的历史区间应该覆盖invest/opti/test的数据区间
    all_starts = [pd.to_datetime(date_str) for date_str in [invest_start, opti_start, test_start]]
    all_ends = [pd.to_datetime(date_str) for date_str in [invest_end, opti_end, test_end]]
    benchmark_start = regulate_date_format(min(all_starts))
    benchmark_end = regulate_date_format(max(all_ends))

    hist_benchmark = get_history_panel(
            htypes=config['benchmark_dtype'],
            shares=config['benchmark_asset'],
            start=benchmark_start,
            end=benchmark_end,
            freq=oper.op_data_freq,
            asset_type=config['benchmark_asset_type'],
            adj=config['backtest_price_adj'],
            data_source=datasource,
    ).slice_to_dataframe(htype=config['benchmark_dtype'])

    return hist_op, hist_ref, back_trade_prices, hist_opti, hist_opti_ref, opti_trade_prices, hist_benchmark, \
           invest_cash_plan, opti_cash_plan, test_cash_plan


def reconnect_ds(data_source=None):
    """ （当数据库连接超时时）重新连接到data source，如果不指定具体的data_source，则重新连接默认数据源

    Parameters
    ----------
    data_source:
        需要重新连接的datasource对象

    Returns
    -------
    """
    if data_source is None:
        data_source = qteasy.QT_DATA_SOURCE

    if not isinstance(data_source, qteasy.DataSource):
        raise TypeError(f'data source not recognized!')

    # reconnect twice to make sure the connection is established
    data_source.reconnect()
    data_source.reconnect()


def check_and_prepare_live_trade_data(operator, config, datasource=None, live_prices=None):
    """ 在run_mode == 0的情况下准备相应的历史数据

    Parameters
    ----------
    operator: Operator
        需要设置数据的Operator对象
    config: ConfigDict
        用于设置Operator对象的环境参数变量
    datasource: DataSource
        用于下载数据的DataSource对象
    live_prices: pd.DataFrame, optional
        用于实盘交易的最新价格数据，如果不提供，则从datasource中下载获取

    Returns
    -------
    hist_op: HistoryPanel
        用于回测的历史数据，包含用于计算交易结果的所有历史价格种类
    hist_ref: HistoryPanel
        用于回测的历史参考数据，包含用于计算交易结果的所有历史参考数据
    """

    run_mode = config['mode']
    if run_mode != 0:
        raise ValueError(f'run_mode should be 0, but {run_mode} is given!')
    # 合并生成交易信号和回测所需历史数据，数据类型包括交易信号数据和回测价格数据
    hist_op = get_history_panel(
            htypes=operator.all_price_and_data_types,
            shares=config['asset_pool'],
            rows=operator.max_window_length,
            freq=operator.op_data_freq,
            asset_type=config['asset_type'],
            adj='none',
            data_source=datasource,
    )  # TODO: this function get_history_panel() is extremely slow, need to be optimized

    # 解析参考数据类型，获取参考数据
    hist_ref = get_history_panel(
            htypes=operator.op_ref_types,
            shares=None,
            rows=operator.max_window_length,
            freq=operator.op_data_freq,
            asset_type=config['asset_type'],
            adj='none',
            data_source=datasource,
    )
    if any(
            (stg.strategy_run_freq.upper() in ['D', 'W', 'M']) and
            stg.use_latest_data_cycle
            for stg
            in operator.strategies
    ):  # 如果有任何一个策略需要估算当前周期的数据
        # 从hist_op的index中找到日期序列，最后一个日期是prev_cycle_end, 根据日期序列计算本cycle的开始和结束日期
        prev_cycle_date = hist_op.hdates[-1]

        latest_cycle_date = next_market_trade_day(
                prev_cycle_date,
                nearest_only=False,
        )

        extended_op_values = np.zeros(shape=(hist_op.shape[0], 1, hist_op.shape[2]))
        extended_ref_values = np.zeros(shape=(hist_ref.shape[0], 1, hist_ref.shape[2]))
        # 如果需要估算当前的除open/high/low/close/volume以外的其他数据：
        # 直接沿用上一周期的数据
        # 将hist_op和ref最后一行的数据复制到extended_op_values和extended_ref_values中,作为默认值
        extended_op_values[:, 0, :] = hist_op.values[:, -1, :]
        if not hist_ref.is_empty:
            extended_ref_values[:, 0, :] = hist_ref.values[:, -1, :]

        # 如果没有给出live_prices，则使用eastmoney的stock_live_kline_price获取当前周期的最新数据
        if live_prices is None:
            from qteasy.emfuncs import stock_live_kline_price
            live_kline_prices = stock_live_kline_price(
                    symbols=hist_op.shares,
                    freq=operator.op_data_freq,
            )
            live_kline_prices.set_index('symbol', inplace=True)
        else:
            live_kline_prices = live_prices
        # 将live_kline_prices中的数据填充到extended_op_values和extended_ref_values中
        live_kline_prices = live_kline_prices.reindex(index=hist_op.shares)
        for i, htype in enumerate(hist_op.htypes):
            if htype in live_kline_prices.columns:
                extended_op_values[:, 0, i] = live_kline_prices[htype].values

        # 将extended_hist_op和extended_hist_ref添加到hist_op和hist_ref中
        extended_hist_op = HistoryPanel(
                values=extended_op_values,
                levels=hist_op.shares,
                rows=[latest_cycle_date],
                columns=hist_op.htypes,
        )
        hist_op = hist_op.join(extended_hist_op, same_shares=True, same_htypes=True)
        if not hist_ref.is_empty:
            extended_hist_ref = HistoryPanel(
                    values=extended_ref_values,
                    levels=hist_ref.shares,
                    rows=[latest_cycle_date],
                    columns=hist_ref.htypes,
            )
            hist_ref = hist_ref.join(extended_hist_ref, same_shares=True, same_htypes=True)

    return hist_op, hist_ref


def check_and_prepare_backtest_data(operator, config, datasource=None):
    """ 在run_mode == 1的回测模式情况下准备相应的历史数据

    Returns
    -------
    """
    (hist_op,
     hist_ref,
     back_trade_prices,
     hist_opti,
     hist_opti_ref,
     opti_trade_prices,
     hist_benchmark,
     invest_cash_plan,
     opti_cash_plan,
     test_cash_plan
     ) = check_and_prepare_hist_data(operator, config, datasource)

    return hist_op, hist_ref, back_trade_prices, hist_benchmark, invest_cash_plan


def check_and_prepare_optimize_data(operator, config, datasource=None):
    """ 在run_mode == 2的策略优化模式情况下准备相应的历史数据

    Parameters
    ----------
    operator: qteasy.Operator
        运算器对象
    config: qteasy.Config
        配置对象
    datasource: qteasy.DataSource
        数据源对象

    Returns
    -------
    """
    (hist_op,
     hist_ref,
     back_trade_prices,
     hist_opti,
     hist_opti_ref,
     opti_trade_prices,
     hist_benchmark,
     invest_cash_plan,
     opti_cash_plan,
     test_cash_plan
     ) = check_and_prepare_hist_data(operator, config, datasource)

    return hist_opti, hist_opti_ref, opti_trade_prices, hist_benchmark, opti_cash_plan, test_cash_plan


# noinspection PyTypeChecker
def run(operator, **kwargs):
    """开始运行，qteasy模块的主要入口函数

    接受operator执行器对象作为主要的运行组件，根据输入的运行模式确定运行的方式和结果
    根据QT_CONFIG环境变量中的设置和运行模式（mode）进行不同的操作：
    mode == 0:
        进入实时信号生成模式：实盘运行模式是一个无限循环：
        根据Config以及Operator中策略的设置定时启动相应的交易策略，读取最新的实时数据，生成交易信号，并将交易信号解析为
        交易指令，发送到交易所Broker对象执行。
        所有的交易结果和实时持仓都会被记录到数据库中，如果数据库中已经有了相应的记录，新的实盘运行结果可以在已经有的记录上
        继续运行，或者用户也可以选择新建一个实盘账户，重新开始运行。

        实盘运行的过程会显示在屏幕上，用户可以在实盘运行过程中隋时进入交互模式，查看实盘运行的状态，或者修改运行参数。

        用户需要在Terminal中以命令行的方式运行qteasy的实盘模式，通过tradershell查看运行过程并进行交互。

    mode == 1, backtest mode, 回测模式，根据历史数据生成交易信号，执行交易：
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
            16，win_rate                             胜率

        上述所有评价结果和历史区间数据能够以可视化的方式输出到图表中。同时回测的结果数据和回测区间的每一次模拟交易记录也可以被记录到log对象中
        保存在磁盘上供未来调用

    mode == 2, optimization mode, 优化模式，使用一段历史数据区间内的数据来寻找最优的策略参数组合，然后在另一段历史数据区间内进行回测，评价:
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

                3，Incremental_step_searching            递进搜索法

                递进步长法的基本思想是对参数空间进行多轮递进式的搜索，每一轮搜索方法与蒙特卡洛法相同但是每一轮搜索后都将搜索
                范围缩小到更希望产生全局最优的子空间中，并在这个较小的子空间中继续使用蒙特卡洛法进行搜索，直到该子空间太小、
                或搜索轮数大于设定值为止。

                使用这种技术，在一个250*250*250的空间中，能够把搜索量从15,000,000降低到10,000左右,缩减到原来的1/1500，
                却不太会影响最终搜索的效果。

                关于递进步长法的参数和输出，参见self._search_incremental()函数的docstring

            4，Genetic_Algorithm                     遗传算法 （尚未实现）

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

            5, Gradient Descendent Algorithm        梯度下降算法 （尚未实现）

                梯度下降算法

        2，有监督方法类：这一类方法依赖于历史数据上的（有用的）先验信息：比如过去一个区间上的已知交易信号、或者价格变化信息。然后通过
        优化方法寻找历史数据和有用的先验信息之间的联系（目标联系）。这一类优化方法的假设是，如果这些通过历史数据直接获取先验信息的
        联系在未来仍然有效，那么我们就可能在未来同样根据这些联系，利用已知的数据推断出对我们有用的信息。
        这一类方法包括：
            1，ANN_based_methods                     基于人工神经网络的有监督方法（尚未实现）
            2，SVM                                   支持向量机类方法（尚未实现）
            3，KNN                                   基于KNN的方法（尚未实现）

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

    Parameters
    ----------
    operator : Operator
        策略执行器对象
    **kwargs:
        可用的kwargs包括所有合法的qteasy配置参数，参见qteasy文档

    Returns
    -------
        1, 在live_trade模式或模式0下，进入实盘交易Shell
        2, 在back_test模式或模式1下, 返回: loop_result
        3, 在optimization模式或模式2下: 返回一个list，包含所有优化后的策略参数
    """

    try:
        # 如果operator尚未准备好,is_ready()会检查汇总所有问题点并raise
        operator.is_ready()
    except Exception as e:
        raise ValueError(f'operator object is not ready for running, please check following info:\n'
                         f'{e}')

    optimization_methods = {0: _search_grid,
                            1: _search_montecarlo,
                            2: _search_incremental,
                            3: _search_ga,
                            4: _search_gradient,
                            5: _search_pso,
                            6: _search_aco
                            }
    # 如果函数调用时用户给出了关键字参数(**kwargs），将关键字参数赋值给一个临时配置参数对象，
    # 覆盖QT_CONFIG的设置，但是仅本次运行有效
    config = ConfigDict(**QT_CONFIG)
    configure(config=config, **kwargs)

    # 赋值给参考数据和运行模式
    benchmark_data_type = config['benchmark_asset']
    run_mode = config['mode']
    """
    用于交易信号生成、数据回测、策略优化、结果测试以及结果评价参考的历史数据:
    hist_op:            信号生成数据，根据策略的运行方式，信号生成数据可能包含量价数据、基本面数据、指数、财务指标等等
    back_trade_prices:          回测价格数据，用于在backtest模式下对生成的信号进行测试，仅包含买卖价格数据（定价回测）
    hist_opti:          策略优化数据，数据的类型与信号生成数据一样，但是取自专门的独立区间用于策略的参数优化
    hist_opti_loop:     优化回测价格，用于在optimization模式下在策略优化区间上回测交易结果，目前这组数据并未提前生成，
                        而是在optimize的时候生成，实际上应该提前生成
    hist_test:          策略检验数据，数据的类型与信号生成数据一样，同样取自专门的独立区间用于策略参数的性能检测
    hist_test_loop:     检验回测价格，用于在optimization模式下在策略检验区间上回测交易结果
    hist_benchmark:     评价参考价格，用于评价回测结果，大部分用于评价回测结果的alpha表现（取出无风险回报之后的表现）
                        相关的指标都需要用到参考价格;
    invest_cash_plan:
    opti_cash_plan:
    test_cssh_plan:
    """

    if run_mode == 0 or run_mode == 'live':
        '''进入实时信号生成模式: 
        '''
        # 启动交易shell
        from qteasy.trader import start_trader
        from qteasy import QT_DATA_SOURCE
        start_trader(
                operator=operator,
                account_id=config['live_trade_account_id'],
                user_name=config['live_trade_account'],
                init_cash=config['live_trade_init_cash'],
                init_holdings=config['live_trade_init_holdings'],
                config=config,
                datasource=QT_DATA_SOURCE,
                debug=config['live_trade_debug_mode'],
        )

    elif run_mode == 1 or run_mode == 'back_test':
        # 进入回测模式，生成历史交易清单，使用真实历史价格回测策略的性能
        (hist_op,
         hist_ref,
         back_trade_prices,
         hist_benchmark,
         invest_cash_plan
         ) = check_and_prepare_backtest_data(
                operator=operator,
                config=config
        )
        # 在生成交易信号之前准备历史数据
        operator.assign_hist_data(
                hist_data=hist_op,
                reference_data=hist_ref,
                cash_plan=invest_cash_plan,
        )

        # 生成交易清单，对交易清单进行回测，对回测的结果进行基本评价
        loop_result = _evaluate_one_parameter(
                par=None,
                op=operator,
                trade_price_list=back_trade_prices,
                benchmark_history_data=hist_benchmark,
                benchmark_history_data_type=benchmark_data_type,
                config=config,
                stage='loop'
        )
        if config['report']:
            # 格式化输出回测结果
            _print_loop_result(loop_result, config)
        if config['visual']:
            # 图表输出投资回报历史曲线
            _plot_loop_result(loop_result, config)

        return loop_result

    elif run_mode == 2 or run_mode == 'optimization':
        # 进入优化模式，使用真实历史数据或模拟历史数据反复测试策略，寻找并测试最佳参数
        # 判断operator对象的策略中是否有可优化的参数，即优化标记opt_tag设置为1，且参数数量不为0
        assert operator.opt_space_par[0] != [], \
            f'ConfigError, none of the strategy parameters is adjustable, set opt_tag to be 1 or 2 to ' \
            f'activate optimization in mode 2, and make sure strategy has adjustable parameters'
        (hist_opti,
         hist_opti_ref,
         opti_trade_prices,
         hist_benchmark,
         opti_cash_plan,
         test_cash_plan
         ) = check_and_prepare_optimize_data(
                operator=operator,
                config=config
        )
        operator.assign_hist_data(
                hist_data=hist_opti,
                cash_plan=opti_cash_plan,
                reference_data=hist_opti_ref,
        )
        # 使用how确定优化方法并生成优化后的参数和性能数据
        how = config['opti_method']
        optimal_pars, perfs = optimization_methods[how](
                hist=hist_opti,
                benchmark=hist_benchmark,
                benchmark_type=benchmark_data_type,
                op=operator,
                config=config
        )
        # 输出策略优化的评价结果，该结果包含在result_pool的extra额外信息属性中
        hist_opti_loop = hist_opti.fillna(0)
        result_pool = _evaluate_all_parameters(
                par_generator=optimal_pars,
                total=config['opti_output_count'],
                op=operator,
                trade_price_list=hist_opti_loop,
                benchmark_history_data=hist_benchmark,
                benchmark_history_data_type=benchmark_data_type,
                config=config,
                stage='test-o'
        )
        # 评价回测结果——计算参考数据收益率以及平均年化收益率
        opti_eval_res = result_pool.extra
        if config['report']:
            _print_test_result(opti_eval_res, config=config)
        if config['visual']:
            pass
            # _plot_test_result(opti_eval_res, config=config)

        # 完成策略参数的寻优，在测试数据集上检验寻优的结果，此时operator的交易数据已经分配好，无需再次分配
        if config['test_type'] in ['single', 'multiple']:
            result_pool = _evaluate_all_parameters(
                    par_generator=optimal_pars,
                    total=config['opti_output_count'],
                    op=operator,
                    trade_price_list=opti_trade_prices,
                    benchmark_history_data=hist_benchmark,
                    benchmark_history_data_type=benchmark_data_type,
                    config=config,
                    stage='test-t'
            )

            # 评价回测结果——计算参考数据收益率以及平均年化收益率
            test_eval_res = result_pool.extra
            if config['report']:
                _print_test_result(test_eval_res, config)
            if config['visual']:
                _plot_test_result(test_eval_res=test_eval_res, opti_eval_res=opti_eval_res, config=config)

        elif config['test_type'] == 'montecarlo':
            for i in range(config['test_cycle_count']):
                # 临时生成用于测试的模拟数据，将模拟数据传送到operator中，使用operator中的新历史数据
                # 重新生成交易信号，并在模拟的历史数据上进行回测
                mock_hist = _create_mock_data(hist_opti)
                print(f'config.test_cash_dates is {config["test_cash_dates"]}')
                operator.assign_hist_data(
                        hist_data=mock_hist,
                        cash_plan=test_cash_plan,
                )
                mock_hist_loop = mock_hist.slice_to_dataframe(htype='close')
                result_pool = _evaluate_all_parameters(
                        par_generator=optimal_pars,
                        total=config['opti_output_count'],
                        op=operator,
                        trade_price_list=mock_hist,
                        benchmark_history_data=mock_hist_loop,
                        benchmark_history_data_type=benchmark_data_type,
                        config=config,
                        stage='test-t'
                )

                # 评价回测结果——计算参考数据收益率以及平均年化收益率
                test_eval_res = result_pool.extra
                if config['report']:
                    # TODO: 应该有一个专门的函数print_montecarlo_test_report
                    _print_test_result(test_eval_res, config)
                if config['visual']:  # 如果config.visual == True
                    # TODO: 应该有一个专门的函数plot_montecarlo_test_result
                    pass

        return optimal_pars


def _evaluate_all_parameters(par_generator,
                             total,
                             op: Operator,
                             trade_price_list: HistoryPanel,
                             benchmark_history_data,
                             benchmark_history_data_type,
                             config,
                             stage='optimize') -> ResultPool:
    """ 接受一个策略参数生成器对象，批量生成策略参数，反复调用_evaluate_one_parameter()函数，使用所有生成的策略参数
        生成历史区间上的交易策略和回测结果，将得到的回测结果全部放入一个结果池对象，并根据策略筛选方法筛选出符合要求的回测
        结果，并返回筛选后的结果。

        根据config中的配置参数，这里可以选择进行并行计算以充分利用多核处理器的全部算力以缩短运行时间。

    Parameters
    ----------
    par_generator: Iterables
        一个迭代器对象，生成所有需要迭代测试的策略参数
    op: Operator
        一个operator对象，包含多个投资策略，用于根据交易策略以及策略的配置参数生成交易信号
    trade_price_list: pd.DataFrame
        用于进行回测的历史数据，该数据历史区间与前面的数据相同，但是仅包含回测所需要的价格信息，通常为收盘价
        （假设交易价格为收盘价）
    benchmark_history_data: pd.DataFrame
        用于回测结果评价的参考历史数据，历史区间与回测历史数据相同，但是通常是能代表整个市场整体波动的金融资
        产的价格，例如沪深300指数的价格。
    benchmark_history_data_type: str
        用于回测结果评价的参考历史数据种类，通常为收盘价close
    config: Config
        参数配置对象，用于保存相关配置，在所有的参数配置中，其作用的有下面N种：
        1, config.opti_output_count:
            优化结果数量
        2, config.parallel:
            并行计算选项，True时进行多进程并行计算，False时进行单进程计算
    stage: str
        该参数直接传递至_evaluate_one_parameter()函数中，其含义和作用参见其docstring

    Returns
    -------
        pool，一个Pool对象，包含经过筛选后的所有策略参数以及它们的性能表现

    """
    pool = ResultPool(config.opti_output_count)  # 用于存储中间结果或最终结果的参数池对象
    i = 0
    best_so_far = 0
    opti_target = config.optimize_target
    # 启用多进程计算方式利用所有的CPU核心计算
    if config.parallel:
        # 启用并行计算
        with ProcessPoolExecutor() as proc_pool:
            futures = {proc_pool.submit(_evaluate_one_parameter,
                                        par,
                                        op,
                                        trade_price_list,
                                        benchmark_history_data,
                                        benchmark_history_data_type,
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
                                           trade_price_list=trade_price_list,
                                           benchmark_history_data=benchmark_history_data,
                                           benchmark_history_data_type=benchmark_history_data_type,
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


def _evaluate_one_parameter(par,
                            op: Operator,
                            trade_price_list: HistoryPanel,
                            benchmark_history_data,
                            benchmark_history_data_type,
                            config,
                            stage='optimize') -> dict:
    """ 基于op中的交易策略，在给定策略参数par的条件下，计算交易策略在一段历史数据上的交易信号，并对交易信号的交易
        结果进行回测，对回测结果数据进行评价，并给出评价结果。

    本函数是一个方便的包裹函数，包裹了交易信号生成、交易信号回测以及回测结果评价结果的打包过程，同时，根据QT基
    本配置的不同，可以在交易信号回测的过程中进行多重回测，即将一段历史区间分成几个子区间，在每一个子区间上分别
    回测后返回多次回测的综合结果。

    Parameters
    ----------
    par: tuple, list, dict
        输入的策略参数组合，这些参数必须与operator运行器对象中的交易策略相匹配，且符合op对象中每个交易策
        略的优化标记设置，关于交易策略的优化标记如何影响参数导入，参见qt.operator.set_opt_par()的
        docstring
    op: qt.Operator
        一个operator对象，包含多个投资策略，用于根据交易策略以及策略的配置参数生成交易信号
    trade_price_list: HistoryPanel
        用于模拟交易回测的历史价格，历史区间覆盖整个模拟交易期间，包含回测所需要的价格信息，可以为收盘价
        和/或其他回测所需要的历史价格
    benchmark_history_data: pd.DataFrame
        用于回测结果评价的参考历史数据，历史区间与回测历史数据相同，但是通常是能代表整个市场整体波动的金融资
        产的价格，例如沪深300指数的价格。
    benchmark_history_data_type: str
        用于回测结果评价的参考历史数据种类，通常为收盘价close，但也可以是其他价格，例如开盘价open
    config: Config
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
    stage: str, optional, Default: 'optimize'
        运行标记，代表不同的运行阶段控制运行过程的不同处理方式，包含三种不同的选项
        1, 'loop':      运行模式为回测模式，在这种模式下：
                        使用投资区间回测投资计划
                        使用config.trade_log来确定是否打印回测结果
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
    Returns
    -------
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
    op_list = None
    if op.op_type == 'batch':
        op_list = op.create_signal()
    et = time.time()
    op_run_time = et - st
    res_dict['op_run_time'] = op_run_time
    riskfree_ir = config.riskfree_ir
    log_backtest = False
    period_length = 0
    period_count = 0
    trade_dates = np.array(trade_price_list.hdates)
    if op.op_type == 'batch' and op_list is None:  # 如果策略无法产生有意义的操作清单，则直接返回基本信息
        res_dict['final_value'] = np.NINF
        res_dict['complete_values'] = pd.DataFrame()
        return res_dict
    # 根据stage的值选择使用投资金额种类以及运行类型（单区间运行或多区间运行）及区间参数及回测参数
    if stage == 'loop':
        invest_cash_amounts = config.invest_cash_amounts
        invest_cash_dates = pd.to_datetime(config.invest_start) if \
            config.invest_cash_dates is None \
            else pd.to_datetime(config.invest_cash_dates)
        period_util_type = 'single'
        indicators = 'years,fv,return,mdd,v,ref,alpha,beta,sharp,info'
        log_backtest = config.trade_log  # 回测参数trade_log只有在回测模式下才有用
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
    elif stage == 'test-o':  # 在优化过程中，在优化区间上测试参数的性能
        invest_cash_amounts = config.test_cash_amounts[0]
        # TODO: only works when config.opti_cash_dates is a string, if it is a list, it will not work
        invest_cash_dates = pd.to_datetime(config.opti_start) if \
            config.opti_cash_dates is None \
            else pd.to_datetime(config.opti_cash_dates)
        period_util_type = config.test_type
        period_count = config.test_sub_periods
        period_length = config.test_sub_prd_length
        indicators = config.test_indicators
    else:  # stage == 'test-t':  # 在优化结束后，在测试区间上测试找到的最优参数的性能
        invest_cash_amounts = config.test_cash_amounts[0]
        # TODO: only works when config.opti_cash_dates is a string, if it is a list, it will not work
        invest_cash_dates = pd.to_datetime(config.test_start) if \
            config.test_cash_dates is None \
            else pd.to_datetime(config.test_cash_dates)
        period_util_type = config.test_type
        period_count = config.test_sub_periods
        period_length = config.test_sub_prd_length
        indicators = config.test_indicators
    # create list of start and end dates
    # in this case, user-defined invest_cash_dates will be disabled, each start dates will be
    # used as the investment date for each sub-periods
    invest_cash_dates = next_market_trade_day(invest_cash_dates)
    start_dates = []
    end_dates = []
    if period_util_type == 'single' or period_util_type == 'montecarlo':
        start_dates.append(trade_dates[np.searchsorted(trade_dates, invest_cash_dates)])
        end_dates.append(trade_dates[-1])
    elif period_util_type == 'multiple':
        # 多重测试模式，将一个完整的历史区间切割成多个区间，多次测试
        first_history_date = invest_cash_dates
        last_history_date = trade_dates[-1]
        history_range = last_history_date - first_history_date
        sub_hist_range = history_range * period_length
        sub_hist_interval = (1 - period_length) * history_range / period_count
        for i in range(period_count):
            # 计算每个测试区间的起止点，抖动起止点日期，确保起止点在交易日期列表中
            start_date = first_history_date + i * sub_hist_interval
            start_date = trade_dates[np.searchsorted(trade_dates, start_date)]
            start_dates.append(start_date)
            end_date = start_date + sub_hist_range
            end_date = trade_dates[np.searchsorted(trade_dates, end_date)]
            end_dates.append(end_date)
    else:
        raise KeyError(f'Invalid optimization type: {config.opti_type}')
    # loop over all pairs of start and end dates, get the results separately and output average
    perf_list = []
    price_priority_list = op.get_bt_price_type_id_in_priority(priority=config.price_priority_OHLC)
    trade_cost = set_cost(
            buy_fix=config.cost_fixed_buy,
            sell_fix=config.cost_fixed_sell,
            buy_rate=config.cost_rate_buy,
            sell_rate=config.cost_rate_sell,
            buy_min=config.cost_min_buy,
            sell_min=config.cost_min_sell,
            slipage=config.cost_slippage
    )
    st = time.time()
    for start, end in zip(start_dates, end_dates):
        start_idx = op.get_hdate_idx(start)
        end_idx = op.get_hdate_idx(end)
        trade_price_list_seg = trade_price_list.segment(start, end)
        if stage != 'loop':
            invest_cash_dates = trade_price_list_seg.hdates[0]
        cash_plan = CashPlan(
                invest_cash_dates.strftime('%Y%m%d'),
                invest_cash_amounts,
                riskfree_ir
        )
        # TODO: 将op_list_bt_indices的计算放到这一层函数中，以便下面几个函数可以共享
        loop_results, op_log_matrix, op_summary_matrix, op_list_bt_indices = apply_loop(
                operator=op,
                trade_price_list=trade_price_list_seg,
                start_idx=start_idx,
                end_idx=end_idx,
                cash_plan=cash_plan,
                cost_rate=trade_cost,
                moq_buy=config.trade_batch_size,
                moq_sell=config.sell_batch_size,
                inflation_rate=config.riskfree_ir,
                pt_signal_timing=config.PT_signal_timing,
                pt_buy_threshold=config.PT_buy_threshold,
                pt_sell_threshold=config.PT_sell_threshold,
                cash_delivery_period=config.cash_delivery_period,
                stock_delivery_period=config.stock_delivery_period,
                allow_sell_short=config.allow_sell_short,
                long_pos_limit=config.long_position_limit,
                short_pos_limit=config.short_position_limit,
                max_cash_usage=config.maximize_cash_usage,
                trade_log=log_backtest,
                price_priority_list=price_priority_list
        )
        looped_val = process_loop_results(
                operator=op,
                loop_results=loop_results,
                op_log_matrix=op_log_matrix,
                op_summary_matrix=op_summary_matrix,
                op_list_bt_indices=op_list_bt_indices,
                trade_log=log_backtest,
                bt_price_priority_ohlc='OHLC'
        )
        # TODO: 将_get_complete_hist() 与 process_loop_results()合并
        complete_values = _get_complete_hist(
                looped_value=looped_val,
                h_list=trade_price_list,
                benchmark_list=benchmark_history_data,
                with_price=False
        )
        perf = evaluate(
                looped_values=complete_values,
                hist_benchmark=benchmark_history_data,
                benchmark_data=benchmark_history_data_type,
                cash_plan=cash_plan,
                indicators=indicators
        )
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

    Parameters
    ----------
    history_data: HistoryPanel
        模拟数据的参考源

    Returns
    -------
        HistoryPanel
    """

    assert isinstance(history_data, HistoryPanel)
    data_types = history_data.htypes
    # TODO: volume数据的生成还需要继续研究
    assert any(data_type in ['close', 'open', 'high', 'low', 'volume'] for data_type in data_types), \
        f'the data type {data_types} does not fit'
    has_volume = any(data_type in ['volume'] for data_type in data_types)
    # 按照细粒度方法同时生成OHLC数据
    # 针对每一个share生成OHLC数据
    # 先考虑生成正确的信息，以后再考虑优化
    dfs_for_share = []
    for share in history_data.shares:
        share_df = history_data.slice_to_dataframe(share=share)
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
                                 dataframe_as='shares',
                                 shares=history_data.shares)
    return mock_data


def _search_grid(hist, benchmark, benchmark_type, op, config):
    """ 最优参数搜索算法1: 网格搜索法

    在整个参数空间中建立一张间距固定的"网格"，搜索网格的所有交点所在的空间点，
    根据该点的参数生成操作信号、回测后寻找表现最佳的一组或多组参数
    与该算法相关的设置选项有：
    grid_size:  网格大小，float/int/list/tuple 当参数为数字时，生成空间所有方向
                上都均匀分布的网格；当参数为list或tuple时，可以在空间的不同方向
                上生成不同间隔大小的网格。list或tuple的维度须与空间的维度一致

    Parameters
    ----------
    hist: HistoryPanel
        历史数据，优化器的整个优化过程在历史数据上完成
    op: qt.Operator
        交易信号生成器对象
    config: qt.Config
        用于存储优化参数配置变量

    Returns
    -------
    tuple: (pool.items, pool.perfs)
        pool.items 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
    """
    s_range, s_type = op.opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间

    # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
    par_generator, total = space.extract(config.opti_grid_size)
    history_list = hist.fillna(0)
    st = time.time()
    pool = _evaluate_all_parameters(par_generator=par_generator,
                                    total=total,
                                    op=op,
                                    trade_price_list=history_list,
                                    benchmark_history_data=benchmark,
                                    benchmark_history_data_type=benchmark_type,
                                    config=config,
                                    stage='optimize')
    pool.cut(config.maximize_target)
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {sec_to_duration(et - st)}')
    return pool.items, pool.perfs


def _search_montecarlo(hist, benchmark, benchmark_type, op, config):
    """ 最优参数搜索算法2: 蒙特卡洛法

        从待搜索空间中随机抽取大量的均匀分布的参数点并逐个测试，寻找评价函数值最优的多个参数组合
        与该算法相关的设置选项有：
            sample_size:采样点数量，int 由于采样点的分布是随机的，因此采样点越多，越有可能
                        接近全局最优值

    Parameters
    ----------
    hist: HistoryPanel
        历史数据，优化器的整个优化过程在历史数据上完成
    benchmark:
        基准数据，用于计算基准收益率
    benchmark_type:
        基准数据类型，用于计算基准收益率
    op: qt.Operator
        交易信号生成器对象
    config: qt.Config
        用于存储交易相关参数的配置变量

    Returns
    -------
    tuple: (pool.items, pool.perfs)
        pool.items 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
    """
    # s_range, s_type = a_to_sell.opt_space_par
    space = Space(*op.opt_space_par)  # 生成参数空间
    # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与网格法一致
    par_generator, total = space.extract(config.opti_sample_count, how='rand')
    history_list = hist.fillna(0)
    st = time.time()
    pool = _evaluate_all_parameters(par_generator=par_generator,
                                    total=total,
                                    op=op,
                                    trade_price_list=history_list,
                                    benchmark_history_data=benchmark,
                                    benchmark_history_data_type=benchmark_type,
                                    config=config,
                                    stage='optimize')
    pool.cut(config.maximize_target)
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {sec_to_duration(et - st, short_form=True)}')
    return pool.items, pool.perfs


def _search_incremental(hist, benchmark, benchmark_type, op, config):
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

    Parameters
    ----------
    hist: HistoryPanel
        历史数据，优化器的整个优化过程在历史数据上完成
    op: qt.Operator
        交易信号生成器对象
    config: qt.Config
        用于存储交易相关参数的配置变量

    Returns
    -------
    tuple，包含两个变量
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
    history_list = hist.fillna(0)  # 准备历史数据
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
                                                   trade_price_list=history_list,
                                                   benchmark_history_data=benchmark,
                                                   benchmark_history_data_type=benchmark_type,
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
    print(f'\nOptimization completed, total time consumption: {sec_to_duration(et - st)}')
    return pool.items, pool.perfs


def _search_ga(hist, benchmark, benchmark_type, op, config):
    """ 最优参数搜索算法4: 遗传算法
    遗传算法适用于在超大的参数空间内搜索全局最优或近似全局最优解，而它的计算量又处于可接受的范围内

    遗传算法借鉴了生物的遗传迭代过程，首先在参数空间中随机选取一定数量的参数点，将这批参数点称为
    “种群”。随后在这一种群的基础上进行迭代计算。在每一次迭代（称为一次繁殖）前，根据种群中每个个体
    的评价函数值，确定每个个体生存或死亡的几率，规律是若个体的评价函数值越接近最优值，则其生存的几率
    越大，繁殖后代的几率也越大，反之则越小。确定生死及繁殖的几率后，根据生死几率选择一定数量的个体
    让其死亡，而从剩下的（幸存）的个体中根据繁殖几率挑选几率最高的个体进行杂交并繁殖下一代个体，
    同时在繁殖的过程中引入随机的基因变异生成新的个体。最终使种群的数量恢复到初始值。这样就完成
    一次种群的迭代。重复上面过程数千乃至数万代直到种群中出现希望得到的最优或近似最优解为止

    Parameters
    ----------
    hist: HistoryPanel
        历史数据，优化器的整个优化过程在历史数据上完成
    benchmark:

    benchmark_type:

    op: object，
        交易信号生成器对象
    config: ConfigDict

    Returns
    -------
    tuple，包含两个变量
        pool.items 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

    """
    raise NotImplementedError


def _search_gradient(hist, benchmark, benchmark_type, op, config):
    """ 最优参数搜索算法5：梯度下降法
    在参数空间中寻找优化结果变优最快的方向，始终保持向最优方向前进（采用自适应步长）一直到结果不再改变或达到
    最大步数为止，输出结果为最后N步的结果

    Parameters
    ----------
    hist，object，历史数据，优化器的整个优化过程在历史数据上完成
    benchmark:
    benchmark_type:
    op: object，交易信号生成器对象
    config: object, 用于存储交易相关参数配置对象

    Returns
    -------
    """
    raise NotImplementedError


def _search_pso(hist, benchmark, benchmark_type, op, config):
    """ Particle Swarm Optimization 粒子群优化算法，与梯度下降相似，从随机解出发，通过迭代寻找最优解

    Parameters
    ----------
    hist，object，历史数据，优化器的整个优化过程在历史数据上完成
    benchmark:
    benchmark_type:
    op: object，交易信号生成器对象
    config: object, 用于存储交易相关参数配置对象

    Returns
    -------
    """
    raise NotImplementedError


def _search_aco(hist, benchmark, benchmark_type, op, config):
    """ Ant Colony Optimization 蚁群优化算法，

    Parameters
    ----------
    hist，object，历史数据，优化器的整个优化过程在历史数据上完成
    benchmark:
    benchmark_type:
    op，object，交易信号生成器对象
    config: object, 用于存储交易相关参数配置对象

    Returns
    -------
    """
    raise NotImplementedError
