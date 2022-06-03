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
from abc import abstractmethod, ABCMeta
from .utilfuncs import str_to_list
from .utilfuncs import TIME_FREQ_STRINGS


class BaseStrategy:
    """ 量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的策略类调用

        类属性定义了策略类型、策略名称、策略关键属性的数量、类型和取值范围等
        所有的策略类都有一个generate()方法，供Operator对象调用，传入相关的历史数据，并生成一组交易信号。

        策略的实现
        基于一个策略类实现一个具体的策略，需要创建一个策略类，设定策略的基本参数，并重写realize()方法，在
        realize()中编写交易信号的生成规则：

        - 策略的初始化(可选)
        初始化策略的目的是为了设定策略的基本参数；
        除了策略名称、介绍以外，还包括有哪些参数，参数的取值范围和类型、需要使用哪些历史数据、
        数据的频率、信号生成的频率（称为采样频率）、数据滑窗的大小、参考数据的类型等等信息，这些信息都可以在
        策略初始化时通过策略属性设置，如果不在初始化是设置，可以在创建strategy对象时设置。：

        推荐使用下面的方法设置策略

            Class ExampleStrategy(GeneralStg):

                # __init__()是可选，在这里设置的属性值会成为这一策略类的默认值，在创建策略对象的
                # 时候不需要重复设置。
                def __init__(self):
                    # 可选项
                    # 定义这个策略的缺省/默认属性值
                    super().__init_(pars=<default pars>,
                                    par_count=<default par_count>,
                                    par_types=<default par_types>,
                                    par_range=<default par_range>,
                                    **kwargs  # 定义其他的缺省属性值
                                    )

                def realize(self, pars, h, r, t):

                    # 在这里编写信号生成逻辑
                    # res代表信号输出值

                    return res

        用下面的方法创建一个策略对象：

            example_strategy = ExampleStrategy(name='example',
                                               description='example strategy',
                                               pars=(2, 3.0, 'int'),
                                               data_types='close',
                                               bt_price_types='close'
                                               data_freq='d',
                                               sample_freq='2d',
                                               window_length=100)
            # 如果上面的属性在定义策略类的时候已经输入了，那么可以省略

        除了某些策略需要更多特殊属性以外，基本属性的含义及取值范围如下：

            pars: tuple,            策略参数, 用于生成交易信号时所需的可变参数，在opt模式下，qteasy可以
                                    通过修改这个参数寻找参数空间中的最优参数组合
            opt_tag: int,           0: 参加优化，1: 不参加优化
            name: str,              策略名称，用户自定义字符串
            description: str,       策略简介，类似于docstring，简单介绍该类的策略内容
            par_count: int,         策略参数个数
            par_types: tuple/list,  策略参数类型，注意这里并不是数据类型，而是策略参数空间数轴的类型，包含三种类型：
                                    1, 'discr': 离散型参数，通常数据类型为int
                                    2, 'conti': 连续型参数，通常数据类型为float
                                    3, 'enum': 枚举型参数，数据类型不限，可以为其他类型如str或tuple等
            par_range:              策略参数取值范围，该参数供优化器使用，用于产生正确的参数空间并用于优化
            data_freq: str:         静态属性，依赖的数据频率，用于生成策略输出所需的历史数据的频率，取值范围包括：
                                    1, 'TICK'/'tick'/'t':
                                    2, 'MIN'/'min':
                                    3, 'H'/'h':
                                    4, 'D'/'d':
                                    5, 'W'/'w':
                                    6, 'M'/'m':
                                    7, 'Q'/'q':
                                    8, 'Y'/'y':
            sample_freq:            静态属性，策略生成时的采样频率，即相邻两次策略生成的间隔频率，可选参数与data_freq
                                    一样，支持data_freq的倍数频率，如'3d', '2w'等，但是不能高于数据频率。
            window_length:          静态属性，历史数据视窗长度。即生成策略输出所需要的历史数据的数量
            data_types:             静态属性生成策略输出所需要的历史数据的种类，由以逗号分隔的参数字符串组成，可选的参数
                                    字符串包括所有qteasy中内置的标准数据类型或自定义数据类型：
                                    1, 'open'
                                    2, 'high'
                                    3, 'low'
                                    4, 'close'
                                    5, 'volume'
                                    6, 'eps'
                                    7, ...
            bt_price_type:          静态属性，策略回测时所使用的历史价格种类，可以定义为开盘、收盘、最高、最低价，也可以设置
                                    为五档交易价格中的某一个价格，根据交易当时的时间戳动态确定具体的交易价格
            reference_data_types:   参考数据类型，用于生成交易策略的历史数据，但是与具体的股票无关，可用于所有的股票的信号
                                    生成，如指数、宏观经济数据等。
                                    如果参考数据是某指数或个股的数据，必须在数据类型后指明股票或指数代码，如：
                                    - 'close-000300.SH': 表示沪深300指数的收盘价
                                    - 'pe-600517.SH':    股票600517.SH的pe值
                                    如果某种类型的数据本身与股票、指数等具体证券无关，则直接指明即可：
                                    - 'shibor_on':       SHIBOR隔夜拆借利率数据

        - 编写策略规则
        策略规则是交易策略的核心，体现了交易信号与历史数据之间的逻辑关系。
        策略规则必须在realize()方法中定义，realize()方法具有标准的数据输入，用户在规则中只需要考虑交易信号的产生逻辑即可，不
        需要考虑股票的数量、历史周期、数据选择等等问题；
        realize()方法是整个量化交易策略的核心，它体现了从输入数据到交易信号的逻辑过程
        因此realize函数的输入包含历史数据、输出就是交易信号。

        realize()方法的定义如下：

            def realize(self,
                        h: np.ndarray,
                        r: np.ndarray,
                        t: np.ndarray)

        realize()方法的实现：

        策略参数的获取：
            在realize()方法中，可以使用self.pars获取策略参数：

                par_1, par_2, ..., par_n = self.pars

        历史数据及其他相关数据的获取：
        不管Strategy继承了哪一个策略类，realize()方法的输入都可以包括以下几个输入数据：

            - h(history):   历史数据片段，通常这是一个3D的ndarray，包含了所有股票的所有类型的历史数据，且数据的时间起止点是
                            策略运行当时开始倒推到时间窗口长度前的时刻，具体来说，如果这个array的shape为(M, N, L)，即：
                            - M层：
                                每一层的数据表示一只股票的历史数据，具体哪些股票在qteasy运行参数中设定，
                                例如：设定：
                                    - asset_pool = "000001.SZ, 000002.SZ, 600001.SH"
                                表示：
                                    使用"000001.SZ, 000002.SZ, 600000.SH"三支股票参与回测

                                那么输入的数据就会包含3层，且第0、1、2层分别对应了000001.SZ, 000002.SZ, 600000.SH
                                三支股票的数据，使用下面的方法即可获取相应的数据：
                                    h_seg[0, :, :] - 获取000001.SZ的所有历史数据

                            - N行：
                                每一行数据表示股票在一个时间戳（或时间点）上的历史数据。
                                传入的数据一共有N行，N也就是时间戳的数量是通过策略的window_length参数设定的，而
                                data_freq则定义了时间戳的频率。
                                例如：设定：
                                    - data_freq = 'd'
                                    - window_length = 100
                                即表示：
                                    每次信号生成使用的历史数据频率为'天"，且使用100天的数据来生成交易信号

                                这样在每一组strategy运行时，传入的历史数据片段就会包含从100天前到昨天的历史数据，例如
                                在2020-05-30这一天，获取的数据就会是从2020-01-04开始，一直到2020-05-29这100个交易日
                                的历史数据

                            - L列：
                                每一列数据表示与股票相关的一种历史数据类型。具体的历史数据类型在策略属性data_types中设置
                                例如：设定：
                                    - data_types = "open, high, low, close, pe"
                                即表示：
                                    传入的数据会包含5列，分别代表股票的开、高、收、低、市盈率物种数据类型

                                传入的数据排列顺序与data_types的设置一致，也就是说，如果需要获取市盈率数据，可以这样
                                获取：
                                    h_seg[:, :, 4]

                            在策略规则中获取历史数据应该使用上面的切片方法，并做相应计算，下面给出几个例子：
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

                            **注意**
                            在RuleIterator策略类中，h_seg的格式稍有不同，是一个2D数据，参见RuleIterator策略类
                            的docstring

            - r(reference): 参考历史数据，即与每个个股并不直接相关，但是可以在生成交易信号时用做参考的数据，例如根据
                            大盘选股的大盘数据，或者宏观经济数据等。
                            如果不需要参考数据，r 会是None

                            ref_seg的结构是一个N行L列的2D array，包含所有可以使用的参考数据类型，而数据的时间段与
                            历史数据h相同:

                            - N行,
                                每一行数据表示股票在一个时间戳（或时间点）上的历史数据。
                                传入的数据一共有N行，N也就是时间戳的数量是通过策略的window_length参数设定的，而
                                data_freq则定义了时间戳的频率。

                            - L列
                                每一列数据表示与股票相关的一种参考数据类型。具体的参考数据类型在策略属性
                                reference_data_types中设置
                                例如：设定：
                                    - reference_data_types = "000300.SH.close"
                                即表示：
                                    使用的参考历史数据为000300.SH指数的收盘价
                                如果reference_data_types = ""，则传入的参考数据会是None

            - t(trade):     交易历史数据，最近几次交易的结果数据，2D数据。包含N行L列数据
                            如果交易信号不依赖交易结果（只有这样才能批量生成交易信号），t会是None。
                            数据的结构如下

                            - 5行,
                                每一行数据代表一类数据，包括：
                                - 当前持有每种股票的份额
                                - 当前可用的每种股票的份额
                                - 当前的交易价格
                                - 最近一次交易的股票变动数量（正数表示买入，负数表示卖出）
                                - 最近一次交易的成交价格

                            - L列，
                                每一列代表一个股票的数据

                            示例：以下是在策略中获取交易数据的几个例子：


        realize()方法的输出：
        realize()方法的输出就是交易信号，为了确保交易信号有意义，输出信息必须遵循一定的格式。
        对于GeneralStg和FactorSorter两类交易策略来说，输出信号为1D ndarray，这个数组包含的元素数量与参与策略的股票数量
        相同，例如参与策略的股票有20个，则生成的交易策略为shape为(20,)的numpy数组
        特殊情况是RuleIterator策略类，这一类策略会将相同的规则重复应用到所有的股票上，因此仅需要输出一个数字即可。

            - GeneralStg / FactorSorter:
                output：
                        np.array(arr), 如： np.array[0.2, 1.0, 10.0, 100.0]
            - RuleIterator:
                output:
                        float / np.float, 如: 1.0

        按照前述规则设置好策略的参数，并在realize函数中定义好逻辑规则后，一个策略就可以被添加到Operator
        中，并产生交易信号了。
        关于Strategy类的更详细说明，请参见qteasy的文档。
    """
    __mataclass__ = ABCMeta

    AVAILABLE_BT_PRICE_TYPES = ['open', 'high', 'low', 'close',
                                'buy1', 'buy2', 'buy3', 'buy4', 'buy5',
                                'sell1', 'sell2', 'sell3', 'sell4', 'sell5']

    def __init__(self,
                 pars: any = None,
                 opt_tag: int = 0,
                 stg_type: str = 'strategy type',
                 name: str = 'strategy name',
                 description: str = 'intro text of strategy',
                 par_count: int = None,
                 par_types: [list, str] = None,
                 par_range: [list, tuple] = None,
                 data_freq: str = 'd',
                 sample_freq: str = 'd',
                 window_length: int = 270,
                 data_types: [str, list] = 'close',
                 bt_price_type: str = 'close',
                 reference_data_types: [str, list] = ''):
        """ 初始化策略，赋予策略基本属性，包括策略的参数及其他控制属性

        """
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
                if not item.lower() in ['int', 'float', 'conti', 'discr', 'enum']:
                    raise KeyError(f'Invalid type ({item}), should be one of "int, float, conti, discr, enum"')
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

        self._pars = pars  # 策略的参数，动态属性
        self._opt_tag = opt_tag  # 策略的优化标记，
        self._stg_type = stg_type  # 策略类型
        self._stg_name = name  # 策略的名称
        self._stg_text = description  # 策略的描述文字
        self._par_count = par_count  # 策略参数的元素个数
        self._par_types = par_types  # 策略参数的类型，可选类型'discr/conti/enum'
        self._par_bounds_or_enums = par_range
        logger_core.info(f'Strategy created with basic parameters set, pars={pars}, par_count={par_count},'
                         f' par_types={par_types}, par_range={par_range}')

        # 其他的几个参数都通过参数赋值方法赋值，在赋值方法内会进行参数合法性检，这里只需确保所有参数不是None即可
        assert data_freq is not None
        assert sample_freq is not None
        assert window_length is not None
        assert data_types is not None
        assert bt_price_type is not None
        assert reference_data_types is not None
        self._data_freq = None
        self._sample_freq = None
        self._window_length = None
        self._data_types = None
        self._bt_price_type = None
        self._reference_data_types = None
        self.set_hist_pars(data_freq=data_freq,
                           sample_freq=sample_freq,
                           window_length=window_length,
                           data_types=data_types,
                           bt_price_type=bt_price_type,
                           reference_data_types=reference_data_types)
        logger_core.info(f'Strategy creation. with other parameters: data_freq={data_freq}, sample_freq={sample_freq},'
                         f' window_length={window_length}, bt_price_type={bt_price_type}, '
                         f'reference_data_types={reference_data_types}')

    @property
    def stg_type(self):
        """策略类型，策略类型决定了策略的实现方式，目前支持的策略类型共有三种：'ROLLING TIMING', 'SELECTING', 'SIMPLE TIMNG'"""
        return self._stg_type

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
        self._stg_text = description

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

        :return:
        """
        str1 = f'{self._stg_type}('
        str2 = f'{self.name})'
        return ''.join([str1, str2])

    def info(self, verbose: bool = False):
        """打印所有相关信息和主要属性"""
        print(f'{type(self)} at {hex(id(self))}\nStrategy type: {self.name}')
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_range)
        if self._pars is not None:
            print('Parameter Loaded:', type(self._pars), self._pars)
        else:
            print('No Parameter!')
        # 在verbose == True时打印更多的额外信息
        if verbose:
            print('Information of the strategy:\n', self.name, self.description)

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

    def set_par_range(self, par_range):
        """ 设置策略参数的取值范围

        input:
            :param par_range: 策略的参数取值范围
        :return:
        """
        if par_range is None:
            self._par_bounds_or_enums = []
        else:
            self._par_bounds_or_enums = par_range
        return par_range

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
            if isinstance(reference_data_types, str):
                reference_data_types = str_to_list(reference_data_types, ',')
            assert isinstance(reference_data_types, list), \
                f'TypeError, reference data types should be a list, got {type(reference_data_types)} instead'
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
        if data_idx is None:
            data_idx = -1
        if isinstance(data_idx, (int, np.int)):
            # 生成单组信号
            idx = data_idx
            h_seg = hist_data[idx]
            if ref_data is None:
                ref_seg = None
            else:
                ref_seg = ref_data[idx]
            return self.generate_one(h_seg=h_seg, ref_seg=ref_seg, trade_data=trade_data)
        elif isinstance(data_idx, np.ndarray):
            # 生成信号清单
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
                trade_data_list = all_none_list
            else:
                trade_data_list = [trade_data] * signal_count
            # 使用map完成快速遍历填充
            signals = list(map(self.generate_one, hist_data_list, ref_data_list, trade_data_list))
            sig_list[data_idx] = np.array(signals)
            # 将所有分段组合成完整的ndarray
            return sig_list

    @abstractmethod
    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """ 抽象方法，在各个Strategy类中实现具体操作

        :param h_seg:
        :param ref_seg:
        :param trade_data:
        :return:
        """
        pass


class GeneralStg(BaseStrategy):
    """ 通用交易策略类，用户可以使用策略输入的历史数据、参考数据和成交数据，自定信号生成规则，生成交易信号。

        GeneralStg是最基本的通用策略类，没有任何额外的策略属性，其执行也完全依赖用户输入的策略逻辑，不提供任何的预处理或后处理。
        用户需要在realize()方法中定义完整的策略，直接生成交易信号。

            * 额外的策略属性：
                None

            * realize()方法的实现：realize()方法需要利用输入的参数，输出交易信号
                :input:
                params: tuple 一组策略参数
                h: 历史数据，一个3D numpy数组，包含所有股票在一个时间窗口内的所有类型的历史数据，
                    参考BaseStrategy的docstring
                r: 参考数据，一个2D numpy数组，包含一个时间窗口内所有参考类型的历史数据
                    参考BaseStrategy的docstring
                t: 交易数据，一个2D numpy数组，包含最近一次交易的实际结果
                    参考BaseStraegy的docstring

                :output
                signals: 一个代表交易信号的1D numpy数组，dtype为float

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
    """ 因子排序选股策略，根据用户定义的选股因子筛选排序后确定每个股票的选股权重

        这类策略要求用户从历史数据中提取一个选股因子，并根据选股因子的大小排序后确定投资组合中股票的交易信号
        用户需要在realize()方法中计算选股因子，计算出选股因子后，接下来的排序和选股逻辑都不需要用户自行定义。
        策略会根据预设的条件，从中筛选出符合标准的因子，并将剩下的因子排序，从中选择特定
        数量的股票，最后根据它们的因子值分配权重或信号值。

        这些选股因子的排序和筛选条件，由6个额外的选股参数来控制，因此用户只需要在策略属性中设置好相应的参数，
        策略就可以根据选股因子输出交易信号了。用户只需要集中精力思考选股因子的定义逻辑即可，无需费时费力编写
        因子的筛选排序取舍逻辑了。

            * 额外的策略属性：
                策略使用6个额外的选股参数实现因子排序选股:
                max_sel_count:      float,  选股限额，表示最多选出的股票的数量，如果sel_limit小于1，表示选股的比例：
                                            默认值：0.5
                                            例如：
                                            0.25: 最多选出25%的股票, 10:  最多选出10个股票
                condition:          str ,   确定股票的筛选条件，默认值'any'
                                            可用值包括：
                                            'any'        :默认值，选择所有可用股票
                                            'greater'    :筛选出因子大于ubound的股票
                                            'less'       :筛选出因子小于lbound的股票
                                            'between'    :筛选出因子介于lbound与ubound之间的股票
                                            'not_between':筛选出因子不在lbound与ubound之间的股票
                lbound:             float,  执行条件筛选时的指标下界, 默认值np.-inf
                ubound:             float,  执行条件筛选时的指标上界, 默认值np.inf
                sort_ascending:     bool,   排序方法，对选中的股票进行排序以选择或分配权重：
                                            默认值: False
                                            True         :对选股因子从小到大排列，优先选择因子最小的股票
                                            False        :对选股因子从大到小排列，优先选择因子最大的股票
                weighting:          str ,   确定如何分配选中股票的权重
                                            默认值: 'even'
                                            'even'       :所有被选中的股票都获得同样的权重
                                                          例如:
                                                          Factors: [-0.1,    0,  0.3,  0.4]
                                                          signals: [0.25, 0.25, 0.25, 0.25]
                                            'linear'     :权重根据因子排序线性分配，分值最高者占比约为分值最低者占比的三倍，
                                                          其余居中者的比例按序呈等差数列
                                                          例如:
                                                          Factors: [ -0.1,     0,   0.3,   0.4]
                                                          signals: [0.143, 0.214, 0.286, 0.357]
                                            'distance'   :指标最低的股票获得一个基本权重，其余股票的权重与他们的指标与最低
                                                          指标之间的差值（距离）成比例
                                                          例如:
                                                          Factors: [ -0.1,     0,   0.3,   0.4]
                                                          signals: [0.042, 0.125, 0.375, 0.458]
                                            'proportion' :舍去不合理的因子值后（如负数），其余股票的权重与它们的因子分值
                                                          成正比
                                                          例如:
                                                          Factors: [ -0.1,    0.,   0.3,   0.4]
                                                          signals: [   0.,    0., 0.429, 0.571]

            * realize()方法的实现：realize()方法需要利用输入的参数，输出一组选股因子，用于筛选排序选股

                :input:
                h: 历史数据，一个3D numpy数组，包含所有股票在一个时间窗口内的所有类型的历史数据，
                    参考BaseStrategy的docstring
                r: 参考数据，一个2D numpy数组，包含一个时间窗口内所有参考类型的历史数据
                    参考BaseStrategy的docstring
                t: 交易数据，一个2D numpy数组，包含最近一次交易的实际结果
                    参考BaseStraegy的docstring

                :output
                signals: 一个代表交易信号的1D numpy数组，dtype为float


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

    def generate_one(self, h_seg, ref_seg=None, trade_data=None):
        """处理从_realize()方法传递过来的选股因子

        选出符合condition的因子，并将这些因子排序，根据次序确定所有因子相应股票的选股权重
        将选股权重传递到generate()方法中，生成最终的选股交易信号

        input:
            :type h_seg: np.ndarray
        :return
            numpy.ndarray, 一个一维向量，代表一个周期内股票的投资组合权重，所有权重的和为1
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

        factors = self.realize(h=h_seg, r=ref_seg, t=trade_data).squeeze()
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
        # 根据投资组合比例分配方式，确定被选中产品的权重
        if weighting == 'linear':  # linear 线性比例分配，将所有分值排序后，股票的比例呈线性分布
            dist = np.arange(1, 3, 2. / arg_count)  # 生成一个线性序列，最大值为最小值的约三倍
            chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
        # distance：距离分配，权重与其分值距离成正比，分值最低者获得一个基础比例，其余股票的比例
        # 与其分值的距离成正比，分值的距离为它与最低分之间的差值，因此不管分值是否大于0，股票都能
        # 获取比例分配
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
                           f'should be one of ["linear", "proportion", "even"]')
        return chosen

    @abstractmethod
    def realize(self,
                h,
                r=None,
                t=None):
        """ h_seg和ref_seg都是用于生成交易信号的一段窗口数据，根据这一段窗口数据
            生成一条交易信号
        """
        pass


class RuleIterator(BaseStrategy):
    """ 规则横向分配策略类。这一类策略不考虑每一只股票的区别，将同一套规则同时套用到所有的股票上。

        RuleIterator 策略类继承了交易策略基类

        Rolling_Timing类会自动把上述特定计算算法滚动应用到整个历史数据区间，并且推广到所有的个股中。

        * realize()方法的实现：realize()方法需要利用输入的参数，输出一组选股因子，用于筛选排序选股

            :input:
            h: 历史数据，一个2D numpy数组，包含一只股票在一个时间窗口内的所有类型的历史数据，
                示例：

            r: 参考数据，一个2D numpy数组，包含一个时间窗口内所有参考类型的历史数据
                参考BaseStrategy的docstring

            t: 交易数据，一个2D numpy数组，包含最近一次交易的实际结果
                参考BaseStraegy的docstring

            :output
            signals: 一个代表交易信号的1D numpy数组，dtype为float

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
        if ref_seg is None:
            ref_nonan = None
        else:
            ref_nonan = ref_seg[~np.isnan(ref_seg[:, 0])]

        try:
            return self.realize(h=hist_nonan,
                                r=ref_nonan,
                                t=trade_data,
                                pars=params)
        except Exception:
            return np.nan

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
