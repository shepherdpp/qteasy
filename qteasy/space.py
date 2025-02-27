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

from qteasy.utilfuncs import (
    str_to_list,
    input_to_list,
)


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
    extract(interval_or_qty, how='interval'):
        从参数空间中提取参数点，返回一个参数点的迭代器

    Examples
    --------
    >>> space = Space([(1, 5), (3., 10.), (5, 6, 7, 8, 9)])
    <(1, 5),(3.0, 10.0),(5,...,9)>
    >>> space.dim
    3
    >>> space.axis
    [<Int Axis: (1, 5)>, <Float Axis: (3.0, 10.0)>, <Enum Axis: (5, 6, 7, 8, 9)>]
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

    def __init__(self, pars, par_types: [list, str] = None):
        """参数空间对象初始化，根据输入的参数生成一个空间

        Parameters
        ----------
        pars: int、float或list,
            需要建立参数空间的初始信息，通常为一个数值轴的上下界，如果给出了types，按照types中的类型字符串创建不
            同的轴，如果没有给出types，系统根据不同的输入类型动态生成的空间类型分别如下：
            pars为float，自动生成上下界为(0, items)的浮点型数值轴，
            pars为int，自动生成上下界为(0, items)的整形数值轴
            pars为list，根据list的元素种类和数量生成不同类型轴：
                list元素只有两个且元素类型为int或float：生成上下界为(items[0], items[1])的浮点型数值
                轴或整形数值轴
                list元素不是两个，或list元素类型不是int或float：生成枚举轴，轴的元素包含par中的元素
        par_types: list of str or str, optional
            生成的空间每个轴的类型，如果不给出types，会根据输入的pars自动判断，如果给出types，会根据types中
            的类型字符串创建不同的轴，types中的类型字符串分别如下：
            'int'/'discr':      生成整数型轴
            'float'/'conti':    生成浮点数值轴
            'enum':             生成枚举轴

        Returns
        -------
        None

        Examples
        --------
        >>> space = Space([(1, 5), (3., 10.), (5, 6, 7, 8, 9)])
        <(1, 5),(3.0, 10.0),(5,...,9)>
        >>> space = Space([(1, 5), (3., 10.), (5, 6, 7, 8, 9)], ['float', 'int', 'int'])
        <(1.0, 5.0),(3, 10),(5, 6)>
        """
        self._axis = []
        assert pars is not None, f'InputError, pars should be a list or tuple of items, got {pars}'
        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        pars = list(pars)
        par_dim = len(pars)
        if par_types is None:
            par_types = []
        elif isinstance(par_types, str):
            par_types = str_to_list(par_types, ',')
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
                raise KeyError(f'Invalid parameter type: {par_types[i]}')
        # 逐一生成Axis对象并放入axes列表中
        self._axis = [Axis(par, par_type) for par, par_type in zip(pars, par_types)]

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

    def extract(self, interval_or_qty: int = 1, how: str = 'interval'):
        """从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        Parameters
        ----------
        interval_or_qty: int
            从空间中每个轴上需要提取数据的步长或坐标数量
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
        >>> space = Space([(1, 10), (3, 10), (5, 6, 7, 8, 9)])
        >>> space
        <(1, 10),(3, 10),(5,...,9)>
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
        interval_or_qty_list = input_to_list(pars=interval_or_qty,
                                             dim=self.dim,
                                             padder=[1])
        axis_ranges = [ax.extract(ioq, how) for ax, ioq in zip(self.axis, interval_or_qty_list)]
        total = np.array(list(map(len, axis_ranges))).prod()
        if self.types == ['enum'] and isinstance(self.boes[0], tuple):
            # in this case, space is an enum of tuple parameters, no formation of tuple is needed
            return axis_ranges[0], len(axis_ranges[0])
        if how in ['interval', 'intv', 'step']:
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how in ['rand', 'random']:
            return itertools.zip_longest(*axis_ranges), interval_or_qty  # 使用迭代器工具将所有点组合打包为点集
        else:
            raise KeyError(f'Invalid extraction method: {how}\n'
                           f'Valid methods are: "interval" or "rand"')

    def __contains__(self, item: [list, tuple, object]):
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
        >>> s = Space(['x', 'y'], ['int', 'float'])
        >>> ('x', 'int') in s
        True

        """
        assert isinstance(item, (list, tuple, Space)), \
            f'TypeError, the item must be a point (tuple or list of coordinates) or a subspace, got {type(item)}'
        if isinstance(item, (tuple, list)):  # if item is a point
            if len(item) != self.dim:
                return False
            for coordinate, boe, s_type in zip(item, self.boes, self.types):
                if s_type == 'enum':
                    if coordinate not in boe:
                        return False
                else:
                    if not boe[0] <= coordinate <= boe[1]:
                        return False
        else:  # if item is a space, check if all boes are within self boes
            if item.dim != self.dim:
                return False
            if any(item_type != self_type for item_type, self_type in zip (item.types, self.types)):
                return False
            for it_boe, s_boe, s_type in zip(item.boes, self.boes, self.types):
                if s_type == 'enum':  # in case of enum, check if all items are in self boe
                    if any(it not in s_it for it, s_it in zip(it_boe, s_boe)):
                        return False
                else:  # in other cases just to check both bounds
                    if not s_boe[0] <= it_boe[0] < it_boe[1] <= s_boe[1]:
                        return False
        return True

    def from_point(self, point, distance: [int, float, list], ignore_enums=True):
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
        >>> s = Space([(0, 5), (1, 3), (1, 5)])
        >>> s.from_point(p, 1)
        <(0, 5),(1, 3),(1, 5)>

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
        return Space(pars, self.types)


class Axis:
    """数轴对象，空间对象的一个组成部分，代表空间对象的一个维度

    Axis对象包含Space对象的一个维度，与Space对象相似，Axis对象也有三种类型：
    1，discr (int) Axis，离散型数轴，包含一系列连续的整数，由这些整数值的上下界来定义。例如Axis([0, 10])代表一个Axis，这个Axis上的
        取值范围为0～10，包括0与10
    2，conti (float) Axis，连续数轴对象，包含从下界到上界之间的所有浮点数，同样使用上下界定义，如Axis([0., 2.0])
    3，enum Axis，枚举值数轴，取值范围为一系列任意类型对象，这些对象需要在创建Axis的时候就定义好。
        例如：Axis(['a', 1, 'abc', (1, 2, 3)])就是一个枚举轴，它的取值可以是以下列表中的任意一个
                        ['a', 1, 'abc', (1, 2, 3)]
    Axis对象最重要的方法是extract()方法，代表从数轴的所有可能值中取出一部分并返回给Space对象生成迭代器。
    对于Axis对象来说，有两种基本的extract()方法：
    1，interval方法：间隔取值方法，即按照一定的间隔从数轴中取出一定数量的值。这种方法的参数主要是step_size，对于conti类型的数轴
        step_size可以为一个浮点数，对于其他类型的数轴，step_size只能为整数。取值的举例如下：
        a: 从一个conti数值轴中，以step_size=0.5取值：
            Axis([0, 3]).extract(step_size=0.5) -> [0, 0.5, 1, 1.5, 2. 2.5, 3]
        b: 从一个discr数值轴中，以step_size=2取值:
            Axis([1, 5]).extract(step_size-2) -> [1, 3, 5]
        c: 从一个enum轴中，以step_size=2取值:
            Axis([1, 2, 3, 'a', 'b', 'c', (1, 2)]).extract(step_size=2) -> [1, 3, 'b', (1, 2)]
    2，random方法: 从数轴的所有可选值中随机选出指定数量的值返回到Space对象，对于任何类型的Axis，其取值方法都是类似的，指定的取值数量
    必须是整数：举例如下：
        a: 从一个enum轴中随机取出四个值：
            Axis(['a', 'b', 'c']).extract(count=4) -> ['b', 'a', 'c', 'a']

    Properties
    ----------
    count: int
        输出数轴中元素的个数，若数轴为连续型，输出为inf
    size: int
        数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界
    axis_type: str
        该数轴的类型，可选值为'conti', 'discr', 'enum'

    Methods
    -------
    extract(method, **kwargs)
        从数轴上取出一定数量的值，返回一个Generator对象，该Generator对象可以用于生成Space对象的迭代器
    """
    CONTI = 10
    DISCR = 20
    ENUM = 30
    AVAILABLE_EXTRACT_METHODS = ['int', 'interval', 'random', 'rand']

    def __init__(self, bounds_or_enum, typ=None):
        """ 初始化数轴对象

        Parameters
        ----------
        bounds_or_enum: list or tuple
            数轴的上下界或枚举值，当数轴类型为conti或discr时，bounds_or_enum为一个长度为2的列表或元组，分别代表数轴的上下界；
            当数轴类型为enum时，bounds_or_enum为一个列表或元组，其中的元素为该数轴上所有可用的值
        typ: str, {'conti', 'float', 'discr', 'int', 'enum'}, optional
            数轴的类型，当typ为空时，根据bounds_or_enum的类型自动判断数轴类型

        Raises
        ------
        ValueError
            当输入的数轴类型不在可选值中时，抛出ValueError异常

        """
        import numbers
        self._axis_type = None  # 数轴类型
        self._lbound = None  # 离散型或连续型数轴下界
        self._ubound = None  # 离散型或连续型数轴上界
        self._enum_val = None  # 当数轴类型为“枚举”型时，储存改数轴上所有可用值
        # 将输入的上下界或枚举转化为列表，当输入类型为一个元素时，生成一个空列表并添加该元素
        boe = list(bounds_or_enum)
        length = len(boe)  # 列表元素个数
        if typ is None:
            # 当typ为空时，需要根据输入数据的类型猜测typ
            if length <= 2:
                # list长度小于等于2，根据数据类型取上下界:
                #    1， 当任意一个元素不是数字时，类型为枚举，否则->2
                #    2， 当任意一个元素是浮点型时，类型为连续型，否则->
                #    3， 所有元素都是整形，类型为离散型
                if any(not isinstance(item, numbers.Number) for item in boe):
                    typ = 'enum'
                elif any(isinstance(item, float) for item in boe):
                    typ = 'float'
                else:  # 输入数据类型不是数字时，处理为枚举类型
                    typ = 'int'
            else:  # list长度为其余值时，全部处理为enum数据
                typ = 'enum'
        elif typ != 'enum' and typ != 'int' and typ != 'float':
            typ = 'enum'  # 当发现typ为异常字符串时，修改typ为enum类型
        # 开始根据typ的值生成具体的Axis
        if typ == 'enum':  # 创建一个枚举数轴
            self._new_enumerate_axis(boe)
        elif typ == 'int':  # 创建一个离散型数轴
            if length == 1:
                self._new_discrete_axis(0, boe[0])
            else:
                self._new_discrete_axis(boe[0], boe[1])
        else:  # 创建一个连续型数轴
            if length == 1:
                self._new_continuous_axis(0, boe[0])
            else:
                self._new_continuous_axis(boe[0], boe[1])

    def __repr__(self):
        """输出数轴的字符串表示"""
        if self.axis_type == 'enum':
            return 'Enum Axis({})'.format(self.axis_boe)
        elif self.axis_type == 'float':
            return 'Float Axis({}, {})'.format(self._lbound, self._ubound)
        else:
            return 'Int Axis({}, {})'.format(self._lbound, self._ubound)

    @property
    def count(self):
        """输出数轴中元素的个数，若数轴为连续型，输出为inf"""
        self_type = self._axis_type
        if self_type == 'float':
            return np.inf
        elif self_type == 'int':
            return self._ubound - self._lbound + 1
        else:
            return len(self._enum_val)

    @property
    def size(self):
        """输出数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界"""
        if self.axis_type == 'float':
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

        Parameters
        ----------
        interval_or_qty: int
            需要从数轴中抽取的数据总数或抽取间隔，当how=='interval'时，代表抽取间隔，否则代表总数
        how: str, {'interval', 'int', 'rand', 'random'}, Default 'interval'
            抽取方法，
            'interval'/'int': 从数轴中抽取interval_or_qty个数据，每两个数据之间的间隔固定
            'rand'/'random': 从数轴中抽取interval_or_qty个数据，每两个数据之间的间隔随机

        Returns
        -------
        iterator: 一个迭代器对象，包含所有抽取的数值
        """
        if not isinstance(how, str):
            raise TypeError(f'extract method \'how\' should be a string in {self.AVAILABLE_EXTRACT_METHODS}')
        if how.lower() in ['interval', 'int']:
            if self.axis_type == 'enum':
                return self._extract_enum_interval(interval_or_qty)
            else:
                return self._extract_bounding_interval(interval_or_qty)
        if how.lower() in ['rand', 'random']:
            if self.axis_type == 'enum':
                return self._extract_enum_random(interval_or_qty)
            else:
                return self._extract_bounding_random(interval_or_qty)
        raise KeyError(f'extract method {how} is not valid, make sure method is one of '
                       f'{self.AVAILABLE_EXTRACT_METHODS}')

    def _set_bounds(self, lbound, ubound):
        """设置数轴的上下界, 只适用于离散型或连续型数轴

        Parameters
        ----------
        lbound: int or float
            数轴下界
        ubound: int or float
            数轴上界

        Returns
        -------
        None
        """
        self._lbound = lbound
        self._ubound = ubound
        self.__enum = None

    def _set_enum_val(self, enum):
        """设置数轴的枚举值，适用于枚举型数轴

        此处需要区分tuple_enum类型和普通enum类型的数轴，tuple_enum类型的数轴需要保留tuple类型，
        因此不能使用np.array转换类型。普通enum类型可以使用np.array转换类型。转换类型的原因是为了便于使用np的random直接读出多个值，
        而对于tuple_enum类型来说，使用np.array会强制将tuple类型转换为array，会在后续操作中导致问题。

        Parameters
        ----------
        enum: 数轴枚举值

        Returns
        -------
        None
        """
        self._lbound = None
        self._ubound = None
        self._enum_val = enum

    def _new_discrete_axis(self, lbound, ubound):
        """ 创建一个新的离散型数轴

        Parameters
        ----------
        lbound: int or float
            数轴下界
        ubound: int or float
            数轴上界

        Returns
        -------
        None
        """
        self._axis_type = 'int'
        self._set_bounds(int(lbound), int(ubound))

    def _new_continuous_axis(self, lbound, ubound):
        """ 创建一个新的连续型数轴

        Parameters
        ----------
        lbound: int or float
            数轴下界
        ubound: int or float
            数轴上界

        Returns
        -------
        None
        """
        self._axis_type = 'float'
        self._set_bounds(float(lbound), float(ubound))

    def _new_enumerate_axis(self, enum):
        """ 创建一个新的枚举型数轴

        Parameters
        ----------
        enum: 数轴枚举值

        Returns
        -------
        None
        """
        self._axis_type = 'enum'
        self._set_enum_val(enum)

    def _extract_bounding_interval(self, interval: [int, float]):
        """ 按照间隔方式从离散或连续型数轴中提取值

        Parameters
        ----------
        interval: int or float
            提取间隔

        Returns
        -------
        np.array 从数轴中提取出的值对象
        """
        if self._axis_type == 'float':
            return np.arange(self._lbound, self._ubound, interval)
        if self._axis_type == 'int':
            if not float(interval).is_integer():
                raise ValueError(f'interval should be an integer, got {interval} instead!')
            if not float(self._lbound).is_integer():
                raise ValueError(f'l-bound of discrete axis should be an integer, got {self._lbound} instead')
            return np.arange(self._lbound, self._ubound + 1, interval)

    def _extract_bounding_random(self, qty: int):
        """ 按照随机方式从离散或连续型数轴中提取值

        Parameters
        ----------
        qty: int
            提取的数据总量

        Returns
        -------
        np.array 从数轴中提取出的值对象
        """
        if not float(qty).is_integer():
            raise ValueError(f'interval should be an integer, got {qty} instead!')
        if self._axis_type == 'int':
            return np.random.randint(self._lbound, self._ubound + 1, size=qty)
        if self._axis_type == 'float':
            return np.random.uniform(self._lbound, self._ubound, qty)

    def _extract_enum_interval(self, interval):
        """ 按照间隔方式从枚举型数轴中提取值

        Parameters
        ----------
        interval: int or float
            提取间隔

        Returns
        -------
        list 从数轴中提取出的值对象
        """
        if not float(interval).is_integer():
            raise ValueError(f'interval should be an integer, got {interval} instead!')
        selected = np.arange(0, self.count, interval)
        return [self._enum_val[i] for i in selected]

    def _extract_enum_random(self, qty: int):
        """ 按照随机方式从枚举型数轴中提取值

        Parameters
        ----------
        qty: int
            提取的数据总量

        Returns
        -------
        list 从数轴中提取出的值对象
        """
        if not float(qty).is_integer():
            raise ValueError(f'interval should be an integer, got {qty} instead!')
        selected = np.random.choice(self.count, size=qty)
        return [self._enum_val[i] for i in selected]


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
        self.__capacity = capacity  # 池中最多可以放入的结果数量
        self.__pool = []  # 用于存放被结果所评价的元素，如参数等
        self.__perfs = []  # 用于存放每个中间结果的评价分数，老算法仍然使用列表对象
        self.__extra = []  # 用于存放额外的信息，与每个元素一一相关，在裁剪时会跟随元素被裁剪掉

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

    @property
    def item_count(self):
        return len(self.items)

    @property
    def is_empty(self):
        return len(self.items) == 0

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
