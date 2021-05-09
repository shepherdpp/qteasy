# coding=utf-8
# history.py

# ======================================
# This file contains history data related
# Classes and functions. Such as
# HistoryPanel class, and historical
# data downloading functions based on
# tushare
# ======================================

import pandas as pd
import tushare as ts
import numpy as np
from time import sleep
from warnings import warn
from concurrent.futures import ProcessPoolExecutor, as_completed

from .utilfuncs import str_to_list, list_or_slice, labels_to_dict, list_truncate
from .utilfuncs import list_to_str_format, progress_bar, next_trade_day, next_market_trade_day
from .tsfuncs import get_bar, name_change
from .tsfuncs import income, indicators, balance, cashflow

from ._arg_validators import PRICE_TYPE_DATA, INCOME_TYPE_DATA
from ._arg_validators import BALANCE_TYPE_DATA, CASHFLOW_TYPE_DATA
from ._arg_validators import INDICATOR_TYPE_DATA
from ._arg_validators import COMPOSIT_TYPE_DATA

TUSHARE_TOKEN = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
ts.set_token(TUSHARE_TOKEN)


class HistoryPanel():
    """qteasy 量化投资系统使用的主要历史数据的数据类型.

    HistoryPanel数据结构的核心部分是一个基于numpy的三维ndarray矩阵，这个矩阵由M层N行L列，三个维度的轴标签分别为：
        axis 1: 层，每层的标签为一个个股，每一层在HistoryPanel中被称为一个level，所有level的标签被称为shares
        axis 2: 行，每行的标签为一个时间点，每一行在HistoryPanel中被称为一个row，所有row的标签被称为hdates
        axis 3: 列，每列的标签为一种历史数据，每一列在HistoryPanel中被称为一个column，所有column的标签被称为htypes

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

            在生成一个HistoryPanel的时候，应该同时输入层标签、行标签和列标签分别代表所输入数据的数据类型、日期时间戳以及股票代码，如果
            不输入这些数据，从数据结构的层面上来说不会有问题，但是在qteasy应用中可能会报错。

            历史数据类型可以包括类似开盘价、收盘价这样的量价数据，同样也可以包括诸如pe、ebitda等等财务数据

        :param values: 一个ndarray，必须是一个三维数组，如果不给出values，则会返回一个空HistoryPanel，其empty属性为True
        :param levels: HistoryPanel的层标签，层的数量为values第一个维度的数据量，每一层代表一个数据类型
        :param rows: datetime range或者timestamp index或者str类型，通常是时间类型或可以转化为时间类型，行标签代表每一条数据对应的
                        历史时间戳
        :param columns:str，通常为股票代码或证券代码，
        """

        # TODO: 在生成HistoryPanel时如果只给出data或者只给出data+columns，生成HistoryPanel打印时会报错，问题出在to_dataFrame()上
        self._levels = None
        self._columns = None
        self._rows = None
        if values is None:
            self._l_count, self._r_count, self._c_count = (0, 0, 0)
            self._values = None
            self._is_empty = True
        else:
            assert isinstance(values, np.ndarray), f'input value type should be numpy ndarray, got {type(values)}'
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
                if len(levels) == 1:
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
        """返回HistoryPanel的层标签字典

        HistoryPanel的层标签是保存成一个字典形式的：
        levels =    {level_name[0]: 0,
                     level_name[1]: 1,
                     level_name[2]: 2,
                     ...
                     level_name[l]: l}
        这个字典在level的标签与level的id之间建立了一个联系，因此，如果需要通过层标签来快速地访问某一层的数据，可以非常容易地通过：
            data = HP.values[levels[level_name[a], :, :]
        来访问

        不过这是HistoryPanel内部的处理机制，在HistoryPanel的外部，可以通过切片的方式快速访问不同的数据。
        """
        return self._levels

    @property
    def shares(self):
        """返回HistoryPanel的列标签——股票列表"""
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
        """返回HistoryPanel中数据类型的数量"""
        return self._l_count

    @property
    def share_count(self):
        """获取HistoryPanel中股票的数量"""
        return self._l_count

    @property
    def rows(self):
        """ 与levels类似，rows也是返回一个字典，通过这个字典建立日期与行号的联系：

        rows =  {row_date[0]: 0,
                 row_daet[1]: 1,
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
        if self.is_empty:
            return 0
        else:
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
        """与levels及rows类似，获取一个字典，将股票代码与列号进行对应
        columns = {share_name[0]: 0,
                   share_naem[1]: 1,
                   share_name[2]: 2,
                   ...
                   share_name[c]: c}

        这样便于内部根据股票代码对数据进行切片
        """
        return self._columns

    @property
    def column_count(self):
        """获取HistoryPanel的列数量或股票数量"""
        return self._c_count

    @property
    def htype_count(self):
        """获取HistoryPanel的历史数据类型数量"""
        return self._c_count

    @property
    def shape(self):
        """获取HistoryPanel的各个维度的尺寸"""
        return self._l_count, self._r_count, self._c_count

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

            # print('share_pool is ', share_slice, '\nhtypes is ', htype_slice,
            #      '\nhdates is ', hdate_slice)
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
        assert isinstance(with_val, (int, float, np.int, np.float))
        if not self.is_empty:
            np._values = np.where(np.isnan(self._values), with_val, self._values)
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
        """ Convert the data type of current HistoryPanel to another

        :param dtype:
        :return:
        """
        ALL_DTYPES = ['float', 'int']
        if not self.is_empty:
            assert isinstance(dtype, str), f'InputError, dtype should be a string, got {type(dtype)}'
            assert dtype in ALL_DTYPES, f'data type {dtype} is not recognized or not supported!'
            self.values.astype(dtype)
        return self

    def to_dataframe(self, htype: str = None, share: str = None) -> pd.DataFrame:
        """将HistoryPanel对象中的指定片段转化为DataFrame

        由于HistoryPanel对象包含三维数据，因此在转化时必须指定htype或者share参数中的一个
        """
        if self.is_empty:
            return pd.DataFrame()
        else:
            if all(par is not None for par in (htype, share)) or all(par is None for par in (htype, share)):
                # 两个参数都是非None或都是None，应该弹出警告信息
                raise KeyError(f'Only and exactly one of the parameters htype and share should be given, '
                               f'got both or none')
            if htype is not None:
                assert isinstance(htype, (str, int)), f'htype must be a string or an integer, got {type(htype)}'
                if htype in self.htypes:
                    v = self[htype].T.squeeze()
                    return pd.DataFrame(v, index=self.hdates, columns=self.shares)
                else:
                    raise KeyError(f'htype {htype} is not found!')
            if share is not None:
                assert isinstance(share, (str, int)), f'share must be a string or an integer, got {type(share)}'
                if share in self.shares:
                    v = self[:, share].squeeze()
                    return pd.DataFrame(v, index=self.hdates, columns=self.htypes)
                else:
                    raise KeyError(f'share {share} is not found!')

    # TODO: implement this method
    def to_df_dict(self):
        """ 将一个HistoryPanel转化为一个dict，这个dict的keys是HP中的shares，values是每个shares对应的历史数据
            这些数据以DataFrame的格式存储

        :return:
            dict
        """
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

    # TODO implement this method
    def to_csv(self):
        """ save a HistoryPanel object to csv file

        :return:
        """
        raise NotImplementedError

    # TODO implement this method
    def to_hdf(self):
        """ save a HistoryPanel object to hdf file

        :return:
        """
        raise NotImplementedError

    # TODO implement this method
    def to_db(self):
        """ save HistoryPanel to a database or to update the database with current HistoryPanel

        :return:
        """
        raise NotImplementedError


# TODO implement this method
def csv_to_hp():
    """ read a csv file and convert its data to a HistoryPanel

    :return:
    """
    raise NotImplementedError


# TODO implement this method
def hdf_to_hp():
    """ read a hdf file and convert its data to a HistoryPanel

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
        1，只有一个share，包含一个或多个htype的HistoryPanel，这时HistoryPanel的share为(1, dates, htypes)
            在这种情况下，htypes可以由一个列表，或逗号分隔字符串给出，也可以由DataFrame对象的column Name来生成，而htypes则必须给出
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
        print(f'got None in function for column_type, column type is set to {column_type}')
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
                      chanel: str,
                      parallel: int = None,
                      delay: float = None,
                      delay_every: int = None,
                      progress: bool = None):
    """ 最主要的历史数据获取函数，从本地（数据库/csv/hd5）或者在线（Historical Utility functions）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

        首先利用不同的get_X_type_raw_data()函数获取不同类型的原始数据，再把原始数据整理成为date_by_row及htype_by_column的不同的
        dataframe，再使用stack_dataframe()函数把所有的dataframe组合成HistoryPanel格式

    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param asset_type: str
    :param chanel:
    :param parallel:
    :param delay:
    :param delay_every:
    :param progress:
    :return:
    """
    if isinstance(htypes, str):
        htypes = str_to_list(input_string=htypes, sep_char=',')
    price_type_data = [t for t in htypes if t in PRICE_TYPE_DATA]
    income_type_data = [t for t in htypes if t in INCOME_TYPE_DATA]
    balance_type_data = [t for t in htypes if t in BALANCE_TYPE_DATA]
    cashflow_type_data = [t for t in htypes if t in CASHFLOW_TYPE_DATA]
    indicator_type_data = [t for t in htypes if t in INDICATOR_TYPE_DATA]
    composite_type_data = [t for t in htypes if t in COMPOSIT_TYPE_DATA]
    finance_report_types = [income_type_data,
                            balance_type_data,
                            cashflow_type_data,
                            indicator_type_data]
    dataframes_to_stack = {}
    if chanel == 'local':
        from .database import DataSource
        ds = DataSource()
        result_hp = ds.get_and_update_data(start=start,
                                           end=end,
                                           freq=freq,
                                           shares=shares,
                                           htypes=htypes,
                                           asset_type=asset_type,
                                           adj=adj,
                                           parallel=parallel,
                                           delay=delay,
                                           delay_every=delay_every,
                                           progress=progress,
                                           refresh=False)
        return result_hp
    if chanel == 'online':
        result_hp = HistoryPanel()
        if len(price_type_data) > 0:
            dataframes_to_stack.update(get_price_type_raw_data(start=start,
                                                               end=end,
                                                               freq=freq,
                                                               shares=shares,
                                                               htypes=price_type_data,
                                                               asset_type=asset_type,
                                                               parallel=parallel,
                                                               delay=delay,
                                                               delay_every=delay_every,
                                                               progress=progress))
            if isinstance(shares, str):
                shares = str_to_list(shares)
            result_hp = result_hp.join(other=stack_dataframes(dfs=dataframes_to_stack,
                                                              stack_along='shares'),
                                       same_shares=True)

        for report_type in [t for t in finance_report_types if len(t) > 0]:

            (income_dfs,
             indicator_dfs,
             balance_dfs,
             cashflow_dfs
             ) = get_financial_report_type_raw_data(start=start,
                                                    end=end,
                                                    shares=shares,
                                                    htypes=report_type,
                                                    parallel=parallel,
                                                    delay=delay,
                                                    delay_every=delay_every,
                                                    progress=progress
                                                    )
            if isinstance(shares, str):
                shares = str_to_list(shares)
            for dfs in (income_dfs, indicator_dfs, balance_dfs, cashflow_dfs):
                if len(dfs) > 0:
                    result_hp = result_hp.join(other=stack_dataframes(dfs=dfs,
                                                                      stack_along='shares'),
                                               same_shares=True)

        if len(composite_type_data) > 0:
            dataframes_to_stack.update(get_composite_type_raw_data(start=start,
                                                                   end=end,
                                                                   shares=shares,
                                                                   htypes=composite_type_data,
                                                                   chanel=chanel))
            result_hp = result_hp.join(other=stack_dataframes(dfs=dataframes_to_stack,
                                                              stack_along='shares'),
                                       same_shares=True)

        return result_hp


def get_price_type_raw_data(start: str,
                            end: str,
                            freq: str,
                            shares: [str, list],
                            htypes: [str, list],
                            asset_type: str = 'E',
                            adj: str = 'none',
                            parallel: int = 16,
                            delay: float = 20,
                            delay_every: int = 500,
                            progress: bool = True,
                            prgrs_txt: str = ''):
    """ 在线获取价格和交易量类型历史数据，并且打包成包含date_by_row且htype_by_column的dataframe的列表

    :param start:
        str, 'YYYYMMDD' 格式的日期，历史数据开始的日期

    :param end:
        str, 'YYYYMMDD' 格式的日期，历史数据结束的日期

    :param freq:
        str, 历史数据的频率，如'd'， 'w', '30min'等

    :param htypes:
        str or list, 历史数据的种类，如'close', 'open'等

    :param shares:
        str, 股票代码，必须是诸如'600748.SH'格式的代码

    :param asset_type:
        type:string: one of {'E':股票, 'I':指数, 'F':期货, 'FD':基金}

    :param adj:
        type: string, 是否下载复权数据，one of {'none': 不复权, 'hfq': 后复权, 'qfq': 前复权}

    :param parallel:
        int, 默认16，同时开启的线程数量，为0或1时为单线程

    :param delay:
        默认0，在两次请求网络数据之间需要延迟的时间长短，单位为秒

    :param delay_every:
        int, 默认500，在两次delay之间允许下载的数量

    :param progress: bool:
        progress == True, Default 下载时显示进度条
        progress == False  下载时不显示进度条

    :param prgrs_txt:
        在进度条中显示的信息文本

    :return:
        dict, 一个包含所有下载的DataFrame的字典，字典的key是shares标签
    """
    if htypes is None:
        htypes = PRICE_TYPE_DATA
    if isinstance(htypes, str):
        htypes = str_to_list(input_string=htypes, sep_char=',')
    if isinstance(shares, str):
        shares = str_to_list(input_string=shares, sep_char=',')
    # 使用一个字典存储所有下载的股票数据
    df_per_share = {}
    if parallel is None:
        parallel = 16
    if adj is None:
        adj = 'none'
    if delay is None:
        delay = 20
    if delay_every is None:
        delay_every = 500
    if progress is None:
        progress = True
    i = 0
    total_share_count = len(shares)
    if progress:
        progress_bar(i, total_share_count, comments=prgrs_txt)

    if parallel > 1:  # 同时开启线程数量大于1时，启动多线程，否则单线程，网络状态下16～32线程可以大大提升下载速度，但会受服务器端限制
        proc_pool = ProcessPoolExecutor(parallel)
        if delay > 0:
            truncated_shares = list_truncate(shares, delay_every)
        else:
            truncated_shares = [shares]
            # TODO: CRITICAL!
            # TODO: 一个关键错误！！
            # TODO: 是用多线程并行下载的数据无法保持其返回的顺序一致，也就是说，返回的数据顺序会被打乱，这里使用list来保存
            # TODO: 返回的历史数据结果就不合适了，因为在多线程返回的结果中，无法判断哪一组数据是属于哪一个股票代码的，应该
            # TODO: 使用dict来保存所有的信息，这样才不会搞错数据。
        for shares in truncated_shares:
            futures = {proc_pool.submit(get_bar, share, start, end, asset_type, adj, freq): share for share in
                       shares}
            for f in as_completed(futures):
                raw_df = f.result()
                if raw_df.empty:
                    raw_df = pd.DataFrame([[futures[f], start] + [np.nan] * 9,
                                           [futures[f], end] + [np.nan] * 9],
                                          columns=["ts_code", "trade_date", "open", "high",
                                                   "low", "close", "pre_close", "change",
                                                   "pct_chg", "vol", "amount"])
                    warn(f'historical data {htypes} for {futures[f]} does not exist from {start} to '
                         f'{end} in frequency {freq}', category=UserWarning)
                df_per_share[futures[f]] = raw_df.loc[np.where(raw_df.ts_code == futures[f])]

                i += 1
                if progress:
                    progress_bar(i, total_share_count, comments=prgrs_txt)

            if delay > 0:
                sleep(delay)
    else:
        for share in shares:
            if i % delay_every == 0 and delay > 0:
                sleep(delay)
            raw_df = get_bar(shares=share, start=start, asset_type=asset_type, end=end, freq=freq, adj=adj)
            if raw_df.empty:
                # 当raw_df is None，说明该股票在指定的时段内没有数据，此时应该生成一个简单的空DataFrame，除
                # 了share和date两列有数据以外，其他的数据全都是np.nan，这样就能在填充本地数据时，使用nan覆盖inf数据
                raw_df = pd.DataFrame([[share, start] + [np.nan] * 9,
                                       [share, end] + [np.nan] * 9],
                                      columns=["ts_code", "trade_date", "open", "high",
                                               "low", "close", "pre_close", "change",
                                               "pct_chg", "vol", "amount"])
                warn(f'historical data {htypes} for {share} does not exist from {start} to '
                     f'{end} in frequency {freq}', category=UserWarning)
            df_per_share[share] = raw_df.loc[np.where(raw_df.ts_code == share)]

            i += 1
            if progress:
                progress_bar(i, total_share_count, comments=prgrs_txt)

    columns_to_remove = list(set(PRICE_TYPE_DATA) - set(htypes))
    if len(df_per_share) > 0:
        for df in df_per_share.values():
            df.index = pd.to_datetime(df.trade_date).sort_index()
            df.drop(columns=columns_to_remove, inplace=True)
            df.drop(columns=['ts_code', 'trade_date'], inplace=True)
    return df_per_share


def get_financial_report_type_raw_data(start: str,
                                       end: str,
                                       shares: str,
                                       htypes: [str, list],
                                       parallel: int = 0,
                                       delay=1.25,
                                       delay_every: int = 50,
                                       progress: bool = True):
    """ 在线获取财报类历史数据，目前支持四大类历史数据，分别是：
            income      利润表项目数据
            indicator   关键财务指标
            balance     资产负债表项目数据
            cashflow     现金流量表项目数据
        四大类数据的获取后分别保存在四个不同的字典中返回，每个字典包含所有所需股票的数据，这些数据以DataFrame的形式
        存储在字典的values中，每个DF的键值是其股票的代码

    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param parallel: int, 默认0，数字大于1时开启多线程并行下载，数字为并行线程数量
    :param delay: float, 为了防止网络限制，两次下载之间的间隔时间
    :param delay_every: int, 默认500，在两次delay之间允许下载的数量
    :param progress: bool:
                    progress == True, Default 下载时显示进度条
                    progress == False  下载时不显示进度条
    :return:
        tuple, 包含四个字典元素，每个字典元素中包含所需下载的股票的数据
    """
    if isinstance(htypes, str):
        htypes = str_to_list(input_string=htypes, sep_char=',')

    if isinstance(shares, str):
        shares = str_to_list(input_string=shares, sep_char=',')
    if parallel is None:
        parallel = 16
    if delay is None:
        delay = 20
    if delay_every is None:
        delay_every = 500
    if progress is None:
        progress = True
    total_share_count = len(shares)
    report_fields = ['ts_code', 'end_date']
    income_fields = list_to_str_format(report_fields + [htype for
                                                        htype in htypes
                                                        if htype in INCOME_TYPE_DATA])
    indicator_fields = list_to_str_format(report_fields + [htype for
                                                           htype in htypes
                                                           if htype in INDICATOR_TYPE_DATA])
    balance_fields = list_to_str_format(report_fields + [htype for
                                                         htype in htypes
                                                         if htype in BALANCE_TYPE_DATA])
    cashflow_fields = list_to_str_format(report_fields + [htype for
                                                          htype in htypes
                                                          if htype in CASHFLOW_TYPE_DATA])
    income_dfs = {}
    indicator_dfs = {}
    balance_dfs = {}
    cashflow_dfs = {}
    i = 0
    if progress:
        progress_bar(i, total_share_count)
    if parallel > 1:  # only works when number of shares < 50 because currently only 50 downloads per min is allowed
        proc_pool = ProcessPoolExecutor()
        if len(str_to_list(income_fields)) > 2:
            # TODO: CRITICAL!
            # TODO: 一个关键错误！！
            # TODO: 是用多线程并行下载的数据无法保持其返回的顺序一致，也就是说，返回的数据顺序会被打乱，这里使用list来保存
            # TODO: 返回的历史数据结果就不合适了，因为在多线程返回的结果中，无法判断哪一组数据是属于哪一个股票代码的，应该
            # TODO: 使用dict来保存所有的信息，这样才不会搞错数据。
            futures = {proc_pool.submit(income, share, None, start, end, None, None, None, income_fields): share for
                       share in shares}
            for f in as_completed(futures):
                income_dfs[futures[f]] = (regulate_financial_type_df(f.result()))

                i += 1
                if progress:
                    progress_bar(i, total_share_count)

        if len(str_to_list(indicator_fields)) > 2:
            futures = {proc_pool.submit(indicators, share, None, start, end, None, indicator_fields): share for
                       share in shares}
            for f in as_completed(futures):
                indicator_dfs[futures[f]] = (regulate_financial_type_df(f.result()))

                i += 1
                if progress:
                    progress_bar(i, total_share_count)

        if len(str_to_list(balance_fields)) > 2:
            futures = {proc_pool.submit(balance, share, None, start, end, None, None, None, balance_fields): share for
                       share in shares}
            for f in as_completed(futures):
                balance_dfs[futures[f]] = (regulate_financial_type_df(f.result()))

                i += 1
                if progress:
                    progress_bar(i, total_share_count)

        if len(str_to_list(cashflow_fields)) > 2:
            futures = {proc_pool.submit(cashflow, share, None, start, end, None, None, None, cashflow_fields): share for
                       share in shares}
            for f in as_completed(futures):
                cashflow_dfs[futures[f]] = (regulate_financial_type_df(f.result()))

                i += 1
                if progress:
                    progress_bar(i, total_share_count)

    else:
        for share in shares:
            if i % delay_every == 0 and delay > 0:
                sleep(delay)
            # TODO: Investigate: very strange!!! DON'T KNOW WHY
            # TODO: whenever the ".sort_index()" is removed, the programe is going to fail
            # TODO: if it is added, then the program runs, but WHY??
            if len(str_to_list(income_fields)) > 2:
                df = income(start=start, end=end, share=share, fields=income_fields).sort_index()
                income_dfs[share] = (regulate_financial_type_df(df))

            if len(str_to_list(indicator_fields)) > 2:
                df = indicators(start=start, end=end, share=share, fields=indicator_fields).sort_index()
                indicator_dfs[share] = (regulate_financial_type_df(df))

            if len(str_to_list(balance_fields)) > 2:
                df = balance(start=start, end=end, share=share, fields=balance_fields).sort_index()
                balance_dfs[share] = (regulate_financial_type_df(df))

            if len(str_to_list(cashflow_fields)) > 2:
                df = cashflow(start=start, end=end, share=share, fields=cashflow_fields).sort_index()
                cashflow_dfs[share] = (regulate_financial_type_df(df))

            i += 1
            if progress:
                progress_bar(i, total_share_count)
    return income_dfs, indicator_dfs, balance_dfs, cashflow_dfs


# TODO: implement this function
def get_composite_type_raw_data(start,
                                end,
                                shares,
                                htypes,
                                chanel,
                                parallel: int = 0,
                                delay=1.25,
                                delay_every: int = 50,
                                progress: bool = True):
    """

    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param chanel:
    :return:
    """
    if parallel is None:
        parallel = 16
    if delay is None:
        delay = 20
    if delay_every is None:
        delay_every = 500
    if progress is None:
        progress = True

    return None


def regulate_financial_type_df(df):
    """ 处理下载的财务指标数据，将它们转化为标准的格式：
        process and regulate downloaded financial data in form of DataFrame:
        - remove duplicated items 删除重复的条目
        - convert index into datetime format 将index转化为时间日期格式
        - remove useless columns 删除不需要的列
        - move non-trade day items to nearest next trade day 将所有的日期抖动到最近的下一交易日，确保所有日期都是交易日

    :param df:
    :return:
    """
    # TODO: investigate: what does ann_date really means, how to get correct report date?
    # TODO: current way of extracting date is WRONG!! ann_date sometimes are incorrect!
    if df.empty:
        return df
    df.fillna(np.nan)
    df.drop_duplicates(subset=['ts_code', 'end_date'], inplace=True)
    df.end_date = df.end_date.apply(next_market_trade_day, 1)
    df.index = pd.to_datetime(df.end_date)
    df.index.name = 'date'
    df.drop(columns=['ts_code', 'end_date'], inplace=True)
    return df