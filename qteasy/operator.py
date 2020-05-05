# coding=utf-8
# operator.py

import pandas as pd
import numpy as np
from qteasy.utilfuncs import sma, ema, trix, macd, cdldoji
from qteasy import CashPlan
from abc import abstractmethod, ABCMeta
from .history import HistoryPanel
from .history import str_to_list


class Strategy:
    """ 量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的策略类调用

        类属性定义了策略类型、策略名称、策略关键属性的数量、类型和取值范围等
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
                 par_bounds_or_enums: list = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: [str, list] = ''):
        """ 初始化策略，赋予策略基本属性，包括策略的参数及其他控制属性

        input:
            :param pars: tuple,             策略参数, 动态参数
            :param opt_tag: int,            0: 参加优化，1: 不参加优化
            :param stg_type: str,           策略类型，可取值'TIMING', 'SELECTING', 'RICON'等
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
        self._pars = pars  # 策略的参数
        self._opt_tag = opt_tag  # 策略的优化标记
        self._stg_type = stg_type  # 策略类型
        self._stg_name = stg_name  # 策略的名称
        self._stg_text = stg_text  # 策略的描述文字
        self._par_count = par_count  # 策略参数的元素个数

        if par_types is None:
            # 当没有给出策略参数类型时，参数类型为空列表
            self._par_types = []
        else:
            # 输入的par_types可以允许为字符串或列表，当给定类型为字符串时，使用逗号分隔不同的类型，如
            # 'conti, conti' 代表 ['conti', 'conti']
            if isinstance(par_types, str):
                par_types = str_to_list(par_types, ',')
            assert isinstance(par_types, list), f'TypeError, par type should be a list, got {type(par_types)} instead'
            self._par_types = par_types
        if par_bounds_or_enums is None:
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
        """策略类型"""
        return self._stg_type

    @property
    def stg_name(self):
        """策略名称"""
        return self._stg_name

    @property
    def stg_text(self):
        """策略说明文本"""
        return self._stg_text

    @property
    def par_count(self):
        """策略的参数数量"""
        return self._par_count

    @property
    def par_types(self):
        """策略的参数类型，与Space类中的定义匹配，分为离散型'discr', 连续型'conti', 枚举型'enum'"""
        return self._par_types

    @property
    def par_boes(self):
        """策略的参数取值范围，用来定义参数空间用于参数优化"""
        return self._par_bounds_or_enums

    @property
    def opt_tag(self):
        """策略的优化类型"""
        return self._opt_tag

    @property
    def pars(self):
        """策略参数，元组"""
        return self._pars

    @property
    def data_freq(self):
        """策略依赖的历史数据频率"""
        return self._data_freq

    @property
    def sample_freq(self):
        """策略生成的采样频率"""
        return self._sample_freq

    @property
    def window_length(self):
        """策略依赖的历史数据窗口长度"""
        return self._window_length

    @property
    def data_types(self):
        """策略依赖的历史数据类型"""
        return self._data_types

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
        return self.__str__()

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
        if len(pars) == self.par_count or isinstance(pars, dict):
            self._pars = pars
            return 1
        else:
            raise ValueError(f'parameter setting error in set_pars() method of {self}\n expected par count: '
                             f'{self.par_count}, got {len(pars)}')
            return 0

    def set_opt_tag(self, opt_tag: int) -> int:
        """ 设置策略的优化类型

        input"
            :param opt_tag: int，0：不参加优化，1：参加优化
        :return:
        """
        self._opt_tag = opt_tag
        return opt_tag

    def set_par_boes(self, par_boes):
        """ 设置策略参数的取值范围

        input:
            :param par_boes: 策略的参数取值范围
        :return:
        """
        self._par_bounds_or_enums = par_boes
        return par_boes

    def set_hist_pars(self, sample_freq=None, window_length=None, data_types=None):
        """ 设置策略的历史数据回测相关属性

        :param sample_freq: str, 可以设置为'min'， 'd'等代表回测时的运行或采样频率
        :param window_length: int，表示回测时需要用到的历史数据深度
        :param data_types: str，表示需要用到的历史数据类型
        :return: None
        """
        if sample_freq is not None:
            self._sample_freq = sample_freq
        if window_length is not None:
            self._window_length = window_length
        if data_types is not None:
            self._data_types = data_types

    @abstractmethod
    def generate(self, hist_data: np.ndarray, shares: list, dates: list):
        """策略类的抽象方法，接受输入历史数据并根据参数生成策略输出"""
        raise NotImplementedError


# TODO: 以后可以考虑把Timing改为Alpha Model， Selecting改为Portfolio Manager， Ricon改为Risk Control
# ===============================
# TODO: 一种更好的实现Strategy参数的方法：取消strategy类的类属性，改为用__init__()方法初始化的对象属性，所有属性值通过初始化方法初始化
# TODO: 初始化方法参数给出默认值。这样在自定义每种策略的具体实现类的时候，就不需要通过类属性定义诸如par_count,data_freq等参数了，只需要
# TODO: 定义好_realize()方法即可，而其他的具体参数均可以在实例化策略对象的时候通过初始化参数给出即可
# ===============================
# TODO: 关于Selecting策略的改进：
# TODO: Selecting策略的选股周期和选股数量/比例两个参数作为Selecting类的固有参数放入__init__()方法中，并赋予默认值，同时将ranking table
# TODO: 所涉及到的一系列特殊属性转化为Selecting类的固有属性，同样放入初始化方法中。这样对于所有的selecting继承类，在realize的时候只需要
# TODO: 一个参数hist_data即可，share或dates参数都不再需要，都可以根据其他的固有属性动态生成。
# ===============================
# TODO: 关于Strategy策略的进一步改进：
# TODO: 所有策略中可以设置一个pre_process()预处理方法，把需要放到循环外的计算开销全部放入这个预处理方法中，在循坏外调用，以提升（优化）
# TODO: 的效率
# ===============================
class Timing(Strategy):
    """择时策略的抽象基类，所有择时策略都继承自该抽象类，本类继承自策略基类，同时定义了generate_one()抽象方法，用于实现具体的择时策略"""
    __mataclass__ = ABCMeta

    def __init__(self,
                 pars: tuple = None,
                 stg_name: str = 'NONE',
                 stg_text: str = 'intro text of timing strategy',
                 par_count: int = 0,
                 par_types: list = None,
                 par_bounds_or_enums: list = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: str = 'close'):
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
    def _realize(self, hist_pack, params):
        """ 策略的具体实现方法，在具体类中需要重写，是整个类的择时信号基本生成方法，针对单个个股的价格序列生成多空状态信号

            在择时类策略中，_realize方法接受一个历史数据片段hist_pack，其中包含的数据类型为self.data_types参数定义。
            hist_pack是一个numpy ndarray对象，包含M行N列数据，其中 M = self._window_length, N = len(self._data_types)
            这些数据代表投资产品在一个window_length长的历史区间内的历史价格数据，数据的频率为self.data_freq所指定。

            同时，params是一个元组，包含了应用于这一个投资产品的策略参数（由于同一个策略允许对不同的投资产品应用不同的策略参数，
            这里的策略参数已经被自动分配好了）。投资策略参数的个数为self.par_count所指定，每个投资参数的类型也为self.par_types
            所指定。

            在策略的实现方法中，需要做的仅仅是定义一种方法，根据hist_pack中给出的历史数据，作出关于这个投资产品在历史数据结束后紧
            接着的那个时刻的头寸位置（空头头寸还是多头头寸）。在择时策略的实现方法中，不需要考虑其他任何方面的问题，如交易品种、
            费率、比例等等，也不需要考虑历史数据中的缺陷如停牌等，只需要返回一个代表头寸位置的整数即可：
            返回1代表多头头寸，返回-1代表空头头寸，仅此而已

            qteasy系统会自行把适用于这个历史片段的策略，原样地推广到整个历史数据区间，同时推广到整个投资组合。并且根据投资组合管理
            策略（选股策略Selecting）中定义的选股方法确定每种投资产品的仓位比例。最终生成交易清单。
        input:
            :param hist_pack: ndarray，历史数据，策略的计算在历史数据基础上进行
            :param params: tuple, 策略参数，具体的策略输出结果依靠参数给出
        return:
            :L/S position: int, 一个代表头寸位置的整数，1代表多头头寸，0代表中性，-1代表空头头寸
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
        # 获取输入的历史数据切片中的NaN值位置，提取出所有部位NAN的数据，应用generate_one()函数
        if len(hist_slice.shape) == 2:
            drop = ~np.isnan(hist_slice[:, 0])
        else:
            drop = ~np.isnan(hist_slice)
        # 生成输出值一维向量
        cat = np.zeros(hist_slice.shape[0])
        hist_nonan = hist_slice[drop]  # 仅针对非nan值计算，忽略股票停牌时期
        loop_count = len(hist_nonan) - self.window_length + 1
        if loop_count < 1:  # 在开始应用generate_one()
            return cat

        # 开始进行历史数据的滚动展开
        hist_pack = np.zeros((loop_count, *hist_nonan[:self._window_length].shape))
        for i in range(loop_count):
            hist_pack[i] = hist_nonan[i:i + self._window_length]
        # 滚动展开完成，形成一个新的3D或2D矩阵
        # 开始将参数应用到策略实施函数generate中
        par_list = [pars] * loop_count
        res = np.array(list(map(self._realize,
                                hist_pack,
                                par_list)))
        # 生成的结果缺少最前面window_length那一段，因此需要补齐
        capping = np.zeros(self._window_length - 1)
        # print(f'in Timing.generate_over() function shapes of res and capping are {res.shape}, {capping.shape}')
        res = np.concatenate((capping, res), 0)
        # 将结果填入原始数据中不为Nan值的部分，原来为NAN值的部分保持为0
        cat[drop] = res
        # print(f'created long/short mask for current hist_slice is: \n{cat[self.window_length:][:100]}')
        return cat[self.window_length:]

    def generate(self, hist_data: np.ndarray, shares=None, dates=None):
        """ 生成整个股票价格序列集合的多空状态历史矩阵

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
        # print(f'hist_data got in Timing.generate() function is shaped {hist_data.shape}')
        # 检查输入数据的正确性：检查数据类型和历史数据的总行数应大于策略的数据视窗长度，否则无法计算策略输出
        assert isinstance(hist_data, np.ndarray), f'Type Error: input should be ndarray, got {type(hist_data)}'
        assert len(hist_data.shape) == 3, \
            f'DataError: historical data should be 3 dimensional, got {len(hist_data.shape)} dimensional data'
        assert hist_data.shape[1] >= self._window_length, \
            f'DataError: Not enough history data! expected hist data length {self._window_length},' \
            f' got {hist_data.shape[1]}'
        pars = self._pars
        # 当需要对不同的股票应用不同的参数时，参数以字典形式给出，判断参数的类型
        # print(f'in Timing.generate() pars is a {type(pars)}, value is {pars}')
        if isinstance(pars, dict):
            par_list = pars.values()  # 允许使用dict来为不同的股票定义不同的策略参数
        else:
            par_list = [pars] * hist_data.shape[0]  # 生成长度与shares数量相同的序列
        # 调用_generate_over()函数，生成每一只股票的历史多空信号清单，用map函数把所有的个股数据逐一传入计算，并用list()组装结果
        # print(len(par_list), len(hist_data))
        assert len(par_list) == len(hist_data), \
            f'InputError: can not map {len(par_list)} parameters to {len(hist_data)} shares!'
        res = np.array(list(map(self._generate_over,
                                hist_data,
                                par_list))).T

        # print(f'generate result of np timing generate, result shaped {res.shape}')
        # 每个个股的多空信号清单被组装起来成为一个完整的多空信号矩阵，并返回
        return res


class TimingSimple(Timing):
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

    def _realize(self, hist_price, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return 1


class TimingCrossline(Timing):
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
                         stg_text='Moving average crossline strategy, determin long/short position according to the ' \
                                  'cross point of long and short term moving average prices ',
                         data_types='close')

    def _realize(self, hist_price, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        # 计算长短均线之间的距离
        diff = sma(h[0], l) - sma(h[0], s)
        # 根据观望模式在不同的点位产生Long/short标记
        if hesitate == 'buy':
            cat = np.where(diff < -m, 1, 0)
        elif hesitate == 'sell':
            cat = np.where(diff < m, 1, 0)
        else:  # hesitate == 'none'
            cat = np.where(diff < 0, 1, 0)
        return cat[-1]


class TimingMACD(Timing):
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

    def _realize(self, hist_price, params):
        """生成单只个股的择时多空信号.

        输入:
            idx: 指定的参考指数历史数据
            sRange, 短均线参数，短均线的指数移动平均计算窗口宽度，单位为日
            lRange, 长均线参数，长均线的指数移动平均计算窗口宽度，单位为日
            dRange, DIFF的指数移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """

        s, l, m = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T

        # 计算指数的指数移动平均价格
        diff = ema(h[0], s) - ema(h[0], l)
        dea = ema(diff, m)
        macd = 2 * (diff - dea)
        # diff, dea, macd = macd(hist_price, s, l, m)

        # 生成MACD多空判断：
        # 1， MACD柱状线为正，多头状态，为负空头状态：由于MACD = diff - dea
        cat = np.where(macd > 0, 1, 0)
        return cat[-1]


class TimingDMA(Timing):
    """DMA择时策略

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

    def _realize(self, hist_price, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick dma Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)
        # print('qDMA generated DMA and ama signal:', dma.size, dma, '\n', ama.size, ama)
        # 生成DMA多空判断：
        # 1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        # 2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        # 3， DMA与股价发生背离时的交叉信号，可信度较高
        cat = np.where(dma > ama, 1, 0)
        # print('qDMA generate category data with as type', cat.size, cat)
        return cat[-1]


class TimingTRIX(Timing):
    """TRIX择时策略，运用TRIX均线策略，利用历史序列上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270天
    策略使用2个参数，
        s: int,
        m: int
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

    def _realize(self, hist_price, params):
        """参数:

        input:
        :param idx: 指定的参考指数历史数据
        :param sRange, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        :param mRange, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """
        s, m = params
        # print 'Generating trxi Long short Mask with parameters', params

        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        trxi = trix(h[0], s)
        matrix = sma(trxi, m)

        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = 1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 0
        cat = np.where(trxi > matrix, 1, 0)
        return cat[-1]  # 返回时填充日期序列恢复nan值


class TimingCDL(Timing):
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

    def _realize(self, hist_price, params=None):
        """参数:

        input:
            None
        """
        # 计算历史数据上的CDL指标
        h = hist_price.T
        cat = (cdldoji(h[0], h[1], h[2], h[3]).cumsum() // 100)

        return float(cat[-1])


# TODO: 修改Selecting策略的结构，以支持更加统一的编码风格：generate()方法仅接受历史数据，realize()方法定义选股实现算法，通过静态属性
# TODO: 设置数据类型、数据频率和采样频率，策略参数仅仅跟选股实现算法有关
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
                 par_types: list = None,
                 par_bounds_or_enums: list = None,
                 data_freq: str = 'y',
                 sample_freq: str = 'y',
                 proportion_or_quantity: float = 0.5,
                 window_length: int = 270,
                 data_types: str = 'close'):
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
    def _realize(self, hist_segment):
        """" Selecting 类的选股抽象方法，在不同的具体选股类中应用不同的选股方法，实现不同的选股策略

        input:
            :param hist_segment: type: ndarray, 一个历史数据片段，包含N个股票的data_types种数据在window_length日内的历史数据片段
        :return
            ndarray, 一个一维向量，代表一个周期内股票选择权重，整个向量经过归一化，即所有元素之和为1
        """
        pass

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
        assert isinstance(dates, list), \
            f'TypeError, type list expected in method seg_periods, got {type(dates)} instead! '
        bnds = pd.date_range(start=dates[0], end=dates[-1], freq=freq)
        # 写入第一个选股区间分隔位——0
        seg_pos = np.zeros(shape=(len(bnds) + 2), dtype='int')
        # print(f'in module selecting: function seg_perids: comparing {dates[0]} and {bnds[0]}')
        # 用searchsorted函数把输入的日期与历史数据日期匹配起来
        seg_pos[1:-1] = np.searchsorted(dates, bnds)
        # 最后一个分隔位等于历史区间的总长度
        seg_pos[-1] = len(dates) - 1
        # print('Results check, selecting - segment creation, segments:', seg_pos)
        # 计算每个分段的长度
        seg_lens = (seg_pos - np.roll(seg_pos, 1))[1:]
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
        freq = self.sample_freq
        # 获取完整的历史日期序列，并按照选股频率生成分段标记位，完整历史日期序列从参数获得，股票列表也从参数获得
        # TODO: 这里的选股分段可以与Timing的Rolling Expansion整合，同时避免使用dates和freq，使用self.sample_freq属性
        seg_pos, seg_lens, seg_count = self._seg_periods(dates, freq)
        # 一个空的ndarray对象用于存储生成的选股蒙版
        sel_mask = np.zeros(shape=(len(dates), len(shares)), order='C')
        seg_start = 0

        # 针对每一个选股分段区间内生成股票在投资组合中所占的比例
        # TODO: 可以使用map函数生成分段
        for sp, sl in zip(seg_pos, seg_lens):
            # share_sel向量代表当前区间内的投资组合比例
            share_sel = self._realize(hist_data[:, sp:sp + sl, :])
            seg_end = seg_start + sl
            # 填充相同的投资组合到当前区间内的所有交易时间点
            sel_mask[seg_start:seg_end + 1, :] = share_sel
            seg_start = seg_end
        # 将所有分段组合成完整的ndarray
        return sel_mask


class SelectingTrend(Selecting):
    """趋势选股策略，继承自选股策略类"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='TREND SELECTING',
                         stg_text='Selecting share according to detected trends')

    def _realize(self, hist_segment):
        # 所有股票全部被选中，权值（投资比例）平均分配
        print(f'in selecting realize method, hist_segment received, shaped: {hist_segment.shape}')
        share_count = hist_segment.shape[0]
        return [1. / share_count] * share_count


class SelectingSimple(Selecting):
    """基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='SIMPLE SELECTING',
                         stg_text='Selecting all share and distribute weights evenly')

    def _realize(self, hist_segment):
        # 所有股票全部被选中，投资比例平均分配
        share_count = hist_segment.shape[0]
        return [1. / share_count] * share_count


class SelectingRandom(Selecting):
    """基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='RANDOM SELECTING',
                         stg_text='Selecting share Randomly and distribute weights evenly')

    def _realize(self, hist_segment):
        pct = self.pars[0]
        share_count = hist_segment.shape[0]
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
        策略使用2个参数:
            :param largest_win: boolean 为真时选出EPS最高的股票，否则选出EPS最低的股票
            :param distribution: str 确定如何分配选中股票的权重,
            :param drop_threshold: 确定丢弃值，丢弃当期EPS低于该值的股票
        参数输入数据范围：[('even', 'linear', 'proportion'), (0, 100)]
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
    # TODO：实际上hist_segment就起到了ranking table 的作用，因此不再需要ranking_table()方法，所有排序都在_realize()方法中实现
    def _realize(self, hist_segment):
        """ 根据hist_segment中的EPS数据选择一定数量的股票

        """
        largest_win, distribution, drop_threshold, pct = self.pars
        share_count = hist_segment.shape[0]
        if pct < 1:
            # pct 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            pct = int(share_count * pct)
        else:  # pct 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            pct = int(pct)
        # 历史数据片段必须是ndarray对象，否则无法进行
        assert isinstance(hist_segment, np.ndarray), \
            f'TypeError: expect np.ndarray as history segment, got {type(hist_segment)} instead'
        # 将历史数据片段中的eps求均值，忽略Nan值,
        indices = hist_segment.mean(axis=1).squeeze()
        print(f'in Selecting realize method got ranking vector like:\n {np.round(indices, 3)}')
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


class Ricon(Strategy):
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
                 par_types: list = None,
                 par_bounds_or_enums: list = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: str = 'close'):
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
    def _realize(self, hist_data, shares, dates):
        raise NotImplementedError

    def generate(self, hist_data, shares=None, dates=None):
        return self._realize(hist_data, shares, dates)


class RiconNone(Ricon):
    """无风险控制策略，不对任何风险进行控制"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='NONE',
                         stg_text='Do not take any risk control activity')

    def _realize(self, hist_data, shares=None, dates=None):
        return np.zeros_like(hist_data[:, :, 0].T)


class RiconUrgent(Ricon):
    """urgent风控类，继承自Ricon类，重写_generate_ricon方法"""

    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(1, 40), (-0.5, 0.5)],
                         stg_name='URGENT',
                         stg_text='Generate selling signal when N-day drop rate reaches target')

    def _realize(self, hist_data, shares, dates):
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
        day, drop = self._pars
        h = hist_data[:, :, 0].T
        # print(f'input array got in Ricon.generate() is shaped {hist_data.shape}')
        # print(f'and the hist_data is converted to shape {h.shape}')
        diff = (h - np.roll(h, day)) / h
        diff[:day] = h[:day]
        # print(f'created array in ricon generate() is shaped {diff.shape}')
        # print(f'created array in ricon generate() is {np.where(diff < drop)}')
        return np.where(diff < drop, -1, 0)


# TODO：
# TODO：作为完整的交易信号，为了实现更加贴近实际的交易信号，交易信号应该包括交易方向和头寸位置两个主要参数（对于股票来说
# TODO：只有多头头寸）
# TODO：position > 0时，表示多头头寸
# TODO：position < 0时，表示空头头寸
# TODO：两种不同的头寸位置配合开仓（signal>0）或平仓（signal<0）才能完整地表示所有的交易方式
# TODO：另外，还需要加入更多交易相关信息，如限价单、市价单、交易数量等等，总之，之前仅用singal表示交易信号的方式太过于简单了
def _mask_to_signal(lst):
    """将持仓蒙板转化为交易信号.

        转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
        则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
        生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
        signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
            现金总额不足，则按比例调降买入比率，直到用尽现金。
        signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
        signal = 0时，表示不进行任何操作



    input:
        :param lst，ndarray，持仓蒙板
    return: =====
        op，ndarray，交易信号矩阵
    """

    # 比较本期交易时间点和上期之间的持仓比率差额，差额大于0者可以直接作为补仓买入信号，如上期为0.35，
    # 本期0.7，买入信号为0.35，即使用总资金的35%买入该股，加仓到70%
    op = (lst - np.roll(lst, shift=1, axis=0))
    # 差额小于0者需要计算差额与上期持仓数之比，作为卖出信号的强度，如上期为0.7，本期为0.35，差额为-0.35，则卖出信号强度
    # 为 (0.7 - 0.35) / 0.35 = 0.5即卖出50%的持仓数额，从70%仓位减仓到35%
    op = np.where(op < 0, (op / np.roll(lst, shift=1, axis=0)), op)
    # 补齐因为计算差额导致的第一行数据为NaN值的问题
    # print(f'creating operation signals, first signal is {lst[0]}')
    op[0] = lst[0]
    return op


# TODO：legalize函数将不再需要，理由有2，其一，风控策略能够从策略层面对交易信号进行控制，事实上与legalize函数作用相同，功能可以合并，
# TODO：其二，通过设置sample_freq参数，交易信号的生成已经自动符合T+1规则了
def _legalize(lst):
    """交易信号合法化，整理生成的交易信号，使交易信号符合规则.

    根据历史数据产生的交易信号不一定完全符合实际的交易规则，在必要时需要对交易信号进行
    修改，以确保最终的交易信号符合交易规则，这里的交易规则仅包含与交易时间相关的规则如T+1规则等，与交易
    成本或交易量相关的规则如费率、MOQ等都在回测模块中考虑"""

    # 最基本的操作规则是不允许出现大于1或者小于-1的交易信号
    return lst.clip(-1, 1)


def _timing_blend_change(ser: np.ndarray):
    """ 多择时策略混合模式——变动计数混合

    当发生状态反转的择时策略个数达到N个时，及触发状态反转
    input:
        :type ser: object np.ndarray
    return:
        ndarray: 混合后的择时策略输出
    """
    if ser[0] > 0:
        state = 1
    else:
        state = 0
    res = np.zeros_like(ser)
    prev = ser[0]
    for u, v in np.nditer([res, ser], op_flags=['readwrite']):
        if v < prev:
            state = 0
        elif v > prev:
            state = 1
        u[...] = state
        prev = v
    return res


def _blend(n1, n2, op):
    """混合操作符函数，将两个选股、多空蒙板混合为一个

    input:
        :param n1: np.ndarray: 第一个输入矩阵
        :param n2: np.ndarray: 第二个输入矩阵
        :param op: np.ndarray: 运算符
    return:
        :return: np.ndarray

    """
    if op == 'or':
        return n1 + n2
    elif op == 'and':
        return n1 * n2


def unify(arr):
    """调整输入矩阵每一行的元素，通过等比例缩小（或放大）后使得所有元素的和为1

    example:
    unify([[3.0, 2.0, 5.0], [2.0, 3.0, 5.0]])
    =
    [[0.3, 0.2, 0.5], [0.2, 0.3, 0.5]]

    :param arr: type: np.ndarray
    :return: ndarray
    """
    assert isinstance(arr, np.ndarray), f'InputError: Input should be ndarray! got {type(arr)}'
    s = arr.sum(1)
    shape = (s.shape[0], 1)
    return arr / s.reshape(shape)


class Operator:
    """交易操作生成类，通过简单工厂模式创建择时属性类和选股属性类，并根据这两个属性类的结果生成交易清单

    交易操作生成类包含若干个选股对象组件，若干个择时对象组件，以及若干个风险控制组件，所有这些组件对象都能
    在同一组历史数据对象上进行相应的选股操作、择时操作并进行风控分析。不同的选股或择时对象工具独立地在历史数据
    对象上生成选股蒙版或多空蒙版，这些独立的选股蒙版及多空蒙版又由不同的方式混合起来（通过交易操作对象的蒙版
    混合属性确定，其中选股蒙版混合属性是一个逻辑表达式，根据这个逻辑表达式用户可以确定所有的蒙版的混合方式，
    例如“0 or （ 1 and （ 2 and 3 ） or 4 ）”；多空信号的生成方式是三个生成选项之一）。

    择时类的混合方式有：
        pos-N：只有当大于等于N个策略看多时，输出为看多，否则为看空
        chg-N：在某一个多空状态下，当第N个反转信号出现时，反转状态
        cumulate：没有绝对的多空状态，给每个策略分配同样的权重，当所有策略看多时输出100%看多，否则
        输出的看多比例与看多的策略的权重之和相同，当多空状态发生变化时会生成相应仓位的交易信号

    综合应用所有择时选股风控策略在目标历史数据上后生成的一个交易信号记录，交易信号经过合法性修改后成为
    一个最终输出的合法交易记录（信号）

    """

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表
    def __init__(self, selecting_types=None,
                 timing_types=None,
                 ricon_types=None):
        """根据输入的参数生成选股、择时和风控具体类:

        input:
            :param selecting_types: 一个包含多个字符串的列表，表示不同选股策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
            :param timing_types: 字符串列表，表示不同择时策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
            :param ricon_types: 字符串列表，表示不同风控策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
        """
        # 对象属性：
        # 交易信号通用属性：

        self.__Tp0 = False  # 是否允许T+0交易，True时允许T+0交易，否则不允许
        # 交易策略属性：
        # 对象的timings属性和timing_types属性都是列表，包含若干策略而不是一个策略
        if selecting_types is None:
            selecting_types = ['simple']
        if timing_types is None:
            timing_types = ['simple']
        if ricon_types is None:
            ricon_types = ['none']
        self._timing_types = []
        self._timing = []
        self._timing_history_data = []
        self._timing_blender = 'pos-1'  # 默认的择时策略混合方式
        for timing_type in timing_types:
            # 通过字符串比较确认timing_type的输入参数来生成不同的具体择时策略对象，使用.lower()转化为全小写字母
            self._timing_types.append(timing_type)
            if timing_type.lower() == 'cross_line':
                self._timing.append(TimingCrossline())
            elif timing_type.lower() == 'macd':
                self._timing.append(TimingMACD())
            elif timing_type.lower() == 'dma':
                self._timing.append(TimingDMA())
            elif timing_type.lower() == 'trix':
                self._timing.append(TimingTRIX())
            elif timing_type.lower() == 'cdl':
                self._timing.append(TimingCDL())
            elif timing_type.lower() == 'simple':
                self._timing.append((TimingSimple()))
            else:
                raise TypeError(f'The timing strategy type \'{timing_type}\' can not be recognized!')
        # 根据输入参数创建不同的具体选股策略对象。selecting_types及selectings属性与择时策略对象属性相似
        # 都是列表，包含若干相互独立的选股策略（至少一个）
        self._selecting_type = []
        self._selecting = []
        self._selecting_history_data = []
        # 选股策略的混合方式使用以下字符串描述。简单来说，每个选股策略都独立地生成一个选股蒙版，每个蒙版与其他的
        # 蒙版的混合方式要么是OR（+）要么是AND（*），最终混合的结果取决于这些蒙版的混合方法和混合顺序而多个蒙版
        # 的混合方式就可以用一个类似于四则运算表达式的方式来描述，例如“（ 0 + 1 ） * （ 2 + 3 * 4 ）”
        # 在操作生成模块中，有一个表达式解析器，通过解析四则运算表达式来解算selecting_blender_string，并将混
        # 合的步骤以前缀表达式的方式存储在selecting_blender中，在混合时按照前缀表达式的描述混合所有蒙版。注意
        # 表达式中的数字代表selectings列表中各个策略的索引值
        cur_type = 0
        str_list = []

        for selecting_type in selecting_types:
            self._selecting_type.append(selecting_type)
            if cur_type == 0:
                str_list.append(str(cur_type))
            else:
                str_list.append(f' or {str(cur_type)}')
            cur_type += 1
            if selecting_type.lower() == 'trend':
                self._selecting.append(SelectingTrend())
            elif selecting_type.lower() == 'random':
                self._selecting.append(SelectingRandom())
            elif selecting_type.lower() == 'finance':
                self._selecting.append(SelectingFinance())
            elif selecting_type.lower() == 'simple':
                self._selecting.append(SelectingSimple())
            else:
                raise TypeError(f'The selecting type \'{selecting_type}\' can not be recognized!')
        self._selecting_blender_string = ''.join(str_list)
        # create selecting blender by selecting blender string
        self._selecting_blender = self._exp_to_blender

        # 根据输入参数生成不同的风险控制策略对象
        self._ricon_type = []
        self._ricon = []
        self._ricon_history_data = []
        self._ricon_blender = 'add'
        for ricon_type in ricon_types:
            self._ricon_type.append(ricon_type)
            if ricon_type.lower() == 'none':
                self._ricon.append(RiconNone())
            elif ricon_type.lower() == 'urgent':
                self._ricon.append(RiconUrgent())
            else:
                raise TypeError(f'The risk control strategy \'{ricon_type}\' can not be recognized!')

    @property
    def timing(self):
        return self._timing

    @property
    def selecting(self):
        return self._selecting

    @property
    def ricon(self):
        return self._ricon

    @property
    def strategies(self):
        stg = []
        stg.extend(self.timing)
        stg.extend(self.selecting)
        stg.extend(self.ricon)
        return stg

    @property
    def get_opt_space_par(self):
        ranges = []
        types = []
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass  # 策略优化方案关闭
            elif stg.opt_tag == 1:
                ranges.extend(stg.par_boes)
                types.extend(stg.par_types)
            elif stg.opt_tag == 2:
                ranges.append(stg.par_boes)
                types.extend(['enum'])
        return ranges, types

    @property
    def max_window_length(self):
        """ find out max window length in all strategies

        :return:
        """
        max_wl = 0
        for stg in self.strategies:
            if stg.window_length > max_wl:
                max_wl = stg.window_length
        return max_wl

    # Operation对象有两类属性需要设置：blender混合器属性、Parameters策略参数或属性
    # 这些属性参数的设置需要在OP模块设置一个统一的设置入口，同时，为了实现与Optimizer模块之间的接口
    # 还需要创建两个Opti接口函数，一个用来根据的值创建合适的Space初始化参数，另一个用于接受opt
    # 模块传递过来的参数，分配到合适的策略中去
    # TODO: convert all parameter setting functions to private except one single entry-function set_parameter()
    def set_blender(self, blender_type, *args, **kwargs):
        # 统一的blender混合器属性设置入口
        if isinstance(blender_type, str):
            if blender_type.lower() == 'selecting':
                self._set_selecting_blender(*args, **kwargs)
            elif blender_type.lower() == 'timing':
                self._set_timing_blender(*args, **kwargs)
            elif blender_type.lower() == 'ricon':
                self._set_ricon_blender(*args, **kwargs)
            else:
                print('wrong input!')
                pass
        else:
            print('blender_type should be a string')
        pass

    def set_parameter(self, stg_id,
                      pars=None,
                      opt_tag=None,
                      par_boes=None,
                      sample_freq=None,
                      window_length=None,
                      data_types=None):
        """统一的策略参数设置入口，stg_id标识接受参数的具体成员策略
           stg_id的格式为'x-n'，其中x为's/t/r'中的一个字母，n为一个整数

           :param stg_id:
           :param pars:
           :param opt_tag:
           :param par_boes:
           :return:

        """
        if isinstance(stg_id, str):
            l = stg_id.split('-')
            if l[0].lower() == 's':
                strategy = self.selecting[int(l[1])]
            elif l[0].lower() == 't':
                strategy = self.timing[int(l[1])]
            elif l[0].lower() == 'r':
                strategy = self.ricon[int(l[1])]
            else:
                print(f'InputError: The identifier of strategy is not recognized, should be like \'t-0\', got {stg_id}')
                return None
            if pars is not None:
                if strategy.set_pars(pars):
                    print(f'{strategy} parameter has been set to {pars}')
                else:
                    print(f'parameter setting error')
            if opt_tag is not None:
                strategy.set_opt_tag(opt_tag)
                print(f'{strategy} optimizaiton tag has been set to {opt_tag}')
            if par_boes is not None:
                strategy.set_par_boes(par_boes)
                print(f'{strategy} parameter space range or enum has been set to {par_boes}')
            has_sf = sample_freq is not None
            has_wl = window_length is not None
            has_dt = data_types is not None
            if has_sf or has_wl or has_dt:
                strategy.set_hist_pars(sample_freq=sample_freq,
                                       window_length=window_length,
                                       data_types=data_types)
                print(f'{strategy} history looping parameter has been set to:\n sample frequency: {sample_freq}\n',
                      f'window length: {window_length} \ndata types: {data_types}')
        else:
            print('stg_id should be a string like \'t-0\', got {stg_id}')
        pass

    # =================================================
    # 下面是Operation模块的公有方法：
    def info(self):
        """# 打印出当前交易操作对象的信息，包括选股、择时策略的类型，策略混合方法、风险控制策略类型等等信息
        # 如果策略包含更多的信息，还会打印出策略的一些具体信息，如选股策略的信息等
        # 在这里调用了私有属性对象的私有属性，不应该直接调用，应该通过私有属性的公有方法打印相关信息
        # 首先打印Operation木块本身的信息"""
        print('OPERATION MODULE INFO:')
        print('=' * 25)
        print('Information of the Module')
        print('=' * 25)
        # 打印各个子模块的信息：
        # 首先打印Selecting模块的信息
        print('Total count of Selecting strategies:', len(self._selecting))
        print('the blend type of selecting strategies is', self._selecting_blender_string)
        print('Parameters of Selecting Strategies:')
        for sel in self.selecting:
            sel.info()
        print('=' * 25)

        # 接着打印 timing模块的信息
        print('Total count of timing strategies:', len(self._timing))
        print('The blend type of timing strategies is', self._timing_blender)
        print('Parameters of timing Strategies:')
        for tmg in self.timing:
            tmg.info()
        print('=' * 25)

        # 最后打印Ricon模块的信息
        print('Total count of Risk Control strategies:', len(self._ricon))
        print('The blend type of Risk Control strategies is', self._ricon_blender)
        for ric in self.ricon:
            ric.info()
        print('=' * 25)

    # TODO 临时性使用cashplan作为参数之一，理想中应该只用一个"start_date"即可，这个Start_date可以在core.run()中具体指定，因为
    # TODO 在不同的运行模式下，start_date可能来源是不同的：
    def prepare_data(self, hist_data: HistoryPanel, cash_plan: CashPlan):
        """ 在create_signal之前准备好相关数据如历史数据，检查历史数据是否符合所有策略的要求：

        检查hist_data历史数据的类型正确；
        检查cash_plan投资计划的类型正确；
        检查hist_data是否为空（要求不为空）；
        在hist_data中找到cash_plan投资计划中投资时间点的具体位置
        检查cash_plan投资计划中第一次投资时间点前有足够的数据量，用于滚动回测
        检查cash_plan投资计划中最后一次投资时间点在历史数据的范围内
        从hist_data中根据各个量化策略的参数选取正确的切片放入各个策略数据仓库中

        :param hist_data: 历史数据
        :param cash_plan:
        :return:
        """
        assert isinstance(hist_data, HistoryPanel), \
            f'TypeError: historical data should be HistoryPanel, got {type(hist_data)}'
        assert isinstance(cash_plan, CashPlan), \
            f'TypeError: cash plan should be CashPlan object, got {type(cash_plan)}'
        assert not hist_data.is_empty, \
            f'ValueError: history data can not be empty!'
        first_cash_pos = np.searchsorted(hist_data.hdates, cash_plan.first_day)
        last_cash_pos = np.searchsorted(hist_data.hdates, cash_plan.last_day)
        # debug
        # print(f'first and last cash pos: {first_cash_pos}, {last_cash_pos}')
        assert first_cash_pos >= self.max_window_length, \
            f'InputError, Not enough history data records on first cash date, expect {self.max_window_length},' \
            f' got {first_cash_pos} records only'
        assert last_cash_pos < len(hist_data.hdates), \
            f'InputError, Not enough history data record to cover complete investment plan, history data ends ' \
            f'on {hist_data.hdates[-1]}, last investment on {cash_plan.last_day}'
        for stg in self.selecting:
            self._selecting_history_data.append(hist_data[stg.data_types, :, first_cash_pos:])
            # print(f'slicing historical data {len(hist_data.hdates)} - {first_cash_pos} = '
            #      f'{len(hist_data.hdates) - first_cash_pos}'
            #      f' rows for selecting strategies')
        for stg in self.timing:
            start_pos = first_cash_pos - stg.window_length
            self._timing_history_data.append(hist_data[stg.data_types, :, start_pos:])
            # print(f'slicing historical data {len(hist_data.hdates)} - {first_cash_pos} = '
            #      f'{len(hist_data.hdates) - first_cash_pos}'
            #      f' rows for timing strategies')
        for stg in self.ricon:
            self._ricon_history_data.append(hist_data[stg.data_types, :, first_cash_pos:])
            # print(f'slicing historical data {len(hist_data.hdates)} - {first_cash_pos} = '
            #      f'{len(hist_data.hdates) - first_cash_pos}'
            #      f' rows for ricon strategies')

    # TODO: 供回测或实盘交易的交易信号应该转化为交易订单，并支持期货交易，因此生成的交易订单应该包含四类：
    # TODO: 1，Buy-开多仓，2，sell-平多仓，3，sel_short-开空仓，4，buy_to_cover-平空仓
    # TODO: 应该创建标准的交易订单模式，并且通过一个函数把交易信号转化为交易订单，以供回测或实盘交易使用
    def create_signal(self, hist_data: HistoryPanel):
        """ 操作信号生成方法，在输入的历史数据上分别应用选股策略、择时策略和风险控制策略，生成初步交易信号后，

        对信号进行合法性处理，最终生成合法交易信号
        input:
            hist_data：从数据仓库中导出的历史数据，包含多只股票在一定时期内特定频率的一组或多组数据
        :return=====
            lst：使用对象的策略在历史数据期间的一个子集上产生的所有合法交易信号，该信号可以输出到回测
            模块进行回测和评价分析，也可以输出到实盘操作模块触发交易操作
        """
        # 第一步，在历史数据上分别使用选股策略独立产生若干选股蒙板（sel_mask）
        # 选股策略的所有参数都通过对象属性设置，因此在这里不需要传递任何参数
        import time
        sel_masks = []
        shares = hist_data.shares
        date_list = hist_data.hdates
        assert isinstance(hist_data, HistoryPanel), \
            f'Type Error: historical data should be HistoryPanel, got {type(hist_data)}'
        assert len(self._timing_history_data) > 0, \
            f'ObjectSetupError: history data should be set before signal creation!'
        assert len(self._ricon_history_data) > 0, \
            f'ObjectSetupError: history data should be set before signal creation!'
        st = time.clock()
        for sel, dt in zip(self._selecting, self._selecting_history_data):  # 依次使用选股策略队列中的所有策略逐个生成选股蒙板
            # print('SPEED test OP create, Time of sel_mask creation')
            history_length = dt.shape[1]
            sel_masks.append(
                sel.generate(hist_data=dt, shares=shares, dates=date_list[-history_length:]))  # 生成的选股蒙板添加到选股蒙板队列中
        et = time.clock()
        # print(f'time elapsed for operator.create_signal.Selecting strategy: {et-st:.5f}')
        sel_mask = self._selecting_blend(sel_masks)  # 根据蒙板混合前缀表达式混合所有蒙板
        # print(f'Sel_mask has been created! shape is {sel_mask.shape}')
        # print(f'Sel-mask has been created! mask is\n{sel_mask[:100]}')
        # sel_mask.any(0) 生成一个行向量，每个元素对应sel_mask中的一列，如果某列全部为零，该元素为0，
        # 乘以hist_extract后，会把它对应列清零，因此不参与后续计算，降低了择时和风控计算的开销
        # TODO: 这里本意是筛选掉未中选的股票，降低择时计算的开销，使用新的数据结构后不再适用，需改进以使其适用
        # hist_selected = hist_data * selected_shares
        # 第二步，使用择时策略在历史数据上独立产生若干多空蒙板(ls_mask)
        st = time.clock()
        ls_masks = []
        for tmg, dt in zip(self._timing, self._timing_history_data):  # 依次使用择时策略队列中的所有策略逐个生成多空蒙板
            # 生成多空蒙板时忽略在整个历史考察期内从未被选中过的股票：
            # print('SPEED test OP create, Time of ls_mask creation')
            ls_masks.append(tmg.generate(dt))
            # print(tmg.generate(h_v))
            # print('ls mask created: ', tmg.generate(hist_selected).iloc[980:1000])
        et = time.clock()
        # print(f'time elapsed for operator.create_signal.Timing Strategy: {et-st:.5f}')
        ls_mask = self._timing_blend(ls_masks)  # 混合所有多空蒙板生成最终的多空蒙板
        # print(f'Long/short_mask has been created! shape is {ls_mask.shape}')
        # print('\n long/short mask: \n', ls_mask[:100])
        # print 'Time measurement: risk-control_mask creation'
        # 第三步，风险控制交易信号矩阵生成（简称风控矩阵）
        st = time.clock()
        ricon_mats = []
        for ricon, dt in zip(self._ricon, self._ricon_history_data):  # 依次使用风控策略队列中的所有策略生成风险控制矩阵
            # print('SPEED test OP create, Time of ricon_mask creation')
            ricon_mats.append(ricon.generate(dt))  # 所有风控矩阵添加到风控矩阵队列
        et = time.clock()
        # print(f'time elapsed for operator.create_signal.Ricon Strategy: {et-st:.5f}')
        ricon_mat = self._ricon_blend(ricon_mats)  # 混合所有风控矩阵后得到最终的风控策略
        # print(f'risk control_mask has been created! shape is {ricon_mat.shape}')
        # print('risk control matrix \n', ricon_mat[:100])
        # print (ricon_mat)
        # print('sel_mask * ls_mask: \n', (ls_mask * sel_mask)[:100])
        # 使用mask_to_signal方法将多空蒙板及选股蒙板的乘积（持仓蒙板）转化为交易信号，再加上风控交易信号矩阵，并对交易信号进行合法化
        # print('SPEED test OP create, Time of operation mask creation')
        # %time self._legalize(self._mask_to_signal(ls_mask * sel_mask) + (ricon_mat))
        op_mat = _legalize(_mask_to_signal(ls_mask * sel_mask) + ricon_mat)
        # print(f'Finally op mask has been created, shaped {op_mat.shape}')
        date_list = hist_data.hdates[-op_mat.shape[0]:]
        # print(f'length of date_list: {len(date_list)}')
        lst = pd.DataFrame(op_mat, index=date_list, columns=shares)
        # print('operation matrix: \n', lst.loc[lst.any(axis=1)])
        # 消除完全相同的行和数字全为0的行
        lst_out = lst[lst.any(1)]
        # print('operation matrix: ', '\n', lst_out)
        keep = (lst_out - lst_out.shift(1)).any(1)
        keep.iloc[0] = True
        # print(f'trimmed operation matrix without duplicated signal: \n{lst_out[keep]}')
        return lst_out[keep]

        ################################################################

    # ================================
    # 下面是Operation模块的私有方法

    def _set_timing_blender(self, timing_blender):
        """设置择时策略混合方式，混合方式包括pos-N,chg-N，以及cumulate三种

        input:
            :param timing_blender，str，合法的输入包括：
                'chg-N': N为正整数，取值区间为1到len(timing)的值，表示多空状态在第N次信号反转时反转
                'pos-N': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                'cumulate': 在每个策略发生反转时都会产生交易信号，但是信号强度为1/len(timing)
        return:=====
            无
        """
        self._timing_blender = timing_blender

    def _set_selecting_blender(self, selecting_blender_expression):
        """ 设置选股策略的混合方式，混合方式通过选股策略混合表达式来表示

            给选股策略混合表达式赋值后，直接解析表达式，将选股策略混合表达式的前缀表达式存入选股策略混合器
        """
        if not isinstance(selecting_blender_expression, str):  # 如果输入不是str类型
            self._selecting_blender = self._exp_to_blender
            self._selecting_blender_string = '0'
        else:
            self._selecting_blender = self._exp_to_blender
            self._selecting_blender_string = selecting_blender_expression

    def _set_ricon_blender(self, ricon_blender):
        self._ricon_blender = ricon_blender

    def _timing_blend(self, ls_masks):
        """ 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板

        input：=====
            :type: ls_masks：object ndarray, 多空蒙板列表，包含至少一个多空蒙板
        return：=====
            :rtype: object: 一个混合后的多空蒙板
        """
        blndr = self._timing_blender  # 从对象的属性中读取择时混合参数
        assert isinstance(blndr, str), 'Parmameter Type Error: the timing blender should be a text string!'
        # print 'timing blender is:', blndr
        l_m = 0
        for msk in ls_masks:  # 计算所有多空模版的和
            l_m += msk
        if blndr[0:3] == 'chg':  # 出现N个状态变化信号时状态变化
            # TODO: ！！本混合方法暂未完成！！
            # chg-N方式下，持仓仅有两个位置，1或0，持仓位置与各个蒙板的状态变化有关，如果当前状态为空头，只要有N个或更多
            # 蒙板空转多，则结果转换为多头，反之亦然。这种方式与pos-N的区别在于，pos-N在多转空时往往滞后，因为要满足剩余
            # 的空头数量小于N后才会转空头，而chg-N则不然。例如，三个组合策略下pos-1要等至少两个策略多转空后才会转空，而
            # chg-1只要有一个策略多转空后，就会立即转空
            # 已经实现的chg-1方法由pandas实现，效率很低
            # print 'the first long/short mask is\n', ls_masks[-1]
            assert isinstance(l_m, np.ndarray), 'TypeError: the long short position mask should be an ndArray'
            return np.apply_along_axis(_timing_blend_change, 1, l_m)
        else:  # 另外两种混合方式都需要用到蒙板累加，因此一同处理
            l_count = len(ls_masks)
            # print 'the first long/short mask is\n', ls_masks[-1]
            if blndr == 'cumulate':
                # cumulate方式下，持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，只有所有蒙板均看空时，最终结果才看空
                # 所有蒙板的权重相同，因此，如果一共五个蒙板三个看多两个看空时，持仓为60%
                # print 'long short masks are merged by', blndr, 'result as\n', l_m / l_count
                return l_m / l_count
            elif blndr[0:3] == 'pos':
                # pos-N方式下，持仓同样取决于看多的蒙板的数量，但是持仓只能为1或0，只有满足N个或更多蒙板看多时，最终结果
                # 看多，否则看空，如pos-2方式下，至少两个蒙板看多则最终看多，否则看空
                # print 'timing blender mode: ', blndr
                n = int(blndr[-1])
                # print 'long short masks are merged by', blndr, 'result as\n', l_m.clip(n - 1, n) - (n - 1)
                return l_m.clip(n - 1, n) - (n - 1)
            else:
                print('Blender text not recognized!')
        pass

    def _selecting_blend(self, sel_masks):
        """ 选股策略混合器，将各个选股策略生成的选股蒙板按规则混合成一个蒙板

        input:
            :param sel_masks:
        :return:
            ndarray, 混合完成的选股蒙板
        """
        exp = self._selecting_blender[:]
        # print('expression in operation module', exp)
        s = []
        while exp:  # previously: while exp != []
            if exp[-1].isdigit():
                s.append(sel_masks[int(exp.pop())])
            else:
                s.append(_blend(s.pop(), s.pop(), exp.pop()))
        return unify(s[0])

    def _ricon_blend(self, ricon_mats):
        if self._ricon_blender == 'add':
            r_m = ricon_mats.pop()
            while ricon_mats:  # previously while ricon_mats != []
                r_m += ricon_mats.pop()
            return r_m

    @property
    def _exp_to_blender(self):
        """选股策略混合表达式解析程序，将通常的中缀表达式解析为前缀运算队列，从而便于混合程序直接调用

        系统接受的合法表达式为包含 '*' 与 '+' 的中缀表达式，符合人类的思维习惯，使用括号来实现强制
        优先计算，如 '0 + (1 + 2) * 3'; 表达式中的数字0～3代表选股策略列表中的不同策略的索引号
        上述表达式虽然便于人类理解，但是不利于快速计算，因此需要转化为前缀表达式，其优势是没有括号
        按照顺序读取并直接计算，便于程序的运行。为了节省系统运行开销，在给出混合表达式的时候直接将它
        转化为前缀表达式的形式并直接存储在blender列表中，在混合时直接调用并计算即可
        input： =====
            no input parameter
        return：===== s2: 前缀表达式
            :rtype: list: 前缀表达式
        """
        # TODO: extract expression with re module
        prio = {'or' : 0,
                'and': 1}
        # 定义两个队列作为操作堆栈
        s1 = []  # 运算符栈
        s2 = []  # 结果栈
        # 读取字符串并读取字符串中的各个元素（操作数和操作符），当前使用str对象的split()方法进行，要
        # 求字符串中个元素之间用空格或其他符号分割，应该考虑写一个self.__split()方法，不依赖空格对
        # 字符串进行分割
        # exp_list = self._selecting_blender_string.split()
        exp_list = list(self._selecting_blender_string)
        # 开始循环读取所有操作元素
        while exp_list:
            s = exp_list.pop()
            # 从右至左逐个读取表达式中的元素（数字或操作符）
            # 并按照以下算法处理
            if s.isdigit():
                # 1，如果元素是数字则压入结果栈
                s2.append(s)

            elif s == ')':
                # 2，如果元素是反括号则压入运算符栈
                s1.append(s)
            elif s == '(':
                # 3，扫描到（时，依次弹出所有运算符直到遇到），并把该）弹出
                while s1[-1] != ')':
                    s2.append(s1.pop())
                s1.pop()
            elif s in prio.keys():
                # 4，扫描到运算符时：
                if s1 == [] or s1[-1] == ')' or prio[s] >= prio[s1[-1]]:
                    # 如果这三种情况则直接入栈
                    s1.append(s)
                else:
                    # 否则就弹出s1中的符号压入s2，并将元素放回队列
                    s2.append(s1.pop())
                    exp_list.append(s)
        while s1:
            s2.append(s1.pop())
        s2.reverse()  # 表达式解析完成，生成前缀表达式
        return s2