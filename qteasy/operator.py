# coding=utf-8
# operator.py

# ======================================
# This file contains Operator class, that
# merges and applies investment strategies
# to generate operation signals with
# given history data.
# ======================================

import pandas as pd
import numpy as np
from .finance import CashPlan
from .history import HistoryPanel
from .utilfuncs import str_to_list
from .strategy import RollingTiming
from .strategy import SimpleSelecting
from .strategy import SimpleTiming
from .built_in import AVAILABLE_STRATEGIES, BUILT_IN_STRATEGY_DICT

from .utilfuncs import unify, mask_to_signal


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
            :param selecting_types: 一个包含多个字符串的列表，表示不同选股策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
            :param timing_types: 字符串列表，表示不同择时策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
            :param ricon_types: 字符串列表，表示不同风控策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入

        Operator对象其实就是若干个不同类型的操作策略的容器对象，
        在一个Operator对象中，可以包含任意多个"策略对象"，而运行Operator生成交易信号的过程，就是调用这些不同的交易策略，并通过
        不同的方法对这些交易策略的结果进行组合的过程

        目前在Operator对象中支持三种信号生成器，每种信号生成器用不同的策略生成不同种类的交易信号：

        在同一个Operator对象中，每种信号生成器都可以使用不同种类的策略：

         Gen  \  strategy  | RollingTiming | SimpleSelecting | Simple_Timing | FactoralSelecting |
         ==================|===============|=================|===============|===================|
         Positional target |       Yes     |        Yes      |       Yes     |        Yes        |
         ------------------|---------------|-----------------|---------------|-------------------|
         proportion signal |       Yes     |        Yes      |       Yes     |        Yes        |
         ------------------|---------------|-----------------|---------------|-------------------|
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

        在Operator对象中，包含的策略可以有无限多个，但是Operator会将策略用于生成三种不同类型的信号，不同种类的信号可以同时输出，但是
        不建议这么做，建议一个Operator对象只生成一种类型的信号。

        Operator对象可以同时将多个策略用于生成同一种信号，不过，为了确保输出唯一，多个策略的输出将被以某种方式混合，混合的方式是Operator
        对象的属性，定义了同样用途的不同策略输出结果的混合方式，以下是三种用途及其混合方式的介绍：

            信号类型1,  仓位目标信号（Positional Target，PT信号：
                仓位目标信号代表在某个时间点上应该持有的各种投资产品的仓位百分比。信号取值从-100% ～ 100%，或者-1～1之间，代表在
                这个时间点上，应该将该百分比的全部资产投资到这个产品中。如果百分比为负数，代表应该持有空头仓位。
                应该注意的是，PT信号并不给出明确的操作或者交易信号，仅仅是给出一个目标仓位，是否产生交易信号需要检查当前实际持仓与
                目标持仓之间的差异来确定，当这个差值大于某一个阈值的时候，产生交易信号。这个阈值由QT级别的参数确定。

                所有类型的交易信号都一样，只要交易价格是同一类型的时候，都应该混合为一组信号进入回测程序进行回测，混合的方式由混合
                字符串确定，字符串的格式为"[chg|pos]-0/9|cumulative"(此处应该使用正则表达式)

                'str-T': T为浮点数，当多个策略多空蒙板的总体信号强度达到阈值T时，总体输出为1(或者-1)，否则为0
                'pos-N': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                    这种类型有一个变体：
                    'pos-N-T': T为信号强度阈值，忽略信号强度达不到该阈值的多空蒙板信号，将剩余的多空蒙板进行计数，信号数量达到或
                    超过N时，输出为1（或者-1），否则为0
                'avg': 平均信号强度，所有多空蒙板的信号强度的平均值
                'comboo': 在每个策略发生反转时都会产生交易信号，信号的强度不经过衰减，但是通常第一个信号产生后，后续信号就再无意义

            信号类型2,  生成选股蒙板：
                选股蒙板定义了每一个时刻整个投资组合中每一个投资产品被分配到的权重。同样，如果定义了多个策略，也必须将它们的输出结果混
                合成一个

                选股蒙板的混合方式由一个逻辑表达式来确定，例如'0 and (1 or 2 and (3 or 4))'
                上面的表达式表示了如何根据五个选股蒙板来确定一个个股是否被选中而且权重多大。在目前的系统中，qteasy只是简单地将and运算
                处理为乘法，or运算处理为加法。在只有0和1的情况下这样做是没有问题的，但是在普遍蒙板中存在大量介于0和1之间的浮点数的
                时候，就需要注意了，如果蒙板0中某个股票的权重为0.5,在蒙板1中的权重为0.5，那么0 and 1 与0 or 1的结果分别应该是什么？

                目前这个问题的解决方式是：
                    0.5 and 0.5 = 0.5 * 0.5 = 0.25,
                    0.5 or 0.5 = 0.5 + 0.5 = 1
                完成上述计算后重新unify整个蒙板

                想到还有另一种解决方式：
                    0.5 and 0.5 = 0.5 * 0.5 = 0.25,
                    0.5 or 0.5 = 1 - (1 - 0.5) * (1 - 0.5) = 0.75
                同样在完成上述计算后unify整个蒙板

                孰优孰劣，还需要观察和试验，但是现在先把后一种方式写入代码中，后续再进行验证

            用途3:  生成交易信号矩阵：
                交易信号矩阵是由策略直接生成的交易信号组成的，如前所述，1代表开多仓或平空仓，-1代表平多仓或开空仓。与其他用途一样，如果
                多个策略被用于同样的用途，应该把多个策略的输出混合成一个最终输出。

                交易信号矩阵的混合方式跟多空蒙板的混合方式相似，以混合字符串赖定义。混合字符串的格式为"[chg|pos]-0/9|cumulative"

                'chg-N': N为正整数，取值区间为1到len(timing)的值，表示多空状态在第N次信号反转时反转
                'pos-N': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                'cumulative': 在每个策略发生反转时都会产生交易信号，但是信号强度为1/len(timing)

        ==策略的组合==

        以上三类策略通过不同的方式混合后，可以任意组合一种复杂的策略，因此，在qteasy系统中，复杂的策略是可以由很多个简单的策略组合而来
        的。
        在一个Operator对象中，作为容器可以容纳任意多个任意类型的策略，所有的策略以用途分成三组，所有的策略可以引用不同的历史数据，生成
        同样大小尺度的结果（也就是说，生成的结果有相同的历史区间，相同的时间粒度），最后这些结果被通过某种方法"混合"起来，形成每个用途
        的最终的结果，即多空模版、选股蒙板以及交易信号矩阵。
        三种用途的结果又再次被组合起来，变成整个Operator对象的输出。

        目前采用的组合方式是：

        mask_to_signal(多空模版 * 选股蒙板) + 交易信号
        其中mask_to_signal()函数的作用是将蒙板转化为交易信号，这样输出的就是交易信号

        未来将第三类策略升级为单品种信号生成策略后，信号的组合方式就可以变为：

        mask_to_signal(多空蒙板 * 选股蒙板）+ (交易信号 * 选股蒙板)
        这样同样可以输出一组交易信号

        但这样做还会有问题，预先生成交易信号在交易过程中存在MOQ时可能会发生这样的情况，在试图分多次建仓买入股票时，由于股票价值较高，导致
        分批建仓的信号每次都无法买入，解决的思路有两个，第一是在回测时不仅接受交易信号，还接受目标仓位，那么如果第一次建仓不够买入一手
        股票，到后续的目标仓位时总能有足够资金建仓。第二种是修改回测程序，在每次操作后记录理论操作数量和实际操作数量的差值，等下次有同方向
        操作的时候补齐差额。孰优孰劣？目前还没有想清楚。

    """

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表

    AVAILABLE_LS_BLENDER_TYPES = ['avg', 'avg_pos', 'pos', 'str', 'combo', 'none']

    def __init__(self, selecting_types=None,
                 timing_types=None,
                 ricon_types=None):
        """根据生成具体的对象

        input:
            :param selecting_types: 一个包含多个字符串的列表，表示不同选股策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
            :param timing_types: 字符串列表，表示不同择时策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
            :param ricon_types: 字符串列表，表示不同风控策略，后续可以考虑把字符串列表改为逗号分隔的纯字符串输入
        """
        # 对象属性：
        # 交易信号通用属性：

        # 如果对象的种类未在参数中给出，则直接指定最简单的策略种类
        if selecting_types is None:
            selecting_types = ['all']
        if isinstance(selecting_types, str):
            selecting_types = str_to_list(selecting_types)
        if timing_types is None:
            timing_types = ['long']
        if isinstance(timing_types, str):
            timing_types = str_to_list(timing_types)
        if ricon_types is None:
            ricon_types = ['ricon_none']
        if isinstance(ricon_types, str):
            ricon_types = str_to_list(ricon_types)
        # 在Operator对象中，对每一种类型的策略，需要三个列表对象加上一个字符串作为基本数据结构，存储相关信息：
        # 对于每一类型的策略，第一个列表是_stg_types， 按照顺序保存所有相关策略对象的种类字符串，如['MACD', 'DMA', 'MACD']
        # 第二个列表是_stg，按照顺序存储所有的策略对象，如[Timing(MACD), Timing(timing_DMA), Timing(MACD)]
        # 第三个列表是_stg_history_data, 列表中按照顺序保存用于不同策略的历史数据切片，格式均为np.ndarray，维度为三维
        # 字符串则是"混合"字符串，代表最终将所有的同类策略混合到一起的方式，对于不同类型的策略，混合方式定义不同
        # 以上的数据结构对于所有类型的策略都基本相同
        self._timing_types = []
        self._timing = []
        self._timing_history_data = []
        self._ls_blender = 'pos-1'  # 默认的择时策略混合方式
        for timing_type in timing_types:
            # 通过字符串比较确认timing_type的输入参数来生成不同的具体择时策略对象，使用.lower()转化为全小写字母
            if isinstance(timing_type, str):
                if timing_type.lower() not in AVAILABLE_STRATEGIES:
                    raise KeyError(f'built-in timing strategy \'{timing_type}\' not found!')
                self._timing_types.append(timing_type)
                self._timing.append(BUILT_IN_STRATEGY_DICT[timing_type]())
            # 当传入的对象是一个strategy时，直接
            elif isinstance(timing_type, (RollingTiming, SimpleTiming)):
                self._timing_types.append(timing_type.stg_type)
                self._timing.append(timing_type)
            else:
                raise TypeError(f'The timing strategy type \'{type(timing_type)}\' is not supported!')
        # 根据输入参数创建不同的具体选股策略对象。selecting_types及selectings属性与择时策略对象属性相似
        # 都是列表，包含若干相互独立的选股策略（至少一个）
        self._selecting_type = []
        self._selecting = []
        self._selecting_history_data = []
        # 生成选股蒙板生成策略清单
        cur_type = 0
        str_list = []

        for selecting_type in selecting_types:
            if cur_type == 0:
                str_list.append(str(cur_type))
            else:
                str_list.append(f' or {str(cur_type)}')
            cur_type += 1
            if isinstance(selecting_type, str):
                if selecting_type.lower() not in AVAILABLE_STRATEGIES:
                    raise KeyError(f'KeyError: built-in selecting type \'{selecting_type}\' not found!')
                self._selecting_type.append(selecting_type)
                self._selecting.append(BUILT_IN_STRATEGY_DICT[selecting_type]())
            elif isinstance(selecting_type, (SimpleSelecting, SimpleTiming)):
                self._selecting_type.append(selecting_type.stg_type)
                self._selecting.append(selecting_type)
            else:
                raise TypeError(f'Type Error, the type of object {type(selecting_type)} is not supported!')
        self._selecting_blender_string = ''.join(str_list)
        # create selecting blender by selecting blender string
        self._selecting_blender = self._exp_to_blender

        # 根据输入参数生成不同的风险控制策略对象
        self._ricon_type = []
        self._ricon = []
        self._ricon_history_data = []
        self._ricon_blender = 'add'
        for ricon_type in ricon_types:
            if isinstance(ricon_type, str):
                if ricon_type.lower() not in AVAILABLE_STRATEGIES:
                    raise KeyError(f'ricon type {ricon_type} not available!')
                self._ricon_type.append(ricon_type)
                self._ricon.append(BUILT_IN_STRATEGY_DICT[ricon_type]())
            elif isinstance(ricon_type, (RollingTiming, SimpleTiming)):
                self._ricon_type.append(ricon_type.stg_type)
                self._ricon.append(ricon_type)
            else:
                raise TypeError(f'Type Error, the type of passed object {type(ricon_type)} is not supported!')

    @property
    def timing(self):
        """返回operator对象的所有timing对象"""
        return self._timing

    @property
    def timing_count(self):
        """返回operator对象中的所有timing对象的数量"""
        return len(self.timing)

    @property
    def ls_blender(self):
        """返回operator对象中的多空蒙板混合器"""
        return self._ls_blender

    @property
    def selecting(self):
        """返回operator对象的所有selecting对象"""
        return self._selecting

    @property
    def selecting_count(self):
        """返回operator对象的所有selecting对象的数量"""
        return len(self.selecting)

    @property
    def selecting_blender(self):
        """返回operator对象的所有选股策略的选股结果混合器"""
        return self._selecting_blender_string

    @property
    def selecting_blender_expr(self):
        """返回operator对象的所有选股策略的选股结果的混合器表达式"""
        return self._selecting_blender

    @property
    def ricon(self):
        """返回operator对象的所有ricon对象"""
        return self._ricon

    @property
    def ricon_count(self):
        """返回operator对象的所有ricon对象的数量"""
        return len(self.ricon)

    @property
    def ricon_blender(self):
        """返回operator对象的所有ricon对象的混合器"""
        return self._ricon_blender

    @property
    def strategies(self):
        """返回operator对象的所有策略子对象"""
        stg = [item for item in self.timing + self.selecting + self.ricon]
        return stg

    @property
    def strategy_count(self):
        """返回operator对象的所有策略的数量"""
        return len(self.strategies)

    @property
    def strategy_blenders(self):
        return [self.ls_blender, self.selecting_blender, self.ricon_blender]

    @property
    def op_data_types(self):
        """返回operator对象所有策略子对象所需数据类型的集合"""

        d_types = [typ for item in self.strategies for typ in item.data_types]
        d_types = list(set(d_types))
        d_types.sort()
        return d_types

    @property
    def op_data_freq(self):
        """返回operator对象所有策略子对象所需数据的采样频率"""
        d_freq = [stg.data_freq for stg in self.strategies]
        d_freq = list(set(d_freq))
        assert len(d_freq) == 1, f'ValueError, there are multiple history data frequency required by strategies'
        return d_freq[0]

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
        prio = {'or':  0,
                'and': 1}
        # 定义两个队列作为操作堆栈
        s1 = []  # 运算符栈
        s2 = []  # 结果栈
        # TODO:
        # TODO: 读取字符串并读取字符串中的各个元素（操作数和操作符），当前使用str对象的split()方法进行，要
        # TODO: 求字符串中个元素之间用空格或其他符号分割，应该考虑写一个self.__split()方法，不依赖空格对
        # TODO: 字符串进行分割
        exp_list = self._selecting_blender_string.split()
        # 使用list()的问题是，必须确保表达式中不存在超过一位数字的数，如12等，同时需要去除字符串中的特殊字符如空格等
        # exp_list = list(self._selecting_blender_string.
        #                 replace(' ', '').
        #                 replace('_', '').
        #                 replace('.', '').
        #                 replace('-', ''))
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
            else:
                raise ValueError(f'unidentified characters found in blender string: \'{s}\'')
        while s1:
            s2.append(s1.pop())
        s2.reverse()  # 表达式解析完成，生成前缀表达式
        return s2

    def _exp_to_token(self, string):
        """ 将输入的blender-exp裁切成不同的元素(token)，包括数字、符号、函数等

        :return:
        """
        if not isinstance(string, str):
            raise TypeError()
        token_types = {'operation': 0,
                       'number': 1,
                       'function': 2,
                       'perenthesis': 3}
        tokens = []
        string = string.replace(' ', '')
        string = string.replace('\t', '')
        string = string.replace('\n', '')
        string = string.replace('\r', '')
        cur_token = ''
        prev_token_type = None
        cur_token_type = None
        for ch in string:
            if ch in '+*/^':
                cur_token_type = token_types['operation']
            if ch in '-':
                if prev_token_type == token_types['operation']:
                    cur_token_type = token_types['number']
                else:
                    cur_token_type = token_types['operation']
            if ch in '0123456789':
                # current token type will not change in this case
                cur_token_type = cur_token_type
            if ch in '.':
                # dots in numbers
                cur_token_type = token_types['number']
            if ch in 'abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                cur_token_type = token_types['function']
            if ch in '()':
                cur_token_type = token_types['perenthesis']
            if ch in ',':
                cur_token_type = None

            cur_token += ch
            if cur_token_type != prev_token_type:
                # new token to be added to list, and refresh prev/cur token types
                tokens.append(cur_token)
                prev_token_type = cur_token_type
                cur_token = ''

        return tokens

    def is_number(self, s):
        """ 判断一个字符串是否是一个合法的数字

        :param s:
        :return:
        """
        if not isinstance(s, str):
            return False
        if len(s) == 0:
            return False
        if all(ch in '-0123456789.' for ch in s):
            if s.count('.') + s.count('.') == len(s):
                return False
            if s.count('.') > 1 or s.count('-') > 1:
                return False
            if s.count('-') == 1 and s[0] != '-':
                return False
            if s[0] == '0' and s[1] != '.':
                return False
            return True
        return False

    @property
    def ready(self):
        """ assess if the operator is ready to generate

        :return:
        """
        raise NotImplementedError

    def add_strategy(self, stg, usage):
        """add strategy"""
        raise NotImplementedError

    def remove_strategy(self, stg):
        """remove strategy"""
        raise NotImplementedError

    def clear(self):
        """clear all strategies

        :return:
        """
        raise NotImplementedError

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
    def set_blender(self, blender_type, *args, **kwargs):
        """ 统一的blender混合器属性设置入口

        :param blender_type:
            :type blender_type: str, 一个字符串，用于指定被设置属性的混合器的类型，接收到可识别
            的输入后，调用不同的混合器设置函数，设置混合器

        :return
            None

        """
        if isinstance(blender_type, str):
            if blender_type.lower() in ['selecting', 'sel', 'select']:
                self._set_selecting_blender(*args, **kwargs)
            elif blender_type.lower() in ['ls', 'longshort', 'long_short']:
                self._set_ls_blender(*args, **kwargs)
            elif blender_type.lower() in ['ricon']:
                self._set_ricon_blender(*args, **kwargs)
            else:
                raise ValueError(f'wrong input! \'{blender_type}\' is not a valid input, '
                                 f'choose from [\'selecting\', \'sel\', \'ls\', \'ricon\']')
        else:
            raise TypeError(f'blender_type should be a string, got {type(blender_type)} instead')
        pass

    def set_parameter(self,
                      stg_id: str,
                      pars: [tuple, dict] = None,
                      opt_tag: int = None,
                      par_boes: [tuple, list] = None,
                      par_types: [list, str] = None,
                      sample_freq: str = None,
                      window_length: int = None,
                      data_types: [str, list] = None,
                      **kwargs):
        """ 统一的策略参数设置入口，stg_id标识接受参数的具体成员策略
            stg_id的格式为'x-n'，其中x为's/t/r'中的一个字母，n为一个整数

            这里应该有本函数的详细介绍

            :param stg_id:
                :type stg_id: str, 策略ID字符串，格式为x-N，表示第N个x类策略，x的取值范围为{'s', 't', 'r'},分别表示选股、择时和风控策略

            :param pars:
                :type pars: tuple or dict , 需要设置的策略参数，格式为tuple

            :param opt_tag:
                :type opt_tag: int, 优化类型，0: 不参加优化，1: 参加优化, 2: 以枚举类型参加优化

            :param par_boes:
                :type par_boes: tuple or list, 策略取值范围列表,一个包含若干tuple的列表,代表参数中一个元素的取值范围，如
                [(0, 1), (0, 100), (0, 100)]

            :param par_types:
                :type par_types: str or list, 策略参数类型列表，与par_boes配合确定策略参数取值范围类型，详情参见Space类的介绍

            :param sample_freq:
                :type sample_freq: str, 采样频率，策略运行时的采样频率

            :param window_length:
                :type window_length: int, 窗口长度：策略计算的前视窗口长度

            :param data_types:
                :type data_types: str or list, 策略计算所需历史数据的数据类型

            :return:
        """
        assert isinstance(stg_id, str), f'stg_id should be a string like \'t-0\', got {stg_id} instead'
        l = stg_id.split('-')
        assert len(l) == 2 and l[1].isdigit(), f'stg_id should be a string like \'t-0\', got {stg_id} instead'
        if l[0].lower() == 's':
            assert int(l[1]) < self.selecting_count, \
                f'ValueError: trying to set parameter for the {int(l[1]) + 1}-th selecting strategy but there\'s only' \
                f' {self.selecting_count} selecting strategy(s)'
            strategy = self.selecting[int(l[1])]
        elif l[0].lower() == 't':
            assert int(l[1]) < self.timing_count, \
                f'ValueError: trying to set parameter for the {int(l[1]) + 1}-th timing strategy but there\'s only' \
                f' {self.timing_count} timing strategies'
            strategy = self.timing[int(l[1])]
        elif l[0].lower() == 'r':
            assert int(l[1]) < self.ricon_count, \
                f'ValueError: trying to set parameter for the {int(l[1]) + 1}-th ricon strategy but there\'s only ' \
                f'{self.ricon_count} ricon strategies'
            strategy = self.ricon[int(l[1])]
        else:
            raise ValueError(f'The identifier of strategy is not recognized, should be like \'t-0\', got {stg_id}')
        if pars is not None:
            if strategy.set_pars(pars):
                pass
            else:
                raise ValueError(f'parameter setting error')
        if opt_tag is not None:
            strategy.set_opt_tag(opt_tag)
        if par_boes is not None:
            strategy.set_par_boes(par_boes)
        if par_types is not None:
            strategy.par_types = par_types
        has_sf = sample_freq is not None
        has_wl = window_length is not None
        has_dt = data_types is not None
        if has_sf or has_wl or has_dt:
            strategy.set_hist_pars(sample_freq=sample_freq,
                                   window_length=window_length,
                                   data_types=data_types)
        # set up additional properties of the class if they do exist:
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
        print('OPERATION MODULE INFO:')
        print('=' * 25)
        print('Information of the Module')
        print('=' * 25)
        # 打印各个子模块的信息：
        # 首先打印Selecting模块的信息
        print('Total count of SimpleSelecting strategies:', len(self._selecting))
        print('the blend type of selecting strategies is', self._selecting_blender_string)
        print('Parameters of SimpleSelecting Strategies:')
        for sel in self.selecting:
            sel.info()
        print('=' * 25)

        # 接着打印 timing模块的信息
        print('Total count of timing strategies:', len(self._timing))
        print('The blend type of timing strategies is', self._ls_blender)
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
        assert self.selecting_blender != ''
        assert self.ls_blender != ''
        assert self.ricon_blender != ''
        # 使用循环方式，将相应的数据切片与不同的交易策略关联起来
        self._selecting_history_data = [hist_data[stg.data_types, :, (first_cash_pos - stg.window_length):]
                                        for stg in self.selecting]
        # 用于择时仓位策略的数据需要包含足够的数据窗口用于滚动计算
        self._timing_history_data = [hist_data[stg.data_types, :, (first_cash_pos - stg.window_length):]
                                     for stg in self.timing]
        self._ricon_history_data = [hist_data[stg.data_types, :, (first_cash_pos - stg.window_length):]
                                    for stg in self.ricon]

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
                self._timing_history_data
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
        assert isinstance(hist_data, HistoryPanel), \
            f'Type Error: historical data should be HistoryPanel, got {type(hist_data)}'
        assert len(self._timing_history_data) > 0, \
            f'ObjectSetupError: history data should be set before signal creation!'
        assert len(self._ricon_history_data) > 0, \
            f'ObjectSetupError: history data should be set before signal creation!'
        sel_masks = []
        shares = hist_data.shares
        date_list = hist_data.hdates
        for sel, dt in zip(self._selecting, self._selecting_history_data):  # 依次使用选股策略队列中的所有策略逐个生成选股蒙板
            # TODO: 目前选股蒙板的输入参数还比较复杂，包括shares和dates两个参数，应该消除掉这两个参数，使
            # TODO: sel.generate()函数的signature与tmg.generate()和ricon.generate()一致
            history_length = dt.shape[1]
            sel_masks.append(
                    sel.generate(hist_data=dt, shares=shares, dates=date_list[-history_length:]))
            # 生成的选股蒙板添加到选股蒙板队列中，

        sel_mask = self._selecting_blend(sel_masks)  # 根据蒙板混合前缀表达式混合所有蒙板
        # sel_mask.any(0) 生成一个行向量，每个元素对应sel_mask中的一列，如果某列全部为零，该元素为0，
        # 乘以hist_extract后，会把它对应列清零，因此不参与后续计算，降低了择时和风控计算的开销
        # TODO: 这里本意是筛选掉未中选的股票，降低择时计算的开销，使用新的数据结构后不再适用，需改进以使其适用
        # hist_selected = hist_data * selected_shares
        # 第二步，使用择时策略在历史数据上独立产生若干多空蒙板(ls_mask)
        # 生成多空蒙板时忽略在整个历史考察期内从未被选中过的股票：
        # 依次使用择时策略队列中的所有策略逐个生成多空蒙板
        ls_masks = np.array([tmg.generate(dt) for tmg, dt in zip(self._timing, self._timing_history_data)])
        ls_mask = self._ls_blend(ls_masks)  # 混合所有多空蒙板生成最终的多空蒙板
        # 第三步，风险控制交易信号矩阵生成（简称风控矩阵）
        # 依次使用风控策略队列中的所有策略生成风险控制矩阵
        ricon_mats = np.array([ricon.generate(dt) for ricon, dt in zip(self._ricon, self._ricon_history_data)])
        ricon_mat = self._ricon_blend(ricon_mats)  # 混合所有风控矩阵后得到最终的风控策略

        # 使用mask_to_signal方法将多空蒙板及选股蒙板的乘积（持仓蒙板）转化为交易信号，再加上风控交易信号矩阵，并移除所有大于1或小于-1的信号
        # 生成交易信号矩阵
        if self._ls_blender != 'none':
            # 常规情况下，所有的ls_mask会先被混合起来，然后再与sel_mask相乘后生成交易信号，与ricon_mat相加
            op_mat = (mask_to_signal(ls_mask * sel_mask) + ricon_mat).clip(-1, 1)
        else:
            # 在ls_blender为"none"的时候，代表择时多空蒙板不会进行混合，分别与sel_mask相乘后单独生成交易信号，再与ricon_mat相加
            op_mat = (mask_to_signal(ls_mask * sel_mask).sum(axis=0) + ricon_mat).clip(-1, 1)
        # 生成DataFrame，并且填充日期数据
        date_list = hist_data.hdates[-op_mat.shape[0]:]
        # TODO: 在这里似乎可以不用DataFrame，直接生成一个np.ndarray速度更快
        lst = pd.DataFrame(op_mat, index=date_list, columns=shares)
        # 定位lst中所有不全为0的行
        lst_out = lst.loc[lst.any(axis=1)]
        return lst_out

    # ================================
    # 下面是Operation模块的私有方法
    def _set_ls_blender(self, ls_blender):
        """设置多空蒙板的混合方式，包括多种混合方式, 用于产生不同的混合效果。

        input:
            :param ls_blender:
                str，合法的输入包括：
                'combo':        combo表示……
                'none':         None表示……
                'str-T':        T为浮点数，取值区间为大于零的浮点数，当所有策略的多空信号强度之和大于T时，
                                输出信号为1或-1，没有中间地带
                'pos-N-T':      N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，
                                则为空，当策略的多空输出存在浮点数时， T表示判断某个多空值为多的阈值，
                                例如：
                                    'pos-2-0.2' 表示当至少有两个策略输出的多空值>0.2时，策略输出值
                                    为多，信号强度为所有多空信号之和。信号强度clip到(-1, 1)
                'avg_pos-N-T':  表示……
                'avg':          在每个策略发生反转时都会产生交易信号，总信号强度为所有策略信号强度的平均值

        return:=====
            None
        """
        # TODO: 使用regex判断输入的ls_blender各式是否正确
        assert isinstance(ls_blender, str), f'TypeError, expecting string but got {type(ls_blender)}'
        self._ls_blender = ls_blender

    def _set_selecting_blender(self, selecting_blender_expression):
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
                        f', all elements should be separated by blank space, for example: '
                        f'\' 0 and ( 1 or 2 )\'')

    def _set_ricon_blender(self, ricon_blender):
        self._ricon_blender = ricon_blender

    def _ls_blend(self, ls_masks):
        """ 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板
            这些多空模板的混合方式由混合字符串来定义。
            混合字符串是满足以下任意一种类型的字符串：

            1，  'none'
                模式表示输入的蒙板不会被混合，所有的蒙板会被转化为一个
                三维的ndarray返回,不做任何混合，在后续计算中采用特殊计算方式
                # 分别计算每一个多空蒙板的交易信号，然后再将交易信号混合起来.

            2,  'avg':
                avg方式下，持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，
                只有所有蒙板均看空时，最终结果才看空所有蒙板的权重相同，因此，如
                果一共五个蒙板三个看多两个看空时，持仓为60%。更简单的解释是，混
                合后的多空仓位是所有蒙版仓位的平均值.

            3,  '[pos]/[avg-pos](-N)(-T)'
                格式为满足以上正则表达式的字符串，其混合规则如下：
                在pos-N方式下，
                最终的多空信号强度取决于蒙板集合中各个蒙板的信号值，只有满足N个以
                上的蒙板信号值为多(>0)或者为空(<0)时，最终蒙板的多空信号才为多或
                为空。最终信号的强度始终为-1或1，如果希望最终信号强度为输入信号的
                平均值，应该使用avg_pos-N方式混合

                pos-N还有一种变体，即pos-N-T模式，在这种模式下，N参数仍然代表看
                多的参数个数阈值，但是并不是所有判断持仓为正的数据都会被判断为正
                只有绝对值大于T的数据才会被接受，例如，当T为0.25的时候，0.35会
                被接受为多头，但是0.15不会被接受为多头，因此尽管有两个策略在这个
                时间点判断为多头，但是实际上只有一个策略会被接受.

                avg_pos-N方式下，
                持仓同样取决于看多的蒙板的数量，只有满足N个或更多蒙板看多时，最终结果
                看多，否则看空，在看多/空情况下，最终的多空信号强度=平均多空信号强度
                。当然，avg_pos-1与avg等价，如avg_pos-2方式下，至少两个蒙板看多
                则最终看多，否则看空

                avg_pos-N还有一种变体，即avg_pos-N-T模式，在通常的模式下加
                入了一个阈值Threshold参数T，用来判断何种情况下输入的多空蒙板信号
                可以被保留，当T大于0时，只有输入信号绝对值大于T的时候才会被接受为有
                意义的信号否则就会被忽略。使用avg_pos-N-T模式，并把T设置为一个较
                小的浮点数能够过滤掉一些非常微弱的多空信号.

            4，  'str-T':
                str-T模式下，持仓只能为0或+1，只有当所有多空模版的输出的总和大于
                某一个阈值T的时候，最终结果才会是多头，否则就是空头

            5,  'combo':
                在combo模式下，所有的信号被加总合并，这样每个所有的信号都会被保留，
                虽然并不是所有的信号都有效。在这种模式下，本意是原样保存所有单个输入
                多空模板产生的交易信号，但是由于正常多空模板在生成卖出信号的时候，会
                运用"比例机制"生成卖出证券占持有份额的比例。这种比例机制会在针对
                combo模式的信号组合进行计算的过程中产生问题。
                例如：在将两组信号A和B合并到一起之后，如果A在某一天产生了一个股票
                100%卖出的信号，紧接着B在接下来的一天又产生了一次股票100%卖出的信号，
                两个信号叠加的结果，就是产生超出持有股票总数的卖出数量。将导致信号问题

        input：=====
            :type: ls_masks：object ndarray, 多空蒙板列表，包含至少一个多空蒙板
        return：=====
            :rtype: object: 一个混合后的多空蒙板
        """
        try:
            blndr = str_to_list(self._ls_blender, '-')  # 从对象的属性中读取择时混合参数
        except:
            raise TypeError(f'the timing blender converted successfully!')
        assert isinstance(blndr[0], str) and blndr[0] in self.AVAILABLE_LS_BLENDER_TYPES, \
            f'extracted blender \'{blndr[0]}\' can not be recognized, make sure ' \
            f'your input is like "str-T", "avg_pos-N-T", "pos-N-T", "combo", "none" or "avg"'
        l_m = ls_masks
        l_m_sum = np.sum(l_m, 0)  # 计算所有多空模版的和
        l_count = ls_masks.shape[0]
        # 根据多空蒙板混合字符串对多空模板进行混合
        if blndr[0] == 'none':
            return l_m
        if blndr[0] == 'avg':
            return l_m_sum / l_count
        if blndr[0] == 'pos' or blndr[0] == 'avg_pos':
            l_m_sign = 0.
            n = int(blndr[1])
            if len(blndr) == 3:
                threshold = float(blndr[2])
                for msk in ls_masks:
                    l_m_sign += np.sign(np.where(np.abs(msk) < threshold, 0, msk))
            else:
                for msk in ls_masks:
                    l_m_sign += np.sign(msk)
            if blndr[0] == 'pos':
                res = np.where(np.abs(l_m_sign) >= n, l_m_sign, 0)
                return res.clip(-1, 1)
            if blndr[0] == 'avg_pos':
                res = np.where(np.abs(l_m_sign) >= n, l_m_sum, 0) / l_count
                return res.clip(-1, 1)
        if blndr[0] == 'str':
            threshold = float(blndr[1])
            return np.where(np.abs(l_m_sum) >= threshold, 1, 0) * np.sign(l_m_sum)
        if blndr[0] == 'combo':
            return l_m_sum
        raise ValueError(f'Blender text \'({blndr})\' not recognized!')

    def _selecting_blend(self, sel_masks):
        """ 选股策略混合器，将各个选股策略生成的选股蒙板按规则混合成一个蒙板

        input:
            :param sel_masks:
        :return:
            ndarray, 混合完成的选股蒙板
        """
        exp = self._selecting_blender[:]
        s = []
        while exp:  # 等同于但是更好: while exp != []
            if exp[-1].isdigit():
                s.append(sel_masks[int(exp.pop())])
            else:
                s.append(self._blend(s.pop(), s.pop(), exp.pop()))
        return unify(s[0])

    def _blend(self, n1, n2, op):
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
        elif op == 'orr':
            return 1 - (1 - n1) * (1 - n2)
        else:
            raise ValueError(f'ValueError, unknown operand, {op} is not an operand that can be recognized')

    def _ricon_blend(self, ricon_mats):
        if self._ricon_blender == 'add':
            return ricon_mats.sum(axis=0)
        raise NotImplementedError(f'ricon singal blender method ({self._ricon_blender}) is not supported!')

    def blender_parser(self, blender_string: str = None) -> list:
        """ 最关键的信号混合引擎的核心，将一个合法的混合字符串解析为一个可以被混合引擎调用的混合方法组
        
            混合方法组blenders是一个list，里面按照执行顺序放置了所有的混合运算
            Operator核心根据清单中的混合运算类型，将所有生成的运行交易信号混合起来
            形成一组最终的混合信号
        
        """
        raise NotImplementedError