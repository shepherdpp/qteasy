# coding=utf-8
# ======================================
# File:     trading_util.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-02-20
# Desc:
#   utility functions that may be shared
# between live-trading, back-testing, 
# optimization and other trading-related
# modules.
# ======================================

import pandas as pd
import numpy as np

from qteasy import logger_core as logger, Operator, QT_CONFIG

from qteasy.utilfuncs import str_to_list

from qteasy.trade_recording import read_trade_order, get_position_by_id, get_account, update_trade_order
from qteasy.trade_recording import read_trade_order_detail, read_trade_results_by_delivery_status, write_trade_result
from qteasy.trade_recording import read_trade_results_by_order_id, get_account_cash_availabilities
from qteasy.trade_recording import update_account_balance, update_position, update_trade_result
from qteasy.trade_recording import query_trade_orders, get_account_positions

# TODO: read TIMEZONE from qt config arguments
TIMEZONE = 'Asia/Shanghai'
# TIMEZONE = 'UTC'
CASH_DECIMAL_PLACES = QT_CONFIG['cash_decimal_places']
AMOUNT_DECIMAL_PLACES = QT_CONFIG['amount_decimal_places']


def create_daily_task_schedule(operator, config=None):
    """ 根据operator对象中的交易策略以及环境变量生成每日任务日程

    每日任务日程包括含 sleep / wake_up / run_stg 等所有有效任务类型的任务列表，
    以及每项任务在正常交易日内的执行时间

    Parameters
    ----------
    operator: Operator
        交易策略的Operator对象
    config: dict, optional
        qteasy的配置环境变量, 如果为None, 则使用qteasy.QT_CONFIG

    Returns
    -------
    task_agenda: list of tuple [(datetime.time, str, optional: list of str)]
        每日任务日程, 每项任务是一个tuple, 包含任务的执行时间, 任务的名称, 以及任务的参数列表(optional)
    """
    # 检查输入数据的类型是否正确
    if not isinstance(operator, Operator):
        raise TypeError(f'operator must be an Operator object, got {type(operator)} instead.')
    if not isinstance(config, dict):
        raise TypeError(f'config must be a dict object, got {type(config)} instead.')

    task_agenda = []

    today = pd.Timestamp.now(tz=TIMEZONE).date()

    market_open_time_am = config['market_open_time_am']
    market_close_time_am = config['market_close_time_am']
    market_open_time_pm = config['market_open_time_pm']
    market_close_time_pm = config['market_close_time_pm']
    # exchange_market = config['exchange']
    exchange_market = 'SSE'

    # 调整任务时间，开盘任务在开盘时执行，收盘任务在收盘时执行，sleep和wakeup任务在开盘前后5分钟执行
    # TODO: 开收盘任务执行提前期或sleep/wakeup任务执行延后期，应该是可配置的
    open_close_lead = 0  # 股市开盘和收盘时间提前期
    noon_close_delay = 5  # 午间休市时间延后期
    pre_open_lead = 15  # 开盘前处理提前期
    post_close_delay = 15  # 收盘后处理延后期
    market_open_time = (pd.to_datetime(market_open_time_am) -
                        pd.Timedelta(minutes=open_close_lead)).strftime('%H:%M:%S')
    market_close_time = (pd.to_datetime(market_close_time_pm) +
                         pd.Timedelta(minutes=open_close_lead)).strftime('%H:%M:%S')
    pre_open_time = (pd.to_datetime(market_open_time_am) -
                      pd.Timedelta(minutes=pre_open_lead)).strftime('%H:%M:%S')
    wakeup_time_pm = (pd.to_datetime(market_open_time_pm) -
                      pd.Timedelta(minutes=noon_close_delay)).strftime('%H:%M:%S')
    sleep_time_am = (pd.to_datetime(market_close_time_am) +
                     pd.Timedelta(minutes=noon_close_delay)).strftime('%H:%M:%S')
    post_close_time = (pd.to_datetime(market_close_time_pm) +
                     pd.Timedelta(minutes=post_close_delay)).strftime('%H:%M:%S')

    # 添加交易市场开市和收市任务，早晚收盘和午间休市时时产生open_market/close_market任务
    task_agenda.append((market_open_time, 'open_market'))
    task_agenda.append((pre_open_time, 'pre_open'))
    task_agenda.append((sleep_time_am, 'close_market'))
    task_agenda.append((wakeup_time_pm, 'open_market'))
    task_agenda.append((market_close_time, 'close_market'))
    task_agenda.append((post_close_time, 'post_close'))

    # 根据config中的live_price_acquire参数，生成获取实时价格的任务
    # 数据获取频率是分钟级别的，根据交易市场的开市时间和收市时间，生成获取实时价格的任务时间
    from qteasy.utilfuncs import next_market_trade_day
    a_trade_day = next_market_trade_day(today, exchange=exchange_market)
    if a_trade_day is not None:
        the_next_day = (a_trade_day + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        raise ValueError(f'no next trade day of today({today})')
    run_time_index = _trade_time_index(
            start=a_trade_day,
            end=the_next_day,
            freq=config['live_price_acquire_freq'],
            start_am=market_open_time_am,
            end_am=market_close_time_am,
            include_start_am=False,
            include_end_am=True,
            start_pm=market_open_time_pm,
            end_pm=market_close_time_pm,
            include_start_pm=False,
            include_end_pm=True,
    ).strftime('%H:%M:%S').tolist()
    # 将实时价格的更新时间添加到任务日程，生成价格更新日程，因为价格更新的任务优先级更低，因此每个任务都推迟5秒执行
    for t in run_time_index:
        t = (pd.to_datetime(t) + pd.Timedelta(seconds=5)).strftime('%H:%M:%S')
        task_agenda.append((t, 'acquire_live_price'))

    # 从Operator对象中读取交易策略，分析策略的strategy_run_timing和strategy_run_freq参数，生成任务日程
    for stg_id, stg in operator.get_strategy_id_pairs():
        timing = stg.strategy_run_timing
        freq = stg.strategy_run_freq
        if freq.lower() in ['1min', '5min', '15min', '30min', 'h']:
            # 如果策略的运行频率是分钟级别的，则根据交易市场的开市时间和收市时间，生成每日任务日程
            run_time_index = _trade_time_index(
                    start=a_trade_day,
                    end=the_next_day,
                    freq=freq,
                    start_am=market_open_time_am,
                    end_am=market_close_time_am,
                    include_start_am=True,
                    include_end_am=True,
                    start_pm=market_open_time_pm,
                    end_pm=market_close_time_pm,
                    include_start_pm=True,
                    include_end_pm=True,
            ).strftime('%H:%M:%S').tolist()
        else:
            if timing == 'open':
                # 'open'表示开盘时运行策略即在开盘时运行
                stg_run_time = (pd.to_datetime(market_open_time_am))
            elif timing == 'close':
                # 'close' 表示收盘时运行策略即在收盘时运行
                stg_run_time = (pd.to_datetime(market_close_time_pm))
            else:
                # 其他情况，直接使用timing参数, 除非timing参数不是时间字符串，或者timing参数不在交易市场的开市时间内
                try:
                    stg_run_time = pd.to_datetime(timing)
                except ValueError:
                    raise ValueError(f'Invalid strategy_run_timing: {timing}')
            run_time_index = [stg_run_time.strftime('%H:%M:%S')]

        # 整理所有的timing，如果timing 在交易市场的开盘前或收盘后，此时调整timing为开盘后/收盘前1分钟
        strategy_open_close_timing_offset = config['strategy_open_close_timing_offset']
        for idx in range(len(run_time_index)):
            stg_run_time = pd.to_datetime(run_time_index[idx])
            market_open_time = pd.to_datetime(market_open_time_am)
            market_close_time = pd.to_datetime(market_close_time_pm)
            if stg_run_time <= market_open_time:
                # timing 在交易市场的开盘时间或以前，此时调整timing为开盘后1分钟
                stg_run_time = market_open_time + pd.Timedelta(minutes=strategy_open_close_timing_offset)
                run_time_index[idx] = stg_run_time.strftime('%H:%M:%S')
                continue
            if stg_run_time >= market_close_time:
                # timing 在交易市场的收盘时间或以后，此时调整timing为收盘前1分钟
                stg_run_time = market_close_time - pd.Timedelta(minutes=strategy_open_close_timing_offset)
                run_time_index[idx] = stg_run_time.strftime('%H:%M:%S')

        # 将策略的运行时间添加到任务日程，生成任务日程
        for t in run_time_index:
            if any(item for item in task_agenda if (item[0] == t) and (item[1] == 'run_strategy')):
                # 如果同时发生的'run_stg'任务已经存在，则修改该任务，将stg_id添加到列表中
                task_to_update = [item for item in task_agenda if (item[0] == t) and (item[1] == 'run_strategy')]
                task_idx_to_update = task_agenda.index(task_to_update[0])
                task_agenda[task_idx_to_update][2].append(stg_id)
            else:
                # 否则，则直接添加任务
                task_agenda.append((t, 'run_strategy', [stg_id]))

    # 对任务日程进行排序 （其实排序并不一定需要）
    task_agenda.sort(key=lambda x: x[0])

    return task_agenda


# Utility functions for live trade
def parse_trade_signal(signals,
                       signal_type,
                       shares,
                       prices,
                       own_amounts,
                       own_cash,
                       available_amounts=None,
                       available_cash=None,
                       config=None):
    """ 根据signal_type的值，将operator生成的qt交易信号解析为标准的交易订单元素，包括
    资产代码、头寸类型、交易方向、交易数量等, 不检查账户的可用资金和持仓数量

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    signal_type: str, {'PT', 'PS', 'VS'}
        交易信号类型
    shares: list of str
        股票代码
    prices: np.ndarray
        股票价格
    own_amounts: np.ndarray
        股票持仓数量, 与shares对应, 顺序一致, 无持仓的股票数量为0, 负数表示空头持仓
    own_cash: float
        账户可用资金总额
    available_amounts: np.ndarray
        股票可用持仓数量, 与shares对应, 顺序一致, 无持仓的股票数量为0, 负数表示空头持仓
    available_cash: float
        账户可用资金总额
    config: dict
        交易信号的配置

    Returns
    -------
    order_elements: tuple, (symbols, positions, directions, quantities, quoted_prices)
        symbols: list of str, 交易信号对应的股票代码
        positions: list of str, 交易信号对应的持仓类型
        directions: list of str, 交易信号对应的交易方向
        quantities: list of float, 交易信号对应的交易数量
        quoted_prices: list of float, 交易信号对应的交易价格
    """

    # TODO: 还需要考虑交易批量的限制，如只能买卖整数股或整百股等
    # 处理optional参数:
    # 如果没有提供可用资金和持仓数量，使用当前的资金和持仓数量
    if available_amounts is None:
        available_amounts = own_amounts
    if available_cash is None:
        available_cash = own_cash
    # 如果没有提供交易信号的配置，使用QT_CONFIG中的默认配置
    if config is None:
        from qteasy import QT_CONFIG
        config = {
            'PT_buy_threshold': QT_CONFIG['PT_buy_threshold'],
            'PT_sell_threshold': QT_CONFIG['PT_sell_threshold'],
            'allow_sell_short': QT_CONFIG['allow_sell_short'],
            'cash_decimal_places': QT_CONFIG['cash_decimal_places'],
            'amount_decimal_places': QT_CONFIG['amount_decimal_places'],
            'trade_batch_size': QT_CONFIG['trade_batch_size'],
            'sell_batch_size': QT_CONFIG['sell_batch_size']
        }

    # PT交易信号和PS/VS交易信号需要分开解析
    if signal_type.lower() == 'pt':
        cash_to_spend, amounts_to_sell = _parse_pt_signals(
            signals=signals,
            prices=prices,
            own_amounts=own_amounts,
            own_cash=own_cash,
            pt_buy_threshold=config['PT_buy_threshold'],
            pt_sell_threshold=config['PT_sell_threshold'],
            allow_sell_short=config['allow_sell_short']
        )
    # 解析PT交易信号：
    # 读取当前的所有持仓，与signal比较，根据差值确定计划买进和卖出的数量
    # 解析PS/VS交易信号
    # 直接根据交易信号确定计划买进和卖出的数量
    elif signal_type.lower() == 'ps':
        cash_to_spend, amounts_to_sell = _parse_ps_signals(
            signals=signals,
            prices=prices,
            own_amounts=own_amounts,
            own_cash=own_cash,
            allow_sell_short=config['allow_sell_short']
        )
    elif signal_type.lower() == 'vs':
        cash_to_spend, amounts_to_sell = _parse_vs_signals(
            signals=signals,
            prices=prices,
            own_amounts=own_amounts,
            allow_sell_short=config['allow_sell_short']
        )
    else:
        raise ValueError('Unknown signal type: {}'.format(signal_type))

    # 确认总现金是否足够执行交易，如果不足，则将计划买入金额调整为可用的最大值，可用持仓检查可以分别进行
    total_cash_to_spend = np.sum(cash_to_spend)  # 计划买进的总金额
    if total_cash_to_spend > own_cash:
        # 将计划买入的金额调整为可用的最大值
        cash_to_spend = cash_to_spend * own_cash / total_cash_to_spend

    # 将计算出的买入和卖出的数量转换为交易订单
    symbols, positions, directions, quantities, quoted_prices, remarks= _signal_to_order_elements(
        shares=shares,
        cash_to_spend=cash_to_spend,
        amounts_to_sell=amounts_to_sell,
        prices=prices,
        available_cash=available_cash,
        available_amounts=available_amounts,
        moq_buy=config['trade_batch_size'],
        moq_sell=config['sell_batch_size'],
        allow_sell_short=config['allow_sell_short'],
    )
    return symbols, positions, directions, quantities, quoted_prices, remarks


# TODO: 将parse_pt/ps/vs_signals函数作为通用函数，在core.py的loopstep中直接引用这三个函数的返回值
#  从而消除重复的代码
# TODO: 考虑修改多空买卖信号的表示方式：当前的表示方式为：
#  1. 多头买入信号：正数cash_to_spend
#  2. 空头买入信号：负数cash_to_spend
#  3. 多头卖出信号：负数amounts_to_sell，负数表示空头，与直觉相反
#  4. 空头卖出信号：正数amounts_to_sell，正数表示多头，与直觉相反
#  但是这种表示方式不够直观
#  可以考虑将多头买入信号和空头卖出信号的表示方式统一为：
#  1. 多头买入信号：正数cash_to_spend
#  2. 空头买入信号：负数cash_to_spend
#  3. 多头卖出信号：正数amounts_to_sell
#  4. 空头卖出信号：负数amounts_to_sell
#  上述表示方法用cash表示买入，amounts表示卖出，且正数表示多头，负数表示空头，与直觉相符
#  但是这样需要修改core.py中的代码，需要修改backtest的部分代码，需要详细测试
def _parse_pt_signals(signals,
                      prices,
                      own_amounts,
                      own_cash,
                      pt_buy_threshold,
                      pt_sell_threshold,
                      allow_sell_short):
    """ 解析PT类型的交易信号

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    prices: np.ndarray
        各个资产的价格
    own_amounts: np.ndarray
        各个资产的持仓数量
    own_cash: float
        账户的现金
    pt_buy_threshold: float
        PT买入的阈值
    pt_sell_threshold: float
        PT卖出的阈值
    allow_sell_short: bool
        是否允许卖空

    Returns
    -------
    tuple: (cash_to_spend, amounts_to_sell)
        cash_to_spend: np.ndarray, 买入资产的现金
        amounts_to_sell: np.ndarray, 卖出资产的数量
    """

    # 计算当前总资产
    total_value = np.sum(prices * own_amounts) + own_cash

    ptbt = pt_buy_threshold
    ptst = -pt_sell_threshold
    # 计算当前持有头寸的持仓占比，与交易信号相比较，计算持仓差异
    previous_pos = own_amounts * prices / total_value
    position_diff = signals - previous_pos
    # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
    # 当持有份额大于零时，平多仓：卖出数量 = 仓位差 * 持仓份额，此时持仓份额需大于零
    amounts_to_sell = np.where((position_diff < ptst) & (own_amounts > 0),
                               position_diff / previous_pos * own_amounts,
                               0.)
    # 当持有份额不小于0时，开多仓：买入金额 = 仓位差 * 当前总资产，此时不能持有空头头寸
    cash_to_spend = np.where((position_diff > ptbt) & (own_amounts >= 0),
                             position_diff * total_value,
                             0.)
    # 当允许买空卖空操作时，需要考虑持有股票时卖出或买入，即开多仓和平多仓，以及开空仓和平空仓
    if allow_sell_short:

        # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 仓位差 * 当前总资产，此时持有份额为0
        cash_to_spend += np.where((position_diff < ptst) & (own_amounts <= 0),
                                  position_diff * total_value,
                                  0.)
        # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 仓位差 * 当前持有空头份额
        amounts_to_sell += np.where((position_diff > ptbt) & (own_amounts < 0),
                                    position_diff / previous_pos * own_amounts,
                                    0.)

    return cash_to_spend, amounts_to_sell


def _parse_ps_signals(signals, prices, own_amounts, own_cash, allow_sell_short):
    """ 解析PS类型的交易信号

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    prices: np.ndarray
        当前资产的价格
    own_amounts: np.ndarray
        当前持有的资产份额
    own_cash: float
        当前持有的现金
    allow_sell_short: bool
        是否允许卖空

    Returns
    -------
    tuple: (cash_to_spend, amounts_to_sell)
        cash_to_spend: np.ndarray, 买入资产的现金
        amounts_to_sell: np.ndarray, 卖出资产的数量
    """

    # 计算当前总资产
    total_value = np.sum(prices * own_amounts) + own_cash

    # 当不允许买空卖空操作时，只需要考虑持有股票时卖出或买入，即开多仓和平多仓
    # 当持有份额大于零时，平多仓：卖出数量 =交易信号 * 持仓份额，此时持仓份额需大于零
    amounts_to_sell = np.where((signals < 0) & (own_amounts > 0), signals * own_amounts, 0.)
    # 当持有份额不小于0时，开多仓：买入金额 =交易信号 * 当前总资产，此时不能持有空头头寸
    cash_to_spend = np.where((signals > 0) & (own_amounts >= 0), signals * total_value, 0.)

    # 当允许买空卖空时，允许开启空头头寸：
    if allow_sell_short:

        # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 交易信号 * 当前总资产
        cash_to_spend += np.where((signals < 0) & (own_amounts <= 0), signals * total_value, 0.)
        # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 交易信号 * 当前持有空头份额
        amounts_to_sell -= np.where((signals > 0) & (own_amounts < 0), signals * own_amounts, 0.)

    return cash_to_spend, amounts_to_sell


def _parse_vs_signals(signals, prices, own_amounts, allow_sell_short):
    """ 解析VS类型的交易信号

    Parameters
    ----------
    signals: np.ndarray
        交易信号
    prices: np.ndarray
        当前资产的价格
    own_amounts: np.ndarray
        当前持有的资产的数量
    allow_sell_short: bool
        是否允许卖空

    Returns
    -------
    tuple: (cash_to_spend, amounts_to_sell)
    - symbols: list of str, 产生交易信号的资产代码
    - positions: list of str, 产生交易信号的各各资产的头寸类型('long', 'short')
    - directions: list of str, 产生的交易信号的交易方向('buy', 'sell')
    - quantities: list of float, 所有交易信号的交易数量
    """

    # 计算各个资产的计划买入金额和计划卖出数量
    # 当持有份额大于零时，平多仓：卖出数量 = 信号数量，此时持仓份额需大于零
    amounts_to_sell = np.where((signals < 0) & (own_amounts > 0), signals, 0.)
    # 当持有份额不小于0时，开多仓：买入金额 = 信号数量 * 资产价格，此时不能持有空头头寸，必须为空仓或多仓
    cash_to_spend = np.where((signals > 0) & (own_amounts >= 0), signals * prices, 0.)

    # 当允许买空卖空时，允许开启空头头寸：
    if allow_sell_short:
        # 当持有份额小于等于零且交易信号为负，开空仓：买入空头金额 = 信号数量 * 资产价格
        cash_to_spend += np.where((signals < 0) & (own_amounts <= 0), signals * prices, 0.)
        # 当持有份额小于0（即持有空头头寸）且交易信号为正时，平空仓：卖出空头数量 = 交易信号 * 当前持有空头份额
        amounts_to_sell -= np.where((signals > 0) & (own_amounts < 0), -signals, 0.)

    return cash_to_spend, amounts_to_sell


def _signal_to_order_elements(shares,
                              cash_to_spend,
                              amounts_to_sell,
                              prices,
                              available_cash,
                              available_amounts,
                              moq_buy=0,
                              moq_sell=0,
                              allow_sell_short=False):
    """ 逐个计算每一只资产的买入和卖出的数量，将parse_pt/ps/vs_signal函数计算出的交易信号逐项转化为
    交易订单 trade_orders

    在生成交易信号时，需要考虑可用现金的总量以及可用资产的总量
    如果可用现金不足买入所有的股票，则将买入金额按照比例分配给各个股票
    如果可用资产不足计划卖出数量，则降低卖出的数量，同时在允许卖空的情况下，增加对应的空头买入信号

    Parameters
    ----------
    shares: list of str
        各个资产的代码
    cash_to_spend: np.ndarray
        各个资产的买入金额
    amounts_to_sell: np.ndarray
        各个资产的卖出数量
    prices: np.ndarray
        各个资产的价格
    available_cash: float
        可用现金
    available_amounts: np.ndarray
        可用资产的数量
    moq_buy: float, default 0
        买入的最小交易单位
    moq_sell: float, default 0
        卖出的最小交易单位
    allow_sell_short: bool, default False
        是否允许卖空，如果允许，当可用资产不足时，会增加空头买入信号

    Returns
    -------
    order_elements: tuple, (symbols, positions, directions, quantities, quoted_prices)
    - symbols: list of str, 产生交易信号的资产代码
    - positions: list of str, 产生交易信号的各各资产的头寸类型('long', 'short')
    - directions: list of str, 产生的交易信号的交易方向('buy', 'sell')
    - quantities: list of float, 所有交易信号的交易数量
    - quoted_prices: list of float, 所有交易信号的交易报价
    - remarks: list of str, 生成交易信号的说明，用于为trader提供提示
    """

    # 计算总的买入金额，调整买入金额，使得买入金额不超过可用现金
    total_cash_to_spend = np.sum(cash_to_spend)
    base_remark = ''
    if total_cash_to_spend > available_cash:
        available_to_plan_ratio = available_cash / total_cash_to_spend
        cash_to_spend = cash_to_spend * available_to_plan_ratio
        base_remark = f'Not enough available cash ({available_cash:.2f}), ' \
                      f'adjusted cash to spend to {available_to_plan_ratio:.1%}'

    # 逐个计算每一只资产的买入和卖出的数量
    symbols = []  # 股票代码
    positions = []  # 持仓类型
    directions = []  # 交易方向
    quantities = []  # 交易数量
    quoted_prices = []  # 交易报价
    remarks = []  # 生成交易信号的说明，用于为trader提供提示

    for i, sym in enumerate(shares):
        # 计算多头买入的数量
        if cash_to_spend[i] > 0.001:
            # 计算买入的数量
            quantity = np.round(cash_to_spend[i] / prices[i], AMOUNT_DECIMAL_PLACES)
            if moq_buy > 0:
                quantity = np.trunc(quantity / moq_buy) * moq_buy
            symbols.append(sym)
            positions.append('long')
            directions.append('buy')
            quantities.append(quantity)
            quoted_prices.append(prices[i])
            remarks.append(base_remark)
        # 计算空头买入的数量
        if (cash_to_spend[i] < -0.001) and allow_sell_short:
            # 计算买入的数量
            quantity = np.round(-cash_to_spend[i] / prices[i], AMOUNT_DECIMAL_PLACES)
            if moq_buy > 0:
                quantity = np.trunc(quantity / moq_buy) * moq_buy
            symbols.append(sym)
            positions.append('short')
            directions.append('buy')
            quantities.append(quantity)
            quoted_prices.append(prices[i])
            remarks.append(base_remark)
        # 计算多头卖出的数量
        if amounts_to_sell[i] < -0.001:
            # 计算卖出的数量，如果可用资产不足，则降低卖出的数量，并增加相反头寸的买入数量，买入剩余的数量
            if amounts_to_sell[i] < -available_amounts[i]:
                # 计算卖出的数量
                quantity = np.round(available_amounts[i], AMOUNT_DECIMAL_PLACES)
                if moq_sell > 0:
                    quantity = np.trunc(quantity / moq_sell) * moq_sell
                symbols.append(sym)
                positions.append('long')
                directions.append('sell')
                quantities.append(quantity)
                quoted_prices.append(prices[i])
                remarks.append(base_remark + f'Not enough available stock({available_amounts[i]}), '
                                             f'sell qty ({amounts_to_sell[i]}) reduced and rounded to {quantity}')
                # 如果allow_sell_short，增加反向头寸的买入信号
                if allow_sell_short:
                    quantity = np.round(- amounts_to_sell[i] - available_amounts[i], AMOUNT_DECIMAL_PLACES)
                    if moq_sell > 0:
                        quantity =np.trunc(quantity / moq_sell) * moq_sell
                    symbols.append(sym)
                    positions.append('short')
                    directions.append('buy')
                    quantities.append(quantity)
                    quoted_prices.append(prices[i])
                    remarks.append(base_remark + f'Allow sell short, continue to buy short positions {quantity}')
            else:
                # 计算卖出的数量，如果可用资产足够，则直接卖出
                quantity = np.round(-amounts_to_sell[i], AMOUNT_DECIMAL_PLACES)
                if moq_sell > 0:
                    quantity = np.trunc(quantity / moq_sell) * moq_sell
                symbols.append(sym)
                positions.append('long')
                directions.append('sell')
                quantities.append(quantity)
                quoted_prices.append(prices[i])
                remarks.append(base_remark)
        # 计算空头卖出的数量
        if (amounts_to_sell[i] > 0.001) and allow_sell_short:
            # 计算卖出的数量，如果可用资产不足，则降低卖出的数量，并增加相反头寸的买入数量，买入剩余的数量
            if amounts_to_sell[i] > available_amounts[i]:
                # 计算卖出的数量
                quantity = np.round(- available_amounts[i], 2)
                if moq_sell > 0:
                    quantity = np.trunc(quantity / moq_sell) * moq_sell
                symbols.append(sym)
                positions.append('short')
                directions.append('sell')
                quantities.append(quantity)
                quoted_prices.append(prices[i])
                remarks.append(base_remark + f'Not enough short position stock ({-available_amounts[i]}), '
                                             f'sell short qty ({amounts_to_sell[i]}) reduced and rounded to {quantity}')
                # 增加反向头寸的买入信号
                quantity = np.round(amounts_to_sell[i] + available_amounts[i], AMOUNT_DECIMAL_PLACES)
                if moq_sell > 0:
                    quantity = np.trunc(quantity / moq_sell) * moq_sell
                symbols.append(sym)
                positions.append('long')
                directions.append('buy')
                quantities.append(quantity)
                quoted_prices.append(prices[i])
                remarks.append(base_remark + f'Allow sell short, continue to buy long positions {quantity}')
            else:
                # 计算卖出的数量，如果可用资产足够，则直接卖出
                quantity = np.round(amounts_to_sell[i], AMOUNT_DECIMAL_PLACES)
                if moq_sell > 0:
                    quantity = np.trunc(quantity / moq_sell) * moq_sell
                symbols.append(sym)
                positions.append('short')
                directions.append('sell')
                quantities.append(quantity)
                quoted_prices.append(prices[i])
                remarks.append(base_remark)

    order_elements = (symbols, positions, directions, quantities, quoted_prices, remarks)
    return order_elements


def output_trade_order():
    """ 将交易订单输出到终端或TUI

    Returns
    -------
    order_id: int
        交易订单的id
    """
    pass


def submit_order(order_id, data_source=None):
    """ 将交易订单提交给交易平台或用户以等待交易结果，同时更新账户和持仓信息

    只有刚刚创建的交易订单（status == 'created'）才能提交，否则不需要再次提交
    在提交交易订单以前，对于买入订单，会检查账户的现金是否足够，如果不足，则会按比例调整交易订单的委托数量
    对于卖出订单，会检查账户的持仓是否足够，如果不足，则会按比例调整交易订单的委托数量
    交易订单提交后，会将交易订单的状态设置为submitted，同时将交易订单保存到数据库中
    - 只有使用submit_order才能将信号保存到数据库中，同时调整相应的账户和持仓信息

    Parameters
    ----------
    order_id: int
        交易订单的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    int, 交易订单的id
    None, 如果交易订单的状态不为created，则说明交易订单已经提交过，不需要再次提交
    """

    # 读取交易订单
    trade_order = read_trade_order(order_id, data_source=data_source)

    # 如果交易订单的状态不为created，则说明交易订单已经提交过，不需要再次提交
    if trade_order['status'] != 'created':
        return None

    # 实际上在parse_trade_signal的时候就已经检查过总买入数量与可用现金之间的关系了，这里不再检察
    # 如果交易方向为buy，则需要检查账户的现金是否足够
    position_id = trade_order['pos_id']
    position = get_position_by_id(position_id, data_source=data_source)
    pos_type = position['position']
    if pos_type == 'short':
        # TODO: position为short时做法不同，需要进一步调整
        raise NotImplementedError('short position orders submission is not realized')
    if trade_order['direction'] == 'buy':
        account_id = position['account_id']
        account = get_account(account_id, data_source=data_source)
        # 如果账户的现金不足，则输出警告信息
        if account['available_cash'] < trade_order['qty'] * trade_order['price']:
            logger.warning(f'Available cash {account["available_cash"]} is not enough for trade order: \n'
                           f'{trade_order}'
                           f'trade order might not be executed!')

    # 如果交易方向为sell，则需要检查账户的持仓是否足够
    elif trade_order['direction'] == 'sell':
        # 如果账户的持仓不足，则输出警告信息
        if position['available_qty'] < trade_order['qty']:
            logger.warning(f'Available quantity {position["available_qty"]} is not enough for trade order: \n'
                           f'{trade_order}'
                           f'trade order might not be executed!')

    # 将signal的status改为"submitted"，并将trade_signal写入数据库
    order_id = update_trade_order(order_id=order_id, data_source=data_source, status='submitted')
    # 检查交易订单

    return order_id


def cancel_order(order_id, data_source=None, config=None):
    """ 取消交易订单

    对于已经提交但尚未执行或者partially_fill的订单，可以取消订单，将订单的状态设置为 'canceled'
    取消订单时，生成这个订单的交易结果，交易结果的"canceled_qty"为订单的"qty"，交易结果的 "status" 为 "canceled"
    如果订单的状态为部分成交partial- filled，生成的交易结果的quantity为订单的数量减去已经成交的数量

    Parameters
    ----------
    order_id: int
        交易订单的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    config: dict, optional
        配置参数，主要包含股票和现金交割周期信息，如果为None，则使用默认的配置参数

    Returns
    -------
    int, 交易订单的id
    """
    # TODO: further test this function

    order_details = read_trade_order_detail(order_id=order_id, data_source=data_source)
    order_status = order_details['status']
    if order_status not in ['submitted', 'partial-filled']:
        raise RuntimeError(f'order status wrong: {order_status} cannot be canceled')

    order_results = read_trade_results_by_order_id(order_id=order_id, data_source=data_source)
    if not order_results.empty:
        total_filled_qty = np.round(
                order_results['filled_qty'].sum(),
                AMOUNT_DECIMAL_PLACES,
        )
        already_canceled_qty = np.round(
                order_results['canceled_qty'].sum(),
                AMOUNT_DECIMAL_PLACES,
        )
    else:
        total_filled_qty = 0.
        already_canceled_qty = 0.
    if already_canceled_qty > 0:
        # TODO: there is a bug: if order status is submitted, then canceled_qty should be 0
        raise RuntimeError(f'order status wrong: canceled qty should be 0 '
                           f'unless order is canceled! actual: {already_canceled_qty} for order \n{order_details}\n'
                           f'and result: \n{order_results}')
    remaining_qty = np.round(
            order_details['qty'] - total_filled_qty,
            AMOUNT_DECIMAL_PLACES,
    )
    # debug
    # print(f'[DEBUG]: canceling order {order_id}, order result:\n {order_results}\n'
    #       f'total filled qty: {total_filled_qty}\n'
    #       f'already canceled qty: {already_canceled_qty}\n'
    #       f'remaining qty: {remaining_qty}\n')

    if remaining_qty <= 0:
        raise RuntimeError(f'order status wrong: remaining qty should be larger than 0'
                           f'when order is partially filled, got {remaining_qty}')
    result_of_cancel = {
        'order_id':        order_id,
        'filled_qty':      0.,
        'price':           order_details['price'],
        'transaction_fee': 0.,
        'canceled_qty':    remaining_qty,
        'delivery_amount': 0,
        'delivery_status': 'ND',
    }
    process_trade_result(
            raw_trade_result=result_of_cancel,
            data_source=data_source,
            config=config
    )


def process_account_delivery(account_id, data_source=None, config=None):
    """ 处理account_id账户中所有持仓和现金的交割

    从交易历史中读取尚未交割的现金和持仓，根据config中的设置值 'cash_delivery_period' 和
    'stock_delivery_period' 执行交割，将完成交割的现金和持仓数量更新到现金和持仓的available
    中，并将已完成交割的交易结果的交割状态更新为"DL"

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    config: dict, optional
        配置参数, 默认为None, 表示使用默认的配置参数

    Returns
    -------
    list_of_delivery_result: list of dict,
        以列表形式返回的所有有效交割结果
    """

    if not isinstance(account_id, (int, np.int64)):
        raise TypeError('account_id must be an int')
    if config is None:
        config = {
            'cash_delivery_period': 0,
            'stock_delivery_period': 0,
        }
    if not isinstance(config, dict):
        raise TypeError('config must be a dict')

    undelivered_results = read_trade_results_by_delivery_status('ND', data_source=data_source)
    if undelivered_results is None:
        return

    delivery_result = []
    # 循环处理每一条未交割的交易结果：
    for result_id, result in undelivered_results.iterrows():

        res = deliver_trade_result(
                result_id=result_id,
                account_id=account_id,
                result=result.to_dict(),
                stock_delivery_period=config['stock_delivery_period'],
                cash_delivery_period=config['cash_delivery_period'],
                data_source=data_source,
        )

        if res:
            delivery_result.append(res)

    return delivery_result


def deliver_trade_result(result_id, account_id, result=None, stock_delivery_period=0, cash_delivery_period=0,
                         data_source=None):
    """ 处理交易结果的交割，给出交易结果ID，根据结交割周期修改可用现金/可用持仓，并修改结果的delivery_status为'DL'

    注意，如果delivery_status已经为DL，则不交割，直接返回
    如果result_id对应的account_id与参数account_id不符合，也不执行交割，直接返回

    Parameters
    ----------
    result_id: int
        结果ID，需要交割的交易结果
    account_id: int
        账户ID，如果result所属的account与account_id不匹配则不执行交割
    result: dict, default None
        交易结果，如果不给出，则通过result_id读取结果
    stock_delivery_period: int, default 0
        股票交割周期，单位为天
    cash_delivery_period: int, default 0
        现金交割周期，单位为天
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    delivery_result: dict
    交割结果：包含以下信息
    {
        'pos_id' : int, 更新的持仓ID，如果没有更新则为None
        'prev_qty': float, 更新前的资产可用持仓数量，如果没有更新则为None
        'updated_qty': float, 更新后的资产可用持仓数量，如果没有更新则为None
        'account_id': int, 更新的账户ID，如果没有更新则为None
        'prev_amount': float, 更新前的账户可用现金余额，如果没有更新则为None
        'updated_amount': float, 更新后的账户可用现金余额，如果没有更新则为None
    }
    """
    from .trade_recording import read_trade_result_by_id
    if result is None:
        result = read_trade_result_by_id(result_id=result_id, data_source=data_source)
    if not isinstance(result, dict):
        raise RuntimeError(f'Wrong trade result, expect a dict, got {type(result)} instead')
    if result['delivery_status'] != 'ND':
        # 如果交易结果已经交割过了，则不再交割
        return {}
    order_id = result['order_id']
    order_detail = read_trade_order_detail(order_id=order_id, data_source=data_source)

    if order_detail['account_id'] != account_id:
        # 如果订单不是发自account_id，则不予交割
        return {}

    # 读取交易方向，根据方向判断需要交割现金还是持仓，并分别读取现金/持仓的交割期
    trade_direction = order_detail['direction']
    if trade_direction == 'buy':
        delivery_period = stock_delivery_period
    elif trade_direction == 'sell':
        delivery_period = cash_delivery_period
    else:
        raise ValueError(f'Invalid direction: {trade_direction}')

    # 读取交易结果的execution_time，如果execution_time与现在的日期差小于交割期，则跳过
    execution_date = pd.to_datetime(result['execution_time']).date()
    current_date = pd.to_datetime('today').date()
    day_diff = (current_date - execution_date).days
    if day_diff < delivery_period:
        return {}

    # 可以开始执行交割
    delivery_result = {
        'order_id':         None,
        'pos_id':           None,
        'prev_qty':         None,
        'updated_qty':      None,
        'account_id':       None,
        'prev_amount':      None,
        'updated_amount':   None,
    }

    # 执行交割，更新现金/持仓的available，更新交易结果的delivery_status
    if trade_direction == 'buy':
        position_id = order_detail['pos_id']
        position = get_position_by_id(pos_id=position_id, data_source=data_source)
        delivery_result['order_id'] = order_id
        delivery_result['pos_id'] = position_id
        delivery_result['prev_qty'] = position['available_qty']

        update_position(
                position_id=position_id,
                data_source=data_source,
                available_qty_change=result['delivery_amount'],
        )
        position = get_position_by_id(pos_id=position_id, data_source=data_source)
        delivery_result['updated_qty'] = position['available_qty']

    elif trade_direction == 'sell':
        delivery_result['account_id'] = account_id
        account = get_account(account_id, data_source=data_source)
        delivery_result['order_id'] = order_id
        delivery_result['prev_amount'] = account['available_cash']
        update_account_balance(
                account_id=account_id,
                data_source=data_source,
                available_cash_change=result['delivery_amount'],
        )
        account = get_account(account_id, data_source=data_source)
        delivery_result['updated_amount'] = account['available_cash']
    else:
        raise RuntimeError(f'Wrong trade direction! {trade_direction}')

    update_trade_result(
            result_id=result_id,
            data_source=data_source,
            delivery_status='DL',
    )

    return delivery_result


def process_trade_result(raw_trade_result, data_source=None, config=None):
    """ 处理交易结果: 更新交易委托的状态，更新账户的持仓，更新持有现金金额

    交易结果一旦生成，其内容就不会再改变，因此不需要更新交易结果，只需要根据交易结果
    更新相应交易订单（委托）的状态，更新账户的持仓，更新账户的现金余额

    Parameters
    ----------
    raw_trade_result: dict
        原始交易结果, 与正式交易结果的区别在于，原始交易结果不包含execution_time字段
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    config: dict, optional
        配置参数, 默认为None, 表示使用默认的配置参数

    Returns
    -------
    result_id: int
        交易结果的id
    """

    if not isinstance(raw_trade_result, dict):
        raise TypeError(f'raw_trade_result must be a dict, got {type(raw_trade_result)} instead')

    order_id = raw_trade_result['order_id']
    order_detail = read_trade_order_detail(order_id, data_source=data_source)

    # 确认交易订单的状态不为 'created'. 'filled' or 'canceled'，如果是，则抛出异常
    if order_detail['status'] in ['created']:
        raise AttributeError(f'order {order_id} is noy submitted yet')
    if order_detail['status'] in ['filled', 'canceled']:
        raise AttributeError(f'order {order_id} has already been filled or canceled')
    # 交割历史交易结果
    if config is None:
        import qteasy as qt
        config = qt.QT_CONFIG
    if not isinstance(config, dict):
        raise TypeError('config must be a dict')

    # 读取交易订单的历史交易记录，计算尚未成交的数量：remaining_qty
    trade_results = read_trade_results_by_order_id(order_id, data_source=data_source)
    filled_qty = np.round(
            trade_results['filled_qty'].sum(),
            AMOUNT_DECIMAL_PLACES
    ) if trade_results is not None else 0
    remaining_qty = np.round(
            order_detail['qty'] - filled_qty,
            AMOUNT_DECIMAL_PLACES,
    )
    if not isinstance(remaining_qty, (int, float, np.int64, np.float64)):
        raise TypeError(f'qty {order_detail["qty"]} is not an integer')
    # 如果交易结果中的cancel_qty大于0，则将交易订单的状态设置为 'canceled'，同时确认 canceled_qty等于remaining_qty
    if raw_trade_result['canceled_qty'] > 0:
        if raw_trade_result['canceled_qty'] != remaining_qty:
            raise RuntimeError(f'canceled_qty {raw_trade_result["canceled_qty"]} '
                               f'does not match remaining_qty {remaining_qty}')
        order_detail['status'] = 'canceled'
    # 如果交易结果中的canceled_qty等于0，则检查filled_qty的数量是大于remaining_qty，如果大于，则抛出异常
    else:
        if raw_trade_result['filled_qty'] > remaining_qty:
            raise RuntimeError(f'filled_qty {raw_trade_result["filled_qty"]} '
                               f'is greater than remaining_qty {remaining_qty}')

        # 如果filled_qty等于remaining_qty，则将交易订单的状态设置为 'filled'
        elif raw_trade_result['filled_qty'] == remaining_qty:
            order_detail['status'] = 'filled'

        # 如果filled_qty小于remaining_qty，则将交易订单的状态设置为 'partial-filled'
        elif raw_trade_result['filled_qty'] < remaining_qty:
            order_detail['status'] = 'partial-filled'

    # 计算交易后持仓数量的变化 position_change 和现金的变化值 cash_change
    if order_detail['direction'] == 'sell':
        position_change = - raw_trade_result['filled_qty']
        cash_change = np.round(
                raw_trade_result['filled_qty'] * raw_trade_result['price'] - raw_trade_result['transaction_fee'],
                CASH_DECIMAL_PLACES,
        )
        # print(f'[DEBUG]: in process_trade_result(): selling stock, position_change: {position_change}\n'
        #       f'cash_change = {raw_trade_result["filled_qty"]} * {raw_trade_result["price"]} - '
        #       f'{raw_trade_result["transaction_fee"]} = {cash_change}, ')
    elif order_detail['direction'] == 'buy':
        position_change = raw_trade_result['filled_qty']
        cash_change = np.round(
                - raw_trade_result['filled_qty'] * raw_trade_result['price'] - raw_trade_result['transaction_fee'],
                CASH_DECIMAL_PLACES,
        )
        # print(f'[DEBUG]: in process_trade_result(): buying stock, position_change: {position_change}\n'
        #       f'cash_change = - {raw_trade_result["filled_qty"]} * {raw_trade_result["price"]} - '
        #       f'{raw_trade_result["transaction_fee"]} = {cash_change}, ')
    else:  # for any other unexpected direction
        raise ValueError(f'Invalid direction: {order_detail["direction"]}')

    position_info = get_position_by_id(order_detail['pos_id'], data_source=data_source)
    owned_qty = position_info['qty']
    available_qty = position_info['available_qty']
    position_cost = position_info['cost']
    if position_cost is None:
        position_cost = 0

    available_cash = get_account_cash_availabilities(order_detail['account_id'], data_source=data_source)[1]

    # print(f'[DEBUG]: updating account balance and position for order {order_id}...\n'
    #       f'result: {raw_trade_result}\n'
    #       f'position_change: {position_change}\n'
    #       f'cash_change: {cash_change}\n'
    #       f'available_qty: {available_qty}\n'
    #       f'available_cash: {available_cash}\n')

    # 如果position_change小于available_position_amount，则抛出异常
    if available_qty + position_change < 0:
        raise RuntimeError(f'position_change {position_change} is greater than '
                           f'available position amount {available_qty}')
    # 如果cash_change小于available_cash，则抛出异常
    if available_cash + cash_change < 0:
        raise RuntimeError(f'cash_change {cash_change} is greater than '
                           f'available cash {available_cash}')

    # 计算并生成交易结果的交割数量和交割状态，如果是买入信号，交割数量为position_change，如果是卖出信号，交割数量为cash_change
    if order_detail['direction'] == 'buy':
        raw_trade_result['delivery_amount'] = position_change
    elif order_detail['direction'] == 'sell':
        raw_trade_result['delivery_amount'] = cash_change
    else:
        raise ValueError(f'direction must be buy or sell, got {order_detail["direction"]} instead')
    raw_trade_result['delivery_status'] = 'ND'

    # 至此，如果前面所有步骤都没有发生错误，则交易结果有效，生成交易结果的execution_time字段，正式保存交易结果
    execution_time = pd.to_datetime('today').strftime('%Y-%m-%d %H:%M:%S')  # 产生本地时区时间
    raw_trade_result['execution_time'] = execution_time
    result_id = write_trade_result(raw_trade_result, data_source=data_source)

    # 更新账户的持仓和现金余额和订单状态
    # TODO: 这里可能会有Bug：为了避免在更新账户余额和持仓时出现错误，需要将更新账户余额和持仓的操作放在一个事务中
    #  否则可能出现更新账户余额成功，但更新持仓失败的情况，或订单状态更新失败的情况

    # 如果direction为buy，则同时更新cash_amount和available_cash，如果direction为sell，则只更新cash_amount
    if order_detail['direction'] == 'buy':
        update_account_balance(
                account_id=order_detail['account_id'],
                data_source=data_source,
                cash_amount_change=cash_change,
                available_cash_change=cash_change,
        )
        # calculate new cost if (position_change + owned_qty) is not 0
        prev_cost = position_cost * owned_qty
        if position_change + owned_qty == 0:
            new_cost = 0
        else:
            additional_cost = position_change * raw_trade_result['price'] + raw_trade_result['transaction_fee']
            new_cost = (prev_cost + additional_cost) / (owned_qty + position_change)
        update_position(
                position_id=order_detail['pos_id'],
                data_source=data_source,
                qty_change=position_change,
                cost=new_cost,
        )
    # 如果direction为sell，则同时更新qty和available_qty，如果direction为buy，则只更新qty
    else:  # order_detail['direction'] == 'sell', 因为其他情况已经在前面raise ValueError了
        update_account_balance(
                account_id=order_detail['account_id'],
                data_source=data_source,
                cash_amount_change=cash_change,
        )
        # calculate new cost
        prev_cost = position_cost * owned_qty
        if owned_qty + position_change == 0:  # 如果卖出后持仓为0，则成本为0
            new_cost = 0
        else:
            additional_cost = position_change * raw_trade_result['price'] + raw_trade_result['transaction_fee']
            new_cost = (prev_cost + additional_cost) / (owned_qty + position_change)
        update_position(
                position_id=order_detail['pos_id'],
                data_source=data_source,
                qty_change=position_change,
                available_qty_change=position_change,
                cost=new_cost,
        )
    # 更新交易订单的状态
    update_trade_order(order_id, data_source=data_source, status=order_detail['status'])

    return result_id


def get_last_trade_result_summary(account_id, shares=None, data_source=None):
    """ 获取指定账户的最近的交易结果汇总，获取的结果为ndarray，按照shares的顺序排列

    结果包含最近一次成交量（正数表示买入，负数表示卖出）以及最近一次成交价格，如果最近没有成交，
    则返回值为0/0

    Parameters
    ----------
    account_id: str,
        账户ID
    shares: list of str,
        股票代码列表, 如果不给出股票代码列表，则返回所有持仓股票的最近一次成交量和成交价格
    data_source: str,
        数据源名称

    Returns
    -------
    tuple: (symbols, amounts_changed, trade_prices)
    symbols: ndarray of str,
        股票代码列表
    amounts_changed: ndarray of float,
        最近一次成交量
    trade_prices: ndarray of float,
        最近一次成交价格
    """
    # TODO: test this function, causing error in live mode

    # read all filled and partially filled orders

    all_positions = get_account_positions(account_id=account_id, data_source=data_source)
    if all_positions.empty and (shares is None):
        return [], np.array([]), np.array([])

    all_position_symbols = all_positions['symbol'].to_dict()
    if shares is None:
        shares = list(all_position_symbols.values())

    if isinstance(shares, str):
        shares = str_to_list(shares)
    else:
        if not isinstance(shares, list):
            raise ValueError(f'shares must be a list of symbols, got {type(shares)} instead')

    all_orders = query_trade_orders(
            account_id=account_id,
            data_source=data_source,
    )
    if all_orders.empty:
        return shares, np.zeros(shape=(len(shares),)), np.zeros(shape=(len(shares),))
    all_orders = all_orders[all_orders['status'].isin(['filled', 'partial-filled'])]

    all_results = read_trade_results_by_order_id(
            order_id=all_orders.index.tolist(),
            data_source=data_source,
    )

    if all_orders.empty or (all_results is None):
        return shares, np.zeros(shape=(len(shares),)), np.zeros(shape=(len(shares),))

    # 将交易订单和交易结果合并生成订单交易记录
    all_order_results = all_orders.join(
            all_results.set_index('order_id'),
            how='left',
            lsuffix='-o',
            rsuffix='-e',
    )
    all_order_results = all_order_results.sort_values(by='execution_time')
    # 所有卖出的交易结果的filled_qty为负数，所有买入的交易结果的filled_qty为正数
    all_order_results['filled_qty'] = np.where(
            all_order_results['direction'] == 'sell',
            -all_order_results['filled_qty'],
            all_order_results['filled_qty']
    )

    # 如果同一个order有多次成交记录，则需计算多次成交记录的总数量，并计算多次成交的平均价格
    all_order_results['filled_qty'] = all_order_results['filled_qty'].groupby('order_id').sum()
    all_order_results['price-e'] = all_order_results['price-e'].groupby('order_id').mean()

    # 然后按照position分组并选取时间最后的交易结果记录
    last_trades_by_pos = all_order_results.groupby('pos_id').last()
    # 从结果中读取成交量和平均成交价格
    last_filled_qty = last_trades_by_pos['filled_qty'].to_dict()
    last_filled_price = last_trades_by_pos['price-e'].to_dict()
    # 重新整理key的顺序
    last_filled_qty = {all_position_symbols[k]: v for k, v in last_filled_qty.items()}
    last_filled_price = {all_position_symbols[k]: v for k, v in last_filled_price.items()}

    # update filled qty and filled prices with last filled qty and last filled price
    shares_filled_qty = {k: 0 for k in shares}
    shares_filled_price = {k: 0 for k in shares}
    shares_filled_qty.update(last_filled_qty)
    shares_filled_price.update(last_filled_price)
    last_filled_qty = shares_filled_qty
    last_filled_price = shares_filled_price

    # 删除生成的结果中不需要的shares
    last_filled_qty = {k: v for k, v in last_filled_qty.items() if k in shares}
    last_filled_price = {k: v for k, v in last_filled_price.items() if k in shares}

    amounts_changed = np.array(list(last_filled_qty.values()), dtype='float')
    trade_prices = np.array(list(last_filled_price.values()), dtype='float')
    return shares, amounts_changed, trade_prices


def _trade_time_index(start=None,
                      end=None,
                      periods=None,
                      freq=None,
                      trade_days_only=True,
                      market='SSE',
                      include_start=True,
                      include_end=True,
                      start_am='9:30:00',
                      end_am='11:30:00',
                      include_start_am=True,
                      include_end_am=True,
                      start_pm='13:00:00',
                      end_pm='15:00:00',
                      include_start_pm=False,
                      include_end_pm=True):
    """ 通过start/end/periods/freq生成一个符合交易时间段的datetime series，这个序列中的
    每一个时间都在交易时段内，排除所有的交易日

    Parameters
    ----------
    start: datetime like str,
        日期时间序列的开始日期/时间
    end: datetime like str,
        日期时间序列的终止日期/时间
    periods: int
        日期时间序列的分段数量
    freq: str, {'min', 'h', 'd', 'M'}
        日期时间序列的频率
    trade_days_only: bool, Default True
        是否剔除所有非交易日，默认True，如果为False，则保留所有的非交易日
    market: str, {'SSE', 'SZSE', 'SHFE', ...}, Default 'SSE'
        交易市场类型，不同的交易市场交易日定义可能不同, 默认上交所，trade_days_only为False时无效
    include_start: bool, Default True
        日期时间序列是否包含开始日期/时间
    include_end: bool, Default True
        日期时间序列是否包含结束日期/时间
    start_am: datetime like str, Default '9:30:00'
        早晨交易时段的开始时间
    end_am: datetime like str, Default '11:30:00'
        早晨交易时段的结束时间
    include_start_am: bool, Default True
        早晨交易时段是否包括开始时间
    include_end_am: bool, Default True
        早晨交易时段是否包括结束时间
    start_pm: datetime like str, Default '13:00:00'
        下午交易时段的开始时间
    end_pm: datetime like str, Default '15:00:00'
        下午交易时段的结束时间
    include_start_pm: bool, Default False
        下午交易时段是否包含开始时间
    include_end_pm: bool, Default True
        下午交易时段是否包含结束时间

    Returns
    -------
    time_index: pd.DatetimeIndex

    Examples
    --------
    # target time index not in trading day
    >>> _trade_time_index(start='2021-01-01', end='2021-01-02', freq='h')
    DatetimeIndex([], dtype='datetime64[ns]', freq=None)
    # target time index is in trading day
    >>> _trade_time_index(start='2021-02-01', end='2021-02-02', freq='h')
    DatetimeIndex(['2020-02-01 09:30:00', '2020-02-01 10:30:00',
                   '2020-02-01 11:30:00', '2020-02-01 13:00:00',
                   '2020-02-01 14:00:00', '2020-02-01 15:00:00',
                   '2020-02-02 09:30:00', '2020-02-02 10:30:00',
                   '2020-02-02 11:30:00', '2020-02-02 13:00:00',
                   '2020-02-02 14:00:00', '2020-02-02 15:00:00'],
                    dtype='datetime64[ns]', freq=None)
    """
    # 检查输入数据, freq不能为除了min、h、d、w、m、q、a之外的其他形式
    if freq is not None:
        freq = str(freq).lower()
    # 检查时间序列区间的开闭状况
    closed = None
    if include_start:
        closed = 'left'
    if include_end:
        closed = 'right'
    if include_start and include_end:
        closed = None

    time_index = pd.date_range(start=start, end=end, periods=periods, freq=freq, closed=closed)

    if trade_days_only:
        # 剔除time_index中的non-trade day
        from qteasy import QT_TRADE_CALENDAR as calendar
        calendar = calendar.is_open.unstack(level='exchange')
        try:
            calendar = calendar[market]
        except Exception as e:
            raise RuntimeError(f'Wrong market type is given, {e}')
        trade_cal = calendar.reindex(index=time_index)
        # 如果time_index不是从某天的00:00:00开始，则trade_cal中的第一个值会为nan
        # 此时需要用检查trade_cal的日期，填充正确的交易日标记
        if pd.isna(trade_cal.iloc[0]):
            date = pd.to_datetime(time_index[0].date())
            trade_cal.iloc[0] = calendar.loc[date]
        trade_cal = trade_cal.fillna(method='ffill')
        time_index = trade_cal.loc[trade_cal == 1].index

    # 判断time_index的freq，当freq小于一天时，需要按交易时段取出部分index
    if time_index.freqstr is not None:
        freq_str = time_index.freqstr.lower().split('-')[0]
    else:
        freq_str = time_index.inferred_freq
        if freq_str is not None:
            freq_str = freq_str.lower()
        else:
            time_delta = time_index[1] - time_index[0]
            if time_delta < pd.Timedelta(1, 'd'):
                freq_str = 'h'
            else:
                freq_str = 'd'
    ''' freq_str有以下几种不同的情况：
        min:        T
        hour:       H
        day:        D
        week:       W-SUN/...
        month:      M
        quarter:    Q-DEC/...
        year:       A-DEC/...
        由于周、季、年三种情况存在复合字符串，因此需要split
    '''
    if freq_str[-1:].lower() in ['t', 'h']:
        idx_am = time_index.indexer_between_time(
                start_time=start_am,
                end_time=end_am,
                include_start=include_start_am,
                include_end=include_end_am,
        )
        idx_pm = time_index.indexer_between_time(
                start_time=start_pm,
                end_time=end_pm,
                include_start=include_start_pm,
                include_end=include_end_pm,
        )
        idxer = np.union1d(idx_am, idx_pm)
        return time_index[idxer]
    else:
        return time_index


def get_symbol_names(datasource, symbols, asset_types: list = None, refresh: bool = False):
    """ 获取股票代码对应的股票名称, 必须给出完整的代码，如果代码错误，返回值为'N/A'，如果代码正确但
    基础数据表未下载，则返回值为'N/A'

    Parameters
    ----------
    datasource: DataSource
        数据源
    symbols: str or list of str
        股票代码列表
    asset_types: list, default None
        资产类型列表，如果给出，则只返回给定资产类型的股票名称，如果不给出，则返回所有资产类型的股票名称
    refresh: bool, default False
        是否刷新缓存，默认情况下从缓存数据中读取基本信息以加快速度，如果数据源中的数据已更新，需要刷新缓存

    Returns
    -------
    names: list
        股票名称列表

    Examples
    --------
    >>> get_symbol_names(datasource, '000001.SZ')
    ['平安银行']
    >>> get_symbol_names(datasource, ['000001.SZ', '000002.SZ'])
    ['平安银行', '万科A']
    """

    if isinstance(symbols, str):
        symbols = str_to_list(symbols)
    if not isinstance(symbols, list):
        raise TypeError(f'symbols must be str or list of str, got {type(symbols)} instead')

    if asset_types is None:
        asset_types = ['stock', 'index', 'fund', 'future', 'option']
    else:
        if isinstance(asset_types, str):
            asset_types = str_to_list(asset_types)
        if not isinstance(asset_types, list):
            raise TypeError(f'asset_types must be str or list of str, got {type(asset_types)} instead')
        asset_types = [asset_type.lower() for asset_type in asset_types]
        if not all([asset_type in ['stock', 'index', 'fund', 'future', 'option'] for asset_type in asset_types]):
            raise ValueError(f'invalid asset_types: {asset_types}, must be one of '
                             f'["stock", "index", "fund", "future", "option"]')

    df_s, df_i, df_f, df_ft, df_o = datasource.get_all_basic_table_data(
            raise_error=False,
            refresh_cache=refresh,
    )
    all_data_types = {
        'stock':  df_s[['name']] if not df_s.empty else pd.DataFrame(),
        'index':  df_i[['name']] if not df_i.empty else pd.DataFrame(),
        'fund':   df_f[['name']] if not df_f.empty else pd.DataFrame(),
        'future': df_ft[['name']] if not df_ft.empty else pd.DataFrame(),
        'option': df_o[['name']] if not df_o.empty else pd.DataFrame(),
    }
    all_basics = pd.concat(
            (
                all_data_types[asset_type.lower()] for asset_type in asset_types
            ),
    )
    try:
        names_found = all_basics.reindex(index=symbols).name.tolist()
    except Exception as e:
        raise RuntimeError(f'Error in get_symbol_names(): {e}')
    # replace all nan with 'N/A'
    names_found = ['N/A' if pd.isna(name) else name for name in names_found]

    return names_found
