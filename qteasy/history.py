# coding=utf-8
# ======================================
# File:     history.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-16
# Desc:
#   HistoryPanel Class, and more history
# data manipulating functions.
# ======================================

import pandas as pd
import numpy as np

from qteasy.utilfuncs import (
    str_to_list,
    list_to_str_format,
    list_or_slice,
    labels_to_dict,
    ffill_3d_data,
    fill_nan_data,
    fill_inf_data,
    pandas_freq_alias_version_conversion,
)

from qteasy.datatypes import (
    get_history_data_from_source,
    get_reference_data_from_source,
)


class HistoryPanel():
    """qteasy 量化投资系统使用的主要历史数据的数据类型

    一个HistoryPanel对象其本质是一个numpy.ndarray，这个ndarray是一个
    三维数组，这个三维数组有L层，R行、C列，分别代表L种历史数据、R条数据记录、C种股票的历史数据。历史数据类型可以包括
    类似开盘价、收盘价这样的量价数据，同样也可以包括诸如pe、ebitda等等财务数据

    HistoryPanel数据结构的核心部分是一个基于numpy的三维ndarray矩阵，这个矩阵由M层N行L列，三个维度的轴标签分别为：
        axis 0: levels/层，每层的标签为一个个股，每一层在HistoryPanel中被称为一个level，所有level的标签被称为shares
        axis 1: rows/行，每行的标签为一个时间点，每一行在HistoryPanel中被称为一个row，所有row的标签被称为hdates
        axis 2: columns/列，每列的标签为一种历史数据，每一列在HistoryPanel中被称为一个column，所有column的标签被称为htypes

    使用HistoryPanel类，用户可以：
    1, 方便地对数据进行切片，切片的基本方法是使用__getitem__()方法，也就是使用方括号[]传入切片器或列表对象，切片的输出是一个
       numpy ndarray。
        为了对正确的数轴进行切片，通过方括号传入的切片器或列表对象必须按照[htype slicer, shares slicer, dates slicer]的顺序
        传入，第一个切片器对数据类型进行切片，第二个对股票品种，第三个对日期切片。切片的方法非常灵活：
        * 可以通过直接输入数轴的标签来选择某个单独的数据类型/股票品种，如：
            HistoryPanel['close']: 选择所有股票品种的全部历史收盘价
            HistoryPanel[,'000300.SH']: 选择000300股票品种的所有历史数据
        * 可以以逗号分隔的数轴标签字符串形式指定某几个股票品种或数据类型，如：
            HistoryPanel['close, open, high']: 选择所有股票品种的全部历史收盘、开盘及最高价
        * 可以通过冒号:分隔的数轴标签字符串选择从第一个标签到最后一个标签之间的所有品种或数据类型，如：
            HistoryPanel['000300.SH:000500.SH']: 选择从000300开始到000500之间的所有股票品种全部历史数据
        * 可以通过int列表或str列表指定某几个品种或类型的数据，如：
            HistoryPanel[[0, 1, 2, 4]] 或 HistoryPanel[['close', 'open', 'high', 'low']]
            选择第0、1、2、4种数据类型或'close', 'open', 'high', 'low'等标签代表的数据类型
        * 也可以通过常见的slicer对象来选择， 如：
            HistoryPanel[0:5:2] 选择0、2、4等三种数据类型的全部数据
        * 上面的所有切片方式可以单独使用，也可以混合使用，甚至几个list混合使用也不会造成问题，如：
            要选择000300， 000500， 000700等三只股票的close到high之间所有类型的2010年全年的历史数据，可以用下列方式实现：
            HistoryPanel['close:high', ['000300', '000500', '000700'], '20100101:20101231']
    2, 动态地修改每一个数轴上的标签内容，容易地调取标签和元素位置的对应关系（一个字典）
        HistoryPanel.shares     输出一个列表，包含按顺序排列的所有层标签，即所有股票品种代码或名称
        HistoryPanel.hdates     输出一个列表，包含按顺序排列的所有行标签，即所有数据的日期及时间
        HistoryPanel.htypes     输出一个列表，包含按顺序排列的所有列标签，即所数据类型
        HistoryPanel.levels     输出一个字典，包含所有层标签及其对应的层编号（从0开始到M-1）
        HistoryPanel.columns    输出一个字典，包含所有数据类型标签及其对应的列编号（从0开始到L-1）
        HistoryPanel.rows       输出一个字典，包含所有日期行标签及其对应的行号，从0开始一直到N-1）
    3, 方便地打印HistoryPanel的相关信息
    4, 方便地打印及格式化输出HistoryPanel的内容
    5, 方便地转化为 pandas DataFrame对象
        HistoryPanel不能完整转化为DataFrame对象，因为DataFrame只能适应2D数据。在转化为DataFrame的时候，用户只能选择
        HistoryPanel的一个切片，或者是一个股票品种，或者是一个数据类型，输出的DataFrame包含的数据行数与
    6, 方便地由多个pandas DataFrame对象组合而成

    Properties
    ----------
    is_empty: bool, 该属性返回一个bool值，表示HistoryPanel是否为空
    values: np.ndarray, 该属性返回一个numpy ndarray，包含HistoryPanel的全部数据
    levels: dict, 该属性返回一个dict， 包含所有层标签(股票代码)及其对应的层编号
    rows: dict, 该属性返回一个dict， 包含所有行标签(交易日期)及其对应的行编号
    columns: dict, 该属性返回一个dict， 包含所有列标签(数据类型)及其对应的列编号
    shares: list, 该属性包含所有层标签，即所有股票代码
    hdates: list, 该属性包含所有行标签，即所有日期时间
    htypes: list, 该属性包含所有列标签，即所有历史数据类型

    Methods
    -------
    __getitem__(self, slicer)
        该方法用于对HistoryPanel进行切片，返回一个numpy ndarray
    re_label(self, levels=None, rows=None, columns=None)
        该方法用于重新设置HistoryPanel的标签，如果不输入任何参数，则会自动重新生成标签
    join(self, other, how='outer', axis=0)
        该方法用于将两个HistoryPanel对象合并为一个HistoryPanel对象
    slice_to_dataframe(self, slicer)
        该方法用于将HistoryPanel的一个切片转化为pandas DataFrame对象
    flatten_to_dataframe(self, level=None, htype=None)
        该方法用于将HistoryPanel转化为一个multi-index DataFrame对象

    """

    def __init__(self, values: np.ndarray = None, levels=None, rows=None, columns=None):
        """ 初始化HistoryPanel对象，必须传入values作为HistoryPanel的数据

        在生成一个HistoryPanel的时候，可以同时输入层标签（股票代码）、行标签（日期时间）和列标签（历史数据类型）
        如果不输入这些数据，HistoryPanel会自动生成标签。在某些qteasy应用中，要求输入正确的标签，如果标签不正确
        可能导致报错。

        Parameters
        ----------
        values: ndarray
            一个ndarray，该数组的维度不能超过三维，如果给出的数组维度不够三维，将根据给出的标签推断并补齐维度
            如果不给出values，则会返回一个空HistoryPanel，其empty属性为True
        levels: str or [str] or (str)
            HistoryPanel的股票标签，层的数量为values第一个维度的数据量，每一层代表一种股票或资产
        rows: str or [str] or (str)
            HistoryPanel的时间日期标签。
            datetime range或者timestamp index或者str类型，通常是时间类型或可以转化为时间类型，
            行标签代表每一条数据对应的历史时间戳
        columns: str or [str] or (str)
            HistoryPanel的列标签，代表历史数据的类型，既可以是历史数据的
        """

        # TODO: 在生成HistoryPanel时如果只给出data或者只给出data+columns，生成HistoryPanel打印时会报错，问题出在to_dataFrame()上
        #  在生成HistoryPanel时传入的ndarray会被直接用于HistoryPanel，如果事后修改这个ndarray，HistoryPanel也会改变
        #  应该考虑是否在创建HistoryPanel时生成ndarray的一个copy而不是使用其自身 。
        if (not isinstance(values, np.ndarray)) and (values is not None):
            raise TypeError(f'input value type should be numpy ndarray, got {type(values)}')

        self._levels = None
        self._columns = None
        self._rows = None
        if values is None or values.size == 0:
            self._l_count, self._r_count, self._c_count = (0, 0, 0)
            self._values = None
            self._is_empty = True
        else:
            assert values.ndim <= 3, \
                f'input array should be equal to or less than 3 dimensions, got {len(values.shape)}'

            if isinstance(levels, str):
                levels = str_to_list(levels)
            if isinstance(columns, str):
                columns = str_to_list(columns)
            if isinstance(rows, str):
                rows = str_to_list(rows)
            # 处理输入数据，补齐缺失的维度，根据输入数据的维度以及各维度的标签数据数量确定缺失的维度
            if values.ndim == 1:
                values = values.reshape(1, values.shape[0], 1)
            elif values.ndim == 2:
                if (levels is None) or (len(levels) == 1):
                    values = values.reshape(1, *values.shape)
                else:
                    values = values.reshape(*values.T.shape, 1)
            self._l_count, self._r_count, self._c_count = values.shape
            self._values = values
            self._is_empty = False

            # 检查输入数据的标签，处理标签数据以确认标签代表的数据各维度的数据量
            if levels is None:
                levels = range(self._l_count)
            if rows is None:
                rows = pd.date_range(periods=self._r_count, end='2020-08-08', freq='d')
            if columns is None:
                columns = range(self._c_count)

            assert (len(levels), len(rows), len(columns)) == values.shape, \
                f'ValueError, value shape does not match, input data: ({(values.shape)}) while given axis' \
                f' imply ({(len(levels), len(rows), len(columns))})'

            # 建立三个纬度的标签配对——建立标签序号字典，通过labels_to_dict()函数将标签和该纬度数据序号一一匹配
            # 首先建立层标签序号字典：
            self._levels = labels_to_dict(levels, range(self._l_count))

            # 再建立行标签序号字典，即日期序号字典，再生成字典之前，检查输入标签数据的类型，并将数据转化为pd.Timestamp格式
            assert isinstance(rows, (list, dict, pd.DatetimeIndex)), \
                f'TypeError, input_hdates should be a list or DatetimeIndex, got {type(rows)} instead'
            try:
                new_rows = [pd.to_datetime(date) for date in rows]
            except:
                raise ValueError('one or more item in hdate list can not be converted to Timestamp')
            self._rows = labels_to_dict(new_rows, range(self._r_count))

            # 建立列标签序号字典
            self._columns = labels_to_dict(columns, range(self._c_count))

    @property
    def is_empty(self):
        """判断HistoryPanel是否为空"""
        return self._is_empty

    @property
    def values(self):
        """返回HistoryPanel的values"""
        return self._values

    @property
    def levels(self):
        """返回HistoryPanel的层标签字典，也是HistoryPanel的股票代码字典

        HistoryPanel的层标签是保存成一个字典形式的：
        levels =    {share_name[0]: 0,
                     share_name[1]: 1,
                     share_name[2]: 2,
                     ...
                     share_name[l]: l}
        这个字典在level的标签与level的id之间建立了一个联系，因此，如果需要通过层标签来快速地访问某一层的数据，可以非常容易地通过：
            data = HP.values[levels[level_name[a], :, :]
        来访问

        不过这是HistoryPanel内部的处理机制，在HistoryPanel的外部，可以通过切片的方式快速访问不同的数据。
        """
        return self._levels

    @property
    def shares(self):
        """返回HistoryPanel的层标签——股票列表"""
        if self.is_empty:
            return 0
        else:
            return list(self._levels.keys())

    @shares.setter
    def shares(self, input_shares):
        if not self.is_empty:
            if isinstance(input_shares, str):
                input_shares = str_to_list(input_string=input_shares)
            assert len(input_shares) == self.level_count, \
                f'ValueError, the number of input shares ({len(input_shares)}) does not match level ' \
                f'count ({self.level_count})'
            self._levels = labels_to_dict(input_shares, self.shares)

    @property
    def level_count(self):
        """返回HistoryPanel中股票或资产品种的数量"""
        return self._l_count

    @property
    def share_count(self):
        """获取HistoryPanel中股票或资产品种的数量"""
        return self._l_count

    @property
    def rows(self):
        """ 返回Hi storyPanel的日期字典，通过这个字典建立日期与行号的联系：

        rows =  {row_date[0]: 0,
                 row_date[1]: 1,
                 row_date[2]: 2,
                 ...
                 row_date[r]: r
                 }
        因此内部可以较快地进行数据切片或数据访问

        Returns
        -------
        dict
            日期字典
        """
        return self._rows

    @property
    def hdates(self):
        """获取HistoryPanel的历史日期时间戳list"""
        # TODO: Maybe: 可以将返回值包装成一个pandas.Index对象，
        #  这样有更多方便好用的方法和属性可用
        #  例如
        #  return pd.Index(self._rows.keys())
        #  这样就可以用 HP.hdates.date / HP.hdates.where()
        #  等等方法和属性了
        #  shares 和 htypes 属性也可以如法炮制
        if self.is_empty:
            return 0
        else:
            # return pd.Index(self._rows.keys(), dtype='datetime64')
            return list(self._rows.keys())

    @hdates.setter
    def hdates(self, input_hdates: list):
        if not self.is_empty:
            if not isinstance(input_hdates, list):
                error = f'input_hdates should be a list, got {type(input_hdates)} instead'
                raise TypeError(error)
            if not len(input_hdates) == self.row_count:
                error = f'the number of input shares ({len(input_hdates)}) does not match level count ({self.row_count})'
                raise ValueError(error)
            try:
                new_hdates = [pd.to_datetime(date) for date in input_hdates]
            except Exception as e:
                error = f'{e} one or more item in hdate list can not be converted to Timestamp'
                raise ValueError(error)
            self._rows = labels_to_dict(new_hdates, self.hdates)

    @property
    def row_count(self):
        """获取HistoryPanel的行数量"""
        return self._r_count

    @property
    def hdate_count(self):
        """获取HistoryPanel的历史数据类型数量"""
        return self._r_count

    @property
    def htypes(self):
        """获取HistoryPanel的历史数据类型列表"""
        if self.is_empty:
            return 0
        else:
            return list(self._columns.keys())

    @htypes.setter
    def htypes(self, input_htypes: [str, list]):
        """修改HistoryPanel的历史数据类型"""
        if not self.is_empty:
            if isinstance(input_htypes, str):
                input_htypes = str_to_list(input_string=input_htypes)
            if isinstance(input_htypes, list):
                assert len(input_htypes) == self.column_count, \
                    f'ValueError, the number of input shares ({len(input_htypes)}) does not match level ' \
                    f'count ({self.column_count})'
                self._columns = labels_to_dict(input_htypes, self.htypes)
            else:
                raise TypeError(f'Expect string or list as input htypes, got {type(input_htypes)} instead')

    @property
    def columns(self):
        """返回一个字典，代表HistoryPanel的历史数据，将历史数据与列号进行对应
        columns = {htype_name[0]: 0,
                   htype_naem[1]: 1,
                   htype_name[2]: 2,
                   ...
                   htype_name[c]: c}

        这样便于内部根据股票代码对数据进行切片
        """
        return self._columns

    @property
    def column_count(self):
        """获取HistoryPanel的列数量或历史数据数量"""
        return self._c_count

    @property
    def htype_count(self):
        """获取HistoryPanel的历史数据类型数量"""
        return self._c_count

    @property
    def shape(self):
        """获取HistoryPanel的各个维度的尺寸"""
        return self._l_count, self._r_count, self._c_count

    def __len__(self):
        """获取HistoryPanel的历史数据长度

        Examples
        --------

        """
        return self._r_count

    def __getitem__(self, keys=None):
        """获取历史数据的一个切片，给定一个type、日期或股票代码, 输出相应的数据

        允许的输入包括切片形式的各种输入，包括string、数字列表或切片器对象slice()，返回切片后的ndarray对象
        允许的输入示例，第一个切片代表type切片，第二个是shares，第三个是rows：
        item_key                    output
        [1:3, :,:]                  输出第1个htype～第3个htype的所有历史数据
        [[0,1,2],:,:]:              输出第0、1、2个htype对应的所有股票全部历史数据
        [['close', 'high']]         输出close、high两个类型的所有历史数据
        [0:1]                       输出0、1两个htype的所有历史数据
        ['close,high']              输出close、high两个类型的所有历史数据
        ['close:high']              输出close、high之间所有类型的历史数据（包含close和high）
        [:,[0,1,3]]                 输出0、1、3三个股票的全部历史数据
        [:,['000100', '000120']]    输出000100、000120两只股票的所有历史数据
        [:,0:2]                     输出0、1、2三个股票的历史数据
        [:,'000100,000120']         输出000100、000120两只股票的所有历史数据

        Parameters
        ----------
        keys: list/tuple/slice
            历史数据的类型名，为空时给出所有类型的数据

        Returns
        -------
        out : ndarray
            self.value的一个切片

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                   levels=['000001', '000002', '000003'],
        ...                   rows=pd.date_range('2015-01-05', periods=10),
        ...                   columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp
                share 0, label: 000001
                    open  high  low  close  volume
        2015-01-05    10    20   30     40      50
        2015-01-06    10    20   30     40      50
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        2015-01-11    10    20   30     40      50
        2015-01-12    10    20   30     40      50
        2015-01-13    10    20   30     40      50
        2015-01-14    10    20   30     40      50

        share 1, label: 000002
                    open  high  low  close  volume
        2015-01-05    10    20   30     40      50
        2015-01-06    10    20   30     40      50
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        2015-01-11    10    20   30     40      50
        2015-01-12    10    20   30     40      50
        2015-01-13    10    20   30     40      50
        2015-01-14    10    20   30     40      50

        share 2, label: 000003
                    open  high  low  close  volume
        2015-01-05    10    20   30     40      50
        2015-01-06    10    20   30     40      50
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        2015-01-11    10    20   30     40      50
        2015-01-12    10    20   30     40      50
        2015-01-13    10    20   30     40      50
        2015-01-14    10    20   30     40      50
        >>> hp['close']
        array([[[40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40]],

               [[40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40]],

               [[40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40],
                [40]]])
        >>> hp['close, open, low', '000001:000002']
        array([[[40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30]],

               [[40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30],
                [40, 10, 30]]])
        """
        if self.is_empty:
            return None
        else:
            key_is_none = keys is None
            key_is_tuple = isinstance(keys, tuple)
            key_is_list = isinstance(keys, list)
            key_is_slice = isinstance(keys, slice)
            key_is_string = isinstance(keys, str)
            key_is_number = isinstance(keys, int)

            # first make sure that htypes, share_pool, and hdates are either slice or list
            htype_slice = []
            share_slice = []
            hdate_slice = []
            if key_is_tuple:
                if len(keys) == 2:
                    htype_slice, share_slice = keys
                    hdate_slice = slice(None, None, None)
                elif len(keys) == 3:
                    htype_slice, share_slice, hdate_slice = keys
            elif key_is_slice or key_is_list or key_is_string or key_is_number:  # keys is a slice or list
                htype_slice = keys
                share_slice = slice(None, None, None)
                hdate_slice = slice(None, None, None)
            elif key_is_none:
                htype_slice = slice(None, None, None)
                share_slice = slice(None, None, None)
                hdate_slice = slice(None, None, None)
            else:
                htype_slice = slice(None, None, None)
                share_slice = slice(None, None, None)
                hdate_slice = slice(None, None, None)

            # check and convert each of the slice segments to the right type: a slice or \
            # a list of indices
            htype_slice = list_or_slice(htype_slice, self.columns)
            share_slice = list_or_slice(share_slice, self.levels)
            hdate_slice = list_or_slice(hdate_slice, self.rows)

            return self.values[share_slice][:, hdate_slice][:, :, htype_slice]

    def __str__(self):
        """打印HistoryPanel"""
        res = []
        if self.is_empty:
            res.append(f'{type(self)} \nEmpty History Panel at {hex(id(self))}')
        else:
            if self.level_count <= 7:
                display_shares = self.shares
            else:
                display_shares = self.shares[0:3]
            for share in display_shares:
                res.append(f'\nshare {self.levels[share]}, label: {share}\n')
                df = self.slice_to_dataframe(share=share)
                res.append(df.__str__())
                res.append('\n')
            if self.level_count > 7:
                res.append('\n ...  \n')
                for share in self.shares[-2:]:
                    res.append(f'\nshare {self.levels[share]}, label: {share}\n')
                    df = self.slice_to_dataframe(share=share)
                    res.append(df.__str__())
                    res.append('\n')
                res.append('Only first 3 and last 3 shares are displayed\n')
        return ''.join(res)

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values += other

    def __sub__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values -= other

    def __mul__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values *= other

    def __truediv__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values /= other

    def __floordiv__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values //= other

    def __mod__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values %= other

    def __pow__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values **= other

    def segment(self, start_date=None, end_date=None):
        """ 获取HistoryPanel的一个日期片段，start_date和end_date都是日期型数据，返回
            这两个日期之间的所有数据，返回的类型为一个HistoryPanel，包含所有share和
            htypes的数据

        Parameters
        ----------
        start_date: 开始日期
        end_date: 结束日期

        Returns
        -------
        out : HistoryPanel
            一个HistoryPanel，包含start_date到end_date之间所有share和htypes的数据

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.segment('2015-01-07', '2015-01-10')
        share 0, label: 000100
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50

        share 1, label: 000200
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50

        share 2, label: 000300
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        """
        hdates = np.array(self.hdates)
        if start_date is None:
            start_date = hdates[0]
        if end_date is None:
            end_date = hdates[-1]
        sd = pd.to_datetime(start_date)
        ed = pd.to_datetime(end_date)
        sd_index = hdates.searchsorted(sd)
        ed_index = hdates.searchsorted(ed, side='right')
        new_dates = list(hdates[sd_index:ed_index])
        new_values = self[:, :, sd_index:ed_index]
        return HistoryPanel(new_values, levels=self.shares, rows=new_dates, columns=self.htypes)

    def isegment(self, start_index=None, end_index=None):
        """ 获取HistoryPanel的一个片段，start_index和end_index都是int数，表示日期序号，返回
            这两个序号代表的日期之间的所有数据，返回的类型为一个HistoryPanel，包含所有share和
            htypes的数据

        Parameters
        ----------
        start_index: 开始日期序号
        end_index: 结束日期序号

        Returns
        -------
        out : HistoryPanel
            一个HistoryPanel，包含start_date到end_date之间所有share和htypes的数据

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.isegment(2, 5)
        share 0, label: 000100
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50

        share 1, label: 000200
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50

        share 2, label: 000300
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        """
        hdates = np.array(self.hdates)
        new_dates = list(hdates[start_index:end_index])
        new_values = self[:, :, start_index:end_index]
        return HistoryPanel(new_values, levels=self.shares, rows=new_dates, columns=self.htypes)

    def slice(self, shares=None, htypes=None):
        """ 获取HistoryPanel的一个股票或数据种类片段，shares和htypes可以为列表或逗号分隔字符
            串，表示需要获取的股票或数据的种类。

        Parameters
        ----------
        shares: str or list of str
            需要的股票列表
        htypes: str or list of str
            需要的数据类型列表

        Returns
        -------
        out : HistoryPanel
            一个HistoryPanel，包含shares和htypes中指定的股票和数据类型的数据

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        """
        if self.is_empty:
            return self
        if shares is None:
            shares = self.shares
        if isinstance(shares, str):
            shares = str_to_list(shares)
        if not isinstance(shares, list):
            raise KeyError(f'wrong shares are given!')

        if htypes is None:
            htypes = self.htypes
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
        if not isinstance(htypes, list):
            raise KeyError(f'wrong htypes are given!')
        new_values = self[htypes, shares]
        return HistoryPanel(new_values, levels=shares, columns=htypes, rows=self.hdates)

    def info(self):
        """ 打印本HistoryPanel对象的信息

        Returns
        -------
        None

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.info()
        <class 'qteasy.history.HistoryPanel'>
        History Panel at 0x12215a850
        Datetime Range: 10 entries, 2015-01-05 00:00:00 to 2015-01-14 00:00:00
        Historical Data Types (total 5 data types):
        ['open', 'high', 'low', 'close', 'volume']
        Shares (total 3 shares):
        ['000001', '000002', '000003']
        non-null values for each share and data type:
                open  high  low  close  volume
        000001    10    10   10     10      10
        000002    10    10   10     10      10
        000003    10    10   10     10      10
        memory usage: 1344 bytes
        """
        import sys
        print(f'\n{type(self)}')
        if self.is_empty:
            print(f'Empty History Panel at {hex(id(self))}')
        else:
            print(f'History Panel at {hex(id(self))}')
            if self.row_count != 0:
                print(f'Datetime Range: {self.row_count} entries, {self.hdates[0]} to {self.hdates[-1]}')
            print(f'Historical Data Types (total {self.column_count} data types):')
            if self.column_count <= 10:
                print(f'{self.htypes}')
            else:
                print(f'{self.htypes[0:3]} ... {self.htypes[-3:-1]}')
            print(f'Shares (total {self.level_count} shares):')
            if self.level_count <= 10:
                print(f'{self.shares}')
            else:
                print(f'{self.shares[0:3]} ... {self.shares[-3:-1]}')
            sum_nnan = np.sum(~np.isnan(self.values), 1)
            df = pd.DataFrame(sum_nnan, index=self.shares, columns=self.htypes)
            print('non-null values for each share and data type:')
            print(df)
            print(f'memory usage: {sys.getsizeof(self.values)} bytes\n')

    def copy(self):
        """ 返回一个新的HistoryPanel对象，其值和本对象相同"""
        # TODO: 应该考虑使用copy模块的copy(deep=True)代替下面的代码
        return HistoryPanel(values=self.values, levels=self.levels, rows=self.rows, columns=self.columns)

    def len(self):
        """ 返回HistoryPanel对象的长度，即日期个数

        Returns
        -------
        int
            日期个数

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.len()
        10
        """
        return self.row_count

    def re_label(self, shares: (str, list) = None, htypes: (str, list) = None, hdates: (str, list) = None) -> None:
        """ 给HistoryPanel对象的层、行、列标签重新赋值

        Parameters
        ----------
        shares: str or list of str
            股票列表
        htypes: str or list of str
            数据类型列表
        hdates: str or list of str
            日期列表

        Returns
        -------
        None

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.re_label(shares=['000100', '000200', '000300'], htypes=['typeA', 'typeB', 'typeC', 'typeD', 'typeE'])
        >>> hp
        share 0, label: 000100
                    typeA  typeB  typeC  typeD  typeE
        2015-01-05     10     20     30     40     50
        2015-01-06     10     20     30     40     50
        2015-01-07     10     20     30     40     50
        2015-01-08     10     20     30     40     50
        2015-01-09     10     20     30     40     50
        2015-01-10     10     20     30     40     50
        2015-01-11     10     20     30     40     50
        2015-01-12     10     20     30     40     50
        2015-01-13     10     20     30     40     50
        2015-01-14     10     20     30     40     50

        share 1, label: 000200
                    typeA  typeB  typeC  typeD  typeE
        2015-01-05     10     20     30     40     50
        2015-01-06     10     20     30     40     50
        2015-01-07     10     20     30     40     50
        2015-01-08     10     20     30     40     50
        2015-01-09     10     20     30     40     50
        2015-01-10     10     20     30     40     50
        2015-01-11     10     20     30     40     50
        2015-01-12     10     20     30     40     50
        2015-01-13     10     20     30     40     50
        2015-01-14     10     20     30     40     50

        share 2, label: 000300
                    typeA  typeB  typeC  typeD  typeE
        2015-01-05     10     20     30     40     50
        2015-01-06     10     20     30     40     50
        2015-01-07     10     20     30     40     50
        2015-01-08     10     20     30     40     50
        2015-01-09     10     20     30     40     50
        2015-01-10     10     20     30     40     50
        2015-01-11     10     20     30     40     50
        2015-01-12     10     20     30     40     50
        2015-01-13     10     20     30     40     50
        2015-01-14     10     20     30     40     50
        """
        if not self.is_empty:
            if shares is not None:
                self.shares = shares
            if htypes is not None:
                self.htypes = htypes
            if hdates is not None:
                self.hdates = hdates

    def fillna(self, with_val: [int, float]):
        """ 使用with_value来填充HistoryPanel中的所有nan值

        Parameters
        ----------
        with_val: float or int
            填充的值

        Returns
        -------
        out : HistoryPanel, 填充后的HistoryPanel对象
        """
        if not self.is_empty:
            self._values = fill_nan_data(self._values, with_val)
        return self

    def fillinf(self, with_val: [int, float]):
        """ 使用with_value来填充HistoryPanel中的所有inf值

        Parameters
        ----------
        with_val: float or int
            填充的值

        Returns
        -------
        out : HistoryPanel, 填充后的HistoryPanel对象
        """
        if not self.is_empty:
            self._values = fill_inf_data(self._values, with_val)
        return self

    def ffill(self, init_val=np.nan):
        """ 前向填充缺失值，当历史数据中存在缺失值时，使用缺失值以前
        的最近有效数据填充缺失值

        Parameters
        ----------
        init_val: float, 如果Nan值出现在第一行时，没有前序有效数据，则使用这个值来填充，默认为np.nan

        Returns
        -------
        out : HistoryPanel, 填充后的HistoryPanel对象

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[1, 2, 3], [4, np.nan, 6]], [[np.nan, 8, 9], [np.nan, np.nan, 12]]]),
        ...                   levels=['000001', '000002'], rows=['2015-01-01', '2015-01-02'],
        ...                   columns=['open', 'high', 'low'])
        >>> hp
        share 0, label: 000001
                    open  high  low
        2015-01-01   1.0   2.0  3.0
        2015-01-02   4.0   NaN  6.0
        share 1, label: 000002
                    open  high   low
        2015-01-01   NaN   8.0   9.0
        2015-01-02   NaN   NaN  12.0

        >>> hp.ffill()
        share 0, label: 000001
                    open  high  low
        2015-01-01   1.0   2.0  3.0
        2015-01-02   4.0   2.0  6.0
        share 1, label: 000002
                    open  high   low
        2015-01-01   NaN   8.0   9.0
        2015-01-02   NaN   8.0  12.0

        >>> hp.ffill(init_val=3)
        share 0, label: 000001
                    open  high  low
        2015-01-01   1.0   2.0  3.0
        2015-01-02   4.0   2.0  6.0
        share 1, label: 000002
                    open  high   low
        2015-01-01   3.0   8.0   9.0
        2015-01-02   3.0   8.0  12.0
        """

        if not self.is_empty:
            val = self.values
            if np.all(~np.isnan(val)):
                return self
            self._values = ffill_3d_data(val, init_val)
        return self

    def join(self,
             other,
             same_shares: bool = False,
             same_htypes: bool = False,
             same_hdates: bool = False,
             fill_value: float = np.nan):
        """ 将一个HistoryPanel对象与另一个HistoryPanel对象连接起来，生成一个新的HistoryPanel：

        新HistoryPanel的行、列、层标签分别是两个原始HistoryPanel的行、列、层标签的并集，也就是说，新的HistoryPanel的行、列
        层标签完全包含两个HistoryPanel对象的对应标签。

        Parameters
        ----------
        other: HistoryPanel
            需要合并的另一个HistoryPanel
        same_shares: bool, Default False
            两个HP的shares是否相同，如果相同，可以省去shares维度的标签合并，以节省时间。默认False，
        same_htypes: bool, Default False
            两个HP的htypes是否相同，如果相同，可以省去htypes维度的标签合并，以节省时间。默认False，
        same_hdates: bool, Default False
            两个HP的hdates是否相同，如果相同，可以省去hdates维度的标签合并，以节省时间。默认False，
        fill_value: float, Default np.nan

            空数据填充值，当组合后的HP存在空数据时，应该以什么值填充，默认为np.nan

        Returns
        -------
        HistoryPanel, 一个新的History Panel对象

        Examples
        --------
        # 如果两个HistoryPanel中包含标签相同的数据，那么新的HistoryPanel中将包含调用join方法的HistoryPanel对象的相应数据。例如：
        >>> hp1 = HistoryPanel(np.array([[[8, 9, 9], [7, 5, 5], [4, 8, 4], [1, 0, 7], [8, 7, 9]],
        ...                                     [[2, 3, 3], [5, 4, 6], [2, 8, 7], [3, 3, 4], [8, 8, 7]]]),
        ...                           levels=['000200', '000300'],
        ...                           rows=pd.date_range('2020-01-01', periods=5),
        ...                           columns=['close', 'open', 'high'])
        >>> hp2 = HistoryPanel(np.array([[[8, 9, 9], [7, 5, 5], [4, 8, 4], [1, 0, 7], [8, 7, 9]],
        ...                                     [[2, 3, 3], [5, 4, 6], [2, 8, 7], [3, 3, 4], [8, 8, 7]]]),
        ...                           levels=['000400', '000500'],
        ...                           rows=pd.date_range('2020-01-01', periods=5),
        ...                           columns=['close', 'open', 'high'])
        >>> hp1
        share 0, label: 000200
                    close  open  high
        2020-01-01      8     9     9
        2020-01-02      7     5     5
        2020-01-03      4     8     4
        2020-01-04      1     0     7
        2020-01-05      8     7     9
        share 1, label: 000300
                    close  open  high
        2020-01-01      2     3     3
        2020-01-02      5     4     6
        2020-01-03      2     8     7
        2020-01-04      3     3     4
        2020-01-05      8     8     7
        >>> hp2
        share 0, label: 000400
                    close  open  high
        2020-01-01      8     9     9
        2020-01-02      7     5     5
        2020-01-03      4     8     4
        2020-01-04      1     0     7
        2020-01-05      8     7     9
        share 1, label: 000500
                    close  open  high
        2020-01-01      2     3     3
        2020-01-02      5     4     6
        2020-01-03      2     8     7
        2020-01-04      3     3     4
        2020-01-05      8     8     7

        >>> hp1.join(hp2)
        share 0, label: 000200
        """

        assert isinstance(other, HistoryPanel), \
            f'TypeError, HistoryPanel can only be joined with other HistoryPanel.'
        if self.is_empty:
            return other
        elif other.is_empty:
            return self
        else:
            other_shares = other.shares
            other_htypes = other.htypes
            other_hdates = other.hdates
            this_shares = self.shares
            this_htypes = self.htypes
            this_hdates = self.hdates
            if not same_shares:
                combined_shares = list(set(this_shares).union(set(other_shares)))
                combined_shares.sort()
            else:
                assert this_shares == other_shares, f'Assertion Error, shares of two HistoryPanels are different!'
                combined_shares = self.shares
            if not same_htypes:
                combined_htypes = list(set(this_htypes).union(set(other_htypes)))
                combined_htypes.sort()
            else:
                assert this_htypes == other_htypes, f'Assertion Error, htypes of two HistoryPanels are different!'
                combined_htypes = self.htypes
            if not same_hdates:
                combined_hdates = list(set(this_hdates).union(set(other_hdates)))
                combined_hdates.sort()
            else:
                assert this_hdates == other_hdates, f'Assertion Error, hdates of two HistoryPanels are different!'
                combined_hdates = self.hdates
            combined_values = np.empty(shape=(len(combined_shares),
                                              len(combined_hdates),
                                              len(combined_htypes)))
            combined_values.fill(fill_value)
            if same_shares:
                if same_htypes:
                    for hdate in combined_hdates:
                        combined_hdate_id = labels_to_dict(combined_hdates, combined_hdates)
                        this_hdate_id = labels_to_dict(this_hdates, this_hdates)
                        other_hdate_id = labels_to_dict(other_hdates, other_hdates)
                        if hdate in this_hdates:
                            combined_values[:, combined_hdate_id[hdate], :] = self.values[:, this_hdate_id[hdate], :]
                        else:
                            combined_values[:, combined_hdate_id[hdate], :] = other.values[:, other_hdate_id[hdate], :]
                elif same_hdates:
                    for htype in combined_htypes:
                        combined_htype_id = labels_to_dict(combined_htypes, combined_htypes)
                        this_htype_id = labels_to_dict(this_htypes, this_htypes)
                        other_htype_id = labels_to_dict(other_htypes, other_htypes)
                        if htype in this_htypes:
                            combined_values[:, :, combined_htype_id[htype]] = self.values[:, :, this_htype_id[htype]]
                        else:
                            combined_values[:, :, combined_htype_id[htype]] = other.values[:, :, other_htype_id[htype]]
                else:
                    for hdate in combined_hdates:
                        for htype in combined_htypes:
                            combined_hdate_id = labels_to_dict(combined_hdates, combined_hdates)
                            this_hdate_id = labels_to_dict(this_hdates, this_hdates)
                            other_hdate_id = labels_to_dict(other_hdates, other_hdates)
                            combined_htype_id = labels_to_dict(combined_htypes, combined_htypes)
                            this_htype_id = labels_to_dict(this_htypes, this_htypes)
                            other_htype_id = labels_to_dict(other_htypes, other_htypes)
                            if htype in this_htypes and hdate in this_hdates:
                                combined_values[:, combined_hdate_id[hdate], combined_htype_id[htype]] = \
                                    self.values[:, this_hdate_id[hdate], this_htype_id[htype]]
                            elif htype in other_htypes and hdate in other_hdates:
                                combined_values[:, combined_hdate_id[hdate], combined_htype_id[htype]] = \
                                    other.values[:, other_hdate_id[hdate], other_htype_id[htype]]
            # TODO: implement this section 实现相同htype的HistoryPanel合并
            elif same_htypes:
                raise NotImplementedError
            # TODO: implement this section 实现相同数据历史时间戳的HistoryPanel合并
            else:
                raise NotImplementedError
            return HistoryPanel(values=combined_values,
                                levels=combined_shares,
                                rows=combined_hdates,
                                columns=combined_htypes)

    def as_type(self, dtype):
        """ 将HistoryPanel的数据类型转换为dtype类型，dtype只能为'float'或'int'

        Parameters
        ----------
        dtype: str, {'float', 'int'}
            需要转换的目标数据类型

        Returns
        -------
        self

        Raises
        ______
        AssertionError
            当输入的数据类型不正确或输入除float/int外的其他数据类型时
        """
        ALL_DTYPES = ['float', 'int']
        if not self.is_empty:
            assert isinstance(dtype, str), f'InputError, dtype should be a string, got {type(dtype)}'
            assert dtype in ALL_DTYPES, f'data type {dtype} is not recognized or not supported!'
            self._values = self.values.astype(dtype)
        return self

    def slice_to_dataframe(self,
                           htype: (str, int) = None,
                           share: (str, int) = None,
                           dropna: bool = False,
                           inf_as_na: bool = False) -> pd.DataFrame:
        """ 将HistoryPanel对象中的指定片段转化为DataFrame

        指定htype或者share，将这个htype或share对应的数据切片转化为一个DataFrame。
        由于HistoryPanel对象包含三维数据，因此在转化时必须指定htype或者share参数中的一个

        Parameters
        ----------
        htype:   str or int，
            表示需要生成DataFrame的数据类型切片
            如果给出此参数，定位该htype对应的切片后，将该htype对应的所有股票所有日期的数据转化为一个DataFrame
            如果类型为str，表示htype的名称，如果类型为int，代表该htype所在的列序号
        share:   str or int，
            表示需要生成DataFrame的股票代码切片
            如果给出此参数，定位该share对应的切片后，将该share对应的所有数据类型所有日期的数据转化为一个DataFrame
            如果类型为str，表示股票代码，如果类型为int，代表该share所在的层序号
        dropna: bool, Default False
            是否去除NaN值
        inf_as_na: bool, Default False
            是否将inf值当成NaN值一同去掉，当dropna为False时无效

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(values=np.array([[[1, 2, np.nan], [4, 5, 6]],
        ...                                    [[7, 8, np.nan], [np.inf, 11, 12]]]),
        ...                   levels=['000001', '000002'],
        ...                   rows=['2019-01-01', '2019-01-02'],
        ...                   columns=['open', 'high', 'low']))
        >>> hp
        share 0, label: 000001
                    open  high  low
        2019-01-01   1.0   2.0  NaN
        2019-01-02   4.0   5.0  NaN
        share 1, label: 000002
                    open  high   low
        2019-01-01   7.0   8.0   9.0
        2019-01-02   inf  11.0  12.0

        >>> hp.slice_to_dataframe(htype='open')
        000001  000002
        2019-01-01  1.0  7.0
        2019-01-02  4.0  inf

        >>> hp.slice_to_dataframe(share='000001')
        open  high  low
        2019-01-01  1.0  2.0  NaN
        2019-01-02  4.0  5.0  6.0

        >>> hp.slice_to_dataframe(htype='low', dropna=True)
                    000001  000002
        2019-01-02     6.0    12.0

        """

        if self.is_empty:
            return pd.DataFrame()
        if all(par is not None for par in (htype, share)) or all(par is None for par in (htype, share)):
            # 两个参数都是非None或都是None，应该弹出警告信息
            raise KeyError(f'Only and exactly one of the parameters htype and share should be given, '
                           f'got both or none')
        res_df = pd.DataFrame()
        if htype is not None:
            assert isinstance(htype, (str, int)), f'htype must be a string or an integer, got {type(htype)}'
            if isinstance(htype, int):
                htype = self.htypes[htype]
            if not htype in self.htypes:
                raise KeyError(f'htype {htype} is not found!')
            # 在生成DataFrame之前，需要把数据降低一个维度，例如shape(1, 24, 5) -> shape(24, 5)
            v = self[htype].T
            v = v.reshape(v.shape[-2:])
            res_df = pd.DataFrame(v, index=self.hdates, columns=self.shares)

        if share is not None:
            assert isinstance(share, (str, int)), f'share must be a string or an integer, got {type(share)}'
            if isinstance(share, int):
                share = self.shares[share]
            if not share in self.shares:
                raise KeyError(f'share {share} is not found!')
            # 在生成DataFrame之前，需要把数据降低一个维度，例如shape(1, 24, 5) -> shape(24, 5)
            v = self[:, share]
            v = v.reshape(v.shape[-2:])
            res_df = pd.DataFrame(v, index=self.hdates, columns=self.htypes)

        if dropna and inf_as_na:
            with pd.option_context('mode.use_inf_as_na', True):
                return res_df.dropna(how='all')
        if dropna:
            return res_df.dropna(how='all')

        return res_df

    def flatten_to_dataframe(self, along='row'):
        """ 将一个HistoryPanel"展平"成为一个DataFrame

        HistoryPanel的多层数据会被"平铺"到DataFrame的列，变成一个MultiIndex，或者多层数据
        会被平铺到DataFrame的行，同样变成一个MultiIndex，平铺到行还是列取决于along参数

        Parameters
        ----------
        along: str, {'col', 'row', 'column'} Default: 'row'
            平铺HistoryPanel的每一层时，沿行方向还是列方向平铺，
            'col'或'column'表示沿列方向平铺，'row'表示沿行方向平铺

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close  open        vol
        2020-01-01   12.3  12.5  1020010.0
        2020-01-02   12.6  13.2  1020020.0
        share 1, label: 000001
                    close  open      vol
        2020-01-01    2.3   2.5  20010.0
        2020-01-02    2.6   3.2  20020.0

        >>> hp.flatten_to_dataframe(along='col')
                   000300                  000001
                    close  open        vol  close open      vol
        2020-01-01   12.3  12.5  1020010.0    2.3  2.5  20010.0
        2020-01-02   12.6  13.2  1020020.0    2.6  3.2  20020.0

        >>> hp.flatten_to_dataframe(along='row')
                           close  open        vol
        000300 2020-01-01   12.3  12.5  1020010.0
               2020-01-02   12.6  13.2  1020020.0
        000001 2020-01-01    2.3   2.5    20010.0
               2020-01-02    2.6   3.2    20020.0
        """
        if not isinstance(along, str):
            raise TypeError(f'along must be a string, got {type(along)} instead')
        if along not in ('col', 'row', 'column'):
            raise ValueError(f'along must be "col" or "row", got {along}')

        df_dict = self.to_df_dict(by='share')
        if self.is_empty:
            return pd.DataFrame()
        if along in ('col', 'column'):
            return pd.concat(df_dict, axis=1, keys=df_dict.keys())
        if along == 'row':
            return pd.concat(df_dict, axis=0, keys=df_dict.keys())

    def to_multi_index_dataframe(self, along=None):
        """ 等同于HistoryPanel.flatten_to_dataframe()

        Parameters
        ----------
        along: str, {'col', 'row', 'column'} Default: 'row'
            平铺HistoryPanel的每一层时，沿行方向还是列方向平铺，
            'col'或'column'表示沿列方向平铺，'row'表示沿行方向平铺

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close  open        vol
        2020-01-01   12.3  12.5  1020010.0
        2020-01-02   12.6  13.2  1020020.0
        share 1, label: 000001
                    close  open      vol
        2020-01-01    2.3   2.5  20010.0
        2020-01-02    2.6   3.2  20020.0

        >>> hp.to_multi_index_dataframe(along='col')
                   000300                  000001
                    close  open        vol  close open      vol
        2020-01-01   12.3  12.5  1020010.0    2.3  2.5  20010.0
        2020-01-02   12.6  13.2  1020020.0    2.6  3.2  20020.0

        >>> hp.to_multi_index_dataframe(along='row')
                           close  open        vol
        000300 2020-01-01   12.3  12.5  1020010.0
               2020-01-02   12.6  13.2  1020020.0
        000001 2020-01-01    2.3   2.5    20010.0
               2020-01-02    2.6   3.2    20020.0
        """
        return self.flatten_to_dataframe(along=along)

    def flatten(self, along=None):
        """ 等同于HistoryPanel.flatten_to_dataframe()

        Parameters
        ----------
        along: str, {'col', 'row', 'column'} Default: 'row'
            平铺HistoryPanel的每一层时，沿行方向还是列方向平铺，
            'col'或'column'表示沿列方向平铺，'row'表示沿行方向平铺

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close  open        vol
        2020-01-01   12.3  12.5  1020010.0
        2020-01-02   12.6  13.2  1020020.0
        share 1, label: 000001
                    close  open      vol
        2020-01-01    2.3   2.5  20010.0
        2020-01-02    2.6   3.2  20020.0

        >>> hp.flatten(along='col')
                   000300                  000001
                    close  open        vol  close open      vol
        2020-01-01   12.3  12.5  1020010.0    2.3  2.5  20010.0
        2020-01-02   12.6  13.2  1020020.0    2.6  3.2  20020.0

        >>> hp.flatten(along='row')
                           close  open        vol
        000300 2020-01-01   12.3  12.5  1020010.0
               2020-01-02   12.6  13.2  1020020.0
        000001 2020-01-01    2.3   2.5    20010.0
               2020-01-02    2.6   3.2    20020.0
        """
        return self.flatten_to_dataframe(along=along)

    def to_df_dict(self, by: str = 'share') -> dict:
        """ 将一个HistoryPanel转化为一个dict，这个dict的keys是HP中的shares，values是每个shares对应的历史数据
            这些数据以DataFrame的格式存储

        Parameters
        ----------
        by: str, {'share', 'shares', 'htype', 'htypes'}, Default: 'share'
            - 'share' 或 'shares': 将HistoryPanel中的数据切成若干片，每一片转化成一个DataFrame，
            它的keys是股票的代码，每个股票代码一个DataFrame
            - 'htype' 或 'htypes': 将HistoryPanel中的数据切成若干片，每一片转化成一个DataFrame，

            它的keys是历史数据类型，每种类型一个DataFrame

        Returns
        -------
        df_dict: dict, {str: pandas.DataFrame}

        Examples
        --------
        >>> hp = HistoryPanel(np.random.randn(2, 3, 4),
        ...                   rows=['2020-01-01', '2020-01-02', '2020-01-03'],
        ...                   levels=['000001', '000002', '000003'],
        ...                   columns=['close', 'open', 'high', 'low'])
        >>> hp
        share 0, label: 000001
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        share 1, label: 000002
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        share 2, label: 000003
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2

        >>> hp.to_df_dict(by='share')
        {'000001':
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        , '000002':
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        , '000003':
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2
        }

        >>> hp.to_df_dict(by='htype')
        {'close':
                    000001,  000002,  000003
        2020-01-01  0.1,     1.1,     2.1
        2020-01-02  0.5,     1.5,     2.5
        2020-01-03  0.9,     1.9,     2.9
        , 'open':
                    000001,  000002,  000003
        2020-01-01  0.2,     1.2,     2.2
        2020-01-02  0.6,     1.6,     2.6
        2020-01-03  1.0,     2.0,     3.0
        , 'high':
                    000001,  000002,  000003
        2020-01-01  0.3,     1.3,     2.3
        2020-01-02  0.7,     1.7,     2.7
        2020-01-03  1.1,     2.1,     3.1
        , 'low':
                    000001,  000002,  000003
        2020-01-01  0.4,     1.4,     2.4
        2020-01-02  0.8,     1.8,     2.8
        2020-01-03  1.2,     2.2,     3.2
        }

        """

        if not isinstance(by, str):
            raise TypeError(f'by ({by}) should be a string, and either "shares" or "htypes", got {type(by)}')
        assert by.lower() in ['share', 'shares', 'htype', 'htypes']

        df_dict = {}
        if self.is_empty:
            return df_dict

        if by.lower() in ['share', 'shares']:
            for share in self.shares:
                df_dict[share] = self.slice_to_dataframe(share=share)
            return df_dict

        if by.lower() in ['htype', 'htypes']:
            for htype in self.htypes:
                df_dict[htype] = self.slice_to_dataframe(htype=htype)
            return df_dict

    def unstack(self, by: str = 'share') -> dict:
        """ 等同于方法self.to_df_dict(), 是方法self.to_df_dict()的别称

        Parameters
        ----------
        by: str, {'share', 'htype'}, default 'share'
            指定按照share或者htype来unstack, 默认为share

        Returns
        -------
        dict
            unstack后的结果，是一个字典，key为share或htype，value为对应的DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.random.randn(2, 3, 4),
        ...                   rows=['2020-01-01', '2020-01-02', '2020-01-03'],
        ...                   levels=['000001', '000002', '000003'],
        ...                   columns=['close', 'open', 'high', 'low'])
        >>> hp
        share 0, label: 000001
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        share 1, label: 000002
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        share 2, label: 000003
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2

        >>> hp.unstack(by='share')
        {'000001':
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        , '000002':
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        , '000003':
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2
        }

        >>> hp.unstack(by='htype')
        {'close':
                    000001,  000002,  000003
        2020-01-01  0.1,     1.1,     2.1
        2020-01-02  0.5,     1.5,     2.5
        2020-01-03  0.9,     1.9,     2.9
        , 'open':
                    000001,  000002,  000003
        2020-01-01  0.2,     1.2,     2.2
        2020-01-02  0.6,     1.6,     2.6
        2020-01-03  1.0,     2.0,     3.0
        , 'high':
                    000001,  000002,  000003
        2020-01-01  0.3,     1.3,     2.3
        2020-01-02  0.7,     1.7,     2.7
        2020-01-03  1.1,     2.1,     3.1
        , 'low':
                    000001,  000002,  000003
        2020-01-01  0.4,     1.4,     2.4
        2020-01-02  0.8,     1.8,     2.8
        2020-01-03  1.2,     2.2,     3.2
        }
        """

        return self.to_df_dict(by=by)

    def flattened_head(self, row_count=5):
        """ 以multi-index DataFrame的形式返回HistoryPanel的最初几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only first row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含前row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.flattened_head(3)
                    000300                  000001
                    close,  open,   vol,    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010 2.3,    2.5,    20010
        2020-01-02  12.6,   13.2,   1020020 2.6,    3.2,    20020
        2020-01-03  12.9,   13.0,   1020030 2.9,    3.0,    20030
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.flatten_to_dataframe(along='col').head(row_count)

    def flattened_tail(self, row_count=5):
        """ 以multi-index DataFrame的形式返回HistoryPanel的最后几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only last row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含后row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.flattened_tail(3)
                    000300                  000001
                    close,  open,   vol,    close,  open,   vol
        2020-01-04  12.3,   12.5,   1020040 2.3,    2.5,    20040
        2020-01-05  12.6,   13.2,   1020050 2.6,    3.2,    20050
        2020-01-06  12.9,   13.0,   1020060 2.9,    3.0,    20060
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.flatten_to_dataframe(along='col').tail(row_count)

    def head(self, row_count=5):
        """返回HistoryPanel的最初几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only first row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含前row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.head(3)
        share 0, label: 000300
                    close,  open,   vol,
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        share 1, label: 000001
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.isegment(0, row_count)

    def tail(self, row_count=5):
        """返回HistoryPanel的最末几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only last row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含最后row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.tail(3)
        share 0, label: 000300
                    close,  open,   vol
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.isegment(- row_count, None)

    # TODO: implement this method
    def plot(self, *args, **kwargs):
        """plot current HistoryPanel, settings according to args and kwargs
        """

        raise NotImplementedError

    # TODO: implement this method
    def candle(self, *args, **kwargs):
        """ plot candle chart with data in the HistoryPanel, check data availability before plotting
        """
        raise NotImplementedError

    # TODO: implement this method
    def ohlc(self, *args, **kwargs):
        """ plot ohlc chart with data in the HistoryPanel, check data availability before plotting

        args:
        kwargs:
        :return:
        """
        raise NotImplementedError

    # TODO: implement this method
    def renko(self, *args, **kwargs):
        """ plot renko chart with data in the HistoryPanel, check data availability before plotting

        args:
        kwargs:
        :return:
        """
        raise NotImplementedError


def hp_join(*historypanels):
    """ 当元组*historypanels不是None，且内容全都是HistoryPanel对象时，将所有的HistoryPanel对象连接成一个HistoryPanel

    parameters
    ----------
    historypanels: HistoryPanels
        一个或多个HistoryPanel对象，他们将被组合成一个包含他们所有数据的HistoryPanel

    Returns
    -------
    HistoryPanel
        组合后的HistoryPanel
    """
    assert all(isinstance(hp, HistoryPanel) for hp in historypanels), \
        f'Object type Error, all objects passed to this function should be HistoryPanel'
    res_hp = HistoryPanel()
    for hp in historypanels:
        if isinstance(hp, HistoryPanel):
            res_hp.join(other=hp)
    return res_hp


def dataframe_to_hp(
        df: pd.DataFrame,
        hdates=None,
        htypes=None,
        shares=None,
        column_type: str = None
):
    """ 根据DataFrame中的数据创建HistoryPanel对象。

    Parameters
    ----------
    df: pd.DataFrame,
        需要被转化为HistoryPanel的DataFrame。
    hdates: DatetimeIndex or List of DateTime like, Optional
        如果给出hdates，它会被用于转化后HistoryPanel的日期标签
    htypes: str or list of str, Optional
        转化后HistoryPanel的历史数据类型标签
    shares: str or list of str, Optional
        转化后HistoryPanel的股票代码标签
    column_type: str, Default None
        DataFrame的column代表的数据类型，可以为 'shares' or 'htype'
        如果为None，则必须输入htypes和shares参数中的一个

    Returns
    -------
    HistoryPanel对象

    Notes
    -----
    由于DataFrame只有一个二维数组，因此一个DataFrame只能转化为以下两种HistoryPanel之一：
    1，只有一个share，包含一个或多个htype的HistoryPanel，这时HistoryPanel的shape为(1, dates, htypes)
        在这种情况下，htypes可以由一个列表，或逗号分隔字符串给出，也可以由DataFrame对象的column Name来生成，而share则必须给出
    2，只有一个dtype，包含一个或多个shares的HistoryPanel，这时HistoryPanel的shape为(shares, dates, 1)
    具体转化为何种类型的HistoryPanel可以由column_type参数来指定，也可以通过给出hdates、htypes以及shares参数来由程序判断

    Examples
    --------
    >>> dataframe = pd.DataFrame(
    ...     data=np.random.rand(3, 3),
    ...     index=pd.date_range(start='2020-01-01', periods=3),
    ...     columns=['A', 'B', 'C']
    ... )
    >>> dataframe
    Out:
                       A         B         C
    2020-01-01  0.814394  0.284772  0.259304
    2020-01-02  0.237300  0.483317  0.600886
    2020-01-03  0.744638  0.255470  0.953640

    >>> hp = dataframe_to_hp(dataframe, htypes=['open', 'close', 'high'], shares='000001')
    >>> hp
    share 0, label: 000001
                    open     close      high
    2020-01-01  0.814394  0.284772  0.259304
    2020-01-02  0.237300  0.483317  0.600886
    2020-01-03  0.744638  0.255470  0.953640

    >>> hp = dataframe_to_hp(dataframe, htypes='open', shares=['000001', '000002', '000003'])
    >>> hp
    share 0, label: 000001
                    open
    2020-01-01  0.814394
    2020-01-02  0.237300
    2020-01-03  0.744638
    share 1, label: 000002
                    open
    2020-01-01  0.284772
    2020-01-02  0.483317
    2020-01-03  0.255470
    share 2, label: 000003
                    open
    2020-01-01  0.259304
    2020-01-02  0.600886
    2020-01-03  0.953640
    """

    available_column_types = ['shares', 'htypes', None]
    if not isinstance(df, pd.DataFrame):
        msg = f'Input df should be pandas DataFrame! got {type(df)} instead.'
        raise TypeError(msg)
    if hdates is None:
        hdates = df.rename(index=pd.to_datetime).index
    # if not isinstance(hdates, (list, tuple)):
    #     msg = f'TypeError, hdates should be list or tuple, got {type(hdates)} instead.'
    #     raise TypeError(msg)
    index_count = len(hdates)
    if not index_count == len(df.index):
        msg = f'InputError, can not match {index_count} indices with {len(df.hdates)} rows of DataFrame'
        raise ValueError(msg)
    if not column_type in available_column_types:
        msg = f'column_type should be either "shares" or "htypes", got {type(column_type)} instead!'
        raise ValueError(msg)
    # TODO: Temp codes, implement this method when column_type is not given -- the column type should be infered
    #  by the input combination of shares and htypes
    if column_type is None:  # try to infer a proper column type
        if shares is None:
            htype_list = []
            if htypes is None:
                raise KeyError(f'shares and htypes can not both be None if column_type is not given!')
            if isinstance(htypes, str):
                htype_list = str_to_list(htypes)
            try:
                if len(htype_list) == 1:
                    column_type = 'shares'
                else:
                    column_type = 'htypes'
            except:
                raise ValueError(f'htypes should be a list or a string, got {type(htypes)} instead')
        else:
            share_list = []
            if shares is None:
                raise KeyError(f'shares and htypes can not both be None if column_type is not given!')
            if isinstance(shares, str):
                share_list = str_to_list(shares)
            try:
                if len(share_list) == 1:
                    column_type = 'htypes'
                else:
                    column_type = 'shares'
            except:
                raise ValueError(f'shares should be a list or a string, got {type(shares)} instead')

    if column_type == 'shares':
        if shares is None:
            shares = df.columns
        if isinstance(shares, str):
            shares = str_to_list(shares, sep_char=',')
        if not len(shares) == len(df.columns):
            msg = f'Can not match {len(shares)} shares with {len(df.columns)} columns of DataFrame'
            raise ValueError(msg)
        if htypes is None:
            raise KeyError(f', Please provide a valid name for the htype of the History Panel')
        assert isinstance(htypes, str), \
            f'TypeError, data type of dtype should be a string, got {type(htypes)} instead.'
        share_count = len(shares)
        history_panel_value = np.zeros(shape=(share_count, len(hdates), 1))
        for i in range(share_count):
            history_panel_value[i, :, 0] = df.values[:, i]
    else:  # column_type == 'htype'
        if htypes is None:
            htypes = df.columns
        elif isinstance(htypes, str):
            htypes = htypes.split(',')
            assert len(htypes) == len(df.columns), \
                f'InputError, can not match {len(htypes)} shares with {len(df.columns)} columns of DataFrame'
        else:
            assert isinstance(htypes, (list, tuple)), f'TypeError: levels should be list or tuple, ' \
                                                      f'got {type(htypes)} instead.'
            assert len(htypes) == len(df.columns), \
                f'InputError, can not match {len(htypes)} shares with {len(df.columns)} columns of DataFrame'
        assert shares is not None, f'InputError, shares should be given when they can not inferred'
        assert isinstance(shares, str), \
            f'TypeError, data type of share should be a string, got {type(shares)} instead.'
        history_panel_value = df.values.reshape(1, len(hdates), len(htypes))
    return HistoryPanel(values=history_panel_value, levels=shares, rows=hdates, columns=htypes)


def from_single_dataframe(df: pd.DataFrame,
                          hdates=None,
                          htypes=None,
                          shares=None,
                          column_type: str = None) -> HistoryPanel:
    """ 函数dataframe_to_hp()的别称，等同于dataframe_to_hp()"""
    return dataframe_to_hp(df=df,
                           hdates=hdates,
                           htypes=htypes,
                           shares=shares,
                           column_type=column_type)


def from_multi_index_dataframe(df: pd.DataFrame):
    """ 将一个含有multi-index的DataFrame转化为一个HistoryPanel

    Parameters
    ----------
    df: pd.DataFrame
        需要被转化的DataFrame

    Returns
    -------
    HistoryPanel

    """
    raise NotImplementedError


def stack_dataframes(dfs: [list, dict], dataframe_as: str = 'shares', shares=None, htypes=None, fill_value=None):
    """ 将多个dataframe组合成一个HistoryPanel.

    Parameters
    ----------
    dfs: list of DataFrames or dict of DataFrames
        需要被堆叠的dataframe，可以为list或dict，
        dfs可以是一个dict或一个list，如果是一个list，这个list包含需要组合的所有dataframe，如果是dict，这个dict的values包含
        所有需要组合的dataframe，dict的key包含每一个dataframe的标签，这个标签可以被用作HistoryPanel的层（shares）或列
        （htypes）标签。如果dfs是一个list，则组合后的行标签或列标签必须明确给出。
    dataframe_as: str {'shares', 'htypes'}
        每个dataframe代表的数据类型。
        dataframe_as == 'shares'，
            表示每个DataFrame代表一个share的数据，每一列代表一个htype。组合后的HP对象
            层数与DataFrame的数量相同，而列数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
            在这种模式下：
            如果dfs是一个list，shares参数必须给出，且shares的数量必须与DataFrame的数量相同，作为HP的层标签
            如果dfs是一个dict，shares参数不必给出，dfs的keys会被用于层标签，如果shares参数给出且符合要求，
            shares参数将取代dfs的keys参数

        dataframe_as == 'htypes'，
            表示每个DataFrame代表一个htype的数据，每一列代表一个share。组合后的HP对象
            列数与DataFrame的数量相同，而层数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
            在这种模式下，
            如果dfs是一个list，htypes参数必须给出，且htypes的数量必须与DataFrame的数量相同，作为HP的列标签
            如果dfs是一个dict，htypes参数不必给出，dfs的keys会被用于列标签，如果htypes参数给出且符合要求，
            htypes参数将取代dfs的keys参数
    shares: str or list of str
        生成的HistoryPanel的层标签或股票名称标签。
        如果堆叠方式为"shares"，则层标签必须以dict的key的形式给出或者在shares参数中给出
        以下两种参数均有效且等效：
        '000001.SZ, 000002.SZ, 000003.SZ'
        ['000001.SZ', '000002.SZ', '000003.SZ']

        如果堆叠方式为"htypes"，不需要给出shares，默认使用dfs的columns标签的并集作为输出的层标签
        如果给出了shares，则会强制使用shares作为层标签，多出的标签会用fill_values填充，
        多余的DataFrame数据会被丢弃
    htypes: str or list of str
        生成的HistoryPanel的列标签或数据类型标签。
        如果堆叠方式为"htypes"，则层标签必须以dict的key的形式给出或者在shares参数中给出
        以下两种参数均有效且等效：
        '000001.SZ, 000002.SZ, 000003.SZ'
        ['000001.SZ', '000002.SZ', '000003.SZ']
        如果堆叠方式为"shares"，不需要给出htypes，默认使用dfs的columns标签的并集作为列标签
        如果给出了htypes，则会强制用它作为列标签，多出的标签会用fill_values填充，
        多余的DataFrame数据会被丢弃
    fill_value:
        多余的位置用fill_value填充

    Returns
    -------
    HistoryPanel
        一个由多个单index的数据框组成的HistoryPanel对象

    Examples
    --------
    >>> df1 = pd.DataFrame([[1, 2, 3], [4, 5, 6]], index=['20210101', '20210102'], columns=['open', 'close', 'low'])
    >>> df2 = pd.DataFrame([[7, 8, 9], [10, 11, 12]], index=['20210101', '20210102'], columns=['open', 'close', 'low'])
    >>> df3 = pd.DataFrame([[13, 14, 15], [16, 17, 18]], index=['20210101', '20210102'], columns=['open', 'close', 'low'])
    >>> dataframes = [df1, df2, df3]
    >>> hp = stack_dataframes(dataframes, dataframe_as='shares', shares='000001.SZ, 000002.SZ, 000003.SZ')
    >>> hp
    share 0, label: 000001.SZ
             open  close   low
    20210101  1.0    2.0   3.0
    20210102  4.0    5.0   6.0
    share 1, label: 000002.SZ
              open  close   low
    20210101   7.0    8.0   9.0
    20210102  10.0   11.0  12.0
    share 2, label: 000003.SZ
              open  close   low
    20210101  13.0   14.0  15.0
    20210102  16.0   17.0  18.0

    """
    assert isinstance(dfs, (list, dict)), \
        f'TypeError, dfs should be a list of or a dict whose values are pandas DataFrames, got {type(dfs)} instead.'
    assert dataframe_as in ['shares', 'htypes'], \
        f'InputError, valid input for dataframe_as can only be \'shares\' or \'htypes\''
    if fill_value is None:
        fill_value = np.nan
    assert isinstance(fill_value, (int, float)), f'invalid fill value type {type(fill_value)}'
    if shares is not None:
        if isinstance(shares, str):
            shares = str_to_list(shares)
    if htypes is not None:
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
    combined_index = []
    combined_shares = []
    combined_htypes = []
    # 检查输入参数是否正确
    if dataframe_as == 'shares':
        axis_names = shares
        combined_axis_names = combined_shares
    else:  # dataframe_as == 'htypes':
        axis_names = htypes
        combined_axis_names = combined_htypes
    # 根据叠放方式不同，需要检查的参数也不同
    assert (axis_names is not None) or (isinstance(dfs, dict)), \
        f'htypes should be given if the dataframes are to be stacked along htypes and they are not in a dict'
    assert isinstance(axis_names, (list, str)) or (isinstance(dfs, dict))
    if isinstance(axis_names, str):
        axis_names = str_to_list(axis_names)
    if isinstance(dfs, dict) and axis_names is None:
        axis_names = dfs.keys()
    assert len(axis_names) == len(dfs)
    combined_axis_names.extend(axis_names)

    if isinstance(dfs, dict):
        dfs = dfs.values()
    # 逐个处理所有传入的DataFram，合并index、htypes以及shares
    for df in dfs:
        assert isinstance(df, pd.DataFrame), \
            f'InputError, dfs should be a list of pandas DataFrame, got {type(df)} instead.'
        combined_index.extend(df.rename(index=pd.to_datetime).index)
        if dataframe_as == 'shares':
            combined_htypes.extend(df.columns)
        else:
            combined_shares.extend(df.columns)
    dfs = [df.rename(index=pd.to_datetime) for df in dfs]
    # 合并htypes及shares，
    # 如果没有直接给出shares或htypes，使用他们的并集并排序
    # 如果直接给出了shares或htypes，直接使用并保持原始顺序
    if (dataframe_as == 'shares') and (htypes is None):
        combined_htypes = list(set(combined_htypes))
        combined_htypes.sort()
    elif (dataframe_as == 'shares') and (htypes is not None):
        combined_htypes = htypes
    elif (dataframe_as == 'htypes') and (shares is None):
        combined_shares = list(set(combined_shares))
        combined_shares.sort()
    elif (dataframe_as == 'htypes') and (shares is not None):
        combined_shares = shares
    combined_index = list(set(combined_index))
    htype_count = len(combined_htypes)
    share_count = len(combined_shares)
    index_count = len(combined_index)
    combined_htypes_dict = dict(zip(combined_htypes, range(htype_count)))
    combined_shares_dict = dict(zip(combined_shares, range(share_count)))
    combined_index.sort()
    # 生成并复制数据
    res_values = np.zeros(shape=(share_count, index_count, htype_count))
    res_values.fill(fill_value)
    for df_id in range(len(dfs)):
        extended_df = dfs[df_id].reindex(combined_index)
        for col_name, series in extended_df.items():  # iteritems is deprecated since 1.5 and removed since 2.0
            if dataframe_as == 'shares':
                if col_name not in combined_htypes_dict:
                    continue
                res_values[df_id, :, combined_htypes_dict[col_name]] = series.values
            else:
                if col_name not in combined_shares_dict:
                    continue
                res_values[combined_shares_dict[col_name], :, df_id] = series.values
    return HistoryPanel(res_values,
                        levels=combined_shares,
                        rows=combined_index,
                        columns=combined_htypes)


def from_df_dict(dfs: [list, dict], dataframe_as: str = 'shares', shares=None, htypes=None, fill_value=None):
    """ 函数stack_dataframes()的别称，等同于函数stack_dataframes()"""
    return stack_dataframes(dfs=dfs,
                            dataframe_as=dataframe_as,
                            shares=shares,
                            htypes=htypes,
                            fill_value=fill_value)


def _adjust_freq(hist_data: pd.DataFrame,
                 target_freq: str,
                 *,
                 method: str = 'last',
                 b_days_only: bool = True,
                 trade_time_only: bool = True,
                 forced_start: str = None,
                 forced_end: str = None,
                 **kwargs):
    """ 降低获取数据的频率，通过插值的方式将高频数据降频合并为低频数据，使历史数据的时间频率
    符合target_freq

    Parameters
    ----------
    hist_data: pd.DataFrame
        历史数据，是一个index为日期/时间的DataFrame
    target_freq: str
        历史数据的目标频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
         如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
    method: str
        调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
        数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
        降频可用的methods有：
        - 'last'/'close': 使用合并区间的最后一个值
        - 'first'/'open': 使用合并区间的第一个值
        - 'max'/'high': 使用合并区间的最大值作为合并值
        - 'min'/'low': 使用合并区间的最小值作为合并值
        - 'mean'/'average': 使用合并区间的平均值作为合并值
        - 'sum/total': 使用合并区间的总和作为合并值

        数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
        升频可用的methods有：
        - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN
        - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN
        - 'nan': 使用NaN值填充缺失数据
        - 'zero': 使用0值填充缺失数据
    b_days_only: bool 默认True
        是否强制转换自然日频率为工作日，即：
        'D' -> 'B'
        'W' -> 'W-FRI'
        'M' -> 'BM'
    trade_time_only: bool, 默认True
        为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
    forced_start: str, Datetime like, 默认None
        强制开始日期，如果为None，则使用hist_data的第一天为开始日期
    forced_start: str, Datetime like, 默认None
        强制结束日期，如果为None，则使用hist_data的最后一天为结束日期
    **kwargs:
        用于生成trade_time_index的参数，包括：
        include_start:   日期时间序列是否包含开始日期/时间
        include_end:     日期时间序列是否包含结束日期/时间
        start_am:        早晨交易时段的开始时间
        end_am:          早晨交易时段的结束时间
        include_start_am:早晨交易时段是否包括开始时间
        include_end_am:  早晨交易时段是否包括结束时间
        start_pm:        下午交易时段的开始时间
        end_pm:          下午交易时段的结束时间
        include_start_pm 下午交易时段是否包含开始时间
        include_end_pm   下午交易时段是否包含结束时间

    Returns
    -------
    DataFrame:
    一个重新设定index并填充好数据的历史数据DataFrame

    Examples
    --------
    例如，合并下列数据(每一个tuple合并为一个数值，?表示合并后的数值）
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(?), (?), (?)]
    数据合并方法:
    - 'last'/'close': 使用合并区间的最后一个值。如：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
    - 'first'/'open': 使用合并区间的第一个值。如：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
    - 'max'/'high': 使用合并区间的最大值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
    - 'min'/'low': 使用合并区间的最小值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
    - 'avg'/'mean': 使用合并区间的平均值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]
    - 'sum'/'total': 使用合并区间的平均值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]

    例如，填充下列数据(?表示插入的数据）
        [1, 2, 3] 填充后变为: [?, 1, ?, 2, ?, 3, ?]
    缺失数据的填充方法如下:
    - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN。如：
        [1, 2, 3] 填充后变为: [NaN, 1, 1, 2, 2, 3, 3]
    - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN。如：
        [1, 2, 3] 填充后变为: [1, 1, 2, 2, 3, 3, NaN]
    - 'nan': 使用NaN值填充缺失数据：
        [1, 2, 3] 填充后变为: [NaN, 1, NaN, 2, NaN, 3, NaN]
    - 'zero': 使用0值填充缺失数据：
        [1, 2, 3] 填充后变为: [0, 1, 0, 2, 0, 3, 0]
    """

    if not isinstance(target_freq, str):
        err = TypeError(f'target freq should be a string, got {target_freq}({type(target_freq)}) instead.')
        raise err
    target_freq = target_freq.upper()
    # 如果hist_data为空，直接返回
    if hist_data.empty:
        return hist_data
    if b_days_only:
        if target_freq in ['W', 'W-SUN']:
            target_freq = 'W-FRI'
        elif target_freq == 'M':
            target_freq = 'BM'
    # 如果hist_data的freq与target_freq一致，也可以直接返回
    # TODO: 这里有bug：强制start/end的情形需要排除
    if hist_data.index.freqstr == target_freq:
        return hist_data
    # 如果hist_data的freq为None，可以infer freq
    if hist_data.index.inferred_freq == target_freq:
        return hist_data

    # 新版本pandas修改了部分freq alias，为了确保向后兼容，确保freq_aliases与pandas版本匹配
    target_freq = pandas_freq_alias_version_conversion(target_freq)

    resampled = hist_data.resample(target_freq)
    if method in ['last', 'close']:
        resampled = resampled.last()
    elif method in ['first', 'open']:
        resampled = resampled.first()
    elif method in ['max', 'high']:
        resampled = resampled.max()
    elif method in ['min', 'low']:
        resampled = resampled.min()
    elif method in ['avg', 'mean']:
        resampled = resampled.mean()
    elif method in ['sum', 'total']:
        resampled = resampled.sum()
    elif method == 'ffill':
        resampled = resampled.ffill()
    elif method == 'bfill':
        resampled = resampled.bfill()
    elif method in ['nan', 'none']:
        resampled = resampled.first()
    elif method == 'zero':
        resampled = resampled.first().fillna(0)
    else:
        # for unexpected cases
        err = ValueError(f'resample method {method} can not be recognized.')
        raise err

    # 完成resample频率切换后，根据设置去除非工作日或非交易时段的数据
    # 并填充空数据
    resampled_index = resampled.index
    if forced_start is None:
        start = resampled_index[0]
    else:
        start = pd.to_datetime(forced_start)
    if forced_end is None:
        end = resampled_index[-1]
    else:
        end = pd.to_datetime(forced_end)

    # 如果要求强制转换自然日频率为工作日频率
    # 原来的版本在resample之前就强制转换自然日到工作日，但是测试发现，pd的resample有一个bug：
    # 这个bug会导致method为last时，最后一个工作日的数据取自周日，而不是周五
    # 在实际测试中发现，如果将2020-01-01到2020-01-10之间的Hourly数据汇总到工作日时
    # 2020-01-03是周五，汇总时本来应该将2020-01-03 23:00:00的数据作为当天的数据
    # 但是实际上2020-01-05 23:00:00 的数据被错误地放置到了周五，也就是周日的数据被放到
    # 了周五，这样可能会导致错误的结果
    # 因此解决方案是，仍然按照'D'频率来resample，然后再通过reindex将非交易日的数据去除
    # 不过仅对freq为'D'的频率如此操作
    if b_days_only:
        if target_freq == 'D':
            target_freq = 'B'

    # 如果要求去掉非交易时段的数据
    from qteasy.trading_util import _trade_time_index
    if trade_time_only:
        expanded_index = _trade_time_index(
                start=start,
                end=end,
                freq=target_freq,
                trade_days_only=b_days_only,
                **kwargs
        )
    else:
        expanded_index = pd.date_range(start=start, end=end, freq=target_freq)
    resampled = resampled.reindex(index=expanded_index)
    # 如果在数据开始或末尾增加了空数据（因为forced start/forced end），需要根据情况填充
    if (expanded_index[-1] > resampled_index[-1]) or (expanded_index[0] < resampled_index[0]):
        if method == 'ffill':
            resampled.ffill(inplace=True)
        elif method == 'bfill':
            resampled.bfill(inplace=True)
        elif method == 'zero':
            resampled.fillna(0, inplace=True)

    return resampled


# ==================
# High level functions that creates HistoryPanel that fits the requirement of trade strategies
# ==================
def get_history_panel(
        data_types,
        data_source,
        shares=None,
        freq=None,
        start=None,
        end=None,
        rows=None,
        drop_nan=True,
        resample_method='ffill',
        b_days_only=True,
        trade_time_only=True,
        **kwargs
):
    """ 最主要的历史数据获取函数，从本地DataSource（数据库/csv/hdf/fth）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

    Parameters
    ----------
    data_types: [DataType]
        需要获取的历史数据类型集合，必须是合法的DataType数据类型对象，
    data_source: DataSource
        数据源对象，用于获取数据
    shares: [str, list]
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
         - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
    freq: str
        获取的历史数据的频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
    start: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
    end: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
    rows: int
        获取的历史数据的行数，如果rows为None，则获取所有可用的历史数据
        如果rows为正整数，则获取最近的rows行历史数据，如果给出了start或end参数，则忽略rows参数
    drop_nan: bool
        是否保留全NaN的行
    resample_method: str
        如果数据需要升频或降频时，调整频率的方法
        调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
        数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
        例如，合并下列数据(每一个tuple合并为一个数值，?表示合并后的数值）
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(?), (?), (?)]
        数据合并方法:
        - 'last'/'close': 使用合并区间的最后一个值。如：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
        - 'first'/'open': 使用合并区间的第一个值。如：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
        - 'max'/'high': 使用合并区间的最大值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
        - 'min'/'low': 使用合并区间的最小值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
        - 'avg'/'mean': 使用合并区间的平均值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]
        - 'sum'/'total': 使用合并区间的平均值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]

        数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
        例如，填充下列数据(?表示插入的数据）
            [1, 2, 3] 填充后变为: [?, 1, ?, 2, ?, 3, ?]
        缺失数据的填充方法如下:
        - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN。如：
            [1, 2, 3] 填充后变为: [NaN, 1, 1, 2, 2, 3, 3]
        - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN。如：
            [1, 2, 3] 填充后变为: [1, 1, 2, 2, 3, 3, NaN]
        - 'nan': 使用NaN值填充缺失数据：
            [1, 2, 3] 填充后变为: [NaN, 1, NaN, 2, NaN, 3, NaN]
        - 'zero': 使用0值填充缺失数据：
            [1, 2, 3] 填充后变为: [0, 1, 0, 2, 0, 3, 0]
    b_days_only: bool 默认True
        是否强制转换自然日频率为工作日，即：
        'D' -> 'B'
        'W' -> 'W-FRI'
        'M' -> 'BM'
    trade_time_only: bool, 默认True
        为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
    resample_method: str
        处理数据频率更新时的方法
    **kwargs:
        用于生成trade_time_index的参数，包括：
        include_start:   日期时间序列是否包含开始日期/时间
        include_end:     日期时间序列是否包含结束日期/时间
        start_am:        早晨交易时段的开始时间
        end_am:          早晨交易时段的结束时间
        include_start_am:早晨交易时段是否包括开始时间
        include_end_am:  早晨交易时段是否包括结束时间
        start_pm:        下午交易时段的开始时间
        end_pm:          下午交易时段的结束时间
        include_start_pm 下午交易时段是否包含开始时间
        include_end_pm   下午交易时段是否包含结束时间

    Returns
    -------
    DataFrame
    """
    if not data_types:
        return HistoryPanel()

    if data_source is None:
        raise TypeError(f'data source should not be None!')

    if freq is None:
        raise TypeError(f'freq can not be None!')

    if shares:
        normal_dfs = get_history_data_from_source(
                datasource=data_source,
                htypes=data_types,
                qt_codes=list_to_str_format(shares),
                start=start,
                end=end,
                freq=freq,
                row_count=rows,
                combine_htype_names=True,
        )
        all_dfs = normal_dfs
    else:
        # 获取无share数据
        reference_dfs = get_reference_data_from_source(
                datasource=data_source,
                htypes=data_types,
                start=start,
                end=end,
                freq=freq,
                row_count=rows,
        )
        all_dfs = reference_dfs

    # 处理所有的df，根据设定执行以下几个步骤：
    #  1，确保所有的DataFrame都有同样的时间频率，如果时间频率小于日频，输出时间仅包含交易时间内，如果频率为日频，排除周末
    #  2，检查整行NaN值的情况，根据设定去掉或保留这些行
    #  3，如果df是一个Series，则将其转化为DataFrame
    for htyp, df in all_dfs.items():
        if isinstance(df, pd.Series):
            df = pd.DataFrame(df)
            df.columns = ['none']
        # find freq of the htyp:
        htype_freq = [d_type for d_type in data_types if d_type.name == htyp][0]
        if (not b_days_only) or (not trade_time_only) or (htype_freq.freq != freq):
            new_df = _adjust_freq(
                    df,
                    target_freq=freq,
                    method=resample_method,
                    forced_start=start,
                    forced_end=end,
                    b_days_only=b_days_only,
                    trade_time_only=trade_time_only,
                    **kwargs
            )
            df = new_df
        if rows is not None:
            assert isinstance(rows, int)
            assert rows > 0
            df = df.tail(rows)
        if drop_nan:
            df = df.dropna(how='all')
        all_dfs[htyp] = df

    result_hp = stack_dataframes(all_dfs, dataframe_as='htypes', htypes=all_dfs.keys(), shares=shares)

    return result_hp
