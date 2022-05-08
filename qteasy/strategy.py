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
from numpy.lib.stride_tricks import as_strided
from abc import abstractmethod, ABCMeta
from .utilfuncs import str_to_list
from .utilfuncs import TIME_FREQ_STRINGS


class BaseStrategy:
    """ 量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的策略类调用

        类属性定义了策略类型、策略名称、策略关键属性的数量、类型和取值范围等
        所有的策略类都有一个generate()方法，这个方法是策略类的主入口方法，这个方法接受一组历史数据(np.ndarray对象)从历史数据中提取出
        有用的信息，并生成用于投资的操作或交易信号。
    """
    __mataclass__ = ABCMeta

    AVAILABLE_BT_PRICE_TYPES = ['open', 'high', 'low', 'close',
                                'buy1', 'buy2', 'buy3', 'buy4', 'buy5',
                                'sell1', 'sell2', 'sell3', 'sell4', 'sell5']

    def __init__(self,
                 pars: tuple = (),
                 opt_tag: int = 0,
                 stg_type: str = 'strategy type',
                 stg_name: str = 'strategy name',
                 stg_text: str = 'intro text of strategy',
                 par_count: int = 0,
                 par_types: [list, str] = '',
                 par_bounds_or_enums: [list, tuple] = (),
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: [str, list] = 'close',
                 bt_price_type: str = 'close',
                 reference_data_types: [str, list] = ''):
        """ 初始化策略，赋予策略基本属性，包括策略的参数及其他控制属性

        input:
            :param pars: tuple,             策略参数, 动态参数
            :param opt_tag: int,            0: 参加优化，1: 不参加优化
            :param stg_type: str,           策略类型，可取值'ROLLING TIMING', 'SELECTING', 'SIMPLE TIMNG'等
            :param stg_name: str,           策略名称，在创建继承具体类时赋予该类
            :param stg_text: str,           策略简介，类似于docstring，简单介绍该类的策略内容
            :param par_count: int,          策略参数个数
            :param par_types: int,          策略参数类型，注意这里并不是数据类型，而是策略参数空间数轴的类型，包含三种类型：
                                            1, 'discr': 离散型参数，通常数据类型为int
                                            2, 'conti': 连续型参数，通常数据类型为float
                                            3, 'enum': 枚举型参数，数据类型不限，可以为其他类型如str或tuple等
            :param par_bounds_or_enums:     策略参数取值范围，该参数供优化器使用，用于产生正确的参数空间并用于优化
            :param data_freq: str:          静态属性，依赖的数据频率，用于生成策略输出所需的历史数据的频率，取值范围包括：
                                            1, 'TICK'/'tick'/'t':
                                            2, 'MIN'/'min':
                                            3, 'H'/'h':
                                            4, 'D'/'d':
                                            5, 'W'/'w':
                                            6, 'M'/'m':
                                            7, 'Q'/'q':
                                            8, 'Y'/'y':
            :param sample_freq:             静态属性，策略生成时的采样频率，即相邻两次策略生成的间隔频率，可选参数与data_freq
                                            一样，但是不能高于数据频率。
            :param window_length:           静态属性，历史数据视窗长度。即生成策略输出所需要的历史数据的数量
            :param data_types:              静态属性生成策略输出所需要的历史数据的种类，由以逗号分隔的参数字符串组成，可选的参数
                                            字符串包括：
                                            1, 'open'
                                            2, 'high'
                                            3, 'low'
                                            4, 'close'
                                            5, 'volume'
                                            6, 'eps'
                                            7, ...
            :param bt_price_type:           静态属性，策略回测时所使用的历史价格种类，可以定义为开盘、收盘、最高、最低价，也可以设置
                                            为五档交易价格中的某一个价格，根据交易当时的时间戳动态确定具体的交易价格
        """
        self._pars = pars  # 策略的参数，动态属性，可以直接赋值（通过set_pars函数赋值）
        self._opt_tag = opt_tag  # 策略的优化标记，
        self._stg_type = stg_type  # 策略类型
        self._stg_name = stg_name  # 策略的名称
        self._stg_text = stg_text  # 策略的描述文字
        self._par_count = par_count  # 策略参数的元素个数
        self._par_types = par_types  # 策略参数的类型，可选类型'discr/conti/enum'
        # TODO: parameter validation should take place here
        if not isinstance(par_count, int):
            raise TypeError(f'parameter count (par_count) should be a integer, got {type(par_count)} instead.')
        if pars is not None:
            assert isinstance(pars, (tuple, list, dict))

        if par_types is None:
            par_types = []
            assert par_count == 0, f'parameter count (par_count) should be 0 when parameter type is None'

        if not isinstance(par_types, (str, list)):
            raise TypeError(f'parameter types (par_types) should be a string or list of strings, '
                            f'got {type(par_types)} instead')
        if isinstance(par_types, str):
            par_types = str_to_list(par_types)

        if not par_count == len(par_types):
            raise KeyError(f'parameter count ({par_count}) does not fit parameter types, '
                           f'which imply {len(par_types)} parameters')

        if par_bounds_or_enums is None:  # 策略参数的取值范围或取值列表，如果是数值型，可以取上下限，其他类型的数据必须为枚举列表
            assert par_count == 0, f'parameter count (par_count) should be 0 when parameter bounds are None'
            self._par_bounds_or_enums = []
        else:
            assert isinstance(par_bounds_or_enums, (list, tuple))
            self._par_bounds_or_enums = par_bounds_or_enums
        if not par_count == len(self._par_bounds_or_enums):
            raise KeyError(f'parameter count ({par_count}) does not fit parameter bounds or enums, '
                           f'which imply {len(par_types)} parameters')

        # 依赖的历史数据频率
        self._data_freq = data_freq
        # 策略生成采样频率，即策略操作信号的生成频率
        self._sample_freq = sample_freq
        # 表示历史数据窗口的长度，生成策略的一次操作所依赖的历史数据的数量
        self._window_length = window_length
        if isinstance(data_types, str):
            data_types = str_to_list(data_types, ',')
        assert isinstance(data_types, list), f'TypeError, data type should be a list, got {type(data_types)} instead'
        self._data_types = data_types
        self._bt_price_type = None
        self.set_hist_pars(bt_price_type=bt_price_type)
        if isinstance(reference_data_types, str):
            reference_data_types = str_to_list(reference_data_types, ',')
        self._reference_data_types = reference_data_types

    @property
    def stg_type(self):
        """策略类型，策略类型决定了策略的实现方式，目前支持的策略类型共有三种：'ROLLING TIMING', 'SELECTING', 'SIMPLE TIMNG'"""
        return self._stg_type

    @property
    def stg_name(self):
        """策略名称，打印策略信息的时候策略名称会被打印出来"""
        return self._stg_name

    @stg_name.setter
    def stg_name(self, stg_name: str):
        self._stg_name = stg_name

    @property
    def stg_text(self):
        """策略说明文本，对策略的实现方法和功能进行简要介绍"""
        return self._stg_text

    @stg_text.setter
    def stg_text(self, stg_text: str):
        self._stg_text = stg_text

    @property
    def par_count(self):
        """策略的参数数量"""
        return self._par_count

    @par_count.setter
    def par_count(self, par_count: int):
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

        :param par_types:

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
    def par_boes(self):
        """策略的参数取值范围，用来定义参数空间用于参数优化"""
        return self._par_bounds_or_enums

    @par_boes.setter
    def par_boes(self, boes: list):
        self.set_par_boes(par_boes=boes)

    @property
    def opt_tag(self):
        """策略的优化类型"""
        return self._opt_tag

    @opt_tag.setter
    def opt_tag(self, opt_tag):
        self.set_opt_tag(opt_tag=opt_tag)

    @property
    def pars(self):
        """策略参数，元组"""
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
    def sample_freq(self):
        """策略生成的采样频率"""
        return self._sample_freq

    @sample_freq.setter
    def sample_freq(self, sample_freq):
        self.set_hist_pars(sample_freq=sample_freq)

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
        self.set_hist_pars(data_types=data_types)

    @property
    def history_data_types(self):
        """data_types的别名"""
        return self._data_types

    @history_data_types.setter
    def history_data_types(self, data_types):
        self.set_hist_pars(data_types=data_types)

    @property
    def bt_price_type(self):
        """策略回测时所使用的价格类型"""
        return self._bt_price_type

    @bt_price_type.setter
    def bt_price_type(self, price_type):
        """ 设置策略回测室所使用的价格类型"""
        self.set_hist_pars(bt_price_type=price_type)

    @property
    def bt_price_types(self):
        """策略回测时所使用的价格类型，bt_price_type的别名"""
        return self._bt_price_type

    @bt_price_types.setter
    def bt_price_types(self, price_type):
        """ 设置策略回测室所使用的价格类型"""
        self.set_hist_pars(bt_price_type=price_type)

    @property
    def reference_data_types(self):
        """ 返回策略的参考数据类型，如果不需要参考数据，返回空列表

        :return:
        """
        return self._reference_data_types

    @reference_data_types.setter
    def reference_data_types(self, ref_types):
        """ 设置策略的参考数据类型"""
        self.set_hist_pars(reference_data_types=ref_types)

    def __str__(self):
        """打印所有相关信息和主要属性"""
        str1 = f'{type(self)}'
        str2 = f'\nStrategy type: {self.stg_type} at {hex(id(self))}\n'
        str3 = f'\nInformation of the strategy: {self.stg_name}, {self.stg_text}'
        str4 = f'\nOptimization Tag and opti ranges: {self.opt_tag}, {self.par_boes}'
        if self._pars is not None:
            str5 = f'\nParameter: {self._pars}\n'
        else:
            str5 = f'\nNo Parameter!\n'
        return ''.join([str1, str2, str3, str4, str5])

    def __repr__(self):
        """ 打印对象的代表信息，strategy对象的代表信息即它的名字，其他的属性都是可变的，唯独name是唯一不变的strategy的id
        因此打印的格式为"Timing(macd)"或类似式样

        :return:
        """
        str1 = f'{self._stg_type}('
        str2 = f'{self.stg_name})'
        return ''.join([str1, str2])

    def info(self, verbose: bool = False):
        """打印所有相关信息和主要属性"""
        print(f'{type(self)} at {hex(id(self))}\nStrategy type: {self.stg_name}')
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_boes)
        if self._pars is not None:
            print('Parameter Loaded:', type(self._pars), self._pars)
        else:
            print('No Parameter!')
        # 在verbose == True时打印更多的额外信息
        if verbose:
            print('Information of the strategy:\n', self.stg_name, self.stg_text)

    def set_pars(self, pars: (tuple, dict)) -> int:
        """设置策略参数，在设置之前对参数的个数进行检查

        input:
            :param: type items: tuple，需要设置的参数
        return:
            int: 1: 设置成功，0: 设置失败
        """
        assert isinstance(pars, (tuple, dict)) or pars is None, \
            f'parameter should be either a tuple or a dict, got {type(pars)} instead'
        if pars is None:
            self._pars = pars
            return 1
        if len(pars) == self.par_count or isinstance(pars, dict):
            self._pars = pars
            return 1
        raise ValueError(f'parameter setting error in set_pars() method of \n{self}\nexpected par count: '
                         f'{self.par_count}, got {pars}')

    def set_opt_tag(self, opt_tag: int) -> int:
        """ 设置策略的优化类型

        input"
            :param opt_tag: int，0：不参加优化，1：参加优化
        :return:
        """
        assert isinstance(opt_tag, int), f'optimization tag should be an integer, got {type(opt_tag)} instead'
        assert 0 <= opt_tag <= 2, f'ValueError, optimization tag should be between 0 and 2, got {opt_tag} instead'
        self._opt_tag = opt_tag
        return opt_tag

    def set_par_boes(self, par_boes):
        """ 设置策略参数的取值范围

        input:
            :param par_boes: 策略的参数取值范围
        :return:
        """
        if par_boes is None:
            self._par_bounds_or_enums = []
        else:
            self._par_bounds_or_enums = par_boes
        return par_boes

    def set_hist_pars(self,
                      data_freq=None,
                      sample_freq=None,
                      window_length=None,
                      data_types=None,
                      bt_price_type=None,
                      reference_data_types=None):
        """ 设置策略的历史数据回测相关属性

        :param data_freq: str,
        :param sample_freq: str, 可以设置为'min', 'd', '2d'等代表回测时的运行或采样频率
        :param window_length: int，表示回测时需要用到的历史数据深度
        :param data_types: str，表示需要用到的历史数据类型
        :param bt_price_type: str, 需要用到的历史数据回测价格类型
        :param reference_data_types: str, 策略运行参考数据类型
        :return: None
        """
        if data_freq is not None:
            assert isinstance(data_freq, str), \
                f'TypeError, sample frequency should be a string, got {type(data_freq)} instead'
            assert data_freq.upper() in TIME_FREQ_STRINGS, f'ValueError, "{data_freq}" is not a valid frequency ' \
                                                           f'string'
            self._data_freq = data_freq
        if sample_freq is not None:
            assert isinstance(sample_freq, str), \
                f'TypeError, sample frequency should be a string, got {type(sample_freq)} instead'
            import re
            if not re.match('[0-9]*(min)$|[0-9]*[dwmqyh]$', sample_freq.lower()):
                raise ValueError(f"{sample_freq} is not a valid frequency string,"
                                 f"sample freq can only be like '10d' or '2w'")
            self._sample_freq = sample_freq
        if window_length is not None:
            assert isinstance(window_length, int), \
                f'TypeError, window length should an integer, got {type(window_length)} instead'
            assert window_length > 0, f'ValueError, "{window_length}" is not a valid window length'
            self._window_length = window_length
        if data_types is not None:
            if isinstance(data_types, str):
                data_types = str_to_list(data_types, ',')
            assert isinstance(data_types, list), \
                f'TypeError, data type should be a list, got {type(data_types)} instead'
            self._data_types = data_types
        if bt_price_type is not None:
            assert isinstance(bt_price_type,
                              str), f'Wrong input type, price_type should be a string, got {type(bt_price_type)}'
            assert bt_price_type in self.AVAILABLE_BT_PRICE_TYPES, f'Wrong input type, {bt_price_type} is not a valid ' \
                                                                   f'price type'
            self._bt_price_type = bt_price_type
        if reference_data_types is not None:
            if isinstance(data_types, str):
                reference_data_types = str_to_list(reference_data_types, ',')
            assert isinstance(reference_data_types, list), \
                f'TypeError, data type should be a list, got {type(reference_data_types)} instead'
            self._reference_data_types = reference_data_types

    def set_custom_pars(self, **kwargs):
        """如果还有其他策略参数或用户自定义参数，在这里设置"""
        for k, v in zip(kwargs.keys(), kwargs.values()):
            if k in self.__dict__:
                setattr(self, k, v)
            else:
                raise KeyError(f'The strategy does not have property \'{k}\'')

    def generate(self,
                 hist_data: np.ndarray,
                 ref_data: np.ndarray = None,
                 trade_data: np.ndarray = None,
                 data_idx=None):
        """策略类的抽象方法，接受输入历史数据并根据参数生成策略输出

        :param hist_data:
        :param ref_data:
        :param trade_data:
        :param data_idx:
        """
        # 所有的参数有效性检查都在strategy.ready 以及 operator层面执行
        # 在这里使用map或apply_along_axis快速组装realize()的结果，形成一张交易信号清单
        if isinstance(data_idx, (int, np.int)):
            # 生成单组信号
            idx = data_idx
            h_seg = hist_data[idx]
            ref_seg = ref_data[idx]
            return self.generate_one(h_seg=h_seg, ref_seg=ref_seg, trade_data=trade_data)
        elif isinstance(data_idx, np.ndarray):
            # 生成信号清单
            # 一个空的ndarray对象用于存储生成的选股蒙版，全部填充值为np.nan
            share_count, date_count, htype_count = hist_data[0].shape
            signal_count = len(data_idx)
            sig_list = np.full(shape=(date_count, share_count), fill_value=np.nan, order='C')
            # 遍历data_idx中的序号，生成N组交易信号，将这些信号填充到清单中对应的位置上
            hist_data_list = hist_data[data_idx]
            ref_data_list = ref_data[data_idx]
            trade_data_list = [trade_data] * signal_count
            # 使用map完成快速遍历填充
            signals = list(map(self.generate_one, hist_data_list, ref_data_list, trade_data_list))
            sig_list[data_idx] = np.array(signals)
            # 将所有分段组合成完整的ndarray
            return sig_list[self.window_length:]

    @abstractmethod
    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 抽象方法，在各个Strategy类中实现具体操作

        :param h_seg:
        :param ref_seg:
        :param trade_data:
        :return:
        """
        pass


class RuleIterator(BaseStrategy):
    """ 规则横向分配策略类。这一类策略不考虑每一只股票的区别，将同一套规则同时套用到所有的股票上。

        Rolling Timing择时策略是通过realize()函数来实现的。一个继承了Rolling_Timing类的对象，必须具体实现realize()方法，在
        Rolling_Timing对象中，这是个抽象方法。这个方法接受两个参数，一个是generate_over()函数传送过来的window_history数据，另一个
        是策略参数，策略通过传入的参数，利用window_history历史数据进行某种特定计算，最后生成一个-1～1之间的浮点数，这个数字就是在某一
        时间点的策略输出。

        Rolling_Timing类会自动把上述特定计算算法滚动应用到整个历史数据区间，并且推广到所有的个股中。

        在实现具体的Rolling_Timing类时，必须且仅需要实现两个方法：__init__()方法和_realize()方法，且两个方法的实现都需要遵循一定的规则：

        * __init__()方法的实现：

        __init__()方法定义了该策略的最基本参数，这些参数与策略的使用息息相关，而且推荐使用"super().__init__()"的形式设置这些参数，这些参数
        包括：
            stg_id:
            stg_text:
            par_count:
            par_types:
            par_boes:
            data_freq:
            sample_freq:
            window_length:
            data_types:

        * _realize()方法的实现：

        _realize()方法确定了策略的具体实现方式，要注意_realize()方法需要有两个参数：

            hist_data: ndarray
            params: tuple

        在_realize()方法中用户可以以任何可能的方法使用hist_data，但必须知道hist_data的结构，同时确保返回值为一个浮点数，且返回值在-1～1
        之间（包括-1和+1）。

    """
    __mataclass__ = ABCMeta

    def __init__(self,
                 pars: tuple = None,
                 stg_name: str = 'NEW-RTMG',
                 stg_text: str = 'intro text of rolling timing strategy',
                 **kwargs):
        super().__init__(pars=pars,
                         stg_name=stg_name,
                         stg_text=stg_text,
                         stg_type='R-TIMING',
                         **kwargs)

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 中间构造函数，将历史数据模块传递过来的单只股票历史数据去除nan值，并进行滚动展开
            对于滚动展开后的矩阵，使用map函数循环调用generate_one函数生成整个历史区间的
            循环回测结果（结果为1维向量， 长度为hist_length - _window_length + 1）

        input:
            :param h_seg:
            :param ref_seg:
            :param trade_data:
        :return:
            np.ndarray: 一维向量。根据策略，在历史上产生的多空信号，1表示多头、0或-1表示空头
        """
        # 生成iterators, 将参数送入realize_no_nan中逐个迭代后返回结果
        share_count, window_length, hdata_count = h_seg.shape
        ref_seg_iter = (ref_seg for i in range(share_count))
        trade_data_iter = (trade_data for i in range(share_count))
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
        ref_nonan = ref_seg[~np.isnan(ref_seg[:, 0])]

        try:
            return self.realize(params=params,
                                h_seg=hist_nonan,
                                ref_seg=ref_nonan,
                                trade_data=trade_data)
        except Exception:
            return np.nan

    @abstractmethod
    def realize(self,
                params: tuple,
                h_seg: np.ndarray,
                ref_seg: np.ndarray,
                trade_data: np.ndarray) -> float:
        """ h_seg和ref_seg都是用于生成交易信号的一段窗口数据，根据这一段窗口数据
            生成一个股票的独立交易信号，同样的规则会被复制到其他股票
        """
        pass


class GeneralStg(BaseStrategy):
    """ 通用交易策略类，用户可以使用策略输入的历史数据、参考数据和成交数据，自定信号生成规则，生成交易信号。

        同其他类型的策略一样，Selecting策略同样需要实现抽象方法_realize()，并在该方法中具体描述策略如何根据输入的参数建立投资组合。而
        generate()函数则负责正确地将该定义好的生成方法循环应用到每一个数据分段中。

        Selecting选股策略的生成方式与投资产品的组合方式有关。与择时类策略相比，选股策略与之的区别在于对历史数据的运用方式不同。择时类策略逐一
        计算每个投资品种的投资比例，每一种投资组合的投资比例与其他投资产品无关，因此需要循环读取每一个投资品种的全部或部分历史数据并基于该数据
        确定投资的方向和比例，完成一个投资品种后，用同样的方法独立地确定第二种产品，依此顺序完成所有投资品种的分析决策。而择时策略则不同，该策略
        同时读取所有备选投资产品的历史数据或历史数据片段，并确定这一时期期末所有备选投资产品的投资组合。

        Selecting策略主要由两个成员函数，seg_periods函数根据策略的self.sample_period属性值，将全部历史数据（历史数据以HistoryPanel的
        形式给出）分成数段，每一段历史数据都包含所有的备选投资产品的全部数据类型，但是在时间上首尾相接。例如，从2010年1月1日开始到2020年1月1日
        的全部历史数据可以以"y"为sample_period分为十段，每一段包含一整年的历史数据。

        将数据分段完成后，每一段数据会被整体送入generate()函数中进行处理，该函数会对每一段数据进行运算后确定一个向量，该向量代表从所有备选投资
        产品中建立投资组合的比例。例如：[0, 0.2, 0.3, 0.5, 0]表示建立一个投资组合：从一个含有5个备选投资产品的库中，分别将
        0，20%，30%，50%，0的资金投入到相应的投资产品中。

            * _realize()方法的实现：

            _realize()方法确定了策略的具体实现方式，要注意_realize()方法需要有两个参数：

                :input:
                hist_data: ndarray, 3-dimensional
                params: tuple

                :output
                signals: ndarray, 1-dimensional

            在_realize()方法中用户可以以任何可能的方法使用hist_data，hist_data是一个三维数组，包含L层，R行，C列，分别代表L只个股、
            R个时间序列上的C种数据类型。明确这一点非常重要，因为在_realize()方法中需要正确地利用这些数据生成选股向量。


    """
    __metaclass__ = ABCMeta

    # 设置Selecting策略类的标准默认参数，继承Selecting类的具体类如果沿用同样的静态参数，不需要重复定义
    def __init__(self,
                 pars: tuple = None,
                 stg_name: str = 'NEW-SEL',
                 stg_text: str = 'intro text of selecting strategy',
                 proportion_or_quantity: float = 0.5,
                 **kwargs):
        super().__init__(pars=pars,
                         stg_type='SELECT',
                         stg_name=stg_name,
                         stg_text=stg_text,
                         **kwargs)
        self.proportion_or_quantity = proportion_or_quantity

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 通用交易策略的所有策略代码全部都在realize中实现
        """
        return self.realize(params=self.pars, h_seg=h_seg, ref_seg=ref_seg, trade_data=trade_data)

    @abstractmethod
    def realize(self,
                params,
                h_seg,
                ref_seg,
                trade_data):
        """ h_seg和ref_seg都是用于生成交易信号的一段窗口数据，根据这一段窗口数据
            生成一条交易信号
        """
        pass


class FactorSorter(BaseStrategy):
    """ 因子选股，根据用户定义获选择的因子

        股票的选择取决于一批股票的某一个选股因子，这个指标可以是财务指标、量价指标，或者是其他的指标，这些指标形成一个一维向量，即指标向量
        指标向量首先被用来执行条件选股：当某个股票的指标符合某条件时，股票被选中，
            这些条件包括：大于某数、小于某数、介于某两数之间，或不在两数之间
        对于被选中的股票，还可以根据其指标在所有股票中的大小排序执行选股：例如，从大到小排列的前30%或前10个
        条件选股和排序选股可以兼而有之

        数据类型：由data_types指定的财报指标财报数据，单数据输入，默认数据为EPS
        数据分析频率：季度
        数据窗口长度：90
        策略使用6个参数:
            sort_ascending:     bool,   排序方法，对选中的股票进行排序以选择或分配权重：
                                        True         :对选股指标从小到大排列，优先选择指标最小的股票
                                        False        :对选股指标从大到小排泄，优先选择指标最大的股票
            weighting:          str ,   确定如何分配选中股票的权重
                                        'even'       :所有被选中的股票都获得同样的权重
                                        'linear'     :权重根据分值排序线性分配，分值最高者占比约为分值最低者占比的三倍，
                                                      其余居中者的比例按序呈等差数列
                                        'proportion' :指标最低的股票获得一个基本权重，其余股票的权重与他们的指标与最低
                                                      指标之间的差值成比例
            condition:          str ,   确定如何根据条件选择股票，可用值包括：
                                        'any'        :选择所有可用股票
                                        'greater'    :选择指标大于ubound的股票
                                        'less'       :选择指标小于lbound的股票
                                        'between'    :选择指标介于lbound与ubound之间的股票
                                        'not_between':选择指标不在lbound与ubound之间的股票
            lbound:             float,  执行条件选股时的指标下界
            ubound:             float,  执行条件选股时的指标上界
            pct:                float,  最多从股票池中选出的投资组合的数量或比例，当0<pct<1时，选出pct%的股票，当pct>=1时，选出pct只股票
        参数输入数据范围：[(True, False),
                       ('even', 'linear', 'proportion'),
                       ('any', 'greater', 'less', 'between', 'not_between'),
                       (-inf, inf),
                       (-inf, inf),
                       (0, 1.)]
    """
    __metaclass__ = ABCMeta

    # 设置Selecting策略类的标准默认参数，继承Selecting类的具体类如果沿用同样的静态参数，不需要重复定义
    def __init__(self,
                 pars: tuple = None,
                 stg_name: str = 'NEW-FAC',
                 stg_text: str = 'intro text of selecting strategy',
                 proportion_or_quantity: float = 0.5,
                 condition: str = 'any',
                 lbound: float = -np.inf,
                 ubound: float = np.inf,
                 sort_ascending: bool = True,
                 weighting: str = 'even',
                 **kwargs):
        super().__init__(pars=pars,
                         stg_type='FACTOR',
                         stg_name=stg_name,
                         stg_text=stg_text,
                         **kwargs)
        self.proportion_or_quantity = proportion_or_quantity
        self.condition = condition
        self.lbound = lbound
        self.ubound = ubound
        self.sort_ascending = sort_ascending
        self.weighting = weighting

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """处理从_realize()方法传递过来的选股因子

        选出符合condition的因子，并将这些因子排序，根据次序确定所有因子相应股票的选股权重
        将选股权重传递到generate()方法中，生成最终的选股蒙板

        input:
            :type h_seg: np.ndarray
        :return
            numpy.ndarray, 一个一维向量，代表一个周期内股票的投资组合权重，所有权重的和为1
        """
        pct = self.proportion_or_quantity
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
        factors = self.realize(params=self.pars, h_seg=h_seg, ref_seg=ref_seg, trade_data=trade_data).squeeze()
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
            # 选择分数最高的部分个股，由于np排序时会把NaN值与最大值排到一起，因此需要去掉所有NaN值
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
        # 根据投资组合比例分配方式，确定被选中产品的权重
        # linear 线性比例分配，将所有分值排序后，股票的比例呈线性分布
        if weighting == 'linear':
            dist = np.arange(1, 3, 2. / arg_count)  # 生成一个线性序列，最大值为最小值的约三倍
            chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
        # distance：距离分配，权重与其分值距离成正比，分值最低者获得一个基础比例，其余股票的比例
        # 与其分值的距离成正比，分值的距离为它与最低分之间的差值，因此不管分值是否大于0，股票都能
        # 获取比例分配
        elif weighting == 'distance':
            dist = factors[args]
            d = dist.max() - dist.min()
            if not sort_ascending:
                dist = dist - dist.min() + d / 10.
            else:
                dist = dist.max() - dist + d / 10.
            # print(f'in GeneralStg realize method proportion type got distance of each item like:\n{dist}')
            if ~np.any(dist):  # if all distances are zero
                chosen[args] = 1 / len(dist)
            elif dist.sum() == 0:  # if not all distances are zero but sum is zero
                chosen[args] = dist / len(dist)
            else:
                chosen[args] = dist / dist.sum()
        # proportion：比例分配，权重与其分值成正比，分值为0或小于0者比例为0
        elif weighting == 'proportion':
            fctr = factors[args]
            proportion = fctr / fctr.sum()
            chosen[args] = np.where(proportion < 0, 0, proportion)  # np.where 比 proportion.clip(0) 速度快得多
        # even：均匀分配，所有中选股票在组合中权重相同
        elif weighting == 'even':
            chosen[args] = 1. / arg_count
        else:
            raise KeyError(f'invalid weighting type: "{weighting}". '
                           f'should be one of ["linear", "proportion", "even"]')
        return chosen

    @abstractmethod
    def realize(self,
                params,
                h_seg,
                ref_seg,
                trade_data):
        """ h_seg和ref_seg都是用于生成交易信号的一段窗口数据，根据这一段窗口数据
            生成一条交易信号
        """
        pass