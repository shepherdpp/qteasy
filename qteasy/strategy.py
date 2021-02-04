# coding=utf-8
# strategy.py

# ======================================
# This file contains all built-in
# strategies that inherited from
# Strategy class and its sub-classes.
# ======================================

import numpy as np
from numpy.lib.stride_tricks import as_strided
import pandas as pd
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
        str1 = f'{type(self)} at {hex(id(self))}\n'
        str2 = f'{self.stg_name} of type: \'{self.stg_type}\''  # f'\nStrategy {self.stg_type}'
        return ''.join([str1, str2])

    def info(self, verbose: bool = False):
        """打印所有相关信息和主要属性"""
        print(f'{type(self)} at {hex(id(self))}\nStrategy type: {self.stg_name}')
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_boes)
        if self._pars is not None:
            print('Parameter Loaded:', type(self._pars), self._pars)
        else:
            print('Parameter NOT loaded!')
        # 在verbose == True时打印更多的额外信息
        if verbose:
            print('Information of the strategy:\n', self.stg_name, self.stg_text)

    def set_pars(self, pars: tuple) -> int:
        """设置策略参数，在设置之前对参数的个数进行检查

        input:
            :param: type items: tuple，需要设置的参数
        return:
            int: 1: 设置成功，0: 设置失败
        """
        assert isinstance(pars, (tuple, dict)) or pars is None, \
            f'parameter should be either a tuple or a dict, got {type(items)} instead'
        if pars is None:
            self._pars = pars
            return 1
        if len(pars) == self.par_count or isinstance(pars, dict):
            self._pars = pars
            return 1
        raise ValueError(f'parameter setting error in set_pars() method of \n{self}\nexpected par count: '
                         f'{self.par_count}, got {len(items)}')

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

    def set_custom_pars(self, **kwargs):
        """如果还有其他策略参数或用户自定义参数，在这里设置"""
        for k, v in zip(kwargs.keys(), kwargs.values()):
            if k in self.__dict__:
                setattr(self, k, v)
            else:
                raise KeyError(f'The strategy does not have property \'{k}\'')

    # TODO：Selecting的分段与Timing的Rolling Expansion滚动展开其实是同一个过程，未来可以尝试合并并一同优化
    def _seg_periods(self, dates, freq):
        """ 对输入的价格序列数据进行分段，用于所有与选股相关的派生类中

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
        temp_date_series = pd.date_range(start=dates[self.window_length], end=dates[-1], freq=freq)
        # 在这里发现一个错误，并已经修正：
        # 本来这里期望实现的功能是生成一个日期序列，该序列从dates[self.window_length]为第一天，后续的每个日期都在第一天基础上
        # 后移freq天。但是实际上pd.date_range生成的时间序列并不是从dates[self.window_length]这天开始的，而是它未来某一天。
        # 这就导致后面生成选股信号的时候，第一个选股信号并未产生在dates[self.window_length]当天，而是它的未来某一天，
        # 更糟糕的是，从dates[self.window_length]当天到信号开始那天之间的所有信号都是nan，这会导致这段时间内的交易信号
        # 空白。
        # 解决办法是生成daterange之后，使用pd.Timedelta将它平移到dates[self.window_length]当天即可。
        bnds = temp_date_series - (temp_date_series[0] - dates[self.window_length])
        # 写入第一个选股区间分隔位——0 (仅当第一个选股区间分隔日期与数据历史第一个日期不相同时才这样处理)
        seg_pos = np.zeros(shape=(len(bnds) + 2), dtype='int')
        # debug
        # print(f'in module selecting: function seg_perids generated date bounds supposed to start'
        #       f'from {dates[self.window_length]} to {dates[-1]}, actually got:\n'
        #       f'{bnds}\n'
        #       f'now comparing first date {dates[0]} with first bound {bnds[0]}')
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
        # 然而，为了确保在生成选股数据时，第一天也不会被落下，需要认为在seg_pos列表中前面插入一个0，得到[0,2,5,8]，这样才不会漏掉第一天和第二天
        # 以上是正常情况的处理方式
        # 如果分段的界限是[1,5,10]的时候，情况就不同了
        # 分段界限在时间序列中的seg_pos分别为[0,4,9]，这个列表中的首位本身就是0了，如果再在前面添加0，就会变成[0,0,4,9],会出现问题
        # 因为系统会判断第一个分段起点为0，终点也为0，因此会传递一个空的ndarray到_realize()函数中，引发难以预料的错误
        # 因此，出现这种情况时，要忽略最前面一位，返回时忽略第一位即可
        if seg_pos[1] == 0:
            return seg_pos[1:], seg_lens[1:], len(seg_pos) - 2
        else:
            return seg_pos, seg_lens, len(seg_pos) - 1

    @abstractmethod
    def generate(self, hist_data: np.ndarray, shares: [str, list], dates: [str, list]):
        """策略类的抽象方法，接受输入历史数据并根据参数生成策略输出"""
        raise NotImplementedError


# TODO: 在所有的generate()方法中应该对_realize()函数的输出进行基本检查，以提高自定义策略的用户友好度（在出现错误的定义时能够提供有意义的提示）
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
    是策略参数，策略通过传入的参数，利用window_history历史数据进行某种特定计算，最后生成一个-1～1之间的浮点数，这个数字就是在某一
    时间点的策略输出。

    Rolling_Timing类会自动把上述特定计算算法滚动应用到整个历史数据区间，并且推广到所有的个股中。

    在实现具体的Rolling_Timing类时，必须且仅需要实现两个方法：__init__()方法和_realize()方法，且两个方法的实现都需要遵循一定的规则：

        * __init__()方法的实现：

        __init__()方法定义了该策略的最基本参数，这些参数与策略的使用息息相关，而且推荐使用"super().__init__()"的形式设置这些参数，这些参数
        包括：
            stg_name:
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
    def _realize(self, hist_data: np.ndarray, params: tuple) -> float:
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
            :stg_output: float, 一个代表策略输出的数字，可以代表头寸位置，1代表多头，-1代表空头，0代表空仓，策略输出同样可以代表操作
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
        # print(f'在Timing.generate_over()函数中取到历史数据切片hist_slice的shape为 {hist_slice.shape}, 参数为: {items}')
        # print(f'first 20 rows of hist_price_slice got in Timing.generator_over() is:\n{hist_slice[:20]}')
        # 获取输入的历史数据切片中的NaN值位置，提取出所有部位NAN的数据，应用_realize()函数
        # 由于输入的历史数据来自于HistoryPanel，因此总是三维数据的切片即二维数据，因此可以简化：
        no_nan = ~np.isnan(hist_slice[:, 0])
        # 生成输出值一维向量
        cat = np.zeros(hist_slice.shape[0])
        hist_nonan = hist_slice[no_nan]  # 仅针对非nan值计算，忽略股票停牌时期
        loop_count = len(hist_nonan) - self.window_length + 1
        # debug
        # print(f'there are {len(hist_nonan)} rows of data that are not "Nan", \n'
        #       f'thus these rows of data will be "rolled" to a 2-D '
        #       f'shaped matrix containing in each column {self.window_length} rows of data \neach offsetting 1 row ahead'
        #       f'the next column over the whole matrix, forming a {loop_count} X {self.window_length} matrix')
        if loop_count < 1:  # 在开始应用generate_one()前，检查是否有足够的非Nan数据，如果数据不够，则直接输出全0结果
            return cat[self.window_length:]

        # 如果有足够的非nan数据，则开始进行历史数据的滚动展开
        # ------------- The as_strided solution --------------------------------------
        hist_pack = as_strided(hist_nonan,
                               shape=(loop_count, *hist_nonan[:self._window_length].shape),
                               strides=(hist_nonan.strides[0], *hist_nonan.strides),
                               subok=False,
                               writeable=False)
        # ------------- The numpy sliding_window_view solution -----------------------
        # This solution will only be effective after numpy version 1.20
        # NotImplemented
        # ------------- The for-loop solution ----------------------------------------
        # hist_pack = np.zeros((loop_count, *hist_nonan[:self._window_length].shape))
        # for i in range(loop_count):
        #     hist_pack[i] = hist_nonan[i:i + self._window_length]
        # ----------------------------------------------------------------------------
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
        # debug
        # print(f'created long/short masks with above matrix, shape is {res.shape}\n'
        #       f'containing {np.count_nonzero(res)} non-zero signals, first signal is at {np.where(res)[0]}')
        capping = np.zeros(self._window_length - 1)
        # debug
        # print(f'in Timing.generate_over() function shapes of res and capping are {res.shape}, {capping.shape}')
        res = np.concatenate((capping, res), 0)
        # 将结果填入原始数据中不为Nan值的部分，原来为NAN值的部分保持为0
        cat[no_nan] = res
        # debug
        # print(f'first 100 items of created long/short mask for current hist_slice is '
        #       f'(shape:{cat[self.window_length:].shape}, containing '
        #       f'{np.count_nonzero(cat[self.window_length:])} signals): \n'
        #       f'{cat[self.window_length:][:100]}')
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
        # print(f'the history data passed to rolling realization function is shaped {hist_data.shape}')
        # print(f'generate result of np timing generate, result shaped {res.shape}')
        # print(f'generate result of np timing generate after cutting is shaped {res[self.window_length:, :].shape}')
        # 每个个股的多空信号清单被组装起来成为一个完整的多空信号矩阵，并返回
        return res


class SimpleSelecting(Strategy):
    """选股策略类的抽象基类，所有选股策略类都继承该类。该类定义的策略生成方法是历史数据分段处理，根据历史数据的分段生成横向投资组合分配比例。

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

        同其他类型的策略一样，Selecting策略同样需要实现抽象方法_realize()，并在该方法中具体描述策略如何根据输入的参数建立投资组合。而
        generate()函数则负责正确地将该定义好的生成方法循环应用到每一个数据分段中。

            * _realize()方法的实现：

            _realize()方法确定了策略的具体实现方式，要注意_realize()方法需要有两个参数：

                :input:
                hist_data: ndarray, 3-dimensional
                parames: tuple

                :output
                sel_vector: ndarray, 1-dimensional

            在_realize()方法中用户可以以任何可能的方法使用hist_data，hist_data是一个三维数组，包含L层，R行，C列，分别代表L只个股、
            R个时间序列上的C种数据类型。明确这一点非常重要，因为在_realize()方法中需要正确地利用这些数据生成选股向量。


    """
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
        """" SimpleSelecting 类的选股抽象方法，在不同的具体选股类中应用不同的选股方法，实现不同的选股策略

        input:
            :param hist_data: type: numpy.ndarray, 一个历史数据片段，包含N个股票的data_types种数据在window_length日内的历史
            数据片段
        :return
            numpy.ndarray, 一个一维向量，代表一个周期内股票选择权重，整个向量经过归一化，即所有元素之和为1
        """
        raise NotImplementedError

    # TODO：需要重新定义SimpleSelecting的generate函数，仅使用hist_data一个参数，其余参数都可以根据策略的基本属性推断出来
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
        assert isinstance(self.pars, tuple), f'TypeError, strategy parameter should be a tuple, got {type(self.items)}'
        assert len(self.pars) == self.par_count, \
            f'InputError, expected count of parameter is {self.par_count}, got {len(self.items)} instead'
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
        # print(f'history segmentation factors are:\nseg_pos:\n{seg_pos}\nseg_lens:\n{seg_lens}\n'
        #       f'seg_count\n{seg_count}')
        for sp, sl, fill_len in zip(seg_pos[1:-1], seg_lens, seg_lens[1:]):
            # share_sel向量代表当前区间内的投资组合比例
            # debug
            # print(f'{sl} rows of data,\n starting from {sp - sl} to {sp - 1},\n'
            #       f' will be passed to selection realize function:\n{hist_data[:, sp - sl:sp, :]}')
            share_sel = self._realize(hist_data[:, sp - sl:sp, :])
            # assert isinstance(share_sel, np.ndarray)
            # assert len(share_sel) == len(shares)
            seg_end = seg_start + fill_len
            # 填充相同的投资组合到当前区间内的所有交易时间点
            sel_mask[seg_start:seg_end + 1, :] = share_sel
            # debug
            # print(f'filling data into the sel_mask, now filling \n{share_sel}\nin she sell mask '
            #       f'from row {seg_start} to {seg_end} (not included)\n')
            seg_start = seg_end
        # 将所有分段组合成完整的ndarray
        # debug
        # print(f'hist data is filled with sel value, shape is {sel_mask.shape}\n'
        #       f'the first 100 items of sel values are {sel_mask[:100]}')
        # print(f'but the first {self.window_length} rows will be removed from the data\n'
        #       f'only last {sel_mask.shape[0] - self.window_length} rows will be returned\n'
        #       f'returned mask shape is {sel_mask[self.window_length:].shape}\n'
        #       f'first 100 items are \n{sel_mask[self.window_length:][:100]}')
        return sel_mask[self.window_length:]


class SimpleTiming(Strategy):
    """ 快速择时策略的抽象基类，所有快速择时策略都继承自该抽象类，本类继承自策略基类，同时定义了_realize()抽象方法，用于实现具体的择时策略

        SimpleTiming择时策略的generate()函数采用了简单的整体择时信号计算方式，针对投资组合中的所有个股，逐个将其全部历史数据一次
        性读入后计算整个历史区间的择时信号。
        与RollingTiming相比，SimpleTiming并不会在同一个个股上反复滚动计算，在整个历史区间上将_realize()只应用一次，因此在计算速度上比
        RollingTiming快很多。但是这样的方法并不能完全避免"未来函数"的问题，因此建议将同样的策略同时使用RollingTiming方法实现一次，检查
        两者的输出是否一致，如果一致，则表明算法不存在"未来函数"，可以使用SimpleTiming实现，否则必须使用RollingTiming实现。


        在择时类策略中，generate方法接受的历史数据片段hist_data为一个M * N * L的ndarray, 来自HistoryPanel对象，其定义是：
            M: axis 1: 层，每层的标签为一个个股，每一层在HistoryPanel中被称为一个level，所有level的标签被称为shares
            N: axis 2: 行，每行的标签为一个时间点，每一行在HistoryPanel中被称为一个row，所有row的标签被称为hdates
            L: axis 3: 列，每列的标签为一种历史数据，每一列在HistoryPanel中被称为一个column，所有column的标签被称为htypes

        在SimpleTiming的generate()函数中，每一个个股的历史数据被逐个取出，并送入generate_over()函数进行处理，消除掉N/A值之后，传入
        generate()函数，针对每个个股进行逐个计算，并将最终的结果组合成一个2D的矩阵输出

    Simple Timing择时策略是通过realize()函数来实现的。一个继承了Simple_Timing类的对象，必须具体实现realize()方法。这是个抽象方法。
    这个方法接受两个参数，一个是generate_over()函数传送过来的window_history数据，另一个是策略参数，策略通过传入的参数，最后生成一个
    包含一串-1～1之间的浮点数的向量，这个向量代表该个股在整个历史周期中的多空仓位比例，-1代表满仓做空，+1代表满仓做多，0代表空仓。

    Simple_Timing类会自动把上述特定计算算法推广到所有的个股中。

    在实现具体的Simple_Timing类时，必须且仅需要实现两个方法：__init__()方法和_realize()方法，且两个方法的实现都需要遵循一定的规则：

        * __init__()方法的实现：

        __init__()方法定义了该策略的最基本参数，这些参数与策略的使用息息相关，而且推荐使用"super().__init__()"的形式设置这些参数，这些参数
        包括：
            stg_name:
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

            hist_data: ndarray, 3 dimensional
            parames: tuple

            :output:
            long-short-vector: ndarray, 1 dimensional

        在_realize()方法中用户可以以任何可能的方法使用hist_data，但必须知道hist_data的结构，同时确保返回一个向量（ndarray），且向量
        包含的值在-1～1之间（包括-1和+1），同时向量的长度和hist_data中包含的Timestamp数量相同。这个向量代表了在每一个Timestamp上该个股
        应该持有的仓位及持仓方向。-1代表在这个Timestamp应该持有满仓做空，+1代表应该满仓做多，0代表空仓，而-1与+1之间的不为零浮点数代表介于
        0～100%之间的仓位。
        注意输出的l/s vector的长度必须与历史数据Timestamp的数量相同，否则会报错
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
    def _realize(self, hist_data: np.ndarray):
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


class FactoralSelecting(Strategy):
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
                 data_types: [list, str] = 'close',
                 condition: str = 'any',
                 lbound: float = -np.inf,
                 ubound: float = np.inf,
                 sort_ascending: bool = True,
                 weighting: str = 'even'):
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
        self.condition = condition
        self.lbound = lbound
        self.ubound = ubound
        self.sort_ascending = sort_ascending
        self.weighting = weighting

    @abstractmethod
    def _realize(self, hist_data: np.ndarray):
        """" SimpleSelecting 类的选股抽象方法，在不同的具体选股类中应用不同的选股方法，实现不同的选股策略

        input:
            :param hist_data: type: numpy.ndarray, 一个历史数据片段，包含N个股票的data_types种数据在window_length日内的历史
            数据片段
        :return
            numpy.ndarray, 一个一维向量，代表一个周期内股票的选股因子，选股因子向量的元素数量必须与股票池中的股票数量相同
        """
        raise NotImplementedError

    def _process_factors(self, hist_data: np.ndarray):
        """处理从_realize()方法传递过来的选股因子

        选出符合condition的因子，并将这些因子排序，根据次序确定所有因子相应股票的选股权重
        将选股权重传递到generate()方法中，生成最终的选股蒙板

        input:
            :type hist_data: np.ndarray
        :return
            numpy.ndarray, 一个一维向量，代表一个周期内股票的投资组合权重，所有权重的和为1
        """
        pct = self._poq
        condition = self.condition
        lbound = self.lbound
        ubound = self.ubound
        sort_ascending = self.sort_ascending
        weighting = self.weighting

        share_count = hist_data.shape[0]
        if pct < 1:
            # pct 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            pct = int(share_count * pct)
        else:  # pct 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            pct = int(pct)
        if pct < 1:
            pct = 1
        # 历史数据片段必须是ndarray对象，否则无法进行
        assert isinstance(hist_data, np.ndarray), \
            f'TypeError: expect np.ndarray as history segment, got {type(hist_data)} instead'

        factors = self._realize(hist_data=hist_data)
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
            raise ValueError(f'indication selection condition \'{condition}\' not supported!')
        nan_count = np.isnan(factors).astype('int').sum()  # 清点数据，获取nan值的数量
        if nan_count == share_count:  # 当indices全部为nan，导致没有有意义的参数可选，此时直接返回全0值
            # debug
            # print(f'in SimpleSelecting realize method got ranking vector and share selecting vector like:\n'
            #       f'{np.round(indices, 3)}\n{np.round(chosen,3)}')
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
        #
        if weighting == 'linear':
            dist = np.arange(1, 3, 2. / arg_count)  # 生成一个线性序列，最大值为最小值的约三倍
            chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
        # proportion：比例分配，权重与分值成正比，分值最低者获得一个基础比例，其余股票的比例与其分值成正比
        elif weighting == 'proportion':
            dist = factors[args]
            d = dist.max() - dist.min()
            if not sort_ascending:
                dist = dist - dist.min() + d / 10.
            else:
                dist = dist.max() - dist + d / 10.
            # print(f'in SimpleSelecting realize method proportion type got distance of each item like:\n{dist}')
            if ~np.any(dist):  # if all distances are zero
                chosen[args] = 1 / len(dist)
            elif dist.sum() == 0:  # if not all distances are zero but sum is zero
                chosen[args] = dist / len(dist)
            else:
                chosen[args] = dist / dist.sum()
        # even：均匀分配，所有中选股票在组合中权重相同
        else:  # self.__distribution == 'even'

            chosen[args] = 1. / arg_count
        # debug
        # print(f'in SimpleSelecting realize method got ranking vector and share selecting vector like:\n'
        #       f'{np.round(indices, 3)}\n{np.round(chosen,3)}')
        return chosen

    # TODO：需要重新定义FactoralSelecting的generate函数，仅使用hist_data一个参数，其余参数都可以根据策略的基本属性推断出来
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
        assert isinstance(self.pars, tuple), f'TypeError, strategy parameter should be a tuple, got {type(self.items)}'
        assert len(self.pars) == self.par_count, \
            f'InputError, expected count of parameter is {self.par_count}, got {len(self.items)} instead'
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
        # print(f'history segmentation factors are:\nseg_pos:\n{seg_pos}\nseg_lens:\n{seg_lens}\n'
        #       f'seg_count\n{seg_count}')
        for sp, sl, fill_len in zip(seg_pos[1:-1], seg_lens, seg_lens[1:]):
            # share_sel向量代表当前区间内的投资组合比例
            # debug
            # print(f'{sl} rows of data,\n starting from {sp - sl} to {sp - 1},\n'
            #       f' will be passed to selection realize function:\n{hist_data[:, sp - sl:sp, :]}')
            share_sel = self._process_factors(hist_data[:, sp - sl:sp, :])
            # assert isinstance(share_sel, np.ndarray)
            # assert len(share_sel) == len(shares)
            seg_end = seg_start + fill_len
            # 填充相同的投资组合到当前区间内的所有交易时间点
            sel_mask[seg_start:seg_end + 1, :] = share_sel
            # debug
            # print(f'filling data into the sel_mask, now filling \n{share_sel}\nin she sell mask '
            #       f'from row {seg_start} to {seg_end} (not included)\n')
            seg_start = seg_end
        # 将所有分段组合成完整的ndarray
        # debug
        # print(f'hist data is filled with sel value, shape is {sel_mask.shape}\n'
        #       f'the first 100 items of sel values are {sel_mask[:100]}')
        # print(f'but the first {self.window_length} rows will be removed from the data\n'
        #       f'only last {sel_mask.shape[0] - self.window_length} rows will be returned\n'
        #       f'returned mask shape is {sel_mask[self.window_length:].shape}\n'
        #       f'first 100 items are \n{sel_mask[self.window_length:][:100]}')
        return sel_mask[self.window_length:]


class ReferenceTiming(Strategy):
    """ 根据参考数据对一批股票进行集合择时操作，生成操作模版

    """
    def __init__(self):
        super().__init__()

    def generate(self, hist_data: np.ndarray, shares: [str, list], dates: [str, list]):
        raise NotImplementedError