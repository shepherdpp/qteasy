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

from .finance import CashPlan
from .history import HistoryPanel
from .utilfuncs import str_to_list, ffill_2d_data, fill_nan_data, rolling_window
from .utilfuncs import AVAILABLE_SIGNAL_TYPES, AVAILABLE_OP_TYPES
from .strategy import BaseStrategy
from .built_in import available_built_in_strategies, BUILT_IN_STRATEGIES
from .blender import blender_parser


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

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表

    def __init__(self, strategies=None, signal_type=None, op_type=None):
        """ 生成一个Operator对象

        parameters
        ----------
        strategies : str, Strategy, list of str or list of Strategy
            用于生成交易信号的交易策略清单（以交易信号的id或交易信号对象本身表示）
            如果不给出strategies，则会生成一个空的Operator对象
        signal_type : str, Default: 'pt', {'pt', 'ps', 'vs'}
            需要生成的交易信号的类型，包含以下三种类型:
            'pt', 'ps', 'vs'
            默认交易信号类型为'pt'
        op_type : str, Default: 'batch', {'batch', 'stepwise'}
            Operator对象的的运行模式，包含以下两种：
            'batch', 'stepwise'

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
        '''
        Operator对象的工作数据包含多个字典Dict或其他类型数据，分别存储用于交易信号生成的历史数据
        参考数据、混合方式、以及交易信号的最终结果，这些数据包括三部分：
        
        第一部分：交易策略数据，包括交易策略的ID识别码以及策略对象本身：
        Strategy ID List保存所有交易策略的ID清单，通过ID可以访问与策略相关的数据：
        这部分数据通过add_strategy(), remove_strategy(), remove_strategy()等方法填充或修改
        
            _stg_id:            交易策略ID列表，保存所有相关策略对象的唯一标识id（名称），如:
                                    ['MACD', 
                                     'DMA', 
                                     'MACD-1']
        交易策略对象以字典形式保存：
            _strategies:        以字典形式存储所有交易策略对象本身
                                存储所有的策略对象，如:
                                    {'MACD':    Timing(MACD), 
                                     'DMA':     Timing(timing_DMA), 
                                     'MACD-1':  Timing(MACD)}
        
        第二部分：交易策略运行所需历史数据及其预处理后的数据滑窗、采样清单、混合表达式
        一类历史数据都保存在一系列字典中：通过各个Strategy的ID从字典中访问：
        这部分数据通过assign_hist_data()方法填充或修改

            _op_history_data:   
                                历史数据：
            _op_reference_data: 
                                参考数据：
            _op_hist_data_rolling_window:
                                历史数据的滚动滑窗视图，每个时间点一个滑窗，滑窗的长度等于window_length
            _op_ref_data_rolling_window:
                                参考数据的滚动滑窗视图，每个时间点一个滑窗，滑窗的长度等于window_length
            _op_sample_indices: 
                                策略运行采样点序号

        交易策略的混合表达式和混合操作队列保存在以bt_price_type为键的字典中，通过bt_price_type访问：

            _stg_blender_strings:
                                交易信号混合表达式，该表达式决定了一组多个交易信号应该如何共同影响
                                最终的交易决策，通过该表达式用户可以灵活地控制不同交易信号对最终交易
                                信号的影响，例如只有当多个交易信号同时存在买入时才买入，等等。
                                交易信号表达式以类似于四则运算表达式以及函数式的方式表达，解析后应用
                                到所有交易信号中
                                例如：
                                    {'close':    's0 + s1', 
                                     'open':     's2*(s0+s1)'}

            _stg_blenders:      "信号混合"字典，包含不同价格类型交易信号的混合操作队列，dict的键对应不同的
                                交易价格类型，Value为交易信号混合操作队列，操作队列以逆波兰式
                                存储(RPN, Reversed Polish Notation)
                                例如：
                                    {'close':    ['*', 's1', 's0'], 
                                     'open':     ['*', 's2', '+', 's1', 's0']}
                                     
        第三部分，除上述运行数据外，operator还会保存生成的结果，保存交易清单、清单对应的股票、日期时间以及价格类型
        这些数据会在前两部分数据均准备好后，通过create_signal()方法计算并填充
            
            _op_signal:         
                                生成的交易清单，一个纯ndarray
            _op_signal_shares:  
                                交易清单对应的股票代码
            _op_signal_hdates:  
                                交易清单对应的日期时间
            _op_signal_price_types:
                                交易清单对应的价格类型

        '''
        # Operator对象的工作变量
        self._signal_type = ''
        self._op_type = ''
        self._next_stg_index = 0  # int——递增的策略index，确保不会出现重复的index
        self._strategy_id = []  # List——保存所有交易策略的id，便于识别每个交易策略
        self._strategies = {}  # Dict——保存实际的交易策略对象
        self._op_history_data = {}  # Dict——保存供各个策略进行交易信号生成的历史数据（ndarray，与个股有关）
        self._op_hist_data_rolling_windows = {}  # Dict——保存各个策略的历史数据滚动窗口（ndarray view, 与个股有关）
        self._op_reference_data = {}  # Dic——保存供各个策略进行交易信号生成的参考数据（ndarray，与个股无关）
        self._op_ref_data_rolling_windows = {}  # Dict——保存各个策略的参考数据滚动窗口（ndarray view，与个股无关）
        self._op_sample_indices = {}  # Dict——保存各个策略的运行采样序列值，用于运行采样
        self._stg_blender = {}  # Dict——交易信号混合表达式的解析式
        self._stg_blender_strings = {}  # Dict——交易信号混和表达式的原始字符串形式

        # batch模式下生成的交易清单以及交易清单的相关信息
        self._op_list = None  # 在batch模式下，Operator生成的交易信号清单
        self._op_list_shares = {}  # Operator交易信号清单的股票代码，一个dict: {share: idx}
        self._op_list_hdates = {}  # Operator交易信号清单的日期，一个dict: {hdate: idx}
        self._op_list_price_types = {}  # Operator交易信号清单的价格类型，一个dict: {p_type: idx}
        self._op_list_bt_indices = None  # 在batch模式下生成交易信号清单后，需要回测交易的信号行序号，只有序号中的信号行会被回测

        # stepwise模式下生成的单次交易信号以及相关信息
        self._op_signal_index = 0  # 在stepwise模式下，Operator生成的混合后交易信号的日期序号
        self._op_signal = None  # 在stepwise模式下，Operator生成的交易信号（已经混合好的交易信号）
        self._op_signals_by_price_type_idx = {}  # 在stepwise模式下，各个strategy最近分别生成的交易信号
        # 在stepwise模式下，各个strategy的信号分别存储为以下格式
        # {'open':  [[1,1,1], [1,0,0], [1,1,1]],
        #  'close': [[0,0,0], [1,1,1]]}
        self._op_signal_indices_by_price_type_idx = {}  # 在stepwise模式下，每个strategy最近交易信号的日期序号
        self._op_signal_price_type_idx = None  # 在stepwise模式下，Operator交易信号的价格类型序号

        # 设置operator的主要关键属性
        self.signal_type = signal_type  # 保存operator对象输出的信号类型，使用property_setter
        self.op_type = op_type  # 保存operator对象的运行类型，使用property_setter
        self.add_strategies(stg)  # 添加strategy对象，添加的过程中会处理strategy_id和strategies属性

    def __repr__(self):
        res = list()
        res.append('Operator([')
        if self.strategy_count > 0:
            res.append(', '.join(self._strategy_id))
        res.append('], ')
        res.append(f'\'{self.signal_type}\', \'{self.op_type}\')')
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
    def strategy_blenders(self):
        """返回operator对象中所有交易策略对象的混合表达式"""
        return self._stg_blender

    @strategy_blenders.setter
    def strategy_blenders(self, blenders):
        """ setting blenders of strategy"""
        self.set_blender(blender=blenders, run_timing=None)

    @property
    def signal_type(self):
        """ 返回operator对象的信号类型"""
        return self._signal_type

    @signal_type.setter
    def signal_type(self, st):
        """ 设置signal_type的值"""
        if not isinstance(st, str):
            raise TypeError(f'signal type should be a string, got {type(st)} instead!')
        elif st.lower() in AVAILABLE_SIGNAL_TYPES:
            self._signal_type = AVAILABLE_SIGNAL_TYPES[st.lower()]
        elif st.lower() in AVAILABLE_SIGNAL_TYPES.values():
            self._signal_type = st.lower()
        else:
            raise ValueError(f'Invalid signal type ({st})\nChoose one from '
                             f'{AVAILABLE_SIGNAL_TYPES}')

    @property
    def signal_type_id(self):
        """ 以数字的形式返回operator对象的信号类型，便于loop中识别使用"""
        if self._signal_type == 'pt':
            return 0
        elif self._signal_type == 'ps':
            return 1
        elif self._signal_type == 'vs':
            return 2
        else:
            raise ValueError(f'invalid signal type ({self._signal_type})')

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
        d_types = [typ for item in self.strategies for typ in item.history_data_types]
        d_types = list(set(d_types))
        d_types.sort()
        return d_types

    @property
    def op_data_type_count(self):
        """ 返回operator对象生成交易清单所需的历史数据类型数量
        """
        return len(self.op_data_types)

    @property
    def op_ref_types(self):
        """返回operator对象所有策略子对象所需历史参考数据类型reference_types的集合"""
        ref_types = [typ for item in self.strategies for typ in item.ref_types]
        ref_types = list(set(ref_types))
        ref_types.sort()
        return ref_types

    @property
    def op_ref_type_count(self):
        """ 返回operator对象生成交易清单所需的历史数据类型数量"""
        return len(self.op_ref_types)

    @property
    def op_data_freq(self):
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
        warnings.warn(f'there are multiple history data frequency required by strategies', RuntimeWarning)
        raise ValueError(f'In current version, the data freq of all strategies should be the same, got {d_freq}')
        # return d_freq

    @property
    def strategy_timings(self):
        """返回operator对象所有策略子对象的运行时间类型"""
        p_types = [item.strategy_run_timing for item in self.strategies]
        p_types = list(set(p_types))
        p_types.sort()
        return p_types

    @property
    def all_price_and_data_types(self):
        """ 返回operator对象所有策略自对象的回测价格类型和交易清单历史数据类型的集合"""
        all_types = set(self.op_data_types).union(self.strategy_timings)
        return list(all_types)

    @property
    def op_data_type_list(self):
        """ 返回一个列表，列表中的每个元素代表每一个策略所需的历史数据类型"""
        return [stg.history_data_types for stg in self.strategies]

    @property
    def op_history_data(self):
        """ 返回一个Dict，包含每个策略所需要的history_data，每个ndarray中包含了
        可以用于生成交易信号的历史数据，且这些历史数据的类型与op_data_type_list
        中规定的数据类型相同，历史数据跨度满足信号生成的需求
        """
        return self._op_history_data

    @property
    def op_reference_data(self):
        """ 返回一个Dict，包含每个策略所需要的reference_data，用于生成相应的历史数据

        :return:
        """
        return self._op_reference_data

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
    def bt_price_type_count(self):
        """ 计算operator对象中所有子策略的不同回测价格类型的数量
        to be deprecated

        Returns
        -------
        int, operator对象中所有子策略的不同回测价格类型的数量
        """
        warnings.warn("bt_price_type_count will be deprecated in future versions. "
                      "Use strategy_timing_count instead", DeprecationWarning)
        return len(self.strategy_timings)

    @property
    def strategy_timing_count(self):
        """ 计算operator对象中所有子策略的不同回测价格类型的数量

        Returns
        -------
        int, operator对象中所有子策略的不同回测价格类型的数量
        """
        return len(self.strategy_timings)

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
        if self._op_list_price_types == {}:
            return
        return list(self._op_list_price_types.keys())

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
            len(self._op_list_price_types)
        )

    @property
    def op_signal(self):
        """ stepwise模式下单次生成的交易信号

        Returns
        -------
        np.ndarray, stepwise模式下单次生成的交易信号
        """
        return self._op_signal

    @property
    def op_signal_hdate_idx(self):
        """ stepwise模式下，单次生成的交易信号对应的日期序号

        Returns
        -------
        int, stepwise模式下，单次生成的交易信号对应的日期序号
        """
        return self._op_signal_index

    @property
    def op_signal_hdate(self):
        """ stepwise模式下，单次生成的交易信号对应的日期
        根据op_signal_hdate_idx查找

        Returns
        -------
        datetime, stepwise模式下，单次生成的交易信号对应的日期
        """
        idx = self._op_signal_index
        return self.op_list_hdates[idx]

    @property
    def op_signal_price_type_idx(self):
        """ stepwise模式下，单次生成的交易信号对应的价格类型

        Returns
        -------
        int, stepwise模式下，单次生成的交易信号对应的价格类型的序号
        """
        return self._op_signal_price_type_idx

    @property
    def op_signal_price_type(self):
        """ stepwise模式下，单次生成的交易信号对应的价格类型
        等同于op_signal_price_type_idx

        Returns
        -------
        int, stepwise模式下，单次生成的交易信号对应的价格类型的序号
        """
        return self._op_signal_price_type_idx

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
        if len(self.strategy_blenders) < self.strategy_timing_count:
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
        all_ids = self._strategy_id
        if item_is_str:
            if item not in all_ids:
                warnings.warn(f'No such strategy with ID ({item})!')
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

    def add_strategies(self, strategies):
        """ 添加多个Strategy交易策略到Operator对象中

        使用这个方法，不能在添加交易策策略的同时修改交易策略的基本属性
        输入参数strategies可以为一个列表或者一个逗号分隔字符串
        列表中的元素可以为代表内置策略类型的字符串，或者为一个具体的策略对象
        字符串和策略对象可以混合给出

        Parameters
        ----------
        strategies: stg or list of str or list of Strategy
            交易策略的名称或者交易策略对象

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
            if not isinstance(stg, (str, BaseStrategy)):
                warnings.warn(f'WrongType! some of the items in strategies '
                              f'can not be added - got {stg}', RuntimeWarning)
            self.add_strategy(stg)

    def add_strategy(self, stg, **kwargs):
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
            - strategy_run_freq: str, 策略采样频率
            - strategy_data_types: list, 策略数据类型
            - strategy_run_timing: str, 策略运行时机
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
        >>> op.strategies[0].pars
        (50, 10, 20)
        """

        # TODO: 添加策略时应可以设置name属性
        # TODO: 添加策略时应可以设置description属性
        # TODO: 添加策略时如果有错误，应该删除刚刚添加的strategy
        # 如果输入为一个字符串时，检查该字符串是否代表一个内置策略的id或名称，使用.lower()转化为全小写字母
        if isinstance(stg, str):
            stg = stg.lower()
            if stg not in BUILT_IN_STRATEGIES:
                raise KeyError(f'built-in strategy \'{stg}\' not found! Use "qteasy.built_ins()" to get '
                               f'list of all built-in strategies or detail info')
            stg_id = stg
            strategy = BUILT_IN_STRATEGIES[stg]()
        # 当传入的对象是一个strategy对象时，直接添加该策略对象
        elif isinstance(stg, BaseStrategy):
            if stg in available_built_in_strategies:
                stg_id_index = list(available_built_in_strategies).index(stg)
                stg_id = list(BUILT_IN_STRATEGIES)[stg_id_index]
            else:
                stg_id = 'custom'
            strategy = stg
        else:
            raise TypeError(f'The strategy type \'{type(stg)}\' is not supported!')
        stg_id = self._next_stg_id(stg_id)
        self._strategy_id.append(stg_id)
        self._strategies[stg_id] = strategy
        # 逐一修改该策略对象的各个参数
        self.set_parameter(stg_id=stg_id, **kwargs)

    def _next_stg_id(self, stg_id: str):
        """ 为一个交易策略生成一个新的id"""
        all_ids = self._strategy_id
        if stg_id in all_ids:
            stg_id_stripped = [ID.partition("_")[0] for ID in all_ids if ID.partition("_")[0] == stg_id]
            next_id = stg_id + "_" + str(len(stg_id_stripped))
            return next_id
        else:
            return stg_id

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
        self._strategy_id.pop(pos)
        # self._strategies.pop(pos)
        return

    def clear_strategies(self):
        """ 清空Operator对象中的所有交易策略 """
        if self.strategy_count > 0:
            self._strategy_id = []
            self._strategies = {}
            self._op_history_data = {}

            self._stg_blender = {}
            self._stg_blender_strings = {}
        return

    def get_strategies_by_price_type(self, price_type=None):
        """返回operator对象中的strategy对象, 按price_type筛选

        Parameters
        ----------
        price_type: str, optional
            price_type为一个可选参数，
            如果给出price_type时，返回使用该price_type的交易策略

        Returns
        -------
        List
            返回一个list，包含operator对象中的strategy对象
        """
        warnings.warn('get_strategies_by_price_type is deprecated, '
                      'use get_strategies_by_run_timing instead', DeprecationWarning)
        if price_type is None:
            return self.strategies
        else:
            return [stg for stg in self.strategies if stg.strategy_run_timing == price_type]

    def get_strategies_by_run_timing(self, timing=None):
        """返回operator对象中的strategy对象, timing为一个可选参数，
        如果给出timing时，返回使用该timing的交易策略

        Parameters
        ----------
        timing : str, optional
            一个可用的timing, by default None
        """
        if timing is None:
            return self.strategies
        else:
            return [stg for stg in self.strategies if stg.strategy_run_timing == timing]

    def get_op_history_data_by_price_type(self, price_type=None, get_rolling_window=True):
        """ 返回Operator对象中每个strategy对应的交易信号历史数据，按price_type筛选

        Parameters
        ----------
        price_type: str, optional
            price_type是一个可选参数
            如果给出price_type时，返回使用该price_type的所有策略的历史数据的rolling window
        get_rolling_window: bool, Default: True
            True时返回rolling_window数据，否则直接返回历史数据

        Returns
        -------
        list of ndarray
            返回一个list，包含operator对象运行所需的历史数据
        """
        warnings.warn('get_op_history_data_by_price_type is deprecated, '
                        'use get_op_history_data_by_run_timing instead', DeprecationWarning)
        if get_rolling_window:
            all_hist_data = self._op_hist_data_rolling_windows
        else:
            all_hist_data = self._op_history_data
        if price_type is None:
            return list(all_hist_data.values())
        else:
            relevant_strategy_ids = self.get_strategy_id_by_run_timing(timing=price_type)
            return [all_hist_data[stg_id] for stg_id in relevant_strategy_ids]

    def get_op_history_data_by_run_timing(self, timing=None, get_rolling_window=True):
        """ 返回Operator对象中每个strategy对应的交易信号历史数据，timing是一个可选参数
        如果给出timing时，返回使用该timing的所有策略的历史数据的rolling window

        Parameters
        ----------
        timing : str, optional
            一个可用的timing, by default None
        get_rolling_window : bool, optional
            True时返回rolling_window数据，否则直接返回历史数据, by default True

        Returns
        -------
        List
        """
        if get_rolling_window:
            all_hist_data = self._op_hist_data_rolling_windows
        else:
            all_hist_data = self._op_history_data
        if timing is None:
            return list(all_hist_data.values())
        else:
            relevant_strategy_ids = self.get_strategy_id_by_run_timing(timing=timing)
            return [all_hist_data[stg_id] for stg_id in relevant_strategy_ids]

    def get_op_ref_data_by_price_type(self, price_type=None, get_rolling_window=True):
        """ 返回Operator对象中每个strategy对应的交易信号参考数据，按price_type筛选

        Parameters
        ----------
        price_type: str, optional
            price_type是一个可选参数
            如果给出price_type时，返回使用该price_type的所有策略的历史数据的rolling window
        get_rolling_window: bool, Default: True
            True时返回rolling_window数据，否则直接返回历史数据

        Returns
        -------
        List
            返回一个list，包含operator对象运行所需的历史参考数据
        """
        warnings.warn('get_op_ref_data_by_price_type is deprecated, '
                        'use get_op_ref_data_by_run_timing instead', DeprecationWarning)
        if get_rolling_window:
            all_ref_data = self._op_ref_data_rolling_windows
        else:
            all_ref_data = self._op_reference_data
        if price_type is None:
            return list(all_ref_data.values())
        else:
            relevant_strategy_ids = self.get_strategy_id_by_run_timing(timing=price_type)
            return [all_ref_data[stg_id] for stg_id in relevant_strategy_ids]

    def get_op_ref_data_by_run_timing(self, timing=None, get_rolling_window=True):
        """ 返回Operator对象中每个strategy对应的交易信号参考数据，timing是一个可选参数
        如果给出timing时，返回使用该timing的所有策略的参考数据

        Parameters
        ----------
        timing : str, optional
        一个可用的timing, by default None
        get_rolling_window : bool, optional
        True时返回rolling_window数据，否则直接返回历史数据, by default True

        Returns
        -------
        List
        """
        if get_rolling_window:
            all_ref_data = self._op_ref_data_rolling_windows
        else:
            all_ref_data = self._op_reference_data
        if timing is None:
            return list(all_ref_data.values())
        else:
            relevant_strategy_ids = self.get_strategy_id_by_run_timing(timing=timing)
            return [all_ref_data[stg_id] for stg_id in relevant_strategy_ids]

    def get_op_sample_indices_by_price_type(self, price_type=None):
        """ 返回Operator对象中每个strategy对应的交易信号采样点序列，按price_type筛选

        Parameters
        ----------
        price_type: str, optional
            price_type为一个可选参数，
            如果给出price_type时，返回使用该price_type的交易策略对应的交易采样点序列

        Returns
        -------
        List
            返回一个list，包含operator中的strategy对象所需的交易信号采样点序列
        """
        warnings.warn('get_op_sample_indices_by_price_type is deprecated, '
                        'use get_op_sample_indices_by_run_timing instead', DeprecationWarning)
        all_sample_indices = self._op_sample_indices
        if price_type is None:
            return list(all_sample_indices.values())
        else:
            relevant_strategy_ids = self.get_strategy_id_by_run_timing(timing=price_type)
            return [all_sample_indices[stg_id] for stg_id in relevant_strategy_ids]

    def get_op_sample_indices_by_run_timing(self, timing=None):
        """ 返回Operator对象中每个strategy对应的交易信号采样点序列，timing是一个可选参数
        如果给出timing时，返回使用该timing的所有策略的信号采样点序列

        Parameters
        ----------
        timing : str, optional
        一个可用的timing, by default None

        Returns
        -------
        List
        """
        all_sample_indices = self._op_sample_indices
        if timing is None:
            return list(all_sample_indices.values())
        else:
            relevant_strategy_ids = self.get_strategy_id_by_run_timing(timing=timing)
            return [all_sample_indices[stg_id] for stg_id in relevant_strategy_ids]

    def get_combined_sample_indices(self):
        """ 返回Operator对象所有交易信号采样点序列的并集
        """
        combined_indices = []
        all_sample_indices = self.get_op_sample_indices_by_run_timing()
        for item in all_sample_indices:
            combined_indices = np.union1d(combined_indices, item)
        return combined_indices

    def get_strategy_count_by_price_type(self, price_type=None):
        """返回operator中的交易策略的数量, price_type为一个可选参数，
        如果给出price_type时，返回使用该price_type的交易策略数量"""
        warnings.warn('get_strategy_count_by_price_type is deprecated, '
                        'use get_strategy_count_by_run_timing instead', DeprecationWarning)
        return len(self.get_strategies_by_run_timing(price_type))

    def get_strategy_count_by_run_timing(self, timing=None):
        """返回operator中的交易策略的数量, timing为一个可选参数，
        如果给出timing时，返回使用该timing的交易策略数量"""
        return len(self.get_strategies_by_run_timing(timing))

    def get_strategy_names_by_price_type(self, price_type=None):
        """返回operator对象中所有交易策略对象的名称, price_type为一个可选参数，
        注意，strategy name并没有实际的作用，未来将被去掉
        在操作operator对象时，引用某个策略实际使用的是策略的id，而不是name
        如果给出price_type时，返回使用该price_type的交易策略名称"""
        warnings.warn('get_strategy_names_by_price_type is deprecated, '
                        'use get_strategy_names_by_run_timing instead', DeprecationWarning)
        return [stg.name for stg in self.get_strategies_by_run_timing(price_type)]

    def get_strategy_names_by_run_timing(self, timing=None):
        """返回operator对象中所有交易策略对象的名称, timing为一个可选参数，
        注意，strategy name并没有实际的作用，未来将被去掉
        在操作operator对象时，引用某个策略实际使用的是策略的id，而不是name
        如果给出timing时，返回使用该timing的交易策略名称"""
        return [stg.name for stg in self.get_strategies_by_run_timing(timing)]

    def get_strategy_id_by_price_type(self, price_type=None):  # to be deprecated
        """返回operator对象中所有交易策略对象的ID, price_type为一个可选参数，
        如果给出price_type时，返回使用该price_type的交易策略名称"""
        warnings.warn('get_strategy_id_by_price_type is deprecated, '
                        'use get_strategy_id_by_run_timing instead', DeprecationWarning)
        all_ids = self._strategy_id
        if price_type is None:
            return all_ids
        else:
            res = []
            for stg, stg_id in zip(self.strategies, all_ids):
                if stg.strategy_run_timing == price_type:
                    res.append(stg_id)
            return res

    def get_strategy_id_by_run_timing(self, timing=None):
        """返回operator对象中所有交易策略对象的ID, timing为一个可选参数，
        如果给出timing时，返回使用该timing的交易策略名称"""
        all_ids = self._strategy_id
        if timing is None:
            return all_ids
        else:
            res = []
            for stg, stg_id in zip(self.strategies, all_ids):
                if stg.strategy_run_timing == timing:
                    res.append(stg_id)
            return res

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
        price_types = self.strategy_timings
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
        price_types = self.strategy_timings
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

    def get_price_type_idx(self, price_type):
        """ 给定一个price_type（字符串）返回它对应的index

        Parameters
        ----------
        price_type: str
            price_type为一个字符串，表示价格类型

        Returns
        -------
        int
            返回一个整数，表示price_type对应的index
        """
        if self._op_list_price_types == {}:
            return
        return self._op_list_price_types[price_type]

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

    def set_blender(self, blender=None, run_timing=None):
        """ 统一的blender混合器属性设置入口

        Parameters
        ----------
        blender: str or list of str
            一个合法的交易信号混合表达式当price_type为None时，可以接受list为参数，
            同时为所有的price_type设置混合表达式
        run_timing: str,
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
        >>> op.set_parameter('dma', run_timing='close')
        >>> op.set_parameter('macd', run_timing='open')

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
        if run_timing is None:
            # 当price_type没有显式给出时，同时为所有的price_type设置blender，此时区分多种情况：
            if blender is None:
                # price_type和blender都为空，退出
                return
            if isinstance(blender, str):
                # blender为一个普通的字符串，此时将这个blender转化为一个包含该blender的列表，并交由下一步操作
                blender = [blender]
            if isinstance(blender, list):
                # 将列表中的blender补齐数量后，递归调用本函数，分别赋予所有的price_type
                len_diff = self.strategy_timing_count - len(blender)
                if len_diff > 0:
                    blender.extend([blender[-1]] * len_diff)
                for bldr, pt in zip(blender, self.strategy_timings):
                    self.set_blender(blender=bldr, run_timing=pt)
            else:
                raise TypeError(f'Wrong type of blender, a string or a list of strings should be given,'
                                f' got {type(blender)} instead')
            return
        if isinstance(run_timing, str):
            # 当直接给出price_type时，仅为这个price_type赋予blender
            if run_timing not in self.strategy_timings:
                warnings.warn(
                        f'\n'
                        f'Given run timing \'{run_timing}\' is not valid in current Operator, \n'
                        f'no blender will be created! current valid run timings are as following:\n'
                        f'{self.strategy_timings}')
                return
            if isinstance(blender, str):
                try:
                    parsed_blender = blender_parser(blender)
                    self._stg_blender[run_timing] = parsed_blender
                    self._stg_blender_strings[run_timing] = blender
                except ValueError as e:
                    raise ValueError(f'Invalid blender expression: "{blender}" - {e}')
            else:
                # 如果输入的blender类型不正确，则报错
                raise TypeError(f'Wrong type of blender, a string should be given, got {type(blender)} instead')
                # self._stg_blender_strings[run_timing] = None
                # self._stg_blender[run_timing] = []
        else:
            raise TypeError(f'run_timing should be a string, got {type(run_timing)} instead')
        return

    def get_blender(self, run_timing=None):
        """返回operator对象中的多空蒙板混合器, 如果不指定price_type的话，输出完整的blender字典

        Parameters
        ----------
        run_timing: str
            一个可用的price_type

        Returns
        -------
        blender: dict or list
            如果price_type为None，则返回一个字典，其中包含所有的run_timing的blender
            如果price_type不为None，则返回一个列表，其中包含该run_timing的blender
        """
        if run_timing is None:
            return self._stg_blender
        if run_timing not in self.strategy_timings:
            return None
        if run_timing not in self._stg_blender:
            return None
        return self._stg_blender[run_timing]

    def view_blender(self, run_timing=None):
        """ 返回operator对象中的多空蒙板混合器的可读版本, 即返回blender的原始字符串的更加可读的
             版本，将s0等策略代码替换为策略ID，将blender string的各个token识别出来并添加空格分隔

        Parameters
        ----------
        run_timing: str
            一个可用的run_timing

        """

        from qteasy.blender import human_blender
        if run_timing is None:
            all_blenders = {}
            for run_timing in self.strategy_timings:
                stg_ids = self.get_strategy_id_by_run_timing(run_timing)
                all_blenders[run_timing] = human_blender(
                        self._stg_blender_strings[run_timing],
                        strategy_ids=stg_ids,
                )
            return all_blenders
        if run_timing not in self.strategy_timings:
            return None
        if run_timing not in self._stg_blender:
            return None
        stg_id = self.get_strategy_id_by_run_timing(run_timing)
        return human_blender(
                self._stg_blender_strings[run_timing],
                strategy_ids=stg_id,
        )

    def set_parameter(self,
                      stg_id: [str, int],
                      pars: [tuple, dict] = None,
                      opt_tag: int = None,
                      par_range: [tuple, list] = None,
                      par_types: [list, str] = None,
                      data_freq: str = None,
                      strategy_run_freq: str = None,
                      window_length: int = None,
                      strategy_data_types: [str, list] = None,
                      strategy_run_timing: str = None,
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
        par_range: tuple or list, optional
            可调参数取值范围列表,一个包含若干tuple的列表,代表参数中一个元素的取值范围，如
                [(0, 1), (0, 100), (0, 100)]
        par_types: str or list of str,
            可调参数类型列表，与par_range配合确定策略参数取值范围类型
            int - 整数类型
            float - 浮点数类型
            enum - 枚举类型或给定列表中的元素
        data_freq: str,
            数据频率，策略本身所使用的数据的采样频率
        strategy_run_freq: str,
            运行频率，策略运行时进行信号生成的频率
        strategy_run_timing: str,
            策略的运行时机
        window_length: int,
            窗口长度：策略计算的前视窗口长度
        strategy_data_types: str or list,
            策略计算所需历史数据的数据类型
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
            if strategy.set_pars(pars):
                pass
            else:
                raise ValueError(f'parameter setting error')
        if opt_tag is not None:  # 设置策略的优化标记
            strategy.set_opt_tag(opt_tag)
        if par_range is not None:  # 设置策略的参数优化边界
            strategy.set_par_range(par_range)
        if par_types is not None:  # 设置策略的参数类型
            strategy.par_types = par_types
        has_df = data_freq is not None
        has_sf = strategy_run_freq is not None
        has_wl = window_length is not None
        has_dt = strategy_data_types is not None
        has_pt = strategy_run_timing is not None
        if has_df or has_sf or has_wl or has_dt or has_pt:
            strategy.set_hist_pars(data_freq=data_freq,
                                   strategy_run_freq=strategy_run_freq,
                                   window_length=window_length,
                                   strategy_data_types=strategy_data_types,
                                   strategy_run_timing=strategy_run_timing)
        # 设置可能存在的其他参数
        strategy.set_custom_pars(**kwargs)

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
            'q': 'quarter',
            'm': 'month',
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
        for run_timing in self.strategy_timings:
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
                qty, main_freq, sub_freq = parse_freq_string(stg.strategy_run_freq)
                qty = '' if qty == 1 else qty  # to prevent from printing 1x
                run_type_str = str(qty) + data_freq_name[main_freq.lower()] + ' @ ' + stg.strategy_run_timing
                qty, main_freq, sub_freq = parse_freq_string(stg.data_freq)
                data_type_str = str(stg.window_length * qty) + ' x ' + data_freq_name[main_freq.lower()]
                rprint(f'{adjust_string_length(stg_id, id_width):<{id_width}}'
                       f'{adjust_string_length(stg.name, name_width):<{name_width}}'
                       f'{adjust_string_length(run_type_str, run_timing_width):^{run_timing_width}}'
                       f'{adjust_string_length(data_type_str, data_window_width):^{data_window_width}}'
                       f'{adjust_string_length(str(stg.history_data_types), data_type_width):^{data_type_width}}'
                       f'{adjust_string_length(str(stg.pars), par_width):^{par_width}}')
            print('=' * info_width)
        # 打印每个strategy的详细信息
        if (self.strategy_count > 0) and verbose:
            print(f'{"Strategy Details":-^{info_width}}')
            for stg_id, stg in self.get_strategy_id_pairs():
                stg.info(stg_id=stg_id, verbose=verbose)
            print('=' * info_width)

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

    def run(self, **kwargs):
        """ 运行Operator，返回运行结果，等同于qteasy.run(self, **kwargs)

        See Also
        --------
        qteasy.run
        """
        if self.is_ready(raise_if_not=True):
            import qteasy as qt
            return qt.run(self, **kwargs)

    # TODO: 改造这个函数，仅设置hist_data和ref_data，op的可用性（readiness_check）在另一个函数里检查
    #  op.is_ready（）
    # TODO: 去掉这个函数中与CashPlan相关的流程，将CashPlan的处理移到core.py中，使Operator与CashPlan无关
    def assign_hist_data(
            self,
            hist_data: HistoryPanel,
            cash_plan: CashPlan = None,
            reference_data=None,
            live_mode=False,
            live_running_stgs=None,
    ):
        """ 在create_signal之前准备好相关历史数据，检查历史数据是否符合所有策略的要求：

        检查hist_data历史数据的类型正确；
        检查cash_plan投资计划的类型正确；
        检查hist_data是否为空（要求不为空）；
        在hist_data中找到cash_plan投资计划中投资时间点的具体位置
        检查cash_plan投资计划中的每个投资时间点均有价格数据，也就是说，投资时间点都在交易日内
        检查cash_plan投资计划中第一次投资时间点前有足够的数据量，用于滚动回测
        检查cash_plan投资计划中最后一次投资时间点在历史数据的范围内
        从hist_data中根据各个量化策略的参数选取正确的历史数据切片放入各个策略数据仓库中
        检查op_signal混合器的设置，根据op的属性设置正确的混合器，如果没有设置混合器，则生成一个
            基础混合器（blender）

        然后，根据operator对象中的不同策略所需的数据类型，将hist_data数据仓库中的相应历史数据
        切片后保存到operator的各个策略历史数据属性中，供operator调用生成交易清单。包括：

            self._op_hist_data:
                交易历史数据的滑窗视图，滑动方向沿hdates，滑动间隔为1，长度为window_length
            self._op_ref_data:
                交易参考数据的滑窗视图，滑动方向沿着hdates，滑动间隔为1，长度为window_length
            self._op_sample_idx:
                交易信号采样点序号，默认情况下，Operator按照该序号从滑窗中取出部分，用于计算交易信号
                在live模式下，该序号为[1]或者[0]，[1]表示该策略会被运行，[0]表示该策略不会被运行

        Parameters:
        -----------
        hist_data: HistoryPanel
            历史数据,一个HistoryPanel对象，应该包含operator对象中的所有策略运行所需的历史数据，包含所有
            个股所有类型的数据，

            例如，operator对象中存在两个交易策略，分别需要的数据类型如下：
                策略        所需数据类型
                ------------------------------
                策略A:   close, open, high
                策略B:   close, eps

            hist_data中就应该包含close、open、high、eps四种类型的数据
            数据覆盖的时间段和时间频率也必须符合上述要求
        cash_plan: CashPlan
            一个投资计划，临时性加入，在这里仅检查CashPlan与历史数据区间是否吻合，是否会产生数据量不够的问题
            在live_mode下不需要
        reference_data: HistoryPanel
            参考数据，默认None。一个HistoryPanel对象，这些数据被operator对象中的策略用于生成交易信号，但是与history_data
            不同，参考数据与个股无关，可以被所有个股同时使用，例如大盘指数、宏观经济数据等都可以作为参考数据，某一个个股
            的历史数据也可以被用作参考数据，参考数据可以被所有个股共享。reference_data包含所有策略所需的参考数据。
        live_mode: bool, default False
            是否为实盘模式，如果为True，则不需要根据stg_timing设置op_sample_idx，而是直接根据live_running_stgs提供
            的策略序号来设置op_sample_idx，如果为False，则根据stg_timing设置op_sample_idx
        live_running_stgs: list, optional
            在live模式下，live_running_stgs提供了一个策略序号列表，用于指定哪些策略会被运行，哪些策略不会被运行，
            当live_mode为True时，live_running_stgs必须提供，否则会报错
            live_running_stgs为一个包含若干策略id的列表，列表中的策略的op_sample_idx会被设置为[1]，其他策略的
            op_sample_idx会被设置为[0]

        Returns:
        --------
        None

        Notes
        -----
        1. 该函数仅仅是将历史数据切片后保存到operator的各个策略历史数据属性中，供operator调用生成交易清单。
        2. 该函数不会生成交易清单，也不会执行交易
        3. 该函数不会检查operator的可用性，也不会检查operator的属性是否正确，也不会检查operator的策略是否正确

        Examples
        --------
        关于hist_data的要求：
        例如，operator对象中存在两个交易策略，分别需要的数据类型如下：
            策略        所需数据类型
            ------------------------------
            策略A:   close, open, high
            策略B:   close, eps

        hist_data中就应该包含close、open、high、eps四种类型的数据
        数据覆盖的时间段和时间频率也必须符合上述要求

        关于reference_data的要求：
        例如，operator对象中存在两个交易策略，分别需要的数据类型如下：
            策略        所需数据类型
            ------------------------------
            策略A:   000300.SH (IDX)
            策略B:   601993.SH (IDX)

        reference_data中就应该包含000300.SH(IDX), 601993.SH(IDX)四种类型的数据
        数据覆盖的时间段和时间频率也必须符合上述要求
        """
        from qteasy import logger_core
        logger_core.debug(f'starting prepare operator history data')
        # 确保输入的历史数据是HistoryPanel类型
        if not isinstance(hist_data, HistoryPanel):
            raise TypeError(f'Historical data should be a HistoryPanel, got {type(hist_data)} instead.')
        if not live_mode:
            if cash_plan is None:
                raise ValueError(f'cash plan can not be None unless in live mode')
            # 确保cash_plan的数据类型正确
            if not isinstance(cash_plan, CashPlan):
                raise TypeError(f'cash plan should be CashPlan object, got {type(cash_plan)}')
        # 确保输入的历史数据不为空
        if hist_data.is_empty:
            raise ValueError(f'history data can not be empty!')
        # 如果reference_data不为空
        if reference_data is not None:
            # 确保输入的参考数据类型正确
            # TODO: 为reference data选择最优的数据类型，
            #  是HistoryPanel还是DataFrame？
            if not isinstance(reference_data, HistoryPanel):
                raise TypeError(f'Reference data should be a HistoryPanel, got {type(reference_data)} instead.')
            # 确保输入的参考数据不为空
            if reference_data.is_empty:
                reference_data = None
            # 确保reference_data与hist_data的数据量相同
        # 检查live_mode和live_running_stgs的合法性
        if live_mode:
            if live_running_stgs is None:
                raise ValueError(f'live_running_stgs must be provided when live_mode is True')
            if not isinstance(live_running_stgs, list):
                raise TypeError(f'live_running_stgs must be a list, got {type(live_running_stgs)} instead')
            if len(live_running_stgs) == 0:
                raise ValueError(f'live_running_stgs can not be empty')
            if not all(stg_id in self.strategy_ids for stg_id in live_running_stgs):
                raise TypeError(f'live_running_stgs must contain valid strategy ids, got '
                                f'{[stg_id for stg_id in live_running_stgs if stg_id not in self.strategy_ids]} '
                                f'in the list')
        # TODO 从这里开始下面的操作都应该移动到core.py中，从而把CashPlan从Operator的设置过程中去掉
        #  使Operator与CashPlan无关。使二者脱钩
        # 默认截取部分历史数据，截取的起点是cash_plan的第一个投资日，在历史数据序列中找到正确的对应位置
        # import pdb; pdb.set_trace()
        operator_window_length = self.max_window_length
        op_list_hdates = hist_data.hdates[operator_window_length:]

        if not live_mode:
            first_cash_pos = np.searchsorted(hist_data.hdates, [cash_plan.first_day])
            last_cash_pos = np.searchsorted(hist_data.hdates, [cash_plan.last_day])
            # 确保回测操作的起点前面有足够的数据用于满足回测窗口的要求
            if first_cash_pos < self.max_window_length:
                message = f'History data starts on {hist_data.hdates[0]} does not have' \
                          f' enough data to cover first cash date {cash_plan.first_day}, ' \
                          f'expect {self.max_window_length} cycles, got {first_cash_pos} records only'
                logger_core.error(message)
                raise ValueError(message)
            # 如果第一个投资日不在输入的历史数据范围内，raise
            if first_cash_pos >= len(hist_data.hdates):
                message = f'Investment plan falls out of historical data range,' \
                          f' history data ends on {hist_data.hdates[-1]}, first investment ' \
                          f'on {cash_plan.last_day}'
                logger_core.error(message)
                raise ValueError(message)
            # 如果最后一个投资日不在输入的历史数据范围内，不raise，只记录错误信息
            if last_cash_pos >= len(hist_data.hdates):
                message = f'Not enough history data record to cover complete investment plan,' \
                          f' history data ends on {hist_data.hdates[-1]}, last investment ' \
                          f'on {cash_plan.last_day}'
                logger_core.error(message)
                # raise ValueError(message)
            # 确认cash_plan的所有投资时间点都在价格清单中能找到（代表每个投资时间点都是交易日）
            hist_data_dates = pd.to_datetime(pd.to_datetime(hist_data.hdates).date)
            invest_dates_in_hist = [invest_date in hist_data_dates for invest_date in cash_plan.dates]
            # 如果部分cash_dates没有在投资策略运行日，则将他们抖动到最近的策略运行日
            if not all(invest_dates_in_hist):
                nearest_next = hist_data_dates[np.searchsorted(hist_data_dates, pd.to_datetime(cash_plan.dates))]
                cash_plan.reset_dates(nearest_next)
                logger_core.warning(f'not all dates in cash plan are on trade dates, '
                                    f'they are moved to their nearest next trade dates')
        # TODO 到这里为止上面的操作都应该移动到core.py中
        # 确保输入的history_data有足够的htypes
        hist_data_types = hist_data.htypes
        if any(htyp not in hist_data_types for htyp in self.op_data_types):
            missing_htypes = [htyp for htyp in self.op_data_types if htyp not in hist_data_types]
            message = f'Some historical data types are missing ({missing_htypes}) from the history ' \
                      f'data ({hist_data_types}), make sure history data types covers all strategies'
            logger_core.error(message)
            raise KeyError(message)
        # 确保op的策略都设置了参数
        assert all(stg.has_pars for stg in self.strategies), \
            f'One or more strategies has no parameter set properly!'
        # 确保op的策略都设置了混合方式，在未设置混合器时，混合器是一个空dict
        if self.strategy_blenders == {}:
            logger_core.info(f'User-defined Signal blenders do not exist, default ones will be created!')
            # 如果op对象尚未设置混合方式，则根据op对象的回测历史数据类型生成一组默认的混合器blender：
            # 每一种回测价格类型都需要一组blender，每个blender包含的元素数量与相应的策略数量相同
            for price_type in self.strategy_timings:
                stg_count_for_price_type = self.get_strategy_count_by_run_timing(price_type)
                strategy_indices = ('s' + idx for idx in map(str, range(stg_count_for_price_type)))
                self.set_blender(blender='+'.join(strategy_indices), run_timing=price_type)
        # 为每一个交易策略配置所需的历史数据（3D数组，包含每个个股、每个数据种类的数据）
        self._op_history_data = {
            stg_id: hist_data[stg.history_data_types, :, :]
            for stg_id, stg in self.get_strategy_id_pairs()
        }
        # 如果reference_data存在的时候，为每一个交易策略配置所需的参考数据（2D数据）
        # reference_data输入形式为HistoryPanel的3D数据，需要降低一个维度后传入
        if reference_data:
            self._op_reference_data = {
                stg_id: reference_data[stg.reference_data_types, :, :]
                for stg_id, stg in self.get_strategy_id_pairs()
            }
        else:
            self._op_reference_data = {
                stg_id: None
                for stg_id, stg in self.get_strategy_id_pairs()
            }

        # 为每一个交易策略生成历史数据的滚动窗口（4D/3D数据，包含每个个股、每个数据种类的数据在每一天上的数据滑窗）
        # 清空可能已经存在的数据
        self._op_hist_data_rolling_windows = {}
        self._op_ref_data_rolling_windows = {}
        # 生成数据滑窗
        max_window_length = self.max_window_length
        for stg_id, stg in self.get_strategy_id_pairs():
            window_length = stg.window_length
            # 逐个生成历史数据滚动窗口(4D数据)，赋值给各个策略
            # 一个offset变量用来调整生成滑窗的总数量，确保不管window_length如何变化，滑窗数量相同
            window_length_offset = max_window_length - window_length
            hist_data_val = self._op_history_data[stg_id]
            the_rolling_window = rolling_window(
                    hist_data_val,
                    window=window_length,
                    axis=1
            )
            # 分配数据滑窗：在live模式下，取最后一组或倒数第二组滑窗分配给策略，具体取决于策略的属性
            # use_latest_data_cycle因为live模式下，策略只会运行一次
            # 在backtest模式下，将从倒数第二组滑窗或最后一组滑窗回溯window_length组滑窗并分配给策略
            # 是否包含最后一组滑窗，取决于strategy的属性use_latest_data_cycle的值
            if live_mode and stg.use_latest_data_cycle:  # 分配最后一组滑窗
                self._op_hist_data_rolling_windows[stg_id] = the_rolling_window[-1:]
            elif live_mode:  # 分配倒数第二组滑窗
                self._op_hist_data_rolling_windows[stg_id] = the_rolling_window[-2:-1]
            elif stg.use_latest_data_cycle:  # 从最后一组滑窗开始回溯window_length组滑窗
                self._op_hist_data_rolling_windows[stg_id] = the_rolling_window[window_length_offset + 1:]
            else:  # 从倒数第二组滑窗开始回溯window_length组滑窗
                self._op_hist_data_rolling_windows[stg_id] = the_rolling_window[window_length_offset:-1]

            # 为每一个交易策略分配所需的参考数据滚动窗口（3D数据）
            # 逐个生成参考数据滚动窗口，赋值给各个策略
            ref_data_val = self._op_reference_data[stg_id]
            if ref_data_val is not None:
                ref_data_val = ref_data_val.reshape(ref_data_val.shape[1:])  # 将ref数据变为二维，以符合Strategy的要求
                the_rolling_window = rolling_window(
                        ref_data_val,
                        window=window_length,
                        axis=0
                )
                # 参考数据滑窗的分配方式与历史数据滑窗的分配方式相同
                if live_mode and stg.use_latest_data_cycle:
                    self._op_ref_data_rolling_windows[stg_id] = the_rolling_window[-1:]
                elif live_mode:
                    self._op_ref_data_rolling_windows[stg_id] = the_rolling_window[-2:-1]
                elif stg.use_latest_data_cycle:
                    self._op_ref_data_rolling_windows[stg_id] = the_rolling_window[window_length_offset + 1:]
                else:
                    self._op_ref_data_rolling_windows[stg_id] = the_rolling_window[window_length_offset:-1]
            else:
                self._op_ref_data_rolling_windows[stg_id] = None

            if live_mode:
                # 如果是live_trade，数据采样点永远是0，取第0组滑窗生成信号
                self._op_sample_indices[stg_id] = [0] if stg_id in live_running_stgs else []
            else:
                # 如果不是live_trade，根据策略运行频率strategy_run_freq生成信号生成采样点序列
                freq = stg.strategy_run_freq
                # 根据strategy_run_freq生成一个策略运行采样日期序列
                # TODO: 这里生成的策略运行采样日期时间应该可以由用户自定义，而不是完全由freq生成，
                #  例如，如果freq为'M'的时候，应该允许用户选择采样日期是在每月的第一天，还是最后
                #  一天，抑或是每月的第三天或第N天。或者每周四、每周二等等。
                #  注：
                #  需要生成每月第一天，则freq='MS'，
                #  生成每月最后一天，freq='M'，
                #  生成每月第N天，则pd.date_range(freq='MS') + pd.DateOffset(days=N)
                #  甚至，还应该进一步允许定义时间，
                #  例如：
                #  运行在每日9:00，则此时没有当天数据可用
                #  运行在每日10:00，则每日有开盘价可用，但收盘价不可用
                #  诸如此类
                # TODO: 另外，在live-trade模式下，策略运行采样日期时间序列决定了本次策略是否会
                #  运行，规则是：如果需要某策略运行，则将其采样时间序列设置为[1]，如果不需要某策略运行，
                #  则将其采样时间序列设置为[0]。这时，在运行op.create_signal时，传入参数sample_idx=1
                #  即可。
                temp_date_series = pd.date_range(start=op_list_hdates[0], end=op_list_hdates[-1], freq=freq)
                if len(temp_date_series) <= 1:
                    # 如果strategy_run_freq太大，无法生成有意义的多个取样日期，则生成一个取样点，位于第一日
                    sample_pos = np.zeros(shape=(1,), dtype='int')
                    sample_pos[0] = np.searchsorted(op_list_hdates, op_list_hdates[0])  # 起点第一日
                    self._op_sample_indices[stg_id] = sample_pos
                else:
                    # pd.date_range生成的时间序列是从op_dates未来某一天开始的，因此需要使用pd.Timedelta将它平移到op_dates第一天。
                    target_dates = temp_date_series - (temp_date_series[0] - op_list_hdates[0])
                    # 用searchsorted函数在历史数据日期中查找匹配target_dates的取样点
                    sample_pos = np.searchsorted(op_list_hdates, target_dates)
                    # sample_pos中可能有重复的数字，表明target_dates匹配到同一个交易日，此时需去掉重复值，这里使用一种较快的技巧方法去重
                    sample_pos = sample_pos[np.not_equal(sample_pos, np.roll(sample_pos, 1))]
                    self._op_sample_indices[stg_id] = sample_pos

        # TODO: 检查生成的数据滑窗是否有问题，如果有问题则提出改进建议，
        #  例如：检查是否有部分滑窗存在全NaN数据？

        # 为stepwise运行模式准备相关数据结构，包括每个策略的历史交易信号dict和历史日期序号dict，这部分数据是
        # 按price_type_idx组合的，而不是price_type。这里只创建数据结构，暂时不初始化数值
        self._op_signals_by_price_type_idx = {
            price_type_idx: [] for
            price_type_idx in
            range(self.strategy_timing_count)
        }
        self._op_signal_indices_by_price_type_idx = {
            price_type_idx: [] for
            price_type_idx in
            range(self.strategy_timing_count)
        }

        # 设置策略生成的交易信号清单的各个维度的序号index，包括shares, hdates, price_types，以及对应的index
        share_count, hdate_count, htype_count = hist_data.shape
        self._op_list_shares = {share: idx for share, idx in zip(hist_data.shares, range(share_count))}
        self._op_list_hdates = {hdate: idx for hdate, idx in zip(op_list_hdates, range(len(op_list_hdates)))}
        self._op_list_price_types = {price_type: idx for price_type, idx in zip(self.strategy_timings,
                                                                                range(self.strategy_timing_count))}

        # 初始化历史交易信号和历史日期序号dict，在其中填入全0信号（信号的格式为array[0,0,0]，长度为share_count）
        for price_type_idx in range(self.strategy_timing_count):
            # 按照price_type_idx逐个生成数据并填充
            price_type = self.strategy_timings[price_type_idx]
            stg_count = self.get_strategy_count_by_run_timing(price_type)
            self._op_signals_by_price_type_idx[price_type_idx] = [np.zeros(share_count)] * stg_count
            self._op_signal_indices_by_price_type_idx[price_type_idx] = [0] * stg_count

        return

    def create_signal(self, trade_data=None, sample_idx=None, price_type_idx=None):
        """ 生成交易信号。

        遍历Operator对象中的strategy对象，调用它们的generate方法生成策略交易信号
        如果Operator对象拥有不止一个Strategy对象，则遍历所有策略，分别生成交易信号后，再混合成最终的信号
        如果Operator拥有的Strategy对象交易执行价格类型不同，则需要分别混合，混合的方式可以相同，也可以不同

        用于生成交易信号的历史数据存储在operator对象的几个属性中，在生成交易信号时直接调用。

        根据不同的sample_idx参数的类型，采取不同的工作模式生成交易信号：

        - 如果sample_idx为一个int或np.int时，进入stepwise模式，生成单组信号（单个价格类型上单一时间点混合信号）
            从operator中各个strategy的全部历史数据滑窗中，找出第singal_idx组数据滑窗，仅生成一组用于特定
            回测price_type价格类型的交易信号
            例如，假设 sample_idx = 7, price_type_idx = 0
            则提取出第7组数据滑窗，提取price_type序号为0的交易策略，并使用这些策略生成一组交易信号
                    array[1, 0, 0, 0, 1]
            此时生成的是一个1D数组

            为了确保只在sample采样时间点产生交易信号，需要比较sample_idx与operator的op_sample_indices，
            只有sample_idx在op_sample_indices中时，才会产生交易信号，否则输出None

        - 如果sample_idx为None（默认）或一个ndarray，进入batch模式，生成完整清单
            生成一张完整的交易信号清单，此时，sample_idx必须是一个1D的int型向量，这个向量中的每
            一个元素代表的滑窗会被提取出来生成相应的信号，其余的滑窗忽略，相应的信号设置为np.nan
            例如，假设 sample_idx = np.array([0, 3, 7])T
            生成一张完整的交易信号清单，清单中第0，3，7等三组信号为使用相应的数据滑窗生成，其余的信号
            全部为np.nan：
                    array[[  0,   0,   0,   0,   0],
                          [nan, nan, nan, nan, nan],
                          [nan, nan, nan, nan, nan],
                          [  0,   0,   1,   0,   0],
                          [nan, nan, nan, nan, nan],
                          [nan, nan, nan, nan, nan],
                          [nan, nan, nan, nan, nan],
                          [  1,   0,   0,   0,   1]]
            当sample_idx为None时，使用self._op_sample_idx的值为采样清单
            此时生成的是一个3D数组

        在生成交易信号之前需要调用assign_hist_data准备好相应的历史数据

        输出一个ndarray，包含所有交易价格类型的各个个股的交易信号清单，一个3D矩阵
        levels = shares
        columns = price_types
        rows = hdates

        Parameters
        ----------
        trade_data: np.ndarray
            可选参数，交易过程数据，包括最近一次成交的数据以及最近一次交易信号，如果在回测过程中实时
            产生交易信号，则可以将上述数据传入Operator，从而新一轮交易信号可以与上一次交易结果相关。
            如果给出trade_date信号，trade_date中需要包含所有股票的交易信息，每列表示不同的交易价
            格种类，其结构与生成的交易信号一致
        sample_idx: None, int, np.int, ndarray
            交易信号序号。
            如果参数为int型，则只计算该序号滑窗数据的交易信号
            如果参数为array，则计算完整的交易信号清单
        price_type_idx: None, int
            回测价格类型序号
            如果给出sample_idx，必须给出这个参数
            当给出一个price_type_idx时，不会激活所有的策略生成交易信号，而是只调用相关的策略生成
            一组信号

        Returns
        -------
        signal_value: np.ndarray
        使用对象的策略在历史数据期间的一个子集上产生的所有合法交易信号，该信号可以输出到回测
        模块进行回测和评价分析，也可以输出到实盘操作模块触发交易操作
        当sample_idx不是None时，必须给出一个int，此时price_type_idx也必须给出
        此时输出为一个1D数组
        当sample_idx为None时，会生成一张完整的
        """
        from .blender import signal_blend
        signal_type = self.signal_type
        blended_signal = None
        # 最终输出的所有交易信号都是ndarray，且每种交易价格类型都有且仅有一组信号
        # 一个字典保存所有交易价格类型各自的交易信号ndarray
        # 如果price_type_idx给出时，只计算这个price_type的交易信号
        signal_out = {}
        if price_type_idx is None:
            run_timings = self.strategy_timings
        else:
            run_timings = [self.strategy_timings[price_type_idx]]
        bt_price_type_count = len(run_timings)
        all_zero_signal = np.zeros(len(self._op_list_shares), dtype='float')
        for timing in run_timings:
            # 针对每种交易价格类型分别调用所有的相关策略，准备将rolling_window数据逐个传入策略
            relevant_strategies = self.get_strategies_by_run_timing(timing=timing)
            relevant_hist_data = self.get_op_history_data_by_run_timing(
                    timing=timing,
                    get_rolling_window=True
            )
            relevant_ref_data = self.get_op_ref_data_by_run_timing(
                    timing=timing,
                    get_rolling_window=True
            )
            if sample_idx is None:
                # TODO: 这里的signal_mode实际上就是self.op_type。但是self.op_type并没有
                #  在create_signal过程中起到任何作用，应该考虑op_type和sample_idx的关系，
                #  将sample_idx的使用方法简化:
                #  例如:
                #  - 在生成信号之前检查sample_idx的类型，并加以调整
                #  - 根据op_type确定运行模式
                signal_mode = 'batch'   # TODO: self.op_type == 'batch'
                relevant_sample_indices = self.get_op_sample_indices_by_run_timing(timing=timing)
            else:
                # stepwise运行，此时逐个比较sample_idx与op_sample_indices_by_price_type，只有sample_idx在其中时，才运行
                # 此时strategy必须配套修改：当sample_idx为None时，策略输出也为None，即不运行
                signal_mode = 'stepwise'
                relevant_sample_indices = [sample_idx if sample_idx in _ else None
                                           for _ in
                                           self.get_op_sample_indices_by_run_timing(
                                                   timing=timing
                                           )]
            # 依次使用策略队列中的所有策略逐个生成交易信号
            op_signals = [
                stg.generate(hist_data=hd,
                             ref_data=rd,
                             trade_data=trade_data,
                             data_idx=si) for
                stg, hd, rd, si in
                zip(relevant_strategies,
                    relevant_hist_data,
                    relevant_ref_data,
                    relevant_sample_indices)
            ]
            if (signal_mode == 'stepwise') and (signal_type in ['ps', 'vs']):
                # stepwise mode, 这时候如果idx不在sample_idx中，就使用全0信号
                op_signals = [
                    all_zero_signal if news is None else news for
                    news in op_signals
                ]
                self._op_signals_by_price_type_idx[price_type_idx] = op_signals
                self._op_signal_indices_by_price_type_idx[price_type_idx] = [
                    old_idx if new_idx is None else old_idx for
                    old_idx, new_idx in zip(self._op_signal_indices_by_price_type_idx[price_type_idx],
                                            [sample_idx] * len(relevant_strategies))
                ]
            elif (signal_mode == 'stepwise') and (signal_type == 'pt'):
                # stepwise mode, 这时候如果idx不在sample_idx中，就沿用上次的交易信号（不生成信号）
                op_signals = [
                    olds if news is None else news for
                    olds, news in zip(self._op_signals_by_price_type_idx[price_type_idx],
                                      op_signals)
                ]
                self._op_signals_by_price_type_idx[price_type_idx] = op_signals
                self._op_signal_indices_by_price_type_idx[price_type_idx] = [
                    old_idx if new_idx is None else old_idx for
                    old_idx, new_idx in zip(self._op_signal_indices_by_price_type_idx[price_type_idx],
                                            [sample_idx] * len(relevant_strategies))
                ]
            elif (signal_mode == 'batch') and (signal_type in ['ps', 'vs']):
                # batch mode 且ps/vs信号: 填充signal_list中的空缺值为0
                op_signals = list(map(fill_nan_data, op_signals, [0] * len(relevant_strategies)))
            elif (signal_mode == 'batch') and (signal_type == 'pt'):
                # batch mode 且pt信号: ffill填充signal_list中的空缺值
                op_signals = list(map(ffill_2d_data, op_signals, [0] * len(relevant_strategies)))

            # 生成的交易信号添加到交易信号队列中，

            # 根据蒙板混合前缀表达式混合所有蒙板
            # 针对不同的price-type，应该生成不同的signal，因此不同price-type的signal需要分别混合
            # 最终输出的signal是多个ndarray对象，存储在一个字典中
            signal_blender = self.get_blender(timing)
            blended_signal = signal_blend(op_signals, blender=signal_blender).astype('float')
            # debug
            # print(f'[DEBUG] in function create_signal(), \n'
            #       f'got op_signals: \n{op_signals}\n'
            #       f'got signal_blender: \n{signal_blender}\n'
            #       f'got blended_signal: \n{blended_signal}\n')
            if signal_mode == 'stepwise':
                # stepwise mode, 返回混合好的signal，并给operator的信号缓存赋值
                self._op_signal = blended_signal
                self._op_signal_index = sample_idx
                self._op_signal_price_type_idx = timing
                return blended_signal
            signal_out[timing] = blended_signal
        # 将混合后的交易信号赋值给一个3D数组，每一列表示一种交易价格的信号，每一层一个个股
        signal_shape = blended_signal.T.shape
        signal_value = np.empty((*signal_shape, bt_price_type_count), dtype='float')
        for i, timing in zip(range(bt_price_type_count), run_timings):
            signal_value[:, :, i] = signal_out[timing].T
        self._op_list = signal_value
        return signal_value

