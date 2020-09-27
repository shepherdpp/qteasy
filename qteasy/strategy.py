# coding=utf-8
# strategy.py

# ======================================
# This file contains all built-in
# strategies that inherited from
# Strategy class and its sub-classes.
# ======================================

import numpy as np
import pandas as pd
from qteasy.tafuncs import sma, ema, trix, cdldoji
from abc import abstractmethod, ABCMeta
from .utilfuncs import str_to_list
from .utilfuncs import TIME_FREQ_STRINGS


class Strategy:
    """ 量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的策略类调用

        类属性定义了策略类型、策略名称、策略关键属性的数量、类型和取值范围等
        所有的策略类都包含相似的基础属性
        所有的策略类都有一个generate()方法，这个方法是策略类的主入口方法，这个方法接受一组历史数据(np.ndarray对象)从历史数据中提取出
        有用的信息，并生成用于投资的操作或交易信号。
        另外，所有的策略类都有四个参数设置方法，用于对相关的参数进行设置：
            set_par(): 设置策略参数
            set_opt_tag(): 设置策略优化标志
            set_par_boes(): 设置策略参数空间定义标识
            set_hist_pars(): 设置策略的历史数据相关参数
    """
    __mataclass__ = ABCMeta

    def __init__(self,
                 pars: tuple = None,
                 opt_tag: int = 0,
                 stg_type: str = 'strategy type',
                 stg_name: str = 'strategy name',
                 stg_text: str = 'intro text of strategy',
                 par_count: int = 0,
                 par_types: [list, str] = None,
                 par_bounds_or_enums: [list, tuple] = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: [str, list] = ''):
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
            :param sample_freq:             静态属性，策略生成时测采样频率，即相邻两次策略生成的间隔频率，可选参数与data_freq
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
                                            7,
        """
        self._pars = pars  # 策略的参数，动态属性，可以直接赋值（通过set_pars函数赋值）
        self._opt_tag = opt_tag  # 策略的优化标记，
        self._stg_type = stg_type  # 策略类型
        self._stg_name = stg_name  # 策略的名称
        self._stg_text = stg_text  # 策略的描述文字
        self._par_count = par_count  # 策略参数的元素个数
        self._par_types = par_types  # 策略参数的类型，可选类型'discr/conti/enum'
        if par_bounds_or_enums is None:  # 策略参数的取值范围或取值列表，如果是数值型，可以取上下限，其他类型的数据必须为枚举列表
            self._par_bounds_or_enums = []
        else:
            self._par_bounds_or_enums = par_bounds_or_enums
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

    def __str__(self):
        """打印所有相关信息和主要属性"""
        str1 = f'{type(self)}'
        str2 = f'\nStrategy type: {self.stg_type}'
        str3 = f'\nInformation of the strategy: {self.stg_name}, {self.stg_text}'
        str4 = f'\nOptimization Tag and opti ranges: {self.opt_tag}, {self.par_boes}'
        if self._pars is not None:
            str5 = f'\nParameter Loaded; {type(self._pars)}, {self._pars}\n'
        else:
            str5 = f'\nParameter NOT loaded!\n'
        return ''.join([str1, str2, str3, str4, str5])

    def __repr__(self):
        """ 打印对象的相关信息

        :return:
        """
        str1 = f'{type(self)}'
        str2 = ''  # f'\nStrategy {self.stg_type}'
        return str1

    def info(self, verbose: bool = False):
        """打印所有相关信息和主要属性"""
        print(type(self), f'Strategy type: {self.stg_name}')
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_boes)
        if self._pars is not None:
            print('Parameter Loaded：', type(self._pars), self._pars)
        else:
            print('Parameter NOT loaded!')
        # 在verbose == True时打印更多的额外信息
        if verbose:
            print('Information of the strategy:\n', self.stg_name, self.stg_text)

    def set_pars(self, pars: tuple) -> int:
        """设置策略参数，在设置之前对参数的个数进行检查

        input:
            :param: type pars: tuple，需要设置的参数
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
        raise ValueError(f'parameter setting error in set_pars() method of \n{self}expected par count: '
                         f'{self.par_count}, got {len(pars)}')

    def set_opt_tag(self, opt_tag: int) -> int:
        """ 设置策略的优化类型

        input"
            :param opt_tag: int，0：不参加优化，1：参加优化
        :return:
        """
        assert isinstance(opt_tag, int), f'optimization tag should be an integer, got {type(opt_tag)} instead'
        assert 0 <= opt_tag <= 1, f'ValueError, optimization tag should be 0 or 1, got {opt_tag} instead'
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

    def set_hist_pars(self, data_freq=None, sample_freq=None, window_length=None, data_types=None):
        """ 设置策略的历史数据回测相关属性

        :param data_freq: str,
        :param sample_freq: str, 可以设置为'min'， 'd'等代表回测时的运行或采样频率
        :param window_length: int，表示回测时需要用到的历史数据深度
        :param data_types: str，表示需要用到的历史数据类型
        :return: None
        """
        if data_freq is not None:
            assert isinstance(data_freq, str), \
                f'TypeError, sample frequency should be a string, got {type(data_freq)} instead'
            assert data_freq.upper() in TIME_FREQ_STRINGS, f'ValueError, {data_freq} is not a valid frequency ' \
                                                           f'string'
            self._data_freq = data_freq
        if sample_freq is not None:
            assert isinstance(sample_freq, str), \
                f'TypeError, sample frequency should be a string, got {type(sample_freq)} instead'
            assert sample_freq.upper() in TIME_FREQ_STRINGS, f'ValueError, {sample_freq} is not a valid frequency ' \
                                                             f'string'
            self._sample_freq = sample_freq
        if window_length is not None:
            assert isinstance(window_length, int), \
                f'TypeError, window length should an integer, got {type(window_length)} instead'
            assert window_length > 0, f'ValueError, {window_length} is not a valid window length'
            self._window_length = window_length
        if data_types is not None:
            if isinstance(data_types, str):
                data_types = str_to_list(data_types, ',')
            assert isinstance(data_types, list), \
                f'TypeError, data type should be a list, got {type(data_types)} instead'
            self._data_types = data_types

    @abstractmethod
    def generate(self, hist_data: np.ndarray, shares: [str, list], dates: [str, list]):
        """策略类的抽象方法，接受输入历史数据并根据参数生成策略输出"""
        raise NotImplementedError


class RollingTiming(Strategy):
    """择时策略的抽象基类，所有择时策略都继承自该抽象类，本类继承自策略基类，同时定义了generate_one()抽象方法，用于实现具体的择时策略

        Rolling Timing择时策略的generate()函数采用了滚动信号生成机制，每次从全部历史数据中提取出一个片段（这个片段被称为"窗口"），
        使用这个片段中的全部历史数据计算片段最后一个时间点的策略信号，一个时间点的策略信号计算完成后，再提取出第二个相邻的历史数据片段，
        并计算下一个策略信号。例如：
            假设历史数据开始于第0天，结束于第1000天，频率为'D'，若历史数据片段窗口长度为100天，那么首先0～100天的历史数据会被提取出来，用于
            计算第100天的策略输出信号，接着，第1～101天的历史数据被提取出来用于计算第101天的策略输出信号，以此类推，重复901次，计算从100天
            到1000天的全部策略信号

        在择时类策略中，generate方法接受的历史数据片段hist_data为一个M * N * L的ndarray, 来自HistoryPanel对象，其定义是：
            M: axis 1: 层，每层的标签为一个个股，每一层在HistoryPanel中被称为一个level，所有level的标签被称为shares
            N: axis 2: 行，每行的标签为一个时间点，每一行在HistoryPanel中被称为一个row，所有row的标签被称为hdates
            L: axis 3: 列，每列的标签为一种历史数据，每一列在HistoryPanel中被称为一个column，所有column的标签被称为htypes

        在generate()函数中，每一个个股的历史数据被逐个取出，并送入generate_over()函数进行处理，每个个股的数据块为N行L列。
        在generate_over()函数中，上述数据被打包成为一个历史数据片段hist_pack，其中包含的数据类型为self.data_types参数定义。
        hist_pack是一个numpy ndarray对象，包含M行N列数据，其中:
            M = self._window_length,
            N = len(self._data_types)
        这些数据代表投资产品在一个window_length长的历史区间内的历史价格数据，数据的频率为self.data_freq所指定。

    Rolling Timing择时策略是通过realize()函数来实现的。一个继承了Rolling_Timing类的对象，必须具体实现realize()方法，在
    Rolling_Timing对象中，这是个抽象方法。这个方法接受两个参数，一个是generate_over()函数传送过来的window_history数据，另一个
    是策略参数，策略通过传入的参数，利用window_history历史数据进行某种特定计算，最后生成一个-1～1之间的浮点数，这个数子就是在某一
    时间点的策略输出。

    Rolling_Timing类会自动把上述特定计算算法滚动应用到整个历史数据区间，并且推广到所有的个股中。

    """
    __mataclass__ = ABCMeta

    def __init__(self,
                 pars: tuple = None,
                 stg_name: str = 'NONE',
                 stg_text: str = 'intro text of timing strategy',
                 par_count: int = 0,
                 par_types: [list, str] = None,
                 par_bounds_or_enums: [list, tuple] = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: [list, str] = 'close'):
        super().__init__(pars=pars,
                         stg_type='TIMING',
                         stg_name=stg_name,
                         stg_text=stg_text,
                         par_count=par_count,
                         par_types=par_types,
                         par_bounds_or_enums=par_bounds_or_enums,
                         data_freq=data_freq,
                         sample_freq=sample_freq,
                         window_length=window_length,
                         data_types=data_types)

    @abstractmethod
    def _realize(self, hist_data: np.ndarray, params: tuple) -> int:
        """ 策略的具体实现方法，在具体类中需要重写，是整个类的择时信号基本生成方法，针对单个个股的价格序列生成多空状态信号

            同时，params是一个元组，包含了应用于这一个投资产品的策略参数（由于同一个策略允许对不同的投资产品应用不同的策略参数，
            这里的策略参数已经被自动分配好了）。投资策略参数的个数为self.par_count所指定，每个投资参数的类型也为self.par_types
            所指定。

            在策略的实现方法中，需要做的仅仅是定义一种方法，根据hist_pack中给出的历史数据，作出关于这个投资产品在历史数据结束后紧
            接着的那个时刻的头寸位置（空头头寸还是多头头寸）。在择时策略的实现方法中，不需要考虑其他任何方面的问题，如交易品种、
            费率、比例等等，也不需要考虑历史数据中的缺陷如停牌等，只需要返回一个代表头寸位置或交易信号的整数即可：
                ---------------------------------
                return  |   L/S    | Signal
                =================================
                  1     |  多头头寸 | 开多仓或平空仓
                  0     |  没有头寸 | 无操作
                 -1     |  空头头寸 | 开空仓或平多仓

            qteasy系统会自行把适用于这个历史片段的策略，原样地推广到整个历史数据区间，同时推广到整个投资组合。并且根据投资组合管理
            策略（选股策略Selecting）中定义的选股方法确定每种投资产品的仓位比例。最终生成交易清单。
        input:
            :param hist_data: ndarray，历史数据，策略的计算在历史数据基础上进行
            :param params: tuple, 策略参数，具体的策略输出结果依靠参数给出
        return:
            :stg_output: int, 一个代表策略输出的数字，可以代表头寸位置，1代表多头，-1代表空头，0代表空仓，策略输出同样可以代表操作
            信号，1代表开多仓或平空仓，-1代表开空仓或平多仓，0代表不操作
        """
        raise NotImplementedError

    def _generate_over(self, hist_slice: np.ndarray, pars: tuple):
        """ 中间构造函数，将历史数据模块传递过来的单只股票历史数据去除nan值，并进行滚动展开
            对于滚动展开后的矩阵，使用map函数循环调用generate_one函数生成整个历史区间的
            循环回测结果（结果为1维向量， 长度为hist_length - _window_length + 1）

        input:
            :param hist_slice: 历史数据切片，一只个股的所有类型历史数据，shape为(rows, columns)
                rows： 历史数据行数，每行包含个股在每一个时间点上的历史数据
                columns： 历史数据列数，每列一类数据如close收盘价、open开盘价等
            :param pars: 策略生成参数，将被原样传递到_realize()函数中
        :return:
            np.ndarray: 一维向量。根据策略，在历史上产生的多空信号，1表示多头、0或-1表示空头
        """
        # print(f'hist_slice got in Timing.generate_over() function is shaped {hist_slice.shape}, parameter: {pars}')
        # print(f'first 20 rows of hist_slice got in Timing.generator_over() is:\n{hist_slice[:20]}')
        # 获取输入的历史数据切片中的NaN值位置，提取出所有部位NAN的数据，应用_realize()函数
        # 由于输入的历史数据来自于HistoryPanel，因此总是三维数据的切片即二维数据，因此可以简化：
        # if len(hist_slice.shape) == 2:
        #     no_nan = ~np.isnan(hist_slice[:, 0])
        # else:
        #     no_nan = ~np.isnan(hist_slice)
        no_nan = ~np.isnan(hist_slice[:, 0])
        # 生成输出值一维向量
        cat = np.zeros(hist_slice.shape[0])
        hist_nonan = hist_slice[no_nan]  # 仅针对非nan值计算，忽略股票停牌时期
        loop_count = len(hist_nonan) - self.window_length + 1
        if loop_count < 1:  # 在开始应用generate_one()前，检查是否有足够的非Nan数据，如果数据不够，则直接输出全0结果
            return cat[self.window_length:]

        # 如果有足够的非nan数据，则开始进行历史数据的滚动展开
        hist_pack = np.zeros((loop_count, *hist_nonan[:self._window_length].shape))
        # TODO：需要找到比循环的方式更快的数据滚动展开的方法，目前循环就是最快的办法，是否可以尝试使用矩阵的公式创建？
        for i in range(loop_count):
            hist_pack[i] = hist_nonan[i:i + self._window_length]
        # 滚动展开完成，形成一个新的3D或2D矩阵
        # 开始将参数应用到策略实施函数generate中
        par_list = [pars] * loop_count
        # TODO: 因为在generate_over()函数中接受的参数都只会是一个个股的数据，因此不存在par_list会不同的情况，因此不需要使用map，
        # TODO: 可以使用apply_along_axis()从而进一步提高效率
        res = np.array(list(map(self._realize,
                                hist_pack,
                                par_list)))
        # TODO: 如果在创建cat的时候就去掉最前面一段，那么这里的capping和concatenate()就都不需要了，这都是很费时的操作
        # 生成的结果缺少最前面window_length那一段，因此需要补齐
        capping = np.zeros(self._window_length - 1)
        # debug
        # print(f'in Timing.generate_over() function shapes of res and capping are {res.shape}, {capping.shape}')
        res = np.concatenate((capping, res), 0)
        # 将结果填入原始数据中不为Nan值的部分，原来为NAN值的部分保持为0
        cat[no_nan] = res
        # debug
        # print(f'created long/short mask for current hist_slice is: \n{cat[self.window_length:][:100]}')
        return cat[self.window_length:]

    def generate(self, hist_data: np.ndarray, shares=None, dates=None):
        """ 生成整个股票价格序列集合的多空状态历史矩阵，采用滚动计算的方法，确保每一个时间点上的信号都只与它之前的一段历史数据有关

            本方法基于np的ndarray计算，是择时策略的打包方法。
            择时策略的具体实现方法写在self._realize()方法中，定义一种具体的方法，根据一个固定长度的历史数据片段来确定一只股票
            或其他投资产品在历史数据片段的结束时的头寸位置。而generate函数则接收一个包含N只股票的更长的历史数据，把多只股票的
            历史数据进行切片，分别应用不同的（或相同的）策略参数，并调用generate_over()函数，反复地在更长历史数据区间里滚动地
            计算股票的多空位置，形成整个历史区间上的多空信号矩阵。
        input：
            param: hist_data：np.nadarray，历史价格数据，是一个3D数据组
        return：=====
            L/S mask: ndarray, 所有股票在整个历史区间内的所有多空信号矩阵，包含M行N列，每行是一个时间点上的多空信号，每列一只股票
        """
        # debug
        # print(f'hist_data got in Timing.generate() function is shaped {hist_data.shape}')
        # 检查输入数据的正确性：检查数据类型和历史数据的总行数应大于策略的数据视窗长度，否则无法计算策略输出
        assert isinstance(hist_data, np.ndarray), f'Type Error: input should be ndarray, got {type(hist_data)}'
        assert hist_data.ndim == 3, \
            f'DataError: historical data should be 3 dimensional, got {hist_data.ndim} dimensional data'
        assert hist_data.shape[1] >= self._window_length, \
            f'DataError: Not enough history data! expected hist data length {self._window_length},' \
            f' got {hist_data.shape[1]}'
        pars = self._pars
        # 当需要对不同的股票应用不同的参数时，参数以字典形式给出，判断参数的类型
        if isinstance(pars, dict):
            par_list = pars.values()  # 允许使用dict来为不同的股票定义不同的策略参数
        else:
            par_list = [pars] * len(hist_data)  # 生成长度与shares数量相同的序列
        # 调用_generate_over()函数，生成每一只股票的历史多空信号清单，用map函数把所有的个股数据逐一传入计算，并用list()组装结果
        assert len(par_list) == len(hist_data), \
            f'InputError: can not map {len(par_list)} parameters to {hist_data.shape[0]} shares!'
        # 使用map()函数将每一个参数应用到历史数据矩阵的每一列上（每一列代表一个个股的全部历史数据），使用map函数的速度比循环快得多
        res = np.array(list(map(self._generate_over,
                                hist_data,
                                par_list))).T

        # debug
        # print(f'the history data passed to simple rolling realization function is shaped {hist_data.shape}')
        # print(f'generate result of np timing generate, result shaped {res.shape}')
        # print(f'generate result of np timing generate after cutting is shaped {res[self.window_length:, :].shape}')
        # 每个个股的多空信号清单被组装起来成为一个完整的多空信号矩阵，并返回
        return res


class Selecting(Strategy):
    """选股策略类的抽象基类，所有选股策略类都继承该类"""
    __metaclass__ = ABCMeta

    # 设置Selecting策略类的标准默认参数，继承Selecting类的具体类如果沿用同样的静态参数，不需要重复定义
    def __init__(self,
                 pars: tuple = None,
                 opt_tag: int = 0,
                 stg_name: str = 'NONE',
                 stg_text: str = 'intro text of selecting strategy',
                 par_count: int = 1,
                 par_types: [list, str] = None,
                 par_bounds_or_enums: [list, tuple] = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'y',
                 proportion_or_quantity: float = 0.5,
                 window_length: int = 270,
                 data_types: [list, str] = 'close'):
        if par_types is None:
            par_types = ['conti']
        if par_bounds_or_enums is None:
            par_bounds_or_enums = [(0, 1)]
        super().__init__(pars=pars,
                         opt_tag=opt_tag,
                         stg_type='SELECTING',
                         stg_name=stg_name,
                         stg_text=stg_text,
                         par_count=par_count,
                         par_types=par_types,
                         par_bounds_or_enums=par_bounds_or_enums,
                         data_freq=data_freq,
                         sample_freq=sample_freq,
                         window_length=window_length,
                         data_types=data_types)
        self._poq = proportion_or_quantity

    @abstractmethod
    def _realize(self, hist_data: np.ndarray):
        """" Selecting 类的选股抽象方法，在不同的具体选股类中应用不同的选股方法，实现不同的选股策略

        input:
            :param hist_data: type: numpy.ndarray, 一个历史数据片段，包含N个股票的data_types种数据在window_length日内的历史
            数据片段
        :return
            numpy.ndarray, 一个一维向量，代表一个周期内股票选择权重，整个向量经过归一化，即所有元素之和为1
        """
        raise NotImplementedError

    # TODO：改写Selecting类，使用sample_freq来定义分段频率，使Timing策略和Selecting策略更多地共享属性
    # TODO：Selecting的分段与Timing的Rolling Expansion滚动展开其实是同一个过程，未来可以尝试合并并一同优化
    def _seg_periods(self, dates, freq):
        """ 对输入的价格序列数据进行分段，Selection类会对每个分段应用不同的股票组合

        对输入的价格序列日期进行分析，生成每个历史分段的起止日期所在行号，并返回行号和分段长度（数据行数）
        input:
            dates ndarray，日期序列，
            freq：str 分段频率，取值为‘Q'：季度， ’Y'，年度； ‘M'，月度
        return: =====
            seg_pos: 每一个历史分段的开始日期;
            seg_lens：每一个历史分段中含有的历史数据数量，
            len(seg_lens): 分段的数量
            生成历史区间内的时间序列，序列间隔为选股间隔，每个时间点代表一个选股区间的开始时间
        """
        # assert isinstance(dates, list), \
        #     f'TypeError, type list expected in method seg_periods, got {type(dates)} instead! '
        bnds = pd.date_range(start=dates[self.window_length], end=dates[-1], freq=freq)
        # 写入第一个选股区间分隔位——0 (仅当第一个选股区间分隔日期与数据历史第一个日期不相同时才这样处理)
        seg_pos = np.zeros(shape=(len(bnds) + 2), dtype='int')
        # debug
        # print(f'in module selecting: function seg_perids: comparing {dates[0]} and {bnds[0]}')
        # 用searchsorted函数把输入的日期与历史数据日期匹配起来
        seg_pos[1:-1] = np.searchsorted(dates, bnds)
        # 最后一个分隔位等于历史区间的总长度
        seg_pos[-1] = len(dates) - 1
        # print('Results check, selecting - segment creation, segments:', seg_pos)
        # 计算每个分段的长度
        seg_lens = (seg_pos - np.roll(seg_pos, 1))[1:]
        # 默认情况下是要在seg_pos的最前面添加0，表示从第一个日期起始，但如果界限日期与第一个日期重合，则需要除去第一个分割位，因为这样会有两个
        # [0]了，例子如下（为简单起见，例子中的日期都用整数代替）：
        # 例子：要在[1，2，3，4，5，6，7，8，9，10]这样一个时间序列中，按照某频率分段，假设分段的界限分别是[3,6,9]
        # 那么，分段界限在时间序列中的seg_pos分别为[2,5,8], 这三个pos分别是分段界限3、6、9在时间序列中所处的位置：
        # 第3天的位置为2，第6天的位置为5，第9天的位置为8
        # 然而，为了确保在生成选股数据时，第一天也不会被拉下，需要认为在seg_pos列表中前面插入一个0，得到[0,2,5,8]，这样才不会漏掉第一天和第二天
        # 以上是正常情况的处理方式
        # 如果分段的界限是[1,5,10]的时候，情况就不同了
        # 分段界限在时间序列中的seg_pos分别为[0,4,9]，这个列表中的首位本身就是0了，如果再在前面添加0，就会变成[0,0,4,9],会出现问题
        # 因为系统会判断第一个分段起点为0，终点也为0，因此会传递一个空的ndarray到_realize()函数中，引发难以预料的错误
        # 因此，出现这种情况时，要忽略最前面一位，返回时忽略第一位即可
        if seg_pos[1] == 0:
            return seg_pos[1:], seg_lens[1:], len(seg_pos) - 2
        else:
            return seg_pos, seg_lens, len(seg_pos) - 1

    # TODO：需要重新定义Selecting的generate函数，仅使用hist_data一个参数，其余参数都可以根据策略的基本属性推断出来
    # TODO: 使函数的定义符合继承类的抽象方法定义规则
    def generate(self, hist_data: np.ndarray, shares, dates):
        """
        生成历史价格序列的选股组合信号：将历史数据分成若干连续片段，在每一个片段中应用某种规则建立投资组合
        建立的投资组合形成选股组合蒙版，每行向量对应所有股票在当前时间点在整个投资组合中所占的比例

        input:
            :param hist_data: type: HistoryPanel, 历史数据
            :param shares: type:
            :param dates
        :return:=====
            sel_mask：选股蒙版，是一个与输入历史数据尺寸相同的ndarray，dtype为浮点数，取值范围在0～1之间
            矩阵中的取值代表股票在投资组合中所占的比例，0表示投资组合中没有该股票，1表示该股票占比100%
        """
        # 提取策略参数
        assert self.pars is not None, 'TypeError, strategy parameter should be a tuple, got None!'
        assert isinstance(self.pars, tuple), f'TypeError, strategy parameter should be a tuple, got {type(self.pars)}'
        assert len(self.pars) == self.par_count, \
            f'InputError, expected count of parameter is {self.par_count}, got {len(self.pars)} instead'
        assert isinstance(hist_data, np.ndarray), \
            f'InputError: Expect numpy ndarray object as hist_data, got {type(hist_data)}'
        assert isinstance(shares, list), f'InputError, shares should be a list, got {type(shares)} instead'
        assert isinstance(dates, list), f'TypeError, dates should be a list, got{type(dates)} instead'
        assert all([isinstance(share, str) for share in shares]), \
            f'TypeError, all elements in shares should be str, got otherwise'
        assert all([isinstance(date, pd.Timestamp) for date in dates]), \
            f'TYpeError, all elements in dates should be Timestamp, got otherwise'
        freq = self.sample_freq
        # 获取完整的历史日期序列，并按照选股频率生成分段标记位，完整历史日期序列从参数获得，股票列表也从参数获得
        # TODO: 这里的选股分段可以与Timing的Rolling Expansion整合，同时避免使用dates和freq，使用self.sample_freq属性
        seg_pos, seg_lens, seg_count = self._seg_periods(dates, freq)
        # 一个空的ndarray对象用于存储生成的选股蒙版
        sel_mask = np.zeros(shape=(len(dates), len(shares)), order='C')
        # 原来的函数实际上使用未来的数据生成今天的结果，这样是错误的
        # 例如，对于seg_start = 0，seg_lengt = 6的时候，使用seg_start:seg_start + seg_length的数据生成seg_start的数据，
        # 也就是说，用第0:6天的数据，生成了第0天的信号
        # 因此，seg_start不应该是seg_pos[0]，而是seg_pos[1]的数，因为这才是真正应该开始计算的第一条信号
        # 正确的方法是用seg_start:seg_length的数据生成seg_start+seg_length那天的信号，即
        # 使用0:6天的数据（不含第6天）生成第6天的信号
        # 不过这样会带来一个变化，即生成全部操作信号需要更多的历史数据，包括第一个信号所在日期之前window_length日的数据
        # 因此在输出数据的时候需要将前window_length个数据截取掉
        seg_start = seg_pos[1]
        # 针对每一个选股分段区间内生成股票在投资组合中所占的比例
        # TODO: 可以使用map函数生成分段
        # debug
        # print(f'hist data received in selecting strategy (shape: {hist_data.shape}):\n{hist_data}')
        # print(f'history segmentation factors are:\nseg_pos:\n{seg_pos}\nseg_lens:\n{seg_lens}\nseg_count\n{
        # seg_count}')
        for sp, sl, fill_len in zip(seg_pos[1:-1], seg_lens, seg_lens[1:]):
            # share_sel向量代表当前区间内的投资组合比例
            # debug
            # print(f'{sl} rows of data,\n starting from {sp - sl} to {sp - 1},\n'
            #       f' will be passed to selection realize function:\n{hist_data[:, sp - sl:sp, :]}')
            share_sel = self._realize(hist_data[:, sp - sl:sp, :])
            seg_end = seg_start + fill_len
            # 填充相同的投资组合到当前区间内的所有交易时间点
            sel_mask[seg_start:seg_end + 1, :] = share_sel
            # debug
            # print(f'filling data into the sel_mask, now filling \n{share_sel}\nin she sell mask '
            #       f'from row {seg_start} to {seg_end} (not included)\n')
            seg_start = seg_end
        # 将所有分段组合成完整的ndarray
        # debug
        # print(f'hist data is filled with sel value, shape is {sel_mask.shape}')
        # print(f'but the first {self.window_length} rows will be removed from the data\n'
        #       f'only last {sel_mask.shape[0] - self.window_length} rows will be returned\n'
        #       f'returned mask shape is {sel_mask[self.window_length:].shape}')
        return sel_mask[self.window_length:]


class SimpleTiming(Strategy):
    """ 风险控制抽象类，所有风险控制策略均继承该类

        风险控制策略在选股和择时策略之后发生作用，在选股和择时模块形成完整的投资组合及比例分配后，通过比较当前和预期的投资组合比例
        生成交易信号，而风控策略则在交易信号生成以后，根据历史数据对交易信号进行调整，其作用可以在已有的交易信号基础上增加新的交易信号
        也可以删除某些交易信号，或对交易信号进行修改。通过对交易信号的直接操作，实现风险控制的目的。

        风险控制策略目前的作用仅仅是在多空蒙版和选股蒙板之外对交易信号作出一些补充，但是从根本上来说这是远远不够的
        风控策略应该能够起到更大的作用，对整个选股和择时策略的系统性运行风险进行监控，控制或降低系统性风险。
        因此，未来可能会对风控策略的基本架构进行重新调整，以适应起应有的功能
    """
    __metaclass__ = ABCMeta

    def __init__(self,
                 pars: tuple = None,
                 opt_tag: int = 0,
                 stg_name: str = 'NONE',
                 stg_text: str = 'intro text of selecting strategy',
                 par_count: int = 2,
                 par_types: [list, str] = None,
                 par_bounds_or_enums: [list, tuple] = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: [list, str] = 'close'):
        super().__init__(pars=pars,
                         opt_tag=opt_tag,
                         stg_type='RICON',
                         stg_name=stg_name,
                         stg_text=stg_text,
                         par_count=par_count,
                         par_types=par_types,
                         par_bounds_or_enums=par_bounds_or_enums,
                         data_freq=data_freq,
                         sample_freq=sample_freq,
                         window_length=window_length,
                         data_types=data_types)

    @abstractmethod
    def _realize(self, hist_data: np.ndarray, params: tuple):
        """抽象方法，在实际实现SimpleTiming对象的时候必须实现这个方法，以实现策略的计算"""
        raise NotImplementedError

    def _generate_over(self, hist_slice: np.ndarray, pars: tuple):
        """处理给定的历史数据中的nan值，因为nan值代表股票历史数据中的停牌或空缺位，在计算时应该忽略这些数据

        input:
            :param hist_slice: 历史数据切片，一只个股的所有类型历史数据，shape为(rows, columns)
                rows： 历史数据行数，每行包含个股在每一个时间点上的历史数据
                columns： 历史数据列数，每列一类数据如close收盘价、open开盘价等
            :param pars: 策略生成参数，将被原样传递到_realize()函数中
        :return:
            np.ndarray: 一维向量。根据策略，在历史上产生的多空信号，1表示多头、0或-1表示空头
        """
        nonan = ~np.isnan(hist_slice[:, 0])
        # 生成输出值一维向量
        cat = np.zeros(hist_slice.shape[0])
        hist_nonan = hist_slice[nonan]  # 仅针对非nan值计算，忽略股票停牌时期
        loop_count = len(hist_nonan) - self.window_length + 1
        if loop_count < 1:  # 在开始应用generate_one()前，检查是否有足够的非Nan数据，如果数据不够，则直接输出全0结果
            return cat
        # 将所有的非nan值（即hist_nonan）传入_realize()函数，并将结果填充到cat[nonan],从而让计算结果不受影响
        cat[nonan] = self._realize(hist_data=hist_nonan, params=pars)
        return cat

    # TODO: 增加generate_over()函数，处理nan值
    def generate(self, hist_data, shares=None, dates=None):
        """基于_realze()方法生成整个股票价格序列集合时序状态值，生成的信号结构与Timing类似，但是所有时序信号是一次性生成的，而不像
        Timing一样，是滚动生成的。这样做能够极大地降低计算复杂度，提升效率。不过这种方法只有在确认时序信号的生成与起点无关时才能采用

        在generate()函数的定义方面，与Rolling_Timing完全一样，只是没有generate_over()函数

        本方法基于np的ndarray计算
        :param hist_data:
        :param shares:
        :param dates:
        :return:
        """
        assert isinstance(hist_data, np.ndarray), f'Type Error: input should be ndarray, got {type(hist_data)}'
        assert hist_data.ndim == 3, \
            f'DataError: historical data should be 3 dimensional, got {hist_data.ndim} dimensional data'
        assert hist_data.shape[1] >= self._window_length, \
            f'DataError: Not enough history data! expected hist data length {self._window_length},' \
            f' got {hist_data.shape[1]}'
        pars = self._pars
        # 当需要对不同的股票应用不同的参数时，参数以字典形式给出，判断参数的类型
        if isinstance(pars, dict):
            par_list = pars.values()  # 允许使用dict来为不同的股票定义不同的策略参数
        else:
            par_list = [pars] * len(hist_data)  # 生成长度与shares数量相同的序列
        # 准备调用realize()函数，对每一个个股进行分别计算
        assert len(par_list) == len(hist_data), \
            f'InputError: can not map {len(par_list)} parameters to {hist_data.shape[0]} shares!'
        # 使用map()函数将每一个参数应用到历史数据矩阵的每一列上（每一列代表一个个股的全部历史数据），使用map函数的速度比循环快得多
        res = np.array(list(map(self._generate_over,
                                hist_data,
                                par_list))).T

        # debug
        # print(f'the history data passed to simple rolling realization function is shaped {hist_data.shape}')
        # print(f'generate result of np timing generate, result shaped {res.shape}')
        # print(f'generate result of np timing generate after cutting is shaped {res[self.window_length:, :].shape}')
        # 每个个股的多空信号清单被组装起来成为一个完整的多空信号矩阵，并返回
        return res[self.window_length:, :]


# All following strategies can be used to create strategies by referring to its name
# Built-in Rolling timing strategies:


class TimingCrossline(RollingTiming):
    """crossline择时策略类，利用长短均线的交叉确定多空状态

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用4个参数，
        s: int, 短均线计算日期；
        l: int, 长均线计算日期；
        m: int, 均线边界宽度；
        hesitate: str, 均线跨越类型
    参数输入数据范围：[(10, 250), (10, 250), (10, 250), ('buy', 'sell', 'none')]

    """

    def __init__(self, pars: tuple = None):
        """Crossline交叉线策略只有一个动态属性，其余属性均不可变"""
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'discr', 'conti', 'enum'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (1, 100), ('buy', 'sell', 'none')],
                         stg_name='CROSSLINE STRATEGY',
                         stg_text='Moving average crossline strategy, determine long/short position according to the ' \
                                  'cross point of long and short term moving average prices ',
                         data_types='close')

    def _realize(self, hist_data, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        # 计算长短均线之间的距离
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        # 根据观望模式在不同的点位产生Long/short标记
        if hesitate == 'buy':
            m = -m
        elif hesitate == 'sell':
            pass
        else:  # hesitate == 'none'
            m = 0
        if diff < m:
            return 1
        else:
            return 0


class TimingMACD(RollingTiming):
    """MACD择时策略类，运用MACD均线策略，在hist_price Series对象上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars: tuple = None):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         stg_name='MACD STRATEGY',
                         stg_text='MACD strategy, determin long/short position according to differences of '
                                  'exponential weighted moving average prices',
                         data_types='close')

    def _realize(self, hist_data, params):
        """生成单只个股的择时多空信号
        生成MACD多空判断：
        1， MACD柱状线为正，多头状态，为负空头状态：由于MACD = diff - dea

        输入:
            idx: 指定的参考指数历史数据
            sRange, 短均线参数，短均线的指数移动平均计算窗口宽度，单位为日
            lRange, 长均线参数，长均线的指数移动平均计算窗口宽度，单位为日
            dRange, DIFF的指数移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """

        s, l, m = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T

        # 计算指数的指数移动平均价格
        diff = ema(h[0], s) - ema(h[0], l)
        dea = ema(diff, m)
        _macd = 2 * (diff - dea)
        # 以下使用utfuncs中的macd函数（基于talib）生成相同结果，但速度稍慢
        # diff, dea, _macd = macd(hist_data, s, l, m)


        if _macd[-1] > 0:
            return 1
        else:
            return 0


class TimingDMA(RollingTiming):
    """DMA择时策略
    生成DMA多空判断：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        3， DMA与股价发生背离时的交叉信号，可信度较高

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         stg_name='DMA STRATEGY',
                         stg_text='DMA strategy, determin long/short position according to differences of moving '
                                  'average prices',
                         data_types='close')

    def _realize(self, hist_data, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick dma Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)
        # print('qDMA generated DMA and ama signal:', dma.size, dma, '\n', ama.size, ama)

        if dma[-1] > ama[-1]:
            return 1
        else:
            return 0


class TimingTRIX(RollingTiming):
    """TRIX择时策略，运用TRIX均线策略，利用历史序列上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270天
    策略使用2个参数，
        s: int, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        m: int, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”
    参数输入数据范围：[(10, 250), (10, 250)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250)],
                         stg_name='TRIX STRATEGY',
                         stg_text='TRIX strategy, determine long/short position according to triple exponential '
                                  'weighted moving average prices',
                         data_freq='d',
                         sample_freq='d',
                         window_length=270,
                         data_types='close')

    def _realize(self, hist_data, params):
        """参数:

        input:
        :param hist_data:
        :param params:
        :return:

        """
        s, m = params
        # print 'Generating trxi Long short Mask with parameters', params

        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        trxi = trix(h[0], s)
        matrix = sma(trxi, m)

        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = 1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 0
        if trxi[-1] > matrix[-1]:
            return 1
        else:
            return 0


class TimingCDL(RollingTiming):
    """CDL择时策略，在K线图中找到符合要求的cdldoji模式

    数据类型：open, high, low, close 开盘，最高，最低，收盘价，多数据输入
    数据分析频率：天
    数据窗口长度：100天
    参数数量：0个，参数类型：N/A，输入数据范围：N/A
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=None,
                         par_bounds_or_enums=None,
                         stg_name='CDL INDICATOR STRATEGY',
                         stg_text='CDL Indicators, determine long/short position according to CDL Indicators',
                         window_length=200,
                         data_types='open,high,low,close')

    def _realize(self, hist_data, params=None):
        """参数:

        input:
            None
        """
        # 计算历史数据上的CDL指标
        h = hist_data.T
        cat = (cdldoji(h[0], h[1], h[2], h[3]).cumsum() // 100)

        return float(cat[-1])


# Built in Simple timing strategies:

class RiconNone(SimpleTiming):
    """无风险控制策略，不对任何风险进行控制"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='NONE',
                         stg_text='Do not take any risk control activity')

    def _realize(self, hist_data, params=None):
        return np.zeros_like(hist_data.squeeze())


class TimingSimple(SimpleTiming):
    """简单择时策略，返回整个历史周期上的恒定多头状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self):
        super().__init__(stg_name='SIMPLE',
                         stg_text='Simple Timing strategy, return constant long position on the whole history')

    def _realize(self, hist_data, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return np.ones_like(hist_data.squeeze())


class SimpleDMA(SimpleTiming):
    """DMA择时策略
    生成DMA多空判断：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        3， DMA与股价发生背离时的交叉信号，可信度较高

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         stg_name='QUICK DMA STRATEGY',
                         stg_text='Quick DMA strategy, determine long/short position according to differences of '
                                  'moving average prices with simple timing strategy',
                         data_types='close')

    def _realize(self, hist_data, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick dma Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)
        # print('qDMA generated DMA and ama signal:', dma.size, dma, '\n', ama.size, ama)

        cat = np.where(dma > ama, 1, 0)
        return cat


class RiconUrgent(SimpleTiming):
    """urgent风控类，继承自Ricon类，重写_generate_ricon方法"""

    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(1, 40), (-0.5, 0.5)],
                         stg_name='URGENT',
                         stg_text='Generate selling signal when N-day drop rate reaches target')

    def _realize(self, hist_data, params):
        """
        # 根据N日内下跌百分比确定的卖出信号，让N日内下跌百分比达到pct时产生卖出信号

        input =====
            :type hist_data: tuple like (N, pct): type N: int, Type pct: float
                输入参数对，当股价在N天内下跌百分比达到pct时，产生卖出信号
        return ====
            :rtype: object np.ndarray: 包含紧急卖出信号的ndarray
        """
        assert self._pars is not None, 'Parameter of Risk Control-Urgent should be a pair of numbers like (N, ' \
                                       'pct)\nN as days, pct as percent drop '
        assert isinstance(hist_data, np.ndarray), \
            f'Type Error: input historical data should be ndarray, got {type(hist_data)}'
        # debug
        # print(f'hist data: \n{hist_data}')
        day, drop = self._pars
        h = hist_data
        diff = (h - np.roll(h, day)) / h
        diff[:day] = h[:day]
        # debug
        # print(f'input array got in Ricon.generate() is shaped {hist_data.shape}')
        # print(f'and the hist_data is converted to shape {h.shape}')
        # print(f'diff result:\n{diff}')
        # print(f'created array in ricon generate() is shaped {diff.shape}')
        # print(f'created array in ricon generate() is {np.where(diff < drop)}')
        return np.where(diff < drop, -1, 0).squeeze()


# Built in Selecting strategies:

class SelectingSimple(Selecting):
    """基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='SIMPLE SELECTING',
                         stg_text='Selecting all share and distribute weights evenly')

    def _realize(self, hist_data):
        # 所有股票全部被选中，投资比例平均分配
        share_count = hist_data.shape[0]
        return [1. / share_count] * share_count


class SelectingRandom(Selecting):
    """基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='RANDOM SELECTING',
                         stg_text='Selecting share Randomly and distribute weights evenly')

    def _realize(self, hist_data):
        pct = self.pars[0]
        share_count = hist_data.shape[0]
        if pct < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size=share_count, p=[pct, 1 - pct])
        else:  # pct >= 1 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(share_count, size=(int(pct)), replace=False)
            chosen = np.zeros(share_count)
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum()  # 投资比例平均分配


class SelectingFinance(Selecting):
    """ 根据所有股票的上期财报或过去多期财报中的某个指标选股，按照指标数值分配选股权重

        数据类型：由data_types指定的财报指标财报数据，单数据输入，默认数据为EPS
        数据分析频率：季度
        数据窗口长度：90
        策略使用3个参数:
            largest_win:    bool,   为真时选出EPS最高的股票，否则选出EPS最低的股票
            distribution:   str ,   确定如何分配选中股票的权重,
            drop_threshold: float,  确定丢弃值，丢弃当期EPS低于该值的股票
            pct:            float,  确定从股票池中选出的投资组合的数量或比例，当0<pct<1时，选出pct%的股票，当pct>=1时，选出pct只股票
        参数输入数据范围：[(True, False), ('even', 'linear', 'proportion'), (0, 100)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['enum', 'enum', 'discr', 'conti'],
                         par_bounds_or_enums=[(True, False), ('even', 'linear', 'proportion'), (0, 100), (0, 1)],
                         stg_name='FINANCE SELECTING',
                         stg_text='Selecting share_pool according to financial report EPS indicator',
                         data_freq='d',
                         sample_freq='y',
                         window_length=90,
                         data_types='eps')

    # TODO: 因为Strategy主类代码重构，ranking table的代码结构也应该相应修改，待修改
    def _realize(self, hist_data):
        """ 根据hist_segment中的EPS数据选择一定数量的股票

        """
        largest_win, distribution, drop_threshold, pct = self.pars
        share_count = hist_data.shape[0]
        if pct < 1:
            # pct 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            pct = int(share_count * pct)
        else:  # pct 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            pct = int(pct)
        # 历史数据片段必须是ndarray对象，否则无法进行
        assert isinstance(hist_data, np.ndarray), \
            f'TypeError: expect np.ndarray as history segment, got {type(hist_data)} instead'
        # 将历史数据片段中的eps求均值，忽略Nan值,
        indices = hist_data.mean(axis=1).squeeze()
        print(f'in Selecting realize method got ranking vector like:\n {indices: .3f}')
        nan_count = np.isnan(indices).astype('int').sum()  # 清点数据，获取nan值的数量
        if largest_win:
            # 选择分数最高的部分个股，由于np排序时会把NaN值与最大值排到一起，因此需要去掉所有NaN值
            pos = max(share_count - pct - nan_count, 0)
        else:  # 选择分数最低的部分个股
            pos = pct
        # 对数据进行排序，并把排位靠前者的序号存储在arg_found中
        if distribution == 'even':
            # 仅当投资比例为均匀分配时，才可以使用速度更快的argpartition方法进行粗略排序
            arg_found = indices.argpartition(pos)[pos:]
        else:  # 如果采用其他投资比例分配方式时，必须使用较慢的全排序
            arg_found = indices.argsort()[pos:]
        # nan值数据的序号存储在arg_nan中
        arg_nan = np.where(np.isnan(indices))[0]
        # 使用集合操作从arg_found中剔除arg_nan，使用assume_unique参数可以提高效率
        args = np.setdiff1d(arg_found, arg_nan, assume_unique=True)
        # 构造输出向量，初始值为全0
        chosen = np.zeros_like(indices)
        # 根据投资组合比例分配方式，确定被选中产品的占比
        # Linear：根据分值排序线性分配，分值最高者占比约为分值最低者占比的三倍，其余居中者的比例按序呈等差数列
        if distribution == 'linear':
            dist = np.arange(1, 3, 2. / len(args))  # 生成一个线性序列，最大值为最小值的约三倍
            chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
        # proportion：比例分配，占比与分值成正比，分值最低者获得一个基础比例，其余股票的比例与其分值成正比
        elif distribution == 'proportion':
            dist = indices[args]
            d = dist.max() - dist.min()
            if largest_win:
                dist = dist - dist.min() + d / 10.
            else:
                dist = dist.max() - dist + d / 10.
            chosen[args] = dist / dist.sum()
        # even：均匀分配，所有中选股票在组合中占比相同
        else:  # self.__distribution == 'even'
            chosen[args] = 1. / len(args)
        print(f'in Selecting realize method got share selecting vector like:\n {np.round(chosen,3)}')
        return chosen