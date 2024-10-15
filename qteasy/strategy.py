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
import warnings

from qteasy.utilfuncs import (
    TIME_FREQ_STRINGS,
    str_to_list,
)


class BaseStrategy:
    """ 量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的策略类调用

    Properties
    ----------
    pars: any
        策略可调参数，可以是任意类型。策略的优化过程，就是寻找策略可调参数的最优组合的过程。
    opt_tag: int {0, 1}
        策略的优化标签，0表示不参与优化，1表示参与优化
    par_count: int
        策略可调参数的个数
    par_types: [list, str]
        策略可调参数的类型，可以是一个列表，也可以是一个字符串，如果是字符串，则表示所有参数的类型都相同
    par_range: [list, tuple]
        策略可调参数的取值范围，可以是一个列表，也可以是一个元组，如果是列表，则表示所有参数的取值范围都相同
    stg_type: str
        策略类型，用户自定义，用于区分不同的策略，例如均线策略、趋势跟随策略等
    name: str
        策略名称，用户自定义，用于区分不同的策略
    description: str
        策略描述，用户自定义，用于描述策略的基本原理
    data_freq: str
        策略所使用的数据的频率，可以是以下几种类型：
        'd'：日线数据
        'w'：周线数据
        'm'：月线数据
    sample_freq: str
        策略的采样频率，可以是以下几种类型：
        'd'：日线数据
        'w'：周线数据
        'm'：月线数据
    window_length: int
        策略所使用的数据的长度，即策略所使用的数据的长度，例如策略所使用的均线的长度
    data_types: [str, list]
        策略所使用的数据的类型，可以是一个字符串，也可以是一个列表，如果是字符串，则表示所有数据的类型都相同
    reference_data_types: [str, list]
        策略所使用的参考数据的类型，可以是一个字符串，也可以是一个列表，如果是字符串，则表示所有数据的类型都相同
    bt_price_type: str
        策略回测时的价格类型，可以是以下几种类型：
        'open'：开盘价
        'high'：最高价
        'low'：最低价
        'close'：收盘价

    Methods
    -------
    generate(data: np.ndarray, pars: any = None)
        生成策略信号，该方法是策略的核心方法，所有的策略都必须实现该方法

    """
    __mataclass__ = ABCMeta

    AVAILABLE_STG_RUN_TIMING = ['open', 'close', 'unit_nav', 'accum_nav']

    def __init__(
            self,
            pars: any = None,
            opt_tag: int = 0,
            stg_type: str = 'strategy type',
            name: str = 'strategy name',
            description: str = 'intro text of strategy',
            par_count: int = None,
            par_types: [[str], str] = None,
            par_range: [list, tuple] = None,
            strategy_run_freq: str = 'd',
            sample_freq: str = None,  # to be deprecated
            strategy_run_timing: str = 'close',
            bt_price_type: str = None,  # to be deprecated
            strategy_data_types: [str, [str]] = 'close',
            data_types: [str, [str]] = None,  # to be deprecated
            use_latest_data_cycle: bool = True,
            reference_data_types: [str, [str]] = '',
            data_freq: str = 'd',
            window_length: int = 270,
    ):
        """ 初始化策略

        Parameters
        ----------
        pars: any
            策略参数，可以是任意类型，但是需要根据具体的策略类来确定具体的参数类型
        opt_tag: int {0, 1}
            策略的优化标签，0表示不参与优化，1表示参与优化
        stg_type: str
            策略类型，用户自定义，用于区分不同的策略，例如均线策略、趋势跟随策略等
        name: str
            策略名称，用户自定义策略的名称，用于区分不同的策略
        description: str
            策略描述，用户自定义策略的描述，用于区分不同的策略
        par_count: int
            策略可调参数的个数
        par_types: list of str, {'int', 'float', 'enum'}
            策略可调参数的类型，每个参数的类型可以是int, float或enum
        par_range: list or tuple
            策略可调参数的取值范围，每个参数的取值范围可以是一个tuple，也可以是一个list
        strategy_run_freq: str {'d', 'w', 'm', 'q', 'y'}
            策略的运行频率，可以是分钟、日频、周频、月频、季频或年频，分别表示每分钟运行一次、每日运行一次等等
            TODO: 如果运行频率低于日频，可以通过'w-Fri'等方式指定哪一天运行
        sample_freq: str, deprecated
            策略的运行频率，可以是分钟、日频、周频、月频、季频或年频，分别表示每分钟运行一次、每日运行一次等等
        strategy_run_timing: datetime-like or str
            策略运行的时间点，策略运行频率低于天时，这个参数是一个时间，表示策略每日的运行时间
            例如'09:30:00'表示每天的09:30:00运行策略，可以设定为'open'或'close'，表示每天开盘或收盘运行策略
            如果运行频率高于天频，则这个参数无效，策略运行时间为交易日正常交易时段中频次分割点。
            例如，如果运行频率为'h', 假设股市9：30开市，15：30收市
            则策略运行时间为
            ['09:30:00', '10:30:00',
             '11:30:00', '13:00:00',
             '14:00:00', '15:00:00',]
        bt_price_type: str, deprecated
            策略运行的时间点，策略运行频率低于天时，这个参数是一个时间，表示策略每日的运行时间
        strategy_data_types: str or list of str
            策略使用的数据类型，例如close, open, high, low等
        data_types: str or list of str, deprecated
            策略使用的数据类型，例如close, open, high, low等
        use_latest_data_cycle: bool, default True
            是否使用最新的数据周期生成交易信号，默认True
            如果为True: 默认值
                在实盘运行时，会尝试下载当前周期的最新数据，或尝试使用最近的实时数据估算当前周期的数据，此时应该注意避免出现未来函数，
                    如运行时间点为开盘时，这时就不能使用收盘价/最高价/最低价生成交易信号，会导致策略运行失真。
                在回测交易时，会使用回测当前时间点的最新数据生成交易信号。此时应该注意避免出现未来函数，如回测时间点为
                    开盘时，但是使用当前周期的收盘价生成交易信号，会导致策略运行失真。
            如果为False：
                在回测或实盘运行时都仅使用当前已经获得的上一周期的已知数据生成交易信号，在运行频率较低时，可能会导致
                    交易信号的滞后，但是可以避免未来函数的出现。
        reference_data_types: str or list of str
            策略使用的参考数据类型，例如close, open, high, low等
        data_freq: str {'d', 'w', 'm', 'q', 'y'}
            策略使用的数据频率，可以是日频、周频、月频、季频或年频
        window_length: int
            策略使用的数据窗口长度，即策略使用的历史数据的长度

        Returns
        -------
        None
        """
        # 关于已经废弃的参数，给出警告信息，并赋值给新的参数
        if sample_freq is not None:
            warnings.warn('sample_freq is deprecated, use strategy_run_freq instead')
            strategy_run_freq = sample_freq
        if bt_price_type is not None:
            warnings.warn('bt_price_type is deprecated, use strategy_run_timing instead')
            strategy_run_timing = bt_price_type
        if data_types is not None:
            warnings.warn('data_types is deprecated, use strategy_data_types instead')
            strategy_data_types = data_types

        # 检查策略参数是否合法：
        # 如果给出了策略参数，则根据参数推测并设置par_count/par_types/par_range等三个参数
        from qteasy import logger_core
        logger_core.info(f'initializing new Strategy: type: {stg_type}, name: {name}, text: {description}')
        implied_par_count = None
        implied_par_types = None
        implied_par_range = None
        if pars is None:
            pass
        # 如果给出了pars且为tuple时，推测 par_count, par_types, par_range 三个参数的值
        elif isinstance(pars, (tuple, list)):
            implied_par_count = len(pars)
            implied_par_types = []
            implied_par_range = []
            for item in pars:
                if isinstance(item, int):
                    implied_par_types.append('int')
                    implied_par_range.append((item, item + 1))
                elif isinstance(item, float):
                    implied_par_types.append('float')
                    implied_par_range.append((item - 1, item + 1))
                elif isinstance(item, str):
                    implied_par_types.append('enum')
                    implied_par_range.append(tuple([item]))
                else:
                    raise TypeError(f'Invalid parameter item type: ({type(item)}), parameter can only contain'
                                    f'integers, floats or strings')
        # 如果给出了pars且为dict时，仅检查是否dict中的所有值都是tuple
        elif isinstance(pars, dict):
            if not all(isinstance(item, tuple) for item in pars.values()):
                raise TypeError(f'All items is a dict type parameter should be tuples, invalid type encountered')

        else:
            raise TypeError(f'Invalid parameter type. pars should be a tuple, '
                            f'a list or a dict, got {type(pars)} instead.')

        # 如果给出了par_count/par_types/par_range等三个参数，则检查其合法性，如果合法，替换
        # 推测参数（若存在），如果不合法，使用推测参数（若存在）并给出警告，如果推测参数不存在，
        # 则报错，并给出有价值的指导意见
        if par_count is None:
            par_count = implied_par_count
        else:
            # TODO: 按照当前的代码，par_count一但设置后就无法修改，这点是否合理？
            if not isinstance(par_count, int):
                raise TypeError(f'parameter count (par_count) should be a integer, got {type(par_count)} instead.')
            if par_count < 0:
                raise ValueError(f'Invalid parameter count ({par_count}), it should not be less than 0')
            if implied_par_count is not None:
                if par_count != implied_par_count:
                    logger_core.warning(f'Invalid parameter count ({par_count}), given parameter implies '
                                        f'({implied_par_count})'
                                        f'par_count adjusted, you should '
                                        f'probably pass "par_count = {implied_par_count}"')
                    par_count = implied_par_count

        if par_types is None:
            par_types = implied_par_types
        else:
            if not isinstance(par_types, (str, list)):
                raise TypeError(f'parameter types (par_types) should be a string or list of strings, '
                                f'got {type(par_types)} instead')
            if isinstance(par_types, str):
                par_types = str_to_list(par_types)
            for item in par_types:
                if not isinstance(item, str):
                    raise KeyError(f'Invalid type ({type(item)}), should only pass strings in par_types')
                if not item.lower() in ['int', 'float', 'conti', 'discr', 'enum', 'list']:
                    raise KeyError(f'Invalid type ({item}), should be one of "int, float, conti, discr, enum, list"')
            if len(par_types) < par_count:
                logger_core.warning(f'Not enough parameter types({len(par_types)}) to assign'
                                    f' to all ({par_count}) parameters')
            elif len(par_types) > par_count:
                logger_core.info(f'Got more parameter types({len(par_types)}) than count of parameters({par_count})')
                par_types = par_types[0:par_count]

        if par_range is None:
            par_range = implied_par_range
        else:
            if not isinstance(par_range, (tuple, list)):
                raise TypeError(f'parameter range (par_range) should be a tuple or a list, '
                                f'got {type(par_range)} instead')
            for item in par_range:
                if not isinstance(item, (tuple, list)):
                    raise KeyError(f'Invalid type ({type(item)}), should only pass strings in par_types')
            if len(par_range) < par_count:
                logger_core.warning(f'Not enough parameter ranges({len(par_range)}) to assign'
                                    f' to all ({par_count}) parameters')
            elif len(par_range) > par_count:
                logger_core.info(f'Got more parameter types({len(par_range)}) than count of parameters({par_count})')
                par_range = par_range[0:par_count]

        self._pars = None
        self._opt_tag = None
        self.set_opt_tag(opt_tag)  # 策略的优化标记，
        self._stg_type = stg_type  # 策略类型
        self._stg_name = name  # 策略的名称
        self._stg_text = description  # 策略的描述文字
        self._par_count = par_count  # 策略参数的元素个数
        self._par_types = par_types  # 策略参数的类型，可选类型'int/float/discr/conti/enum/list'
        self._par_bounds_or_enums = par_range
        self.set_pars(pars)  # 设置策略参数，使用set_pars()函数同时检查参数的合法性
        logger_core.info(f'Strategy created with basic parameters set, pars={pars}, par_count={par_count},'
                         f' par_types={par_types}, par_range={par_range}')

        # 其他的几个参数都通过参数赋值方法赋值，在赋值方法内会进行参数合法性检，这里只需确保所有参数不是None即可
        assert data_freq is not None
        assert strategy_run_freq is not None
        assert window_length is not None
        assert strategy_data_types is not None
        assert strategy_run_timing is not None
        assert reference_data_types is not None
        assert use_latest_data_cycle is not None
        self._data_freq = None
        self._strategy_run_freq = None
        self._window_length = None
        self._data_types = None
        self._strategy_run_timing = None
        self._reference_data_types = None
        self._use_latest_data_cycle = None
        self.set_hist_pars(data_freq=data_freq,
                           strategy_run_freq=strategy_run_freq,
                           window_length=window_length,
                           strategy_data_types=strategy_data_types,
                           strategy_run_timing=strategy_run_timing,
                           reference_data_types=reference_data_types,
                           use_latest_data_cycle=use_latest_data_cycle)
        logger_core.info(
            f'Strategy creation. with other parameters: data_freq={data_freq}, strategy_run_freq={strategy_run_freq},'
            f' window_length={window_length}, strategy_run_timing={strategy_run_timing}, '
            f'reference_data_types={reference_data_types}')

    @property
    def stg_type(self):
        """策略类型，表明策略的基类，即：
            - GeneralStg: GENERAL
            - FactorSorter: FACTOR
            - RuleIterator: RULE-ITER
        """
        return self._stg_type

    @property
    def pars(self):
        """策略参数，是一个列表，列表中的每个元素都是一个参数值"""
        return self._pars

    @pars.setter
    def pars(self, new_pars: (tuple, dict)):
        """设置策略参数，参数的合法性检查在这里进行"""
        self.set_pars(new_pars)

    @property
    def name(self):
        """策略名称，打印策略信息的时候策略名称会被打印出来"""
        return self._stg_name

    @name.setter
    def name(self, name: str):
        self._stg_name = name

    @property
    def description(self):
        """策略说明文本，对策略的实现方法和功能进行简要介绍"""
        return self._stg_text

    @description.setter
    def description(self, description: str):
        if not isinstance(description, str):
            raise TypeError(f'description should be a string, got {type(description)} instead.')
        self._stg_text = description

    @property
    def par_count(self):
        """策略的参数数量"""
        return self._par_count

    @par_count.setter
    def par_count(self, par_count: int):
        if not isinstance(par_count, int):
            raise TypeError(f'par count should be an integer, got {type(par_count)} instead.')
        self._par_count = par_count

    @property
    def par_types(self):
        """策略的参数类型，与Space类中的定义匹配，分为离散型'discr', 连续型'conti', 枚举型'enum'"""
        return self._par_types

    @par_types.setter
    def par_types(self, par_types: [list, str]):
        """ 设置par_types属性

        输入的par_types可以允许为字符串或列表，当给定类型为字符串时，使用逗号分隔不同的类型，如
        'conti, conti' 代表 ['conti', 'conti']

        Parameters
        ----------
        par_types: [list, str]
            策略的参数类型，与Space类中的定义匹配，分为离散型'discr', 连续型'conti', 枚举型'enum',
            或者也可以为'int', 'float'分别表示离散型和连续型

        Returns
        -------
        None
        """
        if par_types is None:
            # 当没有给出策略参数类型时，参数类型为空列表
            self._par_types = []
        else:
            if isinstance(par_types, str):
                par_types = str_to_list(par_types, ',')
            assert isinstance(par_types, list), f'TypeError, par type should be a list, got {type(par_types)} instead'
            self._par_types = par_types

    @property
    def par_range(self):
        """策略的参数取值范围，用来定义参数空间用于参数优化"""
        return self._par_bounds_or_enums

    @par_range.setter
    def par_range(self, boes: list):
        self.set_par_range(par_range=boes)

    @property
    def opt_tag(self):
        """策略的优化类型"""
        return self._opt_tag

    @opt_tag.setter
    def opt_tag(self, opt_tag):
        self.set_opt_tag(opt_tag=opt_tag)

    @property
    def pars(self):
        """策略参数，元组
        :return:
        """
        return self._pars

    @pars.setter
    def pars(self, pars: tuple):
        self.set_pars(pars)

    @property
    def has_pars(self):
        return self.pars is not None

    @property
    def data_freq(self):
        """策略依赖的历史数据频率"""
        return self._data_freq

    @data_freq.setter
    def data_freq(self, data_freq):
        self.set_hist_pars(data_freq=data_freq)

    @property
    def sample_freq(self):  # to be deprecated
        """策略生成的采样频率"""
        warnings.warn('sample_freq is deprecated, use strategy_run_freq instead', DeprecationWarning)
        return self._strategy_run_freq

    @sample_freq.setter
    def sample_freq(self, sample_freq):  # to be deprecated
        warnings.warn('sample_freq is deprecated, use strategy_run_freq instead', DeprecationWarning)
        self.set_hist_pars(strategy_run_freq=sample_freq)

    @property
    def strategy_run_freq(self):
        """策略生成的采样频率"""
        return self._strategy_run_freq

    @strategy_run_freq.setter
    def strategy_run_freq(self, sample_freq):
        self.set_hist_pars(strategy_run_freq=sample_freq)

    @property
    def window_length(self):
        """策略依赖的历史数据窗口长度"""
        return self._window_length

    @window_length.setter
    def window_length(self, window_length):
        self.set_hist_pars(window_length=window_length)

    @property
    def data_types(self):
        """策略依赖的历史数据类型"""
        return self._data_types

    @data_types.setter
    def data_types(self, data_types):
        warnings.warn('data_types is deprecated, use history_data_types instead', DeprecationWarning)
        self.set_hist_pars(strategy_data_types=data_types)

    @property
    def strategy_data_types(self):
        """data_types的别名"""
        return self._data_types

    @strategy_data_types.setter
    def strategy_data_types(self, data_types):
        self.set_hist_pars(strategy_data_types=data_types)

    @property
    def history_data_types(self):
        """data_types的别名"""
        return self._data_types

    @history_data_types.setter
    def history_data_types(self, data_types):
        self.set_hist_pars(strategy_data_types=data_types)

    @property
    def strategy_run_timing(self):
        """ 策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        return self._strategy_run_timing

    @strategy_run_timing.setter
    def strategy_run_timing(self, price_type):
        """ 设置策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        self.set_hist_pars(strategy_run_timing=price_type)

    @property
    def strategy_timing(self):
        """ 策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        return self._strategy_run_timing

    @strategy_timing.setter
    def strategy_timing(self, price_type):
        """ 设置策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        self.set_hist_pars(strategy_run_timing=price_type)

    @property
    def bt_price_type(self):  # to be deprecated
        """策略的运行时机，strategy_run_timing的旧名, to be deprecated"""
        warnings.warn('bt_price_type is deprecated, use strategy_run_timing instead', DeprecationWarning)
        return self._strategy_run_timing

    @bt_price_type.setter
    def bt_price_type(self, price_type):  # to be deprecated
        """ 设置策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        warnings.warn('bt_price_type is deprecated, use strategy_run_timing instead', DeprecationWarning)
        self.set_hist_pars(strategy_run_timing=price_type)

    @property
    def bt_price_types(self):
        """ 策略的运行时机，strategy_run_timing的旧名, to be deprecated"""
        warnings.warn('bt_price_types is deprecated, use strategy_run_timing instead', DeprecationWarning)
        return self._strategy_run_timing

    @bt_price_types.setter
    def bt_price_types(self, price_type):
        """ 设置策略的运行时机，策略运行时机决定了live运行时策略的运行时间，以及回测时策略的价格类型"""
        warnings.warn('bt_price_types is deprecated, use strategy_run_timing instead', DeprecationWarning)
        self.set_hist_pars(strategy_run_timing=price_type)

    @property
    def ref_types(self):
        """ 返回策略的参考数据类型，如果不需要参考数据，返回空列表

        :return:
        """
        return self._reference_data_types

    @ref_types.setter
    def ref_types(self, ref_types):
        """ 设置策略的参考数据类型"""
        self.set_hist_pars(reference_data_types=ref_types)

    @property
    def reference_data_types(self):
        """ ref_types的别名

        Returns
        -------
        list: 策略的参考数据类型，如果不需要参考数据，返回空列表
        """
        return self._reference_data_types

    @reference_data_types.setter
    def reference_data_types(self, ref_types):
        """ 设置策略的参考数据类型"""
        self.set_hist_pars(reference_data_types=ref_types)

    @property
    def use_latest_data_cycle(self):
        """ 是否使用最新的数据周期生成交易信号，默认仅使用截止到上一周期的数据生成交易信号"""
        return self._use_latest_data_cycle

    @use_latest_data_cycle.setter
    def use_latest_data_cycle(self, use_latest_data_cycle):
        """ 设置是否使用最新的数据周期生成交易信号，默认仅使用截止到上一周期的数据生成交易信号"""
        self.set_hist_pars(use_latest_data_cycle=use_latest_data_cycle)

    def __str__(self):
        """打印所有相关信息和主要属性"""
        str1 = f'{type(self)}'
        str2 = f'\nStrategy type: {self.stg_type} at {hex(id(self))}\n'
        str3 = f'\nInformation of the strategy: {self.name}, {self.description}'
        str4 = f'\nOptimization Tag and opti ranges: {self.opt_tag}, {self.par_range}'
        if self._pars is not None:
            str5 = f'\nParameter: {self._pars}\n'
        else:
            str5 = f'\nNo Parameter!\n'
        return ''.join([str1, str2, str3, str4, str5])

    def __repr__(self):
        """ 打印对象的代表信息，strategy对象的代表信息即它的名字，其他的属性都是可变的，唯独name是唯一不变的strategy的id
        因此打印的格式为"Timing(macd)"或类似式样

        Returns
        -------
        str
        """
        str1 = f'{self._stg_type}('
        str2 = f'{self.name})'
        return ''.join([str1, str2])

    def info(self, verbose: bool = True, stg_id: str = None) -> None:
        """打印所有相关信息和主要属性

        Parameters
        ----------
        verbose: bool, default True
            是否打印更多的信息
        stg_id: str, default None
            策略的ID，如果为None，则打印策略的名称，否则打印策略的ID

        Returns
        -------
        None
        """
        from .utilfuncs import adjust_string_length
        from rich import print as rprint
        from shutil import get_terminal_size

        if stg_id is None:
            stg_id = self.name
        term_width = get_terminal_size().columns
        info_width = int(term_width * 0.75) if term_width > 120 else term_width
        key_width = max(24, int(info_width * 0.3))
        value_width = max(7, info_width - key_width)
        stg_type = self.__class__.__bases__[0].__name__
        rprint(f'\n{"Strategy_ID":<{key_width}}{adjust_string_length(str(stg_id), value_width)}')
        rprint('=' * info_width)
        if self._pars is not None:
            rprint(f'{"Strategy Parameter":<{key_width}}{adjust_string_length(str(self._pars), value_width)}')
        else:
            rprint('Strategy Parameter: No Parameter!')
        rprint(f'{"Strategy_type":<{key_width}}{stg_type}\n'
               f'{"Strategy name":<{key_width}}{self.name}\n'
               f'Description\n    {self.description}')
        # 在verbose == True时打印更多的额外信息, 以表格形式打印所有参数职
        if verbose:
            run_type_str = self.strategy_run_freq + ' @ ' + self.strategy_run_timing
            data_type_str = str(self.window_length) + ' ' + self.data_freq
            rprint(
                    f'\n'
                    f'{"Strategy Properties":<{key_width}}{"Values":{value_width}}\n'
                    f'{"-" * info_width}\n'
                    f'{"Param.count":<{key_width}}{self.par_count}\n'
                    f'{"Param.types":<{key_width}}{adjust_string_length(str(self.par_types), value_width)}\n'
                    f'{"Param.range":<{key_width}}{adjust_string_length(str(self.par_range), value_width)}\n'
                    f'{"Run parameters":<{key_width}}{adjust_string_length(run_type_str, value_width)}\n'
                    f'{"Data types":<{key_width}}{adjust_string_length(str(self.history_data_types), value_width)}\n'
                    f'{"Data parameters":<{key_width}}{adjust_string_length(data_type_str, value_width)}'
            )
        print()

    def set_pars(self, pars: (tuple, dict)) -> int:
        """设置策略参数，在设置之前对参数的个数进行检查

        Parameters
        ----------
        pars: tuple or dict of tuples
            需要设置的参数

        Returns
        -------
        int: 1: 设置成功，0: 设置失败
        """
        assert isinstance(pars, (tuple, dict)) or pars is None, \
            f'parameter should be either a tuple or a dict, got {type(pars)} instead'
        if pars is None:
            self._pars = pars
            return 1
        if isinstance(pars, dict):
            return self.set_dict_pars(pars)

        # try correct par types
        pars = self.correct_pars_type(pars)
        # now pars should be tuples
        if self.check_pars(pars):
            self._pars = pars
            return 1
        else:
            return 0

    def check_pars(self, pars: tuple) -> bool:
        """检查pars(一个tuple)是否符合strategy的参数设置"""
        for par, par_type, par_range in zip(pars, self._par_types, self.par_range):
            if not isinstance(pars, tuple):
                raise TypeError(f'Invalid parameter type, expect tuple, got {type(pars)}.')
            if len(pars) != self.par_count:
                # 如果参数的个数不对，那么抛出异常
                raise ValueError(f'Invalid strategy parameter, expect {self.par_count} parameters,'
                                 f' got {len(pars)} ({pars}).')
            if par_type in ['int', 'discr']:
                # 如果par_type是int或者discr，那么par应该是一个整数
                if not isinstance(par, int):
                    raise Exception(f'Invalid parameter, it should be an integer, got {type(par)}')

            if par_type in ['float', 'conti']:
                # 如果par_type是float或者conti，那么par应该是一个浮点数/整数
                if not isinstance(par, (int, float)):
                    raise Exception(f'Invalid parameter, it should be a float or an integer, got {type(par)}')

            if par_type in ['enum']:
                # 如果par_type是enum，那么par应该是par_range中的一个元素
                if par not in par_range:
                    raise ValueError(f'Invalid parameter, {par} should be one of items in ({par_range})')
            else:
                l_bound, u_bound = par_range
                # 如果par_type是int或者float，那么par应该在par_range定义的范围内
                if (par < l_bound) or (par > u_bound):
                    raise ValueError(f'Invalid parameter! {par} is out of range: ({l_bound} - {u_bound})')
        return True

    def correct_pars_type(self, pars: tuple) -> tuple:
        """ 将可能为字符串格式的pars根据type调整为正确的格式

        Parameters
        ----------
        pars: tuple
            策略参数

        Returns
        -------
        pars: tuple
            pars in corrected type
        """

        if len(pars) != self._par_count:
            raise ValueError(f'Invalid strategy parameter, expect {self.par_count} parameters,'
                             f' got {len(pars)} ({pars}).')
        # corrected_pars = [None] * self._par_count
        corrected_pars = [None for _ in range(self._par_count)]
        try:
            for i in range(self._par_count):
                par = pars[i]
                p_type = self.par_types[i]
                if p_type in ['int', 'descr']:
                    corrected_pars[i] = int(par)
                elif p_type in ['float', 'conti']:
                    corrected_pars[i] = float(par)
                else:
                    corrected_pars[i] = par

            return tuple(corrected_pars)

        except Exception as e:
            raise RuntimeError({e})

    def set_dict_pars(self, pars: dict) -> int:
        """ 当策略参数是一个dict的时候，这个dict的key是股票代码，values是每个股票代码的不同策略参数，每个策略参数都应该符合
            检查dict的合法性，并设置参数
        """

        if not isinstance(pars, dict):
            raise TypeError(f'Invalid parameter, expect a dict, got {type(pars)}')
        if len(pars) == 0:
            return self.set_pars(None)
        for key in pars.keys():
            if not isinstance(key, str):
                raise TypeError(f'Invalid parameter, all keys of dict type parameter should be a stock code,'
                                f' got a {type(key)}')
        if all(self.check_pars(par) for par in pars.values()):
            self._pars = pars
            return 1

    def update_pars(self, pars: (tuple, dict)) -> None:
        """ 极简方式更新策略的参数，默认参数格式正确，不检查参数的合规性"""
        self._pars = pars

    def set_opt_tag(self, opt_tag: int) -> int:
        """ 设置策略的优化类型"""
        assert isinstance(opt_tag, int), f'optimization tag should be an integer, got {type(opt_tag)} instead'
        assert 0 <= opt_tag <= 2, f'ValueError, optimization tag should be between 0 and 2, got {opt_tag} instead'
        self._opt_tag = opt_tag
        return opt_tag

    def set_par_range(self, par_range):
        """ 设置策略参数的取值范围"""
        if par_range is None:
            self._par_bounds_or_enums = []
        else:
            self._par_bounds_or_enums = par_range
        return par_range

    def set_hist_pars(self,
                      data_freq: str = None,
                      strategy_run_freq: str = None,
                      window_length: int = None,
                      strategy_data_types: str = None,
                      strategy_run_timing: str = None,
                      reference_data_types: str = None,
                      use_latest_data_cycle: bool = None) -> None:
        """ 设置策略的历史数据回测相关属性

        Parameters
        ----------
        data_freq: str
            数据频率，可以设置为'min', 'd', '2d'等代表回测时的运行或采样频率
        strategy_run_freq: str
            策略运行频率，可以设置为'min', 'd', '2d'等代表回测时的运行或采样频率
        window_length: int
            回测时需要用到的历史数据窗口的长度
        strategy_data_types: str
            需要用到的历史数据类型
        strategy_run_timing: str
            需要用到的历史数据回测价格类型
        reference_data_types: str
            策略运行参考数据类型
        use_latest_data_cycle: bool
            是否使用最近的一个完整的数据周期

        Returns
        -------
        None
        """
        if data_freq is not None:
            assert isinstance(data_freq, str), \
                f'TypeError, sample frequency should be a string, got {type(data_freq)} instead'
            assert data_freq.upper() in TIME_FREQ_STRINGS, f'ValueError, "{data_freq}" is not a valid frequency ' \
                                                           f'string'
            self._data_freq = data_freq
        if strategy_run_freq is not None:
            assert isinstance(strategy_run_freq, str), \
                f'TypeError, sample frequency should be a string, got {type(strategy_run_freq)} instead'
            import re
            if not re.match('[0-9]*(min)$|[0-9]*[dwmqyh]$', strategy_run_freq.lower()):
                raise ValueError(f"{strategy_run_freq} is not a valid frequency string,"
                                 f"sample freq can only be like '10d' or '2w'")
            self._strategy_run_freq = strategy_run_freq
        if window_length is not None:
            assert isinstance(window_length, int), \
                f'TypeError, window length should an integer, got {type(window_length)} instead'
            assert window_length > 0, f'ValueError, "{window_length}" is not a valid window length'
            self._window_length = window_length
        if strategy_data_types is not None:
            if isinstance(strategy_data_types, str):
                strategy_data_types = str_to_list(strategy_data_types, ',')
            assert isinstance(strategy_data_types, list), \
                f'TypeError, data type should be a list, got {type(strategy_data_types)} instead'
            self._data_types = strategy_data_types
        if strategy_run_timing is not None:
            assert isinstance(strategy_run_timing,
                              str), f'Wrong input type, price_type should be a string, got {type(strategy_run_timing)}'
            try:
                pd.to_datetime(strategy_run_timing)
            except Exception as e:
                if strategy_run_timing not in self.AVAILABLE_STG_RUN_TIMING:
                    # TODO: add deprecation warning: 以前定义的bt_price_type的部分允许值已经不再适用，需要更新
                    raise ValueError(f'Invalid price type, should be one of {self.AVAILABLE_STG_RUN_TIMING}, '
                                     f'got {strategy_run_timing} instead')

            self._strategy_run_timing = strategy_run_timing
        if reference_data_types is not None:
            if isinstance(reference_data_types, str):
                reference_data_types = str_to_list(reference_data_types, ',')
            assert isinstance(reference_data_types, list), \
                f'TypeError, reference data types should be a list, got {type(reference_data_types)} instead'
            self._reference_data_types = reference_data_types

        if use_latest_data_cycle is not None:
            assert isinstance(use_latest_data_cycle, bool), \
                f'TypeError, use_latest_data_cycle should be a bool, got {type(use_latest_data_cycle)} instead'
            # warn the user if use_latest_data_cycle is set to True for future functions
            if use_latest_data_cycle:
                if self.strategy_run_timing != 'close':
                    warnings.warn(f'Be cautious of future function! Data required for strategy might '
                                  f'not be available at {self.strategy_run_timing}!', UserWarning)
            self._use_latest_data_cycle = use_latest_data_cycle

    def set_custom_pars(self, **kwargs):
        """如果还有其他策略参数或用户自定义参数，在这里设置"""
        for k, v in zip(kwargs.keys(), kwargs.values()):
            if k in self.__dict__:
                setattr(self, k, v)
            else:
                # deprecated key processing warning
                if k == 'sample_freq':
                    warnings.warn('sample_freq is deprecated, use strategy_fun_freq instead')
                    self.set_hist_pars(strategy_run_freq=v)
                    continue
                if k == 'bt_price_type':
                    warnings.warn('bt_price_type is deprecated, use strategy_run_timing instead')
                    self.set_hist_pars(strategy_run_timing=v)
                    continue
                if k == 'bt_data_type':
                    warnings.warn('bt_data_type is deprecated, use strategy_data_types instead')
                    self.set_hist_pars(strategy_run_timing=v)
                    continue
                if k == 'data_types':
                    warnings.warn('data_types is deprecated, use strategy_data_types instead')
                    self.set_hist_pars(strategy_data_types=v)
                    continue
                if k == 'bt_run_freq':
                    warnings.warn('bt_run_freq is deprecated, use strategy_run_freq instead')
                    self.set_hist_pars(strategy_run_freq=v)
                    continue
                if k == 'proportion_or_quantity':
                    warnings.warn('proportion_or_quantity is deprecated, use max_sel_count instead')
                    self.set_custom_pars(max_sel_count=v)
                    continue
                raise KeyError(f'The strategy does not have property \'{k}\'')

    def generate(self,
                 hist_data: np.ndarray,
                 ref_data: np.ndarray = None,
                 trade_data: np.ndarray = None,  # deprecated since v1.1
                 data_idx=None):
        """策略类的抽象方法，接受输入历史数据并根据参数生成策略输出

        Parameters
        ----------
        hist_data: np.ndarray
            策略运行所需的历史数据，包括价格数据、指标数据等
        ref_data: np.ndarray
            策略运行所需的参考数据，包括价格数据、指标数据等
        trade_data: np.ndarray  # deprecated since v1.1
            策略运行所需的交易数据，包括价格数据、指标数据等  # TODO (v1.1 Deprecate, v1.2 删除)
        data_idx: int or np.ndarray
            策略运行所需的历史数据的索引，用于在历史数据中定位当前运行的数据

        Returns
        -------
        stg_signal: np.ndarray
            策略运行的输出，包括交易信号、交易指令等
        """

        # TODO: for v1.1规划更新
        #  改变trade_data的定义。删除trade_data，允许用户在hist_data和ref_data
        #  中定义持仓量、成交量、成交价等数据，这些数据类型通过特殊的数据类型关键字指定，因此客户在策略定
        #  义时可以通过data_type来灵活地指定所需的数据，不需要专门的trade_data数据类型了。
        #  同时，这样做还有一个好处，可以定义更多更广泛的数据类型，例如交易日日期、星期几、月份、交易时间
        #  等等数据，所有与股票无关的数据都可以定义为reference_data，与股票相关的数据可以定义为
        #  history_data。这样可以大大增加策略的灵活性。
        #  同时为未来允许用户自定义数据类型做好准备。

        # 所有的参数有效性检查都在strategy.ready 以及 operator层面执行
        # 在这里根据data_idx的类型，生成一组交易信号，或者一张完整的交易信号清单
        if data_idx is None:
            # 为了实现stepwise模式运行op，且与qt的realtime模式配合实现实盘运行，是否可以考虑
            #  当data_idx为None时输出None？这样在op运行时可以使用data_idx的值控制是否运行策略？
            # data_idx = -1
            return None

        if isinstance(data_idx, (int, np.int64)):
            # 如果data_idx为整数时，生成单组信号stg_signal
            idx = data_idx
            h_seg = hist_data[idx]
            if ref_data is None:
                ref_seg = None
            else:
                ref_seg = ref_data[idx]
            return self.generate_one(h_seg=h_seg, ref_seg=ref_seg, trade_data=trade_data)
        elif isinstance(data_idx, np.ndarray):  # 如果data_idx为一组整数时，生成完整信号清单 signal_list
            # 一个空的ndarray对象用于存储生成的选股蒙版，全部填充值为np.nan
            signal_count, share_count, date_count, htype_count = hist_data.shape
            sig_list = np.full(shape=(signal_count, share_count), fill_value=np.nan, order='C')
            # 遍历data_idx中的序号，生成N组交易信号，将这些信号填充到清单中对应的位置上
            all_none_list = [None] * signal_count
            hist_data_list = hist_data[data_idx]
            if ref_data is None:
                ref_data_list = all_none_list
            else:
                ref_data_list = ref_data[data_idx]
            if trade_data is None:
                # warnings.warn('trade_data is deprecated, use hist_data and ref_data instead', DeprecationWarning)
                trade_data_list = all_none_list
            else:
                trade_data_list = [trade_data] * signal_count
            # 使用map完成快速遍历填充
            signals = list(map(self.generate_one, hist_data_list, ref_data_list, trade_data_list))
            # 将生成的交易信号填充到清单中对应的位置(data_idx)上
            sig_list[data_idx] = np.array(signals)
            # 将所有分段组合成完整的ndarray
            return sig_list
        else:  # for any other unexpected type of input
            raise TypeError(f'invalid type of data_idx: ({type(data_idx)})')

    @abstractmethod
    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 抽象方法，在各个Strategy类中实现具体操作

        Parameters
        ----------
        h_seg: np.ndarray
            策略运行所需的历史数片段，包括价格数据、指标数据等
        ref_seg: np.ndarray
            策略运行所需的参考数片段，包括价格数据、指标数据等
        trade_data: np.ndarray  depreciated since v1.1
            策略运行所需的交易数据片段，包括价格数据、指标数据等

        Returns
        -------
        stg_signal: np.ndarray
        """
        pass


class GeneralStg(BaseStrategy):
    """ 通用交易策略类，用户可以使用策略输入的历史数据、参考数据和成交数据，自定信号生成规则，生成交易信号。

        策略的实现
        要创建一个通用交易策略，需要创建一个GeneralStg策略类，并重写realize()方法，在其中定义交易信号
        的生成规则，并在策略属性中定义相关的数据类型和策略的运行参数。这样就可以将策略用于实盘或回测了。

        推荐使用下面的方法创建策略类：

            Class ExampleStrategy(GeneralStg):

                def realize(self, h, r=None, t=None, pars=None):

                    # 在这里编写信号生成逻辑
                    ...
                    result = ...
                    # result代表策略的输出

                    return result

        用下面的方法创建一个策略对象：

            example_strategy = ExampleStrategy(pars=<example pars>,
                                               name='example',
                                               description='example strategy',
                                               strategy_data_types='close'
                                               ...
                                               )
            在创建策略类的时候可以定义默认策略参数，详见qteasy的文档——创建交易策略

        GeneralStg通用策略的参数如下，更详细的参数说明、取值范围和含义请参见qteasy文档：

            pars: tuple,            策略参数
            opt_tag: int,           优化标记，策略是否参与参数优化
            name: str,              策略名称
            description: str,       策略简介
            par_count: int,         策略参数个数
            par_types: tuple/list,  策略参数类型
            par_range:              策略参数取值范围
            data_freq: str:         数据频率，用于生成策略输出所需的历史数据的频率
            strategy_run_freq:            策略运行采样频率，即相邻两次策略生成的间隔频率。
            window_length:          历史数据视窗长度。即生成策略输出所需要的历史数据的数量
            strategy_data_types:             静态属性生成策略输出所需要的历史数据的种类，由以逗号分隔的参数字符串组成
            strategy_run_timing:          策略回测时所使用的历史价格种类，可以定义为开盘、收盘、最高、最低价中的一种
            reference_data_types:   参考数据类型，用于生成交易策略的历史数据，但是与具体的股票无关，可用于所有的股票的信号
                                    生成，如指数、宏观经济数据等。

        - 编写策略规则，策略规则是通过realize()函数实现的，关于realize()函数更详细的介绍，请参见qteasy文档。

        realize()的定义：

            def realize(self,
                        h: np.ndarray,
                        r: np.ndarray,
                        t: np.ndarray):

        realize()中获取策略参数：

                par_1, par_2, ..., par_n = self.pars

        realize()中获取历史数据及其他相关数据，关于历史数据的更多详细说明，请参考qteasy文档：

            - h(history): 历史数据片段，shape为(M, N, L)，即：

                - M层：   股票类型

                - N行：   交易日期/时间轴

                - L列：   历史数据类型轴

                在realize()中获取历史数据可以使用切片的方法，获取的数据可用于策略。下面给出几个例子：
                例如：设定：
                        - asset_pool = "000001.SZ, 000002.SZ, 600001.SH"
                        - data_freq = 'd'
                        - window_length = 100
                        - strategy_data_types = "open, high, low, close, pe"

                    以下例子都基于前面给出的参数设定
                    例1，计算每只股票最近的收盘价相对于10天前的涨跌幅：
                        close_last_day = h_seg[:, -1, 3]
                        close_10_day = h_seg[:, -10, 3]
                        rate_10 = (close_last_day / close_10_day) - 1

                    例2, 判断股票最近的收盘价是否大于10日内的最高价：
                        max_10_day = h_seg[:, -10:-1, 1].max(axis=1)
                        close_last_day = h_seg[:, -1, 3]
                        penetrate = close_last_day > max_10_day

                    例3, 获取股票最近10日市盈率的平均值
                        pe_10_days = h_seg[:, -10:-1, 4]
                        avg_pe = pe_10_days.mean(axis=1)

                    例4, 计算股票最近收盘价的10日移动平均价和50日移动平均价
                        close_10_days = h_seg[:, -10:-1, 3]
                        close_50_days = h_seg[:, -50:-1, 3]
                        ma_10 = close_10_days.mean(axis=1)
                        ma_50 = close_10_days.mean(axis=1)

            - r(reference):参考历史数据，默认为None，shape为(N, L)
                与每个个股并不直接相关，但是可以在生成交易信号时用做参考的数据，例如大盘数据，或者
                宏观经济数据等，

                - N行, 交易日期/时间轴

                - L列，参考数据类型轴

                以下是获取参考数据的几个例子：
                    设定：
                        - reference_data_types = "000300.SH.close, 000001.SH.close"

                    例1: 获取最近一天的沪深300收盘价：
                        close_300 = r[-1, 0]
                    例2: 获取五天前的上证指数收盘价:
                        close_SH = r[-5, 1]

            - t(trade):交易历史数据，默认为None，shape为(N, 5)
                最近几次交易的结果数据，2D数据。包含N行5列数据
                如果交易信号不依赖交易结果（只有这样才能批量生成交易信号），t会是None。
                数据的结构如下

                - N行， 股票/证券类型轴
                    每一列代表一只个股或证券

                - 5列,  交易数据类型轴
                    - 0, own_amounts:              当前持有每种股票的份额
                    - 1, available_amounts:        当前可用的每种股票的份额
                    - 2, current_prices:           当前的股票价格
                    - 3, recent_amounts_change:    最近一次成交量（正数表示买入，负数表示卖出）
                    - 4, recent_trade_prices:      最近一次成交价格

                示例：以下是在策略中获取交易数据的几个例子：

                    例1: 获取所有股票最近一次成交的价格和成交量(1D array，没有成交时输出为nan)：
                        volume = t[:, 3]
                        trade_prices = t[:, 4]
                        或者:
                        t = t.T
                        volume = t[3]
                        trade_prices = t[4]
                    例2: 获取当前持有股票数量:
                        own_amounts = t[:, 0]
                        或者:
                        t = t.T
                        own_amounts = t[0]


        realize()方法的输出：
        realize()方法的输出就是交易信号(1D ndarray),shape为(M,)，M为股票的个数，dtype为float
        ndarray中每个元素代表相应股票的操作信号。在不同的信号类型时，交易信号的含义不同：

             signal type   |         PT           |            PS           |       VS
            ------------------------------------------------------------------------------------
                sig > 1    |         N/A          |           N/A           | Buy in sig shares
             1 >= sig > 0  | Buy to sig position  | Buy with sig% of cash   | Buy in sig shares
                sig = 0    | Sell to hold 0 share |        Do Nothing       |     Do Nothing
             0 > sig >= -1 |         N/A          | Sell sig% of share hold |  Sell sig shares
               sig < -1    |         N/A          |           N/A           |  Sell sig shares

        按照前述规则设置好策略的参数，并在realize函数中定义好逻辑规则后，一个策略就可以被添加到Operator
        中，并产生交易信号了。

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

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 通用交易策略的所有策略代码全部都在realize中实现
        """
        return self.realize(h=h_seg, r=ref_seg, t=trade_data)

    @abstractmethod
    def realize(self,
                h,
                r=None,
                t=None):
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

    推荐使用下面的方法创建策略类：

        Class ExampleStrategy(FactorSorter):

            def realize(self, h, r=None, t=None, pars=None):

                # 在这里编写信号生成逻辑
                ...
                factor = ...
                # factor代表策略输出的选股因子，用于进一步选股

                return factor

    用下面的方法创建一个策略对象：

        example_strategy = ExampleStrategy(pars=<example pars>,
                                           name='example',
                                           description='example strategy',
                                           strategy_data_types='close'
                                           ...
                                           )
        在创建策略类的时候可以定义默认策略参数，详见qteasy的文档——创建交易策略

    与通用策略类不同，FactorSorter策略需要几个特殊属性用于确定选股行为（以下*者）
    策略属性如下，更详细的参数说明、取值范围和含义请参见qteasy文档：

        pars:               tuple,  策略参数
        opt_tag:            int,    优化标记，策略是否参与参数优化
        name:               str,    策略名称
        description:        str,    策略简介
        par_count:          int,    策略参数个数
        par_types:          tuple,  策略参数类型
        par_range:          tuple,  策略参数取值范围
        data_freq:          str:    数据频率，用于生成策略输出所需的历史数据的频率
        strategy_run_freq:                策略运行采样频率，即相邻两次策略生成的间隔频率。
        window_length:              历史数据视窗长度。即生成策略输出所需要的历史数据的数量
        strategy_data_types:                 静态属性生成策略输出所需要的历史数据的种类，由以逗号分隔的参数字符串组成
        strategy_run_timing:              策略回测时所使用的历史价格种类，可以定义为开盘、收盘、最高、最低价中的一种
        reference_data_types:       参考数据类型，用于生成交易策略的历史数据，但是与具体的股票无关，可用于所有的股票的信号
                                    生成，如指数、宏观经济数据等。
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

    - 编写策略规则，策略规则是通过realize()函数实现的，关于realize()函数更详细的介绍，请参见qteasy文档。

    realize()的定义：

        def realize(self,
                    h: np.ndarray,
                    r: np.ndarray = None,
                    t: np.ndarray = None,
                    pars: tuple = None
                    ):

    realize()中获取策略参数：

            par_1, par_2, ..., par_n = self.pars

    或者：
            if pars is not None:
                par_1, par_2, ..., par_n = pars
            else:
                par_1, par_2, ..., par_n = self.pars

    realize()中获取历史数据及其他相关数据，关于历史数据的更多详细说明，请参考qteasy文档：

        - h(history): 历史数据片段，shape为(M, N, L)，即：

            - M层：   M种股票的数据

            - N行：   历史数据时间跨度

            - L列：   L种历史数据类型

            在realize()中获取历史数据可以使用切片的方法，获取的数据可用于策略。下面给出几个例子：
            例如：设定：
                    - asset_pool = "000001.SZ, 000002.SZ, 600001.SH"
                    - data_freq = 'd'
                    - window_length = 100
                    - strategy_data_types = "open, high, low, close, pe"

                以下例子都基于前面给出的参数设定
                例1，计算每只股票最近的收盘价相对于10天前的涨跌幅：
                    close_last_day = h[:, -1, 3]
                    close_10_day = h[:, -10, 3]
                    rate_10 = (close_last_day / close_10_day) - 1

                例2, 判断股票最近的收盘价是否大于10日内的最高价：
                    max_10_day = h[:, -10:-1, 1].max(axis=1)
                    close_last_day = h[:, -1, 3]
                    penetrate = close_last_day > max_10_day

                例3, 获取股票最近10日市盈率的平均值
                    pe_10_days = h[:, -10:-1, 4]
                    avg_pe = pe_10_days.mean(axis=1)

                例4, 计算股票最近收盘价的10日移动平均价和50日移动平均价
                    close_10_days = h[:, -10:-1, 3]
                    close_50_days = h[:, -50:-1, 3]
                    ma_10 = close_10_days.mean(axis=1)
                    ma_50 = close_10_days.mean(axis=1)

        - r(reference):参考历史数据，默认为None，shape为(N, L)
            与每个个股并不直接相关，但是可以在生成交易信号时用做参考的数据，例如大盘数据，或者
            宏观经济数据等，

            - N行, 交易日期/时间轴

            - L列，参考数据类型轴

            以下是获取参考数据的几个例子：
                设定：
                    - reference_data_types = "close-000300.SH, close-000001.SH"

                例1: 获取最近一天的沪深300收盘价：
                    close_300 = r[-1, 0]
                例2: 获取五天前的上证指数收盘价:
                    close_SH = r[-5, 1]

        - t(trade):交易历史数据，默认为None，shape为(N, 5)
            最近几次交易的结果数据，2D数据。包含N行5列数据
            如果交易信号不依赖交易结果（只有这样才能批量生成交易信号），t会是None。
            数据的结构如下

            - N行， 股票/证券类型轴
                每一列代表一只个股或证券

            - 5列,  交易数据类型轴
                - 0, own_amounts:              当前持有每种股票的份额
                - 1, available_amounts:        当前可用的每种股票的份额
                - 2, current_prices:           当前的交易价格
                - 3, recent_amounts_change:    最近一次成交量（正数表示买入，负数表示卖出）
                - 4, recent_trade_prices:      最近一次成交价格

            示例：以下是在策略中获取交易数据的几个例子：

                例1: 获取所有股票最近一次成交的价格和成交量(1D array，没有成交时输出为nan)：
                    volume = t[:, 3]
                    trade_prices = t[:, 4]
                    或者:
                    t = t.T
                    volume = t[3]
                    trade_prices = t[4]
                例2: 获取当前持有股票数量:
                    own_amounts = t[:, 0]
                    或者:
                    t = t.T
                    own_amounts = t[0]

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

    在使用FactorSorter策略类时，建议将信号类型设置为PT,此时策略根据选股因子生成的交易信号含义如下:

         signal type   |         PT prefered type     |
        -----------------------------------------------
            sig > 1    |              N/A             |
         1 >= sig > 0  |      Buy to sig position     |
            sig = 0    |      Sell to hold 0 share    |
         0 > sig >= -1 |             N/A              |
           sig < -1    |             N/A              |
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

    def info(self, verbose: bool = True, stg_id=None):
        """ display more FactorSorter-specific properties

        Parameters
        ----------
        verbose: bool
            if True, display more properties
        stg_id: str
            strategy id, if None, use self.name
        """
        from .utilfuncs import adjust_string_length
        from rich import print as rprint
        from shutil import get_terminal_size

        term_width = get_terminal_size().columns
        info_width = int(term_width * 0.75) if term_width > 120 else term_width
        key_width = max(24, int(info_width * 0.3))
        value_width = max(7, info_width - key_width)

        super().info(verbose=verbose, stg_id=stg_id)
        if self.max_sel_count > 1:
            rprint(f'{"Max select count":<{key_width}}{int(self.max_sel_count)}')
        else:
            rprint(f'{"Max select count":<{key_width}}{self.max_sel_count:.1%}')
        rprint(f'{"Sort Ascending":<{key_width}}{self.sort_ascending}\n'
               f'{"Weighting":<{key_width}}{adjust_string_length(self.weighting, value_width)}\n'
               f'{"Filter Condition":<{key_width}}{adjust_string_length(self.condition, value_width)}\n'
               f'{"Filter ubound":<{key_width}}{self.ubound}\n'
               f'{"Filter lbound":<{key_width}}{self.lbound}')

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """处理从_realize()方法传递过来的选股因子

        选出符合condition的因子，并将这些因子排序，根据次序确定所有因子相应股票的选股权重
        将选股权重传递到generate()方法中，生成最终的选股交易信号

        Parameters
        ----------
        h_seg: np.ndarray
            一个三维数组，shape为(M, N, L)，代表M个股票在N个交易时间内的L种历史数据
        ref_seg: np.ndarray
            一个二维数组，shape为(N, L)，代表N个交易时间内的L种参考数据
        trade_data: np.ndarray
            一个二维数组，shape为(N,5)，代表N交易时间内的五种交易相关数据

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

        share_count = h_seg.shape[0]
        if pct < 1:
            # pct 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            pct = int(share_count * pct)
        else:  # pct 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            pct = int(pct)
        if pct < 1:
            pct = 1
        # 历史数据片段必须是ndarray对象，否则无法进行
        assert isinstance(h_seg, np.ndarray), \
            f'TypeError: expect np.ndarray as history segment, got {type(h_seg)} instead'

        factors = self.realize(h=h_seg, r=ref_seg, t=trade_data)
        # factors必须是一维向量，如果因子是二维向量，允许shape为(N, 1)型，此时将其转换为一维向量，否则报错
        if factors.ndim == 2:
            factors = factors.flatten()
        # if len(factors) != share_count:
        #     raise ValueError(f'invalid length of factors, expect {share_count}, got {len(factors)} instead')
        chosen = np.zeros_like(factors)
        # 筛选出不符合要求的指标，将他们设置为nan值
        if condition == 'any':
            pass
        elif condition == 'greater':
            factors[np.where(factors < ubound)] = np.nan
        elif condition == 'less':
            factors[np.where(factors > lbound)] = np.nan
        elif condition == 'between':
            factors[np.where((factors < lbound) & (factors > ubound))] = np.nan
        elif condition == 'not_between':
            factors[np.where(np.logical_and(factors > lbound, factors < ubound))] = np.nan
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
    def realize(self,
                h,
                r=None,
                t=None):
        """ h, r, 和 t 都是用于生成交易信号的窗口数据，根据这一段窗口数据
            生成一条交易信号
        """
        pass


class RuleIterator(BaseStrategy):
    """ 规则迭代策略类。这一类策略不考虑每一只股票的区别，将同一套规则同时迭代应用到所有的股票上。

    这类策略要求用户针对投资组合中的一个投资品种设计交易规则，在realize()方法定义该交易规则，
    策略可以把同样的交易规则应用推广到投资组合中的所有投资品种上，同时可以采用不同的策略参数。

    Properties
    ----------
    pars:               tuple,
        策略参数
    opt_tag:            int,
        优化标记，策略是否参与参数优化
    name:               str,
        策略名称
    description:        str,
        策略简介
    par_count:          int,
        策略参数个数
    par_types:          tuple,
        策略参数类型
    par_range:          tuple,
        策略参数取值范围
    data_freq:          str:
        数据频率，用于生成策略输出所需的历史数据的频率
    strategy_run_freq:
        策略运行采样频率，即相邻两次策略生成的间隔频率。
    window_length:
        历史数据视窗长度。即生成策略输出所需要的历史数据的数量
    strategy_data_types:
        静态属性生成策略输出所需要的历史数据的种类，由以逗号分隔的参数字符串组成
    strategy_run_timing:
        策略回测时所使用的历史价格种类，可以定义为开盘、收盘、最高、最低价中的一种
    reference_data_types:
        参考数据类型，用于生成交易策略的历史数据，但是与具体的股票无关，可用于所有
        的股票的信号生成，如指数、宏观经济数据等。

    Examples
    --------
        Class ExampleStrategy(RuleIterator):

            def realize(self, h, r=None, t=None, pars=None):

                # 在这里编写信号生成逻辑
                ...
                result = ...
                # result代表策略的输出

                return result

    用下面的方法创建一个策略对象：

        example_strategy = ExampleStrategy(pars=<example pars>,
                                           name='example',
                                           description='example strategy',
                                           strategy_data_types='close'
                                           ...
                                           )
        在创建策略类的时候可以定义默认策略参数，详见qteasy的文档——创建交易策略

    - 编写策略规则，策略规则是通过realize()函数实现的，关于realize()函数更详细的介绍，请参见qteasy文档。

    realize()的定义：

        def realize(self,
                    h: np.ndarray,
                    r: np.ndarray = None,
                    t: np.ndarray = None,
                    pars: tuple = None
                    ):

    realize()中获取策略参数：

            par_1, par_2, ..., par_n = self.pars

    realize()中获取历史数据及其他相关数据，关于历史数据的更多详细说明，请参考qteasy文档：
        :input:
        h: 历史数据，一个2D numpy数组，包含一只股票在一个时间窗口内的所有类型的历史数据，
            h 的shape为(N, L)，含义如下：

            - N行：交易时间轴
            - L列： 历史数据类型轴

            示例：
                以下例子都基于前面给出的参数设定
                例1，计算最近的收盘价相对于10天前的涨跌幅：
                    close_last_day = h_seg[-1, 3]
                    close_10_day = h_seg[-10, 3]
                    rate_10 = (close_last_day / close_10_day) - 1

                例2, 判断股票最近的收盘价是否大于10日内的最高价：
                    max_10_day = h_seg[-10:-1, 1].max(axis=1)
                    close_last_day = h_seg[-1, 3]
                    penetrate = close_last_day > max_10_day

                例3, 获取股票最近10日市盈率的平均值
                    pe_10_days = h_seg[-10:-1, 4]
                    avg_pe = pe_10_days.mean(axis=1)

                例4, 计算股票最近收盘价的10日移动平均价和50日移动平均价
                    close_10_days = h_seg[-10:-1, 3]
                    close_50_days = h_seg[-50:-1, 3]
                    ma_10 = close_10_days.mean(axis=1)
                    ma_50 = close_10_days.mean(axis=1)

        - r(reference):参考历史数据，默认为None，shape为(N, L)
            与每个个股并不直接相关，但是可以在生成交易信号时用做参考的数据，例如大盘数据，或者
            宏观经济数据等，

            - N行, 交易日期/时间轴

            - L列，参考数据类型轴

            以下是获取参考数据的几个例子：
                设定：
                    - reference_data_types = "000300.SH.close, 000001.SH.close"

                例1: 获取最近一天的沪深300收盘价：
                    close_300 = r[-1, 0]
                例2: 获取五天前的上证指数收盘价:
                    close_SH = r[-5, 1]

        - t(trade):交易历史数据，默认为None，shape为(N, 5)
            最近几次交易的结果数据，2D数据。包含N行5列数据
            如果交易信号不依赖交易结果（只有这样才能批量生成交易信号），t会是None。
            数据的结构如下

            - N行， 股票/证券类型轴
                每一列代表一只个股或证券

            - 5列,  交易数据类型轴
                - 0, own_amounts:              当前持有每种股票的份额
                - 1, available_amounts:        当前可用的每种股票的份额
                - 2, current_prices:           当前的交易价格
                - 3, recent_amounts_change:    最近一次成交量（正数表示买入，负数表示卖出）
                - 4, recent_trade_prices:      最近一次成交价格

            示例：以下是在策略中获取交易数据的几个例子：

                例1: 获取所有股票最近一次成交的价格和成交量(1D array，没有成交时输出为nan)：
                    volume = t[:, 3]
                    trade_prices = t[:, 4]
                    或者:
                    t = t.T
                    volume = t[3]
                    trade_prices = t[4]
                例2: 获取当前持有股票数量:
                    own_amounts = t[:, 0]
                    或者:
                    t = t.T
                    own_amounts = t[0]

        :output
        signals: 一个代表交易信号的数字，dtype为float

    realize()方法的输出：
    realize()方法的输出就是交易信号，该交易信号是一个数字，策略会将其推广到整个投资组合：

        def realize(): -> int

        投资组合： [share1, share2, share3, share4]
                    |        |       |       |
                 [ int1,    int2,   int3,   int4] -> np.array[ int1,    int2,   int3,   int4]

    在不同的信号类型下，信号的含义不同。

         signal type   |         PT           |            PS           |       VS
        ------------------------------------------------------------------------------------
            sig > 1    |         N/A          |           N/A           | Buy in sig shares
         1 >= sig > 0  | Buy to sig position  | Buy with sig% of cash   | Buy in sig shares
            sig = 0    | Sell to hold 0 share |        Do Nothing       |     Do Nothing
         0 > sig >= -1 |         N/A          | Sell sig% of share hold |  Sell sig shares
           sig < -1    |         N/A          |           N/A           |  Sell sig shares

    按照前述规则设置好策略的参数，并在realize函数中定义好逻辑规则后，一个策略就可以被添加到Operator
    中，并产生交易信号了。

    关于Strategy类的更详细说明，请参见qteasy的文档。
    RuleIterator 策略类继承了交易策略基类

    """
    __mataclass__ = ABCMeta

    def __init__(self,
                 name: str = 'Rule-Iterator',
                 description: str = 'description of rule iterator strategy',
                 **kwargs):
        super().__init__(name=name,
                         description=description,
                         stg_type='RULE-ITER',
                         **kwargs)

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 中间构造函数，将历史数据模块传递过来的单只股票历史数据去除nan值，并进行滚动展开
            对于滚动展开后的矩阵，使用map函数循环调用generate_one函数生成整个历史区间的
            循环回测结果（结果为1维向量， 长度为hist_length - _window_length + 1）

        Parameters
        ----------
        h_seg: np.ndarray
            历史数据片段, 二维数组，shape为(N, L)，其中N为历史数据长度，L为历史数据类型轴
        ref_seg: np.ndarray
            参考数据片段, 二维数组，shape为(N, L)，其中N为历史数据长度，L为参考数据类型轴
        trade_data: np.ndarray
            交易数据片段, 二维数组，shape为(N, 5)，其中N为历史数据长度，5为交易数据类型轴

        Returns
        -------
        signal: np.ndarray
            一维向量。根据策略，在历史上产生的仓位信号或交易信号，具体信号的含义取决于策略类型
        """
        # 生成iterators, 将参数送入realize_no_nan中逐个迭代后返回结果
        share_count, window_length, hdata_count = h_seg.shape
        ref_seg_iter = (ref_seg for i in range(share_count))
        if trade_data is None:
            trade_data_iter = (None for i in range(share_count))
        else:
            trade_data_iter = trade_data
        pars = self.pars
        if isinstance(pars, dict):
            pars_iter = pars.values()
        else:
            pars_iter = (pars for i in range(share_count))
        signal = np.array(list(map(self.realize_no_nan,
                                   pars_iter,
                                   h_seg,
                                   ref_seg_iter,
                                   trade_data_iter)))

        return signal

    def realize_no_nan(self,
                       params,
                       h_seg,
                       ref_seg,
                       trade_data):
        """ 生成没有nan的数据，传递到realize中并获取结果返回
        """
        # 仅针对非nan值计算，忽略股票停牌时期
        hist_nonan = h_seg[~np.isnan(h_seg[:, 0])]
        if ref_seg is None:
            ref_nonan = None
        else:
            ref_nonan = ref_seg[~np.isnan(ref_seg[:, 0])]

        return self.realize(h=hist_nonan,
                            r=ref_nonan,
                            t=trade_data,
                            pars=params)

    @abstractmethod
    def realize(self,
                h,
                r=None,
                t=None,
                pars=None):
        """ h_seg和ref_seg都是用于生成交易信号的一段窗口数据，根据这一段窗口数据
            生成一个股票的独立交易信号，同样的规则会被复制到其他股票
        """
        pass
