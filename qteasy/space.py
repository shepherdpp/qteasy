# coding=utf-8
# ======================================
# File:     space.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-09-30
# Desc:
#   parameter Space Class and ResultPool
#   Class for strategy optimization.
# ======================================

import numpy as np
import itertools
import warnings

from typing import Union, Iterable

from qteasy.utilfuncs import (
    input_to_list,
)
from qteasy.parameter import Parameter


class Space:
    """定义一个参数空间，一个参数空间包含一个或多个Axis对象，存储在axes列表中

    参数空间类用于生成并管理一个参数空间，从参数空间中根据一定的要求提取出一系列的参数点并组装成迭代器供优化器调用
    参数空间包含一个或多个轴，每个轴代表参数空间的一个维度，从每个轴上取出一个数值作为参数空间中某个点的坐标，而这个坐标
    就代表空间中的一个参数组合
    参数空间支持三种不同的轴，整数轴、浮点轴，这两种都是数值型的轴，还有另一种枚举轴，包含不同对象的枚举，同样可以作为参数
    空间的一个维度独立存在，与数值轴的操作方式相同
    数值轴的定义方式为上下界定义，枚举轴的定义方式为枚举定义，数值轴的取值范围为上下界之间的合法数值，而枚举轴的取值为枚举
    列表中的值

    Properties
    ----------
    dim: int
        参数空间的维度，即轴的数量
    axis: list
        参数空间的轴列表，每个轴都是一个Axis对象
    size: int
        参数空间的大小，即参数空间中参数点的数量
    shape: tuple
        参数空间的形状，即每个轴的长度，用于生成网格坐标
    volume: float
        参数空间的体积，即参数空间中所有参数点的坐标的乘积，用于计算参数空间的密度
    count: int
        参数空间中所有参数点的数量，如果存在连续轴，数量为inf

    Methods
    -------
    extract(qty, how='interval'):
        从参数空间中提取参数点，返回一个参数点的迭代器

    Examples
    --------
    >>> space = Space([(1, 5), (3., 10.), (5, 6, 7, 8, 9)])
    <(1, 5),(3.0, 10.0),(5,...,9)>
    >>> space.dim
    3
    >>> space.axis
    [<Int Parameter: (1, 5)>, <Float Parameter: (3.0, 10.0)>, <Enum Parameter: (5, 6, 7, 8, 9)>]
    >>> space.size
    100
    >>> space.volume
    400.0
    >>> space.shape
    (5, 7, 5)
    >>> space.count
    inf
    >>> space.types
    ['int', 'float', 'enum']
    >>> list(space.extract(4, how='interval')[0])
    [(1, 3.0, 5),
     (1, 3.0, 9),
     (1, 7.0, 5),
     (1, 7.0, 9),
     (5, 3.0, 5),
     (5, 3.0, 9),
     (5, 7.0, 5),
     (5, 7.0, 9)]
    >>> list(space.extract(8, how='rand')[0])
    [(1, 7.928856883024961, 9),
     (3, 9.764777688087385, 8),
     (4, 8.445573333306598, 5),
     (1, 7.7484413238800105, 9),
     (1, 8.943201541252197, 9),
     (4, 3.315940540291259, 7),
     (1, 3.3702544943635155, 7),
     (1, 7.595081100116288, 8)]
    """

    def __init__(self,
                 *par_ranges: Union[Iterable, Parameter, list[Parameter]],
                 par_types: Union[list[str], str] = None
                 ):
        """参数空间对象初始化，根据输入的参数生成一个空间

        Parameters
        ----------
        *par_ranges: tuple, list of tuple, Parameter, list of Parameter
            参数空间中包括的参数，可以输入参数对象，参数对象的列表或者参数的范围列表
            参数范围的列表和参数对象不能混合输入。
            如果输入参数对象，则生成一个包含这些参数对象的参数空间，此时不需要输入par_types参数
            如果输入参数范围列表，则根据par_types参数生成不同类型的参数对象，如果不输入par_types参数，
            则根据参数范围自动判断参数类型
        par_types: list of str or str, optional
            生成的空间每个轴的类型，如果不给出types，会根据输入的pars自动判断，如果给出types，会根据types中
            的类型字符串创建不同的轴，types中的类型字符串分别如下：
            'int'/'discr':      生成整数型轴
            'float'/'conti':    生成浮点数值轴
            'enum':             生成枚举轴
            ‘array’:            生成数组轴，数组轴的元素为一个数组

        Returns
        -------
        Space object

        Examples
        --------
        # 直接输入Parameter对象
        >>> par1 = Parameter((1, 5), 'int')
        >>> par2 = Parameter((3., 10.), 'float')
        >>> par3 = Parameter((5, 6, 7, 8, 9), 'enum')
        >>> space = Space(par1, par2, par3)
        <(1, 5),(3.0, 10.0),(5,...,9)>
        # 输入Parameter对象列表
        >>> space = Space((1, 5), (3., 10.), (5, 6, 7, 8, 9))
        <(1, 5),(3.0, 10.0),(5,...,9)>
        # 输入参数范围列表，并指定每个参数的类型
        >>> space = Space((1, 5), (3., 10.), (5, 6, 7, 8, 9), par_types=['float', 'int', 'int'])
        <(1.0, 5.0),(3, 10),(5, 6)>
        """
        self._axis = []
        # import pdb; pdb.set_trace()
        # 处理输入，如果pars参数为Parameter对象，则直接使用
        if any(isinstance(par, Parameter) for par in par_ranges):
            if not all(isinstance(par, Parameter) for par in par_ranges):
                raise TypeError('All elements in pars should be Parameter objects if pars contains Parameter objects')
            self._axis = list(par_ranges)
            return

        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        par_ranges = list(par_ranges)
        par_dim = len(par_ranges)
        if par_types is None:
            par_types = []
        if isinstance(par_types, str):
            par_types = [par_types]
        if not isinstance(par_types, list):
            raise TypeError(f'par_types should be a list of strings, got {type(par_types)} instead')
        if not all(isinstance(pt, (str, type(None))) for pt in par_types):
            raise TypeError('All elements in par_types should be strings or None')

        par_types = input_to_list(par_types, par_dim, None)
        # 预处理par_types
        for i in range(len(par_types)):
            if par_types[i] is None:
                continue
            elif par_types[i].lower() in ['int', 'discr']:
                par_types[i] = 'int'
            elif par_types[i].lower() in ['float', 'conti']:
                par_types[i] = 'float'
            elif par_types[i].lower() in ['enum', 'enumerate']:
                par_types[i] = 'enum'
            else:
                continue
                # raise KeyError(f'Invalid parameter type: {par_types[i]}')
        # 逐一生成Axis对象并放入axes列表中
        self._axis = [Parameter(par, par_type=par_type) for par, par_type in zip(par_ranges, par_types)]

    @property
    def dim(self):  # 空间的维度
        """返回参数空间的维度，即轴的数量

        Returns
        -------
        int
            参数空间的维度
        """
        return len(self._axis)

    @property
    def axis(self):
        """返回参数空间的轴列表，每个轴都是一个Axis对象"""
        return self._axis

    @property
    def types(self):
        """List of types of axis of the space"""
        if self.dim > 0:
            types = [ax.par_type for ax in self.axis]
            return types
        else:
            return None

    @property
    def boes(self):
        """List of bounds of axis of the space"""
        if self.dim > 0:
            boes = [ax.par_range for ax in self.axis]
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
        return tuple(s)

    @property
    def volume(self):
        """输出空间的尺度，输出每个维度的跨度之乘积"""
        s = [ax.size for ax in self._axis]
        # return np.product(s)  # np.product() will be deprecated in the future
        return np.prod(s)

    @property
    def count(self):
        s = [ax.count for ax in self._axis]
        # return np.product(s)  # np.product() will be deprecated in the future
        return np.prod(s)

    def __repr__(self):
        output = []
        for item in self.boes:
            if len(item) <= 3:
                output.append(str(item))
            else:
                output.append(f'({item[0]},...,{item[-1]})')
        return '<' + ','.join(output) + '>'

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

    def extract(self, quantities: Union[int, list[int]] = 1, how: str = 'interval'):
        """从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        Parameters
        ----------
        quantities: int or list of int, default 1
            从空间中每个轴上需要提取数据的点的数量
        how: str, default 'interval', {'interval', 'intv', 'step', 'rand', 'random'}
            合法参数：
            interval/intv/step,以间隔步长的方式提取坐标，这时候interval_or_qty代表步长
            rand/random, 以随机方式提取坐标，这时候interval_or_qty代表提取数量

        Returns
        -------
        tuple (iter, total)
            iter，迭代器数据，打包好的所有需要被提取的点的集合
            total，int，迭代器输出的点的数量

        Examples
        --------
        >>> space = Space((1, 10), (3, 10), (5, 6, 7, 8, 9))
        >>> space
        <(1, 10),(3, 10),(5,...,9)>
        >>> list(space.extract([2, 2, 2], how='interval')[0])
        [(1, 3.0, 5),
         (1, 3.0, 9),
         (1, 10.0, 5),
         (1, 10.0, 9),
         (10, 3.0, 5),
         (10, 3.0, 9),
         (10, 10.0, 5),
         (10, 10.0, 9)]
        >>> list(space.extract(8, how='rand')[0])
        [(1, 7.928856883024961, 9),
         (3, 9.764777688087385, 8),
         (4, 8.445573333306598, 5),
         (1, 7.7484413238800105, 9),
         (1, 8.943201541252197, 9),
         (4, 3.315940540291259, 7),
         (1, 3.3702544943635155, 7),
         (1, 7.595081100116288, 8)]
        """
        interval_or_qty_list = input_to_list(pars=quantities,
                                             dim=self.dim,
                                             padder=[1])
        axis_ranges = [ax.gen_values(qty, how) for ax, qty in zip(self.axis, interval_or_qty_list)]
        total = np.array(list(map(len, axis_ranges))).prod()
        if self.types == ['enum'] and isinstance(self.boes[0], tuple):
            # in this case, space is an enum of tuple parameters, no formation of tuple is needed
            return axis_ranges[0], len(axis_ranges[0])
        if how in ['interval', 'intv', 'step']:
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how in ['rand', 'random']:
            return itertools.zip_longest(*axis_ranges), quantities  # 使用迭代器工具将所有点组合打包为点集
        else:
            raise KeyError(f'Invalid extraction method: {how}\n'
                           f'Valid methods are: "interval" or "rand"')

    def __contains__(self, item: Union[list, tuple, object]):
        """ 判断item是否在Space对象中, 返回True如果item在Space中，否则返回False

        Parameters
        ----------
        item: list or tuple of coordinates or a Space
            要判断的对象，必须是一个坐标点或者一个子空间

        Returns
        -------
        bool

        Examples
        --------
        >>> s = Space(('x', 'y'), (0, 10), par_types=['enum','int'])
        <('x', 'y'),(0, 10)>
        >>> ('x', 6) in s
        True
        >>> ('z', 6) in s
        False
        >>> ('x', 15) in s
        False

        """
        assert isinstance(item, (list, tuple, Space)), \
            f'TypeError, the item must be a point (tuple or list of coordinates) or a subspace, got {type(item)}'
        if isinstance(item, (tuple, list)):  # if item is a point, all parameter should be in its range
            if len(item) != self.dim:
                return False
            return all(cordi in ax for cordi, ax in zip(item, self.axis))
        else:  # if item is a space, check if all boes are within self boes
            if item.dim != self.dim:  # different dimensions
                return False
            if any(item_type != self_type for item_type, self_type in zip (item.types, self.types)):
                # different par types
                return False
            if any(item_type in ['float_array', 'int_array'] for item_type in item.types):
                # check array shapes
                item_array_axis = [item for item, t in zip(item.axis, item.types) if t in ['float_array', 'int_array']]
                self_array_axis = [item for item, t in zip(self.axis, self.types) if t in ['float_array', 'int_array']]
                if any(it.shape != st.shape for it, st in zip(item_array_axis, self_array_axis)):
                    return False
            for it_boe, s_boe, s_type in zip(item.boes, self.boes, self.types):
                if s_type == 'enum':  # in case of enum, check if all items are in self boe
                    if any(it not in s_it for it, s_it in zip(it_boe, s_boe)):
                        return False
                else:  # in other cases just to check both bounds
                    if not s_boe[0] <= it_boe[0] < it_boe[1] <= s_boe[1]:
                        return False
        return True

    def from_point(self, point, distance: Union[int, float, list, tuple], ignore_enums=True):
        """在已知空间中以一个点为中心点生成一个字空间

        Parameters
        ----------
        point: tuple or list of coordinates
            已知参数空间中的一个参数点
        distance: int or float，
            需要生成的新的子空间的数轴半径
        ignore_enums: bool, Default True
            忽略enum型轴，生成的子空间包含枚举型轴的全部元素，False生成的子空间包含enum轴的部分元素

        Returns
        -------
        Space，新的子空间

        Examples
        --------
        >>> p = (1, 2, 3)
        >>> s = Space([(0, 9), (0, 9), (0, 9)])
        >>> s.from_point(p, 1)
        <(0, 2),(1, 4),(2, 5)>

        """
        assert point in self, f'ValueError, point {point} is not in space!'
        assert self.dim > 0, 'original space should not be empty!'
        assert isinstance(distance, (int, float, list, tuple)), \
            f'TypeError, the distance must be a number or a list of numbers, got {type(distance)} instead'
        pars = []
        if isinstance(distance, (list, tuple)):
            assert len(distance) == self.dim, \
                f'ValueError, can not match {len(distance)} distances in {self.dim} dimensions!'
        else:
            distance = [distance] * self.dim
        for coordinate, boe, s_type, dis in zip(point, self.boes, self.types, distance):
            if s_type != 'enum':
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
        return Space(*pars, par_types=self.types)


class ResultPool:
    """结果池类，用于保存限定数量的中间结果，当压入的结果数量超过最大值时，去掉perf最差的结果.

    最初的算法是在每次新元素入池的时候都进行排序并去掉最差结果，这样要求每次都在结果池深度范围内进行排序
    第一步的改进是记录结果池中最差结果，新元素入池之前与最差结果比较，只有优于最差结果的才入池，避免了部分情况下的排序
    新算法在结果入池的循环内函数中避免了耗时的排序算法，将排序和修剪不合格数据的工作放到单独的cut函数中进行，这样只进行一次排序
    新算法将一百万次1000深度级别的排序简化为一次百万级别排序，实测能提速一半左右, 即使在结果池很小，总数据量很大的情况下，
    循环排序的速度也慢于单次排序修剪

    Properties
    ----------
    items: list, ReadOnly
        所有池中参数
    perfs: list, ReadOnly
        所有池中参数的评价分
    extra: list, ReadOnly
        所有池中参数的额外信息
    capacity: int
        池中最多可以放入的结果数量
    item_count: int
        池中当前的结果数量
    is_empty: bool
        池是否为空

    Methods
    -------
    in_pool(item, perf, extra=None) Deprecated Warning
        将一个元素压入池中
    push(item, perf, extra=None)
        将一个元素压入池中
    clear()
        清除所有元素
    cut(keep_largest=True)
        修剪池中的元素，使其数量不超过池的容量
    """

    # result pool operation:
    def __init__(self, capacity):
        """ 初始化结果池

        Parameters
        ----------
        capacity: int
            池中最多可以放入的结果数量
        """
        self.__capacity = 0  # 池中最多可以放入的结果数量
        self.__pool = []  # 用于存放被结果所评价的元素，如参数等
        self.__perfs = []  # 用于存放每个中间结果的评价分数，老算法仍然使用列表对象
        self.__extra = []  # 用于存放额外的信息，与每个元素一一相关，在裁剪时会跟随元素被裁剪掉

        self._set_capacity(capacity)

    @property
    def items(self):
        return self.__pool  # 只读属性，所有池中参数

    @property
    def perfs(self):
        return self.__perfs  # 只读属性，所有池中参数的评价分

    @property
    def extra(self):
        return self.__extra  # 只读属性，所有池中参数的额外信息

    @property
    def capacity(self):
        return self.__capacity

    @capacity.setter
    def capacity(self, value):
        self._set_capacity(value)

    @property
    def item_count(self):
        return len(self.items)

    @property
    def is_empty(self):
        return len(self.items) == 0

    def _set_capacity(self, value):
        """ 检查输入数据的合法性，设置结果池的容量"""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f'Capacity should be a positive integer, got {value} instead')
        self.__capacity = value

    def clear(self):
        """ 清空整个结果池

        :return:
        """
        self.__pool = []
        self.__perfs = []

    def in_pool(self, item, perf, extra=None):
        """将新的结果压入池中  # deprecated

        Parameters
        ----------
        item: object
            需要放入结果池的参数对象
        perf: float
            放入结果池的参数评价分数
        extra: object， optional
            需要放入结果池的参数对象的额外信息

        Returns
        -------
        None
        """
        warnings.warn(f'in_pool() is deprecated, use push() instead', DeprecationWarning)
        self.push(item, perf, extra)

    def push(self, item, perf, extra=None):
        """将新的结果压入池中

        Parameters
        ----------
        item: object
            需要放入结果池的参数对象
        perf: float
            放入结果池的参数评价分数
        extra: object， optional
            需要放入结果池的参数对象的额外信息

        Returns
        -------
        None
        """
        # perf必须是数值类型
        if not isinstance(perf, (int, float)):
            raise TypeError(f'Performance score must be a number, got {type(perf)} instead')
        self.__pool.append(item)  # 新元素入池
        self.__perfs.append(perf)  # 新元素评价分记录
        self.__extra.append(extra)

    def __add__(self, other):
        """ 将另一个pool中的内容合并到self中

        Parameters
        ----------
        other: ResultPool
            另一个结果池对象

        Returns
        -------
        self
        """
        self.__pool.extend(other.items)
        self.__perfs.extend(other.perfs)
        self.__extra.extend(other.extra)
        return self

    def cut(self, keep_largest=True):
        """将pool内的结果排序并剪切到capacity要求的大小

        直接对self对象进行操作，排序并删除不需要的结果

        Parameters
        ----------
        keep_largest: bool, Default True
            True保留评价分数最高的结果，False保留评价分数最低的结果

        Returns
        -------
        None
        """
        poo = self.__pool  # 所有池中元素
        per = self.__perfs  # 所有池中元素的评价分
        ext = self.__extra  # 池中元素的额外信息
        cap = self.__capacity
        if keep_largest:
            arr = np.array(per).argsort()[-cap:]
        else:
            arr = np.array(per).argsort()[:cap]
        poo2 = [poo[i] for i in arr]
        per2 = [per[i] for i in arr]
        ext2 = [ext[i] for i in arr]
        self.__pool = poo2
        self.__perfs = per2
        self.__extra = ext2


def space_around_centre(space, centre, radius, ignore_enums=True):
    """在给定的参数空间中指定一个参数点，并且创建一个以该点为中心且包含于给定参数空间的子空间

    如果参数空间中包含枚举类型维度，可以予以忽略或其他操作
    """
    return space.from_point(point=centre, distance=radius, ignore_enums=ignore_enums)
