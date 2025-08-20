# coding=utf-8
# ======================================
# File:     qt_operator.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-21
# Desc:
#   Operator Class definition.
# ======================================


import warnings

import numpy as np
import pandas as pd

from typing import Union, Any, Iterable, Mapping

from qteasy.finance import CashPlan
from qteasy.history import HistoryPanel
from qteasy.strategy import BaseStrategy
from qteasy.blender import blender_parser
from qteasy.group import Group
from qteasy.database import DataSource

from qteasy.utilfuncs import (
    AVAILABLE_SIGNAL_TYPES,
    AVAILABLE_OP_TYPES,
    pandas_freq_alias_version_conversion,
    str_to_list,
    ffill_2d_data,
    fill_nan_data,
    rolling_window,
)

from qteasy.built_in import (
    available_built_in_strategies,
    BUILT_IN_STRATEGIES,
    get_built_in_strategy,
)


class Operator:
    """ Operator(交易员)类，用于生成Operator对象，它是qteasy的核心对象。

    Operator是一个容器对象，它包含一系列交易策略，保存每一个交易策略所需的历史数据，并且可以调用所有交易策略，生成交易信号，
    同时根据保存的规则把所有交易策略生成的信号混合起来，形成一组最终的交易信号。就像一个交易员在实际交易中的行为一样。

    创建一个Operator对象时，需要给出一组交易策略，并设定好交易员的交易模式和信号模式，交易模式和信号模式都是Operator对象最重要
    的属性，他们共同决定了交易员的行为模式:

    Properties
    ----------
    strategies:
        一个列表，Operator对象包含的策略对象，可以给出自定义策略对象或内置
        交易策略的id，
        例如：
         - ['macd', 'dma']:
            一个包含两个内置交易策略的列表
         - [ExampleStrategy(), 'macd']
            一个包含两个交易策略，其中第一个是自定义策略的列表
    signal_type:
        交易信号模式，Operator支持三种不同的信号模式，分别如下：
         - PT：positional target，生成的信号代表某种股票的目标仓位
         - PS：proportion signal，比例买卖信号，代表每种股票的买卖百分比
         - VS：volume signal，数量买卖信号，代表每种股票的计划买卖数量
        在不同的信号模式下，交易信号代表不同的含义，交易的执行有所不同，具体含义见下文
    op_type:
        运行类型，Operator对象有两种不同的运行类型：
         - batch/b:         批量信号模式，此模式下交易信号是批量生成的，速度快效率高，但是
                            不支持某些特殊交易策略的模拟回测交易，也不支持实时交易
         - stepwise/step/s: 实时信号模式，此模式下使用最近的历史数据和交易相关数据生成一条
                            交易信号，生成的交易信号考虑当前持仓及最近的交易结果，支持各种
                            特殊交易策略，也可以用于实时交易

    Methods
    -------
    assign_hist_data():
        准备交易数据，为所有的交易策略分配交易数据，生成数据滑窗，以便生成交易信号
    create_signal():
        生成交易信号，在batch模式下，使用所有的数据生成完整交易信号清单，用于交易信号的模拟
        回测交易
        在stepwise模式下，利用数据滑窗和交易相关数据，生成一组交易信号


    """

    def __init__(self,
                 strategies: Union[str, list[Union[str, BaseStrategy, type]]] = None,
                 *,
                 name: str = None,
                 signal_type: str = 'pt',
                 op_type: str = 'batch',
                 group_merge_type: str = 'None'):
        """ 生成一个Operator对象

        parameters
        ----------
        strategies : str, Strategy, list of str or Strategy
            用于生成交易信号的交易策略清单（以交易信号的id或交易信号对象本身表示）
            如果不给出strategies，则会生成一个空的Operator对象
        name : str, optional
            Operator对象的名称
        signal_type : str, {'pt', 'ps', 'vs'}, default 'pt'
            交易信号模式，Operator支持为每个策略组设置三种不同的信号模式之一，分别如下：
                - PT：positional target，生成的信号代表某种股票的目标仓位
                - PS：proportion signal，比例买卖信号，代表每种股票的买卖百分比
                - VS：volume signal，数量买卖信号，代表每种股票的计划买卖数量
            在不同的信号模式下，交易信号代表不同的含义，交易的执行有所不同，具体含义见文档
        op_type : str, {'batch', 'stepwise'}, default 'batch'
            运行类型，Operator对象有两种不同的运行类型：
                - batch/b:         批量信号模式，此模式下交易信号是批量生成的，速度快效率高，但是
                                   不支持某些特殊交易策略的模拟回测交易，也不支持实时交易
                - stepwise/step/s: 实时信号模式，此模式下使用最近的历史数据和交易相关数据生成一条
                                   交易信号，生成的交易信号考虑当前持仓及最近的交易结果，支持各种
                                   特殊交易策略，也可以用于实时交易
        group_merge_type : str, {'None', 'and', 'or'}, default 'None'
            交易策略组的合并方式，决定了当一个Operator对象中包含多个交易策略组时，如何将这些策略组
            生成的交易信号进行合并。可选的合并方式包括：
                - None: 每个策略组独立生成交易信号，同一时刻生成的交易信号会分别独立执行
                - and: 同一时刻不同策略组运行生成的信号会被加总后合并执行
                - or:  同一时刻不同策略组运行生成的信号会被相乘后合并执行

        Examples
        --------
        >>> import qteasy as qt
        >>> op = Operator('dma, macd')
        Operator([dma, macd], 'pt', 'batch')
        >>> op = Operator(['dma', 'macd'])
        Operator([dma, macd], 'pt', 'batch')

        >>> stg_dma = qt.built_in.DMA
        >>> stg_macd = qt.built_in.MACD
        >>> op = Operator([stg_dma, stg_macd])
        Operator([dma, macd], 'pt', 'batch')

        """

        self.name = name
        # 如果对象的种类未在参数中给出，则直接指定最简单的策略种类
        if isinstance(strategies, str):
            stg = str_to_list(strategies)
        elif isinstance(strategies, BaseStrategy):
            stg = [strategies]
        elif isinstance(strategies, list):
            stg = strategies
        else:
            stg = []
        if signal_type is None:
            signal_type = 'pt'
        if op_type is None:
            op_type = 'batch'

        # 初始化Operator对象的"工作数据"或"运行数据"，以下属性由Operator自动设置，不允许用户手动设置：
        # Operator对象的工作变量
        self._op_type = ''
        self._next_stg_index = 0  # int——递增的策略index，确保不会出现重复的index
        self._strategy_id = []  # List——保存所有交易策略的id，便于识别每个交易策略
        self._strategies = {}  # Dict——保存实际的交易策略对象

        # Operator对象包含的交易策略组
        self._groups = []  # 交易策略组，所有同时同频运行的策略会被归为同一组
        self.group_timing_table = None  # 交易策略组的运行时间表
        self.group_merge_type = group_merge_type  # 交易策略组的合并方式，默认为None
        self.group_schedules = {}  # 交易策略组的运行时间表，包含每个组的运行时间和频率

        # Operator对象存储的历史数据缓存和窗口缓存：
        self.data_buffers = {}  # Dict——Operator对象的历史数据缓存，缓存所有策略所需的历史数据
        self.data_window_views = {}  # Dict——Operator对象的历史数据滑窗视图，保存所有策略所需的历史数据滑窗
        self.data_window_indices = {}  # Dict——Operator对象的历史数据滑窗索引，保存所有策略所需的历史数据滑窗索引

        # batch模式下生成的交易清单以及交易清单的相关信息
        self._op_list = None  # 在batch模式下，Operator生成的交易信号清单
        self._op_list_types = None  # Operator交易信号的类型清单，一个list或者ndarray: 表示每一行信号的类型（PT/PS/VS）
        self._op_list_bt_indices = None  # 在batch模式下生成交易信号清单后，需要回测交易的信号行序号，只有序号中的信号行会被回测
        self._op_list_shares = {}  # Operator交易信号清单的股票代码，一个dict: {share: idx}
        self._op_list_hdates = {}  # Operator交易信号清单的日期，一个dict: {hdate: idx}

        # stepwise模式下生成的单次交易信号以及相关信息
        # self._op_signal_index = 0  # 在stepwise模式下，Operator生成的混合后交易信号的日期序号
        # self._op_signal = None  # 在stepwise模式下，Operator生成的交易信号（已经混合好的交易信号）
        # self._op_signals_by_price_type_idx = {}  # 在stepwise模式下，各个strategy最近分别生成的交易信号
        # self._op_signal_indices_by_price_type_idx = {}  # 在stepwise模式下，每个strategy最近交易信号的日期序号
        # self._op_signal_price_type_idx = None  # 在stepwise模式下，Operator交易信号的价格类型序号

        # 设置operator的主要关键属性
        self.op_type = op_type  # 保存operator对象的运行类型，使用property_setter
        self.add_strategies(stg)  # 添加strategy对象，添加的过程中会处理strategy_id和strategies属性

    def __repr__(self):
        res = list()
        res.append('Operator([')
        if self.strategy_count > 0:
            res.append(', '.join(self._strategy_id))
        res.append('], ')
        res.append(f'\'{self.op_type}\')')
        return ''.join(res)

    @property
    def empty(self):
        """检查operator是否包含任何策略"""
        res = (len(self.strategies) == 0)
        return res

    @property
    def strategies(self):
        """以列表的形式返回operator对象的所有Strategy对象"""
        return [self._strategies[stg_id] for stg_id in self._strategy_id]

    @property
    def strategy_count(self):
        """返回operator对象中的所有Strategy对象的数量"""
        return len(self._strategy_id)

    @property
    def strategy_ids(self):
        """返回operator对象中所有交易策略对象的ID"""
        return self._strategy_id

    @property
    def op_type(self):
        """ 返回operator对象的运行类型"""
        return self._op_type

    @op_type.setter
    def op_type(self, op_type):
        """ 设置operator对象的运行类型"""
        if not isinstance(op_type, str):
            raise KeyError(f'op_type should be a string, got {type(op_type)} instead.')
        op_type = op_type.lower()
        if op_type not in AVAILABLE_OP_TYPES:
            raise KeyError(f'Invalid op_type ({op_type})')
        if op_type in ['s', 'st', 'step', 'stepwise']:
            op_type = 'stepwise'
        else:
            op_type = 'batch'
        self._op_type = op_type

    @property
    def op_data_types(self):
        """返回operator对象所有策略子对象所需历史数据类型的集合"""
        d_types = [typ for item in self.strategies for typ in item.data_types]
        d_types = list(set(d_types))
        d_types.sort()
        return d_types

    @property
    def op_data_type_count(self):
        """ 返回operator对象生成交易清单所需的历史数据类型数量
        """
        return len(self.op_data_types)

    @property
    def op_ref_types(self) -> list:
        """返回operator对象所有策略子对象所需历史参考数据类型reference_types的集合"""
        ref_types = [typ for item in self.strategies for typ in item.ref_types]
        ref_types = list(set(ref_types))
        ref_types.sort()
        return ref_types

    @property
    def op_ref_type_count(self) -> int:
        """ 返回operator对象生成交易清单所需的历史数据类型数量"""
        return len(self.op_ref_types)

    @property
    def op_data_freq(self) -> Union[str, list[str]]:
        """返回operator对象所有策略子对象所需数据的采样频率
            如果所有strategy的data_freq相同时，给出这个值，否则给出一个排序的列表
        """
        d_freq = [stg.data_freq for stg in self.strategies]
        d_freq = list(set(d_freq))
        d_freq.sort()
        if len(d_freq) == 0:
            return ''
        if len(d_freq) == 1:
            return d_freq[0]
        warnings.warn(f'there are multiple history data frequency required by strategies',
        RuntimeWarning, stacklevel=2)
        raise ValueError(f'In current version, the data freq of all strategies should be the same, got {d_freq}')
        # return d_freq

    @property
    def strategy_groups(self):
        """返回operator对象所有策略子对象的运行时间类型"""
        return {g.name: g for g in self._groups}

    @property
    def groups(self):
        """返回operator对象所有策略子对象的运行时间类型"""
        return {g.name: g for g in self._groups}

    @property
    def group_ids(self):
        """返回operator对象所有策略子对象的运行时间类型"""
        return [g.name for g in self._groups]

    @property
    def group_names(self):
        """返回operator对象所有策略子对象的运行时间类型"""
        return [g.name for g in self._groups]

    @property
    def all_price_and_data_types(self):
        """ 返回operator对象所有策略自对象的回测价格类型和交易清单历史数据类型的集合"""
        all_types = set(self.op_data_types).union(self.strategy_groups)
        return list(all_types)

    @property
    def op_data_type_list(self):
        """ 返回一个列表，列表中的每个元素代表每一个策略所需的历史数据类型"""
        return [stg.history_data_types for stg in self.strategies]

    @property
    def opt_space_par(self):
        """一次性返回operator对象中所有参加优化（opt_tag != 0）的子策略的参数空间Space信息

        改属性的返回值是一个元组，包含ranges, types两个列表，这两个列表正好可以直接用作Space对象的创建参数，用于创建一个合适的
        Space对象

        一个完整的投资策略由三类多个不同的子策略组成。每个子策略都有自己特定的参数空间，它们的参数空间信息存储在stg.par_boes以及
        stg.par_types等属性中。通常，我们在优化参数的过程中，希望仅对部分策略的参数空间进行搜索，而其他的策略保持参数不变。为了实现
        这样的控制，我们可以给每一个子策略一个属性opt_tag优化标签，通过设置这个标签的值，可以控制这个子策略是否参与优化：
        {0: 'No optimization, 不参与优化，这个子策略在整个优化过程中将始终使用同一组参数',
         1: 'Normal optimization, 普通优化，这个子策略在优化过程中使用不同的参数，这些参数都是从它的参数空间中按照规律取出的',
         2: 'enumerate optimization, 枚举优化，在优化过程中使用不同的参数，但并非取自其参数空间，而是来自一个预设的枚举对象'}

         这个函数遍历operator对象中所有子策略，根据其优化类型选择它的参数空间信息，组合成一个多维向量用于创建可以用于生成所有相关
         策略的参数的高维空间

        Returns
        -------
        ranges, types: list, list
            两个列表，分别包含了所有参与优化的策略的参数空间的范围和类型信息，这两个列表可以直接用作Space对象的创建参数，用于
            创建一个合适的Space对象
        """

        ranges = []
        types = []
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass  # 策略参数不参与优化
            elif stg.opt_tag == 1:
                # 所有的策略参数全部参与优化，且策略的每一个参数作为一个个体参与优化
                ranges.extend(stg.par_range)
                types.extend(stg.par_types)
            elif stg.opt_tag == 2:
                # 所有的策略参数全部参与优化，但策略的所有参数组合作为枚举同时参与优化
                ranges.append(stg.par_range)
                types.extend(['enum'])
        return ranges, types

    @property
    def opt_tags(self):
        """ 返回所有策略的优化类型标签
            该属性返回值是一个列表，按顺序列出所有交易策略的优化类型标签
        """
        return [stg.opt_tag for stg in self.strategies]

    @property
    def max_window_length(self):
        """ 计算并返回operator对象所有子策略中最长的策略形成期。在准备回测或优化历史数据时，以此确保有足够的历史数据供策略形成

        Returns
        -------
        int, operator对象中所有子策略中最长的策略形成期
        """
        if self.strategy_count == 0:
            return 0
        else:
            return max(stg.window_length for stg in self.strategies)

    @property
    def strategy_group_count(self):
        """ 计算operator对象中所有子策略的不同回测价格类型的数量

        Returns
        -------
        int, operator对象中所有子策略的不同回测价格类型的数量
        """
        return len(self.strategy_groups)

    @property
    def op_list(self):
        """ 生成的交易清单，包含了所有交易信号，以及交易信号对应的交易价格

        Returns
        -------
        list, 交易清单，包含了所有交易信号，以及交易信号对应的交易价格
        """
        return self._op_list

    @property
    def op_list_shares(self):
        """ 生成的交易清单的shares序号，股票代码清单

        Returns
        -------
        list, 交易清单的shares序号，股票代码清单
        """
        if self._op_list_shares == {}:
            return
        return list(self._op_list_shares.keys())

    @property
    def op_list_hdates(self):
        """ 生成的交易清单的hdates序号，交易清单的日期序号

        Returns
        -------
        list, 交易清单的hdates序号，交易清单的日期序号
        """
        if self._op_list_hdates == {}:
            return
        return list(self._op_list_hdates.keys())

    @property
    def op_list_price_types(self):
        """ 生成的交易清单的price_types，回测交易价格类型

        Returns
        -------
        list, 生成的交易清单的price_types，回测交易价格类型
        """
        if self._op_list_types == {}:
            return
        return list(self._op_list_types.keys())

    @property
    def op_list_shape(self):
        """ 生成的交易清单的shape。

        Returns
        -------
        tuple, (op_list_shares, op_list_hdates, op_list_price_types)
            生成的交易清单的shape，包含三个维度的数据量
        """
        if self._op_list_shares == {}:
            return
        return (
            len(self._op_list_shares),
            len(self._op_list_hdates),
            len(self._op_list_types)
        )

    @property
    def ready(self):
        """ 检查Operator对象是否已经准备好，可以开始生成交易信号

        返回True，表明Operator的各项属性已经具备以下条件：
            1，Operator 已经有strategy
            2，所有类型的strategy都有blender

        Returns
        -------
        bool, Operator对象是否已经准备好，可以开始生成交易信号
        """
        if self.empty:
            return False
        message = [f'Operator readiness:\n']
        is_ready = True
        if self.strategy_count == 0:
            message.append(f'No strategy -- add strategies to Operator!')
            is_ready = False
        if len(self.strategy_blenders) < self.strategy_group_count:
            message.append(f'No blender -- some of the strategies will not be used for signal, add blender')
            is_ready = False
        else:
            pass

        if len(self.op_data_type_list) < self.strategy_count:
            message.append(f'No history data -- ')
            is_ready = False

        if not is_ready:
            print(''.join(message))

        return is_ready

    def __getitem__(self, item):
        """ 根据策略的名称或序号返回子策略

        Parameters
        ----------
        item: int or str
            策略的名称或序号

        Returns
        -------
        Strategy, 子策略

        Notes
        -----
        1，当item为int时，返回的是第item个策略
        2，当item为str时，返回的是名称为item的策略
        3，当item不符合要求时，返回最后一个策略

        Examples
        --------
        >>> op = Operator('dma, macd')
        >>> op[0]
        RULE-ITER(DMA)
        >>> op['dma']
        RULE-ITER(DMA)
        >>> op[999]
        RULE-ITER(MACD)
        >>> op['invalid_strategy_name']
        UserWarning: No such strategy with ID (invalid_strategy_name)!

        See Also
        --------
        get_stg()
        get_strategy_by_id()
        """

        item_is_int = isinstance(item, int)
        item_is_str = isinstance(item, str)
        if not (item_is_int or item_is_str):
            warnings.warn(f'strategy id should be either an integer or a string, got {type(item)} instead!')
            return
        all_ids = self.strategy_ids
        if item_is_str:
            if item not in all_ids:
                warnings.warn(f'No such strategy with ID ({item}) in {all_ids}!',
                              RuntimeWarning, stacklevel=2)
                return
            return self._strategies[item]
        strategy_count = self.strategy_count
        if item >= strategy_count - 1:
            # 当输入的item明显不符合要求时，仍然返回结果，是否不合理？
            item = strategy_count - 1
        elif item < 0:
            item = 0
        return self._strategies[all_ids[item]]

    def get_stg(self, stg_id):
        """ 获取一个strategy对象, Operator[item]的另一种用法

        Parameters
        ----------
        stg_id: int or str
            策略的名称或序号

        Returns
        -------
        Strategy, 子策略

        Notes
        -----
        1，当stg_id为int时，返回的是第stg_id个策略
        2，当stg_id为str时，返回的是名称为stg_id的策略
        3，当stg_id不符合要求时，返回最后一个策略

        Examples
        --------
        >>> op = Operator('dma, macd')
        >>> op[0]
        RULE-ITER(DMA)
        >>> op['dma']
        RULE-ITER(DMA)
        >>> op[999]
        RULE-ITER(MACD)
        >>> op['invalid_strategy_name']
        UserWarning: No such strategy with ID (invalid_strategy_name)!

        See Also
        --------
        get_strategy_by_id()
        """
        return self[stg_id]

    def get_strategy_by_id(self, stg_id):
        """ 获取一个strategy对象, Operator[item]的另一种用法

        Parameters
        ----------
        stg_id: int or str
            策略的名称或序号

        Returns
        -------
        Strategy, 子策略

        See Also
        --------
        get_stg()
        """
        return self[stg_id]

    def get_strategy_id_pairs(self):
        """ 返回一个generator，包含op中所有strategy和id对：

        Returns
        -------
        generator, 包含op中所有strategy和id对

        Examples
        --------
        >>> op = Operator('dma, macd')
        >>> list(op.get_strategy_id_pairs())
        [('dma', RULE-ITER(DMA)), ('macd', RULE-ITER(MACD))]
        """

        return zip(self._strategy_id, self.strategies)

    def get_group_by_id(self, group_id):
        """ 获取一个Group对象

        Parameters
        ----------
        group_id: int or str
            组的名称或序号

        Returns
        -------
        Group, 子组

        Notes
        -----
        1，当group_id为int时，返回的是第group_id个组
        2，当group_id为str时，返回的是名称为group_id的组
        3，当group_id不符合要求时，返回最后一个组

        Examples
        --------
        >>> op = Operator('dma, macd')
        >>> op.get_group_by_id(0)
        Group(name=Group_1, members=[RULE-ITER(DMA), RULE-ITER(MACD)])
        >>> op.get_group_by_id('Group_1')
        Group(name=Group_1, members=[RULE-ITER(DMA), RULE-ITER(MACD)])
        """
        if isinstance(group_id, int):
            if group_id < 0 or group_id >= len(self.groups):
                group_id = len(self.groups) - 1
            return self.groups[group_id]
        elif isinstance(group_id, str):
            for group in self.groups:
                if group.name == group_id:
                    return group
            warnings.warn(f'No such group with ID ({group_id})!', RuntimeWarning, stacklevel=2)
            return None
        else:
            raise TypeError(f'group_id should be an integer or a string, got {type(group_id)} instead!')

    def add_strategies(self, strategies: Union[str, list[Union[str, BaseStrategy, type]]], **kwargs: Any):
        """ 添加多个Strategy交易策略到Operator对象中

        使用这个方法，不能在添加交易策策略的同时修改交易策略的基本属性
        输入参数strategies可以为一个列表或者一个逗号分隔字符串
        列表中的元素可以为代表内置策略类型的字符串，或者为一个具体的策略对象
        字符串和策略对象可以混合给出

        Parameters
        ----------
        strategies: stg or list of str or list of Strategy
            交易策略的名称或者交易策略对象
        **kwargs: Any
            添加的交易策略所共享的属性，一般如run_timing， run_freq等属性

        Returns
        -------
        None

        Examples
        --------
        >>> op = Operator()
        >>> op.add_strategies(['dma', 'macd'])
        >>> op.strategies
        [RULE-ITER(DMA), RULE-ITER(MACD)]
        """

        if isinstance(strategies, str):
            strategies = str_to_list(strategies)
        assert isinstance(strategies, list), f'TypeError, the strategies ' \
                                             f'should be a list of string, got {type(strategies)} instead'
        for stg in strategies:
            if not isinstance(stg, (str, BaseStrategy, type)):
                warnings.warn(f'WrongType! some of the items in strategies '
                              f'can not be added - got {stg}', RuntimeWarning, stacklevel=2)
            self.add_strategy(stg, **kwargs)

    def add_strategy(self, stg: Union[str, BaseStrategy, type, tuple, list, Any], **kwargs):

        """ 添加一个strategy交易策略到operator对象中

        如果调用本方法添加一个交易策略到Operator中，可以在添加的时候同时修改或指定交易策略的基本属性

        Parameters
        ----------
        stg: str or int or Strategy
            需要添加的交易策略，也可以是内置交易策略的策略id或策略名称
        kwargs:
            任意合法的策略属性，可以在添加策略时直接给该策略属性赋值，
            必须明确指定需要修改的属性名称，包含
            - pars: dict or tuple, 策略可调参数
            - opt_tag: int, 策略优化标签
            - stg_type: int, 策略类型
            - par_count: int, 策略参数个数
            - par_types: list, 策略参数类型
            - par_ranges: list, 策略参数范围
            - data_freq: str, 策略数据频率
            - window_length: int, 策略窗口长度
            - run_freq: str, 策略采样频率
            - data_types: list, 策略数据类型
            - group: str, 策略运行时机
            - use_latest_data_cycle: bool, 策略是否使用最新数据周期

        Returns
        -------
        None

        Examples
        --------
        >>> op = Operator()
        >>> op.add_strategy('dma', opt_tag=1, pars=(50, 10, 20))
        >>> op.strategies
        [RULE-ITER(DMA)]
        >>> op.strategies[0].opt_tag
        1
        >>> op.strategies[0].par_values
        (50, 10, 20)
        """

        # TODO: 添加策略时应可以设置name属性
        # TODO: 添加策略时应可以设置description属性
        # TODO: 添加策略时如果有错误，应该删除刚刚添加的strategy
        # 如果输入为一个字符串时，检查该字符串是否代表一个内置策略的id或名称，使用.lower()转化为全小写字母
        if isinstance(stg, str):
            stg_id = stg.lower()
            strategy = get_built_in_strategy(stg)
        # 当传入的对象是一个strategy对象时，直接添加该策略对象
        elif isinstance(stg, BaseStrategy):
            if stg in available_built_in_strategies:
                stg_id_index = list(available_built_in_strategies).index(stg)
                stg_id = list(BUILT_IN_STRATEGIES)[stg_id_index]
            else:
                stg_id = 'custom'
            strategy = stg
        elif isinstance(stg, type):
            if stg in available_built_in_strategies:
                stg_id_index = list(available_built_in_strategies).index(stg)
                stg_id = list(BUILT_IN_STRATEGIES)[stg_id_index]
            else:
                stg_id = 'custom'
            strategy = stg()
        elif isinstance(stg, (tuple, list)):
            err = TypeError(f'Strategy can not be a tuple of a list, only one strategy can be added! \n'
                            f'To add multiple strategies in the same time, use add_strategies() method instead!')
            raise err
        else:
            err = TypeError(f'The strategy type \'{type(stg)}\' is not supported!')
            raise err

        if stg in self.strategies:
            raise ValueError(f'The strategy {stg} is already in operator, '
                             f'please add a different strategy or its copy.')

        stg_id = self._next_stg_id(stg_id)
        strategy._strategy_id = stg_id
        self._strategy_id.append(stg_id)
        self._strategies[stg_id] = strategy

        # 特殊处理run_freq和run_timings参数，如果这两个参数存在kwargs中，则需要单独修改strategy的这两个参数
        if 'run_freq' in kwargs:
            run_freq = kwargs.pop('run_freq')
            if not isinstance(run_freq, str):
                raise TypeError(f'run_freq should be a string, got {type(run_freq)} instead!')
            strategy.run_freq = run_freq
        if 'run_timing' in kwargs:
            run_timing = kwargs.pop('run_timing')
            if not isinstance(run_timing, str):
                raise TypeError(f'run_timing should be a string, got {type(run_timing)} instead!')
            strategy.run_timing = run_timing

        # 逐一修改该策略对象的各个参数
        self.set_parameter(stg_id=stg_id, **kwargs)

        if len(self._groups) == 0 or not any(
                strategy.run_timing == group.run_timing and strategy.run_freq == group.run_freq
                for group in self._groups
        ):  # create a new group if no existing group matches the strategy's timing and frequency
            group_id = self._next_group_id()
            new_group = Group(name=group_id,
                              signal_type='PT',
                              blender=None, )
            new_group.add_strategy(strategy)
            strategy._group_id = group_id  # TODO: group里保存strategy，同时strategy里又保存group会造成信息冗余，可能出错
            self._groups.append(new_group)
        else:  # add the strategy to an existing group
            for group in self._groups:
                if strategy.run_timing == group.run_timing and strategy.run_freq == group.run_freq:
                    group.add_strategy(strategy)
                    strategy._group_id = group.name
                    break
            return

    def _next_stg_id(self, stg_id: str):
        """ 为一个交易策略生成一个新的id"""
        all_ids = self._strategy_id
        # 补全stg_id中缺失的序号，主要是将“stg_id”变为"stg_id_0"
        all_ids = [ID + '_0' if len(ID.split("_")) == 1 else ID for ID in all_ids]
        all_id_names = [ID.split("_")[0] for ID in all_ids if ID.split("_")[0] == stg_id]
        if stg_id in all_id_names:
            stg_id_stripped = [int(ID.split("_")[1]) for ID in all_ids if ID.split("_")[0] == stg_id]
            next_id = stg_id + "_" + str(max(stg_id_stripped) + 1)
            return next_id
        else:
            return stg_id

    def _next_group_id(self):
        """ 为一个交易策略组生成一个新的id"""
        all_ids = self.group_ids
        group_id_stripped = [int(ID.split("_")[1]) for ID in all_ids]
        next_id = 'Group' + "_" + str(max(group_id_stripped) + 1) if group_id_stripped else 'Group_1'
        return next_id

    def remove_strategy(self, id_or_pos=None):
        """从Operator对象中移除一个交易策略, 删除时可以给出策略的id或者策略在Operator中的位置"""
        pos = -1
        if id_or_pos is None:
            pos = -1
        if isinstance(id_or_pos, int):
            if id_or_pos < self.strategy_count:
                pos = id_or_pos
            else:
                pos = -1
        if isinstance(id_or_pos, str):
            all_ids = self._strategy_id
            if id_or_pos not in all_ids:
                raise ValueError(f'the strategy {id_or_pos} is not in operator')
            else:
                pos = all_ids.index(id_or_pos)
        # 删除strategy的时候，不需要实际删除某个strategy，只需要删除其id即可
        strategy = self[pos]
        self._strategy_id.pop(pos)
        # 接下来还需要删除该strategy所在group中的members
        group = self.groups[strategy._group_id]
        group.members.pop(group.members.index(strategy))
        # 如果该group中没有其他成员了，则删除该group
        if len(group.members) == 0:
            self._groups.remove(group)
        return

    def clear_strategies(self):
        """ 清空Operator对象中的所有交易策略 """
        if self.strategy_count > 0:
            self._strategy_id = []
            self._strategies = {}
        return

    def get_strategies_by_group(self, group_id=None):
        """返回operator对象中的strategy对象, timing为一个可选参数，
        如果给出timing时，返回使用该timing的交易策略

        Parameters
        ----------
        group_id : str, optional
            一个可用的timing, by default None
        """
        if group_id is None:
            return self.strategies
        else:
            return self.groups[group_id].members

    def get_strategy_count_by_group(self, group_id=None):
        """返回operator中的交易策略的数量, timing为一个可选参数，
        如果给出timing时，返回使用该timing的交易策略数量"""
        return len(self.get_strategies_by_group(group_id))

    def get_strategy_names_by_group(self, group_id=None):
        """返回operator对象中所有交易策略对象的名称, timing为一个可选参数，
        注意，strategy name并没有实际的作用，未来将被去掉
        在操作operator对象时，引用某个策略实际使用的是策略的id，而不是name
        如果给出timing时，返回使用该timing的交易策略名称"""
        return [stg.name for stg in self.get_strategies_by_group(group_id)]

    def get_strategy_id_by_group(self, group_id=None):
        """返回operator对象中所有交易策略对象的ID, timing为一个可选参数，
        如果给出timing时，返回使用该timing的交易策略名称"""
        all_ids = self._strategy_id
        if group_id is None:
            return all_ids
        else:
            return [stg.strategy_id for stg in self.groups[group_id].members]

    def get_bt_price_type_id_in_priority(self, priority=None):
        """ 根据字符串priority输出正确的回测交易价格ID

        Parameters
        ----------
        priority: str,
            优先级字符串
            例如，当优先级为"OHLC"时，而price_types为['close', 'open']时
            价格执行顺序为[1, 0], 表示先取第1列，再取第0列进行回测

        Returns
        -------
        sequence: list of int
            返回一个list，包含每一个交易策略在回测时的执行先后顺序
        """
        if priority is None:
            priority = 'OHLCAN'
        price_priority_list = []
        price_type_table = {
            'O': ['open'],
            'H': ['high'],
            'L': ['low'],
            'C': ['close', 'unit_nav', 'accum_nav'],
        }
        price_types = self.strategy_groups
        for p_type in priority.upper():
            price_type_names = price_type_table[p_type]
            if all(price_type_name not in price_types for price_type_name in price_type_names):
                continue
            found_price_type_name = [price_type_name
                                     for
                                     price_type_name in price_type_names
                                     if
                                     price_type_name in price_types][0]
            price_priority_list.append(price_types.index(found_price_type_name))
        return price_priority_list

    def get_bt_price_types_in_priority(self, priority=None):
        """ 根据字符串priority输出正确的回测交易价格

        Parameters
        ----------
        priority: str,
            优先级字符串
            例如，当优先级为"OHLC"时，而price_types为['close', 'open']时
            价格执行顺序为['open', 'close'], 表示先处理open价格，再处理'close'价格

        Returns
        -------
        sequence: list of str
            返回一个list，包含每一个交易策略在回测时的执行先后顺序
        """
        price_types = self.strategy_groups
        price_priority_list = self.get_bt_price_type_id_in_priority(priority=priority)
        return [price_types[i] for i in price_priority_list]

    def get_share_idx(self, share):
        """ 给定一个share（字符串）返回它对应的index

        Parameters
        ----------
        share: str
            share为一个字符串，表示股票代码

        Returns
        -------
        int
            返回一个整数，表示share对应的index
        """
        if self._op_list_shares == {}:
            return
        return self._op_list_shares[share]

    def get_hdate_idx(self, hdate):
        """ 给定一个hdate（字符串）返回它对应的index

        Parameters
        ----------
        hdate: str
            hdate为一个字符串，表示交易日期

        Returns
        -------
        int
            返回一个整数，表示hdate对应的index
        """
        if self._op_list_hdates == {}:
            return
        return self._op_list_hdates[hdate]

    def set_opt_par(self, opt_par):
        """optimizer接口函数，将输入的opt参数切片后传入stg的参数中

        本函数与set_parameter()不同，在优化过程中非常有用，可以同时将参数设置到几个不同的策略中去，只要这个策略的opt_tag不为零
        在一个包含多个Strategy的Operator中，可能同时有几个不同的strategy需要寻优。这时，为了寻找最优解，需要建立一个Space，包含需要寻优的
        几个strategy的所有参数空间。通过这个space生成参数空间后，空间中的每一个向量实际上包含了不同的策略的参数，因此需要将他们原样分配到不
        同的策略中。

        Parameters
        ----------
        opt_par: Tuple
            一组参数，可能包含多个策略的参数，在这里被分配到不同的策略中

        Returns
        -------
        None

        Notes
        -----
        这里使用strategy.update_pars接口，不检查策略参数的合规性，因此需要提前确保参数符合strategy的设定

        Examples
        --------
        一个Operator对象有三个strategy，分别需要2， 3， 3个参数，而其中第一和第三个策略需要参数寻优，这个operator的所有策略参数可以写
        成一个2+3+2维向量，其中下划线的几个是需要寻优的策略的参数：
                 stg1:   stg2:       stg3:
                 tag=1   tag=0       tag=1
                [p0, p1, p2, p3, p4, p5, p6, p7]
                 ==  ==              ==  ==  ==
        为了寻优方便，可以建立一个五维参数空间，用于生成五维参数向量：
                [v0, v1, v2, v3, v4]
        set_opt_par函数遍历Operator对象中的所有strategy函数，检查它的opt_tag值，只要发现opt_tag不为0，则将相应的参数赋值给strategy：
                 stg1:   stg2:       stg3:
                 tag=1   tag=0       tag=1
                [p0, p1, p2, p3, p4, p5, p6, p7]
                 ==  ==              ==  ==  ==
                [v0, v1]            [v2, v3, v4]

        在另一种情况下，一个策略的参数本身就以一个tuple的形式给出，一系列的合法参数组以enum的形式形成一个完整的参数空间，这时，opt_tag被
        设置为2，此时参数空间中每个向量的一个分量就包含了完整的参数信息，例子如下：

        一个Operator对象有三个strategy，分别需要2， 3， 3个参数，而其中第一和第三个策略需要参数寻优，这个operator的所有策略参数可以写
        成一个2+3+2维向量，其中下划线的几个是需要寻优的策略的参数，注意其中stg3的opt_tag被设置为2：
                 stg1:   stg2:       stg3:
                 tag=1   tag=0       tag=2
                [p0, p1, p2, p3, p4, p5, p6, p7]
                 ==  ==              ==  ==  ==
        为了寻优建立一个3维参数空间，用于生成五维参数向量：
                [v0, v1, v2]，其中v2 = (i0, i1, i2)
        set_opt_par函数遍历Operator对象中的所有strategy函数，检查它的opt_tag值，对于opt_tag==2的策略，则分配参数给这个策略
                 stg1:   stg2:       stg3:
                 tag=1   tag=0       tag=2
                [p0, p1, p2, p3, p4, p5, p6, p7]
                 ==  ==              ==  ==  ==
                [v0, v1]         v2=[i0, i1, i2]
        """
        s = 0
        k = 0
        # 依次遍历operator对象中的所有策略：
        for stg in self.strategies:
            # 优化标记为0：该策略的所有参数在优化中不发生变化
            if stg.opt_tag == 0:
                pass
            # 优化标记为1：该策略参与优化，用于优化的参数组的类型为上下界
            elif stg.opt_tag == 1:
                k += stg.par_count
                stg.update_pars(opt_par[s:k])  # 使用update_pars更新参数，不检查参数的正确性
                s = k
            # 优化标记为2：该策略参与优化，用于优化的参数组的类型为枚举
            elif stg.opt_tag == 2:
                # 在这种情况下，只需要取出参数向量中的一个分量，赋值给策略作为参数即可。因为这一个分量就包含了完整的策略参数tuple
                k += 1
                stg.update_pars(opt_par[s])  # 使用update_pars更新参数，不检查参数的正确性
                s = k

    def set_blender(self, blender=None, group=None):
        """ 统一的blender混合器属性设置入口

        Parameters
        ----------
        blender: str or list of str
            一个合法的交易信号混合表达式当price_type为None时，可以接受list为参数，
            同时为所有的price_type设置混合表达式
        group: str,
            一个字符串，用于指定需要混合的交易信号的价格类型，
            如果给出price_type则设置该price_type的策略的混合表达式
            如果price_type为None，则设置所有price_type的策略的混合表达式，此时：
                如果给出的blender为一个字符串，则设置所有的price_type为相同的表达式
                如果给出的blender为一个列表，则按照列表中各个元素的顺序分别设置每一个price_type的混合表达式，
                如果blender中的元素不足，则重复最后一个混合表达式

        Returns
        -------
        None

        Raises
        ------
        TypeError
            如果给出的price_type不是正确的类型

        Warnings
        --------
        如果给出的price_type不存在，则给出warning并返回

        Examples
        --------
        >>> op = Operator('dma, macd')
        >>> op.set_parameter('dma', group='close')
        >>> op.set_parameter('macd', group='open')

        >>> # 设置open的策略混合模式
        >>> op.set_blender('s1+s2', 'open')
        >>> op.get_blender()
        >>> {'open': ['+', 's2', 's1']}

        >>> # 给所有的交易价格策略设置同样的混合表达式
        >>> op.set_blender('s1 + s2')
        >>> op.get_blender()
        >>> {'close': ['+', 's2', 's1'], 'open':  ['+', 's2', 's1']}

        >>> # 通过一个列表给不同的交易价格策略设置不同的混合表达式（交易价格按照字母顺序从小到大排列）
        >>> op.set_blender(['s1 + s2', 's3*s4'], None)
        >>> op.get_blender()
        >>> {'close': ['+', 's2', 's1'], 'open':  ['*', 's4', 's3']}
        """
        if self.strategy_count == 0:
            return
        if group is None:
            # 当price_type没有显式给出时，同时为所有的price_type设置blender，此时区分多种情况：
            if blender is None:
                # price_type和blender都为空，退出
                return
            if isinstance(blender, str):
                # blender为一个普通的字符串，此时将这个blender转化为一个包含该blender的列表，并交由下一步操作
                blender = [blender]
            if isinstance(blender, list):
                # 将列表中的blender补齐数量后，递归调用本函数，分别赋予所有的price_type
                len_diff = self.strategy_group_count - len(blender)
                if len_diff > 0:
                    blender.extend([blender[-1]] * len_diff)
                for bldr, pt in zip(blender, self.strategy_groups):
                    self.set_blender(blender=bldr, group=pt)
            else:
                raise TypeError(f'Wrong type of blender, a string or a list of strings should be given,'
                                f' got {type(blender)} instead')
            return
        if isinstance(group, str):
            # 当直接给出price_type时，仅为这个price_type赋予blender
            if group not in self.strategy_groups:
                msg = f'\n' \
                      f'Given run timing \'{group}\' is not valid in current Operator, \n' \
                      f'no blender will be created! current valid run timings are: \n' \
                      f'{self.strategy_groups}'
                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                return
            if isinstance(blender, str):
                try:
                    parsed_blender = blender_parser(blender)
                    self._stg_blender[group] = parsed_blender
                    self._stg_blender_strings[group] = blender
                except ValueError as e:
                    raise ValueError(f'Invalid blender expression: "{blender}" - {e}')
            else:
                # 如果输入的blender类型不正确，则报错
                raise TypeError(f'Wrong type of blender, a string should be given, got {type(blender)} instead')
                # self._stg_blender_strings[group] = None
                # self._stg_blender[group] = []
        else:
            raise TypeError(f'group should be a string, got {type(group)} instead')
        return

    def get_blender(self, group_name=None):
        """返回operator对象中的多空蒙板混合器, 如果不指定group_name的话，输出完整的blender字典

        Parameters
        ----------
        group_name: str
            一个可用的group_name

        Returns
        -------
        blender: dict or list
            如果group_name为None，则返回一个字典，其中包含所有的run_timing的blender
            如果group_name不为None，则返回一个列表，其中包含该run_timing的blender
        """
        if group_name is None:
            return {g.id: g.blender for g in self._groups if g.blender is not None}
        if group_name not in self.strategy_groups:
            return None
        return self.groups[group_name].blender

    def view_blender(self, group=None):
        """ 返回operator对象中的多空蒙板混合器的可读版本, 即返回blender的原始字符串的更加可读的
             版本，将s0等策略代码替换为策略ID，将blender string的各个token识别出来并添加空格分隔

        Parameters
        ----------
        group: str
            一个可用的run_timing

        """

        from qteasy.blender import human_blender
        if group is None:
            all_blenders = {}
            for group in self.strategy_groups:
                stg_ids = self.get_strategy_id_by_group(group)
                all_blenders[group] = human_blender(
                        group._stg_blender_strings[group],
                        strategy_ids=stg_ids,
                )
            return all_blenders
        if group not in self.strategy_groups:
            return None
        stg_id = self.get_strategy_id_by_group(group)
        return human_blender(
                self._stg_blender_strings[group],
                strategy_ids=stg_id,
        )

    def set_parameter(self,
                      stg_id: Union[str, int],
                      pars: Union[tuple, dict] = None,
                      opt_tag: int = None,
                      window_length: int = None,
                      strategy_data_types: Union[str, list] = None,
                      par_values: Union[tuple, list] = None,
                      **kwargs):
        """ 统一的策略参数设置入口，stg_id标识接受参数的具体成员策略，将函数参数中给定的策略参数赋值给相应的策略

        Parameters
        ----------
        stg_id: str,
            策略的名称（ID），根据ID定位需要修改参数的策略
        pars: tuple or dict, optional
            可调策略参数，格式为tuple
            在创建一个策略的时候，可以设置部分策略参数为"可调参数"，这些参数的取值范围可以在策略优化
            过程中进行调整，通过调整这些参数的组合，可以找到最优的策略参数组合，从而找到最优的策略
        opt_tag: int, optional
            优化类型：
            0: 不参加优化，在策略优化过程中不调整该策略的可调参数
            1: 参加优化，在策略优化过程中根据优化算法主动调整策略参数以寻找最佳参数组合
            2: 以枚举类型参加优化，在策略优化过程中仅从给定的参数组合种选取最优的参数组合
        window_length: int,
            窗口长度：策略计算的前视窗口长度
        strategy_data_types: str or list,
            策略计算所需历史数据的数据类型
        par_values: tuple or list,
            策略参数的具体取值
        kwargs: dict,
            其他参数

        """

        assert isinstance(stg_id, (int, str)), f'stg_id should be a int or a string, got {type(stg_id)} instead'
        # 根据策略的名称或ID获取策略对象
        # TODO; 应该允许同时设置多个策略的参数（对于opt_tag这一类参数非常有用）
        strategy = self.get_strategy_by_id(stg_id)
        if strategy is None:
            raise KeyError(f'Specified strategie does not exist or can not be found!')
        # 逐一修改该策略对象的各个参数
        if pars is not None:  # 设置策略参数
            if not strategy.set_pars(pars):
                raise ValueError(f'parameter setting error')
        if opt_tag is not None:  # 设置策略的优化标记
            strategy.set_opt_tag(opt_tag)
        has_wl = window_length is not None
        has_dt = strategy_data_types is not None
        if has_wl or has_dt:
            strategy.set_hist_pars(window_length=window_length,
                                   strategy_data_types=strategy_data_types)
        if par_values is not None:  # 设置策略参数的具体取值
            strategy.update_par_values(*par_values)
        # 设置可能存在的其他参数
        strategy.set_custom_pars(**kwargs)

    def set_group_parameter(self,
                            group: Union[str, int],
                            run_timing: str = None,
                            run_freq: str = None,
                            signal_type: str = None,
                            blender: Union[str, list] = None,
                            **kwargs):
        """ 设置一个策略组的参数
        Parameters
        ----------
        group: str or int
            策略组的名称或ID
        run_timing: str, optional
            策略组的运行时机，修改运行时机时，修改策略组中所有交易策略的运行时机
        signal_type: str, optional
            策略组的交易信号类型，默认为'PT'，即百分比持仓目标
        blender: str or list, optional
            策略组的交易信号混合表达式，可以是一个字符串或一个字符串列表
        kwargs: dict, optional
            其他参数，可以是任意合法的策略组参数，如group_name, run_timing, run_freq等

        Returns
        -------
        None
        Raises
        ------
        TypeError
            如果group不是字符串或整数类型
        ValueError
            如果group不存在或无法找到
        """
        group = self.get_group_by_id(group)

        has_sf = run_freq is not None
        has_pt = run_timing is not None
        if has_sf or has_pt:
            for strategy in group.strategies:
                strategy.set_hist_pars(run_timing=run_timing,
                                       run_freq=run_freq)
        if signal_type is not None:
            group.set_signal_type(signal_type)
        if blender is not None:
            if isinstance(blender, str):
                blender = [blender]
            elif not isinstance(blender, list):
                raise TypeError(f'blender should be a string or a list of strings, got {type(blender)} instead')
            group.set_blender(blender=blender)

    # =================================================
    # 下面是Operation模块的公有方法：
    def info(self, verbose=False):
        """ 打印出当前交易操作对象的信息，包括选股、择时策略的类型，策略混合方法、风险控制策略类型等等信息

        如果策略包含更多的信息，还会打印出策略的一些具体信息，如选股策略的信息等
        在这里调用了私有属性对象的私有属性，不应该直接调用，应该通过私有属性的公有方法打印相关信息
        首先打印Operation木块本身的信息

        Parameters
        ----------
        verbose: bool, Default False
            是否打印出策略的详细信息, 如果为True, 则会打印出策略的详细信息，包括选股策略的信息等
        """
        from .utilfuncs import adjust_string_length
        from rich import print as rprint
        from shutil import get_terminal_size
        terminal_width = get_terminal_size().columns
        info_width = int(terminal_width * 0.75) if terminal_width > 120 else terminal_width
        signal_type_descriptions = {
            'pt': 'Position Target, signal represents position holdings in percentage of total value',
            'ps': 'Percentage trade signal, represents buy/sell stock in percentage of total value',
            'vs': 'Value trade signal, represent tha amount of stocks to be sold/bought'
        }
        op_type_description = {
            'batch': 'All history operation signals are generated before back testing',
            'stepwise': 'History op signals are generated one by one, every piece of signal will be back tested before '
                        'the next signal being generated.'
        }
        data_freq_name = {
            'y': 'year',
            'ye': 'year end',
            'q': 'quarter',
            'qe': 'quarter end',
            'm': 'month',
            'me': 'month end',
            'w': 'week',
            'd': 'days',
            'min': 'min',
            '1min': 'min',
            '5min': '5min',
            '15min': '15min',
            '30min': '30min',
            'h': 'hours',
        }
        rprint(f'{"Operator Information":-^{info_width}}\n'
               f'Strategies:  {self.strategy_count} Strategies\n'
               f'Run Mode:    {self.op_type} - {op_type_description[self.op_type]}\n'
               f'Signal Type: {self.signal_type} - {signal_type_descriptions[self.signal_type]}\n')
        # 打印blender的信息：
        for run_timing in self.strategy_groups:
            rprint(f'{"Strategy blenders":-^{info_width}}\n'
                  f'for strategy running timing - {run_timing}:')
            if self.strategy_blenders != {}:
                rprint(f'signal blenders: {self.view_blender(run_timing)}\n')
            else:
                rprint(f'no blender\n')
        # 打印各个strategy的基本信息：
        if (self.strategy_count > 0) and (not verbose):
            id_width = int(info_width * .1)
            name_width = int(info_width * .2)
            run_timing_width = int(info_width * .15)
            data_window_width = int(info_width * .10)
            data_type_width = int(info_width * .25)
            par_width = int(info_width * .20)
            rprint(f'{"Strategies":-^{info_width}}\n'
                   f'{"stg_id":<{id_width}}'
                   f'{"name":<{name_width}}'
                   f'{"run timing":<{run_timing_width}}'
                   f'{"data window":<{data_window_width}}'
                   f'{"data types":<{data_type_width}}'
                   f'{"parameters":<{par_width}}\n'
                   f'{"_" * info_width}')
            for stg_id, stg in self.get_strategy_id_pairs():
                from .utilfuncs import parse_freq_string
                qty, main_freq, sub_freq = parse_freq_string(stg.run_freq)
                qty = '' if qty == 1 else qty  # to prevent from printing 1x
                run_type_str = str(qty) + data_freq_name[main_freq.lower()] + ' @ ' + stg.strategy_run_timing
                qty, main_freq, sub_freq = parse_freq_string(stg.data_freq)
                data_type_str = str(stg.window_length * qty) + ' x ' + data_freq_name[main_freq.lower()]
                rprint(f'{adjust_string_length(stg_id, id_width) :<{id_width}}'
                       f'{adjust_string_length(stg.name, name_width) :<{name_width}}'
                       f'{adjust_string_length(run_type_str, run_timing_width) :^{run_timing_width}}'
                       f'{adjust_string_length(data_type_str, data_window_width) :^{data_window_width}}'
                       f'{adjust_string_length(str(stg.history_data_types), data_type_width) :^{data_type_width}}'
                       f'{adjust_string_length(str(stg.par_values), par_width) :^{par_width}}')
            print('=' * info_width)
        # 打印每个strategy的详细信息
        if (self.strategy_count > 0) and verbose:
            print(f'{"Strategy Details":-^{info_width}}')
            for stg_id, stg in self.get_strategy_id_pairs():
                stg.info(stg_id=stg_id, verbose=verbose)
            print('=' * info_width)

    # Adding functions for the new operator class
    def prepare_running_schedule(self, start_date=None, end_date=None):
        """ Running Schedule也就是策略运行时间表，包含每个策略的运行时间和频率等信息

        在运行策略之前，必须先准备好运行时间表，这个时间表根据交易员中每个策略组的运行时机参数确定。
        运行时间表包括N行，每一行代表一个时间点，列数为策略组的数量，每个单元格表示该策略组在该时间
        点是否运行，0表示不运行，1表示运行。

        在这个方法中，将设置以下两个属性的值：
        - `group_schedules`: 一个字典，键为策略组名称，值为该组的运行时间表
        - `group_timing_table`: 一个DataFrame，包含所有策略组的运行时间表

        Parameters
        ----------
        start_date: str or pd.Timestamp, optional
            开始日期，默认为None，表示从数据源的起始日期开始
        end_date: str or pd.Timestamp, optional
            结束日期，默认为None，表示到数据源的结束日期为止

        Returns
        -------
        None
        """
        print('preparing group timing table')
        self.group_schedules = {}
        for group in self._groups:
            if group.run_timing is None or group.run_freq is None:
                raise ValueError(f"Group {group.name} has no run timing or frequency defined.")
            schedule_index = pd.date_range(
                            start=start_date,
                            end=end_date,
                            freq=group.run_freq,
                    ) + pd.Timedelta(hours=0)  # Adjust days to datetime,
            if group.run_freq.upper() == 'D':
                schedule_index = pd.date_range(
                            start=start_date,
                            end=end_date,
                            freq=group.run_freq,
                    ) + pd.Timedelta(hours=16)  # 运行时间设定为16:00
            self.group_schedules[group.name] = pd.DataFrame(
                    data=1,
                    index=schedule_index,
                    columns=['is_running'],
            )
        self.group_timing_table = pd.concat(self.group_schedules.values(), axis=1)
        self.group_timing_table = self.group_timing_table.fillna(0).astype('int')

    def get_signal_count(self, steps=None) -> int:
        """ 获取当前运行时间表中所有策略组生成的交易信号数量

        Parameters
        ----------
        steps: list of int, optional
            如果给出steps，则只计算这些步骤对应的交易信号数量
            如果为None，则计算所有步骤的交易信号数量

        Returns
        -------
        int: 交易信号的数量
        """
        assert not self.group_timing_table.empty, "Group timing table is empty. Please prepare it first."
        if steps is not None:
            running_schedule = self.group_timing_table.iloc[steps]
        else:
            running_schedule = self.group_timing_table

        if self.group_merge_type == 'None':
            return running_schedule.sum().sum()  # same as np.sum(running_schedule.values)
        else:  # 'OR' or 'AND'
            return len(running_schedule)

    def prepare_data_buffer(self, start_date=None, end_date=None, data_source: dict = None):
        print('preparing data buffer')
        for strategie in self.strategies:
            for data_type in strategie.data_types:
                if data_type not in self.data_buffers:
                    self.data_buffers[data_type] = data_source[data_type][start_date:end_date]

    def create_data_windows(self):
        """ Create data windows for each strategy and its data types.
        Also create data window indices for each strategy and its data types.
        data window indices are created according to group schedules.
        """
        print('creating data windows')
        for group in self._groups:
            schedule = self.group_timing_table
            for strategy in group.members:
                self.data_window_views[strategy.name] = {}
                self.data_window_indices[strategy.name] = {}
                for data_type in strategy.data_types:
                    print(f'Creating data window for strategy: {strategy.name}, data type: {data_type}')
                    window_length = strategy.data_window_lengths[data_type]
                    buffered_data = self.data_buffers.get(data_type, None)

                    window = rolling_window(buffered_data.values, window=window_length, axis=0)
                    self.data_window_views[strategy.name][data_type] = window
                    print(f'Window shape for {strategy.name} on {data_type}: \n{window.shape}')

                    total_window_indices = np.arange(len(buffered_data) - window_length + 1) + window_length - 1
                    running_schedule = schedule.index
                    window_schedules = buffered_data.index[total_window_indices]
                    # TODO: 在这里应该注意：np.searchsorted使用了默认参数side=“left”，表示找到的数据窗口时间一定是小于运行时间的
                    #  但是如果strategy设置了“use_latest_cycle”，这就表明数据窗口的时间可以等于运行时间。
                    #  这时应该使用参数side="right"来运行np.searchsorted，使找到的数据窗口时间小于等于运行时间
                    schedule_indices = np.searchsorted(window_schedules, running_schedule) - 1

                    self.data_window_indices[strategy.name][data_type] = schedule_indices
                    print(f'Window indices for {strategy.name} on {data_type}: \n'
                          f'{self.data_window_indices[strategy.name][data_type]}')

    def run_step(self, step_index):
        """ 运行当前步骤的所有策略组，生成交易信号

        本函数是一个生成器函数，返回每个策略组在当前步骤的交易信号。

        Parameters
        ----------
        step_index: int
            当前步骤的索引，表示在运行时间表中的位置

        Returns
        -------
        generator: (signal_type, step_index, signal)
            返回一个生成器，包含每个策略组在当前步骤的交易信号
            signal_type: str, 策略组的信号类型
            step_index: int, 当前步骤的索引
            signal: np.ndarray, 交易信号，一组数字，在不同信号类型模式下表示不同的含义
        """
        if self.group_timing_table is None:
            raise ValueError("Group timing table is not set. Please set it before running steps.")
        group_timing = self.group_timing_table.iloc[step_index].values
        group_count = len(self.groups)
        groups = [self.groups[i] for i in range(group_count) if group_timing[i]]

        signal_type = groups[0].signal_type if groups else None

        signal = 0 if self.group_merge_type == 'OR' else 1
        print(f'In current op run step, following groups are running: {groups}')
        for group in groups:
            # ----set up data window for each strategy
            for strategy in group.members:
                strategy.update_data_window(
                    data_windows=self.data_window_views[strategy.name],
                    window_indices=self.data_window_indices[strategy.name],
                    window_index=step_index,
                )

            # ---- end setting up data windows
            signal_type = group.signal_type

            if self.group_merge_type == 'None':
                signal = group.blend((stg.realize() for stg in group.members))
                yield signal_type, step_index, signal
            elif self.group_merge_type == 'OR':
                signal += group.blend((stg.realize() for stg in group.members))
            elif self.group_merge_type == 'AND':
                signal *= group.blend((stg.realize() for stg in group.members))

        if self.group_merge_type != 'None':
            yield signal_type, step_index, signal

    def is_ready(self, raise_if_not=False):
        """ 全面检查op是否可以开始运行，检查数据是否正确分配，策略属性是否合理，blender是否设置
        策略参数是否完整。
            如果op可以运行，返回True
            如果op不可以运行，检查所有可能存在的问题，提出改进建议，汇总后raise ValueError

        Parameters
        ----------
        raise_if_not: bool, Default False
            如果True，当operator对象未准备好时，raise ValueError
            如果False，当operator对象未准备好时，返回False

        Returns
        -------
        bool
            如果operator对象准备好了，返回True
        """
        ready = True
        err_msg = ''
        if self.strategy_count == 0:
            err_msg += f'operator object should contain at least one strategy, use operator.add_strategy() to add one.'
            ready = False

        if raise_if_not and not ready:
            raise AttributeError(err_msg)

        return ready

    def run(self, steps: Iterable):
        """ 运行Operator，返回运行结果，等同于qteasy.run(self, **kwargs)
        # TODO Operator.run()函数应该被重构为一个私有函数，而不是直接调用qteasy.run(self, **kwargs)，这样可以避免在qteasy中直接调用Operator.run()，而是通过qteasy.run()来运行Operator 相反，qteasy.run()函数应该被重构为一个公有函数，直接调用Operator.run()函数
        See Also
        --------
        qteasy.run
        """
        for step in steps:
            print(f'Running step {step} for operator {self.name}')
            for result in self.run_step(step):
                yield result

    def create_signals(self, start_date=None, end_date=None, data_source: dict = None):
        """ 创建交易信号，准备好数据缓冲区和数据窗口

        Parameters
        ----------
        start_date: str or pd.Timestamp, optional
            开始日期，默认为None，表示从数据源的起始日期开始
        end_date: str or pd.Timestamp, optional
            结束日期，默认为None，表示到数据源的结束日期为止
        data_source: dict, optional
            数据源字典，包含提前准备好的所有需要的数据类型的数据缓存

        Returns
        -------
        None
        """
        self.prepare_running_schedule(start_date=start_date, end_date=end_date)
        self.prepare_data_buffer(start_date=start_date, end_date=end_date, data_source=data_source)
        self.create_data_windows()

        # tentative parameter total_run_steps = 25
        total_run_steps = 25
        # create trade signals between start and end dates
        self.prepare_data_buffer(
                start_date=start_date,
                end_date=end_date,
                data_source=data_source
        )

        self.prepare_running_schedule(start_date=start_date, end_date=end_date)

        self.create_data_windows()

        # for group in self.groups:
        #     print(f'Group {group.name} data windows:')
        #     for strategy in group.members:
        #         print(f'Strategy {strategy.name}/{strategy.run_freq}@{strategy.run_timing} data windows and indices:')
        #         for dtype in strategy.data_types:
        #             window = self.data_window_views[strategy.name][dtype]
        #             indices = self.data_window_indices[strategy.name][dtype]
        #             print(f'{dtype}: {window.shape}, indices: {indices}\n'
        #                   f'window (first 2 windows):\n{window[indices[0:2]]}\n')

        signal_count = self.get_signal_count(range(total_run_steps))

        self._op_list = np.empty(shape=(signal_count, 3))
        self._op_list_types = np.empty(shape=(signal_count,), dtype=int)  # signal type: 0/1/2 for pt/ps/vs
        self._op_list_bt_indices = np.empty(shape=(signal_count,), dtype=int)

        signal_index = 0
        for signal in self.run(range(total_run_steps)):
            self._op_list_types[signal_index] = signal[0]  # the type of the signal
            self._op_list[signal_index] = signal[2]  # the array of the signals
            self._op_list_bt_indices[signal_index] = signal[1]  # the array of the signals
            signal_index += 1


