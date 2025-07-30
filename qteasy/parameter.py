# coding=utf-8
# ======================================
# File:     parameter.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-07-10
# Desc:
#   Definition of adjustable parameter
# of strategies, these parameters
# influence the performance of
# strategies.
# ======================================

import numpy as np


class Parameter:
    """参数对象，参数空间的组成部分，代表参数空间的一个维度或一个方面

    Parameter对象包含Space对象的一个维度，Parameter对象有四种类型：
    1，discr (int) Parameter，离散型数轴，包含一系列连续的整数，由这些整数值的上下界来定义。例如Parameter([0, 10])代表一个Parameter，这个Parameter上的
        取值范围为0～10，包括0与10
    2，conti (float) Parameter，连续数轴对象，包含从下界到上界之间的所有浮点数，同样使用上下界定义，如Parameter([0., 2.0])
    3，enum Parameter，枚举值数轴，取值范围为一系列任意类型对象，这些对象需要在创建Parameter的时候就定义好。
        例如：Parameter(['a', 1, 'abc', (1, 2, 3)])就是一个枚举轴，它的取值可以是以下列表中的任意一个
                        ['a', 1, 'abc', (1, 2, 3)]
    4，array Parameter，数组数轴，取值范围为一个数组对象，这个数组对象可以是int/float类型的numpy array对象。
    Parameter对象最重要的方法是gen_value()方法，代表从数轴的所有可能值中取出一部分并返回给Space对象生成迭代器。
    对于Parameter对象来说，有两种基本的gen_value()方法：
        1，interval方法：间隔取值方法，即按照一定的间隔从数轴中取出一定数量的值。这种方法的参数主要是step_size，对于conti类型的数轴
            step_size可以为一个浮点数，对于其他类型的数轴，step_size只能为整数。取值的举例如下：
            a: 从一个conti数值轴中，以step_size=0.5取值：
                Parameter([0, 3]).gen_value(step_size=0.5) -> [0, 0.5, 1, 1.5, 2. 2.5, 3]
            b: 从一个discr数值轴中，以step_size=2取值:
                Parameter([1, 5]).gen_value(step_size-2) -> [1, 3, 5]
            c: 从一个enum轴中，以step_size=2取值:
                Parameter([1, 2, 3, 'a', 'b', 'c', (1, 2)]).gen_value(step_size=2) -> [1, 3, 'b', (1, 2)]
        2，random方法: 从数轴的所有可选值中随机选出指定数量的值返回到Space对象，对于任何类型的Parameter，其取值方法都是类似的，指定的取值数量
        必须是整数：举例如下：
            a: 从一个enum轴中随机取出四个值：
                Parameter(['a', 'b', 'c']).gen_value(count=4) -> ['b', 'a', 'c', 'a']
    另外Parameter对象还有常规的set_value方法等

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
    gen_value(method, **kwargs)
        从数轴上取出一定数量的值，返回一个Generator对象，该Generator对象可以用于生成Space对象的迭代器
    """
    CONTI = 10
    DISCR = 20
    ENUM = 30
    ARRAY = 40  # 数轴类型常量
    AVAILABLE_EXTRACT_METHODS = ['int', 'interval', 'random', 'rand']

    def __init__(self, name: str, bounds_or_enum, typ=None, value=None):
        """ 初始化参数对象

        Parameters
        ----------
        name: str
            参数名称
        bounds_or_enum: list or tuple
            数轴的上下界或枚举值，当数轴类型为conti或discr时，bounds_or_enum为一个长度为2的列表或元组，分别代表数轴的上下界；
            当数轴类型为enum时，bounds_or_enum为一个列表或元组，其中的元素为该数轴上所有可用的值
        typ: str, {'conti', 'float', 'discr', 'int', 'enum'}, optional
            数轴的类型，当typ为空时，根据bounds_or_enum的类型自动判断数轴类型
        value: any, optional
            参数的初始值，默认为None。对于枚举型数轴，value可以是bounds_or_enum中的任意一个元素；对于离散型或连续型数轴，
            value可以是一个整数或浮点数，代表该数轴上的一个具体值

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
        # 开始根据typ的值生成具体的Parameter
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
        """输出参数的字符串表示"""
        if self.axis_type == 'enum':
            return 'Enum Parameter({})'.format(self.axis_boe)
        elif self.axis_type == 'float':
            return 'Float Parameter({}, {})'.format(self._lbound, self._ubound)
        else:
            return 'Int Parameter({}, {})'.format(self._lbound, self._ubound)

    @property
    def count(self):
        """输出参数中可用元素的个数，若参数为连续型，输出为inf"""
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

    def gen_value(self, interval_or_qty=1, how='interval'):
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
        raise KeyError(f'gen_value method {how} is not valid, make sure method is one of '
                       f'{self.AVAILABLE_EXTRACT_METHODS}')

    def set_value(self, value):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError

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
