# coding=utf-8
# ======================================
# File:     history.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-16
# Desc:
#   HistoryPanel Class, and more history
#   data manipulating functions.
# ======================================

import pandas as pd
import numpy as np

import qteasy
from .utilfuncs import str_to_list, list_or_slice, labels_to_dict, ffill_3d_data


class HistoryPanel():
    """qteasy 量化投资系统使用的主要历史数据的数据类型.

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
            HistoryPanel.shares 输出一个列表，包含按顺序排列的所有层标签，即所有股票品种代码或名称
            HistoryPanel.hdates 输出一个列表，包含按顺序排列的所有行标签，即所有数据的日期及时间
            HistoryPanel.htypes 输出一个列表，包含按顺序排列的所有列标签，即所数据类型
            HistoryPanel.levels 输出一个字典，包含所有层标签及其对应的层编号（从0开始到M-1）
            HistoryPanel.columns 输出一个字典，包含所有数据类型标签及其对应的列编号（从0开始到L-1）
            HistoryPanel.rows 输出一个字典，包含所有日期行标签及其对应的行号，从0开始一直到N-1）
        3, 方便地打印HistoryPanel的相关信息
        4, 方便地打印及格式化输出HistoryPanel的内容，如：

        5, 方便地转化为 pandas DataFrame对象
            HistoryPanel不能完整转化为DataFrame对象，因为DataFrame只能适应2D数据。在转化为DataFrame的时候，用户只能选择
            HistoryPanel的一个切片，或者是一个股票品种，或者是一个数据类型，输出的DataFrame包含的数据行数与
        6, 方便地由多个pandas DataFrame对象组合而成
    """

    def __init__(self, values: np.ndarray = None, levels=None, rows=None, columns=None):
        """ 初始化HistoryPanel对象，必须传入values作为HistoryPanel的数据

            一个HistoryPanel对象是qteasy中用于历史数据操作的主要数据结构，其本质是一个numpy.ndarray，这个ndarray是一个
            三维数组，这个三维数组有L层，R行、C列，分别代表L种历史数据、R条数据记录、C种股票的历史数据。

            在生成一个HistoryPanel的时候，可以同时输入层标签（股票代码）、行标签（日期时间）和列标签（历史数据类型）
            如果不输入这些数据，HistoryPanel会自动生成标签。在某些qteasy应用中，要求输入正确的标签，如果标签不正确
            可能导致报错。

            历史数据类型可以包括类似开盘价、收盘价这样的量价数据，同样也可以包括诸如pe、ebitda等等财务数据

        :param values:
            一个ndarray，该数组的维度不能超过三维，如果给出的数组维度不够三维，将根据给出的标签推断并补齐维度
            如果不给出values，则会返回一个空HistoryPanel，其empty属性为True

        :param levels:
            HistoryPanel的股票标签，层的数量为values第一个维度的数据量，每一层代表一种股票或资产

        :param rows:
            HistoryPanel的时间日期标签。
            datetime range或者timestamp index或者str类型，通常是时间类型或可以转化为时间类型，
            行标签代表每一条数据对应的历史时间戳

        :param columns:str，
            HistoryPanel的列标签，代表历史数据的类型，既可以是历史数据的
        """

        # TODO: 在生成HistoryPanel时如果只给出data或者只给出data+columns，生成HistoryPanel打印时会报错，问题出在to_dataFrame()上
        # TODO: 在生成HistoryPanel时传入的ndarray会被直接用于HistoryPanel，如果事后修改这个ndarray，HistoryPanel也会改变
        # TODO: 应该考虑是否在创建HistoryPanel时生成ndarray的一个copy而不是使用其自身 。
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
        :return:
        """
        return self._rows

    @property
    def hdates(self):
        """获取HistoryPanel的历史日期时间戳list"""
        # TODO: Maybe: 可以将返回值包装成一个pandas.Index对象，
        # TODO: 这样有更多方便好用的方法和属性可用
        # TODO: 例如
        # TODO: return pd.Index(self._rows.keys())
        # TODO: 这样就可以用 HP.hdates.date / HP.hdates.where()
        # TODO: 等等方法和属性了
        # TODO: shares 和 htypes 属性也可以如法炮制
        if self.is_empty:
            return 0
        else:
            # return pd.Index(self._rows.keys(), dtype='datetime64')
            return list(self._rows.keys())

    @hdates.setter
    def hdates(self, input_hdates: list):
        if not self.is_empty:
            assert isinstance(input_hdates, list), f'TypeError, input_hdates should be '
            assert len(input_hdates) == self.row_count, \
                f'ValueError, the number of input shares ({len(input_hdates)}) does not match level ' \
                f'count ({self.row_count})'
            try:
                new_hdates = [pd.to_datetime(date) for date in input_hdates]
            except:
                raise ValueError('one or more item in hdate list can not be converted to Timestamp')
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
        """获取HistoryPanel的历史数据长度"""
        return self._r_count

    def __getitem__(self, keys=None):
        """获取历史数据的一个切片，给定一个type、日期或股票代码, 输出相应的数据

        允许的输入包括切片形式的各种输入，包括string、数字列表或切片器对象slice()，返回切片后的ndarray对象
        允许的输入示例，第一个切片代表type切片，第二个是shares，第三个是rows：
        item_key                    output
        [1:3, :,:]                  输出1～3之间所有htype的历史数据
        [[0,1,2],:,:]:              输出第0、1、2个htype对应的所有股票全部历史数据
        [['close', 'high']]         输出close、high两个类型的所有历史数据
        [0:1]                       输出0、1两个htype的所有历史数据
        ['close,high']              输出close、high两个类型的所有历史数据
        ['close:high']              输出close、high之间所有类型的历史数据（包含close和high）
        [:,[0,1,3]]                 输出0、1、3三个股票的全部历史数据
        [:,['000100', '000120']]    输出000100、000120两只股票的所有历史数据
        [:,0:2]                     输出0、1、2三个股票的历史数据
        [:,'000100,000120']         输出000100、000120两只股票的所有历史数据

        input：
            :param keys: list/tuple/slice历史数据的类型名，为空时给出所有类型的数据
        输出：
            self.value的一个切片
        """
        if self.is_empty:
            return None
        else:
            key_is_None = keys is None
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
            elif key_is_None:
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
                df = self.to_dataframe(share=share)
                res.append(df.__str__())
                res.append('\n')
            if self.level_count > 7:
                res.append('\n ...  \n')
                for share in self.shares[-2:]:
                    res.append(f'\nshare {self.levels[share]}, label: {share}\n')
                    df = self.to_dataframe(share=share)
                    res.append(df.__str__())
                    res.append('\n')
                res.append('Only first 3 and last 3 shares are displayed\n')
        return ''.join(res)

    def __repr__(self):
        return self.__str__()

    def segment(self, start_date=None, end_date=None):
        """ 获取HistoryPanel的一个日期片段，start_date和end_date都是日期型数据，返回
            这两个日期之间的所有数据，返回的类型为一个HistoryPanel，包含所有share和
            htypes的数据

        :input
            :param start_date: 开始日期
            :param end_date: 结束日期

        :return
            HistoryPanel
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

    def slice(self, shares=None, htypes=None):
        """ 获取HistoryPanel的一个股票或数据种类片段，shares和htypes可以为列表或逗号分隔字符
            串，表示需要获取的股票或数据的种类。

        :input
            :param shares: 需要的股票列表
            :param htypes: 需要的数据类型列表

        :return
            HistoryPanel
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

        :return:
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
            sum_nnan = np.sum(~np.isnan(self.values), 1)
            df = pd.DataFrame(sum_nnan, index=self.shares, columns=self.htypes)
            print('non-null values for each share and data type:')
            print(df)
            print(f'memory usage: {sys.getsizeof(self.values)} bytes\n')

    def copy(self):
        # TODO: 应该考虑使用copy模块的copy(deep=True)代替下面的代码
        return HistoryPanel(values=self.values, levels=self.levels, rows=self.rows, columns=self.columns)

    def re_label(self, shares: str = None, htypes: str = None, hdates=None):
        """ 给HistoryPanel对象的层、行、列标签重新赋值

        :param shares: List or Str
        :param htypes:
        :param hdates:
        :return: HistoryPanel
        """
        if not self.is_empty:
            if shares is not None:
                self.shares = shares
            if htypes is not None:
                self.htypes = htypes
            if hdates is not None:
                self.hdates = hdates

    def fillna(self, with_val: [int, float, np.int, np.float]):
        """ 使用with_value来填充HistoryPanel中的所有nan值

        :param with_val:
        :return:
        """
        if not self.is_empty:
            self._values = np.where(np.isnan(self._values), with_val, self._values)
        return self

    def fillinf(self, with_val: [int, float, np.int, np.float]):
        """ 使用with_value来填充HistoryPanel中的所有inf值

        :param with_val: flaot
        :return:
        """
        if not self.is_empty:
            self._values = np.where(np.isinf(self._values), with_val, self._values)
        return self

    def ffill(self, init_val=np.nan):
        """ 前向填充缺失值，当历史数据中存在缺失值时，使用缺失值以前
        的最近有效数据填充缺失值

        :param init_val: float, 如果Nan值出现在第一行时，没有前序有效数据，则使用这个值来填充，默认为np.nan
        :return:
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
        """ Join one historypanel object with another one
            将一个HistoryPanel对象与另一个HistoryPanel对象连接起来，生成一个新的HistoryPanel：

            新HistoryPanel的行、列、层标签分别是两个原始HistoryPanel的行、列、层标签的并集，也就是说，新的HistoryPanel的行、列
            层标签完全包含两个HistoryPanel对象的对应标签。

            如果两个HistoryPanel中包含标签相同的数据，那么新的HistoryPanel中将包含调用join方法的HistoryPanel对象的相应数据。例如：

            hp1:
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

            hp2:
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

            连接时可以指定两个HistoryPanel之间共享的标签类型，如

        :param other: type: HistoryPanel 需要合并的另一个HistoryPanel
        :param same_shares: 两个HP的shares是否相同，如果相同，可以省去shares维度的标签合并，以节省时间。默认False，
        :param same_htypes: 两个HP的htypes是否相同，如果相同，可以省去htypes维度的标签合并，以节省时间。默认False，
        :param same_hdates: 两个HP的hdates是否相同，如果相同，可以省去hdates维度的标签合并，以节省时间。默认False，
        :param fill_value:  空数据填充值，当组合后的HP存在空数据时，应该以什么值填充，默认为np.nan
        :return:
        一个新的History Panel对象
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
        """ 将HistoryPanel的数据类型转换为dtype类型
        dtype只能为'float'或'int'

        :param dtype:
        :return:
        """
        ALL_DTYPES = ['float', 'int']
        if not self.is_empty:
            assert isinstance(dtype, str), f'InputError, dtype should be a string, got {type(dtype)}'
            assert dtype in ALL_DTYPES, f'data type {dtype} is not recognized or not supported!'
            self._values = self.values.astype(dtype)
        return self

    def to_dataframe(self,
                     htype: (str, int) = None,
                     share: (str, int) = None,
                     dropna: bool = False,
                     inf_as_na: bool = False) -> pd.DataFrame:
        """ 将HistoryPanel对象中的指定片段转化为DataFrame

            指定htype或者share，将这个htype或share对应的数据切片转化为一个DataFrame。
            由于HistoryPanel对象包含三维数据，因此在转化时必须指定htype或者share参数中的一个

            :param htype:   一个string或int，表示需要生成DataFrame的数据类型切片
                            如果给出此参数，定位该htype对应的切片后，将该htype对应的所有股票所有日期的数据转化为一个DataFrame
                            如果类型为str，表示htype的名称，如果类型为int，代表该htype所在的列序号

            :param share:   一个string或int，表示需要生成DataFrame的股票代码切片
                            如果给出此参数，定位该share对应的切片后，将该share对应的所有数据类型所有日期的数据转化为一个DataFrame
                            如果类型为str，表示股票代码，如果类型为int，代表该share所在的层序号

            :param dropna:  Boolean，是否去除NaN值

            :param inf_as_na:
                            Boolean，是否将inf值当成NaN值一同去掉，当dropna为False时无效
            :return:
                pandas.DataFrame

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

    def to_df_dict(self, by: str = 'share') -> dict:
        """ 将一个HistoryPanel转化为一个dict，这个dict的keys是HP中的shares，values是每个shares对应的历史数据
            这些数据以DataFrame的格式存储

        :param by: str, 'share' 或 'shares' 将HistoryPanel中的数据切成若干片，每一片转化成一个DataFrame，
                        它的keys是股票的代码，每个股票代码一个DataFrame
                        'htype' 或 'htypes' 将HistoryPanel中的数据切成若干片，每一片转化成一个DataFrame，
                        它的keys是历史数据类型，每种类型一个DataFrame

        :return:
            dict
        """
        assert isinstance(by, str)
        assert by.lower() in ['share', 'shares', 'htype', 'htypes']

        df_dict = {}
        if self.is_empty:
            return df_dict

        if by.lower() in ['share', 'shares']:
            for share in self.shares:
                df_dict[share] = self.to_dataframe(share=share)
            return df_dict

        if by.lower() in ['htype', 'htypes']:
            for htype in self.htypes:
                df_dict[htype] = self.to_dataframe(htype=htype)
            return df_dict

    # TODO: implement this method
    def head(self, row_count=5):
        """打印HistoryPanel的最初几行，默认打印五行"""

        raise NotImplementedError

    # TODO: implement this method
    def tail(self, row_count=5):
        """打印HistoryPanel的最末几行，默认打印五行"""

        raise NotImplementedError

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

        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    # TODO: implement this method
    def renko(self, *args, **kwargs):
        """ plot renko chart with data in the HistoryPanel, check data availability before plotting

        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError


def hp_join(*historypanels):
    """ 当元组*historypanels不是None，且内容全都是HistoryPanel对象时，将所有的HistoryPanel对象连接成一个HistoryPanel

    :param historypanels: 一个或多个HistoryPanel对象，他们将被组合成一个包含他们所有数据的HistoryPanel
    :return:
    """
    assert all(isinstance(hp, HistoryPanel) for hp in historypanels), \
        f'Object type Error, all objects passed to this function should be HistoryPanel'
    res_hp = HistoryPanel()
    for hp in historypanels:
        if isinstance(hp, HistoryPanel):
            res_hp.join(other=hp)
    return res_hp


def dataframe_to_hp(df: pd.DataFrame,
                    hdates=None,
                    htypes=None,
                    shares=None,
                    column_type: str = None) -> HistoryPanel:
    """ 根据DataFrame中的数据创建HistoryPanel对象。由于DataFrame只有一个二维数组，因此一个DataFrame只能转化为以下两种HistoryPanel之一：
        1，只有一个share，包含一个或多个htype的HistoryPanel，这时HistoryPanel的shape为(1, dates, htypes)
            在这种情况下，htypes可以由一个列表，或逗号分隔字符串给出，也可以由DataFrame对象的column Name来生成，而share则必须给出
        2，只有一个dtype，包含一个或多个shares的HistoryPanel，这时HistoryPanel的shape为(shares, dates, 1)
        具体转化为何种类型的HistoryPanel可以由column_type参数来指定，也可以通过给出hdates、htypes以及shares参数来由程序判断

    :param df: pd.DataFrame, 需要被转化为HistoryPanel的DataFrame。
    :param hdates:
    :param htypes: str,
    :param shares: str,
    :param column_type: str: 可以为'share' or 'htype'
    :return:
        HistoryPanel对象
    """
    available_column_types = ['shares', 'htypes', None]
    from collections import Iterable
    assert isinstance(df, pd.DataFrame), f'Input df should be pandas DataFrame! got {type(df)} instead.'
    if hdates is None:
        hdates = df.rename(index=pd.to_datetime).index
    assert isinstance(hdates, Iterable), f'TypeError, hdates should be iterable, got {type(hdates)} instead.'
    index_count = len(hdates)
    assert index_count == len(df.index), \
        f'InputError, can not match {index_count} indices with {len(df.hdates)} rows of DataFrame'
    assert column_type in available_column_types, f'column_type should be a string in ["shares", "htypes"], ' \
                                                  f'got {type(column_type)} instead!'
    # TODO: Temp codes, implement this method when column_type is not given -- the column type should be infered
    # TODO: by the input combination of shares and htypes
    if column_type is None:
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
        # print(f'got None in function for column_type, column type is set to {column_type}')
    if column_type == 'shares':
        if shares is None:
            shares = df.columns
        elif isinstance(shares, str):
            shares = str_to_list(shares, sep_char=',')
            assert len(shares) == len(df.columns), \
                f'InputError, can not match {len(shares)} shares with {len(df.columns)} columns of DataFrame'
        else:
            assert isinstance(shares, Iterable), f'TypeError: levels should be iterable, got {type(shares)} instead.'
            assert len(shares) == len(df.columns), \
                f'InputError, can not match {len(shares)} shares with {len(df.columns)} columns of DataFrame'
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
            assert isinstance(htypes, Iterable), f'TypeError: levels should be iterable, got {type(htypes)} instead.'
            assert len(htypes) == len(df.columns), \
                f'InputError, can not match {len(htypes)} shares with {len(df.columns)} columns of DataFrame'
        assert shares is not None, f'InputError, shares should be given when they can not inferred'
        assert isinstance(shares, str), \
            f'TypeError, data type of share should be a string, got {type(shares)} instead.'
        history_panel_value = df.values.reshape(1, len(hdates), len(htypes))
    return HistoryPanel(values=history_panel_value, levels=shares, rows=hdates, columns=htypes)


def stack_dataframes(dfs: [list, dict], stack_along: str = 'shares', shares=None, htypes=None):
    """ 将多个dataframe组合成一个HistoryPanel.

    dfs可以是一个dict或一个list，如果是一个list，这个list包含需要组合的所有dataframe，如果是dict，这个dict的values包含
    所有需要组合的dataframe，dict的key包含每一个dataframe的标签，这个标签可以被用作HistoryPanel的层（shares）或列
    （htypes）标签。如果dfs是一个list，则组合后的行标签或列标签必须明确给出。

    组合的方式有两种，根据stack_along参数的值来确定采用哪一种组合方式：
    stack_along == 'shares'，
        表示把DataFrame按照股票方式组合，假定每个DataFrame代表一个share的数据，每一列代表一个htype。组合后的HP对象
        层数与DataFrame的数量相同，而列数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
        在这种模式下：
        如果dfs是一个list，shares参数必须给出，且shares的数量必须与DataFrame的数量相同，作为HP的层标签
        如果dfs是一个dict，shares参数不必给出，dfs的keys会被用于层标签，如果shares参数给出且符合要求，shares参数将取代dfs的keys参数

    stack_along == 'htypes'，
        表示把DataFrame按照数据类型方式组合，假定每个DataFrame代表一个htype的数据，每一列代表一个share。组合后的HP对象
        列数与DataFrame的数量相同，而层数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
        在这种模式下，
        如果dfs是一个list，htypes参数必须给出，且htypes的数量必须与DataFrame的数量相同，作为HP的列标签
        如果dfs是一个dict，htypes参数不必给出，dfs的keys会被用于列标签，如果htypes参数给出且符合要求，htypes参数将取代dfs的keys参数

    :param dfs: type list, containing multiple dataframes
    :param stack_along: type str, 'shares' 或 'htypes'
    :param shares:
    :param htypes:
    :return:
    """
    assert isinstance(dfs, (list, dict)), \
        f'TypeError, dfs should be a list of or a dict whose values are pandas DataFrames, got {type(dfs)} instead.'
    assert stack_along in ['shares', 'htypes'], \
        f'InputError, valid input for stack_along can only be \'shaers\' or \'htypes\''
    combined_index = []
    combined_shares = []
    combined_htypes = []
    if stack_along == 'shares':
        assert (shares is not None) or (isinstance(dfs, dict)), \
            f'shares should be given if the dataframes are to be stacked along shares and they are not in a dict'
        assert isinstance(shares, (list, str)) or (isinstance(dfs, dict))
        if isinstance(shares, str):
            shares = str_to_list(shares)
        if isinstance(dfs, dict) and shares is None:
            shares = dfs.keys()
        assert len(shares) == len(dfs)
        combined_shares.extend(shares)
    else:
        assert (htypes is not None) or (isinstance(dfs, dict)), \
            f'htypes should be given if the dataframes are to be stacked along htypes and they are not in a dict'
        assert isinstance(htypes, (list, str)) or (isinstance(dfs, dict))
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
        if isinstance(dfs, dict) and htypes is None:
            htypes = dfs.keys()
        assert len(htypes) == len(dfs)
        combined_htypes.extend(htypes)

    if isinstance(dfs, dict):
        dfs = dfs.values()

    for df in dfs:
        assert isinstance(df, pd.DataFrame), \
            f'InputError, dfs should be a list of pandas DataFrame, got {type(df)} instead.'
        combined_index.extend(df.rename(index=pd.to_datetime).index)
        if stack_along == 'shares':
            combined_htypes.extend(df.columns)
        else:
            combined_shares.extend(df.columns)
    dfs = [df.rename(index=pd.to_datetime) for df in dfs]
    if stack_along == 'shares':
        combined_htypes = list(set(combined_htypes))
        combined_htypes.sort()
    else:
        combined_shares = list(set(combined_shares))
        combined_shares.sort()
    combined_index = list(set(combined_index))
    htype_count = len(combined_htypes)
    share_count = len(combined_shares)
    index_count = len(combined_index)
    combined_htypes_dict = dict(zip(combined_htypes, range(htype_count)))
    combined_shares_dict = dict(zip(combined_shares, range(share_count)))
    combined_index.sort()
    res_values = np.zeros(shape=(share_count, index_count, htype_count))
    res_values.fill(np.nan)
    for df_id in range(len(dfs)):
        extended_df = dfs[df_id].reindex(combined_index)
        for col_name, series in extended_df.iteritems():
            if stack_along == 'shares':
                res_values[df_id, :, combined_htypes_dict[col_name]] = series.values
            else:
                res_values[combined_shares_dict[col_name], :, df_id] = series.values
    return HistoryPanel(res_values,
                        levels=combined_shares,
                        rows=combined_index,
                        columns=combined_htypes)


# ==================
# High level functions that creates HistoryPanel that fits the requirement of trade strategies
# ==================
def get_history_panel(start,
                      end,
                      freq,
                      shares,
                      htypes,
                      asset_type: str,
                      adj: str,
                      data_source=None):
    """ 最主要的历史数据获取函数，从本地DataSource（数据库/csv/hdf/fth）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

    :param start:
    :param end:
    :param freq:
    :param shares:
    :param htypes:
    :param asset_type: str
    :param adj:
    :param data_source: DataSource Object
    :return:
    """
    if data_source is None:
        from qteasy import QT_DATA_SOURCE
        ds = QT_DATA_SOURCE
    else:
        if not isinstance(data_source, qteasy.DataSource):
            raise TypeError(f'data_source should be a data source object, got {type(data_source)} instead')
        ds = data_source
    result_hp = ds.get_history_data(shares=shares,
                                    htypes=htypes,
                                    start=start,
                                    end=end,
                                    freq=freq,
                                    asset_type=asset_type,
                                    adj=adj)
    return result_hp
