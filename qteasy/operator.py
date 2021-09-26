# coding=utf-8
# operator.py

# ======================================
# This file contains Operator class, that
# merges and applies investment strategies
# to generate operation signals with
# given history data.
# ======================================
import warnings

import pandas as pd
import numpy as np
from .finance import CashPlan
from .history import HistoryPanel
from .utilfuncs import str_to_list
from .strategy import Strategy
from .built_in import AVAILABLE_BUILT_IN_STRATEGIES, BUILT_IN_STRATEGIES

from .utilfuncs import mask_to_signal
from .blender import blender_parser


class Signal:
    """ 交易信号类，包含相关的属性和完整的交易信号清单。完整的交易信号包括以下属性：

        signal_type:    信号类型，
                            PT-仓位目标信号
                            PS-比例交易信号
                            VS-数量交易信号
        price_type:     价格类型：
                            0 - 市价交易信号
                            1 - 定价交易信号
        signal_matrix:  交易信号清单
        price_matrix:   交易价格清单，
                            当价格类型为0时，使用回测时的市场价格交易，价格清单中的数字代表市场价格类型
                            当价格类型为1时，使用固定的交易价格交易，价格清单中的数字代表给定的交易价格

        包含的方法有：

        merge:

    """

    def __init__(self, sig_type, price_type, op_matrix, price_matrix=None):
        """ 创建一个新的signal对象

        :param sig_type:
        :param price_type:
        :param sig_matrix:
        :param price_matrix:
        """
        # 检查输入数据是否符合要求，否则报错：

        # 属性赋值
        self._signal_type = sig_type
        self._price_type = price_type
        self._op_matrix = op_matrix
        if price_type == 'fixed':
            self._price_matrix = price_matrix
        else:
            self._price_matrix = None

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value):
        self._signal_type = value

    @property
    def price_type(self):
        return self._price_type

    @property
    def op(self):
        return self._op_matrix

    @property
    def prices(self):
        return self._price_matrix

    def blend(self, other, blend_type):
        """ blend self with other signal object

        :param blend_type:
        :return:
        """
        if not isinstance(other, Signal):
            raise TypeError(f'other should be another Signal object')
        if self.signal_type != other.signal_type:
            raise TypeError('Two signals should be of the same type')
        if self.price_type == 'fixed':
            raise ValueError(f'Only market price types can be blended')
        if self.price_type != other.price_type:
            raise ValueError(f'Two signals should have same type of market price')
        # depending on the signal type of self
        if self.signal_type == 'PT':
            return self._blend_pt(other, blend_type)
        if self.signal_type == 'PS':
            return self._blend_ps(other, blend_type)
        if self.signal_type == 'vs':
            return self._blend_vs(other, blend_type)

    def __and__(self, other):
        """ 最基本的信号混合方法之一： 与，数值上等于两个信号矩阵相乘（PT或PS）

        """
        raise NotImplementedError

    def __or__(self, other):
        """ 最基本的信号混合方法之一：或。数值上等于两个信号矩阵之和

        """
        raise NotImplementedError

    def __mul__(self, other):
        """ 最基本的信号混合方法之一；__and__()的别名

        """
        return self.__and__(other)

    def __add__(self, other):
        """ 最基本的信号混合方法之一：__or__()的别名

        """
        return self.__or__(other)

    # def


class Operator:
    """交易操作生成类，通过简单工厂模式创建择时属性类和选股属性类，并根据这两个属性类的结果生成交易清单

    根据输入的参数生成Operator对象，在对象中创建相应的策略类型:

    input:
            :param strategies: 一个包含多个字符串的列表，表示不同策略
            :param signal_type: 信号生成器的类型，可以使用三种不同的信号生成器，分别生成不同类型的信号：
                                pt：positional target，生成的信号代表某种股票的目标仓位
                                ps：proportion signal，比例买卖信号，代表每种股票的买卖百分比
                                VS：volume signal，数量买卖信号，代表每种股票的计划买卖数量

        Operator对象其实就是若干个不同类型的操作策略的容器对象，
        在一个Operator对象中，可以包含任意多个"策略对象"，而运行Operator生成交易信号的过程，就是调用这些不同的交易策略，并通过
        不同的方法对这些交易策略的结果进行组合的过程

        目前在Operator对象中支持三种信号生成器，每种信号生成器用不同的策略生成不同种类的交易信号：

        在同一个Operator对象中，每种信号生成器都可以使用不同种类的策略：

         Gen  \  strategy  | RollingTiming | SimpleSelecting | Simple_Timing | FactoralSelecting |
         ==================|===============|=================|===============|===================|
         Positional target |       Yes     |        Yes      |       Yes     |        Yes        |
         proportion signal |       Yes     |        Yes      |       Yes     |        Yes        |
         volume signal     |       Yes     |        Yes      |       Yes     |        Yes        |

        ==五种策略类型==

        目前Operator支持四种不同类型的策略，它们并不仅局限于生成一种信号，不同策略类型之间的区别在于利用历史数据并生成最终结果的
        方法不一样。几种生成类型的策略分别如下：

            1,  RollingTiming 逐品种滚动时序信号生成器，用于生成择时信号的策略

                这类策略的共同特征是对投资组合中的所有投资产品逐个考察其历史数据，根据其历史数据，在历史数据的粒度上生成整个时间段上的
                时间序列信号。时间序列信号可以为多空信号，即用>0的数字表示多头头寸，<0的数字代表空头头寸，0代表中性头寸。也可以表示交
                易信号，即>0的数字表示建多仓或平空仓，<0的数字表示见空仓或平多仓。

                这种策略生成器将投资组合中的每一个投资产品逐个处理，每个投资产品中的NA值可以单独处理，与其他投资品种不相关、互不影响，
                同时，每个投资产品可以应用不同的参数生成信号，是最为灵活的择时信号生成器。

                另外，为了避免前视偏差，滚动择时策略仅利用一小段有限的历史数据（被称为时间窗口）来生成每一个时间点上的信号，同时确保
                时间窗口总是处于需要计算多空位置那一点的过去。这种技术称为"时间窗口滚动"。这样的滚动择时信号生成方法适用于未来数据会
                对当前的信号产生影响的情况下。采用滚动择时策略生成方法，可以确保每个时间点的交易信号只跟过去一段时间有关，从而彻底排除
                前视偏差可能给策略带来的影响。

                不过，由于时间窗口滚动的计算方式需要反复提取一段时间窗口内的数据，并反复计算，因此计算复杂度与数据总量M与时间窗口长度N
                的乘积M*N成正比，效率显著低于简单时序信号生成策略，因此，在可能的情况下（例如，简单移动平均值相关策略不受未来价格影响）
                应该尽量使用简单时序信号生成策略，以提升执行速度。

            2,  SimpleSelecting 简单投资组合分配器，用于周期性地调整投资组合中每个个股的权重比例

                这类策略的共同特征是周期性运行，且运行的周期与其历史数据的粒度不同。在每次运行时，根据其历史数据，为潜在投资组合中的每
                一个投资产品分配一个权重，并最终确保所有的权重值归一化。权重为0时表示该投资产品被从组合中剔除，而权重的大小则代表投资
                过程中分配投资资金的比例。

                这种方式生成的策略可以用于生成周期性选股蒙板，也可以用于生成周期性的多空信号模板。

                这种生成方式的策略是针对历史数据区间运行的，是运算复杂度最低的一类生成方式，对于数量超大的投资组合，可以采用这种方式生
                成投资策略。但仅仅局限于部分周期性运行的策略。

            3,  SimpleTiming 逐品种简单时序信号生成器，用于生成择时信号的策略

                这类策略的共同特征是对投资组合中的所有投资产品逐个考察其历史数据，并在历史数据的粒度上生成整个时间段上的时间序列信号。
                这种策略生成方法与逐品种滚动时序信号生成策略的信号产生方法类似，只是缺少了"滚动"的操作，时序信号是一次性在整个历史区间
                上生成的，并不考虑未来数据对当前信号的影响。这类方法生成的信号既可以代表多空信号，也可以代表交易信号。

                同时，简单时序信号生成器也保留了滚动时序信号生成器的灵活性优点：每个投资产品独立处理，不同数据的NA值互不关联，互不影响，
                同时每个不同的投资产品可以应用完全不同的策略参数。最大的区别就在于信号不是滚动生成的。

                正因为没有采用滚动计算的方式，因此简单时序信号生成器的计算复杂度只有O(M),与历史数据数量M成正比，远小于滚动生成器。
                不过，其风险在于策略本身是否受未来数据影响，如果策略本身不受未来数据的影响，则采用简单时序生成器是一种较优的选择，例如，
                基于移动平均线相交的相交线策略、基于过去N日股价变动的股价变动策略本身具备不受未来信息影响的特点，使用滚动时序生成器和
                简单时序生成器能得到相同的结果，而简单时序生成器的计算耗时大大低于滚动时序生成器，因此应该采用简单滚动生成器。又例如，
                基于指数平滑均线或加权平均线的策略，或基于波形降噪分析的策略，其输出信号受未来信息的影响，如果使用简单滚动生成器将会
                导致未来价格信息对回测信号产生影响，因此不应该使用简单时序信号生成器。

            4,  FactoralSelecting 因子选股投资组合分配器，用于周期性地调整投资组合中每个个股的权重比例

                这类策略的共同特征是周期性运行，且运行的周期与其历史数据的粒度不同。在每次运行时，根据其历史数据，为每一个股票计算一个
                选股因子，这个选股因子可以根据任意选定的数据根据任意可能的逻辑生成。生成选股因子后，可以通过对选股因子的条件筛选和
                排序执行选股操作。用户可以在策略属性层面定义筛选条件和排序方法，同时可以选择不同的选股权重分配方式

                这种方式生成的策略可以用于生成周期性选股蒙板，也可以用于生成周期性的多空信号模板。

                这种生成方式的策略是针对历史数据区间运行的，是运算复杂度最低的一类生成方式，对于数量超大的投资组合，可以采用这种方式生
                成投资策略。但仅仅局限于部分周期性运行的策略。


        ==策略的三种信号类型==

        在Operator对象中，包含的策略可以有无限多个，但是Operator会将策略用于生成三种不同类型的信号，一个Operator对象只生成一种
        类型的信号，信号类型由Operator对象的SignalGenerator属性确定。

        Operator对象可以同时将多个策略用于生成同一种信号，为了确保输出唯一，多个策略的输出将被以某种方式混合，混合的方式是Operator
        对象的属性，定义了同样用途的不同策略输出结果的混合方式，以下是三种用途及其混合方式的介绍：

            信号类型1,  仓位目标信号(Positional Target，PT信号)：
                仓位目标信号代表在某个时间点上应该持有的各种投资产品的仓位百分比。信号取值从-100% ～ 100%，或者-1～1之间，代表在
                这个时间点上，应该将该百分比的全部资产投资到这个产品中。如果百分比为负数，代表应该持有空头仓位。
                应该注意的是，PT信号并不给出明确的操作或者交易信号，仅仅是给出一个目标仓位，是否产生交易信号需要检查当前实际持仓与
                目标持仓之间的差异来确定，当这个差值大于某一个阈值的时候，产生交易信号。这个阈值由QT级别的参数确定。

            信号类型2,  比例买卖信号(Proportional Signal，PS信号)：
                比例买卖信号代表每一个时间周期上计划买入或卖出的各个股票的数量，当信号代表买入时，该信号的数值代表计划买入价值占当时
                总资产的百分比；当信号代表卖出时，该信号的数值代表计划卖出的数量占当时该股票的持有数量的百分比，亦即：
                    - 当信号代表买入时，0.3代表使用占总资产30%的现金买入某支股票
                    - 当信号代表卖出时，-0.5代表卖出所持有的某种股票的50%的份额

            信号类型3:  数量买卖信号(Volume Signal，VS信号)：
                数量买卖信号代表每一个时间周期上计划买入或卖出的各个股票的数量，这个数量代表计划买卖数量，实际买卖数量受买卖规则影响，
                因此可能与计划买卖信号不同。例如： 500代表买入相应股票500股


        ==交易信号的混合==

            尽管同一个Operator对象同时只能生成一种类型的信号，但由于Operator对象能容纳无限多个不同的交易策略，因而Operator对象
            也能产生无限多组同类型的交易策略。为了节省交易回测时的计算开销，避免冲突的交易信号或重复的交易信号占用计算资源，同时也
            为了增加交易信号的灵活度，应该将所有交易信号首先混合成一组，再送入回测程序进行回测。

            不过，在一个Operator对象中，不同策略生成的交易信号可能运行的交易价格是不同的，例如，某些策略生成开盘价交易信号，而另一
            些策略生成的是收盘价交易策略，那么不同的交易价格信号当然不应该混合。但除此之外，只要是交易价格相同的信号，都应该全部混合。
            除非所有的额交易信号都是基于"固定价格"交易而不是"市场价格"交易的。所有以"固定价格"交易的信号都不能被混合，必须单独进入
            回测系统进行混合。

            交易信号的混合即交易信号的各种运算或函数，从简单的逻辑运算、加减运算一直到复杂的自定义函数，只要能够应用于一个ndarray的
            函数，理论上都可以用于混合交易信号，只要最终输出的交易信号有意义即可。

            交易信号的混合基于一系列事先定义的运算和函数，这些函数或运算都被称为"原子函数"或"算子"，用户利用这些"算子"来操作
            Operator对象生成的交易信号，并将多个交易信号组变换成一个唯一的交易信号组，同时保持其形状不变，数字有意义。

            交易信号的混合是由一个混合表达式来确定的，例如'0 and (1 + 2) * avg(3, 4)'

            上面的表达式表示了如何将五组交易信号变换为一组信号。表达式可以是任意合法的通用四则运算表达式，表达式中可以包含任意内建
            的信号算子或函数，用户可以相当自由地组合自己的混合表达式。表达式中的数字0～4代表Operator所生成的交易信号，这些数字也
            不必唯一，可以重复，也可以遗漏，如写成"1+1+1*2+max(1, 4)"是完全合法的，只是第二组信号会被重复使用四次，而第一组(0)和第
            四组(3)数据不会被用到而已。如果数字超过了信号的个数，则会使用最后一组信号，如"999+999"表达式被用于只有两组信号的Operator
            对象时，系统会把第二组信号相加返回。

            交易信号的算子包括以下这些：

            and: 0.5 and 0.5 = 0.5 * 0.5 = 0.25,
            or:  0.5 or 0.5 = 0.5 + 0.5 = 1
            orr: 0.5 orr 0.5 = 1 - (1 - 0.5) * (1 - 0.5) = 0.75
            not: not(1) = 1 - 1 = 0; not(0.3) = 1 - 0.3 = 0.7
            + :  0.5 + 0.5 = 1
            - :  1.0 - 0.5 = 0.5
            * :  0.5 * 0.5 = 0.25
            / :  0.25 / 0.5 = 0.5

            算子还包括以下函数：

            'chg-N()': N为正整数，取值区间为1到len(timing)的值，表示多空状态在第N次信号反转时反转
            'pos-N()': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
            'cumulative()': 在每个策略发生反转时都会产生交易信号，但是信号强度为1/len(timing)
            所有类型的交易信号都一样，只要交易价格是同一类型的时候，都应该混合为一组信号进入回测程序进行回测，混合的方式由混合
            字符串确定，字符串的格式为"[chg|pos]-0/9|cumulative"(此处应该使用正则表达式)

            'str-T()': T为浮点数，当多个策略多空蒙板的总体信号强度达到阈值T时，总体输出为1(或者-1)，否则为0
            'pos-N()': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                这种类型有一个变体：
                'pos-N-T': T为信号强度阈值，忽略信号强度达不到该阈值的多空蒙板信号，将剩余的多空蒙板进行计数，信号数量达到或
                超过N时，输出为1（或者-1），否则为0
            'avg()': 平均信号强度，所有多空蒙板的信号强度的平均值
            'combo()': 在每个策略发生反转时都会产生交易信号，信号的强度不经过衰减，但是通常第一个信号产生后，后续信号就再无意义

    """

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表

    AVAILABLE_BLENDER_TYPES = ['avg', 'avg_pos', 'pos', 'str', 'combo', 'none']
    AVAILABLE_SIGNAL_TYPES = {'position target':   'pt',
                              'proportion signal': 'ps',
                              'volume signal':     'vs'}

    def __init__(self, strategies=None, signal_type=None):
        """生成具体的Operator对象

        Operator对象的基本数据结构：包含四个列表加一个字典Dict，存储相关信息：
            _stg_id:            str, 交易策略列表，按照顺序保存所有相关策略对象的id（名称），如['MACD', 'DMA', 'MACD']
            _strategies:        :type: [Strategy, ...],
                                按照顺序存储所有的策略对象，如[Timing(MACD), Timing(timing_DMA), Timing(MACD)]
            _signal_history_data:
                                :type [ndarray, ...], 列表中按照顺序保存用于不同策略的三维历史数据切片
            _backtest_history_data:
                                :type [ndarray, ...], 列表中按照顺序保存用于不同策略回测的交易价格数据
            _op_blenders:       :type dict,
                                "信号混合"字典，包含不同价格类型交易信号的混合表达式，dict的键对应不同的
                                交易价格类型，每个值包含交易信号混合表达式，表达式存储为一个列表，表达式以逆波兰式
                                存储(RPN, Reversed Polish Notation)
        Operator对象的基本属性包括：
            signal_type:


        input:
            :param strategies: str, 用于生成交易信号的交易策略清单（以交易信号的id或交易信号对象本身表示）
            :param signal_type: str, 需要生成的交易信号的类型，包含一下三种类型
        """
        # 如果对象的种类未在参数中给出，则直接指定最简单的策略种类
        if isinstance(strategies, str):
            stg = str_to_list(strategies)
        elif isinstance(strategies, list):
            stg = strategies
        else:
            stg = []
        if signal_type is None:
            signal_type = 'pt'
        if (signal_type.lower() not in self.AVAILABLE_SIGNAL_TYPES) and \
                (signal_type.lower() not in self.AVAILABLE_SIGNAL_TYPES.values()):
            signal_type = 'pt'

        # 初始化基本数据结构
        self._signal_type = ''  # 保存operator对象输出的信号类型
        self._stg_types = []  # 保存所有交易策略的id，便于识别每个交易策略
        self._strategies = []  # 保存实际的交易策略对象
        self._signal_history_data = []  # 保存供各个策略生成交易信号的历史数据（ndarray）
        self._bt_history_data = []  # 保存供各个策略进行历史交易回测的历史价格数据（ndarray）
        self._stg_blender = {}  # 交易信号混合表达式字典

        # 添加strategy对象
        for s in stg:
            # 逐一添加所有的策略
            self.add_strategy(s)
        # 添加signal_type属性
        self.signal_type = signal_type

    @property
    def strategies(self):
        """返回operator对象的所有timing对象"""
        return self._strategies

    @property
    def strategy_count(self):
        """返回operator对象中的所有timing对象的数量"""
        return len(self.strategies)

    @property
    def strategy_names(self):
        """返回operator对象中所有交易策略对象的名称"""
        return [stg.stg_name for stg in self.strategies]

    @property
    def strategy_blenders(self):
        return self._stg_blender

    @property
    def signal_type(self):
        """ 返回operator对象的信号类型"""
        return self._signal_type

    @signal_type.setter
    def signal_type(self, st):
        """ 设置signal_type的值"""
        if not isinstance(st, str):
            raise TypeError(f'signal type should be a string, got {type(st)} instead!')
        elif st.lower() in self.AVAILABLE_SIGNAL_TYPES:
            self._signal_type = self.AVAILABLE_SIGNAL_TYPES[st.lower()]
        elif st.lower() in self.AVAILABLE_SIGNAL_TYPES.values():
            self._signal_type = st.lower()
        else:
            raise ValueError(f'the signal type {st} is not valid!')

    @property
    def op_data_types(self):
        """返回operator对象所有策略子对象所需数据类型的集合"""
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
    def op_data_freq(self):
        """返回operator对象所有策略子对象所需数据的采样频率"""
        d_freq = [stg.data_freq for stg in self.strategies]
        d_freq = list(set(d_freq))
        if len(d_freq) == 0:
            return ''
        if len(d_freq) == 1:
            return d_freq[0]
        warnings.warn(f'there are multiple history data frequency required by strategies', RuntimeWarning)
        return d_freq

    @property
    def bt_price_types(self):
        """返回operator对象所有策略子对象的回测价格类型"""
        p_types = [item.price_type for item in self.strategies]
        p_types = list(set(p_types))
        return p_types

    @property
    def op_history_data(self):
        """ 返回生成交易信号所需的历史数据列表"""
        return self._signal_history_data

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

         return: ranges, types
        """
        ranges = []
        types = []
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass  # 策略参数不参与优化
            elif stg.opt_tag == 1:
                # 所有的策略参数全部参与优化，且策略的每一个参数作为一个个体参与优化
                ranges.extend(stg.par_boes)
                types.extend(stg.par_types)
            elif stg.opt_tag == 2:
                # 所有的策略参数全部参与优化，但策略的所有参数组合作为枚举同时参与优化
                ranges.append(stg.par_boes)
                types.extend(['enum'])
        return ranges, types

    @property
    def opt_types(self):
        """返回所有策略的优化类型标签"""
        return [stg.opt_tag for stg in self.strategies]

    @property
    def max_window_length(self):
        """ 计算并返回operator对象所有子策略中最长的策略形成期。在准备回测或优化历史数据时，以此确保有足够的历史数据供策略形成

        :return: int
        """
        return max(stg.window_length for stg in self.strategies)

    @property
    def bt_price_type_count(self):
        """ 计算operator对象中所有子策略的不同回测价格类型的数量
        :return: int
        """
        return len(self.bt_price_types)

    @property
    def ready(self):
        """ 检查Operator对象是否已经准备好，可以开始生成交易信号，如果可以，返回True，否则返回False

        返回True，表明Operator的各项属性已经具备以下条件：
            1，
            2，

        :return:
        """
        raise NotImplementedError

    def __getitem__(self, item):
        """ 根据策略的名称或序号返回子策略"""
        item_is_int = isinstance(item, int)
        item_is_str = isinstance(item, str)
        if not (item_is_int or item_is_str):
            warnings.warn('the item is in a wrong format and can not be parsed!')
            return
        if item_is_str:
            if item not in self.strategy_names:
                warnings.warn('the strategy name can not be recognized!')
                return
            return self.get_strategy_by_name(item)
        strategy_count = self.strategy_count
        if item >= strategy_count - 1:
            item = strategy_count - 1
        return self.strategies[item]

    def add_strategy(self, stg, **kwargs):
        """ 添加一个strategy交易策略到operator对象中

        :param: stg, 需要添加的交易策略，可以为交易策略对象，也可以是内置交易策略的策略id或策略名称
        :param: kwargs, 任意合法的策略属性，可以在添加策略时直接给该策略属性赋值
        """
        # 如果输入为一个字符串时，检查该字符串是否代表一个内置策略的id或名称，使用.lower()转化为全小写字母
        if isinstance(stg, str):
            if stg.lower() not in AVAILABLE_BUILT_IN_STRATEGIES:
                raise KeyError(f'built-in timing strategy \'{stg}\' not found!')
            strategy_type = stg
            strategy = BUILT_IN_STRATEGIES[stg]
        # 当传入的对象是一个strategy对象时，直接添加该策略对象
        elif isinstance(stg, Strategy):
            strategy_type = stg.stg_type
            strategy = stg
        else:
            raise TypeError(f'The strategy type \'{type(stg)}\' is not supported!')

        self._stg_types.append(strategy_type)
        self._strategies.append(strategy)
        # 逐一修改该策略对象的各个参数
        self.set_parameter(stg_id=len(self._strategies), **kwargs)

    def remove_strategy(self, id_or_name=None):
        """从Operator对象中移除一个交易策略"""
        pos = -1
        if id_or_name is None:
            pos = -1
        if isinstance(id_or_name, int):
            if id_or_name < self.strategy_count:
                pos = id_or_name
            else:
                pos = -1
        if isinstance(id_or_name, str):
            if id_or_name not in self.strategy_names:
                raise ValueError(f'the strategy {id_or_name} is not in operator')
            else:
                pos = self.strategy_names.index(id_or_name)
        self._stg_types.pop(pos)
        self._strategies.pop(pos)
        return

    def clear_strategies(self):
        """clear all strategies

        :return:
        """
        raise NotImplementedError

    def get_strategies_by_price_type(self, price_type=None):
        """返回operator对象中的strategy对象, price_type为一个可选参数，
        如果给出price_type时，返回使用该price_type的交易策略

        :param price_type: str 一个可用的price_type

        """
        if price_type is None:
            return self._strategies
        else:
            return [stg for stg in self._strategies if stg.price_type == price_type]

    def get_strategy_count_by_price_type(self, price_type=None):
        """返回operator中的交易策略的数量, price_type为一个可选参数，
        如果给出price_type时，返回使用该price_type的交易策略数量"""
        return len(self.get_strategies_by_price_type(price_type))

    def get_strategy_names_by_price_type(self, price_type=None):
        """返回operator对象中所有交易策略对象的名称, price_type为一个可选参数，
        如果给出price_type时，返回使用该price_type的交易策略名称"""
        return [stg.stg_name for stg in self.get_strategies_by_price_type(price_type)]

    def get_strategy_by_name(self, stg_name):
        """ 根据输入的策略名称返回strategy对象"""
        assert stg_name.upper() in self.strategy_names, f'stg_name {stg_name} can not be found in operator. \n' \
                                                        f'{self.strategy_names}'
        stg_names = self.strategy_names
        strategies = self.strategies
        stg_idx = stg_names.index(stg_name.upper())
        print(f'getting strategy: \n{strategies[stg_idx]}')
        return strategies[stg_idx]

    def set_opt_par(self, opt_par):
        """optimizer接口函数，将输入的opt参数切片后传入stg的参数中

        :param opt_par:
            :type opt_par:Tuple
            一组参数，可能包含多个策略的参数，在这里被分配到不同的策略中

        :return
            None

        本函数与set_parameter()不同，在优化过程中非常有用，可以同时将参数设置到几个不同的策略中去，只要这个策略的opt_tag不为零
        在一个包含多个Strategy的Operator中，可能同时有几个不同的strategy需要寻优。这时，为了寻找最优解，需要建立一个Space，包含需要寻优的
        几个strategy的所有参数空间。通过这个space生成参数空间后，空间中的每一个向量实际上包含了不同的策略的参数，因此需要将他们原样分配到不
        同的策略中。

        举例如下：

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
                stg.set_pars(opt_par[s:k])
                s = k
            # 优化标记为2：该策略参与优化，用于优化的参数组的类型为枚举
            elif stg.opt_tag == 2:
                # 在这种情况下，只需要取出参数向量中的一个分量，赋值给策略作为参数即可。因为这一个分量就包含了完整的策略参数tuple
                k += 1
                stg.set_pars(opt_par[s])
                s = k

    # TODO: 完善本函数的Docstring，添加详细的使用介绍和示例
    def set_blender(self, price_type, blender):
        """ 统一的blender混合器属性设置入口

        :param price_type:
            :type price_type: str, 一个字符串，用于指定需要混合的交易信号的价格类型
        :param blender:
            :type blender: str, 一个合法的交易信号混合表达式

        :return
            None

        """
        if isinstance(price_type, str):
            self._stg_blender[price_type] = blender_parser(blender)
        else:
            raise TypeError(f'price_type should be a string, got {type(price_type)} instead')
        pass

    def get_blender(self, price_type=None):
        """返回operator对象中的多空蒙板混合器, 如果不指定price_type的话，输出完整的blender字典

        :param price_type: str 一个可用的price_type

        """
        if price_type is None:
            return self._stg_blender
        else:
            return self._stg_blender[price_type]

    def set_parameter(self,
                      stg_id: str,
                      pars: [tuple, dict] = None,
                      opt_tag: int = None,
                      par_boes: [tuple, list] = None,
                      par_types: [list, str] = None,
                      data_freq: str = None,
                      sample_freq: str = None,
                      window_length: int = None,
                      data_types: [str, list] = None,
                      price_type: str = None,
                      **kwargs):
        """ 统一的策略参数设置入口，stg_id标识接受参数的具体成员策略
            将函数参数中给定的策略参数赋值给相应的策略

            这里应该有本函数的详细介绍

            :param stg_id:
                :type stg_id: str, 策略的名称（ID），根据ID定位需要修改参数的策略

            :param pars:
                :type pars: tuple or dict , 需要设置的策略参数，格式为tuple

            :param opt_tag:
                :type opt_tag: int, 优化类型，0: 不参加优化，1: 参加优化, 2: 以枚举类型参加优化

            :param par_boes:
                :type par_boes: tuple or list, 策略取值范围列表,一个包含若干tuple的列表,代表参数中一个元素的取值范围，如
                [(0, 1), (0, 100), (0, 100)]

            :param par_types:
                :type par_types: str or list, 策略参数类型列表，与par_boes配合确定策略参数取值范围类型，详情参见Space类的介绍

            :param data_freq:
                :type data_freq: str, 数据频率，策略本身所使用的数据的采样频率

            :param sample_freq:
                :type sample_freq: str, 采样频率，策略运行时进行信号生成的采样频率，该采样频率决定了信号的频率

            :param window_length:
                :type window_length: int, 窗口长度：策略计算的前视窗口长度

            :param data_types:
                :type data_types: str or list, 策略计算所需历史数据的数据类型

            :param price_type:
                :type price_type: str, 策略回测交易时使用的交易价格类型

            :return:
        """
        assert isinstance(stg_id, (int, str)), f'stg_id should be a int, got {type(stg_id)} instead'
        # 根据策略的名称或ID获取策略对象
        if isinstance(stg_id, str):
            strategy = self.get_strategy_by_name(stg_id)
        else:
            strategy = self[stg_id]
        # 逐一修改该策略对象的各个参数
        if pars is not None:  # 设置策略参数
            if strategy.set_pars(pars):
                pass
            else:
                raise ValueError(f'parameter setting error')
        if opt_tag is not None:  # 设置策略的优化标记
            strategy.set_opt_tag(opt_tag)
        if par_boes is not None:  # 设置策略的参数优化边界
            strategy.set_par_boes(par_boes)
        if par_types is not None:  # 设置策略的参数类型
            strategy.par_types = par_types
        has_df = data_freq is not None
        has_sf = sample_freq is not None
        has_wl = window_length is not None
        has_dt = data_types is not None
        has_pt = price_type is not None
        if has_df or has_sf or has_wl or has_dt or has_pt:
            strategy.set_hist_pars(data_freq=data_freq,
                                   sample_freq=sample_freq,
                                   window_length=window_length,
                                   data_types=data_types,
                                   price_type=price_type)
        # 设置可能存在的其他参数
        strategy.set_custom_pars(**kwargs)

    # =================================================
    # 下面是Operation模块的公有方法：
    def info(self, verbose=False):
        """ 打印出当前交易操作对象的信息，包括选股、择时策略的类型，策略混合方法、风险控制策略类型等等信息
            如果策略包含更多的信息，还会打印出策略的一些具体信息，如选股策略的信息等
            在这里调用了私有属性对象的私有属性，不应该直接调用，应该通过私有属性的公有方法打印相关信息
            首先打印Operation木块本身的信息
            :type verbose: bool

        """
        print('OPERATOR INFO:')
        print('=' * 25)
        print('Information of the Module')
        print('=' * 25)
        # 打印各个子模块的信息：
        print(f'Total {self.strategy_count} operation strategies, requiring {self.op_data_type_count} '
              f'types of historical data:')
        all_op_data_types = []
        for data_type in self.op_data_types:
            all_op_data_types.append(data_type)
        print(", ".join(all_op_data_types))
        for price_type in self.bt_price_types:
            print(f'for backtest histoty price type: {price_type}: \n'
                  f'{self.get_strategies_by_price_type(price_type)}:')
            if self.strategy_blenders != {}:
                print(f'{self.get_blender(price_type)}')
            else:
                print(f'no blender')
        # 打印每个strategy的详细信息
        if verbose:
            print('Parameters of SimpleSelecting Strategies:')
            for stg in self.strategies:
                stg.info()
            print('=' * 25)

    # TODO 临时性使用cashplan作为参数之一，理想中应该只用一个"start_date"即可，这个Start_date可以在core.run()中具体指定，因为
    # TODO 在不同的运行模式下，start_date可能来源是不同的：
    def prepare_data(self, hist_data: HistoryPanel, cash_plan: CashPlan):
        """ 在create_signal之前准备好相关历史数据，检查历史数据是否符合所有策略的要求：

            检查hist_data历史数据的类型正确；
            检查cash_plan投资计划的类型正确；
            检查hist_data是否为空（要求不为空）；
            在hist_data中找到cash_plan投资计划中投资时间点的具体位置
            检查cash_plan投资计划中的每个投资时间点均有价格数据，也就是说，投资时间点都在交易日内
            检查cash_plan投资计划中第一次投资时间点前有足够的数据量，用于滚动回测
            检查cash_plan投资计划中最后一次投资时间点在历史数据的范围内
            从hist_data中根据各个量化策略的参数选取正确的切片放入各个策略数据仓库中

            然后，根据operator对象中的不同策略所需的数据类型，将hist_data数据仓库中的相应历史数据
            切片后保存到operator的各个策略历史数据属性中，供operator调用生成交易清单。

        :param hist_data:
            :type hist_data: HistoryPanel
            历史数据,一个HistoryPanel对象，应该包含operator对象中的所有策略运行所需的历史数据，包含所有
            个股所有类型的数据，例如，operator对象中存在两个交易策略，分别需要的数据类型如下：
                策略        所需数据类型
                ------------------------------
                策略A:   close, open, high
                策略B:   close, eps

            hist_data中就应该包含close、open、high、eps四种类型的数据
            数据覆盖的时间段和时间频率也必须符合上述要求

        :param cash_plan:
            :type cash_plan: CashPlan
            一个投资计划，临时性加入，在这里仅检查CashPlan与历史数据区间是否吻合，是否会产生数据量不够的问题

        :return:
            None
        """
        # 确保输入的历史数据是HistoryPanel类型
        if not isinstance(hist_data, HistoryPanel):
            raise TypeError(f'Historical data should be HistoryPanel, got {type(hist_data)}')
        # TODO: 临时性处理方式
        # 确保cash_plan的数据类型正确
        if not isinstance(cash_plan, CashPlan):
            raise TypeError(f'cash plan should be CashPlan object, got {type(cash_plan)}')
        # 确保输入的历史数据不为空
        if hist_data.is_empty:
            raise ValueError(f'history data can not be empty!')
        # 默认截取部分历史数据，截取的起点是cash_plan的第一个投资日，在历史数据序列中找到正确的对应位置
        first_cash_pos = np.searchsorted(hist_data.hdates, cash_plan.first_day)
        last_cash_pos = np.searchsorted(hist_data.hdates, cash_plan.last_day)
        # 确保回测操作的起点前面有足够的数据用于满足回测窗口的要求
        # TODO: 这里应该提高容错度，设置更好的回测历史区间设置方法，尽量使用户通过较少的参数设置就能完成基
        # TODO: 本的运行，不用过分强求参数之间的关系完美无缺，如果用户输入的参数之间有冲突，根据优先级调整
        # TODO: 相关参数即可，毋须责备求全。
        # TODO: 当运行模式为0时，不需要判断cash_pos与max_window_length的关系
        assert first_cash_pos >= self.max_window_length, \
            f'InputError, History data starts on {hist_data.hdates[0]} does not have enough data to cover' \
            f' first cash date {cash_plan.first_day}, ' \
            f'expect {self.max_window_length} cycles, got {first_cash_pos} records only'
        # 确保最后一个投资日也在输入的历史数据范围内
        # TODO: 这里应该提高容错度，如果某个投资日超出了历史数据范围，可以丢弃该笔投资，仅输出警告信息即可
        # TODO: 没必要过度要求用户的输入完美无缺。
        assert last_cash_pos < len(hist_data.hdates), \
            f'InputError, Not enough history data record to cover complete investment plan, history data ends ' \
            f'on {hist_data.hdates[-1]}, last investment on {cash_plan.last_day}'
        # 确认cash_plan的所有投资时间点都在价格清单中能找到（代表每个投资时间点都是交易日）
        invest_dates_in_hist = [invest_date in hist_data.hdates for invest_date in cash_plan.dates]
        if not all(invest_dates_in_hist):
            np_dates_in_hist = np.array(invest_dates_in_hist)
            where_not_in = [cash_plan.dates[i] for i in list(np.where(np_dates_in_hist == False)[0])]
            raise ValueError(f'Cash investment should be on trading days, '
                             f'following dates are not valid!\n{where_not_in}')
        # 确保op的策略都设置了参数
        assert all(stg.has_pars for stg in self.strategies), \
            f'One or more strategies has no parameter set properly!'
        # 确保op的策略都设置了混合方式
        # assert self._stg_blender != ''
        # 使用循环方式，将相应的数据切片与不同的交易策略关联起来
        self._signal_history_data = [hist_data[stg.data_types, :, (first_cash_pos - stg.window_length):]
                                     for stg in self.strategies]

    # TODO: 需要改进：
    # TODO: 供回测或实盘交易的交易信号应该转化为交易订单，并支持期货交易，因此生成的交易订单应该包含四类：
    # TODO: 1，Buy-开多仓，2，sell-平多仓，3，sel_short-开空仓，4，buy_to_cover-平空仓
    # TODO: 应该创建标准的交易订单模式，并且通过一个函数把交易信号转化为交易订单，以供回测或实盘交易使用

    # TODO: 需要调查：
    # TODO: 为什么在已经通过prepare_data()方法设置好了每个不同策略所需的历史数据之后，在create_signal()方法中还需要传入
    # TODO: hist_data作为参数？这个参数现在已经没什么用了，完全可以拿掉。在sel策略的generate方法中也不应该
    # TODO: 需要传入shares和dates作为参数。只需要selecting_history_data中的一部分就可以了
    def create_signal(self, hist_data: HistoryPanel):
        """ 操作信号生成方法，在输入的历史数据上分别应用选股策略、择时策略和风险控制策略，生成初步交易信号后，

        对信号进行合法性处理，最终生成合法交易信号
        input:
        :param hist_data:
            :type hist_data: HistoryPanel
            从数据仓库中导出的历史数据，包含多只股票在一定时期内特定频率的一组或多组数据
            ！！但是！！
            作为参数传入的这组历史数据并不会被直接用于交易信号的生成，用于生成交易信号的历史数据
            存储在operator对象的下面三个属性中，在生成交易信号时直接调用，避免了每次生成交易信号
            时再动态分配历史数据。
                self._selecting_history_data
                self._signal_history_data
                self._ricon_history_data

        :return=====
            list
            使用对象的策略在历史数据期间的一个子集上产生的所有合法交易信号，该信号可以输出到回测
            模块进行回测和评价分析，也可以输出到实盘操作模块触发交易操作
        """
        # 第一步，在历史数据上分别使用选股策略独立产生若干选股蒙板（sel_mask）
        # 选股策略的所有参数都通过对象属性设置，因此在这里不需要传递任何参数
        # 生成空的选股蒙板

        # 确保输入历史数据的数据格式正确；并确保择时策略和风控策略都已经关联号相应的历史数据
        # TODO: 这里的格式检查是否可以移到prepar_data()中去？这样效率更高
        assert isinstance(hist_data, HistoryPanel), \
            f'Type Error: historical data should be HistoryPanel, got {type(hist_data)}'
        assert len(self._signal_history_data) > 0, \
            f'ObjectSetupError: history data should be set before signal creation!'
        assert len(self._ricon_history_data) > 0, \
            f'ObjectSetupError: history data should be set before signal creation!'
        sel_masks = []
        shares = hist_data.shares
        date_list = hist_data.hdates
        # TODO， 使用map代替for loop可能能够再次提升运行速度
        for stg, dt in zip(self.strategies, self.op_history_data):  # 依次使用选股策略队列中的所有策略逐个生成选股蒙板
            # TODO: 目前选股蒙板的输入参数还比较复杂，包括shares和dates两个参数，应该消除掉这两个参数，使
            # TODO: sel.generate()函数的signature与tmg.generate()和ricon.generate()一致
            history_length = dt.shape[1]
            sel_masks.append(
                    stg.generate(hist_data=dt, shares=shares, dates=date_list[-history_length:]))
            # 生成的选股蒙板添加到选股蒙板队列中，

        op_signals = self._selecting_blend(sel_masks)  # 根据蒙板混合前缀表达式混合所有蒙板

        # 生成DataFrame，并且填充日期数据
        date_list = hist_data.hdates[-op_signals.shape[0]:]
        # TODO: 在这里似乎可以不用DataFrame，直接生成一个np.ndarray速度更快
        lst = pd.DataFrame(op_signals, index=date_list, columns=shares)
        # 定位lst中所有不全为0的行
        lst_out = lst.loc[lst.any(axis=1)]
        return lst_out

    def _set_strategy_blender(self, selecting_blender_expression):
        """ 设置选股策略的混合方式，混合方式通过选股策略混合表达式来表示

            给选股策略混合表达式赋值后，直接解析表达式，将选股策略混合表达式的前缀表达式存入选股策略混合器
        """
        if not isinstance(selecting_blender_expression, str):  # 如果输入不是str类型
            self._selecting_blender_string = '0'
            self._selecting_blender = ['0']
        else:
            self._selecting_blender_string = selecting_blender_expression
            try:
                self._selecting_blender = self._exp_to_blender
            except:
                raise ValueError(
                        f'SimpleSelecting blender expression is not Valid: (\'{selecting_blender_expression}\')'
                        f', the expression might contain unidentified operator, a valid expression contains only \n'
                        f'numbers, function or variable names and operations such as "+-*/^&|", for example: '
                        f'\' 0 & ( 1 | 2 )\'')