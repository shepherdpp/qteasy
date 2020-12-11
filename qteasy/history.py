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

from concurrent.futures import ProcessPoolExecutor, as_completed

from .utilfuncs import str_to_list, list_or_slice, labels_to_dict
from .utilfuncs import list_to_str_format, progress_bar
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

        :param values:
        :param levels:
        :param rows: datetime range or timestamp index of the data
        :param columns:
        """
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
        return self._is_empty

    @property
    def values(self):
        return self._values

    @property
    def levels(self):
        return self._levels

    @property
    def shares(self):
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
        return self._l_count

    @property
    def share_count(self):
        return self._l_count

    @property
    def rows(self):
        return self._rows

    @property
    def hdates(self):
        """hdates 是一个list"""
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
        return self._r_count

    @property
    def hdate_count(self):
        return self._r_count

    @property
    def htypes(self):
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
        return self._columns

    @property
    def column_count(self):
        return self._c_count

    @property
    def htype_count(self):
        return self._c_count

    @property
    def shape(self):
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
        res = []
        if self.is_empty:
            res.append(f'{type(self)} \nEmpty History Panel at {hex(id(self))}')
        else:
            if self.level_count <= 10:
                display_shares = self.shares
            else:
                display_shares = self.shares[0:3]
            for share in display_shares:
                res.append(f'\nshare {self.levels[share]}, label: {share}\n')
                df = self.to_dataframe(share=share)
                res.append(df.__str__())
                res.append('\n')
            if self.level_count > 10:
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
            将一个HistoryPanel对象与另一个HistoryPanel对象连接起来

            连接时可以指定两个HistoryPanel之间共享的

        :param other: type: HistoryPanel 需要合并的另一个HistoryPanel
        :param same_shares: 两个HP的shares是否相同，如果相同，可以省去shares纬度的标签合并。默认False，
        :param same_htypes: 两个HP的htypes是否相同，如果相同，可以省去htypes纬度的标签合并。默认False，
        :param same_hdates: 两个HP的hdates是否相同，如果相同，可以省去hdates纬度的标签合并。默认False，
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
            elif same_htypes:
                raise NotImplementedError
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

        由于HistoryPanel对象包含三维数据，因此在转化时必须指定
        """
        if self.is_empty:
            return pd.DataFrame()
        else:
            if all(par is not None for par in (htype, share)) or all(par is None for par in (htype, share)):
                # 两个参数都是非None或都是None，应该弹出警告信息
                raise KeyError(f'Only and exactly one of the parameters htype and share should be given, '
                               f'got both or none')
            if htype is not None:
                assert isinstance(htype, str), f'htype must be a string, got {type(htype)}'
                if htype in self.htypes:
                    v = self[htype].T.squeeze()
                    return pd.DataFrame(v, index=self.hdates, columns=self.shares)
                else:
                    raise KeyError(f'htype {htype} is not found!')
            if share is not None:
                assert isinstance(share, str), f'share must be a string, got {type(share)}'
                if share in self.shares:
                    v = self[:, share].squeeze()
                    return pd.DataFrame(v, index=self.hdates, columns=self.htypes)
                else:
                    raise KeyError(f'share {share} is not found!')

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

    :param same_shares:
    :param same_htypes:
    :param same_hdates:
    :param *historypanels: tuple,
    :return:
    """
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


def stack_dataframes(dfs: list, stack_along: str = 'shares', shares=None, htypes=None):
    """ 将多个dataframe组合成一个HistoryPanel

    组合的方式有两种，根据stack_along参数的值来确定采用哪一种组合方式：
    stack_along == 'shares'，
    表示把DataFrame按照股票方式组合，假定每个DataFrame代表一个share的数据，每一列代表一个htype。组合后的HP对象
    层数与DataFrame的数量相同，而列数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
    在这种模式下，shares参数必须给出，且shares的数量必须与DataFrame的数量相同
    stack_along == 'htypes'，
    表示把DataFrame按照数据类型方式组合，假定每个DataFrame代表一个htype的数据，每一列代表一个share。组合后的HP对象
    列数与DataFrame的数量相同，而层数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
    在这种模式下，htypes参数必须给出，且htypes的数量必须与DataFrame的数量相同

    :param dfs: type list, containing multiple dataframes
    :param stack_along: type str, 'shares' 或 'htypes'
    :param shares:
    :param htypes:
    :return:
    """
    assert isinstance(dfs, list), f'TypeError, dfs should be a list of pandas DataFrames, got {type(dfs)} instead.'
    assert stack_along in ['shares', 'htypes'], \
        f'InputError, valid input for stack_along can only be \'shaers\' or \'htypes\''
    combined_index = []
    combined_shares = []
    combined_htypes = []
    if stack_along == 'shares':
        assert shares is not None
        assert htypes is None, \
            f'ValueError, Only shares should be given if the dataframes shall be stacked along axis shares'
        assert isinstance(shares, (list, str))
        if isinstance(shares, str):
            shares = str_to_list(shares)
        assert len(shares) == len(dfs)
        combined_shares.extend(shares)
    else:
        assert htypes is not None
        assert shares is None, \
            f'ValueError, Only htypes should be given if the dataframes shall be stacked along axis htypes'
        assert isinstance(htypes, (list, str))
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
        assert len(htypes) == len(dfs)
        combined_htypes.extend(htypes)
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
    # debug
    # print(f'In stack dataframe function, combined index is:\n{combined_index}\nlength: {len(combined_index)}')
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
# TODO: problem downloading financial type data, problems should be inspected and solved
def get_history_panel(start, end, freq, shares, htypes, asset_type: str = 'E', chanel: str = 'local'):
    """ 最主要的历史数据获取函数，从本地（数据库/csv/hd5）或者在线（Historical Utility functions）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

        首先利用不同的get_X_type_raw_data()函数获取不同类型的原始数据，再把原始数据整理成为date_by_row及htype_by_column的不同的
        dataframe，再使用stack_dataframe()函数把所有的dataframe组合成HistoryPanel格式

    :param asset_type: str
    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param chanel:
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
    dataframes_to_stack = []
    # print(f'in function get_history_panel got shares: \n{shares}\nand htypes:\n{htypes}')
    if chanel == 'local':
        from .database import DataSource
        ds = DataSource()
        return ds.get_and_update_data(start=start, end=end, freq=freq,
                                      shares=shares, htypes=htypes, asset_type=asset_type)
    if chanel == 'online':
        result_hp = HistoryPanel()
        if len(price_type_data) > 0:
            dataframes_to_stack.extend(get_price_type_raw_data(start=start,
                                                               end=end,
                                                               freq=freq,
                                                               shares=shares,
                                                               htypes=price_type_data,
                                                               asset_type=asset_type,
                                                               chanel=chanel))
            if isinstance(shares, str):
                shares = str_to_list(shares)
            result_hp = result_hp.join(other=stack_dataframes(dfs=dataframes_to_stack,
                                                              stack_along='shares',
                                                              shares=shares),
                                       same_shares=True)

        for report_type in [t for t in finance_report_types if len(t) > 0]:

            income_dfs, indicator_dfs, balance_dfs, cashflow_dfs = get_financial_report_type_raw_data(start=start,
                                                                                                      end=end,
                                                                                                      shares=shares,
                                                                                                      htypes=report_type,
                                                                                                      chanel=chanel)
            if isinstance(shares, str):
                shares = str_to_list(shares)
            for dfs in (income_dfs, indicator_dfs, balance_dfs, cashflow_dfs):
                if len(dfs) > 0:
                    result_hp = result_hp.join(other=stack_dataframes(dfs=dfs,
                                                                      stack_along='shares',
                                                                      shares=shares),
                                               same_shares=True)

        if len(composite_type_data) > 0:
            print('Getting composite historical data...')
            dataframes_to_stack = get_composite_type_raw_data(start=start,
                                                              end=end,
                                                              shares=shares,
                                                              htypes=composite_type_data,
                                                              chanel=chanel)
            result_hp = result_hp.join(other=stack_dataframes(dfs=dataframes_to_stack,
                                                              stack_along='shares',
                                                              shares=str_to_list(shares)),
                                       same_shares=True)

        # debug
        # print(f'in function get_history_panel(), history panel is generated, they are:\n')
        # if result_hp is not None:
            # print(f'result history panel: \n{result_hp.info()}')

        return result_hp

# TODO: dynamically group shares thus data downloading can be less repetitive
# TODO: remove parameter chanel, and add progress: bool, to determine if progress bar
# TODO: should be displayed.
def get_price_type_raw_data(start: str,
                            end: str,
                            freq: str,
                            shares: [str, list],
                            htypes: [str, list],
                            asset_type: str = 'E',
                            parallel: int = 16,
                            delay = 0,
                            chanel: str = 'online'):
    """ 在线获取普通类型历史数据，并且打包成包含date_by_row且htype_by_column的dataframe的列表

    :param start:
    :param end:
    :param freq:
    :param shares:
    :param asset_type: type:string: one of {'E':股票, 'I':指数, 'F':期货, 'FD':基金}
    :param parallel: int, 默认16，同时开启的线程数量，为0或1时为单线程
    :param delay:   默认0，在两次请求网络数据之间需要延迟的时间长短，单位为秒
    :param htypes:
    :param chanel: str: {'online', 'local'}
                    chanel == 'online' 从网络获取历史数据
                    chanel == 'local'  从本地数据库获取历史数据
    :return:
    """
    if htypes is None:
        htypes = PRICE_TYPE_DATA
    if isinstance(htypes, str):
        htypes = str_to_list(input_string=htypes, sep_char=',')
    if isinstance(shares, str):
        shares = str_to_list(input_string=shares, sep_char=',')
    df_per_share = []
    total_share_count = len(shares)
    # debug
    # print(f'will download htype date {htypes} for share {shares}'
    i = 0
    progress_bar(i, total_share_count)

    if parallel > 1: # 同时开启线程数量大于1时，启动多线程，否则单线程，网络状态下16～32线程可以大大提升下载速度，但会受服务器端限制
        proc_pool = ProcessPoolExecutor(parallel)
        futures = {proc_pool.submit(get_bar, share, start, end, asset_type, None, freq): share for share in
                   shares}
        for f in as_completed(futures):
            raw_df = f.result()

            assert raw_df is not None, f'ValueError, something wrong downloading historical data {htypes} for share: ' \
                                       f'{futures[f]} from {start} to {end} in frequency {freq}'
            raw_df.drop_duplicates(subset=['ts_code', 'trade_date'], inplace=True)
            raw_df.index = range(len(raw_df))
            # print('\nraw df after rearange\n', raw_df)
            df_per_share.append(raw_df.loc[np.where(raw_df.ts_code == futures[f])])
            i += 1
            progress_bar(i, total_share_count)
    else:
        for share in shares:
            if delay > 0:
                sleep(delay)
            raw_df = get_bar(shares=share, start=start, asset_type=asset_type, end=end, freq=freq)
            # debug
            # print('raw df before rearange\n', raw_df)
            assert raw_df is not None, f'ValueError, something wrong downloading historical data {htypes} for share: ' \
                                       f'{share} from {start} to {end} in frequency {freq}'
            raw_df.drop_duplicates(subset=['ts_code', 'trade_date'], inplace=True)
            raw_df.index = range(len(raw_df))
            # print('\nraw df after rearange\n', raw_df)
            df_per_share.append(raw_df.loc[np.where(raw_df.ts_code == share)])
            i += 1
            progress_bar(i, total_share_count)
    columns_to_remove = list(set(PRICE_TYPE_DATA) - set(htypes))
    for df in df_per_share:
        df.index = pd.to_datetime(df.trade_date).sort_index()
        df.drop(columns=columns_to_remove, inplace=True)
        df.drop(columns=['ts_code', 'trade_date'], inplace=True)
    return df_per_share

# TODO: remove parameter chanel, and add progress: bool, to determine if progress bar
# TODO: should be displayed.
# TODO: and dynamically group shares thus data downloading can be less repetitive.
def get_financial_report_type_raw_data(start: str,
                                       end: str,
                                       shares: str,
                                       htypes: [str, list],
                                       parallel: int = 0,
                                       delay = 1.25,
                                       chanel: str = 'online'):
    """ 在线获取财报类历史数据

    :param report_type:
    :return:
    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param parallel: int, 默认0，数字大于1时开启多线程并行下载，数字为并行线程数量
    :param delay: float, 为了防止网络限制，两次下载之间的间隔时间
    :param chanel:
    :return:
    """
    if isinstance(htypes, str):
        htypes = str_to_list(input_string=htypes, sep_char=',')

    if isinstance(shares, str):
        shares = str_to_list(input_string=shares, sep_char=',')
    total_share_count = len(shares)
    report_fields = ['ts_code', 'ann_date']
    # debug
    # # print(f'in function get financial report type raw data, got htypes: \n{htypes}, \n'
    # #       f'income fields will be {[htype for htype in htypes if htype in INCOME_TYPE_DATA]}')
    # print(f'in function get financial report type raw data, got shares: \n{shares}')
    # print(f'income fields will be {report_fields + [htype for htype in htypes if htype in INCOME_TYPE_DATA]}
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
    income_dfs = []
    indicator_dfs = []
    balance_dfs = []
    cashflow_dfs = []
    # print('htypes:', htypes, "\nreport fields: ", report_fields)
    i = 0
    progress_bar(i, total_share_count)
    if parallel > 1: # only works when number of shares < 50 because currently only 50 downloads per min is allowed
        proc_pool = ProcessPoolExecutor()
        if len(str_to_list(income_fields)) > 2:
            futures = {proc_pool.submit(income, share, None, start, end, None, None, None, income_fields): share for
                       share in shares}
            for f in as_completed(futures):
                df = f.result()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code', 'ann_date'], inplace=True)
                income_dfs.append(df)
                i += 1
                progress_bar(i, total_share_count)

        if len(str_to_list(indicator_fields)) > 2:
            futures = {proc_pool.submit(indicators, share, None, start, end, None, indicator_fields): share for
                       share in shares}
            for f in as_completed(futures):
                df = f.result()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code', 'ann_date'], inplace=True)
                indicator_dfs.append(df)
                i += 1
                progress_bar(i, total_share_count)

        if len(str_to_list(balance_fields)) > 2:
            futures = {proc_pool.submit(balance, share, None, start, end, None, None, None, balance_fields): share for
                       share in shares}
            for f in as_completed(futures):
                df = f.result()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code', 'ann_date'], inplace=True)
                balance_dfs.append(df)
                i += 1
                progress_bar(i, total_share_count)

        if len(str_to_list(cashflow_fields)) > 2:
            futures = {proc_pool.submit(cashflow, share, None, start, end, None, None, None, cashflow_fields): share for
                       share in shares}
            for f in as_completed(futures):
                df = f.result()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code', 'ann_date'], inplace=True)
                cashflow_dfs.append(df)
                i += 1
                progress_bar(i, total_share_count)

    else:
        for share in shares:
            if delay > 0:
                sleep(delay)
            # TODO: refract these codes, combine and simplify similar codes
            if len(str_to_list(income_fields)) > 2:
                df = income(start=start, end=end, share=share, fields=income_fields).sort_index()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code','ann_date'], inplace=True)
                income_dfs.append(df)

            if len(str_to_list(indicator_fields)) > 2:
                df = indicators(start=start, end=end, share=share, fields=indicator_fields).sort_index()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code','ann_date'], inplace=True)
                indicator_dfs.append(df)

            if len(str_to_list(balance_fields)) > 2:
                df = balance(start=start, end=end, share=share, fields=balance_fields).sort_index()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code','ann_date'], inplace=True)
                balance_dfs.append(df)

            if len(str_to_list(cashflow_fields)) > 2:
                df = cashflow(start=start, end=end, share=share, fields=cashflow_fields).sort_index()
                df.drop_duplicates(subset=['ts_code', 'ann_date'], inplace=True)
                df.index = pd.to_datetime(df.ann_date)
                df.index.name = 'date'
                df.drop(columns=['ts_code','ann_date'], inplace=True)
                cashflow_dfs.append(df)
                # print('raw df before rearange\n', raw_df)

                # print('\nsingle df of share after removal\n', df)

            i += 1
            progress_bar(i, total_share_count)
    return income_dfs, indicator_dfs, balance_dfs, cashflow_dfs


# TODO: implement this function
def get_composite_type_raw_data(start, end, shares, htypes, chanel):
    """

    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param chanel:
    :return:
    """
    raise NotImplementedError