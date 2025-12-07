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
import logging
from typing import Union, Optional, Generator

from concurrent.futures import ProcessPoolExecutor, as_completed

from qteasy.qt_operator import Operator

from qteasy.backtest import (
    Backtester,
    generate_cash_invest_and_delivery_arrays,
)

from qteasy.history import (
    HistoryPanel,
    stack_dataframes,
)

from qteasy.utilfuncs import (
    sec_to_duration,
    progress_bar,
    str_to_list,
)

from qteasy.space import (
    Space,
    ResultPool,
)

from qteasy.finance import (
    CashPlan,
)


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


class Optimizer:
    """ 最优参数搜索器对象

    Parameters
    ----------

    Returns
    -------
    """

    def __init__(self,
                 *,
                 op: Operator,
                 method: str,
                 shares: list[str],
                 pool_size: int,
                 opti_target: str,
                 opti_direction: str,
                 parallel: bool,
                 opti_start_date: str,
                 opti_end_date: str,
                 test_start_date: str,
                 test_end_date: str,
                 opti_cash_plan: CashPlan,
                 test_cash_plan: CashPlan,
                 cost_params: np.ndarray,  # 交易成本参数
                 signal_parsing_params: dict,  # 交易信号解析参数
                 trading_moq_params: dict,  # 交易最小单位参数
                 trading_delivery_params: dict,  # 交易交割参数
                 logger: Optional[logging.Logger] = None):
        """初始化Optimizer对象，设置基本参数

        Parameters
        ----------
        op: Operator
            交易操作对象，包含交易信号生成和交易执行的逻辑
        method: str
            优化方法名称，目前支持的优化方法包括：
                'grid'：网格搜索法
                'montecarlo'：蒙特卡洛法
                'incremental'：增量递进搜索法
                'ga'：遗传算法
                'gradient'：梯度下降法
                'pso'：粒子群优化算法
                'aco'：蚁群优化算法
        shares: list[str]
            交易标的列表，包含所有交易标的的代码
        pool_size: int
            优化结果池的大小，表示在优化过程中保存的最佳参数组合数量
        opti_target: str
            优化目标名称，用于指定优化过程中需要最大化或最小化的性能指标
        opti_direction: str
            优化方向，取值为 'maximize' 或 'minimize'，表示优化目标是最大化还是最小化
        opti_start_date: str
            优化区间开始日期，格式为 'YYYY-MM-DD' 或 'YYYYMMDD'
        opti_end_date: str
            优化区间结束日期，格式为 'YYYY-MM-DD' 或 'YYYYMMDD'
        test_start_date: str
            测试区间开始日期，格式为 'YYYY-MM-DD' 或 'YYYYMMDD'
        test_end_date: str
            测试区间结束日期，格式为 'YYYY-MM-DD' 或 'YYYYMMDD'
        opti_cash_plan: CashPlan,
            现金投资计划
        test_cash_plan: CashPlan,
            现金投资计划
        cost_params: np.ndarray
            交易成本参数，包括买入费率、卖出费率、最低买入费用、最低卖出费用、交易滑点
            buy_rate: float, 交易成本：固定买入费率
            sell_rate: float, 交易成本：固定卖出费率
            buy_min: float, 交易成本：最低买入费用
            sell_min: float, 交易成本：最低卖出费用
            slipage: float, 交易成本：滑点
        signal_parsing_params: dict
            交易信号解析参数字典，包含解析交易信号所需的所有参数，通常是parse_signal_parsing_params()函数的输出
        trading_moq_params: dict
            交易最小单位参数字典，包含交易最小单位相关的所有参数，通常是parse_trading_moq_params()函数的输出
        trading_delivery_params: dict
            交易交割参数字典，包含交易交割相关的所有参数，通常是parse_trading_delivery_params()函数的输出
        logger: Optional[logging.Logger]
            可选的日志记录器对象，用于记录回测过程中的日志信息"""

        # 参数基础校验
        assert isinstance(op, Operator), "op must be an instance of Operator"
        if isinstance(shares, str):
            shares = str_to_list(shares)
        assert isinstance(shares, list) and all(isinstance(s, str) for s in shares), "shares must be a list of strings"
        if not isinstance(method, str):
            raise ValueError("method must be a string")
        if method not in self.AVAILABLE_OPTIMIZERS:
            raise ValueError(
                    f"method {method} is not supported. Available methods are: {list(self.AVAILABLE_OPTIMIZERS.keys())}")
        if not isinstance(pool_size, int) or pool_size <= 0:
            raise ValueError("pool_size must be a positive integer")
        if opti_direction not in ['maximize', 'minimize']:
            raise ValueError("opti_direction must be either 'maximize' or 'minimize'")
        if opti_target not in ['fv', 'vol', 'mdd']:
            raise ValueError("opti_target must be a valid performance metric: 'fv', 'vol', or 'mdd'")

        # 1，所有基本属性
        self.opti_method = method
        self.opti_func = self.AVAILABLE_OPTIMIZERS[method]

        self.op = op
        self.op_signals: Optional[np.ndarray] = None  # 回测生成的交易信号表格，实际上在op内也可以存储
        self.shares = shares
        self.opti_method = method
        self.opti_target = opti_target
        self.opti_direction = opti_direction

        self.opti_start = opti_start_date
        self.opti_end = opti_end_date
        self.test_start = test_start_date
        self.test_end = test_end_date

        self.opti_cash_plan = opti_cash_plan
        self.test_cash_plan = test_cash_plan

        self.cost_params = cost_params
        self.signal_parsing_params = signal_parsing_params
        self.trading_moq_params = trading_moq_params
        self.trading_delivery_params = trading_delivery_params
        # self.opti_data_package = opti_data_package
        # self.test_data_package = test_data_package
        # self.opti_trade_price_data = opti_trade_price_data
        # self.test_trade_price_data = test_trade_price_data
        self.logger = logger

        # 2，回测器属性
        self.opti_backtester: Optional[Backtester] = None  # 优化区间回测器对象
        self.test_backtester: Optional[Backtester] = None  # 测试区间回测器对象

        # 用于存储优化结果参数的属性
        self.result_pool = ResultPool(capacity=pool_size)
        self.result_pool_size = pool_size  # 优化结果池的大小
        self.parallel = parallel  # 是否启用多进程计算方式
        self.current_parameters = None  # 当前优化参数
        self.best_parameters = None  # 最佳优化参数
        self.best_performance = None  # 最佳性能评分

    def optimize(self,
                 trade_price_data:np.ndarray):
        # 调用指定的优化方法进行最优参数搜索

        # 现金投入和交割数据表
        (opti_cash_investment_array,
         opti_cash_inflation_array,
         opti_delivery_day_indicators) = generate_cash_invest_and_delivery_arrays(
                invest_cash_plan=self.opti_cash_plan,
                op_schedule=self.op.group_timing_table.index,
        )

        # Optimizer对象包含两个Backtester回测器对象，一个用于优化区间的回测，另一个用于测试区间的回测
        self.opti_backtester = Backtester(
                op=self.op,
                shares=self.shares,
                cash_plan=self.opti_cash_plan,
                cash_investment_array=opti_cash_investment_array,
                cash_inflation_array=opti_cash_inflation_array,
                delivery_day_indicators=opti_delivery_day_indicators,
                cost_params=self.cost_params,
                signal_parsing_params=self.signal_parsing_params,
                trading_moq_params=self.trading_moq_params,
                trading_delivery_params=self.trading_delivery_params,
                trade_price_data=trade_price_data,
                logger=self.logger,
        )

        s_range, s_type = self.op.opt_space_par
        search_space = Space(s_range, s_type)  # 生成参数空间
        search_config = {
            'maximize_target': True if self.opti_direction == 'maximize' else False,
        }

        self.opti_func(
                space=search_space,
                search_config=search_config,
        )

        return self

    def validate(self,
                 trade_price_data:np.ndarray):
        # 验证optimize过程中产生的交易参数在测试区间的表现
        # if self.result_pool.is_empty():
        #     pass

        # 现金投入和交割数据表
        (test_cash_investment_array,
         test_cash_inflation_array,
         test_delivery_day_indicators) = generate_cash_invest_and_delivery_arrays(
                invest_cash_plan=self.test_cash_plan,
                op_schedule=self.op.group_timing_table.index,
        )

        self.test_backtester = Backtester(
                op=self.op,
                shares=self.shares,
                cash_plan=self.test_cash_plan,
                cash_investment_array=test_cash_investment_array,
                cash_inflation_array=test_cash_inflation_array,
                delivery_day_indicators=test_delivery_day_indicators,
                cost_params=self.cost_params,
                signal_parsing_params=self.signal_parsing_params,
                trading_moq_params=self.trading_moq_params,
                trading_delivery_params=self.trading_delivery_params,
                trade_price_data=trade_price_data,
                logger=self.logger,
        )

        raise NotImplementedError

    def _evaluate_parameter(self, par_values: tuple) -> float:
        """ 使用一组策略参数进行回测，并返回回测结果的评价指标字典

        Parameters
        ----------
        par_values: tuple
            策略参数值元组，元组中的每一个值对应策略空间中的一个参数

        Returns
        -------
        """
        self.op.set_opt_par_values(par_values=par_values)
        # 在优化区间进行回测
        self.opti_backtester.run()
        if self.opti_target == 'fv':
            return self.opti_backtester.trade_result_final_value()
        elif self.opti_target == 'vol':
            return self.opti_backtester.trade_result_volatility()
        elif self.opti_target == 'mdd':
            return self.opti_backtester.trade_result_max_drawdown()
        else:
            raise ValueError(f'Unsupported optimization target: {self.opti_target}')

    def _evaluate_parameters(self,
                             total: int,
                             par_value_list: Union[list, tuple, Generator],
                             parallel: bool,
                             epoch_id: int = 1) -> ResultPool:
        """ 循环批量运行self._evaluate_parameter函数，生成结果后存入结果池中

        Parameters
        ----------
        total: int
            参数组合总数量，用于进度条显示
        par_value_list: list/tuple/Generator
            策略参数值列表或生成器，列表或生成器中的每一个元素都是一组策略参数值元组
        parallel: bool
            是否启用多进程计算方式，如果是True，则启用多进程计算方式利用所有的CPU核心计算，
            否则使用单进程计算
        epoch_id: int
            当前优化轮次编号，默认为1

        Returns
        -------
            pool，一个Pool对象，包含经过筛选后的所有策略参数以及它们的性能表现

        """

        # 启用多进程计算方式利用所有的CPU核心计算
        if parallel:
            # 启用并行计算
            self._evaluate_parameters_parallel(
                    total=total,
                    par_value_list=par_value_list,
                    epoch_id=epoch_id,
            )
        # 禁用多进程计算方式，使用单进程计算
        else:
            self._evaluate_parameters_sequential(
                    total=total,
                    par_value_list=par_value_list,
                    epoch_id=epoch_id,
            )

        return self.result_pool

    def _evaluate_parameters_parallel(self,
                                      total: int,
                                      par_value_list: Union[list, tuple, Generator],
                                      epoch_id: int) -> ResultPool:
        """ 并行循环批量运行evaluate_parameters()
        """
        i = 0
        best_so_far = 0

        # 启用并行计算
        with ProcessPoolExecutor() as proc_pool:
            futures = {proc_pool.submit(self._evaluate_parameter, par): par for par in
                       par_value_list}
        for f in as_completed(futures):
            target_value = f.result()
            self.result_pool.push(item=futures[f], perf=target_value, extra=None)
            i += 1
            if target_value > best_so_far:
                best_so_far = target_value
            if i % 10 == 0:
                progress_bar(i, total, comments=f'Epoch:{epoch_id}: best performance: {best_so_far:.3f}')

        # 将当前参数以及评价结果成对压入参数池中，并返回所有成对参数和评价结果
        progress_bar(i, i)

        return self.result_pool

    def _evaluate_parameters_sequential(self,
                                        total: int,
                                        par_value_list: Union[list, tuple, Generator],
                                        epoch_id: int) -> ResultPool:
        """ 顺序循环运行evaluate_parameters()方法
        """
        i = 0
        best_so_far = 0

        for par in par_value_list:
            target_value = self._evaluate_parameter(par_values=par)
            self.result_pool.push(item=par, perf=target_value, extra=None)
            i += 1
            if target_value > best_so_far:
                best_so_far = target_value
            if i % 10 == 0:
                progress_bar(i, total, comments=f'Epoch:{epoch_id}: best performance: {best_so_far:.3f}')

        # 将当前参数以及评价结果成对压入参数池中，并返回所有成对参数和评价结果
        progress_bar(i, i)

        return self.result_pool

    def _search_grid(self,
                     space: Space,
                     search_config: dict) -> None:
        """ 最优参数搜索算法1: 网格搜索法

        在整个参数空间中建立一张间距固定的"网格"，搜索网格的所有交点所在的空间点，
        根据该点的参数生成操作信号、回测后寻找表现最佳的一组或多组参数
        与该算法相关的设置选项有：
        grid_size:  网格大小，float/int/list/tuple 当参数为数字时，生成空间所有方向
                    上都均匀分布的网格；当参数为list或tuple时，可以在空间的不同方向
                    上生成不同间隔大小的网格。list或tuple的维度须与空间的维度一致

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """

        # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
        par_generator, total = space.extract(search_config.get('sample_count'))
        st = time.time()
        pool = self._evaluate_parameters(
                total=total,
                par_value_list=par_generator,
                parallel=self.parallel
        )
        pool.cut(search_config.get('maximize_target'))
        et = time.time()
        print(f'\nOptimization completed, total time consumption: {sec_to_duration(et - st)}')

    def _search_montecarlo(self,
                           space: Space,
                           search_config: dict) -> None:
        """ 最优参数搜索算法2: 蒙特卡洛法

        从待搜索空间中随机抽取大量的均匀分布的参数点并逐个测试，寻找评价函数值最优的多个参数组合
        与该算法相关的设置选项有：
            sample_size:采样点数量，int 由于采样点的分布是随机的，因此采样点越多，越有可能
                        接近全局最优值

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """

        # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与网格法一致
        par_generator, total = space.extract(search_config.get('sample_count'), how='rand')
        st = time.time()
        pool = self._evaluate_parameters(
                total=total,
                par_value_list=par_generator,
                parallel=self.parallel
        )
        pool.cut(search_config.get('maximize_target'))
        et = time.time()
        print(f'\nOptimization completed, total time consumption: {sec_to_duration(et - st, short_form=True)}')

    def _search_incremental(self,
                            space: Space,
                            search_config: dict) -> None:
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
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """
        sample_count = search_config.get('opti_r_sample_count')
        min_volume = search_config.get('opti_min_volume')
        max_rounds = search_config.get('opti_max_rounds')
        reduce_ratio = search_config.get('opti_reduce_ratio')
        parallel = search_config.get('parallel')

        spaces = list()  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
        base_space = space
        base_volume = base_space.volume
        base_dimension = base_space.dim
        # 每一轮参数寻优后需要保留的参数组的数量
        reduced_sample_count = int(sample_count * reduce_ratio)
        pool = ResultPool(reduced_sample_count)  # 用于存储中间结果或最终结果的参数池对象

        spaces.append(base_space)  # 将整个空间作为第一个子空间对象存储起来
        space_count_in_round = 1  # 本轮运行子空间的数量
        current_round = 1  # 当前运行轮次
        current_volume = base_space.volume  # 当前运行轮次子空间的总体积
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
        epoch = 0
        st = time.time()
        # 从当前space开始搜索，当subspace的体积小于min_volume或循环次数达到max_rounds时停止循环
        while current_volume >= min_volume and current_round < max_rounds:
            epoch += 1
            # 在每一轮循环中，spaces列表存储该轮所有的空间或子空间
            while spaces:
                space = spaces.pop()
                # 逐个弹出子空间列表中的子空间，随机选择参数，生成参数生成器generator
                # 生成的所有参数及评价结果压入pool结果池，每一轮所有空间遍历完成后再排序择优
                par_generator, total = space.extract(sample_count // space_count_in_round, how='rand')
                self._evaluate_parameters(
                        total=total,
                        par_value_list=par_generator,
                        parallel=parallel,
                        epoch_id=epoch
                )
                pool.cut(search_config.get('maximize_target'))
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
        et = time.time()
        print(f'\nOptimization completed, total time consumption: {sec_to_duration(et - st)}')

    def _search_ga(self,
                   space: Space,
                   search_config: dict) -> None:
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
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """

        raise NotImplementedError

    def _search_gradient(self,
                         space: Space,
                         search_config: dict) -> None:
        """ 最优参数搜索算法5：梯度下降法
        在参数空间中寻找优化结果变优最快的方向，始终保持向最优方向前进（采用自适应步长）一直到结果不再改变或达到
        最大步数为止，输出结果为最后N步的结果

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """
        raise NotImplementedError

    def _search_knn(self,
                    space: Space,
                    search_config: dict) -> None:
        """ K-Nearest Neighbors 最近邻算法

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """
        raise NotImplementedError

    def _search_svm(self,
                    space: Space,
                    search_config: dict) -> None:
        """ Support Vector Machine 支持向量机算法

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """
        raise NotImplementedError

    def _search_pso(self,
                    space: Space,
                    search_config: dict) -> None:
        """ Particle Swarm Optimization 粒子群优化算法，与梯度下降相似，从随机解出发，通过迭代寻找最优解

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """
        raise NotImplementedError

    def _search_aco(self,
                    space: Space,
                    search_config: dict) -> None:
        """ Ant Colony Optimization 蚁群优化算法，

        Parameters
        ----------
        space: qt.Space
            参数空间对象
        search_config: dict
            用于存储交易相关参数的配置变量

        Returns
        -------
        None，搜索的结果最佳值会被保存在self.result_pool属性中
        """
        raise NotImplementedError

    def report_result(self):
        """

            :return:
            """
        pass

    def plot_result(self):
        """

        :return:
        """
        raise NotImplementedError

    AVAILABLE_OPTIMIZERS = {
        'grid':        _search_grid,
        'montecarlo':  _search_montecarlo,
        'incremental': _search_incremental,
        'ga':          _search_ga,
        # 'gradient':    _search_gradient,
        # 'knn':         _search_knn,
        # 'svm':         _search_svm,
        'pso':         _search_pso,
        'aco':         _search_aco,
    }