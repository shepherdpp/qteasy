# coding=utf-8
# ======================================
# File:     strategy.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-09-27
# Desc:
#   Strategy Base Classes and its derived
#   Classes.
# ======================================

import numpy as np
import pandas as pd
from abc import abstractmethod, ABCMeta
from typing import Union, List, Tuple, Dict, Any, Callable, Literal, Iterable
import warnings

from qteasy.utilfuncs import (
    TIME_FREQ_STRINGS,
    input_to_list,
)
from qteasy.datatypes import DataType
from qteasy.parameter import Parameter


def _dict_par_format_is_valid(par_name: str, pars, value_type, key_type):
    """检查字典的键和值的类型"""
    assert isinstance(pars, dict), f'parameter "{par_name}" is invalid, please check your input'
    assert all(isinstance(dtype, value_type) for dtype in pars.values()), \
        f'parameter "{par_name}" should be a dict of {value_type} objects, got {pars} instead'
    assert all(isinstance(dtype.__getattribute__(key_type), str) for dtype in pars.values()), \
        f'parameter "{par_name}" should be a dict of {value_type} objects with {key_type} as key, ' \
        f'got {pars} instead'
    assert all(key == dtype.__getattribute__(key_type) for key, dtype in pars.items()), \
        f'parameter "{par_name}" should be a dict of {value_type} objects with {key_type} as key, ' \
        f'got {pars} instead'

    return True


class BaseStrategy:
    """ 量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的策略类调用

    定义一个交易策略，需要包含四大要素：

    1，交易策略的运行时机和运行频率，决定了策略在实盘运行时的运行时间点，交易员对象将在这些时间点调用策略
        的realize()方法生成交易信号。
        交易时机和运行频率是通过run_timing和run_freq两个参数来确定的，这两个参数通常在策略初始化时指定

    2，策略的可调参数，这些参数可以在策略运行前进行调整，影响策略的性能表现
        策略的可调参数通过Parameter对象来定义，每个Parameter对象包含参数的名称、类型、取值范围和默认值
        定义好Parameter对象后，可调参数可以通过策略对象的pars属性设置，而参数的值可以通过par_values参
        数在策略初始化后进行设置

    3，生成交易信号所需的历史数据，历史数据通过指定数据类型名称、数据的频率和时间窗口长度来确定。
        一个交易策略可以使用多种不同的历史数据类型，各种数据类型的频率和窗口长度可以不同

    4，策略的运行逻辑，即如何根据历史数据生成交易信号，这个逻辑通过重写策略的realize()方法来实现
        在realize()方法中，可以使用get_pars()和get_data()方法来获取策略的参数和历史数据来计算交易信号

    如果要创建一个自定义交易策略对象，使用下面的方法：
    ```python
    class MyStrategy(BaseStrategy):

        def __init__(self, par_values=(<parameter values>), **kwargs):
            super().__init__(
                name='<strategy name>',
                description='<strategy description>',
                stg_type='BASE',
                run_freq='<strategy run frequency>',  # 定义策略运行频率
                run_timing='<strategy run timing>',  # 定义策略运行时机
                pars=[<list of Parameter objects>],  # 定义策略的可调参数类型和取值范围
                data_types=[<list of DataType objects>],  # 定义策略使用的数据类型，关于更多细节见qteasy文档
                **kwargs,
            )
            if par_values:
                self.update_par_values(par_values)

        def realize(self):
            '''实现策略的交易逻辑，生成交易信号'''
            # 获取策略参数
            param1, param2 = self.get_pars('param1', 'param2')
            # 获取历史数据
            price_data = self.get_data('price')
            # 计算交易信号
            signals = ...  # 根据参数和数据计算交易信号
            return signals

    需要注意，交易策略的输出交易信号并不是真正的交易指令，而是一个实数类型的交易信号，在后续的交易执行环节中，
    这个信号将被解析为具体的交易指令。交易信号的类型由交易员对象的signal_type属性决定，交易信号的类型有三种，
    分别是：

        - 'VS'：数量买卖信号，最简单直接的信号类型。这个实数代表的是买入或卖出相应数量的股票：
            例如10表示买入10股股票，-5表示卖出5股股票
        - 'PT'：仓位比例信号，这个实数代表的是目标持仓比例，通过买入或卖出股票使当前持仓比例达到目标持仓比例，
            例如0.5表示持有50%的多头仓位，如果目前持有20%的多头，则需要买入30%的股票，
            如果目前持有70%的多头，则需要卖出20%的股票
        - 'PS'：比例买卖信号，这个实数代表的是买入或卖出相应比例的股票：
            例如0.5表示使用当前总投资额的50%买入股票，如果当前总投资额为10000元，则买入5000元的股票

    不同交易信号在三种信号类型下的含义示例见下表：

            signal\type |         PT           |            PS           |       VS
            ------------------------------------------------------------------------------------
                1.5     | 持有多头仓位比例150%*   |  买入总投资额150%的股票    | 多头买入1.5股或1.5份
                0.5     |   持有多头仓位比例50%   |  买入总投资额50%的股票     | 多头买入0.5股或0.5份
                0.0     |    调整持仓比例至0      |     不进行任何操作        |     不进行任何操作
               -0.5     |  持有空头仓位比例至50%   |     卖出当前持仓的50%     | 卖出当前持仓0.5股或0.5份
               -1.5     | 持有空头仓位比例至150%*  | 卖出当前全部持仓并持50%空仓 | 卖出1.5股或1.5份或空头买入

    Properties
    ----------
    name: str
        策略名称，用户自定义，用于区分不同的策略一个
    description: str
        策略描述，用户自定义，用于描述策略的基本原理
    strategy_id: str
        策略的唯一ID，在策略运行时由系统分配
    group_id: str
        策略所在的策略组ID，策略组是一个策略的集合，策略组可以包含多个策略，该ID由系统分配
    par_values: tuple
        策略参数，元组，每个策略都包含若干个可调参数，这些参数可以在策略运行前进行调整，影响策略的性能表现
    signal_type: str
        策略生成的交易信号类型，不同的信号类型将被解析为不同的交易指令
        - 'pt'表示仓位比例，
        - 'ps'表示买卖信号，
        - 'vs'表示持仓变化量

    Methods
    -------
    get_pars(*par_names)
        获取策略参数的值，可以获取多个参数
    get_data(*data_type_ids)
        获取历史数据，可以获取多个数据类型的数据
    realize()
        生成策略信号，抽象方法，在几种不同的子类中实现

    """
    __metaclass__ = ABCMeta

    AVAILABLE_STG_RUN_TIMING = ['open', 'close', 'unit_nav', 'accum_nav']

    def __init__(
            self,
            *,
            name: str = '',
            description: str = '',
            stg_type: str = 'BASE',
            run_freq: str = 'd',
            run_timing: str = 'close',
            pars: Union[Parameter, List[Parameter], Dict[str, Parameter]] = None,
            data_types: Union[DataType, List[DataType], Dict[str, DataType]] = None,
            use_latest_data_cycle: Union[bool, List[bool], Dict[str, bool]] = False,
            window_length: Union[int, List[int], Dict[str, int]] = 30,
            opt_tag: int = 0,
            par_values: Union[Tuple[Any], List[Any]] = None,
    ):
        """ 初始化策略

        Parameters
        ----------
        name: str
            策略名称，用户自定义策略的名称，用于区分不同的策略
        description: str
            策略描述，用户自定义策略的描述，用于区分不同的策略
        stg_type: str
            策略类型，用户自定义，用于区分不同的策略，例如均线策略、趋势跟随策略等
        run_freq: str {'d', 'w', 'm', 'q', ’qe‘， 'y', 'ye'}, default: 'd'
            策略的运行频率，可以是分钟、日频、周频、月频、季频或年频，分别表示每分钟运行一次、每日运行一次等等
            如果运行频率低于日频，可以通过'w_Fri' / 'm_15'(每月15日) / 'm_-2'(每月倒数第二天)等方式指定具体
            哪一天运行
        run_timing: datetime-like or str, default: 'close
            策略运行的时间点，策略运行频率低于天时，这个参数是一个时间，表示策略每日的运行时间
            例如'09:30:00'表示每天的09:30:00运行策略，可以设定为'open'或'close'，表示每天开盘或收盘运行策略
            如果运行频率高于天频，则这个参数无效，策略运行时间为交易日正常交易时段中频次分割点。
            例如，如果运行频率为'h', 假设股市9：30开市，15：30收市
            则策略运行时间为
            ['09:30:00', '10:30:00',
             '11:30:00', '13:00:00',
             '14:00:00', '15:00:00',]
        pars: Parameter, list of Parameter, dict {str: Parameter}, default None
            策略可调参数，Parameter对象，确定策略的可调参数，参数类型以及取值范围
        data_types: DataType, list of DataTypes, dict{str: DataType}
            策略使用的数据类型，每个数据类型一个类型名
        use_latest_data_cycle: bool, list of bool, dict{str: bool}, default True
            是否使用最新的数据周期生成交易信号，默认True
            如果为True: 默认值
                在实盘运行时，会尝试下载当前周期的最新数据，或尝试使用最近的实时数据估算当前周期的数据，此时应该注意避免出现未来函数，
                    如运行时间点为开盘时，这时就不能使用收盘价/最高价/最低价生成交易信号，会导致策略运行失真。
                在回测交易时，会使用回测当前时间点的最新数据生成交易信号。此时应该注意避免出现未来函数，如回测时间点为
                    开盘时，但是使用当前周期的收盘价生成交易信号，会导致策略运行失真。
            如果为False：
                在回测或实盘运行时都仅使用当前已经获得的上一周期的已知数据生成交易信号，在运行频率较低时，可能会导致
                    交易信号的滞后，但是可以避免未来函数的出现。
        window_length: int, list of int, dict{str: int}, default 30
            策略使用的数据窗口长度，即策略使用的历史数据的长度
        opt_tag: int {0, 1}
            策略的优化标签，0表示不参与优化，1表示参与优化

        Returns
        -------
        None
        """

        # 检查策略参数是否合法：
        from qteasy import logger_core
        logger_core.info(f'initializing new Strategy: type: {stg_type}, name: {name}, text: {description}')

        self._stg_name = str(name)
        self._stg_description = str(description)
        self._run_freq = run_freq
        self._run_timing = run_timing

        self._pars = None
        self.set_pars(pars)  # 设置策略参数，使用set_pars()函数同时检查参数的合法性
        self._opt_tag = None
        self.set_opt_tag(opt_tag)  # 策略的优化标记，
        self._stg_type = stg_type  # 策略类型
        if par_values:
            self.update_par_values(par_values)

        logger_core.info(f'Strategy created with basic parameters set, pars={pars}, par_count={self.par_count},'
                         f' par_types={self.par_types}, par_range={self.par_range}')

        self._data_types = None
        self._data_ids = None
        self._data_ULC = None
        self._data_WL = None
        self.set_data_types(data_types, use_latest_data_cycle, window_length)
        logger_core.info(f'Strategy data types set:\n'
                         f'data_types={self.data_types}, data_ids={self._data_ids}, ')

        # 以下是策略运行时产生的动态参数
        self._share_count = 0
        self._share_names = None
        self._strategy_id = None  # 策略的唯一ID，在策略运行时由系统分配
        self._group_id = None  # 策略所在的策略组ID，策略组是一个策略的集合，策略组可以包含多个策略

    @property
    def name(self):
        """策略名称，打印策略信息的时候策略名称会被打印出来"""
        return self._stg_name

    @name.setter
    def name(self, name: str):
        self._stg_name = name

    @property
    def strategy_id(self):
        return self._strategy_id

    @property
    def group_id(self):
        return self._group_id

    @property
    def description(self):
        """策略说明文本，对策略的实现方法和功能进行简要介绍"""
        return self._stg_description

    @description.setter
    def description(self, description: str):
        self._stg_description = str(description)

    @property
    def stg_type(self):
        """策略类型，表明策略的基类，即：
            - GeneralStg: GENERAL
            - FactorSorter: FACTOR
            - RuleIterator: RULE-ITER
        """
        return self._stg_type

    @property
    def has_pars(self) -> bool:
        """返回True如果策略有可调参数，否则返回False"""
        return self.pars != {}

    @property
    def pars(self):
        """策略参数，是一个列表，列表中的每个元素都是一个参数值"""
        return self._pars

    @pars.setter
    def pars(self, new_pars):
        """设置策略参数，参数的合法性检查在这里进行"""
        self.set_pars(new_pars)

    @property
    def par_count(self):
        """策略的参数数量"""
        return len(self.par_values)

    @property
    def par_values(self) -> tuple:
        """策略参数，元组
        Return
        -------
        tuple: 策略参数的值，元组中的每个元素都是一个参数值，如果没有设置参数，则返回None
        """
        return tuple(par.value for par in self._pars.values()) if self._pars is not None else None

    @par_values.setter
    def par_values(self, pars: tuple):
        """设置策略参数，参数的合法性检查在这里进行"""
        self.update_par_values(*pars)

    @property
    def par_names(self):
        """策略的参数名称列表"""
        return [par.name for par in self.pars.values()] if self.par_values is not None else []

    @property
    def par_types(self):
        """策略的参数类型，由策略参数类的par_type属性给出"""
        return {name: par.par_type for name, par in self.pars.items()}

    @property
    def par_range(self):
        """策略的参数取值范围，用来定义参数空间用于参数优化"""
        return {name: par.par_range for name, par in self.pars.items()}

    @property
    def opt_tag(self):
        """策略的优化类型"""
        return self._opt_tag

    @opt_tag.setter
    def opt_tag(self, opt_tag):
        self.set_opt_tag(opt_tag=opt_tag)

    @property
    def run_freq(self):
        """策略生成的采样频率"""
        return self._run_freq

    @run_freq.setter
    def run_freq(self, run_freq):
        # check if run_freq is valid
        if not isinstance(run_freq, str):
            raise TypeError(f'sample_freq should be a string, got {type(run_freq)} instead')
        if run_freq not in TIME_FREQ_STRINGS:
            raise ValueError(f'run_freq should be one of {TIME_FREQ_STRINGS}, got {run_freq} instead')
        self._run_freq = run_freq

    @property
    def run_timing(self):
        """ 策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        return self._run_timing

    @run_timing.setter
    def run_timing(self, run_timing):
        """ 设置策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        self._run_timing = run_timing

    @property
    def data_type_count(self):
        """策略依赖的历史数据类型的数量"""
        return len(self.data_types)

    @property
    def data_types(self):
        """策略依赖的历史数据类型"""
        return self._data_types

    @data_types.setter
    def data_types(self, data_types: Union[DataType, List[DataType], Dict[str, DataType]]):
        """设置策略依赖的历史数据类型"""
        self.set_data_types(
                data_types,
                False,
                30,
        )

    @property
    def data_type_ids(self):
        """策略依赖的历史数据类型的ID"""
        return self._data_ids

    @property
    def data_ids(self):
        """策略依赖的历史数据类型的名称"""
        return self._data_ids

    @property
    def data_names(self):
        """策略依赖的历史数据类型的名称"""
        return {dtype_id: dtype.name for dtype_id, dtype in self._data_types.items()}

    @property
    def data_freqs(self):
        """策略依赖的历史数据类型的频率"""
        return {dtype_id: dtype.freq for dtype_id, dtype in self._data_types.items()}

    @property
    def data_ulc(self):
        """策略依赖的历史数据类型的最新周期使用标志"""
        return self._data_ULC

    @property
    def data_window_lengths(self):
        """策略依赖的历史数据类型的窗口长度"""
        return self._data_WL

    @property
    def window_lengths(self):
        """策略依赖的历史数据类型的窗口长度"""
        return self._data_WL

    @property
    def max_window_length(self):
        """ 策略所有历史数据种类中，最大的窗口长度"""
        return max(self._data_WL.values()) if self._data_WL else 0

    @property
    def share_count(self):
        """运行时参数，策略运行时的股票数量，只有运行后才能确定"""
        return self._share_count

    @property
    def share_names(self):
        """运行时参数，策略运行时的股票名称列表，只有运行后才能确定"""
        if self._share_names is None:
            warnings.warn('share_names is not set, please initialize the strategy first')
            return []
        return self._share_names

    def get_use_latest_data_cycle(self, data_type: str = None) -> bool:
        """ 根据dtype_id获取历史数据的最新周期使用参数"""
        return self._data_ULC[data_type]

    def get_data_ulc(self, data_type: str = None) -> bool:
        """ 根据dtype_id获取历史数据的最新周期使用参数"""
        return self._data_ULC[data_type]

    def get_window_length(self, data_type: str = None) -> int:
        """根据dtype_id获取历史数据窗口长度"""
        return self._data_WL[data_type]

    def get_data_name(self, data_type: str = None) -> str:
        """ 根据dtype_id获取数据类型的名称"""
        return self.data_names[data_type]

    def __str__(self):
        """返回交易策略的主要信息"""
        return f'Strategy {self.stg_type}({self.name})'

    def __repr__(self):
        """ 打印对象的代表信息

        Returns
        -------
        str
        """
        return f'{self._stg_type}({self.name}, {self.par_values})'

    def info(self, verbose: bool = False, status: bool = False, stg_id: str = None, extra_info = None) -> None:
        """打印所有相关信息和主要属性

        Parameters
        ----------
        verbose: bool, default False
            是否打印更多的信息
        status: bool, default False
            是否打印策略的运行状态
        stg_id: str, default None
            策略的ID，如果为None，则打印策略的名称，否则打印策略的ID
        extra_info: str, default None
            额外的信息，可以是任何字符串，会被打印在策略主信息之后，参数和数据之前

        Returns
        -------
        None
        """
        from rich import print as rprint
        from shutil import get_terminal_size
        from .utilfuncs import adjust_string_length

        if stg_id is None:
            stg_id = self.name
        term_width = get_terminal_size().columns
        info_width = int(term_width * 0.75) if term_width > 120 else term_width
        key_width = max(24, int(info_width * 0.3))
        value_width = max(7, info_width - key_width)
        stg_title = f' Strategy: {stg_id} '
        rprint(f'{stg_title:=^{info_width}}')
        if verbose:
            rprint(f'{self.__str__()}: {self.description}')
        else:
            rprint(self.__str__())

        if verbose:
            # 打印额外信息
            if extra_info:
                rprint(extra_info)

            # 打印所有策略可调参数相关信息
            par_name_width = int(info_width * .1)
            par_type_width = int(info_width * .2)
            par_range_width = int(info_width * .2)
            par_value_width = int(info_width * .5)
            rprint(f'{" Parameters ":-^{info_width}}\n'
                   f'{"name":<{par_name_width}}'
                   f'{"type":<{par_type_width}}'
                   f'{"range":<{par_range_width}}'
                   f'{"value":<{par_value_width}}')
            for par_name, par in self.pars.items():
                rprint(
                        f'{adjust_string_length(par_name, par_name_width) :<{par_name_width}}'
                        f'{adjust_string_length(par.par_type, par_type_width) :<{par_type_width}}'
                        f'{adjust_string_length(str(par.par_range), par_range_width) :^{par_range_width}}'
                        f'{adjust_string_length(str(par.value), par_value_width) :^{par_value_width}}'
                )

            # 打印所有策略数据类型相关信息
            dtype_id_width = int(info_width * .2)
            window_width = int(info_width * .1)
            ulc_width = int(info_width * .2)
            description_width = int(info_width * .5)
            rprint(f'{" Data Types ":-^{info_width}}\n'
                   f'{"id":<{dtype_id_width}}'
                   f'{"window":<{window_width}}'
                   f'{"use latest":<{ulc_width}}'
                   f'{"description":<{description_width}}')
            for dtype_id, dtype in self.data_types.items():
                rprint(
                        f'{adjust_string_length(dtype_id, dtype_id_width) :<{dtype_id_width}}'
                        f'{adjust_string_length(str(self.get_window_length(dtype_id)), window_width) :<{window_width}}'
                        f'{adjust_string_length(str(self.get_data_ulc(dtype_id)), ulc_width) :^{ulc_width}}'
                        f'{adjust_string_length(str(dtype.description), description_width, hans_aware=True) :^{description_width}}'
                )
        else:
            par_info = f'{self.par_names}, {self.par_values}'
            dtype_info = ', '.join([f'{dtype}@{window}d' for dtype, window in self.window_lengths.items()])
            rprint(f'Parameters: {par_info:<{value_width}}')
            rprint(f'Date Types: {dtype_info:<{value_width}}')
            # 打印额外信息
            if extra_info:
                rprint(extra_info)

    def set_pars(self, pars: Union[Parameter, List[Parameter], Dict[str, Parameter]]) -> None:
        """ 设置参数字典，设置par对象的名字，设置策略的attribute
        不设定参数的值

        Parameters
        ----------
        pars: Parameter, list of Parameters, tuple of Parameters, dict{str: Parameter}
            需要设置的参数字典，key为参数名、value为参数

        Returns
        -------
        None
        """

        if pars is None:
            pars = {}
        # 如果给出了pars且为tuple时，pars必须是Parameter对象，
        elif isinstance(pars, Parameter):
            pars = {pars.name: pars}
        elif isinstance(pars, (list, tuple)):
            if not all(isinstance(par, Parameter) for par in pars):
                raise TypeError(f'pars should be a list of Parameter objects, got {type(pars)} instead')
            pars = {par.name: par for par in pars}
        elif isinstance(pars, dict):
            # 确保每一个par.name与key一致
            for key, par in pars.items():
                if not isinstance(par, Parameter):
                    raise TypeError(f'pars should be a dict of Parameter objects, got {type(pars)} instead')
                if key != par.name:
                    par.name = key
        else:
            raise TypeError(f'pars is in invalid type! ({type(pars)})')

        if not _dict_par_format_is_valid('pars', pars, Parameter, 'name'):
            raise ValueError(f'pars is invalid! ({pars})')

        self._pars = {name: par for name, par in pars.items()}

        for name, par in pars.items():
            par.name = name
            self.__setattr__(name, par.value)

        return

    def get_pars(self, *par_names):
        """get the value of parameter by its name or id, alias as operator.par_name
        multiple parameters can be got at one time"""
        return self._get_pars_or_data(*par_names)

    def _get_pars_or_data(self, *names: str):
        """get the value of parameter or data by its name or id, alias as operator.par_name or operator.dtype_id
        multiple parameters or data can be got at one time"""
        undefined_names = [name for name in names if name not in self.par_names and name not in self.data_type_ids]
        if undefined_names:
            raise KeyError(f'names {undefined_names} not defined in strategy {self}')
        if len(names) > 1:
            return tuple(self.__getattribute__(name) for name in names)
        else:
            return self.__getattribute__(names[0])

    def set_data_types(self,
                       data_types: Union[DataType, List[DataType], Dict[str, DataType]],
                       use_latest_data_cycle,
                       window_length) -> None:
        """ 设置策略参数

        Parameters
        ----------
        data_types: DataType，list of DataType, dict {str: DataType}
            需要设置的参数字典，key为参数名、value为参数
        use_latest_data_cycle: bool, list of bool, dict {str: bool}
            是否使用最新的数据周期生成交易信号，默认仅使用截止到上一周期的数据生成交易信号
        window_length: int, list of int, dict {str: int}
            策略使用的数据窗口长度，即策略使用的历史数据的长度

        Returns
        -------
        int: 1: 设置成功，0: 设置失败
        """
        if data_types is None:
            data_types = {}
        elif isinstance(data_types, DataType):
            data_types = {data_types.dtype_id: data_types}
        elif isinstance(data_types, (list, tuple)):
            data_types = {dtype.dtype_id: dtype for dtype in data_types}
        elif isinstance(data_types, dict):
            # set up dtype_id for each DataType object
            for key, dtype in data_types.items():
                if not isinstance(dtype, DataType):
                    raise TypeError(f'pars should be a dict of DataType objects, got {type(data_types)} instead')
                if key != dtype.dtype_id:
                    dtype.dtype_id = key
        else:
            raise TypeError(f'pars is invalid! ({data_types})')

        if not _dict_par_format_is_valid('data_types', data_types, DataType, 'dtype_id'):
            raise ValueError(f'pars is invalid! ({data_types})')

        self._data_types = data_types
        self._data_ids = [dtype_name for dtype_name in data_types]
        self._data_types = data_types

        # 设置ULC
        if isinstance(use_latest_data_cycle, bool):
            self._data_ULC = {d_name: use_latest_data_cycle for d_name in self.data_types}
        elif isinstance(use_latest_data_cycle, (list, tuple)):
            ULCs = input_to_list(use_latest_data_cycle, len(self.data_types), False)
            self._data_ULC = {self._data_ids[i]: ULCs[i] for i in range(len(ULCs))}
        elif isinstance(use_latest_data_cycle, dict):
            self._data_ULC = {d_name: False for d_name in self._data_ids}
            self._data_ULC.update(use_latest_data_cycle)
        elif use_latest_data_cycle is None:
            self._data_ULC = {d_name: False for d_name in self._data_ids}
        else:
            raise TypeError(f'parameter "use_latest_data_cycles" is invalid ({use_latest_data_cycle}), '
                            f'please check your input')

        # 设置window lengths
        if isinstance(window_length, (int, float)):
            if window_length <= 0:
                raise ValueError(f'window_length should be a positive integer, got {window_length} instead')
            window_length = int(window_length)
            self._data_WL = {d_name: window_length for d_name in self.data_types}
        elif isinstance(window_length, (list, tuple)):
            WLs = input_to_list(window_length, len(self.data_types), 20)
            self._data_WL = {self._data_ids[i]: WLs[i] for i in range(len(WLs))}
        elif isinstance(window_length, dict):
            self._data_WL = {d_name: 20 for d_name in self._data_ids}
            self._data_WL.update(window_length)
        elif window_length is None:
            self._data_WL = {d_name: 20 for d_name in self._data_ids}
        else:
            raise TypeError(f'parameter "window_length" is invalid ({window_length}), please check your input')

        for dtype_id in data_types:
            self.__setattr__(dtype_id, None)

    def get_data(self, *dtype_id):
        """通过dtype_id获取历史数据，可以获取多个数据类型的数据"""
        return self._get_pars_or_data(*dtype_id)

    def update_data_types(self,
                          dtype_id=None,
                          *,
                          use_latest_data_cycle: Union[bool, tuple[bool], list[bool], dict[str, bool]] = None,
                          window_length: Union[int, tuple[int], list[int], dict[str, int]] = None) -> None:
        """ 更新交易策略的数据参数，可以更新单个数据类型的参数，也可以更新多个数据类型的参数
        如果给出dtype_id，则更新单个参数，否则更新所有参数
        """
        if dtype_id is not None:
            if dtype_id not in self.data_types:
                raise KeyError(f'data type {dtype_id} is not defined in the strategy')
            if use_latest_data_cycle is not None:
                assert isinstance(use_latest_data_cycle, bool), \
                    f'use_latest_data_cycle should be a boolean, got {type(use_latest_data_cycle)} instead'
                self._data_ULC[dtype_id] = use_latest_data_cycle
            if window_length is not None:
                assert isinstance(window_length, int) and window_length > 0, \
                    f'window_length should be a positive integer, got {window_length} instead'
                self._data_WL[dtype_id] = window_length
        else:  # 如果没有给出dtype_id，则更新所有参数或按照dict更新参数
            if use_latest_data_cycle is not None:
                if isinstance(use_latest_data_cycle, bool):
                    self._data_ULC = {d_name: use_latest_data_cycle for d_name in self.data_types}
                elif isinstance(use_latest_data_cycle, (list, tuple)):
                    if len(use_latest_data_cycle) != len(self.data_types):
                        raise ValueError(f'Length of use_latest_data_cycle should be {len(self.data_types)}, '
                                         f'got {len(use_latest_data_cycle)} instead')
                    ULCs = input_to_list(use_latest_data_cycle, len(self.data_types), False)
                    self._data_ULC = {self._data_ids[i]: ULCs[i] for i in range(len(ULCs))}
                elif isinstance(use_latest_data_cycle, dict):
                    assert all(isinstance(v, bool) for v in use_latest_data_cycle.values()), \
                        f'All use_latest_data_cycle should be boolean, got {use_latest_data_cycle} instead'
                    self._data_ULC.update(use_latest_data_cycle)
                else:
                    raise TypeError(f'Only one "use_latest_data_cycles" should be given when dtype_id is None, ')
            if window_length is not None:
                if isinstance(window_length, (int, float)):
                    if window_length <= 0:
                        raise ValueError(f'window_length should be a positive integer, got {window_length} instead')
                    window_length = int(window_length)
                    self._data_WL = {d_name: window_length for d_name in self.data_types}
                elif isinstance(window_length, (list, tuple)):
                    if len(window_length) != len(self.data_types):
                        raise ValueError(f'Length of window_length should be {len(self.data_types)}, '
                                         f'got {len(window_length)} instead')
                    WLs = input_to_list(window_length, len(self.data_types), 20)
                    self._data_WL = {self._data_ids[i]: WLs[i] for i in range(len(WLs))}
                elif isinstance(window_length, dict):
                    assert all(isinstance(v, int) for v in window_length.values()), \
                        f'All window lengths should be positive integers, got {window_length} instead'
                    self._data_WL.update(window_length)
                else:
                    raise TypeError(f'parameter "window_length" is invalid ({window_length}), please check your input')

    def update_par_values(self, *par_values: Any, **kwargs: Any) -> None:
        """ 快速更新策略的参数值

        Parameters
        ----------
        par_values: tuple, optional
            策略参数的值，元组中的每个元素是按顺序排列的所有参数值，如果
            没有设置参数，则必须传入kwargs参数
        kwargs: dict
            以字典形式传入具体需要更新的参数值，键为参数名，值为参数值

        Returns
        -------
        None
        """
        # allow updating partial parameter values, thus length check is not needed
        if par_values != ():
            if len(par_values) > self.par_count:
                raise ValueError(f'Number of par_values should not exceed {self.par_count}, '
                                 f'got {len(par_values)} instead')
            for par_name, par_value in zip(self.par_names, par_values):
                self._pars[par_name].value = par_value
                self.__setattr__(par_name, par_value)
        else:  # 如果没有传入par_values，则必须传入kwargs参数
            if not kwargs:
                raise ValueError('par_values is None, please provide par_values or kwargs to update parameters')
            for par_name, par_value in kwargs.items():
                if par_name not in self.par_names:
                    raise KeyError(f'parameter {par_name} is not defined in the strategy')
                self._pars[par_name].value = par_value
                self.__setattr__(par_name, par_value)

    def update_par_ranges(self, *par_ranges: Any, **kwargs) -> None:
        """ 快速更新策略的参数取值范围

        Parameters
        ----------
        par_ranges: tuple of dict, optional
            策略参数的取值范围，元组中的每个元素是按顺序排列的所有参数取值范围的字典，
            如果没有设置参数，则必须传入kwargs参数

        Returns
        -------
        None
        """
        # allow updating partial parameter ranges, thus length check is not needed
        if par_ranges != ():
            if len(par_ranges) > self.par_count:
                raise ValueError(f'Number of par_ranges should not exceed {self.par_count}, '
                                 f'got {len(par_ranges)} instead')
            for par_name, par_range in zip(self.par_names, par_ranges):
                self._pars[par_name].update_par_range(new_range=par_range)
        else:  # 如果没有传入par_ranges，则必须传入kwargs参数
            if not kwargs:
                raise ValueError('par_ranges is None, please provide par_ranges or kwargs to update parameter ranges')
            for par_name, par_range in kwargs.items():
                if par_name not in self.par_names:
                    raise KeyError(f'parameter {par_name} is not defined in the strategy')
                self._pars[par_name].update_par_range(new_range=par_range)

    def set_opt_tag(self, opt_tag: int) -> int:
        """ 设置策略的优化类型"""
        assert isinstance(opt_tag, int), f'optimization tag should be an integer, got {type(opt_tag)} instead'
        assert 0 <= opt_tag <= 2, f'ValueError, optimization tag should be between 0 and 2, got {opt_tag} instead'
        self._opt_tag = opt_tag
        return opt_tag

    def update_running_data_window(self, data_windows:dict, window_indices:dict, window_index:int):
        """ 将策略的历史数据更新为window_index指定的历史数据"""
        data_window = None
        for dtype_name in self.data_types:
            data_window = data_windows[dtype_name][window_indices[dtype_name][window_index]]
            setattr(self, dtype_name, data_window)
        self._share_count = data_window.shape[1] if data_window is not None else 0
        self._share_names = data_window.index.tolist() if isinstance(data_window, pd.DataFrame) else None

    def set_custom_pars(self, **kwargs):
        """如果还有其他策略参数或用户自定义参数，在这里设置"""
        for k, v in zip(kwargs.keys(), kwargs.values()):
            if k in self.__dict__:
                setattr(self, k, v)
            else:
                raise KeyError(f'The strategy does not have property \'{k}\'')

    @abstractmethod
    def generate(self):
        """策略类的抽象方法，接受输入历史数据并根据参数生成策略输出

        Parameters
        ----------

        Returns
        -------
        stg_signal: np.ndarray
            策略运行的输出，包括交易信号、交易指令等
        """


class GeneralStg(BaseStrategy):
    """ 通用交易策略类，用户需要完整定义策略的所有交易逻辑，并在realize()方法中定义策略
    的信号输出。

    realize()方法的输出：
    realize()方法的输出就是交易信号(1D ndarray),shape为(M,)，M为股票的个数，dtype为float

    关于GeneralStg类的更详细说明，请参见qteasy的文档。
    """
    __metaclass__ = ABCMeta

    # 设置Selecting策略类的标准默认参数，继承Selecting类的具体类如果沿用同样的静态参数，不需要重复定义
    def __init__(self,
                 name: str = 'General',
                 description: str = 'description of General strategy',
                 **kwargs):
        super().__init__(stg_type='GENERAL',
                         name=name,
                         description=description,
                         **kwargs)

    def generate(self):
        """ 通用交易策略的所有策略代码全部都在realize中实现
        """
        return self.realize()

    @abstractmethod
    def realize(self):
        """ h_seg和ref_seg都是用于生成交易信号的一段窗口数据，根据这一段窗口数据
            生成一条交易信号
            交易信号的格式必须为1D 的numpy数组，数据类型为float
        """
        pass


class FactorSorter(BaseStrategy):
    """ 因子排序选股策略，根据用户定义的选股因子筛选排序后确定每个股票的选股权重(请注意，FactorSorter策略
        生成的交易信号在0到1之间，推荐设置signal_type为"PT")

    这类策略要求用户从历史数据中提取一个选股因子，并根据选股因子的大小排序后确定投资组合中股票的交易信号
    用户需要在realize()方法中计算选股因子，计算出选股因子后，接下来的排序和选股逻辑都不需要用户自行定义。
    策略会根据预设的条件，从中筛选出符合标准的因子，并将剩下的因子排序，从中选择特定数量的股票，最后根据它
    们的因子值分配权重或信号值。

    这些选股因子的排序和筛选条件，由6个选股参数来控制，因此用户只需要在策略属性中设置好相应的参数，
    策略就可以根据选股因子输出交易信号了。用户只需要集中精力思考选股因子的定义逻辑即可，无需费时费力编写
    因子的筛选排序取舍逻辑了。

    这六个选股参数如下：

        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False, True: 优先选择因子最小的股票, False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比

    realize()方法的输出：
    FactorSorter交易策略的输出信号为1D ndarray，这个数组不是交易信号，而是选股因子，策略会根据选股因子
    自动生成股票的交易信号，通常交易信号类型应该为PT，即使用选股因子控制股票的目标仓位。

        output：
                np.array(arr), 如： np.array[0.1, 1.0, 10.0, 100.0]

    根据上述选股因子，FactorSorter()策略会根据其配置参数生成各个股票的目标仓位，
        例如：当
                max_sel_count=0.5
                condition='greater',
                ubound=0.5,
                weighting='even'
        时，上述因子的选股结果为:
                np.array[0.0, 0.0, 0.5, 0.5]

    关于Strategy类的更详细说明，请参见qteasy的文档。

    """
    __metaclass__ = ABCMeta

    # 设置Selecting策略类的标准默认参数，继承Selecting类的具体类如果沿用同样的静态参数，不需要重复定义
    def __init__(self,
                 name: str = 'Factor',
                 description: str = 'description of factor sorter strategy',
                 max_sel_count: float = 0.5,
                 condition: str = 'any',
                 lbound: float = -np.inf,
                 ubound: float = np.inf,
                 sort_ascending: bool = False,
                 weighting: str = 'even',
                 **kwargs):
        super().__init__(stg_type='FACTOR',
                         name=name,
                         description=description,
                         **kwargs)
        self.max_sel_count = max_sel_count
        self.condition = condition
        self.lbound = lbound
        self.ubound = ubound
        self.sort_ascending = sort_ascending
        self.weighting = weighting

    def info(self, verbose: bool = False, stg_id=None, **kwargs):
        """ display more FactorSorter-specific properties

        Parameters
        ----------
        verbose: bool
            if True, display more properties
        stg_id: str
            strategy id, if None, use self.name
        **kwargs:
            other parameters
        """
        from .utilfuncs import adjust_string_length
        from shutil import get_terminal_size

        term_width = get_terminal_size().columns
        info_width = int(term_width * 0.75) if term_width > 120 else term_width
        key_width = max(24, int(info_width * 0.3))
        value_width = max(7, info_width - key_width)

        extra_info = f'{" Selection Properties ":-^{info_width}}\n'
        if self.max_sel_count > 1:
            extra_info += f'{"Max select count":<{key_width}}{int(self.max_sel_count)}\n'
        else:
            extra_info += f'{"Max select count":<{key_width}}{self.max_sel_count:.1%}\n'
        extra_info += f'{"Sort Ascending":<{key_width}}{self.sort_ascending}\n' \
               f'{"Weighting":<{key_width}}{adjust_string_length(self.weighting, value_width)}\n' \
               f'{"Filter Condition":<{key_width}}{adjust_string_length(self.condition, value_width)}\n' \
               f'{"Filter ubound":<{key_width}}{self.ubound}\n' \
               f'{"Filter lbound":<{key_width}}{self.lbound}'

        super().info(verbose=verbose, stg_id=stg_id, extra_info=extra_info)

    def generate(self):
        """处理从_realize()方法传递过来的选股因子

        选出符合condition的因子，并将这些因子排序，根据次序确定所有因子相应股票的选股权重
        将选股权重传递到generate()方法中，生成最终的选股交易信号

        Parameters
        ----------

        Returns
        -------
        chosen: numpy.ndarray
            一个一维向量，代表一个周期内股票的投资组合权重，所有权重的和为1
        """
        pct = self.max_sel_count
        condition = self.condition
        lbound = self.lbound
        ubound = self.ubound
        sort_ascending = self.sort_ascending  # True: 选择最小的，Fals: 选择最大的
        weighting = self.weighting

        # 获取realize()方法计算得到的选股因子
        factors = self.realize()

        share_count = factors.shape[0]
        if pct < 1:
            # pct 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            pct = int(share_count * pct)
        else:  # pct 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            pct = int(pct)
        if pct < 1:
            pct = 1

        # factors必须是一维向量，如果因子是二维向量，允许shape为(N, 1)型，此时将其转换为一维向量，否则报错
        if factors.ndim == 2:
            factors = factors.flatten()

        chosen = np.zeros_like(factors)
        # 筛选出不符合要求的指标，将他们设置为nan值
        if condition == 'any':
            pass
        elif condition == 'greater':
            factors[np.where(factors < ubound)] = np.nan
        elif condition == 'less':
            factors[np.where(factors > lbound)] = np.nan
        elif condition == 'between':
            factors[np.where((factors < lbound) | (factors > ubound))] = np.nan
        elif condition == 'not_between':
            factors[np.where((factors > lbound) & (factors < ubound))] = np.nan
        else:
            raise ValueError(f'invalid selection condition \'{condition}\''
                             f'should be one of ["any", "greater", "less", "between", "not_between"]')
        nan_count = np.isnan(factors).astype('int').sum()  # 清点数据，获取nan值的数量
        if nan_count == share_count:  # 当indices全部为nan，导致没有有意义的参数可选，此时直接返回全0值
            return chosen
        if not sort_ascending:
            # 选择分数最高的部分个股，由于np排序时会把NaN值与最大值排到一起，总数需要加上NaN值的数量
            pos = max(share_count - pct - nan_count, 0)
        else:  # 选择分数最低的部分个股
            pos = pct
        # 对数据进行排序，并把排位靠前者的序号存储在arg_found中
        if weighting == 'even':
            # 仅当投资比例为均匀分配时，才可以使用速度更快的argpartition方法进行粗略排序
            if not sort_ascending:
                share_found = factors.argpartition(pos)[pos:]
            else:
                share_found = factors.argpartition(pos)[:pos]
        else:  # 如果采用其他投资比例分配方式时，必须使用较慢的全排序
            if not sort_ascending:
                share_found = factors.argsort()[pos:]
            else:
                share_found = factors.argsort()[:pos]
        # nan值数据的序号存储在arg_nan中
        share_nan = np.where(np.isnan(factors))[0]
        # 使用集合操作从arg_found中剔除arg_nan，使用assume_unique参数可以提高效率
        args = np.setdiff1d(share_found, share_nan, assume_unique=True)
        # 构造输出向量，初始值为全0
        arg_count = len(args)
        # 如果符合条件的选项数量为0，则直接返回全0
        if arg_count == 0:
            return chosen
        # 根据投资组合比例分配方式，确定被选中产品的权重

        # ones：全1分配，所有中选股票在组合中权重相同且全部为1
        if weighting == 'ones':
            chosen[args] = 1.
        # linear 线性比例分配，将所有分值排序后，股票的比例呈线性分布
        elif weighting == 'linear':
            dist = np.arange(1, 3, 2. / arg_count)  # 生成一个线性序列，最大值为最小值的约三倍
            chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
        # distance：距离分配，权重与其分值距离成正比，分值最低者获得一个基础比例，其余股票的比例
        #  与其分值的距离成正比，分值的距离为它与最低分之间的差值，因此不管分值是否大于0，股票都能
        #  获取比例分配
        elif weighting == 'distance':
            dist = factors[args]
            d_max = dist[-1]
            d_min = dist[0]
            d = d_max - d_min
            if not sort_ascending:
                dist = dist - d_min + d / 10.
            else:
                dist = d_max - dist + d / 10.
            d_sum = dist.sum()
            if ~np.any(dist):  # if all distances are zero
                chosen[args] = 1 / len(dist)
            elif d_sum == 0:  # if not all distances are zero but sum is zero
                chosen[args] = dist / len(dist)
            else:
                chosen[args] = dist / d_sum
        # proportion：比例分配，权重与其分值成正比，分值为0或小于0者比例为0
        elif weighting == 'proportion':
            f = factors[args]
            f = np.where(f < 0, 0, f)  # np.where 比 np.clip(0) 速度快得多
            chosen[args] = f / f.sum()
        # even：均匀分配，所有中选股票在组合中权重相同
        elif weighting == 'even':
            chosen[args] = 1. / arg_count
        else:
            raise KeyError(f'invalid weighting type: "{weighting}". '
                           f'should be one of ["ones", "linear", "distance", "proportion", "even"]')
        return chosen

    @abstractmethod
    def realize(self):
        """ realize strategy here"""
        pass


class RuleIterator(BaseStrategy):
    """ 规则迭代策略类。这一类策略不考虑每一只股票的区别，将同一套规则同时迭代应用到所有的股票上。

    RuleIterator策略类的特殊功能是可以对同一套交易规则，将不同的参数应用到投资组合中的不同股票上。
    例如，用户可以设计一个均线交叉策略，并将其应用到投资组合中的所有股票上，同时可以为每只股票
    设定不同的均线周期参数。

    例如，用户可以为投资组合中的股票分别设定不同的均线参数：
        stock1: short_window=5, long_window=20
        stock2: short_window=10, long_window=50
        stock3: short_window=20, long_window=100
        stock4: short_window=30, long_window=200

    这样，用户只需要编写一套均线交叉的交易规则，就可以将其应用到投资组合中的所有股票上，同时
    还可以为每只股票设定不同的均线参数。这种特殊的交易策略，需要用到RuleIterator类的
    multi_pars属性。

    这类策略要求用户针对投资组合中的一个投资品种设计交易规则，在realize()方法定义该交易规则，
    策略可以把同样的交易规则应用推广到投资组合中的所有投资品种上，同时可以采用不同的策略参数。

    realize()方法的输出：
    realize()方法的输出就是交易信号，该交易信号是一个数字，策略会将其推广到整个投资组合：

        def realize(): -> int

        投资组合： [share1, share2, share3, share4]
                    |        |       |       |
                 [ int1,    int2,   int3,   int4] -> np.array[ int1,    int2,   int3,   int4]

    按照前述规则设置好策略的参数，并在realize函数中定义好逻辑规则后，一个策略就可以被添加到Operator
    中，并产生交易信号了。

    关于Strategy类的更详细说明，请参见qteasy的文档。
    RuleIterator 策略类继承了交易策略基类

    """
    __metaclass__ = ABCMeta

    def __init__(self,
                 name: str = 'Rule-Iterator',
                 description: str = 'description of rule iterator strategy',
                 allow_multi_par: bool = True,
                 **kwargs):
        super().__init__(name=name,
                         description=description,
                         stg_type='RULE-ITER',
                         **kwargs)
        self._data_windows = {}
        self.allow_multi_par = allow_multi_par  # 设置为True，表示策略可以对不同的股票使用不同的参数
        self.multi_pars = None

    def info(self, verbose: bool = False, stg_id=None, **kwargs):
        """ display more FactorSorter-specific properties

        Parameters
        ----------
        verbose: bool
            if True, display more properties
        stg_id: str
            strategy id, if None, use self.name
        **kwargs:
            other parameters
        """
        from shutil import get_terminal_size

        term_width = get_terminal_size().columns
        info_width = int(term_width * 0.75) if term_width > 120 else term_width
        key_width = max(24, int(info_width * 0.3))

        extra_info = f'{" Iteration Properties ":-^{info_width}}\n'
        extra_info += f'{"Allow multi pars":<{key_width}}{self.allow_multi_par}'

        if self.allow_multi_par:
            if not self.multi_pars:
                extra_info += f'\n{"Multi-parameter not set":<{info_width}}'
            elif verbose:  # print out complete multi_pars
                multi_par_str = '\n'.join([f'{str(k)}: {str(v)}' for k, v in self.multi_pars.items()])
                extra_info += f'\n{"Multi-parameter":<{info_width}}\n{multi_par_str}'
            else:  # print out brief multi_pars info
                extra_info += f'\n{"Multi-parameter (pass verbose=True to view all multi pars)":<{info_width}}\n' \
                              f'{self.multi_pars[self.multi_pars.values()[0]]}\n...'

        super().info(verbose=verbose, stg_id=stg_id, extra_info=extra_info)

    def update_par_values(self, *par_values: Any, **kwargs: Any) -> None:
        """ 快速更新策略的参数值，如果参数是一个multi_par，将其写入multi_par，
        并将其第一组参数值写入par_values

        Parameters
        ----------
        par_values: tuple, optional
            策略参数的值，元组中的每个元素是按顺序排列的所有参数值，如果
            没有设置参数，则必须传入kwargs参数
        kwargs: dict
            以字典形式传入具体需要更新的参数值，键为参数名，值为参数值

        Returns
        -------
        None
        """
        if not par_values:
            super().update_par_values(**kwargs)
            return

        if isinstance(par_values[0], dict):
            # par values中有multi_par，更新multi_par
            par_values = par_values[0]
            self._update_multi_pars(par_values)
            # 将第一个参数值写入par_values
            par_values = self.multi_pars[0]
            super().update_par_values(*par_values)
        else:
            # par_values是一个tuple或list，直接更新参数值
            super().update_par_values(*par_values)

    def _update_multi_pars(self, multi_pars):
        """ 设置多参数的函数，允许用户为每只股票设置不同的参数

        Parameters
        ----------
        multi_pars: tuple, list, ndarray, or dict {str: tuple, list, ndarray}
            策略参数列表，或者None

        Returns
        -------
        multi_pars: tuple
            返回一个元组，包含每个股票的参数，如果multi_pars为None，则返回一个空元组
        """
        if not self.allow_multi_par:
            # 如果不允许多参数，则直接返回一个空元组
            self.multi_pars = None
            raise ValueError('multi_pars is not allowed, you need to set allow_multi_par to True first')

        # 将tuple/list形式的multi_pars转化为dict形式，key为股票代码，value为参数的值元组
        if multi_pars is None:
            self.multi_pars = None
        elif isinstance(multi_pars, (tuple, list)):
            self.multi_pars = tuple(multi_pars)
        elif isinstance(multi_pars, dict):
            self.multi_pars = tuple(multi_pars.values())
        else:
            raise TypeError(f'multi_pars should be a tuple, list, or dict, not {type(multi_pars)}')

    def update_running_data_window(self, data_windows:dict, window_indices:dict, window_index:int):
        """ 将策略的历史数据更新为window_index指定的历史数据，对Rule_iterator来说数据不能直接保存到"""
        for dtype_name in self.data_types:
            data_window = data_windows[dtype_name][window_indices[dtype_name][window_index]]
            self._data_windows[dtype_name] = data_window
            self._share_count = data_window.shape[1] if data_window is not None else 0
            self._share_names = data_window.index.tolist() if isinstance(data_window, pd.DataFrame) else None

    def generate(self):
        """ 中间构造函数，将历史数据模块传递过来的单只股票历史数据去除nan值，并进行滚动展开
            对于滚动展开后的矩阵，使用map函数循环调用generate_one函数生成整个历史区间的
            循环回测结果（结果为1维向量， 长度为hist_length - _window_length + 1）

        Parameters
        ----------

        Returns
        -------
        signal: np.ndarray
            一维向量。根据策略，在历史上产生的仓位信号或交易信号，具体信号的含义取决于策略类型
        """
        # 生成iterators, 将参数送入realize_no_nan中逐个迭代后返回结果
        signal = np.empty(self.share_count, dtype=float)

        for i in range(self.share_count):
            if self.allow_multi_par and self.multi_pars:
                # 如果允许多参数，则为每个股票使用不同的参数
                par = self.multi_pars[i]
                self.update_par_values(*par)
            # 更新股票使用的数据
            for dtype_name in self.data_types:
                setattr(self, dtype_name, self._data_windows[dtype_name][:, i])
            signal[i] = self.realize()

        return signal

    @abstractmethod
    def realize(self):
        """ realize strategy here"""
        pass
