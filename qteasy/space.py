# coding=utf-8
# space.py

# ======================================
# This file contains Space class and
# Axis class. both are critical classes
# for strategy parameter optimization.
# ======================================

import numpy as np
import itertools
from .utilfuncs import str_to_list, input_to_list


class Space:
    """定义一个参数空间，一个参数空间包含一个或多个Axis对象，存储在axes列表中

    参数空间类用于生成并管理一个参数空间，从参数空间中根据一定的要求提取出一系列的参数点并组装成迭代器供优化器调用
    参数空间包含一个或多个轴，每个轴代表参数空间的一个维度，从每个轴上取出一个数值作为参数空间中某个点的坐标，而这个坐标
    就代表空间中的一个参数组合
    参数空间支持三种不同的轴，整数轴、浮点轴，这两种都是数值型的轴，还有另一种枚举轴，包含不同对象的枚举，同样可以作为参数
    空间的一个维度独立存在，与数值轴的操作方式相同
    数值轴的定义方式为上下界定义，枚举轴的定义方式为枚举定义，数值轴的取值范围为上下界之间的合法数值，而枚举轴的取值为枚举
    列表中的值
    """

    def __init__(self, pars, par_types: [list, str] = None):
        """参数空间对象初始化，根据输入的参数生成一个空间

        input:
            :param pars，int、float或list,需要建立参数空间的初始信息，通常为一个数值轴的上下界，如果给出了types，按照
                types中的类型字符串创建不同的轴，如果没有给出types，系统根据不同的输入类型动态生成的空间类型分别如下：
                    pars为float，自动生成上下界为(0, pars)的浮点型数值轴，
                    pars为int，自动生成上下界为(0, pars)的整形数值轴
                    pars为list，根据list的元素种类和数量生成不同类型轴：
                        list元素只有两个且元素类型为int或float：生成上下界为(pars[0], pars[1])的浮点型数值
                        轴或整形数值轴
                        list元素不是两个，或list元素类型不是int或float：生成枚举轴，轴的元素包含par中的元素
            :param par_types，list，默认为空，生成的空间每个轴的类型，如果给出types，应该包含每个轴的类型字符串：
                'discr': 生成整数型轴
                'conti': 生成浮点数值轴
                'enum': 生成枚举轴
        return: =====
            无
        """
        self._axis = []
        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        pars = list(pars)
        par_dim = len(pars)
        # debug
        # print('par types before processing:', par_types)
        if par_types is None:
            par_types = []
        elif isinstance(par_types, str):
            par_types = str_to_list(par_types, ',')
        par_types = input_to_list(par_types, par_dim, None)
        # debug：
        # print('par dim:', par_dim)
        # print('pars and par_types:', pars, par_types)
        # 逐一生成Axis对象并放入axes列表中
        self._axis = [Axis(par, par_type) for par, par_type in zip(pars, par_types)]

    @property
    def dim(self):  # 空间的维度
        return len(self._axis)

    @property
    def axis(self):
        return self._axis

    @property
    def types(self):
        """List of types of axis of the space"""
        if self.dim > 0:
            types = [ax.axis_type for ax in self.axis]
            return types
        else:
            return None

    @property
    def boes(self):
        """List of bounds of axis of the space"""
        if self.dim > 0:
            boes = [ax.axis_boe for ax in self.axis]
            return boes
        else:
            return None

    @property
    def shape(self):
        """输出空间的维度大小，输出形式为元组，每个元素代表对应维度的元素个数"""
        s = [ax.count for ax in self._axis]
        return tuple(s)

    @property
    def size(self):
        """输出空间的尺度，输出每个维度的跨度之乘积"""
        s = [ax.size for ax in self._axis]
        return np.product(s)

    @property
    def count(self):
        s = [ax.count for ax in self._axis]
        return np.product(s)

    def info(self):
        """打印空间的各项信息"""
        if self.dim > 0:
            print(type(self))
            print('dimension:', self.dim)
            print('types:', self.types)
            print('the bounds or enums of space', self.boes)
            print('shape of space:', self.shape)
            print('size of space:', self.size)
        else:
            print('Space is empty!')

    def extract(self, interval_or_qty: int = 1, how: str = 'interval'):
        """从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        input:
            :param interval_or_qty: int。从空间中每个轴上需要提取数据的步长或坐标数量
            :param how, str, 有两个合法参数：
                'interval',以间隔步长的方式提取坐标，这时候interval_or_qty代表步长
                'rand', 以随机方式提取坐标，这时候interval_or_qty代表提取数量
        return: tuple，包含两个数据
            iter，迭代器数据，打包好的所有需要被提取的点的集合
            total，int，迭代器输出的点的数量
        """
        interval_or_qty_list = input_to_list(pars=interval_or_qty,
                                             dim=self.dim,
                                             padder=[1])
        axis_ranges = [ax.extract(ioq, how) for ax, ioq in zip(self.axis, interval_or_qty_list)]
        total = np.array(list(map(len, axis_ranges))).prod()

        if how == 'interval':
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how == 'rand':
            return itertools.zip_longest(*axis_ranges), interval_or_qty  # 使用迭代器工具将所有点组合打包为点集

    def __contains__(self, point: [list, tuple]):
        """ 判断item是否在Space对象中, 返回True如果item在Space中，否则返回False

        :param point:
        :return: bool
        """
        assert isinstance(point, (list, tuple)), \
            f'TypeError, a point in a space must be in forms of a tuple or a list, got {type(point)}'
        if len(point) != self.dim:
            return False
        for coordinate, boe, type in zip(point, self.boes, self.types):
            if type == 'enum':
                if not coordinate in boe:
                    return False
            else:
                if not boe[0] < coordinate < boe[1]:
                    return False
        return True

    def from_point(self, point, distance: [int, float, list], ignore_enums=True):
        """在已知空间中以一个点为中心点生成一个字空间

        input:
            :param point，object，已知参数空间中的一个参数点
            :param distance， int或float，需要生成的新的子空间的数轴半径
            :param ignore_enums，bool，True忽略enum型轴，生成的子空间包含枚举型轴的全部元素，False生成的子空间
                包含enum轴的部分元素
        return: =====

        """
        assert point in self, f'ValueError, point {point} is not in space!'
        assert self.dim > 0, 'original space should not be empty!'
        assert isinstance(distance, (int, float, list)), \
            f'TypeError, the distance must be a number of a list of numbers, got {type(distance)} instead'
        pars = []
        if isinstance(distance, list):
            assert len(distance) == self.dim, \
                f'ValueError, can not match {len(distance)} distances in {self.dim} dimensions!'
        else:
            distance = [distance] * self.dim
        for coordinate, boe, type, dis in zip(point, self.boes, self.types, distance):
            if type != 'enum':
                space_lbound = boe[0]
                space_ubound = boe[1]
                lbound = max((coordinate - dis), space_lbound)
                ubound = min((coordinate + dis), space_ubound)
                pars.append((lbound, ubound))
            else:
                if ignore_enums:
                    pars.append(boe)
                else:
                    enum_pos = boe.index(coordinate)
                    lbound = max((enum_pos - dis), 0)
                    ubound = min((enum_pos + dis), len(boe))
                    pars.append(boe[lbound:ubound])
        return Space(pars, self.types)


class Axis:
    """数轴对象，空间对象的一个组成部分，代表空间对象的一个维度


    """

    def __init__(self, bounds_or_enum, typ=None):
        self._axis_type = None  # 数轴类型
        self._lbound = None  # 离散型或连续型数轴下界
        self._ubound = None  # 离散型或连续型数轴上界
        self._enum_val = None  # 当数轴类型为“枚举”型时，储存改数轴上所有可用值
        # 将输入的上下界或枚举转化为列表，当输入类型为一个元素时，生成一个空列表并添加该元素
        boe = list(bounds_or_enum)
        length = len(boe)  # 列表元素个数
        # debug
        # print('in Axis: boe recieved, and its length:', boe, length, 'type of boe:', typ)
        if typ is None:
            # 当typ为空时，需要根据输入数据的类型猜测typ
            if length <= 2:  # list长度小于等于2，根据数据类型取上下界，int产生离散，float产生连续
                if isinstance(boe[0], int):
                    typ = 'discr'
                elif isinstance(boe[0], float):
                    typ = 'conti'
                else:  # 输入数据类型不是数字时，处理为枚举类型
                    typ = 'enum'
            else:  # list长度为其余值时，全部处理为enum数据
                typ = 'enum'
        elif typ != 'enum' and typ != 'discr' and typ != 'conti':
            typ = 'enum'  # 当发现typ为异常字符串时，修改typ为enum类型
        # debug
        # print('in Axis, after infering typ, the typ is:', typ)
        # 开始根据typ的值生成具体的Axis
        if typ == 'enum':  # 创建一个枚举数轴
            self._new_enumerate_axis(boe)
        elif typ == 'discr':  # 创建一个离散型数轴
            if length == 1:
                self._new_discrete_axis(0, boe[0])
            else:
                self._new_discrete_axis(boe[0], boe[1])
        else:  # 创建一个连续型数轴
            if length == 1:
                self._new_continuous_axis(0, boe[0])
            else:
                self._new_continuous_axis(boe[0], boe[1])

    @property
    def count(self):
        """输出数轴中元素的个数，若数轴为连续型，输出为inf"""
        self_type = self._axis_type
        if self_type == 'conti':
            return np.inf
        elif self_type == 'discr':
            return self._ubound - self._lbound
        else:
            return len(self._enum_val)

    @property
    def size(self):
        """输出数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界"""
        self_type = self._axis_type
        if self_type == 'conti':
            return self._ubound - self._lbound
        else:
            return self.count

    @property
    def axis_type(self):
        """返回数轴的类型"""
        return self._axis_type

    @property
    def axis_boe(self):
        """返回数轴的上下界或枚举"""
        if self._axis_type == 'enum':
            return tuple(self._enum_val)
        else:
            return self._lbound, self._ubound

    def extract(self, interval_or_qty=1, how='interval'):
        """从数轴中抽取数据，并返回一个iterator迭代器对象

        input:
            :param interval_or_qty: int 需要从数轴中抽取的数据总数或抽取间隔，当how=='interval'时，代表抽取间隔，否则代表总数
            :param how: str 抽取方法，'interval' 或 'rand'， 默认'interval'
        return:
            一个迭代器对象，包含所有抽取的数值
        """
        if how == 'interval':
            if self.axis_type == 'enum':
                return self._extract_enum_interval(interval_or_qty)
            else:
                return self._extract_bounding_interval(interval_or_qty)
        else:
            if self.axis_type == 'enum':
                return self._extract_enum_random(interval_or_qty)
            else:
                return self._extract_bounding_random(interval_or_qty)

    def _set_bounds(self, lbound, ubound):
        """设置数轴的上下界, 只适用于离散型或连续型数轴

        input:
            :param lbound int/float 数轴下界
            :param ubound int/float 数轴上界
        return:
            None
        """
        self._lbound = lbound
        self._ubound = ubound
        self.__enum = None

    def _set_enum_val(self, enum):
        """设置数轴的枚举值，适用于枚举型数轴

        input:
            :param enum: 数轴枚举值
        :return:
            None
        """
        self._lbound = None
        self._ubound = None
        self._enum_val = np.array(enum, subok=True)

    def _new_discrete_axis(self, lbound, ubound):
        """ 创建一个新的离散型数轴

        input:
            :param lbound: 数轴下界
            :param ubound: 数轴上界
        :return:
            None
        """
        self._axis_type = 'discr'
        self._set_bounds(int(lbound), int(ubound))

    def _new_continuous_axis(self, lbound, ubound):
        """ 创建一个新的连续型数轴

        input:
            :param lbound: 数轴下界
            :param ubound: 数轴上界
        :return:
            None
        """
        self._axis_type = 'conti'
        self._set_bounds(float(lbound), float(ubound))

    def _new_enumerate_axis(self, enum):
        """ 创建一个新的枚举型数轴

        input:
            :param enum: 数轴的枚举值
        :return:
        """
        self._axis_type = 'enum'
        self._set_enum_val(enum)

    def _extract_bounding_interval(self, interval):
        """ 按照间隔方式从离散或连续型数轴中提取值

        input:
            :param interval: 提取间隔
        :return:
            np.array 从数轴中提取出的值对象
        """
        return np.arange(self._lbound, self._ubound, interval)

    def _extract_bounding_random(self, qty: int):
        """ 按照随机方式从离散或连续型数轴中提取值

        input:
            :param qty: 提取的数据总量
        :return:
            np.array 从数轴中提取出的值对象
        """
        if self._axis_type == 'discr':
            result = np.random.randint(self._lbound, self._ubound + 1, size=qty)
        else:
            result = self._lbound + np.random.random(size=qty) * (self._ubound - self._lbound)
        return result

    def _extract_enum_interval(self, interval):
        """ 按照间隔方式从枚举型数轴中提取值

        input:
            :param interval: 提取间隔
        :return:
            list 从数轴中提取出的值对象
        """
        count = self.count
        return self._enum_val[np.arange(0, count, interval)]

    def _extract_enum_random(self, qty: int):
        """ 按照随机方式从枚举型数轴中提取值

        input:
            :param qty: 提取间隔
        :return:
            list 从数轴中提取出的值对象
        """
        count = self.count
        return self._enum_val[np.random.choice(count, size=qty)]