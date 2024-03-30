# coding=utf-8
# ======================================
# File:     optimization.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-03-12
# Desc:
#   Core functions for strategy optimization
#  and parameter searching
# ======================================

import pandas as pd
import numpy as np
import time
import math

from concurrent.futures import ProcessPoolExecutor, as_completed

from .backtest import apply_loop, process_loop_results, _get_complete_hist
from .history import HistoryPanel, stack_dataframes
from .utilfuncs import sec_to_duration, progress_bar
from .utilfuncs import next_market_trade_day
from .space import Space, ResultPool
from .finance import CashPlan, set_cost
from .qt_operator import Operator
from .evaluate import evaluate, performance_statistics
from ._arg_validators import ConfigDict


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
    complete_values = None
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
    import os
    from qteasy import QT_TRADE_LOG_PATH
    log_file_path_name = os.path.join(QT_TRADE_LOG_PATH, 'trade_log.csv')
    res_dict['trade_log'] = pd.read_csv(log_file_path_name) if log_backtest else None
    log_file_path_name = os.path.join(QT_TRADE_LOG_PATH, 'trade_records.csv')
    res_dict['trade_record'] = pd.read_csv(log_file_path_name) if log_backtest else None
    res_dict['complete_history'] = complete_values
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

    TODO: 当numpy版本高于1.21时，这个算法在parallel==True时会有极大的效率损失，应优化

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
            # TODO: progress bar does not work properly, find a way to get progress bar working
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
